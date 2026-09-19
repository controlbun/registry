-- 009_namespace_claim.sql
--
-- An account bound to a namespace, on dated evidence, alongside the free string
-- that `author` has always been.
--
-- Premise, restated because a premise stated in one migration gets violated in
-- every other one: the registry never designates. That applies here three times
-- over. Once to who may hold a namespace, once to what counts as evidence for
-- holding it, and once to what a held namespace is worth, which is nothing.
--
-- **`author` stays a free namespace string and does not become an account.**
-- `V2.md` section 1 gives three cases that break the cheap version and all three
-- are live. Indexing the literature is deferred rather than reversed, and an
-- entry for somebody else's published direction has an author who never signed
-- up and may never. It is already false today: every row in this corpus was
-- hand-entered or is a fixture, so every author here has no account. And
-- evidence gets written about other people's work, so an attack card, an
-- independent evaluation and a support card all name an author who is not the
-- submitter. So claiming is a separate object, and the one thing it must not
-- become is a condition on publishing.
--
-- **Unclaimed is the ordinary state, not a gap.** Nothing in this migration is
-- reachable from `submission` or `intervention`, no row anywhere needs a claim
-- to exist, and no claim is needed for anything to render. A namespace with no
-- row here is a namespace nobody has bound an account to, which is what every
-- namespace in this corpus is, and it renders the way 005, 007 and 008 render
-- their absences: as a fact with its own words, never as a finding.
--
-- **The binding is the provider's `sub`, never `preferred_username`.** Handles
-- are renameable on both providers this is written for. A claim bound to a
-- handle either breaks the day somebody renames or, worse, follows the handle to
-- whoever registers it next, which is squatting with the registry's help.
-- `subject` is the opaque stable id and is what the claim is keyed on. `handle`
-- is kept beside it as what the provider said at `claimed_at`, for display and
-- for nothing else: it is dated on arrival and is never looked up by.
--
-- **`provider` and the evidence `kind` are open strings.** Huggingface and
-- GitHub are the two being built against and neither is written down as a
-- permitted set. A CHECK here would say which identity providers a person is
-- allowed to be a person at, and a list of evidence kinds would say which ways
-- of establishing a claim are legitimate, which is the same object `kind`,
-- `hook_point`, `profile` and artifact file format already refuse to be.
--
-- Common providers, documented and enforced nowhere: `huggingface`, `github`.
-- Common evidence kinds, the same: `repo`, the repository an artifact was
-- published from; `doi`, a paper naming the author; `human-decision`, somebody
-- here deciding, with the reasoning recorded as the detail so it can be argued
-- with. A kind nobody has met stores and renders.
--
-- **A namespace takes more than one claimant, and that is deliberate.** The
-- unique constraint is on the account and the namespace together, so one account
-- claims one namespace once, and two accounts claiming `allenai` are two rows
-- that both stand. Making `namespace` unique would make the registry the thing
-- that decides a contested claim, which is designation arriving through an
-- index. Both render, both carry their evidence, and a reader adjudicates.
--
-- **Org membership is an observation with a date, never a stored fact.** People
-- join and leave organisations, so a membership written down once and read
-- forever is stale the moment it is wrong and carries no marker saying it might
-- be. `namespace_membership_observation` is append-only by construction:
-- `observed_at` is part of what makes a row unique, so looking again writes a
-- second row rather than overwriting the first, and there is no column anywhere
-- that says a person is currently a member of anything. What the page can say is
-- what was seen and when.
--
-- This is the rule the history audit and the attestations already follow. The
-- audit result is dated and re-run before a change in visibility; a proof
-- attests a file at a time. Neither is a permanent property of the thing.
--
-- `source` records which endpoint answered, because an observation with no
-- account of where it came from is a fact again.
--
-- **Nothing here is a measurement**, so no column carries an `-- eval-result`
-- marker, exactly as 004, 006, 007 and 008 say of their own.
--
-- **What this makes impossible to express.**
--
-- A ranking, a filter or a sort over claim status, anywhere. That is the point
-- rather than a side effect: nothing in this schema derives an order from
-- whether a namespace is claimed, no view ships a boolean the page could sort
-- on, and `tests/test_invariants.py` fails the build on one. So you cannot ask
-- this registry for the claimed submissions, cannot put claimed ones first, and
-- cannot see at a glance which of ten claimants of one label has an account
-- behind it. Every author in this corpus is unclaimed, including all five real
-- rows, so a claim column would be a column of absences read as a column of
-- deficiencies.
--
-- A claim that expires. There is no `valid_until` and no revocation, because
-- neither can be honest without somebody re-checking, and re-checking at read
-- time is the network call the falsifier is built to never need. A claim is
-- dated and a membership observation is dated; how old is too old is the
-- reader's question and the page gives them the date to answer it with.
--
-- A namespace held by a group rather than by an account. An HF org has a `sub`
-- of its own and could be recorded here as one, but the membership that makes a
-- person part of it is the observation table and stays separate, so "the org
-- holds this namespace" and "this person was in the org on a date" are two
-- statements and cannot be collapsed into one.
--
-- Evidence about somebody else's claim. `namespace_claim_evidence` hangs off the
-- claim it supports, so a second opinion about a claim has nowhere to go here.
-- That is the shape 008 left for the same reason: the object for disagreeing
-- with somebody's record is a separate authored one, and this schema does not
-- yet have its equivalent for claims. Left for whoever gets a contested claim,
-- with the shape of the problem written down rather than discovered later.

CREATE TABLE namespace_claim (
    id                  TEXT    PRIMARY KEY,
    -- The same free string `submission.author` carries. No foreign key: a
    -- namespace is a string anybody can publish under, a claim is a later and
    -- separate statement about it, and neither needs the other to exist.
    namespace           TEXT    NOT NULL,
    -- Open string. `huggingface` and `github` are what this is built against.
    -- Nothing enumerates the set and there is no CHECK.
    provider            TEXT    NOT NULL,
    -- The provider's `sub`. Opaque, stable, and the only thing the binding is
    -- made of.
    subject             TEXT    NOT NULL,
    -- `preferred_username` as the provider reported it at `claimed_at`. Display
    -- only. Renameable, therefore never an identity, therefore never a lookup
    -- key. NULL when the provider did not say.
    handle              TEXT,
    claimed_at          TEXT    NOT NULL,
    is_synthetic        INTEGER NOT NULL DEFAULT 0,
    -- One account claims one namespace once. `namespace` alone is deliberately
    -- not unique: see above.
    UNIQUE (provider, subject, namespace)
);

CREATE TABLE namespace_claim_evidence (
    claim_id            TEXT    NOT NULL REFERENCES namespace_claim (id),
    -- Open string. See above for the common values and for why there is no list.
    kind                TEXT    NOT NULL,
    -- The identifier or the words, depending on the kind: a repo, a DOI, or the
    -- reasoning behind a human decision. Rendered inside a `data-authored`
    -- region, per the 2026-09-19 decision, because the third kind is somebody's
    -- prose and can carry names, dates and figures.
    detail              TEXT    NOT NULL,
    recorded_at         TEXT    NOT NULL,
    PRIMARY KEY (claim_id, kind, detail)
);

CREATE TABLE namespace_membership_observation (
    id                  TEXT    PRIMARY KEY,
    -- The account, keyed the same way the claim is: provider plus subject.
    -- Attached to the account rather than to the claim, because what the
    -- provider said is true of the account whether or not it claimed anything.
    provider            TEXT    NOT NULL,
    subject             TEXT    NOT NULL,
    -- What the provider called the organisation.
    org                 TEXT    NOT NULL,
    -- `roleInOrg` where the provider gives one. NULL when it did not, which is
    -- an absence and not a lesser membership.
    role                TEXT,
    observed_at         TEXT    NOT NULL,
    -- Which endpoint answered. An observation with no account of where it came
    -- from is a stored fact again.
    source              TEXT    NOT NULL,
    is_synthetic        INTEGER NOT NULL DEFAULT 0,
    -- `observed_at` is in the key, so looking again appends rather than
    -- overwrites and the history stays readable. Nothing updates a row here.
    UNIQUE (provider, subject, org, observed_at)
);
