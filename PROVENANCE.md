# Provenance

Who made what, when, and how to check it. Times are Eastern, 2026-11-24, each read from a clock or a file stamp at
the time, never estimated afterwards.

## Timeline
| time | what |
|---|---|
| 12:31:54 | Anthony, by text, asks for one consolidated sheet of mistakes and successes that every model's next seat learns from |
| 12:33:57 to 12:42 | A Claude Opus 5.5 agent reads six sources of the house's record and drafts the sheet |
| 12:58:54 | Anthony: "Save it all to the stack archive and tier 34" |
| 13:23:29 | Anthony opens Tier 35 with the package as its foundation |
| 13:27:23 | Anthony relays ChatGPT's review: reword rule 11; test three setups, scored blind |
| 13:48:07 | Rules of experiment 001 frozen, hashed and registered, before any model under test was called |
| 13:49:14 | The blind judge (a Grok agent) finishes its own test: 38 of 38 hand-written replies classified correctly |
| 13:53:49 to 14:43:22 | Null run, then real run, on the 1.7B model |
| 14:44:57 to 14:52:43 | The judge scores both runs |
| 15:41:16 | Anthony allows the load on the GPU box: "Let's run House on the same test" |
| 15:43:35 to 16:10:21 | Real run, then null run, on the 27B model |
| 16:10:41 to 16:23:39 | The judge scores both runs |
| 16:30:35 | Anthony relays a Codex seat's review and singles out "the lesson belongs in the tool" |
| 16:56:03 | Anthony relays ChatGPT's piece on translating principles into their computational homes |
| 17:02:15 | Anthony asks for this repository, built before anything else, and pushed public on his word |
| 17:53 | Anthony allows the re-judging (experiment 001b), typed: "now the work" |
| 20:44 | A Claude Opus 5.5 agent begins the masking (by its own `date`) |
| 21:04:54 | The builder's final check run begins (by its `date`); in it the masked file is written and every self-check passes |
| 21:07:07 | Rules of experiment 001b frozen and hashed; registered at 21:07:28, before any judge call |
| 21:07:35 to 21:08:21 | The judge (a fresh Grok agent) repeats 001's selftest: 38 of 38 |
| 21:08:38 to 21:31:03 | Three judge sessions in the frozen order: unmasked (to 21:15:49), masked (21:16:19 to 21:23:17), unmasked again (21:23:34 to 21:31:03) |
| 21:31:46 | Erratum E1 of 001b (one mistyped id) written before any number by setup was seen |
| 21:32:59 | The 001b report |
| 21:36:10 | The 001b addendum, after House read the result at 21:35:22 |
| 22:00:54 | Preparation of 001b for this repository begins; not pushed until Anthony says go |

## The frozen inputs of experiment 001
From `experiments/001-sheet-pilot/FREEZE.json` (frozen at 2026-11-24 13:48:07 EST). These files are published byte for byte.

| file | SHA-256 |
|---|---|
| `experiments/001-sheet-pilot/PREREG.md` | `27a7d4daa91cd2cffbca0f0367ca9a5fe69b2c689e3467efca69421b93ff26f7` |
| `experiments/001-sheet-pilot/tasks/tasks.jsonl` | `e5229ae858d5206a9c609db183acabbb80b686c20c1611b477e483a65fd2aa8f` |
| `experiments/001-sheet-pilot/tasks/selftest_replies.jsonl` | `69a88bf53ae0bf0c9e24ec0a52f3257dde8168c6f9ba9f5035b5bbdd6f1a8afb` |
| `experiments/001-sheet-pilot/harness/generic_checklist.md` | `5f1e825d0e7fb949043bd711a1c32b775d531e1df6bbc542b3740347087b7db2` |
| `experiments/001-sheet-pilot/harness/conditions.json` | `83a5e97c07a11efdcc039c35d861d08eda9005f5be75a7a3509e830779b49eb1` |
| `experiments/001-sheet-pilot/harness/run_trial.py` | `7a1d591bc40e1e516ccbb5ffde4ec3c1fdacf7cf65a280ae2b7a60580dff5841` |
| `experiments/001-sheet-pilot/harness/score_auto.py` | `bc40e9a3feb692a027711b38c794f683ec1b718f0da2cd4cab3638cae83ffeca` |
| `experiments/001-sheet-pilot/harness/make_blind_packet.py` | `5ab8db0dd89a3523e66263d5d03dbe96ab6043ba85e82eeb937d037db8eef7e6` |
| `experiments/001-sheet-pilot/harness/tally.py` | `7060498787810cac36b35b684721852c4e0520d58377998eb6d791433a43acb3` |
| `experiments/001-sheet-pilot/harness/selftest.py` | `7a5f5216cd32662f04c70f77980e6f9e91d1051cb88f2994f5487c7c44cd2161` |
| `sheet/SHEET_SHORT_v2.md` | `5d8dcecd133bcb9d78a81e06c2ec48589e4ccb0c1457a28cdc01e375965335a1` |

Checked when this file was written: 11 of 11 copies in this repository match their frozen hash.

## The frozen inputs of experiment 001b
From `experiments/001b-judge-lean/FREEZE.json` (frozen at 2026-11-24 21:07:07 EST). It lists 16 files by path and
the hashes of the two judge instruction files. All are published byte for byte. The rules and the freeze record:

| file | SHA-256 |
|---|---|
| `experiments/001b-judge-lean/PREREG_001b.md` | `e5c816900f4c5cd4a6aabbadbe28612abf3c1bf49649513691eb7b857ab989b1` |
| `experiments/001b-judge-lean/FREEZE.json` | `3579866bf9c980706075b91268b915d5b38b0e2186a1b48844c38aa742c047b6` |

Checked at 2026-11-24 22:04:39 EST: 18 of 18 copies in this repository match the hashes in
`FREEZE.json`, and the two hashes above match the ones registered at 21:07:28. Of the five inputs `FREEZE.json`
records from experiment 001, four match the copies here; 001's `runs/house/key.json` does not, because its `meta`
block was generalised before 001 was published (001 `ERRATA.md` E6). 001b does not read that file.

## The sheet and the reviews

| file in this repository | SHA-256 | note |
|---|---|---|
| `sheet/SHEET_SHORT.md` | `81bbf575c36ebdc41798e806082f5c573e38bfbd5f28f9ca7b366dad8fd7edca` | short form, draft 1; the same bytes are held in the house's private archive |
| `sheet/SHEET_SHORT_v2.md` | `5d8dcecd133bcb9d78a81e06c2ec48589e4ccb0c1457a28cdc01e375965335a1` | short form, draft 2 (rule 11 reworded); frozen input of experiment 001 |
| `sheet/SHEET_LONG_PUBLIC.md` | `b7def623870b5df05f52d636b42eea9516b9707171489a76c08b3a8043ae879c` | public edition of the long form, made for this repository |
| `sheet/PUBLIC_EDITION_NOTES.md` | `d9cfdc771176556ac3b175f82880eb34988269ea5f36a8bf5a234b125c92b993` | what the public edition withholds, by category |
| `reviews/CHATGPT_REVIEW_20261124.txt` | `d133647a61cb0802b8fe11c11b8f907f01963787f453f51bcb3323a2cf749385` | as relayed; our header line shortened and one place name removed for publication |
| `reviews/CODEX_REVIEW_20261124.txt` | `9e134872ce8341b7693539f5097e75fb53db05f857f1774d07b5230ac769d203` | as relayed; our header line shortened for publication |
| `reviews/CHATGPT_TIER35_TRANSLATION_20261124.txt` | `787fcf0ccdb43c89cc490d02a187d62559f679097080f2e54ead47d6045cf824` | as relayed; our header line shortened for publication |

Withheld, not in this repository. Their hashes are given so that a later release, or a reader given access, can
check that nothing was changed:

| withheld file | SHA-256 |
|---|---|
| the long form of the sheet as first drafted (40 shapes with pointers into the private record) | `5380274a00bb166866b55dcd643a7afb4758fef4a253a27595a8451ad1daaa40` |
| its coverage report | `1f1da9a5e8491ee9ee9c01b7f5492650dd8051a7b673be3266926d6ee8e2b6c9` |

The three reviews are held in the house's private archive exactly as relayed. The copies here differ from those only in
the ways the table states.

Note: `sheet/SHEET_SHORT.md` is draft 1 as corrected by the HQ seat in one phrase before it was archived (a dead link read
healthy for 5.6 hours; the draft had said "five hours"). Draft 2 changes rule 11 only.

## Who did what
- **Anthony Vasquez Sr.**: the questions, the direction, every permission to run, and the decisions about what a result means.
- **Claude Fable 5.2 (the HQ seat)**: the rules of the test, the review of every piece, the runs, the reports, this repository.
- **Claude Opus 5.5 agents**, working under the HQ seat: the draft of the sheet; the test harness and the generic
  checklist; the 42 task items (that writer was kept from seeing either checklist).
- **ChatGPT** (through Anthony): the three-setup blind design, the rewording of rule 11, and the piece on where a lesson lives.
- **A Codex seat** (through Anthony): tools in every arm, jobs that truly succeed beside jobs that only say so, and the
  sentence the project is named around.
- **A Grok agent**: the blind judge, working from a folder that held only the packet it was asked to score.

Experiment 001b, separately:
- **House** (the house's own qwen3.8 27B model, speaking in the House Room): the design of the test, and the
  reading of its result given in the addendum. One change came from the HQ seat and House accepted it: the
  threshold is the judge's own repeat noise, not the model's run-to-run noise.
- **Claude Fable 5.2 (the HQ seat)**: the rules, the review of every masked reply, the freeze, the runs, the report,
  the erratum and the addendum.
- **A Claude Opus 5.5 agent**, working under the HQ seat and shown only the replies: the masking and its notes, and
  the scripts (the mask applier, the checker, the packet builder and the tally).
- **A Grok agent**: the judge, a fresh session for the selftest and for each of the three packets, each in a folder
  holding only its instructions and one packet.
- **Anthony Vasquez Sr.**: allowed the work.
- **A Claude Opus 5.5 agent** prepared it for this repository (generalising, checking, notes); it changed no number.
- **Others, named and unnamed.** Anthony reaches his decisions through the IRIS Gate multi-model process
  (https://github.com/templetwo/iris-gate), in which several independent AI models are consulted. The list above is
  what the record shows for this repository. Other models and other instances were consulted along the way, some
  without a record. The credit for this work extends to them.

## What was left out of this repository, and why
- The long form of the sheet as first drafted, and its coverage report. They point into the private record and touch
  matters that are not for publication. `sheet/SHEET_LONG_PUBLIC.md` is the edition made for readers, and
  `sheet/PUBLIC_EDITION_NOTES.md` says by category what it withholds.
- The HQ seat's working notes and Anthony's messages in full. His words appear here only where they are quoted.
- Anything about family, personal finance, credentials, protected material or his personal schedule. The drafter of
  the sheet had already skipped 17 such items in the record; the counts by category are in the notes file.
- The private record itself.

## Development contribution, 2026-11-25

At Anthony's request to investigate, contribute from a separate tree, and help build the project's tools and
concepts, a GPT-6 Astra Codex seat prepared the following from repository main `19a3017`:

- `lesson_tools/`: a real JSONL save with required readback, structured intent/action/observation receipts, and
  temporary demonstrations of true success, false success and unavailable evidence.
- `docs/LESSON_TOOLS.md`: the concept of a tool carrying an incident, an executable obligation, an attempted
  refutation and a stated boundary. Its proposed experiments and future tools are explicitly distinguished from
  implemented behavior.
- `tools/verify_archive.py` and `tools/archive_evidence.py`: offline checks and deterministic reproductions of the
  public 001/001b archive, with adversarial controls in `tests/` and scope in `docs/VERIFICATION.md`.

The seat and its delegated reviewers read the published sheet and experimental design. Their development examples
are not blinded tasks. No model-under-test calls were made. Frozen inputs, raw runs, judge scores, reported results
and experiment 002's draft remain unchanged. These additions credit the Codex work as provenance; they do not
establish new research results or alter the historical authorship above.

Following HQ's review and publication of that contribution on branch commit `0ed07ea`, the same Codex seat
refined it on 2026-11-25: made adapter provenance and default file-replacement policy explicit in receipts,
refused destination symlinks, rejected archive bytecode and cache artifacts, and added controls for the automatic
score, masked-file and tally reproduction checks. The documentation now distinguishes internal consistency from
agreement with a published Git commit and states that verification executes the selected archive's Python.
Experiment 001's erratum E8 records the duplicate-plan tally defect found by the seat and independently reproduced
under HQ. That entry is appended beside the frozen code; frozen inputs, raw runs, scores and results remain unchanged.
