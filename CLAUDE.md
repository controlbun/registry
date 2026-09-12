# Working agreement

Project brief is in `BRIEF.md`. Settled decisions are in `DECISIONS.md`, which is
authoritative: do not contradict it, and add to it whenever something is decided.

**`DECISIONS.md` keeps superseded entries on purpose.** Check an entry for a
`**Superseded by:**` or `**Amended by:**` line before acting on it. Five carry one
today, and two of those read as live rules when they are not: transfer as a
required eval field, and ranking by precision and attack survival.

## The premise, which you will violate by accident

**Plurality is the product. The registry never designates; consumers pin,
visibly.** Ten people extracting `kindness` with different contrast data,
different theories of the trait and different confound axes is the content, not a
duplication problem. The registry makes disagreement legible. It does not resolve
it.

Separate the two senses of "canonical" before flagging anything:

- **Designating** is the registry asserting one entry is the right one. Rejected.
- **Pinning** is a consumer freezing `author/label@version` for one purpose so its
  own numbers are comparable. Ordinary experimental control. Fine, and required.
  Arena seasons pin. Model revisions and judge models pin.

A pin must be named, cited and contestable. If the pin is invisible or presented as
the answer rather than a choice, it has become a designation.

This is the one thing that gets eroded, and it never erodes in one move. It goes
one reasonable local improvement at a time: scores should be comparable, so fix
the confound axes on the trait; users need to pick one, so rank them; quality
varies, so require a validation field. Each defensible alone. Together they delete
the thesis. The erosion is a ratchet and does not reverse on its own.

Two drivers worth knowing so you can catch yourself:

- **Optimizing for the reader who wants one answer, against the contributor who
  wants a voice.** A registry is contributor-first. Every time reader convenience
  wins, the design centralizes.
- **Reasoning from precedent.** Precedent shows the mature curated version,
  because open systems look like failures early. For a novel object, absence of
  precedent is not evidence against it.

### Trip-wire vocabulary

If you are about to write any of these about this project, stop and flag it before
continuing: *official, authoritative, verified, approved, certified, curated,
required field, mandatory, minimum bar, quality gate, threshold, default sort, the
best, gold standard, ground truth, consensus, supported methods, allowed values,
one of.*

A closed enumeration is the same failure at field level: `method: a / b / c`
declares which ways of doing the thing are legitimate. Document common values,
enforce none, and make extension points namespaced profiles that outsiders can
publish without asking.

"Canonical" is not on the list because it is ambiguous. Apply the designate/pin
test instead: is the registry asserting correctness, or is a consumer freezing a
reference for its own measurement? The first is the failure. The second is fine as
long as it is visible.

Some of these will survive scrutiny. None should pass without it.

### The inverse question, asked every time

Before proposing any constraint, state what it makes impossible to express. Not
what it improves. A proposal that cannot name what plurality it removes has not
been thought through.

### Invariants, executable not aspirational

Prose principles get pattern-matched away. Checkable ones do not. The arena's
`_falsifier/verify.py` is the right precedent: extend the habit from numbers to
design. Tests that fail the build:

- No schema field is both an eval result and `NOT NULL`
- No endpoint returns a single "best" submission for a label, and a bare label
  never resolves to one artifact
- Every pin records who pinned it, when, and what alternatives existed
- No default sort key on any multi-submission view
- Any label namespace permits an unlimited number of claimants
- Absence of an eval renders as its own state, not as an error
- No closed enum on any user-supplied field. Document common values; reject none.
  Schema `CHECK` constraints listing permitted strings fail the build.
- A judged score renders with a coherence measure beside it or renders as
  uninterpretable, never as a bare number

Add one whenever a new invariant is settled. An invariant that is only in prose
is not an invariant.

### Premises live at the top of every document

A premise stated in one section will be violated in every other section. This is
observed, not hypothetical: the data model was rewritten for plurality and the
remaining six sections of `BRIEF.md` kept arguing for canonical traits, required
fields and ranking until they were audited. Restate the premise in each document's
opening, and when a premise changes, re-read the whole file rather than editing the
section that named it.

### The advocate role

The arena has `_advocate/`, which argues the opposing case. Keep the pattern here.
When a design decision is being settled, one pass should argue for the plural
reading explicitly, as a role rather than as a disclaimer.

## The object graph

`BRIEF.md` is authoritative on conflict. This is a map, not a spec.

- **Label**, namespaced `author/label`, free to claim, carries the author's own
  definition. A bare label is a computed view across claimants, owned by nobody.
  `interprets:` and `distinguishes-from:` pointers let taxonomy emerge from claims.
- **Submission**, the primary object. One author's complete take, versioned and
  immutable. `author/label@version` resolves to one frozen submission forever.
- **Recipe**, optional. Declares a namespaced versioned `profile` plus a payload,
  plus a pinned entrypoint and container digest. Never a method list.
- **Intervention**, the artifact. Open `kind`, model id plus revision, layer with
  stated indexing convention, open `hook_point`, chat template hash, norms,
  `license_status`. safetensors on ingest, always.
- **EvalSuite**, authored and pointable at anyone's submission. **Attack** is the
  adversarial case of the same mechanism, with attacker and author dispositions
  both displayed.
- **Comparison**, derived and never authored. The asymmetry in which confound axes
  each author checked is the informative cell.
- **Run** and **Reproduction**, provenance, and a reproduction reports its delta
  rather than a pass.

v0 is schema, storage on the HF Hub, Postgres metadata, Python client, Comparison,
views, and the ported falsifier. Build against fixtures labeled synthetic. Seed
with competing claimants on one label, not coverage across ten labels.

## Before writing any code

The data model and v0 scope are agreed enough to build against. Propose the
structure, wait for a yes, then build. Do not run a project initializer or create a
directory tree on your own initiative.

v0 accepts no uploads and serves nothing publicly. Do not build an upload route, a
public API, or bulk fetch, regardless of how much easier it would make testing. The
dual-use policy is a launch blocker and those features assume it exists.

## Working style

Write in my voice, not yours. For anything a human will judge me by, a README, a
launch post, docs, an email to a collaborator, do the structure and the accuracy
check and leave the prose to me. Lead with the result. Do not narrate process or
mistakes as a headline.

No em dashes. US spelling. State a rule once and I will not repeat it.

Push back where my framing is wrong. State the disagreement once with reasoning,
then execute my decision without relitigating it.

The v0 scope is fixed. Do not build toward v1 or v2. If you think v0 needs
something, say so and wait.

## Never fabricate numbers

This project's value proposition is trustworthy eval scores. Never invent a trait
score, coherence score, benchmark delta, cosine similarity or any metric, including
as example data, placeholder content or test fixtures. If a fixture needs numbers,
make them obviously synthetic and label them so in the file. Never put a
plausible-looking score in a README or a screenshot.

Same for empirical claims about methods. Cite the paper or say it is inference.
Secondhand claims from research summaries are not citations. If a claim matters,
read the source before it goes in a document.

## Verification over recall

Do not write code against remembered APIs. nnsight, TransformerLens, HF Hub and the
steering libraries move fast. Check the installed version's real signatures first
and show me what you checked.

Same for platform facts: Hub storage and LFS limits, rate limits, hosting costs,
model licenses. Run the command or fetch the page.

## Reproducibility

This is a tool about reproducibility, so it has to be exemplary. Pin every
dependency, record seeds, container digests and git SHAs, and keep every script
rerunnable from a clean checkout. Flag anything that is not reproducible rather
than shipping it.

## Legal, before it is expensive

A steering vector is derived from model weights, so redistributing one may be
constrained by that model's license. Check what each model's license permits for
derived artifacts before adding support for it. This constrains which families the
registry can carry at all, so it belongs in the schema discussion.

Check dependency licenses. Flag copyleft.

## Safety

Flag any feature that increases misuse surface, especially anything that makes
refusal-removal or malicious-persona artifacts easier to find, fetch in bulk, or
apply. The dual-use policy is a launch blocker. Do not build distribution features
that assume it before it exists.

Note the tension with the plurality premise and do not resolve it silently: open
contribution and misuse gating pull against each other. Where they conflict, raise
it rather than quietly choosing one.

## Manifests and timestamps

The manifests are a closed set. They are notarized records of past doc states, not
a live check, and nothing here is restamped as docs change. `shasum -c` against any
of them is expected to disagree with the working tree, and that disagreement is not
an error to fix. Git tracks the edits. The stamps exist to date the design.

**Every manifest name carries the date and time it was stamped.** A new snapshot
therefore never collides with an old one, `ots stamp` never hits its
refuse-to-overwrite, and no proof is ever discarded to make room for another.

What each one attests:

- `MANIFEST-a` and `-b`, earlier states of the design docs, anchored in Bitcoin
  blocks 966590 and 966592
- `MANIFEST-c`, an intermediate state, proof still pending
- `MANIFEST_FINAL_2026-09-11_2317`, all six docs as of that moment. Replaced the
  rolling `MANIFEST.sha256`, whose proof was pending and never anchored
- `MANIFEST_BRIEF_2026-09-11_2320`, `BRIEF.md` alone, so the brief can be handed to
  someone and dated without disclosing the rest of the set. Covers the
  pre-correction brief
- `MANIFEST_BRIEF_2026-09-12_0013`, the corrected `BRIEF.md`, after the Concept
  Sliders claims were verified and relabelled as convergent. This is the current
  disclosure document
- `MANIFEST_FINAL_2026-09-12_0013`, all six docs at that revision

Never regenerate any of them, and never rewrite one to make a checksum verify.
Rewriting an anchored proof's manifest orphans the proof, which is the only thing
it is for. `.ots.bak` files are the pre-upgrade proofs `ots upgrade` sets aside.

To date a new state, stamp a new pair under a new timestamped name rather than
touching an existing one, and leave it alone until `ots upgrade` anchors it.

```
ots info <manifest>.sha256.ots      # offline, shows what a proof attests
ots upgrade <manifest>.sha256.ots   # network, pending proofs only
```

## Repo

Private. Assume it may go public or gain collaborators later, so write nothing that
would need a history rewrite to remove. This includes personal, financial and
immigration details: keep them out of the repo entirely. Secrets in `.env` from the
first commit, `.env` gitignored before the first file exists.

Private working material goes in `_local/`, which is gitignored and never
committed. Do not copy anything out of it into a tracked file.

Not hosted on GitHub. No Actions, no GitHub remote, no `gh` workflows. The
falsifier and the invariant tests are enforced by a local gate instead: a
`make verify` target and a pre-push hook, both tracked so a collaborator
inherits them.
