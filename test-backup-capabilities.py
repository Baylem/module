"""Check the backup and manual save declarations for flush-only engines."""

from pathlib import Path
import unittest

import yaml


class BackupCapabilitiesTest(unittest.TestCase):
    def test_flush_only_games_offer_manual_save_and_clean_stop(self):
        for game, save, stop in (
            ("ark-survival-ascended", "SaveWorld", "DoExit"),
            ("project-zomboid", "save", "quit"),
        ):
            with self.subTest(game=game):
                template = Path(__file__).parent / game / "template.yaml"
                caps = yaml.safe_load(template.read_text(encoding="utf-8"))["spec"]["capabilities"]
                self.assertNotIn("quiesce", caps)
                self.assertEqual(caps["lifecycle"]["stop"], [save, stop])
                actions = {action["id"]: action["command"] for action in caps["actions"]}
                self.assertEqual(actions["save-world"], save)


if __name__ == "__main__":
    unittest.main()
