# The Sort, side run for DeepSeek: what came back (second version)

> Prepared public edition of a checked report. Original report SHA256: `123d25ef56ccc9ed45405d3ab143fe83d8bdf8b268a65b15117a3994b14f8498`. Historical hashes below identify original private artifacts, not these rewritten public files.
> The report records its original reporting date; historical decision lists are source context, not new requests.
> The [public summary](../results/side_tally.json), [public record](../records/side/) and
> [companion report](run1_report.md) are included. The public record projects sent prompts, label maps,
> visible answers, judgment prose and analysis metadata, excluding provider reasoning and private identifiers.
> Offline reconstruction of the public analysis passed within the [documented scope](../README.md#public-edition-and-reconstruction).
> Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.
> This publication edition follows Anthony's direction to make the work open before his own folder review. See [public-edition notes](../PUBLIC_EDITION_NOTES.md).

Written by the HQ seat (Claude Fable 5.2) at 2026-11-26 11:40:21 EST. This second version (2026-11-26 11:50:47 EST) applies four wording corrections from the Codex seat's read-back of the first (private independent audit, original SHA256 f12f204b...0573b63f), which rebuilt all seventeen comparison rows from the raw sorts on its own and found the numbers correct. The first version is kept as a private superseded report (sha256 32c1f37f...e2d94222). No count changed.

## What kind of run this was
AN EXPLORATORY, DESCRIPTIVE FOLLOW-UP SELECTED AFTER RUN 1, WITH ITS OWN PROSPECTIVE ANALYSIS PLAN. Choosing
DeepSeek, the larger requested limit and the lessons to highlight was done after run 1's result was seen. Its rules
were frozen before it ran (the original side-run freeze record, anchor 860184e5...60dfc323) and cleared by the Codex
seat. Nothing here is counted into run 1, no class or agreement figure is produced, and neither of
run 1's guesses is scored again. Anthony authorized this separate follow-up.

Where each figure comes from: homes, majorities and the limit-ending table are the frozen tally's
(the original side tally, sha256 a9130fcf...c848cfa6); the lesson-by-lesson comparison is the frozen
comparison script's (the original comparison output), which read only the two tally files and pinned
run 1's by its hash; tokens are what the maker reported in its replies; the cost is HQ's arithmetic at list prices.

## The run
- 2026-11-26 11:20:49 to 11:38:48 EST, one run, the original side-run configuration, exit 0. The anchor was verified before
  the test call and again before the count. The one test call (11:20:42 EST) answered "ready" and reported the model
  asked for.
- Only deepseek-v4-pro sorted, three times, with a requested limit of 60,000 written tokens a message and new
  shuffles under master seed 20261127. 6 of 6 planned messages were sent. No call was repeated.
- 3 of 3 sorts were readable as asked, and all 3 judgment answers came back. No maker-reported limit ending on
  either message; no stop for an overrun.

## What it wrote
| Sort | First message: written tokens | Of which reasoning, as reported | Second message: written | Of which reasoning |
|---|---|---|---|---|
| 1 | 32,493 | 32,306 | 4,254 | 3,858 |
| 2 | 18,660 | 18,473 | 4,593 | 4,129 |
| 3 | 21,515 | 21,328 | 3,818 | 3,413 |

Two of the three first messages reported more than the 19,000 that run 1 requested; one reported less. These are
the maker's own counters. This run changed the shuffles as well as the limit, so it does not isolate the effect of
the limit, and one run of three sorts says nothing general about how this maker behaves.

## Its homes
A majority home for a lesson is the one given in at least two of the three sorts. DeepSeek has a majority home on
16 of the 17 lessons. On lesson 4 it has no majority home: its three readable sorts gave three different homes
(tool, harness and check). No answer is missing. On 6 of the 17 lessons its three sorts were not all the
same (this count includes lesson 4).

## Beside run 1, lesson by lesson
Descriptive only. The comparison is with run 1's outside-group modal home. That modal home rests on the five
outside models that had majority homes in run 1 on sixteen lessons, and on four of them on lesson 4, where
claude-opus-5-5 also had no majority home. Run 1's group stays six as frozen, and all seventeen lessons stay in
this comparison's denominator. In the table, the script's word "(missing)" means no majority home, not a missing
answer.

| Lesson | Run 1: outside group's modal home | Side run: DeepSeek's majority home | Result | Run 1's class for the lesson |
|---|---|---|---|---|
| *1 | check | check | match | contested |
| 2 | judgment | retrieval | different | settled |
| 3 | check | check | match | settled |
| *4 | check | (missing) | missing | contested |
| 5 | gate | gate | match | settled |
| 6 | check | check | match | settled |
| 7 | check | check | match | settled |
| 8 | check | check | match | settled |
| 9 | harness | harness | match | settled |
| 10 | check | check | match | settled |
| *11 | check | retrieval | different | leaning |
| 12 | tool | tool | match | settled |
| 13 | check | check | match | settled |
| 14 | judgment | judgment | match | settled |
| *15 | check | judgment | different | leaning |
| 16 | check | check | match | settled |
| 17 | judgment | judgment | match | settled |

- Same majority home as run 1's modal home: 13 of 17. A different majority home: 3 (lessons 2, 11 and 15). No
  majority home: 1 (lesson 4).
- Read against run 1's classes, which are copied here as labels only: of the 13 lessons run 1 called settled,
  DeepSeek's majority home is the same on 12 and different on 1 (lesson 2: retrieval, where the group's modal home
  was judgment). Of the 2 leaning lessons, different on both (11: retrieval; 15: judgment). Of the 2 contested
  lessons, the same on lesson 1 (check) and no majority home on lesson 4.
- An additional descriptive observation, made by HQ after looking at the side results and outside the frozen
  comparison with the group's modal home: on lessons 11 and 15, DeepSeek's majority home is the majority home
  claude-opus-5-5 had in run 1 (retrieval and judgment), where the other four had check. That is a description of
  two lessons, not a finding about the two models.

## What this does and does not say
It says where DeepSeek put the lessons in three sorts under the higher requested limit: with the outside group's
modal home on thirteen lessons, with a different majority home on three, and with no majority home on one. The
lessons where it differs or has no majority home include three of the four that run 1 itself did not call settled.
It does not say what run 1 "would have been". These sorts are not added to run 1's counts, and no lesson's class
changes. The side run came later, with new shuffles and a different requested limit; the other five outside models
received 19,000 and reported no limit ending in run 1. It does not explain the amount or the quality of DeepSeek's
reasoning.

## The judgment answers
The original judgment-answer compilation (sha256 d8e498ac...f7c1d7de). Collected for a
person to read; nothing scored, counted or sorted them; HQ has not summarised them.

## Reported usage and estimated cost
Reported over the six messages: 7,434 read tokens, of which the maker reported 3,072 as cached and 4,362 as not,
and 85,333 written tokens (83,507 of them reasoning). With that split, at the maker's list prices, the Codex
seat's arithmetic gives about $0.34 at peak-hour prices and about $0.17 off peak. The run fell outside the hours
the maker's page lists as peak. The test call adds about a hundredth of a cent. No invoice was inspected. (The
first version's $0.35 treated every read token as uncached.) The planning
figure was about $1.43 before read tokens if every message had used the whole requested limit.

## Keys
HQ's saved search of the side folder's saved files and the lane's test-call files: 32 files, no match for any of
the four keys or their 8-character pieces, planted control found (private saved scan receipt).

## Limits
Everything in the side run's rules page under "What it cannot show"; one model, three sorts, one occasion; new
shuffles; a limit the other five were not given; and, as in run 1, the six definitions written by this maker's
sister model.

## Receipts
- Original side-run manifest SHA256: e65a25d8...67d7d78; original record key: 0d9fd772...9edad43.
- Original side tally SHA256: a9130fcf...c848cfa6.
- Command logs, the preflight transcript, usage-table receipt and detailed private audit records are not included.
  Their source filenames and private locations have been replaced by these descriptions. Public records and
  analysis outputs have their own mappings and hashes. Offline reconstruction of the public analysis passed
  within the [documented scope](../README.md#public-edition-and-reconstruction); it cannot recover omitted
  provider fields or private operational receipts. Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.
