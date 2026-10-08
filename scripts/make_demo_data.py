"""Cut a small image stack around each demo field from the cached study area, so the demo runs offline.

usage: python scripts/make_demo_data.py data/cache/west_kaithal_2025.npz data/demo/fields.geojson data/demo/stacks
"""
import sys
from pathlib import Path

from parali.area import AreaStack
from parali.fields import load_fields

PAD_DEG = 0.0018  # ~180 m of context around the field


def main(area, fields, out):
    st = AreaStack.load(Path(area))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for f in load_fields(fields):
        x0, y0, x1, y1 = f.bbox
        sub = st.subset((x0 - PAD_DEG, y0 - PAD_DEG, x1 + PAD_DEG, y1 + PAD_DEG))
        sub.save(out / f"{f.id}.npz")
        print(f.id, sub.scl.shape, (out / f"{f.id}.npz").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(*sys.argv[1:4])
