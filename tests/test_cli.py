import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,"-m","nuv",*args],capture_output=True,text=True,encoding="utf-8",env={**os.environ,"PYTHONUTF8":"1"})

    def test_help_exposes_build_inspect_verify_and_uninstall(self):
        result=self.run_cli("--help")
        self.assertEqual(result.returncode,0,result.stderr)
        for command in ("build","inspect","verify","uninstall","ow-extract","ow-import"):
            self.assertIn(command,result.stdout)

    def test_missing_game_exits_cleanly_and_creates_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            result=self.run_cli("build","--game-dir",str(root/"missing"),"--output",str(root/"output"))
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn("Traceback",result.stderr)
            self.assertIn("nightreign.exe",result.stderr)
            self.assertFalse((root/"output").exists())

    def test_build_exports_identical_loose_media_for_event_preparation(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from test_build import BuildTests
        from nuv.__main__ import run_build
        from nuv.bank import Bank
        fixture = BuildTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        mapping = fixture.mapping
        mapping["characters"][0]["bank"] = "sd/hero01.bnk"
        output = fixture.root/"out"
        args = SimpleNamespace(game_dir=None, voices=str(fixture.root/"voices.json"),
                               base_profile=None, output=str(output))
        with patch("nuv.__main__.find_game", return_value=fixture.root/"game"), \
             patch("nuv.__main__.game_version", return_value="1.3.3.0"), \
             patch("nuv.__main__._json", side_effect=[mapping, fixture.voices]), \
             patch("nuv.__main__.Resources") as resources:
            resources.return_value.read_bank.return_value = (fixture.bank(), "fixture")
            run_build(args)
        report = json.loads((output/"build-report.json").read_text(encoding="utf-8"))
        bank_report = report["banks"]["sd/hero01.bnk"]
        mid = bank_report["characters"][0]["events"][0]["media_id"]
        mirror = output/"mod"/"sd"/"wem"/str(mid)[:2]/f"{mid}.wem"
        self.assertTrue(mirror.is_file(), "PrepareEvent needs a loose WEM alongside embedded media")
        embedded = Bank.parse((output/"mod/sd/hero01.bnk").read_bytes()).media_bytes(mid)
        self.assertEqual(mirror.read_bytes(), embedded)
        self.assertEqual(report["loose_media_files"], 1)

    def test_verify_rejects_arbitrary_directory_without_deleting_anything(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            keep=root/"keep.txt"
            keep.write_text("unchanged")
            result=self.run_cli("uninstall",str(root))
            self.assertNotEqual(result.returncode,0)
            self.assertIn("manifest",result.stderr)
            self.assertEqual(keep.read_text(),"unchanged")
