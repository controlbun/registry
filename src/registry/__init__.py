"""A registry for activation-steering artifacts.

    from registry import load, compare, claimants, namespace

    load("alice/kindness@v1")   one pinned submission
    load("alice/kindness")      the head of that author's revision chain
    load("soham/pro-human")     raises: three current versions, none supersedes
    load("kindness")            raises: a bare label does not resolve
    compare("kindness")         every claimant, and what sits between them
    namespace("alice")          who has bound an account to it, usually nobody
"""

from .client import (
    Ambiguous,
    BareLabelError,
    ClaimEvidence,
    Comparison,
    Contract,
    Evidence,
    MembershipObservation,
    MismatchedArtifact,
    Namespace,
    NamespaceClaim,
    NotFound,
    Submission,
    claimants,
    compare,
    load,
    namespace,
)

__all__ = [
    "Ambiguous", "BareLabelError", "ClaimEvidence", "Comparison", "Contract",
    "Evidence", "MembershipObservation", "MismatchedArtifact", "Namespace",
    "NamespaceClaim", "NotFound", "Submission", "claimants", "compare",
    "load", "namespace",
]
