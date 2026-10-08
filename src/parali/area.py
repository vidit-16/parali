"""A cached stack of every scene over one study area, so fields and plots can be cut out without re-reading."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
from affine import Affine

from parali import config
from parali.fields import Field, pixel_mask
from parali.history import FieldHistory
from parali.imagery import read_chip, search_scenes

SCALE = 10000  # reflectance stored as int16 = round(r * SCALE); NODATA where missing
NODATA = -32768


@dataclass
class AreaStack:
    bbox: tuple
    dates: list[date]
    crs: str
    transform: Affine
    refl: np.ndarray  # int16 [T, B, H, W]
    scl: np.ndarray   # uint8 [T, H, W]

    def band(self, t: int, name: str) -> np.ndarray:
        a = self.refl[t, config.BANDS.index(name)].astype("float32")
        a[a == NODATA] = np.nan
        return a / SCALE

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, bbox=np.array(self.bbox), dates=np.array([d.isoformat() for d in self.dates]),
                            crs=self.crs, transform=np.array(tuple(self.transform)[:6]), refl=self.refl, scl=self.scl)

    @classmethod
    def load(cls, path: Path) -> "AreaStack":
        z = np.load(path)
        return cls(bbox=tuple(z["bbox"]), dates=[date.fromisoformat(d) for d in z["dates"]], crs=str(z["crs"]),
                   transform=Affine(*z["transform"]), refl=z["refl"], scl=z["scl"])

    def histories(self, fields: list[Field], inner_buffer_m: float = config.FIELD_INNER_BUFFER_M) -> dict[str, FieldHistory]:
        hw = self.scl.shape[1:]
        out = {}
        for f in fields:
            m = pixel_mask(f, self.crs, self.transform, hw, inner_buffer_m)
            vals = self.refl[:, :, m].astype("float32")
            vals[vals == NODATA] = np.nan
            out[f.id] = FieldHistory(f.id, list(self.dates), config.BANDS, vals / SCALE, self.scl[:, m])
        return out


def encode(r: np.ndarray) -> np.ndarray:
    out = np.round(np.nan_to_num(r, nan=0) * SCALE).clip(-32000, 32000).astype("int16")
    out[~np.isfinite(r)] = NODATA
    return out



def fetch_area(bbox, start: str, end: str, tile: str | None = None, reader=read_chip, log=print,
               workers: int = 8) -> AreaStack:
    scenes = search_scenes(bbox, start, end, tile=tile)
    log(f"{len(scenes)} scenes")
    refl, scl, dates = [], [], []
    crs = transform = shape = None
    with ThreadPoolExecutor(workers) as ex:
        for i, (s, chip) in enumerate(zip(scenes, ex.map(lambda s: reader(s, bbox), scenes)), 1):
            if crs is None:
                crs, transform, shape = str(chip.crs), chip.transform, chip.scl.shape
            if chip.scl.shape != shape:
                log(f"  skip {s.date}: grid {chip.scl.shape} != {shape}")
                continue
            refl.append(np.stack([encode(chip.bands[b]) for b in config.BANDS]))
            scl.append(chip.scl)
            dates.append(s.date)
            log(f"  {i}/{len(scenes)} {s.date}")
    return AreaStack(tuple(bbox), dates, crs, transform, np.stack(refl), np.stack(scl).astype("uint8"))