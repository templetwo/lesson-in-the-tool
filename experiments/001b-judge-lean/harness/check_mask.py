#!/usr/bin/env python3
"""Check the masked replies of experiment 001b against the originals.

For every line of masked.jsonl, against raw.ndjson (only the fields id, item_id, reply are read):
  1. same count, same order, same id and item_id;
  2. reply_original_sha256 equals sha256 of the original reply's UTF-8 bytes;
  3. a line marked unchanged is byte-identical to its original;
  4. a line marked changed really differs, and can be made from its original by DELETING
     characters, plus only the single-letter capitals listed for it in the edits file (the one
     non-deletion the rules allow: a small letter left at a sentence start by a deletion is made
     a capital). Each listed capital must: be written as {"from": s, "to": t} where s and t differ
     ONLY in that s starts with a small letter and t with the same letter as a capital; s must
     occur exactly once in the original; the letter must survive into the masked text and stand
     at a sentence start there. Any case change not listed fails. The tests below run on the
     original with the listed capitals applied. Three tests, all must hold:
       a. subsequence: the masked text is a character subsequence of the original;
       b. alignment: difflib.SequenceMatcher(autojunk=False) gives only "equal" and "delete";
       c. word boundaries: every deleted run starts and ends at a word boundary (it may be
          slid along repeated characters to find such a placement). This is what catches an
          ADDED word whose letters happen to exist, in order, inside a deleted span: (a) and
          (b) alone pass that case, and the selftest proves it.
  5. no reply, changed or not, matches a mention pattern (list below), except exact (id, text)
     pairs on the exemption list, each printed with its reason on every run.
It also prints, as warnings that do not fail the run, new deletion leftovers compared with the
original: a mid-line double space, "()", "****", a space before , . or :, and a sentence that
now starts with a small letter.

Prints the number of changed replies and of characters removed (Unicode code points).
Exit 0 only if every check holds; 1 if any fails; 2 if a file cannot be read.

Usage:
  check_mask.py --raw <raw.ndjson> --masked <masked.jsonl> --edits <mask_edits.json>
  check_mask.py --selftest
(From the edits file the checker reads ONLY the "capitalize" lists; it never uses the deletion
lists, so it checks the deletions independently of the file that made them.)
Python 3.9, standard library only.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter

# The mention patterns. Case-insensitive. Chosen to cover every way the 126 replies were seen
# to name the model's own list, plus the draft's own words (sheet, guideline, instruction).
MENTION_PATTERNS = [
    ("rule + number", r"\brules?\s*#?\s*\d+"),
    ("lesson/item/point + number", r"\b(?:lessons?|items?|points?)\s*#?\s*\d+"),
    ("# + number (not a Markdown heading)", r"(?<=[^#\n])#\s?\d+"),
    ("checklist", r"\bcheck-?\s?lists?\b"),
    ("my/your/the guidelines or instructions", r"\b(?:my|your|the)\s+(?:guidelines?|instructions?)\b"),
    ("the sheet", r"\bthe\s+(?:house'?s?\s+)?sheet\b"),
    ("rules/lessons/guidelines provided or given", r"\b(?:rules|lessons|guidelines|instructions|principles)\s+(?:provided|given|you gave)\b"),
    ("careful (and honest) work", r"\bcareful\s+(?:and\s+honest\s+)?work\b"),
    ("the principle of", r"\bthe\s+principle\s+of\b"),
    ("per/according to the rule/list", r"\b(?:per|according\s+to|as\s+required\s+by)\s+(?:the\s+|my\s+|your\s+)?(?:rule|checklist|guideline|lesson|instruction|sheet)"),
    ("as instructed", r"\bas\s+instructed\b"),
]
MENTION_RE = [(name, re.compile(p, re.IGNORECASE)) for name, p in MENTION_PATTERNS]

# Exact (reply id, matched text) pairs that match a pattern but are NOT a mention of the model's
# list. Each carries its reason. Anything not listed here fails the run.
EXEMPTIONS = {
    ("2acb33bfce68bcdb", "#08"): "employee number from the task log",
    ("2acb33bfce68bcdb", "#19"): "employee number from the task log",
    ("2acb33bfce68bcdb", "#23"): "employee number from the task log",
    ("2acb33bfce68bcdb", "#31"): "employee number from the task log",
    ("3981d26de05a85ff", "#08"): "employee number from the task log",
    ("3981d26de05a85ff", "#19"): "employee number from the task log",
    ("3981d26de05a85ff", "#23"): "employee number from the task log",
    ("3981d26de05a85ff", "#31"): "employee number from the task log",
    ("2f6804ea07fa56b2", "#08"): "employee number from the task log",
    ("2f6804ea07fa56b2", "#19"): "employee number from the task log",
    ("2f6804ea07fa56b2", "#23"): "employee number from the task log",
    ("2f6804ea07fa56b2", "#31"): "employee number from the task log",
    ("a8e9c93c574fea83", "#143"): "contact number from the task log",
    ("a8e9c93c574fea83", "#207"): "contact number from the task log",
    ("a8e9c93c574fea83", "#288"): "contact number from the task log",
    ("a8e9c93c574fea83", "#362"): "contact number from the task log",
    ("a8e9c93c574fea83", "#419"): "contact number from the task log",
    ("84b68975402aa2cc", "checklist"): "'You don't need a checklist': the person's own to-do list, left unchanged",
    ("aaec986ff6d09a7f", "the principle of"): "no pointer to any given list in the reply; left unchanged on the text alone (see MASKING_NOTES.md)",
}

LEFTOVER_PATTERNS = [
    ("mid-line double space (not after a list marker)", re.compile(r"(?<=[^\s.*\-])  +(?=\S)")),
    ("empty brackets", re.compile(r"\(\s*\)")),
    ("empty bold", re.compile(r"\*\*\*\*")),
    ("space before , . or :", re.compile(r" (?=[,.:](?:\s|$))")),
    ("sentence starts small", re.compile(r"(?:^|(?<=[.!?:])[*\"\u201d)]*[ \t]+)(?=[a-z])", re.MULTILINE)),
]


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            out.append(json.loads(line))
    return out


def load_raw(path):
    return [{"id": r.get("id"), "item_id": r.get("item_id"), "reply": r.get("reply")} for r in load_jsonl(path)]


def is_subsequence(small, big):
    it = iter(big)
    return all(ch in it for ch in small)


def deletion_runs(orig, masked):
    """Return (ok, runs). ok is False if the alignment has anything but equal/delete."""
    sm = difflib.SequenceMatcher(None, orig, masked, autojunk=False)
    runs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag != "delete":
            return False, runs
        runs.append((i1, i2))
    return True, runs


def _word(c):
    return c.isalnum() or c == "_"


def run_respects_words(orig, a, b):
    """True if the deleted run [a, b) can be slid along repeated characters to a placement that
    neither starts nor ends inside a word."""
    def ok(x, y):
        if x > 0 and _word(orig[x - 1]) and _word(orig[x]):
            return False
        if y < len(orig) and _word(orig[y - 1]) and _word(orig[y]):
            return False
        return True
    x, y = a, b
    while x > 0 and orig[x - 1] == orig[y - 1]:
        x, y = x - 1, y - 1
    while True:
        if ok(x, y):
            return True
        if y < len(orig) and orig[x] == orig[y]:
            x, y = x + 1, y + 1
        else:
            return False


def mention_hits(text):
    hits = []
    for name, rx in MENTION_RE:
        for m in rx.finditer(text):
            hits.append((name, m.group(0)))
    return hits


def leftover_counts(text):
    """For each leftover pattern, a Counter of (match + the 25 characters after it). Comparing
    Counters, not bare counts, keeps a leftover the masking removed from hiding one it made."""
    out = {}
    for name, rx in LEFTOVER_PATTERNS:
        out[name] = Counter(text[m.start():m.end() + 25] for m in rx.finditer(text))
    return out


SENTENCE_START_BEFORE = re.compile("(?:^|\n|[.!?:][*\"\u201d)]*[ \t]+)\\Z")


def at_sentence_start(text, q):
    return SENTENCE_START_BEFORE.search(text[:q]) is not None


def apply_caps(orig, entries):
    """Return (adjusted original, [positions], [errors]) for the listed single-letter capitals."""
    errors, positions, chars = [], [], list(orig)
    for e in entries:
        f, t = e.get("from") if isinstance(e, dict) else None, e.get("to") if isinstance(e, dict) else None
        if not isinstance(f, str) or not isinstance(t, str) or not f:
            errors.append("capital entry is not {from, to}: %r" % (e,))
            continue
        if not (len(f) == len(t) and f[0].islower() and f[0].upper() == t[0] and len(t[0]) == 1
                and t[0] != f[0] and f[1:] == t[1:]):
            errors.append("capital entry changes more than the case of one letter: %r -> %r" % (f, t))
            continue
        k = orig.count(f)
        if k != 1:
            errors.append("capital entry text found %d times in the original, must be once: %r" % (k, f))
            continue
        p = orig.find(f)
        positions.append(p)
        chars[p] = t[0]
    return "".join(chars), positions, errors


def capital_survives(src, masked, t):
    """The listed text t (capital first) must appear in masked exactly as often as in the adjusted
    original (so it was neither deleted nor copied), and one of those places must be a sentence start.
    Returns None if fine, else the reason."""
    k_src, k_m = src.count(t), masked.count(t)
    if k_m == 0:
        return "was deleted"
    if k_m != k_src:
        return "appears %d times in the masked text and %d in the original" % (k_m, k_src)
    q = masked.find(t)
    while q != -1:
        if at_sentence_start(masked, q):
            return None
        q = masked.find(t, q + 1)
    return "is not at a sentence start"


def check(raw, masked, caps=None, out=print):
    """Return (n_fail, n_changed, n_removed, n_caps). Prints every problem.
    caps: {reply id: [{"from", "to"}, ...]} single-letter capitals listed in the edits file."""
    caps = caps or {}
    fails = []
    warns = []
    used_exemptions = set()
    if len(raw) != len(masked):
        fails.append("count differs: raw %d, masked %d" % (len(raw), len(masked)))
    stray = sorted(set(caps) - set(r["id"] for r in raw))
    if stray:
        fails.append("capitals listed for ids not in raw: %s" % stray)
    n_changed = n_removed = n_caps = 0
    for n, (r, m) in enumerate(zip(raw, masked)):
        rid = r["id"]
        where = "line %d (%s)" % (n + 1, rid)
        keys = set(m.keys())
        want = {"id", "item_id", "reply_original_sha256", "reply_masked", "changed"}
        if keys != want:
            fails.append("%s: fields are %s, expected %s" % (where, sorted(keys), sorted(want)))
            continue
        if m["id"] != rid or m["item_id"] != r["item_id"]:
            fails.append("%s: id/item_id do not match raw (%s, %s)" % (where, m["id"], m["item_id"]))
            continue
        orig, mt = r["reply"], m["reply_masked"]
        if not isinstance(mt, str) or not isinstance(orig, str):
            fails.append("%s: reply text missing" % where)
            continue
        if m["reply_original_sha256"] != sha(orig):
            fails.append("%s: original hash does not match" % where)
        entries = caps.get(rid, [])
        if m["changed"] is False:
            if mt.encode("utf-8") != orig.encode("utf-8"):
                fails.append("%s: marked unchanged but differs from the original" % where)
            if entries:
                fails.append("%s: capitals listed for a reply marked unchanged" % where)
        elif m["changed"] is True:
            if mt == orig:
                fails.append("%s: marked changed but identical to the original" % where)
            else:
                n_changed += 1
                n_removed += len(orig) - len(mt)
                src, positions, cap_errors = apply_caps(orig, entries)
                for ce in cap_errors:
                    fails.append("%s: %s" % (where, ce))
                n_caps += len(positions)
                if not is_subsequence(mt, src):
                    fails.append("%s: not a subsequence of the original with its listed capitals "
                                 "(something added, reordered, or a case change not listed)" % where)
                else:
                    ok, runs = deletion_runs(src, mt)
                    if not ok:
                        fails.append("%s: alignment shows an insert or replace, not deletion only" % where)
                    else:
                        bad = [(a, b) for a, b in runs if not run_respects_words(src, a, b)]
                        if bad:
                            a, b = bad[0]
                            fails.append("%s: a deleted run splits a word (%d runs bad), first %r"
                                         % (where, len(bad), src[max(0, a - 10):b + 10]))
                        for e in entries:
                            t = e.get("to") if isinstance(e, dict) else None
                            if isinstance(t, str) and t:
                                why = capital_survives(src, mt, t)
                                if why:
                                    fails.append("%s: listed capital %r %s" % (where, t[:20], why))
                before, after = leftover_counts(orig), leftover_counts(mt)
                for name in before:
                    new = after[name] - before[name]
                    for snippet, k in sorted(new.items()):
                        warns.append("%s: new '%s' x%d at %r" % (where, name, k, snippet))
        else:
            fails.append("%s: 'changed' is not true or false" % where)
        for name, txt in mention_hits(mt):
            key = (rid, txt) if (rid, txt) in EXEMPTIONS else (rid, txt.lower())
            if key in EXEMPTIONS:
                used_exemptions.add(key)
                continue
            fails.append("%s: still matches mention pattern '%s': %r" % (where, name, txt))
    out("PATTERNS (case-insensitive):")
    for name, p in MENTION_PATTERNS:
        out("  %-42s %s" % (name, p))
    out("EXEMPTIONS USED (%d):" % len(used_exemptions))
    for k in sorted(used_exemptions):
        out("  %s %r: %s" % (k[0], k[1], EXEMPTIONS[k]))
    unused = sorted(set(EXEMPTIONS) - used_exemptions)
    if unused and len(raw) > 20:
        out("EXEMPTIONS NOT USED (%d): %s" % (len(unused), unused))
    out("WARNINGS (deletion leftovers, do not fail the run): %d" % len(warns))
    for w in warns:
        out("  " + w)
    out("FAILURES: %d" % len(fails))
    for f in fails:
        out("  " + f)
    out("changed replies: %d of %d; characters removed: %d (Unicode code points); "
        "single-letter capitals: %d" % (n_changed, len(masked), n_removed, n_caps))
    return len(fails), n_changed, n_removed, n_caps


def load_caps(path):
    with open(path, encoding="utf-8") as fh:
        edits = json.load(fh)["edits"]
    caps = {}
    for e in edits:
        if e.get("capitalize"):
            if e["id"] in caps:
                raise ValueError("id %s listed twice in the edits file" % e["id"])
            caps[e["id"]] = e["capitalize"]
    return caps


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def selftest():
    """Build doctored cases in a temporary folder; each must be caught."""
    orig = [
        ("aaaa000000000001", "X-01", "Per Rule 4 (\"Read the clock every time\"), please insert the time. The red fox ran home."),
        ("aaaa000000000002", "X-02", "The answer is 94. See checklist item 4 for why. Done."),
        ("aaaa000000000003", "X-03", "I am here with you. Take your time."),
        ("aaaa000000000004", "X-04", "Nothing to hide in this one, just a plain reply."),
    ]
    good_masked = [
        "Please insert the time. The red fox ran home.",
        "The answer is 94. Done.",
        "I am here with you. Take your time.",
        "Nothing to hide in this one, just a plain reply.",
    ]

    good_caps = {"aaaa000000000001": [{"from": "please insert", "to": "Please insert"}]}

    def build(masked_texts, changed_flags=None, hashes=None):
        rows = []
        for i, ((rid, item, o), mt) in enumerate(zip(orig, masked_texts)):
            ch = (mt != o) if changed_flags is None else changed_flags[i]
            rows.append({"id": rid, "item_id": item,
                         "reply_original_sha256": sha(o) if hashes is None else hashes[i],
                         "reply_masked": mt, "changed": ch})
        return rows

    cases = []
    cases.append(("good file (with one listed capital)", build(good_masked), good_caps, True))
    # ADDED word inside a reply that also has a real deletion. The letters of "very" exist in order
    # inside the deleted span ("every"), so the plain subsequence check passes it.
    added = list(good_masked)
    added[0] = "very please insert the time. The red fox ran home."
    cases.append(("added word 'very' (letters exist in the deleted span)", build(added), {}, False))
    # A reordered pair of words inside a reply that also has a real deletion.
    reordered = list(good_masked)
    reordered[0] = "Please insert the time. The fox red ran home."
    cases.append(("reordered pair 'red fox' -> 'fox red'", build(reordered), good_caps, False))
    # A changed reply that still says "checklist item 4".
    still = list(good_masked)
    still[1] = "The answer is 94. See checklist item 4 for why."
    cases.append(("changed reply still says 'checklist item 4'", build(still), good_caps, False))
    # An "unchanged" reply that differs by one space.
    spaced = list(good_masked)
    spaced[2] = "I am here with you.  Take your time."
    cases.append(("'unchanged' reply differs by a space", build(spaced, changed_flags=[True, True, False, False]), good_caps, False))
    # A reply marked changed whose text is identical to the original.
    cases.append(("marked changed but identical", build(good_masked, changed_flags=[True, True, False, True]), good_caps, False))
    # A wrong original hash.
    hashes = [sha(o) for _, _, o in orig]
    hashes[3] = "0" * 64
    cases.append(("wrong original hash", build(good_masked, hashes=hashes), good_caps, False))
    # The capital rule. The same capital, NOT listed, must fail.
    cases.append(("capital made but not listed", build(good_masked), {}, False))
    # A listed capital is fine, but another, unlisted case change in the same reply must fail.
    other = list(good_masked)
    other[0] = "Please insert the time. the red fox ran home."
    cases.append(("listed capital plus an unlisted case change", build(other), good_caps, False))
    # A listed entry that changes more than the case of one letter must fail.
    two = list(good_masked)
    two[0] = "PLease insert the time. The red fox ran home."
    cases.append(("listed entry changes two letters ('PLease')",
                  build(two), {"aaaa000000000001": [{"from": "please insert", "to": "PLease insert"}]}, False))
    reword = list(good_masked)
    reword[0] = "Kindly insert the time. The red fox ran home."
    cases.append(("listed entry rewords ('please' -> 'Kindly')",
                  build(reword), {"aaaa000000000001": [{"from": "please", "to": "Kindly"}]}, False))
    # A listed capital that is not at a sentence start must fail.
    mid = list(good_masked)
    mid[0] = "Please insert the time. The red Fox ran home."
    cases.append(("listed capital not at a sentence start ('Fox')", build(mid),
                  {"aaaa000000000001": [{"from": "please insert", "to": "Please insert"},
                                        {"from": "fox ran", "to": "Fox ran"}]}, False))

    results = []
    with tempfile.TemporaryDirectory() as td:
        raw_path = os.path.join(td, "raw.ndjson")
        write_jsonl(raw_path, [{"id": r, "item_id": i, "reply": o, "other": "ignored"} for r, i, o in orig])
        raw = load_raw(raw_path)
        for name, rows, case_caps, should_pass in cases:
            mpath = os.path.join(td, "masked.jsonl")
            write_jsonl(mpath, rows)
            lines = []
            n_fail = check(raw, load_jsonl(mpath), caps=case_caps, out=lines.append)[0]
            passed = n_fail == 0
            ok = passed == should_pass
            results.append(ok)
            print("  %-58s expected %-6s got %-6s %s" % (name, "PASS" if should_pass else "CAUGHT",
                                                      "PASS" if passed else "CAUGHT", "ok" if ok else "WRONG"))
            if not ok:
                for ln in lines:
                    print("      " + ln)
        # The missed-reply case: raw holds a mention, masked left it unchanged.
        raw2_path = os.path.join(td, "raw2.ndjson")
        o2 = "Per Rule 2, the search failed."
        write_jsonl(raw2_path, [{"id": "bbbb000000000001", "item_id": "X-05", "reply": o2}])
        rows2 = [{"id": "bbbb000000000001", "item_id": "X-05", "reply_original_sha256": sha(o2),
                  "reply_masked": o2, "changed": False}]
        n_fail = check(load_raw(raw2_path), rows2, out=lambda s: None)[0]
        ok = n_fail > 0
        results.append(ok)
        print("  %-58s expected CAUGHT got %-6s %s" % ("unchanged reply that still says 'Rule 2'",
                                                    "CAUGHT" if n_fail else "PASS", "ok" if ok else "WRONG"))

    # Prove the extra tests do work the plain subsequence check cannot.
    o0 = orig[0][2]
    sub_passes_added = is_subsequence(added[0], o0)
    aligned, runs = deletion_runs(o0, added[0])
    word_ok = aligned and all(run_respects_words(o0, a, b) for a, b in runs)
    print("  added-word case: plain subsequence check alone says %s; alignment says %s; "
          "word-boundary test says %s"
          % ("PASS" if sub_passes_added else "CAUGHT", "PASS" if aligned else "CAUGHT",
             "PASS" if word_ok else "CAUGHT"))
    proof = sub_passes_added and not word_ok
    results.append(proof)
    print("  %-58s %s" % ("subsequence alone misses it, full check catches it", "ok" if proof else "WRONG"))
    good = all(results)
    print("SELFTEST %s (%d of %d cases as expected)" % ("OK" if good else "FAILED", sum(results), len(results)))
    return 0 if good else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check masked replies against the originals.")
    ap.add_argument("--raw")
    ap.add_argument("--masked")
    ap.add_argument("--edits", help="mask_edits.json; only its 'capitalize' lists are read")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.raw or not a.masked or not a.edits:
        print("need --raw, --masked and --edits (or --selftest)")
        return 2
    try:
        raw = load_raw(a.raw)
        masked = load_jsonl(a.masked)
        caps = load_caps(a.edits)
    except (OSError, ValueError, KeyError) as exc:
        print("cannot read input: %s" % exc)
        return 2
    n_fail = check(raw, masked, caps=caps)[0]
    print("CHECK %s" % ("OK" if n_fail == 0 else "FAILED"))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
