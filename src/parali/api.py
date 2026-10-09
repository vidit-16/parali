"""HTTP routes. Pure function of (method, path, body) so API Gateway and the local server share it."""
import hmac
import json
import os
import re
from dataclasses import dataclass
from typing import Callable

from parali import season, service
from parali.store import Store


@dataclass
class Deps:
    store: Store
    dispatch: Callable[[str], None]          # start processing a claim (async on AWS)
    officer_pin: str | None = None
    speaker: Callable[[str], bytes] | None = None
    reset: Callable[[], None] | None = None
    agent_backend: object | None = None                      # None: scripted assistant
    transcriber: Callable[[bytes], str] | None = None        # 16 kHz PCM -> Hindi text
    fires: Callable[[], list] | None = None                  # FIRMS points for the season
    dispatch_check: Callable[[str], None] | None = None      # start a check-any-field job


def _json(status: int, body) -> tuple[int, dict, bytes]:
    return status, {"Content-Type": "application/json"}, json.dumps(body, default=str).encode()


def _pin_ok(deps: Deps, headers: dict) -> bool:
    if not deps.officer_pin:
        return True
    given = {k.lower(): v for k, v in headers.items()}.get("x-officer-pin", "")
    return hmac.compare_digest(given, deps.officer_pin)


def _claim_view(store: Store, c: dict) -> dict:
    out = dict(c)
    for k in ("evidence_key", "audio_key", "audio_key_pa", "notice_key"):
        if c.get(k):
            out[k.replace("_key", "_url")] = store.blob_url(c[k])
    return out


def handle(method: str, path: str, body: bytes | None, headers: dict, deps: Deps) -> tuple[int, dict, bytes]:
    s = deps.store
    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return _json(400, {"error": "body must be JSON"})
    try:
        if method == "GET" and path == "/api/fields":
            return _json(200, s.list("fields"))
        if method == "GET" and path == "/api/claims":
            return _json(200, [_claim_view(s, c) for c in s.list("claims")])
        if method == "GET" and path == "/api/fires":
            pts = deps.fires() if deps.fires else []
            return _json(200, [{"lat": f.lat, "lon": f.lon, "date": f.date.isoformat(), "source": f.source} for f in pts])
        if method == "GET" and path == "/api/stats":
            return _json(200, _stats(s))
        if method == "GET" and path == "/api/config":
            return _json(200, {"voice_in": deps.transcriber is not None, "voice_out": deps.speaker is not None,
                               "model": getattr(deps.agent_backend, "mode", "scripted")})
        if method == "GET" and path == "/api/officer/check":
            return _json(200, {"ok": True}) if _pin_ok(deps, headers) else _json(403, {"error": "wrong PIN"})
        if method == "GET" and path == "/api/queue":
            return _json(200, [_claim_view(s, c) for c in service.queue(s)])
        m = re.fullmatch(r"/api/claims/([0-9a-f]{6,32})", path)
        if method == "GET" and m:
            c = s.get("claims", m.group(1))
            if c is None:
                return _json(404, {"error": "not found"})
            return _json(200, {**_claim_view(s, c), "events": s.events(c["id"])})
        if method == "POST" and path == "/api/claims":
            c = service.create_claim(s, str(data.get("field_id", "")), *season.SEASON)
            deps.dispatch(c["id"])
            return _json(201, _claim_view(s, c))
        m = re.fullmatch(r"/api/claims/([0-9a-f]{6,32})/appeal", path)
        if method == "POST" and m:
            c = service.appeal(s, m.group(1), str(data.get("note", "")), deps.speaker)
            return _json(200, _claim_view(s, c))
        m = re.fullmatch(r"/api/claims/([0-9a-f]{6,32})/review", path)
        if method == "POST" and m:
            if not _pin_ok(deps, headers):
                return _json(403, {"error": "officer PIN required"})
            c = service.review(s, m.group(1), str(data.get("officer_id", "")), str(data.get("verdict", "")),
                               str(data.get("note", ""))[:500], deps.speaker)
            return _json(200, _claim_view(s, c))
        if method == "POST" and path == "/api/check":
            from parali import check
            if deps.dispatch_check is None:
                return _json(503, {"error": "field checks are not available here"})
            try:
                item = check.create(s, data.get("geometry") or {})
            except check.CheckError as e:
                return _json(400, {"error": str(e)})
            deps.dispatch_check(item["id"])
            return _json(201, item)
        m = re.fullmatch(r"/api/check/([0-9a-f]{12})", path)
        if method == "GET" and m:
            item = s.get("checks", m.group(1))
            if item is None:
                return _json(404, {"error": "not found"})
            for r in (item.get("result") or {}).values():
                r["evidence_url"] = s.blob_url(r["evidence_key"])
            return _json(200, item)
        if method == "POST" and path == "/api/agent":
            return _json(200, _agent_turn(deps, data))
        if method == "POST" and path == "/api/demo/reset":
            if not _pin_ok(deps, headers) or deps.reset is None:
                return _json(403, {"error": "officer PIN required"})
            deps.reset()
            return _json(200, {"ok": True})
    except service.WorkflowError as e:
        return _json(409, {"error": str(e)})
    return _json(404, {"error": "no such route"})


def _stats(s: Store) -> dict:
    claims = s.list("claims")
    by = {}
    for c in claims:
        by[c["status"]] = by.get(c["status"], 0) + 1
    adv = [c.get("advance") or {} for c in claims]
    return {
        "claims": len(claims),
        "by_status": by,
        "advances_paid": sum(1 for a in adv if a.get("status") == "paid"),
        "advance_amount": sum(a.get("amount", 0) for a in adv if a.get("status") == "paid"),
        "to_recover": sum((c.get("settlement") or {}).get("recover") or 0 for c in claims),
    }


def _agent_turn(deps: Deps, data: dict) -> dict:
    import base64
    import uuid

    from parali import agent
    farmer_id = str(data.get("farmer_id", ""))
    if deps.store.get("fields", farmer_id) is None:
        raise service.WorkflowError("unknown farmer")
    text = str(data.get("text", ""))[:500]
    transcript = None
    if data.get("audio_b64") and deps.transcriber:
        pcm = base64.b64decode(data["audio_b64"])[: 16000 * 2 * 30]
        text = transcript = deps.transcriber(pcm)
    r = agent.respond(deps.store, farmer_id, text, deps.dispatch, backend=deps.agent_backend)
    out = {"transcript": transcript, "text": text, "hi": r.hi, "en": r.en, "tools": r.tools, "mode": r.mode,
           "note": r.note}
    pa = mp3 = None
    if data.get("lang") == "pa" and r.hi:
        # templates carry their own Punjabi; only the model's free-text question needs translating
        pa = r.pa or (deps.speaker.translate_pa(r.hi) if hasattr(deps.speaker, "translate_pa") else None)
        mp3 = deps.speaker.speak_pa(pa) if pa and hasattr(deps.speaker, "speak_pa") else None
    if pa:
        out["pa"] = pa
    if mp3:
        key = f"agent/{uuid.uuid4().hex[:12]}-pa.mp3"
        deps.store.put_blob(key, mp3, "audio/mpeg")
        out["audio_url"] = deps.store.blob_url(key)
    elif deps.speaker and r.hi:
        key = f"agent/{uuid.uuid4().hex[:12]}.mp3"
        deps.store.put_blob(key, deps.speaker(r.hi), "audio/mpeg")
        out["audio_url"] = deps.store.blob_url(key)
    return out


def officer_pin_from_env() -> str | None:
    return os.environ.get("OFFICER_PIN") or None
