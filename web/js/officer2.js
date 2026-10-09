// Officer desk: the claims the rules could not settle, with the field's pictures, the system's reading, the
// farmer's appeal, the payment record, and the officer's decision. Names and money appear only here.
import { $, $$, esc, icon, rupees, store, initialLang, setupHeader, fmtDate, filmstrip, kindOf, getJSON } from "./shared.js";

const T = {
  en: {
    explore: "Explore", officer: "Officer", farmer: "Farmer",
    signinTitle: "Officer sign-in", signinNote: "Village officers see names, money and the review queue. The public map does not.",
    officerId: "Officer ID", pin: "PIN", signin: "Sign in", demoPin: "Demo PIN: 2468", wrongPin: "That PIN is not right.", signout: "Sign out",
    tabs: { todo: "To decide", done: "Decided", all: "All claims" },
    summary: (n, m) => `${n} of ${m} claims need you. The rules settled the rest.`,
    chip: { possible_burn: "Possible burn", needs_review: "Unclear", officer_approved: "Approved by you", officer_confirmed_burnt: "Burn confirmed",
      auto_approved: "Approved by the rules", submitted: "Being checked", appealed: "Appealed" },
    atStake: (x) => `${rupees(x)} advance at stake`, noAdv: "No advance paid",
    reading: "What the satellite saw", clear: "Clear images", fires: "Fire alerts within 375 m", none: "none", last: "Last season (2024)",
    lastV: { auto_approved: "Clean", possible_burn: "Possible burn", needs_review: "Unclear" },
    appeal: "The farmer's appeal", infrared: "Infrared view of every clear image (a fresh burn turns dark blue)",
    book: "Payment record", scheme: (st) => `${st === "HR" ? "Haryana" : "Punjab"} · ₹1,000 an acre, half before harvest`,
    when: { before: "Before harvest", after: "After the check", now: "Today" },
    rows: {
      adv: (x) => `Advance paid for a clean 2024`, noadv: "No advance: 2024 was not clearly clean",
      held: "Balance held until you decide", released: "Balance released to the farmer's account",
      recover: "Advance to be repaid; notice drafted", link: "Payment link sent to the farmer (Razorpay, test mode)", repaid: "Advance repaid by the farmer (Razorpay, test mode)", linkOff: "Payment link cancelled: farmer appealed", notpay: "Balance not payable", appeal: "Farmer appealed",
      review: (id, v) => `${id} ${v === "approve" ? "approved the claim" : "confirmed the burn"}`,
    },
    rail: "Bank transfer is simulated in this demo",
    decide: "Your decision", note: "What you saw or checked. Needed to confirm a burn.",
    approve: (x) => `Approve and release ${rupees(x)}`, approveNo: "Approve", confirm: "Confirm burn and draft notice",
    needNote: "Write what you saw or checked before confirming a burn.",
    decided: (id, at) => `Decided by ${id} · ${at}`, notice: "Open the recovery notice",
    empty: "Nothing waiting. The rules settled every claim.", pick: "Pick a claim on the left.",
    acres: "acres", total: (t, p) => `Season total ${rupees(t)} · paid so far ${rupees(p)}`,
  },
  hi: {
    explore: "देखें", officer: "अधिकारी", farmer: "किसान",
    signinTitle: "अधिकारी साइन-इन", signinNote: "नाम, राशि और जाँच की सूची सिर्फ़ ग्राम अधिकारी देखते हैं। सार्वजनिक नक्शे पर ये नहीं दिखते।",
    officerId: "अधिकारी आईडी", pin: "पिन", signin: "साइन-इन करें", demoPin: "डेमो पिन: 2468", wrongPin: "पिन सही नहीं है।", signout: "साइन-आउट",
    tabs: { todo: "फ़ैसला बाकी", done: "तय हो चुके", all: "सभी दावे" },
    summary: (n, m) => `${m} में से ${n} दावों पर आपका फ़ैसला चाहिए। बाकी नियमों ने तय कर दिए।`,
    chip: { possible_burn: "जलने की आशंका", needs_review: "साफ़ नहीं", officer_approved: "आपने मंज़ूर किया", officer_confirmed_burnt: "जलना पक्का",
      auto_approved: "नियमों से मंज़ूर", submitted: "जाँच जारी", appealed: "अपील" },
    atStake: (x) => `${rupees(x)} अग्रिम दाँव पर`, noAdv: "कोई अग्रिम नहीं",
    reading: "उपग्रह ने क्या देखा", clear: "साफ़ तस्वीरें", fires: "375 मीटर में आग अलर्ट", none: "कोई नहीं", last: "पिछला सीज़न (2024)",
    lastV: { auto_approved: "साफ़", possible_burn: "जलने की आशंका", needs_review: "साफ़ नहीं" },
    appeal: "किसान की अपील", infrared: "हर साफ़ तस्वीर का इन्फ्रारेड दृश्य (ताज़ा जला खेत गहरा नीला दिखता है)",
    book: "भुगतान का रिकॉर्ड", scheme: (st) => `${st === "HR" ? "हरियाणा" : "पंजाब"} · ₹1,000 प्रति एकड़, आधा कटाई से पहले`,
    when: { before: "कटाई से पहले", after: "जाँच के बाद", now: "आज" },
    rows: {
      adv: () => "साफ़ 2024 के लिए अग्रिम दिया", noadv: "कोई अग्रिम नहीं: 2024 साफ़ नहीं दिखा",
      held: "आपके फ़ैसले तक बाकी राशि रोकी गई", released: "बाकी राशि किसान के खाते में भेजी",
      recover: "अग्रिम वापस होगा; नोटिस का मसौदा तैयार", link: "किसान को भुगतान लिंक भेजा (Razorpay, टेस्ट मोड)", repaid: "किसान ने अग्रिम लौटाई (Razorpay, टेस्ट मोड)", linkOff: "भुगतान लिंक रद्द: किसान ने अपील की", notpay: "बाकी राशि देय नहीं", appeal: "किसान ने अपील की",
      review: (id, v) => `${id} ने ${v === "approve" ? "दावा मंज़ूर किया" : "जलना पक्का किया"}`,
    },
    rail: "इस डेमो में बैंक भुगतान नकली है",
    decide: "आपका फ़ैसला", note: "आपने क्या देखा या जाँचा। जलना पक्का करने के लिए ज़रूरी।",
    approve: (x) => `मंज़ूर करें और ${rupees(x)} भेजें`, approveNo: "मंज़ूर करें", confirm: "जलना पक्का करें और नोटिस बनाएँ",
    needNote: "जलना पक्का करने से पहले लिखें कि आपने क्या देखा या जाँचा।",
    decided: (id, at) => `${id} ने तय किया · ${at}`, notice: "वसूली नोटिस खोलें",
    empty: "कुछ बाकी नहीं। नियमों ने हर दावा तय कर दिया।", pick: "बाईं ओर से कोई दावा चुनें।",
    acres: "एकड़", total: (t, p) => `सीज़न की कुल राशि ${rupees(t)} · अब तक दिया ${rupees(p)}`,
  },
};
// officers in both states read Hindi or English; the Punjabi and Haryanvi choices show the Hindi desk
const pick = (l) => (l === "en" ? "en" : "hi");
let lang = initialLang("en");
const t = () => T[pick(lang)];

const S = { claims: [], fields: {}, windows: [], tab: "todo", sel: null, detail: null, officer: store.get("saakshi-officer", sessionStorage), pin: store.get("saakshi-pin", sessionStorage) };

function labelText() { $$("[data-t]").forEach((el) => { const v = t()[el.dataset.t]; if (typeof v === "string") el.textContent = v; }); }

// ---- sign-in ----
async function checkPin(pin) {
  const r = await fetch("/api/officer/check", { headers: { "X-Officer-Pin": pin } });
  return r.ok;
}
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

// ---- queue ----
const isOpen = (c) => c.status === "possible_burn" || c.status === "needs_review";
function chipKey(c) { return c.appeal && isOpen(c) ? "appealed" : c.status; }
function renderQueue() {
  const L = t(), open = S.claims.filter(isOpen);
  const list = S.tab === "todo" ? open.sort((a, b) => (b.appeal ? 1 : 0) - (a.appeal ? 1 : 0) || (a.status === "possible_burn" ? -1 : 1))
    : S.tab === "done" ? S.claims.filter((c) => c.review) : S.claims;
  $("#queue").innerHTML = `<div class="q-head"><div class="q-who"><b>${esc(S.officer)}</b><button class="link" id="signout">${esc(L.signout)}</button></div>
      <p class="cap">${esc(L.summary(open.length, S.claims.length))}</p>
      <div class="tabs">${Object.entries(L.tabs).map(([k, v]) => `<button data-tab="${k}" class="${S.tab === k ? "on" : ""}">${esc(v)}${k === "todo" ? ` <i>${open.length}</i>` : ""}</button>`).join("")}</div></div>
    <ul class="q-list">${list.length ? list.map((c) => {
      const k = kindOf(c.status), adv = c.advance?.status === "paid" ? c.advance.amount : 0;
      return `<li><button data-id="${c.id}" class="${S.sel === c.id ? "on" : ""}"><span class="dot ${chipKey(c) === "appealed" ? "appeal" : k}"></span>
        <span class="q-main"><b>${esc(name(c))}</b><small>${esc(fieldLabel(c))} · ${esc(village(c))}</small></span>
        <span class="q-side"><em class="chip ${chipKey(c) === "appealed" ? "appeal" : k}">${esc(L.chip[chipKey(c)] || c.status)}</em><small>${esc(adv ? L.atStake(adv) : L.noAdv)}</small></span></button></li>`;
    }).join("") : `<li class="empty">${esc(L.empty)}</li>`}</ul>`;
  $$("#queue [data-tab]").forEach((b) => { b.onclick = () => { S.tab = b.dataset.tab; renderQueue(); }; });
  $$("#queue [data-id]").forEach((b) => { b.onclick = () => select(b.dataset.id); });
  $("#signout").onclick = () => { store.del("saakshi-pin", sessionStorage); S.pin = null; showSignin(); };
}
const name = (c) => (lang === "en" ? c.farmer_name : c.farmer_name_hi || c.farmer_name);
const fieldLabel = (c) => (lang === "en" ? c.field_name : c.field_name_hi || c.field_name);
const village = (c) => { const f = S.fields[c.field_id]; return f ? (lang === "en" ? f.village : f.village_hi || f.village) : c.village; };

// ---- case ----
async function select(id) {
  S.sel = id;
  renderQueue();
  S.detail = await getJSON(`/api/claims/${id}`);
  renderCase();
}
function bookRows(c) {
  const L = t(), R = L.rows, adv = c.advance || {}, st = c.settlement || {}, ev = c.events || [];
  const rows = [];
  if (adv.status === "paid") rows.push({ when: L.when.before, text: R.adv(), amt: `+${rupees(adv.amount)}`, cls: "in" });
  else rows.push({ when: L.when.before, text: R.noadv, amt: "—", cls: "" });
  ev.filter((e) => e.type === "appeal").forEach((e) => rows.push({ when: fmtDate(e.at, lang), text: R.appeal, amt: "", cls: "note", note: e.note }));
  ev.filter((e) => e.type === "reviewed").forEach((e) => rows.push({ when: fmtDate(e.at, lang), text: R.review(e.by, e.verdict), amt: "", cls: "note", note: e.note }));
  if (st.state === "pending") rows.push({ when: L.when.after, text: R.held, amt: rupees((st.total || 0) - (adv.status === "paid" ? adv.amount : 0)), cls: "held" });
  if (st.state === "balance_due") rows.push({ when: st.released_at ? fmtDate(st.released_at, lang) : L.when.after, text: R.released, amt: `+${rupees(st.balance)}`, cls: "in" });
  const rec = c.recovery || {};
  ev.filter((e) => e.type === "recovery_cancelled").forEach((e) => rows.push({ when: fmtDate(e.at, lang), text: R.linkOff, amt: "", cls: "note" }));
  if (st.state === "recover_advance" && rec.status === "paid") rows.push({ when: fmtDate(rec.paid_at, lang), text: R.repaid, amt: `−${rupees(st.recover)}`, cls: "out", note: rec.payment_id });
  else if (st.state === "recover_advance" && rec.status === "issued") rows.push({ when: fmtDate(rec.issued_at, lang), text: R.link, amt: `−${rupees(st.recover)}`, cls: "held" });
  else if (st.state === "recover_advance") rows.push({ when: L.when.now, text: R.recover, amt: `−${rupees(st.recover)}`, cls: "out" });
  if (st.state === "not_payable") rows.push({ when: L.when.after, text: R.notpay, amt: "—", cls: "" });
  return rows;
}
function renderCase(flash = false) {
  const L = t(), c = S.detail, f = S.fields[c.field_id], d = c.decision || {}, k = kindOf(c.status);
  if (!c) { $("#case").innerHTML = `<p class="empty">${esc(L.pick)}</p>`; return; }
  const adv = c.advance?.status === "paid" ? c.advance.amount : 0, st = c.settlement || {};
  const balance = (st.total || Math.round((c.acres || 0) * 1000)) - adv;
  const bw = d.burn_date ? S.windows.findIndex((w) => w.start <= d.burn_date && d.burn_date <= w.end) : -1;
  const rows = bookRows(c);
  $("#case").innerHTML = `<header class="c-head"><div><h2>${esc(name(c))}</h2><p>${esc(fieldLabel(c))} · ${c.acres} ${esc(L.acres)} · ${esc(village(c))}</p></div>
      <em class="chip ${chipKey(c) === "appealed" ? "appeal" : k}">${esc(L.chip[chipKey(c)] || c.status)}</em></header>
    <div class="c-grid">
      <div class="c-left"><div id="film"></div>
        ${c.evidence_url ? `<details class="sec burnview"><summary>${esc(L.infrared)}</summary><img src="${esc(c.evidence_url)}" alt="" loading="lazy"></details>` : ""}</div>
      <div class="c-right">
        <section><h3>${esc(L.reading)}</h3><div class="band ${kindOf(d.outcome)}"><div class="ic">${icon(kindOf(d.outcome) === "clean" ? "i-check" : kindOf(d.outcome) === "burn" ? "i-flame" : "i-eye")}</div>
          <div><b>${esc(L.chip[d.outcome] || d.outcome)}</b><p>${esc(d.reason || "")}</p></div></div>
          <dl class="facts"><div><dt>${esc(L.clear)}</dt><dd>${(d.clear_dates || []).length}</dd></div><div><dt>${esc(L.fires)}</dt><dd>${d.fires_nearby || esc(L.none)}</dd></div>
            <div><dt>${esc(L.last)}</dt><dd>${esc(L.lastV[c.advance?.prev_outcome] || "—")}</dd></div></dl></section>
        ${c.appeal ? `<section class="appeal"><h3>${esc(L.appeal)}</h3><blockquote>${esc(c.appeal.note)}</blockquote><small>${esc(fmtDate(c.appeal.at, lang))}</small></section>` : ""}
        <section><h3>${esc(L.book)}</h3><p class="cap">${esc(L.scheme(c.state_code))}</p>
          <ol class="book">${rows.map((r, i) => `<li class="${r.cls}${flash && i === rows.length - 1 ? " new" : ""}"><span class="w">${esc(r.when)}</span><span class="tx">${esc(r.text)}${r.note ? `<small>“${esc(r.note)}”</small>` : ""}</span><b>${esc(r.amt)}</b></li>`).join("")}</ol>
          <p class="cap">${esc(L.total(st.total || Math.round((c.acres || 0) * 1000), adv + (st.state === "balance_due" ? st.balance : 0)))} · ${esc(L.rail)}</p></section>
        ${isOpen(c) ? `<section class="decide"><h3>${esc(L.decide)}</h3><textarea id="note" rows="2" placeholder="${esc(L.note)}"></textarea><p class="err" id="derr" hidden></p>
          <div class="d-btns"><button class="btn primary" id="approve">${icon("i-check")}<span>${esc(balance > 0 ? L.approve(balance) : L.approveNo)}</span></button>
          <button class="btn danger" id="confirm">${icon("i-flame")}<span>${esc(L.confirm)}</span></button></div></section>`
        : c.review ? `<section class="decided"><p class="cap">${esc(L.decided(c.review.officer_id, fmtDate(c.review.at, lang)))}</p>
          ${c.notice_url ? `<a class="btn ghost small" href="${esc(c.notice_url)}" target="_blank" rel="noopener">${esc(L.notice)}</a>` : ""}</section>` : ""}
      </div></div>`;
  if (f) filmstrip($("#film"), S.windows, f.geometry, lang, bw);
  $("#approve")?.addEventListener("click", () => decide("approve"));
  $("#confirm")?.addEventListener("click", () => decide("confirm_burnt"));
}
async function decide(verdict) {
  const note = $("#note").value.trim();
  if (verdict === "confirm_burnt" && !note) { $("#derr").textContent = t().needNote; $("#derr").hidden = false; return; }
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
  S.claims = await getJSON("/api/claims");
  S.detail = await getJSON(`/api/claims/${S.sel}`);
  renderQueue();
  renderCase(true);
}

async function load() {
  const [claims, fields, mf] = await Promise.all([getJSON("/api/claims"), getJSON("/api/fields"), getJSON("/tiles/manifest.json")]);
  S.claims = claims; S.windows = mf.windows;
  fields.forEach((f) => { S.fields[f.id] = f; });
  renderQueue();
  const first = S.claims.find(isOpen);
  if (first) select(first.id); else $("#case").innerHTML = `<p class="empty">${esc(t().empty)}</p>`;
}

setupHeader(lang, (l) => { lang = l; labelText(); renderQueue(); if (S.detail) renderCase(); });
labelText();
(async () => {
  if (S.pin && (await checkPin(S.pin))) load(); else showSignin();
})();
