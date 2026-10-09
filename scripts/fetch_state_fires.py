"""NASA FIRMS fire alerts for all of Punjab and Haryana over the season, for the map's opening fly-in.

usage: uv run --extra aws python scripts/fetch_state_fires.py [--profile envhacks]
Needs FIRMS_MAP_KEY in the environment. Writes data/firms/pb_hr_2025.csv and tiles/fires_states.geojson.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from parali import firms, tiles  # noqa: E402
from parali.check import REGION_BBOX  # noqa: E402  Punjab and Haryana, roughly

STACK, REGION = "envhacks-parali", "us-west-2"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="envhacks")
    a = p.parse_args()
    path = ROOT / "data/firms/pb_hr_2025.csv"
    if path.exists():
        fs = firms.load(path)
    else:
        fs = firms.fetch(REGION_BBOX, date.fromisoformat(tiles.SEASON[0]), date.fromisoformat(tiles.SEASON[1]))
        firms.save(fs, path)
    # one point per alert; the same fire seen by two satellites a few minutes apart stays two points,
    # which is how FIRMS counts them too
    from shapely.geometry import Point, shape
    from shapely.ops import unary_union
    states = unary_union([shape(f["geometry"]) for f in json.loads((ROOT / "data/states_pb_hr.geojson").read_text())["features"]])
    fs = [f for f in fs if states.contains(Point(f.lon, f.lat))]  # the request box also clips Rajasthan, Himachal and UP
    feats = [{"type": "Feature", "properties": {"d": (f.date - tiles.DAY0).days},
              "geometry": {"type": "Point", "coordinates": [round(f.lon, 4), round(f.lat, 4)]}} for f in fs]
    body = json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")).encode()
    s = boto3.Session(profile_name=a.profile, region_name=REGION)
    out = {o["OutputKey"]: o["OutputValue"] for o in s.client("cloudformation").describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]}
    tiles.S3Sink(out["Bucket"], "tiles/", client=s.client("s3")).put("fires_states.geojson", body, "application/json")
    print(f"{len(feats)} alerts in Punjab and Haryana, {len(body) // 1024} KB")


if __name__ == "__main__":
    main()
