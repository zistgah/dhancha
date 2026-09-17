"""Unknown — an absent value that refuses to pretend.

EXTRACTED, not invented: this is the cross-cutting type from the communication
element, lifted unchanged because it is not about communication. Every domain has
the same failure — a layer that cannot do its job quietly returns a default, and
every layer above it reports success on nothing.

Arithmetic on Unknown raises. That is the whole mechanism. A contributor who does
not know something says so in the type system, and the layers above carry that
ignorance all the way to the answer instead of laundering it into a zero.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
__all__ = ["Unknown", "Quantity", "known", "require"]


from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Unknown:
    """An absent value that refuses to pretend.

    Contract: unknown is not generated. Every path that cannot compute a number
    returns Unknown(reason=...) and every consumer must either propagate it or
    declare it. Arithmetic on Unknown raises — a missing input may never be
    silently coerced to zero, which is how a link budget comes out green on
    nothing.
    """
    reason: str
    needs: tuple = field(default_factory=tuple)

    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        n = f" (needs: {', '.join(self.needs)})" if self.needs else ""
        return f"UNKNOWN — {self.reason}{n}"

    def _no(self, *_a, **_k):
        raise TypeError(f"arithmetic on {self}")

    __add__ = __radd__ = __sub__ = __rsub__ = _no
    __mul__ = __rmul__ = __truediv__ = __rtruediv__ = _no
    __float__ = _no


@dataclass(frozen=True)
class Quantity:
    """A number that carries where it came from."""
    value: float
    unit: str
    source: str = "computed"

    def __float__(self) -> float:
        return float(self.value)

    def __str__(self) -> str:
        return f"{self.value:.6g} {self.unit}"


def known(x: Any) -> bool:
    return not isinstance(x, Unknown)


def require(**kw) -> Any:
    """Return Unknown naming every missing input, or None if all are present."""
    missing = [k for k, v in kw.items() if v is None or isinstance(v, Unknown)]
    if missing:
        return Unknown("required input absent", tuple(missing))
    return None
