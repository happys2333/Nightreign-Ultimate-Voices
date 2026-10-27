"""Bounded PCM16 WAV input and little-endian Wwise PCM media.

The emitted 24-byte fmt uses Wwise's AkChannelConfig extension, as documented
by vgmstream/src/meta/wwise.c. It contains no loops or streaming prefetch.
"""

from array import array
import math
from pathlib import Path
import struct
import sys
import wave


MAX_SECONDS = 8
MAX_RATE = 48000
MAX_PCM_BYTES = MAX_SECONDS * MAX_RATE * 2 * 2
MAX_WAV_BYTES = MAX_PCM_BYTES + 1024 * 1024


def _gain(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("gain must be a finite number between -60 and 12 dB")
    if not math.isfinite(value) or not -60 <= value <= 12:
        raise ValueError("gain must be a finite number between -60 and 12 dB")
    return float(value)


def pcm_wem(path: Path, gain_db: float = 0.0) -> bytes:
    """Read <=8 seconds of mono/stereo PCM16 WAV at <=48 kHz.

    A size budget is checked before reading the file or allocating sample
    storage. Positive gain saturates at the PCM16 range; it cannot wrap.
    """
    gain_db = _gain(gain_db)
    path = Path(path)
    size = path.stat().st_size
    if size > MAX_WAV_BYTES:
        raise ValueError("WAV file exceeds the input byte budget")
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels()
            rate = source.getframerate()
            frames = source.getnframes()
            if channels not in (1, 2) or source.getsampwidth() != 2:
                raise ValueError("voice WAV must be mono/stereo PCM16")
            if source.getcomptype() != "NONE" or not 1 <= rate <= MAX_RATE:
                raise ValueError("voice WAV must be uncompressed PCM at <=48000 Hz")
            if not 1 <= frames <= rate * MAX_SECONDS:
                raise ValueError("voice WAV must contain 0 < duration <=8 seconds")
            expected = frames * channels * 2
            if expected > MAX_PCM_BYTES:
                raise ValueError("WAV PCM data exceeds the byte budget")
            pcm = source.readframes(frames)
            if len(pcm) != expected:
                raise ValueError("truncated WAV PCM data")
    except (wave.Error, EOFError, struct.error) as exc:
        raise ValueError(f"invalid PCM WAV: {exc}") from exc
    if gain_db:
        samples = array("h")
        samples.frombytes(pcm)
        if sys.byteorder != "little":
            samples.byteswap()
        factor = 10 ** (gain_db / 20)
        for index, value in enumerate(samples):
            samples[index] = max(-32768, min(32767, round(value * factor)))
        if sys.byteorder != "little":
            samples.byteswap()
        pcm = samples.tobytes()
    mask = 4 if channels == 1 else 3
    channel_config = channels | 0x100 | (mask << 12)
    fmt = struct.pack("<HHIIHHHHI", 0xFFFE, channels, rate, rate * channels * 2,
                      channels * 2, 16, 6, 16, channel_config)
    body = b"WAVEfmt " + struct.pack("<I", len(fmt)) + fmt
    body += b"data" + struct.pack("<I", len(pcm)) + pcm
    return b"RIFF" + struct.pack("<I", len(body)) + body


def validate_pcm_wem(data: bytes) -> dict:
    """Accept only the bounded, one-shot PCM WEM layout emitted above."""
    if not isinstance(data, bytes) or not 54 <= len(data) <= MAX_PCM_BYTES + 52:
        raise ValueError("invalid PCM WEM size")
    if data[:4] != b"RIFF" or data[8:16] != b"WAVEfmt ":
        raise ValueError("voice media must be little-endian PCM WEM")
    if struct.unpack_from("<I", data, 4)[0] != len(data) - 8:
        raise ValueError("invalid PCM WEM RIFF size")
    if struct.unpack_from("<I", data, 16)[0] != 24 or data[44:48] != b"data":
        raise ValueError("unsupported PCM WEM chunk layout")
    tag, channels, rate, byte_rate, align, bits, extra, valid, config = struct.unpack_from(
        "<HHIIHHHHI", data, 20)
    if (tag != 0xFFFE or channels not in (1, 2) or not 1 <= rate <= MAX_RATE
            or align != channels * 2 or byte_rate != rate * align
            or bits != 16 or extra != 6 or valid != 16):
        raise ValueError("unsupported PCM WEM format")
    mask = 4 if channels == 1 else 3
    if config != channels | 0x100 | (mask << 12):
        raise ValueError("invalid Wwise PCM channel configuration")
    size = struct.unpack_from("<I", data, 48)[0]
    if size != len(data) - 52 or size % align or not 0 < size <= rate * align * MAX_SECONDS:
        raise ValueError("invalid PCM WEM data size or duration")
    return {"channels": channels, "sample_rate": rate, "frames": size // align,
            "duration_seconds": size / align / rate, "pcm_bytes": size}
