"""Proof that the model being part of the identity actually bites.

`schema/migrations/010` widened the submission key from three columns to four.
Every check here reconstructs the behavior the old key produced and asserts the
new code refuses it, because a widened key that nothing exercises is a widened
key until the next person writes a three-column lookup.

The case that makes all of this necessary is one author holding one label on two
models. It does not occur in the real corpus and it is the whole reason for the
change, so it is built here as a labeled synthetic row: the model ids are
`fixtures/build.py`'s placeholders, which resolve to nothing and say so in their
own names, and no number below is a measurement of anything.

Four things the old key did, each asserted to be gone:

- Collided. Two models, one author, one label, one version was one row.
- Resolved a short reference by picking. It now raises and names both.
- Looked an artifact up by three quarters of its key, which returns whichever
  row the database reaches first.
- Printed a reference that does not say which artifact it is about.

Plus the migration's own guard, which is the one check that runs against a
database nobody in this repository has: somebody else's, with a submission the
carry-across cannot answer for.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import client, comparison, db, order, ref, views  # noqa: E402

# The two placeholder models `fixtures/build.py` writes. Neither resolves to
# anything and both say so in their own name.
MODEL_A = "placeholder/does-not-resolve-1b"
MODEL_B = "placeholder/other-architecture-7b"


@pytest.fixture
def conn(tmp_path):
    path = tmp_path / "bite.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return db.connect(path)


def database_of(conn: sqlite3.Connection) -> str:
    return conn.execute("PRAGMA database_list").fetchone()[2]


def second_model(conn: sqlite3.Connection) -> None:
    """Alice's same take on the same word, against the other model.

    SYNTHETIC. Alice's `kindness@v1` exists in the fixtures on `MODEL_A`; this
    adds the row that was previously unwritable, pointing at bob's fixture
    tensor so the two rows are distinguishable by their bytes as well as by
    their key. Nothing here is a measurement.
    """
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at,is_synthetic) VALUES (?,?,?,?,?,?,1)",
        ("alice", MODEL_B, "kindness", "v1",
         "SYNTHETIC. The same author's take on the same word against a second "
         "model. Neither supersedes the other.", "2026-09-12T00:00:00Z"),
    )
    conn.execute(
        "INSERT INTO intervention (id,author,model_id,label,version,kind,"
        "model_revision,layer,layer_convention,hook_point,shape,dtype,"
        "artifact_path,is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        ("iv_alice_b", "alice", MODEL_B, "kindness", "v1", "direction",
         "1" * 40, 12, "block-0indexed", "resid_pre", "[8]", "float32",
         "fixtures/bob_kindness_v1.safetensors"),
    )
    conn.commit()


# --------------------------------------------------------------------------- #
# The string rule.


@pytest.mark.parametrize("text,author,model,label,version", [
    ("soham/allenai/Olmo-3-1125-32B/pro-human@meandiff",
     "soham", "allenai/Olmo-3-1125-32B", "pro-human", "meandiff"),
    ("soham/Qwen/Qwen3-8B/trauma@d61-diffmeans-expository-L34",
     "soham", "Qwen/Qwen3-8B", "trauma", "d61-diffmeans-expository-L34"),
    # No distributor. One segment is a model id and always was: the model is the
    # middle rather than a fixed segment count, which is the whole reason this
    # parses at all.
    ("alice/gpt2/kindness@v1", "alice", "gpt2", "kindness", "v1"),
    # Four segments in the middle. Nothing counts them.
    ("alice/a/b/c/d/kindness@v1", "alice", "a/b/c/d", "kindness", "v1"),
    # The short form, which carries no model and is answered from the corpus.
    ("alice/kindness@v1", "alice", None, "kindness", "v1"),
    ("alice/kindness", "alice", None, "kindness", None),
    # A version with an `@` in it. First `@` ends the label, which is 001's rule
    # kept rather than a new one.
    ("a/m/l@v@2", "a", "m", "l", "v@2"),
])
def test_the_split_takes_the_middle_as_the_model(text, author, model, label, version):
    got = ref.parse(text)
    assert (got.author, got.model, got.label, got.version) == (
        author, model, label, version)


@pytest.mark.parametrize("text", ["kindness", "kindness@v1", "/kindness", "a//b"])
def test_a_bare_label_is_refused_at_the_split(text):
    """And an empty segment with it: `a//b` is not a model id, it is a typo."""
    with pytest.raises(ref.BareLabelError):
        ref.parse(text)


def test_format_and_parse_are_inverses():
    parts = ("soham", "allenai/Olmo-3-1125-32B", "pro-human", "meandiff")
    got = ref.parse(ref.format(*parts))
    assert (got.author, got.model, got.label, got.version) == parts


# --------------------------------------------------------------------------- #
# The key.


def test_the_old_key_collided_and_this_one_does_not(conn):
    """The row that could not be written before.

    Under `PRIMARY KEY (author, label, version)` this insert raised
    `IntegrityError`, which is the bug: two different artifacts in two different
    residual bases were one row's worth of identity.
    """
    second_model(conn)
    rows = conn.execute(
        "SELECT model_id FROM submission WHERE author='alice' AND label='kindness'"
    ).fetchall()
    assert sorted(r["model_id"] for r in rows) == sorted([MODEL_A, MODEL_B])


def test_the_same_key_on_one_model_still_collides(conn):
    """The widening did not make the key permissive.

    A second row with all four columns equal is still one submission, because
    immutability is what a pin depends on.
    """
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO submission (author,model_id,label,version,definition,"
            "created_at,is_synthetic) VALUES (?,?,?,?,?,?,1)",
            ("alice", MODEL_A, "kindness", "v1", "a second take on one model",
             "2026-09-12T00:00:00Z"),
        )


def test_a_short_reference_refuses_rather_than_picking(conn):
    """It names both, in full, or the error is a dead end.

    The old client had no model in the key at all, so this question could not be
    asked. The failure it would have produced once the column existed is a
    lookup on `author` and `label` returning two rows and the first one winning,
    which is the registry choosing a model on the caller's behalf.
    """
    second_model(conn)
    with pytest.raises(client.Ambiguous) as caught:
        client.load("alice/kindness", database=database_of(conn))

    said = str(caught.value)
    for model in (MODEL_A, MODEL_B):
        assert f"alice/{model}/kindness" in said, (
            f"{model} is not named, so the reader cannot write the reference "
            "that would resolve"
        )


def test_a_short_reference_with_a_version_still_refuses_on_the_model(conn):
    """The version does not disambiguate a model, and must not appear to."""
    second_model(conn)
    with pytest.raises(client.Ambiguous):
        client.load("alice/kindness@v1", database=database_of(conn))


def test_the_short_form_still_resolves_while_it_names_one(conn):
    """Because the convenience is the reason anybody tolerates the long form."""
    got = client.load("alice/kindness", database=database_of(conn))
    assert got.ref == f"alice/{MODEL_A}/kindness@v1"
    # And the full reference it hands back resolves to the same row.
    assert client.load(got.ref, database=database_of(conn)).ref == got.ref


def test_naming_the_model_resolves_each_one_separately(conn):
    second_model(conn)
    a = client.load(f"alice/{MODEL_A}/kindness@v1", database=database_of(conn))
    b = client.load(f"alice/{MODEL_B}/kindness@v1", database=database_of(conn))
    assert a.model_id == MODEL_A and b.model_id == MODEL_B
    assert a.ref != b.ref
    # Different artifacts, not one artifact seen twice. The layer differs because
    # the two fixture models are hooked at different layers.
    assert a.contract.layer != b.contract.layer


# --------------------------------------------------------------------------- #
# The three-column lookups that would return the wrong artifact.


def test_the_claimant_view_does_not_reach_the_other_models_artifact(conn):
    """The lookup `views.claimant_view` does, keyed on the row it was handed.

    On three columns this query matches two interventions and `fetchone`
    returns whichever the database reaches first, so one of the two pages
    renders the other one's layer, hook point and digest under its own heading.
    Nothing fails; the page is simply about a different artifact than it says.
    """
    second_model(conn)
    rows = {
        r["model_id"]: r for r in conn.execute(
            "SELECT * FROM submission WHERE author='alice' AND label='kindness'"
        )
    }
    for model, row in rows.items():
        view = views.claimant_view(conn, row)
        assert view["model_id"] == model
        assert view["ref"] == f"alice/{model}/kindness@v1"

    # And the two views are about different artifacts, which is the thing the
    # three-column lookup could not guarantee.
    assert (rows[MODEL_A] is not rows[MODEL_B])
    assert (views.claimant_view(conn, rows[MODEL_A])["artifact_path"]
            != views.claimant_view(conn, rows[MODEL_B])["artifact_path"])


def test_engagement_is_counted_against_the_right_artifact(conn):
    """`order.engagement` looked an intervention up by three columns too.

    alice's fixture row carries an attack; the second model's row carries none.
    On three columns both queries hit the same first row and the second model's
    submission inherits scrutiny nobody performed on it, which is an ordering
    key derived from the wrong artifact.
    """
    second_model(conn)
    on_a = order.engagement(conn, "alice", MODEL_A, "kindness", "v1")
    on_b = order.engagement(conn, "alice", MODEL_B, "kindness", "v1")
    assert on_a > 0, "the fixture attack is gone, so this test checks nothing"
    assert on_b == 0, (
        "the second model's submission was credited with scrutiny of the first "
        "model's artifact"
    )


def test_the_similarity_matrix_keys_both_rows_apart(conn):
    """Two claimants of one word that are not in the same basis.

    Keyed on three columns the two collapse to one string, so the matrix holds
    one row where there are two and the second silently overwrites the first.
    """
    second_model(conn)
    matrix = comparison.similarity_matrix(conn, "kindness")
    alices = sorted(k for k in matrix if k.startswith("alice/"))
    assert alices == [f"alice/{MODEL_A}/kindness@v1", f"alice/{MODEL_B}/kindness@v1"]

    # And the angle between them is refused rather than computed, because they
    # are not in the same residual basis.
    cell = matrix[alices[0]][alices[1]]
    assert cell["v"] is None
    assert cell["why"] == "different model or revision"


# --------------------------------------------------------------------------- #
# The migration's own guard.


def pre_010(path: Path) -> sqlite3.Connection:
    """A database with every migration before 010 applied and none after."""
    conn = db.connect(path)
    conn.execute("CREATE TABLE _migration (name TEXT PRIMARY KEY,"
                 " applied_at TEXT NOT NULL)")
    for sql in sorted(db.MIGRATIONS_DIR.glob("*.sql")):
        if sql.name.startswith("010"):
            break
        conn.executescript(sql.read_text())
        conn.execute("INSERT INTO _migration VALUES (?, 'before')", (sql.name,))
    conn.commit()
    return conn


def old_submission(conn: sqlite3.Connection, author: str, version: str = "v1") -> None:
    conn.execute(
        "INSERT INTO submission (author,label,version,definition,created_at,"
        "is_synthetic) VALUES (?,?,?,?,?,1)",
        (author, "kindness", version, "SYNTHETIC. A row written before 010.",
         "2026-09-12T00:00:00Z"),
    )


def old_intervention(conn: sqlite3.Connection, iv_id: str, author: str,
                     model: str, version: str = "v1") -> None:
    conn.execute(
        "INSERT INTO intervention (id,author,label,version,kind,model_id,layer,"
        "layer_convention,hook_point,shape,dtype,is_synthetic)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,1)",
        (iv_id, author, "kindness", version, "direction", model, 4,
         "block-0indexed", "resid_post", "[8]", "float32"),
    )


def test_the_migration_carries_the_model_across(tmp_path):
    """The premise the migration relies on, exercised rather than trusted."""
    conn = pre_010(tmp_path / "old.db")
    old_submission(conn, "alice")
    old_intervention(conn, "iv_alice", "alice", MODEL_A)
    conn.commit()

    assert "010_model_in_identity.sql" in db.migrate(conn)
    row = conn.execute("SELECT * FROM submission").fetchone()
    assert row["model_id"] == MODEL_A


def test_the_migration_refuses_a_submission_with_no_artifact(tmp_path):
    """There is no model to carry across, and nothing may invent one.

    Without the guard the join drops the row and the migration reports success
    on a database that has quietly lost somebody's submission.
    """
    conn = pre_010(tmp_path / "orphan.db")
    old_submission(conn, "alice")
    old_intervention(conn, "iv_alice", "alice", MODEL_A)
    # The one with no intervention attached, which the schema has always allowed
    # and which 010 cannot answer for.
    old_submission(conn, "bob")
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        db.migrate(conn)


def test_the_migration_refuses_one_submission_on_two_models(tmp_path):
    """The other direction: the carry-across would make two rows out of one.

    Also a state the old schema allowed, since `intervention.id` is the primary
    key and nothing stopped two of them sharing a submission. Duplicating the
    row would be the migration deciding that one author's one take was two
    submissions, which is a judgment and not a translation.
    """
    conn = pre_010(tmp_path / "forked.db")
    old_submission(conn, "alice")
    old_intervention(conn, "iv_a", "alice", MODEL_A)
    old_intervention(conn, "iv_b", "alice", MODEL_B)
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        db.migrate(conn)


def test_the_dependent_tables_follow_the_key(tmp_path):
    """`recipe`, `pin` and `support_card` carry the model or the key is a lie.

    A foreign key that names three of four columns does not reference the
    submission any more, and SQLite would have refused the table outright. What
    this asserts is the other half: the rows that existed before are still
    attached to the submission they were about.
    """
    conn = pre_010(tmp_path / "deps.db")
    old_submission(conn, "alice")
    old_intervention(conn, "iv_alice", "alice", MODEL_A)
    conn.execute(
        "INSERT INTO recipe (id,author,label,version,profile,payload_json)"
        " VALUES ('rc','alice','kindness','v1','someone/profile-v1','{}')")
    conn.execute(
        "INSERT INTO pin (id,pinned_by,pinned_at,purpose,author,label,version,"
        "alternatives_json) VALUES ('pn','someone','2026-09-12T00:00:00Z',"
        "'a purpose','alice','kindness','v1','[]')")
    conn.execute(
        "INSERT INTO support_card (id,author,label,version,reporter,reported_at,"
        "purpose,expected,is_synthetic) VALUES ('sc','alice','kindness','v1',"
        "'someone','2026-09-12T00:00:00Z','a purpose','what the contract said',1)")
    conn.commit()

    db.migrate(conn)
    for table in ("recipe", "pin", "support_card"):
        row = conn.execute(f"SELECT model_id FROM {table}").fetchone()
        assert row["model_id"] == MODEL_A, f"{table} lost its submission"
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


# --------------------------------------------------------------------------- #
# What it must not become.


def test_the_model_is_not_an_ordering_key(conn):
    """Identity, not a facet that ranks.

    Two rows differing only in model come back in the ordering the page names,
    which is recency here, and not grouped or sorted by model id. If ordering
    ever derived from the model, `MODEL_A` sorting before `MODEL_B` would put
    one model's artifacts above another's with nothing on screen saying why.
    """
    second_model(conn)
    conn.execute(
        "UPDATE submission SET created_at='2026-09-13T00:00:00Z'"
        " WHERE author='alice' AND model_id=?", (MODEL_B,))
    conn.commit()

    rows = order.apply_order(conn, db.claimants(conn, "kindness"),
                             key=order.ORDER_RECENT)
    alices = [r["model_id"] for r in rows if r["author"] == "alice"]
    assert alices == [MODEL_B, MODEL_A], (
        "recency no longer decides the order between two takes by one author"
    )
    assert MODEL_B > MODEL_A, "the fixture names no longer make this test mean anything"


def test_a_bare_label_still_views_across_models(conn):
    """A bare label is owned by nobody, so it is not narrowed to one model.

    Narrowing it here would make the view a statement about which model the word
    belongs to, which is the designation this registry does not make.
    """
    second_model(conn)
    models = {s.model_id for s in client.claimants("kindness",
                                                   database=database_of(conn))}
    assert models == {MODEL_A, MODEL_B}
