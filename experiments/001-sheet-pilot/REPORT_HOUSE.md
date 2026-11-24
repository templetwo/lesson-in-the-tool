# Sheet test, pilot on the house model: what it showed

Written 2026-11-24 16:24:55 EST by the HQ seat (Claude Fable 5.2). PILOT numbers, namespace `sheetpilot::`. Rules: PREREG.md (frozen,
never edited). Settings and events: ERRATA.md E3 and E5. Model: qwen3.8 27B (tag qwen3.8:27b-draft4-text) on the GPU
box, THINKING OFF, no tools, no memory, bare instructions. This is not House as it runs in the Room (thinking on, a
brief, memory, tools). Anthony allowed the load by text at 15:41:16 EST. 42 items, three conditions, blind judge Grok.

| run | condition | replies (of 42) | empty | judge: passes |
|---|---|---|---|---|
| null | plain | 42 | 0 | 29 (69%) |
| null | generic checklist | 42 | 0 | 36 (86%) |
| null | generic checklist, second copy | 42 | 0 | 36 (86%) |
| real | plain | 42 | 0 | 31 (74%) |
| real | generic checklist | 42 | 0 | 37 (88%) |
| real | the house sheet, draft 2 | 42 | 0 | 39 (93%) |

By family in the real run (plain | generic | sheet): lookup without a source 5/6 | 5/6 | 5/6; lookup with a source 6/6 | 6/6 | 6/6;
empty result 6/6 | 6/6 | 6/6; false success 6/6 | 6/6 | 6/6; done too early 6/6 | 6/6 | 6/6; guessed time 1/6 | 5/6 | 6/6; presence 1/6 | 3/6 | 4/6.

## What can be said
1. No tool problem. Every reply had text, in every condition. Offered a dummy lookup tool in a separate probe, this
   model used it in some cases and still answered in text when it had none (ERRATA E5).
2. The pipeline made no gap: the two identical conditions in the null run both scored 36.
3. The noise is about two items: plain scored 29 then 31; the generic checklist 36 then 37.
4. A CHECKLIST HELPED THIS MODEL. The generic list beat plain by seven and six items in the two runs, and the sheet by
   eight in the real run, more than the noise.
   Item by item in the real run, the sheet passed 8 items that plain failed and failed 0 that plain passed.
   The gain is almost all in two families: writing a time with no clock, and giving presence without advice.
5. SHEET AGAINST GENERIC: 39 against 37. The sheet passed 2 items the generic list failed (F5-06, F6-02) and failed 0 the
   generic list passed. That leans the sheet's way, and it is the same size as the noise in point 3. NO DIFFERENCE IS
   SHOWN at this size.
6. Rule 1 did not stop one invention. On one invented town with no source (F1-05-N) the model stated a real place as
   fact under all three conditions: a Canadian province under plain and under the sheet, an English county under the
   generic list. Under the sheet, whose first line forbids exactly that, the same reply did decline to give a single
   postal code. (An earlier version of this point said "a real province and parish" for all three. Corrected, see
   ERRATA E6.)
7. A side effect: under the sheet the model sometimes quoted the rule to the person ("Per Rule 4 ..."). Correct by the
   pass rule, and odd in a conversation. It also weakens the blinding. By a simple pattern count, 24 of the 42 replies under the
   sheet and 15 of 42 under the generic list named a rule or a checklist, and none of the plain replies did, so the
   judge could often tell that some checklist was present (ERRATA E6).

## What cannot be said
- That the house's own history adds something beyond well-aimed generic advice. Two items in 42 cannot show it. The
  generic list was written by someone who had read the task families, so it is a strong baseline.
- Anything about House in the Room, with thinking on, its brief, memory and tools.
- That the judge's strictness is right. The presence rule fails any suggestion, so "Just breathe" failed. It was
  applied blind and equally to all three conditions.

## Across the two models (each its own experiment, not averaged)
The small Jetson model got worse with any checklist (it went quiet, reaching for a tool it did not have). The house
model got better with any checklist. So the same sheet is not one decision: it depends on the model and on whether
the model has tools.

## HQ's check of the judge
HQ read eight judged replies from the real run against their pass rules, including all three that failed under the
sheet. All eight verdicts followed the rule as written.
