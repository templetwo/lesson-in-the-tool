"""Builds hand-made, NON-dry run folders for the tally's tests and selftest. FIXTURE content only.

The runner can only make dry runs (only the dry-run caller exists), and the tally refuses dry runs, so the tally is
tested on folders made here. Every result is written with caller "fixture" so a reader of any tally output can see
where it came from. Each reply is written in the real reply format and parsed by the real parser. The file layout is
copied from runner.py by hand; no test proves the two stay the same (see README, Found).

sorters: list of (name, group).
assign[(name, repeat)]: a list with one entry per line number 1..line_count, each either a main home (str) or a
(main, second) pair; or None for a reply that fails to parse.
dry_row_in=(name, repeat) marks one row of that result dry_run: true, to test the tally's refusal.

Version 2 (2026-11-25, after PICKS_20261125.md): groups, second homes, and a sentence with a double space, quotes
and a non-ASCII letter, so the judgment file can be checked for an exact copy.

Two-turn build (2026-11-25): turn 1 replies are LABEL | main: HOME | second: HOME or none; the sentence comes in a
turn-2 reply (LABEL | SENTENCE), stored under "turn2" exactly as the runner stores it. turn2[(name, repeat)] may be
"ok" (the default), "missing" (no reply text came back) or "broken" (text that cannot be parsed); a repeat whose turn
1 is None gets the runner's not-sent record whatever turn2 says. caller="by_sorter" writes result_callers[name] into
each result and manifest "callers" (default: the sorted set of result_callers; manifest_callers overrides it, to test
a mismatch).
"""
import os
import random

from common import write_json, sha256_file, sha256_bytes
from reply_parser import parse_sort_reply, parse_question_reply
from runner import turn2_not_sent

FIXTURE_SENTENCE = 'FIXTURE sentence  for line %d by %s r%d, "quoted", café.'
BROKEN_TURN2 = "FIXTURE question reply that cannot be parsed"


def fixture_provider(name):
    """Fix B: the provider a fixture sorter gets when the caller names none (one per sorter)."""
    return "fixture-provider-%s" % name


def make_run(root, sorters, repeats, homes, line_count, assign, dry_row_in=None, providers=None, caller="fixture",
             turn2=None, result_callers=None, manifest_callers=None):
    """providers: {name: provider}; a sorter not named gets fixture_provider(name). caller (fix A): written into the
    manifest and every result; the tally refuses "fixture" unless a test passes allow_fixture. Another name is only
    for testing that a caller on the tally's real_callers list is accepted unmarked."""
    prov = {s: (providers or {}).get(s, fixture_provider(s)) for s, _ in sorters}
    t2mode = turn2 or {}
    out = os.path.join(root, "run")
    os.makedirs(os.path.join(out, "prompts"))
    os.makedirs(os.path.join(out, "results"))
    lines = ["FIXTURE line %d, not a real lesson." % i for i in range(1, line_count + 1)]
    lines_sha = sha256_bytes("\n".join(lines).encode("utf-8"))
    homes_sha = sha256_bytes("\n".join(homes).encode("utf-8"))
    rng = random.Random(4242)
    key_prompts, written = [], []
    for s, g in sorters:
        for k in range(1, repeats + 1):
            order = list(range(1, line_count + 1))
            rng.shuffle(order)
            labels = {"L%02d" % (i + 1): n for i, n in enumerate(order)}
            ppath = os.path.join("prompts", "%s__r%d.json" % (s, k))
            write_json(os.path.join(out, ppath), {"dry_run": False, "sorter": s, "repeat": k,
                                                  "text": "FIXTURE prompt", "question_text": "FIXTURE question"})
            a = assign[(s, k)]
            if a is None:
                raw = "FIXTURE reply that cannot be parsed"
            else:
                parts = []
                for lab, n in sorted(labels.items()):
                    h = a[n - 1]
                    main, second = (h, "none") if isinstance(h, str) else h
                    parts.append("%s | main: %s | second: %s\n" % (lab, main, second))
                raw = "".join(parts)
            parsed = parse_sort_reply(raw, sorted(labels), homes, dry_run=False)
            if a is not None and not parsed["ok"]:
                raise ValueError("fixture reply did not parse: %s" % parsed["errors"])
            rows = [dict([("dry_run", False)] + list(r.items())) for r in parsed["rows"]]
            if dry_row_in == (s, k) and rows:
                rows[0]["dry_run"] = True
            if parsed["ok"]:
                mode = t2mode.get((s, k), "ok")
                if mode == "ok":
                    raw2 = "".join("%s | %s\n" % (lab, FIXTURE_SENTENCE % (n, s, k))
                                   for lab, n in sorted(labels.items()))
                elif mode == "missing":
                    raw2 = None
                elif mode == "broken":
                    raw2 = BROKEN_TURN2
                else:
                    raise ValueError("turn2 mode must be ok, missing or broken: %r" % mode)
                p2 = parse_question_reply(raw2, sorted(labels))
                if mode == "ok" and not p2["ok"]:
                    raise ValueError("fixture turn 2 reply did not parse: %s" % p2["errors"])
                t2 = {"dry_run": False, "sent": True, "not_sent_reason": None, "raw_reply": raw2,
                      "parse_ok": p2["ok"], "parse_errors": p2["errors"],
                      "rows": [dict([("dry_run", False)] + list(r.items())) for r in p2["rows"]]}
            else:
                t2 = turn2_not_sent(False)
            rpath = os.path.join("results", "%s__r%d.json" % (s, k))
            write_json(os.path.join(out, rpath), {
                "dry_run": False, "sorter": s, "group": g, "provider": prov[s], "repeat": k,
                "caller": (result_callers or {}).get(s, caller) if caller == "by_sorter" else caller,
                "lines_sha256": lines_sha, "homes_sha256": homes_sha,
                "raw_reply": raw, "parse_ok": parsed["ok"], "parse_errors": parsed["errors"], "rows": rows,
                "turn2": t2})
            key_prompts.append({"dry_run": False, "sorter": s, "group": g, "repeat": k, "home_order": list(homes),
                                "labels": [{"dry_run": False, "label": lab, "line_number": n}
                                           for lab, n in sorted(labels.items())]})
            written += [ppath, rpath]
    key = {
        "dry_run": False, "lines_source": {"sha256": lines_sha},
        "lines": [{"dry_run": False, "line_number": i + 1, "text": t} for i, t in enumerate(lines)],
        "homes_sha256": homes_sha,
        "sorters": [{"dry_run": False, "name": s, "group": g, "provider": prov[s]} for s, g in sorters],
        "prompts": key_prompts}
    if caller == "by_sorter":
        key["real_callers"] = dict(result_callers or {})
    write_json(os.path.join(out, "key.json"), key)
    written.append("key.json")
    manifest = {"dry_run": False, "caller": caller}
    if caller == "by_sorter":
        manifest["callers"] = (manifest_callers if manifest_callers is not None
                               else sorted(set((result_callers or {}).values())))
    manifest["files"] = [{"dry_run": False, "path": p, "sha256": sha256_file(os.path.join(out, p))} for p in written]
    write_json(os.path.join(out, "manifest.json"), manifest)
    return out
