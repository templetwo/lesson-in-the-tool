# Checks of the publication edition

The six commands below were run on 2026-11-26 in the new publication-edition folder after the status update and
before the subsequent privacy-review fixes, with Python bytecode writes disabled. All completed with exit 0. Temporary test outputs were kept outside the
checked tree. These verification commands made no provider/model requests, and the real-call switch was absent.
No credential source file or template was read. The recorded logs and their hashes confirm the results below.

| Working directory | Command | Observed result |
|---|---|---|
| Repository root | `python3 -B experiments/003-the-sort/tools/reproduce.py` | 24 main and 3 side trials; all 27 prompt/question texts and maps reconstructed; both complete tally comparisons pass; side comparison 13 match, 3 different, 1 missing. |
| Repository root | `python3 -B tools/verify_archive.py` | Full manifest coverage; frozen 001/001b commitments and documented exception pass; their deterministic reproductions and negative control pass. |
| Repository root | `python3 -B -m unittest discover -s tests -v` | 54 tests pass: the existing repository suite still passes with 003 added; it does not test experiment 003. |
| Repository root | `python3 -B -m lesson_tools` | Six local demonstrations complete, including true success, contradicted claims and unavailable evidence. |
| `experiments/003-the-sort/code/run1` | `python3 -B check_public_offline.py` | 58 tests across four reviewed offline modules pass; no boundary violation. |
| `experiments/003-the-sort/code/side` | `python3 -B check_public_offline.py` | 58 tests across four reviewed offline modules pass; no boundary violation. |

The two 58-test runs are selected offline subsets, not the full historical collection suites. Omitted credential
templates, original Git working-tree paths and historical working files are not silently reintroduced to make
the old full suites run. The public reconstruction checks exercise the actual projected records instead.

Four additional controls were run earlier on disposable copies: a missing result is refused; an altered parsed
row is refused even with its manifest hash refreshed; an altered label map is refused even with its manifest
hash refreshed; and an attempted file deletion is blocked while the sentinel file remains. These earlier controls
were not rerun for the publication-status update and did not modify the checked package or its source records.

The earlier structural projection audit checked 27 results, 27 prompt files and 50 recorded calls. All visible reply,
partial-text and prompt/question strings remained unchanged; all 380 numeric usage leaves and all 50 settings
objects were retained. Public manifest and prompt/input links were checked. Hidden provider payloads and checked
identifier values were absent. That separate audit was not rerun for the publication-status update. It is field-level
verification, not a semantic privacy clearance for the prose.

The root manifest is regenerated using `digest` and `inventory` from the repository's own `tools/verify_archive.py`.
After adding the final provenance/check documents, the verifier is run again against the resulting manifest;
the separate file inventory supplied for review names exact hashes and byte counts. The manifest does not hash
itself, and internal consistency does not establish an independently published commit.

The 003 helper compares all semantic tally fields while excluding only explicitly named historical timestamps,
original-source provenance fields and the public comparison's explanatory suffix. It checks new public hashes
and normalizes only archive-relative versus computed absolute paths. It does not reconstruct provider responses,
full serialized second requests, withheld reasoning-character lengths, invoice/pricing arithmetic or freeze-time
authenticity. It checks internal agreement of the public files, not that they are what the models returned. The
coordinated judgment-text/hash-chain change reported by HQ's second reader is described in `PUBLIC_EDITION_NOTES.md`;
it is not an additional control run by this document's editor.

After the privacy-review corrections, generalized credential-filename guards and reported-call label change,
all six listed commands were rerun on this publication edition and passed again: reconstruction, archive
verification, the 54 existing repository tests, six demonstrations and both 58-test offline subsets. Focused
checks of the generalized guards also passed 30 synthetic-file cases. The earlier projection and four mutation
controls remain earlier receipts for the unchanged evidence; they were not rerun in this pass.

HQ reported the following review and search (2026-11-26; helix 83464):

> Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.
