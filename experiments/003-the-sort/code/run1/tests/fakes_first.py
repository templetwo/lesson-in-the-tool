"""Imported FIRST by every test module (2026-11-25, the two-turn and callers build).

1. If SORT_REAL_CALLS is present in this process's environment at all, the tests refuse to run: the import raises,
   so the whole test module fails loudly instead of running beside an armed switch.
2. Before any test runs, the four ways out of real_callers are replaced with tripwires: the key function, the key
   file opener, the transport, and urllib's opener. A test that reaches any of them without first installing its
   own fake fails with "a test reached the real ...". The originals are kept in REAL, so the guard tests can call
   the real key function and the real transport with the switch unset and prove they refuse before touching the
   (tripwired) opener or connection.

No test ever writes SORT_REAL_CALLS into os.environ. Tests that need the switch "on" pass a plain dict as `env`.
"""
import os

SWITCH = "SORT_REAL_CALLS"
if SWITCH in os.environ:
    raise RuntimeError("%s is set in this environment; the tests refuse to run with the switch present" % SWITCH)

REAL = {}


def tripwire(what):
    def f(*a, **k):
        raise AssertionError("a test reached the real %s; every test must install a fake first" % what)
    f.is_tripwire = True
    return f


def install():
    try:
        import real_callers
    except ImportError:  # the red run, before Part 2 existed
        return None
    if not REAL:
        REAL.update(read_key=real_callers.read_key, http_post_json=real_callers.http_post_json,
                    _urlopen=real_callers._urlopen, _open=real_callers._open)
    real_callers.read_key = tripwire("key function")
    real_callers.http_post_json = tripwire("transport")
    real_callers._urlopen = tripwire("urllib opener")
    real_callers._open = tripwire("key file opener")
    return real_callers


install()
