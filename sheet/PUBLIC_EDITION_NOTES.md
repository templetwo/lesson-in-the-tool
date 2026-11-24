# Notes on the public edition of the long form

Written 2026-11-24 17:19:39 EST by a Claude Opus 5.5 reviewer working for the HQ seat. The time was read with `date`.

## What the public edition is

`SHEET_LONG_PUBLIC.md` is a public edition of the house's private long-form sheet of mistakes, fixes and what worked.
It keeps all 40 shapes of the private draft (28 kinds of mistake, 12 kinds of thing that worked), in the same order,
with the same plain names and the same episode counts. For each shape it gives the episodes that are safe to publish,
how the mistake was caught, and the fix or rule as the draft states it.

It is an edition, not a new analysis. No shape was added, no episode was invented, and no rule was made stronger. The
reviewer who made it did not re-check any event against the record.

## What is withheld, with hashes

The private originals are not in this repository. Their SHA-256 hashes, computed with `shasum -a 256` and written into
this file by the command that computed them:

| file | bytes | SHA-256 |
|---|---|---|
| `SHEET_DRAFT.md` (the private long form) | 37328 | `5380274a00bb166866b55dcd643a7afb4758fef4a253a27595a8451ad1daaa40` |
| `RESULT.md` (its drafter's coverage report) | 13066 | `1f1da9a5e8491ee9ee9c01b7f5492650dd8051a7b673be3266926d6ee8e2b6c9` |

These are the same hashes that `PROVENANCE.md` lists for them.

## What was removed or generalised, by category

Counts only. No removed content is described.

**Removed outright**
- Pointers into the private record: all 40 "Pointers" lines, 115 pointer items in all, by script count. No pointer
  was replaced. Where an episode already carried a date, the date stays.
- The draft's "Closes" column (how many monthly summaries of working sessions carry each shape). It is a figure from a
  private summary, and this edition does not carry it.
- Whole episodes, 7 in all, across 4 shapes: security and account matters, 4; protected material, 3. One shape (26)
  is left with no episode, and says "episodes withheld".
- One sentence of one rule (shape 26): security and account matters.

**Generalised (the episode stays, a detail is made general)**
- Security and account matters (logins and keys, permissions, how the house is defended): 9 episodes.
- Money: 1 episode (an exact amount).
- Names of internal tools, services, message channels, record surfaces and the startup routine, replaced by plain
  descriptions: 24 episodes, 1 rule sentence (shape 1) and the opening of shape 1. Counted by hand.
- Wording: in 15 places where the draft described a program or a seat turning something down or marking it, this
  edition says "rejected", "declined" or "marked". One of these is in a shape name: W2 says "stores that reject"
  where the draft's name used a different word.

**Corrected**
- One cross-reference: the draft's shape 28 says "see What worked 10", which is the shape about gates. The shape it
  plainly means is W9 (reading the driver source for the GPU). This edition says W9.

## Where the private draft came from

The drafter, a Claude Opus 5.5 agent, read the house's record on 2026-11-24. In general terms its sources were: the
closing summaries that working sessions write and their periodic digests; a ledger of caught errors; a catalog of the
ways the house's own instruments have given false readings; the house's written operating procedures; and a small
store of recorded learnings.

## What the drafter had already left out

Before this edition, the drafter skipped 17 items for privacy and counted them by category: family, 4; personal
finance, 4; credentials, 5; protected material, 3; personal schedule, 1. None of those items is in the private draft,
so none can be in this edition.

## Limits, as the drafter stated them

- About 50 of the record's roughly 2,400 domains were opened. Shapes that live mostly in the unread part will be
  undercounted or missing.
- The episode counts are the drafter's own.
- Most episodes come from Claude seats on one machine. Errors by other models appear mainly when a Claude seat wrote
  them down.
- The underlying events were not re-verified. The draft reports what the record says.
- Dates on some entries are the date they were written down, not the date of the event (marked "undated" here).
