# The Sort, side run for DeepSeek: the rules

Written by the HQ seat (Claude Fable 5.2) at 2026-11-26 11:14:08 EST, replacing the draft of 10:47 EST after
the Codex seat (gpt-6-astra) read that draft against the code and corrected it in ten places (its read-back:
`test2_stale/scratch/codex_side_limit/SIDE_RULES_READBACK.md`, sha256 5b89617a...400e04d5). Nothing has run. This
page is frozen with the side run's code and settings before any call.

## What kind of run this is
AN EXPLORATORY, DESCRIPTIVE FOLLOW-UP SELECTED AFTER RUN 1, WITH ITS OWN PROSPECTIVE ANALYSIS PLAN.
Choosing DeepSeek, the larger requested limit and the lessons to highlight was done after run 1's result was seen;
all of that is post hoc relative to run 1. Freezing this plan before the side run's own data exists makes the
side analysis prospective. It does not turn the side run into part of the plan registered before run 1, and it is
not a confirmatory test of anything. Nothing here is added to run 1's frozen rules. The report must carry this
label too, not only this page.
Authority: Anthony's pick 16, by text at 10:45:48 EST on 2026-11-26 ("1. A."): a side run of DeepSeek with more
room, reported next to run 1 and never mixed into it, at about 1.50 dollars at the very most if its limit behaves
as it did, frozen and read back first. He then asked, at 10:48:01 EST, "All this needs to be added to the
preregistration right?"; this page is the dated addendum that answer promised.

## Why
In run 1 (2026-11-25 23:56 to 2026-11-26 00:29 EST) two of deepseek-v4-pro's three first messages ended at the
requested limit of 19,000 written tokens with all reported completion tokens attributed to reasoning and no
final-answer text. It had the only maker-reported limit endings in run 1, so it has no two-of-three majority home
on any lesson there.

## What is the same as run 1
The seventeen lessons of `sheet/SHEET_SHORT_v2.md` at commit 441752c; the six definitions (`homes_real.json`); the
instruction wording (`prompt_text.json`); two messages a sort; three sorts; thinking set high by the maker's own
setting; the model must report itself as the one asked for; no call repeated and no other model in its place; and
every failure rule of run 1's rules in force.

## What is different
- Only deepseek-v4-pro sorts, as a group of one named "side".
- Main calls REQUEST a limit of 60,000 written tokens, where run 1 requested 19,000. The one-word test call
  requests 2,000 and goes to DeepSeek only. The code accepts a whole number from 1 to 60,000 for a run's limit;
  with the setting absent it is 19,000, as in run 1.
- The shuffles are NEW. The runner draws its seeds in roster order, so a one-model run cannot reproduce the orders
  DeepSeek saw as the sixth of eight. This run uses its own master seed, 20261127, and its three lesson orders,
  three home orders and first-prompt hashes differ from run 1's. The report records the prompt hashes actually
  sent; it does not claim they equal run 1's. Because the shuffles change as well as the limit, this run does not
  isolate the effect of the limit.
- Run 1 is read, never written: its settings, results and tally are untouched and live in another folder.

## What a requested limit does and does not mean
The request is permitted by the maker's API reference. That is not evidence that a reply will finish, that the
maker enforces the number in a particular way, or that its accounting matches another maker's. The limit-ending
table reports the maker's own markers; it does not infer one from a token count. The stop after an overrun checks
the run's limit and stops later calls only after an overrun has been reported; it cannot prevent the overrun, and
missing usage figures establish nothing.

## Calls
One main run reserves at most six attempts and one test run reserves one. A failed attempt uses up its place and is
not retried. These counters work inside one run; they do not stop a person starting another. The governing rule
is: no additional run beyond these three planned sorts without Anthony's word.

## Cost, as an estimate with its condition
If the limit behaves as it did in run 1's two cut-off calls: six main calls at 60,000 written tokens at the
maker's peak-hour price of 3.96 dollars a million come to 1.4256 dollars, and the test call adds 0.00792, so
1.43352 dollars before read tokens. Allowing 2,500 read tokens for each of the seven requests at 1.32 dollars a
million adds 0.0231, giving 1.45662. The read allowance is an assumption. None of this is a ceiling the program
enforces on a whole bill, and no invoice will have been inspected.

## What counts as a failure
A first-message limit ending fails that sort. A second-message limit ending fails the judgment answer while the
valid first-message sort remains. Failed sorts, and sorts not sent after a stop, stay in the three-repeat
denominator. A home for a lesson still needs at least two matching readable sorts.

## What is reported, all of it description
1. From the tally, for the one model: how many of its three sorts are readable; its majority home for each lesson
   and the lessons with none; maker-reported limit endings by message and sorts not sent after a stop; its
   judgment sentences collected for a person to read. No classes, no agreement figure, no resampled interval, and
   no comparison with the house's own table. The three replies are three repeats of one model, never three models.
2. From the comparison script, which reads only the two tally files and pins run 1's by its hash
   (78879c80560cde940027808742c04c75e921372b1a953297bcfd42e317dada5f): for each of the seventeen lessons, the side
   run's majority home against run 1's outside-group modal home, as match, different or missing, with all
   seventeen kept in the denominator and missing majorities shown apart from differing homes. Run 1's classes are
   copied as labels only, to mark its contested lessons (1 and 4) and leaning ones (11 and 15).
3. The maker's token counters for each message stay in the saved call records. Any table of them in the report is
   HQ's reading of those records, named as such.

## What is never done
- The side run's sorts are not counted into run 1's classes, modal counts, agreement figure or guesses, and they do
  not replace run 1's DeepSeek rows.
- No class, agreement statistic or new guess is produced for the side run, and neither of run 1's guesses is scored
  again.
- gemma4's two failed sorts in run 1 stay failed (pick 17).

## What it cannot show
What run 1 "would have been". The side run comes later, with new shuffles and a larger requested limit; the other
five outside models received 19,000 and reported no limit ending in run 1. It shows DeepSeek's responses and
two-of-three majorities under the higher requested limit, including any further failures. It does not explain the
amount or the quality of its reasoning.

## The files and the order
Code: the run-1 code plus three changes made by the Codex seat and checked by HQ (a run may name its limit; the
tally describes a group of one; `side_compare.py`). Settings: `config_side_deepseek.json`,
`tally_side_deepseek.json`, `compare_side_deepseek.json`. Order: freeze the code, settings and this page with a new
anchor; the Codex seat reads the freeze and this page against the code and clears it or not; the test call; the
run into `real_runs/side_1`; the key search; the tally; the comparison; the report beside run 1's, read back by the
Codex seat.
