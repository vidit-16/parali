"""Generate the demo video's narration (Amazon Polly or Sarvam) from docs/video/script.md.

One mp3 per scene in web/video/ (s1.mp3 ... s8.mp3, wa.mp3) plus scenes.json with each scene's text, which the
autopilot shows as captions. Re-run after editing the script.

usage: uv run --extra aws python scripts/make_voiceover.py [--voice polly:Kajal | polly:Matthew | polly:Arthur | sarvam:shubh ...]
       [--profile envhacks] [--rate 100%] [--only s1,s5]
"""
import argparse
import html
import json
import re
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "video"


def scenes() -> list[tuple[str, str]]:
    rows = []
    for line in (ROOT / "docs/video/script.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(s\d|wa)\s*\|[^|]*\|\s*([^|]+?)\s*\|", line)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="envhacks")
    ap.add_argument("--rate", default="100%")
    ap.add_argument("--voice", default="polly:Kajal")
    ap.add_argument("--only", default="", help="comma-separated scenes to regenerate, e.g. s1,s5; the rest keep their audio")
    a = ap.parse_args()
    engine, voice = a.voice.split(":", 1)
    polly = boto3.Session(profile_name=a.profile, region_name="us-west-2").client("polly")
    langs = {"Kajal": "en-IN", "Matthew": "en-US", "Arthur": "en-GB", "Brian": "en-GB", "Stephen": "en-US"}

    def speak(text: str) -> bytes:
        if engine == "sarvam":
            import base64
            from parali import sarvam
            out = sarvam._post("/text-to-speech", {"text": text, "target_language_code": "en-IN", "model": "bulbul:v3",
                                                   "speaker": voice, "output_audio_codec": "mp3"}, sarvam.api_key())
            return base64.b64decode(out["audios"][0])
        ssml = f'<speak><prosody rate="{a.rate}">{html.escape(text)}</prosody></speak>'
        return polly.synthesize_speech(Text=ssml, TextType="ssml", OutputFormat="mp3", VoiceId=voice, Engine="neural",
                                       LanguageCode=langs.get(voice, "en-IN"))["AudioStream"].read()
    OUT.mkdir(parents=True, exist_ok=True)
    meta, only = [], set(filter(None, a.only.split(",")))
    for sid, text in scenes():
        if not only or sid in only:
            audio = speak(text)
            (OUT / f"{sid}.mp3").write_bytes(audio)
            print(sid, f"{len(audio) // 1024} KB")
        # the captions show what the voice is given spelled out ("P M two point five") as it is written
        meta.append({"id": sid, "text": text.replace("P M two point five", "PM2.5").replace("Patiala Kaithal", "Patiala–Kaithal")
                     .replace("Sentinel two", "Sentinel-2")})
    (OUT / "scenes.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
