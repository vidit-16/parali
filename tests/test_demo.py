"""Runs every demo field through the real pipeline on the committed 2025 data."""
import json

import pytest

from parali import server
from parali.api import handle


@pytest.fixture
def deps(tmp_path, monkeypatch):
    d = server.make_deps(tmp_path, officer_pin="1")
    ran = []
    d.dispatch = ran.append
    d.ran = ran
    return d


def call(deps, method, path, body=None, pin=None):
    status, _, out = handle(method, path, json.dumps(body).encode() if body else None,
                            {"X-Officer-Pin": pin} if pin else {}, deps)
    return status, json.loads(out)


def test_every_demo_field_gets_a_decision(deps):
    from parali import firms, service
    from parali.rules import Thresholds
    fields = call(deps, "GET", "/api/fields")[1]
    assert len(fields) >= 5
    th = Thresholds.load()
    fires = firms.load(server.ROOT / "data" / "firms" / "kaithal_2025.csv")
    stacks = server.demo_stacks(server.DEMO / "stacks")
    outcomes = {}
    for f in fields:
        _, c = call(deps, "POST", "/api/claims", {"field_id": f["id"]})
        done = service.process_claim(deps.store, c["id"], stacks, fires, th)
        outcomes[f["id"]] = done["status"]
        assert done["message"]["hi"] and done["evidence_key"]
        assert deps.store.get_blob(done["evidence_key"]).startswith(b"\x89PNG")
    # the demo needs one of each: approved, sent to officer, possible burn
    assert {"auto_approved", "needs_review", "possible_burn"} <= set(outcomes.values())
    assert outcomes["f-satbir"] == "needs_review"   # fire point nearby, clean field


def test_reset_clears_claims(deps):
    call(deps, "POST", "/api/claims", {"field_id": "f-satbir"})
    assert call(deps, "GET", "/api/claims")[1]
    assert call(deps, "POST", "/api/demo/reset", {}, pin="1")[0] == 200
    assert call(deps, "GET", "/api/claims")[1] == []
    assert call(deps, "GET", "/api/fields")[1]
