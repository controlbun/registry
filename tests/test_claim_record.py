"""A capture becomes a claim, and every check in that path is shown to bite.

`artifacts/claim.py` is the join between a sign-in capture and the three tables
`schema/migrations/009` defines. Before it existed, the one real claim in this
corpus was a person reading a capture on screen and typing a subject id into
`artifacts/seed.py`, which is the transcription this project refuses everywhere
else.

Every test below is written the way `tests/test_write_claim_bite.py` and
`tests/test_scan_gap_bite.py` are: "the check passes" proves nothing on its own,
so each mutation is asserted to have landed before its result is believed, and
the control case is run beside the refusal so a function that refused everything
would not read as green.

**No identity here is a person.** The providers do not exist, the subjects were
issued by nobody, and the organizations sit on the reserved `.invalid` TLD, which
is the convention `fixtures/SYNTHETIC.md` sets. The one real identity in this
project is recorded in `V2.md`, and the only place it appears here is the block
that checks the real record still carries what the sign-in produced, which is the
canary the author asked for.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import db, views  # noqa: E402


def _load(name: str):
    """Import a script out of `artifacts/`, which is not a package."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "artifacts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


claim = _load("claim")

# Obviously not a person, and not reachable from anywhere. See the header.
PROVIDER = "test-provider-does-not-exist"
SUBJECT = "SYNTHETIC-SUBJECT-NOT-ISSUED-BY-ANY-PROVIDER-a"
OTHER_SUBJECT = "SYNTHETIC-SUBJECT-NOT-ISSUED-BY-ANY-PROVIDER-b"
ENDPOINT = "https://test-provider.invalid/oauth/userinfo"


def capture(**over) -> dict:
    """One synthetic capture in the shape `/signed-in/` writes."""
    entry = {
        "shape": "controlbun.registry/membership-capture@1",
        "captured_at": "2026-01-05T00:00:00Z",
        "provider": PROVIDER,
        "issuer": "https://test-provider.invalid",
        "userinfo_endpoint": ENDPOINT,
        "sub": SUBJECT,
        "preferred_username": "synthetic-handle",
        "orgs": [{"name": "synthetic-org-does-not-resolve", "roleInOrg": "admin"}],
    }
    entry.update(over)
    return entry


@pytest.fixture
def conn(tmp_path) -> sqlite3.Connection:
    c = db.connect(tmp_path / "t.db")
    db.migrate(c)
    return c


@pytest.fixture
def record(tmp_path) -> Path:
    return tmp_path / "claims.jsonl"


def synthetic(entry: dict) -> dict:
    """Mark an entry as a fixture, which is what every row written here is."""
    return {**entry, "is_synthetic": True}


def rows(conn, table: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(f"SELECT * FROM {table}")]


# --------------------------------------------------------------------------- #
# The binding, and the refusal that keeps it off the handle.


def test_a_capture_with_no_sub_is_refused_and_never_falls_back_to_the_handle(
        conn, record):
    """The whole design is one opaque id. A capture without it writes nothing.

    The control underneath is the point: the same capture with a `sub` goes
    through, so this is a refusal aimed at one missing field rather than a
    function that refuses everything.
    """
    without = capture(sub=None)
    assert without["preferred_username"], (
        "the probe has no handle either, so a fallback to the handle would "
        "look like this refusal and this test would pass on the wrong reason"
    )
    with pytest.raises(claim.Refused) as refused:
        claim.claim_from(without, namespace="anyone", evidence=[])
    assert "handles are renameable" in str(refused.value)
    assert not record.exists()
    assert rows(conn, "namespace_claim") == []

    entry = synthetic(claim.claim_from(capture(), namespace="anyone", evidence=[]))
    claim.insert(conn, entry)
    assert rows(conn, "namespace_claim")[0]["subject"] == SUBJECT


def test_the_id_is_made_of_the_subject_and_not_of_the_handle(conn):
    """Two accounts wearing one handle are two claims; one account renaming is one.

    The primary key is derived from exactly the columns the UNIQUE constraint is
    made of, so this is the identity rule expressed twice in the same string.
    """
    one = claim.claim_from(capture(preferred_username="before-the-rename"),
                           namespace="allen", evidence=[])
    renamed = claim.claim_from(capture(preferred_username="after-the-rename"),
                               namespace="allen", evidence=[])
    other = claim.claim_from(capture(sub=OTHER_SUBJECT,
                                     preferred_username="before-the-rename"),
                             namespace="allen", evidence=[])
    assert one["handle"] != renamed["handle"], "the probe did not change the handle"
    assert claim.claim_id(one) == claim.claim_id(renamed), (
        "a rename produced a different claim id, which means the claim is keyed "
        "on the handle and breaks the day somebody renames"
    )
    assert claim.claim_id(one) != claim.claim_id(other)

    claim.insert(conn, synthetic(one))
    with pytest.raises(sqlite3.IntegrityError):
        claim.insert(conn, synthetic(renamed))
    claim.insert(conn, synthetic(other))
    assert len(rows(conn, "namespace_claim")) == 2, (
        "two accounts claiming one namespace is a state this registry holds "
        "rather than one it resolves"
    )


# --------------------------------------------------------------------------- #
# Nothing writes a token, and nothing from the capture leaks sideways.


@pytest.mark.parametrize("key", [
    "provider_token", "access_token", "client_secret", "Authorization",
    "code_verifier", "api_key",
])
def test_a_credential_shaped_key_stops_the_run_before_anything_is_written(
        conn, record, key):
    """The cost of being wrong here is a secret in a public repository.

    Asserted to have landed: the probe key really is in the capture, and the
    same capture without it goes through, so the refusal is about this key.
    """
    poisoned = capture(**{key: "SYNTHETIC-VALUE-NOT-A-REAL-CREDENTIAL"})
    assert key in poisoned
    with pytest.raises(claim.Refused) as refused:
        claim.claim_from(poisoned, namespace="anyone", evidence=[])
    assert key in str(refused.value)
    assert not record.exists()
    assert rows(conn, "namespace_claim") == []


def test_a_credential_nested_inside_an_org_entry_is_caught_too(record):
    """A walk over the top-level keys only would miss this one."""
    nested = capture(orgs=[{"name": "synthetic-org-does-not-resolve",
                            "roleInOrg": "admin",
                            "api_token": "SYNTHETIC-VALUE-NOT-A-CREDENTIAL"}])
    with pytest.raises(claim.Refused):
        claim.observations_from(nested)
    assert not record.exists()


def test_the_record_carries_the_fields_the_row_carries_and_no_others(record):
    """The capture is gitignored and the record is not, so the projection is the
    line between them. A field the row has no column for has no business in a
    tracked file, and copying the capture dict is how that would happen.
    """
    fat = capture(email="nobody@test-provider.invalid",
                  picture="https://test-provider.invalid/avatar.png",
                  isPro=True)
    entry = claim.claim_from(fat, namespace="anyone", evidence=[])
    claim.append_record(entry, record)
    written = record.read_text()
    for leaked in ("nobody@test-provider.invalid", "avatar.png", "isPro"):
        assert leaked not in written, (
            f"{leaked} came out of the capture and into the tracked record, "
            "which collapses the separation those two files exist for"
        )
    assert set(json.loads(written)) == {
        "shape", "namespace", "provider", "subject", "handle", "claimed_at",
        "evidence", "derived_from", "is_synthetic",
    }


# --------------------------------------------------------------------------- #
# A membership is a look, not a status.


def observe_twice(conn, record, *, first, second):
    for when in (first, second):
        for entry in claim.observations_from(capture(captured_at=when)):
            entry = synthetic(entry)
            claim.append_record(entry, record)
            claim.insert(conn, entry)


def test_looking_again_appends_beside_the_last_look(conn, record):
    """Two looks are two rows, and the first one is still there afterwards."""
    observe_twice(conn, record, first="2026-01-05T00:00:00Z",
                  second="2026-03-05T00:00:00Z")
    seen = rows(conn, "namespace_membership_observation")
    assert [m["observed_at"] for m in seen] == [
        "2026-01-05T00:00:00Z", "2026-03-05T00:00:00Z"]
    assert len(record.read_text().splitlines()) == 2


def test_the_same_look_twice_is_refused_rather_than_overwritten(conn):
    """There is no path through this module that replaces an observation.

    Proven by the constraint rather than by reading the code: the id and the
    UNIQUE key are made of the same columns, so the convenient version of
    `insert` cannot be written without also changing one of them.
    """
    entry = synthetic(claim.observations_from(capture())[0])
    claim.insert(conn, entry)
    with pytest.raises(sqlite3.IntegrityError):
        claim.insert(conn, entry)


def test_the_module_contains_no_update_statement():
    source = (ROOT / "artifacts" / "claim.py").read_text()
    for line in source.splitlines():
        if line.lstrip().startswith("#"):
            continue
        assert "UPDATE " not in line.upper(), (
            f"an UPDATE in the module that writes memberships: {line.strip()!r}. "
            "A membership that can be updated is a standing fact with a date "
            "printed beside it, which is the badge this design is not."
        )


def test_an_observation_never_loses_the_endpoint_that_answered(conn):
    """An observation with no account of where it came from is a stored fact."""
    with pytest.raises(claim.Refused) as refused:
        claim.observations_from(capture(userinfo_endpoint=None))
    assert "where it came from" in str(refused.value)
    entry = synthetic(claim.observations_from(capture())[0])
    claim.insert(conn, entry)
    assert rows(conn, "namespace_membership_observation")[0]["source"] == ENDPOINT


def test_orgs_null_and_orgs_empty_are_two_facts_and_neither_is_a_row():
    """Both write nothing, and they write nothing for different reasons.

    `astro/src/lib/handshake.mjs` keeps the three states apart in the capture and this
    keeps them apart here: neither produces an observation, and neither is an
    error, which is the rule `schema/migrations/008` applies to an absence.
    """
    assert claim.observations_from(capture(orgs=None)) == []
    assert claim.observations_from(capture(orgs=[])) == []


def test_an_org_the_provider_did_not_name_stops_rather_than_being_dropped(conn):
    """`org` is NOT NULL, so there is no row. Skipping it loses one quietly."""
    with pytest.raises(claim.Refused) as refused:
        claim.observations_from(capture(orgs=[{"roleInOrg": "admin"}]))
    assert "Nothing was written" in str(refused.value)
    assert rows(conn, "namespace_membership_observation") == []


# --------------------------------------------------------------------------- #
# No closed enum on anything a provider or an author supplies.


def test_a_provider_a_kind_and_a_role_nobody_has_met_all_round_trip(conn):
    """Three open strings, carried rather than checked.

    A list of providers says which identity services a person is allowed to be
    a person at; a list of evidence kinds says which ways of establishing a
    claim are legitimate; a list of roles says which memberships count.
    """
    invented = capture(
        provider="a-provider-invented-next-year",
        orgs=[{"name": "synthetic-org-does-not-resolve",
               "roleInOrg": "a-role-nobody-has-invented-yet"}],
    )
    entry = synthetic(claim.claim_from(
        invented, namespace="allen",
        evidence=[claim.evidence_entry("a-kind-nobody-has-invented-yet",
                                       "Whatever this turns out to be.",
                                       "2026-01-05T00:00:00Z")],
    ))
    claim.insert(conn, entry)
    for observation in claim.observations_from(invented):
        claim.insert(conn, synthetic(observation))

    view = views.namespace_view(conn, "allen")["claims"][0]
    assert view["provider"] == "a-provider-invented-next-year"
    assert view["evidence"][0]["kind"] == "a-kind-nobody-has-invented-yet"
    assert view["memberships"][0]["role"] == "a-role-nobody-has-invented-yet"


def test_a_shape_with_no_reader_is_refused_for_having_no_reader(conn):
    """Refuse what cannot be verified, and say that rather than "unsupported".

    The difference is not decoration. "This shape is not allowed" declares which
    shapes are legitimate, which is the closed enum one level up; "there is no
    reader for it here" names a gap in this file that somebody can close.
    """
    with pytest.raises(claim.Refused) as refused:
        claim.insert(conn, {"shape": "somebody.else/claim@3", "namespace": "x"})
    said = str(refused.value)
    assert "no reader for it here" in said
    assert "illegitimate" in said
    assert rows(conn, "namespace_claim") == []


# --------------------------------------------------------------------------- #
# A claim is never a condition on anything.


def test_recording_a_claim_touches_nothing_outside_the_three_claim_tables(conn):
    """Publishing is not conditional on a claim, and this is the write side of it.

    The invariant tests next door prove no schema, view or page derives an order
    or a filter from a claim. This proves the recording step itself does not
    reach into a submission to mark it.
    """
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at) VALUES (?,?,?,?,?,?)",
        ("allen", "placeholder/does-not-resolve-1b", "kindness", "v1",
         "Their own words.", "2026-01-01T00:00:00Z"),
    )
    conn.commit()
    before = rows(conn, "submission")
    claim.insert(conn, synthetic(claim.claim_from(
        capture(), namespace="allen", evidence=[])))
    assert rows(conn, "submission") == before


def test_an_unclaimed_namespace_is_untouched_by_all_of_this(conn):
    claim.insert(conn, synthetic(claim.claim_from(
        capture(), namespace="allen", evidence=[])))
    assert views.namespace_view(conn, "somebody-else")["claims"] == []


# --------------------------------------------------------------------------- #
# The record is what survives the rebuild.


def test_a_claim_absent_from_the_record_is_absent_from_the_rebuild(tmp_path):
    """The reason the record is tracked, shown rather than stated.

    `make site` drops `registry.db`. A claim that exists only as a row is gone
    on the next build, and the page that showed it goes quiet with nothing
    saying why.
    """
    first = db.connect(tmp_path / "one.db")
    db.migrate(first)
    entry = synthetic(claim.claim_from(capture(), namespace="allen", evidence=[]))
    claim.insert(conn=first, entry=entry)
    assert views.namespace_view(first, "allen")["claims"]

    rebuilt = db.connect(tmp_path / "two.db")
    db.migrate(rebuilt)
    assert views.namespace_view(rebuilt, "allen")["claims"] == [], (
        "a fresh database already holds the claim, so this proves nothing"
    )
    record = tmp_path / "claims.jsonl"
    claim.append_record(entry, record)
    claim.replay(rebuilt, record)
    assert views.namespace_view(rebuilt, "allen")["claims"][0]["subject"] == SUBJECT


def test_a_record_replayed_into_a_database_that_holds_it_stops(tmp_path):
    """A database holding some of the record and not the rest is the state
    worth finding out about, so a duplicate is a stop and not a skip."""
    conn = db.connect(tmp_path / "t.db")
    db.migrate(conn)
    record = tmp_path / "claims.jsonl"
    claim.append_record(
        synthetic(claim.claim_from(capture(), namespace="allen", evidence=[])),
        record)
    claim.replay(conn, record)
    with pytest.raises(claim.Refused) as refused:
        claim.replay(conn, record)
    assert "seeded twice" in str(refused.value)


# --------------------------------------------------------------------------- #
# The real record, which is the one thing here that is not synthetic.
#
# These values come from a real sign-in on 2026-09-19 and are recorded in
# `V2.md`. They are written out here as a canary: if the record stops producing
# them, something moved that should not have.

REAL = {
    "namespace": "soham",
    "provider": "custom:huggingface",
    "subject": "62cf4580e7f6014c0ea2450f",
    "handle": "sohampadia",
    "claimed_at": "2026-09-19T16:51:32Z",
}
REAL_ORG = ("controlbun", "admin", "2026-09-19T16:51:32Z")


def real_record() -> list[dict]:
    entries = claim.read_record()
    assert entries, (
        "artifacts/claims.jsonl is empty, so the claim that was in seed.py has "
        "nowhere to come from and the rebuild will not produce it"
    )
    return entries


def test_the_record_still_produces_the_claim_the_sign_in_produced(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    db.migrate(conn)
    claim.replay(conn, claim.RECORD)

    row = next(r for r in rows(conn, "namespace_claim")
               if r["namespace"] == REAL["namespace"])
    for field, value in REAL.items():
        assert row[field] == value, f"{field} changed: {row[field]!r}"
    assert row["is_synthetic"] == 0

    membership = rows(conn, "namespace_membership_observation")[0]
    assert (membership["org"], membership["role"],
            membership["observed_at"]) == REAL_ORG
    assert membership["source"].startswith("https://huggingface.co/")


def test_the_canary_above_is_actually_comparing_something(tmp_path):
    """The bite for the test above. A record with one character changed has to
    fail it, or that test is a green light wired to nothing."""
    bent = tmp_path / "bent.jsonl"
    lines = []
    for entry in real_record():
        if entry.get("shape") == claim.CLAIM:
            entry = {**entry, "subject": "SYNTHETIC-NOT-THE-REAL-SUBJECT"}
        lines.append(json.dumps(entry, sort_keys=True))
    bent.write_text("\n".join(lines) + "\n")

    conn = db.connect(tmp_path / "t.db")
    db.migrate(conn)
    claim.replay(conn, bent)
    row = next(r for r in rows(conn, "namespace_claim")
               if r["namespace"] == REAL["namespace"])
    assert row["subject"] != REAL["subject"]


def test_the_seed_script_no_longer_types_a_claim():
    """The defect this whole path exists to remove.

    Not a style preference. Every other real value in this corpus is derived
    from a file by a script, and this one was read off a screen and typed.
    """
    source = (ROOT / "artifacts" / "seed.py").read_text()
    for table in ("namespace_claim", "namespace_claim_evidence",
                  "namespace_membership_observation"):
        assert f"INSERT INTO {table}" not in source, (
            f"{table} is written by hand in seed.py again, which puts a subject "
            "id back into a file somebody types into"
        )
    assert "claim.replay(conn)" in source, (
        "seed.py no longer replays the claim record, so the claim is gone from "
        "the rebuild entirely"
    )


def test_the_capture_stays_ignored_and_the_record_is_tracked():
    """Two files, one dated statement each, and only one of them is published.

    Checked against git rather than against the text of `.gitignore`, because
    the comment in that file used to describe an intention that was not a rule.
    """
    def ignored(path: Path) -> bool:
        return subprocess.run(
            ["git", "check-ignore", "-q", str(path)], cwd=ROOT,
        ).returncode == 0

    assert ignored(claim.CAPTURES), (
        "the sign-in capture is not ignored, and it is a dated statement about "
        "a real person in a public repository"
    )
    assert not ignored(claim.RECORD), (
        "the claim record is ignored, so the rebuild has nothing to replay on "
        "anybody else's checkout"
    )


def test_a_line_the_database_refuses_never_reaches_the_record(tmp_path):
    """The order inside `write` is the whole argument, so it is checked.

    A row with no record line is lost on the next `make site`, which costs one
    command rerun. A record line the database refuses is permanent: the record
    is append-only and `replay` stops on a duplicate, so every build from then
    on stops with it.
    """
    conn = db.connect(tmp_path / "t.db")
    db.migrate(conn)
    record = tmp_path / "claims.jsonl"
    entry = synthetic(claim.claim_from(capture(), namespace="allen", evidence=[]))

    claim.write(conn, [entry], record)
    assert len(record.read_text().splitlines()) == 1

    with pytest.raises(claim.Refused) as refused:
        claim.write(conn, [entry], record)
    assert "already holds this one" in str(refused.value)
    assert len(record.read_text().splitlines()) == 1, (
        "the refused line was appended anyway, which makes every later replay "
        "stop on a duplicate the record can never lose"
    )


def test_a_database_with_no_schema_is_named_rather_than_traced(tmp_path):
    """A mistyped --db used to reach an INSERT and print a traceback."""
    with pytest.raises(claim.Refused) as refused:
        claim.opened(tmp_path / "not-the-one-you-meant.db")
    assert "Nothing was written" in str(refused.value)
