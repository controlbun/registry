-- 003_support_card.sql
--
-- A support card: somebody used this artifact in their own work, pinned a
-- version, and reports whether it behaved the way the published contract said it
-- would.
--
-- This is not an evaluation and must not become one. An eval re-measures the
-- artifact against a benchmark. A support card reports applied use, which is the
-- only evidence in this schema that touches external validity: not "your number
-- reproduces" but "I used this for something real and it did what it claimed".
--
-- It is also the only evidence that tests the application contract. BRIEF.md's
-- third failure mode is silent misuse: a vector applied at the wrong layer, hook
-- point or chat template does not fail loudly, it appears not to work. Nothing
-- else here can tell us whether the layer, hook point, template hash and
-- coefficient range we publish are actually sufficient to use the thing. A
-- support card can, and `deviations` is where it does.
--
-- **Why this is not a star rating with prose.** DECISIONS.md rejected user
-- ratings because a direction that also moves sentiment and verbosity feels more
-- effective in use, since more is happening, while a well-isolated one feels
-- subtler. So satisfaction systematically favors the confounded artifact. The
-- defense is that a card records a prediction and an outcome rather than a
-- feeling: `expected` is what the contract said, `observed` is what happened, and
-- a card with no `expected` is an opinion rather than evidence.
--
-- Every result column is nullable and marked, like every other measured field
-- here. A usage report with nothing observed yet is a state, not an error.

CREATE TABLE support_card (
    id                  TEXT    PRIMARY KEY,
    -- Usage is version-specific. A report against @v1 says nothing about @v2, and
    -- resolving this to "the latest" would silently relabel someone's evidence.
    author              TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,

    -- Who used it, and where the work lives. A repo pinned by commit makes the
    -- report checkable; without it this is hearsay with a name attached.
    reporter            TEXT    NOT NULL,
    reported_at         TEXT    NOT NULL,
    repo                TEXT,
    repo_commit         TEXT,

    -- What they were doing. Open text: the point is applied use, and nobody can
    -- enumerate in advance what people will apply an intervention to.
    purpose             TEXT    NOT NULL,

    -- The prediction and the outcome. These are the pair that makes this evidence
    -- rather than a testimonial, which is why `expected` is required and the
    -- observation is not: you may report that you have not finished looking, but
    -- you may not report an outcome against no prediction.
    expected            TEXT    NOT NULL,
    observed            TEXT,   -- eval-result

    -- Did it behave as the contract said. Open string, because "predictably" is
    -- not binary: `as-documented`, `partial`, `not-as-documented` are common
    -- values and an author who needs a different word writes it.
    predictability      TEXT,   -- eval-result

    -- What they had to work out that the published metadata did not tell them.
    -- A defect report about our contract, and invisible everywhere else in this
    -- schema. "The layer index was off by one" belongs here.
    deviations          TEXT,   -- eval-result

    -- The author's reply, displayed beside the report and never in place of it,
    -- the same way an attack carries both dispositions.
    author_response     TEXT,   -- eval-result

    is_synthetic        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (author, label, version) REFERENCES submission (author, label, version)
);
