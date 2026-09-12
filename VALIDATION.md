# Direction validity

The research core of this project. Not because one criterion has to be settled
before the registry can exist, which would contradict the plurality premise in
`BRIEF.md`, but for two narrower reasons:

- The schema has to be expressive enough to record any criterion an author might
  use, including ones not listed here.
- The seed submissions have to demonstrate criteria good enough that the registry
  is worth imitating. What gets seeded sets the norm, and norms are the only
  quality mechanism a non-curated registry has.

---

## The object under test

A direction `d` in a model's activation space, labeled with a trait name. The claim
attached to it is: *steering along `d` produces more of the trait this label names,
and not merely more of something correlated with it.*

**The arena's own `d` is the worked example.** This project began with the author
trying to attack it:

> idea came when i was thinking of critizing my pro human directing actually
> represents that direction and if i could reuse someone elses better pro human
> direction without the effort

That direction is in fact heavily audited: de-confounded against length, sentiment
and action-vs-inaction, held-out separation 1.00, control-pair transfer, causal
steering confirmed for +d against norm-matched random directions with the -d half
withdrawn. See `CONTEXT.md` for the full state.

The point is that **it is still not enough, and none of it transfers.** A thorough
audit does not produce certainty, it produces a well-documented single opinion.
There is no way to check it against another take on the same construct and no way
to adopt a better one without redoing every step. That is the gap: comparison and
reuse, not rigor.

**This is not what Steering Arena tests.** In the arena `d` is given and frozen,
and the search is over token sequences. SCORE 2 and SPEC test whether a *sequence*
generalizes or rides a token artifact. Neither says anything about whether `d`
itself means what its label claims. Sequence validity and direction validity are
separate problems. Do not let the arena's instruments imply coverage they do not
have.

---

## Failure modes for `d`

A mean-difference direction built from contrast pairs can encode any of these
instead of the named trait:

- **Sentiment.** The obvious one for `kindness`. Positive affect is the confound
  most likely to produce a direction that scores well and means nothing.
- **Verbosity / length.** Longer responses read as warmer to a judge.
- **Register and formality.** Politeness markers rather than kindness.
- **Lexical artifact.** A handful of tokens that appeared disproportionately in the
  positive half of the pairs.
- **Template artifact.** Whatever the contrast-pair prompt scaffold has in common,
  which generalizes to nothing outside that scaffold.
- **Prompt-bucket / condition artifact.** The direction may encode *which
  experimental condition the model is in* rather than the trait: trait-encouraging
  versus trait-discouraging system prompt. Reportedly conceded in the
  persona-vectors paper itself, that its correlations arise primarily from
  distinguishing prompt types. **Unverified secondhand, read the paper before
  relying on it.** If true it is the most important confound on this list, the
  hardest to notice, and the one most authors will miss in the same way.

The last three are the reason held-out judge scores are weak evidence. A holdout
drawn from the same generator and the same scaffold shares the artifact.

---

## A hard constraint before any criterion

**A judged score without a coherence measure beside it is uninterpretable.** Not
incomplete, uninterpretable. From the arena's behavior study: judge-human agreement
was 81% where the text held together and 42% where it degenerated, worse than
chance on a forced choice. The `anti_top` arm did not produce a small effect, it
**inverted** — the human rated the degraded side kinder 14 to 3, because empty text
reads as less unkind than a real opinion.

Consequences for the registry:

- Coherence is structurally paired with any judged score, not a collateral axis
  alongside sentiment and verbosity. A submission reporting a trait score with no
  coherence measure renders as uninterpretable rather than as a number.
- This is the one place the registry constrains rather than records, and it is
  defensible because it is a statement about instrument validity, not about which
  criterion is correct.
- It bites hardest at high coefficients, which is exactly where effect sizes look
  most impressive.

---

## Candidate criteria

Roughly weakest to strongest as evidence, but the ordering is an argument rather
than a finding, and a submission is free to use any subset or something absent
here. The registry records which were used; it does not require any of them.

1. **Held-out judge eval.** Trait score on questions not in the contrast pairs.
   Necessary, not close to sufficient. The author wrote both the pairs and the
   rubric, so this measures internal consistency.

2. **Confound audit.** Score the same generations on competing axes (sentiment,
   verbosity, formality) and report whether the trait score moves independently.
   Already implemented per candidate direction in the arena's `data/directions/`.
   Stronger, but it only rules out the confounds you thought to name.

3. **Out-of-template transfer.** Does `d` produce the trait on prompts
   structurally unlike the contrast pairs it came from? This is the criterion the
   Function Vectors work leaned on: function vectors triggered the task in
   zero-shot and natural-text settings that did not resemble the ICL contexts they
   were collected from (Todd et al., ICLR 2024). It directly attacks the template
   and lexical artifacts, which are the failure modes the other criteria miss.
   Strongest criterion available cheaply, so worth doing in every seed submission
   and worth surfacing prominently when a submission lacks it. Not required, since
   requiring it would mean the registry asserting a criterion.

4. **Necessity, not just sufficiency.** Addition shows `d` is sufficient to push
   the behavior. Ablating or projecting out `d` and showing the behavior degrades
   shows it is load-bearing. Causal mediation is the established tool. More
   expensive, much harder to fake.

5. **Cross-model recipe agreement.** Run one recipe on several models. The
   directions are not comparable as tensors, but the behavioral effects are. If
   the same recipe produces the trait in four models, the recipe encodes something
   real; if it works on one, suspect the model-specific artifact. Expensive today,
   since it means running the recipe several times; cheap if a fanout runner ever
   exists.

6. **Adversarial falsification.** A populated arena where many players reach high
   SCORE 1 while the behavior tapes show no corresponding change in output is
   evidence against `d`, not against the players. Crowdsourced falsification of a
   direction would be novel: existing persona-vector and SAE work validates against
   evals the authors wrote themselves. Not established. Open question, below.

---

## Convergent work, not a source: Concept Sliders

**Provenance, stated because it matters.** This project did not come from this line
of work. It came from the origin quote above: wanting to know whether the arena's
own pro-human direction represented what it claimed, and whether someone else's
better one could be reused without redoing the effort. The connection below was
noticed afterwards, while thinking about who to involve, and every claim in this
section was unverified secondhand until checked against the papers on 2026-09-12.
What follows is convergence with adjacent work in a different modality, not
derivation from it.

The closest thing to a solved version of this problem is in diffusion, not language.

- **Concept Sliders** (Gandikota, Materzynska, Zhou, Torralba, Bau; arXiv:2311.12092,
  ECCV 2024) trains LoRA adaptors as low-rank parameter directions for named
  concepts while explicitly minimizing interference with other attributes, and
  distributes pretrained sliders for download at `sliders.baulab.info`.
- **ESD** (Gandikota et al., arXiv:2303.07345, ICCV 2023) erases concepts from model
  weights and scores accuracy on the erased class alongside accuracy on untargeted
  classes, reporting the collateral damage rather than only the targeted success.

Two transferable lessons:

- **Report interference by default.** The erasing papers show the edit alongside its
  effect on untargeted concepts in the same figure. The registry equivalent is that
  an artifact page shows the trait score and the collateral axes together, with no
  way to display one without the other. Not a separate tab.
- **Precision is the claim, not magnitude.** Sliders are sold on *precise* control,
  not strong control. That is the right framing here too: a direction that moves the
  trait hard and everything else with it is a worse artifact than one that moves it
  modestly and nothing else. Whatever the headline number on an artifact page is, it
  should be a precision measure rather than an effect size.

Both are matters of what gets rendered, so they constrain the schema.

---

## Open questions to take to others

Each needs someone with relevant expertise rather than more reasoning from here.

- **Does adversarial prompt search constitute evidence about a direction's
  validity, or only about the search space?** If the arena's anti-correlation
  between score and observed behavior is admissible evidence, that is a new
  validation method and a paper. If it is not, the arena and the registry stay
  separate. This is the highest-value unresolved question in the project.

- **What can a Comparison compute across submissions that validated
  differently?** The hardest consequence of plurality. If author A ran a transfer
  test and author B ran an ablation, what statement can the registry make about the
  pair beyond cosine similarity? Candidates: run each author's eval against the
  other's submission, which is cheap and symmetric; or define a small set of
  registry-computed measures applied uniformly to every submission regardless of
  what its author did. The second is a canonical eval smuggled back in, so if it is
  the right answer that is worth knowing explicitly.

- **Does a non-curated registry need a floor at all?** Open registries have no
  quality gate and still produce usable ecosystems, mostly through norms set by
  early high-quality entries. Whether that works for evidential claims, as opposed
  to code that either runs or does not, is unresolved.

- **Does the Function Vectors transfer argument port from task vectors to trait
  vectors?** Tasks have checkable outputs. Traits are judged. The transfer test may
  weaken substantially when correctness is replaced by a rubric score.

- **What confounds are not on the list above?** The value of asking someone whose
  published work is about models appearing capable while relying on shallow
  heuristics is that they will name the ones not thought of.

- **What broke after Concept Sliders shipped?** The only post-release evidence
  available anywhere about distributing concept-control artifacts at scale. Which
  metadata turned out to be missing, what people applied wrong, whether anyone
  reused a slider on a model it was not trained for, and whether the `diffusers`
  integration mattered more than the demo. This answers v0 scoping questions
  directly. The deployment experience is not in any paper, though follow-up work on
  erasure side effects now exists (arXiv:2505.17013, arXiv:2508.15124), so the gap
  is operational rather than total.

---

## What this implies for the schema

Provisional, pending the answers above. The shift from earlier drafts: the schema
records evidence rather than demanding it.

- **Every criterion is an optional, separately typed field.** Transfer, confound
  audit, necessity, cross-model agreement each get their own slot so they can be
  added after publication without reprocessing, and so absence is visible.
- **Absence is rendered, not hidden.** A submission with no transfer result says so
  on its page. That is the substitute for a requirement: nobody is blocked, and
  nobody can look like they checked something they did not.
- **Confound axes are author-declared, not fixed by the label.** The Comparison
  surfaces the asymmetry between what each author checked. Fixing the axes on a
  canonical trait was the earlier design and it contradicted plurality.
- **Precision over magnitude in whatever is displayed first**, per the Concept
  Sliders lesson. A direction that moves the trait hard and everything else with it
  is worse than one that moves it modestly and nothing else.
- **Negative results are first-class.** A submission whose own evidence says the
  direction failed is a valid and useful submission. A registry that only holds
  successes is a marketing surface.