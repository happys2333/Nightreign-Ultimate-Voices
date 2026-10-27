"""Command-line entry point. Everything exits before the game starts."""
import argparse
import json
from pathlib import Path
import sys
import time

from .build import MAX_ADDED_MEDIA, build_bank, remove_package, verify_package, write_package
from .bank import Bank
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
            "loose_media_files":0,"loose_media_bytes":0,
            "media_delivery":["embedded-bank","loose-prepare-event"],
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
        # PrepareEvent may request in-memory media by file ID even when a bank
        # includes it. ME3 supports sd/wem/<first two digits>/<id>.wem. Keep an
        # identical local copy so both LoadBank and preparation can find audio.
        parsed=Bank.parse(built)
        for character_detail in detail["characters"]:
            for event in character_detail["events"]:
                media_id=event["media_id"]
                resource=f"sd/wem/{str(media_id)[:2]}/{media_id}.wem"
                media=parsed.media_bytes(media_id)
                if resource in banks:
                    if banks[resource]!=media:
                        raise ValueError("Generated voice media ID collision across banks")
                    continue
                banks[resource]=media
                report["loose_media_files"]+=1
                report["loose_media_bytes"]+=len(media)
    report["build_seconds"]=round(time.perf_counter()-started,3)
    write_package(output,banks,profile_text,report)
    return {"output":str(output),"profile":str(output/"UltimateVoices.me3"),"banks":len(report["banks"]),
            "loose_media_files":report["loose_media_files"],
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
    extract=sub.add_parser("ow-extract",help="使用 DataTool 离线提取指定 OW 英雄语音")
    extract.add_argument("--overwatch-dir",required=True,help="本机守望先锋安装根目录")
    extract.add_argument("--datatool",default=str(ROOT/".tools/owlib-source/DataTool/bin/Release/net10.0/DataTool.exe"))
    extract.add_argument("--manifest",default=str(ROOT/"config/overwatch.json"))
    extract.add_argument("--output",default=str(ROOT/"local/overwatch/pinned"))
    importing=sub.add_parser("ow-import",help="导入审核后的 OW 敌我大招语音并可选构建原生声库")
    importing.add_argument("--source",default=str(ROOT/"local/overwatch/pinned"))
    importing.add_argument("--manifest",default=str(ROOT/"config/overwatch.json"))
    importing.add_argument("--decoder",default=str(ROOT/".tools/vgmstream/vgmstream-cli.exe"))
    importing.add_argument("--output",default=str(ROOT/"local/overwatch/imported"))
    importing.add_argument("--build",action="store_true",help="导入成功后构建 Nightreign 模组")
    importing.add_argument("--game-dir",help="Nightreign Game 目录；省略则检测 Steam")
    importing.add_argument("--base-profile",help="原有无缝联机 .me3 配置")
    importing.add_argument("--package-output",default=str(ROOT/"dist/UltimateVoices-Overwatch"))
    args=parser.parse_args(argv)
    try:
        if args.command=="inspect":
            game=find_game(args.game_dir)
            result={"game_directory":str(game),"game_version":game_version(game),"profiles":[str(p) for p in game.glob("*.me3")]}
        elif args.command=="build":
            result=run_build(args)
        elif args.command=="verify":
            result=verify_package(Path(args.output))
        elif args.command=="ow-extract":
            from .overwatch import extract_heroes
            result=extract_heroes(Path(args.overwatch_dir),Path(args.datatool),Path(args.output),_json(Path(args.manifest)))
        elif args.command=="ow-import":
            from .overwatch import import_voices,vgmstream_decoder
            decode,identity=vgmstream_decoder(Path(args.decoder))
            result=import_voices(Path(args.source),_json(Path(args.manifest)),Path(args.output),decoder=decode,decoder_identity=identity)
            if args.build:
                result["package"]=run_build(argparse.Namespace(game_dir=args.game_dir,base_profile=args.base_profile,
                    voices=result["config"],output=args.package_output))
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
