"""Prove a vendored copy of a primitive has not drifted from the reference.

A sovereign domain cannot import another repository at run time — it must still work with
the network unplugged and the sibling repo absent. So it vendors. Vendoring without a
drift check is how two implementations of one thing appear, which this estate has already
paid for once at nine-repository scale.

This compares BEHAVIOUR on a shared vector set, not source text. Two files may differ in
comments, imports and formatting and still be the same primitive; two files may be
textually similar and answer differently.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations
import importlib.util, os


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        raise FileNotFoundError(f"no module at {os.path.abspath(path)}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def compare(reference, vendored, vectors):
    """vectors: [(callable_name, args, kwargs)] -> list of divergences, empty if none.

    A name missing from either side is a divergence, and is reported as which side.
    """
    out = []
    for fname, args, kwargs in vectors:
        a = getattr(reference, fname, None)
        b = getattr(vendored, fname, None)
        if a is None or b is None:
            out.append(f"{fname}: missing from "
                       + ("the reference" if a is None else "the vendored copy"))
            continue
        try:
            ra, ea = a(*args, **kwargs), None
        except Exception as e:
            ra, ea = None, type(e).__name__
        try:
            rb, eb = b(*args, **kwargs), None
        except Exception as e:
            rb, eb = None, type(e).__name__
        if ea != eb:
            out.append(f"{fname}{args}: reference raised {ea}, vendored raised {eb}")
        elif str(ra) != str(rb):
            out.append(f"{fname}{args}: reference gave {ra!r}, vendored gave {rb!r}")
    return out
