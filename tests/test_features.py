from datetime import date

import numpy as np
import pytest

from parali.config import BANDS
from parali.features import brightness, field_features, mirbi, nbr
from parali.history import FieldHistory


def history(rows, scl=None):
    """rows: list of dicts band -> value, applied to every pixel (4 pixels)."""
    t, p = len(rows), 4
    values = np.zeros((t, len(BANDS), p), dtype="float32")
    for i, r in enumerate(rows):
        for b, v in r.items():
            values[i, BANDS.index(b), :] = v
    if scl is None:
        scl = np.full((t, p), 4, dtype="uint8")
    dates = [date(2025, 10, 1 + 3 * i) for i in range(t)]
    return FieldHistory("f", dates, BANDS, values, scl)


CROP = dict(red=0.05, green=0.07, blue=0.04, nir08=0.30, swir16=0.20, swir22=0.12)
BURNT = dict(red=0.04, green=0.04, blue=0.03, nir08=0.12, swir16=0.17, swir22=0.18)


def test_nbr_values():
    assert nbr(np.float32(0.3), np.float32(0.1)) == pytest.approx(0.5)
    assert nbr(np.float32(0.1), np.float32(0.3)) == pytest.approx(-0.5)


def test_mirbi_rises_with_char():
    assert mirbi(0.17, 0.18) > mirbi(0.20, 0.12)


def test_brightness_mean():
    assert brightness(0.1, 0.2, 0.3) == pytest.approx(0.2)


def test_field_features_crop_then_burn():
    f = field_features(history([CROP, BURNT]))
    assert f[0].nbr > 0.3
    assert f[1].nbr < -0.1
    assert f[0].dark_share == 0.0
    assert f[1].dark_share == 1.0
    assert f[1].nir < f[0].nir


def test_cloud_pixels_excluded():
    scl = np.array([[4, 4, 9, 9]], dtype="uint8")
    [d] = field_features(history([CROP], scl=scl))
    assert d.n_valid == 2 and d.valid_share == 0.5


def test_all_cloud_date_gives_nan_not_error():
    scl = np.full((1, 4), 9, dtype="uint8")
    [d] = field_features(history([CROP], scl=scl))
    assert d.n_valid == 0 and np.isnan(d.nbr)


def test_dark_area_class_not_masked():
    scl = np.full((1, 4), 2, dtype="uint8")
    [d] = field_features(history([BURNT], scl=scl))
    assert d.n_valid == 4


def test_dark_share_follows_threshold():
    rows = [CROP]
    h = history(rows)
    h.values[0, BANDS.index("nir08"), :2] = 0.10   # two pixels NBR ~ -0.09
    h.values[0, BANDS.index("nir08"), 2:] = 0.06   # two pixels NBR ~ -0.33
    [d] = field_features(h)
    assert d.dark(-0.05) == 1.0
    assert d.dark(-0.20) == 0.5
    assert d.dark(-0.40) == 0.0
    assert "nbr_px" not in d.as_dict()
