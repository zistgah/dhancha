"""Bill of materials: lines, quotes, and totals that refuse to round up to a lie.

EXTRACTED — and this one is a CORRECTION. A thinner version of this was written into the
spine while the richer version already existed in a domain. That is reinvention of
retrieved code, inside the repository whose whole purpose is to stop it. The domain's
shape is the reference; the domain keeps its own vendored copy because it is sovereign,
and core.drift proves the two have not diverged.

  a quote carries its source and the time it was retrieved, or it is not a quote
  an unpriced line blocks the combined total; the total becomes Unknown
  a mixed-currency total needs a declared exchange rate naming its source and date

`to_cyclonedx()` emits ECMA-424 (OWASP CycloneDX) so the result is readable by tooling
nobody here has to maintain. CycloneDX prices nothing; provenance of a price stays ours.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field, asdict

from .unknown import Unknown


@dataclass
class BomLine:
    ref: str
    mpn: str
    qty: int = 1
    manufacturer: str = ""
    description: str = ""
    alternates: tuple = field(default_factory=tuple)
    subsystem: str = ""

    def key(self):
        return (self.manufacturer.strip().lower(), self.mpn.strip().upper())


@dataclass(frozen=True)
class PriceQuote:
    mpn: str
    unit_price: float
    currency: str
    qty_break: int
    source: str
    retrieved_utc: str
    url: str = ""
    stock: object = None
    note: str = ""

    def extended(self, qty: int) -> float:
        return self.unit_price * qty

    def as_dict(self):
        return asdict(self)


def parse_csv(text: str):
    """ref,mpn,qty,manufacturer,description,subsystem — header required."""
    rows, out = list(csv.DictReader(io.StringIO(text))), []
    for i, r in enumerate(rows, 2):
        if not (r.get("mpn") or "").strip():
            raise ValueError(f"line {i}: mpn is empty — a BoM line without a "
                             f"part number cannot be priced or ordered")
        out.append(BomLine(
            ref=(r.get("ref") or f"L{i-1}").strip(),
            mpn=r["mpn"].strip(),
            qty=int((r.get("qty") or "1").strip() or 1),
            manufacturer=(r.get("manufacturer") or "").strip(),
            description=(r.get("description") or "").strip(),
            subsystem=(r.get("subsystem") or "").strip(),
            alternates=tuple(a.strip() for a in (r.get("alternates") or "").split("|") if a.strip()),
        ))
    return out


@dataclass
class PricedLine:
    line: BomLine
    quote: object          # PriceQuote or Unknown

    @property
    def priced(self) -> bool:
        return isinstance(self.quote, PriceQuote)

    @property
    def extended(self):
        return self.quote.extended(self.line.qty) if self.priced else self.quote


def totals(priced_lines, fx=None):
    """Per-currency totals, plus a single total ONLY if the rates are declared.

    A BoM half-priced in USD and half in INR has no single number until someone
    says which rate, on which date, from which source. `fx` is that declaration
    or the combined total stays Unknown.
    """
    per = {}
    unknown = []
    for pl in priced_lines:
        if pl.priced:
            per[pl.quote.currency] = per.get(pl.quote.currency, 0.0) + pl.extended
        else:
            unknown.append(pl.line.ref)
    out = {
        "per_currency": {k: round(v, 4) for k, v in sorted(per.items())},
        "lines_total": len(priced_lines),
        "lines_priced": len(priced_lines) - len(unknown),
        "lines_unpriced": len(unknown),
        "unpriced_refs": unknown,
    }
    if unknown:
        out["combined"] = Unknown(
            f"{len(unknown)} of {len(priced_lines)} lines have no price — "
            "a total over the priced subset would read as the cost of the build",
            tuple(unknown[:12]))
        return out
    if len(per) == 1:
        c, v = next(iter(per.items()))
        out["combined"] = {"value": round(v, 4), "currency": c, "fx": "not needed"}
        return out
    if not fx:
        out["combined"] = Unknown(
            f"lines are quoted in {', '.join(sorted(per))} and no exchange rate "
            "has been declared", ("--fx <file>", "rate source", "rate date"))
        return out
    miss = [c for c in per if c != fx.get("base") and c not in fx.get("rates", {})]
    if miss:
        out["combined"] = Unknown(f"no declared rate for {', '.join(miss)}",
                                  tuple(miss))
        return out
    tot = 0.0
    for c, v in per.items():
        tot += v if c == fx["base"] else v * fx["rates"][c]
    out["combined"] = {"value": round(tot, 4), "currency": fx["base"],
                       "fx": f"{fx.get('source','declared')} @ {fx.get('date','undated')}"}
    return out


# --------------------------------------------------------------- CycloneDX (ECMA-424)
CDX_SPEC = "1.6"


def to_cyclonedx(lines, priced=None, *, name="lab", version="0.1",
                 serial=None, timestamp=None):
    """Emit an HBOM. Physical parts are components of type 'device' (CycloneDX has no
    'hardware' type — 'device' is the correct one and has been since 1.0).

    A line with no quote is emitted WITHOUT a price. It is never emitted at zero.
    """
    by_ref = {}
    for p in (priced or []):
        by_ref[getattr(p, "ref", None) or getattr(getattr(p, "line", None), "ref", "")] = p
    comps = []
    for l in lines:
        ref = getattr(l, "ref", "")
        c = {"type": "device", "bom-ref": ref,
             "name": getattr(l, "mpn", "") or ref,
             "description": getattr(l, "description", "")}
        mf = getattr(l, "manufacturer", "")
        if mf:
            c["manufacturer"] = {"name": mf}
        q = getattr(l, "qty", None)
        if q is not None:
            c.setdefault("properties", []).append(
                {"name": "ayeai:qty", "value": str(q)})
        sub = getattr(l, "subsystem", "")
        if sub:
            c.setdefault("properties", []).append(
                {"name": "ayeai:subsystem", "value": sub})
        p = by_ref.get(ref)
        quote = getattr(p, "quote", None) if p else None
        if quote is not None and getattr(quote, "source", None) and \
                getattr(quote, "retrieved_utc", None):
            c.setdefault("properties", []).extend([
                {"name": "ayeai:unitPrice", "value": str(quote.unit_price)},
                {"name": "ayeai:currency", "value": quote.currency},
                {"name": "ayeai:priceSource", "value": quote.source},
                {"name": "ayeai:priceRetrievedUtc", "value": quote.retrieved_utc},
            ])
        else:
            c.setdefault("properties", []).append(
                {"name": "ayeai:priced", "value": "false"})
        comps.append(c)
    doc = {"bomFormat": "CycloneDX", "specVersion": CDX_SPEC, "version": 1,
           "metadata": {"component": {"type": "platform", "name": name,
                                      "version": version}},
           "components": comps}
    if serial:
        doc["serialNumber"] = serial
    if timestamp:
        doc["metadata"]["timestamp"] = timestamp
    return doc


# The in-toto predicate type OWASP recognises for any CycloneDX BoM. The estate's Candor
# receipts are already in-toto Statement v1, so a BoM attaches to one without a new format.
CDX_PREDICATE_TYPE = "https://cyclonedx.org/bom"
