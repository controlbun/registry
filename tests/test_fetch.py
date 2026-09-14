"""Resolving an artifact to bytes, and refusing the wrong ones.

Most of this runs against a local HTTP server rather than the Hub, so `make verify`
stays offline and rerunnable from a clean checkout. One test does hit the real Hub
and skips when there is no network, because the thing it checks cannot be faked:
that a real LFS object, which is what every artifact will be, redirects to a CDN
and still arrives byte-identical.
"""

from __future__ import annotations

import hashlib
import http.server
import socket
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import load as load_bytes
from safetensors.numpy import save

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from registry import fetch  # noqa: E402

SHA = "c1e0da3fb595874da299e783c7ad9c08a95ce7e9"
BLOB = save({"t": np.arange(8, dtype=np.float32)})


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """A cache per test.

    The real cache is keyed by commit and never expires, which is correct in
    production and would make these tests pass on yesterday's bytes.
    """
    monkeypatch.setattr(fetch, "CACHE", tmp_path / "cache")


@pytest.fixture
def server(monkeypatch):
    """A stand-in Hub. Serves one object at one commit and 404s everything else."""
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            want = f"/org/repo/resolve/{SHA}/t.safetensors"
            if self.path == want:
                self.send_response(200)
                self.send_header("Content-Length", str(len(BLOB)))
                self.end_headers()
                self.wfile.write(BLOB)
            elif self.path.endswith("/redirected.safetensors"):
                # LFS objects redirect to a CDN. The real fetch has to follow it.
                self.send_response(302)
                self.send_header("Location", want)
                self.end_headers()
            else:
                self.send_error(404)

        def log_message(self, *a):
            pass

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    monkeypatch.setattr(fetch, "HUB", f"http://127.0.0.1:{port}")
    yield
    httpd.shutdown()


def test_a_pinned_fetch_returns_the_bytes(server):
    assert fetch.from_hub("org/repo", SHA, "t.safetensors") == BLOB


def test_a_redirect_is_followed(server):
    """Every real artifact is an LFS object and every LFS object redirects."""
    assert fetch.from_hub("org/repo", SHA, "redirected.safetensors") == BLOB


def test_a_missing_commit_says_so_rather_than_falling_back(server):
    with pytest.raises(fetch.FetchError, match="no t.safetensors|does not exist"):
        fetch.from_hub("org/repo", "b" * 40, "t.safetensors")


def test_the_second_fetch_comes_from_cache(server, tmp_path, monkeypatch):
    fetch.from_hub("org/repo", SHA, "t.safetensors")

    def explode(*a, **k):
        raise AssertionError("refetched something already cached")

    monkeypatch.setattr(urllib.request, "urlopen", explode)
    assert fetch.from_hub("org/repo", SHA, "t.safetensors") == BLOB


@pytest.mark.parametrize("ref", ["main", "v1.0", "abc123", "", "HEAD", "a" * 39])
def test_only_a_commit_sha_resolves(ref):
    """A tag is movable by the repo owner, so pinning to one pins to nothing."""
    with pytest.raises(fetch.FetchError, match="not a commit SHA"):
        fetch.hub_url("org/repo", ref, "t.safetensors")


def test_the_url_is_the_shape_the_hub_serves():
    fetch_url = fetch.hub_url("org/repo", SHA, "t.safetensors")
    assert fetch_url.endswith(f"/org/repo/resolve/{SHA}/t.safetensors")


# ------------------------------------------------------------------ ordering


def test_a_served_copy_wins_over_the_authors_repo(server, monkeypatch):
    """Ours first, because its availability is the thing we control."""
    asked = []
    real = fetch.from_hub
    monkeypatch.setattr(fetch, "from_hub",
                        lambda r, c, p, **k: (asked.append(r), real(r, c, p, **k))[1])
    fetch.resolve(artifact_path="t.safetensors",
                  served_repo="org/repo", served_commit=SHA,
                  artifact_repo="someone/else", artifact_commit="d" * 40)
    assert asked == ["org/repo"]


def test_a_local_path_is_used_when_no_repo_is_recorded(tmp_path, monkeypatch):
    """How the fixtures work, and how anyone runs this with no network."""
    monkeypatch.setattr(fetch, "ROOT", tmp_path)
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "x.safetensors").write_bytes(BLOB)
    assert fetch.resolve(artifact_path="fixtures/x.safetensors") == BLOB


def test_nothing_recorded_anywhere_is_an_error_not_an_empty_result():
    with pytest.raises(fetch.FetchError, match="no artifact recorded"):
        fetch.resolve(artifact_path=None)


# -------------------------------------------------------------- the real Hub


def _online() -> bool:
    try:
        urllib.request.urlopen("https://huggingface.co", timeout=5)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _online(), reason="offline")
def test_the_real_hub_serves_a_real_lfs_object_byte_identical():
    """The one thing a local server cannot stand in for.

    `.safetensors` is LFS-tracked by the default gitattributes on a model repo no
    matter how small the file is, so this 96-byte object took the full LFS path on
    upload and comes back through a CDN redirect. Every real artifact will do the
    same, and this is the only test that proves our code survives it.
    """
    blob = fetch.from_hub("controlbun/fetch-test", SHA, "t.safetensors")
    assert hashlib.sha256(blob).hexdigest() == hashlib.sha256(BLOB).hexdigest()
    assert load_bytes(blob)["t"].tolist() == list(range(8))
