import { $$ } from "./ui.js";
import { landing } from "./landing.js";
import { farmer } from "./farmer.js";
import { officer } from "./officer.js";
import { story } from "./story.js";
import { mapView } from "./map.js";

const routes = { "": landing, story, farmer, officer, map: mapView };
let cleanup = null;

async function route() {
  const [name, ...rest] = location.hash.replace(/^#\/?/, "").split("/");
  const view = routes[name] || landing;
  $$("nav a").forEach((a) => a.classList.toggle("active", a.dataset.nav === name));
  if (cleanup) { try { cleanup(); } catch { /* view already gone */ } cleanup = null; }
  const app = document.getElementById("app");
  app.innerHTML = "";
  window.scrollTo(0, 0);
  try {
    cleanup = await view(app, rest);
  } catch (e) {
    app.innerHTML = `<div class="card"><p class="err">Could not load this page: ${e.message}</p></div>`;
  }
}

window.addEventListener("hashchange", route);
route();
