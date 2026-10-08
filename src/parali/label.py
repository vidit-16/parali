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


def render_strip(stack: AreaStack, plot: Field, out: Path, pad: int = 16, max_dates: int = 12) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    (pr0, pc0, pr1, pc1), (r0, c0, r1, c1) = plot_window(stack, plot, pad)
    keep = []
    for t in range(len(stack.dates)):
        scl = stack.scl[t, pr0:pr1, pc0:pc1]
        if np.mean(~np.isin(scl, (0, 1, 8, 9, 10))) >= 0.8:
            keep.append(t)
    if len(keep) > max_dates:
        keep = [keep[i] for i in np.linspace(0, len(keep) - 1, max_dates).round().astype(int)]

    fig, axes = plt.subplots(2, max(len(keep), 1), figsize=(2.1 * max(len(keep), 1), 4.6), squeeze=False)
    for j, t in enumerate(keep):
        def win(b):
            return stack.band(t, b)[r0:r1, c0:c1]
        rgb = np.dstack([win("red"), win("green"), win("blue")]) / 0.16
        swir = np.dstack([win("swir22") / 0.35, win("nir08") / 0.45, win("red") / 0.2])
        for i, img in enumerate((rgb, swir)):
            ax = axes[i, j]
            ax.imshow(np.clip(np.nan_to_num(img), 0, 1), interpolation="nearest")
            ax.add_patch(Rectangle((pc0 - c0 - 0.5, pr0 - r0 - 0.5), pc1 - pc0, pr1 - pr0,
                                   fill=False, edgecolor="yellow", linewidth=1.2))
            ax.set_xticks([]); ax.set_yticks([])
        axes[0, j].set_title(stack.dates[t].strftime("%d %b"), fontsize=8)
    axes[0, 0].set_ylabel("true colour", fontsize=7)
    axes[1, 0].set_ylabel("SWIR / NIR / red", fontsize=7)
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
body{font:15px system-ui;margin:16px;background:#fafafa;color:#222}
img{max-width:100%;border:1px solid #ccc;background:#fff}
button{font-size:16px;padding:8px 16px;margin-right:8px}
#bar{margin:10px 0}
.help{color:#555;font-size:13px;max-width:900px}
</style>
<p class=help>Yellow square = the plot (80 m). Judge only what is inside it.<br>
<b>Burnt</b>: most of the square turns dark grey or black in the top row on some date after harvest, usually for one
or more dates in a row. In the bottom row a burn looks dark red / maroon.<br>
<b>Not burnt</b>: it fades to tan or brown, or goes dark <i>blue</i> in the bottom row (wet soil after irrigation), then turns green.<br>
<b>Unsure</b>: only part of the square is dark, the edge of a dark field crosses it, or you cannot tell.</p>
<div id=bar><b id=pid></b> &nbsp; <span id=prog></span></div>
<img id=img>
<div id=bar>
<button onclick="mark('burnt')">Burnt (B)</button>
<button onclick="mark('not_burnt')">Not burnt (N)</button>
<button onclick="mark('unsure')">Unsure (U)</button>
<button onclick="back()">Back (&larr;)</button>
</div>
<script>
let ids=[], labels={}, i=0;
async function load(){const r=await fetch('/state');const s=await r.json();ids=s.ids;labels=s.labels;
 i=ids.findIndex(x=>!(x in labels)); if(i<0) i=ids.length; show();}
function show(){const done=Object.keys(labels).length;
 document.getElementById('prog').textContent=`${done} / ${ids.length} labelled`;
 if(i>=ids.length){document.getElementById('pid').textContent='All done';document.getElementById('img').src='';return;}
 const id=ids[i];document.getElementById('pid').textContent=id+(labels[id]?' (was: '+labels[id]+')':'');
 document.getElementById('img').src='/chip/'+id+'.png';}
async function mark(l){if(i>=ids.length)return;const id=ids[i];labels[id]=l;
 await fetch('/label',{method:'POST',body:JSON.stringify({plot_id:id,label:l})});
 i++; while(i<ids.length && ids[i] in labels) i++; show();}
function back(){if(i>0){i--;show();}}
document.onkeydown=e=>{const k=e.key.toLowerCase();if(k=='b')mark('burnt');else if(k=='n')mark('not_burnt');
 else if(k=='u')mark('unsure');else if(e.key=='ArrowLeft')back();};
load();
</script>"""


def serve(plot_ids: list[str], chips: Path, out: Path, port: int = 8765) -> None:
    labels = read_labels(out)

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
            elif self.path.startswith("/chip/"):
                p = chips / Path(self.path).name
                if p.parent == chips and p.exists():
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
