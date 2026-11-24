# Experiment 001: the sheet as a prompt (pilot)

Start with `PREREG.md` (the rules, frozen before the run), then `ERRATA.md` (what was found and set along the way,
and what we got wrong when describing it), then the two reports: `REPORT.md` for the 1.7B model and `REPORT_HOUSE.md`
for the 27B model.

- `FREEZE.json`: the hash of the rules and of every input, with the time of the freeze.
- `harness/`: the runner, the script scorer, the blind-packet maker, the tally, the selftest, the generic checklist.
  `harness/README.md` has the steps in order.
- `tasks/`: the 42 items, the hand-written replies used to test the scorers, and the writer's own check.
- `runs/`: one folder per run. `raw.ndjson` holds the replies (it never names the condition), `key.json` maps reply
  ids to conditions, `judge_packet.jsonl` is what the judge saw, `judge_scores.jsonl` is what it answered,
  `auto_scores.ndjson` is the script's partial reading. `smoke_*` folders are declared warm-up calls and were not
  scored. `house_temps.log` is the GPU box's temperatures during its runs; every line ends with a false
  "BOX UNREACHABLE" label that is explained in `ERRATA.md` E5.
- `PILOT_RESULTS.json`: the counts behind the tables in the reports.

These are pilot numbers. They are never to be pooled with a later run.
