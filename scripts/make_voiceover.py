"""Generate the demo video's narration with Amazon Polly from docs/video/script.md.

One mp3 per scene in web/video/ (s1.mp3 ... s8.mp3, wa.mp3) plus scenes.json with each scene's text, which the
autopilot shows as captions. Re-run after editing the script.

usage: uv run --extra aws python scripts/make_voiceover.py [--profile envhacks] [--rate 104%]
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
    ap.add_argument("--rate", default="104%")
    a = ap.parse_args()
    polly = boto3.Session(profile_name=a.profile, region_name="us-west-2").client("polly")
    OUT.mkdir(parents=True, exist_ok=True)
    meta = []
    for sid, text in scenes():
        ssml = f'<speak><prosody rate="{a.rate}">{html.escape(text)}</prosody></speak>'
        audio = polly.synthesize_speech(Text=ssml, TextType="ssml", OutputFormat="mp3", VoiceId="Kajal",
                                        Engine="neural", LanguageCode="en-IN")["AudioStream"].read()
        (OUT / f"{sid}.mp3").write_bytes(audio)
        # the caption shows "P M two point five" as written for the voice: show it as PM2.5
        meta.append({"id": sid, "text": text.replace("P M two point five", "PM2.5").replace("Patiala Kaithal", "Patiala–Kaithal")})
        print(sid, f"{len(audio) // 1024} KB")
    (OUT / "scenes.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
