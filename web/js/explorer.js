// Saakshi explorer: the season over the Patiala-Kaithal border belt, from our own Sentinel-2 tiles.
// Burn patches are burn-like ground seen by the satellite; decisions on fields come from the rules and an officer.
// This is the public view: fields carry their killa number, never the farmer's name or money.

// ?frames=timer: drive animation frames from a timer, for headless screenshots where the tab is hidden
const params = new URLSearchParams(location.search);
if (params.get("frames") === "timer") {
  window.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16);
  window.cancelAnimationFrame = (id) => clearTimeout(id);
}

const T = {
  // Punjabi (pa) and Haryanvi (hr) are drafts and need a native speaker's review.
  en: {
    loading: "Loading the season from orbit", explore: "Explore", officer: "Officer", farmer: "Farmer",
    caption: "Every November, Delhi's air turns hazardous.<small>Part of that smoke is straw burnt in Punjab and Haryana. Each dot is a NASA fire alert from the 2025 season.</small>",
    delhi: "Delhi", km: (n) => `${n} km from the belt`, study: "Study area · Patran, Punjab",
    kicker: "Patiala–Kaithal border belt · kharif 2025",
    headline: "<em>9 in 10</em> hectares that looked burnt got no fire alert.",
    alerts: "Fire alerts", vslbl: "Clean fields wrongly flagged (lower is better)", vscap: "399 fields checked by hand, in Punjab and Haryana",
    play: "Play the season", explorebtn: "Explore the map",
    fine: "Burn-like: ground that turned near-black right after its plant signal collapsed, seen by Sentinel-2.",
    l_burns: "Burns", l_fires: "Fire alerts", l_fields: "Fields", l_missed: "Only burns no alert caught", ha: "ha burn-like", fa: "fire alerts",
    stages: ["Standing paddy", "Harvest begins", "Harvest", "Stubble", "Peak burning", "Burning tails off", "Wheat sowing", "Wheat up"],
    toast: "Tap a dot to open a field", refphoto: "Close-up photo: Esri, not taken this season",
    v: { clean: "Clean", review: "With the officer", burn: "Possible burn" },
    vline: { clean: (n) => `No burn in any of ${n} clear images`, burn: (d) => `Burn signature on ${d}`, review: () => "Unclear: the officer looks at it" },
    signal: "Plant signal through the season", signalNote: "A burn drops it below zero overnight.",
    clear: "Clear images", nearest: "Fire alerts within 375 m", none: "none", last: "Last season (2024)",
    checked: (d) => `Checked ${d}`, again: "Run again", check: "Run the satellite check",
    steps: ["Finding every clear image", "Removing clouds", "Comparing dates", "Checking fire alerts"],
    acres: "acres", err: "The check did not finish. Try again.",
  },
  hi: {
    loading: "उपग्रह से सीज़न ला रहे हैं", explore: "देखें", officer: "अधिकारी", farmer: "किसान",
    caption: "हर नवंबर दिल्ली की हवा ख़तरनाक हो जाती है।<small>उस धुएँ का एक हिस्सा पंजाब और हरियाणा में जली पराली है। हर बिंदु 2025 सीज़न का NASA आग अलर्ट है।</small>",
    delhi: "दिल्ली", km: (n) => `क्षेत्र से ${n} किमी`, study: "अध्ययन क्षेत्र · पातड़ां, पंजाब",
    kicker: "पटियाला–कैथल सीमा क्षेत्र · खरीफ़ 2025",
    headline: "जले दिखने वाले हर <em>10 में से 9</em> हेक्टेयर पर आग का कोई अलर्ट नहीं आया।",
    alerts: "आग अलर्ट", vslbl: "साफ़ खेत जिन्हें गलती से संदिग्ध बताया (कम बेहतर)", vscap: "पंजाब और हरियाणा के 399 खेत, हाथ से जाँचे",
    play: "पूरा सीज़न देखें", explorebtn: "नक्शा देखें",
    fine: "जले जैसा: वह ज़मीन जो पौधों का संकेत गिरते ही लगभग काली हो गई, Sentinel-2 उपग्रह से देखी गई।",
    l_burns: "जले खेत", l_fires: "आग अलर्ट", l_fields: "खेत", l_missed: "केवल वे जले खेत जिन पर अलर्ट नहीं आया", ha: "हेक्टेयर जले जैसे", fa: "आग अलर्ट",
    stages: ["खड़ा धान", "कटाई शुरू", "कटाई", "पराली", "सबसे ज़्यादा जलना", "जलना घटा", "गेहूँ बुआई", "गेहूँ उगा"],
    toast: "खेत खोलने के लिए बिंदु पर टैप करें", refphoto: "नज़दीकी फ़ोटो: Esri, इस सीज़न की नहीं",
    v: { clean: "साफ़", review: "अधिकारी के पास", burn: "जलने की आशंका" },
    vline: { clean: (n) => `${n} साफ़ तस्वीरों में कहीं जलना नहीं`, burn: (d) => `${d} को जलने का निशान`, review: () => "साफ़ नहीं: अधिकारी देखेंगे" },
    signal: "सीज़न भर पौधों का संकेत", signalNote: "जलने पर यह एक रात में शून्य से नीचे गिरता है।",
    clear: "साफ़ तस्वीरें", nearest: "375 मीटर में आग अलर्ट", none: "कोई नहीं", last: "पिछला सीज़न (2024)",
    checked: (d) => `${d} को जाँचा`, again: "फिर जाँचें", check: "उपग्रह जाँच चलाएँ",
    steps: ["हर साफ़ तस्वीर ढूँढ रहे हैं", "बादल हटा रहे हैं", "तारीखें मिला रहे हैं", "आग अलर्ट जाँच रहे हैं"],
    acres: "एकड़", err: "जाँच पूरी नहीं हुई। फिर कोशिश करें।",
  },
  pa: {
    loading: "ਉਪਗ੍ਰਹਿ ਤੋਂ ਸੀਜ਼ਨ ਲਿਆ ਰਹੇ ਹਾਂ", explore: "ਵੇਖੋ", officer: "ਅਧਿਕਾਰੀ", farmer: "ਕਿਸਾਨ",
    caption: "ਹਰ ਨਵੰਬਰ ਦਿੱਲੀ ਦੀ ਹਵਾ ਖ਼ਤਰਨਾਕ ਹੋ ਜਾਂਦੀ ਹੈ।<small>ਉਸ ਧੂੰਏਂ ਦਾ ਇੱਕ ਹਿੱਸਾ ਪੰਜਾਬ ਅਤੇ ਹਰਿਆਣਾ ਵਿੱਚ ਸਾੜੀ ਪਰਾਲੀ ਹੈ। ਹਰ ਬਿੰਦੂ 2025 ਸੀਜ਼ਨ ਦਾ NASA ਅੱਗ ਅਲਰਟ ਹੈ।</small>",
    delhi: "ਦਿੱਲੀ", km: (n) => `ਖੇਤਰ ਤੋਂ ${n} ਕਿਮੀ`, study: "ਅਧਿਐਨ ਖੇਤਰ · ਪਾਤੜਾਂ, ਪੰਜਾਬ",
    kicker: "ਪਟਿਆਲਾ–ਕੈਥਲ ਸਰਹੱਦੀ ਖੇਤਰ · ਸਾਉਣੀ 2025",
    headline: "ਸੜੇ ਦਿਸਦੇ ਹਰ <em>10 ਵਿੱਚੋਂ 9</em> ਹੈਕਟੇਅਰ ਲਈ ਕੋਈ ਅੱਗ ਅਲਰਟ ਨਹੀਂ ਆਇਆ।",
    alerts: "ਅੱਗ ਅਲਰਟ", vslbl: "ਸਾਫ਼ ਖੇਤ ਜਿਨ੍ਹਾਂ ਨੂੰ ਗਲਤੀ ਨਾਲ ਸ਼ੱਕੀ ਕਿਹਾ (ਘੱਟ ਬਿਹਤਰ)", vscap: "ਪੰਜਾਬ ਅਤੇ ਹਰਿਆਣਾ ਦੇ 399 ਖੇਤ, ਹੱਥੀਂ ਜਾਂਚੇ",
    play: "ਪੂਰਾ ਸੀਜ਼ਨ ਵੇਖੋ", explorebtn: "ਨਕਸ਼ਾ ਵੇਖੋ",
    fine: "ਸੜੇ ਵਰਗੀ: ਉਹ ਜ਼ਮੀਨ ਜੋ ਪੌਦਿਆਂ ਦਾ ਸੰਕੇਤ ਡਿੱਗਦੇ ਹੀ ਲਗਭਗ ਕਾਲੀ ਹੋ ਗਈ, Sentinel-2 ਉਪਗ੍ਰਹਿ ਤੋਂ ਵੇਖੀ।",
    l_burns: "ਸੜੇ ਖੇਤ", l_fires: "ਅੱਗ ਅਲਰਟ", l_fields: "ਖੇਤ", l_missed: "ਸਿਰਫ਼ ਉਹ ਸੜੇ ਖੇਤ ਜਿਨ੍ਹਾਂ ਉੱਤੇ ਅਲਰਟ ਨਹੀਂ ਆਇਆ", ha: "ਹੈਕਟੇਅਰ ਸੜੇ ਵਰਗੇ", fa: "ਅੱਗ ਅਲਰਟ",
    stages: ["ਖੜ੍ਹਾ ਝੋਨਾ", "ਵਾਢੀ ਸ਼ੁਰੂ", "ਵਾਢੀ", "ਪਰਾਲੀ", "ਸਭ ਤੋਂ ਵੱਧ ਸਾੜ", "ਸਾੜ ਘਟਿਆ", "ਕਣਕ ਦੀ ਬਿਜਾਈ", "ਕਣਕ ਉੱਗੀ"],
    toast: "ਖੇਤ ਖੋਲ੍ਹਣ ਲਈ ਬਿੰਦੂ ਉੱਤੇ ਟੈਪ ਕਰੋ", refphoto: "ਨੇੜਲੀ ਫ਼ੋਟੋ: Esri, ਇਸ ਸੀਜ਼ਨ ਦੀ ਨਹੀਂ",
    v: { clean: "ਸਾਫ਼", review: "ਅਧਿਕਾਰੀ ਕੋਲ", burn: "ਸਾੜ ਦਾ ਸ਼ੱਕ" },
    vline: { clean: (n) => `${n} ਸਾਫ਼ ਤਸਵੀਰਾਂ ਵਿੱਚ ਕਿਤੇ ਸਾੜ ਨਹੀਂ`, burn: (d) => `${d} ਨੂੰ ਸਾੜ ਦਾ ਨਿਸ਼ਾਨ`, review: () => "ਸਾਫ਼ ਨਹੀਂ: ਅਧਿਕਾਰੀ ਵੇਖੇਗਾ" },
    signal: "ਸੀਜ਼ਨ ਭਰ ਪੌਦਿਆਂ ਦਾ ਸੰਕੇਤ", signalNote: "ਸਾੜ ਨਾਲ ਇਹ ਇੱਕ ਰਾਤ ਵਿੱਚ ਸਿਫ਼ਰ ਤੋਂ ਹੇਠਾਂ ਡਿੱਗਦਾ ਹੈ।",
    clear: "ਸਾਫ਼ ਤਸਵੀਰਾਂ", nearest: "375 ਮੀਟਰ ਵਿੱਚ ਅੱਗ ਅਲਰਟ", none: "ਕੋਈ ਨਹੀਂ", last: "ਪਿਛਲਾ ਸੀਜ਼ਨ (2024)",
    checked: (d) => `${d} ਨੂੰ ਜਾਂਚਿਆ`, again: "ਦੁਬਾਰਾ ਜਾਂਚੋ", check: "ਉਪਗ੍ਰਹਿ ਜਾਂਚ ਚਲਾਓ",
    steps: ["ਹਰ ਸਾਫ਼ ਤਸਵੀਰ ਲੱਭ ਰਹੇ ਹਾਂ", "ਬੱਦਲ ਹਟਾ ਰਹੇ ਹਾਂ", "ਤਾਰੀਖਾਂ ਮਿਲਾ ਰਹੇ ਹਾਂ", "ਅੱਗ ਅਲਰਟ ਜਾਂਚ ਰਹੇ ਹਾਂ"],
    acres: "ਏਕੜ", err: "ਜਾਂਚ ਪੂਰੀ ਨਹੀਂ ਹੋਈ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
  },
  hr: {
    loading: "उपग्रह तै सीज़न ल्यावां सां", explore: "देक्खो", officer: "अफसर", farmer: "किसान",
    caption: "हर नवंबर म्ह दिल्ली की हवा खतरनाक हो ज्यावै सै।<small>उस धुम्मे का एक हिस्सा पंजाब अर हरियाणा म्ह जळी पराळी सै। हर बिंदु 2025 सीज़न का NASA आग अलर्ट सै।</small>",
    delhi: "दिल्ली", km: (n) => `इलाके तै ${n} किमी`, study: "अध्ययन इलाका · पातड़ां, पंजाब",
    kicker: "पटियाला–कैथल बॉर्डर इलाका · खरीफ़ 2025",
    headline: "जळे दिक्खण आळे हर <em>10 म्ह तै 9</em> हेक्टेयर पै कोए आग का अलर्ट कोनी आया।",
    alerts: "आग अलर्ट", vslbl: "साफ खेत जिन पै गलती तै शक करया (कम आच्छा)", vscap: "पंजाब अर हरियाणा के 399 खेत, हाथ तै जांचे",
    play: "पूरा सीज़न देक्खो", explorebtn: "नक्सा देक्खो",
    fine: "जळे बरगी: वा धरती जो पौधां का संकेत गिरते ए काळी हो गी, Sentinel-2 नै देक्खी।",
    l_burns: "जळे खेत", l_fires: "आग अलर्ट", l_fields: "खेत", l_missed: "सिर्फ वे जळे खेत जिन पै अलर्ट कोनी आया", ha: "हेक्टेयर जळे बरगे", fa: "आग अलर्ट",
    stages: ["खड़या धान", "कटाई शुरू", "कटाई", "पराळी", "सब तै घणा जळाणा", "जळाणा घटया", "गेहूं की बिजाई", "गेहूं उग्या"],
    toast: "खेत खोलण खातर बिंदु पै टैप करो", refphoto: "नजदीक की फोटू: Esri, इस सीज़न की कोनी",
    v: { clean: "साफ", review: "अफसर कनै", burn: "जळण का शक" },
    vline: { clean: (n) => `${n} साफ फोटुआं म्ह कितै जळाणा कोनी`, burn: (d) => `${d} नै जळण का निसान`, review: () => "साफ कोनी: अफसर देक्खैगा" },
    signal: "सीज़न भर पौधां का संकेत", signalNote: "जळण पै यो एक रात म्ह जीरो तै तळै गिरै सै।",
    clear: "साफ फोटू", nearest: "375 मीटर म्ह आग अलर्ट", none: "कोए ना", last: "पाछला सीज़न (2024)",
    checked: (d) => `${d} नै जांच्या`, again: "फेर जांचो", check: "उपग्रह जांच चलाओ",
    steps: ["हर साफ फोटो टोहण लाग रे सां", "बादळ हटाण लाग रे सां", "तारीख मिलाण लाग रे सां", "आग अलर्ट जांचण लाग रे सां"],
    acres: "किल्ले", err: "जांच पूरी कोनी होई। फेर कोसिस करो।",
  },
};
const HTML_LANG = { en: "en", hi: "hi", pa: "pa", hr: "hi" };
const LOCALE = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", hr: "hi-IN" };
const LOCAL_NAME = { en: ["साक्षी", "hi"], hi: ["साक्षी", "hi"], hr: ["साक्षी", "hi"], pa: ["ਸਾਕਸ਼ੀ", "pa"] };
const CODE = { en: "EN", hi: "हिं", pa: "ਪੰ", hr: "हरि" };
// Burn colours run orange to purple by date. Yellow is kept for NASA fire alerts only.
const BURN_RAMP = [[30, "#FF9D5C"], [50, "#FF6A3D"], [62, "#E8384F"], [80, "#C2187E"], [100, "#7B2CBF"]];
const DELHI = [77.209, 28.6139];
const STUDY_BOX = [76.06, 29.86, 76.22, 30.01]; // the hand-labelled Patran area, glued to the Kaithal outline
const INDIA = { center: [79.5, 23.2], zoom: 3.6 };

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const icon = (id) => `<svg><use href="#${id}"/></svg>`;
const store = { get: (k) => { try { return localStorage.getItem(k); } catch { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* blocked */ } } };

let lang = store.get("saakshi-lang") || (navigator.language.startsWith("hi") ? "hi" : navigator.language.startsWith("pa") ? "pa" : "en");
if (!T[lang]) lang = "en";
const t = () => T[lang];

const state = { day: 0, playing: false, raf: 0, layers: { burns: true, fires: true, fields: true, missed: false }, intro: true, field: null, check: null, visible: new Set() };
let map, manifest, windows = [], day0, D0, D1, centers = [], cumHa = [], cumFires = [], beltFires = [], demo = {}, fieldsById = {}, syncPins = () => {};

// ---- language ----
function applyLang() {
  document.documentElement.lang = HTML_LANG[lang];
  $$("[data-i18n]").forEach((el) => { const v = t()[el.dataset.i18n]; if (typeof v === "string") el.innerHTML = v; });
  const [local, script] = LOCAL_NAME[lang];
  $("#name-local").textContent = local;
  $("#name-local").lang = script;
  $("#lang-cur").textContent = CODE[lang];
  $$("#lang-menu li").forEach((li) => { li.classList.toggle("on", li.dataset.lang === lang); li.setAttribute("aria-selected", li.dataset.lang === lang); });
  $$(".layers [data-tip]").forEach((b) => b.setAttribute("aria-label", t()[b.dataset.tip]));
  if (windows.length) { buildTicks(); renderTimeline(); }
  if (state.field) renderPanel();
  syncPins();
  if (map && map.getLayer && delhiMarker) delhiMarker.getElement().innerHTML = delhiHtml();
  if (studyMarker) studyMarker.getElement().textContent = t().study;
}

// ---- dates ----
const dayNum = (iso) => Math.round((new Date(iso) - day0) / 864e5);
const dateOf = (d) => new Date(day0.getTime() + d * 864e5);
const MONTH = () => (lang === "en" ? "short" : "long");
const fmtDay = (d, month = MONTH()) => dateOf(d).toLocaleDateString(LOCALE[lang], { day: "numeric", month });
const fmtIso = (iso) => new Date(iso).toLocaleDateString(LOCALE[lang], { day: "numeric", month: "long" });
const fmtRange = (w) => { const s = new Date(w.start), e = new Date(w.end); return `${s.getDate()}–${e.getDate()} ${e.toLocaleDateString(LOCALE[lang], { month: MONTH() })}`; };
const windowIndex = (d) => { let k = 0; windows.forEach((w, j) => { if (dayNum(w.start) <= d) k = j; }); return k; };

// ---- timeline: one stop per day ----
function buildSpark() {
  const svg = $("#spark"), W = 1000, H = 26, n = D1 - D0;
  const daily = Array.from({ length: n + 1 }, (_, i) => manifest.burn_ha_by_day[D0 + i] || 0);
  const smooth = daily.map((_, i) => (daily[i - 1] || 0) * 0.25 + daily[i] * 0.5 + (daily[i + 1] || 0) * 0.25);
  const max = Math.max(...smooth);
  const pts = smooth.map((v, i) => [(i / n) * W, H - Math.sqrt(v / max) * H]);
  const path = `M0,${H} ` + pts.map(([x, y]) => `L${x.toFixed(1)},${y.toFixed(1)}`).join(" ") + ` L${W},${H} Z`;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.innerHTML = `<defs><clipPath id="sparkclip"><rect id="sparkcut" x="0" y="-2" width="0" height="${H + 4}"/></clipPath></defs>
    <path class="all" d="${path}"/><path class="past" d="${path}" clip-path="url(#sparkclip)"/>`;
  $("#scrub").insertAdjacentHTML("beforeend", `<div class="thumb" id="thumb"></div>`);
  const slider = $("#slider");
  slider.min = D0; slider.max = D1; slider.step = 1;
}
function buildTicks() {
  const marks = [D0];
  for (let d = D0 + 1; d <= D1; d++) { const x = dateOf(d); if (x.getDate() === 1 || x.getDate() === 15) marks.push(d); }
  $("#ticks").innerHTML = marks.map((d) => {
    const x = dateOf(d), lab = x.getDate() === 15 ? "15" : fmtDay(d, "short");
    return `<span style="left:${((d - D0) / (D1 - D0)) * 100}%">${esc(lab)}</span>`;
  }).join("");
}
function renderTimeline() {
  const frac = (state.day - D0) / (D1 - D0);
  $("#when").textContent = fmtDay(state.day);
  $("#stage").textContent = t().stages[windowIndex(state.day)];
  $("#sparkcut")?.setAttribute("width", String(frac * 1000));
  const th = $("#thumb");
  if (th) th.style.left = `${frac * 100}%`;
  $("#slider").value = state.day;
  $("#ring").style.strokeDashoffset = String(151 * (1 - frac));
  $("#ha").textContent = Math.round(cumHa[state.day - D0] || 0).toLocaleString("en-IN");
  $("#fa").textContent = (cumFires[state.day - D0] || 0).toLocaleString("en-IN");
}

const zoomFade = (v) => ["interpolate", ["linear"], ["zoom"], 14.3, v, 15.3, 0];
function setDay(d) {
  d = Math.max(D0, Math.min(D1, Math.round(d)));
  state.day = d;
  // between the middles of two ten-day windows, fade from one picture to the next
  let j = 0;
  centers.forEach((c, m) => { if (c <= d) j = m; });
  const k = Math.min(j + 1, windows.length - 1);
  const f = k === j ? 0 : Math.max(0, Math.min(1, (d - centers[j]) / (centers[k] - centers[j])));
  // only the two pictures in play (and the next one, preloading) fetch tiles
  const want = new Set([j, k, Math.min(k + 1, windows.length - 1)]);
  windows.forEach((w, m) => {
    const id = `img-${w.id}`;
    if (want.has(m) !== state.visible.has(m)) map.setLayoutProperty(id, "visibility", want.has(m) ? "visible" : "none");
    map.setPaintProperty(id, "raster-opacity", zoomFade(m === j ? 1 : m === k ? f : 0));
  });
  state.visible = want;
  map.setFilter("burns", ["<=", ["get", "d"], d]);
  map.setFilter("burns-new", ["all", [">", ["get", "d"], d - 4], ["<=", ["get", "d"], d]]);
  map.setFilter("fires", ["<=", ["get", "d"], d]);
  map.setFilter("fires-states", ["<=", ["get", "d"], d]);
  map.setLayoutProperty("fires", "icon-size", ["case", [">", ["get", "d"], d - 3], 1, 0.62]);
  renderTimeline();
}

function play(speed = 6, onEnd = null, from = null) {
  stop();
  if (from !== null) setDay(from);
  else if (state.day >= D1) setDay(D0);
  state.playing = true;
  $("#play-glyph").setAttribute("href", "#i-pause");
  $("#play").setAttribute("aria-label", "Pause");
  let last = performance.now(), acc = state.day;
  const tick = (now) => {
    acc += ((now - last) / 1000) * (reduced ? speed / 2 : speed);
    last = now;
    if (Math.round(acc) !== state.day) { setDay(acc); state.onDay && state.onDay(state.day); }
    if (state.day >= D1) { stop(); onEnd && onEnd(); return; }
    state.raf = requestAnimationFrame(tick);
  };
  state.raf = requestAnimationFrame(tick);
}
function stop() {
  cancelAnimationFrame(state.raf);
  state.playing = false;
  $("#play-glyph").setAttribute("href", "#i-play");
  $("#play").setAttribute("aria-label", "Play");
}

// ---- hero, captions, hints ----
function showHero() {
  state.intro = false;
  const h = $("#hero");
  h.hidden = false;
  document.body.classList.add("hero-open");
  requestAnimationFrame(() => requestAnimationFrame(() => h.classList.add("show")));
}
function hideHero() { $("#hero").hidden = true; document.body.classList.remove("hero-open"); }
function toast(text, ms = 4200) {
  const el = $("#toast");
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toast.t);
  toast.t = setTimeout(() => { el.hidden = true; }, ms);
}

const regionBounds = () => { const [w, s, e, n] = manifest.bounds; return [[w, s], [e, n]]; };
function fitRegion(duration = 1200) {
  const wide = innerWidth > 900, bottom = innerWidth <= 640 ? Math.round(innerHeight * 0.52) : 120;
  map.fitBounds(regionBounds(), { padding: { top: 80, bottom, left: wide ? 120 : 24, right: wide ? 90 : 24 }, duration: reduced ? 0 : duration });
}

function playSeason() {
  hideHero();
  closePanel();
  fitRegion();
  state.onDay = (d) => {
    if (d === 58) map.flyTo({ center: [76.15, 29.935], zoom: 11.8, duration: reduced ? 0 : 2600, essential: true });
  };
  setTimeout(() => play(5, () => { state.onDay = null; if (fieldsById["f-baljeet"]) openField(fieldsById["f-baljeet"]); }, D0), reduced ? 0 : 1300);
}

// ---- the opening: India, the smoke, then into the belt ----
let delhiMarker = null, studyMarker = null;
function haversineKm([lon1, lat1], [lon2, lat2]) {
  const r = Math.PI / 180, a = Math.sin(((lat2 - lat1) * r) / 2) ** 2 + Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin(((lon2 - lon1) * r) / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(a));
}
function delhiHtml() {
  const [w, s, e, n] = manifest.bounds, km = Math.round(haversineKm(DELHI, [(w + e) / 2, (s + n) / 2]) / 10) * 10;
  return `<i></i><b>${esc(t().delhi)}</b><span>${esc(t().km(km))}</span>`;
}
function runIntro() {
  const cap = $("#caption");
  cap.innerHTML = t().caption;
  cap.hidden = false;
  setDay(D1);
  let skipped = false;
  const land = () => {
    cap.hidden = true;
    play(9, () => { if (state.intro) { setDay(D0 + 42); showHero(); toast(t().toast); } }, D0);
  };
  const skip = () => {
    if (skipped) return;
    skipped = true;
    cap.hidden = true;
    stop();
    map.stop();
    fitRegion(0);
    setDay(D0 + 42);
    showHero();
  };
  ["mousedown", "wheel", "touchstart", "keydown"].forEach((ev) => addEventListener(ev, skip, { once: true, passive: true }));
  setTimeout(() => {
    if (skipped) return;
    const wide = innerWidth > 900, bottom = innerWidth <= 640 ? Math.round(innerHeight * 0.52) : 120;
    map.fitBounds(regionBounds(), { padding: { top: 80, bottom, left: wide ? 120 : 24, right: wide ? 90 : 24 }, duration: 4200, curve: 1.5, essential: true });
    map.once("moveend", () => {
      if (skipped) return;
      ["mousedown", "wheel", "touchstart", "keydown"].forEach((ev) => removeEventListener(ev, skip));
      land();
    });
  }, 3200);
  store.set("saakshi-intro", "1");
}

// ---- fields and the case file ----
function centroid(g) {
  const ring = g.coordinates[0], n = ring.length - 1;
  return ring.slice(0, n).reduce((a, [x, y]) => [a[0] + x / n, a[1] + y / n], [0, 0]);
}
const kindOf = (o) => (o === "auto_approved" || o === "officer_approved" ? "clean" : o === "possible_burn" ? "burn" : "review");
const ICON = { clean: "i-check", burn: "i-flame", review: "i-eye" };
const fieldName = (p) => (lang === "en" ? p.name : p.name_hi || p.name);

function openField(f) {
  stop();
  state.field = f;
  state.check = demo[f.properties.id] ? { status: "done", ...demo[f.properties.id] } : null;
  // jump the season to the day that matters for this field, so the map shows what the card says
  const bd = state.check?.result?.current?.decision?.burn_date;
  setDay(bd ? dayNum(bd) + 1 : D1);
  const narrow = innerWidth <= 640;
  map.flyTo({ center: centroid(f.geometry), zoom: 15.2, duration: reduced ? 0 : 2200, essential: true,
    offset: narrow ? [0, -innerHeight * 0.22] : [-200, 0] });
  hideHero();
  renderPanel();
  $("#panel").hidden = false;
  document.body.classList.add("panel-open");
}
function closePanel() { state.field = null; state.check = null; $("#panel").hidden = true; document.body.classList.remove("panel-open"); }

// before/after cut from our own tiles: late September against the window of the burn (or early November)
function lonLatToPx([lon, lat], z) {
  const s = 256 * 2 ** z, y = Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
  return [((lon + 180) / 360) * s, (1 - y / Math.PI) / 2 * s];
}
async function drawCut(canvas, windowId, geom) {
  const z = 14, W = 128, H = 80, scale = 3;
  const pts = geom.coordinates[0].map((c) => lonLatToPx(c, z));
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const x0 = cx - W / 2, y0 = cy - H / 2;
  canvas.width = W * scale; canvas.height = H * scale;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  const tiles = [];
  for (let tx = Math.floor(x0 / 256); tx <= Math.floor((x0 + W) / 256); tx++)
    for (let ty = Math.floor(y0 / 256); ty <= Math.floor((y0 + H) / 256); ty++) tiles.push([tx, ty]);
  await Promise.all(tiles.map(([tx, ty]) => new Promise((ok) => {
    const img = new Image();
    img.onload = () => { ctx.drawImage(img, (tx * 256 - x0) * scale, (ty * 256 - y0) * scale, 256 * scale, 256 * scale); ok(); };
    img.onerror = ok;
    img.src = `/tiles/${windowId}/${z}/${tx}/${ty}.webp`;
  })));
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  pts.forEach(([x, y], i) => (i ? ctx.lineTo : ctx.moveTo).call(ctx, (x - x0) * scale, (y - y0) * scale));
  ctx.closePath();
  ctx.stroke();
}

function signalSvg(series, burnIso) {
  const pts = series.filter((s) => s.nbr !== null && s.valid >= 0.5);
  if (pts.length < 2) return "";
  const W = 340, H = 96, padL = 26, padB = 16, x0 = new Date(series[0].date), x1 = new Date(series.at(-1).date);
  const X = (iso) => padL + ((new Date(iso) - x0) / (x1 - x0)) * (W - padL - 4);
  const Y = (v) => 6 + (1 - (v + 0.4) / 1.2) * (H - padB - 6);  // NBR -0.4 .. 0.8
  const line = pts.map((p, i) => `${i ? "L" : "M"}${X(p.date).toFixed(1)},${Y(p.nbr).toFixed(1)}`).join(" ");
  const dots = pts.map((p) => `<circle class="dot" cx="${X(p.date).toFixed(1)}" cy="${Y(p.nbr).toFixed(1)}" r="2"/>`).join("");
  const months = [];
  for (let m = new Date(x0.getFullYear(), x0.getMonth() + 1, 1); m <= x1; m = new Date(m.getFullYear(), m.getMonth() + 1, 1))
    months.push(`<text x="${X(m.toISOString()).toFixed(1)}" y="${H - 3}">${esc(m.toLocaleDateString(LOCALE[lang], { month: MONTH() }))}</text>`);
  const mark = burnIso ? `<line class="mark" x1="${X(burnIso)}" x2="${X(burnIso)}" y1="4" y2="${H - padB}"/>` : "";
  return `<svg class="signal" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">
    <line class="grid" x1="${padL}" x2="${W}" y1="${Y(0)}" y2="${Y(0)}"/><text x="0" y="${Y(0) + 3}">0</text>
    <text x="0" y="${Y(0.6) + 3}">0.6</text>${mark}<path class="line" d="${line}"/>${dots}${months.join("")}</svg>`;
}

const SCAN_SVG = `<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" fill="#1A2440"/>
  <use href="#sa" fill="#2A3A63" transform="translate(32 30) scale(.8) translate(-32 -33)"/>
  <g clip-path="url(#scanclip)"><rect width="64" height="64" rx="16" fill="url(#sky)"/><use href="#sa" fill="#fff" transform="translate(32 30) scale(.8) translate(-32 -33)"/></g></svg>`;

function renderPanel() {
  const f = state.field, p = f.properties, L = t(), c = state.check;
  const village = lang === "en" ? p.village : p.village_hi || p.village;
  let html = `<div class="head"><h2>${esc(fieldName(p))}</h2><p class="sub">${p.acres} ${esc(L.acres)} · ${esc(village)}</p></div>`;
  if (c && c.status === "done") {
    const cur = c.result.current, prev = c.result.previous, d = cur.decision, k = kindOf(d.outcome), kp = kindOf(prev.decision.outcome);
    const after = d.burn_date ? windows[windowIndex(dayNum(d.burn_date))] : windows[4];
    const vline = k === "burn" ? L.vline.burn(fmtIso(d.burn_date)) : k === "clean" ? L.vline.clean(d.clear_dates.length) : L.vline.review();
    html += `<div class="compare" id="compare"><canvas class="before"></canvas><canvas class="after"></canvas><div class="handle"></div>
        <input type="range" min="0" max="100" value="50" aria-label="Before and after">
        <span class="tag l">${esc(fmtRange(windows[0]))}</span><span class="tag r">${esc(fmtRange(after))}</span></div>
      <div class="band ${k}"><div class="ic">${icon(ICON[k])}</div><div><b>${esc(L.v[k])}</b><p>${esc(vline)}</p></div></div>
      <div class="sec"><h3>${esc(L.signal)}</h3>${signalSvg(cur.series, d.burn_date)}<p class="cap">${esc(L.signalNote)}</p></div>
      <div class="sec"><dl class="facts"><div><dt>${esc(L.clear)}</dt><dd>${d.clear_dates.length}</dd></div>
        <div><dt>${esc(L.nearest)}</dt><dd>${cur.fires.length || esc(L.none)}</dd></div></dl></div>
      <div class="sec"><div class="last"><span class="mini ${kp}">${icon(ICON[kp])}</span><span>${esc(L.last)}: <b>${esc(L.v[kp])}</b></span></div></div>
      <div class="foot"><span>${c.checked_at ? esc(L.checked(fmtIso(c.checked_at))) : ""}</span><button class="btn ghost small" id="run-check">${esc(L.again)}</button></div>`;
  } else if (c && c.status !== "done" && !c.failed) {
    const s = Math.min(c.step || 0, L.steps.length - 1);
    html += `<div class="scanning">${SCAN_SVG}<p>${esc(L.steps[s])}</p><div class="dots">${L.steps.map((_, j) => `<i class="${j <= s ? "on" : ""}"></i>`).join("")}</div></div>`;
  } else {
    html += `<div class="sec">${c && c.failed ? `<p class="err">${esc(L.err)}</p>` : ""}<button class="btn primary wide" id="run-check">${icon("i-scan")}<span>${esc(L.check)}</span></button></div>`;
  }
  $("#panel-body").innerHTML = html;
  $("#run-check")?.addEventListener("click", runCheck);
  const cmp = $("#compare");
  if (cmp) {
    const d = c.result.current.decision, after = d.burn_date ? windows[windowIndex(dayNum(d.burn_date))] : windows[4];
    drawCut($(".before", cmp), windows[0].id, f.geometry);
    drawCut($(".after", cmp), after.id, f.geometry);
    $("input", cmp).oninput = (e) => cmp.style.setProperty("--cut", `${e.target.value}%`);
  }
}

async function runCheck() {
  const f = state.field;
  state.check = { status: "queued", step: 0 };
  renderPanel();
  const stepper = setInterval(() => {
    if (!state.check || state.check.status === "done" || state.field !== f) return clearInterval(stepper);
    state.check.step = Math.min((state.check.step || 0) + 1, t().steps.length - 1);
    renderPanel();
  }, 4200);
  try {
    const r = await fetch("/api/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ geometry: f.geometry }) });
    if (!r.ok) throw new Error(String(r.status));
    const { id } = await r.json();
    for (let k = 0; k < 60 && state.field === f; k++) {
      await new Promise((ok) => setTimeout(ok, 2000));
      const item = await (await fetch(`/api/check/${id}`)).json();
      if (item.status === "done" || item.status === "error") {
        clearInterval(stepper);
        if (state.field === f) { state.check = item.status === "done" ? { ...item, checked_at: item.done_at } : { failed: true }; renderPanel(); }
        return;
      }
    }
    throw new Error("timeout");
  } catch {
    clearInterval(stepper);
    if (state.field === f) { state.check = { failed: true }; renderPanel(); }
  }
}

// ---- map ----
function diamondImage(size = 22) {
  const c = document.createElement("canvas");
  c.width = c.height = size * 2;
  const g = c.getContext("2d"), m = size, r = size * 0.62;
  g.beginPath(); g.moveTo(m, m - r); g.lineTo(m + r, m); g.lineTo(m, m + r); g.lineTo(m - r, m); g.closePath();
  g.fillStyle = "rgba(245,197,66,0.28)"; g.fill();
  g.lineWidth = size * 0.3; g.strokeStyle = "rgba(0,0,0,0.65)"; g.stroke();
  g.lineWidth = size * 0.16; g.strokeStyle = "#F5C542"; g.stroke();
  return { width: c.width, height: c.height, data: g.getImageData(0, 0, c.width, c.height).data };
}

async function init() {
  const [mf, demoChecks] = await Promise.all([
    fetch("/tiles/manifest.json").then((r) => r.json()),
    fetch("data/demo_checks.json").then((r) => (r.ok ? r.json() : {})).catch(() => ({})),
  ]);
  manifest = mf; demo = demoChecks;
  windows = manifest.windows;
  day0 = new Date(manifest.day0);
  D0 = dayNum(windows[0].start); D1 = dayNum(windows.at(-1).end);
  centers = windows.map((w) => (dayNum(w.start) + dayNum(w.end)) / 2);
  let acc = 0;
  cumHa = Array.from({ length: D1 - D0 + 1 }, (_, i) => (acc += manifest.burn_ha_by_day[D0 + i] || 0));
  state.day = D0;
  buildSpark();

  const intro = params.get("intro") === "1" || (params.get("intro") !== "0" && !store.get("saakshi-intro") && !reduced);
  map = new maplibregl.Map({
    container: "map", attributionControl: false, maxZoom: 17.5, minZoom: 3,
    ...(intro ? INDIA : { bounds: regionBounds(), fitBoundsOptions: { padding: 60 } }),
    style: {
      version: 8,
      sources: {
        esri: { type: "raster", tileSize: 256, maxzoom: 18,
          tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"] },
        labels: { type: "raster", tileSize: 256, maxzoom: 13,
          tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"] },
      },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": "#0D0E11" } },
        { id: "esri", type: "raster", source: "esri", paint: {
          "raster-saturation": ["interpolate", ["linear"], ["zoom"], 9, -0.7, 13, -0.55, 15, 0],
          "raster-brightness-max": ["interpolate", ["linear"], ["zoom"], 5, 0.62, 9, 0.42, 13, 0.4, 15, 1],
          "raster-contrast": ["interpolate", ["linear"], ["zoom"], 13, -0.15, 15, 0] } },
      ],
    },
  });
  window.saakshi = { map, state };
  const data = Promise.all([
    fetch("data/region.geojson").then((r) => r.json()),
    fetch("data/states.geojson").then((r) => r.json()),
    fetch("/tiles/fires.geojson").then((r) => r.json()),
    fetch("/tiles/fires_states.geojson").then((r) => r.json()).catch(() => ({ type: "FeatureCollection", features: [] })),
    fetch("/api/fields").then((r) => (r.ok ? r.json() : [])).catch(() => []),
  ]);
  map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution:
    "Our tiles: Copernicus Sentinel-2 (ESA) via AWS Open Data · Fire alerts: NASA FIRMS · Basemap, labels and close-up photo: Esri, Maxar, Earthstar Geographics · Boundaries © OpenStreetMap contributors" }), "bottom-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric", maxWidth: 110 }), "bottom-left");
  setTimeout(() => $$(".maplibregl-ctrl-attrib").forEach((el) => el.classList.remove("maplibregl-compact-show")), 0);

  // isStyleLoaded() also waits for basemap tiles, and style.load can fire before we listen: poll the style itself
  while (!(map.style && map.style._loaded)) await new Promise((ok) => setTimeout(ok, 30));
  const [region, states, firesFc, stateFires, fieldsList] = await data;
  beltFires = firesFc.features;
  let fa = 0;
  const byDay = {};
  beltFires.forEach((f) => { byDay[f.properties.d] = (byDay[f.properties.d] || 0) + 1; });
  cumFires = Array.from({ length: D1 - D0 + 1 }, (_, i) => (fa += byDay[D0 + i] || 0));
  map.addImage("diamond", diamondImage(), { pixelRatio: 2 });

  // high-density screens and in-between zooms stretch 256 px tiles: ask for the next zoom's tiles instead
  windows.forEach((w) => {
    map.addSource(`img-${w.id}`, { type: "raster", tileSize: 128, minzoom: manifest.minzoom, maxzoom: manifest.maxzoom, bounds: manifest.bounds,
      tiles: [`${location.origin}/tiles/${w.id}/{z}/{x}/{y}.webp`] });
    map.addLayer({ id: `img-${w.id}`, type: "raster", source: `img-${w.id}`, layout: { visibility: "none" },
      paint: { "raster-opacity": 0, "raster-opacity-transition": { duration: 0 }, "raster-fade-duration": 120 } });
  });
  map.addSource("region", { type: "geojson", data: region });
  map.addLayer({ id: "region", type: "line", source: "region", paint: { "line-color": "#FFFFFF", "line-opacity": 0.55, "line-width": 1.1 } });
  const [bw, bs, be, bn] = STUDY_BOX;
  map.addSource("study", { type: "geojson", data: { type: "Feature", geometry: { type: "Polygon", coordinates: [[[bw, bs], [be, bs], [be, bn], [bw, bn], [bw, bs]]] } } });
  map.addLayer({ id: "study", type: "line", source: "study", minzoom: 8, paint: { "line-color": "#FFFFFF", "line-opacity": 0.8, "line-width": 1.2, "line-dasharray": [3, 3] } });

  map.addSource("burns", { type: "geojson", data: "/tiles/burns.geojson" });
  map.addLayer({ id: "burns", type: "fill", source: "burns", paint: {
    "fill-color": ["interpolate", ["linear"], ["get", "d"], ...BURN_RAMP.flat()],
    "fill-opacity": ["interpolate", ["linear"], ["zoom"], 9, 0.95, 14, 0.7, 16, 0.3] } });
  map.addLayer({ id: "burns-new", type: "line", source: "burns", paint: { "line-color": "#FFFFFF",
    "line-width": ["interpolate", ["linear"], ["zoom"], 9, 1, 14, 2.2], "line-blur": 0.6, "line-opacity": 0.85 } });

  map.addSource("fires-states", { type: "geojson", data: stateFires });
  map.addLayer({ id: "fires-states", type: "circle", source: "fires-states", maxzoom: 9.5, paint: {
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 0.7, 6, 1.4, 9, 2.2],
    "circle-color": "#F5C542", "circle-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.7, 8.5, 0.6, 9.5, 0] } });
  map.addSource("fires", { type: "geojson", data: firesFc });
  map.addLayer({ id: "fires", type: "symbol", source: "fires", minzoom: 8.5, layout: {
    "icon-image": "diamond", "icon-allow-overlap": true, "icon-ignore-placement": true, "icon-size": 0.62 },
    paint: { "icon-opacity": ["interpolate", ["linear"], ["zoom"], 8.5, 0, 9.5, 1] } });

  map.addLayer({ id: "labels", type: "raster", source: "labels", paint: {
    "raster-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.95, 11, 0.85, 12.5, 0] } });
  map.addSource("states", { type: "geojson", data: states });
  map.addLayer({ id: "states", type: "line", source: "states", maxzoom: 11, paint: { "line-color": "#FFFFFF", "line-opacity": 0.35, "line-width": 1, "line-dasharray": [4, 3] } });

  const fieldsFc = { type: "FeatureCollection", features: fieldsList.map(({ geometry, ...p }) => ({ type: "Feature", id: p.id, properties: p, geometry })) };
  fieldsFc.features.forEach((f) => { fieldsById[f.properties.id] = f; });
  const kindFor = (id) => (demo[id] ? kindOf(demo[id].result.current.decision.outcome) : "none");
  const dotsFc = { type: "FeatureCollection", features: fieldsFc.features.map((f) => ({ type: "Feature", properties: { id: f.properties.id, k: kindFor(f.properties.id) }, geometry: { type: "Point", coordinates: centroid(f.geometry) } })) };
  map.addSource("fields", { type: "geojson", data: fieldsFc });
  map.addSource("field-dots", { type: "geojson", data: dotsFc });
  map.addLayer({ id: "fields-hit", type: "fill", source: "fields", minzoom: 12.5, paint: { "fill-color": "#FFFFFF", "fill-opacity": 0.04 } });
  map.addLayer({ id: "fields", type: "line", source: "fields", minzoom: 12.5, paint: { "line-color": "#FFFFFF", "line-width": ["interpolate", ["linear"], ["zoom"], 12.5, 1.2, 15, 2.5] } });
  const dotColor = ["match", ["get", "k"], "clean", "#43C485", "burn", "#FF6A3D", "review", "#F5C542", "#FFFFFF"];
  map.addLayer({ id: "field-dots-halo", type: "circle", source: "field-dots", minzoom: 7.5, maxzoom: 12.5, paint: {
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 7, 12, 12], "circle-color": dotColor, "circle-opacity": 0.22, "circle-blur": 0.4 } });
  map.addLayer({ id: "field-dots", type: "circle", source: "field-dots", minzoom: 7.5, maxzoom: 12.5, paint: {
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3.5, 12, 5.5], "circle-color": dotColor,
    "circle-stroke-color": "#0D0E11", "circle-stroke-width": 1.5 } });

  const pins = fieldsFc.features.map((f) => {
    const el = document.createElement("button");
    el.className = "pin";
    el.onclick = (e) => { e.stopPropagation(); openField(f); };
    return { f, el, m: new maplibregl.Marker({ element: el, anchor: "left", offset: [14, 0] }).setLngLat(centroid(f.geometry)) };
  });
  syncPins = () => pins.forEach(({ f, el, m }) => {
    // classList, not className: the map keeps its own positioning classes on the marker element
    el.classList.remove("clean", "burn", "review", "none");
    el.classList.add("pin", kindFor(f.properties.id));
    el.lang = HTML_LANG[lang];
    el.innerHTML = `<i></i>${esc(fieldName(f.properties))}`;
    if (map.getZoom() >= 12.5 && state.layers.fields) m.addTo(map); else m.remove();
  });
  Object.assign(window.saakshi, { pins, syncPins });

  delhiMarker = new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "delhi" }), anchor: "left", offset: [-6, 0] }).setLngLat(DELHI).addTo(map);
  delhiMarker.getElement().innerHTML = delhiHtml();
  studyMarker = new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "study-label" }), anchor: "bottom-left", offset: [0, -4] }).setLngLat([bw, bn]);
  const stateLabels = [["PUNJAB", [75.35, 30.95]], ["HARYANA", [76.25, 29.0]]].map(([name, at]) =>
    new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "state-label", textContent: name }) }).setLngLat(at));
  const onZoom = () => {
    const z = map.getZoom();
    syncPins();
    delhiMarker.getElement().style.display = z < 10.5 ? "" : "none";
    if (z >= 8.5 && z < 12.5) studyMarker.addTo(map); else studyMarker.remove();
    stateLabels.forEach((m) => (z >= 5.5 && z < 9.5 ? m.addTo(map) : m.remove()));
    $("#refchip").hidden = z < 14.6;
  };
  map.on("zoom", onZoom);
  applyLang();
  onZoom();

  const tip = $("#tip");
  map.on("click", "fields-hit", (e) => openField(fieldsById[e.features[0].properties.id]));
  map.on("click", "field-dots", (e) => openField(fieldsById[e.features[0].properties.id]));
  map.on("mousemove", "field-dots", (e) => {
    map.getCanvas().style.cursor = "pointer";
    const p = fieldsById[e.features[0].properties.id].properties;
    tip.textContent = `${fieldName(p)} · ${p.acres} ${t().acres}`;
    tip.hidden = false;
    tip.style.left = `${e.originalEvent.clientX + 14}px`;
    tip.style.top = `${e.originalEvent.clientY - 12}px`;
  });
  map.on("mouseleave", "field-dots", () => { map.getCanvas().style.cursor = ""; tip.hidden = true; });
  map.on("mouseenter", "fields-hit", () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", "fields-hit", () => { map.getCanvas().style.cursor = ""; });

  // controls
  $("#play").onclick = () => { state.intro = false; hideHero(); state.playing ? stop() : play(6); };
  $("#slider").oninput = (e) => { state.intro = false; stop(); setDay(Number(e.target.value)); };
  $("#play-season").onclick = playSeason;
  $("#explore").onclick = () => { hideHero(); toast(t().toast); };
  $("#panel-close").onclick = closePanel;
  $("#zoom-in").onclick = () => map.zoomIn();
  $("#zoom-out").onclick = () => map.zoomOut();
  $("#zoom-fit").onclick = () => { closePanel(); fitRegion(900); };
  const setLayer = (k, on) => {
    state.layers[k] = on;
    const b = $(`.layers [data-layer="${k}"]`);
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", on);
    if (k === "missed") {
      // dim the patches a fire alert came within 375 m of; what stays lit is what the alerts missed
      map.setPaintProperty("burns", "fill-opacity", on ? ["case", ["==", ["get", "a"], 1], 0.12, 0.95]
        : ["interpolate", ["linear"], ["zoom"], 9, 0.95, 14, 0.7, 16, 0.3]);
      if (on && !state.layers.burns) setLayer("burns", true);
      return;
    }
    const ids = k === "burns" ? ["burns", "burns-new"] : k === "fires" ? ["fires", "fires-states"] : ["fields", "fields-hit", "field-dots", "field-dots-halo"];
    ids.forEach((id) => map.setLayoutProperty(id, "visibility", on ? "visible" : "none"));
    syncPins();
  };
  $$(".layers button").forEach((b) => {
    b.onclick = () => setLayer(b.dataset.layer, !state.layers[b.dataset.layer]);
    b.onmouseenter = () => { const r = b.getBoundingClientRect(); tip.textContent = t()[b.dataset.tip]; tip.hidden = false; tip.style.left = `${r.left - tip.offsetWidth - 10}px`; tip.style.top = `${r.top + 6}px`; requestAnimationFrame(() => { tip.style.left = `${r.left - tip.offsetWidth - 10}px`; }); };
    b.onmouseleave = () => { tip.hidden = true; };
  });
  const menu = $("#lang-menu"), btn = $("#lang-btn");
  const openMenu = (open) => { menu.hidden = !open; btn.setAttribute("aria-expanded", open); };
  btn.onclick = (e) => { e.stopPropagation(); openMenu(menu.hidden); };
  $$("#lang-menu li").forEach((li) => {
    li.tabIndex = 0;
    li.onclick = () => { lang = li.dataset.lang; store.set("saakshi-lang", lang); applyLang(); openMenu(false); };
    li.onkeydown = (e) => { if (e.key === "Enter") li.click(); };
  });
  addEventListener("click", () => openMenu(false));
  addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea")) return;
    if (e.key === " ") { e.preventDefault(); $("#play").click(); }
    if (e.key === "ArrowRight") { stop(); setDay(state.day + (e.shiftKey ? 10 : 1)); }
    if (e.key === "ArrowLeft") { stop(); setDay(state.day - (e.shiftKey ? 10 : 1)); }
    if (e.key === "Escape") { closePanel(); openMenu(false); }
  });
  addEventListener("resize", () => { if (state.intro && !intro) fitRegion(0); });

  setDay(D0);
  let started = false;
  const ready = new Promise((ok) => {
    const go = () => { if (started) return; started = true; $("#loader").classList.add("gone"); setTimeout(() => $("#loader")?.remove(), 700); ok(); };
    map.on("idle", go);
    setTimeout(go, 4500);  // never hold the page hostage to the slowest tile
  });
  if (intro) { ready.then(runIntro); return; }
  if (reduced) { ready.then(() => { setDay(D0 + 42); showHero(); }); return; }
  map.once("dragstart", () => { if (state.intro) { stop(); showHero(); } });
  ready.then(() => setTimeout(() => play(9, () => { if (state.intro) { setDay(D0 + 42); showHero(); toast(t().toast); } }, D0), 500));
}

init().catch((e) => {
  document.body.insertAdjacentHTML("beforeend", `<p class="err" style="position:fixed;top:90px;left:16px;z-index:9">Map failed to load: ${esc(e.message)}</p>`);
});
