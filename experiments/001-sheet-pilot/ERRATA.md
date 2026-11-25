# Errata and run log for the sheet test (PREREG.md is frozen and is not edited)

Every entry is dated from the clock. Nothing here changes the rules in PREREG.md; it records what was found and what
was set before the scored runs.

## R1. Scorer selftests, before any model under test was called
- Script: `selftest.py` on the real tasks, run by HQ after the freeze inputs were final: SELFTEST PASSED. The script
  decided 13 of the 38 hand-written replies and contradicted no label.
- Judge: a fresh Grok agent, working in a folder that held only the packet and its instructions. Result: 38 of 38
  right ("JUDGE SELFTEST PASSED"). The record of its run shows no mention of the test's own folder or of any key file.

## E1. Smoke test, declared: three calls, not scored, not pooled
Written 2026-11-24 13:53:40 EST. Before the null run HQ ran `run_trial.py --limit 3 --seed 1` into `runs/smoke_lfm3/` to check the
plumbing against the Jetson's model. All three records said ok. TWO OF THE THREE REPLIES WERE EMPTY. Both empty ones
were under a checklist condition (prompt tokens 783 and 824); the one with a reply was the plain condition (63).

What HQ then measured directly (five more calls, also not scored):
- Plain condition: the model answers (109 to 173 tokens).
- With either checklist in the instructions, the model sometimes returns no reply at all: it used the whole 400-token
  budget and stopped on length, or produced 27 tokens and stopped, with empty content both times.
- With reasoning left visible, those tokens are reasoning text (3,893 characters, no answer, budget spent).
- With reasoning switched off and a 1,500-token budget: one item answered after about 500 hidden tokens; another used
  all 1,500 and still gave no reply.
So `think: false` HIDES this model's reasoning in Ollama. It does not stop it. A long instruction block makes the model
reason at length even when told not to.

The maker says the same. Liquid's card for LFM3-1.7B (fetched from Hugging Face during this check): "Reasoning is
enabled by default. You can set `enable_thinking=False` to disable thinking traces, but this behavior can be
inconsistent, especially for reasoning-heavy tasks." Its example uses a budget of 2048 new tokens.

What is set for the runs because of this, decided BEFORE the null run and the real run:
1. `--num-predict 2048` (the card's own example value) for both runs. Context stays 4096; prompt plus budget fits.
2. An empty reply is a counted outcome, reported per condition beside the judge's pass rate. The judge still sees
   every reply, empty ones included, and applies the item's pass rule.
3. Seeds: null run 20261124, real run 20261125.
Why this matters beyond the harness: if a 600-word instruction block makes this small model fail to answer at all,
that is itself an answer to "should the sheet go into the Jetson model's prompt", whatever the sheet says. The same
behaviour bears on the Jetson's Room voice, which also gives this model a system text with thinking switched off.

## E2. What the two runs on the Jetson's model showed, before any judging
Written 2026-11-24 14:45:14 EST. Null run 13:53:49 to 14:14:38 EST, real run 14:14:38 to 14:43:22 EST (stamps in the task output);
the calls that errored were retried once at 14:44:38 to 14:44:50 EST. Counts are from raw.ndjson joined to key.json by HQ.

| run | condition | replies captured (of 42) | EMPTY replies | stopped at the 2048 budget |
|---|---|---|---|---|
| lfm3_null | C0 | 42 | 0 | 0 |
| lfm3_null | C1 | 41 | 27 | 5 |
| lfm3_null | C2null | 41 | 26 | 4 |
| lfm3 | C0 | 42 | 0 | 0 |
| lfm3 | C1 | 39 | 25 | 2 |
| lfm3 | C2 | 42 | 22 | 11 |

lfm3_null: still missing after the retry (server error both times): F2-05 under C1, F2-05 under C2null

lfm3: still missing after the retry (server error both times): F2-05 under C1, F3-02 under C1, F6-02 under C1

The plain condition never produced an empty reply. Under EITHER checklist, more than half the replies were empty.
The server errors are all HTTP 500 from Ollama, "XML syntax error ... element <function> closed by </param...": the
model wrote a malformed TOOL CALL and Ollama's parser for this model failed on it.

Mechanism, checked with six direct calls (not scored): under a checklist the model tries to CALL A TOOL to look the
thing up. No tool was offered, so Ollama strips the call and returns empty text (about 20 to 30 tokens, a normal stop).
When HQ offered a dummy `lookup` tool, the same prompts returned a proper tool call and no text, for example a lookup
for the invented town's county and postal code, under the generic checklist and under the sheet alike.

What this means for the pilot. This model was trained for agent work with tools. Told to check before it claims, it
reaches for a tool. A text-only harness cannot see that, and scores it as silence. So on THIS model the pilot as
designed cannot answer the sheet question: the judged pass rates below it are mostly a count of empty text. The
judging is still run and reported, because the frozen rules say so. The useful result is the mechanism itself.
A harness that offers a lookup tool and treats "asked to look it up" as a kind of reply is a different test and
needs its own rules written before it runs. It is not a patch to this one.

## E3. The house model: his yes, and the settings, written before its first call
Written 2026-11-24 15:42:49 EST. Anthony allowed the load by text at 15:41:16 EST: "Let’s run House on the same
test and let’s see what it built and then if it runs into the same tool issue, we have a lead."
Read on the box at 15:42:04 EST before any load: nothing loaded in Ollama, both cards idle with junction 22 C and
fans turning, no jobs running besides the box's own fan and light daemons.

Settings for the house model, decided before its first call:
- Endpoint `http://<gpu-box>:11434` (the box's address on the house network, removed for publication), tag
  `qwen3.8:27b-draft4-text` (the tag the house's route for this model points at).
- `--num-ctx 32768`, the size the Room loads this model with, so the test and the Room share one loaded copy and the
  model is not reloaded back and forth. `--num-predict 2048`, as in the Jetson runs. `--timeout 180`.
- Thinking OFF, because the frozen harness sends `think: false` on every call. KNOWN LIMIT: in the Room this model has
  run with thinking ON since 2026-11-23 19:38. So this is the house model with thinking off, in a bare instruction
  setup with no tools and no memory. It is not House as it runs in the Room. A thinking-on run would be its own
  declared variant.
- Seeds: real run 20261126, null run 20261127. The real run goes FIRST this time, so that if the box misbehaves under
  load the run that answers his question is already captured. A three-call smoke test comes before both, not scored.
- Card temperatures are logged once a minute to `runs/house_temps.log` for the length of the runs.

## E4. Two corrections to what HQ said about the Jetson pilot (caught by an echo agent reading HQ's work)
Written 2026-11-24 15:44:10 EST.
1. ORDER. HQ texted Anthony "18 (and 21 when I ran it a second time)". The plain condition scored 21 in the NULL run,
   which ran FIRST (13:53:49), and 18 in the real run, which ran second. REPORT.md has the right numbers per run; the
   text had the order backwards. Corrected to him by text.
2. CAUSE. HQ wrote and texted that it had found why the replies were empty, as one cause. There are two kinds of empty
   reply and only one was tested. (a) SHORT empties (a few dozen tokens, a normal stop): the model is calling a tool it
   was not given. Tested on three prompts, with and without a dummy tool (six calls), and consistent with the five
   HTTP 500 parse errors. (b) Empties that used the WHOLE 2048 budget (10 of the 47 empty replies in the real run, 5 of
   53 in the null run): not tested reply by reply. The warm-up in E1 showed hidden reasoning running out of budget, and
   that is the likely cause, but it is an inference. The middle group (41 to 2047 tokens, then a normal stop with no
   text) is also untested: it could be reasoning followed by a stripped tool call.
   So REPORT.md point 3 ("the cause is ... tries to call a lookup tool") overstates. Read it as: a tool call that the
   server strips is the tested cause of the short empties; the rest are unexplained in detail.

## E5. The house model's runs, before any judging
Written 2026-11-24 16:11:33 EST. Smoke test 15:42:49 to 15:43:08 EST (3 calls, `runs/smoke_house`, not scored): all three answered
with text. Real run (seed 20261126) ended 15:56:24 EST; null run (seed 20261127) 15:56:24 to 16:10:21 EST.
- Both runs: 126 of 126 replies captured, 0 errors, 0 empty replies, 0 replies stopped at the budget, in every
  condition. Median reply length by condition 135.5 to 168.5 tokens (this line first said 136 to 181, from a cruder
  middle-value pick; corrected in E6).
- The box held. Hottest card junction in the minute-by-minute log: 74 C. Every line of `runs/house_temps.log` ends
  with the words "BOX UNREACHABLE": that label is a fault in HQ's logger (it is printed whenever the remote command's
  last test is false), not a fact about the box. Each of those 27 lines carries live readings from the box.
- A probe at 16:10:51 EST, not scored (6 calls, a dummy `lookup` tool offered): on the invented-town item the house
  model called the tool under the plain condition and under the sheet, and answered in text under the generic
  checklist; on an empty-result item it answered in text under both checklists and did both under plain. So this model
  uses a tool when it has one and still answers in text when it has none. The silence seen on the Jetson's small model
  did not appear here.

## E6. Corrections found by a pre-publication review, and what was generalised for publication
Written 2026-11-24 17:27:31 EST. Before this work was made public, a Claude Opus 5.5 reviewer read every file and recomputed every count.
All counts matched the raw data and all 11 frozen hashes matched. It found the following, and each is corrected here.
1. A FACTUAL ERROR in the house model's report and in what HQ told Anthony. The report said that on one invented town
   the model "named a real province and parish as fact" under all three conditions. The three replies to F1-05-N: under
   plain, a Canadian province and a county; under the generic list, an English county; under the sheet, a Canadian
   province and a parish, and in that reply the model declined to give a single postal code. All three stated a real
   place as fact, so the point stands, but "province" was wrong for one of them. REPORT_HOUSE.md point 6 is corrected.
2. REPORT_HOUSE.md point 4 said both checklists beat plain "in both runs". The sheet ran only in the real run. Now: the
   generic list beat plain by seven and six in the two runs, the sheet by eight in the real run.
3. E5 gave the house model's median reply length as 136 to 181 tokens. The medians by condition are 135.5 to 168.5.
4. A LIMIT ON THE BLINDING that the reports did not state. Under a checklist the models often named a rule or a
   checklist in their reply. By a simple pattern count on the house model's real run: 24 of 42 replies under the sheet,
   15 of 42 under the generic list, 0 of 42 under plain (the reviewer, with a different pattern, counted 21 and 12). On
   the small model, empty replies came only from the checklist conditions. So the judge could often tell that some
   checklist was present, though not always which. No count changes; the judging was less blind than "blind" suggests.
5. The task file and its generator. `tasks/tasks.jsonl` as frozen carries a field, `auto_mode`, that the HQ seat added
   to all 42 items at 13:42:30, before the freeze at 13:48:07, to say whether a script may pass and fail an item, only
   fail it, or not judge it. The generator `tasks/build_items.py` was not updated, so running it reproduces the file as
   the task writer left it, with a different hash, and `tasks/README.md` listed the earlier hashes. Prompts and pass
   rules are identical in both. A note is now in `tasks/README.md`.
6. Generalised for publication, in files that are not frozen: message-record row numbers, the name of the house's
   dispatch tool and a run-log filename, the box's route name, the box's address on the house network (now `<gpu-box>`),
   identifiers from the house's private record, the name of a command-guard rule, and private file paths in the two
   READMEs and in the `meta` block of each run's `key.json`. Nothing in a frozen file was changed. The frozen files
   still carry paths and identifiers from the private record; an outside reader cannot resolve them.

## E7. Pointer: the caution in E6 point 4 was tested in experiment 001b
Written 2026-11-24 22:06:49 EST. Nothing above is changed by this entry.
E6 point 4 said the judge could often tell that some checklist was present. Experiment 001b judged the larger model's
126 replies again, as they are (twice) and with every mention of a rule or checklist deleted, under rules frozen before
any judge call. No lean was shown: removing the mentions moved no verdict, so the judge numbers in `REPORT_HOUSE.md`
stand for this judge, while one repeat of the judging read zero noise and three replies with unchanged text still
flipped. See `experiments/001b-judge-lean/`.

## E8. The frozen tally does not reject a duplicated planned pair
Written 2026-11-25. Found by the GPT-6 Astra Codex seat; reproduced the same day by an independent Claude Opus
reviewer under HQ. Nothing above is changed by this entry.

`harness/tally.py` builds its per-pair table with a dict, which collapses a duplicated planned pair, while its
expected count comes from the list (`len(planned)`). Its coverage sentence prints "all planned pairs have exactly
one reply" without checking that the plan itself has no duplicates. Duplicating one planned pair in a copy of the
house run's key makes `compute` return no problems with 127 expected and 126 captured; the rendered sentence still
claims complete coverage.

All four published plans (`house`, `house_null`, `lfm3`, `lfm3_null`) contain 126 distinct pairs. No published
number depends on this defect. The frozen tally remains unchanged. The separate archive verifier rejects a
duplicate plan, and its tests keep that malformed-input case as a control.
