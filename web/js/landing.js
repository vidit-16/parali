import { api, esc } from "./ui.js";

export async function landing(app) {
  const [n, stats] = await Promise.all([
    fetch("data/numbers.json").then((r) => r.json()),
    api("/api/stats").catch(() => null),
  ]);
  const r = n.rules, f = n.firms, a = n.advance, c = n.context, h = n.held_out;

  app.innerHTML = `
  <section class="hero">
    <div>
      <div class="kicker">Air track · stubble burning · Haryana</div>
      <h1>Pay farmers before harvest for not burning. Check every field from space after.</h1>
      <p class="hi-line" lang="hi">कटाई से पहले अग्रिम राशि, कटाई के बाद उपग्रह से हर खेत की जाँच।</p>
      <p class="lead">Fire alerts punish farmers who never burnt, and the no-burn reward arrives too late to change
        anything. Parali Check verifies every field with free Sentinel-2 images, so the state can pay before harvest
        and recover money only where an officer confirms a burn.</p>
      <div class="row">
        <a class="btn green" href="#/story">▶ Play the season</a>
        <a class="btn secondary" href="#/farmer"><span lang="hi">मैं किसान हूँ</span> · Farmer</a>
        <a class="btn secondary" href="#/officer">Village officer</a>
      </div>
    </div>
    <figure class="card hero-card" style="margin:0">
      <img src="img/satbir.png" alt="Satbir Singh's field across the 2025 season: stays tan while a neighbouring field turns black on 7 November">
      <figcaption class="cap"><b>Satbir Singh, West Kaithal.</b> A satellite fire alert 98 m away would put a red entry
        on his record: no MSP sale for two seasons. His field (outline) stays clean all season; the black patch on
        7 Nov is a neighbour's.</figcaption>
    </figure>
  </section>

  <section class="section">
    <div class="kicker">The problem in three numbers</div>
    <div class="grid g3">
      <div class="card stat ember"><div class="big">${c.delhi_pm25_share_peak}%</div>
        <p>of Delhi's PM2.5 came from farm fires on the worst day of November 2024.</p>
        <p class="small muted">${esc(c.delhi_pm25_source)}</p></div>
      <div class="card stat straw"><div class="big">${f.clean_flagged}%</div>
        <p>of clean fields are flagged by thermal fire alerts alone, which caught only ${f.burns_caught}% of actual
          burns: fields are burnt and ploughed between satellite passes.</p>
        <p class="small muted">Our measurement, ${n.labelled_plots} hand-labelled plots in west Kaithal, 2025 season.</p></div>
      <div class="card stat green"><div class="big">+${c.upfront_trial_gain_pp}<span style="font-size:.5em"> pts</span></div>
        <p>compliance when farmers got 25% of the no-burn payment upfront, in a randomised trial in Punjab.
          Paying only after verification barely changed behaviour.</p>
        <p class="small muted">${esc(c.upfront_trial_source)}</p></div>
    </div>
    <p class="muted small" style="margin-top:12px">Haryana pays ₹${c.incentive_per_acre.toLocaleString("en-IN")}/acre for
      managing straw without burning, after a manual check that farmers call slow and unreliable; in Kaithal only
      ${esc(c.kaithal_applied)} registered farmers applied. Paying upfront at scale needs cheap, fast, fair verification.
      That is what this builds.</p>
  </section>

  <section class="section">
    <div class="kicker">How it works</div>
    <h2>Advance, verify, settle</h2>
    <div class="grid g3 steps">
      <div class="card step"><h3>Before harvest</h3><p>Each registered field is checked against <b>last season's</b>
        images. Clean last season: 25% of the incentive is paid now. Burnt last season: no advance; one clean
        season earns it back.</p><p class="small muted">${a.eligible_share}% of cropland qualified for 2025.</p></div>
      <div class="card step"><h3>After harvest</h3><p>Every clear Sentinel-2 image of the field from 1 Oct to 30 Nov is
        read from the AWS Open Data registry. Fixed rules look for the signature of a burn: near-infrared drops in one
        step and the field turns near-black.</p><p class="small muted">Clean fields are approved and the balance released automatically.</p></div>
      <div class="card step"><h3>Officer confirms</h3><p>Unclear cases and every possible burn go to the village officer
        with the images. A confirmed burn on an advanced field gets a recovery notice drafted with the evidence.</p>
        <p class="small muted">The system never rejects or penalises on its own.</p></div>
    </div>
  </section>

  <section class="section">
    <div class="kicker">Measured, not promised</div>
    <h2>Against the fire alerts used today</h2>
    <div class="card">
      <table class="plain">
        <tr><th></th><th>Satellite check (this project)</th><th>Fire alerts alone (FIRMS, 375 m)</th></tr>
        <tr><td>Clean fields wrongly flagged</td><td class="num" style="color:var(--green)">${r.clean_flagged}% <span class="muted small">(held-out: ${h.clean_flagged.join("%, ")}%)</span></td><td class="num" style="color:var(--ember)">${f.clean_flagged}%</td></tr>
        <tr><td>Burnt fields approved without a human</td><td class="num">${r.burnt_auto_approved}% <span class="muted small">(held-out: ${h.burnt_auto_approved.join("%, ")}%)</span></td><td class="muted">n/a</td></tr>
        <tr><td>Burns caught</td><td class="num">every labelled burn went to the officer</td><td class="num">${f.burns_caught}%</td></tr>
        <tr><td>Claims settled without an officer</td><td class="num">${r.auto_approved}% <span class="muted small">(held-out: ${h.auto_approved.join("%, ")}%)</span></td><td class="muted">all checked by hand</td></tr>
      </table>
      <p class="small muted" style="margin:12px 0 0">${n.labelled_plots} plots of 80 m labelled by hand from the image series
        (${n.burnt_labels} burnt), sampled by distance to fire points and by burn signal, weighted back to the whole area.
        "Held-out": thresholds fitted on one half, scored on the other. Advance check: fields clean in 2024 burnt in 2025
        at ${a.burnt_if_clean_last_year}%, fields not clean in 2024 at ${a.burnt_if_not_clean_last_year}%.</p>
    </div>
  </section>

  <section class="section split">
    <div class="card">
      <div class="kicker">What the AI does</div>
      <ul class="tick">
        <li>Understands the farmer's Hindi, Hinglish or English (Amazon Transcribe, Bedrock).</li>
        <li>Picks one of seven tools: status, advance, file, explain, contest, call-back, fields.</li>
        <li>Reads the answer aloud in Hindi (Amazon Polly).</li>
      </ul>
    </div>
    <div class="card">
      <div class="kicker">What only code and people do</div>
      <ul class="tick cross">
        <li>Decide a claim: fixed rules in <code>rules.py</code>, thresholds in one file, 130+ tests.</li>
        <li>Say what was decided: the farmer hears text built from the decision record, not the model's words.</li>
        <li>Confirm a burn, recover money, fine or file a case: the village officer.</li>
      </ul>
    </div>
  </section>

  ${stats ? `<section class="section"><div class="kicker">Live from this deployment</div>
    <div class="grid g3">
      <div class="card stat"><div class="big">${stats.claims}</div><p>claims checked</p></div>
      <div class="card stat green"><div class="big">${stats.advances_paid}</div><p>advances paid (${"₹" + stats.advance_amount.toLocaleString("en-IN")})</p></div>
      <div class="card stat straw"><div class="big">${(stats.by_status.needs_review || 0) + (stats.by_status.possible_burn || 0)}</div><p>with the officer now</p></div>
    </div></section>` : ""}

  <section class="section card">
    <div class="kicker">Limits, stated plainly</div>
    <p class="small">Field boundaries are hand-drawn samples; there is no public cadastral map. Labels are one person's
      reading of 20 m images, not site visits, and only ${n.burnt_labels} plots were burnt. Satellites track fields, not
      people. Fields under about an acre are too small and go to the officer. The trial's effect on burning is the
      trial's result, not ours. Recovering an advance is administratively hard; we only make it evidence-backed.</p>
  </section>`;
}
