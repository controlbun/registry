"""The handoff between the intake form and whatever coding agent is helping an author.

Premise, restated because a premise stated in one document gets violated in every
other one: **plurality is the product; the registry never designates, consumers
pin, visibly.** Nothing here ranks, scores, approves or filters anything, and the
prompt below tells a reader's agent what this registry records and why, so it can
go and read its own author's files. It says nothing about what a good artifact is,
because that is not a question this project answers.

**It is a manual, not a governance surface.** That distinction is `DECISIONS.md`
2026-09-16 on `controlbun.agentContext`, and the commit that rewrote that entry is
titled with it. Describing the fields accurately is the whole job. An agent that
reads what `layer_convention` is for has learned why getting it wrong is silent,
and an agent that reads that a bare label is a view across claimants has learned
the premise without this document editorializing about it.

**The one rule the prompt states in the strongest terms it can manage is: never
write a value you did not read.** A registry whose reason to exist is trustworthy
provenance cannot take a plausible-looking chat template hash from something that
generates plausible-looking text. Absence is a state everywhere in this schema,
by `schema/migrations/005` for the revision and `006` for the digest, and it
renders as "not recorded" rather than as a gap. So the format has one way to say
an absence and it is a positive statement with a reason, not an omission: a field
the agent cannot find is declared, and a field that is neither declared nor
answered is a refusal naming it.

**Liberal in, strict out.** What comes back from a chat window has markdown
fences, preamble, bullets, bold keys, blockquote markers and typographic quotes
around it, because that is what agents emit. All of that is peeled. What is passed
on is checked: an integer that is an integer, a commit that is forty hex through
`controlbun.fetch.commit_sha` rather than a second copy of that rule, and no value
that is still a placeholder out of the template.

**The one unbounded value is written last, and that is structural.** A model
asked to open a delimiter forgets to close it, which is not a thing a stricter
instruction fixes. `definition` used to be the fifth of twenty-eight lines, so
one missing `>>>` ran to the end of the submission and swallowed the other
twenty-three; the first three real uses of this handoff failed that way and
nothing was recoverable. It is now the last line of the template, below the
`not-found:` lines, so an unterminated fence swallows nothing and the end of the
submission closes it. The general rule, recorded in `DECISIONS.md` 2026-09-20:
in any format a language model is asked to produce, the value with no natural
end goes last, because a missing terminator then costs nothing. The prose above
the template still explains `definition` third, where it belongs, and says in
its own words that the position is the format protecting the field rather than
ranking it.

Two entry points for the form, and this module owns no socket, no route and no
markup. `artifacts/intake.py` owns all three and is not edited from here:

    prompt()     the text the `agent-prompt` button copies
    received()   one paste in, the form's fields out, or a refusal with the reason

Wiring, for whoever adds the two routes. Both sit behind `_admitted()` like
everything else, and neither reaches the network or the filesystem.

    GET  /agent-prompt   `prompt(suggestions(conn))`, served as text/plain
    POST /agent-paste    `received(body)`, the same JSON shape as `/check`:
                         `display` pairs for the panel, plus `fields` keyed by
                         `data-field` for the page to assign into its inputs

`Refused` joins the tuple `do_POST` already catches, next to `intake.Refused`,
so a bad paste comes back as the sentence it carries rather than a traceback.
Parsing happens here rather than in the page's script because the rules are the
schema's and there is one implementation of them that a test can drive.
"""

from __future__ import annotations

import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from controlbun import fetch  # noqa: E402

# The markers. Long enough that nothing in ordinary prose is one, and plain ASCII
# so a chat window has nothing to prettify. Matched case-insensitively and with
# whatever decoration arrives around them.
BEGIN = "=== BEGIN CONTROLBUN SUBMISSION ==="
END = "=== END CONTROLBUN SUBMISSION ==="

# The multi-line value delimiters, for the definition and anything else with a
# newline or a colon in it. Chosen over quoting because a quote is the character a
# chat window is most likely to replace with a different quote.
OPEN_BLOCK = "<<<"
CLOSE_BLOCK = ">>>"

_BEGIN_RX = re.compile(r"^[\s>*=#_`-]*BEGIN\s+CONTROLBUN\s+SUBMISSION\b", re.I)
_END_RX = re.compile(r"^[\s>*=#_`-]*END\s+CONTROLBUN\s+SUBMISSION\b", re.I)
_FENCE_RX = re.compile(r"^\s*(```+|~~~+)\s*\w*\s*$")
_QUOTE_RX = re.compile(r"^(\s*>\s)+")
_BULLET_RX = re.compile(r"^\s*(?:[-+*•]\s+|\d+[.)]\s+)")
# The optional quotes around the key are for the agent that answers in JSON
# anyway. Its braces are read past and its quoting is undone below, because a
# refusal over punctuation would send somebody back for a reformat of an answer
# that is already complete and already correct.
_KEY_RX = re.compile(r"^\s*[\"']?([A-Za-z][A-Za-z0-9 ._-]{0,40}?)[\"']?\s*[:=]\s*(.*)$")
_PUNCTUATION_ONLY = {"{", "}", "[", "]", "},", "],", "{,"}
_NUMBER_RX = re.compile(r"^-?\d+(\.\d+)?([eE][-+]?\d+)?$")
_ABSENT_RX = re.compile(r"^(?:not[\s_-]*found|absent|unknown|not[\s_-]*recorded)$")

# What a chat window does to a paste on its own. Replaced rather than refused,
# and the reader is told it happened.
_TYPOGRAPHY = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    " ": " ", " ": " ", " ": " ",
    "​": "", "‌": "", "‍": "", "﻿": "",
}


class Refused(ValueError):
    """A paste this will not turn into form values, with the reason in the message.

    One class for every refusal here, for the reason `artifacts/intake.py` gives
    for its own: the reader is somebody holding a reply from their agent, and a
    sentence they can act on is the entire product of the error path.
    """


# --------------------------------------------------------------------------- #
# What the form takes, which is read off the form rather than described twice.


@dataclass(frozen=True)
class Spec:
    """One thing the prompt asks for and the parser hands back.

    `form` is the `data-field` name in `artifacts/intake.py`, so a parsed paste
    drops straight into the page's inputs. `cannot_be_absent` marks the columns
    `schema/migrations/001`, `005` and `010` leave NOT NULL: not a bar an artifact
    has to clear, a shape the row physically has. Four of them are the identity
    itself since 010, `author`, `model_id`, `label` and `version`, and an absence
    in one of those is not a recorded absence but the lack of a row to record it
    against. Everything else is nullable and an absence in it records as an
    absence.

    `column` is the third spelling and exists for one reason: a declared absence
    is stored against the field it is about, and `artifacts/intake.py insert`
    compares it to the value in the row. Two spellings of one field is a
    question somebody has to stop and resolve, so the translation lives here
    beside the other one rather than in whichever caller noticed. Empty means
    the name already is the column, which is true of everything but `sha256`.
    """

    name: str
    form: tuple[str, ...]
    cast: str = "text"
    cannot_be_absent: bool = False
    aliases: tuple[str, ...] = ()
    column: str = ""

    @property
    def stored(self) -> str:
        """The name the row holds this under."""
        return self.column or self.name


# Order is the order the template asks for them in and the order they are
# displayed. It is not the order the prose above the template explains them in:
# `definition` is explained third, where it belongs, and written last, where an
# unterminated fence costs nothing. Those two orders differ on purpose and the
# prompt says so in its own words.
#
# `shape`, `dtype` and `l2_norm` are NOT NULL columns and are not marked here,
# because `intake.entry_from` takes all three off the bytes rather than off the
# form: stating one is a claim the bytes are held to, and stating nothing is not
# a wrong claim.
SPECS: tuple[Spec, ...] = (
    Spec("author", ("author",), cannot_be_absent=True, aliases=("namespace",)),
    Spec("label", ("label",), cannot_be_absent=True),
    Spec("version", ("version",), cannot_be_absent=True),
    Spec("created_at", ("created_at",), cannot_be_absent=True,
         aliases=("created", "extracted_at", "when")),
    Spec("intervention_id", ("intervention_id",), cannot_be_absent=True,
         aliases=("id", "intervention")),
    Spec("kind", ("kind",), cannot_be_absent=True),
    # Part of the primary key since `schema/migrations/010`, which is why this
    # cannot be absent: without it there is no submission to write, rather than a
    # submission with an unrecorded model.
    Spec("model_id", ("model_id",), cannot_be_absent=True, aliases=("model",)),
    Spec("model_revision", ("model_revision",), aliases=("revision",)),
    Spec("layer", ("layer",), cast="integer", cannot_be_absent=True),
    Spec("layer_convention", ("layer_convention",), cannot_be_absent=True,
         aliases=("convention",)),
    Spec("hook_point", ("hook_point",), cannot_be_absent=True, aliases=("hook",)),
    Spec("chat_template_hash", ("chat_template_hash",),
         aliases=("template_hash", "chat_template")),
    Spec("shape", ("shape",)),
    Spec("dtype", ("dtype",)),
    Spec("l2_norm", ("l2_norm",), cast="number", aliases=("l2", "norm")),
    Spec("sha256", ("sha256",), column="artifact_sha256",
         aliases=("artifact_sha256", "digest", "file_sha256")),
    Spec("activation_norm", ("activation_norm",), cast="number"),
    Spec("coeff_low", ("coeff_low",), cast="number",
         aliases=("coefficient_low", "alpha_low")),
    Spec("coeff_high", ("coeff_high",), cast="number",
         aliases=("coefficient_high", "alpha_high")),
    Spec("steering_position", ("steering_position",), aliases=("position",)),
    Spec("license_status", ("license_status",), aliases=("license",)),
    # One field, two inputs. The path inside the published repo and the row's
    # `artifact_path` are the same string or the fetch is a 404
    # (`artifacts/publish.py`), and the form spells that string twice because the
    # two modes each have their own box. Whichever mode is hidden ignores its copy.
    Spec("artifact_path", ("link_path", "bytes_path"), cannot_be_absent=True,
         aliases=("path", "path_in_repo")),
    Spec("artifact_repo", ("link_repo",), aliases=("repo", "hub_repo")),
    Spec("artifact_commit", ("link_commit",), cast="commit",
         aliases=("commit", "commit_sha")),
    # The other half of the pin since `schema/migrations/007`. Both droppable,
    # and both empty means the Hub, which is where a row recording neither has
    # always resolved. An agent sitting in the checkout the artifact was
    # published from is exactly who knows which host that is.
    Spec("artifact_host", ("link_host",), aliases=("host",)),
    Spec("artifact_url_template", ("link_url_template",),
         aliases=("url_template", "template")),
    # Last, and last structurally rather than by rank. It is the only value in
    # this list with no natural end to it, so it is the only one the template
    # fences, and a fence with nothing after it swallows nothing when its
    # closing marker is missing. `_gather` closes it on the end of the
    # submission for that reason. Moving it here is what turned the defect that
    # lost the first three real submissions from fatal into a note.
    Spec("definition", ("definition",), cannot_be_absent=True),
)

BY_NAME: dict[str, Spec] = {}
for _spec in SPECS:
    BY_NAME[_spec.name] = _spec
    for _alias in _spec.aliases:
        BY_NAME[_alias] = _spec


# --------------------------------------------------------------------------- #
# The prompt.


_HEAD = """\
You are helping the person you work for prepare one submission to controlbun, a
registry of activation-steering artifacts. Read their files and answer about
their artifact. Do not answer from memory of how registries like this usually
work, and do not answer from what a field's name suggests it should hold.

Answer by going and looking: the extraction script, its config and its logs, the
notebook, the model card of the model the activations were read from, the commit
history, and the artifact file itself. Where you looked is worth more than what
you produce, so say where each answer came from if the person asks.

## The rule that outranks every other instruction here

**Never write a value you did not read.** Not a hash, not a revision, not a
layer index, not a license. This registry exists so that somebody can pick up a
stranger's steering vector and apply it correctly, and every number in it is
load bearing in a way that fails silently: a vector applied at the wrong layer
or under the wrong chat template does not error, it appears not to work. A
plausible value you produced is indistinguishable from one the author measured,
and it destroys the only thing this registry is for.

If you cannot find something, say so in the block at the bottom with the
`not-found:` line, which takes the field name and the reason. Absence is a real
state in this schema. Nullable columns exist for exactly this and a row with a
missing revision renders as "not recorded" rather than as a gap or an error.
The real artifacts in this registry today record no revision, no chat template
hash and no activation norm, and each absence is documented as what was never
captured rather than filled with something that reads like a measurement.

An empty field is a fact. A guessed field is a forgery.

## Nothing here is chosen from a list

Every field below is an open string. There is no set of permitted kinds, hook
points, layer conventions, steering positions, methods or file formats, and
there is no page that lists them. Where this text says a value is common, it
means other people have used it, and nothing whatsoever follows from that.

If the thing your author built does not fit a word anybody has used before, use
their word. An artifact nobody has a name for is a submission this registry
wants, not a problem to work around. The same goes for the file: the intake tool
refuses bytes it cannot read without executing them, and says so in those terms,
rather than refusing a format for not being on a list.

## What the registry needs, and why each one

Two objects get written from your answers. A **submission**, which is one
author's complete take on a label against one model, frozen forever at
`author/model_id/label@version`. An **intervention**, which is the artifact
itself plus everything needed to apply it.

The model is part of the reference because a direction is a tensor in one
model's residual basis and does nothing for another one. So

    soham/allenai/Olmo-3-1125-32B/pro-human@meandiff

is one submission, and the same author's take on the same word against another
model is a different submission with its own reference. Neither supersedes the
other and neither is the real one.

**author** Your author's own namespace. Free to claim and never assigned.

**label** The trait or behavior, as your author names it. Free to claim, and
other people claim the same one: `author/label` is theirs, and the bare label is
a view across everybody who claims it, owned by nobody. The registry holds
competing takes on the same word deliberately and resolves none of them.

**definition** Your author's own theory of the label, in their own words. This
is the field that matters most and the one you are least able to produce
yourself. It is load bearing twice: it feeds contrast-pair generation, and it is
the thing another author disagrees with when they claim the same label.

Do not write the correct definition of the word. There is not one. Ten people
meaning different things by "kindness" is the content of this registry, not a
collision to be tidied up: one author's kindness is warmth in affect and
another's is costly help and explicitly not warmth, and both submissions stand.
So write what your author thinks the trait is, including the part that makes
their take unlike anybody else's, and including what they think it is not. If
you have their words for it, in a paper, a README, a docstring or the contrast
prompts themselves, use theirs. If you do not, ask them rather than composing
one.

Its line is the last one in the block, below every other field and below the
`not-found:` lines. That is the format protecting it rather than demoting it,
and the reason is under `How to answer`. Read this section again before you
write that line; it is the one place in the block worth spending your effort.

**version** Whatever distinguishes this take from the author's other takes on
the same label against the same model. `author/model_id/label@version` resolves
to one frozen submission forever, so it is never reused and never edited: a
correction is a new version. Versions in this registry today name what changed,
like the estimator that produced the direction or the layer it was read from,
rather than counting.

A take on a different model is not a version. It is another submission, and the
model in the reference is what keeps the two apart.

**created_at** When the work happened, which is not when it is typed into the
form. ISO 8601, UTC. The run log, the file's own timestamp or the commit date,
not today's date.

**intervention_id** The primary key of the artifact row, and the thing an eval
report or an attack points at later. Unique across the whole registry, stable
forever, and your author's to choose.

**kind** What this artifact is. `direction`, `sae-latent`, `probe`, `reft` and
`lora` are values the schema's own comment calls common rather than permitted,
and an unrecognized kind is storable and displayable and simply has no apply
path in the client until somebody writes one.

**model_id** The model the activations were read out of, and part of what the
submission is rather than a property of it. A direction has no meaning apart
from it. Base and instruct are different models, so give the exact repo id the
extraction loaded, not the family name.

Give the whole string the way the distributor writes it, distributor included:
`allenai/Olmo-3-1125-32B`, `Qwen/Qwen3-8B`. A model with no distributor is one
segment and that is fine, `gpt2` and `bert-base-uncased` among them; nothing here
requires a slash and nothing checks the shape of what you write.

**model_revision** The exact revision of those weights, if the extraction
recorded it. A commit on the model repo. If nobody wrote it down, `not-found:`
it and say so. Do not paste the sha the model repo has today: that is a false
provenance claim that reads exactly like a true one, and it is worse than the
hole it fills.

**layer** An integer. Which layer the activations came from.

**layer_convention** How to read that integer, stated separately because getting
it wrong is silent. `block-0indexed` is a value this corpus already holds. Read
it off the hook name or the indexing in the extraction code rather than assuming
the usual one, and if the code counts from one, or counts sublayers, or indexes
something other than transformer blocks, write down what it counts.

**hook_point** Where in the block the activations were read, and where the
artifact acts. `resid_pre`, `resid_post`, `mlp_out` and `attn_out` are common.
Architectures have hook points those four do not name, and where your author's
is not among them, name it their way.

**chat_template_hash** The template the activations were read under, identified
by a digest, because a vector extracted under one template may not transfer to
another. Take the value your author's code computed. Nothing here fixes what
hash function or what exact string, so pass through what their pipeline
records, and if you compute one yourself, tell them in your reply what you
hashed and with what, so they can decide whether that is the thing to record.
If no template was applied, because activations were read from raw text against
a base checkpoint, that is the common case for a base-model extraction:
`not-found:` it with that sentence. Never produce a hex string for this field.

**shape**, **dtype**, **l2_norm**, **sha256** Optional, and checked. The intake
tool reads all four out of the bytes for itself. If you state one, the bytes are
held to it and the row keeps what you said, which is worth more than a number
derived from the bytes it is being compared against: state them when they are
cited from your author's own record, the paper, or the extraction output. State
nothing and the row records what the file says. Saying nothing is not a wrong
claim, and for a first submission it is usually the better answer.

`shape` is compared as the numbers in it, so `[8192]` and `(8192,)` are the
same answer and neither is wrong.

**`sha256` is the one to leave out unless you know it survives.** It is the
digest of the whole file, header included, and the intake tool rewrites the
header with its keys sorted before it records anything, because safetensors
seeds its header order per process and a file that does not reproduce byte for
byte makes every digest in this registry meaningless. So the digest the row
ends up with is of the file the tool wrote, and the digest your author recorded
for the file they exported will not match it unless their export was already
sorted. That is a difference in byte order, not in the tensor, and stating a
digest is the one way to turn it into a refusal.

**activation_norm** The typical residual norm at that layer, and only if the
author's coefficients are expressed as a fraction of activation magnitude. If
they scaled a raw alpha against a unit vector, leave it absent even when the
number is measured somewhere, because putting it here asserts something about
what the coefficients mean.

**coeff_low**, **coeff_high** The coefficient range the author actually swept or
recommends. Absent if they did not sweep one.

**steering_position** Where the intervention is applied during generation, in
the author's words.

**license_status** Whether a source model's license reaches a direction read out
of it is open. This registry's own author takes the position that a direction is
the work of whoever built it, and records the case against that position beside
it; you are not bound by either. Read the source model's license and say what you
read, where you read it and when. If something is unresolved, say that:
unresolved rights mean the artifact can be pointed at but not served, which is a
fact the registry records rather than a reason to refuse it.

## Where the artifact is, and the pin

**artifact_path** Where the file sits inside the published repo, and nowhere
else. Relative, no leading slash.

**This is not where the file is on your author's machine.** That is the mistake
this field actually gets, and it gets it from people who found the file, which
is to say from you. A scratch path, a cluster mount, a home directory or
anything starting with `/` is refused, and refused rather than cleaned up,
because the registry hands this exact string to the host when somebody later
downloads the vector. A local path stored here describes a folder that exists
on one machine, so every fetch after today looks for it and gets a 404.

If the artifact is already published, give the path it has in that repo,
character for character. If it is not published yet, this field is a decision
rather than a lookup: choose where it will sit once it is uploaded, and say so.
`vectors/<name>.safetensors` is a reasonable shape and nothing requires it.

So: read where the file is now to find and verify the bytes, then answer with
where it goes. Those are two different strings and only the second one belongs
here.

**artifact_repo** The repo the author published it in, as `owner/name`. Their
own account, never the registry's. Any host; most steering artifacts are in
GitHub repos and that is not a lesser answer than a Hub one.

**artifact_commit** Forty hex characters. A commit, never a branch and never a
tag: whoever owns a repo can move a tag, so pinning to one pins to whatever is
there today, which is the opposite of what `author/model_id/label@version`
promises. If
you only have a branch, resolve it to the commit it points at right now and give
that. If the artifact is not published anywhere yet, `not-found:` the repo and
the commit and give the path anyway; the intake tool publishes the file to the
author's own namespace and records the commit it made.

**artifact_host** Which host that repo is on, as a bare authority:
`huggingface.co`, `github.com`, anything. Droppable, and dropping it means the
Hub.

**artifact_url_template** How `{host}`, `{repo}`, `{commit}` and `{path}` become
a URL that returns the file's bytes. Droppable, and dropping it means the Hub's
layout.

**The commit has to end up in the URL, and that is the only shape rule.** A
template that resolves to a URL not containing the commit is refused, because
such a URL returns whatever is at that address today, and a pin to whatever is
there today is the thing `author/model_id/label@version` promises not to be. You can
leave out any of the other three: hard-coding the host in the template is
normal, and the GitHub media layout below does exactly that. Two further
mechanical rules, so they do not surprise you: the scheme has to be http or
https, and each placeholder has to be a bare `{name}` with no format spec and
no attribute access.

Do not guess the rest of it: fetch the URL you are about to give and check that
what comes back is the artifact rather than a redirect page or a git-LFS pointer
file, and say that you checked. GitHub needs two different layouts depending on
whether the file is LFS-tracked. For one repo, one commit and one path, the
media host returns the object and `raw` returns a small text pointer beginning
`version http`, and neither is an error, so only fetching tells you which layout
your author's file needs.

The file itself goes in as safetensors, holding exactly one tensor. A file
holding several is refused, because nothing can tell which one is the artifact.
The tool converts what it can read without running it and refuses a pickle in
those words.
"""

_HOW = """\
## How to answer

Write whatever you want to your author first. Then put the block below at the
end of your reply, and put nothing after it. The parser finds it inside
surrounding prose and ignores everything else, so explanation costs nothing.

One field per line, `field: value`. For anything with a newline or a colon in
it, and that means the definition, open with `<<<` and close with `>>>` on their
own lines. For anything you could not find, one `not-found:` line naming the
field and the reason. Leave nothing empty and leave no placeholder in: the
parser refuses both rather than guessing which you meant.

**The definition is the last line of the block, and last here is not least.** It
is the field that matters most and the only one with no natural end to it, so it
sits where running long is free. Everything short goes above it, the `not-found:`
lines included, and the one value that can be any length goes where nothing comes
after it.
"""


def _wrap(text: str) -> str:
    """One paragraph at the width the rest of this document is written to.

    Wrapped here rather than in the source, because the markers substitute
    shorter than their names and a paragraph laid out by eye around
    `OPEN_BLOCK` comes out ragged in the text an agent actually reads.
    `break_on_hyphens` off because `not-found:` is a field name and a wrap
    inside it reads as two words.
    """
    return textwrap.fill(" ".join(text.split()), width=80,
                         break_on_hyphens=False)


# Wrong beside right, and nothing in it is invented. Two of the three were
# observed and are dated here; the third is a refusal the parser makes, stated
# as a refusal rather than as something somebody did. A template shows the
# shape and does not stop the mistake, which is why the same one happened three
# times, and an invented failure would teach an agent to avoid something nobody
# has ever done while leaving the real ones where they are.
_GOES_WRONG = "\n\n".join([
    "## What actually goes wrong",

    _wrap("The first three submissions written through this handoff were all "
          "refused, and all three failed the same way. None of them was wrong "
          "about the artifact."),

    _wrap(f"**The `{OPEN_BLOCK}` that never closed.** All three, hours apart, "
          "one author, one agent, one line."),

    f"    definition: {OPEN_BLOCK}\n"
    "    ...the author's own theory, over as many lines as it takes...\n"
    "    intervention_id: ...       <- swallowed, and so was every line below",

    "What came back, all three times:",

    # The refusal those three got, verbatim. Rewrapped under an indent and not
    # reworded: a message quoted back differently from the one that arrives is
    # a message somebody stops trusting.
    f"    definition opened with {OPEN_BLOCK} and nothing closed it, so it ran"
    " to the\n    end of the submission and took everything after it with it,"
    " including\n    artifact_path, hook_point, intervention_id, kind, layer,"
    " layer_convention,\n    license_status, model_id, model_revision,"
    " not-found, steering_position.",

    "The fix is one line:",

    f"    definition: {OPEN_BLOCK}\n"
    "    ...the author's own theory, over as many lines as it takes...\n"
    f"    {CLOSE_BLOCK}",

    _wrap("`definition` is the last line of the block for this reason, so "
          f"forgetting the `{CLOSE_BLOCK}` there now swallows nothing and the "
          f"end of the submission closes it. Open a `{OPEN_BLOCK}` on any "
          "value with lines after it, forget to close it, and the block still "
          "eats them and the whole paste is still refused."),

    _wrap("**A local path in `artifact_path`.** Observed once, on a real "
          "submission, and caught before the row was written. The agent "
          "answered with the path it had just read the file from on the "
          "author's cluster. Anything starting with `/` is refused: it names a "
          "folder on one machine, so every fetch after today gets a 404. "
          "Answer with where the file sits in the published repo, like "
          "`vectors/direction.safetensors`."),

    _wrap("**A branch where the commit goes.** `artifact_commit: main` is "
          "refused, and refused rather than resolved for you. Whoever owns a "
          "repo can move `main`, so it pins to whatever is there today, which "
          "is the opposite of what `author/model_id/label@version` promises. "
          "Resolve it yourself and give the forty hex characters it points at "
          "right now."),
]) + "\n"

_TEMPLATE = f"""\
{BEGIN}
author: <namespace>
label: <the trait, as your author names it>
version: <what distinguishes this take>
created_at: <ISO 8601 UTC, when the work ran>
intervention_id: <unique, stable, the author's to choose>
kind: <what this artifact is>
model_id: <the repo id the activations were read from>
model_revision: <the revision of those weights>
layer: <the integer>
layer_convention: <how to read that integer>
hook_point: <where in the block>
chat_template_hash: <the digest your author's code recorded>
shape: <only if cited from the author's record>
dtype: <only if cited from the author's record>
l2_norm: <only if cited from the author's record>
sha256: <only if cited from the author's record>
activation_norm: <only if coefficients are fractions of it>
coeff_low: <the swept range, low end>
coeff_high: <the swept range, high end>
steering_position: <where it is applied during generation>
license_status: <what the model license permits, where you read it, when>
artifact_path: <where it sits in the published repo, relative, not a local path>
artifact_repo: <owner/name>
artifact_commit: <forty hex characters>
artifact_host: <the host that repo is on; drop the line for the Hub>
artifact_url_template: <how host, repo, commit and path become a URL>
not-found: <field name> <why there is no value, in a sentence>
definition: {OPEN_BLOCK}
<your author's own theory of the label, in their words,
over as many lines as it takes>
{CLOSE_BLOCK}
{END}
"""

# Read off the spec list rather than typed out again. It was typed out again,
# and it named the fields in an order the template no longer uses the moment
# `definition` moved, which is a second copy going stale in the same edit that
# made it wrong.
_REQUIRED = [spec.name for spec in SPECS if spec.cannot_be_absent]
_TAIL = _wrap(
    "Every line is droppable except the ones the schema cannot write a row "
    "without: " + ", ".join(_REQUIRED[:-1]) + f" and {_REQUIRED[-1]}"
    + ". For those, a `not-found:` is refused too, because there is no row to "
    "write without them. That is a shape the database has, not a judgment "
    "about the artifact."
) + "\n"

_OBSERVED_HEAD = """\
## What other people have typed into these fields

Read out of this registry's own corpus at the moment the prompt was copied. Not
a menu, not a set to pick from, and not an indication that a value outside it is
wrong. It is here so that where your author's answer coincides with somebody
else's, it is spelled the same way, and where it does not, it stays theirs.
"""


def prompt(observed: dict[str, list[str]] | None = None) -> str:
    """The text the button copies, ready to paste into a coding agent.

    `observed` takes `intake.suggestions(conn)` verbatim, which is the same
    query the datalists behind the form's text fields are built from. Passing it
    is optional and passing nothing is not a degraded prompt: the corpus section
    is autocomplete in prose, and every field is open with or without it.
    """
    parts = [_HEAD]
    # `observed` is keyed by the form's `data-field` names, and this document
    # asks for the schema's. They differ for everything the form splits across
    # link and bytes mode, so `link_host` would appear here under a name that
    # appears nowhere else in the prompt and that the template does not use. One
    # field with two spellings in one document is a question somebody has to
    # stop and resolve, so it is translated back here rather than explained.
    said_as = {form: spec.name for spec in SPECS for form in spec.form}
    lines = sorted(
        f"{said_as.get(field, field)}: " + ", ".join(values)
        for field, values in (observed or {}).items() if values
    )
    if lines:
        parts.append(_OBSERVED_HEAD + "\n" + "\n".join(lines) + "\n")
    # The template goes last and nothing follows it but the one paragraph about
    # which lines are droppable, because the thing being asked for is the thing
    # an agent's eye lands on when it starts writing. `_GOES_WRONG` sits
    # immediately above it for the same reason: a failure named far from where
    # the answer gets typed is a failure nobody reads.
    parts += [_HOW, _GOES_WRONG, _TEMPLATE, _TAIL]
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# The paste, coming back.


@dataclass(frozen=True)
class Handoff:
    """One parsed paste: what to put in the form, and what was said to be absent.

    `values` is keyed by the form's own `data-field` names, so the page assigns
    them without a second mapping. `absent` is the agent's own account of why a
    field has no value, kept rather than dropped because it is the difference
    between a field nobody recorded and a field nobody looked for, and that
    difference is the whole reason the format has a line for it.
    """

    values: dict[str, str] = field(default_factory=dict)
    absent: dict[str, str] = field(default_factory=dict)
    extra: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def pinned(self) -> bool:
        """Whether a published pin came back, which is link mode in the form."""
        return bool(self.values.get("link_repo") and self.values.get("link_commit"))

    def display(self) -> list[tuple[str, str]]:
        """Pairs for the panel. An absence is a sentence, never a blank."""
        out: list[tuple[str, str]] = []
        for spec in SPECS:
            if spec.form[0] in self.values:
                out.append((spec.name, self.values[spec.form[0]]))
            elif spec.name in self.absent:
                out.append((spec.name, f"absent: {self.absent[spec.name]}"))
        for key, value in sorted(self.extra.items()):
            out.append((f"{key} (no field for this)", value))
        for note in self.notes:
            out.append(("note", note))
        return out


def _normalize(text: str) -> tuple[str, bool]:
    """Undo what a chat window does to a paste, and say whether it did any."""
    out = text
    for bad, good in _TYPOGRAPHY.items():
        out = out.replace(bad, good)
    return out, out != text


def _peel(line: str) -> str:
    """One line with its markdown taken off. Not applied inside a `<<<` block."""
    line = _QUOTE_RX.sub("", line)
    line = _BULLET_RX.sub("", line)
    return line.replace("*", "").replace("`", "").rstrip()


def _block(text: str) -> list[str]:
    """The lines between the markers, or a refusal that says which way it failed."""
    lines = [_QUOTE_RX.sub("", raw).rstrip() for raw in text.splitlines()]
    starts = [n for n, line in enumerate(lines) if _BEGIN_RX.match(line)]
    ends = [n for n, line in enumerate(lines) if _END_RX.match(line)]

    if not starts:
        raise Refused(
            "there is no submission block in what was pasted. The prompt asks "
            f"for one, opening with a line reading {BEGIN!r}. Paste the whole "
            "reply, marker lines included: prose around the block is read past "
            "and costs nothing, and the markers are the only thing this looks "
            "for."
        )
    if len(starts) > 1:
        raise Refused(
            f"{len(starts)} submission blocks were pasted, and they are "
            f"{len(starts)} different submissions as far as this can tell. Paste "
            "one. Picking between them here would be this tool deciding which "
            "of your author's answers is the one they meant."
        )

    start = starts[0]
    after = [n for n in ends if n > start]
    if not after:
        return lines[start + 1:]
    return lines[start + 1:after[0]]


def _pairs(lines: list[str]) -> tuple[list[tuple[str, str]], list[str]]:
    """Every `key: value` in the block, in order, plus notes about how they read.

    Three spellings of a multi-line value are taken, because the format asks for
    one and an agent produces whichever its training suggests: the `<<<` block
    the prompt specifies, a YAML-style `|` with the lines indented under it, and
    a bare key whose value is on the indented lines below. The first is
    unambiguous and the other two are guesses about intent, which is why an
    empty value with nothing indented under it is a refusal rather than a
    fourth guess.
    """
    pairs: list[tuple[str, str]] = []
    notes: list[str] = []
    n = 0
    while n < len(lines):
        raw = lines[n]
        n += 1
        line = _peel(raw)
        if (not line.strip() or _FENCE_RX.match(line)
                or line.strip() in _PUNCTUATION_ONLY
                or set(line.strip()) <= {"=", "-", "_"}):
            continue

        match = _KEY_RX.match(line)
        if not match:
            # A wrapped line. Chat windows wrap at seventy-odd characters and a
            # reason that runs past that arrives as prose under its own field,
            # so the tail is joined back on rather than dropped. An unindented
            # tail is joined too and said out loud, because the other thing it
            # could be is a stray sentence somebody left inside the block.
            if pairs:
                last_key, last_value = pairs[-1]
                pairs[-1] = (last_key, f"{last_value} {line.strip()}".strip())
                if not raw.startswith((" ", "\t")):
                    notes.append(
                        f"{line.strip()!r} was read as the rest of {last_key}"
                    )
                continue
            notes.append(f"read past a line that is not a field: {line.strip()!r}")
            continue

        key, value = _unquote(match.group(1), match.group(2))

        if value in (OPEN_BLOCK, "|", ">") or (
            not value and n < len(lines) and lines[n].strip() == OPEN_BLOCK
        ):
            if not value:
                n += 1
                value = OPEN_BLOCK
            body, n = _gather(lines, n, fenced=value == OPEN_BLOCK, key=key,
                              answered=_answered(pairs), notes=notes)
            pairs.append((key, body))
            continue

        if not value:
            body, n = _gather(lines, n, fenced=False)
            if body:
                pairs.append((key, body))
                continue

        pairs.append((key, value))
    return pairs, notes


def _unquote(key: str, value: str) -> tuple[str, str]:
    """A key and a value with JSON's punctuation taken off, and nothing else.

    The trailing comma goes only when what is left is a quoted string or a bare
    number, which is the two shapes JSON writes and is narrow enough that a
    license ending in a comma, or a definition that does, keeps it. Wrapping
    quotes go when both ends have them, so a value that merely opens with a
    quoted phrase is left alone.
    """
    key = key.strip().strip("\"'")
    value = value.strip()
    if value.endswith(","):
        without = value[:-1].rstrip()
        quoted = len(without) > 1 and without[0] == without[-1] and without[0] in "\"'"
        if quoted or _NUMBER_RX.match(without):
            value = without
    if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return key, value.strip()


def _answered(pairs: list[tuple[str, str]]) -> frozenset[str]:
    """The fields already given a value above here, by the name this form uses.

    Read at the point a fence opens rather than at the end, because that is the
    question `_eaten` asks: of the names appearing below this `<<<`, which ones
    had not been answered yet, and are therefore lines the fence swallowed
    rather than the author's own prose.
    """
    return frozenset(
        BY_NAME[name].name for key, _ in pairs
        if (name := _key(key)) in BY_NAME
    )


def _eaten(lines: list[str], opened: int, answered: frozenset[str]) -> list[str]:
    """Fields an unclosed fence swallowed, which is what tells the two cases apart.

    Only names this form knows, because a definition is prose and its prose has
    colons in it: every "Estimator:" and "On verdicts:" inside the swallowed
    block matches the key pattern too, and listing those back would bury the
    ones that matter in the author's own sentences. Case-sensitively, so a
    sentence opening "Position: ..." is prose and `position:` is a field.

    And only names nothing above the fence answered. Every other field is
    written before the definition now, so a line inside the definition spelled
    like one of them is the author's prose by construction. That narrowing is
    what the reordering bought: without it, an author whose theory of a trait
    happens to contain a line reading `model: ...` would be refused for it.
    """
    known = {spec.name for spec in SPECS}
    known.update(alias for spec in SPECS for alias in spec.aliases)
    known.add("not-found")
    found: set[str] = set()
    for line in lines[opened:]:
        match = _KEY_RX.match(line)
        if not match or match.group(1) not in known:
            continue
        name = match.group(1)
        name = BY_NAME[name].name if name in BY_NAME else name
        if name not in answered:
            found.add(name)
    return sorted(found)


def _gather(lines: list[str], n: int, *, fenced: bool, key: str = "",
            answered: frozenset[str] = frozenset(),
            notes: list[str] | None = None) -> tuple[str, int]:
    """A multi-line value from `n` on: to the closing marker, or while indented.

    Nothing is peeled inside a fenced body. A definition is prose and its
    asterisks, backticks and leading dashes are the author's.

    **A `<<<` with nothing after it is closed by the end of the submission.**
    Opening a delimiter and forgetting to close it is among the most common
    things a model does with one, and the first three real uses of this handoff
    all did it on the definition. So the template puts the one unbounded value
    last and this accepts the end of input as its terminator: nothing follows
    it, so nothing is lost, and the submitter is told what was decided rather
    than left to assume a marker was read. Closing at the next line that looks
    like a key would be the other thing, and it is not done here: that is a
    guess about where somebody's prose ends and it can truncate it.

    **A `<<<` that swallowed fields is still refused.** If the fence was not
    last, what ran to the end of the submission took every field below it, and
    the row that arrives at the caller is missing all of them. That reported as
    seven required fields being absent, which is true, useless, and points at
    the wrong end of the paste: the author's agent wrote all seven and one
    missing marker ate them. Said here because this is the only place that
    knows the fence never closed, and the two cases are told apart by whether
    anything the form takes and nobody had answered sits inside the body.
    """
    opened = n
    body: list[str] = []
    while n < len(lines):
        raw = lines[n]
        if fenced:
            if raw.strip() == CLOSE_BLOCK:
                n += 1
                break
            body.append(raw)
            n += 1
            continue
        if not raw.strip():
            if body:
                body.append("")
            n += 1
            continue
        if not raw.startswith((" ", "\t")):
            break
        body.append(_peel(raw).strip())
        n += 1
    else:
        if fenced:
            eaten = _eaten(lines, opened, answered)
            if eaten:
                raise Refused(
                    f"{key or 'a value'} opened with {OPEN_BLOCK} and nothing "
                    f"closed it, so it ran to the end of the submission and "
                    f"took everything after it with it, including "
                    f"{', '.join(eaten)}. Put {CLOSE_BLOCK} on a line of its "
                    f"own where the value ends. Nothing else about the paste "
                    f"is wrong. The template asks for the definition last, "
                    f"below every other line, because there a missing "
                    f"{CLOSE_BLOCK} costs nothing; this one had fields after "
                    f"it."
                )
            if notes is not None:
                notes.append(
                    f"{key or 'a value'} opened with {OPEN_BLOCK} and nothing "
                    f"closed it. It is the last thing in the submission, so "
                    f"the end of the submission closed it and nothing was "
                    f"lost: every line from the {OPEN_BLOCK} to the end is the "
                    f"value. Put {CLOSE_BLOCK} on a line of its own if part of "
                    f"that was meant to be something else."
                )
    return "\n".join(body).strip("\n").rstrip(), n


def _absence(value: str) -> tuple[str, str]:
    """A `not-found:` line as the field it names and the reason given for it."""
    parts = value.strip().split(None, 1)
    if not parts:
        raise Refused(
            "a not-found line names no field. It takes the field name and then "
            "why the value is absent, and both halves are the point: a field "
            "nobody recorded and a field nobody looked for are different "
            "states, and only the reason tells them apart."
        )
    name = _key(parts[0])
    reason = parts[1].strip() if len(parts) > 1 else ""
    # The separator an agent puts between the field and the reason, in every
    # spelling a chat window produces, dashes included.
    reason = reason.lstrip(":-–— ").strip()
    if _placeholder(parts[0]) or _placeholder(reason):
        raise Refused(
            f"a not-found line still reads {value.strip()!r}, which is the "
            "template rather than an answer. It takes the name of the field "
            "that has no value and the reason it has none."
        )
    if not reason:
        raise Refused(
            f"not-found names {name} with no reason. Write why it is absent, "
            "even if the reason is that the extraction never recorded it. The "
            "reason is what a reader sees in place of the value, and it is what "
            "separates an absence from an omission."
        )
    return name, reason


def _key(raw: str) -> str:
    return re.sub(r"[ .\-]+", "_", raw.strip().strip(":").lower())


def _placeholder(value: str) -> bool:
    """Whether a value is still the template's angle brackets or a stub.

    Newlines included, because the one field whose placeholder spans two lines
    is the definition, and the definition is the field this is protecting: a
    template that reads as prose is the likeliest thing to survive a careless
    pass and the least likely thing to be noticed in a form.
    """
    stripped = value.strip()
    if stripped.startswith("<") and stripped.endswith(">"):
        return True
    return stripped.lower() in {"todo", "tbd", "...", "n/a", "na", "none", "null",
                                "unknown", "?", "-", "--"}


def _cast(spec: Spec, value: str) -> str:
    """The value as it goes into the form, or a refusal saying why it cannot.

    Checked and passed on as written, never rewritten: a coefficient typed as
    `1e-2` reaches the row as the author spelled it. What this establishes is
    that `artifacts/intake.py` will take it, on the same rules, one step earlier,
    where the person who can fix it is still looking at the paste.
    """
    if spec.cast == "integer":
        try:
            int(value)
        except ValueError:
            raise Refused(
                f"{spec.name} is stored as an integer and {value!r} is not one. "
                "A hook that is not at a layer is a kind of artifact this column "
                "cannot describe, which is worth saying out loud rather than "
                "rounding into it."
            ) from None
    elif spec.cast == "number":
        try:
            float(value)
        except ValueError:
            raise Refused(
                f"{spec.name} is stored as a number and {value!r} is not one. "
                "Leave it out with a not-found line if it was never measured: "
                "the column is nullable and an absence records as an absence."
            ) from None
    elif spec.cast == "commit":
        try:
            fetch.commit_sha(value.strip())
        except fetch.FetchError as refused:
            raise Refused(f"{spec.name}: {refused}") from refused
    return value


def parse(text: str) -> Handoff:
    """One paste in, the form's fields out, or `Refused` naming what was wrong.

    The strict half, in order: a value that is still a placeholder out of the
    template, a field answered twice differently, a field the schema cannot
    write a row without, and a number that is not one. Each is a refusal rather
    than a guess, because every one of them is a case where guessing produces a
    row that looks exactly like a correct one.
    """
    if not (text or "").strip():
        raise Refused("nothing was pasted.")

    cleaned, retyped = _normalize(text)
    pairs, notes = _pairs(_block(cleaned))
    if retyped:
        notes.append("typographic quotes and invisible spaces were replaced with "
                     "their plain equivalents")

    values: dict[str, str] = {}
    absent: dict[str, str] = {}
    extra: dict[str, str] = {}
    seen: dict[str, str] = {}

    for raw_key, raw_value in pairs:
        key = _key(raw_key)

        if _ABSENT_RX.match(key):
            name, reason = _absence(raw_value)
            if name in BY_NAME:
                name = BY_NAME[name].name
            absent[name] = reason
            continue

        if not raw_value.strip():
            raise Refused(
                f"{key} was given with nothing after the colon. An empty value "
                "is either a field you could not find or one you meant to fill, "
                "and this cannot tell which. Write the value, or a not-found "
                "line naming the field and why it is absent."
            )

        if _placeholder(raw_value):
            raise Refused(
                f"{key} still reads {raw_value.strip()!r}, which is the "
                "placeholder from the prompt rather than an answer. Either it "
                "was never filled in or it was filled with a stub; both are the "
                "same problem. Delete the line and add a not-found for the "
                "field, or go and read the value."
            )

        spec = BY_NAME.get(key)
        if spec is None:
            extra[key] = raw_value
            continue

        if spec.name in seen and seen[spec.name] != raw_value:
            raise Refused(
                f"{spec.name} was answered twice, as {seen[spec.name]!r} and "
                f"{raw_value!r}. Which one is right is a question for whoever "
                "wrote them."
            )
        seen[spec.name] = raw_value

        checked = _cast(spec, raw_value)
        for form_field in spec.form:
            values[form_field] = checked

    both = sorted(set(absent) & set(seen))
    if both:
        raise Refused(
            f"{', '.join(both)} came back with a value and a not-found line. "
            "One of the two is wrong and this has no way to tell which."
        )

    missing = [s.name for s in SPECS if s.cannot_be_absent and s.name not in seen]
    if missing:
        declared = [name for name in missing if name in absent]
        raise Refused(
            "the schema cannot write a row without "
            + ", ".join(missing)
            + ". "
            + (f"{', '.join(declared)} came back as not-found, and a not-found "
               "does not help here: these are the columns the row is made of, "
               "so an absent one is no row rather than a recorded absence. "
               if declared else "")
            + "Everything else is nullable and an absence in it is a state. "
              "Go back with what is missing named."
        )

    if extra:
        notes.append(
            "no field in this form takes " + ", ".join(sorted(extra))
            + ", so they are shown rather than dropped: put anything worth "
              "keeping into the definition, or record it in the recipe payload."
        )
    if values.get("link_repo") and not values.get("link_commit"):
        notes.append(
            "a repo came back with no commit, so nothing is pinned yet. A "
            "branch is not a pin: resolve it to the forty hex characters it "
            "points at now, or take the bytes route and let the upload make "
            "the commit that gets recorded."
        )
    elif not values.get("link_repo"):
        notes.append(
            "no published repo and commit came back, so this is the bytes "
            "route: the file goes up to the author's own namespace from here "
            "and the commit that upload makes is what gets recorded."
        )

    return Handoff(values=values, absent=absent, extra=extra, notes=notes)


def stored_absences(absent: dict[str, str]) -> dict[str, str]:
    """Declared absences keyed by the column the row stores, not the name asked for.

    One translation, in the module that owns the three spellings. A name this
    document does not know passes through untouched, which is the point: the
    field side of an absence is an open string and a table of the ones we happen
    to have met would be a list of which fields are allowed an explanation.
    """
    return {BY_NAME[name].stored if name in BY_NAME else name: reason
            for name, reason in absent.items()}


def received(text: str) -> dict:
    """One paste as the payload the form's paste region renders.

    Shaped like `artifacts/intake.py`'s other JSON answers: `display` is pairs
    the panel prints verbatim, and `fields` is keyed by `data-field` so the page
    fills its own inputs without knowing any of the names above.

    `absent` is keyed by the column instead, because unlike `fields` it is not
    filled into an input: it travels through the page to `/write` and lands in
    the row as it stands. The page posting back a second spelling of a field
    name is how the reason would get written against a field nothing else calls
    by that name.
    """
    got = parse(text)
    return {
        "fields": got.values,
        "absent": stored_absences(got.absent),
        "pinned": got.pinned,
        "display": got.display(),
        # Everything the parser had to decide rather than read. These were
        # computed and then dropped here, so a definition closed one sentence
        # in reported as "19 fields filled" while two thirds of it had been
        # re-read as the rest of six fields nobody asked for. A paste that
        # parses is not the same as a paste that was understood, and the
        # difference is exactly this list.
        "notes": got.notes,
    }
