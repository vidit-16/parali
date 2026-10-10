"""End-to-end smoke test against a running Saakshi (the live site by default).

Walks what a judge does: the pages and map data load; every demo claim is decided, in four languages, with
working voice notes and pictures; an officer confirms a burn (notice and payment link follow), the farmer
appeals (the link is cancelled), an officer approves another case (the balance is released); the assistant
answers in Punjabi with audio. Uses the public demo PIN, as reset_demo.py does.

It changes the demo's claims. Run scripts/reset_demo.py afterwards so judges start clean.

usage: uv run python scripts/smoke.py [--base https://d5gpae5oilzws.cloudfront.net] [--pin 2468] [--live-check]
"""
import argparse
import sys
import time

import requests

FAILS: list[str] = []


def ok(cond: bool, what: str) -> bool:
    print(("  ok   " if cond else "  FAIL ") + what, flush=True)
    if not cond:
        FAILS.append(what)
    return cond


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://d5gpae5oilzws.cloudfront.net")
    ap.add_argument("--pin", default="2468")
    ap.add_argument("--live-check", action="store_true", help="also run one live satellite check (about 20 s)")
    a = ap.parse_args()
    B, PIN = a.base.rstrip("/"), {"X-Officer-Pin": a.pin}
    get = lambda p, **kw: requests.get(B + p, timeout=30, **kw)  # noqa: E731
    post = lambda p, body=None, **kw: requests.post(B + p, json=body, timeout=60, **kw)  # noqa: E731

    print("pages and map data")
    for p in ("/", "/officer.html", "/farmer.html", "/js/explorer.js", "/js/shared.js", "/css/explorer.css",
              "/tiles/manifest.json", "/tiles/burns.geojson", "/tiles/burn_points.geojson", "/tiles/fires.geojson"):
        ok(get(p).status_code == 200, f"GET {p}")
    mf = get("/tiles/manifest.json").json()
    w = mf["windows"][-1]["id"]
    ok(get(f"/tiles/{w}/{mf['minzoom']}/{_tile(mf, mf['minzoom'])}.webp").status_code == 200, "a tile inside the bounds loads")
    ok(get("/api/officer/check").status_code == 403 and get("/api/officer/check", headers=PIN).status_code == 200,
       "officer routes need the PIN")

    print("demo claims")
    fields, claims = get("/api/fields").json(), get("/api/claims").json()
    ok(len(claims) == len(fields) == 11, f"{len(claims)} claims for {len(fields)} fields")
    ok(all(c["status"] != "submitted" and not c.get("error") for c in claims), "every claim decided, none failed")
    for c in claims:
        langs = set((c.get("message") or {}).keys())
        local = "pa" if c.get("state_code") == "PB" else "hr"
        ok({"en", "hi", local} <= langs, f"{c['field_id']}: message in en, hi, {local}")
        for k in ("audio_url", f"audio_url_{local}", "evidence_url"):
            if c.get(k):
                ok(get(c[k]).status_code == 200, f"{c['field_id']}: {k} loads")
    kinds = {c["status"] for c in claims}
    ok({"auto_approved", "possible_burn"} <= kinds, f"mix of outcomes: {sorted(kinds)}")

    print("officer confirms a burn, the farmer appeals")
    burn = next((c for c in claims if c["status"] == "possible_burn" and (c.get("advance") or {}).get("status") == "paid"), None)
    if ok(burn is not None, "an open possible burn with an advance"):
        r = post(f"/api/claims/{burn['id']}/review", {"officer_id": "SMOKE", "verdict": "confirm_burnt", "note": "smoke test"}, headers=PIN)
        ok(r.status_code == 200 and r.json()["status"] == "officer_confirmed_burnt", "review answers at once")
        c = _follow(get, burn["id"], {"recovery_notice", "farmer_told"})
        ok(bool(c.get("notice_url")) and get(c["notice_url"]).status_code == 200, "recovery notice written and served")
        rec = c.get("recovery") or {}
        ok(rec.get("status") == "issued" and rec.get("amount") == c["advance"]["amount"], "payment link for exactly the advance")
        r = post(f"/api/claims/{burn['id']}/appeal", {"note": "smoke test: the field was not burnt"})
        c = r.json()
        ok(r.status_code == 200 and c["status"] == "needs_review", "appeal sends it back to the officer")
        ok((c.get("recovery") or {}).get("status") in ("cancelled", None), "appeal cancels the payment link")

    print("officer approves another case")
    other = next((c for c in claims if c["status"] in ("possible_burn", "needs_review") and c["id"] != (burn or {}).get("id")), None)
    if ok(other is not None, "another open case"):
        r = post(f"/api/claims/{other['id']}/review", {"officer_id": "SMOKE", "verdict": "approve", "note": ""}, headers=PIN)
        ok(r.status_code == 200 and r.json()["status"] == "officer_approved", "approved")
        c = _follow(get, other["id"], {"farmer_told"})
        s, adv = c["settlement"], c.get("advance") or {}
        paid = adv.get("amount", 0) if adv.get("status") == "paid" else 0
        ok(s["state"] == "balance_due" and s["balance"] + paid == s["total"], "balance plus advance is the full incentive")

    print("assistant")
    pb = next(f for f in fields if f.get("state") == "PB")
    r = post("/api/agent", {"farmer_id": pb["id"], "lang": "pa", "text": "ਮੇਰੇ ਦਾਅਵੇ ਦਾ ਕੀ ਹਾਲ ਹੈ"})
    j = r.json() if r.ok else {}
    ok(r.ok and bool(j.get("pa")) and any("਀" <= ch <= "੿" for ch in j.get("pa", "")), "answers in Punjabi")
    ok(bool(j.get("audio_url")) and get(j["audio_url"]).status_code == 200, "with a voice note")

    if a.live_check:
        print("live satellite check")
        r = post("/api/check", {"geometry": pb["geometry"]})
        cid = r.json().get("id") if r.ok else None
        item = {}
        for _ in range(30):
            time.sleep(2)
            item = get(f"/api/check/{cid}").json()
            if item.get("status") in ("done", "error"):
                break
        ok(item.get("status") == "done", f"check finished: {item.get('status')}")

    print(f"\n{'all passed' if not FAILS else str(len(FAILS)) + ' failed'}. Run scripts/reset_demo.py to give judges a clean demo.")
    sys.exit(1 if FAILS else 0)


def _tile(mf, z):
    import math
    w, s, e, n = mf["bounds"]
    lon, lat = (w + e) / 2, (s + n) / 2
    k = 2 ** z
    return f"{int((lon + 180) / 360 * k)}/{int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * k)}"


def _follow(get, claim_id, want, seconds=60):
    """The decision's follow-up runs in the background: wait for its events."""
    for _ in range(seconds // 2):
        c = get(f"/api/claims/{claim_id}").json()
        if want <= {e["type"] for e in c.get("events") or []}:
            ok(True, "follow-up done: " + ", ".join(sorted(want)))
            return c
        time.sleep(2)
    ok(False, "follow-up done: " + ", ".join(sorted(want)))
    return c


if __name__ == "__main__":
    main()
