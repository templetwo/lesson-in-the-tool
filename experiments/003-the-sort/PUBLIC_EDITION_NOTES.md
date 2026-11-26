# Public edition notes: experiment 003, the Sort

This publication edition follows Anthony's direction of 2026-11-26 to put test 1 in the open before his own review
of this folder. Publication is not registration with an outside registry, adoption of the proposed next tests,
or permission for additional model calls. Wording, credit and rulings-file decisions remain his.

HQ reported the following review and search (2026-11-26; helix 83464):

> Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.

## Scope of this publication edition

The checked opening and the researcher's bias question remain as written. Anthony has not yet reviewed the opening,
HQ's draft credit line or the exact wording. Any changes he makes will be recorded as dated errata, not silent edits.
The personal rulings transcript stays out. The initial summary-only proposal was superseded during preparation by
a level (b) projection: sent textual prompts, label maps, visible answers, judgment prose and the metadata needed
for count reconstruction. Provider reasoning and identifiers remain out. Publication does not answer the Stale Door
choices or the four-test addendum questions.

## What is original and what is a public copy

`SOURCE_MAP.json` maps every exported source artifact to its original SHA-256 and byte count and its public path,
SHA-256 and byte count. It also lists generated files, per-file transformations and declared frozen omissions.
For eleven documents, the map records differences from a local candidate that was never published, so the changes to publication-status wording remain visible.
Original hashes identify private originals; they do not vouch for rewritten bytes. New run manifests bind the
public records, and the repository's `MANIFEST.sha256` covers every file in this public edition except itself.
Generated provenance documents do not authenticate provider output or establish independent publication history.

The public transformation map retains original line ranges, the replacement and its reason, but omits hashes and
byte lengths of the original replaced-line spans. Those span details remain in the private work records. Original
whole-file hashes remain published as freeze commitments, so a short replaced value could in principle still be
confirmed by guessing. These replacements are for hygiene, not secrecy. None of the replaced values is a credential.

The report editions contain prose edits beyond their added notices: private session, review and ruling indices
are removed; machine paths, host aliases and operational-receipt filenames become semantic descriptions. The side
report's reference to a private numbered pick becomes a statement that Anthony authorized the follow-up, without
claiming new authority. Numerical results, tables, methodological limits and original manifest/key/tally hash
references remain. Private coordination identifiers are removed from report prose; record numbers retained in
frozen rules pages, tests and `freeze/commitments.json` are pointers into private records, not public evidence of
those records' contents. The reports' "GPU host" is the rules' "local host A" (qwen3.8 27B); "Other local host" is
"local host B" (gemma4).

In both code editions, the `real_callers.py` docstring is also revised: it now says that neither the local
credential-settings file nor its template is included, replacing the original statement that the template ships.

The two code editions remain separate under `code/run1/` and `code/side/`. Their mapping names the applicable
original freeze. Machine-specific paths, hosts and a scanner-test credential basename are generalized. The code's
original runtime and collection instructions are historical; the documented offline helpers perform no model calls.
Credential files and templates are absent. Real collection is not an operation supported or cleared by this publication edition.

Apart from the declared public-edition transformations, the main rules page is preserved as frozen, including its
historical draft opening and dated corrections. Its closing section, "THE RULES IN FORCE", governed run 1.

`freeze/commitments.json` records the three in-force anchors and two withdrawn predecessors. The complete original
per-file hash dictionaries are retained in sanitized manifest editions. The attribution field changes are declared;
the replacement main-freeze wording is narrowed from a before-any-call claim to before main experimental sorting,
because probes and definition writing had already occurred. The two side-folder copies of the main freezes map to
the same public editions. An anchor outside a frozen file list here means a private coordination-table record,
not external public preregistration or a certified timestamp. Freeze strings and later table-row times stay distinct.

In `results/comparison.json`, each active source `sha256` now identifies the public tally used by this edition.
The historical tally-file hash is retained separately as `original_sha256`, an informational commitment to the
different original bytes read by the original comparison.

## Projected model record

The public edition preserves 24 main-run trials and three side-run trials, all 27 saved prompt files, and 50 recorded
sent calls (44 main, six side). All failed, incomplete and unsent entries retain their recorded identities and
denominator consequences. The two incomplete DeepSeek replies stay null with empty visible partial text; reasoning
is never substituted for an answer. Every visible first reply, follow-up reply, parsed judgment sentence and saved
prompt/question string is unchanged by the projection. Local provider labels are consistently generalized in
metadata and configurations, including dictionary keys.

All 50 raw provider bodies are replaced by the status/incomplete-reason projection. Numeric settings and numeric
usage, including reasoning token counts, are retained. Twelve Anthropic usage objects lose nonnumeric metadata.
The structural review checked that the retained complete replies equal the provider-visible answer blocks and
that provider identifiers and hidden payloads do not remain in these projected records.

HQ reported the following review and search (2026-11-26; helix 83464):

> Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.

The saved prompt files contain the first prompt and follow-up question. They do not contain the full serialized
second request. The source callers show how prior state was used, but omitted reasoning and provider continuation
identifiers prevent an exact wire-request replay. The public record supports recomputing saved-answer analyses,
not repeating the original provider conversations or recovering private reasoning.

## Declared omissions

- `key_sources.local.json`: never read, hashed or included; it is not a frozen input.
- Credential-location templates: withheld unread; their original freeze-list hashes remain in the omission map.
- The rulings transcript: personal texts are withheld. Applicable decisions already stated in the checked write-up
  remain there; this does not release the transcript.
- Provider reasoning/thinking text, reasoning summaries, signatures, encrypted content, request/response/account
  identifiers, fingerprints, arbitrary metadata and account/billing/access-program objects: omitted from raw bodies.
- Nonnumeric service/geography usage metadata: omitted; numeric counts and durations remain.
- This machine's filesystem paths, network addresses and host labels: replaced as recorded per file. The notes
  give replacement classes and whole-file commitments, not original-span hashes or byte lengths and not a second
  copy of the private literals.
- Smoke/preflight outputs and development runs: not part of this two-run evidence package.
- Internal build/readback documents, superseded draft settings and the definition writer's original response:
  omitted; the active frozen settings, used definitions, checked reports and corrections are present.
- Private coordination/Stack/log bodies and superseded report/code revisions: omitted. Freeze commitments and
  explicitly attributed chronology remain, without claiming independently certified timing.
- Complete serialized second requests: not present in the saved prompt format and not invented for this edition.

The JSON omission map identifies each excluded in-force frozen file and preserves its recorded original hash.
An omitted file has no public hash or public size. A null original size means the bytes were not opened for this
export; it is not a zero-byte file. Older 001/001b archives were already public and remain byte-for-byte unchanged.

## Reconstruction and checks

From the repository root:

```sh
python3 -B experiments/003-the-sort/tools/reproduce.py
python3 -B tools/verify_archive.py
python3 -B -m unittest discover -s tests -v
```

The 54 tests run by the root unittest command are the repository's existing suite. They still pass with 003 added,
but they do not test experiment 003. The separate 003 reconstruction helper and reviewed offline subsets supply
the experiment-specific checks described in `CHECKS.md`.

The 003 helper validates public manifests, reconstructs all 27 prompt/question texts and label/home maps from
saved seeds, reparses visible answers, and reproduces all semantic tally fields using each run's code edition.
That covers majority classifications, agreement and bootstrap outputs, stability, house comparisons, judgment
parsing and provider-reported limit endings. It reconstructs the side comparison: 13 matches, three differences
and one missing majority among 17 lessons. It validates current public input hashes while treating explicitly
named original hashes and historical paths/timestamps as provenance, not as active public-byte commitments.

The helper checks that the public files agree with each other; it cannot show they are what the models returned.
HQ's second verification reader reported changing a judgment sentence in a disposable copy, refreshing the chain
of dependent hashes and observing the helper pass (helix 83477). That is the expected limit of internal agreement,
not an authenticity check. The helper's sent-call figures are labeled as reported and not independently checked.

It does not generate new model answers, establish that the judgments are correct, reproduce full second requests,
recover withheld reasoning-character lengths, authenticate freeze times or verify invoice/pricing arithmetic.
The price estimates remain estimates; no invoice is supplied. The published numeric usage permits further
inspection but is not independent proof of billing.

The root archive verifier reconstructs 001/001b and checks manifest integrity for 003. The separate 003 helper
supplies the additional reconstruction above. `CHECKS.md` records the commands actually run and their observed
results.

HQ reported the following review and search (2026-11-26; helix 83464):

> Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.
