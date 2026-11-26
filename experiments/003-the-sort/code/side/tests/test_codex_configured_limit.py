"""Configured caps: pure controls and fixture-only main/smoke integration.

The process switch must be absent. Real adapter calls use only installed fake
key/transport functions and a plain env dictionary. All generated files are
synthetic and confined to this candidate's scratch directory.
"""
import fakes_first  # Install forbidden-I/O tripwires before importing production modules.

import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import callers
from common import Refuse
import real_callers as real
import runner
import tally
import test_two_turn_and_callers as existing_fakes  # Alias avoids duplicate TestCase discovery.


BASE = Path(__file__).resolve().parents[1]
SCRATCH = BASE / 'scratch/configured_limit_tests'
FIELDS = {'anthropic': 'output_tokens', 'openai': 'output_tokens', 'xai': 'output_tokens',
          'deepseek': 'completion_tokens', 'ollama': 'eval_count'}
INVALID = (None, True, False, 0, -1, 60001, 60000.0, '60000', [], {})
FAKE_ENV = {'SORT_REAL_CALLS': 'allow'}  # Passed as data; never installed in os.environ.
MESSAGES = [{'role': 'user', 'content': 'FIXTURE configured-limit request'}]


def request_cap(adapter, body):
    if adapter.kind in ('anthropic', 'deepseek'):
        return body['max_tokens']
    if adapter.kind in ('openai', 'xai'):
        return body['max_output_tokens']
    return body['options']['num_predict']


class UsageFake:
    is_dry = False

    def __init__(self, kind, count, limit=60000):
        self.name = 'FIXTURE-' + kind
        self.kind = self.provider = kind
        self.output_token_limit = limit
        self.count, self.calls = count, 0

    def call(self, conversation, env=None):
        self.calls += 1
        return callers.Reply('FIXTURE retained reply', {
            'caller': self.name, 'turn': conversation.turn(), 'complete': True,
            'error': None, 'failure_reason': None,
            'usage_json': json.dumps({FIELDS[self.kind]: self.count,
                                     'output_tokens_details': {'reasoning_tokens': self.count}})})


class ConfiguredLimitTests(unittest.TestCase):
    def setUp(self):
        self.assertNotIn('SORT_REAL_CALLS', os.environ)
        self.addCleanup(lambda: self.assertNotIn('SORT_REAL_CALLS', os.environ))
        SCRATCH.mkdir(parents=True, exist_ok=True)
        directory = tempfile.TemporaryDirectory(prefix='FIXTURE-configured-cap-', dir=str(SCRATCH))
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.spies = existing_fakes.Spies(reply=existing_fakes.reply_by_turn)
        lines = ['FIXTURE line %d, not a real lesson.' % n for n in range(1, 18)]
        source = {'repo': 'FIXTURE-NO-REPO', 'commit_requested': 'FIXTURE-COMMIT', 'commit': 'f' * 40,
                  'path': 'FIXTURE-LINES.txt', 'blob_id': 'a' * 40,
                  'sha256': hashlib.sha256('\n'.join(lines).encode()).hexdigest(), 'lines': lines}
        replacements = [(real, '_open', fakes_first.tripwire('key file opener')),
                        (real, '_urlopen', fakes_first.tripwire('network opener')),
                        (real, 'read_key', self.spies.read_key),
                        (real, 'http_post_json', self.spies.post),
                        (real, 'clock', lambda: 'FIXTURE-NO-CLOCK'),
                        (runner, 'clock', lambda: 'FIXTURE-NO-CLOCK'),
                        (runner, 'load_lines', lambda *args: copy.deepcopy(source))]
        for obj, name, value in replacements:
            p = patch.object(obj, name, value)
            p.start()
            self.addCleanup(p.stop)

    def cfg(self, **changes):
        cfg = json.loads((BASE / 'config_real.json').read_text())
        cfg.update(repo='FIXTURE-NO-REPO', commit='FIXTURE-COMMIT', lines_path='FIXTURE-LINES.txt',
                   homes_file=str(BASE / 'fixtures/homes_fixture.json'), deny_list=str(BASE / 'deny_list.txt'),
                   prompt_text=str(BASE / 'prompt_text.json'), out_dir=str(self.directory / 'run'), repeats=1)
        cfg.pop('output_token_limit', None)
        cfg.update(changes)
        return cfg

    def assert_no_calls(self):
        self.assertEqual(self.spies.keys, [])
        self.assertEqual(self.spies.posts, [])

    def test_absent_main_key_keeps_19000_default_for_all_eight(self):
        adapters = runner.check_config(self.cfg())
        self.assertEqual(len(adapters), 8)
        self.assertEqual([c.output_token_limit for c in adapters.values()], [19000] * 8)
        self.assert_no_calls()

    def test_config_accepts_exact_integer_boundaries_and_forwards_to_all_eight(self):
        for limit in (1, 19000, 19001, 59999, 60000):
            with self.subTest(limit=limit):
                adapters = runner.check_config(self.cfg(output_token_limit=limit))
                self.assertEqual([c.output_token_limit for c in adapters.values()], [limit] * 8)
        self.assert_no_calls()

    def test_all_eight_adapter_requests_accept_60000(self):
        self.assertEqual(len(real.ADAPTERS), 8)
        for name in real.ADAPTERS:
            with self.subTest(adapter=name):
                adapter = callers.get_caller(name, output_token_limit=60000)
                _, body = adapter.build_request(MESSAGES)
                self.assertEqual(request_cap(adapter, body), 60000)
                self.assertEqual(body[adapter.messages_field], MESSAGES)
        self.assert_no_calls()

    def test_invalid_main_key_refuses_before_factory_input_loading_or_writes(self):
        for limit in INVALID:
            with self.subTest(limit=limit):
                with patch.object(runner, 'get_caller', side_effect=AssertionError('factory reached')) as factory, \
                     patch.object(runner, 'load_lines', side_effect=AssertionError('input reached')) as source, \
                     patch.object(runner, 'write_json', side_effect=AssertionError('write reached')) as writer:
                    with self.assertRaises(Refuse):
                        runner.run(self.cfg(output_token_limit=limit), env=FAKE_ENV)
                    factory.assert_not_called()
                    source.assert_not_called()
                    writer.assert_not_called()
                self.assertFalse((self.directory / 'run').exists())
        self.assert_no_calls()

    def test_factories_reject_non_integer_or_out_of_range_values(self):
        for factory in (callers.get_caller, real.get_adapter):
            for limit in INVALID:
                with self.subTest(factory=factory.__name__, limit=limit):
                    with self.assertRaises(Refuse):
                        factory('xai:grok-4.7', output_token_limit=limit)
        self.assert_no_calls()

    def test_direct_real_caller_check_uses_configured_main_limit(self):
        adapters = runner.check_real_callers(self.cfg(output_token_limit=60000))
        self.assertEqual([c.output_token_limit for c in adapters.values()], [60000] * 8)
        self.assert_no_calls()

    def test_real_config_fake_main_persists_effective_limit_everywhere(self):
        cfg = self.cfg(output_token_limit=60000)
        out = Path(runner.run(cfg, env=FAKE_ENV))
        self.assertEqual(len(self.spies.posts), 16)
        for post in self.spies.posts:
            body = post['body']
            self.assertEqual(body.get('max_tokens', body.get('max_output_tokens',
                             body.get('options', {}).get('num_predict'))), 60000)
        for name in ['manifest.json', 'key.json']:
            saved = json.loads((out / name).read_text())
            self.assertEqual(saved['call_budget']['output_token_limit'], 60000)
            self.assertEqual(saved['call_budget']['attempted']['total'], 16)
        results = sorted((out / 'results').glob('*.json'))
        self.assertEqual(len(results), 8)
        for path in results:
            saved = json.loads(path.read_text())
            self.assertTrue(saved['parse_ok'] and saved['turn2']['parse_ok'])
            self.assertEqual(saved['call_budget']['output_token_limit'], 60000)
            self.assertEqual([c['usage_limit_check']['limit'] for c in saved['calls']], [60000, 60000])

    def usage_budget(self, kind, count, smoke=False):
        fake = UsageFake(kind, count, limit=2000 if smoke else 60000)
        cfg = {'output_token_limit': 60000, 'repeats': 3,
               'sorters': [{'name': 'FIXTURE-A'}, {'name': 'FIXTURE-B'}]}
        wrapped, budget = runner.budget_callers(cfg, {'FIXTURE-A': fake, 'FIXTURE-B': fake}, smoke=smoke)
        return fake, wrapped, budget

    @staticmethod
    def invoke(caller, turn=1):
        messages = copy.deepcopy(MESSAGES)
        if turn == 2:
            messages += [{'role': 'assistant', 'content': 'FIXTURE prior'},
                         {'role': 'user', 'content': 'FIXTURE question'}]
        return caller.call(callers.Conversation(messages, []), env={})

    def test_budget_and_f_accept_equality_at_60000_without_adding_reasoning(self):
        for kind in FIELDS:
            with self.subTest(kind=kind):
                fake, wrapped, budget = self.usage_budget(kind, 60000)
                first = self.invoke(wrapped['FIXTURE-A'])
                self.invoke(wrapped['FIXTURE-A'], turn=2)
                self.assertEqual(first.record['usage_limit_check'], {
                    'status': 'within_limit', 'field': FIELDS[kind],
                    'reported_output_tokens': 60000, 'limit': 60000})
                self.assertEqual(fake.calls, 2)
                self.assertEqual(budget.receipt()['output_token_limit'], 60000)
                self.assertIsNone(budget.receipt()['per_sorter']['FIXTURE-A']['stop'])

    def test_f_stops_at_60001_without_charging_skips_or_stopping_other_sorter(self):
        for kind in FIELDS:
            with self.subTest(kind=kind):
                fake, wrapped, budget = self.usage_budget(kind, 60001)
                first = self.invoke(wrapped['FIXTURE-A'])
                self.assertEqual(first.text, 'FIXTURE retained reply')
                self.assertEqual(first.record['usage_limit_check']['status'], 'exceeded')
                self.assertEqual(first.record['usage_limit_check']['limit'], 60000)
                skipped = self.invoke(wrapped['FIXTURE-A'], turn=2)
                self.assertIsNone(skipped.text)
                self.assertIs(skipped.record['sent'], False)
                self.assertEqual(skipped.record['failure_reason'], runner.USAGE_STOP_REASON)
                self.assertEqual(fake.calls, 1)
                self.assertEqual(budget.receipt()['attempted']['total'], 1)
                self.assertEqual(self.invoke(wrapped['FIXTURE-B']).text, 'FIXTURE retained reply')
                self.assertEqual(fake.calls, 2)

    def test_budget_refuses_adapter_limit_different_from_config_before_delegate(self):
        cfg = {'output_token_limit': 60000, 'repeats': 1, 'sorters': [{'name': 'FIXTURE-A'}]}
        fake = UsageFake('openai', 10, limit=19000)
        with self.assertRaises(Refuse):
            runner.budget_callers(cfg, {'FIXTURE-A': fake})
        self.assertEqual(fake.calls, 0)

    def test_smoke_uses_2000_even_when_main_is_60000(self):
        self.spies.reply = None  # Fake response is the word ready.
        lines = []
        self.assertEqual(runner.smoke(self.cfg(output_token_limit=60000), env=FAKE_ENV, out=lines.append), 0)
        self.assertEqual(len(self.spies.posts), 8)
        for post in self.spies.posts:
            body = post['body']
            self.assertEqual(body.get('max_tokens', body.get('max_output_tokens',
                             body.get('options', {}).get('num_predict'))), 2000)
        budgets = [json.loads(line.split(': ', 1)[1]) for line in lines if line.startswith('call budget ')]
        self.assertEqual([b['output_token_limit'] for b in budgets], [2000, 2000])
        self.assertEqual(budgets[-1]['attempted']['total'], 8)
        self.assertFalse((self.directory / 'run').exists())

    def test_smoke_rejects_invalid_main_key_before_constructing_adapters(self):
        for limit in INVALID:
            with self.subTest(limit=limit):
                lines = []
                with patch.object(runner, 'get_caller', wraps=runner.get_caller) as factory:
                    code = runner.smoke(self.cfg(output_token_limit=limit), env=FAKE_ENV, out=lines.append)
                    self.assertEqual(code, 2)
                    factory.assert_not_called()
                self.assertTrue(any('output_token_limit' in line for line in lines))
        self.assert_no_calls()

    def test_smoke_f_threshold_stays_2000_not_configured_main_limit(self):
        fake, wrapped, budget = self.usage_budget('openai', 2001, smoke=True)
        first = self.invoke(wrapped['FIXTURE-A'])
        self.assertEqual(first.record['usage_limit_check']['limit'], 2000)
        self.assertEqual(first.record['usage_limit_check']['status'], 'exceeded')
        self.assertFalse(runner.smoke_reply_status('FIXTURE', first)[1])
        self.assertIs(self.invoke(wrapped['FIXTURE-A']).record['sent'], False)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(budget.receipt()['attempted']['total'], 1)

    def test_g_counts_provider_markers_without_reinterpreting_60000_numerically(self):
        for provider, marker in [('anthropic', 'max_tokens'), ('openai', 'incomplete'),
                                 ('xai', 'incomplete'), ('deepseek', 'length'), ('ollama', 'length')]:
            for count, complete in [(22, False), (60000, True), (60001, True)]:
                with self.subTest(provider=provider, count=count, complete=complete):
                    call = {'caller': 'FIXTURE-adapter', 'provider': provider, 'turn': 1,
                            'complete': complete, 'stop': 'stop' if complete else marker,
                            'failure_reason': None if complete else 'provider_incomplete',
                            'usage_json': json.dumps({FIELDS[provider]: count}),
                            'response_body_json': json.dumps({'status': 'incomplete',
                                'incomplete_details': {'reason': 'max_output_tokens'}})}
                    res = {'caller': 'FIXTURE-adapter', 'provider': provider, 'calls': [call],
                           'parse_ok': complete, 'raw_reply': 'FIXTURE' if complete else None,
                           'call_budget': {'output_token_limit': 60000}}
                    self.assertEqual(tally.limit_ending_counts(res), (0 if complete else 1, 0, 0))


if __name__ == '__main__':
    unittest.main()
