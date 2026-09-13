# Minor updates

One line per change too small for `DECISIONS.md` and not worth editing `CLAUDE.md`
for. Newest last. Editing `CLAUDE.md` invalidates the manifests; this file is where
that churn goes instead.

- 2026-09-12 Manifests and proofs moved from the repo root to `_attest/`. Verify from the repo root, e.g. `shasum -a 256 -c _attest/MANIFEST_FINAL_2026-09-12_0020.sha256`, since `shasum -c` resolves listed paths against the working directory and not the manifest's location.
- 2026-09-12 Seed documents are direction, not specification. `BRIEF.md`, `DECISIONS.md` and `VALIDATION.md` inform intent; they are not a spec to conform to and their inconsistencies are not defects to reconcile before building. The tests in `tests/test_invariants.py` remain hard constraints, which is the whole reason the premise survives the docs being loosened.
- 2026-09-12 Stamping is not repeated for document changes. The anchored manifests date the design; git history carries everything after, and editing `CLAUDE.md` no longer implies a restamp.
- 2026-09-13 The Jinja frontend is retired. `web/templates/` and the HTML-emitting half of `src/registry/render.py` are deleted; the shared view logic moved to `src/registry/views.py` and the ordering display names to `src/registry/order.py`. Astro is the frontend.
- 2026-09-13 The repo section of `CLAUDE.md` is scoped to a private backup and needs amending when the repo goes public, because GitHub Pages publishes from a branch or an Actions workflow and that section currently rules out both. Recorded here rather than edited in, so the manifests stay valid until the amendment is actually made.
