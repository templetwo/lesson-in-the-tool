"""Runner: for a config of sorters and repeats, build each prompt, hold the two-turn conversation, parse, and write
the files.

Usage: /usr/bin/python3 -B runner.py --config CONFIG.json            a run
       /usr/bin/python3 -B runner.py --config CONFIG.json --smoke    one line to each configured sorter (real only)

Writes, inside out_dir (which must sit inside this folder and be new or empty):
  key.json                     private: the lines, their source and hashes, seeds, and every label-to-line map
  prompts/<sorter>__r<k>.json  the exact first message sent ("text") and the second message ("question_text")
  results/<sorter>__r<k>.json  turn 1's raw reply, parse result and rows; "turn2" with its own; "calls"
  manifest.json                written last: the sha256 of every file above
Every file in a dry run has "dry_run": true as its first key and on every row.

Version 2 (2026-11-25, after PICKS_20261125.md): each sorter in the config is {"name": ..., "group": ...}; the group
is written into every result file and into the key. Groups do not change the prompt.

Fix round (2026-11-25): each sorter is {"name": ..., "group": ..., "provider": ...}; required keys "groups" (may be
{}; {"cloud": {"min_providers": 3}}) and "prompt_text" (the wording file, its sha256 recorded in the key). Refused
before anything is written: a group spanning fewer providers than its min_providers (B), sorter names or group
spellings equal after case folding, and planned output paths equal after case folding (G).

Two-turn and callers build (2026-11-25, picks 9 to 12):
  * Two turns of ONE conversation per (sorter, repeat). Turn 1 sends the first message and asks only for homes. If
    its reply parses, turn 2 sends [first message, turn 1's reply text exactly as returned, second message] and asks
    the question. If turn 1 does not parse, turn 2 is not sent, and the result's "turn2" says so. If turn 2 does not
    parse, the sort stands and the sentences are missing. Both raw replies are always kept.
  * "caller" is "dryrun" or "by_sorter". With "by_sorter" the run must not be dry, and "real_callers" maps every
    sorter to one adapter named in real_callers.ADAPTERS whose provider equals the sorter's. Each result records its
    own adapter as "caller"; the manifest records "caller": "by_sorter" and "callers" (the adapters, sorted).
  * A by_sorter run checks the SORT_REAL_CALLS switch right after the config check, before reading the lines or
    writing anything; every adapter checks it again before reading a key, and the transport before connecting.
  * Optional key "status": text kept in the key (the draft config says DRAFT there).
  * Optional Boolean "require_model_match" defaults to true, is passed to each real caller, and is kept in the key.
  * Optional "output_token_limit": integer 1 through 60000, default 19000. Used for main requests, usage stops and
    the call-budget receipts; smoke always uses 2000. A requested token bound is not a whole-bill dollar ceiling.
  * Returned answers are checkpointed before parsing or asking the next turn. Incomplete results have an explicit
    persistence_state and no completed-run manifest. There is no resume path. Atomic replacement preserves the
    previous checkpoint if a later checkpoint cannot be written or replaced.
  * Relative paths in a config resolve against the directory the runner is started from (run it from test1_sort/).
"""
import argparse
import copy
import json
import os
import random
import re
import sys

from common import Refuse, inside_here, load_json, write_json, sha256_file, clock
from lines_loader import load_lines
from homes import load_homes
from prompt_builder import build_prompt, load_deny_list, load_prompt_text
from reply_parser import parse_sort_reply, parse_question_reply
from callers import (get_caller, Conversation, Reply, TOP_LEVEL, OUTPUT_TOKEN_LIMIT,
                     validate_output_token_limit)

REQUIRED = ["dry_run", "caller", "repo", "commit", "lines_path", "homes_file", "deny_list", "prompt_text", "sorters",
            "groups", "repeats", "master_seed", "out_dir"]
OPTIONAL = ["real_callers", "status", "require_model_match", "output_token_limit"]
SORTER = re.compile(r"^[A-Za-z0-9-]+(?:_[A-Za-z0-9-]+)*$")
NOT_SENT_REASON = "turn 1 did not parse, so the question was not asked"
USAGE_STOP_REASON = "sorter_output_limit_exceeded"
USAGE_STOP_ERROR = "sorter stopped after reported output usage exceeded the effective call limit"


def turn2_not_sent(dry):
    """The turn2 record of a result whose sort did not parse. The tally requires exactly this form."""
    return {"dry_run": dry, "sent": False, "not_sent_reason": NOT_SENT_REASON, "raw_reply": None, "parse_ok": False,
            "parse_errors": [], "rows": []}


def turn2_usage_stopped(dry):
    return {"dry_run": dry, "sent": False, "not_sent_reason": USAGE_STOP_REASON, "raw_reply": None,
            "parse_ok": False, "parse_errors": [], "rows": []}


def output_usage_check(caller, record):
    """Read one provider's reported aggregate. Never add reasoning-detail subsets.

    This after-the-response stop cannot prevent an overrun. Missing or malformed usage is unavailable,
    not zero, and no detection is promised for output the maker does not report in the expected field.
    """
    fields = {"anthropic": "output_tokens", "openai": "output_tokens", "xai": "output_tokens",
              "deepseek": "completion_tokens", "ollama": "eval_count"}
    field = fields.get(getattr(caller, "kind", None))
    limit = getattr(caller, "output_token_limit", None)
    check = {"status": "unavailable", "field": field, "reported_output_tokens": None, "limit": limit}
    if field is None or type(limit) is not int or limit < 1:
        return dict(check, reason="unsupported_usage_contract")
    raw = record.get("usage_json")
    if not isinstance(raw, str):
        return dict(check, reason="missing_or_nontext_usage")
    try:
        usage = json.loads(raw)
    except (ValueError, TypeError):
        return dict(check, reason="malformed_usage_json")
    if not isinstance(usage, dict) or field not in usage:
        return dict(check, reason="missing_output_count")
    count = usage[field]
    if type(count) is not int or count < 0:
        return dict(check, reason="invalid_output_count")
    return {"status": "exceeded" if count > limit else "within_limit", "field": field,
            "reported_output_tokens": count, "limit": limit}


def check_providers(sorters, groups):
    """Fix B ("6 from 3"). Every sorter names its provider. `groups` is required and may be {}: no defaults, so a
    missing setting cannot quietly switch the check off. Each entry names a group some sorter has and gives exactly
    {"min_providers": n}; the group must span at least n providers, counted without case. Shared with tally.py.
    It does not check balance: four sorters from one provider and one each from two others pass min 3."""
    for e in sorters:
        p = e.get("provider")
        if not isinstance(p, str) or not p.strip() or p != p.strip() or "\n" in p or "\r" in p:
            raise Refuse("sorter %r provider %r must be non-empty text without surrounding spaces or line breaks"
                         % (e.get("name"), p))
    if not isinstance(groups, dict):
        raise Refuse("groups must be an object keyed by group name, for example {\"cloud\": {\"min_providers\": 3}}")
    present = {e["group"] for e in sorters}
    for g, spec in sorted(groups.items()):
        if g not in present:
            raise Refuse("groups names %r, which no sorter has (a misspelt group would switch its check off)" % g)
        if not isinstance(spec, dict) or set(spec) != {"min_providers"} or not isinstance(spec["min_providers"], int) \
                or isinstance(spec["min_providers"], bool) or spec["min_providers"] < 1:
            raise Refuse("groups entry %r must be exactly {\"min_providers\": a whole number of at least 1}" % g)
        provs = sorted({e["provider"].casefold() for e in sorters if e["group"] == g})
        if len(provs) < spec["min_providers"]:
            raise Refuse("group %r spans %d provider(s) %s (counted without case); min_providers is %d"
                         % (g, len(provs), provs, spec["min_providers"]))


def check_real_callers(cfg, output_token_limit=None):
    """With caller "by_sorter": real_callers maps every sorter, and only the sorters, to an adapter that exists, is
    not the dry caller, and has the sorter's provider. Returns {sorter: adapter}. Constructs adapters only: no key is
    read and no connection is opened."""
    main_limit = validate_output_token_limit(cfg.get("output_token_limit", OUTPUT_TOKEN_LIMIT))
    if output_token_limit is None:
        output_token_limit = main_limit
    else:
        validate_output_token_limit(output_token_limit)
    model_match = cfg.get("require_model_match", True)
    if type(model_match) is not bool:
        raise Refuse("require_model_match must be a Boolean")
    rc = cfg.get("real_callers")
    names = [e["name"] for e in cfg["sorters"]]
    if not isinstance(rc, dict) or not all(isinstance(v, str) for v in rc.values()):
        raise Refuse("a by_sorter run needs real_callers: an object mapping each sorter name to an adapter name")
    if sorted(rc) != sorted(names):
        raise Refuse("real_callers must name every sorter and only the sorters: missing %s, extra %s"
                     % (sorted(set(names) - set(rc)), sorted(set(rc) - set(names))))
    out = {}
    for e in cfg["sorters"]:
        if rc[e["name"]] == "dryrun":
            raise Refuse("no caller named 'dryrun' may be mapped in a by_sorter run")
        c = get_caller(rc[e["name"]], require_model_match=model_match, output_token_limit=output_token_limit)
        if c.is_dry:
            raise Refuse("no caller named %r may be mapped in a by_sorter run (it is a dry caller)" % c.name)
        if c.provider.casefold() != e["provider"].casefold():
            raise Refuse("sorter %r has provider %r but its adapter %r is provider %r"
                         % (e["name"], e["provider"], c.name, c.provider))
        out[e["name"]] = c
    return out


def check_config(cfg):
    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        raise Refuse("config is missing %s" % missing)
    extra = [k for k in cfg if k not in REQUIRED and k not in OPTIONAL]
    if extra:
        raise Refuse("config has keys this runner does not know: %s" % extra)
    validate_output_token_limit(cfg.get("output_token_limit", OUTPUT_TOKEN_LIMIT))
    if not isinstance(cfg["dry_run"], bool):
        raise Refuse("dry_run must be true or false")
    if type(cfg.get("require_model_match", True)) is not bool:
        raise Refuse("require_model_match must be a Boolean")
    if "status" in cfg and (not isinstance(cfg["status"], str) or not cfg["status"].strip()):
        raise Refuse("status, when given, must be text")
    if cfg["caller"] not in TOP_LEVEL:
        raise Refuse("caller must be one of %s; a real run names each sorter's adapter in real_callers"
                     % (list(TOP_LEVEL),))
    s = cfg["sorters"]
    if not isinstance(s, list) or not s:
        raise Refuse("sorters must be a non-empty list of {\"name\": ..., \"group\": ..., \"provider\": ...}")
    for entry in s:
        if not isinstance(entry, dict) or set(entry) != {"name", "group", "provider"}:
            raise Refuse("each sorter must be exactly {\"name\": ..., \"group\": ..., \"provider\": ...}; got %r"
                         % (entry,))
        for field in ("name", "group"):
            v = entry[field]
            if not isinstance(v, str) or not SORTER.match(v) or "__" in v:
                raise Refuse("sorter %s %r must be letters, digits, '-' or single '_'" % (field, v))
    check_providers(s, cfg["groups"])
    names = [e["name"] for e in s]
    if len(set(names)) != len(names):
        raise Refuse("a sorter name is repeated")
    # Fix G: this Mac's volume ignores case in file names, so S1 and s1 would write one file.
    folded = [n.casefold() for n in names]
    twins = sorted(n for n in names if folded.count(n.casefold()) > 1)
    if twins:
        raise Refuse("sorter names %s are equal after case folding; on this volume they would overwrite each "
                     "other's files" % twins)
    spellings = sorted(set(e["group"] for e in s))
    gtwins = sorted(g for g in spellings if [x.casefold() for x in spellings].count(g.casefold()) > 1)
    if gtwins:
        raise Refuse("group names %s are equal after case folding" % gtwins)
    if cfg["caller"] == "dryrun":
        if "real_callers" in cfg:
            raise Refuse("real_callers belongs to a by_sorter run, not a dry run")
        caller = get_caller("dryrun")
        if not cfg["dry_run"]:
            raise Refuse("caller %r is a dry-run caller but the run is not marked dry_run: true" % caller.name)
        callers = {n: caller for n in names}
    else:
        if cfg["dry_run"]:
            raise Refuse("run is marked dry but its caller is by_sorter (real adapters)")
        callers = check_real_callers(cfg)
    if not isinstance(cfg["repeats"], int) or isinstance(cfg["repeats"], bool) or cfg["repeats"] < 1:
        raise Refuse("repeats must be a whole number of at least 1")
    if not isinstance(cfg["master_seed"], int) or isinstance(cfg["master_seed"], bool):
        raise Refuse("master_seed must be a whole number")
    out = cfg["out_dir"]
    if not inside_here(out):
        raise Refuse("out_dir %s is outside this folder; this build writes only inside its own folder" % out)
    if os.path.exists(out) and (not os.path.isdir(out) or os.listdir(out)):
        raise Refuse("out_dir %s exists and is not an empty folder" % out)
    return callers


class CallBudget:
    """One sequential run's attempt limits, derived before its first caller is invoked.

    Counts are conservative reservations, not billing confirmations. A failed delegate is never refunded.
    Per-sorter and per-adapter limits prevent unused allowance on one model funding another model's calls.
    The ledger is process-local: returned-answer checkpoints persist snapshots, not an in-flight billing journal.
    """
    def __init__(self, cfg, callers, smoke=False):
        from callers import SMOKE_OUTPUT_TOKEN_LIMIT
        self._mode = "smoke" if smoke else "main"
        main_limit = validate_output_token_limit(cfg.get("output_token_limit", OUTPUT_TOKEN_LIMIT))
        limit = SMOKE_OUTPUT_TOKEN_LIMIT if smoke else main_limit
        repeats = 1 if smoke else cfg.get("repeats")
        if type(repeats) is not int or repeats < 1:
            raise Refuse("call budget requires a positive repeat count")
        count = repeats if smoke else 2 * repeats
        sorters = cfg.get("sorters")
        if not isinstance(sorters, list) or not sorters or not all(isinstance(entry, dict) for entry in sorters):
            raise Refuse("call budget requires configured sorters")
        names = [entry.get("name") for entry in sorters]
        if not all(isinstance(name, str) and name for name in names) or len(set(names)) != len(names):
            raise Refuse("call budget requires unique sorter names")
        if set(names) != set(callers):
            raise Refuse("call budget callers differ from configured sorters")
        self._planned = dict.fromkeys(("total", "external", "anthropic", "other_external", "local", "dry_fixture"), 0)
        self._attempted = dict(self._planned)
        self._per_sorter, self._per_adapter = {}, {}
        real = False
        for name in names:
            caller = callers[name]
            if caller.is_dry:
                category = "dry_fixture"
            else:
                real = True
                kind = getattr(caller, "kind", None)
                if kind not in ("anthropic", "openai", "xai", "deepseek", "ollama"):
                    raise Refuse("call budget cannot classify adapter %r" % caller.name)
                category = "local" if kind == "ollama" else "anthropic" if kind == "anthropic" else "other_external"
                if getattr(caller, "output_token_limit", None) != limit:
                    raise Refuse("call budget adapter output limit differs from the selected run limit")
            spec = {"caller": caller.name, "category": category, "planned": count, "attempted": 0, "stop": None}
            self._per_sorter[name] = spec
            if caller.name not in self._per_adapter:
                self._per_adapter[caller.name] = {"category": category, "planned": 0, "attempted": 0}
            aggregate = self._per_adapter[caller.name]
            if aggregate["category"] != category:
                raise Refuse("call budget adapter has inconsistent categories")
            aggregate["planned"] += count
            for bucket in self._buckets(category):
                self._planned[bucket] += count
        self._output_token_limit = limit if real else None

    @staticmethod
    def _buckets(category):
        return ("total", "external", category) if category in ("anthropic", "other_external") else ("total", category)

    def reserve(self, sorter):
        spec = self._per_sorter.get(sorter)
        if spec is None:
            raise Refuse("call budget has no configured sorter %r" % sorter)
        aggregate = self._per_adapter[spec["caller"]]
        buckets = self._buckets(spec["category"])
        if spec["attempted"] >= spec["planned"] or aggregate["attempted"] >= aggregate["planned"] \
                or any(self._attempted[bucket] >= self._planned[bucket] for bucket in buckets):
            raise Refuse("call budget exhausted for sorter %r and adapter %r" % (sorter, spec["caller"]))
        spec["attempted"] += 1
        aggregate["attempted"] += 1
        for bucket in buckets:
            self._attempted[bucket] += 1

    def receipt(self):
        return copy.deepcopy({"mode": self._mode, "output_token_limit": self._output_token_limit,
                              "planned": self._planned, "attempted": self._attempted,
                              "per_sorter": self._per_sorter, "per_adapter": self._per_adapter})

    def stop_for(self, sorter):
        return copy.deepcopy(self._per_sorter[sorter]["stop"])

    def record_usage(self, sorter, check):
        if check["status"] == "exceeded" and self._per_sorter[sorter]["stop"] is None:
            self._per_sorter[sorter]["stop"] = {"reason": USAGE_STOP_REASON, "usage_limit_check": copy.deepcopy(check)}


class BudgetedCaller:
    def __init__(self, caller, budget, sorter):
        self._caller, self._budget, self._sorter = caller, budget, sorter

    def __getattr__(self, name):
        return getattr(self._caller, name)

    def call(self, conversation, env=None):
        if self._budget.stop_for(self._sorter) is not None:
            return Reply(None, {"caller": self._caller.name, "turn": conversation.turn(), "sent": False,
                                "complete": False, "error": USAGE_STOP_ERROR, "failure_reason": USAGE_STOP_REASON,
                                "not_sent_reason": USAGE_STOP_REASON})
        self._budget.reserve(self._sorter)
        reply = self._caller.call(conversation, env=env)
        check = output_usage_check(self._caller, reply.record)
        self._budget.record_usage(self._sorter, check)
        record = copy.deepcopy(reply.record)
        record["usage_limit_check"] = check
        return Reply(reply.text, record)


def budget_callers(cfg, callers, smoke=False):
    budget = CallBudget(cfg, callers, smoke=smoke)
    return {name: BudgetedCaller(caller, budget, name) for name, caller in callers.items()}, budget


def check_planned_paths(paths):
    """Fix G: refuse two planned output paths that are equal after case folding. With the sorter name pattern
    (ASCII letters, digits, '-', single '_') and the name check above, no config reaches this today; it is the
    last guard before anything is written, and it is tested directly."""
    folded = {}
    for p in paths:
        folded.setdefault(p.casefold(), []).append(p)
    twins = sorted(v for v in folded.values() if len(v) > 1)
    if twins:
        raise Refuse("planned output paths are equal after case folding: %s" % twins)


def _flagged(dry, d):
    return dict([("dry_run", dry)] + [(k, v) for k, v in d.items() if k != "dry_run"])


def _checkpoint_result(path, result):
    """Flush a new result beside its destination, then atomically replace it.

    A failed write leaves the previous result intact and may leave a .checkpoint
    file for inspection. The nonempty run cannot be resumed or reused.
    """
    encoded = json.dumps(result, indent=1, ensure_ascii=False, allow_nan=False) + "\n"
    pending = path + ".checkpoint"
    with open(pending, "x", encoding="utf-8") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)


def _turn2_pending(dry):
    # Neither a confirmed send nor an ordinary not-sent result is claimed here.
    return {"dry_run": dry, "sent": None, "not_sent_reason": "incomplete checkpoint; turn 2 has not returned",
            "raw_reply": None, "parse_ok": None, "parse_errors": [], "rows": []}


def run(cfg, env=None):
    """env: the environment the switch is read from; None means os.environ. Tests pass a plain dict."""
    callers = check_config(cfg)
    dry = cfg["dry_run"]
    if cfg["caller"] == "by_sorter":
        from real_callers import require_switch
        require_switch(env)
    callers, budget = budget_callers(cfg, callers)
    src = load_lines(cfg["repo"], cfg["commit"], cfg["lines_path"])
    homes, homes_sha = load_homes(cfg["homes_file"])
    deny = load_deny_list(cfg["deny_list"])
    ptext = load_prompt_text(cfg["prompt_text"])
    home_names = [h["name"] for h in homes]
    leak = [cfg["repo"], src["repo"], cfg["commit"], src["commit"], src["commit"][:7], cfg["lines_path"],
            os.path.basename(cfg["lines_path"]), cfg["homes_file"], os.path.basename(cfg["homes_file"])]

    provider_of = {e["name"]: e["provider"] for e in cfg["sorters"]}
    rng = random.Random(cfg["master_seed"])
    plan = []
    for entry in cfg["sorters"]:
        for k in range(1, cfg["repeats"] + 1):
            plan.append((entry["name"], entry["group"], k, rng.getrandbits(32), rng.getrandbits(32)))

    out = cfg["out_dir"]
    check_planned_paths([os.path.join(d, "%s__r%d.json" % (name, k)) for name, _, k, _, _ in plan
                         for d in ("prompts", "results")] + ["key.json", "manifest.json"])
    os.makedirs(os.path.join(out, "prompts"), exist_ok=True)
    os.makedirs(os.path.join(out, "results"), exist_ok=True)
    key_prompts, written = [], []
    for sorter, group, k, line_seed, home_seed in plan:
        caller = callers[sorter]
        prompt = build_prompt(src["lines"], homes, line_seed, home_seed, deny, leak_strings=leak, prompt_text=ptext)
        stem = "%s__r%d.json" % (sorter, k)
        ppath = os.path.join("prompts", stem)
        write_json(os.path.join(out, ppath), {"dry_run": dry, "sorter": sorter, "repeat": k,
                                              "prompt_sha256": prompt.sha256, "text": prompt.text,
                                              "question_sha256": prompt.question_sha256,
                                              "question_text": prompt.question_text})
        conv = Conversation([{"role": "user", "content": prompt.text}], prompt.labels)
        r1 = caller.call(conv, env=env)
        calls = [_flagged(dry, r1.record)]
        rpath = os.path.join("results", stem)
        result_path = os.path.join(out, rpath)
        result = {
            "dry_run": dry, "sorter": sorter, "group": group, "provider": provider_of[sorter], "repeat": k,
            "caller": caller.name,
            "line_seed": line_seed, "home_seed": home_seed,
            "lines_commit": src["commit"], "lines_sha256": src["sha256"], "homes_sha256": homes_sha,
            "prompt_file": ppath, "prompt_sha256": prompt.sha256, "question_sha256": prompt.question_sha256,
            "raw_reply": r1.text, "parse_ok": None, "parse_errors": [], "rows": [],
            "turn2": _turn2_pending(dry), "calls": calls, "persistence_state": "turn1_returned",
            "call_budget": budget.receipt(),
        }
        _checkpoint_result(result_path, result)
        p1 = parse_sort_reply(r1.text, prompt.labels, home_names, dry_run=dry)
        result.update(raw_reply=p1["raw"], parse_ok=p1["ok"], parse_errors=p1["errors"],
                      rows=[_flagged(dry, r) for r in p1["rows"]])
        if p1["ok"]:
            result["persistence_state"] = "turn2_pending"
            _checkpoint_result(result_path, result)
            conv.messages += [{"role": "assistant", "content": r1.text},
                              {"role": "user", "content": prompt.question_text}]
            r2 = caller.call(conv, env=env)
            result["call_budget"] = budget.receipt()
            calls.append(_flagged(dry, r2.record))
            if r2.record.get("sent") is False and r2.record.get("failure_reason") == USAGE_STOP_REASON:
                turn2 = turn2_usage_stopped(dry)
                result["turn2"] = turn2
                result["persistence_state"] = "turn2_not_sent"
                _checkpoint_result(result_path, result)
            else:
                result["turn2"] = {"dry_run": dry, "sent": True, "not_sent_reason": None, "raw_reply": r2.text,
                                   "parse_ok": None, "parse_errors": [], "rows": []}
                result["persistence_state"] = "turn2_returned"
                _checkpoint_result(result_path, result)
                p2 = parse_question_reply(r2.text, prompt.labels)
                turn2 = {"dry_run": dry, "sent": True, "not_sent_reason": None, "raw_reply": p2["raw"],
                         "parse_ok": p2["ok"], "parse_errors": p2["errors"],
                         "rows": [_flagged(dry, r) for r in p2["rows"]]}
        else:
            turn2 = turn2_not_sent(dry)
        result.update(turn2=turn2, persistence_state="complete")
        _checkpoint_result(result_path, result)
        key_prompts.append({"dry_run": dry, "sorter": sorter, "group": group, "repeat": k, "line_seed": line_seed,
                            "home_seed": home_seed, "home_order": prompt.home_order,
                            "labels": [{"dry_run": dry, "label": e["label"], "line_number": e["line_number"]}
                                       for e in prompt.key]})
        written += [ppath, rpath]
    key = {
        "dry_run": dry,
        "lines_source": {k: src[k] for k in ("repo", "commit_requested", "commit", "path", "sha256", "blob_id")},
        "lines": [{"dry_run": dry, "line_number": i + 1, "text": t} for i, t in enumerate(src["lines"])],
        "homes_file": os.path.abspath(cfg["homes_file"]), "homes_sha256": homes_sha,
        "deny_list_sha256": sha256_file(cfg["deny_list"]),
        "prompt_text_file": ptext["path"], "prompt_text_sha256": ptext["sha256"],
        "master_seed": cfg["master_seed"],
        "require_model_match": cfg.get("require_model_match", True),
        "call_budget": budget.receipt(),
        "sorters": [{"dry_run": dry, "name": e["name"], "group": e["group"], "provider": e["provider"]}
                    for e in cfg["sorters"]],
        "groups": cfg["groups"],
        "repeats": cfg["repeats"],
        "prompts": key_prompts,
    }
    if cfg["caller"] == "by_sorter":
        key["real_callers"] = dict(cfg["real_callers"])
    if "status" in cfg:
        key["status"] = cfg["status"]
    write_json(os.path.join(out, "key.json"), key)
    written.append("key.json")
    manifest = {"dry_run": dry, "written_at": clock(), "caller": cfg["caller"], "call_budget": budget.receipt()}
    if cfg["caller"] == "by_sorter":
        manifest["callers"] = sorted(set(cfg["real_callers"].values()))
    manifest["files"] = [{"dry_run": dry, "path": p, "sha256": sha256_file(os.path.join(out, p))} for p in written]
    write_json(os.path.join(out, "manifest.json"), manifest)
    return out


def smoke_reply_status(head, reply):
    """Pure status rendering: even a ready reply fails preflight after a reported output overrun."""
    rec = reply.record
    check = rec.get("usage_limit_check", {})
    if check.get("status") == "exceeded":
        return ("%s: FAILED: %s; reported output %s exceeds limit %s" %
                (head, USAGE_STOP_REASON, check["reported_output_tokens"], check["limit"])), False
    if rec.get("error"):
        return "%s: FAILED: %s" % (head, rec["error"][:300]), False
    if reply.text is None:
        return "%s: FAILED: the reply was not complete (stop %r)" % (head, rec.get("stop")), False
    if reply.text.strip().rstrip(".").casefold() == "ready":
        return ("%s: ok, replied %r; model reported %r; usage %s" %
                (head, reply.text.strip(), rec.get("model_reported"), rec.get("usage_json"))), True
    return ("%s: replied, but not the word ready: %r; model reported %r" %
            (head, reply.text[:120], rec.get("model_reported"))), False


def smoke(cfg, env=None, out=print):
    """Sends each configured sorter the one line "Reply with the single word ready." in a fresh conversation and
    prints one status line per sorter. Writes nothing. Returns 0 only when every sorter replied ready."""
    from real_callers import SMOKE_LINE, require_switch, SMOKE_OUTPUT_TOKEN_LIMIT
    if not isinstance(cfg, dict) or cfg.get("caller") != "by_sorter" or not isinstance(cfg.get("sorters"), list):
        out("REFUSED: --smoke needs a by_sorter config with sorters and real_callers")
        return 2
    try:
        callers = check_real_callers(cfg, output_token_limit=SMOKE_OUTPUT_TOKEN_LIMIT)
        callers, budget = budget_callers(cfg, callers, smoke=True)
    except Refuse as e:
        out("REFUSED: %s" % e)
        return 2
    out("call budget planned: %s" % json.dumps(budget.receipt(), sort_keys=True))
    all_ok = True
    for e in cfg["sorters"]:
        c = callers[e["name"]]
        head = "%s (%s)" % (e["name"], c.name)
        try:
            require_switch(env)
            r = c.call(Conversation([{"role": "user", "content": SMOKE_LINE}], []), env=env)
        except Refuse as err:
            out("%s: REFUSED: %s" % (head, err))
            all_ok = False
            continue
        status, passed = smoke_reply_status(head, r)
        out(status)
        all_ok = all_ok and passed
    out("call budget attempted: %s" % json.dumps(budget.receipt(), sort_keys=True))
    return 0 if all_ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--smoke", action="store_true", help="one line to each configured real sorter; writes nothing")
    a = ap.parse_args(argv)
    if a.smoke:
        try:
            cfg = load_json(a.config, "runner config")
        except Refuse as e:
            print("REFUSED: %s" % e)
            return 2
        return smoke(cfg)
    try:
        cfg = load_json(a.config, "runner config")
        out = run(cfg)
    except Refuse as e:
        print("REFUSED: %s" % e)
        return 2
    man = load_json(os.path.join(out, "manifest.json"), "manifest")
    oks = sent = oks2 = 0
    for row in man["files"]:
        if row["path"].startswith("results/"):
            res = load_json(os.path.join(out, row["path"]), "result")
            oks += 1 if res["parse_ok"] else 0
            sent += 1 if res["turn2"]["sent"] else 0
            oks2 += 1 if res["turn2"]["parse_ok"] else 0
    print("wrote %d files plus manifest.json to %s; dry_run=%s; sorts parsed ok: %d of %d; questions parsed ok: %d "
          "of %d sent" % (len(man["files"]), out, man["dry_run"], oks, len(cfg["sorters"]) * cfg["repeats"], oks2,
                          sent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
