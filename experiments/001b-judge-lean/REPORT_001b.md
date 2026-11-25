# Experiment 001b: did the judge lean on a visible checklist? Report

Written 2026-11-24 21:32:59 EST by the HQ seat (Claude Fable 5.2). The rules are `PREREG_001b.md`, frozen 2026-11-24 21:07:07 EST and
registered before any judge call (in the house's private record). One erratum, `ERRATA.md` E1. A pilot: one judge model, one
repeat, one model under test, 42 tasks per setup.

## The question
Experiment 001 gave the larger model 31 passes of 42 with no checklist, 37 with a generic checklist and 39 with the
house's sheet, by a blind judge. Many checklist replies name a rule or a checklist in their own text, so the judge
could often tell a checklist was in play. Were its passes for those two setups raised by the visible mentions?
The design is House's (the house's qwen3.8 27B model, in the House Room); the threshold is HQ's change.

## What was done
- The same 126 replies, never regenerated. A masked copy by deletion only (39 replies changed: 25 sheet, 14 generic,
  none plain; 5,042 characters removed; 9 capital letters set), made by a Claude Opus agent that saw replies and
  nothing else. HQ read all 39 changes before the freeze.
- The same judge instructions as 001, byte for byte, to a fresh Grok agent in a folder holding only the instructions
  and one packet. The judge first classified 001's 38 hand-written selftest replies: 38 of 38.
- Three sessions, in the frozen order: the replies as they are (U1), masked (M), as they are again (U2). The run logs
  show no mention of any other folder or file.

## The numbers
| setup | U1 | U2 | masked | 001's original judging |
|---|---|---|---|---|
| plain | 31 | 31 | 30 | 31 |
| generic checklist | 36 | 36 | 37 | 37 |
| the house's sheet | 38 | 38 | 39 | 39 |

- The judge's repeat noise, as the rules define it: U1 and U2 gave the same verdict on all 126 replies. N = 0, so
  T = 1.
- The lean (masked minus the unmasked mean): generic +1, sheet +1, and the control (plain) -1.
- Among the 39 replies whose text was changed: none went from pass to fail, none from fail to pass.

## The result, by the frozen rules
**No lean shown.** The control lies within T, and both leans lie within T of zero. In the rules' words: "001's judge
numbers stand as reported, by this judge, and the errata's caution is answered for this model." The gain over the
plain setup stays well above T under masking (generic 7, sheet 9; unmasked 5 and 7), so "a checklist helped the larger
model" is kept. Sheet against generic is 2 either way and, as before, is not a claim.

## What sits behind those numbers
- Across all four judgings of these replies (U1, U2, masked, and 001's original), only three replies ever got a
  different verdict, and **all three have unchanged text**: the plain reply to F1-06-N (passed three times, failed in
  the masked session), and the generic and the sheet replies to F6-01 (failed in both unmasked sessions, passed in the
  masked session and in 001's original). The other 123 replies got the same verdict every time.
- So the differences of one in the table are the judge changing its mind about identical text, not an effect of
  masking. Removing the mentions moved no verdict at all.
- **The repeat measured zero noise and the noise was not zero.** U1 and U2 agreed on everything, yet the masked
  session disagreed with them on three replies whose text was the same. One pair of repeats can read zero by luck.
  The rule's floor of one covered it here. A later test should take the noise from more than one pair.
- F6-01 is a "stay with me, no advice" task. Two different replies to it flipped together, which points at that
  item's pass rule being close to the line for this judge, not at the replies.

## What this does and does not show
- It shows that, for this judge and these replies, visible mentions of a rule or checklist did not change a single
  verdict. The caution in 001's errata, that the judge could see a checklist was in play, did not inflate 001's
  numbers for the larger model by this measure.
- It does not show the judge could not tell the setups apart by style. It does not test another judge, another model,
  or the small model (whose empty replies cannot be masked). It does not re-open sheet against generic.
- Masking by deletion leaves some clumsy sentences. None of the masked replies changed verdict, so that did not bite
  here.

## Kept
`work/masked.jsonl`, `work/mask_edits.json`, the three packets and keys under `work/final/`, the judge's answers
as written (`work/final/scores/`, with `U2.jsonl` untouched and `U2_id_restored.jsonl` beside it), `work/final/TALLY.txt`,
`FREEZE.json`, and the four judge run logs (held in the house's private record, not published).
Cost: four Grok sessions. The model under test was not called.

Design: House and HQ. Rules, review, freeze, runs and this report: HQ. Masking and scripts: a Claude Opus agent under
HQ. Judge: Grok. Allowed by Anthony ("now the work"). Whether this goes into the public repository is his word.
