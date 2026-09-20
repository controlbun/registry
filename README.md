# registry

A registry of activation-steering artifacts.

> **Status 2026-09-20.** Live. The site is at
> [controlbun.com](https://controlbun.com) and is built from this repository.

Ten people extracting `kindness` with different contrast data, different theories
of the trait and different ideas about what could be confounding it is the
content here, not a duplication problem. The registry holds all of them side by
side and makes the disagreement legible. It does not pick a winner, and nothing
in it designates one submission as the right one for a label. Consumers pin
`author/model_id/label@version` for their own purposes, visibly, and a pin is a
choice somebody made rather than an answer the registry gave.

## What is in it today

Five submissions, all real, all one author's own directions. Two labels, one
kind, two model ids. **No label has more than one claimant**, so the plurality
this exists for is a mechanism here and not yet something on display. That is a
fact about a new registry rather than a gap being papered over, and the site says
so in its own words.

Nothing in the corpus is fabricated. The shapes the tests need and the corpus
does not have, two people disagreeing on one label, an attack, an uninterpretable
score, live in `tests/probe.py` and never reach the site.

## Build it and check it

Python 3.13 or newer, and Node for the site.

```
python3 -m venv .venv && .venv/bin/pip install -e .
make verify
```

`make verify` is the whole gate: the invariant scans, a site build, a dependency
license audit, the test suite, an internal link check, the falsifier, and a
binding check on the notarized manifests. Nothing on GitHub builds anything, and
that is deliberate. Pages serves a locally built `astro/dist` from a branch, so
what a reader gets is the artifact that passed this gate on a machine rather than
whatever a runner produced from the same source.

```
make hooks    # wires the gate to pre-push, so it is not optional
make serve    # preview the built site
```

The falsifier re-derives every number the site publishes from the artifacts
themselves. If a page states a figure that does not trace to bytes in this
repository, `make verify` fails.

## The documents

Every document here opens with a status block saying whether it still instructs,
and `tests/test_doc_status.py` fails the build if one does not.

| | |
|---|---|
| `DECISIONS.md` | Authoritative. Superseded entries are kept and marked; check for a `**Superseded by:**` or `**Amended by:**` line before acting on one. |
| `CLAUDE.md` | The working agreement, and the premise most likely to be eroded by accident. |
| `BRIEF.md` | The original design direction. Seed, not specification. |
| `WHAT-IT-DOES.md` | What the running system does today, each claim with the check that produced it. |
| `VALIDATION.md` | Whether a direction is the thing its author says it is. Open, deliberately. |
| `CONTEXT.md` | Upstream project state and prior art, dated. |
| `V2.md` | The contribution plan. Partly overtaken. |
| `V1.md`, `GO-LIVE.md` | Spent. The record of taking the site public, not instructions. |
| `minor_updates.md` | Dated small changes, and the history audits. |

`_attest/` holds OpenTimestamps proofs that date earlier states of the design in
the Bitcoin chain. They are notarized records of past document states rather than
a live check, so `shasum -c` against one is expected to disagree with the working
tree. Never regenerate one.

## Artifacts, and whose they are

A direction is a tensor in one model's residual basis at one layer, so it carries
no weights and cannot reconstruct any. The author's working position is that his
own directions are his own work, built against a model rather than derived from
it. That position is contested and nobody has litigated it; `NOTICE` and
`DECISIONS.md` 2026-09-19 carry it with the case against it.

A source model's license may still reach an artifact derived from it. Each
artifact records what its own author read, at what URL, on what date, in
`license_status`, and where bytes cannot be redistributed the registry points at
them rather than serving them. There is no list of model families this project
carries.

## License

Apache-2.0. See `LICENSE`, and `NOTICE` for what the license cannot settle.
