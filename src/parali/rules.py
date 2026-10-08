"""Fixed rules that turn a field's features into a decision. No model is involved.

The system can approve or refer. It never rejects: a burn finding is "possible_burn" and an
officer has to confirm it.
"""
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from parali import config
from parali.features import DateFeatures

APPROVED = "auto_approved"
REVIEW = "needs_review"
POSSIBLE_BURN = "possible_burn"

RULES_FILE = Path(__file__).with_name("rules.toml")


@dataclass(frozen=True)
class Thresholds:
    min_valid_share: float
    min_clear_images: int
    dark_nbr: float
    burn_share: float
    nir_drop: float
    persist_images: int
    partial_share: float
    max_burn_brightness: float
    fire_radius_m: float

    @classmethod
    def load(cls, path: Path = RULES_FILE) -> "Thresholds":
        return cls(**tomllib.loads(path.read_text(encoding="utf-8")))


@dataclass
class Decision:
    outcome: str
    rule: str
    reason: str
    burn_date: date | None = None
    clear_dates: list[date] = field(default_factory=list)
    max_dark_share: float = 0.0
    fires_nearby: int = 0

    def as_dict(self):
        return {
            "outcome": self.outcome,
            "rule": self.rule,
            "reason": self.reason,
            "burn_date": self.burn_date.isoformat() if self.burn_date else None,
            "clear_dates": [d.isoformat() for d in self.clear_dates],
            "max_dark_share": round(self.max_dark_share, 3),
            "fires_nearby": self.fires_nearby,
        }


def clear_images(feats: list[DateFeatures], th: Thresholds) -> list[DateFeatures]:
    return [f for f in feats if f.n_valid >= config.MIN_FIELD_PIXELS and f.valid_share >= th.min_valid_share]


def burn_events(clear: list[DateFeatures], th: Thresholds) -> list[tuple[int, bool]]:
    """Indexes into `clear` where a burn-like step happens, with whether it persists."""
    out = []
    for i in range(1, len(clear)):
        a, b = clear[i - 1], clear[i]
        if a.nir <= 0:
            continue
        drop = (a.nir - b.nir) / a.nir
        dark = b.dark(th.dark_nbr) >= th.burn_share
        if th.max_burn_brightness > 0:
            dark = dark and b.brightness <= th.max_burn_brightness
        if drop >= th.nir_drop and dark:
            after = clear[i:i + th.persist_images]
            persists = len(after) == th.persist_images and all(x.dark(th.dark_nbr) >= th.burn_share for x in after)
            out.append((i, persists))
    return out


def decide(feats: list[DateFeatures], th: Thresholds, fires_nearby: int = 0,
           start: date | None = None, end: date | None = None) -> Decision:
    """feats should include images from before the window so the first step can be seen."""
    inside = [f for f in feats if (start is None or f.date >= start) and (end is None or f.date <= end)]
    if inside and inside[0].n_pixels < config.MIN_FIELD_PIXELS:
        return Decision(REVIEW, "field_too_small",
                        f"Field has {inside[0].n_pixels} usable pixels at 20 m; at least {config.MIN_FIELD_PIXELS} needed.",
                        fires_nearby=fires_nearby)

    clear_all = clear_images(feats, th)
    in_dates = {f.date for f in inside}
    clear_in = [f for f in clear_all if f.date in in_dates]
    max_dark = max((f.dark(th.dark_nbr) for f in clear_in), default=0.0)
    base = dict(clear_dates=[f.date for f in clear_in], max_dark_share=max_dark, fires_nearby=fires_nearby)

    if len(clear_in) < th.min_clear_images:
        return Decision(REVIEW, "too_few_clear_images",
                        f"{len(clear_in)} clear images in the claim window; {th.min_clear_images} needed.", **base)

    events = [(clear_all[i], p) for i, p in burn_events(clear_all, th) if clear_all[i].date in in_dates]
    lasting = [e for e, p in events if p]
    if lasting:
        e = lasting[0]
        return Decision(POSSIBLE_BURN, "burn_scar_persistent",
                        f"NIR fell sharply and {e.dark(th.dark_nbr):.0%} of the field stayed dark from {e.date}. "
                        "Officer to confirm.", burn_date=e.date, **base)
    if events:
        e = events[0][0]
        return Decision(REVIEW, "dark_on_one_image",
                        f"Burn-like change on {e.date} that does not persist on the next clear image.",
                        burn_date=e.date, **base)
    if max_dark >= th.partial_share:
        return Decision(REVIEW, "partial_scar",
                        f"Up to {max_dark:.0%} of the field looked dark; below the {th.burn_share:.0%} burn level.", **base)
    if fires_nearby:
        return Decision(REVIEW, "fire_point_nearby_no_scar",
                        f"{fires_nearby} satellite fire point(s) within {th.fire_radius_m:.0f} m, but no burn scar on the field.",
                        **base)
    return Decision(APPROVED, "no_burn_signal",
                    f"{len(clear_in)} clear images, no burn-like change, no fire point nearby.", **base)
