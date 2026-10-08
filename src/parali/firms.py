"""NASA FIRMS active fire points. Used as the current-system baseline and to find candidate burnt areas."""
import csv
import io
import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import requests

API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SOURCES = ("VIIRS_SNPP_SP", "VIIRS_NOAA20_SP", "VIIRS_NOAA21_NRT")
MAX_DAYS = 5


@dataclass(frozen=True)
class Fire:
    lat: float
    lon: float
    date: date
    source: str
    confidence: str
    frp: float


def map_key() -> str:
    key = os.environ.get("FIRMS_MAP_KEY")
    if not key:
        raise RuntimeError("FIRMS_MAP_KEY is not set")
    return key


def parse_csv(text: str, source: str) -> list[Fire]:
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        out.append(Fire(
            lat=float(r["latitude"]),
            lon=float(r["longitude"]),
            date=date.fromisoformat(r["acq_date"]),
            source=source,
            confidence=r.get("confidence", ""),
            frp=float(r.get("frp") or 0),
        ))
    return out


def fetch(bbox, start: date, end: date, sources=SOURCES, key: str | None = None, session=None) -> list[Fire]:
    key = key or map_key()
    session = session or requests.Session()
    area = ",".join(f"{v:.4f}" for v in bbox)
    fires = []
    for source in sources:
        day = start
        while day <= end:
            n = min(MAX_DAYS, (end - day).days + 1)
            r = session.get(f"{API}/{key}/{source}/{area}/{n}/{day.isoformat()}", timeout=120)
            r.raise_for_status()
            fires.extend(parse_csv(r.text, source))
            day += timedelta(days=n)
    return fires


def save(fires: list[Fire], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["lat", "lon", "date", "source", "confidence", "frp"])
        for x in fires:
            w.writerow([x.lat, x.lon, x.date.isoformat(), x.source, x.confidence, x.frp])


def load(path: Path) -> list[Fire]:
    with path.open(encoding="utf-8") as f:
        return [Fire(float(r["lat"]), float(r["lon"]), date.fromisoformat(r["date"]), r["source"],
                     r["confidence"], float(r["frp"])) for r in csv.DictReader(f)]


def distance_m(lat0, lon0, lats, lons):
    """Equirectangular distance in metres; fine at field scale."""
    k = 111_320.0
    dx = (np.asarray(lons) - lon0) * k * np.cos(np.radians(lat0))
    dy = (np.asarray(lats) - lat0) * k
    return np.hypot(dx, dy)


def fires_near(fires: list[Fire], lat: float, lon: float, radius_m: float,
               start: date | None = None, end: date | None = None) -> list[Fire]:
    sel = [f for f in fires if (start is None or f.date >= start) and (end is None or f.date <= end)]
    if not sel:
        return []
    d = distance_m(lat, lon, [f.lat for f in sel], [f.lon for f in sel])
    return [f for f, dist in zip(sel, d) if dist <= radius_m]
