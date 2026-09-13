# Minor updates

One line per change too small for `DECISIONS.md` and not worth editing `CLAUDE.md`
for. Newest last. Editing `CLAUDE.md` invalidates the manifests; this file is where
that churn goes instead.

- 2026-09-12 Manifests and proofs moved from the repo root to `_attest/`. Verify from the repo root, e.g. `shasum -a 256 -c _attest/MANIFEST_FINAL_2026-09-12_0020.sha256`, since `shasum -c` resolves listed paths against the working directory and not the manifest's location.
- 2026-09-12 Seed documents are direction, not specification. `BRIEF.md`, `DECISIONS.md` and `VALIDATION.md` inform intent; they are not a spec to conform to and their inconsistencies are not defects to reconcile before building. The tests in `tests/test_invariants.py` remain hard constraints, which is the whole reason the premise survives the docs being loosened.
- 2026-09-12 Stamping is not repeated for document changes. The anchored manifests date the design; git history carries everything after, and editing `CLAUDE.md` no longer implies a restamp.
- 2026-09-13 Two frontends exist: `web/templates/` (Jinja, rendered by `src/registry/render.py`) and `astro/`. Astro is what `make site` builds and what the falsifier checks; the Jinja one is only reached by `tests/test_render.py` and still carries the between-claimants table that was removed from Astro. Decide whether to retire it or bring it forward.
