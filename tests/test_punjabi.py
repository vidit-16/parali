import json

from parali import api, sarvam, service
from parali.messages import farmer_text, to_gurmukhi
from parali.tts import Voice
from tests.test_season import stacks_by_year, store  # noqa: F401  (fixture)
from tests.test_service import TH


class FakeVoice(Voice):  # Polly and Sarvam replaced
    def __call__(self, text, language="hi-IN"):
        return b"en-mp3" if language == "en-IN" else b"hi-mp3"


def voice(speak=lambda pa: b"pa-mp3", translate=lambda hi: None):
    return FakeVoice(speak_pa=speak, translate_pa=translate)


def test_names_move_from_devanagari_to_gurmukhi():
    assert to_gurmukhi("गुरप्रीत सिंह") == "ਗੁਰਪ੍ਰੀਤ ਸਿੰਘ"
    assert to_gurmukhi("किल्ला 12/4") == "ਕਿੱਲਾ 12/4"
    assert to_gurmukhi("हरजिंदर") == "ਹਰਜਿੰਦਰ"


def test_every_message_has_punjabi_with_the_same_numbers():
    claim = {"status": "possible_burn", "farmer_name_hi": "गुरप्रीत", "field_name": "Killa 12/4",
             "field_name_hi": "किल्ला 12/4", "decision": {"burn_date": "2025-11-06"},
             "advance": {"status": "paid", "amount": 1250, "eligible": True},
             "settlement": {"state": "recover_advance", "recover": 1250}}
    for status in ("submitted", "auto_approved", "needs_review", "possible_burn", "officer_approved",
                   "officer_confirmed_burnt"):
        t = farmer_text({**claim, "status": status})
        assert t["pa"] and sarvam.numbers(t["pa"]) == sarvam.numbers(t["hi"]), status


def test_translation_is_refused_when_money_or_script_changes(monkeypatch):
    monkeypatch.setattr(sarvam, "api_key", lambda: "k")
    hi = "पहले दी गई ₹1,250 की अग्रिम राशि वापस करनी होगी।"
    for bad in ("£1250 ਦੀ ਪਹਿਲੀ ਅਦਾਇਗੀ ਵਾਪਸ ਕੀਤੀ ਜਾਵੇਗੀ।", "ਪਹਿਲਾਂ ₹1,520 ਵਾਪਸ ਕਰਨੇ ਪੈਣਗੇ।", "ਪਹਿਲੇ advance ₹1,250 refund ਕਰੋ।"):
        monkeypatch.setattr(sarvam, "_post", lambda *a, bad=bad: {"translated_text": bad})
        assert sarvam.translate_pa(hi) is None, bad
    monkeypatch.setattr(sarvam, "_post", lambda *a: {"translated_text": "ਪਹਿਲਾਂ ਦਿੱਤੀ ₹1,250 ਦੀ ਅਗਾਊਂ ਰਕਮ ਵਾਪਸ ਕਰਨੀ ਪਵੇਗੀ।"})
    assert sarvam.translate_pa(hi)


def test_punjab_claims_get_punjabi_audio(store):  # noqa: F811
    said = []
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    c = service.run_season(store, c["id"], stacks_by_year(None, None), [], TH, voice(lambda pa: said.append(pa) or b"pa-mp3"))
    assert c["state_code"] == "PB" and said == [c["message"]["pa"]]
    assert store.get_blob(c["audio_key_pa"]) == b"pa-mp3" and store.get_blob(c["audio_key"]) == b"hi-mp3"


def test_without_sarvam_the_farmer_still_gets_hindi_audio(store):  # noqa: F811
    c = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    c = service.run_season(store, c["id"], stacks_by_year(None, None), [], TH, voice(lambda pa: None))
    assert c["message"]["pa"] and "audio_key_pa" not in c and c["audio_key"]


def test_agent_answers_in_punjabi_from_its_templates(store):  # noqa: F811
    translated = []
    deps = api.Deps(store=store, dispatch=lambda cid: None, speaker=voice(translate=lambda hi: translated.append(hi)))
    body = json.dumps({"farmer_id": "f1", "text": "ਮੇਰੇ ਖੇਤ ਕਿਹੜੇ ਹਨ", "lang": "pa"}).encode()
    status, _, out = api.handle("POST", "/api/agent", body, {}, deps)
    out = json.loads(out)
    assert status == 200 and out["tools"] == ["my_fields"] and out["pa"].startswith("ਤੁਹਾਡੇ ਨਾਮ")
    assert translated == []  # template text, nothing machine-translated
    out = json.loads(api.handle("POST", "/api/agent", json.dumps({"farmer_id": "f1", "text": "my fields"}).encode(), {}, deps)[2])
    assert "pa" not in out and out["audio_url"]
