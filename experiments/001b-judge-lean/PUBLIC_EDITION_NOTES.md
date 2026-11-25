# Public edition notes for experiment 001b

Written 2026-11-24, between 22:05:44 and 22:11:19 EST (two readings of `date`), by a Claude Opus 5.5 agent working under the HQ seat, before
publication. This follows what 001's `ERRATA.md` entry E6 did for experiment 001: frozen files are published byte for
byte; in files that are not frozen, private paths, machine names, identifiers from the house's private record and
names of private files were generalised. No number and no finding was changed.

## Generalised, in files that are not frozen

| file | was | is now |
|---|---|---|
| `FREEZE_REGISTERED.txt`, line 1 | the identifier of the registration entry in the house's private record | "an entry in the house's private record (its identifier withheld for publication)". The time and both registered hashes are unchanged. |
| `REPORT_001b.md`, line 4 | the same identifier, shortened | "(in the house's private record)" |
| `REPORT_001b.md`, "Kept" section | the four judge run logs named by their private file names | "the four judge run logs (held in the house's private record, not published)" |
| `REPORT_001b_ADDENDUM.md`, line 4 | the line number of House's message in the House Room's record, beside its time | the time only |

`ERRATA.md`, `work/MASKING_NOTES.md` and `work/final/TALLY.txt` are published as they were written; nothing in them
needed changing. The judge's score files are published as written.

## Frozen files, published byte for byte, and what they still carry

Every file named in `FREEZE.json` (16 paths, plus the two judge instruction files whose hashes it records) is
unchanged. A scan before publication found these private-record traces in them, all left in place so that the hashes
hold:

- `FREEZE.json`: the name of the seat, model and machine that froze it.
- `PREREG_001b.md`: "Mac Studio"; the House Room line numbers of House's design (234, 248 and 252); the name of the
  house's dispatch tool for the Grok judge. It also says the rules were registered before any judge call, without
  an identifier.
- `harness/README.md`: the folder on the house's machine the scripts were run from, and a variable pointing at 001's
  folder there. It also names files not published here: `work/BUILD_RESULT.md`, `work/trial/` and the deleted
  `work/_replies_view.jsonl` (see "Left out" below). The README in this folder gives the same commands with paths
  that work inside this repository.
- `harness/tally_rejudge.py`: a comment naming the draft of the rules (`PREREG_001b_DRAFT.md`), which is not
  published. The five decision lines it printed in `work/final/TALLY.txt` were checked during this preparation and
  each appears word for word in the frozen `PREREG_001b.md` (bold marks and line breaks aside).
- The packets and `work/masked.jsonl`: invented employee and contact numbers from 001's task log (for example
  `#143`), which are already public in 001's tasks and replies. No real address, number or name.

The scan looked for: home-folder paths, the machine's user name, the house's private store, house-network
addresses, tailnet addresses, e-mail addresses, phone numbers, token-shaped strings, "claim" followed by
an identifier, the dispatch tool's name, cache and home paths, the machine and seat name, record line numbers and
run-log file names. It found the items above and nothing else.

## Left out, and why

- **The four judge run logs** (the Grok sessions for the selftest and for U1, M and U2). 001 published none of its
  judge run logs either; the `runs/*.log` files in 001 are the model runner's output, not the judge's. The logs carry
  the judge's working folder on the house's machine, its visible working notes and its cost, and they stay in the
  house's private record. What they were used for in the report (that no session mentioned any other folder or file)
  therefore rests on the house's own reading of them.
- **The draft of the rules** (`PREREG_001b_DRAFT.md`). Only the frozen rules are published.
- **`work/BUILD_RESULT.md`**, the builder's record of the self-checks before the freeze. It names a private file on
  the house's machine. Its substance is reproduced below: every self-check was run again in this repository copy.
- **`work/trial/`**, a dry build of the packets with seeds 1, 2, 3 and order seed 1, made to test the builder. It is
  not part of the run. It can be rebuilt with `harness/make_packets.py` and those seeds; that was done during this
  preparation and the three packet hashes matched the trial packets exactly
  (`54e670e5...`, `ba1e6da6...`, `afa82cfb...`).
- **The House Room record** behind House's design and reading. House's words are reported in the reports; the room's
  record is private.

## Two things a careful reader should know

1. **001's key file.** `FREEZE.json` records the hash of 001's `runs/house/key.json` as it was on the house's
   machine. The repository copy hashes differently because its `meta` block was generalised for 001's publication
   (001 E6, point 6). The other four inputs from 001 match. 001b does not read that file.
2. **The judge's selftest answers are byte-identical to 001's.** `work/judge_selftest/judge_selftest_scores.jsonl`
   has the same hash as `../001-sheet-pilot/runs/judge_selftest/judge_selftest_scores.jsonl` (`e3204cce...`). The
   house's record shows it was written by a fresh session at 21:08:21 EST on 2026-11-24, in its own folder. That is
   what to expect when a judge answers all 38 lines correctly in packet order in the same format, but with the run
   logs withheld, that it was a fresh session rests on the house's record, not on anything here.

## Checks run in this repository copy before publication

Run on 2026-11-24 at 22:04:39 EST (by `date`), from `experiments/001b-judge-lean/`, with the commands in this folder's
README (outputs written outside the repository):

- Frozen hashes: 18 of 18 OK (the 16 files in `FREEZE.json` and the two judge instruction files).
- `python3 harness/check_mask.py --selftest`: `SELFTEST OK (14 of 14 cases as expected)`, exit 0.
- `python3 harness/tally_rejudge.py --selftest`: `SELFTEST OK (14 of 14 checks as expected)`, exit 0.
- `python3 harness/make_packets.py --selftest`: `SELFTEST OK (9 of 9 checks as expected)`, exit 0.
- `check_mask.py` on the real files: `CHECK OK`, 0 failures, 0 warnings, 39 of 126 changed, 5042 characters removed,
  9 capitals, exit 0.
- `apply_mask_edits.py` rebuild of `work/masked.jsonl`: identical bytes.
- `make_packets.py` with the frozen seeds: all three packets, all three keys and the session order identical.
- `tally_rejudge.py` with `U2_id_restored.jsonl` and 001's judge scores: output identical to `work/final/TALLY.txt`,
  exit 0. With `U2.jsonl` as written: refused, exit 2, `REFUSED: U2: id 'a72690cc274f06f' is not in the U2 key`.
