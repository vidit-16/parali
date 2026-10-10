"""Check any field: a polygon drawn on the map, verdicts for last season and this season.

No claim, no money, no officer: this is the same rules engine on a field of the user's choosing, so anyone
can see what the system would say about a real field.
"""
import uuid
from datetime import date

from parali import season
from parali.store import Store, now_iso

# Punjab and Haryana, roughly; checks outside are refused rather than silently wrong.
REGION_BBOX = (73.8, 27.6, 77.6, 32.6)
MIN_HA, MAX_HA = 0.2, 20.0


class CheckError(ValueError):
    pass


def validate(geometry: dict):
    from shapely.geometry import shape

    from parali.fields import project
    try:
        g = shape(geometry)
    except Exception as e:
        raise CheckError(f"not a valid polygon: {e}") from e
    if g.geom_type != "Polygon" or not g.is_valid:
        raise CheckError("draw one simple field outline")
    x0, y0, x1, y1 = g.bounds
    if not (REGION_BBOX[0] <= x0 and x1 <= REGION_BBOX[2] and REGION_BBOX[1] <= y0 and y1 <= REGION_BBOX[3]):
        raise CheckError("only fields in Punjab and Haryana can be checked")
    ha = project(g, "EPSG:32643").area / 1e4
    if not MIN_HA <= ha <= MAX_HA:
        raise CheckError(f"field is {ha:.2f} ha; draw a field between {MIN_HA} and {MAX_HA} ha")
    return g, ha


def create(store: Store, geometry: dict) -> dict:
    _, ha = validate(geometry)
    item = {"id": uuid.uuid4().hex[:12], "geometry": geometry, "hectares": round(ha, 2),
            "acres": round(ha * 2.471, 1), "status": "queued", "created_at": now_iso()}
    store.put("checks", item["id"], item)
    return item


def run(store: Store, check_id: str, stacks, fires, th) -> dict:
    from parali import evidence
    from parali.fields import Field
    from parali.service import _decide_season

    item = store.get("checks", check_id)
    if item is None:
        raise CheckError("unknown check")
    g, _ = validate(item["geometry"])
    f = Field(f"check-{check_id}", g, {})
    out = {}
    for name, (s, e) in (("current", season.SEASON), ("previous", season.PREV_SEASON)):
        # record the stage as it happens, so the app can show real progress instead of a spinner
        item.update(status="running", stage=name)
        store.put("checks", check_id, item)
        s, e = date.fromisoformat(s), date.fromisoformat(e)
        stack, feats, near, d = _decide_season(f, stacks, fires, th, s, e)
        if name == "current":
            item["clear_images"] = len(d.clear_dates)
        key = f"checks/{check_id}-{name}.png"
        store.put_blob(key, evidence.render(stack, f, d.burn_date), "image/png")
        out[name] = {"season": str(s.year), "decision": d.as_dict(), "evidence_key": key,
                     "evidence_dates": evidence.frame_dates(stack, f, d.burn_date),
                     "series": [{"date": x.date.isoformat(), "nbr": None if x.nbr != x.nbr else round(x.nbr, 4),
                                 "valid": round(x.valid_share, 2)} for x in feats],
                     "fires": [{"lat": p.lat, "lon": p.lon, "date": p.date.isoformat()} for p in near]}
    item.pop("stage", None)
    item.update(status="done", result=out, advance_eligible=season.advance_eligible(out["previous"]["decision"]["outcome"]),
                done_at=now_iso())
    store.put("checks", check_id, item)
    return item
