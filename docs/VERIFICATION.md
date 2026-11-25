# Checking the published evidence

From the repository root, with Python 3.9 or later:

```sh
python3 -B tools/verify_archive.py
python3 -B -m unittest discover -s tests -v
```

The verifier also works from another directory or a source ZIP. Use `--root PATH`
to select an archive. It needs only the Python standard library, makes no model
or network calls, and writes its rebuilds to temporary folders. Exit 0 means
every listed check completed; exit 1 means verification failed. The first failure
names its evidence. Earlier `OK` lines are partial progress, not a final verdict.

## What it checks

1. **Publication coverage.** Every regular file must occur exactly once in
   `MANIFEST.sha256` with its current SHA-256. Missing, extra, duplicated, unsafe
   or symlinked entries fail. The manifest itself, root Git metadata, Python
   bytecode/cache files and `.DS_Store` are excluded. This is stricter than
   checking only the paths already listed in a manifest.
2. **Frozen commitments.** Both original freeze records are pinned to their
   published hashes at `19a3017`. All eleven 001 inputs match hashes and sizes.
   All eighteen 001b inputs match; four of its five inputs from 001 match their
   original commitments. Old absolute paths are never followed: inputs are
   resolved within this archive, with an explicit mapping for the short sheet.
3. **The one public-edition exception.** 001's `runs/house/key.json` was
   generalised for publication. Both its original hash and the exact public
   replacement hash are checked. This is printed as `KNOWN EXCEPTION`, never
   silently skipped. A further byte change fails. See 001 E6 and 001b's
   `PUBLIC_EDITION_NOTES.md`.
4. **The evidence joins.** The four scored 001 runs must have unique, exhaustive
   task/condition plans; raw IDs must match keys; retries must follow errors;
   packets must contain exactly their source prompts, pass rules and replies;
   every captured reply must have one valid automatic score and one Boolean
   judge score. Every published count in `PILOT_RESULTS.json` is recomputed.
5. **Preserved failures.** `lfm3` has 130 attempts, seven error attempts and 123
   captured replies, leaving three task/condition pairs unresolved. `lfm3_null`
   has 130 attempts, six error attempts and 124 replies, leaving two unresolved.
   These are the specific gaps documented in 001 E2, not full coverage disguised
   by a smaller denominator. Both house runs have 126 replies and no errors.
6. **Re-judging.** 001b's setup map agrees with 001's house key. Its three packets,
   keys and scores map one-to-one to all 126 original replies. The corrected U2
   score file must differ from the original by exactly the documented E1 ID
   repair and nothing else. Both published judge selftests match the 38 frozen
   examples and expected verdicts.
7. **Reproduction.** Four automatic-score files, the masked replies, three
   packets, three keys, the session order and 001b's tally are rebuilt byte for
   byte. Seeds and judge-folder hashes agree with the freeze. The uncorrected U2
   file must still be refused for its documented typo.
8. **Existing self-checks.** The 001 harness and task checks and all three 001b
   harness selftests must pass. The old 001 selftest writes beside itself and
   references private absolute paths, so a temporary copy is made and only that
   copy's two checklist paths are relocated. The original scripts and frozen
   conditions remain unchanged. The fake transport makes no network calls.

## Why another checker

The manual checks remain useful. This command connects them and adds a check
for missing evidence across files.

One concrete control comes from reviewing frozen `harness/tally.py`: adding a
duplicate planned pair in memory lets its `compute` function return no problems
with 127 expected and 126 captured, while its rendered sentence claims every
planned pair has one reply. The published plan has no such duplicate. This is a
failure of that malformed-input check, not evidence that the reported result is
wrong. The new verifier refuses the duplicate without changing the frozen file.

Tests deliberately damage copies of the archive: duplicate plans or IDs, missing
scores, non-Boolean verdicts, altered packet text, changed totals, a wrong setup
map, an altered U2 correction and changed frozen inputs even after a new manifest
is written. Semantic tests call the evidence checker directly so that an early
checksum failure cannot conceal an untested join.

## What a pass cannot establish

- The real time of freezing or registration, the contents of withheld logs, or
  whether a judge session was isolated. Those claims still rest on the record
  described in the public-edition notes.
- Whether the judge made the right semantic decision, whether masking removed
  every cue, or whether the experiment has enough power. In particular, 001b E2
  remains a limit of its frozen mention-pattern checker.
- Authenticity against someone changing this verifier and all its commitments.
  These are local consistency checks, not an external signature service.
- New model behavior. The verifier reruns deterministic code; it neither repeats
  the models' trials nor upgrades pilots into established results.

Smoke runs and run logs receive manifest integrity checks, not the full semantic
joins applied to the four scored runs. The verifier compares the machine-readable
001 totals and 001b tally; it does not parse every numerical sentence in prose.

## Updating the publication manifest

After reviewing an intentional addition or a change to unfrozen documentation,
regenerate the manifest, then run the verifier. Inspect the manifest diff; a new
manifest is not permission to change historical evidence.

```sh
python3 -B - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, 'tools')
from verify_archive import digest, inventory
root = Path('.').resolve()
lines = [digest(root / name) + '  ' + name for name in sorted(inventory(root))]
(root / 'MANIFEST.sha256').write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY
```

The two freeze commitments remain independent of this manifest update. Changing
them would require changing the verifier's explicit historical commitments too.
