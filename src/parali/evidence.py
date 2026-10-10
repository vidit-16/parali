"""Before/after image strip for one field, for the officer and the farmer. Pillow only, so it runs in Lambda."""
import io
from datetime import date

import numpy as np
from PIL import Image, ImageDraw

from parali import config
from parali.area import AreaStack
from parali.fields import Field, project

SCALE = 8
GAP = 4
LABEL_H = 16
YELLOW = (255, 214, 0)
RED = (220, 40, 40)


def clear_dates(stack: AreaStack, mask: np.ndarray, min_share: float = 0.8) -> list[int]:
    out = []
    for t in range(len(stack.dates)):
        ok = ~np.isin(stack.scl[t][mask], config.SCL_MASKED)
        if ok.size and ok.mean() >= min_share:
            out.append(t)
    return out


def pick_dates(clear: list[int], dates: list[date], burn: date | None, n: int) -> list[int]:
    if len(clear) <= n:
        return clear
    idx = [clear[i] for i in np.linspace(0, len(clear) - 1, n).round().astype(int)]
    if burn is not None:
        b = min(clear, key=lambda t: abs((dates[t] - burn).days))
        if b not in idx:
            idx[min(range(n), key=lambda i: abs((dates[idx[i]] - burn).days))] = b
    return sorted(set(idx))


def to_rgb(stack: AreaStack, t: int, kind: str) -> np.ndarray:
    if kind == "true":
        bands, div = ("red", "green", "blue"), (0.16, 0.16, 0.16)
    else:
        bands, div = ("swir22", "nir08", "red"), (0.35, 0.45, 0.2)
    rgb = np.dstack([stack.band(t, b) / d for b, d in zip(bands, div)])
    return (np.clip(np.nan_to_num(rgb), 0, 1) * 255).astype("uint8")


def _frames(stack: AreaStack, field: Field, burn_date: date | None, n: int):
    from rasterio.features import geometry_mask
    from shapely.geometry import mapping
    hw = stack.scl.shape[1:]
    g = project(field.geometry, stack.crs)
    mask = geometry_mask([mapping(g)], out_shape=hw, transform=stack.transform, invert=True)
    return g, hw, pick_dates(clear_dates(stack, mask), stack.dates, burn_date, n)


def frame_dates(stack: AreaStack, field: Field, burn_date: date | None = None, n: int = 8) -> list[str]:
    """The dates render() draws, left to right, so a page can cut the image into frames."""
    return [stack.dates[t].isoformat() for t in _frames(stack, field, burn_date, n)[2]]


def render(stack: AreaStack, field: Field, burn_date: date | None = None, n: int = 8) -> bytes:
    """One column per date: the date, the colour picture, then the infrared (SWIR2, NIR, red) picture, where
    burnt ground is maroon and wet soil dark blue. Frames are GAP pixels apart; the label row is LABEL_H high."""
    g, hw, ts = _frames(stack, field, burn_date, n)
    h, w = hw[0] * SCALE, hw[1] * SCALE
    img = Image.new("RGB", (max(len(ts), 1) * (w + GAP), 2 * (h + GAP) + LABEL_H), "white")
    draw = ImageDraw.Draw(img)
    inv = ~stack.transform
    ring = [tuple(v * SCALE for v in inv @ xy) for xy in g.exterior.coords]
    for j, t in enumerate(ts):
        x = j * (w + GAP)
        hit = burn_date is not None and stack.dates[t] == burn_date
        draw.text((x + 2, 2), stack.dates[t].strftime("%d %b"), fill=RED if hit else (30, 30, 30))
        for i, kind in enumerate(("true", "swir")):
            y = LABEL_H + i * (h + GAP)
            tile = Image.fromarray(to_rgb(stack, t, kind)).resize((w, h), Image.NEAREST)
            img.paste(tile, (x, y))
            draw.line([(px + x, py + y) for px, py in ring], fill=RED if hit else YELLOW, width=2)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()
