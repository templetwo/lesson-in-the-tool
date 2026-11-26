"""Synthetic non-dry runner -> validated tally -> side comparison integration.

Uses only in-memory fake keys/transport and disposable candidate scratch. There
is deliberately no allow_fixture bypass in either tally, so the actual pipeline
boundary is exercised. None of these temporary outputs is experimental data.
"""
import fakes_first
import copy
import json
from pathlib import Path
import re
import unittest

from common import sha256_file, write_json
import runner
import tally
import side_compare
from tests import test_codex_configured_limit as fixture


class SideFlow(unittest.TestCase):
    setUp = fixture.ConfiguredLimitTests.setUp
    cfg = fixture.ConfiguredLimitTests.cfg

    def count(self, cfg, label):
        run_dir = runner.run(cfg, env=fixture.FAKE_ENV)
        tc = {"run_dir": run_dir, "sorters": copy.deepcopy(cfg["sorters"]),
              "groups": copy.deepcopy(cfg["groups"]), "repeats": cfg["repeats"],
              "real_callers": sorted(set(cfg["real_callers"].values())),
              "cut_points_by_size": {"6": {"settled_min": 5, "leaning_min": 4}}
              if len(cfg["sorters"]) > 1 else {},
              "bootstrap": {"seed": 20261127, "draws": 20, "level": 0.95}}
        report, judgment = tally.compute(tc)
        self.assertIs(report["inputs"]["allow_fixture"], False)
        self.assertNotIn("status", report)
        path = self.directory / (label + ".json")
        write_json(str(path), report)
        return path, report, judgment

    def test_fake_real_pipeline_counts_singleton_and_compares_all_seventeen(self):
        def replies(messages):
            labels = re.findall(r"(?m)^(L\d\d): ", messages[0]["content"])
            first = len(messages) == 1
            return "".join(("%s | main: check | second: none\n" if first else
                            "%s | Offline synthetic judgment sentence.\n") % label for label in labels)
        self.spies.reply = replies
        homes_file = str(fixture.BASE / "homes_real.json")
        reference_cfg = self.cfg(out_dir=str(self.directory / "reference-run"), homes_file=homes_file)
        reference_path, reference, _ = self.count(reference_cfg, "reference-tally")
        reference_hash = sha256_file(str(reference_path))

        side_cfg = self.cfg(out_dir=str(self.directory / "side-run"), repeats=3,
                            master_seed=20261127, output_token_limit=60000, homes_file=homes_file)
        name = "cloud-deepseek"
        side_cfg["sorters"] = [s for s in side_cfg["sorters"] if s["name"] == name]
        side_cfg["groups"] = {"cloud": {"min_providers": 1}}
        side_cfg["real_callers"] = {name: side_cfg["real_callers"][name]}
        side_path, side, judgment = self.count(side_cfg, "side-tally")
        self.assertEqual(side["groups"]["cloud"]["parse_failures"], {"count": 0, "of_replies": 3})
        self.assertEqual(side["groups"]["cloud"]["agreement"], {})
        self.assertIsNone(side["groups"]["cloud"]["class_counts"])
        self.assertTrue(judgment)
        self.assertEqual(len(self.spies.posts), 16 + 6)
        manifest = json.loads((Path(side_cfg["out_dir"]) / "manifest.json").read_text())
        self.assertEqual(manifest["call_budget"]["output_token_limit"], 60000)
        self.assertEqual(manifest["call_budget"]["planned"]["total"], 6)

        cfg = {"reference_tally": str(reference_path), "reference_sha256": reference_hash,
               "reference_group": "cloud", "side_tally": str(side_path), "side_group": "cloud",
               "side_sorter": name, "out_dir": str(self.directory / "comparison")}
        comparison = side_compare.run(cfg)
        self.assertEqual(comparison["counts"]["of"], 17)
        self.assertEqual(comparison["counts"], {"match": 17, "different": 0, "missing": 0, "of": 17})
        self.assertEqual(sum(comparison["counts"][k] for k in ("match", "different", "missing")), 17)
        self.assertEqual(comparison["match_fraction"]["denominator"], 17)
        self.assertEqual([r["line_number"] for r in comparison["rows"]], list(range(1, 18)))
        self.assertEqual(comparison["sources"]["reference"]["sha256"], reference_hash)
        self.assertEqual(comparison["sources"]["side"]["sha256"], sha256_file(str(side_path)))
        self.assertEqual(comparison["sources"]["side"]["reported_run_provenance"]["manifest_sha256"],
                         sha256_file(str(Path(side_cfg["out_dir"]) / "manifest.json")))
        self.assertEqual(sha256_file(str(reference_path)), reference_hash)
        self.assertEqual(json.loads((Path(cfg["out_dir"]) / "comparison.json").read_text()), comparison)


if __name__ == "__main__":
    unittest.main()
