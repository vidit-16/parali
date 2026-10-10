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
