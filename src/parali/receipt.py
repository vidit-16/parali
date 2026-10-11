"""Payment advice for a farmer's incentive balance, written once the payout succeeds.

Same letterhead and style as the recovery notice. It records what was paid, for which field and season, and the
payment references Cashfree returned. In this demo the payout runs in Cashfree's test mode, and the page says so.
"""
import html

from parali.messages import hi_date, pa_date, rupees, to_gurmukhi
from parali.notice import STATE, _d
from parali.store import Store


def render(claim: dict) -> str:
    p, s, adv = claim.get("payout") or {}, claim.get("settlement") or {}, claim.get("advance") or {}
    e = lambda v: html.escape(str(v if v is not None else ""))  # noqa: E731
    st = STATE.get(claim.get("state_code"), STATE["PB"])
    ref = f"SKS/PAY/2025/{claim['id'][:6].upper()}-{p.get('n', 1)}"
    advance = adv.get("amount", 0) if adv.get("status") == "paid" else 0
    by = (claim.get("review") or {}).get("officer_id")
    why = (f"The village officer ({by}) reviewed the satellite pictures of your field for the 2025 season and approved your claim."
           if by else "No burning showed in any clear satellite picture of your field in the 2025 season, so your claim was approved.")
    name_hi = claim.get("farmer_name_hi") or claim.get("farmer_name", "")
    field_hi = claim.get("field_name_hi") or claim.get("field_name", "")
    paid_on = (p.get("paid_at") or "")[:10]
    local = (f'<section class="local" lang="pa"><p>{e(to_gurmukhi(name_hi))} ਜੀ, ਖੇਤ {e(to_gurmukhi(field_hi))} ਲਈ ਬਾਕੀ ₹{e(rupees(p.get("amount") or 0))} '
             f'{e(pa_date(paid_on) if paid_on else "")} ਨੂੰ ਤੁਹਾਡੇ ਬੈਂਕ ਖਾਤੇ ਵਿੱਚ ਭੇਜੇ ਗਏ।</p></section>') if claim.get("state_code") == "PB" else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Payment advice {e(ref)}</title>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Geist:wght@500;600&family=Mukta:wght@400;600&family=Noto+Sans+Gurmukhi:wght@400;600&display=swap" rel="stylesheet">
<style>
@page {{ size: A4; margin: 16mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #E9E6DF; color: #1B1B1B; font: 15px/1.6 "Source Serif 4", Georgia, serif; }}
.sheet {{ max-width: 760px; margin: 28px auto; padding: 44px 52px 36px; background: #FFFEFB; box-shadow: 0 2px 20px rgba(0,0,0,.12); }}
.head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; padding-bottom: 14px; border-bottom: 2px solid #1B1B1B; }}
.dept {{ font: 600 13px/1.4 Geist, sans-serif; }}
.dept b {{ display: block; font: 700 19px/1.25 "Source Serif 4", serif; }}
.dept small {{ color: #6B6B6B; font-weight: 500; }}
.mark {{ width: 52px; height: 52px; border-radius: 14px; background: linear-gradient(225deg, #3D6BFF, #D9468C 55%, #FF8A3D); color: #fff; display: grid; place-items: center; font: 700 22px Mukta, sans-serif; flex: none; }}
.meta {{ display: flex; justify-content: space-between; margin: 14px 0 20px; font: 500 12.5px Geist, sans-serif; color: #444; }}
.status {{ display: inline-block; margin-bottom: 16px; padding: 3px 10px; border: 1.5px solid #1F8A4C; border-radius: 4px; color: #1F8A4C; font: 600 11.5px Geist, sans-serif; letter-spacing: .08em; }}
h1 {{ font-size: 17px; margin: 0 0 12px; }} h1 span {{ font-weight: 400; }}
p {{ margin: 0 0 12px; }}
.amount {{ display: flex; align-items: baseline; justify-content: space-between; margin: 8px 0 18px; padding: 16px 18px; border-radius: 8px; background: #EEF8F1; border: 1.5px solid #1F8A4C; font-family: Geist, sans-serif; }}
.amount span {{ color: #1F5E3A; font-size: 13px; }} .amount b {{ color: #1F8A4C; font-size: 26px; }}
table {{ width: 100%; border-collapse: collapse; margin: 0 0 18px; font-size: 14px; }}
td {{ padding: 8px 10px; border-top: 1px solid #DDD8CC; vertical-align: top; }}
tr:last-child td {{ border-bottom: 1px solid #DDD8CC; }}
td:first-child {{ width: 36%; color: #6B6B6B; font: 500 12.5px Geist, sans-serif; padding-top: 10px; }}
.mono {{ font-family: ui-monospace, Consolas, monospace; font-size: 13px; }}
.local {{ margin-top: 20px; padding-top: 14px; border-top: 1px dashed #A9A396; font-family: "Noto Sans Gurmukhi", sans-serif; }}
.foot {{ margin-top: 22px; font: 500 11px Geist, sans-serif; color: #8A8478; }}
.print {{ position: fixed; right: 18px; bottom: 18px; padding: 10px 16px; border: 0; border-radius: 10px; background: #1B1B1B; color: #fff; font: 600 13px Geist, sans-serif; cursor: pointer; }}
@media print {{ body {{ background: #fff; }} .sheet {{ margin: 0; box-shadow: none; max-width: none; }} .print {{ display: none; }} }}
@media (max-width: 640px) {{ .sheet {{ margin: 0; padding: 26px 20px 84px; }} }}
</style></head><body>
<article class="sheet">
<header class="head"><div class="dept"><b>Agriculture Department</b>Crop Residue Management incentive · {e(st[0])}<br><small>Prepared with Saakshi satellite verification</small></div><div class="mark">सा</div></header>
<div class="meta"><span>Ref. {e(ref)}</span><span>{e(_d(paid_on))}</span></div>
<span class="status">PAID</span>
<p>To <b>{e(claim.get('farmer_name'))}</b>, {e(claim.get('field_name'))}, {e(claim.get('village'))}, {e(st[0])}</p>
<h1>Payment advice: <span>balance of the no-burn incentive, kharif 2025</span></h1>
<p>{e(why)} The balance of your incentive has been paid to your bank account.</p>
<div class="amount"><span>Balance paid</span><b>₹{e(rupees(p.get('amount') or 0))}</b></div>
<table>
<tr><td>Field</td><td>{e(claim.get('field_name'))}, {e(claim.get('village'))} · {e(claim.get('acres'))} acres</td></tr>
<tr><td>Incentive for the season</td><td>₹{e(rupees(s.get('total') or 0))}</td></tr>
<tr><td>Advance paid before harvest</td><td>{"₹" + e(rupees(advance)) if advance else "none"}</td></tr>
<tr><td>Balance paid</td><td>₹{e(rupees(p.get('amount') or 0))} on {e(_d(paid_on))}</td></tr>
<tr><td>Paid through</td><td>{e(p.get('rail'))}</td></tr>
<tr><td>Transfer reference</td><td class="mono">{e(p.get('transfer_id'))} · Cashfree {e(p.get('cf_transfer_id'))}</td></tr>
<tr><td>Bank reference (UTR)</td><td class="mono">{e(p.get('utr') or '—')}</td></tr>
</table>
<section class="local" lang="hi" style="font-family: Mukta, sans-serif"><p>{e(name_hi)} जी, खेत {e(field_hi)} की बाकी राशि ₹{e(rupees(p.get('amount') or 0))}
{e(hi_date(paid_on) if paid_on else '')} को आपके बैंक खाते में भेजी गई।</p></section>
{local}
<p class="foot">Sample payment advice generated by Saakshi. Test mode: Cashfree simulated the bank transfer and no money moved.
Not issued by any government office.</p>
</article>
<button class="print" onclick="print()">Print or save as PDF</button>
</body></html>"""


def write(store: Store, claim: dict) -> None:
    p = claim.get("payout") or {}
    key = f"receipts/{claim['id']}-{p.get('n', 1)}.html"
    store.put_blob(key, render(claim).encode(), "text/html; charset=utf-8")
    p["receipt_key"] = key
