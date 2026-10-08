"""Draft recovery notice for an officer-confirmed burn on a field that received an advance.

The system drafts; the officer reviews, signs and decides whether to issue it. Fines, red entries and FIRs
are separate decisions the notice only refers to.
"""
import html
from datetime import date

from parali.messages import hi_date


def render(claim: dict, evidence_url: str, today: date | None = None) -> str:
    today = today or date.today()
    s = claim.get("settlement") or {}
    adv = claim.get("advance") or {}
    dec = claim.get("decision") or {}
    rev = claim.get("review") or {}
    e = lambda v: html.escape(str(v if v is not None else ""))  # noqa: E731
    burn = dec.get("burn_date")
    fires = claim.get("fires") or []
    fire_line = (f"{len(fires)} NASA FIRMS fire point(s) within range during the season."
                 if fires else "No NASA FIRMS fire point near the field; the burn was found in Sentinel-2 imagery.")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Recovery notice {e(claim['id'])}</title>
<style>
body{{font:14px/1.55 system-ui,"Noto Sans Devanagari",sans-serif;max-width:760px;margin:24px auto;padding:0 16px;color:#111}}
h1{{font-size:18px;margin:0 0 4px}} .draft{{color:#a3321e;font-weight:600}} table{{border-collapse:collapse;width:100%;margin:10px 0}}
td{{border:1px solid #ccc;padding:6px 8px;vertical-align:top}} td:first-child{{width:38%;color:#444}} img{{max-width:100%;border:1px solid #ccc}}
.hi{{margin-top:18px;padding-top:12px;border-top:1px dashed #999}}
</style></head><body>
<p class="draft">DRAFT for officer review. Not issued until signed.</p>
<h1>Notice: recovery of advance under the Crop Residue Management incentive</h1>
<p>Date: {e(today.isoformat())} &nbsp; Reference: {e(claim['id'])}</p>
<table>
<tr><td>Farmer</td><td>{e(claim.get('farmer_name'))}</td></tr>
<tr><td>Field</td><td>{e(claim.get('field_name'))}, {e(claim.get('village'))} ({e(claim.get('acres'))} acres)</td></tr>
<tr><td>Season</td><td>{e(claim.get('season_start'))} to {e(claim.get('season_end'))}</td></tr>
<tr><td>Advance paid</td><td>Rs {e(adv.get('amount'))} on the basis of a clean {e(adv.get('prev_season'))} season</td></tr>
<tr><td>Finding</td><td>Burn-like scar on the field from {e(burn)}; {e(dec.get('reason'))} {e(fire_line)}</td></tr>
<tr><td>Confirmed by</td><td>{e(rev.get('officer_id'))} on {e((rev.get('at') or '')[:10])}. Officer note: {e(rev.get('note'))}</td></tr>
<tr><td>Amount to be recovered</td><td><b>Rs {e(s.get('recover'))}</b> (the advance). The balance of the incentive is not payable for this season.</td></tr>
<tr><td>For reference</td><td>Environmental compensation for stubble burning for this landholding under the CAQM rules (2024 amendment) is Rs {e(s.get('compensation_reference'))} per incident. Whether to levy it, make a red entry or file a case is a separate decision.</td></tr>
</table>
<p>Satellite evidence (Sentinel-2, each column one clear image; red outline marks the first burn-like image):</p>
<img src="{e(evidence_url)}" alt="Sentinel-2 images of the field across the season">
<p>The farmer may respond within 15 days with any evidence that the field was not burnt (for example a
baler or happy seeder receipt, or a site inspection request). The images above can be reviewed with the
village officer.</p>
<div class="hi" lang="hi">
<p><b>सूचना: फसल अवशेष प्रबंधन प्रोत्साहन की अग्रिम राशि की वसूली (मसौदा)</b></p>
<p>{e(claim.get('farmer_name_hi') or claim.get('farmer_name'))} जी, आपके खेत {e(claim.get('field_name_hi') or claim.get('field_name'))}
की उपग्रह तस्वीरों में {e(hi_date(burn) if burn else '')} के आसपास पराली जलाने का निशान मिला, जिसकी पुष्टि ग्राम अधिकारी ने की है।
इसलिए पिछले सीज़न के आधार पर दी गई अग्रिम राशि रु {e(s.get('recover'))} वापस करनी होगी।
आप 15 दिन के भीतर अपना पक्ष और कोई सबूत दे सकते हैं।</p>
</div>
</body></html>"""
