"""The reference form, written once and read once.

    soham/allenai/Olmo-3-1125-32B/pro-human@meandiff
    soham/Qwen/Qwen3-8B/trauma@d61-diffmeans-expository-L34
    author / model_id                  / label     @ version

Four parts, and the model is one of them rather than a property hanging off the
other three. An intervention is a tensor in one model's residual basis, so a
reference that does not name the model has not named an artifact.

**This module formats and splits. It resolves nothing.** Turning a short
`author/label` into a submission needs the corpus, so that lives in `client.py`
where the database is. What is here is the string rule, in one place, because
the ref is printed by the client, by the export, by the publisher and by four
Astro components, and six spellings of one format is six chances for a page to
show a reference that does not resolve.

## Parsing, which looks impossible and is not

Split on `@` for the version, then split the rest on `/`: **the first segment is
the author, the last is the label, and everything in between is the model.**
That works for any model id length because the model is the middle rather than a
fixed number of segments. `gpt2` and `bert-base-uncased` have no distributor and
are one segment; `allenai/Olmo-3-1125-32B` is two. Nothing here requires a slash
in a model id and nothing validates its shape: it is an open string like every
other user-supplied field in this schema.

The short form `author/label@version` still parses, and comes back with no model.
It resolves when that author holds that label on exactly one model and raises
naming the alternatives when they hold it on more. A short form that silently
picked a model would be the registry choosing, which is the thing it does not do.
"""

from __future__ import annotations

from dataclasses import dataclass


class BareLabelError(LookupError):
    """Raised when a bare label is handed to something that wants an artifact.

    `kindness` is a view across everybody claiming the word, owned by nobody. It
    does not resolve, here or anywhere else.
    """


@dataclass(frozen=True)
class Parsed:
    """The parts of a reference, before anything looks them up.

    `model` and `version` are None when the reference did not carry one. Both are
    short forms and both are answerable from the corpus, and neither is answered
    here.
    """

    author: str
    model: str | None
    label: str
    version: str | None

    @property
    def short(self) -> bool:
        """Whether the model was left out, which is the form that may not resolve."""
        return self.model is None


def format(author: str, model_id: str, label: str, version: str) -> str:
    """The four parts as the one string every surface prints.

    Shadows the builtin inside this module and nowhere else; callers write
    `ref.format(...)`, which reads as what it is.
    """
    return f"{author}/{model_id}/{label}@{version}"


def short(author: str, label: str, version: str | None = None) -> str:
    """The model-less form, for an error message naming what did not resolve."""
    return f"{author}/{label}" + (f"@{version}" if version else "")


def parse(ref: str) -> Parsed:
    """Split a reference. Raises `BareLabelError` on a bare label.

    First `@` ends the label, so a version may contain one and a label may not.
    That is 001's rule kept rather than a new one.
    """
    rest, _, version = ref.partition("@")
    segments = [s for s in rest.split("/")]

    if len(segments) < 2 or not all(s.strip() for s in segments):
        raise BareLabelError(
            f"{ref!r} is a bare label and does not resolve to an artifact. "
            f"Several people may claim it, on several models, and mean "
            f'different things. Use compare("{rest}") to see every claimant, '
            f'then name one as "author/model/{rest}" or pin a version as '
            f'"author/model/{rest}@v1".'
        )

    author, label = segments[0], segments[-1]
    middle = segments[1:-1]
    return Parsed(
        author=author,
        model="/".join(middle) if middle else None,
        label=label,
        version=version or None,
    )
