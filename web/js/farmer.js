import { $, advanceBadge, api, badge, chart, esc, evidence, moneyRow, playAudio, rupees, waitForClaim } from "./ui.js";
import { Recorder, browserRecognition } from "./voice.js";

const MIC = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>`;
const CHIPS = ["मेरा दावा कहाँ तक पहुँचा?", "क्या मुझे अग्रिम राशि मिलेगी?", "मुझे दावा दर्ज करना है", "यह फ़ैसला क्यों हुआ?", "फ़ायर अलर्ट गलत है, मैंने पराली नहीं जलाई"];

export async function farmer(app, [fid]) {
  const fields = await api("/api/fields");
  if (!fid) return pick(app, fields);
  const f = fields.find((x) => x.id === fid);
  if (!f) { location.hash = "#/farmer"; return; }
  return home(app, f);
}

function pick(app, fields) {
  app.innerHTML = `
    <div class="phone" style="max-width:860px">
      <h1 lang="hi" style="font-size:32px">आप कौन हैं?</h1>
      <p class="muted">Pick a farmer to see the app as they would. Five real fields in west Kaithal, 2025 season.</p>
      <div class="persona-grid">
        ${fields.map((f) => `<a class="card persona" href="#/farmer/${esc(f.id)}" style="text-decoration:none;color:inherit">
          <div class="name" lang="hi">${esc(f.farmer_hi || f.farmer)}</div>
          <div class="muted">${esc(f.farmer)} · ${esc(f.name)} · ${esc(f.acres)} acres</div></a>`).join("")}
      </div>
    </div>`;
}

async function home(app, f) {
  const cfg = await api("/api/config").catch(() => ({}));
  app.innerHTML = `
    <div class="phone">
      <a href="#/farmer" class="small">← farmers</a>
      <h1 lang="hi" style="font-size:30px;margin-top:6px">नमस्ते ${esc(f.farmer_hi || f.farmer)} जी</h1>
      <p class="muted" style="margin-top:-6px"><span lang="hi">${esc(f.name_hi || f.name)}</span> · ${esc(f.acres)} acres · ${esc(f.village)}</p>

      <div class="card">
        <div class="mic-wrap">
          <button class="mic" id="mic" aria-label="Hold to speak">${MIC}</button>
          <div lang="hi" id="mic-hint" class="muted">दबाकर रखें और बोलें · Hold and speak</div>
        </div>
        <div class="chips">${CHIPS.map((c) => `<button class="chip">${esc(c)}</button>`).join("")}</div>
        <form class="ask" id="ask"><input id="q" lang="hi" placeholder="या यहाँ लिखें / or type here" autocomplete="off"><button class="btn green">पूछें</button></form>
        <div class="convo" id="convo" aria-live="polite"></div>
        <div class="small muted" id="mode"></div>
      </div>

      <h2 lang="hi" style="margin-top:28px;font-size:22px">मेरा दावा · My claim</h2>
      <div id="claim"></div>
    </div>`;

  const convo = $("#convo");
  let busy = false;

  async function ask(payload, shownText) {
    if (busy) return;
    busy = true;
    const mic = $("#mic");
    mic.classList.add("busy");
    if (shownText) convo.insertAdjacentHTML("beforeend", `<div class="bubble me">${esc(shownText)}</div>`);
    try {
      const r = await api("/api/agent", { method: "POST", body: JSON.stringify({ farmer_id: f.id, ...payload }) });
      if (r.transcript) convo.insertAdjacentHTML("beforeend", `<div class="bubble me">${esc(r.transcript)}</div>`);
      const id = "a" + Math.random().toString(36).slice(2);
      convo.insertAdjacentHTML("beforeend", `<div class="bubble bot"><div class="hi" lang="hi">${esc(r.hi)}</div>
        ${r.en ? `<div class="en">${esc(r.en)}</div>` : ""}
        <div class="meta"><button class="play" id="${id}">▶ सुनें</button><span>${esc(modeLabel(r))}</span></div></div>`);
      $(`#${id}`).onclick = () => playAudio(r.audio_url, r.hi);
      playAudio(r.audio_url, r.hi);
      convo.lastElementChild.scrollIntoView({ block: "nearest", behavior: "smooth" });
      if ((r.tools || []).some((t) => ["file_claim", "contest"].includes(t))) refreshClaim();
    } catch (e) {
      convo.insertAdjacentHTML("beforeend", `<div class="bubble bot err">${esc(e.message)}</div>`);
    } finally {
      busy = false;
      mic.classList.remove("busy");
    }
  }

  document.querySelectorAll(".chip").forEach((b) => (b.onclick = () => ask({ text: b.textContent }, b.textContent)));
  $("#ask").onsubmit = (e) => {
    e.preventDefault();
    const t = $("#q").value.trim();
    if (t) { $("#q").value = ""; ask({ text: t }, t); }
  };
  setupMic($("#mic"), cfg, ask);
  $("#mode").textContent = cfg.voice_in ? "Voice: Amazon Transcribe (hi-IN) · Reply: Amazon Polly" : "Voice: browser speech recognition (local demo)";

  let stop = false;
  async function refreshClaim() {
    const all = await api("/api/claims");
    const c = all.filter((x) => x.field_id === f.id).pop();
    const box = $("#claim");
    if (!box) return;
    if (!c) {
      box.innerHTML = `<div class="card"><p lang="hi">अभी कोई दावा दर्ज नहीं है। 2025 सीज़न के लिए पराली न जलाने का दावा दर्ज करें।</p>
        <button class="btn green" id="file">दावा दर्ज करें · File no-burn claim</button></div>`;
      $("#file").onclick = () => ask({ text: "मुझे दावा दर्ज करना है" }, "मुझे दावा दर्ज करना है");
      return;
    }
    render(box, await api(`/api/claims/${c.id}`));
    if (c.status === "submitted") waitForClaim(c.id, (x) => !stop && render(box, x)).catch(() => {});
  }
  refreshClaim();
  return () => { stop = true; };
}

function modeLabel(r) {
  if (r.mode === "bedrock") return "Understood by Amazon Bedrock";
  if (r.mode === "scripted-fallback") return "Rule-based answer (AI model unavailable right now)";
  return "Rule-based understanding";
}

function render(box, c) {
  const m = c.message || { hi: "उपग्रह तस्वीरों की जाँच चल रही है…", en: "Checking satellite images…" };
  const adv = c.advance || null;
  box.innerHTML = `<div class="card">
    <div class="row">${badge(c.status, true)} ${advanceBadge(adv)}</div>
    <p lang="hi" style="font-size:19px;line-height:1.65;margin:12px 0 4px">${esc(m.hi)}</p>
    <p class="muted small">${esc(m.en)}</p>
    <div class="row" style="margin-bottom:12px"><button class="play" id="listen">▶ सुनें · Listen</button>
      ${c.notice_url ? `<a class="small" href="${esc(c.notice_url)}" target="_blank" rel="noopener">Notice (draft)</a>` : ""}</div>
    ${c.settlement ? moneyRow(c) : ""}
    ${adv ? `<p class="small muted" style="margin-top:10px">Advance: based on the ${esc(adv.prev_season)} season (${esc(adv.prev_reason || "")}). ${adv.amount ? rupees(adv.amount) : ""}</p>` : ""}
    ${c.series ? `<details style="margin-top:10px"><summary>Satellite evidence · उपग्रह तस्वीरें</summary>${chart(c.series, c.decision && c.decision.burn_date)}${evidence(c)}</details>` : ""}
  </div>`;
  $("#listen", box).onclick = () => playAudio(c.audio_url, m.hi);
}

function setupMic(btn, cfg, ask) {
  const recognize = browserRecognition();
  let rec = null;
  const hint = $("#mic-hint");
  const down = async (e) => {
    e.preventDefault();
    if (btn.classList.contains("busy")) return;
    if (!cfg.voice_in) {
      if (!recognize) { hint.textContent = "Voice needs Chrome or Edge here. Type instead."; return; }
      btn.classList.add("rec");
      hint.textContent = "सुन रहे हैं… listening";
      try { const t = await recognize(); ask({ text: t }, t); } catch (err) { hint.textContent = "Did not catch that: " + err.message; }
      btn.classList.remove("rec");
      hint.textContent = "दबाकर रखें और बोलें · Hold and speak";
      return;
    }
    try {
      rec = new Recorder();
      await rec.start();
      btn.classList.add("rec");
      hint.textContent = "बोलिए… छोड़ने पर भेजेंगे · release to send";
    } catch (err) { hint.textContent = "Microphone blocked: " + err.message; rec = null; }
  };
  const up = async () => {
    if (!rec) return;
    const r = rec; rec = null;
    btn.classList.remove("rec");
    hint.textContent = "दबाकर रखें और बोलें · Hold and speak";
    const { b64, seconds } = await r.stop();
    if (seconds < 0.6) { hint.textContent = "Hold the button while you speak."; return; }
    ask({ audio_b64: b64 });
  };
  btn.addEventListener("pointerdown", down);
  btn.addEventListener("pointerup", up);
  btn.addEventListener("pointerleave", up);
}
