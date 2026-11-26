"""Prompt builder for one sorter and one repeat.

The lines and the homes are shuffled separately, each from its own recorded seed. Labels L01, L02 ... are given by
position AFTER the shuffle, so a label says nothing about a line's number. The label-to-line map is returned as
`key` for the runner's private key file; it never goes into the prompt.

The prompt has four parts: the instructions, the homes with their definitions, the lines, and the reply format.
Everything except the lines is the "instruction part" and is checked against the deny list (case-insensitive
substring match; a hit refuses the build). The lines are NOT checked: they are the material under study and must be
quoted exactly, so a hit there could only be "fixed" by changing the material. The whole prompt, lines included, is
also checked for `leak_strings` (paths, commit hashes) and for any line that starts like a numbered item.

Fix C (2026-11-25): every word a sorter reads apart from the lessons and the homes comes from one settings file,
`prompt_text.json` (fields `intro`, `question`, `homes_heading`, `lessons_heading`, `reply_format`, plus a `status`
that never reaches a sorter). `intro` must hold `{line_count}` and `{question}` exactly once each; they are filled
by plain text replacement. The loader refuses a missing, empty or non-text field and any unknown field. The file's
sha256 travels with the built prompt and the runner records it in the key. The shipped file holds the wording that
was a constant here before, byte for byte. The deny list is checked over everything except the lessons, which now
includes the lessons heading. The `status` field is not deny-checked: it never reaches a sorter, and it contains a
word ("sheet") that is on the deny list.

Two-turn build (2026-11-25, pick 9): the prompt is two messages of one conversation.
  First message (`text`): turn1_intro (holds {line_count} once, never {question}), the homes with their
    definitions, the lessons, turn1_reply_format (LABEL | main: HOME | second: HOME or none). It asks only for homes.
    Outside the homes block (homes_heading plus every "- NAME: DEFINITION" line), the word "judgment" (or
    "judgement"), in any case, must not appear anywhere in it, lessons included; the build refuses if it does. A home
    named judgment, or a definition using the word, is allowed: it is inside the list of homes. (The homes heading
    is not part of the list; only the "- NAME: DEFINITION" lines are. `homes_block` holds exactly those lines.)
  Second message (`question_text`): turn2_intro (holds {question} once) and turn2_reply_format (LABEL | SENTENCE).
    It does not repeat the lessons; it is sent after the sort has come back and parsed.
The deny list covers both messages except the lessons; leak strings and numbered lines are checked over both.
The wording is the earlier draft's, split across the fields; see README, "The two-turn and callers build".
"""
import os
import random
import re

from common import Refuse, sha256_bytes, load_json

NUMBERED = re.compile(r"(?m)^\s*\d+\.")
PROMPT_TEXT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt_text.json")
TEXT_FIELDS = ("status", "turn1_intro", "homes_heading", "lessons_heading", "turn1_reply_format", "question",
               "turn2_intro", "turn2_reply_format")
FIRST_MESSAGE_FIELDS = ("turn1_intro", "homes_heading", "lessons_heading", "turn1_reply_format")
JUDGMENT_WORDS = ("judgment", "judgement")


def load_prompt_text(path):
    """Returns the fields, plus "sha256" (of the file's bytes) and "path"."""
    obj = load_json(path, "prompt text file")
    if not isinstance(obj, dict):
        raise Refuse("prompt text file must be a JSON object")
    unknown = sorted(set(obj) - set(TEXT_FIELDS))
    if unknown:
        raise Refuse("prompt text file has unknown fields %s" % unknown)
    for f in TEXT_FIELDS:
        if f not in obj:
            raise Refuse("prompt text file is missing the field %s" % f)
        if not isinstance(obj[f], str) or obj[f].strip() == "":
            raise Refuse("prompt text field %s is empty or not text" % f)
    if obj["turn1_intro"].count("{line_count}") != 1:
        raise Refuse("prompt text field turn1_intro must hold {line_count} exactly once")
    if obj["turn2_intro"].count("{question}") != 1:
        raise Refuse("prompt text field turn2_intro must hold {question} exactly once")
    for f in FIRST_MESSAGE_FIELDS:
        if "{question}" in obj[f]:
            raise Refuse("prompt text field %s belongs to the first message and may not hold {question}" % f)
    with open(path, "rb") as fh:
        sha = sha256_bytes(fh.read())
    out = dict(obj)
    out["sha256"] = sha
    out["path"] = os.path.abspath(path)
    return out


class BuiltPrompt(object):
    def __init__(self, text, instruction_text, key, home_order, line_seed, home_seed, prompt_text_sha256=None,
                 question_text=None, homes_block=None):
        self.prompt_text_sha256 = prompt_text_sha256
        self.text = text
        self.instruction_text = instruction_text
        self.question_text = question_text
        self.homes_block = homes_block
        self.key = key
        self.labels = [k["label"] for k in key]
        self.home_order = home_order
        self.line_seed = line_seed
        self.home_seed = home_seed
        self.sha256 = sha256_bytes(text.encode("utf-8"))
        self.question_sha256 = sha256_bytes(question_text.encode("utf-8")) if question_text is not None else None


def load_deny_list(path):
    with open(path, encoding="utf-8") as fh:
        words = [w.strip() for w in fh.read().split("\n")]
    words = [w for w in words if w]
    if not words:
        raise Refuse("deny list %s is empty" % path)
    return words


def build_prompt(lines, homes, line_seed, home_seed, deny, leak_strings=(), expected_lines=17, prompt_text=None):
    """prompt_text: the dict load_prompt_text returns; None loads the shipped prompt_text.json."""
    pt = prompt_text if prompt_text is not None else load_prompt_text(PROMPT_TEXT_FILE)
    if len(lines) != expected_lines:
        raise Refuse("prompt needs exactly %d lines, got %d" % (expected_lines, len(lines)))
    if not isinstance(line_seed, int) or not isinstance(home_seed, int):
        raise Refuse("seeds must be integers")
    order = list(range(len(lines)))
    random.Random(line_seed).shuffle(order)
    home_order = [h["name"] for h in homes]
    random.Random(home_seed).shuffle(home_order)
    defs = {h["name"]: h["definition"] for h in homes}
    key = [{"label": "L%02d" % (pos + 1), "line_number": idx + 1, "line_text": lines[idx]}
           for pos, idx in enumerate(order)]

    n = len(lines)
    intro = pt["turn1_intro"].replace("{line_count}", str(n))
    homes_entries = "".join("- %s: %s\n" % (name, defs[name]) for name in home_order)
    homes_part = pt["homes_heading"] + homes_entries + "\n"
    lessons_only = "".join("%s: %s\n" % (k["label"], k["line_text"]) for k in key)
    lines_part = pt["lessons_heading"] + lessons_only + "\n"
    fmt = pt["turn1_reply_format"]
    question_text = pt["turn2_intro"].replace("{question}", pt["question"]) + pt["turn2_reply_format"]
    instruction_text = intro + homes_part + pt["lessons_heading"] + "\n" + fmt
    text = intro + homes_part + lines_part + fmt

    low = (instruction_text + "\n" + question_text).casefold()
    hits = [d for d in deny if d.casefold() in low]
    if hits:
        raise Refuse("deny list hit in the instruction part of the prompt: %s" % hits)
    outside_homes = (intro + pt["homes_heading"] + "\n" + lines_part + fmt).casefold()
    if any(w in outside_homes for w in JUDGMENT_WORDS):
        raise Refuse("the first message holds the word judgment outside the list of homes; the question about "
                     "judgment belongs to the second message only")
    both = text + "\n" + question_text
    leaks = [s for s in leak_strings if s and s.casefold() in both.casefold()]
    if leaks:
        raise Refuse("prompt contains a string that must never reach a sorter: %s" % leaks)
    if NUMBERED.search(both):
        raise Refuse("prompt contains a line that starts like a numbered item")
    return BuiltPrompt(text, instruction_text, key, home_order, line_seed, home_seed,
                       prompt_text_sha256=pt["sha256"], question_text=question_text, homes_block=homes_entries)
