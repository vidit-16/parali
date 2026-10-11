from parali.speech import opus_rate


def test_opus_rate_comes_from_the_voice_note_header():
    head = b"OggS" + b"\0" * 24 + b"OpusHead" + bytes([1, 1, 0x38, 0x01]) + (16000).to_bytes(4, "little")
    assert opus_rate(head) == 16000
    assert opus_rate(head.replace((16000).to_bytes(4, "little"), (48000).to_bytes(4, "little"))) == 48000
    assert opus_rate(b"not an ogg file") == 16000  # unreadable: the usual WhatsApp rate
