import { api, badge, esc } from "./ui.js";

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
    <div id="map"></div>
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
  return () => map.remove();
}
