# Everything in this directory is real

> **Status 2026-09-20.** Live. What is in this directory, what each recorded
> number means, and what none of them is evidence for.

This was the counterpart of `fixtures/SYNTHETIC.md`, which is gone: the whole
corpus is real now, per `DECISIONS.md` 2026-09-19. Every number attached to
these artifacts was produced by running a model. None is fabricated and none is
rounded for display.

Three directions on `soham/pro-human`, all from
`github.com/soham-padia/steering-arena` at commit `b8b4721`, all against
`allenai/Olmo-3-1125-32B` at layer 32, `resid_post`, last token, from the same 135
contrastive pairs. They differ only in the estimator: `meandiff`, `logistic`,
`lda`. Three submissions rather than one, because they are alternatives and not
components, and the interesting question about them is which one you would pick.

| File | Submission | sha256 of the source `.npz` |
|---|---|---|
| `soham/d_olmo3_v1.safetensors` | `soham/pro-human@meandiff` | `8406d93a…` |
| `soham/d_olmo3_logistic.safetensors` | `soham/pro-human@logistic` | `f8ae8523…` |
| `soham/d_olmo3_lda.safetensors` | `soham/pro-human@lda` | `09cc9991…` |

Filenames are the author's, kept as published, so a reader comparing our copy
against the origin is comparing the same name.

## Reproducing these files

```
.venv/bin/python artifacts/ingest_arena.py           # fetch, verify, convert
.venv/bin/python artifacts/ingest_arena.py --check   # offline, verify only
```

The `.npz` is verified against a recorded sha256 before it is read and the
`.safetensors` against a recorded sha256 after it is written, so a clean checkout
reproduces these byte for byte and `make verify` never needs the network.

Publishing them to the Hub, and pinning the commit so the client can fetch them
without a checkout, is `artifacts/PUBLISHING.md`.

`.npz` became safetensors on ingest because `numpy.load` has an `allow_pickle`
argument and a registry handing out other people's array files cannot ask a reader
to trust a flag default. All three load with `allow_pickle=False`, which the
ingest asserts rather than assumes, so nothing was lost in the conversion.

## What each number here means, and what it does not

Everything traces to a file in steering-arena at the pinned commit.

- **Transfer, 0.74 / 0.716 / 0.685.** `control_pairs.transfer_ratio` from each
  file's `.confound_audit.json`: the mean projection gap on six held-out control
  pairs over the mean gap on the training pairs. Not out-of-template transfer in
  the sense `VALIDATION.md` calls the strongest cheap criterion.
- **Confound cosines.** `confound_cosines` from the same file. Cosine of the
  shipped direction against a separately estimated confound direction, so low is
  good. `valence` and `length_independent` sit at the floor for all three and
  carry nothing. `approach` does not: 0.1223, 0.1697 and 0.1246, which makes
  logistic 39% more approach-contaminated than the other two on the one axis
  never orthogonalized out.
- **No trait score and no coherence score.** Neither exists. No judged behavioral
  evaluation was run on any of the three, so the page says not measured rather
  than showing a number from a different battery.
- **Held-out separation 1.000**, recorded in the eval note rather than as a score,
  because it is measured on a held-out split of the same 135 pairs the direction
  was fitted on. That is internal consistency. It is not evidence of transfer and
  is not a trait score.
- **Pairwise cosines 0.6965, 0.4261, 0.8318**, recomputed here from the shipped
  tensors and checked by the falsifier on every build.

### Two numbers deliberately not recorded as evidence

`mean_train_gap` is an identity, not a measurement: for a unit-norm `d` it equals
the norm of the class-mean difference times the cosine between `d` and that
difference, and predicting all three from one reproduces them to within 0.01%. It
is in the recipe payload, where it describes the extraction, and not in
`eval_report`, where it would read as a result.

`mean_control_gap` and `transfer_ratio` are one measurement stated twice: control
gap equals train gap times transfer ratio, to within 0.06%. Only the ratio is
recorded.

### The audit file's own cosines are not these cosines

Each `.confound_audit.json` for the logistic and lda files carries an
`estimator_agreement` block recording `cos_meandiff_lda = 0.3997`. This registry
publishes 0.4261 for the same pair. Both are correct for what they measure: the
audit re-fits the three estimators in-script and compares those raw fits, while
the shipped vectors have length and sentiment orthogonalized out. The registry
holds shipped vectors, so it computes and publishes what is in the tensors it
holds.

The meandiff file has no `estimator_agreement` block at all, and its
`"no confound flag tripped by these tests"` therefore records that the test never
ran rather than that it passed. That flag derives from the minimum of three
pairwise cosines among estimators and is identical regardless of which direction
is being audited, which is why the other two carry byte-identical blocks.

## Three fields that are null, and why each one is not a gap to fill

- **`model_revision`.** The extraction ran through NDIF against whatever it was
  serving, and the script recorded an empty `model_build`. Not withheld, not
  forgotten: never captured. `schema/migrations/005` made the column nullable for
  this, and the page renders "not recorded".
- **`chat_template_hash`.** No template was applied. Activations were read from
  raw concatenated text against a base checkpoint, which is a fact about the
  extraction and is stated in the recipe payload.
- **`activation_norm`.** The residual norm at layer 32 is measured, 50.97 in the
  layer sweep, but the bake-off scaled raw alphas against a unit vector rather
  than against it. Recording it in that column would assert the published
  coefficients are fractions of activation magnitude, and they are not. The number
  is in the recipe payload with the sentence that makes it readable.

## License

`allenai/Olmo-3-1125-32B` is apache-2.0, confirmed from the Hub model API on
2026-09-14 and again on 2026-09-19.

This section used to say a direction is derived from model weights and that
redistribution is therefore governed by the model's license rather than by who ran
the extraction. The author's position is the other one, recorded in `DECISIONS.md`
2026-09-19: a direction is his own work, built against a model. Either way these
four files redistribute cleanly, which is why the sentence was never load-bearing
here. Apache-2.0 reaches a derivative work only where the additions "represent, as
a whole, an original work of authorship", and excludes works that "remain
separable from" the Work; on the author's reading it never reaches at all. Both
roads end in the same place for OLMo-3, and that is a fact about OLMo-3 rather
than a general rule.

## What is not here

The steering bake-off. Twenty-four generations per direction across four prompts
and three alphas, of which 13, 13 and 9 respectively are byte-identical to the
unsteered baseline, with the sign convention not holding where they do differ.
That is a real result and the registry has nowhere to put it: it is neither a
score nor an attack, and `eval_report.notes` does not carry generations. It stays
in the arena repo until there is somewhere honest to put it.
