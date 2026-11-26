"""Singleton descriptive tally through real validation, using saved FIXTURE files only.

All writes stay in this copy's scratch. No runner entry point, adapter, transport
or real-call switch is used; the CLI retains its real output containment check.
"""
import fakes_first

import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from common import Refuse, load_json, sha256_file, write_json
from fixture_runs import FIXTURE_SENTENCE, make_run
from reply_parser import parse_question_reply, parse_sort_reply
from runner import turn2_not_sent
import tally

SCRATCH = HERE / "scratch/singleton_tally_tests"
NAME = "fixture-deepseek"
CALLER = "fixture-deepseek-adapter"
HOMES = ["FIXTURE-A", "FIXTURE-B"]
NOTE = "Single-sorter group: descriptive counts only; classes and agreement statistics are not computed."
STOP = "sorter_output_limit_exceeded"
STOP_ERROR = "sorter stopped after reported output usage exceeded the effective call limit"
CHECK = {"status": "exceeded", "field": "completion_tokens", "reported_output_tokens": 60001, "limit": 60000}


def call(turn, cutoff=False):
    return {"dry_run": False, "caller": CALLER, "provider": "deepseek", "turn": turn,
            "complete": not cutoff, "stop": "length" if cutoff else "stop",
            "error": "FIXTURE incomplete" if cutoff else None,
            "failure_reason": "provider_incomplete" if cutoff else None}


def skip(turn):
    return {"dry_run": False, "caller": CALLER, "turn": turn, "sent": False, "complete": False,
            "error": STOP_ERROR, "failure_reason": STOP, "not_sent_reason": STOP}


def failed_first(row):
    parsed = parse_sort_reply(None, ["L01", "L02"], HOMES, dry_run=False)
    row.update(raw_reply=None, parse_ok=False, parse_errors=parsed["errors"], rows=[],
               turn2=turn2_not_sent(False))


class SingletonTallyTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="singleton-fixture-", dir=str(SCRATCH))
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sequence = 0
        self.statistics = []
        for name in ("fleiss_kappa", "krippendorff_alpha_nominal", "bootstrap"):
            patcher = mock.patch.object(tally, name, side_effect=AssertionError("singleton called " + name))
            self.statistics.append(patcher.start())
            self.addCleanup(patcher.stop)
            self.addCleanup(self.statistics[-1].assert_not_called)

    def fixture(self, assignments=None, turn2=None):
        self.sequence += 1
        assign = {(NAME, r): (assignments or [HOMES] * 3)[r - 1] for r in (1, 2, 3)}
        run_dir = make_run(str(self.root / str(self.sequence)), [(NAME, "side")], 3, HOMES, 2, assign,
                           providers={NAME: "deepseek"}, caller="by_sorter", result_callers={NAME: CALLER},
                           turn2=turn2)
        cfg = {"run_dir": run_dir, "sorters": [{"name": NAME, "group": "side", "provider": "deepseek"}],
               "groups": {"side": {"min_providers": 1}}, "repeats": 3, "cut_points_by_size": {},
               "bootstrap": {"seed": 20261127, "draws": 20, "level": 0.95}}
        return Path(run_dir), cfg

    def rewrite(self, run_dir, relative, mutate, rehash=True):
        path = run_dir / relative
        obj = load_json(str(path), "FIXTURE saved file")
        mutate(obj)
        write_json(str(path), obj)
        if rehash:
            manifest = load_json(str(run_dir / "manifest.json"), "FIXTURE manifest")
            for entry in manifest["files"]:
                if entry["path"] == relative:
                    entry["sha256"] = sha256_file(str(path))
            write_json(str(run_dir / "manifest.json"), manifest)

    def result(self, run_dir, repeat, mutate, rehash=True):
        self.rewrite(run_dir, "results/%s__r%d.json" % (NAME, repeat), mutate, rehash)

    def test_pipeline_and_cli_write_descriptive_counts_and_exact_judgment(self):
        run_dir, cfg = self.fixture([HOMES, HOMES, list(reversed(HOMES))])
        report, judgment = tally.compute(cfg, allow_fixture=True)
        group = report["groups"]["side"]
        self.assertEqual(report["status"], "FIXTURE, NOT DATA")
        self.assertEqual(group["agreement"], {})
        self.assertEqual(group["agreement_note"], NOTE)
        self.assertIsNone(group["cut_points"])
        self.assertIsNone(group["class_counts"])
        self.assertEqual([r["sorter_majority"][NAME] for r in group["per_line"]], HOMES)
        self.assertEqual([r["class"] for r in group["per_line"]], [None, None])
        self.assertEqual([r["count_text"] for r in group["per_line"]], ["1 of 1"] * 2)
        self.assertEqual(group["parse_failures"], {"count": 0, "of_replies": 3})
        self.assertIn(FIXTURE_SENTENCE % (1, NAME, 1), judgment)
        cfg["out_dir"] = str(self.root / "tally-output")
        config_path = self.root / "tally-config.json"
        write_json(str(config_path), cfg)
        output = io.StringIO()
        # Keep validation, output containment and serialization real; only the
        # nondeterministic clock is replaced with an explicit fixture value.
        with mock.patch.object(tally, "clock", return_value="FIXTURE CLOCK"), contextlib.redirect_stdout(output):
            self.assertEqual(tally.main(["--config", str(config_path), "--allow-fixture"]), 0)
        written = load_json(str(Path(cfg["out_dir"]) / "tally.json"), "FIXTURE tally")
        self.assertEqual(written["groups"], report["groups"])
        self.assertEqual((Path(cfg["out_dir"]) / "judgment_sentences.txt").read_text(), judgment)
        self.assertIn(NOTE, output.getvalue())
        self.assertIn("group side (1 sorters; cut points None)", output.getvalue())
        self.assertIn("1 of 1", output.getvalue())
        self.assertNotIn("fleiss_kappa:", output.getvalue())
        self.assertNotIn("krippendorff_alpha:", output.getvalue())
        self.assertNotIn("interval", output.getvalue())

    def test_two_failed_repeats_keep_three_in_denominator_and_limit_marker_separate(self):
        run_dir, cfg = self.fixture([None, None, HOMES])
        def cutoff(row):
            failed_first(row)
            row["calls"] = [call(1, cutoff=True)]
        self.result(run_dir, 1, cutoff)
        report, _ = tally.compute(cfg, allow_fixture=True)
        group = report["groups"]["side"]
        self.assertEqual(group["parse_failures"], {"count": 2, "of_replies": 3})
        self.assertEqual(group["turn2"], {"sent": 1, "failed": 0, "not_sent": 2, "of_replies": 3})
        self.assertEqual([r["sorter_majority"][NAME] for r in group["per_line"]], [None, None])
        self.assertEqual([r["count_text"] for r in group["per_line"]], ["0 of 1"] * 2)
        self.assertEqual(group["per_sorter"][NAME]["lines_no_majority"], 2)
        self.assertEqual(report["limit_endings_by_sorter"], [
            {"sorter": NAME, "group": "side", "message_1": 1, "message_2": 0, "sorts_not_sent_after_f": 0}])

    def test_question_limit_failure_preserves_first_homes(self):
        run_dir, cfg = self.fixture()
        before, _ = tally.compute(cfg, allow_fixture=True)
        def question_cutoff(row):
            row["calls"] = [call(1), call(2, cutoff=True)]
            parsed = parse_question_reply(None, ["L01", "L02"])
            row["turn2"].update(raw_reply=None, parse_ok=False, parse_errors=parsed["errors"], rows=[])
        self.result(run_dir, 1, question_cutoff)
        after, judgment = tally.compute(cfg, allow_fixture=True)
        for field in set(before["groups"]["side"]) - {"turn2"}:
            self.assertEqual(before["groups"]["side"][field], after["groups"]["side"][field], field)
        self.assertEqual(after["groups"]["side"]["turn2"],
                         {"sent": 3, "failed": 1, "not_sent": 0, "of_replies": 3})
        self.assertIn("question reply failed to parse; no sentence", judgment)
        self.assertEqual(after["limit_endings_by_sorter"][0]["message_2"], 1)

    def test_f_stop_preserves_first_answer_and_separates_unsent_sorts_from_cutoffs(self):
        run_dir, cfg = self.fixture()
        budget = {"output_token_limit": 60000, "per_sorter": {NAME: {
            "caller": CALLER, "planned": 6, "attempted": 1,
            "stop": {"reason": STOP, "usage_limit_check": copy.deepcopy(CHECK)}}}}
        def first_stop(row):
            first = call(1)
            first.update(usage_json=json.dumps({"completion_tokens": 60001}), usage_limit_check=copy.deepcopy(CHECK))
            row["calls"] = [first, skip(2)]
            row["call_budget"] = copy.deepcopy(budget)
            row["turn2"] = {"dry_run": False, "sent": False, "not_sent_reason": STOP,
                            "raw_reply": None, "parse_ok": False, "parse_errors": [], "rows": []}
        self.result(run_dir, 1, first_stop)
        def later_skip(row):
            failed_first(row)
            row["calls"] = [skip(1)]
            row["call_budget"] = copy.deepcopy(budget)
        for repeat in (2, 3):
            self.result(run_dir, repeat, later_skip)
        report, judgment = tally.compute(cfg, allow_fixture=True)
        group = report["groups"]["side"]
        self.assertEqual(group["parse_failures"], {"count": 2, "of_replies": 3})
        self.assertEqual(group["turn2"], {"sent": 0, "failed": 0, "not_sent": 3, "of_replies": 3})
        self.assertEqual([r["sorter_majority"][NAME] for r in group["per_line"]], [None, None])
        self.assertEqual(report["limit_endings_by_sorter"], [
            {"sorter": NAME, "group": "side", "message_1": 0, "message_2": 0, "sorts_not_sent_after_f": 2}])
        self.assertIn("repeat 1: (question not asked: " + STOP + ")", judgment)
        self.assertTrue(load_json(str(run_dir / ("results/%s__r1.json" % NAME)), "FIXTURE result")["parse_ok"])

    def test_singleton_thresholds_are_refused_even_when_size_one_is_not_present(self):
        _, cfg = self.fixture()
        for size in (1, 2):
            with self.subTest(group_size=size):
                candidate = copy.deepcopy(cfg)
                if size == 2:
                    candidate["sorters"].append({"name": "fixture-second", "group": "side", "provider": "fixture-other"})
                candidate["cut_points_by_size"] = {"1": {"settled_min": 1, "leaning_min": 1}}
                with self.assertRaisesRegex(Refuse, "cut points for size 1 are not allowed; single-sorter groups are descriptive only"):
                    tally.check_config(candidate)

    def test_existing_manifest_hash_reparse_and_caller_checks_still_apply(self):
        cases = {
            "hash": (lambda r: r.update(raw_reply="FIXTURE tampered"), False, "hash"),
            "reparse": (lambda r: r.update(raw_reply="FIXTURE tampered"), True, "fresh parse"),
            "caller": (lambda r: r.update(caller="fixture-other-adapter"), True, "caller"),
        }
        for name, (mutate, rehash, expected) in cases.items():
            with self.subTest(case=name):
                run_dir, cfg = self.fixture()
                tally.compute(cfg, allow_fixture=True)
                self.result(run_dir, 1, mutate, rehash)
                with self.assertRaisesRegex(Refuse, expected):
                    tally.compute(cfg, allow_fixture=True)
        run_dir, cfg = self.fixture()
        tally.compute(cfg, allow_fixture=True)
        manifest_path = run_dir / "manifest.json"
        manifest = load_json(str(manifest_path), "FIXTURE manifest")
        manifest["files"].append(dict(manifest["files"][0]))
        write_json(str(manifest_path), manifest)
        with self.assertRaisesRegex(Refuse, "twice|repeated"):
            tally.compute(cfg, allow_fixture=True)

    def test_provider_minimum_remains_enforced(self):
        _, cfg = self.fixture()
        cfg["groups"]["side"]["min_providers"] = 2
        with self.assertRaisesRegex(Refuse, "provider"):
            tally.check_config(cfg)


if __name__ == "__main__":
    unittest.main()
