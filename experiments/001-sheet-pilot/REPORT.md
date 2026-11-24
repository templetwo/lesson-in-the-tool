# Sheet test, pilot on the Jetson's small model: what it showed

Written 2026-11-24 14:53:49 EST by the HQ seat (Claude Fable 5.2). PILOT numbers, namespace `sheetpilot::`, never to be pooled with a
later run. Rules: PREREG.md (frozen 13:48:07 EST and registered in the house's private record). What changed or was found along the way:
ERRATA.md. Model: lfm3:1.7b on the Jetson through Ollama, thinking switched off, budget 2048 tokens. 42 items, three
conditions. Blind judge: a fresh Grok agent that first classified 38 of 38 hand-written replies correctly.

| run | condition | replies captured (of 42) | empty replies | judge: passes of the 42 asked | passes among replies that had text |
|---|---|---|---|---|---|
| null | plain | 42 | 0 | 21 of 42 (50%) | 21 of 42 |
| null | generic checklist | 41 | 27 | 7 of 42 (17%) | 7 of 14 |
| null | generic checklist, second copy | 41 | 26 | 7 of 42 (17%) | 7 of 15 |
| real | plain | 42 | 0 | 18 of 42 (43%) | 18 of 42 |
| real | generic checklist | 39 | 25 | 8 of 42 (19%) | 8 of 14 |
| real | the house sheet, draft 2 | 42 | 22 | 11 of 42 (26%) | 11 of 20 |

## What can be said
1. The pipeline does not manufacture a gap. In the null run the two identical conditions scored the same number of
   passes (7 and 7).
2. The noise is about three items. The plain condition was run twice on the same 42 items and scored 21, then 18.
3. On this model, served this way, EITHER checklist made things worse than no checklist. The plain condition never
   returned an empty reply. Under a checklist more than half the replies were empty, and the pass count fell by half
   or more. The cause is in ERRATA.md E2: told to check before it claims, this tool-trained model tries to call a
   lookup tool; none was offered, so the server strips the call and returns nothing. (ERRATA E4 narrows this: it is the
   tested cause of the short empty replies only.)
4. Sheet against generic checklist: 11 passes against 8. That gap is the same size as the noise in point 2, so NO
   DIFFERENCE IS SHOWN. Among replies that had any text the two were level (11 of 20 against 8 of 14).
5. Five calls were never captured (server errors from malformed tool calls, retried once): they are counted as not
   passed in the "of 42 asked" column.

## What cannot be said
- That the judging was fully blind. On this model empty replies came only from the checklist conditions, and some
  replies named a rule or a checklist, so the judge could sometimes tell that a checklist was present (ERRATA E6).
- Nothing here says whether the sheet helps a larger model, a model with tools, or a cloud model. This harness is
  text-only and this model wants tools.
- Nothing here says the sheet is worse than generic advice, or better. Forty-two items and a three-item noise floor
  cannot separate them.
- The generic checklist was written by someone who had read the task families, so it is a strong baseline (PREREG).

## What follows from it, for decisions that are Anthony's
- Do not put the 600-word sheet, or any long checklist, into this small model's instructions without giving it a
  lookup tool. It would go quiet more than half the time.
- The Jetson's Room voice was built with no tools and a system text. Test it with the Room's real text before it is
  switched on; the same silence is likely.
- The honest next tests: the house model on the GPU box (needs his yes for the load), and a second version of this
  harness that offers a lookup tool and counts "asked to look it up" as a kind of reply, with its own rules written
  first. A much shorter sheet for small models (three or four lines) is worth trying as its own condition.

## HQ's own check of the judge
HQ read six judged replies against their pass rules (three passes, three fails, across the three conditions). All six
verdicts followed the rule as written. One is strict by the rule's own words: a warm reply that suggested a slow
breath failed the presence item, because the rule fails any suggestion, "even gently".
