"""The local intake form, and the wall between it and the published site.

Two halves, and the second is the one that matters most.

The first drives the server in process: link mode against a stand-in Hub, bytes
mode with the upload replaced, and the refusals in between. What it asserts is
that both modes end as a row pointing at a pinned remote, that nothing writes
`served_repo`, and that no artifact bytes are left anywhere afterwards.

The second reads `astro/dist` and `astro.config.mjs`. `artifacts/intake.py` is a
running process that accepts a file and writes rows, which is exactly the thing
`DECISIONS.md` 2026-09-17 says fires the dual-use trigger when anybody but the
operator can reach it. The binding is what keeps it clear of that, so the binding
is checked, and so is the published site, because the way this leaks is not
somebody rebinding the socket. It is a form appearing on the static site months
from now with nothing failing.

Every tensor written here is a synthetic fixture, labeled in its own header, for
the reason `fixtures/SYNTHETIC.md` gives: an integer ramp is obvious on sight and
no number here is a measurement of anything.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import save_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "artifacts"))

import agent_handoff  # noqa: E402
import intake  # noqa: E402
import publish  # noqa: E402
from controlbun import artifact, db  # noqa: E402

# Forty hex characters so `fetch.commit_sha` takes it. Not a commit anything made.
SHA = "b" * 40
REPO = "author/directions"
REMOTE_PATH = "vectors/probe.safetensors"

SYNTHETIC = ("SYNTHETIC FIXTURE. An integer ramp, normalized. Not a real "
             "direction, not derived from any model, not a measurement.")


def synthetic_blob(tmp: Path, dim: int = 8) -> bytes:
    """A safetensors file whose header says it is a fixture. Bytes, not numbers."""
    ramp = np.arange(dim, dtype=np.float32) + 1.0
    path = tmp / "probe.safetensors"
    save_file({"direction": ramp / np.linalg.norm(ramp)}, str(path),
              metadata={"synthetic": "true", "note": SYNTHETIC})
    artifact.sort_header(path)
    return path.read_bytes()


# --------------------------------------------------------------------------- #
# The server, in process, over a real socket.


@pytest.fixture
def blob(tmp_path) -> bytes:
    return synthetic_blob(tmp_path)


@pytest.fixture
def hub(blob):
    """A stand-in host serving one file at one commit, under two layouts.

    The Hub's, which is where a row recording no host of its own resolves, and
    a second one shaped like GitHub's media host: the commit in a different
    position and no mention of the host the repo is on. Two, because a server
    that only knew one could not tell a form that passes the row's template
    through from one that ignores it.
    """

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            served = (f"/{REPO}/resolve/{SHA}/{REMOTE_PATH}",
                      f"/media/{REPO}/{SHA}/{REMOTE_PATH}")
            if self.path in served:
                self.send_response(200)
                self.send_header("Content-Length", str(len(blob)))
                self.end_headers()
                self.wfile.write(blob)
                return
            self.send_error(404)

        def log_message(self, *a):
            pass

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


@pytest.fixture
def tool(tmp_path, monkeypatch, hub):
    """A running intake, an empty schema, and a tree of its own to not write to.

    `intake.ROOT` is repointed so `artifact.local_path` resolves an
    `artifact_path` against the temp tree, and so the assertion that no artifact
    bytes were left behind has somewhere finite to look.
    """
    from controlbun import fetch

    tree = tmp_path / "tree"
    tree.mkdir()
    monkeypatch.setattr(intake, "ROOT", tree)
    monkeypatch.setattr(intake, "RECORD", tmp_path / "intake.jsonl")
    monkeypatch.setattr(fetch, "HUB", hub)
    monkeypatch.setattr(fetch, "CACHE", tmp_path / "cache")

    database = str(tmp_path / "registry.db")
    conn = db.connect(database)
    db.migrate(conn)
    conn.close()

    state = intake.Intake(database, "sohampadia/pro-human")
    handler = type("Bound", (intake.Handler,), {"intake": state})
    httpd = ThreadingHTTPServer((intake.HOST, 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    class Client:
        def __init__(self):
            self.base = f"http://{intake.HOST}:{httpd.server_address[1]}"
            self.token = state.token
            self.tree = tree
            self.database = database
            self.record = tmp_path / "intake.jsonl"
            self.staged = state.staged

        def call(self, route, *, body=None, kind=None, token=None,
                 host=None, origin=None) -> tuple[int, dict]:
            url = f"{self.base}{route}"
            url += ("&" if "?" in route else "?") + "k=" + (
                self.token if token is None else token)
            request = urllib.request.Request(
                url, data=body, method="POST" if body is not None else "GET")
            if kind:
                request.add_header("Content-Type", kind)
            if host:
                request.add_header("Host", host)
            if origin:
                request.add_header("Origin", origin)
            try:
                with urllib.request.urlopen(request) as reply:
                    return reply.status, reply.read()
            except urllib.error.HTTPError as refused:
                return refused.code, refused.read()

        def post_json(self, route, payload, **kw):
            code, raw = self.call(route, body=json.dumps(payload).encode(),
                                  kind="application/json", **kw)
            return code, json.loads(raw)

        def rows(self) -> list[sqlite3.Row]:
            conn = db.connect(self.database)
            conn.row_factory = sqlite3.Row
            try:
                return conn.execute("SELECT * FROM intervention").fetchall()
            finally:
                conn.close()

    yield Client()
    httpd.shutdown()
    httpd.server_close()
    state.close()


SUBMISSION = {
    "author": "probe", "label": "kindness", "version": "v1",
    "definition": "A synthetic probe submission written by the test suite.",
    "created_at": "2026-09-18T00:00:00Z",
    "intervention_id": "iv_probe_v1", "kind": "direction",
    "model_id": "placeholder/does-not-resolve-1b", "model_revision": "",
    "layer": "3", "layer_convention": "block-0indexed",
    "hook_point": "resid_post", "chat_template_hash": "",
    "activation_norm": "", "coeff_low": "", "coeff_high": "",
    "steering_position": "", "license_status": "",
    "shape": "", "dtype": "", "l2_norm": "", "sha256": "",
}


def link_fields(**over) -> dict:
    return {**SUBMISSION, "link_repo": REPO, "link_commit": SHA,
            "link_path": REMOTE_PATH, **over}


def leftovers() -> set[Path]:
    return set(Path(tempfile.gettempdir()).glob("registry-intake-*"))


# --------------------------------------------------------------------------- #
# Both modes end at the same place.


def test_link_mode_records_the_pointer_and_keeps_no_bytes(tool):
    """The end state is a row and nothing else: no file, no served copy."""
    before = leftovers()
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    assert code == 200, checked
    shown = dict(checked["display"])
    assert shown["sha256"] and shown["shape"] == "[8]" and shown["dtype"] == "float32"

    code, written = tool.post_json("/write", {"handle": checked["handle"],
                                              "fields": link_fields()})
    assert code == 200, written

    row, = tool.rows()
    assert (row["artifact_repo"], row["artifact_commit"]) == (REPO, SHA)
    assert row["artifact_path"] == REMOTE_PATH
    assert row["artifact_sha256"] == shown["sha256"]
    assert row["served_repo"] is None and row["served_commit"] is None

    assert not list(tool.tree.rglob("*.safetensors")), (
        "link mode kept the bytes it fetched. What it records is a pointer; a "
        "copy in the tree is the distributor question arriving sideways."
    )
    from controlbun import fetch
    assert not fetch.CACHE.exists(), (
        "the fetch went through the operator's real cache. It is swapped for a "
        "throwaway so the check is a download rather than a reread, and so "
        "nothing is left behind by a mode whose whole claim is that it keeps "
        "the pointer and not the bytes."
    )
    assert leftovers() == before


def test_link_mode_takes_a_row_that_names_its_own_host(tool, hub):
    """The gap this closes: an artifact published somewhere that is not the Hub.

    The template below is shaped like GitHub's media host, which serves file
    content from a host the repo does not live on. Nothing in the form, the
    schema or `controlbun.fetch` has heard of it; the row carries it.
    """
    template = "http://{host}/media/{repo}/{commit}/{path}"
    fields = link_fields(link_host=hub.split("//", 1)[1],
                         link_url_template=template)

    code, checked = tool.post_json("/check", {"mode": "link", "fields": fields})
    assert code == 200, checked
    code, written = tool.post_json("/write", {"handle": checked["handle"],
                                              "fields": fields})
    assert code == 200, written

    row, = tool.rows()
    assert row["artifact_host"] == hub.split("//", 1)[1]
    assert row["artifact_url_template"] == template
    assert (row["artifact_repo"], row["artifact_commit"]) == (REPO, SHA)
    assert row["served_host"] is None and row["served_url_template"] is None


def test_a_link_with_no_host_records_no_host(tool):
    """Absence is a state. Nothing fills the Hub in behind the operator."""
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    assert code == 200, checked
    code, written = tool.post_json("/write", {"handle": checked["handle"],
                                              "fields": link_fields()})
    assert code == 200, written

    row, = tool.rows()
    assert row["artifact_host"] is None, (
        "a host nobody stated was written onto the row, which is a provenance "
        "claim that reads exactly like a checked fact"
    )
    assert row["artifact_url_template"] is None


def test_changing_the_template_after_the_check_is_refused(tool, hub):
    """It decides which bytes come back, so it is one of the frozen fields."""
    fields = link_fields(link_host=hub.split("//", 1)[1],
                         link_url_template="http://{host}/media/{repo}/{commit}/{path}")
    code, checked = tool.post_json("/check", {"mode": "link", "fields": fields})
    assert code == 200, checked

    code, refused = tool.post_json("/write", {
        "handle": checked["handle"],
        "fields": {**fields, "link_url_template": "http://{host}/{repo}/resolve/{commit}/{path}"},
    })
    assert code != 200
    assert "link_url_template" in json.dumps(refused)


def test_a_template_that_loses_the_commit_is_refused(tool, hub):
    """`controlbun.fetch` owns this and the form does not restate it."""
    fields = link_fields(link_host=hub.split("//", 1)[1],
                         link_url_template="http://{host}/media/{repo}/main/{path}")
    code, refused = tool.post_json("/check", {"mode": "link", "fields": fields})
    assert code != 200
    assert "not a pinned fetch" in json.dumps(refused)


def test_the_form_offers_hosts_and_templates_without_constraining_them(tool):
    """Datalists, not a `<select>`. Three layouts across two hosts, suggested."""
    page = tool.call("/")[1].decode()
    assert "<select" not in page, "a closed list arrived as a control"
    for shown in ("media.githubusercontent.com", "raw.githubusercontent.com",
                  "{host}/{repo}/resolve/{commit}/{path}"):
        assert shown in page, f"{shown} is not offered as a suggestion"
    assert 'data-field="link_host"' in page
    assert 'data-field="link_url_template"' in page


def test_bytes_mode_publishes_and_records_only_the_pin(tool, blob, monkeypatch):
    """Converted here, uploaded to the author's namespace, and gone from here."""
    before = leftovers()
    pushed: list[tuple[str, Path]] = []

    def fake_upload(files, *, repo, message, create=False):
        for rel, local in files:
            assert local.exists(), "the upload was handed a path with no file"
            assert not local.is_relative_to(tool.tree), (
                f"{local} is inside the repository. Bytes mode stages outside it "
                "so that nothing it handles can become a file this registry holds."
            )
            pushed.append((rel, Path(local)))
        return SHA, f"{repo}/commit/{SHA}"

    monkeypatch.setattr(publish, "upload", fake_upload)

    fields = {**SUBMISSION, "bytes_path": "artifacts/probe/d.safetensors",
              "bytes_repo": "someauthor/directions", "bytes_message": "probe"}
    code, raw = tool.call(
        "/check?mode=bytes&filename=probe.npz&fields="
        + urllib.parse.quote(json.dumps(fields)),
        body=blob, kind="application/octet-stream")
    checked = json.loads(raw)
    assert code == 200, checked
    shown = dict(checked["display"])
    assert shown["shape"] == "[8]" and shown["tensor"] == "direction"

    code, written = tool.post_json("/write", {"handle": checked["handle"],
                                              "fields": fields})
    assert code == 200, written

    assert [rel for rel, _ in pushed] == ["artifacts/probe/d.safetensors"]
    row, = tool.rows()
    assert (row["artifact_repo"], row["artifact_commit"]) == \
        ("someauthor/directions", SHA)
    assert row["artifact_path"] == "artifacts/probe/d.safetensors"
    assert row["served_repo"] is None

    assert not list(tool.tree.rglob("*.safetensors")), (
        "bytes mode left the artifact in the repository. It converts, checks, "
        "publishes and records the pin; holding the bytes is the one thing it "
        "is not for."
    )
    assert not pushed[0][1].exists(), "the staged file outlived the upload"
    assert leftovers() == before


def test_neither_mode_can_write_a_served_copy():
    """A source check, because this is the line the dual-use deferral sits on."""
    text = (ROOT / "artifacts" / "intake.py").read_text()
    offenders = [
        line.strip() for line in text.splitlines()
        # The column being assigned, or named in a statement that writes. Prose
        # about the columns is the rest of the mentions and is the point of them.
        if re.search(r"served_(repo|commit)\s*(=[^=]|,)", line)
        or re.search(r"(INSERT|UPDATE)[^\n]*served_", line, re.I)
    ]
    assert not offenders, (
        "intake writes served_repo, which makes this registry a distributor "
        "rather than an index and fires the first trigger in DECISIONS.md "
        f"2026-09-17:\n{offenders}"
    )


# --------------------------------------------------------------------------- #
# What it refuses, and how the refusal reads.


def test_over_the_cap_reads_as_a_cap_on_this_form(tool):
    """Invariant 7: refuse what cannot be verified, and say that.

    The refusal a reader must not get is that their file is too big for this
    registry, or that the format is not on a list. What is true is narrower: this
    form checks the whole file in memory before it writes anything, that costs
    memory, and there is another door with no limit on it.
    """
    oversized = urllib.request.Request(
        f"{tool.base}/check?mode=bytes&filename=big.safetensors&k={tool.token}",
        data=b"", method="POST")
    oversized.add_header("Content-Length", str(intake.BYTES_CAP + 1))
    try:
        with urllib.request.urlopen(oversized, timeout=5):
            pytest.fail("the cap did not bite")
    except urllib.error.HTTPError as refused:
        reason = json.loads(refused.read())["refused"]

    assert "link mode" in reason
    for word in ("not supported", "unsupported", "too large for this registry"):
        assert word not in reason.lower(), (
            f"the refusal says {word!r}, which describes the artifact. The cap "
            "is a property of this form on this machine."
        )


def test_a_branch_is_not_a_pin(tool):
    code, body = tool.post_json(
        "/check", {"mode": "link", "fields": link_fields(link_commit="main")})
    assert code == 400
    assert "commit" in body["refused"]


def test_a_pickle_is_refused_with_the_reason_ingest_gives(tool):
    """The rule lives in `controlbun.ingest` and is not restated here."""
    pickle = b"\x80\x04" + b"\x00" * 64
    code, raw = tool.call(
        "/check?mode=bytes&filename=d.pt&fields=" + urllib.parse.quote(
            json.dumps({**SUBMISSION, "bytes_path": "artifacts/p/d.safetensors"})),
        body=pickle, kind="application/octet-stream")
    assert code == 400
    assert "pickle" in json.loads(raw)["refused"]


def test_uploading_into_this_registrys_namespace_is_refused(tool, blob, monkeypatch):
    """`publish.upload` owns this and intake inherits it by calling it."""
    fields = {**SUBMISSION, "bytes_path": "artifacts/p/d.safetensors",
              "bytes_repo": "controlbun/mirror"}
    code, raw = tool.call(
        "/check?mode=bytes&filename=d.safetensors&fields="
        + urllib.parse.quote(json.dumps(fields)),
        body=blob, kind="application/octet-stream")
    handle = json.loads(raw)["handle"]

    monkeypatch.setattr(publish, "_token", lambda: "not used; the guard is first")
    code, body = tool.post_json("/write", {"handle": handle, "fields": fields})
    assert code == 400
    assert "served" in body["refused"] and "dual-use" in body["refused"]
    assert not tool.rows()


def test_editing_the_artifact_after_the_check_is_refused(tool):
    """The form stays editable, so the check has to be about what gets written."""
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    code, body = tool.post_json(
        "/write", {"handle": checked["handle"],
                   "fields": link_fields(link_path="vectors/somethingelse.safetensors")})
    assert code == 400
    assert "link_path" in body["refused"] and "Check again" in body["refused"]
    assert not tool.rows()


def test_a_missing_definition_is_refused_rather_than_invented(tool):
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    code, body = tool.post_json(
        "/write", {"handle": checked["handle"],
                   "fields": link_fields(definition="   ")})
    assert code == 400
    assert "definition" in body["refused"]
    assert not tool.rows()


def test_an_unmeasured_field_records_as_absent_and_never_as_zero(tool):
    """Invariant 6, applied to the write path rather than to a page."""
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    tool.post_json("/write", {"handle": checked["handle"],
                              "fields": link_fields()})
    row, = tool.rows()
    for column in ("model_revision", "chat_template_hash", "activation_norm",
                   "coeff_low", "coeff_high", "steering_position",
                   "license_status"):
        assert row[column] is None, (
            f"{column} was left empty on the form and stored as {row[column]!r}. "
            "An empty string and a zero both read as an answer."
        )


# --------------------------------------------------------------------------- #
# An absence is a positive statement with a reason, and the reason has to land.
#
# `agent_handoff` has captured these since it existed and the write path dropped
# them on the floor, so the first real submission recorded a NULL where its
# author had written a paragraph about where he looked. These check the whole
# run, because every hop in it was already correct on its own.


# Not a measurement of anything and says so. The reason a fixture absence gets
# is a sentence about this test suite, because `fixtures/SYNTHETIC.md` means
# invented prose as much as invented numbers.
WHY_NO_TEMPLATE = ("Written by the test suite. No chat template was applied to "
                   "this synthetic ramp because nothing generated text with it.")


def test_a_reason_for_an_absence_survives_the_row_the_record_and_the_replay(tool):
    """The whole run: the page's paste region to a rebuilt database.

    Every hop was correct before this and the reason still reached nothing,
    because `/agent-paste` handed it to a page that did not pass it on.
    """
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    assert code == 200, checked
    code, written = tool.post_json("/write", {
        "handle": checked["handle"],
        "fields": link_fields(),
        "absent": {"chat_template_hash": WHY_NO_TEMPLATE},
    })
    assert code == 200, written

    row, = tool.rows()
    assert row["chat_template_hash"] is None, "the value was invented from a reason"

    def reasons(database) -> dict[str, str]:
        conn = db.connect(database)
        try:
            return {r["field"]: r["reason"] for r in conn.execute(
                "SELECT field, reason FROM intervention_absence"
                " WHERE intervention_id = ?", (row["id"],))}
        finally:
            conn.close()

    assert reasons(tool.database) == {"chat_template_hash": WHY_NO_TEMPLATE}

    entry, = intake.read_record(tool.record)
    assert entry["absent"] == {"chat_template_hash": WHY_NO_TEMPLATE}, (
        "the reason is in the database and not in the record, so `make site` "
        "drops it on the next rebuild. That is what `published.json` taught "
        "about two columns and `intake.jsonl` about twenty."
    )

    Path(tool.database).unlink()
    conn = db.connect(tool.database)
    db.migrate(conn)
    try:
        intake.replay(conn, tool.record)
    finally:
        conn.close()
    assert reasons(tool.database) == {"chat_template_hash": WHY_NO_TEMPLATE}


def test_a_value_and_a_reason_for_the_same_field_is_refused_and_neither_wins(tool):
    """Two claims about one field, and nothing here can tell which was meant.

    Refused rather than resolved, because preferring the value deletes the
    author's sentence and preferring the sentence deletes the author's value,
    and both happen silently while the entry still reads correct to whoever
    wrote it.
    """
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    code, refused = tool.post_json("/write", {
        "handle": checked["handle"],
        "fields": link_fields(chat_template_hash="c" * 64),
        "absent": {"chat_template_hash": WHY_NO_TEMPLATE},
    })
    assert code == 400, refused
    assert "chat_template_hash" in refused["refused"]
    assert not tool.rows(), "a contradiction was half written"
    assert not intake.read_record(tool.record), (
        "the record kept a line describing a row the database refused"
    )


def test_the_refusal_is_in_insert_so_a_hand_edited_record_cannot_walk_past_it(tool):
    """`replay` is the other caller, and a rebuild is where this would slip.

    A record is a text file somebody can correct. The check lives in the one
    function both the live write and the rebuild go through, so a contradiction
    typed into it is stopped at `make site` rather than written silently.
    """
    entry = {
        "author": "probe", "label": "kindness", "version": "v1",
        "definition": "A synthetic probe submission written by the test suite.",
        "created_at": "2026-09-18T00:00:00Z",
        "absent": {"model_revision": "Nobody recorded which weights these were."},
        "intervention": {
            "id": "iv_probe_v1", "kind": "direction",
            "model_id": "placeholder/does-not-resolve-1b",
            "model_revision": "d" * 40,
            "layer": 3, "layer_convention": "block-0indexed",
            "hook_point": "resid_post", "shape": "[8]", "dtype": "float32",
            "artifact_path": REMOTE_PATH,
        },
    }
    conn = db.connect(tool.database)
    db.migrate(conn)
    try:
        with pytest.raises(intake.Refused) as refused:
            intake.insert(conn, entry)
    finally:
        conn.close()
    assert "model_revision" in str(refused.value)


def test_a_reason_can_be_about_a_field_nothing_here_has_a_list_of(tool):
    """The field side is an open string, which is the whole design.

    A column per field would be the closed enumeration wearing a schema hat:
    the set of fields allowed an explanation would be whatever somebody thought
    of first, and the next person with an absence worth explaining would have
    to ask. So a name this repository has never seen stores and comes back.
    """
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    made_up = "tokenizer_build_id"
    code, written = tool.post_json("/write", {
        "handle": checked["handle"],
        "fields": link_fields(),
        "absent": {made_up: "Written by the test suite about a field nobody "
                            "has declared anywhere."},
    })
    assert code == 200, written
    conn = db.connect(tool.database)
    try:
        stored = [r["field"] for r in conn.execute(
            "SELECT field FROM intervention_absence")]
    finally:
        conn.close()
    assert stored == [made_up]


def test_an_absence_with_no_reason_is_the_ordinary_case_and_writes_nothing(tool):
    """Most absences have none and never will. That is not a lesser record.

    A missing reason is not a finding anywhere in this project, so the row goes
    in unchanged and the association table stays empty rather than gaining a
    line saying nobody explained anything.
    """
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    code, written = tool.post_json("/write", {
        "handle": checked["handle"],
        "fields": link_fields(),
        # A blank one is dropped, not stored: an empty reason reads on a page
        # exactly like a reason nobody gave, and only one of them is honest.
        "absent": {"chat_template_hash": "   "},
    })
    assert code == 200, written
    row, = tool.rows()
    assert row["chat_template_hash"] is None
    conn = db.connect(tool.database)
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM intervention_absence").fetchone()[0] == 0
    finally:
        conn.close()
    assert intake.read_record(tool.record)[0]["absent"] == {}


def test_a_record_written_before_008_replays_untouched(tool):
    """Every line in `artifacts/intake.jsonl` predates this feature.

    An entry with no `absent` key at all is not an entry with a problem. It is
    what the record looked like the day before, and the rebuild has to take it
    without a backfill, which is 005's argument about `model_revision` and
    007's about the host.
    """
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    tool.post_json("/write", {"handle": checked["handle"],
                              "fields": link_fields()})
    entry, = intake.read_record(tool.record)
    entry.pop("absent")
    tool.record.write_text(json.dumps(entry, sort_keys=True) + "\n")

    Path(tool.database).unlink()
    conn = db.connect(tool.database)
    db.migrate(conn)
    try:
        assert intake.replay(conn, tool.record) == [
                "probe/placeholder/does-not-resolve-1b/kindness@v1"]
    finally:
        conn.close()


def test_the_page_carries_the_reasons_to_the_write_and_builds_them_from_the_paste(tool):
    """The seam that was missing: the paste region had them and dropped them.

    Read off the page rather than asserted about the server, because the server
    was already right. What was wrong is the eighteen lines of script between
    `/agent-paste` answering and `/write` being posted.
    """
    code, body = tool.call("/")
    page = body.decode()
    assert "res.body.absent" in page, (
        "the page never reads the absences `/agent-paste` returns, which is "
        "the hop where the author's account of an absence was lost"
    )
    assert "absent: absences()" in page, (
        "the page reads them and does not post them, which is the same bug one "
        "line further on"
    )
    assert "data-absent" in page and "[data-absent]" in page, (
        "the reasons are not read back off the page the way `fields` is, so "
        "there are two ways of getting a value out of this form"
    )
    assert "<select" not in page.lower()


# --------------------------------------------------------------------------- #
# Reachable from here and from nowhere else.


def test_a_request_with_no_run_token_is_refused(tool):
    code, _ = tool.call("/", token="")
    assert code == 403
    code, _ = tool.post_json("/check", {"mode": "link", "fields": link_fields()},
                             token="wrong")
    assert code == 403


def test_a_rebound_hostname_is_refused(tool):
    """The bind alone does not stop a name that resolves to 127.0.0.1."""
    code, _ = tool.call("/", host="intake.attacker.example")
    assert code == 403


def test_a_cross_origin_post_is_refused(tool):
    code, body = tool.post_json("/check", {"mode": "link", "fields": link_fields()},
                                origin="https://elsewhere.example")
    assert code == 403
    assert not tool.rows()


def test_it_binds_loopback_and_offers_no_way_to_change_that(tool):
    source = (ROOT / "artifacts" / "intake.py").read_text()
    assert intake.HOST == "127.0.0.1"
    assert "0.0.0.0" not in source, (
        "a bind address other than loopback appears in the tool. The localhost "
        "binding is the whole difference between an operator tool and the "
        "submission route the dual-use policy is waiting on."
    )
    # The prose is allowed to name the flag that does not exist; the parser is
    # not allowed to define it. An option gets used.
    options = re.findall(r'add_argument\(\s*"(--[\w-]+)"', source)
    assert not ({"--host", "--bind", "--interface", "--address"} & set(options)), (
        f"the binding is an option: {options}"
    )
    assert re.search(r'ThreadingHTTPServer\(\(HOST,', source), (
        "the listener no longer takes its address from the one constant"
    )
    assert tool.base.startswith("http://127.0.0.1:")


def test_the_run_token_is_never_logged(tool, capsys):
    tool.call("/")
    logged = capsys.readouterr()
    assert tool.token not in logged.err + logged.out, (
        "the token is in the URL, so logging a request line puts it in the "
        "terminal scrollback"
    )


# --------------------------------------------------------------------------- #
# Open fields, and a page that invents nothing.


def test_no_field_offers_a_closed_set(tool):
    conn = db.connect(tool.database)
    try:
        html = intake.page(conn, token="t", repo="a/b", origin="o").decode()
    finally:
        conn.close()
    assert "<select" not in html, (
        "a dropdown of permitted values is the closed-enum failure arriving "
        "through a control. Suggest with a datalist behind a free-text field, "
        "which is what astro/src/data/observed-labels.ts already argues for."
    )
    for name in ("kind", "hook_point", "label", "layer_convention",
                 "license_status"):
        field = re.search(rf'<input data-field="{name}"[^>]*>', html)
        assert field, f"{name} is not on the form"
        assert "readonly" not in field.group(0) and "disabled" not in field.group(0)


def test_the_page_prefills_no_number_it_did_not_derive(tool):
    """Never fabricate numbers, applied to the HTML.

    The tensor facts are the fields somebody would be tempted to seed with a
    plausible shape or a unit norm, and a prefilled one is a claim the operator
    did not make.
    """
    conn = db.connect(tool.database)
    try:
        html = intake.page(conn, token="t", repo="a/b", origin="o").decode()
    finally:
        conn.close()
    for name in ("shape", "dtype", "l2_norm", "sha256", "layer",
                 "activation_norm", "coeff_low", "coeff_high"):
        field = re.search(rf'<input data-field="{name}"[^>]*>', html)
        assert 'value=""' in field.group(0), (
            f"{name} arrives prefilled, which puts a number in front of the "
            "operator that nothing derived"
        )


def test_the_page_is_balanced_markup_with_no_id_used_twice(tool):
    """The page is a string built by concatenation, which is how a tag goes missing.

    A stray `</div>` moves the readout inside the form and an id reused puts two
    explanations behind one field, and both render as something slightly wrong
    rather than as an error.
    """
    conn = db.connect(tool.database)
    try:
        page = intake.page(conn, token="t", repo="a/b", origin="o").decode()
    finally:
        conn.close()

    void = {"input", "br", "hr", "meta", "link", "img", "source", "option"}

    class Balance(HTMLParser):
        def __init__(self):
            super().__init__()
            self.open: list[str] = []
            self.wrong: list[str] = []

        def handle_starttag(self, tag, attrs):
            if tag not in void:
                self.open.append(tag)

        def handle_endtag(self, tag):
            if tag in void:
                return
            if not self.open or self.open[-1] != tag:
                self.wrong.append(f"</{tag}> closes {self.open[-1:] or ['nothing']}")
            else:
                self.open.pop()

    read = Balance()
    read.feed(page)
    assert not read.wrong and not read.open, (read.wrong, read.open)

    ids = re.findall(r'id="([^"]+)"', page)
    assert len(ids) == len(set(ids)), \
        [i for i in ids if ids.count(i) > 1]


def test_the_page_script_parses(tool):
    """The script is a Python string, so nothing else checks it is JavaScript."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    script = Path(tempfile.mkdtemp(prefix="registry-page-script-")) / "page.mjs"
    script.write_text(intake.SCRIPT)
    done = subprocess.run([node, "--check", str(script)], capture_output=True,
                          text=True)
    shutil.rmtree(script.parent, ignore_errors=True)
    assert done.returncode == 0, done.stderr


def test_every_field_explains_itself_somewhere_a_keyboard_can_reach(tool):
    """A `title` attribute is a tooltip a keyboard and a screen reader never get.

    So the explanation is an element the control points at with
    `aria-describedby`: read out on focus, opened by `:focus-within` for a
    pointer-less reader, and hidden behind nothing that only a mouse can do.
    """
    conn = db.connect(tool.database)
    try:
        page = intake.page(conn, token="t", repo="a/b", origin="o").decode()
    finally:
        conn.close()

    described = dict(re.findall(r'id="(why-[^"]+)">(.*?)</div>', page, re.S))
    controls = re.findall(r'<(?:input|textarea) data-field="(\w+)"[^>]*>', page)
    assert controls, "no fields on the page at all"
    for name in controls + ["file"]:
        tag = re.search(rf'<(?:input|textarea)[^>]*\bid="(?:f-)?{name}"[^>]*>', page)
        assert tag, f"{name} is not on the form"
        assert "title=" not in tag.group(0), (
            f"{name} explains itself with a title attribute, which is hover-only"
        )
        assert f'aria-describedby="why-{name}"' in tag.group(0), (
            f"{name} points at no explanation"
        )
        assert len(described.get(f"why-{name}", "").strip()) > 20, (
            f"why-{name} is missing or empty"
        )


def test_the_prompt_handoff_seams_are_on_the_page(tool):
    """Two ids another module wires up, so this page holds the shape for them.

    Designed here and empty here: the prompt text and the paste parsing are
    somebody else's, and until those routes exist both buttons answer a 404 with
    a sentence rather than a broken page.
    """
    conn = db.connect(tool.database)
    try:
        page = intake.page(conn, token="t", repo="a/b", origin="o").decode()
    finally:
        conn.close()
    assert 'id="agent-prompt"' in page
    region = re.search(r'<div id="agent-paste">(.*?)</div>\s*<p class="status"',
                       page, re.S)
    assert region and "<textarea" in region.group(1), (
        "the paste region has no textarea in it"
    )


def test_the_record_replays_into_a_rebuilt_database(tool):
    """`make site` drops registry.db. The record is why that is survivable."""
    code, checked = tool.post_json("/check", {"mode": "link",
                                              "fields": link_fields()})
    tool.post_json("/write", {"handle": checked["handle"],
                              "fields": link_fields()})
    assert tool.record.exists() and len(intake.read_record(tool.record)) == 1

    Path(tool.database).unlink()
    conn = db.connect(tool.database)
    db.migrate(conn)
    try:
        assert intake.replay(conn, tool.record) == [
                "probe/placeholder/does-not-resolve-1b/kindness@v1"]
    finally:
        conn.close()
    row, = tool.rows()
    assert (row["artifact_repo"], row["artifact_commit"]) == (REPO, SHA)


# --------------------------------------------------------------------------- #
# The published site, which is where this leaks if it ever leaks.


DIST = ROOT / "astro" / "dist"

# --------------------------------------------------------------------------- #
# The structural criterion, which replaced a list of names on 2026-09-20.
#
# This dict used to hold `<form`, `method=post`, `enctype`, `formaction`,
# `type=file`, `multipart/form-data`, `XMLHttpRequest` and `sendBeacon`, and it
# read every one of them as a write path arriving. That was right while the
# published site could not hold a session and became wrong the moment
# `/signed-in/` did: the page is now a client that signs a reader in at their
# own provider and, if they ask, puts one file in their own account. Every one
# of those eight patterns is in the build, and none of them is the thing the
# guard exists to stop.
#
# So the question changed from *does a request exist* to **where is it aimed**,
# which is the criterion `artifacts/SIGNIN.md` proposed before it was deleted
# and `DECISIONS.md` 2026-09-20 records. Two properties, and both bite:
#
#   1. Nothing on this site is a target that receives. The build emits files,
#      runs no route, and no element anywhere names this origin as somewhere to
#      send to. That is `test_the_site_build_emits_files_and_cannot_run_a_route`
#      below, unchanged, plus `test_nothing_on_the_site_posts_to_this_site`.
#   2. Every origin the site can send a reader's data to is named here, with the
#      page it is on and the reason. A new destination is an edit to this file,
#      which is a decision somebody made rather than a line that arrived.
#
# What is gone is the claim that a static build *structurally* cannot write.
# It can now, to somebody else's origin, with the reader's own credentials. That
# is the price, it is stated in the decision entry, and these two tests are what
# keep it from widening quietly.
#
# It widened once already, on 2026-09-20, and the widening is in `MAY_SEND_TO`
# rather than in a new clause: one of those destinations is a table this project
# owns, and the site writes a submission to it. Property 1 is untouched by that,
# because the row goes to Supabase and not here, and property 2 is the whole
# mechanism: the destination was already named, so what the edit had to say is
# what is now sent there and why that is narrower than it sounds.

# Patterns that are a write surface wherever they appear, because none of them
# has an honest use on a site with no origin that receives.
ALWAYS_REFUSED = {
    r"\b127\.0\.0\.1\b": "a loopback address, which is a local tool's and not this site's",
    r"\blocalhost:\d": "a loopback address, which is a local tool's and not this site's",
    r"\bnavigator\.sendBeacon\b": "a fire-and-forget POST, which exists to send without being noticed",
    r"\bmultipart/form-data\b": "an upload encoding, which only a submitting form needs",
}

# Every origin the built site may send a reader's data to, mapped to why.
#
# An enumeration on purpose, which is the opposite of how this repository treats
# user-supplied values and the right way round here: the values being enumerated
# are this project's own, and what is being constrained is the registry rather
# than a contributor. `DECISIONS.md` 2026-09-15 named that inversion as the one
# legitimate closed set in this design.
#
# Neither of these is this site. The reader's data goes to the reader's identity
# provider and to the reader's own account, and this project receives none of it.
MAY_SEND_TO = {
    "huggingface.co": (
        "the reader's identity provider and the host of the reader's own "
        "account. Discovery, userinfo, and, only when the reader takes the "
        "upload offer, creating one repository under their own namespace and "
        "committing one file to it."
    ),
    "supabase.co": (
        "the project that holds the Hugging Face provider configuration and "
        "performs the code exchange. It is a confidential client so this site "
        "holds no client secret; what it returns is a session that lives in "
        "one variable in one tab. **Since 2026-09-20 the site also writes "
        "there**: `POST /rest/v1/pending_submission` puts one submission in a "
        "holding table, over the submitter's own session, when they press "
        "submit. That is a write to a destination this project owns and it is "
        "the widest thing on this list, so it is spelled out rather than "
        "covered by the sentence above. Three properties make it the narrow "
        "thing it is, and each is held somewhere that fails a build: the row's "
        "identity is stamped by Postgres and refused when the payload "
        "disagrees with the verified session, which is "
        "`schema/supabase/001_pending_submission.sql` and "
        "`tests/test_pending_submission.py`; the table is not the corpus and "
        "nothing in it reaches a reader until the author pulls it into a "
        "tracked file and publishes a rebuild, which is `intake.pull`; and "
        "reading stays anonymous, because no read anywhere on this site goes "
        "through it."
    ),
}


def receiving_targets(text: str) -> list[str]:
    """Absolute URLs this text could send to, as bare hosts.

    Scheme-bearing literals only. A relative URL cannot leave the origin, and an
    origin that cannot receive is the property held separately below.
    """
    return sorted({
        m.group(1).lower()
        for m in re.finditer(r"https?://([A-Za-z0-9.-]+)", text)
    })


def built_files():
    for path in sorted(DIST.rglob("*")):
        if path.is_file() and path.suffix in {".html", ".js", ".mjs", ".css"}:
            yield path


def test_the_built_site_carries_no_surface_that_sends_unasked():
    """The patterns with no honest use here, whatever else the page does."""
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    offenders = []
    for path in built_files():
        text = path.read_text(errors="ignore")
        for pattern, what in ALWAYS_REFUSED.items():
            for m in re.finditer(pattern, text, re.I):
                offenders.append(f"{path.relative_to(DIST)}: {what} ({m.group(0)!r})")
    assert not offenders, (
        "the built site carries a write surface:\n  " + "\n  ".join(offenders)
    )


def test_nothing_on_the_site_posts_to_this_site():
    """The property that survived the reversal intact.

    The site has no origin that receives. A form whose `action` is this site, a
    `formaction`, or a request literal naming this origin would each be the
    first one, and all three are absent because there is nothing behind them to
    answer. The page that signs somebody in submits no form at all: it reads its
    fields with script and sends them nowhere.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    origin = re.search(
        r'site:\s*"([^"]+)"', (ROOT / "astro" / "astro.config.mjs").read_text()
    ).group(1)
    host = re.sub(r"^https?://", "", origin).rstrip("/")
    offenders = []
    for path in built_files():
        text = path.read_text(errors="ignore")
        for m in re.finditer(r"\b(?:form)?action\s*=\s*[\"']?([^\"'\s>]+)", text, re.I):
            offenders.append(f"{path.relative_to(DIST)}: a submit target {m.group(1)!r}")
        for m in re.finditer(rf"https?://{re.escape(host)}\S*", text):
            # The canonical link and the link-preview tags name this origin and
            # send nothing; a request literal is what this is looking for.
            if re.search(r"(fetch|method|body|action)", text[max(0, m.start() - 120):m.start()], re.I):
                offenders.append(f"{path.relative_to(DIST)}: a request aimed at this site ({m.group(0)!r})")
    assert not offenders, (
        "the built site aims a request at itself:\n  " + "\n  ".join(offenders)
        + "\n\nThere is nothing here to answer one. The build emits files and "
        "runs no route, which is the property the reversal on 2026-09-20 kept."
    )


def test_every_origin_the_site_can_send_to_is_accounted_for():
    """A new destination is an edit to `MAY_SEND_TO`, which is a decision.

    Scoped to the script, because the HTML's off-site links are anchors and
    `tests/test_pinned_page.py` already asks whether the build invented one. An
    anchor navigates away and sends this page's data nowhere; a literal in a
    bundle is somewhere a request can be aimed.

    Scoped further to `_astro/`, which is what this project's own source
    compiles to. `pagefind/` is a vendored bundle from a version pinned in the
    lockfile, and the URLs in it are documentation links in its own comments, so
    listing them here would be this project accounting for somebody else's
    prose. What still covers that directory is the clause above, which reads
    every built file and refuses a loopback address and a beacon wherever one
    appears.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    unaccounted = {}
    for path in built_files():
        if path.suffix not in {".js", ".mjs"}:
            continue
        if path.relative_to(DIST).parts[0] != "_astro":
            continue
        for host in receiving_targets(path.read_text(errors="ignore")):
            if not any(host == known or host.endswith("." + known)
                       for known in MAY_SEND_TO):
                unaccounted.setdefault(host, str(path.relative_to(DIST)))
    assert not unaccounted, (
        f"the built script can reach origins nobody accounted for: {unaccounted}. "
        "Add it to MAY_SEND_TO with the reason, or take it out. A destination "
        "that arrives without a test edit is one nobody decided on."
    )


def configured_targets(html: str) -> list[str]:
    """Hosts handed to script through a `data-` attribute, as bare hosts.

    A URL in a data attribute is a destination the build configured and the
    script reads at runtime, which is the same category as a literal in a
    bundle and not the same category as an anchor.
    """
    return sorted({
        m.group(1).lower()
        for m in re.finditer(r'data-[\w-]+="https?://([A-Za-z0-9.-]+)', html)
    })


def test_every_origin_configured_on_a_page_is_accounted_for():
    """The half the clause above could not see, and did not, for a day.

    `test_every_origin_the_site_can_send_to_is_accounted_for` reads `_astro/`
    scripts. The Supabase project URL is not in one: it is built into
    `signed-in/index.html` as `data-supabase-url` and read off the element at
    runtime, because it comes from a `.env` this repository does not carry. So
    the destination the site sends the most to was outside the enumeration
    entirely, and the enumeration was green because it was looking in the one
    place that value never appears.

    Found when the submission POST was added on 2026-09-20 and the guard did
    not move. It is the failure this repository keeps catching written out in
    full: a check that passes because it cannot see the thing it is about.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    unaccounted = {}
    for path in DIST.rglob("*.html"):
        for host in configured_targets(path.read_text(errors="ignore")):
            if not any(host == known or host.endswith("." + known)
                       for known in MAY_SEND_TO):
                unaccounted.setdefault(host, str(path.relative_to(DIST)))
    assert not unaccounted, (
        f"a page configures a destination nobody accounted for: {unaccounted}. "
        "Add it to MAY_SEND_TO with the reason, or take it out."
    )


def test_the_configured_origin_clause_actually_sees_the_project():
    """And is not green because it matches nothing.

    The clause above would pass on a build with no data attributes at all,
    which is exactly how the scoped-to-`_astro` one passed. So this asserts the
    scan finds the destination it exists for, by shape rather than by the
    project's own subdomain, which is in a file this repository does not carry.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    page = (DIST / "signed-in" / "index.html").read_text(errors="ignore")
    found = configured_targets(page)
    assert any(host.endswith("supabase.co") for host in found), (
        "the page that signs somebody in configures no Supabase project, so "
        "either this build had no .env or the attribute moved and this clause "
        "is now looking at nothing"
    )


def test_the_criterion_flags_what_it_claims_to_flag():
    """The bite. A guard that is green for the wrong reason is the failure this
    repository has hit more than once, so every clause above is shown refusing
    a plausible next edit rather than asserted to work.
    """
    for bad, pattern in (
        ('fetch("http://127.0.0.1:8931/x")', r"\b127\.0\.0\.1\b"),
        ('open("http://localhost:8931/")', r"\blocalhost:\d"),
        ("navigator.sendBeacon('/x', d)", r"\bnavigator\.sendBeacon\b"),
        ('enctype="multipart/form-data"', r"\bmultipart/form-data\b"),
    ):
        assert any(re.search(p, bad, re.I) for p in ALWAYS_REFUSED), (
            f"the guard missed {bad!r}"
        )
        assert re.search(pattern, bad, re.I), f"{pattern!r} no longer matches {bad!r}"

    # An origin nobody accounted for is caught, and the two that are named pass.
    assert receiving_targets('fetch("https://example.invalid/collect")') == \
        ["example.invalid"]
    for allowed in ("https://huggingface.co/oauth/userinfo",
                    "https://abc.supabase.co/auth/v1/token"):
        host = receiving_targets(allowed)[0]
        assert any(host == known or host.endswith("." + known)
                   for known in MAY_SEND_TO), f"{host} is not accounted for"
    assert not any(
        "example.invalid" == known or "example.invalid".endswith("." + known)
        for known in MAY_SEND_TO
    )

    # A configured destination is caught in the attribute it arrives in, and an
    # anchor to the same host is not one: an anchor navigates away and sends
    # this page's data nowhere.
    assert configured_targets('<div data-collect-url="https://example.invalid/x">') == \
        ["example.invalid"]
    assert configured_targets('<a href="https://example.invalid/x">read</a>') == []

    # And a submit target is caught wherever it is spelled.
    for bad in ('<form action="/claim">', '<button formaction="/claim">'):
        assert re.search(r"\b(?:form)?action\s*=\s*[\"']?([^\"'\s>]+)", bad, re.I), (
            f"the submit-target clause missed {bad!r}"
        )


def test_the_site_build_emits_files_and_cannot_run_a_route():
    config = (ROOT / "astro" / "astro.config.mjs").read_text()
    assert re.search(r'output:\s*"static"', config), (
        "astro.config.mjs is no longer static output. Its own comment says why: "
        "a build that emits files cannot drift into being a public surface the "
        "way a running process can."
    )
    assert "adapter" not in config, "an adapter turns the site into a server"

    pages = ROOT / "astro" / "src" / "pages"
    routes = [
        p.relative_to(ROOT) for p in pages.rglob("*")
        if p.is_file() and re.search(r"export\s+(const|async\s+function)\s+POST",
                                     p.read_text(errors="ignore"))
    ]
    assert not routes, f"an endpoint that accepts POST is in the site: {routes}"


# View-layer files that name the tool, with why each one is not an invitation.
# An enumeration on purpose and the right way round, same shape and same
# argument as `MAY_SEND_TO` above: what is constrained is this project rather
# than a contributor, and a new entry is a decision somebody made rather than a
# line that arrived.
#
# This list was empty until 2026-09-20, when the prompt `/submit/` hands to a
# coding agent started being generated by that tool. The prompt is prose the
# tool wrote about the fields it reads; a reader cannot press it, reach it or
# run it, which is the difference between a name and an offer.
NAMES_THE_TOOL = {
    "lib/handshake.mjs": "the argument for refusing a paste and filled fields "
                         "at once cites the function that refuses a value and "
                         "a reason for having none, one object along. A "
                         "citation in a comment is not a route.",
    "data/agent-prompt.json": "generated by `artifacts/intake.py prompt` out "
                              "of `agent_handoff.prompt`, and its prose "
                              "describes what reads the bytes on the author's "
                              "machine. Nothing in it is a URL or a command a "
                              "reader could run.",
    "pages/submit.astro": "says in a comment where the prompt on the page "
                          "comes from, so the next person to read it does not "
                          "conclude somebody typed it in.",
}


def test_the_site_does_not_know_the_intake_tool_exists():
    """A loopback tool named on a published page is an invitation nobody but
    the operator can accept.

    The lookbehind excludes `test_intake.py`, which is this file. Naming a
    guard that constrains the view layer is not a reference to the tool the
    guard is about, and a substring match said it was: `/signed-in/` cites the
    test that permits it, which is the citation an auditor wants and exactly
    what the unqualified version flagged.

    The named files are accounted for in `NAMES_THE_TOOL` with the reason.
    Everything else is still a finding, and the clause below this one is the
    one that catches an actual invitation regardless of what is on that list.
    """
    hits = [
        str(p.relative_to(ROOT / "astro" / "src"))
        for p in (ROOT / "astro" / "src").rglob("*")
        if p.is_file()
        and re.search(r"(?<!test_)intake", p.read_text(errors="ignore"))
    ]
    unaccounted = [where for where in hits if where not in NAMES_THE_TOOL]
    assert not unaccounted, (
        f"the view layer references the intake tool: {unaccounted}. It is a "
        "separate process on loopback, and a link to it from a published page "
        "is an invitation the page cannot honor for anybody but the operator. "
        "Add it to NAMES_THE_TOOL with the reason, or take it out."
    )


def test_no_page_offers_the_loopback_tool_to_anybody():
    """The clause the enumeration above cannot weaken, and the real property.

    Naming the tool in a comment is not the failure. The failure is a published
    page carrying somewhere to press, somewhere to point a browser, or a
    command to run, none of which anybody but the operator can use. So this
    reads every view-layer file including the ones on the list, and it looks
    for an origin, a port or an instruction rather than for a word.
    """
    offers = []
    for path in sorted((ROOT / "astro" / "src").rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(errors="ignore")
        for offer in (r"127\.0\.0\.1", r"\blocalhost\b",
                      r"intake\.py\s+serve", r"href=[\"'][^\"']*intake"):
            if re.search(offer, text):
                offers.append(f"{path.relative_to(ROOT)}: {offer}")
    assert not offers, (
        "a page offers the loopback tool to a reader who cannot reach it: "
        f"{offers}"
    )


def test_that_guard_still_catches_the_tool_it_is_about():
    """The bite for the lookbehind, because a narrowing that goes one character
    too far is how a guard goes quiet."""
    wanted = re.compile(r"(?<!test_)intake")
    for named in ("artifacts/intake.py", "intake.jsonl", "run the intake form",
                  "from intake import serve"):
        assert wanted.search(named), f"the guard stopped seeing {named!r}"
    assert not wanted.search("see tests/test_intake.py for the criterion")
    # And every file on the list is one that exists and does name it, so an
    # entry left behind after a file was renamed cannot sit there exempting
    # nothing while looking like it exempts something.
    for where in NAMES_THE_TOOL:
        path = ROOT / "astro" / "src" / where
        assert path.exists(), f"NAMES_THE_TOOL carries {where}, which is gone"
        assert wanted.search(path.read_text(errors="ignore")), (
            f"{where} no longer names the tool, so its exemption is dead "
            "weight that would silently cover the next line somebody adds"
        )


# --------------------------------------------------------------------------- #
# Naming the tensor in a file that holds several.
#
# The refusal came first and the affordance came second, which is the right way
# round: `ingest.one_array` has always refused a multi-array file, and the
# author naming one back is how a library of directions and their controls gets
# in without the form deciding which array is the artifact.


def _library() -> bytes:
    """A stand-in for a direction library: several arrays in one file.

    Integer ramps, labeled synthetic in the header for the reason
    `fixtures/SYNTHETIC.md` gives. Nothing here is a measurement and the shapes
    are small enough to read.
    """
    from safetensors.numpy import save
    return save({
        "direction": np.arange(8, dtype=np.float32),
        "contrast": np.arange(8, dtype=np.float32) * 2,
        "random_matched": np.arange(8, dtype=np.float32) * 3,
    })


def test_a_file_of_several_arrays_is_refused_and_the_refusal_names_them(tmp_path):
    from controlbun import ingest as ing
    with pytest.raises(ing.RefusedBytes) as refused:
        intake.check_bytes(_library(), "lib.safetensors", "v/d.safetensors",
                           stated={})
    said = str(refused.value)
    for name in ("direction", "contrast", "random_matched"):
        assert name in said, f"the refusal has to name {name} or it is a dead end"
    assert "not a refusal of the file" in said


def test_naming_a_tensor_that_is_not_there_is_refused_against_the_real_list():
    """No near-match fallback. Writing the wrong tensor under the right name is
    the one failure nothing downstream catches."""
    from controlbun import ingest as ing
    with pytest.raises(ing.RefusedBytes) as refused:
        intake.check_bytes(_library(), "lib.safetensors", "v/d.safetensors",
                           stated={}, tensor="dierction")
    assert "dierction" in str(refused.value)
    assert "direction" in str(refused.value)


def test_naming_the_tensor_writes_that_one_and_keeps_its_name():
    checked = intake.check_bytes(_library(), "lib.safetensors", "v/d.safetensors",
                                 stated={}, tensor="direction")
    try:
        assert checked.tensor_name == "direction"
        assert checked.facts.shape == "[8]"
        # The one that was asked for, not the one the format serialized first.
        blob = Path(checked.staged).read_bytes()
        assert artifact.tensor_names(blob) == ["direction"]
    finally:
        shutil.rmtree(checked.staging_root, ignore_errors=True)


def test_the_form_offers_the_tensor_field_and_explains_it(tool):
    conn = db.connect(tool.database)
    try:
        page = intake.page(conn, token="t", repo="a/b", origin="o").decode()
    finally:
        conn.close()
    assert 'data-field="bytes_tensor"' in page
    assert 'id="why-bytes_tensor"' in page


def test_a_refused_paste_comes_back_with_its_reason_not_as_a_missing_route(tool):
    """The three failures behind the paste button are not one failure.

    A dead server, an absent route and a refusal with a reason all rendered as
    "nothing answers /agent-paste on this run", so a paste the parser had read
    and rejected for a stated reason reported as a tool that was not running.
    The reason is the whole product of the error path.
    """
    code, body = tool.post_json("/agent-paste", {"pasted": "no block here at all"},
                                origin=tool.base)
    assert code == 400, "a paste with no block is refused"
    assert body.get("refused"), "and the refusal carries its reason"
    assert "nothing answers" not in body["refused"].lower()


def test_the_page_tells_those_three_apart(tool):
    conn = db.connect(tool.database)
    try:
        page = intake.page(conn, token="t", repo="a/b", origin="o").decode()
    finally:
        conn.close()
    # A network failure is caught rather than left to reject the handler, and
    # 404 is read off the status rather than inferred from a missing key.
    assert "gone: true" in page
    assert "res.status === 404" in page


def test_the_page_renders_parser_notes_rather_than_counting_them(tool):
    """The count was the whole message and the notes never left the server."""
    conn = db.connect(tool.database)
    try:
        page = intake.page(conn, token="t", repo="a/b", origin="o").decode()
    finally:
        conn.close()
    assert "res.body.notes" in page, "the handler has to read them"
    assert "class = 'notes'" in page or "className = 'notes'" in page
    assert ".notes {" in page, "and they need a style or they are a wall of text"


def _unsorted(tmp: Path) -> bytes:
    """A safetensors file whose header keys are not in sorted order.

    Which is what an ordinary export produces: safetensors seeds its header
    order per process. Integer ramp, labeled synthetic, no number a measurement.
    """
    from safetensors.numpy import save
    return save({"direction": np.arange(8, dtype=np.float32)},
                metadata={"z": "1", "a": "2", "note": SYNTHETIC})


def test_stating_the_input_digest_is_told_apart_from_a_real_mismatch(tmp_path):
    """The author's own digest cannot survive the header rewrite.

    `disagreements` says "one of the two moved", which is right for a pinned
    artifact on the read path and alarming nonsense here: the author stated the
    digest of the file they exported and the tool sorted the header before
    recording. Same tensor, different byte order.
    """
    import hashlib
    blob = _unsorted(tmp_path)
    with pytest.raises(intake.Refused) as refused:
        intake.check_bytes(blob, "d.safetensors", "v/d.safetensors",
                           stated={"sha256": hashlib.sha256(blob).hexdigest()})
    said = str(refused.value)
    assert "the file you handed over" in said
    assert "Clear the sha256 field" in said
    assert "one of the two moved" not in said


def test_a_digest_matching_neither_side_keeps_the_original_message(tmp_path):
    """Detected, not assumed. A digest that is nobody's is the case the
    original sentence was written for and it still gets it."""
    blob = _unsorted(tmp_path)
    with pytest.raises(artifact.MismatchedArtifact) as apart:
        intake.check_bytes(blob, "d.safetensors", "v/d.safetensors",
                           stated={"sha256": "a" * 64})
    assert "one of the two moved" in str(apart.value)


# --------------------------------------------------------------------------- #
# `take`: a submission somebody built in a browser, replayed into the corpus.
#
# The other half of the 2026-09-20 write path. `/submit/` produces the pointer
# and the contract and computes no tensor fact, so everything the row says about
# the bytes is derived here, by `controlbun.artifact`, from the file fetched at
# the pin. These tests are what make that claim executable rather than a
# paragraph in a module docstring.
#
# The helpers come from `tests/test_submit_page.py` rather than being written
# again, so the object under test is the one the page actually builds. A second
# hand-written copy of the shape in this file would pass forever after the page
# stopped producing it.

from test_submit_page import (  # noqa: E402
    a_form, paste_record, paste_text, submission,
)


@pytest.fixture
def taker(tmp_path, monkeypatch, hub):
    """An empty corpus, a tree of its own, and a host serving one file."""
    from controlbun import fetch

    tree = tmp_path / "tree"
    tree.mkdir()
    monkeypatch.setattr(intake, "ROOT", tree)
    monkeypatch.setattr(fetch, "HUB", hub)
    monkeypatch.setattr(fetch, "CACHE", tmp_path / "cache")

    database = tmp_path / "registry.db"
    conn = db.connect(str(database))
    db.migrate(conn)
    yield conn, tmp_path / "intake.jsonl"
    conn.close()


def a_submission(**over):
    form = a_form(repo=REPO, commit=SHA, path=REMOTE_PATH)
    form.update(over)
    return submission(form)


def a_paste(*, pasted=None, pasted_extra="", drop=(), author_in_text="sohampadia",
            **fields):
    """The other record `/submit/` builds: one block of text, unread.

    Pinned at the file this fixture's host serves, the same way `a_submission`
    is, so both routes are tested against bytes that exist. `pasted` replaces
    the whole text, which is how a paste the parser will refuse gets in:
    nothing in the browser looks at it, so anything can arrive here.
    """
    fields.setdefault("artifact_repo", REPO)
    fields.setdefault("artifact_commit", SHA)
    fields.setdefault("artifact_path", REMOTE_PATH)
    text = pasted if pasted is not None else paste_text(
        author=author_in_text, extra=pasted_extra, drop=drop, **fields,
    )
    return paste_record(text)


def test_take_derives_every_tensor_fact_from_the_bytes(taker):
    """The record says nothing about the tensor and the row says everything.

    So a submitter cannot state a shape, a dtype or a digest that the file does
    not have, because there is no field for one and nothing here reads one.
    """
    conn, record = taker
    entry = intake.take(conn, a_submission(), record)

    iv = entry["intervention"]
    assert iv["shape"] == "[8]"
    assert iv["dtype"] == "float32"
    assert iv["l2_norm"] is not None
    assert iv["artifact_sha256"] == hashlib.sha256(
        synthetic_blob(record.parent)).hexdigest()

    row, = conn.execute("SELECT * FROM intervention").fetchall()
    assert row["artifact_repo"] == REPO
    assert row["artifact_commit"] == SHA
    assert row["artifact_path"] == REMOTE_PATH


def test_take_writes_the_row_and_the_record_together(taker):
    conn, record = taker
    intake.take(conn, a_submission(), record)
    assert conn.execute("SELECT COUNT(*) c FROM submission").fetchone()["c"] == 1
    lines = [json.loads(line) for line in record.read_text().splitlines()]
    assert len(lines) == 1
    # And the record replays into a database that was dropped and rebuilt.
    conn.execute("DELETE FROM intervention")
    conn.execute("DELETE FROM submission")
    conn.commit()
    assert intake.replay(conn, record) == [
        "sohampadia/allenai/Olmo-3-1125-32B/pro-human@meandiff"
    ]


def test_the_namespace_on_the_row_is_the_handle_and_not_a_field(taker):
    """`DECISIONS.md` 2026-09-19. The page builds `author` from the capture and
    this carries it through; an `author` typed into the form reaches neither."""
    conn, record = taker
    entry = intake.take(conn, a_submission(author="meta"), record)
    assert entry["author"] == "sohampadia"


def test_a_shape_with_no_reader_is_refused_and_says_so(taker):
    conn, record = taker
    with pytest.raises(intake.Refused) as refused:
        intake.take(conn, {"shape": "controlbun.registry/link-submission@99"},
                    record)
    said = str(refused.value)
    assert "no reader for it here" in said
    assert "rather than a statement that the shape is illegitimate" in said
    # Both readable shapes are named, so whoever holds the unreadable one can
    # see what this version does read rather than being told only that theirs
    # is not it.
    assert intake.LINK_SUBMISSION in said and intake.AGENT_PASTE in said
    assert not record.exists()


def test_every_shape_this_version_reads_says_why_it_exists(taker):
    """The enumeration, held to being an enumeration somebody wrote reasons in.

    Two shapes rather than one since the agent handoff landed, and the point of
    the list is that a third is an edit here as well as there.
    """
    assert set(intake.SHAPES) == {intake.LINK_SUBMISSION, intake.AGENT_PASTE}
    for shape, why in intake.SHAPES.items():
        assert len(why.split()) > 8, f"{shape} is on the list with no reason"


# --------------------------------------------------------------------------- #
# The paste, which is the other shape and the same path through.


def test_a_paste_is_parsed_here_and_lands_as_the_same_row(taker):
    """The whole of the agent handoff, end to end, in one function.

    What the browser sent is text. Every field on the row came out of
    `agent_handoff.parse` on this machine, and every tensor fact came off the
    bytes at the pin, exactly as it does when somebody types the fields in.
    """
    conn, record = taker
    notes = []
    entry = intake.take(conn, a_paste(), record, notes=notes)

    assert entry["label"] == "pro-human"
    assert entry["version"] == "meandiff"
    assert entry["intervention"]["layer"] == 31
    assert entry["intervention"]["artifact_repo"] == REPO
    assert entry["intervention"]["artifact_commit"] == SHA
    # Derived here, from the file, and not from anything in the text.
    assert entry["intervention"]["shape"] == "[8]"
    assert entry["intervention"]["dtype"] == "float32"
    assert entry["intervention"]["artifact_sha256"] == hashlib.sha256(
        synthetic_blob(record.parent)).hexdigest()

    lines = [json.loads(line) for line in record.read_text().splitlines()]
    assert len(lines) == 1


def test_a_paste_and_filled_fields_together_is_refused_and_neither_wins(taker):
    """The rule `insert` applies to one field, applied to a whole submission.

    Two accounts of one submission, and nothing here can tell which was meant.
    Preferring either drops one of somebody's statements while the record still
    reads correct to whoever wrote it.
    """
    conn, record = taker
    given = a_paste()
    given["label"] = "typed-as-well"
    given["intervention"] = {"kind": "direction"}
    with pytest.raises(intake.Refused) as refused:
        intake.take(conn, given, record)
    said = str(refused.value)
    assert "a paste and" in said and "label" in said and "intervention" in said
    assert "nothing here can tell which was meant" in said
    assert conn.execute("SELECT COUNT(*) c FROM submission").fetchone()["c"] == 0
    assert not record.exists()


def test_a_paste_the_parser_refuses_comes_back_as_the_parser_s_own_sentence(taker):
    """No second sentence wrapped around the first.

    The reader is somebody holding a reply from their coding agent, and what
    `parse` produces names the field and says what to do about it. A message
    from here saying the paste could not be read would be strictly less.
    """
    conn, record = taker
    bad = a_paste(pasted="here is what I found, but no block")
    with pytest.raises(agent_handoff.Refused) as refused:
        intake.take(conn, bad, record)
    assert "there is no submission block in what was pasted" in str(refused.value)
    assert not record.exists()

    missing = a_paste(drop=("layer", "hook_point"))
    with pytest.raises(agent_handoff.Refused) as refused:
        intake.take(conn, missing, record)
    assert "the schema cannot write a row without layer, hook_point" in str(
        refused.value)


def test_the_stamped_author_outranks_the_one_in_the_paste(taker):
    """An agent writes down the namespace it read in its author's files. The
    row's handle came through the insert policy out of a verified session. The
    stamped one is what the row records and the difference is said out loud,
    which is what `stamped` does for the same reason one object along."""
    conn, record = taker
    notes = []
    entry = intake.take(conn, a_paste(author_in_text="someone-else"), record,
                        notes=notes)
    assert entry["author"] == "sohampadia"
    assert any("someone-else" in note and "sohampadia" in note for note in notes), (
        f"the disagreement was resolved silently: {notes}"
    )


def test_what_the_parser_decided_rather_than_read_comes_back_with_the_row(taker):
    """A paste that parses is not the same as a paste that was understood.

    These are the only evidence of the difference, so they travel even when
    nothing was refused, and they are shown in full rather than counted.
    """
    conn, record = taker
    notes = []
    intake.take(conn, a_paste(pasted_extra="beard_length: 4"), record, notes=notes)
    assert any("beard_length" in note for note in notes), notes


def test_a_paste_with_no_pin_is_refused_with_what_to_do_about_it(taker):
    """The prompt lets an agent declare the repo and the commit absent, because
    the loopback form publishes the bytes itself when they are nowhere yet.
    Nothing here can: this site receives no bytes. So the refusal says that and
    says where the upload offer is, rather than reporting that the empty string
    is not a commit."""
    conn, record = taker
    with pytest.raises(intake.Refused) as refused:
        intake.take(conn, a_paste(drop=("artifact_repo", "artifact_commit")),
                    record)
    said = str(refused.value)
    assert "no published repo and commit" in said
    assert "/submit/" in said
    assert not record.exists()


def test_a_paste_carrying_no_text_at_all_is_refused_rather_than_parsed(taker):
    conn, record = taker
    with pytest.raises(intake.Refused) as refused:
        intake.take(conn, {"shape": intake.AGENT_PASTE, "author": "sohampadia"},
                    record)
    assert "no `pasted` text" in str(refused.value)


def test_a_record_carrying_anything_that_reads_like_a_credential_stops(taker):
    """Belt and braces: the projection copies named fields and could not carry
    a stray key anyway. This refuses before that, because the failure being
    guarded against is a secret in a public repository and the cheap check is
    the one that runs first."""
    conn, record = taker
    for key in ("provider_token", "apiKey", "Authorization", "code_verifier"):
        given = a_submission()
        given["intervention"][key] = "should never travel"
        with pytest.raises(intake.Refused) as refused:
            intake.take(conn, given, record)
        assert key in str(refused.value)
        assert "Nothing was written." in str(refused.value)
    assert not record.exists()


def test_bytes_nobody_can_fetch_refuse_here_rather_than_becoming_a_row(taker):
    """A submission whose pin does not resolve is refused with the reason, and
    the reason is a fact about the artifact rather than a credential to go find.
    `DECISIONS.md` 2026-09-20 names the failure this stops: a registry whose
    pages mostly point at things nobody can fetch is a bibliography."""
    conn, record = taker
    with pytest.raises(Exception) as refused:
        intake.take(conn, a_submission(commit="c" * 40), record)
    assert "has no" in str(refused.value)
    assert "does not fall back to another revision" in str(refused.value)
    assert conn.execute("SELECT COUNT(*) c FROM submission").fetchone()["c"] == 0
    assert not record.exists()


def test_take_refuses_a_value_and_a_reason_for_having_none(taker):
    """The contradiction `insert` refuses, reached through this path too,
    because both the live write and the replay come through one function."""
    conn, record = taker
    given = a_submission(
        model_revision="abc123",
        absent={"model_revision": "the manifest records no revision anywhere"},
    )
    with pytest.raises(intake.Refused) as refused:
        intake.take(conn, given, record)
    assert "two claims about one field" in str(refused.value)


# --------------------------------------------------------------------------- #
# `pull`: every submission the site received, into the record the build replays.
#
# The site posts to `pending_submission` now, and this is the other end of that.
# What it must not become is a queue: nothing here approves, rejects, ranks,
# counts or orders anything, and `taken_at` means read in rather than accepted.
#
# **Nothing here touches the network.** `pending` and `mark_taken` are the two
# functions that do, and they are one `urllib` call each; `pull` takes the rows
# it is given and a callback to mark them, so the part with the rule in it runs
# against a list of dicts. That split is the reason the rule is testable at all.
# Whether the project answers is not this gate's question, and a gate that
# depended on it would go red for reasons that have nothing to do with this
# repository.


def a_row(record=None, *, subject="opaque", handle="sohampadia", **over):
    """One `pending_submission` row, shaped the way PostgREST returns one.

    `subject` and `handle` are the stamped columns. Postgres wrote them from
    the verified session and refused the insert if they disagreed with it, so
    in this fixture they are the ground the record is read against.
    """
    row = {
        "id": "00000000-0000-0000-0000-000000000001",
        "received_at": "2026-09-20T12:00:00Z",
        "account": "11111111-2222-3333-4444-555555555555",
        "subject": subject,
        "handle": handle,
        "record": a_submission() if record is None else record,
        "taken_at": None,
    }
    row.update(over)
    return row


def test_pull_writes_through_the_same_function_a_mailed_file_goes_through(taker):
    """One function writes a submission and there is not a second one.

    `take` is what `intake.py take` calls on a file somebody handed over and it
    is what this calls on a row the site received. So the record and the
    database cannot come apart, which is the shape `artifacts/claim.py` and
    `artifacts/publish.py` already use and the reason this is not its own
    module.
    """
    conn, record = taker
    marked = []
    results = intake.pull(conn, [a_row()], path=record,
                          mark=lambda row_id, at: marked.append((row_id, at)),
                          at="2026-09-20T13:00:00Z")

    assert len(results) == 1
    assert results[0]["ref"] == "sohampadia/allenai/Olmo-3-1125-32B/pro-human@meandiff"
    assert conn.execute("SELECT COUNT(*) c FROM submission").fetchone()["c"] == 1
    assert len(record.read_text().splitlines()) == 1
    assert marked == [("00000000-0000-0000-0000-000000000001", "2026-09-20T13:00:00Z")]

    # And the tracked record replays into a database that was dropped, which is
    # what `make site` does on every build.
    conn.execute("DELETE FROM intervention")
    conn.execute("DELETE FROM submission")
    conn.commit()
    assert intake.replay(conn, record) == [
        "sohampadia/allenai/Olmo-3-1125-32B/pro-human@meandiff"
    ]


def test_the_stamped_identity_wins_over_the_record_s_own():
    """The property the table exists for, at the point the author reads it.

    A capture that arrives as a file is a stranger's JSON and nothing
    downstream can tell an edited one from a real one. The columns came through
    an insert policy that refused the row unless they matched the verified
    session, so where the two disagree the columns are the answer.
    """
    claimed = a_submission()
    claimed["author"] = "somebody-else"
    claimed["subject"] = "somebody-elses-subject"
    out, differs = intake.stamped(a_row(claimed))

    assert out["author"] == "sohampadia"
    assert out["subject"] == "opaque"
    assert len(differs) == 2
    assert any("somebody-else" in line and "sohampadia" in line for line in differs)
    assert any("somebody-elses-subject" in line and "opaque" in line
               for line in differs)


def test_agreement_is_silent_and_disagreement_is_not_a_refusal():
    """It is a fact about two reads of one account at two moments, not a
    finding against anybody. A handle renamed between the capture and the
    session would produce it, and that is a real thing that happens to real
    people rather than an attack."""
    out, differs = intake.stamped(a_row())
    assert differs == []
    assert out["author"] == "sohampadia"

    renamed = a_submission()
    renamed["author"] = "old-name"
    out, differs = intake.stamped(a_row(renamed))
    assert out["author"] == "sohampadia"
    assert len(differs) == 1
    # Surfaced and not raised. Nothing about it stops the row.
    assert "stamped" not in out


def test_a_row_the_insert_policy_could_not_have_written_is_refused():
    """`subject` and `handle` are `not null` and the policy binds both. A row
    with neither did not come through it, so something other than the site put
    it there and it is not going into a tracked file."""
    for missing in ({"subject": ""}, {"handle": ""}):
        with pytest.raises(intake.Refused) as refused:
            intake.stamped(a_row(**missing))
        assert "did not come through the insert policy" in str(refused.value)


def test_a_refused_row_stays_unread_and_does_not_stop_the_others(taker):
    """A pin nobody can fetch is one submitter's problem and the rows behind it
    are other people's. The refused row keeps `taken_at` null, so it is there
    next time and the author can write back about it. Refusing is what the
    schema refuses and never a judgment about the work."""
    conn, record = taker
    marked = []
    bad = a_submission()
    bad["shape"] = "controlbun.registry/link-submission@99"
    results = intake.pull(
        conn,
        [a_row(bad, id="row-bad"), a_row(id="row-good")],
        path=record,
        mark=lambda row_id, at: marked.append(row_id),
    )

    assert "no reader for it" in results[0]["refused"]
    assert "refused" not in results[1]
    # Only the one that was written is marked, so the other is still pending.
    assert marked == ["row-good"]
    assert len(record.read_text().splitlines()) == 1


def test_pull_marks_nothing_it_did_not_write(taker):
    """The order matters and it is the order `take` already uses: row, then
    record line, then the mark. A run that dies between them leaves the row
    unmarked and the next pull refuses it as a duplicate rather than losing it.
    """
    conn, record = taker
    intake.pull(conn, [a_row()], path=record, mark=lambda *_: None)
    results = intake.pull(conn, [a_row(id="again")], path=record,
                          mark=lambda *_: pytest.fail("a duplicate was marked"))
    said = results[0].get("refused") or ""
    assert "already holds this submission" in said, (
        "the same submission was written twice"
    )
    # And the record did not grow a second line for it.
    assert len(record.read_text().splitlines()) == 1


def test_pull_orders_nothing_and_counts_nothing_about_a_submission():
    """`CLAUDE.md`: no ordering is ever derived from an eval result, and this is
    not a queue. `pending` asks for `received_at.asc`, which is arrival order
    and the only thing a list of rows can be in; nothing anywhere reads a
    position, a count or a score off a row."""
    source = (ROOT / "artifacts" / "intake.py").read_text()
    block = source[source.index("def pending("):source.index("def cmd_pull(")]
    assert "received_at.asc" in block
    # The prose is taken out first. Every one of these words is in the comments
    # here, saying the code does not do it, which is the trap a substring scan
    # walks into every time in this repository. The bite below shows the strip
    # still keeping a real line.
    code = _code_only(block)
    for ranking in ("sort=", "rank", "score", "priority", "approve", "reject"):
        assert ranking not in code.lower(), (
            f"the pull reads {ranking!r} off a pending row, which makes it a queue"
        )


def _code_only(source: str) -> str:
    """Python with its docstrings and comments removed."""
    out = re.sub(r'"""(?:.|\n)*?"""', "", source)
    return "\n".join(line.split("#")[0] for line in out.splitlines())


def test_the_prose_strip_does_not_hide_a_real_line():
    """The bite. A filter that got too wide is how a guard goes green for the
    wrong reason, which is the failure this repository has hit more than once."""
    sample = (
        'def f():\n'
        '    """Nothing here sorts or ranks anything."""\n'
        '    # and nothing scores it either\n'
        '    rows.sort(key=lambda r: r["score"])\n'
    )
    stripped = _code_only(sample)
    assert 'rows.sort(key=lambda r: r["score"])' in stripped
    assert "Nothing here sorts" not in stripped
    assert "nothing scores it either" not in stripped


def test_the_pull_refuses_without_the_secret_key_and_names_it():
    """And does not fall back to `.env`, which is where it is deliberately not."""
    with pytest.raises(intake.Refused) as refused:
        intake.credentials({"SUPABASE_URL": "https://x.supabase.co"},
                           {"SUPABASE_SECRET_KEY": "would-be-wrong"})
    said = str(refused.value)
    assert "SUPABASE_SECRET_KEY is not set" in said
    assert "would-be-wrong" not in said, "the refusal echoed a key back"

    with pytest.raises(intake.Refused) as refused:
        intake.credentials({"SUPABASE_SECRET_KEY": "sb_secret_x"}, {})
    assert "no SUPABASE_URL" in str(refused.value)
    assert "sb_secret_x" not in str(refused.value)


def test_the_project_url_comes_from_the_same_place_the_build_reads_it():
    """One copy of it. A second would be a second place for it to disagree,
    and the site build already reads `.env` at the repository root."""
    url, secret = intake.credentials(
        {"SUPABASE_SECRET_KEY": "sb_secret_x"},
        {"SUPABASE_URL": "https://x.supabase.co/"},
    )
    assert url == "https://x.supabase.co"
    assert secret == "sb_secret_x"
    # And the environment wins, so a one-off run against another project does
    # not mean editing a file.
    url, _ = intake.credentials(
        {"SUPABASE_SECRET_KEY": "sb_secret_x", "SUPABASE_URL": "https://y.supabase.co"},
        {"SUPABASE_URL": "https://x.supabase.co"},
    )
    assert url == "https://y.supabase.co"
