"""Command-line entry point. Everything exits before the game starts."""
import argparse
import json
from pathlib import Path
import sys
import time

from .build import MAX_ADDED_MEDIA, build_bank, remove_package, verify_package, write_package
from .game import ROOT, Resources, find_game, game_version
from .profile import create_profile


def _json(path: Path) -> dict:
    if path.stat().st_size > 1024 * 1024:
        raise ValueError(f"Configuration exceeds 1 MiB: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_build(args) -> dict:
    started=time.perf_counter()
    game=find_game(args.game_dir)
    mapping=_json(ROOT/"config/characters.json")
    version=game_version(game)
    if version != mapping["game_version"]:
        raise ValueError(f"Unsupported game version {version}; verified native event map requires {mapping['game_version']}")
    config_path=Path(args.voices).resolve()
    voices=_json(config_path)
    known={item["id"] for item in mapping["characters"]}
    unknown=set(voices.get("characters",{}))-known
    if unknown:
        raise ValueError(f"Unknown voice characters: {', '.join(sorted(unknown))}")
    profile=Path(args.base_profile).resolve() if args.base_profile else None
    output=Path(args.output).resolve()
    if output == ROOT or output == game or output in game.parents or game in output.parents:
        raise ValueError("Output must be a separate dedicated directory outside the game installation")
    profile_text=create_profile(profile,output/"mod")
    resources=Resources(game,profile)
    banks={}
    report={"game_version":version,"game_directory":str(game),"base_profile":str(profile) if profile else None,
            "mode":"existing-profile" if profile else "offline-solo", "banks":{},"added_media_bytes":0,
            "runtime":{"processes":0,"dlls":0,"polling":False,"network_messages":0},
            "validation":{"static_bank_structure":True,"in_game_playback":False,"mixed_install_coop":False,"remote_distance":False,"fps_benchmark":False}}
    grouped={}
    for character in mapping["characters"]:
        if voices.get("characters",{}).get(character["id"],{}).get("enabled",True) and character["id"] in voices.get("characters",{}):
            grouped.setdefault(character["bank"],[]).append(character)
    if not grouped:
        raise ValueError("Enable at least one character in the voices configuration")
    for bank_name,characters in grouped.items():
        source,origin=resources.read_bank(bank_name)
        partial_map={**mapping,"bank":bank_name,"characters":characters}
        partial_voices={**voices,"characters":{item["id"]:voices["characters"][item["id"]] for item in characters}}
        built,detail=build_bank(source,partial_map,partial_voices,config_path.parent)
        detail["source_path"]=origin
        report["added_media_bytes"]+=detail["added_media_bytes"]
        if report["added_media_bytes"]>MAX_ADDED_MEDIA:
            raise ValueError("All voices together exceed the 16 MiB added media budget")
        report["banks"][bank_name]=detail
        banks[bank_name]=built
    report["build_seconds"]=round(time.perf_counter()-started,3)
    write_package(output,banks,profile_text,report)
    return {"output":str(output),"profile":str(output/"UltimateVoices.me3"),"banks":len(banks),
            "characters":sum(len(bank["characters"]) for bank in report["banks"].values()),
            "added_media_bytes":report["added_media_bytes"],"build_seconds":report["build_seconds"]}


def main(argv=None) -> int:
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,"reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser=argparse.ArgumentParser(description="Nightreign 大招本地语音：离线生成原生声库，无常驻进程")
    sub=parser.add_subparsers(dest="command",required=True)
    inspect=sub.add_parser("inspect",help="查找本机游戏、版本和现有 ME3 配置")
    inspect.add_argument("--game-dir")
    build=sub.add_parser("build",help="生成角色语音模组和独立 ME3 配置")
    build.add_argument("--game-dir")
    build.add_argument("--base-profile",help="现有无缝联机 .me3 配置；省略则生成单机离线配置")
    build.add_argument("--voices",default=str(ROOT/"config/voices.json"))
    build.add_argument("--output",default=str(ROOT/"dist/UltimateVoices"))
    verify=sub.add_parser("verify",help="校验生成文件的拥有清单和完整性")
    verify.add_argument("output",nargs="?",default=str(ROOT/"dist/UltimateVoices"))
    uninstall=sub.add_parser("uninstall",help="仅删除本工具完整拥有的输出，拒绝删除用户文件")
    uninstall.add_argument("output",nargs="?",default=str(ROOT/"dist/UltimateVoices"))
    args=parser.parse_args(argv)
    try:
        if args.command=="inspect":
            game=find_game(args.game_dir)
            result={"game_directory":str(game),"game_version":game_version(game),"profiles":[str(p) for p in game.glob("*.me3")]}
        elif args.command=="build":
            result=run_build(args)
        elif args.command=="verify":
            result=verify_package(Path(args.output))
        else:
            remove_package(Path(args.output))
            result={"removed":str(Path(args.output).resolve())}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,KeyError,TypeError) as error:
        print(f"错误: {error}",file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
