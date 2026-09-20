"""The bar at the top: two ways in, one shown, and one credential kept.

Premise, restated because a premise stated in one file gets violated in every
other one: **plurality is the product, the registry never designates, and
consumers pin visibly.** Holding a session changes which door the bar names
first and changes nothing about who may open it. `/sign-in/` explains, it links
to `/signed-in/`, and `/signed-in/` is where a submission is sent from. All
three are reachable by somebody who has never signed in, and nothing here is a
condition on publishing.

**The two properties this file exists for**, both of which would be satisfied by
prose and neither of which would then mean anything:

1. **No Hugging Face provider token is ever written to browser storage, the
   Supabase session is the only credential that is, it lives under one named
   key, and Sign out removes it.**

   This read "nothing on this site writes a token to browser storage", which was
   true and was the wrong property. It was true because the session died with
   the tab, and the cost of that was paid somewhere else: the bar said **Add
   artifact** off a remembered handle, to a reader whose session had been gone
   since their last reload, and the page behind it could only ask them to sign
   in again. Closing that gap meant the session had to persist, so the old
   property became false on 2026-09-20 and is narrowed here rather than dropped.

   What survived is the shape of the check: every write in `astro/src` is
   resolved to the literal key it is and refused if nobody accounted for it. The
   resolver that catches a renamed constant is the part that made the old
   version worth anything and it is unchanged. What changed is which keys may
   hold a credential and which credential is refused by name.
   `tests/test_signed_in_page.py` holds the same rule one level down, on the
   bundle the return leg actually ships.

2. **The bar's signed-in state never comes from anything the page asserts about
   a person.** It comes from one key in the reader's own browser and from
   nothing else. The failure this stops is specific and it is the obvious next
   edit: a submission page knows an author's handle, so a bar that read the page
   it was sitting on would greet a stranger by the name of whoever they were
   reading, and would do it on the pages where it looks most plausible.

**Read at the source, so these run without a build.** The page tests next door
skip when `astro/dist` is absent, which is right for a claim about rendered
output and wrong for a claim about what a file can do. Where a claim is about
what a reader sees, the built page is read as well and that half skips.

Nothing here fabricates a handle, a date or a number. The one handle written
down is the string a counterexample needs to be a counterexample, and the token
strings below are labels saying where they must not turn up.
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
SRC = ROOT / "astro" / "src"
NAV = SRC / "components" / "SiteNav.astro"
HEAD = SRC / "components" / "Head.astro"
HANDSHAKE = SRC / "lib" / "handshake.mjs"
SIGNED_IN = SRC / "pages" / "signed-in.astro"
CSS = SRC / "styles" / "app.css"

NODE = shutil.which("node")

# The key the whole arrangement turns on, written in one place here so a rename
# fails this file loudly rather than making every check below inert. It was
# `controlbun.who` and held a handle; it is `controlbun.session` and holds the
# Supabase session the handle came with, which is what stops the two from
# disagreeing.
SESSION_KEY = "controlbun.session"

# The key that held a handle and no session. Nothing writes it now and the head
# script deletes it, so a browser carrying one from an older build stops being
# offered a way in that cannot work.
RETIRED_KEY = "controlbun.who"


def source_files() -> list[Path]:
    """Every file in the view layer somebody could write a line of script in."""
    found = [
        p for p in sorted(SRC.rglob("*"))
        if p.is_file() and p.suffix in {".astro", ".mjs", ".js", ".ts", ".tsx"}
    ]
    assert found, "no view-layer source found, so everything below proves nothing"
    return found


def without_comments(source: str) -> str:
    """The code, with the prose taken out.

    Same reason as `tests/test_signed_in_page.py::without_comments`: every file
    here explains what it does not do, and a substring scan reads the
    explanation as the thing. Kept separate rather than imported, because that
    module skips its whole file on a machine with no node.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"^\s*//.*$", "", source, flags=re.M)


# --------------------------------------------------------------------------- #
# 1. One credential is kept, under one key, and it is not the provider's.


# Every key this site may put in a reader's browser, with why. An enumeration on
# purpose, and the right way round: the values enumerated are this project's
# own, and what is constrained is the registry rather than a contributor.
# `DECISIONS.md` 2026-09-15 named that inversion as the one legitimate closed
# set in this design, and `tests/test_intake.py` uses it for destinations.
MAY_KEEP = {
    "theme": "the reader's own display preference, read by the head script "
             "before first paint so a chosen theme does not flash.",
    "controlbun.pkce": "the PKCE verifier, which has to survive a navigation by "
                       "definition and is removed the moment it is used. On its "
                       "own, without the authorization code, it exchanges for "
                       "nothing.",
    SESSION_KEY: "the Supabase session: an access token, the refresh token that "
                 "renews it, when it expires, and the account id, subject and "
                 "handle it was issued for. Row-level security scopes that JWT "
                 "to inserting one row into `pending_submission` as its owner, "
                 "with no read of anybody else's rows and no update or delete "
                 "policy at all. It persists so a return visit is not a second "
                 "sign-in, and so the bar never offers a way in that has "
                 "nothing behind it.",
}

# The keys that may hold something a request can be made with, and why each one
# is on a list of two rather than on a list of one.
MAY_BE_A_CREDENTIAL = {
    "controlbun.pkce": "a verifier, which exchanges for nothing without the "
                       "authorization code and is removed the moment it is used",
    SESSION_KEY: "the Supabase session, which is the credential this change "
                 "exists to persist",
}

# Words that would mean the thing being kept is a credential rather than a
# display fact, matched against the whole call rather than against the key.
CREDENTIAL = r"token|secret|password|credential|bearer|apikey|api_key|verifier"

# The credential that must never reach storage, in every spelling Supabase uses
# for it. `contribute-repos` makes the first of these able to create and write
# repositories in somebody's Hugging Face namespace.
PROVIDER_CREDENTIAL = r"provider_token|provider_refresh_token|providerToken"


def storage_writes(text: str, *, where: str = "<text>") -> list[tuple[str, str]]:
    """(key, the whole call) for every write into a reader's browser.

    The key is resolved to the literal it is. A `setItem(WHO, ...)` says nothing
    on its own, and reading only the identifier is how an enumeration goes
    quietly inert: rename the constant's value and every check below passes
    while a different key is written.
    """
    code = without_comments(text)
    found: list[tuple[str, str]] = []
    for m in re.finditer(
        r"(?:localStorage|sessionStorage)\.setItem\(\s*([^,]+?)\s*,([^;]{0,160})",
        code,
    ):
        given, rest = m.group(1).strip(), m.group(2)
        literal = re.fullmatch(r"[\"']([^\"']*)[\"']", given)
        if literal:
            key = literal.group(1)
        else:
            named = re.search(
                rf"\b(?:const|let|var)\s+{re.escape(given)}\s*=\s*[\"']([^\"']+)[\"']",
                code,
            )
            key = named.group(1) if named else f"{where}: unresolved ({given})"
        found.append((key, m.group(0)))
    for m in re.finditer(r"document\.cookie\s*=([^;]{0,160})", code):
        found.append((f"{where}: a cookie", m.group(0)))
    return found


def test_the_resolver_flags_what_it_claims_to_flag():
    """The bite. A scanner green for the wrong reason is the failure this
    repository has hit more than once, so the resolver is shown catching each
    plausible next edit rather than asserted to work.

    The last two are the ones that matter. A constant whose value moved and an
    expression the scanner cannot read are both ways an enumeration passes while
    something else entirely is being written.
    """
    cases = [
        ('localStorage.setItem("controlbun.token", access);', "controlbun.token"),
        ('sessionStorage.setItem("session", JSON.stringify(signed));', "session"),
        ('const K = "controlbun.session";\nlocalStorage.setItem(K, t);',
         "controlbun.session"),
        ('localStorage.setItem(keyFor(user), t);', "unresolved"),
    ]
    for snippet, expected in cases:
        found = storage_writes(snippet)
        assert found, f"the resolver missed {snippet!r}"
        assert expected in found[0][0], f"{snippet!r} resolved to {found[0][0]!r}"

    assert storage_writes('document.cookie = "who=" + handle;')

    # And a comment saying a thing is not written is not the thing being
    # written. The trap `CLAUDE.md` names, one layer out.
    assert not storage_writes("// localStorage.setItem('token', access)")
    assert not storage_writes("/* nothing writes sessionStorage.setItem here */")


def test_nothing_on_the_site_keeps_anything_nobody_accounted_for():
    """A new key is an edit to `MAY_KEEP`, which is a decision somebody made
    rather than a line that arrived."""
    unaccounted = []
    for path in source_files():
        for key, call in storage_writes(path.read_text(), where=str(path.name)):
            if key not in MAY_KEEP:
                unaccounted.append(f"{path.relative_to(ROOT)}: {key!r} in {call!r}")
    assert not unaccounted, (
        "the site keeps something in a reader's browser that nobody accounted "
        "for:\n  " + "\n  ".join(unaccounted)
        + "\n\nAdd it to MAY_KEEP with the reason, or take it out."
    )


def test_no_provider_token_reaches_a_readers_browser():
    """The hard constraint, narrowed on 2026-09-20 and held at the same width.

    **The old property.** No write into browser storage anywhere in the view
    layer could be a token, with the PKCE verifier named as the single
    exemption. That held while the Supabase session died with the tab.

    **Why it stopped being the right one.** The bar read a remembered handle and
    offered **Add artifact** to somebody whose session was gone, and the page
    behind the offer could only ask them to sign in again. Making the offer true
    meant persisting the session, which is a credential, so the old property
    would have had to be deleted to ship the fix. It is narrowed instead.

    **What replaced it.** No Hugging Face provider token reaches storage in any
    spelling, anywhere in the view layer. That is the one that matters: with
    `contribute-repos` it creates and writes repositories in somebody's own
    namespace, and Hugging Face never returns it on a renewal, so keeping it
    buys nothing past its expiry. Which keys may hold a credential at all is the
    test below this one.
    """
    offenders = []
    for path in source_files():
        for key, call in storage_writes(path.read_text(), where=str(path.name)):
            for spelling in re.findall(PROVIDER_CREDENTIAL, key + " " + call, re.I):
                offenders.append(
                    f"{path.relative_to(ROOT)}: {spelling!r} in {call.strip()!r}"
                )
    assert not offenders, (
        "a Hugging Face provider token reaches a reader's browser:\n  "
        + "\n  ".join(offenders)
        + "\n\nThat one can write repositories in somebody's account and "
        "cannot be renewed. It is held in a variable for one upload and "
        "written nowhere."
    )


def test_only_the_two_named_keys_may_hold_a_credential():
    """The other half of the narrowing, and the half that could rot quietly.

    Refusing the provider token by name is not enough on its own: a third key
    holding some other credential would pass that scan. So every key that a
    credential-shaped write lands in has to be one of two, each with its reason
    written down beside it.
    """
    offenders = []
    for path in source_files():
        for key, call in storage_writes(path.read_text(), where=str(path.name)):
            if key in MAY_BE_A_CREDENTIAL:
                continue
            if re.search(CREDENTIAL, key, re.I) or re.search(CREDENTIAL, call, re.I):
                offenders.append(f"{path.relative_to(ROOT)}: {key!r} in {call.strip()!r}")
    assert not offenders, (
        "a credential is kept under a key nobody accounted for:\n  "
        + "\n  ".join(offenders)
        + "\n\nAdd it to MAY_BE_A_CREDENTIAL with the reason, or take it out."
    )


def test_the_session_is_written_in_one_place_and_it_is_the_module_s_record():
    """A page that assembled its own object beside `heldSessionFrom` would pass
    every scan above while writing whatever it liked, which is how the email on
    the Supabase user row would arrive in a browser."""
    page = SIGNED_IN.read_text()
    written = re.findall(r"localStorage\.setItem\(\s*([A-Za-z_$][\w$]*)", page)
    assert written == ["HELD"], written
    assert re.search(rf'HELD\s*=\s*"{re.escape(SESSION_KEY)}"', page), (
        "the key the session lives under moved, and the bar reads the old one"
    )
    assert re.search(
        r"function keep\(held\) \{\n\s*localStorage\.setItem\(HELD, JSON\.stringify\(held\)\);",
        page,
    ), "the page no longer writes through one function"
    # And every value handed to that function is the module's projection.
    for call in re.findall(r"\bkeep\(([^\n]*)", page):
        if call.startswith("held)"):
            continue  # the definition itself
        assert call.startswith("heldSessionFrom("), (
            f"keep({call.strip()}) writes something the module did not build"
        )


def test_the_verifier_is_still_removed_the_moment_it_is_used():
    """The one credential-shaped thing that is written, held to the reason it
    is allowed. Duplicated from `tests/test_signed_in_page.py` on purpose: the
    exemption above is stated here, so the condition on it is checked here."""
    source = SIGNED_IN.read_text()
    assert "sessionStorage.removeItem(VERIFIER)" in source


# --------------------------------------------------------------------------- #
# 2. The bar's state comes from the browser and never from the page.


def test_the_bar_takes_no_props_and_imports_nothing():
    """The structural half, checked where it would be broken first.

    A prop is how this gets "smarter": pass the page's author in, and the bar
    can greet somebody. Frontmatter with nothing in it is the property, and it
    is worth asserting precisely because it looks like an absence of work.
    """
    front = re.search(r"^---\n(.*?)\n---", NAV.read_text(), re.S)
    assert front, "SiteNav has no frontmatter fence, so this checks nothing"
    body = without_comments(front.group(1)).strip()
    assert body == "", (
        f"SiteNav's frontmatter computes something: {body!r}. Everything the "
        "bar knows about a reader comes from that reader's browser, and a "
        "value arriving at build time is a value the page asserted."
    )
    # Read with the prose taken out, because the block above the account markup
    # explains that there is no import and a substring scan reads the
    # explanation as the thing. The trap `CLAUDE.md` names, one layer out.
    code = without_comments(NAV.read_text())
    for reaching in ("Astro.props", "interface Props", "import "):
        assert reaching not in code, (
            f"SiteNav reaches {reaching!r}, which is a fact from outside the "
            "reader's own browser deciding what the bar says about them"
        )


def test_the_account_markup_holds_no_build_time_expression():
    """The other half. Frontmatter can be empty while the markup still
    interpolates, and `data-who={author}` is one character from being written.
    """
    markup = re.sub(r"^---\n.*?\n---", "", NAV.read_text(), flags=re.S)
    markup = re.sub(r"<script.*?</script>", "", markup, flags=re.S)
    markup = re.sub(r"\{/\*.*?\*/\}", "", markup, flags=re.S)
    leftover = re.findall(r"\{[^}]*\}", markup)
    assert not leftover, (
        f"the bar interpolates a build-time value: {leftover}. What is shown "
        "has to come from the reader's browser, and an expression here is the "
        "page deciding who somebody is."
    )


def test_the_state_is_read_from_one_key_and_from_nothing_else():
    """Where the bar's answer comes from, named.

    Both scripts read the same key and neither reads anything about the page.
    `querySelector` reaching for a byline, a `data-author` attribute or the
    corpus JSON would each be the page asserting a person, and each is the edit
    that would look like an improvement.
    """
    for path in (NAV, HEAD):
        code = without_comments(path.read_text())
        keys = re.findall(
            r"(?:localStorage|sessionStorage)\.getItem\(\s*(?:[\"']([^\"']+)[\"']|([A-Za-z_$][\w$]*))",
            code,
        )
        resolved = set()
        for literal, named in keys:
            if literal:
                resolved.add(literal)
            else:
                found = re.search(
                    rf"\b(?:const|let|var)\s+{re.escape(named)}\s*=\s*[\"']([^\"']+)[\"']",
                    code,
                )
                resolved.add(found.group(1) if found else f"unresolved {named}")
        assert resolved <= {"theme", SESSION_KEY}, (
            f"{path.name} reads {sorted(resolved)}, which is more than the "
            "theme and the one key the bar's state comes from"
        )
        for asserting in ("data-author", "data-owner", "controlbun.json",
                          "byline", ".author"):
            assert asserting not in code, (
                f"{path.name} reads {asserting!r} off the page, so the bar can "
                "say a reader is whoever they happen to be reading about"
            )


def test_the_choice_is_made_before_first_paint():
    """Inline, in the head, and not a module. Same requirement as the theme and
    for the same reason: a decision taken after paint is a frame of the wrong
    affordance, which is worse here than it is for a color."""
    head = HEAD.read_text()
    script = re.search(r"<script([^>]*)>(.*?)</script>", head, re.S)
    assert script, "the head ships no script, so nothing decides before paint"
    assert "is:inline" in script.group(1), (
        "the head script is bundled, so it runs after first paint"
    )
    assert f'localStorage.getItem("{SESSION_KEY}")' in script.group(2), (
        "the head no longer reads the key, so the bar decides after paint"
    )
    assert "document.documentElement.dataset.who" in script.group(2)
    # And the decision is conditioned on the record being able to renew. A
    # handle alone is the state that made the bar over-promise: it named
    # somebody and led to a page that could only ask them to sign in again.
    assert "held.refresh_token" in script.group(2), (
        "the head offers Add artifact off a handle rather than off a session "
        "that can still be renewed, which is the gap this key replaced"
    )
    # The old key is deleted rather than left in browsers that still hold one.
    assert f'localStorage.removeItem("{RETIRED_KEY}")' in script.group(2), (
        "a browser carrying the retired handle key keeps it forever, since "
        "nothing reads it now"
    )

    # And CSS is what acts on it, rather than a second decision in script.
    css = CSS.read_text()
    assert ":root:not([data-who]) .sitenav .whenin" in css
    assert ":root[data-who] .sitenav .whenout" in css


def test_the_built_pages_decide_in_the_head_too():
    """The half that is about rendered output. Skips unbuilt, which is why the
    checks above read the source."""
    if not DIST.exists():
        pytest.skip("site not built; run `make site`")
    pages = sorted(DIST.rglob("index.html"))
    assert pages, "no built pages"
    for path in pages:
        html = path.read_text()
        needle = f'localStorage.getItem("{SESSION_KEY}")'
        assert needle in html, (
            f"{path.relative_to(DIST)} never reads the key, so the bar here "
            "shows Sign in to somebody who signed in on the previous page"
        )
        assert html.index(needle) < html.index("<body"), (
            f"{path.relative_to(DIST)} decides after the head, which is a "
            "frame of the wrong affordance"
        )


# --------------------------------------------------------------------------- #
# 3. What the bar offers, and that neither offer is a dead end.


def nav_markup() -> str:
    markup = re.sub(r"^---\n.*?\n---", "", NAV.read_text(), flags=re.S)
    return re.sub(r"<script.*?</script>", "", markup, flags=re.S)


def test_both_ways_in_ship_and_they_are_named_the_two_names():
    markup = nav_markup()
    assert re.search(r'<a href="/sign-in/">\s*Sign in\s*</a>', markup), (
        "the bar does not offer Sign in"
    )
    assert re.search(r'<a href="/signed-in/">\s*Add artifact\s*</a>', markup), (
        "the bar does not offer Add artifact"
    )
    assert re.search(r'id="signout"[^>]*>\s*Sign out', markup), (
        "there is persisted state and no way to clear it"
    )
    # A dead href renders as a working control and is worse than no control.
    for href in re.findall(r'href="([^"]*)"', markup):
        assert href.strip() not in ("", "#"), f"{href!r} is a placeholder link"


def test_add_artifact_lands_where_a_submission_is_actually_sent():
    """The button points at a surface that takes one, checked against that
    page rather than against a path somebody believed in."""
    assert 'href="/signed-in/"' in nav_markup()
    page = SIGNED_IN.read_text()
    assert 'id="send-record"' in page, (
        "the page Add artifact points at no longer has the button that sends"
    )
    assert 'id="build-record"' in page


def test_a_restored_session_says_what_came_back_and_what_did_not():
    """The note this replaced said no token survives a reload, which is now
    false, and it appeared on the dead end the change removed.

    What a reader arriving tomorrow gets instead is a session that works and one
    thing that did not come back with it: the reading of what Hugging Face says
    about them, which needs a provider token this browser keeps nowhere. Saying
    that is the point. A page that silently showed yesterday's membership would
    be the "confirmed on a date" rule broken at the one place nothing re-checks.
    """
    page = SIGNED_IN.read_text()
    assert 'id="remembered"' in page, "the page has nowhere to say what came back"
    said = re.search(r'say\(\s*\n?\s*"remembered",(.*?)\n\s*\);', page, re.S)
    assert said, "nothing fills the restored note, so it never appears"
    text = said.group(1).lower()
    assert "kept the session" in text
    assert "did not come back" in text, (
        "the note has to name the thing a restored session does not carry"
    )
    assert "hugging face session" in text, (
        "the note has to say what signing out does not do, in the place "
        "somebody is reading about the session being kept"
    )
    # And the button that starts a fresh authorization is still on the page.
    assert 'id="begin"' in page


def test_a_session_that_cannot_be_renewed_is_a_state_with_its_own_words():
    """Not an error and not silence. A refused renewal is what a session signed
    out elsewhere looks like, and the reader did nothing wrong, so it gets a
    sentence and the button that fixes it rather than a failure banner."""
    page = SIGNED_IN.read_text()
    assert 'id="stale"' in page, "there is nowhere to say a renewal was refused"
    said = re.search(r"function staleSaid\(problem\) \{(.*?)\n  \}", page, re.S)
    assert said, "nothing builds the sentence, so the element never fills"
    text = said.group(1).lower()
    assert "could not be renewed" in text
    assert "not a failure of anything you typed" in text
    assert "signing in again" in text
    # The endpoint's own words are in it, so the reader is not told less than
    # this page knows.
    assert "problem.message" in said.group(1)
    # And the session is deleted rather than left to fail again on every press.
    assert re.search(r"forget\(\);\s*\n\s*show\(\"working\", false\);", page), (
        "a session the identity service refuses is kept, so the bar goes on "
        "offering Add artifact off a record that cannot renew"
    )


def test_signing_out_deletes_the_session_and_says_what_it_did_not_do():
    """Deleting the key is still the whole of it, and the key is bigger now.

    This asserted that the receipt says it forgot a handle, which was the whole
    truth while a handle was all there was. It deletes a session now, so the
    receipt has to say that, and it has to say the two things it still does not
    do: it sends nothing, so the session is not revoked at the identity service,
    and the account at Hugging Face is that provider's and untouched.

    No request, on purpose and at a cost. Revoking would put the identity
    endpoint and the publishable key in the bar, which is on every page, and
    `tests/test_signed_in_page.py` holds that endpoint to the one page with
    business for it.
    """
    code = without_comments(NAV.read_text())
    assert f'const HELD = "{SESSION_KEY}";' in code
    assert "localStorage.removeItem(HELD)" in code
    for reaching in ("fetch(", "XMLHttpRequest", "sendBeacon", "location.assign"):
        assert reaching not in code, (
            f"signing out reaches {reaching!r}. Revoking from here would put "
            "the identity endpoint on every page on the site."
        )
    said = re.search(r'id="nav-said"[^>]*>(.*?)</p>', NAV.read_text(), re.S)
    assert said, "there is no receipt for a press"
    words = " ".join(said.group(1).split()).lower()
    assert "deleted the session and the handle from this browser" in words
    assert "not revoked at the identity service" in words, (
        "the receipt claims more than deleting a key does"
    )
    assert "hugging face session is untouched" in words


def test_the_bar_says_nothing_that_claims_a_standing():
    """Trip-wire vocabulary, on the one piece of copy that now sits on every
    page. Signing in confers nothing, so a word implying it does is the word
    that turns a handle into a status."""
    words = " ".join(re.sub(r"<[^>]+>", " ", nav_markup()).split()).lower()
    for claimed in ("verified", "approved", "authorized", "authorised",
                    "certified", "official", "trusted", "member since"):
        assert claimed not in words, f"the bar says {claimed!r}"


def test_holding_a_session_is_never_a_condition_on_reaching_anything():
    """The premise, at the one place this change could quietly break it.

    Nothing is hidden behind being signed in. `/sign-in/` is offered to a reader
    who is not, it links to `/signed-in/`, and that page is where a submission is
    sent from. What the key changes is which door the bar names first.
    """
    markup = nav_markup()
    # The signed-out affordance leads somewhere that leads on.
    assert 'href="/sign-in/"' in markup
    assert 'href="/signed-in/"' in (SRC / "pages" / "sign-in.astro").read_text()
    # And the pages themselves are not gated on the key.
    for path in (SRC / "pages" / "sign-in.astro", SIGNED_IN):
        code = without_comments(path.read_text())
        assert not re.search(rf"if\s*\(\s*!\s*[^)]*{re.escape(SESSION_KEY)}", code), (
            f"{path.name} refuses somebody for not carrying the key"
        )


# --------------------------------------------------------------------------- #
# 4. What is kept, run against the module that builds it.


def run_js(body: str):
    """Evaluate `body` against the real module, same shape as the page test."""
    if not NODE:
        pytest.skip("node not on PATH")
    script = (
        f"import * as h from {json.dumps(HANDSHAKE.as_uri())};\n"
        "const out = await (async () => {\n" + body + "\n})();\n"
        "process.stdout.write(JSON.stringify(out ?? null));\n"
    )
    done = subprocess.run(
        [NODE, "--input-type=module", "-e", script], capture_output=True, text=True,
    )
    if done.returncode != 0:
        raise AssertionError(done.stderr.strip())
    return json.loads(done.stdout or "null")


def test_node_is_the_thing_that_runs_this_module():
    """A skipped guard is a guard that is not there, and astro needs node to
    build at all."""
    assert NODE, "node is not on PATH, and the site cannot be built without it"


# A token endpoint answer, with every field that must not travel labeled as what
# it is. No number here is a measurement and no handle here is anybody's.
A_SESSION = (
    '{access_token: "supabase-access", refresh_token: "supabase-refresh",'
    ' expires_at: 2000000000, token_type: "bearer",'
    ' provider_token: "hugging-face-must-not-travel",'
    ' provider_refresh_token: "nor-must-this",'
    ' user: {id: "account-uuid", email: "nor-must-this-at-all",'
    '        user_metadata: {sub: "opaque-subject", preferred_username: "someone",'
    '                        avatar_url: "nor-this-either"}}}'
)


def test_what_is_kept_is_the_session_and_the_three_identity_fields():
    held = run_js(
        f'return h.heldSessionFrom({A_SESSION}, {{provider: "custom:huggingface",'
        ' recordedAt: "2026-09-20T00:00:00Z"});'
    )
    assert set(held) == {
        "shape", "recorded_at", "provider", "access_token", "refresh_token",
        "expires_at", "user",
    }
    assert held["access_token"] == "supabase-access"
    assert held["refresh_token"] == "supabase-refresh"
    assert held["expires_at"] == 2000000000
    assert held["recorded_at"] == "2026-09-20T00:00:00Z"
    # Shaped the way `pendingRowFrom` reads a session, so that function keeps
    # its one parameter and no parameter a token can arrive in.
    assert set(held["user"]) == {"id", "user_metadata"}
    assert set(held["user"]["user_metadata"]) == {"sub", "preferred_username"}
    assert held["user"]["user_metadata"]["preferred_username"] == "someone"


def test_the_provider_token_cannot_reach_what_is_kept():
    """The rule the whole split turns on, checked by key and by value.

    The projection names its fields, so a token endpoint that grows a claim
    cannot push one into a browser. A projection that renamed a field while
    still copying it would pass a scan of the keys, which is why the planted
    strings are checked too. The email is in here for the same reason: it exists
    in the identity service's own user row and in no file, page or table of this
    project's, and spreading `user` would have put it in every reader's browser.
    """
    held = run_js(
        f'return h.heldSessionFrom({A_SESSION}, {{provider: "custom:huggingface"}});'
    )
    flat = json.dumps(held).lower()
    for word in ("provider_token", "provider_refresh_token", "email",
                 "avatar", "secret", "password", "bearer", "apikey"):
        assert word not in flat, f"what is kept carried {word!r}"
    for planted in ("hugging-face-must-not-travel", "nor-must-this",
                    "nor-must-this-at-all", "nor-this-either"):
        assert planted not in flat, f"what is kept carried {planted!r}"


def test_a_session_with_no_refresh_token_is_refused_rather_than_half_kept():
    """A record that names somebody and cannot renew is exactly the state the
    bar used to offer a way in on. Refused here so it cannot be written."""
    said = run_js(
        "try { h.heldSessionFrom({access_token: 'a'}); return null; }\n"
        "catch (problem) { return problem.message; }"
    )
    assert "no refresh token" in said
    assert "nothing was written to this browser" in said
    assert run_js(
        "try { h.heldSessionFrom({refresh_token: 'r'}); return null; }\n"
        "catch (problem) { return problem.message; }"
    ).startswith("the identity service answered with no access token")


def test_an_expiry_nobody_stated_counts_as_spent():
    """Renewing a token with time left costs one request. Using one without
    costs a person the press they already made, and no row is written."""
    spent = run_js(
        "return {unknown: h.accessSpent({}),"
        " past: h.accessSpent({expires_at: 1000}, {now: 2000000}),"
        " soon: h.accessSpent({expires_at: 1000}, {now: 950000}),"
        " later: h.accessSpent({expires_at: 100000}, {now: 1000})};"
    )
    assert spent["unknown"] is True
    assert spent["past"] is True
    # Inside the margin counts as spent: a token that expires during the
    # request is a request that fails after somebody pressed send.
    assert spent["soon"] is True
    assert spent["later"] is False


def test_the_signer_a_restored_session_submits_under_carries_no_token():
    """`submissionFrom` reads three fields off whatever it is handed, and on a
    restored session that is the held record. Handing it the record itself
    would put a token one property access away from the submission."""
    signer = run_js(
        f'return h.signerFrom(h.heldSessionFrom({A_SESSION}, '
        '{provider: "custom:huggingface"}));'
    )
    assert set(signer) == {"provider", "sub", "preferred_username"}
    assert signer["preferred_username"] == "someone"
    assert "token" not in json.dumps(signer).lower()


def test_no_handle_means_the_bar_has_nothing_to_show():
    """A provider that named no handle is a state, not a failure. The session
    is still held, because it can still send a row, and the bar shows Sign in
    because there is no name to put in it.

    Held at both ends: the projection records the absence rather than inventing
    a name, and the head script offers Add artifact only when a handle is there.
    """
    held = run_js(
        'return h.heldSessionFrom({access_token: "a", refresh_token: "r",'
        ' user: {id: "account-uuid", user_metadata: {sub: "s"}}});'
    )
    assert held["user"]["user_metadata"]["preferred_username"] is None
    assert held["refresh_token"] == "r"
    assert run_js(
        'return h.signerFrom(null).preferred_username;'
    ) is None
    head = without_comments(HEAD.read_text())
    assert "said.preferred_username" in head, (
        "the head no longer conditions the bar on a handle being there"
    )


# --------------------------------------------------------------------------- #
# 5. What a reader is told, on the page that does the writing.


def test_the_page_says_which_credential_it_keeps_and_which_it_never_writes():
    """It keeps a credential now, so it says which one and says the other is
    kept nowhere.

    This asserted "no token is kept", which was the whole truth until the
    session persisted and is now the sentence a reader would be most misled by.
    The page's own standard: a sentence that was true and stopped being true is
    worse than one that was never true, because it was checked once.
    """
    source = SIGNED_IN.read_text()
    words = " ".join(re.sub(r"<[^>]+>", " ", source).split()).lower()
    assert "kept in this browser" in words
    assert "kept nowhere at all" in words, (
        "the page does not say the Hugging Face token is kept nowhere, which "
        "is the half of the split a reader has most at stake in"
    )
    assert "no token is kept" not in words, (
        "the page still says no token is kept, and one is"
    )
    assert "deletes the session and the handle from this browser" in words
    assert "does not end your hugging face session" in words


def test_the_page_no_longer_says_the_submission_is_the_only_thing_it_writes():
    """It did say that, correctly, until the handle was kept."""
    words = " ".join(re.sub(r"<[^>]+>", " ", SIGNED_IN.read_text()).split()).lower()
    assert "the one thing it writes is the submission you send" not in words, (
        "the page still claims the submission is the only thing it writes"
    )


def test_the_page_no_longer_says_a_session_ends_with_the_tab():
    """Three sentences said so and every one of them was checked once."""
    words = " ".join(re.sub(r"<[^>]+>", " ", SIGNED_IN.read_text()).split()).lower()
    for gone in ("the session lives in this tab and closing it ends it",
                 "no token survives a reload",
                 "keeping a handle is not holding a session"):
        assert gone not in words, f"the page still says {gone!r}"


def test_the_built_page_says_it_too():
    """The half about rendered output, which is where copy finally binds."""
    built = DIST / "signed-in" / "index.html"
    if not built.exists():
        pytest.skip("site not built; run `make site`")
    html = re.sub(r"<(script|style).*?</\1>", "", built.read_text(), flags=re.S)
    words = " ".join(re.sub(r"<[^>]+>", " ", html).split()).lower()
    assert "kept in this browser" in words
    assert "kept nowhere at all" in words
    assert "deletes the session and the handle from this browser" in words
