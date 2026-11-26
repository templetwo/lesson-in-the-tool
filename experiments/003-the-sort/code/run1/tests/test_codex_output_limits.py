"""Offline request/finalization controls; no calls, switch enabling, clocks or credentials."""
import copy
import json
import unittest
from unittest import mock

import callers
from common import Refuse
import real_callers as real


MESSAGES = [{"role": "user", "content": "FIXTURE invented output-limit request"}]


def payload(adapter, cutoff):
    """Invented replies with each maker's published completion/cutoff markers."""
    text = "FIXTURE partial answer" if cutoff else "FIXTURE complete answer"
    if adapter.kind == "anthropic":
        return {"model": adapter.model, "content": [{"type": "text", "text": text}],
                "usage": {"output_tokens": 20}, "stop_reason": "max_tokens" if cutoff else "end_turn"}
    if adapter.kind in ("openai", "xai"):
        return {"model": adapter.model, "output": [{"type": "message", "content": [
                    {"type": "output_text", "text": text}]}], "usage": {"output_tokens": 20},
                "status": "incomplete" if cutoff else "completed",
                "incomplete_details": {"reason": "max_output_tokens"} if cutoff else None}
    if adapter.kind == "deepseek":
        return {"model": adapter.model, "usage": {"completion_tokens": 20}, "choices": [
            {"message": {"content": text}, "finish_reason": "length" if cutoff else "stop"}]}
    return {"model": adapter.model, "message": {"content": text}, "done": True,
            "done_reason": "length" if cutoff else "stop", "eval_count": 20}


class OutputLimitTests(unittest.TestCase):
    def setUp(self):
        # A regression that accidentally crosses a live boundary fails before touching it.
        for name in ("read_key", "http_post_json", "_urlopen", "_open", "clock"):
            patcher = mock.patch.object(real, name, side_effect=AssertionError("forbidden boundary: " + name))
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(real.Adapter, "call", side_effect=AssertionError("Adapter.call forbidden"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_cap(self, adapter, body, expected):
        if adapter.kind in ("anthropic", "deepseek"):
            self.assertEqual(body.get("max_tokens"), expected)
            self.assertNotIn("max_output_tokens", body)
        elif adapter.kind in ("openai", "xai"):
            self.assertEqual(body.get("max_output_tokens"), expected)
            self.assertNotIn("max_tokens", body)
        else:
            self.assertEqual(body.get("options", {}).get("num_predict"), expected)
            self.assertNotIn("max_tokens", body)
            self.assertNotIn("max_output_tokens", body)

    def test_named_limits_exported_by_both_modules(self):
        for module in (callers, real):
            with self.subTest(module=module.__name__):
                self.assertEqual(getattr(module, "OUTPUT_TOKEN_LIMIT", None), 19000)
                self.assertEqual(getattr(module, "SMOKE_OUTPUT_TOKEN_LIMIT", None), 2000)

    def test_every_default_request_has_explicit_19000_cap(self):
        captured = []
        for name in real.ADAPTERS:
            with self.subTest(name=name):
                adapter = real.get_adapter(name)
                url, body = adapter.build_request(MESSAGES)
                captured.append((url, copy.deepcopy(body)))
                self.assert_cap(adapter, captured[-1][1], 19000)
                self.assertEqual(body[adapter.messages_field], MESSAGES)
        self.assertEqual(len(captured), 8)

    def test_smoke_request_has_explicit_2000_cap_for_every_maker(self):
        for name in real.ADAPTERS:
            with self.subTest(name=name):
                adapter = callers.get_caller(name, output_token_limit=2000)
                _, body = adapter.build_request(MESSAGES)
                self.assert_cap(adapter, body, 2000)

    def test_factory_forwards_limit_and_model_match_together(self):
        sentinel = object()
        name = next(iter(real.ADAPTERS))
        with mock.patch.object(real, "get_adapter", return_value=sentinel) as capture:
            self.assertIs(callers.get_caller(name, require_model_match=False, output_token_limit=2000), sentinel)
            capture.assert_called_once_with(name, require_model_match=False, output_token_limit=2000)

    def test_factories_reject_invalid_or_excessive_limits(self):
        name = next(iter(real.ADAPTERS))
        for factory in (callers.get_caller, real.get_adapter):
            for limit in (True, False, None, 0, -1, 19001, 20000, 19000.0, "19000"):
                with self.subTest(factory=factory.__name__, limit=limit):
                    with self.assertRaises(Refuse):
                        factory(name, output_token_limit=limit)

    def test_limits_accept_bounded_positive_integers(self):
        for limit in (1, 2000, 18999, 19000):
            with self.subTest(limit=limit):
                adapter = real.get_adapter("openai:gpt-6.2-astra", output_token_limit=limit)
                self.assertEqual(adapter.build_request(MESSAGES)[1]["max_output_tokens"], limit)

    def test_dryrun_factory_validates_limit_without_real_adapter(self):
        with mock.patch.object(real, "get_adapter", side_effect=AssertionError("dryrun used real factory")):
            self.assertTrue(callers.get_caller("dryrun", output_token_limit=2000).is_dry)
            with self.assertRaises(Refuse):
                callers.get_caller("dryrun", output_token_limit=19001)

    def test_local_timeout_is_900_and_cloud_timeout_stays_1800(self):
        for name in real.ADAPTERS:
            with self.subTest(name=name):
                adapter = real.get_adapter(name)
                self.assertEqual(adapter.timeout, 900 if adapter.kind == "ollama" else 1800)

    def test_mutated_limit_is_refused_before_build(self):
        for name in real.ADAPTERS:
            with self.subTest(name=name):
                adapter = real.get_adapter(name)
                adapter.output_token_limit = 19001
                with self.assertRaises(Refuse):
                    adapter.build_request(MESSAGES)

    def test_repeated_requests_do_not_share_mutable_options(self):
        adapter = real.get_adapter("ollama-local-a:qwen3.8:27b-draft4-text")
        first = adapter.build_request(MESSAGES)[1]
        self.assert_cap(adapter, first, 19000)
        first["options"]["num_predict"] = 1
        first["messages"][0]["content"] = "FIXTURE changed capture"
        second = adapter.build_request(MESSAGES)[1]
        self.assert_cap(adapter, second, 19000)
        self.assertEqual(second["messages"], MESSAGES)

    def test_every_maker_cutoff_returns_none_and_records_partial_evidence(self):
        for name in real.ADAPTERS:
            with self.subTest(name=name):
                adapter = real.get_adapter(name)
                response = payload(adapter, cutoff=True)
                before = copy.deepcopy(response)
                reply = real.finalize_reply(adapter, {"caller": name, "turn": 1}, response=response)
                self.assertIsNone(reply.text)
                self.assertFalse(reply.record["complete"])
                self.assertEqual(reply.record["failure_reason"], "provider_incomplete")
                self.assertEqual(reply.record["partial_text"], "FIXTURE partial answer")
                self.assertEqual(json.loads(reply.record["response_body_json"]), before)
                self.assertIsNotNone(reply.record["usage_json"])
                self.assertEqual(response, before)

    def test_normal_complete_replies_remain_countable_for_every_maker(self):
        for name in real.ADAPTERS:
            with self.subTest(name=name):
                adapter = real.get_adapter(name)
                reply = real.finalize_reply(adapter, {"caller": name, "turn": 1}, response=payload(adapter, False))
                self.assertEqual(reply.text, "FIXTURE complete answer")
                self.assertTrue(reply.record["complete"])
                self.assertIsNone(reply.record["failure_reason"])


if __name__ == "__main__":
    unittest.main()
