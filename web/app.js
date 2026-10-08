const STATUS = {
  submitted: "Checking images",
  auto_approved: "Approved",
  needs_review: "With officer",
  possible_burn: "Possible burn, officer to confirm",
  officer_approved: "Approved by officer",
  officer_confirmed_burnt: "Burn confirmed by officer",
};
const RULE = {
  no_burn_signal: "No burn signal",
  burn_scar_persistent: "Burn-like scar on 2+ images",
  dark_on_one_image: "Dark on one image only",
  partial_scar: "Part of field dark",
  fire_point_nearby_no_scar: "Fire point nearby, no scar",
  too_few_clear_images: "Too few clear images",
  field_too_small: "Field too small",
};

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const badge = (s) => `<span class="badge s-${esc(s)}">${esc(STATUS[s] || s)}</span>`;

function store(k, v) {
  try { if (v === undefined) return localStorage.getItem(k) || ""; localStorage.setItem(k, v); } catch { return ""; }
}

async function api(path, opts = {}) {
  const r = await fetch(path, { ...opts, headers: { "Content-Type": "application/json", ...(opts.headers || {}) } });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.error || r.statusText);
  return body;
}

document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === b));
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("hidden", v.id !== b.dataset.view));
  if (b.dataset.view === "officer") loadOfficer();
}));

/* ---------- chart ---------- */
function chart(series, burnDate) {
  const pts = series.filter((p) => p.nbr !== null && p.valid >= 0.6);
  if (pts.length < 2) return "";
  const W = 640, H = 180, L = 34, R = 8, T = 10, B = 22;
  const t0 = Date.parse(pts[0].date), t1 = Date.parse(pts[pts.length - 1].date);
  const x = (d) => L + ((Date.parse(d) - t0) / (t1 - t0 || 1)) * (W - L - R);
  const y = (v) => T + (1 - (v + 0.4) / 1.0) * (H - T - B);   // NBR range -0.4 .. 0.6
  const line = (k, f) => pts.map((p, i) => `${i ? "L" : "M"}${x(p.date).toFixed(1)},${f(p[k]).toFixed(1)}`).join("");
  let g = "";
  for (const v of [-0.2, 0, 0.2, 0.4]) g += `<line class="grid" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/><text x="2" y="${y(v) + 4}">${v.toFixed(1)}</text>`;
  const months = [...new Set(pts.map((p) => p.date.slice(0, 7)))];
  for (const m of months) {
    const d = `${m}-01`;
    if (Date.parse(d) >= t0) g += `<text x="${x(d)}" y="${H - 6}">${new Date(d).toLocaleString("en", { month: "short" })}</text>`;
  }
  const burn = burnDate ? `<line class="burn" x1="${x(burnDate)}" x2="${x(burnDate)}" y1="${T}" y2="${H - B}"/>` : "";
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Burn index over the season">
    ${g}${burn}<path class="nir" d="${line("nir", (v) => y(v * 2 - 0.4))}"/><path class="nbr" d="${line("nbr", y)}"/></svg>
    <div class="legend">Solid: burn index (NBR) per clear image. Dashed: near-infrared, scaled. ${burnDate ? "Red line: first burn-like image." : ""}
    Harvest lowers NBR slowly; a burn drops it in one step.</div>`;
}

/* ---------- speech ---------- */
function speak(claim) {
  if (claim.audio_url) { new Audio(claim.audio_url).play(); return; }
  if (!("speechSynthesis" in window) || !claim.message) return;
  const u = new SpeechSynthesisUtterance(claim.message.hi);
  u.lang = "hi-IN";
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

function facts(c) {
  const d = c.decision || {};
  return `<div class="facts">
    <div><b>Clear images in window</b>${(d.clear_dates || []).length}</div>
    <div><b>Most of field dark</b>${d.max_dark_share !== undefined ? Math.round(d.max_dark_share * 100) + "%" : "-"}</div>
    <div><b>Fire points nearby</b>${d.fires_nearby ?? "-"}</div>
    <div><b>Rule</b>${esc(RULE[d.rule] || d.rule || "-")}</div>
  </div>`;
}

function evidence(c) {
  if (!c.evidence_url) return "";
  return `<div class="evidence"><img src="${esc(c.evidence_url)}" alt="Satellite images of the field across the season"></div>
    <div class="legend">Each column is one clear Sentinel-2 image. Top: true colour. Bottom: SWIR / NIR / red, where a fresh
    burn turns dark red and wet soil turns dark blue. The outline is the field${c.decision && c.decision.burn_date ? "; red outline marks the first burn-like image" : ""}.</div>`;
}

/* ---------- farmer ---------- */
let fields = [], claims = [], current = null, poll = null;

async function loadFarmer() {
  [fields, claims] = await Promise.all([api("/api/fields"), api("/api/claims")]);
  const byField = Object.fromEntries(claims.map((c) => [c.field_id, c]));
  $("#fields").innerHTML = fields.map((f) => {
    const c = byField[f.id];
    return `<div class="card">
      <h3>${esc(f.name)}</h3>
      <div class="meta">${esc(f.farmer)} · ${esc(f.village)}${f.acres ? ` · ${f.acres} acres` : ""}</div>
      ${c ? `${badge(c.status)} <button class="ghost" data-open="${esc(c.id)}">Open</button>`
          : `<button data-file="${esc(f.id)}">File no-burn claim</button>`}
    </div>`;
  }).join("");
  document.querySelectorAll("[data-file]").forEach((b) => b.onclick = () => fileClaim(b.dataset.file, b));
  document.querySelectorAll("[data-open]").forEach((b) => b.onclick = () => openClaim(b.dataset.open));
}

async function fileClaim(fieldId, btn) {
  btn.disabled = true;
  try {
    const c = await api("/api/claims", { method: "POST", body: JSON.stringify({ field_id: fieldId }) });
    await loadFarmer();
    openClaim(c.id);
  } catch (e) { btn.disabled = false; alert(e.message); }
}

async function openClaim(id) {
  clearTimeout(poll);
  current = await api(`/api/claims/${id}`);
  renderClaim(current);
  if (current.status === "submitted") poll = setTimeout(() => openClaim(id).then(loadFarmer), 2000);
}

function renderClaim(c) {
  const el = $("#claim");
  el.classList.remove("hidden");
  const m = c.message || { hi: "उपग्रह तस्वीरों की जाँच चल रही है…", en: "Checking satellite images…" };
  el.innerHTML = `<div>${badge(c.status)} <b>${esc(c.field_name)}</b> · ${esc(c.farmer_name)}</div>
    <p class="msg-hi" lang="hi">${esc(m.hi)}</p>
    <p class="msg-en">${esc(m.en)}</p>
    ${c.message ? `<button id="listen">▶ सुनें / Listen</button>` : ""}
    ${c.decision ? facts(c) : ""}
    ${c.series ? chart(c.series, c.decision && c.decision.burn_date) : ""}
    ${evidence(c)}`;
  const l = $("#listen");
  if (l) l.onclick = () => speak(c);
  el.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---------- officer ---------- */
$("#officer-id").value = store("officer-id");
$("#officer-pin").value = store("officer-pin");
$("#officer-id").onchange = (e) => store("officer-id", e.target.value);
$("#officer-pin").onchange = (e) => store("officer-pin", e.target.value);
const pinHeader = () => ({ "X-Officer-Pin": $("#officer-pin").value });

async function loadOfficer() {
  const [q, all] = await Promise.all([api("/api/queue"), api("/api/claims")]);
  $("#queue").innerHTML = q.length ? q.map((c) => `<div data-id="${esc(c.id)}">
      <span><b>${esc(c.field_name)}</b> · ${esc(c.farmer_name)}, ${esc(c.village)}</span>${badge(c.status)}
      <span class="why">${esc((c.decision || {}).reason || "")}</span></div>`).join("")
    : `<p class="intro">Nothing waiting. Claims the system is unsure about will appear here.</p>`;
  document.querySelectorAll("#queue > div").forEach((d) => d.onclick = () => openReview(d.dataset.id));
  $("#all tbody").innerHTML = all.map((c) => `<tr><td>${esc(c.field_name)}</td><td>${esc(c.farmer_name)}</td>
    <td>${badge(c.status)}</td><td>${esc(RULE[(c.decision || {}).rule] || "")}</td></tr>`).join("");
}

async function openReview(id) {
  document.querySelectorAll("#queue > div").forEach((d) => d.classList.toggle("sel", d.dataset.id === id));
  const c = await api(`/api/claims/${id}`);
  const el = $("#detail");
  el.classList.remove("hidden");
  el.innerHTML = `<div>${badge(c.status)} <b>${esc(c.field_name)}</b> · ${esc(c.farmer_name)}, ${esc(c.village)}</div>
    <p>${esc((c.decision || {}).reason || "")}</p>
    ${facts(c)}${chart(c.series || [], c.decision && c.decision.burn_date)}${evidence(c)}
    ${(c.fires || []).length ? `<p>Fire points: ${c.fires.map((f) => `${esc(f.date)} (${esc(f.source)})`).join(", ")}</p>` : ""}
    <label>Note (what you checked)<textarea id="note"></textarea></label>
    <div class="actions">
      <button id="approve">Approve claim</button>
      <button id="confirm" class="danger">Confirm burn</button>
    </div>
    <p id="rev-err" class="err"></p>
    <h3>History</h3>
    <ul class="events">${(c.events || []).map((e) => `<li>${esc(e.at)} · ${esc(e.type)} · ${esc(e.by)} ${esc(e.outcome || e.verdict || "")}</li>`).join("")}</ul>`;
  const send = async (verdict) => {
    try {
      await api(`/api/claims/${id}/review`, { method: "POST", headers: pinHeader(),
        body: JSON.stringify({ officer_id: $("#officer-id").value, verdict, note: $("#note").value }) });
      el.classList.add("hidden");
      loadOfficer();
    } catch (e) { $("#rev-err").textContent = e.message; }
  };
  $("#approve").onclick = () => send("approve");
  $("#confirm").onclick = () => send("confirm_burnt");
}

$("#reset").onclick = async () => {
  if (!confirm("Delete all demo claims?")) return;
  try { await api("/api/demo/reset", { method: "POST", headers: pinHeader(), body: "{}" }); }
  catch (e) { alert(e.message); return; }
  $("#detail").classList.add("hidden"); $("#claim").classList.add("hidden");
  loadOfficer(); loadFarmer();
};

loadFarmer().catch((e) => { $("#fields").innerHTML = `<p class="err">Could not load fields: ${esc(e.message)}</p>`; });
