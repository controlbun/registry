# Local build gate. This repo is not on GitHub, so there is no CI; these targets
# are the enforcement. `make hooks` wires them to pre-push so they are not optional.

PY := .venv/bin/python

.PHONY: verify test invariants manifests hooks site licenses

verify: invariants test manifests

# Rebuild the corpus, export it, and build the static site with its search index.
# npm ci rather than npm install: the lockfile is the pinned truth.
site:
	$(PY) fixtures/build.py
	PYTHONPATH=src $(PY) -m registry.export
	cd astro && npm ci --silent && npm run build

licenses:
	cd astro && npm run licenses

invariants:
	$(PY) -m pytest tests/test_invariants.py -q

test:
	$(PY) -m pytest -q

# Proofs bind file content, so a manifest that no longer matches the tree is a
# superseded record and not a failure. This only checks that every proof still
# binds its own manifest, which is the thing that would indicate real damage.
manifests:
	@fail=0; for f in _attest/MANIFEST*.sha256; do \
	  m=$$(shasum -a 256 "$$f" | cut -d' ' -f1); \
	  p=$$(ots info "$$f.ots" 2>/dev/null | awk '/File sha256 hash/{print $$NF}'); \
	  if [ "$$m" != "$$p" ]; then echo "BROKEN BINDING: $$f"; fail=1; fi; \
	done; [ $$fail -eq 0 ] && echo "all proofs bind their manifests"

hooks:
	git config core.hooksPath hooks
	@echo "pre-push gate active"
