# How this work is done

These rules were not invented for this project. Each one was earned by an earlier mistake in the house this work comes
from, and the first experiment here was run under them. They are written plainly so that anyone, and any model, can
hold us to them.

## Before a test runs

1. **Write the rules first.** The question, the conditions, the tasks, the scoring and what would count as an answer
   are written down before the first model call.
2. **Freeze them.** Hash the rules and every input, register the hashes somewhere that keeps its own time, and read
   the registration back. After that the rules file is never edited.
3. **Show the test can fail.** Every scorer is run first on hand-written replies that should pass and replies that
   should fail. A check that has never failed has not been tested.
4. **Show the pipeline makes no gap.** Run two identical conditions against each other. They must come out the same,
   or the difference tells you how big the noise is.
5. **Stand a baseline beside the thing you are testing.** If the question is "does our own list help", a list of
   ordinary good advice of the same length runs beside it. Without it, any gain could be "a list helps".

## While it runs

6. **Raw replies are the record.** Scores are a reading of them. Both are kept.
7. **The judge is a different kind of model, and blind.** It sees the task, the pass rule and the reply. It never
   sees which condition produced the reply.
8. **Nothing is retried silently.** A failed call is a record with its error.
9. **A pilot is called a pilot.** Its numbers are kept under their own name and never pooled with a later run.

## After

10. **Corrections go beside the original, never over it.** `ERRATA.md` sits next to the frozen rules and records what
    was found, what was changed before a scored run, and what we got wrong when describing the result.
11. **"No difference" is a result.** It is reported as plainly as a win.
12. **State the limits in the same breath as the finding.** How many tasks, how many runs, what was not checked.
13. **Say who is a biased judge.** A model that helped build something is not the one to say whether it is good.
    Reviews from other kinds of model are asked for and published unedited.

## Why the files carry machine paths

The frozen files are published exactly as they were hashed, so the hashes can be checked. Some of them carry file
paths from the machine they were written on. Rewriting them for neatness would break the one property that makes
them worth publishing.
