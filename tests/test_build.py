from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from test_bank import sample_bank


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        with wave.open(str(self.root / "voice.wav"), "wb") as stream:
            stream.setparams((1, 2, 24000, 0, "NONE", ""))
            stream.writeframes(struct.pack("<h", 1000) * 2400)
        self.mapping = {"game_version":"1.3.3.0", "bank":"sd/cs_main.bnk",
                        "characters":[{"id":"wylder","name_zh":"追踪者","events":["Play_c000107105"]}]}
        self.voices = {"gain_db":-6,"characters":{"wylder":{"audio":"voice.wav","enabled":True}}}

    def bank(self):
        from nuv.build import event_hash
        return sample_bank().replace(struct.pack("<BII",4,13,10), struct.pack("<BII",4,13,event_hash("Play_c000107105")))

    def test_build_preserves_original_actions_and_has_no_runtime_components(self):
        from nuv.bank import Bank
        from nuv.build import build_bank, event_hash
        source = self.bank()
        built, report = build_bank(source, self.mapping, self.voices, self.root)
        event = event_hash("Play_c000107105")
        self.assertEqual(Bank.parse(built).event_actions(event)[:2], (20,21))
        self.assertEqual(report["characters"][0]["id"], "wylder")
        self.assertEqual(report["source_sha256"], hashlib.sha256(source).hexdigest())
        self.assertEqual(report["runtime"], {"processes":0,"dlls":0,"polling":False,"network_messages":0})
        self.assertGreater(report["added_media_bytes"],0)

    def test_build_normalizes_quiet_callouts_by_default_and_allows_role_override(self):
        from nuv.bank import Bank
        from nuv.build import build_bank
        voices = deepcopy(self.voices)
        voices["gain_db"] = 0
        for global_flag, role_flag, normalized in (
                (None, None, True), (False, True, True), (True, False, False)):
            with self.subTest(global_flag=global_flag, role_flag=role_flag):
                config = deepcopy(voices)
                if global_flag is not None:
                    config["normalize"] = global_flag
                if role_flag is not None:
                    config["characters"]["wylder"]["normalize"] = role_flag
                built, report = build_bank(self.bank(), self.mapping, config, self.root)
                detail = report["characters"][0]
                wem = Bank.parse(built).media_bytes(detail["events"][0]["media_id"])
                sample = struct.unpack_from("<h", wem, 52)[0]
                if normalized:
                    self.assertGreater(sample, 4100)
                    self.assertLess(sample, 4150)
                else:
                    self.assertEqual(sample, 1000)
                self.assertEqual(detail["normalize"], normalized)

    def test_new_animation_event_uses_verified_template_without_changing_original(self):
        from nuv.bank import Bank
        from nuv.build import build_bank, event_hash
        mapping = deepcopy(self.mapping)
        mapping["characters"][0]["events"] = ["Play_c900207000"]
        mapping["characters"][0]["event_templates"] = {"Play_c900207000":"Play_c000107105"}
        old_id = event_hash("Play_c000107105")
        new_id = event_hash("Play_c900207000")
        source = self.bank()
        mapping["event_fingerprints"] = {"Play_c000107105":hashlib.sha256(Bank.parse(source).objects_by_id[old_id].payload).hexdigest()}
        built, report = build_bank(source, mapping, self.voices, self.root)
        saved = Bank.parse(built)
        event = report["characters"][0]["events"][0]
        self.assertEqual(saved.event_actions(new_id), (event["action_id"],))
        for original in Bank.parse(source).objects:
            self.assertEqual(saved.objects_by_id[original.id], original)
        self.assertEqual(event["template_name"], "Play_c000107105")
        self.assertTrue(event["created_event"])
        mapping["event_fingerprints"]["Play_c000107105"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "changed"):
            build_bank(source, mapping, self.voices, self.root)

    def test_audited_native_vocal_action_is_removed_before_appending_callout(self):
        from nuv.bank import Bank
        from nuv.build import build_bank, digest, event_hash
        source = self.bank()
        originals = Bank.parse(source).objects_by_id
        eid = event_hash("Play_c000107105")
        mapping = deepcopy(self.mapping)
        mapping["banks"] = {mapping["bank"]:digest(source)}
        mapping["characters"][0]["native_vocals"] = [{"event":"Play_c000107105",
            "event_sha256":digest(originals[eid].payload), "actions":{"20":digest(originals[20].payload)}}]
        built, report = build_bank(source, mapping, self.voices, self.root)
        event = report["characters"][0]["events"][0]
        parsed = Bank.parse(built)
        self.assertEqual(parsed.event_actions(eid), (21,event["action_id"]))
        self.assertEqual(parsed.objects_by_id[20], originals[20])
        self.assertEqual(parsed.media_bytes(555), b"old!")
        self.assertEqual(report["characters"][0]["native_vocals"][0]["removed_action_ids"], [20])
        mapping["characters"][0]["native_vocals"][0]["actions"]["20"] = "0"*64
        with self.assertRaisesRegex(ValueError,"vocal.*changed"):
            build_bank(source, mapping, self.voices, self.root)

    def test_build_rejects_non_boolean_normalization(self):
        from nuv.build import build_bank
        for value in (1, "yes", None):
            voices = deepcopy(self.voices)
            voices["normalize"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "normalize"):
                build_bank(self.bank(), self.mapping, voices, self.root)

    def test_refuses_changed_original_event_and_unknown_roles(self):
        from nuv.build import build_bank
        mapping = deepcopy(self.mapping)
        mapping["event_fingerprints"] = {"Play_c000107105":"0"*64}
        with self.assertRaisesRegex(ValueError,"changed"):
            build_bank(self.bank(),mapping,self.voices,self.root)
        voices = deepcopy(self.voices)
        voices["characters"]["typo"]={"audio":"voice.wav","enabled":True}
        with self.assertRaisesRegex(ValueError,"Unknown"):
            build_bank(self.bank(),self.mapping,voices,self.root)

    def test_disabled_character_needs_no_file_and_never_changes_bank(self):
        from nuv.build import build_bank
        voices = {"characters":{"wylder":{"enabled":False}}}
        built, report = build_bank(self.bank(),self.mapping,voices,self.root)
        self.assertEqual(built,self.bank())
        self.assertEqual(report["added_media_bytes"],0)

    def test_failure_does_not_touch_existing_output_or_game_files(self):
        from nuv.build import build_bank, write_package
        output=self.root/"out"
        source=self.bank()
        built,report=build_bank(source,self.mapping,self.voices,self.root)
        write_package(output,built,"profileVersion='v1'\n",report)
        original={p.relative_to(output):p.read_bytes() for p in output.rglob("*") if p.is_file()}
        bad=deepcopy(self.voices)
        bad["characters"]["wylder"]["audio"]="missing.wav"
        with self.assertRaises(FileNotFoundError):
            build_bank(source,self.mapping,bad,self.root)
        self.assertEqual(original,{p.relative_to(output):p.read_bytes() for p in output.rglob("*") if p.is_file()})
        (output/"my-notes.txt").write_text("keep me")
        with self.assertRaisesRegex(ValueError,"unowned"):
            write_package(output,built,"profileVersion='v1'\n",report)
        self.assertEqual((output/"my-notes.txt").read_text(),"keep me")

    def test_owned_package_can_rebuild_and_verify_detects_tampering(self):
        from nuv.build import build_bank, write_package, verify_package
        output=self.root/"out"
        built,report=build_bank(self.bank(),self.mapping,self.voices,self.root)
        write_package(output,built,"profileVersion='v1'\n",report)
        self.assertTrue(verify_package(output)["valid"])
        write_package(output,built,"profileVersion='v1'\n# updated\n",report)
        self.assertTrue(verify_package(output)["valid"])
        (output/"mod/sd/cs_main.bnk").write_bytes(b"broken")
        with self.assertRaisesRegex(ValueError,"modified"):
            verify_package(output)

    def test_wwise_hash_known_init_bank_id(self):
        from nuv.build import event_hash
        self.assertEqual(event_hash("Init"),1355168291)

    def test_refuses_bank_with_changed_source_digest(self):
        from nuv.build import build_bank
        mapping=deepcopy(self.mapping)
        mapping["banks"]={"sd/cs_main.bnk":"0"*64}
        with self.assertRaisesRegex(ValueError,"source bank"):
            build_bank(self.bank(),mapping,self.voices,self.root)

    def test_windows_temporary_rename_denial_is_retried(self):
        from unittest.mock import patch
        from nuv.build import build_bank, write_package, verify_package
        output=self.root/"out"
        built,report=build_bank(self.bank(),self.mapping,self.voices,self.root)
        original=Path.rename
        calls=[]
        def rename(path,target):
            calls.append((path,target))
            if len(calls)==1:
                raise PermissionError(13,"temporary directory sharing violation")
            return original(path,target)
        with patch.object(Path,"rename",rename):
            write_package(output,built,"profileVersion='v1'\n",report)
        self.assertTrue(verify_package(output)["valid"])
        self.assertEqual(len(calls),2)

    def test_failed_publish_restores_old_package(self):
        from unittest.mock import patch
        from nuv.build import build_bank, write_package, verify_package
        output=self.root/"out"
        built,report=build_bank(self.bank(),self.mapping,self.voices,self.root)
        write_package(output,built,"old profile\n",report)
        original=Path.rename
        def rename(path,target):
            if path.name=="prepared":
                raise PermissionError(13,"publishing denied")
            return original(path,target)
        with patch.object(Path,"rename",rename), patch("nuv.build.time.sleep"):
            with self.assertRaises(PermissionError):
                write_package(output,built,"new profile\n",report)
        self.assertTrue(verify_package(output)["valid"])
        self.assertEqual((output/"UltimateVoices.me3").read_text(),"old profile\n")

    def test_failed_publish_and_restore_preserve_a_recoverable_old_package(self):
        from unittest.mock import patch
        from nuv.build import build_bank, write_package, verify_package
        output=self.root/"out"
        built,report=build_bank(self.bank(),self.mapping,self.voices,self.root)
        write_package(output,built,"old profile\n",report)
        original=Path.rename
        def rename(path,target):
            if path==output:
                return original(path,target)
            raise PermissionError(13,"both publish and restore denied")
        with patch.object(Path,"rename",rename), patch("nuv.build.time.sleep"):
            with self.assertRaises(ValueError):
                write_package(output,built,"new profile\n",report)
        surviving=list(self.root.rglob("cs_main.bnk"))
        self.assertEqual(len(surviving),1,"old bank must survive temporary-directory cleanup")
        backup=surviving[0].parents[2]
        self.assertTrue(verify_package(backup)["valid"])
        self.assertEqual((backup/"UltimateVoices.me3").read_text(),"old profile\n")
