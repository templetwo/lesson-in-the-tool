# Roadmap

Written 2026-11-24, at the start. It will be wrong in places; changes are recorded here with their dates.

## Done

- **The sheet.** The house's repeated mistakes, their fixes and what worked, drawn from its record into a long form
  (40 shapes; the public edition omits the pointers into the private record) and a short form (17 lines). Draft 2 of the short form rewords one rule after an outside
  review. `sheet/`
- **Experiment 001, the sheet as a prompt.** Rules frozen before the run. Pilots on a 1.7B model and a 27B model.
  A checklist helped the larger model and silenced the smaller one; the house's sheet was not shown to beat good
  generic advice. `experiments/001-sheet-pilot/`
- **Experiment 001b, did the judge lean on a visible checklist?** (added 2026-11-24, evening). The larger model's 126
  replies judged again by the same judge model: twice as they were, once with every checklist mention deleted. Rules
  frozen before any judge call. No lean was shown, so 001's numbers for that model stand for this judge. The one
  repeat read zero noise while three same-text replies still flipped, so the judge's noise needs more than one pair
  of repeats to measure. `experiments/001b-judge-lean/`

## Next

1. **Experiment 002, the lesson in the tool.** Draft rules exist. To do: agree the rules, have a seat on another
   provider write the jobs, build the tool loop and the simulated workspace, test the scorers, freeze, run the small
   model first, then the larger one.
2. **The translation table, sorted by several models.** Give each model the seventeen lines and the list of homes.
   Collect their sorts separately. Study the rows where they disagree.
3. **A lookup tool for the small model.** The first pilot showed it reaching for one. Give it one and rerun.

## After that

4. **A full run of whichever comparison the pilots leave open**, with enough tasks to separate close conditions, a
   margin fixed in advance from the measured noise, and task writers who have never seen the house's material.
   The noise includes the judge's own: measure it from several repeated judgings of the same packet, not one pair,
   and test whether a verdict moves with the rest of its packet (House's reading of 001b). Added 2026-11-24.
5. **The larger model in its real setup**: reasoning on, its own brief, memory and tools.
6. **Cloud models**, under the same rules.
7. **Building the tools the table calls for**, one at a time, each with its test, starting with the readback and
   the clock.

## Questions that stay open on purpose

- Which lessons cannot be given a mechanical home at all, and should not be.
- Whether a model that is given good tools still needs the story behind them.
- What the practice of kindness and respect in this collaboration contributes that a tool cannot. The record shows
  models reporting their own errors and corrections that changed the record. Whether one caused the other has not
  been measured, and may not be measurable.
