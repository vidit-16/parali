// Saakshi explorer: the season over the Patiala-Kaithal border belt, from our own Sentinel-2 tiles.
// Burn patches are burn-like ground seen by the satellite; decisions on fields come from the rules and an officer.

// ?frames=timer: drive animation frames from a timer, for headless screenshots where the tab is hidden
if (new URLSearchParams(location.search).get("frames") === "timer") {
  window.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16);
  window.cancelAnimationFrame = (id) => clearTimeout(id);
}

const T = {
  // Punjabi (pa) and Haryanvi (hr) are drafts and need a native speaker's review.
  en: {
    loading: "Loading the season from orbit", explore: "Explore", officer: "Officer", farmer: "Farmer",
    kicker: "Patiala–Kaithal border belt · kharif 2025",
    headline: "<em>9 in 10</em> hectares that looked burnt got no fire alert.",
    alerts: "Fire alerts", vscap: "Clean fields wrongly flagged, on 314 fields checked by hand",
    play: "Play the season", explorebtn: "Explore the map",
    fine: "Burn-like ground seen by Sentinel-2. Every flag goes to an officer.",
    l_burns: "Burns", l_fires: "Fire alerts", l_fields: "Fields", ha: "ha burn-like", fa: "fire alerts",
    stages: ["Standing paddy", "Harvest begins", "Harvest", "Stubble", "Peak burning", "Burning tails off", "Wheat sowing", "Wheat up"],
    check: "Run the satellite check", steps: ["Finding every clear image", "Removing clouds", "Comparing dates", "Checking fire alerts"],
    v: { clean: "Clean", review: "With the officer", burn: "Possible burn" },
    reading: "Satellite reading", decides: "The satellite reports. A village officer decides.",
    pay: "No-burn payment", before: "before harvest", after: "after the check", noadv: "all after the check",
    s25: "This season · 2025", s24: "Last season · 2024", images: "See the images",
    burnOn: (d) => `Burn signature on ${d}`, cleanAll: (n) => `Clean in all ${n} clear images`,
    fires: (n) => n ? `${n} fire alert${n > 1 ? "s" : ""} within 375 m` : "no fire alert within 375 m",
    acres: "acres", err: "The check did not finish. Try again.",
    advYes: "Clean last season, so half is paid before harvest.", advNo: "Last season was not clearly clean, so it is all paid after the check.",
  },
  hi: {
    loading: "उपग्रह से सीज़न ला रहे हैं", explore: "देखें", officer: "अधिकारी", farmer: "किसान",
    kicker: "पटियाला–कैथल सीमा क्षेत्र · खरीफ़ 2025",
    headline: "जले दिखने वाले हर <em>10 में से 9</em> हेक्टेयर पर आग का कोई अलर्ट नहीं आया।",
    alerts: "आग अलर्ट", vscap: "साफ़ खेत जिन्हें गलती से संदिग्ध बताया, हाथ से जाँचे 314 खेतों पर",
    play: "पूरा सीज़न देखें", explorebtn: "नक्शा देखें",
    fine: "Sentinel-2 उपग्रह को जले जैसी दिखी ज़मीन। हर संदेह अधिकारी के पास जाता है।",
    l_burns: "जले खेत", l_fires: "आग अलर्ट", l_fields: "खेत", ha: "हेक्टेयर जले जैसे", fa: "आग अलर्ट",
    stages: ["खड़ा धान", "कटाई शुरू", "कटाई", "पराली", "सबसे ज़्यादा जलना", "जलना घटा", "गेहूँ बुआई", "गेहूँ उगा"],
    check: "उपग्रह जाँच चलाएँ", steps: ["हर साफ़ तस्वीर ढूँढ रहे हैं", "बादल हटा रहे हैं", "तारीखें मिला रहे हैं", "आग अलर्ट जाँच रहे हैं"],
    v: { clean: "साफ़", review: "अधिकारी के पास", burn: "जलने की आशंका" },
    reading: "उपग्रह की रिपोर्ट", decides: "उपग्रह बताता है। फ़ैसला ग्राम अधिकारी करते हैं।",
    pay: "न जलाने की राशि", before: "कटाई से पहले", after: "जाँच के बाद", noadv: "पूरी राशि जाँच के बाद",
    s25: "यह सीज़न · 2025", s24: "पिछला सीज़न · 2024", images: "तस्वीरें देखें",
    burnOn: (d) => `${d} को जलने का निशान`, cleanAll: (n) => `सभी ${n} साफ़ तस्वीरों में साफ़`,
    fires: (n) => n ? `375 मीटर के अंदर ${n} आग अलर्ट` : "375 मीटर के अंदर कोई आग अलर्ट नहीं",
    acres: "एकड़", err: "जाँच पूरी नहीं हुई। फिर कोशिश करें।",
    advYes: "पिछला सीज़न साफ़ था, इसलिए आधी राशि कटाई से पहले।", advNo: "पिछला सीज़न साफ़ नहीं दिखा, इसलिए पूरी राशि जाँच के बाद।",
  },
  pa: {
    loading: "ਉਪਗ੍ਰਹਿ ਤੋਂ ਸੀਜ਼ਨ ਲਿਆ ਰਹੇ ਹਾਂ", explore: "ਵੇਖੋ", officer: "ਅਧਿਕਾਰੀ", farmer: "ਕਿਸਾਨ",
    kicker: "ਪਟਿਆਲਾ–ਕੈਥਲ ਸਰਹੱਦੀ ਖੇਤਰ · ਸਾਉਣੀ 2025",
    headline: "ਸੜੇ ਦਿਸਦੇ ਹਰ <em>10 ਵਿੱਚੋਂ 9</em> ਹੈਕਟੇਅਰ ਲਈ ਕੋਈ ਅੱਗ ਅਲਰਟ ਨਹੀਂ ਆਇਆ।",
    alerts: "ਅੱਗ ਅਲਰਟ", vscap: "ਸਾਫ਼ ਖੇਤ ਜਿਨ੍ਹਾਂ ਨੂੰ ਗਲਤੀ ਨਾਲ ਸ਼ੱਕੀ ਕਿਹਾ, ਹੱਥੀਂ ਜਾਂਚੇ 314 ਖੇਤਾਂ ਉੱਤੇ",
    play: "ਪੂਰਾ ਸੀਜ਼ਨ ਵੇਖੋ", explorebtn: "ਨਕਸ਼ਾ ਵੇਖੋ",
    fine: "Sentinel-2 ਉਪਗ੍ਰਹਿ ਨੂੰ ਸੜੀ ਵਰਗੀ ਦਿਸੀ ਜ਼ਮੀਨ। ਹਰ ਸ਼ੱਕ ਅਧਿਕਾਰੀ ਕੋਲ ਜਾਂਦਾ ਹੈ।",
    l_burns: "ਸੜੇ ਖੇਤ", l_fires: "ਅੱਗ ਅਲਰਟ", l_fields: "ਖੇਤ", ha: "ਹੈਕਟੇਅਰ ਸੜੇ ਵਰਗੇ", fa: "ਅੱਗ ਅਲਰਟ",
    stages: ["ਖੜ੍ਹਾ ਝੋਨਾ", "ਵਾਢੀ ਸ਼ੁਰੂ", "ਵਾਢੀ", "ਪਰਾਲੀ", "ਸਭ ਤੋਂ ਵੱਧ ਸਾੜ", "ਸਾੜ ਘਟਿਆ", "ਕਣਕ ਦੀ ਬਿਜਾਈ", "ਕਣਕ ਉੱਗੀ"],
    check: "ਉਪਗ੍ਰਹਿ ਜਾਂਚ ਚਲਾਓ", steps: ["ਹਰ ਸਾਫ਼ ਤਸਵੀਰ ਲੱਭ ਰਹੇ ਹਾਂ", "ਬੱਦਲ ਹਟਾ ਰਹੇ ਹਾਂ", "ਤਾਰੀਖਾਂ ਮਿਲਾ ਰਹੇ ਹਾਂ", "ਅੱਗ ਅਲਰਟ ਜਾਂਚ ਰਹੇ ਹਾਂ"],
    v: { clean: "ਸਾਫ਼", review: "ਅਧਿਕਾਰੀ ਕੋਲ", burn: "ਸਾੜ ਦਾ ਸ਼ੱਕ" },
    reading: "ਉਪਗ੍ਰਹਿ ਦੀ ਰਿਪੋਰਟ", decides: "ਉਪਗ੍ਰਹਿ ਦੱਸਦਾ ਹੈ। ਫ਼ੈਸਲਾ ਪਿੰਡ ਦਾ ਅਧਿਕਾਰੀ ਕਰਦਾ ਹੈ।",
    pay: "ਨਾ ਸਾੜਨ ਦੀ ਰਕਮ", before: "ਵਾਢੀ ਤੋਂ ਪਹਿਲਾਂ", after: "ਜਾਂਚ ਤੋਂ ਬਾਅਦ", noadv: "ਪੂਰੀ ਰਕਮ ਜਾਂਚ ਤੋਂ ਬਾਅਦ",
    s25: "ਇਹ ਸੀਜ਼ਨ · 2025", s24: "ਪਿਛਲਾ ਸੀਜ਼ਨ · 2024", images: "ਤਸਵੀਰਾਂ ਵੇਖੋ",
    burnOn: (d) => `${d} ਨੂੰ ਸਾੜ ਦਾ ਨਿਸ਼ਾਨ`, cleanAll: (n) => `ਸਾਰੀਆਂ ${n} ਸਾਫ਼ ਤਸਵੀਰਾਂ ਵਿੱਚ ਸਾਫ਼`,
    fires: (n) => n ? `375 ਮੀਟਰ ਅੰਦਰ ${n} ਅੱਗ ਅਲਰਟ` : "375 ਮੀਟਰ ਅੰਦਰ ਕੋਈ ਅੱਗ ਅਲਰਟ ਨਹੀਂ",
    acres: "ਏਕੜ", err: "ਜਾਂਚ ਪੂਰੀ ਨਹੀਂ ਹੋਈ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
    advYes: "ਪਿਛਲਾ ਸੀਜ਼ਨ ਸਾਫ਼ ਸੀ, ਇਸ ਲਈ ਅੱਧੀ ਰਕਮ ਵਾਢੀ ਤੋਂ ਪਹਿਲਾਂ।", advNo: "ਪਿਛਲਾ ਸੀਜ਼ਨ ਸਾਫ਼ ਨਹੀਂ ਦਿਸਿਆ, ਇਸ ਲਈ ਪੂਰੀ ਰਕਮ ਜਾਂਚ ਤੋਂ ਬਾਅਦ।",
  },
  hr: {
    loading: "उपग्रह तै सीज़न ल्यावां सां", explore: "देक्खो", officer: "अफसर", farmer: "किसान",
    kicker: "पटियाला–कैथल बॉर्डर इलाका · खरीफ़ 2025",
    headline: "जळे दिक्खण आळे हर <em>10 म्ह तै 9</em> हेक्टेयर पै कोए आग का अलर्ट कोनी आया।",
    alerts: "आग अलर्ट", vscap: "साफ खेत जिन पै गलती तै शक करया, हाथ तै जांचे 314 खेतां पै",
    play: "पूरा सीज़न देक्खो", explorebtn: "नक्सा देक्खो",
    fine: "Sentinel-2 नै जळी बरगी दिक्खी धरती। हर शक अफसर कनै जावै सै।",
    l_burns: "जळे खेत", l_fires: "आग अलर्ट", l_fields: "खेत", ha: "हेक्टेयर जळे बरगे", fa: "आग अलर्ट",
    stages: ["खड़या धान", "कटाई शुरू", "कटाई", "पराळी", "सब तै घणा जळाणा", "जळाणा घटया", "गेहूं की बिजाई", "गेहूं उग्या"],
    check: "उपग्रह जांच चलाओ", steps: ["हर साफ फोटो टोहण लाग रे सां", "बादळ हटाण लाग रे सां", "तारीख मिलाण लाग रे सां", "आग अलर्ट जांचण लाग रे सां"],
    v: { clean: "साफ", review: "अफसर कनै", burn: "जळण का शक" },
    reading: "उपग्रह की रपट", decides: "उपग्रह बतावै सै। फैसला गाम का अफसर करै सै।",
    pay: "ना जळाण की रकम", before: "कटाई तै पहल्यां", after: "जांच के पाच्छै", noadv: "पूरी रकम जांच के पाच्छै",
    s25: "यो सीज़न · 2025", s24: "पाछला सीज़न · 2024", images: "फोटू देक्खो",
    burnOn: (d) => `${d} नै जळण का निसान`, cleanAll: (n) => `सारी ${n} साफ फोटुआं म्ह साफ`,
    fires: (n) => n ? `375 मीटर भीतर ${n} आग अलर्ट` : "375 मीटर भीतर कोए आग अलर्ट कोनी",
    acres: "किल्ले", err: "जांच पूरी कोनी होई। फेर कोसिस करो।",
    advYes: "पाछला सीज़न साफ था, इस करकै आधी रकम कटाई तै पहल्यां।", advNo: "पाछला सीज़न साफ कोनी दिख्या, इस करकै पूरी रकम जांच के पाच्छै।",
  },
};
const HTML_LANG = { en: "en", hi: "hi", pa: "pa", hr: "hi" };
const LOCALE = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", hr: "hi-IN" };
const LOCAL_NAME = { en: ["साक्षी", "hi"], hi: ["साक्षी", "hi"], hr: ["साक्षी", "hi"], pa: ["ਸਾਕਸ਼ੀ", "pa"] };
const CODE = { en: "EN", hi: "हिं", pa: "ਪੰ", hr: "हरि" };
const RATE_PER_ACRE = 1000, ADVANCE_SHARE = 0.5; // season.SCHEMES: Haryana's rate, half before harvest
// Burn colours run orange to purple by date. Yellow is kept for NASA fire alerts only.
const BURN_RAMP = [[30, "#FF9D5C"], [50, "#FF6A3D"], [62, "#E8384F"], [80, "#C2187E"], [100, "#7B2CBF"]];

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const rupees = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const icon = (id) => `<svg><use href="#${id}"/></svg>`;

let lang = "en";
try { lang = localStorage.getItem("saakshi-lang") || (navigator.language.startsWith("hi") ? "hi" : navigator.language.startsWith("pa") ? "pa" : "en"); } catch { /* storage blocked */ }
if (!T[lang]) lang = "en";
const t = () => T[lang];

const state = { i: 0, playing: false, timer: null, layers: { burns: true, fires: true, fields: true }, intro: true, field: null, check: null, verdicts: {} };
let map, manifest, fires = [], windows = [], day0, syncPins = () => {};

// ---- language ----
function applyLang() {
  document.documentElement.lang = HTML_LANG[lang];
  $$("[data-i18n]").forEach((el) => { const v = t()[el.dataset.i18n]; if (typeof v === "string") el.innerHTML = v; });
  const [local, script] = LOCAL_NAME[lang];
  $("#name-local").textContent = local;
  $("#name-local").lang = script;
  $("#lang-cur").textContent = CODE[lang];
  $$("#lang-menu li").forEach((li) => { li.classList.toggle("on", li.dataset.lang === lang); li.setAttribute("aria-selected", li.dataset.lang === lang); });
  renderTimeline();
  if (state.field) renderPanel();
}
function setLang(l) {
  lang = l;
  try { localStorage.setItem("saakshi-lang", lang); } catch { /* storage blocked */ }
  applyLang();
  syncPins();
}

// ---- dates ----
function dayNum(iso) { return Math.round((new Date(iso) - day0) / 864e5); }
// Indian-language locales abbreviate months oddly ("नव॰"), so they get the full name
const MONTH = () => (lang === "en" ? "short" : "long");
function fmtRange(w, month = MONTH()) {
  const s = new Date(w.start), e = new Date(w.end);
  return `${s.getDate()}–${e.getDate()} ${e.toLocaleDateString(LOCALE[lang], { month })}`;
}
function fmtDay(iso) { return new Date(iso).toLocaleDateString(LOCALE[lang], { day: "numeric", month: "long" }); }

// ---- timeline ----
function buildSpark() {
  const svg = $("#spark"), d0 = dayNum(windows[0].start), d1 = dayNum(windows.at(-1).end);
  const byDay = manifest.burn_ha_by_day, max = Math.max(...Object.values(byDay));
  const W = 1000, H = 30, span = d1 - d0 + 1, bw = W / span;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const grad = BURN_RAMP.map(([d, c]) => `<stop offset="${Math.max(0, (d - d0) / span)}" stop-color="${c}"/>`).join("");
  let bars = "";
  for (const [d, ha] of Object.entries(byDay)) {
    const x = (Number(d) - d0) * bw, h = Math.max(1.5, Math.sqrt(ha / max) * H);
    bars += `<rect x="${x.toFixed(1)}" y="${(H - h).toFixed(1)}" width="${Math.max(2, bw - 1.5).toFixed(1)}" height="${h.toFixed(1)}" rx="1"/>`;
  }
  svg.innerHTML = `<defs><linearGradient id="sparkg" x1="0" x2="1">${grad}</linearGradient>
    <clipPath id="sparkclip"><rect id="sparkcut" x="0" y="-2" width="0" height="${H + 4}"/></clipPath></defs>
    <g class="base">${bars}</g><g fill="url(#sparkg)" clip-path="url(#sparkclip)">${bars}</g>`;
  $("#scrub").insertAdjacentHTML("beforeend", `<div class="thumb" id="thumb"></div>`);
}

function renderTimeline() {
  if (!windows.length) return;
  const w = windows[state.i], n = windows.length, frac = (state.i + 1) / n;
  $("#when").textContent = fmtRange(w);
  $("#stage").textContent = t().stages[state.i];
  $("#ticks").innerHTML = windows.map((x, j) => {
    const s = new Date(x.start), lab = j === 0 || s.getDate() === 1 ? `${s.getDate()} ${s.toLocaleDateString(LOCALE[lang], { month: MONTH() })}` : String(s.getDate());
    return `<span class="${j === state.i ? "now" : ""}">${esc(lab)}</span>`;
  }).join("");
  const cut = $("#sparkcut");
  if (cut) cut.setAttribute("width", String(frac * 1000));
  const th = $("#thumb");
  if (th) th.style.left = `${frac * 100}%`;
  $("#slider").value = state.i;
  $("#ring").style.strokeDashoffset = String(157 * (1 - frac));
}

function countTo(el, to) {
  const from = Number(el.dataset.v || 0);
  el.dataset.v = to;
  if (reduced) { el.textContent = Math.round(to).toLocaleString("en-IN"); return; }
  const t0 = performance.now(), dur = 600;
  const step = (now) => {
    const k = Math.min(1, (now - t0) / dur), v = from + (to - from) * (1 - Math.pow(1 - k, 3));
    el.textContent = Math.round(v).toLocaleString("en-IN");
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function show(i) {
  const prevEnd = state.i === i ? -1 : dayNum(windows[state.i].end);
  state.i = i;
  const end = dayNum(windows[i].end);
  windows.forEach((w, j) => map.setPaintProperty(`img-${w.id}`, "raster-opacity", ["interpolate", ["linear"], ["zoom"], 14.3, j === i ? 1 : 0, 15.3, 0]));
  map.setFilter("burns", ["<=", ["get", "d"], end]);
  map.setFilter("burns-new", ["all", [">", ["get", "d"], prevEnd < end ? prevEnd : -1], ["<=", ["get", "d"], end]]);
  map.setPaintProperty("burns-new", "line-opacity", 0.9);
  clearTimeout(show.fade);
  show.fade = setTimeout(() => map.setPaintProperty("burns-new", "line-opacity", 0), 700);
  map.setFilter("fires", ["<=", ["get", "d"], end]);
  const ha = Object.entries(manifest.burn_ha_by_day).reduce((s, [d, v]) => s + (Number(d) <= end ? v : 0), 0);
  countTo($("#ha"), ha);
  countTo($("#fa"), fires.filter((f) => f.properties.d <= end).length);
  renderTimeline();
}

function setPlaying(on, stepMs = 1100, onEnd = null) {
  state.playing = on;
  clearInterval(state.timer);
  $("#play-glyph").setAttribute("href", on ? "#i-pause" : "#i-play");
  $("#play").setAttribute("aria-label", on ? "Pause" : "Play");
  if (!on) return;
  if (state.i >= windows.length - 1) show(0);
  state.timer = setInterval(() => {
    if (state.i >= windows.length - 1) { setPlaying(false); onEnd && onEnd(); return; }
    show(state.i + 1);
    state.onStep && state.onStep(state.i);
  }, reduced ? 1600 : stepMs);
}

function showHero() {
  state.intro = false;
  const h = $("#hero");
  h.hidden = false;
  document.body.classList.add("hero-open");
  requestAnimationFrame(() => requestAnimationFrame(() => h.classList.add("show")));
}

function hideHero() { $("#hero").hidden = true; document.body.classList.remove("hero-open"); }

function regionBounds() { const [w, s, e, n] = manifest.bounds; return [[w, s], [e, n]]; }
function fitRegion(duration = 1200) {
  const wide = innerWidth > 900;
  // on a phone the headline card covers the lower half, so the region sits in the upper half
  const bottom = innerWidth <= 640 ? Math.round(innerHeight * 0.52) : 120;
  map.fitBounds(regionBounds(), { padding: { top: 80, bottom, left: wide ? 120 : 24, right: wide ? 90 : 24 }, duration: reduced ? 0 : duration });
}

function playSeason() {
  hideHero();
  closePanel();
  fitRegion();
  show(0);
  state.onStep = (i) => {
    if (i === 4) map.flyTo({ center: [76.14, 29.935], zoom: 11.6, duration: reduced ? 0 : 2400, essential: true });
  };
  setTimeout(() => setPlaying(true, 1500, () => {
    state.onStep = null;
    const f = fieldsById["f-baljeet"];
    if (f) openField(f);
  }), reduced ? 0 : 1300);
}

// ---- fields and the check panel ----
let fieldsById = {};
function centroid(g) {
  const ring = g.coordinates[0], n = ring.length - 1;
  return ring.slice(0, n).reduce((a, [x, y]) => [a[0] + x / n, a[1] + y / n], [0, 0]);
}
const kindOf = (outcome) => (outcome === "auto_approved" || outcome === "officer_approved" ? "clean" : outcome === "possible_burn" ? "burn" : "review");
const ICON = { clean: "i-check", burn: "i-flame", review: "i-eye" };

function openField(f) {
  state.field = f;
  state.check = null;
  const narrow = innerWidth <= 640;
  map.flyTo({ center: centroid(f.geometry), zoom: 15.4, duration: reduced ? 0 : 2200, essential: true,
    offset: narrow ? [0, -innerHeight * 0.22] : [-200, 0] });
  hideHero();
  renderPanel();
  $("#panel").hidden = false;
  document.body.classList.add("panel-open");
}
function closePanel() { state.field = null; state.check = null; $("#panel").hidden = true; document.body.classList.remove("panel-open"); }

function verdictCard(title, r) {
  const d = r.decision, k = kindOf(d.outcome), L = t();
  const what = d.burn_date ? L.burnOn(fmtDay(d.burn_date)) : k === "clean" ? L.cleanAll(d.clear_dates.length) : "";
  return `<div class="verdict ${k}">
    <div class="ic">${icon(ICON[k])}</div>
    <div><div class="t"><b>${esc(L.v[k])}</b><span>${esc(title)}</span></div>
      <p class="facts">${esc([what, L.fires(r.fires.length)].filter(Boolean).join(" · "))}</p></div>
    <details><summary>${esc(L.images)}</summary><img src="${esc(r.evidence_url)}" alt="" loading="lazy"></details>
  </div>`;
}

const SCAN_SVG = `<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" fill="#1A2440"/>
  <use href="#sa" fill="#2A3A63" transform="translate(32 30) scale(.8) translate(-32 -33)"/>
  <g clip-path="url(#scanclip)"><rect width="64" height="64" rx="16" fill="url(#sky)"/><use href="#sa" fill="#fff" transform="translate(32 30) scale(.8) translate(-32 -33)"/></g></svg>`;

function renderPanel() {
  const f = state.field, p = f.properties, L = t();
  const local = lang !== "en";
  const name = local ? p.farmer_hi || p.farmer : p.farmer;
  const killa = local ? p.name_hi || p.name : p.name;
  const village = local ? p.village_hi || p.village : p.village;
  const initials = p.farmer.split(" ").map((s) => s[0]).join("").slice(0, 2);
  const full = p.acres * RATE_PER_ACRE;
  const c = state.check;
  let body;
  if (!c) {
    body = `<button class="btn primary wide" id="run-check">${icon("i-scan")}<span>${esc(L.check)}</span></button>
      <p class="note">${icon("i-shield")}<span>${esc(L.decides)}</span></p>`;
  } else if (c.failed || c.status === "error") {
    body = `<p class="err">${esc(L.err)}</p><button class="btn primary wide" id="run-check">${icon("i-scan")}<span>${esc(L.check)}</span></button>`;
  } else if (c.status !== "done") {
    const k = c.step % L.steps.length;
    body = `<div class="scanning">${SCAN_SVG}<p id="scan-step">${esc(L.steps[k])}</p>
      <div class="dots">${L.steps.map((_, j) => `<i class="${j <= k ? "on" : ""}"></i>`).join("")}</div></div>`;
  } else {
    const r = c.result, adv = c.advance_eligible ? full * ADVANCE_SHARE : 0;
    body = `<div class="section"><h3>${esc(L.reading)}</h3>${verdictCard(L.s25, r.current)}${verdictCard(L.s24, r.previous)}
      <p class="note">${icon("i-shield")}<span>${esc(L.decides)}</span></p></div>`;
    state.verdicts[p.id] = kindOf(r.current.decision.outcome);
    syncPins();
    body = `<div class="section"><h3>${esc(L.pay)}</h3><div class="pay">
        <div class="total"><b>${rupees(full)}</b><span>${p.acres} ${esc(L.acres)} × ${rupees(RATE_PER_ACRE)}</span></div>
        <div class="bar2"><i style="width:${adv ? ADVANCE_SHARE * 100 : 0}%"></i></div>
        <div class="legend">${adv ? `<span><b>${rupees(adv)}</b> ${esc(L.before)}</span><span><b>${rupees(full - adv)}</b> ${esc(L.after)}</span>`
          : `<span>${esc(L.noadv)}</span>`}</div>
        <p class="note" style="margin-top:10px">${esc(c.advance_eligible ? L.advYes : L.advNo)}</p></div></div>` + body;
  }
  $("#panel-body").innerHTML = `<div class="who"><div class="avatar">${esc(initials)}</div>
    <div><h2>${esc(name)}</h2><p>${esc(killa)} · ${p.acres} ${esc(L.acres)} · ${esc(village)}</p></div></div>
    <div class="section">${body}</div>`;
  const btn = $("#run-check");
  if (btn) btn.onclick = runCheck;
}

async function runCheck() {
  const f = state.field;
  state.check = { status: "queued", step: 0 };
  renderPanel();
  const stepper = setInterval(() => {
    if (!state.check || state.check.status === "done" || state.field !== f) return clearInterval(stepper);
    state.check.step = Math.min(state.check.step + 1, t().steps.length - 1);
    renderPanel();
  }, 4200);
  try {
    const r = await fetch("/api/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ geometry: f.geometry }) });
    if (!r.ok) throw new Error((await r.json()).error || r.status);
    const { id } = await r.json();
    for (let k = 0; k < 60 && state.field === f; k++) {
      await new Promise((ok) => setTimeout(ok, 2000));
      const item = await (await fetch(`/api/check/${id}`)).json();
      if (item.status === "done" || item.status === "error") {
        clearInterval(stepper);
        if (state.field === f) { state.check = item; renderPanel(); }
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
async function init() {
  manifest = await (await fetch("/tiles/manifest.json")).json();
  windows = manifest.windows;
  day0 = new Date(manifest.day0);
  buildSpark();
  applyLang();

  map = new maplibregl.Map({
    container: "map",
    attributionControl: false,
    bounds: regionBounds(), fitBoundsOptions: { padding: 60 },
    maxZoom: 17.5, minZoom: 7,
    style: {
      version: 8,
      sources: {
        esri: { type: "raster", tileSize: 256, maxzoom: 18,
          tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"] },
      },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": "#0B1120" } },
        { id: "esri", type: "raster", source: "esri", paint: {
          "raster-saturation": ["interpolate", ["linear"], ["zoom"], 13, -1, 15, 0],
          "raster-brightness-max": ["interpolate", ["linear"], ["zoom"], 13, 0.22, 15, 1],
          "raster-contrast": ["interpolate", ["linear"], ["zoom"], 13, -0.3, 15, 0] } },
      ],
    },
  });
  window.saakshi = { map, state };
  const data = Promise.all([
    fetch("data/region.geojson").then((r) => r.json()),
    fetch("/tiles/fires.geojson").then((r) => r.json()),
    fetch("/api/fields").then((r) => (r.ok ? r.json() : [])).catch(() => []),
  ]);
  map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution:
    "Our tiles: Copernicus Sentinel-2 (ESA) via AWS Open Data · Fire alerts: NASA FIRMS · Close-up imagery: Esri, Maxar, Earthstar Geographics · District boundary © OpenStreetMap contributors" }), "bottom-right");
  // start with the credits folded into their (i) button; they open on tap
  setTimeout(() => $$(".maplibregl-ctrl-attrib").forEach((el) => el.classList.remove("maplibregl-compact-show")), 0);
  addEventListener("resize", () => { if (state.intro) fitRegion(0); });

  // isStyleLoaded() also waits for basemap tiles, and style.load can fire before we listen: poll the style itself
  while (!(map.style && map.style._loaded)) await new Promise((ok) => setTimeout(ok, 30));
  const [region, firesFc, fieldsList] = await data;
  fires = firesFc.features;

  // high-density screens would stretch 256 px tiles: ask for the next zoom's tiles there instead
  const tileSize = devicePixelRatio >= 1.5 ? 128 : 256;
  windows.forEach((w) => {
    map.addSource(`img-${w.id}`, { type: "raster", tileSize, minzoom: manifest.minzoom, maxzoom: manifest.maxzoom, bounds: manifest.bounds,
      tiles: [`${location.origin}/tiles/${w.id}/{z}/{x}/{y}.webp`] });
    map.addLayer({ id: `img-${w.id}`, type: "raster", source: `img-${w.id}`,
      paint: { "raster-opacity": 0, "raster-opacity-transition": { duration: reduced ? 0 : 700 }, "raster-fade-duration": 0 } });
  });
  map.addSource("region", { type: "geojson", data: region });
  map.addLayer({ id: "region-glow", type: "line", source: "region", paint: { "line-color": "#6F8FFF", "line-opacity": 0.25, "line-width": 6, "line-blur": 6 } });
  map.addLayer({ id: "region", type: "line", source: "region", paint: { "line-color": "#B8C8FF", "line-opacity": 0.6, "line-width": 1.2 } });

  map.addSource("burns", { type: "geojson", data: "/tiles/burns.geojson" });
  const burnColor = ["interpolate", ["linear"], ["get", "d"], ...BURN_RAMP.flat()];
  map.addLayer({ id: "burns", type: "fill", source: "burns", paint: { "fill-color": burnColor,
    "fill-opacity": ["interpolate", ["linear"], ["zoom"], 9, 0.95, 14, 0.7, 16, 0.3] } });
  map.addLayer({ id: "burns-new", type: "line", source: "burns", paint: { "line-color": "#FFFFFF",
    "line-width": ["interpolate", ["linear"], ["zoom"], 9, 1.2, 14, 2.5], "line-blur": 1, "line-opacity": 0,
    "line-opacity-transition": { duration: reduced ? 0 : 900 } } });

  map.addSource("fires", { type: "geojson", data: firesFc });
  map.addLayer({ id: "fires", type: "circle", source: "fires", paint: {
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 1.6, 11, 3.5, 14, 10, 16, 18],
    "circle-color": ["interpolate", ["linear"], ["zoom"], 10, "#F5C542", 12, "rgba(245,197,66,0.1)"],
    "circle-stroke-color": "#F5C542", "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 8, 0, 11, 1, 14, 2] } });

  const fieldsFc = { type: "FeatureCollection", features: fieldsList.map(({ geometry, ...p }) => ({ type: "Feature", id: p.id, properties: p, geometry })) };
  fieldsFc.features.forEach((f) => { fieldsById[f.properties.id] = f; });
  map.addSource("fields", { type: "geojson", data: fieldsFc });
  map.addLayer({ id: "fields-hit", type: "fill", source: "fields", paint: { "fill-color": "#FFFFFF", "fill-opacity": 0.04 } });
  map.addLayer({ id: "fields-halo", type: "line", source: "fields", paint: { "line-color": "#000", "line-opacity": 0.5, "line-width": ["interpolate", ["linear"], ["zoom"], 11, 2, 15, 6], "line-blur": 2 } });
  map.addLayer({ id: "fields", type: "line", source: "fields", paint: { "line-color": "#FFFFFF", "line-width": ["interpolate", ["linear"], ["zoom"], 11, 1, 15, 2.5] } });
  const pins = fieldsFc.features.map((f) => {
    const el = document.createElement("button");
    el.className = "pin";
    el.onclick = (e) => { e.stopPropagation(); openField(f); };
    return { f, el, m: new maplibregl.Marker({ element: el, anchor: "bottom", offset: [0, -6] }).setLngLat(centroid(f.geometry)) };
  });
  syncPins = () => pins.forEach(({ f, el, m }) => {
    const p = f.properties, local = lang !== "en";
    el.lang = local ? "hi" : "en";
    el.className = `pin ${state.verdicts[p.id] || ""}`;
    el.innerHTML = `<i></i>${esc(local ? p.farmer_hi || p.farmer : p.farmer)}`;
    if (map.getZoom() >= 12 && state.layers.fields) m.addTo(map); else m.remove();
  });
  map.on("zoomend", syncPins);
  syncPins();
  Object.assign(window.saakshi, { pins, syncPins });
  map.on("click", "fields-hit", (e) => openField(fieldsById[e.features[0].properties.id]));
  map.on("mouseenter", "fields-hit", () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", "fields-hit", () => { map.getCanvas().style.cursor = ""; });

  // controls
  $("#play").onclick = () => { state.intro = false; hideHero(); setPlaying(!state.playing); };
  $("#slider").oninput = (e) => { state.intro = false; setPlaying(false); show(Number(e.target.value)); };
  $("#play-season").onclick = playSeason;
  $("#explore").onclick = hideHero;
  $("#panel-close").onclick = closePanel;
  $("#zoom-in").onclick = () => map.zoomIn();
  $("#zoom-out").onclick = () => map.zoomOut();
  $("#zoom-fit").onclick = () => { closePanel(); fitRegion(900); };
  $$(".layers button").forEach((b) => b.onclick = () => {
    const k = b.dataset.layer, on = !state.layers[k];
    state.layers[k] = on;
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", on);
    const ids = k === "burns" ? ["burns", "burns-new"] : k === "fires" ? ["fires"] : ["fields", "fields-hit", "fields-halo"];
    ids.forEach((id) => map.setLayoutProperty(id, "visibility", on ? "visible" : "none"));
    syncPins();
  });
  const menu = $("#lang-menu"), btn = $("#lang-btn");
  const openMenu = (open) => { menu.hidden = !open; btn.setAttribute("aria-expanded", open); };
  btn.onclick = (e) => { e.stopPropagation(); openMenu(menu.hidden); };
  $$("#lang-menu li").forEach((li) => { li.tabIndex = 0; li.onclick = () => { setLang(li.dataset.lang); openMenu(false); show(state.i); }; li.onkeydown = (e) => { if (e.key === "Enter") li.click(); }; });
  addEventListener("click", () => openMenu(false));
  addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea")) return;
    if (e.key === " ") { e.preventDefault(); $("#play").click(); }
    if (e.key === "ArrowRight") { setPlaying(false); show(Math.min(windows.length - 1, state.i + 1)); }
    if (e.key === "ArrowLeft") { setPlaying(false); show(Math.max(0, state.i - 1)); }
    if (e.key === "Escape") { closePanel(); openMenu(false); }
  });

  // opening: the season plays once over the whole belt, then the headline
  show(0);
  let started = false;
  const ready = new Promise((ok) => {
    const go = () => { if (started) return; started = true; map.resize(); fitRegion(0); $("#loader").classList.add("gone"); setTimeout(() => $("#loader")?.remove(), 700); ok(); };
    map.on("sourcedata", (e) => { if (e.sourceId === `img-${windows[0].id}` && map.isSourceLoaded(e.sourceId)) go(); });
    setTimeout(go, 5000);  // never hold the page hostage to the slowest tile
  });
  if (reduced) { ready.then(() => { show(4); showHero(); }); return; }
  map.once("dragstart", () => { if (state.intro) { setPlaying(false); showHero(); } });
  ready.then(() => setTimeout(() => setPlaying(true, 650, () => { if (state.intro) { show(4); showHero(); } }), 600));
}

init().catch((e) => {
  document.body.insertAdjacentHTML("beforeend", `<p class="err" style="position:fixed;top:90px;left:16px;z-index:9">Map failed to load: ${esc(e.message)}</p>`);
});
