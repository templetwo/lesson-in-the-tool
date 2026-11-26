"""Pure postprocessing regressions and switch-off controls. Never enables a caller.

Before the fix, finalize() reproduces the existing Adapter.call postprocessing
without its key, transport, clock, or guard paths. This makes the initial red
run a behavioral comparison, not an absent-helper import error.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import real_callers as rc
from callers import Conversation, Reply
from common import Refuse

FAKE = "FAKE_ONLY_NOT_A_KEY_0123456789"
NAME = "openai:gpt-6.2-astra"


def response(model="gpt-6.2-astra", text="FAKE ordinary reply", status="completed"):
    return {"model": model, "status": status, "usage": {},
            "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}


def finalize(adapter, resp=None, error=None, key=FAKE, extra=None):
    record = {"caller": adapter.name, "turn": 1, "provider": adapter.provider,
              "model_requested": adapter.model, "model_reported": None, "model_matches": None,
              "complete": False, "stop": None, "usage_json": None, "response_body_json": None,
              "partial_text": None, "error": None}
    helper = getattr(rc, "finalize_reply", None)
    if helper is not None:
        return helper(adapter, record, response=resp, error=error, key=key, extra_headers=extra)
    # Exact old postprocessing, with clock assignments omitted: no I/O.
    text = None
    if error is not None:
        record["error"] = "%s: %s" % (type(error).__name__, error)
    else:
        record["response_body_json"] = json.dumps(resp, ensure_ascii=False, sort_keys=True)
        try:
            text, model_rep, usage, stop, complete = adapter.read_response(resp)
            record.update(model_reported=model_rep, model_matches=(model_rep == adapter.model) if model_rep else None,
                          usage_json=json.dumps(usage, sort_keys=True) if usage is not None else None,
                          stop=stop, complete=bool(complete))
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            record["error"] = "unexpected response shape (%s: %s)" % (type(exc).__name__, exc)
            text = None
    if not record["complete"]:
        record["partial_text"] = text
        text = None
    failed = record["error"] is not None
    record = rc.scrub(record, key, rc.MIN_KEY_PIECE if failed else 0)
    return Reply(rc.redact(text, key, 0), record)


class PureCallerFixTests(unittest.TestCase):
    def setUp(self):
        self.adapter = rc.get_adapter(NAME)

    def test_plain_success_whole_key_is_cleaned(self):
        reply = finalize(self.adapter, response(text=FAKE))
        self.assertNotIn(FAKE, json.dumps(reply.record))
        self.assertNotIn(FAKE, reply.text)
        self.assertTrue(reply.record["complete"])

    def test_quoted_whole_key_is_cleaned_before_body_serialization(self):
        key = 'FAKE_ONLY_QUOTED_"_NOT_A_KEY_012345'
        reply = finalize(self.adapter, response(text=key), key=key)
        body = json.loads(reply.record["response_body_json"])
        self.assertNotEqual(body["output"][0]["content"][0]["text"], key)
        self.assertNotIn(json.dumps(key)[1:-1], reply.record["response_body_json"])

    def test_structured_dictionary_keys_are_cleaned(self):
        reply = finalize(self.adapter, response(model={FAKE: "FAKE metadata"}))
        self.assertNotIn(FAKE, json.dumps(reply.record))

    def test_json_escaped_error_secret_is_removed(self):
        key = r"FAKE\A\B\C\D\E\F"
        error = rc.TransportError(401, json.dumps({"error": key}))
        reply = finalize(self.adapter, error=error, key=key)
        self.assertNotIn(json.dumps(key)[1:-1], reply.record["error"])
        self.assertIsNone(reply.text)

    def test_incomplete_reply_pieces_are_cleaned(self):
        fragment = FAKE[-8:]
        reply = finalize(self.adapter, response(text=fragment, status="incomplete"))
        self.assertNotIn(fragment, json.dumps(reply.record))
        self.assertIsNone(reply.text)

    def test_refused_reply_pieces_are_cleaned(self):
        fragment = FAKE[-8:]
        reply = finalize(self.adapter, response(text=fragment, status="refused"))
        self.assertNotIn(fragment, json.dumps(reply.record))
        self.assertIsNone(reply.text)

    def test_extra_header_values_are_cleaned_from_success_body(self):
        value = "FAKE_WORKSPACE_IDENTIFIER_ABCDEFGHIJ"
        reply = finalize(self.adapter, response(text=value), extra={"FAKE-workspace": value})
        self.assertNotIn(value, json.dumps(reply.record))
        self.assertNotIn(value, reply.text)

    def test_extra_header_whole_values_are_cleaned_but_fragments_preserved(self):
        value = "FAKE_HEADER_VALUE_ABCDEFGHIJ"
        reply = finalize(self.adapter, error=ValueError("FAKE invalid header: %s %s %s" % (value, value[-8:], FAKE[-8:])),
                         extra={"FAKE-header": value})
        self.assertNotIn(value, reply.record["error"])
        self.assertIn(value[-8:], reply.record["error"])
        self.assertNotIn(FAKE[-8:], reply.record["error"])

    def test_workspace_fragment_preserves_refusal_detail_and_no_fallback(self):
        adapter = rc.get_adapter("anthropic:claude-opus-5-5")
        body = {"model": adapter.model,
                "content": [{"type": "thinking", "thinking": "", "signature": "FIXTURE"},
                            {"type": "text", "text": ""}],
                "stop_reason": "refusal", "stop_details": {"type": "refusal", "category": "FIXTURE"},
                "usage": {"input_tokens": 11, "output_tokens": 22}}
        reply = finalize(adapter, body, key="fake-key-Q7xW2pL9vN4rT6yZ8bC1",
                         extra={"anthropic-workspace-id": "FIXTURE-workspace"})
        self.assertIsNone(reply.text)
        self.assertFalse(reply.record["complete"])
        self.assertEqual(reply.record["stop"], "refusal")
        saved = json.loads(reply.record["response_body_json"])
        self.assertEqual(saved["stop_details"], body["stop_details"])
        self.assertEqual(saved["content"][0]["signature"], "FIXTURE")
        _, payload = adapter.build_request([{"role": "user", "content": "FIXTURE"}])
        self.assertNotIn("fallbacks", payload)

    def test_model_mismatch_is_failed_and_not_countable(self):
        reply = finalize(self.adapter, response(model="FAKE_WRONG_MODEL"))
        self.assertIsNone(reply.text)
        self.assertFalse(reply.record["complete"])
        self.assertEqual(reply.record.get("failure_reason"), "model_mismatch")

    def test_missing_or_nonstring_model_fails_strictly(self):
        for model in (None, "", 7, {"FAKE": "model"}):
            with self.subTest(model=model):
                reply = finalize(self.adapter, response(model=model))
                self.assertIsNone(reply.text)
                self.assertFalse(reply.record["complete"])
                self.assertIn(reply.record.get("failure_reason"), ("model_reported_missing", "model_reported_invalid"))

    def test_default_model_policy_is_strict(self):
        self.assertIs(getattr(self.adapter, "require_model_match", None), True)

    def test_explicit_nonstrict_policy_is_recorded(self):
        self.adapter.require_model_match = False
        reply = finalize(self.adapter, response(model="FAKE_WRONG_MODEL"))
        self.assertEqual(reply.text, "FAKE ordinary reply")
        self.assertIs(reply.record.get("require_model_match"), False)
        self.assertIs(reply.record["model_matches"], False)

    def test_nonboolean_model_policy_is_refused(self):
        self.adapter.require_model_match = "FAKE_INVALID_FLAG"
        with self.assertRaisesRegex(Refuse, "require_model_match"):
            finalize(self.adapter, response())

    def test_model_error_itself_is_redacted(self):
        reply = finalize(self.adapter, response(model=FAKE))
        self.assertEqual(reply.record.get("failure_reason"), "model_mismatch")
        self.assertNotIn(FAKE, json.dumps(reply.record))

    def test_redaction_key_collision_fails_closed(self):
        body = response()
        second = "FAKE_SECOND_COLLISION_SECRET"
        body["usage"] = {FAKE: "FAKE first", second: "FAKE second"}
        reply = finalize(self.adapter, body, extra={"FAKE-header": second})
        self.assertIsNone(reply.text)
        self.assertEqual(reply.record.get("failure_reason"), "redaction_collision")
        self.assertNotIn(FAKE, json.dumps(reply.record))

    def test_success_fragment_policy_remains_explicit(self):
        fragment = FAKE[-8:]
        reply = finalize(self.adapter, response(text=fragment))
        self.assertEqual(reply.text, fragment)
        self.assertTrue(reply.record["complete"])

    def test_usage_serialization_does_not_reintroduce_a_tracked_escape(self):
        key = r"\ue000"
        body = response()
        body["usage"] = {"fixture": "X"}
        reply = finalize(self.adapter, body, key=key,
                         extra={"fixture-one": "X", "fixture-two": "[KEY REDACTED]"})
        self.assertNotIn(key, reply.record["usage_json"])
        self.assertNotIn(key, reply.record["response_body_json"])

    def test_later_secret_cannot_reintroduce_earlier_secret_as_marker(self):
        tracked = "[KEY REDACTED]"
        reply = finalize(self.adapter, response(text="FAKE_XYZ"),
                         extra={"FAKE-first": tracked, "FAKE-second": "FAKE_XYZ"})
        self.assertNotIn(tracked, json.dumps(reply.record))
        self.assertNotIn(tracked, reply.text)
        self.assertNotIn("FAKE_XYZ", reply.text)

    def test_redaction_separator_cannot_join_neighbors_into_a_secret(self):
        key = "FAKEfoobar"
        reply = finalize(self.adapter, response(text="FAKEfooXbar"), key=key,
                         extra={"FAKE-one": "X", "FAKE-two": "[KEY REDACTED]"})
        self.assertNotIn(key, reply.text)
        body = json.loads(reply.record["response_body_json"])
        self.assertNotIn(key, body["output"][0]["content"][0]["text"])
        tracked = "FAKEfoo[KEY REDACTED]"
        reply = finalize(self.adapter, response(text="FAKEfooX"),
                         extra={"FAKE-one": "X", "FAKE-two": tracked})
        self.assertNotIn(tracked, reply.text)
        body = json.loads(reply.record["response_body_json"])
        self.assertNotIn(tracked, body["output"][0]["content"][0]["text"])

    def test_header_value_equal_to_internal_envelope_label_does_not_crash(self):
        reply = finalize(self.adapter, response(text="FAKE ordinary reply"), extra={"FAKE-header": "body"})
        self.assertEqual(reply.text, "FAKE ordinary reply")
        self.assertTrue(reply.record["complete"])
        self.assertIsInstance(json.loads(reply.record["response_body_json"]), dict)

    def test_header_value_equal_to_public_record_label_preserves_schema(self):
        reply = finalize(self.adapter, response(), extra={"FAKE-header": "error"})
        self.assertIn("error", reply.record)
        self.assertIsNone(reply.record["error"])
        self.assertTrue(reply.record["complete"])

    def test_finalization_does_not_mutate_response(self):
        body = response(text=FAKE)
        before = copy.deepcopy(body)
        finalize(self.adapter, body)
        self.assertEqual(body, before)

    def test_all_adapter_guards_still_refuse_before_any_io(self):
        trips = []
        def tripwire(*args, **kwargs):
            trips.append(True)
            raise AssertionError("FAKE test reached forbidden I/O")
        with patch.object(rc, "read_key", tripwire), patch.object(rc, "http_post_json", tripwire), \
             patch.object(rc, "_open", tripwire), patch.object(rc, "_urlopen", tripwire):
            for name in rc.ADAPTERS:
                with self.subTest(name=name), self.assertRaisesRegex(Refuse, "real calls are off"):
                    rc.get_adapter(name).call(Conversation([{"role": "user", "content": "FAKE"}], []), env={})
        self.assertEqual(trips, [])


if __name__ == "__main__":
    unittest.main()
