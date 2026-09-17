#!/usr/bin/env python3
"""Generate the site from the registries. Nothing about a domain is written in the markup.

  site_gen.py            # writes docs/*.html
  site_gen.py --check    # regenerates to a temp dir and fails if docs/ is stale

A test asserts that no domain id appears in any generated page's source outside the data
it fetches — delete the registry and the site reports it, rather than showing an empty
map as though the map were empty.
"""
import argparse, html, json, os, sys, tempfile, filecmp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NE = "not established"

CSS = """
:root{--ink:#e9e4d8;--dim:#8d99a8;--bg:#0b0e13;--pan:#11161e;--line:#222c38;--hot:#c9a45c;--ok:#57c8a0;--ne:#c2803c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 ui-monospace,Menlo,Consolas,monospace}
.wrap{max-width:70rem;margin:0 auto;padding:2rem 1.1rem 5rem}
h1{font-size:1.7rem;letter-spacing:.04em;margin:0 0 .2rem}
h2{font-size:.82rem;text-transform:uppercase;letter-spacing:.14em;color:var(--hot);font-weight:400;margin:2.4rem 0 .6rem;border-bottom:1px solid var(--line);padding-bottom:.4rem}
p{max-width:52rem}.dim{color:var(--dim)}.ne{color:var(--ne)}
nav a{color:var(--hot);text-decoration:none;margin-right:1.2rem;font-size:.85rem}
nav{margin:.8rem 0 1.4rem}
table{border-collapse:collapse;width:100%;margin:.6rem 0;font-size:.86rem}
td,th{border-bottom:1px solid var(--line);padding:.42rem .5rem;text-align:left;vertical-align:top}
th{color:var(--hot);font-weight:400;font-size:.72rem;text-transform:uppercase;letter-spacing:.09em}
.card{background:var(--pan);border:1px solid var(--line);border-radius:3px;padding:.9rem 1rem;margin:.5rem 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));gap:.7rem}
.layer{display:flex;gap:.7rem;align-items:baseline;border-bottom:1px solid var(--line);padding:.4rem 0}
.layer b{color:var(--hot);min-width:4.5rem;font-weight:400}
.gal{display:grid;grid-template-columns:repeat(auto-fill,minmax(13rem,1fr));gap:1rem}
.gal a{display:block;color:var(--ink);text-decoration:none;font-size:.8rem}
.gal img{width:100%;border:1px solid var(--line);border-radius:2px;display:block;margin-bottom:.35rem}
.flow{font-size:.84rem;color:var(--dim);line-height:2.1}
.flow span{background:var(--pan);border:1px solid var(--line);padding:.2rem .5rem;border-radius:2px;color:var(--ink)}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--dim);font-size:.8rem}
code{color:var(--hot)}
"""

NAVBAR = """<nav><a href="index.html">spine</a><a href="domains.html">domains</a>
<a href="labs.html">labs</a><a href="posters.html">posters</a>
<a href="corpus.html">corpus</a></nav>"""


def page(title, body):
    return (f"<!doctype html><meta charset=\"utf-8\"><title>{html.escape(title)}</title>"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<style>{CSS}</style><div class=\"wrap\">{body}"
            "<footer>dhancha — the domain spine. "
            "&copy; 1993&ndash;2026 Abhishek Choudhary. All rights reserved. AyeAI.<br>"
            "Retrieve, don't reconstruct. Where the corpus does not establish a "
            "relationship, it is not inferred.</footer></div>")


def build(out):
    reg = json.load(open(os.path.join(ROOT, "domains", "registry.json")))
    stack = json.load(open(os.path.join(ROOT, "labs", "stack.json")))
    grail = json.load(open(os.path.join(ROOT, "labs", "holygrail.json")))
    inv = json.load(open(os.path.join(ROOT, "spine", "invariants.json")))["invariants"]
    anti = json.load(open(os.path.join(ROOT, "spine", "anti_conflation.json")))
    std = json.load(open(os.path.join(ROOT, "spine", "standards.json")))
    posters = sorted(f for f in os.listdir(os.path.join(ROOT, "docs", "posters"))
                     if f.endswith(".jpg") and ".thumb" not in f) \
        if os.path.isdir(os.path.join(ROOT, "docs", "posters")) else []
    os.makedirs(out, exist_ok=True)

    # ---------- index
    b = ["<h1>dhancha <span class=\"dim\">ڈھانچہ</span></h1>",
         "<p class=\"dim\">the skeleton every domain is built on, and nothing more than a skeleton</p>",
         NAVBAR,
         "<p>Many domains. Many laboratories. Many implementations. One common spine. "
         "A domain satisfies ten invariants and then authors its own purpose, contract, "
         "context, state model, invariants, failure modes, evidence requirements, workflow "
         "and artifact model. Those nine are never shared.</p>",
         "<h2>the four extracted primitives</h2><table><tr><th>primitive</th>"
         "<th>the failure it exists to stop</th></tr>",
         "<tr><td><code>core.unknown</code></td><td>a missing term became zero, the margin "
         "came out positive, and the paper said the link closes</td></tr>",
         "<tr><td><code>core.device</code></td><td>an unbound device returned plausible "
         "readings instead of refusing</td></tr>",
         "<tr><td><code>core.packets</code></td><td>work was handed over with nothing that "
         "decided &ldquo;done&rdquo;</td></tr>",
         "<tr><td><code>core.rungs</code></td><td>a claim was read at a higher maturity than "
         "it was entered at</td></tr>",
         "<tr><td><code>core.bom</code></td><td>a total was quoted over the priced subset and "
         "read as the cost of the whole build</td></tr></table>",
         "<h2>the ten invariants</h2><table><tr><th>id</th><th>name</th><th>rule</th></tr>"]
    for i in inv:
        b.append(f"<tr><td>{i['id']}</td><td>{html.escape(i['name'])}</td>"
                 f"<td class=\"dim\">{html.escape(i['rule'])}</td></tr>")
    b.append("</table>")
    b.append("<h2>do not conflate</h2><div class=\"grid\">")
    for a, c in anti["pairs"]:
        b.append(f"<div class=\"card\">{html.escape(a)} <span class=\"ne\">&ne;</span> "
                 f"{html.escape(c)}</div>")
    b.append("<h2>adopted, not invented</h2><table><tr><th>standard</th>"
             "<th>replaces</th><th>what it does NOT do</th></tr>")
    for e in std["standards"]:
        b.append(f"<tr><td>{html.escape(e['name'])}</td>"
                 f"<td class=\"dim\">{html.escape(e['replaces'])}</td>"
                 f"<td class=\"ne\">{html.escape(e['does_not'])}</td></tr>")
    b.append("</table>")
    b.append("<p class=\"dim\">Checked, not merely printed: "
             "<code>tools/anti_conflate.py</code> refuses a text that equates any pair above, "
             "and passes a text that distinguishes them.</p>")
    open(os.path.join(out, "index.html"), "w").write(page("dhancha — the domain spine", "".join(b)))

    # ---------- domains
    fam = {f["code"]: f for f in reg["families"]}
    b = ["<h1>collaborator domains</h1>",
         f"<p class=\"dim\">{reg['enumerated_here']} enumerated &middot; "
         f"<span class=\"ne\">{reg['unenumerated']} of the declared {reg['declared_total']} "
         "not yet named</span></p>", NAVBAR,
         f"<div class=\"card dim\">{html.escape(reg['enumeration_note'])}</div>",
         "<h2>families</h2><table><tr><th>code</th><th>family</th><th>ids</th></tr>"]
    for f in reg["families"]:
        cls = ' class="ne"' if f["id_range"] == NE else ""
        b.append(f"<tr><td>{f['code']}</td><td>{html.escape(f['name'])}</td>"
                 f"<td{cls}>{html.escape(f['id_range'])}</td></tr>")
    b.append("</table>")
    b.append("<h2>how each domain is enabled</h2>")
    b.append("<p class=\"dim\">The enablement list belongs to the domain. It is not "
             "boilerplate, and a component with no named task in a domain is not installed "
             "in that domain&rsquo;s lab.</p>")
    b.append("<table id=\"dt\"><tr><th>domain</th><th>family</th><th>enabled with</th>"
             "<th>Holy Grail lab</th></tr></table>")
    b.append("<p class=\"dim\" id=\"dnote\"></p>")
    b.append("""<script>
fetch('registry.json').then(r=>r.json()).then(reg=>{
  const t=document.getElementById('dt'),fam={};
  reg.families.forEach(f=>fam[f.code]=f.name);
  reg.domains.forEach(d=>{
    const en=(d.enablement.length?d.enablement:(d.crossing?[d.crossing]:['not established']))
      .map(x=>'<div>'+x+'</div>').join('');
    const lab=d.holy_grail_lab==='not established'
      ? '<span class="ne">not established</span>' : d.holy_grail_lab;
    t.insertAdjacentHTML('beforeend',
      `<tr><td><b>${d.name}</b><div class="dim">${d.subdomains.join(' · ')||''}</div></td>
       <td class="dim">${fam[d.family]||d.family}</td>
       <td class="dim">${en}</td><td>${lab}</td></tr>`);
  });
  document.getElementById('dnote').textContent =
    reg.domains.length+' domains rendered from the registry. '+
    reg.unenumerated+' of the declared '+reg.declared_total+' are not named here.';
}).catch(()=>{document.getElementById('dnote').textContent=
 'registry.json could not be read from this page. The map is NOT empty — it is unread. '+
 'Nothing is claimed about the domains.';});
</script>""")
    open(os.path.join(out, "domains.html"), "w").write(page("collaborator domains", "".join(b)))

    # ---------- labs
    b = ["<h1>the labs</h1>",
         "<p class=\"dim\">a reproducible laboratory for your own work first</p>", NAVBAR,
         "<p>Bring your domain problem. The stack below is yours to use for your ordinary "
         "work, extend, publish from and build instruments on. Contribute back what turns "
         "out to be useful. You do not have to become a theorist of anything.</p>",
         "<h2>the common stack</h2><div class=\"card\">"]
    for L in stack["layers"]:
        b.append(f"<div class=\"layer\"><b>Layer {L['n']}</b><div>{html.escape(L['name'])}"
                 f"<div class=\"dim\">{html.escape(L['holds'])}</div></div></div>")
    b.append(f"</div><p class=\"dim\">{html.escape(stack['rule'])}</p>")
    b.append("<h2>profiles</h2><table><tr><th>profile</th><th>for</th><th>hardware</th>"
             "<th>cost</th></tr>")
    for k, v in stack["profiles"].items():
        b.append(f"<tr><td>{k}</td><td class=\"dim\">{html.escape(v['target'])}</td>"
                 f"<td class=\"dim\">{html.escape(v['hardware'])}</td>"
                 f"<td class=\"ne\">{html.escape(v['cost'])}</td></tr>")
    b.append(f"</table><div class=\"card ne\">{html.escape(stack['cost_note'])}</div>")
    b.append("<h2>the Holy Grail loop</h2><p class=\"flow\">"
             + " &rarr; ".join(f"<span>{html.escape(s)}</span>" for s in grail["loop"])
             + "</p>")
    b.append(f"<p>{html.escape(grail['closure'])}</p>"
             f"<div class=\"card dim\">{html.escape(grail['rung_governance'])}</div>")
    b.append("<h2>labs named in the corpus</h2><div class=\"grid\">")
    for n in grail["named_labs"]:
        b.append(f"<div class=\"card\">{html.escape(n)}</div>")
    b.append(f"</div><p class=\"ne\">{grail['unnamed']} enumerated domains have no lab named "
             "in the corpus. The pattern still applies; the name is his to give.</p>")
    b.append("<h2>generating one</h2><div class=\"card\"><code>"
             "python3 tools/lab_gen.py --list<br>"
             "python3 tools/lab_gen.py --domain &lt;id from --list&gt; --out ../labs/&lt;id&gt;<br>"
             "python3 tools/lab_gen.py --all --out ../labs"
             "</code></div>")
    open(os.path.join(out, "labs.html"), "w").write(page("the labs", "".join(b)))

    # ---------- posters
    b = ["<h1>the posters</h1>",
         "<p class=\"dim\">the corpus this spine was extracted from</p>", NAVBAR]
    if posters:
        b.append("<div class=\"gal\">")
        for p in posters:
            thumb = p.replace(".jpg", ".thumb.jpg")
            label = p[:-4].replace("-", " ")
            orig = next((o for o in os.listdir(os.path.join(ROOT, "docs", "posters"))
                         if o.startswith(p[:-4] + ".orig.")), None)
            extra = (f"<div class=\"dim\">full resolution: "
                     f"<a href=\"posters/{orig}\">{orig.split('.')[-1]}</a></div>") if orig else ""
            b.append(f"<a href=\"posters/{p}\"><img loading=\"lazy\" src=\"posters/{thumb}\" "
                     f"alt=\"{html.escape(label)}\">{html.escape(label)}</a>{extra}")
        b.append("</div>")
        b.append("<p class=\"dim\">Shown at the resolution carried in this repository. "
                 "If full-resolution originals were present beside the seed script they were "
                 "installed instead, and this gallery serves those.</p>")
    else:
        b.append("<div class=\"card ne\">No posters are present in this repository. "
                 "They were not installed, and nothing is claimed about them.</div>")
    open(os.path.join(out, "posters.html"), "w").write(page("the posters", "".join(b)))

    # ---------- corpus
    b = ["<h1>the collaborator corpus</h1>",
         "<p class=\"dim\">one architecture &middot; many projections &middot; many "
         "traversals &middot; many domains &middot; many collaborators</p>", NAVBAR,
         "<p>The prose original is his. What this site serves is its structured form: every "
         "domain, its subdomains, the enablement list that belongs to it, and the Holy Grail "
         "lab the corpus names for it. The structured form is the one a machine can act on, "
         "and it is what <code>tools/lab_gen.py</code> reads.</p>",
         "<h2>the proposition</h2><div class=\"card\">Bring your domain problem. Here is the "
         "reproducible computational and physical infrastructure to investigate it, from "
         "hardware to application. The Holy Grail laboratory closes the loop from hypothesis "
         "to verified realization.</div>",
         "<h2>the three populations</h2><div class=\"grid\">",
         "<div class=\"card\"><b>Domain experts</b><div class=\"dim\">questions, domain "
         "knowledge, hypotheses, experiments, instruments, datasets, validation criteria, "
         "real problems</div></div>",
         "<div class=\"card\"><b>Research and engineering builders</b><div class=\"dim\">"
         "software, hardware, simulation, instrumentation, algorithms, models, integration"
         "</div></div>",
         "<div class=\"card\"><b>Infrastructure contributors</b><div class=\"dim\">common "
         "representations, contracts, orchestration, provenance, verification, "
         "reproducibility, interoperability, deployment</div></div></div>",
         "<h2>the contribution loop</h2><p class=\"flow\">"
         + " &rarr; ".join(f"<span>{s}</span>" for s in
                           ["common infrastructure", "common contracts", "domain lab kit",
                            "their own work", "experiment / result",
                            "component, data, method, instrument, model", "provenance",
                            "verify / reproduce", "contribute back"]) + "</p>",
         "<h2>on the count</h2>",
         f"<div class=\"card dim\">{html.escape(reg['enumeration_note'])}</div>",
         "<h2>the text as filed</h2>",
         "<p class=\"dim\">If <code>CORPUS.md</code> was placed beside the seed script it "
         "was installed verbatim and is linked below. Otherwise this page carries the "
         "structured form only, and says so rather than implying the prose is here.</p>",
         "<p id=\"cl\"></p>",
         "<script>fetch('CORPUS.md',{method:'HEAD'}).then(r=>{document.getElementById('cl')"
         ".innerHTML=r.ok?'<a href=\"CORPUS.md\">CORPUS.md</a> &mdash; the prose original, "
         "installed verbatim':'<span class=\"ne\">CORPUS.md is not in this repository.</span>';})"
         ".catch(()=>{document.getElementById('cl').innerHTML='<span class=\"ne\">CORPUS.md is "
         "not in this repository.</span>';});</script>"]
    open(os.path.join(out, "corpus.html"), "w").write(page("the collaborator corpus", "".join(b)))

    # registry copy the pages fetch
    open(os.path.join(out, "registry.json"), "w").write(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    return ["index.html", "domains.html", "labs.html", "posters.html", "corpus.html",
            "registry.json"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    docs = os.path.join(ROOT, "docs")
    if a.check:
        tmp = tempfile.mkdtemp()
        names = build(tmp)
        stale = [n for n in names
                 if not os.path.exists(os.path.join(docs, n))
                 or not filecmp.cmp(os.path.join(tmp, n), os.path.join(docs, n), shallow=False)]
        if stale:
            print("FAIL site is stale, regenerate with tools/site_gen.py: " + ", ".join(stale))
            return 1
        print(f"OK site matches the registries ({len(names)} files)")
        return 0
    names = build(docs)
    print(f"OK site: {len(names)} files -> docs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
