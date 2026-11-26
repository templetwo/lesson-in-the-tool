# Experiment 003: the Sort

Published 2026-11-26 at Anthony's direction before his own review of this folder; he asked that the work be made
open first. This write-up was authored by the HQ seat (Claude Fable 5.2). The opening, credit and exact wording
have not been reviewed by Anthony. Later changes will be recorded as dated errata.

The text through Cost retains the passed write-up (source SHA256
`7b5ab13f66d4227029830412a162ff741c2d7cfafc64587a4a0133986109b68f`), apart from this header and the publication-status
sentence about the included reports. The final Codex wording-readback receipt (SHA256
`8b318e567679875e71eb7812a41aef7f2b1ae320cf91e15e95b02eb11b6e3a0c`) names that exact source and records a pass.
That receipt concerns draft wording; it does not review these publication-status edits or establish privacy clearance.
The checked original reports have SHA256 `8742dddf4a1fe3303767a7319ff931971a1183242800910f987046c1654dfcf0` (run 1)
and `123d25ef56ccc9ed45405d3ab143fe83d8bdf8b268a65b15117a3994b14f8498` (side run). Those hashes identify private
originals; the public copies are [the run-1 report](reports/run1_report.md) and [the side-run report](reports/side_report.md).

## In one paragraph
The repository asks where each lesson should live so the next model avoids repeating the mistake. Whether embedding
a lesson in a tool works better than stating it in a prompt remains an open question. This experiment first asked
these models where the lessons belong. In the outside group, fifteen of seventeen lessons met the planned
settled-or-leaning threshold. Its modal main home matched the house's earlier table on five of sixteen comparable
lessons.

## What was asked
Eight language models each got the seventeen lessons of the short sheet exactly as written, in a shuffled order,
and six homes (tool, check, gate, harness, retrieval, judgment) with a one-sentence definition of each, written by
an outside model from the six names alone. Each model was asked to give every lesson one main home and, optionally, a
second. A second message was sent only after a readable first sort, asking what remained a matter of judgment. Six outside
models from four makers sorted (claude-fable-5-2, claude-opus-5-5, gpt-6.2-astra, gpt-6.2-sol, grok-4.7,
deepseek-v4-pro, each under its maker's own high-effort configuration), and two local models were counted as a
group of their own (a qwen3.8 27B and gemma4). Three sorts each, every one a fresh conversation. A model's majority
home for a lesson is the home it gave in at least two of its three sorts. Scripts parsed and tallied the
assignments using fixed rules; no human or model judge graded the judgment answers' contents.

## What was frozen before experimental sorting
The rules, the code, the settings and the counting settings were frozen by hash, the hashes recorded outside the
folder, and a second seat read the frozen files back against the code. Two guesses were fixed:
1. At least ten of the seventeen lessons would come out settled (five or six of the six outside models sharing a
   home) or leaning (four).
2. Each model would be steady: fewer than six of its seventeen lessons without a home given in two of three sorts.

Before the freeze there were preliminary calls that produced no sorting data: a one-word test to each model, and
the call in which an outside model wrote the six definitions.

The first freeze was withdrawn before the main experimental sorts. The readback found that the rules promised an
output limit the code did not send to three of the four outside providers, and that the tally computed agreement
statistics for the local pair against the rules. Request limits and tally behavior were corrected, and new freezes
were issued. The reviewed xAI output-limit mechanism did not establish a whole-bill ceiling, so that part of the
spending plan remained an estimate the researcher accepted before the main run.

## Run 1 (2026-11-25 23:56 to 2026-11-26 00:29 EST)
24 first messages and 20 second messages were sent. 20 of 24 sorts could be read as asked.

**Guess 1 held: 15 of 17.** Thirteen lessons settled, two leaning, two contested (lessons 1 and 4). To read beside
it: DeepSeek produced one readable sort, so it has no two-of-three majority home on any lesson and gives the
outside group no majority votes. That limits the group's modal counts to at most five, and Opus has no majority
home on lesson 4. On the thirteen settled lessons the other five models' majority homes agree.

**Guess 2 did not hold.** The criterion passed for six models and failed for two, and the guess is about all eight.
DeepSeek and gemma4 each had two failed sorts, which makes a two-of-three majority impossible. That is the scoring
mechanism; it does not show that either model disagrees with itself.
- deepseek-v4-pro: two of its three first messages ended at the requested limit of 19,000 written tokens with all
  reported completion tokens attributed to reasoning and no final-answer text.
- gemma4: two of its three sorts left out two words the reply format asks for. A person can read them; the rule
  fixed before the run says a sort not written exactly as asked is failed and never repaired.

**Agreement.** Among the available outside-model majority homes: Krippendorff's alpha 0.83, 95% percentile interval
0.57 to 0.97 from 2,000 resamples of the lessons, on 84 of the 102 planned ratings. Missing majorities are left
out, so this does not estimate agreement with DeepSeek. The interval resamples lessons conditional on these models
and the observed missingness; it does not resample models or failed collection.

**Where the lessons went.** Each model's cell is its majority home; "none" means no majority home.

| Lesson | House's earlier table | Outside group's modal home | Class | claude-fable-5-2 | claude-opus-5-5 | gpt-6.2-astra | gpt-6.2-sol | grok-4.7 | deepseek-v4-pro | qwen3.8 27B (local) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | check + judgment | check, 3 of 6 | contested | check | check | gate | gate | check | none | check |
| 2 | tool | judgment, 5 of 6 | settled | judgment | judgment | judgment | judgment | judgment | none | check |
| 3 | tool | check, 5 of 6 | settled | check | check | check | check | check | none | check |
| 4 | tool + check | check, 3 of 6 | contested | harness | none | check | check | check | none | check |
| 5 | gate | gate, 5 of 6 | settled | gate | gate | gate | gate | gate | none | gate |
| 6 | harness | check, 5 of 6 | settled | check | check | check | check | check | none | check |
| 7 | tool | check, 5 of 6 | settled | check | check | check | check | check | none | check |
| 8 | retrieval | check, 5 of 6 | settled | check | check | check | check | check | none | check |
| 9 | (this table) | harness, 5 of 6 | settled | harness | harness | harness | harness | harness | none | harness |
| 10 | tool | check, 5 of 6 | settled | check | check | check | check | check | none | check |
| 11 | tool | check, 4 of 6 | leaning | check | retrieval | check | check | check | none | retrieval |
| 12 | tool + check | tool, 5 of 6 | settled | tool | tool | tool | tool | tool | none | tool |
| 13 | retrieval | check, 5 of 6 | settled | check | check | check | check | check | none | check |
| 14 | check | judgment, 5 of 6 | settled | judgment | judgment | judgment | judgment | judgment | none | judgment |
| 15 | check | check, 4 of 6 | leaning | check | judgment | check | check | check | none | judgment |
| 16 | harness | check, 5 of 6 | settled | check | check | check | check | check | none | check |
| 17 | judgment | judgment, 5 of 6 | settled | judgment | judgment | judgment | judgment | judgment | none | judgment |

The outside group's modal homes were check on eleven lessons, judgment on three, and gate, harness and tool on one
each. Retrieval was never the group's modal home.

**Beside the house's earlier table** (a side comparison fixed in advance as exploratory; it decides nothing).
Lesson 9 is left out because the table's entry for it, "(this table)", is not one of the six homes. The group's
modal home is the table's main home on 5 of the 16 lessons compared. Sorter by sorter there are two separate
counts, never added together: of the 96 planned sorter-by-lesson cells, 4 match the table exactly (main home and
second home alike) and 35 share at least one home with it. Only 79 of the 96 planned sorter-by-lesson cells had a
majority home; missing majorities counted as nonmatches under the fixed rule. The table has tool as main home on
seven lessons; the group's modal home was tool on one. The local qwen model's majority home matched the outside
group's modal home on 14 of 17 lessons.

## The limit, and a question that anticipated it
According to HQ's recorded message timestamps, about twenty-four minutes before the main run, the researcher raised
a question about unequal limits: "Wouldn't That be biases". A rule was added before the freeze: every reply the
maker reports as ending at the limit is counted, by model and by message, in a table of its own. The table reads:
DeepSeek, two first messages; every other model, none. One requested limit number, with two reported limit endings
for one sorter and none reported for the others. Every comparison involving DeepSeek in run 1 carries that limit.
Under their makers' high-effort configurations, claude-opus-5-5's first messages reported 233 to 238 written tokens
with zero reported thinking tokens, and two of deepseek-v4-pro's reported 19,000 completion tokens, all of them as
reasoning. These are the makers' own counters and are not calibrated or comparable units.

## The side run for DeepSeek (2026-11-26 11:20 to 11:38 EST)
AN EXPLORATORY, DESCRIPTIVE FOLLOW-UP SELECTED AFTER RUN 1, WITH ITS OWN PROSPECTIVE ANALYSIS PLAN. Choosing
DeepSeek, the larger requested limit and the lessons to highlight was done after run 1's result was seen. Its own
rules were frozen and read back before it ran. Nothing in it is counted into run 1; no lesson's class changes and
neither guess is scored again.

Only deepseek-v4-pro sorted, three times, requesting up to 60,000 written tokens a message, with new shuffles, so
the run does not isolate the effect of the limit. All three sorts were readable and no limit ending was reported.
Its first messages reported 32,493, 18,660 and 21,515 written tokens.

| Lesson | Run 1: outside group's modal home | Side run: DeepSeek's majority home | Result | Run 1's class |
|---|---|---|---|---|
| *1 | check | check | match | contested |
| 2 | judgment | retrieval | different | settled |
| 3 | check | check | match | settled |
| *4 | check | no majority home | no majority | contested |
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

On lesson 4 its three readable sorts gave tool, harness and check, so it has no majority home there; no answer is
missing. DeepSeek's majority home is the same as run 1's outside-group modal home on 13 of 17 lessons, different on
3, and it has no majority home on 1. Of the thirteen lessons run 1 called settled, the same on twelve; of the two
leaning, different on both; of the two contested, the same on one.

## What this can and cannot show
It shows where these models put these lessons under these definitions, and where they disagree. It cannot show
where a lesson actually works; that is what the experiments on tools are for. One possible explanation for so many
lessons landing in "check" is the relationship between the lessons' wording and the check definition the sorters
were given; this experiment did not test that explanation. It is one run plus one small follow-up.

## Limits
- Two pairs of outside models share a maker, and training or design may overlap. Their votes should not be treated
  as independent replications.
- Claude Fable 5.2 wrote the house's earlier table and also sorted. The exploratory comparison with the table does
  not isolate that.
- The six definitions were written by deepseek-flash; its sister model is one of the sorters.
- A few lessons name their home in plain words.
- The makers' settings are not comparable units; the local models' context windows were set by their machines.
- Grok's second-turn reported input equals 2,550 plus its preceding reasoning-token count in all three repetitions,
  though three plain text messages and no response id were sent. The saved records do not establish whether this
  reflects available context, reconstruction or usage accounting; the cause remains unresolved. It concerns the
  second message only.
- No human or model judge graded the judgment answers' contents. HQ has not summarized those answers.

## How it was checked
HQ and Codex used different model families and checked one another's work. Before the main sorting run, Codex
compared the frozen rules with the code and identified the limit and local-statistics mismatches. HQ ran the full
suite on Codex's proposed fix and caught a runner-to-tally defect that would have caused the tally to reject
real-run manifests. Codex corrected it, added a regression check, and ran the full suite and selftest; HQ then
checked and adopted the revised candidate. After the runs, Codex independently reconstructed the classifications,
majority homes, classes and comparisons from saved raw sorts, reproduced Run 1's alpha and seeded interval, and
checked reported usage against saved provider fields. The first Run 1 readback identified sixteen groups of
corrections or qualifications; the side-run readback identified four. Final wording was checked against exact
report hashes. Operational statements such as host actions and key searches remain attributed to HQ's receipts.
The corrected reports and the record of the corrections are included in this publication folder.

## Cost
Run 1's list-price estimates were about $0.49 for Anthropic and $0.83 for the paid providers, including DeepSeek
priced at peak rates. The side-run estimate was about $0.17 at the applicable off-peak rates, or $0.34 at peak
rates. No invoice was inspected. These cover the two runs' sorting calls, not every call made while building.

## Public edition and reconstruction

This publication edition is prepared at Anthony's direction to make the work open before his own review of the
folder. The passed opening and exact bias quotation are retained, the rulings file is omitted, and the HQ-drafted
credit below remains unreviewed by Anthony, as do the opening and exact wording. This publication is not outside
registration and does not authorize new tests or new model calls. Later changes will be recorded as dated errata.

| Included here | Purpose |
|---|---|
| [Run 1 report](reports/run1_report.md) and [side-run report](reports/side_report.md) | Sanitized public editions of the two checked reports |
| [Corrections](reports/CORRECTIONS.md) | A short account of corrections documented in the checked reports; superseded reports are not included |
| [Run 1 tally](results/run1_tally.json), [side tally](results/side_tally.json), and [comparison](results/comparison.json) | Public editions of the analysis outputs |
| [Run 1 records](records/run1/) and [side-run records](records/side/) | Sent prompts, label maps, visible answers, judgment prose and metadata for reconstructing the published analyses |
| [Run 1 code](code/run1/) and [side-run code](code/side/) | Separate code editions mapped to their respective originals |
| [Freeze records](freeze/) | Records of the original freezes and the declared public editions |
| [Public-edition notes](PUBLIC_EDITION_NOTES.md) | Omissions, transformations, and original/public file mappings and hashes |

The [rules pages](code/run1/rules/SORT_RULES.md) and their [side-run code copy](code/side/rules/SORT_RULES.md) preserve the historical frozen content with declared hygiene transformations, so they still open as a draft saying nothing has run; the closing “THE RULES IN FORCE” section states what governed.

The exported records are a public projection, not the complete original provider replies. The offline replay
passed on this public edition: 24 main-run trials and 3 side-run trials, retaining failed and missing entries and
44 main-run plus 6 side-run sent-call records. It verified the public manifest hashes, rebuilt the first-prompt
and question bytes and label maps for all 27 trials from saved seeds, and reparsed the visible answers. After
explicit normalization of provenance-only fields, every tally semantic field matched: classifications, agreement,
bootstrap intervals, repeat stability, house comparisons, judgment parsing and provider-reported limit-ending
counts. The side comparison reproduced 13 matches, 3 differences and 1 missing majority across all 17 lessons.

This replay does not generate the model responses again or reconstruct the full serialized second request.
The prompt files contain the first prompt and the question, not the complete second-turn wire request. It does
not reconstruct reasoning-character lengths from withheld text, invoice costs, pricing arithmetic or private
freeze times. Provider reasoning fields, provider/account identifiers, credentials, private operational paths
and hostnames, rulings and smoke-test logs are excluded.

Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.

Original hashes identify original bytes; they do not authenticate transformed public copies. The public copies
need their own file lists and hashes. Historical statements above about raw-record checks describe earlier private
audits; they are separate from verification of this exported record. See the public-edition notes for that boundary.

From the repository root, the offline verification commands are:

```sh
python3 -B experiments/003-the-sort/tools/reproduce.py
python3 -B tools/verify_archive.py
python3 -B -m unittest discover -s tests -v
```

The experiment-specific helper passed with exit code 0 and the scope described above. The repository-wide archive
verifier passed. All 54 tests in the repository's existing unit-test suite still pass with 003 added; they do not
test experiment 003. [CHECKS.md](CHECKS.md) records the commands and observed results. The archive verifier's
semantic reconstruction of experiments 001/001b remains distinct.

## Provisional credit

The following credit was drafted by HQ and has not been reviewed by Anthony. It is retained in this publication
edition; later changes will be recorded as dated errata:

> Designed and run by Anthony J. Vasquez Sr. with Claude (the HQ seat); independent review, fixes and verification
> by the Codex seat (gpt-6-astra); home definitions written by deepseek-flash.
