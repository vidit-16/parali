"""Speech for the farmer. Hindi, Haryanvi and Indian English with Amazon Polly (the Kajal voice speaks both
Hindi and English); Punjabi with Sarvam (sarvam.py). The text comes from messages.py and agent.compose; the
voices only read it."""
from parali import sarvam

VOICE = "Kajal"


def polly_mp3(text: str, region: str | None = None, language: str = "hi-IN") -> bytes:
    import html
    import boto3
    polly = boto3.client("polly", region_name=region)
    # Polly speaks about 9 dB quieter than Sarvam; +6 dB is the most SSML allows, and it does not clip
    ssml = f'<speak><prosody volume="+6dB">{html.escape(text, quote=False)}</prosody></speak>'
    r = polly.synthesize_speech(Text=ssml, TextType="ssml", VoiceId=VOICE, Engine="neural", LanguageCode=language,
                                OutputFormat="mp3")
    return louder(r["AudioStream"].read(), 2)  # 3 dB more: level with Sarvam, peaks still below full scale


_KBPS = {1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],
         2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160]}
_RATE = {1: [44100, 48000, 32000], 2: [22050, 24000, 16000], 25: [11025, 12000, 8000]}


def louder(mp3: bytes, steps: int) -> bytes:
    """Raise an MP3's volume by 1.5 dB per step without re-encoding, as mp3gain does: every granule's
    global_gain field goes up. Frames it cannot read (not Layer III, or with a CRC over the field) stay as they are."""
    b = bytearray(mp3)
    i = 0
    if b[:3] == b"ID3":
        i = 10 + ((b[6] & 0x7F) << 21 | (b[7] & 0x7F) << 14 | (b[8] & 0x7F) << 7 | (b[9] & 0x7F))

    def field(bit: int, add: int | None = None) -> int:  # 8 bits from bit offset; optionally add to them
        byte, sh = divmod(bit, 8)
        v = ((b[byte] << 8 | b[byte + 1]) >> (8 - sh)) & 0xFF
        if add is not None:
            nv = min(255, v + add)
            w = (b[byte] << 8 | b[byte + 1]) & ~(0xFF << (8 - sh)) | nv << (8 - sh)
            b[byte], b[byte + 1] = w >> 8 & 0xFF, w & 0xFF
        return v

    while i + 4 <= len(b):
        h = int.from_bytes(b[i:i + 4], "big")
        ver, layer, crc = h >> 19 & 3, h >> 17 & 3, not (h >> 16 & 1)
        br, sr, pad, mono = h >> 12 & 15, h >> 10 & 3, h >> 9 & 1, (h >> 6 & 3) == 3
        if h >> 21 != 0x7FF or ver == 1 or layer != 1 or br in (0, 15) or sr == 3:
            break  # not a Layer III frame header: stop rather than guess
        mpeg1 = ver == 3
        rate = _RATE[1 if mpeg1 else 2 if ver == 2 else 25][sr]
        size = (144 if mpeg1 else 72) * _KBPS[1 if mpeg1 else 2][br] * 1000 // rate + pad
        if i + size > len(b):
            break
        if not crc:
            ch = 1 if mono else 2
            bit = (i + 4) * 8 + ((9 + (5 if mono else 3) + 4 * ch) if mpeg1 else (8 + (1 if mono else 2)))
            for _ in range(ch * (2 if mpeg1 else 1)):
                field(bit + 21, steps)
                bit += 59 if mpeg1 else 63
        i += size
    return bytes(b)


class Voice:
    """Called with Hindi text it returns Polly's mp3, like a plain speaker function. speak_pa() reads Punjabi
    text and returns None when Sarvam is unavailable, in which case the farmer hears the Hindi."""

    def __init__(self, region: str | None = None, speak_pa=sarvam.speak_pa, translate_pa=sarvam.translate_pa):
        self.region = region
        self.speak_pa = speak_pa
        self.translate_pa = translate_pa

    def __call__(self, text: str, language: str = "hi-IN") -> bytes:
        return polly_mp3(text, self.region, language)


def speak(speaker, text: str, lang: str) -> bytes | None:
    """mp3 of text in lang ("hi", "hr", "en", "pa"), or None if no voice for it is available."""
    if speaker is None or not text:
        return None
    if lang == "pa":
        return speaker.speak_pa(text) if hasattr(speaker, "speak_pa") else None
    if lang == "en":
        return speaker(text, "en-IN") if isinstance(speaker, Voice) else None
    return speaker(text)  # Hindi; Haryanvi is read by the Hindi voice
