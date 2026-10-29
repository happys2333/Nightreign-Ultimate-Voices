"""Assemble existing runtime resources, without mutating either working mod."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from nuv.build import verify_package

SOURCES={
    'Native':'610f553520e5127da7366fe6c619683acac11b7aee6f6b2450b8186af0b573e1',
    'MMV-Addon':'0eafca3631ddbbf3b2ec67edb49068bdc4ebcf5e4d48b2b1720a0a1c2921be69',
}
sha=lambda data:hashlib.sha256(data).hexdigest()

def assemble(variant,built):
    verify_package(built)
    report=json.loads((built/'build-report.json').read_text(encoding='utf-8'))
    assert report['game_version']=='1.3.3.0'
    assert report['animation']['source_sha256']==SOURCES[variant], 'Wrong animation base for runtime variant'
    assert report['runtime']=={'processes':0,'dlls':0,'polling':False,'network_messages':0}
    assert len(report['banks'])==10 and report['loose_media_files']==11
    assert report['event_registration']['registered_events']==3
    assert report['animation']['inserted_event_count']==4
    assert all(op['event_type']==129 for op in report['animation']['operations'])
    manifest=json.loads((built/'.nuv-manifest.json').read_text(encoding='utf-8'))
    resources={}
    for name,digest in manifest['files'].items():
        if not name.startswith('mod/'):continue
        path=PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts
        value=(built/name).read_bytes();assert sha(value)==digest
        resources[name]=value
    expected={'mod/chr/c0000.anibnd.dcx','mod/sound/eventinfo.eib','mod/sound/soundbanksinfo.mobnkinfo'}
    expected.update(f'mod/sd/hero{n:02d}.bnk' for n in range(1,11))
    assert len(resources)==24 and expected.issubset(resources)
    assert len([p for p in resources if p.startswith('mod/sd/wem/') and p.endswith('.wem')])==11
    templates=ROOT/'release/overwatch'
    files=dict(resources)
    flavor='Native' if variant=='Native' else 'MMV'
    for language in ['zh-CN','en']:
        files[f'README.{language}.md']=(templates/f'README-{flavor}.{language}.md').read_bytes()
    files['CREDITS.txt']=(templates/'CREDITS.txt').read_bytes()
    files['LICENSE']=(ROOT/'LICENSE').read_bytes()
    if variant=='Native':
        for name in ['Launch.cmd','Launch-Seamless.cmd','UltimateVoices.me3','UltimateVoices-Seamless.me3']:
            files[name]=(templates/name).read_bytes()
        files['SeamlessCoop/README.txt']=b'Copy your own complete SeamlessCoop folder here if using the bundled co-op profile. No nrsc.dll is included.\n'
    else:
        files['ME3-PACKAGE.txt']=(templates/'ME3-PACKAGE.txt').read_bytes()
    public={
        'name':'Nightreign x Overwatch Ultimate Voices','version':'0.1.0','variant':variant,
        'stage':'Beta runtime candidate','game_file_version':'1.3.3.0',
        'audio_language':'zhCN','characters':10,'voice_mounts':11,
        'animation_source_sha256':report['animation']['source_sha256'],
        'animation_sha256':report['animation']['output_sha256'],
        'runtime':report['runtime'],'functional_baseline':'9b723ad',
        'prepared':'2026-10-29','public_upload_performed':False,
        'gameplay_feedback':'MMV variant: local tester reported no issues observed on 2026-10-28. Native variant not separately game-tested.',
        'mmv_derived_animation_included':variant=='MMV-Addon',
    }
    files['RELEASE.json']=json.dumps(public,ensure_ascii=False,indent=2).encode('utf-8')
    for name,data in files.items():
        assert Path(name).suffix.lower() not in {'.dll','.exe','.co2','.sl2','.pdb','.zip'}
        if Path(name).suffix.lower() in {'.txt','.md','.cmd','.me3','.json'}:
            text=data.decode('utf-8-sig')
            assert not any(s in text for s in ['D:\\codeWork','D:/codeWork','C:\\Users\\happy','C:/Users/happy'])
    files['SHA256SUMS.txt']=''.join(f'{sha(data)}  {name}\n' for name,data in sorted(files.items())).encode()
    output=ROOT/'dist/nexus';output.mkdir(parents=True,exist_ok=True)
    archive=output/f'Nightreign-Overwatch-Voices-0.1.0-{variant}.zip'
    prefix='UltimateVoices-Overwatch/' if variant=='Native' else 'UltimateVoices-MMV/'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(prefix+name,(2026,10,29,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)
        for name,data in files.items():assert z.read(prefix+name)==data
    archive.with_suffix('.zip.sha256').write_text(f'{sha(archive.read_bytes())}  {archive.name}\n',encoding='ascii')
    result={'variant':variant,'archive':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive.read_bytes()),'files':len(files),'resources':{name:sha(data) for name,data in resources.items()},'public_release_metadata':public}
    receipt=ROOT/'local/overwatch-release';receipt.mkdir(parents=True,exist_ok=True)
    (receipt/f'{variant}-archive-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['resources','public_release_metadata']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant',required=True,choices=SOURCES)
    parser.add_argument('--built',required=True,type=Path)
    args=parser.parse_args()
    assemble(args.variant,args.built.resolve())
