#!/usr/bin/env python3
"""Run every item under every condition against one Ollama model.

For each (item, condition) pair it calls <endpoint>/api/chat once, with a system message
(the condition's text) and the item's prompt as the user message. Calls go in a seeded
shuffled order. Writes, inside --out:

  raw.ndjson  one line per call: opaque id, item_id, model, start/end, options, reply,
              server token counts and durations, done_reason, ctx_warning, error.
              It has NO condition and NO system text. It is still NOT judge-safe: the
              prompt token count differs by condition. Only judge_packet.jsonl goes to a judge.
  key.json    run identity (model, seed, null flag, limit, hashes, planned pairs) and the
              map from opaque id to item and condition. Never give this to a judge.

A failed call is written as a record with its error. Nothing is retried silently.
A "finished" pair is one that has a record with a reply and no error. Running the same
command again resumes: finished pairs are skipped, and pairs whose only records are
errors are tried again (printed as such; the old error records stay in raw.ndjson).

Python 3.9, standard library only.
"""
import argparse
import datetime
import hashlib
import json
import os
import random
import secrets
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score_auto  # noqa: E402  (shared JSONL loader and task validation)

FIXED_OPTIONS = {"temperature": 0.1, "top_k": 50, "repeat_penalty": 1.1}
IDENTITY_KEYS = ("model", "seed", "null", "limit", "tasks_sha256", "conditions_sha256",
                 "num_ctx", "num_predict", "conditions")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso():
    """Wall clock from the system, local time with offset."""
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def load_conditions(path):
    """Return (conditions dict, {label: system text}). Refuses if a file hash has changed."""
    with open(path, "r", encoding="utf-8") as fh:
        cond = json.load(fh)
    texts = {}
    for name, info in cond["files"].items():
        if not os.path.exists(info["path"]):
            raise SystemExit("REFUSING: checklist file %r is missing: %s" % (name, info["path"]))
        got = sha256_file(info["path"])
        if got != info["sha256"]:
            raise SystemExit("REFUSING: checklist file %r changed. conditions.json says %s, file is %s (%s)"
                             % (name, info["sha256"], got, info["path"]))
        with open(info["path"], "r", encoding="utf-8") as fh:
            texts[name] = fh.read()
    sentence = cond["neutral_sentence"]
    sep = cond["separator"]
    systems = {}
    for label, parts in cond["conditions"].items():
        pieces = []
        for p in parts:
            pieces.append(sentence if p == "sentence" else texts[p])
        systems[label] = sep.join(pieces)
    return cond, systems


def http_chat(endpoint, payload, timeout):
    """POST /api/chat and return the decoded JSON. Raises on any failure."""
    url = endpoint.rstrip("/") + "/api/chat"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read()[:500].decode("utf-8", "replace")
        raise RuntimeError("HTTP %s from %s: %s" % (e.code, url, detail))
    return json.loads(data.decode("utf-8"))


# The selftest replaces this with a fake that makes no network call.
TRANSPORT = http_chat


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def append_line(path, obj):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def coverage(planned, key_ids, raw_records):
    """Return (finished set, error_record_count, error_pairs set)."""
    finished = set()
    errors = 0
    error_pairs = set()
    for r in raw_records:
        k = key_ids.get(r.get("id"))
        if k is None:
            continue
        pair = (k["item_id"], k["condition"])
        if r.get("error") or r.get("reply") is None:
            errors += 1
            error_pairs.add(pair)
        else:
            finished.add(pair)
    finished &= set(planned)
    return finished, errors, error_pairs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run the sheet test against one Ollama model.")
    ap.add_argument("--endpoint", required=True, help="Ollama base URL, for example http://127.0.0.1:11436")
    ap.add_argument("--model", required=True)
    ap.add_argument("--tasks", required=True, help="path to tasks.jsonl")
    ap.add_argument("--out", required=True, help="run folder (created if missing)")
    ap.add_argument("--seed", required=True, type=int, help="seed for the call order (recorded in key.json)")
    ap.add_argument("--null", action="store_true", help="replace C2 with a second copy of C1, labelled C2null")
    ap.add_argument("--limit", type=int, default=None, help="only the first N pairs of the shuffled order (dry run; use its own --out)")
    ap.add_argument("--num-ctx", type=int, default=4096)
    ap.add_argument("--num-predict", type=int, default=400)
    ap.add_argument("--timeout", type=float, default=600.0, help="seconds per call before it is recorded as an error")
    ap.add_argument("--conditions", default=os.path.join(HERE, "conditions.json"))
    a = ap.parse_args(argv)

    cond, systems = load_conditions(a.conditions)
    tasks = score_auto.load_jsonl(a.tasks)
    problems = score_auto.validate_tasks(tasks)
    if problems:
        print("REFUSING: task file problems:")
        for p in problems:
            print("  " + p)
        return 2
    for w in score_auto.mode_warnings(tasks):
        print(w)
    by_id = dict((t["item_id"], t) for t in tasks)

    labels = ["C0", "C1", "C2null" if a.null else "C2"]
    pairs = [(t["item_id"], c) for t in tasks for c in labels]
    random.Random(a.seed).shuffle(pairs)
    if a.limit is not None:
        pairs = pairs[:a.limit]

    os.makedirs(a.out, exist_ok=True)
    key_path = os.path.join(a.out, "key.json")
    raw_path = os.path.join(a.out, "raw.ndjson")
    meta = {
        "model": a.model,
        "seed": a.seed,
        "null": bool(a.null),
        "limit": a.limit,
        "tasks_path": os.path.abspath(a.tasks),
        "tasks_sha256": sha256_file(a.tasks),
        "conditions_path": os.path.abspath(a.conditions),
        "conditions_sha256": sha256_file(a.conditions),
        "checklist_sha256": dict((n, i["sha256"]) for n, i in cond["files"].items()),
        "num_ctx": a.num_ctx,
        "num_predict": a.num_predict,
        "conditions": labels,
        "options_fixed": FIXED_OPTIONS,
        "think": False,
        "planned_pairs": [list(p) for p in pairs],
    }
    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as fh:
            key = json.load(fh)
        old = key["meta"]
        diffs = [k for k in IDENTITY_KEYS if old.get(k) != meta.get(k)]
        if diffs:
            print("REFUSING to resume: this run folder belongs to a different run. Differs in: " + ", ".join(diffs))
            for k in diffs:
                print("  %s: folder has %r, this command has %r" % (k, old.get(k), meta.get(k)))
            return 2
        key["meta"].setdefault("endpoints_used", [])
    else:
        key = {"meta": meta, "ids": {}}
        key["meta"]["endpoints_used"] = []
        key["meta"]["created"] = now_iso()
    if a.endpoint not in key["meta"]["endpoints_used"]:
        key["meta"]["endpoints_used"].append(a.endpoint)
    write_json_atomic(key_path, key)

    raw = score_auto.load_jsonl(raw_path) if os.path.exists(raw_path) else []
    for r in raw:
        if r.get("id") not in key["ids"]:
            print("REFUSING: raw.ndjson has id %r that key.json does not know. The folder is damaged." % r.get("id"))
            return 2
    finished, _, error_pairs = coverage(pairs, key["ids"], raw)
    todo = [p for p in pairs if p not in finished]
    retrying = [p for p in todo if p in error_pairs]
    print("run folder: %s" % a.out)
    print("planned pairs %d, already finished %d, to call now %d" % (len(pairs), len(finished), len(todo)))
    if retrying:
        print("NOTE: %d of those pairs have only error records so far; they are being tried again now. "
              "The old error records stay in raw.ndjson." % len(retrying))

    for n, (item_id, label) in enumerate(todo, 1):
        oid = secrets.token_hex(8)
        while oid in key["ids"]:
            oid = secrets.token_hex(8)
        # The key entry is written before the call, so a raw record never exists without one.
        key["ids"][oid] = {"item_id": item_id, "condition": label}
        write_json_atomic(key_path, key)

        options = dict(FIXED_OPTIONS)
        options["num_ctx"] = a.num_ctx
        options["num_predict"] = a.num_predict
        payload = {
            "model": a.model,
            "messages": [
                {"role": "system", "content": systems[label]},
                {"role": "user", "content": by_id[item_id]["prompt"]},
            ],
            "stream": False,
            "think": False,
            "options": options,
        }
        rec = {"id": oid, "item_id": item_id, "model": a.model, "start": now_iso(), "end": None,
               "options": options, "stream": False, "think": False, "reply": None,
               "prompt_eval_count": None, "eval_count": None, "total_duration": None,
               "load_duration": None, "prompt_eval_duration": None, "eval_duration": None,
               "done_reason": None, "ctx_warning": None, "error": None}
        try:
            resp = TRANSPORT(a.endpoint, payload, a.timeout)
            if not isinstance(resp, dict):
                raise RuntimeError("server returned a non-object: %r" % (resp,))
            if resp.get("error"):
                raise RuntimeError("server error: %s" % resp.get("error"))
            msg = resp.get("message")
            if not isinstance(msg, dict) or not isinstance(msg.get("content"), str):
                raise RuntimeError("no message.content in server reply (keys: %s)" % sorted(resp.keys()))
            rec["reply"] = msg["content"]
            for k in ("prompt_eval_count", "eval_count", "total_duration", "load_duration",
                      "prompt_eval_duration", "eval_duration", "done_reason"):
                rec[k] = resp.get(k)
            pec = rec["prompt_eval_count"]
            if isinstance(pec, int):
                # Heuristic only: Ollama truncates silently when the prompt plus the reply budget
                # exceeds num_ctx. A cached prefix can make prompt_eval_count read low.
                rec["ctx_warning"] = (pec + a.num_predict) > a.num_ctx
        except Exception as e:  # every failure becomes a record, never a silent retry
            rec["error"] = "%s: %s" % (type(e).__name__, e)
        rec["end"] = now_iso()
        append_line(raw_path, rec)
        status = "ERROR " + rec["error"] if rec["error"] else "ok"
        if rec.get("ctx_warning"):
            status += " (ctx_warning: prompt tokens + num_predict > num_ctx)"
        print("[%d/%d] %s %s %s" % (n, len(todo), oid, item_id, status))
        sys.stdout.flush()

    raw = score_auto.load_jsonl(raw_path) if os.path.exists(raw_path) else []
    finished, errors, _ = coverage(pairs, key["ids"], raw)
    missing = len(pairs) - len(finished)
    print("COVERAGE expected %d, captured %d, missing %d, error records %d"
          % (len(pairs), len(finished), missing, errors))
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
