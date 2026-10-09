"""Speech for the farmer. Hindi with Amazon Polly; Punjabi with Sarvam (sarvam.py). The text comes from
messages.py and agent.compose; the voices only read it."""
from parali import sarvam

VOICE = "Kajal"


def polly_mp3(text: str, region: str | None = None) -> bytes:
    import boto3
    polly = boto3.client("polly", region_name=region)
    r = polly.synthesize_speech(Text=text, VoiceId=VOICE, Engine="neural", LanguageCode="hi-IN", OutputFormat="mp3")
    return r["AudioStream"].read()


class Voice:
    """Called with Hindi text it returns Polly's mp3, like a plain speaker function. speak_pa() reads Punjabi
    text and returns None when Sarvam is unavailable, in which case the farmer hears the Hindi."""

    def __init__(self, region: str | None = None, speak_pa=sarvam.speak_pa, translate_pa=sarvam.translate_pa):
        self.region = region
        self.speak_pa = speak_pa
        self.translate_pa = translate_pa

    def __call__(self, text: str) -> bytes:
        return polly_mp3(text, self.region)
