"""Find field-shaped patches in the cached study area for the demo: burnt, clean, and wet-soil examples.

Prints candidates as GeoJSON features; the chosen ones are copied into data/demo/fields.geojson by hand.
"""
import json
import sys
from pathlib import Path

import numpy as np
from rasterio.features import shapes
from shapely.geometry import mapping, shape

from parali.area import AreaStack
from parali.features import brightness, nbr
from parali.fields import reproject

SCL_BAD = (0, 1, 8, 9, 10)


def components(mask, transform, min_px, max_px):
    for geom, v in shapes(mask.astype("uint8"), mask=mask, transform=transform):
        g = shape(geom)
        n = g.area / 400
        if min_px <= n <= max_px:
            yield g


def main(area_path):
    st = AreaStack.load(Path(area_path))
    T = len(st.dates)
    nir = np.stack([st.band(t, "nir08") for t in range(T)])
    s2 = np.stack([st.band(t, "swir22") for t in range(T)])
    s1 = np.stack([st.band(t, "swir16") for t in range(T)])
    vis = np.stack([brightness(st.band(t, "red"), st.band(t, "green"), st.band(t, "blue")) for t in range(T)])
    bad = np.isin(st.scl, SCL_BAD)
    n = nbr(nir, s2)
    n[bad] = np.nan
    out = []

    # burnt: sharp NIR drop, very low NBR, near-black, on two consecutive dates
    for t in range(1, T - 1):
        drop = (nir[t - 1] - nir[t]) / nir[t - 1]
        burn = (drop > 0.35) & (n[t] < -0.15) & (vis[t] < 0.065) & (n[t + 1] < -0.1) & (vis[t + 1] < 0.075)
        for g in components(burn, st.transform, 20, 150):
            out.append(("burnt", str(st.dates[t]), g))

    # clean: cropland early, never dark after harvest
    early = [t for t, d in enumerate(st.dates) if d.month == 10 and d.day <= 12]
    late = [t for t, d in enumerate(st.dates) if (d.month == 10 and d.day > 15) or d.month >= 11]
    with np.errstate(all="ignore"):
        crop = np.nanmedian(n[early], axis=0) > 0.3
        clean = crop & (np.nanmin(n[late], axis=0) > -0.15) & (np.nanmin(vis[late], axis=0) > 0.065)
    for g in components(clean, st.transform, 20, 150):
        out.append(("clean", "", g))

    # wet: dark in visible and NBR, but SWIR low (MIRBI low) late in the season
    for t in late:
        mir = 10 * s2[t] - 9.8 * s1[t] + 2
        wet = (vis[t] < 0.07) & (n[t] < -0.05) & (mir < 1.6)
        for g in components(wet, st.transform, 20, 150):
            out.append(("wet", str(st.dates[t]), g))

    feats = []
    for kind, d, g in out:
        r = g.minimum_rotated_rectangle
        if g.area / r.area < 0.65:  # keep compact, field-like shapes
            continue
        ll = reproject(g.simplify(10), st.crs, "EPSG:4326")
        feats.append({"type": "Feature", "properties": {"kind": kind, "date": d, "ha": round(g.area / 1e4, 2)},
                      "geometry": mapping(ll)})
    by = {}
    for f in feats:
        by.setdefault(f["properties"]["kind"], []).append(f)
    for k, v in by.items():
        print(k, len(v), file=sys.stderr)
    json.dump({"type": "FeatureCollection", "features": feats}, sys.stdout)


if __name__ == "__main__":
    main(sys.argv[1])
