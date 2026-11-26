"""Freeze helper, in the house's FREEZE.json format (as in experiments/001b-judge-lean/FREEZE.json at 441752c):
a JSON object with sorted keys and one-space indent, no final newline, holding "experiment", "files" (relative path
to sha256, computed here by program, never typed), "frozen_at" (read from /bin/date) and "frozen_by". With
--inventory it also holds "inventory": the folders whose every file was listed.

Usage:
  /usr/bin/python3 -B freeze.py write  --root DIR --out FREEZE.json --experiment NAME --frozen-by WHO
                                       [--inventory FOLDER ...] [FILE ...]
  /usr/bin/python3 -B freeze.py verify --root DIR [--expect-sha256 HASH] FREEZE.json

write refuses: a missing file; a path that is absolute, climbs out of root, or resolves outside root once links are
followed; a listed path that is itself a symbolic link (and, in an inventory folder, any link at all, file or
folder); two spellings of one file (paths are normalised first, so "a.txt" and "./a.txt" are one entry; on this
Mac's case-blind volume "a.txt" and "A.txt" are one file, and so is any other spelling that resolves to the same
real path); the freeze file itself; and an existing freeze file (a freeze is written once). It prints the sha256 of
the freeze file it wrote, so that hash can be kept somewhere else.

WHAT verify PROVES, AND WHAT IT DOES NOT (fix round, 2026-11-25):
  It proves that every file listed in FREEZE.json is present, is not a link, stays inside root, and has the listed
  sha256. On its own it does NOT notice an unlisted new file, an entry removed from FREEZE.json, or FREEZE.json
  rewritten with fresh hashes. Two additions narrow that:
  - inventory: freeze written with --inventory FOLDER records every file under FOLDER, and verify refuses any file
    under it that is not listed. That also catches a removed entry for a file under such a folder. It does not
    catch a removed "inventory" key: that is a rewrite of FREEZE.json.
  - --expect-sha256 HASH: verify refuses unless FREEZE.json itself has that sha256, so a hash kept somewhere else
    (a commit, a Stack record, a message) anchors the whole manifest. Without it a rewritten FREEZE.json passes.
"""
import argparse
import json
import os
import re
import sys

from common import Refuse, sha256_file, clock

LIMITS = [
    "LIMITS: verify proves only that every file listed in FREEZE.json is present, is not a link, stays inside root",
    "  and has the listed sha256. On its own it does not notice an unlisted new file, an entry removed from",
    "  FREEZE.json, or FREEZE.json rewritten with fresh hashes. A freeze written with --inventory refuses unlisted",
    "  files under its named folders; only --expect-sha256 with a hash kept elsewhere catches a rewritten manifest.",
]


def _norm(p, allow_root=False):
    """Normalise a listed path. Refuses an empty, absolute or climbing path ('..' anywhere, as before)."""
    if not isinstance(p, str) or not p:
        raise Refuse("path %r is empty or not text" % (p,))
    if os.path.isabs(p) or ".." in p.replace("\\", "/").split("/"):
        raise Refuse("path %r is absolute or climbs out of root" % p)
    q = os.path.normpath(p)
    if q == "." and not allow_root:
        raise Refuse("path %r names the root itself, not a file" % p)
    return q


def _inside(root, full):
    real, top = os.path.realpath(full), os.path.realpath(root)
    return real == top or real.startswith(top + os.sep)


def _identity(root, q):
    """Two spellings are one entry when their normalised paths match without case, or their real paths do."""
    return {"name:" + q.casefold(), "real:" + os.path.realpath(os.path.join(root, q)).casefold()}


def _check_file(root, q):
    full = os.path.join(root, q)
    if os.path.islink(full):
        raise Refuse("listed path %s is a symbolic link; links are never frozen" % q)
    if not _inside(root, full):
        raise Refuse("listed path %s resolves outside the root once links are followed" % q)
    if not os.path.isfile(full):
        raise Refuse("file to freeze not found: %s" % q)
    return full


def _walk_inventory(root, folder, skip_real):
    """Every file under folder, as normalised root-relative paths. Refuses any link inside it, file or folder."""
    top = os.path.join(root, folder)
    if os.path.islink(top) or not os.path.isdir(top) or not _inside(root, top):
        raise Refuse("inventory folder %s is not a real folder inside the root" % folder)
    found = []
    for d, dirs, fs in os.walk(top):
        for n in sorted(dirs + fs):
            full = os.path.join(d, n)
            rel = os.path.normpath(os.path.relpath(full, root))
            if os.path.islink(full):
                raise Refuse("inventory folder %s holds a symbolic link: %s" % (folder, rel))
            if n in fs and os.path.realpath(full) != skip_real:
                found.append(rel)
    return found


def write_freeze(root, files, out_path, experiment, frozen_by, inventory=()):
    if os.path.exists(out_path):
        raise Refuse("%s already exists; a freeze is written once" % out_path)
    if not files and not inventory:
        raise Refuse("no files given")
    out_real = os.path.realpath(out_path)
    seen, listed = set(), []
    for f in files:
        q = _norm(f)
        if os.path.realpath(os.path.join(root, q)) == out_real:
            raise Refuse("the freeze file cannot list itself")
        ident = _identity(root, q)
        if ident & seen:
            raise Refuse("a file is listed twice: %r is another spelling of a path already listed" % f)
        _check_file(root, q)
        seen |= ident
        listed.append(q)
    inv = []
    for folder in inventory:
        fq = _norm(folder, allow_root=True)
        if fq in inv:
            raise Refuse("inventory folder %s is named twice" % fq)
        inv.append(fq)
        for q in _walk_inventory(root, fq, out_real):
            ident = _identity(root, q)
            if ident & seen:
                continue  # already listed by name or by an overlapping inventory folder
            _check_file(root, q)
            seen |= ident
            listed.append(q)
    if not listed:
        raise Refuse("no files given (the inventory folders are empty)")
    hashes = {q: sha256_file(os.path.join(root, q)) for q in listed}
    obj = {"experiment": experiment, "files": hashes, "frozen_at": clock(), "frozen_by": frozen_by}
    if inv:
        obj["inventory"] = sorted(inv)
    with open(out_path, "x", encoding="utf-8") as fh:
        json.dump(obj, fh, sort_keys=True, indent=1, ensure_ascii=False)
    return obj


def verify_freeze(freeze_path, root, expect_sha256=None):
    """Returns a list of problems; an empty list means every check passed. See LIMITS for what that proves."""
    if expect_sha256 is not None:
        got = sha256_file(freeze_path)
        if got != expect_sha256:
            return ["%s has sha256 %s, not the expected %s; it is not the anchored manifest, so nothing else was "
                    "checked" % (freeze_path, got, expect_sha256)]
    with open(freeze_path, encoding="utf-8") as fh:
        obj = json.load(fh)
    files = obj.get("files")
    if not isinstance(files, dict) or not files:
        return ["freeze file has no files map"]
    problems, seen, names = [], set(), set()
    for f, want in sorted(files.items()):
        try:
            q = _norm(f)
        except Refuse as e:
            problems.append(str(e))
            continue
        if q != f:
            problems.append("listed path %r is not in normal form (%r)" % (f, q))
            continue
        ident = _identity(root, q)
        if ident & seen:
            problems.append("listed twice: %s is another spelling of a listed path" % f)
            continue
        seen |= ident
        names.add(q)
        full = os.path.join(root, q)
        if os.path.islink(full):
            problems.append("symbolic link: %s (links are never frozen)" % q)
        elif not _inside(root, full):
            problems.append("resolves outside the root: %s" % q)
        elif not os.path.isfile(full):
            problems.append("missing: %s" % q)
        elif sha256_file(full) != want:
            problems.append("changed: %s (frozen %s, now %s)" % (q, want, sha256_file(full)))
    inv = obj.get("inventory")
    if inv is not None:
        if not isinstance(inv, list) or not inv:
            return problems + ["inventory is not a non-empty list of folders"]
        for folder in inv:
            try:
                fq = _norm(folder, allow_root=True)
                found = _walk_inventory(root, fq, os.path.realpath(freeze_path))
            except Refuse as e:
                problems.append(str(e))
                continue
            for q in found:
                if q not in names:
                    problems.append("unlisted file under inventory folder %s: %s" % (fq, q))
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--root", required=True)
    w.add_argument("--out", required=True)
    w.add_argument("--experiment", required=True)
    w.add_argument("--frozen-by", required=True)
    w.add_argument("--inventory", action="append", default=[])
    w.add_argument("files", nargs="*")
    v = sub.add_parser("verify")
    v.add_argument("--root", required=True)
    v.add_argument("--expect-sha256")
    v.add_argument("freeze")
    a = ap.parse_args(argv)
    if a.cmd == "write":
        try:
            obj = write_freeze(a.root, a.files, a.out, a.experiment, a.frozen_by, inventory=a.inventory)
        except Refuse as e:
            print("REFUSED: %s" % e)
            return 2
        print("wrote %s: %d files, frozen_at %s%s" % (a.out, len(obj["files"]), obj["frozen_at"],
                                                    "; inventory %s" % obj["inventory"] if "inventory" in obj else ""))
        print("sha256 of %s: %s (keep it somewhere else; give it to verify --expect-sha256)"
              % (a.out, sha256_file(a.out)))
        return 0
    for line in LIMITS:
        print(line)
    if a.expect_sha256 is not None and not re.match(r"^[0-9a-f]{64}$", a.expect_sha256):
        print("REFUSED: --expect-sha256 must be 64 lowercase hex characters")
        return 2
    problems = verify_freeze(a.freeze, a.root, expect_sha256=a.expect_sha256)
    for p in problems:
        print("VERIFY FAILED: %s" % p)
    if problems:
        return 1
    print("ANCHOR OK: FREEZE.json has the expected sha256" if a.expect_sha256 else
          "NOT ANCHORED: no --expect-sha256 given, so a rewritten FREEZE.json would also pass")
    print("VERIFY OK: every listed file matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
