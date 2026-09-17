#!/usr/bin/env python3
"""Judge a domain descriptor (and optionally its repo) against the ten invariants.

Usage: spine_validate.py <descriptor.json> [--repo DIR]
Exit 0 conformant, 1 non-conformant, 3 cannot judge (and says why, and where it looked).
"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.units import valid as _unit_valid, why as _unit_why

REQUIRED_PORTS = {"mock", "template"}
STATES = {"built", "wired_unproven", "not_built"}
NOT_ESTABLISHED = "not established"


def fail(rs, inv, msg):
    rs.append((inv, msg))


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print("spine_validate: no descriptor given", file=sys.stderr)
        return 3
    path = args[0]
    repo = None
    if "--repo" in args:
        repo = args[args.index("--repo") + 1]
    if not os.path.exists(path):
        print(f"spine_validate: cannot judge — no descriptor at {os.path.abspath(path)}",
              file=sys.stderr)
        return 3
    d = json.load(open(path))
    bad = []

    if repo:
        own = os.path.join(repo, "descriptor.json")
        if os.path.exists(own):
            here = json.load(open(own)).get("id")
            if here != d["id"]:
                print(f"spine_validate: refusing to judge '{d['id']}' against the repo at "
                      f"{os.path.abspath(repo)}, which declares itself '{here}'. "
                      "A descriptor judged against another domain's tree reports nonsense "
                      "confidently.", file=sys.stderr)
                return 3
        elif not os.path.exists(os.path.join(repo, d["interface"])):
            print(f"spine_validate: the repo at {os.path.abspath(repo)} carries no "
                  f"descriptor.json and no {d['interface']}. It is not this domain's tree, "
                  "so D1, D2 and D7 are NOT judged.", file=sys.stderr)
            repo = None

    for k in ("id", "interface", "registry", "ports", "conformance", "verbs",
              "attachment_points", "state", "correlates"):
        if k not in d:
            fail(bad, "D0", f"descriptor has no '{k}'")
    if bad:
        for i, m in bad:
            print(f"FAIL {i}: {m}")
        return 1

    # D3
    missing = REQUIRED_PORTS - set(d["ports"])
    if missing:
        fail(bad, "D3", f"ports missing {sorted(missing)}")

    # D4
    for c in d["conformance"]:
        crit = str(c.get("criterion", "")).strip()
        unit = str(c.get("unit", "")).strip()
        if crit == NOT_ESTABLISHED:
            continue
        if not crit or not unit:
            fail(bad, "D4", f"condition {c.get('id')} has no measurable criterion; "
                            f"write '{NOT_ESTABLISHED}' rather than inventing one")
            continue
        code = c.get("unit_ucum")
        if code is None:
            fail(bad, "D4", f"condition {c.get('id')} carries a prose unit '{unit}' and no "
                            "unit_ucum. A unit a machine cannot read is not a unit.")
        elif not _unit_valid(code):
            fail(bad, "D4", f"condition {c.get('id')}: {_unit_why(code)}")

    # D7
    if repo:
        rp = os.path.join(repo, "roadmap", "packages.json")
        alt = [q for q in (os.path.join(repo, "packets.json"),
                           os.path.join(repo, "docs", "packets.md"),
                           os.path.join(repo, "src", d["id"], "dispatch.py"))
               if os.path.exists(q)]
        if not os.path.exists(rp) and not alt:
            fail(bad, "D7", "no work surface. Looked for roadmap/packages.json, "
                            "packets.json, docs/packets.md and a dispatch module. "
                            "Without one, nobody can pick work up.")
        elif not os.path.exists(rp):
            print(f"NOTE D7: the work surface here is {os.path.relpath(alt[0], repo)}, not "
                  "roadmap/packages.json. Both are accepted; dependency and cycle checks "
                  "run only on the roadmap form, so they are NOT judged.")
        else:
            pk = json.load(open(rp))["packages"]
            ids = [p["id"] for p in pk]
            if len(ids) != len(set(ids)):
                fail(bad, "D7", "duplicate package ids")
            known = set(ids)
            for p in pk:
                for dep in p.get("deps", []):
                    if dep not in known:
                        fail(bad, "D7", f"{p['id']} depends on unknown {dep}")
            if not any(not p.get("deps") for p in pk):
                fail(bad, "D7", "no zero-dependency package — nobody can start")

    # D11 — the spine must declare what it adopts rather than invent
    if repo:
        std = os.path.join(repo, "spine", "standards.json")
        if os.path.exists(std):
            s = json.load(open(std))["standards"]
            for e in s:
                if not e.get("replaces") or not e.get("does_not"):
                    fail(bad, "D11", f"{e['id']} does not say what it replaces and what it "
                                     "does not do; an adoption read as a guarantee is worse "
                                     "than no adoption")

    # D10
    if d["state"] not in STATES:
        fail(bad, "D10", f"state '{d['state']}' is not one of {sorted(STATES)}")

    # D2 + D1, only judgeable with the repo present
    if repo:
        iface = os.path.join(repo, d["interface"])
        if not os.path.exists(iface):
            fail(bad, "D1", f"interface absent (looked at {os.path.abspath(iface)})")
        else:
            src = open(iface, errors="replace").read()
            if re.search(r"\)\s*\{[^}]*\breturn\b", src):
                fail(bad, "D1", "interface file contains an implementation body")
        colf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "spine", "collisions.json")
        collide = set()
        if os.path.exists(colf):
            collide = {c["id"] for c in json.load(open(colf))["collisions"]}
        for impl in d["implementations"]:
            if impl in collide:
                continue
            hits = []
            for dp, _, fns in os.walk(repo):
                if any(s in dp for s in (".git", "/registry", "/descriptors")):
                    continue
                for fn in fns:
                    if not fn.endswith((".c", ".h", ".py", ".sh")):
                        continue
                    fp = os.path.join(dp, fn)
                    if os.path.basename(d["registry"]) == fn:
                        continue
                    if impl in os.path.relpath(fp, repo):
                        continue
                    if re.search(r"\b" + re.escape(impl) + r"\b",
                                 open(fp, errors="replace").read()):
                        hits.append(os.path.relpath(fp, repo))
            if hits:
                fail(bad, "D2", f"implementation '{impl}' named outside the registry: {hits[:4]}")

    for i, m in bad:
        print(f"FAIL {i}: {m}")
    if bad:
        return 1
    print(f"OK {d['id']}: conformant against {'descriptor + repo' if repo else 'descriptor only'}")
    if not repo:
        print("NOTE: D1, D2 and D7 were NOT judged — no --repo given.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
