"""The Python client.

`BRIEF.md` calls this the product and the website discovery, on the grounds that
if integration is friction nobody uses it.

Three things it refuses to do, because the registry refuses to do them:

- **A bare label does not resolve.** `load("kindness")` raises and points you at
  `compare("kindness")`. There is no canonical kindness to load, so a client that
  answered would be inventing one. This is the single behavior most likely to be
  "fixed" by a future convenience patch.
- **A short reference that names several submissions does not resolve either.**
  A submission is `author/model_id/label@version`. `author/label` is a
  convenience that works while the author holds that label on one model, and
  raises `Ambiguous` naming the models when they hold it on more. Same rule one
  level down: it is the caller's question, not the registry's.
- **Nothing is ordered by a measured result.** `compare()` returns claimants in
  storage order. A direction that also moves sentiment feels more effective in
  use, so ranking on measured effect favors the confounded one.
- **A missing measurement is `None`.** Never 0.0, never omitted from the object.
  You can ask whether something was measured; you cannot be handed a number that
  nobody produced. Where somebody wrote down why there is none, `absences`
  carries that sentence, because an absence with a reason and an absence nobody
  looked into are different states and only one of them tells you what to do.
- **A namespace does not report whether it is claimed.** `namespace()` hands
  back the claims and their evidence, and there is no boolean beside them,
  because a boolean is what a caller sorts on. Nothing in this client or in the
  site orders anything by claim status, and an unclaimed namespace is the state
  every namespace in this registry is in.

Deliberately not here: an nnsight or steering-vectors adapter. Neither library is
installed, and writing an integration against a remembered API signature is how
you ship something that looks right and does not run. `Contract` carries
everything such an adapter needs, and `Submission.vector()` hands over the tensor;
the adapter is a small function to write once the target library is pinned.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import artifact, db, fetch, ref as _ref

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "registry.db"


# A bare label handed to `load`. Defined in `controlbun.ref`, next to the split
# that raises it, and re-exported here unchanged: it was this module's name
# first, `registry/__init__.py` publishes it, and the tests catch
# `client.BareLabelError`. One class, two spellings of the same import.
BareLabelError = _ref.BareLabelError


# The bytes that arrived are not what the submission says they are. Defined in
# `artifact`, next to the comparison that raises it, and re-exported here
# unchanged: it was this module's name first, `registry/__init__.py` publishes
# it, and the tests catch `client.MismatchedArtifact`. One class, two spellings
# of the same import, so `except` and `isinstance` keep working either way.
MismatchedArtifact = artifact.MismatchedArtifact


class NotFound(LookupError):
    """Raised when a reference names something the registry does not hold."""


class Ambiguous(LookupError):
    """A short reference that names more than one submission.

    A sibling of `BareLabelError`, one level down. That one refuses to turn a bare
    label into an artifact because several authors claim it; this refuses to turn
    a short `author/label` into an artifact because the author's own corpus holds
    several answers to it. Two shapes of that, and both are the registry declining
    to pick:

    - **The author holds that label on several models.** An intervention is a
      tensor in one model's residual basis, so these are different artifacts and
      not versions of one. Name the model.
    - **The author has several current versions on that model**, none superseding
      the others. Pin a version.

    In both cases the caller's own reference is the fix, and the message names the
    alternatives so that writing it does not need a second lookup.
    """


@dataclass(frozen=True)
class Contract:
    """Everything needed to apply the artifact correctly.

    A vector applied at the wrong layer, hook point or chat template does not
    fail loudly; it appears not to work. That is why this travels with the tensor
    rather than living in a README.
    """

    model_id: str
    model_revision: str
    layer: int
    layer_convention: str
    hook_point: str
    chat_template_hash: str | None
    steering_position: str | None
    coeff_low: float | None
    coeff_high: float | None
    l2_norm: float | None
    activation_norm: float | None
    dtype: str
    shape: str
    # The digest of the file as published, header included. Here rather than
    # beside the fetch fields because it is the third thing `_check` compares,
    # next to shape and dtype, and because it is a published fact: anyone can
    # fetch the author's repo themselves and check the bytes without this client.
    # None when nobody recorded one, which is the normal state for an artifact
    # this registry points at rather than holds. See schema/migrations/006.
    artifact_sha256: str | None = None


@dataclass(frozen=True)
class Evidence:
    """What the author measured, and what they did not.

    `state` is `reportable`, `uninterpretable` or `absent`. A trait score with no
    coherence beside it is uninterpretable rather than a number, because judge
    agreement collapses on degenerate text.
    """

    state: str
    trait: float | None
    coherence: float | None
    transfer: float | None
    confounds: dict[str, float] | None
    curve: list[dict] | None
    axes_checked: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Submission:
    author: str
    # Part of what this submission is, not a property of it. The same label by
    # the same author on another model is another submission and both stand, the
    # same way two authors on one label are two submissions and both stand.
    #
    # `contract.model_id` holds the same string and is not redundant with this
    # one: the contract is what an application reads to apply the tensor
    # correctly, and this is what identifies the row. They are equal today
    # because the schema keys the intervention on the submission, and reading the
    # identity off the contract would make every caller that wants to name a
    # submission depend on it having an artifact attached.
    model_id: str
    label: str
    version: str
    definition: str
    contract: Contract
    evidence: Evidence
    recipe: dict | None
    attacks: list[dict]
    verifications: list[dict]
    is_synthetic: bool
    # Why a field on the contract has no value, keyed by the column it is
    # about. Empty for almost every submission, which is the ordinary state:
    # `contract.chat_template_hash is None` has always been answerable and this
    # is the other question, whether anybody said why. See
    # schema/migrations/008. Open on the field side, so a key here is whatever
    # the author accounted for and not a member of a set this client knows.
    absences: dict[str, str] = field(default_factory=dict)
    _artifact_path: str | None = None
    # Where the author published it, and where we serve a copy from, kept apart
    # on purpose. See 004_served_copy.sql: one pair of columns cannot express a
    # mirror that has drifted from its origin.
    #
    # The host and the template travel with each pair rather than being known by
    # this client, which is 007_any_host.sql: a row says which host its repo is
    # on and how that turns into a URL, so an artifact published somewhere
    # nobody here has met resolves without a code change. Both are None on every
    # row written before that column existed, which is a state and not a gap:
    # `fetch.from_repo` resolves those where they always resolved.
    _artifact_repo: str | None = None
    _artifact_commit: str | None = None
    _artifact_host: str | None = None
    _artifact_url_template: str | None = None
    _served_repo: str | None = None
    _served_commit: str | None = None
    _served_host: str | None = None
    _served_url_template: str | None = None

    @property
    def ref(self) -> str:
        """`author/model_id/label@version`, which resolves to this row forever."""
        return _ref.format(self.author, self.model_id, self.label, self.version)

    def vector(self) -> np.ndarray:
        """The tensor itself, as numpy.

        Fetched from wherever it lives, then checked against what this submission
        says it is. The check is not ceremony: the bytes may have come off a CDN
        at a commit we pinned months ago, and a digest, shape or dtype that
        disagrees with the record means the two have come apart. Loading it anyway
        would hand back a tensor that silently is not the one the page describes.
        """
        if not any((self._artifact_path, self._artifact_repo, self._served_repo)):
            raise NotFound(f"{self.ref} has no artifact attached")

        return self._check(fetch.resolve(
            artifact_path=self._artifact_path,
            served_repo=self._served_repo,
            served_commit=self._served_commit,
            served_host=self._served_host,
            served_url_template=self._served_url_template,
            artifact_repo=self._artifact_repo,
            artifact_commit=self._artifact_commit,
            artifact_host=self._artifact_host,
            artifact_url_template=self._artifact_url_template,
        ))

    def _check(self, blob: bytes) -> np.ndarray:
        """What arrived against what was recorded, then the tensor it holds.

        One line of work now, because the comparison moved to
        `controlbun.artifact` where the write path can reach it too. It used to be
        written out here, and a second copy of it appeared on the write path the
        moment there was one, which is how `pairwise` and the two `<head>`
        blocks went. What this method still owns is the question only the reader
        can answer: **which facts a fetch is entitled to insist on.**

        **Three of the four, and the digest is the one that can fail alone.**
        Shape and dtype are two facts and a great many tensors satisfy both: a
        substituted float32 [5120] passes them and is a different artifact. The
        digest identifies the file. Shape and dtype stay because they are what
        the record promises for an artifact whose digest nobody recorded, and
        because applying a wrong-shaped tensor does not fail loudly.

        **The L2 norm is claimed at write time and not here, deliberately.** A
        tolerance-bearing claim is worth enforcing where it is authored, because
        that is the moment it can still be corrected. Enforcing it again at read
        time, against a row that is frozen and immutable, makes a published
        artifact permanently unfetchable over a descriptive float that no
        application reads: coefficients scale against `activation_norm`, not
        this. An identifying claim is enforced everywhere; a descriptive one is
        enforced where it is written and re-derived by the falsifier after.

        **No recorded digest is a state, not a refusal.** Most artifacts are
        pointed at rather than held and nobody hashed their bytes. Refusing
        those would make the column a required field by the back door, which is
        the shape every quality gate in this project arrives in. `Claim` says
        that with a `None` rather than with a branch.
        """
        return artifact.confirmed(
            blob,
            artifact.Claim(
                shape=self.contract.shape,
                dtype=self.contract.dtype,
                sha256=self.contract.artifact_sha256,
            ),
            subject=self.ref,
        ).tensor

    def torch(self):
        """The same tensor as a torch tensor. Imported lazily so torch stays
        optional: most of what this client does needs numpy and nothing else."""
        import torch  # noqa: PLC0415

        return torch.from_numpy(self.vector())

    def coefficient(self, fraction: float) -> float:
        """A coefficient expressed as a fraction of activation magnitude.

        A raw alpha means nothing across models, which is why `activation_norm`
        is recorded. Returns None-free arithmetic or raises, rather than guessing
        a scale the author did not supply.
        """
        if self.contract.activation_norm is None:
            raise NotFound(
                f"{self.ref} records no activation norm, so a coefficient cannot be "
                "expressed as a fraction of activation magnitude. Use a raw alpha "
                "and know that it does not transfer across models."
            )
        return fraction * self.contract.activation_norm

    def measured(self, name: str) -> bool:
        """Whether a named measurement exists. Absence is a state you can ask
        about, not a zero you get handed."""
        return getattr(self.evidence, name, None) is not None


@dataclass(frozen=True)
class MembershipObservation:
    """What a provider said about an account's org membership, and when.

    Never a current fact. People join and leave organisations, so this is an
    observation with a date on it and the date is not decoration: it is what
    lets a reader decide whether the observation is recent enough for what they
    are doing. There is no `is_member` anywhere, here or in the schema.
    """

    org: str
    # `roleInOrg` where the provider gives one, None where it did not.
    role: str | None
    observed_at: str
    # Which endpoint answered.
    source: str


@dataclass(frozen=True)
class ClaimEvidence:
    """One reason offered for a claim, with the date it was recorded.

    `kind` is an open string. `repo`, `doi` and `human-decision` are what this
    is built against and nothing enumerates the set, so a kind this client has
    never seen arrives and reads out unchanged.
    """

    kind: str
    detail: str
    recorded_at: str


@dataclass(frozen=True)
class NamespaceClaim:
    """An account bound to a namespace, on dated evidence.

    Named in full rather than `Claim`, because `controlbun.artifact.Claim` is
    already what a writer asserts about a tensor and the two have nothing to do
    with each other.

    Bound to `subject`, the provider's opaque stable id. `handle` is what the
    provider called the account when the claim was made and may not be what it
    calls it now, so it is display and never a lookup key: handles are
    renameable, and a claim bound to one follows the handle to whoever
    registers it next.
    """

    namespace: str
    provider: str
    subject: str
    handle: str | None
    claimed_at: str
    evidence: list[ClaimEvidence]
    memberships: list[MembershipObservation]
    is_synthetic: bool

    @property
    def account(self) -> str:
        """The binding, written the way it should be quoted: provider and
        subject. Not the handle, which is what it was called on the day."""
        return f"{self.provider}:{self.subject}"


@dataclass(frozen=True)
class Namespace:
    """A namespace and whoever has claimed it, which is usually nobody.

    `claims` is empty for every namespace in this registry today, and that is
    the ordinary state rather than a missing one: `author` is a free string,
    every row here was written down rather than signed up for, and an unclaimed
    namespace says nothing at all about the work published under it.

    **There is no `is_claimed` and there will not be.** A boolean is the shape a
    caller sorts and filters on, and ordering anything by claim status is the
    designation this registry does not do. Read the claims; do not count them.
    """

    name: str
    claims: list[NamespaceClaim]


@dataclass(frozen=True)
class Comparison:
    label: str
    claimants: list[Submission]
    pairs: list[dict]

    def axes_nobody_checked(self) -> list[str]:
        """Axes exactly one claimant thought to check.

        The asymmetry is the informative cell: what one author checked and
        another did not is a thing no single submission page can show.
        """
        seen: dict[str, int] = {}
        for c in self.claimants:
            for axis in c.evidence.axes_checked:
                seen[axis] = seen.get(axis, 0) + 1
        return sorted(a for a, n in seen.items() if n < len(self.claimants))


def _connect(database: str | Path | None) -> sqlite3.Connection:
    return db.connect(database or DEFAULT_DB)


def _parse(ref: str) -> _ref.Parsed:
    """Split `author/model_id/label@version`, or the short form without a model.

    The rule is in `controlbun.ref` and not repeated here: first segment is the
    author, last is the label, everything between is the model. A bare label is
    refused at the split rather than later, because there is nothing downstream
    that could answer it.
    """
    return _ref.parse(ref)


def _build(conn: sqlite3.Connection, row: sqlite3.Row) -> Submission:
    from . import views  # noqa: PLC0415  (shared view logic, one source of truth)

    view = views.claimant_view(conn, row)
    iv = conn.execute(
        # Named rather than `*`, so adding a column to the schema does not
        # silently start travelling through the client. Widened in 004 to carry
        # both where the author published it and where we serve a copy from, in
        # 006 to carry the digest those bytes are checked against, and in 007 to
        # carry the host each pair is on and the template that turns it into a
        # URL. Keyed on all four identity columns since 010.
        "SELECT artifact_path, artifact_repo, artifact_commit,"
        " artifact_host, artifact_url_template,"
        " served_repo, served_commit, served_host, served_url_template,"
        " artifact_sha256 FROM intervention"
        " WHERE author=? AND model_id=? AND label=? AND version=?",
        (row["author"], row["model_id"], row["label"], row["version"]),
    ).fetchone()

    return Submission(
        author=view["author"],
        model_id=view["model_id"],
        label=view["label"],
        version=view["version"],
        definition=view["definition"],
        contract=Contract(
            model_id=view["model_id"],
            model_revision=view["model_revision"],
            layer=view["layer"],
            layer_convention=view["layer_convention"],
            hook_point=view["hook_point"],
            chat_template_hash=view["chat_template_hash"],
            steering_position=view["steering_position"],
            coeff_low=view["coeff_low"],
            coeff_high=view["coeff_high"],
            l2_norm=view["l2_norm"],
            activation_norm=view["activation_norm"],
            dtype=view["dtype"],
            shape=view["shape"],
            # Through `claimant_view` like every other contract field. It was
            # read off the row directly while nothing rendered it, and the page
            # renders it now: the digest is what lets a reader who fetched the
            # file by hand do the check this client does for them.
            artifact_sha256=view["artifact_sha256"],
        ),
        evidence=Evidence(
            state=view["score_state"],
            trait=view["trait_score"],
            coherence=view["coherence_score"],
            transfer=view["transfer_score"],
            confounds=view["confounds"],
            curve=view["coeff_curve"],
            axes_checked=view["axes"],
        ),
        recipe=view["recipe"],
        attacks=[dict(a) for a in view["attacks"]],
        verifications=view["verifications"],
        is_synthetic=view["is_synthetic"],
        absences=view["absences"],
        _artifact_path=iv["artifact_path"] if iv else None,
        _artifact_repo=iv["artifact_repo"] if iv else None,
        _artifact_commit=iv["artifact_commit"] if iv else None,
        _artifact_host=iv["artifact_host"] if iv else None,
        _artifact_url_template=iv["artifact_url_template"] if iv else None,
        _served_repo=iv["served_repo"] if iv else None,
        _served_commit=iv["served_commit"] if iv else None,
        _served_host=iv["served_host"] if iv else None,
        _served_url_template=iv["served_url_template"] if iv else None,
    )


def load(ref: str, *, database: str | Path | None = None) -> Submission:
    """Load one submission by `author/model_id/label@version`.

    Three parts of that reference may be left out and each one is answered
    differently.

    **The label alone does not resolve, ever.** Several people claim one word on
    several models and mean different things by it. That is refused at the split.

    **The model may be left out**, and `author/label` resolves when that author
    holds that label on exactly one model. When they hold it on more, this raises
    `Ambiguous` naming them, because an intervention is a tensor in one model's
    residual basis and picking between two would be the registry answering a
    question the caller has to answer. The short form is a convenience over the
    author's own corpus, not a default model.

    **The version may be left out**, and this resolves the head of that author's
    revision chain on that model: the version nothing supersedes. That is the
    author's own history, not the registry choosing between authors. Pin the
    version when the number needs to stay comparable later; a pinned reference
    resolves to the same frozen submission permanently.

    **An author with several current versions gets an error, not a pick.** This
    used to be `max(version_strings)`, which reads a revision order off text that
    does not carry one. On the corpus today it returns `meandiff` for
    `soham/pro-human`, the oldest of three, because `m` sorts last; and `v9` beats
    `v10` for anyone numbering past nine. Worse than wrong: the three are parallel
    takes by one author with no ordering between them at all, so any answer here
    is the registry designating one, which is the thing it does not do.
    `superseded_by` is the field that records a revision chain, so that is what
    gets read.
    """
    parsed = _parse(ref)
    owner, label, version = parsed.author, parsed.label, parsed.version
    conn = _connect(database)

    model = parsed.model
    if model is None:
        models = [
            r["model_id"] for r in conn.execute(
                "SELECT DISTINCT model_id FROM submission"
                " WHERE author=? AND label=? ORDER BY model_id",
                (owner, label),
            )
        ]
        if not models:
            raise NotFound(f"{ref!r} is not in this registry")
        if len(models) > 1:
            raise Ambiguous(
                f"{_ref.short(owner, label)} is published on {len(models)} "
                "models, and a direction extracted against one says nothing "
                "about another, so picking one would be this registry choosing "
                "on your behalf. Name the model you mean: "
                + ", ".join(
                    _ref.format(owner, m, label, version) if version
                    else f"{owner}/{m}/{label}"
                    for m in models
                )
            )
        model = models[0]

    if version is None:
        rows = list(conn.execute(
            "SELECT version, superseded_by FROM submission"
            " WHERE author=? AND model_id=? AND label=?",
            (owner, model, label),
        ))
        if not rows:
            raise NotFound(f"{ref!r} is not in this registry")

        heads = [r["version"] for r in rows if not r["superseded_by"]]
        if len(heads) == 1:
            version = heads[0]
        elif not heads:
            raise Ambiguous(
                f"every version of {owner}/{model}/{label} is superseded by "
                "another, so the revision chain is a cycle and there is no head. "
                "Pin one: "
                + ", ".join(
                    _ref.format(owner, model, label, r["version"]) for r in rows
                )
            )
        else:
            raise Ambiguous(
                f"{owner}/{model}/{label} has {len(heads)} current versions and "
                "nothing orders them, so picking one would be this registry "
                "choosing on your behalf. Pin the one you mean: "
                + ", ".join(
                    _ref.format(owner, model, label, v) for v in sorted(heads)
                )
            )

    row = conn.execute(
        "SELECT * FROM submission"
        " WHERE author=? AND model_id=? AND label=? AND version=?",
        (owner, model, label, version),
    ).fetchone()
    if row is None:
        raise NotFound(
            f"{_ref.format(owner, model, label, version)} is not in this registry"
        )
    return _build(conn, row)


def namespace(name: str, *, database: str | Path | None = None) -> Namespace:
    """Who has claimed a namespace, which for every namespace here is nobody.

    A namespace that nothing has been published under is not an error: the
    string is free, so asking about one returns an unclaimed namespace rather
    than raising. `NotFound` is for a reference to something that was supposed
    to resolve, and a namespace never was.

    Deliberately not reachable from `Submission`. A claim is a property of the
    namespace and not of the artifact, and putting it on the submission object
    would set it beside the evidence, where the next reader to want one number
    per submission reads it as part of the score. Ask about the namespace.
    """
    conn = _connect(database)
    from . import views  # noqa: PLC0415  (shared view logic, one source of truth)

    view = views.namespace_view(conn, name)
    return Namespace(
        name=view["namespace"],
        claims=[
            NamespaceClaim(
                namespace=c["namespace"],
                provider=c["provider"],
                subject=c["subject"],
                handle=c["handle"],
                claimed_at=c["claimed_at"],
                evidence=[ClaimEvidence(**e) for e in c["evidence"]],
                memberships=[MembershipObservation(**m) for m in c["memberships"]],
                is_synthetic=c["is_synthetic"],
            )
            for c in view["claims"]
        ],
    )


def claimants(label: str, *, database: str | Path | None = None) -> list[Submission]:
    """Everyone claiming a label, in storage order.

    Across models, deliberately. A bare label is a view across everybody claiming
    the word and nobody owns it, so narrowing this to one model would make the
    view a statement about which model the word belongs to. What the model does
    here is show up in each `Submission.ref`, where the reader can see that two
    claimants are not on the same basis.

    No ordering is applied here on purpose. Sorting is the caller's explicit
    choice, and no measured result may decide it.
    """
    conn = _connect(database)
    return [_build(conn, row) for row in db.claimants(conn, label)]


def compare(label: str, *, database: str | Path | None = None) -> Comparison:
    """The client-side version of the label view.

    Returns every claimant plus what can be computed between them. Angle
    similarity is reported as geometry and nothing more: behaviorally
    indistinguishable vectors can sit far apart in angle (arXiv:2602.06801), so a
    low value is not evidence that two authors reached different conclusions.
    """
    from .comparison import pairwise  # noqa: PLC0415

    conn = _connect(database)
    return Comparison(
        label=label,
        claimants=[_build(conn, row) for row in db.claimants(conn, label)],
        pairs=pairwise(conn, label),
    )
