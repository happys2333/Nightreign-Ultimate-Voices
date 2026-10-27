import tempfile
import tomllib
import unittest
from pathlib import Path


class ProfileTests(unittest.TestCase):
    def test_clone_keeps_seamless_and_overlays_in_original_order(self):
        from nuv.profile import create_profile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "game" / "coop.me3"
            source.parent.mkdir()
            text = '''profileVersion = "v1"
savefile = "NR0000.co2"
start_online = false
[[supports]]
game = "nightreign"
[[natives]]
path = "./mods/SeamlessCoop/nrsc.dll"
load_early = true
[[packages]]
id = "MapMod"
path = "./mods/maps"
[[packages]]
id = "Translation"
path = "./mods/cn"
load_after = [{id="MapMod", optional=false}]
'''
            source.write_text(text)
            result = create_profile(source, root / "output" / "mod")
            parsed = tomllib.loads(result)
            self.assertFalse(parsed["start_online"])
            self.assertEqual(parsed["savefile"], "NR0000.co2")
            self.assertEqual(parsed["natives"][0]["path"], (source.parent / "mods/SeamlessCoop/nrsc.dll").as_posix())
            self.assertEqual(parsed["packages"][0]["id"], "MapMod")
            self.assertEqual(parsed["packages"][-1]["load_after"], [{"id":"MapMod","optional":False},{"id":"Translation","optional":False}])
            self.assertEqual(source.read_text(), text)

    def test_online_or_foreign_game_profile_is_rejected(self):
        from nuv.profile import create_profile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for text in ['start_online=true\n[[supports]]\ngame="nightreign"', 'start_online=false\n[[supports]]\ngame="eldenring"']:
                source = root / "wrong.me3"
                source.write_text(text)
                with self.assertRaises(ValueError):
                    create_profile(source, root / "mod")

    def test_inherited_profiles_fail_with_actionable_message(self):
        from nuv.profile import create_profile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "inherit.me3"
            source.write_text('profileVersion="v1"\nstart_online=false\nincludes=["other.me3"]\n[[supports]]\ngame="nightreign"')
            with self.assertRaisesRegex(ValueError, "includes"):
                create_profile(source, root / "mod")

    def test_effective_bank_respects_load_after_and_rejects_cycles(self):
        from nuv.profile import effective_packages
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "coop.me3"
            source.write_text('''[[packages]]
id="Patch"
path="patch"
load_after=[{id="Base"}]
[[packages]]
id="Base"
path="base"
''')
            self.assertEqual([p.name for p in effective_packages(source)], ["base","patch"])
            source.write_text('''[[packages]]
id="A"
path="a"
load_after=[{id="B"}]
[[packages]]
id="B"
path="b"
load_after=[{id="A"}]
''')
            with self.assertRaisesRegex(ValueError, "cycle"):
                effective_packages(source)
