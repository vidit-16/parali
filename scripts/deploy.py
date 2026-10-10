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


def fill_empty_tiles(s3, bucket: str) -> None:
    """The season pictures cover two areas, but the map's bounds are one box. Every tile address in that box
    without a picture gets a transparent one, so the map never asks for something that is not there."""
    import io
    import math
    from concurrent.futures import ThreadPoolExecutor

    from PIL import Image
    mf = json.loads(s3.get_object(Bucket=bucket, Key="tiles/manifest.json")["Body"].read())
    have = set()
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix="tiles/"):
        have.update(o["Key"] for o in page.get("Contents", []))

    def tile(lon, lat, z):
        n = 2 ** z
        return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    w, s, e, n = mf["bounds"]
    missing = []
    for z in range(mf["minzoom"], mf["maxzoom"] + 1):
        (x0, y0), (x1, y1) = tile(w, n, z), tile(e, s, z)
        missing += [f"tiles/{win['id']}/{z}/{x}/{y}.webp" for win in mf["windows"]
                    for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    missing = [k for k in missing if k not in have]
    buf = io.BytesIO()
    Image.new("RGBA", (256, 256), (0, 0, 0, 0)).save(buf, "WEBP", lossless=True)
    empty = buf.getvalue()
    put = lambda k: s3.put_object(Bucket=bucket, Key=k, Body=empty, ContentType="image/webp")  # noqa: E731
    with ThreadPoolExecutor(32) as ex:
        list(ex.map(put, missing))
    print(f"empty tiles: {len(missing)} added")


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
    types = {".geojson": "application/json", ".js": "text/javascript", ".css": "text/css", ".html": "text/html", ".json": "application/json",
             ".png": "image/png", ".svg": "image/svg+xml"}
    for f in sorted(p for p in web.rglob("*") if p.is_file()):
        rel = f.relative_to(web).as_posix()
        ctype = types.get(f.suffix, mimetypes.guess_type(f.name)[0] or "application/octet-stream")
        if ctype.startswith("text/") or ctype == "application/json":
            ctype += "; charset=utf-8"
        # no-cache: browsers revalidate (cheap 304s) instead of running a stale script after a deploy
        s3.upload_file(str(f), bucket, f"web/{rel}", ExtraArgs={"ContentType": ctype, "CacheControl": "no-cache"})
        print("web/", rel)
    s3.upload_file(str(ROOT / "data/firms/kaithal_2025.csv"), bucket, "data/firms.csv")
    fill_empty_tiles(s3, bucket)

    tbl = s.resource("dynamodb").Table(table)
    fc = json.loads((ROOT / "data/demo/fields.geojson").read_text(encoding="utf-8"))
    for feat in fc["features"]:
        item = {**feat["properties"], "geometry": feat["geometry"]}
        tbl.put_item(Item={"pk": f"fields#{item['id']}", "sk": "META", "kind": "fields", "body": json.dumps(item)})
        print("field", item["id"])

    s.client("cloudfront").create_invalidation(DistributionId=out["DistributionId"], InvalidationBatch={
        "Paths": {"Quantity": 1, "Items": ["/*"]}, "CallerReference": str(time.time())})
    # where Razorpay sends a payer back to after a payment link
    s.client("ssm").put_parameter(Name="/saakshi/public_url", Value=out["Url"], Type="String", Overwrite=True)
    print(f"\nLive at {out['Url']}  (officer PIN {a.pin})")


if __name__ == "__main__":
    main()
