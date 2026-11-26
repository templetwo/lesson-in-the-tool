"""Lines loader: reads a numbered file AT A GIVEN COMMIT and returns its seventeen lines.

Read only. It runs exactly three git commands, all with GIT_OPTIONAL_LOCKS=0 so git does not even refresh its
index: `rev-parse --verify <commit>^{commit}`, `show <full commit>:<path>` and `rev-parse <full commit>:<path>`.
It then recomputes the git blob id from the bytes `git show` gave and refuses unless it equals the id git stores,
which proves the bytes are the stored file and not a filtered or converted copy.

Parsing rule: a line that starts with digits, a dot and one space is an item. Only the digits, the dot and that one
space are removed; the rest is kept exactly. Refuses unless the items are numbered exactly 1 to N in order (N = 17 by
default), unless every item sits on one line, and unless nothing but blank lines follows the first item.
"""
import hashlib
import os
import re
import subprocess

from common import Refuse, sha256_bytes

ITEM = re.compile(r"^(\d+)\. (.*)$")


def parse_numbered_lines(text, expected=17):
    if "\r" in text:
        raise Refuse("the file holds a carriage return; lines cannot be taken exactly as written")
    items = []
    seen_item = False
    prev_was_item = False
    for n, raw in enumerate(text.split("\n"), start=1):
        m = ITEM.match(raw)
        if m:
            items.append((int(m.group(1)), m.group(2), n))
            seen_item = True
            prev_was_item = True
            continue
        if raw.strip() == "":
            prev_was_item = False
            continue
        if seen_item:
            if prev_was_item:
                raise Refuse("file line %d continues numbered item %d onto a second line" % (n, items[-1][0]))
            raise Refuse("file line %d is text between or after the numbered items: %r" % (n, raw[:60]))
    numbers = [i[0] for i in items]
    if numbers != list(range(1, len(numbers) + 1)):
        raise Refuse("items are not numbered 1, 2, 3 ... in order; found %s" % numbers)
    if len(items) != expected:
        raise Refuse("found %d numbered lines, expected exactly %d" % (len(items), expected))
    for num, body, n in items:
        if body.strip() == "":
            raise Refuse("item %d (file line %d) is empty" % (num, n))
    return [body for _, body, _ in items]


def _git(repo, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    proc = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, env=env)
    if proc.returncode != 0:
        raise Refuse("git %s failed: %s" % (" ".join(args), proc.stderr.decode("utf-8", "replace").strip()))
    return proc.stdout


def load_lines(repo, commit, path, expected=17):
    if os.path.isabs(path) or ".." in path.split("/"):
        raise Refuse("path must be relative to the repository and must not climb out of it: %r" % path)
    if not re.match(r"^[0-9a-fA-F]{7,40}$", commit):
        raise Refuse("commit must be a hash of 7 to 40 hex characters, not a branch or tag name: %r" % commit)
    full = _git(repo, "rev-parse", "--verify", "--quiet", commit + "^{commit}").decode().strip()
    if not re.match(r"^[0-9a-f]{40}$", full):
        raise Refuse("commit %r did not resolve to one full hash" % commit)
    data = _git(repo, "show", "%s:%s" % (full, path))
    stored_id = _git(repo, "rev-parse", "%s:%s" % (full, path)).decode().strip()
    got_id = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
    if got_id != stored_id:
        raise Refuse("the bytes git show gave (blob %s) are not the stored file (blob %s)" % (got_id, stored_id))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise Refuse("file is not UTF-8: %s" % e)
    lines = parse_numbered_lines(text, expected)
    return {
        "repo": os.path.abspath(repo),
        "commit_requested": commit,
        "commit": full,
        "path": path,
        "sha256": sha256_bytes(data),
        "blob_id": stored_id,
        "lines": lines,
    }
