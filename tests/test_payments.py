import hashlib
import hmac
import json

from parali import api, payments, service
from tests.test_season import stacks_by_year, store  # noqa: F401  (fixture)
from tests.test_service import TH


class FakeRazorpay(payments.Razorpay):
    def __init__(self):
        super().__init__("rzp_test_x", "secret")
        self.links, self.cancelled, self.paid = {}, [], set()

    def create_link(self, amount, reference, description, name, notes, callback):
        lid = f"plink_{len(self.links) + 1}"
        self.links[lid] = {"amount": amount, "reference": reference, "callback": callback}
        return {"id": lid, "short_url": f"https://rzp.io/i/{lid}", "status": "created"}

    def get_link(self, link_id):
        return {"status": "paid" if link_id in self.paid else "created", "payments": [{"payment_id": "pay_9"}]}

    def cancel_link(self, link_id):
        self.cancelled.append(link_id)


def confirmed_burn(store):  # noqa: F811
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    st = stacks_by_year(None, 4)
    service.assess_advance(store, c["id"], st, [], TH, "2024-10-01", "2024-11-30")
    service.disburse_advance(store, c["id"], "dept")
    service.process_claim(store, c["id"], st, [], TH)
    return c["id"]


def deps(store, rp):  # noqa: F811
    return api.Deps(store=store, dispatch=lambda cid: None, payments=lambda: rp, base_url=lambda: "https://x.test")


def review(d, cid, verdict="confirm_burnt"):
    body = json.dumps({"officer_id": "VO-7", "verdict": verdict, "note": "seen"}).encode()
    return json.loads(api.handle("POST", f"/api/claims/{cid}/review", body, {}, d)[2])


def signed(rp, link_id, ref, status="paid", pay="pay_1"):
    q = {"razorpay_payment_link_id": link_id, "razorpay_payment_link_reference_id": ref,
         "razorpay_payment_link_status": status, "razorpay_payment_id": pay}
    q["razorpay_signature"] = hmac.new(rp.key_secret.encode(), f"{link_id}|{ref}|{status}|{pay}".encode(),
                                       hashlib.sha256).hexdigest()
    return q


def test_confirmed_burn_gets_a_payment_link_and_the_message_says_so(store):  # noqa: F811
    rp = FakeRazorpay()
    c = review(deps(store, rp), confirmed_burn(store))
    rec = c["recovery"]
    assert rec["status"] == "issued" and rec["amount"] == 1250 and rp.links[rec["link_id"]]["amount"] == 1250
    assert rp.links[rec["link_id"]]["callback"] == "https://x.test/api/razorpay/return"
    assert "payment link" in c["message"]["en"] and "ਲਿੰਕ" in c["message"]["pa"]


def test_signed_return_marks_the_advance_recovered(store):  # noqa: F811
    rp = FakeRazorpay()
    d, notified = deps(store, rp), []
    d.notify = notified.append
    c = review(d, confirmed_burn(store))
    lid, ref = c["recovery"]["link_id"], f"{c['id']}-1"
    forged = {**signed(rp, lid, ref), "razorpay_signature": "0" * 64}
    assert api.handle("GET", "/api/razorpay/return", None, {}, d, forged)[1]["Location"].endswith("paid=failed")
    status, headers, _ = api.handle("GET", "/api/razorpay/return", None, {}, d, signed(rp, lid, ref))
    assert status == 302 and headers["Location"] == f"/farmer.html?paid={c['id']}"
    c = store.get("claims", c["id"])
    assert c["recovery"]["status"] == "paid" and "Nothing more is due" in c["message"]["en"]
    assert notified and notified[-1]["recovery"]["status"] == "paid"
    assert [e for e in store.events(c["id"]) if e["type"] == "advance_recovered"][0]["payment_id"] == "pay_1"


def test_asking_razorpay_finds_a_payment_made_without_returning(store):  # noqa: F811
    rp = FakeRazorpay()
    d = deps(store, rp)
    c = review(d, confirmed_burn(store))
    rp.paid.add(c["recovery"]["link_id"])
    out = json.loads(api.handle("POST", f"/api/claims/{c['id']}/recovery/check", b"{}", {}, d)[2])
    assert out["recovery"]["status"] == "paid" and out["recovery"]["payment_id"] == "pay_9"


def test_appeal_cancels_the_link_and_a_new_confirmation_issues_another(store):  # noqa: F811
    rp = FakeRazorpay()
    d = deps(store, rp)
    c = review(d, confirmed_burn(store))
    first = c["recovery"]["link_id"]
    a = json.loads(api.handle("POST", f"/api/claims/{c['id']}/appeal", json.dumps({"note": "wet soil"}).encode(), {}, d)[2])
    assert rp.cancelled == [first] and a["recovery"]["status"] == "cancelled"
    again = review(d, c["id"])
    assert again["recovery"]["status"] == "issued" and again["recovery"]["link_id"] != first
    assert rp.links[again["recovery"]["link_id"]]["reference"] == f"{c['id']}-2"


def test_without_razorpay_nothing_changes(store):  # noqa: F811
    c = review(deps(store, None), confirmed_burn(store))
    assert "recovery" not in c and "written notice" in c["message"]["en"]


def test_repaid_then_appeal_won_pays_the_full_amount(store):  # noqa: F811
    rp = FakeRazorpay()
    d = deps(store, rp)
    c = review(d, confirmed_burn(store))
    lid, ref = c["recovery"]["link_id"], f"{c['id']}-1"
    api.handle("GET", "/api/razorpay/return", None, {}, d, signed(rp, lid, ref))
    api.handle("POST", f"/api/claims/{c['id']}/appeal", json.dumps({"note": "it was wet soil"}).encode(), {}, d)
    won = review(d, c["id"], "approve")
    assert won["settlement"]["state"] == "balance_due" and won["settlement"]["balance"] == won["settlement"]["total"] == 2500
    assert rp.cancelled == []  # nothing open to cancel: it was paid
