"""Negative controls for the archive verifier; changes stay in temporary copies."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from verify_archive import verify_freezes, verify_manifest
from archive_evidence import verify_evidence

PILOT = "experiments/001-sheet-pilot/"
REJUDGE = "experiments/001b-judge-lean/"
HOUSE = PILOT + "runs/house/"


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "archive"

        def ignored(directory, names):
            return [name for name in names
                    if name in ("__pycache__", ".DS_Store") or name.endswith(".pyc")
                    or (Path(directory) == REPO and name == ".git")]

        shutil.copytree(REPO, self.root, ignore=ignored)
        # Include new verifier files during development. Tests never repair a
        # damaged manifest before testing it, except where explicitly stated.
        self.write_manifest()

    def path(self, relative):
        return self.root / relative

    def write_manifest(self):
        lines = []
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and path.name != "MANIFEST.sha256":
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                lines.append(digest + "  " + path.relative_to(self.root).as_posix())
        self.path("MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def edit_json(self, relative, edit):
        path = self.path(relative)
        value = json.loads(path.read_text(encoding="utf-8"))
        edit(value)
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def edit_rows(self, relative, edit):
        path = self.path(relative)
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        edit(rows)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def test_published_archive_including_recorded_errors_and_exception(self):
        self.assertTrue(verify_manifest(self.root))
        self.assertTrue(verify_freezes(self.root))
        self.assertTrue(verify_evidence(self.root))

    def test_manifest_detects_changed_file(self):
        with self.path("README.md").open("a", encoding="utf-8") as stream:
            stream.write("\nChanged.\n")
        with self.assertRaises(ValueError):
            verify_manifest(self.root)

    def test_manifest_detects_missing_file(self):
        self.path("README.md").unlink()
        with self.assertRaises(ValueError):
            verify_manifest(self.root)

    def test_manifest_detects_unlisted_file(self):
        self.path("unlisted.txt").write_text("unlisted evidence\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_manifest(self.root)

    def test_manifest_rejects_duplicate_entry(self):
        path = self.path("MANIFEST.sha256")
        text = path.read_text(encoding="utf-8")
        path.write_text(text + text.splitlines()[0] + "\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_manifest(self.root)

    def test_manifest_rejects_unsafe_and_malformed_entries(self):
        manifest = self.path("MANIFEST.sha256")
        clean = manifest.read_text(encoding="utf-8")
        digest = "0" * 64
        for entry in (digest + "  ../outside", digest + "  /tmp/outside",
                      digest + " README.md", "not-a-hash  README.md"):
            with self.subTest(entry=entry):
                manifest.write_text(clean + entry + "\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    verify_manifest(self.root)

    def test_manifest_rejects_symlink(self):
        self.path("linked.txt").symlink_to(self.path("README.md"))
        with self.assertRaises(ValueError):
            verify_manifest(self.root)

    def test_frozen_sheet_cannot_be_repaired_by_updating_manifest(self):
        with self.path("sheet/SHEET_SHORT_v2.md").open("a", encoding="utf-8") as stream:
            stream.write("\n")
        self.write_manifest()
        verify_manifest(self.root)
        with self.assertRaises(ValueError):
            verify_freezes(self.root)

    def test_freeze_record_cannot_omit_commitments(self):
        self.edit_json(PILOT + "FREEZE.json", lambda data: data["files"].pop("PREREG.md"))
        self.write_manifest()
        verify_manifest(self.root)
        with self.assertRaises(ValueError):
            verify_freezes(self.root)

    def test_known_public_key_exception_is_exact_not_blanket(self):
        with self.path(HOUSE + "key.json").open("a", encoding="utf-8") as stream:
            stream.write("\n")
        with self.assertRaises(ValueError):
            verify_freezes(self.root)

    def test_duplicate_planned_pair_is_refused_without_hash_check(self):
        self.edit_json(HOUSE + "key.json", lambda data:
                       data["meta"]["planned_pairs"].append(data["meta"]["planned_pairs"][0]))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_incomplete_plan_is_refused_without_hash_check(self):
        self.edit_json(HOUSE + "key.json", lambda data: data["meta"]["planned_pairs"].pop())
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_duplicate_json_key_is_refused(self):
        path = self.path(HOUSE + "key.json")
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace('"meta": {', '"meta": {}, "meta": {', 1), encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_duplicate_raw_reply_is_refused(self):
        self.edit_rows(HOUSE + "raw.ndjson", lambda rows: rows.append(rows[0]))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_changed_packet_reply_is_refused(self):
        self.edit_rows(HOUSE + "judge_packet.jsonl", lambda rows:
                       rows[0].update(reply="This is not the recorded reply."))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_missing_judge_score_is_refused(self):
        self.edit_rows(HOUSE + "judge_scores.jsonl", lambda rows: rows.pop())
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_duplicate_judge_score_is_refused(self):
        self.edit_rows(HOUSE + "judge_scores.jsonl", lambda rows: rows.append(rows[0]))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_numeric_judge_verdict_is_not_boolean(self):
        self.edit_rows(HOUSE + "judge_scores.jsonl", lambda rows: rows[0].update({"pass": 1}))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_published_total_must_match_scores(self):
        self.edit_json(PILOT + "PILOT_RESULTS.json", lambda data:
                       data["results"]["house"]["C0"].update({"pass": 32}))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_rejudge_setup_map_must_match_original_key(self):
        def change(data):
            key = next(iter(data))
            data[key] = "C1" if data[key] == "C0" else "C0"
        self.edit_json(REJUDGE + "work/setup_map.json", change)
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_u2_id_repair_must_not_change_verdicts(self):
        self.edit_rows(REJUDGE + "work/final/scores/U2_id_restored.jsonl", lambda rows:
                       rows[0].update({"pass": not rows[0]["pass"]}))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_cli_clean_copy_and_corrupted_copy(self):
        command = [sys.executable, "-B", str(REPO / "tools/verify_archive.py"),
                   "--root", str(self.root)]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        def snapshot():
            return {path.relative_to(self.root).as_posix():
                    hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
                    for path in self.root.rglob("*")}
        before = snapshot()
        good = subprocess.run(command, cwd=self.temp.name, capture_output=True,
                              text=True, env=env, timeout=60)
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        self.assertEqual(snapshot(), before, "verification changed the archive")
        self.path("README.md").write_text("damaged\n", encoding="utf-8")
        bad = subprocess.run(command, cwd=self.temp.name, capture_output=True,
                             text=True, env=env, timeout=60)
        self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)


if __name__ == "__main__":
    unittest.main()
