"""Planted-bug check for the decision rules: apply one small bug at a time to a copy of the package and make sure
the tests fail. Exits non-zero if any bug survives.

usage: uv run python scripts/plant_bugs.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "src/parali/rules.py"

BUGS = [
    ("drop >= nir_drop becomes >", "if drop >= th.nir_drop and dark:", "if drop > th.nir_drop and dark:"),
    ("burn share check flipped", "dark = b.dark(th.dark_nbr) >= th.burn_share", "dark = b.dark(th.dark_nbr) > th.burn_share"),
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
    ("dark threshold ignored", "x.dark(th.dark_nbr) >= th.burn_share for x in after",
     "x.dark_share >= th.burn_share for x in after"),
]


def main():
    survived = []
    src = (ROOT / TARGET).read_text(encoding="utf-8")
    for name, old, new in BUGS:
        if old not in src:
            print(f"SKIP  {name}: pattern not found")
            survived.append(name)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "src", Path(tmp) / "src")
            (Path(tmp) / TARGET).write_text(src.replace(old, new, 1), encoding="utf-8")
            env = {**os.environ, "PYTHONPATH": str(Path(tmp) / "src")}
            r = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider",
                                "tests/test_rules.py", "tests/test_service.py", "tests/test_evaluate.py"],
                               cwd=ROOT, env=env, capture_output=True, text=True)
        caught = r.returncode != 0
        print(f"{'caught' if caught else 'SURVIVED':8} {name}")
        if not caught:
            survived.append(name)
    print(f"\n{len(BUGS) - len(survived)}/{len(BUGS)} planted bugs caught")
    sys.exit(1 if survived else 0)


if __name__ == "__main__":
    main()
