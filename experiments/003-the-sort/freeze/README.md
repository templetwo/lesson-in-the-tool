# Freeze records: public editions

This directory records five private, machine-local freeze manifests: two withdrawn
predecessors and three lists in force for the main and exploratory side runs.
These records are not an external public preregistration.

`commitments.json` gives each original manifest's full SHA-256, size, recorded
freeze time, status, public-edition SHA-256 and the exact field substitutions.
It also identifies the private coordination-table rows that held the anchors
outside the listed files, with their separate recorded row timestamps. Those
rows are provenance references, not independent public timestamp certification.

The `.public.json` files retain every original per-file hash and filename. Only
`frozen_by` changes: private host/session attribution becomes a research-seat
attribution, and the main replacement manifest's overly broad timing phrase is
narrowed to “before main experimental sorting.” Preliminary probes and the
definition-writing call had already taken place. The unchanged original hash
commits to the original wording; it does not authenticate this corrected edition.

| List | Recorded freeze time (EST) | Status | Files |
|---|---|---|---:|
| First main list | 2026-11-25 22:32:01 | Withdrawn before main experimental sorting | 38 |
| First counting list | 2026-11-25 23:01:41 | Superseded before main experimental sorting | 2 |
| Replacement main list | 2026-11-25 23:47:39 | In force for run 1 | 47 |
| Replacement counting list | 2026-11-25 23:47:39 | In force for run 1 | 2 |
| Side-run list | 2026-11-26 11:14:25 | In force for the exploratory side run | 63 |

The two counting lists commit to identical file dictionaries; their manifest
bytes differ in time and attribution. The side list also commits to copies of
the two run-1 manifests. The alias entries in `commitments.json` map those copies
to the corresponding public editions; they are not extra freeze events or
side-run authorities.

An original manifest hash cannot verify a sanitized manifest. Original per-file
hashes likewise do not verify altered public source copies. Some committed files
are intentionally omitted from publication. Use the package-wide edition mapping
for included, transformed and omitted files; this directory preserves the original
commitments without claiming every committed file is shipped.
