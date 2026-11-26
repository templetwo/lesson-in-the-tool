"""Fixture-only agreement-rule checks; no runner/adapters imported or real I/O.

Load selected tally functions through the AST so this module cannot activate the
real-caller path. CLI writes, clock, input loading and compute are all replaced.
"""
import argparse
import ast
from collections import Counter
from contextlib import redirect_stdout
from fractions import Fraction
import io
import json
import math
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, mock_open


NOTE = "Agreement statistics are not computed for a group of two, by rule."
SOURCE = Path(__file__).resolve().parents[1] / "tally.py"


def load_selected_functions():
    names = {"fleiss_kappa", "krippendorff_alpha_nominal", "percentile_interval",
             "bootstrap", "group_report", "main"}
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in functions} != names:
        raise AssertionError("the selected tally functions changed")
    namespace = dict(Counter=Counter, Fraction=Fraction, math=math, random=random,
                     argparse=argparse)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace


def fixture_group(namespace, size, name):
    members = ["fixture-%s-%d" % (name, i) for i in range(size)]
    lines = [1, 2, 3]
    cfg = {"cut_points_by_size": {"6": {"settled_min": 5, "leaning_min": 4}},
           "bootstrap": {"seed": 17, "draws": 40, "level": 0.95}}
    main = {s: {1: "tool", 2: "check", 3: "tool"} for s in members}
    second = {s: {1: "check", 2: None, 3: None} for s in members}
    raw_main = {s: {n: [main[s][n]] * 3 for n in lines} for s in members}
    raw_second = {s: {n: [second[s][n]] * 3 for n in lines} for s in members}
    table = {n: {"line_number": n, "home_main": main[members[0]][n],
                 "home_second": second[members[0]][n]} for n in lines}
    result = namespace["group_report"](cfg, name, members, lines, 3, raw_main,
                                       raw_second, main, second, [], {"tool", "check"}, table)
    result["turn2"] = {"sent": size * 3, "failed": 0, "not_sent": 0,
                       "of_replies": size * 3}
    return result


class AgreementRuleTests(unittest.TestCase):
    def setUp(self):
        self.namespace = load_selected_functions()

    def test_two_sorter_json_omits_statistics_but_keeps_descriptive_counts(self):
        # Round-trip the representation that write_json will serialize.
        group = json.loads(json.dumps(fixture_group(self.namespace, 2, "local")))
        self.assertEqual(group["agreement"], {})
        self.assertEqual(group.get("agreement_note"), NOTE)
        self.assertEqual(group["size"], 2)
        self.assertIsNone(group["class_counts"])
        self.assertEqual([row["count_text"] for row in group["per_line"]], ["2 of 2"] * 3)
        self.assertEqual(group["parse_failures"], {"count": 0, "of_replies": 6})
        self.assertEqual(group["second_homes"][0]["by_majority"]["sorters_with_second"], 2)
        self.assertEqual(group["house_table"]["group"], {"exact": 6, "overlap": 6, "of": 6})
        self.assertTrue(all(row["lines_no_majority"] == 0 for row in group["per_sorter"].values()))

    def test_two_sorter_rule_skips_computation_and_resampling_regardless_of_group_name(self):
        spies = {}
        for name in ("fleiss_kappa", "krippendorff_alpha_nominal", "bootstrap"):
            spies[name] = Mock(return_value=1.0 if name != "bootstrap" else {})
            self.namespace[name] = spies[name]
        fixture_group(self.namespace, 2, "unfamiliar-fixture-group")
        for name, spy in spies.items():
            with self.subTest(function=name):
                spy.assert_not_called()

    def test_cloud_and_other_larger_groups_keep_statistics_and_intervals(self):
        for size, name in ((6, "cloud"), (3, "unfamiliar-fixture-group")):
            with self.subTest(size=size, name=name):
                group = fixture_group(self.namespace, size, name)
                self.assertNotIn("agreement_note", group)
                self.assertEqual(set(group["agreement"]), {"fleiss_kappa", "krippendorff_alpha"})
                for entry in group["agreement"].values():
                    self.assertEqual(entry["value"], 1.0)
                    self.assertEqual(entry["bootstrap"]["interval"], [1.0, 1.0])
                    self.assertEqual(entry["bootstrap"]["draws"], 40)

    def test_cli_prints_local_explanation_and_counts_with_cloud_statistics_only(self):
        groups = {g: fixture_group(self.namespace, size, g)
                  for g, size in (("cloud", 6), ("local", 2))}
        report = {"status": "FIXTURE, NOT DATA", "inputs": {"callers": ["fixture"]}, "groups": groups}
        fake_os = SimpleNamespace(path=SimpleNamespace(join=lambda *parts: "/".join(parts)), makedirs=Mock())
        write_json = Mock()
        fake_open = mock_open()
        self.namespace.update(os=fake_os, open=fake_open, write_json=write_json,
                              load_json=Mock(return_value={"out_dir": "fixture-output-not-written"}),
                              compute=Mock(return_value=(report, "FIXTURE SENTENCES\n")),
                              clock=Mock(return_value="FIXTURE CLOCK"), Refuse=RuntimeError,
                              FIXTURE_MARK="FIXTURE, NOT DATA")
        stream = io.StringIO()
        with redirect_stdout(stream):
            result = self.namespace["main"](["--config", "fixture-config-not-read", "--allow-fixture"])
        self.assertEqual(result, 0)
        cloud_text, local_text = stream.getvalue().split("group local", 1)
        self.assertIn("fleiss_kappa: 1.0 interval [1.0, 1.0]", cloud_text)
        self.assertIn("krippendorff_alpha: 1.0 interval [1.0, 1.0]", cloud_text)
        self.assertIn(NOTE, local_text)
        self.assertNotIn("fleiss_kappa", local_text)
        self.assertNotIn("krippendorff_alpha", local_text)
        self.assertNotIn("interval", local_text)
        self.assertIn("2 of 2", local_text)
        self.assertIn("house table: exact 6 of 6, overlap 6 of 6", local_text)
        written_report = json.loads(json.dumps(write_json.call_args[0][1]))
        self.assertEqual(written_report["groups"]["local"]["agreement"], {})
        self.assertEqual(written_report["groups"]["local"]["agreement_note"], NOTE)
        fake_open.assert_called_once_with("fixture-output-not-written/judgment_sentences.txt", "w", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
