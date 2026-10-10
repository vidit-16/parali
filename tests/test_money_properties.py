"""Money properties, checked over many generated cases (seeded, so a failure always reproduces):
the advance and the balance add up to the incentive, nothing is negative, recovery is exactly the advance,
and an open appeal never sits next to an open payment link."""
import json
import random

import pytest
from shapely.geometry import mapping

from parali import api, season, service
from parali.store import LocalStore
from tests.test_payments import FakeRazorpay, signed
from tests.test_season import stacks_by_year
from tests.test_service import FIELD_GEOM, TH

STATUSES = ["auto_approved", "officer_approved", "officer_confirmed_burnt", "needs_review", "possible_burn", "submitted"]


@pytest.mark.parametrize("seed", range(5))
def test_settlement_adds_up_for_any_field(seed):
    rnd = random.Random(seed)
    for _ in range(400):
        acres, state = round(rnd.uniform(0.1, 60), 2), rnd.choice(["PB", "HR", None])
        total, adv = season.full_amount(acres, state), season.advance_amount(acres, state)
        assert 0 <= adv <= total
        paid = rnd.choice([0, adv])
        status = rnd.choice(STATUSES)
        s = season.settle(status, acres, paid, state)
        assert s["total"] == total
        if status in season.CLEAN:
            assert s["state"] == "balance_due" and s["balance"] + paid == total and s["balance"] >= 0 and s["recover"] == 0
        elif status == "officer_confirmed_burnt":
            assert s["balance"] == 0 and s["recover"] == paid
            assert s["state"] == ("recover_advance" if paid else "not_payable")
            assert s["compensation_reference"] > 0
        else:
            assert s["state"] == "pending" and s["balance"] is None and s["recover"] is None


def test_compensation_never_falls_as_the_holding_grows():
    amounts = [season.environmental_compensation(a / 10) for a in range(1, 800)]
    assert amounts == sorted(amounts)


def _fresh(tmp_path, i):
    s = LocalStore(tmp_path / str(i))
    s.put("fields", "f1", {"id": "f1", "name": "Killa 12", "farmer": "Ramesh", "acres": 2.5, "geometry": mapping(FIELD_GEOM)})
    return s


def _check(c):
    s, rec, adv = c.get("settlement") or {}, c.get("recovery") or {}, c.get("advance") or {}
    paid = adv.get("amount", 0) if adv.get("status") == "paid" else 0
    assert paid <= s.get("total", 0)
    if s.get("state") == "balance_due":
        # a repaid advance is paid out again in full; otherwise the balance is what the advance left
        assert s["balance"] == s["total"] - (0 if rec.get("status") == "paid" else paid)
    if s.get("state") == "recover_advance":
        assert s["recover"] == paid > 0
    if rec:
        assert rec["amount"] == paid
    if c.get("appeal") and c["status"] in service.REVIEW_STATES:
        assert rec.get("status") != "issued", "an appeal is open but the payment link is still live"
    for v in (s.get("balance"), s.get("recover")):
        assert v is None or v >= 0


def test_random_paths_through_a_claim_keep_the_money_straight(tmp_path):
    rnd, reached = random.Random(7), set()
    for i in range(64):
        store, rp = _fresh(tmp_path, i), FakeRazorpay()
        d = api.Deps(store=store, dispatch=lambda cid: None, payments=lambda: rp, base_url=lambda: "https://x.test")
        st = stacks_by_year(rnd.choice([None, 4]), rnd.choice([None, 4]))
        c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
        service.assess_advance(store, c["id"], st, [], TH, "2024-10-01", "2024-11-30")
        if store.get("claims", c["id"])["advance"]["eligible"] and rnd.random() < 0.8:
            service.disburse_advance(store, c["id"], "dept")
        _check(service.process_claim(store, c["id"], st, [], TH))
        for _ in range(rnd.randint(2, 7)):
            c = store.get("claims", c["id"])
            move = rnd.choice(["approve", "confirm_burnt", "appeal", "pay"])
            if move in ("approve", "confirm_burnt") and c["status"] in service.REVIEW_STATES:
                body = json.dumps({"officer_id": "VO-1", "verdict": move, "note": "seen on the ground"}).encode()
                api.handle("POST", f"/api/claims/{c['id']}/review", body, {}, d)
            elif move == "appeal" and c["status"] in service.APPEALABLE:
                api.handle("POST", f"/api/claims/{c['id']}/appeal", json.dumps({"note": "wet soil, not ash"}).encode(), {}, d)
            elif move == "pay" and (c.get("recovery") or {}).get("status") == "issued":
                rec = c["recovery"]
                api.handle("GET", "/api/razorpay/return", None, {}, d, signed(rp, rec["link_id"], f"{c['id']}-{rec['n']}"))
            c = store.get("claims", c["id"])
            _check(c)
            reached |= {c["status"], (c.get("settlement") or {}).get("state"), "link " + str((c.get("recovery") or {}).get("status")),
                        "appealed" if c.get("appeal") else None}
    # the generated paths must actually reach the cases worth checking
    assert {"officer_approved", "officer_confirmed_burnt", "recover_advance", "link issued", "link paid", "link cancelled", "appealed"} <= reached, reached
