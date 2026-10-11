"""Farmer's voice to text with Amazon Transcribe streaming (hi-IN).

The browser records 16 kHz mono PCM (16-bit little-endian) and sends it in one request; we stream it to
Transcribe and return the final transcript. A clip of a few seconds comes back in about the length of the clip.
WhatsApp voice notes (Ogg Opus) go to Transcribe as they are: it reads that format directly. Sarvam is the
first choice for both; this is the fallback when Sarvam is unavailable.
"""
import asyncio

SAMPLE_RATE = 16000
CHUNK = 8000  # bytes: 0.25 s of 16 kHz 16-bit audio
MAX_SECONDS = 30


def transcribe_pcm(pcm: bytes, language: str = "hi-IN", region: str = "us-west-2") -> str:
    if len(pcm) > SAMPLE_RATE * 2 * MAX_SECONDS:
        pcm = pcm[: SAMPLE_RATE * 2 * MAX_SECONDS]
    return asyncio.run(_stream(pcm, language, region))


def opus_rate(ogg: bytes) -> int:
    """The input sample rate written in an Ogg Opus file's header (OpusHead), 16000 if it cannot be read."""
    i = ogg.find(b"OpusHead")
    if i < 0 or len(ogg) < i + 16:
        return 16000
    rate = int.from_bytes(ogg[i + 12:i + 16], "little")
    return rate if 8000 <= rate <= 48000 else 16000


def transcribe_ogg(ogg: bytes, language: str = "hi-IN", region: str = "us-west-2") -> str:
    """A WhatsApp voice note (Ogg Opus) to text."""
    return asyncio.run(_stream(ogg[: 2_000_000], language, region, encoding="ogg-opus", rate=opus_rate(ogg)))


async def _stream(pcm: bytes, language: str, region: str, encoding: str = "pcm", rate: int = SAMPLE_RATE) -> str:
    from amazon_transcribe.client import TranscribeStreamingClient
    from amazon_transcribe.handlers import TranscriptResultStreamHandler

    parts: list[str] = []

    class Handler(TranscriptResultStreamHandler):
        async def handle_transcript_event(self, event):
            for r in event.transcript.results:
                if not r.is_partial and r.alternatives:
                    parts.append(r.alternatives[0].transcript)

    client = TranscribeStreamingClient(region=region)
    stream = await client.start_stream_transcription(
        language_code=language, media_sample_rate_hz=rate, media_encoding=encoding)

    async def send():
        for i in range(0, len(pcm), CHUNK):
            await stream.input_stream.send_audio_event(audio_chunk=pcm[i:i + CHUNK])
        await stream.input_stream.end_stream()

    await asyncio.gather(send(), Handler(stream.output_stream).handle_events())
    return " ".join(parts).strip()
