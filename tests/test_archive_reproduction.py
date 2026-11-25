"""Check reproduction comparisons independently of manifest and freeze gates."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import verify_archive
from verify_archive import PILOT, REJUDGE, verify_manifest, verify_reproductions


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "archive"
        # Only the published inputs used by these reproductions. No later
        # experiment or private job is needed, copied, or executed.
        for relative in (PILOT, REJUDGE, "sheet"):
            shutil.copytree(REPO / relative, self.root / relative,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))

    def assert_reproduction_refuses(self, message):
        # Deliberately bless the edited bytes in a fresh manifest. Failure must
        # come from the reproduction itself, not a stale checksum or a freeze.
        lines = []
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and path.name != "MANIFEST.sha256":
                lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + "  "
                             + path.relative_to(self.root).as_posix())
        (self.root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
        verify_manifest(self.root)
        with self.assertRaisesRegex(ValueError, re.escape(message)):
            verify_reproductions(self.root)

    def test_changed_auto_verdict_is_refused_after_manifest_update(self):
        path = self.root / PILOT / "runs/house/auto_scores.ndjson"
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        for index, line in enumerate(lines):
            row = json.loads(line)
            if row["verdict"] == "pass":
                # Both values belong to the score schema. Keep IDs, count,
                # order, and every other row intact; recomputation must catch it.
                row["verdict"] = "fail"
                lines[index] = json.dumps(row) + "\n"
                break
        else:
            self.fail("fixture has no auto-pass verdict to change")
        path.write_text("".join(lines), encoding="utf-8")
        self.assert_reproduction_refuses("reproduction differs: %s" % path)

    def test_changed_tally_number_is_refused_after_manifest_update(self):
        path = self.root / REJUDGE / "work/final/TALLY.txt"
        original = path.read_text(encoding="utf-8")
        before = "  C0       31    31    30      31"
        after = "  C0       32    31    30      31"
        self.assertEqual(original.count(before), 1)
        path.write_text(original.replace(before, after), encoding="utf-8")
        self.assert_reproduction_refuses("001b tally differs from published TALLY.txt")

    def test_rebuilt_mask_bytes_are_compared_even_when_json_values_are_unchanged(self):
        path = self.root / REJUDGE / "work/masked.jsonl"
        real_run = verify_archive.run
        changed_outputs = []

        def altered_output(root, relative, *args, **kwargs):
            result = real_run(root, relative, *args, **kwargs)
            if relative == REJUDGE + "/harness/apply_mask_edits.py":
                output = Path(args[args.index("--out") + 1])
                output.write_bytes(b" " + output.read_bytes())
                changed_outputs.append(output)
            return result

        # Alter only the real builder's temporary output. The published mask
        # stays intact for the independent mask checker and packet builder;
        # no later comparison can accidentally cover the missing mask check.
        with patch.object(verify_archive, "run", altered_output):
            self.assert_reproduction_refuses("reproduction differs: %s" % path)
        self.assertEqual(len(changed_outputs), 1)


if __name__ == "__main__":
    unittest.main()
