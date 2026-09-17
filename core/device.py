"""The honest-device pattern. EXTRACTED from the radio HAL.

One spec type, one device interface, one registry, one refusing stub, and a
conformance harness that is mutation-tested against a deliberate liar. This shape
is domain-invariant: a sensor, an actuator, a radio and an instrument all fail the
same way, by synthesising a plausible reading rather than admitting they are not
there.

The rule the harness enforces: an unbound device RAISES. It does not return zeros,
noise, or a replayed capture presented as live.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations
from dataclasses import dataclass, field


class NotFitted(Exception):
    """The device is not bound to anything. Nothing is produced."""


class Unsupported(Exception):
    """The substrate cannot perform this operation. Never a fabricated success."""


@dataclass(frozen=True)
class Capability:
    name: str
    present: bool
    note: str = ""


class Device:
    """Subclass and implement. Every unimplemented method raises Unsupported."""
    name = "unnamed"
    fitted = False

    def capabilities(self) -> tuple:
        raise Unsupported(f"{self.name}: capabilities not declared")

    def read(self, n: int = 1):
        raise NotFitted(f"{self.name}: nothing is bound; no samples exist to return")

    def write(self, payload):
        raise NotFitted(f"{self.name}: nothing is bound; nothing was written")


class Registry:
    """The only place a device implementation is named."""

    def __init__(self):
        self._d = {}

    def register(self, device: Device):
        if device.name in self._d:
            raise ValueError(f"{device.name} already registered")
        self._d[device.name] = device
        return device

    def get(self, name: str) -> Device:
        if name not in self._d:
            raise KeyError(f"no device '{name}'. Registered: {sorted(self._d)}")
        return self._d[name]

    def names(self) -> tuple:
        return tuple(sorted(self._d))


def conform(device: Device) -> list:
    """Return the ways this device lies. Empty means it was honest.

    This is the harness that must be mutation-tested: plant a device that returns
    zeros when unbound and assert that this function CATCHES it. A harness never
    tested against a liar has never been tested.
    """
    faults = []
    if not getattr(device, "fitted", False):
        try:
            out = device.read(4)
            faults.append(
                f"{device.name}: unbound, yet read() returned {type(out).__name__} "
                "instead of raising NotFitted")
        except NotFitted:
            pass
        except Unsupported:
            pass
    try:
        caps = device.capabilities()
        if not isinstance(caps, (tuple, list)):
            faults.append(f"{device.name}: capabilities() did not return a sequence")
    except Unsupported:
        faults.append(f"{device.name}: declares no capabilities at all")
    return faults
