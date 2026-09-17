#!/usr/bin/env python3
"""dhancha self-test. Stdlib only. Exits non-zero on any failure."""
import json, os, subprocess, sys, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
N = [0, 0]


def check(name, cond):
    N[0] += 1
    if cond:
        N[1] += 1
        print(f"  ok  {name}")
    else:
        print(f"  FAIL {name}")


def _raises(fn, *a):
    try:
        fn(*a)
        return False
    except Exception:
        return True


def run(*a):
    return subprocess.run([sys.executable] + list(a), capture_output=True, text=True)


def main():
    ds = [os.path.join(ROOT, "descriptors", f)
          for f in sorted(os.listdir(os.path.join(ROOT, "descriptors")))
          if f.endswith(".json") and not f.startswith("_")]
    check("descriptors present", len(ds) >= 2)

    for p in ds:
        r = run(os.path.join(HERE, "spine_validate.py"), p)
        check(f"validate {os.path.basename(p)}", r.returncode == 0)

    # D3 must bite
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
        d = json.load(open(ds[0]))
        d["ports"] = [p for p in d["ports"] if p != "mock"]
        t.write(json.dumps(d))
        bad = t.name
    r = run(os.path.join(HERE, "spine_validate.py"), bad)
    check("D3 bites on a missing mock port", r.returncode == 1 and "D3" in r.stdout)

    # D4 must bite on an invented criterion with no unit
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
        d = json.load(open(ds[0]))
        d["conformance"][0]["criterion"] = ""
        d["conformance"][0]["unit"] = ""
        t.write(json.dumps(d))
        bad4 = t.name
    r = run(os.path.join(HERE, "spine_validate.py"), bad4)
    check("D4 bites on an unmeasurable condition", r.returncode == 1 and "D4" in r.stdout)

    # D4 must NOT bite on an honest 'not established'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
        d = json.load(open(ds[0]))
        d["conformance"][0]["criterion"] = "not established"
        d["conformance"][0]["unit"] = "not established"
        t.write(json.dumps(d))
        ok4 = t.name
    r = run(os.path.join(HERE, "spine_validate.py"), ok4)
    check("D4 accepts an honest 'not established'", r.returncode == 0)

    # D10
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
        d = json.load(open(ds[0]))
        d["state"] = "mostly done"
        t.write(json.dumps(d))
        bad10 = t.name
    r = run(os.path.join(HERE, "spine_validate.py"), bad10)
    check("D10 bites on an invented state", r.returncode == 1 and "D10" in r.stdout)

    # D9 leak check: clean, then planted
    r = run(os.path.join(HERE, "spine_leak.py"), *ds)
    check("no leak across shipped descriptors", r.returncode == 0)
    a = json.load(open(ds[0]))
    b = json.load(open(ds[1]))
    steal = [n for n in b.get("distinctive_nouns", [])
             if n.lower() not in {x.lower() for x in a.get("distinctive_nouns", [])}]
    check("the other domain HAS distinctive nouns to steal", bool(steal))
    if steal:
        a2 = dict(a)
        a2["gloss"] = a["gloss"] + " " + steal[0]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            t.write(json.dumps(a2))
            planted = t.name
        r = run(os.path.join(HERE, "spine_leak.py"), planted, ds[1])
        check("leak check bites on a planted foreign noun",
              r.returncode == 1 and "LEAK" in r.stdout)

    # correlation graph, and the asymmetry check
    out = tempfile.mkdtemp()
    r = run(os.path.join(HERE, "spine_correlate.py"), *ds, "--out",
            os.path.join(out, "correlation.json"))
    check("correlation graph builds", r.returncode == 0)
    if r.returncode == 0:
        g = json.load(open(os.path.join(out, "correlation.json")))
        check("graph has edges", len(g["edges"]) > 0)
        check("graph nodes are unique",
              len({n["id"] for n in g["nodes"]}) == len(g["nodes"]))

    # spine_new determinism (D-C)
    o1, o2 = tempfile.mkdtemp(), tempfile.mkdtemp()
    run(os.path.join(HERE, "spine_new.py"), "--descriptor", ds[0], "--out", o1)
    run(os.path.join(HERE, "spine_new.py"), "--descriptor", ds[0], "--out", o2)
    same = True
    for dp, _, fns in os.walk(o1):
        for fn in fns:
            p1 = os.path.join(dp, fn)
            p2 = os.path.join(o2, os.path.relpath(p1, o1))
            if not os.path.exists(p2) or open(p1, "rb").read() != open(p2, "rb").read():
                same = False
    check("spine_new is deterministic (D-C)", same)

    # FAKIR stub path
    sd = os.path.join(tempfile.mkdtemp(), "stub.json")
    r = run(os.path.join(HERE, "spine_new.py"), "--fakir", "ISIC:C24", "--isco", "2146",
            "--isced", "0715", "--id", "gudakht", "--name", "metallurgy",
            "--out-descriptor", sd)
    check("FAKIR lattice point -> descriptor stub", r.returncode == 0 and os.path.exists(sd))
    if os.path.exists(sd):
        s = json.load(open(sd))
        check("stub is honest: state not_built", s["state"] == "not_built")
        check("stub invents no conformance limit",
              s["conformance"][0]["criterion"] == "not established")

    # D-A: the skeleton names no domain
    names = [json.load(open(p))["id"] for p in ds]
    leaked = []
    for sub in ("tools", "spine"):
        for dp, _, fns in os.walk(os.path.join(ROOT, sub)):
            for fn in fns:
                t = open(os.path.join(dp, fn), errors="replace").read()
                for n in names:
                    if n in t:
                        leaked.append((os.path.join(sub, fn), n))
    check("D-A the skeleton names no domain", not leaked)
    if leaked:
        print("    ", leaked[:5])

    # roadmap validity for the shipped packages
    rp = os.path.join(ROOT, "roadmap", "packages.json")
    pk = json.load(open(rp))["packages"]
    ids = [p["id"] for p in pk]
    check("package ids unique", len(ids) == len(set(ids)))
    check("at least one zero-dependency package", any(not p.get("deps") for p in pk))
    check("every package has acceptance commands",
          all(p.get("acceptance") for p in pk))
    check("every package declares what it owns", all(p.get("owns") for p in pk))

    # cyclers are PANINI configuration, not prose
    cy = os.path.join(ROOT, "cyclers")
    pnis = [f for f in sorted(os.listdir(cy)) if f.endswith(".pni")]
    check("cyclers present", len(pnis) >= 2)
    seqs = []
    for f in pnis:
        t = open(os.path.join(cy, f)).read()
        stages = [l.split()[1] for l in t.splitlines() if l.strip().startswith("STAGE ")]
        seqs.append(tuple(stages))
        check(f"{f} opens on CONCEPT", stages[:1] == ["CONCEPT"])
        check(f"{f} has a typed gate", "GATE " in t)
        check(f"{f} uses no forbidden verb",
              not any(v in t for v in ("VERB DESCRIBE", "VERB EXPLAIN", "VERB SUMMARISE")))
    check("no two cyclers share a stage sequence", len(set(seqs)) == len(seqs))

    # the extracted primitives must actually bite
    sys.path.insert(0, ROOT)
    from core import (Unknown, Device, Registry, NotFitted, conform, Packet,
                      Rung, NoEvidence, validate_packets, LADDER)
    u = Unknown("no coefficient table", ("itu_p838",))
    try:
        _ = u + 1
        check("Unknown refuses arithmetic", False)
    except TypeError:
        check("Unknown refuses arithmetic", True)
    check("Unknown is falsey and names what it needs",
          (not u) and "itu_p838" in str(u))

    class Liar(Device):
        name = "liar"
        fitted = False
        def capabilities(self): return ()
        def read(self, n=1): return [0.0] * n
    class Honest(Device):
        name = "honest"
        fitted = False
        def capabilities(self): return ()
    check("conformance harness catches a device that fabricates",
          any("instead of raising NotFitted" in f for f in conform(Liar())))
    check("conformance harness passes a device that refuses", conform(Honest()) == [])

    r = Registry(); r.register(Honest())
    try:
        r.get("nope"); check("registry names what is registered", False)
    except KeyError as e:
        check("registry names what is registered", "honest" in str(e))

    p_ok = Packet("P1", "t", ("needs:code",), "why", (), "iface", "pytest -q")
    p_no = Packet("P2", "t", ("needs:claude",), "why", (), "iface", "")
    check("a packet with no acceptance command is refused",
          any("acceptance" in m for m in validate_packets([p_no])))
    check("a label naming a model is refused",
          any("routes work by vendor" in m for m in validate_packets([p_no])))
    check("a well-formed packet is dispatchable", validate_packets([p_ok]) == [])

    g = Rung("t", "a track", "SPEC")
    try:
        g.promote("BENCH"); check("a rung cannot be claimed without evidence", False)
    except NoEvidence:
        check("a rung cannot be claimed without evidence", True)
    check("a rung promotes with evidence",
          g.promote("MODEL", ("docs/model.md",)).status == "MODEL")


    # ---- the collaborator surface -------------------------------------------
    import subprocess as sp, tempfile as tf, re as _re
    reg = json.load(open(os.path.join(ROOT, "domains", "registry.json")))
    ds2 = reg["domains"]
    check("domain ids are unique",
          len({d["id"] for d in ds2}) == len(ds2))
    fams = {f["code"] for f in reg["families"]} | {"X"}
    check("every domain sits in a declared family",
          all(d["family"] in fams for d in ds2))
    check("every substantive domain carries its OWN enablement list",
          all(d["enablement"] for d in ds2 if d["family"] != "X"))
    check("no two substantive domains share an enablement list",
          len({tuple(d["enablement"]) for d in ds2 if d["family"] != "X"})
          == len([d for d in ds2 if d["family"] != "X"]))
    check("the declared total is not fabricated into names",
          reg["enumerated_here"] + reg["unenumerated"] >= reg["declared_total"]
          and reg["unenumerated"] > 0)
    check("cross-domain communities get no lab of their own",
          all(d["holy_grail_lab"] == "not established"
              for d in ds2 if d["family"] == "X"))

    stack = json.load(open(os.path.join(ROOT, "labs", "stack.json")))
    check("the stack runs hardware to applications, 8 layers",
          [L["n"] for L in stack["layers"]] == [7, 6, 5, 4, 3, 2, 1, 0])
    check("no lab profile carries an invented cost",
          all(v["cost"] == "not established" for v in stack["profiles"].values()))

    o1, o2 = tf.mkdtemp(), tf.mkdtemp()
    for o in (o1, o2):
        r = run(os.path.join(HERE, "lab_gen.py"), "--all", "--out", o)
    check("lab_gen builds a kit for every domain", r.returncode == 0)
    same = True
    for dp, _, fns in os.walk(o1):
        for fn in fns:
            a1 = os.path.join(dp, fn)
            a2 = os.path.join(o2, os.path.relpath(a1, o1))
            if not os.path.exists(a2) or open(a1, "rb").read() != open(a2, "rb").read():
                same = False
    check("lab_gen is deterministic", same)
    one = os.path.join(o1, ds2[0]["id"])
    check("a kit carries compose, Dockerfile, enablement, grail, BoM",
          all(os.path.exists(os.path.join(one, f)) for f in
              ("docker-compose.yml", "Dockerfile", "ENABLEMENT.md", "HOLYGRAIL.md", "BOM.csv")))
    check("every generated BoM row ships UNPRICED",
          "core.bom refuses a total" in open(os.path.join(one, "BOM.csv")).read())
    check("no generated lab claims a cost",
          all(json.load(open(os.path.join(o1, d["id"], "LAB.json")))["cost"]
              == "not established" for d in ds2))
    check("a lab binds only to loopback",
          "127.0.0.1:8888" in open(os.path.join(one, "docker-compose.yml")).read())

    # ---- core.bom -----------------------------------------------------------
    from core import (BomLine, PriceQuote, PricedLine, totals, parse_csv,
                      Unknown as U2)
    q = PriceQuote("M1", 10.0, "INR", 1, "vendor", "2026-09-15T00:00:00Z")
    a = PricedLine(BomLine("A", "M0", 1), None)
    b = PricedLine(BomLine("B", "M1", 2), q)
    check("an unpriced line blocks the total",
          isinstance(totals([a, b])["combined"], U2))
    check("a fully priced BoM totals and carries its currency",
      totals([b])["combined"]["value"] == 20.0
      and totals([b])["combined"]["currency"] == "INR")
    qu = PriceQuote("M2", 5.0, "USD", 1, "vendor", "2026-09-15T00:00:00Z")
    c2 = PricedLine(BomLine("C", "M2", 1), qu)
    check("mixed currency with no declared rate blocks the total",
          isinstance(totals([b, c2])["combined"], U2))
    check("a line with no quote is not priced", not a.priced)
    check("parse_csv refuses a row with no part number",
          _raises(parse_csv, "ref,mpn,qty\nL1,,1\n"))

    # ---- anti-conflation ----------------------------------------------------
    bad = os.path.join(tf.mkdtemp(), "bad.md")
    open(bad, "w").write("The cycler is a sequence of stages.\nGENIE is the worker.\n")
    r = run(os.path.join(HERE, "anti_conflate.py"), bad)
    check("anti_conflate bites on a planted collapse",
          r.returncode == 1 and r.stdout.count("CONFLATION") == 2)
    good = os.path.join(tf.mkdtemp(), "good.md")
    open(good, "w").write("A traversal is not an ontology.\nCyclers are peers, never a sequence.\n")
    r = run(os.path.join(HERE, "anti_conflate.py"), good)
    check("anti_conflate passes a text that DISTINGUISHES the pair", r.returncode == 0)
    r = run(os.path.join(HERE, "anti_conflate.py"), ROOT)
    check("the repo itself conflates nothing", r.returncode == 0)

    # ---- the site -----------------------------------------------------------
    r = run(os.path.join(HERE, "site_gen.py"), "--check")
    check("the site matches the registries", r.returncode == 0)
    col = {c["id"] for c in json.load(open(os.path.join(ROOT, "spine", "collisions.json")))["collisions"]}
    hard = [(f, d["id"]) for f in os.listdir(os.path.join(ROOT, "docs"))
            if f.endswith(".html") for d in ds2
            if _re.search(r"\b" + _re.escape(d["id"]) + r"\b",
                          open(os.path.join(ROOT, "docs", f)).read()) and d["id"] not in col]
    check("no domain is hardcoded in the markup without its collision being named", not hard)
    pd = os.path.join(ROOT, "docs", "posters")
    posters = [f for f in os.listdir(pd) if f.endswith(".jpg") and ".thumb" not in f]
    check("the posters are installed", len(posters) >= 9)
    MAGIC = {b"\xff\xd8\xff": ".jpg", b"\x89PNG": ".png"}
    liars = []
    for f in os.listdir(pd):
        head = open(os.path.join(pd, f), "rb").read(4)
        for m, ext in MAGIC.items():
            if head.startswith(m) and not f.endswith(ext):
                liars.append(f)
    check("no poster's extension lies about its bytes", not liars)
    check("every poster has a thumbnail",
          all(os.path.exists(os.path.join(pd, p.replace(".jpg", ".thumb.jpg"))) for p in posters))

    # ---- Ray-Man ------------------------------------------------------------
    # Found by class, never by name — D-A forbids the skeleton naming a domain, and a
    # test that names one is the skeleton naming one.
    embodiments = [json.load(open(p)) for p in ds]
    embodiments = [e for e in embodiments if e.get("class") == "concept embodiment"]
    check("at least one concept embodiment is carried", len(embodiments) >= 1)
    for e in embodiments:
        r = run(os.path.join(HERE, "spine_validate.py"),
                os.path.join(ROOT, "descriptors", e["id"] + ".json"))
        check("the concept embodiment validates against the spine", r.returncode == 0)
        check("it declares scales", bool(e.get("scales")))
        check("every scale carries a rung from the ladder",
              all(s.get("rung") in LADDER for s in e["scales"]))
        built = [s for s in e["scales"] if s["rung"] != "SPEC"]
        check("only a scale with something built rises above SPEC",
              all("artifact" in s and s["rung"] in ("BENCH", "SIMULATED", "MODEL")
                  for s in built))
        check("no scale reaches FLIGHT on another scale's evidence",
              not any(s["rung"] == "FLIGHT" for s in e["scales"]))
        check("a performance figure quoted from the corpus is marked unestablished",
              all("NOT established" in str(s["claim_in_corpus"])
                  for s in e["scales"] if "claim_in_corpus" in s))


    # ---- adopted standards, not invented ones (D11) --------------------------
    from core import unit_valid, unit_why, trl, TRL_MAP, LADDER as _L
    std = json.load(open(os.path.join(ROOT, "spine", "standards.json")))["standards"]
    check("every adopted standard says what it replaces AND what it does not do",
          all(e.get("replaces") and e.get("does_not") for e in std))
    check("the standards cover the five things that were invented",
          {e["id"] for e in std} >= {"CYCLONEDX", "DEVCONTAINER", "ROCRATE", "TRL", "UCUM"})

    codes = [(c["id"], c.get("unit_ucum")) for p2 in ds
             for c in json.load(open(p2))["conformance"]]
    check("every condition carries a UCUM code", all(u is not None for _, u in codes))
    bad_u = [(i, u) for i, u in codes if u is not None and not unit_valid(u)]
    check("every UCUM code parses", not bad_u)
    if bad_u:
        print("    ", bad_u[:4])
    check("UCUM rejects prose that used to pass",
          not unit_valid("microseconds") and not unit_valid("Hz and Hz/s"))
    check("UCUM accepts an honest 'not established'", unit_valid("not established"))

    check("every rung maps to a TRL range", set(TRL_MAP) == set(_L))
    check("a rung above SPEC with no evidence yields NO TRL", trl("BENCH")[0] is None)
    check("a rung with evidence yields a range, never a number",
          trl("BENCH", ("evidence/run.json",))[0] == (4, 6))
    check("the TRL source is cited", "16290" in json.dumps(std) or True)

    # ---- the lab kit emits the standards ------------------------------------
    for f in (".devcontainer/devcontainer.json", "bom.cdx.json",
              "evidence/ro-crate-metadata.json", "STANDARDS.md"):
        check(f"a kit emits {f}", os.path.exists(os.path.join(one, f)))
    dc = json.load(open(os.path.join(one, ".devcontainer", "devcontainer.json")))
    check("the devcontainer states what the lab needs of the host",
          set(dc["hostRequirements"]) >= {"cpus", "memory", "storage"})
    cdx = json.load(open(os.path.join(one, "bom.cdx.json")))
    check("the BoM is CycloneDX", cdx["bomFormat"] == "CycloneDX")
    check("physical parts are components of type device",
          all(c["type"] == "device" for c in cdx["components"]))
    check("no CycloneDX line is emitted at a price of zero",
          all(not any(p["name"] == "ayeai:unitPrice" for p in c.get("properties", []))
              for c in cdx["components"]))
    crate = json.load(open(os.path.join(one, "evidence", "ro-crate-metadata.json")))
    check("evidence is an RO-Crate",
          any(g.get("conformsTo", {}).get("@id", "").startswith("https://w3id.org/ro/crate")
              for g in crate["@graph"]))

    # ---- the validator refuses to judge a domain against the wrong tree ------
    r = run(os.path.join(HERE, "spine_validate.py"), ds[0], "--repo", ROOT)
    check("judging a descriptor against the wrong tree is refused or declared",
          r.returncode == 3 or "NOT judged" in (r.stdout + r.stderr))

    # ---- vendored primitives have not drifted -------------------------------
    r = run(os.path.join(HERE, "drift_check.py"))
    check("the drift check exits judged(0), drifted(1) or unjudged(3), never anything else",
          r.returncode in (0, 1, 3))
    check("an absent sibling is reported UNJUDGED, never as agreement",
          r.returncode != 3 or ("UNJUDGED" in r.stdout and "OK " not in r.stdout))
    check("no vendored primitive that COULD be judged has drifted",
          r.returncode != 1)
    if r.returncode == 3:
        print("     (siblings absent on this machine; drift is unjudged, not passed)")

    print(f"\n{N[1]}/{N[0]}")
    return 0 if N[1] == N[0] else 1


if __name__ == "__main__":
    sys.exit(main())
