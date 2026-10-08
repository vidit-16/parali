"""Render labelling strips for every evaluation plot, plus the three worked examples shown in the labelling guide.

usage: python scripts/make_label_images.py data/cache/west_kaithal_2025.npz
"""
import sys
from pathlib import Path

from parali.area import AreaStack
from parali.fields import load_fields
from parali.label import render_strip

GUIDE = {  # chosen by looking at the strips: one clear burn, one clean plot with burnt and wet neighbours, one mixed
    "burnt": ("data/demo/fields.geojson", "f-mahender"),
    "not_burnt": ("data/eval/plots.geojson", "p012_122"),
    "unsure": ("data/eval/plots.geojson", "p117_021"),
}


def main(area):
    st = AreaStack.load(Path(area))
    for name, (src, fid) in GUIDE.items():
        f = {x.id: x for x in load_fields(src)}[fid]
        render_strip(st, f, Path("data/eval/guide") / f"{name}.png")
    plots = load_fields("data/eval/plots.geojson")
    for i, p in enumerate(plots, 1):
        render_strip(st, p, Path("data/eval/chips") / f"{p.id}.png")
        if i % 50 == 0:
            print(f"{i}/{len(plots)}", flush=True)
    print("done")


if __name__ == "__main__":
    main(sys.argv[1])
