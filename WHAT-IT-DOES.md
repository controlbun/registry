# What this does, and what it does not

Facts about the running system, not commitments. Every claim carries the check
that produced it, so rerun them rather than trusting them. Last checked
2026-09-20 against `main`.

**This was drafted as a dual-use policy and is not one.** A policy governs
decisions, and the decisions it would govern still do not exist. Something can
be submitted now, and no decision was added with it: nothing is approved,
rejected, ranked or ordered, because the namespace is the sender's own handle
and there is no question for anybody to answer about it. `DECISIONS.md`
2026-09-19 records that no policy is required and that what a review step does,
if there is ever one, is a separate question that this did not answer.

---

## What it holds

Five submissions, all real, all the author's own directions. The five fabricated
fixtures that used to sit beside them were removed on 2026-09-19, because a
public site whose corpus is half invented invites "is this real".

Two labels, `pro-human` and `trauma`. One kind, `direction`. Two model ids, both
of which resolve. **No label has more than one claimant**, so the plurality this
registry is for is a mechanism here rather than something on display.

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

**There is no API over the corpus and no bulk fetch.** The site is a static
build with no server behind it. No endpoint returns a list of artifacts and no
machine-readable dump is published. `src/controlbun/fetch.py` resolves one
artifact at a time from an explicit `author/model_id/label@version` reference,
by commit SHA, sending no credentials.

The one endpoint this project owns is the Supabase table a submission is sent
to, and nothing about the corpus goes through it. A signed-in person can insert
their own row and read their own rows back; there is no policy that lets anybody
read anybody else's, and no update or delete policy exists, so neither is
possible with the key the site carries.

*Check: no `.json` in `astro/dist` outside the search index; `fetch.py` has no
listing function; `schema/supabase/001_pending_submission.sql` has one insert
policy and one select policy, both scoped to `auth.uid()`.*

**Reading is anonymous and nothing meters it.** Browsing, comparing, following a
pin and fetching an artifact send no credential and go through no account. The
only thing signing in permits is sending a submission.

*Check: `tests/test_signed_in_page.py` fails the build if an identity endpoint
appears on any page other than `/signed-in/`.*

**There is no rate limit on the site because there is nothing to limit.** Static
files. True of the current architecture and false the day anything is served
dynamically. The submission endpoint is a different thing and whatever limits
Supabase applies to it are Supabase's rather than this project's; nothing here
has been configured or measured, so nothing here is claimed.

**Nothing is ranked and no popularity signal is collected.** Downloads and stars
render as "not tracked" rather than as zero, because a zero would be a
measurement claiming nobody had. No ordering anywhere derives from a measured
result. So there is no "most effective" anything to surface, by construction
rather than by restraint.

*Check: `not tracked` in `SubmissionRows.astro` and `ArtifactCard.astro`;
invariant 4 in `tests/test_invariants.py` fails the build on an ordering derived
from an eval result.*

**This registry receives no artifact bytes, and a submission is a pointer.**
Identity is Hugging Face's, and this registry issues no password. Somebody who
signs in at `/signed-in/` can send one submission: a pointer to bytes in their
own account, plus the contract describing them. The bytes stay where their
author put them. Nothing sent appears on the site until the corpus is rebuilt
and published, which is what lets the falsifier check the build readers read.

*Check: `SELECT count(*) FROM intervention WHERE served_repo IS NOT NULL` is 0,
which holds for rows that arrived this way as well as for the seeded ones.*

**Who a submission is from is stamped by Postgres, not claimed by the sender.**
The insert policy on `pending_submission` refuses any row whose account,
subject or handle disagrees with the verified session, so a submission cannot
claim to be from somebody it is not. There is no review step behind that and
nothing to approve: the namespace is the handle the provider reported, so there
is no question for a reviewer to answer, and nothing in the table is ranked,
counted or ordered.

*Check: `schema/supabase/001_pending_submission.sql`, and
`tests/test_pending_submission.py`, which fails the build if the policy stops
binding all three columns.*

*Accuracy note, 2026-09-20, prose left to the author: this paragraph has been
wrong twice in two days and both are worth seeing. It read "There are no
accounts and no uploads. Nothing can be submitted", which stopped being true
when `/signed-in/` shipped, and then "issues no account and receives no upload
... a file the submitter hands over", which stopped being true the same day when
the form started posting. `DECISIONS.md` 2026-09-20 has both changes.*

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
