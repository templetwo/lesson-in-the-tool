"""Frozen run-1 config, with synthetic replies: byte-for-byte behavioral snapshot.

The golden hashes were measured before changing the frozen implementation. Clock
and provenance paths are fixed fixture inputs; every written JSON byte and every
outbound payload is captured in memory. No network, credentials or output run.
"""
import tests.fakes_first  # Install tripwires before importing any execution path.
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import callers
import real_callers
import runner
from common import load_json


GOLDEN = Path(__file__).parent / "fixtures" / "run1_default_behavior.json"


def capture_default(explicit=False):
    cfg = load_json("config_real.json", "frozen run-1 fixture config")
    assert "output_token_limit" not in cfg
    if explicit:
        cfg["output_token_limit"] = 19000
    # The run's source, roster, repeats, seed and prompt wording are unchanged.
    # A virtual output directory avoids writing synthetic experimental records.
    cfg["out_dir"] = "scratch/FIXTURE-default-byte-compatibility"
    homes, homes_sha = runner.load_homes(cfg["homes_file"])
    ptext = runner.load_prompt_text(cfg["prompt_text"])
    ptext["path"] = "/FIXTURE/prompt_text.json"
    cfg["homes_file"] = "/FIXTURE/homes_real.json"
    files, requests = {}, []
    real_sha256_file = runner.sha256_file

    def write(path, obj):
        # Exact common.write_json encoding, including insertion order/newline.
        files[str(path)] = (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode()

    def file_hash(path):
        if str(path) in files:
            return hashlib.sha256(files[str(path)]).hexdigest()
        return real_sha256_file(path)

    def fake_call(adapter, conversation, env=None):
        url, body = adapter.build_request(conversation.messages)
        requests.append({"url": url, "body": copy.deepcopy(body)})
        turn = conversation.turn()
        text = "".join(("%s | main: check | second: none\n" if turn == 1
                        else "%s | FIXTURE unscored sentence.\n") % label
                       for label in conversation.labels)
        record = {"caller": adapter.name, "turn": turn,
                  "settings_sent_json": json.dumps(adapter.settings(), sort_keys=True)}
        if adapter.kind == "anthropic":
            response = {"model": adapter.model, "stop_reason": "end_turn",
                        "content": [{"type": "text", "text": text}], "usage": {"output_tokens": 100}}
        elif adapter.kind in ("openai", "xai"):
            response = {"model": adapter.model, "status": "completed", "incomplete_details": None,
                        "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
                        "usage": {"output_tokens": 100}}
        elif adapter.kind == "deepseek":
            response = {"model": adapter.model, "choices": [{"message": {"content": text},
                        "finish_reason": "stop"}], "usage": {"completion_tokens": 100}}
        else:
            response = {"model": adapter.model, "message": {"content": text},
                        "done": True, "done_reason": "stop", "eval_count": 100}
        return real_callers.finalize_reply(adapter, record, response=response)

    with patch.object(runner, "load_homes", return_value=(homes, homes_sha)), \
            patch.object(runner, "load_prompt_text", return_value=ptext), \
            patch.object(runner, "write_json", side_effect=write), \
            patch.object(runner, "_checkpoint_result", side_effect=write), \
            patch.object(runner, "sha256_file", side_effect=file_hash), \
            patch.object(runner.os, "makedirs"), \
            patch.object(runner, "clock", return_value="FIXTURE fixed clock"), \
            patch.object(real_callers.Adapter, "call", fake_call):
        runner.run(cfg, env={"SORT_REAL_CALLS": "allow"})
    prefix = cfg["out_dir"] + "/"
    return {"fixture": "synthetic replies; never experimental data",
            "config_source_sha256": real_sha256_file("config_real.json"),
            "request_count": len(requests),
            "requests_sha256": hashlib.sha256(json.dumps(requests, sort_keys=True).encode()).hexdigest(),
            "files_sha256": {path[len(prefix):]: hashlib.sha256(raw).hexdigest()
                             for path, raw in sorted(files.items())}}


class FrozenDefaultCompatibility(unittest.TestCase):
    def test_absent_key_matches_prechange_frozen_behavior_bytes(self):
        self.assertEqual(capture_default(), json.loads(GOLDEN.read_text()))

    def test_explicit_19000_is_identical_to_absent_key(self):
        self.assertEqual(capture_default(explicit=True), json.loads(GOLDEN.read_text()))


if __name__ == "__main__":
    unittest.main()
