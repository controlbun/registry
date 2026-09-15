"""A registry for activation-steering artifacts.

    from registry import load, compare, claimants

    load("alice/kindness@v1")   one pinned submission
    load("alice/kindness")      the head of that author's revision chain
    load("soham/pro-human")     raises: three current versions, none supersedes
    load("kindness")            raises: a bare label does not resolve
    compare("kindness")         every claimant, and what sits between them
"""

from .client import (
    Ambiguous,
    BareLabelError,
    Comparison,
    Contract,
    Evidence,
    MismatchedArtifact,
    NotFound,
    Submission,
    claimants,
    compare,
    load,
)

__all__ = [
    "Ambiguous", "BareLabelError", "Comparison", "Contract", "Evidence",
    "MismatchedArtifact", "NotFound", "Submission", "claimants", "compare",
    "load",
]
