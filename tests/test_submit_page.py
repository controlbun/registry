"""`/submit/`: the two ways to build a submission, and the one that is not
checked here.

Premise, restated because a premise stated in one file gets violated in every
other one: **plurality is the product, the registry never designates, and
consumers pin visibly.** Nothing on this page ranks, scores, approves or filters
a submission. There is no queue and there is nothing to approve: the namespace is
the handle the provider reported, so there is no question for a reviewer to
answer.

**This file is a split out of `tests/test_signed_in_page.py`, taken on
2026-09-20 with the page.** What moved is everything about the submission: the
record the browser builds, what the built page says about where it goes, and the
upload offer. What stayed there is the return leg, the capture and the session.
The split is the same one the pages took and for the same reason: the bar's
**Add artifact** pointed at the return leg, so pressing it mid-sign-in reloaded
that page and discarded the exchange.

**The two routes, and the asymmetry between them.** Fields are checked in the
browser as they are typed. A paste is not checked here at all: it crosses as
text, and `artifacts/agent_handoff.py` parses it on the author's machine when
the row is pulled in. So the tests below assert that nothing in the view layer
reads a paste, and that the page says so in those words. A check here would be
the first line of a second parser, and two parsers that drift is the failure
this repository keeps catching.

**The prompt is generated, and this file is what stops it drifting.** The built
page has to carry exactly `agent_handoff.prompt(suggestions(conn))` for this
corpus. Not something like it.

**Every test that touches the network is absent on purpose.** `make verify` runs
from a clean checkout with no network.

No number in this file is a measurement. The commit is forty letter `a`s, which
is forty hex characters and not a commit anybody made, and the model id in the
fixtures does not need to resolve because nothing here fetches.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"
SRC = ROOT / "astro" / "src"
PAGE = SRC / "pages" / "submit.astro"
HANDSHAKE = SRC / "lib" / "handshake.mjs"
HELD = SRC / "lib" / "held.mjs"
PROMPT_DATA = SRC / "data" / "agent-prompt.json"
BUILT = DIST / "submit" / "index.html"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "artifacts"))

import agent_handoff  # noqa: E402
import intake  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

import played_harness as played  # noqa: E402

# Run against the real module rather than a restatement of it, same as the page
# tests next door. Imported rather than copied, because a second implementation
# in a test is the same failure as a second implementation in the product, one
# layer out and harder to notice.
from test_signed_in_page import reachable_scripts, run_js  # noqa: E402


# --------------------------------------------------------------------------- #
# The record the browser builds, route one: the fields.


def a_form(**over):
    form = {
        "label": "pro-human", "version": "meandiff",
        "created_at": "2026-09-01", "definition": "what the author means by it",
        "intervention_id": "iv-1", "kind": "difference-in-means",
        "model_id": "allenai/Olmo-3-1125-32B", "layer": "31",
        "layer_convention": "block-0indexed", "hook_point": "resid_post",
        "repo": "someone/direction", "commit": "a" * 40,
        "path": "direction.safetensors",
    }
    form.update(over)
    return form


def submission(form, handle="sohampadia"):
    return run_js(
        f"return h.submissionFrom({json.dumps(form)}, {{capture: "
        f'{{preferred_username: {json.dumps(handle)}, provider: "custom:huggingface",'
        ' sub: "opaque"}, submittedAt: "2026-09-20T00:00:00Z"});'
    )


def test_the_namespace_is_the_handle_and_no_field_can_override_it():
    """`DECISIONS.md` 2026-09-19: shown, not offered. A pre-filled default was
    considered and rejected, because somebody who has decided to take a name
    clears the field and types it. The only version that does anything is the
    one with no field, so a value called `author` in the form has to be ignored
    rather than preferred."""
    out = submission(a_form(author="meta", namespace="meta"), handle="qwen-fan")
    assert out["author"] == "qwen-fan"
    assert "namespace" not in out


def test_a_submission_with_no_handle_is_refused_rather_than_defaulted():
    with pytest.raises(AssertionError) as refused:
        submission(a_form(), handle="")
    assert "no field to type one into" in str(refused.value)


def test_a_branch_or_a_tag_cannot_be_pinned():
    """Forty hex characters, which is `controlbun.fetch.commit_sha`'s one rule
    stated in the same words. A tag is movable by whoever owns the repository,
    so a pin naming one would resolve to different bytes later while the digest
    beside it kept claiming otherwise."""
    for bad in ("main", "v1.0", "a" * 39, "z" * 40):
        with pytest.raises(AssertionError) as refused:
            submission(a_form(commit=bad))
        assert "40-character commit sha" in str(refused.value)


def test_the_bytes_never_go_to_this_registry_s_own_namespace():
    """`publish.ServedCopy` refuses this on the author's machine and the reason
    is in `schema/migrations/004`: `artifact_repo` is where an author published
    and `served_repo` is where this registry serves a copy from, and one pair of
    columns cannot express a mirror that has drifted from its origin. The two
    callers are now on different computers, so the rule is in both."""
    for bad in ("controlbun/x", "CONTROLBUN/x"):
        with pytest.raises(AssertionError) as refused:
            submission(a_form(repo=bad))
        assert "004_served_copy" in str(refused.value)
    # And a namespace that merely contains the word is fine.
    assert submission(a_form(repo="controlbunny/x"))["artifact"]["repo"] == \
        "controlbunny/x"


def test_no_tensor_fact_is_computed_in_the_browser():
    """One thing in this project reads bytes. A second implementation of shape,
    dtype, norm and digest in JavaScript is the failure this repository has hit
    more often than any other, so the record crossing is the pointer and the
    contract and the facts are derived where the corpus is rebuilt."""
    out = submission(a_form())
    # The intervention is where a tensor fact would land, and `shape` at the
    # top level is this record's own versioned shape rather than a tensor's.
    for derived in ("sha256", "l2_norm", "dtype", "shape", "size"):
        assert derived not in out["intervention"], (
            f"{derived} is in a submission built in the browser, which means "
            "something there is reading bytes and deciding what they say"
        )
    assert "artifact_sha256" not in json.dumps(out["artifact"])
    assert HANDSHAKE.read_text().count("safetensors") == 0


def test_an_absence_is_a_sentence_and_an_empty_one_is_not_recorded():
    out = submission(a_form(absent={
        "chat_template_hash": "no hash of the template string is computed anywhere",
        "activation_norm": "   ",
        "a_field_nobody_has_met": "and the field side takes any string",
    }))
    assert set(out["absent"]) == {"chat_template_hash", "a_field_nobody_has_met"}


def test_the_optional_fields_are_absent_rather_than_empty_strings():
    """Absence renders as absence. A row carrying "" where nobody said anything
    is a value somebody has to read as a blank, which is the state
    `schema/migrations/005` and `007` both refuse."""
    out = submission(a_form())
    iv = out["intervention"]
    for field in ("model_revision", "chat_template_hash", "steering_position",
                  "license_status"):
        assert iv[field] is None
    for field in ("activation_norm", "coeff_low", "coeff_high"):
        assert iv[field] is None
    assert out["artifact"]["host"] is None
    assert out["artifact"]["url_template"] is None


def test_nothing_in_the_submission_is_a_score_or_an_order():
    out = submission(a_form())
    # Key names, not the whole blob, and `status` is deliberately not on the
    # list below. `license_status` is a field an author asserts about a source
    # model's license, and a substring scan reads it as a review state, which
    # is the trap `CLAUDE.md` names: a grep catching the word rather than the
    # meaning.
    keys = set(out) | set(out["intervention"]) | set(out["artifact"])
    for forbidden in ("rank", "score", "rating", "quality", "approved",
                      "reviewed", "tier", "sort", "order", "count"):
        assert not any(forbidden in key for key in keys), (
            f"a submission carries a key containing {forbidden!r}: "
            f"{sorted(k for k in keys if forbidden in k)}"
        )


# --------------------------------------------------------------------------- #
# Route two: the paste, which crosses unread.


# One block, shaped the way the prompt asks for it, built from the marker
# constants rather than from a copy of them. Everything the schema cannot write
# a row without, plus the pin, and nothing else: an optional field is added by
# whichever test is about it.
PASTE_FIELDS = {
    "author": "sohampadia",
    "label": "pro-human",
    "version": "meandiff",
    "created_at": "2026-09-01T00:00:00Z",
    "intervention_id": "iv-1",
    "kind": "difference-in-means",
    "model_id": "allenai/Olmo-3-1125-32B",
    "layer": "31",
    "layer_convention": "block-0indexed",
    "hook_point": "resid_post",
    "artifact_path": "direction.safetensors",
    "artifact_repo": "someone/direction",
    "artifact_commit": "a" * 40,
}


def paste_text(*, extra: str = "", drop: tuple[str, ...] = (), **over) -> str:
    """What a coding agent produced, as text and nothing more structured.

    The definition goes in the `<<<` block the prompt specifies, because it is
    the one field that is prose and the one whose format matters.
    """
    fields = {**PASTE_FIELDS, **over}
    lines = [f"{name}: {value}" for name, value in fields.items()
             if name not in drop]
    lines.append(
        "definition: " + agent_handoff.OPEN_BLOCK
        + "\nA synthetic definition written by the test suite.\n"
        + agent_handoff.CLOSE_BLOCK
    )
    if extra:
        lines.append(extra)
    body = "\n".join(lines)
    return (
        "I read the extraction script and its config. Here is the block.\n\n"
        f"{agent_handoff.BEGIN}\n{body}\n{agent_handoff.END}\n"
    )


def paste_record(text: str, handle: str = "sohampadia") -> dict:
    """The record the page builds from a paste, through the real function."""
    return run_js(
        f"return h.pasteFrom({json.dumps(text)}, {{capture: "
        f'{{preferred_username: {json.dumps(handle)}, provider: "custom:huggingface",'
        ' sub: "opaque"}, submittedAt: "2026-09-20T00:00:00Z"});'
    )


def test_a_paste_crosses_as_text_and_nothing_in_the_browser_reads_it():
    """The property the whole arrangement rests on.

    The record carries the paste, the three identity fields and when it was
    built. No field is extracted, no marker is looked for and no judgment is
    made, because `agent_handoff.parse` is the one implementation of that and
    it is in Python.
    """
    record = paste_record(paste_text())
    assert set(record) == {"shape", "submitted_at", "provider", "subject",
                           "author", "pasted"}
    assert record["shape"] == "controlbun.registry/agent-paste@1"
    assert record["shape"] == intake.AGENT_PASTE, (
        "the browser and the reader disagree about what shape a paste is"
    )
    assert record["author"] == "sohampadia"
    assert agent_handoff.BEGIN in record["pasted"]
    # The prose around the block travels too. `parse` reads past it, and
    # trimming it here would be this file deciding what part of somebody's
    # reply is the answer.
    assert record["pasted"].startswith("I read the extraction script")


def test_a_paste_the_parser_will_refuse_still_crosses_unexamined():
    """Which is the cost, stated as a test rather than as a sentence.

    Something with no block in it at all is sent, lands in the holding table,
    and is refused when the author pulls it. A check here would be the first
    line of the second parser.
    """
    record = paste_record("there is no block in this at all")
    assert record["pasted"] == "there is no block in this at all"
    with pytest.raises(agent_handoff.Refused):
        agent_handoff.parse(record["pasted"])


def test_an_empty_paste_is_the_one_thing_the_page_will_not_send():
    """Not a check on the content. A box nobody typed in is nothing to send,
    which is a fact about the press rather than a judgment about the text."""
    with pytest.raises(AssertionError) as refused:
        paste_record("   \n  ")
    assert "nothing to send" in str(refused.value)


def test_a_paste_and_filled_fields_together_is_refused_and_neither_wins():
    """The rule this project already applies where one field carries both a
    value and a reason for having none, applied to a whole submission.

    Named rather than counted: the sentence says what is filled in as well as
    the paste, so whoever wrote them decides which to clear. Nothing is
    preferred and nothing is dropped.
    """
    said = run_js(
        "try { h.chosenRoute({label: 'pro-human', version: 'meandiff'},"
        " 'a paste'); return null; }\n"
        "catch (problem) { return problem.message; }"
    )
    assert "label" in said and "version" in said
    assert "nothing here can tell which was meant" in said
    assert "neither is sent and nothing is preferred" in said


def test_an_absence_counts_as_filling_the_fields_in():
    """An absence is a positive statement about a field, so it belongs to the
    route that makes statements field by field. An agent writes its own on the
    `not-found:` lines the prompt asks for."""
    said = run_js(
        "try { h.chosenRoute({absent: {layer: 'the log records none'}},"
        " 'a paste'); return null; }\n"
        "catch (problem) { return problem.message; }"
    )
    assert "a reason for layer being absent" in said


def test_the_upload_offer_belongs_to_the_field_route_and_does_not_count_alone():
    """It fills three fields in, which is what makes it part of that route, and
    the flag it sets is a fact about how the bytes got there rather than
    something somebody typed. A flag on its own is not two accounts of
    anything."""
    assert run_js(
        "return h.chosenRoute({uploaded_by_registry: true}, 'a paste');"
    ) == "paste"


def test_neither_one_nor_the_other_says_what_to_do():
    said = run_js(
        "try { h.chosenRoute({}, ''); return null; }\n"
        "catch (problem) { return problem.message; }"
    )
    assert "nothing is filled in and nothing is pasted" in said
    assert "copy the prompt" in said


# --------------------------------------------------------------------------- #
# The prompt, which is generated and must not drift.


def built() -> str:
    if not BUILT.exists():
        pytest.skip("site not built; run `make site`")
    return BUILT.read_text()


def bundle() -> str:
    """Everything the page's script loads, the chunks it imports included.

    `reachable_scripts` is imported rather than restated for the reason the
    helpers above it are: a second implementation in a test is the same failure
    as a second one in the product.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    text = "".join(path.read_text() for path in reachable_scripts(built()))
    assert text, "the page ships no script, so there is nothing that sends"
    return text


def text_of(page: str) -> str:
    for tag in ("script", "style"):
        page = re.sub(rf"<{tag}.*?</{tag}>", "", page, flags=re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", page).split())


def prompt_on_the_page() -> str:
    """The prompt as the built page carries it, unescaped.

    Read out of the rendered HTML rather than out of the data file, because the
    data file is the input and the question is what a reader can copy. The
    button copies this element's `textContent`, which is what the browser gives
    back after it undoes the entity encoding, and `html.unescape` is that
    operation here.
    """
    found = re.search(
        r'<pre id="agent-prompt-text"[^>]*>(.*?)</pre>', built(), re.S,
    )
    assert found, "the built page carries no prompt element"
    return html.unescape(found.group(1))


def test_the_prompt_on_the_page_is_the_one_the_module_builds():
    """The whole of why the prompt is generated rather than written into the
    template.

    `agent_handoff.prompt` is a pure function of the field list and what this
    corpus already holds, and the parser on the other end was written against
    it. A second copy in an Astro page would go stale the first time a field
    was added, and the failure would be silent: an agent answering the old
    prompt, a parser refusing a field the reader was never asked for.
    """
    if not (ROOT / "registry.db").exists():
        pytest.skip("no corpus; run `make site`")
    conn = sqlite3.connect(ROOT / "registry.db")
    conn.row_factory = sqlite3.Row
    try:
        wanted = agent_handoff.prompt(intake.suggestions(conn))
    finally:
        conn.close()

    generated = json.loads(PROMPT_DATA.read_text())["prompt"]
    assert generated == wanted, (
        "astro/src/data/agent-prompt.json is stale. It is written by "
        "`artifacts/intake.py prompt` during `make site`."
    )
    assert prompt_on_the_page() == wanted, (
        "the built page carries a prompt that is not the one the module "
        "builds, so what a reader copies and what the parser reads have come "
        "apart"
    )


def test_the_page_holds_no_second_copy_of_the_prompt():
    """The edit this would lose to: somebody pastes the text into the template
    because the import looked indirect."""
    source = PAGE.read_text()
    assert "agent-prompt.json" in source, "the page no longer reads the built file"
    for sentence in ("Never write a value you did not read",
                     agent_handoff.BEGIN):
        assert sentence not in source, (
            f"{sentence!r} is typed into the page as well as generated"
        )


def test_the_prompt_is_a_build_step_and_not_a_manual_one():
    """A generated file that nothing regenerates is a file somebody edits by
    hand once and forgets. It is in the same target as the export it sits
    beside."""
    make = (ROOT / "Makefile").read_text()
    site = re.search(r"^site:\n(.*?)(?=\n\w)", make, re.S | re.M)
    assert site, "there is no site target"
    assert "intake.py prompt" in site.group(1)


def test_the_reader_can_read_the_prompt_before_running_it():
    """It is text somebody is about to hand to an agent with their files open.
    A copy button with nothing to read beside it asks for more trust than this
    page is owed."""
    assert 'id="copy-prompt"' in built()
    assert "Read the prompt first" in built()


# --------------------------------------------------------------------------- #
# What the built page says, and does not do.


def test_the_page_says_plainly_that_a_paste_is_not_checked_until_it_is_pulled():
    """The difference between the two routes, said without softening.

    The field route surfaces a mistake as somebody types. The paste route
    cannot, because the parser is on the author's machine, and a page that let
    somebody assume otherwise would be trading their time for the appearance of
    a check.
    """
    body = text_of(built()).lower()
    assert "a paste is not checked until the author pulls it in" in body
    assert "nothing in this browser reads what you paste" in body
    assert "by mail" in body, (
        "the page does not say how a refusal reaches somebody, which is the "
        "part that makes the delay concrete"
    )
    assert "two of them drift" in body or "two parsers" in body or \
        "two of them" in body, "the page does not say why there is one parser"


def test_the_page_says_pasting_and_filling_at_once_is_refused():
    body = text_of(built()).lower()
    assert "pasting and filling the fields in at once is refused" in body
    assert "neither is preferred" in body


def test_the_page_receives_nothing_and_submits_no_form():
    """The structural criterion, applied to the one page that would break it
    first. A field that holds what somebody typed is not a target; a form with
    somewhere to send it is. This page has the first and not the second."""
    page = built()
    assert "<input" in page, "the submission form has no fields, so there is none"
    for receiving in (r"<form\b", r"\bformaction\b", r"\baction\s*=", r"\benctype\b"):
        assert not re.search(receiving, page, re.I), (
            f"{receiving} is on the page, which means something submits"
        )


def test_the_page_says_a_submission_does_not_appear_until_it_is_published():
    """The sentence that keeps this honest. The corpus is a file in git and the
    site is built from it on one machine, which is what lets the falsifier check
    the build readers actually read."""
    body = text_of(built()).lower()
    assert "does not appear on this site until the author rebuilds and publishes" in body
    assert "file in git" in body


def test_the_page_sends_the_submission_to_the_holding_table():
    """The form posts. Downloading is a copy for the person who made it and is
    no longer how anything gets here, which the page has to say in the same
    place it offers the download."""
    code = bundle()
    assert "/rest/v1/pending_submission" in code, (
        "the page no longer sends anything, or sends it somewhere this test "
        "has not read"
    )
    page = built()
    assert 'id="send-record"' in page, "there is no button that sends"
    assert 'id="keep-record"' in page, "the download went away rather than moving"


def test_the_page_says_the_identity_on_the_row_is_stamped_and_not_typed():
    """The property the whole design rests on, said to the person it protects.

    A submitter has to be able to tell that their handle is not a field
    somebody else could fill in, because that is the difference between this
    and a form where anybody can publish as anybody.
    """
    body = text_of(built()).lower()
    assert "taken from your signed session by the database" in body
    assert "cannot claim to be from somebody it is not" in body


def test_the_receipt_is_read_off_the_answer_and_not_off_what_was_sent():
    """Showing a fact rather than showing a hope. `Prefer: return=representation`
    is why there is an answer to read, and the four fields shown come out of it.
    """
    source = PAGE.read_text()
    for field in ("written.received_at", "written.id", "written.handle",
                  "written.subject"):
        assert field in source, f"the receipt does not show {field}"
    body = text_of(built()).lower()
    assert "what the database wrote, read back off its answer" in body


def test_the_page_offers_no_queue_and_nothing_to_approve():
    """The thing a holding table turns into if nobody watches. `DECISIONS.md`
    2026-09-17 records why a review step with no stated rule fills with the
    reviewer's taste, and the namespace being the handle is why there is no
    question to ask in the first place."""
    body = text_of(built()).lower()
    assert "nothing to approve" in body
    # `position` alone is not on this list, and the reason is the trap
    # `CLAUDE.md` names: `steering_position` is a field on every intervention
    # here, so the bare substring flags the form for containing the schema. The
    # queue is "your position", not a column called position.
    for queueing in ("pending review", "awaiting approval", "in the queue",
                     "your position", "position in", "your turn", "under review",
                     "will be reviewed", "once approved", "moderat"):
        assert queueing not in body, f"{queueing!r} is a queue arriving in prose"


def test_the_page_names_what_the_handle_rule_makes_impossible():
    """A rule that cannot name its cost has not been thought through."""
    body = text_of(built()).lower()
    assert "pseudonym" in body
    assert "no field for it" in body


def test_the_upload_offer_says_whose_account_the_bytes_go_to():
    body = text_of(built()).lower()
    assert "your own account" in body
    assert "never to this project" in body
    assert "one more permission at that point and not before" in body


def test_nothing_is_editable_or_withdrawable_from_the_page():
    """No update and no delete policy exists, so neither is possible through
    the publishable key. The page says so rather than offering a button that
    would fail."""
    code = bundle()
    for verb in ("DELETE", "PATCH", "PUT"):
        assert f'method: "{verb}"' not in code, (
            f"the page can {verb} a row, and the table has no policy for it"
        )
    body = text_of(built()).lower()
    assert "no way to edit or withdraw this from here" in body


def test_neither_route_offers_anything_that_reads_as_the_better_one():
    """Two ways in, and the page says neither is the real one. The reader with
    a coding agent and the reader without are both contributors here."""
    body = text_of(built()).lower()
    assert "neither is the better one" in body


def test_nothing_on_the_page_confers_a_standing():
    """Trip-wire vocabulary, on the page most likely to grow it. Submitting
    confers nothing, so a word implying it does is the word that turns a row in
    a holding table into a status.

    Whole words, and `verify` is deliberately not among them: the prompt on
    this page tells an agent to go and verify the bytes at a URL before writing
    it down, which is the verb about bytes and the opposite of a badge. The
    trap `CLAUDE.md` names is the grep that catches the word rather than the
    meaning.
    """
    body = text_of(built()).lower()
    # `approved` is deliberately not on this list either. The page says
    # "nothing was approved and nothing was ranked", which is the negation, and
    # the queue test above is what holds the forms that would be a claim.
    for claimed in ("verified", "certified", "official", "trusted",
                    "authoritative", "curated", "gold standard"):
        assert not re.search(rf"\b{claimed}\b", body), (
            f"the page says {claimed!r}"
        )


# --------------------------------------------------------------------------- #
# The session, which this page holds and does not own.


def test_the_submit_path_renews_rather_than_asking_for_a_new_authorization():
    """The press that matters most is the one most likely to land on a spent
    access token, since the page may have been open for an hour. Renewing is a
    request; re-authorizing is a redirect that loses the record on the page."""
    source = PAGE.read_text()
    assert re.search(r"const now = await usable\(", source), (
        "the send path does not renew, so a spent token is a failed submission"
    )
    renewal = re.search(r"export async function usable\(.*?\n\}", HELD.read_text(),
                        re.S)
    assert renewal, "there is no renewal before the send"
    assert "accessSpent(held)" in renewal.group(0)
    assert "refreshSession(" in renewal.group(0)
    # And it renews rather than starting an authorization, which would leave
    # the page and take the typed record with it.
    assert "authorizeUrl" not in renewal.group(0), (
        "the send path re-authorizes, which navigates away from the record"
    )


def test_the_permission_window_comes_back_through_the_registered_redirect():
    """The upload offer needs a second authorization, and the redirect URL the
    identity service knows about is `/signed-in/`. Adding a second one is a
    console change only the account holder can make, so this page does not need
    one: the window lands there, that page relays the code to whoever opened
    it, and the exchange happens here against the verifier this window wrote.
    """
    source = PAGE.read_text()
    assert 'new URL("/signed-in/", location.origin)' in source, (
        "the permission window is aimed somewhere the identity service has not "
        "been told about, so it will refuse the redirect"
    )
    signed_in = (SRC / "pages" / "signed-in.astro").read_text()
    assert "window.opener.postMessage(" in signed_in, (
        "the page the window lands on no longer relays the code, so the upload "
        "offer cannot complete from anywhere else"
    )


def test_the_page_says_nothing_about_a_session_it_cannot_check():
    """A page that is not the return leg knows one thing about a reader: what
    the session in their own browser says. It reads no page content and asserts
    nothing about who anybody is.

    **The patterns are reads and not the word.** This matched the bare
    substring `data-author` until 2026-09-20, when the page started marking a
    played-back record with `data-authored`, which is the site's own mark for
    somebody's quoted words and the one the falsifier reads on a published page
    to tell an author's number from one this registry derived. The page writing
    that attribute onto its own output is the opposite of the failure here, and
    the substring called it the failure: the trap `CLAUDE.md` names, a grep
    catching the word rather than the meaning, one more time. What matters is
    whether this page **reads** an author off a document, so the patterns below
    are the ways it could.
    """
    source = PAGE.read_text()
    for asserting in (r"data-author[\"'=\]]", r"data-owner[\"'=\]]",
                      r"dataset\.(author|owner)", r"controlbun\.json"):
        assert not re.search(asserting, source), (
            f"the page reads {asserting!r}, so it can say a reader is whoever "
            "they happen to be reading about"
        )


def test_that_narrowing_still_catches_a_page_reading_an_author():
    """The bite. A guard narrowed to let a legitimate edit through is a guard
    one character away from seeing nothing, which is the failure this
    repository has hit more than once."""
    reads = (r"data-author[\"'=\]]", r"data-owner[\"'=\]]",
             r"dataset\.(author|owner)", r"controlbun\.json")
    for bad in ('document.querySelector("[data-author]")',
                'node.getAttribute("data-owner")',
                'const who = box.dataset.author;',
                'import corpus from "../data/controlbun.json";'):
        assert any(re.search(p, bad) for p in reads), (
            f"the guard stopped seeing {bad!r}"
        )
    # And the mark the page writes on its own output is not one of them.
    for fine in ('body.setAttribute("data-authored", "");',
                 '<div class="played-body" data-authored>'):
        assert not any(re.search(p, fine) for p in reads), (
            f"the guard flags {fine!r}, which is the page quoting somebody "
            "rather than reading them"
        )


def test_no_session_in_this_browser_is_a_state_with_its_own_words():
    """Not an error and not an empty page. Somebody who arrives here without a
    session did nothing wrong, and there is one thing to do about it."""
    page = built()
    assert 'id="nosession"' in page
    body = text_of(page).lower()
    assert "there is no session in this browser" in body
    assert 'href="/sign-in/"' in page and 'href="/signed-in/"' in page


# --------------------------------------------------------------------------- #
# What this account has already sent, read back.
#
# **A record played back is the submitter's own text and it is not a corpus
# page.** Everything below is about keeping those two apart, because one design
# slip in this direction is a submission queue awaiting approval, which is the
# thing this project exists not to be.
#
# **The states the corpus gives no instance of are built here rather than
# looked for.** Nobody has sent a paste, nobody's handle has been renamed
# between a sign-in and a send, and nothing in the holding table has been read
# in. Those three are the interesting cases, so they are constructed, the same
# way `tests/probe.py` constructs the corpus states nothing real demonstrates.
# Every value in them is obviously synthetic and no number in this file is a
# measurement.


def a_row(record: dict, **over) -> dict:
    """One row as the holding table answers with it. Synthetic throughout."""
    row = {
        "id": "00000000-0000-4000-8000-000000000000",
        "received_at": "2026-09-20T00:00:00Z",
        "subject": "opaque",
        "handle": "sohampadia",
        "record": record,
        "taken_at": None,
    }
    row.update(over)
    return row


def played_back(row: dict) -> dict:
    return run_js(f"return h.playback({json.dumps(row)});")


def ordered(rows: list[dict], newest_first: bool = False) -> list[dict]:
    return run_js(
        f"return h.inArrivalOrder({json.dumps(rows)}, "
        f"{{newestFirst: {str(newest_first).lower()}}});"
    )


def names_in(shown: dict) -> set[str]:
    return {entry["name"] for group in shown["groups"] for entry in group["entries"]}


def test_a_record_plays_back_every_key_it_holds_including_one_nobody_has_met():
    """No closed enum on the way back either.

    A reader checking their own work needs what they sent, and a list of keys
    this file knows about would drop the one a record grew after it was
    written. The record is walked rather than read.
    """
    record = submission(a_form())
    record["a_key_nobody_has_met"] = "and it comes back anyway"
    shown = played_back(a_row(record))
    for name in record:
        if name in ("artifact", "intervention", "absent", "pasted"):
            continue
        assert name in names_in(shown), f"{name} was sent and does not come back"
    assert "a_key_nobody_has_met" in names_in(shown)
    # And the nested objects come back as their own groups, by the name the
    # record gave them rather than by a title this page chose.
    assert {"artifact", "intervention", "absent"} <= {
        group["name"] for group in shown["groups"] if group["name"]
    }


def test_a_value_that_was_not_sent_plays_back_as_its_own_state():
    """Absence renders as absence, which is the rule an absent eval gets. An
    empty string in its place is a value somebody has to read as a blank."""
    shown = played_back(a_row(submission(a_form())))
    intervention = next(g for g in shown["groups"] if g["name"] == "intervention")
    absent = {e["name"]: e for e in intervention["entries"] if e["state"] == "none"}
    assert "model_revision" in absent
    assert absent["model_revision"]["text"] is None


def test_a_paste_plays_back_as_text_and_nothing_here_reads_it():
    """The property the whole arrangement rests on, in the other direction.

    Sending a paste does not parse it and neither does reading it back. The
    text comes out whole, with the prose the agent wrote around it, and no
    field is extracted from it anywhere in this browser.
    """
    record = paste_record(paste_text())
    shown = played_back(a_row(record))
    assert shown["pasted"] == record["pasted"]
    assert agent_handoff.BEGIN in shown["pasted"]
    # Every field the block inside it names, and none of them became a field.
    # `author` is not among them: it is on the record's envelope as well, put
    # there by `pasteFrom` off the session, and it comes back for that reason
    # rather than by anything having read the block.
    for field in set(PASTE_FIELDS) - {"author"}:
        assert field not in names_in(shown), (
            f"{field} was read out of a paste in the browser, which is the "
            "second parser this arrangement exists to not have"
        )
    # What does come back as fields is the record's own envelope, unread.
    assert {"shape", "submitted_at", "provider", "author"} <= names_in(shown)


def test_the_stamped_identity_wins_and_the_disagreement_is_surfaced():
    """`CLAUDE.md`: where the stamped identity and the record's own copy
    disagree, the stamped one is used and the disagreement is surfaced rather
    than either being preferred silently. `artifacts/intake.py` does this when
    the author pulls the row; this does it on the page, for the person it is
    about, who is the one who can say which is right.

    Constructed, because nobody in this corpus has renamed a handle between
    signing in and sending.
    """
    record = submission(a_form(), handle="the-handle-that-was")
    shown = played_back(a_row(record, handle="the-handle-now"))
    assert shown["stamped"]["handle"] == "the-handle-now"
    assert shown["differs"] == [{
        "field": "handle",
        "stamped": "the-handle-now",
        "in_record": "the-handle-that-was",
    }]
    # And an agreeing row says nothing, because there is nothing to say.
    assert played_back(a_row(submission(a_form())))["differs"] == []


def test_playback_mints_no_reference_that_resolves():
    """`author/model_id/label@version` resolves to one frozen submission in the
    corpus, forever. A row in a holding table resolves to nothing, so printing
    the ref would be this page claiming a resolution that does not exist. The
    label and the version come back as two strings somebody typed."""
    shown = played_back(a_row(submission(a_form())))
    flat = json.dumps(shown)
    assert "@meandiff" not in flat, "a played-back record carries a version ref"
    assert "pro-human@" not in flat
    assert "sohampadia/allenai" not in flat


def test_playback_invents_no_field_of_its_own():
    """It says what is in the record. A key the record does not carry, arriving
    on the way out, would be this page asserting something about somebody's
    unpublished work."""
    record = submission(a_form())
    shown = played_back(a_row(record))
    for group in shown["groups"]:
        source = record if group["name"] is None else record[group["name"]]
        for entry in group["entries"]:
            assert entry["name"] in source, (
                f"{entry['name']} is not in the record and is on the page"
            )


def test_the_only_order_is_the_clock_and_it_reverses():
    """An order has to be something. This one is the time each row arrived,
    which is the order `intake.pending` reads them in on the author's machine,
    and reversing it changes nothing about any row."""
    rows = [
        a_row(submission(a_form(label="second")), received_at="2026-09-20T02:00:00Z"),
        a_row(submission(a_form(label="first")), received_at="2026-09-20T01:00:00Z"),
        a_row(submission(a_form(label="third")), received_at="2026-09-20T03:00:00Z"),
    ]
    at = lambda out: [row["received_at"] for row in out]
    assert at(ordered(rows)) == [
        "2026-09-20T01:00:00Z", "2026-09-20T02:00:00Z", "2026-09-20T03:00:00Z",
    ]
    assert at(ordered(rows, newest_first=True)) == list(
        reversed(at(ordered(rows)))
    )


def test_no_ordering_derives_from_anything_in_a_record():
    """The invariant `CLAUDE.md` states about eval results, applied where there
    are no eval results and somebody might reach for the next thing: a label, a
    layer, a version string, whether the author has read the row in.

    Two rows arriving at the same moment keep the order they came in, and a row
    with no arrival time is not moved for having none.
    """
    same = [
        a_row(submission(a_form(label="zzz", layer="41")), id="second",
              taken_at="2026-09-20T09:00:00Z"),
        a_row(submission(a_form(label="aaa", layer="7")), id="first"),
    ]
    assert [row["id"] for row in ordered(same)] == ["second", "first"]

    missing = [a_row(submission(a_form()), id="no-clock", received_at=None),
               a_row(submission(a_form()), id="has-one")]
    assert [row["id"] for row in ordered(missing)] == ["no-clock", "has-one"]


def joined(source: str) -> str:
    """JavaScript string concatenation, put back together.

    Every sentence a record renders is a string in the page's script, wrapped
    across lines at eighty columns. Asserting on the wrapped halves would be
    asserting on where the wrap fell.
    """
    return re.sub(r'"\s*\+\s*\n\s*"', "", source)


def test_the_page_reads_back_what_this_account_sent():
    """Read off the built bundle rather than the source, because the question
    is what the browser does. A minifier renames functions and keeps string
    literals, so the literals are what there is to assert on."""
    code = bundle()
    assert "rest/v1/pending_submission?" in code, (
        "the page no longer reads anything back, or it reads from somewhere "
        "this test has not seen"
    )
    assert "id,received_at,subject,handle,record,taken_at" in code, (
        "the read no longer names its columns, so a column added to that table "
        "later reaches this browser without anybody deciding it should"
    )
    assert "received_at.asc" in code
    assert 'id="played"' in built(), "there is nowhere for it to render"


def test_the_read_needs_only_the_policy_that_was_already_there():
    """Nothing was widened to show somebody their own rows.

    The select policy is `account = auth.uid()`: one signed-in person reads
    their own rows and nobody else's, and `auth.uid()` is null for an anonymous
    caller, so anonymous reads return an empty list. This asserts the schema
    still says that and still offers nothing wider, because a view or a policy
    for `anon` is how a holding table becomes a second corpus with none of the
    properties the first one has.
    """
    schema = (ROOT / "schema" / "supabase" / "001_pending_submission.sql").read_text()
    assert re.search(r"for\s+select\s+to\s+authenticated\s+using\s*\(\s*account\s*=\s*auth\.uid\(\)\s*\)",
                     schema, re.S), "the select policy is not the one this page relies on"
    assert not re.search(r"\bto\s+anon\b", schema), (
        "the holding table grants an anonymous role something, and reading "
        "somebody's unpublished record is not a thing a stranger does here"
    )
    assert "create view" not in schema.lower(), (
        "a view over this table is a second surface with its own policies"
    )


def test_a_played_back_record_says_where_it_cannot_be_missed_what_it_is_not():
    """Three claims, in the region and on every record rather than in a note
    under it: it is not in the corpus, nothing has checked it, and nobody else
    can read it. A long list is a thing somebody scrolls, so the banner at the
    top is not enough on its own."""
    body = " ".join(text_of(built()).split()).lower()
    assert ("none of this is in the corpus, nothing has checked it, and nobody "
            "else can read it") in body
    assert "no bytes were fetched, no paste was parsed" in body
    assert "counts toward a claimant" in body

    # And again on each record, which is drawn by the script and so is read out
    # of the page's source rather than out of the rendered body.
    source = joined(PAGE.read_text())
    assert ("Your own words, unchecked, not in the corpus, and readable by "
            "nobody else.") in source, (
        "a record on its own no longer says what it is, so a reader who "
        "scrolled past the banner has nothing"
    )


def test_a_number_in_a_played_back_record_is_marked_as_the_submitters_own():
    """The rule the falsifier enforces on a published page, applied to a page
    it cannot see.

    Every figure the site publishes is re-derived or traced, and `data-authored`
    is what marks the regions that are somebody's own words instead. A record in
    the holding table is entirely that: nothing has fetched the bytes at the
    pin, so no number in one can be re-derived, and it must not sit in the same
    grammar as a number that was.
    """
    source = PAGE.read_text()
    assert 'setAttribute("data-authored", "")' in source, (
        "a played-back record is no longer marked as the submitter's own words"
    )
    assert "asTyped(entry.text)" in source, (
        "a value renders without the quoting that says it is a string somebody "
        "typed rather than a figure anything derived"
    )
    body = " ".join(text_of(built()).split()).lower()
    assert "a number here is a number you typed" in body
    assert "cannot re-derive it" in body


def test_nothing_played_back_reads_as_a_queue():
    """The same list `test_the_page_offers_no_queue_and_nothing_to_approve`
    holds the rendered page to, applied to the page's source.

    That test reads `text_of(built())`, which strips `<script>`, and every
    sentence a record renders is a string inside one. So the copy that is most
    at risk of becoming a queue was the copy that guard could not see, which is
    the failure this repository keeps catching: a check that passes because it
    cannot look at the thing it is about.
    """
    source = PAGE.read_text().lower()
    for queueing in ("pending review", "awaiting approval", "in the queue",
                     "your position", "position in", "your turn", "under review",
                     "will be reviewed", "once approved", "moderat"):
        assert queueing not in source, f"{queueing!r} is a queue arriving in prose"
    # `taken_at` is the one field that could read as a verdict, and it renders
    # in the words `artifacts/intake.py` and the schema comment both use.
    assert "Read in means pulled" in PAGE.read_text()
    assert "which is not the same as " in PAGE.read_text()


def test_a_pending_row_reaches_no_other_page_and_no_search_index():
    """It counts toward nothing. `CLAUDE.md` has an invariant that no page
    asserts a plurality the corpus does not hold, and an unpublished record
    turning up in a claimant count, a label view or the site search would be
    the shortest route to breaking it."""
    src = ROOT / "astro" / "src"
    # The path rather than the table's name: three files name the table in a
    # comment, and naming it is not reaching it.
    reaching = sorted(
        str(p.relative_to(src)) for p in src.rglob("*")
        if p.is_file()
        and "/rest/v1/pending_submission" in p.read_text(errors="ignore")
    )
    assert reaching == ["lib/hub.mjs"], (
        f"the holding table is reached from {reaching}; both hops belong to the "
        "one module that talks to the project"
    )
    calling = sorted(
        str(p.relative_to(src)) for p in src.rglob("*")
        if p.is_file() and "readPending" in p.read_text(errors="ignore")
    )
    assert calling == ["lib/hub.mjs", "pages/submit.astro"], (
        f"a second page reads the holding table: {calling}"
    )
    assert re.search(r'<section id="played"[^>]*data-pagefind-ignore',
                     built()), (
        "the region is not held out of the search index, so a record could be "
        "indexed the moment anything renders into it at build time"
    )


def test_the_ordering_is_named_on_screen_and_switchable():
    """A default ordering is allowed and has to be named and switchable. What
    is being switched here is a clock, and being able to reverse it is the
    cheapest demonstration that the sequence carries nothing.

    `tests/test_ordering_control.py` exists because a bar rendered, set
    `aria-pressed` and had no handler behind it. So the handler is asserted as
    well as the copy, and the order itself is `inArrivalOrder`, which the tests
    above run.
    """
    body = " ".join(text_of(built()).split()).lower()
    assert "ordered by the time each one arrived here" in body
    assert "oldest first" in body and "newest first" in body
    assert "it is not a rank, not a place in a line" in body

    source = PAGE.read_text()
    assert 'document.querySelectorAll("#played-order button")' in source
    assert 'button.dataset.newest === "true"' in source
    assert "inArrivalOrder(sent, { newestFirst })" in source, (
        "the control no longer orders through the function the tests run"
    )


def test_an_account_that_has_sent_nothing_gets_words_and_not_an_empty_box():
    body = " ".join(text_of(built()).split()).lower()
    assert "this account has sent nothing yet" in body
    assert "that is a state and not a failure" in body
    source = PAGE.read_text()
    assert "nothing was sent for this" in source, (
        "a field nobody filled in renders as a blank rather than as an absence"
    )
    assert 'role="status"' in built(), "the fetch state is not announced"
    assert 'id="played-said"' in built()


def test_the_records_leave_the_document_on_sign_out():
    """The next person to sign in on this browser is a different person, and a
    hidden element is still an element."""
    source = PAGE.read_text()
    listener = re.search(
        r'window\.addEventListener\("controlbun:session".*?\}\);', source, re.S)
    assert listener and "forgetPlayed()" in listener.group(0), (
        "signing out leaves one person's records on the page"
    )
    wipe = re.search(r"function forgetPlayed\(\).*?\n  \}", source, re.S)
    assert wipe and "sent = []" in wipe.group(0)
    assert "list.replaceChildren()" in source, (
        "the rendered records are hidden rather than removed"
    )


def test_the_part_that_needs_script_says_so_with_scripting_off():
    """Not a dead region. The page already says the form needs JavaScript; the
    read back is a second thing that does, and it has no other page to point
    at."""
    noscript = re.search(r"<noscript>(.*?)</noscript>", built(), re.S)
    assert noscript, "the page no longer says anything with scripting off"
    said = " ".join(re.sub(r"<[^>]+>", " ", noscript.group(1)).split()).lower()
    assert "reading back what you have already sent needs it too" in said
    assert "no other page on this site that has it" in said


# --------------------------------------------------------------------------- #
# What a reader actually sees, drawn by the page's own script.
#
# Everything above this line asks whether the right strings are in the source.
# `tests/ordering_harness.py` exists because that question passed on a control
# that rendered, set `aria-pressed` and had no handler: presence is not
# behavior. Every sentence a record shows is built by script out of a fetch, so
# these run that script against rows and read what it drew.


def rendered(rows, press=None):
    return played.render(rows, press=press)


def test_reading_back_is_a_read_and_asks_for_what_it_says_it_does():
    """The harness refuses any request that is not this one and any that
    carries a method, so the shape of the request is held here as well as in
    the bundle."""
    out = rendered([a_row(submission(a_form()))])
    assert len(out["asked"]) == 1, "reading back made more than one request"
    asked = out["asked"][0]
    assert asked["method"] == "GET"
    assert "/rest/v1/pending_submission" in asked["url"]
    assert "order=received_at.asc" in asked["url"]


def test_a_record_a_reader_sees_says_what_it_is_and_shows_what_was_sent():
    out = rendered([a_row(submission(a_form()))])
    assert out["said"] == (
        "This account has sent 1 record, below. None of them is in the corpus."
    )
    shown = played.records(out)
    assert len(shown) == 1
    text = played.flatten(shown[0])
    assert ("Your own words, unchecked, not in the corpus, and readable by "
            "nobody else.") in text
    # The work a submitter came to check: the label, the version, the model,
    # their own definition and the pin.
    for value in ("pro-human", "meandiff", "allenai/Olmo-3-1125-32B",
                  "what the author means by it", "someone/direction", "a" * 40,
                  "direction.safetensors"):
        assert value in text, f"{value} was sent and is not on the page"
    # An absence is a sentence rather than a blank.
    assert "nothing was sent for this" in text


def test_every_value_a_reader_sees_is_marked_as_typed_rather_than_derived():
    """The rule `data-authored` carries on a published page, on a page the
    falsifier cannot reach: the numbers in here are the submitter's own and
    nothing has re-derived one."""
    out = rendered([a_row(submission(a_form()))])
    record = played.records(out)[0]
    marked = played.find(record, tag="div", **{"class": "played-body"})
    assert marked and "data-authored" in marked[0]["attrs"], (
        "a record renders outside a marked region, so a number in one reads "
        "as a figure this registry derived"
    )
    typed = {played.flatten(node)
             for node in played.find(record, tag="span", **{"class": "typed"})}
    # The layer is the number in this fixture, and it renders as a typed
    # string inside the marked region like everything else.
    assert "31" in typed
    assert "pro-human" in typed
    # And nothing a reader sees is a value that escaped the quoting.
    for group in ("dd",):
        for cell in played.find(record, tag=group):
            text = played.flatten(cell)
            assert (text == "" or "nothing was sent for this" in text
                    or text in typed), f"{text!r} renders unquoted"


def test_nothing_drawn_reads_as_a_queue():
    """The same list the built page is held to, applied to what the script
    draws, which is where the copy at risk of becoming a queue actually is."""
    rows = [
        a_row(submission(a_form()), id="one"),
        a_row(submission(a_form()), id="two", received_at="2026-09-20T01:00:00Z",
              taken_at="2026-09-20T09:00:00Z"),
    ]
    text = played.flatten(rendered(rows)["list"]).lower()
    # Phrases rather than the bare words, for the reason the built-page version
    # of this list gives: the copy that keeps a record from reading as a verdict
    # is the copy that says it is not one, so "not the same as accepted" is the
    # sentence a substring scan on `accepted` flags. The trap `CLAUDE.md` names,
    # caught here rather than worked around by softening the sentence.
    for queueing in ("pending review", "awaiting approval", "in the queue",
                     "your position", "position in", "your turn", "under review",
                     "will be reviewed", "once approved", "moderat",
                     "is approved", "was approved", "has been accepted",
                     "was rejected", "waiting for review"):
        assert queueing not in text, f"{queueing!r} is a queue arriving in prose"
    # `taken_at` is the field that could read as a verdict, and both states are
    # rendered here: one row has been read in and one has not.
    assert "the author read this in on 2026-09-20t09:00:00z" in text
    assert "has not read this in yet" in text
    assert "not the same as accept" in text


def test_nothing_drawn_is_a_reference_that_resolves():
    out = rendered([a_row(submission(a_form()))])
    text = played.flatten(out["list"])
    assert "@meandiff" not in text, (
        "a record in the holding table renders a version ref, which resolves "
        "to a frozen submission in the corpus and to nothing here"
    )
    assert "pro-human@" not in text


def test_the_order_is_named_and_a_press_reverses_what_is_drawn():
    """A control that renders and does nothing is worse than none. This is the
    press, through the page's own handler and its own ordering function."""
    rows = [
        a_row(submission(a_form()), id="second",
              received_at="2026-09-20T02:00:00Z"),
        a_row(submission(a_form()), id="first",
              received_at="2026-09-20T01:00:00Z"),
    ]
    oldest = rendered(rows)
    assert oldest["order"]["hidden"] is False, (
        "two records and no way to see what the order is"
    )
    assert oldest["order"]["now"] == "oldest first"
    assert oldest["order"]["pressed"] == {"oldest": "true", "newest": "false"}
    first = [played.flatten(r) for r in played.records(oldest)]
    assert "2026-09-20T01:00:00Z" in first[0]

    newest = rendered(rows, press="newest")
    assert newest["order"]["now"] == "newest first"
    assert newest["order"]["pressed"] == {"oldest": "false", "newest": "true"}
    after = [played.flatten(r) for r in played.records(newest)]
    assert "2026-09-20T02:00:00Z" in after[0], "the press changed nothing"
    assert [text[:40] for text in after] == [text[:40] for text in reversed(first)]


def test_one_record_is_not_offered_an_ordering():
    """An order of one is not an order, and a control over it is a control
    with nothing to do."""
    out = rendered([a_row(submission(a_form()))])
    assert out["order"]["hidden"] is True


def test_a_paste_is_drawn_as_the_text_it_is():
    out = rendered([a_row(paste_record(paste_text()))])
    record = played.records(out)[0]
    text = played.flatten(record)
    assert "nothing in this browser has read it" in text
    assert agent_handoff.BEGIN in text, "the paste itself is not shown"
    assert "I read the extraction script" in text, (
        "the prose the agent wrote around the block was trimmed, which is this "
        "page deciding which part of somebody's reply is the answer"
    )
    assert played.find(record, tag="pre"), "a paste renders as prose"


def test_an_account_that_has_sent_nothing_is_told_so():
    out = rendered([])
    assert out["none"]["hidden"] is False
    assert out["said"] == "This account has sent nothing yet."
    assert played.records(out) == []


def test_the_page_is_reachable():
    """A page nothing links to is a page nobody reads, and this is the one the
    bar's Add artifact points at."""
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    linkers = [
        str(p.relative_to(DIST)) for p in DIST.rglob("*.html")
        if p.parent.name != "submit"
        and 'href="/submit/"' in p.read_text(errors="ignore")
    ]
    assert linkers, "nothing on the site links to /submit/"
    assert "signed-in/index.html" in linkers, (
        "the page that finishes a sign-in does not offer the page that takes a "
        "submission, so somebody who has just signed in has nowhere to go"
    )
