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

    def test_normalization_boosts_quiet_speech_to_target_level(self):
        original = (-800, -400, 0, 400, 800) * 100
        self.write_wave(samples=struct.pack(f"<{len(original)}h", *original))
        wem = pcm_wem(self.path, normalize=True)
        samples = struct.unpack(f"<{len(original)}h", wem[52:])
        rms = math.sqrt(sum(value * value for value in samples) / len(samples))
        self.assertAlmostEqual(20 * math.log10(rms / 32768), -18, delta=0.01)
        self.assertGreater(rms, 5 * math.sqrt(sum(value * value for value in original)
                                            / len(original)))
        self.assertEqual(samples[2], 0)
        self.assertAlmostEqual(samples[0], 2 * samples[1], delta=1)
        self.assertEqual(samples[0], -samples[4])
        self.assertEqual(wem[:52], pcm_wem(self.path)[:52])
        self.assertEqual(validate_pcm_wem(wem)["frames"], len(original))

    def test_normalization_lowers_loud_speech_to_target_level(self):
        original = (-20000, -10000, 0, 10000, 20000) * 100
        self.write_wave(samples=struct.pack(f"<{len(original)}h", *original))
        samples = struct.unpack(f"<{len(original)}h", pcm_wem(self.path, normalize=True)[52:])
        rms = math.sqrt(sum(value * value for value in samples) / len(samples))
        self.assertAlmostEqual(20 * math.log10(rms / 32768), -18, delta=0.01)
        self.assertLess(max(samples), max(original))
        self.assertAlmostEqual(samples[0], 2 * samples[1], delta=1)

    def test_normalization_preserves_transients_below_peak_ceiling(self):
        original = (16000, -16000) + (100, -100) * 200
        self.write_wave(samples=struct.pack(f"<{len(original)}h", *original))
        samples = struct.unpack(f"<{len(original)}h", pcm_wem(self.path, normalize=True)[52:])
        peak = max(abs(value) for value in samples)
        self.assertAlmostEqual(20 * math.log10(peak / 32768), -1, delta=0.001)
        rms = math.sqrt(sum(value * value for value in samples) / len(samples))
        self.assertLess(20 * math.log10(rms / 32768), -18)
        self.assertAlmostEqual(samples[0] / original[0], samples[2] / original[2], delta=0.01)
        self.assertEqual(samples[0], -samples[1])

    def test_normalization_limits_upward_boost_for_near_silence(self):
        original = (-10, -5, 0, 5, 10) * 100
        self.write_wave(samples=struct.pack(f"<{len(original)}h", *original))
        samples = struct.unpack(f"<{len(original)}h", pcm_wem(self.path, normalize=True)[52:])
        boost_db = 20 * math.log10(max(samples) / max(original))
        self.assertAlmostEqual(boost_db, 24, delta=0.05)
        self.assertLess(max(samples), 200)

    def test_normalization_keeps_digital_silence_silent(self):
        self.write_wave(channels=2)
        raw = pcm_wem(self.path)
        self.assertEqual(pcm_wem(self.path, gain_db=12, normalize=True), raw)

    def test_explicit_gain_is_applied_after_normalization(self):
        original = (-800, -400, 0, 400, 800) * 100
        self.write_wave(samples=struct.pack(f"<{len(original)}h", *original))
        normalized = struct.unpack(f"<{len(original)}h", pcm_wem(self.path, normalize=True)[52:])
        samples = struct.unpack(f"<{len(original)}h",
                                pcm_wem(self.path, gain_db=-6, normalize=True)[52:])
        rms = math.sqrt(sum(value * value for value in samples) / len(samples))
        self.assertAlmostEqual(20 * math.log10(rms / 32768), -24, delta=0.01)
        self.assertAlmostEqual(samples[4] / normalized[4], 10 ** (-6 / 20), delta=0.001)

    def test_explicit_gain_may_exceed_normalization_peak_ceiling_and_saturates(self):
        original = (16000, -16000) + (100, -100) * 200
        self.write_wave(samples=struct.pack(f"<{len(original)}h", *original))
        samples = struct.unpack(f"<{len(original)}h",
                                pcm_wem(self.path, gain_db=6, normalize=True)[52:])
        self.assertEqual(samples[:2], (32767, -32768))
        self.assertGreater(samples[2], 300)
        self.assertEqual(samples[2], -samples[3])

    def test_normalization_uses_all_stereo_samples_with_one_shared_gain(self):
        original = (-1000, 100, -500, 50, 0, 0, 500, -50, 1000, -100) * 100
        self.write_wave(channels=2, samples=struct.pack(f"<{len(original)}h", *original))
        wem = pcm_wem(self.path, normalize=True)
        samples = struct.unpack(f"<{len(original)}h", wem[52:])
        rms = math.sqrt(sum(value * value for value in samples) / len(samples))
        self.assertAlmostEqual(20 * math.log10(rms / 32768), -18, delta=0.01)
        self.assertAlmostEqual(samples[0], -10 * samples[1], delta=5)
        self.assertAlmostEqual(samples[2], -10 * samples[3], delta=5)
        self.assertEqual(samples[4:6], (0, 0))
        self.assertEqual(validate_pcm_wem(wem)["channels"], 2)
        self.assertEqual(validate_pcm_wem(wem)["frames"], len(original) // 2)

    def test_rejects_non_boolean_normalization_options(self):
        self.write_wave()
        for normalize in (1, 0, "yes", "false", None, 1.0):
            with self.subTest(normalize=normalize), self.assertRaises(ValueError):
                pcm_wem(self.path, normalize=normalize)

    def test_disabling_normalization_preserves_original_pcm_and_existing_gain(self):
        original = (-32768, -2000, 0, 2000, 32767)
        pcm = struct.pack(f"<{len(original)}h", *original)
        self.write_wave(samples=pcm)
        self.assertEqual(pcm_wem(self.path, normalize=False)[52:], pcm)
        self.assertEqual(pcm_wem(self.path, normalize=False), pcm_wem(self.path))
        self.assertEqual(pcm_wem(self.path, gain_db=-6, normalize=False),
                         pcm_wem(self.path, gain_db=-6))

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
