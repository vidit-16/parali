import argparse
import csv
import sys
from datetime import date
from pathlib import Path

from parali import firms
from parali.features import field_features
from parali.fields import load_fields
from parali.history import FieldHistory, build_histories


def cmd_firms(a):
    bbox = tuple(float(v) for v in a.bbox.split(","))
    fires = firms.fetch(bbox, date.fromisoformat(a.start), date.fromisoformat(a.end))
    firms.save(fires, Path(a.out))
    print(f"{len(fires)} fire points -> {a.out}")


def cmd_history(a):
    fields = load_fields(a.fields)
    out = Path(a.out)
    hist = build_histories(fields, a.start, a.end, tile=a.tile)
    for fid, h in hist.items():
        h.save(out / f"{fid}.npz")
    print(f"{len(hist)} field histories -> {out}")


def cmd_area(a):
    from parali.area import fetch_area
    bbox = tuple(float(v) for v in a.bbox.split(","))
    stack = fetch_area(bbox, a.start, a.end, tile=a.tile, log=lambda m: print(m, flush=True))
    stack.save(Path(a.out))
    print(f"{len(stack.dates)} dates, grid {stack.scl.shape[1:]} -> {a.out}")


def cmd_features(a):
    paths = sorted(Path(a.history).glob("*.npz"))
    w = csv.writer(sys.stdout)
    header = False
    for p in paths:
        h = FieldHistory.load(p)
        for d in field_features(h):
            row = {"field_id": h.field_id, **d.as_dict()}
            if not header:
                w.writerow(row.keys())
                header = True
            w.writerow(round(v, 4) if isinstance(v, float) else v for v in row.values())


def main(argv=None):
    p = argparse.ArgumentParser(prog="parali")
    sub = p.add_subparsers(required=True)

    s = sub.add_parser("firms", help="download FIRMS fire points")
    s.add_argument("--bbox", required=True, help="west,south,east,north")
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_firms)

    s = sub.add_parser("history", help="read Sentinel-2 pixels for every field and date")
    s.add_argument("--fields", required=True)
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--tile")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_history)

    s = sub.add_parser("area", help="cache every scene over a study area")
    s.add_argument("--bbox", required=True, help="west,south,east,north")
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--tile")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_area)

    s = sub.add_parser("features", help="print per-date features as CSV")
    s.add_argument("--history", required=True)
    s.set_defaults(func=cmd_features)

    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
