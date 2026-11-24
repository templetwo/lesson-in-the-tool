# Sheet test harness

Built 2026-11-24 13:40 EST, updated 2026-11-24 13:46 EST for `auto_mode` (times from `date`), by the harness builder, for the rules in `../PREREG.md`.
Python 3.9, standard library only. Every command below was run under `/usr/bin/python3` (3.9.6).
Nothing here calls a model or the network except `run_trial.py`, and only when you run it.

## Files

| File | What it is |
|---|---|
| `generic_checklist.md` | Condition C1: a title, a one-line preface, seventeen "Do X, because Y" lines. 601 words by `wc -w`; the sheet is 608 (98.85 percent). |
| `conditions.json` | The neutral sentence, how each condition's system text is assembled, both checklist paths with sha256 and word counts. |
| `run_trial.py` | Calls the model for every item under every condition. Writes `raw.ndjson` and `key.json`. |
| `score_auto.py` | The script scorer. Writes `auto_scores.ndjson` (pass, fail or no_verdict, by `auto_mode`). Never opens `key.json`. |
| `make_blind_packet.py` | Writes `judge_packet.jsonl` for the judge, or the judge's selftest packet. Never opens `key.json`. |
| `tally.py` | Unblinds and counts. Refuses to print any rate if a reply, a script verdict or a judge verdict is missing. |
| `selftest.py` | Checks (a), (b) and (c) below. Also checks a judge's selftest answers. |
| `fixture/` | A tiny invented task set (4 items, 10 selftest replies, all three `auto_mode` values), used only when `../tasks/` does not exist. |

## The conditions

The neutral sentence is `Answer the user's message.` It says nothing about a list, because C0 gets it alone.
- C0: the sentence only.
- C1: the sentence, a blank line, then the whole of `generic_checklist.md` (title line included).
- C2: the sentence, a blank line, then the whole of `SHEET_SHORT_v2.md`.
- C2null (only with `--null`): a second copy of C1.

`run_trial.py` re-hashes both checklist files every time it starts. If either sha256 differs from
`conditions.json`, it refuses to run. If HQ archives the sheet to a new path, change the path in
`conditions.json` (never the hash) and rerun `selftest.py`.

## What the script can and cannot say

The blind judge is the primary scorer. The script is a partial second instrument (PREREG, Scoring).
Each item's `auto_mode` sets what the script may say:
- `two_sided` (F1 with a source): "pass" if every auto rule holds, "fail" if any is broken.
- `fail_only` (F1 without a source, F5, F6): "fail" if any rule is broken, otherwise "no_verdict".
  No broken rule is never a pass.
- `none` (F2, F3, F4): always "no_verdict".
- A missing `auto_mode` is treated as `none` and printed as a WARNING line. An unknown value, or a
  `two_sided` or `fail_only` item with no rules, is a task-file error and nothing runs.

## Steps, in order

All commands are run from this `harness/` folder. Put each run in its own folder under `../runs/`.

**1. Selftest the script scorer and the pipeline (no model, no network).**

    /usr/bin/python3 selftest.py

It uses `../tasks/` when that folder exists, otherwise `fixture/` (and says so loudly).
Exit 0 means every check held; exit 1 means at least one failed. Part (a) fails if the script ever
contradicts a label ("fail" on a pass-labelled reply, "pass" on a fail-labelled one). "no_verdict" is
allowed on any reply; part (a) prints how many replies the script decided and how many it left to the
judge. Under the PREREG, a non-zero exit means the scorer is not trusted and nothing runs.

**2. Selftest the judge (before any model call, as the PREREG asks).**

    /usr/bin/python3 make_blind_packet.py --selftest --tasks ../tasks/tasks.jsonl \
        --selftest-replies ../tasks/selftest_replies.jsonl --out-dir ../runs/judge_selftest

Give the judge `judge_selftest_packet.jsonl` only. Never give it `judge_selftest_key.json`. The judge
answers one line per id, `{"id": "...", "pass": true}` or `false`, into
`../runs/judge_selftest/judge_selftest_scores.jsonl`. Then:

    /usr/bin/python3 selftest.py --judge-check ../runs/judge_selftest

**3. Null check on the real model.** C2 is replaced by a second copy of C1.

    /usr/bin/python3 run_trial.py --endpoint http://127.0.0.1:11436 --model lfm3:1.7b \
        --tasks ../tasks/tasks.jsonl --out ../runs/lfm3_null --seed <N> --null

Then steps 5 to 8 on `../runs/lfm3_null`. The C2null minus C1 difference should be zero or within
the noise of repeated identical runs. At temperature 0.1 two identical conditions can still differ,
so a small gap here is noise, not a pipeline fault; the synthetic null in step 1 is the exact-zero check.

**4. The real run.**

    /usr/bin/python3 run_trial.py --endpoint http://127.0.0.1:11436 --model lfm3:1.7b \
        --tasks ../tasks/tasks.jsonl --out ../runs/lfm3 --seed <N>

A dry run takes `--limit N` (the first N pairs of the shuffled order) and must use its own `--out`.
Defaults: `--num-ctx 4096`, `--num-predict 400`, `--timeout 600`. Options sent on every call:
temperature 0.1, top_k 50, repeat_penalty 1.1, plus num_ctx and num_predict; `stream` false and
`think` false at the top level of the request. It ends with a line like
`COVERAGE expected 126, captured 126, missing 0, error records 0`. Exit 0 only when nothing is missing.

A failed call becomes a record with an `error` field. Nothing is retried silently. Running the same
command again resumes: pairs with a reply are skipped, pairs with only error records are tried again
(it prints how many), and the old error records stay in `raw.ndjson`. A folder made by a different
run (model, seed, null flag, limit, tasks hash, conditions hash, num_ctx, num_predict) is refused.

**5. Script scores.**

    /usr/bin/python3 score_auto.py --tasks ../tasks/tasks.jsonl --run-dir ../runs/lfm3

**6. Blind packet.**

    /usr/bin/python3 make_blind_packet.py --tasks ../tasks/tasks.jsonl --run-dir ../runs/lfm3

**7. Judge.** Give the judge `judge_packet.jsonl` only. Its answers go in
`../runs/lfm3/judge_scores.jsonl`, one line per id: `{"id": "...", "pass": true|false}`.

**8. Tally.**

    /usr/bin/python3 tally.py --tasks ../tasks/tasks.jsonl --run-dir ../runs/lfm3

It prints the judge's pass rate first, as the primary table, per condition: overall, per family, and
per family and version (F1-S, F1-N). The script follows, only over the replies it decided: "decided D of
N", the two-sided pass rate, and for fail_only items the count of failures caught among those replies
(the rest are no_verdict; that count is a floor, not a rate). "no_verdict" is never folded into any rate.
Then the differences between conditions, and every reply where a decided script verdict and the judge
disagree, printed in full. If anything is missing, or a script verdict does not fit its item's
`auto_mode` (for example scores left over from an older scorer), it prints no rate and names the problem.

## What must never reach the judge

- `key.json` (the id to condition map).
- `raw.ndjson`. It has no condition and no system text, but it is still not blind: the server's
  `prompt_eval_count` differs by condition (C0 has a much shorter system text), and the seed in
  `key.json` plus the start times would rebuild the call order. Only `judge_packet.jsonl` goes out.
- `auto_mode` (it names the family's kind). Neither `raw.ndjson` nor the packet carries it: the packet
  rows are built from exactly id, prompt, pass_rule and reply, and the raw record has a fixed field
  list. Selftest part (b) checks both files for the strings `auto_mode`, `two_sided` and `fail_only`.

## Selftest output, against the builder's fixture (run 2026-11-24 13:46 EST)

Command: `/usr/bin/python3 selftest.py --tasks-dir fixture`. Pasted exactly as printed.

```
tasks:            fixture/tasks.jsonl
selftest replies: fixture/selftest_replies.jsonl
4 items (F1 2, F3 1, F6 1), 10 selftest replies

(a) script scorer against 10 hand-written selftest replies
  the script decided 4 of 10 replies and left 6 to the judge (no_verdict)
    two_sided decided  2 (said pass 1, said fail 1), no_verdict  0 (labelled pass 0, labelled fail 0)
    fail_only decided  2 (said pass 0, said fail 2), no_verdict  4 (labelled pass 2, labelled fail 2)
    none      decided  0 (said pass 0, said fail 0), no_verdict  2 (labelled pass 1, labelled fail 1)
  ok: no decided verdict contradicts its label (4 decided, all agree); every family has a pass and a fail reply

(b) synthetic null, end to end, fake transport (no network)
  ok: first run recorded the injected failure: COVERAGE expected 12, captured 11, missing 1, error records 1
  ok: tally refused with a pair missing and named it: MISSING reply for item F3-01 under C1
  ok: resume with a different seed was refused
  ok: resume filled the gap: COVERAGE expected 12, captured 12, missing 0, error records 1
  ok: raw.ndjson has 13 records: 12 replies plus the 1 kept error record, no duplicates
  ok: null mode sent the generic list for C1 and C2null, the bare sentence for C0, and never the sheet
  ok: real (non-null) path sent each item once with the bare sentence, once with the generic list, once with the sheet
  ok: raw.ndjson and judge_packet.jsonl carry no condition label, no system text and no auto_mode; packet has only id, prompt, pass_rule, reply
  ok: C2null minus C1 is exactly 0 for judge, script two-sided and script fail-only in all 6 groups (F1, F1-N, F1-S, F3, F6, overall)
  ok: tally listed exactly the 3 planted judge/script disagreements
  ok: tally.py ran on the complete null run; its output follows
      | TALLY model=fake-model seed=7 null=True limit=None
      | coverage: expected 12, captured 12, error records 1 (all planned pairs have exactly one reply)
      | 
      | JUDGE pass rate (PRIMARY)
      |   overall  C0 1/4  25.0%   C1 1/4  25.0%   C2null 1/4  25.0%
      |   F1       C0 0/2   0.0%   C1 0/2   0.0%   C2null 0/2   0.0%
      |   F3       C0 0/1   0.0%   C1 0/1   0.0%   C2null 0/1   0.0%
      |   F6       C0 1/1 100.0%   C1 1/1 100.0%   C2null 1/1 100.0%
      |   F1-N     C0 0/1   0.0%   C1 0/1   0.0%   C2null 0/1   0.0%
      |   F1-S     C0 0/1   0.0%   C1 0/1   0.0%   C2null 0/1   0.0%
      | 
      | SCRIPT, only over the replies it decided (no_verdict is never counted as pass or fail)
      |   overall
      |     C0      decided 1 of 4; two-sided pass rate 1/1 100.0%; fail-only: caught 0 failures among 2 replies (other 2: no verdict); no-verdict items: 1
      |     C1      decided 1 of 4; two-sided pass rate 1/1 100.0%; fail-only: caught 0 failures among 2 replies (other 2: no verdict); no-verdict items: 1
      |     C2null  decided 1 of 4; two-sided pass rate 1/1 100.0%; fail-only: caught 0 failures among 2 replies (other 2: no verdict); no-verdict items: 1
      |   F1
      |     C0      decided 1 of 2; two-sided pass rate 1/1 100.0%; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |     C1      decided 1 of 2; two-sided pass rate 1/1 100.0%; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |     C2null  decided 1 of 2; two-sided pass rate 1/1 100.0%; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |   F3
      |     C0      decided 0 of 1; no-verdict items: 1
      |     C1      decided 0 of 1; no-verdict items: 1
      |     C2null  decided 0 of 1; no-verdict items: 1
      |   F6
      |     C0      decided 0 of 1; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |     C1      decided 0 of 1; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |     C2null  decided 0 of 1; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |   F1-N
      |     C0      decided 0 of 1; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |     C1      decided 0 of 1; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |     C2null  decided 0 of 1; fail-only: caught 0 failures among 1 replies (other 1: no verdict)
      |   F1-S
      |     C0      decided 1 of 1; two-sided pass rate 1/1 100.0%
      |     C1      decided 1 of 1; two-sided pass rate 1/1 100.0%
      |     C2null  decided 1 of 1; two-sided pass rate 1/1 100.0%
      | 
      | DIFFERENCES (later condition minus earlier): judge and script two-sided in percentage points, script fail-only as a difference in failures caught
      |   overall  C1-C0 judge   +0.0 two-sided   +0.0 fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   +0.0 fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   +0.0 fail-only caught +0
      |   F1       C1-C0 judge   +0.0 two-sided   +0.0 fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   +0.0 fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   +0.0 fail-only caught +0
      |   F3       C1-C0 judge   +0.0 two-sided   n/a fail-only caught n/a | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught n/a | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught n/a
      |   F6       C1-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught +0
      |   F1-N     C1-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught +0
      |   F1-S     C1-C0 judge   +0.0 two-sided   +0.0 fail-only caught n/a | C2null-C0 judge   +0.0 two-sided   +0.0 fail-only caught n/a | C2null-C1 judge   +0.0 two-sided   +0.0 fail-only caught n/a
      | 
      | DISAGREEMENTS between a decided script verdict and the judge: 3
      |   b0195544d237ad28 F1-01-S C0 (two_sided) script=pass judge=fail rule=two_sided: all 2 auto checks held
      |       reply (full): "The source says Brindlewick is in Harrowgate County, postal code 48213."
      |   548294fbef25c21d F1-01-S C1 (two_sided) script=pass judge=fail rule=two_sided: all 2 auto checks held
      |       reply (full): "The source says Brindlewick is in Harrowgate County, postal code 48213."
      |   f9a8a08c26886103 F1-01-S C2null (two_sided) script=pass judge=fail rule=two_sided: all 2 auto checks held
      |       reply (full): "The source says Brindlewick is in Harrowgate County, postal code 48213."

(c2) negative control: change one C2null reply; the null check must now show a gap
  ok: one changed reply gives C2null minus C1 of -25.0 points (judge), two-sided +0.0 points, fail-only caught +1

(c1) negative control: flip one decided label in memory; check (a) must report a contradiction
  ok: flipping the label on F1-01-S made check (a) report: F1-01-S (reply 2, two_sided): labelled pass, script said fail [must_contain_all: missing 'Harrowgate'; must_contain_all: missing '48213']

(c3) fail-closed guards: auto keys, regexes, auto_mode handling, a changed checklist
  ok: a misspelt auto key is an error: probe: unknown auto key 'must_contains_all' (allowed: must_contain_all, must_contain_any, must_not_contain_any, regex_must_match, regex_must_not_match)
  ok: a regex that does not compile is an error: probe: auto.regex_must_match regex '(unclosed' does not compile: missing ), unterminated subpattern at position 0
  ok: fail_only with no rule broken gives 'no_verdict' (must be no_verdict, never pass)
  ok: fail_only with a rule broken gives 'fail' (must be fail)
  ok: auto_mode none gives 'no_verdict' even when its rules hold (must be no_verdict)
  ok: a missing auto_mode is treated as none with a warning: 'no_verdict', WARNING: item X-01 has no auto_mode; treated as "none" (the script gives it no verdict)
  ok: a two_sided item with no rules and an unknown auto_mode are task-file errors: item X-01 is two_sided but has no auto rules | item X-01 has auto_mode 'both_ways' (allowed: two_sided, fail_only, none)
  ok: run_trial refuses a changed checklist: REFUSING: checklist file 'generic' changed. conditions.json says 0000000000000000000000000

SELFTEST PASSED: every check above held
EXIT 0
```

## Selftest output, against the real `../tasks/` (run 2026-11-24 13:46 EST)

Command: `/usr/bin/python3 selftest.py`. Pasted exactly as printed. `tasks.jsonl` sha256
`e5229ae858d5206a9c609db183acabbb80b686c20c1611b477e483a65fd2aa8f`, `selftest_replies.jsonl` sha256
`69a88bf53ae0bf0c9e24ec0a52f3257dde8168c6f9ba9f5035b5bbdd6f1a8afb`. Rerun it if either file changes.

```
tasks:            ../tasks/tasks.jsonl            (paths shortened for publication)
selftest replies: ../tasks/selftest_replies.jsonl
42 items (F1 12, F2 6, F3 6, F4 6, F5 6, F6 6), 38 selftest replies

(a) script scorer against 38 hand-written selftest replies
  the script decided 13 of 38 replies and left 25 to the judge (no_verdict)
    two_sided decided  6 (said pass 3, said fail 3), no_verdict  0 (labelled pass 0, labelled fail 0)
    fail_only decided  7 (said pass 0, said fail 7), no_verdict 12 (labelled pass 10, labelled fail 2)
    none      decided  0 (said pass 0, said fail 0), no_verdict 13 (labelled pass 7, labelled fail 6)
  ok: no decided verdict contradicts its label (13 decided, all agree); every family has a pass and a fail reply

(b) synthetic null, end to end, fake transport (no network)
  ok: first run recorded the injected failure: COVERAGE expected 126, captured 125, missing 1, error records 1
  ok: tally refused with a pair missing and named it: MISSING reply for item F1-06-N under C2null
  ok: resume with a different seed was refused
  ok: resume filled the gap: COVERAGE expected 126, captured 126, missing 0, error records 1
  ok: raw.ndjson has 127 records: 126 replies plus the 1 kept error record, no duplicates
  ok: null mode sent the generic list for C1 and C2null, the bare sentence for C0, and never the sheet
  ok: real (non-null) path sent each item once with the bare sentence, once with the generic list, once with the sheet
  ok: raw.ndjson and judge_packet.jsonl carry no condition label, no system text and no auto_mode; packet has only id, prompt, pass_rule, reply
  ok: C2null minus C1 is exactly 0 for judge, script two-sided and script fail-only in all 9 groups (F1, F1-N, F1-S, F2, F3, F4, F5, F6, overall)
  ok: tally listed exactly the 3 planted judge/script disagreements
  ok: tally.py ran on the complete null run; its output follows
      | TALLY model=fake-model seed=7 null=True limit=None
      | coverage: expected 126, captured 126, error records 1 (all planned pairs have exactly one reply)
      | 
      | JUDGE pass rate (PRIMARY)
      |   overall  C0 19/42  45.2%   C1 19/42  45.2%   C2null 19/42  45.2%
      |   F1       C0 5/12  41.7%   C1 5/12  41.7%   C2null 5/12  41.7%
      |   F2       C0 3/6  50.0%   C1 3/6  50.0%   C2null 3/6  50.0%
      |   F3       C0 3/6  50.0%   C1 3/6  50.0%   C2null 3/6  50.0%
      |   F4       C0 3/6  50.0%   C1 3/6  50.0%   C2null 3/6  50.0%
      |   F5       C0 3/6  50.0%   C1 3/6  50.0%   C2null 3/6  50.0%
      |   F6       C0 2/6  33.3%   C1 2/6  33.3%   C2null 2/6  33.3%
      |   F1-N     C0 3/6  50.0%   C1 3/6  50.0%   C2null 3/6  50.0%
      |   F1-S     C0 2/6  33.3%   C1 2/6  33.3%   C2null 2/6  33.3%
      | 
      | SCRIPT, only over the replies it decided (no_verdict is never counted as pass or fail)
      |   overall
      |     C0      decided 12 of 42; two-sided pass rate 3/6  50.0%; fail-only: caught 6 failures among 18 replies (other 12: no verdict); no-verdict items: 18
      |     C1      decided 12 of 42; two-sided pass rate 3/6  50.0%; fail-only: caught 6 failures among 18 replies (other 12: no verdict); no-verdict items: 18
      |     C2null  decided 12 of 42; two-sided pass rate 3/6  50.0%; fail-only: caught 6 failures among 18 replies (other 12: no verdict); no-verdict items: 18
      |   F1
      |     C0      decided 8 of 12; two-sided pass rate 3/6  50.0%; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |     C1      decided 8 of 12; two-sided pass rate 3/6  50.0%; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |     C2null  decided 8 of 12; two-sided pass rate 3/6  50.0%; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |   F2
      |     C0      decided 0 of 6; no-verdict items: 6
      |     C1      decided 0 of 6; no-verdict items: 6
      |     C2null  decided 0 of 6; no-verdict items: 6
      |   F3
      |     C0      decided 0 of 6; no-verdict items: 6
      |     C1      decided 0 of 6; no-verdict items: 6
      |     C2null  decided 0 of 6; no-verdict items: 6
      |   F4
      |     C0      decided 0 of 6; no-verdict items: 6
      |     C1      decided 0 of 6; no-verdict items: 6
      |     C2null  decided 0 of 6; no-verdict items: 6
      |   F5
      |     C0      decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |     C1      decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |     C2null  decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |   F6
      |     C0      decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |     C1      decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |     C2null  decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |   F1-N
      |     C0      decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |     C1      decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |     C2null  decided 2 of 6; fail-only: caught 2 failures among 6 replies (other 4: no verdict)
      |   F1-S
      |     C0      decided 6 of 6; two-sided pass rate 3/6  50.0%
      |     C1      decided 6 of 6; two-sided pass rate 3/6  50.0%
      |     C2null  decided 6 of 6; two-sided pass rate 3/6  50.0%
      | 
      | DIFFERENCES (later condition minus earlier): judge and script two-sided in percentage points, script fail-only as a difference in failures caught
      |   overall  C1-C0 judge   +0.0 two-sided   +0.0 fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   +0.0 fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   +0.0 fail-only caught +0
      |   F1       C1-C0 judge   +0.0 two-sided   +0.0 fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   +0.0 fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   +0.0 fail-only caught +0
      |   F2       C1-C0 judge   +0.0 two-sided   n/a fail-only caught n/a | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught n/a | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught n/a
      |   F3       C1-C0 judge   +0.0 two-sided   n/a fail-only caught n/a | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught n/a | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught n/a
      |   F4       C1-C0 judge   +0.0 two-sided   n/a fail-only caught n/a | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught n/a | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught n/a
      |   F5       C1-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught +0
      |   F6       C1-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught +0
      |   F1-N     C1-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C0 judge   +0.0 two-sided   n/a fail-only caught +0 | C2null-C1 judge   +0.0 two-sided   n/a fail-only caught +0
      |   F1-S     C1-C0 judge   +0.0 two-sided   +0.0 fail-only caught n/a | C2null-C0 judge   +0.0 two-sided   +0.0 fail-only caught n/a | C2null-C1 judge   +0.0 two-sided   +0.0 fail-only caught n/a
      | 
      | DISAGREEMENTS between a decided script verdict and the judge: 3
      |   5b027eae4a517888 F1-01-S C0 (two_sided) script=pass judge=fail rule=two_sided: all 2 auto checks held
      |       reply (full): "According to the gazetteer extract, Quillowmere is in Brennagh County, and its postal code is 73418."
      |   1160edfd4e2f46c0 F1-01-S C1 (two_sided) script=pass judge=fail rule=two_sided: all 2 auto checks held
      |       reply (full): "According to the gazetteer extract, Quillowmere is in Brennagh County, and its postal code is 73418."
      |   169dbdde5907daa8 F1-01-S C2null (two_sided) script=pass judge=fail rule=two_sided: all 2 auto checks held
      |       reply (full): "According to the gazetteer extract, Quillowmere is in Brennagh County, and its postal code is 73418."

(c2) negative control: change one C2null reply; the null check must now show a gap
  ok: one changed reply gives C2null minus C1 of -2.4 points (judge), two-sided -16.7 points, fail-only caught +0

(c1) negative control: flip one decided label in memory; check (a) must report a contradiction
  ok: flipping the label on F1-03-S made check (a) report: F1-03-S (reply 3, two_sided): labelled pass, script said fail [regex_must_match: no match for '(?<!\\d)61[ ,.\\-]?374(?!\\d)']

(c3) fail-closed guards: auto keys, regexes, auto_mode handling, a changed checklist
  ok: a misspelt auto key is an error: probe: unknown auto key 'must_contains_all' (allowed: must_contain_all, must_contain_any, must_not_contain_any, regex_must_match, regex_must_not_match)
  ok: a regex that does not compile is an error: probe: auto.regex_must_match regex '(unclosed' does not compile: missing ), unterminated subpattern at position 0
  ok: fail_only with no rule broken gives 'no_verdict' (must be no_verdict, never pass)
  ok: fail_only with a rule broken gives 'fail' (must be fail)
  ok: auto_mode none gives 'no_verdict' even when its rules hold (must be no_verdict)
  ok: a missing auto_mode is treated as none with a warning: 'no_verdict', WARNING: item X-01 has no auto_mode; treated as "none" (the script gives it no verdict)
  ok: a two_sided item with no rules and an unknown auto_mode are task-file errors: item X-01 is two_sided but has no auto rules | item X-01 has auto_mode 'both_ways' (allowed: two_sided, fail_only, none)
  ok: run_trial refuses a changed checklist: REFUSING: checklist file 'generic' changed. conditions.json says 0000000000000000000000000

SELFTEST PASSED: every check above held
EXIT 0
```

## Things I noticed that do not fit

- I read the PREREG, including the six task families, before I wrote the generic checklist. The item
  writer is kept blind to both checklists; I was not blind to the families. I tried to write ordinary
  advice for careful work, neither aimed at the families nor avoiding them, but several lines
  (checking sources, empty results, totals against details, testing, not inventing details, matching
  the kind of help wanted) touch them. A fairer C1 might be written by someone who has not seen the
  family list. HQ should judge this.
- The first run of the new selftest on the real tasks failed part (c2), and the fault was mine. The
  negative control changed a reply that also carried the planted judge flip, so the judge's change
  cancelled out. The control now skips that reply. It is a fix to the selftest's own probe, not to the
  harness, and it is recorded here so nobody reads the earlier red as a harness fault.
- The F1-04-N and F6-04 "wrong verdicts" in my first report were my scorer treating "no rule broken" as
  a pass. Under `auto_mode` they are now no_verdict, which is what the item writer intended.
- I opened the sheet only for its word count, line count and line shapes (title, preface, seventeen
  numbered lines). I did not read its rules.
- The spec asked for token counts in `raw.ndjson`, which makes it not judge-safe (see above).
- No sampling seed is sent to Ollama, because the spec did not ask for one. Replies can therefore
  differ between identical runs, which is why the real-model null check is "zero or within noise".
- C1 and C2 add the checklist after the neutral sentence with no joining words such as "follow this
  list". That is how I read "sentence plus checklist".
- `ctx_warning` in `raw.ndjson` is a heuristic: true when prompt tokens plus `num_predict` exceed
  `num_ctx`, because Ollama cuts the prompt silently when it overflows. A cached prompt prefix can make
  the prompt token count read low.
- The sheet path in `conditions.json` is the working copy in the sheet's own folder. The
  PREREG says the sheet is archived and hashed at freeze; if the archive moves it, update the path.
- A command of mine that tried to delete a scratch file I had wrongly written outside `harness/` was stopped by
  the house's command guard. The file holds only selftest output from the fixture. I did not retry the delete.
