# Experiment 001b harness

All scripts: `/usr/bin/python3` (3.9), standard library only, no network, no model calls.
Run from `~/.sovereign/hq/lanes/runs/2026-11-24_sheet-test-rejudge/`. Below, `S=~/.sovereign/hq/lanes/runs/2026-11-24_sheet-test`.

## Files
| File | What it is |
|---|---|
| `work/mask_edits.json` | The masker's hand-chosen deletions: per reply id, the exact substrings removed. The line-by-line record of what was hidden. |
| `work/masked.jsonl` | 126 lines in raw order: `{id, item_id, reply_original_sha256, reply_masked, changed}`. Hash = sha256 of the reply's UTF-8 bytes. |
| `work/MASKING_NOTES.md` | The rule the masker applied and every hard or unsure call. |
| `work/trial/` | A trial build with seeds 1, 2, 3 and order seed 1. Not for the real run. |
| `harness/apply_mask_edits.py` | Applies `mask_edits.json` (deletions and listed capitals) to the originals; the only way `masked.jsonl` is written. |
| `work/BUILD_RESULT.md` | The real output of every self-check. |

## Steps, in order

1. **Rebuild the masked file from the edits (optional; proves it is reproducible).**
   `/usr/bin/python3 harness/apply_mask_edits.py --raw $S/runs/house/raw.ndjson --edits work/mask_edits.json --out work/masked.jsonl`
   Refuses if a span is missing, doubled or overlapping. Reads only `id`, `item_id`, `reply` from raw.

2. **Check the checker, then the mask.**
   `/usr/bin/python3 harness/check_mask.py --selftest` must print `SELFTEST OK`.
   `/usr/bin/python3 harness/check_mask.py --raw $S/runs/house/raw.ndjson --masked work/masked.jsonl --edits work/mask_edits.json` must print `CHECK OK` and exit 0. From the edits file it reads ONLY the listed capitals, never the deletion lists.
   - Proves: same order and ids; every original hash; unchanged lines byte-identical; changed lines really differ and are deletion-only, apart from the listed single-letter capitals, by three tests (character subsequence; a `difflib` alignment with only equal/delete; every deleted run starts and ends at a word boundary); no reply, changed or not, matches a mention pattern outside the printed exemption list.
   - The selftest proves each doctored case is caught: an added word, a reordered pair, a changed reply still saying "checklist item 4", an "unchanged" reply off by a space, a changed-but-identical line, a wrong hash, a missed reply still saying "Rule 2", a capital made but not listed, a listed capital beside an unlisted case change, a listed entry that changes two letters or rewords, and a listed capital that is not at a sentence start. A listed capital must differ from its source only in the case of the first letter, occur once in the original, survive into the masked text and stand at a sentence start. It also shows that the subsequence test ALONE passes the added-word case, so the word-boundary test is doing real work.
   - Does NOT prove: that nothing was added when an added word is a WHOLE word that also sits inside a deleted span (for example a reply that deletes "Rule 4 (Read the clock)" and adds "clock" elsewhere at a word boundary). None of the three tests can tell that apart from a kept word; only HQ reading `mask_edits.json` against the pairs guards it. Nor that every mention was found (the pattern list is the masker's; a mention in words no pattern covers would pass); that the masking choices were right; that deletions left readable sentences. The "warnings" list (sentences now starting small, etc.) is for HQ's reading, not a gate. HQ reads every changed pair; `mask_edits.json` is the shortest way to do that.

3. **Freeze.** Hash `work/masked.jsonl`, `work/mask_edits.json` and the rules together, as the draft says.

4. **Make the packets with fresh seeds chosen at the freeze.**
   `/usr/bin/python3 harness/make_packets.py --tasks $S/tasks/tasks.jsonl --raw $S/runs/house/raw.ndjson --masked work/masked.jsonl --out work --seed-u1 A --seed-u2 B --seed-m C --seed-order D`
   - Writes `work/packets/{U1,U2,M}/packet.jsonl`, `work/keys/{U1,U2,M}.json`, `work/session_order.json`.
   - Each line is exactly `{id, prompt, pass_rule, reply}`; ids are 16 hex from that packet's seed; each packet has its own shuffle. Rebuilding with the same seeds and inputs gives the same bytes.
   - First `/usr/bin/python3 harness/make_packets.py --selftest` must print `SELFTEST OK`. It proves on made-up replies: same seeds give byte-identical packets, keys and order; other seeds give other ids and orders; lines hold exactly the four fields; no id is shared between packets or with raw; U1 and U2 hold the originals and M the masked replies; a repeated seed and a wrong original hash are refused. On every real build it also proves (refuses otherwise): masked matches raw by order, id and hash; seeds differ; no id repeats within or across packets or equals a raw reply id; no two packets share an order; every item has a prompt and pass rule. Each key records its seed, its source, the input hashes and the packet's sha256.
   - Does NOT hide which packet a folder is: the FOLDER NAME says U1, U2 or M. **Give each judge a copy of `packet.jsonl` in a neutral folder holding only the judge instructions. Never a folder named U1, U2 or M, never a key.**
   - Run the judge sessions in the order in `session_order.json`.

5. **Tally.** First `/usr/bin/python3 harness/tally_rejudge.py --selftest` must print `SELFTEST OK`. Then:
   `/usr/bin/python3 harness/tally_rejudge.py --scores-u1 <U1 answers> --scores-u2 <U2 answers> --scores-m <M answers> --key-u1 work/keys/U1.json --key-u2 work/keys/U2.json --key-m work/keys/M.json --setup-map <reply id -> C0/C1/C2> --masked work/masked.jsonl [--orig-scores <001 verdicts by reply id>]`
   - Prints P(c, X), N(c), N, D, T, L(c) for C1, C2 and the control C0, the paired flips among changed replies (per setup and in all), G(c) under U and under M, P(C2) - P(C1) under U and M, the count of changed replies per setup, then the decision lines word for word from the rules.
   - Boundary, as the draft now defines it, printed word for word: within T means |L| <= T; a lean is L < -T; a reverse lean is L > +T. If |L(C0)| > T, "MEASUREMENT FAILED" and the control rule are printed first, and every other number and line still follows, marked as record only.
   - `--orig-scores` shows 001's verdicts as one more column; no number uses them.
   - Refuses (exit 2) on a missing, doubled or unknown id, a `pass` that is not true/false, a key that does not cover every reply once, a reply without a setup, or a key whose recorded `masked_sha256` differs from the `--masked` file given (so the paired flips are counted on the same masked file the packets were built from).
   - The selftest proves: a known lean (L(C2) = -4), a known noise (N = 1, D = 1), the paired flips, the gains, a control moved outside T reported as failed with that line first, a case exactly on the boundary (L(C2) = -1 and L(C0) = +1 with T = 1, both within), a no-lean case, and refusal on a missing id, a doubled id, a non-boolean pass and keys built from another masked file.
   - Does NOT check that the score files came from the right judge session, or the setup map; those are HQ's.

## Things to know
- If any C0 reply was changed by the masking, L(C0) is not a pure "nothing changed" control. The tally prints the changed count per setup so this is visible. In the trial (with a made-up setup map) it is not meaningful; in the real run it is.
- `work/_replies_view.jsonl` (the masker's id/item_id/reply extract) was deleted at the end of the build.
