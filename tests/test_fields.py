from rasterio.transform import from_origin
from shapely.geometry import box

from parali.fields import Field, load_fields, pixel_mask, project, reproject, save_fields

CRS = "EPSG:32643"


def field_in_utm(x0, y0, x1, y1):
    return Field(id="f1", geometry=reproject(box(x0, y0, x1, y1), CRS, "EPSG:4326"))


def test_pixel_mask_with_inner_buffer():
    # 200 m x 200 m field on a 20 m grid -> 10x10 pixels, minus a 20 m ring -> 8x8
    tr = from_origin(500000, 3300000, 20, 20)
    f = field_in_utm(500040, 3299760, 500240, 3299960)
    m = pixel_mask(f, CRS, tr, (20, 20), inner_buffer_m=20)
    assert m.sum() == 64
    m0 = pixel_mask(f, CRS, tr, (20, 20), inner_buffer_m=0)
    assert m0.sum() == 100


def test_tiny_field_vanishes_after_buffer():
    tr = from_origin(500000, 3300000, 20, 20)
    f = field_in_utm(500040, 3299940, 500070, 3299970)
    assert pixel_mask(f, CRS, tr, (20, 20), inner_buffer_m=20).sum() == 0


def test_project_roundtrip_area():
    f = field_in_utm(500000, 3299000, 500100, 3299100)
    assert abs(project(f.geometry, CRS).area - 10000) < 5


def test_save_load(tmp_path):
    f = Field(id="k1", geometry=box(76.3, 29.7, 76.301, 29.701), props={"farmer": "Test"})
    p = tmp_path / "f.geojson"
    save_fields([f], p)
    [g] = load_fields(p)
    assert g.id == "k1" and g.props == {"farmer": "Test"}
    assert g.geometry.equals(f.geometry)
