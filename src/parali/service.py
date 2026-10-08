"""Claim workflow, shared by the Lambda handlers and the local demo server.

submitted -> auto_approved | needs_review | possible_burn
needs_review | possible_burn -> officer_approved | officer_confirmed_burnt (officer id required)
"""
import uuid
from datetime import date
from typing import Callable

from parali import evidence
from parali.area import AreaStack
from parali.features import field_features
from parali.fields import Field
from parali.firms import Fire, fires_near
from parali.messages import farmer_text
from parali.rules import Thresholds, decide
from parali.store import Store, now_iso

REVIEW_STATES = ("needs_review", "possible_burn")
OFFICER_VERDICTS = {"approve": "officer_approved", "confirm_burnt": "officer_confirmed_burnt"}

StackProvider = Callable[[Field, date, date], AreaStack]
Speaker = Callable[[str], bytes]


class WorkflowError(ValueError):
    pass


def field_from_item(item: dict) -> Field:
    from shapely.geometry import shape
    props = {k: v for k, v in item.items() if k not in ("id", "geometry")}
    return Field(item["id"], shape(item["geometry"]), props)


def create_claim(store: Store, field_id: str, season_start: str, season_end: str, as_of: str | None = None) -> dict:
    f = store.get("fields", field_id)
    if f is None:
        raise WorkflowError(f"unknown field {field_id}")
    for c in store.list("claims"):
        if c["field_id"] == field_id and c["season_start"] == season_start:
            raise WorkflowError("a claim for this field and season already exists")
    claim = {
        "id": uuid.uuid4().hex[:10],
        "field_id": field_id,
        "field_name": f.get("name", field_id),
        "farmer_name": f.get("farmer", ""),
        "village": f.get("village", ""),
        "acres": f.get("acres"),
        "season_start": season_start,
        "season_end": season_end,
        "as_of": as_of or season_end,
        "status": "submitted",
        "created_at": now_iso(),
    }
    store.put("claims", claim["id"], claim)
    store.add_event(claim["id"], {"type": "submitted", "by": "farmer"})
    return claim


def _speak(store: Store, claim: dict, speaker: Speaker | None) -> None:
    text = farmer_text(claim)
    claim["message"] = text
    if speaker is None:
        claim.pop("audio_key", None)
        return
    key = f"audio/{claim['id']}-{claim['status']}.mp3"
    store.put_blob(key, speaker(text["hi"]), "audio/mpeg")
    claim["audio_key"] = key


def process_claim(store: Store, claim_id: str, stacks: StackProvider, fires: list[Fire], th: Thresholds,
                  speaker: Speaker | None = None) -> dict:
    claim = store.get("claims", claim_id)
    if claim is None:
        raise WorkflowError(f"unknown claim {claim_id}")
    if claim["status"] not in ("submitted",) + REVIEW_STATES:
        raise WorkflowError(f"claim is already {claim['status']}")
    field = field_from_item(store.get("fields", claim["field_id"]))
    start, end = date.fromisoformat(claim["season_start"]), date.fromisoformat(claim["season_end"])
    as_of = date.fromisoformat(claim["as_of"])
    stack = stacks(field, start, min(end, as_of))
    feats = field_features(stack.histories([field])[field.id])
    c = field.geometry.centroid
    near = fires_near(fires, c.y, c.x, th.fire_radius_m, start, min(end, as_of)) if th.fire_radius_m else []
    d = decide(feats, th, len(near), start, min(end, as_of))

    key = f"evidence/{claim_id}.png"
    store.put_blob(key, evidence.render(stack, field, d.burn_date), "image/png")
    claim.update({
        "status": d.outcome,
        "decision": d.as_dict(),
        "evidence_key": key,
        "series": [{"date": x.date.isoformat(), "nbr": _r(x.nbr), "nir": _r(x.nir), "brightness": _r(x.brightness),
                    "valid": round(x.valid_share, 2)} for x in feats],
        "fires": [{"lat": f.lat, "lon": f.lon, "date": f.date.isoformat(), "source": f.source} for f in near],
        "processed_at": now_iso(),
    })
    _speak(store, claim, speaker)
    store.put("claims", claim_id, claim)
    store.add_event(claim_id, {"type": "decided", "by": "system", "outcome": d.outcome, "rule": d.rule,
                               "reason": d.reason})
    return claim


def review(store: Store, claim_id: str, officer_id: str, verdict: str, note: str = "",
           speaker: Speaker | None = None) -> dict:
    claim = store.get("claims", claim_id)
    if claim is None:
        raise WorkflowError(f"unknown claim {claim_id}")
    if not officer_id or not officer_id.strip():
        raise WorkflowError("officer id is required")
    if verdict not in OFFICER_VERDICTS:
        raise WorkflowError(f"verdict must be one of {sorted(OFFICER_VERDICTS)}")
    if claim["status"] not in REVIEW_STATES:
        raise WorkflowError(f"claim is {claim['status']}, not waiting for review")
    claim["status"] = OFFICER_VERDICTS[verdict]
    claim["review"] = {"officer_id": officer_id.strip(), "verdict": verdict, "note": note, "at": now_iso()}
    _speak(store, claim, speaker)
    store.put("claims", claim_id, claim)
    store.add_event(claim_id, {"type": "reviewed", "by": officer_id.strip(), "verdict": verdict, "note": note})
    return claim


def queue(store: Store) -> list[dict]:
    order = {"possible_burn": 0, "needs_review": 1}
    return sorted((c for c in store.list("claims") if c["status"] in REVIEW_STATES),
                  key=lambda c: (order[c["status"]], c["created_at"]))


def _r(v):
    return None if v != v else round(v, 4)
