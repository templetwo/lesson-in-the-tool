"""Compare one descriptive singleton tally with a hash-pinned reference tally.

Usage: python3 -B side_compare.py --config CONFIG.json
Paths resolve from the current working directory, like the runner's config paths.
Only the two tally files are read; their reported run provenance is copied, not
revalidated. Explicit fixture/status/dry markers are refused; this cannot detect
forged unmarked reports, authenticate the side run, or reconstruct its majorities.
No new classes, agreement statistics, guesses, or complete-case denominator are
computed. The reference's existing leaning/contested labels are highlighted.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

from common import Refuse, inside_here


CONFIG_KEYS = {'reference_tally', 'reference_sha256', 'reference_group', 'side_tally',
               'side_group', 'side_sorter', 'out_dir'}
SHA256 = re.compile(r'^[0-9a-f]{64}$')
REFERENCE_CLASSES = {None, 'settled', 'leaning', 'contested'}
HOMES = {'tool', 'check', 'gate', 'harness', 'retrieval', 'judgment'}
PROVENANCE_NOTE = ('Tally byte hashes were measured here. Run directory, manifest and key hashes below are '
                   'reported by those tallies; raw runs were not revalidated.')


def _text(value):
    return isinstance(value, str) and bool(value) and value == value.strip() and not any(ord(c) < 32 for c in value)


def _digest(value):
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Refuse('duplicate JSON object key: %r' % key)
        out[key] = value
    return out


def _json(raw, where):
    def nonfinite(value):
        raise Refuse('%s contains a non-finite JSON value: %s' % (where, value))
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_constant=nonfinite)
    except (ValueError, UnicodeDecodeError) as error:
        raise Refuse('%s is not valid JSON: %s' % (where, error))


def _config(cfg):
    if not isinstance(cfg, dict) or set(cfg) != CONFIG_KEYS:
        raise Refuse('comparison config must contain exactly %s' % ', '.join(sorted(CONFIG_KEYS)))
    if not all(_text(value) for value in cfg.values()) or not _digest(cfg['reference_sha256']):
        raise Refuse('comparison config needs nonempty trimmed strings and a lowercase reference SHA256')
    reference, side = Path(cfg['reference_tally']).resolve(), Path(cfg['side_tally']).resolve()
    if reference == side:
        raise Refuse('reference and side tally paths must differ')
    try:
        if reference.exists() and side.exists() and os.path.samefile(str(reference), str(side)):
            raise Refuse('reference and side tally paths name the same file')
    except OSError as error:
        raise Refuse('cannot check tally paths: %s' % error)
    return reference, side


def _markers(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ('dry_run', 'allow_fixture', 'fixture') and child is not False:
                raise Refuse('tally has a non-false %s marker' % key)
            if key == 'status':
                raise Refuse('tally has a status marker; fixture/status reports are not comparison inputs')
            _markers(child)
    elif isinstance(value, list):
        for child in value:
            _markers(child)
    elif isinstance(value, str) and value.upper() in ('DRYRUN', 'FIXTURE, NOT DATA', 'FAKE, NOT DATA'):
        raise Refuse('tally contains a fixture/fake marker')


def _read(path, pinned=None):
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise Refuse('cannot read tally %s: %s' % (path, error))
    digest = hashlib.sha256(raw).hexdigest()
    if pinned is not None and digest != pinned:
        raise Refuse('reference tally SHA256 differs from its pinned value')
    data = _json(raw, str(path))
    if not isinstance(data, dict) or data.get('dry_run') is not False:
        raise Refuse('tally must explicitly say dry_run false')
    inputs = data.get('inputs')
    if not isinstance(inputs, dict) or inputs.get('allow_fixture') is not False:
        raise Refuse('tally inputs must explicitly say allow_fixture false')
    if not _text(inputs.get('run_dir')) or not all(_digest(inputs.get(k)) for k in ('manifest_sha256', 'key_sha256')):
        raise Refuse('tally needs reported run directory and manifest/key SHA256 values')
    _markers(data)
    return data, {'path': str(path), 'sha256': digest,
                  'reported_run_provenance': {k: inputs[k] for k in ('run_dir', 'manifest_sha256', 'key_sha256')}}


def _group(report, name):
    groups = report.get('groups')
    if not isinstance(groups, dict) or name not in groups or not isinstance(groups[name], dict):
        raise Refuse('tally has no group %r' % name)
    group = groups[name]
    members, size = group.get('sorters'), group.get('size')
    if not isinstance(members, list) or not members or not all(_text(s) for s in members) \
            or len(set(members)) != len(members) or type(size) is not int or size != len(members):
        raise Refuse('group %r has inconsistent sorter membership or size' % name)
    rows = group.get('per_line')
    if not isinstance(rows, list) or not rows:
        raise Refuse('group %r needs nonempty per_line rows' % name)
    numbers = [row.get('line_number') if isinstance(row, dict) else None for row in rows]
    if not all(type(n) is int and n > 0 for n in numbers) or len(set(numbers)) != len(numbers):
        raise Refuse('group %r has missing, invalid or duplicate line numbers' % name)
    return group, numbers


def _home(value):
    return isinstance(value, str) and value in HOMES


def _row(row, members):
    majority = row.get('sorter_majority')
    if not isinstance(majority, dict) or set(majority) != set(members) \
            or not all(home is None or _home(home) for home in majority.values()):
        raise Refuse('line %s has malformed sorter majorities' % row['line_number'])
    counts = Counter(home for home in majority.values() if home is not None)
    count = max(counts.values()) if counts else 0
    modal = sorted(home for home, total in counts.items() if total == count)
    reported = row.get('modal_homes')
    if not isinstance(reported, list) or not all(_home(home) for home in reported) \
            or len(reported) != len(set(reported)) or sorted(reported) != modal \
            or type(row.get('modal_count')) is not int or row['modal_count'] != count \
            or row.get('count_text') != '%d of %d' % (count, len(members)):
        raise Refuse('line %s has inconsistent modal homes/counts' % row['line_number'])
    return modal


def _singleton(report, name, sorter, group):
    if set(report['groups']) != {name} or group['sorters'] != [sorter] or group['size'] != 1:
        raise Refuse('side tally must contain exactly the selected singleton group')
    settings = report.get('settings')
    roster = settings.get('sorters') if isinstance(settings, dict) else None
    if not isinstance(roster, list) or len(roster) != 1 or not isinstance(roster[0], dict) \
            or roster[0].get('name') != sorter or roster[0].get('group') != name:
        raise Refuse('side tally settings must name only the selected sorter and group')
    declared_groups = settings.get('groups')
    if not isinstance(declared_groups, dict) or set(declared_groups) - {name}:
        raise Refuse('side tally settings declare another group')
    if not isinstance(group.get('per_sorter'), dict) or set(group['per_sorter']) != {sorter}:
        raise Refuse('side per_sorter membership differs from the singleton')
    if group.get('agreement') != {} or 'class_counts' not in group or group['class_counts'] is not None \
            or 'cut_points' not in group or group['cut_points'] is not None:
        raise Refuse('side singleton must have empty agreement and no classes or cut points')


def compute(cfg):
    """Read exactly two tally files and produce a deterministic descriptive object."""
    reference_path, side_path = _config(cfg)
    reference, reference_source = _read(reference_path, cfg['reference_sha256'])
    side, side_source = _read(side_path)
    reference_group, reference_numbers = _group(reference, cfg['reference_group'])
    side_group, side_numbers = _group(side, cfg['side_group'])
    _singleton(side, cfg['side_group'], cfg['side_sorter'], side_group)
    if side_numbers != reference_numbers:
        raise Refuse('reference and side must contain exactly the same ordered line numbers')
    rows, counts = [], {'match': 0, 'different': 0, 'missing': 0, 'of': len(reference_numbers)}
    for ref, other in zip(reference_group['per_line'], side_group['per_line']):
        modal = _row(ref, reference_group['sorters'])
        if len(modal) != 1:
            raise Refuse('reference line %s has a tied or missing modal home' % ref['line_number'])
        label = ref.get('class')
        if 'class' not in ref or not isinstance(label, (str, type(None))) or label not in REFERENCE_CLASSES:
            raise Refuse('reference line has an invalid reported class')
        _row(other, side_group['sorters'])
        if 'class' not in other or other['class'] is not None:
            raise Refuse('side singleton line must not have a class')
        home = other['sorter_majority'][cfg['side_sorter']]
        result = 'missing' if home is None else 'match' if home == modal[0] else 'different'
        counts[result] += 1
        rows.append({'line_number': ref['line_number'], 'reference_home': modal[0],
                     'reference_class': label, 'reference_attention': label in ('leaning', 'contested'),
                     'side_home': home, 'result': result})
    return {'format': 'sort-side-comparison-v1', 'dry_run': False, 'descriptive_only': True,
            'reference_group': cfg['reference_group'], 'side_group': cfg['side_group'],
            'side_sorter': cfg['side_sorter'],
            'sources': {'reference': reference_source, 'side': side_source},
            'provenance_note': PROVENANCE_NOTE,
            'comparison_note': ('All reference lines remain in the denominator, including missing side majorities. '
                                'Reference classes are copied labels, not new side classes or scored guesses.'),
            'counts': counts, 'match_fraction': {'numerator': counts['match'], 'denominator': counts['of']},
            'rows': rows}


def _output(path):
    out = Path(path)
    if not inside_here(str(out)):
        raise Refuse('comparison out_dir is outside this code folder')
    if out.is_symlink() or (out.exists() and (not out.is_dir() or any(out.iterdir()))):
        raise Refuse('comparison out_dir must be new or empty and not a symlink')
    return out


def run(cfg):
    _config(cfg)
    out = _output(cfg['out_dir'])
    comparison = compute(cfg)
    # Recheck immediately before writes; exclusive creation never overwrites a result.
    out = _output(str(out))
    try:
        out.mkdir(parents=True, exist_ok=True)
        with (out / 'comparison.json').open('x', encoding='utf-8') as stream:
            json.dump(comparison, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
    except OSError as error:
        raise Refuse('could not write comparison: %s' % error)
    return comparison


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    args = parser.parse_args(argv)
    try:
        try:
            cfg = _json(Path(args.config).read_bytes(), 'comparison config')
        except OSError as error:
            raise Refuse('cannot read comparison config: %s' % error)
        result = run(cfg)
    except Refuse as error:
        print('REFUSED: %s' % error)
        return 2
    counts = result['counts']
    print('Descriptive comparison: matches {match} of {of}; different {different}; missing {missing}'.format(**counts))
    print('line | reference home | side majority | result | reference class')
    for row in result['rows']:
        print('%s%s | %s | %s | %s | %s' % ('*' if row['reference_attention'] else '', row['line_number'],
              row['reference_home'], row['side_home'] or '(missing)', row['result'], row['reference_class'] or '-'))
    print('* marks reference leaning/contested labels; no side classes or guesses are scored.')
    print(PROVENANCE_NOTE)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
