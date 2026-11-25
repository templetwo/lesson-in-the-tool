"""Offline structural checks for the published 001 and 001b evidence.

This checks the record, not the judge's judgment. Historical error attempts and
the one documented score-id correction remain visible. No archive file is written.
Python 3.9+, standard library only.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key %r" % key)
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (OSError, ValueError) as exc:
        raise ValueError("%s: %s" % (path, exc)) from exc


def read_rows(path):
    rows = []
    try:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            require(bool(line.strip()), "blank JSONL line %d" % number)
            try:
                row = json.loads(line, object_pairs_hook=unique_object)
            except ValueError as exc:
                raise ValueError("line %d: %s" % (number, exc)) from exc
            require(isinstance(row, dict), "line %d is not an object" % number)
            rows.append(row)
    except (OSError, ValueError) as exc:
        raise ValueError("%s: %s" % (path, exc)) from exc
    return rows


def index(rows, label, field="id"):
    result = {}
    for row in rows:
        value = row.get(field)
        require(isinstance(value, str) and bool(value), "%s: invalid %s" % (label, field))
        require(value not in result, "%s: duplicate %s %r" % (label, field, value))
        result[value] = row
    return result


def same_ids(actual, expected, label):
    require(set(actual) == set(expected), "%s: IDs do not match (missing=%s, extra=%s)" %
            (label, sorted(set(expected) - set(actual)), sorted(set(actual) - set(expected))))


def scores(path, expected):
    result = index(read_rows(path), str(path))
    same_ids(result, expected, str(path))
    for oid, row in result.items():
        require(set(row) == {"id", "pass"} and type(row["pass"]) is bool,
                "%s: %s must have id and boolean pass" % (path, oid))
    return result


def check_packet(row, oid, task, reply, label):
    require(row == {"id": oid, "prompt": task["prompt"],
                    "pass_rule": task["pass_rule"], "reply": reply},
            "%s: packet content differs from source for %s" % (label, oid))


def check_run(base, name, tasks, published):
    run = base / "runs" / name
    key = read_json(run / "key.json")
    labels = ["C0", "C1", "C2null" if name.endswith("_null") else "C2"]
    require(key["meta"]["conditions"] == labels, "%s: unexpected conditions" % name)
    plan = key["meta"]["planned_pairs"]
    require(isinstance(plan, list) and all(isinstance(p, list) and len(p) == 2
            and all(isinstance(v, str) for v in p) for p in plan), "%s: malformed plan" % name)
    pairs = [tuple(p) for p in plan]
    require(len(set(pairs)) == len(pairs), "%s: duplicate planned pair" % name)
    require(set(pairs) == {(item, label) for item in tasks for label in labels},
            "%s: planned pairs must cover every task and condition" % name)
    raw = index(read_rows(run / "raw.ndjson"), name + " raw")
    same_ids(raw, key["ids"], name + " raw/key")
    attempts = {pair: [] for pair in pairs}
    captured = {}
    for oid, row in raw.items():
        entry = key["ids"][oid]
        pair = (entry["item_id"], entry["condition"])
        require(pair in attempts, "%s: key contains unplanned pair %r" % (name, pair))
        require(row.get("item_id") == pair[0], "%s: raw/key item mismatch for %s" % (name, oid))
        attempts[pair].append(oid)
        if row.get("error") is not None:
            require(isinstance(row["error"], str) and row["error"] and row.get("reply") is None,
                    "%s: invalid error attempt %s" % (name, oid))
        else:
            require(isinstance(row.get("reply"), str), "%s: reply is not text for %s" % (name, oid))
            captured[oid] = row
    missing = set()
    for pair, ids in attempts.items():
        require(1 <= len(ids) <= 2, "%s: expected one attempt and at most one retry for %r" % (name, pair))
        successes = [oid for oid in ids if oid in captured]
        require(len(successes) <= 1, "%s: duplicate captured replies for %r" % (name, pair))
        if len(ids) == 2:
            require(ids[0] not in captured, "%s: retry follows a captured reply for %r" % (name, pair))
        if not successes:
            missing.add(pair)
    declared_missing = {
        "lfm3": {("F2-05", "C1"), ("F3-02", "C1"), ("F6-02", "C1")},
        "lfm3_null": {("F2-05", "C1"), ("F2-05", "C2null")},
    }.get(name, set())
    require(missing == declared_missing, "%s: missing replies differ from 001 ERRATA E2" % name)
    packet = index(read_rows(run / "judge_packet.jsonl"), name + " packet")
    same_ids(packet, captured, name + " packet/captured")
    judge = scores(run / "judge_scores.jsonl", captured)
    auto = index(read_rows(run / "auto_scores.ndjson"), name + " auto")
    same_ids(auto, captured, name + " auto/captured")
    allowed = {"two_sided": {"pass", "fail"}, "fail_only": {"fail", "no_verdict"},
               "none": {"no_verdict"}}
    for oid, row in captured.items():
        task = tasks[row["item_id"]]
        check_packet(packet[oid], oid, task, row["reply"], name)
        verdict = auto[oid]
        require(set(verdict) == {"id", "verdict", "rule"} and
                isinstance(verdict["rule"], str) and isinstance(verdict["verdict"], str) and
                verdict["verdict"] in allowed[task["auto_mode"]],
                "%s: invalid automatic verdict for %s" % (name, oid))
    same_ids(published, labels, name + " result conditions")
    for label in labels:
        ids = [oid for oid in captured if key["ids"][oid]["condition"] == label]
        text = [oid for oid in ids if captured[oid]["reply"].strip()]
        totals = {"captured": len(ids), "pass": sum(judge[oid]["pass"] for oid in ids),
                  "empty": len(ids) - len(text), "text": len(text),
                  "text_pass": sum(judge[oid]["pass"] for oid in text)}
        fields = {"captured", "pass", "empty", "text", "text_pass"} if name.startswith("lfm3") else {"captured", "pass", "empty"}
        require(set(published[label]) == fields, "%s %s: unexpected result fields" % (name, label))
        for field, value in published[label].items():
            require(type(value) is int and value == totals[field],
                    "%s %s: PILOT_RESULTS %s differs from evidence" % (name, label, field))
    return key, captured, "%s: %d attempts, %d error attempts, %d captured, %d unresolved tasks; published counts match" % (
        name, len(raw), len(raw) - len(captured), len(captured), len(missing))


def check_selftest(folder, tasks, fixtures):
    key = read_json(folder / "judge_selftest_key.json")
    packet = index(read_rows(folder / "judge_selftest_packet.jsonl"), str(folder))
    same_ids(packet, key, str(folder))
    judge = scores(folder / "judge_selftest_scores.jsonl", key)
    require(len(key) == 38, "%s: expected 38 selftest cases" % folder)
    actual = []
    for oid, entry in key.items():
        expected = entry["expected"]
        require(expected in ("pass", "fail"), "%s: invalid expected verdict" % folder)
        require(judge[oid]["pass"] == (expected == "pass"), "%s: selftest verdict differs for %s" % (folder, oid))
        check_packet(packet[oid], oid, tasks[entry["item_id"]], packet[oid]["reply"], str(folder))
        actual.append((entry["item_id"], packet[oid]["reply"], expected))
    require(Counter(actual) == Counter((r["item_id"], r["reply"], r["expected"]) for r in fixtures),
            "%s: selftest cases differ from frozen fixtures" % folder)


def check_rejudge(base, tasks, house_key, house):
    setup = read_json(base / "work/setup_map.json")
    require(setup == {oid: entry["condition"] for oid, entry in house_key["ids"].items()},
            "001b: setup_map differs from 001 house key")
    masked = index(read_rows(base / "work/masked.jsonl"), "001b masked")
    same_ids(masked, house, "001b masked/house")
    for oid, row in masked.items():
        require(row["item_id"] == house[oid]["item_id"] and
                row["reply_original_sha256"] == hashlib.sha256(house[oid]["reply"].encode("utf-8")).hexdigest() and
                isinstance(row["reply_masked"], str) and type(row["changed"]) is bool and
                row["changed"] == (row["reply_masked"] != house[oid]["reply"]),
                "001b: masked source metadata differs for %s" % oid)
    folder = base / "work/final"
    original = (folder / "scores/U2.jsonl").read_bytes()
    restored = (folder / "scores/U2_id_restored.jsonl").read_bytes()
    old, new = b'"a72690cc274f06f"', b'"a72690cca274f06f"'
    require(original.count(old) == 1 and original.count(new) == 0 and
            original.replace(old, new) == restored,
            "001b: U2 restored scores must change only the documented E1 id")
    original_scores = index(read_rows(folder / "scores/U2.jsonl"), "001b original U2 scores")
    require(original_scores[old.decode().strip('"')] == {"id": old.decode().strip('"'), "pass": True},
            "001b: original E1 score differs from erratum")
    seen = set(house)
    summaries = []
    for name in ("U1", "U2", "M"):
        key = read_json(folder / "keys" / (name + ".json"))
        entries = key["entries"]
        packet = index(read_rows(folder / "packets" / name / "packet.jsonl"), "001b " + name)
        same_ids(packet, entries, "001b " + name + " packet/key")
        require(len(entries) == 126 and key["lines"] == 126 and key["packet"] == name,
                "001b %s: expected 126 entries in named packet" % name)
        reply_ids = [entry["reply_id"] for entry in entries.values()]
        require(len(set(reply_ids)) == len(reply_ids) and set(reply_ids) == set(house),
                "001b %s: reply mapping is not one-to-one" % name)
        require(not (set(entries) & seen), "001b %s: packet IDs overlap raw or another packet" % name)
        seen.update(entries)
        filename = "U2_id_restored.jsonl" if name == "U2" else name + ".jsonl"
        judge = scores(folder / "scores" / filename, entries)
        for oid, entry in entries.items():
            rid = entry["reply_id"]
            require(entry["item_id"] == house[rid]["item_id"], "001b %s: item mismatch for %s" % (name, oid))
            reply = masked[rid]["reply_masked"] if name == "M" else house[rid]["reply"]
            check_packet(packet[oid], oid, tasks[entry["item_id"]], reply, "001b " + name)
        counts = [sum(row["pass"] for oid, row in judge.items() if setup[entries[oid]["reply_id"]] == label)
                  for label in ("C0", "C1", "C2")]
        summaries.append("001b %s: 126 mapped scores; C0/C1/C2 passes %s" % (name, "/".join(map(str, counts))))
    return summaries


def verify_evidence(root: Path) -> list:
    """Return check receipts, or raise ValueError; never infer missing evidence."""
    try:
        pilot = root / "experiments/001-sheet-pilot"
        rejudge = root / "experiments/001b-judge-lean"
        tasks = index(read_rows(pilot / "tasks/tasks.jsonl"), "001 tasks", "item_id")
        require(len(tasks) == 42, "001: expected 42 tasks")
        published = read_json(pilot / "PILOT_RESULTS.json")["results"]
        names = ("house", "house_null", "lfm3", "lfm3_null")
        same_ids(published, names, "001 published runs")
        results, summaries = {}, []
        for name in names:
            key, captured, summary = check_run(pilot, name, tasks, published[name])
            results[name] = (key, captured)
            summaries.append(summary)
        fixtures = read_rows(pilot / "tasks/selftest_replies.jsonl")
        for folder in (pilot / "runs/judge_selftest", rejudge / "work/judge_selftest"):
            check_selftest(folder, tasks, fixtures)
        summaries.append("001 and 001b: both judge selftests match all 38 frozen cases and expected verdicts")
        summaries.extend(check_rejudge(rejudge, tasks, *results["house"]))
        return summaries
    except (OSError, KeyError, TypeError, IndexError) as exc:
        raise ValueError("archive evidence is missing or malformed: %s" % exc) from exc
