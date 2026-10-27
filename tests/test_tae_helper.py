"""Build-time C# helper integration tests; no game writes or runtime hooks.

Run: python -m unittest discover -s tests -p test_tae_helper.py -v
Requires .NET SDK and prepared .tools/soulsformats. Set NUV_TAE_REAL_SOURCE and
NUV_TAE_GAME_DIR for the optional read-only MMV integration test.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tools/tae/bin/Release/net9.0/Nuv.TaePatcher.dll"
FIXTURE = ROOT / "tools/tae/tests/bin/Release/net9.0/Fixture.dll"
OPERATIONS = [
    dict(tae_id=2901, animation_id=610000, sound_id=900207000, start_seconds=0, end_seconds=1 / 30),
    dict(tae_id=2901, animation_id=615000, sound_id=900207000, start_seconds=0, end_seconds=1 / 30),
    dict(tae_id=2902, animation_id=620000, sound_id=900307000, start_seconds=0, end_seconds=1 / 30),
    dict(tae_id=2908, animation_id=680000, sound_id=900907000, start_seconds=3.3, end_seconds=3.3 + 1 / 30),
]


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)


class TaeHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".tools/soulsformats/SoulsFormats/SoulsFormats.csproj").exists():
            raise unittest.SkipTest("run scripts/Prepare-AnimationTools.ps1 first")
        for project in ("tools/tae/Nuv.TaePatcher.csproj", "tools/tae/tests/Fixture.csproj"):
            result = run("dotnet", "build", project, "-c", "Release", "--nologo", "-v", "quiet")
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)

    def setUp(self):
        scratch = ROOT / "local/timing-update/helper-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.input = self.directory / "input.anibnd"
        self.output = self.directory / "output.anibnd"
        self.report = self.directory / "report.json"
        self.plan_file = self.directory / "plan.json"
        self.game = self.directory / "game"
        self.game.mkdir()
        self.fixture("normal")

    def fixture(self, kind):
        result = run("dotnet", FIXTURE, "create", self.input, kind)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.source_hash = hashlib.sha256(self.input.read_bytes()).hexdigest()
        self.plan = dict(schema_version=1, source_sha256=self.source_hash, operations=copy.deepcopy(OPERATIONS))

    def invoke(self, **paths):
        self.plan_file.write_text(self.plan if isinstance(self.plan, str) else json.dumps(self.plan), encoding="utf-8")
        kwargs = dict(input=self.input, output=self.output, plan=self.plan_file, game_dir=self.game, report=self.report)
        kwargs.update(paths)
        arguments = [item for key, value in kwargs.items() for item in ("--" + key.replace("_", "-"), value)]
        return run("dotnet", HELPER, *arguments)

    def reject(self, code, **paths):
        result = self.invoke(**paths)
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("TAE_PATCH_ERROR " + code + ":", result.stderr)
        self.assertNotIn("\n   at ", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.report.exists())
        self.assertEqual(self.source_hash, hashlib.sha256(self.input.read_bytes()).hexdigest())
        return result

    def test_invalid_plan_schema_is_rejected_before_output(self):
        self.plan["schema_version"] = 2
        self.reject("PLAN_INVALID")

    def test_source_hash_mismatch_is_rejected_before_output(self):
        self.plan["source_sha256"] = "0" * 64
        self.reject("SOURCE_HASH")

    def test_missing_animation_is_rejected_before_output(self):
        self.plan["operations"][0]["animation_id"] = 999999
        self.reject("ANIMATION_COUNT")

    def test_missing_tae_is_rejected_before_output(self):
        self.plan["operations"][0]["tae_id"] = 9999
        self.reject("TAE_COUNT")

    def test_duplicate_plan_target_is_rejected_before_output(self):
        self.plan["operations"].append(copy.deepcopy(self.plan["operations"][0]))
        self.reject("PLAN_INVALID")

    def test_duplicate_animation_is_rejected_before_output(self):
        self.fixture("duplicate-animation")
        self.reject("ANIMATION_COUNT")

    def test_duplicate_tae_is_rejected_before_output(self):
        self.fixture("duplicate-tae")
        self.reject("TAE_COUNT")

    def test_sound_id_collision_is_rejected_before_output(self):
        self.fixture("collision")
        self.reject("SOUND_COLLISION")

    def test_invalid_numeric_values_and_unknown_fields_are_rejected(self):
        for field, value in (("start_seconds", -1), ("end_seconds", 121), ("start_seconds", 3.4), ("sound_id", 0), ("animation_id", 2**31), ("event_type", 129)):
            with self.subTest(field=field, value=value):
                self.plan["operations"] = copy.deepcopy(OPERATIONS)
                self.plan["operations"][3][field] = value
                self.reject("PLAN_INVALID")

    def test_operation_count_is_bounded(self):
        self.plan["operations"] = []
        self.reject("PLAN_INVALID")
        self.plan["operations"] = [dict(OPERATIONS[0], animation_id=i + 1) for i in range(65)]
        self.reject("PLAN_INVALID")

    def test_duplicate_json_fields_and_malformed_json_are_rejected(self):
        for value in ('{"schema_version":1,"schema_version":1}', '{', json.dumps(dict(self.plan, operations="wrong type")), json.dumps(dict(self.plan, schema_version=True))):
            with self.subTest(value=value):
                self.plan = value
                self.reject("PLAN_INVALID")

    def test_plan_file_size_is_bounded(self):
        self.plan = " " * (1024 * 1024 + 1)
        self.reject("PLAN_INVALID")

    def test_input_file_size_is_bounded(self):
        with self.input.open("wb") as stream:
            stream.truncate(256 * 1024 * 1024 + 1)
        result = self.invoke()
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("TAE_PATCH_ERROR SOURCE_SIZE:", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.report.exists())

    def test_existing_report_is_not_overwritten(self):
        self.report.write_bytes(b"keep report")
        result = self.invoke()
        self.assertEqual(2, result.returncode)
        self.assertIn("TAE_PATCH_ERROR PATH_UNSAFE:", result.stderr)
        self.assertEqual(b"keep report", self.report.read_bytes())
        self.assertFalse(self.output.exists())

    def test_report_cannot_equal_output(self):
        self.reject("PATH_UNSAFE", report=self.output)

    def test_sound_collision_in_a_later_sound_row_type_is_rejected(self):
        self.fixture("collision-134")
        self.reject("SOUND_COLLISION")

    def test_output_in_game_directory_is_rejected(self):
        self.reject("PATH_UNSAFE", output=self.game / "forbidden.anibnd")

    def test_report_in_game_directory_is_rejected(self):
        self.reject("PATH_UNSAFE", report=self.game / "forbidden.json")

    def test_windows_path_aliases_cannot_bypass_game_write_guard(self):
        for index, output in enumerate(("\\\\?\\" + str(self.game / "forbidden0.anibnd"), str(self.game) + ".\\forbidden1.anibnd", str(self.game) + " \\forbidden2.anibnd", "//?/" + str(self.game / "forbidden3.anibnd").replace("\\", "/"))):
            with self.subTest(output=output):
                self.report = self.directory / f"report{index}.json"
                self.reject("PATH_UNSAFE", output=output)

    def test_existing_output_is_not_overwritten(self):
        self.output.write_bytes(b"keep me")
        result = self.invoke()
        self.assertEqual(2, result.returncode)
        self.assertIn("TAE_PATCH_ERROR PATH_UNSAFE:", result.stderr)
        self.assertEqual(b"keep me", self.output.read_bytes())
        self.assertFalse(self.report.exists())

    def test_input_cannot_be_output_or_report(self):
        self.reject("PATH_UNSAFE", output=self.input)
        self.reject("PATH_UNSAFE", report=self.input)

    def test_junction_path_is_rejected(self):
        junction = self.directory / "junction"
        created = run("cmd", "/c", "mklink", "/J", junction, self.game)
        if created.returncode:
            self.skipTest("junction creation unavailable")
        self.addCleanup(lambda: junction.rmdir() if junction.exists() else None)
        self.reject("PATH_UNSAFE", output=junction / "forbidden.anibnd")

    def test_exactly_four_additions_preserve_every_original(self):
        result = self.invoke()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(self.output.exists(), "patch output was not created")
        self.assertTrue(self.report.exists(), "audit report was not created")
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(1, report["schema_version"])
        self.assertEqual(4, report["inserted_event_count"])
        self.assertEqual(3, report["changed_member_count"])
        self.assertTrue(report["all_original_events_headers_groups_unchanged"])
        self.assertTrue(report["all_other_binder_members_unchanged"])
        self.assertEqual(self.source_hash, report["source_sha256"])
        self.assertEqual(hashlib.sha256(self.output.read_bytes()).hexdigest(), report["output_sha256"])
        self.assertEqual(self.source_hash, hashlib.sha256(self.input.read_bytes()).hexdigest())
        audit = run("dotnet", FIXTURE, "audit", self.input, self.output, self.plan_file)
        self.assertEqual(0, audit.returncode, audit.stdout + audit.stderr)

    def test_preparation_publishes_pinned_metadata_and_source_digest(self):
        script = ROOT / "scripts/Prepare-AnimationTools.ps1"
        self.assertTrue(script.exists(), "animation bootstrap script is missing")
        result = run("pwsh", "-NoProfile", "-File", script)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        metadata = json.loads((ROOT / ".tools/animation-tools.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(1, metadata["schema_version"])
        self.assertEqual(1, metadata["helper_format_version"])
        self.assertEqual("9e1c36f54962f80c143e3c1fe8a709204aefacf9", metadata["soulsformats_revision"])
        manifest = ""
        for path, digest in sorted(metadata["helper_source_files"].items()):
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
            manifest += f"{path}:{digest}\n"
        self.assertEqual(hashlib.sha256(manifest.encode()).hexdigest(), metadata["helper_source_sha256"])
        for path, field in (("Nuv.TaePatcher.dll", "helper_dll_sha256"), ("SoulsFormats.dll", "soulsformats_dll_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / ".tools/tae-patcher" / path).read_bytes()).hexdigest(), metadata[field])

    def test_preparation_refuses_unexpected_checkout_without_reset(self):
        script = ROOT / "scripts/Prepare-AnimationTools.ps1"
        self.assertTrue(script.exists(), "animation bootstrap script is missing")
        tool_root = self.directory / "bad-tools"
        repo = tool_root / "soulsformats"
        repo.mkdir(parents=True)
        sentinel = repo / "keep.txt"
        sentinel.write_text("preserve my checkout", encoding="utf-8")
        result = run("pwsh", "-NoProfile", "-File", script, "-ToolRoot", tool_root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("without the expected Git repository", result.stderr)
        self.assertEqual("preserve my checkout", sentinel.read_text())
        self.assertFalse((tool_root / "animation-tools.json").exists())

    def test_preparation_supports_windows_powershell(self):
        result = run("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ROOT / "scripts/Prepare-AnimationTools.ps1")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    @unittest.skipUnless(os.getenv("NUV_TAE_REAL_SOURCE") and os.getenv("NUV_TAE_GAME_DIR"), "optional real MMV source integration")
    def test_real_mmv_exactly_four_additions(self):
        self.input = Path(os.environ["NUV_TAE_REAL_SOURCE"])
        self.game = Path(os.environ["NUV_TAE_GAME_DIR"])
        self.source_hash = hashlib.sha256(self.input.read_bytes()).hexdigest()
        self.plan["source_sha256"] = self.source_hash
        result = self.invoke()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        audit = run("dotnet", FIXTURE, "audit", self.input, self.output, self.plan_file, self.game)
        self.assertEqual(0, audit.returncode, audit.stdout + audit.stderr)
        data = json.loads(audit.stdout)
        self.assertEqual(623, data["member_count"])
        self.assertEqual(4, data["addition_count"])
        self.assertEqual(3, data["changed_member_count"])
        self.assertTrue(data["originals_restored_byte_identical"])


if __name__ == "__main__":
    unittest.main()
