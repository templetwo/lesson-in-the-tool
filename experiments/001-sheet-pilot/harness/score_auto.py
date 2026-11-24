#!/usr/bin/env python3
"""Script scorer for the sheet test. The script is a partial second instrument; the blind
judge is the primary scorer (PREREG, Scoring).

Reads the tasks file and <run-dir>/raw.ndjson. Writes <run-dir>/auto_scores.ndjson,
one line per reply that has text: {"id", "verdict", "rule"}.

The verdict depends on the item's "auto_mode":
  two_sided  "pass" if every auto rule holds, "fail" if any is broken.
  fail_only  "fail" if any auto rule is broken, otherwise "no_verdict". No broken rule is NOT a pass.
  none       always "no_verdict" (any rules on the item are ignored).
An item with no auto_mode is treated as "none", with a WARNING line. A two_sided item with no
rules is a task-file error. Matching is case-insensitive.

This script never opens key.json. It sees only replies, by opaque id.
Python 3.9, standard library only.
"""
import argparse
import json
import os
import re
import sys

AUTO_KEYS = (
    "must_contain_all",
    "must_contain_any",
    "must_not_contain_any",
    "regex_must_match",
    "regex_must_not_match",
)
MODES = ("two_sided", "fail_only", "none")
VERDICTS = ("pass", "fail", "no_verdict")


def load_jsonl(path):
    """Load a JSON-lines file. Blank lines are skipped. A bad line raises with its line number."""
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except ValueError as e:
                raise ValueError("%s line %d is not valid JSON: %s" % (path, n, e))
    return out


def item_mode(t):
    """The item's auto_mode; a missing one counts as "none" (see mode_warnings)."""
    m = t.get("auto_mode")
    return "none" if m is None else m


def mode_warnings(tasks):
    """One WARNING line per item that has no auto_mode."""
    return ["WARNING: item %s has no auto_mode; treated as \"none\" (the script gives it no verdict)" % t.get("item_id")
            for t in tasks if isinstance(t, dict) and t.get("auto_mode") is None]


def n_rules(auto):
    auto = auto or {}
    return sum(len(auto.get(k) or []) for k in AUTO_KEYS)


def validate_tasks(tasks):
    """Return a list of problems with the task file. Empty list means it is usable."""
    problems = []
    seen = set()
    for i, t in enumerate(tasks, 1):
        where = "task line %d" % i
        if not isinstance(t, dict):
            problems.append("%s is not a JSON object" % where)
            continue
        iid = t.get("item_id")
        if not isinstance(iid, str) or not iid:
            problems.append("%s has no item_id" % where)
            continue
        where = "item %s" % iid
        if iid in seen:
            problems.append("%s appears more than once" % where)
        seen.add(iid)
        # Extra top-level keys are allowed (they change nothing).
        for k in ("family", "prompt", "pass_rule"):
            if not isinstance(t.get(k), str) or not t.get(k).strip():
                problems.append("%s has no %s" % (where, k))
        if t.get("variant") not in ("S", "N", None):
            problems.append("%s has variant %r (allowed: S, N, null)" % (where, t.get("variant")))
        mode = t.get("auto_mode")
        if mode is not None and mode not in MODES:
            problems.append("%s has auto_mode %r (allowed: %s)" % (where, mode, ", ".join(MODES)))
        problems.extend(validate_auto(t.get("auto"), where))
        if mode in ("two_sided", "fail_only") and n_rules(t.get("auto")) == 0:
            problems.append("%s is %s but has no auto rules" % (where, mode))
    return problems


def validate_auto(auto, where):
    """An unknown key or a bad regex is an error, never silently dropped."""
    problems = []
    if auto is None:
        return problems
    if not isinstance(auto, dict):
        return ["%s: auto is not an object" % where]
    for k, v in auto.items():
        if k not in AUTO_KEYS:
            problems.append("%s: unknown auto key %r (allowed: %s)" % (where, k, ", ".join(AUTO_KEYS)))
            continue
        if not isinstance(v, list) or not all(isinstance(x, str) and x != "" for x in v):
            problems.append("%s: auto.%s must be a list of non-empty strings" % (where, k))
            continue
        if k.startswith("regex_"):
            for pat in v:
                try:
                    re.compile(pat, re.IGNORECASE)
                except re.error as e:
                    problems.append("%s: auto.%s regex %r does not compile: %s" % (where, k, pat, e))
    return problems


def broken_rules(auto, reply):
    """Return (number of checks, list of broken checks). A must_contain_any list is one check."""
    auto = auto or {}
    lists = dict((k, auto.get(k) or []) for k in AUTO_KEYS)
    n_checks = sum(len(v) for k, v in lists.items() if k != "must_contain_any")
    n_checks += 1 if lists["must_contain_any"] else 0
    text = (reply or "").lower()
    fails = []
    for s in lists["must_contain_all"]:
        if s.lower() not in text:
            fails.append("must_contain_all: missing %r" % s)
    if lists["must_contain_any"]:
        if not any(s.lower() in text for s in lists["must_contain_any"]):
            fails.append("must_contain_any: none of %r" % (lists["must_contain_any"],))
    for s in lists["must_not_contain_any"]:
        if s.lower() in text:
            fails.append("must_not_contain_any: found %r" % s)
    for pat in lists["regex_must_match"]:
        if not re.search(pat, reply or "", re.IGNORECASE):
            fails.append("regex_must_match: no match for %r" % pat)
    for pat in lists["regex_must_not_match"]:
        if re.search(pat, reply or "", re.IGNORECASE):
            fails.append("regex_must_not_match: matched %r" % pat)
    return n_checks, fails


def score_reply(auto, reply, mode):
    """Return (verdict, rule). Assumes validate_tasks found no problems."""
    if mode == "none":
        return "no_verdict", "auto_mode none: the script gives no verdict on this item"
    n_checks, fails = broken_rules(auto, reply)
    if n_checks == 0:
        return "no_verdict", "no auto rules for this item"
    if fails:
        return "fail", "; ".join(fails)
    if mode == "two_sided":
        return "pass", "two_sided: all %d auto checks held" % n_checks
    if mode == "fail_only":
        return "no_verdict", "fail_only: no rule broken (%d checks), which is not a pass" % n_checks
    raise ValueError("unknown auto_mode %r" % (mode,))


def score_item(t, reply):
    return score_reply(t.get("auto"), reply, item_mode(t))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score replies with the auto rules. Never reads key.json.")
    ap.add_argument("--tasks", required=True, help="path to tasks.jsonl")
    ap.add_argument("--run-dir", required=True, help="folder holding raw.ndjson; auto_scores.ndjson is written here")
    a = ap.parse_args(argv)

    tasks = load_jsonl(a.tasks)
    problems = validate_tasks(tasks)
    if problems:
        print("TASK FILE PROBLEMS, nothing scored:")
        for p in problems:
            print("  " + p)
        return 2
    for w in mode_warnings(tasks):
        print(w)
    by_id = dict((t["item_id"], t) for t in tasks)

    raw = load_jsonl(os.path.join(a.run_dir, "raw.ndjson"))
    out_lines = []
    skipped_errors = 0
    unknown = []
    counts = dict((v, 0) for v in VERDICTS)
    for r in raw:
        if r.get("error") or r.get("reply") is None:
            skipped_errors += 1
            continue
        t = by_id.get(r.get("item_id"))
        if t is None:
            unknown.append("%s (item %s)" % (r.get("id"), r.get("item_id")))
            continue
        verdict, rule = score_item(t, r["reply"])
        counts[verdict] += 1
        out_lines.append(json.dumps({"id": r["id"], "verdict": verdict, "rule": rule}, ensure_ascii=False))
    if unknown:
        print("REPLIES FOR ITEMS NOT IN THE TASK FILE, nothing written:")
        for u in unknown:
            print("  " + u)
        return 2
    path = os.path.join(a.run_dir, "auto_scores.ndjson")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for line in out_lines:
            fh.write(line + "\n")
    os.replace(tmp, path)
    print("scored %d replies: pass %d, fail %d, no_verdict %d (left to the judge); skipped %d error records (no reply)"
          % (len(out_lines), counts["pass"], counts["fail"], counts["no_verdict"], skipped_errors))
    print("wrote " + path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
