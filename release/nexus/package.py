"""Assemble the Nexus source toolkit from an explicit allowlist, never dist/."""
import hashlib,json,subprocess,zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[2]
out=root/'dist/nexus';out.mkdir(parents=True,exist_ok=True)
receipt=root/'local/nexus-release';receipt.mkdir(parents=True,exist_ok=True)
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
files={}
for name in tracked:
    if not name:continue
    path=Path(name)
    if (name.startswith(('nuv/','tests/','config/')) or
        name in ['Build.cmd','LICENSE','pyproject.toml','uv.lock',
                 'scripts/Prepare-AnimationTools.ps1','scripts/Prepare-OverwatchTools.ps1',
                 'scripts/Generate-TestVoices.ps1','tools/tae/Program.cs',
                 'tools/tae/Nuv.TaePatcher.csproj','tools/tae/README.md',
                 'tools/tae/tests/Program.cs','tools/tae/tests/Fixture.csproj',
                 'tools/owlib/NuvPinnedSfx.cs','docs/retimed-callout-trigger.md']):
        files[name]=(root/path).read_bytes()
for name in ['README.en.md','README.zh-CN.md','OW-PRESET.md','THIRD_PARTY_NOTICES.md','CHANGELOG.md','START-HERE.txt']:
    files[name]=(root/'release/nexus'/name).read_bytes()
files['README.md']=files['README.en.md']
files['CUSTOM-AUDIO.md']=(root/'docs/CUSTOM-AUDIO.md').read_bytes()
files['voices/README.txt']=b'Place your own PCM16 WAV files here; see README.en.md or README.zh-CN.md.\nNo game media is included.\n'
files['RELEASE.json']=json.dumps({'name':'Nightreign Ultimate Voices - Local Build Toolkit','version':'0.1.0','stage':'Beta','functional_baseline':'9b723ad','prepared':'2026-10-28','game_file_version':'1.3.3.0','prebuilt_game_resources_included':False,'audio_included':False,'ai_code':'substantial generation; human-directed requirements and local testing','required_tools':['ME3','Git','uv','.NET 9 SDK'],'optional_ow_build':'2.25.0.1.154504N zhCN; requires .NET 10 SDK'},indent=2).encode()
allowed={'.py','.json','.pem','.cmd','.toml','.lock','.ps1','.cs','.csproj','.md','.txt',''}
for name,data in files.items():
    assert Path(name).suffix in allowed,name
    assert not any(part in ['local','.tools','.venv','.git','dist','bin','obj','__pycache__'] for part in Path(name).parts),name
    assert not any(x in data for x in [b'D:\\codeWork',b'D:/codeWork',b'C:\\Users\\happy',b'C:/Users/happy']),name
    data.decode('utf-8-sig')
files['SHA256SUMS.txt']=''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name,data in sorted(files.items())).encode()
archive=out/'Nightreign-Ultimate-Voices-0.1.0-Build-Toolkit.zip'
prefix='Nightreign-Ultimate-Voices-0.1.0/'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,data in sorted(files.items()):
        info=zipfile.ZipInfo(prefix+name,(2026,10,28,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16;z.writestr(info,data)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,data in files.items():assert z.read(prefix+name)==data
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(f'{sha}  {archive.name}\n',encoding='ascii')
report={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha,'file_count':len(files),'no_game_audio_or_binaries':True,'no_private_paths':True,'zip_crc_passed':True,'files':sorted(files)}
(receipt/'archive-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
