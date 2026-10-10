"""Clear the demo's claims and file one fresh claim per demo field, so judges start with open cases.

Uses the public demo PIN (shown on the officer sign-in screen). Each claim runs the full season: last season's
check, the advance, this season's check, the farmer's messages and voice notes.

usage: uv run python scripts/reset_demo.py [--base https://d5gpae5oilzws.cloudfront.net] [--pin 2468]
"""
import argparse
import time

import requests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://d5gpae5oilzws.cloudfront.net")
    ap.add_argument("--pin", default="2468")
    a = ap.parse_args()
    r = requests.post(f"{a.base}/api/demo/reset", headers={"X-Officer-Pin": a.pin}, timeout=60)
    r.raise_for_status()
    fields = requests.get(f"{a.base}/api/fields", timeout=30).json()
    for f in fields:
        r = requests.post(f"{a.base}/api/claims", json={"field_id": f["id"]}, timeout=30)
        print(f["id"], r.status_code)
        time.sleep(1)  # each claim starts its own run; don't start eleven at once
    for _ in range(60):
        time.sleep(10)
        claims = requests.get(f"{a.base}/api/claims", timeout=30).json()
        waiting = [c["field_id"] for c in claims if c["status"] == "submitted"]
        print(f"{len(claims) - len(waiting)}/{len(claims)} decided")
        if not waiting:
            break
    for c in sorted(claims, key=lambda c: c["field_id"]):
        print(f"{c['field_id']:14} {c['status']:24} advance={c.get('advance', {}).get('status')}  "
              f"langs={sorted((c.get('message') or {}).keys())}  frames={len(c.get('evidence_dates') or [])}")


if __name__ == "__main__":
    main()
