import argparse
import csv
import sys
from datetime import date
from pathlib import Path

from parali import firms
from parali.features import field_features
from parali.fields import load_fields
from parali.history import FieldHistory, build_histories


def cmd_firms(a):
    bbox = tuple(float(v) for v in a.bbox.split(","))
    fires = firms.fetch(bbox, date.fromisoformat(a.start), date.fromisoformat(a.end))
    firms.save(fires, Path(a.out))
    print(f"{len(fires)} fire points -> {a.out}")


def cmd_history(a):
    fields = load_fields(a.fields)
    out = Path(a.out)
    hist = build_histories(fields, a.start, a.end, tile=a.tile)
    for fid, h in hist.items():
        h.save(out / f"{fid}.npz")
    print(f"{len(hist)} field histories -> {out}")


def cmd_area(a):
    from parali.area import fetch_area
    bbox = tuple(float(v) for v in a.bbox.split(","))
    stack = fetch_area(bbox, a.start, a.end, tile=a.tile, log=lambda m: print(m, flush=True))
    stack.save(Path(a.out))
    print(f"{len(stack.dates)} dates, grid {stack.scl.shape[1:]} -> {a.out}")


def cmd_plots(a):
    from parali.area import AreaStack
    from parali.fields import save_fields
    from parali.label import render_strip
    from parali.plots import sample_plots
    stack = AreaStack.load(Path(a.area))
    plots = sample_plots(stack, firms.load(Path(a.firms)), per_stratum=a.per_stratum)
    save_fields(plots, Path(a.out))
    chips = Path(a.chips)
    for i, p in enumerate(plots, 1):
        render_strip(stack, p, chips / f"{p.id}.png")
        if i % 25 == 0:
            print(f"  {i}/{len(plots)} chips", flush=True)
    print(f"{len(plots)} plots -> {a.out}, chips -> {chips}")


def cmd_plots_extra(a):
    from parali.area import AreaStack
    from parali.fields import save_fields
    from parali.label import render_strip
    from parali.plots import add_signal_strata
    stack = AreaStack.load(Path(a.area))
    old = load_fields(a.plots)
    plots = add_signal_strata(stack, firms.load(Path(a.firms)), old, extra=a.extra)
    save_fields(plots, Path(a.plots))
    new = [p for p in plots if p.props.get("round") == 2]
    for p in new:
        render_strip(stack, p, Path(a.chips) / f"{p.id}.png")
    sizes = {}
    for p in plots:
        sizes.setdefault(p.props["stratum"], [p.props["stratum_size"], 0])[1] += 1
    for k, (size, n) in sorted(sizes.items()):
        print(f"  {k:10} population {size:6}  plots {n}")
    print(f"{len(new)} new plots -> {a.plots}")


def cmd_label(a):
    from parali.label import serve
    ids = [f.id for f in load_fields(a.plots)]
    serve(ids, Path(a.chips).resolve(), Path(a.out), port=a.port)


def _fmt(v):
    return "-" if v is None else f"{v:.1%}"


def _print_score(title, s):
    r, b, c = s["rules_possible_burn"], s["firms_baseline"], s["rules_not_auto_approved"]
    print(f"\n{title}  ({s['used']} plots, {s['burnt_labels']} burnt, {s['unsure']} unsure left out)")
    print(f"  auto-approved {_fmt(s['auto_approved_share'])}  review {_fmt(s['review_share'])}  "
          f"possible burn {_fmt(s['possible_burn_share'])}")
    print(f"  {'':24}{'precision':>10}{'recall':>9}{'wrongful':>10}")
    print(f"  {'rules: possible_burn':24}{_fmt(r['precision']):>10}{_fmt(r['recall']):>9}{_fmt(r['wrongful_burnt_rate']):>10}")
    print(f"  {'rules: not approved':24}{_fmt(c['precision']):>10}{_fmt(c['recall']):>9}{_fmt(c['wrongful_burnt_rate']):>10}")
    print(f"  {'FIRMS only (375 m)':24}{_fmt(b['precision']):>10}{_fmt(b['recall']):>9}{_fmt(b['wrongful_burnt_rate']):>10}")
    print(f"  burnt plots auto-approved: {_fmt(s['burnt_auto_approved'])}")


def cmd_evaluate(a):
    import json
    from dataclasses import asdict
    from parali.area import AreaStack
    from parali.evaluate import build_cases, cross_validate, fit, score
    from parali.label import read_labels
    from parali.rules import Thresholds
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    th = Thresholds.load()
    plots = load_fields(a.plots)
    labels = read_labels(Path(a.labels))
    hist = AreaStack.load(Path(a.area)).histories(plots, inner_buffer_m=0)
    cases = build_cases(plots, labels, hist, firms.load(Path(a.firms)), start, end)
    current = score(cases, th, start, end)
    _print_score("Current rules.toml", current)
    cv = cross_validate(cases, th, start, end)
    for i, r in enumerate(cv, 1):
        _print_score(f"Held-out half {i} (thresholds fitted on the other half)", r["test"])
    best, best_s = fit(cases, th, start, end)
    print(f"\nFitted on all labels: {asdict(best)}")
    out = {"current": current, "cross_validation": [{"thresholds": asdict(r["thresholds"]), "test": r["test"]} for r in cv],
           "fitted_all": {"thresholds": asdict(best), "score": best_s}}
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"-> {a.out}")


def cmd_demo(a):
    from parali.server import serve
    speaker = transcriber = backend = None
    if a.aws:  # real Polly, Transcribe and Bedrock with your AWS credentials
        from functools import partial
        from parali.agent import BedrockBackend
        from parali.speech import transcribe_pcm
        from parali.tts import polly_mp3
        speaker = partial(polly_mp3, region="us-west-2")
        transcriber = partial(transcribe_pcm, region="us-west-2")
        backend = BedrockBackend()
    serve(Path(a.state), port=a.port, speaker=speaker, officer_pin=a.pin, transcriber=transcriber,
          agent_backend=backend)


def cmd_features(a):
    paths = sorted(Path(a.history).glob("*.npz"))
    w = csv.writer(sys.stdout)
    header = False
    for p in paths:
        h = FieldHistory.load(p)
        for d in field_features(h):
            row = {"field_id": h.field_id, **d.as_dict()}
            if not header:
                w.writerow(row.keys())
                header = True
            w.writerow(round(v, 4) if isinstance(v, float) else v for v in row.values())


def main(argv=None):
    p = argparse.ArgumentParser(prog="parali")
    sub = p.add_subparsers(required=True)

    s = sub.add_parser("firms", help="download FIRMS fire points")
    s.add_argument("--bbox", required=True, help="west,south,east,north")
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_firms)

    s = sub.add_parser("history", help="read Sentinel-2 pixels for every field and date")
    s.add_argument("--fields", required=True)
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--tile")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_history)

    s = sub.add_parser("area", help="cache every scene over a study area")
    s.add_argument("--bbox", required=True, help="west,south,east,north")
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--tile")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_area)

    s = sub.add_parser("plots", help="sample evaluation plots and render labelling images")
    s.add_argument("--area", required=True)
    s.add_argument("--firms", required=True)
    s.add_argument("--per-stratum", type=int, default=70)
    s.add_argument("--out", required=True)
    s.add_argument("--chips", required=True)
    s.set_defaults(func=cmd_plots)

    s = sub.add_parser("plots-extra", help="re-stratify by burn signal and add plots from signal strata")
    s.add_argument("--area", required=True)
    s.add_argument("--firms", required=True)
    s.add_argument("--plots", required=True)
    s.add_argument("--chips", required=True)
    s.add_argument("--extra", type=int, default=40)
    s.set_defaults(func=cmd_plots_extra)

    s = sub.add_parser("label", help="open the labelling page")
    s.add_argument("--plots", required=True)
    s.add_argument("--chips", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--port", type=int, default=8765)
    s.set_defaults(func=cmd_label)

    s = sub.add_parser("evaluate", help="score rules and FIRMS baseline against hand labels")
    s.add_argument("--area", required=True)
    s.add_argument("--plots", required=True)
    s.add_argument("--labels", required=True)
    s.add_argument("--firms", required=True)
    s.add_argument("--start", default="2025-10-01")
    s.add_argument("--end", default="2025-11-30")
    s.add_argument("--out", default="data/eval/results.json")
    s.set_defaults(func=cmd_evaluate)

    s = sub.add_parser("demo", help="run the web app locally on saved 2025 data")
    s.add_argument("--state", default="data/local")
    s.add_argument("--port", type=int, default=8080)
    s.add_argument("--pin", default="2468", help="officer PIN for the demo")
    s.add_argument("--aws", action="store_true", help="use Polly, Transcribe and Bedrock (needs AWS credentials)")
    s.set_defaults(func=cmd_demo)

    s = sub.add_parser("features", help="print per-date features as CSV")
    s.add_argument("--history", required=True)
    s.set_defaults(func=cmd_features)

    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
