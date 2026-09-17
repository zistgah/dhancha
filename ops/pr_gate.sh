#!/usr/bin/env bash
# D8 / Z15 / Z16. Judges a diff, not a promise.
set -u
CLAIMS='faster|fastest|optimal|optimised|optimized|complete|fully|production-ready|robust|scalable|proven|guaranteed|best'
self_test=0; [ "${1:-}" = "--self-test" ] && self_test=1

root() { git rev-parse --show-toplevel 2>/dev/null || pwd; }
R="$(root)"

judge() {
  local diff="$1" rc=0
  if grep -Eqi "^\+.*($CLAIMS)" "$diff"; then
    if ! grep -q '"measurement"' "$R/ops/budgets.json" 2>/dev/null; then
      echo "FAIL Z15: the diff makes a claim and ops/budgets.json records no measurement"; rc=1
    fi
    if ! grep -Eq "^\+\+\+ .*(evidence|measurements|bench)/" "$diff"; then
      echo "FAIL Z15: a claim landed with no measurement artifact in the same change"; rc=1
    fi
  fi
  local pkgs
  pkgs=$(grep -Eo '^\+\+\+ b/(drivers|ports)/[a-z0-9_]+' "$diff" | sort -u | wc -l)
  if [ "$pkgs" -gt 1 ]; then
    echo "FAIL Z16: $pkgs packages in one change. One package, one pull request, one proof."; rc=1
  fi
  return $rc
}

if [ "$self_test" = 1 ]; then
  t="$PWD/.prgate-$$"; mkdir -p "$t"
  printf '+++ b/drivers/a/x.c\n+this is the fastest path\n' > "$t/claim.diff"
  printf '+++ b/drivers/a/x.c\n+adds a port\n' > "$t/clean.diff"
  printf '+++ b/drivers/a/x.c\n+++ b/drivers/b/y.c\n+two\n' > "$t/two.diff"
  fails=0
  judge "$t/claim.diff" >/dev/null || fails=$((fails+1))
  judge "$t/two.diff"   >/dev/null || fails=$((fails+1))
  judge "$t/clean.diff" >/dev/null && clean=1 || clean=0
  rm -rf "$t"
  if [ "$fails" = 2 ] && [ "$clean" = 1 ]; then echo "  ok  pr_gate bites on a claim and on a two-package change, passes a clean one"; exit 0; fi
  echo "  FAIL pr_gate self-test (bites=$fails clean=$clean)"; exit 1
fi

git diff --unified=0 "${1:-HEAD~1}" > "$PWD/.prgate.diff" || { echo "cannot read a diff here"; exit 3; }
judge "$PWD/.prgate.diff"; rc=$?
rm -f "$PWD/.prgate.diff"
exit $rc
