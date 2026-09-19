# Everything in this directory is fabricated

**No number here is a measurement.** Nothing in this directory was produced by
running a model, extracting a direction, or scoring an output. It exists to
exercise the shape of the product: two claimants on one label who disagree, one
with a transfer result and one without, one carrying an attack against it.

Two conventions make that impossible to miss, by design rather than by trust:

- **Scores are repeated-digit decimals.** `0.1111`, `0.2222`, `0.7777`. Real
  measurements do not look like this. If you ever see one of these on a page that
  claims to show real data, the fixture loader has leaked into production.
- **Vectors are integer ramps**, `[1,2,3,...]` and its reverse, normalized. They
  are not directions in any model's residual basis, and the models and revisions
  they claim to belong to are placeholders that do not resolve.

**No identity here is a person.** The one namespace claim in this set names a
provider that does not exist, a subject string no provider issued, and an
organisation that does not resolve, on a hostname under the reserved `.invalid`
TLD. The only real identity in this project is recorded in `V2.md` and appears
nowhere in this directory.

Every fixture row also sets `is_synthetic = 1`, and every `.safetensors` file
carries `synthetic: "true"` plus a note in its embedded metadata, so the marker
survives the file being copied out of this directory and separated from this
README.

Cosine similarities computed between these vectors are real arithmetic over fake
inputs. They say nothing about any trait and must never be quoted as if they did.

## What the set exercises

| Fixture | Why it is here |
|---|---|
| `alice/kindness@v1` | Theory: kindness is warmth in affect. Has a transfer result. Checked sentiment and verbosity |
| `bob/kindness@v1` | Theory: kindness is costly help, explicitly not warmth. No transfer result. Checked refusal rate and formality |
| `carol`'s attack | Sentiment confound above a coefficient, with attacker and author disagreeing about what it means |
| The pin | A consumer freezing one claimant for one purpose, recording who, when, and what it was picked over |
| `alice`'s namespace claim | One claimed namespace against seven unclaimed ones, so the page has to render both and neither as a rank |

The two authors checked **different confound axes**. That asymmetry is the point:
it is the cell a Comparison can surface that no single submission can.
