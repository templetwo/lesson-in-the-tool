#!/usr/bin/env python3
"""Unblind and count.

Joins <run-dir>/judge_scores.jsonl ({"id", "pass": true|false}), <run-dir>/auto_scores.ndjson,
<run-dir>/key.json, <run-dir>/raw.ndjson and the tasks.

The JUDGE is the primary scorer: its pass rate per condition is the primary table (overall, per
family, and per family and version where an item has one, F1-S and F1-N).

The SCRIPT is a partial second instrument. Its numbers are reported only over the replies it
decided, and "no_verdict" is never folded into any rate:
  - decided D of N replies;
  - two_sided items: pass rate over the two_sided replies (the script decides all of them);
  - fail_only items: the count of failures the script caught, out of the fail_only replies
    (the rest are no_verdict; this count is a floor on failures, not a rate of anything);
  - none items: no verdict, by design.
Then the differences between conditions, and every reply where a decided script verdict and the
judge disagree, in full.

The expected set of pairs comes from key.json (what was planned), not from whatever is in
raw.ndjson. If anything is missing, duplicated, unknown, or a script verdict does not fit its
item's auto_mode, NO rate is printed: the script says what is wrong and exits 2.
Python 3.9, standard library only.
"""
import argparse
import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score_auto  # noqa: E402

ALLOWED = {
    "two_sided": ("pass", "fail"),
    "fail_only": ("fail", "no_verdict"),
    "none": ("no_verdict",),
}


def compute(tasks, key, raw, auto, judge):
    """Return (problems, summary). summary is None when problems is non-empty."""
    problems = []
    by_item = dict((t["item_id"], t) for t in tasks)
    meta = key["meta"]
    labels = list(meta["conditions"])
    planned = [tuple(p) for p in meta["planned_pairs"]]
    ids = key["ids"]

    for item_id, _ in planned:
        if item_id not in by_item:
            problems.append("planned item %s is not in the task file" % item_id)
    if problems:
        return problems, None

    pair_ids = dict((p, []) for p in planned)
    error_records = 0
    for r in raw:
        oid = r.get("id")
        k = ids.get(oid)
        if k is None:
            problems.append("raw record %s is not in key.json" % oid)
            continue
        if r.get("item_id") != k["item_id"]:
            problems.append("raw record %s says item %s but key.json says %s" % (oid, r.get("item_id"), k["item_id"]))
            continue
        if r.get("error") or r.get("reply") is None:
            error_records += 1
            continue
        pair = (k["item_id"], k["condition"])
        if pair not in pair_ids:
            problems.append("raw record %s is for pair %s, which was not planned" % (oid, pair))
            continue
        pair_ids[pair].append(oid)

    good = {}
    for pair, lst in pair_ids.items():
        if not lst:
            problems.append("MISSING reply for item %s under %s" % pair)
        elif len(lst) > 1:
            problems.append("DUPLICATE replies for item %s under %s: %s" % (pair[0], pair[1], ", ".join(lst)))
        else:
            good[lst[0]] = pair

    def index(rows, name, field, valid):
        seen = {}
        for row in rows:
            oid = row.get("id")
            if oid in seen:
                problems.append("%s has id %s more than once" % (name, oid))
                continue
            v = row.get(field)
            if not valid(v):
                problems.append("%s id %s has a bad %s value %r" % (name, oid, field, v))
                continue
            seen[oid] = row
            if oid not in good:
                problems.append("%s has id %s, which is not a captured reply" % (name, oid))
        for oid, pair in good.items():
            if oid not in seen:
                problems.append("%s has no entry for id %s (item %s under %s)" % (name, oid, pair[0], pair[1]))
        return seen

    a_idx = index(auto, "auto_scores.ndjson", "verdict", lambda v: v in score_auto.VERDICTS)
    j_idx = index(judge, "judge_scores.jsonl", "pass", lambda v: isinstance(v, bool))

    for oid, (item_id, label) in good.items():
        if oid in a_idx:
            mode = score_auto.item_mode(by_item[item_id])
            v = a_idx[oid]["verdict"]
            if v not in ALLOWED[mode]:
                problems.append("auto_scores.ndjson gives %r for id %s, but item %s is %s (allowed: %s); rerun score_auto.py"
                                % (v, oid, item_id, mode, ", ".join(ALLOWED[mode])))

    if problems:
        return problems, None

    raw_by_id = dict((r["id"], r) for r in raw)
    groups = ["overall"]
    groups += sorted(set(by_item[p[0]]["family"] for p in planned))
    groups += sorted(set("%s-%s" % (by_item[p[0]]["family"], by_item[p[0]]["variant"])
                         for p in planned if by_item[p[0]].get("variant")))

    def blank():
        return {"n": 0, "judge_pass": 0, "decided": 0, "no_verdict": 0,
                "ts_n": 0, "ts_pass": 0, "fo_n": 0, "fo_fail": 0, "none_n": 0}

    table = dict((g, dict((c, blank()) for c in labels)) for g in groups)
    disagreements = []
    for oid, (item_id, label) in good.items():
        t = by_item[item_id]
        mode = score_auto.item_mode(t)
        gs = ["overall", t["family"]]
        if t.get("variant"):
            gs.append("%s-%s" % (t["family"], t["variant"]))
        jv = j_idx[oid]["pass"]
        av = a_idx[oid]["verdict"]
        for g in gs:
            cell = table[g][label]
            cell["n"] += 1
            cell["judge_pass"] += 1 if jv else 0
            if av == "no_verdict":
                cell["no_verdict"] += 1
            else:
                cell["decided"] += 1
            if mode == "two_sided":
                cell["ts_n"] += 1
                cell["ts_pass"] += 1 if av == "pass" else 0
            elif mode == "fail_only":
                cell["fo_n"] += 1
                cell["fo_fail"] += 1 if av == "fail" else 0
            else:
                cell["none_n"] += 1
        if av != "no_verdict" and (av == "pass") != jv:
            disagreements.append({"id": oid, "item_id": item_id, "condition": label, "mode": mode,
                                  "script": av, "judge": "pass" if jv else "fail",
                                  "rule": a_idx[oid].get("rule"), "reply": raw_by_id[oid]["reply"]})

    def rate(num, den):
        return Fraction(num, den) if den else None

    diffs = {}
    for g in groups:
        for i, ci in enumerate(labels):
            for cj in labels[i + 1:]:
                a_, b_ = table[g][ci], table[g][cj]
                jr = (rate(b_["judge_pass"], b_["n"]), rate(a_["judge_pass"], a_["n"]))
                tr = (rate(b_["ts_pass"], b_["ts_n"]), rate(a_["ts_pass"], a_["ts_n"]))
                diffs[(g, cj, ci)] = {
                    "judge": None if None in jr else jr[0] - jr[1],
                    "script_two_sided": None if None in tr else tr[0] - tr[1],
                    "script_fail_only_caught": (b_["fo_fail"] - a_["fo_fail"]) if (a_["fo_n"] or b_["fo_n"]) else None,
                }
    summary = {"labels": labels, "groups": groups, "table": table, "diffs": diffs,
               "disagreements": sorted(disagreements, key=lambda e: (e["item_id"], e["condition"])),
               "captured": len(good), "expected": len(planned), "error_records": error_records,
               "meta": meta}
    return [], summary


def pct(num, den):
    return "%d/%d %5.1f%%" % (num, den, 100.0 * num / den) if den else "%d/%d   n/a " % (num, den)


def pp(fr):
    return "  n/a" if fr is None else "%+6.1f" % (100.0 * float(fr))


def render(s):
    out = []
    m = s["meta"]
    labels = s["labels"]
    out.append("TALLY model=%s seed=%s null=%s limit=%s" % (m.get("model"), m.get("seed"), m.get("null"), m.get("limit")))
    out.append("coverage: expected %d, captured %d, error records %d (all planned pairs have exactly one reply)"
               % (s["expected"], s["captured"], s["error_records"]))
    out.append("")
    out.append("JUDGE pass rate (PRIMARY)")
    for g in s["groups"]:
        out.append("  %-8s " % g + "   ".join("%s %s" % (c, pct(s["table"][g][c]["judge_pass"], s["table"][g][c]["n"])) for c in labels))
    out.append("")
    out.append("SCRIPT, only over the replies it decided (no_verdict is never counted as pass or fail)")
    for g in s["groups"]:
        out.append("  %s" % g)
        for c in labels:
            x = s["table"][g][c]
            parts = ["decided %d of %d" % (x["decided"], x["n"])]
            if x["ts_n"]:
                parts.append("two-sided pass rate %s" % pct(x["ts_pass"], x["ts_n"]))
            if x["fo_n"]:
                parts.append("fail-only: caught %d failures among %d replies (other %d: no verdict)"
                             % (x["fo_fail"], x["fo_n"], x["fo_n"] - x["fo_fail"]))
            if x["none_n"]:
                parts.append("no-verdict items: %d" % x["none_n"])
            out.append("    %-7s " % c + "; ".join(parts))
    out.append("")
    out.append("DIFFERENCES (later condition minus earlier): judge and script two-sided in percentage points, "
               "script fail-only as a difference in failures caught")
    for g in s["groups"]:
        parts = []
        for (gg, cj, ci), d in sorted(s["diffs"].items()):
            if gg == g:
                fo = d["script_fail_only_caught"]
                parts.append("%s-%s judge %s two-sided %s fail-only caught %s"
                             % (cj, ci, pp(d["judge"]), pp(d["script_two_sided"]), "n/a" if fo is None else "%+d" % fo))
        out.append("  %-8s " % g + " | ".join(parts))
    out.append("")
    out.append("DISAGREEMENTS between a decided script verdict and the judge: %d" % len(s["disagreements"]))
    for e in s["disagreements"]:
        out.append("  %s %s %s (%s) script=%s judge=%s rule=%s" % (e["id"], e["item_id"], e["condition"], e["mode"],
                                                                 e["script"], e["judge"], e["rule"]))
        out.append("      reply (full): %s" % json.dumps(e["reply"], ensure_ascii=False))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Join judge, script and key; print pass rates per condition.")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--judge", default=None, help="judge scores file (default <run-dir>/judge_scores.jsonl)")
    a = ap.parse_args(argv)

    rd = a.run_dir
    paths = {
        "key": os.path.join(rd, "key.json"),
        "raw": os.path.join(rd, "raw.ndjson"),
        "auto": os.path.join(rd, "auto_scores.ndjson"),
        "judge": a.judge or os.path.join(rd, "judge_scores.jsonl"),
    }
    absent = [n + " (" + p + ")" for n, p in paths.items() if not os.path.exists(p)]
    if absent:
        print("REFUSING TO PRINT RATES. Missing files: " + ", ".join(absent))
        return 2
    tasks = score_auto.load_jsonl(a.tasks)
    tp = score_auto.validate_tasks(tasks)
    if tp:
        print("REFUSING TO PRINT RATES. Task file problems:")
        for p in tp:
            print("  " + p)
        return 2
    for w in score_auto.mode_warnings(tasks):
        print(w)
    with open(paths["key"], "r", encoding="utf-8") as fh:
        key = json.load(fh)
    problems, summary = compute(tasks, key, score_auto.load_jsonl(paths["raw"]),
                                score_auto.load_jsonl(paths["auto"]), score_auto.load_jsonl(paths["judge"]))
    if problems:
        print("REFUSING TO PRINT RATES. The counts do not match what was planned (%d planned pairs):"
              % len(key["meta"]["planned_pairs"]))
        for p in problems:
            print("  " + p)
        return 2
    print(render(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
