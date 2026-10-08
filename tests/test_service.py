from datetime import date, timedelta

import numpy as np
import pytest
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

from parali import service
from parali.area import AreaStack, encode
from parali.config import BANDS
from parali.fields import reproject
from parali.firms import Fire
from parali.messages import farmer_text, hi_date
from parali.rules import Thresholds
from parali.store import LocalStore

CRS = "EPSG:32643"
TH = Thresholds(min_valid_share=0.6, min_clear_images=4, dark_nbr=-0.15, burn_share=0.3, nir_drop=0.35,
                persist_images=2, partial_share=0.1, max_burn_brightness=0.0, fire_radius_m=500)
CROP = dict(red=0.05, green=0.07, blue=0.04, nir08=0.30, swir16=0.20, swir22=0.12)
BARE = dict(red=0.12, green=0.11, blue=0.09, nir08=0.24, swir16=0.30, swir22=0.24)
BURNT = dict(red=0.04, green=0.04, blue=0.03, nir08=0.10, swir16=0.17, swir22=0.18)


def make_stack(burn_at=None, n=10):
    tr = from_origin(500000, 3300000, 20, 20)
    dates = [date(2025, 10, 1) + timedelta(days=5 * i) for i in range(n)]
    refl = np.zeros((n, len(BANDS), 12, 12), dtype="int16")
    for t in range(n):
        v = CROP if t < 3 else BARE
        if burn_at is not None and burn_at <= t < burn_at + 2:
            v = BURNT
        for b, x in v.items():
            refl[t, BANDS.index(b)] = encode(np.full((12, 12), x, dtype="float32"))
    return AreaStack((0, 0, 1, 1), dates, CRS, tr, refl, np.full((n, 12, 12), 4, dtype="uint8"))


FIELD_GEOM = reproject(box(500040, 3299800, 500200, 3299960), CRS, "EPSG:4326")


@pytest.fixture
def store(tmp_path):
    s = LocalStore(tmp_path)
    s.put("fields", "f1", {"id": "f1", "name": "Killa 12", "farmer": "Ramesh", "village": "Test",
                           "geometry": mapping(FIELD_GEOM)})
    return s


def run(store, stack, fires=(), speaker=None):
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    return service.process_claim(store, c["id"], lambda f, a, b: stack, list(fires), TH, speaker)


def test_clean_field_auto_approved_with_evidence_and_audio(store):
    spoken = []
    c = run(store, make_stack(), speaker=lambda t: spoken.append(t) or b"mp3")
    assert c["status"] == "auto_approved"
    assert store.get_blob(c["evidence_key"]).startswith(b"\x89PNG")
    assert store.get_blob(c["audio_key"]) == b"mp3"
    assert "स्वीकृत" in spoken[0] and "Ramesh" in spoken[0]
    assert [e["type"] for e in store.events(c["id"])] == ["submitted", "decided"]


def test_burnt_field_goes_to_officer_not_rejected(store):
    c = run(store, make_stack(burn_at=4))
    assert c["status"] == "possible_burn"
    assert c["decision"]["burn_date"] == "2025-10-21"
    assert "अंतिम फ़ैसला नहीं" in c["message"]["hi"]
    assert service.queue(store)[0]["id"] == c["id"]


def test_fire_point_nearby_sends_clean_field_to_review(store):
    centre = FIELD_GEOM.centroid
    fire = Fire(centre.y, centre.x, date(2025, 10, 20), "S", "n", 3.0)
    c = run(store, make_stack(), fires=[fire])
    assert c["status"] == "needs_review"
    assert c["fires"][0]["date"] == "2025-10-20"


def test_officer_review_needs_id_and_review_state(store):
    c = run(store, make_stack(burn_at=4))
    with pytest.raises(service.WorkflowError):
        service.review(store, c["id"], "  ", "confirm_burnt")
    with pytest.raises(service.WorkflowError):
        service.review(store, c["id"], "VO-7", "reject")
    r = service.review(store, c["id"], "VO-7", "confirm_burnt", "seen on site")
    assert r["status"] == "officer_confirmed_burnt" and r["review"]["officer_id"] == "VO-7"
    with pytest.raises(service.WorkflowError):
        service.review(store, c["id"], "VO-7", "approve")
    assert store.events(c["id"])[-1]["by"] == "VO-7"


def test_auto_approved_claim_cannot_be_reviewed(store):
    c = run(store, make_stack())
    with pytest.raises(service.WorkflowError):
        service.review(store, c["id"], "VO-7", "confirm_burnt")


def test_duplicate_claim_rejected(store):
    service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    with pytest.raises(service.WorkflowError):
        service.create_claim(store, "f1", "2025-10-01", "2025-11-30")


def test_unknown_field(store):
    with pytest.raises(service.WorkflowError):
        service.create_claim(store, "nope", "2025-10-01", "2025-11-30")


def test_messages_cover_every_status():
    for s in ("submitted", "auto_approved", "needs_review", "possible_burn", "officer_approved",
              "officer_confirmed_burnt"):
        m = farmer_text({"status": s, "field_name": "K", "decision": {"rule": "partial_scar", "burn_date": "2025-11-06",
                                                                       "clear_dates": ["2025-10-01"]}})
        assert m["hi"] and m["en"]
    assert hi_date("2025-11-06") == "6 नवंबर"


def test_stack_subset_keeps_georeference():
    st = make_stack()
    sub = st.subset(reproject(box(500040, 3299840, 500120, 3299920), CRS, "EPSG:4326").bounds)
    assert sub.scl.shape[1] < st.scl.shape[1]
    x, y = sub.transform @ (0, 0)
    assert 500000 <= x <= 500060 and 3299900 <= y <= 3300000


def test_rupees_indian_grouping():
    from parali.messages import rupees
    assert [rupees(n) for n in (750, 1140, 123456, 10000000)] == ["750", "1,140", "1,23,456", "1,00,00,000"]


def test_money_lines():
    from parali.messages import advance_text, farmer_text
    base = {"field_name": "K", "decision": {"clear_dates": ["2025-10-01"]}}
    paid = {"eligible": True, "amount": 750, "status": "paid", "prev_season": "2024"}
    c = {**base, "status": "auto_approved", "advance": paid,
         "settlement": {"state": "balance_due", "balance": 2250, "recover": 0, "total": 3000}}
    t = farmer_text(c)
    assert "2,250" in t["hi"] and "750" in t["en"]
    c = {**base, "status": "officer_confirmed_burnt", "advance": paid,
         "settlement": {"state": "recover_advance", "balance": 0, "recover": 750, "total": 3000}}
    assert "वापस" in farmer_text(c)["hi"]
    no = {"eligible": False, "amount": 0, "status": "not_eligible", "prev_season": "2024"}
    c = {**base, "status": "auto_approved", "advance": no,
         "settlement": {"state": "balance_due", "balance": 3000, "recover": 0, "total": 3000}}
    assert "next year" in farmer_text(c)["en"]
    assert "advance" in advance_text({"advance": paid})["en"] and "no advance" in advance_text({"advance": no})["en"]
