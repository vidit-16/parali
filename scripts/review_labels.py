"""Blind review of the plots whose full-season strips were relabelled by Claude (labels_claude.csv).

The labeller sees the full strip for each plot and marks burnt / not burnt / unsure without seeing Claude's call.
Their answers go to labels_review.csv; the earlier full-strip relabels they made (relabel_full.csv) count as
already done. scripts/finalize_labels.py then builds the evaluation labels from the labeller's own calls only.

usage: uv run python scripts/review_labels.py            (Patran on :8765, Kaithal on :8766)
"""
import threading
from pathlib import Path

from parali.label import read_labels, serve, write_labels

ROOT = Path(__file__).resolve().parents[1]
AREAS = [("Patran", ROOT / "data/eval", 8765), ("Kaithal", ROOT / "data/eval/kaithal", 8766)]


def start(name: str, d: Path, port: int) -> threading.Thread:
    ids = sorted(read_labels(d / "labels_claude.csv"))
    out = d / "labels_review.csv"
    done = read_labels(out)
    earlier = {k: v for k, v in read_labels(d / "relabel_full.csv").items() if k in ids and k not in done}
    if earlier:
        write_labels(out, {**done, **earlier})
    print(f"{name}: {len(ids)} plots, {len(read_labels(out))} done  ->  http://127.0.0.1:{port}")
    t = threading.Thread(target=serve, args=(ids, d / "chips_full", out, port), daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    threads = [start(*a) for a in AREAS]
    for t in threads:
        t.join()
