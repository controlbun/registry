# What this does, and what it does not

Facts about the running system, not commitments. Every claim carries the check
that produced it, so rerun them rather than trusting them. Last checked
2026-09-17 against `main`.

**This was drafted as a dual-use policy and is not one.** A policy governs
decisions, and there are none to govern yet: nothing can be submitted, nothing is
served, and the client sends no credentials at anything. `DECISIONS.md`
2026-09-17 records when that changes and why writing it earlier would be worse.

---

## What it holds

Eight submissions. Three are real and are the author's own directions; five are
fabricated fixtures that exist to exercise the interface and say so on every page
that shows them.

Three labels: `kindness`, `refusal`, `pro-human`. Three kinds: `direction`,
`sae-latent`, `probe`. Three model ids, two of which are placeholders that do not
resolve to anything.

*Check: `SELECT` against `registry.db` after `make site`.*

## What it does not do

Description rather than promise, which is the strongest form this can take.

**It serves no artifact bytes.** Zero rows have `served_repo` set. No
`.safetensors`, `.npz` or `.pt` file appears anywhere in the published site. The
bytes an artifact page describes live wherever its author put them, and the page
links there.

*Check: `SELECT count(*) FROM intervention WHERE served_repo IS NOT NULL` is 0,
and `find astro/dist -name "*.safetensors" -o -name "*.npz" -o -name "*.pt"` is
empty.*

**There is no API and no bulk fetch.** A static build with no server behind it.
No endpoint returns a list of artifacts and no machine-readable dump is
published. `src/registry/fetch.py` resolves one artifact at a time from an
explicit `author/model_id/label@version` reference, by commit SHA, sending no
credentials.

*Check: no `.json` in `astro/dist` outside the search index; `fetch.py` has no
listing function.*

**There is no rate limit because there is nothing to limit.** Static files. True
of the current architecture and false the day anything is served dynamically.

**Nothing is ranked and no popularity signal is collected.** Downloads and stars
render as "not tracked" rather than as zero, because a zero would be a
measurement claiming nobody had. No ordering anywhere derives from a measured
result. So there is no "most effective" anything to surface, by construction
rather than by restraint.

*Check: `not tracked` in `SubmissionRows.astro` and `ArtifactCard.astro`;
invariant 4 in `tests/test_invariants.py` fails the build on an ordering derived
from an eval result.*

**There are no accounts and no uploads.** Nothing can be submitted.

## What the search index covers

The site ships a client-side full-text index, 784 KB, over the body of every
page. That includes author definitions, labels and attack methods. It is a
discovery surface over what concepts the corpus contains, and it is the one part
of the current system that makes semantics searchable rather than merely present.
Named here because it is better named than found.

*Check: `du -sh astro/dist/pagefind`.*

## What this is not

Not a claim that anything here has been checked for safety. Nothing in the
registry is vetted, endorsed or certified. The registry records claims and the
evidence for and against them; it does not assert that any of them are true or
that any artifact is safe to use.
