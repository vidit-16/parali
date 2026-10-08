"""Score the rules and the FIRMS-only baseline against hand labels.

Plots were sampled in strata, so every count is weighted by stratum_size / labelled_in_stratum to
estimate rates for the whole study area. Plots labelled "unsure" are left out of accuracy and
reported separately.
"""
import itertools
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import date

from parali.features import DateFeatures, field_features
from parali.fields import Field
from parali.firms import Fire, distance_m
from parali.history import FieldHistory
from parali.rules import APPROVED, POSSIBLE_BURN, REVIEW, Thresholds, decide


@dataclass
class Case:
    plot: Field
    label: str            # burnt / not_burnt / unsure
    feats: list[DateFeatures]
    fire_dist_m: float    # nearest fire point inside the claim window (inf if none)
    weight: float

    def fires_within(self, radius_m: float) -> int:
        return int(self.fire_dist_m <= radius_m)


BASELINE_RADIUS_M = 375  # half a VIIRS pixel plus a little geolocation slack


def build_cases(plots: list[Field], labels: dict[str, str], hist: dict[str, FieldHistory], fires: list[Fire],
                start: date, end: date) -> list[Case]:
    lab = [p for p in plots if p.id in labels]
    per_stratum = Counter(p.props["stratum"] for p in lab)
    cases = []
    for p in lab:
        c = p.geometry.centroid
        cases.append(Case(
            plot=p,
            label=labels[p.id],
            feats=field_features(hist[p.id]),
            fire_dist_m=nearest_fire_m(fires, c.y, c.x, start, end),
            weight=p.props["stratum_size"] / per_stratum[p.props["stratum"]],
        ))
    return cases


def nearest_fire_m(fires: list[Fire], lat: float, lon: float, start: date, end: date) -> float:
    sel = [f for f in fires if start <= f.date <= end]
    if not sel:
        return float("inf")
    return float(distance_m(lat, lon, [f.lat for f in sel], [f.lon for f in sel]).min())


def _rates(pairs):
    """pairs: (truth_burnt: bool, flagged: bool, weight)."""
    tp = sum(w for t, f, w in pairs if t and f)
    fp = sum(w for t, f, w in pairs if not t and f)
    fn = sum(w for t, f, w in pairs if t and not f)
    tn = sum(w for t, f, w in pairs if not t and not f)
    return {
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "wrongful_burnt_rate": fp / (fp + tn) if fp + tn else None,
    }


def score(cases: list[Case], th: Thresholds, start: date, end: date) -> dict:
    sure = [c for c in cases if c.label in ("burnt", "not_burnt")]
    outcomes = {c.plot.id: decide(c.feats, th, c.fires_within(th.fire_radius_m), start, end).outcome for c in sure}
    total_w = sum(c.weight for c in sure) or 1.0
    share = defaultdict(float)
    for c in sure:
        share[outcomes[c.plot.id]] += c.weight / total_w
    burnt_w = sum(c.weight for c in sure if c.label == "burnt")
    leak = sum(c.weight for c in sure if c.label == "burnt" and outcomes[c.plot.id] == APPROVED)
    rules = _rates([(c.label == "burnt", outcomes[c.plot.id] == POSSIBLE_BURN, c.weight) for c in sure])
    caught = _rates([(c.label == "burnt", outcomes[c.plot.id] != APPROVED, c.weight) for c in sure])
    baseline = _rates([(c.label == "burnt", c.fires_within(BASELINE_RADIUS_M) > 0, c.weight) for c in sure])
    return {
        "labelled": len(cases),
        "used": len(sure),
        "unsure": len(cases) - len(sure),
        "burnt_labels": sum(c.label == "burnt" for c in sure),
        "est_burnt_share": burnt_w / total_w,
        "auto_approved_share": share[APPROVED],
        "review_share": share[REVIEW],
        "possible_burn_share": share[POSSIBLE_BURN],
        "burnt_auto_approved": leak / burnt_w if burnt_w else None,
        "rules_possible_burn": rules,
        "rules_not_auto_approved": caught,
        "firms_baseline": baseline,
        "outcomes": outcomes,
    }


GRID = {
    "dark_nbr": (-0.10, -0.15, -0.20, -0.25),
    "burn_share": (0.3, 0.5),
    "nir_drop": (0.25, 0.35, 0.45),
    "max_burn_brightness": (0.0, 0.06, 0.08),
    "fire_radius_m": (0, 375, 750),
}


def objective(s: dict) -> float:
    """Higher is better. Missing a burn costs money; flagging a clean farmer costs trust and a red
    entry. Both matter, review is the cheap middle."""
    r = s["rules_possible_burn"]
    if r["recall"] is None or r["wrongful_burnt_rate"] is None:
        return float("-inf")
    leak = s["burnt_auto_approved"] or 0.0
    return r["recall"] - 3 * r["wrongful_burnt_rate"] - 2 * leak - 0.5 * s["review_share"]


def fit(cases: list[Case], base: Thresholds, start: date, end: date, grid=GRID) -> tuple[Thresholds, dict]:
    keys = list(grid)
    best = None
    for vals in itertools.product(*(grid[k] for k in keys)):
        th = replace(base, **dict(zip(keys, vals)))
        s = score(cases, th, start, end)
        o = objective(s)
        if best is None or o > best[0]:
            best = (o, th, s)
    return best[1], best[2]


def split(cases: list[Case], k: int = 2) -> list[list[Case]]:
    """Deterministic folds by plot id, so the same plot always lands in the same fold."""
    folds = [[] for _ in range(k)]
    for c in sorted(cases, key=lambda c: c.plot.id):
        folds[sum(map(ord, c.plot.id)) % k].append(c)
    return folds


def cross_validate(cases: list[Case], base: Thresholds, start: date, end: date, grid=GRID) -> list[dict]:
    """Fit on one half, score on the other, both ways. Reported numbers come from held-out plots."""
    a, b = split(cases)
    out = []
    for train, test in ((a, b), (b, a)):
        th, _ = fit(train, base, start, end, grid)
        out.append({"thresholds": th, "test": score(test, th, start, end)})
    return out
