import json
import urllib.error

from parali import api, payouts, service
from tests.test_payments import deps as pay_deps
from tests.test_season import stacks_by_year, store  # noqa: F401  (fixture)
from tests.test_service import TH


class FakeCashfree(payouts.Cashfree):
    def __init__(self, fail=False):
        super().__init__("TEST_APP", "secret")
        self.sent, self.fail = [], fail

    def transfer(self, transfer_id, amount, name, remarks):
        if self.fail:
            raise urllib.error.HTTPError("x", 400, "bad", {}, None)
        self.sent.append((transfer_id, amount))
        return {"transfer_id": transfer_id, "cf_transfer_id": f"CF{len(self.sent)}", "status": "SUCCESS", "transfer_utr": "TESTUTR1"}

    def status(self, transfer_id):
        return {"status": "SUCCESS"}


def review_open_claim(store, cf, verdict="approve"):  # noqa: F811
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    st = stacks_by_year(None, 4)
    service.assess_advance(store, c["id"], st, [], TH, "2024-10-01", "2024-11-30")
    service.disburse_advance(store, c["id"], "dept")
    service.process_claim(store, c["id"], st, [], TH)
    d = pay_deps(store, None)
    d.payouts = lambda: cf
    body = json.dumps({"officer_id": "VO-7", "verdict": verdict, "note": "seen"}).encode()
    return json.loads(api.handle("POST", f"/api/claims/{c['id']}/review", body, {}, d)[2])


def test_an_approved_balance_is_paid_once_through_cashfree(store):  # noqa: F811
    cf = FakeCashfree()
    c = review_open_claim(store, cf)
    p, s = c["payout"], c["settlement"]
    assert p["status"] == "SUCCESS" and p["amount"] == s["balance"] == s["total"] - c["advance"]["amount"]
    assert cf.sent == [(p["transfer_id"], s["balance"])] and p["rail"] == payouts.RAIL
    assert "payout_sent" in [e["type"] for e in store.events(c["id"])]
    payouts.release(store, store.get("claims", c["id"]), cf)
    assert len(cf.sent) == 1  # never paid twice


def test_a_confirmed_burn_pays_nothing(store):  # noqa: F811
    cf = FakeCashfree()
    c = review_open_claim(store, cf, "confirm_burnt")
    assert cf.sent == [] and "payout" not in c


def test_without_cashfree_the_payout_stays_simulated(store):  # noqa: F811
    c = review_open_claim(store, None)
    assert c["settlement"]["state"] == "balance_due" and "payout" not in c


def test_a_failed_transfer_is_recorded_and_sent_again_under_a_new_id(store):  # noqa: F811
    c = review_open_claim(store, FakeCashfree(fail=True))
    assert c["payout"]["status"] == "FAILED" and "payout_failed" in [e["type"] for e in store.events(c["id"])]
    cf = FakeCashfree()
    c = payouts.release(store, store.get("claims", c["id"]), cf)
    assert c["payout"]["status"] == "SUCCESS" and c["payout"]["n"] == 2 and cf.sent[0][0].endswith("_2")


def test_request_signature_decrypts_to_client_id_and_time():
    import pytest
    crypto = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.rsa")
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    key = crypto.generate_private_key(public_exponent=65537, key_size=2048)
    for fmt in (serialization.PublicFormat.SubjectPublicKeyInfo, serialization.PublicFormat.PKCS1):
        pem = key.public_key().public_bytes(serialization.Encoding.PEM, fmt).decode()
        sig = payouts.signature("TEST_APP", pem, now=1760000000)
        import base64
        plain = key.decrypt(base64.b64decode(sig), padding.OAEP(mgf=padding.MGF1(hashes.SHA1()), algorithm=hashes.SHA1(), label=None))
        assert plain == b"TEST_APP.1760000000"


class PendingCashfree(FakeCashfree):
    """The bank takes a while: the transfer is pending until asked again."""
    def __init__(self):
        super().__init__()
        self.asked = 0

    def transfer(self, transfer_id, amount, name, remarks):
        self.sent.append((transfer_id, amount))
        return {"transfer_id": transfer_id, "cf_transfer_id": "CF9", "status": "PENDING"}

    def status(self, transfer_id):
        self.asked += 1
        return {"status": "PENDING"} if self.asked < 6 else {"status": "SUCCESS", "transfer_utr": "UTR9"}


def test_a_pending_payout_is_followed_up_until_it_lands_with_a_receipt(store, monkeypatch):  # noqa: F811
    from parali import whatsapp
    monkeypatch.setattr(payouts.time, "sleep", lambda s: None)  # the waits between status checks
    cf = PendingCashfree()
    c = review_open_claim(store, cf)
    assert c["payout"]["status"] == "PENDING" and "receipt_key" not in c["payout"]
    assert "on its way" in whatsapp.short_status(c, "en") and "on its way" in whatsapp.money_line(c, "en")
    c = payouts.refresh(store, store.get("claims", c["id"]), cf)
    assert c["payout"]["status"] == "PENDING"  # still with the bank
    c = payouts.refresh(store, store.get("claims", c["id"]), cf)
    assert c["payout"]["status"] == "SUCCESS" and c["payout"]["utr"] == "UTR9" and len(cf.sent) == 1
    html = store.get_blob(c["payout"]["receipt_key"]).decode()
    assert "Payment advice" in html and "UTR9" in html and "Test mode" in html and "PAID" in html
    kinds = [e["type"] for e in store.events(c["id"])]
    assert kinds.count("payout_pending") == 1 and kinds.count("payout_sent") == 1
    assert "sent to your bank" in whatsapp.short_status(c, "en")


def test_the_daily_sweep_sends_a_failed_payout_again(store):  # noqa: F811
    from parali import whatsapp
    c = review_open_claim(store, FakeCashfree(fail=True))
    assert "failed" in whatsapp.short_status(c, "en") and "failed" in whatsapp.money_line(c, "en")
    cf = FakeCashfree()
    assert payouts.sweep(store, cf) == [c["id"]]
    assert store.get("claims", c["id"])["payout"]["status"] == "SUCCESS" and payouts.sweep(store, cf) == []


def test_only_an_officer_can_send_a_failed_payout_again(store):  # noqa: F811
    c = review_open_claim(store, FakeCashfree(fail=True))
    cf = FakeCashfree()
    d = pay_deps(store, None)
    d.payouts, d.officer_pin = (lambda: cf), "2468"
    body = json.dumps({"retry": True}).encode()
    out = json.loads(api.handle("POST", f"/api/claims/{c['id']}/payout/check", body, {}, d)[2])
    assert out["payout"]["status"] == "FAILED" and cf.sent == []
    out = json.loads(api.handle("POST", f"/api/claims/{c['id']}/payout/check", body, {"X-Officer-Pin": "2468"}, d)[2])
    assert out["payout"]["status"] == "SUCCESS" and out["payout"]["receipt_url"].endswith(".html")
