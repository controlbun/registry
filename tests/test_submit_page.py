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
    nothing about who anybody is."""
    source = PAGE.read_text()
    for asserting in ("data-author", "data-owner", "controlbun.json"):
        assert asserting not in source, (
            f"the page reads {asserting!r}, so it can say a reader is whoever "
            "they happen to be reading about"
        )


def test_no_session_in_this_browser_is_a_state_with_its_own_words():
    """Not an error and not an empty page. Somebody who arrives here without a
    session did nothing wrong, and there is one thing to do about it."""
    page = built()
    assert 'id="nosession"' in page
    body = text_of(page).lower()
    assert "there is no session in this browser" in body
    assert 'href="/sign-in/"' in page and 'href="/signed-in/"' in page


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
