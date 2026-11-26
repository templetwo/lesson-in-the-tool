"""Shared pieces for the Test 1 plumbing. Python 3.9, standard library only."""
import hashlib
import json
import os
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(HERE, "scratch")
DRYRUN = "DRYRUN"


class Refuse(Exception):
    """A refusal. The message says what was wrong. Nothing is repaired."""


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def make_scratch_dir(prefix):
    """A fresh temporary folder inside this folder's scratch/, never the system temp folder."""
    os.makedirs(SCRATCH, exist_ok=True)
    return tempfile.mkdtemp(prefix=prefix, dir=SCRATCH)


def inside_here(path):
    """True when path resolves to somewhere inside this folder."""
    real = os.path.realpath(path)
    here = os.path.realpath(HERE)
    return real == here or real.startswith(here + os.sep)


def clock():
    """The time, read from /bin/date, in the house's form: 2026-11-24 21:07:07 EST."""
    out = subprocess.run(["/bin/date", "+%Y-%m-%d %H:%M:%S %Z"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise Refuse("%s not found: %s" % (what, path))
    except (ValueError, UnicodeDecodeError) as e:
        raise Refuse("%s is not valid JSON (%s): %s" % (what, e, path))


def write_json(path, obj):
    """Write JSON with keys in insertion order, so "dry_run" stays the first key."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
