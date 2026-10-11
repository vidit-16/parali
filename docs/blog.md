# Checking stubble-burning claims field by field with Sentinel-2 on AWS

Every November, farmers in Punjab and Haryana clear paddy straw by burning it, and the smoke drifts over Delhi.
States pay an incentive for not burning: Haryana paid ₹1,000 an acre in 2024. The incentive works badly in
practice. It is paid months after the season, once a committee has checked photos, and the main enforcement
signal is NASA's VIIRS fire alerts, which decide who gets a red entry, a fine or an FIR.

For Environmental Hacks 2026 I built Saakshi, a system that checks each farmer's claim from satellite pictures,
pays clean fields quickly and sends every possible burn to a village officer. This post covers why fire alerts
are the wrong tool, how the field check works on AWS, and what I would change.

## Why fire alerts are not enough

A fire alert is a hot pixel about 375 m across, seen at the moment a satellite passes. Two things go wrong at
field scale:

- A field can be burnt and ploughed between two passes, so the burn is never seen.
- A fire on the next field lands on your record, because the pixel is larger than your field.

On fields we labelled by hand from the season's pictures, fire alerts flagged 9.0% of clean fields and caught
only a minority of real burns. Meanwhile, a randomised trial in Punjab found that paying part of the incentive
upfront roughly doubled compliance compared with paying only after verification. Paying upfront is only
defensible if every field can be checked afterwards, cheaply and in a way the farmer can see.

## What a burn looks like from orbit

Sentinel-2 photographs the same field every few days at 10–20 m resolution, which is fine enough to see one
field. A fresh burn leaves a clear trace across a few bands:

- The near-infrared reflectance, which is high over standing crop and stubble, drops sharply.
- The field turns dark in the burn ratio (NBR, which compares near-infrared with shortwave infrared) and in
  brightness.
- The dark patch stays for the following clear pictures instead of vanishing like a cloud shadow or wet soil.

Saakshi's rules look for exactly that combination: a sharp near-infrared drop, a large share of the field dark,
and the darkness persisting. Clean fields are approved. Anything ambiguous, such as a field that looked dark
without the sharp drop a fresh burn causes, goes to an officer rather than being decided by the rules.

## The field check on AWS

The imagery is the Sentinel-2 Level-2A collection in the AWS Open Data registry, stored as Cloud-Optimised
GeoTIFFs. That format is the reason the whole thing is cheap:

1. A Lambda function asks the Earth Search STAC API for every scene covering the field in the season.
2. For each scene it opens the bands with rasterio and reads only the window around the field. COGs are tiled
   internally, so this is a handful of HTTP range requests instead of downloading a 100 MB tile.
3. The scene classification layer masks clouds and shadows, and the remaining pixels inside the field outline
   become per-date features: reflectance, NBR, dark share.
4. The rules run over the time series and produce a decision with the dates of the evidence.

The stack runs in us-west-2, the same region as the imagery, so reads are fast and free of transfer charges. A
check takes about ten seconds of Lambda time, a fraction of a rupee per field per season. That is what makes it
realistic to check every registered field rather than a sample.

Around the check:

- **DynamoDB** holds fields and claims, plus an append-only event log per claim (decision, notice, payment
  link, payout, farmer notified). The partition key is the claim and the sort key is the event time, so the
  officer's audit trail is a single query.
- **S3 and CloudFront** serve the web app and the generated documents: evidence images, recovery notices and
  payment receipts.
- **EventBridge** runs a daily sweep that follows up payouts still pending at the bank.
- **Amazon Bedrock** with Nova 2 Lite, through the Strands Agents SDK, interprets what a farmer asks in the app
  or on WhatsApp and chooses one of seven tools: status, explanation, money, appeal and so on. None of the tools
  can approve, reject, pay or penalise, and anything the farmer is told about a decision or money comes from
  fixed templates filled from the record. The model routes questions; it never decides.
- **Polly and Transcribe** handle Hindi and English voice; Punjabi voice comes from Sarvam AI.
- Everything is one **AWS SAM** template.

## People decide, the satellite gives evidence

The design rule I held to was that no model or rule can confirm a burn. A possible burn goes to the village
officer, who sees the colour and infrared pictures for each date, the vegetation signal across the season,
nearby fire alerts and last season's result. Only the officer can confirm. A confirmed burn on a field that got
an advance produces a drafted recovery notice and a payment link to return it.

The farmer sees the same pictures the officer saw, in Punjabi, Hindi, Haryanvi or English, with a voice note,
and can appeal by voice. An appeal cancels the payment link and returns the case to the officer.

## Results

On 593 labelled fields in Patran (Punjab) and Kaithal (Haryana), 111 of them burnt:

- Saakshi wrongly flagged 0.6% of clean fields; fire alerts flagged 9.0%.
- None of the 111 burnt fields was approved without an officer.
- 75% of Saakshi's flags were real burns, against 6% for fire alerts.

On the first-pass labels alone the gap holds: 1.6% against 8.7%. Fields that were clean in 2024 burnt in 2025
at 1.8%, against 8.6% for the rest, which is why "clean last season" is the basis for the advance.

## What I learned

- **Read less data.** Windowed reads from COGs turned a heavy remote-sensing job into a short Lambda call. Most
  of the performance work was making sure nothing read more pixels than the field needed.
- **Keep models away from decisions.** Letting the model only pick a tool made the assistant easy to reason
  about and easy to test, and a guard throws away any model reply that states a decision on its own.
- **Fire alerts are context, not evidence.** They are useful to show the officer, but a field-scale decision
  needs field-scale pictures.
- **Language is part of the product.** Supporting Punjabi properly needed a third-party voice, since Polly has
  no Punjabi voice. For farmers in Punjab that was not optional.

## Next

Field outlines in the demo are samples, because there is no public cadastral map, and the labels are readings of
the pictures rather than site visits. The next steps are to run with a district's real field registry, move
payouts from test mode to the state's direct-benefit-transfer rail, and give officers a batch view for the
season.

Links: [code](https://github.com/vidit-16/saakshi) · [live demo](https://d5gpae5oilzws.cloudfront.net)
(officer PIN 2468) · [video](https://www.youtube.com/watch?v=_0H2pnWebJQ)

Assisted by Claude Code.
