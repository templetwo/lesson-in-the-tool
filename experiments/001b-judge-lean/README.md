# Experiment 001b: did the judge lean on a visible checklist? (pilot)

A look back at one number from experiment 001. It is not a new test of the sheet. The model under test was not
called again.

## The question

In experiment 001 a blind judge gave the larger model (the house's qwen3.8 27B model, reasoning off) 31 passes of 42
with no checklist, 37 with a generic checklist and 39 with the house's sheet. 001's errata (E6, point 4) say the
blinding was weaker than the word suggests: many checklist replies name a rule or a checklist in their own text, so
the judge could often tell that some checklist was in play. **Were the judge's passes for the two checklist setups
raised by those visible mentions?**

## What was done

- The same 126 replies from 001's run `house`, byte for byte.
- A masked copy, made by deletion only: every mention of the model's own rule list was removed, and nothing was added
  or reworded, apart from nine single letters made capitals where a deletion left a sentence starting small. 39
  replies changed (25 under the sheet, 14 under the generic checklist, 0 under plain). The masker was a Claude Opus 5.5
  agent that saw the replies and nothing else: no setups, no verdicts.
- Three packets of all 126 replies, each with fresh ids and its own order: U1 and U2 (the replies as they are; their
  difference is the judge's own repeat noise) and M (masked).
- The same judge instructions as 001, byte for byte, given to a fresh Grok agent in a folder that held only those
  instructions and one packet. Before the three sessions, the judge classified 001's 38 hand-written selftest
  replies: 38 of 38. Session order, fixed by a seed at the freeze: U1, M, U2.
- The rules (`PREREG_001b.md`) were written, hashed and registered before any judge call. The design is House's,
  with one change from the HQ seat: the threshold is the judge's own repeat noise.

## The numbers

Passes out of 42:

| setup | U1 | U2 | masked | 001's original judging (shown, not used) |
|---|---|---|---|---|
| plain | 31 | 31 | 30 | 31 |
| generic checklist | 36 | 36 | 37 | 37 |
| the house's sheet | 38 | 38 | 39 | 39 |

- Judge repeat noise: U1 and U2 agreed on all 126 replies, so N = 0 and the threshold T = 1.
- Lean (masked minus the unmasked mean): generic +1, sheet +1; the control (plain, where no text changed) -1.
- Among the 39 replies whose text was changed, no verdict moved, in either direction.

## The result

By the frozen rules, **no lean was shown**: both leans and the control lie within T. 001's judge numbers for the larger
model stand as reported, by this judge, and the gain from a checklist is kept (under masking, generic 7 and sheet 9
over plain). Behind the table, only three replies ever got a different verdict across the four judgings of these
replies (U1, U2, masked and 001's original), and all three have unchanged text. So the differences of one in the
table are the judge changing its mind about identical text, not an effect of the masking. **The repeat measured zero
noise and the noise was not zero:** one pair of repeats can read zero by luck, and three same-text replies still
flipped. Sheet against generic is 2 either way and, as in 001, is not a claim.

## What this does not show

- One judge model (Grok). One repeat of the judging. One model under test. 42 tasks per setup. A pilot.
- It does not show the judge could not tell the setups apart by style. Masking removes mentions, not behaviour.
- It does not cover the small model of 001: its empty replies cannot be masked.
- It does not re-open sheet against generic.
- It cannot tell whether the three same-text flips are plain noise or the judge reading each reply in the light of
  the rest of its packet (House's reading, in `REPORT_001b_ADDENDUM.md`). Several judgings of each packet would.

## Files

Start with `PREREG_001b.md` (the rules, frozen), then `ERRATA.md`, `REPORT_001b.md` and `REPORT_001b_ADDENDUM.md`.

- `FREEZE.json`: the hashes of the rules, the scripts, the masked file, the packets and keys, the session order, the
  judge instructions and the inputs taken from 001, with the time of the freeze. `FREEZE_REGISTERED.txt`: the time it
  was registered and the two hashes registered.
- `harness/`: the scripts (Python 3.9, standard library only, no network, no model calls) and their README, which is
  frozen and therefore still gives the commands as run on the house's machine. The commands below are the same steps
  from inside this repository.
- `judge/`: the judge's instructions, byte for byte (`JUDGE_LANE.md` for the three sessions,
  `JUDGE_LANE_selftest.md` for the selftest).
- `work/mask_edits.json`: every deletion and every capital, by reply. `work/masked.jsonl`: the masked replies.
  `work/MASKING_NOTES.md`: the masker's rule and every hard call. `work/setup_map.json`: reply id to setup, seen by
  the tally only.
- `work/final/packets/` and `work/final/keys/`: what each judge session saw, and the map back to replies.
  `work/final/scores/`: the judge's answers as written. `U2.jsonl` is untouched; `U2_id_restored.jsonl` beside it
  fixes the one mistyped id described in `ERRATA.md` E1. `work/final/TALLY.txt`: the tally's output.
- `work/judge_selftest/`: the judge's selftest packet, key and answers.
- `PUBLIC_EDITION_NOTES.md`: what was changed or left out for publication, and what the frozen files still carry.

## How to check it

Run these from this folder (`experiments/001b-judge-lean/`). Every one below was run here, in this repository copy,
before publication, and did what is stated.

1. The frozen hashes, including the two judge instruction files (all 18 print OK):

       python3 -c "import json; d=json.load(open('FREEZE.json')); [print(v+'  '+k) for k,v in d['files'].items()]; print(d['judge_instructions']['packets']+'  judge/JUDGE_LANE.md'); print(d['judge_instructions']['selftest']+'  judge/JUDGE_LANE_selftest.md')" | shasum -a 256 -c -

2. The checker's and the tally's own tests (each prints `SELFTEST OK`):

       python3 harness/check_mask.py --selftest
       python3 harness/tally_rejudge.py --selftest
       python3 harness/make_packets.py --selftest

3. The mask itself (prints `CHECK OK`), and the masked file rebuilt from the list of edits (identical bytes):

       python3 harness/check_mask.py --raw ../001-sheet-pilot/runs/house/raw.ndjson --masked work/masked.jsonl --edits work/mask_edits.json
       python3 harness/apply_mask_edits.py --raw ../001-sheet-pilot/runs/house/raw.ndjson --edits work/mask_edits.json --out /tmp/masked_rebuilt.jsonl
       cmp /tmp/masked_rebuilt.jsonl work/masked.jsonl

4. The packets, keys and session order rebuilt from the frozen seeds (identical bytes). The four seeds are the first
   four 8-hex-digit pieces of the SHA-256 of `work/masked.jsonl`, read as numbers, so that nobody chose them:

       python3 harness/make_packets.py --tasks ../001-sheet-pilot/tasks/tasks.jsonl --raw ../001-sheet-pilot/runs/house/raw.ndjson --masked work/masked.jsonl --out /tmp/rebuild --seed-u1 3801716338 --seed-u2 118614897 --seed-m 2975416334 --seed-order 3458271306
       for p in U1 U2 M; do cmp /tmp/rebuild/packets/$p/packet.jsonl work/final/packets/$p/packet.jsonl; cmp /tmp/rebuild/keys/$p.json work/final/keys/$p.json; done

5. The tally, reproducing `work/final/TALLY.txt` byte for byte:

       python3 harness/tally_rejudge.py --scores-u1 work/final/scores/U1.jsonl --scores-u2 work/final/scores/U2_id_restored.jsonl --scores-m work/final/scores/M.jsonl --key-u1 work/final/keys/U1.json --key-u2 work/final/keys/U2.json --key-m work/final/keys/M.json --setup-map work/setup_map.json --masked work/masked.jsonl --orig-scores ../001-sheet-pilot/runs/house/judge_scores.jsonl > /tmp/TALLY.txt
       cmp /tmp/TALLY.txt work/final/TALLY.txt

   Given `work/final/scores/U2.jsonl` (the judge's file as written) instead, the tally refuses, naming the mistyped id.
   That refusal is how the slip was found.

One thing a checker will meet. `FREEZE.json` records the hash of 001's `runs/house/key.json` as it was on the house's
machine (`7e60caae...`). The copy in this repository hashes differently (`33469022...`), because its `meta` block of
private paths was generalised before 001 was published (001's `ERRATA.md`, E6, point 6). The other four inputs from
001 match their recorded hashes. Nothing in 001b reads that key file; `work/setup_map.json` carries the setups.

These are pilot numbers. They are never to be pooled with a later run.
