"""Draft recovery notice for an officer-confirmed burn on a field that received an advance.

The system drafts; the officer reviews, signs and decides whether to issue it. Fines, red entries and FIRs
are separate decisions the notice only refers to. The letterhead is generic, and the page carries a DRAFT
watermark: this is a mock-up of the letter a department would send, not a government document.
"""
import html
from datetime import date

from parali import season
from parali.messages import hi_date, pa_date, rupees, to_gurmukhi

STATE = {"PB": ("Punjab", "पंजाब", "ਪੰਜਾਬ"), "HR": ("Haryana", "हरियाणा", "ਹਰਿਆਣਾ")}


def _d(iso: str | None) -> str:
    if not iso:
        return ""
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def render(claim: dict, evidence_url: str, today: date | None = None) -> str:
    s = claim.get("settlement") or {}
    adv = claim.get("advance") or {}
    dec = claim.get("decision") or {}
    rev = claim.get("review") or {}
    rec = claim.get("recovery") or {}
    today = today or (date.fromisoformat(rev["at"][:10]) if rev.get("at") else date.today())  # dated the day the burn was confirmed
    e = lambda v: html.escape(str(v if v is not None else ""))  # noqa: E731
    st = STATE.get(claim.get("state_code"), STATE["PB"])
    burn = dec.get("burn_date")
    fires = claim.get("fires") or []
    ref = f"SKS/CRM/2025/{claim['id'][:6].upper()}"
    recover = rupees(s.get("recover") or 0)
    fire_line = (f"{len(fires)} NASA fire alert(s) were recorded within range during the season."
                 if fires else "No NASA fire alert was recorded near the field; the burn was found in the Sentinel-2 pictures.")
    pay = (f"""<div class="pay"><b>Pay online</b><span>{e(rec.get('url'))}</span><small>Razorpay payment link (test mode). Payment is recorded against reference {e(ref)}.</small></div>"""
           if rec.get("status") == "issued" and rec.get("url") else "")
    paid = rec.get("status") == "paid"
    if paid:
        pay = (f"""<div class="pay paid"><b>Returned on {e(_d(rec.get('paid_at')))}</b><span>₹{e(rupees(rec.get('amount') or s.get('recover') or 0))} received</span>"""
               f"""<small>Razorpay payment {e(rec.get('payment_id') or '')} (test mode), against reference {e(ref)}. Nothing more is due.</small></div>""")
    name_hi = claim.get("farmer_name_hi") or claim.get("farmer_name", "")
    field_hi = claim.get("field_name_hi") or claim.get("field_name", "")
    pa = ""
    if claim.get("state_code") == "PB":
        pa = f"""<section class="local" lang="pa"><h3>ਸੂਚਨਾ: ਅਗਾਊਂ ਰਕਮ ਦੀ ਵਾਪਸੀ (ਮਸੌਦਾ)</h3>
<p>{e(to_gurmukhi(name_hi))} ਜੀ, ਤੁਹਾਡੇ ਖੇਤ {e(to_gurmukhi(field_hi))} ਦੀਆਂ ਸੈਟੇਲਾਈਟ ਤਸਵੀਰਾਂ ਵਿੱਚ {e(pa_date(burn) if burn else '')} ਦੇ ਆਸ-ਪਾਸ
ਪਰਾਲੀ ਸਾੜਨ ਦਾ ਨਿਸ਼ਾਨ ਮਿਲਿਆ, ਜਿਸ ਦੀ ਪੁਸ਼ਟੀ ਪਿੰਡ ਦੇ ਅਧਿਕਾਰੀ ਨੇ ਕੀਤੀ ਹੈ। ਇਸ ਲਈ ਪਿਛਲੇ ਸੀਜ਼ਨ ਦੇ ਆਧਾਰ ਤੇ ਦਿੱਤੀ ਅਗਾਊਂ ਰਕਮ
₹{e(recover)} ਵਾਪਸ ਕਰਨੀ ਪਵੇਗੀ। ਤੁਸੀਂ 15 ਦਿਨਾਂ ਦੇ ਅੰਦਰ ਆਪਣਾ ਪੱਖ ਅਤੇ ਕੋਈ ਸਬੂਤ ਦੇ ਸਕਦੇ ਹੋ।</p></section>"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recovery notice {e(ref)}</title>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Geist:wght@500;600&family=Mukta:wght@400;600&family=Noto+Sans+Gurmukhi:wght@400;600&display=swap" rel="stylesheet">
<style>
@page {{ size: A4; margin: 16mm 16mm 18mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #E9E6DF; color: #1B1B1B; font: 15px/1.6 "Source Serif 4", Georgia, serif; }}
.sheet {{ position: relative; max-width: 800px; margin: 28px auto; padding: 46px 54px 40px; background: #FFFEFB; box-shadow: 0 2px 20px rgba(0,0,0,.12); overflow: hidden; }}
.sheet::before {{ content: "DRAFT · NOT AN OFFICIAL DOCUMENT"; position: absolute; top: 46%; left: 50%; transform: translate(-50%, -50%) rotate(-28deg); white-space: nowrap;
  font: 700 46px Geist, sans-serif; letter-spacing: .08em; color: rgba(185, 45, 30, .035); pointer-events: none; }}
.head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; padding-bottom: 14px; border-bottom: 2px solid #1B1B1B; }}
.dept {{ font: 600 13px/1.4 Geist, sans-serif; letter-spacing: .02em; }}
.dept b {{ display: block; font: 700 19px/1.25 "Source Serif 4", serif; letter-spacing: 0; }}
.dept small {{ color: #6B6B6B; font-weight: 500; }}
.mark {{ width: 52px; height: 52px; border-radius: 14px; background: linear-gradient(225deg, #3D6BFF, #D9468C 55%, #FF8A3D); color: #fff; display: grid; place-items: center; font: 700 22px Mukta, sans-serif; flex: none; }}
.meta {{ display: flex; justify-content: space-between; margin: 14px 0 22px; font: 500 12.5px Geist, sans-serif; color: #444; }}
.status {{ display: inline-block; margin-bottom: 18px; padding: 3px 10px; border: 1.5px solid #B92D1E; border-radius: 4px; color: #B92D1E; font: 600 11.5px Geist, sans-serif; letter-spacing: .08em; }}
.to {{ margin-bottom: 18px; }}
.to b {{ display: block; }}
h1 {{ font-size: 17px; margin: 0 0 14px; }}
h1 span {{ font-weight: 400; }}
p {{ margin: 0 0 12px; }}
table {{ width: 100%; border-collapse: collapse; margin: 6px 0 18px; font-size: 14px; }}
td {{ padding: 8px 10px; border-top: 1px solid #DDD8CC; vertical-align: top; }}
tr:last-child td {{ border-bottom: 1px solid #DDD8CC; }}
td:first-child {{ width: 34%; color: #6B6B6B; font: 500 12.5px Geist, sans-serif; padding-top: 10px; }}
.amount td {{ background: #FBF1EE; }}
.amount td:last-child {{ font-weight: 700; font-size: 17px; color: #B92D1E; }}
figure {{ margin: 6px 0 18px; }}
figure img {{ width: 100%; border: 1px solid #DDD8CC; image-rendering: pixelated; }}
figcaption {{ font: 500 12px Geist, sans-serif; color: #6B6B6B; margin-top: 6px; }}
.pay {{ display: grid; gap: 2px; margin: 0 0 18px; padding: 12px 14px; border: 1.5px dashed #3D6BFF; border-radius: 8px; font-family: Geist, sans-serif; }}
.pay.paid {{ border: 1.5px solid #1F8A4C; background: #EEF8F1; }} .pay.paid span {{ color: #1F8A4C; font-weight: 600; }}
.pay b {{ font-size: 13px; }} .pay span {{ font-size: 14px; color: #3D6BFF; word-break: break-all; }} .pay small {{ color: #6B6B6B; font-size: 12px; }}
ol {{ margin: 0 0 18px; padding-left: 20px; }}
li {{ margin-bottom: 4px; }}
.signs {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 34px 0 10px; font: 500 12.5px Geist, sans-serif; color: #444; }}
.signs div {{ border-top: 1px solid #1B1B1B; padding-top: 6px; }}
.signs b {{ display: block; color: #1B1B1B; }}
.local {{ margin-top: 26px; padding-top: 16px; border-top: 1px dashed #A9A396; }}
.local h3 {{ margin: 0 0 6px; font-size: 15px; }}
[lang=hi] {{ font-family: Mukta, sans-serif; }} [lang=pa] {{ font-family: "Noto Sans Gurmukhi", sans-serif; }}
.foot {{ margin-top: 24px; font: 500 11px Geist, sans-serif; color: #8A8478; }}
.print {{ position: fixed; right: 18px; bottom: 18px; padding: 10px 16px; border: 0; border-radius: 10px; background: #1B1B1B; color: #fff; font: 600 13px Geist, sans-serif; cursor: pointer; }}
@media print {{ body {{ background: #fff; }} .sheet {{ margin: 0; padding: 0; box-shadow: none; max-width: none; }} .print {{ display: none; }} }}
@media (max-width: 640px) {{ .sheet {{ margin: 0; padding: 26px 20px; }} .signs {{ grid-template-columns: 1fr; }} }}
</style></head><body>
<article class="sheet">
<header class="head"><div class="dept"><b>Agriculture Department</b>Crop Residue Management incentive · {e(st[0])}<br><small>Prepared with Saakshi satellite verification</small></div><div class="mark">सा</div></header>
<div class="meta"><span>Ref. {e(ref)}</span><span>{e(_d(today.isoformat()))}</span></div>
<span class="status">{"ADVANCE RETURNED · CASE CLOSED" if paid else "DRAFT FOR OFFICER REVIEW · NOT ISSUED UNTIL SIGNED"}</span>
<div class="to">To<b>{e(claim.get('farmer_name'))}</b>{e(claim.get('field_name'))}, {e(claim.get('village'))}, {e(st[0])}</div>
<h1>Subject: <span>recovery of the advance paid under the Crop Residue Management incentive, kharif 2025</span></h1>
<p>An advance of ₹{e(rupees(adv.get('amount') or 0))} was paid to you before harvest because your field showed no burning in {e(adv.get('prev_season'))}.
The incentive is paid on the condition that crop residue is not burnt this season.</p>
<p>Sentinel-2 satellite pictures of your field show a burn scar from {e(_d(burn))}. {e(fire_line)} The village officer reviewed the
pictures{(" and noted: “" + e(rev.get('note')) + "”") if rev.get('note') else ""} and confirmed the burn on {e(_d(rev.get('at')))}.</p>
<table>
<tr><td>Field</td><td>{e(claim.get('field_name'))}, {e(claim.get('village'))} · {e(claim.get('acres'))} acres</td></tr>
<tr><td>Season checked</td><td>{e(_d(claim.get('season_start')))} to {e(_d(claim.get('season_end')))}</td></tr>
<tr><td>Advance paid</td><td>₹{e(rupees(adv.get('amount') or 0))}{(" on " + e(_d(adv.get('paid_at')))) if adv.get('paid_at') else ""}</td></tr>
<tr><td>Satellite finding</td><td>Burn scar from {e(_d(burn))}; {len(dec.get('clear_dates') or [])} clear pictures read</td></tr>
<tr><td>Confirmed by</td><td>{e(rev.get('officer_id'))}, village officer</td></tr>
<tr><td>Estimated smoke released</td><td>≈ {season.smoke_kg(claim.get('acres'))} kg of fine particles (PM2.5)</td></tr>
<tr class="amount"><td>{"Amount returned" if paid else "Amount to be returned"}</td><td>₹{e(recover)}{(" · paid " + e(_d(rec.get('paid_at')))) if paid else ""}</td></tr>
</table>
<figure><img src="{e(evidence_url)}" alt="Satellite pictures of the field through the season"><figcaption>Sentinel-2 pictures of the field, one column per clear date: colour above, infrared below (burnt ground shows maroon). The red outline marks the date of the burn scar.</figcaption></figure>
{pay}
{"" if not paid else "<!--"}<p><b>How to respond.</b> Within 15 days of this notice you may:</p>
<ol><li>return ₹{e(recover)}{" using the payment link above" if pay else ""}; or</li>
<li>show that the field was not burnt, for example with a baler or happy-seeder receipt, or ask for a site inspection; or</li>
<li>appeal in the Saakshi app or on WhatsApp. Nothing is recovered while an appeal is open.</li></ol>{"" if not paid else "-->"}
<p>Environmental compensation for stubble burning on this landholding under the CAQM rules (2024 amendment) is ₹{e(rupees(s.get('compensation_reference') or 0))} per incident.
Whether to levy it, make a red entry or file a case is a separate decision and is not part of this notice.</p>
<div class="signs"><div><b>Village officer</b>{e(rev.get('officer_id'))} · signature and date</div><div><b>Received by the farmer</b>signature or thumb impression and date</div></div>
<section class="local" lang="hi"><h3>सूचना: अग्रिम राशि की वापसी (मसौदा)</h3>
<p>{e(name_hi)} जी, आपके खेत {e(field_hi)} की उपग्रह तस्वीरों में {e(hi_date(burn) if burn else '')} के आसपास पराली जलाने का निशान मिला,
जिसकी पुष्टि ग्राम अधिकारी ने की है। इसलिए पिछले सीज़न के आधार पर दी गई अग्रिम राशि ₹{e(recover)} वापस करनी होगी।
आप 15 दिन के भीतर अपना पक्ष और कोई सबूत दे सकते हैं, या ऐप अथवा WhatsApp पर अपील कर सकते हैं।</p></section>
{pa}
<p class="foot">Sample notice generated by Saakshi. Not issued by any government office.</p>
</article>
<button class="print" onclick="print()">Print or save as PDF</button>
</body></html>"""
