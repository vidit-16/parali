"""Per-field pixel history: every usable pixel of a field on every scene date."""
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

from parali import config
from parali.fields import Field, pixel_mask, union_bbox
from parali.imagery import Chip, read_chip, search_scenes


@dataclass
class FieldHistory:
    field_id: str
    dates: list[date]
    bands: tuple[str, ...]
    values: np.ndarray  # float32 [T, B, P] reflectance
    scl: np.ndarray     # uint8 [T, P]

    def band(self, name: str) -> np.ndarray:
        return self.values[:, self.bands.index(name), :]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, field_id=self.field_id, dates=np.array([d.isoformat() for d in self.dates]),
                            bands=np.array(self.bands), values=self.values, scl=self.scl)

    @classmethod
    def load(cls, path: Path) -> "FieldHistory":
        z = np.load(path)
        return cls(field_id=str(z["field_id"]), dates=[date.fromisoformat(d) for d in z["dates"]],
                   bands=tuple(str(b) for b in z["bands"]), values=z["values"], scl=z["scl"])


def extract(chip: Chip, masks: dict[str, np.ndarray]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Field pixels from one chip: field_id -> (values [B, P], scl [P])."""
    stack = np.stack([chip.bands[b] for b in config.BANDS])
    return {fid: (stack[:, m], chip.scl[m]) for fid, m in masks.items()}


def build_histories(fields: list[Field], start: str, end: str, tile: str | None = None,
                    scenes=None, reader=read_chip, log=print) -> dict[str, FieldHistory]:
    bbox = union_bbox(fields)
    if scenes is None:
        scenes = search_scenes(bbox, start, end, tile=tile)
    log(f"{len(scenes)} scenes")
    per_field: dict[str, list] = {f.id: [] for f in fields}
    masks = None
    for i, scene in enumerate(scenes, 1):
        chip = reader(scene, bbox)
        if masks is None:
            masks = {f.id: pixel_mask(f, chip.crs, chip.transform, chip.scl.shape) for f in fields}
        for fid, (vals, scl) in extract(chip, masks).items():
            per_field[fid].append((scene.date, vals, scl))
        log(f"  {i}/{len(scenes)} {scene.date}")
    out = {}
    for fid, rows in per_field.items():
        out[fid] = FieldHistory(
            field_id=fid,
            dates=[r[0] for r in rows],
            bands=config.BANDS,
            values=np.stack([r[1] for r in rows]).astype("float32"),
            scl=np.stack([r[2] for r in rows]).astype("uint8"),
        )
    return out
