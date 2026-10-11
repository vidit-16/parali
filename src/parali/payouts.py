"""Paying the farmer: the incentive balance goes out through Cashfree Payouts (test mode in this demo).

The decision record (service._settle) says what is due; this module moves it. In test mode Cashfree simulates the
bank side and accepts transfers only to its published test accounts, so every demo farmer is paid "to" that
account; the transfer id, status and bank reference are Cashfree's own. Without Cashfree keys the payout stays
simulated, as the record already says.
"""
import base64
import hashlib
import re
import json
import os
import secrets
import time
import urllib.error
import urllib.request

from parali.store import Store, now_iso

API = "https://sandbox.cashfree.com/payout"
VERSION = "2024-01-01"
RAIL = "Cashfree Payouts, test mode"
# Cashfree's test bank account that returns success (docs: payouts "data to test integration")
TEST_ACCOUNT = {"bank_account_number": "026291800001191", "bank_ifsc": "YESB0000262"}
DONE = ("SUCCESS",)
FAILED = ("FAILED", "REJECTED", "REVERSED")
_keys: dict = {}


def keys() -> dict:
    """app_id, secret and public_key (for the request signature): CASHFREE_* variables locally, SSM on Lambda."""
    if os.environ.get("CASHFREE_APP_ID"):
        return {"app_id": os.environ["CASHFREE_APP_ID"], "secret": os.environ.get("CASHFREE_SECRET", "")}
    if not (_keys.get("app_id") and _keys.get("secret") and _keys.get("public_key")) and os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        import boto3
        try:
            page = boto3.client("ssm").get_parameters_by_path(Path="/saakshi/cashfree/", WithDecryption=True)
            _keys.update({p["Name"].rsplit("/", 1)[-1]: p["Value"] for p in page["Parameters"]})
        except Exception as e:
            print(f"cashfree keys unavailable: {type(e).__name__}")
    return _keys


# ---- request signature: Cashfree's alternative to IP whitelisting, which a Lambda (no fixed IP) cannot use.
# The signature is "<client id>.<unix time>" encrypted with Cashfree's public key (RSA, OAEP padding with SHA-1),
# base64. Written out here, about forty lines, rather than adding a crypto library to the Lambda bundle.

def _der(buf: bytes, i: int) -> tuple[int, int, int]:
    """(tag, start of value, end of value) of the DER element at i."""
    tag, n = buf[i], buf[i + 1]
    i += 2
    if n & 0x80:
        k = n & 0x7F
        n, i = int.from_bytes(buf[i:i + k], "big"), i + k
    return tag, i, i + n


def rsa_public_key(pem: str) -> tuple[int, int]:
    """(n, e) from a PEM "PUBLIC KEY" (SubjectPublicKeyInfo) or "RSA PUBLIC KEY" (PKCS#1)."""
    body = "".join(line for line in pem.strip().splitlines() if line and not line.startswith("-----"))
    der = base64.b64decode(body)
    _, i, end = _der(der, 0)                 # outer SEQUENCE
    tag, j, k = _der(der, i)
    if tag == 0x30:                          # SubjectPublicKeyInfo: algorithm SEQUENCE, then BIT STRING
        _, j, k = _der(der, k)
        der, i = der[j + 1:k], 0             # skip the unused-bits byte
        _, i, end = _der(der, 0)             # RSAPublicKey SEQUENCE
    _, a, b = _der(der, i)
    _, c, d = _der(der, b)
    return int.from_bytes(der[a:b], "big"), int.from_bytes(der[c:d], "big")


def _mgf1(seed: bytes, length: int) -> bytes:
    out, n = b"", 0
    while len(out) < length:
        out += hashlib.sha1(seed + n.to_bytes(4, "big")).digest()
        n += 1
    return out[:length]


def oaep_encrypt(message: bytes, n: int, e: int) -> bytes:
    k, h = (n.bit_length() + 7) // 8, 20
    if len(message) > k - 2 * h - 2:
        raise ValueError("message too long")
    db = hashlib.sha1(b"").digest() + b"\x00" * (k - len(message) - 2 * h - 2) + b"\x01" + message
    seed = secrets.token_bytes(h)
    masked_db = bytes(x ^ y for x, y in zip(db, _mgf1(seed, k - h - 1)))
    masked_seed = bytes(x ^ y for x, y in zip(seed, _mgf1(masked_db, h)))
    em = b"\x00" + masked_seed + masked_db
    return pow(int.from_bytes(em, "big"), e, n).to_bytes(k, "big")


def signature(app_id: str, public_pem: str, now: int | None = None) -> str:
    n, e = rsa_public_key(public_pem)
    return base64.b64encode(oaep_encrypt(f"{app_id}.{int(now or time.time())}".encode(), n, e)).decode()


class Cashfree:
    def __init__(self, app_id: str, secret: str, public_key: str = ""):
        self.app_id, self.secret, self.public_key = app_id, secret, public_key

    @classmethod
    def from_keys(cls) -> "Cashfree | None":
        k = keys()
        return cls(k["app_id"], k["secret"], k.get("public_key", "")) if k.get("app_id") and k.get("secret") else None

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        headers = {"x-client-id": self.app_id, "x-client-secret": self.secret, "x-api-version": VERSION,
                   "Content-Type": "application/json"}
        if self.public_key:
            headers["x-cf-signature"] = signature(self.app_id, self.public_key)
        req = urllib.request.Request(API + path, json.dumps(body).encode() if body is not None else None, headers, method=method)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())

    def transfer(self, transfer_id: str, amount: int, name: str, remarks: str) -> dict:
        try:
            return self._transfer_v2(transfer_id, amount, name, remarks)
        except urllib.error.HTTPError as e:  # keep Cashfree's reason for the log
            raise urllib.error.HTTPError(e.url, e.code, e.read().decode(errors="replace")[:300], e.headers, None)

    def _transfer_v2(self, transfer_id: str, amount: int, name: str, remarks: str) -> dict:
        return self._call("POST", "/transfers", {
            "transfer_id": transfer_id, "transfer_amount": amount, "transfer_currency": "INR", "transfer_mode": "banktransfer",
            "transfer_remarks": re.sub(r"[^A-Za-z0-9 ]", " ", remarks)[:70],  # Cashfree accepts letters, digits and spaces
            "beneficiary_details": {"beneficiary_name": name[:100] or "Farmer", "beneficiary_instrument_details": TEST_ACCOUNT}})

    def status(self, transfer_id: str) -> dict:
        return self._call("GET", f"/transfers?transfer_id={transfer_id}")


def release(store: Store, claim: dict, cf: "Cashfree | None") -> dict:
    """Send the balance that is due, once. A failed transfer can be sent again under a new id."""
    s, p = claim.get("settlement") or {}, claim.get("payout") or {}
    if cf is None or s.get("state") != "balance_due" or not s.get("balance") or p.get("status") in DONE + ("PENDING", "RECEIVED"):
        return claim
    n = int(p.get("n", 0)) + 1
    tid = f"SKS_{claim['id']}_{n}"
    try:
        out = cf.transfer(tid, int(s["balance"]), claim.get("farmer_name", ""), f"Saakshi incentive balance {claim['id']}")
        if out.get("status") not in DONE + FAILED:
            time.sleep(2)
            out = {**out, **cf.status(tid)}
    except urllib.error.HTTPError as e:
        detail = (e.msg or "")[:300]
        print(f"cashfree transfer failed: HTTP {e.code} {detail}")
        out = {"status": "FAILED", "status_description": f"HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"cashfree transfer failed: {type(e).__name__}")
        out = {"status": "FAILED", "status_description": type(e).__name__}
    claim["payout"] = {"n": n, "transfer_id": tid, "cf_transfer_id": out.get("cf_transfer_id"), "status": out.get("status"),
                       "utr": out.get("transfer_utr"), "amount": int(s["balance"]), "rail": RAIL, "sent_at": now_iso(),
                       "note": out.get("status_description", "")}
    store.put("claims", claim["id"], claim)
    store.add_event(claim["id"], {"type": "payout_sent" if out.get("status") not in FAILED else "payout_failed", "by": "system",
                                  "amount": int(s["balance"]), "rail": RAIL, "status": out.get("status"),
                                  "cf_transfer_id": out.get("cf_transfer_id")})
    return claim
