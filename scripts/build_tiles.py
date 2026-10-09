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


def run_blocks(session, fn, region, blocks, workers=6):
    lam = session.client("lambda", config=Config(read_timeout=910, connect_timeout=10, retries={"max_attempts": 0}))

    def one(b):
        t = time.time()
        for attempt in range(20):
            try:
                r = lam.invoke(FunctionName=fn, Payload=json.dumps({"block": list(b), "region": mapping(region),
                                                                    "workers": workers}).encode())
                break
            except lam.exceptions.TooManyRequestsException:  # account concurrency limit: wait for a slot
                time.sleep(20 + attempt * 5)
        else:
            return b, False, {"error": "throttled"}
        body = json.loads(r["Payload"].read())
        ok = "FunctionError" not in r
        print(f"block {b}: {'ok' if ok else 'FAILED'} in {time.time() - t:.0f}s  {json.dumps(body)[:300]}", flush=True)
        return b, ok, body

    with ThreadPoolExecutor(len(blocks)) as ex:
        return list(ex.map(one, blocks))


def merge_burns(sink, blocks, fire_feats=()):
    """One burn layer for the map. Each patch gets a=1 if any fire alert of the season fell within
    375 m of it (the radius the rules use), so the map can show the burns no alert caught."""
    feats = []
    for bx, by in blocks:
        data = sink.get(f"burns/{bx}_{by}.geojson")
        if data:
            feats += json.loads(data)["features"]
    if fire_feats:
        from pyproj import Transformer
        from shapely import STRtree, transform
        from shapely.geometry import shape
        utm = Transformer.from_crs(4326, 32643, always_xy=True)
        to_m = lambda g: transform(g, lambda xy: list(zip(*utm.transform(xy[:, 0], xy[:, 1]))))  # noqa: E731
        tree = STRtree([to_m(shape(f["geometry"])) for f in fire_feats])
        for f in feats:
            f["properties"]["a"] = int(len(tree.query(to_m(shape(f["geometry"])), predicate="dwithin", distance=375)) > 0)
    sink.put("burns.geojson", json.dumps({"type": "FeatureCollection", "features": feats},
                                         separators=(",", ":")).encode(), "application/json")  # CloudFront compresses application/json
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
                                         separators=(",", ":")).encode(), "application/json")  # CloudFront compresses application/json
    return feats


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="envhacks")
    p.add_argument("--blocks", nargs="*", help="only these z11 blocks, as x,y")
    p.add_argument("--skip-blocks", action="store_true", help="reuse block outputs already in S3")
    p.add_argument("--skip-pyramid", action="store_true", help="only redo the burn, fire and manifest files")
    p.add_argument("--workers", type=int, default=6, help="dates read at once per block (fewer = less memory)")
    p.add_argument("--old-totals-cover-missing", action="store_true",
                   help="blocks without a stored summary are counted from the previous manifest")
    a = p.parse_args()

    s = boto3.Session(profile_name=a.profile, region_name=REGION)
    out = outputs(s)
    region = shape(json.loads((ROOT / "data/region.geojson").read_text())["features"][0]["geometry"])
    blocks = [tuple(int(v) for v in b.split(",")) for b in a.blocks] if a.blocks else tiles.blocks_for(region)
    sink = tiles.S3Sink(out["Bucket"], "tiles/", client=s.client("s3"))
    print(f"{len(blocks)} blocks", flush=True)

    if not a.skip_blocks:
        results = run_blocks(s, out["TilesFunction"], region, blocks, a.workers)
        failed = [b for b, ok, _ in results if not ok]
        if failed:
            print("failed blocks:", failed)

    # Everything after the block jobs covers the whole region, so rerunning one block keeps the rest.
    every = tiles.blocks_for(region)
    if not a.skip_pyramid:
        for w, _, _ in tiles.WINDOWS:
            print(f"pyramid {w}: {tiles.pyramid(sink, w, every)} tiles", flush=True)
    fire_feats = fire_layer(sink, region)
    print("fire alerts in region:", len(fire_feats))
    print("burn patches:", merge_burns(sink, every, fire_feats))

    burn_ha: dict[int, float] = {}
    summaries, missing = [], []
    for bx, by in every:
        data = sink.get(f"burns/{bx}_{by}.json")
        (summaries.append(json.loads(data)) if data else missing.append((bx, by)))
    if missing and a.old_totals_cover_missing:
        # blocks built before per-block summaries were stored: their totals are in the previous manifest
        old = json.loads((ROOT / "data/tiles_manifest.json").read_text())
        summaries.append({"burn_ha": old["burn_ha_by_day"]})
        missing = []
    if missing:
        print("no summary for blocks:", missing)
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
