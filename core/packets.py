"""Work packets — the orchestration surface. EXTRACTED from the communication element.

A packet is one unit of work another agent, or another person, can take away and
finish without asking a question, because it carries its own inputs, its own
interface and, above all, its own acceptance command. The command is the contract:
the packet is done when it passes, and not when the work reads well.

Labels are CAPABILITIES — needs:code, needs:proof, needs:testing, needs:ontology,
needs:visual, needs:legal, needs:human — never a model name. Which agent takes a
packet is a dispatch decision by the human, not a property of the work.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict, field

CAPABILITIES = ("needs:code", "needs:proof", "needs:testing", "needs:ontology",
                "needs:visual", "needs:legal", "needs:human")


@dataclass(frozen=True)
class Packet:
    id: str
    title: str
    needs: tuple
    why: str
    inputs: tuple
    interface: str
    acceptance: str
    forbidden: tuple = field(default_factory=lambda: (
        "inventing a numeric constant that is not derived or cited",
        "returning a value where the module currently returns Unknown, without "
        "naming the source of the value",
        "a driver that synthesises samples instead of raising NotFitted",
    ))

    def as_dict(self):
        return asdict(self)




def validate(packets) -> list:
    """Return the reasons these packets cannot be dispatched. Empty means dispatchable."""
    bad = []
    seen = set()
    for p in packets:
        if p.id in seen:
            bad.append(f"{p.id}: duplicate id")
        seen.add(p.id)
        if not p.acceptance:
            bad.append(f"{p.id}: no acceptance command — nothing decides 'done'")
        for n in p.needs:
            if n not in CAPABILITIES:
                bad.append(f"{p.id}: label '{n}' is not a capability; "
                           "a label naming a model routes work by vendor, not by need")
    return bad


def as_json(packets) -> str:
    return json.dumps([p.as_dict() for p in packets], indent=2, ensure_ascii=False)
