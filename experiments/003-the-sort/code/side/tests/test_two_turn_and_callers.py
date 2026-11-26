"""Tests for the two-turn sort (pick 9) and the real callers (picks 10 to 12), 2026-11-25.

Brief: ../BUILD_BRIEF_test1_two_turn_and_callers.md. FIXTURE content and fakes only. No test makes a real model
call and no test reads a real key: fakes_first (imported first) has already replaced the key function, the key file
opener, the transport and urllib's opener with tripwires, and every test that needs the switch "on" passes a plain
dict as env; os.environ is never given SORT_REAL_CALLS.
"""
import fakes_first  # noqa: F401  (must stay the first import)

import contextlib
import copy
import glob
import io
import json
import os
import re
import shutil
import unittest

from common import Refuse, HERE, make_scratch_dir, sha256_file, sha256_bytes, write_json

A, B, C = "FIXTURE-A", "FIXTURE-B", "FIXTURE-C"
CLOUD = [("S%d" % i, "cloud") for i in range(1, 7)]
LOCAL = [("L1", "local"), ("L2", "local")]
CP6 = {"6": {"settled_min": 5, "leaning_min": 4}}
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
FIXTURE_HOMES = os.path.join(HERE, "fixtures", "homes_fixture.json")
DENY = os.path.join(HERE, "deny_list.txt")
PROMPT_TEXT = os.path.join(HERE, "prompt_text.json")
FIXTURE_LINES = ["FIXTURE line %d, not a real lesson." % i for i in range(1, 18)]
QUESTION = "what remains judgment once this lesson has its home?"
# From the fix round (tests/test_fix_round.py, taken 19:22:01 EST from the code before fix C): the one-message prompt.
OLD_PROMPT_SHA = {(11, 22): "3ed4fcd5287b8bd9b06be445f94ef004ae9cb7cf9adffe83ea842ea46ac90c83",
                  (5, 6): "286efcefdc95310479e961bf2054f91a9849d95d2fb9c5dc918e8e73008973c9"}
OLD_DRYRUN_V2_PROMPTS = "06fb0002c0526c6edc05976bc808b9cbc901321aed255e485cf0b4facd6f2322"
ALLOW = {"SORT_REAL_CALLS": "allow"}  # a plain dict passed as env; never os.environ
FAKE_KEY = "fake-key-Q7xW2pL9vN4rT6yZ8bC1"
EIGHT = ["anthropic:claude-fable-5-2", "anthropic:claude-opus-5-5", "openai:gpt-6.2-astra", "openai:gpt-6.2-sol",
         "xai:grok-4.7", "deepseek:deepseek-v4-pro", "ollama-local-a:qwen3.8:27b-draft4-text",
         "ollama-local-b:gemma4:e4b-mlx"]


def old_from_new(turn1_text, question=QUESTION):
    """Put back exactly the pieces the split removed from the first message. If the result hashes to the old
    one-message prompt, the first message is the old wording minus these pieces and nothing else."""
    t = turn1_text
    t = t.replace("Use the home names exactly as written.\n\n",
                  "Use the home names exactly as written. Then write one sentence that answers this question: "
                  + question + "\n\n", 1)
    t = t.replace("LABEL | main: HOME | second: HOME or none\n", "LABEL | main: HOME | second: HOME or none | SENTENCE\n",
                  1)
    t = t.replace("or the word none. Separate the three parts",
                  "or the word none. SENTENCE is one sentence that does not contain the character |. Separate the "
                  "four parts", 1)
    return t


def sort_lines(labels, home=A, second="none"):
    return "".join("%s | main: %s | second: %s\n" % (l, home, second) for l in labels)


def question_lines(labels, sentence="FIXTURE sentence."):
    return "".join("%s | %s\n" % (l, sentence) for l in labels)


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = make_scratch_dir("t_2turn_")
        self.addCleanup(shutil.rmtree, self.dir)

    def patch(self, obj, name, value):
        old = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(setattr, obj, name, old)


# ======================= Part 1: the judgment question moves to a second message =======================

class PromptTextFields(Base):
    def test_shipped_file_has_separate_fields_for_each_message_and_is_still_draft(self):
        from prompt_builder import load_prompt_text, TEXT_FIELDS
        pt = load_prompt_text(PROMPT_TEXT)
        self.assertEqual(set(TEXT_FIELDS), {"status", "turn1_intro", "homes_heading", "lessons_heading",
                                            "turn1_reply_format", "question", "turn2_intro", "turn2_reply_format"})
        self.assertTrue(pt["status"].startswith("DRAFT"))
        self.assertEqual(pt["question"], QUESTION)
        self.assertEqual(pt["turn1_intro"].count("{line_count}"), 1)
        self.assertEqual(pt["turn2_intro"].count("{question}"), 1)
        for f in ("turn1_intro", "homes_heading", "lessons_heading", "turn1_reply_format"):
            self.assertNotIn("{question}", pt[f], f)

    def test_loader_refuses_the_question_placeholder_in_a_first_message_field(self):
        from prompt_builder import load_prompt_text
        with open(PROMPT_TEXT, encoding="utf-8") as fh:
            obj = json.load(fh)
        obj["turn1_reply_format"] += "{question}"
        p = os.path.join(self.dir, "pt.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        with self.assertRaisesRegex(Refuse, "first message"):
            load_prompt_text(p)

    def test_loader_refuses_the_old_one_message_fields(self):
        from prompt_builder import load_prompt_text
        with open(PROMPT_TEXT, encoding="utf-8") as fh:
            obj = json.load(fh)
        obj["intro"] = "old"
        p = os.path.join(self.dir, "pt.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        with self.assertRaisesRegex(Refuse, "unknown"):
            load_prompt_text(p)


class FirstMessage(Base):
    def setUp(self):
        super().setUp()
        from homes import load_homes
        from prompt_builder import load_deny_list, load_prompt_text
        self.homes = load_homes(FIXTURE_HOMES)[0]
        self.deny = load_deny_list(DENY)
        self.pt = load_prompt_text(PROMPT_TEXT)

    def build(self, homes=None, pt=None, lines=None, ls=11, hs=22):
        from prompt_builder import build_prompt
        return build_prompt(lines or FIXTURE_LINES, homes or self.homes, ls, hs, self.deny,
                            prompt_text=pt or self.pt)

    def test_the_word_judgment_is_nowhere_in_the_first_message_outside_the_homes(self):
        p = self.build()
        outside = p.text.replace(p.homes_block, "")
        self.assertEqual(len(p.text) - len(outside), len(p.homes_block))
        self.assertNotIn("judgment", outside.casefold())
        self.assertNotIn("judgement", outside.casefold())
        self.assertIn(QUESTION, p.question_text)

    def test_the_word_in_a_home_definition_is_allowed(self):
        homes = [dict(h) for h in self.homes]
        homes[0]["definition"] = "FIXTURE definition that names judgment."
        p = self.build(homes=homes)
        self.assertIn("judgment", p.homes_block)

    def test_the_word_in_any_first_message_field_refuses_the_build(self):
        for field in ("turn1_intro", "homes_heading", "lessons_heading", "turn1_reply_format"):
            for word in ("judgment", "Judgement"):
                with self.subTest(field=field, word=word):
                    pt = dict(self.pt)
                    pt[field] = pt[field].replace("\n", " %s\n" % word, 1) if "\n" in pt[field] else pt[field] + word
                    with self.assertRaisesRegex(Refuse, "judgment outside the list of homes"):
                        self.build(pt=pt)

    def test_the_word_in_a_lesson_refuses_the_build(self):
        lines = list(FIXTURE_LINES)
        lines[4] = "FIXTURE line that names judgment."
        with self.assertRaisesRegex(Refuse, "judgment outside the list of homes"):
            self.build(lines=lines)

    def test_the_real_lines_at_the_commit_are_clean(self):
        from lines_loader import load_lines
        src = load_lines(REPO, "441752c", "sheet/SHEET_SHORT_v2.md")
        p = self.build(lines=src["lines"])
        self.assertNotIn("judg", p.text.replace(p.homes_block, "").casefold())

    def test_first_message_is_the_old_wording_minus_the_question_and_sentence_parts(self):
        for (ls, hs), want in OLD_PROMPT_SHA.items():
            with self.subTest(seeds=(ls, hs)):
                p = self.build(ls=ls, hs=hs)
                self.assertEqual(sha256_bytes(old_from_new(p.text).encode("utf-8")), want)
                self.assertNotIn("DRAFT", p.text + p.question_text)

    def test_second_message_carries_the_question_and_its_format(self):
        p = self.build()
        self.assertTrue(p.question_text.startswith("For each lesson, write one sentence that answers this question: "
                                                   + QUESTION + "\n\n"))
        self.assertIn("LABEL | SENTENCE\n", p.question_text)
        self.assertIn("SENTENCE is one sentence that does not contain the character |.", p.question_text)
        self.assertEqual(p.question_sha256, sha256_bytes(p.question_text.encode("utf-8")))
        for k in p.key:
            self.assertNotIn(k["line_text"], p.question_text)

    def test_deny_list_covers_the_second_message(self):
        for field in ("question", "turn2_intro", "turn2_reply_format"):
            with self.subTest(field=field):
                pt = dict(self.pt)
                pt[field] = pt[field].replace("\n", " Temple\n", 1) if "\n" in pt[field] else pt[field] + " Temple"
                with self.assertRaisesRegex(Refuse, "deny list hit"):
                    self.build(pt=pt)


class SortParser(unittest.TestCase):
    labels, homes = ["L01", "L02", "L03"], [A, B, C]

    def p(self, raw, dry=False):
        from reply_parser import parse_sort_reply
        return parse_sort_reply(raw, self.labels, self.homes, dry_run=dry)

    def test_three_part_lines_accepted(self):
        raw = "L01 | main: %s | second: none\nL02 | main: %s | second: %s\nL03 | main: %s | second: none\n" % (A, B, A, C)
        r = self.p(raw)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["rows"], [{"label": "L01", "home_main": A, "home_second": None},
                                     {"label": "L02", "home_main": B, "home_second": A},
                                     {"label": "L03", "home_main": C, "home_second": None}])

    def test_a_sentence_on_the_sort_line_is_refused(self):
        raw = "L01 | main: %s | second: none | A sentence.\n" % A + sort_lines(["L02", "L03"])
        r = self.p(raw)
        self.assertFalse(r["ok"])
        self.assertTrue(any("cannot be placed" in e for e in r["errors"]), r["errors"])

    def test_three_homes_as_an_extra_field_named_as_such(self):
        raw = "L01 | main: %s | second: %s | third: %s\n" % (A, B, C) + sort_lines(["L02", "L03"])
        r = self.p(raw)
        self.assertTrue(any("three or more homes" in e for e in r["errors"]), r["errors"])

    def test_other_refusals_kept(self):
        tail = sort_lines(["L02", "L03"])
        cases = {"unknown main home": ("L01 | main: FIXTURE-Z | second: none\n" + tail, "unknown main home"),
                 "second equals main": ("L01 | main: %s | second: %s\n" % (A, A) + tail, "equals the main home"),
                 "second without main": ("L01 | main: none | second: %s\n" % B + tail, "second home with no main"),
                 "missing label": (tail, "missing label"),
                 "repeated": (tail + tail + "L01 | main: %s | second: none\n" % A, "repeated"),
                 "two in second": ("L01 | main: %s | second: %s, %s\n" % (A, B, C) + tail, "three or more homes"),
                 "DRYRUN in a real run": (sort_lines(self.labels, home="DRYRUN"), "DRYRUN in a run not marked dry"),
                 "not text": (None, "reply is not text")}
        for why, (raw, reason) in cases.items():
            with self.subTest(why=why):
                r = self.p(raw)
                self.assertFalse(r["ok"])
                self.assertEqual(r["rows"], [])
                self.assertEqual(r["raw"], raw)
                self.assertTrue(any(reason in e for e in r["errors"]), r["errors"])


class QuestionParser(unittest.TestCase):
    labels = ["L01", "L02", "L03"]

    def p(self, raw):
        from reply_parser import parse_question_reply
        return parse_question_reply(raw, self.labels)

    def test_accepted(self):
        r = self.p('L02 | Two  "x", café.\nL01 | One.\nL03 | Three.\n')
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["rows"], [{"label": "L01", "sentence": "One."},
                                     {"label": "L02", "sentence": 'Two  "x", café.'},
                                     {"label": "L03", "sentence": "Three."}])

    def test_refusals(self):
        cases = {"missing label": ("L01 | a.\nL02 | b.\n", "missing label"),
                 "repeated": ("L01 | a.\nL01 | a.\nL02 | b.\nL03 | c.\n", "repeated"),
                 "unknown": ("L01 | a.\nL02 | b.\nL03 | c.\nL04 | d.\n", "unknown label"),
                 "empty sentence": ("L01 |  \nL02 | b.\nL03 | c.\n", "cannot be placed"),
                 "pipe": ("L01 | a | b.\nL02 | b.\nL03 | c.\n", "cannot be placed"),
                 "carriage return": ("L01 | a.\r\nL02 | b.\r\nL03 | c.\r\n", "cannot be placed"),
                 "preamble": ("Sure:\nL01 | a.\nL02 | b.\nL03 | c.\n", "cannot be placed"),
                 "sort line": ("L01 | main: %s | second: none\nL02 | b.\nL03 | c.\n" % A, "cannot be placed"),
                 "not text": (None, "reply is not text")}
        for why, (raw, reason) in cases.items():
            with self.subTest(why=why):
                r = self.p(raw)
                self.assertFalse(r["ok"])
                self.assertEqual(r["rows"], [])
                self.assertEqual(r["raw"], raw)
                self.assertTrue(any(reason in e for e in r["errors"]), r["errors"])


class DryCallerTwoTurns(Base):
    def test_takes_the_conversation_and_answers_both_turns_with_the_reserved_word(self):
        from callers import get_caller, Conversation
        from reply_parser import parse_sort_reply, parse_question_reply
        labels = ["L%02d" % i for i in range(1, 18)]
        c = get_caller("dryrun")
        conv = Conversation([{"role": "user", "content": "FIXTURE first message"}], labels)
        r1 = c.call(conv)
        p1 = parse_sort_reply(r1.text, labels, [A, B], dry_run=True)
        self.assertTrue(p1["ok"], p1["errors"])
        self.assertTrue(all(x["home_main"] == "DRYRUN" and x["home_second"] is None for x in p1["rows"]))
        self.assertFalse(parse_sort_reply(r1.text, labels, [A, B], dry_run=False)["ok"])
        conv.messages += [{"role": "assistant", "content": r1.text}, {"role": "user", "content": "FIXTURE second"}]
        r2 = c.call(conv)
        p2 = parse_question_reply(r2.text, labels)
        self.assertTrue(p2["ok"], p2["errors"])
        self.assertTrue(all(x["sentence"] == "DRYRUN" for x in p2["rows"]))
        self.assertEqual((r1.record["turn"], r2.record["turn"]), (1, 2))


def dry_config(out_dir, **over):
    cfg = {"dry_run": True, "caller": "dryrun", "repo": REPO, "commit": "441752c",
           "lines_path": "sheet/SHEET_SHORT_v2.md", "homes_file": FIXTURE_HOMES, "deny_list": DENY,
           "prompt_text": PROMPT_TEXT,
           "sorters": [{"name": "S1", "group": "cloud", "provider": "p1"},
                       {"name": "S2", "group": "cloud", "provider": "p2"}],
           "groups": {}, "repeats": 1, "master_seed": 5, "out_dir": out_dir}
    cfg.update(over)
    return cfg


def scripted_dry(turn1=None, turn2=None, seen=None):
    """A stand-in for the dry-run caller (is_dry, name dryrun) whose replies can be junk on either turn. It keeps a
    deep copy of every conversation it was given in `seen`."""
    from callers import Reply, DryRunCaller

    class Scripted(DryRunCaller):
        def call(self, conversation, env=None):
            if seen is not None:
                seen.append(copy.deepcopy(conversation.messages))
            n = sum(1 for m in conversation.messages if m["role"] == "user")
            real = DryRunCaller.call(self, conversation, env)
            override = turn1 if n == 1 else turn2
            return Reply(real.text if override is None else override, real.record)
    return Scripted


class RunnerTwoTurns(Base):
    def run_with(self, caller_cls):
        import callers
        import runner
        self.patch(callers, "CALLERS", dict(callers.CALLERS, dryrun=caller_cls))
        out = runner.run(dry_config(os.path.join(self.dir, "run")))
        with open(os.path.join(out, "results", "S1__r1.json"), encoding="utf-8") as fh:
            res = json.load(fh)
        with open(os.path.join(out, "prompts", "S1__r1.json"), encoding="utf-8") as fh:
            prm = json.load(fh)
        return out, res, prm

    def test_turn_two_is_sent_in_the_same_conversation_after_the_sort_parses(self):
        seen = []
        out, res, prm = self.run_with(scripted_dry(seen=seen))
        self.assertEqual(len(seen), 4)  # two sorters, two turns each
        first, second = seen[0], seen[1]
        self.assertEqual(first, [{"role": "user", "content": prm["text"]}])
        self.assertEqual(second[:1], first)
        self.assertEqual(second[1], {"role": "assistant", "content": res["raw_reply"]})
        self.assertEqual(second[2], {"role": "user", "content": prm["question_text"]})
        self.assertEqual(len(second), 3)
        self.assertTrue(res["parse_ok"])
        self.assertTrue(res["turn2"]["sent"] and res["turn2"]["parse_ok"])
        self.assertEqual(len(res["turn2"]["rows"]), 17)
        self.assertNotIn("sentence", json.dumps(res["rows"]))
        self.assertEqual([c["turn"] for c in res["calls"]], [1, 2])

    def test_turn_one_unparsed_means_turn_two_is_not_sent_and_the_result_says_so(self):
        seen = []
        out, res, prm = self.run_with(scripted_dry(turn1="FIXTURE junk", seen=seen))
        self.assertEqual(len(seen), 2)  # one call per sorter: turn 1 only
        self.assertFalse(res["parse_ok"])
        self.assertEqual(res["raw_reply"], "FIXTURE junk")
        self.assertFalse(res["turn2"]["sent"])
        self.assertIn("not asked", res["turn2"]["not_sent_reason"])
        self.assertIsNone(res["turn2"]["raw_reply"])
        self.assertEqual([c["turn"] for c in res["calls"]], [1])

    def test_turn_two_unparsed_keeps_the_sort_and_the_raw_reply(self):
        out, res, prm = self.run_with(scripted_dry(turn2="FIXTURE junk answer"))
        self.assertTrue(res["parse_ok"])
        self.assertEqual(len(res["rows"]), 17)
        self.assertTrue(res["turn2"]["sent"])
        self.assertFalse(res["turn2"]["parse_ok"])
        self.assertEqual(res["turn2"]["raw_reply"], "FIXTURE junk answer")
        self.assertEqual(res["turn2"]["rows"], [])

    def test_dry_run_prompts_are_the_old_wording_split(self):
        """The 24 dry-run prompts of config_dryrun.json, with the removed pieces put back, are byte for byte the
        earlier builder's scratch/dryrun_v2 prompts (seeds and shuffles unchanged too)."""
        import hashlib
        import runner
        with open(os.path.join(HERE, "config_dryrun.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        cfg["out_dir"] = os.path.join(self.dir, "run")
        out = runner.run(cfg)
        hs = []
        for s in cfg["sorters"]:
            for k in range(1, cfg["repeats"] + 1):
                with open(os.path.join(out, "prompts", "%s__r%d.json" % (s["name"], k)), encoding="utf-8") as fh:
                    prm = json.load(fh)
                self.assertEqual(prm["prompt_sha256"], sha256_bytes(prm["text"].encode("utf-8")))
                hs.append(sha256_bytes(old_from_new(prm["text"]).encode("utf-8")))
        self.assertEqual(hashlib.sha256("\n".join(hs).encode()).hexdigest(), OLD_DRYRUN_V2_PROMPTS)


# ---------- the tally and turn 2 ----------

def tcfg(run_dir, sorters=CLOUD, repeats=3, **over):
    from fixture_runs import fixture_provider
    cfg = {"run_dir": run_dir,
           "sorters": [{"name": n, "group": g, "provider": fixture_provider(n)} for n, g in sorters],
           "groups": {}, "repeats": repeats,
           "cut_points_by_size": CP6, "bootstrap": {"seed": 7, "draws": 100, "level": 0.95}}
    cfg.update(over)
    return cfg


def tally(cfg):
    from tally import compute
    return compute(cfg, allow_fixture=True)


def rewrite_and_rehash(run_dir, rel, mutate):
    p = os.path.join(run_dir, rel)
    with open(p, encoding="utf-8") as fh:
        obj = json.load(fh)
    mutate(obj)
    write_json(p, obj)
    mp = os.path.join(run_dir, "manifest.json")
    with open(mp, encoding="utf-8") as fh:
        man = json.load(fh)
    for row in man["files"]:
        if row["path"] == rel:
            row["sha256"] = sha256_file(p)
    write_json(mp, man)


def split_assign(sorters):
    per = {s: [A, A if i < 4 else B, A if i < 3 else B] for i, (s, _) in enumerate(sorters)}
    out = {(s, r): per[s] for s, _ in sorters for r in (1, 2, 3)}
    return out


class TallyTurnTwo(Base):
    def sub(self, name):
        d = os.path.join(self.dir, name)
        os.makedirs(d)
        return d

    def mixed_assign(self, both):
        assign = split_assign(CLOUD)
        for s, _ in LOCAL:
            for r in (1, 2, 3):
                assign[(s, r)] = [(A, B), A, B] if s == "L1" else [B, A, (B, C)]
        assign[("S2", 2)] = None
        assign[("L2", 3)] = None
        return assign

    def test_removing_or_breaking_every_turn_two_reply_leaves_every_count_unchanged(self):
        from fixture_runs import make_run
        both = CLOUD + LOCAL
        assign = self.mixed_assign(both)
        base = tally(tcfg(make_run(self.sub("ok"), both, 3, [A, B, C], 3, assign), sorters=both))[0]
        for mode in ("missing", "broken"):
            with self.subTest(mode=mode):
                t2 = {(s, r): mode for s, _ in both for r in (1, 2, 3)}
                rd = make_run(self.sub(mode), both, 3, [A, B, C], 3, assign, turn2=t2)
                rep, judg = tally(tcfg(rd, sorters=both))
                for g in ("cloud", "local"):
                    a = {k: v for k, v in base["groups"][g].items() if k != "turn2"}
                    b = {k: v for k, v in rep["groups"][g].items() if k != "turn2"}
                    self.assertEqual(a, b, g)
                self.assertEqual(base["parse_failures_listed"], rep["parse_failures_listed"])
                self.assertEqual(rep["groups"]["cloud"]["turn2"], {"sent": 17, "failed": 17, "not_sent": 1,
                                                                   "of_replies": 18})
                self.assertIn("(question reply failed to parse; no sentence)", judg)
                self.assertNotIn("FIXTURE sentence", judg)

    def test_turn_two_failures_counted_and_shown_per_group(self):
        from fixture_runs import make_run
        both = CLOUD + LOCAL
        assign = self.mixed_assign(both)
        t2 = {("S1", 1): "broken", ("S3", 2): "missing", ("L1", 1): "broken"}
        rep, judg = tally(tcfg(make_run(self.dir, both, 3, [A, B, C], 3, assign, turn2=t2), sorters=both))
        self.assertEqual(rep["groups"]["cloud"]["turn2"], {"sent": 17, "failed": 2, "not_sent": 1, "of_replies": 18})
        self.assertEqual(rep["groups"]["local"]["turn2"], {"sent": 5, "failed": 1, "not_sent": 1, "of_replies": 6})
        self.assertIn("  [cloud] S2 repeat 2: (sort reply failed to parse; question not asked)", judg)
        self.assertIn("  [cloud] S1 repeat 1: (question reply failed to parse; no sentence)", judg)
        self.assertIn('  [cloud] S1 repeat 2: FIXTURE sentence  for line 1 by S1 r2, "quoted", café.', judg)

    def test_tally_prints_the_turn_two_line_per_group(self):
        import tally as tally_mod
        from fixture_runs import make_run
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)},
                      turn2={("S1", 1): "broken"})
        cp = os.path.join(self.dir, "cfg.json")
        with open(cp, "w", encoding="utf-8") as fh:
            json.dump(tcfg(rd, out_dir=os.path.join(self.dir, "out")), fh)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = tally_mod.main(["--config", cp, "--allow-fixture"])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertIn("  turn 2 (the question): failed 1 of 18 sent; not sent 0", buf.getvalue())

    def test_reparse_covers_turn_two(self):
        from fixture_runs import make_run

        def good():
            d = self.sub("r%d" % len(os.listdir(self.dir)))
            return make_run(d, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)})
        cases = {"raw changed, rows kept": lambda r: r["turn2"].update(raw_reply="FIXTURE other"),
                 "row sentence changed, raw kept": lambda r: r["turn2"]["rows"][0].update(sentence="FIXTURE x."),
                 "marked failed, raw parses": lambda r: r["turn2"].update(parse_ok=False, rows=[]),
                 "not sent after a parsed sort": lambda r: r["turn2"].update(sent=False)}
        for why, mutate in cases.items():
            with self.subTest(why=why):
                rd = good()
                rewrite_and_rehash(rd, "results/S2__r1.json", mutate)
                with self.assertRaisesRegex(Refuse, "turn 2"):
                    tally(tcfg(rd))

    def test_turn_two_sent_after_a_failed_sort_is_refused(self):
        from fixture_runs import make_run
        assign = {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}
        assign[("S4", 1)] = None
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, assign)
        rewrite_and_rehash(rd, "results/S4__r1.json",
                           lambda r: r["turn2"].update(sent=True, raw_reply="L01 | x.\nL02 | y.\n"))
        with self.assertRaisesRegex(Refuse, "turn 2"):
            tally(tcfg(rd))

    def test_a_result_without_a_turn_two_record_is_refused(self):
        from fixture_runs import make_run
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)})
        rewrite_and_rehash(rd, "results/S1__r1.json", lambda r: r.pop("turn2"))
        with self.assertRaisesRegex(Refuse, "turn 2"):
            tally(tcfg(rd))


class TallySettingsGroups(Base):
    """Helix record 82519 (the Codex seat's read-back, HQ confirmed): settings had the key "groups" twice, so the
    written report lost the config's min_providers."""

    def test_settings_carry_each_groups_min_providers(self):
        from fixture_runs import make_run
        provs = dict(zip([s for s, _ in CLOUD], ["p1", "p1", "p2", "p2", "p3", "p3"]))
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)},
                      providers=provs)
        cfg = tcfg(rd, groups={"cloud": {"min_providers": 3}})
        cfg["sorters"] = [{"name": s, "group": g, "provider": provs[s]} for s, g in CLOUD]
        rep, _ = tally(cfg)
        self.assertEqual(rep["settings"]["groups"], {"cloud": {"min_providers": 3}})
        self.assertEqual(rep["settings"]["groups_note"], "computed separately and never pooled")


# ======================= Part 2: the real callers, with fakes only =======================

def fake_response(kind, text, model, complete=True):
    if kind == "anthropic":
        return {"id": "msg_fake", "type": "message", "role": "assistant", "model": model,
                "content": [{"type": "thinking", "thinking": "", "signature": "FIXTURE"},
                            {"type": "text", "text": text}],
                "stop_reason": "end_turn" if complete else "max_tokens", "stop_details": None,
                "usage": {"input_tokens": 11, "output_tokens": 22}}
    if kind in ("openai", "xai"):
        return {"id": "resp_fake", "object": "response", "model": model,
                "status": "completed" if complete else "incomplete",
                "output": [{"type": "reasoning", "summary": []},
                           {"type": "message", "role": "assistant",
                            "content": [{"type": "output_text", "text": text, "annotations": []}]}],
                "usage": {"input_tokens": 11, "output_tokens": 22, "output_tokens_details": {"reasoning_tokens": 5},
                          "total_tokens": 33}}
    if kind == "deepseek":
        return {"id": "fake", "object": "chat.completion", "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text,
                                                     "reasoning_content": "FIXTURE reasoning"},
                             "finish_reason": "stop" if complete else "length"}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33,
                          "completion_tokens_details": {"reasoning_tokens": 5}}}
    if kind == "ollama":
        return {"model": model, "created_at": "FIXTURE", "message": {"role": "assistant", "content": text},
                "done": complete, "done_reason": "stop" if complete else "length",
                "prompt_eval_count": 11, "eval_count": 22}
    raise AssertionError(kind)


def kind_of(url):
    for k, host in (("anthropic", "api.anthropic.com"), ("openai", "api.openai.com"), ("xai", "api.x.ai"),
                    ("deepseek", "api.deepseek.com"), ("ollama", ":11434")):
        if host in url:
            return k
    raise AssertionError(url)


class Spies(object):
    """Recording fakes for the key function and the transport."""

    def __init__(self, reply=None, fail=None):
        self.keys, self.posts = [], []
        self.reply, self.fail = reply, fail

    def read_key(self, source, env=None, **kw):
        self.keys.append(source)
        headers = {"anthropic-workspace-id": "FIXTURE-workspace"} if source == "anthropic" else {}
        return FAKE_KEY, headers

    def post(self, url, headers, body, timeout, env=None):
        self.posts.append({"url": url, "headers": dict(headers), "body": copy.deepcopy(body), "timeout": timeout})
        if self.fail:
            raise self.fail(headers)
        kind = kind_of(url)
        msgs = body.get("messages") or body.get("input")
        text = self.reply(msgs) if self.reply else "ready"
        return fake_response(kind, text, body["model"])


def reply_by_turn(msgs):
    labels = re.findall(r"(?m)^(L\d\d): ", msgs[0]["content"])
    if sum(1 for m in msgs if m["role"] == "user") == 1:
        return sort_lines(labels)
    return question_lines(labels, "Fake sentence.")


class RealBase(Base):
    def install(self, spies):
        import real_callers
        self.patch(real_callers, "read_key", spies.read_key)
        self.patch(real_callers, "http_post_json", spies.post)
        return real_callers


class TestsRunGuarded(unittest.TestCase):
    def test_switch_absent_from_this_process_and_tripwires_in_place(self):
        import real_callers
        self.assertNotIn("SORT_REAL_CALLS", os.environ)
        for name in ("read_key", "http_post_json", "_urlopen", "_open"):
            self.assertTrue(getattr(getattr(real_callers, name), "is_tripwire", False), name)

    def test_no_test_file_names_a_real_key_path_or_key_variable(self):
        from real_callers import scan_for_key_names
        files = sorted(glob.glob(os.path.join(HERE, "tests", "*.py"))) + [os.path.join(HERE, "selftest.py")]
        self.assertGreater(len(files), 5)
        self.assertEqual(scan_for_key_names(files), [])

    def test_the_scan_can_see_a_named_path(self):
        from real_callers import scan_for_key_names
        d = make_scratch_dir("t_2turn_scan_")
        self.addCleanup(shutil.rmtree, d)
        p = os.path.join(d, "x.py")
        with open(p, "w") as fh:
            fh.write("path = '~/" + "." + "private-fixture-keys" + ".env'\nname = 'X" + "_API" + "_KEY'\n")
        self.assertEqual(len(scan_for_key_names([p])), 2)


class SwitchGuard(RealBase):
    def test_require_switch_refuses_unless_exactly_allow(self):
        from real_callers import require_switch
        for env in ({}, {"SORT_REAL_CALLS": "yes"}, {"SORT_REAL_CALLS": "Allow"}, {"SORT_REAL_CALLS": ""}):
            with self.subTest(env=env):
                with self.assertRaisesRegex(Refuse, "SORT_REAL_CALLS"):
                    require_switch(env)
        require_switch(ALLOW)

    def test_real_key_function_refuses_before_touching_any_file(self):
        real_read_key = fakes_first.REAL["read_key"]
        opened = []
        with self.assertRaisesRegex(Refuse, "SORT_REAL_CALLS"):
            real_read_key("anthropic", env={}, opener=lambda *a, **k: opened.append(a))
        with self.assertRaisesRegex(Refuse, "SORT_REAL_CALLS"):
            real_read_key("anthropic", env={})  # the module opener is a tripwire: reaching it would fail differently
        self.assertEqual(opened, [])

    def test_real_transport_refuses_before_opening_a_connection(self):
        real_post = fakes_first.REAL["http_post_json"]
        with self.assertRaisesRegex(Refuse, "SORT_REAL_CALLS"):
            real_post("http://local-b.example.invalid:11434/api/chat", {}, {"model": "x"}, 5, env={})

    def test_every_adapter_refuses_with_the_switch_unset_before_a_key_or_a_connection(self):
        from callers import get_caller, Conversation
        spies = Spies()
        self.install(spies)
        for name in EIGHT:
            with self.subTest(adapter=name):
                with self.assertRaisesRegex(Refuse, "SORT_REAL_CALLS"):
                    get_caller(name).call(Conversation([{"role": "user", "content": "x"}], []), env={})
        self.assertEqual((spies.keys, spies.posts), ([], []))

    def test_a_real_run_with_the_switch_unset_refuses_before_writing_anything(self):
        import runner
        spies = Spies()
        self.install(spies)
        cfg = real_config(os.path.join(self.dir, "run"))
        with self.assertRaisesRegex(Refuse, "SORT_REAL_CALLS"):
            runner.run(cfg, env={})
        self.assertFalse(os.path.exists(cfg["out_dir"]))
        self.assertEqual((spies.keys, spies.posts), ([], []))


class KeyFunction(Base):
    def sources(self, obj):
        p = os.path.join(self.dir, "key_sources.local.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        return p

    def keyfile(self, name, text):
        p = os.path.join(self.dir, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def read(self, source, sources_path):
        return fakes_first.REAL["read_key"](source, env=ALLOW, sources_path=sources_path, opener=open)

    def test_reads_a_name_value_line_and_a_whole_file(self):
        f1 = self.keyfile("drop.env", "# FIXTURE\nOTHER=1\nexport FIXTURE_NAME=\"%s\"\n" % FAKE_KEY)
        f2 = self.keyfile("whole.txt", FAKE_KEY + "\n")
        sp = self.sources({"anthropic": {"kind": "env_line", "file": f1, "name": "FIXTURE_NAME",
                                         "headers": {"anthropic-workspace-id": "FIXTURE-ws"}},
                           "deepseek": {"kind": "whole_file", "file": f2}})
        self.assertEqual(self.read("anthropic", sp), (FAKE_KEY, {"anthropic-workspace-id": "FIXTURE-ws"}))
        self.assertEqual(self.read("deepseek", sp), (FAKE_KEY, {}))

    def test_refusals_never_carry_the_key(self):
        f1 = self.keyfile("drop.env", "FIXTURE_NAME=%s\n" % FAKE_KEY)
        cases = {"placeholder": ({"openai": {"kind": "whole_file", "file": "<path to the key file>"}}, "openai",
                                 "placeholder"),
                 "no entry": ({"openai": {"kind": "whole_file", "file": f1}}, "xai", "no entry"),
                 "name absent": ({"xai": {"kind": "env_line", "file": f1, "name": "OTHER"}}, "xai", "no line"),
                 "unknown kind": ({"xai": {"kind": "FIXTURE-unknown-kind", "file": f1}}, "xai", "kind"),
                 "missing file": ({"xai": {"kind": "whole_file", "file": f1 + ".nope"}}, "xai", "cannot be read"),
                 "header placeholder": ({"xai": {"kind": "env_line", "file": f1, "name": "FIXTURE_NAME",
                                                 "headers": {"x": "<fill me>"}}}, "xai", "placeholder")}
        for why, (obj, source, reason) in cases.items():
            with self.subTest(why=why):
                with self.assertRaises(Refuse) as cm:
                    self.read(source, self.sources(obj))
                self.assertIn(reason, str(cm.exception))
                self.assertNotIn(FAKE_KEY[6:], str(cm.exception))

    def test_template_ships_placeholders_only_and_is_refused_as_is(self):
        tp = os.path.join(HERE, "key_sources.local.TEMPLATE.json")
        with open(tp, encoding="utf-8") as fh:
            obj = json.load(fh)
        self.assertEqual(sorted(k for k in obj if not k.startswith("_")), ["anthropic", "deepseek", "openai", "xai"])
        for source in ("anthropic", "deepseek", "openai", "xai"):
            for v in obj[source].values():
                if isinstance(v, str) and v not in ("env_line", "whole_file"):
                    self.assertTrue(v.startswith("<") and v.endswith(">"), v)
            with self.assertRaisesRegex(Refuse, "placeholder"):
                self.read(source, tp)
        self.assertFalse(os.path.exists(os.path.join(HERE, "key_sources.local.json")))


EXPECTED_BODIES = {
    "anthropic:claude-fable-5-2": ("https://api.anthropic.com/v1/messages",
                                   {"model": "claude-fable-5-2", "max_tokens": 19000, "thinking": {"type": "adaptive"},
                                    "output_config": {"effort": "high"}}, "messages"),
    "anthropic:claude-opus-5-5": ("https://api.anthropic.com/v1/messages",
                                  {"model": "claude-opus-5-5", "max_tokens": 19000, "thinking": {"type": "adaptive"},
                                   "output_config": {"effort": "high"}}, "messages"),
    "openai:gpt-6.2-astra": ("https://api.openai.com/v1/responses",
                             {"model": "gpt-6.2-astra", "reasoning": {"effort": "high"}, "max_output_tokens": 19000}, "input"),
    "openai:gpt-6.2-sol": ("https://api.openai.com/v1/responses",
                           {"model": "gpt-6.2-sol", "reasoning": {"effort": "high"}, "max_output_tokens": 19000}, "input"),
    "xai:grok-4.7": ("https://api.x.ai/v1/responses", {"model": "grok-4.7", "reasoning": {"effort": "high"}, "max_output_tokens": 19000}, "input"),
    "deepseek:deepseek-v4-pro": ("https://api.deepseek.com/chat/completions",
                                 {"model": "deepseek-v4-pro", "thinking": {"type": "enabled"},
                                  "reasoning_effort": "high", "max_tokens": 19000}, "messages"),
    "ollama-local-a:qwen3.8:27b-draft4-text": ("http://local-a.example.invalid:11434/api/chat",
                                            {"model": "qwen3.8:27b-draft4-text", "stream": False, "think": None,
                                             "options": {"num_predict": 19000}},
                                            "messages"),
    "ollama-local-b:gemma4:e4b-mlx": ("http://local-b.example.invalid:11434/api/chat",
                                     {"model": "gemma4:e4b-mlx", "stream": False, "think": None,
                                      "options": {"num_predict": 19000}}, "messages"),
}


class Adapters(RealBase):
    CONV = [{"role": "user", "content": "FIXTURE one"}, {"role": "assistant", "content": "FIXTURE two"},
            {"role": "user", "content": "FIXTURE three"}]

    def test_eight_adapters_named_with_their_providers(self):
        import real_callers
        self.assertEqual(sorted(real_callers.ADAPTERS), sorted(EIGHT))
        provs = {n: real_callers.get_adapter(n).provider for n in EIGHT}
        self.assertEqual(provs, {EIGHT[0]: "anthropic", EIGHT[1]: "anthropic", EIGHT[2]: "openai",
                                 EIGHT[3]: "openai", EIGHT[4]: "xai", EIGHT[5]: "deepseek",
                                 EIGHT[6]: "ollama-local-a", EIGHT[7]: "ollama-local-b"})

    def test_each_request_holds_only_the_messages_given_and_the_documented_settings(self):
        from callers import get_caller, Conversation
        spies = Spies()
        self.install(spies)
        for name in EIGHT:
            with self.subTest(adapter=name):
                spies.posts.clear()
                url, settings, field = EXPECTED_BODIES[name]
                reply = get_caller(name).call(Conversation(copy.deepcopy(self.CONV), []), env=ALLOW)
                self.assertEqual(reply.text, "ready")
                post = spies.posts[0]
                self.assertEqual(post["url"], url)
                want = dict(settings)
                want[field] = self.CONV
                self.assertEqual(post["body"], want)
                for banned in ("system", "tools", "instructions", "previous_response_id", "temperature", "top_p",
                               "top_k", "fallbacks", "conversation"):
                    self.assertNotIn(banned, post["body"])

    def test_headers_carry_the_key_and_are_never_saved(self):
        from callers import get_caller, Conversation
        spies = Spies()
        self.install(spies)
        for name in EIGHT:
            with self.subTest(adapter=name):
                spies.posts.clear()
                reply = get_caller(name).call(Conversation([{"role": "user", "content": "x"}], []), env=ALLOW)
                h = spies.posts[0]["headers"]
                if name.startswith("anthropic"):
                    self.assertEqual(h.get("x-api-key"), FAKE_KEY)
                    self.assertEqual(h.get("anthropic-version"), "2026-10-21")
                    self.assertEqual(h.get("anthropic-workspace-id"), "FIXTURE-workspace")
                elif name.startswith("ollama"):
                    self.assertNotIn(FAKE_KEY, json.dumps(h))
                else:
                    self.assertEqual(h.get("Authorization"), "Bearer " + FAKE_KEY)
                saved = json.dumps(reply.record)
                self.assertNotIn(FAKE_KEY, saved)
                for word in ("x-api-key", "Authorization", "anthropic-workspace-id", "FIXTURE-workspace"):
                    self.assertNotIn(word, saved)
        self.assertEqual(spies.keys.count("anthropic"), 2)
        self.assertNotIn("ollama", " ".join(spies.keys))

    def test_everything_that_comes_back_is_kept(self):
        from callers import get_caller, Conversation
        spies = Spies()
        self.install(spies)
        rec = get_caller("deepseek:deepseek-v4-pro").call(
            Conversation([{"role": "user", "content": "x"}], []), env=ALLOW).record
        self.assertEqual(rec["caller"], "deepseek:deepseek-v4-pro")
        self.assertEqual(rec["turn"], 1)
        self.assertEqual((rec["model_requested"], rec["model_reported"], rec["model_matches"]),
                         ("deepseek-v4-pro", "deepseek-v4-pro", True))
        self.assertEqual(json.loads(rec["usage_json"])["completion_tokens_details"], {"reasoning_tokens": 5})
        self.assertEqual(json.loads(rec["settings_sent_json"]),
                         {"model": "deepseek-v4-pro", "thinking": {"type": "enabled"},
                          "reasoning_effort": "high", "max_tokens": 19000})
        self.assertEqual(json.loads(rec["response_body_json"])["choices"][0]["message"]["reasoning_content"],
                         "FIXTURE reasoning")
        self.assertRegex(rec["started_at"], r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d [A-Z]+$")
        self.assertRegex(rec["finished_at"], r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d [A-Z]+$")
        self.assertIs(rec["complete"], True)
        self.assertEqual(rec["stop"], "stop")
        self.assertIsNone(rec["error"])

    def test_a_reported_model_that_differs_is_flagged_not_hidden(self):
        from callers import get_caller, Conversation
        spies = Spies()
        self.install(spies)
        orig = spies.post

        def other_model(url, headers, body, timeout, env=None):
            r = orig(url, headers, body, timeout, env)
            r["model"] = "claude-opus-4-8"
            return r
        self.patch(__import__("real_callers"), "http_post_json", other_model)
        rec = get_caller("anthropic:claude-fable-5-2").call(
            Conversation([{"role": "user", "content": "x"}], []), env=ALLOW).record
        self.assertEqual((rec["model_reported"], rec["model_matches"]), ("claude-opus-4-8", False))

    def test_an_incomplete_reply_gives_no_text_and_keeps_the_partial_text(self):
        import real_callers
        from callers import get_caller, Conversation
        spies = Spies()
        self.install(spies)
        for name in EIGHT:
            with self.subTest(adapter=name):
                def partial(url, headers, body, timeout, env=None):
                    return fake_response(kind_of(url), "L01 | main: half", body["model"], complete=False)
                self.patch(real_callers, "http_post_json", partial)
                r = get_caller(name).call(Conversation([{"role": "user", "content": "x"}], []), env=ALLOW)
                self.assertIsNone(r.text)
                self.assertIs(r.record["complete"], False)
                self.assertEqual(r.record["partial_text"], "L01 | main: half")

    def test_a_refusal_stop_is_a_failed_turn_and_no_fallback_is_asked_for(self):
        import real_callers
        from callers import get_caller, Conversation
        spies = Spies()
        self.install(spies)

        def refused(url, headers, body, timeout, env=None):
            r = fake_response("anthropic", "", body["model"])
            r["stop_reason"], r["stop_details"] = "refusal", {"type": "refusal", "category": "FIXTURE"}
            return r
        self.patch(real_callers, "http_post_json", refused)
        r = get_caller("anthropic:claude-opus-5-5").call(Conversation([{"role": "user", "content": "x"}], []),
                                                         env=ALLOW)
        self.assertIsNone(r.text)
        self.assertEqual(r.record["stop"], "refusal")
        self.assertIn("FIXTURE", r.record["response_body_json"])

    def test_messages_must_alternate_from_a_user_message(self):
        from callers import get_caller, Conversation
        spies = Spies()
        self.install(spies)
        for bad in ([], [{"role": "assistant", "content": "x"}],
                    [{"role": "user", "content": "x"}, {"role": "user", "content": "y"}],
                    [{"role": "system", "content": "x"}], [{"role": "user", "content": "x", "name": "n"}]):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(Refuse, "messages"):
                    get_caller("openai:gpt-6.2-sol").call(Conversation(bad, []), env=ALLOW)
        self.assertEqual(spies.posts, [])


class FailedCallSavesNoKey(RealBase):
    def echoing_error(self):
        """A 401 whose body echoes the key the request carried (whole, and its first and last characters), as some
        makers do. A request that carried no key (Ollama) gets a body that says so."""
        import real_callers

        def make(headers):
            sent = headers.get("x-api-key") or headers.get("Authorization", "")[len("Bearer "):]
            if not sent:
                return real_callers.TransportError(401, '{"error": "FIXTURE: no key was sent"}')
            body = ('{"error": {"message": "Incorrect API key provided: %s. It starts %s and ends %s."}}'
                    % (sent, sent[:8], sent[-6:]))
            return real_callers.TransportError(401, body)
        return make

    def test_an_error_body_that_echoes_the_key_is_redacted(self):
        from callers import get_caller, Conversation
        spies = Spies(fail=self.echoing_error())
        self.install(spies)
        r = get_caller("openai:gpt-6.2-astra").call(Conversation([{"role": "user", "content": "x"}], []), env=ALLOW)
        self.assertIsNone(r.text)
        saved = json.dumps(r.record)
        self.assertIn("401", saved)
        for frag in (FAKE_KEY, FAKE_KEY[:8], FAKE_KEY[-6:], FAKE_KEY[9:20]):
            self.assertNotIn(frag, saved)

    def test_a_whole_run_whose_calls_fail_writes_and_prints_no_key(self):
        import runner
        spies = Spies(fail=self.echoing_error())
        self.install(spies)
        cfg = real_config(os.path.join(self.dir, "run"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = runner.run(cfg, env=ALLOW)
        texts = [buf.getvalue()]
        for root, _, fs in os.walk(out):
            for f in fs:
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    texts.append(fh.read())
        self.assertGreater(len(texts), 5)
        joined = "\n".join(texts)
        self.assertIn("401", joined)
        for frag in (FAKE_KEY, FAKE_KEY[:8], FAKE_KEY[-6:], FAKE_KEY[9:20]):
            self.assertNotIn(frag, joined)
        with open(os.path.join(out, "results", "S1__r1.json"), encoding="utf-8") as fh:
            res = json.load(fh)
        self.assertFalse(res["parse_ok"])
        self.assertIsNone(res["raw_reply"])
        self.assertFalse(res["turn2"]["sent"])


def real_config(out_dir, **over):
    cfg = {"dry_run": False, "caller": "by_sorter", "repo": REPO, "commit": "441752c",
           "lines_path": "sheet/SHEET_SHORT_v2.md", "homes_file": FIXTURE_HOMES, "deny_list": DENY,
           "prompt_text": PROMPT_TEXT,
           "sorters": [{"name": "S1", "group": "cloud", "provider": "anthropic"},
                       {"name": "S2", "group": "cloud", "provider": "openai"},
                       {"name": "L1", "group": "local", "provider": "ollama-local-a"},
                       {"name": "L2", "group": "local", "provider": "ollama-local-b"}],
           "real_callers": {"S1": "anthropic:claude-fable-5-2", "S2": "openai:gpt-6.2-astra",
                            "L1": "ollama-local-a:qwen3.8:27b-draft4-text", "L2": "ollama-local-b:gemma4:e4b-mlx"},
           "groups": {}, "repeats": 1, "master_seed": 9, "out_dir": out_dir}
    cfg.update(over)
    return cfg


class RealRunWithFakes(RealBase):
    def test_a_by_sorter_run_end_to_end_is_tallied_as_data_by_its_listed_callers(self):
        import runner
        from tally import compute
        spies = Spies(reply=reply_by_turn)
        self.install(spies)
        cfg = real_config(os.path.join(self.dir, "run"))
        out = runner.run(cfg, env=ALLOW)
        with open(os.path.join(out, "manifest.json"), encoding="utf-8") as fh:
            man = json.load(fh)
        self.assertEqual(man["caller"], "by_sorter")
        self.assertEqual(man["callers"], sorted(cfg["real_callers"].values()))
        with open(os.path.join(out, "results", "S1__r1.json"), encoding="utf-8") as fh:
            res = json.load(fh)
        self.assertEqual(res["caller"], "anthropic:claude-fable-5-2")
        self.assertTrue(res["parse_ok"] and res["turn2"]["parse_ok"])
        self.assertEqual([c["turn"] for c in res["calls"]], [1, 2])
        self.assertIs(res["calls"][0]["dry_run"], False)
        self.assertEqual(len(spies.posts), 8)
        self.assertEqual(spies.posts[1]["body"]["messages"][1],
                         {"role": "assistant", "content": res["raw_reply"]})
        tc = {"run_dir": out, "sorters": cfg["sorters"], "groups": {}, "repeats": 1, "cut_points_by_size": {},
              "bootstrap": {"seed": 1, "draws": 10, "level": 0.9}, "real_callers": sorted(cfg["real_callers"].values())}
        rep, judg = compute(tc)
        self.assertNotIn("status", rep)
        self.assertEqual(rep["groups"]["cloud"]["turn2"], {"sent": 2, "failed": 0, "not_sent": 0, "of_replies": 2})
        self.assertIn("Fake sentence.", judg)
        tc["real_callers"] = sorted(cfg["real_callers"].values())[1:]
        with self.assertRaisesRegex(Refuse, "not on the tally config's real_callers"):
            compute(tc)

    def test_runner_config_refusals_for_real_callers(self):
        import runner
        spies = Spies()
        self.install(spies)
        rc = real_config("x")["real_callers"]
        cases = {"mapping missing": ({"real_callers": None}, "real_callers"),
                 "sorter not mapped": ({"real_callers": dict(list(rc.items())[:3])}, "every sorter"),
                 "unknown adapter": ({"real_callers": dict(rc, S1="anthropic:claude-x")}, "no caller named"),
                 "provider differs": ({"real_callers": dict(rc, S1="openai:gpt-6.2-sol")}, "provider"),
                 "dry run marked": ({"dry_run": True}, "dry"),
                 "mapping in a dry run": ({"dry_run": True, "caller": "dryrun"}, "real_callers"),
                 "an adapter as the run's caller": ({"caller": "anthropic:claude-fable-5-2"}, "caller must be"),
                 "dry caller mapped": ({"real_callers": dict(rc, S1="dryrun")}, "no caller named")}
        for i, (why, (over, reason)) in enumerate(cases.items()):
            with self.subTest(why=why):
                cfg = real_config(os.path.join(self.dir, "x%d" % i))
                for k, v in over.items():
                    if v is None:
                        cfg.pop(k)
                    else:
                        cfg[k] = v
                with self.assertRaisesRegex(Refuse, reason):
                    runner.check_config(cfg)
        self.assertEqual((spies.keys, spies.posts), ([], []))


class TallyByCaller(Base):
    def run_dir(self, callers, listed=None):
        from fixture_runs import make_run
        return make_run(self.dir, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)},
                        caller="by_sorter", result_callers=callers, manifest_callers=listed)

    def test_each_result_caller_must_be_listed_and_match_the_manifest(self):
        from tally import compute
        callers = {s: ("lab-a" if i % 2 else "lab-b") for i, (s, _) in enumerate(CLOUD)}
        rd = self.run_dir(callers)
        rep, _ = compute(tcfg(rd, real_callers=["lab-a", "lab-b"]))
        self.assertEqual(rep["inputs"]["callers"], ["lab-a", "lab-b"])
        with self.assertRaisesRegex(Refuse, "not on the tally config's real_callers"):
            compute(tcfg(rd, real_callers=["lab-a"]))

    def test_manifest_callers_differing_from_the_results_is_refused(self):
        from tally import compute
        callers = {s: "lab-a" for s, _ in CLOUD}
        rd = self.run_dir(callers, listed=["lab-a", "lab-b"])
        with self.assertRaisesRegex(Refuse, "manifest lists callers"):
            compute(tcfg(rd, real_callers=["lab-a", "lab-b"]))

    def test_by_sorter_may_not_be_named_a_real_caller(self):
        from tally import compute
        rd = self.run_dir({s: "lab-a" for s, _ in CLOUD})
        with self.assertRaisesRegex(Refuse, "real_callers must be"):
            compute(tcfg(rd, real_callers=["lab-a", "by_sorter"]))


class Smoke(RealBase):
    def draft(self):
        with open(os.path.join(HERE, "config_real_DRAFT.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def test_smoke_sends_each_sorter_the_one_line_in_a_fresh_conversation_and_prints_a_status(self):
        import runner
        spies = Spies()
        self.install(spies)
        lines = []
        code = runner.smoke(self.draft(), env=ALLOW, out=lines.append)
        self.assertEqual(code, 0, lines)
        self.assertEqual(len(spies.posts), 8)
        for p in spies.posts:
            msgs = p["body"].get("messages") or p["body"].get("input")
            self.assertEqual(msgs, [{"role": "user", "content": "Reply with the single word ready."}])
        self.assertEqual(len([l for l in lines if ": ok," in l]), 8, lines)

    def test_smoke_reports_a_wrong_word_and_a_failure_per_sorter(self):
        import real_callers
        import runner
        spies = Spies(reply=lambda msgs: "Ready!")
        self.install(spies)
        lines = []
        code = runner.smoke(self.draft(), env=ALLOW, out=lines.append)
        self.assertEqual(code, 1)
        self.assertEqual(len([l for l in lines if "not the word ready" in l]), 8, lines)
        spies2 = Spies(fail=lambda headers: real_callers.TransportError(503, "FIXTURE unavailable"))
        self.install(spies2)
        lines = []
        self.assertEqual(runner.smoke(self.draft(), env=ALLOW, out=lines.append), 1)
        self.assertEqual(len([l for l in lines if "FAILED" in l and "503" in l]), 8, lines)

    def test_smoke_with_the_switch_unset_refuses_every_sorter_and_touches_nothing(self):
        import runner
        spies = Spies()
        self.install(spies)
        lines = []
        code = runner.smoke(self.draft(), env={}, out=lines.append)
        self.assertEqual(code, 1)
        self.assertEqual(len([l for l in lines if "REFUSED" in l and "SORT_REAL_CALLS" in l]), 8, lines)
        self.assertEqual((spies.keys, spies.posts), ([], []))


class DraftConfig(RealBase):
    def test_the_draft_config_has_the_picks_and_passes_the_check_without_a_key_or_a_connection(self):
        import real_callers
        import runner
        spies = Spies()
        self.install(spies)
        with open(os.path.join(HERE, "config_real_DRAFT.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        self.assertIn("DRAFT", cfg["status"])
        self.assertIs(cfg["dry_run"], False)
        self.assertEqual(cfg["caller"], "by_sorter")
        self.assertEqual(cfg["repeats"], 3)
        self.assertEqual(cfg["groups"], {"cloud": {"min_providers": 3}})
        groups = [s["group"] for s in cfg["sorters"]]
        self.assertEqual((groups.count("cloud"), groups.count("local")), (6, 2))
        self.assertEqual(sorted(cfg["real_callers"].values()), sorted(EIGHT))
        self.assertEqual(sorted(cfg["real_callers"]), sorted(s["name"] for s in cfg["sorters"]))
        for s in cfg["sorters"]:
            self.assertEqual(real_callers.get_adapter(cfg["real_callers"][s["name"]]).provider, s["provider"])
        for k in ("homes_file", "deny_list", "prompt_text", "out_dir"):
            self.assertFalse(os.path.isabs(cfg[k]), k)
        cwd = os.getcwd()
        os.chdir(HERE)
        self.addCleanup(os.chdir, cwd)
        runner.check_config(cfg)
        self.assertEqual((spies.keys, spies.posts), ([], []))


if __name__ == "__main__":
    unittest.main()
