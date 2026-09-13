"""A registry for activation-steering artifacts.

    from registry import load, compare, claimants

    load("alice/kindness@v1")   one pinned submission
    load("alice/kindness")      that author's newest
    load("kindness")            raises: a bare label does not resolve
    compare("kindness")         every claimant, and what sits between them
"""

from .client import (
    BareLabelError,
    Comparison,
    Contract,
    Evidence,
    NotFound,
    Submission,
    claimants,
    compare,
    load,
)

__all__ = [
    "BareLabelError", "Comparison", "Contract", "Evidence", "NotFound",
    "Submission", "claimants", "compare", "load",
]
