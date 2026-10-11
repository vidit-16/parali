# Recording the demo video

The whole video plays by itself in the browser: the site, the narration (Sarvam "shubh"), captions, the WhatsApp
clip and the AWS console screenshots. You record the screen once. The rules: under 3:00, on YouTube (public or
unlisted), and the video must show AWS in use.

## Before recording (once)

- `web/video/console1.png`, `console2.png`, `console3.png`: the AWS console screenshots (CloudFormation resources,
  Lambda logs, DynamoDB items), account ID blurred. They show in the "How it works" scene. Missing files are
  skipped.
- `web/video/wa.mp4`: the WhatsApp screen recording, cut to the length of its narration and shown in a phone frame.
  Without it the scene shows an "On WhatsApp" card.
- Deploy, so both are live.

### The WhatsApp recording (phone)

Record after one autopilot take, so Satbir has been approved and paid, which matches the story. Do Not Disturb
on, brightness up, the chat with the Saakshi test number cleared. Have `whatsapp-voice-note-punjabi.mp3` ready to
play on the laptop. Start the phone's screen recording with the microphone on.

1. Type **change**, send. Tap **Punjab · ਪੰਜਾਬ**, then the list button, then **Satbir Singh**.
2. The reply arrives in English and Punjabi, with a voice note and the satellite pictures. Play the voice note for
   about 3 seconds.
3. Tap **Why?**, then **My money**.
4. Hold the WhatsApp mic, play the Punjabi clip on the laptop next to the phone, release when it ends. The reply
   shows what was heard and answers in Punjabi.
5. Stop recording. It is cut to 20-30 seconds with ffmpeg and the WhatsApp narration is re-timed to it.

## Record

1. Open https://d5gpae5oilzws.cloudfront.net/video/director.html in Chrome on the laptop. Close other tabs, turn
   on Do Not Disturb, plug in the charger.
2. Press **Prepare** and wait for "Ready" (one to two minutes: it resets the demo and loads the season once).
3. Start recording the screen **with system sound**: Win + Alt + R (Xbox Game Bar), or OBS with Desktop Audio.
4. Press **Start**. The page goes full screen; move the mouse to the screen edge. It ends on the closing card.
   Stop recording when the card has shown for a couple of seconds.
5. A **Download captions (.srt)** button appears a few seconds after the end. Upload it to YouTube as subtitles
   (it is timed from the moment you pressed Start, so trim the recording to start there).
6. One part went wrong? Re-run from that scene with `?from=s4` (or `s2`, `s5`, `s6`, `wa`, `s7`) and `&to=` to
   stop early. Press Prepare first whenever an officer scene (s4, s5) is included: a decision can be taken once.

Options on the start panel:

- **Captions** puts the narration in a strip under the page, so it never covers the app.
- **Narration** unticked plays the same take silently, with the same timing, for a voice you record yourself.
  Read each scene's line from `docs/video/script.md` as its caption appears (or record afterwards over the video).

| Scene | What plays |
|---|---|
| s1 | Opening: Satbir's story, India, Delhi, the belt |
| s2 | The 2025 season plays |
| s3 | Live satellite check on a field; zoom on the result and its AWS line |
| s4 | Officer confirms a burn; zoom on the checklist; the recovery notice |
| s5 | Officer approves Satbir; the payment advice (Cashfree, test mode) |
| s6 | Satbir's page in Punjabi, his voice note, the passbook |
| wa | WhatsApp, in a phone frame |
| s7 | How it works on AWS, the console screenshots, zoom on Bedrock |
| s8 | Closing card |

## Background music (optional)

In Clipchamp: import the recording, add a quiet track from its free music library under it, set the music to about
10% volume, export 1080p. Keep it calm and low; the narration carries the video.

## Upload

Check the length is under 3:00, upload to YouTube as unlisted, add the .srt as subtitles, and open the link in a
private window before submitting.
