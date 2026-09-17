# CONTRACT — dhancha

- **D1–D10** as stated in SPINE.md are normative and are enforced by `make check`.
- **Z15** measure, then claim. A claim without a recorded measurement is a defect.
- **Z16** one package, one pull request, one proof.
- **D-A** The skeleton names no domain. `grep` for any domain id in `tools/` or `spine/`
  must return nothing; domains exist only in `descriptors/`.
- **D-B** A validator that cannot validate says what it looked for and where. It never
  reports absence as conformance and never reports conformance as absence.
- **D-C** Generated output is regenerable. `spine_new.py` run twice on one descriptor
  produces byte-identical trees.
- **D-D** Nothing here reaches the world. No mint, no publish, no network call.
