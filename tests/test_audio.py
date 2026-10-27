import math
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from nuv.audio import pcm_wem, validate_pcm_wem


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "voice.wav"

    def write_wave(self, *, channels=1, rate=48000, width=2, frames=480,
                   samples=None):
        with wave.open(str(self.path), "wb") as out:
            out.setnchannels(channels)
            out.setsampwidth(width)
            out.setframerate(rate)
            out.writeframes(samples if samples is not None else bytes(frames * channels * width))

    def test_pcm_samples_survive_conversion_and_wem_has_wwise_channel_config(self):
        samples = struct.pack("<hhhh", -32768, -2000, 2000, 32767)
        self.write_wave(channels=2, samples=samples)
        wem = pcm_wem(self.path)
        self.assertEqual(wem[:4], b"RIFF")
        self.assertEqual(struct.unpack_from("<I", wem, 4)[0], len(wem) - 8)
        self.assertEqual(wem[8:16], b"WAVEfmt ")
        self.assertEqual(struct.unpack_from("<I", wem, 16)[0], 24)
        self.assertEqual(struct.unpack_from("<H", wem, 20)[0], 0xFFFE)
        self.assertEqual(struct.unpack_from("<I", wem, 40)[0], 0x3102)
        self.assertEqual(wem[52:], samples)
        self.assertEqual(validate_pcm_wem(wem)["frames"], 2)

    def test_gain_changes_samples_and_clips_to_signed_pcm16(self):
        self.write_wave(samples=struct.pack("<hh", 1000, 30000))
        wem = pcm_wem(self.path, gain_db=20 * math.log10(2))
        self.assertEqual(struct.unpack("<hh", wem[52:]), (2000, 32767))

    def test_rejects_unsupported_audio_and_duration_before_reading_frames(self):
        for settings in ({"channels": 3}, {"rate": 96000}, {"width": 3},
                         {"frames": 0}, {"frames": 48000 * 8 + 1}):
            with self.subTest(settings=settings):
                self.write_wave(**settings)
                with self.assertRaises(ValueError):
                    pcm_wem(self.path)
        self.write_wave()
        data = bytearray(self.path.read_bytes())
        struct.pack_into("<I", data, 40, 0xFFFFFFFE)
        self.path.write_bytes(data)
        with self.assertRaises(ValueError):
            pcm_wem(self.path)

    def test_rejects_truncated_input_and_nonfinite_gain(self):
        self.write_wave()
        self.path.write_bytes(self.path.read_bytes()[:-2])
        with self.assertRaises(ValueError):
            pcm_wem(self.path)
        self.write_wave()
        for gain in (float("nan"), float("inf"), -61, 13):
            with self.subTest(gain=gain), self.assertRaises(ValueError):
                pcm_wem(self.path, gain_db=gain)

    def test_wem_validation_checks_sizes_codec_and_frame_alignment(self):
        self.write_wave()
        wem = pcm_wem(self.path)
        for corrupt in (wem[:-1], wem + b"x", wem[:20] + b"\x01\x00" + wem[22:]):
            with self.subTest(size=len(corrupt)), self.assertRaises(ValueError):
                validate_pcm_wem(corrupt)


if __name__ == "__main__":
    unittest.main()
