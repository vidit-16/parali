"""Parity: every language has every piece of text, every screen shows the same numbers for a claim, and the
web app and the server use the same smoke estimate."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from parali import messages, notice, season, whatsapp
from tests.test_payments import FakeRazorpay, confirmed_burn, deps, review
from tests.test_season import store  # noqa: F401  (fixture)

WEB = Path(__file__).resolve().parents[1] / "web" / "js"
# Haryana officers read Hindi, so the officer desk has no Haryanvi table (pick() maps it to Hindi)
LANGS = {"farmer2.js": ["en", "hi", "pa", "hr"], "explorer.js": ["en", "hi", "pa", "hr"], "officer2.js": ["en", "hi", "pa"]}

KEYS_JS = r"""
const src = require("fs").readFileSync(process.argv[1], "utf8");
const start = src.indexOf("const T = {");
const end = src.indexOf("\n};", start) + 3;
const rupees = (x) => x, esc = (x) => x;
const T = eval("(" + src.slice(start, end).replace("const T = ", "").replace(/;$/, "") + ")");
const keys = (o, p = "") => Object.entries(o).flatMap(([k, v]) =>
  v && typeof v === "object" && !Array.isArray(v) ? keys(v, p + k + ".") : [p + k + (Array.isArray(v) ? "[" + v.length + "]" : "")]);
console.log(JSON.stringify(Object.fromEntries(Object.entries(T).map(([l, v]) => [l, keys(v)]))));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("name", sorted(LANGS))
def test_every_language_has_every_web_string(name):
    out = subprocess.run(["node", "-e", KEYS_JS, str(WEB / name)], capture_output=True, text=True, check=True).stdout
    tables = json.loads(out)
    assert sorted(tables) == sorted(LANGS[name])
    en = set(tables["en"])
    for lang, keys in tables.items():
        assert set(keys) == en, f"{name} {lang}: missing {sorted(en - set(keys))}, extra {sorted(set(keys) - en)}"


def test_every_whatsapp_short_text_is_in_every_language():
    english_only = {"intro", "state", "pick", "list"}  # the farmer picker comes before a language is known
    want = set(whatsapp.SHORT["en"]) - english_only
    for lang in ("hi", "pa", "hr"):
        assert set(whatsapp.SHORT[lang]) == want, lang


def test_smoke_estimate_is_the_same_in_the_web_app():
    assert season.PM25_KG_PER_ACRE == pytest.approx(18.72)
    for name in ("shared.js", "explorer.js"):
        src = (WEB / name).read_text(encoding="utf-8")
        assert "PM25_KG_PER_ACRE = 2.6 * 0.8 * 9" in src, name
        assert not re.search(r"acres[^;\n]*\*\s*19\b", src), f"{name} still rounds to 19 kg an acre"


def test_a_confirmed_burn_shows_the_same_numbers_everywhere(store):  # noqa: F811
    c = review(deps(store, FakeRazorpay()), confirmed_burn(store))
    amount = messages.rupees(c["settlement"]["recover"])
    assert amount == messages.rupees(c["recovery"]["amount"]) == messages.rupees(c["advance"]["amount"])
    for lang in ("en", "hi", "pa", "hr"):
        assert amount in whatsapp.short_status(c, lang), lang
        assert amount in whatsapp.money_line(c, lang), lang
        assert amount in c["message"][lang], lang
    html = notice.render(c, "/e.png")
    assert html.count(f"₹{amount}") >= 3  # amount row, how to respond, local sections
    assert f"≈ {season.smoke_kg(c['acres'])} kg" in html
    assert c["recovery"]["url"] in whatsapp.short_status(c, "en")


def test_an_approved_claim_shows_the_same_balance_everywhere(store):  # noqa: F811
    from tests.test_payments import TH, service, stacks_by_year
    cl = service.create_claim(store, "f1", "2025-10-01", "2025-11-30")
    st = stacks_by_year(None, None)
    service.assess_advance(store, cl["id"], st, [], TH, "2024-10-01", "2024-11-30")
    service.disburse_advance(store, cl["id"], "dept")
    c = service.process_claim(store, cl["id"], st, [], TH)
    assert c["status"] == "auto_approved" and c["settlement"]["state"] == "balance_due"
    bal = messages.rupees(c["settlement"]["balance"])
    assert c["settlement"]["balance"] + c["advance"]["amount"] == c["settlement"]["total"]
    for lang in ("en", "hi", "pa", "hr"):
        assert bal in whatsapp.short_status(c, lang) and bal in whatsapp.money_line(c, lang), lang
        assert str(season.smoke_kg(c["acres"])) in whatsapp.short_status(c, lang), lang
