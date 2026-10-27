"""Offline, pinned local Overwatch voice extraction and import.

DataTool and vgmstream run only while preparing assets, before Nightreign.
An audited manifest identifies the hero, audience, resource GUID and bytes;
the importer never guesses an enemy/friendly version from a file's order.
"""
from collections.abc import Callable
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import uuid
import wave

from .audio import pcm_wem
from .build import _guard_output, _rename, digest

ROLES = frozenset({"wylder","guardian","ironeye","duchess","raider","revenant","recluse","executor","scholar","undertaker"})
MAX_SOURCE = 32 * 1024 * 1024


def overwatch_version(game: Path) -> str:
    info = Path(game) / ".build.info"
    if info.stat().st_size > 1024 * 1024:
        raise ValueError("Overwatch .build.info exceeds size limit")
    lines = info.read_text(encoding="utf-8-sig").splitlines()
    if not lines:
        raise ValueError("Empty Overwatch .build.info")
    columns = [column.split("!",1)[0] for column in lines[0].split("|")]
    active=[]
    for line in lines[1:]:
        row=dict(zip(columns,line.split("|")))
        if row.get("Active")=="1":
            active.append(row.get("Version",""))
    if len(active)!=1 or not active[0]:
        raise ValueError("Expected one active Overwatch build")
    return active[0]


def selected_sources(source_root: Path, preset: dict) -> list[tuple[dict,Path]]:
    root=Path(source_root).resolve(strict=True)
    if preset.get("schema")!=1 or preset.get("language")!="zhCN" or not preset.get("overwatch_build"):
        raise ValueError("Expected a versioned zhCN Overwatch selection manifest")
    roles=preset.get("roles",[])
    if not roles or len(roles)>len(ROLES):
        raise ValueError("Expected 1–10 selected Overwatch roles")
    seen=set()
    selected=[]
    for role in roles:
        identifier=role["nightreign"]
        clip=role["clip"]
        if identifier not in ROLES or identifier in seen:
            raise ValueError("Unknown or duplicate Nightreign role")
        seen.add(identifier)
        if not re.fullmatch(r"[0-9A-Fa-f]+",role["hero_id"]):
            raise ValueError("Invalid Overwatch hero ID")
        if role["audience"] not in ("enemy","friendly") or clip.get("audience")!=role["audience"]:
            raise ValueError(f"{identifier}: selected voice has the wrong audience")
        if clip.get("hero_id","").lower()!=role["hero_id"].lower():
            raise ValueError(f"{identifier}: selected voice belongs to a different hero")
        if not clip.get("selection_evidence"):
            raise ValueError(f"{identifier}: enemy/friendly selection needs recorded evidence")
        guid=clip.get("resource_guid","")
        if not re.fullmatch(r"[0-9A-Fa-f]{12}\.(?:0[Bb]2|03[Ff])",guid):
            raise ValueError(f"{identifier}: invalid Overwatch audio resource GUID")
        relative=PurePosixPath(clip["relative_path"])
        if relative.is_absolute() or ".." in relative.parts or any(":" in part or "\\" in part for part in relative.parts):
            raise ValueError("Overwatch audio path escapes extraction root")
        path=(root/Path(*relative.parts)).resolve(strict=True)
        if not path.is_relative_to(root) or path.suffix.lower() not in (".ogg",".wem",".wav"):
            raise ValueError("Invalid selected Overwatch audio path")
        if not path.name.lower().startswith(guid.lower()):
            raise ValueError("Selected filename does not match the pinned resource GUID")
        if path.stat().st_size>MAX_SOURCE:
            raise ValueError("Selected Overwatch audio exceeds 32 MiB")
        if digest(path.read_bytes())!=clip.get("sha256","").lower():
            raise ValueError(f"{identifier}: local Overwatch audio hash changed; re-audit the selected clip")
        selected.append((role,path))
    return selected


def check_extraction_log(returncode: int, log: str) -> None:
    lower=log.lower()
    if returncode or "not supported" in lower or "exception" in lower or "unable to load voice data" in lower:
        raise ValueError("DataTool extraction failed (possibly build not supported):\n"+log[-4000:])
    if "[casc] ready" not in lower or "execution finished" not in lower:
        raise ValueError("DataTool did not report a complete local extraction:\n"+log[-4000:])


def extract_heroes(game: Path, datatool: Path, output: Path, preset: dict) -> dict:
    game=Path(game).resolve(strict=True)
    tool=Path(datatool).resolve(strict=True)
    if overwatch_version(game)!=preset["overwatch_build"]:
        raise ValueError("Local Overwatch version differs from the audited voice manifest")
    output=_guard_output(output)
    if output==game or output in game.parents or game in output.parents:
        raise ValueError("Extraction output must be outside the Overwatch installation")
    if output.exists():
        selected_sources(output,preset)
        return {"source":str(output),"reused":True,"build":preset["overwatch_build"]}
    output.parent.mkdir(parents=True,exist_ok=True)
    log_directory=output.parent/"logs"
    log_directory.mkdir(exist_ok=True)
    log_path=log_directory/f"datatool-{uuid.uuid4().hex}.log"
    with tempfile.TemporaryDirectory(prefix=".ow-extract-",dir=output.parent) as temporary:
        staged=Path(temporary)/"extracted"
        hero_ids=list(dict.fromkeys(role["hero_id"] for role in preset["roles"]))
        resources=[]
        for role in preset["roles"]:
            guid=role["clip"]["resource_guid"]
            if not re.fullmatch(r"[0-9A-Fa-f]{12}\.(?:0[Bb]2|03[Ff])",guid):
                raise ValueError("Invalid pinned audio resource GUID")
            if role["clip"]["relative_path"]!=f"Pinned/{guid}.wem":
                raise ValueError("Expected an original pinned WEM resource path")
            resources.append(guid)
        command=[str(tool),str(game),"extract-nuv-audio",str(staged/"Pinned"),*resources,
                 "--language=zhCN","--speech-language=zhCN","--rcn","--online=false",
                 "--raw-sound=true"]
        with log_path.open("wb") as log:
            try:
                result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=1800,check=False)
            except subprocess.TimeoutExpired:
                raise ValueError(f"DataTool timed out; see {log_path}") from None
        if log_path.stat().st_size>32*1024*1024:
            raise ValueError(f"DataTool log exceeds size limit: {log_path}")
        check_extraction_log(result.returncode,log_path.read_text(encoding="utf-8",errors="replace"))
        selected_sources(staged,preset)
        metadata={"build":preset["overwatch_build"],"language":"zhCN","hero_ids":hero_ids,
                  "datatool_sha256":digest(tool.read_bytes()),"log":str(log_path)}
        (staged/".ow-extraction.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
        _rename(staged,output)
    return {"source":str(output),"reused":False,"build":preset["overwatch_build"],"log":str(log_path)}


def vgmstream_decoder(executable: Path) -> tuple[Callable[[Path,Path],None],str]:
    tool=Path(executable).resolve(strict=True)
    identity=digest(tool.read_bytes())
    def decode(source: Path,target: Path) -> None:
        try:
            result=subprocess.run([str(tool),"-i","-o",str(target),str(source)],
                                  capture_output=True,timeout=120,check=False)
        except subprocess.TimeoutExpired:
            raise ValueError(f"vgmstream timed out decoding {source.name}") from None
        if result.returncode or not target.is_file():
            raise ValueError("vgmstream decode failed: "+(result.stdout+result.stderr)[-3000:].decode("utf-8",errors="replace"))
    return decode,identity


def import_voices(source_root: Path,preset: dict,output: Path,*,
                  decoder: Callable[[Path,Path],None],decoder_identity: str) -> dict:
    selected=selected_sources(source_root,preset)
    output=_guard_output(output)
    source_root=Path(source_root).resolve()
    if output==source_root or output in source_root.parents:
        raise ValueError("Import output cannot replace its source extraction")
    identity={"manifest":preset,"decoder":decoder_identity,"import_pipeline":2}
    revision=digest(json.dumps(identity,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8"))[:20]
    destination=output/revision
    result={"config":str(destination/"voices.json"),"source_report":str(destination/"sources.json"),"characters":len(selected)}
    if destination.exists():
        if destination.is_symlink() or destination.is_junction():
            raise ValueError("Existing OW import cannot be a symbolic link or junction")
        marker=destination/".ow-import.json"
        if not marker.is_file() or marker.stat().st_size>1024*1024:
            raise ValueError("Existing OW import lacks its ownership manifest")
        records=json.loads(marker.read_text(encoding="utf-8"))
        expected={f"{role['nightreign']}.wav" for role,_ in selected}|{"voices.json","sources.json"}
        if records.get("revision")!=revision or set(records.get("files",{}))!=expected:
            raise ValueError("Existing OW import manifest changed")
        for name,sha in records["files"].items():
            file=destination/name
            if file.is_symlink() or file.is_junction() or file.stat().st_size>MAX_SOURCE or digest(file.read_bytes())!=sha:
                raise ValueError("Existing imported voice was modified; select a new output directory")
        return result
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ow-import-",dir=output) as temporary:
        prepared=Path(temporary)/"prepared"
        prepared.mkdir()
        config={"gain_db":preset.get("gain_db",0),
                "normalize":preset.get("normalize",True),"characters":{}}
        report={"overwatch_build":preset["overwatch_build"],"language":preset["language"],
                "decoder_sha256":decoder_identity,"clips":[]}
        total=0
        for role,source in selected:
            target=prepared/f"{role['nightreign']}.wav"
            decoder(source,target)
            wem=pcm_wem(target,gain_db=config["gain_db"],normalize=config["normalize"])
            total+=len(wem)
            if total>16*1024*1024:
                raise ValueError("Imported audio exceeds the 16 MiB media budget")
            with wave.open(str(target),"rb") as audio:
                duration=audio.getnframes()/audio.getframerate()
            config["characters"][role["nightreign"]]={"audio":target.name,"enabled":True}
            report["clips"].append({**role,"wav_sha256":digest(target.read_bytes()),"duration_seconds":round(duration,6)})
        (prepared/"voices.json").write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (prepared/"sources.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        records={"revision":revision,"files":{p.name:digest(p.read_bytes()) for p in prepared.iterdir()}}
        (prepared/".ow-import.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
        _rename(prepared,destination)
    return result
