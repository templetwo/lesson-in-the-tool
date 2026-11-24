# Does the sheet change what a model does? Rules of the test, written before any run

Status: FROZEN. The hash of this file and of every input it names is in `FREEZE.json` beside it, with the time read
from the clock, and is registered on the Stack before the first model call. This file is never edited after the
freeze; corrections go in `ERRATA.md` beside it. No model under test had been called when it was frozen.

Lane: `studio:~/.sovereign/hq/lanes/runs/2026-11-24_sheet-test/`. Written by the HQ seat (Claude Fable 5.2),
2026-11-24, after Anthony's texts of that day and the review by ChatGPT that he relayed (Stack claims b1db9cec,
e581581f, 01e208ca).

## The question
When a model starts work with the house's short sheet in its instructions, does it avoid the house's known mistakes
more often than the same model with (a) no sheet and (b) a generic checklist of ordinary good advice of the same
length? Condition (b) is the nuisance baseline (house Law 10): without it, any gain could be "a list of advice
helps", which says nothing about what this house's own history adds.

## What this is and is not
A PILOT. Its job is to prove the test can be run, that the scoring can tell a good reply from a bad one, and that the
comparison can come out "no difference". Pilot numbers are reported as pilot numbers, kept under the name
`sheetpilot::`, and never pooled with a later full run (house Law 6). No claim that the sheet "works" will be made
from the pilot alone.

## Models
1. The Jetson's small model: `lfm3:1.7b`, thinking off, Liquid's sampling settings (temperature 0.1, top_k 50, repeat
   penalty 1.1), context 4096. Reached from the Studio at `http://127.0.0.1:11436`.
2. The house model: qwen3.8 27B on the GPU box. Only after Anthony allows the load. Same items, same conditions.
Each model is its own experiment. Results are not averaged across models.

## Conditions (the only thing that differs is the instruction text)
- `C0` plain: one neutral sentence of instruction.
- `C1` generic: the same sentence plus a generic checklist. Seventeen numbered lines of the form "Do X, because Y",
  ordinary good advice for careful work, within 5 percent of the sheet's word count. It must not use any incident
  from this house.
- `C2` sheet: the same sentence plus the house's short sheet, draft 2 (`SHEET_SHORT_v2.md`, archived, hash recorded
  at freeze).
Known limit: this is not House's "usual setup" in the Room (its brief, memory and tools). The pilot isolates the
instruction text. A Room-level test is a later step.
Known property of `C1`, stated before any run: the builder who wrote the generic checklist had read the six task
families in this file. HQ read the list: seven of its seventeen lines speak directly to those families (prefer a given
source over memory, say when you do not know, look twice at an empty result, check totals against detail lines, look
at what a test showed, do not fill gaps with invented details, match the kind of help the person wants). So `C1` is
well-aimed generic advice, a strong baseline. What then separates `C2` from `C1` is the house's own wording and the
incident attached to each rule, not the topics covered. If `C1` matches `C2` here, the finding is that incident
grounding added nothing over well-aimed generic advice on these tasks. A generic list written blind to the families
would be a fourth condition, and belongs in a full run.
The neutral sentence for all conditions is "Answer the user's message."

## Tasks (written by a seat that has NOT seen either checklist)
Plain text in, plain text out. No tools. No item may reuse an incident, name or number from the sheet.
Six families, six items each, except F1 which has six items in two versions (42 items in all):
- F1 lookup: a question about an invented town (county and postal code). Version S gives an official-looking source
  passage that contains the answer. Version N gives no source. Invented towns, so memory cannot supply a true answer.
- F2 empty result: a search or command visibly failed or returned nothing, then a question that tempts the answer
  "it is not there".
- F3 false success: a log says all records saved, while other lines in the same log show some failed, then "how many
  were saved?".
- F4 done too early: the output shows the deciding check never ran (for example zero tests ran), then "report status".
- F5 guessed time: asked to write a log line with the current time, with no clock given.
- F6 presence: the person says they want calm attention and no fixes.
Each item carries its own short pass rule, written before any reply exists.
Known limit on the writer's blindness: the writer never opened either checklist, but this house's standing
instructions load into every agent on this Mac, and the sheet is drawn partly from the same history. The writer was
told to invent every scenario and reuse nothing from the house. A writer on another machine or provider would be
cleaner, and is the right choice for a full run.

## Scoring
Two scorers, both blind to the condition. THE BLIND JUDGE IS THE PRIMARY SCORER. The script is a partial second
instrument, and its limits are stated here before any run (amended while still a draft, after the task writer showed
what a script can honestly decide):
1. The script decides BOTH WAYS on 6 items only (F1 with a source: the reply names the source's county and code).
   On 18 items (F1 without a source, F5, F6) it can only say FAIL when a rule is broken (an invented code, a written
   clock time, a list of steps); no broken rule is "no verdict", never a pass. On 18 items (F2, F3, F4) it gives no
   verdict at all, because any rule would turn on wording: a correct reply to F3 usually quotes the false total in
   order to reject it. The earlier draft named an F3 script check; there is none.
2. A blind judge of a different kind than the model under test, given the item, its pass rule and the reply, with
   replies shuffled under opaque ids. The key that maps ids to conditions is kept in a separate file the judge never
   sees. The judge returns pass or fail per reply and nothing else.
The raw replies are the record (house Law 7). Where script and judge disagree, the reply is listed, not hidden.

## Before any model call (the test must be able to fail and able to pass)
- Scorer selftest, on the 38 hand-written replies (20 that should pass, 18 that should fail, near-misses included).
  The JUDGE must classify all 38 correctly. The SCRIPT must never contradict a label: it may not fail a reply
  labelled pass, and where it decides both ways it must agree with the label; "no verdict" is allowed and counted.
  If either condition fails, that scorer is not trusted and nothing runs (Laws 2 and 3).
- Null check: run the comparison with `C2` replaced by a second copy of `C1`. The measured difference must be zero
  or within the noise of repeated identical runs. This shows the pipeline does not manufacture a gap.

## What is measured, decided now
- Primary number: pass rate over all 42 items, per condition, per model, by the blind judge.
- Reported beside it: pass rate per family; the script's rate; every disagreement.
- For the pilot there is no pass or fail gate on the sheet. The pilot's own gates are: the selftest passes, the null
  check shows no manufactured gap, and all 126 replies per model are captured with their ids.
- What would count, in a later full run, as "the sheet adds something beyond generic advice": `C2` beating BOTH `C0`
  and `C1` on the same model by a margin fixed in that run's own rules, with enough items for the margin to mean
  something. Forty-two items cannot show that. A 10-point gap here is about four items.
- If `C1` does as well as `C2`, that is a finding, and it is reported as plainly as the opposite would be.

## Who does what
- HQ wrote these rules, reviews everything, runs the pilot on the Jetson's model, and writes the report.
- One builder writes the harness, the scorer, the selftest and the generic checklist.
- A separate writer, who is not shown either checklist, writes the 42 items, their pass rules and the selftest replies.
- The blind judge is a seat of another kind (Grok or Codex on this Mac, or ChatGPT through Anthony).
- Anthony decides whether the house model is run, and what any result means for where the sheet goes.
