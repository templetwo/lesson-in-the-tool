#!/usr/bin/env python3
"""Check the published 001/001b evidence offline, without rewriting the archive.

Python 3.9+, standard library only. Run from any directory. This checks internal
consistency and reproducibility against the archive's own records, not a Git
commit, the truth of a judge, or the time of a freeze. It executes Python from
the target archive; use only an archive whose code you trust.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile

from archive_evidence import verify_evidence

PILOT = "experiments/001-sheet-pilot"
REJUDGE = "experiments/001b-judge-lean"
# Published commitments at main 19a3017. Updating the publication manifest must
# not silently authorize changing an experiment's original freeze record.
FREEZES = {
    PILOT: "03010ac5156d1d80b83632ec448bb9fa3915b2fe2a24834577cedda00692f7b3",
    REJUDGE: "3579866bf9c980706075b91268b915d5b38b0e2186a1b48844c38aa742c047b6",
}
KEY_ORIGINAL = "7e60caaec94f6f00b805b1efb97f16c556740f39489b911044511d98f6aab31f"
KEY_PUBLIC = "33469022d7e1d81546b8785c4bdac2c83d0b61b4331269b97eb674d439b1db50"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def require_archive_name(name, relative):
    require(name not in ("__pycache__", ".DS_Store") and not name.endswith(".pyc"),
            "forbidden archive artifact: %s" % relative)


def local_file(root, relative):
    """Only canonical archive-relative regular files; never follow a symlink."""
    p = PurePosixPath(relative)
    require(relative and not p.is_absolute() and ".." not in p.parts
            and str(p) == relative and "\\" not in relative,
            "unsafe or noncanonical path: %r" % relative)
    target = root
    for part in p.parts:
        require_archive_name(part, relative)
        target = target / part
        require(not target.is_symlink(), "symlink is not an archive file: %s" % relative)
    require(target.is_file(), "missing regular file: %s" % relative)
    return target


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hash(root, relative, expected):
    path = local_file(root, relative)
    require(digest(path) == expected, "SHA-256 mismatch: %s" % relative)
    return path


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "%s: duplicate JSON key %r" % (path.name, key))
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def inventory(root):
    """List every archive file, refusing caches and bytecode rather than hiding them."""
    files = set()
    for base, dirs, names in os.walk(root, followlinks=False):
        current = Path(base)
        dirs[:] = sorted(d for d in dirs if not (current == root and d == ".git"))
        for d in dirs:
            require_archive_name(d, (current / d).relative_to(root).as_posix())
            require(not (current / d).is_symlink(), "symlink directory: %s" % (current / d))
        for name in names:
            if current == root and name in (".git", "MANIFEST.sha256"):
                continue
            relative = (current / name).relative_to(root).as_posix()
            local_file(root, relative)
            files.add(relative)
    return files


def verify_manifest(root):
    entries = {}
    manifest = local_file(root, "MANIFEST.sha256")
    for number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(match is not None, "MANIFEST.sha256: malformed line %d" % number)
        expected, relative = match.groups()
        require(relative not in entries, "manifest duplicate path: %s" % relative)
        check_hash(root, relative, expected)
        entries[relative] = expected
    require(entries, "manifest is empty")
    actual = inventory(root)
    require(set(entries) == actual,
            "manifest coverage mismatch; unlisted=%s; unexpected=%s"
            % (sorted(actual - entries.keys()), sorted(entries.keys() - actual)))
    return ["manifest: %d files, exact coverage and SHA-256 matches" % len(entries)]


def verify_freezes(root):
    frozen = {}
    for experiment, expected in FREEZES.items():
        frozen[experiment] = read_json(check_hash(root, experiment + "/FREEZE.json", expected))
    first = frozen[PILOT]
    for name, record in first["files"].items():
        # The old absolute 'path' fields are provenance, not paths to open.
        relative = ("sheet/SHEET_SHORT_v2.md" if name ==
                    "../2026-11-24_consolidated-sheet/SHEET_SHORT_v2.md"
                    else PILOT + "/" + name)
        path = check_hash(root, relative, record["sha256"])
        require(path.stat().st_size == record["bytes"], "frozen byte count mismatch: " + relative)
    second = frozen[REJUDGE]
    for name, expected in second["files"].items():
        check_hash(root, REJUDGE + "/" + name, expected)
    for label, name in (("packets", "JUDGE_LANE.md"), ("selftest", "JUDGE_LANE_selftest.md")):
        check_hash(root, REJUDGE + "/judge/" + name, second["judge_instructions"][label])
    for name, expected in second["inputs_from_001"].items():
        if name == "runs/house/key.json":
            require(expected == KEY_ORIGINAL, "unknown original house key commitment")
            check_hash(root, PILOT + "/" + name, KEY_PUBLIC)
        else:
            check_hash(root, PILOT + "/" + name, expected)
    masked_hash = second["files"]["work/masked.jsonl"]
    seeds = dict(zip(("u1", "u2", "m", "order"),
                     (int(masked_hash[i:i + 8], 16) for i in range(0, 32, 8))))
    require(second["seeds"] == seeds, "001b seeds do not derive from the masked-file hash")
    order = read_json(local_file(root, REJUDGE + "/work/final/session_order.json"))
    require(order == {"seed": seeds["order"], "order": second["session_order"]},
            "001b session order disagrees with freeze")
    for index, name in enumerate(second["session_order"], 1):
        require(second["judge_folders"]["s%d" % index]["packet_sha256"] ==
                second["files"]["work/final/packets/%s/packet.jsonl" % name],
                "001b judge-folder packet hash mismatch")
    return ["freeze 001: 11 inputs match hashes and byte counts",
            "freeze 001b: 18 inputs and 4 unchanged inputs from 001 match",
            "KNOWN EXCEPTION: 001 house/key.json matches the exact public edition; "
            "original frozen hash differs (001 E6; 001b PUBLIC_EDITION_NOTES)"]


def run(root, relative, *args, expected_code=0):
    script = local_file(root, relative)
    result = subprocess.run([sys.executable, "-B", str(script), *map(str, args)],
                            cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=60)
    require(result.returncode == expected_code,
            "%s: expected exit %d, got %d\n%s" %
            (relative, expected_code, result.returncode,
             (result.stdout + result.stderr).decode("utf-8", errors="replace")[-4000:]))
    return result.stdout


def same_bytes(path, original):
    require(path.read_bytes() == original.read_bytes(), "reproduction differs: %s" % original)


def verify_reproductions(root):
    # -B prevents bytecode writes, not imports from existing .pyc files. Check
    # before running any archived Python, including when called without main().
    inventory(root)
    p, r = root / PILOT, root / REJUDGE
    tasks = p / "tasks/tasks.jsonl"
    checks = [(PILOT + "/tasks/check_items.py", ()),
              (REJUDGE + "/harness/check_mask.py", ("--selftest",)),
              (REJUDGE + "/harness/tally_rejudge.py", ("--selftest",)),
              (REJUDGE + "/harness/make_packets.py", ("--selftest",))]
    for script, args in checks:
        run(root, script, *args)
    with tempfile.TemporaryDirectory(prefix="lesson-archive-") as temp:
        out = Path(temp)
        # The frozen 001 selftest writes beside itself and its conditions file
        # names private absolute paths. Relocate only a temporary copy:
        # published files stay unchanged and old machine paths are never opened.
        staged = out / "selftest"
        for folder in ("harness", "tasks"):
            shutil.copytree(p / folder, staged / PILOT / folder,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        sheet = staged / "sheet/SHEET_SHORT_v2.md"
        sheet.parent.mkdir()
        shutil.copyfile(root / "sheet/SHEET_SHORT_v2.md", sheet)
        conditions_path = staged / PILOT / "harness/conditions.json"
        conditions = read_json(conditions_path)
        conditions["files"]["generic"]["path"] = str(staged / PILOT / "harness/generic_checklist.md")
        conditions["files"]["sheet"]["path"] = str(sheet)
        conditions_path.write_text(json.dumps(conditions), encoding="utf-8")
        run(staged, PILOT + "/harness/selftest.py")
        # Re-score copies, never the published raw/score files.
        for name in ("house", "house_null", "lfm3", "lfm3_null"):
            copied = out / name
            copied.mkdir()
            shutil.copyfile(p / "runs" / name / "raw.ndjson", copied / "raw.ndjson")
            run(root, PILOT + "/harness/score_auto.py", "--tasks", tasks, "--run-dir", copied)
            same_bytes(copied / "auto_scores.ndjson", p / "runs" / name / "auto_scores.ndjson")
        run(root, REJUDGE + "/harness/check_mask.py", "--raw", p / "runs/house/raw.ndjson",
            "--masked", r / "work/masked.jsonl", "--edits", r / "work/mask_edits.json")
        run(root, REJUDGE + "/harness/apply_mask_edits.py", "--raw", p / "runs/house/raw.ndjson",
            "--edits", r / "work/mask_edits.json", "--out", out / "masked.jsonl")
        same_bytes(out / "masked.jsonl", r / "work/masked.jsonl")
        freeze = read_json(r / "FREEZE.json")
        args = ["--tasks", tasks, "--raw", p / "runs/house/raw.ndjson",
                "--masked", r / "work/masked.jsonl", "--out", out / "rebuild"]
        for label in ("u1", "u2", "m", "order"):
            args.extend(("--seed-" + label, freeze["seeds"][label]))
        run(root, REJUDGE + "/harness/make_packets.py", *args)
        for name in ("U1", "U2", "M"):
            for relative in ("packets/%s/packet.jsonl" % name, "keys/%s.json" % name):
                same_bytes(out / "rebuild" / relative, r / "work/final" / relative)
        same_bytes(out / "rebuild/session_order.json", r / "work/final/session_order.json")
        args = []
        for name in ("U1", "U2", "M"):
            score = "U2_id_restored" if name == "U2" else name
            args.extend(("--scores-" + name.lower(), r / ("work/final/scores/%s.jsonl" % score),
                         "--key-" + name.lower(), r / ("work/final/keys/%s.json" % name)))
        args.extend(("--setup-map", r / "work/setup_map.json", "--masked", r / "work/masked.jsonl",
                     "--orig-scores", p / "runs/house/judge_scores.jsonl"))
        tally = run(root, REJUDGE + "/harness/tally_rejudge.py", *args)
        require(tally == (r / "work/final/TALLY.txt").read_bytes(), "001b tally differs from published TALLY.txt")
        args[args.index("--scores-u2") + 1] = r / "work/final/scores/U2.jsonl"
        refused = run(root, REJUDGE + "/harness/tally_rejudge.py", *args, expected_code=2)
        require(b"a72690cc274f06f" in refused and b"not in the U2 key" in refused,
                "001b original U2 was not refused for its documented mistyped ID")
    return ["self-checks: 001 harness/tasks and all three 001b harness selftests passed",
            "reproduced: four auto-score files, masked replies, three packets/keys, "
            "session order and 001b tally byte for byte",
            "negative control: original U2 scores refused for the documented ID error"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="archive root whose Python harnesses will be executed "
                             "(default: this script's repository)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        for check in (verify_manifest, verify_freezes, verify_evidence, verify_reproductions):
            for message in check(root):
                print("OK " + message, flush=True)
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print("FAIL " + str(exc), file=sys.stderr)
        return 1
    print("VERIFIED internal consistency with this archive's manifest and freeze records. "
          "No Git commit comparison; freeze timing and judge correctness are not verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
