import { $, $$, api, badge, chart, esc, evidence, moneyRow, playAudio, rupees, waitForClaim } from "./ui.js";

const PIN = { "X-Officer-Pin": "2468" };
const PREV = {
  auto_approved: `<span class="badge b-ok">clean</span>`, officer_approved: `<span class="badge b-ok">clean</span>`,
  needs_review: `<span class="badge b-warn">unclear</span>`, possible_burn: `<span class="badge b-bad">burn-like</span>`,
};
const CAST = { kamlesh: "f-kamlesh", satbir: "f-satbir", baljeet: "f-baljeet" };

const SCENES = [
  { id: "smoke", title: "The smoke", when: "Every November" },
  { id: "advance", title: "Before harvest: the advance", when: "September 2025" },
  { id: "clean", title: "A clean field pays itself", when: "After harvest" },
  { id: "alert", title: "A fire alert near Satbir", when: "November" },
  { id: "missed", title: "A burn the alerts missed", when: "6 November" },
  { id: "officer", title: "The officer decides", when: "December" },
  { id: "voice", title: "Satbir asks, in Hindi", when: "December" },
  { id: "numbers", title: "Does it work?", when: "Measured" },
];

export async function story(app) {
  app.innerHTML = `
    <h1 style="font-size:30px">One season in west Kaithal</h1>
    <p class="muted" style="margin-top:-6px">Real fields, real 2024 and 2025 Sentinel-2 images, the live system. Each step runs it.</p>
    <div class="story-stage">
      <div class="story-steps" id="steps">${SCENES.map((s, i) => `<button data-i="${i}"><span class="small muted">${esc(s.when)}</span><br>${i + 1}. ${esc(s.title)}</button>`).join("")}</div>
      <div class="card scene" id="scene"></div>
    </div>`;
  const state = { i: 0, claims: {}, stop: false };
  $$("#steps button").forEach((b) => (b.onclick = () => go(+b.dataset.i)));

  async function go(i) {
    state.i = i;
    $$("#steps button").forEach((b, j) => { b.classList.toggle("on", j === i); b.classList.toggle("done", j < i); });
    const s = SCENES[i], el = $("#scene");
    el.innerHTML = `<div class="when">${esc(s.when)}</div><h2>${esc(s.title)}</h2><div id="body"><span class="spinner"></span></div>
      <div class="row" style="margin-top:18px">${i > 0 ? `<button class="btn ghost" id="prev">← Back</button>` : ""}
      ${i < SCENES.length - 1 ? `<button class="btn green" id="next">Next →</button>` : `<a class="btn green" href="#/">Done</a>`}</div>`;
    if ($("#prev")) $("#prev").onclick = () => go(i - 1);
    if ($("#next")) $("#next").onclick = () => go(i + 1);
    try { await RENDER[s.id]($("#body"), state); } catch (e) { $("#body").innerHTML = `<p class="err">${esc(e.message)}</p>`; }
  }

  go(0);
  return () => { state.stop = true; };
}

async function ensureClaims(state, body) {
  const all = await api("/api/claims");
  for (const [who, fid] of Object.entries(CAST)) {
    let c = all.find((x) => x.field_id === fid);
    if (!c) c = await api("/api/claims", { method: "POST", body: JSON.stringify({ field_id: fid }) });
    state.claims[who] = c.id;
  }
  if (body) body.innerHTML = `<p><span class="spinner"></span> Reading last season's and this season's Sentinel-2 images for three fields…</p>`;
  const out = {};
  for (const [who, id] of Object.entries(state.claims)) out[who] = await waitForClaim(id);
  return out;
}

const RENDER = {
  async smoke(body) {
    const n = await fetch("data/numbers.json").then((r) => r.json());
    body.innerHTML = `
      <p>On the worst day of November 2024, farm fires were <b>${n.context.delhi_pm25_share_peak}%</b> of Delhi's PM2.5.
        Haryana fights it with two levers, and both are broken.</p>
      <div class="grid g2">
        <div class="card" style="box-shadow:none"><h3>The stick</h3><p>Thermal fire alerts trigger a <b>red entry</b>: no MSP sale
          for two seasons, an FIR, and up to ₹30,000 in compensation. In our measurement the alerts flagged
          <b>${n.firms.clean_flagged}%</b> of clean fields and caught <b>${n.firms.burns_caught}%</b> of burns.</p></div>
        <div class="card" style="box-shadow:none"><h3>The carrot</h3><p>₹1,000 an acre for not burning, paid <b>after</b> a slow
          manual check. A randomised trial in Punjab found that only paying upfront changed behaviour:
          <b>+${n.context.upfront_trial_gain_pp} points</b> compliance.</p></div>
      </div>
      <p style="margin-top:12px">Paying upfront needs verification that is cheap, fast and fair for every field. Follow three farmers through one season.</p>`;
  },

  async advance(body, state) {
    const c = await ensureClaims(state, body);
    const row = (who, label) => {
      const a = c[who].advance || {};
      return `<tr><td><b>${esc(c[who].farmer_name)}</b><br><span class="small muted">${esc(label)}</span></td>
        <td>${esc(a.prev_season)}: ${PREV[a.prev_outcome] || esc(a.prev_outcome)}</td>
        <td class="num">${a.eligible ? `<span style="color:var(--green)">${rupees(a.amount)} paid</span>` : `<span class="muted">no advance</span>`}</td></tr>`;
    };
    body.innerHTML = `<p>Before harvest, each registered field is checked against <b>last season's</b> images. Clean last season:
      half the incentive now, when it can pay for a baler or a happy seeder.</p>
      <table class="plain"><tr><th>Farmer</th><th>Last season</th><th>Advance</th></tr>
      ${row("kamlesh", "3.8 acres")}${row("baljeet", "5.7 acres")}${row("satbir", "2.7 acres")}</table>
      <p class="small muted" style="margin-top:10px">Satbir's field had a partly dark patch in 2024, so no advance this year.
        A clean 2025 earns it back next year.</p>`;
  },

  async clean(body, state) {
    const c = (await ensureClaims(state)).kamlesh;
    body.innerHTML = `<p>After harvest, every clear Sentinel-2 image of Kamlesh Devi's field from 1 Oct to 30 Nov is read straight
      from the AWS Open Data registry. No burn signal: approved with no officer involved.</p>
      <div class="row">${badge(c.status)}</div>
      <p lang="hi" style="font-size:18px;margin:10px 0 4px">${esc(c.message.hi)}</p>
      <button class="play" id="l1">▶ सुनें</button>
      <div style="margin-top:12px">${moneyRow(c)}</div>${chart(c.series)}`;
    $("#l1").onclick = () => playAudio(c.audio_url, c.message.hi);
  },

  async alert(body, state) {
    const c = (await ensureClaims(state)).satbir;
    const f = (c.fires || [])[0];
    body.innerHTML = `<p>A NASA FIRMS fire point was detected ${f ? `on ${esc(f.date)}` : ""} within 375 m of Satbir Singh's field.
      Today that alone can mean a red entry. The satellite images say otherwise: his field stays tan all season.
      The dark patch on 7 November is a neighbour's.</p>
      ${evidence(c)}
      <p style="margin-top:12px">${badge(c.status)} The rules cannot auto-approve with a fire point nearby, so it goes to the officer with this evidence, not to a penalty.</p>`;
  },

  async missed(body, state) {
    const c = (await ensureClaims(state)).baljeet;
    body.innerHTML = `<p>Baljeet Singh received an advance for a clean 2024. In 2025 his field shows the burn signature on
      <b>${esc(c.decision.burn_date)}</b>: near-infrared falls in one step and most of the field turns near-black.
      The nearest FIRMS fire point is almost a kilometre away; the thermal alerts missed it.</p>
      ${chart(c.series, c.decision.burn_date)}${evidence(c)}
      <p style="margin-top:12px">${badge(c.status)} Never a final decision: the officer has to confirm.</p>`;
  },

  async officer(body, state) {
    const c = await ensureClaims(state);
    const sat = c.satbir, bal = c.baljeet;
    body.innerHTML = `<p>The officer sees only the cases the rules could not settle. Two here.</p>
      <div class="grid g2">
        <div class="card" style="box-shadow:none"><b>Satbir Singh</b><p class="small">FIRMS point nearby, field clean in every image.</p>
          <div id="s-act">${sat.status === "needs_review" ? `<button class="btn green" id="ok">Approve claim</button>` : badge(sat.status)}</div></div>
        <div class="card" style="box-shadow:none"><b>Baljeet Singh</b><p class="small">Burn scar on ${esc(bal.decision.burn_date)}, advance of ${rupees((bal.advance || {}).amount)} paid.</p>
          <div id="b-act">${bal.status === "possible_burn" ? `<button class="btn ember" id="burn">Confirm burn</button>` : badge(bal.status)}</div></div>
      </div><div id="out" style="margin-top:14px"></div>`;
    const act = async (id, verdict, note) => {
      const r = await api(`/api/claims/${id}/review`, { method: "POST", headers: PIN,
        body: JSON.stringify({ officer_id: "VO-KTL-07", verdict, note }) });
      return api(`/api/claims/${r.id}`);
    };
    const show = (x) => {
      if (x.notice_url) $("#out").innerHTML = `<p><b>Recovery notice drafted</b> for the officer to sign, with the evidence. Fines, red entries and cases stay separate decisions.</p>
        <iframe class="notice-frame" src="${esc(x.notice_url)}" title="Recovery notice draft"></iframe>`;
    };
    if ($("#ok")) $("#ok").onclick = async () => { const x = await act(sat.id, "approve", "Fire point is a neighbour's field; Satbir's field clean in all images."); $("#s-act").innerHTML = badge(x.status) + `<div style="margin-top:8px">${moneyRow(x)}</div>`; };
    if ($("#burn")) $("#burn").onclick = async () => { const x = await act(bal.id, "confirm_burnt", "Site visit: burnt stubble on the field."); $("#b-act").innerHTML = badge(x.status); show(x); };
    if (bal.notice_url) show(bal);
  },

  async voice(body, state) {
    await ensureClaims(state);
    body.innerHTML = `<p>Satbir does not open a dashboard. He asks the app in Hindi. The AI only works out what he is asking;
      the answer he hears is built from the decision record.</p>
      <div class="bubble me" style="justify-self:start">मेरा दावा कहाँ तक पहुँचा?</div><div id="ans" style="margin-top:10px"><span class="spinner"></span></div>`;
    const r = await api("/api/agent", { method: "POST", body: JSON.stringify({ farmer_id: CAST.satbir, text: "मेरा दावा कहाँ तक पहुँचा?" }) });
    $("#ans").innerHTML = `<div class="bubble bot"><div class="hi" lang="hi">${esc(r.hi)}</div><div class="en">${esc(r.en)}</div>
      <div class="meta"><button class="play" id="pl">▶ सुनें</button><span>${r.mode === "bedrock" ? "Amazon Bedrock + Polly" : "Rule-based understanding + Polly"}</span></div></div>`;
    $("#pl").onclick = () => playAudio(r.audio_url, r.hi);
    playAudio(r.audio_url, r.hi);
  },

  async numbers(body) {
    const n = await fetch("data/numbers.json").then((r) => r.json());
    body.innerHTML = `<table class="plain">
      <tr><th></th><th>Satellite check</th><th>Fire alerts alone</th></tr>
      <tr><td>Clean fields flagged</td><td class="num" style="color:var(--green)">${n.rules.clean_flagged}%</td><td class="num" style="color:var(--ember)">${n.firms.clean_flagged}%</td></tr>
      <tr><td>Burns caught</td><td class="num">all labelled burns sent to the officer</td><td class="num">${n.firms.burns_caught}%</td></tr>
      <tr><td>Burnt fields approved automatically</td><td class="num">${n.rules.burnt_auto_approved}%</td><td>-</td></tr>
      <tr><td>Claims settled without an officer</td><td class="num">${n.rules.auto_approved}%</td><td>-</td></tr></table>
      <p style="margin-top:12px">Advance rule, checked on 2024 vs 2025: fields clean last season burnt at <b>${n.advance.burnt_if_clean_last_year}%</b>,
        others at <b>${n.advance.burnt_if_not_clean_last_year}%</b>. ${n.advance.eligible_share}% of cropland qualified.</p>
      <p class="small muted">${n.labelled_plots} hand-labelled plots, ${n.burnt_labels} burnt, west Kaithal 2025. Full method in the repository.</p>`;
  },
};
