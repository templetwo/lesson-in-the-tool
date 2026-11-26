"""Recount the public Sort projections without Git, model calls or filesystem writes.

Run from any working directory with: python3 -B experiments/003-the-sort/tools/reproduce.py
This publication helper is new. The two frozen analysis implementations stay
separate; the runner is never executed. Public hashes verify public projections,
not the authenticity or completeness of withheld provider response bodies.
"""
from contextlib import contextmanager
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r'^[0-9a-f]{64}$')
VIOLATIONS = []


class ReplayError(Exception):
    pass


def require(ok, message):
    if not ok:
        raise ReplayError(message)


def beneath(path, root):
    return path == root or root in path.parents


def install_guard():
    require('SORT_REAL_CALLS' not in os.environ, 'SORT_REAL_CALLS must be absent, not merely empty')
    sys.dont_write_bytecode = True
    sys.pycache_prefix = None
    stdlib = {Path(sys.base_prefix).resolve(), Path(sys.prefix).resolve(), Path(os.__file__).resolve().parent}

    def audit(event, args):
        reason = None
        if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.exec', 'os.spawn'}:
            reason = 'network/subprocess access'
        elif event in {'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.truncate', 'os.link', 'os.symlink', 'os.chmod', 'os.chown', 'os.utime', 'os.setxattr', 'os.removexattr', 'os.chdir', 'os.putenv', 'os.unsetenv', 'os.kill', 'os.killpg', 'shutil.copyfile', 'shutil.copymode', 'shutil.copystat', 'shutil.rmtree', 'shutil.move'}:
            reason = 'filesystem/process mutation'
        elif event == 'open':
            path, mode, flags = args
            if (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (
                    isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
                reason = 'filesystem write'
            elif isinstance(path, (str, bytes, os.PathLike)):
                target = Path(os.fsdecode(path)).resolve()
                if target.name.startswith('key_sources') or target.name.endswith('.env'):
                    reason = 'credential-settings read'
                elif target != Path('/dev/urandom') and not beneath(target, ROOT) and not any(beneath(target, p) for p in stdlib):
                    reason = 'read outside the public experiment and Python standard library'
        if reason:
            VIOLATIONS.append(reason)
            raise ReplayError('Offline replay refused ' + reason)

    sys.addaudithook(audit)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key in ' + path.name)
            result[key] = value
        return result

    def nonfinite(value):
        raise ReplayError('non-finite JSON value in ' + path.name)

    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=nonfinite)


def different_paths(a, b, prefix=''):
    if type(a) is not type(b):
        return [prefix or '/']
    if isinstance(a, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            p = prefix + '/' + key
            out.extend([p] if key not in a or key not in b else different_paths(a[key], b[key], p))
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [prefix + '/length']
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in different_paths(x, y, prefix + '/' + str(i))]
    return [] if a == b else [prefix or '/']


def same(a, b, label):
    differences = different_paths(a, b)
    require(not differences, label + ' differs at ' + ', '.join(differences[:12]))


def no_collection(*args, **kwargs):
    raise ReplayError('collection entry point is forbidden during public replay')


@contextmanager
def edition_modules(edition):
    code = ROOT / 'code' / edition
    old_path = list(sys.path)
    sys.path[:0] = [str(code / 'tests'), str(code)]
    before = set(sys.modules)
    try:
        importlib.import_module('fakes_first')
        runner = importlib.import_module('runner')
        callers = importlib.import_module('callers')
        real = importlib.import_module('real_callers')
        runner.run = runner.smoke = runner.get_caller = no_collection
        callers.get_caller = no_collection
        real.Adapter.call = no_collection
        yield code, importlib.import_module('tally')
    finally:
        sys.path[:] = old_path
        for name in set(sys.modules) - before:
            module = sys.modules.get(name)
            filename = getattr(module, '__file__', None)
            if filename and beneath(Path(filename).resolve(), code):
                del sys.modules[name]


def verify_stimuli(code, run):
    key = read_json(run / 'key.json')
    sheet = ROOT / 'sources' / 'SHEET_SHORT_v2.md'
    require(key['lines_source']['sha256'] == digest(sheet), 'public sheet hash differs from run key')
    require(str(key['lines_source']['commit']).startswith('441752c'), 'unexpected source commit in run key')
    for field, name in [('homes_sha256', 'homes_real.json'), ('deny_list_sha256', 'deny_list.txt'),
                        ('prompt_text_sha256', 'prompt_text.json')]:
        require(key[field] == digest(code / name), name + ' hash differs from run key')
    lines = importlib.import_module('lines_loader').parse_numbered_lines(sheet.read_text(encoding='utf-8'))
    same([{'line_number': i + 1, 'text': text} for i, text in enumerate(lines)],
         [{'line_number': row['line_number'], 'text': row['text']} for row in key['lines']], 'key lesson text')
    homes, unused_hash = importlib.import_module('homes').load_homes(str(code / 'homes_real.json'))
    builder = importlib.import_module('prompt_builder')
    wording = builder.load_prompt_text(str(code / 'prompt_text.json'))
    deny = builder.load_deny_list(str(code / 'deny_list.txt'))
    attempts = 0
    for p in key['prompts']:
        require(type(p['line_seed']) is int and type(p['home_seed']) is int, 'non-integer per-trial seed')
        prompt = builder.build_prompt(lines, homes, p['line_seed'], p['home_seed'], deny, prompt_text=wording)
        stem = '%s__r%d.json' % (p['sorter'], p['repeat'])
        saved = read_json(run / 'prompts' / stem)
        result = read_json(run / 'results' / stem)
        same([p['sorter'], p['repeat']], [saved['sorter'], saved['repeat']], 'prompt identity')
        same(prompt.text, saved['text'], 'rebuilt sort prompt')
        same(prompt.question_text, saved['question_text'], 'rebuilt question prompt')
        same(prompt.home_order, p['home_order'], 'rebuilt home order')
        same([{'label': row['label'], 'line_number': row['line_number']} for row in prompt.key],
             [{'label': row['label'], 'line_number': row['line_number']} for row in p['labels']], 'rebuilt label map')
        for field, value in [('prompt_sha256', prompt.sha256), ('question_sha256', prompt.question_sha256)]:
            require(saved[field] == value and result[field] == value, field + ' does not bind prompt and result')
        require(result['prompt_file'] == 'prompts/' + stem, 'result prompt_file does not match its trial')
        attempts += sum(call.get('sent') is not False for call in result.get('calls', []))
    return {'trials': len(key['prompts']), 'reported_sent_calls_not_independently_checked': attempts}


def historical_commitments(obj, fields):
    for field in fields:
        if field in obj:
            require(isinstance(obj[field], str) and SHA256.fullmatch(obj[field]), 'invalid informational ' + field)
            del obj[field]


def normalize_tally(report, edition, computed):
    report = copy.deepcopy(report)
    report.pop('written_at', None)  # historical write time is not part of the recount
    inputs = report['inputs']
    historical_commitments(inputs, ('original_manifest_sha256', 'original_key_sha256', 'original_house_table_sha256'))
    run_label = 'records/' + edition
    if computed:
        require(Path(inputs['run_dir']).resolve() == ROOT / run_label, 'computed run path differs')
        inputs['run_dir'] = run_label
        if inputs['house_table'] is not None:
            require(Path(inputs['house_table']).resolve() == ROOT / 'code/run1/house_table.json', 'computed house table differs')
            inputs['house_table'] = 'code/run1/house_table.json'
    else:
        require(inputs['run_dir'] == run_label, 'published tally must name its public records path')
        require(inputs['house_table'] in (None, 'code/run1/house_table.json'), 'published house-table path is not canonical')
    return report


def replay_tally(edition, config_name):
    run = ROOT / 'records' / edition
    with edition_modules(edition) as (code, tally):
        cfg = read_json(code / config_name)
        cfg['run_dir'] = str(run)
        cfg.pop('out_dir', None)
        if cfg.get('house_table'):
            cfg['house_table'] = str(ROOT / 'code/run1/house_table.json')
        # compute verifies the exact public manifest inventory and every listed hash,
        # checks coverage/bindings, and reparses both visible answer turns.
        report, unused_judgment_text = tally.compute(cfg, need_out=False, allow_fixture=False)
        details = verify_stimuli(code, run)
        expected = read_json(ROOT / 'results' / (edition + '_tally.json'))
        same(normalize_tally(report, edition, True), normalize_tally(expected, edition, False), edition + ' tally')
        details.update(manifest_sha256=digest(run / 'manifest.json'), key_sha256=digest(run / 'key.json'),
                       summary_sha256=digest(ROOT / 'results' / (edition + '_tally.json')))
        return details


def replay_comparison():
    with edition_modules('side') as (code, unused_tally):
        compare = importlib.import_module('side_compare')
        cfg = read_json(code / 'compare_side_deepseek.json')
        cfg['reference_tally'] = str(ROOT / 'results/run1_tally.json')
        cfg['side_tally'] = str(ROOT / 'results/side_tally.json')
        expected = read_json(ROOT / 'results/comparison.json')
        cfg['reference_sha256'] = expected['sources']['reference']['sha256']
        # compute has no output writes; the historical out_dir is not used.
        actual = compare.compute(cfg)
        for name, label in [('reference', 'results/run1_tally.json'), ('side', 'results/side_tally.json')]:
            actual['sources'][name]['path'] = label
            source = expected['sources'][name]
            require(source['path'] in (label, Path(label).name), 'published comparison path differs')
            source['path'] = label
            historical_commitments(source, ('original_sha256',))
            historical = source.pop('original_reported_run_provenance', None)
            if historical is not None:
                require(isinstance(historical, dict) and set(historical) == {'run_dir', 'manifest_sha256', 'key_sha256'}, 'invalid original reported provenance schema')
                require(isinstance(historical['run_dir'], str) and historical['run_dir'].startswith('WITHHELD/'), 'original run path must remain withheld')
                for field in ('manifest_sha256', 'key_sha256'):
                    require(isinstance(historical[field], str) and SHA256.fullmatch(historical[field]), 'invalid original reported hash')
        note = expected.get('provenance_note')
        require(isinstance(note, str) and note.startswith(compare.PROVENANCE_NOTE), 'comparison provenance note lost its original boundary')
        # An added publication explanation is not an output of the original comparator.
        expected['provenance_note'] = compare.PROVENANCE_NOTE
        same(actual, expected, 'side comparison')
        return actual['counts']


def main():
    install_guard()
    result = {'run1': replay_tally('run1', 'tally_real.json'),
              'side': replay_tally('side', 'tally_side_deepseek.json'),
              'comparison': replay_comparison()}
    require(not VIOLATIONS, 'a forbidden boundary was attempted')
    result['verified'] = 'Public manifest bytes, rebuilt prompts/maps, visible-answer parsing, complete tally fields and side comparison.'
    result['excluded_from_equality'] = ['historical written_at', 'informational original_* hash commitments',
                                       'comparison original_reported_run_provenance', 'comparison provenance-note publication suffix']
    result['normalized'] = ['absolute computed run/house-table paths and absolute or summary-relative comparison paths to fixed public relative paths']
    result['limit'] = 'This checks agreement among the public files, not that they are what the models returned. It does not authenticate withheld original provider bodies or prove privacy clearance.'
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Do not echo model-written text or attempted private paths on a failed check.
        print('REPRODUCTION FAILED: %s' % (error if isinstance(error, ReplayError) else type(error).__name__), file=sys.stderr)
        raise SystemExit(1)
