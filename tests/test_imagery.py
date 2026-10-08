from datetime import date

import numpy as np
import pytest

from parali.imagery import Scene, dedupe_by_date, to_reflectance, valid_mask


def scene(d, nodata=0.0, cloud=0.0, sid="x"):
    return Scene(id=sid, date=d, tile="43RFN", cloud_cover=cloud, nodata_pct=nodata, hrefs={}, scale_offset={})


def test_reflectance_applies_scale_and_offset():
    dn = np.array([1000, 3500, 11000], dtype="uint16")
    r = to_reflectance(dn, 0.0001, -0.1)
    np.testing.assert_allclose(r, [0.0, 0.25, 1.0], atol=1e-6)


def test_reflectance_zero_dn_is_nodata():
    r = to_reflectance(np.array([0, 2000], dtype="uint16"), 0.0001, -0.1)
    assert np.isnan(r[0])
    assert r[1] == pytest.approx(0.1, abs=1e-6)


def test_dedupe_keeps_least_nodata_then_least_cloud():
    d = date(2025, 11, 9)
    a = scene(d, nodata=30, cloud=0, sid="a")
    b = scene(d, nodata=0, cloud=20, sid="b")
    c = scene(d, nodata=0, cloud=5, sid="c")
    other = scene(date(2025, 11, 4), sid="o")
    out = dedupe_by_date([a, b, c, other])
    assert [s.id for s in out] == ["o", "c"]


def test_valid_mask_keeps_dark_and_shadow_classes():
    scl = np.array([0, 1, 2, 3, 4, 5, 8, 9, 10])
    bands = {"nir08": np.ones(9, dtype="float32")}
    ok = valid_mask(bands, scl)
    assert ok.tolist() == [False, False, True, True, True, True, False, False, False]


def test_valid_mask_drops_nan_pixels():
    scl = np.array([4, 4])
    bands = {"nir08": np.array([0.3, np.nan], dtype="float32")}
    assert valid_mask(bands, scl).tolist() == [True, False]
