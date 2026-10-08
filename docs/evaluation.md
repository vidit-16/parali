# Evaluation

## Question

Does a satellite check of each field decide no-burn claims better than the thermal fire alerts the state
uses today, and is "clean last season" a safe basis for paying an advance?

## Data

- **Imagery:** Sentinel-2 L2A, collection `sentinel-2-c1-l2a` on Earth Search (AWS Open Data). Study area west
  Kaithal, 76.08–76.20 E, 29.88–29.99 N, tile 43RFP. 31 cloud-free dates for 25 Sep – 4 Dec 2025, 27 for 2024.
  Scale and offset applied (reflectance = DN × 0.0001 − 0.1); no-data and cloud masked (SCL 0, 1, 8, 9, 10);
  SCL 2 and 3 kept on purpose because Sen2Cor can put burn scars there.
- **Fire points:** NASA FIRMS, VIIRS S-NPP and NOAA-20 standard processing plus NOAA-21 NRT, 25 Sep – 5 Dec
  2025 (`data/firms/kaithal_2025.csv`).
- **Labels:** 314 plots of 80 m (4 × 4 pixels) on early-season cropland, labelled burnt / not burnt / unsure by
  one person from the image strip of the whole season (`data/eval/labels.csv`, images re-creatable with
  `scripts/make_label_images.py`). 20 burnt, 242 not burnt, 52 unsure (left out). An AI-assisted second read
  flagged disagreements for re-checking; the labels are the labeller's.

## Sampling and weighting

Plots were sampled in strata, then weighted back to the whole area by stratum size:

- distance to the nearest FIRMS point: < 400 m, 400–750 m, 750 m – 2 km, > 2 km;
- crossed with whether the cell shows a burn-like signal on some date (rounds 2 and 3 added plots only from
  signal strata, where burns concentrate).

Earlier plots stay valid after re-stratifying: a simple random sample within a stratum is still one within
each of its sub-strata.

## Method

Per date, for every whole pixel inside the plot: NBR, MIRBI, visible brightness, NIR. The rules
(`rules.py`): a possible burn is a sharp NIR drop with at least 30% of the field near-black (NBR < −0.15 and
brightness ≤ 0.07); a dark share of 15% or more, a fire point within 375 m, too few clear images or a small
field send the claim to the officer; otherwise approved.

Thresholds were chosen by grid search on the labels with an objective that weights missed burns, wrongful
flags and review load, then checked by fitting on one half and scoring on the other, both ways
(`parali evaluate`).

Baseline: a field counts as burnt if any FIRMS point is within 375 m during 1 Oct – 30 Nov.

## Results (weighted)

| | Rules (thresholds in `rules.toml`) | Held-out half 1 | Held-out half 2 | FIRMS only |
|---|---|---|---|---|
| Clean fields flagged as possible burn | 2.6% | 4.8% | 4.9% | 14.1% |
| Burnt fields auto-approved | 0% | 0% | 6.4% (one plot) | – |
| Auto-approved | 75.8% | 84.0% | 81.7% | – |
| Sent to officer | 20.5% | 10.0% | 10.3% | – |
| Burns caught (recall) | every burn sent to officer | | | 14.1% |

Advance eligibility (`scripts/advance_eval.py`): 2024 verdict from the rules, 2025 from the labels.

| 2024 verdict | Share of cropland | Burnt in 2025 |
|---|---|---|
| clean (advance eligible) | 78.2% | 1.8% |
| not clean (unclear or burnt) | 21.8% | 8.6% |

## What we learned

- **A burn scar lasts one clear image.** Every labelled burn showed on a single date; fields are ploughed
  within days. Thermal snapshots and slow manual checks both miss most burns. The rule needs only one image.
- **Bare soil looks burnt to NBR.** Dry harvested soil reaches NBR −0.2, so a pixel counts as dark only if it is
  also near-black in visible light. That one change cut the review share from 60% to 20%.
- **Wet soil is the other look-alike.** Irrigated fields before sowing go dark, but blue in a SWIR/NIR/red view
  rather than red.
- **Small fields are hard.** At 20 m, a one-acre field has about 10 whole pixels; under 8 it goes to review.

## Limits

One labeller, from 20 m images, no site visits. 20 burnt plots is small; burn-side numbers move by single
plots. FIRMS 2024 points were not used for the 2024 verdicts. The study area is one 12 × 12 km box.
