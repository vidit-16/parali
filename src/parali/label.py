"""Hand-labelling: one image strip per plot, and a small local page to mark burnt / not burnt / unsure."""
import csv
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from parali.area import AreaStack
from parali.fields import Field, project

LABELS = ("burnt", "not_burnt", "unsure")


def plot_window(stack: AreaStack, plot: Field, pad: int):
    g = project(plot.geometry, stack.crs)
    inv = ~stack.transform
    c0, r0 = inv @ (g.bounds[0], g.bounds[3])
    c1, r1 = inv @ (g.bounds[2], g.bounds[1])
    r0, c0, r1, c1 = int(round(r0)), int(round(c0)), int(round(r1)), int(round(c1))
    return (r0, c0, r1, c1), (max(r0 - pad, 0), max(c0 - pad, 0), r1 + pad, c1 + pad)


def clear_dates(stack: AreaStack, plot: Field, pad: int = 9) -> list[int]:
    (pr0, pc0, pr1, pc1), _ = plot_window(stack, plot, pad)
    return [t for t in range(len(stack.dates))
            if np.mean(~np.isin(stack.scl[t, pr0:pr1, pc0:pc1], (0, 1, 8, 9, 10))) >= 0.8]


def render_strip(stack: AreaStack, plot: Field, out: Path, pad: int = 9, per_line: int = 12) -> None:
    """Every clear image of the season, wrapped onto lines of per_line dates. Every date, not a sample:
    burnt fields here are ploughed within days, so a burn can show on one image only, and an earlier
    version that sampled 12 dates hid the burn date of most plots the rules flagged."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    (pr0, pc0, pr1, pc1), (r0, c0, r1, c1) = plot_window(stack, plot, pad)
    keep = clear_dates(stack, plot, pad)
    lines = max(1, -(-len(keep) // per_line))
    fig, axes = plt.subplots(2 * lines, per_line, figsize=(2.1 * per_line, 4.9 * lines), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for j, t in enumerate(keep):
        row, col = 2 * (j // per_line), j % per_line

        def win(b):
            return stack.band(t, b)[r0:r1, c0:c1]
        rgb = np.dstack([win("red"), win("green"), win("blue")]) / 0.16
        swir = np.dstack([win("swir22") / 0.35, win("nir08") / 0.45, win("red") / 0.2])
        for i, img in enumerate((rgb, swir)):
            ax = axes[row + i, col]
            ax.axis("on")
            ax.imshow(np.clip(np.nan_to_num(img), 0, 1), interpolation="nearest")
            ax.add_patch(Rectangle((pc0 - c0 - 0.5, pr0 - r0 - 0.5), pc1 - pc0, pr1 - pr0,
                                   fill=False, edgecolor="cyan", linewidth=2.5))
            ax.set_xticks([]); ax.set_yticks([])
        axes[row, col].set_title(stack.dates[t].strftime("%d %b"), fontsize=11, fontweight="bold")
        if col == 0:
            axes[row, 0].set_ylabel("normal colour", fontsize=10)
            axes[row + 1, 0].set_ylabel("burn view", fontsize=10)
    fig.tight_layout(pad=0.3)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=80)
    plt.close(fig)


def read_labels(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return {r["plot_id"]: r["label"] for r in csv.DictReader(f)}


def write_labels(path: Path, labels: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["plot_id", "label"])
        for k in sorted(labels):
            w.writerow([k, labels[k]])
    tmp.replace(path)


PAGE = """<!doctype html><meta charset="utf-8"><title>Label plots</title>
<style>
body{font:15px system-ui;margin:16px;background:#fafafa;color:#222;max-width:1500px}
img{max-width:100%;border:1px solid #ccc;background:#fff;display:block}
button{font-size:16px;padding:10px 18px;margin-right:8px;cursor:pointer}
.b{background:#a3321e;color:#fff;border:0}.n{background:#2f6b3a;color:#fff;border:0}.u{background:#888;color:#fff;border:0}
#bar{margin:12px 0;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
#pid{font-size:17px}
details{background:#fff;border:1px solid #ddd;border-radius:8px;padding:10px 14px;margin-bottom:14px}
summary{font-weight:600;font-size:16px;cursor:pointer}
.steps li{margin:4px 0}
.ex{margin:14px 0}
.ex h4{margin:6px 0}
.tag{display:inline-block;padding:1px 8px;border-radius:4px;color:#fff;font-size:13px;margin-right:6px}
</style>
<details id=guide open>
<summary>How to label (click to hide)</summary>
<ol class=steps>
<li>Each strip is one small patch of farmland across the 2025 season: <b>every clear image</b>, read left to right and line by line, late Sept to early Dec. A burn often shows on one image only, so check every date.
  <b>Only look inside the cyan box.</b> Everything around it is just context.</li>
<li>Each column is one satellite image. <b>Top row</b> = normal colour. <b>Bottom row</b> = "burn view", where burnt ground
  shows up as <b>dark red / maroon</b>.</li>
<li>Normal season: green crop (Sept–Oct) → light tan/brown after harvest → green again as wheat comes up (Dec).</li>
<li>A burn: inside the box, on one or more dates (usually late Oct to mid Nov), it turns <b>charcoal / black</b> on top
  and <b>dark red</b> below. Burnt ground stays dark for a few days to a couple of weeks, then gets ploughed.</li>
<li>Not a burn: <b>dark blue</b> in the bottom row = wet soil after irrigation, before sowing. Dark green = new crop.</li>
</ol>
<div class=ex><h4><span class=tag style="background:#a3321e">Burnt</span>On <b>06 Nov</b> the box goes black (top) and dark red (bottom).</h4><img src="/guide/burnt.png"></div>
<div class=ex><h4><span class=tag style="background:#2f6b3a">Not burnt</span>The box stays tan all season. The black fields on <b>06 Nov</b> and the dark blue (wet) fields on <b>24–27 Nov</b> are neighbours, not this plot.</h4><img src="/guide/not_burnt.png"></div>
<div class=ex><h4><span class=tag style="background:#888">Unsure</span>Box is at a village edge next to a road, partly buildings, partly field. When you can't tell in ~5 seconds, press U.</h4><img src="/guide/unsure.png"></div>
<p>Rule of thumb: <b>B</b> only if most of the box clearly goes black + dark red on some date. Mixed, edge of a dark field, or
not farmland → <b>U</b>. Everything else → <b>N</b>. Most plots will be N; that's expected.</p>
</details>
<div id=bar><b id=pid></b><span id=prog></span></div>
<img id=img>
<div id=bar>
<button class=b onclick="mark('burnt')">Burnt (B)</button>
<button class=n onclick="mark('not_burnt')">Not burnt (N)</button>
<button class=u onclick="mark('unsure')">Unsure (U)</button>
<button onclick="back()">Back (&larr;)</button>
</div>
<script>
let ids=[], labels={}, i=0;
async function load(){const r=await fetch('/state');const s=await r.json();ids=s.ids;labels=s.labels;
 i=ids.findIndex(x=>!(x in labels)); if(i<0) i=ids.length; if(Object.keys(labels).length) document.getElementById('guide').open=false; show();}
function show(){const done=Object.keys(labels).length;
 document.getElementById('prog').textContent=`${done} / ${ids.length} labelled`;
 if(i>=ids.length){document.getElementById('pid').textContent='All done. You can close this page.';document.getElementById('img').src='';return;}
 const id=ids[i];document.getElementById('pid').textContent='Plot '+id+(labels[id]?' (was: '+labels[id]+')':'');
 document.getElementById('img').src='/chip/'+id+'.png';}
async function mark(l){if(i>=ids.length)return;const id=ids[i];labels[id]=l;
 await fetch('/label',{method:'POST',body:JSON.stringify({plot_id:id,label:l})});
 i++; while(i<ids.length && ids[i] in labels) i++; show();}
function back(){if(i>0){i--;show();}}
document.onkeydown=e=>{const k=e.key.toLowerCase();if(k=='b')mark('burnt');else if(k=='n')mark('not_burnt');
 else if(k=='u')mark('unsure');else if(e.key=='ArrowLeft')back();};
load();
</script>"""


def serve(plot_ids: list[str], chips: Path, out: Path, port: int = 8765, guide: Path | None = None) -> None:
    labels = read_labels(out)
    guide = guide or chips.parent / "guide"

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self.send(200, PAGE.encode(), "text/html; charset=utf-8")
            elif self.path == "/state":
                self.send(200, json.dumps({"ids": plot_ids, "labels": labels}).encode(), "application/json")
            elif self.path.startswith(("/chip/", "/guide/")):
                base = chips if self.path.startswith("/chip/") else guide
                p = base / Path(self.path).name
                if p.parent == base and p.exists():
                    self.send(200, p.read_bytes(), "image/png")
                else:
                    self.send(404, b"", "text/plain")
            else:
                self.send(404, b"", "text/plain")

        def do_POST(self):
            if self.path != "/label":
                return self.send(404, b"", "text/plain")
            n = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(n))
            if d.get("plot_id") in plot_ids and d.get("label") in LABELS:
                labels[d["plot_id"]] = d["label"]
                write_labels(out, labels)
                self.send(200, b"ok", "text/plain")
            else:
                self.send(400, b"bad label", "text/plain")

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"{datetime.now():%H:%M} labelling at http://127.0.0.1:{port}  ({len(labels)}/{len(plot_ids)} done)")
    srv.serve_forever()
