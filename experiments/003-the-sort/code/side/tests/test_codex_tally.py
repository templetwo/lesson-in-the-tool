"""Offline regressions for the per-sorter caller binding. Fixtures stay marked.

No adapter, enabled-switch dictionary, published adapter test, or live job is
imported. All test files are temporary children of the separate Stale Door lane.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from common import Refuse, load_json, sha256_file, write_json
from fixture_runs import make_run
from tally import compute

SCRATCH = HERE.parent / "test2_stale/scratch/codex_fix_tally"
SORTERS = [("S%d" % n, "cloud") for n in range(1, 7)] + [("L1", "local"), ("L2", "local")]
PROVIDERS = dict(zip([s for s, _ in SORTERS], ["p1", "p1", "p2", "p2", "p3", "p3", "lp1", "lp2"]))
CALLERS = {s: "fixture-adapter-" + PROVIDERS[s] for s, _ in SORTERS}
ASSIGN = {(s, r): ["FIXTURE-A", "FIXTURE-B"] for s, _ in SORTERS for r in (1, 2, 3)}


def rewrite(run_dir, rel, mutate):
    path = Path(run_dir) / rel
    obj = load_json(str(path), rel)
    mutate(obj)
    write_json(str(path), obj)
    manifest_path = Path(run_dir) / "manifest.json"
    manifest = load_json(str(manifest_path), "manifest")
    for row in manifest["files"]:
        if row["path"] == rel:
            row["sha256"] = sha256_file(str(path))
    write_json(str(manifest_path), manifest)


class CodexTallyCallerBinding(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="fixture-", dir=str(SCRATCH))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.number = 0

    def run_dir(self, by_sorter=True, assign=None):
        self.number += 1
        opts = {"caller": "by_sorter", "result_callers": CALLERS} if by_sorter else {}
        rd = make_run(str(self.root / ("run-%d" % self.number)), SORTERS, 3,
                      ["FIXTURE-A", "FIXTURE-B"], 2, assign or ASSIGN,
                      providers=PROVIDERS, **opts)
        if by_sorter:
            # The runner records this map. Older fixture helpers did not; keep
            # this test's source binding explicit regardless of helper version.
            rewrite(rd, "key.json", lambda key: key.update(real_callers=dict(CALLERS)))
        return rd

    def tally(self, rd):
        cfg = {"run_dir": rd,
               "sorters": [{"name": s, "group": g, "provider": PROVIDERS[s]} for s, g in SORTERS],
               "groups": {"cloud": {"min_providers": 3}}, "repeats": 3,
               "cut_points_by_size": {"6": {"settled_min": 5, "leaning_min": 4}},
               "bootstrap": {"seed": 1125, "draws": 30, "level": 0.95},
               "real_callers": sorted(set(CALLERS.values()))}
        return compute(cfg, allow_fixture=True)

    def test_original_cross_provider_swap_is_refused_despite_same_global_set(self):
        rd = self.run_dir()
        rewrite(rd, "results/S1__r1.json", lambda row: row.update(caller=CALLERS["S3"]))
        rewrite(rd, "results/S3__r1.json", lambda row: row.update(caller=CALLERS["S1"]))
        with self.assertRaisesRegex(Refuse, "caller.*key.*real_callers"):
            self.tally(rd)

    def test_saved_map_cannot_be_bypassed_by_changing_manifest_mode(self):
        rd = self.run_dir()
        rewrite(rd, "results/S1__r1.json", lambda row: row.update(caller=CALLERS["S3"]))
        rewrite(rd, "results/S3__r1.json", lambda row: row.update(caller=CALLERS["S1"]))
        # Preserve the saved map and global caller set, changing only the mode
        # to an otherwise allowed name. That must not disable map validation.
        rewrite(rd, "manifest.json", lambda manifest: manifest.update(caller=CALLERS["S1"]))
        with self.assertRaisesRegex(Refuse, "key.real_callers.*by_sorter"):
            self.tally(rd)

    def test_missing_saved_map_is_refused_for_by_sorter(self):
        rd = self.run_dir()
        rewrite(rd, "key.json", lambda key: key.pop("real_callers"))
        with self.assertRaisesRegex(Refuse, "key.*real_callers"):
            self.tally(rd)

    def test_saved_map_must_be_an_object_with_text_values(self):
        values = [None, list(CALLERS), "FIXTURE not a map", True]
        values += [dict(CALLERS, S1=value) for value in (None, True, 1, "", "   ", ["fixture-a"], {"caller": "fixture-a"})]
        for value in values:
            with self.subTest(value=value):
                rd = self.run_dir()
                rewrite(rd, "key.json", lambda key: key.update(real_callers=value))
                with self.assertRaisesRegex(Refuse, "key.*real_callers"):
                    self.tally(rd)

    def test_saved_map_must_cover_each_sorter_and_no_others(self):
        missing = dict(CALLERS)
        missing.pop("S1")
        for value in (missing, dict(CALLERS, S9="fixture-adapter-p9"),
                      dict(missing, s1=CALLERS["S1"])):
            with self.subTest(value=value):
                rd = self.run_dir()
                rewrite(rd, "key.json", lambda key: key.update(real_callers=value))
                with self.assertRaisesRegex(Refuse, "key.*real_callers.*every sorter"):
                    self.tally(rd)

    def test_every_repeat_is_bound_even_when_the_sort_failed(self):
        assign = dict(ASSIGN)
        assign[("S1", 3)] = None
        rd = self.run_dir(assign=assign)
        rewrite(rd, "results/S1__r3.json", lambda row: row.update(caller=CALLERS["S3"]))
        with self.assertRaisesRegex(Refuse, "caller.*key.*real_callers"):
            self.tally(rd)

    def test_present_incomplete_persistence_state_is_refused(self):
        for state in ("turn1_returned", "turn2_pending", "turn2_returned", "unknown", None, True):
            with self.subTest(state=state):
                rd = self.run_dir()
                rewrite(rd, "results/S1__r1.json", lambda row: row.update(persistence_state=state))
                with self.assertRaisesRegex(Refuse, "persistence_state.*complete"):
                    self.tally(rd)

    def test_complete_persistence_state_and_legacy_absence_both_accepted(self):
        legacy, _ = self.tally(self.run_dir())
        rd = self.run_dir()
        for sorter, _ in SORTERS:
            for repeat in (1, 2, 3):
                rewrite(rd, "results/%s__r%d.json" % (sorter, repeat),
                        lambda row: row.update(persistence_state="complete"))
        complete, _ = self.tally(rd)
        self.assertEqual(complete["groups"], legacy["groups"])

    def test_unchanged_mapping_accepts_shared_adapters_and_keeps_fixture_mark(self):
        report, judgment = self.tally(self.run_dir())
        self.assertEqual(report["status"], "FIXTURE, NOT DATA")
        self.assertTrue(judgment.startswith("FIXTURE, NOT DATA\n"))
        self.assertEqual([row["modal_count"] for row in report["groups"]["cloud"]["per_line"]], [6, 6])
        self.assertEqual(report["settings"]["groups"], {"cloud": {"min_providers": 3}})

    def test_legacy_single_caller_without_saved_map_still_tallies(self):
        mapped, _ = self.tally(self.run_dir())
        legacy, _ = self.tally(self.run_dir(by_sorter=False))
        self.assertEqual(mapped["groups"], legacy["groups"])
        self.assertEqual(legacy["status"], "FIXTURE, NOT DATA")
        self.assertEqual(legacy["inputs"]["callers"], ["fixture"])


if __name__ == "__main__":
    unittest.main()
