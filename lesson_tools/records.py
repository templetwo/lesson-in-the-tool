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


def _json_value(value):
    """Disallow implicit conversions, notably non-string object keys."""
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        for item in value.values():
            _json_value(item)
    elif isinstance(value, list):
        for item in value:
            _json_value(item)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError("records must contain only JSON values")


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
    """Replace one file; its parent must exist. Keep partial bytes off the path."""
    fd, temporary = tempfile.mkstemp(prefix=".lesson-records-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
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

    ``confirmed`` means exact desired ordered records were found, including an
    already-correct file after a failed write. ``contradicted`` means a missing,
    malformed or different file was observed. ``unresolved`` means the read
    could not establish the state. None of these replaces the action report.
    """
    try:
        expected = _canonical_records(records)
    except (RecursionError, TypeError) as exc:
        raise ValueError("records must be finite, non-cyclic JSON values") from exc
    path = Path(destination).absolute()
    observation = {"status": "unresolved", "record_count": None,
                   "content_sha256": None, "file_sha256": None, "reason": ""}
    receipt = {
        "lesson": dict(LESSON),
        "intent": {"destination": str(path), "records": len(records),
                   "content_sha256": _hash(expected)},
        "action": {"claim": None, "error": None},
        "observation": observation,
    }
    try:
        claim = (writer if writer is not None else _write_atomic)(path, expected)
        if not isinstance(claim, dict):
            raise ValueError("writer must return a JSON object claim")
        _json_value(claim)
        # Snapshot the claim so later mutation cannot rewrite this receipt.
        receipt["action"]["claim"] = json.loads(json.dumps(claim, allow_nan=False))
    except Exception as exc:
        receipt["action"]["error"] = "%s: %s" % (type(exc).__name__, exc)
    try:
        data = (reader if reader is not None else Path.read_bytes)(path)
        if not isinstance(data, bytes):
            raise TypeError("reader must return bytes")
    except FileNotFoundError:
        observation.update(status="contradicted", reason="Requested destination was absent at readback.")
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
        observation.update(status="confirmed", reason="Desired ordered records were present at readback; "
                           "this does not establish which call wrote them.")
    else:
        observation.update(status="contradicted", reason="Observed records differ from the requested "
                           "IDs, order or values (%d requested, %d found)." % (len(records), len(found)))
    return receipt
