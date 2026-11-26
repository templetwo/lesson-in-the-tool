"""Tests for the fix round (../FIX_BRIEF_test1.md, fixes A to I), 2026-11-25.

Each class is one fix. Each test was run once on the code before its fix and went red there; the README section
"Fix round" has the red and the green runs as printed. FIXTURE content only.

Two-turn build (2026-11-25): the C tests now name the split fields of prompt_text.json, and the two byte-for-byte
guards (OLD_PROMPT_SHA, OLD_DRYRUN_V2_PROMPTS) compare the old one-message prompt with the new first message after
putting back exactly the pieces the split removed (old_from_new in tests/test_two_turn_and_callers.py).
"""
import fakes_first  # noqa: F401  (must stay the first import)

import contextlib
import io
import json
import os
import shutil
import unittest

from common import Refuse, HERE, make_scratch_dir, sha256_file, write_json
from fixture_runs import make_run, fixture_provider
from tally import compute
from freeze import write_freeze, verify_freeze
import freeze
import runner

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
A, B, C = "FIXTURE-A", "FIXTURE-B", "FIXTURE-C"
CLOUD = [("S%d" % i, "cloud") for i in range(1, 7)]
CP6 = {"6": {"settled_min": 5, "leaning_min": 4}}


def tcfg(run_dir, sorters=CLOUD, repeats=3, **over):
    cfg = {"run_dir": run_dir,
           "sorters": [{"name": n, "group": g, "provider": fixture_provider(n)} for n, g in sorters],
           "groups": {}, "repeats": repeats,
           "cut_points_by_size": CP6, "bootstrap": {"seed": 7, "draws": 50, "level": 0.95}}
    cfg.update(over)
    return cfg


def tally(cfg):
    """Fixture runs are refused as data since fix A; these tests use the switch on purpose."""
    return compute(cfg, allow_fixture=True)


def good_run(root, sorters=CLOUD, line_count=2):
    return make_run(root, sorters, 3, [A, B], line_count,
                    {(s, r): [A, B, A, B][:line_count] for s, _ in sorters for r in (1, 2, 3)})


def rewrite_and_rehash(run_dir, rel, mutate):
    """Edit one JSON file of a run and refresh its hash in the manifest, as a careful forger would."""
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


def dry_config(out_dir, **over):
    cfg = {"dry_run": True, "caller": "dryrun", "repo": REPO, "commit": "441752c",
           "lines_path": "sheet/SHEET_SHORT_v2.md",
           "homes_file": os.path.join(HERE, "fixtures", "homes_fixture.json"),
           "deny_list": os.path.join(HERE, "deny_list.txt"),
           "prompt_text": os.path.join(HERE, "prompt_text.json"),
           "sorters": [{"name": "S1", "group": "cloud", "provider": "p1"},
                       {"name": "S2", "group": "cloud", "provider": "p2"}],
           "groups": {}, "repeats": 1, "master_seed": 5, "out_dir": out_dir}
    cfg.update(over)
    return cfg


class Base(unittest.TestCase):
    def setUp(self):
        # addCleanup, not tearDown: a setUp that fails after this line still removes the folder. (The red run of
        # fix C at 19:30 used tearDown and left seven empty t_fix_* folders in scratch/; see the README.)
        self.dir = make_scratch_dir("t_fix_")
        self.addCleanup(shutil.rmtree, self.dir)

    def sub(self, name):
        d = os.path.join(self.dir, name)
        os.makedirs(d)
        return d

    def files(self, root, names):
        for n in names:
            p = os.path.join(root, n)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("FIXTURE " + n)


# ---------- H: the freeze helper and links, and two spellings of one path ----------

class FixH(Base):
    def setUp(self):
        super().setUp()
        self.root = self.sub("root")
        self.files(self.root, ["a.txt", "b.txt", "real/c.txt"])
        self.out = os.path.join(self.root, "FREEZE.json")

    def test_dot_slash_is_the_same_entry_and_refused_as_a_repeat(self):
        with self.assertRaisesRegex(Refuse, "listed twice"):
            write_freeze(self.root, ["a.txt", "./a.txt"], self.out, "fixture", "test")

    def test_case_twin_is_the_same_entry_on_this_volume(self):
        with self.assertRaisesRegex(Refuse, "listed twice"):
            write_freeze(self.root, ["a.txt", "A.txt"], self.out, "fixture", "test")

    def test_path_is_stored_normalised(self):
        obj = write_freeze(self.root, ["./a.txt", "real//c.txt"], self.out, "fixture", "test")
        self.assertEqual(sorted(obj["files"]), ["a.txt", "real/c.txt"])

    def test_listed_symlink_refused_at_write(self):
        os.symlink(os.path.join(self.root, "a.txt"), os.path.join(self.root, "link.txt"))
        with self.assertRaisesRegex(Refuse, "symbolic link"):
            write_freeze(self.root, ["link.txt"], self.out, "fixture", "test")

    def test_linked_folder_out_of_root_refused(self):
        outside = self.sub("outside")
        self.files(outside, ["x.txt"])
        os.symlink(outside, os.path.join(self.root, "away"))
        with self.assertRaisesRegex(Refuse, "outside the root"):
            write_freeze(self.root, ["away/x.txt"], self.out, "fixture", "test")

    def test_linked_folder_inside_root_is_a_second_spelling(self):
        os.symlink(os.path.join(self.root, "real"), os.path.join(self.root, "alias"))
        with self.assertRaisesRegex(Refuse, "listed twice"):
            write_freeze(self.root, ["real/c.txt", "alias/c.txt"], self.out, "fixture", "test")

    def test_verify_refuses_a_listed_file_replaced_by_a_link(self):
        write_freeze(self.root, ["a.txt", "b.txt"], self.out, "fixture", "test")
        outside = self.sub("outside")
        same = os.path.join(outside, "a.txt")
        shutil.copyfile(os.path.join(self.root, "a.txt"), same)
        os.remove(os.path.join(self.root, "a.txt"))
        os.symlink(same, os.path.join(self.root, "a.txt"))
        self.assertTrue(any("symbolic link" in p for p in verify_freeze(self.out, self.root)),
                        verify_freeze(self.out, self.root))

    def test_verify_refuses_an_entry_not_in_normal_form(self):
        with open(self.out, "w", encoding="utf-8") as fh:
            json.dump({"experiment": "x", "frozen_at": "x", "frozen_by": "x",
                       "files": {"./a.txt": sha256_file(os.path.join(self.root, "a.txt"))}}, fh)
        self.assertTrue(any("normal form" in p for p in verify_freeze(self.out, self.root)),
                        verify_freeze(self.out, self.root))


# ---------- I: inventory mode, the outside anchor, and the stated limits ----------

class FixI(Base):
    def setUp(self):
        super().setUp()
        self.root = self.sub("root")
        self.files(self.root, ["a.txt", "data/d1.txt", "data/deep/d2.txt"])
        self.out = os.path.join(self.root, "FREEZE.json")

    def test_inventory_lists_every_file_and_refuses_an_unlisted_new_one(self):
        obj = write_freeze(self.root, ["a.txt"], self.out, "fixture", "test", inventory=["data"])
        self.assertEqual(sorted(obj["files"]), ["a.txt", "data/d1.txt", "data/deep/d2.txt"])
        self.assertEqual(obj["inventory"], ["data"])
        self.assertEqual(verify_freeze(self.out, self.root), [])
        self.files(self.root, ["data/deep/new.txt"])
        self.assertTrue(any("unlisted" in p and "data/deep/new.txt" in p for p in verify_freeze(self.out, self.root)))

    def test_inventory_catches_a_removed_entry(self):
        write_freeze(self.root, [], self.out, "fixture", "test", inventory=["data"])
        with open(self.out, encoding="utf-8") as fh:
            obj = json.load(fh)
        del obj["files"]["data/d1.txt"]
        os.remove(self.out)
        with open(self.out, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        self.assertTrue(any("unlisted" in p and "data/d1.txt" in p for p in verify_freeze(self.out, self.root)))

    def test_inventory_of_the_whole_root_leaves_the_freeze_file_out(self):
        obj = write_freeze(self.root, [], self.out, "fixture", "test", inventory=["."])
        self.assertNotIn("FREEZE.json", obj["files"])
        self.assertEqual(verify_freeze(self.out, self.root), [])

    def test_inventory_refuses_a_linked_folder_inside_it(self):
        os.symlink(os.path.join(self.root, "data", "deep"), os.path.join(self.root, "data", "loop"))
        with self.assertRaisesRegex(Refuse, "symbolic link"):
            write_freeze(self.root, [], self.out, "fixture", "test", inventory=["data"])

    def test_expect_sha256_refuses_a_manifest_rewritten_with_fresh_hashes(self):
        write_freeze(self.root, ["a.txt"], self.out, "fixture", "test")
        kept = sha256_file(self.out)
        with open(os.path.join(self.root, "a.txt"), "a") as fh:
            fh.write("changed")
        with open(self.out, encoding="utf-8") as fh:
            obj = json.load(fh)
        obj["files"]["a.txt"] = sha256_file(os.path.join(self.root, "a.txt"))
        os.remove(self.out)
        with open(self.out, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, sort_keys=True, indent=1)
        self.assertEqual(verify_freeze(self.out, self.root), [])  # the documented limit
        probs = verify_freeze(self.out, self.root, expect_sha256=kept)
        self.assertTrue(probs and "expected" in probs[0], probs)

    def test_verify_prints_its_limits_first(self):
        write_freeze(self.root, ["a.txt"], self.out, "fixture", "test")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = freeze.main(["verify", "--root", self.root, self.out])
        lines = buf.getvalue().splitlines()
        self.assertEqual(code, 0)
        self.assertTrue(lines[0].startswith("LIMITS:"), lines[:3])
        self.assertIn("does not notice", " ".join(lines[:4]))


# ---------- G: names that differ only by case ----------

class FixG(Base):
    def test_case_twin_sorters_refused_before_anything_is_written(self):
        out = os.path.join(self.dir, "run")
        cfg = dry_config(out, sorters=[{"name": "S1", "group": "cloud", "provider": "p1"},
                                       {"name": "s1", "group": "cloud", "provider": "p2"}])
        with self.assertRaisesRegex(Refuse, "equal after case folding"):
            runner.run(cfg)
        self.assertFalse(os.path.exists(out))

    def test_case_twin_groups_refused(self):
        cfg = dry_config(os.path.join(self.dir, "run"),
                         sorters=[{"name": "S1", "group": "cloud", "provider": "p1"},
                                  {"name": "S2", "group": "Cloud", "provider": "p2"}])
        with self.assertRaisesRegex(Refuse, "equal after case folding"):
            runner.check_config(cfg)

    def test_a_group_used_twice_is_not_a_twin(self):
        runner.check_config(dry_config(os.path.join(self.dir, "run")))

    def test_planned_paths_equal_after_case_folding_refused(self):
        with self.assertRaisesRegex(Refuse, "equal after case folding"):
            runner.check_planned_paths(["results/S1__r1.json", "results/s1__r1.json"])
        runner.check_planned_paths(["results/S1__r1.json", "results/S2__r1.json"])


# ---------- F: files on disk and in the manifest must be exactly the expected ones ----------

class FixF(Base):
    def test_unlisted_file_in_results_refused(self):
        rd = good_run(self.dir)
        self.files(rd, ["results/extra.json"])
        with self.assertRaisesRegex(Refuse, "not listed in the manifest: results/extra.json"):
            tally(tcfg(rd))

    def test_unlisted_file_in_prompts_refused(self):
        rd = good_run(self.dir)
        self.files(rd, ["prompts/S9__r1.json"])
        with self.assertRaisesRegex(Refuse, "not listed in the manifest: prompts/S9__r1.json"):
            tally(tcfg(rd))

    def test_unlisted_folder_in_results_refused(self):
        rd = good_run(self.dir)
        os.makedirs(os.path.join(rd, "results", "more"))
        with self.assertRaisesRegex(Refuse, "not listed in the manifest: results/more"):
            tally(tcfg(rd))

    def test_listed_prompt_not_expected_refused(self):
        rd = good_run(self.dir)
        self.files(rd, ["prompts/S9__r1.json"])
        mp = os.path.join(rd, "manifest.json")
        with open(mp, encoding="utf-8") as fh:
            man = json.load(fh)
        man["files"].append({"dry_run": False, "path": "prompts/S9__r1.json",
                             "sha256": sha256_file(os.path.join(rd, "prompts/S9__r1.json"))})
        write_json(mp, man)
        with self.assertRaisesRegex(Refuse, "does not expect: \\['prompts/S9__r1.json'\\]"):
            tally(tcfg(rd))

    def test_expected_prompt_missing_refused(self):
        rd = good_run(self.dir)
        os.remove(os.path.join(rd, "prompts", "S1__r1.json"))
        mp = os.path.join(rd, "manifest.json")
        with open(mp, encoding="utf-8") as fh:
            man = json.load(fh)
        man["files"] = [r for r in man["files"] if r["path"] != "prompts/S1__r1.json"]
        write_json(mp, man)
        with self.assertRaisesRegex(Refuse, "expected file is missing: prompts/S1__r1.json"):
            tally(tcfg(rd))


# ---------- D: labels and lines pair one to one, each prompt once ----------

class FixD(Base):
    def test_codex_case_two_labels_on_line_1(self):
        rd = good_run(self.dir)

        def both_on_line_1(key):
            for p in key["prompts"]:
                for e in p["labels"]:
                    e["line_number"] = 1
        rewrite_and_rehash(rd, "key.json", both_on_line_1)
        with self.assertRaisesRegex(Refuse, "one to one"):
            tally(tcfg(rd))

    def test_one_prompt_listed_twice_in_the_key(self):
        rd = good_run(self.dir)
        rewrite_and_rehash(rd, "key.json", lambda key: key["prompts"].append(dict(key["prompts"][0])))
        with self.assertRaisesRegex(Refuse, "more than once"):
            tally(tcfg(rd))

    def test_a_prompt_for_no_expected_sorter_in_the_key(self):
        rd = good_run(self.dir)

        def add(key):
            extra = json.loads(json.dumps(key["prompts"][0]))
            extra["sorter"] = "S9"
            key["prompts"].append(extra)
        rewrite_and_rehash(rd, "key.json", add)
        with self.assertRaisesRegex(Refuse, "exactly once"):
            tally(tcfg(rd))

    def test_key_lines_not_numbered_1_to_n(self):
        rd = good_run(self.dir)

        def renumber(key):
            key["lines"][1]["line_number"] = 1
        rewrite_and_rehash(rd, "key.json", renumber)
        with self.assertRaisesRegex(Refuse, "key lines are not numbered exactly 1 to"):
            tally(tcfg(rd))


# ---------- E: the stored parse must equal a fresh parse of raw_reply ----------

class FixE(Base):
    def test_codex_case_raw_reply_changed_rows_kept(self):
        rd = good_run(self.dir)
        rewrite_and_rehash(rd, "results/S2__r1.json", lambda r: r.update(raw_reply="DRYRUN"))
        with self.assertRaisesRegex(Refuse, "fresh parse"):
            tally(tcfg(rd))

    def test_row_home_changed_raw_kept(self):
        rd = good_run(self.dir)

        def flip(r):
            r["rows"][0]["home_main"] = B if r["rows"][0]["home_main"] == A else A
        rewrite_and_rehash(rd, "results/S3__r2.json", flip)
        with self.assertRaisesRegex(Refuse, "fresh parse"):
            tally(tcfg(rd))

    def test_failure_errors_changed(self):
        assign = {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}
        assign[("S4", 2)] = None
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, assign)
        rewrite_and_rehash(rd, "results/S4__r2.json", lambda r: r.update(parse_errors=["FIXTURE other reason"]))
        with self.assertRaisesRegex(Refuse, "fresh parse"):
            tally(tcfg(rd))

    def test_untouched_run_still_tallies(self):
        rd = good_run(self.dir)
        rep, _ = tally(tcfg(rd))
        self.assertEqual([x["modal_count"] for x in rep["groups"]["cloud"]["per_line"]], [6, 6])


# ---------- C: the wording a sorter reads lives in prompt_text.json ----------

PROMPT_TEXT = os.path.join(HERE, "prompt_text.json")
FIXTURE_LINES = ["FIXTURE line %d, not a real lesson." % i for i in range(1, 18)]
# Taken at 19:22:01 EST from the code before fix C (the wording then a constant in prompt_builder.py).
OLD_PROMPT_SHA = {(11, 22): "3ed4fcd5287b8bd9b06be445f94ef004ae9cb7cf9adffe83ea842ea46ac90c83",
                  (5, 6): "286efcefdc95310479e961bf2054f91a9849d95d2fb9c5dc918e8e73008973c9"}
# sha256 of the 24 prompt_sha256 values of scratch/dryrun_v2 (config order, repeats 1..3), joined by "\n";
# read at 19:3x EST from the earlier builder's dry run, made with the wording as a constant.
OLD_DRYRUN_V2_PROMPTS = "06fb0002c0526c6edc05976bc808b9cbc901321aed255e485cf0b4facd6f2322"
STATUS = "DRAFT, written by a builder that had read the sheet; to be replaced or approved before any freeze"


class FixC(Base):
    def setUp(self):
        super().setUp()
        from homes import load_homes
        from prompt_builder import load_deny_list
        self.homes = load_homes(os.path.join(HERE, "fixtures", "homes_fixture.json"))[0]
        self.deny = load_deny_list(os.path.join(HERE, "deny_list.txt"))
        with open(PROMPT_TEXT, encoding="utf-8") as fh:
            self.shipped = json.load(fh)

    def write_text(self, obj):
        p = os.path.join(self.dir, "pt%d.json" % len(os.listdir(self.dir)))
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        return p

    def test_shipped_file_has_the_status_and_the_question_as_its_own_field(self):
        self.assertEqual(self.shipped["status"], STATUS)
        self.assertEqual(self.shipped["question"], "what remains judgment once this lesson has its home?")
        self.assertEqual(self.shipped["turn2_intro"].count("{question}"), 1)  # two-turn build: was "intro"

    def test_loader_refuses_a_missing_or_empty_field(self):
        from prompt_builder import load_prompt_text, TEXT_FIELDS
        for field in TEXT_FIELDS:  # two-turn build: the split field names
            for why, val in (("missing", None), ("empty", ""), ("blank", "  "), ("not text", 3)):
                with self.subTest(field=field, why=why):
                    obj = dict(self.shipped)
                    if val is None:
                        del obj[field]
                    else:
                        obj[field] = val
                    with self.assertRaisesRegex(Refuse, field):
                        load_prompt_text(self.write_text(obj))
        obj = dict(self.shipped, extra="x")
        with self.assertRaisesRegex(Refuse, "unknown"):
            load_prompt_text(self.write_text(obj))

    def test_loader_refuses_an_intro_without_each_placeholder_once(self):
        from prompt_builder import load_prompt_text
        # two-turn build: {line_count} lives in turn1_intro, {question} in turn2_intro
        for field, ph in (("turn2_intro", "{question}"), ("turn1_intro", "{line_count}")):
            with self.subTest(ph=ph):
                with self.assertRaisesRegex(Refuse, "exactly once"):
                    load_prompt_text(self.write_text(dict(self.shipped, **{field: self.shipped[field].replace(ph, "")})))
                with self.assertRaisesRegex(Refuse, "exactly once"):
                    load_prompt_text(self.write_text(dict(self.shipped, **{field: self.shipped[field] + ph})))

    def test_builder_reads_the_wording_from_the_file(self):
        from prompt_builder import load_prompt_text, build_prompt
        obj = dict(self.shipped, question="FIXTURE question, not the real one?",
                   turn1_reply_format=self.shipped["turn1_reply_format"].replace("Reply format.",
                                                                                 "FIXTURE reply format."))
        pt = load_prompt_text(self.write_text(obj))
        p = build_prompt(FIXTURE_LINES, self.homes, 1, 2, self.deny, prompt_text=pt)
        self.assertIn("FIXTURE question, not the real one?", p.question_text)  # two-turn build: second message
        self.assertIn("FIXTURE reply format.", p.text)
        self.assertNotIn("what remains judgment", p.text + p.question_text)
        self.assertEqual(p.prompt_text_sha256, pt["sha256"])

    def test_present_wording_is_unchanged_byte_for_byte(self):
        """Two-turn build: the first message, with the removed pieces put back, is the old prompt byte for byte."""
        from prompt_builder import load_prompt_text, build_prompt
        from test_two_turn_and_callers import old_from_new
        from common import sha256_bytes
        pt = load_prompt_text(PROMPT_TEXT)
        for (ls, hs), want in OLD_PROMPT_SHA.items():
            with self.subTest(seeds=(ls, hs)):
                p = build_prompt(FIXTURE_LINES, self.homes, ls, hs, self.deny, prompt_text=pt)
                self.assertEqual(sha256_bytes(old_from_new(p.text).encode("utf-8")), want)
                self.assertNotIn(STATUS, p.text + p.question_text)
                self.assertNotIn("DRAFT", p.text + p.question_text)

    def test_deny_list_still_covers_everything_but_the_lessons(self):
        from prompt_builder import load_prompt_text, build_prompt, TEXT_FIELDS
        for field in [f for f in TEXT_FIELDS if f != "status"]:  # two-turn build: the split field names
            with self.subTest(field=field):
                obj = dict(self.shipped)
                obj[field] = obj[field].replace("\n", " Temple\n", 1) if "\n" in obj[field] else obj[field] + " Temple"
                pt = load_prompt_text(self.write_text(obj))
                with self.assertRaisesRegex(Refuse, "deny list hit"):
                    build_prompt(FIXTURE_LINES, self.homes, 1, 2, self.deny, prompt_text=pt)
        lines = list(FIXTURE_LINES)
        lines[0] = "FIXTURE lesson naming the Temple and a sheet."
        build_prompt(lines, self.homes, 1, 2, self.deny, prompt_text=load_prompt_text(PROMPT_TEXT))

    def test_runner_records_the_file_hash_in_the_key_and_the_dry_run_prompts_are_unchanged(self):
        with open(os.path.join(HERE, "config_dryrun.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        # A reviewed copy must exercise its own input files, not the original
        # installation paths preserved in the example configuration.
        cfg["homes_file"] = os.path.join(HERE, "fixtures", "homes_fixture.json")
        cfg["deny_list"] = os.path.join(HERE, "deny_list.txt")
        cfg["prompt_text"] = PROMPT_TEXT
        cfg["out_dir"] = os.path.join(self.dir, "run")
        out = runner.run(cfg)
        with open(os.path.join(out, "key.json"), encoding="utf-8") as fh:
            key = json.load(fh)
        self.assertEqual(key["prompt_text_sha256"], sha256_file(PROMPT_TEXT))
        self.assertEqual(key["prompt_text_file"], os.path.abspath(PROMPT_TEXT))
        hs = []
        for s in cfg["sorters"]:
            for k in range(1, cfg["repeats"] + 1):
                with open(os.path.join(out, "prompts", "%s__r%d.json" % (s["name"], k)), encoding="utf-8") as fh:
                    # two-turn build: the old prompt is the first message with the removed pieces put back
                    from test_two_turn_and_callers import old_from_new
                    from common import sha256_bytes
                    hs.append(sha256_bytes(old_from_new(json.load(fh)["text"]).encode("utf-8")))
        import hashlib
        self.assertEqual(hashlib.sha256("\n".join(hs).encode()).hexdigest(), OLD_DRYRUN_V2_PROMPTS)


# ---------- B: "6 from 3": providers per sorter, min_providers per group ----------

def provided(sorters, providers):
    return [{"name": n, "group": g, "provider": p} for (n, g), p in zip(sorters, providers)]


class FixB(Base):
    def cfg(self, providers, groups, sorters=(("S1", "cloud"), ("S2", "cloud"), ("S3", "cloud"))):
        return dry_config(os.path.join(self.dir, "run"), sorters=provided(sorters, providers), groups=groups)

    def test_runner_refuses_a_cloud_group_with_too_few_providers(self):
        with self.assertRaisesRegex(Refuse, "spans 2 provider"):
            runner.check_config(self.cfg(["p-one", "p-one", "p-two"], {"cloud": {"min_providers": 3}}))

    def test_runner_counts_providers_without_case(self):
        with self.assertRaisesRegex(Refuse, "spans 2 provider"):
            runner.check_config(self.cfg(["OpenX", "openx", "p-two"], {"cloud": {"min_providers": 3}}))

    def test_runner_refuses_a_groups_entry_no_sorter_has(self):
        with self.assertRaisesRegex(Refuse, "no sorter has"):
            runner.check_config(self.cfg(["p1", "p2", "p3"], {"clouds": {"min_providers": 3}}))

    def test_runner_requires_a_provider_and_the_groups_setting(self):
        cfg = self.cfg(["p1", "p2", "p3"], {})
        del cfg["sorters"][0]["provider"]
        with self.assertRaisesRegex(Refuse, "provider"):
            runner.check_config(cfg)
        cfg = self.cfg(["p1", "p2", "p3"], {})
        del cfg["groups"]
        with self.assertRaisesRegex(Refuse, "missing \\['groups'\\]"):
            runner.check_config(cfg)

    def test_runner_accepts_three_providers_and_records_them(self):
        out = runner.run(self.cfg(["p1", "p2", "p3"], {"cloud": {"min_providers": 3}}))
        with open(os.path.join(out, "key.json"), encoding="utf-8") as fh:
            key = json.load(fh)
        self.assertEqual([(s["name"], s["provider"]) for s in key["sorters"]], [("S1", "p1"), ("S2", "p2"), ("S3", "p3")])
        self.assertEqual(key["groups"], {"cloud": {"min_providers": 3}})
        with open(os.path.join(out, "results", "S2__r1.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["provider"], "p2")

    def test_tally_refuses_a_group_with_too_few_providers(self):
        provs = ["p1", "p1", "p2", "p2", "p2", "p2"]
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)},
                      providers=dict(zip([s for s, _ in CLOUD], provs)))
        cfg = tcfg(rd, groups={"cloud": {"min_providers": 3}})
        cfg["sorters"] = provided(CLOUD, provs)
        with self.assertRaisesRegex(Refuse, "spans 2 provider"):
            tally(cfg)
        cfg["groups"] = {"cloud": {"min_providers": 2}}
        tally(cfg)

    def test_tally_refuses_providers_that_differ_from_the_key(self):
        provs = ["p1", "p1", "p2", "p2", "p3", "p3"]
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)},
                      providers=dict(zip([s for s, _ in CLOUD], provs)))
        cfg = tcfg(rd, groups={})
        cfg["sorters"] = provided(CLOUD, ["p1", "p1", "p2", "p2", "p3", "p9"])
        with self.assertRaisesRegex(Refuse, "do not match the run's key"):
            tally(cfg)


# ---------- A: only listed real callers are data; the fixture switch marks everything ----------

MARK = "FIXTURE, NOT DATA"


class FixA(Base):
    def test_fixture_run_refused_without_the_switch(self):
        rd = good_run(self.dir)
        with self.assertRaisesRegex(Refuse, "not on the tally config's real_callers"):
            compute(tcfg(rd))

    def test_real_callers_may_not_list_fixture_or_dryrun(self):
        rd = good_run(self.dir)
        for bad in (["fixture"], ["DryRun"], ["x", "x"], [""], "fixture"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(Refuse, "real_callers must be a list of distinct"):
                    compute(tcfg(rd, real_callers=bad))

    def test_listed_real_caller_is_data_and_unmarked(self):
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)},
                      caller="lab-model")
        rep, judg = compute(tcfg(rd, real_callers=["lab-model"]))
        self.assertNotIn(MARK, json.dumps(rep))
        self.assertNotIn(MARK, judg)
        with self.assertRaisesRegex(Refuse, "not on the tally config's real_callers"):
            compute(tcfg(rd, real_callers=["other-model"]))

    def test_missing_caller_refused_even_with_the_switch(self):
        rd = good_run(self.dir)
        rewrite_and_rehash(rd, "results/S5__r3.json", lambda r: r.pop("caller"))
        with self.assertRaisesRegex(Refuse, "no caller recorded"):
            compute(tcfg(rd), allow_fixture=True)

    def test_switch_marks_every_output_file_and_the_first_printed_line(self):
        import tally as tally_mod
        rd = good_run(self.dir)
        cfg = tcfg(rd, out_dir=os.path.join(self.dir, "out"))
        cp = os.path.join(self.dir, "cfg.json")
        with open(cp, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = tally_mod.main(["--config", cp, "--allow-fixture"])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertTrue(buf.getvalue().splitlines()[0].startswith(MARK), buf.getvalue()[:200])
        out = sorted(os.listdir(cfg["out_dir"]))
        self.assertEqual(out, ["judgment_sentences.txt", "tally.json"])
        with open(os.path.join(cfg["out_dir"], "tally.json"), encoding="utf-8") as fh:
            rep = json.load(fh)
        self.assertEqual(list(rep.items())[0], ("status", MARK))
        with open(os.path.join(cfg["out_dir"], "judgment_sentences.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.readline(), MARK + "\n")
        buf = io.StringIO()
        cfg["out_dir"] = os.path.join(self.dir, "out2")
        with open(cp, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh)
        with contextlib.redirect_stdout(buf):
            code = tally_mod.main(["--config", cp])
        self.assertEqual((code, buf.getvalue().splitlines()[0][:9]), (2, "REFUSED: "))
        self.assertFalse(os.path.exists(cfg["out_dir"]))


if __name__ == "__main__":
    unittest.main()
