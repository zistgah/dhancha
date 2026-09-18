# dhancha (ڈھانچہ) — the domain spine

The skeleton every FAKIR domain is built on, and nothing more than a skeleton.

A domain — communication engineering, device control, metallurgy, anaesthesiology,
hydrology — is not built by copying another domain. It is built by satisfying ten
invariants and then authoring its own everything else.

- `SPINE.md` — the ten invariants, normative
- `spine/spine.schema.json` — the domain descriptor, machine readable
- `tools/spine_new.py` — generate a conformant skeleton from a descriptor (or from a FAKIR lattice code)
- `tools/spine_validate.py` — judge any repo against the invariants
- `tools/spine_leak.py` — refuse a domain that wears another domain's vocabulary
- `tools/spine_correlate.py` — the correlation graph across domains and estate components
- `cyclers/*.pni` — PANINI configuration so the work is done by whichever AI, not by one

Instantiated domains: `descriptors/zasab.json` (device control), `descriptors/ertabat.json`
(communication engineering), `descriptors/rayman.json` (a concept embodiment, carried at the
rung each of its scales actually reached).

## What the spine adopts rather than invents

`spine/standards.json` — each entry names what it replaces and, just as importantly, what
it does **not** do. CycloneDX (ECMA-424) for the bill of materials, Development Containers
for the lab, RO-Crate for captured evidence, UCUM for units, ISO 16290 TRLs as a declared
mapping from the rung ladder. Adopting a standard is not the same as being certified by it.

## The collaborator surface

- `domains/registry.json` — the collaborator domains, each with its OWN enablement list.
  66 enumerated against a declared 390. The remainder is left unnamed rather than invented.
- `labs/stack.json` — the dockerised lab, layer 0 physical world to layer 7 applications.
- `labs/holygrail.json` — the research-to-evidence loop, instantiated per domain, small
  enough to run locally.
- `tools/lab_gen.py` — a domain id in, a working lab kit out. Every cost reads
  `not established` until a BoM is priced: low cost is a measurement, not an adjective.
- `tools/anti_conflate.py` — refuses a text that collapses two things the corpus keeps apart.
- `tools/site_gen.py` — the site, generated from the registries. No domain is written into
  the markup.
- `cyclers/lab.pni` — hand a collaborator's lab to whichever model, through PANINI.

    make check

Stdlib Python 3 only. No pip, no network, no key.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22821645.svg)](https://doi.org/10.5281/zenodo.22821645)
