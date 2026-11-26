"""Tally (the script scoring) for Test 1, The Sort.

Usage: /usr/bin/python3 -B tally.py --config TALLY_CONFIG.json [--allow-fixture]

Version 2 (2026-11-25, after PICKS_20261125.md): sorters are in groups that are never pooled; the main home decides
every figure; second homes are reported beside; the house table comparison gives exact and overlap counts.

Fix round (2026-11-25, ../FIX_BRIEF_test1.md), also refused before anything is counted: (A) a run whose manifest or
any result names a caller not on real_callers, unless --allow-fixture (then tally.json starts with "status":
"FIXTURE, NOT DATA", judgment_sentences.txt starts with that line, and so does the first printed line; a refusal
still prints only its REFUSED line); (B) a group spanning fewer providers than its min_providers, or providers that
differ from the key's; (D) key lines not exactly 1..N, a (sorter, repeat) not exactly once in the key's prompts or
in the results, a label map that is not one to one onto exactly the lines 1..N; (E) a stored parse_ok, errors or
rows that differ from a fresh parse of raw_reply; (F) a manifest that lists a file not expected or a path twice, an
expected prompt missing, anything on disk in results/ or prompts/ that the manifest does not list.

Config keys:
  run_dir             the runner's output folder
  sorters             [{"name": ..., "group": ..., "provider": ...}], must match the run's key exactly. The set of
                      expected result and prompt files comes from HERE, not from the manifest. A single-sorter group
                      gets descriptive counts only, with no classes or agreement statistics.
  groups              required, may be {}: {"cloud": {"min_providers": 3}}; the same rule as the runner's
  real_callers        optional, default []: caller names whose runs are data; never "fixture" or "dryrun"
  repeats             repeats expected per sorter
  cut_points_by_size  {"6": {"settled_min": 5, "leaning_min": 4}, ...}; required (may be {}), no defaults. A group
                      whose size has no entry gets the raw "k of n" and no settled / leaning / contested word.
                      Size "1" thresholds are refused; a single-sorter group is always descriptive only.
  bootstrap           {"seed": int, "draws": int, "level": float}
  out_dir             (CLI only) where tally.json and judgment_sentences.txt go; inside this folder, new or empty
  house_table         optional: JSON {"rows": [{"line_number": n, "home_main": h, "home_second": h or null}, ...]}
                      covering every line once

It refuses, printing nothing but the refusal and writing nothing, when: an expected result file or the key is missing
on disk or from the manifest; the run holds results the config does not expect; a hash recorded by the runner no
longer matches; any file has dry_run anything but false at the top or on any row, or a row without the flag, or the
value DRYRUN in a home field; a result or the key disagrees with the config's sorters and groups; a result does not
match the key; the config or the house table is malformed.

Definitions (all settings are written into the output). Everything below is computed PER GROUP; groups are never
pooled.
  majority main home    for one sorter and line: the main home given in MORE THAN HALF of the expected repeats. A
                        repeat whose reply failed to parse gives no home, but still counts in the denominator.
                        Otherwise "no majority".
  modal home            per line: the main home that is the majority main home of the most sorters in the group.
                        Ties are all listed.
  modal_count           how many of the group's sorters have the modal home as their majority main home, also given
                        as count_text "k of n".
  class                 settled if modal_count >= settled_min; leaning if >= leaning_min; else contested; null when
                        cut_points_by_size has no entry for the group's size.
  steadiness            per sorter, main home only, both readings of the draft: share of lines where the repeats are
                        not all the same (a failed repeat counts as not the same), and share of lines with no majority.
  agreement             Fleiss' kappa and Krippendorff's alpha (nominal) on majority main homes; "no majority" is
                        missing; Fleiss is not computed when any value is missing. Percentile bootstrap over lines,
                        same resamples for both; undefined resamples counted and reported. No verbal labels.
                        Groups of one or two have empty agreement with an agreement_note explaining why. Groups
                        of two retain their existing rule; a single-sorter group also never receives classes.
  second homes          per line: by_majority = how many sorters have a majority second home (a second home given in
                        more than half of the expected repeats) and which; raw = how many parsed replies gave any
                        second home, out of the parsed replies, and which. Never used in any figure above.
  parse failures        counted per group (out of the group's replies); also listed once with their reasons. Never
                        counted across groups.
  house table           rows with a home not on the list are left out and named. For each sorter and compared line,
                        the sorter's homes are its majority main home plus its majority second home if any.
                        exact = same main home and the same set of homes; overlap = at least one home shared (so
                        every exact match is also an overlap match). The two counts are reported separately and
                        never added. A sorter with no majority main home on a line matches neither.

The "what remains judgment" sentences are copied, per line, group, sorter and repeat, into judgment_sentences.txt
for a person to read. This code never scores, counts, searches or classifies them.

Two-turn and callers build (2026-11-25, picks 9 to 12):
  * Homes come from turn 1 only (raw_reply, parse_ok, parse_errors, rows at the top of each result). Nothing in the
    counting of homes reads "turn2"; tests show that removing or breaking every turn-2 reply changes no figure.
  * Sentences come from turn 2 ("turn2": sent, not_sent_reason, raw_reply, parse_ok, parse_errors, rows). The
    judgment file says "(sort reply failed to parse; question not asked)" or "(question reply failed to parse; no
    sentence)" where a sentence is missing.
  * Fix E covers both turns: turn 2 must have been sent when turn 1 parsed, except a proven F-rule usage stop.
    A sent turn 2's stored parse must equal a fresh parse of its raw_reply. A usage stop retains the first answer
    and counts the question as not sent, with no failed sent question; the call and budget records must agree.
    After a failed first sort, turn 2 must be exactly the runner's ordinary not-sent record.
  * Each group carries "turn2": {"sent", "failed" (sent but did not parse), "not_sent", "of_replies"}, printed as
    "turn 2 (the question): failed F of S sent; not sent N".
  * A run made with caller "by_sorter" lists its adapters in the manifest's "callers"; each must be on real_callers
    and the list must equal the set of the results' callers. "by_sorter" itself may never be on real_callers.
  * Helix record 82519 (the Codex seat's read-back): settings carried the key "groups" twice, so the written report
    lost the config's min_providers. The sentence now has its own key, "groups_note".
  * Codex fix round: a by_sorter key must carry real_callers as a complete sorter-to-caller map. Every repeat's
    result caller must equal that saved assignment, including failed sorts. The global caller allow-list remains
    a separate check. A saved map requires manifest caller by_sorter; changing the mode cannot disable the binding.
    Legacy single-caller runs need no map. A result carrying persistence_state may be tallied only when that state
    is "complete"; older results without the field retain their existing validation.
"""
import argparse
import json
import math
import os
import random
import sys
from collections import Counter
from fractions import Fraction

from common import Refuse, DRYRUN, inside_here, load_json, write_json, sha256_file, clock
from reply_parser import parse_sort_reply, parse_question_reply
from runner import check_providers, turn2_not_sent

HOME_FIELDS = ("home", "home_main", "home_second")
SORT_FAILED = "(sort reply failed to parse; question not asked)"
QUESTION_FAILED = "(question reply failed to parse; no sentence)"
USAGE_STOP = "sorter_output_limit_exceeded"
USAGE_STOP_ERROR = "sorter stopped after reported output usage exceeded the effective call limit"
QUESTION_STOPPED = "(question not asked: sorter_output_limit_exceeded)"
FIXTURE_MARK = "FIXTURE, NOT DATA"
LIMIT_ENDINGS_NOTE = (
    "Counts use provider-reported limit/length endings, not proof that the configured output cap caused them. "
    "Zero means no such marker was recorded; missing or redacted evidence and F-stopped sorts may still limit "
    "what was observed. Comparisons involving a sorter with a recorded limit ending or F stop must report "
    "that limitation.")


# ---------- statistics ----------

def fleiss_kappa(units):
    """units: list of lists of category values, one list per line. Returns float, or None when undefined."""
    if not units or any(v is None for u in units for v in u):
        return None
    n = len(units[0])
    if n < 2 or any(len(u) != n for u in units):
        return None
    N = len(units)
    totals = Counter()
    p_bar = Fraction(0)
    for u in units:
        c = Counter(u)
        totals.update(c)
        p_bar += Fraction(sum(x * x for x in c.values()) - n, n * (n - 1))
    p_bar /= N
    p_e = sum(Fraction(t, N * n) ** 2 for t in totals.values())
    if p_e == 1:
        return None
    return float((p_bar - p_e) / (1 - p_e))


def krippendorff_alpha_nominal(units):
    """Missing values are None. Units with fewer than two values are not pairable and are left out."""
    o_same = Fraction(0)
    n_c = Counter()
    for u in units:
        vals = [v for v in u if v is not None]
        m = len(vals)
        if m < 2:
            continue
        c = Counter(vals)
        for cat, cnt in c.items():
            o_same += Fraction(cnt * (cnt - 1), m - 1)
            n_c[cat] += cnt
    n = sum(n_c.values())
    if n < 2:
        return None
    expected_diff = n * n - sum(x * x for x in n_c.values())
    if expected_diff == 0:
        return None
    observed_diff = n - o_same
    return float(1 - Fraction(n - 1) * observed_diff / expected_diff)


def percentile_interval(values, level):
    v = sorted(values)
    m = len(v)
    if m == 0:
        return None
    lo = int(math.floor(m * (1 - level) / 2))
    hi = int(math.ceil(m * (1 + level) / 2)) - 1
    return [v[max(0, min(m - 1, lo))], v[max(0, min(m - 1, hi))]]


def bootstrap(units, fn, seed, draws, level):
    rng = random.Random(seed)
    n = len(units)
    vals, undefined = [], 0
    for _ in range(draws):
        x = fn([units[rng.randrange(n)] for _ in range(n)])
        if x is None:
            undefined += 1
        else:
            vals.append(x)
    return {"interval": percentile_interval(vals, level), "draws": draws, "draws_undefined": undefined,
            "seed": seed, "level": level, "method": "percentile, lines resampled with replacement"}


# ---------- checks ----------

def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def check_config(cfg, need_out=False):
    for k in ("run_dir", "sorters", "groups", "repeats", "cut_points_by_size", "bootstrap"):
        if k not in cfg:
            raise Refuse("tally config is missing %s" % k)
    known = {"run_dir", "sorters", "groups", "repeats", "cut_points_by_size", "bootstrap", "out_dir", "house_table",
             "real_callers"}
    if set(cfg) - known:
        raise Refuse("tally config has unknown keys %s" % sorted(set(cfg) - known))
    rc = cfg.get("real_callers", [])
    if not isinstance(rc, list) or len(set(rc)) != len(rc) or not all(isinstance(c, str) and c.strip() for c in rc) \
            or any(c.casefold() in ("fixture", DRYRUN.casefold(), "by_sorter") for c in rc):
        raise Refuse("real_callers must be a list of distinct non-empty caller names, and may never name the "
                     "fixture or dryrun callers or by_sorter; got %r" % (rc,))
    s = cfg["sorters"]
    if not isinstance(s, list) or not s:
        raise Refuse("sorters must be a non-empty list of {name, group, provider}")
    for e in s:
        if not isinstance(e, dict) or set(e) != {"name", "group", "provider"} or \
                not all(isinstance(e[f], str) and e[f] for f in ("name", "group")):
            raise Refuse("each sorter must be exactly {\"name\": ..., \"group\": ..., \"provider\": ...}; got %r"
                         % (e,))
    names = [e["name"] for e in s]
    if len(set(names)) != len(names):
        raise Refuse("a sorter name is repeated")
    check_providers(s, cfg["groups"])  # fix B, the same rule the runner applies
    if not _is_int(cfg["repeats"]) or cfg["repeats"] < 1:
        raise Refuse("repeats must be a whole number of at least 1")
    cps = cfg["cut_points_by_size"]
    if not isinstance(cps, dict):
        raise Refuse("cut_points_by_size must be an object keyed by group size, for example {\"6\": {...}}")
    if "1" in cps:
        raise Refuse("cut points for size 1 are not allowed; single-sorter groups are descriptive only")
    for size, cp in cps.items():
        if not (isinstance(size, str) and size.isdigit() and str(int(size)) == size and int(size) >= 1):
            raise Refuse("cut_points_by_size key %r is not a group size" % (size,))
        if not isinstance(cp, dict) or set(cp) != {"settled_min", "leaning_min"}:
            raise Refuse("cut points for size %s must give exactly settled_min and leaning_min" % size)
        if not (_is_int(cp["settled_min"]) and _is_int(cp["leaning_min"])
                and 1 <= cp["leaning_min"] <= cp["settled_min"] <= int(size)):
            raise Refuse("cut points for size %s must satisfy 1 <= leaning_min <= settled_min <= %s; got %s"
                         % (size, size, cp))
    b = cfg["bootstrap"]
    if not isinstance(b, dict) or set(b) != {"seed", "draws", "level"}:
        raise Refuse("bootstrap must give exactly seed, draws and level")
    if not (_is_int(b["seed"]) and _is_int(b["draws"]) and b["draws"] >= 1
            and isinstance(b["level"], float) and 0 < b["level"] < 1):
        raise Refuse("bootstrap seed and draws must be whole numbers (draws >= 1) and level a number between 0 and 1")
    if need_out:
        out = cfg.get("out_dir")
        if not out:
            raise Refuse("tally config needs out_dir")
        if not inside_here(out):
            raise Refuse("out_dir %s is outside this folder" % out)
        if os.path.exists(out) and (not os.path.isdir(out) or os.listdir(out)):
            raise Refuse("out_dir %s exists and is not an empty folder" % out)


def check_not_dry(obj, where):
    """dry_run must be false at the top and on every row; DRYRUN must not appear in any HOME field.
    Sentences are never looked at here."""
    if not isinstance(obj, dict) or obj.get("dry_run", None) is not False:
        raise Refuse("%s: top-level dry_run is not false (dry-run files are never tallied)" % where)

    def walk(x, path):
        if isinstance(x, dict):
            if "dry_run" in x and x["dry_run"] is not False:
                raise Refuse("%s: dry_run is not false at %s" % (where, path or "top"))
            for k, v in x.items():
                if (k in HOME_FIELDS and v == DRYRUN) or (k == "home_order" and isinstance(v, list) and DRYRUN in v):
                    raise Refuse("%s: holds the reserved home DRYRUN at %s/%s" % (where, path, k))
                walk(v, path + "/" + str(k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                if isinstance(v, dict) and v.get("dry_run", None) is not False:
                    raise Refuse("%s: row %s[%d] does not say dry_run false" % (where, path, i))
                walk(v, "%s[%d]" % (path, i))
    walk(obj, "")


def _safe_rel(p):
    return isinstance(p, str) and p and not os.path.isabs(p) and ".." not in p.split("/")


def load_house_table(path, line_numbers):
    table = load_json(path, "house table")
    rows = table.get("rows") if isinstance(table, dict) else None
    if not isinstance(rows, list):
        raise Refuse("house table must be {\"rows\": [...]}")
    by_line = {}
    for r in rows:
        if not isinstance(r, dict) or set(r) != {"line_number", "home_main", "home_second"} \
                or not _is_int(r["line_number"]) or not isinstance(r["home_main"], str) or not r["home_main"] \
                or not (r["home_second"] is None or (isinstance(r["home_second"], str) and r["home_second"])) \
                or r["home_second"] == r["home_main"]:
            raise Refuse("house table row is malformed: %r" % (r,))
        if r["line_number"] in by_line:
            raise Refuse("house table gives line %d twice" % r["line_number"])
        by_line[r["line_number"]] = r
    if sorted(by_line) != line_numbers:
        raise Refuse("house table lines %s do not match the run's lines %s" % (sorted(by_line), line_numbers))
    return by_line


# ---------- the tally ----------

def _majority(values, R):
    c = Counter(v for v in values if v is not None)
    top = [h for h, x in c.items() if 2 * x > R]
    return top[0] if top else None


def check_usage_stopped_question(res, where):
    """The only allowed question skip after a valid first answer: a bound F-rule stop.

    The reported aggregate is checked directly, without adding reasoning detail.
    These are consistency checks of saved evidence, not independent billing proof.
    """
    def refuse(detail):
        raise Refuse("%s: unproved usage-stop question skip (%s)" % (where, detail))

    t2 = res["turn2"]
    expected_t2 = {"dry_run": False, "sent": False, "not_sent_reason": USAGE_STOP,
                   "raw_reply": None, "parse_ok": False, "parse_errors": [], "rows": []}
    if t2 != expected_t2 or t2.get("sent") is not False or t2.get("parse_ok") is not False:
        refuse("question record")
    calls = res.get("calls")
    if not isinstance(calls, list) or len(calls) != 2 or not all(isinstance(c, dict) for c in calls):
        refuse("requires one actual first call and one skipped question")
    first, skipped = calls
    caller = res["caller"]
    if first.get("caller") != caller or not _is_int(first.get("turn")) or first["turn"] != 1 \
            or first.get("complete") is not True or first.get("error") is not None \
            or first.get("failure_reason") is not None or "sent" in first or "not_sent" in first:
        refuse("first-call identity or completion")
    check = first.get("usage_limit_check")
    if not isinstance(check, dict) or set(check) != {"status", "field", "reported_output_tokens", "limit"} \
            or check["status"] != "exceeded" or check["field"] not in ("output_tokens", "completion_tokens", "eval_count") \
            or not _is_int(check["limit"]) or not _is_int(check["reported_output_tokens"]) \
            or not 0 < check["limit"] < check["reported_output_tokens"]:
        refuse("first-call usage check")
    try:
        usage = json.loads(first.get("usage_json"))
    except (TypeError, ValueError):
        refuse("first-call usage JSON")
    if not isinstance(usage, dict) or not _is_int(usage.get(check["field"])) \
            or usage[check["field"]] != check["reported_output_tokens"]:
        refuse("reported usage differs from the triggering check")
    expected_skip = {"dry_run": False, "caller": caller, "turn": 2, "sent": False, "complete": False,
                     "error": USAGE_STOP_ERROR, "failure_reason": USAGE_STOP, "not_sent_reason": USAGE_STOP}
    if skipped != expected_skip or skipped.get("sent") is not False or skipped.get("complete") is not False:
        refuse("skipped-call record")
    budget = res.get("call_budget")
    if not isinstance(budget, dict) or not _is_int(budget.get("output_token_limit")) \
            or budget["output_token_limit"] != check["limit"] or not isinstance(budget.get("per_sorter"), dict):
        refuse("effective budget limit")
    spec = budget["per_sorter"].get(res["sorter"])
    if not isinstance(spec, dict) or spec.get("caller") != caller \
            or spec.get("stop") != {"reason": USAGE_STOP, "usage_limit_check": check} \
            or not _is_int(spec.get("planned")) or not _is_int(spec.get("attempted")) \
            or not 1 <= spec["attempted"] <= spec["planned"]:
        refuse("sorter stop binding")


def limit_ending_counts(res):
    """G: descriptive evidence only; never changes parsing, homes, or existing counts."""
    calls = res.get("calls", [])
    if not isinstance(calls, list):
        return 0, 0, 0
    ended = set()
    provider, caller = res.get("provider"), res.get("caller")
    for call in calls:
        if not isinstance(call, dict) or call.get("caller") != caller or call.get("provider") != provider \
                or not _is_int(call.get("turn")) or call["turn"] not in (1, 2) \
                or call.get("sent") is False or call.get("complete") is not False \
                or call.get("failure_reason") == "transport_error":
            continue
        marker = call.get("stop")
        cutoff = provider == "anthropic" and marker == "max_tokens"
        cutoff |= provider in ("deepseek", "ollama", "ollama-local-a", "ollama-local-b") and marker == "length"
        if provider in ("openai", "xai") and marker == "incomplete":
            try:
                body = json.loads(call.get("response_body_json"))
            except (TypeError, ValueError):
                body = None
            cutoff = isinstance(body, dict) and body.get("status") == "incomplete" \
                and isinstance(body.get("incomplete_details"), dict) \
                and body["incomplete_details"].get("reason") == "max_output_tokens"
        if cutoff:
            ended.add(call["turn"])
    unsent = False
    if len(calls) == 1 and res.get("parse_ok") is False and res.get("raw_reply") is None:
        expected = {"dry_run": False, "caller": caller, "turn": 1, "sent": False, "complete": False,
                    "error": USAGE_STOP_ERROR, "failure_reason": USAGE_STOP, "not_sent_reason": USAGE_STOP}
        budget = res.get("call_budget", {})
        specs = budget.get("per_sorter", {}) if isinstance(budget, dict) else {}
        spec = specs.get(res.get("sorter"), {}) if isinstance(specs, dict) else {}
        stop = spec.get("stop", {}) if isinstance(spec, dict) else {}
        check = stop.get("usage_limit_check", {}) if isinstance(stop, dict) else {}
        unsent = calls[0] == expected and _is_int(calls[0].get("turn")) \
            and calls[0].get("sent") is False and calls[0].get("complete") is False \
            and isinstance(budget, dict) and isinstance(spec, dict) and isinstance(stop, dict) \
            and isinstance(check, dict) and spec.get("caller") == caller \
            and stop.get("reason") == USAGE_STOP and check.get("status") == "exceeded" \
            and check.get("field") in ("output_tokens", "completion_tokens", "eval_count") \
            and _is_int(check.get("limit")) and _is_int(check.get("reported_output_tokens")) \
            and 0 < check["limit"] < check["reported_output_tokens"] \
            and _is_int(budget.get("output_token_limit")) \
            and budget.get("output_token_limit") == check["limit"]
    return int(1 in ended), int(2 in ended), int(unsent)


def compute(cfg, need_out=False, allow_fixture=False):
    check_config(cfg, need_out)
    run_dir, R = cfg["run_dir"], cfg["repeats"]
    sorters = [e["name"] for e in cfg["sorters"]]
    group_of = {e["name"]: e["group"] for e in cfg["sorters"]}
    groups = []
    for e in cfg["sorters"]:
        if e["group"] not in groups:
            groups.append(e["group"])

    man_path = os.path.join(run_dir, "manifest.json")
    manifest = load_json(man_path, "manifest")
    check_not_dry(manifest, "manifest.json")
    listed = {}
    for row in manifest.get("files", []):
        if not _safe_rel(row.get("path")) or not isinstance(row.get("sha256"), str):
            raise Refuse("manifest has a malformed file row: %r" % (row,))
        if row["path"] in listed:
            raise Refuse("manifest lists %s twice" % row["path"])
        listed[row["path"]] = row["sha256"]
    expected = ["results/%s__r%d.json" % (s, k) for s in sorters for k in range(1, R + 1)]
    expected_prompts = ["prompts/%s__r%d.json" % (s, k) for s in sorters for k in range(1, R + 1)]
    for p in expected + expected_prompts + ["key.json"]:
        if not os.path.isfile(os.path.join(run_dir, p)):
            raise Refuse("expected file is missing: %s" % p)
        if p not in listed:
            raise Refuse("expected file is not listed in the runner's manifest: %s" % p)
    # Fix F: the manifest must list exactly the expected files, and results/ and prompts/ must hold nothing else.
    extra = sorted(p for p in listed if p not in set(expected + expected_prompts + ["key.json"]))
    if extra:
        raise Refuse("the manifest lists files the tally config does not expect: %s" % extra)
    for folder in ("results", "prompts"):
        for name in sorted(os.listdir(os.path.join(run_dir, folder))):
            if "%s/%s" % (folder, name) not in listed:
                raise Refuse("on disk but not listed in the manifest: %s/%s" % (folder, name))
    for p, h in sorted(listed.items()):
        full = os.path.join(run_dir, p)
        if not os.path.isfile(full):
            raise Refuse("file listed in the manifest is missing: %s" % p)
        if sha256_file(full) != h:
            raise Refuse("hash recorded by the runner no longer matches: %s" % p)

    # Fix A: only runs whose every caller is on the config's real_callers list are tallied as data. A test may pass
    # allow_fixture (never a config key, so a frozen config cannot carry it); every output then says FIXTURE_MARK.
    real = cfg.get("real_callers", [])
    result_callers = [(p, load_json(os.path.join(run_dir, p), p).get("caller")) for p in expected]
    if manifest.get("caller") == "by_sorter":
        listed_callers = manifest.get("callers")
        if not isinstance(listed_callers, list) or not all(isinstance(c, str) and c for c in listed_callers) \
                or listed_callers != sorted(set(listed_callers)):
            raise Refuse("manifest.json of a by_sorter run must list its callers, sorted and distinct")
        if set(listed_callers) != {c for _, c in result_callers}:
            raise Refuse("the manifest lists callers %s but the results name %s"
                         % (listed_callers, sorted({str(c) for _, c in result_callers})))
        callers_seen = [("manifest.json", c) for c in listed_callers] + result_callers
    else:
        callers_seen = [("manifest.json", manifest.get("caller"))] + result_callers
    no_caller = [w for w, c in callers_seen if not isinstance(c, str) or not c]
    if no_caller:
        raise Refuse("no caller recorded in %s" % no_caller)
    not_real = sorted({c for _, c in callers_seen if c not in real})
    if not_real and not allow_fixture:
        raise Refuse("caller(s) %s are not on the tally config's real_callers list %s; only runs by a listed real "
                     "caller are tallied as data" % (not_real, real))

    key = load_json(os.path.join(run_dir, "key.json"), "key")
    check_not_dry(key, "key.json")
    key_groups = {e.get("name"): (e.get("group"), e.get("provider")) for e in key.get("sorters", [])}
    cfg_groups = {e["name"]: (e["group"], e["provider"]) for e in cfg["sorters"]}
    if key_groups != cfg_groups or len(key.get("sorters", [])) != len(cfg_groups):
        raise Refuse("the config's sorters, groups and providers %s do not match the run's key %s"
                     % (sorted(cfg_groups.items()), sorted(key_groups.items(), key=str)))
    if "real_callers" in key and manifest.get("caller") != "by_sorter":
        raise Refuse("key.real_callers is present but the manifest caller is not by_sorter")
    assigned_callers = None
    if manifest.get("caller") == "by_sorter":
        assigned_callers = key.get("real_callers")
        if not isinstance(assigned_callers, dict) or not all(
                isinstance(s, str) and isinstance(c, str) and c.strip()
                for s, c in assigned_callers.items()):
            raise Refuse("key.real_callers of a by_sorter run must be an object mapping sorter names to "
                         "non-empty caller names")
        if set(assigned_callers) != set(sorters):
            raise Refuse("key.real_callers must name every sorter and only the sorters: missing %s, extra %s"
                         % (sorted(set(sorters) - set(assigned_callers)),
                            sorted(set(assigned_callers) - set(sorters))))
    # Fix D: before anything is counted, the key's lines are exactly 1..N, every (sorter, repeat) has exactly one
    # prompt in the key and one result, and each prompt's labels pair one to one onto exactly the lines 1..N.
    # The lists are checked before any dict is built, so a later duplicate cannot silently overwrite an earlier one.
    key_line_numbers = [r.get("line_number") for r in key.get("lines", [])]
    N = len(key_line_numbers)
    if N == 0 or key_line_numbers != list(range(1, N + 1)):
        raise Refuse("key lines are not numbered exactly 1 to N in order: %s" % key_line_numbers)
    want_pairs = {(s, k) for s in sorters for k in range(1, R + 1)}
    pair_count = Counter((p.get("sorter"), p.get("repeat")) for p in key.get("prompts", []))
    twice = sorted(x for x, c in pair_count.items() if c > 1)
    if twice:
        raise Refuse("key: (sorter, repeat) %s appear more than once in the prompts" % twice)
    if set(pair_count) != want_pairs:
        raise Refuse("key: the prompts do not hold each (sorter, repeat) of the config exactly once; extra %s, "
                     "missing %s" % (sorted(set(pair_count) - want_pairs, key=str),
                                     sorted(want_pairs - set(pair_count))))
    for p in key["prompts"]:
        labs = [e.get("label") for e in p.get("labels", [])]
        nums = [e.get("line_number") for e in p.get("labels", [])]
        if len(set(labs)) != len(labs) or not all(_is_int(n) for n in nums) \
                or sorted(nums) != list(range(1, N + 1)):
            raise Refuse("key: the label map of %s repeat %s does not pair its labels one to one onto exactly the "
                         "lines 1 to %d: %s" % (p.get("sorter"), p.get("repeat"), N, list(zip(labs, nums))))
    result_pairs = Counter()
    for s in sorters:
        for k in range(1, R + 1):
            res = load_json(os.path.join(run_dir, "results/%s__r%d.json" % (s, k)), "result")
            result_pairs[(res.get("sorter"), res.get("repeat"))] += 1
    if any(c != 1 for c in result_pairs.values()) or set(result_pairs) != want_pairs:
        raise Refuse("results do not hold each (sorter, repeat) of the config exactly once: %s"
                     % sorted(result_pairs.items(), key=str))

    line_text = {r["line_number"]: r["text"] for r in key["lines"]}
    line_numbers = sorted(line_text)
    maps, label_order, homes_set, home_order = {}, {}, None, {}
    for p in key["prompts"]:
        maps[(p["sorter"], p["repeat"])] = {e["label"]: e["line_number"] for e in p["labels"]}
        label_order[(p["sorter"], p["repeat"])] = [e["label"] for e in p["labels"]]
        home_order[(p["sorter"], p["repeat"])] = list(p["home_order"])
        hs = frozenset(p["home_order"])
        if homes_set is not None and hs != homes_set:
            raise Refuse("key: prompts were built from different home lists")
        homes_set = hs
    table = load_house_table(cfg["house_table"], line_numbers) if cfg.get("house_table") else None

    v_main = {s: {n: [] for n in line_numbers} for s in sorters}
    v_second = {s: {n: [] for n in line_numbers} for s in sorters}
    sentences = {n: [] for n in line_numbers}
    failures = []
    limit_endings = {s: {"sorter": s, "group": group_of[s], "message_1": 0, "message_2": 0,
                         "sorts_not_sent_after_f": 0} for s in sorters}
    turn2_seen = []  # (sorter, sent, parsed): used only for the turn-2 counts and never by any figure
    for s in sorters:
        for k in range(1, R + 1):
            p = "results/%s__r%d.json" % (s, k)
            res = load_json(os.path.join(run_dir, p), p)
            check_not_dry(res, p)
            if "persistence_state" in res and res["persistence_state"] != "complete":
                raise Refuse("%s: persistence_state must be complete before tallying; got %r"
                             % (p, res["persistence_state"]))
            if assigned_callers is not None and res.get("caller") != assigned_callers[s]:
                raise Refuse("%s says caller %r but key.real_callers assigns %r to sorter %r"
                             % (p, res.get("caller"), assigned_callers[s], s))
            if res.get("sorter") != s or res.get("repeat") != k or res.get("group") != group_of[s] \
                    or res.get("provider") != cfg_groups[s][1]:
                raise Refuse("%s says sorter %r group %r provider %r repeat %r; the config says %r group %r provider "
                             "%r repeat %r" % (p, res.get("sorter"), res.get("group"), res.get("provider"),
                                               res.get("repeat"), s, group_of[s], cfg_groups[s][1], k))
            if res.get("lines_sha256") != key["lines_source"]["sha256"] or res.get("homes_sha256") != key["homes_sha256"]:
                raise Refuse("%s was made from other lines or homes than the key records" % p)
            lab = maps.get((s, k))
            if lab is None:
                raise Refuse("key has no label map for %s" % p)
            # Fix E: reparse raw_reply with this prompt's labels (key order) and homes; the stored parse must equal it.
            fresh = parse_sort_reply(res.get("raw_reply"), label_order[(s, k)], home_order[(s, k)], dry_run=False)
            fresh_rows = [dict([("dry_run", False)] + list(r.items())) for r in fresh["rows"]]
            if res.get("parse_ok") is not fresh["ok"] or res.get("parse_errors") != fresh["errors"] \
                    or res.get("rows") != fresh_rows:
                raise Refuse("%s: the stored parse_ok, errors or rows differ from a fresh parse of its raw_reply"
                             % p)
            # Two-turn build: fix E for turn 2. Read here only to check it and to copy sentences; no count of homes
            # below this point reads anything from turn2.
            t2 = res.get("turn2")
            if not isinstance(t2, dict):
                raise Refuse("%s has no turn 2 record" % p)
            if res.get("parse_ok") is True:
                if t2.get("sent") is not True:
                    if t2.get("not_sent_reason") != USAGE_STOP:
                        raise Refuse("%s: turn 2 was not sent although the sort parsed" % p)
                    check_usage_stopped_question(res, p)
                else:
                    fresh2 = parse_question_reply(t2.get("raw_reply"), label_order[(s, k)])
                    fresh2_rows = [dict([("dry_run", False)] + list(r.items())) for r in fresh2["rows"]]
                    if t2.get("parse_ok") is not fresh2["ok"] or t2.get("parse_errors") != fresh2["errors"] \
                            or t2.get("rows") != fresh2_rows:
                        raise Refuse("%s: the stored turn 2 parse_ok, errors or rows differ from a fresh parse of its "
                                     "turn 2 raw_reply" % p)
            elif t2 != turn2_not_sent(False):
                raise Refuse("%s: the sort did not parse, so turn 2 must be the not-sent record; it is not" % p)
            if res.get("parse_ok") is True:
                rows = res.get("rows", [])
                bad = sorted(r.get("label") for r in rows) != sorted(lab) or any(
                    r.get("home_main") not in homes_set
                    or (r.get("home_second") is not None and (r["home_second"] not in homes_set
                                                              or r["home_second"] == r["home_main"]))
                    for r in rows)
                if bad:
                    raise Refuse("%s is marked parsed but its rows do not match the key" % p)
                for r in rows:
                    n = lab[r["label"]]
                    v_main[s][n].append(r["home_main"])
                    v_second[s][n].append(r["home_second"])
                said = {r["label"]: r["sentence"] for r in t2["rows"]} if t2["parse_ok"] else {}
                missing_sentence = QUESTION_STOPPED if t2["sent"] is False else QUESTION_FAILED
                for r in rows:
                    sentences[lab[r["label"]]].append((s, k, said.get(r["label"], missing_sentence)))
                turn2_seen.append((s, t2["sent"], t2["parse_ok"] is True))
            elif res.get("parse_ok") is False:
                if res.get("rows"):
                    raise Refuse("%s is a parse failure but carries rows" % p)
                failures.append({"sorter": s, "group": group_of[s], "repeat": k,
                                 "errors": res.get("parse_errors", []), "file": p})
                for n in line_numbers:
                    sentences[n].append((s, k, SORT_FAILED))
                turn2_seen.append((s, False, False))
            else:
                raise Refuse("%s has no parse_ok true or false" % p)
            for field, count in zip(("message_1", "message_2", "sorts_not_sent_after_f"), limit_ending_counts(res)):
                limit_endings[s][field] += count

    maj_main = {s: {n: _majority(v_main[s][n], R) for n in line_numbers} for s in sorters}
    maj_second = {s: {n: _majority(v_second[s][n], R) for n in line_numbers} for s in sorters}

    group_reports = {}
    for g in groups:
        members = [s for s in sorters if group_of[s] == g]
        group_reports[g] = group_report(cfg, g, members, line_numbers, R, v_main, v_second, maj_main, maj_second,
                                        failures, homes_set, table)
        # Two-turn build: turn 2 is counted here, after and apart from every figure group_report computed.
        mine = [x for x in turn2_seen if group_of[x[0]] == g]
        group_reports[g]["turn2"] = {"sent": sum(1 for _, sent, _ in mine if sent),
                                     "failed": sum(1 for _, sent, ok in mine if sent and not ok),
                                     "not_sent": sum(1 for _, sent, _ in mine if not sent),
                                     "of_replies": len(members) * R}

    judgment = ([FIXTURE_MARK] if allow_fixture else []) + [
                "Judgment sentences, copied exactly as the sorters wrote them.",
                "Question asked: what remains judgment once this lesson has its home?",
                "These are not scored, counted or classified anywhere in the code. A person reads them.", ""]
    for n in line_numbers:
        judgment.append("Line %d: %s" % (n, line_text[n]))
        for s, k, sent in sorted(sentences[n], key=lambda x: (sorters.index(x[0]), x[1])):
            judgment.append("  [%s] %s repeat %d: %s" % (group_of[s], s, k, sent))
        judgment.append("")

    callers = sorted({load_json(os.path.join(run_dir, p), p).get("caller") for p in expected})
    report = {"status": FIXTURE_MARK} if allow_fixture else {}
    report.update({
        "dry_run": False,
        "inputs": {"run_dir": os.path.abspath(run_dir), "manifest_sha256": sha256_file(man_path),
                   "key_sha256": listed["key.json"], "callers": callers,
                   "real_callers": real, "allow_fixture": allow_fixture,
                   "house_table": cfg.get("house_table"),
                   "house_table_sha256": sha256_file(cfg["house_table"]) if cfg.get("house_table") else None},
        "settings": {"sorters": cfg["sorters"], "groups": cfg["groups"], "repeats": R, "cut_points_by_size": cfg["cut_points_by_size"],
                     "bootstrap": cfg["bootstrap"],
                     "majority_rule": "more than half of the expected repeats; failed repeats count in the denominator",
                     "figures_use": "main home only; second homes are reported beside and change no figure",
                     "agreement_values": "each sorter's majority main home per line; no majority = missing",
                     "groups_note": "computed separately and never pooled"},
        "parse_failures_listed": failures,
        "parse_failures_note": "listed only, never counted across groups; each group carries its own count",
        "groups": group_reports,
        "limit_endings_by_sorter": [limit_endings[s] for s in sorters],
        "limit_endings_note": LIMIT_ENDINGS_NOTE,
    })
    return report, "\n".join(judgment) + "\n"


def group_report(cfg, g, members, line_numbers, R, v_main, v_second, maj_main, maj_second, failures, homes_set,
                 table):
    size = len(members)
    cp = cfg["cut_points_by_size"].get(str(size))
    per_line = []
    for n in line_numbers:
        c = Counter(maj_main[s][n] for s in members if maj_main[s][n] is not None)
        mc = max(c.values()) if c else 0
        modal = sorted(h for h, x in c.items() if x == mc) if c else []
        if cp is None:
            cls = None
        else:
            cls = "settled" if mc >= cp["settled_min"] else "leaning" if mc >= cp["leaning_min"] else "contested"
        per_line.append({"line_number": n, "sorter_majority": {s: maj_main[s][n] for s in members},
                         "modal_homes": modal, "modal_count": mc, "count_text": "%d of %d" % (mc, size),
                         "class": cls})

    per_sorter = {}
    for s in members:
        not_same = sum(1 for n in line_numbers if len(v_main[s][n]) < R or len(set(v_main[s][n])) > 1)
        no_maj = sum(1 for n in line_numbers if maj_main[s][n] is None)
        per_sorter[s] = {
            "repeats_failed": sum(1 for f in failures if f["sorter"] == s),
            "lines_not_all_same": not_same, "share_lines_not_all_same": not_same / len(line_numbers),
            "lines_no_majority": no_maj, "share_lines_no_majority": no_maj / len(line_numbers),
        }

    agreement = {}
    if size > 2:
        units = [[maj_main[s][n] for s in members] for n in line_numbers]
        b = cfg["bootstrap"]
        for name, fn in (("fleiss_kappa", fleiss_kappa), ("krippendorff_alpha", krippendorff_alpha_nominal)):
            v = fn(units)
            entry = {"value": v}
            if v is None:
                if name == "fleiss_kappa" and any(x is None for u in units for x in u):
                    entry["reason"] = "not computed: at least one sorter has no majority home on at least one line"
                else:
                    entry["reason"] = "undefined on these data (fewer than two homes used, or nothing pairable)"
            else:
                entry["bootstrap"] = bootstrap(units, fn, b["seed"], b["draws"], b["level"])
            agreement[name] = entry

    second = []
    for n in line_numbers:
        bym = Counter(maj_second[s][n] for s in members if maj_second[s][n] is not None)
        raw = Counter(h for s in members for h in v_second[s][n] if h is not None)
        second.append({"line_number": n,
                       "by_majority": {"sorters_with_second": sum(bym.values()), "of": size,
                                       "homes": dict(sorted(bym.items()))},
                       "raw": {"replies_with_second": sum(raw.values()),
                               "of_replies": sum(len(v_second[s][n]) for s in members),
                               "homes": dict(sorted(raw.items()))}})

    house = {"not_given": True}
    if table is not None:
        excluded = []
        for n in line_numbers:
            r = table[n]
            if r["home_main"] not in homes_set or (r["home_second"] is not None and r["home_second"] not in homes_set):
                excluded.append({"line_number": n, "home_main": r["home_main"], "home_second": r["home_second"],
                                 "reason": "a home not on the list"})
        skip = {e["line_number"] for e in excluded}
        compared = [n for n in line_numbers if n not in skip]
        ps, pl = {}, []
        for s in members:
            ex = ov = 0
            for n in compared:
                r = table[n]
                want = {r["home_main"]} | ({r["home_second"]} if r["home_second"] else set())
                m = maj_main[s][n]
                if m is None:
                    continue
                got = {m} | ({maj_second[s][n]} if maj_second[s][n] else set())
                ex += 1 if (m == r["home_main"] and got == want) else 0
                ov += 1 if got & want else 0
            ps[s] = {"exact": ex, "overlap": ov, "of": len(compared)}
        house = {"excluded_lines": excluded, "per_sorter": ps,
                 "group": {"exact": sum(x["exact"] for x in ps.values()),
                           "overlap": sum(x["overlap"] for x in ps.values()),
                           "of": len(compared) * size},
                 "note": "exploratory; every exact match is also an overlap match; the two counts are never added"}

    report = {"sorters": members, "size": size, "cut_points": cp,
              "parse_failures": {"count": sum(1 for f in failures if f["group"] == g), "of_replies": size * R},
              "per_line": per_line,
              "class_counts": dict(Counter(x["class"] for x in per_line)) if cp else None,
              "per_sorter": per_sorter, "agreement": agreement, "second_homes": second, "house_table": house}
    if size == 1:
        report["agreement_note"] = ("Single-sorter group: descriptive counts only; "
                                    "classes and agreement statistics are not computed.")
    elif size == 2:
        report["agreement_note"] = "Agreement statistics are not computed for a group of two, by rule."
    return report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--allow-fixture", action="store_true",
                    help="tally a run whose callers are not on real_callers; every output says FIXTURE, NOT DATA")
    a = ap.parse_args(argv)
    try:
        cfg = load_json(a.config, "tally config")
        report, judgment = compute(cfg, need_out=True, allow_fixture=a.allow_fixture)
    except Refuse as e:
        print("REFUSED: %s" % e)
        return 2
    if a.allow_fixture:
        print("%s: tallied with --allow-fixture; nothing below is data" % FIXTURE_MARK)
    report["written_at"] = clock()
    out = cfg["out_dir"]
    os.makedirs(out, exist_ok=True)
    write_json(os.path.join(out, "tally.json"), report)
    with open(os.path.join(out, "judgment_sentences.txt"), "w", encoding="utf-8") as fh:
        fh.write(judgment)
    print("callers: %s" % ", ".join(report["inputs"]["callers"]))
    for g, gr in report["groups"].items():
        print("group %s (%d sorters; cut points %s)" % (g, gr["size"], gr["cut_points"]))
        print("  parse failures: %d of %d replies" % (gr["parse_failures"]["count"], gr["parse_failures"]["of_replies"]))
        print("  turn 2 (the question): failed %d of %d sent; not sent %d"
              % (gr["turn2"]["failed"], gr["turn2"]["sent"], gr["turn2"]["not_sent"]))
        for x, sec in zip(gr["per_line"], gr["second_homes"]):
            print("  line %2d: %-9s modal %s, %s; second homes by majority %d of %d, raw %d of %d"
                  % (x["line_number"], x["class"] or "-", "/".join(x["modal_homes"]) or "-", x["count_text"],
                     sec["by_majority"]["sorters_with_second"], sec["by_majority"]["of"],
                     sec["raw"]["replies_with_second"], sec["raw"]["of_replies"]))
        if gr.get("agreement_note"):
            print("  %s" % gr["agreement_note"])
        for name, e in gr["agreement"].items():
            bs = e.get("bootstrap") or {}
            print("  %s: %s interval %s (undefined draws %s)" % (name, e["value"], bs.get("interval"),
                                                                bs.get("draws_undefined")))
        h = gr["house_table"]
        if h.get("not_given"):
            print("  house table: not given")
        else:
            print("  house table: exact %d of %d, overlap %d of %d (separate counts); left out: %s"
                  % (h["group"]["exact"], h["group"]["of"], h["group"]["overlap"], h["group"]["of"],
                     [e["line_number"] for e in h["excluded_lines"]]))
    print("Provider-reported limit endings by sorter")
    print("  sorter | message 1 | message 2 | sorts not sent after F")
    for row in report.get("limit_endings_by_sorter", []):
        print("  %s | %d | %d | %d" % (row["sorter"], row["message_1"], row["message_2"], row["sorts_not_sent_after_f"]))
    if not any(row["message_1"] or row["message_2"] for row in report.get("limit_endings_by_sorter", [])):
        print("  No provider-reported limit endings were recorded.")
    if report.get("limit_endings_note"):
        print("  %s" % report["limit_endings_note"])
    print("wrote %s and %s" % (os.path.join(out, "tally.json"), os.path.join(out, "judgment_sentences.txt")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
