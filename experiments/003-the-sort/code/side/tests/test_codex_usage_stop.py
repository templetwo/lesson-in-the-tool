"""Pure fake responses for the reported-usage stop; no caller switch, transport, or runner execution."""
import copy
import json
from pathlib import Path
import sys
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import runner
from callers import Conversation, Reply

STOP_REASON = 'sorter_output_limit_exceeded'
FIELDS = {'anthropic': 'output_tokens', 'openai': 'output_tokens', 'xai': 'output_tokens',
          'deepseek': 'completion_tokens', 'ollama': 'eval_count'}


class FakeUsageCaller:
    is_dry = False

    def __init__(self, kind, usage, limit=19000, text='FAKE retained answer', complete=True):
        self.name, self.kind, self.provider = 'FAKE-adapter', kind, kind
        self.output_token_limit, self.calls = limit, 0
        self.reply = Reply(text, {'caller': self.name, 'turn': 1, 'complete': complete,
                                 'usage_json': usage, 'response_body_json': 'FAKE retained body', 'error': None})

    def call(self, conversation, env=None):
        self.calls += 1
        return self.reply


def prepare(kind='anthropic', usage=None, limit=19000, two_sorters=False, smoke=False, **kwargs):
    fake = FakeUsageCaller(kind, usage, limit=limit, **kwargs)
    names = ['FAKE-A', 'FAKE-B'] if two_sorters else ['FAKE-A']
    cfg = {'caller': 'by_sorter', 'dry_run': False, 'repeats': 3,
           'sorters': [{'name': name, 'group': 'FAKE-group', 'provider': kind} for name in names]}
    wrapped, budget = runner.budget_callers(cfg, dict.fromkeys(names, fake), smoke=smoke)
    return fake, wrapped, budget


def invoke(caller, turn=1):
    messages = [{'role': 'user', 'content': 'FAKE first'}]
    if turn == 2:
        messages += [{'role': 'assistant', 'content': 'FAKE reply'}, {'role': 'user', 'content': 'FAKE second'}]
    return caller.call(Conversation(messages, []), env={})


class UsageStopTests(unittest.TestCase):
    def test_each_provider_total_over_limit_stops_only_future_calls(self):
        for kind, field in FIELDS.items():
            with self.subTest(kind=kind):
                usage = json.dumps({field: 19001})
                fake, wrapped, budget = prepare(kind, usage)
                first = invoke(wrapped['FAKE-A'])
                self.assertEqual(first.text, 'FAKE retained answer')
                self.assertEqual(first.record['usage_json'], usage)
                self.assertEqual(first.record['response_body_json'], 'FAKE retained body')
                self.assertTrue(first.record['complete'])
                check = first.record.get('usage_limit_check')
                self.assertEqual(check, {'status': 'exceeded', 'field': field,
                                         'reported_output_tokens': 19001, 'limit': 19000})
                skipped = invoke(wrapped['FAKE-A'], turn=2)
                self.assertIsNone(skipped.text)
                self.assertEqual(skipped.record.get('sent'), False)
                self.assertEqual(skipped.record.get('failure_reason'), STOP_REASON)
                self.assertEqual(skipped.record.get('not_sent_reason'), STOP_REASON)
                self.assertEqual(skipped.record['turn'], 2)
                self.assertFalse(skipped.record['complete'])
                self.assertEqual(fake.calls, 1)
                self.assertEqual(budget.receipt()['attempted']['total'], 1)
                self.assertEqual(budget.receipt()['per_sorter']['FAKE-A'].get('stop'),
                                 {'reason': STOP_REASON, 'usage_limit_check': check})

    def test_exact_limit_does_not_stop(self):
        fake, wrapped, budget = prepare(usage=json.dumps({'output_tokens': 19000}))
        first = invoke(wrapped['FAKE-A'])
        invoke(wrapped['FAKE-A'], turn=2)
        self.assertEqual(first.record.get('usage_limit_check', {}).get('status'), 'within_limit')
        self.assertEqual(fake.calls, 2)
        self.assertIsNone(budget.receipt()['per_sorter']['FAKE-A'].get('stop'))

    def test_nested_reasoning_subset_is_not_added_to_total(self):
        for kind, field in FIELDS.items():
            with self.subTest(kind=kind):
                usage = {field: 12000, 'output_tokens_details': {'reasoning_tokens': 13000},
                         'completion_tokens_details': {'reasoning_tokens': 13000}}
                fake, wrapped, budget = prepare(kind, json.dumps(usage))
                first = invoke(wrapped['FAKE-A'])
                invoke(wrapped['FAKE-A'], turn=2)
                self.assertEqual(first.record.get('usage_limit_check', {}).get('reported_output_tokens'), 12000)
                self.assertEqual(fake.calls, 2)

    def test_missing_or_malformed_usage_is_disclosed_without_assuming_zero(self):
        bad = [None, '', '{', '[]', '{}', '{"output_tokens": true}', '{"output_tokens": -1}',
               '{"output_tokens": 1.5}', '{"output_tokens": "19001"}']
        for usage in bad:
            with self.subTest(usage=usage):
                fake, wrapped, budget = prepare(usage=usage)
                first = invoke(wrapped['FAKE-A'])
                invoke(wrapped['FAKE-A'], turn=2)
                check = first.record.get('usage_limit_check', {})
                self.assertEqual(check.get('status'), 'unavailable')
                self.assertIsNone(check.get('reported_output_tokens'))
                self.assertTrue(check.get('reason'))
                self.assertEqual(first.record['usage_json'], usage)
                self.assertEqual(fake.calls, 2)

    def test_stop_is_per_sorter_even_when_two_sorters_share_an_adapter(self):
        fake, wrapped, budget = prepare(usage=json.dumps({'output_tokens': 19001}), two_sorters=True)
        invoke(wrapped['FAKE-A'])
        invoke(wrapped['FAKE-A'], turn=2)
        other = invoke(wrapped['FAKE-B'])
        self.assertEqual(other.text, 'FAKE retained answer')
        self.assertEqual(fake.calls, 2)
        self.assertEqual(budget.receipt()['attempted']['total'], 2)

    def test_every_later_repeat_is_explicitly_unsent_and_uncharged(self):
        fake, wrapped, budget = prepare(usage=json.dumps({'output_tokens': 19001}))
        invoke(wrapped['FAKE-A'])
        for unused in range(8):
            skipped = invoke(wrapped['FAKE-A'])
            self.assertEqual(skipped.record.get('sent'), False)
            self.assertEqual(skipped.record.get('caller'), fake.name)
            self.assertNotIn('model_reported', skipped.record)
            self.assertNotIn('usage_json', skipped.record)
            self.assertNotIn('response_body_json', skipped.record)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(budget.receipt()['attempted']['total'], 1)

    def test_unsuccessful_reply_can_still_trigger_a_reported_usage_stop(self):
        fake, wrapped, budget = prepare(usage=json.dumps({'output_tokens': 19001}), text=None, complete=False)
        first = invoke(wrapped['FAKE-A'])
        second = invoke(wrapped['FAKE-A'])
        self.assertIsNone(first.text)
        self.assertEqual(second.record.get('sent'), False)
        self.assertEqual(fake.calls, 1)

    def test_smoke_uses_effective_2000_limit_and_stop_precedes_budget_exhaustion(self):
        fake, wrapped, budget = prepare(usage=json.dumps({'output_tokens': 2001}), limit=2000, smoke=True)
        first = invoke(wrapped['FAKE-A'])
        self.assertEqual(first.record.get('usage_limit_check', {}).get('limit'), 2000)
        second = invoke(wrapped['FAKE-A'])
        self.assertEqual(second.record.get('sent'), False)
        self.assertEqual(fake.calls, 1)

    def test_original_returned_record_is_not_mutated(self):
        fake, wrapped, budget = prepare(usage=json.dumps({'output_tokens': 19001}))
        before = copy.deepcopy(fake.reply.record)
        annotated = invoke(wrapped['FAKE-A'])
        self.assertEqual(fake.reply.record, before)
        self.assertIsNot(annotated.record, fake.reply.record)
        self.assertEqual(annotated.text, fake.reply.text)

    def test_smoke_rejects_over_limit_ready_reply(self):
        fake, wrapped, budget = prepare(usage=json.dumps({'output_tokens': 2001}), limit=2000,
                                       smoke=True, text='ready')
        reply = invoke(wrapped['FAKE-A'])
        helper = getattr(runner, 'smoke_reply_status', None)
        if helper is not None:
            status, passed = helper('FAKE-head', reply)
        else:
            # Baseline smoke accepted a complete error-free ready reply regardless of its usage.
            status, passed = 'FAKE-head: ok', not reply.record.get('error') and reply.text == 'ready'
        self.assertFalse(passed)
        self.assertIn(STOP_REASON, status)
        self.assertEqual(reply.text, 'ready')


if __name__ == '__main__':
    unittest.main()
