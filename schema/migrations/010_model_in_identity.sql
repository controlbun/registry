-- 010_model_in_identity.sql
--
-- `model_id` moves onto the submission and into its primary key. A submission is
-- identified by `(author, model_id, label, version)` and its reference form is
--
--     soham/allenai/Olmo-3-1125-32B/pro-human@meandiff
--
-- Premise, restated because a premise stated in one migration gets violated in
-- every other one: the registry never designates; consumers pin, visibly. This
-- migration widens an identity. It does not add a filter, a facet or an ordering,
-- and nothing below may be read as the registry saying which model's directions
-- count. The same label on two models is two submissions and both stand, exactly
-- as two authors on one label are two submissions and both stand.
--
-- **Why the model belongs in the key rather than hanging off it.** One author
-- holds one label on several models and those are different artifacts, not one
-- artifact with an attribute. `soham/allenai/Olmo-3-1125-32B/pro-human@v` and
-- `soham/Qwen/Qwen3-8B/trauma@v` both have to exist, and under the old key the
-- second take on a label the author already held collided with the first. The old
-- key made "one author, one label, one version" a fact about the world, and it
-- never was: `BRIEF.md` has said since the first draft that a vector is a tensor
-- in one model's residual basis, so a submission that does not name the model in
-- its identity is not identified.
--
-- **What this makes impossible to express, asked before the constraint went in.**
-- One submission whose artifact spans several models. That shape was already
-- unwritable: `intervention.model_id` is NOT NULL and singular, so a submission
-- claiming two models was two intervention rows sharing one key with no way to
-- tell which recipe, pin or support card was about which. What is lost is a
-- hypothetical, and what is gained is that the cross-model case stops being a
-- collision. A recipe that fans out to several models is still expressible: it is
-- one recipe published as several submissions, which is what fanning out is.
--
-- `model_id` is an open string and nothing here validates its shape. A slash is
-- not required: `gpt2` and `bert-base-uncased` are single-segment model ids and a
-- schema that insisted on a distributor would refuse them. Parsing recovers the
-- model as everything between the first segment and the last rather than by
-- counting segments, so the identity carries any depth.
--
-- SQLite cannot add a column to a primary key in place, so five tables are
-- rebuilt: `submission`, and the four that reference it. Column lists and order
-- are the current ones with `model_id` inserted after `author`, which is where
-- the reference form reads it.
--
-- **Existing rows carry their model across rather than being given one.** Every
-- submission in this corpus has exactly one intervention and that intervention has
-- exactly one `model_id`, so the value is read off the artifact that already holds
-- it and nothing is invented. That premise is checked below rather than trusted:
-- `_010_guard` fails the migration if the rebuilt table does not hold exactly as
-- many rows as the old one, which is what a submission with no intervention, or
-- with two on different models, would produce. A migration that quietly dropped
-- somebody's submission because it had no artifact attached is the failure mode
-- this is here to make loud.

PRAGMA foreign_keys = OFF;

CREATE TABLE submission_new (
    author              TEXT    NOT NULL,
    -- The model the activations were read out of, as the full distributor-and-name
    -- string the extraction loaded: `allenai/Olmo-3-1125-32B`, `Qwen/Qwen3-8B`,
    -- `meta-llama/Llama-3.3-70B-Instruct`. Open, unvalidated, and part of the key
    -- rather than a property of it. Base and instruct are different models, so
    -- they are different submissions.
    model_id            TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    definition          TEXT    NOT NULL,
    created_at          TEXT    NOT NULL,
    -- Forward link when the author supersedes this version. Within one model:
    -- a take on another model is not a revision of this one, it is another
    -- submission, and a chain that crossed models would be the schema asserting
    -- that one model's artifact replaces another's.
    superseded_by       TEXT,
    is_synthetic        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (author, model_id, label, version)
);

INSERT INTO submission_new (author, model_id, label, version, definition,
                            created_at, superseded_by, is_synthetic)
SELECT s.author, i.model_id, s.label, s.version, s.definition,
       s.created_at, s.superseded_by, s.is_synthetic
FROM submission s
JOIN intervention i
  ON i.author = s.author AND i.label = s.label AND i.version = s.version;

-- The check the paragraph above promises, as a statement that fails the build
-- rather than a sentence that hopes. A CHECK constraint is the only thing
-- `executescript` will raise on, so the guard is a table that cannot hold a zero.
CREATE TABLE _010_guard (ok INTEGER NOT NULL CHECK (ok = 1));
INSERT INTO _010_guard (ok) SELECT CASE
    WHEN (SELECT count(*) FROM submission_new) = (SELECT count(*) FROM submission)
    THEN 1 ELSE 0 END;
DROP TABLE _010_guard;

DROP TABLE submission;
ALTER TABLE submission_new RENAME TO submission;

-- The four tables that reference a submission. Each gains `model_id` after
-- `author` and points its foreign key at all four columns.

CREATE TABLE intervention_new (
    id                  TEXT    PRIMARY KEY,
    author              TEXT    NOT NULL,
    model_id            TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    kind                TEXT    NOT NULL,
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
    artifact_sha256     TEXT,
    artifact_host       TEXT,
    artifact_url_template TEXT,
    served_host         TEXT,
    served_url_template TEXT,
    FOREIGN KEY (author, model_id, label, version)
        REFERENCES submission (author, model_id, label, version)
);

INSERT INTO intervention_new SELECT
    id, author, model_id, label, version, kind, model_revision, layer,
    layer_convention, hook_point, chat_template_hash, shape, dtype, l2_norm,
    activation_norm, coeff_low, coeff_high, steering_position, license_status,
    artifact_repo, artifact_commit, artifact_path, is_synthetic,
    served_repo, served_commit, artifact_sha256, artifact_host,
    artifact_url_template, served_host, served_url_template
FROM intervention;

DROP TABLE intervention;
ALTER TABLE intervention_new RENAME TO intervention;

CREATE TABLE recipe_new (
    id                  TEXT    PRIMARY KEY,
    author              TEXT    NOT NULL,
    model_id            TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    profile             TEXT    NOT NULL,
    payload_json        TEXT    NOT NULL,
    entrypoint_library  TEXT,
    entrypoint_version  TEXT,
    container_digest    TEXT,
    theory              TEXT,
    FOREIGN KEY (author, model_id, label, version)
        REFERENCES submission (author, model_id, label, version)
);

INSERT INTO recipe_new
SELECT r.id, r.author, s.model_id, r.label, r.version, r.profile, r.payload_json,
       r.entrypoint_library, r.entrypoint_version, r.container_digest, r.theory
FROM recipe r
JOIN submission s
  ON s.author = r.author AND s.label = r.label AND s.version = r.version;

DROP TABLE recipe;
ALTER TABLE recipe_new RENAME TO recipe;

CREATE TABLE pin_new (
    id                  TEXT    PRIMARY KEY,
    pinned_by           TEXT    NOT NULL,
    pinned_at           TEXT    NOT NULL,
    purpose             TEXT    NOT NULL,
    author              TEXT    NOT NULL,
    model_id            TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    -- JSON array of the alternatives that were considered and passed over, in the
    -- same reference form as the target. A pin with no alternatives recorded is
    -- not contestable, and a pin whose alternatives do not name their models is
    -- claiming a choice was made across a field it was not made across.
    --
    -- **Carried across verbatim and not rewritten.** This is what the consumer
    -- wrote down about their own choice, and a migration that expanded each
    -- string into a four-part reference would be inferring which model they had
    -- in mind and recording the inference in their words. The seeders write the
    -- four-part form, so the corpus this registry rebuilds carries it; a row from
    -- an older database keeps the reference its author typed, which is a shorter
    -- reference and not a false one.
    alternatives_json   TEXT    NOT NULL,
    rationale           TEXT,
    FOREIGN KEY (author, model_id, label, version)
        REFERENCES submission (author, model_id, label, version)
);

INSERT INTO pin_new
SELECT p.id, p.pinned_by, p.pinned_at, p.purpose, p.author, s.model_id, p.label,
       p.version, p.alternatives_json, p.rationale
FROM pin p
JOIN submission s
  ON s.author = p.author AND s.label = p.label AND s.version = p.version;

DROP TABLE pin;
ALTER TABLE pin_new RENAME TO pin;

-- 003's table, which carries the same foreign key and was not named in 001. Usage
-- is model-specific for the same reason it is version-specific: a report against
-- one model's artifact says nothing about another model's.
CREATE TABLE support_card_new (
    id                  TEXT    PRIMARY KEY,
    author              TEXT    NOT NULL,
    model_id            TEXT    NOT NULL,
    label               TEXT    NOT NULL,
    version             TEXT    NOT NULL,
    reporter            TEXT    NOT NULL,
    reported_at         TEXT    NOT NULL,
    repo                TEXT,
    repo_commit         TEXT,
    purpose             TEXT    NOT NULL,
    expected            TEXT    NOT NULL,
    observed            TEXT,   -- eval-result
    predictability      TEXT,   -- eval-result
    deviations          TEXT,   -- eval-result
    author_response     TEXT,   -- eval-result
    is_synthetic        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (author, model_id, label, version)
        REFERENCES submission (author, model_id, label, version)
);

INSERT INTO support_card_new
SELECT c.id, c.author, s.model_id, c.label, c.version, c.reporter, c.reported_at,
       c.repo, c.repo_commit, c.purpose, c.expected, c.observed, c.predictability,
       c.deviations, c.author_response, c.is_synthetic
FROM support_card c
JOIN submission s
  ON s.author = c.author AND s.label = c.label AND s.version = c.version;

DROP TABLE support_card;
ALTER TABLE support_card_new RENAME TO support_card;

-- Deliberately untouched: `label_relation`. `interprets:` and
-- `distinguishes-from:` are pointers between labels, and a bare label is a view
-- across claimants owned by nobody, so a relation is not obviously a statement
-- about one model's artifact. Whether a relation is model-scoped is a real
-- question and adding the column here would have answered it by accident. Raised
-- rather than decided; see DECISIONS.md.

PRAGMA foreign_keys = ON;
