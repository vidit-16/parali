"""What the farmer hears and reads. Fixed text per outcome, filled from the decision. No model writes these.

Hindi, English and Punjabi are all written here; a voice service only reads them aloud."""
import re
import unicodedata
from datetime import date

HI_MONTHS = ("जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर")
PA_MONTHS = ("ਜਨਵਰੀ", "ਫ਼ਰਵਰੀ", "ਮਾਰਚ", "ਅਪ੍ਰੈਲ", "ਮਈ", "ਜੂਨ", "ਜੁਲਾਈ", "ਅਗਸਤ", "ਸਤੰਬਰ", "ਅਕਤੂਬਰ", "ਨਵੰਬਰ", "ਦਸੰਬਰ")

REASON_HI = {
    "too_few_clear_images": "बादलों के कारण आपके खेत की पर्याप्त साफ़ तस्वीरें नहीं मिलीं।",
    "dark_on_one_image": "एक तस्वीर में खेत का रंग गहरा दिखा, पर अगली तस्वीर में नहीं।",
    "partial_scar": "खेत के एक हिस्से का रंग गहरा दिखा।",
    "fire_point_nearby_no_scar": "पास में आग का उपग्रह संकेत मिला, पर आपके खेत पर जलने का निशान नहीं दिखा।",
    "field_too_small": "खेत छोटा होने के कारण तस्वीरों से पक्का फ़ैसला नहीं हो सका।",
}

REASON_EN = {
    "too_few_clear_images": "Not enough cloud-free images of the field.",
    "dark_on_one_image": "The field looked dark on one image but not on the next.",
    "partial_scar": "Part of the field looked dark.",
    "fire_point_nearby_no_scar": "A satellite fire point was detected nearby, but there is no burn scar on this field.",
    "field_too_small": "The field is too small for a confident reading at 20 m.",
}

REASON_PA = {
    "too_few_clear_images": "ਬੱਦਲਾਂ ਕਾਰਨ ਤੁਹਾਡੇ ਖੇਤ ਦੀਆਂ ਕਾਫ਼ੀ ਸਾਫ਼ ਤਸਵੀਰਾਂ ਨਹੀਂ ਮਿਲੀਆਂ।",
    "dark_on_one_image": "ਇੱਕ ਤਸਵੀਰ ਵਿੱਚ ਖੇਤ ਦਾ ਰੰਗ ਗੂੜ੍ਹਾ ਦਿਸਿਆ, ਪਰ ਅਗਲੀ ਤਸਵੀਰ ਵਿੱਚ ਨਹੀਂ।",
    "partial_scar": "ਖੇਤ ਦੇ ਇੱਕ ਹਿੱਸੇ ਦਾ ਰੰਗ ਗੂੜ੍ਹਾ ਦਿਸਿਆ।",
    "fire_point_nearby_no_scar": "ਨੇੜੇ ਅੱਗ ਦਾ ਸੈਟੇਲਾਈਟ ਸੰਕੇਤ ਮਿਲਿਆ, ਪਰ ਤੁਹਾਡੇ ਖੇਤ ਉੱਤੇ ਸਾੜਨ ਦਾ ਨਿਸ਼ਾਨ ਨਹੀਂ ਦਿਸਿਆ।",
    "field_too_small": "ਖੇਤ ਛੋਟਾ ਹੋਣ ਕਾਰਨ ਤਸਵੀਰਾਂ ਤੋਂ ਪੱਕਾ ਫ਼ੈਸਲਾ ਨਹੀਂ ਹੋ ਸਕਿਆ।",
}


def hi_date(d: date | str) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{d.day} {HI_MONTHS[d.month - 1]}"


def pa_date(d: date | str) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{d.day} {PA_MONTHS[d.month - 1]}"


def rupees(n: int) -> str:
    """Indian digit grouping: 123456 -> 1,23,456."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    return ",".join([head] + parts + [tail]) if head else ",".join(parts + [tail])


# Devanagari and Gurmukhi share a layout (Gurmukhi = Devanagari + 0x100), so names written in Hindi can be shown
# in Gurmukhi letter by letter. Letters Gurmukhi lacks get their usual Punjabi spelling, and a doubled consonant
# takes the addak (ल्ल -> ੱਲ).
_NO_GURMUKHI = {"ष": "ਸ਼", "ऋ": "ਰਿ", "ृ": "ਿ", "ॉ": "ੋ", "ऑ": "ਓ", "ॅ": "ੈ", "ऍ": "ਐ", "ः": "", "ऽ": ""}


def to_gurmukhi(text: str) -> str:
    out = []
    text = unicodedata.normalize("NFC", text or "").replace("ड़", "ੜ").replace("ढ़", "ੜ")
    for ch in text:
        if ch in _NO_GURMUKHI:
            out.append(_NO_GURMUKHI[ch])
        elif "ऀ" <= ch <= "ॿ" and ch not in "।॥":
            g = chr(ord(ch) + 0x100)
            out.append(g if unicodedata.name(g, "") else ch)
        else:
            out.append(ch)
    s = "".join(out)
    s = re.sub(r"([\u0a15-\u0a39])\u0a4d\1", "\u0a71\\1", s)
    # nasal mark: tippi after a bare consonant or a short vowel sign, bindi after long ones
    s = re.sub(r"([\u0a15-\u0a39\u0a3f\u0a41\u0a42])\u0a02", "\\1\u0a70", s)
    # Gurmukhi joins consonants only with a subscript ਰ, ਵ or ਹ, and not at the end of a word
    s = re.sub("\u0a4d(?![ਰਵਹ])", "", s)
    s = re.sub("\u0a4dਰ(?![\u0a3e-\u0a4c\u0a70\u0a71\u0a02\u0a15-\u0a39])", "ਰ", s)
    s = s.replace("ਿਯਾ", "ਿਆ")
    return re.sub(r"ਸਿੰਹ\b", "ਸਿੰਘ", s)


def _pa_name(claim: dict, key: str) -> str:
    return to_gurmukhi(claim.get(f"{key}_hi") or "") or claim.get(key, "")


def advance_text(claim: dict) -> dict:
    """Before harvest: is there an advance, and why."""
    adv = claim.get("advance") or {}
    y = adv.get("prev_season", "")
    if adv.get("eligible"):
        amt = rupees(adv.get("amount", 0))
        paid = adv.get("status") == "paid"
        return {
            "hi": f"{y} में आपके खेत में पराली जलाने का निशान नहीं मिला, इसलिए आपको ₹{amt} की अग्रिम राशि "
                  + ("मिल चुकी है।" if paid else "मिलेगी।") + " बाकी राशि कटाई के बाद उपग्रह जाँच से तय होगी।",
            "en": f"Your field was clean in {y}, so you " + ("received" if paid else "get")
                  + f" an advance of Rs {amt}. The rest is decided by the satellite check after harvest.",
            "pa": f"{y} ਵਿੱਚ ਤੁਹਾਡੇ ਖੇਤ ਵਿੱਚ ਪਰਾਲੀ ਸਾੜਨ ਦਾ ਨਿਸ਼ਾਨ ਨਹੀਂ ਮਿਲਿਆ, ਇਸ ਲਈ ਤੁਹਾਨੂੰ ₹{amt} ਦੀ ਅਗਾਊਂ ਰਕਮ "
                  + ("ਮਿਲ ਚੁੱਕੀ ਹੈ।" if paid else "ਮਿਲੇਗੀ।") + " ਬਾਕੀ ਰਕਮ ਵਾਢੀ ਤੋਂ ਬਾਅਦ ਸੈਟੇਲਾਈਟ ਜਾਂਚ ਨਾਲ ਤੈਅ ਹੋਵੇਗੀ।",
        }
    if adv:
        return {
            "hi": f"{y} की तस्वीरों में आपका खेत साफ़ नहीं दिखा, इसलिए इस साल अग्रिम राशि नहीं है। "
                  "पूरी राशि कटाई के बाद जाँच से मिलेगी। इस साल खेत साफ़ रहा तो अगले साल अग्रिम मिलेगी।",
            "en": f"Your field was not clearly clean in {y}, so there is no advance this year. The full amount "
                  "comes after the post-harvest check. A clean season this year earns the advance next year.",
            "pa": f"{y} ਦੀਆਂ ਤਸਵੀਰਾਂ ਵਿੱਚ ਤੁਹਾਡਾ ਖੇਤ ਸਾਫ਼ ਨਹੀਂ ਦਿਸਿਆ, ਇਸ ਲਈ ਇਸ ਸਾਲ ਅਗਾਊਂ ਰਕਮ ਨਹੀਂ ਹੈ। "
                  "ਪੂਰੀ ਰਕਮ ਵਾਢੀ ਤੋਂ ਬਾਅਦ ਜਾਂਚ ਨਾਲ ਮਿਲੇਗੀ। ਇਸ ਸਾਲ ਖੇਤ ਸਾਫ਼ ਰਿਹਾ ਤਾਂ ਅਗਲੇ ਸਾਲ ਅਗਾਊਂ ਰਕਮ ਮਿਲੇਗੀ।",
        }
    return {"hi": "", "en": "", "pa": ""}


def _money(claim: dict) -> dict:
    s = claim.get("settlement") or {}
    adv = claim.get("advance") or {}
    paid = adv.get("amount", 0) if adv.get("status") == "paid" else 0
    if s.get("state") == "balance_due":
        bal = rupees(s["balance"])
        hi, en, pa = f" बाकी राशि ₹{bal} जारी की जाएगी", f" The remaining Rs {bal} will be released", f" ਬਾਕੀ ₹{bal} ਜਾਰੀ ਕੀਤੇ ਜਾਣਗੇ"
        if paid:
            hi += f" (₹{rupees(paid)} अग्रिम पहले मिल चुकी है)"
            en += f" (Rs {rupees(paid)} was paid as advance)"
            pa += f" (₹{rupees(paid)} ਅਗਾਊਂ ਪਹਿਲਾਂ ਮਿਲ ਚੁੱਕੇ ਹਨ)"
        hi += "।"
        en += "."
        pa += "।"
        if adv and not adv.get("eligible"):
            hi += " इस साल खेत साफ़ रहा, अगले साल आपको अग्रिम राशि मिलेगी।"
            en += " This clean season earns you the advance next year."
            pa += " ਇਸ ਸਾਲ ਖੇਤ ਸਾਫ਼ ਰਿਹਾ, ਅਗਲੇ ਸਾਲ ਤੁਹਾਨੂੰ ਅਗਾਊਂ ਰਕਮ ਮਿਲੇਗੀ।"
        return {"hi": hi, "en": en, "pa": pa}
    if s.get("state") == "recover_advance":
        r = rupees(s["recover"])
        return {"hi": f" पहले दी गई ₹{r} की अग्रिम राशि वापस करनी होगी; ग्राम अधिकारी आपको लिखित सूचना देंगे।",
                "en": f" The advance of Rs {r} has to be returned; the village officer will send a written notice.",
                "pa": f" ਪਹਿਲਾਂ ਦਿੱਤੀ ₹{r} ਦੀ ਅਗਾਊਂ ਰਕਮ ਵਾਪਸ ਕਰਨੀ ਪਵੇਗੀ; ਪਿੰਡ ਦੇ ਅਧਿਕਾਰੀ ਤੁਹਾਨੂੰ ਲਿਖਤੀ ਸੂਚਨਾ ਭੇਜਣਗੇ।"}
    return {"hi": "", "en": "", "pa": ""}


def farmer_text(claim: dict) -> dict:
    """Returns {"hi", "en", "pa"} for the claim's current status, with the money line."""
    base = _status_text(claim)
    money = _money(claim)
    return {k: base[k] + money[k] for k in ("hi", "en", "pa")}


def _status_text(claim: dict) -> dict:
    status = claim["status"]
    dec = claim.get("decision") or {}
    name = claim.get("farmer_name_hi") or claim.get("farmer_name", "")
    greet_hi = f"नमस्ते {name} जी। " if name else "नमस्ते। "
    name_pa = _pa_name(claim, "farmer_name")
    greet_pa = f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {name_pa} ਜੀ। " if name_pa else "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ। "
    field = claim.get("field_name", "")
    field_hi = claim.get("field_name_hi") or field
    field_pa = _pa_name(claim, "field_name")

    if status == "auto_approved":
        n = len(dec.get("clear_dates", []))
        return {
            "hi": greet_hi + f"{field_hi} खेत के लिए आपका दावा स्वीकृत हो गया है। उपग्रह की {n} साफ़ तस्वीरों में "
                  "पराली जलाने का कोई निशान नहीं मिला।",
            "en": f"Your claim for {field} is approved. {n} clear satellite images show no sign of burning.",
            "pa": greet_pa + f"{field_pa} ਖੇਤ ਲਈ ਤੁਹਾਡਾ ਦਾਅਵਾ ਮਨਜ਼ੂਰ ਹੋ ਗਿਆ ਹੈ। ਸੈਟੇਲਾਈਟ ਦੀਆਂ {n} ਸਾਫ਼ ਤਸਵੀਰਾਂ ਵਿੱਚ "
                  "ਪਰਾਲੀ ਸਾੜਨ ਦਾ ਕੋਈ ਨਿਸ਼ਾਨ ਨਹੀਂ ਮਿਲਿਆ।",
        }
    if status == "needs_review":
        rule = dec.get("rule", "")
        return {
            "hi": greet_hi + f"{field_hi} खेत का दावा ग्राम अधिकारी को जाँच के लिए भेजा गया है। "
                  + REASON_HI.get(rule, "") + " आपको अभी कुछ करने की ज़रूरत नहीं है।",
            "en": f"Your claim for {field} has gone to the village officer for a check. "
                  + REASON_EN.get(rule, "") + " You do not need to do anything now.",
            "pa": greet_pa + f"{field_pa} ਖੇਤ ਦਾ ਦਾਅਵਾ ਪਿੰਡ ਦੇ ਅਧਿਕਾਰੀ ਕੋਲ ਜਾਂਚ ਲਈ ਭੇਜਿਆ ਗਿਆ ਹੈ। "
                  + REASON_PA.get(rule, "") + " ਤੁਹਾਨੂੰ ਹਾਲੇ ਕੁਝ ਕਰਨ ਦੀ ਲੋੜ ਨਹੀਂ।",
        }
    if status == "possible_burn":
        when = dec.get("burn_date")
        when_hi = f"{hi_date(when)} के आसपास " if when else ""
        when_en = f"around {date.fromisoformat(when):%d %b} " if when else ""
        when_pa = f"{pa_date(when)} ਦੇ ਆਸ-ਪਾਸ " if when else ""
        return {
            "hi": greet_hi + f"उपग्रह तस्वीरों में {when_hi}{field_hi} खेत में जलने जैसा निशान दिखा है। "
                  "यह अंतिम फ़ैसला नहीं है। ग्राम अधिकारी तस्वीरें देखकर तय करेंगे, और आप अपनी बात रख सकते हैं।",
            "en": f"Satellite images show a burn-like mark on {field} {when_en}. This is not a final decision. "
                  "The village officer will look at the images, and you can give your side.",
            "pa": greet_pa + f"ਸੈਟੇਲਾਈਟ ਤਸਵੀਰਾਂ ਵਿੱਚ {when_pa}{field_pa} ਖੇਤ ਵਿੱਚ ਸੜਨ ਵਰਗਾ ਨਿਸ਼ਾਨ ਦਿਸਿਆ ਹੈ। "
                  "ਇਹ ਆਖ਼ਰੀ ਫ਼ੈਸਲਾ ਨਹੀਂ ਹੈ। ਪਿੰਡ ਦੇ ਅਧਿਕਾਰੀ ਤਸਵੀਰਾਂ ਦੇਖ ਕੇ ਫ਼ੈਸਲਾ ਕਰਨਗੇ, ਅਤੇ ਤੁਸੀਂ ਆਪਣੀ ਗੱਲ ਰੱਖ ਸਕਦੇ ਹੋ।",
        }
    if status == "officer_approved":
        return {
            "hi": greet_hi + f"ग्राम अधिकारी ने {field_hi} खेत के लिए आपका दावा स्वीकृत कर दिया है।",
            "en": f"The village officer approved your claim for {field}.",
            "pa": greet_pa + f"ਪਿੰਡ ਦੇ ਅਧਿਕਾਰੀ ਨੇ {field_pa} ਖੇਤ ਲਈ ਤੁਹਾਡਾ ਦਾਅਵਾ ਮਨਜ਼ੂਰ ਕਰ ਦਿੱਤਾ ਹੈ।",
        }
    if status == "officer_confirmed_burnt":
        return {
            "hi": greet_hi + f"ग्राम अधिकारी ने जाँच के बाद पाया कि {field_hi} खेत में पराली जलाई गई थी, "
                  "इसलिए दावा स्वीकृत नहीं हुआ। आप इस फ़ैसले पर आपत्ति दर्ज कर सकते हैं।",
            "en": f"After checking, the village officer found that straw was burnt on {field}, so the claim "
                  "was not approved. You can object to this decision.",
            "pa": greet_pa + f"ਪਿੰਡ ਦੇ ਅਧਿਕਾਰੀ ਨੇ ਜਾਂਚ ਤੋਂ ਬਾਅਦ ਪਾਇਆ ਕਿ {field_pa} ਖੇਤ ਵਿੱਚ ਪਰਾਲੀ ਸਾੜੀ ਗਈ ਸੀ, "
                  "ਇਸ ਲਈ ਦਾਅਵਾ ਮਨਜ਼ੂਰ ਨਹੀਂ ਹੋਇਆ। ਤੁਸੀਂ ਇਸ ਫ਼ੈਸਲੇ ਉੱਤੇ ਇਤਰਾਜ਼ ਦਰਜ ਕਰ ਸਕਦੇ ਹੋ।",
        }
    return {
        "hi": greet_hi + f"{field_hi} खेत का दावा मिल गया है। उपग्रह तस्वीरों की जाँच चल रही है।",
        "en": f"Your claim for {field} has been received. The satellite check is running.",
        "pa": greet_pa + f"{field_pa} ਖੇਤ ਦਾ ਦਾਅਵਾ ਮਿਲ ਗਿਆ ਹੈ। ਸੈਟੇਲਾਈਟ ਤਸਵੀਰਾਂ ਦੀ ਜਾਂਚ ਚੱਲ ਰਹੀ ਹੈ।",
    }
