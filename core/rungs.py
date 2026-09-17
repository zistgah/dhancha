"""The maturity ladder. EXTRACTED from the SOTA track registry.

A claim can never be read at a higher rung than it was entered at, and promotion
requires evidence in the tree. The ladder is deliberately shared across domains
and across the collaborative programmes, so one repo's BENCH means what another's
does.

SPEC        the idea is described; nothing here computes it
MODEL       a closed-form or numerical model exists in this repo
SIMULATED   the model has been run against synthetic input
BENCH       measured on hardware on someone's bench
FLIGHT      measured in the deployed environment

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

LADDER = ("SPEC", "MODEL", "SIMULATED", "BENCH", "FLIGHT")

# A DECLARED mapping onto ISO 16290:2013 Technology Readiness Levels, so a collaborator
# can state a TRL to ESA, NASA, a defence programme or Horizon Europe without inventing
# one. It is a RANGE, never a number: ISO 16290 defines the levels and deliberately
# leaves the assessment to the adopting organisation, and so does this.
TRL_MAP = {
    "SPEC":      (1, 2),   # basic principles observed; concept formulated
    "MODEL":     (2, 3),   # concept formulated; analytical proof of concept
    "SIMULATED": (3, 4),   # analytical proof; validation in a laboratory environment
    "BENCH":     (4, 6),   # laboratory validation through demonstration in a relevant one
    "FLIGHT":    (7, 9),   # demonstration in the operational environment, up to flight proven
}
TRL_SOURCE = "ISO 16290:2013, Space systems — Definition of the Technology Readiness Levels"


def trl(status: str, evidence=()):
    """Return the TRL RANGE a rung corresponds to, or None with a reason.

    A rung above SPEC with no evidence recorded gets no TRL at all: a readiness level
    quoted without the evidence that earned it is the precise thing this refuses.
    """
    if status not in TRL_MAP:
        return None, f"{status} is not a rung: {LADDER}"
    if status != "SPEC" and not evidence:
        return None, (f"{status} is claimed with no evidence recorded, so no TRL is "
                      "stated. Record the artifact first.")
    lo, hi = TRL_MAP[status]
    return (lo, hi), (f"range only, per {TRL_SOURCE}; the assessment itself is the "
                      "adopting organisation's, not this tool's")


class NoEvidence(Exception):
    """Raised when a promotion is attempted without an artifact to stand on."""


@dataclass(frozen=True)
class Rung:
    key: str
    title: str
    status: str
    computable_today: tuple = ()
    not_computable: tuple = ()
    open_question: str = ""
    evidence: tuple = ()

    def as_dict(self):
        return asdict(self)

    def trl(self):
        return trl(self.status, self.evidence)

    def promote(self, to: str, evidence: tuple = ()):
        if to not in LADDER:
            raise ValueError(f"{to} is not a rung: {LADDER}")
        if LADDER.index(to) <= LADDER.index(self.status):
            raise ValueError(f"{to} does not sit above {self.status}")
        if not evidence:
            raise NoEvidence(
                f"{self.key}: promotion to {to} needs an artifact in the tree. "
                "A rung claimed without evidence is the thing this ladder exists to stop."
            )
        return Rung(self.key, self.title, to, self.computable_today,
                    self.not_computable, self.open_question, tuple(evidence))
