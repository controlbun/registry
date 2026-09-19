"""The sign-in tool: what it records, what it refuses, and what it never writes.

Two things are under test and they are different sizes.

The small one is the capture shape, which is a pure function of one userinfo
response and is exercised without a browser, a project or a person. Every
identity here is synthetic except where a test says otherwise, per
`fixtures/SYNTHETIC.md`; none of the `sub` values below belongs to anybody.

The large one is the property that makes this tool shippable at all: it is a
loopback process and nothing about it reaches the published site. The guard in
`tests/test_intake.py` fails the build if `astro/dist` ever ships a form, a POST
target, a scripted request or a loopback address, and the tests at the bottom of
this file are the other half of that: they fail if the view layer ever learns
this tool exists, and they fail if this tool ever grows the surface the guard
looks for.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "artifacts"))

import signin  # noqa: E402

SYNTHETIC = "synthetic, not a real account"

# Obviously synthetic: a hex string of one repeated digit is not an identifier
# any provider would mint. The one real identity in this project is recorded in
# `V2.md` and is deliberately not used here.
FAKE_SUB = "1" * 24
FAKE_ORG_SUB = "2" * 24


def userinfo_with(**over) -> dict:
    said = {"sub": FAKE_SUB, "preferred_username": "synthetic-person",
            "orgs": [{"name": "synthetic-org", "sub": FAKE_ORG_SUB,
                      "roleInOrg": "contributor"}]}
    said.update(over)
    return said


def capture_of(said: dict, **over) -> dict:
    kw = {"provider": "custom:synthetic", "issuer": "https://example.invalid",
          "endpoint": "https://example.invalid/oauth/userinfo",
          "captured_at": "2026-09-19T00:00:00Z"}
    kw.update(over)
    return signin.capture_from(said, **kw)


# --------------------------------------------------------------------------- #
# The shape of the evidence.


def test_a_capture_carries_the_moment_it_was_taken():
    """A membership with no date is a badge. The date is the whole object."""
    entry = capture_of(userinfo_with())
    assert entry["captured_at"] == "2026-09-19T00:00:00Z"
    assert entry["shape"] == "controlbun.registry/membership-capture@1"


def test_it_binds_to_sub_and_keeps_the_handle_as_a_separate_thing():
    """Handles are renameable. Two captures across a rename are one identity."""
    before = capture_of(userinfo_with(preferred_username="old-handle"))
    after = capture_of(userinfo_with(preferred_username="new-handle"),
                       captured_at="2026-09-20T00:00:00Z")
    assert before["sub"] == after["sub"] == FAKE_SUB
    assert before["preferred_username"] != after["preferred_username"]


def test_no_sub_is_refused_rather_than_recorded_against_the_handle():
    with pytest.raises(signin.Refused) as refused:
        capture_of(userinfo_with(sub=None))
    assert "sub" in str(refused.value)


def test_orgs_has_three_states_and_they_are_three_different_facts():
    """A list, an empty list and nothing said are not the same answer.

    The middle one is membership of no organization, which is a real reading.
    The last is that the provider said nothing about organizations, which is
    the case `schema/migrations/008_absence_reason.sql` calls an absence with a
    reason rather than an omission or an error.
    """
    some = capture_of(userinfo_with())
    none = capture_of(userinfo_with(orgs=[]))
    unsaid = capture_of(userinfo_with(orgs=None))

    assert some["orgs"] and "orgs_absence" not in some
    assert none["orgs"] == [] and "orgs_absence" not in none
    assert unsaid["orgs"] is None and unsaid["orgs_absence"]


def test_an_unobserved_membership_is_not_an_error_and_not_an_empty_answer():
    unsaid = capture_of(userinfo_with(orgs=None))
    reason = unsaid["orgs_absence"].lower()
    assert "read-memberships" in reason, "the reason has to say what would fix it"
    assert "not the same as membership of none" in reason
    # Rendering it reaches the absence, not a blank list and not a failure.
    page = signin.captured(unsaid).decode()
    assert "absent" in page and "error" not in page.lower()


def test_an_org_entry_is_passed_through_exactly_as_the_provider_wrote_it():
    """Reshaping into the keys this file knows is a closed enumeration.

    The next key Hugging Face adds would be dropped on the floor by anything
    that reads `name` and `roleInOrg` and rebuilds an entry out of them.
    """
    odd = {"name": "synthetic-org", "sub": FAKE_ORG_SUB,
           "roleInOrg": "contributor",
           "somethingAddedLater": {"nested": [1, 2, 3]}}
    entry = capture_of(userinfo_with(orgs=[odd]))
    assert entry["orgs"] == [odd]
    assert json.loads(json.dumps(entry))["orgs"][0]["somethingAddedLater"]


def test_an_org_shape_this_file_does_not_recognize_still_gets_a_sentence():
    """Dropping an entry we cannot name is losing evidence silently."""
    lines = signin.confirmations(capture_of(userinfo_with(
        orgs=[{"identifier": "no-name-key"}, "a-bare-string"])))
    assert len(lines) == 2
    assert any("did not name" in line for line in lines)
    assert any("a-bare-string" in line for line in lines)


def test_a_membership_is_confirmed_on_a_date_and_never_called_verified():
    """Nothing re-reads this, so a word implying something does is the word
    that turns dated evidence into a standing."""
    entry = capture_of(userinfo_with())
    line, = signin.confirmations(entry)
    assert line == "member of synthetic-org, confirmed 2026-09-19T00:00:00Z"
    for surface in (line, signin.captured(entry).decode(),
                    signin.landing("http://example.invalid").decode()):
        assert not re.search(r"\bverif", surface, re.I), (
            "'verified' claims a freshness this tool does not have"
        )


def test_the_provider_string_is_carried_not_checked():
    """No list of provider names anywhere, including this one."""
    entry = capture_of(userinfo_with(), provider="custom:something-nobody-added")
    assert entry["provider"] == "custom:something-nobody-added"
    source = (ROOT / "artifacts" / "signin.py").read_text()
    code = "\n".join(l for l in source.splitlines() if not l.lstrip().startswith("#"))
    assert not re.search(r"(PROVIDERS|KNOWN_PROVIDERS)\s*=", code)
    assert not re.search(r"provider\s+not\s+in\s", code)


def test_the_record_round_trips_and_never_rewrites_a_line(tmp_path):
    record = tmp_path / "memberships.jsonl"
    assert signin.read_record(record) == []
    first = capture_of(userinfo_with())
    second = capture_of(userinfo_with(orgs=[]), captured_at="2026-09-20T00:00:00Z")
    signin.append_record(first, record)
    signin.append_record(second, record)
    assert signin.read_record(record) == [first, second]
    assert record.read_text().count("\n") == 2


# --------------------------------------------------------------------------- #
# PKCE, which is what puts the answer in the query string instead of a fragment.


def test_the_challenge_is_the_s256_of_the_verifier_unpadded():
    verifier, challenge = signin.pkce_pair()
    expected = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    assert challenge == expected
    assert "=" not in challenge
    # Supabase answers "code challenge has to be between 43 and 128 characters".
    assert 43 <= len(challenge) <= 128


def test_two_runs_do_not_share_a_verifier():
    assert signin.pkce_pair()[0] != signin.pkce_pair()[0]


def test_the_authorize_url_asks_for_pkce_and_names_the_loopback_return():
    url = signin.authorize_url("https://p.example.invalid",
                               provider="custom:huggingface",
                               redirect_to="http://127.0.0.1:8931/callback",
                               challenge="c" * 43)
    assert url.startswith("https://p.example.invalid/auth/v1/authorize?")
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    assert query["provider"] == ["custom:huggingface"]
    # Lowercase: Supabase validates this value and answers "Invalid
    # code_challenge_method" for anything else.
    assert query["code_challenge_method"] == ["s256"]
    assert query["redirect_to"] == ["http://127.0.0.1:8931/callback"]


def test_the_pending_verifier_is_single_use():
    state = signin.SignIn("https://p.example.invalid", "k", "custom:x", Path("/x"))
    state.start()
    state.take()
    with pytest.raises(signin.Refused):
        state.take()


# --------------------------------------------------------------------------- #
# The tool as a running process.


@pytest.fixture
def tool(tmp_path, monkeypatch):
    """The server, with the two network hops replaced and nothing else."""
    state = signin.SignIn("https://p.example.invalid", "publishable-key-stub",
                          "custom:synthetic", tmp_path / "memberships.jsonl")
    handler = type("BoundHandler", (signin.Handler,), {"signin": state})
    httpd = ThreadingHTTPServer((signin.HOST, 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    seen: dict[str, object] = {}

    def fake_exchange(url, key, *, code, verifier):
        seen["code"], seen["verifier"] = code, verifier
        return {"access_token": "stub-session-token",
                "refresh_token": "stub-refresh-token",
                "provider_token": "stub-provider-token",
                "user": {"id": FAKE_SUB}}

    def fake_discovery(url=signin.DISCOVERY):
        return {"issuer": "https://example.invalid",
                "userinfo_endpoint": "https://example.invalid/oauth/userinfo"}

    def fake_userinfo(endpoint, token):
        seen["token"] = token
        return userinfo_with()

    monkeypatch.setattr(signin, "exchange", fake_exchange)
    monkeypatch.setattr(signin, "discovery", fake_discovery)
    monkeypatch.setattr(signin, "userinfo", fake_userinfo)

    port = httpd.server_address[1]

    class Tool:
        base = f"http://{signin.HOST}:{port}"
        record = state.record
        signin = state
        calls = seen

        def get(self, path, headers=None):
            request = urllib.request.Request(self.base + path,
                                             headers=headers or {})
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    return response.status, response.read().decode()
            except urllib.error.HTTPError as error:
                return error.code, error.read().decode()

    try:
        yield Tool()
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_it_binds_loopback_and_offers_no_way_to_change_that():
    """The bind is the constraint. A `--host` would be the docstring undone."""
    assert signin.HOST == "127.0.0.1"
    source = (ROOT / "artifacts" / "signin.py").read_text()
    code = "\n".join(l for l in source.splitlines() if not l.lstrip().startswith("#"))
    assert "--host" not in code
    assert "0.0.0.0" not in code
    assert re.findall(r"^HOST\s*=.*$", code, re.M) == ['HOST = "127.0.0.1"'], (
        "one assignment, and it is loopback. A second one is where a flag "
        "would land without looking like a flag."
    )


def test_the_landing_page_needs_the_run_token(tool):
    assert tool.get("/")[0] == 403
    assert tool.get(f"/?k={tool.signin.token}")[0] == 200


def test_a_cross_site_navigation_cannot_reach_the_landing_page(tool):
    code, _ = tool.get(f"/?k={tool.signin.token}",
                       {"Sec-Fetch-Site": "cross-site",
                        "Origin": "https://somewhere.invalid"})
    assert code == 403


def test_the_landing_page_offers_a_link_out_and_no_target_that_receives(tool):
    """The structural difference between an auth redirect and a write path.

    A link to the provider sends this page's data nowhere. A form, a POST, a
    scripted request or a beacon is a target that receives. This page has the
    first and none of the second, which is the property `SIGNIN.md` proposes
    the `astro/dist` guard should key on if sign-in is ever taken into the
    built site.
    """
    _, page = tool.get(f"/?k={tool.signin.token}")
    assert "/auth/v1/authorize?" in page
    for banned in ("<form", "XMLHttpRequest", "sendBeacon", "enctype",
                   "formaction", "multipart/form-data", "<script", "fetch("):
        assert banned not in page, f"the sign-in page grew {banned}"


def test_the_landing_page_says_what_is_about_to_be_read_before_it_is_read(tool):
    _, page = tool.get(f"/?k={tool.signin.token}")
    assert "sub" in page and "orgs" in page
    assert "renamed" in page, "the reader is told why the handle is not the binding"


def test_the_callback_needs_no_run_token_because_the_provider_drives_it(tool):
    """It arrives cross-site on a legitimate return, so the token and the
    `Origin` check cannot apply. What replaces them is the single-use verifier
    and an exchange the caller cannot fake."""
    tool.get(f"/?k={tool.signin.token}")
    code, page = tool.get("/callback?code=stub-authorization-code",
                          {"Sec-Fetch-Site": "cross-site"})
    assert code == 200
    assert "synthetic-org" in page and "confirmed" in page


def test_a_callback_with_no_flow_in_flight_is_refused(tool):
    code, page = tool.get("/callback?code=stub-authorization-code")
    assert code == 400
    assert "no sign-in is in flight" in page
    assert signin.read_record(tool.record) == []


def test_a_callback_with_no_code_names_the_two_ways_that_happens(tool):
    tool.get(f"/?k={tool.signin.token}")
    code, page = tool.get("/callback")
    assert code == 400
    assert "access_token" in page, "the fragment case has to be named"
    assert "Redirect URLs" in page, "so does the allowlist case"


def test_a_provider_side_failure_is_reported_as_what_it_was(tool):
    tool.get(f"/?k={tool.signin.token}")
    code, page = tool.get("/callback?error=access_denied"
                          "&error_description=the+person+said+no")
    assert code == 400
    assert "the person said no" in page


def test_a_session_with_no_provider_token_records_nothing_and_says_why(
        tool, monkeypatch):
    """The token is returned on the sign-in and never on a refresh, so the fix
    is signing in again rather than retrying."""
    monkeypatch.setattr(signin, "exchange",
                        lambda *a, **k: {"access_token": "stub-session-token"})
    tool.get(f"/?k={tool.signin.token}")
    code, page = tool.get("/callback?code=stub-authorization-code")
    assert code == 400
    assert "sign in again" in page
    assert signin.read_record(tool.record) == []


# --------------------------------------------------------------------------- #
# Tokens, which are the thing that must never land anywhere.


def test_a_completed_capture_writes_no_token_anywhere(tool):
    tool.get(f"/?k={tool.signin.token}")
    tool.get("/callback?code=stub-authorization-code")
    entry, = signin.read_record(tool.record)
    written = json.dumps(entry)
    for secret in ("stub-provider-token", "stub-session-token",
                   "stub-refresh-token", "stub-authorization-code",
                   tool.signin.token):
        assert secret not in written, f"{secret} reached the record"
    assert set(entry) <= {"shape", "captured_at", "provider", "issuer",
                          "userinfo_endpoint", "sub", "preferred_username",
                          "orgs", "orgs_absence"}, (
        "an unexpected key in the capture. Every key here is a deliberate one "
        "and a new one is a decision, not an accident."
    )
    # The provider token did reach the userinfo call, which is the only place
    # it is allowed to go.
    assert tool.calls["token"] == "stub-provider-token"


def test_neither_the_code_nor_the_token_reaches_a_rendered_page(tool):
    tool.get(f"/?k={tool.signin.token}")
    _, page = tool.get("/callback?code=stub-authorization-code")
    for secret in ("stub-provider-token", "stub-session-token",
                   "stub-authorization-code"):
        assert secret not in page


def test_the_log_line_drops_the_query_string_where_the_code_arrives():
    """The default handler logs the request line. On the callback that is the
    authorization code, and a terminal scrollback is not a place for one."""
    source = (ROOT / "artifacts" / "signin.py").read_text()
    assert "def log_message" in source
    body = source.split("def log_message", 1)[1].split("\n    def ", 1)[0]
    assert "urlsplit" in body and ".path" in body
    assert "self.path}" not in body


def test_nothing_in_the_module_prints_or_writes_a_secret():
    source = (ROOT / "artifacts" / "signin.py").read_text()
    code = "\n".join(l for l in source.splitlines() if not l.lstrip().startswith("#"))
    for pattern in (r"print\([^)]*\b(token|secret|key|code)\b",
                    r"(append_record|write_text|\.write)\([^)]*\b"
                    r"(provider_token|access_token|refresh_token|verifier)\b",
                    r"log[^\n]*\b(provider_token|access_token|code)\b"):
        assert not re.search(pattern, code), f"{pattern} matched"
    # The client secret is Supabase's. This module names it in prose, to say
    # which setting the project needs, and never reads it, which is the thing
    # that matters: what is never in a variable is never in an error message.
    assert not re.search(r"""\benv\s*(\.get\(|\[)\s*["']HF_OAUTH""", code), (
        "nothing here reads a Hugging Face app credential. Supabase is the "
        "confidential client and performs the exchange."
    )


def test_the_env_file_is_read_from_outside_the_repository_and_is_ignored():
    """`.env` has been gitignored since before the first file existed."""
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in ignored
    assert "artifacts/memberships.jsonl" in ignored, (
        "a capture is a dated statement about a real person. Whether one "
        "becomes part of the published snapshot is a publish-step decision, "
        "not something the capture step makes by writing to a tracked file."
    )


def test_a_missing_env_file_refuses_with_the_names_it_needed(tmp_path):
    with pytest.raises(signin.Refused) as refused:
        signin.read_env(tmp_path / "nothing-here")
    said = str(refused.value)
    assert "SUPABASE_URL" in said and "HF_OAUTH_CLIENT_ID" in said


def test_config_names_which_setting_is_missing():
    with pytest.raises(signin.Refused) as refused:
        signin.config({"SUPABASE_URL": "https://p.example.invalid"})
    assert "SUPABASE_PUBLISHABLE_KEY" in str(refused.value)


# --------------------------------------------------------------------------- #
# The published site, which is where this would leak if it ever leaked.
#
# `tests/test_intake.py` reads `astro/dist` and fails on a form, a POST target,
# a scripted request or a loopback address. That guard is deliberately untouched
# here. These are the other half of it.


def test_the_site_does_not_know_the_sign_in_tool_exists():
    # Word boundaries, because "Assigning" contains the substring and a scanner
    # that is green for the wrong reason is the failure mode this repo has hit
    # three times.
    wanted = re.compile(r"\bsignin\b|signin\.py|memberships\.jsonl", re.I)
    hits = [
        p.relative_to(ROOT) for p in (ROOT / "astro" / "src").rglob("*")
        if p.is_file() and wanted.search(p.read_text(errors="ignore"))
    ]
    assert not hits, (
        f"the view layer references the sign-in tool: {hits}. It is a separate "
        "process on loopback. A sign-in button on the built site is the front "
        "door of a write path, and the dual-use policy a write path needs does "
        "not exist yet. `artifacts/SIGNIN.md` has the argument and the "
        "structural test that would replace this one if it is ever taken."
    )


def test_the_built_site_carries_no_supabase_endpoint():
    """The guard in test_intake.py looks for a write surface. An authorize URL
    is not one, so it would pass that guard while being the thing this
    decision is about. Checked here by name instead."""
    dist = ROOT / "astro" / "dist"
    if not dist.exists():
        pytest.skip("site not built; run `make site`")
    offenders = [
        p.relative_to(dist) for p in dist.rglob("*")
        if p.is_file() and p.suffix in {".html", ".js", ".mjs", ".css"}
        and re.search(r"/auth/v1/|supabase|signInWithOAuth", p.read_text(errors="ignore"), re.I)
    ]
    assert not offenders, f"an identity endpoint is in the built site: {offenders}"


def test_the_sign_in_tool_is_not_part_of_the_build():
    """Nothing in the build chain runs it, so nothing it does can reach a page."""
    makefile = (ROOT / "Makefile").read_text()
    assert "signin" not in makefile


def test_the_tool_adds_no_dependency():
    """Stdlib only. Nothing to pin, nothing to license-audit, no copyleft."""
    source = (ROOT / "artifacts" / "signin.py").read_text()
    # Column zero only. Indented `from` in prose inside a docstring is not an
    # import, and matching it made this assert on the word "a".
    imports = set(re.findall(r"^(?:import|from)\s+([A-Za-z_][\w.]*)",
                             source, re.M))
    assert "urllib.request" in imports, "the scan has to have found the imports"
    third_party = imports - {
        "argparse", "base64", "dataclasses", "datetime", "hashlib", "html",
        "http", "http.server", "json", "pathlib", "secrets", "sys",
        "threading", "urllib", "urllib.error", "urllib.parse",
        "urllib.request", "webbrowser", "__future__",
    }
    assert not third_party, f"a dependency arrived: {third_party}"
