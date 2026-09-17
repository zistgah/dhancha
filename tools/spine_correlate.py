#!/usr/bin/env python3
"""Build the correlation graph across domains and estate components.

Usage: spine_correlate.py descriptors/*.json [--out docs/correlation.json]
Edges come only from declared `correlates` entries. Nothing is inferred.
"""
import json, os, sys

KINDS = {"shares_primitive", "consumes", "supplies", "co_located",
         "same_lattice_point", "mounts_in"}


def main():
    argv = sys.argv[1:]
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if not argv:
        print("spine_correlate: no descriptors given", file=sys.stderr)
        return 3
    nodes, edges = {}, []
    for p in argv:
        d = json.load(open(p))
        nodes[d["id"]] = {"id": d["id"], "name": d["name"], "script": d.get("script", ""),
                          "state": d["state"], "kind": "domain",
                          "fakir": d.get("fakir", {})}
        for c in d["correlates"]:
            if c["kind"] not in KINDS:
                print(f"FAIL {d['id']}: correlation kind '{c['kind']}' not in {sorted(KINDS)}")
                return 1
            edges.append({"from": d["id"], "to": c["with"], "kind": c["kind"],
                          "shared": c["shared"]})
            nodes.setdefault(c["with"], {"id": c["with"], "name": c["with"],
                                         "kind": "component", "state": "external"})
    # a shared primitive must be declared by both ends when both ends are domains
    for e in edges:
        if e["kind"] == "shares_primitive" and nodes[e["to"]]["kind"] == "domain":
            back = [x for x in edges if x["from"] == e["to"] and x["to"] == e["from"]]
            if not back:
                print(f"FAIL asymmetric shares_primitive: {e['from']} -> {e['to']} "
                      f"is not declared in return")
                return 1
    g = {"nodes": sorted(nodes.values(), key=lambda n: n["id"]),
         "edges": sorted(edges, key=lambda x: (x["from"], x["to"], x["kind"]))}
    s = json.dumps(g, indent=2) + "\n"
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        open(out, "w").write(s)
        print(f"OK correlation graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges -> {out}")
    else:
        sys.stdout.write(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
