"""Evaluation plots: small squares on cropland, sampled in strata by distance to FIRMS fire points.

Sampling is stratified so there are enough burnt examples, which over-represents areas near fire
points. Each plot carries its stratum and the stratum's population size so metrics can be weighted
back to the whole area.

A second round splits each fire-distance stratum by whether the cell shows a burn-like signal in the
images, then adds plots only from the signal strata. Earlier plots stay valid: a simple random sample
within a stratum is still a simple random sample within each of its sub-strata.
"""
from dataclasses import dataclass

import numpy as np
from shapely.geometry import Point, box

from parali.area import AreaStack
from parali.features import nbr
from parali.fields import Field, reproject
from parali.firms import Fire, distance_m

STRATA = (("on", 0, 400), ("near", 400, 750), ("mid", 750, 2000), ("far", 2000, float("inf")))


@dataclass
class Candidate:
    row: int
    col: int
    lon: float
    lat: float
    fire_dist_m: float


def crop_mask(stack: AreaStack, cells: int, early_until, min_nbr: float = 0.25) -> np.ndarray:
    """Cells (cells x cells pixels) that held a standing crop early in the season."""
    early = [t for t, d in enumerate(stack.dates) if d <= early_until]
    vals = []
    for t in early:
        n = nbr(stack.band(t, "nir08"), stack.band(t, "swir22"))
        n[np.isin(stack.scl[t], (0, 1, 8, 9, 10))] = np.nan
        vals.append(n)
    with np.errstate(all="ignore"):
        med = np.nanmedian(np.stack(vals), axis=0)
    h, w = med.shape
    h2, w2 = h // cells, w // cells
    blocks = med[:h2 * cells, :w2 * cells].reshape(h2, cells, w2, cells)
    with np.errstate(all="ignore"):
        return np.nanmin(blocks, axis=(1, 3)) >= min_nbr


def candidates(stack: AreaStack, fires: list[Fire], cells: int, early_until) -> list[Candidate]:
    ok = crop_mask(stack, cells, early_until)
    out = []
    lats = np.array([f.lat for f in fires])
    lons = np.array([f.lon for f in fires])
    for r, c in zip(*np.nonzero(ok)):
        x, y = stack.transform @ ((c + 0.5) * cells, (r + 0.5) * cells)
        p = reproject(Point(x, y), stack.crs, "EPSG:4326")
        d = float(distance_m(p.y, p.x, lats, lons).min()) if len(fires) else float("inf")
        out.append(Candidate(int(r), int(c), p.x, p.y, d))
    return out


def _plot(stack: AreaStack, c: Candidate, cells: int, props: dict) -> Field:
    x0, y1 = stack.transform @ (c.col * cells, c.row * cells)
    x1, y0 = stack.transform @ ((c.col + 1) * cells, (c.row + 1) * cells)
    geom = reproject(box(x0, y0, x1, y1), stack.crs, "EPSG:4326")
    return Field(id=f"p{c.row:03d}_{c.col:03d}", geometry=geom, props=props)


def _fire_stratum(d: float) -> str:
    return next(name for name, lo, hi in STRATA if lo <= d < hi)


def signal_mask(stack: AreaStack, cells: int, dark_nbr: float = -0.15, max_bright: float = 0.08,
                min_drop: float = 0.25, min_share: float = 0.25) -> np.ndarray:
    """Cells where, on some date from October on, at least min_share of pixels turned near-black with low NBR
    right after a NIR drop. Deliberately looser than the decision rules."""
    from parali.features import brightness
    h, w = stack.scl.shape[1:]
    h2, w2 = h // cells, w // cells
    hit_any = np.zeros((h2, w2), dtype=bool)
    prev_nir = None
    for t, d in enumerate(stack.dates):
        bad = np.isin(stack.scl[t], (0, 1, 8, 9, 10))
        nir = stack.band(t, "nir08")
        nir[bad] = np.nan
        if prev_nir is not None and d.month >= 10:
            with np.errstate(all="ignore"):
                drop = (prev_nir - nir) / prev_nir
                n = nbr(nir, stack.band(t, "swir22"))
                b = brightness(stack.band(t, "red"), stack.band(t, "green"), stack.band(t, "blue"))
                hit = (n < dark_nbr) & (b <= max_bright) & (drop >= min_drop)
            share = hit[:h2 * cells, :w2 * cells].reshape(h2, cells, w2, cells).mean(axis=(1, 3))
            hit_any |= share >= min_share
        prev_nir = np.where(np.isnan(nir), prev_nir, nir) if prev_nir is not None else nir
    return hit_any


def add_signal_strata(stack: AreaStack, fires: list[Fire], plots: list[Field], extra: int = 40, cells: int = 4,
                      early_until=None, seed: int = 11) -> list[Field]:
    """Re-stratify existing plots by fire distance x burn signal and add `extra` plots from the signal strata."""
    rng = np.random.default_rng(seed)
    early_until = early_until or stack.dates[0].replace(month=10, day=12)
    cands = candidates(stack, fires, cells, early_until)
    sig = signal_mask(stack, cells)
    key = {(c.row, c.col): f"{_fire_stratum(c.fire_dist_m)}{'+sig' if sig[c.row, c.col] else ''}" for c in cands}
    sizes = {}
    for k in key.values():
        sizes[k] = sizes.get(k, 0) + 1
    out, taken = [], set()
    for p in plots:
        r, cc = map(int, p.id[1:].split("_"))
        k = key[(r, cc)]
        out.append(Field(p.id, p.geometry, {**p.props, "stratum": k, "stratum_size": sizes[k]}))
        taken.add((r, cc))
    sig_strata = sorted(k for k in sizes if k.endswith("+sig"))
    total = sum(sizes[k] for k in sig_strata)
    for k in sig_strata:
        n = max(3, round(extra * sizes[k] / total))
        pool = [c for c in cands if key[(c.row, c.col)] == k and (c.row, c.col) not in taken]
        for i in sorted(rng.choice(len(pool), size=min(n, len(pool)), replace=False)) if pool else []:
            c = pool[i]
            out.append(_plot(stack, c, cells, {"stratum": k, "stratum_size": sizes[k],
                                               "fire_dist_m": round(c.fire_dist_m), "round": 2}))
            taken.add((c.row, c.col))
    return out


def sample_plots(stack: AreaStack, fires: list[Fire], per_stratum: int = 70, cells: int = 4,
                 early_until=None, seed: int = 7) -> list[Field]:
    rng = np.random.default_rng(seed)
    early_until = early_until or stack.dates[0].replace(month=10, day=12)
    cands = candidates(stack, fires, cells, early_until)
    plots = []
    for name, lo, hi in STRATA:
        pool = [c for c in cands if lo <= c.fire_dist_m < hi]
        pick = rng.choice(len(pool), size=min(per_stratum, len(pool)), replace=False) if pool else []
        for k in sorted(pick):
            c = pool[k]
            plots.append(_plot(stack, c, cells, {
                "stratum": name, "stratum_size": len(pool), "fire_dist_m": round(c.fire_dist_m),
            }))
    return plots
