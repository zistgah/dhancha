#!/usr/bin/env python3
"""Prove the vendored BoM primitive in the sovereign domains still answers as core does.

A domain cannot import this repository at run time — it must work with the network
unplugged and this repository absent. So it vendors. This is the check that stops a
vendored copy from quietly becoming a second implementation.

Searches for each sibling; when a sibling is absent it says where it looked and reports
the check as UNJUDGED. It never reports an absent sibling as agreement.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import drift, BomLine, PriceQuote
import core.bom as reference

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV = ("ref,mpn,qty,manufacturer,description\n"
       "L1,RTL2832U,1,Realtek,SDR front end\n")

VECTORS = [("parse_csv", (CSV,), {})]


def vendored():
    """Read what each DESCRIPTOR declares it vendors. The skeleton names no domain (D-A)."""
    out = []
    dd = os.path.join(ROOT, "descriptors")
    for f in sorted(os.listdir(dd)):
        if not f.endswith(".json") or f.startswith("_"):
            continue
        import json as _j
        d = _j.load(open(os.path.join(dd, f)))
        for v in d.get("vendors", []):
            out.append((d["id"], v))
    return out


def find(domain, rel):
    for base in (os.path.join(ROOT, "..", domain),
                 os.path.join(ROOT, "..", "..", domain),
                 os.path.expanduser(f"~/{domain}"),
                 f"/shared/estate/github/zistgah/{domain}"):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            return os.path.abspath(p), None
    return None, [os.path.abspath(os.path.join(b, rel)) for b in (
        os.path.join(ROOT, "..", domain), os.path.join(ROOT, "..", "..", domain),
        os.path.expanduser(f"~/{domain}"), f"/shared/estate/github/zistgah/{domain}")]


def main():
    rc, judged = 0, 0
    declared = vendored()
    for name, v in declared:
        found, looked = find(name, v["path"])
        if not found:
            print(f"UNJUDGED {name} [{v['primitive']}]: not found. Looked at:")
            for l in looked:
                print("   ", l)
            print(f"UNJUDGED {name}: no agreement is claimed.")
            continue
        # The vendored module uses package-relative imports, so it is loaded AS part of
        # its package rather than as a loose file.
        try:
            pkg_dir = os.path.dirname(os.path.dirname(found))      # .../src/<pkg>
            sys.path.insert(0, os.path.dirname(pkg_dir))           # .../src
            import importlib
            mod = importlib.import_module(
                os.path.basename(pkg_dir) + "." + v["module"])
        except Exception as e:
            print(f"UNJUDGED {name}: {found} would not import "
                  f"({type(e).__name__}: {e}). No agreement is claimed.")
            continue
        judged += 1
        out = drift.compare(reference, mod, VECTORS)
        if out:
            rc = 1
            for line in out:
                print(f"DRIFT {name}: {line}")
        else:
            print(f"OK {name}: vendored {v['primitive']} agrees with core on "
                  f"{len(VECTORS)} vector(s)")
    if judged == 0:
        print(f"drift: {len(declared)} vendored primitive(s), NONE judged — the siblings "
              "are not on this machine. This is not a pass and not a failure; it is "
              "unjudged, and nothing is claimed about whether they have drifted.")
        return 3
    if judged < len(declared):
        print(f"drift: {judged} of {len(declared)} judged; the rest are unjudged above.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
