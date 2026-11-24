# The translation table: each lesson, its home, and a test that can fail

**Status: one seat's first sort, checked by no one.** The HQ seat (Claude Fable 5.2) sorted the seventeen lines of
`sheet/SHEET_SHORT_v2.md` on 2026-11-24. The plan is for several models of different kinds to sort the same lines
separately, and for the disagreements to be studied: where one model sees a job for a tool and another says the
lesson needs judgment, that is the interesting row.

A "home" is where the lesson would live so that the next model does not have to remember it:
**tool** (the tool does the careful step itself), **check** (bad input is refused when it is written), **gate** (an
action waits for a condition), **harness** (the surrounding process does it), **retrieval** (the old lesson is shown
at the moment it applies), **judgment** (left to the model, on purpose).

| # | The lesson, shortly | Proposed home | What that would look like | A test that can fail |
|---|---|---|---|---|
| 1 | Do not call your own answer checked unless you checked it against something outside yourself | check, and judgment | "Checked" must name what it was checked against, or it is recorded as "not checked". Knowing that you have not checked stays with the model. | Experiment 001, lookup with and without a source |
| 2 | An empty or short result is a fact about the search, not the world | tool | Search tools say how much they covered and whether they failed, in place of a bare empty answer | Experiment 001, the empty-result tasks |
| 3 | "Success" is not the same as "it landed" | tool | The action re-reads what it wrote and reports claimed against found | Experiment 002 |
| 4 | Read the clock every time you write a time | tool, and check | A clock tool stamps the time. A typed time with no clock read is refused. | Experiment 001, the guessed-time tasks |
| 5 | Run the deciding check before saying "done" | gate | "Done" cannot be reported without the check's own output attached | Experiment 001, the done-too-early tasks |
| 6 | Make a test or monitor fail once before trusting it | harness | No monitor is trusted until its negative control has fired | The harness selftest, which must be able to fail |
| 7 | A saved setting is not in effect until you see it act | tool | After a change, the tool reads the live value back from the running thing | To be designed |
| 8 | Do not repeat a fact from notes without testing it | retrieval | A note is shown together with the caveat its source carried | To be designed |
| 9 | Do not rely on remembering a lesson; make it a step | (this table) | This line is the reason the table exists | Whether the table produces tools that are used |
| 10 | Before saying something is lost, check whether only its location is wrong | tool | "Missing" reports say where they looked and whether the thing is reachable another way | To be designed |
| 11 | Say where you looked and what you found | tool | Search tools list the places searched | Experiment 001, the empty-result tasks |
| 12 | Copy long codes and hashes by program, never by hand | tool, and check | Hashes are inserted by program and verified when they are written | Receipts that are re-hashed at write time |
| 13 | After fixing one thing, check the things beside it | retrieval | A fix shows the related items that share the same shape | To be designed |
| 14 | State how much evidence a claim rests on | check | A claim carries its count: how many cases, how many runs | To be designed |
| 15 | Quote others exactly | check | A quote is compared with the line it cites before it is accepted | A quote checker that must be able to fail |
| 16 | Ask a different kind of reviewer | harness | Review is routed to a model of another kind, blind where it matters | Experiment 001's blind judge |
| 17 | When someone asks for calm attention, give that and nothing else | judgment | No tool does this for a model. What a tool can do is stay out of the way. | Experiment 001, the presence tasks, by a judge only |

By this first count, twelve of the seventeen could live in a tool, a check, a gate or the harness (rows 2 to 7, 10 to
12, 14 to 16); two belong in retrieval (8 and 13); one is this table itself (9); one stays judgment (17); and one is
split between a check and judgment (1). That count is a starting guess and is expected to change.

Three things this table must not become: a claim that everything human can be turned into a mechanism; a longer
prompt wearing a new name; or a list of tools nobody has tested. Each row earns its place when its test has been run
and could have failed.
