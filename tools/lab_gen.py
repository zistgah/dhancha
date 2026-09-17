#!/usr/bin/env python3
"""Generate a dockerised lab kit for one collaborator domain.

  lab_gen.py --domain physics --out ../labs-out/physics
  lab_gen.py --all --out ../labs-out          # every enumerated domain

Deterministic: two runs on one registry produce byte-identical trees. Every cost is
Unknown until a BoM is priced — 'low cost' is a measurement, not an adjective.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NE = "not established"

COMPOSE = """# {name} — dockerised lab, generated from domains/registry.json
# Layers 2-7 of labs/stack.json. Layers 0 and 1 are physical and are in BOM.csv.
services:
  workbench:
    build: .
    image: humanesque/lab-{id}:0.1
    working_dir: /work
    volumes:
      - ./work:/work
      - ./evidence:/evidence          # captured, never generated
    environment:
      - LAB_DOMAIN={id}
      - LAB_PROFILE={profile}
    # devices: uncomment what this lab actually has. An absent device stays absent.
    # devices:
    #   - /dev/ttyUSB0:/dev/ttyUSB0
    ports:
      - "127.0.0.1:8888:8888"         # loopback only; exposing it is a separate act
"""

DOCKERFILE = """# {name} — layer 4 research software over layers 2-3.
# Pinned base, no network at run time, no key baked in.
FROM debian:stable-slim

RUN apt-get update && apt-get install -y --no-install-recommends \\
      python3 python3-pip python3-venv git make ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

# Layer 4 — domain stack. Fill from ENABLEMENT.md; install only what this domain uses.
# Layer 6 — Humanesque components, as needed and never all: {components}

WORKDIR /work
CMD ["/bin/bash"]
"""


DEVCONTAINER = {
    "classroom": {"cpus": 2, "memory": "4gb", "storage": "32gb"},
    "bench": {"cpus": 4, "memory": "8gb", "storage": "64gb"},
    "workstation": {"cpus": 8, "memory": "16gb", "storage": "256gb"},
    "cluster": {"cpus": 16, "memory": "64gb", "storage": "1tb"},
    "composed": {"cpus": 8, "memory": "16gb", "storage": "256gb"},
}


def devcontainer(d, stack):
    """One file that VS Code, Codespaces, DevPod, Coder and the devcontainer CLI all read.
    hostRequirements states what the lab NEEDS, so a machine too small says so up front
    instead of failing halfway through a build."""
    hr = DEVCONTAINER[d["lab_profile"]]
    return {
        "name": f"{d['name']} lab",
        "dockerComposeFile": "../docker-compose.yml",
        "service": "workbench",
        "workspaceFolder": "/work",
        "hostRequirements": hr,
        "features": {},
        "postCreateCommand": "echo 'Nothing has been measured yet. See HOLYGRAIL.md.'",
        "remoteEnv": {"LAB_DOMAIN": d["id"], "LAB_PROFILE": d["lab_profile"]},
        "customizations": {"vscode": {"extensions": []}},
    }


def rocrate(d):
    """The evidence directory as an RO-Crate. Captured, never generated — and now
    machine-readable about WHAT was captured, by which instrument, when."""
    return {
        "@context": "https://w3id.org/ro/crate/1.2/context",
        "@graph": [
            {"@id": "ro-crate-metadata.json", "@type": "CreativeWork",
             "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
             "about": {"@id": "./"}},
            {"@id": "./", "@type": "Dataset",
             "name": f"{d['name']} — captured evidence",
             "description": ("Every file here was captured by an instrument, never "
                             "generated. A result with no entry in this crate is not "
                             "evidence."),
             "license": {"@id": "https://spdx.org/licenses/Apache-2.0"},
             "hasPart": []},
            {"@id": "#instrument-template", "@type": "IndividualProduct",
             "name": "name the instrument, its model and its calibration date",
             "description": "not established"},
        ],
    }


def cyclonedx_stub(d, stack):
    """An HBOM in ECMA-424. Parts are components of type 'device'. Nothing is priced,
    and nothing is emitted at zero."""
    hw = stack["profiles"][d["lab_profile"]]["hardware"]
    return {
        "bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
        "metadata": {"component": {"type": "platform",
                                   "name": f"{d['id']}-lab", "version": "0.1"}},
        "components": [
            {"type": "device", "bom-ref": "L1-COMPUTE", "name": "compute",
             "description": hw,
             "properties": [{"name": "ayeai:qty", "value": "1"},
                            {"name": "ayeai:priced", "value": "false"}]},
            {"type": "device", "bom-ref": "L0-INSTRUMENT", "name": "instrument",
             "description": "name the part",
             "properties": [{"name": "ayeai:qty", "value": "1"},
                            {"name": "ayeai:priced", "value": "false"}]},
        ],
    }


def kit(d, stack, grail, out):
    files = {}
    i = d["id"]
    files["docker-compose.yml"] = COMPOSE.format(
        id=i, name=d["name"], profile=d["lab_profile"])
    files["Dockerfile"] = DOCKERFILE.format(
        name=d["name"], components=", ".join(d["components"]) or "none declared")
    enab = d["enablement"] or ["not established — this domain's enablement list is not in the corpus yet"]
    files["ENABLEMENT.md"] = (
        f"# How this lab enables {d['name']}\n\n"
        + (f"*{d['crossing']}*\n\n" if d.get("crossing") else "")
        + "".join(f"- {e}\n" for e in enab)
        + f"\nSubdomains served: {', '.join(d['subdomains']) or NE}\n"
        + f"\nHumanesque components mounted: {', '.join(d['components']) or 'none declared'}\n"
        + "\nNot every domain gets every component. A component nobody in this domain uses "
          "is not installed.\n")
    files["HOLYGRAIL.md"] = (
        f"# Holy Grail lab — {d['holy_grail_lab'] if d['holy_grail_lab'] != NE else d['name']}\n\n"
        + ("" if d["holy_grail_lab"] != NE else
           "This domain has no lab named in the corpus yet. The pattern below still applies; "
           "the name is yours to give.\n\n")
        + " → ".join(grail["loop"]) + "\n\n" + grail["closure"] + "\n\n"
        + grail["rung_governance"] + "\n")
    files["BOM.csv"] = (
        "ref,description,qty,unit_price,currency,source,retrieved_utc\n"
        f"L1-COMPUTE,{stack['profiles'][d['lab_profile']]['hardware']},1,,,,\n"
        "L0-INSTRUMENT,domain instrument — name the part,1,,,,\n"
        "# Every row above is UNPRICED. core.bom refuses a total until each carries a\n"
        "# source and a retrieved_utc. That is what makes 'low cost' checkable.\n")
    files[".devcontainer/devcontainer.json"] = json.dumps(
        devcontainer(d, stack), indent=2) + "\n"
    files["bom.cdx.json"] = json.dumps(cyclonedx_stub(d, stack), indent=2) + "\n"
    files["evidence/ro-crate-metadata.json"] = json.dumps(rocrate(d), indent=2,
                                                          ensure_ascii=False) + "\n"
    files["STANDARDS.md"] = (
        "# What this kit emits, and what it does not claim\n\n"
        "- `.devcontainer/devcontainer.json` — Development Containers Specification. Opens "
        "in VS Code, Codespaces, DevPod, Coder or the devcontainer CLI. `hostRequirements` "
        "says what the lab needs; it does not provision anything.\n"
        "- `bom.cdx.json` — CycloneDX (ECMA-424) HBOM, physical parts as `type: device`. "
        "CycloneDX prices nothing; every line here is marked unpriced.\n"
        "- `evidence/ro-crate-metadata.json` — RO-Crate 1.2. Says what was captured, by "
        "which instrument, when. It asserts nothing about whether the measurement is right.\n"
        "- Maturity is a rung from `core.rungs`, which maps to a TRL RANGE per ISO "
        "16290:2013. A rung with no evidence gets no TRL at all.\n")
    files["LAB.json"] = json.dumps({
        "domain": d["id"], "name": d["name"], "family": d["family"],
        "profile": d["lab_profile"], "holy_grail_lab": d["holy_grail_lab"],
        "components": d["components"], "state": "not_built",
        "cost": NE, "cost_note": "Unknown until BOM.csv is priced",
    }, indent=2, ensure_ascii=False) + "\n"
    files["README.md"] = (
        f"# {d['name']} — Humanesque lab kit\n\n"
        "A reproducible laboratory for your own work first. Use it, extend it, publish from "
        "it, build your own instruments on it. Contribute back what turns out to be useful.\n\n"
        "    docker compose build && docker compose run --rm workbench\n\n"
        "- `ENABLEMENT.md` — what this stack actually gives this domain\n"
        "- `HOLYGRAIL.md` — the research-to-evidence loop, instantiated here\n"
        "- `BOM.csv` — layers 0 and 1. Unpriced until you price it.\n\n"
        "Nothing here reports a result it did not measure, and nothing here claims a cost it "
        "did not price.\n")
    for rel, body in sorted(files.items()):
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(body)
    for sub in ("work",):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
        open(os.path.join(out, sub, ".gitkeep"), "w").write("")
    return len(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    reg = json.load(open(os.path.join(ROOT, "domains", "registry.json")))
    stack = json.load(open(os.path.join(ROOT, "labs", "stack.json")))
    grail = json.load(open(os.path.join(ROOT, "labs", "holygrail.json")))
    by = {d["id"]: d for d in reg["domains"]}
    if a.list:
        for d in reg["domains"]:
            print(f"  {d['id']:30} {d['family']:2} {d['name']}")
        print(f"\n{len(by)} enumerated, {reg['unenumerated']} of the declared "
              f"{reg['declared_total']} not yet named.")
        return 0
    if not a.out:
        print("lab_gen: --out is required unless you asked for --list", file=sys.stderr)
        return 3
    targets = list(by.values()) if a.all else ([by[a.domain]] if a.domain in by else [])
    if not targets:
        print(f"lab_gen: no domain '{a.domain}'. Try --list.", file=sys.stderr)
        return 3
    n = 0
    for d in targets:
        n += kit(d, stack, grail, os.path.join(a.out, d["id"]) if a.all else a.out)
    print(f"OK {len(targets)} lab kit(s), {n} files -> {a.out}")
    print("Every cost reads 'not established'. Price the BoM before calling a lab low cost.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
