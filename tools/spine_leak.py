#!/usr/bin/env python3
"""D9. A domain that wears another domain's vocabulary is one workflow with a noun slot.

Usage: spine_leak.py <descriptor.json> [more.json ...] [--prose DIR]
Every descriptor declares distinctive_nouns. This refuses any descriptor (or, with
--prose, any file in DIR) that uses another domain's distinctive noun.
"""
import json, os, re, sys


def words(text):
    return set(re.findall(r"[a-z][a-z0-9_-]{2,}", text.lower()))


def main():
    argv = sys.argv[1:]
    prose = None
    if "--prose" in argv:
        i = argv.index("--prose")
        prose = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if not argv:
        print("spine_leak: no descriptors given", file=sys.stderr)
        return 3
    ds = {}
    for p in argv:
        if not os.path.exists(p):
            print(f"spine_leak: cannot judge — {os.path.abspath(p)} absent", file=sys.stderr)
            return 3
        d = json.load(open(p))
        ds[d["id"]] = d
    bad = 0
    for did, d in ds.items():
        mine = {n.lower() for n in d.get("distinctive_nouns", [])}
        foreign = {}
        for oid, o in ds.items():
            if oid == did:
                continue
            for n in o.get("distinctive_nouns", []):
                if n.lower() not in mine:
                    foreign[n.lower()] = oid
        text = json.dumps(d).lower()
        for n, owner in foreign.items():
            if re.search(r"\b" + re.escape(n) + r"\b", text):
                print(f"LEAK {did}: uses '{n}', which belongs to {owner}")
                bad = 1
        if prose:
            for dp, _, fns in os.walk(prose):
                if ".git" in dp:
                    continue
                for fn in fns:
                    if not fn.endswith((".md", ".pni", ".json")):
                        continue
                    t = open(os.path.join(dp, fn), errors="replace").read().lower()
                    for n, owner in foreign.items():
                        if re.search(r"\b" + re.escape(n) + r"\b", t):
                            print(f"LEAK {os.path.relpath(os.path.join(dp, fn), prose)}: "
                                  f"'{n}' belongs to {owner}")
                            bad = 1
    if not bad:
        print(f"OK no cross-domain vocabulary leak across {len(ds)} descriptor(s)")
    return bad


if __name__ == "__main__":
    sys.exit(main())
