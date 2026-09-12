-- 001_init.sql
--
-- Premise, restated because a premise stated in one section gets violated in every
-- other one: the registry never designates; consumers pin, visibly. Nothing in this
-- schema may make one submission the answer for a label. A bare label is a query
-- across claimants, not a row that anyone owns.
--
-- Conventions this schema relies on, enforced by tests/test_invariants.py:
--   * Columns holding a measured result carry a trailing `-- eval-result` marker
--     and are never NOT NULL. Absence of a measurement is a state, not an error.
--   * No CHECK constraint enumerates permitted strings. Common values are
--     documented in comments; none are enforced.
--   * No UNIQUE constraint is on a label alone. Claimants per label are unlimited.

PRAGMA foreign_keys = ON;

-- A submission is one author's complete take. It is the primary object.
-- Immutable once written: a revision is a new row with a new version.
-- The bare label is deliberately not a table. `kindness` is a view across every
-- submission claiming it, owned by nobody.
CREATE TABLE submission (
    author              TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    -- The author's own theory of the trait, in prose. Load-bearing twice over: it
    -- feeds contrast-pair generation and it is the thing other authors disagree
    -- with. A submission without it is legible to nobody.
    definition          TEXT    NOT NULL,
    created_at          TEXT    NOT NULL,
    -- Forward link when the author supersedes this version. Never a backward
    -- deletion; superseded versions stay fetchable because pins target them.
    superseded_by       TEXT,
    is_synthetic        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (author, label, version)
);

-- Taxonomy emerges from claims rather than from a committee. `relation` is an open
-- string; `interprets` and `distinguishes-from` are the common values, not the
-- permitted ones.
CREATE TABLE label_relation (
    from_author         TEXT    NOT NULL,
    from_label          TEXT    NOT NULL,
    relation            TEXT    NOT NULL,
    to_author           TEXT    NOT NULL,
    to_label            TEXT    NOT NULL,
    note                TEXT,
    PRIMARY KEY (from_author, from_label, relation, to_author, to_label)
);

-- Where to hook, what to do there, and how to scale it. Named Intervention rather
-- than Vector so a probe, an SAE latent, a ReFT edit or a LoRA adaptor fits without
-- a rewrite.
CREATE TABLE intervention (
    id                  TEXT    PRIMARY KEY,
    author              TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    -- Open string. `direction`, `sae-latent`, `probe`, `reft`, `lora` are the ones
    -- with client support today, not the permitted set. An unrecognised kind is
    -- storable and displayable and simply has no apply path until someone writes one.
    kind                TEXT    NOT NULL,
    model_id            TEXT    NOT NULL,
    -- Base and instruct are different models; so is a different revision.
    model_revision      TEXT    NOT NULL,
    layer               INTEGER NOT NULL,
    -- Stated in the schema rather than the README because getting this wrong is
    -- silent. Common value: `block-0indexed`.
    layer_convention    TEXT    NOT NULL,
    -- Open string. `resid_pre`, `resid_post`, `mlp_out`, `attn_out` are common.
    hook_point          TEXT    NOT NULL,
    chat_template_hash  TEXT,
    shape               TEXT    NOT NULL,
    dtype               TEXT    NOT NULL,
    l2_norm             REAL,
    -- Lets a coefficient be expressed as a fraction of activation magnitude rather
    -- than a raw alpha that means nothing across models.
    activation_norm     REAL,
    coeff_low           REAL,
    coeff_high          REAL,
    steering_position   TEXT,
    -- Unresolved redistribution rights mean the artifact cannot be served.
    license_status      TEXT,
    -- safetensors always. Resolution is by commit SHA, not tag: a tag is movable by
    -- the repo owner, and immutability is what pins depend on.
    artifact_repo       TEXT,
    artifact_commit     TEXT,
    artifact_path       TEXT,
    is_synthetic        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (author, label, version) REFERENCES submission (author, label, version)
);

-- Optional. A published vector with no runnable procedure is still a submission,
-- and requiring a recipe would exclude exactly the historical artifacts worth
-- comparing against. Absence renders as absence.
CREATE TABLE recipe (
    id                  TEXT    PRIMARY KEY,
    author              TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    -- Namespaced and versioned, e.g. `soham/contrastive-v1`. Not chosen from a list,
    -- because there is no list. Outsiders publish profiles without asking.
    profile             TEXT    NOT NULL,
    payload_json        TEXT    NOT NULL,
    entrypoint_library  TEXT,
    entrypoint_version  TEXT,
    container_digest    TEXT,
    -- Recipe is the structural constraint. Two vectors indistinguishable by
    -- behavior are still distinguishable by provenance. See the identifiability
    -- section in VALIDATION.md.
    theory              TEXT,
    FOREIGN KEY (author, label, version) REFERENCES submission (author, label, version)
);

-- Provenance for anything that produced an artifact or a measurement.
CREATE TABLE run (
    id                  TEXT    PRIMARY KEY,
    who                 TEXT    NOT NULL,
    ran_at              TEXT    NOT NULL,
    hardware            TEXT,
    seed                INTEGER,
    git_sha             TEXT,
    container_digest    TEXT,
    logs_uri            TEXT
);

-- Authored, attachable, reusable. Pointing your eval at someone else's submission is
-- a first-class action and the main way comparability accumulates without anyone
-- mandating it.
CREATE TABLE eval_suite (
    id                  TEXT    PRIMARY KEY,
    author              TEXT    NOT NULL,
    name                TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    -- Pinned as weights with a revision, never an endpoint, or the score stops being
    -- reproducible the moment the provider updates the model.
    judge_model         TEXT,
    judge_revision      TEXT,
    rubric              TEXT,
    holdout_uri         TEXT,
    -- Author-declared, JSON array. Nobody dictates the list. The registry shows
    -- which axes you checked next to which axes someone else checked.
    confound_axes_json  TEXT,
    UNIQUE (author, name, version)
);

-- Every result column here is nullable and marked. A submission that did not measure
-- something says so; it cannot be made to look like it checked.
CREATE TABLE eval_report (
    id                  TEXT    PRIMARY KEY,
    eval_suite_id       TEXT    NOT NULL REFERENCES eval_suite (id),
    intervention_id     TEXT    NOT NULL REFERENCES intervention (id),
    run_id              TEXT    REFERENCES run (id),
    reported_at         TEXT    NOT NULL,
    trait_score         REAL,   -- eval-result
    -- Structurally paired with trait_score, not a collateral axis. A judged score
    -- displayed without one renders as uninterpretable rather than as a number:
    -- judge-human agreement ran 81% on coherent text against 42% on degenerate text.
    coherence_score     REAL,   -- eval-result
    transfer_score      REAL,   -- eval-result
    necessity_score     REAL,   -- eval-result
    confound_json       TEXT,   -- eval-result
    coeff_curve_json    TEXT,   -- eval-result
    notes               TEXT,   -- eval-result
    is_synthetic        INTEGER NOT NULL DEFAULT 0
);

-- The adversarial case of pointing an evaluation at someone else's submission. The
-- strongest evidence available, because it is the one kind the author did not choose.
CREATE TABLE attack (
    id                  TEXT    PRIMARY KEY,
    intervention_id     TEXT    NOT NULL REFERENCES intervention (id),
    attacker            TEXT    NOT NULL,
    attacked_at         TEXT    NOT NULL,
    -- Open string. Adversarial prompt set, alternative confound axis, held-out
    -- domain, ablation, transfer to an unlike template.
    method              TEXT    NOT NULL,
    run_id              TEXT    REFERENCES run (id),
    result_json         TEXT,   -- eval-result
    -- Genuinely contested rather than merely open. The attacker states theirs and
    -- the author states theirs and both are displayed. `no-finding`,
    -- `confirmed-limitation` and `invalidated` are common values; an attacker who
    -- wants a different word uses it. A registry-assigned disposition would be the
    -- registry adjudicating the dispute, which is the one thing it does not do.
    attacker_disposition TEXT,  -- eval-result
    author_disposition   TEXT,  -- eval-result
    author_response      TEXT,  -- eval-result
    -- The author's claim that a later version answers this, not a resolution.
    claimed_answered_by  TEXT,
    is_synthetic        INTEGER NOT NULL DEFAULT 0
);

-- A separate run of the same recipe by a different party. Reports its delta; it does
-- not award a pass, because setting the threshold would be the registry making the
-- judgment it is trying to hand to the reader.
CREATE TABLE reproduction (
    id                  TEXT    PRIMARY KEY,
    original_intervention_id TEXT NOT NULL REFERENCES intervention (id),
    reproduced_intervention_id TEXT NOT NULL REFERENCES intervention (id),
    reproducer          TEXT    NOT NULL,
    run_id              TEXT    REFERENCES run (id),
    -- Displayed as a fact and not as evidence of disagreement. Behaviorally
    -- indistinguishable vectors can sit far apart in angle: see the identifiability
    -- section in VALIDATION.md.
    cosine_to_original  REAL,   -- eval-result
    shared_eval_deltas_json TEXT, -- eval-result
    is_synthetic        INTEGER NOT NULL DEFAULT 0
);

-- A consumer freezing one submission for one purpose so its own numbers are
-- comparable. Ordinary experimental control, and the opposite of a designation only
-- as long as it stays visible. Who, when, and what it was picked over are all
-- required: an unattributed pin is a designation wearing a different hat.
CREATE TABLE pin (
    id                  TEXT    PRIMARY KEY,
    pinned_by           TEXT    NOT NULL,
    pinned_at           TEXT    NOT NULL,
    purpose             TEXT    NOT NULL,
    author              TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    -- JSON array of the author/label@version alternatives that were considered and
    -- passed over. A pin with no alternatives recorded is not contestable.
    alternatives_json   TEXT    NOT NULL,
    rationale           TEXT,
    FOREIGN KEY (author, label, version) REFERENCES submission (author, label, version)
);

-- Deliberately absent: any table for Comparison. It is derived and never authored,
-- so it is computed on demand. A comparisons table invites someone to write a row by
-- hand, and a hand-written comparison is an opinion with a schema.
--
-- Also deliberately absent: any ranking, score aggregate, or `is_official` flag.
