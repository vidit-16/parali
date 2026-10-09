// Farmer view: one farmer's own field and money, in their language, with questions by voice or text and an
// appeal when they think the satellite is wrong. Phone-first.
import { $, $$, esc, icon, rupees, store, initialLang, setupHeader, fmtDate, filmstrip, kindOf, getJSON, ORBIT } from "./shared.js";
import { Recorder } from "./voice.js";

// Punjabi (pa) and Haryanvi (hr) are drafts and need a native speaker's review.
const T = {
  en: {
    explore: "Explore", officer: "Officer", farmer: "Farmer",
    who: "Who is using the app?", whoNote: "Demo: pick a farmer. A real farmer signs in with their phone number and sees only their own fields.",
    hello: (n) => `Namaste, ${n}`, switch: "Not you?", noClaim: "No claim this season yet.",
    status: { clean: "Paid in full", burn: "The satellite saw a burn", review: "An officer is looking", wait: "Being checked" },
    listen: "Listen", money: "Your money", field: "Your field this season",
    rows: { adv: "Advance before harvest", noadv: "No advance this year: last season was not clearly clean", bal: "Rest of the money",
      balHeld: "Held until the officer decides", balPaid: "Sent to your bank account", repay: "Advance to return", notpay: "Not payable this season" },
    total: (t) => `Full amount for your field: ${rupees(t)}`,
    ask: "Ask anything", askHint: "Hold the mic and speak in Hindi, or type.", send: "Send", listening: "Listening… let go to send",
    suggest: ["When will my money come?", "Why is my claim held?", "How do I appeal?"],
    thinking: "Thinking", you: "You", appeal: "I did not burn: appeal", appealTitle: "Tell the officer why the satellite is wrong",
    appealHint: "For example: used a happy seeder; the dark patch is wet soil after irrigation.", appealSend: "Send appeal",
    appealed: (d) => `Appeal sent on ${d}. The officer will look before any money is asked back.`, cancel: "Cancel",
    micErr: "The microphone is not available here. Type instead.", err: "Could not reach Saakshi. Try again.",
  },
  hi: {
    explore: "देखें", officer: "अधिकारी", farmer: "किसान",
    who: "ऐप कौन इस्तेमाल कर रहा है?", whoNote: "डेमो: एक किसान चुनें। असली किसान अपने फ़ोन नंबर से साइन-इन करता है और सिर्फ़ अपने खेत देखता है।",
    hello: (n) => `नमस्ते, ${n} जी`, switch: "आप नहीं हैं?", noClaim: "इस सीज़न का कोई दावा अभी नहीं।",
    status: { clean: "पूरी राशि मिल गई", burn: "उपग्रह को जलने का निशान दिखा", review: "अधिकारी देख रहे हैं", wait: "जाँच जारी है" },
    listen: "सुनें", money: "आपकी राशि", field: "इस सीज़न आपका खेत",
    rows: { adv: "कटाई से पहले अग्रिम", noadv: "इस साल अग्रिम नहीं: पिछला सीज़न साफ़ नहीं दिखा", bal: "बाकी राशि",
      balHeld: "अधिकारी के फ़ैसले तक रुकी", balPaid: "आपके बैंक खाते में भेजी", repay: "अग्रिम लौटाना होगा", notpay: "इस सीज़न देय नहीं" },
    total: (t) => `आपके खेत की पूरी राशि: ${rupees(t)}`,
    ask: "कुछ भी पूछें", askHint: "माइक दबाकर हिंदी में बोलें, या लिखें।", send: "भेजें", listening: "सुन रहे हैं… छोड़ते ही भेजेंगे",
    suggest: ["मेरा पैसा कब आएगा?", "मेरा दावा क्यों रुका है?", "अपील कैसे करूँ?"],
    thinking: "सोच रहे हैं", you: "आप", appeal: "मैंने नहीं जलाया: अपील करें", appealTitle: "अधिकारी को बताइए कि उपग्रह क्यों ग़लत है",
    appealHint: "जैसे: हैप्पी सीडर चलाया था; काला हिस्सा सिंचाई के बाद गीली मिट्टी है।", appealSend: "अपील भेजें",
    appealed: (d) => `${d} को अपील भेजी गई। पैसा वापस माँगने से पहले अधिकारी देखेंगे।`, cancel: "रहने दें",
    micErr: "यहाँ माइक नहीं चल रहा। लिखकर पूछें।", err: "साक्षी से संपर्क नहीं हो पाया। फिर कोशिश करें।",
  },
  pa: {
    explore: "ਵੇਖੋ", officer: "ਅਧਿਕਾਰੀ", farmer: "ਕਿਸਾਨ",
    who: "ਐਪ ਕੌਣ ਵਰਤ ਰਿਹਾ ਹੈ?", whoNote: "ਡੈਮੋ: ਇੱਕ ਕਿਸਾਨ ਚੁਣੋ। ਅਸਲ ਕਿਸਾਨ ਆਪਣੇ ਫ਼ੋਨ ਨੰਬਰ ਨਾਲ ਸਾਈਨ-ਇਨ ਕਰਦਾ ਹੈ ਅਤੇ ਸਿਰਫ਼ ਆਪਣੇ ਖੇਤ ਵੇਖਦਾ ਹੈ।",
    hello: (n) => `ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ${n} ਜੀ`, switch: "ਤੁਸੀਂ ਨਹੀਂ ਹੋ?", noClaim: "ਇਸ ਸੀਜ਼ਨ ਦਾ ਕੋਈ ਦਾਅਵਾ ਅਜੇ ਨਹੀਂ।",
    status: { clean: "ਪੂਰੀ ਰਕਮ ਮਿਲ ਗਈ", burn: "ਉਪਗ੍ਰਹਿ ਨੂੰ ਸਾੜ ਦਾ ਨਿਸ਼ਾਨ ਦਿਸਿਆ", review: "ਅਧਿਕਾਰੀ ਵੇਖ ਰਹੇ ਹਨ", wait: "ਜਾਂਚ ਜਾਰੀ ਹੈ" },
    listen: "ਸੁਣੋ", money: "ਤੁਹਾਡੀ ਰਕਮ", field: "ਇਸ ਸੀਜ਼ਨ ਤੁਹਾਡਾ ਖੇਤ",
    rows: { adv: "ਵਾਢੀ ਤੋਂ ਪਹਿਲਾਂ ਅਗਾਊਂ", noadv: "ਇਸ ਸਾਲ ਅਗਾਊਂ ਨਹੀਂ: ਪਿਛਲਾ ਸੀਜ਼ਨ ਸਾਫ਼ ਨਹੀਂ ਦਿਸਿਆ", bal: "ਬਾਕੀ ਰਕਮ",
      balHeld: "ਅਧਿਕਾਰੀ ਦੇ ਫ਼ੈਸਲੇ ਤੱਕ ਰੁਕੀ", balPaid: "ਤੁਹਾਡੇ ਬੈਂਕ ਖਾਤੇ ਵਿੱਚ ਭੇਜੀ", repay: "ਅਗਾਊਂ ਵਾਪਸ ਕਰਨਾ ਪਵੇਗਾ", notpay: "ਇਸ ਸੀਜ਼ਨ ਦੇਣਯੋਗ ਨਹੀਂ" },
    total: (t) => `ਤੁਹਾਡੇ ਖੇਤ ਦੀ ਪੂਰੀ ਰਕਮ: ${rupees(t)}`,
    ask: "ਕੁਝ ਵੀ ਪੁੱਛੋ", askHint: "ਮਾਈਕ ਦਬਾ ਕੇ ਹਿੰਦੀ ਵਿੱਚ ਬੋਲੋ, ਜਾਂ ਲਿਖੋ।", send: "ਭੇਜੋ", listening: "ਸੁਣ ਰਹੇ ਹਾਂ… ਛੱਡਦੇ ਹੀ ਭੇਜਾਂਗੇ",
    suggest: ["ਮੇਰਾ ਪੈਸਾ ਕਦੋਂ ਆਵੇਗਾ?", "ਮੇਰਾ ਦਾਅਵਾ ਕਿਉਂ ਰੁਕਿਆ ਹੈ?", "ਅਪੀਲ ਕਿਵੇਂ ਕਰਾਂ?"],
    thinking: "ਸੋਚ ਰਹੇ ਹਾਂ", you: "ਤੁਸੀਂ", appeal: "ਮੈਂ ਨਹੀਂ ਸਾੜਿਆ: ਅਪੀਲ ਕਰੋ", appealTitle: "ਅਧਿਕਾਰੀ ਨੂੰ ਦੱਸੋ ਕਿ ਉਪਗ੍ਰਹਿ ਕਿਉਂ ਗਲਤ ਹੈ",
    appealHint: "ਜਿਵੇਂ: ਹੈਪੀ ਸੀਡਰ ਚਲਾਇਆ ਸੀ; ਕਾਲਾ ਹਿੱਸਾ ਸਿੰਚਾਈ ਤੋਂ ਬਾਅਦ ਗਿੱਲੀ ਮਿੱਟੀ ਹੈ।", appealSend: "ਅਪੀਲ ਭੇਜੋ",
    appealed: (d) => `${d} ਨੂੰ ਅਪੀਲ ਭੇਜੀ ਗਈ। ਪੈਸਾ ਵਾਪਸ ਮੰਗਣ ਤੋਂ ਪਹਿਲਾਂ ਅਧਿਕਾਰੀ ਵੇਖੇਗਾ।`, cancel: "ਰਹਿਣ ਦਿਓ",
    micErr: "ਇੱਥੇ ਮਾਈਕ ਨਹੀਂ ਚੱਲ ਰਿਹਾ। ਲਿਖ ਕੇ ਪੁੱਛੋ।", err: "ਸਾਕਸ਼ੀ ਨਾਲ ਸੰਪਰਕ ਨਹੀਂ ਹੋਇਆ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
  },
  hr: {
    explore: "देक्खो", officer: "अफसर", farmer: "किसान",
    who: "ऐप कौण चलावै सै?", whoNote: "डेमो: एक किसान चुणो। असली किसान अपणे फोन नंबर तै साइन-इन करै सै अर सिर्फ अपणे खेत देक्खै सै।",
    hello: (n) => `राम राम, ${n} जी`, switch: "थम कोनी?", noClaim: "इस सीज़न का कोए दावा इब्ब तक कोनी।",
    status: { clean: "पूरी रकम मिलगी", burn: "उपग्रह नै जळण का निसान दिख्या", review: "अफसर देक्खण लाग रे सैं", wait: "जांच चालू सै" },
    listen: "सुणो", money: "थारी रकम", field: "इस सीज़न थारा खेत",
    rows: { adv: "कटाई तै पहल्यां एडवांस", noadv: "इस साल एडवांस कोनी: पाछला सीज़न साफ कोनी दिख्या", bal: "बाकी रकम",
      balHeld: "अफसर के फैसले तक रुकी", balPaid: "थारे बैंक खाते म्ह भेज दी", repay: "एडवांस उल्टा देणा पड़ैगा", notpay: "इस सीज़न देण लायक कोनी" },
    total: (t) => `थारे खेत की पूरी रकम: ${rupees(t)}`,
    ask: "कुछ भी पूछो", askHint: "माइक दबा कै हिंदी म्ह बोलो, या लिखो।", send: "भेजो", listening: "सुणण लाग रे सां… छोड्डते ए भेजांगे",
    suggest: ["मेरा पीसा कद आवैगा?", "मेरा दावा क्यूं रुक रया सै?", "अपील क्यूकर करूं?"],
    thinking: "सोच्चण लाग रे सां", you: "थम", appeal: "मन्नै कोनी जळाई: अपील करो", appealTitle: "अफसर नै बताओ उपग्रह क्यूं गलत सै",
    appealHint: "जियां: हैप्पी सीडर चलाया था; काळा हिस्सा सिंचाई पाच्छै गीली माट्टी सै।", appealSend: "अपील भेजो",
    appealed: (d) => `${d} नै अपील भेज दी। पीसा उल्टा मांगण तै पहल्यां अफसर देक्खैगा।`, cancel: "रहण दो",
    micErr: "उरै माइक कोनी चालरा। लिख कै पूछो।", err: "साक्षी तै बात कोनी हो पाई। फेर कोसिस करो।",
  },
};
let lang = initialLang("hi");
const t = () => T[lang];
const S = { fields: [], claims: [], windows: [], me: store.get("saakshi-farmer"), chat: [], recording: null };

function labelText() { $$("[data-t]").forEach((el) => { const v = t()[el.dataset.t]; if (typeof v === "string") el.textContent = v; }); }
const local = (en, hi) => (lang === "en" ? en : hi || en);

function renderWho() {
  const L = t();
  $("#phone").innerHTML = `<section class="card glass"><h1>${esc(L.who)}</h1><p class="cap">${esc(L.whoNote)}</p>
    <ul class="who">${S.fields.map((f) => `<li><button data-id="${f.id}"><b>${esc(local(f.farmer, f.farmer_hi))}</b><small>${esc(local(f.name, f.name_hi))} · ${esc(local(f.village, f.village_hi))}</small></button></li>`).join("")}</ul></section>`;
  $$("#phone [data-id]").forEach((b) => { b.onclick = () => { S.me = b.dataset.id; store.set("saakshi-farmer", S.me); render(); }; });
}

function moneyRows(c) {
  const R = t().rows, adv = c.advance || {}, st = c.settlement || {};
  const rows = [];
  rows.push(adv.status === "paid" ? { text: R.adv, amt: `+${rupees(adv.amount)}`, cls: "in", when: fmtDate(adv.paid_at, lang) } : { text: R.noadv, amt: "—", cls: "" });
  const rest = (st.total || 0) - (adv.status === "paid" ? adv.amount : 0);
  if (st.state === "balance_due") rows.push({ text: `${R.bal}: ${R.balPaid}`, amt: `+${rupees(st.balance)}`, cls: "in", when: fmtDate(st.released_at, lang) });
  else if (st.state === "recover_advance") rows.push({ text: R.repay, amt: `−${rupees(st.recover)}`, cls: "out" });
  else if (st.state === "not_payable") rows.push({ text: `${R.bal}: ${R.notpay}`, amt: "—", cls: "" });
  else rows.push({ text: `${R.bal}: ${R.balHeld}`, amt: rupees(rest), cls: "held" });
  return rows;
}

function render() {
  const L = t(), f = S.fields.find((x) => x.id === S.me);
  if (!f) return renderWho();
  const c = S.claims.find((x) => x.field_id === f.id);
  const k = c ? kindOf(c.status) : "wait";
  const d = c?.decision || {};
  const bw = d.burn_date ? S.windows.findIndex((w) => w.start <= d.burn_date && d.burn_date <= w.end) : -1;
  const msg = c?.message ? (lang === "en" ? c.message.en : c.message.hi) : "";
  const canAppeal = c && ["possible_burn", "needs_review", "officer_confirmed_burnt"].includes(c.status);
  $("#phone").innerHTML = `<section class="hello"><h1>${esc(L.hello(local(f.farmer, f.farmer_hi)))}</h1>
      <p class="cap">${esc(local(f.name, f.name_hi))} · ${f.acres} ${lang === "en" ? "acres" : "एकड़"} · ${esc(local(f.village, f.village_hi))} · <button class="link" id="switch">${esc(L.switch)}</button></p></section>
    ${c ? `<section class="card glass status-card ${k}"><div class="band ${k}"><div class="ic">${icon(k === "clean" ? "i-check" : k === "burn" ? "i-flame" : "i-eye")}</div>
        <div><b>${esc(L.status[k])}</b><p>${esc(msg)}</p></div></div>
        ${c.audio_url ? `<button class="btn ghost small listen" id="listen">${icon("i-play")}<span>${esc(L.listen)}</span></button><audio id="audio" src="${esc(c.audio_url)}" preload="none"></audio>` : ""}
        ${c.appeal ? `<p class="cap appealed">${esc(L.appealed(fmtDate(c.appeal.at, lang)))}</p>` : canAppeal ? `<button class="btn ghost wide" id="appeal">${esc(L.appeal)}</button>` : ""}
        <div id="appeal-box"></div></section>
      <section class="card glass"><h2>${esc(L.money)}</h2><ol class="book">${moneyRows(c).map((r) => `<li class="${r.cls}"><span class="tx">${esc(r.text)}${r.when ? `<small>${esc(r.when)}</small>` : ""}</span><b>${esc(r.amt)}</b></li>`).join("")}</ol>
        <p class="cap">${esc(L.total(c.settlement?.total || 0))}</p></section>` : `<section class="card glass"><p>${esc(L.noClaim)}</p></section>`}
    <section class="card glass"><h2>${esc(L.field)}</h2><div id="film"></div></section>
    <section class="card glass ask"><h2>${esc(L.ask)}</h2><p class="cap">${esc(L.askHint)}</p>
      <div class="chat" id="chat"></div>
      <div class="chips">${L.suggest.map((q) => `<button class="chipq">${esc(q)}</button>`).join("")}</div>
      <form class="composer" id="composer"><button type="button" class="mic" id="mic" aria-label="Hold to speak">${micSvg}</button>
        <input id="q" autocomplete="off" placeholder="${esc(L.ask)}…"><button class="btn primary small" type="submit">${esc(L.send)}</button></form>
      <p class="cap" id="mic-note" hidden></p></section>`;
  filmstrip($("#film"), S.windows, f.geometry, lang, bw);
  renderChat();
  $("#switch").onclick = () => { store.del("saakshi-farmer"); S.me = null; S.chat = []; render(); };
  $("#listen")?.addEventListener("click", () => $("#audio").play());
  $("#appeal")?.addEventListener("click", () => openAppeal(c));
  $$(".chipq").forEach((b) => { b.onclick = () => ask({ text: b.textContent }); });
  $("#composer").onsubmit = (e) => { e.preventDefault(); const q = $("#q").value.trim(); if (q) { $("#q").value = ""; ask({ text: q }); } };
  wireMic();
}
const micSvg = `<svg viewBox="0 0 24 24"><rect x="9" y="3.5" width="6" height="11" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V20.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`;

function renderChat() {
  const L = t();
  $("#chat").innerHTML = S.chat.map((m) => m.me
    ? `<div class="msg me"><small>${esc(L.you)}</small><p>${esc(m.text)}</p></div>`
    : m.pending ? `<div class="msg bot pending">${ORBIT}<p>${esc(L.thinking)}…</p></div>`
    : `<div class="msg bot"><p>${esc(lang === "en" ? m.en : m.hi)}</p>${m.audio ? `<button class="link" data-audio="${esc(m.audio)}">${icon("i-play")} ${esc(L.listen)}</button>` : ""}</div>`).join("");
  $$("#chat [data-audio]").forEach((b) => { b.onclick = () => new Audio(b.dataset.audio).play(); });
  const el = $("#chat");
  el.scrollTop = el.scrollHeight;
}
async function ask(payload) {
  const L = t();
  if (payload.text) S.chat.push({ me: true, text: payload.text });
  S.chat.push({ pending: true });
  renderChat();
  try {
    const r = await getJSON("/api/agent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ farmer_id: S.me, ...payload }) });
    S.chat.pop();
    if (r.transcript) S.chat.push({ me: true, text: r.transcript });
    S.chat.push({ hi: r.hi, en: r.en, audio: r.audio_url });
    renderChat();
    if (r.audio_url && lang !== "en") new Audio(r.audio_url).play().catch(() => {});
    if ((r.tools || []).some((x) => x === "contest" || x === "file_claim")) refresh();
  } catch {
    S.chat.pop();
    S.chat.push({ hi: L.err, en: L.err });
    renderChat();
  }
}
function wireMic() {
  const mic = $("#mic"), note = $("#mic-note");
  const start = async (e) => {
    e.preventDefault();
    if (S.recording) return;
    try {
      S.recording = new Recorder();
      await S.recording.start();
      mic.classList.add("on");
      note.textContent = t().listening; note.hidden = false;
    } catch { S.recording = null; note.textContent = t().micErr; note.hidden = false; }
  };
  const end = async () => {
    if (!S.recording) return;
    const rec = S.recording; S.recording = null;
    mic.classList.remove("on"); note.hidden = true;
    const { b64, seconds } = await rec.stop();
    if (seconds > 0.6) ask({ audio_b64: b64 });
  };
  mic.addEventListener("pointerdown", start);
  ["pointerup", "pointerleave", "pointercancel"].forEach((ev) => mic.addEventListener(ev, end));
}
function openAppeal(c) {
  const L = t();
  $("#appeal").hidden = true;
  $("#appeal-box").innerHTML = `<div class="appeal-form"><h3>${esc(L.appealTitle)}</h3><textarea id="appeal-note" rows="3" placeholder="${esc(L.appealHint)}"></textarea>
    <p class="err" id="appeal-err" hidden></p><div class="d-btns"><button class="btn primary" id="appeal-send">${esc(L.appealSend)}</button><button class="btn ghost" id="appeal-cancel">${esc(L.cancel)}</button></div></div>`;
  $("#appeal-cancel").onclick = () => { $("#appeal-box").innerHTML = ""; $("#appeal").hidden = false; };
  $("#appeal-send").onclick = async () => {
    const note = $("#appeal-note").value.trim();
    if (!note) { $("#appeal-note").focus(); return; }
    try {
      await getJSON(`/api/claims/${c.id}/appeal`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ note }) });
      await refresh();
    } catch (e) { $("#appeal-err").textContent = e.message; $("#appeal-err").hidden = false; }
  };
}
async function refresh() { S.claims = await getJSON("/api/claims"); render(); }

async function load() {
  const [fields, claims, mf] = await Promise.all([getJSON("/api/fields"), getJSON("/api/claims"), getJSON("/tiles/manifest.json")]);
  S.fields = fields.sort((a, b) => a.farmer.localeCompare(b.farmer)); S.claims = claims; S.windows = mf.windows;
  render();
}
setupHeader(lang, (l) => { lang = l; labelText(); render(); });
labelText();
load();
