"""`/signed-in/`: the return leg, the submission it makes possible, and the
guards that were rewritten rather than deleted to let it exist.

Premise, restated because a premise stated in one file gets violated in every
other one: **plurality is the product, the registry never designates, and
consumers pin visibly.** Identity is somebody else's here. Signing in confers no
standing, nothing on that page ranks, counts or orders anything, and there is no
queue: the namespace is the handle the provider reported, so there is nothing for
a reviewer to decide.

**This file replaces `tests/test_signin.py`, which went with the loopback tool it
tested.** What it inherits is the part that was about the shape of the evidence
rather than about a socket: `orgs` has three states and they are three different
facts, a capture binds `sub` and never the handle, a membership is confirmed on a
date and never called verified, and no key that reads like a credential appears
anywhere. Those ran against `artifacts/signin.py` in Python and now run against
`astro/src/lib/handshake.mjs` under node, because that is the file that writes a
capture now and there is one of it rather than two.

**Every test that touches the network is absent on purpose.** `make verify` runs
from a clean checkout with no network. What is checked here is what the built
page contains and what the pure module computes; whether Hugging Face answers is
not this gate's question and a gate that depended on it would go red for reasons
that have nothing to do with this repository.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"
LIB = ROOT / "astro" / "src" / "lib"
HANDSHAKE = LIB / "handshake.mjs"
HUB = LIB / "hub.mjs"
PAGE = ROOT / "astro" / "src" / "pages" / "signed-in.astro"
BUILT = DIST / "signed-in" / "index.html"

NODE = shutil.which("node")


# --------------------------------------------------------------------------- #
# Running the module the page runs, rather than a Python restatement of it.


def run_js(body: str):
    """Evaluate `body` against the real module and return what it printed.

    Against the file itself, imported by URL, so there is no copy of the logic
    in this directory to drift from the one that ships. A second implementation
    in a test is the same failure as a second implementation in the product,
    one layer further out and harder to notice.
    """
    if not NODE:
        pytest.skip("node not on PATH")
    script = (
        f"import * as h from {json.dumps(HANDSHAKE.as_uri())};\n"
        "const out = await (async () => {\n" + body + "\n})();\n"
        "process.stdout.write(JSON.stringify(out ?? null));\n"
    )
    done = subprocess.run(
        [NODE, "--input-type=module", "-e", script],
        capture_output=True, text=True,
    )
    if done.returncode != 0:
        raise AssertionError(done.stderr.strip())
    return json.loads(done.stdout or "null")


def capture_from(userinfo: dict, **kw) -> dict:
    said = json.dumps(userinfo)
    meta = json.dumps({
        "provider": kw.get("provider", "custom:huggingface"),
        "issuer": kw.get("issuer", "https://huggingface.co"),
        "endpoint": kw.get("endpoint", "https://huggingface.co/oauth/userinfo"),
        "capturedAt": kw.get("captured_at", "2026-09-20T00:00:00Z"),
    })
    return run_js(f"return h.captureFrom({said}, {meta});")


def test_node_is_the_thing_that_runs_this_module():
    """The suite would skip silently on a machine with no node, and a skipped
    guard is a guard that is not there. `astro` needs node to build at all, so
    a checkout that can run `make verify` can run this."""
    assert NODE, "node is not on PATH, and the site cannot be built without it"


# --------------------------------------------------------------------------- #
# The capture, which is what survived the deleted file.


def test_a_capture_carries_the_moment_it_was_taken():
    entry = capture_from({"sub": "62cf4580e7f6014c0ea2450f", "orgs": []})
    assert entry["captured_at"] == "2026-09-20T00:00:00Z"
    assert entry["shape"] == "controlbun.registry/membership-capture@1"
    assert entry["userinfo_endpoint"] == "https://huggingface.co/oauth/userinfo"


def test_it_binds_to_sub_and_keeps_the_handle_as_a_separate_thing():
    """Handles are renameable, so a record bound to one either breaks on a
    rename or follows the name to whoever takes it next."""
    entry = capture_from({"sub": "opaque-subject", "preferred_username": "someone"})
    assert entry["sub"] == "opaque-subject"
    assert entry["preferred_username"] == "someone"


def test_no_sub_is_refused_rather_than_recorded_against_the_handle():
    with pytest.raises(AssertionError) as refused:
        capture_from({"preferred_username": "someone"})
    assert "no `sub`" in str(refused.value)


def test_orgs_has_three_states_and_they_are_three_different_facts():
    """The rule `DECISIONS.md` 2026-09-20 says has to survive the deleted file.

    A list is what the provider said. `[]` is membership of nothing and is a
    real answer. `null` is the provider saying nothing at all, and it carries
    its own sentence rather than reading as an empty answer or as a failure.
    """
    said = capture_from({"sub": "s", "orgs": [{"name": "controlbun"}]})
    assert said["orgs"] == [{"name": "controlbun"}]
    assert "orgs_absence" not in said

    none = capture_from({"sub": "s", "orgs": []})
    assert none["orgs"] == []
    assert "orgs_absence" not in none, (
        "membership of nothing is an answer, and a sentence beside it would "
        "read as the provider having said nothing"
    )

    silent = capture_from({"sub": "s"})
    assert silent["orgs"] is None
    assert "not the same as membership of none" in silent["orgs_absence"]
    assert "not a failure" in silent["orgs_absence"]


def test_an_org_entry_is_passed_through_exactly_as_the_provider_wrote_it():
    """Reshaping an entry into the keys this project happens to know is a closed
    enumeration with a different hat on, and the next key Hugging Face adds
    would be dropped on the floor."""
    odd = {"name": "lab", "roleInOrg": "admin", "aKeyNobodyHasSeen": 7,
           "nested": {"deep": True}}
    entry = capture_from({"sub": "s", "orgs": [odd]})
    assert entry["orgs"] == [odd]


def test_a_membership_is_confirmed_on_a_date_and_never_called_verified():
    lines = run_js(
        'return h.confirmations({captured_at: "2026-09-20T00:00:00Z",'
        ' orgs: [{name: "controlbun"}, {}]});'
    )
    assert lines[0] == "member of controlbun, confirmed 2026-09-20T00:00:00Z"
    assert "did not name" in lines[1], (
        "an entry with no recognizable name still gets a sentence rather than "
        "being dropped, because dropping it loses an organization quietly"
    )
    assert not any(re.search(r"verif", line, re.I) for line in lines)


def test_an_unobserved_membership_produces_no_sentence_at_all():
    assert run_js('return h.confirmations({orgs: null});') == []


def test_no_key_that_reads_like_a_credential_can_reach_a_capture():
    """`artifacts/claim.py` walks every key and stops the run on one of these.

    The capture never carries one, and this is the check that the writer cannot
    start: a userinfo response holding a token is copied into nothing, because
    the projection names its fields rather than spreading what it was given.
    """
    entry = capture_from({
        "sub": "s", "access_token": "should-not-travel",
        "provider_token": "nor-this", "refresh_token": "nor-this-either",
    })
    flat = json.dumps(entry).lower()
    for word in ("token", "secret", "password", "credential", "bearer",
                 "verifier", "apikey"):
        assert word not in flat, f"a capture carried a key reading like {word!r}"


# --------------------------------------------------------------------------- #
# PKCE and the authorize URL.


def test_the_challenge_is_the_s256_of_the_verifier_unpadded():
    same = run_js(
        "const p = await h.pkcePair();"
        "const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(p.verifier));"
        "const b = btoa(String.fromCharCode(...new Uint8Array(d)))"
        "  .replace(/\\+/g,'-').replace(/\\//g,'_').replace(/=+$/,'');"
        "return {match: b === p.challenge, padded: /=/.test(p.challenge),"
        " length: p.verifier.length};"
    )
    assert same["match"]
    assert not same["padded"]
    # Between 43 and 128 characters is what Supabase validates a verifier against.
    assert 43 <= same["length"] <= 128


def test_two_runs_do_not_share_a_verifier():
    assert run_js(
        "const a = await h.pkcePair(); const b = await h.pkcePair();"
        "return a.verifier === b.verifier;"
    ) is False


def test_the_authorize_url_carries_pkce_and_the_scopes_it_was_given():
    """The PKCE parameters are load-bearing rather than decoration. Supply them
    and the return leg is `?code=` in the query string, which the page reads and
    then removes from the address bar. Omit them and Supabase runs the implicit
    flow and puts the answer in a fragment, which is a session in every history
    entry that copies the URL.
    """
    url = run_js(
        'return h.authorizeUrl("https://x.supabase.co/", {'
        ' provider: "custom:huggingface",'
        ' redirectTo: "https://controlbun.com/signed-in/",'
        ' challenge: "chal",'
        ' scopes: ["openid", "profile", "read-memberships"]});'
    )
    assert url.startswith("https://x.supabase.co/auth/v1/authorize?")
    assert "code_challenge=chal" in url
    assert "code_challenge_method=s256" in url
    assert "scopes=openid+profile+read-memberships" in url


def test_the_scope_parameter_replaces_rather_than_adds():
    """Verified against supabase/auth's `loadCustomProvider` on 2026-09-20: a
    `scopes` query parameter overrides the provider's configured list entirely.
    So the wider request has to restate the narrow ones, and a caller that
    passed only the extra would silently drop `read-memberships`.

    Checked here as a property of the page's two constants rather than of the
    network: the write list contains the read list.
    """
    source = PAGE.read_text()
    read = re.search(r'READ_SCOPES = "([^"]+)"', source).group(1).split()
    write = re.search(r'WRITE_SCOPES = "([^"]+)"', source).group(1).split()
    assert set(read) <= set(write), (
        f"{sorted(set(read) - set(write))} is asked for at sign-in and not at "
        "upload, so taking the offer would drop it"
    )
    assert set(write) - set(read), "the upload asks for nothing extra at all"


def test_signing_in_asks_for_no_write_access_to_anything():
    """A reader, a namespace claimant and anybody submitting a link to an
    already-public file is never asked to grant write access. That is the whole
    reason the scope is incremental, and it is a property of one constant."""
    read = re.search(
        r'READ_SCOPES = "([^"]+)"', PAGE.read_text()
    ).group(1).split()

    # Checked as a property rather than against a literal list. This asserted
    # the exact three, and adding `email` broke it: Supabase refuses the
    # sign-in without an email claim, because its OIDC handler builds an
    # `auth.users` row and that row needs an address. A hardcoded list turns
    # every legitimate change into a failure and teaches whoever hits it to
    # edit the expectation, which is how a check stops meaning anything.
    #
    # What has to stay true is that nothing here grants write access. Every
    # scope has to be one somebody deliberately put on this list.
    READ_ONLY = {"openid", "email", "profile", "read-memberships"}
    unexpected = [s for s in read if s not in READ_ONLY]
    assert not unexpected, (
        f"{unexpected} is not a scope this list was written to include. "
        "Adding one is a decision: say in the page what it is for."
    )
    for scope in read:
        assert not re.search(r"write|manage|contribute|jobs|webhooks|inference",
                             scope), f"{scope} is not a read scope"


def test_the_upload_asks_for_the_narrowest_scope_that_creates_a_repository():
    """`contribute-repos` is documented by Hugging Face as "Create repositories
    and access those created by this app. Cannot access any other repositories
    unless additional permissions are granted." `write-repos` and
    `manage-repos` both reach every repository the person owns, which is more
    than putting one file in a new one needs."""
    write = re.search(
        r'WRITE_SCOPES = "([^"]+)"', PAGE.read_text()
    ).group(1).split()
    assert "contribute-repos" in write
    for wider in ("write-repos", "manage-repos", "read-repos"):
        assert wider not in write, (
            f"{wider} reaches repositories the offer has no business in"
        )


# --------------------------------------------------------------------------- #
# The submission.


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
# What the built page says and does not do.


def built() -> str:
    if not BUILT.exists():
        pytest.skip("site not built; run `make site`")
    return BUILT.read_text()


def bundle() -> str:
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    scripts = re.findall(r'<script[^>]*src="([^"]+)"', built())
    text = ""
    for src in scripts:
        path = DIST / src.lstrip("/")
        if path.exists():
            text += path.read_text()
    assert text, "the page ships no script, so there is no return leg on it"
    return text


def text_of(html: str) -> str:
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def test_the_identity_endpoint_is_on_this_page_and_on_no_other():
    """The guard `tests/test_signin.py` held for the whole build, narrowed
    rather than dropped.

    It used to fail on `/auth/v1/`, `supabase` or `signInWithOAuth` anywhere in
    `astro/dist`, which was the right check while nothing on the site could hold
    a session. One page holds one now. Every other page must still be clean, and
    the same string turning up under `/about/` or on a submission view is still
    a finding.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    allowed = {"signed-in/index.html"}
    scripts = {
        src.lstrip("/") for src in re.findall(r'<script[^>]*src="([^"]+)"', built())
    }
    offenders = []
    for path in sorted(DIST.rglob("*")):
        if not path.is_file() or path.suffix not in {".html", ".js", ".mjs", ".css"}:
            continue
        where = str(path.relative_to(DIST))
        if where in allowed or where in scripts:
            continue
        if re.search(r"/auth/v1/|supabase|signInWithOAuth", path.read_text(errors="ignore"), re.I):
            offenders.append(where)
    assert not offenders, (
        f"an identity endpoint is on a page that has no business with one: {offenders}"
    )


def test_the_page_keeps_the_session_and_never_the_provider_token():
    """One credential persists and the other never does.

    **The old property.** This asserted two writes, neither of which was a
    credential: the PKCE verifier, and three display facts about who signed in.
    That was true and the arrangement behind it was not honest, because the bar
    read those display facts and offered **Add artifact** to somebody whose
    session had died on their last reload.

    **Why it stopped being the right one.** Making that offer true meant keeping
    the Supabase session with its refresh token, which is a credential, and
    which is the whole point: row-level security scopes that JWT to inserting
    one row as its owner, it reads nobody else's rows, and there is no update or
    delete policy at all.

    **What replaced it.** The Hugging Face `provider_token` never reaches
    storage in any spelling. It is the one that can create and write
    repositories in somebody's own namespace, and Hugging Face returns it on the
    sign-in itself and never on a renewal, so keeping it would buy nothing past
    its expiry. What is kept is one key holding `heldSessionFrom`'s projection,
    and the page writes it through one function.
    `tests/test_nav_account.py` holds the same rule across every file in the
    view layer.
    """
    code = bundle()
    writes = [
        m.group(0) for m in re.finditer(
            r"(?:localStorage\.setItem|sessionStorage\.setItem|document\.cookie\s*=)"
            r"[^;]{0,120}", code,
        )
    ]
    assert len(writes) == 2, f"more than the verifier and the session: {writes}"
    assert "removeItem" in code, "the verifier is stored and never removed"
    for leak in (r"setItem\([^)]*provider_token", r"setItem\([^)]*providerToken",
                 r"cookie\s*=[^;]*token"):
        assert not re.search(leak, code, re.I), f"a provider token is written: {leak}"

    # What is written is read off the source rather than the bundle, because
    # the bundler renames the constant and `setItem(F,a)` says nothing about
    # what F is. The count above is the bundle's answer and this is the
    # source's, and both have to hold.
    source = PAGE.read_text()
    written = re.findall(r"sessionStorage\.setItem\(\s*([A-Za-z_$][\w$]*)", source)
    assert written == ["VERIFIER"], written
    assert re.search(r'VERIFIER\s*=\s*"controlbun\.pkce"', source), (
        "the one thing in sessionStorage is no longer the PKCE verifier"
    )
    assert "sessionStorage.removeItem(VERIFIER)" in source

    kept = re.findall(r"localStorage\.setItem\(\s*([A-Za-z_$][\w$]*)", source)
    assert kept == ["HELD"], kept
    assert re.search(r'HELD\s*=\s*"controlbun\.session"', source), (
        "the key the session lives under moved, and the bar reads the old one"
    )
    # The value is the module's projection and not an object built here. A
    # literal assembled at the call site is how a field nobody intended gets
    # kept: `heldSessionFrom` names its fields, so neither provider token and
    # not the email on the Supabase user row can push into a browser.
    assert re.search(
        r"localStorage\.setItem\(HELD, JSON\.stringify\(held\)\);", source
    ), "the page assembles what it keeps rather than writing the module's record"
    for call in re.findall(r"\bkeep\(([^\n]*)", source):
        if call.startswith("held)"):
            continue  # the definition
        assert call.startswith("heldSessionFrom("), (
            f"keep({call.strip()}) writes something the module did not build"
        )


def test_the_renewal_is_the_endpoint_supabase_documents():
    """Read rather than recalled, against supabase/auth v2.197.0, which is what
    the live project answers at `/auth/v1/health`, on 2026-09-20.

    `RefreshTokenGrantParams` in `internal/api/token_refresh.go` is one field,
    `refresh_token`. `RefreshTokenGrant` in `internal/tokens/service.go` sets
    `Token`, `TokenType`, `ExpiresIn`, `ExpiresAt`, `RefreshToken` and `User`
    and nothing else; `ProviderAccessToken` is `omitempty` on that struct and is
    assigned in exactly one place in the package, inside the PKCE branch of
    `internal/api/token.go`. So a renewal never returns a Hugging Face token.
    """
    source = HUB.read_text()
    m = re.search(r"export async function refreshSession\(.*?\n\}", source, re.S)
    assert m, "refreshSession is gone, so a return visit re-authorizes"
    body = m.group(0)
    assert "/auth/v1/token?grant_type=refresh_token" in body
    assert 'method: "POST"' in body
    assert "refresh_token: refreshToken" in body, (
        "the body field is not the one the endpoint reads"
    )
    # The one call here whose credential is in the request body rather than in
    # a header, so a failing body is never rendered whole and is dropped
    # outright if it contains what was sent.
    assert "ask(" not in body, (
        "the renewal goes through the shared helper, which reads a failing "
        "body back into the message. This call carries a refresh token in that "
        "body and an error page that reflected the request would put it on "
        "screen."
    )
    assert "said.includes(refreshToken)" in body


def test_the_code_is_taken_out_of_the_address_bar():
    """An authorization code in the URL is in every history entry, every copied
    link and every referrer. The loopback tool's answer was to drop the query
    string from its log line; the browser's answer is to replace the URL."""
    assert "replaceState" in bundle()


def test_the_page_receives_nothing_and_submits_no_form():
    """The structural criterion, applied to the one page that would break it
    first. A field that holds what somebody typed is not a target; a form with
    somewhere to send it is. This page has the first and not the second."""
    html = built()
    assert "<input" in html, "the submission form has no fields, so there is none"
    for receiving in (r"<form\b", r"\bformaction\b", r"\baction\s*=", r"\benctype\b"):
        assert not re.search(receiving, html, re.I), (
            f"{receiving} is on the page, which means something submits"
        )


def test_the_page_says_a_submission_does_not_appear_until_it_is_published():
    """The sentence that keeps this honest. The corpus is a file in git and the
    site is built from it on one machine, which is what lets the falsifier check
    the build readers actually read."""
    body = text_of(built()).lower()
    assert "does not appear on this site until the author rebuilds and publishes" in body
    assert "file in git" in body


# --------------------------------------------------------------------------- #
# The submission is sent, since 2026-09-20.


def test_the_page_sends_the_submission_to_the_holding_table():
    """The form posts. Downloading is a copy for the person who made it and is
    no longer how anything gets here, which the page has to say in the same
    place it offers the download."""
    code = bundle()
    assert "/rest/v1/pending_submission" in code, (
        "the page no longer sends anything, or sends it somewhere this test "
        "has not read"
    )
    html = built()
    assert 'id="send-record"' in html, "there is no button that sends"
    assert 'id="keep-record"' in html, "the download went away rather than moving"


def test_the_page_no_longer_says_it_writes_to_no_database():
    """It did say that, correctly, until the table existed. A sentence that was
    true and stopped being true is worse than one that was never true, because
    it was checked once."""
    body = text_of(built()).lower()
    for gone in ("nothing on this page writes to a database",
                 "no row is written",
                 "it stores nothing: no cookie, no token, no row"):
        assert gone not in body, f"the page still claims {gone!r}"


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
    assert "return=representation" in HUB.read_text()
    source = PAGE.read_text()
    for field in ("written.received_at", "written.id", "written.handle",
                  "written.subject"):
        assert field in source, f"the receipt does not show {field}"
    body = text_of(built()).lower()
    assert "what the database wrote, read back off its answer" in body


def test_the_page_still_offers_nothing_to_approve_after_it_started_sending():
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
                     "your position", "position in", "your turn", "under review"):
        assert queueing not in body, f"{queueing!r} is a queue arriving in prose"


def test_the_session_is_never_rendered_and_the_provider_token_is_never_held():
    """The two halves of the split, at the page that holds both.

    **The old property.** The session lived in one module variable, was never
    put in storage, and was gone on a reload. That is what made the bar's
    remembered handle an over-promise, so it was the property that had to go.

    **What replaced it.** The session is held in one variable and written to one
    key through one function, which is the test above. The provider token is
    held in one local inside the function that uses it and never assigned to
    anything that outlives the call. And neither is rendered, which did not
    change: a token in the DOM is a token in a screenshot, in a bug report and
    in whatever reads the page.
    """
    source = PAGE.read_text()
    assert re.search(r"let signed = null;", source), "the session is held elsewhere"
    # Kept under one key and nothing else. The count in the test above covers
    # the bundle; this covers the name, which a bundler renames away.
    assert not re.search(r"setItem\([^)]*signed", source)
    assert re.search(r"function keep\(held\)", source), (
        "the page no longer writes the session through one function"
    )
    # The provider token is a parameter and a local, and never a variable with
    # a lifetime. `let token` at module scope is the edit this refuses.
    assert not re.search(r"^\s*(?:let|var)\s+token\b", source, re.M), (
        "the provider token is held in a variable outside the call that uses it"
    )
    for holding in (r"signed\.provider_token", r"held\.provider_token",
                    r"provider_token\s*:"):
        assert not re.search(holding, source), (
            f"the provider token is kept on an object: {holding}"
        )
    # Not rendered, either of them.
    for rendering in (r'say\("[^"]*",\s*signed', r"textContent\s*=\s*signed",
                      r'say\("[^"]*",\s*[^)]*\.access_token\b',
                      r'say\("[^"]*",\s*token\b'):
        assert not re.search(rendering, source), (
            f"a credential reaches the page: {rendering}"
        )


def test_a_refused_renewal_is_a_state_with_its_own_words():
    """Not an error and not silence. A reader whose session was signed out
    somewhere else did nothing wrong, and there is one thing to do about it, so
    the page says what happened, drops the session and shows the button."""
    source = PAGE.read_text()
    assert "function staleSaid(problem)" in source
    assert 'show("stale", true)' in source
    said = re.search(r"function staleSaid\(problem\) \{(.*?)\n  \}", source, re.S)
    assert said, "nothing builds the sentence"
    assert "not a failure of anything you typed" in said.group(1)
    # The session goes, so the next press does not fail the same way and the
    # bar stops offering a way in that has nothing behind it.
    assert re.search(r"forget\(\);", source), (
        "a session the identity service refuses is kept anyway"
    )
    assert re.search(r"function forget\(\) \{\s*\n\s*localStorage\.removeItem\(HELD\);",
                     source)


def test_the_submit_path_renews_rather_than_asking_for_a_new_authorization():
    """The press that matters most is the one most likely to land on a spent
    access token, since the page may have been open for an hour. Renewing is a
    request; re-authorizing is a redirect that loses the record on the page."""
    source = PAGE.read_text()
    assert re.search(r"const now = await usable\(\);", source), (
        "the send path does not renew, so a spent token is a failed submission"
    )
    usable = re.search(r"async function usable\(\) \{(.*?)\n  \}", source, re.S)
    assert usable, "there is no renewal before the send"
    assert "accessSpent(signed)" in usable.group(1)
    assert "refreshSession(" in usable.group(1)
    # And it renews rather than starting an authorization, which would leave
    # the page and take the typed record with it.
    assert "begin(" not in usable.group(1), (
        "the send path re-authorizes, which navigates away from the record"
    )


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


def test_the_page_offers_no_queue_and_nothing_to_approve():
    body = text_of(built()).lower()
    for absent in ("pending review", "awaiting approval", "submission queue",
                   "will be reviewed", "once approved", "moderat"):
        assert absent not in body, f"{absent!r} is a review step arriving in prose"
    assert "nothing to approve" in body


def test_the_page_names_what_the_handle_rule_makes_impossible():
    """A rule that cannot name its cost has not been thought through."""
    body = text_of(built()).lower()
    assert "pseudonym" in body
    assert "no field for it" in body


def test_the_page_says_reading_stays_anonymous():
    body = text_of(built()).lower()
    assert "anonymous" in body


def test_a_membership_on_the_page_is_never_called_verified():
    assert not re.search(r"\bverif", text_of(built()), re.I)


def test_the_upload_offer_says_whose_account_the_bytes_go_to():
    body = text_of(built()).lower()
    assert "your own account" in body
    assert "never to this project" in body
    assert "one more permission at that point and not before" in body


def test_the_page_is_reachable():
    """A page nothing links to is a page nobody reads."""
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    linkers = [
        str(p.relative_to(DIST)) for p in DIST.rglob("*.html")
        if p.parent.name != "signed-in"
        and 'href="/signed-in/"' in p.read_text(errors="ignore")
    ]
    assert linkers, "nothing on the site links to /signed-in/"
    assert "sign-in/index.html" in linkers, (
        "the page that explains signing in no longer links to the page that "
        "does it, so a reader who finishes the explanation has nowhere to go"
    )


def test_the_page_adds_no_dependency():
    """One page, one script, no dependency, which is what `SIGNIN.md` costed
    out before it was deleted. The two modules it imports are this
    repository's."""
    package = json.loads((ROOT / "astro" / "package.json").read_text())
    assert set(package.get("devDependencies", {})) == {"astro", "pagefind"}
    assert not package.get("dependencies")
    for module in (HANDSHAKE, HUB):
        for line in module.read_text().splitlines():
            assert not re.match(r"\s*import .* from ['\"][^./]", line), (
                f"{module.name} imports a package: {line.strip()}"
            )


def without_comments(source: str) -> str:
    """The code, with the prose taken out.

    Both modules explain in their own docstrings what they do not do, which a
    substring scan reads as them doing it. Same trap as everywhere else here:
    the sentence saying "writes nothing to `localStorage`" is the one a naive
    grep flags.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"^\s*//.*$", "", source, flags=re.M)


def test_the_pure_module_touches_no_network_and_no_dom():
    """The reason it is a separate file: everything about the shape of the
    evidence can be exercised without a browser, a provider or a person."""
    source = without_comments(HANDSHAKE.read_text())
    for reaching in ("fetch(", "document.", "window.", "localStorage",
                     "sessionStorage", "XMLHttpRequest"):
        assert reaching not in source, f"{HANDSHAKE.name} reaches {reaching}"


def test_the_network_module_writes_nothing_down():
    """A token is an argument, it goes into one header, and the frame ends."""
    source = without_comments(HUB.read_text())
    for writing in ("localStorage", "sessionStorage", "document.cookie",
                    "console.log", "console.error"):
        assert writing not in source, f"{HUB.name} writes to {writing}"


def test_that_comment_strip_does_not_hide_a_real_one():
    """The bite. A scanner that stops seeing the thing it looks for because a
    filter got too wide is the failure mode this repository has hit more than
    once, so the filter is shown keeping a real line."""
    sample = (
        "/** Writes nothing to localStorage. */\n"
        "// and not to sessionStorage either\n"
        "sessionStorage.setItem('x', y);\n"
    )
    stripped = without_comments(sample)
    assert "sessionStorage.setItem" in stripped
    assert "Writes nothing" not in stripped
    assert "not to sessionStorage either" not in stripped


def test_the_source_records_that_the_reversal_was_taken_deliberately():
    """The next person to open this page will wonder how a static build grew a
    client. The answer has to be in the file rather than only in a report."""
    source = PAGE.read_text()
    assert "reverses a property recorded twice" in source
    assert "DECISIONS.md" in source
    assert 'output: "static"' in source
