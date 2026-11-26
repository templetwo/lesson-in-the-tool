"""Offline config/fixture wiring checks. No enabled environment or real I/O."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import callers
from common import Refuse
from fixture_runs import make_run
import real_callers
from reply_parser import parse_sort_reply


class CallerPolicyWiring(unittest.TestCase):
    def setUp(self):
        self.assertNotIn("SORT_REAL_CALLS", os.environ)

    def test_default_identity_policy_reaches_adapter_factory(self):
        marker = object()
        with patch.object(real_callers, "get_adapter", return_value=marker) as factory:
            result = callers.get_caller("openai:gpt-6.2-astra")
        self.assertIs(result, marker)
        factory.assert_called_once_with("openai:gpt-6.2-astra", require_model_match=True, output_token_limit=19000)

    def test_explicit_identity_override_reaches_adapter_factory(self):
        marker = object()
        with patch.object(real_callers, "get_adapter", return_value=marker) as factory:
            result = callers.get_caller("openai:gpt-6.2-astra", require_model_match=False)
        self.assertIs(result, marker)
        factory.assert_called_once_with("openai:gpt-6.2-astra", require_model_match=False, output_token_limit=19000)

    def test_identity_policy_rejects_non_boolean_before_factory(self):
        for value in (None, 0, 1, "false", [], {}):
            with self.subTest(value=value), patch.object(real_callers, "get_adapter") as factory:
                with self.assertRaises(Refuse):
                    callers.get_caller("openai:gpt-6.2-astra", require_model_match=value)
                factory.assert_not_called()

    def test_dry_caller_remains_dry(self):
        reply = callers.get_caller("dryrun").call(callers.Conversation(
            [{"role": "user", "content": "FIXTURE"}], ["L01"]), env={})
        self.assertEqual(reply.record, {"caller": "dryrun", "turn": 1})

    def test_every_adapter_identity_policy_controls_countable_text(self):
        text = "L01 | main: FIXTURE-HOME | second: none"
        for name in real_callers.ADAPTERS:
            with self.subTest(adapter=name):
                adapter = callers.get_caller(name)
                model = "FIXTURE-WRONG-MODEL"
                if name.startswith("anthropic:"):
                    body = {"model": model, "stop_reason": "end_turn", "usage": {},
                            "content": [{"type": "text", "text": text}]}
                elif name.startswith(("openai:", "xai:")):
                    body = {"model": model, "status": "completed", "usage": {},
                            "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}
                elif name.startswith("deepseek:"):
                    body = {"model": model, "usage": {},
                            "choices": [{"finish_reason": "stop", "message": {"content": text}}]}
                else:
                    body = {"model": model, "done": True, "done_reason": "stop", "message": {"content": text}}
                reply = real_callers.finalize_reply(adapter, {}, response=body)
                parsed = parse_sort_reply(reply.text, ["L01"], ["FIXTURE-HOME"], dry_run=False)
                self.assertFalse(parsed["ok"])
                self.assertEqual(parsed["rows"], [])
                self.assertEqual(reply.record["failure_reason"], "model_mismatch")
                override = callers.get_caller(name, require_model_match=False)
                accepted = real_callers.finalize_reply(override, {}, response=body)
                self.assertIs(accepted.record["require_model_match"], False)
                self.assertTrue(parse_sort_reply(accepted.text, ["L01"], ["FIXTURE-HOME"], dry_run=False)["ok"])


class FixtureMapWiring(unittest.TestCase):
    def test_by_sorter_fixture_saves_the_assignment_map(self):
        scratch = Path(__file__).resolve().parents[2] / "test2_stale/scratch/codex_fix_integration"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="fixture_map_", dir=str(scratch)) as folder:
            names = [("S1", "cloud"), ("S2", "cloud")]
            mapping = {"S1": "FIXTURE-provider1", "S2": "FIXTURE-provider2"}
            run = make_run(folder, names, 1, ["FIXTURE-HOME"], 1,
                           {(s, 1): ["FIXTURE-HOME"] for s, _ in names},
                           caller="by_sorter", result_callers=mapping)
            key = json.loads((Path(run) / "key.json").read_text())
            self.assertEqual(key.get("real_callers"), mapping)


if __name__ == "__main__":
    unittest.main()
