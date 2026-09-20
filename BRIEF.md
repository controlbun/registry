# Project brief: a registry for steering vectors

Working title: undecided, and deliberately so. Deferred until it is known whether
this lives inside an existing ecosystem's naming conventions.

See `CONTEXT.md` for compute, upstream state and prior art. See `VALIDATION.md` for the
direction-validity problem, which is the research core of this project.

---

## The prompt

> I'm building a public registry for activation-steering artifacts, in the spirit
> of GitHub or Hugging Face rather than a curated database. Two premises shape it.
>
> **A vector is not portable, but a recipe is.** A steering vector is a tensor in
> one model's residual basis at one layer, so a `kindness` vector for Qwen2.5-7B
> does nothing for OLMo 3 7B. What travels is the extraction recipe: the contrast
> data, the author's definition of the trait, the layer sweep, the evaluation.
>
> **Plurality is the product.** Ten people will extract `kindness` with different
> contrast data, different theories of what kindness is, and different ideas about
> what could be confounding it. The registry holds all ten side by side and makes
> the disagreement legible. It does not pick a winner, mandate a definition, or
> impose a single evaluation. The primary object is a **Submission**: one author's
> complete take, self-contained, comparable to others after the fact rather than
> conformant to them in advance.
>
> Help me design and build this. Start with the data model and the v0 scope. Push
> back where my framing is wrong.

---

## Origin

This project came out of trying to attack the arena's own premise. In the author's
words:

> idea came when i was thinking of critizing my pro human directing actually
> represents that direction and if i could reuse someone elses better pro human
> direction without the effort

That is the whole problem in one sentence, and the sharp version is not that the
arena's direction is unvalidated. It is heavily validated: orthogonalized against
length, sentiment and action-vs-inaction; held-out separation 1.00; control-pair
transfer; a causal steering test against norm-matched random directions, half of
which was withdrawn when a fixed-baseline re-analysis failed to support it. More
evidence than most published directions carry.

**And it is still not enough, and none of it is reusable.** Certainty does not
arrive at the end of a good audit. There is no way to check the result against
someone else's take on the same construct, and no way to adopt a better one without
redoing every step. The gap is comparison and reuse, not rigor.

Keep this framing when explaining the project: "I audited my own direction about as
hard as anyone does, and I still could not tell whether someone else's was better,
or borrow it if it was." That is the honest account and a stronger opening than any
pitch about infrastructure.

---

## Relationship to Steering Arena

Steering Arena (`github.com/soham-padia/steering-arena`, deployed as a HF Space,
model served on NDIF via NNsight) is upstream of this project and already exists.
In the arena, a direction `d` is **given**: fixed, public, frozen per season.
Players submit token sequences and the server scores how far each shifts the
model's state along `d`, averaged over frozen probe prompts across a layer band.
SCORE 2 takes the weakest layer over a wider band, so a sequence that only moves
`d` where it was optimized scores near zero there. SPEC reports how much of the
movement is specifically along `d` versus movement anywhere.

**The arena tests sequence validity. The registry has to test direction validity.**
These are different objects and the arena's instruments do not transfer to the
second problem. That distinction is the reason this is a separate project rather
than an arena feature, and it is the thing to get right before any schema is final.

**The two stay separate, connected by a dependency rather than shared code.** The
arena becomes the registry's first consumer: each season pins one claimant, cites
it, and links to the entry showing what it was picked over. The arena gets a
defensible `d` instead of an asserted one; the registry gets a real consumer and a
concrete demonstration that plurality is useful rather than merely tolerant. One
documented interface, no shared implementation.

Two further reasons for the separation, both practical. The arena is becoming a
lab-hosted project with prize money, so anything bundled with it inherits lab
governance and blurs ownership of the registry. And the dual-use surfaces compound
badly if merged: an anti-human board plus artifact distribution is a much harder
policy problem as one project than as two.

What the arena already provides that v0 can build on:

- 135 contrastive seed pairs, published as `seed-pairs.jsonl`
- A frozen 16-prompt probe set (`data/probes/season3.json`, per season)
- A layer sweep with a confound audit per candidate direction
  (`data/directions/`)
- Cached generations for the behavior study, so re-judging costs no compute
  (`data/cache/`)
- `_falsifier/verify.py`, which re-derives every published number from raw
  artifacts and exits non-zero on drift
- `_advocate/`, which argues the opposing case

The falsifier pattern is the single most reusable thing here. Port it: every
published eval number in the registry should be re-derivable from raw artifacts by
a script that fails loudly, not by trust in a database row.

---

## Why this shape

The naive version, a bucket of `.pt` files with a README, fails for three reasons:

1. **No cross-model reuse.** Every model needs its own extraction. A file bucket
   has an N x M cold-start problem with nothing to amortize it.
2. **No way to tell a real vector from a spurious one.** Mean-difference extraction
   cheerfully encodes "uses the word *lovely*," "hedges more," or "writes longer
   sentences" instead of the trait you named. A `kindness` vector and a `verbosity`
   vector can be indistinguishable from their metadata alone.
3. **Silent misuse.** Layer indexing conventions, hook points, chat templates and
   coefficient scales differ between libraries. A vector downloaded without that
   metadata will be applied wrong and appear to "not work."

Carrying the recipe alongside the artifact addresses the first and third: a recipe
fans out to new models, and the application contract is declared once in a schema.

The second is not fixed by any schema, and pretending otherwise is the trap. No
required eval field makes a direction valid, because the author writes the eval.
What the registry can do is make each author's evidence and each author's blind
spots visible next to everyone else's, so a reader sees which confounds one person
checked and another did not. **Validity is a conversation the registry hosts, not
a property it certifies.**

---

## Data model (first draft, challenge this)

**Design premise: the registry never designates; consumers pin, visibly.**

Two senses of "canonical" need separating, because conflating them makes the
premise sound more radical than it is.

- **Canonical-as-authority.** The registry asserts that one direction *is*
  kindness and the others are wrong or secondary. **Rejected.**
- **Canonical-as-fixed-reference.** A consumer says: for this measurement I use
  this exact tensor, held constant, so numbers are comparable. That is ordinary
  experimental control. **Fine, and necessary.**

The arena needs the second and must not claim the first. It freezes a `d` per
season because scores across players have to be commensurable, the same way one
pins a model revision or a judge model. Every season should declare
`d = author/model_id/label@version`, immutable for the season, chosen and cited,
with the alternatives it was picked over visible. A season page saying "the
pro-human direction" is doing the thing the premise rejects. A season page saying
"this season uses `soham/allenai/Olmo-3-1125-32B/pro-human@meandiff`, over these
three alternatives, for these reasons" is doing the registry's work.

So, precisely:

- The registry **never designates**. No entry is official, no default resolution
  for a bare label, no single answer to "give me kindness."
- Consumers **pin**. A local choice with a name attached, not a global fact.
- Pins are **visible and contestable**.

**And plurality is the product.** GitHub does not arbitrate what
"react" means, it has `facebook/react`. Hugging Face does not pick the canonical
sentiment model, it has hundreds. Neither curated its way to usefulness, and a
registry that decided in advance what `kindness` means would be a worse object
than one that holds ten disagreeing answers side by side. Ten people extracting
kindness with different contrast data, different theories of the trait, and
different confound axes is the interesting first page, not a duplication problem.

The consequence: **comparability is computed rather than imposed.** Earlier drafts
declared confound axes on a curated Trait so scores would be comparable across
recipes. That inverts the point. Authors declare their own axes; the registry
derives relationships between submissions after the fact.

**Label**, a claim, not an authority.
Namespaced `author/label`, e.g. `soham/kindness`. Anyone can claim any label.
A label carries the author's own natural-language definition of what they mean by
it, which is load-bearing twice over: it feeds contrast-pair generation, and it is
the thing other authors disagree with. The bare string `kindness` is a **view**
across every submission claiming it, computed on demand, owned by nobody.

Optional `interprets:` pointers to other labels the author considers the same
thing, and `distinguishes-from:` pointers to labels they consider different. This
is how the taxonomy emerges, from claims rather than from a committee.

**Submission**, the primary object. One author's complete take: a label, a
definition, a recipe, the resulting intervention for one or more models, an
evaluation the author chose, and whatever confound axes the author thought to
check.

A submission is self-contained and internally consistent. It does not have to be
consistent with anyone else's. What it must be is *legible*: enough declared
metadata that another submission can be compared against it mechanically.

**A submission is identified by author, model, label and version, in that
order.** `soham/allenai/Olmo-3-1125-32B/pro-human@meandiff`. The model is part of
what a submission *is* rather than an attribute hanging off it, because a vector
is a tensor in one model's residual basis and a `kindness` direction for one model
does nothing for another. One author holding one label on several models holds
several submissions; none supersedes the others and none is the real one. The
model id is the full distributor-and-name string the extraction loaded, and is an
open string like everything else here: a model with no distributor is a single
segment and parsing recovers the model as everything between the author and the
label rather than by counting them.

**This widens an identity and adds nothing else.** Not a filter, not an ordering,
not a facet that ranks. The same label on two models is two submissions that both
stand, exactly like two authors on one label.

**Submissions are versioned and immutable, and the version is what a pin targets.**
`soham/allenai/Olmo-3-1125-32B/pro-human@meandiff` resolves to exactly one frozen
submission forever. An author revising after an attack publishes a new version;
the old one stays fetchable, because a season or a paper that pinned it must keep
resolving. Without this, pinning is not possible and every citation rots.
Superseded versions stay visible and link forward, since the revision history is
part of the evidence. A take on another model is not a revision of this one.

**Recipe**, how the intervention was produced. Versioned, belongs to a submission,
**optional**.

Optional because a direction someone has the tensor for but not the procedure is
still a submission. A 2023 paper's published vector with no reproducible code is
worth holding. The missing recipe renders as absent, per the same rule that covers
a missing eval.

A closed list of methods would be a designation in miniature: it would declare
which ways of making a direction are legitimate, and whoever invents the seventh
would have nowhere to put it. So a Recipe declares a **profile** it follows, plus a
payload that profile understands.

- `profile`: namespaced and versioned like everything else, e.g.
  `soham/contrastive-v1`
- `payload`: whatever that profile specifies
- Entrypoint: a pinned library + version and a container digest, so the run is
  rerunnable regardless of profile
- **The author's stated theory of the trait, in prose.** Required by convention
  across every profile, because it is what makes a disagreement between two
  submissions interpretable rather than just a number gap.

The registry validates that a reproducible entrypoint exists. It does not validate
that the method is on a list, because it does not keep a list.

**`soham/contrastive-v1`**, the first profile, shipped as an example rather than a
standard. Its payload:

- Contrast-pair source: uploaded dataset, or a generator prompt + generator model
  + seed
- Method within the contrastive family: `diffmean`, `caa`, or anything else the
  author names in prose
- Token masking policy: prompt-only, response-only, last-token, all
- Layer sweep range and the selection criterion

Profiles other people will plausibly need, and should publish themselves rather
than petition for: unsupervised discovery, SAE latent selection, probe training on
a labeled corpus, direction arithmetic over existing submissions, and
imported-from-paper with no procedure.

Consequence for Comparison: within a shared profile it can compute a great deal;
across profiles much less, falling back to behavioral measures and cosine
similarity. Comparability is earned rather than mandated here too.

**Comparison**, derived, never authored. Computed between any two submissions that
share a model, a label claim, or an evaluation set. Not a ranking.

- Cosine similarity between interventions on the same model and layer, **displayed
  as a fact and not as evidence of disagreement.** See the identifiability section
  in `VALIDATION.md`: behaviorally indistinguishable vectors can be far apart in
  angle, so a low similarity is not by itself a finding
- Agreement on any evaluation prompts both submissions happen to share
- Behavioral correlation when both are applied to the same held-out prompts
- Which confound axes each author checked, and which one checked that the other
  did not. The asymmetry is the most informative cell in the table.
- Where they diverge, and on which axis

Two submissions claiming `kindness` that diverge on shared evals or on collateral
axes is a finding, and the registry's job is to surface it rather than to decide
which is right. Geometric distance alone is not that finding.

**EvalSuite**, authored, attachable, reusable.

An author writes an evaluation and may point it at their own submission or anyone
else's. Evaluations are not owned by labels. Running someone else's eval against
your submission, or yours against theirs, is a first-class action and the main
mechanism by which comparability accumulates without being mandated.

Contents are the author's choice. What follows is a suggested starting set, not a
required schema. An author who omits a field is making a visible statement about
what they did not check, which is more useful than a mandatory field filled in
badly.

- Holdout questions, ideally not in the contrast pairs
- Judge model + rubric. Pinned as weights with a revision, not an endpoint, or the
  score stops being reproducible.
- Coherence measure. Steering hard enough breaks fluency, so effect size without
  a fluency measure is close to meaningless.
- **Confound axes, author-declared.** Sentiment, verbosity, formality, refusal
  rate, benchmark delta. Nobody dictates the list. What the registry does is show
  which axes you checked next to which axes someone else checked, so the gaps are
  visible rather than assumed away. Note the prompt-bucket confound in
  `VALIDATION.md`: a direction may encode which system-prompt condition the model
  is in rather than the trait, and few authors will think to check it.
- **Out-of-template transfer**, per `VALIDATION.md`. Held-out scores on prompts
  resembling the contrast pairs are weak evidence. Transfer to structurally unlike
  prompts is stronger. Strongly encouraged, surfaced prominently when present and
  when absent, not enforced.
- Coefficient sweep curve, not a single point

**Intervention**, the artifact itself, output of (Recipe x Model x Run).

Named Intervention rather than Vector deliberately. An intervention is *where to
hook, what to do there, and how to scale it*. A residual direction, an SAE latent,
a probe, a ReFT edit and a LoRA adaptor all fit that shape, so v3 method pluralism
costs a `kind` field instead of a rewrite. It also makes a Concept Slider a valid
artifact type in this registry, which is worth raising with the Concept Sliders
authors (arXiv:2311.12092). Noted as convergent rather than as a source; see
`VALIDATION.md`.

- `kind`: an open string. `direction`, `sae-latent`, `probe`, `reft` and `lora` are
  the ones with client support today, not the permitted set. An unrecognized kind
  is storable and displayable, and simply has no apply path in the client until
  someone writes one. v0 only *applies* `direction`, but the field is open and
  exists from the first migration.
- `model_id` **plus pinned revision/commit**. Base vs instruct is a different
  model; so is a different revision.
- `layer` with **explicit indexing convention**, 0-indexed transformer block,
  stated in the schema rather than the README
- `hook_point`: an open string, with `resid_pre`, `resid_post`, `mlp_out` and
  `attn_out` as the common values rather than the allowed ones. Adopt nnterp's
  standardized module naming if it covers the case; architectures have hook points
  these four do not name.
- `chat_template_hash`. Vectors extracted under one template may not transfer to
  another.
- shape, dtype, L2 norm, **and the typical activation norm at that layer**, so
  coefficients can be expressed as a fraction of activation magnitude rather than
  a raw alpha that means nothing across models
- recommended coefficient range and steering position
- `license_status` for the source model, per the blocker below. An artifact whose
  redistribution rights are unresolved cannot be served.
- **Stored as safetensors, always.** Accept whatever people upload, `.npz`
  included, and normalize on ingest. Never serve `.npz`: with `allow_pickle` it is
  arbitrary code execution on load, and these files go to people who will load
  them without looking.

**Attack**, the adversarial case of pointing your evaluation at someone else's
submission. Same mechanism as EvalSuite, different intent, so it gets its own
rendering rather than its own subsystem.

The strongest evidence available, because it is the one kind the author did not
choose. A page reading "three people tried to break this, two found nothing, one
found a sentiment confound above coefficient 1.5" tells a reader more than any
score the author selected.

- Target Intervention, attacker, date
- Method: adversarial prompt set, alternative confound axis, held-out domain,
  ablation, transfer to an unlike template
- Result: what moved, what did not, at which coefficients
- Disposition, and this one is genuinely contested rather than merely open. The
  attacker states theirs, the author states theirs, and both are displayed. Common
  values are `no-finding`, `confirmed-limitation` and `invalidated`; an attacker
  who wants a different word uses it. A registry-assigned disposition would be the
  registry adjudicating the dispute, which is the one thing it does not do.
- Whether a later submission version supersedes the attack, which is the author's
  claim rather than a resolution
- Reproducible like everything else: an attack asserts nothing the falsifier
  cannot re-derive

This is where the arena's adversarial logic belongs. Attacks target directions,
which is the registry's object; the arena's competition targets sequences against
a frozen direction. Related in spirit, separate in mechanism.

**Run**, provenance. Who, when, hardware, seeds, git SHA, container digest, logs.
Produces one Intervention and one EvalReport.

**Reproduction**, a separate Run of the same Recipe by a different party.

Reports the cosine similarity to the original and the delta on each shared eval.
It does not award a pass or fail, because setting the threshold would be the
registry making the judgment it is trying to hand to the reader. A reproduction at
0.94 and one at 0.41 are both displayed as what they are.

This is still the trust primitive: "reputable" becomes a measurable and contested
property rather than a brand.

---

## Discovery, not ranking

Many submissions will claim the same label on the same model. That is the intended
state, so the interface question is not which one wins but how a user sees the
shape of the disagreement.

**Nothing is ranked by default.** A label view shows every submission claiming it,
with the Comparison matrix between them: cosine similarities, where they agree on
shared evals, which confound axes each author checked, where they diverge. A user
picks based on which author's theory of the trait matches their use, which is a
judgment the registry should inform rather than make.

**No user ratings.** Not because plurality needs policing, but because a single
number collapses exactly the information the registry exists to show. Stars would
answer "which is most popular" when the useful question is "how do these differ
and why." The argument is now about resolution rather than trust.

There is a reason to think ratings would actively mislead here, though it is
untested: a direction that also moves sentiment and verbosity *feels* more
effective in use, because more is happening. A well-isolated one produces a
subtler effect. If so, ratings would favor the confounded submission. The
abliteration literature is the nearest documented case, where removing refusal has
off-target effects on expressed confidence that users plausibly do not notice.

- **Download counts are shown as a fact**, not a badge, not a sort key.
- **Usage drives the audit queue.** Heavily used with nobody having run an
  independent eval against it is the highest-value thing to look at next. Surface
  that list. NU AI Safety and the other university groups are a natural home for
  the work.
- **Sorting is user-chosen and explicit.** By transfer result, by isolation, by
  recency, by number of independent evals run against it. Never a single composite
  score, because composing them is the judgment being delegated to the user.

**Labels are namespaced and free.** `author/label`, claimed by anyone, no
gatekeeping, no canonical trait list. The bare string is a computed view across
claimants. Taxonomy emerges from authors' own `interprets:` and
`distinguishes-from:` pointers, which is a claim one can disagree with rather than
a category one is filed under.

The cost is real and worth stating: without a canonical eval per label, scores are
not automatically comparable across submissions. Comparability has to be earned by
running the same eval against multiple submissions, which is why that action is
first-class and cheap. The bet is that earned comparability on a plural corpus
beats mandated comparability on a thin one.

---

## v0 scope, ship in weeks not months

**Nothing blocks starting.** v0 is software: schema, storage, client, Comparison,
and the rendering. It needs no new extraction, no validated direction, and no
finished policy, because v0 accepts no uploads and serves nothing publicly. The
open items in `DECISIONS.md` gate *launch*, not code.

Content arrives when it arrives. The arena's Season 3 direction is an obvious early
submission and can be imported at any point; it is not a prerequisite, and waiting
on it would be waiting on nothing.

Deliberately narrow:

- **Build against hand-authored fixtures first.** *Done, and then undone.*
  Synthetic submissions clearly labeled as synthetic were enough to build and
  render every view, and they came out again on 2026-09-19 because the site was
  about to be public and a corpus that is half fabricated invites "is this real"
  from exactly the readers it is for. The shapes they exercised, two claimants
  on one label who disagree, one with a transfer result and one without, one
  with an attack against it, moved to `tests/probe.py`, which the tests build
  and the site never sees. See `DECISIONS.md`.
- **Then seed with disagreement, not coverage.** The instinct is 5 to 10 different
  traits. Under the plurality premise the better seed is 3 or 4 *competing
  submissions for one label*, from different recipes, with the Comparison between
  them computed and rendered. One label done that way demonstrates the whole
  product; ten labels done once each demonstrates a file bucket. **This is still
  the right shape and the corpus does not have it.** Five real submissions, one
  author, so no label has more than one claimant and the premise is demonstrated
  zero times. What the corpus needs is a second person, not a second label, and
  not a fabricated stand-in for either.
- **Model-agnostic from the start.** No reason to pick a model at the schema layer.
  Whatever the first real submissions run on is what v0 carries.
- **Storage: build on the HF Hub as the backend.** Repos, LFS, versioning, auth
  and CDN for free. Vectors are kilobytes to megabytes; do not build object
  storage. The value is the schema and the Comparison layer on top.
- **Postgres for metadata**, thin web frontend, artifact pages that lead with the
  eval chart.
- **Falsifier from the first artifact.** Port `_falsifier/verify.py`. Every number
  on an artifact page re-derives from raw data or CI fails.
- **Python client from day one.**
  `load("soham/allenai/Olmo-3-1125-32B/pro-human@meandiff")` returning an object
  that plugs into `steering-vectors`, `rotalabs-steer`, and raw `nnsight`/HF
  hooks. The model is in the reference rather than a keyword argument, because it
  is part of what the submission is. Namespaced, because there is no canonical
  `kindness` to load.
  A `compare("kindness")` call returning every claimant is the client-side version
  of the label view. If integration is friction nobody uses it: the client is the
  product, the website is discovery. nnsight first, since that is the stack already
  in use.

Explicit v0 non-goals: hosted inference, arbitrary uploads, multi-method support,
a playground.

On uploads specifically: the public upload path is the single feature that cannot
ship before the dual-use policy exists, because an upload form plus a search index
*is* the distribution channel. v0 seeds artifacts by hand. The schema is designed
for uploads from the first migration so nothing has to be rebuilt, but the route
stays closed until the policy is written and published.

---

## Scaling path

- **v1, CI extraction runner.** Upload a recipe; it fans out to supported models
  and auto-produces artifacts plus eval reports. Converts N x M from a cold-start
  problem into a build matrix. Needs a compute arrangement that does not exist yet,
  so treat it as a direction rather than a plan.
- **v2, hosted steering inference.** A playground where people feel the vector
  before downloading, plus an API. NDIF already serves models via NNsight, so the
  honest first question is whether this is an NDIF feature rather than a thing to
  build. Gate any independent build behind demonstrated v1 traction.
- **v3, method pluralism.** SAE latents, probes, ReFT interventions and
  attention-head edits as first-class artifact types behind a common
  apply-interface. At that point the registry is about *interpretable
  interventions* generally, not steering vectors specifically.

---

## Three things to settle before launch, not before code

These gate accepting uploads and serving artifacts publicly. None of them gate
building the schema, the client, the Comparison layer or the views, because v0 does
neither of those things.

**1. Direction validity.** See `VALIDATION.md`. Not a code blocker: the schema
records any criterion an author uses rather than asserting one. What is open is
what a Comparison can compute across submissions whose authors validated
differently, and that shapes one module rather than the build. The question worth
taking to people with relevant expertise.

One finding from the arena's behavior study is a hard schema constraint and is not
optional: **a judged score is uninterpretable without a coherence measure beside
it.** Judge-human agreement ran 81% where the text held together and 42% where it
degenerated, worse than chance on a forced choice, and one arm inverted sign
entirely because empty text reads as less unkind than a real opinion. So coherence
is not a nice-to-have collateral axis; any judged eval rendered without one should
be displayed as uninterpretable rather than as a number. See `VALIDATION.md`.

**2. Dual-use policy.** A public registry of vectors that remove refusal or install
a malicious persona is, among other things, a jailbreak distribution channel.
Persona-vector work legitimately ships an `evil` vector, so safety research needs
these and a blanket ban is wrong. But there needs to be a tiered access model, an
abuse policy and a published stance *before* launch, not after the first incident.

This is no longer hypothetical. The arena runs an anti-human board, which is a
public ranked corpus of prefixes that push a model in a harmful direction. The
registry version is worse: a direction plus a coefficient is a reusable artifact
rather than a model-specific prompt. Concrete questions that need answers, not
gestures: does bulk fetch exist, is there a rate limit, are refusal-ablation
artifacts gated behind identity, and what is the takedown path. This also
determines whether labs and academic groups engage at all, which determines
whether reputable players' vectors ever actually show up. Treat it as a launch
blocker, not a compliance chore.

**3. Model license position.** Settled on 2026-09-19 and no longer a blocker.
The author's position is that a direction is his own work, built against a model
rather than derived from it: he wrote the contrast prompts, chose the layer and
the estimator, and did arithmetic on activations he elicited. `DECISIONS.md`
carries it with the case against it and with what it forecloses, and `CLAUDE.md`
carries the working rule.

What this paragraph used to say, and what was wrong with it: that a vector is
derived from model weights, and that the question decides which model families
the registry can carry at all. The first is the disputed premise rather than the
settled fact. The second is a permitted-sources list, which this registry does not
have and cannot have without becoming the thing it exists not to be. Rights stay
per artifact in `license_status`, asserted by the author with a URL and a date,
and where bytes cannot be redistributed the registry points and does not serve.
OLMo is still the easiest starting point, because Apache-2.0 makes the question
moot rather than because it is the one that passes.

---

## Neuronpedia: interop, not competition

They own SAE feature dictionaries and have expanded into probes, concepts and
transcoders. OLMo 3 is already covered: an Olmo 3 7B SAE by David Chanin
(`16-res-matryoshka-65k`, May 2026) and an Olmo 3 32B SAE by Bartosz Cywinski.
Inference is not enabled on the 7B model page, so there is no in-browser steering
there. Duplicating the feature-dictionary work is a losing fight.

One correction to an earlier assumption: secondary sources suggested Neuronpedia
already accepts arbitrary user-uploaded custom vectors with full metadata, which
would have made much of this redundant. Direct inspection says the surface is
narrower than that and organized per model and layer rather than around competing
claims about a trait. **Verify this directly before designing around either
reading.** The distinction that matters is not storage, which they may well have,
but whether plural disagreeing claims on one label are a first-class object.

The clean split: they index *what the model represents*; this indexes *competing
claims about behavioral interventions, and the evidence for and against each*.
Link out to their feature pages for SAE-derived artifacts, accept their features as
a recipe profile. A partnership is worth more than frontend polish.

---

## What success looks like at 6 months

Not upload volume, and not consensus either. Three things:

- Someone asks "which kindness vector for this model" and gets a page showing
  several claimants, what each author meant by kindness, what each checked, and
  where they diverge, from which they can pick the one whose theory matches their
  use. The answer being plural is the success case, not a failure to curate.
- Two submissions claiming the same label turn out to disagree substantively, and
  the Comparison makes the disagreement precise enough to be worth arguing about.
  That is the registry producing knowledge rather than storing files.
- Someone runs their evaluation against someone else's submission, unprompted.
  That is the moment earned comparability starts working and the trust layer stops
  being a design document.