from datetime import date

import numpy as np
from rasterio.transform import from_origin

from parali.area import AreaStack, encode
from parali.config import BANDS
from parali.firms import Fire
from parali.label import plot_window, read_labels, write_labels
from parali.plots import sample_plots

CRS = "EPSG:32643"


def stack(h=40, w=40):
    tr = from_origin(500000, 3300000, 20, 20)
    t = 2
    refl = np.zeros((t, len(BANDS), h, w), dtype="int16")
    vals = dict(red=0.05, green=0.07, blue=0.04, nir08=0.35, swir16=0.2, swir22=0.12)
    for b, v in vals.items():
        refl[:, BANDS.index(b)] = encode(np.full((h, w), v, dtype="float32"))
    # right half is bare in early October -> not cropland
    refl[:, BANDS.index("nir08"), :, w // 2:] = encode(np.full((h, w // 2), 0.15, dtype="float32"))
    scl = np.full((t, h, w), 4, dtype="uint8")
    return AreaStack((0, 0, 1, 1), [date(2025, 10, 5), date(2025, 10, 10)], CRS, tr, refl, scl)


def fire_at(st, row, col):
    from parali.fields import reproject
    from shapely.geometry import Point
    x, y = st.transform @ (col, row)
    p = reproject(Point(x, y), CRS, "EPSG:4326")
    return Fire(p.y, p.x, date(2025, 11, 1), "S", "n", 1.0)


def test_sample_plots_only_on_cropland_with_strata():
    st = stack()
    plots = sample_plots(st, [fire_at(st, 2, 2)], per_stratum=5, cells=4)
    assert plots
    for p in plots:
        r, c = map(int, p.id[1:].split("_"))
        assert c < 5  # cell column in left (cropland) half: 40 px / 4 = 10 cells, half = 5
    strata = {p.props["stratum"] for p in plots}
    assert "on" in strata
    near = [p for p in plots if p.props["stratum"] == "on"]
    assert all(p.props["fire_dist_m"] < 400 for p in near)
    assert all(p.props["stratum_size"] >= len(near) for p in near)


def test_sampling_is_reproducible():
    st = stack()
    f = [fire_at(st, 2, 2)]
    a = [p.id for p in sample_plots(st, f, per_stratum=3, cells=4, seed=1)]
    b = [p.id for p in sample_plots(st, f, per_stratum=3, cells=4, seed=1)]
    assert a == b


def test_plot_window_matches_cells():
    st = stack()
    p = sample_plots(st, [fire_at(st, 2, 2)], per_stratum=1, cells=4)[0]
    r, c = map(int, p.id[1:].split("_"))
    (pr0, pc0, pr1, pc1), _ = plot_window(st, p, pad=5)
    assert (pr0, pc0, pr1, pc1) == (r * 4, c * 4, r * 4 + 4, c * 4 + 4)


def test_labels_roundtrip(tmp_path):
    p = tmp_path / "labels.csv"
    assert read_labels(p) == {}
    write_labels(p, {"p2": "burnt", "p1": "unsure"})
    assert read_labels(p) == {"p1": "unsure", "p2": "burnt"}


def test_signal_strata_split_existing_and_add_from_signal():
    from parali.plots import add_signal_strata
    st = stack(h=40, w=40)
    # add a late date where the top-left 8x8 cropland pixels turn near-black after a NIR drop
    import numpy as np
    from datetime import date as _d
    new = st.refl[-1:].copy()
    for b, v in dict(red=0.03, green=0.03, blue=0.03, nir08=0.10, swir16=0.17, swir22=0.18).items():
        new[0, BANDS.index(b), :8, :8] = encode(np.full((8, 8), v, dtype="float32"))
    st.refl = np.concatenate([st.refl, new])
    st.scl = np.concatenate([st.scl, st.scl[-1:]])
    st.dates = st.dates + [_d(2025, 11, 5)]
    fires = [fire_at(st, 2, 2)]
    old = sample_plots(st, fires, per_stratum=2, cells=4)
    out = add_signal_strata(st, fires, old, extra=4, cells=4)
    assert len(out) > len(old)
    added = [p for p in out if p.props.get("round") == 2]
    assert added and all(p.props["stratum"].endswith("+sig") for p in added)
    for p in added:
        r, c = map(int, p.id[1:].split("_"))
        assert r < 2 and c < 2  # only the burnt 8x8 corner = 2x2 cells
    assert len({p.id for p in out}) == len(out)
