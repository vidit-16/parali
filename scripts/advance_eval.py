"""2024 rule verdict vs 2025 hand label, on labelled plots. Weighted by stratum like the main evaluation."""
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from parali import firms
from parali.area import AreaStack
from parali.evaluate import nearest_fire_m
from parali.features import field_features
from parali.fields import load_fields
from parali.label import read_labels
from parali.rules import Thresholds, decide

plots = load_fields("data/eval/plots.geojson")
labels = read_labels(Path("data/eval/labels.csv"))
lab = [p for p in plots if labels.get(p.id) in ("burnt", "not_burnt")]
th = Thresholds.load()
st24 = AreaStack.load(Path("data/cache/west_kaithal_2024.npz"))
H = st24.histories(lab, inner_buffer_m=0)
fires = firms.load(Path("data/firms/kaithal_2025.csv"))  # 2025 points only; 2024 FIRMS not fetched, rule run without fire input

S, E = date(2024, 10, 1), date(2024, 11, 30)
per_stratum = Counter(p.props["stratum"] for p in lab)
w = {p.id: p.props["stratum_size"] / per_stratum[p.props["stratum"]] for p in lab}

v24 = {}
for p in lab:
    d = decide(field_features(H[p.id]), th, 0, S, E)
    v24[p.id] = "clean" if d.outcome == "auto_approved" else ("burn" if d.outcome == "possible_burn" else "unclear")

tab = defaultdict(float)
n = Counter()
for p in lab:
    tab[(v24[p.id], labels[p.id])] += w[p.id]
    n[(v24[p.id], labels[p.id])] += 1
print("2024 rule verdict x 2025 label (counts / weighted):")
for k in sorted(n):
    print(f"  {k[0]:8} 2024 -> {k[1]:10} 2025: {n[k]:3} plots, weight {tab[k]:.0f}")

def share(v):
    tot = sum(x for (a, b), x in tab.items() if a == v)
    bur = tab.get((v, "burnt"), 0)
    return bur / tot if tot else float("nan"), tot

for v in ("clean", "unclear", "burn"):
    s, tot = share(v)
    print(f"burnt in 2025 among 2024-{v}: {s:.1%}  (weight {tot:.0f})")
all_tot = sum(tab.values())
all_b = sum(x for (a, b), x in tab.items() if b == "burnt")
print(f"burnt in 2025 overall: {all_b / all_tot:.1%}")
eligible = share("clean")[1] / all_tot
print(f"share of fields eligible for advance (2024 clean): {eligible:.1%}")
burnt25 = [p.id for p in lab if labels[p.id] == "burnt"]
print("2025 burnt plots and their 2024 verdict:", [(i, v24[i]) for i in burnt25])
nc = sum(x for (a, b), x in tab.items() if a != "clean")
nc_b = sum(x for (a, b), x in tab.items() if a != "clean" and b == "burnt")
print(f"burnt in 2025 among 2024-not-clean: {nc_b / nc:.1%}  (weight {nc:.0f})")
