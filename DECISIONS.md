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

## 2026-09-11 AICR is the compute backend, not the host
**Decided:** Extraction and eval run on AICR. The web tier and artifact storage
live elsewhere: HF Hub for artifacts, small VPS for metadata and frontend.
**Why:** 24h batch limit, acceptable use scoped to institutional research,
snapshots with no off-site backup.

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
  constrains which families the registry can carry. Prior practice worth checking:
  low-rank adaptors derived from open image models have been redistributed
  permissively at scale for years.

## Open, not blocking

- **Name.** Undecided deliberately. Deferred until it is known whether this lives
  inside an existing ecosystem's naming conventions.
- **Whether comparable infrastructure already exists or is planned elsewhere.**
  Changes whether this is a layer on existing infrastructure or parallel to it.
  Worth resolving early; the single question that could save the most work.
- **Interop with existing feature indexes.** Accepting their features as a recipe
  profile, and linking out rather than duplicating.
- **Adversarial falsification as a validation method.** If a populated arena's
  score-versus-behavior gap is admissible evidence about a direction, that is novel
  and a paper. Unresolved, and the highest-upside open question.
- **Whether v0 stays single-model.** Superseded in practice: the schema is
  model-agnostic and v0 carries whatever the first real submissions run on. The
  arena runs Season 3 on Olmo-3-1125-32B.

- **Automatic direction discovery as a seeding method.** SliderSpace finds many
  interpretable composable directions from a single prompt without per-attribute
  supervision. If that ports to language-model residual directions, the registry
  seeds itself from a short trait list rather than one hand-built recipe at a time,
  which changes the cold-start answer. Speculative; do not build toward it.