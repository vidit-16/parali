import base64
import json

import pytest
from shapely.geometry import box, mapping

pytest.importorskip("boto3")
from parali import aws  # noqa: E402
from parali.store import LocalStore  # noqa: E402


@pytest.fixture
def local(tmp_path, monkeypatch):
    s = LocalStore(tmp_path)
    s.put("fields", "f1", {"id": "f1", "name": "K", "geometry": mapping(box(76.1, 29.9, 76.101, 29.901))})
    sent = []
    monkeypatch.setattr(aws, "store", lambda: s)
    monkeypatch.setattr(aws, "_dispatch", sent.append)
    monkeypatch.setenv("OFFICER_PIN", "9")
    return s, sent


def event(method, path, body=None, b64=False, headers=None):
    e = {"requestContext": {"http": {"method": method}}, "rawPath": path, "headers": headers or {}}
    if body is not None:
        raw = json.dumps(body)
        e["body"] = base64.b64encode(raw.encode()).decode() if b64 else raw
        e["isBase64Encoded"] = b64
    return e


def test_get_fields(local):
    r = aws.api_handler(event("GET", "/api/fields"), None)
    assert r["statusCode"] == 200 and json.loads(r["body"])[0]["id"] == "f1"


@pytest.mark.parametrize("b64", [False, True])
def test_post_claim_plain_and_base64(local, b64):
    s, sent = local
    r = aws.api_handler(event("POST", "/api/claims", {"field_id": "f1"}, b64=b64), None)
    assert r["statusCode"] == 201
    assert sent == [json.loads(r["body"])["id"]]


def test_review_uses_pin_from_env(local):
    r = aws.api_handler(event("POST", "/api/claims/abcdef1234/review", {"officer_id": "x", "verdict": "approve"},
                              headers={"x-officer-pin": "nope"}), None)
    assert r["statusCode"] == 403
