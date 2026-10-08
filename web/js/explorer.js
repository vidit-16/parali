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
    explore: "Explore", officer: "Officer", farmer: "Farmer",
    kicker: "Patiala–Kaithal border belt · kharif 2025",
    headline: "<em>9 in 10</em> hectares that looked burnt got no fire alert.",
    alerts: "Fire alerts", vscap: "clean fields wrongly flagged · 314 fields checked by hand",
    play: "Play the season", explorebtn: "Explore the map",
    fine: "Burn-like ground seen by Sentinel-2. Every flag goes to an officer.",
    l_burns: "Burns", l_fires: "Fire alerts", l_fields: "Fields", ha: "ha burn-like", fa: "fire alerts",
    stages: ["Standing paddy", "Harvest begins", "Harvest", "Stubble", "Peak burning", "Burning tails off", "Wheat sowing", "Wheat up"],
    check: "Run the satellite check", steps: ["Finding every clear image", "Removing clouds", "Comparing dates", "Checking fire alerts"],
    stamp: { clean: "Clean ✓", review: "With officer", burn: "Burnt?" },
    full: "Full payment", advance: "Advance before harvest", none: "none",
    cur: "2025 season", prev: "2024 season · decides the advance",
    burnOn: (d) => `Burn signature on ${d}.`, cleanAll: (n) => `Clean in all ${n} clear images.`,
    fires: (n) => n ? `${n} fire alert${n > 1 ? "s" : ""} within 375 m.` : "No fire alert within 375 m.",
    acres: "acres", err: "The check did not finish. Try again.",
    advYes: "Clean in 2024: half is paid before harvest.", advNo: "2024 not clearly clean: paid in full after the check.",
  },
  hi: {
    explore: "देखें", officer: "अधिकारी", farmer: "किसान",
    kicker: "पटियाला–कैथल सीमा क्षेत्र · खरीफ़ 2025",
    headline: "जले दिखने वाले हर <em>10 में से 9</em> हेक्टेयर पर आग का कोई अलर्ट नहीं आया।",
    alerts: "आग अलर्ट", vscap: "साफ़ खेत जिन्हें गलती से संदिग्ध बताया · 314 खेत हाथ से जाँचे",
    play: "पूरा सीज़न देखें", explorebtn: "नक्शा देखें",
    fine: "Sentinel-2 उपग्रह को जले जैसी दिखी ज़मीन। हर संदेह अधिकारी के पास जाता है।",
    l_burns: "जले खेत", l_fires: "आग अलर्ट", l_fields: "खेत", ha: "हेक्टेयर जले जैसे", fa: "आग अलर्ट",
    stages: ["खड़ा धान", "कटाई शुरू", "कटाई", "पराली", "सबसे ज़्यादा जलना", "जलना घटा", "गेहूँ बुआई", "गेहूँ उगा"],
    check: "उपग्रह जाँच चलाएँ", steps: ["हर साफ़ तस्वीर ढूँढ रहे हैं", "बादल हटा रहे हैं", "तारीखें मिला रहे हैं", "आग अलर्ट जाँच रहे हैं"],
    stamp: { clean: "साफ़ ✓", review: "अधिकारी", burn: "जला?" },
    full: "पूरी राशि", advance: "कटाई से पहले अग्रिम", none: "नहीं",
    cur: "2025 सीज़न", prev: "2024 सीज़न · इसी से अग्रिम तय होता है",
    burnOn: (d) => `${d} को जलने का निशान।`, cleanAll: (n) => `सभी ${n} साफ़ तस्वीरों में खेत साफ़।`,
    fires: (n) => n ? `375 मीटर के अंदर ${n} आग अलर्ट।` : "375 मीटर के अंदर कोई आग अलर्ट नहीं।",
    acres: "एकड़", err: "जाँच पूरी नहीं हुई। फिर कोशिश करें।",
    advYes: "2024 में साफ़: आधी राशि कटाई से पहले।", advNo: "2024 साफ़ नहीं दिखा: पूरी राशि जाँच के बाद।",
  },
  pa: {
    explore: "ਵੇਖੋ", officer: "ਅਧਿਕਾਰੀ", farmer: "ਕਿਸਾਨ",
    kicker: "ਪਟਿਆਲਾ–ਕੈਥਲ ਸਰਹੱਦੀ ਖੇਤਰ · ਸਾਉਣੀ 2025",
    headline: "ਸੜੇ ਦਿਸਦੇ ਹਰ <em>10 ਵਿੱਚੋਂ 9</em> ਹੈਕਟੇਅਰ ਲਈ ਕੋਈ ਅੱਗ ਅਲਰਟ ਨਹੀਂ ਆਇਆ।",
    alerts: "ਅੱਗ ਅਲਰਟ", vscap: "ਸਾਫ਼ ਖੇਤ ਜਿਨ੍ਹਾਂ ਨੂੰ ਗਲਤੀ ਨਾਲ ਸ਼ੱਕੀ ਕਿਹਾ · 314 ਖੇਤ ਹੱਥੀਂ ਜਾਂਚੇ",
    play: "ਪੂਰਾ ਸੀਜ਼ਨ ਵੇਖੋ", explorebtn: "ਨਕਸ਼ਾ ਵੇਖੋ",
    fine: "Sentinel-2 ਉਪਗ੍ਰਹਿ ਨੂੰ ਸੜੀ ਵਰਗੀ ਦਿਸੀ ਜ਼ਮੀਨ। ਹਰ ਸ਼ੱਕ ਅਧਿਕਾਰੀ ਕੋਲ ਜਾਂਦਾ ਹੈ।",
    l_burns: "ਸੜੇ ਖੇਤ", l_fires: "ਅੱਗ ਅਲਰਟ", l_fields: "ਖੇਤ", ha: "ਹੈਕਟੇਅਰ ਸੜੇ ਵਰਗੇ", fa: "ਅੱਗ ਅਲਰਟ",
    stages: ["ਖੜ੍ਹਾ ਝੋਨਾ", "ਵਾਢੀ ਸ਼ੁਰੂ", "ਵਾਢੀ", "ਪਰਾਲੀ", "ਸਭ ਤੋਂ ਵੱਧ ਸਾੜ", "ਸਾੜ ਘਟਿਆ", "ਕਣਕ ਦੀ ਬਿਜਾਈ", "ਕਣਕ ਉੱਗੀ"],
    check: "ਉਪਗ੍ਰਹਿ ਜਾਂਚ ਚਲਾਓ", steps: ["ਹਰ ਸਾਫ਼ ਤਸਵੀਰ ਲੱਭ ਰਹੇ ਹਾਂ", "ਬੱਦਲ ਹਟਾ ਰਹੇ ਹਾਂ", "ਤਾਰੀਖਾਂ ਮਿਲਾ ਰਹੇ ਹਾਂ", "ਅੱਗ ਅਲਰਟ ਜਾਂਚ ਰਹੇ ਹਾਂ"],
    stamp: { clean: "ਸਾਫ਼ ✓", review: "ਅਧਿਕਾਰੀ", burn: "ਸੜਿਆ?" },
    full: "ਪੂਰੀ ਰਕਮ", advance: "ਵਾਢੀ ਤੋਂ ਪਹਿਲਾਂ ਅਗਾਊਂ", none: "ਨਹੀਂ",
    cur: "2025 ਸੀਜ਼ਨ", prev: "2024 ਸੀਜ਼ਨ · ਇਸੇ ਨਾਲ ਅਗਾਊਂ ਤੈਅ ਹੁੰਦਾ ਹੈ",
    burnOn: (d) => `${d} ਨੂੰ ਸਾੜ ਦਾ ਨਿਸ਼ਾਨ।`, cleanAll: (n) => `ਸਾਰੀਆਂ ${n} ਸਾਫ਼ ਤਸਵੀਰਾਂ ਵਿੱਚ ਖੇਤ ਸਾਫ਼।`,
    fires: (n) => n ? `375 ਮੀਟਰ ਅੰਦਰ ${n} ਅੱਗ ਅਲਰਟ।` : "375 ਮੀਟਰ ਅੰਦਰ ਕੋਈ ਅੱਗ ਅਲਰਟ ਨਹੀਂ।",
    acres: "ਏਕੜ", err: "ਜਾਂਚ ਪੂਰੀ ਨਹੀਂ ਹੋਈ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
    advYes: "2024 ਵਿੱਚ ਸਾਫ਼: ਅੱਧੀ ਰਕਮ ਵਾਢੀ ਤੋਂ ਪਹਿਲਾਂ।", advNo: "2024 ਸਾਫ਼ ਨਹੀਂ ਦਿਸਿਆ: ਪੂਰੀ ਰਕਮ ਜਾਂਚ ਤੋਂ ਬਾਅਦ।",
  },
  hr: {
    explore: "देक्खो", officer: "अफसर", farmer: "किसान",
    kicker: "पटियाला–कैथल बॉर्डर इलाका · खरीफ़ 2025",
    headline: "जळे दिक्खण आळे हर <em>10 म्ह तै 9</em> हेक्टेयर पै कोए आग का अलर्ट कोनी आया।",
    alerts: "आग अलर्ट", vscap: "साफ खेत जिन पै गलती तै शक करया · 314 खेत हाथ तै जांचे",
    play: "पूरा सीज़न देक्खो", explorebtn: "नक्सा देक्खो",
    fine: "Sentinel-2 नै जळी बरगी दिक्खी धरती। हर शक अफसर कनै जावै सै।",
    l_burns: "जळे खेत", l_fires: "आग अलर्ट", l_fields: "खेत", ha: "हेक्टेयर जळे बरगे", fa: "आग अलर्ट",
    stages: ["खड़या धान", "कटाई शुरू", "कटाई", "पराळी", "सब तै घणा जळाणा", "जळाणा घटया", "गेहूं की बिजाई", "गेहूं उग्या"],
    check: "उपग्रह जांच चलाओ", steps: ["हर साफ फोटो टोहण लाग रे सां", "बादळ हटाण लाग रे सां", "तारीख मिलाण लाग रे सां", "आग अलर्ट जांचण लाग रे सां"],
    stamp: { clean: "साफ ✓", review: "अफसर", burn: "जळया?" },
    full: "पूरी रकम", advance: "कटाई तै पहल्यां एडवांस", none: "कोनी",
    cur: "2025 सीज़न", prev: "2024 सीज़न · इसतै एडवांस तय होवै",
    burnOn: (d) => `${d} नै जळण का निसान।`, cleanAll: (n) => `सारी ${n} साफ फोटुआं म्ह खेत साफ।`,
    fires: (n) => n ? `375 मीटर भीतर ${n} आग अलर्ट।` : "375 मीटर भीतर कोए आग अलर्ट कोनी।",
    acres: "किल्ले", err: "जांच पूरी कोनी होई। फेर कोसिस करो।",
    advYes: "2024 म्ह साफ: आधी रकम कटाई तै पहल्यां।", advNo: "2024 साफ कोनी दिख्या: पूरी रकम जांच के पाच्छै।",
  },
};
const HTML_LANG = { en: "en", hi: "hi", pa: "pa", hr: "hi" };
const RATE_PER_ACRE = 1000, ADVANCE_SHARE = 0.5; // season.SCHEMES: Haryana's rate, half before harvest

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const rupees = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

let lang = "en";
try { lang = localStorage.getItem("saakshi-lang") || (navigator.language.startsWith("hi") ? "hi" : navigator.language.startsWith("pa") ? "pa" : "en"); } catch { /* storage blocked */ }
if (!T[lang]) lang = "en";
const t = () => T[lang];

const state = { i: 0, playing: false, timer: null, layers: { burns: true, fires: true, fields: true }, intro: true, field: null, check: null };
let map, manifest, fires = [], windows = [], day0;

function applyLang() {
  document.documentElement.lang = HTML_LANG[lang];
  $$("[data-i18n]").forEach((el) => { const v = t()[el.dataset.i18n]; if (typeof v === "string") el.innerHTML = v; });
  $$(".langs button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
  renderTimeline();
  if (state.field) renderPanel();
}

function dayNum(iso) { return Math.round((new Date(iso) - day0) / 864e5); }
function fmtRange(w) {
  const s = new Date(w.start), e = new Date(w.end);
  const loc = lang === "en" ? "en-IN" : lang === "pa" ? "pa-IN" : "hi-IN";
  const m = e.toLocaleDateString(loc, { month: "short" });
  return `${s.getDate()}–${e.getDate()} ${m}`;
}

function renderTimeline() {
  if (!windows.length) return;
  const w = windows[state.i];
  $("#when").textContent = fmtRange(w);
  $("#stage").textContent = t().stages[state.i];
  $("#fill").style.clipPath = `inset(0 ${100 - ((state.i + 1) / windows.length) * 100}% 0 0)`;
  $$("#ticks button").forEach((b, j) => { b.classList.toggle("past", j <= state.i); b.classList.toggle("now", j === state.i); b.textContent = fmtRange(windows[j]).split(" ")[0] + " " + fmtRange(windows[j]).split(" ")[1]; });
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
  const prevDay = state.i === i ? -1 : dayNum(windows[state.i].end);
  state.i = i;
  const end = dayNum(windows[i].end);
  windows.forEach((w, j) => map.setPaintProperty(`img-${w.id}`, "raster-opacity", ["interpolate", ["linear"], ["zoom"], 14.3, j === i ? 1 : 0, 15.3, 0]));
  map.setFilter("burns", ["<=", ["get", "d"], end]);
  map.setFilter("burns-new", ["all", [">", ["get", "d"], prevDay < end ? prevDay : -1], ["<=", ["get", "d"], end]]);
  map.setPaintProperty("burns-new", "line-opacity", 1);
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
  $("#play-icon").setAttribute("d", on ? "M7 5h4v14H7zM13 5h4v14h-4z" : "M8 5v14l11-7z");
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
  requestAnimationFrame(() => h.classList.add("show"));
}

function regionBounds() { const [w, s, e, n] = manifest.bounds; return [[w, s], [e, n]]; }

function playSeason() {
  $("#hero").hidden = true;
  closePanel();
  map.fitBounds(regionBounds(), { padding: 60, duration: reduced ? 0 : 1200 });
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
  const ring = g.coordinates[0];
  const n = ring.length - 1;
  return ring.slice(0, n).reduce((a, [x, y]) => [a[0] + x / n, a[1] + y / n], [0, 0]);
}

function openField(f) {
  state.field = f;
  state.check = null;
  map.flyTo({ center: centroid(f.geometry), zoom: 15.4, duration: reduced ? 0 : 2200, essential: true });
  $("#hero").hidden = true;
  renderPanel();
  $("#panel").hidden = false;
}
function closePanel() { state.field = null; state.check = null; $("#panel").hidden = true; }

function stampFor(outcome) {
  const k = outcome === "auto_approved" || outcome === "officer_approved" ? "clean" : outcome === "possible_burn" ? "burn" : "review";
  return `<span class="stamp ${k}">${esc(t().stamp[k])}</span>`;
}
function fmtDay(iso) {
  const loc = lang === "en" ? "en-IN" : lang === "pa" ? "pa-IN" : "hi-IN";
  return new Date(iso).toLocaleDateString(loc, { day: "numeric", month: "long" });
}

function seasonBlock(title, r) {
  const d = r.decision;
  const what = d.burn_date ? t().burnOn(fmtDay(d.burn_date)) : d.outcome === "auto_approved" ? t().cleanAll(d.clear_dates.length) : "";
  return `<div class="season"><h3>${esc(title)}</h3>${stampFor(d.outcome)}
    <p>${esc(what)} ${esc(t().fires(r.fires.length))}</p>
    <img src="${esc(r.evidence_url)}" alt="Satellite images of the field through the season"></div>`;
}

function renderPanel() {
  const f = state.field, p = f.properties, L = t();
  const name = lang === "en" ? p.farmer : p.farmer_hi || p.farmer;
  const killa = lang === "en" ? p.name : p.name_hi || p.name;
  const village = lang === "en" ? p.village : p.village_hi || p.village;
  const full = p.acres * RATE_PER_ACRE;
  const c = state.check;
  let body = "";
  if (!c) {
    body = `<button class="primary" id="run-check" style="width:100%;justify-content:center">${esc(L.check)}</button>`;
  } else if (c.status === "error" || c.failed) {
    body = `<p class="err">${esc(L.err)}</p><button class="primary" id="run-check">${esc(L.check)}</button>`;
  } else if (c.status !== "done") {
    body = `<div class="scan"><p id="scan-step">${esc(L.steps[c.step % L.steps.length])}</p></div>`;
  } else {
    const r = c.result;
    const adv = c.advance_eligible ? full * ADVANCE_SHARE : 0;
    body = `<div class="money"><div><b>${rupees(full)}</b><span>${esc(L.full)}</span></div>
      <div><b>${adv ? rupees(adv) : esc(L.none)}</b><span>${esc(L.advance)}</span></div></div>
      ${seasonBlock(L.cur, r.current)}${seasonBlock(L.prev, r.previous)}
      <p class="cap">${esc(c.advance_eligible ? L.advYes : L.advNo)}</p>`;
  }
  $("#panel-body").innerHTML = `<h2>${esc(name)}</h2>
    <p class="sub">${esc(killa)} · ${p.acres} ${esc(L.acres)} · ${esc(village)}</p>${body}`;
  const btn = $("#run-check");
  if (btn) btn.onclick = runCheck;
}

async function runCheck() {
  const f = state.field;
  state.check = { status: "queued", step: 0 };
  renderPanel();
  const stepper = setInterval(() => {
    if (!state.check || state.check.status === "done") return clearInterval(stepper);
    state.check.step++;
    const el = $("#scan-step");
    if (el) el.textContent = t().steps[state.check.step % t().steps.length];
  }, 3200);
  try {
    const r = await fetch("/api/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ geometry: f.geometry }) });
    if (!r.ok) throw new Error((await r.json()).error || r.status);
    const { id } = await r.json();
    for (let k = 0; k < 60 && state.field === f; k++) {
      await new Promise((ok) => setTimeout(ok, 2000));
      const item = await (await fetch(`/api/check/${id}`)).json();
      if (item.status === "done" || item.status === "error") {
        if (state.field === f) { state.check = item; renderPanel(); }
        clearInterval(stepper);
        return;
      }
    }
    throw new Error("timeout");
  } catch (e) {
    clearInterval(stepper);
    if (state.field === f) { state.check = { failed: true }; renderPanel(); }
  }
}

// ---- map ----
async function init() {
  manifest = await (await fetch("/tiles/manifest.json")).json();
  windows = manifest.windows;
  day0 = new Date(manifest.day0);
  $("#ticks").innerHTML = windows.map((w, j) => `<button data-i="${j}"></button>`).join("");
  applyLang();

  map = new maplibregl.Map({
    container: "map",
    attributionControl: false,
    bounds: regionBounds(), fitBoundsOptions: { padding: 40 },
    maxZoom: 17.5, minZoom: 7,
    style: {
      version: 8,
      sources: {
        esri: { type: "raster", tileSize: 256, maxzoom: 18,
          tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"] },
      },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": "#0E1424" } },
        { id: "esri", type: "raster", source: "esri", paint: {
          "raster-saturation": ["interpolate", ["linear"], ["zoom"], 13, -0.85, 15, 0],
          "raster-brightness-max": ["interpolate", ["linear"], ["zoom"], 13, 0.35, 15, 1] } },
      ],
    },
  });
  const data = Promise.all([
    fetch("data/region.geojson").then((r) => r.json()),
    fetch("/tiles/fires.geojson").then((r) => r.json()),
    fetch("/api/fields").then((r) => (r.ok ? r.json() : [])).catch(() => []),
  ]);
  map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution:
    "Our tiles: Copernicus Sentinel-2 (ESA) via AWS Open Data · Fire alerts: NASA FIRMS · Close-up imagery: Esri, Maxar, Earthstar Geographics · District boundary © OpenStreetMap contributors" }), "bottom-left");
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

  // the style is inline, so layers can go on as soon as it is parsed; "load" would wait for every basemap tile
  window.saakshi = { map, state, t0: performance.now(), marks: [] };
  const mark = (m) => window.saakshi.marks.push([m, Math.round(performance.now())]);
  mark("map created");
  // isStyleLoaded() also waits for basemap tiles, and style.load can fire before we listen: poll the style itself
  while (!(map.style && map.style._loaded)) await new Promise((ok) => setTimeout(ok, 30));
  mark("style loaded")
  const [region, firesFc, fieldsList] = await data;
  mark("data")
  fires = firesFc.features;

  windows.forEach((w) => {
    map.addSource(`img-${w.id}`, { type: "raster", tileSize: 256, minzoom: manifest.minzoom, maxzoom: manifest.maxzoom, bounds: manifest.bounds,
      tiles: [`${location.origin}/tiles/${w.id}/{z}/{x}/{y}.webp`] });
    map.addLayer({ id: `img-${w.id}`, type: "raster", source: `img-${w.id}`,
      paint: { "raster-opacity": 0, "raster-opacity-transition": { duration: reduced ? 0 : 700 }, "raster-fade-duration": 0 } });
  });
  map.addSource("region", { type: "geojson", data: region });
  map.addLayer({ id: "region", type: "line", source: "region", paint: { "line-color": "#9FB4FF", "line-opacity": 0.5, "line-width": 1.2 } });

  map.addSource("burns", { type: "geojson", data: "/tiles/burns.geojson" });
  const burnColor = ["interpolate", ["linear"], ["get", "d"], 30, "#FFEC82", 50, "#FFAA3C", 62, "#F04632", 80, "#C81E6E", 100, "#781E96"];
  map.addLayer({ id: "burns", type: "fill", source: "burns", paint: { "fill-color": burnColor,
    "fill-opacity": ["interpolate", ["linear"], ["zoom"], 9, 0.95, 14, 0.75, 16, 0.35] } });
  map.addLayer({ id: "burns-new", type: "line", source: "burns", paint: { "line-color": "#FFFFFF",
    "line-width": ["interpolate", ["linear"], ["zoom"], 9, 1.2, 14, 2.5], "line-blur": 1, "line-opacity": 0,
    "line-opacity-transition": { duration: reduced ? 0 : 900 } } });

  map.addSource("fires", { type: "geojson", data: firesFc });
  map.addLayer({ id: "fires", type: "circle", source: "fires", paint: {
    "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 1.6, 11, 3.5, 14, 10, 16, 18],
    "circle-color": ["interpolate", ["linear"], ["zoom"], 10, "#F5C542", 12, "rgba(245,197,66,0.12)"],
    "circle-stroke-color": "#F5C542", "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 8, 0, 11, 1, 14, 2] } });

  const fieldsFc = { type: "FeatureCollection", features: fieldsList.map(({ geometry, ...p }) => ({ type: "Feature", id: p.id, properties: p, geometry })) };
  fieldsFc.features.forEach((f) => { fieldsById[f.properties.id] = f; });
  map.addSource("fields", { type: "geojson", data: fieldsFc });
  map.addLayer({ id: "fields-hit", type: "fill", source: "fields", paint: { "fill-color": "#FFFFFF", "fill-opacity": 0.04 } });
  map.addLayer({ id: "fields", type: "line", source: "fields", paint: { "line-color": "#FFFFFF", "line-width": ["interpolate", ["linear"], ["zoom"], 11, 1, 15, 3] } });
  const markers = fieldsFc.features.map((f) => {
    const el = document.createElement("button");
    el.className = "flabel";
    el.textContent = f.properties.farmer;
    el.onclick = (e) => { e.stopPropagation(); openField(f); };
    return { f, el, m: new maplibregl.Marker({ element: el, anchor: "bottom" }).setLngLat(centroid(f.geometry)) };
  });
  const syncMarkers = () => markers.forEach(({ f, el, m }) => {
    el.textContent = lang === "en" ? f.properties.farmer : f.properties.farmer_hi || f.properties.farmer;
    if (map.getZoom() >= 12 && state.layers.fields) m.addTo(map); else m.remove();
  });
  map.on("zoomend", syncMarkers);
  syncMarkers();
  map.on("click", "fields-hit", (e) => openField(fieldsById[e.features[0].properties.id]));
  map.on("mouseenter", "fields-hit", () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", "fields-hit", () => { map.getCanvas().style.cursor = ""; });

  // controls
  $("#play").onclick = () => { if (state.intro) { state.intro = false; } $("#hero").hidden = true; setPlaying(!state.playing); };
  $("#ticks").onclick = (e) => { const b = e.target.closest("button"); if (b) { setPlaying(false); show(Number(b.dataset.i)); } };
  $("#play-season").onclick = playSeason;
  $("#explore").onclick = () => { $("#hero").hidden = true; };
  $("#panel-close").onclick = closePanel;
  $$(".layers button").forEach((b) => b.onclick = () => {
    const k = b.dataset.layer, on = !state.layers[k];
    state.layers[k] = on;
    b.classList.toggle("on", on);
    const ids = k === "burns" ? ["burns", "burns-new"] : k === "fires" ? ["fires"] : ["fields", "fields-hit"];
    ids.forEach((id) => map.setLayoutProperty(id, "visibility", on ? "visible" : "none"));
    syncMarkers();
  });
  $$(".langs button").forEach((b) => b.onclick = () => {
    lang = b.dataset.lang;
    try { localStorage.setItem("saakshi-lang", lang); } catch { /* storage blocked */ }
    applyLang();
    syncMarkers();
    show(state.i);
  });
  addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea")) return;
    if (e.key === " ") { e.preventDefault(); $("#play").click(); }
    if (e.key === "ArrowRight") { setPlaying(false); show(Math.min(windows.length - 1, state.i + 1)); }
    if (e.key === "ArrowLeft") { setPlaying(false); show(Math.max(0, state.i - 1)); }
    if (e.key === "Escape") closePanel();
  });

  // opening: the season plays once over the whole belt, then the headline
  show(0);
  let started = false;
  const ready = new Promise((ok) => {
    const go = () => { if (started) return; started = true; $("#loader").classList.add("gone"); setTimeout(() => $("#loader").remove(), 700); ok(); };
    map.on("sourcedata", (e) => { if (e.sourceId === `img-${windows[0].id}` && map.isSourceLoaded(e.sourceId)) go(); });
    setTimeout(go, 5000);  // never hold the page hostage to the slowest tile
  });
  if (reduced) { ready.then(() => { show(4); showHero(); }); return; }
  const stop = () => { if (state.intro) { setPlaying(false); showHero(); } };
  map.once("dragstart", stop);
  ready.then(() => setTimeout(() => setPlaying(true, 650, () => { if (state.intro) { show(4); showHero(); } }), 600));
}

init().catch((e) => {
  document.body.insertAdjacentHTML("beforeend", `<p class="err" style="position:fixed;top:90px;left:16px;z-index:9">Map failed to load: ${esc(e.message)}</p>`);
});
