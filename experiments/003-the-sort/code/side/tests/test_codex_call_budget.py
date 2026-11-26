"""Pure fake-caller budget tests. Never enables a switch or runs the runner/smoke entry points."""
import ast
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import runner
from callers import Conversation, Reply
from common import Refuse


class FakeCaller:
    is_dry = False

    def __init__(self, name, kind, failure=False, output_token_limit=19000):
        self.name, self.kind, self.provider = name, kind, kind
        self.output_token_limit = output_token_limit
        self.failure, self.calls = failure, []

    def call(self, conversation, env=None):
        self.calls.append(copy.deepcopy(conversation.messages))
        if self.failure:
            raise ValueError('FAKE failed attempt')
        return Reply('FAKE reply', {'caller': self.name})


def fixture(repeats=3, output_token_limit=19000):
    kinds = ['anthropic', 'anthropic', 'openai', 'openai', 'xai', 'deepseek', 'ollama', 'ollama']
    callers = {'FAKE-%d' % i: FakeCaller('FAKE-adapter-%d' % i, kind, output_token_limit=output_token_limit)
               for i, kind in enumerate(kinds)}
    cfg = {'caller': 'by_sorter', 'dry_run': False, 'require_model_match': True, 'repeats': repeats,
           'sorters': [{'name': name, 'group': 'FAKE-group', 'provider': caller.provider}
                       for name, caller in callers.items()],
           'real_callers': {name: caller.name for name, caller in callers.items()}}
    return cfg, callers


def prepared(cfg, callers, smoke=False):
    helper = getattr(runner, 'budget_callers', None)
    # The baseline runner delegates directly: preserve that behavior for assertion-based red receipts.
    return helper(cfg, callers, smoke=smoke) if helper else (callers, None)


def receipt(budget):
    return budget.receipt() if budget is not None else {}


def attempt(caller):
    return caller.call(Conversation([{'role': 'user', 'content': 'FAKE'}], []), env={})


class CallBudgetTests(unittest.TestCase):
    def test_plan_counts_all_eight_sorters_and_billing_categories(self):
        cfg, raw = fixture()
        wrapped, budget = prepared(cfg, raw)
        self.assertEqual(receipt(budget).get('planned'),
                         {'total': 48, 'external': 36, 'anthropic': 12, 'other_external': 24, 'local': 12, 'dry_fixture': 0})
        self.assertEqual(receipt(budget).get('output_token_limit'), 19000)
        self.assertEqual(sum(len(c.calls) for c in raw.values()), 0)

    def test_call_49_is_refused_before_delegate(self):
        cfg, raw = fixture()
        wrapped, budget = prepared(cfg, raw)
        for caller in wrapped.values():
            for unused in range(6):
                attempt(caller)
        with self.assertRaisesRegex(Refuse, 'call budget'):
            attempt(wrapped['FAKE-0'])
        self.assertEqual(sum(len(c.calls) for c in raw.values()), 48)

    def test_unused_other_model_allowance_cannot_fund_extra_expensive_call(self):
        cfg, raw = fixture()
        wrapped, budget = prepared(cfg, raw)
        for unused in range(6):
            attempt(wrapped['FAKE-0'])
        with self.assertRaisesRegex(Refuse, 'call budget'):
            attempt(wrapped['FAKE-0'])
        self.assertEqual(len(raw['FAKE-0'].calls), 6)
        self.assertEqual(len(raw['FAKE-2'].calls), 0)

    def test_duplicate_adapters_share_aggregate_without_losing_sorter_limits(self):
        cfg, raw = fixture()
        raw['FAKE-1'] = raw['FAKE-0']
        cfg['real_callers']['FAKE-1'] = raw['FAKE-0'].name
        wrapped, budget = prepared(cfg, raw)
        for name in ('FAKE-0', 'FAKE-1'):
            for unused in range(6):
                attempt(wrapped[name])
        with self.assertRaisesRegex(Refuse, 'call budget'):
            attempt(wrapped['FAKE-1'])
        record = receipt(budget).get('per_adapter', {}).get(raw['FAKE-0'].name, {})
        self.assertEqual((record.get('planned'), record.get('attempted')), (12, 12))
        self.assertEqual(len(raw['FAKE-0'].calls), 12)

    def test_failed_attempts_consume_allowance_and_are_not_retried(self):
        cfg, raw = fixture(repeats=1)
        raw['FAKE-0'].failure = True
        wrapped, budget = prepared(cfg, raw)
        for unused in range(2):
            with self.assertRaisesRegex(ValueError, 'FAKE failed'):
                attempt(wrapped['FAKE-0'])
        with self.assertRaisesRegex(Refuse, 'call budget'):
            attempt(wrapped['FAKE-0'])
        self.assertEqual(len(raw['FAKE-0'].calls), 2)
        self.assertEqual(receipt(budget).get('attempted', {}).get('total'), 2)

    def test_reservation_is_visible_inside_delegate_before_it_fails(self):
        cfg, raw = fixture(repeats=1)
        wrapped, budget = prepared(cfg, raw)
        seen = []
        def observe(conversation, env=None):
            seen.append(receipt(budget).get('attempted', {}).get('total'))
            raise ValueError('FAKE observation')
        raw['FAKE-0'].call = observe
        with self.assertRaises(ValueError):
            attempt(wrapped['FAKE-0'])
        self.assertEqual(seen, [1])

    def test_skipped_questions_reduce_attempts_without_changing_plan(self):
        cfg, raw = fixture()
        wrapped, budget = prepared(cfg, raw)
        for caller in wrapped.values():
            for unused in range(3):
                attempt(caller)
        result = receipt(budget)
        self.assertEqual(result.get('planned', {}).get('total'), 48)
        self.assertEqual(result.get('attempted', {}).get('total'), 24)
        self.assertEqual(result.get('attempted', {}).get('external'), 18)

    def test_smoke_has_own_one_per_sorter_budget_and_2000_limit(self):
        cfg, raw = fixture(repeats=99, output_token_limit=2000)
        wrapped, budget = prepared(cfg, raw, smoke=True)
        result = receipt(budget)
        self.assertEqual(result.get('planned'),
                         {'total': 8, 'external': 6, 'anthropic': 2, 'other_external': 4, 'local': 2, 'dry_fixture': 0})
        self.assertEqual(result.get('mode'), 'smoke')
        self.assertEqual(result.get('output_token_limit'), 2000)
        attempt(wrapped['FAKE-0'])
        with self.assertRaisesRegex(Refuse, 'call budget'):
            attempt(wrapped['FAKE-0'])

    def test_plan_scales_from_config_and_receipts_are_detached(self):
        cfg, raw = fixture(repeats=1)
        wrapped, budget = prepared(cfg, raw)
        first = receipt(budget)
        self.assertEqual(first.get('planned', {}).get('total'), 16)
        if budget is not None:
            first['planned']['total'] = 999
            self.assertEqual(budget.receipt()['planned']['total'], 16)

    def test_unknown_adapter_kind_refuses_before_fake_call(self):
        cfg, raw = fixture()
        raw['FAKE-0'].kind = 'FAKE-unknown'
        with self.assertRaisesRegex(Refuse, 'call budget'):
            prepared(cfg, raw)
        self.assertEqual(sum(len(c.calls) for c in raw.values()), 0)

    def test_actual_check_real_callers_passes_main_limit_to_factory(self):
        cfg, raw = fixture()
        captures = []
        by_name = {caller.name: caller for caller in raw.values()}
        def factory(name, **kwargs):
            captures.append(kwargs)
            return by_name[name]
        with patch.object(runner, 'get_caller', factory):
            runner.check_real_callers(cfg)
        self.assertEqual([call.get('output_token_limit') for call in captures], [19000] * 8)

    def test_source_wraps_both_entrypoints_and_keeps_budget_receipts(self):
        tree = ast.parse((BASE / 'runner.py').read_text())
        funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        for name in ('run', 'smoke'):
            calls = [node.func.id for node in ast.walk(funcs[name])
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
            self.assertIn('budget_callers', calls, name)
        source = ast.get_source_segment((BASE / 'runner.py').read_text(), funcs['run'])
        self.assertGreaterEqual(source.count('"call_budget"'), 2)


if __name__ == '__main__':
    unittest.main()
