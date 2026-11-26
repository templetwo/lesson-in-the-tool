"""F-rule tally regression fixtures; only the separate Test2 scratch is written.

No runner entry point, adapter call, environment switch, key, or transport is used.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from common import Refuse, load_json, sha256_file, write_json
from fixture_runs import make_run
from reply_parser import parse_sort_reply
from runner import turn2_not_sent
from tally import compute

SCRATCH = HERE.parents[1] / "test2_stale/scratch/codex_limits_round/tally"
STOP = "sorter_output_limit_exceeded"
ERROR = "sorter stopped after reported output usage exceeded the effective call limit"
SORTERS = [("F%d" % n, "cloud") for n in range(6)]
CALLERS = {s: "fixture-adapter-" + s for s, _ in SORTERS}
HOMES = ["FIXTURE-A", "FIXTURE-B"]
CHECK = {"status": "exceeded", "field": "output_tokens", "reported_output_tokens": 19001, "limit": 19000}


def skipped_call(caller, turn):
    return {"dry_run": False, "caller": caller, "turn": turn, "sent": False, "complete": False,
            "error": ERROR, "failure_reason": STOP, "not_sent_reason": STOP}


def stop_result(result):
    caller = result["caller"]
    result["calls"] = [
        {"dry_run": False, "caller": caller, "turn": 1, "complete": True, "error": None,
         "failure_reason": None, "usage_json": json.dumps({"output_tokens": 19001}),
         "usage_limit_check": copy.deepcopy(CHECK)}, skipped_call(caller, 2)]
    result["turn2"] = {"dry_run": False, "sent": False, "not_sent_reason": STOP,
                       "raw_reply": None, "parse_ok": False, "parse_errors": [], "rows": []}
    result["call_budget"] = {"output_token_limit": 19000, "per_sorter": {
        result["sorter"]: {"caller": caller, "planned": 6, "attempted": 2 * result["repeat"] - 1,
                           "stop": {"reason": STOP, "usage_limit_check": copy.deepcopy(CHECK)}}}}
    result["persistence_state"] = "complete"


def rewrite(run_dir, relative, mutate):
    path = Path(run_dir) / relative
    result = load_json(str(path), relative)
    mutate(result)
    write_json(str(path), result)
    manifest_path = Path(run_dir) / "manifest.json"
    manifest = load_json(str(manifest_path), "manifest")
    for entry in manifest["files"]:
        if entry["path"] == relative:
            entry["sha256"] = sha256_file(str(path))
    write_json(str(manifest_path), manifest)


class UsageStopTallyTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="usage-tally-fixture-", dir=str(SCRATCH))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sequence = 0

    def fixture(self):
        self.sequence += 1
        assign = {(s, r): HOMES for s, _ in SORTERS for r in (1, 2, 3)}
        return make_run(str(self.root / str(self.sequence)), SORTERS, 3, HOMES, 2, assign,
                        caller="by_sorter", result_callers=CALLERS)

    def tally(self, run_dir):
        cfg = {"run_dir": run_dir, "sorters": [
            {"name": s, "group": g, "provider": "fixture-provider-" + s} for s, g in SORTERS],
            "groups": {}, "repeats": 3,
            "cut_points_by_size": {"6": {"settled_min": 5, "leaning_min": 4}},
            "bootstrap": {"seed": 17, "draws": 20, "level": 0.95}}
        return compute(cfg, allow_fixture=True)

    def test_valid_first_answer_survives_proven_question_skip_without_sent_failure(self):
        run_dir = self.fixture()
        before, _ = self.tally(run_dir)
        rewrite(run_dir, "results/F0__r3.json", stop_result)
        after, sentences = self.tally(run_dir)
        self.assertEqual(after["status"], "FIXTURE, NOT DATA")
        self.assertEqual(after["groups"]["cloud"]["turn2"],
                         {"sent": 17, "failed": 0, "not_sent": 1, "of_replies": 18})
        for name in set(before["groups"]["cloud"]) - {"turn2"}:
            self.assertEqual(before["groups"]["cloud"][name], after["groups"]["cloud"][name], name)
        self.assertIn("F0 repeat 3: (question not asked: sorter_output_limit_exceeded)", sentences)
        self.assertNotIn("F0 repeat 3: (question reply failed to parse", sentences)
        saved = load_json(str(Path(run_dir) / "results/F0__r3.json"), "fixture result")
        self.assertEqual(saved["call_budget"]["per_sorter"]["F0"]["attempted"], 5)

    def test_later_skipped_sorts_are_missing_votes_and_questions_not_sent(self):
        run_dir = self.fixture()
        rewrite(run_dir, "results/F0__r1.json", stop_result)
        for repeat in (2, 3):
            def skip_first(result):
                stopped = dict(result)
                stop_result(stopped)
                result["call_budget"] = stopped["call_budget"]
                result["call_budget"]["per_sorter"]["F0"]["attempted"] = 1
                result["calls"] = [skipped_call(result["caller"], 1)]
                parsed = parse_sort_reply(None, ["L01", "L02"], HOMES, dry_run=False)
                result.update(raw_reply=None, parse_ok=False, parse_errors=parsed["errors"], rows=[],
                              turn2=turn2_not_sent(False), persistence_state="complete")
            rewrite(run_dir, "results/F0__r%d.json" % repeat, skip_first)
        report, _ = self.tally(run_dir)
        group = report["groups"]["cloud"]
        self.assertEqual(group["turn2"], {"sent": 15, "failed": 0, "not_sent": 3, "of_replies": 18})
        self.assertEqual([row["modal_count"] for row in group["per_line"]], [5, 5])
        self.assertTrue(all(row["sorter_majority"]["F0"] is None for row in group["per_line"]))
        self.assertEqual(group["parse_failures"]["count"], 2)

    def test_ordinary_unproved_question_skip_is_still_refused(self):
        run_dir = self.fixture()
        rewrite(run_dir, "results/F0__r1.json", lambda row: row.update(turn2=turn2_not_sent(False)))
        with self.assertRaisesRegex(Refuse, "turn 2 was not sent although the sort parsed"):
            self.tally(run_dir)

    def test_corrupt_skip_proof_is_refused(self):
        def change_first(field, value):
            return lambda row: row["calls"][0].update({field: value})
        def change_check(field, value):
            return lambda row: row["calls"][0]["usage_limit_check"].update({field: value})
        def change_skip(field, value):
            return lambda row: row["calls"][1].update({field: value})
        mutations = {
            "missing_calls": lambda row: row.pop("calls"),
            "extra_call": lambda row: row["calls"].append(dict(row["calls"][1])),
            "actual_wrong_caller": change_first("caller", "fixture-wrong"),
            "actual_wrong_turn": change_first("turn", 2),
            "actual_bool_turn": change_first("turn", True),
            "actual_incomplete": change_first("complete", False),
            "actual_not_sent": change_first("sent", False),
            "check_status": change_check("status", "within_limit"),
            "check_at_limit": change_check("reported_output_tokens", 19000),
            "check_bool_limit": change_check("limit", True),
            "check_float_tokens": change_check("reported_output_tokens", 19001.0),
            "check_wrong_field": change_check("field", "total_tokens"),
            "usage_missing": change_first("usage_json", None),
            "usage_disagrees": change_first("usage_json", '{"output_tokens": 18000}'),
            "skip_wrong_caller": change_skip("caller", "fixture-wrong"),
            "skip_wrong_turn": change_skip("turn", 1),
            "skip_wrong_reason": change_skip("not_sent_reason", "some other reason"),
            "skip_fabricated_model": change_skip("model_reported", "fixture-model"),
            "skip_fabricated_usage": change_skip("usage_json", "{}"),
            "question_raw": lambda row: row["turn2"].update(raw_reply="FIXTURE fabricated question answer"),
            "question_reason": lambda row: row["turn2"].update(not_sent_reason="wrong"),
            "budget_missing": lambda row: row.pop("call_budget"),
            "budget_limit": lambda row: row["call_budget"].update(output_token_limit=20000),
            "stop_missing": lambda row: row["call_budget"]["per_sorter"]["F0"].pop("stop"),
            "stop_reason": lambda row: row["call_budget"]["per_sorter"]["F0"]["stop"].update(reason="wrong"),
            "stop_check": lambda row: row["call_budget"]["per_sorter"]["F0"]["stop"]["usage_limit_check"].update(limit=18999),
            "budget_caller": lambda row: row["call_budget"]["per_sorter"]["F0"].update(caller="fixture-wrong"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                run_dir = self.fixture()
                rewrite(run_dir, "results/F0__r1.json", stop_result)
                rewrite(run_dir, "results/F0__r1.json", mutate)
                with self.assertRaises(Refuse):
                    self.tally(run_dir)


if __name__ == "__main__":
    unittest.main()
