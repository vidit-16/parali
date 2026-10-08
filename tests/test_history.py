from datetime import date

import numpy as np
from rasterio.transform import from_origin
from shapely.geometry import box

from parali.config import BANDS
from parali.fields import Field, reproject
from parali.history import FieldHistory, build_histories
from parali.imagery import Chip, Scene

CRS = "EPSG:32643"


def utm_field(fid, x0, y0, x1, y1):
    return Field(id=fid, geometry=reproject(box(x0, y0, x1, y1), CRS, "EPSG:4326"))


def fake_reader(scene, bbox):
    tr = from_origin(500000, 3300000, 20, 20)
    level = 0.3 if scene.date.day < 10 else 0.1
    bands = {b: np.full((20, 20), level, dtype="float32") for b in BANDS}
    return Chip(scene=scene, crs=CRS, transform=tr, bands=bands, scl=np.full((20, 20), 4, dtype="uint8"))


def scenes():
    return [Scene(f"s{d}", date(2025, 10, d), "43RFN", 0, 0, {}, {}) for d in (5, 15)]


def test_build_histories_with_fake_reader():
    # 1 m inside pixel edges: only pixels wholly inside each field should be kept
    fields = [utm_field("a", 500041, 3299761, 500239, 3299959), utm_field("b", 500001, 3299801, 500099, 3299899)]
    out = build_histories(fields, "x", "y", scenes=scenes(), reader=fake_reader, log=lambda *_: None)
    assert out["a"].values.shape == (2, len(BANDS), 64)
    assert out["b"].values.shape[2] == 9  # ~100 m field -> 3x3 whole pixels
    assert np.allclose(out["a"].band("nir08")[0], 0.3)
    assert np.allclose(out["a"].band("nir08")[1], 0.1)


def test_history_save_load_roundtrip(tmp_path):
    fields = [utm_field("a", 500040, 3299760, 500240, 3299960)]
    h = build_histories(fields, "x", "y", scenes=scenes(), reader=fake_reader, log=lambda *_: None)["a"]
    h.save(tmp_path / "a.npz")
    g = FieldHistory.load(tmp_path / "a.npz")
    assert g.dates == h.dates and g.bands == h.bands
    np.testing.assert_array_equal(g.values, h.values)
