from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import wave


class OverwatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.source=self.root/"source"
        self.source.mkdir()
        self.relative="HeroVoice/半藏/Default/Ultimate/00000000A566.0B2-test.ogg"
        self.clip=self.source/self.relative
        self.clip.parent.mkdir(parents=True)
        self.clip.write_bytes(b"test compressed local audio")
        self.preset={"schema":1,"overwatch_build":"2.25.0.1.154504N","language":"zhCN","gain_db":-6,
            "roles":[{"nightreign":"ironeye","hero":"Hanzo","hero_zh":"半藏","hero_id":"5","audience":"enemy",
                      "clip":{"hero_id":"5","audience":"enemy","resource_guid":"00000000A566.0B2",
                              "relative_path":self.relative,"sha256":hashlib.sha256(self.clip.read_bytes()).hexdigest(),
                              "selection_evidence":"native ultimate enemy slot verified"}}]}

    def test_pinned_sources_reject_changed_bytes_wrong_hero_side_and_escape(self):
        from nuv.overwatch import selected_sources
        selected=selected_sources(self.source,self.preset)
        self.assertEqual(selected[0][1],self.clip.resolve())
        for field,value in (("hero_id","7"),("audience","friendly"),("relative_path","../escape.ogg"),("sha256","0"*64)):
            wrong=deepcopy(self.preset)
            wrong["roles"][0]["clip"][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                selected_sources(self.source,wrong)

    def test_import_writes_bounded_wavs_and_a_builder_compatible_config(self):
        from nuv.overwatch import import_voices
        def decoder(source,target):
            with wave.open(str(target),"wb") as output:
                output.setparams((1,2,48000,0,"NONE",""))
                output.writeframes(b"\1\0"*4800)
        result=import_voices(self.source,self.preset,self.root/"imports",decoder=decoder,decoder_identity="test-decoder-v1")
        config=json.loads(Path(result["config"]).read_text(encoding="utf-8"))
        self.assertEqual(config["gain_db"],-6)
        self.assertEqual(set(config["characters"]),{"ironeye"})
        audio=Path(result["config"]).parent/config["characters"]["ironeye"]["audio"]
        self.assertTrue(audio.is_file())
        self.assertEqual(import_voices(self.source,self.preset,self.root/"imports",decoder=decoder,decoder_identity="test-decoder-v1"),result)

    def test_decode_failure_never_publishes_partial_import(self):
        from nuv.overwatch import import_voices
        output=self.root/"imports"
        def fail(source,target):
            target.write_bytes(b"partial")
            raise ValueError("decoder failed")
        with self.assertRaisesRegex(ValueError,"decoder failed"):
            import_voices(self.source,self.preset,output,decoder=fail,decoder_identity="broken")
        self.assertFalse(any(output.glob("*/voices.json")))

    def test_import_rejects_invalid_decoded_wav_without_publication(self):
        from nuv.overwatch import import_voices
        def invalid(source,target):
            target.write_bytes(b"not a PCM WAV")
        output=self.root/"imports"
        with self.assertRaises(ValueError):
            import_voices(self.source,self.preset,output,decoder=invalid,decoder_identity="bad")
        self.assertFalse(any(output.glob("*/voices.json")))

    def test_datatool_success_code_cannot_hide_unsupported_version(self):
        from nuv.overwatch import check_extraction_log
        with self.assertRaisesRegex(ValueError,"not supported"):
            check_extraction_log(0,"[CASC] This version does not support this version.\nBuild version 154504 is not supported")
        with self.assertRaises(ValueError):
            check_extraction_log(0,"[CASC] Initializing...")
        check_extraction_log(0,"[CASC] Ready\n[Core] Execution finished")

    def test_ow_build_parser_reads_only_the_active_local_version(self):
        from nuv.overwatch import overwatch_version
        game=self.root/"Overwatch"
        game.mkdir()
        (game/".build.info").write_text("Branch!STRING:0|Active!DEC:1|Version!STRING:0\ncn|0|old\ncn|1|2.25.0.1.154504N\n")
        self.assertEqual(overwatch_version(game),"2.25.0.1.154504N")
