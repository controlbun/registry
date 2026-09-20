# Local build gate. These targets are the enforcement, and `make hooks` wires them
# to pre-push so they are not optional.
#
# This used to say there is no CI because the repo is not on GitHub. The repo has
# been on GitHub since 2026-09-19 and there is still no CI, which is now a choice
# rather than a circumstance: Pages serves a locally built `astro/dist`, so the
# artifact a reader gets is the one that passed this gate, and a hosted build
# would quietly break that by having the falsifier check a different build.

PY := .venv/bin/python

.PHONY: verify test invariants manifests hooks site licenses serve falsifier links

# The site is built before the tests, not after. Both the falsifier and the page
# tests read `astro/dist`, so building later meant they checked the previous
# build: a frontend that fails to build, or a page carrying a number that traces
# to nothing, used to pass this gate untouched.
#
# `licenses` runs after `site`, because `site` is what installs node_modules and
# there is nothing to audit before it. It was written, documented in CLAUDE.md as
# a requirement, and left out of this chain, so the copyleft check was a target
# nobody called.
verify: invariants site licenses test links falsifier manifests

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
# One seed, because there is one corpus. This was two, and the first of them
# wrote a fabricated half that `DECISIONS.md` 2026-09-19 removed; `seed.py` took
# over the drop-and-rebuild that file owned. The `--check` beside it verifies the
# vendored tensors against the sha256 the ingest recorded, offline.
site:
	$(PY) artifacts/seed.py
	$(PY) artifacts/ingest_arena.py --check
# After the two seeders and before the export, because a row that arrived
# through the form is part of the corpus and the export reads the database
# once. This was a manual step for exactly as long as the falsifier failed any
# row with no local file, which every row from the form is.
	$(PY) artifacts/intake.py replay
# The prompt `/submit/` hands to a coding agent, built from the spec list and
# the values this corpus holds. After the replay, because a row that arrived
# through the form is one of the values it observes, and generated rather than
# written into the page because a second copy of a document that changes
# whenever a field does is a second copy that goes stale.
	$(PY) artifacts/intake.py prompt
	PYTHONPATH=src $(PY) -m controlbun.export
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
