# Context

> **Status 2026-09-20.** Live. Upstream state and prior art, each fact carrying
> the date it was checked. Nothing here has been re-verified since the date on
> the claim itself, and this space moves fast.

Upstream project state and prior art. Facts verified as of 2026-09. Re-check
anything load-bearing before relying on it; this space moves fast.

---

## Upstream project

**Steering Arena.** `github.com/soham-padia/steering-arena`, deployed at
`sohampadianeu-steering-arena.hf.space`. Model served on NDIF via NNsight. Public
pro-human / anti-human activation-steering competition, non-commercial. A season
freezes `(model, layers, direction, probe set, scoring config)`.

**Season 3, live.** `allenai/Olmo-3-1125-32B`, base checkpoint, residual stream
5120-dim. Ranked score over layers 19/23/27/31; second score over 15/23/31/39 with
a per-layer direction, reporting the weakest layer. Direction `olmo3_s3_banded`.
Probes frozen in `data/probes/season3.json`. Season 2 was layer 24 on the same
model, Season 1 was Llama-3.1-8B layer 16; both archived, never mixed.

**How `d` is built.** 135 contrastive pairs across 15 human-values axes,
length-matched. Last-token residual read on `prompt+chosen` vs `prompt+rejected`,
per-pair difference, then a **logistic probe** over the differences rather than
difference-of-means (agrees with mass-mean at cos 0.738, LDA at 0.783). All 64
layers swept; held-out separation saturates at 1.00 everywhere so it cannot rank
layers, and the usable criterion is probe margin against a label-shuffled null,
peaking at layer 25. Orthogonalized against length, sentiment and
action-vs-inaction by Gram-Schmidt; the third sits at cos 0.004, below the
1/sqrt(5120) = 0.014 chance floor.

**Validation state.** Held-out separation 1.00. Control-pair transfer ratio 0.72.
Causal steering confirmed for +d against 8 norm-matched random directions under two
blind judges; the -d half was **withdrawn** 2026-08-27 as estimator-dependent. The
behavior study ran 8 arms over 50 prompts with zero probe overlap, blind in both
orders, two LLM judges plus a human; headline numbers were corrected downward
13-37% against a fixed baseline with no arm changing sign, and the `anti_top` arm
was withdrawn entirely.

**Two findings that constrain the registry**, both from that study:

- **Judge reliability is a property of the condition, not the judge.** 81%
  human agreement where text is coherent, 42% where it degenerates. One arm
  inverted sign. See `VALIDATION.md`.
- **Banding barely fixes single-layer gaming.** Rescoring all 618 Season 2 entries
  under Season 3's metric gave correlation 0.95 and the same optimized string still
  at rank 1. A minimum over a spread band separates; a mean over a narrow band does
  not. Cost: 13% margin reduction, published as a cost rather than an improvement.

**Self-identified open gap:** no random-direction control for the *search*. Until a
string is optimized against a random direction to a matched score and judged
identically, the attribution of behavior to `d` is not established.

Reusable assets: 135 seed pairs, 16 frozen probes, `data/directions/` with every
layer-sweep candidate and its confound audit, cached generations,
`_falsifier/verify.py` (181 checks, exits non-zero on drift), `_advocate/`.

Becoming an official lab competition with prize money, hosted at
`steering-arena.baulab.info`. Stays a separate project; the registry connects to it
as a dependency, with each season pinning one claimant and citing what it was
picked over. The registry's origin is an unresolved criticism of this project's own
frozen direction: see `BRIEF.md` and `VALIDATION.md`.

---

## Prior art and adjacent projects

**Neuronpedia.** SAE feature dictionaries, plus probes, concepts and transcoders.
OLMo 3 covered: Olmo 3 7B SAE by David Chanin (`16-res-matryoshka-65k`, May 2026),
Olmo 3 32B SAE by Bartosz Cywinski. Inference not enabled on the 7B model page.
Interop target, not a competitor. Also hosts AxBench (Stanford
NLP) and Goodfire's Llama 3.3 70B Instruct SAE.

**persona_vectors** (`safety-research/persona_vectors`). Automated pipeline from a
trait name plus natural-language description to a vector. Ships traits including
evil, sycophancy and hallucination for Qwen2.5-7B-Instruct. Closest existing thing
to the Recipe concept; worth reading before finalizing the Recipe schema.

**rotalabs/steering-vectors** on HF. Pre-extracted refusal, uncertainty,
tool_restraint and hierarchy vectors for Qwen3-8B, Mistral-7B and Gemma-2-9B, with
a `rotalabs-steer` client and CAA contrast-pair datasets.

**steering-vectors** library by David Chanin. CAA and representation-engineering
utilities for HF models.

**NDIF / NNsight.** Remote intervention execution on hosted models. The org also
has a unified interface across transformer architectures with standardized naming
and built-in interventions including activation steering, plus Workbench, a UI for
exploratory interpretability analysis. **Check this before finalizing the hook-point
and layer-indexing schema.** It may already define the contract, in which case adopt
it rather than inventing a parallel one.