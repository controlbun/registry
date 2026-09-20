"""A registry for activation-steering artifacts.

    from controlbun import load, compare, claimants, namespace

A submission is `author/model_id/label@version`, and the model is part of what it
is rather than an attribute of it: one author holding one label on two models
holds two submissions and both stand.

    load("soham/allenai/Olmo-3-1125-32B/pro-human@meandiff")
                                one pinned submission, named in full
    load("soham/trauma@d61-diffmeans-expository-L34")
                                the short form, while it names one submission
    load("soham/trauma")        the head of that author's revision chain
    load("soham/pro-human")     raises: four current versions, none supersedes
    load("pro-human")           raises: a bare label does not resolve
    compare("pro-human")        every claimant, across models, and what sits
                                between them
    namespace("soham")          who has bound an account to it, usually nobody

The short form raises `Ambiguous` naming the alternatives when the author holds
that label on more than one model. Picking one would be the registry choosing.
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
