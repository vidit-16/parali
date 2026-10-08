"""Hindi speech with Amazon Polly. The text comes from messages.py; Polly only reads it."""

VOICE = "Kajal"


def polly_mp3(text: str, region: str | None = None) -> bytes:
    import boto3
    polly = boto3.client("polly", region_name=region)
    r = polly.synthesize_speech(Text=text, VoiceId=VOICE, Engine="neural", LanguageCode="hi-IN", OutputFormat="mp3")
    return r["AudioStream"].read()
