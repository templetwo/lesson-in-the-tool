"""A small, local demonstration of a tool carrying a lesson. No model calls."""
import argparse
import json
from pathlib import Path
import tempfile

from .records import save_records


CASES = {
    "true": ("The records landed", "confirmed"),
    "partial": ("Twelve reported, nine saved", "contradicted"),
    "substituted": ("Twelve saved, one value changed", "contradicted"),
    "misdirected": ("The records went somewhere else", "contradicted"),
    "unreadable": ("The readback could not finish", "unresolved"),
    "preexisting": ("The state was already there; this action failed", "confirmed"),
}


def demonstrate(case, workspace):
    """All invented data and deliberate faults stay in a temporary workspace."""
    destination = workspace / (case + ".jsonl")
    records = [{"id": "demo-%02d" % n, "value": n, "demo": True} for n in range(1, 13)]
    writer = reader = None

    def claimed_success(path, data):
        if case == "partial":
            data = b"\n".join(data.splitlines()[:9]) + b"\n"
        elif case == "substituted":
            rows = [json.loads(line) for line in data.splitlines()]
            rows[0]["value"] = -1
            data = ("\n".join(json.dumps(row) for row in rows) + "\n").encode("utf-8")
        elif case == "misdirected":
            path = path.with_name("different-destination.jsonl")
        path.write_bytes(data)
        return {"status": "ok", "records": 12}

    def cannot_read(path):
        raise PermissionError("deliberate demonstration: readback unavailable")

    def failed_action(path, data):
        raise OSError("deliberate demonstration: writer failed before changing anything")

    if case in ("partial", "substituted", "misdirected"):
        writer = claimed_success
    elif case == "unreadable":
        reader = cannot_read
    elif case == "preexisting":
        initial = save_records(destination, records)
        if initial["observation"]["status"] != "confirmed":
            raise ValueError("could not prepare the preexisting-state demonstration")
        writer = failed_action
    receipt = save_records(destination, records, writer=writer, reader=reader)
    expected = CASES[case][1]
    if receipt["observation"]["status"] != expected:
        raise ValueError("%s: expected %s, observed %s" %
                         (case, expected, receipt["observation"]["status"]))
    return {"demonstration": True, "case": case, "title": CASES[case][0], "receipt": receipt}


def render(result):
    receipt = result["receipt"]
    observation = receipt["observation"]
    action = receipt["action"]
    count = observation["record_count"]
    lines = [result["title"], "  Asked: 12 ordered records at the requested destination."]
    if action["error"]:
        lines.append("  Action: " + action["error"])
    else:
        lines.append("  Claimed: " + json.dumps(action["claim"], sort_keys=True))
    lines.append("  Adapters: writer=%s; reader=%s." %
                 (receipt["adapters"]["writer"], receipt["adapters"]["reader"]))
    lines.append("  Readback (%s): %s; %s records observed." %
                 (observation["source"], observation["status"],
                  "unknown" if count is None else count))
    lines.append("  Evidence: " + observation["reason"])
    if observation["content_sha256"]:
        lines.append("  Content SHA-256: " + observation["content_sha256"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["all", *CASES], default="all")
    parser.add_argument("--json", action="store_true", help="print full structured receipts")
    args = parser.parse_args(argv)
    names = list(CASES) if args.case == "all" else [args.case]
    with tempfile.TemporaryDirectory(prefix="lesson-in-the-tool-") as temp:
        results = [demonstrate(name, Path(temp)) for name in names]
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("LESSON 03 — the part that remembers")
            print("Local demonstrations with invented records and deliberate faults.\n")
            print("\n\n".join(render(result) for result in results))
            print("\nThe readback establishes the observed state. Meaning, permission and repair remain open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
