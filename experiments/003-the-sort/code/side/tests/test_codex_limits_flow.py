"""Synthetic returned-reply flow through the dry runner; no real adapter call.

The provider finalizer is pure. Every request-producing caller here remains a
DryRunCaller with a substituted return value, and the real-call switch stays off.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import callers
import real_callers
import runner
from tests import test_codex_persistence as persistence


class LimitFailureFlow(unittest.TestCase):
    setUp = persistence.PersistenceTests.setUp
    cfg = persistence.PersistenceTests.cfg
    result = persistence.PersistenceTests.result
    run_with = persistence.PersistenceTests.run_with

    def run_returned(self, cfg, returned):
        seen = []

        class ReturnedFixture(callers.DryRunCaller):
            def call(self, conversation, env=None):
                seen.append(conversation.turn())
                return returned

        self.run_with(cfg, ReturnedFixture())
        result = self.result(cfg)
        self.assertEqual(seen, [1])
        self.assertIsNone(result['raw_reply'])
        self.assertFalse(result['parse_ok'])
        self.assertEqual(result['turn2'], runner.turn2_not_sent(True))
        self.assertEqual(len(result['calls']), 1)
        self.assertEqual(result['persistence_state'], 'complete')
        manifest = json.loads((Path(cfg['out_dir']) / 'manifest.json').read_text())
        self.assertEqual(manifest['call_budget']['planned']['total'], 2)
        self.assertEqual(manifest['call_budget']['attempted']['total'], 1)
        self.assertEqual(manifest['call_budget']['attempted']['external'], 0)
        return result

    def test_each_provider_cutoff_persists_failure_and_skips_second_message(self):
        for index, name in enumerate(real_callers.ADAPTERS):
            with self.subTest(adapter=name):
                adapter = callers.get_caller(name)
                text = 'FIXTURE partial answer, not experimental data'
                if name.startswith('anthropic:'):
                    body = {'model': adapter.model, 'stop_reason': 'max_tokens', 'usage': {},
                            'content': [{'type': 'text', 'text': text}]}
                elif name.startswith(('openai:', 'xai:')):
                    body = {'model': adapter.model, 'status': 'incomplete', 'usage': {},
                            'incomplete_details': {'reason': 'max_output_tokens'},
                            'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': text}]}]}
                elif name.startswith('deepseek:'):
                    body = {'model': adapter.model, 'usage': {},
                            'choices': [{'finish_reason': 'length', 'message': {'content': text}}]}
                else:
                    body = {'model': adapter.model, 'done': True, 'done_reason': 'length',
                            'message': {'content': text}}
                reply = real_callers.finalize_reply(adapter, {}, response=body)
                self.assertIsNone(reply.text)
                result = self.run_returned(self.cfg('cutoff-%d' % index), reply)
                self.assertEqual(result['calls'][0]['partial_text'], text)
                self.assertEqual(json.loads(result['calls'][0]['response_body_json']), body)

    def test_each_local_timeout_is_recorded_and_skips_second_message(self):
        for index, name in enumerate(n for n in real_callers.ADAPTERS if n.startswith('ollama-')):
            with self.subTest(adapter=name):
                adapter = callers.get_caller(name)
                self.assertEqual(adapter.timeout, 900)
                reply = real_callers.finalize_reply(adapter, {}, error=TimeoutError('FIXTURE local timeout'))
                result = self.run_returned(self.cfg('timeout-%d' % index), reply)
                self.assertFalse(result['calls'][0]['complete'])
                self.assertIn('FIXTURE local timeout', result['calls'][0]['error'])

    def test_usage_overrun_keeps_first_answer_skips_that_sorter_and_runs_other_sorter(self):
        # The dry config and all disk outputs remain explicitly synthetic. Only
        # metadata on this fake is external-shaped, to exercise usage accounting.
        seen = []

        class UsageFixture(callers.DryRunCaller):
            name = 'fixture-usage-adapter'
            is_dry = False
            kind = 'openai'
            provider = 'fixture-provider'
            output_token_limit = callers.OUTPUT_TOKEN_LIMIT

            def call(self, conversation, env=None):
                seen.append(conversation.turn())
                reply = super().call(conversation, env=env)
                reply.record['usage_json'] = json.dumps({
                    'output_tokens': callers.OUTPUT_TOKEN_LIMIT + 1 if len(seen) == 1 else 10})
                return reply

        cfg = self.cfg('usage-stop', repeats=3,
                       sorters=[{'name': s, 'group': 'cloud', 'provider': 'fixture-provider'}
                                for s in ('S1', 'S2')])
        with patch.object(runner, 'get_caller', return_value=UsageFixture()):
            runner.run(cfg, env={})
        manifest = json.loads((Path(cfg['out_dir']) / 'manifest.json').read_text())
        budget = manifest['call_budget']
        stopped = [s for s, spec in budget['per_sorter'].items() if spec.get('stop')]
        self.assertEqual(len(stopped), 1)
        stopped = stopped[0]
        other = next(s for s in ('S1', 'S2') if s != stopped)
        self.assertEqual(len(seen), 7)
        self.assertEqual(budget['attempted']['total'], 7)
        self.assertEqual(budget['per_sorter'][stopped]['attempted'], 1)
        self.assertEqual(budget['per_sorter'][other]['attempted'], 6)
        results = {s: [json.loads((Path(cfg['out_dir']) / ('results/%s__r%d.json' % (s, r))).read_text())
                       for r in (1, 2, 3)] for s in (stopped, other)}
        retained = [row for row in results[stopped] if row['parse_ok']]
        self.assertEqual(len(retained), 1)
        self.assertEqual(len(retained[0]['rows']), 17)
        self.assertTrue(retained[0]['raw_reply'])
        self.assertFalse(retained[0]['turn2']['sent'])
        self.assertEqual(retained[0]['turn2']['not_sent_reason'], 'sorter_output_limit_exceeded')
        for row in results[stopped]:
            if row['parse_ok']:
                continue
            self.assertIsNone(row['raw_reply'])
            self.assertFalse(row['calls'][0]['sent'])
            self.assertEqual(row['calls'][0]['not_sent_reason'], 'sorter_output_limit_exceeded')
        self.assertTrue(all(row['parse_ok'] and row['turn2']['sent'] and row['turn2']['parse_ok']
                            for row in results[other]))


if __name__ == '__main__':
    unittest.main()
