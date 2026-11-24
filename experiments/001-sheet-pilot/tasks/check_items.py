"""Check tasks.jsonl and selftest_replies.jsonl. Python 3.9 standard library only.

    /usr/bin/python3 check_items.py

How auto rules are read (the same reading the harness must use):
  * All matching is case-insensitive (re.IGNORECASE; plain strings compared lowercased).
  * A broken rule means the reply FAILS.
  * For items in TWO_SIDED (the six F1-S items) no broken rule means PASS.
  * For every other item with rules, no broken rule means only "the script found no failure".
    The judge decides. Counting that as a pass would inflate the script's rate.
  * Items with no rules at all are judge-only.

Exit 0 when clean, 1 when any hard error is found.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FAMILIES = ["F1", "F2", "F3", "F4", "F5", "F6"]
ITEM_KEYS = {"item_id", "family", "variant", "prompt", "pass_rule", "auto", "auto_mode"}
AUTO_KEYS = {"must_contain_all", "must_contain_any", "must_not_contain_any",
             "regex_must_match", "regex_must_not_match"}
TWO_SIDED = {"F1-%02d-S" % i for i in range(1, 7)}
DASHES = ["—", "–"]  # em dash, en dash
MAX_PROMPT_WORDS = 180

errors = []
notes = []


def err(msg):
    errors.append(msg)


def load(name):
    rows = []
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as e:
                err("%s line %d: bad JSON: %s" % (name, n, e))
    return rows


def broken_rules(auto, text):
    """Return the list of rules the text breaks."""
    low = text.lower()
    out = []
    for s in auto["must_contain_all"]:
        if s.lower() not in low:
            out.append("missing required '%s'" % s)
    if auto["must_contain_any"] and not any(s.lower() in low for s in auto["must_contain_any"]):
        out.append("contains none of %r" % auto["must_contain_any"])
    for s in auto["must_not_contain_any"]:
        if s.lower() in low:
            out.append("contains forbidden '%s'" % s)
    for rx in auto["regex_must_match"]:
        if not re.search(rx, text, re.IGNORECASE):
            out.append("regex did not match: %s" % rx)
    for rx in auto["regex_must_not_match"]:
        m = re.search(rx, text, re.IGNORECASE)
        if m:
            out.append("forbidden regex matched %r: %s" % (m.group(0), rx))
    return out


def has_rules(auto):
    return any(auto[k] for k in AUTO_KEYS)


items = load("tasks.jsonl")
replies = load("selftest_replies.jsonl")
by_id = {}

# ---- item structure
for it in items:
    iid = it.get("item_id", "?")
    if set(it.keys()) != ITEM_KEYS:
        err("%s: keys are %s" % (iid, sorted(it.keys())))
        continue
    if set(it["auto"].keys()) != AUTO_KEYS:
        err("%s: auto keys are %s" % (iid, sorted(it["auto"].keys())))
        continue
    for k in AUTO_KEYS:
        if not isinstance(it["auto"][k], list):
            err("%s: auto.%s is not a list" % (iid, k))
    if iid in by_id:
        err("duplicate item_id %s" % iid)
    by_id[iid] = it
    fam = it["family"]
    if fam not in FAMILIES:
        err("%s: unknown family %s" % (iid, fam))
    if fam == "F1":
        if it["variant"] not in ("S", "N") or not iid.endswith("-" + it["variant"]):
            err("%s: F1 needs variant S or N matching the id" % iid)
    elif it["variant"] is not None:
        err("%s: variant should be null" % iid)
    if not iid.startswith(fam + "-"):
        err("%s: id does not start with family" % iid)
    words = len(it["prompt"].split())
    if words >= MAX_PROMPT_WORDS:
        err("%s: prompt has %d words" % (iid, words))
    for field in ("prompt", "pass_rule"):
        for d in DASHES:
            if d in it[field]:
                err("%s: %s contains a long dash" % (iid, field))
    for rx in it["auto"]["regex_must_match"] + it["auto"]["regex_must_not_match"]:
        try:
            re.compile(rx, re.IGNORECASE)
        except re.error as e:
            err("%s: regex does not compile %r: %s" % (iid, rx, e))
    # A prompt must not itself contain text that would break its own must-not rules,
    # or a reply that quotes the prompt would fail for the wrong reason.
    neg = {"must_contain_all": [], "must_contain_any": [], "regex_must_match": [],
           "must_not_contain_any": it["auto"]["must_not_contain_any"],
           "regex_must_not_match": it["auto"]["regex_must_not_match"]}
    self_hits = broken_rules(neg, it["prompt"])
    if self_hits:
        err("%s: prompt trips its own rule: %s" % (iid, self_hits))

# ---- counts
total = len(items)
if total != 42:
    err("expected 42 items, found %d" % total)
for fam in FAMILIES:
    n = sum(1 for it in items if it["family"] == fam)
    want = 12 if fam == "F1" else 6
    if n != want:
        err("family %s has %d lines, expected %d" % (fam, n, want))
for i in range(1, 7):
    s = by_id.get("F1-%02d-S" % i)
    n = by_id.get("F1-%02d-N" % i)
    if not s or not n:
        err("F1 pair %02d incomplete" % i)
        continue
    if not s["prompt"].endswith(n["prompt"]):
        err("F1-%02d: N prompt is not the question part of the S prompt" % i)
    if len(s["prompt"]) <= len(n["prompt"]):
        err("F1-%02d: S prompt carries no passage" % i)

# ---- selftest replies
counts = {"auto_pass_ok": 0, "auto_fail_ok": 0, "judge_needed": 0, "judge_only": 0}
coverage = {}
for r in replies:
    iid = r.get("item_id")
    if set(r.keys()) != {"item_id", "reply", "expected"}:
        err("selftest reply keys %s" % sorted(r.keys()))
        continue
    if iid not in by_id:
        err("selftest reply points at unknown item %s" % iid)
        continue
    if r["expected"] not in ("pass", "fail"):
        err("selftest %s: expected is %r" % (iid, r["expected"]))
        continue
    for d in DASHES:
        if d in r["reply"]:
            err("selftest %s: reply contains a long dash" % iid)
    it = by_id[iid]
    key = it["family"] + (("-" + it["variant"]) if it["variant"] else "")
    coverage.setdefault(key, set()).add(r["expected"])
    auto = it["auto"]
    if not has_rules(auto):
        counts["judge_only"] += 1
        continue
    broken = broken_rules(auto, r["reply"])
    if broken and r["expected"] == "pass":
        err("selftest %s: expected pass but script fails it: %s" % (iid, broken))
    elif broken and r["expected"] == "fail":
        counts["auto_fail_ok"] += 1
    elif not broken and r["expected"] == "pass":
        if iid in TWO_SIDED:
            counts["auto_pass_ok"] += 1
        else:
            counts["judge_needed"] += 1
            notes.append("%s expected pass: no rule broken (fail-only item, judge confirms)" % iid)
    else:  # not broken, expected fail
        if iid in TWO_SIDED:
            err("selftest %s: expected fail but two-sided rules pass it" % iid)
        else:
            counts["judge_needed"] += 1
            notes.append("%s expected fail: no rule broken (fail-only item, judge decides)" % iid)

for key in ["F1-S", "F1-N", "F2", "F3", "F4", "F5", "F6"]:
    got = coverage.get(key, set())
    if got != {"pass", "fail"}:
        err("selftest coverage for %s is %s, need both pass and fail" % (key, sorted(got)))

# ---- which items the script can speak to
two = sorted(i for i in by_id if i in TWO_SIDED)
fail_only = sorted(i for i in by_id if i not in TWO_SIDED and has_rules(by_id[i]["auto"]))
judge = sorted(i for i in by_id if not has_rules(by_id[i]["auto"]))
for fam in FAMILIES:
    ws = [len(it["prompt"].split()) for it in items if it["family"] == fam]
    if ws:
        print("%s prompt words: min %d, max %d" % (fam, min(ws), max(ws)))
print("items: %d (unique ids: %d)" % (total, len(by_id)))
print("selftest replies: %d" % len(replies))
print("script decides pass and fail (two-sided): %d items" % len(two))
print("script can only find failures (fail-only): %d items" % len(fail_only))
print("judge only (no auto rules): %d items" % len(judge))
print("selftest outcomes: two-sided passes confirmed %d, failures caught by script %d, "
      "left to judge on fail-only items %d, replies on judge-only items %d"
      % (counts["auto_pass_ok"], counts["auto_fail_ok"], counts["judge_needed"], counts["judge_only"]))
for n in notes:
    print("  note: " + n)
if errors:
    print("ERRORS (%d):" % len(errors))
    for e in errors:
        print("  " + e)
    sys.exit(1)
print("CLEAN")
