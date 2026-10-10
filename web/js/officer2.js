// Officer desk: the claims the rules could not settle. Each case shows the field's pictures (colour and infrared),
// its plant signal, what the system read, the farmer's appeal, where the money stands, and the officer's decision.
// Names and money appear only here.
import { $, $$, esc, icon, rupees, store, initialLang, setupHeader, fmtDate, kindOf, getJSON, drawCut, evidenceViewer, countUp, signalChart, smokeKg } from "./shared.js";

const T = {
  en: {
    explore: "Explore", officer: "Officer", farmer: "Farmer",
    signinTitle: "Officer sign-in", signinNote: "Village officers see names, money and the review queue. The public map does not.",
    officerId: "Officer ID", pin: "PIN", signin: "Sign in", demoPin: "PIN: 2468 · cases reset daily at 5 am IST", wrongPin: "That PIN is not right.", signout: "Sign out",
    tabs: { todo: "To decide", done: "Decided", all: "All" },
    waiting: (n) => (n === 1 ? "case waiting for you" : "cases waiting for you"), settled: (m) => `of ${m} claims; the rules settled the rest`,
    chip: { possible_burn: "Possible burn", needs_review: "Unclear", officer_approved: "Approved", officer_confirmed_burnt: "Burn confirmed",
      auto_approved: "Clean", submitted: "Checking", appealed: "Appealed" },
    atStake: (x) => `${rupees(x)} advance`, noAdv: "no advance",
    reasonTitle: { possible_burn: "Burn signature found", needs_review: "Not clear from orbit", auto_approved: "No burn found" },
    facts: { clear: "clear images", fires: "fire alerts nearby", last: "last season", smokeOut: "PM2.5 released, est.", smokeSaved: "PM2.5 avoided, est." },
    lastV: { auto_approved: "clean", possible_burn: "burn", needs_review: "unclear" },
    appealBy: (n) => `${n} appealed`,
    flowTitle: "Where the money stands",
    flow: { advance: "Advance", check: "Satellite", decision: "Officer", money: "Balance" },
    fv: {
      advPaid: (x) => `+${rupees(x)} paid`, advNone: "none", you: "you decide", approved: "approved", confirmed: "burn confirmed",
      held: (x) => `${rupees(x)} held`, released: (x) => `+${rupees(x)} released`, linkOut: (x) => `${rupees(x)} link sent`,
      repaid: (x) => `${rupees(x)} repaid`, recover: (x) => `${rupees(x)} to recover`, nothing: "nothing due",
    },
    history: "History",
    ev: {
      submitted: "Claim filed", advance_assessed: "2024 checked for the advance", advance_paid: (x) => `Advance of ${rupees(x)} paid`,
      decided: "Satellite check done", appeal: "Farmer appealed", reviewed: (by, v) => `${by} ${v === "approve" ? "approved" : "confirmed the burn"}`,
      balance_released: (x) => `${rupees(x)} released (DBT, simulated)`, recovery_notice: "Recovery notice drafted",
      recovery_link: (x) => `Payment link for ${rupees(x)} sent (Razorpay test)`, advance_recovered: (x) => `${rupees(x)} repaid by the farmer`,
      recovery_cancelled: "Payment link cancelled after the appeal", contest: "Farmer objected on WhatsApp", appeal_whatsapp: "Farmer appealed on WhatsApp", callback_requested: "Farmer asked for a call",
    },
    decide: "Your decision", note: "What you saw or checked on the ground",
    approve: (x) => `Approve · release ${rupees(x)}`, approveNo: "Approve", confirm: "Confirm burn",
    needNote: "Write what you saw or checked before confirming a burn.",
    stamp: { officer_approved: "Approved", officer_confirmed_burnt: "Burn confirmed" }, by: (id, at) => `${id} · ${at}`,
    notice: "Recovery notice", paylink: "Payment link", payWait: "Waiting for the farmer to pay", payDone: (x) => `${rupees(x)} received · case closed`,
    steps: { reviewed: "Decision recorded", recovery_notice: "Recovery notice drafted", recovery_link: "Payment link created",
      balance_released: "Balance released to the farmer", farmer_told: "Farmer told in the app and on WhatsApp" },
    colour: "Colour", infrared: "Infrared", irNote: "Burnt ground shows maroon, wet soil dark blue.", irWait: "Infrared frames come with the satellite check.",
    signal: "Plant signal (NBR) through the season: a burn drops it below zero",
    empty: "Nothing waiting. The rules settled every claim.", acres: "acres", scheme: (st) => `${st === "HR" ? "Haryana" : "Punjab"} · ₹1,000 an acre, half before harvest`,
  },
  hi: {
    explore: "देखें", officer: "अधिकारी", farmer: "किसान",
    signinTitle: "अधिकारी साइन-इन", signinNote: "नाम, राशि और जाँच की सूची सिर्फ़ ग्राम अधिकारी देखते हैं। सार्वजनिक नक्शे पर ये नहीं दिखते।",
    officerId: "अधिकारी आईडी", pin: "पिन", signin: "साइन-इन करें", demoPin: "पिन: 2468 · मामले रोज़ सुबह 5 बजे नए होते हैं", wrongPin: "पिन सही नहीं है।", signout: "साइन-आउट",
    tabs: { todo: "फ़ैसला बाकी", done: "तय", all: "सभी" },
    waiting: () => "मामले आपके फ़ैसले के लिए", settled: (m) => `${m} दावों में से; बाकी नियमों ने तय किए`,
    chip: { possible_burn: "जलने की आशंका", needs_review: "साफ़ नहीं", officer_approved: "मंज़ूर", officer_confirmed_burnt: "जलना पक्का",
      auto_approved: "साफ़", submitted: "जाँच जारी", appealed: "अपील" },
    atStake: (x) => `${rupees(x)} अग्रिम`, noAdv: "अग्रिम नहीं",
    reasonTitle: { possible_burn: "जलने का निशान मिला", needs_review: "उपग्रह से साफ़ नहीं", auto_approved: "जलना नहीं मिला" },
    facts: { clear: "साफ़ तस्वीरें", fires: "पास में आग अलर्ट", last: "पिछला सीज़न", smokeOut: "PM2.5 निकला, अनुमान", smokeSaved: "PM2.5 बचा, अनुमान" },
    lastV: { auto_approved: "साफ़", possible_burn: "जला", needs_review: "साफ़ नहीं" },
    appealBy: (n) => `${n} की अपील`,
    flowTitle: "राशि कहाँ है",
    flow: { advance: "अग्रिम", check: "उपग्रह", decision: "अधिकारी", money: "बाकी राशि" },
    fv: {
      advPaid: (x) => `+${rupees(x)} दिया`, advNone: "नहीं", you: "आप तय करें", approved: "मंज़ूर", confirmed: "जलना पक्का",
      held: (x) => `${rupees(x)} रुकी`, released: (x) => `+${rupees(x)} भेजी`, linkOut: (x) => `${rupees(x)} का लिंक भेजा`,
      repaid: (x) => `${rupees(x)} लौटाए`, recover: (x) => `${rupees(x)} वसूलने हैं`, nothing: "कुछ देय नहीं",
    },
    history: "इतिहास",
    ev: {
      submitted: "दावा दर्ज", advance_assessed: "अग्रिम के लिए 2024 जाँचा", advance_paid: (x) => `${rupees(x)} अग्रिम दिया`,
      decided: "उपग्रह जाँच पूरी", appeal: "किसान ने अपील की", reviewed: (by, v) => `${by} ने ${v === "approve" ? "मंज़ूर किया" : "जलना पक्का किया"}`,
      balance_released: (x) => `${rupees(x)} भेजे (DBT, नकली)`, recovery_notice: "वसूली नोटिस बना",
      recovery_link: (x) => `${rupees(x)} का भुगतान लिंक भेजा (Razorpay टेस्ट)`, advance_recovered: (x) => `किसान ने ${rupees(x)} लौटाए`,
      recovery_cancelled: "अपील के बाद भुगतान लिंक रद्द", contest: "किसान ने WhatsApp पर आपत्ति की", appeal_whatsapp: "किसान ने WhatsApp पर अपील की", callback_requested: "किसान ने फ़ोन माँगा",
    },
    decide: "आपका फ़ैसला", note: "आपने खेत पर क्या देखा या जाँचा",
    approve: (x) => `मंज़ूर करें · ${rupees(x)} भेजें`, approveNo: "मंज़ूर करें", confirm: "जलना पक्का करें",
    needNote: "जलना पक्का करने से पहले लिखें कि आपने क्या देखा या जाँचा।",
    stamp: { officer_approved: "मंज़ूर", officer_confirmed_burnt: "जलना पक्का" }, by: (id, at) => `${id} · ${at}`,
    notice: "वसूली नोटिस", paylink: "भुगतान लिंक", payWait: "किसान के भुगतान का इंतज़ार", payDone: (x) => `${rupees(x)} मिले · मामला बंद`,
    steps: { reviewed: "फ़ैसला दर्ज", recovery_notice: "वसूली नोटिस का मसौदा बना", recovery_link: "भुगतान लिंक बना",
      balance_released: "बाकी राशि किसान को भेजी", farmer_told: "किसान को ऐप और WhatsApp पर बताया" },
    colour: "रंगीन", infrared: "इन्फ्रारेड", irNote: "जली ज़मीन मैरून दिखती है, गीली मिट्टी गहरी नीली।", irWait: "इन्फ्रारेड तस्वीरें उपग्रह जाँच के साथ आती हैं।",
    signal: "सीज़न भर पौधों का संकेत (NBR): जलने पर यह शून्य से नीचे गिरता है",
    empty: "कुछ बाकी नहीं। नियमों ने हर दावा तय कर दिया।", acres: "एकड़", scheme: (st) => `${st === "HR" ? "हरियाणा" : "पंजाब"} · ₹1,000 प्रति एकड़, आधा कटाई से पहले`,
  },
};
// officers in both states read Hindi or English; the Punjabi and Haryanvi choices show the Hindi desk
const pick = (l) => (l === "en" ? "en" : "hi");
let lang = initialLang("en");
const t = () => T[pick(lang)];

const S = { claims: [], fields: {}, windows: [], tab: "todo", sel: null, detail: null, officer: store.get("saakshi-officer", sessionStorage), pin: store.get("saakshi-pin", sessionStorage) };

function labelText() { $$("[data-t]").forEach((el) => { const v = t()[el.dataset.t]; if (typeof v === "string") el.textContent = v; }); }
const name = (c) => (lang === "en" ? c.farmer_name : c.farmer_name_hi || c.farmer_name);
const fieldLabel = (c) => (lang === "en" ? c.field_name : c.field_name_hi || c.field_name);
const village = (c) => { const f = S.fields[c.field_id]; return f ? (lang === "en" ? f.village : f.village_hi || f.village) : c.village; };
const isOpen = (c) => c.status === "possible_burn" || c.status === "needs_review";
const chipKey = (c) => (c.appeal && isOpen(c) ? "appealed" : c.status);
const chipCls = (c) => (chipKey(c) === "appealed" ? "appeal" : kindOf(c.status));
const advPaid = (c) => (c.advance?.status === "paid" ? c.advance.amount : 0);
const burnIndex = (c) => { const d = c.decision?.burn_date; return d ? S.windows.findIndex((w) => w.start <= d && d <= w.end) : -1; };

// ---- sign-in ----
async function checkPin(pin) { return (await fetch("/api/officer/check", { headers: { "X-Officer-Pin": pin } })).ok; }
function showSignin() {
  $("#signin").hidden = false;
  $("#oid").value = S.officer || "";
  $("#signin-form").onsubmit = async (e) => {
    e.preventDefault();
    const oid = $("#oid").value.trim(), pin = $("#pin").value;
    if (!(await checkPin(pin))) { $("#signin-err").textContent = t().wrongPin; $("#signin-err").hidden = false; return; }
    S.officer = oid; S.pin = pin;
    store.set("saakshi-officer", oid, sessionStorage);
    store.set("saakshi-pin", pin, sessionStorage);
    $("#signin").hidden = true;
    load();
  };
}

// ---- queue: one card per case, with the field on its key date ----
function renderQueue(animate = false) {
  const L = t(), open = S.claims.filter(isOpen);
  const list = S.tab === "todo" ? open.sort((a, b) => (b.appeal ? 1 : 0) - (a.appeal ? 1 : 0) || (a.status === "possible_burn" ? -1 : 1))
    : S.tab === "done" ? S.claims.filter((c) => c.review) : S.claims;
  $("#queue").innerHTML = `<div class="q-head"><div class="q-who"><span class="avatar">${esc((S.officer || "?").slice(0, 2).toUpperCase())}</span><b>${esc(S.officer)}</b><button class="link" id="signout">${esc(L.signout)}</button></div>
      <div class="q-count"><b id="q-n">${open.length}</b><span>${esc(L.waiting(open.length))}<small>${esc(L.settled(S.claims.length))}</small></span></div>
      <div class="tabs">${Object.entries(L.tabs).map(([k, v]) => `<button data-tab="${k}" class="${S.tab === k ? "on" : ""}">${esc(v)}</button>`).join("")}</div></div>
    <ul class="q-list ${animate ? "enter" : ""}">${list.length ? list.map((c, i) => `<li style="--i:${i}"><button data-id="${c.id}" class="qc ${chipCls(c)} ${S.sel === c.id ? "on" : ""}">
        <canvas class="qthumb" data-field="${c.field_id}" data-w="${burnIndex(c)}"></canvas>
        <span class="q-main"><b>${esc(name(c))}</b><small>${esc(fieldLabel(c))} · ${esc(village(c))}</small>
          <span class="q-meta"><em class="chip ${chipCls(c)}">${esc(L.chip[chipKey(c)] || c.status)}</em><small>${esc(advPaid(c) ? L.atStake(advPaid(c)) : L.noAdv)}</small></span></span></button></li>`).join("")
      : `<li class="empty">${esc(L.empty)}</li>`}</ul>`;
  if (animate) countUp($("#q-n"), open.length);
  $$("#queue canvas.qthumb").forEach((cv) => {
    const f = S.fields[cv.dataset.field];
    const w = Number(cv.dataset.w) >= 0 ? S.windows[Number(cv.dataset.w)] : S.windows.at(-1);
    if (f && w) drawCut(cv, w.id, f.geometry, 96, 64, 1);
  });
  $$("#queue [data-tab]").forEach((b) => { b.onclick = () => { S.tab = b.dataset.tab; renderQueue(true); }; });
  $$("#queue [data-id]").forEach((b) => { b.onclick = () => select(b.dataset.id); });
  $("#signout").onclick = () => { store.del("saakshi-pin", sessionStorage); S.pin = null; showSignin(); };
}

async function select(id) {
  S.sel = id;
  $$("#queue [data-id]").forEach((b) => b.classList.toggle("on", b.dataset.id === id));
  S.detail = await getJSON(`/api/claims/${id}`);
  renderCase();
}

// ---- where the money stands: advance → satellite → officer → balance ----
function flow(c) {
  const L = t(), F = L.fv, st = c.settlement || {}, rec = c.recovery || {}, adv = advPaid(c);
  const k = kindOf(c.decision?.outcome || c.status);
  const balance = (st.total || 0) - adv;
  const decided = c.status === "officer_approved" || c.status === "officer_confirmed_burnt" || c.status === "auto_approved";
  const money = st.state === "balance_due" ? { v: F.released(st.balance), cls: "in" }
    : st.state === "recover_advance" ? (rec.status === "paid" ? { v: F.repaid(st.recover), cls: "out done" } : rec.status === "issued" ? { v: F.linkOut(st.recover), cls: "out wait" } : { v: F.recover(st.recover), cls: "out" })
    : st.state === "not_payable" ? { v: F.nothing, cls: "" } : { v: F.held(balance), cls: "held wait" };
  const nodes = [
    { label: L.flow.advance, v: adv ? F.advPaid(adv) : F.advNone, cls: adv ? "in" : "", done: true },
    { label: L.flow.check, v: L.chip[c.decision?.outcome] || "—", cls: k, done: !!c.decision },
    { label: L.flow.decision, v: c.status === "officer_approved" ? F.approved : c.status === "officer_confirmed_burnt" ? F.confirmed : c.status === "auto_approved" ? L.chip.auto_approved : F.you, cls: c.status === "officer_confirmed_burnt" ? "burn" : decided ? "clean" : "wait", done: decided },
    { label: L.flow.money, v: money.v, cls: money.cls, done: !money.cls.includes("wait") },
  ];
  const reached = nodes.filter((n) => n.done).length;
  return `<section class="flow" style="--reached:${Math.max(0, reached - 1)}"><h3>${esc(L.flowTitle)}</h3>
    <ol class="flow-line"><i class="rail"><i class="fill"></i><i class="coin"></i></i>${nodes.map((n, i) => `<li class="${n.cls} ${n.done ? "done" : ""}" style="--i:${i}">
      <span class="node"></span><small>${esc(n.label)}</small><b>${esc(n.v)}</b></li>`).join("")}</ol>
    <p class="cap">${esc(L.scheme(c.state_code))}</p></section>`;
}

function history(c) {
  const L = t(), E = L.ev;
  const rows = (c.events || []).map((e) => {
    const f = E[e.type];
    if (!f) return null;
    const text = typeof f === "function" ? (e.type === "reviewed" ? f(e.by, e.verdict) : f(e.amount || 0)) : f;
    return `<li class="h-${e.type}"><span class="w">${esc(fmtDate(e.at, lang))}</span><span>${esc(text)}${e.note ? `<small>“${esc(e.note)}”</small>` : ""}</span></li>`;
  }).filter(Boolean);
  return rows.length ? `<section class="hist"><h3>${esc(L.history)}</h3><ol>${rows.join("")}</ol></section>` : "";
}

function renderCase(flash = false) {
  const L = t(), c = S.detail, f = S.fields[c.field_id], d = c.decision || {}, k = kindOf(d.outcome || c.status);
  const balance = (c.settlement?.total || Math.round((c.acres || 0) * 1000)) - advPaid(c);
  const prev = c.advance?.prev_outcome;
  $("#case").innerHTML = `<div class="case-in">
    <header class="c-head"><div><h2>${esc(name(c))}</h2><p>${esc(fieldLabel(c))} · ${c.acres} ${esc(L.acres)} · ${esc(village(c))}</p></div>
      <em class="chip big ${chipCls(c)}">${esc(L.chip[chipKey(c)] || c.status)}</em></header>
    <div class="c-grid">
      <div class="c-left card-s"><div id="ev"></div>${signalChart(c.series, d.burn_date, lang, L)}</div>
      <div class="c-right">
        <section class="verdict ${k}"><span class="ic">${icon(k === "clean" ? "i-check" : k === "burn" ? "i-flame" : "i-eye")}</span>
          <div><b>${esc(L.reasonTitle[d.outcome] || L.chip[d.outcome] || "")}</b>${d.burn_date ? `<small>${esc(fmtDate(d.burn_date, lang, true))}</small>` : ""}</div></section>
        <div class="facts3">
          <div><b id="f-clear">${(d.clear_dates || []).length}</b><small>${esc(L.facts.clear)}</small></div>
          <div><b>${d.fires_nearby || 0}</b><small>${esc(L.facts.fires)}</small></div>
          <div><b class="${kindOf(prev)}">${esc(L.lastV[prev] || "—")}</b><small>${esc(L.facts.last)}</small></div>
          <div title="2.6 t straw an acre, 80% burnt, ~9 kg PM2.5 a tonne"><b class="smoke">≈ ${smokeKg(c.acres)} kg</b><small>${esc(k === "burn" || c.status === "officer_confirmed_burnt" ? L.facts.smokeOut : L.facts.smokeSaved)}</small></div></div>
        ${c.appeal ? `<section class="bubble"><span class="avatar farmer">${esc((c.farmer_name || "?").slice(0, 1))}</span><div><small>${esc(L.appealBy(name(c)))} · ${esc(fmtDate(c.appeal.at, lang))}</small><p>${esc(c.appeal.note)}</p></div></section>` : ""}
        ${flow(c)}
        ${isOpen(c) ? `<section class="decide"><h3>${esc(L.decide)}</h3><textarea id="note" rows="2" placeholder="${esc(L.note)}"></textarea><p class="err" id="derr" hidden></p>
          <div class="d-btns"><button class="btn primary" id="approve">${icon("i-check")}<span>${esc(balance > 0 ? L.approve(balance) : L.approveNo)}</span></button>
          <button class="btn danger" id="confirm">${icon("i-flame")}<span>${esc(L.confirm)}</span></button></div></section>`
        : c.review ? `<section class="decided ${c.status === "officer_confirmed_burnt" ? "burn" : "clean"} ${flash ? "land" : ""}"><span class="ic">${icon(c.status === "officer_confirmed_burnt" ? "i-flame" : "i-check")}</span>
          <div class="dtx"><b>${esc(L.stamp[c.status] || "")}</b><small>${esc(L.by(c.review.officer_id, fmtDate(c.review.at, lang)))}${c.review.note ? ` · “${esc(c.review.note)}”` : ""}</small>
          ${c.recovery?.status === "issued" ? `<span class="paystate wait"><i></i>${esc(L.payWait)}</span>` : c.recovery?.status === "paid" ? `<span class="paystate done ${S.justPaid ? "land" : ""}">${icon("i-check")}${esc(L.payDone(c.recovery.amount))}</span>` : ""}</div>
          <div class="d-links">${c.notice_url ? `<a class="btn ghost small" href="${esc(c.notice_url)}" target="_blank" rel="noopener">${esc(L.notice)}</a>` : ""}
          ${c.recovery?.status === "issued" ? `<a class="btn ghost small" href="${esc(c.recovery.url)}" target="_blank" rel="noopener">${esc(L.paylink)}</a>` : ""}</div></section>` : ""}
        ${history(c)}
      </div></div></div>`;
  if (f) evidenceViewer($("#ev"), { windows: S.windows, geom: f.geometry, burnIndex: burnIndex(c), lang,
    ir: c.evidence_url ? { url: c.evidence_url, dates: c.evidence_dates || null, burn: d.burn_date } : null, labels: L });
  if (flash) $(".flow")?.classList.add("moving");
  S.justPaid = false;
  watchPayment();
  $("#approve")?.addEventListener("click", () => decide("approve"));
  $("#confirm")?.addEventListener("click", () => decide("confirm_burnt"));
}

async function decide(verdict) {
  const note = $("#note").value.trim();
  if (verdict === "confirm_burnt" && !note) { $("#derr").textContent = t().needNote; $("#derr").hidden = false; $("#note").focus(); return; }
  $$(".d-btns button").forEach((b) => { b.disabled = true; });
  try {
    await getJSON(`/api/claims/${S.sel}/review`, { method: "POST", headers: { "Content-Type": "application/json", "X-Officer-Pin": S.pin },
      body: JSON.stringify({ officer_id: S.officer, verdict, note }) });
  } catch (e) {
    $("#derr").textContent = e.message; $("#derr").hidden = false;
    $$(".d-btns button").forEach((b) => { b.disabled = false; });
    if (/PIN/.test(e.message)) showSignin();
    return;
  }
  await followSteps(verdict);
  S.claims = await getJSON("/api/claims");
  S.detail = await getJSON(`/api/claims/${S.sel}`);
  renderQueue();
  renderCase(true);
}

// after a decision the server finishes the rest in the background; tick each step off as its event lands
async function followSteps(verdict) {
  const L = t(), id = S.sel;
  const keys = verdict === "confirm_burnt" ? ["reviewed", "recovery_notice", "recovery_link", "farmer_told"] : ["reviewed", "balance_released", "farmer_told"];
  const box = $(".decide");
  if (!box) return;
  box.classList.add("working");
  box.innerHTML = `<h3>${esc(L.decide)}</h3><ol class="steps">${keys.map((k) => `<li data-k="${k}"><span class="tick"></span>${esc(L.steps[k])}</li>`).join("")}</ol>`;
  for (let i = 0; i < 40; i++) {
    const c = await getJSON(`/api/claims/${id}`).catch(() => null);
    const seen = new Set((c?.events || []).map((e) => e.type));
    if (c?.status === "officer_approved" && c.settlement?.state !== "balance_due") seen.add("balance_released");  // nothing left to pay
    const finished = seen.has("farmer_told");
    $$(".steps li", box).forEach((li) => {
      const k = li.dataset.k;
      li.classList.toggle("done", seen.has(k));
      if (finished && !seen.has(k)) li.classList.add("skip");  // e.g. no payment link in a demo without Razorpay
    });
    if (finished) { await new Promise((r) => setTimeout(r, 900)); return; }
    await new Promise((r) => setTimeout(r, 1200));
  }
}

// a payment link is open: notice the farmer paying without a refresh. Every third look also asks Razorpay,
// in case the payer closed the page before coming back.
let payTimer = null, payN = 0;
function watchPayment(now = false) {
  clearTimeout(payTimer);
  const id = S.detail?.id;
  if (S.detail?.recovery?.status !== "issued") return;
  payTimer = setTimeout(async () => {
    if (S.detail?.id !== id) return;
    if (++payN % 3 === 0) await getJSON(`/api/claims/${id}/recovery/check`, { method: "POST" }).catch(() => null);
    const c = await getJSON(`/api/claims/${id}`).catch(() => null);
    if (S.detail?.id !== id) return;
    if (c?.recovery?.status === "paid") {
      S.detail = c; S.claims = await getJSON("/api/claims");
      renderQueue(); renderCase(); S.justPaid = true; renderCase();
      return;
    }
    watchPayment();
  }, now ? 0 : 4000);
}
document.addEventListener("visibilitychange", () => { if (!document.hidden) watchPayment(true); });

async function load() {
  const [claims, fields, mf] = await Promise.all([getJSON("/api/claims"), getJSON("/api/fields"), getJSON("/tiles/manifest.json")]);
  S.claims = claims; S.windows = mf.windows;
  fields.forEach((f) => { S.fields[f.id] = f; });
  renderQueue(true);
  const first = S.claims.find(isOpen) || S.claims[0];
  if (first) select(first.id); else $("#case").innerHTML = `<p class="empty">${esc(t().empty)}</p>`;
}

setupHeader(lang, (l) => { lang = l; labelText(); renderQueue(); if (S.detail) renderCase(); });
labelText();
(async () => { if (S.pin && (await checkPin(S.pin))) load(); else showSignin(); })();
