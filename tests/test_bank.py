import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from nuv.audio import pcm_wem
from nuv.bank import Bank


def chunk(tag, payload):
    return tag + struct.pack("<I", len(payload)) + payload


def obj(kind, oid, payload):
    return struct.pack("<BII", kind, len(payload) + 4, oid) + payload


def sample_bank(*, version=135, event_actions=(20, 21), extra=b""):
    header = struct.pack("<IIIII", version, 100, 0, 16, 1)
    # Actor mixer routing prefix: no FX, no attachments, bus 1234, no parent.
    mixer = obj(7, 30, b"\0\0\0" + struct.pack("<II", 1234, 0) + bytes(21))
    play = obj(3, 20, struct.pack("<HIBBBB I", 0x0403, 30, 0, 0, 0, 4, 100))
    other = obj(3, 21, b"unknown original action")
    event = obj(4, 10, bytes([len(event_actions)]) + b"".join(struct.pack("<I", a) for a in event_actions))
    unknown = obj(99, 40, b"\xFF\0preserve\0\xBB")
    objects = (mixer, play, other, event, unknown)
    return (chunk(b"BKHD", header) + chunk(b"ZZZZ", b"opaque chunk")
            + chunk(b"DIDX", struct.pack("<III", 555, 0, 4))
            + chunk(b"DATA", b"old!")
            + chunk(b"HIRC", struct.pack("<I", len(objects)) + b"".join(objects)) + extra)


class BankTests(unittest.TestCase):
    def wem(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "voice.wav"
            with wave.open(str(path), "wb") as out:
                out.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
                out.writeframes(b"\0\0" * 480)
            return pcm_wem(path)

    def test_roundtrip_is_byte_identical_including_unknown_chunks_and_objects(self):
        original = sample_bank()
        bank = Bank.parse(original)
        self.assertEqual(bank.version, 135)
        self.assertEqual(bank.event_ids, {10})
        self.assertEqual(bank.event_actions(10), (20, 21))
        self.assertEqual(bank.to_bytes(), original)

    def test_chunks_exposes_immutable_original_envelopes_for_preservation_checks(self):
        bank = Bank.parse(sample_bank())
        chunks = bank.chunks
        self.assertIsInstance(chunks, tuple)
        self.assertEqual([part.tag for part in chunks], [b"BKHD", b"ZZZZ", b"DIDX", b"DATA", b"HIRC"])
        self.assertEqual(chunks[1].payload, b"opaque chunk")
        with self.assertRaises(AttributeError):
            chunks[1].payload = b"changed"
        bank.add_voice(10, "chunks-check", self.wem())
        saved = Bank.parse(bank.to_bytes())
        self.assertEqual(saved.chunks[1], chunks[1])

    def test_append_voice_preserves_every_original_object_except_event(self):
        bank = Bank.parse(sample_bank())
        before = {o.id: o for o in bank.objects}
        result = bank.add_voice(10, "test-wylder", self.wem(), volume_db=-3)
        reparsed = Bank.parse(bank.to_bytes())
        self.assertEqual(reparsed.event_actions(10), (20, 21, result["action_id"]))
        self.assertEqual(len(reparsed.objects), len(before) + 2)
        for current in reparsed.objects:
            if current.id in before and current.id != 10:
                self.assertEqual(current, before[current.id])
        self.assertEqual(reparsed.media_bytes(555), b"old!")
        self.assertEqual(reparsed.media_bytes(result["media_id"]), self.wem())
        self.assertEqual(result["bus_id"], 1234)
        self.assertEqual(result["original_action_ids"], [20, 21])
        self.assertEqual(reparsed.objects_by_id[result["sound_id"]].kind, 2)
        self.assertEqual(reparsed.objects_by_id[result["action_id"]].kind, 3)

    def test_rejects_missing_event_repeated_namespace_and_bad_wem_without_mutating(self):
        bank = Bank.parse(sample_bank())
        original = bank.to_bytes()
        for event, namespace, wem in ((999, "test", self.wem()), (10, "", self.wem()),
                                      (10, "test", b"bad")):
            with self.subTest(event=event, namespace=namespace), self.assertRaises(ValueError):
                bank.add_voice(event, namespace, wem)
            self.assertEqual(bank.to_bytes(), original)
        bank.add_voice(10, "test", self.wem())
        patched = bank.to_bytes()
        with self.assertRaises(ValueError):
            Bank.parse(patched).add_voice(10, "test", self.wem())
        self.assertEqual(bank.to_bytes(), patched)

    def test_rejects_truncation_duplicate_ids_bad_chunk_sizes_and_bad_indexes(self):
        original = sample_bank()
        corruptions = [original[:-1], original + b"garbage", original + chunk(b"BKHD", bytes(20))]
        corruptions.append(original.replace(struct.pack("<III", 555, 0, 4), struct.pack("<III", 555, 3, 4)))
        corruptions.append(original.replace(obj(99, 40, b"\xFF\0preserve\0\xBB"), obj(99, 21, b"\xFF\0preserve\0\xBB")))
        corruptions.append(original.replace(obj(4, 10, b"\x02" + struct.pack("<II", 20, 21)), obj(4, 10, b"\x03" + struct.pack("<II", 20, 21))))
        for corrupt in corruptions:
            with self.subTest(digest=hashlib.sha256(corrupt).hexdigest()[:8]), self.assertRaises(ValueError):
                Bank.parse(corrupt)

    def test_unsupported_version_can_roundtrip_but_cannot_be_patched(self):
        original = sample_bank(version=136)
        bank = Bank.parse(original)
        self.assertEqual(bank.to_bytes(), original)
        with self.assertRaisesRegex(ValueError, "version"):
            bank.add_voice(10, "test", self.wem())

    def test_unresolved_bus_fails_without_mutation(self):
        original = sample_bank().replace(struct.pack("<II", 1234, 0), bytes(8))
        bank = Bank.parse(original)
        with self.assertRaisesRegex(ValueError, "bus"):
            bank.add_voice(10, "test", self.wem())
        self.assertEqual(bank.to_bytes(), original)

    def test_new_voice_explicitly_plays_once_and_limits_instances_per_game_object(self):
        bank = Bank.parse(sample_bank())
        result = bank.add_voice(10, "finite", self.wem(), volume_db=-6)
        sound = bank.objects_by_id[result["sound_id"]].payload
        self.assertEqual(struct.unpack_from("<I", sound)[0], 0x00010001)
        self.assertEqual(sound[4], 0)  # embedded, no external stream
        self.assertEqual(struct.unpack_from("<I", sound, 9)[0], len(self.wem()))
        # Independent v135 schema: source(14), FX/routing(12), prop bundle.
        count = sound[26]
        properties = {sound[27 + index]: sound[27 + count + index * 4:31 + count + index * 4]
                      for index in range(count)}
        self.assertIn(0x3A, properties)  # AkPropID Loop
        self.assertEqual(struct.unpack("<I", properties[0x3A])[0], 1)
        self.assertEqual(struct.unpack("<f", properties[0])[0], -6)
        after_props = 27 + count * 5
        self.assertEqual(sound[after_props], 0)  # no ranged modifiers
        positioning = after_props + 1
        self.assertEqual(sound[positioning], 1)  # 2D positioning override
        advanced = positioning + 1 + 1 + 4
        self.assertEqual(sound[advanced] & 0x05, 1)  # kill newest, per game object
        self.assertEqual(struct.unpack_from("<H", sound, advanced + 2)[0], 1)

    def test_generated_sound_action_and_media_ids_use_native_30_bit_domain(self):
        bank = Bank.parse(sample_bank())
        result = bank.add_voice(10, "range-test", self.wem())
        for role in ("sound_id", "action_id", "media_id"):
            with self.subTest(role=role):
                self.assertGreater(result[role], 0)
                self.assertLessEqual(result[role], 0x3FFFFFFF)
        again = Bank.parse(sample_bank()).add_voice(10, "range-test", self.wem())
        self.assertEqual(result, again)

    def test_large_event_count_uses_wwise_big_endian_varint_and_aligns_data(self):
        # Wwise varuint is base-128 most-significant group first, unlike LEB128.
        actions = (20,) * 127
        bank = Bank.parse(sample_bank(event_actions=actions))
        result = bank.add_voice(10, "large-event", self.wem())
        output = bank.to_bytes()
        parsed = Bank.parse(output)
        self.assertEqual(parsed.objects_by_id[10].payload[:2], b"\x81\0")
        self.assertEqual(parsed.event_actions(10), actions + (result["action_id"],))
        cursor = 0
        while output[cursor:cursor + 4] != b"DATA":
            cursor += 8 + struct.unpack_from("<I", output, cursor + 4)[0]
        self.assertEqual((cursor + 8) % 16, 0)

    def test_budget_failure_is_atomic_and_precedes_appending_large_media(self):
        from unittest.mock import patch
        bank = Bank.parse(sample_bank())
        original = bank.to_bytes()
        with patch("nuv.bank.MAX_BANK_BYTES", len(original) + len(self.wem())), self.assertRaises(ValueError):
            bank.add_voice(10, "budget", self.wem())
        self.assertEqual(bank.to_bytes(), original)

    def test_multiple_patches_survive_save_and_keep_each_media_payload(self):
        bank = Bank.parse(sample_bank())
        first = bank.add_voice(10, "first", self.wem())
        second = bank.add_voice(10, "second", self.wem(), volume_db=-12)
        saved = Bank.parse(bank.to_bytes())
        self.assertEqual(saved.event_actions(10), (20, 21, first["action_id"], second["action_id"]))
        self.assertEqual(saved.media_bytes(first["media_id"]), self.wem())
        self.assertEqual(saved.media_bytes(second["media_id"]), self.wem())
        third = saved.add_voice(10, "third", self.wem())
        again = Bank.parse(saved.to_bytes())
        self.assertEqual(again.event_actions(10)[-1], third["action_id"])
        self.assertEqual(len(again.objects), 11)

    def test_bank_without_embedded_media_gets_aligned_media_chunks(self):
        original = sample_bank()
        original = original.replace(chunk(b"DIDX", struct.pack("<III", 555, 0, 4)), b"")
        original = original.replace(chunk(b"DATA", b"old!"), b"")
        bank = Bank.parse(original)
        result = bank.add_voice(10, "new-media", self.wem())
        saved = Bank.parse(bank.to_bytes())
        self.assertEqual(saved.media_bytes(result["media_id"]), self.wem())
        self.assertEqual(saved.event_actions(10), (20, 21, result["action_id"]))


if __name__ == "__main__":
    unittest.main()
