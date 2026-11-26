"""Synthetic tally files only; no model/credential calls or run reconstruction."""
import fakes_first  # Must precede production imports.

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from common import Refuse
import side_compare


BASE = Path(__file__).resolve().parents[1]
SCRATCH = BASE / 'scratch/side_compare_tests'


def reports():
    members = ['R%d' % n for n in range(6)]
    values = [['check'] * 6, ['tool'] * 4 + ['check', 'gate'], ['check'] * 3 + ['tool'] * 2 + ['gate']]
    ref_rows = []
    for number, (homes, label) in enumerate(zip(values, ['settled', 'leaning', 'contested']), 1):
        home, count = ('check', 6) if number == 1 else ('tool', 4) if number == 2 else ('check', 3)
        ref_rows.append({'line_number': number, 'sorter_majority': dict(zip(members, homes)),
                         'modal_homes': [home], 'modal_count': count, 'count_text': '%d of 6' % count,
                         'class': label})
    side_rows = [{'line_number': i, 'sorter_majority': {'SIDE': home},
                  'modal_homes': [home] if home else [], 'modal_count': 1 if home else 0,
                  'count_text': '1 of 1' if home else '0 of 1', 'class': None}
                 for i, home in enumerate(['check', 'judgment', None], 1)]

    def report(group, sorters, rows, singleton):
        return {'dry_run': False, 'inputs': {'allow_fixture': False, 'run_dir': '/UNREAD-TEST-PROVENANCE',
                 'manifest_sha256': '1' * 64, 'key_sha256': '2' * 64},
                'settings': {'sorters': [{'name': s, 'group': group, 'provider': 'test-provider'} for s in sorters],
                             'groups': {}, 'repeats': 3, 'cut_points_by_size': {}},
                'groups': {group: {'sorters': sorters, 'size': len(sorters), 'per_line': rows,
                   'per_sorter': {s: {} for s in sorters}, 'agreement': {} if singleton else {'reported': True},
                   'class_counts': None if singleton else {'settled': 1, 'leaning': 1, 'contested': 1},
                   'cut_points': None if singleton else {'settled_min': 5, 'leaning_min': 4}}}}
    return report('cloud', members, ref_rows, False), report('side', ['SIDE'], side_rows, True)


class SideComparisonTests(unittest.TestCase):
    def setUp(self):
        self.assertNotIn('SORT_REAL_CALLS', os.environ)
        self.addCleanup(lambda: self.assertNotIn('SORT_REAL_CALLS', os.environ))
        SCRATCH.mkdir(parents=True, exist_ok=True)
        directory = tempfile.TemporaryDirectory(prefix='FIXTURE-', dir=str(SCRATCH))
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.reference, self.side = reports()
        self.reference_path = self.directory / 'reference.json'
        self.side_path = self.directory / 'side.json'
        self.save()

    def save(self):
        self.reference_path.write_text(json.dumps(self.reference) + '\n')
        self.side_path.write_text(json.dumps(self.side) + '\n')

    def cfg(self):
        return {'reference_tally': str(self.reference_path),
                'reference_sha256': hashlib.sha256(self.reference_path.read_bytes()).hexdigest(),
                'reference_group': 'cloud', 'side_tally': str(self.side_path),
                'side_group': 'side', 'side_sorter': 'SIDE', 'out_dir': str(self.directory / 'comparison')}

    def reject(self, cfg=None):
        cfg = cfg or self.cfg()
        with self.assertRaises(Refuse):
            side_compare.run(cfg)
        self.assertFalse((self.directory / 'comparison/comparison.json').exists())

    def test_match_different_missing_keep_all_lines_and_reference_labels(self):
        result = side_compare.compute(self.cfg())
        self.assertEqual(result['counts'], {'match': 1, 'different': 1, 'missing': 1, 'of': 3})
        self.assertEqual(result['match_fraction'], {'numerator': 1, 'denominator': 3})
        self.assertEqual([r['result'] for r in result['rows']], ['match', 'different', 'missing'])
        self.assertEqual([r['reference_class'] for r in result['rows']], ['settled', 'leaning', 'contested'])
        self.assertEqual([r['reference_attention'] for r in result['rows']], [False, True, True])
        self.assertFalse(any('side_class' in r for r in result['rows']))

    def test_actual_seventeen_line_shape_never_drops_missing(self):
        for report, group in [(self.reference, 'cloud'), (self.side, 'side')]:
            prototype = report['groups'][group]['per_line']
            report['groups'][group]['per_line'] = [dict(copy.deepcopy(prototype[(n-1) % 3]), line_number=n)
                                                  for n in range(1, 18)]
        self.save()
        result = side_compare.compute(self.cfg())
        self.assertEqual(len(result['rows']), 17)
        self.assertEqual(result['counts'], {'match': 6, 'different': 6, 'missing': 5, 'of': 17})
        self.assertEqual(result['match_fraction']['denominator'], 17)

    def test_provenance_hashes_tally_bytes_and_labels_run_hashes_as_reported(self):
        result = side_compare.compute(self.cfg())
        for which, path in [('reference', self.reference_path), ('side', self.side_path)]:
            src = result['sources'][which]
            self.assertEqual(src['path'], str(path.resolve()))
            self.assertEqual(src['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(src['reported_run_provenance']['manifest_sha256'], '1' * 64)
            self.assertEqual(src['reported_run_provenance']['key_sha256'], '2' * 64)
        self.assertIn('not revalidated', result['provenance_note'])

    def test_cli_is_deterministic_and_preserves_both_inputs(self):
        cfg = self.cfg(); config = self.directory / 'config.json';config.write_text(json.dumps(cfg))
        before = [p.read_bytes() for p in (self.reference_path, self.side_path)]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(side_compare.main(['--config', str(config)]), 0)
        saved = json.loads((Path(cfg['out_dir']) / 'comparison.json').read_text())
        self.assertEqual(saved, side_compare.compute(cfg))
        self.assertIn('matches 1 of 3; different 1; missing 1', output.getvalue())
        self.assertIn('reference leaning/contested', output.getvalue())
        self.assertEqual(before, [p.read_bytes() for p in (self.reference_path, self.side_path)])
        self.assertEqual(sorted(p.name for p in Path(cfg['out_dir']).iterdir()), ['comparison.json'])

    def test_only_two_tallies_are_opened_for_compute(self):
        original = Path.read_bytes
        seen = []
        cfg = self.cfg()
        def read(path):
            seen.append(path.resolve())
            self.assertIn(path.resolve(), [self.reference_path.resolve(), self.side_path.resolve()])
            return original(path)
        with patch.object(Path, 'read_bytes', read):
            side_compare.compute(cfg)
        self.assertEqual(seen, [self.reference_path.resolve(), self.side_path.resolve()])

    def test_provenance_path_word_is_not_an_explicit_fixture_status(self):
        # Genuine runner/tally integration uses honestly named synthetic scratch
        # paths. Marker checks are structural, not a claim to detect forged data.
        self.reference['inputs']['run_dir'] = '/scratch/FIXTURE-reference-run'
        self.side['inputs']['run_dir'] = '/scratch/FIXTURE-side-run'
        self.save()
        self.assertEqual(side_compare.compute(self.cfg())['counts']['of'], 3)

    def test_config_exact_keys_strings_and_reference_digest(self):
        for change in [{'extra': True}, {'reference_group': ''}, {'side_sorter': ' SIDE'},
                       {'reference_sha256': 'bad'}, {'reference_sha256': '0' * 64}, {'side_tally': None}]:
            with self.subTest(change=change):
                cfg = self.cfg();cfg.update(change);self.reject(cfg)
        cfg = self.cfg();del cfg['side_group'];self.reject(cfg)

    def test_identical_path_and_alias_are_refused(self):
        cfg = self.cfg();cfg['side_tally'] = cfg['reference_tally'];self.reject(cfg)
        alias = self.directory / 'alias.json';alias.symlink_to(self.reference_path)
        cfg['side_tally'] = str(alias);self.reject(cfg)

    def test_fixture_status_or_nonfalse_flags_are_refused(self):
        for target in ('reference', 'side'):
            for mutate in [lambda d: d.update(dry_run=True), lambda d: d.update(dry_run=0),
                           lambda d: d.update(status='FIXTURE, NOT DATA'), lambda d: d.update(status=None),
                           lambda d: d['inputs'].update(allow_fixture=True),
                           lambda d: d['inputs'].update(allow_fixture=0), lambda d: d.update(fixture=True)]:
                with self.subTest(target=target, mutation=mutate):
                    self.reference, self.side = reports();mutate(getattr(self, target));self.save();self.reject()

    def test_side_must_be_exactly_one_sorter_and_one_group_everywhere(self):
        mutations = [lambda d: d['groups'].update(extra=copy.deepcopy(d['groups']['side'])),
                     lambda d: d['groups']['side'].update(size=2),
                     lambda d: d['groups']['side'].update(size=True),
                     lambda d: d['groups']['side'].update(sorters=['SIDE', 'EXTRA']),
                     lambda d: d['settings']['sorters'].append({'name': 'EXTRA', 'group': 'side'}),
                     lambda d: d['settings']['sorters'][0].update(group='other'),
                     lambda d: d['groups']['side']['per_sorter'].update(EXTRA={})]
        for mutate in mutations:
            self.reference, self.side = reports();mutate(self.side);self.save();self.reject()

    def test_side_cannot_carry_classes_cut_points_or_agreement(self):
        for change in [{'agreement': {'alpha': 1}}, {'class_counts': {}}, {'cut_points': {}},
                       {'class_counts': {'settled': 3}}]:
            self.reference, self.side = reports();self.side['groups']['side'].update(change);self.save();self.reject()
        self.reference, self.side = reports();self.side['groups']['side']['per_line'][0]['class'] = 'settled'
        self.save();self.reject()

    def test_missing_duplicate_reordered_or_mismatched_lines_refuse(self):
        for mutate in [lambda rows: rows.pop(), lambda rows: rows.append(copy.deepcopy(rows[0])),
                       lambda rows: rows.reverse(), lambda rows: rows[0].update(line_number=99),
                       lambda rows: rows[0].update(line_number=True), lambda rows: rows.clear()]:
            self.reference, self.side = reports();mutate(self.side['groups']['side']['per_line']);self.save();self.reject()

    def test_reference_modal_must_be_single_and_match_counts(self):
        for change in [{'modal_homes': []}, {'modal_homes': ['check', 'gate']}, {'modal_homes': ['gate']},
                       {'modal_count': True}, {'modal_count': 7}, {'modal_count': 5}, {'modal_homes': ['']},
                       {'class': 'invented'}, {'sorter_majority': {'R0': 'check'}}]:
            self.reference, self.side = reports();self.reference['groups']['cloud']['per_line'][0].update(change)
            self.save();self.reject()

    def test_side_majority_modal_count_and_home_must_agree(self):
        for change in [{'modal_homes': []}, {'modal_homes': ['tool']}, {'modal_count': 0}, {'modal_count': True},
                       {'sorter_majority': {'SIDE': ''}}, {'sorter_majority': {'SIDE': []}},
                       {'sorter_majority': {'SIDE': 'DRYRUN'}}, {'count_text': '3 of 3'}]:
            self.reference, self.side = reports();self.side['groups']['side']['per_line'][0].update(change)
            self.save();self.reject()

    def test_unknown_home_refuses_even_when_internal_counts_agree(self):
        row = self.side['groups']['side']['per_line'][0]
        row.update(sorter_majority={'SIDE': 'banana'}, modal_homes=['banana'])
        self.save();self.reject()
        self.reference, self.side = reports()
        row = self.reference['groups']['cloud']['per_line'][0]
        row.update(sorter_majority={s: 'banana' for s in row['sorter_majority']}, modal_homes=['banana'])
        self.save();self.reject()

    def test_missing_group_or_reported_provenance_refuses(self):
        cfg = self.cfg();cfg['reference_group'] = 'missing';self.reject(cfg)
        self.side['inputs']['manifest_sha256'] = None;self.save();self.reject()

    def test_occupied_or_outside_output_refuses_without_changing_inputs(self):
        cfg = self.cfg();out = Path(cfg['out_dir']);out.mkdir();sentinel = out / 'keep';sentinel.write_text('KEEP')
        self.reject(cfg);self.assertEqual(sentinel.read_text(), 'KEEP')
        cfg['out_dir'] = '/tmp/FIXTURE-side-compare-outside';self.reject(cfg)
        cfg['out_dir'] = str(self.reference_path);self.reject(cfg)

    def test_cli_refusal_is_nonzero_and_writes_no_comparison(self):
        cfg = self.cfg();cfg['reference_sha256'] = '0' * 64
        config = self.directory / 'config.json';config.write_text(json.dumps(cfg))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(side_compare.main(['--config', str(config)]), 2)
        self.assertIn('REFUSED:', output.getvalue())
        self.assertFalse(Path(cfg['out_dir']).exists())


if __name__ == '__main__':
    unittest.main()
