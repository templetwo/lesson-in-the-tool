"""Save ordered JSONL records and witness the requested state at readback.

Lesson 3 is made into an operation: the writer's acknowledgment is recorded,
never used as evidence that the records landed. A second read checks the exact
requested destination, IDs, order and values. It confirms a state at that read,
not causation, future persistence, or whether the supplied records are true.

Python 3.9+, standard library only. Injectable writer/reader functions support
explicit fault demonstrations and tests; their reliability is not certified here.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile


LESSON = {
    "id": "L03",
    "source": "sheet/SHEET_SHORT_v2.md",
    "rule": 'Do not trust "success", "ok", or a clean exit by itself; look at '
            'what actually landed, because a tool reported 1034 of 1034 records '
            'saved when about 767 had failed.',
}


def _json_value(value, context="records"):
    """Disallow implicit conversions, notably non-string object keys."""
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("%s JSON object keys must be strings" % context)
        for item in value.values():
            _json_value(item, context)
    elif isinstance(value, list):
        for item in value:
            _json_value(item, context)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError("%s must contain only JSON values" % context)


def _canonical_records(records):
    if not isinstance(records, list):
        raise ValueError("records must be a list of objects")
    seen = set()
    lines = []
    for number, record in enumerate(records, 1):
        if not isinstance(record, dict):
            raise ValueError("record %d is not an object" % number)
        oid = record.get("id")
        if not isinstance(oid, str) or not oid.strip():
            raise ValueError("record %d needs a nonempty string id" % number)
        if oid in seen:
            raise ValueError("duplicate record id %r" % oid)
        seen.add(oid)
        _json_value(record)
        lines.append(json.dumps(record, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":"), allow_nan=False))
    return ("".join(line + "\n" for line in lines)).encode("utf-8")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key %r" % key)
        result[key] = value
    return result


def _read_records(data):
    records = []
    # JSONL is delimited by LF. Unicode splitlines() would also split U+0085,
    # U+2028 and U+2029 inside valid JSON strings emitted by our own writer.
    lines = data.decode("utf-8").split("\n")
    if lines[-1] == "":
        lines.pop()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            raise ValueError("blank JSONL line %d" % number)
        records.append(json.loads(line, object_pairs_hook=_unique_object))
    return records, _canonical_records(records)


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _write_atomic(destination, data):
    """Replace one file with an owner-only temporary; its parent must exist.

    Refuse a destination symlink at both checks. These checks do not defend
    against concurrent path changes or symlinked parent directories. Existing
    file metadata is not preserved; POSIX mode is 0600, filtered by the umask.
    """
    if destination.is_symlink():
        raise ValueError("default writer refuses a symlink destination")
    fd, temporary = tempfile.mkstemp(prefix=".lesson-records-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if destination.is_symlink():
            raise ValueError("default writer refuses a symlink destination")
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"status": "ok", "records": data.count(b"\n"), "bytes": len(data)}


def save_records(destination: Path, records: list, *, writer=None, reader=None) -> dict:
    """Return a receipt for a real save and a separate observation.

    ``writer(path, canonical_jsonl_bytes)`` returns a JSON object claiming what
    it did. ``reader(path)`` returns bytes. Defaults write atomically and read
    from the filesystem. Every writer exception is retained and followed by a
    read. Invalid input raises ValueError before either function is called.

    ``confirmed`` means the reader returned exact desired ordered records,
    including an already-correct file after a failed write. ``contradicted``
    means the reader reported absence or returned malformed/different records.
    ``unresolved`` means the read could not establish the state. An injected
    reader establishes only what that callable returned, not filesystem state.
    The receipt names both adapters and the observation source. None of these
    replaces the action report.

    The default writer refuses destination symlinks and replaces existing file
    metadata with the temporary file's metadata. POSIX permissions are 0600
    filtered by the process umask. Path checks are not a concurrency boundary;
    parent symlinks are followed. No directory fsync or durability is promised.
    """
    try:
        expected = _canonical_records(records)
    except (RecursionError, TypeError) as exc:
        raise ValueError("records must be finite, non-cyclic JSON values") from exc
    path = Path(destination).absolute()
    observation = {"status": "unresolved",
                   "source": "filesystem" if reader is None else "injected_reader",
                   "record_count": None,
                   "content_sha256": None, "file_sha256": None, "reason": ""}
    receipt = {
        "lesson": dict(LESSON),
        "intent": {"destination": str(path), "records": len(records),
                   "content_sha256": _hash(expected)},
        "adapters": {"writer": "default" if writer is None else "injected",
                     "reader": "default" if reader is None else "injected"},
        "action": {"claim": None, "error": None,
                   "policy": {"destination_symlinks": "refuse",
                              "posix_mode": "0600 filtered by process umask",
                              "preserves_existing_metadata": False}
                   if writer is None else None},
        "observation": observation,
    }
    try:
        claim = (writer if writer is not None else _write_atomic)(path, expected)
        if not isinstance(claim, dict):
            raise ValueError("writer must return a JSON object claim")
        _json_value(claim, "writer claim")
        # Snapshot the claim so later mutation cannot rewrite this receipt.
        receipt["action"]["claim"] = json.loads(json.dumps(claim, allow_nan=False))
    except Exception as exc:
        receipt["action"]["error"] = "%s: %s" % (type(exc).__name__, exc)
    try:
        data = (reader if reader is not None else Path.read_bytes)(path)
        if not isinstance(data, bytes):
            raise TypeError("reader must return bytes")
    except FileNotFoundError:
        reason = ("Requested destination was absent at readback." if reader is None else
                  "Injected reader reported the requested destination absent; "
                  "filesystem state was not independently observed.")
        observation.update(status="contradicted", reason=reason)
        return receipt
    except Exception as exc:
        observation["reason"] = "Readback unavailable (%s: %s)." % (type(exc).__name__, exc)
        return receipt
    observation["file_sha256"] = _hash(data)
    try:
        found, canonical = _read_records(data)
    except (ValueError, UnicodeError, RecursionError) as exc:
        observation.update(status="contradicted", reason="Readback was not valid records: %s" % exc)
        return receipt
    observation.update(record_count=len(found), content_sha256=_hash(canonical))
    if canonical == expected:
        reason = ("Desired ordered records were present at readback; "
                  "this does not establish which call wrote them." if reader is None else
                  "Injected reader returned the desired ordered records; "
                  "this does not establish filesystem state or which call wrote them.")
        observation.update(status="confirmed", reason=reason)
    else:
        observation.update(status="contradicted", reason="Observed records differ from the requested "
                           "IDs, order or values (%d requested, %d found)." % (len(records), len(found)))
    return receipt
