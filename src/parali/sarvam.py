"""Punjabi speech through Sarvam AI.

Every message and reply has fixed Punjabi text (messages.py, agent.compose); Sarvam reads it aloud. The one
thing without a template is the model's own short question when a request is unclear; that is translated
from Hindi, and the translation is used only if its numbers and currency signs match and it is all
Gurmukhi. In testing, translation turned ₹ into £ and the village officer into a clerk, which is why
nothing about money goes through it.
"""
import base64
import json
import os
import re
import urllib.error
import urllib.request
from functools import lru_cache

API = "https://api.sarvam.ai"
TRANSLATE_MODEL = "sarvam-translate:v1"
TTS_MODEL = "bulbul:v3"
TIMEOUT_S = 12
ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, KeyError, ValueError, IndexError)


@lru_cache(maxsize=1)
def api_key() -> str | None:
    """SARVAM_API_KEY locally; on Lambda the key stays in SSM and only its name is in the environment."""
    if os.environ.get("SARVAM_API_KEY"):
        return os.environ["SARVAM_API_KEY"]
    name = os.environ.get("SARVAM_PARAM")
    if not name:
        return None
    import boto3
    try:
        return boto3.client("ssm").get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:  # no key means no Punjabi voice, not a broken request
        print(f"sarvam key unavailable: {type(e).__name__}")
        return None


def _post(path: str, body: dict, key: str) -> dict:
    req = urllib.request.Request(API + path, json.dumps(body).encode(),
                                 {"api-subscription-key": key, "Content-Type": "application/json"})
    for attempt in (1, 2):  # one retry: the TLS handshake is sometimes reset
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, ConnectionError):
            if attempt == 2:
                raise


def numbers(text: str) -> list[str]:
    return sorted(m.replace(",", "") for m in re.findall(r"\d[\d,]*", text))


def _faithful(src: str, out: str) -> bool:
    signs = lambda t: sorted(re.findall(r"[₹$£€]", t))  # noqa: E731
    return bool(out) and numbers(out) == numbers(src) and signs(out) == signs(src) and not re.search(r"[A-Za-z]", out)


def translate_pa(text_hi: str) -> str | None:
    key = api_key()
    if not key or not text_hi:
        return None
    try:
        out = _post("/translate", {"input": text_hi, "source_language_code": "hi-IN", "target_language_code": "pa-IN",
                                   "model": TRANSLATE_MODEL, "numerals_format": "international"}, key)
    except ERRORS as e:
        print(f"sarvam translate failed: {type(e).__name__}")
        return None
    text = (out.get("translated_text") or "").strip()
    return text if _faithful(text_hi, text) else None


def transcribe(audio: bytes, mime: str = "audio/ogg") -> tuple[str, str] | None:
    """(transcript, language code such as "pa-IN") for a voice note in any Indian language, or None."""
    key = api_key()
    if not key or not audio:
        return None
    import uuid
    b = uuid.uuid4().hex
    fields = [("model", "saarika:v2.5"), ("language_code", "unknown")]
    body = b"".join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields)
    body += (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="voice.{mime.split("/")[-1].split(";")[0]}"\r\n'
             f"Content-Type: {mime.split(';')[0]}\r\n\r\n").encode() + audio + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(API + "/speech-to-text", body,
                                 {"api-subscription-key": key, "Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            out = json.loads(r.read())
        return (out.get("transcript") or "").strip(), out.get("language_code") or ""
    except ERRORS + (urllib.error.HTTPError,) as e:
        print(f"sarvam transcribe failed: {type(e).__name__}")
        return None


def speak_pa(text_pa: str) -> bytes | None:
    key = api_key()
    if not key or not text_pa:
        return None
    try:
        out = _post("/text-to-speech", {"text": text_pa, "target_language_code": "pa-IN", "model": TTS_MODEL,
                                        "output_audio_codec": "mp3"}, key)
        return base64.b64decode(out["audios"][0])
    except ERRORS as e:
        print(f"sarvam speech failed: {type(e).__name__}")
        return None
