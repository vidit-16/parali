// Pieces the officer and farmer pages share with the explorer: language, dates, the field cut from our tiles,
// the orbiting-satellite mark and the header's language picker.

export const $ = (s, el = document) => el.querySelector(s);
export const $$ = (s, el = document) => [...el.querySelectorAll(s)];
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const icon = (id) => `<svg><use href="#${id}"/></svg>`;
export const rupees = (n) => "₹" + Math.round(n || 0).toLocaleString("en-IN");
export const store = {
  get: (k, s = localStorage) => { try { return s.getItem(k); } catch { return null; } },
  set: (k, v, s = localStorage) => { try { s.setItem(k, v); } catch { /* blocked */ } },
  del: (k, s = localStorage) => { try { s.removeItem(k); } catch { /* blocked */ } },
};

export const HTML_LANG = { en: "en", hi: "hi", pa: "pa", hr: "hi" };
export const LOCALE = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", hr: "hi-IN" };
const LOCAL_NAME = { en: ["साक्षी", "hi"], hi: ["साक्षी", "hi"], hr: ["साक्षी", "hi"], pa: ["ਸਾਕਸ਼ੀ", "pa"] };
const CODE = { en: "EN", hi: "हिं", pa: "ਪੰ", hr: "हरि" };
const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const PA_MONTHS = ["ਜਨਵਰੀ", "ਫ਼ਰਵਰੀ", "ਮਾਰਚ", "ਅਪ੍ਰੈਲ", "ਮਈ", "ਜੂਨ", "ਜੁਲਾਈ", "ਅਗਸਤ", "ਸਤੰਬਰ", "ਅਕਤੂਬਰ", "ਨਵੰਬਰ", "ਦਸੰਬਰ"];  // browsers often lack Punjabi month names

export function initialLang(fallback = "en") {
  const l = store.get("saakshi-lang") || fallback;
  return LOCAL_NAME[l] ? l : "en";
}
export function fmtDate(iso, lang, withYear = false) {
  if (!iso) return "";
  const d = new Date(iso);
  if (lang === "en") return `${d.getDate()} ${MONTHS_EN[d.getMonth()]}${withYear ? " " + d.getFullYear() : ""}`;
  if (lang === "pa") return `${d.getDate()} ${PA_MONTHS[d.getMonth()]}${withYear ? " " + d.getFullYear() : ""}`;
  return d.toLocaleDateString(LOCALE[lang], { day: "numeric", month: "long", ...(withYear ? { year: "numeric" } : {}) });
}
export function fmtRange(w, lang) {
  const s = new Date(w.start), e = new Date(w.end);
  const m = lang === "en" ? MONTHS_EN[e.getMonth()] : lang === "pa" ? PA_MONTHS[e.getMonth()] : e.toLocaleDateString(LOCALE[lang], { month: "long" });
  return `${s.getDate()}–${e.getDate()} ${m}`;
}

// header: brand name in the page's script, and the language menu
export function setupHeader(lang, onChange) {
  const paint = (l) => {
    document.documentElement.lang = HTML_LANG[l];
    const [local, script] = LOCAL_NAME[l];
    const nl = $("#name-local");
    if (nl) { nl.textContent = local; nl.lang = script; }
    if ($("#lang-cur")) $("#lang-cur").textContent = CODE[l];
    $$("#lang-menu li").forEach((li) => li.classList.toggle("on", li.dataset.lang === l));
  };
  paint(lang);
  const menu = $("#lang-menu"), btn = $("#lang-btn");
  if (!menu) return;
  const open = (o) => { menu.hidden = !o; btn.setAttribute("aria-expanded", o); };
  btn.onclick = (e) => { e.stopPropagation(); open(menu.hidden); };
  $$("#lang-menu li").forEach((li) => {
    li.tabIndex = 0;
    li.onclick = () => { store.set("saakshi-lang", li.dataset.lang); paint(li.dataset.lang); open(false); onChange(li.dataset.lang); };
    li.onkeydown = (e) => { if (e.key === "Enter") li.click(); };
  });
  addEventListener("click", () => open(false));
}

// the field cut out of our own tiles, one picture per ten-day window
function lonLatToPx([lon, lat], z) {
  const s = 256 * 2 ** z, y = Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
  return [((lon + 180) / 360) * s, (1 - y / Math.PI) / 2 * s];
}
export async function drawCut(canvas, windowId, geom, W = 128, H = 64, scale = 3) {
  const z = 14;
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
  ctx.lineWidth = Math.max(1.5, scale * 0.7);
  ctx.beginPath();
  pts.forEach(([x, y], i) => (i ? ctx.lineTo : ctx.moveTo).call(ctx, (x - x0) * scale, (y - y0) * scale));
  ctx.closePath();
  ctx.stroke();
}

function stripLabel(w, j, lang) {
  const d = new Date(w.start);
  return j === 0 || d.getDate() === 1 ? fmtDate(w.start, lang).replace(/ \S+$/, (m) => (lang === "en" ? m : m)) : String(d.getDate());
}
// a field's season as a filmstrip: a big viewer and eight thumbnails; returns a function to show a frame
export function filmstrip(host, windows, geom, lang, markIndex = -1) {
  host.innerHTML = `<div class="viewer">${windows.map(() => "<canvas></canvas>").join("")}<span class="tag"></span></div>
    <div class="strip">${windows.map((w, j) => `<button class="${j === markIndex ? "burnt" : ""}"><canvas></canvas><span>${esc(stripLabel(w, j, lang))}</span></button>`).join("")}</div>`;
  const big = $$(".viewer canvas", host), small = $$(".strip canvas", host), btns = $$(".strip button", host);
  windows.forEach((w, j) => { drawCut(big[j], w.id, geom); drawCut(small[j], w.id, geom, 128, 64, 1); });
  const show = (i) => {
    big.forEach((c, j) => c.classList.toggle("on", j === i));
    btns.forEach((b, j) => b.classList.toggle("on", j === i));
    $(".viewer .tag", host).textContent = fmtRange(windows[i], lang);
  };
  btns.forEach((b, j) => { b.onclick = () => show(j); });
  show(markIndex >= 0 ? markIndex : windows.length - 1);
  return show;
}

export const ORBIT = `<div class="orbit" aria-hidden="true"><svg class="o-mark" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="url(#sky)"/><use href="#sa" fill="#fff" transform="translate(32 30) scale(.8) translate(-32 -33)"/></svg>
  <svg class="o-ring" viewBox="0 0 120 120"><ellipse cx="60" cy="60" rx="56" ry="16"/></svg><div class="o-path"><i class="o-sat"></i></div></div>`;

export const kindOf = (status) => (status === "auto_approved" || status === "officer_approved" ? "clean"
  : status === "possible_burn" || status === "officer_confirmed_burnt" ? "burn" : status === "needs_review" ? "review" : "wait");

export async function getJSON(url, opts) {
  const r = await fetch(url, opts);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.error || `HTTP ${r.status}`);
  return body;
}

// ---- evidence viewer: colour pictures from our tiles, or the infrared frames of the check, over the same strip ----
// The evidence image has one column per date: a 16 px label row, the colour picture, then the infrared picture,
// frames 4 px apart. Burnt ground is maroon in infrared, wet soil dark blue.
function drawIrFrame(canvas, img, j, n, W = 128, H = 64, scale = 3) { drawEvidenceFrame(canvas, img, j, n, 1, W, H, scale); }
// row 0 is the colour picture, row 1 the infrared one
export function drawEvidenceFrame(canvas, img, j, n, row = 1, W = 128, H = 64, scale = 3) {
  const fw = img.width / n, w = fw - 4, h = (img.height - 16 - 8) / 2, y = 16 + row * (h + 4);
  canvas.width = W * scale; canvas.height = H * scale;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const k = Math.min(canvas.width / w, canvas.height / h);
  ctx.drawImage(img, j * fw, y, w, h, (canvas.width - w * k) / 2, (canvas.height - h * k) / 2, w * k, h * k);
}
export function evidenceViewer(host, { windows, geom, burnIndex = -1, ir = null, lang, labels }) {
  host.innerHTML = `<div class="vtabs" role="tablist"><button role="tab" data-v="colour" class="on">${esc(labels.colour)}</button>
      <button role="tab" data-v="ir" ${ir && ir.dates ? "" : `disabled title="${esc(labels.irWait)}"`}>${esc(labels.infrared)}</button></div>
    <div class="ev"></div><p class="cap irnote" hidden>${esc(labels.irNote)}</p>`;
  const body = $(".ev", host);
  const colour = () => { $(".irnote", host).hidden = true; filmstrip(body, windows, geom, lang, burnIndex); };
  const infrared = async () => {
    $(".irnote", host).hidden = false;
    const img = new Image();
    img.src = ir.url;
    await img.decode().catch(() => {});
    const n = ir.dates.length;
    body.innerHTML = `<div class="viewer">${ir.dates.map(() => "<canvas></canvas>").join("")}<span class="tag"></span></div>
      <div class="strip" style="--n:${n}">${ir.dates.map((d, j) => `<button class="${d === ir.burn ? "burnt" : ""}"><canvas></canvas><span>${esc(j === 0 || d === ir.burn ? fmtDate(d, lang) : String(new Date(d).getDate()))}</span></button>`).join("")}</div>`;
    const big = $$(".viewer canvas", body), small = $$(".strip canvas", body), btns = $$(".strip button", body);
    big.forEach((c, j) => drawIrFrame(c, img, j, n));
    small.forEach((c, j) => drawIrFrame(c, img, j, n, 128, 64, 1));
    const show = (i) => {
      big.forEach((c, j) => c.classList.toggle("on", j === i));
      btns.forEach((b, j) => b.classList.toggle("on", j === i));
      $(".viewer .tag", body).textContent = fmtDate(ir.dates[i], lang);
    };
    btns.forEach((b, j) => { b.onclick = () => show(j); });
    show(Math.max(0, ir.dates.indexOf(ir.burn)));
  };
  $$(".vtabs button", host).forEach((b) => {
    b.onclick = () => {
      if (b.disabled) return;
      $$(".vtabs button", host).forEach((x) => x.classList.toggle("on", x === b));
      (b.dataset.v === "ir" ? infrared : colour)();
    };
  });
  colour();
}

// count a number up when it first appears
export function countUp(el, to, fmt = (v) => String(Math.round(v)), ms = 700) {
  if (!el) return;
  const t0 = performance.now(), from = 0;
  const step = (now) => {
    const k = Math.min(1, (now - t0) / ms), e = 1 - (1 - k) ** 3;
    el.textContent = fmt(from + (to - from) * e);
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// a field's plant signal (NBR) through the season, with the burn date marked
export function signalChart(series, burnDate, lang, labels) {
  const pts = (series || []).filter((p) => p.nbr !== null && p.valid >= 0.6);
  if (pts.length < 3) return "";
  const t0 = new Date("2025-09-15").getTime(), t1 = new Date("2025-12-10").getTime();
  const W = 520, H = 120, pad = 6, x = (d) => pad + ((new Date(d).getTime() - t0) / (t1 - t0)) * (W - 2 * pad);
  const y = (v) => pad + (1 - (Math.max(-0.5, Math.min(0.8, v)) + 0.5) / 1.3) * (H - 2 * pad - 14);
  const line = pts.map((p, i) => `${i ? "L" : "M"}${x(p.date).toFixed(1)},${y(p.nbr).toFixed(1)}`).join(" ");
  const months = ["2025-10-01", "2025-11-01", "2025-12-01"].map((d) => `<text x="${x(d)}" y="${H - 2}">${esc(fmtDate(d, lang).replace(/^1 /, ""))}</text><line class="grid" x1="${x(d)}" x2="${x(d)}" y1="${pad}" y2="${H - 16}"/>`).join("");
  const burn = burnDate ? `<line class="mark" x1="${x(burnDate)}" x2="${x(burnDate)}" y1="${pad}" y2="${H - 16}"/><text class="mlabel" x="${x(burnDate) + 5}" y="${pad + 10}">${esc(fmtDate(burnDate, lang))}</text>` : "";
  return `<figure class="signal-fig"><figcaption>${esc(labels.signal)}</figcaption>
    <svg class="signal" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${months}<line class="zero" x1="${pad}" x2="${W - pad}" y1="${y(0)}" y2="${y(0)}"/>
      <path class="line draw" d="${line}"/>${pts.map((p) => `<circle class="dot" cx="${x(p.date).toFixed(1)}" cy="${y(p.nbr).toFixed(1)}" r="2.2"/>`).join("")}${burn}</svg></figure>`;
}

// names written in Hindi, shown in Gurmukhi (same rules as messages.to_gurmukhi on the server)
const NO_GURMUKHI = { "ष": "ਸ਼", "ऋ": "ਰਿ", "ृ": "ਿ", "ॉ": "ੋ", "ऑ": "ਓ", "ॅ": "ੈ", "ऍ": "ਐ", "ः": "", "ऽ": "" };
export function toGurmukhi(text) {
  let s = [...(text || "").normalize("NFC").replace(/ड\u093c/g, "ੜ").replace(/ढ\u093c/g, "ੜ")].map((ch) => {
    if (ch in NO_GURMUKHI) return NO_GURMUKHI[ch];
    const c = ch.codePointAt(0);
    return c >= 0x900 && c <= 0x97f && ch !== "।" && ch !== "॥" ? String.fromCodePoint(c + 0x100) : ch;
  }).join("");
  s = s.replace(/([\u0a15-\u0a39])\u0a4d\1/g, "\u0a71$1")
    .replace(/([\u0a15-\u0a39\u0a3f\u0a41\u0a42])\u0a02/g, "$1\u0a70")
    .replace(/\u0a4d(?![ਰਵਹ])/g, "")
    .replace(/\u0a4dਰ(?![\u0a3e-\u0a4c\u0a70\u0a71\u0a02\u0a15-\u0a39])/g, "ਰ")
    .replace(/ਿਯਾ/g, "ਿਆ")
    .replace(/ਸਿੰਹ(?![\u0a00-\u0a7f])/g, "ਸਿੰਘ");
  return s;
}

// smoke estimate, same basis as the map and the notice: about 19 kg of PM2.5 per burnt acre
export const PM25_KG_PER_ACRE = 2.6 * 0.8 * 9;  // straw t/acre × share burnt × kg PM2.5 per t; same as season.py
export const smokeKg = (acres) => Math.round((acres || 0) * PM25_KG_PER_ACRE);
