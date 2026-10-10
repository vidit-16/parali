"""Speech for the farmer. Hindi, Haryanvi and Indian English with Amazon Polly (the Kajal voice speaks both
Hindi and English); Punjabi with Sarvam (sarvam.py). The text comes from messages.py and agent.compose; the
voices only read it."""
from parali import sarvam

VOICE = "Kajal"


def polly_mp3(text: str, region: str | None = None, language: str = "hi-IN") -> bytes:
    import boto3
    polly = boto3.client("polly", region_name=region)
    r = polly.synthesize_speech(Text=text, VoiceId=VOICE, Engine="neural", LanguageCode=language, OutputFormat="mp3")
    return r["AudioStream"].read()


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
