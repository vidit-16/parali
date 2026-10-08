from datetime import date

import numpy as np
import pytest
from shapely.geometry import box

from parali import tiles


def test_tile_maths_round_trip():
    x, y = tiles.tile_of(76.14, 29.93, 11)
    w, s, e, n = tiles.tile_lonlat_bounds(x, y, 11)
    assert w <= 76.14 < e and s <= 29.93 < n
    minx, miny, maxx, maxy = tiles.tile_bounds(x, y, 11)
    px, py = tiles.lonlat_to_3857(76.14, 29.93)
    assert minx <= px < maxx and miny <= py < maxy


def test_blocks_cover_the_region_only():
    region = box(76.08, 29.88, 76.20, 29.99)
    blocks = tiles.blocks_for(region)
    assert tiles.tile_of(76.14, 29.93, 11) in blocks
    assert all(region.intersects(box(*tiles.tile_lonlat_bounds(x, y, 11))) for x, y in blocks)
    assert len(blocks) <= 4


def frame(v):
    return np.full((4, 4, 3), v, "uint8")


def test_composite_takes_median_of_clear_frames_only():
    clear = np.ones((4, 4), bool)
    cloudy = np.zeros((4, 4), bool)
    rgb, seen = tiles.composite([frame(10), frame(20), frame(250)], [clear, clear, cloudy])
    assert rgb[0, 0, 0] == 15 and seen.all()


def test_fill_gaps_carries_last_seen_and_back_fills_the_start():
    seen = np.ones((4, 4), bool)
    out = tiles.fill_gaps([(None, None), (frame(50), seen), (frame(0), np.zeros((4, 4), bool))])
    assert [o[0][0, 0, 0] for o in out] == [50, 50, 50]
    assert all(o[1].all() for o in out)


def bands(day, nir, swir, bright):
    shape = (3, 3)
    return tiles.DateBands(day, np.full(shape, nir, "float32"), np.full(shape, swir, "float32"),
                           np.full(shape, bright, "float32"))


def test_burn_day_is_first_date_with_the_signature():
    seq = [bands(date(2025, 9, 28), 0.30, 0.15, 0.10),
           bands(date(2025, 10, 20), 0.28, 0.16, 0.10),
           bands(date(2025, 11, 6), 0.12, 0.20, 0.05),   # NIR -57%, NBR -0.25, near-black
           bands(date(2025, 11, 9), 0.11, 0.20, 0.05)]
    d = tiles.burn_days(seq)
    assert (d == (date(2025, 11, 6) - tiles.DAY0).days).all()


@pytest.mark.parametrize("bright,nir", [(0.12, 0.12), (0.05, 0.25)])
def test_no_burn_when_bright_or_without_a_sharp_drop(bright, nir):
    seq = [bands(date(2025, 10, 1), 0.30, 0.15, 0.10), bands(date(2025, 11, 6), nir, 0.20, bright)]
    assert not tiles.burn_days(seq).any()


def test_cloudy_date_does_not_reset_the_reference():
    seq = [bands(date(2025, 10, 1), 0.30, 0.15, 0.10),
           bands(date(2025, 10, 5), np.nan, np.nan, 0.10),
           bands(date(2025, 11, 6), 0.12, 0.20, 0.05)]
    assert tiles.burn_days(seq).all()


def test_specks_are_dropped_patches_kept():
    d = np.zeros((10, 10), "uint8")
    d[0, 0] = 60
    d[5:8, 5:8] = 66
    out = tiles.drop_specks(d)
    assert out[0, 0] == 0 and (out[5:8, 5:8] == 66).all()


def test_block_tiles_and_pyramid(tmp_path):
    sink = tiles.DirSink(tmp_path)
    rgba = np.zeros((tiles.FULL, tiles.FULL, 4), "uint8")
    rgba[: tiles.TILE, : tiles.TILE] = (200, 100, 50, 255)   # only the top-left z14 tile has data
    n = tiles.write_block_tiles(sink, "1101", 1462, 843, rgba)
    assert n == 4  # one tile at each of z14, z13, z12, z11
    assert (tmp_path / "1101/14/11696/6744.webp").exists()
    assert not (tmp_path / "1101/14/11697/6744.webp").exists()
    assert tiles.pyramid(sink, "1101", [(1462, 843)], min_z=8) == 3
    assert (tmp_path / "1101/8/182/105.webp").exists()


def test_burn_features_are_lonlat_with_day(tmp_path):
    from rasterio.transform import from_bounds
    d = np.zeros((8, 8), "uint8")
    d[2:5, 2:5] = 66
    b = tiles.tile_bounds(1462, 843, 11)
    feats = tiles.burn_features(d, from_bounds(*b, 8, 8))
    assert len(feats) == 1 and feats[0]["properties"]["d"] == 66
    lon, lat = feats[0]["geometry"]["coordinates"][0][0]
    w, s, e, n = tiles.tile_lonlat_bounds(1462, 843, 11)
    assert w < lon < e and s < lat < n
