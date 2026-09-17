"""Unit codes that a machine can read. UCUM, not prose.

D4 says a criterion carries a unit. Until now the unit was free text, so 'Hz and Hz/s',
'microseconds' and 'us' all passed while meaning three different things to three readers
and nothing to a program.

UCUM is rules-based: base units, SI prefixes, / and . operators, and {annotation} for a
dimensionless quantity that still needs a name. This module validates the subset this
estate actually uses and REFUSES a code it cannot parse rather than accepting it quietly.

  https://ucum.org — and QUDT if a unit ever needs to link to its quantity kind.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations
import re

NOT_ESTABLISHED = "not established"

BASE = {"m", "s", "g", "rad", "K", "C", "cd", "mol",
        "Hz", "N", "Pa", "J", "W", "A", "V", "F", "Ohm", "T", "H", "lm", "lx",
        "By", "bit", "B", "Bd", "eV", "L", "l", "t", "min", "h", "d", "a",
        "deg", "'", "''", "%", "1"}
PREFIX = {"Y", "Z", "E", "P", "T", "G", "M", "k", "h", "da",
          "d", "c", "m", "u", "n", "p", "f", "z", "y", "Ki", "Mi", "Gi", "Ti"}
# codes this estate uses that UCUM writes with an annotation or a special form
EXTRA = {"dB", "dB[mW]", "dB[W]", "dB[K]", "B[mW]", "B[W]"}

_ATOM = re.compile(r"^([A-Za-z\[\]'%]+|1)(-?\d+)?$")
_ANNOT = re.compile(r"^\{[A-Za-z0-9_]+\}$")


def _atom_ok(tok: str) -> bool:
    if _ANNOT.match(tok):
        return True
    m = _ATOM.match(tok)
    if not m:
        return False
    sym = m.group(1)
    if sym in BASE or sym in EXTRA:
        return True
    for p in sorted(PREFIX, key=len, reverse=True):
        if sym.startswith(p) and sym[len(p):] in BASE:
            return True
    return False


def valid(code: str) -> bool:
    """True if this is a UCUM expression this module can parse."""
    if not isinstance(code, str) or not code.strip():
        return False
    code = code.strip()
    if code == NOT_ESTABLISHED:
        return True
    # an expression is atoms joined by . and /, optionally with one annotation
    for tok in re.split(r"[./]", code):
        tok = tok.strip()
        if not tok or not _atom_ok(tok):
            return False
    return True


def why(code: str) -> str:
    """Say what is wrong, naming the token. A validator that cannot validate says why."""
    if code == NOT_ESTABLISHED:
        return ""
    if not isinstance(code, str) or not code.strip():
        return "empty unit code"
    bad = [t for t in re.split(r"[./]", code.strip()) if not _atom_ok(t.strip())]
    return (f"not a UCUM code: {bad}. Use a base unit with an SI prefix, or "
            "{annotation} for a named dimensionless quantity, or write "
            f"'{NOT_ESTABLISHED}'." if bad else "")
