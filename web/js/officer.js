import { $, $$, RULE, advanceBadge, api, badge, chart, esc, evidence, facts, moneyRow, rupees, store } from "./ui.js";

const EVENT = {
  submitted: "Claim filed", advance_assessed: "Last season checked", advance_paid: "Advance paid",
  decided: "Satellite check decided", reviewed: "Officer decision", contest: "Farmer objected",
  callback_requested: "Farmer asked for a call",
};

export async function officer(app) {
  app.innerHTML = `
    <h1 style="font-size:30px">Village officer</h1>
    <p class="muted" style="margin-top:-6px">Only the claims the rules could not settle reach you, with the images.</p>
    <div class="card officer-bar">
      <label>Officer ID <input class="txt" id="oid" placeholder="VO-KTL-07" autocomplete="off"></label>
      <label>PIN <input class="txt" id="pin" type="password" autocomplete="off" style="width:110px"></label>
      <span class="small muted">Demo PIN 2468.</span>
      <button class="btn ghost" id="reset" style="margin-left:auto">Reset demo</button>
    </div>
    <div class="tabs" role="tablist">
      <button data-tab="queue" class="on">Waiting for you</button><button data-tab="all">All claims</button>
      <button data-tab="adv">Advances</button><button data-tab="notices">Notices</button>
    </div>
    <div class="officer-grid">
      <div id="list" class="queue"></div>
      <div id="case"></div>
    </div>`;

  $("#oid").value = store("officer-id");
  $("#pin").value = store("officer-pin");
  $("#oid").oninput = (e) => store("officer-id", e.target.value);
  $("#pin").oninput = (e) => store("officer-pin", e.target.value);

  let tab = "queue", selected = null;
  $$(".tabs button").forEach((b) => (b.onclick = () => {
    tab = b.dataset.tab;
    $$(".tabs button").forEach((x) => x.classList.toggle("on", x === b));
    load();
  }));
  $("#reset").onclick = async () => {
    if (!confirm("Delete all demo claims?")) return;
    try { await api("/api/demo/reset", { method: "POST", headers: pin(), body: "{}" }); selected = null; load(); }
    catch (e) { alert(e.message); }
  };

  async function load(withCase = true) {
    const [claims, queue] = await Promise.all([api("/api/claims"), api("/api/queue")]);
    const list = $("#list");
    let items = claims, empty = "No claims yet. Farmers file them from the farmer app.";
    if (tab === "queue") { items = queue; empty = "Nothing waiting. Claims the rules cannot settle will appear here."; }
    if (tab === "adv") { items = claims.filter((c) => c.advance); empty = "No advances assessed yet."; }
    if (tab === "notices") { items = claims.filter((c) => c.notice_url); empty = "No recovery notices drafted."; }
    list.innerHTML = items.length ? items.map((c) => `
      <button class="card qitem ${c.id === selected ? "sel" : ""}" data-id="${esc(c.id)}">
        <span><b>${esc(c.farmer_name)}</b> · ${esc(c.field_name)}</span>${tab === "adv" ? advanceBadge(c.advance) : badge(c.status)}
        <span class="why">${esc(c.contest ? "Farmer objected: " + c.contest.note : (c.decision || {}).reason || "Checking…")}</span>
      </button>`).join("") : `<p class="muted">${empty}</p>`;
    $$(".qitem", list).forEach((b) => (b.onclick = () => { selected = b.dataset.id; load(); openCase(selected); }));
    if (selected && withCase) openCase(selected);
  }

  async function openCase(id) {
    const c = await api(`/api/claims/${id}`);
    const d = c.decision || {};
    const canAct = ["needs_review", "possible_burn"].includes(c.status);
    $("#case").innerHTML = `<div class="card">
      <div class="row">${badge(c.status)} ${advanceBadge(c.advance)}</div>
      <h2 style="margin-top:10px;font-size:22px">${esc(c.farmer_name)} · ${esc(c.field_name)}</h2>
      <p class="muted" style="margin-top:-8px">${esc(c.village)} · ${esc(c.acres)} acres · season ${esc(c.season_start)} to ${esc(c.season_end)}</p>
      <p><b>${esc(RULE[d.rule] || d.rule || "")}.</b> ${esc(d.reason || "")}</p>
      ${c.contest ? `<p class="card" style="background:var(--amber-2);box-shadow:none"><b>Farmer's objection:</b> <span lang="hi">${esc(c.contest.note)}</span></p>` : ""}
      ${facts(c)}
      ${c.settlement ? moneyRow(c) : ""}
      ${chart(c.series, d.burn_date)}
      ${evidence(c)}
      ${(c.fires || []).length ? `<p class="small" style="margin-top:10px"><b>FIRMS points within range:</b> ${c.fires.map((f) => `${esc(f.date)} (${esc(f.source.replace("_", " "))})`).join(", ")}</p>` : ""}
      ${canAct ? `<div style="margin-top:14px"><label class="field-label">What you checked (site visit, phone call, receipts)<textarea class="txt" id="note"></textarea></label>
        <div class="row" style="margin-top:10px"><button class="btn green" id="ok">Approve claim</button><button class="btn ember" id="burn">Confirm burn</button></div>
        <p class="err" id="act-err"></p></div>` : ""}
      ${c.notice_url ? `<h3 style="margin-top:18px">Recovery notice (draft)</h3><iframe class="notice-frame" src="${esc(c.notice_url)}" title="Recovery notice draft"></iframe>
        <p class="small"><a href="${esc(c.notice_url)}" target="_blank" rel="noopener">Open to print or sign</a></p>` : ""}
      <h3 style="margin-top:18px">History</h3>
      <ul class="timeline">${(c.events || []).map((e) => `<li><b>${esc(EVENT[e.type] || e.type)}</b> · ${esc(e.by)} ${esc(e.verdict || e.outcome || (e.amount ? rupees(e.amount) : "") || "")} <span class="muted small">${esc((e.at || "").replace("T", " ").slice(0, 16))}</span>${e.note ? `<div class="small muted">${esc(e.note)}</div>` : ""}</li>`).join("")}</ul>
    </div>`;
    if (canAct) {
      const act = async (verdict) => {
        try {
          await api(`/api/claims/${id}/review`, { method: "POST", headers: pin(),
            body: JSON.stringify({ officer_id: $("#oid").value, verdict, note: $("#note").value }) });
          load();
        } catch (e) { $("#act-err").textContent = e.message; }
      };
      $("#ok").onclick = () => act("approve");
      $("#burn").onclick = () => act("confirm_burnt");
    }
  }

  const pin = () => ({ "X-Officer-Pin": $("#pin").value });
  await load();
  const t = setInterval(() => load(false), 8000);
  return () => clearInterval(t);
}
