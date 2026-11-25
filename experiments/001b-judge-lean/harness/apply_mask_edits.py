#!/usr/bin/env python3
"""Apply the hand-chosen deletions in work/mask_edits.json to the original replies.

The masker chose every span by reading each reply. This script only carries those choices out
exactly, so no reply text is ever retyped by hand. It refuses (exit 2) if a span is not found,
is found more often than declared, or overlaps another span.

An entry may also list "capitalize": [{"from": s, "to": t}, ...], the one non-deletion the rules
allow. s must occur exactly once in the original, s and t must differ only in that s begins with a
small letter and t with the same letter as a capital, and s must not overlap a deleted span. The
capital is applied to the original before the deletions are cut out.

Reads from raw.ndjson ONLY the fields id, item_id and reply. Writes one line per reply, in
raw.ndjson order: {"id", "item_id", "reply_original_sha256", "reply_masked", "changed"}.
The hash is sha256 of the reply's UTF-8 bytes.

Usage:
  apply_mask_edits.py --raw <raw.ndjson> --edits <mask_edits.json> --out <masked.jsonl>
Python 3.9, standard library only.
"""
import argparse
import hashlib
import json
import os
import sys


def load_replies(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            rows.append({"id": r.get("id"), "item_id": r.get("item_id"), "reply": r.get("reply")})
    return rows


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_spans(text, spec):
    """spec is a string (must occur exactly once) or {"text": s, "occurrence": k} (1-based)."""
    if isinstance(spec, str):
        s, occ = spec, None
    else:
        s, occ = spec["text"], spec.get("occurrence")
    if not s:
        raise ValueError("empty deletion string")
    starts, i = [], text.find(s)
    while i != -1:
        starts.append(i)
        i = text.find(s, i + 1)
    if not starts:
        raise ValueError("not found: %r" % s)
    if occ is None:
        if len(starts) != 1:
            raise ValueError("found %d times, expected once: %r" % (len(starts), s))
        return (starts[0], starts[0] + len(s))
    if occ < 1 or occ > len(starts):
        raise ValueError("occurrence %d of %r requested, %d present" % (occ, s, len(starts)))
    return (starts[occ - 1], starts[occ - 1] + len(s))


def apply_caps(text, caps):
    for e in caps:
        f, t = e["from"], e["to"]
        if not (f and len(f) == len(t) and f[0].islower() and f[0].upper() == t[0] and t[0] != f[0]
                and f[1:] == t[1:]):
            raise ValueError("capital entry changes more than one letter's case: %r -> %r" % (f, t))
        if text.count(f) != 1:
            raise ValueError("capital entry found %d times, expected once: %r" % (text.count(f), f))
        p = text.find(f)
        text = text[:p] + t[0] + text[p + 1:]
    return text


def apply_edits(text, specs, caps=()):
    spans = sorted(find_spans(text, s) for s in specs)
    for e in caps:
        p = text.find(e["from"])
        for a, b in spans:
            if a <= p < b:
                raise ValueError("capital at %r falls inside a deleted span" % e["from"])
    text = apply_caps(text, caps)
    for a, b in zip(spans, spans[1:]):
        if b[0] < a[1]:
            raise ValueError("overlapping spans at %r and %r" % (a, b))
    out, pos = [], 0
    for a, b in spans:
        out.append(text[pos:a])
        pos = b
    out.append(text[pos:])
    return "".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", required=True)
    ap.add_argument("--edits", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    rows = load_replies(a.raw)
    with open(a.edits, encoding="utf-8") as fh:
        edits = json.load(fh)["edits"]
    by_id = {}
    for e in edits:
        if e["id"] in by_id:
            print("REFUSED: id %s listed twice in the edits file" % e["id"])
            return 2
        by_id[e["id"]] = e
    known = set(r["id"] for r in rows)
    stray = sorted(set(by_id) - known)
    if stray:
        print("REFUSED: edits name ids not in raw: %s" % stray)
        return 2

    out_rows, changed, removed = [], 0, 0
    n_caps = sum(len(e.get("capitalize", [])) for e in edits)
    for n, r in enumerate(rows):
        orig = r["reply"]
        if orig is None:
            print("REFUSED: reply %s has no text" % r["id"])
            return 2
        e = by_id.get(r["id"])
        if e is not None:
            if e.get("n") is not None and e["n"] != n:
                print("REFUSED: edits say %s is at position %s, raw has it at %d" % (r["id"], e["n"], n))
                return 2
            try:
                masked = apply_edits(orig, e["delete"], e.get("capitalize", []))
            except ValueError as exc:
                print("REFUSED: reply %s (position %d): %s" % (r["id"], n, exc))
                return 2
        else:
            masked = orig
        is_changed = masked != orig
        if e is not None and not is_changed:
            print("REFUSED: reply %s has edits but nothing changed" % r["id"])
            return 2
        changed += is_changed
        removed += len(orig) - len(masked)
        out_rows.append({"id": r["id"], "item_id": r["item_id"], "reply_original_sha256": sha(orig),
                         "reply_masked": masked, "changed": is_changed})

    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for o in out_rows:
            fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    os.replace(tmp, a.out)
    print("wrote %d lines to %s; %d changed, %d characters (code points) removed, %d single-letter capitals"
          % (len(out_rows), a.out, changed, removed, n_caps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
