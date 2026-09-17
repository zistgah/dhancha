PY ?= python3
DESC := $(filter-out descriptors/_template.json,$(wildcard descriptors/*.json))

check:
	@$(PY) tools/selftest.py
	@$(PY) tools/spine_leak.py $(DESC)
	@$(PY) tools/spine_correlate.py $(DESC) --out docs/correlation.json
	@$(PY) tools/anti_conflate.py . docs
	@$(PY) tools/drift_check.py; rc=$$?; [ $$rc -eq 0 ] || [ $$rc -eq 3 ] || exit $$rc
	@$(PY) tools/site_gen.py --check
	@bash ops/pr_gate.sh --self-test

site:
	@$(PY) tools/site_gen.py

labs:
	@$(PY) tools/lab_gen.py --all --out ../labs

pni-check:
	@bash ops/pni_check.sh

.PHONY: check site labs pni-check
