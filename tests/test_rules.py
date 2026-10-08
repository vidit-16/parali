from dataclasses import replace
from datetime import date, timedelta

from parali.features import DateFeatures
from parali.rules import APPROVED, POSSIBLE_BURN, REVIEW, Thresholds, decide

TH = Thresholds(min_valid_share=0.6, min_clear_images=4, dark_nbr=-0.1, burn_share=0.3, nir_drop=0.35,
                persist_images=2, partial_share=0.1, max_burn_brightness=0.0, fire_radius_m=750)

D0 = date(2025, 10, 1)


def day(i, nir=0.30, dark=0.0, valid=20, n=20, bright=0.10):
    return DateFeatures(date=D0 + timedelta(days=3 * i), n_pixels=n, n_valid=valid, nir=nir, swir1=0.2,
                        swir2=0.15, nbr=0.2, mirbi=1.5, brightness=bright, dark_share=dark)


def unburnt():
    nirs = [0.32, 0.30, 0.28, 0.26, 0.25, 0.24, 0.24, 0.23]
    return [day(i, nir=v) for i, v in enumerate(nirs)]


def burnt(at=4, dark=0.8, persist=True):
    out = unburnt()
    out[at] = day(at, nir=0.12, dark=dark)
    if persist:
        out[at + 1] = day(at + 1, nir=0.13, dark=dark)
    return out


def test_clean_field_is_approved():
    d = decide(unburnt(), TH)
    assert d.outcome == APPROVED and d.rule == "no_burn_signal"


def test_persistent_scar_is_possible_burn_never_final():
    d = decide(burnt(), TH)
    assert d.outcome == POSSIBLE_BURN and d.rule == "burn_scar_persistent"
    assert d.burn_date == D0 + timedelta(days=12)
    assert "Officer to confirm" in d.reason


def test_no_code_path_returns_a_final_rejection():
    outcomes = {decide(f, TH, fires_nearby=k).outcome
                for f in (unburnt(), burnt(), burnt(persist=False), burnt(dark=0.15, persist=False))
                for k in (0, 3)}
    assert outcomes <= {APPROVED, REVIEW, POSSIBLE_BURN}


def test_scar_on_one_image_goes_to_review():
    d = decide(burnt(persist=False), TH)
    assert d.outcome == REVIEW and d.rule == "dark_on_one_image"


def test_scar_on_last_image_cannot_be_confirmed_as_persistent():
    feats = unburnt()
    feats[-1] = day(len(feats) - 1, nir=0.10, dark=0.9)
    assert decide(feats, TH).rule == "dark_on_one_image"


def test_partial_scar_goes_to_review():
    feats = unburnt()
    feats[3] = day(3, nir=0.26, dark=0.15)
    d = decide(feats, TH)
    assert d.outcome == REVIEW and d.rule == "partial_scar"


def test_partial_share_boundary():
    feats = unburnt()
    feats[3] = day(3, nir=0.26, dark=0.0999)
    assert decide(feats, TH).outcome == APPROVED
    feats[3] = day(3, nir=0.26, dark=0.10)
    assert decide(feats, TH).rule == "partial_scar"


def test_nir_drop_boundary():
    feats = burnt()
    feats[4] = replace(feats[4], nir=0.26 * 0.66)   # 34% drop from 0.26
    assert decide(feats, TH).outcome != POSSIBLE_BURN
    feats[4] = replace(feats[4], nir=0.26 * 0.64)   # 36% drop
    assert decide(feats, TH).outcome == POSSIBLE_BURN


def test_burn_share_boundary():
    assert decide(burnt(dark=0.2999), TH).outcome != POSSIBLE_BURN
    assert decide(burnt(dark=0.30), TH).outcome == POSSIBLE_BURN


def test_gradual_harvest_decline_is_not_a_burn():
    # dry-down lowers NIR in small steps; dark share rises but never with a sharp drop
    nirs = [0.32, 0.28, 0.24, 0.21, 0.18, 0.16, 0.15, 0.15]
    feats = [day(i, nir=v, dark=0.35 if i >= 5 else 0.0) for i, v in enumerate(nirs)]
    d = decide(feats, TH)
    assert d.outcome == REVIEW and d.rule == "partial_scar"


def test_fire_point_nearby_without_scar_goes_to_review():
    d = decide(unburnt(), TH, fires_nearby=2)
    assert d.outcome == REVIEW and d.rule == "fire_point_nearby_no_scar"


def test_scar_beats_fire_rule():
    assert decide(burnt(), TH, fires_nearby=2).outcome == POSSIBLE_BURN


def test_too_few_clear_images():
    feats = [replace(f, n_valid=5) for f in unburnt()]
    feats[0] = day(0)
    d = decide(feats, TH)
    assert d.outcome == REVIEW and d.rule == "too_few_clear_images"


def test_valid_share_boundary_for_clear_image():
    feats = [replace(f, n_valid=11) for f in unburnt()]  # 55% < 60%
    assert decide(feats, TH).rule == "too_few_clear_images"
    feats = [replace(f, n_valid=12) for f in unburnt()]  # 60%
    assert decide(feats, TH).outcome == APPROVED


def test_small_field_goes_to_review():
    feats = [replace(f, n_pixels=6, n_valid=6) for f in unburnt()]
    assert decide(feats, TH).rule == "field_too_small"


def test_window_excludes_burn_before_claim_start():
    feats = burnt(at=1)
    d = decide(feats, TH, start=D0 + timedelta(days=9))
    assert d.outcome != POSSIBLE_BURN


def test_pre_window_image_used_for_first_step():
    feats = burnt(at=4)
    d = decide(feats, TH, start=feats[4].date)
    assert d.outcome == POSSIBLE_BURN


def test_brightness_check_when_enabled():
    th = replace(TH, max_burn_brightness=0.08)
    feats = burnt()
    feats[4] = replace(feats[4], brightness=0.12)  # dark NBR but not black: e.g. wet ploughed soil
    assert decide(feats, th).outcome != POSSIBLE_BURN
    feats[4] = replace(feats[4], brightness=0.06)
    assert decide(feats, th).outcome == POSSIBLE_BURN


def test_thresholds_file_loads():
    th = Thresholds.load()
    assert 0 < th.burn_share < 1 and th.persist_images >= 1


def test_dropping_the_nir_step_check_would_flag_harvest():
    # the sharp NIR step is what separates a burn from ordinary dry-down
    th = replace(TH, nir_drop=0.0)
    nirs = [0.32, 0.28, 0.24, 0.21, 0.18, 0.16, 0.15, 0.15]
    feats = [day(i, nir=v, dark=0.35 if i >= 5 else 0.0) for i, v in enumerate(nirs)]
    assert decide(feats, TH).outcome != POSSIBLE_BURN
    assert decide(feats, th).outcome == POSSIBLE_BURN


def test_nir_drop_exact_boundary_counts():
    th = replace(TH, nir_drop=0.5)
    feats = burnt()
    feats[3] = replace(feats[3], nir=0.5)
    feats[4] = replace(feats[4], nir=0.25)  # exactly 50%
    assert decide(feats, th).outcome == POSSIBLE_BURN


def test_min_clear_images_exact_boundary():
    feats = [replace(f, n_valid=5) for f in unburnt()]
    for i in range(4):
        feats[i] = day(i, nir=unburnt()[i].nir)
    assert decide(feats, TH).outcome == APPROVED          # exactly 4 clear
    feats[3] = replace(feats[3], n_valid=5)
    assert decide(feats, TH).rule == "too_few_clear_images"  # 3 clear


def test_persistence_uses_the_fitted_dark_threshold():
    import numpy as np
    th = replace(TH, dark_nbr=-0.25)
    feats = unburnt()
    feats[4] = replace(day(4, nir=0.12, dark=0.9), nbr_px=np.full(20, -0.30, dtype="float32"))
    # next image: dark at -0.10 (dark_share says 0.9) but not at the fitted -0.25
    feats[5] = replace(day(5, nir=0.13, dark=0.9), nbr_px=np.full(20, -0.20, dtype="float32"))
    assert decide(feats, th).rule == "dark_on_one_image"
