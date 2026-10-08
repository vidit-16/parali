"""Write the measured numbers the web app shows (web/data/numbers.json) from the evaluation outputs."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

res = json.loads((ROOT / "data/eval/results.json").read_text(encoding="utf-8"))
cur = res["current"]
cv = [r["test"] for r in res["cross_validation"]]
adv_txt = (ROOT / "data/eval/advance_2024_2025.txt").read_text(encoding="utf-8")


def pct(v):
    return None if v is None else round(100 * v, 1)


def grab(label):
    m = re.search(rf"{re.escape(label)}: ([\d.]+)%", adv_txt)
    return float(m.group(1)) if m else None


labels = [l.split(",")[1] for l in (ROOT / "data/eval/labels.csv").read_text().splitlines()[1:]]
numbers = {
    "labelled_plots": len(labels),
    "burnt_labels": labels.count("burnt"),
    "rules": {
        "burnt_auto_approved": pct(cur["burnt_auto_approved"]),
        "auto_approved": pct(cur["auto_approved_share"]),
        "review": pct(cur["review_share"]),
        "possible_burn": pct(cur["possible_burn_share"]),
        "clean_flagged": pct(cur["rules_possible_burn"]["wrongful_burnt_rate"]),
    },
    "firms": {
        "clean_flagged": pct(cur["firms_baseline"]["wrongful_burnt_rate"]),
        "burns_caught": pct(cur["firms_baseline"]["recall"]),
    },
    "held_out": {
        "auto_approved": [pct(t["auto_approved_share"]) for t in cv],
        "burnt_auto_approved": [pct(t["burnt_auto_approved"]) for t in cv],
        "clean_flagged": [pct(t["rules_possible_burn"]["wrongful_burnt_rate"]) for t in cv],
        "firms_clean_flagged": [pct(t["firms_baseline"]["wrongful_burnt_rate"]) for t in cv],
    },
    "advance": {
        "eligible_share": grab("share of fields eligible for advance (2024 clean)"),
        "burnt_if_clean_last_year": grab("burnt in 2025 among 2024-clean"),
        "burnt_if_burnt_last_year": grab("burnt in 2025 among 2024-burn"),
        "burnt_if_not_clean_last_year": grab("burnt in 2025 among 2024-not-clean"),
        "burnt_overall": grab("burnt in 2025 overall"),
    },
    "context": {
        "delhi_pm25_share_peak": 26.2,
        "delhi_pm25_source": "IITM decision support system via CPCB bulletin, 22 Nov 2024",
        "upfront_trial_gain_pp": "8-11",
        "upfront_trial_source": "Jack, Jayachandran, Kala, Pande; J-PAL / MIT CEEPR working paper (Punjab RCT)",
        "kaithal_applied": "18,329 of 49,215",
        "incentive_per_acre": 1000, "advance_share": 50,
    },
}
out = ROOT / "web/data/numbers.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(numbers, indent=1), encoding="utf-8")
print(json.dumps(numbers, indent=1))
