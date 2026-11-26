"""Offline fixture persistence controls. Never enables or calls a real adapter."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
SCRATCH = BASE.parent / 'test2_stale/scratch/codex_fix_persistence'
sys.path.insert(0, str(BASE))
import callers
import runner
from common import Refuse


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.assertNotIn('SORT_REAL_CALLS', os.environ)
        SCRATCH.mkdir(parents=True, exist_ok=True)
        directory = tempfile.TemporaryDirectory(prefix='fixture-', dir=SCRATCH)
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.seen, self.returned = [], []
        lines = ['FIXTURE line %d, not a real lesson.' % n for n in range(1, 18)]
        src = {'repo': 'FIXTURE-NO-REPO', 'commit_requested': 'FIXTURE-COMMIT', 'commit': 'f' * 40,
               'path': 'FIXTURE-LINES.txt', 'blob_id': 'a' * 40,
               'sha256': hashlib.sha256('\n'.join(lines).encode()).hexdigest(), 'lines': lines}
        for name, replacement in (
                ('load_lines', lambda *args: copy.deepcopy(src)),
                ('clock', lambda: 'FIXTURE-NO-CLOCK'),
                ('inside_here', lambda value: SCRATCH in Path(value).resolve().parents)):
            mock = patch.object(runner, name, replacement)
            mock.start()
            self.addCleanup(mock.stop)

    def cfg(self, name='run', **over):
        cfg = {'dry_run': True, 'caller': 'dryrun', 'repo': 'FIXTURE-NO-REPO',
               'commit': 'FIXTURE-COMMIT', 'lines_path': 'FIXTURE-LINES.txt',
               'homes_file': str(BASE / 'fixtures/homes_fixture.json'),
               'deny_list': str(BASE / 'deny_list.txt'), 'prompt_text': str(BASE / 'prompt_text.json'),
               'sorters': [{'name': 'S1', 'group': 'cloud', 'provider': 'fixture-provider'}],
               'groups': {}, 'repeats': 1, 'master_seed': 5, 'out_dir': str(self.root / name)}
        cfg.update(over)
        return cfg

    def scripted(self, fail=None, before_second=None, broken_first=False):
        outer = self

        class FixtureCaller(callers.DryRunCaller):
            def call(self, conversation, env=None):
                outer.seen.append(copy.deepcopy(conversation.messages))
                turn = conversation.turn()
                if turn == 2:
                    if before_second is not None:
                        before_second()
                    if fail is not None:
                        raise fail('FIXTURE second-call interruption')
                reply = super().call(conversation, env=env)
                if turn == 1 and broken_first:
                    reply.text = 'FIXTURE malformed first reply'
                outer.returned.append((turn, reply.text, dict(reply.record)))
                return reply

        return FixtureCaller()

    def run_with(self, cfg, caller):
        def lookup(name, **kwargs):
            self.assertEqual(name, 'dryrun')
            self.assertEqual(kwargs, {}, 'model-match policy belongs only to real caller construction')
            return caller
        with patch.object(runner, 'get_caller', lookup):
            return runner.run(cfg, env={})

    def result(self, cfg):
        path = Path(cfg['out_dir']) / 'results/S1__r1.json'
        self.assertTrue(path.is_file(), 'returned first answer was not persisted')
        return json.loads(path.read_text())

    def test_first_answer_exists_before_second_call_starts(self):
        cfg = self.cfg()

        def inspect():
            result = self.result(cfg)
            self.assertEqual(result['persistence_state'], 'turn2_pending')
            self.assertEqual(result['raw_reply'], self.returned[0][1])
            self.assertTrue(result['parse_ok'])
            self.assertEqual(len(result['rows']), 17)
            self.assertEqual(len(result['calls']), 1)
            self.assertIsNone(result['turn2']['sent'])
            self.assertFalse((Path(cfg['out_dir']) / 'manifest.json').exists())

        self.run_with(cfg, self.scripted(before_second=inspect))

    def test_second_call_refusal_exception_and_baseexceptions_preserve_first_answer(self):
        for index, failure in enumerate((Refuse, RuntimeError, KeyboardInterrupt, SystemExit)):
            with self.subTest(failure=failure.__name__):
                self.seen.clear()
                self.returned.clear()
                cfg = self.cfg('interruption-%d' % index)
                with self.assertRaises(failure):
                    self.run_with(cfg, self.scripted(fail=failure))
                result = self.result(cfg)
                self.assertEqual(result['persistence_state'], 'turn2_pending')
                self.assertEqual(result['raw_reply'], self.returned[0][1])
                self.assertTrue(result['parse_ok'])
                self.assertEqual(len(result['calls']), 1)
                self.assertIsNone(result['turn2']['sent'])
                self.assertFalse((Path(cfg['out_dir']) / 'manifest.json').exists())

    def test_first_raw_answer_saved_before_its_parser_can_raise(self):
        cfg = self.cfg()
        with patch.object(runner, 'parse_sort_reply', side_effect=RuntimeError('FIXTURE parser failure')):
            with self.assertRaisesRegex(RuntimeError, 'parser failure'):
                self.run_with(cfg, self.scripted())
        result = self.result(cfg)
        self.assertEqual(result['persistence_state'], 'turn1_returned')
        self.assertEqual(result['raw_reply'], self.returned[0][1])
        self.assertIsNone(result['parse_ok'])
        self.assertEqual(len(result['calls']), 1)
        self.assertEqual(len(self.seen), 1)
        self.assertFalse((Path(cfg['out_dir']) / 'manifest.json').exists())

    def test_second_raw_answer_saved_before_its_parser_can_raise(self):
        cfg = self.cfg()
        with patch.object(runner, 'parse_question_reply', side_effect=RuntimeError('FIXTURE parser failure')):
            with self.assertRaisesRegex(RuntimeError, 'parser failure'):
                self.run_with(cfg, self.scripted())
        result = self.result(cfg)
        self.assertEqual(result['persistence_state'], 'turn2_returned')
        self.assertEqual(result['raw_reply'], self.returned[0][1])
        self.assertEqual(result['turn2']['raw_reply'], self.returned[1][1])
        self.assertTrue(result['turn2']['sent'])
        self.assertIsNone(result['turn2']['parse_ok'])
        self.assertEqual(len(result['calls']), 2)
        self.assertFalse((Path(cfg['out_dir']) / 'manifest.json').exists())

    def test_later_checkpoint_replacement_failure_preserves_first_answer(self):
        cfg = self.cfg()
        replace = os.replace
        count = [0]

        def fail_third(source, destination):
            count[0] += 1
            if count[0] == 3:
                raise OSError('FIXTURE later checkpoint replacement failure')
            return replace(source, destination)

        with patch.object(runner.os, 'replace', fail_third):
            with self.assertRaisesRegex(OSError, 'later checkpoint replacement failure'):
                self.run_with(cfg, self.scripted())
        result = self.result(cfg)
        self.assertEqual(result['persistence_state'], 'turn2_pending')
        self.assertEqual(result['raw_reply'], self.returned[0][1])
        self.assertEqual(len(result['calls']), 1)
        self.assertFalse((Path(cfg['out_dir']) / 'manifest.json').exists())

    def test_complete_result_has_both_answers_and_matching_final_manifest_hash(self):
        cfg = self.cfg()
        self.run_with(cfg, self.scripted())
        result = self.result(cfg)
        self.assertEqual(result['persistence_state'], 'complete')
        self.assertEqual(result['raw_reply'], self.returned[0][1])
        self.assertEqual(result['turn2']['raw_reply'], self.returned[1][1])
        self.assertEqual(len(result['calls']), 2)
        self.assertTrue(result['parse_ok'] and result['turn2']['parse_ok'])
        manifest = json.loads((Path(cfg['out_dir']) / 'manifest.json').read_text())
        entry = next(row for row in manifest['files'] if row['path'] == 'results/S1__r1.json')
        self.assertEqual(entry['sha256'], hashlib.sha256((Path(cfg['out_dir']) / entry['path']).read_bytes()).hexdigest())
        self.assertFalse(list(Path(cfg['out_dir']).rglob('*.checkpoint')))

    def test_unparsed_first_reply_finishes_without_a_second_call(self):
        cfg = self.cfg()
        self.run_with(cfg, self.scripted(broken_first=True))
        result = self.result(cfg)
        self.assertEqual(result['persistence_state'], 'complete')
        self.assertFalse(result['parse_ok'])
        self.assertEqual(result['turn2'], runner.turn2_not_sent(True))
        self.assertEqual(len(self.seen), 1)

    def test_model_match_default_is_recorded_true_and_false_is_explicit(self):
        for name, override, expected in (('default', {}, True), ('opt-out', {'require_model_match': False}, False)):
            with self.subTest(name=name):
                cfg = self.cfg(name, **override)
                self.run_with(cfg, self.scripted())
                key = json.loads((Path(cfg['out_dir']) / 'key.json').read_text())
                self.assertIs(key['require_model_match'], expected)

    def test_model_match_requires_strict_boolean(self):
        for value in (0, 1, None, 'true', []):
            with self.subTest(value=value):
                with self.assertRaisesRegex(Refuse, 'require_model_match must be a Boolean'):
                    runner.check_config(self.cfg(require_model_match=value))

    def test_only_real_caller_construction_receives_model_match_policy(self):
        class FixtureMetadata:
            is_dry = False
            name = 'fixture-adapter'
            provider = 'fixture-provider'

        for override, expected in (({}, True), ({'require_model_match': False}, False)):
            cfg = self.cfg(caller='by_sorter', dry_run=False,
                           real_callers={'S1': 'fixture-adapter'}, **override)
            with patch.object(runner, 'get_caller', return_value=FixtureMetadata()) as lookup:
                self.assertEqual(set(runner.check_config(cfg)), {'S1'})
                lookup.assert_called_once_with('fixture-adapter', require_model_match=expected,
                                               output_token_limit=19000)


if __name__ == '__main__':
    unittest.main()
