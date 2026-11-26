"""One fixture-only G table check; all fixture writes stay in Test2 scratch."""
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
from common import load_json, sha256_file, write_json
from fixture_runs import make_run
from reply_parser import parse_sort_reply, parse_question_reply
from runner import turn2_not_sent
import tally

SCRATCH = HERE.parents[1] / "test2_stale/scratch/codex_limits_round/tally"
PROVIDERS = ["anthropic", "anthropic", "openai", "openai", "xai", "deepseek", "ollama-local-a", "ollama-local-b"]
SORTERS = [("F%d" % n, "cloud" if n < 6 else "local") for n in range(8)]
CALLERS = {s: "fixture-adapter-" + s for s, _ in SORTERS}
HOMES = ["FIXTURE-A", "FIXTURE-B"]
STOP = "sorter_output_limit_exceeded"
ERROR = "sorter stopped after reported output usage exceeded the effective call limit"
CHECK = {"status": "exceeded", "field": "output_tokens", "reported_output_tokens": 19001, "limit": 19000}


def call_record(sorter, turn, marker=None, reason="max_output_tokens", failure_reason="provider_incomplete"):
    provider = PROVIDERS[int(sorter[1:])]
    record = {"dry_run": False, "caller": CALLERS[sorter], "provider": provider, "turn": turn,
              "complete": marker is None, "stop": marker,
              "error": None if marker is None else "FIXTURE incomplete",
              "failure_reason": None if marker is None else failure_reason}
    if provider in ("openai", "xai") and marker:
        body = {"status": marker, "incomplete_details": {"reason": reason} if reason else None}
        record["response_body_json"] = json.dumps(body)
    return record


def skip(sorter, turn):
    return {"dry_run": False, "caller": CALLERS[sorter], "turn": turn, "sent": False,
            "complete": False, "error": ERROR, "failure_reason": STOP, "not_sent_reason": STOP}


def budget(sorter, attempted):
    return {"output_token_limit": 19000, "per_sorter": {sorter: {
        "caller": CALLERS[sorter], "planned": 6, "attempted": attempted,
        "stop": {"reason": STOP, "usage_limit_check": copy.deepcopy(CHECK)}}}}


class LimitEndingTableTests(unittest.TestCase):
    def test_reported_markers_and_f_unsent_sorts_are_separate_in_json_and_cli(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="limit-table-fixture-", dir=str(SCRATCH)) as directory:
            assign = {(s, r): HOMES for s, _ in SORTERS for r in (1, 2, 3)}
            run_dir = Path(make_run(directory, SORTERS, 3, HOMES, 2, assign,
                                   providers=dict(zip([s for s, _ in SORTERS], PROVIDERS)),
                                   caller="by_sorter", result_callers=CALLERS))
            manifest_path = run_dir / "manifest.json"
            manifest = load_json(str(manifest_path), "fixture manifest")
            for sorter, _ in SORTERS:
                for repeat in (1, 2, 3):
                    relative = "results/%s__r%d.json" % (sorter, repeat)
                    path = run_dir / relative
                    row = load_json(str(path), "fixture result")
                    row["calls"] = [call_record(sorter, 1), call_record(sorter, 2)]
                    first_failed = False
                    second_failed = False
                    if sorter == "F0":
                        if repeat == 1:
                            row["calls"][1] = call_record(sorter, 2, "max_tokens")
                            row["calls"][1].update(usage_json=json.dumps({"output_tokens": 19001}),
                                                    usage_limit_check=copy.deepcopy(CHECK))
                            second_failed = True
                        else:
                            row["calls"] = [skip(sorter, 1)]
                            first_failed = True
                        row["call_budget"] = budget(sorter, 2)
                    if sorter == "F1" and repeat == 1:
                        row["calls"] = [call_record(sorter, 1, "max_tokens")]
                        first_failed = True
                    if sorter == "F1" and repeat == 3:
                        row["calls"][0].update(usage_json=json.dumps({"output_tokens": 19001}),
                                                usage_limit_check=copy.deepcopy(CHECK))
                        row["calls"][1] = skip(sorter, 2)
                        row["call_budget"] = budget(sorter, 4)
                        row["turn2"] = {"dry_run": False, "sent": False, "not_sent_reason": STOP,
                                        "raw_reply": None, "parse_ok": False, "parse_errors": [], "rows": []}
                    if (sorter, repeat) in (("F2", 1), ("F3", 2)):
                        row["calls"] = [call_record(sorter, 1, "incomplete",
                                                    reason="max_output_tokens" if sorter == "F2" else None)]
                        first_failed = True
                    if (sorter, repeat) in (("F2", 2), ("F3", 1), ("F4", 1)):
                        row["calls"][1] = call_record(sorter, 2, "incomplete",
                            reason="content_filter" if sorter == "F2" else "max_output_tokens",
                            failure_reason="model_mismatch" if sorter == "F4" else "provider_incomplete")
                        second_failed = True
                    if sorter == "F4" and repeat == 2:
                        row["calls"] = [call_record(sorter, 1)]
                        row["calls"][0].update(complete=False, error="FIXTURE timeout", failure_reason="transport_error")
                        first_failed = True
                    if sorter in ("F5", "F6") and repeat in (1, 2):
                        if repeat == 1:
                            row["calls"] = [call_record(sorter, 1, "length")]
                            first_failed = True
                        else:
                            row["calls"][1] = call_record(sorter, 2, "length")
                            second_failed = True
                    if sorter == "F7" and repeat == 1:
                        row["calls"] = [call_record(sorter, 1)]
                        first_failed = True  # a complete but unparseable answer is not a limit ending
                    if first_failed:
                        raw = "FIXTURE invalid grammar" if sorter == "F7" else None
                        parsed = parse_sort_reply(raw, ["L01", "L02"], HOMES, dry_run=False)
                        row.update(raw_reply=raw, parse_ok=False, parse_errors=parsed["errors"], rows=[],
                                   turn2=turn2_not_sent(False))
                    if second_failed:
                        parsed = parse_question_reply(None, ["L01", "L02"])
                        row["turn2"].update(raw_reply=None, parse_ok=False, parse_errors=parsed["errors"], rows=[])
                    write_json(str(path), row)
                    for entry in manifest["files"]:
                        if entry["path"] == relative:
                            entry["sha256"] = sha256_file(str(path))
            write_json(str(manifest_path), manifest)
            cfg = {"run_dir": str(run_dir), "sorters": [
                {"name": s, "group": g, "provider": PROVIDERS[i]} for i, (s, g) in enumerate(SORTERS)],
                "groups": {}, "repeats": 3, "cut_points_by_size": {"6": {"settled_min": 5, "leaning_min": 4}},
                "bootstrap": {"seed": 17, "draws": 20, "level": 0.95}}
            report, judgment = tally.compute(cfg, allow_fixture=True)
            expected = [(0, 1, 2), (1, 0, 0), (1, 0, 0), (0, 1, 0),
                        (0, 1, 0), (1, 1, 0), (1, 1, 0), (0, 0, 0)]
            table = json.loads(json.dumps(report))["limit_endings_by_sorter"]
            self.assertEqual([row["sorter"] for row in table], [s for s, _ in SORTERS])
            self.assertEqual([(row["message_1"], row["message_2"], row["sorts_not_sent_after_f"]) for row in table], expected)
            self.assertIn("not proof", report["limit_endings_note"])
            self.assertIn("missing", report["limit_endings_note"])
            self.assertEqual([row["modal_count"] for row in report["groups"]["cloud"]["per_line"]], [5, 5])
            self.assertEqual(report["groups"]["cloud"]["parse_failures"], {"count": 7, "of_replies": 18})
            self.assertEqual(report["groups"]["cloud"]["turn2"], {"sent": 10, "failed": 5, "not_sent": 8, "of_replies": 18})
            self.assertEqual([row["modal_count"] for row in report["groups"]["local"]["per_line"]], [2, 2])
            self.assertEqual(report["groups"]["local"]["turn2"], {"sent": 4, "failed": 1, "not_sent": 2, "of_replies": 6})
            output = io.StringIO()
            with mock.patch.object(tally, "load_json", return_value={"out_dir": "fixture-not-written"}), \
                    mock.patch.object(tally, "compute", return_value=(report, judgment)), \
                    mock.patch.object(tally, "clock", return_value="FIXTURE CLOCK"), \
                    mock.patch.object(tally.os, "makedirs"), mock.patch.object(tally, "write_json"), \
                    mock.patch.object(tally, "open", mock.mock_open(), create=True), contextlib.redirect_stdout(output):
                self.assertEqual(tally.main(["--config", "fixture-not-read", "--allow-fixture"]), 0)
            self.assertIn("Provider-reported limit endings by sorter", output.getvalue())
            self.assertIn("sorter | message 1 | message 2 | sorts not sent after F", output.getvalue())
            for (sorter, _), values in zip(SORTERS, expected):
                self.assertIn("%s | %d | %d | %d" % ((sorter,) + values), output.getvalue())
            self.assertIn(report["limit_endings_note"], output.getvalue())


if __name__ == "__main__":
    unittest.main()
