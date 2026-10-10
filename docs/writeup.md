# Saakshi: pay before harvest, check every field after

## The problem

Every November, burnt paddy straw from Punjab and Haryana adds to the smoke over Delhi; on 22 Nov 2024 farm fires were
about 26% of its PM2.5 by IITM's estimate. The state's tools are weak. Fire alerts from NASA's VIIRS satellites
decide who gets a red entry, an FIR and a fine, but in our labelled sample they flagged 9.0% of clean fields and
caught only 19% of burns: a field can burn and be ploughed between two passes, and a neighbour's fire lands on
your record. The incentive for not burning, ₹1,000 an acre in Haryana in 2024, is paid only after a village committee checks
photos. A randomised trial in 171 Punjab villages found that paying only after verification did not reduce
burning, while paying 25% or 50% upfront roughly doubled compliance, about 10 percentage points. Paying upfront
needs a check that can be run on every field, quickly and defensibly.

## What we built

Saakshi does that check from Sentinel-2 pictures and runs the whole claim around it.

- **Before harvest**, a field that was clean last season gets half the incentive as an advance.
- **After harvest**, every clear picture of the field is read. Fixed rules approve clean fields and release the
  balance; anything unclear and every possible burn goes to the village officer.
- **The officer** sees colour and infrared pictures, the plant signal through the season, nearby fire alerts and
  last season's result, and decides. A confirmed burn on an advanced field gets a drafted recovery notice and a
  payment link to return the advance.
- **The farmer** is told in Punjabi, Hindi, Haryanvi or English, as text and a voice note, in the app and on
  WhatsApp, and can ask why, check their money, or appeal by voice. An appeal cancels the payment link and goes
  back to the officer.
- **The public map** plays the 2025 season for the Patiala–Kaithal border belt: burn-like ground appearing day
  by day, fire alerts, and an estimate of the smoke.

## Results

749 plots in Patran and Kaithal were labelled from the season's pictures: a human first pass, and an AI re-read
of 249 plots on strips showing every clear date, which found 42 burns the earlier strips had hidden. On 593
fields (111 burnt):

- Saakshi wrongly flagged **0.6%** of clean fields; fire alerts alone flagged **9.0%**.
- **None** of the 111 burnt fields was approved without an officer.
- 75% of Saakshi's flags were real burns, against 6% for fire alerts.

On the human first pass alone, the gap holds: 1.6% against 8.7%, flag precision 38%, and still no burnt field
approved without an officer.

Fields clean in 2024 burnt in 2025 at 1.8%, against 8.6% for the rest, so "clean last season" is a sound basis
for the advance; 78% of cropland would qualify.

## Impact

- **Smoke.** In one belt, 3,059 ha looked burnt in the 2025 season, roughly 140 t of PM2.5 by published
  emission factors. Each acre kept clean is about 19 kg of PM2.5 kept out of the air. Saakshi shows this number
  on the map, for each case and to each farmer, as an estimate.
- **Cost.** A check reads only the pixels around one field, about ten seconds of a Lambda function: a fraction of
  a rupee per field per season, so it can run on every registered field, not a sample.
- **Fairness.** The farmer sees the same pictures the officer sees, in their own language, and can contest them.
  A fire next door no longer decides their record, and every burn is confirmed by a person.
- **Why PM2.5, not CO2.** The harm is the winter smog, and PM2.5 is what reaches lungs. The CO2 from straw is
  regrown by the next crop within a year; counting it would overstate the climate effect and miss the health one.

## How it is built

AWS: Sentinel-2 read in place from the AWS Open Data registry, Lambda for the check, the API, the assistant and
the WhatsApp webhook, DynamoDB, S3 and CloudFront, EventBridge for the daily sweep, Bedrock (Amazon Nova 2 Lite
through the Strands Agents SDK) for understanding the farmer's request, Polly and Transcribe for Hindi and English
voice. Sarvam AI gives Punjabi voice and speech to text. The WhatsApp Cloud API carries the chat; Razorpay (test
mode) the repayment link. Everything is one SAM stack.

The model never decides. It picks one of seven tools; none can approve, reject, pay or penalise. What the farmer
hears about a decision or money is composed from the record in fixed templates, not written by the model.

## Limits and next steps

Labels are one person's reading of the pictures, not site visits, and field outlines are samples, since there is
no public cadastral map. Next: run with a district's real field registry, connect the advance and balance to a real direct-benefit-transfer rail, and give officers a
batch view for the season's payouts.

## AI usage

- **Claude Code (Anthropic)** wrote most of the code, the interface text and the analysis scripts, under the
  team's direction and review. It also re-read 249 plots on full-season strips; the headline uses those re-reads,
  and the numbers on the human labels alone are reported next to them.
- **In the product**, Amazon Nova 2 Lite on Bedrock interprets the farmer's request and chooses a tool; Sarvam AI
  and Amazon Polly speak the replies; Sarvam and Amazon Transcribe turn voice into text.
- **Human work:** the problem and the scheme design, the product and policy decisions, the first pass of 749
  labels, the AWS, WhatsApp and Razorpay setup, and testing on real phones.
