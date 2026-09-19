"""A namespace, and whoever has claimed it, which is almost always nobody.

The invariant tests next door check that nothing sorts, filters or gates on a
claim. These check the other half: that the thing exists, travels intact from
the row to the client and to the page, and that the unclaimed state is rendered
as a state rather than as a blank.

Everything here builds its own database from the migrations, except where it
reads the built site, which is what `make verify` has already produced by the
time this runs.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import client, db, export, views  # noqa: E402

DIST = ROOT / "astro" / "dist"
EXPORT = ROOT / "astro" / "src" / "data" / "registry.json"

# Obviously not a person. Nothing below is an identity any provider issued, and
# the only real one in this project is recorded in `V2.md` and is not here.
PROVIDER = "test-provider-does-not-exist"
SUBJECT = "SYNTHETIC-SUBJECT-a"
OTHER_SUBJECT = "SYNTHETIC-SUBJECT-b"


@pytest.fixture
def conn(tmp_path) -> sqlite3.Connection:
    c = db.connect(tmp_path / "t.db")
    db.migrate(c)
    return c


def claim(c, *, id, namespace, subject=SUBJECT, handle=None, at="2026-01-01T00:00:00Z"):
    c.execute(
        "INSERT INTO namespace_claim (id,namespace,provider,subject,handle,"
        "claimed_at,is_synthetic) VALUES (?,?,?,?,?,?,1)",
        (id, namespace, PROVIDER, subject, handle, at),
    )
    return id


# --------------------------------------------------------------------------- #
# The shape of the row.


def test_a_namespace_starts_unclaimed_and_that_is_not_an_error(conn):
    """The ordinary case, and the one the whole design is arranged around.

    Not a raise, not a None, not a sentinel. An empty list of claims, which the
    page renders in words.
    """
    view = views.namespace_view(conn, "nobody-has-claimed-this")
    assert view == {"namespace": "nobody-has-claimed-this", "claims": []}


def test_a_submission_needs_no_claim(conn):
    """Publishing is not conditional on having an account.

    The schema check next door proves no foreign key says so. This proves the
    write actually goes through, because a constraint nobody exercises is a
    constraint nobody has tested.
    """
    conn.execute(
        "INSERT INTO submission (author,model_id,label,version,definition,"
        "created_at) VALUES (?,?,?,?,?,?)",
        ("someone", "placeholder/does-not-resolve-1b", "kindness", "v1",
         "Their own words.", "2026-01-01T00:00:00Z"),
    )
    conn.commit()
    assert views.namespace_view(conn, "someone")["claims"] == []


def test_two_accounts_may_claim_one_namespace(conn):
    """A contested name is a state this registry holds, not one it resolves.

    Both rows come back, in the order they were claimed, and nothing here marks
    one as the holder.
    """
    claim(conn, id="c1", namespace="allen", subject=SUBJECT, at="2026-01-01T00:00:00Z")
    claim(conn, id="c2", namespace="allen", subject=OTHER_SUBJECT,
          at="2026-02-01T00:00:00Z")
    conn.commit()

    claims = views.namespace_view(conn, "allen")["claims"]
    assert [c["subject"] for c in claims] == [SUBJECT, OTHER_SUBJECT]
    assert not any("holder" in k or "primary" in k for c in claims for k in c)


def test_one_account_claims_one_namespace_once(conn):
    claim(conn, id="c1", namespace="allen")
    with pytest.raises(sqlite3.IntegrityError):
        claim(conn, id="c2", namespace="allen")


def test_the_same_account_may_claim_several_namespaces(conn):
    claim(conn, id="c1", namespace="allen")
    claim(conn, id="c2", namespace="allen-personal")
    conn.commit()
    assert len(views.namespace_view(conn, "allen")["claims"]) == 1
    assert len(views.namespace_view(conn, "allen-personal")["claims"]) == 1


def test_the_evidence_kind_is_not_a_set_anything_enforces(conn):
    """A kind this repository has never seen stores and reads back.

    The same argument `kind`, `hook_point`, `profile` and artifact file format
    already make. A list of the ways of establishing a claim we happen to have
    met is a list of the ways that are allowed.
    """
    claim(conn, id="c1", namespace="allen")
    conn.execute(
        "INSERT INTO namespace_claim_evidence (claim_id,kind,detail,recorded_at)"
        " VALUES (?,?,?,?)",
        ("c1", "a-kind-nobody-has-invented-yet", "Whatever this turns out to be.",
         "2026-01-02T00:00:00Z"),
    )
    conn.commit()
    evidence = views.namespace_view(conn, "allen")["claims"][0]["evidence"]
    assert [e["kind"] for e in evidence] == ["a-kind-nobody-has-invented-yet"]


def test_the_provider_is_not_a_set_anything_enforces(conn):
    conn.execute(
        "INSERT INTO namespace_claim (id,namespace,provider,subject,claimed_at)"
        " VALUES (?,?,?,?,?)",
        ("c1", "allen", "some-provider-invented-next-year", "sub-x",
         "2026-01-01T00:00:00Z"),
    )
    conn.commit()
    assert views.namespace_view(conn, "allen")["claims"][0]["provider"] == (
        "some-provider-invented-next-year"
    )


# --------------------------------------------------------------------------- #
# Membership is an observation with a date on it.


def observe(conn, *, id, org, role, at, subject=SUBJECT):
    conn.execute(
        "INSERT INTO namespace_membership_observation (id,provider,subject,org,"
        "role,observed_at,source,is_synthetic) VALUES (?,?,?,?,?,?,?,1)",
        (id, PROVIDER, subject, org, role, at,
         "https://test-provider.invalid/userinfo"),
    )


def test_looking_again_appends_rather_than_overwrites(conn):
    """The history is the point.

    A membership seen in January and again in March is two observations. If the
    second replaced the first, the page could say when it last looked and could
    not say that it had looked before, and a membership that quietly stopped
    being true would leave no trace of having ever been checked.
    """
    claim(conn, id="c1", namespace="allen")
    observe(conn, id="m1", org="allen-institute", role="member",
            at="2026-01-05T00:00:00Z")
    observe(conn, id="m2", org="allen-institute", role="admin",
            at="2026-03-05T00:00:00Z")
    conn.commit()

    seen = views.namespace_view(conn, "allen")["claims"][0]["memberships"]
    assert [(m["role"], m["observed_at"]) for m in seen] == [
        ("member", "2026-01-05T00:00:00Z"),
        ("admin", "2026-03-05T00:00:00Z"),
    ]


def test_the_same_observation_at_the_same_moment_is_one_row(conn):
    claim(conn, id="c1", namespace="allen")
    observe(conn, id="m1", org="allen-institute", role="member",
            at="2026-01-05T00:00:00Z")
    with pytest.raises(sqlite3.IntegrityError):
        observe(conn, id="m2", org="allen-institute", role="member",
                at="2026-01-05T00:00:00Z")


def test_an_observation_is_never_reported_without_its_date(conn):
    """A membership with the date taken off is a badge, which is the failure."""
    claim(conn, id="c1", namespace="allen")
    observe(conn, id="m1", org="allen-institute", role=None,
            at="2026-01-05T00:00:00Z")
    conn.commit()
    m = views.namespace_view(conn, "allen")["claims"][0]["memberships"][0]
    assert m["observed_at"] and m["source"]
    # A role the provider did not state is absent, not a lesser membership.
    assert m["role"] is None


def test_memberships_follow_the_account_not_the_handle(conn):
    """Two accounts, one namespace, and the observations do not cross over."""
    claim(conn, id="c1", namespace="allen", subject=SUBJECT, handle="same-name")
    claim(conn, id="c2", namespace="allen", subject=OTHER_SUBJECT,
          handle="same-name", at="2026-02-01T00:00:00Z")
    observe(conn, id="m1", org="allen-institute", role="member",
            at="2026-01-05T00:00:00Z", subject=SUBJECT)
    conn.commit()

    claims = views.namespace_view(conn, "allen")["claims"]
    assert len(claims[0]["memberships"]) == 1
    assert claims[1]["memberships"] == []


# --------------------------------------------------------------------------- #
# It travels: row, client, export, page.


def test_the_client_hands_back_claims_and_no_boolean(conn, tmp_path):
    claim(conn, id="c1", namespace="allen", handle="allen-on-the-day")
    conn.execute(
        "INSERT INTO namespace_claim_evidence (claim_id,kind,detail,recorded_at)"
        " VALUES (?,?,?,?)",
        ("c1", "doi", "10.5555/synthetic-not-a-real-doi", "2026-01-02T00:00:00Z"),
    )
    observe(conn, id="m1", org="allen-institute", role="admin",
            at="2026-01-05T00:00:00Z")
    conn.commit()

    # The fixture's database, reopened by name, so this is the client's own
    # path through `views` rather than the connection the rows were written on.
    database = tmp_path / "t.db"
    ns = client.namespace("allen", database=database)
    assert ns.name == "allen"
    one = ns.claims[0]
    assert one.subject == SUBJECT
    assert one.handle == "allen-on-the-day"
    assert one.account == f"{PROVIDER}:{SUBJECT}"
    assert one.evidence[0].kind == "doi"
    assert one.memberships[0].observed_at == "2026-01-05T00:00:00Z"
    # No flag to sort on, here or anywhere.
    assert not hasattr(ns, "is_claimed")
    assert not any(f.startswith("is_") for f in vars(one) if f != "is_synthetic")


def test_an_unclaimed_namespace_is_not_a_lookup_failure(tmp_path):
    """`load` raises on a reference that was supposed to resolve. A namespace
    never was: the string is free, so asking about an unclaimed one answers."""
    database = tmp_path / "t.db"
    db.migrate(db.connect(database))
    assert client.namespace("anyone-at-all", database=database).claims == []


def test_the_export_carries_claims_as_a_list_and_never_as_a_scalar(conn):
    """The shape is the guard.

    A scalar is what a table sorts on, so the erosion this design is most
    exposed to is one boolean appearing beside `engagement` in an owner entry.
    Every key in the export mentioning a claim has to be a list of them.
    """
    claim(conn, id="c1", namespace="allen")
    conn.commit()
    payload = export.build(conn)

    entry = next(o for o in payload["owner_index"] if o["owner"] == "allen")
    assert isinstance(entry["claims"], list) and len(entry["claims"]) == 1
    for o in payload["owner_index"]:
        for key, value in o.items():
            if "claim" in key.lower():
                assert isinstance(value, list), (
                    f"owner_index.{key} is a scalar derived from a claim, which "
                    "is the one shape a column can be ordered by"
                )


def test_a_claim_date_never_reaches_the_ordering_keys(conn):
    """`latest` is what somebody did to the work. A claim is not that.

    Left in, the recency default would put a claimed namespace above an
    unclaimed one that published the same day, with nothing on screen saying
    why. This is the version of the rule that survives somebody adding a date
    field without reading the comment beside it.
    """
    claim(conn, id="c1", namespace="allen", at="2030-01-01T00:00:00Z")
    conn.commit()
    entry = next(o for o in export.build(conn)["owner_index"] if o["owner"] == "allen")
    assert entry["latest"] is None, (
        "a namespace whose only record is a claim has nothing dated to order by, "
        "and borrowing the claim date would order the list by claim status"
    )
    assert entry["engagement"] == 0


# --------------------------------------------------------------------------- #
# What the reader is shown.


def built(owner: str) -> str:
    path = DIST / owner / "index.html"
    if not path.exists():
        pytest.skip(f"{path.relative_to(ROOT)} not built; run `make site`")
    return path.read_text()


def visible(html_text: str) -> str:
    raw = html_text
    for tag in ("script", "style", "svg"):
        raw = re.sub(rf"<{tag}.*?</{tag}>", " ", raw, flags=re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", raw).split())


def test_an_unclaimed_namespace_says_so_on_its_own_page():
    """In words, the way every other absence here renders.

    The namespace is found rather than named. This test used to point at
    `soham` and say in its own docstring that `soham` is unclaimed, which was
    true for about an hour: a real sign-in happened and the claim was recorded,
    and the test then failed for the one reason that is not a defect, which is
    that the corpus moved on. A fixture list that names a row is a list that
    goes stale, which is the failure this repository keeps rediscovering.
    """
    payload = json.loads(EXPORT.read_text())
    unclaimed = sorted(
        o["owner"] for o in payload["owner_index"] if not o.get("claims")
    )
    assert unclaimed, (
        "every namespace in the corpus is claimed, so this check cannot see "
        "the unclaimed rendering and is inert"
    )
    text = visible(built(unclaimed[0]))
    assert "is unclaimed" in text
    assert "Nobody has bound an account to it" in text


def test_a_claimed_namespace_shows_the_account_and_the_date():
    text = visible(built("alice"))
    assert "Claimed on Sep 12, 2026" in text
    assert "SYNTHETIC-SUBJECT-NOT-ISSUED-BY-ANY-PROVIDER-alice" in text
    # The handle is shown as what it was called that day, and said to be that.
    assert "which called itself" in text


def test_a_membership_never_renders_without_its_date():
    text = visible(built("alice"))
    assert "Membership of" in text
    for match in re.finditer(r"Membership of .{0,200}", text):
        assert "confirmed on" in match.group(0), (
            "a membership rendered with no date is the badge this design "
            "exists to not be"
        )


def test_no_page_offers_to_sort_or_filter_by_a_claim():
    """The rendered version of the invariant next door.

    A template can be clean and the page still carry a control, because the
    control is often a data attribute the ordering script picks up.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    # `claim` is three words on this site: a claimant of a label, a label an
    # owner has claimed, and the namespace sense this design added. Only a
    # control whose label leads with the third is a finding. See the same
    # separation in `tests/test_invariants.py`.
    offenders = []
    for page in sorted(DIST.rglob("index.html")):
        html_text = page.read_text()
        for m in re.finditer(r"<(?:button|th)[^>]*>[^<]*", html_text):
            if re.search(r">\s*(namespace\s+claim|claim(?!ant)|held\s+by)",
                         m.group(0), re.I) and \
                    re.search(r"data-(col|sort)", m.group(0), re.I):
                offenders.append(f"{page.relative_to(DIST)}: {m.group(0)[:80]}")
        for m in re.finditer(r"data-(?:claimed|claim-status)[^>]*", html_text):
            offenders.append(f"{page.relative_to(DIST)}: {m.group(0)[:80]}")
    assert not offenders, "\n".join(offenders)


def test_the_owners_table_carries_no_claim_column():
    """Deliberately absent, and this is where that decision is enforced.

    A claim renders on the namespace's own page and nowhere else. A column in a
    list of namespaces puts claimed and unclaimed side by side, which is where a
    reader starts taking one for better and somebody reasonable asks to sort by
    it next.

    Checked as the absence of the claim block rather than as a word test. The
    first version of this matched the substring and failed on "Labels claimed",
    which is a count of what an owner has published and has nothing to do with
    accounts: the third time on this project that a word list caught a sentence
    instead of the thing it was aimed at.
    """
    path = DIST / "owners" / "index.html"
    if not path.exists():
        pytest.skip("owners page not built; run `make site`")
    raw = path.read_text()
    assert "<th" in raw, "the owners table has no headers, so this checks nothing"
    assert 'class="claim"' not in raw, (
        "the claim block renders in the list of namespaces, where claimed and "
        "unclaimed sit side by side"
    )
    assert "is unclaimed" not in visible(raw)
    for header in re.findall(r"<th[^>]*>(.*?)</th>", raw, re.S):
        assert not re.search(r">\s*(namespace\s+claim|claim(?!ant)|held\s+by)",
                             f">{header}", re.I), (
            f"the owners table offers a claim column: {header.strip()!r}"
        )


def test_the_export_on_disk_agrees_with_the_page():
    """Transport, the same question the falsifier asks about numbers."""
    if not EXPORT.exists():
        pytest.skip("export not built; run `make site`")
    payload = json.loads(EXPORT.read_text())
    claimed = [o for o in payload["owner_index"] if o["claims"]]
    unclaimed = [o for o in payload["owner_index"] if not o["claims"]]
    assert unclaimed, "every namespace is claimed, which the fixtures do not do"
    for owner in claimed:
        text = visible(built(owner["owner"]))
        for c in owner["claims"]:
            assert c["subject"] in text
            for e in c["evidence"]:
                assert e["detail"][:40] in text
