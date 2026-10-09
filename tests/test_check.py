import pytest
from shapely.geometry import box, mapping

from parali import check
from parali.fields import reproject
from parali.store import LocalStore
from tests.test_service import CRS, FIELD_GEOM, TH, make_stack


def stacks(burn_this_year=None):
    def provider(field, start, end):
        st = make_stack(burn_at=burn_this_year if start.year == 2025 else None)
        st.dates = [d.replace(year=start.year) for d in st.dates]
        return st
    return provider


def test_validate_accepts_a_field():
    g, ha = check.validate(mapping(FIELD_GEOM))
    assert 2.0 < ha < 3.0


@pytest.mark.parametrize("geom,msg", [
    (mapping(box(80.0, 20.0, 80.002, 20.002)), "Punjab and Haryana"),
    (mapping(reproject(box(500040, 3299800, 500060, 3299820), CRS, "EPSG:4326")), "between"),
    (mapping(reproject(box(500000, 3299000, 501000, 3300000), CRS, "EPSG:4326")), "between"),
    ({"type": "Point", "coordinates": [76.1, 29.9]}, "outline"),
    ({"type": "Polygon"}, "valid polygon"),
])
def test_validate_rejects(geom, msg):
    with pytest.raises(check.CheckError, match=msg):
        check.validate(geom)


def test_run_gives_both_seasons_and_advance(tmp_path):
    s = LocalStore(tmp_path)
    item = check.create(s, mapping(FIELD_GEOM))
    done = check.run(s, item["id"], stacks(burn_this_year=4), [], TH)
    assert done["status"] == "done"
    assert done["result"]["previous"]["decision"]["outcome"] == "auto_approved"
    assert done["result"]["current"]["decision"]["outcome"] == "possible_burn"
    assert done["advance_eligible"] is True
    assert s.get_blob(done["result"]["current"]["evidence_key"]).startswith(b"\x89PNG")


def test_api_check_flow(tmp_path):
    import json

    from parali.api import Deps, handle
    s = LocalStore(tmp_path)
    ran = []
    deps = Deps(store=s, dispatch=lambda _: None, dispatch_check=ran.append)
    st, _, out = handle("POST", "/api/check", json.dumps({"geometry": mapping(FIELD_GEOM)}).encode(), {}, deps)
    item = json.loads(out)
    assert st == 201 and ran == [item["id"]]
    check.run(s, item["id"], stacks(), [], TH)
    st, _, out = handle("GET", f"/api/check/{item['id']}", None, {}, deps)
    got = json.loads(out)
    assert st == 200 and got["result"]["current"]["evidence_url"].startswith("/blobs/")
    st, _, out = handle("POST", "/api/check", json.dumps({"geometry": {"type": "Point", "coordinates": [0, 0]}}).encode(), {}, deps)
    assert st == 400


def test_run_records_its_stages(tmp_path):
    seen = []

    class Spy(LocalStore):
        def put(self, kind, key, item):
            if kind == "checks":
                seen.append(item.get("stage") or item["status"])
            super().put(kind, key, item)

    s = Spy(tmp_path)
    item = check.create(s, mapping(FIELD_GEOM))
    done = check.run(s, item["id"], stacks(), [], TH)
    assert seen[-3:] == ["current", "previous", "done"]
    assert done["clear_images"] > 0 and "stage" not in done
