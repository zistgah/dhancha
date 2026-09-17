"""dhancha.core — the primitives every FAKIR domain reuses.

These were EXTRACTED from working domains, not designed in the abstract. Each one
exists because the same failure appeared twice:

  unknown   a missing number became a zero and the result came out green
  device    an unbound device returned a plausible reading instead of refusing
  packets   work was handed over without anything that decided 'done'
  rungs     a claim was read at a higher maturity than it was entered at
  bom       a total was quoted over the priced subset and read as the whole cost
  units     a unit was prose, so three readers read it three ways
  drift     a vendored copy quietly became a second implementation

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from .unknown import Unknown, Quantity, known, require
from .device import Device, Registry, NotFitted, Unsupported, Capability, conform
from .packets import Packet, CAPABILITIES, validate as validate_packets, as_json
from .rungs import Rung, LADDER, NoEvidence
from .bom import (BomLine, PriceQuote, PricedLine, parse_csv, totals,
                  to_cyclonedx, CDX_SPEC, CDX_PREDICATE_TYPE)
from .units import valid as unit_valid, why as unit_why
from .rungs import trl, TRL_MAP, TRL_SOURCE
from . import drift

__all__ = ["Unknown", "Quantity", "known", "require",
           "Device", "Registry", "NotFitted", "Unsupported", "Capability", "conform",
           "Packet", "CAPABILITIES", "validate_packets", "as_json",
           "Rung", "LADDER", "NoEvidence",
           "BomLine", "PriceQuote", "PricedLine", "parse_csv", "totals",
           "to_cyclonedx", "CDX_SPEC", "CDX_PREDICATE_TYPE",
           "unit_valid", "unit_why", "trl", "TRL_MAP", "TRL_SOURCE", "drift"]
