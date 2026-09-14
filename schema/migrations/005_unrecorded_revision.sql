-- 005_unrecorded_revision.sql
--
-- `model_revision` becomes nullable.
--
-- 001 made it NOT NULL on a correct premise: base and instruct are different
-- models, so is a different revision, and a direction extracted against one does
-- not describe the other. That premise is unchanged. What is wrong is the
-- conclusion drawn from it.
--
-- NOT NULL does not produce a revision. It produces a string. An author who never
-- recorded which revision they read activations from types `unknown`, or `main`,
-- or pastes the sha the model has today, and the last of those is worse than
-- nothing: it is a false provenance claim that reads exactly like a true one.
--
-- The first real artifacts in this repository are the case. Three directions
-- extracted through NDIF in June 2026, whose own metadata carries an empty
-- `model_build` because the extraction script never captured what NDIF was
-- serving. The revision is not withheld. It was not recorded, and no string put
-- in that column would make it recorded.
--
-- This is the argument the schema already makes about recipes, in 001: requiring
-- one "would exclude exactly the historical artifacts worth comparing against".
-- Requiring a revision excludes every artifact published before anyone thought to
-- write one down, which is most of the ones worth holding.
--
-- What this does not do is relax the expectation. Absence renders as its own
-- state, the same as an unmeasured eval, so a reader sees "not recorded" against
-- a submission that did not record it and a sha against one that did. That is the
-- distinction a placeholder destroys. When there is an upload path it can refuse
-- a submission whose revision is resolvable and absent, which is enforcement in
-- the place that can tell the difference.
--
-- SQLite cannot drop a NOT NULL constraint in place, so the table is rebuilt.
-- Column list and order are 001's plus 004's two, unchanged otherwise.

PRAGMA foreign_keys = OFF;

CREATE TABLE intervention_new (
    id                  TEXT    PRIMARY KEY,
    author              TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    kind                TEXT    NOT NULL,
    model_id            TEXT    NOT NULL,
    -- Base and instruct are different models; so is a different revision. NULL
    -- means nobody recorded which, and is displayed as that rather than filled.
    model_revision      TEXT,
    layer               INTEGER NOT NULL,
    layer_convention    TEXT    NOT NULL,
    hook_point          TEXT    NOT NULL,
    chat_template_hash  TEXT,
    shape               TEXT    NOT NULL,
    dtype               TEXT    NOT NULL,
    l2_norm             REAL,
    activation_norm     REAL,
    coeff_low           REAL,
    coeff_high          REAL,
    steering_position   TEXT,
    license_status      TEXT,
    artifact_repo       TEXT,
    artifact_commit     TEXT,
    artifact_path       TEXT,
    is_synthetic        INTEGER NOT NULL DEFAULT 0,
    served_repo         TEXT,
    served_commit       TEXT,
    FOREIGN KEY (author, label, version) REFERENCES submission (author, label, version)
);

INSERT INTO intervention_new SELECT
    id, author, label, version, kind, model_id, model_revision, layer,
    layer_convention, hook_point, chat_template_hash, shape, dtype, l2_norm,
    activation_norm, coeff_low, coeff_high, steering_position, license_status,
    artifact_repo, artifact_commit, artifact_path, is_synthetic,
    served_repo, served_commit
FROM intervention;

DROP TABLE intervention;
ALTER TABLE intervention_new RENAME TO intervention;

PRAGMA foreign_keys = ON;
