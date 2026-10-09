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

export function initialLang(fallback = "en") {
  const l = store.get("saakshi-lang") || fallback;
  return LOCAL_NAME[l] ? l : "en";
}
export function fmtDate(iso, lang, withYear = false) {
  if (!iso) return "";
  const d = new Date(iso);
  if (lang === "en") return `${d.getDate()} ${MONTHS_EN[d.getMonth()]}${withYear ? " " + d.getFullYear() : ""}`;
  return d.toLocaleDateString(LOCALE[lang], { day: "numeric", month: "long", ...(withYear ? { year: "numeric" } : {}) });
}
export function fmtRange(w, lang) {
  const s = new Date(w.start), e = new Date(w.end);
  const m = lang === "en" ? MONTHS_EN[e.getMonth()] : e.toLocaleDateString(LOCALE[lang], { month: "long" });
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
