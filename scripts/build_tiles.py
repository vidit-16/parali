"""Build the map for the whole border belt on AWS: one Lambda per z11 block, then the low zooms, the merged
burn layer, the season's fire alerts and a manifest the web app reads.

usage: uv run --extra aws python scripts/build_tiles.py [--profile envhacks] [--blocks 1457,845 ...] [--skip-blocks]
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import boto3
from botocore.config import Config
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from parali import firms, tiles  # noqa: E402

STACK = "envhacks-parali"
REGION = "us-west-2"


def outputs(session):
    return {o["OutputKey"]: o["OutputValue"]
            for o in session.client("cloudformation").describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]}


def run_blocks(session, fn, region, blocks):
    lam = session.client("lambda", config=Config(read_timeout=910, connect_timeout=10, retries={"max_attempts": 0}))

    def one(b):
        t = time.time()
        r = lam.invoke(FunctionName=fn, Payload=json.dumps({"block": list(b), "region": mapping(region)}).encode())
        body = json.loads(r["Payload"].read())
        ok = "FunctionError" not in r
        print(f"block {b}: {'ok' if ok else 'FAILED'} in {time.time() - t:.0f}s  {json.dumps(body)[:300]}", flush=True)
        return b, ok, body

    with ThreadPoolExecutor(len(blocks)) as ex:
        return list(ex.map(one, blocks))


def merge_burns(sink, blocks):
    feats = []
    for bx, by in blocks:
        data = sink.get(f"burns/{bx}_{by}.geojson")
        if data:
            feats += json.loads(data)["features"]
    sink.put("burns.geojson", json.dumps({"type": "FeatureCollection", "features": feats},
                                         separators=(",", ":")).encode(), "application/geo+json")
    return len(feats)


def fire_layer(sink, region):
    w, s, e, n = region.bounds
    path = ROOT / "data/firms/belt_2025.csv"
    if path.exists():
        fs = firms.load(path)
    else:
        fs = firms.fetch((w, s, e, n), date.fromisoformat(tiles.SEASON[0]), date.fromisoformat(tiles.SEASON[1]))
        firms.save(fs, path)
    from shapely.geometry import Point
    feats = [{"type": "Feature", "properties": {"d": (f.date - tiles.DAY0).days},
              "geometry": {"type": "Point", "coordinates": [round(f.lon, 5), round(f.lat, 5)]}}
             for f in fs if region.contains(Point(f.lon, f.lat))]
    sink.put("fires.geojson", json.dumps({"type": "FeatureCollection", "features": feats},
                                         separators=(",", ":")).encode(), "application/geo+json")
    return len(feats)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="envhacks")
    p.add_argument("--blocks", nargs="*", help="only these z11 blocks, as x,y")
    p.add_argument("--skip-blocks", action="store_true", help="reuse block outputs already in S3")
    a = p.parse_args()

    s = boto3.Session(profile_name=a.profile, region_name=REGION)
    out = outputs(s)
    region = shape(json.loads((ROOT / "data/region.geojson").read_text())["features"][0]["geometry"])
    blocks = [tuple(int(v) for v in b.split(",")) for b in a.blocks] if a.blocks else tiles.blocks_for(region)
    sink = tiles.S3Sink(out["Bucket"], "tiles/", client=s.client("s3"))
    print(f"{len(blocks)} blocks", flush=True)

    summaries = []
    if not a.skip_blocks:
        results = run_blocks(s, out["TilesFunction"], region, blocks)
        failed = [b for b, ok, _ in results if not ok]
        if failed:
            print("failed blocks:", failed)
        summaries = [body for _, ok, body in results if ok]
        blocks = [b for b, ok, _ in results if ok]

    for w, _, _ in tiles.WINDOWS:
        print(f"pyramid {w}: {tiles.pyramid(sink, w, blocks)} tiles", flush=True)
    print("burn patches:", merge_burns(sink, blocks))
    print("fire alerts in region:", fire_layer(sink, region))

    burn_ha: dict[int, float] = {}
    for sm in summaries:
        for d, ha in sm.get("burn_ha", {}).items():
            burn_ha[int(d)] = round(burn_ha.get(int(d), 0) + ha, 2)
    manifest = {
        "windows": [{"id": w, "start": st, "end": en} for w, st, en in tiles.WINDOWS],
        "day0": tiles.DAY0.isoformat(), "minzoom": 8, "maxzoom": tiles.MAX_Z,
        "bounds": list(region.bounds), "burn_ha_by_day": dict(sorted(burn_ha.items())),
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if summaries:
        sink.put("manifest.json", json.dumps(manifest).encode(), "application/json")
        (ROOT / "data/tiles_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"\nDone. {out['Url']}/tiles/manifest.json")


if __name__ == "__main__":
    main()
