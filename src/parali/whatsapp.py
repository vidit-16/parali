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


# ---------- conversation ----------

def lang_of(text: str) -> str:
    return "pa" if re.search(r"[਀-੿]", text or "") else "hi"


def _farmers(store: Store) -> list[dict]:
    return sorted((f for f in store.list("fields") if f.get("farmer")), key=lambda f: (f.get("state") != "PB", f["id"]))


def _name(f: dict) -> str:
    """A farmer's name in their own script: Gurmukhi in Punjab, Devanagari in Haryana."""
    hi = f.get("farmer_hi") or f.get("farmer", "")
    return to_gurmukhi(hi) if f.get("state") == "PB" else hi


def menu(store: Store) -> str:
    rows = [f"{i}. {_name(f)} · {f.get('name', '')} · {f.get('village', '')}" for i, f in enumerate(_farmers(store), 1)]
    return ("Saakshi (demo). Reply with a number to be that farmer:\n"
            "साक्षी (डेमो)। जिस किसान के रूप में बात करनी है, उसका नंबर भेजें:\n\n" + "\n".join(rows)
            + "\n\nSend \"change\" any time to pick again.")


HEARD = {"hi": "आपने कहा", "pa": "ਤੁਸੀਂ ਕਿਹਾ"}
NOT_HEARD = {"hi": "आवाज़ साफ़ नहीं आई। कृपया दोबारा बोलें या लिखकर भेजें।",
             "pa": "ਆਵਾਜ਼ ਸਾਫ਼ ਨਹੀਂ ਆਈ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਬੋਲੋ ਜਾਂ ਲਿਖ ਕੇ ਭੇਜੋ।"}


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
    lang = lang_of(text) if text else ("pa" if farmer and farmer.get("state") == "PB" else "hi")

    if msg.get("type") == "audio":
        heard = None
        if transcribe:
            audio, mime = client.download(msg["media_id"])
            heard = transcribe(audio, mime)
        if not heard or not heard[0]:
            client.send_text(phone, NOT_HEARD[lang])
            return "voice not understood"
        text, code = heard
        lang = "pa" if code.startswith("pa") else "hi"
    elif msg.get("type") not in ("text", "interactive"):
        client.send_text(phone, NOT_HEARD[lang])
        return f"unsupported {msg.get('type')}"

    just_linked = False
    if not farmer or CHANGE.match(text):
        farmers = _farmers(store)
        if not CHANGE.match(text) and text.isdigit() and 1 <= int(text) <= len(farmers):
            farmer = farmers[int(text) - 1]
            store.put("wa_links", phone, {"id": phone, "farmer_id": farmer["id"], "at": now_iso()})
            text, lang, just_linked = "status", "pa" if farmer.get("state") == "PB" else "hi", True
        else:
            client.send_text(phone, menu(store))
            return "menu"

    r = agent.respond(store, farmer["id"], text, dispatch, backend=backend)
    reply = r.pa if lang == "pa" and r.pa else None
    if lang == "pa" and not reply and voice is not None and hasattr(voice, "translate_pa"):
        reply = voice.translate_pa(r.hi)
    if not reply:
        lang, reply = "hi", r.hi
    said = f"🎙 {HEARD[lang]}: “{text}”\n\n" if msg.get("type") == "audio" else ""
    client.send_text(phone, said + reply)
    if voice is not None:
        mp3 = voice.speak_pa(reply) if lang == "pa" else voice(reply)
        if mp3:
            client.send_audio(phone, mp3)
    if just_linked or "explain" in r.tools:
        _send_pictures(store, farmer["id"], phone, client, lang)
    return f"{r.mode}:{','.join(r.tools)}"


PICTURE = {"hi": "आपके खेत की उपग्रह तस्वीरें, कटाई से बुआई तक।", "pa": "ਤੁਹਾਡੇ ਖੇਤ ਦੀਆਂ ਸੈਟੇਲਾਈਟ ਤਸਵੀਰਾਂ, ਵਾਢੀ ਤੋਂ ਬਿਜਾਈ ਤੱਕ।"}


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
        pa = claim.get("state_code") == "PB" and msg.get("pa")
        try:
            client.send_text(link["id"], pa or msg.get("hi", ""))
            key = claim.get("audio_key_pa") if pa else claim.get("audio_key")
            mp3 = store.get_blob(key) if key else None
            if mp3:
                client.send_audio(link["id"], mp3)
            sent += 1
        except urllib.error.HTTPError as e:
            print(f"whatsapp notify {link['id'][-4:]}: HTTP {e.code}")
    return sent
