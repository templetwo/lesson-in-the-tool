# Public code edition

This folder preserves the frozen experiment's runtime source, tests, fixtures,
selected settings, definitions and rules, with recorded publication changes.
It is not byte-identical to the collection freeze and is not a paid-call package.
The public export mapping records original and public hashes, omitted frozen
entries, and the exact changed line spans without repeating private locations.

Private repository paths became edition-relative paths. Machine labels became
`local-a` / `local-b`; local endpoints use reserved `example.invalid` addresses.
The model IDs, requested settings, scoring algorithms and original commit pins
are retained. Main-run and side-run code are separate versions.

From this folder, run the reviewed offline subset:

```sh
python3 -B check_public_offline.py
```

The helper refuses a present `SORT_REAL_CALLS` variable, installs the original
fake-I/O tripwires, and blocks network access, subprocesses, writes, credential
settings reads and reads outside this edition, the Python standard library and its OS randomness device.
It tests response finalization/redaction, call budgets, reported-usage stopping
and output-limit payloads. It is a publication helper, not an original test.
It does not run the complete historical suite or reproduce the experiment tally.

The full historical tests and selftest are included for inspection. Git-backed
checks require commit `441752c` in a Git checkout; this archive has no Git
metadata. A credential-template presence check also requires an intentionally
omitted template. Source-specific default-behavior hash fixtures are preserved,
not regenerated to bless changed public paths or machine aliases. No test is
rewritten merely to pass these publication omissions.

Collection/tally/comparison configurations retain their historical settings.
Their original relative run paths are not a runnable collection configuration.
The separate `../../tools/reproduce.py` publication helper overrides only run,
house-table, comparison and output-location settings in memory; it never runs
collection. It verifies the sibling public run projections, rebuilds prompt
bytes and maps from saved seeds, reparses visible answers, and compares complete
tally fields and the side comparison. Run it from this folder with:

```sh
python3 -B ../../tools/reproduce.py
```

The sibling `records/` folders contain publication projections of visible
answers, judgment prose, sent prompts, maps and required usage/status metadata.
Full provider response bodies, reasoning text, credential settings/templates,
private machine locations and original collection directories are withheld.
Historical rulings and working readbacks are also outside this code export.
Original source comments can refer to omitted files or to the build's historical
state; those comments do not describe a complete paid-call environment here.
Reproduction verifies the published projection, not withheld response-body
completeness, original provider authenticity, price arithmetic or privacy clearance.
