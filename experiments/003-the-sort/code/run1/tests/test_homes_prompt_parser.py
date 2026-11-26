"""Tests for the homes loader, the prompt builder, the reply parser and the dry-run caller.

Version 2 (2026-11-25, after PICKS_20261125.md): a reply gives one main home and may give one second home.
Two-turn build (2026-11-25, pick 9): the sort reply is three parts (no sentence); the parser is parse_sort_reply; the
question and its sentences are in the second message (tests/test_two_turn_and_callers.py); the dry caller takes a
conversation.
"""
import fakes_first  # noqa: F401  (must stay the first import)

import json
import os
import shutil
import unittest

from common import Refuse, HERE, make_scratch_dir
from homes import load_homes
from prompt_builder import build_prompt, load_deny_list
from reply_parser import parse_sort_reply as parse_reply
from callers import DryRunCaller, get_caller, Conversation

FIXTURE_HOMES = os.path.join(HERE, "fixtures", "homes_fixture.json")
DENY = os.path.join(HERE, "deny_list.txt")
LINES = ["FIXTURE line %d, not a real lesson." % i for i in range(1, 18)]
A, B, C = "FIXTURE-A", "FIXTURE-B", "FIXTURE-C"


class HomesTests(unittest.TestCase):
    def setUp(self):
        self.dir = make_scratch_dir("t_homes_")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def write(self, obj):
        p = os.path.join(self.dir, "h.json")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(obj if isinstance(obj, str) else json.dumps(obj))
        return p

    def test_fixture_loads(self):
        homes, sha = load_homes(FIXTURE_HOMES)
        self.assertEqual(len(homes), 6)
        self.assertTrue(all(h["name"].startswith("FIXTURE-") for h in homes))
        self.assertEqual(len(sha), 64)

    def test_refusals(self):
        good = [{"name": A, "definition": "FIXTURE definition A."},
                {"name": B, "definition": "FIXTURE definition B."}]
        bad_cases = {
            "one home": good[:1],
            "duplicate name": [good[0], {"name": A, "definition": "other"}],
            "duplicate name by case": [good[0], {"name": A.lower(), "definition": "other"}],
            "duplicate definition": [good[0], {"name": B, "definition": "FIXTURE definition A."}],
            "empty definition": [good[0], {"name": B, "definition": "   "}],
            "empty name": [good[0], {"name": "", "definition": "x"}],
            "reserved name DRYRUN": [good[0], {"name": "DRYRUN", "definition": "x"}],
            "reserved name none": [good[0], {"name": "None", "definition": "x"}],
            "pipe in name": [good[0], {"name": "A|B", "definition": "x"}],
            "comma in name": [good[0], {"name": "A,B", "definition": "x"}],
            "newline in definition": [good[0], {"name": B, "definition": "a\nb"}],
            "extra key": [good[0], {"name": B, "definition": "x", "note": 1}],
            "not a list": {"homes": good},
        }
        for why, obj in bad_cases.items():
            with self.subTest(why=why):
                with self.assertRaises(Refuse):
                    load_homes(self.write(obj))
        with self.assertRaises(Refuse):
            load_homes(self.write("not json"))
        load_homes(self.write(good))


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.homes, _ = load_homes(FIXTURE_HOMES)
        self.deny = load_deny_list(DENY)

    def test_deny_list_ships_required_words(self):
        low = [d.lower() for d in self.deny]
        for word in ["temple", "sheet", "checklist", "readme", "translation table", "tier-35", "lesson-in-the-tool"]:
            self.assertIn(word, low)

    def test_build_is_seeded_and_labelled(self):
        p1 = build_prompt(LINES, self.homes, 11, 22, self.deny)
        p2 = build_prompt(LINES, self.homes, 11, 22, self.deny)
        p3 = build_prompt(LINES, self.homes, 12, 22, self.deny)
        p4 = build_prompt(LINES, self.homes, 11, 23, self.deny)
        self.assertEqual(p1.text, p2.text)
        self.assertNotEqual(p1.text, p3.text)
        self.assertEqual(p1.home_order, p3.home_order)
        self.assertNotEqual(p1.home_order, p4.home_order)
        self.assertEqual([k["label"] for k in p1.key], ["L%02d" % i for i in range(1, 18)])
        self.assertEqual(sorted(k["line_number"] for k in p1.key), list(range(1, 18)))
        for k in p1.key:
            self.assertIn("%s: %s" % (k["label"], LINES[k["line_number"] - 1]), p1.text)
        for h in self.homes:
            self.assertIn(h["name"], p1.text)
            self.assertIn(h["definition"], p1.text)
        self.assertNotIn("what remains judgment once this lesson has its home?", p1.text)
        self.assertIn("what remains judgment once this lesson has its home?", p1.question_text)
        self.assertIn("LABEL | main: HOME | second: HOME or none\n", p1.text)

    def test_deny_hit_in_instructions_refused(self):
        with self.assertRaises(Refuse):
            build_prompt(LINES, self.homes, 1, 2, self.deny + ["remains judgment"])

    def test_deny_hit_in_home_definition_refused(self):
        homes = [dict(h) for h in self.homes]
        homes[0]["definition"] = "FIXTURE definition naming the Temple."
        with self.assertRaises(Refuse):
            build_prompt(LINES, homes, 1, 2, self.deny)

    def test_lines_are_not_deny_checked(self):
        lines = list(LINES)
        lines[3] = "FIXTURE line that says Temple and sheet."
        build_prompt(lines, self.homes, 1, 2, self.deny)

    def test_leak_strings_refused_anywhere(self):
        lines = list(LINES)
        lines[0] = "FIXTURE line holding 441752c."
        with self.assertRaises(Refuse):
            build_prompt(lines, self.homes, 1, 2, self.deny, leak_strings=["441752c"])

    def test_numbered_line_leak_refused(self):
        lines = list(LINES)
        lines[0] = "FIXTURE line\n4. that smuggles a numbered line"
        with self.assertRaises(Refuse):
            build_prompt(lines, self.homes, 1, 2, self.deny)

    def test_wrong_line_count_refused(self):
        with self.assertRaises(Refuse):
            build_prompt(LINES[:16], self.homes, 1, 2, self.deny)


def rep(*rows):
    """Rows are (n, main, second); the two-turn sort line has no sentence part."""
    return "".join("L%02d | main: %s | second: %s\n" % r for r in rows)


GOOD = rep((1, A, "none"), (2, B, A), (3, A, "none"))


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.labels = ["L01", "L02", "L03"]
        self.homes = [A, B, C]

    def p(self, raw, dry=False):
        return parse_reply(raw, self.labels, self.homes, dry_run=dry)

    def test_good_reply_with_one_and_two_homes(self):
        r = self.p(GOOD)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual([(x["label"], x["home_main"], x["home_second"]) for x in r["rows"]],
                         [("L01", A, None), ("L02", B, A), ("L03", A, None)])

    def test_failures_keep_raw_and_drop_rows(self):
        tail = "L02 | main: %s | second: none\nL03 | main: %s | second: none\n" % (A, A)
        cases = {
            "unknown main home": ("L01 | main: FIXTURE-Z | second: none\n" + tail, "unknown main home"),
            "missing label": (tail, "missing label"),
            "repeated label": (tail + tail.splitlines()[0] + "\nL01 | main: %s | second: none\n" % A,
                               "repeated"),
            "three homes, second field holds two": ("L01 | main: %s | second: %s, %s\n" % (A, B, C) + tail,
                                                    "three or more homes"),
            "three homes, extra field": ("L01 | main: %s | second: %s | third: %s\n" % (A, B, C) + tail,
                                         "three or more homes"),
            "two main homes": ("L01 | main: %s, %s | second: none\n" % (A, B) + tail, "more than one main home"),
            "second equals main": ("L01 | main: %s | second: %s\n" % (A, A) + tail,
                                   "second home equals the main home"),
            "second not on list": ("L01 | main: %s | second: FIXTURE-Z\n" % A + tail,
                                   "second home not on the list"),
            "second without main": ("L01 | main: none | second: %s\n" % B + tail,
                                    "second home with no main home"),
            "no main at all": ("L01 | main: none | second: none\n" + tail, "no main home"),
            "old one-home format": ("L01 | %s | s.\n" % A + tail, "cannot be placed"),
            "old one-message format with a sentence": ("L01 | main: %s | second: none | s.\n" % A + tail,
                                                       "cannot be placed"),
            "unplaceable text": ("Here you go:\n" + GOOD, "cannot be placed"),
            "unknown label": (GOOD + "L04 | main: %s | second: none\n" % A, "unknown label"),
            "carriage return": (GOOD.replace("\n", "\r\n"), "cannot be placed"),
            "DRYRUN outside a dry run": (rep(*[(i, "DRYRUN", "none") for i in (1, 2, 3)]),
                                         "DRYRUN in a run not marked dry"),
            "padded home": ("L01 | main:  %s | second: none\n" % A + tail, "unknown main home"),
            "code fence": ("```\n" + GOOD + "```\n", "cannot be placed"),
        }
        for why, (raw, reason) in cases.items():
            with self.subTest(why=why):
                r = self.p(raw)
                self.assertFalse(r["ok"])
                self.assertEqual(r["raw"], raw)
                self.assertEqual(r["rows"], [])
                self.assertTrue(any(reason in e for e in r["errors"]), r["errors"])

    def test_dryrun_only_in_dry(self):
        raw = rep(*[(i, "DRYRUN", "none") for i in (1, 2, 3)])
        self.assertTrue(self.p(raw, dry=True)["ok"])
        self.assertFalse(self.p(raw, dry=False)["ok"])


class CallerTests(unittest.TestCase):
    def test_dry_caller_reply_parses_in_dry_only(self):
        homes, _ = load_homes(FIXTURE_HOMES)
        prompt = build_prompt(LINES, homes, 5, 6, load_deny_list(DENY))
        c = get_caller("dryrun")
        self.assertIsInstance(c, DryRunCaller)
        self.assertTrue(c.is_dry)
        raw = c.call(Conversation([{"role": "user", "content": prompt.text}], prompt.labels)).text
        names = [h["name"] for h in homes]
        r = parse_reply(raw, prompt.labels, names, dry_run=True)
        self.assertTrue(r["ok"], r["errors"])
        self.assertTrue(all(x["home_main"] == "DRYRUN" and x["home_second"] is None for x in r["rows"]))
        self.assertFalse(parse_reply(raw, prompt.labels, names, dry_run=False)["ok"])

    def test_unknown_caller_refused(self):
        with self.assertRaises(Refuse):
            get_caller("some-real-model")


if __name__ == "__main__":
    unittest.main()
