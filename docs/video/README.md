# Recording the demo video

Everything on the web side plays by itself, with its narration and captions. You record the screen, film one
WhatsApp clip and one short AWS console clip, and join them in Clipchamp (free with Windows). The rules: under
3:00, on YouTube (public or unlisted), and the video must show AWS in use.

## 1. Web part (autopilot), about 2:45

1. Open https://d5gpae5oilzws.cloudfront.net/video/director.html in Chrome on the laptop. Close other tabs, turn
   on Do Not Disturb, plug in the charger.
2. Press **Prepare** and wait for "Ready" (about a minute: it resets the demo and loads the season once).
3. Start recording the screen **with system sound**: Win + Alt + R (Xbox Game Bar), or OBS with Desktop Audio.
4. Press **Start**. The page goes full screen; move the mouse to the screen edge. It ends on the closing card.
   Stop recording when the card has shown for a couple of seconds.
5. A **Download captions (.srt)** button appears a few seconds after the end. Save it: upload it to YouTube as
   subtitles (it is timed from the moment you pressed Start, so trim the recording to start there).
6. One part went wrong? Re-run from that scene with `?from=s4` (or `s2`, `s5`, `s6`, `s7`). Press Prepare first
   whenever the officer scenes are included.

| Scene | What plays | Starts about |
|---|---|---|
| s1 | Opening: India, Delhi, the belt | 0:02 |
| s2 | The 2025 season plays | 0:17 |
| s3 | Live satellite check on a field, with the AWS Open Data and Lambda line | 0:42 |
| s4 | Officer confirms a burn; the recovery notice | 0:59 |
| s5 | Officer approves another case; the payment advice (Cashfree) | 1:20 |
| s6 | Farmer page in Punjabi, the farmer's voice note | 1:37 |
| wa | **"On WhatsApp" card: your phone clip goes here** (16 s of narration) | 1:54 |
| s7 | How it works on AWS (your console clip goes over its second half) | 2:11 |
| s8 | Closing card | 2:28 |

## 2. WhatsApp clip (phone)

Record **after** one autopilot take, so Mahender has been approved and paid, which matches the story.

Before: Do Not Disturb on, brightness up. Open the chat with the Saakshi test number; for a clean look clear it
first (chat name, Clear chat). Put `whatsapp-voice-note-punjabi.mp3` (in the `video-samples` folder) ready to play
on the laptop. Control Centre, **long-press** screen record, **Microphone on**, Start.

1. Type **change**, send. The intro arrives with **Punjab · ਪੰਜਾਬ** and **Haryana · हरियाणा** buttons.
2. Tap **Punjab · ਪੰਜਾਬ**, then the list button, then **Mahender Saini**.
3. The reply arrives: two lines in English and Punjabi, a voice note and the satellite pictures. Play the voice
   note for about 3 seconds.
4. Tap **Why?**, then **My money**.
5. Hold the WhatsApp mic, play the Punjabi clip on the laptop next to the phone, release when it ends. The reply
   shows what was heard and answers in Punjabi with a voice note.
6. Stop recording.

It will run 40-60 seconds. Send me rough timestamps (Punjab tapped, farmer picked, reply arrives, voice note,
Why?, My money, voice question, its answer) and I will pick a 20-30 second cut and re-time the WhatsApp narration
to it. The web part leaves room for up to about 30 seconds.

## 3. AWS console clip (laptop), about 10 seconds

Record the screen (no sound needed) while you open, a few seconds each, in the us-west-2 region:

1. **CloudFormation** → stack `envhacks-parali` → **Resources** tab (the Lambda functions, DynamoDB table, S3
   bucket, CloudFront distribution, schedules).
2. **Lambda** → `envhacks-parali-ProcessFunction-…` → **Monitor** → **View CloudWatch logs** → the latest log
   stream (a check reading Sentinel-2, a Cashfree payout).
3. **DynamoDB** → **Explore items** → the stack's table → any item.

It goes over the second half of the "How it works" scene (2:19 onward), where the narration names Lambda,
DynamoDB and CloudFront.

## 4. Join them (Clipchamp)

1. Import the screen recording, the phone clip and the console clip. Put the screen recording on the timeline and
   trim its start to the moment you pressed Start.
2. At the "On WhatsApp" card, put the phone clip on the track above, starting where the card starts. Mute it,
   except 2-3 seconds of the bot's voice note if you like (lower the narration there).
3. Over the second half of "How it works", put the console clip on the track above, muted.
4. Check the total is under 3:00, export 1080p, upload to YouTube as unlisted, add the .srt as subtitles, and open
   the link in a private window before submitting.
