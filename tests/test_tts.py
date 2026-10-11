from parali.tts import louder


def frame(gain: int) -> bytes:
    """One MPEG-2 Layer III mono frame (64 kbps, 24 kHz, no CRC) with the given global_gain."""
    f = bytearray(192)
    f[:4] = bytes.fromhex("fff364c4")
    bit = 4 * 8 + 8 + 1 + 21  # side info: main_data_begin, private bit, part2_3_length + big_values
    byte, sh = divmod(bit, 8)
    w = (f[byte] << 8 | f[byte + 1]) | gain << (8 - sh)
    f[byte], f[byte + 1] = w >> 8, w & 0xFF
    return bytes(f)


def gain(f: bytes, at: int = 0) -> int:
    byte, sh = divmod((at + 4) * 8 + 30, 8)
    return ((f[byte] << 8 | f[byte + 1]) >> (8 - sh)) & 0xFF


def test_louder_raises_every_frame_and_leaves_the_rest():
    tag = b"ID3\x04\x00\x00\x00\x00\x00\x02xx"
    mp3 = tag + frame(140) + frame(255)
    out = louder(mp3, 2)
    assert len(out) == len(mp3) and out[:12] == tag
    assert gain(out, 12) == 142
    assert gain(out, 12 + 192) == 255  # never wraps round
    assert out[12:16] == mp3[12:16]
    assert louder(mp3, 0) == mp3


def test_louder_leaves_something_that_is_not_mp3_alone():
    assert louder(b"not audio at all", 3) == b"not audio at all"
