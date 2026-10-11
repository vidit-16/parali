"""Cut the WhatsApp screen recording for the demo video and build its sound.

The phone clip (web/video/wa.mp4) is cut to the moments that matter, with no sound of its own. Its sound track
(web/video/wa.mp3, which the autopilot plays as the scene's narration) lays short narration lines into the gaps
between the three voices worth hearing: the bot's voice note, the farmer's spoken question, and the bot's spoken
answer. Room noise is filtered out and the farmer's question is brought up to the same level.

usage: uv run --extra aws --extra dev python scripts/make_wa_cut.py path/to/recording.mp4
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "video"
FF = imageio_ffmpeg.get_ffmpeg_exe()

# (start, end) in the recording, in seconds
CUTS = [
    (9.0, 12.4),   # the intro with the state buttons; Punjab is tapped
    (15.2, 18.0),  # the farmer list; Satbir is picked
    (22.4, 25.6),  # his status lands in English and Punjabi; Why? is tapped
    (32.0, 38.4),  # the reason, the pictures and the voice note, which plays
    (44.6, 50.2),  # the farmer asks by voice, in Punjabi
    (69.8, 74.2),  # what was heard, the status, and the spoken answer, which plays
]
# sounds kept from the recording: (start, end) in the recording, and gain in dB
KEEP = [(35.1, 37.5, -2), (45.7, 47.6, 12), (70.5, 74.2, -2)]
# narration: (time in the cut, line)
LINES = [
    (0.1, "Most farmers live on WhatsApp, so Saakshi does too. Satbir picks his state, and his name."),
    (6.3, "His status comes in English and Punjabi. He taps Why, for the satellite pictures, and a voice note."),
    (14.95, "Or asks, by voice."),
    (18.75, "Saakshi hears his Punjabi, and answers in Punjabi."),
]


def run(*args):
    subprocess.run([FF, "-hide_banner", "-v", "error", "-y", *args], check=True)


def to_cut(t: float) -> float:
    """Where a moment of the recording lands in the cut."""
    at = 0.0
    for a, b in CUTS:
        if a <= t <= b:
            return at + t - a
        at += b - a
    raise ValueError(t)


def speak(text: str, path: Path) -> float:
    from parali import sarvam
    out = sarvam._post("/text-to-speech", {"text": text, "target_language_code": "en-IN", "model": "bulbul:v3",
                                           "speaker": "shubh", "output_audio_codec": "mp3"}, sarvam.api_key())
    path.write_bytes(base64.b64decode(out["audios"][0]))
    probe = subprocess.run([FF, "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = probe.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def main(src: str):
    work = ROOT / "data" / "cache" / "wa_cut"
    work.mkdir(parents=True, exist_ok=True)
    total = sum(b - a for a, b in CUTS)

    # the picture: each cut, scaled for the phone frame, joined with hard cuts, no sound
    parts = "".join(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30,scale=592:-2[v{i}];" for i, (a, b) in enumerate(CUTS))
    joined = "".join(f"[v{i}]" for i in range(len(CUTS)))
    run("-i", src, "-filter_complex", f"{parts}{joined}concat=n={len(CUTS)}:v=1:a=0[v]", "-map", "[v]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow", "-movflags", "+faststart",
        "-an", str(OUT / "wa.mp4"))

    # the sound: narration lines and the kept voices, each placed at its time in the cut
    inputs, chains, n = ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=44100:cl=mono"], [], 1
    spoken = []
    for i, (at, text) in enumerate(LINES):
        p = work / f"line{i}.mp3"
        d = speak(text, p)
        spoken.append((at, at + d, text))
        inputs += ["-i", str(p)]
        chains.append(f"[{n}:a]aresample=44100,aformat=channel_layouts=mono,adelay={int(at * 1000)}[s{n}]")
        n += 1
    for a, b, gain in KEEP:
        inputs += ["-i", src]
        at = to_cut(a)
        chains.append(f"[{n}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=mono,"
                      f"highpass=f=90,afftdn=nf=-40,volume={gain}dB,afade=t=in:d=0.08,afade=t=out:st={b - a - 0.15}:d=0.15,"
                      f"adelay={int(at * 1000)}[s{n}]")
        n += 1
    mix = "".join(f"[s{i}]" for i in range(1, n))
    run(*inputs, "-filter_complex", ";".join(chains) + f";[0:a]{mix}amix=inputs={n}:normalize=0:duration=first,"
        "alimiter=limit=0.95[a]", "-map", "[a]", "-c:a", "libmp3lame", "-q:a", "3", str(OUT / "wa.mp3"))

    kept = [(to_cut(a), to_cut(a) + b - a) for a, b, _ in KEEP]
    for s, e, text in spoken:
        clash = [k for k in kept if s < k[1] - 0.3 and e > k[0] + 0.3]
        print(f"{s:5.1f}-{e:5.1f}  {text}" + (f"   overlaps a voice at {clash}" if clash else ""))
    print("voices at", [(round(a, 1), round(b, 1)) for a, b in kept], f"cut is {total:.1f} s")

    meta = json.loads((OUT / "scenes.json").read_text(encoding="utf-8"))
    for m in meta:
        if m["id"] == "wa":
            m["text"] = " ".join(t for _, t in LINES)
    (OUT / "scenes.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
