from datetime import date
from unittest.mock import patch

import numpy as np
from rasterio.transform import from_origin
from shapely.geometry import box

from parali.area import NODATA, AreaStack, encode, fetch_area
from parali.config import BANDS
from parali.fields import Field, reproject
from parali.imagery import Chip, Scene

CRS = "EPSG:32643"


def fake_reader(scene, bbox):
    tr = from_origin(500000, 3300000, 20, 20)
    bands = {b: np.full((10, 10), 0.2 if scene.date.day == 1 else 0.05, dtype="float32") for b in BANDS}
    bands["nir08"][0, 0] = np.nan
    return Chip(scene, CRS, tr, bands, np.full((10, 10), 4, dtype="uint8"))


def scenes(*a, **k):
    return [Scene(f"s{d}", date(2025, 11, d), "T", 0, 0, {}, {}) for d in (1, 9)]


def test_encode_roundtrip_and_nodata():
    r = np.array([0.1234, np.nan, -0.05], dtype="float32")
    e = encode(r)
    assert e.tolist() == [1234, NODATA, -500]


def test_fetch_area_and_histories(tmp_path):
    with patch("parali.area.search_scenes", scenes):
        st = fetch_area((0, 0, 1, 1), "a", "b", reader=fake_reader, log=lambda *_: None, workers=2)
    assert st.refl.shape == (2, len(BANDS), 10, 10)
    assert np.isnan(st.band(0, "nir08")[0, 0])
    assert st.band(1, "red")[5, 5] == np.float32(0.05)

    st.save(tmp_path / "a.npz")
    st2 = AreaStack.load(tmp_path / "a.npz")
    assert st2.dates == st.dates and st2.transform == st.transform

    f = Field("p1", reproject(box(500020, 3299820, 500120, 3299920), CRS, "EPSG:4326"))
    h = st2.histories([f], inner_buffer_m=0)["p1"]
    assert h.values.shape == (2, len(BANDS), 25)
    assert np.allclose(h.band("red")[0], 0.2)
