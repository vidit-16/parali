# Saakshi: pay before harvest, check every field after

## The problem

Every November, burnt paddy straw from Punjab and Haryana adds to the smoke over Delhi; on the worst days farm
fires are about a quarter of its PM2.5. The state's tools are weak. Fire alerts from NASA's VIIRS satellites
decide who gets a red entry, an FIR and a fine, but in our labelled sample they flagged TBD of clean fields and
caught only TBD of burns: a field can burn and be ploughed between two passes, and a neighbour's fire lands on
your record. The incentive for not burning, ₹1,000 an acre in Haryana, is paid only after a slow field visit.
A randomised trial in Punjab found that paying part of it upfront raises compliance by 8 to 11 percentage
points, but paying upfront needs a check that can be run on every field, quickly and defensibly.

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

749 plots in Patran and Kaithal were labelled by hand from the full season of pictures. On the labeller's own
labels (TBD fields, TBD burnt):

- Saakshi wrongly flagged **TBD** of clean fields; fire alerts alone flagged **TBD**.
- **TBD** of burnt fields were approved without an officer.
- TBD of Saakshi's possible-burn flags were real burns.

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
no public cadastral map. Next: run with a district's real field registry, have native speakers check the
Punjabi and Haryanvi, connect the advance and balance to a real direct-benefit-transfer rail, and give officers a
batch view for the season's payouts.

## AI usage

- **Claude Code (Anthropic)** was the pair programmer: it wrote most of the code, the interface text and the
  analysis scripts, under our direction and review. It also re-read 249 plots' picture strips; those calls are
  kept in a separate file and are not used in the results. The results use only the human labeller's labels,
  including a blind review of the same 249 plots.
- **In the product**, Amazon Nova 2 Lite on Bedrock interprets the farmer's request and chooses a tool; Sarvam AI
  and Amazon Polly speak the replies; Sarvam and Amazon Transcribe turn voice into text.
- **Human work:** the labels, the product and policy decisions, the WhatsApp, Razorpay and AWS setup, and testing
  on real phones.
