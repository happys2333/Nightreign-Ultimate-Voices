"""Package the ten editable default clips separately from the runtime mod."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from nuv.audio import pcm_wem
from nuv.bank import Bank

def assemble(source, built):
    report = json.loads((built / 'build-report.json').read_text(encoding='utf-8'))
    files = {}
    checked = 0
    characters = set()
    for resource, detail in report['banks'].items():
        bank = Bank.parse((built / 'mod' / resource).read_bytes())
        for character in detail['characters']:
            identifier = character['id']
            assert identifier not in characters
            characters.add(identifier)
            audio = source / (identifier + '.wav')
            wem = pcm_wem(audio, gain_db=character['gain_db'], normalize=character['normalize'])
            for event in character['events']:
                assert wem == bank.media_bytes(event['media_id']), identifier
                checked += 1
            files['voices/' + audio.name] = audio.read_bytes()
    assert len(characters) == 10 and checked == 11
    files['CUSTOM-AUDIO.md'] = (ROOT / 'docs/CUSTOM-AUDIO.md').read_bytes()
    files['CREDITS.txt'] = (ROOT / 'release/overwatch/CREDITS.txt').read_bytes()
    files['README.txt'] = ('Editable default WAVs, not a standalone mod. Copy voices/ into the Build Toolkit root.\n'
                         '默认可编辑 WAV，不是独立模组。把 voices/ 复制到 Build Toolkit 根目录。\n'
                         'Read CUSTOM-AUDIO.md for bilingual replacement and rebuild instructions.\n').encode('utf-8')
    digest = lambda data: hashlib.sha256(data).hexdigest()
    files['SHA256SUMS.txt'] = ''.join(f'{digest(data)}  {name}\n' for name,data in sorted(files.items())).encode()
    output = ROOT / 'dist/nexus/Nightreign-Overwatch-Voices-0.1.0-Audio-Sources.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = 'Nightreign-Overwatch-Audio-Sources/'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info = zipfile.ZipInfo(prefix + name, (2026,11,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        for name,data in files.items():
            assert z.read(prefix + name) == data
    checksum = digest(output.read_bytes())
    output.with_suffix('.zip.sha256').write_text(f'{checksum}  {output.name}\n', encoding='ascii')
    print(json.dumps({'archive':output.name,'bytes':output.stat().st_size,'sha256':checksum,
                      'characters':len(characters),'runtime_media_matches':checked}, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--built', required=True, type=Path)
    args = parser.parse_args()
    assemble(args.source.resolve(), args.built.resolve())
