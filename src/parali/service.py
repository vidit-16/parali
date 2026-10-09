"""Claim workflow, shared by the Lambda handlers and the local demo server.

Before harvest: assess_advance checks last season; a clean field is offered a 50% advance.
After harvest:  submitted -> auto_approved | needs_review | possible_burn
                needs_review | possible_burn -> officer_approved | officer_confirmed_burnt (officer id required)
Settlement follows the final status: balance released, or the advance recovered (notice drafted for the officer).
"""
import uuid
from datetime import date
from typing import Callable

from typing import TYPE_CHECKING

from parali import notice, season
from parali.messages import farmer_text
from parali.store import Store, now_iso

if TYPE_CHECKING:  # imagery stack pulls in rasterio; keep it out of the agent Lambda
    from parali.area import AreaStack
    from parali.fields import Field
    from parali.firms import Fire
    from parali.rules import Thresholds

REVIEW_STATES = ("needs_review", "possible_burn")
OFFICER_VERDICTS = {"approve": "officer_approved", "confirm_burnt": "officer_confirmed_burnt"}

StackProvider = Callable[["Field", date, date], "AreaStack"]
Speaker = Callable[[str], bytes]


class WorkflowError(ValueError):
    pass


def field_from_item(item: dict) -> "Field":
    from shapely.geometry import shape

    from parali.fields import Field
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
        "farmer_name_hi": f.get("farmer_hi", ""),
        "field_name_hi": f.get("name_hi", ""),
        "village": f.get("village", ""),
        "acres": f.get("acres"),
        "state_code": f.get("state", season.DEFAULT_STATE),
        "season_start": season_start,
        "season_end": season_end,
        "as_of": as_of or season_end,
        "status": "submitted",
        "created_at": now_iso(),
    }
    store.put("claims", claim["id"], claim)
    store.add_event(claim["id"], {"type": "submitted", "by": "farmer"})
    return claim


def _decide_season(field: "Field", stacks: StackProvider, fires: "list[Fire]", th: "Thresholds", start: date, end: date):
    from parali.features import field_features
    from parali.firms import fires_near
    from parali.rules import decide
    stack = stacks(field, start, end)
    feats = field_features(stack.histories([field])[field.id])
    c = field.geometry.centroid
    near = fires_near(fires, c.y, c.x, th.fire_radius_m, start, end) if th.fire_radius_m else []
    return stack, feats, near, decide(feats, th, len(near), start, end)


def assess_advance(store: Store, claim_id: str, stacks: StackProvider, fires: "list[Fire]", th: "Thresholds",
                   prev_start: str, prev_end: str) -> dict:
    """Check last season for this field and offer the advance if it was clean."""
    claim = _get(store, claim_id)
    field = field_from_item(store.get("fields", claim["field_id"]))
    s, e = date.fromisoformat(prev_start), date.fromisoformat(prev_end)
    _, _, _, d = _decide_season(field, stacks, fires, th, s, e)
    eligible = season.advance_eligible(d.outcome)
    claim["advance"] = {
        "prev_season": str(s.year),
        "prev_outcome": d.outcome,
        "prev_rule": d.rule,
        "prev_reason": d.reason,
        "eligible": eligible,
        "amount": season.advance_amount(claim.get("acres") or 0, claim.get("state_code")) if eligible else 0,
        "status": "offered" if eligible else "not_eligible",
    }
    store.put("claims", claim_id, claim)
    store.add_event(claim_id, {"type": "advance_assessed", "by": "system", "eligible": eligible,
                               "prev_outcome": d.outcome})
    return claim


def disburse_advance(store: Store, claim_id: str, by: str) -> dict:
    claim = _get(store, claim_id)
    adv = claim.get("advance") or {}
    if adv.get("status") != "offered":
        raise WorkflowError("no advance on offer for this claim")
    adv["status"] = "paid"
    adv["paid_at"] = now_iso()
    store.put("claims", claim_id, claim)
    store.add_event(claim_id, {"type": "advance_paid", "by": by, "amount": adv["amount"]})
    return claim


def _settle(store: Store, claim: dict) -> None:
    adv = claim.get("advance") or {}
    paid = adv.get("amount", 0) if adv.get("status") == "paid" else 0
    if (claim.get("recovery") or {}).get("status") == "paid":
        paid = 0  # the advance came back; if an appeal wins later, the whole amount is due
    before = (claim.get("settlement") or {}).get("state")
    claim["settlement"] = season.settle(claim["status"], claim.get("acres") or 0, paid, claim.get("state_code"))
    st = claim["settlement"]
    # the payment record: one event each time money is released or asked back (the rail is simulated)
    if st["state"] != before:
        if st["state"] == "balance_due" and st["balance"]:
            st["released_at"] = now_iso()
            store.add_event(claim["id"], {"type": "balance_released", "by": "system", "amount": st["balance"],
                                          "rail": "DBT, simulated"})
        elif st["state"] == "recover_advance":
            store.add_event(claim["id"], {"type": "recovery_notice", "by": "system", "amount": st["recover"]})
    if claim["settlement"]["state"] == "recover_advance" and claim.get("evidence_key"):
        key = f"notices/{claim['id']}.html"
        store.put_blob(key, notice.render(claim, store.blob_url(claim["evidence_key"])).encode(), "text/html; charset=utf-8")
        claim["notice_key"] = key


def _get(store: Store, claim_id: str) -> dict:
    claim = store.get("claims", claim_id)
    if claim is None:
        raise WorkflowError(f"unknown claim {claim_id}")
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
    claim.pop("audio_key_pa", None)
    # Punjab's farmers also hear it in Punjabi; without Sarvam they get the Hindi audio
    if claim.get("state_code") == "PB" and hasattr(speaker, "speak_pa"):
        mp3 = speaker.speak_pa(text["pa"])
        if mp3:
            key = f"audio/{claim['id']}-{claim['status']}-pa.mp3"
            store.put_blob(key, mp3, "audio/mpeg")
            claim["audio_key_pa"] = key


def process_claim(store: Store, claim_id: str, stacks: StackProvider, fires: "list[Fire]", th: "Thresholds",
                  speaker: Speaker | None = None) -> dict:
    claim = store.get("claims", claim_id)
    if claim is None:
        raise WorkflowError(f"unknown claim {claim_id}")
    if claim["status"] not in ("submitted",) + REVIEW_STATES:
        raise WorkflowError(f"claim is already {claim['status']}")
    field = field_from_item(store.get("fields", claim["field_id"]))
    start, end = date.fromisoformat(claim["season_start"]), date.fromisoformat(claim["season_end"])
    as_of = date.fromisoformat(claim["as_of"])
    stack, feats, near, d = _decide_season(field, stacks, fires, th, start, min(end, as_of))

    from parali import evidence
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
    _settle(store, claim)
    _speak(store, claim, speaker)
    store.put("claims", claim_id, claim)
    store.add_event(claim_id, {"type": "decided", "by": "system", "outcome": d.outcome, "rule": d.rule,
                               "reason": d.reason})
    return claim


def run_season(store: Store, claim_id: str, stacks: StackProvider, fires: "list[Fire]", th: "Thresholds",
               speaker: Speaker | None = None) -> dict:
    """Demo path for one claim: last-season check, advance paid if eligible (by the department, before
    harvest), then this season's check and settlement."""
    # Safe to run twice: Lambda retries a failed async run, and a retry must not assess or pay the
    # advance again, or fail because it was already paid.
    claim = _get(store, claim_id)
    if not claim.get("advance"):
        claim = assess_advance(store, claim_id, stacks, fires, th, *season.PREV_SEASON)
    if claim["advance"].get("status") == "offered":
        disburse_advance(store, claim_id, "department")
    claim = _get(store, claim_id)
    if claim["status"] not in ("submitted",) + REVIEW_STATES:
        return claim  # already decided by an earlier run
    return process_claim(store, claim_id, stacks, fires, th, speaker)


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
    _settle(store, claim)
    _speak(store, claim, speaker)
    store.put("claims", claim_id, claim)
    store.add_event(claim_id, {"type": "reviewed", "by": officer_id.strip(), "verdict": verdict, "note": note})
    return claim


def respeak(store: Store, claim: dict, speaker: Speaker | None = None) -> dict:
    """Rewrite the farmer's message after something outside the workflow changed the claim (a payment link)."""
    _speak(store, claim, speaker)
    store.put("claims", claim["id"], claim)
    return claim


APPEALABLE = REVIEW_STATES + ("officer_confirmed_burnt",)


def appeal(store: Store, claim_id: str, note: str, speaker: Speaker | None = None) -> dict:
    """The farmer says the satellite is wrong. The note goes on the claim for the officer; a confirmed burn
    goes back to the officer's queue, and nothing is recovered while the appeal is open."""
    claim = _get(store, claim_id)
    if claim["status"] not in APPEALABLE:
        raise WorkflowError(f"claim is {claim['status']}; there is nothing to appeal")
    note = (note or "").strip()[:500]
    if not note:
        raise WorkflowError("say in a line why the satellite is wrong")
    claim["appeal"] = {"note": note, "at": now_iso()}
    if claim["status"] == "officer_confirmed_burnt":
        claim["status"] = "needs_review"
        _settle(store, claim)
    _speak(store, claim, speaker)  # the farmer's message must not still say "repay"
    store.put("claims", claim_id, claim)
    store.add_event(claim_id, {"type": "appeal", "by": "farmer", "note": note})
    return claim


def queue(store: Store) -> list[dict]:
    order = {"possible_burn": 0, "needs_review": 1}
    return sorted((c for c in store.list("claims") if c["status"] in REVIEW_STATES),
                  key=lambda c: (0 if c.get("appeal") else 1, order[c["status"]], c["created_at"]))


def _r(v):
    return None if v != v else round(v, 4)
