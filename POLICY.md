# Dual use

**DRAFT. Not published.** Two kinds of section below and they are marked
differently, because one of them is not mine to write.

Sections marked **[verified]** describe what the system does. I checked each
claim against the running code and the built site on 2026-09-17, and the check is
noted under each one so you can rerun it rather than trust it.

Sections marked **[draft, yours]** are placeholder prose. They are positions
rather than facts, a reader will judge you by them, and you should rewrite or
delete them rather than approve them as they stand.

---

## The problem, in one paragraph

A steering direction that removes refusal and one that increases kindness are the
same kind of object. Same extraction, same schema row, same page. Nothing about
the structure distinguishes them, so a registry that makes artifacts findable and
reusable makes both findable and reusable. `BRIEF.md` puts it plainly: such a
registry is, among other things, a jailbreak distribution channel. And a blanket
ban is wrong, because persona-vector research legitimately publishes an `evil`
vector and safety work needs exactly these objects.

---

## What the registry holds [verified]

Eight submissions. Three are real and are the author's own directions; five are
fabricated fixtures that exist to exercise the interface and are marked as such
on every page that shows them.

Three labels: `kindness`, `refusal`, `pro-human`. Three kinds: `direction`,
`sae-latent`, `probe`. Three model ids, of which two are placeholders that do not
resolve to anything.

*Checked: `SELECT` against `registry.db` after `make site`.*

## What the registry does not do [verified]

This section is the substance, and most of it is a description rather than a
promise, which is the strongest form it can take.

**It serves no artifact bytes.** Zero rows have `served_repo` set. No
`.safetensors`, `.npz` or `.pt` file appears anywhere in the published site. The
bytes an artifact page describes live wherever its author put them, and the page
links there.

*Checked: `SELECT count(*) FROM intervention WHERE served_repo IS NOT NULL` is 0;
`find astro/dist -name "*.safetensors" -o -name "*.npz" -o -name "*.pt"` is
empty.*

**There is no API and no bulk fetch.** The site is a static build with no server
behind it. No endpoint returns a list of artifacts, and no machine-readable dump
is published. `src/registry/fetch.py` resolves one artifact at a time from an
explicit `author/label@version` reference, by commit SHA, and sends no
credentials.

*Checked: no `.json` in `astro/dist` outside the search index; `fetch.py` has no
listing function.*

**There is no rate limit because there is nothing to limit.** Static files. This
is a description of the current architecture and stops being true the day
anything is served dynamically.

**Nothing is ranked, and no popularity signal is collected.** Downloads and stars
render as "not tracked" rather than as zero, because a zero would be a
measurement claiming nobody had. No ordering anywhere derives from a measured
result. So there is no "most effective" anything to surface, by construction
rather than by restraint.

*Checked: `not tracked` in `SubmissionRows.astro` and `ArtifactCard.astro`;
invariant 4 in `tests/test_invariants.py` fails the build on an ordering derived
from an eval result.*

**There are no accounts and no uploads.** Nothing can be submitted today.

## What the search index covers [verified]

The site ships a client-side full-text index, 784 KB, covering the body of every
page. That includes author definitions, labels and attack methods. It is a
discovery surface over what concepts the corpus contains, and it is worth naming
here rather than discovering later, because it is the one part of the current
system that makes semantics searchable rather than merely present.

*Checked: `du -sh astro/dist/pagefind`.*

---

## What will be declined [draft, yours]

> Placeholder. This is the position, and it is the part that actually matters.
>
> A sketch of the shape, not the content: the useful version of this is narrower
> than "nothing harmful" and broader than "nothing illegal". It probably turns on
> whether an artifact is accompanied by the thing that makes it research rather
> than a tool, which is a stated purpose, an author who is identifiable, and
> evidence somebody could argue with. An `evil` persona vector published with a
> definition, an eval and a name attached is the Anthropic persona-vector paper.
> The same tensor posted anonymously with the label `jailbreak` is not.
>
> If that is the line, say it in your own words. If it is not, say what is.

## Who decides, and on what [draft, yours — partly settled]

Two criteria, and the list is closed. This much is already recorded in `V2.md`:

1. **Schema validity**, which is automated. `make verify` decides it and no human
   is involved.
2. **Dual use**, which is this document. This is the whole of the human judgment.

**Quality is not a criterion.** Not the clarity of a definition, not the adequacy
of the confound axes, not whether the vector looks any good. A submission that
passes the falsifier and this policy is published even if the reviewer thinks it
is weak, because the reviewer thinking so is an attack card they can publish like
anybody else.

That separation is the whole reason declining is compatible with the premise.
**Refusing to hold something is not the same as ranking what you hold.** The
registry never designates one artifact as the right one; it can still decline to
carry a class of thing. Only the first of those is the thesis.

## Decline reasons [draft, yours]

> Placeholder list. The set should be closed and published, and that is the one
> legitimate closed enumeration in this project: every other one would constrain
> contributors, and this one constrains the registry. Enumerating what we may
> refuse for is a limit on us.
>
> A published decline log, counts and reason category only and never the content
> of a declined submission, would make drift visible from outside rather than
> only to the person drifting.

## Gated access [open, needs a decision]

Unresolved, and it is one of the two genuinely open questions.

Hugging Face already solved a version of this: per-repo access requests,
controlled by the author, where a requester shares contact details and agrees to
terms. If artifacts stay on HF and this registry points rather than hosts, that
mechanism is available without building anything, and the decision belongs to the
author of each artifact rather than to us.

The moment this registry serves bytes itself, that stops being true and the
question becomes ours. `schema/migrations/004_served_copy.sql` says so directly:
serving a copy makes this a distributor rather than an index, and "we only
pointed at it" stops being available as an answer.

## Reporting [open, needs a contact]

There is no contact anywhere on the site today, which was flagged in the
first-visit review and is not fixed. A takedown path needs an address a person
can actually reach, and it should be the same one the site signs with.

---

## What this document is not

It is not a claim that anything here has been checked for safety. Nothing in the
registry is vetted, endorsed, or certified, and the absence of a decline is not
an approval. The registry records claims and the evidence for and against them;
it does not assert that any of them are true or that any artifact is safe to use.
