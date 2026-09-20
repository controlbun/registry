# Local build gate. These targets are the enforcement, and `make hooks` wires them
# to pre-push so they are not optional.
#
# This used to say there is no CI because the repo is not on GitHub. The repo has
# been on GitHub since 2026-09-19 and there is still no CI, which is now a choice
# rather than a circumstance: Pages serves a locally built `astro/dist`, so the
# artifact a reader gets is the one that passed this gate, and a hosted build
# would quietly break that by having the falsifier check a different build.

PY := .venv/bin/python
UID := $(shell id -u)
AGENT := com.controlbun.autopublish
AGENT_PLIST := $(HOME)/Library/LaunchAgents/$(AGENT).plist
JOB_DIR := $(HOME)/Library/Logs/controlbun

.PHONY: verify test invariants manifests hooks site licenses serve falsifier links \
        pull pull-dry deploy autopublish-install autopublish-stop autopublish-now

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

# --------------------------------------------------------------------------- #
# What `/submit/` received, onto the site, with nobody typing anything.
#
# `artifacts/AUTOPUBLISH.md` is the operator document. It carries the Keychain
# line, the log path, how to stop this and how to take something down.
#
# `pull` is deliberately not a prerequisite of `site`, and that has not changed.
# `site` runs inside `verify` which runs in the pre-push hook, so a network call
# needing a secret there would break the build for anyone without the key and
# make it depend on a remote service being up.

# The secret key comes from the login Keychain and from nowhere else. It is put
# into one child process's environment, and `artifacts/intake.py` reads it from
# the environment and from nowhere else.
pull:
	$(PY) artifacts/autopublish.py pull

pull-dry:
	$(PY) artifacts/autopublish.py pull --dry-run

# The sequence `GO-LIVE.md` section 4 has typed by hand. Runs `make verify`
# itself, then pushes `main` and `gh-pages` in one invocation so the hook runs
# the gate once more and diffs the pushed tree against the `astro/dist` that
# just passed. Never `--no-verify`: a locally built `astro/dist` is the whole
# argument for having no hosted build, and pushing past the gate deletes it.
deploy:
	$(PY) artifacts/autopublish.py deploy

# Writes into ~/Library/LaunchAgents, which is why it is a target the owner runs
# rather than something a script did on its own. `bootout` first, so reinstalling
# over a loaded agent replaces it instead of failing.
autopublish-install:
	mkdir -p $(JOB_DIR) $(HOME)/Library/LaunchAgents
	$(PY) artifacts/autopublish.py plist > $(AGENT_PLIST)
	plutil -lint $(AGENT_PLIST)
	-launchctl bootout gui/$(UID)/$(AGENT) 2>/dev/null
	launchctl bootstrap gui/$(UID) $(AGENT_PLIST)
	@echo "installed. It fires every 15 minutes, starting within 15 minutes."
	@echo "log: $(JOB_DIR)/autopublish.log"

autopublish-stop:
	launchctl bootout gui/$(UID)/$(AGENT)
	@echo "stopped. The plist is still at $(AGENT_PLIST); delete it to be sure."

autopublish-now:
	launchctl kickstart -p gui/$(UID)/$(AGENT)
