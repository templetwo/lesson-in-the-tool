# Corrections retained with the checked reports

This is a short summary of corrections documented in the [run-1 report](run1_report.md) and
[side-run report](side_report.md). Superseded reports, private review records and operational logs are not included.
The classification tallies did not change. Some descriptions of the results, reported usage and estimated costs did.

## Run 1

- The first experimental freeze was withdrawn after review found missing output-cap settings and agreement statistics
  computed for the local pair against the rules. The implementation was corrected before the main sorting run.
- The second guess applies to all eight models: six passed its criterion and two failed it. Failed repeats prevented
  majorities for DeepSeek and gemma4; that does not demonstrate disagreement between readable answers.
- The repeat-consistency count means no three identical valid repeats, including failed repeats. It does not mean
  three different answers. Alpha describes the 84 available majority ratings out of 102 planned; its interval
  resamples lessons, not models or failed collection.
- House-table exact and overlap counts are separate. Missing majorities remain in the planned denominator. The
  comparison does not isolate an authorship effect. Retrieval was absent from the group modal homes, not every
  individual assignment: Opus chose it on lesson 11.
- Anthropic reported reasoning separately; the initial usage summary missed that field. The revised report also
  identifies the unit of xAI's reported charge and narrows the small preflight-call cost estimate.
- Statements about reasoning quantity, limit effects, local context and xAI's second-turn accounting were narrowed
  to the observed fields. No absence of a reported cutoff proves absence of a limit effect; the accounting pattern's
  cause remains unresolved. Costs are estimates or provider-reported amounts, not inspected invoices.

## Side run

- Lesson 4 has no majority home because its three readable answers gave tool, harness and check. No answer is missing.
- The reference cloud modal uses five available model majorities on sixteen lessons and four on lesson 4. The
  original six-model roster and all seventeen comparison lessons remain in their respective denominators.
- The observation that DeepSeek's majorities on lessons 11 and 15 match Opus's earlier majorities is explicitly a
  descriptive observation made after looking at the side results, outside the frozen modal-home comparison.
- The revised cost calculation separates cached and uncached input tokens: about $0.17 at off-peak list prices or
  $0.34 at peak prices. The earlier $0.35 peak estimate treated all input as uncached; no invoice was inspected.

Public-edition omissions and transformations are documented separately in
[PUBLIC_EDITION_NOTES.md](../PUBLIC_EDITION_NOTES.md). Offline reconstruction of the public analysis passed within
the [documented scope](../README.md#public-edition-and-reconstruction). Complete original provider replies are not
included. Later corrections will be recorded as dated errata.

Before publication, an independent reader (a Claude Opus agent working for the HQ seat, on 2026-11-26) read every model-written string in the 27 result files, by its count 27 sorts and 391 judgment sentences, together with the human-written documents of this folder, and reported no private content in the model text. The HQ seat separately searched every file of this folder for the four provider keys and any 8-character piece of them, and for home paths, user names, private network addresses, host names, e-mail addresses, phone numbers and provider identifiers, and found none. One read and one search are not a guarantee. If you find something here that should not be public, please open an issue.
