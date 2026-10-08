import { $, api, badge, chart, esc, sleep } from "./ui.js";

const COLOR = { auto_approved: "#3fa24f", officer_approved: "#3fa24f", needs_review: "#e0a325", possible_burn: "#e0552b",
  officer_confirmed_burnt: "#e0552b", submitted: "#5b8fd1" };

export async function mapView(app) {
  app.innerHTML = `
    <h1 style="font-size:30px">West Kaithal, 2025 season</h1>
    <p class="muted" style="margin-top:-6px">Demo fields coloured by their claim, and every NASA FIRMS fire point from 25 Sep to 5 Dec.
      Notice how often a fire point sits next to a field that never burnt.</p>
    <div class="map-tools">
      <span class="badge b-ok">Approved</span><span class="badge b-warn">With officer</span><span class="badge b-bad">Possible / confirmed burn</span>
      <span class="badge b-muted">No claim yet</span><span class="badge b-muted"><span style="color:#ff3b1f">●</span> FIRMS fire point</span>
    </div>
    <div class="card" style="margin-bottom:12px">
      <div class="row"><b>Check any field</b><span class="small muted">Draw a field anywhere in Punjab or Haryana (0.2 to 20 ha). The same rules run on last season and this season.</span></div>
      <div class="row" style="margin-top:10px"><button class="btn green" id="draw">Draw a field</button>
        <button class="btn ghost" id="undo" disabled>Undo point</button><button class="btn" id="go" disabled>Check this field</button>
        <span class="small muted" id="draw-hint"></span></div>
    </div>
    <div id="map"></div>
    <div id="check-out" style="margin-top:14px"></div>
    <p class="small muted" style="margin-top:8px">Basemap: Esri World Imagery. Field shapes are hand-drawn samples (no public cadastral map exists).</p>`;

  const map = L.map("map", { scrollWheelZoom: false }).setView([29.94, 76.14], 13);
  L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    maxZoom: 18, attribution: "Imagery © Esri, Maxar, Earthstar Geographics",
  }).addTo(map);

  const [fields, claims, fires] = await Promise.all([api("/api/fields"), api("/api/claims"), api("/api/fires")]);
  const byField = Object.fromEntries(claims.map((c) => [c.field_id, c]));

  const fireLayer = L.layerGroup(fires.map((f) => L.circleMarker([f.lat, f.lon], {
    radius: 5, color: "#fff", weight: 1, fillColor: "#ff3b1f", fillOpacity: 0.9,
  }).bindTooltip(`FIRMS ${esc(f.date)} · ${esc(f.source.replace(/_/g, " "))}`))).addTo(map);

  const shapes = fields.map((f) => {
    const c = byField[f.id];
    const color = c ? COLOR[c.status] || "#ccc" : "#e9e2cf";
    const layer = L.geoJSON(f.geometry, { style: { color, weight: 3, fillOpacity: 0.25 } });
    layer.bindPopup(`<b>${esc(f.farmer)}</b> · ${esc(f.name)}<br>${esc(f.acres)} acres<br>${c ? badge(c.status) : "No claim yet"}
      <br><a href="#/farmer/${esc(f.id)}">Farmer view</a>${c ? ` · <a href="#/officer">Officer view</a>` : ""}`);
    return layer.addTo(map);
  });
  const group = L.featureGroup(shapes);
  if (shapes.length) map.fitBounds(group.getBounds().pad(0.35));
  L.control.layers(null, { "FIRMS fire points": fireLayer }, { collapsed: false }).addTo(map);
  setTimeout(() => map.invalidateSize(), 50);

  // ---- draw a field ----
  let drawing = false, pts = [], line = null, poly = null;
  const hint = $("#draw-hint");
  const redraw = () => {
    if (line) line.remove();
    if (poly) poly.remove();
    line = pts.length ? L.polyline(pts, { color: "#ffd84d", weight: 3 }).addTo(map) : null;
    poly = pts.length >= 3 ? L.polygon(pts, { color: "#ffd84d", weight: 2, fillOpacity: 0.15 }).addTo(map) : null;
    $("#undo").disabled = !pts.length;
    $("#go").disabled = pts.length < 3;
    hint.textContent = drawing ? `${pts.length} corner${pts.length === 1 ? "" : "s"}. Tap the map to add corners.` : "";
  };
  map.on("click", (e) => { if (drawing) { pts.push([e.latlng.lat, e.latlng.lng]); redraw(); } });
  $("#draw").onclick = () => {
    drawing = true; pts = []; redraw();
    map.getContainer().style.cursor = "crosshair";
    if (map.getZoom() < 15) hint.textContent = "Zoom in to a single field, then tap its corners.";
  };
  $("#undo").onclick = () => { pts.pop(); redraw(); };
  $("#go").onclick = async () => {
    drawing = false; map.getContainer().style.cursor = "";
    const ring = pts.map(([la, lo]) => [lo, la]);
    ring.push(ring[0]);
    const out = $("#check-out");
    out.innerHTML = `<div class="card"><span class="spinner"></span> Reading every clear Sentinel-2 image of this field for 2024 and 2025…</div>`;
    try {
      let item = await api("/api/check", { method: "POST", body: JSON.stringify({ geometry: { type: "Polygon", coordinates: [ring] } }) });
      for (let i = 0; i < 120 && !["done", "error"].includes(item.status); i++) { await sleep(2000); item = await api(`/api/check/${item.id}`); }
      if (item.status !== "done") throw new Error(item.error || "the check did not finish");
      out.innerHTML = renderCheck(item);
    } catch (e) { out.innerHTML = `<div class="card"><p class="err">${esc(e.message)}</p></div>`; }
  };

  return () => map.remove();
}

function renderCheck(item) {
  const col = (r, title) => `<div class="card" style="box-shadow:none">
    <h3>${esc(title)} · ${esc(r.season)}</h3><div class="row">${badge(r.decision.outcome)}</div>
    <p class="small" style="margin-top:8px">${esc(r.decision.reason)}</p>
    ${chart(r.series, r.decision.burn_date)}
    <div class="evidence"><img src="${esc(r.evidence_url)}" alt="Sentinel-2 images of the drawn field"></div></div>`;
  const prev = item.result.previous, cur = item.result.current;
  return `<div class="card">
    <h2 style="font-size:22px">Your field: ${esc(item.acres)} acres</h2>
    <p>${item.advance_eligible ? `<span class="badge b-ok">Advance eligible</span> Clean in ${esc(prev.season)}: this field would get half before harvest.`
      : `<span class="badge b-muted">No advance</span> Not clearly clean in ${esc(prev.season)}: full payment only after this season's check.`}</p>
    <div class="grid g2">${col(prev, "Last season")}${col(cur, "This season")}</div>
    <p class="small muted" style="margin-top:10px">Field outlines drawn on a map are approximate; registered fields would come from land records.</p>
  </div>`;
}