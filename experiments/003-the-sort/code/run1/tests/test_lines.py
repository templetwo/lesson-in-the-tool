"""Tests for the lines loader. The git-backed tests read the real repository read only."""
import fakes_first  # noqa: F401  (must stay the first import)

import os
import unittest

from common import Refuse
from lines_loader import parse_numbered_lines, load_lines

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
COMMIT = "441752c"
PATH = "sheet/SHEET_SHORT_v2.md"


def numbered(n, start=1):
    return "# Title\n\nIntro line.\n\n" + "\n\n".join("%d. Item %d text." % (i, i) for i in range(start, start + n)) + "\n"


class ParseTests(unittest.TestCase):
    def test_seventeen_ok_and_only_number_dot_space_removed(self):
        lines = parse_numbered_lines(numbered(17))
        self.assertEqual(len(lines), 17)
        self.assertEqual(lines[0], "Item 1 text.")
        self.assertEqual(lines[16], "Item 17 text.")

    def test_keeps_inner_text_exactly(self):
        text = numbered(16) + "\n17.  two spaces, \"quotes\", 5 of 321.\n"
        lines = parse_numbered_lines(text)
        self.assertEqual(lines[16], " two spaces, \"quotes\", 5 of 321.")

    def test_sixteen_refused(self):
        with self.assertRaises(Refuse):
            parse_numbered_lines(numbered(16))

    def test_eighteen_refused(self):
        with self.assertRaises(Refuse):
            parse_numbered_lines(numbered(18))

    def test_gap_refused(self):
        text = numbered(17).replace("5. Item 5 text.", "6. Item 5 text.")
        with self.assertRaises(Refuse):
            parse_numbered_lines(text)

    def test_continuation_refused(self):
        text = numbered(17).replace("3. Item 3 text.", "3. Item 3 text.\nand it runs on")
        with self.assertRaises(Refuse):
            parse_numbered_lines(text)

    def test_text_after_items_refused(self):
        with self.assertRaises(Refuse):
            parse_numbered_lines(numbered(17) + "\nA footer.\n")

    def test_carriage_return_refused(self):
        with self.assertRaises(Refuse):
            parse_numbered_lines(numbered(17).replace("\n", "\r\n"))


class GitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isdir(os.path.join(REPO, ".git")):
            raise AssertionError("repository not found at %s; these tests need it (read only)" % REPO)

    def test_real_sheet_loads(self):
        got = load_lines(REPO, COMMIT, PATH)
        self.assertEqual(len(got["lines"]), 17)
        self.assertEqual(len(got["commit"]), 40)
        self.assertTrue(got["commit"].startswith(COMMIT))
        self.assertEqual(got["commit_requested"], COMMIT)
        self.assertEqual(len(got["sha256"]), 64)
        self.assertTrue(got["lines"][0].startswith("Do not mark your own answer as checked"))

    def test_readme_is_refused(self):
        with self.assertRaises(Refuse):
            load_lines(REPO, COMMIT, "README.md")

    def test_bad_commit_refused(self):
        with self.assertRaises(Refuse):
            load_lines(REPO, "0000000000000000000000000000000000000000", PATH)

    def test_missing_path_refused(self):
        with self.assertRaises(Refuse):
            load_lines(REPO, COMMIT, "sheet/NO_SUCH_FILE.md")

    def test_escaping_path_refused(self):
        with self.assertRaises(Refuse):
            load_lines(REPO, COMMIT, "../x.md")


if __name__ == "__main__":
    unittest.main()
