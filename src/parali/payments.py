"""Getting an advance back, with Razorpay payment links (test mode).

Money to farmers is a Direct Benefit Transfer through the state's treasury and stays simulated here: that
rail is not a payment gateway. Money from a farmer is different: when an officer confirms a burn after an
advance was paid, the farmer gets a payment link for that amount, in the app and on WhatsApp. Razorpay sends
the payer back to /api/razorpay/return with a signature made from our key secret; a valid signature (or
asking Razorpay directly) marks the advance recovered. An appeal cancels the open link.
"""
import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request

from parali.store import Store, now_iso

API = "https://api.razorpay.com/v1"
RAIL = "Razorpay payment link, test mode"
_keys: dict = {}


def keys() -> dict:
    """key_id and key_secret: RAZORPAY_* variables locally, SSM on Lambda (read again until both are there)."""
    if os.environ.get("RAZORPAY_KEY_ID"):
        return {"key_id": os.environ["RAZORPAY_KEY_ID"], "key_secret": os.environ.get("RAZORPAY_KEY_SECRET", "")}
    if not (_keys.get("key_id") and _keys.get("key_secret")) and os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        import boto3
        try:
            page = boto3.client("ssm").get_parameters_by_path(Path="/saakshi/razorpay/", WithDecryption=True)
            _keys.update({p["Name"].rsplit("/", 1)[-1]: p["Value"] for p in page["Parameters"]})
        except Exception as e:
            print(f"razorpay keys unavailable: {type(e).__name__}")
    return _keys


def public_url() -> str:
    """Where Razorpay sends the payer back to. deploy.py stores the CloudFront address in SSM."""
    if os.environ.get("PUBLIC_URL"):
        return os.environ["PUBLIC_URL"].rstrip("/")
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        import boto3
        try:
            return boto3.client("ssm").get_parameter(Name="/saakshi/public_url")["Parameter"]["Value"].rstrip("/")
        except Exception:
            pass
    return "http://127.0.0.1:8080"


class Razorpay:
    def __init__(self, key_id: str, key_secret: str):
        self.key_id, self.key_secret = key_id, key_secret

    @classmethod
    def from_keys(cls) -> "Razorpay | None":
        k = keys()
        return cls(k["key_id"], k["key_secret"]) if k.get("key_id") and k.get("key_secret") else None

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        auth = base64.b64encode(f"{self.key_id}:{self.key_secret}".encode()).decode()
        req = urllib.request.Request(API + path, json.dumps(body).encode() if body is not None else None,
                                     {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}, method=method)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    def create_link(self, amount: int, reference: str, description: str, name: str, notes: dict, callback: str) -> dict:
        return self._call("POST", "/payment_links", {
            "amount": int(amount) * 100, "currency": "INR", "accept_partial": False, "reference_id": reference,
            "description": description[:2048], "customer": {"name": name[:50]} if name else {},
            "notify": {"sms": False, "email": False}, "reminder_enable": False, "notes": notes,
            "callback_url": callback, "callback_method": "get"})

    def get_link(self, link_id: str) -> dict:
        return self._call("GET", f"/payment_links/{link_id}")

    def cancel_link(self, link_id: str) -> dict:
        return self._call("POST", f"/payment_links/{link_id}/cancel")


def signature_ok(params: dict, key_secret: str) -> bool:
    keys_ = ("razorpay_payment_link_id", "razorpay_payment_link_reference_id", "razorpay_payment_link_status",
             "razorpay_payment_id")
    if not key_secret or not all(params.get(k) for k in keys_ + ("razorpay_signature",)):
        return False
    want = hmac.new(key_secret.encode(), "|".join(params[k] for k in keys_).encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, params["razorpay_signature"])


def issue_recovery(store: Store, claim: dict, rp: Razorpay | None, base_url: str) -> dict:
    """A payment link for an advance that has to come back. Does nothing if one is open or already paid."""
    s = claim.get("settlement") or {}
    rec = claim.get("recovery") or {}
    if rp is None or s.get("state") != "recover_advance" or not s.get("recover") or rec.get("status") in ("issued", "paid"):
        return claim
    n = rec.get("n", 0) + 1
    try:
        link = rp.create_link(s["recover"], f"{claim['id']}-{n}",
                              f"Return of the no-burn advance for {claim.get('field_name', '')} ({claim.get('village', '')})",
                              claim.get("farmer_name", ""), {"claim_id": claim["id"]}, f"{base_url}/api/razorpay/return")
    except (urllib.error.URLError, KeyError, ValueError) as e:
        print(f"razorpay link failed: {type(e).__name__}")
        return claim
    claim["recovery"] = {"status": "issued", "n": n, "link_id": link["id"], "url": link["short_url"],
                         "amount": s["recover"], "issued_at": now_iso(), "rail": RAIL}
    store.put("claims", claim["id"], claim)
    store.add_event(claim["id"], {"type": "recovery_link", "by": "system", "amount": s["recover"], "rail": RAIL})
    return claim


def mark_paid(store: Store, claim: dict, payment_id: str) -> dict:
    from parali.messages import farmer_text
    rec = claim.get("recovery") or {}
    if rec.get("status") == "paid":
        return claim
    rec.update(status="paid", payment_id=payment_id, paid_at=now_iso())
    claim["recovery"] = rec
    claim["message"] = farmer_text(claim)
    store.put("claims", claim["id"], claim)
    if claim.get("notice_key"):  # the notice now records the repayment
        from parali.service import write_notice
        write_notice(store, claim)
        store.put("claims", claim["id"], claim)
    store.add_event(claim["id"], {"type": "advance_recovered", "by": "farmer", "amount": rec.get("amount"),
                                  "rail": RAIL, "payment_id": payment_id})
    return claim


def check(store: Store, claim: dict, rp: Razorpay | None) -> dict:
    """Ask Razorpay whether the open link was paid (for a payer who closed the page before coming back)."""
    rec = claim.get("recovery") or {}
    if rp is None or rec.get("status") != "issued":
        return claim
    link = rp.get_link(rec["link_id"])
    if link.get("status") == "paid":
        pays = link.get("payments") or []
        return mark_paid(store, claim, (pays[-1] or {}).get("payment_id", "") if pays else "")
    return claim


def cancel(store: Store, claim: dict, rp: Razorpay | None) -> dict:
    """An appeal stops recovery: the open link is cancelled."""
    rec = claim.get("recovery") or {}
    if rec.get("status") != "issued":
        return claim
    try:
        if rp is not None:
            rp.cancel_link(rec["link_id"])
    except urllib.error.URLError as e:
        print(f"razorpay cancel failed: {type(e).__name__}")
    rec.update(status="cancelled", cancelled_at=now_iso())
    claim["recovery"] = rec
    store.put("claims", claim["id"], claim)
    store.add_event(claim["id"], {"type": "recovery_cancelled", "by": "system", "reason": "appeal"})
    return claim
