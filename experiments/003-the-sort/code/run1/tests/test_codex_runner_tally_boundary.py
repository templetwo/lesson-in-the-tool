"""HQ82850-authorized real-config boundary test with fake key/transport functions only.

All generated artifacts live in a freshly created FIXTURE-named candidate scratch directory.
The real-run Boolean flags exercise the tally boundary; this is not a real model run.
"""
import fakes_first  # Must install forbidden-I/O tripwires before importing the runner or adapters.

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import real_callers
import runner
from common import make_scratch_dir
from tally import compute
from test_two_turn_and_callers import Spies, reply_by_turn

BASE = Path(__file__).resolve().parents[1]


class RunnerTallyBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.assertNotIn('SORT_REAL_CALLS', os.environ)
        self.directory = Path(make_scratch_dir('FIXTURE-budget-boundary-'))
        self.addCleanup(shutil.rmtree, str(self.directory))
        self.addCleanup(lambda: self.assertNotIn('SORT_REAL_CALLS', os.environ))
        lines = ['FIXTURE line %d, not a real lesson.' % n for n in range(1, 18)]
        self.source = {'repo': 'FIXTURE-NO-REPO', 'commit_requested': 'FIXTURE-COMMIT', 'commit': 'f' * 40,
                       'path': 'FIXTURE-LINES.txt', 'blob_id': 'a' * 40,
                       'sha256': hashlib.sha256('\n'.join(lines).encode()).hexdigest(), 'lines': lines}
        self.cfg = json.loads((BASE / 'config_real.json').read_text())
        self.cfg.update(repo='FIXTURE-NO-REPO', commit='FIXTURE-COMMIT', lines_path='FIXTURE-LINES.txt',
                        homes_file=str(BASE / 'fixtures/homes_fixture.json'), deny_list=str(BASE / 'deny_list.txt'),
                        prompt_text=str(BASE / 'prompt_text.json'), out_dir=str(self.directory / 'run'))
        self.assertIs(self.cfg['dry_run'], False)
        self.assertEqual(self.cfg['caller'], 'by_sorter')
        self.spies = Spies(reply=reply_by_turn)

    def run_fixture(self):
        with patch.object(real_callers, '_open', fakes_first.tripwire('key file opener')), \
             patch.object(real_callers, '_urlopen', fakes_first.tripwire('network opener')), \
             patch.object(real_callers, 'read_key', self.spies.read_key), \
             patch.object(real_callers, 'http_post_json', self.spies.post), \
             patch.object(real_callers, 'clock', lambda: 'FIXTURE-NO-CLOCK'), \
             patch.object(runner, 'clock', lambda: 'FIXTURE-NO-CLOCK'), \
             patch.object(runner, 'load_lines', lambda *args: copy.deepcopy(self.source)):
            # HQ82850 explicitly permits this fake env dictionary; the process environment is never changed.
            return Path(runner.run(self.cfg, env={'SORT_REAL_CALLS': 'allow'}))

    def test_real_config_fake_run_is_accepted_by_tally_without_fixture_bypass(self):
        out = self.run_fixture()
        cfg = {'run_dir': str(out), 'sorters': self.cfg['sorters'], 'groups': self.cfg['groups'],
               'repeats': self.cfg['repeats'], 'cut_points_by_size': {'6': {'settled_min': 5, 'leaning_min': 4}},
               'bootstrap': {'seed': 1, 'draws': 10, 'level': 0.9},
               'real_callers': sorted(set(self.cfg['real_callers'].values()))}
        report, judgment = compute(cfg, allow_fixture=False)
        self.assertIs(report['inputs']['allow_fixture'], False)
        self.assertEqual(len(self.spies.posts), 48)
        self.assertEqual(report['groups']['cloud']['turn2'],
                         {'sent': 18, 'failed': 0, 'not_sent': 0, 'of_replies': 18})
        self.assertEqual(report['groups']['local']['turn2'],
                         {'sent': 6, 'failed': 0, 'not_sent': 0, 'of_replies': 6})
        self.assertIn('Fake sentence.', judgment)

    def test_every_saved_budget_avoids_reserved_boolean_marker(self):
        out = self.run_fixture()
        budgets = []
        markers = []
        def inspect(value, inside_budget=False):
            if isinstance(value, dict):
                for name, child in value.items():
                    if name == 'call_budget':
                        budgets.append(child)
                        inspect(child, True)
                    else:
                        if name == 'dry_run':
                            markers.append(child)
                            self.assertFalse(inside_budget, 'numeric ledger count reused the Boolean dry_run marker')
                            self.assertIs(child, False)
                        if inside_budget and name == 'category':
                            self.assertNotEqual(child, 'dry_run')
                        inspect(child, inside_budget)
            elif isinstance(value, list):
                for child in value:
                    inspect(child, inside_budget)
        for path in out.rglob('*.json'):
            inspect(json.loads(path.read_text()))
        self.assertEqual(len(budgets), 26)  # manifest + key + all 24 result checkpoints
        self.assertTrue(markers)
        for budget in budgets:
            self.assertEqual(budget['planned'].get('dry_fixture'), 0)
            self.assertEqual(budget['attempted'].get('dry_fixture'), 0)


if __name__ == '__main__':
    unittest.main()
