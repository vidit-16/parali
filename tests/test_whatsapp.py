import hashlib
import hmac
import json

import pytest
from shapely.geometry import mapping

from parali import service, whatsapp
from parali.store import LocalStore
from parali.tts import Voice
from tests.test_season import stacks_by_year
from tests.test_service import FIELD_GEOM, TH


class FakeClient:
    def __init__(self):
        self.sent = []

    def mark_read(self, mid):
        pass

    def send_text(self, to, text):
        self.sent.append(("text", to, text))

    def send_audio(self, to, mp3):
        self.sent.append(("audio", to, mp3))

    def send_image(self, to, png, caption=""):
        self.sent.append(("image", to, caption))

    def send_buttons(self, to, body, buttons):
        self.sent.append(("buttons", to, body))
        self.buttons = buttons

    def send_list(self, to, body, button, rows):
        self.sent.append(("list", to, body))
        self.rows = rows

    def download(self, media_id):
        return b"ogg", "audio/ogg; codecs=opus"

    def texts(self):
        return [t for kind, _, t in self.sent if kind in ("text", "buttons", "list")]


class FakeVoice(Voice):
    def __call__(self, text, language="hi-IN"):
        return b"en-mp3" if language == "en-IN" else b"hi-mp3"


@pytest.fixture
def store(tmp_path):
    s = LocalStore(tmp_path)
    s.put("fields", "f-pb", {"id": "f-pb", "name": "Killa 12/4", "name_hi": "किल्ला 12/4", "farmer": "Gurpreet Singh",
                             "farmer_hi": "गुरप्रीत सिंह", "state": "PB", "acres": 2.5, "geometry": mapping(FIELD_GEOM)})
    s.put("fields", "f-hr", {"id": "f-hr", "name": "Killa 44/2", "name_hi": "किल्ला 44/2", "farmer": "Suresh Kumar",
                             "farmer_hi": "सुरेश कुमार", "state": "HR", "acres": 2.5, "geometry": mapping(FIELD_GEOM)})
    return s


def msg(text=None, mid="m1", audio=False, tap=False):
    m = {"id": mid, "from": "919800000001", "type": "audio" if audio else "interactive" if tap else "text"}
    if audio:
        m.update(media_id="media1", mime="audio/ogg")
    else:
        m["text"] = text
    return m


def run(store, m, client, transcribe=None):
    voice = FakeVoice(speak_pa=lambda pa: b"pa-mp3", translate_pa=lambda hi: None)
    return whatsapp.handle(store, m, client, lambda cid: None, voice=voice, transcribe=transcribe)


def test_webhook_checks_meta_signature_and_verify_token():
    body = b'{"entry": []}'
    sig = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert whatsapp.signature_ok(body, sig, "secret")
    assert not whatsapp.signature_ok(body + b" ", sig, "secret") and not whatsapp.signature_ok(body, sig, "")
    q = {"hub.mode": "subscribe", "hub.verify_token": "tok", "hub.challenge": "42"}
    assert whatsapp.verify(q, {"verify_token": "tok"}) == (200, "42")
    assert whatsapp.verify({**q, "hub.verify_token": "x"}, {"verify_token": "tok"})[0] == 403


def test_parses_text_and_voice_notes():
    payload = {"entry": [{"changes": [{"value": {"messages": [
        {"id": "a", "from": "91", "type": "text", "text": {"body": "hi"}},
        {"id": "b", "from": "91", "type": "audio", "audio": {"id": "m9", "mime_type": "audio/ogg; codecs=opus"}}]}}]}]}
    a, b = whatsapp.messages(payload)
    assert a["text"] == "hi" and b["media_id"] == "m9" and b["mime"].startswith("audio/ogg")


def test_new_number_picks_a_state_then_a_farmer(store):
    c = FakeClient()
    assert run(store, msg("hello"), c) == "menu"
    assert [i for i, _ in c.buttons] == ["state:PB", "state:HR"]
    c = FakeClient()
    assert run(store, msg("state:PB", mid="m2", tap=True), c) == "farmer list"
    assert c.rows == [("f:f-pb", "Gurpreet Singh", "ਗੁਰਪ੍ਰੀਤ ਸਿੰਘ · Killa 12/4 · ")]  # English, then their own script
    service.create_claim(store, "f-pb", "2025-10-01", "2025-11-30")
    c = FakeClient()
    assert run(store, msg("f:f-pb", mid="m3", tap=True), c) == "linked"
    assert store.get("wa_links", "919800000001")["farmer_id"] == "f-pb"
    assert c.sent[0][0] == "buttons" and len(c.texts()[0].splitlines()) <= 3  # short text with buttons


def test_a_farmer_is_picked_by_saying_the_name(store):
    c = FakeClient()
    run(store, msg(audio=True), c, transcribe=lambda audio, mime: ("मैं सुरेश बोल रहा हूँ", "hi-IN"))
    link = store.get("wa_links", "919800000001")
    assert link["farmer_id"] == "f-hr" and link["lang"] == "hr"
    assert whatsapp._match_farmer(store, "ਗੁਰਪ੍ਰੀਤ") ["id"] == "f-pb" and whatsapp._match_farmer(store, "hello") is None


def test_the_same_message_is_answered_once(store):
    c = FakeClient()
    run(store, msg("hello"), c)
    assert run(store, msg("hello"), c) == "duplicate" and len(c.sent) == 1


def test_buttons_answer_in_the_farmers_language_and_appeal_takes_the_next_message(store):
    store.put("wa_links", "919800000001", {"id": "919800000001", "farmer_id": "f-pb", "lang": "pa"})
    cl = service.create_claim(store, "f-pb", "2025-10-01", "2025-11-30")
    cl = {**store.get("claims", cl["id"]), "status": "possible_burn", "decision": {"burn_date": "2025-11-06"},
          "settlement": {"state": "pending", "total": 2500}}
    store.put("claims", cl["id"], cl)
    c = FakeClient()
    assert run(store, msg("btn:why", tap=True), c) == "why"
    assert "6 ਨਵੰਬਰ" in c.texts()[0]
    c = FakeClient()
    assert run(store, msg("btn:money", mid="m2", tap=True), c) == "money" and "ਅਗਾਊਂ" in c.texts()[0]
    c = FakeClient()
    run(store, msg("btn:appeal", mid="m3", tap=True), c)
    assert c.texts() == [whatsapp.SHORT["pa"]["askAppeal"]]
    c = FakeClient()
    assert run(store, msg("ਮੈਂ ਪਰਾਲੀ ਨਹੀਂ ਸਾੜੀ, ਹੈਪੀ ਸੀਡਰ ਵਰਤਿਆ", mid="m4"), c) == "appeal"
    assert store.get("claims", cl["id"])["appeal"]["note"].startswith("ਮੈਂ") and "awaiting" not in store.get("wa_links", "919800000001")


def test_voice_note_in_punjabi_is_answered_in_punjabi(store):
    store.put("wa_links", "919800000001", {"id": "919800000001", "farmer_id": "f-hr"})
    c = FakeClient()
    run(store, msg(audio=True), c, transcribe=lambda audio, mime: ("ਮੇਰੇ ਖੇਤ ਕਿਹੜੇ ਹਨ", "pa-IN"))
    text = c.texts()[0]
    assert "ਤੁਸੀਂ ਕਿਹਾ" in text and "ਤੁਹਾਡੇ ਨਾਮ ਉੱਤੇ ਇਹ ਖੇਤ" in text
    c = FakeClient()
    run(store, msg(audio=True, mid="m3"), c, transcribe=lambda audio, mime: None)
    assert c.texts() == [whatsapp.NOT_HEARD["hr"]]  # a Haryana farmer: Haryanvi


def test_hindi_text_gets_hindi_text_and_polly_audio(store):
    store.put("wa_links", "919800000001", {"id": "919800000001", "farmer_id": "f-pb"})
    c = FakeClient()
    run(store, msg("मेरे खेत कौन से हैं"), c)
    assert c.texts()[0].startswith("आपके नाम पर") and ("audio", "919800000001", b"hi-mp3") in c.sent


def test_decision_reaches_linked_phones(store):
    store.put("wa_links", "919800000001", {"id": "919800000001", "farmer_id": "f-pb"})
    cl = service.create_claim(store, "f-pb", "2025-10-01", "2025-11-30")
    cl = service.run_season(store, cl["id"], stacks_by_year(None, None), [], TH, FakeVoice(speak_pa=lambda pa: b"pa-mp3"))
    c = FakeClient()
    assert whatsapp.notify(store, cl, c) == 1
    assert c.texts() == [whatsapp.short_status(cl, "pa")] and ("audio", "919800000001", b"pa-mp3") in c.sent
    assert whatsapp.notify(store, {**cl, "field_id": "f-hr"}, FakeClient()) == 0


def test_webhook_payload_round_trip():
    body = json.dumps({"entry": [{"changes": [{"value": {"statuses": [{"id": "x"}]}}]}]})
    assert whatsapp.messages(json.loads(body)) == []  # delivery receipts are not messages


def test_english_gets_english_and_haryana_gets_haryanvi(store):  # noqa: F811
    store.put("wa_links", "919800000001", {"id": "919800000001", "farmer_id": "f-hr"})
    c = FakeClient()
    run(store, msg("which fields are mine"), c)
    assert c.texts()[0].startswith("Your registered fields") and ("audio", "919800000001", b"en-mp3") in c.sent
    c = FakeClient()
    run(store, msg("मेरे खेत कौन से हैं", mid="m2"), c)
    assert c.texts()[0].startswith("थारे नाम पै")
    c = FakeClient()
    run(store, msg("mera khet kaun sa hai", mid="m3"), c)
    assert c.texts()[0].startswith("थारे नाम पै")  # Hinglish from Haryana: Haryanvi


def test_every_message_has_haryanvi():
    from parali.messages import farmer_text
    t = farmer_text({"status": "possible_burn", "farmer_name_hi": "सुरेश", "field_name_hi": "किल्ला 44/2",
                     "decision": {"burn_date": "2025-11-06"}, "settlement": {"state": "pending"}})
    assert t["hr"].startswith("राम राम सुरेश जी") and "6 नवंबर" in t["hr"]