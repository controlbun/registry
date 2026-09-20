# Working agreement

> **Status 2026-09-20.** Live. The working agreement, and the only document an
> agent is guaranteed to read. `DECISIONS.md` is authoritative where the two
> disagree, and this file does go stale against it: two paragraphs here forbade
> things the project had already decided to do, and were amended on 2026-09-20.

Project brief is in `BRIEF.md`. Settled decisions are in `DECISIONS.md`, which is
authoritative: do not contradict it, and add to it whenever something is decided.

**`DECISIONS.md` keeps superseded entries on purpose.** Check an entry for a
`**Superseded by:**` or `**Amended by:**` line before acting on it. Three of them
read as live rules when they are not: transfer as a required eval field, ranking by
precision and attack survival, and no default sort.

The count is not written here on purpose. It was, and it went stale the first time
an entry was superseded without anyone updating this paragraph.
`tests/test_decisions.py` checks the marking instead: every entry named in a
`**Supersedes:**` line has to carry the pointer back, which is the property that
actually matters.

## The premise, which you will violate by accident

**Plurality is the product. The registry never designates; consumers pin,
visibly.** Ten people extracting `kindness` with different contrast data,
different theories of the trait and different confound axes is the content, not a
duplication problem. The registry makes disagreement legible. It does not resolve
it.

Separate the two senses of "canonical" before flagging anything:

- **Designating** is the registry asserting one entry is the right one. Rejected.
- **Pinning** is a consumer freezing `author/model_id/label@version` for one
  purpose so its own numbers are comparable. Ordinary experimental control. Fine,
  and required. Arena seasons pin. Model revisions and judge models pin.

A pin must be named, cited and contestable. If the pin is invisible or presented as
the answer rather than a choice, it has become a designation.

This is the one thing that gets eroded, and it never erodes in one move. It goes
one reasonable local improvement at a time: scores should be comparable, so fix
the confound axes on the trait; users need to pick one, so rank them; quality
varies, so require a validation field. Each defensible alone. Together they delete
the thesis. The erosion is a ratchet and does not reverse on its own.

Two drivers worth knowing so you can catch yourself:

- **Optimizing for the reader who wants one answer, against the contributor who
  wants a voice.** A registry is contributor-first. Every time reader convenience
  wins, the design centralizes.
- **Reasoning from precedent.** Precedent shows the mature curated version,
  because open systems look like failures early. For a novel object, absence of
  precedent is not evidence against it.

### Trip-wire vocabulary

If you are about to write any of these about this project, stop and flag it before
continuing: *official, authoritative, verified, approved, certified, curated,
required field, mandatory, minimum bar, quality gate, threshold, default sort, the
best, gold standard, ground truth, consensus, supported methods, allowed values,
one of.*

A closed enumeration is the same failure at field level: `method: a / b / c`
declares which ways of doing the thing are legitimate. Document common values,
enforce none, and make extension points namespaced profiles that outsiders can
publish without asking.

"Canonical" is not on the list because it is ambiguous. Apply the designate/pin
test instead: is the registry asserting correctness, or is a consumer freezing a
reference for its own measurement? The first is the failure. The second is fine as
long as it is visible.

**"Better" is not on the list and "the best" is, and that gap is deliberate.**
There is always a better one for what somebody is doing. There is never a best
one. Better is a comparative a consumer makes for one purpose, which is pinning,
which is the product; best is a superlative the registry would be asserting for
everyone, which is designation. The founding sentence on `/about/` is "if I could
reuse someone else's **better** pro-human direction without the effort", so a
rule that forbade the comparative would forbid the reason this exists.

This is a trap for a word list rather than for a reader: banning the substring
catches the sentence the project was started over. A test in
`tests/test_situation_picker.py` did exactly that before it was corrected. Run
the designate/pin test on the sentence, not a grep on the word.

Some of these will survive scrutiny. None should pass without it.

### The inverse question, asked every time

Before proposing any constraint, state what it makes impossible to express. Not
what it improves. A proposal that cannot name what plurality it removes has not
been thought through.

### Invariants, executable not aspirational

Prose principles get pattern-matched away. Checkable ones do not. The arena's
`_falsifier/verify.py` is the right precedent: extend the habit from numbers to
design. Tests that fail the build:

- No schema field is both an eval result and `NOT NULL`
- No endpoint returns a single "best" submission for a label, and a bare label
  never resolves to one artifact
- Every pin records who pinned it, when, and what alternatives existed
- A default ordering is allowed, and must be named on screen and switchable. No
  ordering is ever derived from an eval result: trait, coherence, transfer and
  necessity scores are never sort keys
- Any label namespace permits an unlimited number of claimants
- A submission's key names its model, and no ordering is ever derived from
  `model_id`. The model is identity, not a rank of model families
- No ordering derives from whether an artifact is published anywhere. Having a
  URL is a fact about what the author did with the bytes, not a quality of the
  submission, and most rows will not have one. It is a filter a reader applies,
  never an order the page applies for them
- Absence of an eval renders as its own state, not as an error
- No closed enum on any user-supplied field. Document common values; reject none.
  Schema `CHECK` constraints listing permitted strings fail the build. This covers
  `kind`, `hook_point`, `profile`, method and **artifact file format**: a
  converter set is the same kind of thing, so shipping two converters is fine and
  refusing bytes because the format "is not supported" is not. Refuse what cannot
  be verified, and say that instead.
- A judged score renders with a coherence measure beside it or renders as
  uninterpretable, never as a bare number
- Cosine similarity is a displayed fact, never evidence of disagreement and never
  a sort key. Behaviorally indistinguishable vectors can sit far apart in angle
  (arXiv:2602.06801)
- A namespace claim is never an ordering, a filter, or a condition on publishing.
  Unclaimed is a state with its own words, and it is the ordinary one. A
  claim binds the provider's `sub` and never a renameable handle, a namespace
  takes more than one claimant, and an org membership renders as an observation
  with its date beside it rather than as a standing fact
- No page asserts a plurality the corpus does not hold. A label view counts
  people separately from submissions, so one author's four versions never render
  as four claimants, and any sentence about other claimants is computed from the
  data rather than written down. Absent plurality is a state with its own words,
  the same as an absent eval. Bound in `tests/test_pages.py`, because it is a
  rule about rendered output rather than about a construct in a template
- A check the corpus gives no instance of is proved by a probe, never left to
  pass quietly. `falsifier/verify.py` runs the synthetic-marker rule against two
  strings on every run, so the rule cannot go inert now that nothing in the
  corpus is fabricated
- The published site has no origin that receives, and every origin its own
  script can send a reader's data to is named in a test with the reason. The
  build emits files and runs no route, so nothing here can be posted to; since
  2026-09-20 the site is a client, and the question a guard asks is where a
  request is aimed rather than whether one exists. A new destination is a test
  edit, which is a decision somebody made rather than a line that arrived. A
  destination configured in markup counts: the project URL reaches the script
  through a `data-` attribute and was outside that enumeration until
  2026-09-20, so both the bundle and the built HTML are scanned, and a test
  asserts the scan finds a real one rather than matching nothing
- A submission's author is stamped by the database from the verified session,
  never read off the payload, and the browser builds those columns off the
  session for that reason. Where the stamped identity and the record's own copy
  disagree, the stamped one is used and the disagreement is surfaced rather
  than either being preferred silently
- One sign-in returns two credentials and they have opposite lifetimes. The
  Hugging Face `provider_token` is written to browser storage in no form and
  under no key: with `contribute-repos` it creates and writes repositories in
  somebody's own namespace, and it comes back on the sign-in itself and never on
  a renewal, so keeping it buys nothing past its expiry. The Supabase session,
  which row-level security scopes to inserting one row as its owner with no read
  of anyone else's and no update or delete policy at all, is the only credential
  kept, lives under one named key with its refresh token, and is removed by Sign
  out. Held across every file in `astro/src` by resolving each written key to
  the literal it is and refusing one nobody accounted for. What may be kept is
  the theme, the PKCE verifier and that session, and nothing else. This line
  read "nothing on this site writes a token to browser storage", which was true
  only because the session died with the tab, and the bar paid for it by
  offering Add artifact to readers whose session was already gone
- The bar never offers a way in that has nothing behind it. Add artifact renders
  only where the session in that browser still carries a refresh token, and a
  renewal the identity service refuses deletes the session and renders as its
  own state with its own words, never as an error and never as silence. Sign out
  says what it did and what it did not: it ends the session in this browser, it
  tells nobody, so the session is not revoked at the identity service, and the
  account at the provider is untouched
- Text a page hands a reader to run somewhere else is generated from the code
  that reads the answer back, never re-typed into a template, and a test pins
  the built page to that function's output for the same corpus. The prompt on
  `/submit/` is `agent_handoff.prompt(...)` written into `astro/src/data/` by
  `make site`, and its parser never crosses into the browser: one thing reads a
  format, the way one thing reads bytes. A paste is posted as text and checked
  when the author pulls it, and the page says that in those words rather than
  implying a check it does not do
- The bar's signed-in state never comes from anything the page asserts about a
  person. `SiteNav.astro` takes no props and reads nothing about the page it is
  on. A submission page knows an author's handle, so a bar that read its own
  page would greet a stranger by the name of whoever they were reading
- Every document says at the top whether it still instructs, and on what date it
  said so. `tests/test_doc_status.py` fails the build on a missing block, a date
  in the future, or one pushed below the first twelve lines. The word after the
  date is free prose and is not checked, because a fixed vocabulary of document
  states would be a closed enum on the one field here that is prose. A spent
  runbook that does not say it is spent gets run again, and two of the steps in
  the one this came from are not reversible
- Nothing reaches the deploy branch that the gate did not pass in the same run.
  `hooks/pre-push` runs `make verify` and diffs the pushed tree against the
  `astro/dist` that just passed, and that half binds only a push somebody made:
  in a checkout where `core.hooksPath` was never set, `git push` runs no hook and
  says nothing about it. So the one target that pushes checks the wiring before
  it pushes, runs the gate itself so a red one commits nothing, and refuses a
  checkout that is not on the source branch. No path anywhere passes
  `--no-verify`, and the scans that hold that read source with its comments and
  docstrings taken out, because the sentence stating a rule contains the rule's
  own spelling. Since publishing is automatic the gate is the only reader a
  submission gets, which is why it is a push-time property rather than a habit
- The automatic publisher stages by name and never `git add -A`. It refuses
  outright on a working tree carrying anything it did not write, and on a
  tracked file changing outside the three paths a pull plus a build touches. The
  owner works in this checkout, and a commit that swept up half of what he was
  in the middle of is worse than not publishing, because not publishing is
  visible in the log and that is not. Bound in `tests/test_autopublish.py`

Add one whenever a new invariant is settled. An invariant that is only in prose
is not an invariant.

### Premises live at the top of every document

A premise stated in one section will be violated in every other section. This is
observed, not hypothetical: the data model was rewritten for plurality and the
remaining six sections of `BRIEF.md` kept arguing for canonical traits, required
fields and ranking until they were audited. Restate the premise in each document's
opening, and when a premise changes, re-read the whole file rather than editing the
section that named it.

### The advocate role

The arena has `_advocate/`, which argues the opposing case. Keep the pattern here.
When a design decision is being settled, one pass should argue for the plural
reading explicitly, as a role rather than as a disclaimer.

## The object graph

`BRIEF.md` is authoritative on conflict. This is a map, not a spec.

- **Label**, namespaced `author/label`, free to claim, carries the author's own
  definition. A bare label is a computed view across claimants, owned by nobody.
  `interprets:` and `distinguishes-from:` pointers let taxonomy emerge from claims.
- **Submission**, the primary object. One author's complete take **on one
  model**, versioned and immutable. `author/model_id/label@version` resolves to
  one frozen submission forever: `soham/allenai/Olmo-3-1125-32B/pro-human@meandiff`.
  The model is part of the identity because an intervention is a tensor in one
  model's residual basis, so one author holding one label on several models holds
  several submissions and all of them stand. Parsing takes the first segment as
  the author and the last as the label, so a model id of any depth sits in the
  middle and `gpt2` with no distributor works. The short `author/label@version`
  still resolves while it names one submission and raises naming the alternatives
  when it names more. **This is identity and nothing else.** It is not a filter,
  not an ordering and not a facet that ranks, and nothing may read as one model's
  directions being the real ones.
- **Recipe**, optional. Declares a namespaced versioned `profile` plus a payload,
  plus a pinned entrypoint and container digest. Never a method list.
- **Intervention**, the artifact. Open `kind`, model id plus revision, layer with
  stated indexing convention, open `hook_point`, chat template hash, norms,
  `license_status`. safetensors on ingest, always.
- **EvalSuite**, authored and pointable at anyone's submission. **Attack** is the
  adversarial case of the same mechanism, with attacker and author dispositions
  both displayed.
- **SupportCard**, applied use rather than evaluation. Somebody pinned a version,
  used it in their own work, and reports whether it behaved the way the published
  contract said it would. `expected` is required and `observed` is not, which is
  what keeps it from becoming a star rating.
- **Comparison**, derived and never authored. The asymmetry in which confound axes
  each author checked is the informative cell.
- **Run** and **Reproduction**, provenance, and a reproduction reports its delta
  rather than a pass.

v0 is schema, storage on the HF Hub, SQLite metadata, Python client, Comparison,
views, and the ported falsifier.

**The corpus is real and there is no seed set.** This read "build against
fixtures labeled synthetic, seed with competing claimants on one label", which
was right while the site was private and became the wrong instruction the moment
it was about to be published: a corpus that is half fabricated invites "is this
real" from exactly the readers it is for. `DECISIONS.md` 2026-09-19 removed it.
What the corpus holds is five real submissions by one author, so **no label has
more than one claimant and the plurality premise is demonstrated zero times.**
That is a fact about a new registry, and the pages say it rather than implying
otherwise. Do not fabricate a second claimant to make a view look populated.

The states the checks still need, two people disagreeing on one label, an attack,
an uninterpretable score, live in `tests/probe.py`, which the tests build and the
site never sees. Put a new one there, never in the corpus.

## Before writing any code

The data model and v0 scope are agreed enough to build against. Propose the
structure, wait for a yes, then build. Do not run a project initializer or create a
directory tree on your own initiative.

This paragraph used to say v0 accepts no uploads and serves nothing publicly, and
both halves are now false. The site is live at `controlbun.com` and a submission
posts to Postgres with the identity stamped there. What changed it is in
`DECISIONS.md`: 2026-09-19 "No dual-use policy is required", which lifted the
triggers the old sentence hung on, and 2026-09-20 "A submission is a link".
Amended here rather than left to be discovered, because an agent reading a stale
prohibition stops instead of asking.

What survives: no public API and no bulk fetch. Those were never consequences of
the dual-use policy. They are the misuse surface named in the Safety section
below, and nothing has decided them.

## Working style

Write in my voice, not yours. For anything a human will judge me by, a README, a
launch post, docs, an email to a collaborator, do the structure and the accuracy
check and leave the prose to me. Lead with the result. Do not narrate process or
mistakes as a headline.

No em dashes. US spelling. State a rule once and I will not repeat it.

Push back where my framing is wrong. State the disagreement once with reasoning,
then execute my decision without relitigating it.

The v0 scope is fixed. Do not build toward v1 or v2. If you think v0 needs
something, say so and wait.

## Never fabricate numbers

This project's value proposition is trustworthy eval scores. Never invent a trait
score, coherence score, benchmark delta, cosine similarity or any metric, including
as example data, placeholder content or test fixtures. If a fixture needs numbers,
make them obviously synthetic and label them so in the file. Never put a
plausible-looking score in a README or a screenshot.

Same for empirical claims about methods. Cite the paper or say it is inference.
Secondhand claims from research summaries are not citations. If a claim matters,
read the source before it goes in a document.

## Verification over recall

Do not write code against remembered APIs. nnsight, TransformerLens, HF Hub and the
steering libraries move fast. Check the installed version's real signatures first
and show me what you checked.

Same for platform facts: Hub storage and LFS limits, rate limits, hosting costs,
model licenses. Run the command or fetch the page.

## Reproducibility

This is a tool about reproducibility, so it has to be exemplary. Pin every
dependency, record seeds, container digests and git SHAs, and keep every script
rerunnable from a clean checkout. Flag anything that is not reproducible rather
than shipping it.

## Legal, before it is expensive

**Working position, the author's: a direction is his own work, built by a user
against a model rather than derived from the model.** He wrote the contrast
prompts, chose the layer and the estimator, and did arithmetic on activations he
elicited. The result carries no weights and cannot reconstruct any.
`DECISIONS.md` 2026-09-19 records it with the case against it, the licenses it was
checked against and what it forecloses. It is a position and not legal advice,
nobody has litigated it, and whether weights attract copyright at all is contested.

This sentence used to read that a vector **is** derived from model weights and
that redistributing one **may be** constrained. The hedge was right and its
premise was not, so the premise moved and the hedge stayed: a source model's
license may still reach an artifact, because some of them define derivative work
broadly enough to argue about, and an author who wants to redistribute should read
the source license rather than rely on this file.

So: read the source model's license, record what it says in that artifact's
`license_status` with the URL and the date it was read, and record what is
unresolved as unresolved. That is a per-artifact fact its author asserts. It is
not a gate applied to a model family, and there is no list of families this
project carries. The registry indexes what people submit; where bytes cannot be
redistributed it points and does not serve, which is the structure it already has.

Check dependency licenses. Flag copyleft.

## Safety

Flag any feature that increases misuse surface, especially anything that makes
refusal-removal or malicious-persona artifacts easier to find, fetch in bulk, or
apply. That obligation is the part that matters and it stands unchanged.

The sentence that used to follow it, that the dual-use policy is a launch blocker,
does not. `DECISIONS.md` 2026-09-19 decided no such policy is required and lifted
the capability triggers. Nothing waits on it, which also means nothing is excused
by it: a feature that widens misuse surface still gets flagged, and now there is
no document to point at instead of thinking about it.

Note the tension with the plurality premise and do not resolve it silently: open
contribution and misuse gating pull against each other. Where they conflict, raise
it rather than quietly choosing one.

## Manifests and timestamps

The manifests are a closed set. They are notarized records of past doc states, not
a live check, and nothing here is restamped as docs change. `shasum -c` against any
of them is expected to disagree with the working tree, and that disagreement is not
an error to fix. Git tracks the edits. The stamps exist to date the design.

**Every manifest name carries the date and time it was stamped.** A new snapshot
therefore never collides with an old one, `ots stamp` never hits its
refuse-to-overwrite, and no proof is ever discarded to make room for another.

What each one attests:

- `MANIFEST-a` and `-b`, earliest states of the design docs, anchored in Bitcoin
  blocks 966590 and 966592
- `MANIFEST-c`, an intermediate state, anchored in blocks 966605, 966608 and 966636
- `MANIFEST_FINAL_<date>_<time>`, all tracked docs at that moment
- `MANIFEST_BRIEF_<date>_<time>`, `BRIEF.md` alone, so the brief can be handed to
  someone and dated without disclosing the rest of the set

The newest pair of each is the current record; earlier ones are superseded
snapshots and are expected not to match the tree. `ls MANIFEST_*` shows the series.
Do not enumerate individual stamps here, or this section needs editing every time
one is made, which invalidates the stamp being made.

Never regenerate any of them, and never rewrite one to make a checksum verify.
Rewriting an anchored proof's manifest orphans the proof, which is the only thing
it is for. `.ots.bak` files are the pre-upgrade proofs `ots upgrade` sets aside.

To date a new state, stamp a new pair under a new timestamped name rather than
touching an existing one, and leave it alone until `ots upgrade` anchors it.

```
ots info <manifest>.sha256.ots      # offline, shows what a proof attests
ots upgrade <manifest>.sha256.ots   # network, pending proofs only
```

## Repo

`github.com/controlbun/registry`. Public, and the site is served from it.

This section used to read "Private ... no Actions, no public push, no `gh`
workflows", which was right for an off-site backup and incoherent for a repo that
publishes a website. Amended deliberately rather than discovered mid-build, per
the obligation recorded in `DECISIONS.md` 2026-09-13. Most of it survived; what
changed is marked.

**Write nothing that would need a history rewrite to remove.** This was a
precaution and is now a fact: every commit is readable by anyone. Personal,
financial and immigration details stay out of the repo entirely. Secrets live in
`.env`, gitignored before the first file existed. The audit that checks this runs
against the tip rather than the working tree, because publishing exposes every
commit and not just the last one, and **its result is dated rather than
permanent**: re-run it before any change in visibility and record the date. The
most recent one is in `minor_updates.md`.

Private working material goes in `_local/`, which is gitignored and never
committed. Do not copy anything out of it into a tracked file. This matters more
now, not less.

**No Actions, and nothing on GitHub builds anything.** The prohibition on a public
push is gone; the prohibition on a hosted build is not, and the reason it existed
is unchanged. The falsifier and the invariant tests run in a local gate, `make
verify` plus a pre-push hook, both tracked so a collaborator inherits them.

Pages deploys from a branch carrying a locally built `astro/dist`. So what is
served is the artifact that passed `make verify` on a machine, rather than
whatever a runner produced from the same source. That equivalence is the whole
point, and an Actions-based build would break it quietly: the falsifier would be
checking one build and readers would be reading another.

**Publishing also makes `_attest/` checkable by anyone**, rather than by anyone
who is handed the files, which is most of what the proofs are for.

Do not re-raise CI, Actions or a hosted build as a finding. Settled twice, once
as a backup and once as a published site.
