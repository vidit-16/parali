export const $ = (s, root = document) => root.querySelector(s);
export const $$ = (s, root = document) => [...root.querySelectorAll(s)];
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export async function api(path, opts = {}) {
  const r = await fetch(path, { ...opts, headers: { "Content-Type": "application/json", ...(opts.headers || {}) } });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.error || r.statusText);
  return body;
}

export function store(k, v) {
  try { if (v === undefined) return localStorage.getItem(k) || ""; localStorage.setItem(k, v); } catch { return ""; }
  return v;
}

export function rupees(n) {
  if (n === null || n === undefined) return "-";
  return "₹" + Number(n).toLocaleString("en-IN");
}

export const STATUS = {
  submitted: ["Checking images", "जाँच चल रही है", "b-info"],
  auto_approved: ["Approved", "स्वीकृत", "b-ok"],
  needs_review: ["With officer", "अधिकारी के पास", "b-warn"],
  possible_burn: ["Possible burn: officer to confirm", "जलने जैसा निशान: अधिकारी तय करेंगे", "b-bad"],
  officer_approved: ["Approved by officer", "अधिकारी ने स्वीकृत किया", "b-ok"],
  officer_confirmed_burnt: ["Burn confirmed by officer", "अधिकारी ने जलना पाया", "b-bad"],
};
export const RULE = {
  no_burn_signal: "No burn signal",
  burn_scar_persistent: "Burn-like scar after a sharp NIR drop",
  dark_on_one_image: "Dark on one image only",
  partial_scar: "Part of the field dark",
  dark_without_drop: "Dark, but no fresh-burn change",
  fire_point_nearby_no_scar: "FIRMS fire point nearby, no scar on the field",
  too_few_clear_images: "Too few clear images",
  field_too_small: "Field too small for 20 m pixels",
};

export function badge(status, hindi = false) {
  const s = STATUS[status] || [status, status, "b-muted"];
  return `<span class="badge ${s[2]}" ${hindi ? 'lang="hi"' : ""}>${esc(hindi ? s[1] : s[0])}</span>`;
}

export function advanceBadge(adv) {
  if (!adv) return "";
  if (adv.status === "paid") return `<span class="badge b-ok">Advance paid ${rupees(adv.amount)}</span>`;
  if (adv.status === "offered") return `<span class="badge b-info">Advance offered ${rupees(adv.amount)}</span>`;
  return `<span class="badge b-muted">No advance (${esc(adv.prev_season)} not clean)</span>`;
}

export function chart(series, burnDate) {
  const pts = (series || []).filter((p) => p.nbr !== null && p.valid >= 0.6);
  if (pts.length < 2) return "";
  const W = 640, H = 170, L = 34, R = 8, T = 10, B = 22;
  const t0 = Date.parse(pts[0].date), t1 = Date.parse(pts[pts.length - 1].date);
  const x = (d) => L + ((Date.parse(d) - t0) / (t1 - t0 || 1)) * (W - L - R);
  const y = (v) => T + (1 - (v + 0.4) / 1.0) * (H - T - B);
  let g = "";
  for (const v of [-0.2, 0, 0.2, 0.4]) g += `<line class="grid" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/><text x="2" y="${y(v) + 4}">${v.toFixed(1)}</text>`;
  for (const m of [...new Set(pts.map((p) => p.date.slice(0, 7)))]) {
    const d = `${m}-01`;
    if (Date.parse(d) >= t0) g += `<text x="${x(d)}" y="${H - 6}">${new Date(d).toLocaleString("en", { month: "short" })}</text>`;
  }
  const line = pts.map((p, i) => `${i ? "L" : "M"}${x(p.date).toFixed(1)},${y(p.nbr).toFixed(1)}`).join("");
  const dots = pts.map((p) => `<circle class="dot" r="2.5" cx="${x(p.date).toFixed(1)}" cy="${y(p.nbr).toFixed(1)}"/>`).join("");
  const burn = burnDate ? `<line class="burn" x1="${x(burnDate)}" x2="${x(burnDate)}" y1="${T}" y2="${H - B}"/>` : "";
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Burn index across the season">${g}${burn}<path class="nbr" d="${line}"/>${dots}</svg>
    <div class="legend">Burn index (NBR) for each clear image. Harvest lowers it slowly; a burn drops it in one step${burnDate ? " (dashed line: first burn-like image)" : ""}.</div>`;
}

export function evidence(c) {
  if (!c.evidence_url) return "";
  return `<div class="evidence"><img src="${esc(c.evidence_url)}" alt="Sentinel-2 images of the field across the season"></div>
    <div class="legend">Each column is one clear Sentinel-2 image. Top: normal colour. Bottom: burn view, where fresh char is dark red
    and wet soil dark blue. The outline is the field${c.decision && c.decision.burn_date ? "; red outline: first burn-like image" : ""}.</div>`;
}

export function facts(c) {
  const d = c.decision || {};
  return `<div class="facts">
    <div><b>Clear images in window</b>${(d.clear_dates || []).length}</div>
    <div><b>Largest dark share</b>${d.max_dark_share !== undefined ? Math.round(d.max_dark_share * 100) + "%" : "-"}</div>
    <div><b>FIRMS points within 375 m</b>${d.fires_nearby ?? "-"}</div>
    <div><b>Rule that fired</b>${esc(RULE[d.rule] || d.rule || "-")}</div>
  </div>`;
}

export function moneyRow(c) {
  const a = c.advance || {}, s = c.settlement || {};
  const paid = a.status === "paid" ? a.amount : 0;
  let last = `<div><b>-</b><span>pending check</span></div>`;
  if (s.state === "balance_due") last = `<div><b style="color:var(--green)">${rupees(s.balance)}</b><span>balance to release</span></div>`;
  if (s.state === "recover_advance") last = `<div><b style="color:var(--ember)">${rupees(s.recover)}</b><span>advance to recover</span></div>`;
  if (s.state === "not_payable") last = `<div><b>₹0</b><span>not payable</span></div>`;
  return `<div class="money">
    <div><b>${rupees(s.total)}</b><span>season total (₹1,000/acre)</span></div>
    <div><b>${rupees(paid)}</b><span>advance before harvest</span></div>
    ${last}
  </div>`;
}

export function playAudio(url, fallbackText) {
  if (url) { new Audio(url).play().catch(() => speakBrowser(fallbackText)); return; }
  speakBrowser(fallbackText);
}

function speakBrowser(text) {
  if (!text || !("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "hi-IN";
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function waitForClaim(id, onTick) {
  for (let i = 0; i < 90; i++) {
    const c = await api(`/api/claims/${id}`);
    if (onTick) onTick(c);
    if (c.status !== "submitted" || c.error) return c;
    await sleep(1500);
  }
  throw new Error("The satellite check is taking longer than expected.");
}
