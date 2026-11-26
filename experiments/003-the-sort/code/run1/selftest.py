"""Selftest for the Test 1 plumbing. Prints SELFTEST OK only when every check passed.

  /usr/bin/python3 -B selftest.py               run every check
  /usr/bin/python3 -B selftest.py --break NAME  run every check, with check NAME fed its broken input (must end FAILED)
  /usr/bin/python3 -B selftest.py --break-each  run each check once with its broken input; each must go red.
                                                Prints "N of N went red" and never prints SELFTEST OK.

Version 2 (2026-11-25, after PICKS_20261125.md): main and second homes, groups, exact and overlap matching.

Every check takes `broken`. For a refusal check, the normal input is the broken one (a refusal is expected, and for
its own stated reason) and the "broken" mode feeds a good input instead, so the refusal does not fire and the check
must go red. For a value check, "broken" mode perturbs the hand-made data, or the hand answer it is compared with,
so the check must go red.

HAND WORKING (all exact fractions; the code computes with fractions.Fraction and returns floats):

Tiny table, 4 lines x 3 raters, homes A and B: line1 A A A, line2 A A B, line3 B B B, line4 A B B.
  Fleiss' kappa. n = 3 raters, N = 4 lines. Counts (A,B) per line: (3,0) (2,1) (0,3) (1,2). Totals A 6, B 6 of 12.
    p_A = p_B = 1/2, so P_e = 1/4 + 1/4 = 1/2.
    P_i = (sum n_ij^2 - n) / (n(n-1)): line1 (9-3)/6 = 1; line2 (4+1-3)/6 = 1/3; line3 1; line4 1/3.
    P_bar = (1 + 1/3 + 1 + 1/3) / 4 = 2/3.  kappa = (2/3 - 1/2) / (1 - 1/2) = 1/3.
  Krippendorff's alpha, nominal. Each line has m = 3 values; each ordered pair of values from different raters adds
    1/(m-1) = 1/2 to the coincidence cell. line1: 6 AA pairs, o_AA += 3. line2: AA 2, AB 2, BA 2, so o_AA += 1,
    o_AB += 1, o_BA += 1. line3: o_BB += 3. line4: o_BB += 1, o_AB += 1, o_BA += 1.
    Totals: o_AA 4, o_BB 4, o_AB 2, o_BA 2. n_A = 6, n_B = 6, n = 12.
    alpha = 1 - (n-1) * (o_AB + o_BA) / (n_A n_B + n_B n_A) = 1 - 11 * 4 / 72 = 1 - 11/18 = 7/18.
  So kappa and alpha differ on complete data: 1 - alpha = (nN - 1)/(nN) * (1 - kappa) = 11/12 * 2/3 = 11/18.

Known split, 6 cloud sorters x 3 repeats, 3 lines, every sorter steady, main homes only. Majority main homes:
  line1 6 A; line2 4 A 2 B; line3 3 A 3 B. With cut points 5/4 for size 6: settled (6), leaning (4), contested (3,
  tie A/B).
  Fleiss: n = 6, N = 3. Totals A 13, B 5 of 18. P_e = (13^2 + 5^2) / 18^2 = 194/324 = 97/162.
    P_i: line1 (36-6)/30 = 1; line2 (16+4-6)/30 = 7/15; line3 (9+9-6)/30 = 2/5. P_bar = (1 + 7/15 + 2/5)/3 = 28/45.
    kappa = (28/45 - 97/162) / (1 - 97/162) = (504/810 - 485/810) / (325/810) = 19/325.
  Alpha: weight 1/5 per ordered pair. line1: o_AA += 30/5 = 6. line2: AA 12, BB 2, AB 8, BA 8 (each /5).
    line3: AA 6, BB 6, AB 9, BA 9 (each /5). o_AA = 48/5, o_BB = 8/5, o_AB = o_BA = 17/5. n_A = 13, n_B = 5, n = 18.
    alpha = 1 - 17 * (34/5) / (2 * 13 * 5) = 1 - 578/650 = 72/650.  Check: 1 - (17/18)(306/325) = 648/5850 = 72/650.

Two groups. The cloud group is the known split above. The local group, 2 sorters x 3 repeats, steady:
  L1 (A, A, B), L2 (B, A, B) on lines 1..3. Local per line: line1 A/B tie, "1 of 2"; line2 A "2 of 2"; line3 B "2 of
  2". No cut points for size 2, so no word. Kept apart, the cloud figures are exactly the known split's (line 2 stays
  4 of 6; pooled it would be 6 of 8).
  Local Fleiss: n = 2, N = 3, totals A 3, B 3, P_e = 1/2. P_i: line1 (1+1-2)/2 = 0; line2 (4-2)/2 = 1; line3 1.
    P_bar = 2/3. kappa = (2/3 - 1/2)/(1/2) = 1/3.
  Local alpha: m = 2, weight 1. line1 o_AB 1, o_BA 1; line2 o_AA 2; line3 o_BB 2. n_A = 3, n_B = 3, n = 6.
    alpha = 1 - 5 * 2 / (2 * 9) = 4/9.  Check: 1 - (5/6)(2/3) = 4/9.

Second homes, 6 cloud sorters x 3 repeats, 2 lines, homes A B C. Main homes: line1 A and line2 B in every reply.
  S1: line1 second B in r1, r2, r3; line2 second A in r1 only.
  S2: line1 second B in r1, C in r2, none in r3.      S3: line1 second C in r1 and r2, none in r3.
  S4..S6: no second homes.
  Line1 by majority (second given in more than 1.5 of 3 repeats): S1 B, S3 C -> 2 of 6, {B: 1, C: 1}.
  Line1 raw: replies with a second: S1 3 + S2 2 + S3 2 = 7 of 18; B 3 + 1 = 4, C 1 + 2 = 3.
  Line2 by majority: none -> 0 of 6. Raw: 1 of 18, {A: 1}.
  Main-home figures equal those of the same run with every second home removed (both lines 6 of 6, settled;
  kappa 1 since P_bar = 1 and P_e = 1/2; alpha 1).

House table, 6 cloud sorters x 3 repeats, 3 lines, homes A B C. Table: line1 main A second B; line2 main B; line3
  main "(this table)", which is not on the list, so line 3 is left out and named.
  Sorters: S1 every repeat line1 (A, B), line2 B. S2 line1 (A, B) in r1 only, else A; line2 B. S3 every repeat line1
  (A, C); line2 B. S4..S6 line1 A, line2 B.
  A sorter's homes = majority main + majority second. S1 line1 {A, B} = table, main A: exact and overlap; line2 {B}:
  exact and overlap. S2 line1 {A} (B only 1 of 3): overlap only; line2 exact. S3 line1 {A, C}: overlap only; line2
  exact. S4..S6 like S2. Per sorter (exact, overlap, of): S1 (2, 2, 2); S2..S6 (1, 2, 2). Group: exact 2 + 5 = 7,
  overlap 12, of 12.

No-majority set, 6 cloud sorters x 3 repeats, 2 lines, homes A B C (main homes only).
  S1 repeats: r1 (A, A), r2 (B, A), r3 (C, B). Line1 A/B/C: no majority. Line2 A/A/B: majority A, not all same.
    S1 steadiness: not-all-same 2 of 2 = 1.0; no-majority 1 of 2 = 0.5.
  S2: r2 fails to parse; r1 and r3 are (A, B). Majorities A and B. Not-all-same 1.0; no-majority 0. Failures: 1.
  S3..S6: (A, B) every time. Line1 -> modal A, 5 of 6. Line2 -> B, 5 of 6.
  Fleiss: not computed (S1 has no majority on line 1).
  Alpha: line1 five A values: o_AA += 5. line2 A + 5 B (m = 6): o_BB += 4, o_AB += 1, o_BA += 1.
    n_A = 6, n_B = 5, n = 11. alpha = 1 - 10 * 2 / (2 * 6 * 5) = 2/3.

Perfect agreement, 6 x 3, 4 lines, line i always home i (A B C D): every line settled with 6 of 6; kappa = 1
  (P_bar = 1, P_e = 4 * (1/4)^2 = 1/4); alpha = 1.
"""
import json
import os
import shutil
import sys

# Two-turn and callers build: before anything else, refuse to run beside SORT_REAL_CALLS and replace the key
# function, the key file opener, the transport and urllib's opener with tripwires (the same module the tests use).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests"))
import fakes_first  # noqa: E402,F401

from common import Refuse, HERE, make_scratch_dir
from lines_loader import parse_numbered_lines, load_lines
from homes import load_homes
from prompt_builder import build_prompt, load_deny_list
from reply_parser import parse_sort_reply as parse_reply
from callers import get_caller
from runner import run
from tally import compute as _compute, fleiss_kappa, krippendorff_alpha_nominal, bootstrap, check_not_dry, \
    FIXTURE_MARK


def compute(cfg, **kw):
    """Fix A: every run the older checks tally is a fixture run, so they pass the switch; the fix-round checks
    call _compute directly where the switch is the thing under test."""
    return _compute(cfg, allow_fixture=True, **kw)
from fixture_runs import make_run, FIXTURE_SENTENCE, fixture_provider
from freeze import write_freeze, verify_freeze

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
COMMIT = "441752c"
SHEET = "sheet/SHEET_SHORT_v2.md"
FIXTURE_HOMES = os.path.join(HERE, "fixtures", "homes_fixture.json")
DENY_FILE = os.path.join(HERE, "deny_list.txt")
LINES = ["FIXTURE line %d, not a real lesson." % i for i in range(1, 18)]
A, B, C, D = "FIXTURE-A", "FIXTURE-B", "FIXTURE-C", "FIXTURE-D"
CLOUD = [("S%d" % i, "cloud") for i in range(1, 7)]
LOCAL = [("L1", "local"), ("L2", "local")]
CP6 = {"6": {"settled_min": 5, "leaning_min": 4}}
CHECKS = []


def check(fn):
    CHECKS.append((fn.__name__, fn))
    return fn


def expect_refuse(fn, match):
    """The call must refuse, and for the stated reason: a refusal for some other reason is a failure too."""
    try:
        fn()
    except Refuse as e:
        if match not in str(e):
            raise AssertionError("refused for another reason: %s" % e)
        return
    raise AssertionError("no refusal")


def close(a, b):
    if a is None or abs(a - b) > 1e-12:
        raise AssertionError("got %r, expected %r" % (a, b))


class Scratch(object):
    def __enter__(self):
        self.d = make_scratch_dir("selftest_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d)


def numbered(n):
    return "# T\n\nIntro.\n\n" + "\n\n".join("%d. Item %d." % (i, i) for i in range(1, n + 1)) + "\n"


# ---------- lines loader ----------

def _parse_refusal(name, bad_text, match):
    def c(broken):
        text = numbered(17) if broken else bad_text
        expect_refuse(lambda: parse_numbered_lines(text), match)
    c.__name__ = name
    check(c)


_parse_refusal("loader_refuses_16_lines", numbered(16), "found 16 numbered lines")
_parse_refusal("loader_refuses_18_lines", numbered(18), "found 18 numbered lines")
_parse_refusal("loader_refuses_numbering_gap", numbered(17).replace("5. Item 5.", "6. Item 5."), "not numbered 1, 2, 3")
_parse_refusal("loader_refuses_continued_item", numbered(17).replace("3. Item 3.", "3. Item 3.\nruns on"),
               "continues numbered item 3")
_parse_refusal("loader_refuses_text_after_items", numbered(17) + "\nFooter.\n", "between or after")
_parse_refusal("loader_refuses_carriage_return", numbered(17).replace("\n", "\r\n"), "carriage return")


def _git_refusal(name, commit, path, match):
    def c(broken):
        expect_refuse(lambda: load_lines(REPO, COMMIT, SHEET) if broken else load_lines(REPO, commit, path), match)
    c.__name__ = name
    check(c)


_git_refusal("loader_refuses_unknown_commit", "0" * 40, SHEET, "git rev-parse --verify")
_git_refusal("loader_refuses_branch_name", "main", SHEET, "must be a hash")
_git_refusal("loader_refuses_missing_path", COMMIT, "sheet/NO_SUCH.md", "does not exist")
# README.md at 441752c has numbered items that run onto a second line; that is the refusal that fires first.
_git_refusal("loader_refuses_file_without_17_lines", COMMIT, "README.md", "numbered item")
_git_refusal("loader_refuses_climbing_path", COMMIT, "../x.md", "climb out")


@check
def loader_reads_real_sheet_at_commit(broken):
    got = load_lines(REPO, COMMIT, SHEET, expected=16 if broken else 17)
    assert len(got["lines"]) == 17 and len(got["commit"]) == 40 and got["commit"].startswith(COMMIT)
    assert len(got["sha256"]) == 64 and len(got["blob_id"]) == 40
    assert not got["lines"][0][:1].isdigit(), "number not stripped"


# ---------- homes ----------

GOOD_HOMES = [{"name": A, "definition": "FIXTURE definition A."}, {"name": B, "definition": "FIXTURE definition B."}]


def _homes_refusal(name, bad, match):
    def c(broken):
        with Scratch() as d:
            p = os.path.join(d, "h.json")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(GOOD_HOMES if broken else bad) if not isinstance(bad, str) or broken else bad)
            expect_refuse(lambda: load_homes(p), match)
    c.__name__ = name
    check(c)


_homes_refusal("homes_refuses_one_home", GOOD_HOMES[:1], "at least two")
_homes_refusal("homes_refuses_duplicate_name", [GOOD_HOMES[0], {"name": A, "definition": "x"}], "duplicate home name")
_homes_refusal("homes_refuses_duplicate_name_by_case", [GOOD_HOMES[0], {"name": A.lower(), "definition": "x"}],
               "duplicate home name")
_homes_refusal("homes_refuses_duplicate_definition",
               [GOOD_HOMES[0], {"name": B, "definition": "FIXTURE definition A."}], "repeats another")
_homes_refusal("homes_refuses_empty_definition", [GOOD_HOMES[0], {"name": B, "definition": "  "}], "empty definition")
_homes_refusal("homes_refuses_reserved_DRYRUN", [GOOD_HOMES[0], {"name": "DRYRUN", "definition": "x"}], "reserved")
_homes_refusal("homes_refuses_reserved_none", [GOOD_HOMES[0], {"name": "None", "definition": "x"}],
               "'none' is reserved")
_homes_refusal("homes_refuses_pipe_in_name", [GOOD_HOMES[0], {"name": "X|Y", "definition": "x"}], "'|'")
_homes_refusal("homes_refuses_comma_in_name", [GOOD_HOMES[0], {"name": "X,Y", "definition": "x"}], "','")
_homes_refusal("homes_refuses_extra_key", [GOOD_HOMES[0], {"name": B, "definition": "x", "k": 1}], "exactly the keys")
_homes_refusal("homes_refuses_not_a_list", {"homes": GOOD_HOMES}, "must be a JSON list")
_homes_refusal("homes_refuses_bad_json", "not json", "not valid JSON")


@check
def homes_fixture_is_plainly_fake_and_six(broken):
    homes, sha = load_homes(FIXTURE_HOMES)
    if broken:
        homes = homes + [{"name": "tool", "definition": "a real-looking definition"}]
    assert len(homes) == 6, "PICKS_20261125.md fixes six homes"
    assert all(h["name"].startswith("FIXTURE-") and h["definition"].startswith("FIXTURE ") for h in homes)


# ---------- prompt builder ----------

def _prompt(lines=None, homes=None, deny=None, leak=(), ls=1, hs=2):
    h = homes if homes is not None else load_homes(FIXTURE_HOMES)[0]
    return build_prompt(lines if lines is not None else LINES, h, ls, hs,
                        deny if deny is not None else load_deny_list(DENY_FILE), leak_strings=leak)


@check
def prompt_refuses_deny_hit_in_instructions(broken):
    deny = load_deny_list(DENY_FILE) + ([] if broken else ["what remains judgment"])
    expect_refuse(lambda: _prompt(deny=deny), "deny list hit in the instruction part")


@check
def prompt_refuses_deny_hit_in_home_definition(broken):
    homes = [dict(h) for h in load_homes(FIXTURE_HOMES)[0]]
    if not broken:
        homes[2]["definition"] = "FIXTURE definition that mentions a checklist."
    expect_refuse(lambda: _prompt(homes=homes), "['checklist']")


@check
def prompt_refuses_leak_string(broken):
    lines = list(LINES)
    lines[5] = "FIXTURE line that quotes 441752c."
    expect_refuse(lambda: _prompt(lines=lines, leak=() if broken else ("441752c",)), "must never reach a sorter")


@check
def prompt_refuses_numbered_line(broken):
    lines = list(LINES)
    lines[2] = "FIXTURE line." if broken else "FIXTURE line\n12. smuggled numbered line"
    expect_refuse(lambda: _prompt(lines=lines), "starts like a numbered item")


@check
def prompt_refuses_empty_deny_list(broken):
    with Scratch() as d:
        p = os.path.join(d, "deny.txt")
        with open(p, "w") as fh:
            fh.write("Temple\n" if broken else "\n\n")
        expect_refuse(lambda: load_deny_list(p), "is empty")


@check
def prompt_refuses_wrong_line_count(broken):
    expect_refuse(lambda: _prompt(lines=LINES if broken else LINES[:16]), "exactly 17 lines")


@check
def prompt_does_not_deny_check_the_lines(broken):
    lines = list(LINES)
    lines[0] = "FIXTURE line naming the Temple, a sheet and a README."
    homes = [dict(h) for h in load_homes(FIXTURE_HOMES)[0]]
    if broken:
        homes[0]["definition"] = "FIXTURE definition naming the Temple."
    p = _prompt(lines=lines, homes=homes)
    assert "Temple" in p.text and "Temple" not in p.instruction_text


@check
def prompt_is_seeded_shuffled_keyed_and_states_format(broken):
    p1, p2 = _prompt(ls=7, hs=8), _prompt(ls=7, hs=8 if not broken else 9)
    assert p1.text == p2.text, "same seeds gave different prompts"
    p3 = _prompt(ls=7, hs=99)
    assert p3.key == p1.key and p3.home_order != p1.home_order, "homes not shuffled on their own seed"
    assert [k["line_number"] for k in p1.key] != list(range(1, 18)), "lines not shuffled"
    assert p1.labels == ["L%02d" % i for i in range(1, 18)]
    for k in p1.key:
        assert "%s: %s\n" % (k["label"], k["line_text"]) in p1.text
    assert "line_number" not in p1.text
    assert "LABEL | main: HOME | second: HOME or none\n" in p1.text  # two-turn build: no sentence part


# ---------- reply parser ----------

LABELS, HOMES3 = ["L01", "L02", "L03"], [A, B, C]


def rep(*rows):
    """Two-turn build: the sort line has three parts; a fourth item in a row (the old sentence) is ignored."""
    return "".join("L%02d | main: %s | second: %s\n" % tuple(r[:3]) for r in rows)


GOOD_REPLY = rep((1, A, "none"), (2, B, A), (3, A, "none"))
TAIL = rep((2, A, "none"), (3, A, "none"))


def _parser_failure(name, bad, reason, dry=False):
    def c(broken):
        raw = GOOD_REPLY if broken else bad
        r = parse_reply(raw, LABELS, HOMES3, dry_run=dry)
        assert r["ok"] is False and r["rows"] == [] and r["raw"] == raw and r["errors"], "reply was accepted"
        assert any(reason in e for e in r["errors"]), "failed for another reason: %s" % r["errors"]
    c.__name__ = name
    check(c)


_parser_failure("parser_fails_unknown_main_home", "L01 | main: FIXTURE-Z | second: none\n" + TAIL,
                "unknown main home")
_parser_failure("parser_fails_missing_label", TAIL, "missing label")
_parser_failure("parser_fails_repeated_label", TAIL + TAIL + rep((1, A, "none")), "repeated")
_parser_failure("parser_fails_three_homes_in_second_field",
                "L01 | main: %s | second: %s, %s\n" % (A, B, C) + TAIL, "three or more homes")
_parser_failure("parser_fails_three_homes_as_extra_field",
                "L01 | main: %s | second: %s | third: %s\n" % (A, B, C) + TAIL, "three or more homes")
_parser_failure("parser_fails_two_main_homes", "L01 | main: %s, %s | second: none\n" % (A, B) + TAIL,
                "more than one main home")
_parser_failure("parser_fails_second_equal_to_main", rep((1, A, A, "s.")) + TAIL, "second home equals the main home")
_parser_failure("parser_fails_second_not_on_list", rep((1, A, "FIXTURE-Z", "s.")) + TAIL, "second home not on the list")
_parser_failure("parser_fails_second_without_main", rep((1, "none", B, "s.")) + TAIL, "second home with no main home")
_parser_failure("parser_fails_no_main_home", rep((1, "none", "none", "s.")) + TAIL, "no main home")
_parser_failure("parser_fails_old_one_home_format", "L01 | %s | s.\n" % A + TAIL, "cannot be placed")
_parser_failure("parser_fails_unplaceable_text", "Sure!\n" + GOOD_REPLY, "cannot be placed")
# Two-turn build: parser_fails_empty_sentence moved to the question parser (question_parser_fails_empty_sentence);
# in the sort, a line that still carries a sentence part cannot be placed.
_parser_failure("parser_fails_old_one_message_line_with_sentence", "L01 | main: %s | second: none | s.\n" % A + TAIL,
                "cannot be placed")
_parser_failure("parser_fails_unknown_label", GOOD_REPLY + rep((4, A, "none")), "unknown label")
_parser_failure("parser_fails_carriage_return", GOOD_REPLY.replace("\n", "\r\n"), "cannot be placed")
_parser_failure("parser_fails_code_fence", "```\n" + GOOD_REPLY + "```\n", "cannot be placed")
_parser_failure("parser_fails_DRYRUN_in_real_run", rep(*[(i, "DRYRUN", "none", "DRYRUN") for i in (1, 2, 3)]),
                "DRYRUN in a run not marked dry")


@check
def parser_accepts_one_or_two_homes_by_hand(broken):
    raw = GOOD_REPLY if not broken else GOOD_REPLY.replace("second: %s" % A, "second: %s" % C)
    r = parse_reply(raw, LABELS, HOMES3, dry_run=False)
    assert r["ok"], r["errors"]
    got = [(x["label"], x["home_main"], x["home_second"]) for x in r["rows"]]
    assert got == [("L01", A, None), ("L02", B, A), ("L03", A, None)], got
    assert all(set(x) == {"label", "home_main", "home_second"} for x in r["rows"])


@check
def parser_accepts_DRYRUN_only_when_dry(broken):
    dry = rep(*[(i, "DRYRUN", "none", "DRYRUN") for i in (1, 2, 3)])
    assert parse_reply(dry, LABELS, HOMES3, dry_run=not broken)["ok"]


# ---------- caller and runner ----------

def _run_cfg(out, **over):
    cfg = {"dry_run": True, "caller": "dryrun", "repo": REPO, "commit": COMMIT, "lines_path": SHEET,
           "homes_file": FIXTURE_HOMES, "deny_list": DENY_FILE, "prompt_text": os.path.join(HERE, "prompt_text.json"),
           "sorters": [{"name": "S1", "group": "cloud", "provider": "p1"},
                       {"name": "S2", "group": "cloud", "provider": "p2"},
                       {"name": "L1", "group": "local", "provider": "p3"}],
           "groups": {}, "repeats": 2, "master_seed": 11, "out_dir": out}
    cfg.update(over)
    return cfg


@check
def caller_refuses_unknown_name(broken):
    expect_refuse(lambda: get_caller("dryrun" if broken else "claude-real"), "no caller named")


def _runner_refusal(name, over, match):
    def c(broken):
        with Scratch() as d:
            cfg = _run_cfg(os.path.join(d, "run"), **({} if broken else over))
            expect_refuse(lambda: run(cfg), match)
    c.__name__ = name
    check(c)


_runner_refusal("runner_refuses_dry_caller_in_run_not_marked_dry", {"dry_run": False}, "not marked dry_run")
_runner_refusal("runner_refuses_out_dir_outside_folder", {"out_dir": "/tmp/public-sort-selftest-must-not-exist"},
                "outside this folder")
_runner_refusal("runner_refuses_deny_hit", {"deny_list": os.path.join(HERE, "fixtures", "deny_hits_fixture.txt")},
                "deny list hit")
_runner_refusal("runner_refuses_unknown_config_key", {"temperature": 0}, "does not know")
_runner_refusal("runner_refuses_sorter_without_group", {"sorters": [{"name": "S1", "provider": "p1"}]},
                "exactly {\"name\"")
_runner_refusal("runner_refuses_repeated_sorter",
                {"sorters": [{"name": "S1", "group": "cloud", "provider": "p1"},
                             {"name": "S1", "group": "local", "provider": "p2"}]}, "is repeated")


@check
def runner_refuses_non_empty_out_dir(broken):
    with Scratch() as d:
        out = os.path.join(d, "run")
        os.makedirs(out)
        if not broken:
            with open(os.path.join(out, "x"), "w") as fh:
                fh.write("x")
        expect_refuse(lambda: run(_run_cfg(out)), "not an empty folder")


@check
def runner_dry_run_marks_every_file_and_row(broken):
    with Scratch() as d:
        out = run(_run_cfg(os.path.join(d, "run")))
        if broken:
            p = os.path.join(out, "results", "S2__r1.json")
            with open(p, encoding="utf-8") as fh:
                o = json.load(fh)
            o["rows"][4]["dry_run"] = False
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(o, fh)
        n = 0
        for root, _, fs in os.walk(out):
            for f in fs:
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    o = json.load(fh)
                assert list(o)[0] == "dry_run" and o["dry_run"] is True, f
                for listname in ("rows", "files", "lines", "prompts", "sorters"):
                    for row in o.get(listname, []):
                        assert row.get("dry_run") is True, "%s %s row without dry_run true" % (f, listname)
                        for lab in row.get("labels", []):
                            assert lab.get("dry_run") is True
                n += 1
        assert n == 6 + 6 + 2, n
        with open(os.path.join(out, "results", "L1__r2.json"), encoding="utf-8") as fh:
            r = json.load(fh)
        assert r["parse_ok"] and len(r["rows"]) == 17 and r["group"] == "local"
        assert all(x["home_main"] == "DRYRUN" and x["home_second"] is None for x in r["rows"])


@check
def runner_example_config_has_the_picks_defaults(broken):
    with open(os.path.join(HERE, "config_dryrun.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    if broken:
        cfg["repeats"] = 2
    groups = [s["group"] for s in cfg["sorters"]]
    assert cfg["repeats"] == 3 and cfg["lines_path"] == SHEET and cfg["commit"] == COMMIT
    assert (groups.count("cloud"), groups.count("local"), len(groups)) == (6, 2, 8)
    assert len(load_homes(cfg["homes_file"])[0]) == 6


# ---------- tally refusals ----------

def _tcfg(run_dir, sorters=CLOUD, repeats=3, **over):
    cfg = {"run_dir": run_dir,
           "sorters": [{"name": n, "group": g, "provider": fixture_provider(n)} for n, g in sorters],
           "groups": {}, "repeats": repeats,
           "cut_points_by_size": CP6, "bootstrap": {"seed": 3, "draws": 200, "level": 0.95}}
    cfg.update(over)
    return cfg


def _good(d, sorters=CLOUD, **kw):
    return make_run(d, sorters, 3, [A, B], 2, {(s, r): [A, B] for s, _ in sorters for r in (1, 2, 3)}, **kw)


@check
def tally_refuses_missing_result_file(broken):
    with Scratch() as d:
        rd = _good(d)
        if not broken:
            os.remove(os.path.join(rd, "results", "S6__r3.json"))
        expect_refuse(lambda: compute(_tcfg(rd)), "expected file is missing: results/S6__r3.json")


@check
def tally_refuses_expected_sorter_absent(broken):
    with Scratch() as d:
        rd = _good(d)
        expect_refuse(lambda: compute(_tcfg(rd, sorters=CLOUD if broken else CLOUD + [("S7", "cloud")])),
                      "expected file is missing: results/S7__r1.json")


@check
def tally_refuses_unexpected_result_in_run(broken):
    with Scratch() as d:
        rd = _good(d)
        expect_refuse(lambda: compute(_tcfg(rd, sorters=CLOUD if broken else CLOUD[:5])), "does not expect")


@check
def tally_refuses_group_mismatch_with_run(broken):
    with Scratch() as d:
        rd = _good(d)
        s = CLOUD if broken else CLOUD[:4] + [("S5", "local"), ("S6", "local")]
        expect_refuse(lambda: compute(_tcfg(rd, sorters=s)), "do not match the run's key")


@check
def tally_refuses_group_of_one(broken):
    with Scratch() as d:
        rd = _good(d)
        s = CLOUD if broken else CLOUD[:5] + [("S6", "local")]
        expect_refuse(lambda: compute(_tcfg(rd, sorters=s)), "at least two sorters")


@check
def tally_refuses_changed_hash(broken):
    with Scratch() as d:
        rd = _good(d)
        if not broken:
            p = os.path.join(rd, "results", "S2__r2.json")
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(" ")
        expect_refuse(lambda: compute(_tcfg(rd)), "no longer matches: results/S2__r2.json")


@check
def tally_refuses_dry_row(broken):
    with Scratch() as d:
        # hashes are recorded after the row is marked, so this is the dry-row refusal and not a hash refusal
        rd = _good(d, dry_row_in=None if broken else ("S4", 2))
        expect_refuse(lambda: compute(_tcfg(rd)), "results/S4__r2.json: row /rows[0] does not say dry_run false")


@check
def tally_refuses_dry_run_folder(broken):
    with Scratch() as d:
        sor = [{"name": n, "group": g, "provider": fixture_provider(n)} for n, g in CLOUD]
        rd = _good(d) if broken else run(_run_cfg(os.path.join(d, "run"), sorters=sor, repeats=3))
        expect_refuse(lambda: compute(_tcfg(rd)), "manifest.json: top-level dry_run is not false")


@check
def tally_refuses_bad_cut_points_for_size(broken):
    with Scratch() as d:
        rd = _good(d)
        cp = CP6 if broken else {"6": {"settled_min": 4, "leaning_min": 5}}
        expect_refuse(lambda: compute(_tcfg(rd, cut_points_by_size=cp)), "cut points for size 6 must satisfy")


@check
def tally_refuses_missing_cut_points(broken):
    with Scratch() as d:
        rd = _good(d)
        cfg = _tcfg(rd)
        if not broken:
            del cfg["cut_points_by_size"]
        expect_refuse(lambda: compute(cfg), "missing cut_points_by_size")


@check
def tally_refuses_DRYRUN_in_a_home_field(broken):
    # Called directly: in a whole run, the hash check would catch a tampered file before this check runs.
    # The sentence field holding DRYRUN must NOT refuse: sentences are never looked at.
    row = {"dry_run": False, "home_main": A if broken else "DRYRUN", "home_second": None, "sentence": "DRYRUN"}
    expect_refuse(lambda: check_not_dry({"dry_run": False, "rows": [row]}, "f"), "reserved home DRYRUN")


@check
def tally_refuses_malformed_house_table(broken):
    with Scratch() as d:
        rd = _good(d)
        t = os.path.join(d, "table.json")
        rows = [{"line_number": 1, "home_main": A, "home_second": None},
                {"line_number": 2, "home_main": B, "home_second": None if broken else B}]
        with open(t, "w") as fh:
            json.dump({"rows": rows}, fh)
        expect_refuse(lambda: compute(_tcfg(rd, house_table=t)), "house table row is malformed")


# ---------- tally values on hand-made sets (see the module docstring for the working) ----------

def split_assign(sorters):
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


@check
def stats_tiny_table_kappa_and_alpha_by_hand(broken):
    units = [[A, A, A], [A, A, B], [B, B, B], [A, B, B]]
    if broken:
        units[1] = [A, A, A]
    close(fleiss_kappa(units), 1 / 3)
    close(krippendorff_alpha_nominal(units), 7 / 18)
    close(1 - krippendorff_alpha_nominal(units), (11 / 12) * (1 - fleiss_kappa(units)))


@check
def stats_undefined_when_one_home_or_incomplete(broken):
    one = [[A, A, A], [A, A, A]]
    if broken:
        one[1] = [A, A, B]
    assert fleiss_kappa(one) is None and krippendorff_alpha_nominal(one) is None
    assert fleiss_kappa([[A, None, B], [A, B, B]]) is None


@check
def tally_perfect_agreement(broken):
    with Scratch() as d:
        assign = {(s, r): [A, B, C, D] for s, _ in CLOUD for r in (1, 2, 3)}
        if broken:
            assign[("S3", 1)] = assign[("S3", 2)] = [A, B, C, A]
        g = compute(_tcfg(make_run(d, CLOUD, 3, [A, B, C, D], 4, assign)))[0]["groups"]["cloud"]
        assert [(x["modal_homes"], x["count_text"], x["class"]) for x in g["per_line"]] == \
            [([A], "6 of 6", "settled"), ([B], "6 of 6", "settled"), ([C], "6 of 6", "settled"),
             ([D], "6 of 6", "settled")]
        close(g["agreement"]["fleiss_kappa"]["value"], 1.0)
        close(g["agreement"]["krippendorff_alpha"]["value"], 1.0)
        assert all(v["share_lines_not_all_same"] == 0 and v["share_lines_no_majority"] == 0
                   for v in g["per_sorter"].values())


@check
def tally_known_split(broken):
    with Scratch() as d:
        assign = split_assign(CLOUD)
        if broken:
            for r in (1, 2, 3):
                assign[("S6", r)] = [A, B, A]
        g = compute(_tcfg(make_run(d, CLOUD, 3, [A, B], 3, assign)))[0]["groups"]["cloud"]
        got = [(x["modal_homes"], x["modal_count"], x["class"]) for x in g["per_line"]]
        assert got == [([A], 6, "settled"), ([A], 4, "leaning"), ([A, B], 3, "contested")], got
        close(g["agreement"]["fleiss_kappa"]["value"], 19 / 325)
        close(g["agreement"]["krippendorff_alpha"]["value"], 72 / 650)
        assert g["class_counts"] == {"settled": 1, "leaning": 1, "contested": 1}


@check
def tally_judgment_file_is_an_exact_copy(broken):
    with Scratch() as d:
        assign = split_assign(CLOUD)
        assign[("S2", 2)] = None
        _, judg = compute(_tcfg(make_run(d, CLOUD, 3, [A, B], 3, assign)))
        want = expected_judgment(3, CLOUD, 3, failed={("S2", 2)})
        if broken:
            want = want.replace(FIXTURE_SENTENCE % (2, "S4", 3), FIXTURE_SENTENCE % (2, "S4", 1), 1)
        assert judg == want, "judgment file differs from the exact copy"


@check
def tally_two_groups_kept_apart(broken):
    with Scratch() as d:
        both = CLOUD + LOCAL
        assign = split_assign(CLOUD)
        loc = {"L1": [A, A, B], "L2": [B, A, B] if not broken else [A, A, B]}
        for s, _ in LOCAL:
            for r in (1, 2, 3):
                assign[(s, r)] = loc[s]
        rep_, judg = compute(_tcfg(make_run(d, both, 3, [A, B], 3, assign), sorters=both))
        cl, lo = rep_["groups"]["cloud"], rep_["groups"]["local"]
        assert [x["count_text"] for x in cl["per_line"]] == ["6 of 6", "4 of 6", "3 of 6"]
        close(cl["agreement"]["fleiss_kappa"]["value"], 19 / 325)
        close(cl["agreement"]["krippendorff_alpha"]["value"], 72 / 650)
        got = [(x["modal_homes"], x["count_text"], x["class"]) for x in lo["per_line"]]
        assert got == [([A, B], "1 of 2", None), ([A], "2 of 2", None), ([B], "2 of 2", None)], got
        assert lo["class_counts"] is None and lo["cut_points"] is None
        assert lo["agreement"] == {}
        assert lo["agreement_note"] == "Agreement statistics are not computed for a group of two, by rule."
        assert "L1" not in json.dumps(cl) and "S1" not in json.dumps(lo)
        assert (cl["parse_failures"], lo["parse_failures"]) == ({"count": 0, "of_replies": 18},
                                                                {"count": 0, "of_replies": 6})


@check
def tally_group_size_with_cut_points_gets_words(broken):
    with Scratch() as d:
        both = CLOUD + LOCAL
        assign = split_assign(CLOUD)
        for r in (1, 2, 3):
            assign[("L1", r)], assign[("L2", r)] = [A, A, B], [B, A, B]
        cps = {"6": CP6["6"]}
        if not broken:
            cps["2"] = {"settled_min": 2, "leaning_min": 2}
        lo = compute(_tcfg(make_run(d, both, 3, [A, B], 3, assign), sorters=both,
                           cut_points_by_size=cps))[0]["groups"]["local"]
        assert [x["class"] for x in lo["per_line"]] == ["contested", "settled", "settled"]


def _second_assign():
    base = {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}
    sec = dict(base)
    sec[("S1", 1)] = [(A, B), (B, A)]
    sec[("S1", 2)] = sec[("S1", 3)] = [(A, B), B]
    sec[("S2", 1)], sec[("S2", 2)] = [(A, B), B], [(A, C), B]
    sec[("S3", 1)] = sec[("S3", 2)] = [(A, C), B]
    return base, sec


@check
def tally_second_homes_do_not_move_main_figures(broken):
    with Scratch() as d:
        base, sec = _second_assign()
        if broken:  # a changed MAIN home must move the figures; a changed second home must not
            sec[("S4", 1)] = sec[("S4", 2)] = [(C, A), B]
        os.makedirs(os.path.join(d, "a"))
        os.makedirs(os.path.join(d, "b"))
        g0 = compute(_tcfg(make_run(os.path.join(d, "a"), CLOUD, 3, [A, B, C], 2, base)))[0]["groups"]["cloud"]
        g1 = compute(_tcfg(make_run(os.path.join(d, "b"), CLOUD, 3, [A, B, C], 2, sec)))[0]["groups"]["cloud"]
        for k in ("per_line", "per_sorter", "agreement", "class_counts"):
            assert g0[k] == g1[k], "%s moved" % k
        close(g1["agreement"]["fleiss_kappa"]["value"], 1.0)


@check
def tally_second_home_report_by_hand(broken):
    with Scratch() as d:
        _, sec = _second_assign()
        if broken:
            sec[("S2", 3)] = [(A, B), B]
        g = compute(_tcfg(make_run(d, CLOUD, 3, [A, B, C], 2, sec)))[0]["groups"]["cloud"]
        s = {x["line_number"]: x for x in g["second_homes"]}
        assert s[1]["by_majority"] == {"sorters_with_second": 2, "of": 6, "homes": {B: 1, C: 1}}, s[1]
        assert s[1]["raw"] == {"replies_with_second": 7, "of_replies": 18, "homes": {B: 4, C: 3}}, s[1]
        assert s[2]["by_majority"] == {"sorters_with_second": 0, "of": 6, "homes": {}}
        assert s[2]["raw"] == {"replies_with_second": 1, "of_replies": 18, "homes": {A: 1}}


@check
def tally_house_table_exact_and_overlap_by_hand(broken):
    with Scratch() as d:
        assign = {(s, r): [A, B, C] for s, _ in CLOUD for r in (1, 2, 3)}
        for r in (1, 2, 3):
            assign[("S1", r)] = [(A, B), B, C]
            assign[("S3", r)] = [(A, C), B, C]
        assign[("S2", 1)] = [(A, B), B, C]
        if broken:
            assign[("S2", 2)] = [(A, B), B, C]
        rd = make_run(d, CLOUD, 3, [A, B, C], 3, assign)
        t = os.path.join(d, "table.json")
        with open(t, "w") as fh:
            json.dump({"rows": [{"line_number": 1, "home_main": A, "home_second": B},
                                {"line_number": 2, "home_main": B, "home_second": None},
                                {"line_number": 3, "home_main": "(this table)", "home_second": None}]}, fh)
        h = compute(_tcfg(rd, house_table=t))[0]["groups"]["cloud"]["house_table"]
        assert h["excluded_lines"] == [{"line_number": 3, "home_main": "(this table)", "home_second": None,
                                        "reason": "a home not on the list"}], h["excluded_lines"]
        assert h["per_sorter"]["S1"] == {"exact": 2, "overlap": 2, "of": 2}
        assert all(h["per_sorter"]["S%d" % i] == {"exact": 1, "overlap": 2, "of": 2} for i in range(2, 7)), \
            h["per_sorter"]
        assert h["group"] == {"exact": 7, "overlap": 12, "of": 12}, h["group"]


@check
def tally_no_majority_and_parse_failure(broken):
    with Scratch() as d:
        assign = {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}
        assign[("S1", 1)], assign[("S1", 2)], assign[("S1", 3)] = [A, A], [B, A], [C, B]
        assign[("S2", 2)] = None if not broken else [A, B]
        rep_, _ = compute(_tcfg(make_run(d, CLOUD, 3, [A, B, C], 2, assign)))
        g = rep_["groups"]["cloud"]
        ps = g["per_sorter"]
        assert (ps["S1"]["share_lines_not_all_same"], ps["S1"]["share_lines_no_majority"]) == (1.0, 0.5)
        assert (ps["S2"]["share_lines_not_all_same"], ps["S2"]["share_lines_no_majority"],
                ps["S2"]["repeats_failed"]) == (1.0, 0.0, 1)
        assert (ps["S3"]["share_lines_not_all_same"], ps["S3"]["share_lines_no_majority"]) == (0.0, 0.0)
        assert "parse_failures" not in rep_, "a pooled parse-failure count exists"
        assert g["parse_failures"] == {"count": 1, "of_replies": 18}, g["parse_failures"]
        assert rep_["parse_failures_listed"][0]["sorter"] == "S2"
        assert rep_["parse_failures_listed"][0]["errors"], "parse failure shown without its reasons"
        lines = {x["line_number"]: x for x in g["per_line"]}
        assert lines[1]["sorter_majority"]["S1"] is None and (lines[1]["modal_homes"], lines[1]["modal_count"]) == ([A], 5)
        assert (lines[2]["modal_homes"], lines[2]["modal_count"]) == ([B], 5)
        assert g["agreement"]["fleiss_kappa"]["value"] is None and "no majority" in g["agreement"]["fleiss_kappa"]["reason"]
        close(g["agreement"]["krippendorff_alpha"]["value"], 2 / 3)


@check
def tally_bootstrap_is_seeded(broken):
    import random as _r
    rng = _r.Random(1)
    units = [[rng.choice([A, B, C]) for _ in range(6)] for _ in range(17)]
    b1 = bootstrap(units, krippendorff_alpha_nominal, 5, 300, 0.95)
    b2 = bootstrap(units, krippendorff_alpha_nominal, 6 if broken else 5, 300, 0.95)
    assert b1["interval"] == b2["interval"] and b1["seed"] == 5


# ---------- freeze ----------

def _freeze_dir(d):
    for n in ("a.txt", "b.txt"):
        with open(os.path.join(d, n), "w") as fh:
            fh.write("FIXTURE " + n)


@check
def freeze_verify_passes_untouched(broken):
    with Scratch() as d:
        _freeze_dir(d)
        f = os.path.join(d, "FREEZE.json")
        write_freeze(d, ["a.txt", "b.txt"], f, "fixture", "selftest")
        if broken:
            with open(os.path.join(d, "b.txt"), "a") as fh:
                fh.write("x")
        assert verify_freeze(f, d) == []
        with open(f) as fh:
            raw = fh.read()
        assert not raw.endswith("\n") and raw == json.dumps(json.loads(raw), sort_keys=True, indent=1)


@check
def freeze_verify_fails_on_changed_file(broken):
    with Scratch() as d:
        _freeze_dir(d)
        f = os.path.join(d, "FREEZE.json")
        write_freeze(d, ["a.txt", "b.txt"], f, "fixture", "selftest")
        if not broken:
            with open(os.path.join(d, "a.txt"), "a") as fh:
                fh.write("x")
        assert any(p.startswith("changed: a.txt") for p in verify_freeze(f, d))


@check
def freeze_verify_fails_on_missing_file(broken):
    with Scratch() as d:
        _freeze_dir(d)
        f = os.path.join(d, "FREEZE.json")
        write_freeze(d, ["a.txt", "b.txt"], f, "fixture", "selftest")
        if not broken:
            os.remove(os.path.join(d, "b.txt"))
        assert "missing: b.txt" in verify_freeze(f, d)


def _freeze_refusal(name, files, pre_existing, match):
    def c(broken):
        with Scratch() as d:
            _freeze_dir(d)
            f = os.path.join(d, "FREEZE.json")
            if pre_existing and not broken:
                write_freeze(d, ["a.txt"], f, "fixture", "selftest")
            expect_refuse(lambda: write_freeze(d, ["a.txt"] if broken else files, f, "fixture", "selftest"), match)
    c.__name__ = name
    check(c)


_freeze_refusal("freeze_refuses_overwrite", ["a.txt"], True, "already exists")
_freeze_refusal("freeze_refuses_missing_file", ["nope.txt"], False, "not found")
_freeze_refusal("freeze_refuses_climbing_path", ["../a.txt"], False, "climbs out")
_freeze_refusal("freeze_refuses_repeated_file", ["a.txt", "a.txt"], False, "listed twice")


# ---------- fix round, 2026-11-25 (FIX_BRIEF_test1.md, fixes A to I) ----------

def _rewrite(run_dir, rel, mutate):
    """Edit one JSON file of a run and refresh its manifest hash, as a careful forger would."""
    from common import write_json, sha256_file
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


def _capture(fn, *args):
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*args)
    return code, buf.getvalue().splitlines()


# A: fixture runs are never data; the switch marks every output.

@check
def tally_refuses_fixture_caller_without_switch(broken):
    with Scratch() as d:
        rd = _good(d)
        expect_refuse(lambda: _compute(_tcfg(rd), allow_fixture=broken), "not on the tally config's real_callers")


@check
def tally_refuses_fixture_in_real_callers(broken):
    with Scratch() as d:
        rd = _good(d)
        rc = ["lab-model"] if broken else ["Fixture"]
        expect_refuse(lambda: _compute(_tcfg(rd, real_callers=rc), allow_fixture=True), "real_callers must be")


@check
def tally_fixture_switch_marks_every_output(broken):
    import tally as tally_mod
    with Scratch() as d:
        assign = {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}
        rd = make_run(d, CLOUD, 3, [A, B], 2, assign, caller="lab-model" if broken else "fixture")
        cfg = _tcfg(rd, out_dir=os.path.join(d, "out"), **({"real_callers": ["lab-model"]} if broken else {}))
        cp = os.path.join(d, "cfg.json")
        with open(cp, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh)
        code, lines = _capture(tally_mod.main, ["--config", cp] + ([] if broken else ["--allow-fixture"]))
        assert code == 0 and lines[0].startswith(FIXTURE_MARK), lines[:2]
        with open(os.path.join(d, "out", "tally.json"), encoding="utf-8") as fh:
            assert list(json.load(fh).items())[0] == ("status", FIXTURE_MARK)
        with open(os.path.join(d, "out", "judgment_sentences.txt"), encoding="utf-8") as fh:
            assert fh.readline() == FIXTURE_MARK + "\n"


# B: "6 from 3".

_runner_refusal("runner_refuses_group_with_too_few_providers", {"groups": {"cloud": {"min_providers": 3}}},
                "spans 2 provider")
_runner_refusal("runner_refuses_groups_entry_no_sorter_has", {"groups": {"clouds": {"min_providers": 1}}},
                "no sorter has")


@check
def tally_refuses_group_with_too_few_providers(broken):
    with Scratch() as d:
        provs = dict(zip([s for s, _ in CLOUD], ["p1", "p1", "p2", "p2", "p2", "P2"]))
        rd = make_run(d, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}, providers=provs)
        cfg = _tcfg(rd, groups={"cloud": {"min_providers": 2 if broken else 3}})
        cfg["sorters"] = [{"name": s, "group": g, "provider": provs[s]} for s, g in CLOUD]
        expect_refuse(lambda: compute(cfg), "spans 2 provider")


# C: the wording lives in prompt_text.json.

PROMPT_TEXT = os.path.join(HERE, "prompt_text.json")
OLD_PROMPT_SHA_11_22 = "3ed4fcd5287b8bd9b06be445f94ef004ae9cb7cf9adffe83ea842ea46ac90c83"  # before fix C, 19:22:01


def _prompt_text_refusal(name, change, match):
    def c(broken):
        from prompt_builder import load_prompt_text
        with open(PROMPT_TEXT, encoding="utf-8") as fh:
            obj = json.load(fh)
        if not broken:
            change(obj)
        with Scratch() as d:
            p = os.path.join(d, "pt.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            expect_refuse(lambda: load_prompt_text(p), match)
    c.__name__ = name
    check(c)


_prompt_text_refusal("prompt_text_refuses_missing_field", lambda o: o.pop("question"), "missing the field question")
_prompt_text_refusal("prompt_text_refuses_empty_field", lambda o: o.update(turn1_reply_format=" "),
                     "field turn1_reply_format is empty")
_prompt_text_refusal("prompt_text_refuses_intro_without_question",  # two-turn build: the question is turn2_intro's
                     lambda o: o.update(turn2_intro=o["turn2_intro"].replace("{question}", "")),
                     "{question} exactly once")


def old_from_new(turn1_text, question="what remains judgment once this lesson has its home?"):
    """Two-turn build (the same as tests/test_two_turn_and_callers.old_from_new): put back exactly the pieces the
    split removed from the first message. Equal to the old one-message prompt only if nothing else changed."""
    t = turn1_text.replace("Use the home names exactly as written.\n\n",
                           "Use the home names exactly as written. Then write one sentence that answers this "
                           "question: " + question + "\n\n", 1)
    t = t.replace("LABEL | main: HOME | second: HOME or none\n",
                  "LABEL | main: HOME | second: HOME or none | SENTENCE\n", 1)
    return t.replace("or the word none. Separate the three parts",
                     "or the word none. SENTENCE is one sentence that does not contain the character |. Separate "
                     "the four parts", 1)


@check
def prompt_text_wording_unchanged_and_status_not_sent(broken):
    """Two-turn build: the first message with the removed pieces put back is the old prompt byte for byte."""
    from prompt_builder import load_prompt_text
    from common import sha256_bytes
    pt = load_prompt_text(PROMPT_TEXT)
    p = build_prompt(LINES, load_homes(FIXTURE_HOMES)[0], 11, 23 if broken else 22, load_deny_list(DENY_FILE),
                     prompt_text=pt)
    got = sha256_bytes(old_from_new(p.text).encode("utf-8"))
    assert got == OLD_PROMPT_SHA_11_22, "the wording moved: %s" % got
    assert pt["status"] not in p.text + p.question_text and "DRAFT" not in p.text + p.question_text


@check
def runner_records_prompt_text_sha_in_key(broken):
    from common import sha256_file
    with Scratch() as d:
        src = PROMPT_TEXT
        if broken:
            with open(PROMPT_TEXT, encoding="utf-8") as fh:
                obj = json.load(fh)
            obj["question"] = "FIXTURE question?"
            src = os.path.join(d, "pt.json")
            with open(src, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
        out = run(_run_cfg(os.path.join(d, "run"), prompt_text=src))
        with open(os.path.join(out, "key.json"), encoding="utf-8") as fh:
            key = json.load(fh)
        assert key["prompt_text_sha256"] == sha256_file(PROMPT_TEXT), "key records another prompt text"


# D: labels and lines pair one to one; each prompt once.

def _key_refusal(name, mutate, match):
    def c(broken):
        with Scratch() as d:
            rd = _good(d)
            _rewrite(rd, "key.json", (lambda k: None) if broken else mutate)
            expect_refuse(lambda: compute(_tcfg(rd)), match)
    c.__name__ = name
    check(c)


def _all_on_line_1(key):
    for p in key["prompts"]:
        for e in p["labels"]:
            e["line_number"] = 1


_key_refusal("tally_refuses_two_labels_on_one_line", _all_on_line_1, "one to one")
_key_refusal("tally_refuses_prompt_twice_in_key", lambda k: k["prompts"].append(dict(k["prompts"][0])),
             "more than once")
_key_refusal("tally_refuses_key_lines_not_1_to_n", lambda k: k["lines"][1].update(line_number=1),
             "key lines are not numbered exactly 1 to N")


# E: the stored parse must equal a fresh parse of raw_reply.

def _result_refusal(name, rel, mutate, match):
    def c(broken):
        with Scratch() as d:
            rd = _good(d)
            _rewrite(rd, rel, (lambda r: None) if broken else mutate)
            expect_refuse(lambda: compute(_tcfg(rd)), match)
    c.__name__ = name
    check(c)


_result_refusal("tally_refuses_raw_reply_changed_rows_kept", "results/S2__r1.json",
                lambda r: r.update(raw_reply="DRYRUN"), "fresh parse")
_result_refusal("tally_refuses_stored_row_changed_raw_kept", "results/S3__r2.json",
                lambda r: r["rows"][0].update(home_main=B if r["rows"][0]["home_main"] == A else A), "fresh parse")


# F: files on disk and in the manifest are exactly the expected ones.

@check
def tally_refuses_unlisted_file_on_disk(broken):
    with Scratch() as d:
        rd = _good(d)
        if not broken:
            with open(os.path.join(rd, "results", "extra.json"), "w") as fh:
                fh.write("{}")
        expect_refuse(lambda: compute(_tcfg(rd)), "not listed in the manifest: results/extra.json")


@check
def tally_refuses_listed_file_not_expected(broken):
    from common import sha256_file, write_json
    with Scratch() as d:
        rd = _good(d)
        if not broken:
            p = os.path.join(rd, "prompts", "S9__r1.json")
            with open(p, "w") as fh:
                fh.write("{}")
            with open(os.path.join(rd, "manifest.json"), encoding="utf-8") as fh:
                man = json.load(fh)
            man["files"].append({"dry_run": False, "path": "prompts/S9__r1.json", "sha256": sha256_file(p)})
            write_json(os.path.join(rd, "manifest.json"), man)
        expect_refuse(lambda: compute(_tcfg(rd)), "does not expect: ['prompts/S9__r1.json']")


@check
def tally_refuses_expected_prompt_missing(broken):
    with Scratch() as d:
        rd = _good(d)
        if not broken:
            os.remove(os.path.join(rd, "prompts", "S1__r1.json"))
        expect_refuse(lambda: compute(_tcfg(rd)), "expected file is missing: prompts/S1__r1.json")


# G: names that differ only by case.

def _twin_refusal(name, sorters):
    def c(broken):
        with Scratch() as d:
            out = os.path.join(d, "run")
            cfg = _run_cfg(out, **({} if broken else {"sorters": sorters}))
            expect_refuse(lambda: run(cfg), "equal after case folding")
            assert not os.path.exists(out), "the runner wrote before refusing"
    c.__name__ = name
    check(c)


_twin_refusal("runner_refuses_case_twin_sorters", [{"name": "S1", "group": "cloud", "provider": "p1"},
                                                   {"name": "s1", "group": "cloud", "provider": "p2"}])
_twin_refusal("runner_refuses_case_twin_groups", [{"name": "S1", "group": "cloud", "provider": "p1"},
                                                  {"name": "S2", "group": "Cloud", "provider": "p2"}])


@check
def runner_refuses_case_twin_paths(broken):
    from runner import check_planned_paths
    second = "results/S2__r1.json" if broken else "results/s1__r1.json"
    expect_refuse(lambda: check_planned_paths(["results/S1__r1.json", second]), "equal after case folding")


# H: links and two spellings in the freeze helper.

_freeze_refusal("freeze_refuses_dot_slash_twin", ["a.txt", "./a.txt"], False, "listed twice")
_freeze_refusal("freeze_refuses_case_twin", ["a.txt", "A.txt"], False, "listed twice")


@check
def freeze_stores_normalised_path(broken):
    with Scratch() as d:
        _freeze_dir(d)
        obj = write_freeze(d, ["./b.txt" if broken else "./a.txt"], os.path.join(d, "FREEZE.json"), "fixture", "st")
        assert list(obj["files"]) == ["a.txt"], list(obj["files"])


@check
def freeze_refuses_listed_symlink(broken):
    with Scratch() as d:
        _freeze_dir(d)
        os.symlink(os.path.join(d, "a.txt"), os.path.join(d, "link.txt"))
        expect_refuse(lambda: write_freeze(d, ["a.txt" if broken else "link.txt"], os.path.join(d, "F.json"),
                                           "fixture", "st"), "symbolic link")


@check
def freeze_refuses_link_out_of_root(broken):
    with Scratch() as d:
        root, outside = os.path.join(d, "root"), os.path.join(d, "outside")
        os.makedirs(root)
        os.makedirs(outside)
        _freeze_dir(root)
        _freeze_dir(outside)
        os.symlink(outside, os.path.join(root, "away"))
        expect_refuse(lambda: write_freeze(root, ["a.txt" if broken else "away/a.txt"],
                                           os.path.join(root, "F.json"), "fixture", "st"), "outside the root")


@check
def freeze_verify_refuses_symlink(broken):
    with Scratch() as d:
        root, outside = os.path.join(d, "root"), os.path.join(d, "outside")
        os.makedirs(root)
        os.makedirs(outside)
        _freeze_dir(root)
        _freeze_dir(outside)
        f = os.path.join(root, "FREEZE.json")
        write_freeze(root, ["a.txt", "b.txt"], f, "fixture", "st")
        if not broken:
            os.remove(os.path.join(root, "a.txt"))
            os.symlink(os.path.join(outside, "a.txt"), os.path.join(root, "a.txt"))
        assert any("symbolic link" in p for p in verify_freeze(f, root)), verify_freeze(f, root)


# I: inventory, the outside anchor, the stated limits.

def _inv_dir(d):
    _freeze_dir(d)
    os.makedirs(os.path.join(d, "data", "deep"))
    for n in ("data/d1.txt", "data/deep/d2.txt"):
        with open(os.path.join(d, n), "w") as fh:
            fh.write("FIXTURE " + n)


@check
def freeze_inventory_refuses_unlisted_file(broken):
    with Scratch() as d:
        _inv_dir(d)
        f = os.path.join(d, "FREEZE.json")
        write_freeze(d, ["a.txt"], f, "fixture", "st", inventory=["data"])
        if not broken:
            with open(os.path.join(d, "data", "deep", "new.txt"), "w") as fh:
                fh.write("FIXTURE new")
        assert any(p.startswith("unlisted file under inventory folder data") for p in verify_freeze(f, d))


@check
def freeze_inventory_catches_removed_entry(broken):
    with Scratch() as d:
        _inv_dir(d)
        f = os.path.join(d, "FREEZE.json")
        write_freeze(d, [], f, "fixture", "st", inventory=["data"])
        if not broken:
            with open(f, encoding="utf-8") as fh:
                obj = json.load(fh)
            del obj["files"]["data/d1.txt"]
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
        assert any("unlisted" in p and "data/d1.txt" in p for p in verify_freeze(f, d))


@check
def freeze_inventory_refuses_link_inside(broken):
    with Scratch() as d:
        _inv_dir(d)
        if not broken:
            os.symlink(os.path.join(d, "data", "deep"), os.path.join(d, "data", "loop"))
        expect_refuse(lambda: write_freeze(d, [], os.path.join(d, "F.json"), "fixture", "st", inventory=["data"]),
                      "symbolic link")


@check
def freeze_expect_sha256_refuses_rewritten_manifest(broken):
    from common import sha256_file
    with Scratch() as d:
        _freeze_dir(d)
        f = os.path.join(d, "FREEZE.json")
        write_freeze(d, ["a.txt"], f, "fixture", "st")
        kept = sha256_file(f)
        with open(os.path.join(d, "a.txt"), "a") as fh:
            fh.write("changed")
        with open(f, encoding="utf-8") as fh:
            obj = json.load(fh)
        obj["files"]["a.txt"] = sha256_file(os.path.join(d, "a.txt"))
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        assert verify_freeze(f, d) == [], "the documented limit no longer holds"
        probs = verify_freeze(f, d, expect_sha256=sha256_file(f) if broken else kept)
        assert probs and "not the expected" in probs[0], probs


@check
def freeze_verify_prints_limits_first(broken):
    import freeze as freeze_mod
    with Scratch() as d:
        _freeze_dir(d)
        f = os.path.join(d, "FREEZE.json")
        args = ["write", "--root", d, "--out", f, "--experiment", "fixture", "--frozen-by", "st", "a.txt"]
        code, lines = _capture(freeze_mod.main, args)
        if not broken:
            code, lines = _capture(freeze_mod.main, ["verify", "--root", d, f])
        assert code == 0 and lines[0].startswith("LIMITS:") and "does not notice" in " ".join(lines[:4]), lines[:2]


# ---------- two-turn and callers build, 2026-11-25 (BUILD_BRIEF_test1_two_turn_and_callers.md) ----------
# Fakes only. tests/fakes_first (imported at the top) has tripwired the key function, the key file opener, the
# transport and urllib's opener; a check that needs them installs a recording fake inside `patched`. The switch is
# "on" only as a plain dict passed as env (ALLOW); os.environ is never given it.

import contextlib  # noqa: E402
import copy  # noqa: E402
import re  # noqa: E402

ALLOW = {"SORT_REAL_CALLS": "allow"}
FAKE_KEY = "fake-key-Q7xW2pL9vN4rT6yZ8bC1"
QUESTION = "what remains judgment once this lesson has its home?"


@contextlib.contextmanager
def patched(obj, name, value):
    old = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield value
    finally:
        setattr(obj, name, old)


class Spies(object):
    def __init__(self, text="ready", fail=None):
        self.keys, self.posts, self.text, self.fail = [], [], text, fail

    def read_key(self, source, env=None, **kw):
        self.keys.append(source)
        return FAKE_KEY, {}

    def post(self, url, headers, body, timeout, env=None):
        self.posts.append({"url": url, "headers": dict(headers), "body": copy.deepcopy(body)})
        if self.fail:
            raise self.fail(headers)
        msgs = body.get("messages") or body.get("input")
        text = self.text(msgs) if callable(self.text) else self.text
        m = body["model"]
        if "anthropic" in url:
            return {"model": m, "content": [{"type": "text", "text": text}], "stop_reason": "end_turn", "usage": {}}
        if "/responses" in url:
            return {"model": m, "status": "completed", "usage": {},
                    "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}
        if "deepseek" in url:
            return {"model": m, "usage": {}, "choices": [{"message": {"content": text}, "finish_reason": "stop"}]}
        return {"model": m, "message": {"content": text}, "done": True, "done_reason": "stop"}


@contextlib.contextmanager
def spied(spies):
    import real_callers
    with patched(real_callers, "read_key", spies.read_key), patched(real_callers, "http_post_json", spies.post):
        yield spies


def _by_turn(msgs):
    labels = re.findall(r"(?m)^(L\d\d): ", msgs[0]["content"])
    if sum(1 for m in msgs if m["role"] == "user") == 1:
        return "".join("%s | main: %s | second: none\n" % (l, A) for l in labels)
    return "".join("%s | Fake sentence.\n" % l for l in labels)


def _real_cfg(out):
    return dict(_run_cfg(out, dry_run=False, caller="by_sorter", repeats=1,
                         sorters=[{"name": "S1", "group": "cloud", "provider": "anthropic"},
                                  {"name": "S2", "group": "cloud", "provider": "openai"},
                                  {"name": "L1", "group": "local", "provider": "ollama-local-b"}]),
                real_callers={"S1": "anthropic:claude-opus-5-5", "S2": "openai:gpt-6.2-sol",
                              "L1": "ollama-local-b:gemma4:e4b-mlx"})


EIGHT = ["anthropic:claude-fable-5-2", "anthropic:claude-opus-5-5", "openai:gpt-6.2-astra", "openai:gpt-6.2-sol",
         "xai:grok-4.7", "deepseek:deepseek-v4-pro", "ollama-local-a:qwen3.8:27b-draft4-text",
         "ollama-local-b:gemma4:e4b-mlx"]


# Part 1: the prompt.

@check
def prompt_first_message_has_no_judgment_outside_the_homes(broken):
    homes = [dict(h) for h in load_homes(FIXTURE_HOMES)[0]]
    homes[0]["definition"] = "FIXTURE definition that names judgment."
    p = _prompt(homes=homes)
    outside = p.text if broken else p.text.replace(p.homes_block, "")
    assert "judg" not in outside.casefold(), "the word is in the first message outside the homes"
    assert QUESTION in p.question_text and QUESTION not in p.text


@check
def prompt_refuses_judgment_in_the_first_message(broken):
    from prompt_builder import load_prompt_text
    pt = dict(load_prompt_text(PROMPT_TEXT))
    if not broken:
        pt["turn1_reply_format"] = pt["turn1_reply_format"].replace("Reply format.", "Reply format. Judgement.")
    expect_refuse(lambda: build_prompt(LINES, load_homes(FIXTURE_HOMES)[0], 1, 2, load_deny_list(DENY_FILE),
                                       prompt_text=pt), "judgment outside the list of homes")


@check
def prompt_second_message_holds_the_question_and_its_format(broken):
    p = _prompt()
    want = "For each lesson, write one sentence that answers this question: %s\n\n" % QUESTION
    if broken:
        want = want.replace("each", "every")
    assert p.question_text.startswith(want), p.question_text[:90]
    assert "LABEL | SENTENCE\n" in p.question_text and p.labels[0] + ":" not in p.question_text


# Part 1: the question parser.

def _question_failure(name, bad, reason):
    def c(broken):
        from reply_parser import parse_question_reply
        raw = "L01 | a.\nL02 | b.\nL03 | c.\n" if broken else bad
        r = parse_question_reply(raw, LABELS)
        assert r["ok"] is False and r["rows"] == [] and r["raw"] == raw and r["errors"], "reply was accepted"
        assert any(reason in e for e in r["errors"]), "failed for another reason: %s" % r["errors"]
    c.__name__ = name
    check(c)


_question_failure("question_parser_fails_empty_sentence", "L01 |  \nL02 | b.\nL03 | c.\n", "cannot be placed")
_question_failure("question_parser_fails_pipe_in_sentence", "L01 | a | b.\nL02 | b.\nL03 | c.\n", "cannot be placed")
_question_failure("question_parser_fails_missing_label", "L01 | a.\nL02 | b.\n", "missing label")
_question_failure("question_parser_fails_repeated_label", "L01 | a.\nL01 | a.\nL02 | b.\nL03 | c.\n", "repeated")
_question_failure("question_parser_fails_a_sort_line", "L01 | main: %s | second: none\nL02 | b.\nL03 | c.\n" % A,
                  "cannot be placed")
_question_failure("question_parser_fails_no_text", None, "reply is not text")


@check
def question_parser_accepts_by_hand(broken):
    from reply_parser import parse_question_reply
    r = parse_question_reply('L02 | Two  "x", café.\nL01 | One.\nL03 | Three.\n', LABELS)
    want = [{"label": "L01", "sentence": "One."}, {"label": "L02", "sentence": 'Two  "x", café.'},
            {"label": "L03", "sentence": "Three."}]
    if broken:
        want[1]["sentence"] = "Two \"x\", café."
    assert r["ok"] and r["rows"] == want, r


# Part 1: the dry caller and the runner.

@check
def caller_dry_answers_both_turns_from_the_conversation(broken):
    from callers import Conversation
    from reply_parser import parse_question_reply
    c = get_caller("dryrun")
    conv = Conversation([{"role": "user", "content": "x"}], LABELS)
    r1 = c.call(conv)
    assert parse_reply(r1.text, LABELS, HOMES3, dry_run=True)["ok"]
    conv.messages += [{"role": "assistant", "content": r1.text}] + \
        ([] if broken else [{"role": "user", "content": "y"}])
    r2 = c.call(conv)
    assert parse_question_reply(r2.text, LABELS)["ok"], r2.text


def _scripted(turn1=None, turn2=None, seen=None):
    from callers import Reply, DryRunCaller

    class Scripted(DryRunCaller):
        def call(self, conversation, env=None):
            if seen is not None:
                seen.append(copy.deepcopy(conversation.messages))
            real = DryRunCaller.call(self, conversation, env)
            o = turn1 if conversation.turn() == 1 else turn2
            return Reply(real.text if o is None else o, real.record)
    return Scripted


def _run_scripted(d, cls):
    import callers
    with patched(callers, "CALLERS", dict(callers.CALLERS, dryrun=cls)):
        out = run(_run_cfg(os.path.join(d, "run"), repeats=1))
    with open(os.path.join(out, "results", "S1__r1.json"), encoding="utf-8") as fh:
        res = json.load(fh)
    with open(os.path.join(out, "prompts", "S1__r1.json"), encoding="utf-8") as fh:
        prm = json.load(fh)
    return res, prm


@check
def runner_turn_two_is_sent_in_the_same_conversation(broken):
    with Scratch() as d:
        seen = []
        res, prm = _run_scripted(d, _scripted(seen=seen))
        want_reply = res["raw_reply"] + (" " if broken else "")
        assert seen[1] == [{"role": "user", "content": prm["text"]}, {"role": "assistant", "content": want_reply},
                           {"role": "user", "content": prm["question_text"]}], "conversation not appended as sent"
        assert res["turn2"]["sent"] and res["turn2"]["parse_ok"] and len(res["turn2"]["rows"]) == 17


@check
def runner_turn_one_unparsed_sends_no_turn_two(broken):
    with Scratch() as d:
        seen = []
        res, _ = _run_scripted(d, _scripted(turn1=None if broken else "FIXTURE junk", seen=seen))
        assert res["turn2"]["sent"] is False and "not asked" in res["turn2"]["not_sent_reason"], res["turn2"]
        assert len(seen) == 3 and res["raw_reply"] == "FIXTURE junk"  # three sorters, one call each


@check
def runner_turn_two_unparsed_keeps_the_sort(broken):
    with Scratch() as d:
        res, _ = _run_scripted(d, _scripted(turn2=None if broken else "FIXTURE junk answer"))
        assert res["parse_ok"] and len(res["rows"]) == 17
        assert res["turn2"]["sent"] and res["turn2"]["parse_ok"] is False, res["turn2"]["parse_ok"]
        assert res["turn2"]["raw_reply"] == "FIXTURE junk answer" and res["turn2"]["rows"] == []


# Part 1: the tally and turn 2.

@check
def tally_counts_do_not_depend_on_turn_two(broken):
    with Scratch() as d:
        both = CLOUD + LOCAL
        assign = split_assign(CLOUD)
        for s, _ in LOCAL:
            for r in (1, 2, 3):
                assign[(s, r)] = [(A, B), A, B] if s == "L1" else [B, A, (B, C)]
        os.makedirs(os.path.join(d, "a"))
        os.makedirs(os.path.join(d, "b"))
        g0 = compute(_tcfg(make_run(os.path.join(d, "a"), both, 3, [A, B, C], 3, assign), sorters=both))[0]
        assign2 = dict(assign)
        if broken:  # breaking a turn-1 reply must move the figures; breaking every turn-2 reply must not
            assign2[("S1", 1)] = assign2[("S1", 2)] = None
        t2 = {(s, r): ("broken" if r % 2 else "missing") for s, _ in both for r in (1, 2, 3)}
        g1 = compute(_tcfg(make_run(os.path.join(d, "b"), both, 3, [A, B, C], 3, assign2, turn2=t2),
                           sorters=both))[0]
        for g in ("cloud", "local"):
            a = {k: v for k, v in g0["groups"][g].items() if k != "turn2"}
            b = {k: v for k, v in g1["groups"][g].items() if k != "turn2"}
            assert a == b, "group %s moved" % g
        assert g1["groups"]["cloud"]["turn2"]["failed"] == 18


@check
def tally_turn_two_failures_counted_per_group(broken):
    with Scratch() as d:
        both = CLOUD + LOCAL
        assign = {(s, r): [A, B] for s, _ in both for r in (1, 2, 3)}
        assign[("L2", 3)] = None
        t2 = {("S1", 1): "broken", ("S3", 2): "missing", ("L1", 1): "broken"}
        rep_, judg = compute(_tcfg(make_run(d, both, 3, [A, B], 2, assign, turn2=t2), sorters=both))
        want = {"sent": 18, "failed": 2, "not_sent": 0, "of_replies": 18}
        if broken:
            want["failed"] = 3
        assert rep_["groups"]["cloud"]["turn2"] == want, rep_["groups"]["cloud"]["turn2"]
        assert rep_["groups"]["local"]["turn2"] == {"sent": 5, "failed": 1, "not_sent": 1, "of_replies": 6}
        assert "  [cloud] S1 repeat 1: (question reply failed to parse; no sentence)" in judg
        assert "  [local] L2 repeat 3: (sort reply failed to parse; question not asked)" in judg


_result_refusal("tally_refuses_turn_two_raw_changed_rows_kept", "results/S2__r1.json",
                lambda r: r["turn2"].update(raw_reply="FIXTURE other"), "turn 2 raw_reply")
_result_refusal("tally_refuses_turn_two_not_sent_after_a_parsed_sort", "results/S4__r3.json",
                lambda r: r.update(turn2={"dry_run": False, "sent": False}), "turn 2 was not sent")


@check
def tally_refuses_turn_two_sent_after_a_failed_sort(broken):
    with Scratch() as d:
        assign = {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}
        assign[("S4", 1)] = None
        rd = make_run(d, CLOUD, 3, [A, B], 2, assign)
        if not broken:
            _rewrite(rd, "results/S4__r1.json", lambda r: r["turn2"].update(sent=True, raw_reply="L01 | x.\n"))
        expect_refuse(lambda: compute(_tcfg(rd)), "must be the not-sent record")


@check
def tally_settings_carry_each_groups_min_providers(broken):
    """Helix record 82519: settings had the key "groups" twice and the second replaced the config's groups."""
    with Scratch() as d:
        provs = dict(zip([s for s, _ in CLOUD], ["p1", "p1", "p2", "p2", "p3", "p3"]))
        rd = make_run(d, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)}, providers=provs)
        cfg = _tcfg(rd, groups={} if broken else {"cloud": {"min_providers": 3}})
        cfg["sorters"] = [{"name": s, "group": g, "provider": provs[s]} for s, g in CLOUD]
        st = compute(cfg)[0]["settings"]
        assert st["groups"] == {"cloud": {"min_providers": 3}}, st["groups"]
        assert st["groups_note"] == "computed separately and never pooled"


@check
def tally_by_sorter_callers_each_on_the_list(broken):
    with Scratch() as d:
        callers = {s: ("lab-a" if i % 2 else "lab-b") for i, (s, _) in enumerate(CLOUD)}
        rd = make_run(d, CLOUD, 3, [A, B], 2, {(s, r): [A, B] for s, _ in CLOUD for r in (1, 2, 3)},
                      caller="by_sorter", result_callers=callers)
        rc = ["lab-a", "lab-b"] if broken else ["lab-a"]
        expect_refuse(lambda: _compute(_tcfg(rd, real_callers=rc)), "not on the tally config's real_callers")


# Part 2: the guard.

@check
def real_every_adapter_refuses_with_the_switch_unset(broken):
    from callers import Conversation
    with spied(Spies()) as sp:
        for name in EIGHT:
            expect_refuse(lambda: get_caller(name).call(Conversation([{"role": "user", "content": "x"}], []),
                                                        env=ALLOW if broken else {}), "SORT_REAL_CALLS")
        assert (sp.keys, sp.posts) == ([], [])


@check
def real_key_function_refuses_before_any_file(broken):
    opened = []

    def opener(*a, **k):
        opened.append(a)
        raise FileNotFoundError("FIXTURE")
    expect_refuse(lambda: fakes_first.REAL["read_key"]("anthropic", env=ALLOW if broken else {}, opener=opener),
                  "SORT_REAL_CALLS")
    assert opened == []


@check
def real_transport_refuses_before_a_connection(broken):
    # In broken mode the switch is on, so the real transport reaches urllib's opener, which is a tripwire here.
    expect_refuse(lambda: fakes_first.REAL["http_post_json"]("http://local-b.example.invalid:11434/api/chat", {}, {"model": "x"},
                                                              5, env=ALLOW if broken else {}), "SORT_REAL_CALLS")


@check
def real_runner_refuses_before_writing_anything(broken):
    with Scratch() as d, spied(Spies(text=_by_turn)) as sp:
        cfg = _real_cfg(os.path.join(d, "run"))
        expect_refuse(lambda: run(cfg, env=ALLOW if broken else {}), "SORT_REAL_CALLS")
        assert not os.path.exists(cfg["out_dir"]) and (sp.keys, sp.posts) == ([], [])


@check
def real_requests_hold_the_documented_thinking_settings(broken):
    import real_callers
    want = {"anthropic:claude-fable-5-2": {"thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}},
            "anthropic:claude-opus-5-5": {"thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}},
            "openai:gpt-6.2-astra": {"reasoning": {"effort": "high"}},
            "openai:gpt-6.2-sol": {"reasoning": {"effort": "high"}},
            "xai:grok-4.7": {"reasoning": {"effort": "high"}},
            "deepseek:deepseek-v4-pro": {"thinking": {"type": "enabled"}, "reasoning_effort": "high"},
            "ollama-local-a:qwen3.8:27b-draft4-text": {"think": None, "stream": False},
            "ollama-local-b:gemma4:e4b-mlx": {"think": None, "stream": False}}
    if broken:
        want["xai:grok-4.7"] = {"reasoning": {"effort": "medium"}}
    msgs = [{"role": "user", "content": "x"}]
    for name in EIGHT:
        a = real_callers.get_adapter(name)
        url, body = a.build_request(msgs)
        for k, v in want[name].items():
            assert body.get(k, "absent") == v, (name, k, body.get(k))
        assert body.get(a.messages_field) == msgs and body["model"] == a.model
        assert not set(body) & {"system", "tools", "instructions", "previous_response_id", "fallbacks",
                                "temperature", "conversation"}, (name, sorted(body))


@check
def real_failed_call_saves_no_key(broken):
    import real_callers
    from callers import Conversation
    echo = '{"error": "Incorrect API key provided: %s, starts %s, ends %s"}' % (FAKE_KEY, FAKE_KEY[:8], FAKE_KEY[-6:])
    with spied(Spies(fail=lambda h: real_callers.TransportError(401, echo))):
        r = get_caller("xai:grok-4.7").call(Conversation([{"role": "user", "content": "x"}], []), env=ALLOW)
    saved = echo if broken else json.dumps(r.record)
    assert "401" in saved
    for piece in (FAKE_KEY, FAKE_KEY[:8], FAKE_KEY[-6:]):
        assert piece not in saved, "a key piece was saved"


@check
def real_incomplete_reply_gives_no_text(broken):
    import real_callers
    from callers import Conversation

    def partial(url, headers, body, timeout, env=None):
        return {"model": body["model"], "choices": [{"message": {"content": "L01 | main"},
                                                     "finish_reason": "stop" if broken else "length"}]}
    with spied(Spies()), patched(real_callers, "http_post_json", partial):
        r = get_caller("deepseek:deepseek-v4-pro").call(Conversation([{"role": "user", "content": "x"}], []),
                                                        env=ALLOW)
    assert r.text is None and r.record["partial_text"] == "L01 | main", r.text


@check
def tests_name_no_real_key_path(broken):
    import glob
    from real_callers import scan_for_key_names
    with Scratch() as d:
        files = sorted(glob.glob(os.path.join(HERE, "tests", "*.py"))) + [os.path.join(HERE, "selftest.py")]
        if broken:
            p = os.path.join(d, "x.py")
            with open(p, "w") as fh:
                fh.write("p = '~/" + "." + "private-fixture-keys" + ".env'\n")
            files.append(p)
        assert scan_for_key_names(files) == [], scan_for_key_names(files)


# Part 2: smoke and the draft config.

def _draft():
    with open(os.path.join(HERE, "config_real_DRAFT.json"), encoding="utf-8") as fh:
        return json.load(fh)


@check
def smoke_prints_a_status_per_sorter(broken):
    import runner
    with spied(Spies(text="no" if broken else "ready")) as sp:
        lines = []
        code = runner.smoke(_draft(), env=ALLOW, out=lines.append)
    assert code == 0 and len([l for l in lines if ": ok," in l]) == 8, lines
    assert all((p["body"].get("messages") or p["body"].get("input")) ==
               [{"role": "user", "content": "Reply with the single word ready."}] for p in sp.posts)


@check
def smoke_refuses_every_sorter_with_the_switch_unset(broken):
    import runner
    with spied(Spies()) as sp:
        lines = []
        runner.smoke(_draft(), env=ALLOW if broken else {}, out=lines.append)
    assert len([l for l in lines if "REFUSED" in l]) == 8 and (sp.keys, sp.posts) == ([], []), lines


@check
def config_real_draft_has_the_picks(broken):
    import real_callers
    cfg = _draft()
    if broken:
        cfg["repeats"] = 2
    groups = [s["group"] for s in cfg["sorters"]]
    assert cfg["repeats"] == 3 and (groups.count("cloud"), groups.count("local")) == (6, 2)
    assert cfg["groups"] == {"cloud": {"min_providers": 3}} and "DRAFT" in cfg["status"]
    assert sorted(cfg["real_callers"].values()) == sorted(EIGHT)
    assert all(real_callers.get_adapter(cfg["real_callers"][s["name"]]).provider == s["provider"]
               for s in cfg["sorters"])


# ---------- driver ----------

def run_one(fn, broken):
    try:
        fn(broken)
        return "pass", ""
    except (AssertionError, Refuse) as e:
        return "fail", "%s: %s" % (type(e).__name__, e)
    except Exception as e:  # an unexpected error is a failure, never a skip
        return "error", "%s: %s" % (type(e).__name__, e)


def main(argv):
    names = [n for n, _ in CHECKS]
    if len(set(names)) != len(names):
        print("SELFTEST FAILED: duplicate check names")
        return 1
    if argv[:1] == ["--break-each"]:
        red, bad = 0, []
        for name, fn in CHECKS:
            status, why = run_one(fn, True)
            if status == "fail":
                red += 1
                print("RED   %s  (%s)" % (name, why[:110]))
            else:
                bad.append(name)
                print("%s %s  %s" % ("STILL GREEN" if status == "pass" else "ERROR", name, why[:110]))
        print("BREAK-EACH: %d of %d went red" % (red, len(CHECKS)))
        return 0 if not bad else 1
    target = None
    if argv[:1] == ["--break"]:
        target = argv[1]
        if target not in names:
            print("no check named %s" % target)
            return 2
    failed = 0
    for name, fn in CHECKS:
        status, why = run_one(fn, name == target)
        if status == "pass":
            print("PASS  %s" % name)
        else:
            failed += 1
            print("FAIL  %s  (%s)" % (name, why[:160]))
    if failed:
        print("SELFTEST FAILED: %d of %d checks failed" % (failed, len(CHECKS)))
        return 1
    print("SELFTEST OK (%d checks)" % len(CHECKS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
