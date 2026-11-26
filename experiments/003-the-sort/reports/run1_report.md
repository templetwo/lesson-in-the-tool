# The Sort (Tier 35, test 1), run 1: what came back (second version, with three wording fixes of 00:52 EST)

> Prepared public edition of a checked report. Original report SHA256: `8742dddf4a1fe3303767a7319ff931971a1183242800910f987046c1654dfcf0`. Historical hashes below identify original private artifacts, not these rewritten public files.
> The report records its original reporting date; historical decision lists are source context, not new requests.
> The [public summary](../results/run1_tally.json), [public record](../records/run1/) and
> [companion report](side_report.md) are included. The public record projects sent prompts, label maps,
> visible answers, judgment prose and analysis metadata, excluding provider reasoning and private identifiers.
> Offline reconstruction of the public analysis passed within the [documented scope](../README.md#public-edition-and-reconstruction).
> Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.
> This publication edition follows Anthony's direction to make the work open before his own folder review. See [public-edition notes](../PUBLIC_EDITION_NOTES.md).

Written by the HQ seat (Claude Fable 5.2) at 2026-11-26 00:46:16 EST. This version replaces the one of
00:33:05 EST (kept as a private superseded report, sha256 05be1ad2...550436a) after the Codex seat
(gpt-6-astra) read that version against the data and found sixteen places where it said more than the data does
(private independent readback, original SHA256 59453d3a...0b967212). No run, result or count changed. The Codex seat rebuilt every majority, class, agreement
figure and house-table count from the 20 readable sorts on its own and they match the tally.

Where each kind of figure comes from:
- homes, classes, stability, agreement and the house-table comparison: the frozen tally,
  the original run-1 tally (sha256 78879c80...17dada5f);
- tokens and charges: what each maker reported in its replies, as saved in the run folder;
- cost: HQ's arithmetic at list prices, named as such, with xAI's own reported charge beside it;
- the boxes, the shutdown and the key search: HQ's own receipts and account, which the Codex seat read but did not
  repeat.

## The run
- 2026-11-25 23:56:36 to 2026-11-26 00:28:57 EST, one run, the original run-1 configuration, exit 0. Both freeze anchors verified
  before the run and again before the count (62739620...b914c22d and 5bce8ba7...fc132c09).
- 24 first messages and 20 second messages were sent, 44 of the 48 planned; four second messages were not sent
  because the first had failed. No call was repeated.
- 20 of 24 sorts could be read as asked. All 20 judgment answers that were asked for came back readable.

## Guess 1: at least ten of seventeen lessons settled or leaning. IT HELD: 15 of 17.
13 settled, 2 leaning, 2 contested (lessons 1 and 4). To read beside it: DeepSeek produced one readable sort, so it
has no two-of-three majority home on any lesson and gives the outside group no majority votes. That limits the
group's modal counts to at most five; Opus has no majority home on lesson 4, which leaves four available there. On
the 13 settled lessons the other five models' majority homes agree; that is not a statement that every one of their
repeats agrees. The denominators stay as frozen: six outside models.

## Guess 2: each model is steady. IT DID NOT HOLD.
The criterion (fails at six or more lessons with no home in two of three sorts) passed for six models and failed
for two, so the guess, which is about all eight, did not hold. DeepSeek and gemma4 each had two failed sorts, which
makes a two-of-three majority impossible. That is the scoring mechanism; it does not show that either model
disagrees with itself, and it does not show that they would agree if the failed answers could be recovered.

| Model | Sorts that failed | Lessons with no two-of-three home | Lessons without three identical valid repeats (failed repeats included) | Criterion |
|---|---|---|---|---|
| claude-fable-5-2 | 0 | 0 of 17 | 1 | passed |
| claude-opus-5-5 | 0 | 1 of 17 | 2 | passed |
| gpt-6.2-astra | 0 | 0 of 17 | 0 | passed |
| gpt-6.2-sol | 0 | 0 of 17 | 1 | passed |
| grok-4.7 | 0 | 0 of 17 | 1 | passed |
| deepseek-v4-pro | 2 of 3 | 17 of 17 | 17 | FAILED |
| the house model, qwen3.8 27B (local) | 0 | 0 of 17 | 4 | passed |
| gemma4 (local) | 2 of 3 | 17 of 17 | 17 | FAILED |

Only Opus on lesson 4 gave three different readable homes (check, harness, tool).
- **deepseek-v4-pro:** repeats 1 and 3 asked for a limit of 19,000, reported 19,000 completion tokens and 19,000
  reasoning tokens, returned no final-answer text and ended with `length` (the saved replies do hold its
  reasoning text, 83,250 and 84,410 characters; the answer field is empty). These two calls ended at the requested limit with
  all reported completion tokens attributed to reasoning. That strongly supports reading the limit as counting
  thinking in these calls; it does not settle how this maker behaves in general, and its `length` marker can also
  mean a context limit. Repeat 2 was readable: 15,608 completion tokens, 15,421 of them reasoning.
- **gemma4:** two of its three sorts left out the words "main:" and "second:" that the reply format asks for (it
  wrote `L01 | check | none`). A person can read them; the rule says a sort not written exactly as asked is failed
  and never repaired, so they are failed. The saved counts and stop statuses show no sign of its context running
  out (largest prompt plus reply 3,365 tokens of 8,192; every call finished with reason "stop"). That does not
  establish that the context setting played no part in the format slips. The GPU host's largest was 4,919 of 32,768,
  with the same boundary on what that shows.

## The table from Anthony's question about bias
Maker-reported limit endings: DeepSeek, 2 first messages. Every other sorter, 0 on both messages. No sorter was
stopped for an overrun.
DeepSeek had the only maker-reported limit endings in this run, and it reported the largest first-turn
reasoning-token counts in this run. This is the kind of outcome his question was about ("Wouldn't That be biases",
23:32:53 EST): one requested limit number, with two reported limit endings for DeepSeek and none reported for
other sorters. **Every comparison
involving DeepSeek carries this limit.** By the rule fixed before the run, nothing is rerun or repaired without his
word; a rerun of DeepSeek with more room would be a separate run reported beside this one.
The narrower wording applies: no other limit ending was REPORTED. That is not proof the limit affected no one
else. Token counts are each maker's own accounting, not a calibrated measure of how much or how well a model
thinks.

## Agreement among the outside group
Agreement among the available outside-model majority homes: Krippendorff's alpha 0.83, 95% percentile interval 0.57
to 0.97 from 2,000 resamples of the lessons. It uses 84 available majority ratings of the 102 planned: DeepSeek has
none and Opus lacks lesson 4. Missing majorities are left out, so this does not estimate agreement with DeepSeek.
The interval resamples lessons given the models and gaps observed; it does not resample models or failed
collection. Fleiss' kappa is not computed because majorities are missing.

## Where the lessons went
| Lesson | House's own table | Outside group's modal home (of the majority homes) | Class | Fable Opus Astra Sol Grok DeepSeek | The local house model's majority home |
|---|---|---|---|---|---|
| 1 | check + judgment | check, 3 of 6 | contested | che che gat gat che --- | check |
| 2 | tool | judgment, 5 of 6 | settled | jud jud jud jud jud --- | check |
| 3 | tool | check, 5 of 6 | settled | che che che che che --- | check |
| 4 | tool + check | check, 3 of 6 | contested | har --- che che che --- | check |
| 5 | gate | gate, 5 of 6 | settled | gat gat gat gat gat --- | gate |
| 6 | harness | check, 5 of 6 | settled | che che che che che --- | check |
| 7 | tool | check, 5 of 6 | settled | che che che che che --- | check |
| 8 | retrieval | check, 5 of 6 | settled | che che che che che --- | check |
| 9 | (this table) | harness, 5 of 6 | settled | har har har har har --- | harness |
| 10 | tool | check, 5 of 6 | settled | che che che che che --- | check |
| 11 | tool | check, 4 of 6 | leaning | che ret che che che --- | retrieval |
| 12 | tool + check | tool, 5 of 6 | settled | too too too too too --- | tool |
| 13 | retrieval | check, 5 of 6 | settled | che che che che che --- | check |
| 14 | check | judgment, 5 of 6 | settled | jud jud jud jud jud --- | judgment |
| 15 | check | check, 4 of 6 | leaning | che jud che che che --- | judgment |
| 16 | harness | check, 5 of 6 | settled | che che che che che --- | check |
| 17 | judgment | judgment, 5 of 6 | settled | jud jud jud jud jud --- | judgment |

The outside group's modal homes were check on 11 lessons, judgment on three, and gate, harness and tool on one
each. Retrieval was never the group's modal home; Opus chose retrieval for lesson 11 in all three of its sorts.

Side comparison with the house's own table (exploratory, decides nothing): the group's modal home is the table's
main home on 5 of the 16 lessons compared (1, 5, 12, 15, 17). Sorter by sorter, of the 96 planned
sorter-by-lesson cells, 4 match the table exactly and 35 share a home; only 79 of those cells have a model majority,
and a missing majority counts as no match under the fixed rule. Exact matches by sorter: Fable, Opus, Astra and Sol
1 of 16 each; Grok and DeepSeek 0 of 16. The table has tool as main home on seven lessons; the group's modal home
was tool on one. This exploratory exact-match measure does not isolate an authorship effect, so the caveat that
Claude Fable 5.2 both wrote the table and sorted here stands as it was.
The local house model's majority home matched the outside group's modal home on 14 of 17 lessons. For the local
group the table comparison is 1 of 32 exact and 10 of 32 sharing a home, a separate count never added to the other.

What this can and cannot show, as frozen: it shows where models think a lesson belongs and where they disagree. It
cannot show where a lesson actually works. One possible explanation for so many lessons landing in "check" is the
relationship between the lessons' wording and the check definition the sorters were given; this run did not test
that explanation.

## "Thinking set high" was not one thing
First-message tokens as each maker reported them. These are the makers' own counters and are not comparable
units; a high effort setting does not guarantee thinking on every request.
| Model | First message, written tokens | Of which thinking, as reported |
|---|---|---|
| claude-opus-5-5 | 233 to 238 | 0 |
| gpt-6.2-astra | 493 to 674 | 301 to 482 |
| gpt-6.2-sol | 708 to 1,027 | 516 to 835 |
| claude-fable-5-2 | 1,087 to 1,175 | 859 to 947 |
| gemma4 (local) | 1,387 to 2,295 | not reported separately |
| the house model (local) | 3,004 to 3,853 | not reported separately |
| grok-4.7 | 8,384 to 11,149 | 8,198 to 10,963 |
| deepseek-v4-pro | 15,608 to 19,000 | 15,421 to 19,000 |

## An accounting pattern at xAI, unresolved
The house sent every maker three plain text messages for the second turn: the task, the model's visible first
reply, the question. It sent no response id and no reasoning item. Grok's second-turn reported input equals 2,550
plus its preceding reasoning-token count in all three repetitions (10,748, 13,513 and 11,126 against reasoning of
8,198, 10,963 and 8,576). The other outside second-turn inputs range from 1,312 to 1,796. The saved replies show
`store` true and no previous response id. The saved records do not establish whether this reflects context the
model had, a reconstruction, or usage accounting; the cause remains unresolved. It concerns the second message
only; the home counts come from the first.

## The judgment answers
The original judgment-answer compilation (sha256 14902a2a...49673d14). Collected for a person to
read. Nothing scored, counted or sorted them, and HQ has not summarised them.

## Reported usage and estimated cost
No account invoice was inspected. At list prices from the makers' pages, applied to the reported tokens:
| Model | Estimate for the run |
|---|---|
| claude-fable-5-2 | $0.36, free monthly credit |
| claude-opus-5-5 | $0.13, free monthly credit |
| gpt-6.2-astra | $0.21 |
| gpt-6.2-sol | $0.06 |
| grok-4.7 | $0.32 before discounts |
| deepseek-v4-pro | $0.24 at its peak-hour price |

That is about $0.49 on the Anthropic credit and about $0.83 on the paid makers by this estimate. xAI's own cost
field for its six calls sums to 3,090,580,000 ticks; its documentation defines 10,000,000,000 ticks to the dollar,
charged amount after discounts, so xAI reports $0.31 for Grok. The eight one-word test calls before the run add
about half a cent in all. Grok's largest message was 11,149 written tokens.
About $7.40 a side was the planning figure he approved. The documented output-only bounds were $6.84 for Anthropic
and $5.70 for OpenAI, with accepted estimates for xAI and DeepSeek. No whole bill had a hard dollar ceiling.

## The boxes and the keys (HQ's receipts and account)
- GPU host: 126 sampled card readings (63 samples of two cards, about 30 seconds apart) between 25 and 76 degrees;
  a sample, not a continuous record. The house model was given 32,768 tokens of context.
- Other local host: HQ started its model server at 23:55:13 for the run and stopped it at 00:29:25; HQ then read the port as
  closed and both login entries as disabled.
- Keys: the saved search receipt reports 412 files, no match for any of the four keys or their 8-character pieces,
  and the planted control found (private saved scan receipt).

## Decisions that are Anthony's
A. Rerun DeepSeek's sorts with more room, as a separate run beside this one, or leave run 1 as the record with
   DeepSeek's limit named.
B. Whether anything should be done about gemma4's two sorts (HQ's view: nothing; the rule was fixed before the run).
C. Whether and where this result is registered, and whether any of it goes to the public repository.

## Limits, as frozen, plus what the run added
As frozen: shared training and shared makers; Fable as table author and sorter; the definition writer's sister
model among the sorters; a few lessons naming their home; the makers' settings not being comparable units; the
local context windows being set by the boxes. Added by the run: DeepSeek contributes no outside majority votes,
limiting the group's modal counts to at most five, and Opus's missing majority on lesson 4 leaves four available
there; DeepSeek had the only maker-reported limit endings; gemma4's two format failures; the unresolved xAI
input-accounting pattern.

## What the first version got wrong (HQ's, found by the Codex seat)
1. It said Anthropic did not report thinking separately. It does (`thinking_tokens`): Opus 0, Fable 859 to 947.
   HQ's script looked for one field name only.
2. It said xAI's page does not give the unit of its cost field. It does.
3. It said the test calls add "a cent or two". About half a cent.
4. It labelled a column "all three sorts differ". The figure counts lessons without three identical valid repeats.
5. It said Fable matched the table "the same as the others" and drew a conclusion about self-agreement. Two
   sorters matched on none, and the measure cannot carry that conclusion.
6. It said DeepSeek "thinks far more", that the limit "cut it where it cut nobody else", that gemma4's context
   "played no part", that Grok "may have had its earlier thinking in front of it" while "the others did not", that
   retrieval was "nobody's" home, and it called the cost "measured". Each is narrowed above to what was recorded.
7. It did not say plainly that the second guess, as a guess about all eight models, did not hold.

## Receipts
- Original run manifest SHA256: 76f85b26...19289b9b; original record key: 12bce540...1d6d9157.
- Original run-1 tally SHA256: 78879c80...17dada5f.
- Command logs, context and hardware observations, scan receipts and detailed private audit records are not included.
  Their source filenames and private locations have been replaced by these descriptions. Public records and
  analysis outputs have their own mappings and hashes. Offline reconstruction of the public analysis passed
  within the [documented scope](../README.md#public-edition-and-reconstruction); it cannot recover omitted
  provider fields or private operational receipts. Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.
