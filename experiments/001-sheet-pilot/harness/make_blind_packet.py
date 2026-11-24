#!/usr/bin/env python3
"""Build the blind judge's packet.

Normal mode: reads the tasks and <run-dir>/raw.ndjson and writes <run-dir>/judge_packet.jsonl,
shuffled, one line per reply: {"id", "prompt", "pass_rule", "reply"}. No condition, no system
text, no item id or family, no times, no token counts. Error records (no reply) are left out.
This script never opens key.json.

Selftest mode (--selftest): builds a packet from the hand-written selftest replies so the judge
can be checked BEFORE any model call (PREREG, "Before any model call"). Writes
<out-dir>/judge_selftest_packet.jsonl (same four fields) and <out-dir>/judge_selftest_key.json
(id -> item and expected verdict). The judge gets the packet only. Check its answers with
selftest.py --judge-check <out-dir>.

The judge answers one line per id: {"id": "...", "pass": true|false}.
Python 3.9, standard library only.
"""
import argparse
import json
import os
import random
import secrets
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score_auto  # noqa: E402


def write_jsonl(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def load_tasks_checked(path):
    tasks = score_auto.load_jsonl(path)
    problems = score_auto.validate_tasks(tasks)
    if problems:
        print("TASK FILE PROBLEMS, no packet written:")
        for p in problems:
            print("  " + p)
        return None
    return dict((t["item_id"], t) for t in tasks)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write the shuffled blind packet for the judge.")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--run-dir", help="run folder holding raw.ndjson (normal mode)")
    ap.add_argument("--seed", type=int, default=None, help="shuffle seed; default is a fresh random one")
    ap.add_argument("--selftest", action="store_true", help="build the judge selftest packet instead")
    ap.add_argument("--selftest-replies", help="path to selftest_replies.jsonl (selftest mode)")
    ap.add_argument("--out-dir", help="folder for the selftest packet and its key (selftest mode)")
    a = ap.parse_args(argv)

    by_id = load_tasks_checked(a.tasks)
    if by_id is None:
        return 2
    seed = a.seed if a.seed is not None else secrets.randbits(32)
    rng = random.Random(seed)

    if a.selftest:
        if not a.selftest_replies or not a.out_dir:
            print("--selftest needs --selftest-replies and --out-dir")
            return 2
        replies = score_auto.load_jsonl(a.selftest_replies)
        rows, key = [], {}
        for s in replies:
            t = by_id.get(s.get("item_id"))
            if t is None:
                print("selftest reply names item %r, which is not in the task file" % s.get("item_id"))
                return 2
            oid = secrets.token_hex(8)
            while oid in key:
                oid = secrets.token_hex(8)
            key[oid] = {"item_id": s["item_id"], "expected": s.get("expected")}
            rows.append({"id": oid, "prompt": t["prompt"], "pass_rule": t["pass_rule"], "reply": s.get("reply", "")})
        rng.shuffle(rows)
        os.makedirs(a.out_dir, exist_ok=True)
        write_jsonl(os.path.join(a.out_dir, "judge_selftest_packet.jsonl"), rows)
        with open(os.path.join(a.out_dir, "judge_selftest_key.json"), "w", encoding="utf-8") as fh:
            json.dump(key, fh, indent=1)
            fh.write("\n")
        print("wrote %d selftest rows to %s (give the judge the packet only, not judge_selftest_key.json)"
              % (len(rows), os.path.join(a.out_dir, "judge_selftest_packet.jsonl")))
        return 0

    if not a.run_dir:
        print("--run-dir is required in normal mode")
        return 2
    raw = score_auto.load_jsonl(os.path.join(a.run_dir, "raw.ndjson"))
    rows, skipped = [], 0
    for r in raw:
        if r.get("error") or r.get("reply") is None:
            skipped += 1
            continue
        t = by_id.get(r.get("item_id"))
        if t is None:
            print("raw record %s names item %r, which is not in the task file" % (r.get("id"), r.get("item_id")))
            return 2
        rows.append({"id": r["id"], "prompt": t["prompt"], "pass_rule": t["pass_rule"], "reply": r["reply"]})
    rng.shuffle(rows)
    path = os.path.join(a.run_dir, "judge_packet.jsonl")
    write_jsonl(path, rows)
    print("wrote %d rows to %s; left out %d error records (no reply)" % (len(rows), path, skipped))
    print("Give the judge judge_packet.jsonl only. Never raw.ndjson (its token counts reveal the condition) and never key.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
