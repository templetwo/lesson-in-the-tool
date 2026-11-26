"""Tests for the runner, the tally and the freeze helper. All files go under scratch/.

Version 2 (2026-11-25, after PICKS_20261125.md): sorters carry a group; main home decides; second homes reported
beside; the house table comparison gives exact and overlap counts.

Two-turn build (2026-11-25): a sort whose reply failed to parse now reads "(sort reply failed to parse; question not
asked)" in the judgment file, because the question is asked only after a parsed sort.
"""
import fakes_first  # noqa: F401  (must stay the first import)

import json
import os
import shutil
import unittest

from common import Refuse, HERE, make_scratch_dir, sha256_file
from runner import run
from tally import compute as _compute, fleiss_kappa, krippendorff_alpha_nominal, FIXTURE_MARK


def compute(cfg, **kw):
    """Fix A: every run tallied here is a fixture run, so the switch is passed; the outputs carry FIXTURE_MARK."""
    return _compute(cfg, allow_fixture=True, **kw)
from fixture_runs import make_run, FIXTURE_SENTENCE, fixture_provider
from freeze import write_freeze, verify_freeze

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
A, B, C, D = "FIXTURE-A", "FIXTURE-B", "FIXTURE-C", "FIXTURE-D"
CLOUD = [("S%d" % i, "cloud") for i in range(1, 7)]
LOCAL = [("L1", "local"), ("L2", "local")]
CP6 = {"6": {"settled_min": 5, "leaning_min": 4}}


def dry_config(out_dir, **over):
    cfg = {
        "dry_run": True, "caller": "dryrun", "repo": REPO, "commit": "441752c",
        "lines_path": "sheet/SHEET_SHORT_v2.md",
        "homes_file": os.path.join(HERE, "fixtures", "homes_fixture.json"),
        "deny_list": os.path.join(HERE, "deny_list.txt"),
        "prompt_text": os.path.join(HERE, "prompt_text.json"),
        "sorters": [{"name": "S1", "group": "cloud", "provider": "p1"}, {"name": "S2", "group": "cloud", "provider": "p2"},
                    {"name": "L1", "group": "local", "provider": "p3"}],
        "groups": {}, "repeats": 2, "master_seed": 20261125, "out_dir": out_dir,
    }
    cfg.update(over)
    return cfg


def tally_config(run_dir, sorters, repeats=3, **over):
    cfg = {"run_dir": run_dir,
           "sorters": [{"name": n, "group": g, "provider": fixture_provider(n)} for n, g in sorters],
           "groups": {}, "repeats": repeats,
           "cut_points_by_size": CP6, "bootstrap": {"seed": 7, "draws": 200, "level": 0.95}}
    cfg.update(over)
    return cfg


def walk_rows(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_rows(v, path + "/" + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, dict):
                yield path + "[%d]" % i, v
            yield from walk_rows(v, path + "[%d]" % i)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.dir = make_scratch_dir("t_runner_")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_dry_run_end_to_end(self):
        out = os.path.join(self.dir, "run")
        run(dry_config(out))
        names = sorted(os.listdir(os.path.join(out, "results")))
        self.assertEqual(names, ["L1__r1.json", "L1__r2.json", "S1__r1.json", "S1__r2.json",
                                 "S2__r1.json", "S2__r2.json"])
        files = []
        for root, _, fs in os.walk(out):
            files += [os.path.join(root, f) for f in fs]
        self.assertEqual(len(files), 6 + 6 + 2)
        for f in files:
            with open(f, encoding="utf-8") as fh:
                obj = json.load(fh)
            self.assertEqual(list(obj.keys())[0], "dry_run", f)
            self.assertIs(obj["dry_run"], True, f)
            for where, row in walk_rows(obj):
                self.assertIs(row.get("dry_run"), True, "%s %s" % (f, where))
        with open(os.path.join(out, "results", "L1__r2.json"), encoding="utf-8") as fh:
            res = json.load(fh)
        self.assertTrue(res["parse_ok"])
        self.assertEqual(res["group"], "local")
        self.assertEqual(len(res["rows"]), 17)
        self.assertEqual((res["rows"][0]["home_main"], res["rows"][0]["home_second"]), ("DRYRUN", None))
        with open(os.path.join(out, "manifest.json"), encoding="utf-8") as fh:
            man = json.load(fh)
        for row in man["files"]:
            self.assertEqual(sha256_file(os.path.join(out, row["path"])), row["sha256"])
        with open(os.path.join(out, "prompts", "S1__r1.json"), encoding="utf-8") as fh:
            ptext = json.load(fh)["text"]
        self.assertNotIn("441752c", ptext)
        self.assertNotIn("SHEET_SHORT", ptext)
        self.assertNotIn("local", ptext)

    def test_example_config_has_the_picks_defaults(self):
        with open(os.path.join(HERE, "config_dryrun.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        self.assertEqual(cfg["repeats"], 3)
        self.assertEqual(cfg["lines_path"], "sheet/SHEET_SHORT_v2.md")
        groups = [s["group"] for s in cfg["sorters"]]
        self.assertEqual((groups.count("cloud"), groups.count("local")), (6, 2))
        with open(cfg["homes_file"], encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)), 6)

    def test_refusals(self):
        bad = {
            "dry caller, run not marked dry": {"dry_run": False},
            "unknown caller": {"caller": "gpt"},
            "out dir outside the folder": {"out_dir": "/tmp/public-sort-should-not-exist"},
            "duplicate sorter": {"sorters": [{"name": "S1", "group": "cloud", "provider": "p1"},
                                             {"name": "S1", "group": "local", "provider": "p2"}]},
            "sorter without group": {"sorters": [{"name": "S1", "provider": "p1"}]},
            "plain string sorter": {"sorters": ["S1"]},
            "zero repeats": {"repeats": 0},
            "bad sorter name": {"sorters": [{"name": "S/1", "group": "cloud", "provider": "p1"}]},
        }
        for i, (why, over) in enumerate(bad.items()):
            with self.subTest(why=why):
                cfg = dry_config(os.path.join(self.dir, "x%d" % i))
                cfg.update(over)
                with self.assertRaises(Refuse):
                    run(cfg)
        self.assertFalse(os.path.exists("/tmp/public-sort-should-not-exist"))

    def test_non_empty_out_dir_refused(self):
        out = os.path.join(self.dir, "full")
        os.makedirs(out)
        with open(os.path.join(out, "x"), "w") as fh:
            fh.write("x")
        with self.assertRaises(Refuse):
            run(dry_config(out))

    def test_tally_refuses_dry_run(self):
        out = os.path.join(self.dir, "run")
        run(dry_config(out, sorters=[{"name": "S1", "group": "cloud", "provider": "p1"},
                                     {"name": "S2", "group": "cloud", "provider": "p2"}]))
        with self.assertRaises(Refuse) as cm:
            compute(tally_config(out, [("S1", "cloud"), ("S2", "cloud")], 2))
        self.assertIn("top-level dry_run is not false", str(cm.exception))


class StatTests(unittest.TestCase):
    def test_tiny_table_by_hand(self):
        units = [[A, A, A], [A, A, B], [B, B, B], [A, B, B]]
        self.assertAlmostEqual(fleiss_kappa(units), 1 / 3, places=12)
        self.assertAlmostEqual(krippendorff_alpha_nominal(units), 7 / 18, places=12)

    def test_undefined(self):
        self.assertIsNone(fleiss_kappa([[A, A], [A, A]]))
        self.assertIsNone(krippendorff_alpha_nominal([[A, A], [A, A]]))
        self.assertIsNone(fleiss_kappa([[A, None], [A, A]]))


def split_assign(sorters):
    """The known split on 3 lines for 6 cloud sorters: line1 6 A; line2 4 A 2 B; line3 3 A 3 B."""
    per = {s: [A, A if i < 4 else B, A if i < 3 else B] for i, (s, _) in enumerate(sorters)}
    return {(s, r): per[s] for s, _ in sorters for r in (1, 2, 3)}


def expected_judgment(line_count, sorters, repeats, failed=()):
    out = [FIXTURE_MARK, "Judgment sentences, copied exactly as the sorters wrote them.",
           "Question asked: what remains judgment once this lesson has its home?",
           "These are not scored, counted or classified anywhere in the code. A person reads them.", ""]
    for n in range(1, line_count + 1):
        out.append("Line %d: FIXTURE line %d, not a real lesson." % (n, n))
        for s, g in sorters:
            for k in range(1, repeats + 1):
                sent = ("(sort reply failed to parse; question not asked)" if (s, k) in failed
                        else FIXTURE_SENTENCE % (n, s, k))
                out.append("  [%s] %s repeat %d: %s" % (g, s, k, sent))
        out.append("")
    return "\n".join(out) + "\n"


class TallyTests(unittest.TestCase):
    def setUp(self):
        self.dir = make_scratch_dir("t_tally_")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def sub(self, name):
        d = os.path.join(self.dir, name)
        os.makedirs(d)
        return d

    def test_known_split_and_exact_judgment_copy(self):
        rd = make_run(self.dir, CLOUD, 3, [A, B], 3, split_assign(CLOUD))
        rep, judg = compute(tally_config(rd, CLOUD))
        g = rep["groups"]["cloud"]
        got = [(x["modal_homes"], x["modal_count"], x["count_text"], x["class"]) for x in g["per_line"]]
        self.assertEqual(got, [([A], 6, "6 of 6", "settled"), ([A], 4, "4 of 6", "leaning"),
                               ([A, B], 3, "3 of 6", "contested")])
        self.assertAlmostEqual(g["agreement"]["fleiss_kappa"]["value"], 19 / 325, places=12)
        self.assertAlmostEqual(g["agreement"]["krippendorff_alpha"]["value"], 72 / 650, places=12)
        for s, _ in CLOUD:
            self.assertEqual(g["per_sorter"][s]["share_lines_not_all_same"], 0.0)
            self.assertEqual(g["per_sorter"][s]["share_lines_no_majority"], 0.0)
        self.assertEqual(judg, expected_judgment(3, CLOUD, 3))

    def test_second_homes_reported_and_do_not_move_main_figures(self):
        base = {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}
        withsec = dict(base)
        withsec[("S1", 1)] = withsec[("S1", 2)] = withsec[("S1", 3)] = [(A, B), B]
        withsec[("S1", 1)] = [(A, B), (B, A)]
        withsec[("S2", 1)], withsec[("S2", 2)] = [(A, B), B], [(A, C), B]
        withsec[("S3", 1)] = withsec[("S3", 2)] = [(A, C), B]
        r0, _ = compute(tally_config(make_run(self.sub("a"), CLOUD, 3, [A, B, C], 2, base), CLOUD))
        r1, _ = compute(tally_config(make_run(self.sub("b"), CLOUD, 3, [A, B, C], 2, withsec), CLOUD))
        g0, g1 = r0["groups"]["cloud"], r1["groups"]["cloud"]
        for key in ("per_line", "per_sorter", "agreement", "class_counts"):
            self.assertEqual(g0[key], g1[key], key)
        sec = {x["line_number"]: x for x in g1["second_homes"]}
        self.assertEqual(sec[1]["by_majority"], {"sorters_with_second": 2, "of": 6, "homes": {B: 1, C: 1}})
        self.assertEqual(sec[1]["raw"], {"replies_with_second": 7, "of_replies": 18, "homes": {B: 4, C: 3}})
        self.assertEqual(sec[2]["by_majority"], {"sorters_with_second": 0, "of": 6, "homes": {}})
        self.assertEqual(sec[2]["raw"], {"replies_with_second": 1, "of_replies": 18, "homes": {A: 1}})

    def test_two_groups_kept_apart(self):
        both = CLOUD + LOCAL
        assign = split_assign(CLOUD)
        loc = {"L1": [A, A, B], "L2": [B, A, B]}
        for s, _ in LOCAL:
            for r in (1, 2, 3):
                assign[(s, r)] = loc[s]
        rep, judg = compute(tally_config(make_run(self.dir, both, 3, [A, B], 3, assign), both))
        self.assertEqual(sorted(rep["groups"]), ["cloud", "local"])
        cl, lo = rep["groups"]["cloud"], rep["groups"]["local"]
        self.assertEqual([x["modal_count"] for x in cl["per_line"]], [6, 4, 3])  # pooling would make line 2 = 6
        self.assertAlmostEqual(cl["agreement"]["fleiss_kappa"]["value"], 19 / 325, places=12)
        got = [(x["modal_homes"], x["count_text"], x["class"]) for x in lo["per_line"]]
        self.assertEqual(got, [([A, B], "1 of 2", None), ([A], "2 of 2", None), ([B], "2 of 2", None)])
        self.assertIsNone(lo["class_counts"])
        self.assertEqual(lo["agreement"], {})
        self.assertEqual(lo["agreement_note"],
                         "Agreement statistics are not computed for a group of two, by rule.")
        self.assertNotIn("L1", json.dumps(cl))
        self.assertNotIn("S1", json.dumps(lo))
        self.assertEqual((cl["parse_failures"], lo["parse_failures"]),
                         ({"count": 0, "of_replies": 18}, {"count": 0, "of_replies": 6}))
        self.assertEqual(judg, expected_judgment(3, both, 3))
        cfg = tally_config(make_run(self.sub("c"), both, 3, [A, B], 3, assign), both,
                           cut_points_by_size={"6": CP6["6"], "2": {"settled_min": 2, "leaning_min": 2}})
        lo2 = compute(cfg)[0]["groups"]["local"]
        self.assertEqual([x["class"] for x in lo2["per_line"]], ["contested", "settled", "settled"])

    def test_no_majority_and_parse_failure(self):
        assign = {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}
        assign[("S1", 1)], assign[("S1", 2)], assign[("S1", 3)] = [A, A], [B, A], [C, B]
        assign[("S2", 2)] = None
        rd = make_run(self.dir, CLOUD, 3, [A, B, C], 2, assign)
        rep, judg = compute(tally_config(rd, CLOUD))
        g = rep["groups"]["cloud"]
        s1, s2, s3 = g["per_sorter"]["S1"], g["per_sorter"]["S2"], g["per_sorter"]["S3"]
        self.assertEqual((s1["share_lines_not_all_same"], s1["share_lines_no_majority"]), (1.0, 0.5))
        self.assertEqual((s2["share_lines_not_all_same"], s2["share_lines_no_majority"], s2["repeats_failed"]),
                         (1.0, 0.0, 1))
        self.assertEqual((s3["share_lines_not_all_same"], s3["share_lines_no_majority"]), (0.0, 0.0))
        self.assertNotIn("parse_failures", rep)  # no pooled count
        self.assertEqual(g["parse_failures"], {"count": 1, "of_replies": 18})
        self.assertEqual(rep["parse_failures_listed"][0]["group"], "cloud")
        self.assertIsNone(g["agreement"]["fleiss_kappa"]["value"])
        self.assertAlmostEqual(g["agreement"]["krippendorff_alpha"]["value"], 2 / 3, places=12)
        self.assertEqual(judg, expected_judgment(2, CLOUD, 3, failed={("S2", 2)}))

    def test_perfect_agreement(self):
        assign = {(s, r): [A, B, C, D] for s, _ in CLOUD for r in (1, 2, 3)}
        rep, _ = compute(tally_config(make_run(self.dir, CLOUD, 3, [A, B, C, D], 4, assign), CLOUD))
        g = rep["groups"]["cloud"]
        self.assertTrue(all(x["class"] == "settled" and x["modal_count"] == 6 for x in g["per_line"]))
        self.assertAlmostEqual(g["agreement"]["fleiss_kappa"]["value"], 1.0, places=12)
        self.assertAlmostEqual(g["agreement"]["krippendorff_alpha"]["value"], 1.0, places=12)

    def _good_run(self, sorters=CLOUD):
        return make_run(self.dir, sorters, 3, [A, B], 2, {(s, r): [A, B] for s, _ in sorters for r in (1, 2, 3)})

    def test_missing_file_refused(self):
        rd = self._good_run()
        os.remove(os.path.join(rd, "results", "S4__r2.json"))
        with self.assertRaises(Refuse):
            compute(tally_config(rd, CLOUD))

    def test_expected_sorter_absent_refused(self):
        rd = self._good_run()
        with self.assertRaises(Refuse):
            compute(tally_config(rd, CLOUD + [("S7", "cloud")]))

    def test_unexpected_result_refused(self):
        rd = self._good_run()
        with self.assertRaises(Refuse):
            compute(tally_config(rd, CLOUD[:5]))

    def test_group_mismatch_refused(self):
        rd = self._good_run()
        cfg = tally_config(rd, CLOUD[:4] + [("S5", "local"), ("S6", "local")])
        with self.assertRaises(Refuse):
            compute(cfg)

    def test_singleton_group_must_still_match_run_key(self):
        rd = self._good_run()
        with self.assertRaisesRegex(Refuse, "do not match the run's key"):
            compute(tally_config(rd, CLOUD[:5] + [("S6", "local")]))

    def test_hash_mismatch_refused(self):
        rd = self._good_run()
        p = os.path.join(rd, "results", "S3__r1.json")
        with open(p, encoding="utf-8") as fh:
            obj = json.load(fh)
        obj["rows"][0]["sentence"] = "FIXTURE sentence, edited after the run"
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        with self.assertRaises(Refuse):
            compute(tally_config(rd, CLOUD))

    def test_dry_row_refused(self):
        rd = make_run(self.dir, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)},
                      dry_row_in=("S5", 3))
        with self.assertRaises(Refuse):
            compute(tally_config(rd, CLOUD))

    def test_dryrun_in_home_field_refused_and_sentence_ignored(self):
        from tally import check_not_dry
        with self.assertRaises(Refuse) as cm:
            check_not_dry({"dry_run": False, "rows": [{"dry_run": False, "home_main": "DRYRUN", "sentence": "x"}]}, "f")
        self.assertIn("reserved home DRYRUN", str(cm.exception))
        check_not_dry({"dry_run": False, "rows": [{"dry_run": False, "home_main": A, "sentence": "DRYRUN"}]}, "f")

    def test_bad_cut_points_refused(self):
        rd = self._good_run()
        for cp in ({"6": {"settled_min": 4, "leaning_min": 5}}, {"6": {"settled_min": 7, "leaning_min": 4}},
                   {"six": {"settled_min": 5, "leaning_min": 4}}, {"6": {"settled_min": 5}}):
            with self.subTest(cp=cp):
                with self.assertRaises(Refuse):
                    compute(tally_config(rd, CLOUD, cut_points_by_size=cp))
        cfg = tally_config(rd, CLOUD)
        del cfg["cut_points_by_size"]
        with self.assertRaises(Refuse):
            compute(cfg)

    def test_house_table_exact_and_overlap(self):
        assign = {(s, r): [A, B, C] for s, _ in CLOUD for r in (1, 2, 3)}
        for r in (1, 2, 3):
            assign[("S1", r)] = [(A, B), B, C]
            assign[("S3", r)] = [(A, C), B, C]
        assign[("S2", 1)] = [(A, B), B, C]
        rd = make_run(self.dir, CLOUD, 3, [A, B, C], 3, assign)
        table = os.path.join(self.dir, "table.json")
        with open(table, "w", encoding="utf-8") as fh:
            json.dump({"rows": [{"line_number": 1, "home_main": A, "home_second": B},
                                {"line_number": 2, "home_main": B, "home_second": None},
                                {"line_number": 3, "home_main": "(this table)", "home_second": None}]}, fh)
        rep, _ = compute(tally_config(rd, CLOUD, house_table=table))
        h = rep["groups"]["cloud"]["house_table"]
        self.assertEqual(h["excluded_lines"], [{"line_number": 3, "home_main": "(this table)", "home_second": None,
                                                "reason": "a home not on the list"}])
        self.assertEqual(h["per_sorter"]["S1"], {"exact": 2, "overlap": 2, "of": 2})
        self.assertEqual(h["per_sorter"]["S2"], {"exact": 1, "overlap": 2, "of": 2})
        self.assertEqual(h["per_sorter"]["S3"], {"exact": 1, "overlap": 2, "of": 2})
        self.assertEqual(h["group"], {"exact": 7, "overlap": 12, "of": 12})


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.dir = make_scratch_dir("t_freeze_")
        for n in ("a.txt", "b.txt"):
            with open(os.path.join(self.dir, n), "w") as fh:
                fh.write("FIXTURE " + n)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_write_and_verify(self):
        out = os.path.join(self.dir, "FREEZE.json")
        write_freeze(self.dir, ["a.txt", "b.txt"], out, "fixture experiment", "test")
        with open(out, encoding="utf-8") as fh:
            obj = json.load(fh)
        self.assertEqual(sorted(obj["files"]), ["a.txt", "b.txt"])
        self.assertRegex(obj["frozen_at"], r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d [A-Z]+$")
        self.assertEqual(verify_freeze(out, self.dir), [])
        with open(os.path.join(self.dir, "a.txt"), "a") as fh:
            fh.write("!")
        self.assertTrue(verify_freeze(out, self.dir))
        os.remove(os.path.join(self.dir, "b.txt"))
        self.assertEqual(len(verify_freeze(out, self.dir)), 2)

    def test_refusals(self):
        out = os.path.join(self.dir, "FREEZE.json")
        with self.assertRaises(Refuse):
            write_freeze(self.dir, ["missing.txt"], out, "e", "t")
        with self.assertRaises(Refuse):
            write_freeze(self.dir, ["../x"], out, "e", "t")
        write_freeze(self.dir, ["a.txt"], out, "e", "t")
        with self.assertRaises(Refuse):
            write_freeze(self.dir, ["a.txt"], out, "e", "t")


if __name__ == "__main__":
    unittest.main()
