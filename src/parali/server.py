"""Local demo: the same web app and API, backed by files on disk and saved 2025 imagery. No AWS account needed."""
import json
import mimetypes
import shutil
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from parali import firms, service
from parali.api import Deps, handle
from parali.area import AreaStack
from parali.fields import load_fields
from parali.rules import Thresholds
from parali.store import LocalStore

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
DEMO = ROOT / "data" / "demo"


def seed(store: LocalStore, fields_path: Path) -> None:
    from shapely.geometry import mapping
    for f in load_fields(fields_path):
        store.put("fields", f.id, {"id": f.id, **f.props, "geometry": mapping(f.geometry)})


def demo_stacks(stacks_dir: Path):
    def provider(field, start, end):
        return AreaStack.load(stacks_dir / f"{field.id}.npz")
    return provider


def make_deps(state_dir: Path, speaker=None, officer_pin: str | None = None) -> Deps:
    store = LocalStore(state_dir)
    if not store.list("fields"):
        seed(store, DEMO / "fields.geojson")
    th = Thresholds.load()
    fires = firms.load(ROOT / "data" / "firms" / "kaithal_2025.csv")
    stacks = demo_stacks(DEMO / "stacks")

    def run(claim_id):
        try:
            service.process_claim(store, claim_id, stacks, fires, th, speaker)
        except Exception as e:  # keep the server up; show the failure on the claim
            c = store.get("claims", claim_id)
            c["error"] = str(e)
            store.put("claims", claim_id, c)
            raise

    def reset():
        for sub in ("claims", "events", "blobs"):
            shutil.rmtree(state_dir / sub, ignore_errors=True)

    return Deps(store=store, dispatch=lambda cid: threading.Thread(target=run, args=(cid,), daemon=True).start(),
                officer_pin=officer_pin, speaker=speaker, reset=reset)


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *a, deps: Deps, **kw):
        self.deps = deps
        super().__init__(*a, **kw)

    def log_message(self, *a):
        pass

    def _send(self, status, headers, body):
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _api(self, method):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else None
        self._send(*handle(method, self.path.split("?")[0], body, dict(self.headers), self.deps))

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self._api("POST")
        self._send(404, {}, b"")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/api/"):
            return self._api("GET")
        if path.startswith("/blobs/"):
            data = self.deps.store.get_blob(path[len("/blobs/"):])
            if data is None or ".." in path:
                return self._send(404, {}, b"")
            return self._send(200, {"Content-Type": mimetypes.guess_type(path)[0] or "application/octet-stream"}, data)
        name = "index.html" if path in ("/", "") else path.lstrip("/")
        p = (WEB / name).resolve()
        if p.parent != WEB.resolve() or not p.is_file():
            return self._send(404, {}, b"")
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith("javascript"):
            ctype += "; charset=utf-8"
        self._send(200, {"Content-Type": ctype}, p.read_bytes())


def serve(state_dir: Path, port: int = 8080, speaker=None, officer_pin: str | None = None) -> None:
    deps = make_deps(state_dir, speaker, officer_pin)
    srv = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, deps=deps))
    print(f"Parali Check demo at http://127.0.0.1:{port}  (state in {state_dir})"
          + (f"  officer PIN {officer_pin}" if officer_pin else ""))
    srv.serve_forever()
