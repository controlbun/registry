"""The table a submission lands in, and the policy that stamps who sent it.

Premise, restated because a premise stated in one file gets violated in every
other one: **plurality is the product, the registry never designates, and
consumers pin visibly.** This table holds what strangers sent. It is not the
corpus, it is not a queue, nothing in it is approved, rejected, ranked, counted
or ordered, and `taken_at` means read in rather than accepted.

**What this file can and cannot prove.** The insert policy runs in Postgres, and
`make verify` runs from a clean checkout with no network and no database, which
is a property `tests/test_signed_in_page.py` states and this file keeps. So the
refusal itself is proved live, by hand, against the real project, and recorded
in `DECISIONS.md` 2026-09-20 with the date and what was run. What is proved here
is the two halves that can be: the policy text still binds all three identity
columns to the verified session, and the browser builds the row it sends out of
the session and never out of the record. Between them, a change that would make
a forged submission possible fails this file even though this file cannot reach
a database.

That split is deliberate and it is stated rather than papered over. A test that
went green because it could not reach the network would be the failure this
repository keeps catching, so nothing here skips on a network error: nothing
here uses the network at all.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "schema" / "supabase" / "001_pending_submission.sql"
LIB = ROOT / "astro" / "src" / "lib"
HANDSHAKE = LIB / "handshake.mjs"
HUB = LIB / "hub.mjs"
INTAKE = ROOT / "artifacts" / "intake.py"

NODE = shutil.which("node")

# The three columns the row carries an identity in, and the JWT claim each one
# has to equal for Postgres to accept the row.
STAMPED = {
    "account": r"\(?\s*auth\.uid\(\)",
    "subject": r"\(?\s*auth\.jwt\(\)[^)]*'sub'",
    "handle": r"\(?\s*auth\.jwt\(\)[^)]*'preferred_username'",
}


def sql() -> str:
    return SQL.read_text()


def without_comments(text: str) -> str:
    """The DDL, with the prose taken out.

    The file argues for its own policy at length, so a scan for `with check`
    or for a column name finds the paragraph explaining it as readily as the
    statement doing it. `test_the_comment_strip_does_not_hide_a_real_one`
    below shows the filter still keeping a real line.
    """
    return "\n".join(line.split("--")[0] for line in text.splitlines())


def insert_policy() -> str:
    """The insert policy statement, from `for insert` to its semicolon."""
    ddl = without_comments(sql())
    m = re.search(r"for\s+insert\b.*?;", ddl, re.S | re.I)
    assert m, "there is no insert policy in the file at all"
    return m.group(0)


# --------------------------------------------------------------------------- #
# The policy text, which is what Postgres enforces.


def test_row_level_security_is_on():
    """Without this line every policy below is decoration."""
    assert re.search(
        r"alter\s+table\s+public\.pending_submission\s+enable\s+row\s+level\s+security",
        without_comments(sql()), re.I,
    ), "row level security is not enabled, so the policies constrain nothing"


def test_the_insert_policy_binds_every_identity_column_to_the_session():
    """The property the whole design rests on.

    A submission cannot claim to be from somebody it is not, because the row is
    refused when any of the three disagrees with the verified JWT. Drop one
    conjunct and a signed-in person can submit under anybody's handle, which is
    the forged-capture problem the table exists to kill. Each column is checked
    by name rather than the expression as a whole, so an edit that keeps two
    and loses the third fails here.
    """
    body = insert_policy()
    assert re.search(r"with\s+check", body, re.I), (
        "the insert policy has no `with check`, so it admits any row an "
        "authenticated caller sends"
    )
    missing = [
        column for column, claim in STAMPED.items()
        if not re.search(rf"\b{column}\s*=\s*{claim}", body, re.I | re.S)
    ]
    assert not missing, (
        f"the insert policy no longer binds {missing} to the verified session. "
        "A column that is not bound is a column the payload chooses, and a "
        "payload that chooses its own author is a forged submission."
    )


def test_the_insert_policy_is_for_signed_in_callers_only():
    assert re.search(r"for\s+insert\s+to\s+authenticated", insert_policy(), re.I), (
        "the insert policy is not restricted to `authenticated`, so an "
        "anonymous caller is inside it and `auth.uid()` is null for one"
    )


def test_nobody_reads_anybody_else_s_pending_row():
    """A table strangers could browse would be a second corpus with none of the
    properties the first one has, and it would publish submissions by arriving."""
    ddl = without_comments(sql())
    m = re.search(r"for\s+select\b(.*?);", ddl, re.S | re.I)
    assert m, "there is no select policy, which is a different thing from a closed one"
    assert re.search(r"using\s*\(\s*account\s*=\s*auth\.uid\(\)\s*\)", m.group(1), re.I), (
        "the select policy is not scoped to the caller's own rows"
    )


def test_there_is_no_update_and_no_delete_policy():
    """A submission is a statement somebody made at a time, and a correction is
    another submission. With no policy, neither is possible through the
    publishable key at all, which is stronger than a policy that refuses."""
    ddl = without_comments(sql())
    for verb in ("update", "delete"):
        assert not re.search(rf"for\s+{verb}\b", ddl, re.I), (
            f"an {verb} policy exists, so a row can be changed after it was "
            "sent and the record stops being what somebody said at a time"
        )


def test_the_table_enumerates_nothing():
    """`CLAUDE.md`: no closed enum on any user-supplied field, and a schema
    `CHECK` listing permitted strings fails the build. `tests/test_invariants.py`
    holds that for `schema/migrations`; this file is in a different directory
    and was outside that scan, so the same rule is applied here."""
    ddl = without_comments(sql())
    offenders = []
    for n, line in enumerate(ddl.splitlines(), 1):
        if re.search(r"\bCHECK\b", line, re.I) and re.search(r"'[^']*'", line):
            offenders.append(f"line {n}: {line.strip()}")
        if re.search(r"\bIN\s*\(\s*'", line, re.I):
            offenders.append(f"line {n}: {line.strip()}")
        if re.search(r"\bAS\s+ENUM\b", line, re.I):
            offenders.append(f"line {n}: {line.strip()}")
    assert not offenders, (
        "a closed enumeration declares which ways of doing the thing are "
        "legitimate, and this table is the last place that should decide what "
        "a legitimate artifact looks like:\n" + "\n".join(offenders)
    )


def test_the_record_column_is_opaque_to_the_database():
    """Whether the bytes at the pin are what the submitter says they are is
    answered in Python, where the bytes are, by the one thing here that reads
    them. A shape constraint in the schema would be a second answer."""
    assert re.search(r"record\s+jsonb\s+not null", without_comments(sql()), re.I)


def test_the_comment_strip_does_not_hide_a_real_one():
    """The bite on the filter. A scanner that stops seeing the thing it looks
    for because a filter got too wide is the failure this repository has hit
    more than once."""
    sample = (
        "-- No CHECK constraint lists permitted kinds here.\n"
        "  kind text not null check (kind in ('direction', 'probe')),\n"
    )
    stripped = without_comments(sample)
    assert "check (kind in" in stripped
    assert "No CHECK constraint" not in stripped


def test_the_policy_check_flags_a_policy_that_lost_a_clause():
    """The bite on the policy test. Each clause is shown refusing the edit that
    would remove it rather than asserted to work."""
    whole = (
        "account = auth.uid() "
        "and subject = (auth.jwt() -> 'user_metadata' ->> 'sub') "
        "and handle = (auth.jwt() -> 'user_metadata' ->> 'preferred_username')"
    )
    for column, claim in STAMPED.items():
        assert re.search(rf"\b{column}\s*=\s*{claim}", whole, re.I | re.S), (
            f"the check for {column} does not match the real policy text"
        )
    # And each one, dropped, is caught.
    for column in STAMPED:
        without = re.sub(rf"(and\s+)?\b{column}\s*=\s*[^=]*?(?=(\s+and\s+|$))",
                         "", whole, flags=re.I | re.S)
        assert not re.search(rf"\b{column}\s*=\s*{STAMPED[column]}", without,
                             re.I | re.S), (
            f"dropping the {column} clause left something the check still matches"
        )
    # A payload-sourced value passes nothing: the point is the comparison, so a
    # policy that compared a column to itself is caught too.
    assert not re.search(rf"\bsubject\s*=\s*{STAMPED['subject']}",
                         "subject = subject", re.I | re.S)


# --------------------------------------------------------------------------- #
# The other half: the browser cannot send an identity it was not given.


def run_js(body: str):
    """Evaluate `body` against the real module and return what it printed.

    Against the file itself, imported by URL, the same way
    `tests/test_signed_in_page.py` does it, so there is no copy of the logic in
    this directory to drift from the one that ships.
    """
    if not NODE:
        pytest.skip("node not on PATH")
    source = (
        f'import {{ pendingRowFrom, Refused }} from {json.dumps(HANDSHAKE.as_uri())};\n'
        f"{body}\n"
    )
    done = subprocess.run(
        [NODE, "--input-type=module", "-e", source],
        capture_output=True, text=True, timeout=60,
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout) if done.stdout.strip() else None


SESSION = (
    '{ id: "11111111-2222-3333-4444-555555555555", '
    'user_metadata: { sub: "session-subject", preferred_username: "session-handle" } }'
)


def test_the_row_takes_its_identity_from_the_session():
    row = run_js(
        f"const row = pendingRowFrom({SESSION}, "
        '{ shape: "controlbun.registry/link-submission@1", label: "kindness" });\n'
        "console.log(JSON.stringify(row));"
    )
    assert row["account"] == "11111111-2222-3333-4444-555555555555"
    assert row["subject"] == "session-subject"
    assert row["handle"] == "session-handle"
    assert row["record"]["label"] == "kindness"


def test_a_record_claiming_a_different_author_does_not_change_the_row():
    """The forged-capture case, at the one place a browser could introduce it.

    A capture that arrives as a file is a stranger's JSON and nothing
    downstream can tell an edited one from a real one, which is the whole
    argument in `schema/supabase/001_pending_submission.sql`. Here the record
    names somebody else outright and the row is unmoved: the columns Postgres
    compares against the session are built from the session. The claim is still
    inside `record`, untouched, because deleting it would hide the
    disagreement the author's pull exists to surface.
    """
    row = run_js(
        f"const row = pendingRowFrom({SESSION}, "
        '{ author: "somebody-else", subject: "somebody-elses-subject", '
        'label: "kindness" });\n'
        "console.log(JSON.stringify(row));"
    )
    assert row["subject"] == "session-subject"
    assert row["handle"] == "session-handle"
    # Kept, not scrubbed. The stamped pair wins and the disagreement is visible.
    assert row["record"]["author"] == "somebody-else"
    assert row["record"]["subject"] == "somebody-elses-subject"


def test_a_session_missing_any_of_the_three_sends_nothing():
    """Postgres would refuse the row, since a null never equals a claim. Saying
    so here means the submitter reads a sentence rather than a 401."""
    for session, absent in (
        ('{ user_metadata: { sub: "s", preferred_username: "h" } }', "account id"),
        ('{ id: "x", user_metadata: { preferred_username: "h" } }', "provider subject"),
        ('{ id: "x", user_metadata: { sub: "s" } }', "handle"),
        ("null", "account id"),
    ):
        message = run_js(
            "let said = null;\n"
            f"try {{ pendingRowFrom({session}, {{ label: 'k' }}); }}\n"
            "catch (problem) { said = problem instanceof Refused ? problem.message : null; }\n"
            "console.log(JSON.stringify(said));"
        )
        assert message, f"a session with no {absent} built a row anyway"
        assert absent in message, f"the refusal does not say what is missing: {message}"


def test_no_token_can_reach_the_row():
    """Structural rather than a rule: the function takes the user object out of
    the session and never the session, so there is no parameter a token can
    arrive in. The access token goes into one header, one file along."""
    source = HANDSHAKE.read_text()
    m = re.search(r"export function pendingRowFrom\(([^)]*)\)", source)
    assert m, "pendingRowFrom is gone or has a different shape"
    assert m.group(1).strip() == "user, record", (
        f"pendingRowFrom now takes {m.group(1)!r}; a session parameter here "
        "would be a token parameter here"
    )


def test_the_sending_function_puts_the_token_in_a_header_and_nowhere_else():
    """And writes nothing down. `tests/test_signed_in_page.py` holds that for
    the module as a whole; this is the one function that carries a second
    credential, so it is checked by name."""
    source = HUB.read_text()
    m = re.search(r"export async function sendPending\(.*?\n\}", source, re.S)
    assert m, "sendPending is gone"
    body = m.group(0)
    assert "Authorization: `Bearer ${accessToken}`" in body
    assert "accessToken" not in body.split("body: JSON.stringify(row)")[1], (
        "the token appears after the body is built, which is not where a "
        "header goes"
    )
    for writing in ("localStorage", "sessionStorage", "document.", "console."):
        assert writing not in body, f"sendPending reaches {writing}"


def test_the_row_goes_to_the_pending_table_and_not_to_the_corpus():
    assert "/rest/v1/pending_submission" in HUB.read_text(), (
        "the send no longer names the holding table, so it is aimed somewhere "
        "this file has not read"
    )


# --------------------------------------------------------------------------- #
# The pull, which is the only thing that reads the table with the secret key.


def test_the_secret_key_is_read_from_the_environment_and_never_from_a_file():
    source = INTAKE.read_text()
    assert 'SECRET_KEY_ENV = "SUPABASE_SECRET_KEY"' in source
    # The `.env` reader exists for the project URL. It must not be a fallback
    # for the key: a key in a file in the working tree is a key one `git add
    # -A` away from a public repository.
    m = re.search(r"def credentials\(.*?\n    return url", source, re.S)
    assert m, "credentials() is gone or has a different shape"
    body = m.group(0)
    assert "env_file.get(SECRET_KEY_ENV)" not in body, (
        "the secret key is read from .env, which is the thing it is not in"
    )
    assert re.search(r"secret\s*=\s*\(environ\.get\(SECRET_KEY_ENV\)", body), (
        "the secret key no longer comes from the environment alone"
    )


def test_the_key_is_interpolated_in_one_place_and_it_is_a_header():
    """It bypasses every row-level policy on the project, so it goes into two
    headers and into nothing else.

    The check is that `{secret` appears on exactly the lines that set a header.
    A `print`, an f-string in a refusal message, a URL with the key in the
    query string and a log line would each put it somewhere it is readable
    later, and each one is a line this catches. Checked over the whole module
    rather than over the pull's own functions, because the failure mode is
    somebody adding a debug line somewhere else.

    The variable is `secret` and not `key` on purpose. `refuse_credentials`
    one screen up walks a submission's dictionary keys and interpolates one
    into a refusal message, which is a JSON field name and not a credential,
    and while both were called `key` this test could not tell them apart. The
    first version of it failed on that line, correctly by its own rule and
    wrongly about the code, and the fix was the name rather than an exemption:
    an exemption here would have been a hole shaped like whatever else got
    called `key` later.
    """
    lines = [
        line.split("#")[0] for line in INTAKE.read_text().splitlines()
    ]
    interpolating = [line.strip() for line in lines if "{secret" in line]
    assert interpolating, "the key is never interpolated, so this is inert"
    for line in interpolating:
        assert "add_header" in line, (
            f"the secret key is interpolated somewhere that is not a header: "
            f"{line!r}"
        )
    printing = [
        line.strip() for line in lines
        if re.search(r"\bprint\(", line) and re.search(r"\bsecret\b", line)
    ]
    assert not printing, f"the secret key reaches output: {printing}"
