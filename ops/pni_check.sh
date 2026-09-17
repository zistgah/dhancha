#!/usr/bin/env bash
# Checks cyclers/*.pni with PANINI's OWN checker when it can be found.
# C37: if it is not found, this says so. It does not pretend the files were checked.
set -u
R="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
for c in "$R/../panini/panini.py" "$HOME/panini/panini.py" \
         "/shared/estate/github/zistgah/panini/panini.py"; do
  if [ -f "$c" ]; then
    rc=0
    for f in "$R"/cyclers/*.pni; do python3 "$c" check "$f" || rc=1; done
    exit $rc
  fi
done
echo "pni_check: PANINI not found. Looked at ../panini, ~/panini and /shared/estate/github/zistgah/panini."
echo "pni_check: the .pni files have NOT been checked against the spec. Nothing is asserted about them."
exit 3
