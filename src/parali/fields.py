import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from rasterio.features import geometry_mask
from shapely.geometry import mapping, shape

from parali import config


@dataclass
class Field:
    id: str
    geometry: object  # shapely polygon, lon/lat
    props: dict = field(default_factory=dict)

    @property
    def bbox(self):
        return self.geometry.bounds


def load_fields(path: str | Path) -> list[Field]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for f in data["features"]:
        props = dict(f.get("properties") or {})
        fid = str(props.pop("id"))
        out.append(Field(id=fid, geometry=shape(f["geometry"]), props=props))
    return out


def save_fields(fields: list[Field], path: str | Path) -> None:
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"id": f.id, **f.props}, "geometry": mapping(f.geometry)}
        for f in fields
    ]}
    Path(path).write_text(json.dumps(fc, indent=1), encoding="utf-8")


def union_bbox(fields: list[Field], pad_deg: float = 0.002):
    xs0, ys0, xs1, ys1 = zip(*(f.bbox for f in fields))
    return (min(xs0) - pad_deg, min(ys0) - pad_deg, max(xs1) + pad_deg, max(ys1) + pad_deg)


def reproject(geom, src, dst):
    t = Transformer.from_crs(src, dst, always_xy=True)
    return shapely.transform(geom, lambda x, y: t.transform(x, y), interleaved=False)


def project(geom, crs):
    return reproject(geom, "EPSG:4326", crs)


def pixel_mask(f: Field, crs, transform, shape_hw, inner_buffer_m: float = config.FIELD_INNER_BUFFER_M):
    """Boolean array, True for pixels whose centre lies inside the field shrunk by inner_buffer_m."""
    g = project(f.geometry, crs)
    if inner_buffer_m:
        g = g.buffer(-inner_buffer_m)
    if g.is_empty:
        return np.zeros(shape_hw, dtype=bool)
    return geometry_mask([mapping(g)], out_shape=shape_hw, transform=transform, invert=True)
