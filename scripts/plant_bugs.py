"""Planted-bug (mutation) check: apply one small bug at a time to a copy of the package and make sure the tests
fail. Covers the decision rules, the money (settlement, payment links, appeals), the checks that guard the
officer desk and the payment and WhatsApp callbacks, and the numbers the farmer is told. Exits non-zero if any
bug survives.

usage: uv run python scripts/plant_bugs.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES_TESTS = ["tests/test_rules.py", "tests/test_service.py", "tests/test_evaluate.py"]
MONEY_TESTS = ["tests/test_season.py", "tests/test_payments.py", "tests/test_money_properties.py", "tests/test_parity.py",
               "tests/test_whatsapp.py", "tests/test_api.py"]

RULES = [
    ("drop >= nir_drop becomes >", "if drop >= th.nir_drop and dark:", "if drop > th.nir_drop and dark:"),
    ("burn share check flipped", "dark = th.dark(b) >= th.burn_share", "dark = th.dark(b) > th.burn_share"),
    ("persistence ignored", "if lasting:", "if events:"),
    ("persist length off by one", "len(after) == th.persist_images", "len(after) >= th.persist_images - 1"),
    ("partial share boundary", "if max_dark >= th.partial_share:", "if max_dark > th.partial_share:"),
    ("fire rule removed", "    if fires_nearby:\n", "    if False:\n"),
    ("clear image needs fewer", "if len(clear_in) < th.min_clear_images:", "if len(clear_in) < th.min_clear_images - 1:"),
    ("valid share boundary", "f.valid_share >= th.min_valid_share", "f.valid_share > th.min_valid_share"),
    ("brightness check inverted", "dark = dark and b.brightness <= th.max_burn_brightness",
     "dark = dark and b.brightness >= th.max_burn_brightness"),
    ("window start ignored", "(start is None or f.date >= start)", "(True)"),
    ("small field check removed", "if inside and inside[0].n_pixels < config.MIN_FIELD_PIXELS:", "if False:"),
    ("possible burn becomes final", 'return Decision(POSSIBLE_BURN, "burn_scar_persistent",',
     'return Decision("rejected", "burn_scar_persistent",'),
    ("dark threshold ignored", "return f.dark(self.dark_nbr, self.dark_max_brightness)", "return f.dark_share"),
    ("pixel brightness ignored", "return f.dark(self.dark_nbr, self.dark_max_brightness)", "return f.dark(self.dark_nbr)"),
]

MONEY = [
    ("src/parali/season.py", "balance ignores the advance", '"balance": total - advance_paid', '"balance": total'),
    ("src/parali/season.py", "recovers the full incentive", '"recover": advance_paid, "total": total,', '"recover": total, "total": total,'),
    ("src/parali/season.py", "recovery and not-payable swapped", '"recover_advance" if advance_paid else "not_payable"',
     '"not_payable" if advance_paid else "recover_advance"'),
    ("src/parali/season.py", "advance is the whole incentive", "round(acres * s.rate_per_acre * s.advance_share)", "round(acres * s.rate_per_acre)"),
    ("src/parali/season.py", "compensation tier boundary", "if acres < limit)", "if acres <= limit)"),
    ("src/parali/season.py", "smoke estimate rounded again", "PM25_KG_PER_ACRE = 2.6 * 0.8 * 9", "PM25_KG_PER_ACRE = 19"),
    ("src/parali/payments.py", "payment link for the full incentive", 'link = rp.create_link(s["recover"],', 'link = rp.create_link(s["total"],'),
    ("src/parali/payments.py", "appeal leaves the link open", 'rec.update(status="cancelled"', 'rec.update(status="issued"'),
    ("src/parali/payments.py", "payment signature not checked", "return hmac.compare_digest(want, params[\"razorpay_signature\"])", "return True"),
    ("src/parali/whatsapp.py", "WhatsApp signature not checked", "return hmac.compare_digest(header[7:], want)", "return True"),
    ("src/parali/api.py", "officer PIN not checked", 'return hmac.compare_digest(given, deps.officer_pin)', "return True"),
    ("src/parali/whatsapp.py", "farmer told the total, not the balance", 'x = rupees(s.get("balance") or 0) if k == "paid"',
     'x = rupees(s.get("total") or 0) if k == "paid"'),
    ("src/parali/whatsapp.py", "English line dropped", 'return en if lang == "en" else f"{en}\\n{make(lang)}"', "return make(lang)"),
]
BUGS = [("src/parali/rules.py", n, o, w, RULES_TESTS) for n, o, w in RULES] + [(f, n, o, w, MONEY_TESTS) for f, n, o, w in MONEY]


def run_tests(tmp: str, tests: list[str]) -> int:
    env = {**os.environ, "PYTHONPATH": str(Path(tmp) / "src")}
    return subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *tests],
                          cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace").returncode


def main():
    # a bug only counts as caught if the same tests pass on an untouched copy
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(ROOT / "src", Path(tmp) / "src")
        for tests in (RULES_TESTS, MONEY_TESTS):
            if run_tests(tmp, tests):
                sys.exit(f"tests fail on the untouched copy: {tests}")
    print("baseline: tests pass on the untouched copy")
    survived = []
    for target, name, old, new, tests in BUGS:
        src = (ROOT / target).read_text(encoding="utf-8")
        if old not in src:
            print(f"SKIP  {name}: pattern not found")
            survived.append(name)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "src", Path(tmp) / "src")
            (Path(tmp) / target).write_text(src.replace(old, new, 1), encoding="utf-8")
            caught = run_tests(tmp, tests) != 0
        print(f"{'caught' if caught else 'SURVIVED':8} {name}")
        if not caught:
            survived.append(name)
    print(f"\n{len(BUGS) - len(survived)}/{len(BUGS)} planted bugs caught")
    sys.exit(1 if survived else 0)


if __name__ == "__main__":
    main()
