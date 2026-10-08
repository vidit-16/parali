"""What the farmer hears and reads. Fixed text per outcome, filled from the decision. No model writes these."""
from datetime import date

HI_MONTHS = ("जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर")

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


def hi_date(d: date | str) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{d.day} {HI_MONTHS[d.month - 1]}"


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
        }
    if adv:
        return {
            "hi": f"{y} की तस्वीरों में आपका खेत साफ़ नहीं दिखा, इसलिए इस साल अग्रिम राशि नहीं है। "
                  "पूरी राशि कटाई के बाद जाँच से मिलेगी। इस साल खेत साफ़ रहा तो अगले साल अग्रिम मिलेगी।",
            "en": f"Your field was not clearly clean in {y}, so there is no advance this year. The full amount "
                  "comes after the post-harvest check. A clean season this year earns the advance next year.",
        }
    return {"hi": "", "en": ""}


def _money(claim: dict) -> dict:
    s = claim.get("settlement") or {}
    adv = claim.get("advance") or {}
    paid = adv.get("amount", 0) if adv.get("status") == "paid" else 0
    if s.get("state") == "balance_due":
        hi = f" बाकी राशि ₹{rupees(s['balance'])} जारी की जाएगी"
        en = f" The remaining Rs {rupees(s['balance'])} will be released"
        if paid:
            hi += f" (₹{rupees(paid)} अग्रिम पहले मिल चुकी है)"
            en += f" (Rs {rupees(paid)} was paid as advance)"
        hi += "।"
        en += "."
        if adv and not adv.get("eligible"):
            hi += " इस साल खेत साफ़ रहा, अगले साल आपको अग्रिम राशि मिलेगी।"
            en += " This clean season earns you the advance next year."
        return {"hi": hi, "en": en}
    if s.get("state") == "recover_advance":
        return {"hi": f" पहले दी गई ₹{rupees(s['recover'])} की अग्रिम राशि वापस करनी होगी; ग्राम अधिकारी आपको लिखित सूचना देंगे।",
                "en": f" The advance of Rs {rupees(s['recover'])} has to be returned; the village officer will send a written notice."}
    return {"hi": "", "en": ""}


def farmer_text(claim: dict) -> dict:
    """Returns {"hi": ..., "en": ...} for the claim's current status, with the money line."""
    base = _status_text(claim)
    money = _money(claim)
    return {"hi": base["hi"] + money["hi"], "en": base["en"] + money["en"]}


def _status_text(claim: dict) -> dict:
    status = claim["status"]
    dec = claim.get("decision") or {}
    name = claim.get("farmer_name_hi") or claim.get("farmer_name", "")
    greet_hi = f"नमस्ते {name} जी। " if name else "नमस्ते। "
    field = claim.get("field_name", "")
    field_hi = claim.get("field_name_hi") or field

    if status == "auto_approved":
        n = len(dec.get("clear_dates", []))
        return {
            "hi": greet_hi + f"{field_hi} खेत के लिए आपका दावा स्वीकृत हो गया है। उपग्रह की {n} साफ़ तस्वीरों में "
                  "पराली जलाने का कोई निशान नहीं मिला।",
            "en": f"Your claim for {field} is approved. {n} clear satellite images show no sign of burning.",
        }
    if status == "needs_review":
        rule = dec.get("rule", "")
        return {
            "hi": greet_hi + f"{field_hi} खेत का दावा ग्राम अधिकारी को जाँच के लिए भेजा गया है। "
                  + REASON_HI.get(rule, "") + " आपको अभी कुछ करने की ज़रूरत नहीं है।",
            "en": f"Your claim for {field} has gone to the village officer for a check. "
                  + REASON_EN.get(rule, "") + " You do not need to do anything now.",
        }
    if status == "possible_burn":
        when = dec.get("burn_date")
        when_hi = f"{hi_date(when)} के आसपास " if when else ""
        when_en = f"around {date.fromisoformat(when):%d %b} " if when else ""
        return {
            "hi": greet_hi + f"उपग्रह तस्वीरों में {when_hi}{field_hi} खेत में जलने जैसा निशान दिखा है। "
                  "यह अंतिम फ़ैसला नहीं है। ग्राम अधिकारी तस्वीरें देखकर तय करेंगे, और आप अपनी बात रख सकते हैं।",
            "en": f"Satellite images show a burn-like mark on {field} {when_en}. This is not a final decision. "
                  "The village officer will look at the images, and you can give your side.",
        }
    if status == "officer_approved":
        return {
            "hi": greet_hi + f"ग्राम अधिकारी ने {field_hi} खेत के लिए आपका दावा स्वीकृत कर दिया है।",
            "en": f"The village officer approved your claim for {field}.",
        }
    if status == "officer_confirmed_burnt":
        return {
            "hi": greet_hi + f"ग्राम अधिकारी ने जाँच के बाद पाया कि {field_hi} खेत में पराली जलाई गई थी, "
                  "इसलिए दावा स्वीकृत नहीं हुआ। आप इस फ़ैसले पर आपत्ति दर्ज कर सकते हैं।",
            "en": f"After checking, the village officer found that straw was burnt on {field}, so the claim "
                  "was not approved. You can object to this decision.",
        }
    return {
        "hi": greet_hi + f"{field_hi} खेत का दावा मिल गया है। उपग्रह तस्वीरों की जाँच चल रही है।",
        "en": f"Your claim for {field} has been received. The satellite check is running.",
    }
