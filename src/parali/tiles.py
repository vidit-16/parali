"""Map tiles of our own Sentinel-2 imagery for the Patiala-Kaithal border belt.

The region is cut into zoom-11 web-mercator blocks (about 17 km across here). One block is one job: read
every scene of the season over it, build a cloud-free picture for each ten-day window, find where the
ground first turned burn-like, and write

    {window}/{z}/{x}/{y}.webp     base imagery, z11 to z14
    burns/{x}_{y}.geojson         burn-like patches with the day they first appeared

Zooms below 11 are made from the z11 tiles afterwards (pyramid). The burn patches are for the map only:
field decisions still come from rules.py on the 20 m grid, with the officer deciding.
"""
from __future__ import annotations

import io
import json
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Protocol

import numpy as np

from parali import config

TILE = 256
EARTH_R = 6378137.0
HALF = math.pi * EARTH_R
BLOCK_Z = 11
MAX_Z = 14
SUB = 2 ** (MAX_Z - BLOCK_Z)          # z14 tiles per block side
FULL = TILE * SUB                     # block side in z14 pixels (about 8 m)
COARSE = FULL // 2                    # burn grid: about 17 m, close to the 20 m decision grid
DAY0 = date(2025, 9, 1)               # burn day numbers count from here; 0 means no burn

WINDOWS = (
    ("0921", "2025-09-21", "2025-09-30"),
    ("1001", "2025-10-01", "2025-10-10"),
    ("1011", "2025-10-11", "2025-10-20"),
    ("1021", "2025-10-21", "2025-10-31"),
    ("1101", "2025-11-01", "2025-11-10"),
    ("1111", "2025-11-11", "2025-11-20"),
    ("1121", "2025-11-21", "2025-11-30"),
    ("1201", "2025-12-01", "2025-12-10"),
)
SEASON = (WINDOWS[0][1], WINDOWS[-1][2])

# Burn-like pixel, same signature as the field rules: dark NBR, near-black, right after a sharp NIR drop.
BURN_NBR = -0.15
BURN_MAX_BRIGHT = 0.07
BURN_NIR_DROP = 0.30
MIN_PATCH_PX = 3
DISPLAY_GAIN = 0.18                   # reflectance shown as full white


# ---- web mercator tile maths ----

def lonlat_to_3857(lon: float, lat: float) -> tuple[float, float]:
    x = math.radians(lon) * EARTH_R
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * EARTH_R
    return x, y


def tile_of(lon: float, lat: float, z: int) -> tuple[int, int]:
    x, y = lonlat_to_3857(lon, lat)
    n = 2 ** z
    return int((x + HALF) / (2 * HALF) * n), int((HALF - y) / (2 * HALF) * n)


def tile_bounds(x: int, y: int, z: int) -> tuple[float, float, float, float]:
    """(minx, miny, maxx, maxy) in EPSG:3857."""
    size = 2 * HALF / 2 ** z
    return -HALF + x * size, HALF - (y + 1) * size, -HALF + (x + 1) * size, HALF - y * size


def tile_lonlat_bounds(x: int, y: int, z: int) -> tuple[float, float, float, float]:
    n = 2 ** z
    lon0, lon1 = x / n * 360 - 180, (x + 1) / n * 360 - 180
    lat = lambda t: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * t / n))))  # noqa: E731
    return lon0, lat(y + 1), lon1, lat(y)


def blocks_for(region, z: int = BLOCK_Z) -> list[tuple[int, int]]:
    """Every z-level tile whose square touches the region (a shapely geometry in lon/lat)."""
    from shapely.geometry import box
    w, s, e, n = region.bounds
    x0, y0 = tile_of(w, n, z)
    x1, y1 = tile_of(e, s, z)
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
            if region.intersects(box(*tile_lonlat_bounds(x, y, z)))]


# ---- where tiles go ----

class Sink(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> bytes | None: ...


class DirSink:
    def __init__(self, root: Path):
        self.root = Path(root)

    def put(self, key, data, content_type):
        p = self.root / key
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get(self, key):
        p = self.root / key
        return p.read_bytes() if p.exists() else None


class S3Sink:
    def __init__(self, bucket: str, prefix: str, client=None):
        import boto3
        self.bucket, self.prefix = bucket, prefix
        self.s3 = client or boto3.client("s3")

    def put(self, key, data, content_type):
        self.s3.put_object(Bucket=self.bucket, Key=self.prefix + key, Body=data, ContentType=content_type,
                           CacheControl="public, max-age=86400")

    def get(self, key):
        try:
            return self.s3.get_object(Bucket=self.bucket, Key=self.prefix + key)["Body"].read()
        except self.s3.exceptions.NoSuchKey:
            return None


# ---- the pure parts: compositing and burn detection ----

def to_display(red, green, blue) -> np.ndarray:
    """Reflectance [H, W] x3 -> uint8 [H, W, 3]; NaN becomes 0."""
    a = np.dstack([red, green, blue]) / DISPLAY_GAIN
    return (np.clip(np.nan_to_num(a), 0, 1) ** 0.9 * 255).astype("uint8")


def composite(frames: list[np.ndarray], clear: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Per-pixel median of the clear frames. frames uint8 [H, W, 3], clear bool [H, W].
    Returns (rgb uint8 [H, W, 3], seen bool [H, W])."""
    if not frames:
        return None, None
    st = np.stack(frames).astype("float32")
    m = np.stack(clear)
    st[~m] = np.nan
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.nanmedian(st, axis=0)
    seen = m.any(axis=0)
    return np.nan_to_num(med).astype("uint8"), seen


def fill_gaps(windows: list[tuple[np.ndarray | None, np.ndarray | None]]) -> list[tuple[np.ndarray, np.ndarray]]:
    """Carry each pixel forward from the last window that saw it, then back-fill the start, so the
    time-lapse never shows holes. A filled pixel is shown, it is just older."""
    shape = next((r.shape for r, _ in windows if r is not None), None)
    if shape is None:
        return []
    out, last, last_seen = [], np.zeros(shape, "uint8"), np.zeros(shape[:2], bool)
    for rgb, seen in windows:
        if rgb is None:
            rgb, seen = np.zeros(shape, "uint8"), np.zeros(shape[:2], bool)
        rgb = np.where(seen[..., None], rgb, last)
        seen = seen | last_seen
        out.append((rgb, seen))
        last, last_seen = rgb, seen
    first_rgb, first_seen = None, None
    for i in range(len(out) - 1, -1, -1):
        rgb, seen = out[i]
        if first_rgb is not None:
            rgb = np.where(seen[..., None], rgb, first_rgb)
            seen = seen | first_seen
            out[i] = (rgb, seen)
        first_rgb, first_seen = rgb, seen
    return out


@dataclass
class DateBands:
    day: date
    nir: np.ndarray      # reflectance, coarse grid, NaN where unusable
    swir22: np.ndarray
    bright: np.ndarray   # mean visible reflectance, coarse grid


def burn_days(dates: list[DateBands]) -> np.ndarray:
    """uint8 [H, W]: day number (from DAY0) when the pixel first turned burn-like, 0 if never."""
    from parali.features import nbr
    first = None
    prev = None
    for d in sorted(dates, key=lambda d: d.day):
        if first is None:
            first = np.zeros(d.nir.shape, "uint8")
        nir = d.nir
        if prev is not None and d.day.month >= 10:
            with np.errstate(all="ignore"):
                hit = ((nbr(nir, d.swir22) < BURN_NBR) & (d.bright <= BURN_MAX_BRIGHT)
                       & ((prev - nir) / prev >= BURN_NIR_DROP))
            first[(first == 0) & hit] = (d.day - DAY0).days
        prev = nir.copy() if prev is None else np.where(np.isnan(nir), prev, nir)
    return first if first is not None else np.zeros((0, 0), "uint8")


def drop_specks(days: np.ndarray, min_px: int = MIN_PATCH_PX) -> np.ndarray:
    from rasterio.features import sieve
    if not days.any():
        return days
    kept = sieve((days > 0).astype("uint8"), size=min_px, connectivity=8)
    return np.where(kept > 0, days, 0).astype("uint8")


def downsample2(a: np.ndarray) -> np.ndarray:
    """Mean of 2x2 blocks, ignoring NaN."""
    h, w = a.shape[0] // 2, a.shape[1] // 2
    b = a[: h * 2, : w * 2].reshape(h, 2, w, 2)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return np.nanmean(b, axis=(1, 3))


# ---- writing tiles ----

def encode_webp(rgba: np.ndarray) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "WEBP", quality=80, method=4)
    return buf.getvalue()


def write_block_tiles(sink: Sink, window: str, bx: int, by: int, rgba: np.ndarray) -> int:
    """rgba uint8 [FULL, FULL, 4] for block (bx, by) -> tiles z11..z14. Returns tiles written."""
    from PIL import Image
    n = 0
    img = Image.fromarray(rgba, "RGBA")
    for z in range(MAX_Z, BLOCK_Z - 1, -1):
        k = 2 ** (z - BLOCK_Z)
        size = TILE * k
        level = img if size == FULL else img.resize((size, size), Image.BOX)
        arr = np.asarray(level)
        for j in range(k):
            for i in range(k):
                t = arr[j * TILE:(j + 1) * TILE, i * TILE:(i + 1) * TILE]
                if not t[..., 3].any():
                    continue
                sink.put(f"{window}/{z}/{bx * k + i}/{by * k + j}.webp", encode_webp(t), "image/webp")
                n += 1
    return n


def pyramid(sink: Sink, window: str, blocks: list[tuple[int, int]], min_z: int = 8) -> int:
    """Build zooms below BLOCK_Z from the z11 tiles already in the sink."""
    from PIL import Image
    have = set(blocks)
    n = 0
    for z in range(BLOCK_Z - 1, min_z - 1, -1):
        parents = {(x // 2, y // 2) for x, y in have}
        made = set()
        for px, py in sorted(parents):
            canvas = Image.new("RGBA", (TILE * 2, TILE * 2), (0, 0, 0, 0))
            any_child = False
            for dy in (0, 1):
                for dx in (0, 1):
                    data = sink.get(f"{window}/{z + 1}/{px * 2 + dx}/{py * 2 + dy}.webp")
                    if data:
                        canvas.paste(Image.open(io.BytesIO(data)).convert("RGBA"), (dx * TILE, dy * TILE))
                        any_child = True
            if not any_child:
                continue
            sink.put(f"{window}/{z}/{px}/{py}.webp", encode_webp(np.asarray(canvas.resize((TILE, TILE), Image.BOX))),
                     "image/webp")
            made.add((px, py))
            n += 1
        have = made
    return n


def burn_features(days: np.ndarray, transform, crs: str = "EPSG:3857") -> list[dict]:
    from rasterio.features import shapes
    from rasterio.warp import transform_geom
    feats = []
    for geom, v in shapes(days, mask=days > 0, transform=transform, connectivity=8):
        g = transform_geom(crs, "EPSG:4326", geom, precision=6)
        feats.append({"type": "Feature", "properties": {"d": int(v)}, "geometry": g})
    return feats


# ---- reading Sentinel-2 over a block ----

def search_block(bbox_lonlat, start: str, end: str, max_cloud: float = 80, client=None) -> dict[date, list]:
    """All scenes over the block from every MGRS tile, best one per tile per date, grouped by date."""
    from parali.imagery import dedupe_by_date, scene_from_item
    if client is None:
        from pystac_client import Client
        client = Client.open(config.STAC_URL)
    items = client.search(collections=[config.COLLECTION], bbox=bbox_lonlat, datetime=f"{start}/{end}",
                          query={"eo:cloud_cover": {"lt": max_cloud}}).items()
    by_tile: dict[str, list] = {}
    for it in items:
        s = scene_from_item(it)
        by_tile.setdefault(s.tile, []).append(s)
    out: dict[date, list] = {}
    for scenes in by_tile.values():
        for s in dedupe_by_date(scenes):
            out.setdefault(s.date, []).append(s)
    return dict(sorted(out.items()))


def _read(href, bounds, size, resampling):
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.vrt import WarpedVRT
    with rasterio.open(href) as src, WarpedVRT(src, crs="EPSG:3857", transform=from_bounds(*bounds, size, size),
                                               width=size, height=size, resampling=resampling,
                                               src_nodata=0, nodata=0) as vrt:
        return vrt.read(1)


def read_date(scenes: list, bounds) -> dict[str, np.ndarray]:
    """One date over one block, merging tiles: fine RGB reflectance, coarse NIR, SWIR, SCL."""
    from rasterio.enums import Resampling
    out: dict[str, np.ndarray] = {}
    plan = [("red", FULL, Resampling.bilinear), ("green", FULL, Resampling.bilinear),
            ("blue", FULL, Resampling.bilinear), ("nir08", COARSE, Resampling.average),
            ("swir22", COARSE, Resampling.average), ("scl", COARSE, Resampling.nearest)]
    for s in scenes:
        for band, size, rs in plan:
            dn = _read(s.hrefs[band], bounds, size, rs)
            if band == "scl":
                v = dn.astype("uint8")
                cur = out.get(band)
                out[band] = v if cur is None else np.where(cur == 0, v, cur)
            else:
                scale, offset = s.scale_offset[band]
                r = dn.astype("float32") * scale + offset
                r[dn == 0] = np.nan
                cur = out.get(band)
                out[band] = r if cur is None else np.where(np.isnan(cur), r, cur)
    return out


def region_mask(region_lonlat, bounds, size: int) -> np.ndarray:
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds
    from rasterio.warp import transform_geom
    from shapely.geometry import mapping
    g = transform_geom("EPSG:4326", "EPSG:3857", mapping(region_lonlat))
    return rasterize([(g, 1)], out_shape=(size, size), transform=from_bounds(*bounds, size, size),
                     fill=0, dtype="uint8").astype(bool)


def build_block(bx: int, by: int, region_lonlat, sink: Sink, log: Callable[[str], None] = print,
                workers: int = 12, searcher=search_block, reader=read_date) -> dict:
    """Everything for one z11 block. Returns a small summary (scene count, tiles, burn area by day)."""
    from rasterio.transform import from_bounds
    bounds = tile_bounds(bx, by, BLOCK_Z)
    bbox = tile_lonlat_bounds(bx, by, BLOCK_Z)
    by_date = searcher(bbox, *SEASON)
    log(f"block {bx},{by}: {len(by_date)} dates")
    inside_fine = region_mask(region_lonlat, bounds, FULL)
    inside_coarse = region_mask(region_lonlat, bounds, COARSE)

    frames: dict[str, list] = {w: [] for w, _, _ in WINDOWS}
    clears: dict[str, list] = {w: [] for w, _, _ in WINDOWS}
    burn_input: list[DateBands] = []

    def window_of(d: date) -> str | None:
        iso = d.isoformat()
        return next((w for w, s, e in WINDOWS if s <= iso <= e), None)

    with ThreadPoolExecutor(workers) as ex:
        # read ahead at most `workers` dates, so a block never holds the whole season in memory
        pending = list(by_date.items())
        futures = [(d, ex.submit(reader, s, bounds)) for d, s in pending[:workers]]
        nxt = workers
        while futures:
            d, fut = futures.pop(0)
            b = fut.result()
            if nxt < len(pending):
                futures.append((pending[nxt][0], ex.submit(reader, pending[nxt][1], bounds)))
                nxt += 1
            usable_c = ~np.isin(b["scl"], config.SCL_MASKED)
            nir = np.where(usable_c, b["nir08"], np.nan)
            vis = [b[k] for k in ("red", "green", "blue")]
            bright = (downsample2(vis[0]) + downsample2(vis[1]) + downsample2(vis[2])) / 3
            burn_input.append(DateBands(d, nir, np.where(usable_c, b["swir22"], np.nan), bright))
            w = window_of(d)
            if w:
                usable_f = np.kron(usable_c, np.ones((2, 2), bool)) & np.isfinite(vis[0])
                frames[w].append(to_display(*vis))
                clears[w].append(usable_f)
            log(f"  {d}")

    days = drop_specks(np.where(inside_coarse, burn_days(burn_input), 0).astype("uint8"))
    pix_m = (bounds[2] - bounds[0]) / COARSE * math.cos(math.radians((bbox[1] + bbox[3]) / 2))
    vals, counts = np.unique(days[days > 0], return_counts=True)
    burn_ha = {int(v): round(float(c) * pix_m * pix_m / 1e4, 2) for v, c in zip(vals, counts)}
    feats = burn_features(days, from_bounds(*bounds, COARSE, COARSE))
    sink.put(f"burns/{bx}_{by}.geojson", json.dumps({"type": "FeatureCollection", "features": feats},
                                                    separators=(",", ":")).encode(), "application/geo+json")

    filled = fill_gaps([composite(frames[w], clears[w]) for w, _, _ in WINDOWS])
    tiles = 0
    for (w, _, _), (rgb, seen) in zip(WINDOWS, filled):
        alpha = ((seen & inside_fine) * 255).astype("uint8")
        tiles += write_block_tiles(sink, w, bx, by, np.dstack([rgb, alpha]))
    summary = {"block": [bx, by], "dates": len(by_date), "tiles": tiles, "patches": len(feats), "burn_ha": burn_ha}
    log(json.dumps(summary))
    return summary
