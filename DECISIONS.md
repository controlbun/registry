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
