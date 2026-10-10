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

from parali import agent
from parali.messages import to_gurmukhi
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


def menu(store: Store) -> str:
    # English first, then the name in the farmer's own script
    rows = [f"{i}. {f.get('farmer', '')} ({_name(f)}) · {f.get('name', '')} · {f.get('village', '')}" for i, f in enumerate(_farmers(store), 1)]
    return ("Saakshi (demo). Reply with a number to chat as that farmer. Write or speak in English, Hindi, Punjabi "
            "or Haryanvi; Saakshi answers in the same language.\n\n" + "\n".join(rows)
            + "\n\nSend \"change\" any time to pick again.")


HEARD = {"hi": "आपने कहा", "pa": "ਤੁਸੀਂ ਕਿਹਾ", "en": "You said", "hr": "थमनै कह्या"}
NOT_HEARD = {"hi": "आवाज़ साफ़ नहीं आई। कृपया दोबारा बोलें या लिखकर भेजें।",
             "pa": "ਆਵਾਜ਼ ਸਾਫ਼ ਨਹੀਂ ਆਈ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਬੋਲੋ ਜਾਂ ਲਿਖ ਕੇ ਭੇਜੋ।",
             "en": "I could not hear that clearly. Please say it again or type it.",
             "hr": "आवाज साफ कोनी आई। फेर बोलो या लिख कै भेजो।"}


def handle(store: Store, msg: dict, client, dispatch, backend=None, voice=None, transcribe=None) -> str:
    """Answer one incoming message. Returns what was done, for the log."""
    if store.get("wa_seen", msg["id"]):
        return "duplicate"
    store.put("wa_seen", msg["id"], {"id": msg["id"], "at": now_iso()})
    try:
        client.mark_read(msg["id"])
    except (urllib.error.URLError, KeyError):
        pass
    phone, text = msg["from"], (msg.get("text") or "").strip()
    link = store.get("wa_links", phone)
    farmer = store.get("fields", link["farmer_id"]) if link else None
    lang = lang_of(text, farmer)

    if msg.get("type") == "audio":
        heard = None
        if transcribe:
            audio, mime = client.download(msg["media_id"])
            heard = transcribe(audio, mime)
        if not heard or not heard[0]:
            client.send_text(phone, NOT_HEARD[lang])
            return "voice not understood"
        text, code = heard
        lang = lang_of(text, farmer, code or "hi")
    elif msg.get("type") not in ("text", "interactive"):
        client.send_text(phone, NOT_HEARD[lang])
        return f"unsupported {msg.get('type')}"

    just_linked = False
    if not farmer or CHANGE.match(text):
        farmers = _farmers(store)
        if not CHANGE.match(text) and text.isdigit() and 1 <= int(text) <= len(farmers):
            farmer = farmers[int(text) - 1]
            store.put("wa_links", phone, {"id": phone, "farmer_id": farmer["id"], "at": now_iso()})
            text, lang, just_linked = "status", "pa" if farmer.get("state") == "PB" else "hr", True
        else:
            client.send_text(phone, menu(store))
            return "menu"

    from parali.tts import speak
    r = agent.respond(store, farmer["id"], text, dispatch, backend=backend)
    reply = {"hi": r.hi, "en": r.en, "pa": r.pa, "hr": r.hr}[lang]
    if lang == "pa" and not reply and voice is not None and hasattr(voice, "translate_pa"):
        reply = voice.translate_pa(r.hi)
    if not reply:
        lang, reply = "hi", r.hi
    said = f"🎙 {HEARD[lang]}: “{text}”\n\n" if msg.get("type") == "audio" else ""
    client.send_text(phone, said + reply)
    mp3 = speak(voice, reply, lang) or (speak(voice, r.hi, "hi") if lang != "hi" else None)
    if mp3:
        client.send_audio(phone, mp3)
    if just_linked or "explain" in r.tools:
        _send_pictures(store, farmer["id"], phone, client, lang)
    return f"{r.mode}:{','.join(r.tools)}"


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
        rec = claim.get("recovery") or {}
        pay = f"\n\n₹{rec['amount']}: {rec['url']}" if rec.get("status") == "issued" and rec.get("url") else ""
        try:
            client.send_text(link["id"], (own or msg.get("hi", "")) + pay)
            key = (claim.get(f"audio_key_{lang}") or claim.get("audio_key")) if own else claim.get("audio_key")
            mp3 = store.get_blob(key) if key else None
            if mp3:
                client.send_audio(link["id"], mp3)
            sent += 1
        except urllib.error.HTTPError as e:
            print(f"whatsapp notify {link['id'][-4:]}: HTTP {e.code}")
    return sent
