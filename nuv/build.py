"""Offline voice-bank construction and owned, transactional output packages."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import time

from .audio import pcm_wem
from .bank import Bank

MAX_ADDED_MEDIA = 16 * 1024 * 1024
MANIFEST = ".nuv-manifest.json"
OWNER = "nightreign-ultimate-voices-v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def event_hash(name: str) -> int:
    value = 2166136261
    for byte in name.lower().encode("ascii"):
        value = ((value * 16777619) ^ byte) & 0xFFFFFFFF
    return value


def build_bank(source: bytes, mapping: dict, voices: dict, config_directory: Path) -> tuple[bytes, dict]:
    expected_source = mapping.get("banks", {}).get(mapping.get("bank"))
    if expected_source and digest(source) != expected_source:
        raise ValueError("Unsupported source bank changed by another mod or game update; use the verified native hero bank")
    bank = Bank.parse(source)
    characters = mapping["characters"]
    ids = [character["id"] for character in characters]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate character mapping")
    settings = voices.get("characters", {})
    unknown = set(settings) - set(ids)
    if unknown:
        raise ValueError(f"Unknown voice characters: {', '.join(sorted(unknown))}")
    report = {"source_sha256":digest(source), "bank_version":bank.version,
              "characters":[], "added_media_bytes":0,
              "runtime":{"processes":0,"dlls":0,"polling":False,"network_messages":0}}
    used_events = set()
    for character in characters:
        identifier = character["id"]
        entry = settings.get(identifier, {"enabled":False})
        enabled = entry.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"{identifier}: enabled must be true or false")
        if not enabled:
            continue
        if not entry.get("audio"):
            raise ValueError(f"{identifier}: specify an audio WAV path")
        audio_path = Path(entry["audio"]).expanduser()
        if not audio_path.is_absolute():
            audio_path = config_directory / audio_path
        gain = entry.get("gain_db", voices.get("gain_db", 0.0))
        normalize = entry.get("normalize", voices.get("normalize", True))
        wem = pcm_wem(audio_path, gain_db=gain, normalize=normalize)
        events = character.get("events", [])
        if not events:
            raise ValueError(f"{identifier}: no verified native ultimate event")
        detail = {"id":identifier,"name_zh":character.get("name_zh",identifier),
                  "audio":str(audio_path.resolve()), "gain_db":gain,
                  "normalize":normalize,"events":[]}
        for event_name in events:
            if not isinstance(event_name,str) or not event_name.startswith("Play_"):
                raise ValueError("Expected a native Play_ event name")
            eid = event_hash(event_name)
            if eid in used_events:
                raise ValueError(f"Duplicate event mapping: {event_name}")
            used_events.add(eid)
            original = bank.objects_by_id.get(eid)
            if original is None or original.kind != 4:
                raise ValueError(f"Native event missing: {event_name}")
            expected = mapping.get("event_fingerprints", {}).get(event_name)
            if expected and digest(original.payload) != expected:
                raise ValueError(f"Native event changed by another mod: {event_name}")
            if report["added_media_bytes"] + len(wem) > MAX_ADDED_MEDIA:
                raise ValueError("Added voice media exceeds the 16 MiB package budget")
            result = bank.add_voice(eid, f"nuv-v1:{identifier}:{event_name}", wem)
            result["name"] = event_name
            result["original_event_sha256"] = digest(original.payload)
            detail["events"].append(result)
            report["added_media_bytes"] += len(wem)
        report["characters"].append(detail)
    output = bank.to_bytes()
    verified = Bank.parse(output)
    baseline = Bank.parse(source)
    for original in baseline.objects:
        if original.id not in used_events and verified.objects_by_id.get(original.id) != original:
            raise ValueError("Generated bank changed an original HIRC object")
    for media_id in baseline.media_ids:
        if baseline.media_bytes(media_id) != verified.media_bytes(media_id):
            raise ValueError("Generated bank changed original audio media")
    untouched = lambda b: [c for c in b.chunks if c.tag not in (b"HIRC",b"DIDX",b"DATA",b"BKHD")]
    if untouched(baseline) != untouched(verified):
        raise ValueError("Generated bank changed an original unknown chunk")
    old_header = next(c.payload for c in baseline.chunks if c.tag == b"BKHD")
    new_header = next(c.payload for c in verified.chunks if c.tag == b"BKHD")
    padding = new_header[len(old_header):]
    if not new_header.startswith(old_header) or len(padding) >= max(1,baseline.alignment) or any(padding):
        raise ValueError("Generated bank changed its original bank header")
    for character in report["characters"]:
        for event in character["events"]:
            if verified.event_actions(event["event_id"]) != tuple(event["original_action_ids"]) + (event["action_id"],):
                raise ValueError("Generated bank action validation failed")
            if verified.media_bytes(event["media_id"]) != bank.media_bytes(event["media_id"]):
                raise ValueError("Generated bank media validation failed")
    report["output_sha256"] = digest(output)
    report["original_bytes"] = len(source)
    report["output_bytes"] = len(output)
    return output, report


def _relative(name: str) -> Path:
    p = PurePosixPath(name)
    if p.is_absolute() or not p.parts or any(part in ("..", ".") or ":" in part or "\\" in part for part in p.parts):
        raise ValueError("Invalid output manifest path")
    return Path(*p.parts)


def _guard_output(output: Path) -> Path:
    output = Path(output).absolute()
    if output.is_symlink() or output.is_junction() or output.resolve() == Path(output.anchor):
        raise ValueError("Output must be a dedicated normal directory")
    for parent in output.parents:
        if parent.is_symlink() or parent.is_junction():
            raise ValueError("Output ancestors cannot be symbolic links or junctions")
    return output.resolve()


def _files(root: Path) -> set[str]:
    found = set()
    for directory, subdirectories, files in os.walk(root, followlinks=False):
        for name in subdirectories + files:
            path = Path(directory) / name
            if path.is_symlink() or path.is_junction():
                raise ValueError("Package cannot contain symbolic links or junctions")
        found.update((Path(directory) / name).relative_to(root).as_posix() for name in files)
    return found


def verify_package(output: Path) -> dict:
    output = _guard_output(output)
    manifest_path = output / MANIFEST
    if not manifest_path.is_file() or manifest_path.stat().st_size > 1024 * 1024:
        raise ValueError("Output contains unowned files or no Ultimate Voices manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("owner") != OWNER or not isinstance(manifest.get("files"),dict):
        raise ValueError("Output is not owned by Ultimate Voices")
    expected = set(manifest["files"]) | {MANIFEST}
    if _files(output) != expected:
        raise ValueError("Output contains missing or unowned files; use a different output directory")
    for name, expected_digest in manifest["files"].items():
        path = output / _relative(name)
        if path.stat().st_size > 512 * 1024 * 1024 or digest(path.read_bytes()) != expected_digest:
            raise ValueError(f"Output file modified: {name}; preserve your changes and use a new output directory")
    return {"valid":True,"files":len(manifest["files"]),"owner":OWNER}


def write_package(output: Path, banks: bytes | dict[str, bytes], profile: str, report: dict) -> None:
    output = _guard_output(output)
    if output.exists():
        verify_package(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(banks,bytes):
        banks = {"sd/cs_main.bnk":banks}
    files = {("mod/" + name): data for name,data in banks.items()}
    files["UltimateVoices.me3"] = profile.encode("utf-8")
    files["build-report.json"] = (json.dumps(report,ensure_ascii=False,indent=2) + "\n").encode("utf-8")
    files["Launch.cmd"] = ("@echo off\r\nsetlocal\r\n"
        'where me3 >nul 2>nul\r\nif errorlevel 1 (\r\n'
        '  "%LOCALAPPDATA%\\Programs\\garyttierney\\me3\\bin\\me3.exe" launch -g nightreign -p "%~dp0UltimateVoices.me3"\r\n'
        ') else (\r\n  me3 launch -g nightreign -p "%~dp0UltimateVoices.me3"\r\n)\r\n'
        'if errorlevel 1 pause\r\n').encode("ascii")
    for name in files:
        _relative(name)
    manifest = {"owner":OWNER,"files":{name:digest(value) for name,value in files.items()}}
    with tempfile.TemporaryDirectory(prefix=".nuv-stage-",dir=output.parent) as stage_name:
        stage = Path(stage_name).resolve()
        if stage.parent != output.parent:
            raise ValueError("Staging directory escaped output parent")
        prepared = stage / "prepared"
        prepared.mkdir()
        for name, value in files.items():
            path = prepared / _relative(name)
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(value)
        (prepared / MANIFEST).write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        verify_package(prepared)
        # Keep the previous package outside automatic staging cleanup: Windows
        # may deny both publication and rollback while a file is being read.
        previous = output.with_name(f".{output.name}.nuv-backup-{stage.name.removeprefix('.nuv-stage-')}")
        if previous.exists():
            raise ValueError("Backup destination already exists")
        if output.exists():
            _rename(output,previous)
        try:
            _rename(prepared,output)
        except BaseException:
            if previous.exists():
                try:
                    _rename(previous,output)
                except OSError:
                    raise ValueError(f"Could not restore output; previous package preserved at {previous}") from None
            raise
        if previous.exists():
            remove_package(previous)


def _rename(source: Path, target: Path) -> None:
    # Real Windows builds exhibited intermittent directory sharing denials.
    # Retry only PermissionError, without replacing an unexpected destination.
    for attempt in range(6):
        try:
            source.rename(target)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.05 * (attempt + 1))


def remove_package(output: Path) -> None:
    output = _guard_output(output)
    verify_package(output)
    manifest = json.loads((output / MANIFEST).read_text(encoding="utf-8"))
    for name in manifest["files"]:
        (output / _relative(name)).unlink()
    (output / MANIFEST).unlink()
    directories = sorted((p for p in output.rglob("*") if p.is_dir()),key=lambda p:len(p.parts),reverse=True)
    for directory in directories:
        directory.rmdir()
    output.rmdir()
