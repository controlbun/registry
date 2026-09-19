# Decisions

Authoritative. If this file and a conversation disagree, this file wins. Add an
entry whenever something is settled, with the date and a one-line reason. Do not
silently reverse an entry; supersede it with a new dated one and say why.

Format:

```
## YYYY-MM-DD Short title
**Decided:** what.
**Why:** one or two lines.
**Supersedes:** entry title, if any.
```

---

## Settled

## 2026-09-11 Arena is upstream, registry is a separate project
**Decided:** Steering Arena stays its own project. The registry is downstream of it
and reuses its seed pairs, probes, confound audits and falsifier, but is not an
arena feature. Connected by a documented dependency, not shared code: the arena is
the registry's first consumer and pins one claimant per season.
**Why:** The arena tests sequence validity against a given direction. The registry
has to test direction validity. Different objects, different instruments. Merging
them would also merge their dual-use surfaces, which are easier to reason about
apart.

## 2026-09-11 The registry never designates; consumers pin, visibly
**Decided:** Separate canonical-as-authority from canonical-as-fixed-reference. The
registry never designates an official entry, has no default resolution for a bare
label, and never answers "give me kindness" with one artifact. Consumers pin a
specific `author/label@version` for a specific purpose, and that pin is named,
cited and contestable. Arena seasons pin this way and show what was passed over.
**Why:** A competition needs a frozen target or scores are meaningless, which is
ordinary experimental control and not in tension with plurality. Conflating the two
senses made the premise sound more radical than it is and would have blocked
legitimate version pinning.
**Supersedes:** nothing; sharpens "Plurality is the product."

## 2026-09-11 Direction validity is the blocking research question
**Superseded by:** Evidence is recorded, not required; and v0 is unblocked.
**Decided:** No schema is final and no code is scaffolded until there is an agreed
criterion for whether a direction encodes what its label says. Tracked in
`VALIDATION.md`.
**Why:** The eval section of the schema is a function of the answer. Building first
means rebuilding.

## 2026-09-11 Out-of-template transfer is a required eval field
**Superseded by:** Evidence is recorded, not required.
**Decided:** Held-out judge score alone does not qualify an artifact for
publication. A transfer result on prompts structurally unlike the contrast pairs is
required.
**Why:** Template and lexical artifacts survive a holdout drawn from the same
generator. Transfer is the criterion Function Vectors used and it is cheap.
Provisional pending the `VALIDATION.md` conversations.

## 2026-09-11 Evidence is recorded, not required
**Decided:** No eval field is mandatory. Each criterion is an optional, separately
typed slot. Absence is rendered on the submission page rather than blocking
publication. Negative results are valid submissions.
**Why:** Requiring a criterion means the registry asserting which criterion is
correct, which contradicts plurality. Visible absence achieves the same goal
without the assertion: nobody is gated, and nobody can appear to have checked
something they did not.
**Supersedes:** Out-of-template transfer is a required eval field.

## 2026-09-11 The registry needs no compute
**Decided:** v0 is schema, storage, client, Comparison and views. No extraction, no
eval runs, no GPU dependency. Artifacts on the HF Hub, metadata and frontend on a
small host. If extraction is ever run as a service, that is a v1 question with its
own compute arrangement.
**Why:** An earlier draft assumed a cluster backend for a fanout runner. The
registry does not extract anything; authors bring their own artifacts.

## 2026-09-11 Eval judge is local weights, not an API
**Decided:** The judge model is pinned as weights with a revision and runs
on-cluster. No external judge API in the scoring path.
**Why:** An API judge makes every published score non-reproducible the moment the
provider updates the model. This project's value proposition is reproducible
scores.

## 2026-09-11 Falsifier pattern is ported from the arena
**Decided:** Every published number re-derives from raw artifacts via a script that
exits non-zero on drift. In place before the first artifact is published, not after.
**Why:** Already built and proven in the arena. A database row is not evidence.

## 2026-09-11 Schema object is Intervention, not Vector
**Amended by:** No closed enums; extension points are profiles. `kind` is an open
string, not the list below.
**Decided:** The artifact object is an Intervention with a `kind` field. v0 applies
`direction` only, but the field is open and exists from the first migration.
**Why:** An intervention is where to hook, what to do, and how to scale it. Every
v3 method fits that shape. Hardcoding "vector" means a rewrite.

## 2026-09-11 Attack is a first-class object
**Decided:** Anyone can publish an Attack against an Intervention, with method,
result, disposition and author response. Rendered on the artifact page.
**Why:** A record of what survived scrutiny is stronger evidence than any
author-written eval. Attacks target directions, which is this registry's object,
unlike the arena's competition which targets sequences.

## 2026-09-11 No user ratings, rank on precision and attack survival
**Superseded by:** No ranking by default, sorting is user-chosen.
**Decided:** No stars or user scores. Sort order is measured precision and attack
survival. Download counts are displayed as a fact, never in the sort order.
Comments attach to Traits, not Interventions.
**Why:** A confounded direction feels better to use than a disentangled one, so
ratings would systematically rank it higher, then compound via placement. The
public LoRA repositories are the existence proof: ratings did not produce
trustworthiness.

## 2026-09-11 Popularity drives the audit queue
**Decided:** High usage with no attack history is a public, prioritized list of
what to scrutinize next. Point the reproduction community at it.
**Why:** The one thing popularity is a valid signal for, and it gives anyone who
wants to contribute review effort an obvious place to start.

## 2026-09-11 Plurality is the product
**Decided:** Labels are namespaced `author/label` and free to claim. No canonical
trait list, no mandated eval per label, no required confound axes. The bare label
is a computed view across everyone claiming it. Submission is the primary object
and holds one author's complete take, including their own theory of the trait.
Comparability is derived after the fact via a Comparison object, not imposed
before submission.
**Why:** See also "The registry never designates; consumers pin, visibly," which
sharpens what this entry does and does not forbid.
GitHub did not arbitrate what "react" means and HF did not pick the
canonical sentiment model. Neither curated its way to usefulness. Ten disagreeing
takes on kindness is the content, not a duplication problem. Accepts the cost that
cross-submission scores are not automatically comparable.
**Supersedes:** Canonical traits, free-form tags on top.

## 2026-09-11 No closed enums; extension points are profiles
**Decided:** A closed enumeration is a designation in miniature. Recipe declares a
namespaced versioned `profile` plus a payload, rather than picking from a method
list. `Intervention.kind` and `hook_point` are open strings whose common values are
documented, not enforced. The registry validates that a reproducible entrypoint
exists, not that the method is on a list. `soham/contrastive-v1` ships as an
example profile, not a standard.
**Why:** Third occurrence of the same failure after canonical traits and required
eval fields. A method enum declares which ways of making a direction are
legitimate; whoever invents the seventh has nowhere to put it.

## 2026-09-11 Recipe is optional
**Decided:** A submission with an intervention but no reproducible recipe is valid.
Absence renders as absence, same as a missing eval.
**Why:** Published vectors from papers with no runnable code are worth holding, and
requiring a recipe would exclude exactly the historical artifacts the registry
should be able to compare against.

## 2026-09-11 Submissions are versioned and immutable
**Decided:** `author/label@version` resolves to one frozen submission permanently.
Revisions publish a new version; old versions stay fetchable and link forward.
**Why:** Pinning is impossible without it, and any season or paper that cited a
version would rot. Revision history is also part of the evidence.

## 2026-09-11 Running someone else's eval is a first-class action
**Decided:** Evaluations are authored objects that can be pointed at any
submission, including other people's. Attacks are the adversarial case of the same
mechanism.
**Why:** This is how comparability accumulates without being mandated. It is the
substitute for a canonical eval per label.

## 2026-09-11 No ranking by default, sorting is user-chosen
**Superseded by:** A default ordering is allowed; no ordering derives from an eval
result. The Comparison matrix named below is also gone, replaced by a similarity
column the reader points at a reference of their choosing.
**Decided:** No composite score and no default sort. A label view shows all
claimants plus the Comparison matrix. Users choose an explicit sort key. Download
counts displayed as a fact, never a sort key. Usage with no independent eval
drives a public audit queue.
**Why:** A single number collapses the disagreement the registry exists to show.
Composing the axes is the judgment being handed to the user deliberately.
**Supersedes:** No user ratings, rank on precision and attack survival.

## 2026-09-11 safetensors on ingest, always
**Decided:** Accept any upload format including `.npz`, normalize to safetensors,
never serve `.npz`.
**Why:** `.npz` with `allow_pickle` is arbitrary code execution on load, and these
files go to people who will load them without inspecting them.

## 2026-09-11 Canonical traits, free-form tags on top
**Superseded by:** Plurality is the product.
**Decided:** Traits are canonical and curated. Tags are open and user-supplied.
No user-generated categories beneath the trait level.
**Why:** Confound axes are declared on the Trait so scores stay comparable across
recipes. A folksonomy underneath breaks that.

## 2026-09-11 v0 is unblocked; the open items gate launch, not code
**Decided:** Building starts now. Schema, storage, client, Comparison and views are
built against clearly-labeled synthetic fixtures. The arena's Season 3 direction is
an obvious early submission but not a prerequisite, and can be imported whenever.
**Why:** v0 accepts no uploads and serves nothing publicly, so the dual-use and
license questions do not apply to it yet. Direction validity does not gate a schema
that records criteria rather than asserting one. Waiting on content to build
software was waiting on nothing.
**Supersedes:** the framing of the list below as blocking code.

## 2026-09-11 A judged score without a coherence measure is uninterpretable
**Decided:** Any judged eval displayed without a coherence measure beside it renders
as uninterpretable, not as a number. Coherence is structurally paired with the
score, not a separate collateral axis.
**Why:** The arena's behavior study found judge-human agreement at 81% on coherent
text against 42% on degenerate text, worse than chance, and one arm inverted sign
because empty text reads as less unkind than a real opinion. A score measured on
degenerate output is not a small effect, it is a broken instrument.

## 2026-09-12 No comparable registry exists; Neuronpedia has storage, not this
**Decided:** Build. Checked 2026-09-12: the adjacent work is libraries
(`steering-vectors`, IBM `activation-steering`, EasySteer) and one vendor catalog
(`rotalabs-steer`, its own vectors only). Neuronpedia accepts custom vector uploads
via `NPVector.new()` with `label`, `model_id`, `layer_num`, `hook_type`, `vector`,
`default_steer_strength`, and steers them, but documents no list, search, plural
claim on one label, or comparison. Storage and a playground, not a registry.
**Why:** Closes the open item that was flagged as the single question that could
save the most work. Their six fields are a strict subset of Intervention: no model
revision pin, no `chat_template_hash`, no activation norm, no `license_status`, no
recipe, no eval. The silent-misuse argument is a differentiator, not a claim.

## 2026-09-12 Non-identifiability conditions every behavioral criterion
**Decided:** Record the constraint and demote cosine similarity from evidence of
disagreement to a displayed fact. Behavioral criteria characterize the equivalence
class rather than the direction, and Recipe is promoted as the structural answer
the authors call for.
**Why:** Venkatesh and Kurapath, arXiv:2602.06801, report large equivalence classes
of behaviorally indistinguishable interventions, with orthogonal perturbations at
near-equivalent efficacy. This supports the plurality premise rather than
threatening it: if the equivalence class is large, a bare label resolving to one
artifact is malformed, not merely undesirable. Abstract read; full paper not yet.

## 2026-09-12 SQLite for v0, not Postgres
**Decided:** v0 metadata lives in SQLite. Migrations stay portable SQL, the
connection sits behind one seam, and Postgres or Supabase later is a driver swap.
**Why:** v0 holds a dozen synthetic fixture records, takes no uploads and serves
nothing publicly, so there is no Postgres workload. SQLite is stdlib, so a clean
checkout plus migrations plus fixtures reproduces the database exactly with no
service to install, run or forget, which is the reproducibility standard this
project has to meet. It also drops the driver dependency and its LGPL question.
Postgres has native `ENUM` and encourages `CHECK`, the two constructs the
no-closed-enum invariant exists to catch; SQLite makes them harder to write by
accident. Cost accepted: no native array type, so author-declared confound axes and
recipe payloads are JSON columns, and a type review when it moves.
**Supersedes:** "Postgres for metadata" in the v0 scope section of `BRIEF.md`.

## 2026-09-12 A default ordering is allowed; no ordering derives from an eval result
**Decided:** Multi-submission views carry a default ordering. Below 100 submissions
it is recency, because recency is the only signal that exists at that size. Above
100 it is a decayed engagement score, where engagement means evaluations and attacks
by someone other than the author. The ordering is named on screen and switchable.
**Why:** A page that arrives in storage order reads as broken rather than as
principled, and the reader who wants a starting point is not the enemy. What the
earlier entry was actually protecting is narrower and survives intact: no ordering
derives from a measured result. A direction that also moves sentiment and verbosity
feels more effective in use because more is happening, so ranking on measured effect
would systematically favor the confounded submission and placement would compound it.
Engagement is scrutiny by others, which is the audit-queue signal, not popularity.
The trending function is a placeholder to be replaced by someone who works on
ranking; it is written so that with no engagement anywhere it collapses into recency
rather than inventing a signal.
**Supersedes:** No ranking by default, sorting is user-chosen.

## 2026-09-12 SAEs get cards and evidence; the registry still does not hold them
**Decided:** An SAE is a first-class object with its own card, carrying attacks and
independent evaluations the same way an Intervention does. The weights are not
hosted here: the SAE is pinned by `repo@commit` and the bytes stay wherever they
already live, exactly as `/models/<id>/` is a card for a model this registry does
not hold. v1, with the rest of the upload path.
**Why:** The differentiator was never the dictionary, it is the evidence layer, and
nobody applies one to SAEs. "Latent 41827 is two features that got merged",
"reconstruction error concentrates on a distribution this was not trained for",
"these two latents are one feature split" are real critiques with real literature,
and there is nowhere to publish them against a specific SAE at a specific commit
with the author's response beside them. That is this project's object, pointed at a
different artifact.

Storage was the objection I raised and it was wrong. An SAE is ~2 GB against ~16 KB
for a steering vector, 131,000x, and forty-nine would exhaust the free tier. All of
which is irrelevant, because holding the card does not mean holding the weights.

No third object for corroboration. A Verification is someone else's eval, and an
Attack with disposition `no-finding` is corroboration from someone who tried to
break it, which is worth more than praise. Add a support object only after seeing
what those two miss.
**Supersedes:** nothing. Narrows "Neuronpedia: interop, not competition" in
`BRIEF.md`: do not duplicate the dictionary, do host the argument about it.

## 2026-09-12 SAE-latent provenance lives in the recipe, not the schema
**Decided:** An `sae-latent` records which SAE and which index in its recipe
payload under a namespaced profile, not in new `intervention` columns.
**Why:** A latent is only identified by its dictionary and its index, so a latent
without them is a vector claiming a provenance it cannot evidence, which is worse
than a direction without a recipe: unverifiable in principle rather than merely
unrerunnable. But `sae_id` and `latent_index` as columns would be the closed-enum
failure in another costume, baking one method's vocabulary into a schema every
other method has to carry. A probe has no latent index; a ReFT edit has neither.
`BRIEF.md` already settled the mechanism: accept their features as a recipe profile
and link out to the feature pages.

---

## Open, blocking launch (not code)

- **Data model.** `BRIEF.md` has a draft good enough to scaffold against. Check the
  NDIF unified-interface naming conventions before finalizing hook points and layer
  indexing: if nnterp already defines that contract, adopt it rather than inventing
  a parallel one.
- **Direction validity criterion.** See `VALIDATION.md`. The minimum publishable
  bar, whether necessity testing is per-artifact or sampled, and whether the
  Function Vectors transfer argument ports from task vectors to trait vectors.
- **Dual-use policy.** Launch blocker. Needs concrete answers, not principles:
  bulk-fetch behavior, rate limits, whether refusal-ablation artifacts are gated
  behind identity, takedown path. Sharper now that the arena runs a live
  anti-human board.
- **Model license position.** Whether an activation-derived artifact is a
  derivative of the weights it came from, and what each model's license permits for
  redistribution. Belongs in the schema as per-artifact `license_status`, and
  constrains which families the registry can carry. Prior practice, verified
  2026-09-12: the Concept Sliders repo distributes pretrained LoRA adaptors derived
  from open image models under MIT, with the disclaimer that "the models that you
  use our methods with, might be on a different licenses." Adaptor MIT, source model
  separate, disclosed rather than resolved. That is one worked precedent, not a
  legal opinion.

## Open, not blocking

- **Name.** Undecided deliberately. Deferred until it is known whether this lives
  inside an existing ecosystem's naming conventions.
- **Interop with existing feature indexes.** Accepting their features as a recipe
  profile, and linking out rather than duplicating.
- **Adversarial falsification as a validation method.** If a populated arena's
  score-versus-behavior gap is admissible evidence about a direction, that is novel
  and a paper. Unresolved, and the highest-upside open question.
- **Whether v0 stays single-model.** Superseded in practice: the schema is
  model-agnostic and v0 carries whatever the first real submissions run on. The
  arena runs Season 3 on Olmo-3-1125-32B.

- **Automatic direction discovery as a seeding method.** SliderSpace (Gandikota,
  Wu, Zhang, Bau, Shechtman, Kolkin; arXiv:2502.01639, ICCV 2025) discovers many
  interpretable composable directions from a single prompt, each a low-rank
  adaptor, without per-attribute supervision. If that ports to language-model residual directions, the registry
  seeds itself from a short trait list rather than one hand-built recipe at a time,
  which changes the cold-start answer. Speculative; do not build toward it.

## 2026-09-13 Adoption comes from the client being easy, not from the ordering
**Decided:** The ordering is not tilted toward whatever attracts the most users, now
or later. It stays as already settled: recency below 100 submissions, decayed
scrutiny above it, named on screen and switchable, with no measured result feeding
it. Growth is bought by making the client easy to use.
**Why:** The plan was to order for attraction early and realign to safety once there
were enough users to matter. The realignment never happens. Whatever is at the top
gets looked at, which raises its engagement, which keeps it at the top, and by the
time there is a corpus worth reordering there is also a constituency whose position
depends on the current order. Ordering for attraction is a lever that only moves one
way. A good client is a lever with no such ratchet, and it is the part a person
actually touches.

## 2026-09-13 The ordering control computes what its caption says it computes
**Decided:** The site reorders in the page, running `order.trending_score` with the
constants exported from `order.py` rather than a second copy of the formula.
Every ordering renders as a button, including the active one, and the caption naming
the active ordering updates when the reader changes it.
**Why:** The control shipped with buttons, `aria-pressed`, an explanatory caption and
no handler at all, and the suite was green because the test asserted that the
attribute was in the markup. A reader clicking it concluded the ordering could not be
changed. The first fix sorted by the raw engagement count while the caption promised
engagement decayed by age, which is the same dishonesty one layer down. Behavior is
now tested by running the page's own script against `order.py`, and
`tests/test_ordering_bites.py` reintroduces each failure to prove the tests fail on
it.


## 2026-09-13 The Jinja frontend is retired; Astro is the frontend
**Decided:** `web/templates/` and the HTML-emitting half of `src/registry/render.py`
are deleted. The shared view logic is `src/registry/views.py`, which shapes a
claimant for both `export.py` and `client.py`; the ordering display names moved to
`order.py` beside the keys they name. `tests/test_render.py` became
`tests/test_pages.py` and reads the built Astro output. `make verify` builds the
site before running the suite, because the page tests and the falsifier both read
`astro/dist` and building afterward meant checking the previous build.
**Why:** Two frontends drifted, and the one under test was not the one anybody
would visit. Jinja still carried the quadratic "Between claimants" table that Astro
replaced with a reader-pointed similarity column, so the retired design was the one
the suite was proving correct. The dead ordering control is the same lesson: it
shipped in both, and fixing it twice was the moment to stop maintaining a second
answer to every question.
**What this makes impossible to express:** a server-rendered view with no
JavaScript. The similarity column and the ordering control both run in the browser
now, so a reader with scripts off gets the list in storage order with no angles.
That is a real loss and an acceptable one at v0, which serves nothing publicly; if
a no-JS path is ever needed it is a build-time render of the same `views.py` shapes,
not a second template language.

## 2026-09-13 The site is published on GitHub Pages, when the repo goes public
**Decided:** The built site is served from GitHub Pages once this repo is public.
Publication is gated on the dual-use policy, so neither happens at v0. Nothing is
imported into a deploy platform before then: a connected deploy integration on a
private backup remote is a build surface, which the repo section rules out.

If something has to be served before the repo is public, it is a direct upload of
`astro/dist` with no git connection, because GitHub Pages on the free plan requires
a public repo and serving early would mean publishing the design docs to get a
website. That is a fallback, not the plan.

**Why:** The site is 960K of static files across 49 of them, against a 1 GB Pages
limit and a 100 GB/month soft bandwidth limit. There is no hosting problem here to
solve, so the deciding factor is what the hosting arrangement couples together.
Publishing from the repo is only acceptable once the repo is itself the public
artifact; before that it forces a choice between a private history and a website.

Publishing also makes `_attest/` verifiable by anyone rather than by anyone who is
handed the files. The proofs date the design, and a proof nobody can independently
check is worth less than one they can.

**What this makes impossible to express:** a public site over a private repo. That
combination needs a paid GitHub plan or a second host, and taking it would mean the
published site and the source it was built from are no longer the same object a
reader can check. Declining it is what keeps "build it yourself and compare" true.

**Obligations this creates, to be discharged at publication and not before:**

1. Amend the repo section of `CLAUDE.md`. It currently reads no Actions, no public
   push, no `gh` workflows, which is correct for a private backup and wrong for a
   public repo that publishes from a branch or a workflow. Amend it deliberately at
   that moment rather than discovering the contradiction mid-build.
2. Re-run the history audit against the tip of the day. Publishing exposes every
   commit, not the tip. As of `07489dd`, `_local/`, `.env`, `.env.*` and
   `NOTES-private.md` have never been committed on any branch at any point, and no
   tracked file carries anything credential-shaped. That result is dated, not
   permanent.
3. Confirm the dual-use policy exists and is published with it. It is the launch
   blocker, and the site going up is the launch.

## 2026-09-13 An owner is someone who took part, not someone who published
**Decided:** Owner pages are derived from participation. Authoring an eval suite,
evaluating somebody else's submission, attacking one, or filing a support card all
make a person a page, the same way publishing an artifact does. The page names what
they actually did, and zero submissions renders as a fact rather than as an empty
profile.

This is not an account system and does not pretend to be one. A person is still
derived from what they did and nobody has a page until they do something. Real
profiles arrive with the upload path.

**Why:** `/carol/` was a 404 for days, and so were `/gus/` and `/hana/`. carol ran
the only attack in the fixture corpus and owns an eval suite; gus and hana filed
the support cards. All three are linked by name from the pages their work appears
on, and there was nothing at the other end, because an owner existed only if they
had published a submission.

That is backwards here specifically. The evidence layer is the differentiator, and
it is written by people pointing their suites at other people's submissions. A
reader weighing an attack cannot weigh the attacker if the attacker has no page, so
the old derivation made scrutiny second-class next to publication in a registry
whose thesis is that scrutiny is the content.

Treating it as a fixture gap would have been wrong. Real data reproduces it
exactly: a real evaluator who never ships an artifact 404s the same way.

**What this makes impossible to express:** a participant who is not listed. Anyone
who attacks or evaluates now has a public page enumerating it, whether or not they
wanted one. That is the correct trade for an open registry, where the point of an
attack is that it is attributable, but it is a real constraint and not a free win.

**Also:** `make verify` gained a `links` step. Nothing in the gate followed a link
before, so a page linking to a page that was never built passed everything. The
falsifier re-derives numbers, the invariants read source, the page tests read one
page at a time.

## 2026-09-13 Dates render in UTC
**Decided:** Every date the site prints is formatted with `timeZone: "UTC"`.
**Why:** Timestamps are stored as UTC midnight and `toLocaleDateString` resolves
them in the reader's zone, so west of Greenwich `2026-09-12T00:00:00Z` printed as
"Sep 11, 2026" while the `datetime` attribute beside it said the twelfth. Seven
formatters, every date on the site, and a released-on date that is a day out is the
kind of error a reader acts on without ever suspecting it. A registry about
reproducibility does not get to display a different day than the one it recorded.

## 2026-09-13 Upload preferred, pointer available; SAEs are pointer only
**Decided:** Every artifact records where its author published it, as
`artifact_repo` plus `artifact_commit` plus a path, resolved by commit SHA because
a tag is movable by the repo owner and immutability is what pins depend on. That
pointer is never replaced.

On top of that, the registry serves its own copy where it can. Upload is the
preferred state and a pointer alone is the fallback, not the other way round.

Two things gate serving a copy:

- **Rights.** `license_status` is an open string and the author asserts it. We
  serve only on an explicit affirmative. Silence, `unresolved`, or anything we do
  not recognize means pointer only, and the page says rights are unresolved and
  that is why there is no copy. We are not deciding whether a license permits
  redistribution; we are declining to serve where nobody has said it does. Every
  fixture today reads `unresolved`, so nothing would be served right now anyway.
- **Size, by class rather than by bytes.** SAEs are pinned, never served. A
  direction is about 16KB and a probe is about the same, so sixty thousand of them
  fit in a gigabyte and they will never be the problem. One SAE is about 2GB and is
  the whole informal budget by itself.

**Why a size rule by class and not a threshold.** A per-file cap does not bound
what actually binds. A hundred 400MB adapters each pass a 500MB check and total
40GB. Hugging Face gives a free organization "best-effort" public storage with "the
first few gigabytes" as the informal line, and a 500GB hard limit per single file,
so any per-file number we picked would be three orders of magnitude below what the
platform cares about while failing to constrain the account total. An arbitrary
threshold is also a number that will be wrong in a year with nobody remembering why
it was chosen.

**What is still open:** LoRA and other adapters, tens to hundreds of megabytes
each. They are the only class where a budget rule would earn its keep, and if one
is written it should be a total with a stated policy rather than a per-file cap.

**What this makes impossible:** guaranteeing that an artifact we do not serve stays
fetchable. If an author deletes their repo, `author/label@version` still resolves to
a submission with full provenance and no bytes. Mirroring everything would fix that
and would make this registry the chokepoint the plurality premise exists to avoid,
so the failure stays visible instead.

**It also makes us a distributor rather than an index**, for anything we do serve.
"We only pointed at it" stops being available as an answer. That is what moves the
dual-use policy from a theoretical launch blocker to a load-bearing one: the first
artifact whose `license_status` is not unresolved is the artifact that needs the
policy to already exist.

**Supersedes:** nothing. Extends "SAEs get cards and evidence; the registry still
does not hold them" from SAEs to every kind, and keeps the SAE half of it unchanged.

## 2026-09-13 The artifact kinds are not a list, and the code does not read them
**Decided:** `kind` stays an open string. There is no canonical set of artifact
kinds and the registry does not publish one.

**Why this is not just principle:** the code already works this way. `comparison.py`
decides whether an angle between two artifacts is even defined by looking at the
tensor's `shape`, not at what the artifact is called. `kind` is used in exactly one
place, to write the note saying what is being compared when two kinds differ. So a
kind nobody has thought of yet costs zero lines of code, and invariant 7 plus
`test_no_check_constraint_enumerates_strings` keep it that way.

The fixtures carry three, `direction`, `probe` and `sae-latent`, and the similarity
tests add `lora` and `reft` to prove the angle refuses on a matrix. That is five out
of a field that is much larger and still growing: function vectors, task vectors,
transcoder and crosscoder latents, attention-head interventions, rank-one weight
edits, soft prompts, bias offsets, concept vectors, projection and ablation
directions.

**Citations for that list are not checked and must be before any of it appears in a
public document.** It is written here as a reminder of the field's shape, not as a
claim about specific papers.

**What this makes impossible:** telling a contributor what kind of artifact they are
allowed to publish, and any interface that needs the full set of kinds in advance.
Faceted browsing over kinds has to be built from what the corpus actually contains
rather than from a declared list.

## 2026-09-14 The synthetic marker is per page, not per corpus
**Decided:** `any_synthetic` stops gating a corpus-wide banner. Each page states
what is on it: `all` when every figure traces to a fixture, `mixed` when some do
and the exception is named, `none` when no figure on the page is fabricated and
the page carries no marker at all. The exception is built from `real_authors` in
the export, so it cannot outlive the rows that make it true.

**Why:** the flag was per row in the schema from 001 and only the render was
corpus-wide. That was accurate while the corpus was entirely fabricated and became
false the moment one submission was not: the first real artifact would have
rendered a real measurement under a banner saying every figure on the page is
invented. A marker that is sometimes false is not a marker, and the direction it
was false in is the expensive one.

The same applies below the banner. `SweepChart` and `ConfoundChart` carried an
unconditional "synthetic, repeated-digit values" caption under the figure; both
now take the flag.

**The falsifier check changed with it,** and gained the half it could not have
had before. It attributes numbers rather than pages, so it needs no knowledge of
how routes are built: a figure traceable only to a synthetic claimant must appear
on a marked page, and a page whose figures are all real-only must not be marked.
A value reachable from both is attributed to neither, which is the conservative
reading and the reason 1.0000 cannot convict anything.
`tests/test_synthetic_marker_bites.py` reintroduces both defects and asserts the
mutation landed before believing the result.

**Supersedes:** nothing.

## 2026-09-14 `model_revision` is nullable, and absence renders as absence
**Decided:** `schema/migrations/005` drops NOT NULL from
`intervention.model_revision`.

**Why:** NOT NULL does not produce a revision, it produces a string. An author who
never recorded one types `unknown`, or `main`, or pastes the sha the model has
today, and the last is worse than nothing because a false provenance claim reads
exactly like a true one. The three OLMo-3 directions are the case: extracted
through NDIF in June 2026 with an empty `model_build`, so the revision was never
captured and no string put in that column would capture it.

This is the argument 001 already makes about recipes. Requiring one "would exclude
exactly the historical artifacts worth comparing against"; requiring a revision
excludes every artifact published before anyone thought to record one.

**What this makes impossible:** relying on the schema to guarantee a revision is
present. Enforcement moves to the upload path, which can tell the difference
between a revision that is resolvable and absent and one that never existed.

**Supersedes:** nothing.

## 2026-09-14 The submission URL carries its version
**Decided:** a submission is at `/<owner>/<model>/<label>/<version>/`. The
label-last route is gone.

**Why:** `author/label@version` is the identity in this schema and nothing above
it resolves to one artifact, but the route assumed one submission per author per
label. That held only while nobody had published two takes on their own word.
Three estimators over one contrast set are three submissions, and the old shape
would have collapsed them into one URL, which is the registry picking.

The route stays unambiguous: owner is the first segment, label and version are the
last two, and the variable-depth model id is whatever sits between them.

**Supersedes:** nothing.

## 2026-09-14 Non-Hub provenance lives in the recipe payload, and that is a gap
**Decided:** `artifact_repo` and `artifact_commit` stay Hub-shaped. An artifact
published somewhere else records its origin repo, commit, path and sha256 in the
recipe payload, where it renders as cited provenance.

**Why:** `fetch.hub_url` builds `huggingface.co/{repo}/resolve/{sha}/{path}`, so a
GitHub repo in those columns would publish a URL that 404s and then silently fall
back to the local copy. A wrong URL on the page is worse than no URL.

**This is a limitation and is written down as one.** What it makes impossible to
express is provenance for anything not on the Hub, in the columns that exist for
provenance. The honest fix is a host field or a resolver per host, and it is not
v0 scope. Until then the payload carries it and `artifacts/REAL.md` says where to
look.

**Supersedes:** nothing.

**Superseded by:** 2026-09-18 "The row carries its own URL template, so a pin
can name any host". The host field this entry called the honest fix exists, and
the columns are no longer Hub-shaped. Non-Hub provenance does not live in the
recipe payload any more.

## 2026-09-14 The seed corpus is indexed, not submitted
**Decided:** The corpus is populated by indexing artifacts that already exist,
starting with the literature, and not by waiting for people to upload. Submissions
remain the primary object and the upload path still gets built; it is no longer
what the registry is bootstrapped from.

**Why:** Rohit Gandikota's suggestion on 2026-09-14, and it is the answer to the
two failures already on record. David Bau tried an open-science forum roughly a
year and a half before this and it did not take. Natalie Shapira, asked to imagine
using this, asked "why would they do that, what would be their incentive," and got
no answer worth anything. Both are the same failure: a registry that starts empty
and asks for contributions is asking for a favor before it has given anything.
Google did not ask websites to submit themselves.

**The premise as it was given to me was wrong, and the correction matters more
than the suggestion.** The claim was that Hugging Face is full of wasteful
artifacts sitting unused. Counted on 2026-09-14, off the Hub's own search index:

    abliterated          8,011      sae (noisy substring)  4,591
    uncensored           6,838      sparse autoencoder       108
    steering (anything)    190      linear probe             104
    reft                   111      gemma-scope               85
    control vector          34      llama-scope               27
    steering vector         22      refusal direction         11

Full-text search inside repo files, for the case where an artifact hides in a repo
named something else: `control_vector` 66 hits, `steering_vector` 96,
`ControlVector` 98.

There is no pool of unused steering vectors on the Hub. There are a few hundred
artifacts, total. **The scarcity is the finding.** 34 control-vector repos against
8,011 abliterated models, same field, same techniques, three orders of magnitude
apart, because abliteration outputs a model and the Hub has a slot for models,
while a direction outputs something with no slot: no layer field, no hook point,
no indexing convention, no chat template hash, no coefficient range. It cannot be
found and cannot be applied, so nobody publishes one.

**Not yet decided, and load-bearing:** whether the missing schema causes the
missing supply, or whether the supply is missing because the demand is. The counts
above fit both readings exactly as well. Nothing here resolves that, and the
project should stop acting as though it does. What resolves it is asking people
who have extracted a direction how long validating it took and whether they would
have used someone else's.

**So the crawl target is the literature, not the Hub.** CAA, RepE, ITI, Function
Vectors, Arditi's refusal direction, ELM, Concept Sliders and the community sliders
on SliderFactory and Civitai, Gemma Scope, Llama Scope, the sae-lens ecosystem.
Scattered across GitHub, project pages and OSF, each attached to a paper that
states the layer, the hook point and the contrast data, which is the metadata that
makes an index entry worth having. Hand-entered first. A crawler is an optimization
of something that already works, and building one before the schema has met fifty
of other people's artifacts would automate a schema that is not finished.

**This is the lowest-risk shape of the product, not the highest.** An index points;
it does not host. `004_served_copy.sql` already separates `artifact_repo`, where the
author put it, from `served_repo`, where we serve a copy, NULL everywhere. An
indexer only ever writes the first pair, so there is no redistribution, no
model-license question, and "we only pointed at it" stays available as an answer.

**Hard ordering, and it is a blocker rather than a caveat.** Roughly 95% of the
crawlable Hub corpus by volume is refusal removal. `CLAUDE.md` requires flagging
anything that makes refusal-removal artifacts easier to find or fetch in bulk, and
an automated Hub indexer is not adjacent to that, it is that. Worse, the useful
version is the dangerous version in the same field of the same row: an index
carrying independent measurements of how thoroughly refusal was removed would be
genuinely predictive, because model-tampering success conservatively bounds
held-out input-space attack success (Che et al., arXiv:2502.05209, on which
Gandikota is a co-author; Bau is not). Predictive for the researcher and for everyone else. **The Hub indexer
does not ship before the dual-use policy exists.** The literature index, hand-
entered and pointing at papers, does not carry that weight and can proceed.

**What this makes impossible:** treating an empty corpus as a neutral starting
state. It also means the registry publishes entries about other people's work
without asking, including entries that record what an author did not declare, and
the posture on that has to be settled before the first one goes up rather than in
the reply to the first complaint.

**Two facts about Neuronpedia's scale, added to the 2026-09-12 entry rather than
replacing it.** That entry already establishes the shape correctly, including the
exact `NPVector.new()` field list and the finding that they document no list,
search, plural claim on one label, or comparison. What it does not carry is how
large the thing is: over 50 million latents and vectors across 40-plus models, and
it is how DeepMind shipped Gemma Scope. That matters for this decision
specifically, because an index bootstrapped from the literature will point at
Neuronpedia constantly for anything SAE-derived, and pointing at a platform of that
size is a different proposition from pointing at a peer. The split in `BRIEF.md`
holds: they index what the model represents, this indexes competing claims about
behavioral interventions.

**Supersedes:** nothing.

## 2026-09-14 The consumer surface is a package, and it is how this gets used
**Decided:** The way a researcher touches this registry is
`pip install controlbun` and a resolve call, not a website. The site is for
deciding; the package is for using. `src/registry/client.py` and `fetch.py` are
already that package under a different name and will be renamed and published
rather than rewritten.

    from controlbun import artifact
    d = artifact.load("soham/pro-human@meandiff")

**Why:** every failure mode this project exists to prevent happens at the moment of
application, not at the moment of browsing. `BRIEF.md`'s third failure mode is
silent misuse: a vector applied at the wrong layer, hook point or chat template
does not fail loudly, it appears not to work. A webpage can only display the
application contract. A package can refuse to hand over a tensor whose shape or
dtype disagrees with what the submission recorded, which `client.py` already does
by raising `MismatchedArtifact`, and can carry the layer, hook point and
coefficient range into the call site where they are actually used.

It is also the only thing that produces the evidence the registry runs on. A
support card is somebody reporting that they pinned a version and used it, and
nobody writes one after looking at a page. They write one after the thing worked
or did not.

**Namespacing follows the object graph, not convenience.** `artifact` resolves and
verifies bytes. Anything named for a schema object keeps that object's meaning, so
a `pin` in the package records who pinned it, when, and what the alternatives were,
exactly as `pin` does in the schema, or it is not called that.

**Not yet decided:** whether resolution ever fetches from anywhere but a pinned
commit, what the npm surface is, and whether there is a CLI. The name registrations
on PyPI, npm and GitHub happen in the same sitting as the name going public, along
with the intent-to-use filing, and none of that has happened.

**What this makes impossible:** a website-only product. Anything the site can say
about how to apply an artifact now has to be expressible as something the package
can enforce or refuse, and a field that only renders is a field that will be got
wrong at the call site.

**Supersedes:** nothing.

## 2026-09-14 Scanned code is discovered, not listed
**Decided:** `tests/test_invariants.py` no longer holds a list of directories to
scan. It walks the tree and scans everything with a source suffix except the names
in `NOT_SCANNED`, each of which carries a reason.

**Why:** the list is what failed. `artifacts/` was added carrying the only code in
the repo that writes real `submission`, `intervention`, `recipe` and `eval_report`
rows, and no invariant read it for a day. The guard beside it could not notice:
it asked whether each *listed* directory was readable, which cannot detect a
directory nobody listed.

This is the third time a scanner here has been green while checking nothing, after
`\bbest\b` never matching `best_submission` and the cosine scan still looking for
`cosine_sim` after the field became `angle_similarity`. All three are the same
shape. Inverting the default changes the failure mode from an inert scanner, which
is silent, to a false positive, which is loud.

**Two guards, because discovery keys on suffix and so has its own hole.**
`test_scanner_reaches_every_place_rows_and_views_are_made` names the directories
that must be reached and fails if one stops being scanned or gets excused.
`test_no_code_file_type_escapes_the_scanner` compares `CODE_SUFFIXES` against
`SCANNED_SUFFIXES` and fails on a view written in a type nobody listed, which is
the hole named when the Jinja frontend moved to Astro.

`tests/test_scan_gap_bite.py` narrows the scan back to `src` and `astro/src`,
injects the same four violations into `artifacts/`, `fixtures/` and `falsifier/`,
and asserts each one goes unnoticed, so the probes are proven to test the widening
rather than to pass alongside it. It asserts `0 < narrow < wide` first, because a
narrow scan reading nothing would make every probe pass vacuously from the other
direction.

**What this makes impossible:** keeping code out of the invariants by putting it
somewhere new. Excluding a directory is now an edit to `NOT_SCANNED` with a reason
next to it, and doing that to anything in `MUST_REACH` fails the build.

**Supersedes:** nothing.

## 2026-09-15 A bare `author/label` refuses when the author has several current versions
**Decided:** `client.load("author/label")` resolves the head of that author's
revision chain, the version nothing supersedes. Several heads raises `Ambiguous`
and names them. It no longer picks.

**Why:** it was `max(version_strings)`, which reads a revision order off text that
does not carry one. On the corpus as it stands that returns `meandiff` for
`soham/pro-human`, the oldest of the three, because `m` sorts last. It also
returns `v9` over `v10` for anyone numbering past nine.

The string bug is the smaller half. `artifacts/seed.py` says those three are
parallel takes with no ordering between them, so any answer is the registry
designating one, which is the thing it does not do. `superseded_by` is the field
that records a revision chain, so that is the field that gets read.

`Ambiguous` is a sibling of `BareLabelError` one level down: that one refuses to
turn a bare label into an artifact because several authors claim it, this one
refuses because one author published several takes. Both name the alternatives,
because an error that does not is a dead end.

**What this makes impossible:** getting an artifact out of this client without
naming a version, whenever the author has published more than one current take.
That is intended. Convenience here is designation wearing a different hat.

**Supersedes:** nothing.

## 2026-09-15 One comparability rule, not two
**Decided:** `pairwise` and `similarity_matrix` share `_angle_between`. The pair
row gains `angle_why`, so a page can say which condition failed.

**Why:** they were separate implementations of one question and they disagreed.
`pairwise` gated on model, revision, layer and hook point; `_angle_between` gated
on those plus rank and shape. A LoRA beside a direction at the same layer was
correctly refused by the matrix and reached `np.dot` in `pairwise`. With shape
`[1, n]` against `[n]` the dot yields a size-1 array, `float()` succeeds, and a
number ships for a LoRA, which is the exact failure
`tests/test_similarity_refuses.py` was written to prevent, live the whole time in
the other code path.

**What this makes impossible:** the two views disagreeing about whether an angle
exists. A future comparability rule is added once or not at all.

**Supersedes:** nothing.

## 2026-09-15 An artifact path is repo-relative, and leaving the repo is refused
**Decided:** `registry.artifact.local_path` resolves a database `artifact_path`
against the repository root and raises `UnsafeArtifactPath` if the result escapes.
Used by `fetch.resolve`, `comparison.load_vector` and both falsifier sites. Each
passes its own module `ROOT`, because three test harnesses redirect the code at a
copied tree by rebinding that name.

**Why:** `ROOT / value` is not containment. pathlib drops the left operand when
the right is absolute, so `artifact_path = "/etc/passwd"` resolves to
`/etc/passwd`, and `..` is not normalized away. Four callers did that. Nothing
hostile is in the database today because nothing but this repository writes rows,
and that stops being true the moment there is an upload path, which is exactly
when a check added afterwards is added too late.

Refuses rather than clamps: a path that escapes is not a typo, it is a row
claiming the registry holds something it does not.

**Supersedes:** nothing.

## 2026-09-15 The license audit runs in the gate, and refuses an empty scan
**Decided:** `licenses` is in the `verify` chain, after `site`. The script uses
`fileURLToPath` rather than `.pathname`, and exits non-zero when it finds no
packages.

**Why:** two separate failures in one check. It was never called, so the copyleft
check CLAUDE.md requires did not run. And a file URL percent-encodes, so on a
checkout under a directory whose name contains a space the path contained `%20`,
the scan found nothing, and the script printed "all permissive, nothing to review"
and exited 0. An audit that reports clean when it cannot see anything is worse
than no audit, so an empty scan is now an error on its own.

**Supersedes:** nothing.

## 2026-09-15 Every manifest on disk has to be in all three inventories
**Decided:** `tests/test_attest.py` gains
`test_every_manifest_on_disk_is_in_the_inventory` and
`test_every_proof_and_backup_is_frozen`. The lists no longer decide what is
protected; they are asserted against what exists.

**Why:** the tree stamp made on 2026-09-13 and anchored in block 966895 was added
to none of `REQUIRED_MANIFESTS`, `ANCHORED` or `FROZEN_ATTEST`, despite the file's
own docstring saying to. It sat unprotected for two days while the suite reported
green: deleting or editing all three of its files broke nothing. It is also the
broadest stamp in the set, covering the whole tracked tree including every earlier
proof.

Three hand-maintained lists that must be kept in step is the same shape as the
`SOURCE_DIRS` list that let `artifacts/` go unscanned. Same fix: stop letting the
list decide, and fail when it falls behind what is on disk.

**What this makes impossible:** stamping something and forgetting to protect it.
Adding a stamp still means editing this file; forgetting to is now what goes red.

**Supersedes:** nothing.

## 2026-09-15 v1 is the site going public, and it is scoped in `V1.md`
**Decided:** Three answers taken on 2026-09-15, target Friday 2026-09-18,
explicitly half baked.

1. **The repo goes public and the site is served from GitHub Pages**, which is
   the recorded plan rather than the dist-only fallback. Free, and it makes
   `_attest/` independently verifiable, which is most of what the proofs are for.
   The three obligations recorded on 2026-09-13 come due: the history audit at
   the tip of the day, the `CLAUDE.md` repo-section amendment, and the dual-use
   policy.
2. **controlbun.com is registered and the name goes public on Friday.** That is
   the trigger already recorded for npm, PyPI and the GitHub org, and the
   intent-to-use deferral was measured from the name going public rather than
   from the date it was deferred.
3. **The dual-use policy is deferred.** See the next entry.

**What v1 is not:** the indexed corpus. Seeding from the literature is settled
and is weeks of content work. Friday ships the vessel, with the eight submissions
that exist.

**Supersedes:** nothing. Discharges the "when the repo goes public" branch of
"The site is published on GitHub Pages, when the repo goes public".

## 2026-09-15 The dual-use policy is deferred past launch, knowingly
**Decided:** The site goes public without a dual-use policy. The 2026-09-13 entry
records the policy as the launch blocker, in the words "the site going up is the
launch". That blocker is overridden, not met.

**Why it is being overridden:** the site serves no artifact bytes, takes no
uploads, has no API and no bulk path, and holds eight submissions of which the
three real ones are the author's own work under Apache-2.0. The misuse surface of
a read-only metadata page over that corpus is small.

**Why that reasoning is incomplete, recorded so it is not a surprise later.**
Going public publishes `BRIEF.md` and `VALIDATION.md`, and both carry this
project's own extended analysis of misuse surface, refusal-removal artifacts, and
the tension between open contribution and misuse gating. A reader finds the
analysis and finds nothing answering it. That is a worse position than a quiet
site with no policy page, and it is caused by the combination rather than by
either choice alone. The corpus also includes `refusal` as a fixture label, and
Pagefind indexes label semantics across every page it builds.

**What discharges it:** one page. What the registry will and will not hold, that
it serves no weights today, and how to report something. Estimated at an hour.
The deferral is a scheduling choice, not a judgment that the page is unnecessary.

**What this makes impossible:** answering the first question a safety-adjacent
reader asks, including anyone who arrives from the interpretability side, which
is the audience. It also blocks the Hub indexer, which was already gated on this
policy for a much stronger reason: roughly 95% of the crawlable Hub corpus by
volume is refusal removal.

**Supersedes:** nothing. Overrides, without amending, the launch-blocker clause
in "The site is published on GitHub Pages, when the repo goes public". Revisit
before the corpus grows or before anything is served as bytes.

## 2026-09-15 OPEN: contribution goes through Supabase, not through the site or HF
**Not decided.** Recorded because it is expensive to reconstruct and because two
wrong turns were taken getting here. The plan that follows if it is taken is in
`V2.md`. Gated on v1 shipping and on the dual-use policy existing.

**The shape.** Supabase holds identity, submission writes and the pending state.
Git holds the published snapshot, which is what the site builds from and what the
falsifier checks. HF holds artifact bytes, which is already settled.

**The property being defended is not "no backend".** It is that the published
corpus is a file anyone can rebuild, diff and re-derive. Where writes happen is
orthogonal to that.

### Two corrections, recorded because both were argued out loud

**Submission by pull request was proposed and is wrong.** A PR is public from the
moment it opens, so a submission containing a refusal direction is visible to
everyone before anyone reviews it. It was proposed specifically as the natural home
for the dual-use gate, and it is the one mechanism that cannot gate the thing the
policy exists for. Supabase's pending state is private by default, which is the
property a review queue needs.

**HF as the whole backend is wrong for one reason and it is not technical.** If
identity, storage and metadata all live on HF, this is an HF feature, and the
company most likely to ship a steering-artifact registry owns the user
relationship. GitHub will never ship one. That asymmetry does not apply to bytes,
because bytes are not a relationship, which is why HF stays the store. Neuronpedia
already holds the "atlas on top of HF" position with 50M latents.

### A refinement to "SQLite for v0, not Postgres"
That entry says Postgres or Supabase later is a driver swap behind `db.py`. In this
shape it is not a swap. SQLite stays as the build-time read store and Supabase is
added alongside as the write store, so `db.py` gains no Postgres driver. Cheaper
than that entry anticipated.

### The design problem nobody had noticed
`author` cannot become "a verified account". The seeding decision populates the
corpus by indexing the literature, so most entries have an author who never signed
up. Requiring an account makes the indexed corpus unrepresentable, which kills the
plan that makes the registry worth existing.

So `author` stays a namespace string and **claiming is a separate object.** A
namespace starts unclaimed, indexed entries live there, and a claim binds an
account to it on evidence. That is also the honest answer to squatting: the
namespace is not the claim.

### The erosion risk, which is worse here than in the alternative
A submission queue is the most comfortable place in this system for quality review
to grow, more comfortable than a diff, because a queue has a reviewer and a
reviewer has opinions. Review checks schema validity, which `make verify` already
automates, and dual-use, which is policy. **Never quality.** A submission that
passes both gets published even if the reviewer thinks it is weak, because the
reviewer thinking so is an attack card they can publish like anyone else.

**Decline reasons should be a closed, published set, and this is the one
legitimate closed enum in this schema.** Every other one constrains contributors;
this one constrains the registry. Enumerating what we may refuse for is the
inverse of the usual failure. The trip-wire list in `CLAUDE.md` needs to say so, or
someone deletes it on principle.

### Blocking unknowns
HF is not one of Supabase's built-in OAuth providers, so this depends on its
custom OIDC provider accepting HF. Unverified, and a no rewrites the identity
section. Free plan checked 2026-09-15: 500 MB database, 1 GB storage, 50,000
monthly active users, 5 GB egress, two active projects, paused after one week
idle; Pro is $25/month and never pauses. The pause is an argument for the split,
since it takes down submissions and leaves the site untouched.

And the largest one, unchanged: nobody has established that anyone wants this.
Building a contribution path before asking is the expensive order.

**Supersedes:** nothing. Refines "SQLite for v0, not Postgres" as described above.

## 2026-09-15 Indexing is deferred; the lane without it comes first
**Decided:** Do not build the indexer and do not plan around it. The corpus stays
at what is in it, and grows only by the author adding more of his own arena
directions or by somebody submitting.

**Status of the indexing decision:** deferred, not reversed. "The seed corpus is
indexed, not submitted" (2026-09-14) stays on the books with its counts and its
dual-use ordering intact. Nothing here contradicts it and nothing built in this
lane may foreclose it.

**Why the deferral has a cost worth writing down.** Starting empty and asking for
contributions is the shape that did not work twice already: David Bau's open
science attempt a year and a half ago, and Natalie Shapira asking "why would they
do that, what would be their incentive" and getting no answer worth anything. The
indexing decision existed to avoid exactly that, and taking this lane first walks
back into it deliberately. It is a sequencing choice; it is not a solution to the
cold start.

**Two consequences, both recorded in the plans.**

The plurality thesis stays demonstrated only by fixtures. All three real
submissions are one author, one label, one model. Indexing was the answer to that
and deferring it postpones the answer rather than providing one, which matters
before showing the site to a skeptical reader as evidence of the premise.

The package moves up. With no indexed corpus, somebody running
`controlbun.load()` against the three real directions is the thinnest real path to
a first user that exists, so it matters more in this lane rather than less.

**One thing this lane does not simplify, despite appearances.** `author` still
cannot become a verified account. The strongest argument for that was the indexed
corpus, but two others survive: every row in the corpus today has an author with
no account, since the three real ones were hand-entered and the five fixtures are
synthetic; and attack cards, independent evaluations and support cards all name an
author who is not the submitter. `V2.md` section 1 now gives all three, so the
namespace-and-claim design holds on its own.

**Supersedes:** nothing. Sequences "The seed corpus is indexed, not submitted"
behind v1, the package, and v2 contribution.

## 2026-09-16 Recipes are namespaced, anyone publishes, and there is no list
**Decided:** A recipe is identified by its namespaced versioned `profile`, exactly
as `001_init.sql` already declares. Anyone publishes one without asking.
controlbun publishes recipes under its own namespace like any other author and
holds no privileged position. **There is no page listing available recipes and
there is no set of them.**

`controlbun.extract(artifact, model)` resolves a profile and runs it **on the
caller's hardware**. The registry never runs a model, has no compute, and has no
queue. Locally for anyone with weights, NDIF for anyone without, which is free
for researchers and is what the arena already used.

**Why the no-list clause is the load-bearing half.** `supported methods` is on the
trip-wire list in `CLAUDE.md`, verbatim. If the registry ships the recipes then
the registry decides which methods exist, and that is designation at the method
layer, which is the one layer nobody had looked at. It arrives disguised as
convenience: a "browse available recipes" view is obviously useful and is the whole
failure.

**The test, and it has to stay structural rather than editorial.** Can a stranger
publish a working profile without asking, and does `extract()` find it. The moment
there is a curated list of the recipes controlbun provides, it is a
supported-methods list regardless of what the copy says.

**Recipes stay declarative.** `profile` plus `payload_json`, parameters and not
scripts. `soham/arena-contrast-v1` carries `estimator`, `token_masking`,
`contrast_source`, `confounds_orthogonalized`: there is no code in it. Shipping
other people's scripts is arbitrary code execution by design, and this project
already refused `numpy.load(allow_pickle=True)` for exactly that reason, in
`artifacts/ingest_arena.py`: "a registry that hands out other people's array files
cannot be in the business of asking readers to trust a flag default." A profile
that genuinely needs to be executable declares a `container_digest`, which is
already in the table.

**Consequence worth stating.** `extract()` output cannot be verified against a
committed hash. Same recipe, same model, different GPU and kernels gives a
different tensor. That is already covered: `Reproduction` "reports its delta
rather than a pass", and cosine is a displayed fact rather than evidence of
disagreement.

**What this makes impossible:** a recipes index, a methods browser, any interface
needing the full set of profiles in advance, and a curation role over methods. The
division of labour is users bring the dataset and the compute, anyone brings the
recipe, and we are one of the anyones.

**Supersedes:** nothing. Makes explicit what `001_init.sql` and `CLAUDE.md`
already implied about profiles, and adds the prohibition that was missing.

## 2026-09-16 Attacks can be attacked
**Decided:** An attack targets an intervention **or** another attack, exactly one.
`author_disposition` and `author_response` become target-side fields, because the
party under attack is not always an author.

**Not built.** Needs a migration; `attack.intervention_id` is currently
`NOT NULL REFERENCES intervention`, which is the thing in the way.

**Why this is required rather than nice.** Count what the current table gives each
side. The attacker gets `method`, `result_json` and `run_id`: structured evidence
with provenance. The party under attack gets `author_response`, a prose field. So
an attack is the last *evidenced* word, and an unrebuttable attack is an
authoritative attack. That is designation moved down one layer, from the artifact
to the evidence about it, and it is harder to catch there because it looks like
rigor.

An attack is itself an empirical claim and can be wrong. carol's is
`alternative-confound-axis` with a measured sentiment number; her confound
direction could itself be confounded and her probe set could be bad. There is
currently no way to say so with evidence, only in prose owned by the person she
attacked.

The field rename is the tell that the generality was always there. Those fields
were never about authorship, they were about being the party under attack.

**Regress does not terminate, and that is consistent.** Nothing settles a chain of
attacks, the same way nothing settles ten claimants on one label. The registry's
answer in both cases is to make the disagreement legible and resolve none of it.

**Still open, and not decided here: the render rule.** A depth-five tree on an
artifact page is a forum, which is already rejected: "a comment attached to one
artifact argues with one author, while the disagreement this registry is about
happens between claimants of the same label." Probably attacks on the artifact,
each showing whether it has been contested, the contest one level in, deeper on
its own page. That is a rendering decision and it is unmade.

**Supersedes:** nothing.

## 2026-09-16 IDEA: `controlbun.agentContext` ships the manual to whatever writes the code
**Not decided, not built.** A document about the API and how to use it correctly.
`controlbun.agentContext()` returns it, so a coding agent helping somebody apply
an artifact reads the current thing rather than reconstructing it from training
data that is stale or about a different library.

**Why it matters here more than it would elsewhere.** `BRIEF.md`'s third failure
mode is silent misuse: a vector applied at the wrong layer, hook point or chat
template does not fail loudly, it appears not to work. An agent writing steering
code from memory gets the layer convention wrong, or treats the coefficient as a
fraction of activation magnitude when it is a raw multiplier of a unit vector,
and nothing complains. The application contract is exactly what this document
carries, to exactly the thing that gets it wrong.

Same argument as "The consumer surface is a package", one step out. The page
**displays** the contract, the package **enforces** it by refusing bytes that
disagree with their record, and this **tells whoever is authoring the call site**.

**It passes no judgment on artifacts, and does not need to.** The API already
refuses to designate: `load("kindness")` raises `BareLabelError`, and
`load("soham/pro-human")` raises `Ambiguous` and names the three current versions.
So documenting the functions accurately is sufficient. An agent that reads what
`load` actually does has learned that a bare label does not resolve, without the
document editorializing about plurality. Anything beyond describing the API is
scope this idea does not have.

**One practical note: generate it rather than write it.** A hand-maintained
document drifts from the code it describes, and this repository has produced that
failure three times in a week: a scanner that enumerated two directories, a link
checker that globbed one filename, an attestation inventory kept by hand. Derive
it from the signatures and the schema, and date it.

**Open:** whether the surface is a package call, an `llms.txt` at the domain, an
MCP server, or several. Not v1.

**Supersedes:** nothing. Extends "The consumer surface is a package" (2026-09-14)
to a third surface.

## 2026-09-16 Fetched bytes are checked against a recorded digest, where there is one
**Decided:** `schema/migrations/006` adds `artifact_sha256` to `intervention`,
nullable. `client.Submission._check` now takes bytes rather than a tensor and
refuses a file whose sha256 disagrees with that column, before the parser sees
it. `falsifier/verify.py` gains `check_artifact_digests_match_the_record`, which
recomputes it for every row whose bytes are in this repository and reports itself
inert when there is nothing to recheck. Both seeds record the digest from the
bytes on disk rather than transcribing one, and `artifacts/seed.py` refuses to
seed at all when what it computes disagrees with what `artifacts/source.py`
recorded at ingest.

**Why:** nothing checked the bytes. `fetch.resolve` returns them from our served
copy, from the author's repo, or from disk, and two of those are somebody else's
server. `_check` compared shape and dtype and said in its own docstring that it
was not going to check the norm. The falsifier recomputed shape, dtype and norm
only for rows whose file is already here, which is every row today and none of
the rows the fetch path exists for. So a re-pointed LFS object or a compromised
CDN edge returns a different float32 [5120], it satisfies both recorded facts
because a great many tensors do, `vector()` hands it over, and `_cache_path`
writes it under a key whose comment reads "cached forever, because a SHA is
forever".

The ingest path in this repository already did this correctly.
`artifacts/ingest_arena.py` verifies a sha256 before it parses and again after it
writes. The client path was strictly weaker than the ingest path against a worse
threat model: ingest runs once on the author's machine, the client runs on
everybody else's. That asymmetry inside one repository is the finding.

**Nullable, deliberately.** An artifact this registry points at rather than holds,
whose bytes nobody here has fetched, has no digest anybody recorded.
`artifact_path` is already nullable and the pointer-only case is the normal one
under "Upload preferred, pointer available". NOT NULL would not produce a digest,
it would produce a string, which is the argument 005 makes about `model_revision`
and 001 makes about recipes. It is worse here than in either, because this value
is load-bearing: a revision somebody typed in anyway misleads a reader, and a
digest somebody typed in anyway makes the client refuse the author's own bytes
permanently and name them as the forgery.

**The erosion risk is the mixed corpus, and it is not hypothetical.** Once some
rows carry a digest and some do not, the difference reads as a quality signal:
verified against unverified, which is two words off the trip-wire list. Then it
becomes a badge, then a filter, then a bar for publication. Absence renders as
absence, as everywhere else. An artifact nobody hashed is checked on shape and
dtype and handed over, and a client that refused it would have made the column
mandatory without anybody deciding to.

**What this makes impossible to express:** bytes that legitimately move under a
published version. An author who re-encodes their file, or whose host migrates
it, or whose safetensors writer orders the header differently, now gets a refusal
naming their own artifact. That is a real cost and the answer is the one
immutability already gives: publish a new version rather than edit a frozen one.
It also cannot help the case it was written for, offline. The falsifier only
reaches files that are here, and the row that records a digest and points at
someone else's repo is checked at the moment the client fetches it or not at all.

**Safety:** this reduces misuse surface rather than adding to it, and adds no
distribution capability. It is a refusal, not a route.

**Two incidental findings, recorded because they were not in the review.** The
positive control in `tests/test_artifact_check.py` was built from a reconstructed
`np.arange(8)` rather than from alice's file, so "the recorded artifact loads" was
testing bytes that were never the recorded artifact; it reads the committed
fixture now. And the synthetic half of the falsifier check is the weak half, since
`fixtures/build.py` hashes files it wrote in the same run: the three vendored rows
are the ones where the digest reaches the database only by matching an
independent record, and both scripts say so where a reader will hit it.

**Where the guard against tightening lives.** `tests/test_artifact_digest_bite.py`
asserts nullability against `PRAGMA table_info` after every migration has run,
rather than against the text of 006, so a later migration that rebuilt the table
and added the constraint fails rather than reads clean. Not added to the invariant
list in `CLAUDE.md`: that list is the plurality premise made executable in
`tests/test_invariants.py`, and this is a correctness check in the client and the
falsifier. Raise it if that reading is wrong.

**Supersedes:** nothing.

## 2026-09-17 The picker's two open fields are a combobox built over the datalist, not instead of it
**Decided:** The `kind` and label fields on the home page keep shipping as
`<input list>` over a `<datalist>`. A script reads its words back out of that
datalist, removes the `list` attribute so the browser does not draw its own
popup underneath, and builds a `role="combobox"` over a `role="listbox"` in its
place. Filtering is substring, and the order is: what the corpus holds, then
exact, then prefix, then the start of a hyphenated part, then anywhere, then the
order the page emitted. Whatever is typed is always offered back as the last row
of the popup and is never rewritten on the way out, by Enter, Tab, Escape or
blur.
**Why:** The native popup is unstyleable and looks like a fragment of somebody
else's site dropped into the middle of a serif sentence, which is what prompted
this. Replacing it with a script-only control would have cost the no-script
reader the ninety-five suggestions and left an `<input>` with nothing behind it,
so the datalist stays and becomes the fallback rather than the casualty. One
copy of the list in the page serves both readers.

**Free text is the decision; the widget is not.** `kind` and the label are open
strings in the schema, so a control that only takes its own list declares which
concepts are legitimate: the closed-enum failure arriving through a widget
instead of through a `CHECK`. Nothing in the control can reject what is typed.
There is no commit step, the input's value is the answer at every moment, and
the row that hands the typed text back is what makes that visible at the one
moment it matters. Saying it in prose instead would be the site arguing with an
objection nobody raised, which is the category cut everywhere else on this page.

**Corpus first is about provenance, not quality.** The entries at the top are
the ones a reader can go and read on this site. They are not better, and the
annotation beside them says "in the corpus" rather than anything that could be
read as an endorsement. The rule is load-bearing: on a query like `hum` the
corpus entry `pro-human` matches after a hyphen while `humility` matches as a
prefix, so the corpus is only at the top because the corpus is at the top. A
bite test drops the clause from the comparator and checks the order changes.

**What this makes impossible to express:** a suggestion list with any structure
of its own. The nine groupings in `observed-labels.ts` are flattened before they
reach the page and stay flattened, because a popup with headed sections is a
taxonomy and publishing one says which concepts belong where. It also gives up
anything a suggestion could carry beyond its own name: no counts, no recency, no
"others also typed". Each of those is a ranking signal wearing a smaller hat,
and the field would start recommending rather than completing.

**Safety, named rather than resolved.** This makes concepts easier to find by
typing, and some of the words in that list are refusal-adjacent. It adds no
route to anything: v0 takes no uploads, serves no API, has no bulk fetch, and
the picker resolves to no page. So the misuse surface is unchanged and the
discoverability is slightly better, which is the open-contribution and
misuse-gating tension in its mildest form. Worth knowing it is here before
anything on this page is ever wired to a fetch.

**Where the behaviour is checked.** `tests/combobox_harness.py` runs the real
script out of the real built page in Node against a DOM only as large as the
script uses, on the same argument as `ordering_harness.py`. A type-ahead is a
worse case of the dead-control bug than a button is: a field whose script never
ran looks exactly like a field nobody has clicked, so presence in the markup
proves nothing at all. `tests/test_picker_bites.py` reintroduces ten specific
failures and asserts each check goes red.

**Supersedes:** nothing.

## 2026-09-17 A writer states what it claims about an artifact and the bytes confirm it
**Decided:** `registry.artifact` gains `Claim`, `Facts`, `disagreements` and
`confirmed`. A caller hands over artifact bytes plus whatever it claims about
them and gets back the facts to record, or a refusal naming both sides of every
field that does not match. Shape, dtype, L2 norm and sha256 are compared.
`fixtures/build.py` and `artifacts/seed.py` both go through it and neither types
a tensor fact into an `INSERT` any more. `client.Submission._check` and both
falsifier checks call the same comparison, so there is one of it rather than
three.

**The claim is checked, not replaced, and getting that backwards is the whole
failure.** A function that recomputed and overwrote would be shorter and would
throw away the thing worth having. `artifacts/seed.py` records `[5120]`,
`float32` and a unit norm because those are cited: 5120 is the residual width of
the model the arena ran, the ingest refuses anything but a 1-D float32 array,
and `artifacts/REAL.md` states the shipped directions are unit-norm. The value
of that row is that the citation and the bytes agree. Recompute over it and the
column holds a number that agrees with the bytes by construction, which is the
same nothing `fixtures/build.py` already says its own digest is worth. So a
claim that survives is what gets recorded, and a caller with nothing to claim
gets the derived value.

**Why:** `S1` made `artifact_sha256` derived from the bytes and left the three
fields beside it in the same statement as literals somebody had typed. The
values were right. The mechanism was that somebody had been careful, and it has
no failure mode short of being wrong and staying wrong, because every later
check reads the row. Downstream does not save it: the client and the falsifier
compare arriving bytes *against* the record, so a record that is wrong is not
corrected by them, it is enforced by them. A mistyped shape makes the client
refuse the author's own artifact and name their bytes as the substituted ones,
which is the harm `006` already named for a mistyped digest.

**The tolerance question, answered once.** A digest identifies a file and has no
tolerance. A norm is derived at both ends and the two ends can derive it
differently: `d_olmo3_v1.safetensors` norms to exactly 1.0 read as float32 and
to 1.0000000000683045 promoted to float64. `artifact.L2_TOLERANCE` is 1e-4,
which is the number `falsifier/verify.py` already applied, and the two are now
one constant on purpose. A write-time rule stricter than the gate that rechecks
the row later refuses rows that would have reconciled; a looser one admits rows
that gate rejects after they are published. Equal is the only setting at which
the two agree. The value is bounded by a test to the band `.toFixed(4)` implies:
at least half of the last rendered digit, because a citation read off a page is
only knowable to that, and no more than one whole rendered digit, because
anything larger records a norm as agreeing while it renders as a different
number.

**The read path claims three of the four, deliberately.** `_check` claims shape,
dtype and digest and does not claim the norm. Its old reason, that repeating the
norm here with a stricter rule would reject good artifacts on a rounding
difference, is void now that there is one tolerance. The real reason is that a
tolerance-bearing claim is worth enforcing where it is authored, because that is
the moment it can still be corrected. Enforcing it again at read time, against a
row that is frozen and immutable, makes a published artifact permanently
unfetchable over a descriptive float no application reads: coefficients scale
against `activation_norm`, not this one. An identifying claim is enforced
everywhere and a descriptive one where it is written.

**What this makes impossible to express:** a row that describes an artifact
differently from how the artifact reads. That sounds like nothing lost and is
not quite. An author who records the norm their extraction script printed, in
float64, against a float32 file that reads slightly differently, is now refused
at write time on a difference that is real and uninteresting; the tolerance is
what keeps that from biting and the tolerance is a judgment. An author whose
tensor is genuinely two-dimensional, or whose file holds two tensors because the
second is a bias, cannot be written at all. Those are not hypothetical
plurality: `kind` is an open string and an SAE latent or a ReFT edit may not be
one 1-D tensor. What this does not do is make any field required. Claiming
nothing is a state and returns the derived value, and no column became
`NOT NULL`.

**Safety:** a refusal, not a route. No new distribution capability, nothing
fetched in bulk, and no upload path. The write path this prepares is v2 and is
still gated on the dual-use policy.

**Where the guard lives.** `tests/test_write_claim_bite.py`. Twelve mutations of
the implementation were applied and each one was confirmed to turn a check red,
including two that were green the first time and had to be closed: a writer that
checks the bytes and then types the value next to the result, and a tolerance
widened until every probe stated as a multiple of it slides through. The probe
that matters is the pointer-only row, where a wrong shape reaches the database,
the falsifier cannot see it because it is offline by design, and the client then
refuses the author's correct bytes. Not added to the invariant list in
`CLAUDE.md`, on the same reading as `006`: that list is the plurality premise
made executable, and this is correctness in the writers and the client. Raise it
if that reading is wrong.

**Three incidental findings.** The falsifier was the third implementation of the
same comparison rather than a bystander, and it held its own copy of the
tolerance. Its shape derivation was `f"[{vector.shape[0]}]"`, correct for every
1-D tensor in the corpus and silently wrong for the first artifact that is not
one; it reads `str(list(tensor.shape))` now, which is what the client and both
writers use. And the two writers were making different kinds of claim under one
appearance: `artifacts/seed.py` cites, while `fixtures/build.py` restates what
`write_vector` promises twelve lines above it. Both are checkable and only the
first is provenance.

**Supersedes:** nothing. Pays off item 4 of `V2.md`'s order list, and finishes
what "Fetched bytes are checked against a recorded digest" (2026-09-16) started
on the read path.

## 2026-09-17 Ingest takes bytes from anywhere, and the converters are not a permission list
**Decided:** `registry.ingest` is the general path: a source, a `Claim`, and one
checked safetensors file out. `artifacts/ingest_arena.py` keeps its pinned table
and its `--check` mode and calls it. The three vendored artifacts are byte
identical, confirmed by a live refetch from the pinned commit and not only by the
recorded digests.

Four pieces, and each one is a seam somebody outside can use:

- **Sources** are a two-method protocol, `read` and `provenance`, with no base
  class. `LocalBytes` for an upload or a file, `PinnedURL` for one URL pinned to
  a digest, `PinnedRepoFile` for a path in a repo at a commit. A source's
  provenance is derived from the fields it already holds rather than handed in
  beside it, so there is no second copy of a commit to go stale, and
  `PinnedRepoFile` takes a URL template rather than choosing from a table of
  hosts we happen to know.
- **`FORMATS`** is a mutable dict of `sniff` plus `read`, keyed by content and
  never by filename, because a filename is a claim and the bytes are the fact.
  `.npz` and `.safetensors` ship. A format nobody wrote a converter for is
  refused with a sentence naming what has one and where another goes.
- **Pickle is refused rather than unsupported**, and the distinction is the whole
  point. Two layers, neither covering the other: `zipfile` reads the member list
  without decoding anything, which catches an archive carrying a pickle, and
  `allow_pickle=False` inside the npz converter catches an object array inside a
  member named like every other one, which the member scan cannot see.
- **The output is staged and moved into place only after it is checked.**

**Why the format set is the interesting part.** A list of formats is the
closed-enum failure at file level: `method: a / b / c` for containers. `kind` is
an open string and this is the same kind of thing. What ingest is entitled to
decide is not which ways of packing a tensor are legitimate, it is which bytes it
can read without executing them, and those two sentences look similar and are
nothing alike. The first is a rule about contributors. The second is a statement
about this code, and it is why a pickle gets refused while an unrecognized
container gets an apology and a pointer at the dict.

So `format` joined the vocabulary that `test_no_check_constraint_enumerates_strings`
refuses next to `kind`, `hook`, `profile` and `method`. Tightened, not relaxed:
nothing in the tree matched when the word was added, and narrowing the pattern
back makes the new probe in `tests/test_invariants_bite.py` go silent, which is
how the word is known to be doing work.

**Not exported from `registry/__init__.py`.** That module is the consumer
surface, and a read-only client package advertising an ingest entry point would
be advertising a write path that does not exist. Nothing here serves, uploads or
mirrors anything: `schema/migrations/004` is explicit that serving a copy makes
this a distributor and needs the dual-use policy, which is deferred. Ingest ends
with a file on local disk and what happens to it afterwards is a separate
decision.

**Three findings that were not in the brief.**

The old `convert` saved over the committed artifact and compared the result
afterwards. A drifted conversion therefore reported the drift correctly, exited
nonzero, and had already replaced the bytes the recorded digest identifies. The
next `--check` compared the bad file against the record and failed again, which
is right and far too late. Staging and renaming is not tidiness, it is the fix.

`safetensors` header order is unstable across processes, as `registry.artifact`
already says, but only visibly so with enough keys: with two metadata keys two
processes agree about half the time. The first version of the reproducibility
probe used two, and removing `sort_header` altogether slid past it. Twelve keys
and six processes, and the probe asserts the unsorted control produces more than
one digest so it cannot pass by safetensors having become deterministic.

CPython invalidates a `.pyc` on source size plus mtime **truncated to seconds**.
A mutation that swaps one character for another keeps the size, so a same-size
edit applied in the same second as the previous run reuses stale bytecode: the
mutation is on disk, never loaded, and the probe reports that the check does not
bite when the check is fine. That happened while proving these checks bite, which
is the failure this project keeps producing, arriving in the harness built to
catch it. Anything that mutates a file in place and reruns needs
`PYTHONDONTWRITEBYTECODE`. The existing bite tests are safe because they patch
copies in a fresh directory.

**What this makes impossible to express.** A format this path cannot read without
running it. That is a real loss and it is named rather than hidden: an author
whose artifact only exists as a `.pt` cannot ingest it here, and the answer is a
conversion they run, not a flag we set. Second, a source with no digest at all.
`PinnedURL` requires one because a fetch by name resolves to whatever is there
today, and `LocalBytes` does not, which is the honest split: bytes in hand have
no transit to be substituted in. Third, a payload key that collides with a
provenance key, which makes re-ingesting an already-ingested file a refusal
rather than a silent overwrite. Nothing became required: a caller claiming
nothing gets the derived facts, as `confirmed` already did.

**Safety:** refusals, not routes. No upload path, no API, no bulk fetch, nothing
served, and one fewer way to load a file that executes on load. The single new
network capability is a GET at a URL pinned to a content digest, which is
narrower than what `fetch.from_hub` already does.

**Where the guard lives.** `tests/test_ingest_bite.py`. Sixteen mutations of the
implementation were applied one at a time and every one was confirmed to turn a
named probe red, including the two above that were green the first time. The
probes that matter: a converter spy that asserts the parser is never reached
rather than merely that an exception was raised, a pickle that records having run
so the flag is shown to be load bearing rather than asserted to be, and a
round-trip of `arena_payload` against the committed headers, which is the only
offline check that would notice the conversion changing before somebody reruns it
with network months later. Not added to the invariant list in `CLAUDE.md`, on the
same reading as `006` and the write-claim entry, with one reservation: the open
converter set is the plurality premise at field level rather than a correctness
check, so it may belong there. Raise it.

**Supersedes:** nothing. Implements "safetensors on ingest, always" (2026-09-11)
for sources other than one GitHub commit, and is the shared path the v2 write
step in `V2.md` section 2 would call.

## 2026-09-17 No dual-use policy yet, and the trigger is a capability rather than a date
**Decided:** Do not write one now. `POLICY.md` was drafted and became
`WHAT-IT-DOES.md`, which keeps the verified description and drops the positions.

**Why now is wrong.** A policy governs decisions and there are none. Nothing can
be submitted, nothing is served, and `fetch.py` sends no credentials at anything.
The four questions `BRIEF.md` says need answers before launch, bulk fetch, rate
limits, gating behind identity, and takedown, are all about distribution, and
there is no distribution. `CLAUDE.md` blocks *distribution features* on the
policy, not the site's existence.

Drafting it now also means committing to positions against imagined submissions.
A policy written against hypotheticals is usually wrong against the first real
case, and this one would be published under the author's name.

**Most of the draft was not policy.** It was a description of what the system
does: no bytes served, no API, no bulk fetch, no rate limit because there is
nothing to limit, nothing ranked, no popularity signal collected. Those are true
and useful regardless, and they answer the question a stranger reading the site
cold left with, "is this live, a prototype, or a proposal". Calling that file
`POLICY.md` mislabelled it and made description look like commitment.

**The trigger, and it is a capability rather than a date.** Write it before
whichever of these happens first:

- **Anything is served as bytes.** `004_served_copy.sql` is explicit: serving a
  copy makes this a distributor rather than an index, and "we only pointed at it"
  stops being available as an answer.
- **Anything can be submitted.** `V2.md` makes the review criterion schema
  validity plus dual use. Without the second, review has no rule and becomes
  taste, which is the erosion that entry is mostly about.
- **A bulk or listing surface exists**, including a machine-readable dump of the
  corpus.

**One thing the deferral costs, recorded rather than argued.** `BRIEF.md`:
"This also determines whether labs and academic groups engage at all, which
determines whether reputable players' vectors ever actually show up." Without a
stance, the people whose artifacts would make the corpus worth reading may not
touch it. That is an argument for writing it before soliciting contributions
rather than before existing, which is what this entry says.

**Supersedes:** nothing. Refines the 2026-09-15 override, which deferred the
policy past launch without saying what would end the deferral. This says what.

## 2026-09-18 The author publishes his own artifacts, and the registry records the pin
**Decided:** `artifacts/publish.py`, four separable steps: `plan` prints what
would happen and touches nothing, `push` uploads, `record` writes the pin, and
`verify` fetches it back and compares. The pin is `artifact_repo` plus
`artifact_commit`, in the author's own Hub namespace, defaulting to
`sohampadia/pro-human`. `huggingface_hub==0.36.0` becomes an optional
`publish` extra, needed by `push` and by nothing else.

**Why now.** `fetch.resolve` has three branches and the corpus only ever took
the third. Every real row records a local `artifact_path` and no remote, so the
Hub path existed, was covered by tests against a stand-in server, and had never
run against the real host for a real artifact. A client installed anywhere
without a checkout could not load anything. Publishing the four directions is
what turns `client.load("soham/pro-human@L24").vector()` into a true sentence
off this machine.

**The author's namespace, not `controlbun`.** `artifact_repo` is where the
author put a thing and `served_repo` is where this registry serves a copy from,
and `004` keeps them apart so a mirror that drifted from its origin is
expressible. Nothing here writes the second pair, and that is the line the
dual-use deferral turns on: the 2026-09-17 trigger fires when *this* serves
bytes, can be submitted to, or grows a bulk surface. An author uploading his own
file to his own account, with the registry recording a pointer, is none of the
three. It adds no capability a reader did not already have, since the artifact
is public at a URL either way; what it adds is that the pointer is checkable.

**Two findings that changed the design.**

The path inside the Hub repo has to equal `artifact_path` character for
character, because `fetch.resolve` hands one path field to whichever of the
three sources it picks. `004` says "our copy keeps the author's filename" and
reads like a remark about tidiness; against the code it is a constraint. So the
files go to `artifacts/soham/...` inside the Hub repo rather than to its root,
and `plan` prints the path twice so the `hf upload` argument that would get this
wrong is visible before it is run. The alternative was a seventh migration
adding a remote path column, which buys a nicer-looking repo and a second place
for a path to go stale.

A pin written only into a column does not survive `make site`, which drops the
database and rebuilds it from `fixtures/build.py` and `artifacts/seed.py`. The
row would fall back to the local file, which is present on the machine that ran
the build and nowhere else, so the regression is invisible exactly where it is
introduced. `artifacts/published.json` is the durable record, `apply_pins` is
the only function that writes those two columns, and both the rebuild and
`record` call it.

**A commit, never a branch, and the rule is not restated.** `record` goes
through `fetch.commit_sha`, so `--at-head` reads what `main` points at and
freezes the answer rather than recording the name. Resolving a branch is done
here and not in `registry.fetch`, which says in its own docstring that it does
not resolve one: a helper sitting next to that sentence is one refactor away
from being wired into the read path.

**What this makes impossible to express.** An artifact whose remote path differs
from its local path, which is the constraint above and is a real cost to anyone
whose Hub layout is already fixed; the answer is a column, and it should be
added when somebody actually needs it rather than in advance. A pin to a moving
reference, which is the point. And publishing anything from `fixtures/`, which
`select` leaves out: a fabricated direction uploaded under the author's name
would publish a file whose whole purpose is being not one.

**Nothing became required.** Both columns stay nullable and empty is the normal
state. A row with no pin resolves locally, exactly as before, and `verify` on an
unpinned corpus reports that there is nothing to check rather than failing.

**Safety.** No upload endpoint, no submission form, no public API, no bulk
fetch. The only new network write is the author pushing his own bytes with his
own token, read from `.env` and printed nowhere. `verify`'s refusal is the
substantive half: a commit that resolves to *something* is indistinguishable
from a correct one until the bytes are compared, and a wrong pin is worse than
no pin, because the client then refuses the artifact and names the author's own
file as the substituted one.

**Where the guard lives.** `tests/test_publish.py`, offline against a stand-in
Hub. The probes that matter: `plan` pointed at a dead host, so a dry run that
reads anything remote fails; the local path and the path in the repo asserted
equal on every planned upload; a rebuild that has to keep the pin; a pin naming
no row refused rather than silently updating zero rows; and a commit serving
different bytes under the right path, which is the failure a live upload cannot
rule out by itself.

**Supersedes:** nothing. Pays off the remote branch of `fetch.resolve`, which
has been written since 2026-09-14 and unexercised against the real host.

## 2026-09-18 Intake is a form on 127.0.0.1, and the binding is what keeps it clear of the dual-use trigger
**Decided:** `artifacts/intake.py serve`, a standard-library HTTP server bound to
127.0.0.1, with two modes that end at the same place: a row pointing at a pinned
remote. Link mode takes a repo, a commit and a path, fetches once into a
throwaway cache, checks the bytes and keeps the pointer. Bytes mode takes a file
up to 500 MB, converts and checks it outside this repository, pushes it to the
author's own namespace through the extracted `publish.upload`, records the pin
and deletes the staged file. The form writes the `submission` and `intervention`
rows, not just an artifact pointer. Nothing writes `served_repo`.

**Why the binding is the decision and not an implementation detail.** The
2026-09-17 trigger fires when anything can be submitted. This accepts a file and
writes rows, which is a submission route by every description except who can
reach it, and who can reach it is the entire difference. So the constraint lives
in code rather than in a sentence: the listener takes its address from one
constant, there is no `--host`, and three more checks sit on top of the bind
because the bind alone is not enough. A per-run token, in the URL the command
prints and nowhere else. The `Host` header, because a hostname that resolves to
127.0.0.1 walks straight through a loopback bind. `Origin` and `Sec-Fetch-Site`,
because a page the operator did not open, in the same browser, can post to a
loopback port. `tests/test_intake.py` holds all four.

**The wall is checked on the other side too.** The way this leaks is not somebody
rebinding the socket. It is a form appearing on the published site in six months
with nothing failing, because the pieces were sitting in the repo and reader
convenience won once. So the same test file reads `astro/dist` and fails the
build on a form element, a POST target, an upload encoding, a file input,
`XMLHttpRequest`, `sendBeacon` or a loopback address; asserts `astro.config.mjs`
is still `output: "static"` with no adapter; asserts no page exports a POST
handler; and asserts the view layer does not mention this tool at all.
`astro.config.mjs` already said a build that emits files cannot drift into being
a public surface the way a running process can. This is the running process, so
it pays for the asymmetry with checks the static build does not need.

**Nothing here decides what an artifact may be.** `registry.ingest` owns which
bytes can be read without executing them and answers with an open converter set.
`registry.artifact` owns the comparison between a claim and the bytes.
`registry.fetch` owns the rule that a pin is a commit. The form owns a socket,
some HTML and two INSERTs, and every rule it appears to apply is one of those
three being called, refusal sentence included. Fields are text inputs over
datalists, which is the precedent `astro/src/data/observed-labels.ts` set: the
suggestions are read out of what the corpus already holds, so there is no second
taxonomy to go stale, and there is no `<select>` anywhere on the page. A dropdown
of permitted values is the closed enum arriving through a control.

**The cap is worded as what it is.** 500 MB, because the form holds the whole
file in memory to digest, sniff, convert and recheck it before anything is
written, and that order is the security property. The refusal says that, says it
is a cap on this form on this machine, and points at link mode, which has no
limit because it holds nothing. Invariant 7: refuse what cannot be verified and
say that, never that something is not supported.

**Three findings.**

`publish.py`'s "never `controlbun/*`" was prose in a docstring, which is the
shape `CLAUDE.md` calls aspirational. It is a check in `publish.upload` now,
because the second caller takes its repo out of a text field and the difference
between publishing your own bytes and serving a copy of somebody's is one word
typed into a box.

`make site` deletes `registry.db`, so a row written by this form is gone on the
next build. `artifacts/intake.jsonl` is the durable copy, append-only and
tracked, and `insert` is the one function both the live write and `replay` call.
That is `published.json`'s argument about two columns, applied to twenty.

**`make site` does not replay the record, and that is left open.**
`falsifier/verify.py` fails any row whose `artifact_path` has no file on disk,
and every row this writes is one of those: the bytes are at a pinned remote,
which is the normal case the registry was designed for and the case the falsifier
has never seen, because every row in the corpus today is local. Teaching it that
a pinned remote with no local copy is a state rather than a missing file is a
change to the gate and belongs in its own decision. Until then the replay is a
command the operator runs.

**What this makes impossible to express.** A submission from anybody but the
operator, which is the point and is the cost: the tension `CLAUDE.md` names
between open contribution and misuse gating is not resolved here, it is deferred
by making the only write path local. An artifact whose bytes are neither
published anywhere nor small enough to pass through this machine's memory, which
is a real gap and the answer is publishing them first, not raising the cap. And
a linked artifact that is not already safetensors: link mode records a pointer
the client will parse for itself, so converting it here would leave the row
pointing at one file and describing another. Bytes mode converts, and publishes
what it converted.

**Safety.** No public endpoint, no bulk fetch, no listing surface, and nothing
served. The one new network write is the author pushing his own bytes with his
own token, read the way `publish.py` reads it and printed nowhere, including in
the request log: the run token is in the URL, so the log prints the route and not
the request line. The new local capability is a process that accepts a file, and
every property that keeps it local is a test rather than a habit.

**Supersedes:** nothing. Builds on 2026-09-18 "The author publishes his own
artifacts, and the registry records the pin", whose `push` became `upload` so
two callers share one network write.

## 2026-09-18 GAP: `layer` is one integer, so a band cannot be stated at all
**Found, not decided.** `001_init.sql` declares `layer INTEGER NOT NULL`. An
artifact whose direction is `(21, 8192)` over layers 30 to 50 has no way to say
so. Recorded as a gap rather than fixed, because v0 scope is fixed and this is
schema.

**How it surfaced.** A real submission attempt, against a Llama-3.3-70B
direction library built outside this project. The author's agent worked the
whole contract out of their files and then stopped on this one: the vector it
was asked to submit is a band, the author's own record names layer 34 as the
one they evaluate at, and taking that slice is a real answer that throws away
twenty other rows of a tensor somebody deliberately built. Its words were that
the layer field cannot express it and we should talk about it, which is the
correct escalation and not something the prompt told it to look for.

**Why this is the premise and not an inconvenience.** The trip-wire list catches
a closed enum on a user-supplied field, and this is the same assertion arriving
through a column type: `INTEGER NOT NULL` declares that a steering artifact is a
thing that exists at one layer. Nobody decided that. It is the shape of the
first four artifacts, which are all single-layer, generalized into a constraint
by being written down once. The inverse question answers itself here: what this
makes impossible to express is a multi-layer intervention, and people build
those.

**What is not the answer.** Twenty-one rows, one per layer. The 2026-09-14
decision against turning a five-point sweep into five rows already settled that,
and it settled it for the same reason: a sweep is one artifact somebody made,
and exploding it into rows makes the registry assert a granularity the author
did not.

**Not fixed here.** Three shapes are worth weighing when it is: `layer` widening
to carry a range with its convention, a `layers` column that a single-layer
artifact fills with one element, or the band living in the recipe payload the
way non-Hub provenance does, which the 2026-09-14 entry already calls a gap and
would make this the second thing hiding there. The third is the cheapest and is
probably wrong for the same reason it was wrong the first time.

**Supersedes:** nothing. Related to 2026-09-14 "Non-Hub provenance lives in the
recipe payload, and that is a gap", which is the same kind of entry.

## 2026-09-18 GAP: ingest reads any host, but a row can only pin the Hub
**Found, not decided.** The write path is host-agnostic and the read path is
not, so an artifact published on GitHub can be ingested and cannot be pinned.

**Superseded by:** 2026-09-18 "The row carries its own URL template, so a pin
can name any host", which is the fix. Everything below is the finding as it
stood and the read path no longer works this way.

**The asymmetry, exactly.** `ingest.PinnedRepoFile` takes a `host` and a
`url_template` and its docstring already settles the principle: "A table of the
ones we happen to have met would be a list of where an artifact is allowed to
come from, which is not ours to write." This is not hypothetical support. All
four real directions in this corpus came in through it with `host="github.com"`
and GitHub's media template, because that is where the arena publishes.

Then `fetch.resolve` sends both of its remote branches to `from_hub`, which
builds `{HUB}/{repo}/resolve/{commit}/{path}` and nothing else, and
`intervention` has `artifact_repo` and `artifact_commit` with no column saying
which host they are on. So `github.com/a/b` and `huggingface.co/a/b` are one
string in the row, which is the collision `PinnedRepoFile` names and guards
against on the way in.

**What this makes impossible to express.** Link mode against anything but the
Hub. An author whose vectors live in a GitHub repo, which the author of this
registry says is most of them, has two ways in: republish the bytes to a Hub
namespace, which makes a second copy of something already published and
recorded at a commit; or keep a local file, which is not a pin at all. Neither
records the fact that the artifact is already published, pinned and public
where its author put it.

**The provenance survives and is not reachable.** `PinnedRepoFile.provenance`
writes `source_repo: github.com/owner/name` and `source_commit` into the
safetensors header, so the true origin is in the bytes. Nothing resolves from
it. A fact recorded where no code reads it is the shape this file has flagged
twice before.

**Why it is the premise and not plumbing.** Same failure as the layer gap
recorded above and the closed enums the trip-wire list covers: the schema
asserting what a legitimate artifact looks like, here by making one host the
only one a pin can name. Nobody decided the Hub was the registry's host. It is
where the first artifacts were going and the resolver was written to match.

**Not fixed here.** The shape is already written on the other side: a host
beside the repo, and a url_template in `resolve` the way `PinnedRepoFile`
carries one, so the read path stops knowing any host by name. That is migration
007 plus `fetch`, which is schema, and v0 scope is fixed.

**Supersedes:** nothing. Same kind of entry as 2026-09-18 "GAP: `layer` is one
integer" and 2026-09-14 "Non-Hub provenance lives in the recipe payload, and
that is a gap", which this partly explains.

**Superseded by:** 2026-09-18 "The row carries its own URL template, so a pin
can name any host", which is the fix and takes the shape this entry named.

## 2026-09-18 The row carries its own URL template, so a pin can name any host
**Decided:** `intervention` records `artifact_host` and `artifact_url_template`
beside the repo, commit and path, and `served_host` and `served_url_template`
beside the served pair. `registry.fetch` formats the row's own template and
knows no host by name. There is no table mapping hosts to URL layouts and there
will not be one.

**Why:** `ingest.PinnedRepoFile` settled the principle on the write side and the
read side had not caught up: "A table of the ones we happen to have met would be
a list of where an artifact is allowed to come from, which is not ours to
write." A host nobody here has met now works by construction, with no code
change and no request to anybody. This is the same argument `registry.ingest`
makes about file formats and 001 makes about `kind`; the only difference was
that here the assertion was being made by a missing column rather than by a
CHECK, which is why it survived the trip-wire list for four days.

**What it makes impossible to express: nothing.** It is strictly an addition.
What it removes is the schema's claim that a legitimate artifact is one that
lives on the Hub, which nobody decided. All four real directions in this corpus
came in from GitHub and could be ingested and not pinned.

**Both fields, because neither derives from the other.** GitHub serves file
content from a host its repos do not live on: the host is `github.com` and the
URL is `media.githubusercontent.com/media/{repo}/{commit}/{path}`. And one host
can need more than one layout. Checked with curl against
`soham-padia/steering-arena` at `b8b4721` on 2026-09-18: the media host returned
the 22,424-byte LFS object whose sha256 matches the one `artifacts/source.py`
recorded, `raw.githubusercontent.com` returned the 130-byte LFS pointer for the
same repo, commit and path, and the media host returned 404 for a file that is
not LFS-tracked. Three layouts across two hosts, documented in migration 007 and
offered in the intake form's datalists, enforced nowhere.

**Absence is a state, and no row was backfilled.** Every row in this database
records no host, because there was nowhere to record one. `fetch.hub_pin` is the
default those resolve under, so an existing row resolves after 007 exactly where
it resolved before. Writing `huggingface.co` onto them would produce a string
rather than a fact and would read exactly like a fact somebody checked, which is
the argument 005 makes about `model_revision`.

**A template in a row is a fetch target that came out of data, and three things
are checked about it.** None of them is who the host is.

The commit has to survive into the URL's path or query, which is the property a
pin actually is; that closes S2 in `V1.md`, where a repo containing a `?`
silently turned the pin into a query string and fetched HEAD.

The scheme has to be one a fetch can happen over, because a `file:` URL is a
local read wearing a URL and resolves to different bytes on every machine, so
nobody else can check it. That is refusing what cannot be verified. Any http or
https host works, including ones nobody here has heard of, which is the point.

Every placeholder has to be a bare `{name}`. `str.format` is more than
substitution: `{repo:>200000000}` is seventeen characters of template and two
hundred megabytes of allocation, measured, and `{host.__class__}` walks
attributes of the value rather than printing it. The second reaches nothing
here, because the four values are plain strings and the leak that makes this
famous needs a rich namespace. The first is a real allocation out of a row. Both
are refused, and a URL layout has no use for either.

**What was checked and found not to apply.** A redirect cannot reach `file:`;
`urllib.request.HTTPRedirectHandler.http_error_302` on Python 3.13.5 refuses any
scheme but http, https and ftp, read from the installed source rather than
recalled. No credentials are sent, so a hostile host gets a bare GET. `get_url`
reads a response with no size cap, which is unchanged by this and now applies to
a host a row named rather than to the Hub; worth a cap and not settled here.

**What is not guarded, deliberately, and it is a tension rather than a
conclusion.** A row can name a host on the reader's own network, so a consumer
running `client.load(...).vector()` can be made to issue a GET somewhere
internal. Blocking loopback and private ranges would break the `REGISTRY_HUB`
override this project documents and every local stand-in server in the test
suite, and it would be the first step of the host list this entry exists to
avoid. What limits it today is that v0 accepts no uploads, so every row is
written by the operator on their own machine; no credentials are sent; and the
bytes go back to the caller who asked rather than to a third party. **A
submission route changes that, and this belongs in the dual-use policy rather
than being settled here.** Recorded now so it is not discovered later.

**The cache is keyed on the resolved URL.** It was keyed on repo, commit and
path, which collides across hosts, and also across templates: the media host and
the raw host return different bytes for the same repo, commit and path, so the
template has to be in the key too. That is not hypothetical, it is the check
above. Keying on the URL also fixes a smaller bug it did not set out to: a
`REGISTRY_HUB` pointed somewhere new used to read the old host's bytes back out
of the cache.

**Demonstrated end to end on 2026-09-18, against real hosts.**
`fetch.resolve` with `host` github.com and the media template returned the
22,424 bytes of `d_olmo3_v1.npz` at `b8b4721`, sha256 matching the one
`artifacts/source.py` records; the same row with the raw template returned the
130-byte pointer instead, which is the collision the cache key now carries. And
`client.load(...).vector()` against a row pinned on `github.com` with the raw
template returned the tensor, digest checked against the row. That second one
used a scratch database and a public GitHub-hosted safetensors that is not a
steering artifact, because there is no safetensors in a public GitHub repo of
the author's to point at: the arena publishes `.npz`, and link mode records a
pointer the client parses rather than converting it. **That is a gap and not a
defect of this change.** A GitHub-published `.npz` still cannot be pinned in
link mode; the ingest path converts it and the intake form's bytes mode
publishes the conversion to the Hub. Worth deciding separately.

**Supersedes:** 2026-09-18 "GAP: ingest reads any host, but a row can only pin
the Hub", which is the entry that specified this, and 2026-09-14 "Non-Hub
provenance lives in the recipe payload, and that is a gap", whose decision that
the columns stay Hub-shaped is now false.
