import json

import pytest
from shapely.geometry import box, mapping

from parali.api import Deps, handle
from parali.store import LocalStore


@pytest.fixture
def deps(tmp_path):
    s = LocalStore(tmp_path)
    s.put("fields", "f1", {"id": "f1", "name": "Killa 12", "geometry": mapping(box(76.1, 29.9, 76.101, 29.901))})
    sent = []
    d = Deps(store=s, dispatch=sent.append, officer_pin="2468")
    d.sent = sent
    return d


def call(deps, method, path, body=None, headers=None):
    status, _, out = handle(method, path, json.dumps(body).encode() if body is not None else None, headers or {}, deps)
    return status, json.loads(out)


def test_create_claim_dispatches_processing(deps):
    st, c = call(deps, "POST", "/api/claims", {"field_id": "f1"})
    assert st == 201 and c["status"] == "submitted"
    assert deps.sent == [c["id"]]
    st, got = call(deps, "GET", f"/api/claims/{c['id']}")
    assert st == 200 and got["events"][0]["type"] == "submitted"


def test_duplicate_and_unknown_field_are_409(deps):
    call(deps, "POST", "/api/claims", {"field_id": "f1"})
    assert call(deps, "POST", "/api/claims", {"field_id": "f1"})[0] == 409
    assert call(deps, "POST", "/api/claims", {"field_id": "zz"})[0] == 409


def test_review_requires_pin(deps):
    _, c = call(deps, "POST", "/api/claims", {"field_id": "f1"})
    claim = deps.store.get("claims", c["id"])
    claim["status"] = "possible_burn"
    deps.store.put("claims", c["id"], claim)
    body = {"officer_id": "VO-1", "verdict": "approve"}
    assert call(deps, "POST", f"/api/claims/{c['id']}/review", body)[0] == 403
    assert call(deps, "POST", f"/api/claims/{c['id']}/review", body, {"X-Officer-Pin": "0000"})[0] == 403
    st, r = call(deps, "POST", f"/api/claims/{c['id']}/review", body, {"x-officer-pin": "2468"})
    assert st == 200 and r["status"] == "officer_approved"


def test_queue_lists_only_review_states(deps):
    _, c = call(deps, "POST", "/api/claims", {"field_id": "f1"})
    assert call(deps, "GET", "/api/queue")[1] == []
    claim = deps.store.get("claims", c["id"])
    claim["status"] = "needs_review"
    deps.store.put("claims", c["id"], claim)
    assert [x["id"] for x in call(deps, "GET", "/api/queue")[1]] == [c["id"]]


def test_bad_json_and_unknown_route(deps):
    assert handle("POST", "/api/claims", b"{", {}, deps)[0] == 400
    assert call(deps, "GET", "/api/nothing")[0] == 404
    assert call(deps, "GET", "/api/claims/../../etc")[0] == 404


def test_reset_requires_pin(deps):
    flag = []
    deps.reset = lambda: flag.append(1)
    assert call(deps, "POST", "/api/demo/reset", {})[0] == 403
    assert call(deps, "POST", "/api/demo/reset", {}, {"X-Officer-Pin": "2468"})[0] == 200
    assert flag == [1]
