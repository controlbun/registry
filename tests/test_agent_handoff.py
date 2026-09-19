"""The prompt an author hands their coding agent, and the paste that comes back.

Two halves. The first reads `agent_handoff.prompt()` and asserts the things it
cannot stop saying: that a value nobody read is never written, that an absence is
declared rather than left blank, that every field is open, that a pin is a commit
and not a tag, and that the registry holds competing definitions of one label on
purpose. Those are the reason the prompt exists, and prose is exactly the thing
that gets edited away a sentence at a time.

The second feeds it pastes shaped like what agents actually emit: markdown fences,
preamble, bold keys, bullets, blockquote markers, typographic quotes and trailing
commentary. What it asserts is the pair of properties the module is built around,
liberal in and strict out. Everything recoverable is recovered; everything
genuinely missing or ambiguous is a refusal naming it, because every one of those
cases is a place where a good guess produces a row indistinguishable from a
correct one.

**No number in this file is a measurement.** Following `fixtures/SYNTHETIC.md`:
the floats are repeated-digit decimals, `0.1111` and `0.7777`, which no real
measurement looks like, and the commit is forty letter `b`s, which is forty hex
characters and not a commit anybody made. The model id does not resolve.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "artifacts"))

import agent_handoff as handoff  # noqa: E402
from registry import db  # noqa: E402

# Forty hex characters so `fetch.commit_sha` takes it. Not a commit anything made.
SHA = "b" * 40


def block(body: str) -> str:
    return f"{handoff.BEGIN}\n{body.strip()}\n{handoff.END}\n"


def flat(text: str) -> str:
    """The prompt as one line. It is wrapped prose, and a sentence under test
    otherwise passes or fails on where the wrap happens to fall."""
    return re.sub(r"\s+", " ", text)


# Everything the schema cannot write a row without, and nothing else. Optional
# fields are added per test so that what each one is about stays visible.
CORE = """\
author: probe
label: kindness
version: synthetic-fixture
created_at: 2026-09-18T00:00:00Z
definition: <<<
A synthetic probe definition written by the test suite.
Warmth in affect: explicitly not costly help.
>>>
intervention_id: iv_probe_v1
kind: direction
model_id: placeholder/does-not-resolve-1b
layer: 3
layer_convention: block-0indexed
hook_point: resid_post
artifact_path: vectors/probe.safetensors
"""


# --------------------------------------------------------------------------- #
# The prompt, which is the part a reader's agent acts on.


def test_the_prompt_forbids_producing_a_value_nobody_read():
    text = flat(handoff.prompt()).lower()
    assert "never write a value you did not read" in text
    assert "not-found:" in text
    assert "absence is a real state in this schema" in text
    assert "a guessed field is a forgery" in text
    for field in ("chat_template_hash", "model_revision"):
        assert field in text, f"{field} is the field this fails on, unmentioned"


def test_the_prompt_says_the_pin_is_a_commit_and_says_why():
    text = flat(handoff.prompt())
    assert "Forty hex characters" in text
    assert "A commit, never a branch and never a tag" in text
    assert "whoever owns a repo can move a tag" in text, (
        "the rule without the reason is a rule an agent talks itself out of"
    )


def test_the_prompt_asks_for_the_authors_own_definition_and_says_why():
    text = flat(handoff.prompt())
    assert "Do not write the correct definition of the word. There is not one." in text
    assert "in their own words" in text
    assert "the thing another author disagrees with" in text
    assert "resolves none of them" in text


def test_the_prompt_says_every_field_is_open():
    text = flat(handoff.prompt())
    assert "Nothing here is chosen from a list" in text
    assert "common rather than permitted" in text
    assert "wants, not a problem to work around" in text


def test_the_prompt_names_every_field_the_parser_accepts():
    """A manual that asks for less than the form takes sends a partial answer."""
    text = handoff.prompt()
    missing = [s.name for s in handoff.SPECS if s.name not in text]
    assert not missing, f"the prompt never mentions {missing}"


def test_the_prompt_carries_no_number_that_could_be_read_as_a_measurement():
    """An example value becomes a default, and a default here is a fabrication."""
    decimals = re.findall(r"\d+\.\d+", handoff.prompt())
    assert not decimals, f"the prompt states numbers: {decimals}"


def test_corpus_values_are_offered_as_spelling_and_not_as_a_menu():
    text = flat(handoff.prompt({"hook_point": ["resid_post", "mlp_out"],
                                "kind": ["direction"]}))
    assert "hook_point: resid_post, mlp_out" in text
    assert "Not a menu, not a set to pick from" in text
    assert "not an indication that a value outside it is wrong" in text


def test_the_corpus_section_is_absent_when_there_is_no_corpus():
    assert "What other people have typed" not in handoff.prompt()
    assert "What other people have typed" not in handoff.prompt({"kind": []})


# --------------------------------------------------------------------------- #
# The paste, at its cleanest.


def test_a_clean_block_becomes_the_forms_own_field_names():
    got = handoff.parse(block(CORE))
    assert got.values["author"] == "probe"
    assert got.values["layer"] == "3"
    assert got.values["hook_point"] == "resid_post"
    assert got.values["definition"].splitlines()[1] == (
        "Warmth in affect: explicitly not costly help."
    ), "a colon inside a fenced value split the line into a field"


def test_the_artifact_path_fills_both_modes_with_one_string():
    """`fetch.resolve` hands one path field to the remote, so they are one string."""
    got = handoff.parse(block(CORE))
    assert got.values["link_path"] == got.values["bytes_path"] == (
        "vectors/probe.safetensors"
    )


def test_a_pin_arrives_as_link_mode_and_no_pin_says_so():
    unpinned = handoff.parse(block(CORE))
    assert not unpinned.pinned
    assert any("bytes route" in n for n in unpinned.notes)

    pinned = handoff.parse(block(
        CORE + f"artifact_repo: author/directions\nartifact_commit: {SHA}\n"))
    assert pinned.pinned
    assert pinned.values["link_repo"] == "author/directions"
    assert pinned.values["link_commit"] == SHA


def test_a_pin_can_name_a_host_that_is_not_the_hub():
    """The agent sits in the checkout, so it is the thing that knows this."""
    template = "https://media.githubusercontent.com/media/{repo}/{commit}/{path}"
    got = handoff.parse(block(
        CORE + f"artifact_repo: author/directions\nartifact_commit: {SHA}\n"
        f"artifact_host: github.com\nartifact_url_template: {template}\n"))
    assert got.pinned
    assert got.values["link_host"] == "github.com"
    assert got.values["link_url_template"] == template


def test_dropping_the_host_lines_is_not_a_missing_field():
    """Absence is a state, and it means the Hub."""
    got = handoff.parse(block(
        CORE + f"artifact_repo: author/directions\nartifact_commit: {SHA}\n"))
    assert "link_host" not in got.values
    assert "link_url_template" not in got.values


def test_a_repo_without_a_commit_is_not_a_pin_and_is_not_silent():
    got = handoff.parse(block(CORE + "artifact_repo: author/directions\n"))
    assert not got.pinned
    assert any("branch is not a pin" in n for n in got.notes)


# --------------------------------------------------------------------------- #
# The paste, shaped like what a chat window actually hands over.


MESSY = """\
I read through `extract.py` and the run log in `runs/2026-09-18/`. Two things I
could not find, which I've marked rather than filled in — see below.

Here's the block:

```text
**=== BEGIN CONTROLBUN SUBMISSION ===**
- **author:** probe
- **label:** kindness
- **version:** synthetic-fixture
- created_at: 2026-09-18T00:00:00Z
- definition: <<<
A synthetic probe definition written by the test suite.
The author’s theory, in the author’s “own words”.
>>>
- intervention_id: iv_probe_v1
- kind: direction
- model_id: placeholder/does-not-resolve-1b
- layer: 3
- layer_convention: block-0indexed
- hook_point: resid_post
- coeff_low: 0.1111
- coeff_high: 0.7777
- artifact_path: vectors/probe.safetensors
- not-found: model_revision — the extraction ran against a served endpoint and
  the script never captured what it was serving
- not-found: chat_template_hash - no template was applied; activations were read
  from raw text against a base checkpoint
**=== END CONTROLBUN SUBMISSION ===**
```

Let me know if you want me to go and compute the digest of the file as well.
"""


def test_the_messy_paste_survives_everything_a_chat_window_does_to_it():
    got = handoff.parse(MESSY)
    assert got.values["author"] == "probe"
    assert got.values["kind"] == "direction"
    assert got.values["coeff_low"] == "0.1111"
    assert got.values["coeff_high"] == "0.7777"
    assert "own words" in got.values["definition"]
    assert '“' not in got.values["definition"], "a smart quote came through"
    assert any("typographic quotes" in n for n in got.notes)


def test_a_declared_absence_is_kept_with_its_reason_and_fills_nothing():
    got = handoff.parse(MESSY)
    assert set(got.absent) == {"model_revision", "chat_template_hash"}
    assert "never captured" in got.absent["model_revision"]
    assert "no template was applied" in got.absent["chat_template_hash"]
    assert "model_revision" not in got.values
    assert "chat_template_hash" not in got.values
    shown = dict(got.display())
    assert shown["model_revision"].startswith("absent: ")


def test_a_quoted_reply_with_no_closing_marker_still_reads():
    quoted = "\n".join(
        "> " + line for line in block(CORE).splitlines()
        if not line.startswith(handoff.END)
    )
    got = handoff.parse("On Thursday somebody wrote:\n" + quoted)
    assert got.values["label"] == "kindness"


def test_an_indented_yaml_style_value_is_taken():
    got = handoff.parse(block("""\
author: probe
label: kindness
version: synthetic-fixture
created_at: 2026-09-18T00:00:00Z
definition: |
  A synthetic probe definition written by the test suite.
  Costly help, and explicitly not warmth.
intervention_id: iv_probe_v1
kind: direction
model_id: placeholder/does-not-resolve-1b
layer: 3
layer_convention: block-0indexed
hook_point: resid_post
artifact_path: vectors/probe.safetensors
"""))
    assert got.values["definition"].endswith("explicitly not warmth.")


def test_the_aliases_an_agent_reaches_for_land_on_the_right_field():
    got = handoff.parse(block(
        CORE.replace("model_id:", "model:").replace("hook_point:", "hook:")
        + f"repo: author/directions\ncommit: {SHA}\nnorm: 0.7777\n"))
    assert got.values["model_id"] == "placeholder/does-not-resolve-1b"
    assert got.values["hook_point"] == "resid_post"
    assert got.values["link_repo"] == "author/directions"
    assert got.values["link_commit"] == SHA
    assert got.values["l2_norm"] == "0.7777"


def test_the_agent_that_answers_in_json_anyway_is_read():
    """A complete, correct answer in the wrong punctuation is not worth a refusal."""
    got = handoff.parse(f"""\
{handoff.BEGIN}
{{
  "author": "probe",
  "label": "kindness",
  "version": "synthetic-fixture",
  "created_at": "2026-09-18T00:00:00Z",
  "definition": "Warmth in affect, and explicitly not costly help.",
  "intervention_id": "iv_probe_v1",
  "kind": "direction",
  "model_id": "placeholder/does-not-resolve-1b",
  "layer": 3,
  "layer_convention": "block-0indexed",
  "hook_point": "resid_post",
  "artifact_path": "vectors/probe.safetensors"
}}
{handoff.END}
""")
    assert got.values["author"] == "probe"
    assert got.values["layer"] == "3"
    assert got.values["definition"].endswith("not costly help.")
    assert got.values["link_path"] == "vectors/probe.safetensors"


def test_a_field_nobody_here_has_is_kept_and_shown_rather_than_refused():
    """A key this form has no column for is not an error. There is no closed set.

    Refusing the paste over it would make the parser the thing that decides what
    an author may say about their own artifact, which is the failure at field
    level that `CLAUDE.md` names: document what is common, enforce none of it.
    """
    got = handoff.parse(block(CORE + "contrast_pairs: 135 pairs, from the repo\n"))
    assert got.extra == {"contrast_pairs": "135 pairs, from the repo"}
    assert any("contrast_pairs" in n for n in got.notes)
    assert got.values["author"] == "probe", "a stray key cost the rest of the block"


# --------------------------------------------------------------------------- #
# The refusals, which are the half that keeps a guess out of a row.


def refusal(text: str) -> str:
    with pytest.raises(handoff.Refused) as caught:
        handoff.parse(text)
    return str(caught.value)


def test_nothing_that_looks_like_a_block_is_a_refusal_naming_the_marker():
    said = refusal("Sure! Here are the fields:\n\nauthor: probe\nlabel: kindness\n")
    assert "BEGIN CONTROLBUN SUBMISSION" in said


def test_two_blocks_are_two_submissions_and_are_not_chosen_between():
    said = refusal(block(CORE) + "\nOn reflection:\n\n" + block(CORE))
    assert "2 submission blocks" in said


def test_a_placeholder_left_in_the_template_is_refused():
    said = refusal(block(CORE.replace("layer: 3", "layer: <the integer>")))
    assert "placeholder" in said
    assert "<the integer>" in said


def test_the_two_line_definition_placeholder_is_refused_too():
    """The field likeliest to survive a careless pass, and least visible in a form."""
    said = refusal(block(CORE.replace(
        "A synthetic probe definition written by the test suite.\n"
        "Warmth in affect: explicitly not costly help.",
        "<your author's own theory of the label, in their words,\n"
        "over as many lines as it takes>")))
    assert "placeholder" in said
    assert "definition" in said


def test_the_prompt_pasted_straight_back_is_refused():
    """Nothing is filled in, and every line of it looks like an answer."""
    assert "placeholder" in refusal(handoff.prompt())


def test_a_not_found_line_still_carrying_the_template_is_refused():
    said = refusal(block(CORE + "not-found: <field> <why it is absent>\n"))
    assert "template rather than an answer" in said


def test_an_empty_value_is_refused_rather_than_read_as_an_absence():
    said = refusal(block(CORE + "chat_template_hash:\n"))
    assert "empty value" in said
    assert "not-found" in said


def test_an_absence_with_no_reason_is_refused():
    said = refusal(block(CORE + "not-found: model_revision\n"))
    assert "no reason" in said
    assert "model_revision" in said


def test_a_column_the_row_is_made_of_cannot_be_declared_absent():
    said = refusal(block(CORE.replace("kind: direction\n", "")
                         + "not-found: kind nobody wrote down what this is\n"))
    assert "cannot write a row without" in said
    assert "a not-found does not help here" in said


def test_a_missing_column_the_row_is_made_of_is_named():
    said = refusal(block(CORE.replace("hook_point: resid_post\n", "")))
    assert "hook_point" in said
    assert "nullable" in said, "the message has to say which fields may be absent"


def test_one_field_answered_twice_is_a_question_for_whoever_wrote_it():
    said = refusal(block(CORE + "layer: 4\n"))
    assert "answered twice" in said


def test_a_field_both_answered_and_declared_absent_is_refused():
    said = refusal(block(CORE + "coeff_low: 0.1111\n"
                         "not-found: coeff_low it was never swept\n"))
    assert "coeff_low" in said
    assert "no way to tell which" in said


def test_a_layer_that_is_not_an_integer_is_refused_in_the_schemas_terms():
    said = refusal(block(CORE.replace("layer: 3", "layer: the middle one")))
    assert "stored as an integer" in said


def test_a_coefficient_that_is_not_a_number_is_refused():
    said = refusal(block(CORE + "coeff_high: about a tenth\n"))
    assert "stored as a number" in said
    assert "nullable" in said


def test_a_branch_name_where_the_commit_goes_is_refused_by_the_one_rule():
    """`registry.fetch.commit_sha`, not a second copy of it living here."""
    said = refusal(block(CORE + "artifact_commit: main\n"))
    assert "not a commit SHA" in said
    assert "moved by whoever owns the repo" in said


def test_a_short_hex_string_is_not_a_commit_either():
    said = refusal(block(CORE + f"artifact_commit: {'b' * 12}\n"))
    assert "not a commit SHA" in said


def test_an_empty_paste_says_so():
    assert "nothing was pasted" in refusal("   \n\n  ")


# --------------------------------------------------------------------------- #
# The seam with the form, which is the thing that goes stale silently.


def test_every_field_the_parser_fills_exists_on_the_intake_page(tmp_path):
    """The parser writes into inputs it does not own.

    A renamed `data-field` in `artifacts/intake.py` would leave this filling
    nothing, with no error anywhere: the fetch succeeds, the panel renders, and
    the form stays empty. So the two names are compared rather than trusted.
    """
    import intake

    database = tmp_path / "registry.db"
    conn = db.connect(database)
    db.migrate(conn)
    try:
        page = intake.page(conn, token="t", repo="author/directions",
                           origin="http://127.0.0.1:0").decode()
    finally:
        conn.close()

    on_page = set(re.findall(r'data-field="([^"]+)"', page))
    assert on_page, "no data-field inputs on the intake page at all"
    ours = {name for spec in handoff.SPECS for name in spec.form}
    assert ours <= on_page, (
        "the parser fills fields the form does not have: "
        f"{sorted(ours - on_page)}"
    )


def test_the_payload_the_route_returns_carries_the_pairs_the_panel_prints():
    payload = handoff.received(MESSY)
    assert payload["fields"]["author"] == "probe"
    assert payload["absent"]["model_revision"]
    assert payload["pinned"] is False
    assert ("kind", "direction") in [tuple(p) for p in payload["display"]]


def test_the_prompt_warns_that_artifact_path_is_not_a_local_path():
    """The one field a capable agent gets wrong while understanding it.

    A real submission attempt answered `artifact_path` with the cluster path the
    file was read from, and said in a different field that it knew the two were
    different. The field was asking for a decision and read like a lookup, so
    the prompt now says which, and says it where the answer gets written.
    """
    text = handoff.prompt()
    body = text.split("## Where the artifact is")[1]
    assert "not where the file is on your author's machine" in body.lower()
    assert "404" in body
    # And in the template, where an agent skimming for the shape will see it.
    template = text.split("=== BEGIN CONTROLBUN SUBMISSION ===")[1]
    line = [l for l in template.splitlines() if l.startswith("artifact_path:")]
    assert line and "not a local path" in line[0]


def test_the_corpus_section_uses_the_names_the_template_uses():
    """One field, one spelling, in one document.

    `intake.suggestions` is keyed by the form's `data-field` names, and the
    prompt asks for the schema's. They differ wherever the form splits a field
    across link and bytes mode, so passing the query through raw put `link_host`
    in a document whose template says `artifact_host`.
    """
    observed = {"link_host": ["github.com"],
                "link_url_template": ["https://{host}/{repo}/{commit}/{path}"],
                "kind": ["direction"]}
    text = handoff.prompt(observed)
    assert "artifact_host: github.com" in text
    assert not [l for l in text.splitlines() if l.startswith("link_")]


def test_the_prompt_does_not_promise_a_template_can_drop_the_commit():
    """`fetch.pinned_url` refuses a template whose URL does not carry the
    commit, so a prompt saying otherwise sends an agent to a refusal."""
    from registry import fetch
    text = handoff.prompt()
    assert "commit has to end up in the url" in text.lower()
    assert "any of the four or none" not in text
    # And the rule the prompt now states is the one the code applies.
    with pytest.raises(fetch.FetchError):
        fetch.pinned_url(host="h", repo="a/b", commit="b" * 40, path="p",
                         url_template="https://{host}/{repo}/{path}")
