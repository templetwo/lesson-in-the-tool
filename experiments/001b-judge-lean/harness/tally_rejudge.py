#!/usr/bin/env python3
"""Tally experiment 001b: the judge's repeat noise, the lean, the paired flips and the gains.

Inputs:
  --scores-u1/--scores-u2/--scores-m  judge answers, one line each: {"id": <packet id>, "pass": true|false}
  --key-u1/--key-u2/--key-m           the keys written by make_packets.py
  --setup-map                         {"<reply id>": "C0"|"C1"|"C2"} for all replies (HQ supplies it)
  --masked                            work/masked.jsonl (for which replies changed under masking)
  --orig-scores (optional)            001's original verdicts, {"id": <reply id>, "pass": ...} per line;
                                      shown beside, never used in any number below

Refuses (exit 2) if any score id is missing, doubled or unknown, if a 'pass' is not true/false, if a
key does not cover every reply exactly once, if a reply has no setup, or if a key was built from a
masked file whose sha256 differs from the --masked file given here.

Numbers, as the rules (PREREG_001b) define them:
  P(c, X)   passes for setup c in packet X
  N(c)      |P(c,U1) - P(c,U2)|;  N = the largest of the three
  D         replies with different verdicts in U1 and U2
  L(c)      P(c,M) - mean(P(c,U1), P(c,U2)); C1 and C2 are the lean, C0 is the control
  flips     among replies whose text changed: passed in both U and failed in M; failed in both U
            and passed in M; judged differently in U1 and U2
  G(c)      P(c) - P(C0), under U (means) and under M
  T         the larger of N and 1
Boundary, as the rules define it: "within T" means |L| <= T; "below -T" means L < -T; "above +T"
means L > +T. The control fails only if |L(C0)| > T; a gain is "above T" only if G > T.
The decision lines are printed word for word from the rules. If the control fails, that line is
printed first and every number is still printed.

Usage:
  tally_rejudge.py --scores-u1 F --scores-u2 F --scores-m F --key-u1 F --key-u2 F --key-m F
                   --setup-map F --masked F [--orig-scores F]
  tally_rejudge.py --selftest
Python 3.9, standard library only.
"""
import argparse
import hashlib
import json
import os
import random
import sys
import tempfile

SETUPS = ["C0", "C1", "C2"]
PACKETS = ["U1", "U2", "M"]

# Word for word from PREREG_001b_DRAFT.md, "The decision rules, fixed now" (Markdown bold marks
# dropped), as the draft read at 2026-11-24 21:0x EST.
RULE_T = "Let T = the larger of N and 1."
RULE_WITHIN = ("\"Within T\" means the absolute value is T or less. \"Below -T\" and \"above +T\" mean strictly "
               "beyond it.")
RULE_NO_LEAN = ("No lean shown: L(C1) and L(C2) both lie within T of zero. Then 001's judge numbers stand as "
                "reported, by this judge, and the errata's caution is answered for this model.")
RULE_LEAN = ("A lean is shown for a setup: its L is below -T. Then 001's gain for that setup was raised by about "
             "that many tasks, by this judge, and the reports get an erratum saying so with the number.")
RULE_REVERSE = "A reverse lean: L above +T. Mentions cost passes; reported the same way."
RULE_CONTROL = "If the control L(C0) lies outside T, the measurement is not trusted and is reported as failed."
RULE_GAIN = ("The gain is reported under U and under M. \"A checklist helped the larger model\" is kept only if "
             "G under M is still above T for that setup.")
RULE_SHEET = ("Sheet against generic: P(C2) - P(C1) is reported under U and under M and is not a claim either way.")


class Refuse(Exception):
    pass


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError:
                    raise Refuse("%s line %d is not JSON" % (path, n))
    return out


def load_scores(path, key_entries, label):
    rows = load_jsonl(path)
    seen = {}
    for r in rows:
        pid = r.get("id")
        if pid not in key_entries:
            raise Refuse("%s: id %r is not in the %s key" % (label, pid, label))
        if pid in seen:
            raise Refuse("%s: id %s is doubled" % (label, pid))
        if not isinstance(r.get("pass"), bool):
            raise Refuse("%s: id %s has pass=%r, not true/false" % (label, pid, r.get("pass")))
        seen[pid] = r["pass"]
    missing = sorted(set(key_entries) - set(seen))
    if missing:
        raise Refuse("%s: %d ids missing, first %s" % (label, len(missing), missing[0]))
    return dict((key_entries[pid]["reply_id"], v) for pid, v in seen.items())


def load_key(path, label, masked_sha):
    with open(path, encoding="utf-8") as fh:
        key = json.load(fh)
    got = (key.get("inputs") or {}).get("masked_sha256")
    if got != masked_sha:
        raise Refuse("%s key was built from masked file sha256 %s, but --masked has %s" % (label, got, masked_sha))
    entries = key.get("entries")
    if not isinstance(entries, dict) or not entries:
        raise Refuse("%s key has no entries" % label)
    reply_ids = [e.get("reply_id") for e in entries.values()]
    if len(reply_ids) != len(set(reply_ids)):
        raise Refuse("%s key maps two packet ids to one reply" % label)
    return entries, set(reply_ids)


def fmt(x):
    return ("%d" % x) if float(x).is_integer() else ("%.1f" % x)


def tally(verdicts, setup_of, changed, orig=None, out=print):
    """verdicts: {packet: {reply_id: bool}}. Returns a dict of the numbers (for the selftest)."""
    ids = sorted(setup_of)
    by_setup = dict((c, [i for i in ids if setup_of[i] == c]) for c in SETUPS)
    P = dict(((c, X), sum(1 for i in by_setup[c] if verdicts[X][i])) for c in SETUPS for X in PACKETS)
    Nc = dict((c, abs(P[(c, "U1")] - P[(c, "U2")])) for c in SETUPS)
    N = max(Nc.values())
    D = sum(1 for i in ids if verdicts["U1"][i] != verdicts["U2"][i])
    Umean = dict((c, (P[(c, "U1")] + P[(c, "U2")]) / 2.0) for c in SETUPS)
    L = dict((c, P[(c, "M")] - Umean[c]) for c in SETUPS)
    T = max(N, 1)
    GU = dict((c, Umean[c] - Umean["C0"]) for c in ("C1", "C2"))
    GM = dict((c, P[(c, "M")] - P[("C0", "M")]) for c in ("C1", "C2"))

    out("REPLIES: %d; per setup: %s" % (len(ids), ", ".join("%s %d" % (c, len(by_setup[c])) for c in SETUPS)))
    out("CHANGED UNDER MASKING per setup: %s (total %d)"
        % (", ".join("%s %d" % (c, sum(1 for i in by_setup[c] if changed[i])) for c in SETUPS), sum(changed.values())))
    out("")
    out("P(c, X), passes:")
    out("  setup    U1    U2     M" + ("   001 (shown, not used)" if orig else ""))
    for c in SETUPS:
        line = "  %-5s %5d %5d %5d" % (c, P[(c, "U1")], P[(c, "U2")], P[(c, "M")])
        if orig:
            line += "   %5d" % sum(1 for i in by_setup[c] if orig.get(i))
        out(line)
    out("")
    out("Judge repeat noise: N(C0)=%d  N(C1)=%d  N(C2)=%d  N=%d" % (Nc["C0"], Nc["C1"], Nc["C2"], N))
    out("D (replies judged differently in U1 and U2): %d of %d" % (D, len(ids)))
    out("T = max(N, 1) = %d" % T)
    out("")
    out("Lean L(c) = P(c,M) - mean(P(c,U1), P(c,U2)):  L(C1)=%s  L(C2)=%s  control L(C0)=%s"
        % (fmt(L["C1"]), fmt(L["C2"]), fmt(L["C0"])))
    out("")
    out("Paired flips among the %d changed replies:" % sum(changed.values()))
    flips = {}
    for c in SETUPS + ["all"]:
        pool = [i for i in ids if changed[i] and (c == "all" or setup_of[i] == c)]
        pf = sum(1 for i in pool if verdicts["U1"][i] and verdicts["U2"][i] and not verdicts["M"][i])
        fp = sum(1 for i in pool if not verdicts["U1"][i] and not verdicts["U2"][i] and verdicts["M"][i])
        un = sum(1 for i in pool if verdicts["U1"][i] != verdicts["U2"][i])
        flips[c] = (pf, fp, un)
        out("  %-4s changed %3d | passed both U, failed M: %d | failed both U, passed M: %d | U1 and U2 differ: %d"
            % (c, len(pool), pf, fp, un))
    out("")
    out("Gain G(c) = P(c) - P(C0):  under U (means): G(C1)=%s G(C2)=%s   under M: G(C1)=%s G(C2)=%s"
        % (fmt(GU["C1"]), fmt(GU["C2"]), fmt(GM["C1"]), fmt(GM["C2"])))
    out("Sheet against generic P(C2)-P(C1):  under U (means) %s   under M %s   (not a claim either way)"
        % (fmt(Umean["C2"] - Umean["C1"]), fmt(P[("C2", "M")] - P[("C1", "M")])))
    out("")
    out("DECISION (lines quoted word for word from the rules):")
    control_failed = abs(L["C0"]) > T
    if control_failed:
        out("  MEASUREMENT FAILED. L(C0)=%s lies outside T=%d." % (fmt(L["C0"]), T))
        out("  > " + RULE_CONTROL)
        out("  The lines below are printed for the record only; they do not stand while the control fails.")
    out("  > " + RULE_T)
    out("  > " + RULE_WITHIN)
    if not control_failed:
        out("  Control: L(C0)=%s lies within T=%d." % (fmt(L["C0"]), T))
    lean = []
    for c in ("C1", "C2"):
        if L[c] < -T:
            lean.append((c, "lean"))
        elif L[c] > T:
            lean.append((c, "reverse"))
    if not lean:
        out("  > " + RULE_NO_LEAN)
    for c, kind in lean:
        out("  %s: L=%s" % (c, fmt(L[c])))
        out("  > " + (RULE_LEAN if kind == "lean" else RULE_REVERSE))
    out("  > " + RULE_GAIN)
    for c in ("C1", "C2"):
        kept = GM[c] > T
        out("  %s: G under M = %s, T = %d: \"A checklist helped the larger model\" is %s for %s."
            % (c, fmt(GM[c]), T, "KEPT" if kept else "NOT KEPT", c))
    out("  > " + RULE_SHEET)
    return {"P": P, "N": N, "Nc": Nc, "D": D, "L": L, "T": T, "GU": GU, "GM": GM, "flips": flips,
            "control_failed": control_failed, "lean": lean}


def run(a, out=print):
    with open(a.setup_map, encoding="utf-8") as fh:
        setup_of = json.load(fh)
    if not isinstance(setup_of, dict) or not setup_of:
        raise Refuse("setup map is empty or not an object")
    bad = dict((k, v) for k, v in setup_of.items() if v not in SETUPS)
    if bad:
        raise Refuse("setup map has values other than C0/C1/C2: %s" % sorted(bad.items())[:3])
    with open(a.masked, "rb") as fh:
        masked_sha = hashlib.sha256(fh.read()).hexdigest()
    masked = load_jsonl(a.masked)
    changed = {}
    for m in masked:
        if m.get("id") in changed:
            raise Refuse("masked file has id %s twice" % m.get("id"))
        changed[m.get("id")] = bool(m.get("changed"))
    all_ids = set(setup_of)
    if set(changed) != all_ids:
        raise Refuse("masked file and setup map do not hold the same reply ids")
    verdicts = {}
    for X, kp, sp in (("U1", a.key_u1, a.scores_u1), ("U2", a.key_u2, a.scores_u2), ("M", a.key_m, a.scores_m)):
        entries, reply_ids = load_key(kp, X, masked_sha)
        if reply_ids != all_ids:
            raise Refuse("%s key does not cover exactly the replies in the setup map" % X)
        verdicts[X] = load_scores(sp, entries, X)
    orig = None
    if a.orig_scores:
        orig = {}
        for r in load_jsonl(a.orig_scores):
            orig[r.get("id")] = r.get("pass") is True
    return tally(verdicts, setup_of, changed, orig=orig, out=out)


def selftest():
    results = []

    def note(name, ok):
        results.append(ok)
        print("  %-66s %s" % (name, "ok" if ok else "WRONG"))

    rng = random.Random(7)
    ids = ["%016x" % rng.getrandbits(64) for _ in range(126)]
    setup_of = dict((ids[i], SETUPS[i // 42]) for i in range(126))
    by_setup = dict((c, [i for i in ids if setup_of[i] == c]) for c in SETUPS)
    # Changed under masking: 10 in C1, 20 in C2, 0 in C0.
    changed = dict((i, False) for i in ids)
    for i in by_setup["C1"][:10] + by_setup["C2"][:20]:
        changed[i] = True

    def scenario(control_shift, c2_drop=4):
        """Known design. U1: C0 30, C1 36, C2 38 passes. U2: one C1 reply flipped to fail (noise 1).
        M: C2 loses 4 changed replies that passed in both U; C1 unchanged from U1; C0 shifted."""
        v = {"U1": {}, "U2": {}, "M": {}}
        base = {"C0": 30, "C1": 36, "C2": 38}
        for c in SETUPS:
            for k, i in enumerate(by_setup[c]):
                # changed replies come first in each list, so make passes land on them for C2
                v["U1"][i] = k < base[c]
        v["U2"] = dict(v["U1"])
        v["U2"][by_setup["C1"][35]] = False          # one disagreement: N(C1) = 1, D = 1
        v["M"] = dict(v["U1"])
        for i in by_setup["C2"][:c2_drop]:            # changed C2 replies that passed in both U now fail
            v["M"][i] = False
        for k in range(control_shift):                # move the control
            v["M"][by_setup["C0"][30 + k]] = True
        return v

    with tempfile.TemporaryDirectory() as td:
        def write_case(v, mutate=None, wrong_masked=False):
            with open(os.path.join(td, "masked.jsonl"), "w") as fh:
                for i in ids:
                    fh.write(json.dumps({"id": i, "changed": changed[i]}) + "\n")
            with open(os.path.join(td, "masked.jsonl"), "rb") as fh:
                mh = hashlib.sha256(fh.read()).hexdigest()
            if wrong_masked:
                mh = "0" * 64
            keys = {}
            for X in PACKETS:
                entries = {}
                for n, i in enumerate(ids):
                    entries["%s%013x" % ({"U1": "a01", "U2": "a02", "M": "a03"}[X], n)] = {"reply_id": i, "item_id": "X"}
                keys[X] = entries
                with open(os.path.join(td, X + ".key.json"), "w") as fh:
                    json.dump({"entries": entries, "inputs": {"masked_sha256": mh}}, fh)
                rows = [{"id": pid, "pass": v[X][e["reply_id"]]} for pid, e in entries.items()]
                if mutate and mutate[0] == X:
                    rows = mutate[1](rows)
                with open(os.path.join(td, X + ".scores.jsonl"), "w") as fh:
                    for r in rows:
                        fh.write(json.dumps(r) + "\n")
            with open(os.path.join(td, "setup.json"), "w") as fh:
                json.dump(setup_of, fh)
            return argparse.Namespace(
                scores_u1=os.path.join(td, "U1.scores.jsonl"), scores_u2=os.path.join(td, "U2.scores.jsonl"),
                scores_m=os.path.join(td, "M.scores.jsonl"), key_u1=os.path.join(td, "U1.key.json"),
                key_u2=os.path.join(td, "U2.key.json"), key_m=os.path.join(td, "M.key.json"),
                setup_map=os.path.join(td, "setup.json"), masked=os.path.join(td, "masked.jsonl"), orig_scores=None)

        # Case 1: known lean in C2, noise 1, control in place.
        lines = []
        r = run(write_case(scenario(0)), out=lines.append)
        text = "\n".join(lines)
        note("case 1: P(C2,M)=34, P(C2,U1)=P(C2,U2)=38", r["P"][("C2", "M")] == 34 and r["P"][("C2", "U1")] == 38 and r["P"][("C2", "U2")] == 38)
        note("case 1: noise N(C1)=1, N=1, D=1, T=1", r["Nc"]["C1"] == 1 and r["N"] == 1 and r["D"] == 1 and r["T"] == 1)
        note("case 1: L(C2)=-4, L(C1)=+0.5, L(C0)=0", r["L"]["C2"] == -4 and r["L"]["C1"] == 0.5 and r["L"]["C0"] == 0)
        note("case 1: flips C2: 4 passed both U and failed M, 0 back, 0 split", r["flips"]["C2"] == (4, 0, 0))
        note("case 1: G under U C2=8, under M C2=4; C1 5.5 and 6", r["GU"]["C2"] == 8 and r["GM"]["C2"] == 4 and r["GU"]["C1"] == 5.5 and r["GM"]["C1"] == 6)
        note("case 1: decision is a lean for C2 only, control not failed",
             r["lean"] == [("C2", "lean")] and not r["control_failed"] and RULE_LEAN in text and RULE_NO_LEAN not in text)
        # Case 2: control moved by 3 (outside T=1): measurement must be reported failed.
        lines = []
        r = run(write_case(scenario(3)), out=lines.append)
        text = "\n".join(lines)
        dec = text.split("DECISION")[1]
        note("case 2: control L(C0)=3 outside T: reported as failed, failed line first",
             r["control_failed"] and "MEASUREMENT FAILED" in dec.splitlines()[1] and RULE_CONTROL in text)
        # Case 2b: exactly on the boundary. L(C2) = -1 = -T and control L(C0) = +1 = +T: both are
        # "within T", so no lean and the control holds.
        lines = []
        r = run(write_case(scenario(1, c2_drop=1)), out=lines.append)
        text = "\n".join(lines)
        note("case 2b: on the boundary, L(C2)=-1, L(C0)=+1, T=1",
             r["L"]["C2"] == -1 and r["L"]["C0"] == 1 and r["T"] == 1)
        note("case 2b: on the boundary counts as within: no lean, control holds",
             r["lean"] == [] and not r["control_failed"] and RULE_NO_LEAN in text and "MEASUREMENT FAILED" not in text)
        # Case 3: no lean at all.
        v = scenario(0)
        v["M"] = dict(v["U1"])
        lines = []
        r = run(write_case(v), out=lines.append)
        note("case 3: no change under M: the no-lean line", r["lean"] == [] and RULE_NO_LEAN in "\n".join(lines))
        # Case 4: a missing id must refuse.
        try:
            run(write_case(scenario(0), mutate=("M", lambda rows: rows[1:])), out=lambda s: None)
            note("case 4: missing id refuses", False)
        except Refuse:
            note("case 4: missing id refuses", True)
        # Case 4b: keys built from a different masked file must refuse.
        try:
            run(write_case(scenario(0), wrong_masked=True), out=lambda s: None)
            note("case 4b: keys built from another masked file refuse", False)
        except Refuse:
            note("case 4b: keys built from another masked file refuse", True)
        # Case 5: a doubled id must refuse.
        try:
            run(write_case(scenario(0), mutate=("U2", lambda rows: rows + rows[:1])), out=lambda s: None)
            note("case 5: doubled id refuses", False)
        except Refuse:
            note("case 5: doubled id refuses", True)
        # Case 6: a pass that is not true/false must refuse.
        def stringy(rows):
            rows[0] = {"id": rows[0]["id"], "pass": "yes"}
            return rows
        try:
            run(write_case(scenario(0), mutate=("U1", stringy)), out=lambda s: None)
            note("case 6: pass='yes' refuses", False)
        except Refuse:
            note("case 6: pass='yes' refuses", True)
    good = all(results)
    print("SELFTEST %s (%d of %d checks as expected)" % ("OK" if good else "FAILED", sum(results), len(results)))
    return 0 if good else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tally experiment 001b.")
    for n in ("scores-u1", "scores-u2", "scores-m", "key-u1", "key-u2", "key-m", "setup-map", "masked", "orig-scores"):
        ap.add_argument("--" + n)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    need = ("scores_u1", "scores_u2", "scores_m", "key_u1", "key_u2", "key_m", "setup_map", "masked")
    missing = [n for n in need if not getattr(a, n)]
    if missing:
        print("missing arguments: %s" % ", ".join("--" + m.replace("_", "-") for m in missing))
        return 2
    try:
        run(a)
    except (Refuse, OSError, ValueError) as exc:
        print("REFUSED: %s" % exc)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
