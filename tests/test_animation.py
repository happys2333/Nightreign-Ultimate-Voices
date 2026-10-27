import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class AnimationTests(unittest.TestCase):
    def test_plan_contains_only_enabled_roles_and_keeps_early_release_out(self):
        from nuv.animation import animation_plan
        source = b"source binder"
        mapping = {"animation": {"path":"chr/c0000.anibnd.dcx", "sources":{
            hashlib.sha256(source).hexdigest():"fixture"}}, "characters":[
            {"id":"guardian", "animation_triggers":[{"tae_id":2901,"animation_id":610000,"sound_id":900207000,"start_seconds":0,"end_seconds":1/30}]},
            {"id":"ironeye", "animation_triggers":[{"tae_id":2902,"animation_id":620000,"sound_id":900307000,"start_seconds":0,"end_seconds":1/30}]},
            {"id":"scholar", "animation_triggers":[{"tae_id":2908,"animation_id":680000,"sound_id":900907000,"start_seconds":3.3,"end_seconds":3.3+1/30}]}]}
        plan = animation_plan(source, mapping, {"ironeye","scholar"})
        self.assertEqual(plan["schema_version"], 1)
        self.assertEqual([op["animation_id"] for op in plan["operations"]], [620000,680000])
        self.assertEqual(plan["source_sha256"], hashlib.sha256(source).hexdigest())
        with self.assertRaisesRegex(ValueError, "animation.*changed"):
            animation_plan(b"different binder", mapping, {"ironeye"})
        self.assertIsNone(animation_plan(source, mapping, {"wylder"}))

    def test_resource_resolves_last_effective_package_before_loose_game(self):
        from nuv.game import Resources
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game, first, last = (root / name for name in ("game","first","last"))
            for folder, content in ((game,b"native loose"),(first,b"first mod"),(last,b"last mod")):
                target = folder / "chr/c0000.anibnd.dcx"
                target.parent.mkdir(parents=True)
                target.write_bytes(content)
            with patch("nuv.game.effective_packages",return_value=[first,last]):
                resources = Resources(game, root/"base.me3")
            value, origin = resources.read_animation_bundle()
            self.assertEqual(value, b"last mod")
            self.assertEqual(Path(origin), last/"chr/c0000.anibnd.dcx")
            resources.packages = []
            self.assertEqual(resources.read_animation_bundle()[0], b"native loose")
