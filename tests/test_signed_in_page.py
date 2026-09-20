"""`/signed-in/`: the return leg, and the guards that were rewritten rather than
deleted to let it exist.

Premise, restated because a premise stated in one file gets violated in every
other one: **plurality is the product, the registry never designates, and
consumers pin visibly.** Identity is somebody else's here. Signing in confers no
standing, nothing on that page ranks, counts or orders anything, and there is no
queue: the namespace is the handle the provider reported, so there is nothing for
a reviewer to decide.

**The submission moved out on 2026-09-20 and is in `tests/test_submit_page.py`.**
The form went to `/submit/` with it: the bar's **Add artifact** pointed at this
page while the two were joined, so pressing it mid-sign-in reloaded the page and
discarded the exchange in progress. What is left here is what the page's name
says, plus the two properties that were narrowed rather than dropped when the
session started persisting.

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
# The session in a browser, which is one module rather than a copy per page
# since `/submit/` also has to restore, renew and drop one.
HELD = LIB / "held.mjs"
PAGE = ROOT / "astro" / "src" / "pages" / "signed-in.astro"
SUBMIT = ROOT / "astro" / "src" / "pages" / "submit.astro"
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

    Checked here as a property of two constants rather than of the network: the
    write list contains the read list.

    Both live in `handshake.mjs` since 2026-09-20, because two pages read them:
    `/signed-in/` starts a sign-in and `/submit/` asks for the upload
    permission. A property that spans two files is a property that holds until
    somebody edits one of them.
    """
    source = HANDSHAKE.read_text()
    read = re.search(r'READ_SCOPES =\s*"([^"]+)"', source).group(1).split()
    write = re.search(r'WRITE_SCOPES =\s*\n?\s*"([^"]+)"', source).group(1).split()
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
        r'READ_SCOPES =\s*"([^"]+)"', HANDSHAKE.read_text()
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
        r'WRITE_SCOPES =\s*\n?\s*"([^"]+)"', HANDSHAKE.read_text()
    ).group(1).split()
    assert "contribute-repos" in write
    for wider in ("write-repos", "manage-repos", "read-repos"):
        assert wider not in write, (
            f"{wider} reaches repositories the offer has no business in"
        )


# --------------------------------------------------------------------------- #
# What the built page says and does not do.
#
# The submission itself is `tests/test_submit_page.py`, which holds the helpers
# that build one. It imports `run_js` from here rather than restating it.


def built() -> str:
    if not BUILT.exists():
        pytest.skip("site not built; run `make site`")
    return BUILT.read_text()


def reachable_scripts(page: str) -> list[Path]:
    """Every file a page's script loads, the ones it imports included.

    A bundler splits shared code into chunks that no `<script src>` names: the
    page loads one module and that module imports the rest. Reading only the
    tags was right while each page's script was a single file, and went quiet
    the moment two pages shared a module, which is the failure this repository
    keeps catching: a check that passes because it cannot see the thing it is
    about. `held.mjs` became that shared module on 2026-09-20 and took the
    session write with it.
    """
    queue = [(DIST / src.lstrip("/")).resolve()
             for src in re.findall(r'<script[^>]*src="([^"]+)"', page)]
    seen: list[Path] = []
    while queue:
        path = queue.pop()
        if path in seen or not path.exists():
            continue
        seen.append(path)
        code = path.read_text()
        for rel in re.findall(r'(?:from|import)\s*\(?\s*["\']([^"\']+)["\']', code):
            if rel.startswith("."):
                queue.append((path.parent / rel).resolve())
    return seen


def bundle() -> str:
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    text = "".join(path.read_text() for path in reachable_scripts(built()))
    assert text, "the page ships no script, so there is no return leg on it"
    return text


def test_the_scan_follows_the_imports_and_not_only_the_tags():
    """The bite. A chunk the page imports is code the page ships, and a scan
    that stopped at the tag would report on a fraction of it.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    tagged = {
        (DIST / src.lstrip("/")).resolve()
        for src in re.findall(r'<script[^>]*src="([^"]+)"', built())
    }
    found = set(reachable_scripts(built()))
    assert tagged <= found
    assert found - tagged, (
        "the page's script imports nothing, so this scan is the tag scan with "
        "more steps. If the bundler stopped splitting chunks, say so here."
    )


def text_of(html: str) -> str:
    for tag in ("script", "style"):
        html = re.sub(rf"<{tag}.*?</{tag}>", "", html, flags=re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


# The pages that talk to the identity service, with why each one does. Two
# since 2026-09-20, because the return leg and the submission form are two
# pages: this one exchanges an authorization code and renews a session, and
# `/submit/` renews one before it sends a row and exchanges a second code for
# the upload permission. Everything else on the site is a reader's page and has
# no business with an endpoint.
TALKS_TO_THE_SERVICE = {
    "signed-in/index.html": "the return leg. It exchanges the code, keeps the "
                            "session and reads what the provider said.",
    "submit/index.html": "renews the session before sending a row, and "
                         "exchanges the second code when somebody takes the "
                         "upload offer.",
}


def test_the_identity_endpoint_is_on_these_pages_and_on_no_other():
    """The guard `tests/test_signin.py` held for the whole build, narrowed
    rather than dropped.

    It used to fail on `/auth/v1/`, `supabase` or `signInWithOAuth` anywhere in
    `astro/dist`, which was the right check while nothing on the site could hold
    a session. Two pages hold one now, each with its reason written down. Every
    other page must still be clean, and the same string turning up under
    `/about/` or on a submission view is still a finding.
    """
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    allowed = set(TALKS_TO_THE_SERVICE)
    scripts = set()
    for where in TALKS_TO_THE_SERVICE:
        page = DIST / where
        if not page.exists():
            pytest.fail(f"{where} is on the list and was not built")
        # Imports followed, because the module that renews a session is a
        # shared chunk no tag names and it carries the endpoint by necessity.
        scripts.update(
            str(path.relative_to(DIST))
            for path in reachable_scripts(page.read_text())
        )
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
    written by one function in one module.
    `tests/test_nav_account.py` holds the same rule across every file in the
    view layer.

    **The write moved into `held.mjs` on 2026-09-20**, when `/submit/` became a
    second page that restores, renews and drops a session. The property was
    never "the page writes it in one place", it was "one function writes it",
    and a copy per page would have ended that. So the source half below reads
    the module, and the bundle half still reads what this page ships, which is
    the module plus its own verifier.
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

    held = HELD.read_text()
    kept = re.findall(r"localStorage\.setItem\(\s*([A-Za-z_$][\w$]*)", held)
    assert kept == ["HELD"], kept
    assert re.search(r'HELD\s*=\s*"controlbun\.session"', held), (
        "the key the session lives under moved, and the bar reads the old one"
    )
    # The value is the module's own projection and not an object a caller
    # built. `keep` takes what the endpoint answered rather than a record, so
    # there is no call site that could hand it a literal: `heldSessionFrom`
    # names its fields, so neither provider token and not the email on the
    # Supabase user row can push into a browser.
    assert re.search(
        r"const held = heldSessionFrom\(said, \{ provider \}\);\n"
        r"\s*localStorage\.setItem\(HELD, JSON\.stringify\(held\)\);",
        held,
    ), "the module writes something other than its own projection"
    # And no page writes that key at all.
    for page in (PAGE, SUBMIT):
        assert not re.search(r"localStorage\.setItem", page.read_text()), (
            f"{page.name} writes to localStorage itself, so there are two "
            "rules for one key again"
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
    """The structural criterion, applied where it would break first.

    A field that holds what somebody typed is not a target; a form with
    somewhere to send it is. This page has neither since the form left it, and
    `tests/test_submit_page.py` holds the same rule on the page that has the
    fields.
    """
    html = built()
    for receiving in (r"<form\b", r"\bformaction\b", r"\baction\s*=", r"\benctype\b"):
        assert not re.search(receiving, html, re.I), (
            f"{receiving} is on the page, which means something submits"
        )


def test_the_submission_form_is_not_on_this_page_any_more():
    """The split, asserted here as well as there.

    The form was here because the session died with the tab, so the only page
    that could know who was signed in was the one that had just signed them in.
    Putting it back would put the papercut back: the bar points at `/submit/`,
    and a second form here would be a second place a submission is built.
    """
    html = built()
    for gone in ('id="build-record"', 'id="send-record"', 'id="f-label"',
                 'id="f-pasted"'):
        assert gone not in html, f"{gone} is back on the return leg"
    assert 'href="/submit/"' in html, (
        "the return leg does not offer the page that takes a submission, so "
        "somebody who has just signed in has nowhere to go"
    )


def test_the_page_no_longer_says_it_writes_to_no_database():
    """It did say that, correctly, until the table existed. A sentence that was
    true and stopped being true is worse than one that was never true, because
    it was checked once."""
    body = text_of(built()).lower()
    for gone in ("nothing on this page writes to a database",
                 "no row is written",
                 "it stores nothing: no cookie, no token, no row"):
        assert gone not in body, f"the page still claims {gone!r}"


def test_the_page_says_the_namespace_is_not_a_field_anywhere():
    """The property the whole design rests on, said where somebody first sees
    their handle rather than only where they would type one.

    A submitter has to be able to tell that their handle is not a field
    somebody else could fill in, because that is the difference between this
    and a form where anybody can publish as anybody. The page that takes the
    submission says it too, and `tests/test_submit_page.py` holds that half.
    """
    body = text_of(built()).lower()
    assert "the database writes it from your session" in body
    assert "no box, and no default to type over" in body


def test_the_return_leg_offers_nothing_to_approve():
    """The thing a holding table turns into if nobody watches. `DECISIONS.md`
    2026-09-17 records why a review step with no stated rule fills with the
    reviewer's taste, and the namespace being the handle is why there is no
    question to ask in the first place."""
    body = text_of(built()).lower()
    # `position` alone is not on this list, and the reason is the trap
    # `CLAUDE.md` names: `steering_position` is a field on every intervention
    # here, so the bare substring flags a page for containing the schema. The
    # queue is "your position", not a column called position.
    for queueing in ("pending review", "awaiting approval", "in the queue",
                     "your position", "position in", "your turn", "under review",
                     "will be reviewed", "once approved", "moderat"):
        assert queueing not in body, f"{queueing!r} is a queue arriving in prose"


def test_the_session_is_never_rendered_and_the_provider_token_is_never_held():
    """The two halves of the split, at the page that holds both.

    **The old property.** The session lived in one module variable, was never
    put in storage, and was gone on a reload. That is what made the bar's
    remembered handle an over-promise, so it was the property that had to go.

    **What replaced it.** The session is held in one variable and written to one
    key through one function in one module, which is the test above. The
    provider token is held in one local inside the function that uses it and
    never assigned to anything that outlives the call. And neither is rendered,
    which did not change: a token in the DOM is a token in a screenshot, in a
    bug report and in whatever reads the page.

    Both pages that hold a session are read, because the rule is about the
    thing rather than about a file, and the second page is where it would be
    broken next.
    """
    for source in (PAGE.read_text(), SUBMIT.read_text()):
        # Kept under one key and nothing else. The count in the test above
        # covers the bundle; this covers the name, which a bundler renames
        # away.
        assert not re.search(r"setItem\([^)]*signed", source)
        # The provider token is a parameter and a local, and never a variable
        # with a lifetime. `let token` at module scope is the edit this
        # refuses.
        assert not re.search(r"^\s*(?:let|var)\s+token\b", source, re.M), (
            "the provider token is held in a variable outside the call that "
            "uses it"
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
    assert re.search(r"let signed = null;", SUBMIT.read_text()), (
        "the page that sends holds the session somewhere this has not read"
    )


def test_a_refused_renewal_is_a_state_with_its_own_words():
    """Not an error and not silence. A reader whose session was signed out
    somewhere else did nothing wrong, and there is one thing to do about it, so
    the page says what happened, drops the session and shows the button.

    The sentence is in `held.mjs` because two pages say it, and saying it twice
    is how two pages start saying different things about one state.
    """
    module = HELD.read_text()
    assert "export function staleSaid(problem)" in module
    said = re.search(r"export function staleSaid\(problem\) \{(.*?)\n\}",
                     module, re.S)
    assert said, "nothing builds the sentence"
    assert "not a failure of anything you typed" in said.group(1)
    # The session goes, so the next press does not fail the same way and the
    # bar stops offering a way in that has nothing behind it.
    assert re.search(r"forget\(\);", module), (
        "a session the identity service refuses is kept anyway"
    )
    assert re.search(
        r"export function forget\(\) \{\s*\n\s*localStorage\.removeItem\(HELD\);",
        module,
    )
    # And both pages show it rather than swallowing it.
    for page in (PAGE, SUBMIT):
        source = page.read_text()
        assert 'show("stale", true)' in source, f"{page.name} hides the state"
        assert "staleSaid(" in source, f"{page.name} shows it with no words"


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
