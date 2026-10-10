# Evaluation

## Question

Does a satellite check of each field decide no-burn claims better than the thermal fire alerts the state uses
today, and is "clean last season" a safe basis for paying an advance?

## Data

- **Imagery:** Sentinel-2 L2A, collection `sentinel-2-c1-l2a` on Earth Search (AWS Open Data), 2025 season
  (1 Oct – 30 Nov, with a week of margin) and 2024 for the advance. Two study areas on the Punjab–Haryana border:
  Patran tehsil in Patiala (cached as `west_kaithal_2025.npz`) and an area in Kaithal (`kaithal_west_2025.npz`).
  Scale and offset applied (reflectance = DN × 0.0001 − 0.1); no-data and cloud masked (SCL 0, 1, 8, 9, 10);
  SCL 2 and 3 kept on purpose because Sen2Cor can put burn scars there.
- **Fire alerts:** NASA FIRMS, VIIRS S-NPP, NOAA-20 and NOAA-21, 2025 season (`data/firms/`).
- **Plots:** small square plots on early-season cropland, sampled in strata (below). 749 labelled: 556 in Patran,
  193 in Kaithal.

## Labels

Each plot was labelled burnt, not burnt or unsure from a strip of the season's pictures (colour and infrared).
Unsure plots are left out of accuracy.

1. **First pass, by hand** (`labels.csv`), from strips of up to 12 dates.
2. **Second read, by AI.** The 12-date strips could skip the one date a field was burnt before it was ploughed.
   Claude Code re-read the 249 plots whose hidden dates looked burn-like, on strips showing every clear date
   (`labels_claude.csv`). 42 Patran plots first labelled not burnt or unsure were clear burns on a hidden date;
   none changed in Kaithal.
3. **Headline labels** (`labels_full_strips.csv`): the first pass with the second read on top.

The second read was limited to plots the burn signal pointed at, so the headline set leans toward agreeing with
the rules. The first pass alone is reported next to it below.

## Sampling and weighting

Plots were sampled in strata and weighted back to the whole area by stratum size: distance to the nearest fire
alert (< 400 m, 400–750 m, 750 m – 2 km, > 2 km), crossed with whether the cell shows a burn-like signal on some
date. Later rounds added plots only from signal strata, where burns concentrate. Each area carries its own
weights, so the pooled rates estimate the union of the two areas.

## Method

Per date, for every whole pixel inside the plot: NBR, MIRBI, visible brightness, NIR. A possible burn
(`rules.py`, thresholds in `rules.toml`) is a sharp NIR drop with at least 30% of the field near-black
(NBR < −0.15 and brightness ≤ 0.07). A dark share of 15% or more, a fire alert within 375 m, too few clear
images or a small field send the claim to the officer. Otherwise it is approved.

The thresholds in `rules.toml` were chosen by grid search on the first 314 labelled plots (20 burnt), with an
objective that weights missed burns, wrongful flags and review load, and have not been refitted since. The other
435 plots were labelled afterwards, so for them the rules were fixed in advance. As a further check, thresholds
were refitted on one half of all 749 plots and scored on the other half, both ways.

Baseline: a field counts as burnt if any fire alert is within 375 m between 1 Oct and 30 Nov.

## Results (weighted)

Headline labels, 593 fields used, 111 burnt (`data/eval/results_full_strips.json`; recomputed by
`scripts/check_numbers.py`):

| | Saakshi | Held-out half 1 | Held-out half 2 | Fire alerts only |
|---|---|---|---|---|
| Clean fields wrongly flagged | **0.6%** | 1.7% | 2.9% | 9.0% |
| Burnt fields approved without an officer | **0%** | 0% | 3.6% | n/a |
| Flags that were real burns (precision) | 75% | 53% | 54% | 6% |
| Burns flagged as possible burn (recall) | 58% | 91% | 88% | 19% |
| Approved automatically | 80% | 83% | 85% | n/a |
| Sent to the officer | 18% | 14% | 9% | n/a |

Burns not flagged as a possible burn are not approved: they go to the officer as unclear. That is why "burnt
fields approved without an officer" can be 0% while recall is 58%.

By area (headline labels, current thresholds):

| | Patran | Kaithal |
|---|---|---|
| Fields used, burnt | 432, 105 | 161, 6 |
| Clean fields wrongly flagged | 0.5% (fire alerts 14.6%) | 0.6% (fire alerts 3.2%) |
| Flag precision | 86% | 14% |
| Burns flagged (recall) | 61% (fire alerts 16%) | 21% (fire alerts 58%) |
| Burnt fields approved without an officer | 0% | 0% |

Kaithal burnt very little in this sample, so its burn-side numbers rest on six plots. There, fire alerts caught
more of the burns than the rules' possible-burn flag did; the burns the rules did not flag still went to the
officer rather than being approved.

Human first pass alone (615 fields, 69 burnt): Saakshi wrongly flagged 1.6% of clean fields against 8.7% for fire
alerts, flag precision 38%, and no burnt field was approved without an officer.

**Advance rule** (`scripts/advance_eval.py`, 262 earlier Patran plots): the 2024 verdict from the rules against
the 2025 label.

| 2024 verdict | Share of cropland | Burnt in 2025 |
|---|---|---|
| clean (advance eligible) | 78.2% | 1.8% |
| not clean (unclear or burnt) | 21.8% | 8.6% |

## What we learned

- **A burn scar can last one clear picture.** Fields are often ploughed within days. Thermal snapshots and a
  12-date picture strip both miss these; the rules look at every clear date, and so must the labeller.
- **Bare soil looks burnt to NBR.** Dry harvested soil reaches NBR −0.2, so a pixel counts as dark only if it is
  also near-black in visible light. That one change cut the review share from 60% to 20%.
- **Wet soil is the other look-alike.** Irrigated fields before sowing go dark, but blue in the infrared view,
  not maroon.
- **Small fields are hard.** At 20 m, a one-acre field has about 10 whole pixels; under 8 it goes to review.

## Limits

- No site visits: labels are readings of the same Sentinel-2 pictures the rules use, so they measure agreement
  with a careful human eye, not ground truth.
- The thresholds were fitted on the first 314 of these plots. The held-out halves (1.7% and 2.9% wrongful flags,
  thresholds refitted on the other half) are the more cautious estimate for new fields.
- The AI second read covered only plots the burn signal pointed at (see Labels).
- 111 burnt plots overall, six in Kaithal; burn-side rates move by single plots. No confidence intervals yet.
- FIRMS 2024 alerts were not used for the 2024 verdicts.
