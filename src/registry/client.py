"""The Python client.

`BRIEF.md` calls this the product and the website discovery, on the grounds that
if integration is friction nobody uses it.

Three things it refuses to do, because the registry refuses to do them:

- **A bare label does not resolve.** `load("kindness")` raises and points you at
  `compare("kindness")`. There is no canonical kindness to load, so a client that
  answered would be inventing one. This is the single behavior most likely to be
  "fixed" by a future convenience patch.
- **Nothing is ordered by a measured result.** `compare()` returns claimants in
  storage order. A direction that also moves sentiment feels more effective in
  use, so ranking on measured effect favors the confounded one.
- **A missing measurement is `None`.** Never 0.0, never omitted from the object.
  You can ask whether something was measured; you cannot be handed a number that
  nobody produced.

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
from safetensors.numpy import load_file

from . import db

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "registry.db"


class BareLabelError(LookupError):
    """Raised when a bare label is handed to `load`."""


class NotFound(LookupError):
    """Raised when a reference names something the registry does not hold."""


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
    label: str
    version: str
    definition: str
    contract: Contract
    evidence: Evidence
    recipe: dict | None
    attacks: list[dict]
    verifications: list[dict]
    is_synthetic: bool
    _artifact_path: str | None = None

    @property
    def ref(self) -> str:
        return f"{self.author}/{self.label}@{self.version}"

    def vector(self) -> np.ndarray:
        """The tensor itself, as numpy."""
        if not self._artifact_path:
            raise NotFound(f"{self.ref} has no artifact attached")
        tensors = load_file(str(ROOT / self._artifact_path))
        return next(iter(tensors.values()))

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


def _parse(ref: str) -> tuple[str, str, str | None]:
    """Split `author/label@version`. A bare label is refused here, not later."""
    if "/" not in ref:
        raise BareLabelError(
            f"{ref!r} is a bare label and does not resolve to an artifact. "
            f"Several people may claim it and mean different things. "
            f'Use compare("{ref}") to see every claimant, then load a specific '
            f'one as "author/{ref}" or pin a version as "author/{ref}@v1".'
        )
    owner, rest = ref.split("/", 1)
    if "@" in rest:
        label, version = rest.split("@", 1)
        return owner, label, version
    return owner, rest, None


def _build(conn: sqlite3.Connection, row: sqlite3.Row) -> Submission:
    from . import views  # noqa: PLC0415  (shared view logic, one source of truth)

    view = views.claimant_view(conn, row)
    iv = conn.execute(
        "SELECT artifact_path FROM intervention"
        " WHERE author=? AND label=? AND version=?",
        (row["author"], row["label"], row["version"]),
    ).fetchone()

    return Submission(
        author=view["author"],
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
        _artifact_path=iv["artifact_path"] if iv else None,
    )


def load(ref: str, *, database: str | Path | None = None) -> Submission:
    """Load one submission by `author/label` or `author/label@version`.

    Without a version you get that author's newest, which is their own revision
    history and not the registry choosing between authors. Pin the version when
    the number needs to stay comparable later; a pinned reference resolves to the
    same frozen submission permanently.
    """
    owner, label, version = _parse(ref)
    conn = _connect(database)

    if version is None:
        found = [
            r["version"]
            for r in conn.execute(
                "SELECT version FROM submission WHERE author=? AND label=?",
                (owner, label),
            )
        ]
        if not found:
            raise NotFound(f"{ref!r} is not in this registry")
        version = max(found)

    row = conn.execute(
        "SELECT * FROM submission WHERE author=? AND label=? AND version=?",
        (owner, label, version),
    ).fetchone()
    if row is None:
        raise NotFound(f"{owner}/{label}@{version} is not in this registry")
    return _build(conn, row)


def claimants(label: str, *, database: str | Path | None = None) -> list[Submission]:
    """Everyone claiming a label, in storage order.

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
