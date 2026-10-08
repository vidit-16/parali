from collections import Counter
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds

from parali import config


@dataclass(frozen=True)
class Scene:
    id: str
    date: date
    tile: str
    cloud_cover: float
    nodata_pct: float
    hrefs: dict[str, str] = field(hash=False)
    scale_offset: dict[str, tuple[float, float]] = field(hash=False)


@dataclass
class Chip:
    """Bands for one scene over one bounding box, on the 20 m grid."""
    scene: Scene
    crs: object
    transform: object
    bands: dict[str, np.ndarray]  # reflectance, NaN where DN == 0
    scl: np.ndarray


def scene_from_item(item) -> Scene:
    hrefs, so = {}, {}
    for band in (*config.BANDS, "scl"):
        asset = item.assets[band]
        hrefs[band] = asset.href
        rb = (asset.extra_fields.get("raster:bands") or [{}])[0]
        so[band] = (rb.get("scale", 1.0), rb.get("offset", 0.0))
    p = item.properties
    return Scene(
        id=item.id,
        date=item.datetime.date(),
        tile=p.get("grid:code", ""),
        cloud_cover=float(p.get("eo:cloud_cover", 0.0)),
        nodata_pct=float(p.get("s2:nodata_pixel_percentage", 0.0)),
        hrefs=hrefs,
        scale_offset=so,
    )


def search_scenes(bbox, start: str, end: str, max_cloud: float = 60, tile: str | None = None,
                  client=None) -> list[Scene]:
    if client is None:
        from pystac_client import Client
        client = Client.open(config.STAC_URL)
    items = client.search(collections=[config.COLLECTION], bbox=bbox, datetime=f"{start}/{end}",
                          query={"eo:cloud_cover": {"lt": max_cloud}}).items()
    scenes = [scene_from_item(i) for i in items]
    if not scenes:
        return []
    if tile is None:
        tile = Counter(s.tile for s in scenes).most_common(1)[0][0]
    return dedupe_by_date([s for s in scenes if s.tile == tile])


def dedupe_by_date(scenes: list[Scene]) -> list[Scene]:
    """Keep one scene per date: least no-data, then least cloud."""
    best: dict[date, Scene] = {}
    for s in scenes:
        cur = best.get(s.date)
        if cur is None or (s.nodata_pct, s.cloud_cover) < (cur.nodata_pct, cur.cloud_cover):
            best[s.date] = s
    return [best[d] for d in sorted(best)]


def to_reflectance(dn: np.ndarray, scale: float, offset: float) -> np.ndarray:
    out = dn.astype("float32") * scale + offset
    out[dn == 0] = np.nan
    return out


def valid_mask(chip_bands: dict[str, np.ndarray], scl: np.ndarray) -> np.ndarray:
    ok = np.ones(scl.shape, dtype=bool)
    for arr in chip_bands.values():
        ok &= np.isfinite(arr)
    return ok & ~np.isin(scl, config.SCL_MASKED)


GDAL_ENV = dict(
    AWS_NO_SIGN_REQUEST="YES",
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
    GDAL_HTTP_MULTIPLEX="YES",
    GDAL_HTTP_MAX_RETRY="4",
    GDAL_HTTP_RETRY_DELAY="2",
)


def read_chip(scene: Scene, bbox_lonlat) -> Chip:
    with rasterio.Env(**GDAL_ENV):
        return _read_chip(scene, bbox_lonlat)


def _read_chip(scene: Scene, bbox_lonlat) -> Chip:
    with rasterio.open(scene.hrefs["scl"]) as src:
        crs = src.crs
        b = transform_bounds("EPSG:4326", crs, *bbox_lonlat)
        win = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        win = win.intersection(Window(0, 0, src.width, src.height))
        transform = src.window_transform(win)
        scl = src.read(1, window=win)
    shape = scl.shape
    bands = {}
    for band in config.BANDS:
        with rasterio.open(scene.hrefs[band]) as src:
            ratio = round(config.PIXEL_SIZE_M / src.res[0])
            w = Window(win.col_off * ratio, win.row_off * ratio, win.width * ratio, win.height * ratio)
            dn = src.read(1, window=w, out_shape=shape, resampling=Resampling.average)
        bands[band] = to_reflectance(dn, *scene.scale_offset[band])
    return Chip(scene=scene, crs=crs, transform=transform, bands=bands, scl=scl)
