"""Homes file loader. homes.json is a JSON list of {"name": ..., "definition": ...}.

Refuses: not a list; fewer than two homes; an entry that is not exactly those two string keys; an empty name or
definition; a duplicate name (compared without case); a duplicate definition; the reserved names DRYRUN and none
(version 2: "none" means "no second home" in the reply); a name with "|", ",", a final ":", a line break or
surrounding spaces (the reply format could not carry it unmistakably); a definition with a line break.
It does not try to count sentences in a definition. That is left to the person who writes the definitions.
"""
from common import Refuse, DRYRUN, load_json, sha256_file


def load_homes(path):
    obj = load_json(path, "homes file")
    if not isinstance(obj, list):
        raise Refuse("homes file must be a JSON list")
    if len(obj) < 2:
        raise Refuse("homes file has %d home(s); at least two are needed" % len(obj))
    names, defs, out = set(), set(), []
    for i, h in enumerate(obj):
        if not isinstance(h, dict) or set(h) != {"name", "definition"}:
            raise Refuse("home %d must have exactly the keys name and definition" % i)
        name, d = h["name"], h["definition"]
        if not isinstance(name, str) or not isinstance(d, str):
            raise Refuse("home %d: name and definition must be strings" % i)
        if name.strip() == "":
            raise Refuse("home %d has an empty name" % i)
        if name != name.strip() or any(ch in name for ch in "|,\n\r") or name.endswith(":"):
            raise Refuse("home %d name %r has surrounding spaces, a '|', a ',', a final ':' or a line break"
                         % (i, name))
        if name.upper() == DRYRUN:
            raise Refuse("home name DRYRUN is reserved for dry runs")
        if name.casefold() == "none":
            raise Refuse("home name 'none' is reserved: the reply format uses it for 'no second home'")
        if d.strip() == "":
            raise Refuse("home %r has an empty definition" % name)
        if "\n" in d or "\r" in d:
            raise Refuse("home %r definition has a line break" % name)
        if name.casefold() in names:
            raise Refuse("duplicate home name %r" % name)
        if d.strip().casefold() in defs:
            raise Refuse("home %r repeats another home's definition" % name)
        names.add(name.casefold())
        defs.add(d.strip().casefold())
        out.append({"name": name, "definition": d})
    return out, sha256_file(path)
