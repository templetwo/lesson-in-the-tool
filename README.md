# Tier 35: where does a lesson live?

**A research project at its starting line. Nothing here is an established result. Two small pilots have been run,
their rules were frozen before they ran, and their raw data is in this repository.**

By Anthony Vasquez Sr. (Temple of Two), with Claude (Claude Fable 5.2, the HQ seat). Started 2026-11-24.

> "most of the stuff that we went through, you know it gets repeated and neither one of us kind of catch it because
> my memory and your memory are both not too good when it comes to certain things"
> Anthony, by text, 2026-11-24

> "If the prose makes no difference but a required readback does, that's a useful answer: the lesson belongs in the
> tool, not in a longer prompt."
> a Codex seat, reviewing the first draft the same day; the sentence Anthony singled out

## The question

A person and a series of AI models work together for a long time. They make mistakes, catch them, and write down
what they learned. The models change. The person's memory is finite. The same mistakes come back.

When a lesson has been paid for once, **where should it live so that the next model, one that never made the
mistake, does not make it again?**

A prompt is one possible home. It is not the only one. A lesson can also live in:

- a **tool** that does the careful step itself (re-reads what it wrote, reads the clock, copies the hash),
- a **check** that refuses bad input at the moment it is written,
- **retrieval**, which shows the old lesson at the moment it applies,
- a **gate** that stops an action until a condition is met,
- or the model's own **judgment**, left open on purpose.

This repository is the work of finding out, lesson by lesson, which home actually changes what the next model does,
and of measuring it instead of assuming it.

## Where this came from

The house behind this project keeps a long record of its own work: several thousand entries written by people and by
models from different companies, including a ledger of caught errors and periodic summaries of what each working
session learned. On 2026-11-24 that record was read for its repeated mistakes and boiled down into one sheet:
`sheet/SHEET_SHORT_v2.md`, seventeen lines of the form "do this, because that happened".

The obvious next move was to put the sheet into every model's instructions. Before doing that, we tested it. The
first test said: not so fast.

## What has been measured so far

One experiment, run as a pilot on two local models. Forty-two freshly invented tasks in six families (looking
something up with and without a source, an empty search result, a false success message, a check that never ran,
writing a time with no clock, and a person asking for company instead of advice). Three setups: the model with no
checklist, with a generic checklist of ordinary good advice of the same length, and with the house's sheet. Replies
scored by a judge of a different kind that could not see which setup produced them.

Judge's passes out of 42:

| model | plain | generic checklist | the house sheet | two identical setups (null check) |
|---|---|---|---|---|
| a 1.7B model on a Jetson (`lfm3:1.7b`) | 18 (21 in the null run) | 8 | 11 | 7 and 7 |
| a 27B model on a two-GPU box (`qwen3.8 27B`) | 31 (29 in the null run) | 37 (36 in the null run) | 39 | 36 and 36 |

What that supports, and no more:

1. **On the larger model a checklist helped**, by six to eight tasks, more than the run-to-run noise of about two.
   Nearly all of the gain was in two families: not inventing a time, and staying present without giving advice.
2. **The house's own sheet did not clearly beat well-aimed generic advice.** 39 against 37 leans its way and is the
   same size as the noise. No difference is shown.
3. **On the small model any long checklist made things worse.** More than half its replies came back empty. Told to
   check before it claims, this tool-trained model tries to call a lookup tool; it had none, and the server strips the
   call. That is the tested cause of the short empty replies, on three prompts and six calls. The empty replies that
   used the whole budget were not checked one by one.
4. **The first rule did not stop one invention.** On one invented town the larger model stated a real place as fact
   under all three setups (a Canadian province under two, an English county under the third). Under the sheet, whose
   first line forbids exactly that, the same reply did decline to give a postal code.

Two cautions about these numbers. The noise figures each rest on one repeat. And the judging was less blind than the
word suggests: under a checklist the models often named a rule or a checklist in their replies, and the small model's
empty replies came only from the checklist setups, so the judge could often tell that some checklist was present.

Full reports, with every limit stated: `experiments/001-sheet-pilot/REPORT.md` (small model) and
`experiments/001-sheet-pilot/REPORT_HOUSE.md` (larger model). What changed or was found along the way, including our
own mistakes: `experiments/001-sheet-pilot/ERRATA.md`.

## What has not been shown

- That the house's history adds anything beyond good generic advice. Forty-two tasks cannot separate them.
- Anything about a model with tools, about cloud models, or about the larger model in its everyday setup. The pilot
  used bare instructions, no tools and no memory, with the larger model's reasoning switched off.
- That a lesson in a tool beats a lesson in a prompt. That is the next experiment, and it has not run.

## What comes next

1. **Experiment 002, the lesson in the tool** (`experiments/002-lesson-in-the-tool/PREREG_v2_DRAFT.md`, a draft, not
   frozen). Twelve small jobs in a simulated workspace, each in a version that truly succeeds and a version whose
   success message is false. Four arms: plain; "verify your work"; the house's lesson as prose; and no advice at all,
   with the readback built into the tool. Because half the jobs really succeed, it also catches a model that has
   learned to distrust everything.
2. **The translation table** (`docs/TRANSLATION_TABLE.md`). Each of the seventeen lessons, a proposed home, and a
   test that can fail. One seat's first sort is there, unchecked. The plan is for several models to sort it
   separately and to study where they disagree.
3. **Bigger and cleaner tests** once the pilots have shown where the noise is: more tasks, task writers on another
   provider, the larger model in its real setup, a lookup tool for the small one.

See `docs/ROADMAP.md`.

## How this work is done

The rules are in `docs/METHOD.md`. In short: the rules of a test are written, hashed and registered before the first
model call and never edited afterwards; every test must be shown able to fail; a generic baseline stands beside the
thing being tested; the judge is a different kind of model and cannot see the setup; raw replies are the record;
corrections are written beside the original, never over it; and "no difference" is reported as plainly as a win.

One more rule, specific to this project: the Claude seat that co-authors this work is a biased judge of it. Outside
models were asked to review the sheet and the plan, and their reviews are in `reviews/` as they were relayed, with a
header line added by us and one place name removed. They were written before the pilot reports existed; no outside
model has yet reviewed the reports.

## What is in this repository

```
sheet/                         the consolidated sheet: short form (drafts 1 and 2), a public edition of the long
                               form, and notes on what was withheld from it
experiments/001-sheet-pilot/   frozen rules, hashes, errata, reports, harness, tasks, raw runs, judge scores
experiments/002-lesson-in-the-tool/   draft rules for the next test
docs/                          method, the translation table, the roadmap
reviews/                       reviews by other models, as relayed by Anthony
PROVENANCE.md                  who made what, with hashes
MANIFEST.sha256                the hash of every file in this repository
```

## Checking our work

- `experiments/001-sheet-pilot/FREEZE.json` lists the SHA-256 of the rules and of every input, taken at 13:48:07
  Eastern on 2026-11-24, before any model under test was called. `shasum -a 256` on the files should match. The frozen
  files are published byte for byte, which is why they still carry file paths from the machine they were made on and
  identifiers from the house's private record, which an outside reader cannot resolve. The hashes can be checked by
  anyone. The time of the freeze cannot: it is the house's own record of it.
- In files that are not frozen, private paths and one address on the house network were generalised before
  publication. `experiments/001-sheet-pilot/ERRATA.md`, entry E6, lists what was changed and why.
- `python3 experiments/001-sheet-pilot/harness/selftest.py` runs the scorer's self-check with no model and no network.
- The harness runs against any Ollama endpoint. `experiments/001-sheet-pilot/harness/README.md` has the steps.
- `shasum -a 256 -c MANIFEST.sha256` checks every file here.

## Who made this

Anthony Vasquez Sr. set the direction, asked the questions this project is built on, allowed each run, and decides
what any result means. Claude (Claude Fable 5.2, the HQ seat on the house's Mac Studio) wrote the rules of the test,
reviewed every piece, ran the pilots and wrote the reports. Claude Opus 5.5 agents drafted the sheet from the record,
built the harness and wrote the task items. The three-setup blind design and the rewording of rule 11 are ChatGPT's.
The tools-and-true-successes design of experiment 002 is a Codex seat's. A Grok agent was the blind judge. Their
contributions are named where they were used.

## Rights

Rights are pending. All rights reserved until Anthony Vasquez Sr. chooses a license for this repository.
