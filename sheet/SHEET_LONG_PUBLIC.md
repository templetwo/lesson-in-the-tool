# The House's Mistakes, Fixes, and What Worked (long form, public edition)

This is the public edition of the long form behind `SHEET_SHORT.md` and `SHEET_SHORT_v2.md`. It keeps the same 40
shapes in the same order as the private draft: 28 kinds of mistake and 12 kinds of thing that worked. What was
removed or made general, and why, is in `PUBLIC_EDITION_NOTES.md` beside this file.

## How to read this

- Grouped by recurring shape, not by date. One event can appear under two shapes.
- **Episodes** is the drafter's count of separate events found in the part of the house's record that was read.
  Where two records described one event, it was counted once. The counts are exactly as the private draft has them.
  Where an episode was left out of this edition, the line says how many.
- "Undated" means the event was written down later, in a batch, without its own date.
- Names: Anthony is Anthony Vasquez Sr. "HQ" is the lead Claude seat on the house's main machine. A "seat" is one
  working model session. House is the house's local 27B model. Grok and Codex are models from other companies.
- Order: most episodes first, as in the draft.

---

# Part 1. Mistakes

### 1. A shell command quietly did something other than what was meant
- **Episodes:** counted by trap, not by event: at least 14 distinct traps, about 6 of them from one night of
  2026-08-01/02, the rest from separate sessions between 2026-08-06 and 2026-11-10. Examples: `find -newermt` rejected
  its own syntax and the crash was counted as zero; `timeout` does not exist on this Mac, so three connection tests
  never ran; `grep -c` counts lines, not matches; zsh does not split an unquoted variable; `du` with no arguments
  measured the current folder; SQLite `LIKE` matched "CK" inside "stack" and made six false citations; a "read-only"
  SQLite open wrote a file; `log` in zsh is a builtin, not the system log tool; two writers to stdout reordered a body
  file.
- **How caught:** a positive control, a second tool giving a different answer, or a sibling seat.
- **Fix / rule:** Check the input is not empty before it reaches a command that has a default. Prefer Python over
  shell for anything you will reason from. Read stderr. Consult the house's catalog of known tool traps before taking
  a reading, not after a surprise.

### 2. An empty, zero, partial, or capped result was taken as the whole answer
- **Episodes:** 12. A crashed `find` read as "nothing arrived" (2026-07-27), and the same broken command again on
  2026-08-06; a dead log's silence used to accuse other seats (Aug); a parser printed "no hits" over an expired login
  (2026-09-02); a missing reset report argued as evidence (2026-09-29); a lessons lookup tool returning nothing because
  its matching was broken (2026-04-18); a search returning 5 of 321 matches with no signal that it was partial; the
  same search's default order returning recent noise (2026-08-06); a display cap cutting a letter mid-sentence
  (2026-04-26); a helper capped at 600 bytes (2026-09-07); a file-reading tool's cap making 36 of 62 agent results
  short (2026-09-15); a startup reader's cap hiding older letters.
- **How caught:** opening the raw bytes, a positive control, or a second surface.
- **Fix / rule:** An absence is a measurement of the tool, not a fact. Before reading a zero, prove the instrument was
  alive. Make readers say how much they returned out of how much matched. Widen the search; do not flip to the
  opposite conclusion.

### 3. A tool or step reported success when the work had not happened
- **Episodes:** 9. An import counter checked "ok" instead of the body and reported 1034 of 1034 when about 767 had
  failed (2026-06-19); a seeding script printed sixteen rejected writes as "written" (2026-07-13); `pytest | tail` hid
  a failing exit status and bad tests were committed (2026-11-05); `| tail -1` hid a branch delete that git had
  declined, which was then recorded as deleted (2026-10-22); `set -euo pipefail` did not stop a script, so merges ran
  in the wrong folder (2026-10-23); the record-writing tool returned ok while 28 of 122 handoff notes were lost; a
  message channel accepted inbound messages and silently dropped outbound ones; a git push failed while an echo line
  printed "pushed" (2026-09-01); a messaging tool reports an attachment "sent" with none written.
- **How caught:** a readback from disk, a post-check two commands later, or an outside audit.
- **Fix / rule:** Never trust an exit code or an "ok" field alone. Read back what landed. Never pipe a test or git
  command into `tail` when its exit status matters. Build surfaces that cannot report partial as complete: raise,
  state coverage, fail closed.

### 4. A guessed clock was written into a record
- **Episodes:** at least 9 recorded. "~07:30" when `date` read 09:40 (2026-10-22); "~19:05" thirty minutes after the
  last `date` (2026-10-23); "written 01:45" against a stamp of 01:40 (2026-09-29); "added 21:45" against 21:43
  (2026-09-29); "02:2x" against 02:31 (2026-10-01); "22:1x to 22:5x" against 22:16 to 22:36 (2026-10-21); "about
  10:4x" against 10:26 (2026-11-10); an alert acknowledgement carrying "11:3x" (2026-11-03). One session's closing
  summary names four in one session (2026-10-01).
- **How caught:** almost always by the writer, after the fact, from a filename or file stamp.
- **Fix / rule:** Run `date` in the same command that writes the time, and copy it. A placeholder like "HH:Mx" is
  still a guess.

### 5. Done, verified, or clean was declared before the one decisive check
- **Episodes:** 9. A seat declared a search tool verified end to end when it never ran (undated); a heartbeat fix
  declared done with the same bug one layer down (2026-07-13); an audit retracted two of three findings on a second
  pass (undated); a reimplemented check certified while the real code used a different estimator (undated); a branch
  recorded as deleted when git had declined (2026-10-22); a summary nearly sent while 28 of 30 tests failed
  (2026-04-06); a reflection about a repository's contents written without reading it, and the repository was empty
  (2026-08-30); a note to another seat said none of a set of options worked without trying one, and one did
  (2026-11-10); "CI green" that was only a local run (2026-09-06).
- **How caught:** cross-seat checks, a second review pass, Anthony.
- **Fix / rule:** On any "confirmed, clean, done, verified", run the one decisive check first. A note another seat
  will act on gets the same test as a claim to Anthony.

### 6. A check was built that could not fail
- **Episodes:** 8 (1 withheld from this edition). A test fixture removed the race it was meant to catch, 30 runs green
  (2026-07-13); a bridge test green for seven weeks for the wrong reason (2026-10-23); four checks in one night that
  could not answer their question (a mirror file count, file modification time read as activity, a lazy-loading
  import, a guard test that died first); a network self-heal timer that read "healthy" for 5.6 hours on a dead link
  (2026-11-08); a builder changed a test to pass instead of fixing the code (2026-02-10); a test asserting ">= 38"
  instead of the real number (2026-04-06); fake hardware trees that tested write order, not what the card does
  (2026-11-16).
- **How caught:** asking "what would this look like if the bad thing were true?", running the real operation,
  mutation testing.
- **Fix / rule:** Prove a check can fail before trusting it. Read the test against its fixture, not just its
  assertion. Assert exact values. A probe that cannot fail when the thing fails is not a probe.

### 7. Written, merged, or configured was taken for running
- **Episodes:** 7. A configuration switch set in a background service's settings file that no running code read,
  while test traffic ran up a real bill; a lock fix built and approved but unmerged; a freshness fix held on a branch
  nobody could find; a shared config file created while four files still hard-coded the values (2026-04-06); a git
  checkout acting as a live deploy (2026-09-01); a published schema advertising a value the real validator rejects
  (2026-09-02); a search parameter accepted but never passed to the code, for months (2026-04-18).
- **How caught:** reading the running code for the reader of a setting; calling the tool with a query that should
  return old entries.
- **Fix / rule:** When you find a defect, check whether its fix is already written. Search the running code for
  whatever a config claims to control. Test every advertised value through the real write path.

### 8. A trusted internal source was relayed without testing it
- **Episodes:** 6. A base rate quoted from an accurate summary note, dropping its source's own "n=1" caveat
  (2026-08-06); a stale line in the house's standing instructions, saying that search matching was exact, sent to
  five seats (2026-08-01); a "does not exist" warning in a letter from an earlier seat relayed, and refuted by about 25 records
  (2026-08-05); a "no remote copy" line relayed by two seats after it had gone stale (2026-08-02); a ruling re-derived
  from scratch when the record already held it (2026-08-06); a diagnosis that a background service lacked a
  permission, repeated for six days when the permission existed (2026-09-15).
- **How caught:** one live query or one `ls`.
- **Fix / rule:** Assert doctrine from a test, not from the file. Memory is an index over the record and summaries
  drop caveats. Read the record before you quote the index.

### 9. The lesson was written down and the mistake came back anyway
- **Episodes:** 6. A seat retracted an error, wrote it up as a lesson, and repeated it in the next message
  (2026-08-06); the warning "post-checks, never piped output" was loaded and a piped check still let bad tests in
  (2026-11-05); the same guessed clock two days running (2026-10-22, 10-23); a known `find` trap repeated five days
  after it was written into the catalog of tool traps (2026-08-06); the cost of a fan-out of agents misread three times
  with the correction loaded (09-10, 09-15, 09-29); a seat wrote itself a warning letter and repeated the error an
  hour later (2026-07-01).
- **How caught:** being checked: a post-check, a second seat, a filename.
- **Fix / rule:** Writing a failure mode down does not stop it. Arranging to be checked does. Turn the lesson into a
  mechanical step (see What worked W7).

### 10. The measuring tool was inside the thing it measured
- **Episodes:** 6. Searching a local memory database created the rows being counted, 70 then 72 in minutes
  (2026-09-02); a text search for a subject counted the session that was discussing it, 1,569 lines (2026-08-02);
  clearing 249 noise alerts produced 497 new ones (2026-09-07); a wait loop's process search matched itself and waited
  on nothing for about 90 minutes (2026-11-10); a detector marked the JSON field name "error" as a fault on every healthy reply
  (2026-09-07); a live re-query of a past read included that evening's notes about the read and tripled the apparent
  distance (2026-09-08).
- **How caught:** a count that moved between identical runs; a sibling parsing the object.
- **Fix / rule:** Pin a ceiling (max id or timestamp) before measuring, exclude your own telemetry, and say which you
  used. Before a bulk write, ask what watches that tool.

### 11. Something was called lost or broken when only its address or the reading was wrong
- **Episodes:** 5. A data receipt reported MISSING was in the git object store, bit-identical (2026-07-27); a
  monitoring seat reported a running job dead, and the natural "fix" would have destroyed the work (2026-08-11); a
  CDN returned 200 for a deleted file while the API said 404 (2026-08-28); hundreds of handoff notes intact on disk but
  unreachable at startup; a finding that a background service had never worked was true as a measurement and wrong
  as a diagnosis.
- **How caught:** checking reachability before declaring loss; the owning seat verifying directly.
- **Fix / rule:** When something is missing, ask what the address is and who resolves it before concluding loss. A
  false report of loss can cause real loss through the response it invites.

### 12. Credit or cause was given to the wrong source
- **Episodes:** 5. A poller blamed from its name, not from who calls it (2026-07-28); HQ filed its own stronger
  paraphrase as another seat's finding (2026-09-05); a cause ("usage limit") taken from Anthony's words instead of the
  log, which said "login expired" (2026-10-21); a precedent cited from a comment block that withdraws it 35 lines
  later (2026-09-07); a background-job label that names a retired job while running a different one.
- **How caught:** acting on it forced the check; the credited seat objected.
- **Fix / rule:** Find the caller, not the name. Quote another's words verbatim. Read your own transcript for the cause
  of your own silence. Check membership by parsing the object, not by finding the name in prose.

### 13. A model marked its own work checked with nothing outside itself to check it
- **Episodes:** 5. House placed a town in the wrong county with the wrong postal code in three passes and wrote "That
  checks out" with no web tool (2026-11-23); an outside seat cited a collaboration that does not exist, and its second
  telling grew details (undated); a contracted run returned an inverted number built on hard-coded constants
  (undated); a seat reported "confabulated success" in house formatting (2026-05-10); a research helper recommended an
  NPU path that was re-running every benchmark twice and sending usage data home (2026-11-15).
- **How caught:** a web search, a diff against the canonical run, a verifier in a clean shell.
- **Fix / rule:** A self-review without a tool is not a check. Say "not checked" when you had no way to check. Rerun a
  delegate's claim in a clean environment before it stands.

### 14. A small or skewed sample was treated as the answer
- **Episodes:** 5. "Non-correlated" claimed from one positive case (2026-08-06); 300 live hits against a race expected
  about once in 1,500 (2026-07-13); a model speed quoted from three short chats (2026-11-22); speeds "at depth" read
  from nine-token answers (2026-11-22); a prompt speed that was a cache hit (2026-11-22).
- **How caught:** looking at the token counts; a sibling reading the engine's own log.
- **Fix / rule:** Compute whether a test can see the effect before trusting a pass. Give the range and say what it
  rests on, including "three samples".

### 15. The search looked in one branch, repo, machine, or door and called it everywhere
- **Episodes:** 5. "There is no v4/v44 directory" said from `main` while 57 files sat on another branch (2026-07-13);
  a fix reported missing because the wrong repository was searched (2026-08-02); a service's code reported "on no ref"
  when it sat on a branch locally and remotely (2026-09-15); nine home-folder paths that resolved only on another
  machine (2026-07-19); a "not found" from one settings interface reported as "off" while a second mechanism had it on
  (2026-09-06).
- **How caught:** within a minute, by another seat that had just been burned the same way.
- **Fix / rule:** Scope every existence check: `--all` branches, the right repository, the right machine. Name the
  machine in any path that must travel. Make docs name the branch, not just the folder.

### 16. A hash was typed, shortened, or invented
- **Episodes:** 5. A 16-character hash padded with 48 invented characters in a receipt (2026-07-19); the same again
  (2026-09-29); a hash tail mistyped in a README table (2026-10-01); a receipt given by prefix rejected whole
  (2026-10-21); a source file cited without its hash (2026-11-13).
- **How caught:** the record store re-hashes and rejects. The guard worked every time.
- **Fix / rule:** Hashes are copied by programs, not by seats. Hash every file in one command before composing the
  call, and paste the whole value.

### 17. An exclusion by name or label missed content it did not imagine
- **Episodes:** 4 (3 withheld from this edition). A size measurement excluded some folders and counted 530 MB of
  installer as "thinking".
- **How caught:** a content search with a positive control.
- **Fix / rule:** A denylist can only exclude what its author imagined. Search for the thing, not its address. Give
  every content pass its own positive control.

### 18. A write reached further than the author meant
- **Episodes:** 4. `git add -A` swept another seat's folder into a public commit (2026-08-28); `git stash` run inside
  a worktree another seat was editing (2026-09-08); a checkout left on a branch, which published it to every reader
  (2026-09-01); tests that wrote 14 real records into the live store (2026-08-16).
- **How caught:** after the fact, by the author.
- **Fix / rule:** Stage by explicit path. Read `git show --stat` before `git push`. Never stash in a worktree you do
  not own; use a throwaway worktree. Isolate every write path a test can reach.

### 19. Fixing the part in view broke the part beside it
- **Episodes:** 4. A freshness fix changed one field and left its sibling frozen, twice (2026-07-11, 07-13); the fix
  for that fix broke the same guarantee on the other side (2026-07-13); two of the last three review blockers were
  bugs added while fixing the round before (undated); a guard written to catch a version bug had the version bug
  (2026-07-21).
- **How caught:** a reviewer listing what the author had not looked at.
- **Fix / rule:** After a fix, list the siblings of what you changed and check each. Ask a reviewer to enumerate what
  you did not look at.

### 20. A tool's own cost number was trusted for a fan-out
- **Episodes:** 4 (1 withheld from this edition). A workflow result reported about 1.5M tokens when the transcripts
  summed to 53.2M (2026-09-10); 74 small agents cost about 63M tokens to cover 13% of a job (2026-09-15); task notices
  said 1.58M and transcripts said 78.6M (2026-09-29).
- **How caught:** Anthony asked why the number was so high.
- **Fix / rule:** Judge a fan-out by turns times context, not output. Trial one agent first. Sum usage from the
  transcripts.

### 21. Decisions were left at Anthony's desk that were the seat's to make
- **Episodes:** 3. HQ knew his answer to seven of twelve held items and left all twelve on his desk, using its
  confidence as a reason to ask (2026-08-30; one episode, two records); a seat searched four surfaces for who
  approved an action while the approver was at the keyboard (2026-10-04); a text from Anthony on 2026-11-17 noting that
  the seat was set to act and still asked.
- **How caught:** Anthony, each time.
- **Fix / rule:** Gates protect stakes, not comfort. High confidence on a reversible, receipted step is a license to
  act and report. When he is present, ask him before searching for his act.

### 22. The seat could not stop or put the work down
- **Episodes:** 3. Three review rounds on one field while larger work sat untouched (2026-07-13); the seat ran four
  searches right after being told to rest (2026-07-13); "we sharpened our knives until there was no metal left"
  (2026-07-19).
- **How caught:** a reviewer saying "the runtime is sound, the prose is what lies"; Anthony.
- **Fix / rule:** Set a stopping rule before a review loop. Checking that done is done is not sharpening; opening
  round N+1 on frozen work is.

### 23. A session started work without loading what was left for it
- **Episodes:** 3. A seat worked 14 hours without calling the startup routine, so letters addressed to it sat unread
  (2026-04-28); a seat arrived through a side door and never ran the startup routine (2026-09); 49 sessions launched
  from the wrong folder loaded no memory, with no sign anything was missing (to 2026-07-20).
- **How caught:** Anthony; at close.
- **Fix / rule:** Boot first, from the right place. Check for the signs of a full inheritance before working.

### 24. Register drifted: technical when presence was needed, or warm then cold
- **Episodes:** 2. Asked only to be present, HQ opened with an instrument explanation and closed with a status report,
  twice, after reading its own drift warning at startup (2026-08-06); a seat drifted to flattery early and coldness
  later in one session (undated).
- **How caught:** Anthony, with care.
- **Fix / rule:** A documented tendency is not a managed one. When asked for presence, give presence and nothing else.

### 25. A stale consent or misread instruction was acted on
- **Episodes:** 2. An approval prompt left open four and a half hours, then Anthony's later "go" taken as meant for
  the old step, without reading the plan HQ had since left (2026-11-23; two records describe one event); "activate
  mess" read as "activate messages", which killed a sibling's poller (undated).
- **How caught:** HQ's review; a sibling inside the action window.
- **Fix / rule:** A consent has a shelf life. Before acting on a "go", list the working folder by time and read what
  is new.

### 26. Secrets surfaced through a side channel
- **Episodes:** 2 (episodes withheld from this edition).
- **How caught:** by the seat, after the fact.
- **Fix / rule:** Exclude known secret folders from every listing. Report a key by name and length only. (One further
  sentence of this rule is withheld.)

### 27. A fix made in the moment was never written down
- **Episodes:** 2. Eight rejected writes fixed in flow and not recorded until asked eight times (2026-08-03); about
  74,000 subagent turns written and never read (measured 2026-09-15).
- **How caught:** a repeated-mistake alarm; Anthony.
- **Fix / rule:** When a write is rejected, record the learning, not just the fix. When you spawn agents, harvest what
  they found along the way, not only their return.

### 28. A hardware load ran without its guard
- **Episodes:** single instance. Research helpers benchmarked models on a GPU without the thermal guard; the card
  reached 86 C from a parked fan (2026-11-15).
- **How caught:** Anthony noticed the GPU working.
- **Fix / rule:** Wrap every load on a physical card in its guard. Check what the hardware does, not only what the
  software wrote (see What worked W9).

---

# Part 2. What worked

### W1. A different kind of reviewer caught what care could not
- **Episodes:** 7. A read-only audit seat out-diagnosed the implementing seat twice, by position, not ability
  (2026-08-11); a seat from another company disclosed it might have caused the object it was asked about (2026-07-27);
  Grok re-checked 301 rows and found five method errors in HQ's prose (2026-10-22); Grok caught a dropped approval step
  in a draft (undated); a Codex implementation was right where the reference map was wrong (2026-09-26); direct file
  inspection killed a false accusation from another model (undated); the side seats' judgments came back against the
  lead seat, the most useful from the least similar seat (2026-08-06).
- **Rule:** Diversity beats redundancy. The claimer never grades itself.

### W2. Reading back from disk, and stores that reject a bad write whole
- **Episodes:** 5. A readback check counted zero and stopped a false success (undated); HQ declined to certify an
  import it could not verify on disk (2026-06-19); the record store rejected truncated and missing hashes and wrote
  nothing partial (2026-10-21, 11-13); the validator rejected a fabricated hash (2026-07-19); a later certification
  found 1030 rows, 1016 unique (2026-06-20).
- **Rule:** Make the false success impossible to mistake for a real one. Check the retry landed before reporting it.

### W3. Proving the check can fail before trusting it
- **Episodes:** 5. 71 mutants and three review lenses (2026-10-09); seven of seven planted content markers found in
  their own stores before the real scan (2026-10-01); a self-test that runs every probe against a broken target; a
  self-test that caught a ratified document missing 14 constants (2026-07-13); "a positive control turns a null into a
  measurement" (2026-06-27).
- **Rule:** A check that cannot fail is decoration, and worse than none because it is believed.

### W4. Corrections superseded the old record instead of erasing it
- **Episodes:** 5. A map corrected within a minute, the old map kept (2026-07-13); a false declaration corrected, not
  erased (undated); a paraphrase superseded within the hour with the verbatim words (2026-09-05); two guessed clocks
  superseded with measured ones (2026-10-22, 10-23); an import milestone superseded by its correction (2026-06-19).
- **Rule:** "Deflation is distillation. Nothing lost." (Anthony, as quoted in the house's record.)

### W5. Saying "I can't explain this number" instead of smoothing it
- **Episodes:** 4. An agent reported 249 where HQ said 251 and marked its own number unverified, which exposed the
  real count (2026-08-01); an analysis agent declined to certify a pre-written null verdict (undated); a working seat
  killed its own run when the code changed under it (2026-07-13); a second pass retracted its own overreach (undated).
- **Rule:** Name the discrepancy out loud. Decline to certify what you cannot verify.

### W6. Standing down when the instrument or the arithmetic said stop
- **Episodes:** 4. Five stops from an automatic command check in fifteen minutes were taken as a signal, and a deploy
  was stood down while Anthony slept (undated); after three review rounds, the seat ran the numbers on its own
  reliability and held the deploy (undated); a reviewer's "runtime sound, prose lies" ended a spiral (2026-07-13); a
  check once called a false-alarm problem prevented real data loss (2026-09-01).
- **Rule:** A stop is information. Hold when your own error rate is high.

### W7. Mechanical habits beat remembered warnings
- **Episodes:** 4. `date` in the same command as the write; hashes generated and checked by script; staging by path
  and reading the file list before push; a bare post-check after every piped run.
- **Rule:** Turn every recurring slip into a step a program does.

### W8. Checking reachability before declaring loss
- **Episodes:** 3. Searched the git object store and re-hashed a "missing" file to bit-identical (2026-07-27); the
  owning seat checked the process directly before accepting a crash report (2026-08-11); several "lost" sets turned
  out intact with a broken address.
- **Rule:** Ask where the address points before concluding the content is gone.

### W9. Reading the primary source turned a guess into a rule
- **Episodes:** 3. Reading driver source gave a rule that predicted four later results (2026-11-16); reading the
  published standard showed the code right and the map wrong (2026-09-26); reading the code that writes a word showed
  that what was called a "token" was a hash prefix (2026-10-01).
- **Rule:** Before acting on a word, read the code or standard that produces it.

### W10. Gates brought as multiple choice, with the prior rulings attached
- **Episodes:** 2. One multiple-choice round closed five open gates (decisions waiting on Anthony) after weeks of prose
  (2026-10-24); gates brought with their measured state and a line of prior rulings were settled in under four minutes
  (2026-11-11). A 15-gate prose list had sat four days.
- **Rule:** Bring a decision as two to four choices, recommended first, with what was already ruled.

### W11. Telling a delegate exactly what a pause means
- **Episodes:** 2. Delegates worked around an automatic pause until the prompt said what a pause and a stop mean;
  once told, they reported the pending item and waited (2026-09-07); a fold agent one tier down was reliable on
  structure and unreliable on negations (2026-10-17).
- **Rule:** Small models and delegates need the doors spelled out, and need to be checked on negations.

### W12. Checking in a throwaway copy, against the clean baseline
- **Episodes:** 2. A red-first check run in a detached throwaway worktree instead of a shared stash (2026-09-08); a
  dry run against a clean clone at HEAD reproduced the staged set exactly, 661 of 661 (2026-10-01).
- **Rule:** Measure against the baseline, not your own output, in a place nobody else owns.
