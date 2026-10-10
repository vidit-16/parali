"""Build the evaluation labels from the human labeller's calls only, score the rules against them, and report how
often the labeller and Claude agreed on the plots both looked at.

labels_user_full.csv = labels.csv (first pass) with labels_review.csv (blind full-strip review) on top.
Writes data/eval/results_user.json and prints the headline numbers to put on the map and in the writeup.

usage: uv run python scripts/finalize_labels.py
"""
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from parali import firms
from parali.area import AreaStack
from parali.evaluate import build_cases, score
from parali.fields import Field, load_fields
from parali.label import read_labels, write_labels
from parali.rules import Thresholds

ROOT = Path(__file__).resolve().parents[1]
AREAS = [("data/cache/west_kaithal_2025.npz", ROOT / "data/eval"), ("data/cache/kaithal_west_2025.npz", ROOT / "data/eval/kaithal")]
FIRMS = ["data/firms/kaithal_2025.csv", "data/firms/belt_2025.csv"]
START, END = date(2025, 10, 1), date(2025, 11, 30)


def main():
    fire_list = [f for p in FIRMS for f in firms.load(ROOT / p)]
    cases, agree, pending = [], Counter(), 0
    for i, (area, d) in enumerate(AREAS):
        first, review, claude = (read_labels(d / n) for n in ("labels.csv", "labels_review.csv", "labels_claude.csv"))
        pending += len(set(claude) - set(review))
        for k in set(review) & set(claude):
            agree["same" if review[k] == claude[k] else "different"] += 1
        labels = {**first, **review}
        write_labels(d / "labels_user_full.csv", labels)
        tag = d.name if i else ""
        plots = [Field(f"{tag}:{p.id}" if tag else p.id, p.geometry, p.props) for p in load_fields(d / "plots.geojson")]
        hist = AreaStack.load(ROOT / area).histories(plots, inner_buffer_m=0)
        cases += build_cases(plots, {(f"{tag}:{k}" if tag else k): v for k, v in labels.items()}, hist, fire_list, START, END)
    s = score(cases, Thresholds.load(), START, END)
    (ROOT / "data/eval/results_user.json").write_text(json.dumps({"current": s}, indent=1, default=str), encoding="utf-8")

    pct = lambda v: f"{100 * v:.1f}%"  # noqa: E731
    if pending:
        print(f"note: {pending} plots not reviewed yet; they keep the first-pass label")
    n = agree["same"] + agree["different"]
    if n:
        print(f"labeller and Claude agree on {agree['same']} of {n} reviewed plots ({pct(agree['same'] / n)})")
    print(f"{s['used']} labelled fields, {s['burnt_labels']} burnt, {s['burnt_auto_approved']:.0%} of burnt auto-approved")
    print(f"wrongly flagged clean fields: Saakshi {pct(s['rules_possible_burn']['wrongful_burnt_rate'])}, "
          f"fire alerts {pct(s['firms_baseline']['wrongful_burnt_rate'])}")
    print(f"possible-burn precision {pct(s['rules_possible_burn']['precision'])}, recall {pct(s['rules_possible_burn']['recall'])}; "
          f"fire-alert recall {pct(s['firms_baseline']['recall'])}")
    sys.exit(0)


if __name__ == "__main__":
    main()
