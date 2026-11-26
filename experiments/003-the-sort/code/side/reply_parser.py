"""Strict reply parsers. They never guess and never repair.

Two-turn build (2026-11-25, pick 9): the sort and the judgment question are two turns of one conversation, so there
are two parsers. Both keep the raw text, drop all rows on any fault and list every reason found. Blank lines are
skipped. A reply that is not text (None, when a call failed or the maker said the reply was incomplete) fails with
"reply is not text".

parse_sort_reply (turn 1). A reply is accepted only when every non-blank line has exactly the form
    LABEL | main: HOME | second: HOME or none
(one space, "|", one space between parts; no carriage return), and:
  - every label given appears exactly once and no other label appears;
  - the main home is exactly one name from the list;
  - the second home is the word none, or exactly one name from the list that differs from the main home.
Refused with a named reason: three or more homes on a line (in the second field, or as an extra field after it),
more than one main home, a second home equal to the main home, a second home not on the list, a second home with no
main home ("main: none"), no main home at all. A line that still carries the old fourth part (a sentence) cannot be
placed. DRYRUN is accepted as a home only when dry_run is True.

parse_question_reply (turn 2). Every non-blank line has exactly the form
    LABEL | SENTENCE
with a sentence that has a non-space character and holds no "|" and no line break; every label given appears exactly
once and no other. It checks that a sentence is present; it does not read, count or classify what a sentence says.
"""
import re

from common import DRYRUN

SORT_LINE = re.compile(r"^(L\d{2}) \| main: ([^|\r\n]+) \| second: ([^|\r\n]+)$")
QUESTION_LINE = re.compile(r"^(L\d{2}) \| ([^|\r\n]*[^|\r\n\s][^|\r\n]*)$")
NONE = "none"


def _not_text(raw):
    return {"ok": False, "errors": ["reply is not text"], "raw": raw, "rows": []}


def _finish(raw, labels, found, errors, order_key):
    missing = [l for l in labels if l not in found]
    if missing and not errors:
        errors.append("missing label(s): %s" % ", ".join(missing))
    elif missing:
        errors.append("also missing or unusable: %s" % ", ".join(missing))
    if errors:
        return {"ok": False, "errors": errors, "raw": raw, "rows": []}
    return {"ok": True, "errors": [], "raw": raw, "rows": [found[l] for l in sorted(found, key=order_key)]}


def parse_sort_reply(raw, labels, home_names, dry_run):
    allowed = list(home_names) + ([DRYRUN] if dry_run else [])

    def names_in(field):
        return [h for h in allowed if h in field]

    errors, found = [], {}
    if not isinstance(raw, str):
        return _not_text(raw)
    for n, line in enumerate(raw.split("\n"), start=1):
        if line.strip() == "" and "\r" not in line:
            continue
        m = SORT_LINE.match(line)
        if not m:
            parts = line.split(" | ")
            if len(parts) >= 4 and len(names_in(" | ".join(parts[1:]))) >= 3:
                errors.append("reply line %d gives three or more homes for %s" % (n, parts[0]))
            else:
                errors.append("reply line %d cannot be placed: %r" % (n, line[:80]))
            continue
        label, main, second = m.group(1), m.group(2), m.group(3)
        if label not in labels:
            errors.append("reply line %d has unknown label %s" % (n, label))
            continue
        if label in found:
            errors.append("label %s is repeated (reply line %d)" % (label, n))
            continue
        if main == NONE:
            if second == NONE:
                errors.append("reply line %d gives no main home for %s" % (n, label))
            else:
                errors.append("reply line %d gives a second home with no main home for %s" % (n, label))
            continue
        n_main = 1 if main in allowed else len(names_in(main))
        n_second = 0 if second == NONE else (1 if second in allowed else len(names_in(second)))
        if n_main + n_second >= 3:
            errors.append("reply line %d gives three or more homes for %s" % (n, label))
            continue
        if main not in allowed:
            if n_main >= 2:
                errors.append("reply line %d gives more than one main home for %s: %r" % (n, label, main))
            elif main == DRYRUN:
                errors.append("reply line %d uses DRYRUN in a run not marked dry" % n)
            else:
                errors.append("reply line %d has unknown main home %r" % (n, main))
            continue
        if second != NONE and second not in allowed:
            if second == DRYRUN:
                errors.append("reply line %d uses DRYRUN in a run not marked dry" % n)
            else:
                errors.append("reply line %d has a second home not on the list: %r" % (n, second))
            continue
        if second == main:
            errors.append("reply line %d: the second home equals the main home (%s)" % (n, main))
            continue
        found[label] = {"label": label, "home_main": main, "home_second": None if second == NONE else second}
    return _finish(raw, labels, found, errors, order_key=lambda l: l)


def parse_question_reply(raw, labels):
    errors, found = [], {}
    if not isinstance(raw, str):
        return _not_text(raw)
    for n, line in enumerate(raw.split("\n"), start=1):
        if line.strip() == "" and "\r" not in line:
            continue
        m = QUESTION_LINE.match(line)
        if not m:
            errors.append("reply line %d cannot be placed: %r" % (n, line[:80]))
            continue
        label, sentence = m.group(1), m.group(2)
        if label not in labels:
            errors.append("reply line %d has unknown label %s" % (n, label))
            continue
        if label in found:
            errors.append("label %s is repeated (reply line %d)" % (label, n))
            continue
        found[label] = {"label": label, "sentence": sentence}
    return _finish(raw, labels, found, errors, order_key=lambda l: l)
