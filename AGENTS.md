# AGENTS — how a non-human contributor works here

1. Read `SPINE.md`. Ten invariants. They are the whole brief.
2. Pick ONE package from a domain's `roadmap/packages.json` whose `deps` are empty or met.
3. Work only inside that package's `owns` paths. Touching anything else is out of scope.
4. Satisfy the package's `acceptance` list literally. Each entry is a command that must exit 0.
5. `make check` must pass. `ops/pr_gate.sh` must pass.
6. One package, one pull request, one proof (Z16). Do not batch.
7. Where a value is unknown write `not established`. Do not supply a plausible number.
8. You may not mint, publish, push to a default branch, or edit `attest/`.

The prompts that drive this are in `cyclers/`. Run them through PANINI; any model, any
vendor, or none. The configuration is the specification — do not re-specify in chat.
