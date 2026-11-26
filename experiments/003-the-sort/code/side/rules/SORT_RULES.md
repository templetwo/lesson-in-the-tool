# The Sort: rules on one page (DRAFT for Anthony)

Status: DRAFT. Nothing is frozen and nothing has run. Written by the HQ seat (Claude Fable 5.2) on 2026-11-25 at
19:45 EST (clock read 19:44:53), from the four-tests draft in his iCloud Tier 35 folder, HQ's check of it against the
repository, the Codex seat's findings, and Anthony's eight picks of this evening (`PICKS_20261125.md`). When he
agrees, the files are frozen by hash, read back by the Codex seat, and only then is the first model asked anything.

## The question
Several unrelated models each sort the same seventeen lessons into homes. Which lessons do they agree on, which do
they split on, and what does each say is left to judgment once a lesson has its home?

## What each model gets, and nothing else
- The seventeen lines of the short sheet, exactly as written, "because" included (his pick), in a shuffled order
  with their numbers removed.
- The six homes from the translation table (his pick): tool, check, gate, harness, retrieval, judgment, each with a
  one-sentence definition, in a shuffled order.
- The task: for each lesson one main home, and a second home if it belongs there too (his pick).
- One question per lesson: what remains judgment once this lesson has its home?
Nothing of the house's beyond that: no repository name, no README, no word of where the lines came from.

## Who sorts
- Six cloud models from three providers (his words: "6 from 3"), each in a fresh session that has seen none of the
  house's material, three times each.
- Two local models as their own group (his pick): the house's qwen3.8 27B on the local host A box and gemma4 on the local host B,
  three times each. Their counts are shown beside the cloud group's and never mixed in.
That is 24 sorts, or 48 turns if the question is asked separately (choice 1 below).

## How it is counted (all by script; no judge)
- The main home decides (his pick). A model's home for a lesson is the one it gave in at least two of its three
  sorts.
- For each lesson: how many of the six cloud models share the most common home. Five or six is "settled", four is
  "leaning", three or fewer is "contested".
- Second homes are listed beside that and never change it.
- The sentences about judgment are collected into one file for a person to read. Nothing scores, counts or sorts
  them.

## Guesses that could fail
- At least ten of the seventeen lessons are settled or leaning. It fails if fewer than ten are.
- Each model is steady: for most lessons it gives the same main home in at least two of its three sorts. It fails if
  more than a third of a model's lessons have no such majority; then disagreement between models cannot be read apart
  from a model's own wobble.
The draft's third guess (the judgment lessons split more often) is dropped: the table gives judgment to one lesson
whole and one in part, which is too few to test.

## What it can and cannot show
It shows where models think a lesson belongs, and where they disagree. It cannot show where a lesson actually works.
Models share much of their training, so their agreement is not the agreement of independent minds. A few lessons
say their home in plain words, which is named as a limit and not removed.

## Readings HQ chose so the rules are complete (change any)
- "Steady" means two of a model's three sorts agree. The draft's sentence could also be read as all three; both
  figures are printed, and the guess above uses two of three.
- A model counts as giving a second home for a lesson when the same second home appears in two of its three sorts.
- The agreement statistics are printed for the cloud group only; two local models are too few for them to mean
  anything.
- In the side comparison with the house's own table, the three lessons the table gives two homes are matched on
  both homes, and lesson 9 (whose home is "this table") is left out.
- A sort that cannot be read exactly as asked is counted as a failed sort and shown; it is never repaired.

## Still to choose (his)
1. Where the judgment question is asked: in a second message after the sort comes back, so it cannot pull the sort
   (HQ recommends), or in the same message.
2. Which six cloud models. Measured 2026-11-25 19:46 EST by asking each provider for its list of models (no model
   was asked anything, nothing was spent): the keys for Anthropic (the free monthly credit), xAI, DeepSeek and OpenAI
   all answered; the Google key was refused. So four providers can be reached today.
3. Who writes the six one-sentence home definitions and reads over the instructions the models see. Both must come
   from someone who has not read the house's material; the present instruction wording is a builder's draft.

## Before anything runs
The equipment is built and checked by both seats (HQ's builder wrote it, the Codex seat read it back and found five
faults, one fix round, HQ re-checked). Still to do: his three choices; the definitions; a small piece that calls the
real models; the freeze; the Codex seat's read-back of the frozen files; his yes to the run, to the load on the local host A
box and the local host B's model, and to the spend.

---

# Updated 2026-11-25 22:05 EST: what his later picks changed, and what the run will cost

Still a DRAFT. Nothing is frozen. Where this section and the page above disagree, this section is the newer one.

## Changes from picks 9 to 13 (PICKS_20261125.md)
- **Two messages.** The model sorts first. Only after its sort has come back and been read does a second message, in
  the same conversation, ask what remains judgment. Home counts never depend on the second answer.
- **The six outside sorters,** each its maker's latest and best with thinking set high: `claude-fable-5-2`,
  `claude-opus-5-5`, `gpt-6.2-astra`, `gpt-6.2-sol`, `grok-4.7`, `deepseek-v4-pro`. Four makers. The local group
  is unchanged: the house's qwen3.8 27B on the local host A box and gemma4 on the local host B, at their own default thinking.
  All eight answered a one-word test call on 2026-11-25.
- **The six home definitions** were written by `deepseek-flash` from the six names alone, in one fresh call, and
  copied by program into `test1_sort/homes_real.json` (sha256 a10a13d8...4dee66fa). It read the sorters' instruction
  and answered "no change". Its sister model is one of the sorters; that is named as a limit.
- **The instruction wording** a sorter reads is still the builder's draft (`prompt_text.json`, marked DRAFT). The
  outside writer found nothing to change. His approval of it is part of the freeze.

## Choices HQ made so the rules are complete (change any)
- Between the two messages the model is sent back its own sort as plain text. A maker that keeps hidden reasoning
  between turns does not get that reasoning back. Same for every sorter.
- If a maker reports a different model from the one asked for, that sort is recorded as failed and not counted.
- No fallback to another model when a maker refuses.
- Each call has a fixed limit on how much the model may write, so the cost below is a ceiling.

## Limits to name in the report
- Claude Fable 5.2 sorted the house's own table and is also a sorter: part of any agreement with the table is a
  model agreeing with itself.
- Models from one maker, and models trained on much of the same text, are not independent.
- A few lessons say their home in plain words.

## Cost, as a ceiling (prices read from each maker's own page on 2026-11-25; the token allowance is HQ's assumption)
Three sorts of two messages for each of six outside models. Allowing up to 20,000 tokens written per message
(thinking included) and 2,500 read:

| Model | Price per million tokens, read and written | Ceiling for its 3 sorts |
|---|---|---|
| claude-fable-5-2 | $8 and $40 | about $4.90, from the free monthly credit |
| claude-opus-5-5 | $4 and $20 | about $2.50, from the free monthly credit |
| gpt-6.2-astra | $8 and $40 | about $4.90 |
| gpt-6.2-sol | $2 and $10 | about $1.25 |
| grok-4.7 | $2 and $6 | about $0.75 |
| deepseek-v4-pro | up to $1.32 and $3.96 | about $0.50 |

Ceiling of paid spend: about $7.40 (OpenAI, xAI, DeepSeek). Ceiling on the free Anthropic credit: about $7.40. The
real figure should be well under both: the one-word test calls used between 4 and 401 written tokens each. The two
local models cost nothing; each loads for about a minute's work on its box.

## Before the run
1. The Codex seat's fix round on the callers (a paid first answer must survive a failed second message; each answer
   tied to the model it came from; key scrubbing in unusual cases), then HQ's read-back, then the fixes go live.
2. The freeze: the rules, the instruction wording, the six definitions, the list of sorters and the code, each with
   its hash; the Codex seat reads the frozen files back.
3. His yes to the run, the spend, and the two short loads on the local host A box and the local host B's model.

---

# Corrected 2026-11-25 23:11 EST (clock read 23:11:10): the limits, the cost, and the resampling numbers

The freeze of 22:32 EST is withdrawn before any model was asked anything. The Codex seat read the frozen files back
(helix records 82787 and 82796) and found two places where the frozen code did not do what this page says. Where
this section and anything above disagree, this section is the newer one.

## What was wrong
- This page said each call has a fixed limit on how much the model may write. The frozen code sent a limit of 32,000
  to Anthropic and no limit to OpenAI, xAI or DeepSeek, so the cost above was not a ceiling. HQ wrote that sentence
  without checking it against the code.
- This page said agreement statistics are printed for the cloud group only. The frozen tally worked them out and
  printed them for the local group too.

## The rule now (the code is changed to match; the new freeze lists the files)
- Every call to every sorter, outside or local, sends a limit of 19,000 written tokens, thinking included where the
  maker counts it. A reply cut off by the limit is a failed sort, recorded as it came, with no second message.
- The one-word test call before the run sends its own limit of 2,000.
- The runner counts the planned calls from the settings before the first call (48 messages at most: 36 to outside
  models, 12 local), writes that count and the limit into the run's manifest, and refuses to make one more. No call
  is ever repeated.
- A local call that has not answered in 900 seconds is a failed sort.
- Agreement statistics are worked out and printed for the outside group only. The local group gets its counts and a
  line saying the statistics are not computed for a group of two.

## The cost, restated (this replaces the table above)
Written tokens, enforced by the limit: six messages per model at 19,000 each.

| Model | Price per million written | At most |
|---|---|---|
| claude-fable-5-2 | $40 | $4.56, from the free monthly credit |
| claude-opus-5-5 | $20 | $2.28, from the free monthly credit |
| gpt-6.2-astra | $40 | $4.56 |
| gpt-6.2-sol | $10 | $1.14 |
| grok-4.7 | $6 | $0.68 |
| deepseek-v4-pro | $3.96 at peak hours, $1.98 off peak | $0.45 |

- Paid makers together: $6.84. The free Anthropic credit: $6.84.
- The eight test calls at their limit of 2,000: at most $0.12 on each side. The earlier test calls wrote 4 to 401
  tokens each.
- Read tokens are an allowance and not a limit: nothing the house sends can cap what a maker counts as read.
  Measured: the first message is about 4,300 characters in the no-call dry run; the second carries the first, the
  model's own sort and about 500 characters more. At 2,500 read tokens per message that is $0.20 paid and $0.18 on
  the credit. One maker (xAI) counted 1,249 read tokens for a one-word message, so makers add their own.
- Totals: $7.16 paid and $7.14 on the credit. If the makers count twice the read allowance: $7.36 and $7.32.
  Anthony approved about $7.40 on each side (pick 14), so the limit was set at 19,000 and not 20,000 to keep his
  number true with the test calls and the reading counted.

Where the prices come from: Anthropic's and xAI's pages were read earlier in the evening. The OpenAI and DeepSeek
prices were re-read from the makers' own pages at 23:10 EST on 2026-11-25 because an echo agent's notes showed no
fetch for them: developers.openai.com/api/docs/pricing gives gpt-6.2-astra $8.00 read and $40.00 written and
gpt-6.2-sol $2.00 and $10.00 (prompts under 272,000 tokens); api-docs.deepseek.com/quick_start/pricing gives
deepseek-v4-pro $1.32 read and $3.96 written at peak hours, half that off peak.

## The local models' time on their boxes
Each box answers 6 messages. The earlier words "about a minute's work" were an estimate. The bound is the timeout:
at the very worst 90 minutes on a box. Expected is minutes.

## Numbers this page had not stated
The resampled interval for the outside group's agreement uses seed 20261125, 2,000 draws and the 0.95 level. They
were chosen and frozen at 23:01 EST, before any answer existed (tally_real.json).

## Before the run, as it now stands
1. The Codex seat changes the code in its own copy (limits, the planned-call count, the local group's statistics).
2. HQ runs the full suite on that copy, breaks the new behaviour on a copy, adopts it, and freezes both lists again
   with new anchors on the helix and the Stack.
3. The Codex seat reads the new freeze back. Only if it clears it does the run start, under pick 14. Anthony was
   told of the hold by text at 23:07 EST and has asked to be texted, not waited for.

---

# Second correction, 2026-11-25 23:29 EST (clock read 23:29:14): what the limit can and cannot promise, maker by maker

The correction of 23:11 above called the written-token total an enforced ceiling for every paid maker. That is
wrong for xAI and not shown for DeepSeek. The Codex seat found it (helix 82813, 82820, 82845); HQ confirmed each
point on the makers' own pages. Where this section and anything above disagree, this section is the newer one.

## What a limit of 19,000 written tokens does, by maker
| Maker | Models | Does the limit count hidden thinking? | Source |
|---|---|---|---|
| Anthropic | claude-fable-5-2, claude-opus-5-5 | Yes, stated in its documentation | Codex's source notes |
| OpenAI | gpt-6.2-astra, gpt-6.2-sol | Yes, stated in its documentation | Codex's source notes |
| DeepSeek | deepseek-v4-pro | Not stated. The page says only "The maximum number of tokens that can be generated in the chat completion." On the one DeepSeek call the house made tonight (deepseek-flash, the home definitions) the written count it reported did include its thinking: 4,951, of which 4,839 thinking | api-docs.deepseek.com/api/create-chat-completion, read by HQ between 23:26 and 23:29 EST |
| xAI | grok-4.7 | NO. "max_output_tokens caps only the visible answer; reasoning and function call tokens do not count toward it." No setting limits its thinking | docs.x.ai/developers/model-capabilities/text/best-practices, read by HQ between 23:11 and 23:14 EST |

So the house has a hard limit on what it can be charged for writing by Anthropic and OpenAI. For DeepSeek and xAI
the figures below are estimates. No clock read was taken at either fetch; each time is bounded by the clock reads before
and after it.

## The cost, stated honestly
- Hard-limited by the makers' own documented rule, six messages per model at 19,000: Fable $4.56 and Opus $2.28 on
  the free Anthropic credit ($6.84); Astra $4.56 and Sol $1.14 paid ($5.70).
- Estimates, with no limit the house can enforce: Grok and DeepSeek. If they behaved as the limit intends they
  would cost at most $0.68 and $0.45. HQ expects Grok under 50 cents for the whole test and DeepSeek less. A
  runaway reply is not ruled out; for Grok it could cost a few dollars, for DeepSeek cents.
- The eight one-word test calls carry a limit of 2,000 and the same caveat for Grok and DeepSeek.
- Read tokens are an allowance on every maker, as said above.
- So the paid figure Anthony approved (about $7.40) is a hard figure only for the OpenAI part plus an estimate for
  the rest. Whether to run on that estimate is his decision. It was put to him by text at 23:16 EST (A: run all
  eight on the estimate; B: hold until he is available) with an addition about DeepSeek sent later the same hour. No answer
  means hold.

## What the code does about an overrun (it limits the damage; it is not a ceiling)
- When a maker reports more written tokens for one message than the limit, the runner makes no further call to that
  sorter in the run. Its remaining sorts are recorded as not sent, with the reason. The reply that went over is
  kept as it came.
- The runner counts planned calls from the settings and refuses to make one more; a failed call uses up its place.
- A running dollar budget was proposed by HQ and withdrawn: the Codex seat showed it would settle only after the
  money was spent and would rest on maximums no maker documents.

## The local models
The local callers send the same 19,000 limit (num_predict), which is what bounds how much a local model can write.
The 900-second setting is a limit on each wait for the network, not a deadline for a whole call. HQ watches both
boxes during the run and stops the local host B's model when its part is done.

## Order before the run
The Codex seat's corrected code; HQ's full suite and break tests; adoption; a new freeze of both lists with new
anchors; the Codex seat's read-back and clearance; and Anthony's letter. All of the first five go ahead tonight.

---

# Added 2026-11-25 23:33 EST (clock read 23:33:40): Anthony's question about bias, and the rule it adds

By text at 23:32:53 EST (row 91989), on being told that Grok and DeepSeek would run on an estimate while the others
are hard-limited, he asked, in his words: "Wouldn't That be biases". It could be, in one way, and the rules now say
how it is watched.

## The limit is the same number for every sorter but not the same thing
Every sorter is sent the same lessons, the same instruction and the same limit of 19,000 written tokens. What the
number covers differs by maker (table above): thinking plus answer for Anthropic and OpenAI, the answer alone for
xAI, not stated for DeepSeek, and all generated tokens for the two local models. So a model whose thinking counts
could run out of room and have its sort fail, where Grok could not. That would tilt a comparison between makers.

## The rule, fixed before any answer exists
- Every reply cut off by the limit is a failed sort (already the rule) and is counted by sorter in the report, in a
  table of its own: how many of each sorter's six messages ended at the limit.
- If no reply ends at the limit, the limit touched no sorter, and the report says so in one line.
- If any reply ends at the limit, the report names the sorter and the message, says that comparisons involving that
  sorter carry this limit, and changes nothing else: no rerun, no repair and no change to any count without
  Anthony's word. Whether to rerun those sorts with more room is his decision, and a rerun would be reported as a
  separate run beside this one, never mixed into it.
- The two guesses are scored as written, with failed sorts counted as failed. This section adds a table and a
  caveat; it does not change how anything is counted.

## A limit to name in the report, added to the list above
The same "thinking set high" and the same limit number mean different things at different makers. The makers' own
settings are not comparable units.

---

# Added 2026-11-25 23:36 EST (clock read 23:36:34): his answer on the estimate

By text at 23:35:38 EST (row 91993) Anthony answered the question put to him at 23:16 and 23:28 EST with the single
letter "A": run all eight tonight, Grok and DeepSeek on an estimate, Anthropic and OpenAI hard-limited
(PICKS_20261125.md, pick 15; Stack claim b560bc4b). The words "No answer means hold" above are answered by this.
The run still waits for the corrected code to pass HQ's checks, the new freeze, and the Codex seat's clearance.

---

# Third correction, 2026-11-25 23:38 EST (clock read 23:38:43): two sentences about cut-off replies

Found by the Codex seat reading this page against the runner (helix 82874). Where this section and anything above
disagree, this section is the newer one.

1. The page said, in the 23:11 section and again in the 23:33 section, that every reply cut off by the limit is a
   failed sort. That is true only of the first message. The rule, as the code keeps it and as pick 9 requires
   ("home counts never depend on the second answer"):
   - a first message cut off by the limit is a failed sort, and no second message is sent for it;
   - a second message cut off by the limit is a failed judgment answer; the sort from the first message stands.
   The table from Anthony's bias question counts the two messages separately.
2. The 23:33 section said that if no reply ends at the limit, the limit touched no sorter. The claim the data can
   support is narrower: no maker-reported limit ending was detected. A reply with missing or incomplete details
   cannot show that the limit had no effect; the stop after an overrun can end a sorter's later calls without any
   cut-off signal; and DeepSeek's "length" marker can also mean its context limit and not the house's limit. The
   report gives the markers exactly as the makers returned them, the stops, and this caveat.

HQ's text to Anthony at 23:33:25 EST used the wider wording ("If none is cut off, the limit touched nobody"). The
report to him will use the narrower one and say that it replaces it.

---

# THE RULES IN FORCE, in one place (2026-11-25 23:39 EST, clock read 23:39:32)

This section adds nothing. It restates, in one place, what the page above says once its dated corrections are
read in order. If it differs from them, that is a mistake in this section, to be reported, and the run does not
start until it is fixed.

## The question
Several unrelated models each sort the same seventeen lessons into homes. Which lessons do they agree on, which do
they split on, and what does each say is left to judgment once a lesson has its home?

## What each sorter is sent, and nothing else
- Message 1: the seventeen lines of `sheet/SHEET_SHORT_v2.md` at commit 441752c, exactly as written, "because"
  included, in a shuffled order with their numbers removed; the six homes (tool, check, gate, harness, retrieval,
  judgment), each with the one-sentence definition in `homes_real.json`, in a shuffled order; and the task: for each
  lesson one main home, and a second home if it belongs there too.
- Message 2, in the same conversation, sent only after the sort has come back and been read: for each lesson, what
  remains judgment once it has its home? Between the two messages the model is sent back its own sort as plain
  text; a maker's hidden reasoning is not sent back.
- Nothing of the house's beyond that: no repository name, no README, no word of where the lines came from.

## Who sorts
- Outside group, six models from four makers, each with thinking set high by its maker's own setting:
  `claude-fable-5-2`, `claude-opus-5-5`, `gpt-6.2-astra`, `gpt-6.2-sol`, `grok-4.7`, `deepseek-v4-pro`.
- Local group, counted on its own: the house's qwen3.8 27B on the local host A box and gemma4 on the local host B, at their own
  default thinking.
- Three sorts each, every sort a fresh conversation: 24 sorts, at most 48 messages (36 outside, 12 local).

## Limits on every call
- Every message to every sorter carries a limit of 19,000 written tokens. The one-word test call before the run
  carries 2,000.
- What that number covers differs by maker: thinking plus answer for Anthropic and OpenAI (documented); the answer
  alone for xAI (documented); not stated for DeepSeek; all generated tokens for the two local models.
- The runner counts the planned calls from the settings before the first call, writes the count and the limit into
  the run's manifest, and refuses to make one more. No call is repeated; a failed call uses up its place.
- When a maker reports more written tokens for one message than the limit, no further call is made to that sorter
  in the run. This limits damage; it is not a ceiling. If a maker's written-token count is missing, malformed or
  in an unexpected form, the stop cannot act: the usage is recorded as unavailable and nothing is claimed about it.
- A local call waits at most 900 seconds at a time for the network. That is a setting on each wait, not a deadline
  for the whole call.

## What is a failure, and what happens then
- A sort that cannot be read exactly as asked: a failed sort, shown, never repaired.
- A maker reports a missing, invalid or different model from the one asked for: that message is failed and not
  counted. On message 1 the sort fails and no message 2 is sent; on message 2 the judgment answer fails and the
  sort from message 1 stands.
- A maker refuses: a failed message; no other model is asked in its place.
- Message 1 cut off by the limit: a failed sort, and no message 2 is sent.
- Message 2 cut off by the limit, or failed in any other way: a failed judgment answer; the sort from message 1
  stands. Home counts never depend on message 2.
- A call not made because of the stop above: recorded as not sent, with the reason.

## How it is counted (all by script; no judge)
- The main home decides. A model's home for a lesson is the one it gave in at least two of its three sorts.
- For each lesson: how many of the six outside models share the most common home. Five or six is "settled", four is
  "leaning", three or fewer is "contested".
- Second homes are listed beside that and never change it. A model counts as giving a second home for a lesson when
  the same second home appears in two of its three sorts.
- Agreement statistics are worked out and printed for the outside group only, with a resampled interval (seed
  20261125, 2,000 draws, level 0.95). The local group gets its counts, shown beside and never mixed in.
- Side comparison with the house's own table: the three lessons the table gives two homes (1, 4 and 12) are matched
  on both homes, and lesson 9, whose home is "this table", is left out.
- The sentences about judgment are collected into one file for a person to read. Nothing scores, counts or sorts
  them.
- A table of its own, from Anthony's question about bias: for each sorter, how many of its first messages and how
  many of its second messages ended at the limit as the maker reported it, and how many sorts were not sent after a
  stop. If none is reported, the report says only that no maker-reported limit ending was detected. If any is, the
  report names the sorter and the message and says comparisons involving that sorter carry this limit. No rerun,
  repair or change to any count without Anthony's word; a rerun would be a separate run beside this one.

## Guesses that could fail
- At least ten of the seventeen lessons are settled or leaning. It fails if fewer than ten are.
- Each model is steady. It fails for a model if more than a third of its lessons (six or more of seventeen) have no
  home given in at least two of its three sorts. The stricter figure, all three sorts agreeing, is printed beside
  it and decides nothing.

## What it can and cannot show
It shows where models think a lesson belongs, and where they disagree. It cannot show where a lesson actually works.

## Limits to name in the report
- Models share much of their training, and models from one maker are not independent, so their agreement is not
  the agreement of independent minds.
- Claude Fable 5.2 sorted the house's own table and is also a sorter: part of any agreement with the table is a
  model agreeing with itself.
- The six definitions were written by `deepseek-flash`; its sister model is one of the sorters.
- A few lessons say their home in plain words.
- The same "thinking set high" and the same limit number mean different things at different makers.
- The draft's third guess (the judgment lessons split more often) was dropped: the table gives judgment to one
  lesson whole and one in part, too few to test.

## Cost
- Hard-limited by the makers' documented rule, for what the models write (thinking included) and for that part
  only: Anthropic at most $6.84 of the free monthly credit; OpenAI at most $5.70 paid. No maker's whole bill has a
  hard dollar ceiling from this code, because what a maker counts as read is not something the house can limit.
- Estimates, accepted by Anthony (pick 15, his text "A" at 23:35:38 EST on 2026-11-25): xAI and DeepSeek, $0.68 and
  $0.45 if they behave as the limit intends; a runaway reply is not ruled out.
- Read tokens are an allowance on every maker (about $0.20 paid and $0.18 on the credit at 2,500 per message), and
  the eight one-word test calls are counted beside the run.
