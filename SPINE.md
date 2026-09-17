# The spine — what every FAKIR domain reuses, and what it must never reuse

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

Two domains exist: `zasab` (device control — the nerve) and `ertabat`
(communication engineering — the link). They are deliberately the same SHAPE, and
the reason is not economy. The same failure recurs in both: **a layer that cannot
do its job quietly pretends to, and every layer above it reports success.**

Everything in `core/` is here because that failure appeared twice. Nothing is here
because it looked reusable.

## The four extracted primitives

| primitive | the failure it exists to stop | where it was first paid for |
|---|---|---|
| `core.unknown` | a missing term became a zero, the margin came out positive, and the paper said the link closes | the atmospheric term in a link budget |
| `core.device` | an unbound device returned zeros, noise, or a replayed capture presented as live | a radio driver with no radio |
| `core.packets` | work was handed to another agent with nothing that decided "done" | multi-agent dispatch |
| `core.rungs` | a claim was read at a higher maturity than it was entered at | SPEC read as BENCH |

`Unknown` is the spine's spine. It refuses arithmetic, so a hole cannot be summed
over. A contributor who does not know something says so in the type system, and
every layer above carries that ignorance to the answer.

## The ten invariants

**D1 — one interface header.** The domain declares its capability surface in exactly one normative interface file. The header contains no implementation and names no implementation.

*checked by:* spine_validate: interface file present, declared in descriptor, contains no function body

**D2 — registry, not call sites.** Implementations are bound by a registry. No caller names an implementation. Deleting the registry must break binding, never compilation of callers.

*checked by:* spine_validate: no implementation id appears outside registry/ and descriptor

**D3 — ports include mock and template.** The same interface is realised on N substrates. Two are mandatory: mock (runs with nothing attached) and template (the empty port a third party fills).

*checked by:* spine_validate: ports[] contains mock and template

**D4 — the harness is the definition.** Conformance is an executable suite, not prose. Every condition carries a measurable acceptance criterion with units. A condition whose limit is unknown is written 'not established' — an invented limit is worse than an absent one.

*checked by:* spine_validate: every condition has criterion+unit or the exact string 'not established'

**D5 — one verb table, many surfaces.** skills/verbs.json is the single source for every agent surface. A surface is generated, never hand-written.

*checked by:* spine_validate: verbs.json present, each verb has args+returns+preconditions

**D6 — closed attachment set.** Foreign systems attach at a fixed enumerated set of points or not at all. A new kind of attachment is a contract change, not a patch.

*checked by:* spine_validate: INTEGRATION.md enumerates points; descriptor.attachment_points matches

**D7 — roadmap is data.** Work is packages/tracks/milestones in JSON, validated in `make check`. Every package declares dependencies; packages with none are startable immediately by anyone.

*checked by:* spine_validate + validate_roadmap: ids unique, deps resolve, no cycles, >=1 zero-dependency package

**D8 — measure, then claim.** A performance, coverage or completeness claim requires a recorded measurement in the same commit. One package, one pull request, one proof.

*checked by:* pr_gate: claim vocabulary in diff requires a budgets.json entry and a measurement artifact

**D9 — the engine is common, the workflow is not.** Domains share this skeleton and NOTHING else. Each domain authors its own purpose, contract, context, state model, invariants, failure modes, evidence requirements, workflow and artifact model. Reuse the smallest primitive. Architecture is never inferred from code reuse.

*checked by:* spine_leak: no domain's distinctive nouns may appear in another domain's descriptor or prose

**D10 — nothing pretends.** Built, wired-unproven, and not-built are three different states and are reported as three. No stub that looks alive. Absence is reported with where it was looked for.

*checked by:* spine_validate: descriptor.state values in {built,wired_unproven,not_built}; no other value accepted

## What the spine deliberately does NOT supply

Purpose. Contract. Context. State model. Domain invariants. Failure modes.
Evidence requirements. Workflow. Artifact model.

Those nine belong to the domain and ARE the domain. A skeleton that supplied them
would be one workflow wearing many nouns — which is a mistake this estate has
already made once, at scale, and D9 exists so that it fails a test rather than a
review.

`zasab` and `ertabat` share a **primitive**. They do not share an architecture.
