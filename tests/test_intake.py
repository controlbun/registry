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

# What a write surface looks like in built output. `<input>` on its own is not
# on the list: the situation picker on the front page is two of them, and
# banning the tag would ban the control that makes the open fields open.
WRITE_SURFACE = {
    r"<form\b": "a form element",
    r"method\s*[:=]\s*[\"']?\s*post\b": "a POST target",
    r"\benctype\b": "a form encoding, which only a submitting form needs",
    r"\bformaction\b": "a submit button with its own target",
    r'type\s*=\s*["\']?file\b': "a file input",
    r"\bmultipart/form-data\b": "an upload encoding",
    r"\bXMLHttpRequest\b": "a scripted request older than fetch",
    r"\bsendBeacon\b": "a fire-and-forget POST",
    r"\b127\.0\.0\.1\b": "a loopback address, which is the intake tool's",
    r"\blocalhost:\d": "a loopback address, which is the intake tool's",
}


def test_the_built_site_ships_no_form_and_no_post_target():
    """The site is `output: "static"` and has to stay a thing that cannot accept.

    v0 accepts no uploads and serves nothing publicly, and the dual-use policy
    that a submission route needs does not exist. The intake form is the first
    code in this repository that takes a file and writes a row, so this is the
    check that it never arrives on the published site by being copied, imported
    or reimplemented there.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    offenders = []
    for path in sorted(DIST.rglob("*")):
        if not path.is_file() or path.suffix not in {".html", ".js", ".mjs", ".css"}:
            continue
        text = path.read_text(errors="ignore")
        for pattern, what in WRITE_SURFACE.items():
            for m in re.finditer(pattern, text, re.I):
                offenders.append(f"{path.relative_to(DIST)}: {what} ({m.group(0)!r})")
    assert not offenders, (
        "the built site carries a write surface:\n  " + "\n  ".join(offenders)
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


def test_the_site_does_not_know_the_intake_tool_exists():
    hits = [
        p.relative_to(ROOT) for p in (ROOT / "astro" / "src").rglob("*")
        if p.is_file() and "intake" in p.read_text(errors="ignore")
    ]
    assert not hits, (
        f"the view layer references the intake tool: {hits}. It is a separate "
        "process on loopback, and a link to it from a published page is an "
        "invitation the page cannot honor for anybody but the operator."
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
