"""Validate the module against a real Palworld v1.0.5.102999 REST response."""

import json
from pathlib import Path
import re
import unittest

import yaml


class PalworldFrameRate(unittest.TestCase):
    def test_live_frame_rate_declaration(self):
        root = Path(__file__).resolve().parent / "palworld"
        template = yaml.safe_load((root / "template.yaml").read_text())
        metrics = template["spec"]["capabilities"]["status"]["metrics"]
        metric, = [value for value in metrics if value["id"] == "server-fps"]
        self.assertEqual(metric["command"], "metrics")
        self.assertEqual(metric["performance"], {"signal": "frame_rate", "unit": "per_second"})
        pattern = re.compile(metric["regex"])
        raw = (root / "samples/metrics.json").read_text()
        self.assertEqual(int(pattern.search(raw)["value"]), json.loads(raw)["serverfps"])
        self.assertEqual(pattern.search('{"serverfps":0}')["value"], "0")
        for payload in ({}, {"serverfpsaverage": 60}, {"serverfps": None},
                        {"serverfps": -1}, {"serverfps": 0.5}, {"serverfps": "57"}):
            with self.subTest(payload=payload):
                self.assertIsNone(pattern.search(json.dumps(payload)))


if __name__ == "__main__":
    unittest.main()
