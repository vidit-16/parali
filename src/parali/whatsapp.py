"""WhatsApp for farmers, on Meta's WhatsApp Cloud API.

A farmer texts or sends a voice note in Hindi, Punjabi or Hinglish and gets the same answer the app gives,
as text and as a voice note. The answer comes from agent.respond, so the same tools and the same guard
apply: nothing said on WhatsApp can approve, reject or pay.

The webhook answers Meta at once and handles each message in a separate async invocation, because Meta
re-sends any webhook that takes more than a few seconds, and an answer takes 5 to 15.

The demo has no farmer registry, so the first message from a new number gets the list of demo farmers and
the reply with a number links that phone to one of them ("change" shows the list again).
"""
import hashlib
import hmac
import json
import os
import re
import urllib.error
import urllib.request
import uuid

from parali import agent, season
from parali.service import REVIEW_STATES as REVIEW
from parali.messages import hi_date, pa_date, rupees, to_gurmukhi
from parali.store import Store, now_iso

GRAPH = "https://graph.facebook.com/" + os.environ.get("WA_GRAPH_VERSION", "v23.0")
PARAMS = "/saakshi/whatsapp/"
CHANGE = re.compile(r"^\s*(change|menu|badlo|बदलो|बदलें|ਬਦਲੋ|ਬਦਲੋ ਜੀ)\s*$", re.I)


_config: dict = {}


def config() -> dict:
    """token, phone_number_id, app_secret, verify_token: from SSM on Lambda, WA_* variables locally.
    Kept for the life of the container once complete; read again while any is missing."""
    if os.environ.get("WA_TOKEN"):
        return {k: os.environ.get("WA_" + k.upper(), "") for k in ("token", "phone_number_id", "app_secret", "verify_token")}
    if not all(_config.get(k) for k in ("token", "phone_number_id", "app_secret", "verify_token")):
        _config.clear()
        _config.update(_read_ssm())
    return _config


def _read_ssm() -> dict:
    import boto3
    ssm = boto3.client("ssm")
    out, kw = {}, {}
    while True:
        page = ssm.get_parameters_by_path(Path=PARAMS, WithDecryption=True, **kw)
        out.update({p["Name"].rsplit("/", 1)[-1]: p["Value"] for p in page["Parameters"]})
        if not page.get("NextToken"):
            return out
        kw = {"NextToken": page["NextToken"]}


# ---------- webhook ----------

def verify(query: dict, cfg: dict) -> tuple[int, str]:
    """Meta's one-time GET when the webhook URL is saved."""
    ok = (query.get("hub.mode") == "subscribe" and cfg.get("verify_token")
          and hmac.compare_digest(query.get("hub.verify_token", ""), cfg["verify_token"]))
    return (200, query.get("hub.challenge", "")) if ok else (403, "")


def signature_ok(body: bytes, header: str, app_secret: str) -> bool:
    if not app_secret or not header or not header.startswith("sha256="):
        return False
    want = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(header[7:], want)


def messages(payload: dict) -> list[dict]:
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for m in (change.get("value") or {}).get("messages", []):
                msg = {"id": m["id"], "from": m["from"], "type": m.get("type")}
                if m.get("type") == "text":
                    msg["text"] = m["text"].get("body", "")
                elif m.get("type") == "audio":
                    msg["media_id"], msg["mime"] = m["audio"]["id"], m["audio"].get("mime_type", "audio/ogg")
                elif m.get("type") == "interactive":
                    r = m["interactive"].get("button_reply") or m["interactive"].get("list_reply") or {}
                    msg["text"] = r.get("id") or r.get("title", "")
                out.append(msg)
    return out


# ---------- Graph API ----------

class Client:
    def __init__(self, cfg: dict):
        self.cfg = cfg

    def _call(self, url: str, body: bytes | None = None, ctype: str = "application/json") -> dict:
        h = {"Authorization": f"Bearer {self.cfg['token']}"}
        if body is not None:
            h["Content-Type"] = ctype
        with urllib.request.urlopen(urllib.request.Request(url, body, h), timeout=15) as r:
            return json.loads(r.read() or b"{}")

    def _send(self, to: str, kind: str, content: dict) -> dict:
        body = {"messaging_product": "whatsapp", "to": to, "type": kind, kind: content}
        return self._call(f"{GRAPH}/{self.cfg['phone_number_id']}/messages", json.dumps(body).encode())

    def send_text(self, to: str, text: str) -> dict:
        return self._send(to, "text", {"body": text[:4000], "preview_url": False})

    def send_audio(self, to: str, mp3: bytes) -> dict:
        return self._send(to, "audio", {"id": self._upload(mp3, "audio/mpeg", "reply.mp3")})

    def send_image(self, to: str, png: bytes, caption: str = "") -> dict:
        return self._send(to, "image", {"id": self._upload(png, "image/png", "field.png"), "caption": caption[:1000]})

    def _upload(self, data: bytes, mime: str, name: str) -> str:
        b = uuid.uuid4().hex
        body = (f'--{b}\r\nContent-Disposition: form-data; name="messaging_product"\r\n\r\nwhatsapp\r\n'
                f'--{b}\r\nContent-Disposition: form-data; name="type"\r\n\r\n{mime}\r\n'
                f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'
                ).encode() + data + f"\r\n--{b}--\r\n".encode()
        return self._call(f"{GRAPH}/{self.cfg['phone_number_id']}/media", body, f"multipart/form-data; boundary={b}")["id"]

    def send_buttons(self, to: str, body: str, buttons: list[tuple[str, str]]) -> dict:
        """Up to three tap buttons under a short message; a tap comes back as a message with the button's id."""
        return self._send(to, "interactive", {"type": "button", "body": {"text": body[:1024]}, "action": {"buttons": [
            {"type": "reply", "reply": {"id": i, "title": title[:20]}} for i, title in buttons[:3]]}})

    def send_list(self, to: str, body: str, button: str, rows: list[tuple[str, str, str]]) -> dict:
        """A tap-to-pick list of up to ten rows: (id, title, description)."""
        return self._send(to, "interactive", {"type": "list", "body": {"text": body[:1024]}, "action": {"button": button[:20],
            "sections": [{"title": button[:24], "rows": [{"id": i, "title": ti[:24], "description": d[:72]} for i, ti, d in rows[:10]]}]}})

    def download(self, media_id: str) -> tuple[bytes, str]:
        meta = self._call(f"{GRAPH}/{media_id}")
        req = urllib.request.Request(meta["url"], headers={"Authorization": f"Bearer {self.cfg['token']}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read(), meta.get("mime_type", "audio/ogg")

    def mark_read(self, message_id: str) -> None:
        body = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
        self._call(f"{GRAPH}/{self.cfg['phone_number_id']}/messages", json.dumps(body).encode())


def set_profile(cfg: dict, png: bytes, about: str = "", description: str = "") -> dict:
    """Profile photo (Meta's resumable upload, then the business profile) plus the about line."""
    c = Client(cfg)
    app_id = c._call(f"{GRAPH}/debug_token?input_token={cfg['token']}")["data"]["app_id"]
    session = c._call(f"{GRAPH}/{app_id}/uploads?file_name=saakshi.png&file_length={len(png)}&file_type=image/png", b"",
                      "application/x-www-form-urlencoded")["id"]
    req = urllib.request.Request(f"{GRAPH}/{session}", png, {"Authorization": f"OAuth {cfg['token']}", "file_offset": "0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        handle = json.loads(r.read())["h"]
    body = {"messaging_product": "whatsapp", "profile_picture_handle": handle}
    if about:
        body["about"] = about[:139]
    if description:
        body["description"] = description[:512]
    try:
        return c._call(f"{GRAPH}/{cfg['phone_number_id']}/whatsapp_business_profile", json.dumps(body).encode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": json.loads(e.read() or b"{}").get("error", {}).get("message")}


def setup(cfg: dict, waba: str | None = None) -> dict:
    """Check the token and subscribe the app to the WhatsApp Business Account that owns the number, without
    which Meta sends no message webhooks. Returns only non-secret details."""
    c = Client(cfg)

    def safe(url, body=None):
        try:
            return c._call(url, body, "application/x-www-form-urlencoded") if body is not None else c._call(url)
        except urllib.error.HTTPError as e:
            return {"error": e.code, "message": json.loads(e.read() or b"{}").get("error", {}).get("message")}

    d = safe(f"{GRAPH}/debug_token?input_token={cfg['token']}").get("data", {})
    wabas = sorted({t for s in d.get("granular_scopes", []) if s.get("scope", "").startswith("whatsapp")
                    for t in s.get("target_ids", [])} | ({waba} if waba else set()))
    out = {"token_valid": d.get("is_valid"), "token_type": d.get("type"), "expires_at": d.get("expires_at"),
           "scopes": d.get("scopes"), "wabas": {},
           "phone": safe(f"{GRAPH}/{cfg['phone_number_id']}?fields=display_phone_number,verified_name")}
    for w in wabas:
        out["wabas"][w] = {"before": safe(f"{GRAPH}/{w}/subscribed_apps"),
                           "subscribe": safe(f"{GRAPH}/{w}/subscribed_apps", b"")}
    return out


# ---------- conversation ----------

HINGLISH = re.compile(r"\b(kya|kab|kaise|kyun|kyon|mera|meri|mere|paisa|paise|khet|dawa|daava|hai|nahi|nahin|milega|batao|kitna|ji|"
                      r"haan|aapka|kar|ho|gaya|kad|kyu|thara|mhara)\b", re.I)


def lang_of(text: str, farmer: dict | None = None, heard: str = "") -> str:
    """The language to answer in: Punjabi for Gurmukhi, Haryanvi for a Haryana farmer writing Devanagari or Hinglish,
    Hindi for other Devanagari or Hinglish, English for English. A voice note uses the language Sarvam heard."""
    hr = (farmer or {}).get("state") == "HR"
    if heard:
        return "pa" if heard.startswith("pa") else "en" if heard.startswith("en") else ("hr" if hr else "hi")
    if re.search(r"[\u0a00-\u0a7f]", text or ""):
        return "pa"
    if re.search(r"[\u0900-\u097f]", text or "") or HINGLISH.search(text or ""):
        return "hr" if hr else "hi"
    if re.search(r"[A-Za-z]", text or ""):
        return "en"
    return "pa" if (farmer or {}).get("state") == "PB" else ("hr" if hr else "hi")


def _farmers(store: Store) -> list[dict]:
    return sorted((f for f in store.list("fields") if f.get("farmer")), key=lambda f: (f.get("state") != "PB", f["id"]))


def _name(f: dict) -> str:
    """A farmer's name in their own script: Gurmukhi in Punjab, Devanagari in Haryana."""
    hi = f.get("farmer_hi") or f.get("farmer", "")
    return to_gurmukhi(hi) if f.get("state") == "PB" else hi


# ---- short replies: two lines of text, the full explanation in the voice note ----
SHORT = {
    "en": dict(paid="Approved · ₹{x} sent to your bank", smoke=" · ≈ {kg} kg smoke avoided", repay="Burn confirmed · return ₹{x}",
               repaid="₹{x} returned · nothing more due", confirmed="The officer confirmed a burn", burn="Burn mark seen around {d} · the officer will check",
               review="With the officer · nothing to do now", wait="Satellite check running", appealed="Appeal with the officer · nothing is recovered meanwhile",
               adv="Advance ₹{x} paid", noadv="No advance this year", sent="₹{x} sent", held="₹{x} held until the officer decides",
               ret="₹{x} to return", retd="₹{x} returned", whyBurn="Burnt around {d}: dark in colour, maroon in infrared", whyClean="No burn in {n} clear pictures",
               whyReview="The pictures are not clear enough to decide", askAppeal="Tell the officer in one message why the satellite is wrong. A voice note is fine.",
               noAppeal="Nothing to appeal: your claim is approved.", bWhy="Why?", bMoney="My money", bAppeal="Appeal",
               intro="Saakshi. Pick a farmer to chat as. Write or speak in English, Hindi, Punjabi or Haryanvi; Saakshi answers in the same language. You can also just say a farmer's name.",
               state="Which state?", pick="Pick a farmer", list="Farmers"),
    "hi": dict(paid="मंज़ूर · ₹{x} आपके खाते में भेजे", smoke=" · ≈ {kg} किलो धुआँ बचा", repay="जलना पक्का · ₹{x} लौटाने हैं",
               repaid="₹{x} लौटा दिए · कुछ बाकी नहीं", confirmed="अधिकारी ने जलना पक्का किया", burn="{d} के आसपास जलने का निशान · अधिकारी देखेंगे",
               review="अधिकारी के पास · अभी कुछ नहीं करना", wait="उपग्रह जाँच चल रही है", appealed="अपील अधिकारी के पास · तब तक कोई वसूली नहीं",
               adv="₹{x} अग्रिम मिला", noadv="इस साल अग्रिम नहीं", sent="₹{x} भेजे", held="₹{x} अधिकारी के फ़ैसले तक रुके",
               ret="₹{x} लौटाने हैं", retd="₹{x} लौटाए", whyBurn="{d} के आसपास जला: रंगीन में काला, इन्फ्रारेड में मैरून", whyClean="{n} साफ़ तस्वीरों में कहीं जलना नहीं",
               whyReview="तस्वीरें फ़ैसले के लिए साफ़ नहीं", askAppeal="एक संदेश में अधिकारी को बताइए कि उपग्रह क्यों ग़लत है। बोलकर भी भेज सकते हैं।",
               noAppeal="अपील की ज़रूरत नहीं: आपका दावा मंज़ूर है।", bWhy="क्यों?", bMoney="मेरा पैसा", bAppeal="अपील"),
    "pa": dict(paid="ਮਨਜ਼ੂਰ · ₹{x} ਤੁਹਾਡੇ ਖਾਤੇ ਵਿੱਚ ਭੇਜੇ", smoke=" · ≈ {kg} ਕਿੱਲੋ ਧੂੰਆਂ ਬਚਿਆ", repay="ਸਾੜ ਪੱਕਾ · ₹{x} ਵਾਪਸ ਕਰਨੇ ਹਨ",
               repaid="₹{x} ਵਾਪਸ ਕੀਤੇ · ਕੁਝ ਬਾਕੀ ਨਹੀਂ", confirmed="ਅਧਿਕਾਰੀ ਨੇ ਸਾੜ ਪੱਕਾ ਕੀਤਾ", burn="{d} ਦੇ ਆਸ-ਪਾਸ ਸਾੜ ਦਾ ਨਿਸ਼ਾਨ · ਅਧਿਕਾਰੀ ਵੇਖੇਗਾ",
               review="ਅਧਿਕਾਰੀ ਕੋਲ · ਹਾਲੇ ਕੁਝ ਨਹੀਂ ਕਰਨਾ", wait="ਸੈਟੇਲਾਈਟ ਜਾਂਚ ਚੱਲ ਰਹੀ ਹੈ", appealed="ਅਪੀਲ ਅਧਿਕਾਰੀ ਕੋਲ · ਉਦੋਂ ਤੱਕ ਕੋਈ ਵਸੂਲੀ ਨਹੀਂ",
               adv="₹{x} ਅਗਾਊਂ ਮਿਲੀ", noadv="ਇਸ ਸਾਲ ਅਗਾਊਂ ਨਹੀਂ", sent="₹{x} ਭੇਜੇ", held="₹{x} ਅਧਿਕਾਰੀ ਦੇ ਫ਼ੈਸਲੇ ਤੱਕ ਰੁਕੇ",
               ret="₹{x} ਵਾਪਸ ਕਰਨੇ ਹਨ", retd="₹{x} ਵਾਪਸ ਕੀਤੇ", whyBurn="{d} ਦੇ ਆਸ-ਪਾਸ ਸੜਿਆ: ਰੰਗੀਨ ਵਿੱਚ ਕਾਲਾ, ਇਨਫ੍ਰਾਰੈੱਡ ਵਿੱਚ ਮੈਰੂਨ", whyClean="{n} ਸਾਫ਼ ਤਸਵੀਰਾਂ ਵਿੱਚ ਕਿਤੇ ਸਾੜ ਨਹੀਂ",
               whyReview="ਤਸਵੀਰਾਂ ਫ਼ੈਸਲੇ ਲਈ ਸਾਫ਼ ਨਹੀਂ", askAppeal="ਇੱਕ ਸੁਨੇਹੇ ਵਿੱਚ ਅਧਿਕਾਰੀ ਨੂੰ ਦੱਸੋ ਕਿ ਸੈਟੇਲਾਈਟ ਕਿਉਂ ਗਲਤ ਹੈ। ਬੋਲ ਕੇ ਵੀ ਭੇਜ ਸਕਦੇ ਹੋ।",
               noAppeal="ਅਪੀਲ ਦੀ ਲੋੜ ਨਹੀਂ: ਤੁਹਾਡਾ ਦਾਅਵਾ ਮਨਜ਼ੂਰ ਹੈ।", bWhy="ਕਿਉਂ?", bMoney="ਮੇਰਾ ਪੈਸਾ", bAppeal="ਅਪੀਲ"),
    "hr": dict(paid="मंजूर · ₹{x} थारे खाते म्ह भेजे", smoke=" · ≈ {kg} किलो धुम्मा बच्या", repay="जळाणा पक्का · ₹{x} उल्टे देणे सैं",
               repaid="₹{x} उल्टे दे दिए · कुछ बाकी कोनी", confirmed="अफसर नै जळाणा पक्का करया", burn="{d} के आसपास जळण का निसान · अफसर देक्खैगा",
               review="अफसर कनै · इब्ब कुछ ना करणा", wait="उपग्रह जांच चालू सै", appealed="अपील अफसर कनै · जद ताईं कोए वसूली कोनी",
               adv="₹{x} एडवांस मिल्या", noadv="इस साल एडवांस कोनी", sent="₹{x} भेजे", held="₹{x} अफसर के फैसले तक रुके",
               ret="₹{x} उल्टे देणे सैं", retd="₹{x} उल्टे दिए", whyBurn="{d} के आसपास जळया: रंगीन म्ह काळा, इन्फ्रारेड म्ह मैरून", whyClean="{n} साफ फोटुआं म्ह कितै जळाणा कोनी",
               whyReview="फोटू फैसले खातर साफ कोनी", askAppeal="एक संदेस म्ह अफसर नै बताओ उपग्रह क्यूं गलत सै। बोल कै भी भेज सको सो।",
               noAppeal="अपील की जरूरत कोनी: थारा दावा मंजूर सै।", bWhy="क्यूं?", bMoney="मेरा पीसा", bAppeal="अपील"),
}
CLEAN = ("auto_approved", "officer_approved")
APPEALABLE = ("possible_burn", "needs_review", "officer_confirmed_burnt")
TAP = re.compile(r"^(btn|f|state):[\w-]+$")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]")


def _w(lang: str) -> dict:
    return {**SHORT["en"], **SHORT[lang]}


def _day(iso: str | None, lang: str) -> str:
    from datetime import date
    if not iso:
        return ""
    if lang == "pa":
        return pa_date(iso)
    if lang in ("hi", "hr"):
        return hi_date(iso)
    d = date.fromisoformat(iso)
    return f"{d.day} {d:%b}"


def _claim_of(store: Store, field_id: str) -> dict | None:
    return next((c for c in store.list("claims") if c["field_id"] == field_id), None)


def _field_line(claim: dict, lang: str) -> str:
    name = claim.get("field_name", "") if lang == "en" else claim.get("field_name_hi") or claim.get("field_name", "")
    return to_gurmukhi(name) if lang == "pa" else name


def both(lang: str, make) -> str:
    """English first, then the farmer's own language: the short texts are read by judges as well as farmers.
    Someone who writes in English gets English only."""
    en = make("en")
    return en if lang == "en" else f"{en}\n{make(lang)}"


def _status_key(claim: dict) -> str:
    s, rec, st = claim.get("settlement") or {}, claim.get("recovery") or {}, claim["status"]
    if claim.get("appeal") and st in REVIEW:
        return "appealed"
    if st in CLEAN and s.get("state") == "balance_due":
        return "paid"
    if st == "officer_confirmed_burnt":
        return "repaid" if rec.get("status") == "paid" else "repay" if s.get("recover") else "confirmed"
    return {"possible_burn": "burn", "needs_review": "review"}.get(st, "wait")


# one mark per message, so good news and bad news can be told apart before reading a word
MARK = {"paid": "✅", "repaid": "✅", "repay": "❗", "confirmed": "❗", "burn": "❗", "review": "⏳", "wait": "⏳", "appealed": "⏳"}


def _status_line(claim: dict, lang: str) -> str:
    W, s, k = _w(lang), claim.get("settlement") or {}, _status_key(claim)
    x = rupees(s.get("balance") or 0) if k == "paid" else rupees(s.get("recover") or 0)
    line = W[k].format(x=x, d=_day((claim.get("decision") or {}).get("burn_date"), lang))
    return line + W["smoke"].format(kg=season.smoke_kg(claim.get("acres"))) if k == "paid" else line


def short_status(claim: dict, lang: str) -> str:
    """What happened and the one number that matters, then the field; the voice note has the rest."""
    rec = claim.get("recovery") or {}
    field = _field_line(claim, "en") if lang == "en" else f"{_field_line(claim, 'en')} · {_field_line(claim, lang)}"
    url = f"\n{rec['url']}" if claim["status"] == "officer_confirmed_burnt" and rec.get("status") == "issued" and rec.get("url") else ""
    return f"{MARK[_status_key(claim)]} " + both(lang, lambda l: _status_line(claim, l)) + url + "\n" + field


def _money(claim: dict, lang: str) -> str:
    W, adv, s, rec = _w(lang), claim.get("advance") or {}, claim.get("settlement") or {}, claim.get("recovery") or {}
    parts = [W["adv"].format(x=rupees(adv.get("amount") or 0)) if adv.get("status") == "paid" else W["noadv"]]
    if s.get("state") == "balance_due":
        parts.append(W["sent"].format(x=rupees(s.get("balance") or 0)))
    elif s.get("state") == "recover_advance":
        parts.append((W["retd"] if rec.get("status") == "paid" else W["ret"]).format(x=rupees(s.get("recover") or 0)))
    elif s.get("state") == "pending":
        parts.append(W["held"].format(x=rupees((s.get("total") or 0) - (adv.get("amount", 0) if adv.get("status") == "paid" else 0))))
    return " · ".join(parts)


def money_line(claim: dict, lang: str) -> str:
    return both(lang, lambda l: _money(claim, l))


def _why(claim: dict, lang: str) -> str:
    W, d = _w(lang), claim.get("decision") or {}
    if d.get("burn_date"):
        return W["whyBurn"].format(d=_day(d["burn_date"], lang))
    if claim["status"] in CLEAN:
        return W["whyClean"].format(n=len(d.get("clear_dates") or []))
    return W["whyReview"]


def why_line(claim: dict, lang: str) -> str:
    return both(lang, lambda l: _why(claim, l))


def _buttons(lang: str) -> list[tuple[str, str]]:
    def title(k):
        en, own = SHORT["en"][k], _w(lang)[k]
        two = f"{en} · {own}"
        return en if lang == "en" else two if len(two) <= 20 else own
    return [("btn:why", title("bWhy")), ("btn:money", title("bMoney")), ("btn:appeal", title("bAppeal"))]


def _match_farmer(store: Store, text: str) -> dict | None:
    """A farmer named in a message or voice note: their English, Hindi or Gurmukhi first name, if only one fits."""
    t = (text or "").lower()
    hits = []
    for f in _farmers(store):
        en = (f.get("farmer") or "").split()
        hi = (f.get("farmer_hi") or "").split()
        names = {n.lower() for n in en[:1]} | set(hi[:1]) | {to_gurmukhi(n) for n in hi[:1]}
        if en[:2] == ["Om", "Prakash"] or hi[:2] == ["ओम", "प्रकाश"]:
            names |= {"om prakash", "ओम प्रकाश", "omprakash"}
        if any(n and re.search(r"(?<![\w\u0900-\u0a7f])" + re.escape(n) + r"(?![\w\u0900-\u0a7f])", t) for n in names):
            hits.append(f)
    return hits[0] if len(hits) == 1 else None


def _pick_farmer(store: Store, phone: str, client, lang: str) -> None:
    W = _w("en")
    client.send_buttons(phone, W["intro"] + "\n\n" + W["state"], [("state:PB", "Punjab · ਪੰਜਾਬ"), ("state:HR", "Haryana · हरियाणा")])


def _list_farmers(store: Store, phone: str, client, state: str) -> None:
    W = _w("en")
    rows = [(f"f:{f['id']}", f.get("farmer", ""), f"{_name(f)} · {f.get('name', '')} · {f.get('village', '')}")
            for f in _farmers(store) if f.get("state") == state]
    client.send_list(phone, W["pick"], W["list"], rows)


HEARD = {"hi": "आपने कहा", "pa": "ਤੁਸੀਂ ਕਿਹਾ", "en": "You said", "hr": "थमनै कह्या"}
NOT_HEARD = {"hi": "आवाज़ साफ़ नहीं आई। कृपया दोबारा बोलें या लिखकर भेजें।",
             "pa": "ਆਵਾਜ਼ ਸਾਫ਼ ਨਹੀਂ ਆਈ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਬੋਲੋ ਜਾਂ ਲਿਖ ਕੇ ਭੇਜੋ।",
             "en": "I could not hear that clearly. Please say it again or type it.",
             "hr": "आवाज साफ कोनी आई। फेर बोलो या लिख कै भेजो।"}


def _voice(voice, text: str, lang: str, client, phone: str, fallback: str = "") -> None:
    from parali.tts import speak
    mp3 = speak(voice, EMOJI.sub("", text), lang) or (speak(voice, EMOJI.sub("", fallback), "hi") if fallback and lang != "hi" else None)
    if mp3:
        client.send_audio(phone, mp3)


def handle(store: Store, msg: dict, client, dispatch, backend=None, voice=None, transcribe=None, rp=None) -> str:
    """Answer one incoming message. Returns what was done, for the log."""
    if store.get("wa_seen", msg["id"]):
        return "duplicate"
    store.put("wa_seen", msg["id"], {"id": msg["id"], "at": now_iso()})
    try:
        client.mark_read(msg["id"])
    except (urllib.error.URLError, KeyError):
        pass
    phone, text, code = msg["from"], (msg.get("text") or "").strip(), ""
    link = store.get("wa_links", phone)
    farmer = store.get("fields", link["farmer_id"]) if link else None
    lang = lang_of(text, farmer)

    if msg.get("type") == "audio":
        heard = None
        if transcribe:
            audio, mime = client.download(msg["media_id"])
            heard = transcribe(audio, mime)
        if not heard or not heard[0] or not re.search(r"[\u0900-\u097f\u0a00-\u0a7fA-Za-z]", heard[0]):
            client.send_text(phone, NOT_HEARD[lang])
            return "voice not understood"
        text, code = heard
        lang = lang_of(text, farmer, code or "hi")
    elif msg.get("type") not in ("text", "interactive"):
        client.send_text(phone, NOT_HEARD[lang])
        return f"unsupported {msg.get('type')}"

    # a tap carries an English id, so it is answered in the language the farmer last wrote or spoke
    tap = msg.get("type") == "interactive" or TAP.match(text)
    if tap:
        lang = (link or {}).get("lang") or ("pa" if (farmer or {}).get("state") == "PB" else "hr" if farmer else "en")

    # ---- choosing a farmer: tap a state and a name, or just say the name ----
    if text.startswith("state:"):
        _list_farmers(store, phone, client, text[6:])
        return "farmer list"
    if CHANGE.match(text) and link:
        link = {k: v for k, v in link.items() if k != "lang"}
        store.put("wa_links", phone, link)
    picked = store.get("fields", text[2:]) if text.startswith("f:") else None
    if not picked and not farmer and not tap and not CHANGE.match(text):
        picked = _match_farmer(store, text)
    if picked:
        # a tap: the farmer's own language (English is above it anyway); a spoken or typed name: the language used
        lang = ("pa" if picked.get("state") == "PB" else "hr") if tap else lang_of(text, picked, code)
        farmer, link = picked, {"id": phone, "farmer_id": picked["id"], "at": now_iso(), "lang": lang}
        store.put("wa_links", phone, link)
        claim = _claim_of(store, farmer["id"])
        if claim:
            client.send_buttons(phone, short_status(claim, lang), _buttons(lang))
            f = farmer_text_for(claim)
            _voice(voice, f.get(lang) or "", lang, client, phone, f.get("hi", ""))
            _send_pictures(store, farmer["id"], phone, client, lang)
            return "linked"
        text = "status"
    elif not farmer or CHANGE.match(text):
        _pick_farmer(store, phone, client, lang)
        return "menu"
    elif not tap and link.get("lang") != lang:
        link = {**link, "lang": lang}
        store.put("wa_links", phone, link)

    claim = _claim_of(store, farmer["id"])
    # ---- an appeal in progress: this message is the farmer's reason ----
    if link and link.get("awaiting") == "appeal" and not text.startswith("btn:"):
        link.pop("awaiting", None)
        store.put("wa_links", phone, link)
        if claim and claim["status"] in APPEALABLE:
            from parali import payments, service
            claim = service.appeal(store, claim["id"], text, voice)
            claim = payments.cancel(store, claim, rp() if callable(rp) else rp)
            store.add_event(claim["id"], {"type": "appeal_whatsapp", "by": "farmer"})
            client.send_text(phone, short_status(claim, lang))
            _voice(voice, (claim.get("message") or {}).get(lang) or "", lang, client, phone, (claim.get("message") or {}).get("hi", ""))
            return "appeal"
    if text == "btn:appeal":
        if claim and claim["status"] in APPEALABLE:
            store.put("wa_links", phone, {**link, "awaiting": "appeal"})
            client.send_text(phone, both(lang, lambda l: _w(l)["askAppeal"]))
        else:
            client.send_text(phone, both(lang, lambda l: _w(l)["noAppeal"]))
        return "appeal prompt"
    if text == "btn:money" and claim:
        client.send_buttons(phone, money_line(claim, lang), _buttons(lang))
        from parali.messages import advance_text, farmer_text
        a, f = advance_text(claim), farmer_text(claim)
        _voice(voice, (a.get(lang) or "") + " " + (f.get(lang) or ""), lang, client, phone, a.get("hi", "") + " " + f.get("hi", ""))
        return "money"
    if text == "btn:why" and claim:
        client.send_text(phone, why_line(claim, lang))
        _send_pictures(store, farmer["id"], phone, client, lang)
        f = farmer_text_for(claim)
        _voice(voice, f.get(lang) or "", lang, client, phone, f.get("hi", ""))
        return "why"

    # ---- anything else goes to the assistant ----
    r = agent.respond(store, farmer["id"], text, dispatch, backend=backend)
    reply = {"hi": r.hi, "en": r.en, "pa": r.pa, "hr": r.hr}[lang]
    if lang == "pa" and not reply and voice is not None and hasattr(voice, "translate_pa"):
        reply = voice.translate_pa(r.hi)
    if not reply:
        lang, reply = "hi", r.hi
    said = f"{HEARD[lang]}: “{text}”\n" if msg.get("type") == "audio" else ""
    claim = _claim_of(store, farmer["id"])
    if claim and set(r.tools) & {"claim_status", "explain"}:
        client.send_buttons(phone, said + short_status(claim, lang), _buttons(lang))  # short text; the voice note explains
    else:
        client.send_text(phone, said + reply)
    _voice(voice, reply, lang, client, phone, r.hi)
    if picked or "explain" in r.tools:
        _send_pictures(store, farmer["id"], phone, client, lang)
    return f"{r.mode}:{','.join(r.tools)}"


def farmer_text_for(claim: dict) -> dict:
    from parali.messages import farmer_text
    return claim.get("message") or farmer_text(claim)


PICTURE = {"hi": "आपके खेत की उपग्रह तस्वीरें, कटाई से बुआई तक।", "pa": "ਤੁਹਾਡੇ ਖੇਤ ਦੀਆਂ ਸੈਟੇਲਾਈਟ ਤਸਵੀਰਾਂ, ਵਾਢੀ ਤੋਂ ਬਿਜਾਈ ਤੱਕ।",
           "en": "Satellite pictures of your field, from harvest to sowing.", "hr": "थारे खेत के उपग्रह फोटू, कटाई तै बिजाई तक।"}


def _send_pictures(store: Store, farmer_id: str, phone: str, client, lang: str) -> None:
    """The same season pictures the officer sees, so the farmer can check the reading for themselves."""
    for c in store.list("claims"):
        if c["field_id"] == farmer_id and c.get("evidence_key"):
            png = store.get_blob(c["evidence_key"])
            if png:
                client.send_image(phone, png, PICTURE[lang])
            return


def notify(store: Store, claim: dict, client, voice=None) -> int:
    """Tell linked phones that a claim was decided. WhatsApp allows free-form messages only within 24 hours of
    the farmer's last message; outside that window the send fails and the farmer sees it in the app instead."""
    sent = 0
    for link in store.list("wa_links"):
        if link["farmer_id"] != claim["field_id"]:
            continue
        msg = claim.get("message") or {}
        lang = "pa" if claim.get("state_code") == "PB" else "hr"  # the farmer's own language, Hindi if it is missing
        own = msg.get(lang)
        try:
            client.send_buttons(link["id"], short_status(claim, lang if own else "hi"), _buttons(lang if own else "hi"))
            key = (claim.get(f"audio_key_{lang}") or claim.get("audio_key")) if own else claim.get("audio_key")
            mp3 = store.get_blob(key) if key else None
            if mp3:
                client.send_audio(link["id"], mp3)
            sent += 1
        except urllib.error.HTTPError as e:
            print(f"whatsapp notify {link['id'][-4:]}: HTTP {e.code}")
    return sent
