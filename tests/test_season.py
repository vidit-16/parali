import pytest

from parali import season, service
from parali.store import LocalStore
from tests.test_service import FIELD_GEOM, TH, make_stack

from shapely.geometry import mapping


def test_amounts():
    assert season.full_amount(2.5) == 2500
    assert season.advance_amount(2.5) == 1250


def test_rates_follow_the_state_scheme(monkeypatch):
    monkeypatch.setitem(season.SCHEMES, "HR", season.Scheme("Haryana", 1200, 0.25, "test"))
    assert season.full_amount(2.5, "HR") == 3000 and season.advance_amount(2.5, "HR") == 750
    assert season.full_amount(2.5, "XX") == season.full_amount(2.5)  # unknown state falls back to the default


@pytest.mark.parametrize("prev,ok", [("auto_approved", True), ("officer_approved", True), ("needs_review", False),
                                     ("possible_burn", False), ("officer_confirmed_burnt", False), (None, False)])
def test_advance_only_after_a_clean_season(prev, ok):
    assert season.advance_eligible(prev) is ok


@pytest.mark.parametrize("acres,amount", [(1.9, 5000), (2.0, 10000), (4.9, 10000), (5.0, 30000)])
def test_compensation_tiers(acres, amount):
    assert season.environmental_compensation(acres) == amount


def test_settle_clean_pays_balance_minus_advance():
    s = season.settle("auto_approved", 2.5, 1250)
    assert s["state"] == "balance_due" and s["balance"] == 1250 and s["recover"] == 0


def test_settle_confirmed_burn_recovers_advance():
    s = season.settle("officer_confirmed_burnt", 2.5, 1250)
    assert s["state"] == "recover_advance" and s["recover"] == 1250 and s["balance"] == 0


def test_settle_confirmed_burn_without_advance_has_nothing_to_recover():
    assert season.settle("officer_confirmed_burnt", 2.5, 0)["state"] == "not_payable"


def test_settle_never_final_while_pending():
    for st in ("submitted", "needs_review", "possible_burn"):
        assert season.settle(st, 2.5, 750)["state"] == "pending"


@pytest.fixture
def store(tmp_path):
    s = LocalStore(tmp_path)
    s.put("fields", "f1", {"id": "f1", "name": "Killa 12", "farmer": "Ramesh", "acres": 2.5,
                           "geometry": mapping(FIELD_GEOM)})
    return s


def stacks_by_year(prev_burn, this_burn):
    def provider(field, start, end):
        st = make_stack(burn_at=prev_burn if start.year == 2024 else this_burn)
        st.dates = [d.replace(year=start.year) for d in st.dates]
        return st
    return provider


def run(store, prev_burn=None, this_burn=None, pay=True):
    st = stacks_by_year(prev_burn, this_burn)
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    service.assess_advance(store, c["id"], st, [], TH, "2024-10-01", "2024-11-30")
    if pay and store.get("claims", c["id"])["advance"]["eligible"]:
        service.disburse_advance(store, c["id"], "dept")
    return service.process_claim(store, c["id"], st, [], TH)


def test_clean_last_season_gets_advance_then_balance(store):
    c = run(store)
    assert c["advance"]["eligible"] and c["advance"]["status"] == "paid" and c["advance"]["amount"] == 1250
    assert c["status"] == "auto_approved"
    assert {k: c["settlement"][k] for k in ("state", "balance", "recover", "total")} == {"state": "balance_due", "balance": 1250, "recover": 0, "total": 2500}
    assert c["settlement"]["released_at"]


def test_burnt_last_season_gets_no_advance(store):
    c = run(store, prev_burn=4)
    assert not c["advance"]["eligible"] and c["advance"]["status"] == "not_eligible"
    assert c["advance"]["prev_outcome"] == "possible_burn"
    assert c["settlement"]["balance"] == 2500


def test_cannot_disburse_without_offer(store):
    st = stacks_by_year(4, None)
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    service.assess_advance(store, c["id"], st, [], TH, "2024-10-01", "2024-11-30")
    with pytest.raises(service.WorkflowError):
        service.disburse_advance(store, c["id"], "dept")


def test_confirmed_burn_after_advance_drafts_recovery_notice(store):
    c = run(store, this_burn=4)
    assert c["status"] == "possible_burn" and c["settlement"]["state"] == "pending"
    assert "notice_key" not in c  # nothing drafted until an officer confirms
    r = service.review(store, c["id"], "VO-7", "confirm_burnt", "visited 8 Nov")
    assert r["settlement"]["state"] == "recover_advance" and r["settlement"]["recover"] == 1250
    html = store.get_blob(r["notice_key"]).decode()
    assert "DRAFT FOR OFFICER REVIEW" in html and "₹1,250" in html and "VO-7" in html
    assert "अग्रिम राशि" in html and "ਅਗਾਊਂ ਰਕਮ" in html  # Punjab farmer: Hindi and Punjabi
    assert "not issued by any government office" in html


def test_officer_clears_possible_burn_releases_balance(store):
    c = run(store, this_burn=4)
    r = service.review(store, c["id"], "VO-7", "approve", "site visit: baler used")
    assert r["settlement"]["state"] == "balance_due" and r["settlement"]["balance"] == 1250
    assert "notice_key" not in r


def test_run_season_twice_is_safe(store):
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    first = service.run_season(store, c["id"], stacks_by_year(None, None), [], TH)
    again = service.run_season(store, c["id"], stacks_by_year(None, None), [], TH)
    c = first
    assert again["advance"]["status"] == "paid" and again["status"] == c["status"]
    paid = [e for e in store.events(c["id"]) if e["type"] == "advance_paid"]
    assert len(paid) == 1


def test_release_and_recovery_are_on_the_record(store):
    c = run(store, this_burn=None)
    assert [e for e in store.events(c["id"]) if e["type"] == "balance_released"][0]["amount"] == 1250
    c2 = service.create_claim(store, "f1", "2026-10-01", "2026-11-30")
    st = stacks_by_year(None, 4)
    service.assess_advance(store, c2["id"], st, [], TH, "2024-10-01", "2024-11-30")
    service.disburse_advance(store, c2["id"], "dept")
    service.process_claim(store, c2["id"], st, [], TH)
    r = service.review(store, c2["id"], "VO-7", "confirm_burnt", "seen on site")
    assert r["settlement"]["state"] == "recover_advance"
    assert any(e["type"] == "recovery_notice" for e in store.events(c2["id"]))


def test_appeal_reopens_a_confirmed_burn(store):
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    st = stacks_by_year(None, 4)
    service.assess_advance(store, c["id"], st, [], TH, "2024-10-01", "2024-11-30")
    service.disburse_advance(store, c["id"], "dept")
    service.process_claim(store, c["id"], st, [], TH)
    service.review(store, c["id"], "VO-7", "confirm_burnt")
    with pytest.raises(service.WorkflowError):
        service.appeal(store, c["id"], "  ")
    a = service.appeal(store, c["id"], "I used a happy seeder; the dark patch is wet soil")
    assert a["status"] == "needs_review" and a["settlement"]["state"] == "pending"
    assert service.queue(store)[0]["id"] == c["id"]


def test_appeal_rewrites_the_farmers_message(store):
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    st = stacks_by_year(None, 4)
    service.assess_advance(store, c["id"], st, [], TH, "2024-10-01", "2024-11-30")
    service.disburse_advance(store, c["id"], "dept")
    service.process_claim(store, c["id"], st, [], TH)
    r = service.review(store, c["id"], "VO-7", "confirm_burnt")
    assert "returned" in r["message"]["en"]
    a = service.appeal(store, c["id"], "it was wet soil")
    assert "returned" not in a["message"]["en"]
