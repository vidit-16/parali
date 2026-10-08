"""Build and deploy to AWS, then upload the web app, FIRMS points and demo fields.

usage: uv run --extra aws python scripts/deploy.py [--profile envhacks] [--skip-build]
"""
import argparse
import json
import mimetypes
import subprocess
import sys
import time
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
STACK = "envhacks-parali"
REGION = "us-west-2"


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT, shell=sys.platform == "win32")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="envhacks")
    p.add_argument("--pin", default="2468")
    p.add_argument("--skip-build", action="store_true")
    p.add_argument("--skip-deploy", action="store_true")
    a = p.parse_args()

    if not a.skip_deploy:
        if not a.skip_build:
            run(["sam", "build", "--use-container", "-t", "infra/template.yaml"])
        run(["sam", "deploy", "--stack-name", STACK, "--region", REGION, "--profile", a.profile, "--resolve-s3",
             "--capabilities", "CAPABILITY_IAM", "--no-confirm-changeset", "--no-fail-on-empty-changeset",
             "--parameter-overrides", f"OfficerPin={a.pin}"])

    s = boto3.Session(profile_name=a.profile, region_name=REGION)
    out = {o["OutputKey"]: o["OutputValue"]
           for o in s.client("cloudformation").describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]}
    bucket, table = out["Bucket"], out["Table"]
    s3 = s.client("s3")

    web = ROOT / "web"
    types = {".js": "text/javascript", ".css": "text/css", ".html": "text/html", ".json": "application/json",
             ".png": "image/png", ".svg": "image/svg+xml"}
    for f in sorted(p for p in web.rglob("*") if p.is_file()):
        rel = f.relative_to(web).as_posix()
        ctype = types.get(f.suffix, mimetypes.guess_type(f.name)[0] or "application/octet-stream")
        if ctype.startswith("text/") or ctype == "application/json":
            ctype += "; charset=utf-8"
        s3.upload_file(str(f), bucket, f"web/{rel}", ExtraArgs={"ContentType": ctype})
        print("web/", rel)
    s3.upload_file(str(ROOT / "data/firms/kaithal_2025.csv"), bucket, "data/firms.csv")

    tbl = s.resource("dynamodb").Table(table)
    fc = json.loads((ROOT / "data/demo/fields.geojson").read_text(encoding="utf-8"))
    for feat in fc["features"]:
        item = {**feat["properties"], "geometry": feat["geometry"]}
        tbl.put_item(Item={"pk": f"fields#{item['id']}", "sk": "META", "kind": "fields", "body": json.dumps(item)})
        print("field", item["id"])

    s.client("cloudfront").create_invalidation(DistributionId=out["DistributionId"], InvalidationBatch={
        "Paths": {"Quantity": 1, "Items": ["/*"]}, "CallerReference": str(time.time())})
    print(f"\nLive at {out['Url']}  (officer PIN {a.pin})")


if __name__ == "__main__":
    main()
