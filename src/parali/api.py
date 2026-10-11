"""HTTP routes. Pure function of (method, path, body) so API Gateway and the local server share it."""
import hmac
import json
import os
import re
from dataclasses import dataclass
from typing import Callable

from parali import payments, season, service
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
    notify: Callable[[dict], None] | None = None             # tell the farmer an officer decided (WhatsApp)
    followup: Callable[[str], None] | None = None            # run the slow part of a decision in the background
    payments: Callable[[], object] | None = None             # Razorpay client for recovering advances, or None
    payouts: Callable[[], object] | None = None              # Cashfree client for paying balances, or None (simulated)
    base_url: Callable[[], str] | None = None                # public address Razorpay sends the payer back to


def _json(status: int, body) -> tuple[int, dict, bytes]:
    return status, {"Content-Type": "application/json"}, json.dumps(body, default=str).encode()


def _pin_ok(deps: Deps, headers: dict) -> bool:
    if not deps.officer_pin:
        return True
    given = {k.lower(): v for k, v in headers.items()}.get("x-officer-pin", "")
    return hmac.compare_digest(given, deps.officer_pin)


def _claim_view(store: Store, c: dict) -> dict:
    out = dict(c)
    for k in ("evidence_key", "audio_key", "audio_key_pa", "audio_key_hr", "audio_key_en", "notice_key"):
        if c.get(k):
            out[k.replace("_key", "_url")] = store.blob_url(c[k])
    if (c.get("payout") or {}).get("receipt_key"):
        out["payout"] = {**c["payout"], "receipt_url": store.blob_url(c["payout"]["receipt_key"])}
    return out


def _rp(deps: Deps):
    return deps.payments() if deps.payments else None


def handle(method: str, path: str, body: bytes | None, headers: dict, deps: Deps,
           query: dict | None = None) -> tuple[int, dict, bytes]:
    s = deps.store
    if method == "GET" and path == "/api/razorpay/return":
        return _razorpay_return(deps, query or {})
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
            return _json(200, {"voice_in": deps.transcriber is not None or _sarvam_on(), "voice_out": deps.speaker is not None,
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
            c = payments.cancel(s, c, _rp(deps))
            return _json(200, _claim_view(s, c))
        m = re.fullmatch(r"/api/claims/([0-9a-f]{6,32})/recovery/check", path)
        if method == "POST" and m:
            c = s.get("claims", m.group(1))
            if c is None:
                return _json(404, {"error": "not found"})
            return _json(200, _claim_view(s, payments.check(s, c, _rp(deps))))
        m = re.fullmatch(r"/api/claims/([0-9a-f]{6,32})/payout/check", path)
        if method == "POST" and m:
            # anyone may ask whether a pending payout landed; only an officer may send a failed one again
            from parali import payouts
            c = s.get("claims", m.group(1))
            if c is None:
                return _json(404, {"error": "not found"})
            cf = deps.payouts() if deps.payouts else None
            c = payouts.refresh(s, c, cf)
            if (c.get("payout") or {}).get("status") in payouts.FAILED and _pin_ok(deps, headers) and data.get("retry"):
                c = payouts.release(s, c, cf)
            return _json(200, _claim_view(s, c))
        m = re.fullmatch(r"/api/claims/([0-9a-f]{6,32})/review", path)
        if method == "POST" and m:
            if not _pin_ok(deps, headers):
                return _json(403, {"error": "officer PIN required"})
            # the decision is saved and answered at once; the link, notice, voice notes and WhatsApp follow
            c = service.review(s, m.group(1), str(data.get("officer_id", "")), str(data.get("verdict", "")),
                               str(data.get("note", ""))[:500], None)
            if deps.followup:
                deps.followup(c["id"])
            else:
                c = service.after_decision(s, c["id"], deps.speaker, _rp(deps), deps.base_url() if deps.base_url else "", deps.notify,
                                           deps.payouts() if deps.payouts else None)
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


def _razorpay_return(deps: Deps, q: dict) -> tuple[int, dict, bytes]:
    """Razorpay sends the payer here after a payment link. Signed with our key secret, so it cannot be forged."""
    rp = _rp(deps)
    ref = q.get("razorpay_payment_link_reference_id", "")
    claim = deps.store.get("claims", ref.split("-")[0]) if re.fullmatch(r"[0-9a-f]{6,32}-\d+", ref) else None
    ok = rp is not None and claim is not None and payments.signature_ok(q, rp.key_secret)
    if ok and q.get("razorpay_payment_link_status") == "paid" \
            and (claim.get("recovery") or {}).get("link_id") == q.get("razorpay_payment_link_id"):
        claim = payments.mark_paid(deps.store, claim, q["razorpay_payment_id"])
        claim = service.respeak(deps.store, claim, deps.speaker)  # the voice note says it is settled, too
        if deps.notify:
            deps.notify(claim)  # and WhatsApp confirms the payment
        return 302, {"Location": f"/farmer.html?paid={claim['id']}"}, b""
    return 302, {"Location": "/farmer.html?paid=failed"}, b""


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


def _wav(pcm: bytes, rate: int = 16000) -> bytes:
    import io
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
    return buf.getvalue()


SPEECH_LANG = {"pa": "pa-IN", "hi": "hi-IN", "hr": "hi-IN", "en": "en-IN"}
READABLE = re.compile(r"[\u0900-\u097f\u0a00-\u0a7fA-Za-z]")


def _hear(deps: Deps, pcm: bytes, lang: str = "hi") -> str:
    """Sarvam first, told the page's language (left to guess, it once heard a short Hindi clip as Malayalam).
    AWS Transcribe (Hindi) if Sarvam is unavailable or returns something in another script."""
    from parali import sarvam
    heard = sarvam.transcribe(_wav(pcm), "audio/wav", SPEECH_LANG.get(lang, "hi-IN")) if sarvam.api_key() else None
    if heard and heard[0] and READABLE.search(heard[0]):
        return heard[0]
    text = deps.transcriber(pcm) if deps.transcriber else ""
    return text if text and READABLE.search(text) else ""


def _agent_turn(deps: Deps, data: dict) -> dict:
    import base64
    import uuid

    from parali import agent
    farmer_id = str(data.get("farmer_id", ""))
    if deps.store.get("fields", farmer_id) is None:
        raise service.WorkflowError("unknown farmer")
    text = str(data.get("text", ""))[:500]
    transcript = None
    lang = data.get("lang") if data.get("lang") in ("hi", "en", "pa", "hr") else "hi"
    if data.get("audio_b64"):
        pcm = base64.b64decode(data["audio_b64"])[: 16000 * 2 * 30]
        text = transcript = _hear(deps, pcm, lang)
        if not text:  # nothing usable was heard: say so, in the page's language, instead of guessing
            from parali.whatsapp import NOT_HEARD
            return {"transcript": None, "text": "", "hi": NOT_HEARD["hi"], "en": NOT_HEARD["en"], lang: NOT_HEARD[lang],
                    "tools": [], "mode": "unheard", "note": "voice not understood"}
    r = agent.respond(deps.store, farmer_id, text, deps.dispatch, backend=deps.agent_backend)
    out = {"transcript": transcript, "text": text, "hi": r.hi, "en": r.en, "tools": r.tools, "mode": r.mode,
           "note": r.note}
    from parali.tts import speak
    said = {"hi": r.hi, "en": r.en, "pa": r.pa, "hr": r.hr}[lang]
    if lang == "pa" and not said and r.hi and hasattr(deps.speaker, "translate_pa"):
        said = deps.speaker.translate_pa(r.hi)  # only the model's own short question has no template
    if not said:
        lang, said = "hi", r.hi
    if lang in ("pa", "hr"):
        out[lang] = said
    mp3 = speak(deps.speaker, said, lang) or (speak(deps.speaker, r.hi, "hi") if lang != "hi" else None)
    if mp3:
        key = f"agent/{uuid.uuid4().hex[:12]}-{lang}.mp3"
        deps.store.put_blob(key, mp3, "audio/mpeg")
        out["audio_url"] = deps.store.blob_url(key)
    return out


def _sarvam_on() -> bool:
    from parali import sarvam
    return bool(sarvam.api_key())


def officer_pin_from_env() -> str | None:
    return os.environ.get("OFFICER_PIN") or None
