from dataclasses import asdict, dataclass, field
from datetime import date

import numpy as np

from parali import config
from parali.history import FieldHistory


def nbr(nir, swir2):
    with np.errstate(divide="ignore", invalid="ignore"):
        return (nir - swir2) / (nir + swir2)


def mirbi(swir1, swir2):
    return 10 * swir2 - 9.8 * swir1 + 2


def brightness(red, green, blue):
    return (red + green + blue) / 3


def usable(values: np.ndarray, scl: np.ndarray) -> np.ndarray:
    """values [B, P], scl [P] -> bool [P]."""
    return np.isfinite(values).all(axis=0) & ~np.isin(scl, config.SCL_MASKED)


@dataclass
class DateFeatures:
    date: date
    n_pixels: int
    n_valid: int
    nir: float
    swir1: float
    swir2: float
    nbr: float
    mirbi: float
    brightness: float
    dark_share: float  # share of valid pixels with NBR below -0.10, kept for display
    nbr_px: np.ndarray | None = field(default=None, repr=False, compare=False)
    bright_px: np.ndarray | None = field(default=None, repr=False, compare=False)

    def dark(self, threshold: float, max_bright: float = 0.0) -> float:
        """Share of valid pixels with NBR below threshold and, if max_bright > 0, visible brightness at or
        below max_bright. Char is near-black; bare dry soil can have low NBR but stays bright."""
        if self.nbr_px is None:
            return self.dark_share
        if not self.nbr_px.size:
            return 0.0
        hit = self.nbr_px < threshold
        if max_bright > 0 and self.bright_px is not None:
            hit &= self.bright_px <= max_bright
        return float(np.mean(hit))

    @property
    def valid_share(self) -> float:
        return self.n_valid / self.n_pixels if self.n_pixels else 0.0

    def as_dict(self):
        d = asdict(self)
        d.pop("nbr_px")
        d.pop("bright_px")
        d["date"] = self.date.isoformat()
        d["valid_share"] = round(self.valid_share, 3)
        return d


def field_features(h: FieldHistory, dark_nbr: float = -0.10) -> list[DateFeatures]:
    out = []
    bi = {b: i for i, b in enumerate(h.bands)}
    for t, d in enumerate(h.dates):
        v = h.values[t]
        ok = usable(v, h.scl[t])
        n = int(ok.sum())
        if n == 0:
            out.append(DateFeatures(d, v.shape[1], 0, *([float("nan")] * 6), 0.0))
            continue
        nir, s1, s2 = v[bi["nir08"], ok], v[bi["swir16"], ok], v[bi["swir22"], ok]
        px_nbr = nbr(nir, s2)
        px_bright = brightness(v[bi["red"], ok], v[bi["green"], ok], v[bi["blue"], ok])
        out.append(DateFeatures(
            date=d,
            n_pixels=v.shape[1],
            n_valid=n,
            nir=float(np.median(nir)),
            swir1=float(np.median(s1)),
            swir2=float(np.median(s2)),
            nbr=float(np.median(px_nbr)),
            mirbi=float(np.median(mirbi(s1, s2))),
            brightness=float(np.median(px_bright)),
            dark_share=float(np.mean(px_nbr < dark_nbr)),
            nbr_px=px_nbr.astype("float32"),
            bright_px=px_bright.astype("float32"),
        ))
    return out
