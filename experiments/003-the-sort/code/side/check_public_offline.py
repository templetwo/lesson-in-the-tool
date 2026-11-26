"""Public-export check helper, added after collection; not part of either original freeze.

Run with python3 -B check_public_offline.py from either code edition. This runs
only the four reviewed pure/fake modules named below, not the historical suite.
No Git repository, credential settings, saved run, or provider call is needed.
"""
from pathlib import Path
import json
import os
import sys
import unittest

if 'SORT_REAL_CALLS' in os.environ:
    raise SystemExit('Refusing: SORT_REAL_CALLS must be absent, not merely empty.')
sys.dont_write_bytecode = True
sys.pycache_prefix = None  # do not read a machine-specific external bytecode cache
HERE = Path(__file__).resolve().parent
MODULES = ('test_codex_callers', 'test_codex_call_budget',
           'test_codex_usage_stop', 'test_codex_output_limits')
violations = []
stdlib_roots = {Path(sys.base_prefix).resolve(), Path(sys.prefix).resolve(),
                Path(os.__file__).resolve().parent}


def beneath(path, root):
    return path == root or root in path.parents


def audit(event, args):
    reason = None
    if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.exec', 'os.spawn'}:
        reason = 'network or subprocess boundary'
    elif event in {'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.truncate', 'os.link', 'os.symlink', 'os.chmod', 'os.chown', 'os.utime', 'os.setxattr', 'os.removexattr', 'os.chdir', 'os.putenv', 'os.unsetenv', 'os.kill', 'os.killpg', 'shutil.copyfile', 'shutil.copymode', 'shutil.copystat', 'shutil.rmtree', 'shutil.move'}:
        reason = 'filesystem/process mutation'
    elif event == 'open':
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing:
            reason = 'filesystem write'
        elif isinstance(path, (str, bytes, os.PathLike)):
            target = Path(os.fsdecode(path)).resolve()
            if target.name.startswith('key_sources') or target.name.endswith('.env'):
                reason = 'credential-settings read'
            elif target != Path('/dev/urandom') and not beneath(target, HERE) and not any(beneath(target, p) for p in stdlib_roots):
                reason = 'read outside this code edition and Python standard library'
    if reason:
        # Do not print a possibly sensitive attempted path or argument.
        violations.append(reason)
        raise RuntimeError('Offline check refused: ' + reason)


sys.addaudithook(audit)
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'tests'))
import fakes_first  # installs key/transport tripwires before test-module imports

suite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'scope': 'four reviewed offline modules; not the whole historical suite',
                  'tests': result.testsRun, 'failures': len(result.failures),
                  'errors': len(result.errors), 'boundary_violations': violations,
                  'switch_absent': 'SORT_REAL_CALLS' not in os.environ}))
raise SystemExit(0 if result.wasSuccessful() and not violations else 1)
