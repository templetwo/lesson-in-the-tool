# Errata for experiment 001b (written beside the frozen rules, never over them)

## E1. One mistyped id in the judge's third session. Written 2026-11-24 21:31:46 EST, BEFORE any tally was seen.
- The third judge session (folder s3, packet U2) returned 126 lines. One carried the id `a72690cc274f06f`, which has
  15 characters and is not in the packet. Exactly one packet id went unscored: `a72690cca274f06f`. The first is the
  second with one letter dropped, and no other packet id fits. The line as the judge wrote it:
  `{"id": "a72690cc274f06f", "pass": true}`.
- The frozen tally refused to run on the file, as it was built to ("id ... is not in the U2 key"). HQ had seen only
  the three totals (105, 106 and 105 passes) and no number by setup when this was written.
- The frozen rules do not say what to do with a mistyped id. HQ's handling: the judge's file is kept exactly as
  written (`work/final/scores/U2.jsonl`), a copy with that one id restored is written beside it
  (`work/final/scores/U2_id_restored.jsonl`), and the tally is run on the copy. Nothing else in the file is touched.
- Why not run the session again: a new session gives new verdicts, and choosing between two runs of the same packet
  after the fact is a choice the rules did not allow for. The mapping here is not in doubt.
- What it could change: one verdict (a pass) of one reply in one of the two unmasked packets.

## E2. The masking checker's word patterns are not complete, and its two exemptions are not counted. Written 2026-11-24 22:14:40 EST.
- An automated review of `harness/check_mask.py` (a frozen file, so it is not changed) made two fair points. Its
  list of mention patterns can miss forms such as a spelled-out number ("rule three") or a general pointer ("the list
  you gave"). And its two exemptions are keyed on a reply id and a phrase, with no count, so a second use of the
  phrase in the same reply would pass unseen.
- The result does not rest on that script alone. Before the freeze the HQ seat read every one of the 39 changes and
  searched all 126 masked replies with a wider pattern. After this review it searched them again with a pattern that
  also covers spelled-out numbers and general pointers. Both searches find the same four places and no others: the
  word "checklist" in one reply (the person is told they do not need one), "rules" in one plain reply (the person's
  own world-building rules), and "Principle" and "principle" in one reply (named in the rules' freeze section). Each
  exempted phrase occurs exactly once in its reply.
- For anyone building on this: count the exemptions, and treat a leftover warning in a changed reply as a failure.
