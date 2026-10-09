"""Run the live satellite check once for every demo field and keep the results with the web app, so a field's
panel opens with its answer instead of a 20-second wait. "Run again" in the app still calls the live check.

usage: uv run python scripts/demo_checks.py [--base https://d5gpae5oilzws.cloudfront.net]
Writes web/data/demo_checks.json and web/data/checks/<field>-<season>.png.
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web/data"


def check(base: str, field: dict) -> dict:
    r = requests.post(f"{base}/api/check", json={"geometry": field["geometry"]}, timeout=30)
    r.raise_for_status()
    cid = r.json()["id"]
    for _ in range(60):
        time.sleep(3)
        item = requests.get(f"{base}/api/check/{cid}", timeout=30).json()
        if item["status"] in ("done", "error"):
            break
    if item["status"] != "done":
        raise RuntimeError(f"{field['id']}: {item.get('error', item['status'])}")
    for name, res in item["result"].items():
        png = requests.get(res["evidence_url"] if res["evidence_url"].startswith("http") else base + res["evidence_url"], timeout=60)
        png.raise_for_status()
        rel = f"checks/{field['id']}-{name}.png"
        (OUT / rel).write_bytes(png.content)
        res["evidence_url"] = f"data/{rel}"
        res.pop("evidence_key", None)
    return {"advance_eligible": item["advance_eligible"], "acres": item["acres"], "result": item["result"],
            "checked_at": item.get("done_at")}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="https://d5gpae5oilzws.cloudfront.net")
    a = p.parse_args()
    (OUT / "checks").mkdir(parents=True, exist_ok=True)
    fields = requests.get(f"{a.base}/api/fields", timeout=30).json()
    with ThreadPoolExecutor(4) as ex:
        results = dict(zip([f["id"] for f in fields], ex.map(lambda f: check(a.base, f), fields)))
    (OUT / "demo_checks.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    for fid, r in results.items():
        print(fid, r["result"]["current"]["decision"]["outcome"], r["result"]["previous"]["decision"]["outcome"])


if __name__ == "__main__":
    main()
