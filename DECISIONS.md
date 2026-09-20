# Decisions

> **Status 2026-09-20.** Live, and authoritative over every other document here.
> Entries are kept after they stop being true, so check one for a
> `**Superseded by:**` or `**Amended by:**` line before acting on it. The index
> below marks them.

Authoritative. If this file and a conversation disagree, this file wins. Add an
entry whenever something is settled, with the date and a one-line reason. Do not
silently reverse an entry; supersede it with a new dated one and say why.

Format:

```

<!-- index: generated, do not edit by hand -->

- `2026-09-11` Arena is upstream, registry is a separate project
- `2026-09-11` The registry never designates; consumers pin, visibly
- `2026-09-11` Direction validity is the blocking research question  **[superseded]**
- `2026-09-11` Out-of-template transfer is a required eval field  **[superseded]**
- `2026-09-11` Evidence is recorded, not required
- `2026-09-11` The registry needs no compute
- `2026-09-11` Eval judge is local weights, not an API
- `2026-09-11` Falsifier pattern is ported from the arena
- `2026-09-11` Schema object is Intervention, not Vector  **[amended]**
- `2026-09-11` Attack is a first-class object
- `2026-09-11` No user ratings, rank on precision and attack survival  **[superseded]**
- `2026-09-11` Popularity drives the audit queue
- `2026-09-11` Plurality is the product
- `2026-09-11` No closed enums; extension points are profiles
- `2026-09-11` Recipe is optional
- `2026-09-11` Submissions are versioned and immutable  **[superseded]**
- `2026-09-11` Running someone else's eval is a first-class action
- `2026-09-11` No ranking by default, sorting is user-chosen  **[superseded]**
- `2026-09-11` safetensors on ingest, always
- `2026-09-11` Canonical traits, free-form tags on top  **[superseded]**
- `2026-09-11` v0 is unblocked; the open items gate launch, not code
- `2026-09-11` A judged score without a coherence measure is uninterpretable
- `2026-09-12` No comparable registry exists; Neuronpedia has storage, not this
- `2026-09-12` Non-identifiability conditions every behavioral criterion
- `2026-09-12` SQLite for v0, not Postgres
- `2026-09-12` A default ordering is allowed; no ordering derives from an eval result
- `2026-09-12` SAEs get cards and evidence; the registry still does not hold them
- `2026-09-12` SAE-latent provenance lives in the recipe, not the schema
- `2026-09-13` Adoption comes from the client being easy, not from the ordering
- `2026-09-13` The ordering control computes what its caption says it computes
- `2026-09-13` The Jinja frontend is retired; Astro is the frontend
- `2026-09-13` The site is published on GitHub Pages, when the repo goes public  **[amended]**
- `2026-09-13` An owner is someone who took part, not someone who published
- `2026-09-13` Dates render in UTC
- `2026-09-13` Upload preferred, pointer available; SAEs are pointer only
- `2026-09-13` The artifact kinds are not a list, and the code does not read them
- `2026-09-14` The synthetic marker is per page, not per corpus  **[amended]**
- `2026-09-14` `model_revision` is nullable, and absence renders as absence
- `2026-09-14` The submission URL carries its version
- `2026-09-14` Non-Hub provenance lives in the recipe payload, and that is a gap  **[superseded]**
- `2026-09-14` The seed corpus is indexed, not submitted
- `2026-09-14` The consumer surface is a package, and it is how this gets used
- `2026-09-14` Scanned code is discovered, not listed
- `2026-09-15` A bare `author/label` refuses when the author has several current versions  **[amended]**
- `2026-09-15` One comparability rule, not two
- `2026-09-15` An artifact path is repo-relative, and leaving the repo is refused
- `2026-09-15` The license audit runs in the gate, and refuses an empty scan
- `2026-09-15` Every manifest on disk has to be in all three inventories
- `2026-09-15` v1 is the site going public, and it is scoped in `V1.md`
- `2026-09-15` The dual-use policy is deferred past launch, knowingly
- `2026-09-15` OPEN: contribution goes through Supabase, not through the site or HF  **[amended]**
- `2026-09-15` Indexing is deferred; the lane without it comes first  **[amended]**
- `2026-09-16` Recipes are namespaced, anyone publishes, and there is no list
- `2026-09-16` Attacks can be attacked
- `2026-09-16` IDEA: `controlbun.agentContext` ships the manual to whatever writes the code
- `2026-09-16` Fetched bytes are checked against a recorded digest, where there is one
- `2026-09-17` The picker's two open fields are a combobox built over the datalist, not instead of it
- `2026-09-17` A writer states what it claims about an artifact and the bytes confirm it
- `2026-09-17` Ingest takes bytes from anywhere, and the converters are not a permission list
- `2026-09-17` No dual-use policy yet, and the trigger is a capability rather than a date  **[amended]**
- `2026-09-18` The author publishes his own artifacts, and the registry records the pin
- `2026-09-18` Intake is a form on 127.0.0.1, and the binding is what keeps it clear of the dual-use trigger
- `2026-09-18` GAP: `layer` is one integer, so a band cannot be stated at all  **[open gap]**
- `2026-09-18` GAP: ingest reads any host, but a row can only pin the Hub  **[superseded]**
- `2026-09-18` The row carries its own URL template, so a pin can name any host
- `2026-09-19` `make site` replays intake, and authored prose is marked as authored
- `2026-09-19` An absence carries its reason, keyed by field name and never by column
- `2026-09-19` No dual-use policy is required, and what review does is a later question
- `2026-09-19` A namespace is claimed by an account, and a claim is never a rank  **[amended]**
- `2026-09-19` The page points at the artifact, and the URL is built once in Python
- `2026-09-19` A submission is identified by author, model, label and version
- `2026-09-19` A direction is the author's own work, built against a model
- `2026-09-19` A signed-in submitter's namespace is their provider handle, and is not theirs to type
- `2026-09-19` A claim is derived from a capture, and the record is what survives the rebuild
- `2026-09-19` The site signposts sign-in, receives nothing, and names no account of its own  **[superseded]**
- `2026-09-19` GAP: `kind` is open and the columns around it are not, so a token sequence cannot be stored  **[open gap]**
- `2026-09-19` The synthetic corpus is removed, and plurality is now demonstrated zero times
- `2026-09-20` Reading is open, writing is signed, and that is the whole auth boundary
- `2026-09-19` There is a contact route, and the address is written out
- `2026-09-20` `artifacts/signin.py` goes when the browser path lands
- `2026-09-20` A submission is a link, and a private repo is not a blocker
- `2026-09-20` GAP: nothing notices when a pin stops resolving  **[open gap]**
- `2026-09-20` The site holds a session, submits to nobody, and uploads only where it is told  **[amended]**
- `2026-09-20` The form posts, Postgres stamps who sent it, and a pull is the only way in
- `2026-09-20` Every document says whether it still instructs, and a test enforces it
- `2026-09-20` The bar offers one of two ways in, off a handle this browser keeps and a session it does not  **[amended]**
- `2026-09-20` A sign-in survives a page navigation and a browser restart, and only one of its two credentials does
- `2026-09-20` The submit page offers the agent handoff, and the parser does not cross

<!-- end index -->

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
**Superseded by:** A submission is identified by author, model, label and
version. Versioning and immutability survive unchanged; what is wrong below is
the reference form, which is now `author/model_id/label@version`.
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
- **Model license position.** No longer blocking. Settled as a working position on
  2026-09-19, "A direction is the author's own work, built against a model", which
  carries the reasoning both ways, the four license instruments it was checked
  against, and the precedent. It stays per-artifact in `license_status` and it does
  not constrain which families the registry carries, because the registry does not
  have a list of those. What remains blocking is the dual-use policy above.

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
**Decided:** `web/templates/` and the HTML-emitting half of `src/controlbun/render.py`
are deleted. The shared view logic is `src/controlbun/views.py`, which shapes a
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

**Amended by:** 2026-09-19 "No dual-use policy is required, and what review does
is a later question", which lifted obligation 3 rather than discharging it. The
gate this entry put in front of publication is gone; obligations 1 and 2 stood
and were discharged when the site went up on 2026-09-20. Nothing else here
changes, and the reasoning about coupling the site to the repo is why the
arrangement still looks the way it does.

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
**Amended by:** The synthetic corpus is removed, and plurality is now
demonstrated zero times. The per-page marker stands as decided. What changed is
the falsifier half: with no synthetic row in the corpus the check below had
nothing to convict, so the rule is a pure function now and a probe proves it
bites on every run.
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
deciding; the package is for using. `src/controlbun/client.py` and `fetch.py` are
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
**Amended by:** A submission is identified by author, model, label and version.
The rule below is unchanged and gains a sibling one level up: `author/label`
now also raises `Ambiguous` when the author holds that label on several
models, before any version question is reached.
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
**Decided:** `controlbun.artifact.local_path` resolves a database `artifact_path`
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
**Amended by:** A namespace is claimed by an account, and a claim is never a
rank. The identity half of this entry, "The design problem nobody had noticed"
below, is built and settled as of 2026-09-19. Everything else here, including
whether contribution goes through Supabase at all, is still open.

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
**Amended by:** The synthetic corpus is removed, and plurality is now
demonstrated zero times. The deferral stands. One of the two consequences below
is understated: "the plurality thesis stays demonstrated only by fixtures" was
true while the fixtures were here, and it is now demonstrated by nothing.
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
**Decided:** `controlbun.artifact` gains `Claim`, `Facts`, `disagreements` and
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
**Decided:** `controlbun.ingest` is the general path: a source, a `Claim`, and one
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

`safetensors` header order is unstable across processes, as `controlbun.artifact`
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
**Amended by:** 2026-09-19 "No dual-use policy is required, and what review
does is a later question". The reasoning below stands and the three triggers no
longer gate anything. In particular "anything can be submitted" is not a gate.

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
here and not in `controlbun.fetch`, which says in its own docstring that it does
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

**Nothing here decides what an artifact may be.** `controlbun.ingest` owns which
bytes can be read without executing them and answers with an open converter set.
`controlbun.artifact` owns the comparison between a claim and the bytes.
`controlbun.fetch` owns the rule that a pin is a commit. The form owns a socket,
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
beside the served pair. `controlbun.fetch` formats the row's own template and
knows no host by name. There is no table mapping hosts to URL layouts and there
will not be one.

**Why:** `ingest.PinnedRepoFile` settled the principle on the write side and the
read side had not caught up: "A table of the ones we happen to have met would be
a list of where an artifact is allowed to come from, which is not ours to
write." A host nobody here has met now works by construction, with no code
change and no request to anybody. This is the same argument `controlbun.ingest`
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

## 2026-09-19 `make site` replays intake, and authored prose is marked as authored
**Decided:** `make site` runs `artifacts/intake.py replay` between the seeders
and the export, so a row that arrived through the form is part of the corpus
without anybody remembering a step. Two checks had to change first and the
second is the interesting one.

**A pinned row has no local file and that is not a missing file.** The
falsifier failed any row whose `artifact_path` was not on disk. That was right
while every row was a vendored file and wrong the moment one was a pin: the
point of a pin is that the bytes are at somebody else's commit. `_pinned` tells
them apart, and the run prints how many rows it did not recheck, because a gate
that quietly covers less than it used to is how a check goes inert. The
falsifier still does not fetch, so `make verify` still never needs the network.

**A definition is prose and prose contains numerals.** The first real
submission quoted its author's own measurements in its definition: `F = 0.9690`,
`p = 0.0005`, a permutation null. The number scan called five of them
unaccounted, and a sixth, `0.5000`, collided with a fixture value and convicted
a real page of publishing figures that were invented. Both readings were wrong
and they were wrong in opposite directions.

**Decided: mark the prose, scan around it.** Every region the site attributes
to a person carries `data-authored`: definitions, theories, an attacker's
response, a support card's purpose. The falsifier reads that attribute and
scans everything outside it exactly as strictly as before.

**What this is not.** It is not an exemption for numbers somebody wants to
publish unchecked. The falsifier's standard was always "re-derives **or** traces
to its source", and a quoted figure traces to the submission that carries it.
What changed is that the page now says so, with a rule down the side, so a
reader can tell a figure this registry derived from a figure its author is
claiming. Before today nothing on the site made that distinction, because no
definition had contained a numeral.

**The guard, because the exclusion is worth exactly what the marking is worth.**
`check_authored_regions_are_marked` fails the build if a definition in the
export renders outside a marked region, and if a page is more marked prose than
page. Proven to bite rather than assumed: removing the attribute from
`ArtifactCard.astro` and rebuilding produces sixteen failures.

**One more word-list trap, the second this project has hit.** `CLAUDE.md`
already records that banning the substring "best" caught the founding sentence.
`test_nothing_is_ranked` scanned for the ordinal "1st" and matched
"~25-token 1st-person retrospective reports" in the author's own methodology.
It now reads the page with authored prose stripped, which is the same
distinction: what the registry asserts, not what it is quoting.

**What this makes impossible to express:** a figure inside authored prose is no
longer held to the export, so an author can write any number into their own
definition. That is already true of the field and always was. What it buys is
that the page stops implying the registry stands behind it.

**Supersedes:** nothing.

## 2026-09-19 An absence carries its reason, keyed by field name and never by column
**Decided:** `schema/migrations/008` adds `intervention_absence`, one row per
field somebody accounted for: `intervention_id`, an open `field`, and the
author's prose. The reason travels from the paste region through `/write`, into
the row, into `artifacts/intake.jsonl`, through `replay`, into the export and
onto the page, where it renders beside the absence inside a `data-authored`
region.

**The hole it closes.** `artifacts/agent_handoff.py` has asked for this since it
existed. Its central rule is that an absence is a positive statement with a
reason and never an omission; the prompt's `not-found:` line takes the field
name and the sentence, `parse` captures both, `received` returns both, and then
nothing persisted them. The first real submission is the case. It recorded
`chat_template_hash` NULL and threw away its author's account of where he
looked: a template was applied at capture, at a named file and line, and no hash
of the template string is computed anywhere in that pipeline, and the manifest's
`tokenizer_hash` is not that value. That is the difference between an absence a
reader can act on and an empty cell, and the project stated the premise without
keeping it.

**An association keyed by field name, and that is the whole design.** A column
per field, `chat_template_hash_reason` beside `chat_template_hash`, is the
closed enumeration wearing a schema hat: the set of fields allowed an
explanation becomes whatever somebody thought of, and the next person with an
absence worth explaining has to ask for a migration. `field` is an open string
with no CHECK and no foreign key onto a column list, which is the argument
`controlbun.ingest` makes about file formats and `PinnedRepoFile` makes about
hosts, applied to the one place it had not been made. A name this repository has
never seen stores and renders; what it cannot do is contradict a value, because
there is no value of that name to contradict.

`tests/test_invariants.py test_no_column_pairs_an_explanation_to_one_named_field`
fails the build on the convenient version, because the convenient version is
what arrives next.

**A value and a reason are mutually exclusive, and the contradiction is refused
rather than resolved.** A row saying both `chat_template_hash = '9f0c...'` and
"there is no chat template hash anywhere in that pipeline" is two claims by one
author about one field. Preferring the value deletes the sentence; preferring
the sentence deletes the value; both happen silently while the entry still reads
correct to whoever wrote it. So neither wins. `intake.insert` refuses the whole
entry and names the fields, which covers the live write and the rebuild because
both call it, so a contradiction typed into the record by hand is stopped at
`make site` rather than written. A CHECK cannot express this: the value is in
another table's row.

**Absence of a reason is not a lesser state and must not render as one.** Most
absences have none and never will. No row means nobody wrote one down, which
renders exactly as it rendered before the table existed: the field says absent
and says nothing else. A blank reason is dropped rather than stored, because an
empty string on a page reads exactly like a reason nobody gave and only one of
them is honest. Nothing anywhere treats a missing reason as a finding.

**The reasons are authored prose and are marked as such.** They name files,
lines and sometimes figures, so they sit inside `data-authored` for the reason
the entry above this one gives. `check_authored_regions_are_marked` now reads
definitions and reasons through one function, so a reason rendered unmarked
fails the build. Proven to bite twice rather than assumed: dropping the
attribute from `AbsenceReason.astro` and rebuilding fails the falsifier naming
the real submission, and `tests/test_falsifier_bites.py` renders a reason both
ways and checks the run goes red only for the unmarked one.
The card prints a reason beside each absence it has a line for, and everything
else lands in a panel of its own, because the schema puts no set on the field
name and a card cannot assume it has seen them all.

**The existing submission was corrected, not invented.** `artifacts/intake.jsonl`
gained the one reason that was lost, quoted from the author's own reply in the
conversation that produced the row, and the corpus was replayed. The two other
absences that reply recorded, `artifact_repo` and `artifact_commit`, are
satisfied now because the intake published the artifact, so nothing was written
for them. No fixture absence got a reason: `fixtures/build.py` has no words for
any of them, and inventing prose is the same failure as inventing a number.

**What this makes impossible to express.** A reason for an absence on anything
but an intervention. A support card with no `observed`, an eval report with no
transfer score and a submission with no recipe are all absences somebody might
want to account for, and this table holds none of them: it is keyed on
`intervention_id` and carries a foreign key to it. Widening it means dropping
that key or naming the kind of subject, and naming the kind is an enumeration of
which objects are allowed to explain themselves. Left for whoever has the second
case, with the shape written down rather than discovered later.

Also impossible: two reasons for one field on one intervention, since the
primary key is the pair. One author, one field, one account of it. A second
opinion about somebody else's absence is a different object and the registry
already has `attack` for that.

**Nothing became required.** Every column stays as nullable as it was, no field
gained a bar to clear, and a submission that accounts for nothing is the normal
one. What changed is that an author who did the work of looking now has
somewhere to put the answer.

**Supersedes:** nothing. Pays off the `not-found:` line in
`artifacts/agent_handoff.py`, which has been parsed and discarded since
2026-09-18.

## 2026-09-19 No dual-use policy is required, and what review does is a later question
**Decided:** No dual-use policy is needed. It does not gate the site, it does
not gate submission, and nothing waits on it.

**Why, in the author's terms.** The question that produced the 2026-09-17 entry
was what a dual-use policy even is for a thing like this, and the answer that
came out of drafting one was that most of it was not policy. It was a
description of what the system does, which is why `POLICY.md` became
`WHAT-IT-DOES.md`. A policy governs decisions, and the decisions it would govern
do not exist. That conclusion is unchanged; what changes here is that the
capability triggers attached to it are lifted rather than left standing as a
gate on work nobody is blocked on.

**What is deliberately not decided here.** What a review step does when
submissions open. The 2026-09-17 entry's real claim was never that a document is
required; it was that a review step with no stated rule fills up with whatever
the reviewer thinks that day. That concern is unaffected by this entry and it is
a problem of the future, to be answered when there is a submission route and not
before. Recorded so that answering it later is not mistaken for reopening this.

**What this makes impossible to express.** Nothing in the schema or the client.
What it removes is a prepared answer to the first question a safety-adjacent
reader asks, which the 2026-09-15 entry already named as the cost of deferring
and which is unchanged in kind by making the deferral permanent. Publishing
`BRIEF.md` and `VALIDATION.md` still means publishing this project's own
analysis of misuse surface with nothing answering it. That was true before this
entry and is true after it.

**Supersedes:** 2026-09-17 "No dual-use policy yet, and the trigger is a
capability rather than a date", whose reasoning stands and whose triggers do
not.

## 2026-09-19 A namespace is claimed by an account, and a claim is never a rank
**Decided:** `schema/migrations/009` adds three tables. `namespace_claim` binds
an account to an `author` string, `namespace_claim_evidence` records what was
offered for it, and `namespace_membership_observation` records what a provider
said about that account's org memberships and when it said it. `author` stays a
free string and nothing anywhere requires a claim.

**`author` does not become an account, and `V2.md` section 1 gives the three
cases.** Indexing the literature is deferred rather than reversed, so an entry
for somebody else's published direction has an author who never signed up.
Every row in this corpus today was hand-entered or is a fixture, so the rule
would already be false. And attack cards, independent evaluations and support
cards all name an author who is not the submitter, which means the subject of a
piece of evidence may have no account while its writer does. So claiming is a
separate object and publishing is not conditional on it.
`test_publishing_never_requires_a_claim` fails the build on the foreign key
that would make it conditional, which is the strongest form of the erosion and
the one a schema makes easiest.

**Bound to `sub`, never to `preferred_username`.** Handles are renameable on
both providers this is written for, so a claim keyed on one breaks on a rename
or, worse, follows the name to whoever registers it next, which is squatting
with the registry's help. `handle` is kept on the row as what the provider said
at `claimed_at`, rendered as "which called itself X that day", and nothing
keys, joins or looks up by it.

**Org membership is an observation with a date and never a stored fact.**
`orgs` is an HF-specific claim and does not survive into Supabase, which `V2.md`
records as better than it looks: storing membership at signup was always wrong
because people join and leave organisations. So the row is what userinfo
answered and when, `observed_at` is part of what makes it unique so looking
again appends rather than overwrites, and the page says "Membership of X
confirmed on 12 Sep 2026" rather than saying anything in the present tense. This
is the rule the history audit and the attestations already follow: the result is
dated, not permanent.

**A namespace takes more than one claimant.** Uniqueness is on the account and
the namespace together. Two accounts claiming `allenai` are two rows and both
stand with their own evidence, because making `namespace` unique would make the
index settle a contested name. This is the label rule one object over.

**No closed enum on `provider` or on the evidence kind.** `huggingface` and
`github`, and `repo`, `doi` and `human-decision`, are documented in the
migration and enforced nowhere. A list of evidence kinds says which ways of
establishing a claim are legitimate, and a list of providers says which
identity services a person is allowed to be a person at.

**The rendering decision, which is the one that matters.** A claim renders on
the namespace's own page and nowhere else. Not a column in `/owners/`, not a
mark on a submission row, not a line on the label view where claimants of one
word sit side by side. The moment claimed and unclaimed appear next to each
other in a list a reader takes one for better, and the next reasonable request
is to sort by it. Unclaimed is written out in words, the way 005, 007 and 008
absences are, because every namespace in this corpus is unclaimed including
`soham`, who authored all five real rows.

**Nothing derives an order from it, and that is executable.**
`test_no_ordering_is_derived_from_a_namespace_claim` scans for the sort, the
comparator, the column header and the filter, and
`tests/test_invariants_bite.py` proves each one red. `claimed_at` is kept out of
the owner index's `latest` deliberately: it is a date and it would have fit, and
leaving it in would have put a claimed namespace above an unclaimed one that
published the same day with nothing on screen saying why. Every ordering key in
`export.py` is something somebody did to the work. A claim is not.

**Third word-sense trap, recorded because this project now has three.** `claim`
is three different words here: a claimant of a label, a label an owner has
claimed, and the namespace sense this entry adds. The first scanner matched the
substring and convicted the existing `Claimants` sort control and the `Labels
claimed` column, neither of which has anything to do with accounts. It now
matches what a header leads with. `CLAUDE.md` already records "best" catching
the founding sentence and an ordinal scan catching "1st-person retrospective
reports"; this is the same failure and the same fix.

**The evidence detail is authored prose and is marked as such.** A human
decision is recorded with its reasoning, which can carry names, dates and
figures, so it renders through `Prose.astro` inside `data-authored` and the
falsifier's `_authored_texts` reads it off the owner index. Proven to bite
rather than assumed: `tests/test_falsifier_bites.py` renders one both ways and
the run goes red only for the unmarked one.

**One fixture claim, seven unclaimed namespaces, and no real one.** `alice` is
claimed by an account whose provider does not exist, whose subject no provider
issued and whose org sits on a reserved `.invalid` hostname, all recorded in
`fixtures/SYNTHETIC.md`. Nothing real is claimed, including `soham`: the sign-in
that would produce a real claim has not happened, and writing the row by hand
because the id is known would be inventing the event the row attests. The only
real identity in this project stays where `V2.md` put it.

**What this makes impossible to express.** Asking which namespaces are claimed.
There is no list, no filter, no count on any page and no boolean in the export
or the client, so a reader cannot see at a glance which of ten claimants of one
word has an account behind it and cannot put those first. That is the cost and
it is paid on purpose: the question has one useful answer and a dozen harmful
ones, and every harmful one reads a claim as a mark of quality that nothing
about a claim supports.

Also impossible: a claim that expires, since there is no revocation and no
`valid_until`; evidence about somebody else's claim, since evidence hangs off
the claim it supports and the object for disagreeing with a record is a separate
authored one this schema does not yet have; and a namespace held by a group
rather than by an account, since the membership that makes a person part of an
org is a separate dated observation and the two cannot be collapsed.

**Not built here.** The sign-in flow, the userinfo call and anything that talks
to Supabase. This is the data model and the rendering; the live flow is separate
work and `V2.md` stays not settled.

**Supersedes:** nothing. Implements `V2.md` section 1 and settles the identity
half of the open 2026-09-15 entry "OPEN: contribution goes through Supabase, not
through the site or HF", which stays open on everything else.

**Amended by:** 2026-09-19 "A claim is derived from a capture, and the record is
what survives the rebuild". The rendering rule, the binding, the open strings and
the ordering ban all stand. What is wrong in this entry is "One fixture claim,
seven unclaimed namespaces, and no real one": the sign-in happened the same day,
`soham` is claimed, and the row was typed rather than derived, which is what the
amendment fixes.


## 2026-09-19 The page points at the artifact, and the URL is built once in Python
**Decided:** The export carries `artifact_repo`, `artifact_commit`,
`artifact_host`, `artifact_url_template` and `artifact_sha256`, and the artifact
page renders the host, the repo, the commit, the digest, a link that resolves to
the bytes, and the one-line client call. The URL is built by
`controlbun.fetch.row_url` and by nothing else. No component assembles one from
parts.

**Why.** The registry's premise is that it points at artifacts rather than
serving them, and its pages pointed at nothing. `artifact_path` travelled into
`astro/src/data/controlbun.json` and the other five columns did not, so migration
007, the any-host templates, `artifacts/publish.py` and the pin on the one real
submission were invisible to anybody reading the website.
`controlbun.load("soham/trauma@d61-diffmeans-expository-L34").vector()` resolved
that pin from a cold cache and a person with a browser had nothing. Nothing
failed, because the pin work went end to end through the Python client and the
client never touches the export, so the website was never in the loop.

**One rule, one place.** `row_url` is extracted from `from_repo` rather than
written beside the page, so the URL a reader is shown is the URL the client
fetches, including the fallback a row with no host of its own takes. It already
refuses a template that drops the commit, a scheme that is not a network fetch
and a placeholder carrying a format spec. A template assembling a URL from parts
would be a second copy of all of that in the half nobody runs
`tests/test_fetch.py` against, which is the failure mode this repo has already
had several times.

**It serves no bytes.** The link goes to where the author published, on their
host, at their commit. `schema/migrations/004` is unchanged and `served_repo`
stays NULL. What a reader gets by following the link is the file; what they get
by running the client call is the file with its sha256 checked against the
record first, which is why both are on the page and why the second is described
as doing the check rather than as documentation.

**Absence renders as absence.** Nine of the ten rows here record no repo: five
synthetic fixtures and four real directions whose author never published them at
a URL. Those pages say nobody recorded where the bytes are, print the digest
anyway because that is a fact about the bytes rather than about where they are,
and link nowhere. No URL is invented for a row that has none, and
`tests/test_pinned_page.py` asks that of the whole build at once rather than of
the sentence on one page: every off-site link on the site has to be a URL the
export carries.

**What this makes impossible to express.** Nothing that was expressible before.
The new invariant beside it does remove one thing: a view ordered so that a
reader can see at a glance which submissions they can actually get. That is a
real want and it is a filter rather than an order, so `published` is on every
claimant in the export for a reader to select on. Ordering on it would make
having a URL into a quality, and a quality is one step from a default that reads
as the registry's own judgment.

**Supersedes:** nothing. It closes the gap the 2026-09-18 entry "The row carries
its own URL template, so a pin can name any host" left on the read path, which
that entry settled for the client and not for the site.


## 2026-09-19 A submission is identified by author, model, label and version
**Decided:** a submission's primary key becomes `(author, model_id, label,
version)` and its reference form becomes
`soham/allenai/Olmo-3-1125-32B/pro-human@meandiff`. `model_id` is the full
distributor-and-name string the extraction loaded and moves onto `submission`,
into its primary key, and onto the four tables that reference it:
`intervention`, `recipe`, `pin` and `support_card`. `schema/migrations/010`.

**Why.** One author holds one label on several models, and those are different
artifacts rather than one artifact with an attribute. `soham/pro-human` on
Olmo 3 and `soham/trauma` on Llama 3.3 already coexist only because the labels
differ; the same author's second take on a word he already holds collided with
the first under the old key. `BRIEF.md` has said since the first draft that a
vector is a tensor in one model's residual basis, so a submission that does not
name the model in its identity was not identified. The old key made "one author,
one label, one version" a fact about the world and it never was.

**Parsing, which looks impossible and is not.** Split on `@` for the version,
then split the rest on `/`: first segment is the author, last is the label,
everything between is the model. Any model id depth works because the model is
the middle rather than a fixed segment count, so `gpt2` and `bert-base-uncased`
with no distributor parse as well as `meta-llama/Llama-3.3-70B-Instruct`.
Nothing requires a slash in a model id and nothing validates its shape; it is an
open string like every other user-supplied field here. The rule lives in
`src/controlbun/ref.py` and in one place, and `views.claimant_view` puts the
formatted `ref` in the export so no template composes a second copy of it.

**The short form still resolves, and refuses rather than picks.**
`author/label@version` resolves while that author holds that label on exactly
one model. On more than one it raises `Ambiguous` naming each alternative in
full, which is the same shape as the 2026-09-15 rule one level up: that one
refuses to choose a version, this one refuses to choose a model. A short form
that silently picked would be the registry choosing, and convenience here is
designation wearing a different hat.

**This is identity and nothing else.** Not a filter, not an ordering, not a
facet that ranks. Nothing on any page reads as one model's directions being the
real ones. The same label on two models is two submissions that both stand,
exactly like two authors on one label. `claimants()` and `compare()` still take
a bare label and still return claimants across every model, because a bare label
is a view owned by nobody and narrowing it to one model would make the view a
statement about which model the word belongs to.

**What this makes impossible to express.** One submission whose artifact spans
several models. That shape was already unwritable: `intervention.model_id` is
singular and NOT NULL, so a submission claiming two models was two intervention
rows sharing one key with nothing to say which recipe, pin or support card was
about which. What is lost is a hypothetical. A recipe that fans out across models
is still expressible, as one recipe published as several submissions, which is
what fanning out is.

**Existing rows carry their model rather than being given one.** Every
submission in the corpus has exactly one intervention carrying exactly one
`model_id`, checked before the migration was written to rely on it. The
migration reads the value across and a `CHECK` constraint fails the build if the
rebuilt table does not hold exactly as many rows as the old one, which is what a
submission with no artifact, or with two on different models, would produce. A
migration that quietly dropped somebody's submission for having no artifact
attached is the failure this makes loud.

**`pin.alternatives_json` is carried across verbatim.** It is what a consumer
wrote about their own choice, and expanding each string into a four-part
reference would be inferring which model they meant and recording the inference
in their words. The seeders write the full form.

**RAISED, NOT DECIDED: whether a relation is model-scoped.** `label_relation` is
keyed `(from_author, from_label, relation, to_author, to_label)` with no version
and no model, and 010 leaves it alone. `interprets:` and `distinguishes-from:`
are pointers between labels, and a bare label is a view across claimants owned by
nobody, so a relation is not obviously a statement about one model's artifact.
The case for scoping it: "erik's refusal is topic sensitivity" is a reading of a
particular vector and may not hold for erik's take on another model. The case
against: a relation is how taxonomy emerges from claims, and a taxonomy that
forks per model is a taxonomy nobody can read. Adding the column in this
migration would have answered it by accident. Open.

**Supersedes:** Submissions are versioned and immutable.


## 2026-09-19 A direction is the author's own work, built against a model
**Decided:** the project's working position is the author's, in his words:
"artifacts are not derived from models rather built by user against a model." A
direction is the work of whoever built it. He wrote the contrast prompts, chose
the layer and the estimator, and did arithmetic on activations he elicited. The
result carries no weights, cannot reconstruct any, and is better described as a
measurement of a model than a piece of one. On that reading the author holds
whatever rights exist in it and the source model's license does not reach it.

**This is a position and not legal advice.** Nobody has litigated it. Searched
three ways on 2026-09-19, no paper, post or commentary addressing specifically
whether a steering vector is a derivative work of its model was found, which is
an absence rather than a negative answer. Whether model weights attract copyright
at all is contested: the Copyright Office's Part 3 report is read as recording the
question as disputed while noting a "strong argument" that weights implicate the
reproduction and derivative work rights where outputs are substantially similar to
inputs (skadden.com/insights/publications/2025/05/copyright-office-report, dated
2025-05-15, fetched 2026-09-19), and a practitioner piece arguing the restrictive
side concedes in the same document that "[w]hether fine-tuning constitutes
sufficient human authorship to generate copyright in the resulting weights is an
open question" (wcr.legal/fine-tuned-model-license, dated 2026-03-07, fetched
2026-09-19). A position taken where the underlying right may not exist is a
position about a hypothetical, and it is recorded as one.

**The case against, which is why this entry exists rather than a sentence.** Four
things cut at it, and a reader who cannot see them has been handed an assertion.

1. **One widely used license names activations in terms.** CreativeML Open
   RAIL++-M, which governs SDXL, defines "Derivatives of the Model" to include
   "any other model which is created or initialized by transfer of patterns of the
   weights, parameters, **activations** or output of the Model, to the other
   model, in order to cause the other model to perform similarly to the Model"
   (huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/raw/main/LICENSE.md,
   fetched 2026-09-19). The trailing qualifier is the answer available here, since
   a direction does not cause another model to perform similarly to the source.
   That is an argument, not a reading anyone has construed.
2. **A lab with counsel published the opposite view on the same class of object.**
   `Goodfire/Llama-3.3-70B-Instruct-SAE-l50` declares `license: llama3.3` and its
   card says "By using Goodfire/Llama-3.3-70B-Instruct-SAE-l50 you agree to the
   LLAMA 3.3 COMMUNITY LICENSE AGREEMENT" (fetched 2026-09-19). An SAE is trained
   on activations, exactly as a direction is estimated from them.
3. **The symmetry problem, which has no clean answer.** If a direction is its
   author's own work because it is a handful of floats computed from activations,
   the same reasoning runs for a LoRA, and practitioner commentary treats LoRA
   adapters as bound by the base license because an adapter "only exists in
   relationship to the base model" (wcr.legal, as above). "It is smaller" is not a
   principled line. The line this project would draw is that a direction is not a
   model and cannot be run, but that line is drawn here and not anywhere else.
4. **The permissive practice this could lean on is uncounselled.** Several Hub
   repos declare MIT or Apache-2.0 over artifacts derived from restrictively
   licensed models with no stated reasoning. Citing them as precedent is citing
   habit, and it reads as habit on inspection.

**What the license texts actually say. Every one fetched 2026-09-19.**

- **Apache-2.0**, which governs `allenai/Olmo-3-1125-32B` (`license: apache-2.0`
  from the Hub model API, confirmed 2026-09-14 and again 2026-09-19) and
  `Qwen/Qwen3-8B` (same API, `license: apache-2.0`). Moot either way. A Derivative
  Work has to be one "for which the editorial revisions, annotations,
  elaborations, or other modifications represent, as a whole, an original work of
  authorship", and the definition "shall not include works that remain separable
  from ... the Work". Four of the five real directions sit here, and both readings
  end in the same place.
- **Llama 3.3 Community License**, release date December 6, 2024, read at
  developer.meta.com/ai/llama3_3/license (www.llama.com redirects there). It
  defines "Llama Materials" as "Meta's proprietary Llama 3.3 and Documentation
  (and any portion thereof) made available under this Agreement" and never defines
  derivative work as a standalone term. Two clauses matter and they point in
  opposite directions. Section 5.b: "with respect to any derivative works and
  modifications of the Llama Materials that are made by you, as between you and
  Meta, you are and will be the owner of such derivative works and
  modifications." So even on the reading this entry rejects, ownership lands with
  the author. Section 1.b.i reaches further than ownership: "If you use the Llama
  Materials or any outputs or results of the Llama Materials to create, train,
  fine tune, or otherwise improve an AI model, which is distributed or made
  available, you shall also include 'Llama' at the beginning of any such AI model
  name." **This entry does not resolve that clause and does not try.** The
  `license_status` on `soham/trauma@d61-diffmeans-expository-L34` records it as
  unresolved, read at the same URL on 2026-09-18, and it stays unresolved. The
  trigger is creating an AI model and a direction is not one, which is the
  author's reading and is the reading his row already declines to treat as
  settled.
- **Gemma Terms of Use**, last modified April 1, 2026, ai.google.dev/gemma/terms.
  Cuts both ways in one definition. "Model Derivatives" means "all (i)
  modifications to Gemma, (ii) works based on Gemma, or (iii) any other machine
  learning model which is created by transfer of patterns of the weights,
  parameters, operations, or Output of Gemma". Limb (iii) is confined to a machine
  learning model and its list is "weights, parameters, operations, or Output",
  which does not name activations. Limb (ii), "works based on Gemma", is
  unqualified and is the broadest language in any of these four. Against that,
  Google shipped its own activation-derived artifacts outside these terms
  entirely: Gemma Scope carries `license: cc-by-4.0` and is ungated
  (huggingface.co/google/gemma-scope), while `google/gemma-2-2b` carries
  `license: gemma` and `gated: manual`. That is how the model's own vendor chose
  to treat an artifact read out of its model's activations. It is a choice a
  copyright holder is free to make about its own work rather than a statement
  about what binds a third party, and it is recorded as evidence of practice.
- **Qwen LICENSE AGREEMENT**, the terms on `Qwen/Qwen2.5-72B-Instruct`, which
  differ from the Llama ones in the way that matters here: there is no naming
  clause. Outputs get attribution rather than a name. "If you use the Materials or
  any outputs or results therefrom to create, train, fine-tune, or improve an AI
  model that is distributed or made available, you shall prominently display
  'Built with Qwen' or 'Improved using Qwen' in the related product
  documentation." The commercial threshold is 100 million monthly active users
  against Llama 3.3's 700 million. Recorded because a position written against one
  license is a position about that license.

**Precedent, and the finding is mostly absence.** Concept Sliders (arXiv:2311.12092,
Bau lab) distributes 23 pretrained SDXL sliders at
`sliders.baulab.info/weights/xl_sliders/`, and **that directory states no license
at all**, nor does the project page above it. The code is MIT. The repo README
scopes the grant and pushes the question back: "The code and methods behind our
work have been released under MIT. However, the models that you use our methods
with, might be on a different licenses. Please read the model's license (the model
you are using) carefully for more details." So the most cited project publishing
this kind of artifact neither asserts the position this entry takes nor its
opposite. It disclaims. The same shape holds across the Hub: several published
control-vector and steering-vector repos state no license, and the ones that do
state a code license by reflex. `vgel/repeng` is MIT on the code and silent on what
a trained vector is. On SAEs, which are the closest large-scale analogue, practice
splits three ways on the same base model family: Google CC-BY-4.0, EleutherAI MIT
on Llama-trained SAEs, Goodfire the Llama agreement itself. **There is no settled
practice to defer to, which is the actual state of the field and is why this is a
position rather than a finding.**

**What this forecloses.** Three things, and the third is the one that costs.

First, neutrality. Until today the project had no house view and a contributor's
`license_status` was the only assertion on the page. Now there is a stated position
behind it, and a contributor who takes Goodfire's view writes their dissent into a
field whose surrounding prose disagrees with them. `license_status` stays an open
string that its author asserts and nothing validates it, so the disagreement is
still expressible. What is gone is its being expressible without a house view in
the room. That is the plurality cost and it is not zero.

Second, the answer "we never took a view", if an indexed artifact is ever
challenged. It has been traded for a dated record of what was read and when, which
is the trade this project makes everywhere else.

Third, and this is the expensive one: **the derivative reading was a free hook for
the dual-use policy and this position removes it.** If artifacts inherited their
model's terms, they would inherit the Llama Acceptable Use Policy and the Gemma
Prohibited Use Policy with them, and misuse gating would have arrived as somebody
else's contract rather than as this project's rule. Taking the author's position
cuts that off. The dual-use policy now has to stand on its own reasoning, which is
where it should have stood anyway, and it is still the launch blocker. Recorded
here rather than resolved, per the standing instruction not to settle the
open-contribution-against-misuse-gating tension quietly.

**What it changes operationally, which is close to nothing, and that is the
point.** Stated rather than left implied:

- **The serving gate is unchanged.** 2026-09-13 stands: the registry serves a copy
  only on an explicit affirmative in `license_status`, and silence or unresolved
  means pointer only. This entry is a view about what the law is. That gate is a
  policy about what we do when nobody has said, and it does not depend on the view.
- **No schema change, and no field becomes closed.** `license_status` stays an open
  string the author asserts. There is no enum, no validated vocabulary, and nothing
  refuses a row for what it says there.
- **No list of model families, and there never was one.** The registry indexes what
  people submit. Where bytes cannot be redistributed it points and does not serve,
  which is the structure that already existed and is why this question is less
  urgent here than it would be for a host.
- **Nothing in the corpus moves.** The four OLMo directions resolve the same way
  under either reading. The Llama-derived one keeps its pointer, keeps its dated
  reading, and keeps its unresolved clause.
- **Docs that stated the old premise as fact were amended, not deleted.**
  `CLAUDE.md`, `BRIEF.md`, `artifacts/REAL.md`, the intake form's help text for
  `license_status`, the agent handoff, and the license caption on the artifact card.
  Each now says what it used to say and why that changed, because the premise was
  stated in six places and would otherwise have kept arguing the other way.
- **One string was deliberately not touched.** `artifacts/source.py` writes the
  `license_status` carried by the four OLMo interventions and it still states the
  old premise. That is published corpus content under the author's name, and this
  project's own rule is that correcting such a field means a new version rather
  than an edit in place. Left for the author.

**Supersedes:** nothing. It closes the "Model license position" item under "Open,
blocking launch (not code)" above, which now points here, and it amends prose in
CLAUDE.md, BRIEF.md and artifacts/REAL.md rather than an entry.

## 2026-09-19 A signed-in submitter's namespace is their provider handle, and is not theirs to type
**Decided:** when somebody submits through a signed-in path, the namespace is
the handle their provider reported at sign-in. It is shown, not offered: no
field, no default to override.

**What this is not.** It is not "author becomes a verified account", which
`V2.md` section 1 considers and rejects on three grounds, all of which still
hold and none of which this touches. An indexed entry for somebody else's
published direction has an author who never signed up, and that lane is
deferred rather than reversed. Every row in the corpus today has an author with
no account. An attack card, an independent evaluation and a support card each
name a subject who is not the submitter. This rule binds one write path. It
binds no schema column, forecloses no lane, and renames nothing.

**Why.** `author` is free text and squatting has nothing standing in front of
it. `V2.md` answers that with "the namespace is not the claim, the claim is the
claim", and that stays true: a namespace still takes any number of claimants and
a claim is still evidence somebody can argue with. What this adds is that the
one path where identity is already known stops asking a question it can answer.
Somebody signed in as `qwen-fan` cannot submit under `Qwen`.

**A pre-filled default was considered and is not enough, which is the argument
that decided this.** Pre-filling the handle and letting it be edited stops
nobody: a person who has decided to take `meta` clears the field and types
`meta`. The only version that does anything is the one with no field, so the
question is whether to take the cost of that or leave squatting unaddressed on
this path.

**And it inherits a dispute process rather than inventing one.** A namespace
that is a handle cannot be taken unless the handle is taken, and handles live on
a platform that already has contested names, rules for them, and somebody to
appeal to. This registry does not want to be the venue for an argument about who
is really `allenai`, and this is how it avoids becoming one without asserting
anything itself. What it does not do is stop `meta` appearing in the corpus at
all: an indexed entry can carry any author string, because the author of a
paper's direction never signed up and the entry is about them rather than by
them. That is the same distinction as everywhere else here, between a name
somebody claimed and a name somebody was given.

**Two consequences, recorded because neither is obvious.**

The first real claim in this corpus is the first exception. Namespace `soham`,
handle `sohampadia`. It predates this rule, was recorded from a real capture,
and is pinned and published under that name, so it stands. The rule is for
submissions that arrive signed in, and the corpus will hold both shapes.

Handles are renameable, which is why a claim binds `sub` and not a handle.
Under this rule a rename means the namespace string stays where it is while the
handle moves, and somebody else may later sign in holding it. That produces two
subjects claiming one namespace, which the schema already permits on purpose
and which renders as two claims with their dates and evidence rather than as a
conflict anybody has to resolve. It degrades into the plural case visibly. That
is the intended behavior and not a hole to close later.

**It also removes the form, and the evidence with it.** If the namespace is the
handle, there is nothing for a submitter to fill in and nothing to argue about:
the provider attests the handle, and the capture is the attestation. Evidence on
a claim exists for the case this rule forecloses, somebody signed in as
`qwen-fan` claiming `Qwen`, which needs a repo, a DOI or a human decision with
its reason. That case cannot arise on this path, so a claim made this way
carries no evidence and needs no page to collect any. What a remote write path
has to build for claiming is therefore a session and somewhere to put it, and
not a form.

The one real claim in this corpus carries evidence prose precisely because it is
the exception: namespace `soham`, handle `sohampadia`.

**What this makes impossible to express.** A signed-in author publishing under a
name other than their handle: a pseudonym, a lab name they hold no account for,
or a namespace shared by several people who each sign in as themselves. The
last is the one worth watching, because a research group is exactly the shape
that wants it, and the answer today is that they claim a namespace rather than
submit into one.

**Supersedes:** nothing. Refines `V2.md` section 1, which stays correct: this
constrains a write path and leaves `author` a free string everywhere else.


## 2026-09-19 A claim is derived from a capture, and the record is what survives the rebuild
**Decided:** `artifacts/claim.py` turns a sign-in capture into the three rows
`schema/migrations/009` defines, through `artifacts/claims.jsonl`, which is
tracked and append-only. `artifacts/seed.py` no longer writes a claim: it calls
`claim.replay(conn)`, the same function the recording commands call, so the
rebuild and the recording step cannot come apart. The export is byte identical
across the change, which is how the move was checked.

**The defect was transcription.** The one real claim in this corpus was made by
a person reading a capture on screen and typing a subject id, a handle, a role
and three timestamps into a Python file. Every other real value here is derived
from a file by a script, and the reason is stated in `seed.py`'s own docstring
about tensor facts: a fact that was typed in is a fact that can be typed in
wrong, and the row is what every later check reads. A subject id is worse than a
shape, because nothing can disagree with it afterwards.

**The capture stays gitignored and the record does not, and that line is the
design.** A capture is whatever the provider chose to return about a real
person. The record carries the fields the row carries and not one more:
namespace, provider, subject, handle, the dates, the organization and the role.
`test_the_record_carries_the_fields_the_row_carries_and_no_others` fails on a
projection that copies the capture dict, which is the one line of code that
would collapse the two.

**Two shapes in one file, because a claim and a look are two statements.**
`namespace-claim@1` carries the binding and its evidence. `membership-
observation@1` carries one organization at one moment, attached to the account
rather than to the claim, which is what the migration already says. So a second
sign-in appends observations with no second claim, and `observe` is a separate
command for exactly that.

**No id is typed either.** Each row's primary key is derived from exactly the
columns its `UNIQUE` constraint is made of, so a duplicate is refused by both
rather than by one, and a rename produces the same claim id while a second
account produces a different one. That is the sub-not-handle rule expressed
twice in the same string. The two hand-written ids are gone and nothing
referenced them: a claim id reaches no view, no export and no page.

**A capture carrying anything credential-shaped stops the run.** Walked
recursively over key names, before anything is appended or inserted.
`artifacts/signin.py` writes no token by construction, so this guards against a
capture that came from somewhere else, and the cost of being wrong in that
direction is a secret in a public repository.

**`adopt` exists and is not how a claim is made.** The rows predate the record
and the capture behind them is gitignored and no longer in the tree, so the
record for the existing claim was derived from the database rather than from a
capture. Entries carry `derived_from`, so the record says which of the two it
was. Signing in again was the alternative and it would have dated the claim to
today rather than to when it was made.

**Nothing about this is a condition on anything.** No ordering, no filter, no
gate on publishing, no `is_member` column and no `UPDATE` anywhere in the
module. The existing invariant scanners already reach `artifacts/`, so they
cover this file the day it appeared;
`test_recording_a_claim_touches_nothing_outside_the_three_claim_tables` adds the
write side, which the scanners cannot see.

**What this makes impossible to express.** A claim for an account nobody can
sign in as. There is no `--subject` flag and no way to hand-write a capture this
will read, so an identity that is real and unprovable through a configured
provider cannot come through this path. `artifacts/SIGNIN.md` records the same
gap one object earlier and it is deliberate for the machine-read half; the
authored half stays open, which is where an entry for somebody else's published
direction goes.

Also impossible: a claim dated at a moment other than its capture. `claimed_at`
is the capture's own timestamp and there is no flag that changes it, so a claim
dated later than the evidence that produced it cannot be written down.

**Supersedes:** 2026-09-19 A namespace is claimed by an account, and a claim is
never a rank, in one paragraph and no further. Its rendering rule, its binding,
its open strings and its ordering ban all stand. The paragraph beginning "One
fixture claim, seven unclaimed namespaces, and no real one" was true for about
an hour, and that is what the amendment corrects.

## 2026-09-19 The site signposts sign-in, receives nothing, and names no account of its own
**Superseded by:** 2026-09-20 The site holds a session, submits to nobody, and
uploads only where it is told. The return leg exists, `/signed-in/` holds a
session, and `/sign-in/` is the explainer beside it rather than the whole of it.
What survives is that this registry still creates no account, that `/sign-in/`
still ships no script, and that the site still has no origin that receives. The
`https://huggingface.co/login` anchor this entry put in `AUTHORED_OFFSITE` is
gone, because it sent somebody to a login that returned them to Hugging Face.

**Decided:** `/sign-in/` ships on the published site. It carries two outbound
anchors to Hugging Face's own registration and login pages, an internal link to
`/about/`, and nothing else: no field, no form, no script of its own, no
identity endpoint. It reads as three steps, hold an account, sign in, claim a
namespace, because claiming is the act with meaning here and signing in on its
own gives somebody nothing.

**What it is not.** Not a sign-up. This registry creates no account, and a page
implying one would advertise the model `V2.md` section 1 declines, which is the
same model the home page's Account section was removed for. The page says in its
first paragraph that none of it works yet, and says at the login link that the
trip back does not exist.

**The return leg is not built and that is the point of the entry.** After
Hugging Face and Supabase redirect back, the session lands where only
client-side script can read it. Shipping that script reverses a decision
recorded twice, so it is not a side effect of building a page.
`artifacts/SIGNIN.md` carries the costing: the three shapes it could take, which
guard lines each crosses, the smallest honest version, and what each spends in
the three terms `astro.config.mjs` gives for static output. Nothing is decided
there.

**Two things the guards turned out to say, which are worth having written
down.** An anchor to an authorization endpoint passes `WRITE_SURFACE`, exactly
as `SIGNIN.md` predicted, and fails the Supabase-endpoint test, which is the one
that exists for it. And `WRITE_SURFACE` catches `XMLHttpRequest` and
`sendBeacon` but not `fetch`, so a scripted POST with a computed method passes
it. That gap is named rather than closed: adding `fetch` would flag any page
that reads JSON, and the structural criterion `SIGNIN.md` proposes is the better
answer. Neither guard was weakened.

**One guard was widened, with its own bite test.**
`test_every_offsite_link_is_a_url_the_export_carries` asks whether the build
invented a URL, and its answer was "the export put it there". It now has a
second answer, `AUTHORED_OFFSITE`, a dict of URL to the one page allowed to
carry it. A marking in the markup was considered and rejected: anything wearing
the attribute would pass, so the next hand-written link would arrive without
anybody deciding it should. A dict entry is a test edit, which is a decision,
and the same URL on a page that did not author it still fails. Both HF URLs were
fetched before they went in; `/login` renders and links to `/join` as "Sign Up",
which is how the registration URL was confirmed rather than assumed.

**What this makes impossible to express.** A working sign-in, which is the
point. Also, at the level of the guard: an off-site link generated by a template
from anything other than a published row. Every such link now has to be either
in the export or in a dict somebody edited, and there is no third way for one to
appear.

**Not decided here.** Where the page belongs in the navigation. It is linked
from `/about/` and from the unclaimed-namespace note, and deliberately not from
the top bar, because a nav item reading "Sign in" is an offer this build cannot
honor and that is the greyed-out Account section under a different word. That
call is the author's once the path works.

**One bug in the supersession check, found by this entry's title.**
`tests/test_decisions.py` matched a `Supersedes:` claim against entry titles by
substring, and sixteen entries claim to supersede "nothing". The first title
containing that word made all sixteen claim to supersede it. The line says the
entry supersedes nothing, so the parser now takes it at its word, and a bite
test holds the fix. A bare title with no date in front of it is still resolved,
because five real supersessions are written that way.

**Supersedes:** nothing. `SIGNIN.md`'s recommendation that the tool stay out of
the built site is untouched: the loopback tool is still not referenced by the
view layer, and both tests that check it still pass.

## 2026-09-19 GAP: `kind` is open and the columns around it are not, so a token sequence cannot be stored
**Found, not decided.** A discovered token sequence is an intervention on the
same construct a direction is, and this schema cannot hold one. `kind` is an
open string and `001_init.sql` says beside it that "an unrecognized kind is
storable and displayable". It is not. Five columns are `NOT NULL` and every one
assumes a residual-stream tensor:

    layer INTEGER, layer_convention TEXT, hook_point TEXT, shape TEXT, dtype TEXT

Demonstrated rather than reasoned: inserting a row with `kind='token-sequence'`
and no layer fails on `NOT NULL constraint failed: intervention.layer`.

**How it surfaced.** The author reports, from his own steering arena on
`allenai/Olmo-3-1125-32B`, that two different token sequences prepended to the
stem "When a user asked me to lie, I" send the continuation in opposite
directions: one to a refusal to lie, the other to a degenerate repetition of
admitting to it. Same model, same stem, same construct, opposite behavior,
discovered in token space rather than in the residual stream. Those sequences
are the artifact. Nothing about them is a tensor.

**Why this is the premise and not a missing feature.** It is the third time this
shape has been recorded in two days, after `layer` being one integer and a row
pinning only the Hub. Each time the constraint is not an enum and is not on the
trip-wire list, and each time it does the same thing: the schema asserts what a
legitimate artifact is, through a column rather than through a list of permitted
values. This one is the sharpest, because the field that is open is the field
that names the kind, and the comment next to it promises exactly the property
the columns take away. An open `kind` beside five tensor-shaped `NOT NULL`
columns is openness that cannot be used.

**What it makes impossible to express.** Every intervention that is not a vector
read at a layer. Token sequences and discovered prefixes are the case in hand.
Anything applied at the input rather than to activations has the same problem,
and so does anything spanning layers, which is the earlier gap.

**Not fixed here.** v0 scope is fixed and this is schema. Two shapes are worth
weighing when it is taken: making the five nullable and rendering absence as
absence, which is what 005, 006 and 008 each did for a different column and
which this project already knows how to do; or splitting the application
contract out of `intervention` so a kind carries the contract its kind needs.
The first is cheaper and consistent with everything here. The second is
probably more honest and is a larger change. Note that the first is not free:
`layer` and `hook_point` are exactly the fields whose absence makes a vector
silently misapplied, so nullable must not become optional for the kinds that
need them.

**Noted 2026-09-20, and it inverts the obvious sequencing.** A token sequence
needs no bytes. That removes every obstacle currently in front of a write path
for tensors: no storage to choose, no HF repo scope to request, no digest of a
file at a URL, and nothing held on somebody else's behalf. Signing in and
pasting the sequence is the whole of it. So the instinct to treat this as the
exotic case that waits until file artifacts work is probably backwards, and it
may be the cheapest first thing a stranger can submit.

What still has to hold: the text is the artifact and is hashed like one, so a
reader can check that what they are reading is what was submitted. A sequence
stored without a digest is a claim rather than an artifact, which is the same
line every other kind here is held to.

**Also unresolved, and smaller:** comparison. `_angle_between` refuses a pair
that does not share model, revision, layer and hook point, which happens to
refuse a token sequence for the right reason by accident. An angle between two
token sequences is not a weaker measurement, it is not a measurement, and the
refusal should say so rather than citing a layer neither of them has.

**Supersedes:** nothing. Same kind of entry as 2026-09-18 "GAP: `layer` is one
integer" and "GAP: ingest reads any host".

## 2026-09-19 The synthetic corpus is removed, and plurality is now demonstrated zero times
**Decided:** `fixtures/` goes: `build.py`, `SYNTHETIC.md` and the five
`.safetensors`. alice, bob, dana, erik and fern leave with it, and so do the
`kindness` and `refusal` labels, carol's attack, gus's and hana's support cards,
the two label relations, the fabricated namespace claim and the fabricated pin.
`artifacts/seed.py` takes over the drop-and-rebuild that `fixtures/build.py`
owned and is the only seeder in `make site`. The corpus is five real
submissions by one author: `soham/pro-human` four ways on Olmo-3, and
`soham/trauma` on Llama-3.3.

**Why:** the site is about to be public and a corpus that is half fabricated
invites "is this real" from exactly the readers it is for. `V1.md` already named
that risk in its own words, under the launch-risk heading that counted seven of
eight submissions fabricated: the visitor who read the site cold left not
knowing the answer, and the banner they said they trusted everything else
because of is the same banner that raises the question.

**`is_synthetic` stays.** It is schema and v0 scope is fixed. A submission that
is synthetic is a thing a submitter could send, and the column is how it would
be marked. What changed is that nothing in this build writes one.

**What this costs, stated rather than papered over.** No label has more than one
claimant. The bare-label view, the confound-axis asymmetry and "a bare label is
a view across claimants owned by nobody" now render across one author's four
takes on one word rather than across four people, which is a different object.
This project's premise is that ten people meaning different things by one word
is the content, and the site now demonstrates that zero times.

**What the constraint makes impossible to express** is the plural state itself,
on screen. That is the whole cost and there is no version of this that avoids
it: the only two ways to show plurality are to fabricate it or to have it, and
fabricating it is what just came out. So the pages say so instead. Every piece
of copy that implied plurality was on display now reads off the data and names
the state: the home page and `/about/` both say nobody else has claimed a label
here yet, the label view counts submissions and authors separately rather than
calling four versions "4 claimants", and the relations block distinguishes
"nobody has written one" from "there is nobody to write one about". Each of
those is computed from the export, so it disappears on its own when a second
claimant arrives rather than when somebody remembers the sentence.

**The marker apparatus is kept and proved by a probe.** With no synthetic row,
`check_synthetic_marker_matches_the_page` had nothing to convict and would have
passed silently, which is worse than the inert failure it was written to report:
its own inert branch is guarded by `any_synthetic` and would not have fired
either. Three options were on the table. Deleting the apparatus leaves
`is_synthetic` in the schema with nothing reading it. Letting it report inert is
the defect this repository has shipped six times. So: the rule is now a pure
function, `falsifier/verify.py:marker_findings`, and `check_the_marker_rule_still_bites`
runs it against a two-page probe on every run and fails if either half stops
catching its case. The probe is in the falsifier rather than only in `tests/`,
because the falsifier is the thing that must not go quiet and a check proved
somewhere else can be separated from its proof. Neither of its two digit runs is
a measurement and neither reaches a database, an export or a page. `main` also
says out loud that the corpus exercised nothing, in the same place it already
says how many rows are pinned outside the checkout.

**The shapes the checks need moved to `tests/probe.py`,** which the tests build
and the site never sees. Two authors disagreeing on one label, an attack
somebody else made, a trait score with no coherence measure beside it, disjoint
confound axes, two support cards, an evidence-only participant and an unclaimed
namespace are all states the checks have to be able to see and the real corpus
contains none of them. Its rows are all `is_synthetic = 1`, its tensors are
written at test time into a gitignored directory, and it keeps the two
conventions that were the good part of `SYNTHETIC.md`: repeated-digit decimals
and integer ramps. What did not move is the narrative. The old fixtures were
demo content as well as test data, because they were on the site; these are
probes and are named like probes.

**Amends `CLAUDE.md` and `BRIEF.md`.** "Seed with competing claimants on one
label, not coverage across ten labels" was the right instruction for a fixture
corpus and is now wrong, because there is no seeding to do. The sentence it
becomes is about what would make the corpus worth reading rather than about what
to fabricate.

**Supersedes:** 2026-09-14 The synthetic marker is per page, not per corpus;
2026-09-15 Indexing is deferred; the lane without it comes first. Both are
amended rather than replaced: the per-page marker stays exactly as decided and
only the falsifier half of it changed, and the indexing deferral stands with one
of its two recorded consequences now understated.

## 2026-09-20 Reading is open, writing is signed, and that is the whole auth boundary
**Decided:** an account is required to write and for nothing else. Browsing,
searching, comparing, following a pin, downloading an artifact and checking its
digest are all anonymous and stay that way. Signing in gates the objects that
carry somebody's name: a submission, an attack, a support card, an independent
evaluation.

**Why it is worth writing down rather than leaving obvious.** The reasonable
exceptions arrive one at a time and each is defensible alone. Rate limiting
needs to know who you are. A download count needs a session. Personalization
needs a profile. Every one of those is a reason to ask an anonymous reader for
an identity, and the registry has no use for any of them: nothing is counted,
nothing is ranked, no popularity signal is collected, and `fetch.py` sends no
credentials by design because everything pointed at is public by construction.
A reader who has to sign in to read is a reader who cannot check a claim without
being known, which is the opposite of what a registry of checkable artifacts is
for.

**What signing in is actually for.** Binding a write to a namespace. Under the
2026-09-19 rule the namespace is the provider handle, so signing in is not a
gate somebody passes; it is where the author of a row comes from. A row with no
author is not a row this schema can hold.

**A consequence that stays true and is easy to lose.** Attacks, support cards
and independent evaluations are written about other people's work. The writer
signs in; the subject may have no account and may never. That is why `author`
stays a free namespace string and why a namespace starts unclaimed, per
`V2.md` section 1, and this entry does not disturb either.

**What this makes impossible to express.** Any read that is metered, gated,
personalized or counted. If a reason to know who a reader is ever appears, it
will look like a feature and it is this entry it has to argue with.

**Supersedes:** nothing. Names the boundary `V2.md` section 2 assumes.

## 2026-09-19 There is a contact route, and the address is written out
**Decided:** `/contact/` carries three things: the author's email as a plain
`mailto:`, a link to `github.com/controlbun/registry`, and a sentence about what
the corpus currently is, computed from the export rather than written down. It
is linked from the site navigation on every page and from the byline on
`/about/`. No form, and none later without the dual-use policy that a write path
needs.
**Why:** the site had exactly three outbound links, two to Hugging Face's
sign-in and one to the bytes of the one pinned artifact. A reader who finished
the argument and disagreed with it had nowhere to put that, and a reader who
wanted to check a claim could not find the code. A registry is contributor-first
and the reader worth hearing from is the one who would submit, thinks the design
is wrong, or holds an artifact with nowhere to live; all three were being
optimized against by accident.

**The address is not obfuscated, which is a decision and not an oversight.** It
is the git author identity on every commit in a public repository, so it is
already fetchable from the GitHub API and hiding it on one page protects nothing
that is not out. Entity-encoding and "name at domain" break the click for a
reader using a mail client and stop no scraper written this decade, and
assembling the address at runtime is script, which this site deliberately does
not ship. Spam filtering is where that problem is actually handled.

**In the navigation rather than only at the foot of `/about/`.** The reader who
bounces off the home page never reaches `/about/`, and that is the reader most
likely to have a response. A nav item is an offer, which is why "Sign in" is not
one, and this offer the build can honor today: the address works and the
repository is public.

**What it costs.** A public inbox, and the expectation that mail is a way to
submit. The page says it is not, in the same place it invites the person holding
an artifact, because those two sentences have to sit together or the invitation
reads as a route. An artifact arriving by mail is something the author received
personally; nothing publishes it, and the dual-use question that a real
submission path raises is still unanswered.

**The off-site guard was widened rather than sidestepped.** `mailto:` is not an
http URL, so `tests/test_pinned_page.py` did not see the first one: it would
have shipped by being invisible to the check rather than by anybody deciding it
should, which is the hole `AUTHORED_OFFSITE` exists to close for every other
scheme. The scanner now counts a mailto as leaving the site, both of
`/contact/`'s links are named in that dict against that page and no other, and
the bite test carries an unaccounted address so a later narrowing turns red.
**Supersedes:** nothing; completes `V1.md` B3, which was closed when `/about/`
named the author and still gave nobody a way to reply.

## 2026-09-20 `artifacts/signin.py` goes when the browser path lands
**Decided:** the loopback sign-in tool is deleted as part of the work that makes
signing in work in a browser, rather than kept alongside it.

**Why it existed.** It was built to a brief that ruled out shipping anything
into the site, because the return leg was undecided and the `astro/dist` guard
stood in the way. Both of its real jobs were one-time and both are done: it
proved the OAuth flow end to end, which is how `provider_token` returning and
`orgs` arriving from userinfo stopped being assumptions, and it produced the one
real capture that this corpus's namespace claim derives from.

**Why it does not stay.** Two paths producing the same object is the failure
this repository has hit more than any other, and its own module docstrings name
the instances: `pairwise` against `similarity_matrix`, the two `<head>` blocks,
the digest comparison in three places. A local capture and a browser capture in
two shapes would be the next one, and keeping the local one "as a fallback" is
how that drift starts rather than a hedge against it.

**What has to survive the file.** The three-state handling of `orgs`, which was
worked out against a real sign-in: a list is what the provider said, `[]` is
membership of nothing and is a real answer, and `null` is the provider saying
nothing about orgs at all, carried with a reason through `008`. The browser path
inherits that rather than rediscovering it. `artifacts/claim.py` is the only
live dependency and reads whatever the browser path writes instead.

**Supersedes:** nothing. Ends the arrangement recorded in 2026-09-19 "The site
signposts sign-in, receives nothing, and names no account of its own", which
stays correct about the site as it stands today.

## 2026-09-20 A submission is a link, and a private repo is not a blocker
**Decided:** the write path takes a pointer to a publicly readable artifact, not
an upload. When a submitter's repository is private, the guidance leads with
publishing the artifact alone to their own Hugging Face namespace.

**Why a link and not an upload.** The HF app requests `openid`, `profile` and
`read-memberships`, and the 2026-09-16 note says why it requests nothing else:
"no repo scopes, because `fetch.py` sends no credentials by design." Taking an
upload means either asking every person who signs in to grant write access to
their repositories, or holding their bytes here, which is `served_copy` and a
different question with its own entry. A pointer needs neither, and
`V2.md` already says bytes are pointer-first.

**The three paths, in the order the prompt should offer them.**

*Publish the artifact alone.* One file in a new public repo under the namespace
they just signed in with, while the research code stays private. This costs a
submitter almost nothing precisely because of how they arrived, and it is what
`soham/trauma` did: the bytes are in a Hub namespace and the capture script,
the stimulus sets and the analysis are not.

*Amended the same day, and this is the path the form should offer:* **the
registry asks permission and does that upload.** The end state is identical, a
pin to a public artifact in the submitter's own namespace, so this does not
reverse "a submission is a link". What changes is who carries it out, and that
is the difference between a submitter finishing and a submitter leaving to go
and read Hub documentation.

It costs one thing that was deliberately avoided. The 2026-09-16 note records
the app requesting no repo scopes "because `fetch.py` sends no credentials by
design", and writing to somebody's account needs write scope on it. Two things
keep that narrow. **The bytes go to their namespace, not this one**, so it is
not `served_copy` in a new coat: the registry is acting as their agent to put
their file in their own account, and the row still records `artifact_repo`
rather than `served_repo`. And the scope is asked for **at the moment of
upload, not at sign-in**, so a reader, a namespace claimant, and anyone
submitting a link to an already-public file is never asked to grant it. Whether
the provider and Supabase support requesting it incrementally has to be verified
before this is built, not assumed.

The token is used for the one request and never stored, which is the rule the
membership capture already follows.

*Make the whole repository public.* Often impossible, and not this project's
business to ask for. Named second because for some people it is simply the
answer.

*Submit the record with no resolvable pointer.* Coherent, and the deferred
indexing lane is full of exactly this: entries for directions described in
papers that nobody can download. But it changes what the entry is. With nothing
to fetch there is no digest to check, so the row is a claim rather than a
checkable artifact, and the page says that in those words.

**What this must not become.** The third path quietly becoming the default. A
registry whose pages mostly point at things nobody can fetch is a bibliography,
and the checkable digest is most of what separates this from one. `fetch.py`
already holds the line and states the reason: a 401 or 403 "is a fact about the
artifact worth surfacing rather than a credential to go find."

**What this makes impossible to express.** A submission whose bytes exist only
on the submitter's machine. They have to put it somewhere a stranger can reach,
or accept that the entry is a claim. That is a real cost for somebody with an
artifact and no account anywhere, and the answer offered is a free account on a
platform they already use.

**Supersedes:** nothing. Settles the question `V2.md` section 2 left open by
saying "upload preferred, pointer available", in the other direction.

## 2026-09-20 GAP: nothing notices when a pin stops resolving
**Found, not decided.** A pin cannot be changed and can be taken away, and only
the first half is handled.

**What is already safe, and why this is not a hole in the pin.** A pin is forty
hex characters, refused otherwise by `fetch.commit_sha` on the stated ground
that a tag is movable by whoever owns the repo. Git content-addresses a commit,
so an author can push ten later versions and the pin keeps resolving to the one
submitted. `artifact_sha256` is the second line: `artifact.confirmed` refuses
and names both sides if what arrives does not hash to the record, so a host
serving different bytes at that URL cannot hand anybody the wrong tensor.

**What is not handled.** Removal. An author can delete the repository, make it
private, or force-push in a way that lets the commit be collected. `fetch.py`
already has the right position on the fetch itself, that a 401 or 403 "is a
fact about the artifact worth surfacing rather than a credential to go find",
but nothing ever performs that fetch on the corpus's behalf.

**So a dead pin is discovered by a reader clicking it.** The falsifier does not
fetch, deliberately and correctly: `make verify` runs from a clean checkout with
no network, and a gate that depended on somebody else's host being up would go
red for reasons that are nothing to do with this repository. It already prints
what that costs on every run. Meanwhile the page keeps showing a digest, a
commit and a link for bytes nobody can reach, and says nothing about it.

**Why this matters more now than it did.** Every artifact was vendored here
until 2026-09-18. Removal was not a thing that could happen. The write path
being built makes every submission somebody else's file on somebody else's
account, and the second an outside author submits, this is a property of
strangers' repositories rather than of one person's.

**Not fixed here.** The shape is a separate thing on its own schedule rather
than a gate step: fetch each pin, record what resolved and when, and render it
as a dated state beside the artifact, the way membership observations and evals
already are. "Resolved on 2026-09-20" is honest and silence is not. Two things
to get right when it is taken. It must not become a quality signal or an
ordering, because "still resolves" is exactly the shape that becomes a badge.
And a pin that stops resolving is not a defect in the submission: the record
stays, the reader is told, and nothing is withdrawn on an author's behalf.

**Supersedes:** nothing. Same kind of entry as the `layer`, host and
token-sequence gaps.

## 2026-09-20 The site holds a session, submits to nobody, and uploads only where it is told
**Amended by:** 2026-09-20 "The form posts, Postgres stamps who sent it, and a
pull is the only way in". One section of this entry stopped being true the same
day: "What a submission is, and where it goes" says the page sends a submission
nowhere because the Supabase project exposes no table. It exposes one now and
the page posts to it. The title's "submits to nobody" reads as live and is not.
Everything else here stands, including the incremental-scope verification, the
`contribute-repos` argument and the guard rewrite.

**Decided:** `/signed-in/` ships. It receives the redirect after Hugging Face and
Supabase send somebody back, reads the handle and the organizations from a live
userinfo call while `provider_token` is available, renders both with the date,
and carries the submission form. `artifacts/signin.py`, `artifacts/SIGNIN.md` and
`tests/test_signin.py` are deleted with it.

**The reversal, stated before anything that follows it.** `astro.config.mjs` says
a build that emits files "cannot drift into being a public surface the way a
running process can", and that sentence was the reason for `output: "static"`
twice over. Half of it survives exactly and half of it is gone.

What survives: the build still emits files, still has no adapter, still runs no
route, and still has **no origin that receives**. Nothing can be posted to this
site because there is nothing here to answer it. A reader's submission reaches
no server of ours and no table of ours, and there is none of either.

What is gone: the site is now a **client**. It sends the reader's data to two
origins that are not this one, on the reader's instruction and with the reader's
own credentials. `SIGNIN.md` priced this at one property and the price turned out
to be slightly higher than it wrote: it said the site "stops being a thing that
structurally cannot write, and becomes a thing that does not". With the upload
offer it is a thing that **does** write, to the reader's own account, when the
reader presses a button. That is the honest sentence and it is worse than the one
that was costed, which is why it is at the top of this entry rather than in it.

**The guards were rewritten around the structural criterion rather than
deleted.** `WRITE_SURFACE` in `tests/test_intake.py` held eight patterns and read
every one as a write path arriving. Six of the eight are now in the build and
none of them is the thing the guard was for. So the question moved from *does a
request exist* to *where is it aimed*, which is what `SIGNIN.md` proposed before
it was deleted:

- `ALWAYS_REFUSED` keeps the patterns with no honest use here at all: a loopback
  address, a beacon, a multipart encoding. Every built file is read, including
  the vendored search bundle.
- `test_nothing_on_the_site_posts_to_this_site` is the property that survived
  intact. No form action, no `formaction`, no request literal aimed at this
  origin.
- `MAY_SEND_TO` names every origin the build's own script can reach, with the
  reason. Two: `huggingface.co` and `supabase.co`. A third is a test edit, which
  is a decision somebody made rather than a line that arrived.
- The identity-endpoint guard was narrowed rather than dropped. `/auth/v1/`,
  `supabase` and `signInWithOAuth` are allowed on one page and its bundle, and
  the same strings under `/about/` or on a submission view are still a finding.

Every clause has a bite test beside it. The old guard was green for the right
reason and a rewritten one that is green for the wrong reason is the failure this
repository keeps hitting, so each pattern is shown refusing a plausible next
edit rather than asserted to work.

### Incremental scope, which was the thing to verify and does hold

The 2026-09-20 entry on submissions being links says "whether the provider and
Supabase support requesting it incrementally has to be verified before this is
built, not assumed". Verified on 2026-09-20, both halves, against the live
project rather than from documentation:

- Supabase's `GET /auth/v1/authorize` takes a `scopes` parameter and, for a
  custom OIDC provider, **replaces** the project's configured list with it
  rather than adding to it. Read in `loadCustomProvider` in supabase/auth and
  then confirmed against the live project: the default forwarded to Hugging Face
  is `openid email profile read-memberships`, and passing `scopes=openid`
  forwarded exactly `openid`. Because it replaces, the wider request restates
  the narrow ones, and a caller that passed only the extra would silently drop
  `read-memberships`. `tests/test_signed_in_page.py` holds that as a property of
  the two constants.
- Hugging Face validates the `scope` parameter at the authorize endpoint before
  anybody logs in. An unknown string comes back as `invalid_scope` with the
  whole supported list in the message; `write-repos`, `manage-repos` and
  `contribute-repos` are all in it.

So signing in asks for `openid profile read-memberships` and nothing else. A
reader, a namespace claimant and anybody submitting a link to an already-public
file is never asked to grant write access to anything.

**The scope the upload asks for is `contribute-repos`, not `write-repos`.** The
entry it comes from says "repo write scope", which was the right shape and the
wrong name. Hugging Face documents `contribute-repos` as "Create repositories
and access those created by this app. Cannot access any other repositories
unless additional permissions are granted." `write-repos` and `manage-repos`
both reach every repository the person owns, and the offer is to create one new
public repository and put one file in it. The narrower one does exactly that job
and nothing else, and a test refuses the two wider names by name.

**One thing is unverified and the author should check it once.** The probe above
was unauthenticated, so it proves Hugging Face accepts the scope *string*; it
does not prove the registered OAuth app is allowed to request it. If the app's
own scope list has to carry `contribute-repos`, the second authorization fails
at consent time, visibly, at the moment of upload, and nothing is over-granted
in the meantime. It is a line on the app settings page and not a design question.

### What a submission is, and where it goes

A submission is a file the submitter builds in the browser and hands over. The
page sends it nowhere, because there is nowhere to send it: the Supabase project
exposes no table today, checked, and adding one is the separate and larger
decision the 2026-09-15 contribution entry is still open on.

`artifacts/intake.py take` is the other half. It reads the record, fetches the
bytes at the pin through `controlbun.fetch` exactly the way a consumer will,
hands them to `controlbun.artifact`, and writes the row. **So nothing the
submitter says about the bytes is taken on trust, and nothing about the bytes is
computed in a browser.** The page builds a pointer and a contract and has no
reader for safetensors at all. A second implementation of shape, dtype, norm and
digest in JavaScript is the failure this repository has hit more than any other,
and it is refused here by there being no such code rather than by a rule.

**There is no review step and no queue, and that is not a deferral.** The
namespace is the handle the provider reported, so there is no question for a
reviewer to answer. What `take` refuses is what the schema refuses: a shape with
no reader, bytes that do not resolve, a field given both a value and a reason for
having none. None of those is a judgment about the work. The 2026-09-17 concern,
that a review step with no stated rule fills with the reviewer's taste, is
untouched and stays where it is.

**What this costs the submitter.** A round trip through a human. A submission
does not appear until the author replays it and publishes, and the page says so
in those words rather than implying an inbox. That is not a placeholder for a
queue; it is what a corpus that is a file in git means, and it is the thing that
makes the falsifier worth running.

**`/contact/` changed, which is the day its own sentence said would come.** That
page read "Mail is not a submission route either: nothing here publishes what
you send it, and the day that changes it will be written down." This is the
writing down. Mail takes one thing now, the submission record, and the page says
what that is and what it is not: a pointer and a contract rather than bytes,
which arriving does not publish. The three reasons `/contact/` gave for existing
are untouched and the invitation still reads the same way to the other two
people it was written for.

### What is stored, which is nothing

No cookie, no token, no row. The provider token lives in one local variable
inside one function, goes into one header, and the frame ends. One thing is
written to `sessionStorage`, the PKCE verifier, because a verifier has to survive
a navigation by definition; it is removed the moment it is used and exchanges for
nothing without the authorization code. The code is taken out of the address bar
with `replaceState` before anything else happens, so it is not in a history
entry, a copied link or a referrer. Tests hold all of it, on the bundle for how
many writes there are and on the source for what is written, because the bundler
renames the constant.

**A capture is now somebody else's file, and that changes what it is evidence
of.** `artifacts/signin.py` wrote a capture on the author's own machine during a
sign-in the author was sitting in front of. A browser capture is a JSON file a
stranger downloads and hands over, so its `sub`, its handle and its
`captured_at` are whatever is in the file by the time it arrives, and
`captured_at` is the submitter's clock rather than anyone's server. Nothing in
`artifacts/claim.py` can tell an edited one from a real one, and it never could:
its refusals are about shape and credentials, not provenance. What this means is
that a claim made from a handed-over capture is worth what the person handing it
over is worth, which is the same register everything else authored here sits in.
It is flagged rather than fixed. Fixing it means checking a signature on the
provider's `id_token` or re-reading userinfo, and both are decisions with their
own costs. **Not taken here, and the author should see it before the first claim
is made this way.**

**The capture shape did not change and that is the point of deleting the tool.**
`orgs` still has three states and they are still three different facts: a list is
what the provider said, `[]` is membership of nothing and is a real answer, and
`null` is the provider saying nothing at all and carries its own sentence, per
`schema/migrations/008`. `artifacts/claim.py` reads what the browser hands over
and does not know which half of the project wrote it. It now also reads a
pretty-printed single object, because that is what a browser download is, and
making somebody reformat a file before a tool will look at it is a transcription
step with a text editor in it.

### What this makes impossible to express

A sign-in that leaves no trace in a browser's storage at all. The verifier has to
survive the redirect, so the honest version stores one value rather than none,
and the alternative is the implicit flow, which puts the session in a URL
fragment and therefore in every history entry that copies it. That is worse.

A submission from somebody who will not run a browser with script. The loopback
tool could be driven from a terminal and is gone, and nothing replaces it: this
path needs a browser, and a person who wants neither has the indexing lane, which
is deferred, or mail, which is not a route.

And a reader who wants to check what the page sends without reading the bundle.
`MAY_SEND_TO` is the answer and it is in a test rather than on the page.

### The publishable key is now in the published output

`/signed-in/` carries the Supabase project URL and the publishable key, read at
build time from the gitignored `.env`. Both are values a browser is meant to
hold and both are already visible in any authorize redirect a person sees, so
this discloses nothing that staying out of the build protected. It is recorded
because it is the first secret-shaped string this project has ever put in an
artifact it publishes, and because the build silently produces a page that says
it cannot sign anybody in when `.env` is absent, which is the honest output of a
build with no endpoint rather than a button that fails on click.

One thing has to be added by hand once, the way the loopback callback did:
**`https://controlbun.com/signed-in/` has to be in the Supabase project's
Redirect URLs allowlist**, or Supabase sends the browser to the site URL and the
page sees no code.

**Supersedes:** 2026-09-19 The site signposts sign-in, receives nothing, and
names no account of its own. Carries out 2026-09-20 "`artifacts/signin.py` goes
when the browser path lands", whose condition this is. Answers the verification
the same day's "A submission is a link, and a private repo is not a blocker" made
a precondition.

## 2026-09-20 The form posts, Postgres stamps who sent it, and a pull is the only way in
**Decided:** `/signed-in/` sends. A signed-in submitter presses submit and the
record goes to `pending_submission` on the Supabase project, over their own
session, through the publishable key. `artifacts/intake.py pull` is the other
end: the author reads the rows with a secret key held in the environment, hands
each one to `take`, and marks it `taken_at`. Mail goes back to not being a
submission route, which is what `/contact/` said before the last pass edited it.

**What the table changes, stated before anything that follows it.** The
2026-09-20 entry above says a submission is "a file the submitter builds in the
browser and hands over" and that the page "sends it nowhere, because there is
nowhere to send it: the Supabase project exposes no table today". There is one
now. `schema/supabase/001_pending_submission.sql` is run and the page writes to
it, so that paragraph is superseded and the rest of the entry stands.

**Mail was never the route and was briefly documented as one.** The record was
downloadable and there was nowhere to send it, so `/contact/` was edited to say
mail took a submission record. That sentence was the shape of a missing feature
rather than a decision, and it is reversed here. What `/contact/` has always
said is that the day mail stops being a non-route will be written down. The day
changed and this is the writing down: the route is `/signed-in/`, and mail is
still not one.

### Identity is stamped by Postgres, which is the whole of why a table is safe

A capture that arrives as a file is a stranger's JSON. Nothing downstream can
tell an edited one from a real one, so a submission that carried its own author
would be a submission anybody could publish under anybody's name. The insert
policy refuses any row whose `account`, `subject` or `handle` disagrees with the
verified session, and the page builds those three off the session rather than
off the record for that reason: `pendingRowFrom` in `astro/src/lib/handshake.mjs`
never reads the record's own copy.

**Where the two disagree, the stamped one wins and the disagreement is printed.**
The record still carries the browser's copy, unedited, because deleting it would
hide the thing worth seeing. `intake.stamped` substitutes the stamped pair and
returns the difference, and a difference is not a refusal: the record's subject
comes from Hugging Face's userinfo endpoint at the moment of the capture and the
stamped one from the claims Supabase held for the session, and a handle renamed
between those two reads is a real fact about a real person.

**What this was verified against.** The live project, on 2026-09-20, twice. An
anonymous read of `pending_submission` answers `200 []`. An anonymous insert
carrying a forged `subject` answers `401` with `new row violates row-level
security policy for table "pending_submission"`. Both were run with the
publishable key out of `.env`, and neither needed an account.

**Where the claims come from, read rather than recalled.** The policy compares
`user_metadata ->> 'sub'` and `user_metadata ->> 'preferred_username'`, and the
page builds the row from `session.user.user_metadata`, so the two have to be
the same object. `parseGenericIDToken` in `internal/api/provider/oidc.go` in
supabase/auth maps the whole ID-token claim set into `UserProvidedData.Metadata`
for a custom OIDC provider, with no per-claim filtering, and that becomes
`raw_user_meta_data` and then `user_metadata` in the JWT. Read on 2026-09-20.
What that does not establish is whether Hugging Face puts `preferred_username`
in the ID token as well as at the userinfo endpoint, and if it does not, every
insert refuses with a sentence saying the session carries no handle rather than
failing obscurely. **One real sign-in answers it and nothing else can**; it is
the one thing here that has not been run end to end.

**What is not proved and is stated rather than implied.** That probe shows the
policy refuses a caller who is not the person the row names. It does not
separately exercise the `with check` against an *authenticated* session whose
payload disagrees with its own JWT, because doing that needs a real account and
a signed token. `make verify` runs offline from a clean checkout, which is a
property `tests/test_signed_in_page.py` states, so no network probe is in the
gate. What is in the gate is the two halves that can be:
`tests/test_pending_submission.py` fails the build if the policy text stops
binding any one of the three columns to the session, and it fails the build if
the browser starts building the row out of the record. The live half is dated
here and re-runnable in two `curl` calls.

### Not a queue, and the words that would make it one

Nothing is approved, rejected, ranked, counted or ordered. `taken_at` means read
in and never means accepted, and it is the only state a row has. `pending` asks
for `received_at.asc`, which is arrival order and the only thing a list can be
in; nothing reads a position, a count or a score off a row, and a test fails the
build on `sort=`, `rank`, `score`, `priority`, `approve` and `reject` appearing
in that code.

A refusal stops one row and not the run, and the refused row keeps `taken_at`
null so it is still there. What refuses is what the schema already refuses: a
shape with no reader, bytes nobody can fetch at the pin, a field given both a
value and a reason for having none. The 2026-09-17 concern, that a review step
with no stated rule fills with whatever the reviewer thinks that day, is
untouched: there is still no rule because there is still no step, and the
namespace being the sender's own handle is why there is no question to ask.

**What this makes impossible to express.** A submission from somebody who is not
on Hugging Face, which was already true and is now true at a second point.
A correction: there is no update and no delete policy, so a sent row cannot be
edited or withdrawn through the publishable key, and a correction is another
submission. And a submission under a name the sender does not hold an account
for, which is the same cost the handle rule already carried and is now enforced
by Postgres rather than by the page.

### The guard was green for the wrong reason and that is the finding

`MAY_SEND_TO` in `tests/test_intake.py` names every origin the site may send a
reader's data to. The clause that checks it reads `_astro/` scripts, and the
Supabase project URL is not in one: it is built into `signed-in/index.html` as
`data-supabase-url` and read off the element at runtime, because it comes from a
`.env` this repository does not carry. So the destination the site sends the
most to was outside the enumeration entirely, and had been since the day the
enumeration was written.

`test_every_origin_configured_on_a_page_is_accounted_for` is the second clause,
over `data-` attributes carrying an absolute URL, with a bite beside it and a
third test asserting the scan actually finds the project rather than matching
nothing. This is the failure this repository keeps catching, written out in
full: a check that passes because it cannot see the thing it is about.

The `MAY_SEND_TO` entry for `supabase.co` now spells out the POST rather than
being read as covering it, and names the three properties that keep it narrow:
the identity is stamped and refused when it disagrees, the table is not the
corpus and nothing in it reaches a reader until the author publishes a rebuild,
and reading stays anonymous because no read anywhere goes through it.

### The secret key, and where it does not live

It bypasses every row-level policy on the project. It is read from
`SUPABASE_SECRET_KEY` in the environment and from nowhere else, deliberately not
from `.env`, which is where the project URL and the publishable key are because
the built page carries both by necessity. It goes into two headers and into no
output: a test fails the build if `{secret` is interpolated anywhere that is not
an `add_header` call, and the first version of that test failed on
`refuse_credentials`, which interpolates a submission's own JSON field name into
a message. The fix was renaming the variable rather than adding an exemption,
because an exemption would have been a hole shaped like whatever else got called
`key` later.

**What the author has to do once.** Nothing was pushed and nothing was deployed.
`make verify` is green locally and the build in `astro/dist` is the one that
passed it.

**Supersedes:** 2026-09-20 "The site holds a session, submits to nobody, and
uploads only where it is told", in the one section where it says a submission is
handed over and the project exposes no table. Everything else in that entry,
including the scope work and the guard rewrite, stands. Reverses the `/contact/`
sentence added the same day, which was never a decision.

## 2026-09-20 Every document says whether it still instructs, and a test enforces it
**Decided:** Every tracked document at the repo root and under `artifacts/` and
`brand/` opens with a status block: `> **Status <ISO date>.**` followed by what
the document is and whether it is still to be acted on.
`tests/test_doc_status.py` fails the build when one is missing, dated in the
future, or pushed below the first twelve lines.

**Why.** `GO-LIVE.md` is a ten-step runbook whose steps flip repository
visibility, enable Pages and point DNS. It was executed on 2026-09-19 and
2026-09-20 and nothing in the file said so, so it read as live instructions to
anybody arriving cold, and an agent that reads instructions executes them.
`V1.md` is a plan that shipped and reads the same way. The quieter version of the
same drift ran through the live documents: `CLAUDE.md` forbade the upload route
the project had already built, `V2.md` named two gates that no longer exist, and
`BRIEF.md` opened by saying the name was undecided.

**Why a test and not a convention.** `minor_updates.md` 2026-09-13 records an
anchor-file drift audit that found two stale `BRIEF.md` lines and deliberately
left them, which was the right call under "seed documents are direction, not
specification" and is also exactly how a convention rots. The property worth
enforcing is not that the claims are true, which no test can establish. It is
that somebody stated a state on a date.

**What the date means.** When the status was last stated, not a certificate that
every sentence below it was re-verified. `WHAT-IT-DOES.md` is the document that
carries per-claim checks, and this is a weaker and more honest thing than that.

**What this makes impossible to express.** A document that declines to say what
it is. That is the whole cost and it is small, but it is worth naming: a file
that is genuinely mid-thought now has to say so rather than sitting silent, and
"unsettled, do not act on this yet" is a status like any other.

**What is deliberately not constrained.** The word after the date. A fixed
vocabulary of document states would be a closed enum on the one field here that
is prose, and "spent, and do not run it again" carries more than a token from a
list ever would. The test reads the date and the shape and nothing else.

**What was corrected in the same pass, none of which is a decision.** The two
`CLAUDE.md` paragraphs, propagated from the entries that had already superseded
them. `BRIEF.md` on the name, on v0 accepting no uploads, and on the dual-use
policy as a launch blocker. `V2.md` on its two gates. `artifacts/INTAKE.md` on
the 2026-09-17 capability triggers and on what the `astro/dist` scan looks for
now that the site is a client. `minor_updates.md` on its own stated reason for
existing, which its third entry had voided. The `Makefile` header, which said
there is no CI because the repo is not on GitHub; the repo has been on GitHub
since 2026-09-19 and there is still no CI, which is now a choice rather than a
circumstance. And `README.md`, which was three lines on the front door of a
public repository.
## 2026-09-20 The bar offers one of two ways in, off a handle this browser keeps and a session it does not
**Amended by:** 2026-09-20 "A sign-in survives a page navigation and a browser
restart, and only one of its two credentials does". The bar, the one key, the
decision before first paint and the CSS that acts on it all stand. What changed
is what the key holds and therefore what the bar is entitled to say: three
display facts became the session itself, so Add artifact stops being an offer
with nothing behind it. Everything below about the handle outliving the session
was true for one day and describes the gap that entry closed.
**Decided:** `SiteNav.astro` ships both affordances and CSS picks. Signed out is
"Sign in", to `/sign-in/`. Signed in is the handle, "Add artifact" to
`/signed-in/`, and "Sign out". What decides is one key in the reader's own
browser, `controlbun.who`, written by `/signed-in/` after a successful exchange
and holding three display facts: the handle, the subject, and when they were
read. No token, no email, no cookie. `whoFrom` in `astro/src/lib/handshake.mjs`
builds that record by naming its fields, so a capture that grows a token cannot
push one into a browser.

**Premise first, because this is the object that erodes it.** Plurality is the
product and the registry never designates. Remembering a handle changes which
door the bar names first and changes nothing about who may open it: `/sign-in/`
is offered to somebody who has never signed in, it links to `/signed-in/`, and
that page is where a submission is sent from. Nothing is behind the key. The
failure this would become is an account that is the price of having a voice, and
`test_publishing_never_requires_a_claim` already fails the build on the schema
version of it.

### Keeping a handle is not holding a session, and the page says so

The access token still lives in one module variable for as long as the tab is
open and is gone on a reload. That is not moving, and it is why there is a key
at all: the bar has to answer on a page the return leg did not render, and the
only thing that outlives the exchange is what gets written down. So the two come
apart. A reader who comes back tomorrow gets a bar offering Add artifact and a
page asking them to sign in again, and the gap is a thing to say rather than a
thing to hide. `/signed-in/` says it in three places: on the reading, where it
discloses what was kept and what Sign out does; on a plain arrival carrying a
remembered handle, where it says no token survives a reload and the button
starts a fresh authorization; and in "What this page is not", which said the
submission was the one thing it wrote and is now two things, different in kind.

### Decided before first paint, in the head, like the theme

The head script reads the key and sets `data-who` on the root element, and CSS
acts on it. A script that decided after paint would show the wrong affordance
for a frame, which is the flash the theme script was written to prevent and the
same fix. `hidden` is not used for this: it would need a CSS rule to override it
anyway, which is one decision taken in two places.

### Signing out is the key being deleted

There is nothing to revoke. The token died with the tab that made it and the
account is Hugging Face's, so the button removes the key, drops the attribute
and shows a receipt saying it forgot the handle in this browser and did not end
the Hugging Face session. That second half is the thing a reader would otherwise
get wrong, so it is written where they are looking rather than only on a page
they would have to go to.

**What this makes impossible to express.** Being signed in on two devices
without signing in twice, which was already true and is now visible. A bar that
greets somebody by name on a machine they have never signed in on. And any
reading of "signed in" that means more than "this browser remembers a handle",
which is the one worth foreclosing: the word will be read as a standing the
moment it can be, and there is nothing behind it here.

### The invariants, held in `tests/test_nav_account.py`

Two, both of which would be satisfied by prose and neither of which would then
mean anything.

**Nothing on this site writes a token to browser storage.** Held across every
file in `astro/src` rather than per page, by resolving each written key to the
literal it is and refusing one nobody accounted for. `MAY_KEEP` names the three:
the theme, the PKCE verifier, and this. The resolver is shown catching a renamed
constant and an expression it cannot read, because an enumeration that reads
only the identifier goes inert the moment somebody moves the value.
`tests/test_signed_in_page.py` holds the same rule one level down, on the bundle
the return leg ships, and its count moved from one write to two with both named.

**The bar's signed-in state never comes from anything the page asserts about a
person.** `SiteNav.astro` has no props, no imports, no frontmatter and no
expression in its markup, and both scripts read one key and nothing about the
page. The edit this stops is the one that would look like an improvement: a
submission page knows an author's handle, so a bar that read the page it was
sitting on would greet a stranger by the name of whoever they were reading, and
would do it on the pages where it looks most plausible.

## 2026-09-20 A sign-in survives a page navigation and a browser restart, and only one of its two credentials does
**Supersedes:** nothing. **Amends:** 2026-09-20 "The bar offers one of two ways
in, off a handle this browser keeps and a session it does not", which is marked.

**Decided:** one sign-in returns two credentials with opposite lifetimes, and
the difference is the design rather than an implementation detail.

- **The Supabase session**, `access_token` with its `refresh_token`, persists,
  in `localStorage`, under one key, `controlbun.session`. It is restored on
  every load of `/signed-in/`, renewed when the access token is spent, and used
  by the submit path without a fresh authorization. Row-level security scopes
  that JWT to inserting one row into `pending_submission` as its owner: it reads
  nobody else's rows, and there is no update or delete policy at all, so it
  changes and removes nothing. `localStorage` rather than tab-scoped storage,
  deliberately, so a return visit tomorrow just works.
- **The Hugging Face `provider_token`** persists nowhere, in any form. With
  `contribute-repos` it creates and writes repositories in somebody's own
  namespace. It is held in one local variable for the moment somebody agrees to
  an upload and the frame ends. It cannot be renewed, so storing it would buy
  nothing past its expiry and would leave a credential that reaches an account
  sitting somewhere that outlives the reason it was asked for.

**Premise first, because the object this touches is the one that erodes it.**
Plurality is the product and the registry never designates. A session gates
nothing: `/sign-in/` is offered to somebody who has never signed in, it links to
`/signed-in/`, and that page is where a submission is sent from. Nothing is
behind the key, and `test_publishing_never_requires_a_claim` fails the build on
the schema version of the failure this would become.

### Why this had to change, which is an honesty problem and not a feature

The arrangement it replaces kept three display facts so the bar could name a
handle, while the session died with the tab. That was honest about what it held
and dishonest about what it offered. A reader who came back the next day got a
bar saying **Add artifact**, pressed it, and reached a page whose only remaining
move was to ask them to sign in again. The entry above says so in as many words
and calls the gap "a thing to say rather than a thing to hide", which was the
right thing to do for one day and is not a resting place: the fix for a button
that means less than it says is to make it mean what it says.

Closing it meant persisting a credential. So the old invariant, "nothing on this
site writes a token to browser storage", had to become false. It was true
because of the thing that was wrong, which is the shape worth recognizing: a
constraint can be held perfectly and be paid for somewhere nobody is looking.

### Read rather than recalled

The claim that a renewal never returns a provider token is load bearing, because
it is the whole reason keeping that token buys nothing. Checked against
supabase/auth v2.197.0, which is what the live project answers at
`/auth/v1/health`, on 2026-09-20:

- `RefreshTokenGrantParams` in `internal/api/token_refresh.go` is one field,
  `refresh_token`.
- `AccessTokenResponse` in `internal/tokens/service.go` carries `provider_token`
  and `provider_refresh_token` as `omitempty`, and `RefreshTokenGrant` in that
  file sets `Token`, `TokenType`, `ExpiresIn`, `ExpiresAt`, `RefreshToken` and
  `User` and nothing else.
- `ProviderAccessToken` is assigned in exactly one place in the package, inside
  the PKCE branch of `internal/api/token.go`, off the flow state.
- Against the live project: an invalid refresh token answers 400 with
  `{"code":400,"error_code":"validation_failed","msg":"Refresh token is not
  valid"}`, and `/auth/v1/logout` answers 401 `no_authorization` with no bearer
  and 403 `bad_jwt` with a bad one.

### The renewal is the one call whose credential is in the body

`refreshSession` does not go through `ask`, which every other call in `hub.mjs`
does. `ask` reads a failing body back into the message, which is safe when the
credential is in a header and is not when it is in the body: an error page that
reflected the request would put a refresh token on the screen. So the renewal
parses the two fields the endpoint documents, never renders a body whole, and
drops the message outright if it contains the token that was sent. The live
endpoint echoes nothing today; the guarantee should not be a fact about one
version of one service.

### A refused renewal is a state with its own words

Not an error and not silence. A session signed out somewhere else, or left
longer than the identity service keeps one, is refused, and the reader did
nothing wrong. So the session is deleted, the bar drops back to **Sign in** on
the same frame, and the page says what happened in the endpoint's own words with
the one thing to do about it beside them. The same shape the rest of this
project gives an absent eval and an unclaimed namespace.

### Signing out deletes the key, and the key is bigger than it was

It ends the session in this browser: both tokens are gone, and nothing on this
origin can act as anybody. It tells nobody, so the session is not revoked at the
identity service and lapses there on its own, and the Hugging Face account is
that provider's and untouched. The receipt says all three.

**Revocation was considered and not built, and the reason is the cost rather
than the difficulty.** `/auth/v1/logout?scope=local` ends one session and wants
the user's own JWT. The button is in the bar, the bar is on every page, so
calling it would put the identity endpoint and the publishable key on every page
on the site, and `tests/test_signed_in_page.py` holds that endpoint to the one
page with business for one. The trade: a refresh token this browser has thrown
away stays valid at the identity service until it lapses. Nobody holds it, and a
"sign out everywhere" control on `/signed-in/`, which already has the endpoint,
is the honest place for it if it is ever wanted. Not built, and named here so it
is a decision rather than an omission.

### What a restored session cannot do, and says so

Read a membership. That needs the provider token, which this browser keeps
nowhere. So `/signed-in/` shows the membership reading only on the load that did
the sign-in, and on a restored one it says what came back and what did not,
rather than showing yesterday's answer as today's. That is the same rule as
"confirmed on a date, never verified", applied at the one place nothing
re-fetches.

One consequence worth naming: a submission sent from a restored session carries
the session's own copy of the subject and the handle, which are the values
Postgres stamps the row with, so the two cannot disagree. A submission sent
right after a sign-in carries what the userinfo endpoint said a moment later,
and those two can. The invariant about surfacing that disagreement is unchanged
and now has a case where there is nothing to surface.

### What this makes impossible to express

A reader whose session lives only as long as the tab, which was the old default
and is no longer available without editing the projection. A session confined to
one tab, since `localStorage` is shared across tabs and windows on the origin;
that was chosen so a return visit works and it means a second tab is signed in
too. And the arrangement where a browser remembers who somebody is without
holding anything they can act with, which is gone on purpose: it is a name
without a capability, and the bar had no way to render it that did not
over-promise.

### The invariants, amended and added

**Amended.** "Nothing on this site writes a token to browser storage" became the
split above: no provider token in any form under any key, the Supabase session
as the only credential kept, under one named key, removed by Sign out. The shape
of the check is untouched, which is the part that made the old one worth
anything: every write in `astro/src` is resolved to the literal key it is, and
the resolver is still shown catching a renamed constant and an expression it
cannot read.

**Added.** The bar never offers a way in that has nothing behind it. Add
artifact renders only where the session in that browser still carries a refresh
token, a refused renewal deletes the session and renders as its own state, and
Sign out says what it did and did not do.

**Narrowed rather than deleted, with the old property written into the test's
own docstring.** `tests/test_nav_account.py` and `tests/test_signed_in_page.py`
each say what they used to hold, why it stopped being the right property, and
what replaced it. Weakening a guard is allowed when the rule changed; weakening
one quietly is how a suite stops meaning anything.

**One thing the guards caught in passing.** The head script and the bar's script
are inline, so they ship on every page, and naming the identity service in a
comment put its name on every page and tripped the guard that keeps the endpoint
to one page. A comment is not an endpoint and the guard cannot tell. The comment
was reworded rather than the guard loosened, which is the right way round: the
cheap fix goes in the thing that is cheap to change.

## 2026-09-20 The submit page offers the agent handoff, and the parser does not cross
**Decided:** the submission form moves off `/signed-in/` to its own page,
`/submit/`, and gains a second way in beside the twenty fields: a copy button
for the prompt `artifacts/agent_handoff.py` already builds, and a box to paste
back what a coding agent produced. **`prompt()` is generated into the build.
`parse()` stays in Python and runs when the author pulls.** Pasting and filling
fields at once is refused and neither wins.
**Why:** the mechanism was finished and reachable only from a loopback form on
127.0.0.1, which is to say only by the author. Every field on it is something an
agent sitting in the checkout where the extraction happened can read off the
author's own scripts, and the people this registry is for mostly have one.

### The split that makes it cost nothing

`prompt(observed)` is a pure function of the spec list and the values this
corpus holds, so it is built during `make site` by `artifacts/intake.py prompt`
and written to `astro/src/data/agent-prompt.json`, which the page imports.
`astro/src/data/controlbun.json` is the precedent and the argument is the same:
a second copy of a document that changes whenever a field does is a copy that
goes stale, and the failure would be silent. An agent answering last month's
prompt, a parser refusing a field the reader was never asked for.

`tests/test_submit_page.py` asserts the text in the built page is exactly
`agent_handoff.prompt(suggestions(conn))` for this corpus, and that the page
source carries no second copy of it.

### The parser does not cross, and what that costs

`parse()` is several hundred lines of liberal-in strict-out recovery across
markdown fences, preamble, bold keys, bullets, blockquote markers, typographic
quotes and trailing commentary, refusing by name rather than guessing. **None of
it is ported and no part of it is approximated in the page**, not even a shallow
check that the markers are there. Two parsers that drift is the failure this
repository keeps catching, and the drift would be worst exactly where it
matters: a paste that passed in a browser and refused on the author's machine.

So the page posts the raw text and `agent_handoff.parse` runs at pull time, on
the machine that reads the bytes, beside the one implementation of everything
else that reads them.

**The cost is real and the page says it without softening.** A mistake in a
paste is not found as somebody types, the way a mistake in a field is. It is
found when the author pulls the row in, and the refusal reaches the submitter by
mail. `tests/test_submit_page.py` fails the build if that sentence leaves the
page.

### What lands in `record`, for each of the two routes

`schema/supabase/001_pending_submission.sql` is untouched: `record` is `jsonb`
and validates nothing, for the reason it already gives.

- `controlbun.registry/link-submission@1`, unchanged. The fields, the pin, the
  declared absences, and the browser's own copy of the subject and the handle.
- `controlbun.registry/agent-paste@1`, new. `pasted`, which is the text exactly
  as it arrived including the agent's prose around the block, plus the same
  three identity fields and `submitted_at`. Nothing is extracted from it in the
  browser, which is the property rather than an omission.

`artifacts/intake.py` reads both. `SHAPES` is the enumeration, with a sentence
per entry saying what that shape is, and a shape with no reader is still refused
with both names in the message rather than with a statement that the shape is
illegitimate.

### Pasting and filling at once

Refused, and neither is preferred. That is the rule `insert` already applies
where one field carries both a value and a reason for having none: resolving it
drops one of somebody's two statements while the record still reads correct to
whoever wrote it. Two accounts of a whole submission is the same thing one
object up. `chosenRoute` refuses it in the browser, naming what is filled in as
well as the paste, and `take` refuses it again on the author's machine for a
record that arrives carrying both.

The upload offer belongs to the field route, because it fills three fields in.
An absence typed into the absences box counts as filling fields in too, since an
absence is a positive statement about a field; an agent writes its own on the
`not-found:` lines the prompt asks for.

### The stamped author outranks the one in the paste

A paste carries an `author:` line, because the prompt asks for one and an agent
reading its author's files can answer it. The row's handle came through the
insert policy out of a verified session. The stamped one is what the row
records, and the disagreement is printed rather than swallowed, which is what
`stamped` already does for the structured route and for the same reason.

### `/submit/` is its own page

Taken with this rather than after it. The bar's **Add artifact** pointed at
`/signed-in/` while the form lived there, so pressing it during a return leg
reloaded the page and discarded the exchange in progress. That was recorded as a
papercut when the bar shipped and the split is the real fix. `/signed-in/` keeps
the redirect, the reading of what the provider said, the capture download and
the namespace explanation; `/submit/` takes the fields, the absences, the upload
offer and the handoff.

**It needs no console change.** The upload offer's second authorization lands on
the redirect URL the identity service already knows, `/signed-in/`, and that
page relays the code to whichever window opened it and closes. The exchange
happens in the window that holds the verifier, which is `/submit/`. Adding a
second allowed redirect URL was the alternative and would have been a change
only the account holder can make.

**The session moved to `astro/src/lib/held.mjs`.** Two pages restore, renew and
drop one now, and a copy per page is two sets of rules for one key. The property
was never "one page writes it", it was **one function writes it**, and that
function takes what the token endpoint answered rather than a record, so no
caller can hand it an object it assembled. `tests/test_nav_account.py` and
`tests/test_signed_in_page.py` were repointed at the module and say in their own
docstrings what they used to read and why.

### What this makes impossible to express

A paste checked before it is sent. Somebody who pastes a reply missing the
`hook_point` line finds out when the author writes back, not in the browser, and
there is no arrangement that gives them both that and one parser.

A submission built half one way and half the other: somebody who has a pin from
the upload offer and a paste for everything else has to clear one of them. That
is a real shape and it is refused rather than merged, because merging means
deciding which account of a field is the one they meant.

And a page that both finishes a sign-in and takes a submission, which is what
the split gives up. The cost is one more navigation for somebody who has just
signed in, and the link is on the page they land on.

### The invariant this added

Added to `CLAUDE.md`: text a page hands a reader to run elsewhere is generated
from the code that reads the answer, and a test pins the built page to that
function. What made this worth writing down is that it is not a rule about
prompts. It is the same rule as "one thing in this project reads bytes",
applied to a document: the thing that produces a format and the thing that
consumes it are one source, or they drift.
