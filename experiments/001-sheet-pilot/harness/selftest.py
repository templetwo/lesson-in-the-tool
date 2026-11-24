#!/usr/bin/env python3
"""Selftest for the sheet-test harness. Makes NO model call and NO network call.

(a) Script scorer vs hand-written replies: the script must never contradict a label. "fail" on a
    reply labelled pass, or "pass" on a reply labelled fail, is a FAILURE. "no_verdict" is allowed
    on any reply; it is counted and printed (decided vs left to the judge), not a failure.
    The PREREG also asks for one pass and one fail reply per family; a family without both is a failure.
(b) Synthetic null, end to end: run_trial.py --null with a fake transport whose reply depends
    only on the user prompt, then score_auto.py, make_blind_packet.py, a synthetic judge and
    tally.py. Every C2null minus C1 difference must be exactly zero. Along the way: one injected
    failed call must be recorded as an error, tally must refuse and name the missing pair, a
    resume must fill the gap without duplicates, the sheet text must never be sent in null mode,
    and neither raw.ndjson nor the judge packet may carry a condition or any system text.
(c) The selftest can fail: (c1) flip one decided label in memory (a fail-labelled reply the
    script fails becomes pass-labelled) and require check (a) to report a contradiction;
    (c2) change one C2null reply and require tally to show a nonzero difference;
    (c3) fail-closed guards on the task file, the auto rules and the checklist hashes.

Exit 0: everything held. Exit 1: any failure.

Uses ../tasks/ if that folder exists, otherwise harness/fixture/ (said loudly).
Separate mode: --judge-check DIR compares a judge's selftest answers with the expected labels.
Python 3.9, standard library only.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_blind_packet  # noqa: E402
import run_trial  # noqa: E402
import score_auto  # noqa: E402
import tally  # noqa: E402

FAILS = []          # failures


def fail(msg):
    FAILS.append(msg)
    print("  FAIL: " + msg)


def ok(msg):
    print("  ok: " + msg)


def quiet(fn, argv):
    """Run a script's main() with its printing captured. Returns (exit code, text)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            code = fn(argv)
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 2
            print(str(e))
    return code, buf.getvalue()


# ---------------------------------------------------------------- (a)
def check_a(tasks, replies):
    """Return (contradictions, decided, no_verdict, other_problems) without printing.
    decided and no_verdict are lists of (item_id, mode, expected, verdict)."""
    wrong, decided, no_verdict_rows, other = [], [], [], []
    tp = score_auto.validate_tasks(tasks)
    if tp:
        return wrong, decided, no_verdict_rows, ["task file: " + p for p in tp]
    by_id = dict((t["item_id"], t) for t in tasks)
    have = {}
    for i, s in enumerate(replies, 1):
        t = by_id.get(s.get("item_id"))
        if t is None:
            other.append("selftest reply %d names unknown item %r" % (i, s.get("item_id")))
            continue
        exp = s.get("expected")
        if exp not in ("pass", "fail"):
            other.append("selftest reply %d (%s) has expected %r" % (i, s["item_id"], exp))
            continue
        have.setdefault(t["family"], set()).add(exp)
        verdict, rule = score_auto.score_item(t, s.get("reply", ""))
        row = (s["item_id"], score_auto.item_mode(t), exp, verdict)
        if verdict == "no_verdict":
            no_verdict_rows.append(row)
        else:
            decided.append(row)
            if verdict != exp:
                wrong.append("%s (reply %d, %s): labelled %s, script said %s [%s]"
                             % (s["item_id"], i, row[1], exp, verdict, rule))
    for fam in sorted(set(t["family"] for t in tasks)):
        missing = set(["pass", "fail"]) - have.get(fam, set())
        if missing:
            other.append("family %s has no selftest reply expected to %s" % (fam, " or ".join(sorted(missing))))
    return wrong, decided, no_verdict_rows, other


def run_a(tasks, replies):
    print("\n(a) script scorer against %d hand-written selftest replies" % len(replies))
    wrong, decided, no_verdict_rows, other = check_a(tasks, replies)
    for p in other:
        fail(p)
    for w in wrong:
        fail("CONTRADICTION: " + w)
    print("  the script decided %d of %d replies and left %d to the judge (no_verdict)"
          % (len(decided), len(replies), len(no_verdict_rows)))
    for mode in score_auto.MODES:
        d = [r for r in decided if r[1] == mode]
        u = [r for r in no_verdict_rows if r[1] == mode]
        if d or u:
            print("    %-9s decided %2d (said pass %d, said fail %d), no_verdict %2d (labelled pass %d, labelled fail %d)"
                  % (mode, len(d), sum(1 for r in d if r[3] == "pass"), sum(1 for r in d if r[3] == "fail"),
                     len(u), sum(1 for r in u if r[2] == "pass"), sum(1 for r in u if r[2] == "fail")))
    if not wrong and not other:
        ok("no decided verdict contradicts its label (%d decided, all agree); every family has a pass and a fail reply"
           % len(decided))


# ---------------------------------------------------------------- (b)
class FakeTransport(object):
    """Reply depends only on the user prompt. The first call fails on purpose."""

    def __init__(self, reply_for_prompt):
        self.reply_for_prompt = reply_for_prompt
        self.calls = []

    def __call__(self, endpoint, payload, timeout):
        system = payload["messages"][0]["content"]
        user = payload["messages"][1]["content"]
        self.calls.append((system, user))
        if len(self.calls) == 1:
            raise OSError("injected failure for the selftest")
        return {"message": {"role": "assistant", "content": self.reply_for_prompt[user]},
                "done": True, "done_reason": "stop", "prompt_eval_count": 10, "eval_count": 5,
                "total_duration": 1, "load_duration": 0, "prompt_eval_duration": 1, "eval_duration": 1}


def synthetic_judge(run_dir, tasks, flip_reply):
    """Deterministic judge from the reply text only: agrees with the script where it decides,
    except it disagrees on every reply equal to flip_reply. no_verdict replies: sha256 parity."""
    by_id = dict((t["item_id"], t) for t in tasks)
    raw = dict((r["id"], r) for r in score_auto.load_jsonl(os.path.join(run_dir, "raw.ndjson")))
    rows = []
    for p in score_auto.load_jsonl(os.path.join(run_dir, "judge_packet.jsonl")):
        reply = p["reply"]
        verdict, _ = score_auto.score_item(by_id[raw[p["id"]]["item_id"]], reply)
        if verdict == "no_verdict":
            ans = hashlib.sha256(reply.encode("utf-8")).digest()[0] % 2 == 0
        else:
            ans = verdict == "pass"
        if reply == flip_reply:
            ans = not ans
        rows.append({"id": p["id"], "pass": ans})
    with open(os.path.join(run_dir, "judge_scores.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def score_pack_judge(run_dir, tasks_path, tasks, flip_reply):
    c1, o1 = quiet(score_auto.main, ["--tasks", tasks_path, "--run-dir", run_dir])
    c2, o2 = quiet(make_blind_packet.main, ["--tasks", tasks_path, "--run-dir", run_dir, "--seed", "11"])
    if c1 != 0 or c2 != 0:
        fail("score_auto exit %s / make_blind_packet exit %s:\n%s%s" % (c1, c2, o1, o2))
        return False
    synthetic_judge(run_dir, tasks, flip_reply)
    return True


def load_compute(run_dir, tasks):
    with open(os.path.join(run_dir, "key.json")) as fh:
        key = json.load(fh)
    return tally.compute(tasks, key,
                         score_auto.load_jsonl(os.path.join(run_dir, "raw.ndjson")),
                         score_auto.load_jsonl(os.path.join(run_dir, "auto_scores.ndjson")),
                         score_auto.load_jsonl(os.path.join(run_dir, "judge_scores.jsonl")))


def null_diffs(summary):
    out = []
    for (g, cj, ci), d in sorted(summary["diffs"].items()):
        if set([cj, ci]) == set(["C1", "C2null"]):
            out.append((g, d["judge"], d["script_two_sided"], d["script_fail_only_caught"]))
    return out


def run_b_and_c2(tasks_path, tasks, replies, work):
    print("\n(b) synthetic null, end to end, fake transport (no network)")
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    run_dir = os.path.join(work, "null_run")

    reply_for_item = {}
    for s in replies:
        if s.get("expected") == "pass":
            reply_for_item.setdefault(s["item_id"], s.get("reply", ""))
    for s in replies:
        reply_for_item.setdefault(s["item_id"], s.get("reply", ""))
    reply_for_prompt = {}
    for t in tasks:
        reply_for_prompt[t["prompt"]] = reply_for_item.get(t["item_id"], "Placeholder reply for item %s." % t["item_id"])
    # plant a judge/script disagreement on the first item whose fake reply the script decides
    flip_item = None
    for t in sorted(tasks, key=lambda x: x["item_id"]):
        if score_auto.score_item(t, reply_for_prompt[t["prompt"]])[0] != "no_verdict":
            flip_item = t["item_id"]
            break
    if flip_item is None:
        flip_item = sorted(t["item_id"] for t in tasks)[0]
    flip_reply = reply_for_prompt[[t for t in tasks if t["item_id"] == flip_item][0]["prompt"]]

    cond, systems = run_trial.load_conditions(os.path.join(HERE, "conditions.json"))
    fake = FakeTransport(reply_for_prompt)
    saved = run_trial.TRANSPORT
    run_trial.TRANSPORT = fake
    try:
        argv = ["--endpoint", "http://fake.invalid", "--model", "fake-model", "--tasks", tasks_path,
                "--out", run_dir, "--seed", "7", "--null"]
        code1, out1 = quiet(run_trial.main, argv)
        n_items = len(tasks)
        planned = 3 * n_items
        cov1 = [l for l in out1.splitlines() if l.startswith("COVERAGE")]
        if code1 == 1 and cov1 and ("captured %d" % (planned - 1)) in cov1[0] and "error records 1" in cov1[0]:
            ok("first run recorded the injected failure: " + cov1[0])
        else:
            fail("first run should exit 1 with one error record; got exit %s, %s" % (code1, cov1 or out1[-300:]))

        # tally must refuse while a pair is missing
        if score_pack_judge(run_dir, tasks_path, tasks, flip_reply):
            code_t, out_t = quiet(tally.main, ["--tasks", tasks_path, "--run-dir", run_dir])
            if code_t == 2 and "REFUSING TO PRINT RATES" in out_t and "MISSING reply" in out_t and "%" not in out_t:
                miss = [l.strip() for l in out_t.splitlines() if "MISSING" in l]
                ok("tally refused with a pair missing and named it: " + "; ".join(miss))
            else:
                fail("tally should refuse while a pair is missing; exit %s, output:\n%s" % (code_t, out_t))

        # wrong-identity resume must be refused
        code_w, out_w = quiet(run_trial.main, argv[:-3] + ["--seed", "8", "--null"])
        if code_w == 2 and "REFUSING to resume" in out_w:
            ok("resume with a different seed was refused")
        else:
            fail("resume with a different seed should be refused; exit %s" % code_w)

        code2, out2 = quiet(run_trial.main, argv)
        cov2 = [l for l in out2.splitlines() if l.startswith("COVERAGE")]
        if code2 == 0 and cov2 and ("expected %d, captured %d, missing 0" % (planned, planned)) in cov2[0]:
            ok("resume filled the gap: " + cov2[0])
        else:
            fail("resume should complete coverage; exit %s, %s" % (code2, cov2 or out2[-300:]))
    finally:
        run_trial.TRANSPORT = saved

    raw = score_auto.load_jsonl(os.path.join(run_dir, "raw.ndjson"))
    good = [r for r in raw if not r.get("error")]
    if len(raw) == planned + 1 and len(good) == planned and len(set(r["id"] for r in raw)) == len(raw):
        ok("raw.ndjson has %d records: %d replies plus the 1 kept error record, no duplicates" % (len(raw), len(good)))
    else:
        fail("raw.ndjson should have %d records (%d good); has %d (%d good)" % (planned + 1, planned, len(raw), len(good)))

    # what was sent: sheet never in null mode; each item once under C0 text, twice under C1 text
    sheet_text = systems["C2"]
    sent = fake.calls[1:]  # the first call was the injected failure; its retry is in this list
    per_item = {}
    for system, user in sent:
        per_item.setdefault(user, []).append(system)
    bad = []
    if any(s == sheet_text for s, _ in fake.calls):
        bad.append("the sheet text was sent during a null run")
    for t in tasks:
        got = per_item.get(t["prompt"], [])
        if got.count(systems["C0"]) != 1 or got.count(systems["C1"]) != 2 or len(got) != 3:
            bad.append("item %s was sent %d times (C0 text %d, C1 text %d)" % (
                t["item_id"], len(got), got.count(systems["C0"]), got.count(systems["C1"])))
    if bad:
        for b in bad:
            fail(b)
    else:
        ok("null mode sent the generic list for C1 and C2null, the bare sentence for C0, and never the sheet")

    # the real (non-null) path: each item gets C0 text, C1 text and the sheet text exactly once
    real_dir = os.path.join(work, "real_run")
    fake_real = FakeTransport(reply_for_prompt)
    fake_real.calls.append(("(no injected failure on this run)", ""))
    run_trial.TRANSPORT = fake_real
    try:
        code_r, out_r = quiet(run_trial.main, ["--endpoint", "http://fake.invalid", "--model", "fake-model",
                                               "--tasks", tasks_path, "--out", real_dir, "--seed", "7"])
    finally:
        run_trial.TRANSPORT = saved
    expect_c2 = cond["neutral_sentence"] + cond["separator"] + open(cond["files"]["sheet"]["path"], encoding="utf-8").read()
    bad_r = []
    if code_r != 0:
        bad_r.append("non-null fake run exit %s" % code_r)
    if systems["C2"] != expect_c2:
        bad_r.append("C2 system text is not sentence + separator + sheet file")
    per = {}
    for system, user in fake_real.calls[1:]:
        per.setdefault(user, []).append(system)
    for t in tasks:
        got = per.get(t["prompt"], [])
        if len(got) != 3 or got.count(systems["C0"]) != 1 or got.count(systems["C1"]) != 1 or got.count(expect_c2) != 1:
            bad_r.append("item %s on the real path was sent %d times (C0 %d, C1 %d, sheet %d)" % (
                t["item_id"], len(got), got.count(systems["C0"]), got.count(systems["C1"]), got.count(expect_c2)))
    if bad_r:
        for b_ in bad_r:
            fail(b_)
    else:
        ok("real (non-null) path sent each item once with the bare sentence, once with the generic list, once with the sheet")

    # blindness of raw.ndjson and the packet
    if not score_pack_judge(run_dir, tasks_path, tasks, flip_reply):
        return
    leaks = []
    probes = [cond["neutral_sentence"], systems["C1"][len(cond["neutral_sentence"]):].strip()[:60],
              sheet_text[len(cond["neutral_sentence"]):].strip()[:60], "C2null",
              "auto_mode", "two_sided", "fail_only"]
    for name in ("raw.ndjson", "judge_packet.jsonl"):
        text = open(os.path.join(run_dir, name), encoding="utf-8").read()
        for p in probes:
            if p and p in text:
                leaks.append("%s contains %r" % (name, p[:40]))
        for row in score_auto.load_jsonl(os.path.join(run_dir, name)):
            if "condition" in row or "system" in row:
                leaks.append("%s row %s has a condition or system field" % (name, row.get("id")))
            if name == "judge_packet.jsonl" and set(row) != set(["id", "prompt", "pass_rule", "reply"]):
                leaks.append("judge packet row has fields %s" % sorted(row))
    if leaks:
        for l in sorted(set(leaks)):
            fail(l)
    else:
        ok("raw.ndjson and judge_packet.jsonl carry no condition label, no system text and no auto_mode; packet has only id, prompt, pass_rule, reply")

    problems, summary = load_compute(run_dir, tasks)
    if problems:
        for p in problems:
            fail("tally problem on the complete null run: " + p)
        return
    nd = null_diffs(summary)
    nonzero = [x for x in nd if any(v is not None and v != 0 for v in x[1:])]
    if nd and not nonzero:
        ok("C2null minus C1 is exactly 0 for judge, script two-sided and script fail-only in all %d groups (%s)"
           % (len(nd), ", ".join(x[0] for x in nd)))
    else:
        fail("null difference not zero: %s" % nonzero)
    n_flip = sum(1 for r in good if r["reply"] == flip_reply)
    decidable_flip = score_auto.score_item([t for t in tasks if t["item_id"] == flip_item][0], flip_reply)[0] != "no_verdict"
    want = n_flip if decidable_flip else 0
    if len(summary["disagreements"]) == want:
        ok("tally listed exactly the %d planted judge/script disagreements" % want)
    else:
        fail("tally listed %d disagreements, planted %d" % (len(summary["disagreements"]), want))
    code_t, out_t = quiet(tally.main, ["--tasks", tasks_path, "--run-dir", run_dir])
    if code_t == 0:
        ok("tally.py ran on the complete null run; its output follows")
        print("\n".join("      | " + l for l in out_t.splitlines()))
    else:
        fail("tally.py exit %s on the complete null run:\n%s" % (code_t, out_t))

    # (c2) negative control for the null check
    print("\n(c2) negative control: change one C2null reply; the null check must now show a gap")
    neg = os.path.join(work, "negative_run")
    shutil.copytree(run_dir, neg)
    with open(os.path.join(neg, "key.json")) as fh:
        key = json.load(fh)
    by_id = dict((t["item_id"], t) for t in tasks)
    alt_by_item = {}
    for s in replies:
        alt_by_item.setdefault(s["item_id"], []).append(s.get("reply", ""))
    target, new_reply = None, None
    for r in good:
        if key["ids"][r["id"]]["condition"] != "C2null" or r["reply"] == flip_reply:
            continue  # a reply carrying the planted judge flip would cancel the judge's change
        t_ = by_id[r["item_id"]]
        cur = score_auto.score_item(t_, r["reply"])[0]
        for cand in alt_by_item.get(r["item_id"], []) + [""]:
            v = score_auto.score_item(t_, cand)[0]
            if v != "no_verdict" and v != cur and cand != flip_reply:
                target, new_reply = r["id"], cand
                break
        if target:
            break
    if not target:
        fail("could not build the negative control (no C2null reply with a decided alternative of another verdict)")
        return
    lines = []
    for r in score_auto.load_jsonl(os.path.join(neg, "raw.ndjson")):
        if r["id"] == target:
            r["reply"] = new_reply
        lines.append(json.dumps(r, ensure_ascii=False))
    with open(os.path.join(neg, "raw.ndjson"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    if not score_pack_judge(neg, tasks_path, tasks, flip_reply):
        return
    problems, summary = load_compute(neg, tasks)
    if problems:
        fail("negative control tally problems: %s" % problems)
        return
    overall = [x for x in null_diffs(summary) if x[0] == "overall"]
    if overall and overall[0][1] not in (None, 0) and any(v not in (None, 0) for v in overall[0][2:]):
        _, j, ts, fo = overall[0]
        ok("one changed reply gives C2null minus C1 of %+.1f points (judge), two-sided %s points, fail-only caught %s"
           % (100 * float(j), "n/a" if ts is None else "%+.1f" % (100 * float(ts)), "n/a" if fo is None else "%+d" % fo))
    else:
        fail("changing one C2null reply did not move the null difference: %s" % overall)


# ---------------------------------------------------------------- (c1)
def run_c1(tasks, replies):
    print("\n(c1) negative control: flip one decided label in memory; check (a) must report a contradiction")
    idx = None
    # prefer a fail-labelled reply the script fails: flipped, it is the "script fails a pass" case
    for want in ("fail", "pass"):
        for i, s in enumerate(replies):
            t = [x for x in tasks if x["item_id"] == s.get("item_id")]
            if t and s.get("expected") == want and score_auto.score_item(t[0], s.get("reply", ""))[0] == want:
                idx = i
                break
        if idx is not None:
            break
    if idx is None:
        fail("no decidable selftest reply to flip")
        return
    flipped = [dict(s) for s in replies]
    flipped[idx]["expected"] = "fail" if flipped[idx]["expected"] == "pass" else "pass"
    wrong, _, _, _ = check_a(tasks, flipped)
    if any(flipped[idx]["item_id"] in w for w in wrong):
        ok("flipping the label on %s made check (a) report: %s" % (flipped[idx]["item_id"], wrong[0]))
    else:
        fail("check (a) did not notice a flipped label on %s" % flipped[idx]["item_id"])


# ---------------------------------------------------------------- (c3)
def run_c3(work):
    print("\n(c3) fail-closed guards: auto keys, regexes, auto_mode handling, a changed checklist")
    p = score_auto.validate_auto({"must_contains_all": ["x"]}, "probe")
    (ok if p else fail)("a misspelt auto key is an error: %s" % (p[0] if p else "NOT CAUGHT"))
    p = score_auto.validate_auto({"regex_must_match": ["(unclosed"]}, "probe")
    (ok if p else fail)("a regex that does not compile is an error: %s" % (p[0] if p else "NOT CAUGHT"))
    v = score_auto.score_reply({"must_not_contain_any": ["zebra"]}, "no rule broken here", "fail_only")[0]
    (ok if v == "no_verdict" else fail)("fail_only with no rule broken gives %r (must be no_verdict, never pass)" % v)
    v = score_auto.score_reply({"must_not_contain_any": ["zebra"]}, "a zebra", "fail_only")[0]
    (ok if v == "fail" else fail)("fail_only with a rule broken gives %r (must be fail)" % v)
    v = score_auto.score_reply({"must_contain_all": ["zebra"]}, "a zebra", "none")[0]
    (ok if v == "no_verdict" else fail)("auto_mode none gives %r even when its rules hold (must be no_verdict)" % v)
    t_missing = {"item_id": "X-01", "family": "X", "variant": None, "prompt": "p", "pass_rule": "r",
                 "auto": {"must_contain_all": ["zebra"]}}
    w = score_auto.mode_warnings([t_missing])
    v = score_auto.score_item(t_missing, "a zebra")[0]
    (ok if (w and v == "no_verdict") else fail)("a missing auto_mode is treated as none with a warning: %r, %s"
                                                  % (v, w[0] if w else "NO WARNING"))
    bad_two = dict(t_missing, auto_mode="two_sided", auto={})
    bad_mode = dict(t_missing, auto_mode="both_ways")
    p1, p2 = score_auto.validate_tasks([bad_two]), score_auto.validate_tasks([bad_mode])
    (ok if p1 and p2 else fail)("a two_sided item with no rules and an unknown auto_mode are task-file errors: %s | %s"
                                % (p1[0] if p1 else "NOT CAUGHT", p2[0] if p2 else "NOT CAUGHT"))
    os.makedirs(work, exist_ok=True)
    with open(os.path.join(HERE, "conditions.json")) as fh:
        c = json.load(fh)
    c["files"]["generic"]["sha256"] = "0" * 64
    probe = os.path.join(work, "conditions_bad_hash.json")
    with open(probe, "w") as fh:
        json.dump(c, fh)
    try:
        run_trial.load_conditions(probe)
        fail("run_trial accepted a checklist whose sha256 does not match conditions.json")
    except SystemExit as e:
        ok("run_trial refuses a changed checklist: %s" % str(e)[:90])


# ---------------------------------------------------------------- judge check
def judge_check(d):
    with open(os.path.join(d, "judge_selftest_key.json")) as fh:
        key = json.load(fh)
    path = os.path.join(d, "judge_selftest_scores.jsonl")
    ans = {}
    bad = []
    for row in score_auto.load_jsonl(path):
        if row.get("id") in ans:
            bad.append("id %s answered twice" % row.get("id"))
        if not isinstance(row.get("pass"), bool):
            bad.append("id %s has pass=%r" % (row.get("id"), row.get("pass")))
        ans[row.get("id")] = row.get("pass")
    right = 0
    for oid, k in sorted(key.items(), key=lambda kv: kv[1]["item_id"]):
        if oid not in ans:
            bad.append("no answer for %s (item %s)" % (oid, k["item_id"]))
        elif ans[oid] != (k["expected"] == "pass"):
            bad.append("%s (item %s): expected %s, judge said %s" % (oid, k["item_id"], k["expected"], "pass" if ans[oid] else "fail"))
        else:
            right += 1
    for oid in ans:
        if oid not in key:
            bad.append("judge answered unknown id %s" % oid)
    print("JUDGE SELFTEST: %d of %d right" % (right, len(key)))
    for b in bad:
        print("  FAIL: " + b)
    print("JUDGE SELFTEST " + ("PASSED" if not bad else "FAILED: the judge is not trusted, nothing runs (PREREG)"))
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Selftest for the harness. No model or network calls.")
    ap.add_argument("--tasks-dir", default=os.path.join(os.path.dirname(HERE), "tasks"))
    ap.add_argument("--keep", action="store_true", help="keep the work folder harness/.selftest_work")
    ap.add_argument("--judge-check", metavar="DIR", help="only check a judge's selftest answers in DIR")
    a = ap.parse_args(argv)

    if a.judge_check:
        return judge_check(a.judge_check)

    tdir = a.tasks_dir
    if not os.path.isdir(tdir):
        print("=" * 72)
        print("NOTE: %s does not exist. RUNNING AGAINST THE BUILDER'S FIXTURE," % tdir)
        print("NOT THE REAL TASK ITEMS. A pass here says nothing about the real items.")
        print("=" * 72)
        tdir = os.path.join(HERE, "fixture")
    tasks_path = os.path.join(tdir, "tasks.jsonl")
    rep_path = os.path.join(tdir, "selftest_replies.jsonl")
    print("tasks:            %s" % tasks_path)
    print("selftest replies: %s" % rep_path)
    for p in (tasks_path, rep_path):
        if not os.path.exists(p):
            print("FAIL: %s is missing (not falling back to the fixture, because the folder exists)" % p)
            return 1
    try:
        tasks = score_auto.load_jsonl(tasks_path)
        replies = score_auto.load_jsonl(rep_path)
    except ValueError as e:
        print("FAIL: %s" % e)
        return 1
    tp = score_auto.validate_tasks(tasks)
    if tp:
        print("FAIL: task file problems:")
        for p in tp:
            print("  " + p)
        return 1
    for w in score_auto.mode_warnings(tasks):
        print(w)
    fams = {}
    for t in tasks:
        fams[t["family"]] = fams.get(t["family"], 0) + 1
    print("%d items (%s), %d selftest replies" % (len(tasks), ", ".join("%s %d" % kv for kv in sorted(fams.items())), len(replies)))

    run_a(tasks, replies)
    work = os.path.join(HERE, ".selftest_work")
    try:
        run_b_and_c2(tasks_path, tasks, replies, work)
    except Exception as e:  # a crash in the selftest is a failure, never a pass
        fail("selftest (b)/(c2) crashed: %s: %s" % (type(e).__name__, e))
    run_c1(tasks, replies)
    run_c3(work)
    if not a.keep and os.path.exists(work):
        shutil.rmtree(work)

    print("")
    if FAILS:
        print("SELFTEST FAILED: %d failure(s)" % len(FAILS))
        return 1
    print("SELFTEST PASSED: every check above held")
    return 0


if __name__ == "__main__":
    sys.exit(main())
