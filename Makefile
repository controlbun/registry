# Local build gate. This repo is not on GitHub, so there is no CI; these targets
# are the enforcement. `make hooks` wires them to pre-push so they are not optional.

PY := .venv/bin/python

.PHONY: verify test invariants manifests hooks site licenses serve falsifier links

# The site is built before the tests, not after. Both the falsifier and the page
# tests read `astro/dist`, so building later meant they checked the previous
# build: a frontend that fails to build, or a page carrying a number that traces
# to nothing, used to pass this gate untouched.
verify: invariants site test links falsifier manifests

falsifier:
	$(PY) falsifier/verify.py

# A 404 on our own site is a claim that something exists. Nothing else in the gate
# follows a link: the invariants read source, the page tests read one page at a
# time, and the falsifier re-derives numbers.
links:
	$(PY) falsifier/links.py

# Rebuild the corpus, export it, and build the static site with its search index.
# npm ci rather than npm install: the lockfile is the pinned truth.
#
# Two seeds, two files, because `fixtures/build.py` says at the top that nothing
# it produces is a measurement and that has to stay true of every line in it. The
# real rows live in `artifacts/seed.py` and the `--check` beside it verifies the
# vendored tensors against the sha256 the ingest recorded, offline.
site:
	$(PY) fixtures/build.py
	$(PY) artifacts/seed.py
	$(PY) artifacts/ingest_arena.py --check
	PYTHONPATH=src $(PY) -m registry.export
	cd astro && npm ci --silent && npm run build

licenses:
	cd astro && npm run licenses

# Clean URLs mean directories, which file:// cannot resolve. Serve it instead.
serve:
	cd astro && npm run preview

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
