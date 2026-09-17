#!/usr/bin/env python3
"""Generate a conformant domain skeleton from a descriptor, or a descriptor stub from
a FAKIR lattice point.

  spine_new.py --descriptor descriptors/x.json --out ../x
  spine_new.py --fakir ISIC:J61 --isco 2153 --isced 0714 --id x --name "..." --out-descriptor x.json

Deterministic: running twice on one descriptor produces byte-identical output (D-C).
"""
import json, os, sys, argparse

TPL_IFACE = """/* {name} — capability surface. D1: no implementation lives here. */
#ifndef {up}_HAL_H
#define {up}_HAL_H
#include <stddef.h>
#include <stdint.h>

typedef struct {id}_ctx {id}_ctx;

typedef struct {{
    const char *name;
    int  (*open)({id}_ctx **out, const char *cfg);
    int  (*close)({id}_ctx *ctx);
    int  (*caps)({id}_ctx *ctx, uint32_t *bitmap);
    int  (*get)({id}_ctx *ctx, const char *key, char *buf, size_t n);
    int  (*set)({id}_ctx *ctx, const char *key, const char *val);
    int  (*step)({id}_ctx *ctx, uint64_t t_ns);
}} {id}_hal;

#endif
"""

TPL_REG = """/* D2: the only file permitted to name an implementation. */
#include "{id}_hal.h"
extern const {id}_hal *{id}_registry[];
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--descriptor")
    ap.add_argument("--out")
    ap.add_argument("--fakir")
    ap.add_argument("--isco", default="")
    ap.add_argument("--isced", default="")
    ap.add_argument("--id")
    ap.add_argument("--name")
    ap.add_argument("--out-descriptor")
    a = ap.parse_args()

    if a.fakir:
        if not (a.id and a.name and a.out_descriptor):
            print("spine_new: --fakir needs --id, --name and --out-descriptor", file=sys.stderr)
            return 3
        stub = {
            "id": a.id, "name": a.name, "script": "", "gloss": "",
            "fakir": {"isic": [a.fakir], "isco": [a.isco] if a.isco else [],
                      "isced": [a.isced] if a.isced else [],
                      "agi_layers": ["L0", "L1", "L2"], "ilm_languages": []},
            "interface": f"include/{a.id}_hal.h",
            "registry": f"src/registry.c",
            "implementations": [], "ports": ["mock", "template"],
            "conformance": [{"id": f"{a.id.upper()}-C1", "condition": "not established",
                             "criterion": "not established", "unit": "not established"}],
            "verbs": "skills/verbs.json", "attachment_points": [],
            "state": "not_built", "distinctive_nouns": [], "correlates": []
        }
        open(a.out_descriptor, "w").write(json.dumps(stub, indent=2) + "\n")
        print(f"OK descriptor stub -> {a.out_descriptor}")
        print("Every 'not established' is a real unknown. Fill it by measurement, not by guess.")
        return 0

    if not (a.descriptor and a.out):
        print("spine_new: give --descriptor and --out", file=sys.stderr)
        return 3
    if not os.path.exists(a.descriptor):
        print(f"spine_new: cannot read {os.path.abspath(a.descriptor)}", file=sys.stderr)
        return 3
    d = json.load(open(a.descriptor))
    i = d["id"]
    files = {
        d["interface"]: TPL_IFACE.format(id=i, up=i.upper(), name=d["name"]),
        d["registry"]: TPL_REG.format(id=i),
        "skills/verbs.json": json.dumps({"domain": i, "verbs": []}, indent=2) + "\n",
        "descriptor.json": json.dumps(d, indent=2) + "\n",
        "roadmap/packages.json": json.dumps({"packages": []}, indent=2) + "\n",
        "roadmap/tracks.json": json.dumps({"tracks": []}, indent=2) + "\n",
        "roadmap/milestones.json": json.dumps({"milestones": []}, indent=2) + "\n",
        "INTEGRATION.md": f"# INTEGRATION — {d['name']}\n\n"
                          + "".join(f"- {p}\n" for p in d["attachment_points"])
                          + "\nThere is no fifth path. A new kind of attachment is a contract change.\n",
    }
    for p in d["ports"]:
        files[f"ports/{p}/PORT.md"] = f"# port: {p}\n\nstate: not_built\n"
    for m in d["implementations"]:
        files[f"drivers/{m}/DRIVER.md"] = f"# implementation: {m}\n\nstate: not_built\n"
    for rel, body in sorted(files.items()):
        fp = os.path.join(a.out, rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        open(fp, "w").write(body)
    print(f"OK {len(files)} files -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
