"""Recompute the headline evaluation from the label files and check it against the published results and the
figures the map shows. Exits non-zero on any difference.

Scores only the current rules.toml (the full `parali evaluate` also refits thresholds on held-out halves,
which takes much longer and does not change the headline).

usage: uv run python scripts/check_numbers.py
"""
import json
import sys
from datetime import date
from pathlib import Path

from parali import firms
from parali.area import AreaStack
from parali.evaluate import build_cases, score
from parali.fields import Field, load_fields
from parali.label import read_labels
from parali.rules import Thresholds

ROOT = Path(__file__).resolve().parents[1]
AREAS = [("data/cache/west_kaithal_2025.npz", "data/eval/plots.geojson", "data/eval/labels_full_strips.csv"),
         ("data/cache/kaithal_west_2025.npz", "data/eval/kaithal/plots.geojson", "data/eval/kaithal/labels_full_strips.csv")]
FIRMS = ["data/firms/kaithal_2025.csv", "data/firms/belt_2025.csv"]
START, END = date(2025, 10, 1), date(2025, 11, 30)


def main():
    fire_list = [f for p in FIRMS for f in firms.load(ROOT / p)]
    cases = []
    for i, (area, plots_path, labels_path) in enumerate(AREAS):
        tag = Path(plots_path).parent.name if i else ""
        plots = [Field(f"{tag}:{p.id}" if tag else p.id, p.geometry, p.props) for p in load_fields(ROOT / plots_path)]
        labels = {(f"{tag}:{k}" if tag else k): v for k, v in read_labels(ROOT / labels_path).items()}
        hist = AreaStack.load(ROOT / area).histories(plots, inner_buffer_m=0)
        cases += build_cases(plots, labels, hist, fire_list, START, END)
    now = score(cases, Thresholds.load(), START, END)
    published = json.loads((ROOT / "data/eval/results_full_strips.json").read_text(encoding="utf-8"))["current"]

    bad = []
    for k in ("labelled", "used", "burnt_labels", "burnt_auto_approved"):
        if now[k] != published[k]:
            bad.append(f"{k}: now {now[k]}, published {published[k]}")
    for g in ("rules_possible_burn", "firms_baseline"):
        for m in ("precision", "recall", "wrongful_burnt_rate"):
            if abs(now[g][m] - published[g][m]) > 1e-9:
                bad.append(f"{g}.{m}: now {now[g][m]:.4f}, published {published[g][m]:.4f}")

    pct = lambda v: f"{100 * v:.1f}%"  # noqa: E731
    shown = {"rules": pct(now["rules_possible_burn"]["wrongful_burnt_rate"]), "alerts": pct(now["firms_baseline"]["wrongful_burnt_rate"]),
             "used": str(now["used"]), "burnt": str(now["burnt_labels"])}
    page = (ROOT / "web/index.html").read_text(encoding="utf-8") + (ROOT / "web/js/explorer.js").read_text(encoding="utf-8")
    for name, v in shown.items():
        if v not in page:
            bad.append(f"the map does not show {name} = {v}")

    print(f"{now['used']} labelled fields, {now['burnt_labels']} burnt, {now['burnt_auto_approved']:.0%} of burnt auto-approved")
    print(f"wrongly flagged clean fields: Saakshi {shown['rules']}, fire alerts {shown['alerts']}; "
          f"possible-burn precision {pct(now['rules_possible_burn']['precision'])}")
    print("\n".join(["DIFFERS " + b for b in bad]) or "matches the published results and the map")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
