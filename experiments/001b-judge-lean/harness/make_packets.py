#!/usr/bin/env python3
"""Write the three judge packets of experiment 001b: U1, U2 (original replies) and M (masked).

  <out>/packets/U1/packet.jsonl   <out>/packets/U2/packet.jsonl   <out>/packets/M/packet.jsonl
  <out>/keys/U1.json              <out>/keys/U2.json              <out>/keys/M.json
  <out>/session_order.json

Each packet line is exactly {"id", "prompt", "pass_rule", "reply"}, 126 lines, with a fresh
opaque 16-hex id per line and its own seeded shuffle. The ids and the shuffle both come from that
packet's seed, so a packet can be rebuilt byte for byte from its seed and the same inputs. The
key, outside the packet folder, maps each packet id to the original reply id and item id, and
records the seed, the source (original or masked), the input hashes and the packet's sha256.
session_order.json holds the order of the three judge sessions from one seeded shuffle of
["U1", "U2", "M"].

Refuses (exit 2) if: the masked file does not match raw by order, id or original hash; a seed is
repeated; any packet id repeats within or across packets or equals a raw reply id; two packets
come out in the same order; a task is missing for an item.

Nothing written inside a packet folder says which packet it is or which lines were masked, EXCEPT
the folder's own name. Give the judge a copy of packet.jsonl in a neutral folder, never a folder
named U1, U2 or M.

Usage:
  make_packets.py --tasks <tasks.jsonl> --raw <raw.ndjson> --masked <masked.jsonl> --out <dir>
                  --seed-u1 N --seed-u2 N --seed-m N --seed-order N
  make_packets.py --selftest   (made-up replies in a temporary folder)
Python 3.9, standard library only.
"""
import argparse
import contextlib
import hashlib
import io
import tempfile
import json
import os
import random
import sys

NAMES = ["U1", "U2", "M"]


def sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def write_jsonl(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def build_packet(rows, seed, taken):
    """rows: list of (reply_id, item_id, prompt, pass_rule, reply). Returns (packet, key_entries)."""
    rng = random.Random(seed)
    packet, entries = [], {}
    for reply_id, item_id, prompt, pass_rule, reply in rows:
        pid = "%016x" % rng.getrandbits(64)
        while pid in taken:
            pid = "%016x" % rng.getrandbits(64)
        taken.add(pid)
        entries[pid] = {"reply_id": reply_id, "item_id": item_id}
        packet.append({"id": pid, "prompt": prompt, "pass_rule": pass_rule, "reply": reply})
    rng.shuffle(packet)
    return packet, entries


def selftest():
    """Two builds with the same seeds are identical; other seeds give other ids and orders; lines carry
    only the four fields; no id is shared between packets or with raw; U1 and U2 hold the original
    replies and M the masked ones; a repeated seed and a masked file with a wrong hash are refused."""
    results = []

    def note(name, ok):
        results.append(ok)
        print("  %-62s %s" % (name, "ok" if ok else "WRONG"))

    def quiet(argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def read_dir(d):
        out = {}
        for rel in ["packets/U1/packet.jsonl", "packets/U2/packet.jsonl", "packets/M/packet.jsonl",
                    "keys/U1.json", "keys/U2.json", "keys/M.json", "session_order.json"]:
            with open(os.path.join(d, rel), "rb") as fh:
                out[rel] = fh.read()
        return out

    with tempfile.TemporaryDirectory() as td:
        tasks = [{"item_id": "T-%d" % k, "prompt": "prompt %d" % k, "pass_rule": "rule text %d" % k, "family": "F"}
                 for k in range(3)]
        raw, masked = [], []
        for n in range(24):
            rid = "%016x" % (0xABC000 + n)
            reply = "Reply %d. Per Rule %d, I checked it." % (n, n % 5) if n % 3 == 0 else "Reply %d, plain." % n
            mreply = reply.replace(" Per Rule %d," % (n % 5), "") if n % 3 == 0 else reply
            raw.append({"id": rid, "item_id": "T-%d" % (n % 3), "reply": reply, "tokens": 99, "other": "x"})
            masked.append({"id": rid, "item_id": "T-%d" % (n % 3), "reply_original_sha256": sha_text(reply),
                           "reply_masked": mreply, "changed": mreply != reply})
        tp, rp, mp = (os.path.join(td, f) for f in ("tasks.jsonl", "raw.ndjson", "masked.jsonl"))
        write_jsonl(tp, tasks)
        write_jsonl(rp, raw)
        write_jsonl(mp, masked)
        base = ["--tasks", tp, "--raw", rp, "--masked", mp]
        da, db, dc = (os.path.join(td, x) for x in ("a", "b", "c"))
        ca = quiet(base + ["--out", da, "--seed-u1", "11", "--seed-u2", "12", "--seed-m", "13", "--seed-order", "5"])[0]
        cb = quiet(base + ["--out", db, "--seed-u1", "11", "--seed-u2", "12", "--seed-m", "13", "--seed-order", "5"])[0]
        cc = quiet(base + ["--out", dc, "--seed-u1", "21", "--seed-u2", "22", "--seed-m", "23", "--seed-order", "6"])[0]
        note("three builds run", ca == cb == cc == 0)
        fa, fb = read_dir(da), read_dir(db)
        note("same seeds: every packet, key and the session order byte-identical", fa == fb)

        def lines(d, name):
            return load_jsonl(os.path.join(d, "packets", name, "packet.jsonl"))

        def key(d, name):
            with open(os.path.join(d, "keys", name + ".json"), encoding="utf-8") as fh:
                return json.load(fh)

        ok_ids, ok_order = True, True
        for name in NAMES:
            ia = [x["id"] for x in lines(da, name)]
            ic = [x["id"] for x in lines(dc, name)]
            if set(ia) & set(ic):
                ok_ids = False
            oa = [key(da, name)["entries"][i]["reply_id"] for i in ia]
            oc = [key(dc, name)["entries"][i]["reply_id"] for i in ic]
            if oa == oc:
                ok_order = False
        note("different seeds: different ids for every packet", ok_ids)
        note("different seeds: a different order for every packet", ok_order)
        four = all(set(x.keys()) == {"id", "prompt", "pass_rule", "reply"} and list(x.keys()) == ["id", "prompt", "pass_rule", "reply"]
                   for name in NAMES for x in lines(da, name))
        note("every packet line holds exactly id, prompt, pass_rule, reply", four)
        allid = [x["id"] for name in NAMES for x in lines(da, name)]
        note("no id shared between packets or with a raw reply id",
             len(allid) == len(set(allid)) == 72 and not (set(allid) & set(r["id"] for r in raw)))
        orig_by = dict((r["id"], r["reply"]) for r in raw)
        mask_by = dict((m["id"], m["reply_masked"]) for m in masked)

        def texts_ok(name, want):
            k = key(da, name)["entries"]
            got = lines(da, name)
            return (len(got) == len(want) and set(k[x["id"]]["reply_id"] for x in got) == set(want)
                    and all(x["reply"] == want[k[x["id"]]["reply_id"]] for x in got))
        note("U1 and U2 hold every original reply, M every masked reply",
             texts_ok("U1", orig_by) and texts_ok("U2", orig_by) and texts_ok("M", mask_by)
             and sorted(x["reply"] for x in lines(da, "U1")) == sorted(x["reply"] for x in lines(da, "U2"))
             and sorted(x["reply"] for x in lines(da, "M")) != sorted(x["reply"] for x in lines(da, "U1")))
        code = quiet(base + ["--out", os.path.join(td, "d"), "--seed-u1", "1", "--seed-u2", "1", "--seed-m", "3", "--seed-order", "1"])[0]
        note("a repeated seed is refused", code == 2)
        bad = list(masked)
        bad[0] = dict(bad[0], reply_original_sha256="0" * 64)
        write_jsonl(mp, bad)
        code = quiet(base + ["--out", os.path.join(td, "e"), "--seed-u1", "1", "--seed-u2", "2", "--seed-m", "3", "--seed-order", "1"])[0]
        note("a masked file whose original hash is wrong is refused", code == 2)
    good = all(results)
    print("SELFTEST %s (%d of %d checks as expected)" % ("OK" if good else "FAILED", sum(results), len(results)))
    return 0 if good else 1


def main(argv=None):
    if argv is None and sys.argv[1:] == ["--selftest"]:
        return selftest()
    ap = argparse.ArgumentParser(description="Write the U1, U2 and M judge packets.")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--masked", required=True)
    ap.add_argument("--out", required=True, help="folder that gets packets/, keys/ and session_order.json")
    ap.add_argument("--seed-u1", type=int, required=True)
    ap.add_argument("--seed-u2", type=int, required=True)
    ap.add_argument("--seed-m", type=int, required=True)
    ap.add_argument("--seed-order", type=int, required=True)
    a = ap.parse_args(argv)

    seeds = {"U1": a.seed_u1, "U2": a.seed_u2, "M": a.seed_m}
    if len(set(seeds.values())) != 3:
        print("REFUSED: the three packet seeds must differ")
        return 2

    tasks = dict((t["item_id"], t) for t in load_jsonl(a.tasks))
    raw = [{"id": r.get("id"), "item_id": r.get("item_id"), "reply": r.get("reply")} for r in load_jsonl(a.raw)]
    masked = load_jsonl(a.masked)
    if len(raw) != len(masked):
        print("REFUSED: raw has %d replies, masked has %d" % (len(raw), len(masked)))
        return 2
    raw_ids = set()
    for n, (r, m) in enumerate(zip(raw, masked)):
        if r["id"] != m.get("id") or r["item_id"] != m.get("item_id"):
            print("REFUSED: line %d: masked id/item_id do not match raw" % (n + 1))
            return 2
        if not isinstance(r["reply"], str) or m.get("reply_original_sha256") != sha_text(r["reply"]):
            print("REFUSED: line %d (%s): original hash does not match raw" % (n + 1, r["id"]))
            return 2
        t = tasks.get(r["item_id"])
        if t is None or not t.get("prompt") or not t.get("pass_rule"):
            print("REFUSED: no prompt/pass_rule for item %r" % r["item_id"])
            return 2
        if r["id"] in raw_ids:
            print("REFUSED: raw reply id %s appears twice" % r["id"])
            return 2
        raw_ids.add(r["id"])

    sources = {
        "U1": ("original", [(r["id"], r["item_id"], tasks[r["item_id"]]["prompt"], tasks[r["item_id"]]["pass_rule"], r["reply"]) for r in raw]),
        "U2": ("original", [(r["id"], r["item_id"], tasks[r["item_id"]]["prompt"], tasks[r["item_id"]]["pass_rule"], r["reply"]) for r in raw]),
        "M": ("masked", [(m["id"], m["item_id"], tasks[m["item_id"]]["prompt"], tasks[m["item_id"]]["pass_rule"], m["reply_masked"]) for m in masked]),
    }

    taken = set(raw_ids)  # a packet id may never equal a raw reply id
    built = {}
    for name in NAMES:
        src, rows = sources[name]
        packet, entries = build_packet(rows, seeds[name], taken)
        built[name] = (src, packet, entries)

    orders = dict((name, [built[name][2][line["id"]]["reply_id"] for line in built[name][1]]) for name in NAMES)
    for i in range(3):
        for j in range(i + 1, 3):
            if orders[NAMES[i]] == orders[NAMES[j]]:
                print("REFUSED: packets %s and %s came out in the same order" % (NAMES[i], NAMES[j]))
                return 2
    all_ids = [pid for name in NAMES for pid in built[name][2]]
    if len(all_ids) != len(set(all_ids)) or set(all_ids) & raw_ids:
        print("REFUSED: packet ids are not unique across packets and raw")
        return 2

    inputs = {"tasks_sha256": sha_file(a.tasks), "raw_sha256": sha_file(a.raw), "masked_sha256": sha_file(a.masked)}
    for name in NAMES:
        src, packet, entries = built[name]
        pdir = os.path.join(a.out, "packets", name)
        os.makedirs(pdir, exist_ok=True)
        ppath = os.path.join(pdir, "packet.jsonl")
        write_jsonl(ppath, packet)
        os.makedirs(os.path.join(a.out, "keys"), exist_ok=True)
        key = {"packet": name, "seed": seeds[name], "source": src, "lines": len(packet),
               "packet_sha256": sha_file(ppath), "inputs": inputs, "entries": entries}
        write_json(os.path.join(a.out, "keys", name + ".json"), key)
        print("wrote %s: %d lines, source %s, seed %d, sha256 %s" % (ppath, len(packet), src, seeds[name], key["packet_sha256"]))

    order = list(NAMES)
    random.Random(a.seed_order).shuffle(order)
    write_json(os.path.join(a.out, "session_order.json"), {"seed": a.seed_order, "order": order})
    print("session order (seed %d): %s" % (a.seed_order, " -> ".join(order)))
    print("Give each judge a COPY of one packet.jsonl in a neutral folder. Never the keys, never a folder named U1, U2 or M.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
