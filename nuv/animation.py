"""Build-time plans for native animation sound events; no runtime helper."""
import json
from pathlib import Path
import subprocess
import tempfile

from .build import digest

SOULSFORMATS_REVISION = "9e1c36f54962f80c143e3c1fe8a709204aefacf9"


def animation_plan(source: bytes, mapping: dict, enabled_ids: set[str]) -> dict | None:
    operations = [dict(op) for character in mapping["characters"]
                  if character["id"] in enabled_ids
                  for op in character.get("animation_triggers", [])]
    if not operations:
        return None
    sha = digest(source)
    if sha not in mapping.get("animation", {}).get("sources", {}):
        raise ValueError("Effective animation bundle changed or is unsupported; refusing to overwrite another animation mod")
    return {"schema_version":1, "source_sha256":sha, "operations":operations}


def _helper(root: Path) -> Path:
    instruction = "Run scripts/Prepare-AnimationTools.ps1 to prepare the verified build-time animation helper"
    metadata = root/".tools/animation-tools.json"
    dll = root/".tools/tae-patcher/Nuv.TaePatcher.dll"
    if not metadata.is_file() or not dll.is_file() or metadata.stat().st_size > 65536:
        raise ValueError(instruction)
    info = json.loads(metadata.read_text(encoding="utf-8-sig"))
    if (info.get("schema_version") != 1 or info.get("helper_format_version") != 1
            or info.get("soulsformats_revision") != SOULSFORMATS_REVISION):
        raise ValueError(instruction)
    expected_sources = {"tools/tae/Nuv.TaePatcher.csproj", "tools/tae/Program.cs"}
    if set(info.get("helper_source_files", {})) != expected_sources:
        raise ValueError(instruction)
    for name, sha in info["helper_source_files"].items():
        if digest((root/name).read_bytes()) != sha:
            raise ValueError(instruction)
    for path, key in ((dll,"helper_dll_sha256"), (dll.parent/"SoulsFormats.dll","soulsformats_dll_sha256")):
        if not path.is_file() or digest(path.read_bytes()) != info.get(key):
            raise ValueError(instruction)
    return dll


def build_animation(source: bytes, mapping: dict, enabled_ids: set[str], game: Path) -> tuple[bytes, dict]:
    from .game import ROOT
    plan = animation_plan(source, mapping, enabled_ids)
    if plan is None:
        raise ValueError("No enabled animation timing operations")
    helper = _helper(ROOT)
    with tempfile.TemporaryDirectory(prefix="nuv-tae-") as temporary:
        stage = Path(temporary)
        input_path, output_path = stage/"source.anibnd.dcx", stage/"patched.anibnd.dcx"
        plan_path, report_path = stage/"plan.json", stage/"report.json"
        input_path.write_bytes(source)
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        try:
            result = subprocess.run(["dotnet",str(helper),"--input",str(input_path),"--output",str(output_path),
                "--plan",str(plan_path),"--game-dir",str(game),"--report",str(report_path)],
                capture_output=True,text=True,encoding="utf-8",timeout=120)
        except (subprocess.TimeoutExpired, OSError) as error:
            raise ValueError(f"Animation helper could not run: {error}") from None
        if result.returncode:
            raise ValueError(f"Animation helper refused the patch: {(result.stderr or result.stdout).strip()[:1000]}")
        if not output_path.is_file() or not report_path.is_file() or output_path.stat().st_size > 256*1024*1024:
            raise ValueError("Animation helper did not produce bounded output and an audit report")
        output = output_path.read_bytes()
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("source_sha256") != digest(source) or report.get("output_sha256") != digest(output):
            raise ValueError("Animation helper output hash validation failed")
        return output, report
