"""Evaluation plots: small squares on cropland, sampled in strata by distance to FIRMS fire points.

Sampling is stratified so there are enough burnt examples, which over-represents areas near fire
points. Each plot carries its stratum and the stratum's population size so metrics can be weighted
back to the whole area.
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
            x0, y1 = stack.transform @ (c.col * cells, c.row * cells)
            x1, y0 = stack.transform @ ((c.col + 1) * cells, (c.row + 1) * cells)
            geom = reproject(box(x0, y0, x1, y1), stack.crs, "EPSG:4326")
            plots.append(Field(id=f"p{c.row:03d}_{c.col:03d}", geometry=geom, props={
                "stratum": name, "stratum_size": len(pool), "fire_dist_m": round(c.fire_dist_m),
            }))
    return plots
