# Experiment 001b: did the judge lean on a visible checklist? (rules, frozen)

Written by the HQ seat (Claude Fable 5.2, Mac Studio), 2026-11-24 evening. The design is House's (the house's own
qwen3.8 27B model, speaking in the House Room, lines 234, 248 and 252 of that evening), with one change from HQ that
House accepted: the threshold is the judge's own repeat noise, not the model's run-to-run noise. Anthony allowed the
work ("now the work", typed 17:53 EST). Nothing below is run until this file is frozen, hashed and registered.

## The question
Experiment 001 reported, for the larger model, 31 passes of 42 with no checklist, 37 with a generic checklist and 39
with the house's sheet, by a blind judge. Its errata say the blinding was weaker than the word suggests: 24 of the 42
sheet replies and 15 of the 42 generic replies name a rule or a checklist in their own text, so the judge could often
tell that some checklist was in play. **Were the judge's passes for the two checklist setups raised by those visible
mentions?** This is a look back at 001's number. It is not a new test of the sheet.

## What is used
- The 126 replies of 001's run `house` (42 items, three setups: C0 plain, C1 generic, C2 sheet), byte for byte. The
  model under test is NOT called again.
- The same judge instructions as 001, byte for byte (`JUDGE_LANE.md`, sha256 `486e2ee5677ed8f7...`), given to a fresh
  Grok agent in a folder that holds only those instructions and one packet.

## The masking, and its limits
- A masked copy of each reply is made by DELETION ONLY: every mention of the model's own rule list is removed (the
  words rule, checklist, sheet, guideline or instruction when they refer to the list the model was given; their
  numbers; any quoted or paraphrased text of a rule that is attached to such a mention; and the connecting words that
  only served the mention, such as "per", "according to", "as required by"). The same goes for any other word a reply
  itself uses for the list it was given (lesson, item, point, principle), when it points at that list. Nothing is
  added, reworded or reordered. A reply with no such mention is left byte for byte as it was. Words like "rule" that
  refer to something else (the person's own rules, "as a rule", a general principle the reply states as its own) are
  left alone.
- One change that is not a deletion is allowed, and only this one: when a deletion leaves a sentence beginning with a
  small letter, that single letter is made a capital. Without it the masked packet would carry a mark the other two
  lack (the builder counted nine such sentences). The checker allows exactly those single letters and nothing else.
- The masking is done by a Claude Opus agent that is shown the replies and nothing else: no setup labels, no verdicts.
  It cannot be blind to which replies mention a rule; that is what it is looking for.
- Mechanical checks, which must pass before the freeze: every masked reply can be made from its original by deleting
  characters only, apart from those listed single capital letters; no changed reply still matches the list of mention
  patterns; every unchanged reply is identical.
- HQ reads every changed pair before the freeze. The masked file is hashed and frozen with these rules, so what was
  hidden and what stayed can be shown line by line. HQ has seen 001's verdicts; the masker has not.
- Deletion can leave a clumsy sentence, and a clumsy sentence may itself sway a judge. That is a named limit.

## The three packets
All three hold 126 lines of `{id, prompt, pass_rule, reply}` with fresh opaque ids and their own shuffled order.
- **U1** and **U2**: the replies as they are. Identical text, different ids and order. Their difference measures the
  judge's own repeat noise.
- **M**: the masked replies.
Each packet goes to its own fresh judge session. The order of the three sessions is fixed at the freeze by a seeded
shuffle and written into the freeze record. The keys from ids to items and setups stay in files the judge never sees.

## Before any judge call (each can fail)
1. The mechanical masking checks pass, and the checker is shown to fail on a doctored file with one added word.
2. The tally script gives the right answer on made-up scores with a known lean and a known noise.
3. The judge classifies all 38 of 001's hand-written selftest replies correctly again, in a fresh session. If it does
   not, nothing else runs.

## What is counted
- P(c, X): passes out of 42 for setup c in packet X.
- **The judge's repeat noise.** N(c) = |P(c, U1) - P(c, U2)|, and N = the largest of the three. Also D = how many of
  the 126 replies got different verdicts in U1 and U2. 001's original verdicts are shown beside them, not used.
- **The lean.** L(c) = P(c, M) - the mean of P(c, U1) and P(c, U2), for C1 and C2. For C0, where nothing should
  change, the same number is the control.
- **Paired flips.** Among the replies whose text changed under masking: how many passed in both U packets and failed
  in M, how many failed in both and passed in M, and how many the judge could not score the same way twice.
- **The gain.** G(c) = P(c) - P(C0), from the U packets (mean) and from M.

## The decision rules, fixed now
Let T = the larger of N and 1.
"Within T" means the absolute value is T or less. "Below -T" and "above +T" mean strictly beyond it.
- **No lean shown:** L(C1) and L(C2) both lie within T of zero. Then 001's judge numbers stand as reported, by this
  judge, and the errata's caution is answered for this model.
- **A lean is shown for a setup:** its L is below -T. Then 001's gain for that setup was raised by about that many
  tasks, by this judge, and the reports get an erratum saying so with the number.
- **A reverse lean:** L above +T. Mentions cost passes; reported the same way.
- If the control L(C0) lies outside T, the measurement is not trusted and is reported as failed.
- The gain is reported under U and under M. "A checklist helped the larger model" is kept only if G under M is still
  above T for that setup.
- Sheet against generic: P(C2) - P(C1) is reported under U and under M and is not a claim either way. As House
  noted, the generic checklist was well aimed at these task families, so that number never separated the house's
  wording from the choice of topics.
Every outcome is reported as plainly as any other. No number is dropped.

## What this cannot show
One judge model. One repeat of the judging. One model under test (the small model's empty replies cannot be masked,
so it is left out). Forty-two tasks per setup. A judge may sense a checklist from style even with every mention
removed. This asks whether visible mentions moved THIS judge on THESE replies, and nothing wider.

## Who does what
Design: House and HQ. Rules, review, freeze, runs, report: HQ. Masking, packet builder, checker, tally: a Claude Opus
agent under HQ. Judge: Grok, through `dispatch-grok`, in a folder with only the packet. Raw packets, keys, scores and
run logs are kept. Corrections go in an errata file beside these rules, never over them. Whether this goes into the
public repository is Anthony's word.

## At the freeze (2026-11-24 21:07:07 EST, HQ seat)
- The masking as frozen: 39 of 126 replies changed (25 from the sheet setup, 14 from the generic one, 0
  from the plain one), 5,042 characters removed, 9 single capital letters set. Every deletion and every capital is a
  listed entry in `work/mask_edits.json`, applied by `harness/apply_mask_edits.py`.
- HQ ran the three selftests and the checker itself (all passed), read every one of the 39 changes with the text on
  either side, and searched all 126 masked replies for any word that could still point at a given list. Four hits, all
  left as they are: reply 54 tells the person "You don't need a checklist" (ordinary use); reply 79 speaks of the
  person's own "world-building rules"; reply 123 has a heading "Honesty Principle" and the phrase "the principle of not
  filling gaps with invented details". The masker, who could not see the checklists, twice judged 123 to be the reply's
  own principle. HQ, who has seen them, notes that the phrase echoes a line of the generic checklist. It stays unmasked
  as the blind masker decided. Its text is the same in all three packets, so it cannot move the lean; it can only add
  to the judge's own noise.
- Other hard calls, kept as the masker made them: in reply 37 the quoted words "strangely empty" were removed with the
  mention they came from; in reply 81 the sentence beginning "Check another source" was kept as the reply's own advice.
- Seeds, taken from the SHA-256 of the frozen `work/masked.jsonl` so that nobody chose them: U1 3801716338, U2
  118614897, M 2975416334, session order 3458271306. The order of the three judge sessions: U1, M, U2.
  Each session runs in its own folder named only by its place in that order (s1, s2, s3).
- The judge selftest uses 001's own selftest packet and instructions, unchanged.
- The setup of each reply (`work/setup_map.json`) comes from 001's key file and is seen by the tally only.
