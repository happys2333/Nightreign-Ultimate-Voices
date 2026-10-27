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
        for command in ("build","inspect","verify","uninstall"):
            self.assertIn(command,result.stdout)

    def test_missing_game_exits_cleanly_and_creates_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            result=self.run_cli("build","--game-dir",str(root/"missing"),"--output",str(root/"output"))
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn("Traceback",result.stderr)
            self.assertIn("nightreign.exe",result.stderr)
            self.assertFalse((root/"output").exists())

    def test_verify_rejects_arbitrary_directory_without_deleting_anything(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            keep=root/"keep.txt"
            keep.write_text("unchanged")
            result=self.run_cli("uninstall",str(root))
            self.assertNotEqual(result.returncode,0)
            self.assertIn("manifest",result.stderr)
            self.assertEqual(keep.read_text(),"unchanged")
