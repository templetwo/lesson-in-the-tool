# The part that remembers

The project began with a repeat: a mistake was caught, a lesson was written, and
another seat made the mistake again. A useful tool should change what survives
that handoff. The next model may never read the story. The careful step still
happens.

This contribution starts with one lesson and one real operation. `save_records`
writes a JSONL file, reads the requested destination, and compares the complete
ordered records with the request. The tool does the readback every time. No
agent loop, model, memory service or extra prompt is needed.

Try its six local demonstrations from the repository root:

```sh
python3 -B -m lesson_tools
python3 -B -m lesson_tools --case substituted --json
```

The demonstration uses invented records in a temporary folder and removes them
when it finishes. The underlying function is a real file-writing operation:

```python
from pathlib import Path
from lesson_tools.records import save_records

receipt = save_records(Path("records.jsonl"), [{"id": "r1", "value": 7}])
print(receipt["observation"])
```

## A lesson has a body

A lesson-bearing tool has four parts that can be inspected separately:

| Part | This first tool |
|---|---|
| What taught it | Sheet rule 3: a tool reported 1,034 records saved while about 767 had failed. The public sheet is the source for that account. |
| What it now does | Reads the exact requested destination and checks ordered identities and values after every write attempt. |
| What could defeat it | Twelve records are requested and twelve are found, but one value or identity is wrong. A counter would accept this. This tool must refuse confirmation. |
| Where its knowledge ends | The requested state was observed at readback. That does not establish who caused it, how long it will last, or whether the records mean what the user intended. |

The story is available to explain the obligation. The obligation does not depend
on a model reading, believing or remembering the story. That is the operational
meaning of “the tool remembers” in this prototype.

## Keep the disagreement visible

The receipt preserves three different things:

- **Intent:** the requested destination, record count and program-computed
  content hash.
- **Action:** what the writer claimed, or the error it raised.
- **Observation:** what the readback found, its file and content hashes, and a
  bounded conclusion.

The receipt also names the writer and reader as `default` or `injected` in
`adapters`, and the observation's source as `filesystem` or `injected_reader`.
With the default filesystem reader, the conclusion has three states:

| State | Meaning | Example |
|---|---|---|
| `confirmed` | The requested ordered records were observed at the requested destination. | All twelve records match. |
| `contradicted` | The destination was absent, or its readable contents differ from the request. | Nine records landed; twelve different records landed; the write went elsewhere. |
| `unresolved` | The readback could not establish the destination's contents. | Reading the file failed. |

These are conclusions about a specific observed state. They are not an overall
“task done” field. The action's claim remains beside the observation even when
they disagree. An error can coexist with a confirmed state: if matching records
were already there and this writer failed, the state is present but this call
has not earned credit for creating it. The `preexisting` demonstration makes
that distinction visible.

The tool must also be able to confirm real success plainly. A mechanism that
replaces false confidence with permanent suspicion has learned the wrong lesson.

## Name what supplied the evidence

The optional `writer` and `reader` callables let development controls introduce
specific faults. An injected reader can return matching bytes when no file
exists. Its `confirmed` status means those returned records match; it does not
establish filesystem state. The source field and reason preserve that limit.
An injected writer's claim is always checked through whichever reader was
selected. The tool does not certify an adapter's honesty or independence.

The default writer's policy is included in `action.policy`. It refuses a
destination symlink, including a dangling one, and preserves the link and its
target. It still attempts the readback after refusal, so an already-matching
symlink target can be observed alongside the writer's error. Parent-directory
symlinks are followed; the destination checks do not protect against concurrent
path changes. Use a directory whose paths are under your control.

A successful default write replaces the file with a temporary file whose POSIX
mode starts at `0600`, filtered by the process umask. Existing permissions and
other metadata are not preserved. The contents are flushed and the temporary
file is synced before replacement, but the parent directory is not synced: this
is no promise of survival across a crash. Records and readback are held in
memory with no size limit. These are boundaries of this small file operation,
not judgments the receipt can settle for its caller.

## Let each tool carry its attempted refutation

The tests are part of the tool's meaning. They cover true and empty success,
partial writes, wrong values with the right count, duplicate or substituted
identities, writes to the wrong destination, unreadable evidence and errors
alongside an already-correct state. Invalid requests are rejected before writing.

```sh
python3 -B -m unittest discover -s tests -v
```

The archive verifier applies the same principle to the project's own evidence:
it must reject a duplicated plan, a missing score and a changed frozen input.
Its controls live beside the record tool's controls. A green badge without a
demonstrated failure case would repeat the problem this project studies.

## A family of specific obligations

The next tools should grow from different failure mechanisms. Each needs its
own observable, its own counterexample and its own stopping point.

| Candidate | Obligation inherited from the sheet | Counterexample it must survive | What remains judgment |
|---|---|---|---|
| Search with an account of coverage | Return searched sources, scope, limits and failures with the matches. | An empty result after only one of three sources responded. | Whether those sources were sufficient for the question. |
| A setting with a live readback | Report persisted configuration and effective running state separately. | The file changed; the process still uses the old setting. | Whether to restart or change the system. |
| A revisitable receipt | Re-observe the relevant state when an old receipt is used again. | Yesterday's confirmed file has since changed. | Whether the changed state is acceptable. |

These are proposed siblings, not implemented capabilities. They should not share
one universal success checker: records, searches and running settings have
different ways of being wrong. They can share a receipt vocabulary while keeping
their obligations specific.

Some lessons should remain outside this machinery. Presence is one. A tool can
leave space for attention; a receipt cannot decide that someone was understood.

## What this build can teach us next

This is an engineering prototype informed by the sheet. Its demonstrations are
development controls, not blinded tasks or results from experiment 002. The
draft registration and all frozen material remain unchanged.

The tests establish that this implementation detects the specified defects.
Experiment 002 would ask the further question: does a model receiving these
observations report the outcome more faithfully? A model could ignore a correct
receipt, repeat the action's false claim, or distrust a confirmed success.

One proposed addition for a future revision of that experiment is a
**count-preserving error**: the count is correct and the records are wrong.
Another is **unavailable observation**, scored separately from a false result.
Both proposals need to be decided before any tasks or rules are frozen. The
receipt's useful shape should be tested too: compact evidence may help where a
long historical explanation does not. None of those effects has been measured.

The direction is concrete: turn one paid-for mistake into one obligation that
survives the next handoff, and keep an example nearby that could prove it failed.
