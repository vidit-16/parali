from datetime import date, timedelta

import pytest
from shapely.geometry import box

from parali.evaluate import Case, _rates, cross_validate, fit, score, split
from parali.features import DateFeatures
from parali.fields import Field
from parali.rules import Thresholds

TH = Thresholds(min_valid_share=0.6, min_clear_images=4, dark_nbr=-0.1, burn_share=0.3, nir_drop=0.35,
                persist_images=2, partial_share=0.1, max_burn_brightness=0.0, fire_radius_m=750)
D0 = date(2025, 10, 1)
START, END = date(2025, 10, 1), date(2025, 11, 30)


def feats(burn=False, wet=False):
    nirs = [0.32, 0.30, 0.28, 0.26, 0.25, 0.24, 0.24, 0.23]
    out = [DateFeatures(D0 + timedelta(days=3 * i), 16, 16, v, 0.2, 0.15, 0.2, 1.5, 0.10, 0.0)
           for i, v in enumerate(nirs)]
    if burn or wet:
        bright = 0.04 if burn else 0.11
        for i in (4, 5):
            out[i] = DateFeatures(out[i].date, 16, 16, 0.12, 0.17, 0.18, -0.2, 2.0, bright, 0.9)
    return out


def case(pid, label, stratum="near", size=100, n_in_stratum=1, fires=0, **kw):
    p = Field(pid, box(76, 29, 76.001, 29.001), {"stratum": stratum, "stratum_size": size})
    return Case(p, label, feats(**kw), 100.0 if fires else float("inf"), size / n_in_stratum)


def test_rates_weighted():
    r = _rates([(True, True, 1), (False, True, 3), (True, False, 1), (False, False, 5)])
    assert r["precision"] == pytest.approx(0.25)
    assert r["recall"] == pytest.approx(0.5)
    assert r["wrongful_burnt_rate"] == pytest.approx(3 / 8)


def test_score_counts_and_baseline():
    cases = [case("a", "burnt", burn=True, fires=1), case("b", "not_burnt"), case("c", "not_burnt", fires=1),
             case("d", "unsure")]
    s = score(cases, TH, START, END)
    assert s["used"] == 3 and s["unsure"] == 1 and s["burnt_labels"] == 1
    assert s["rules_possible_burn"]["recall"] == 1.0
    assert s["firms_baseline"]["wrongful_burnt_rate"] == pytest.approx(0.5)
    assert s["outcomes"]["b"] == "auto_approved"
    assert s["outcomes"]["c"] == "needs_review"


def test_strata_weights_change_estimates():
    near = [case("n1", "burnt", "near", 100, 2, burn=True), case("n2", "not_burnt", "near", 100, 2)]
    far = [case("f1", "not_burnt", "far", 1000, 1)]
    s = score(near + far, TH, START, END)
    assert s["est_burnt_share"] == pytest.approx(50 / 1100)


def test_fit_picks_brightness_to_separate_wet_soil():
    cases = ([case(f"b{i}", "burnt", burn=True) for i in range(5)]
             + [case(f"w{i}", "not_burnt", wet=True) for i in range(5)]
             + [case(f"c{i}", "not_burnt") for i in range(5)])
    th, s = fit(cases, TH, START, END)
    assert th.max_burn_brightness > 0
    assert s["rules_possible_burn"]["wrongful_burnt_rate"] == 0
    assert s["rules_possible_burn"]["recall"] == 1.0


def test_split_is_deterministic_and_complete():
    cases = [case(f"p{i:03d}", "not_burnt") for i in range(20)]
    a, b = split(cases)
    assert len(a) + len(b) == 20 and {c.plot.id for c in a}.isdisjoint({c.plot.id for c in b})
    assert [c.plot.id for c in split(cases)[0]] == [c.plot.id for c in a]


def test_cross_validate_reports_held_out():
    cases = ([case(f"b{i}", "burnt", burn=True) for i in range(6)]
             + [case(f"w{i}", "not_burnt", wet=True) for i in range(6)])
    out = cross_validate(cases, TH, START, END)
    assert len(out) == 2 and all("test" in r for r in out)
