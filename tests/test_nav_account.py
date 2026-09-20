"""The bar at the top: two ways in, one shown, and nothing a token can reach.

Premise, restated because a premise stated in one file gets violated in every
other one: **plurality is the product, the registry never designates, and
consumers pin visibly.** Remembering a handle changes which door the bar names
first and changes nothing about who may open it. `/sign-in/` explains, it links
to `/signed-in/`, and `/signed-in/` is where a submission is sent from. All
three are reachable by somebody who has never signed in, and nothing here is a
condition on publishing.

**The two properties this file exists for**, both of which would be satisfied by
prose and neither of which would then mean anything:

1. **Nothing on this site writes a token to browser storage.** Held across every
   file in `astro/src` rather than per page, by resolving each written key to
   the literal it is and refusing one nobody accounted for.
   `tests/test_signed_in_page.py` holds the same property one level down, on the
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
down is the string a counterexample needs to be a counterexample.
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
# fails this file loudly rather than making every check below inert.
WHO_KEY = "controlbun.who"


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
# 1. Nothing writes a token to browser storage.


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
    WHO_KEY: "three display facts about who signed in, the handle, the subject "
             "and when they were read, so the bar can offer Add artifact on a "
             "page the return leg did not render. Not a session: the token it "
             "arrived with is already gone.",
}

# Words that would mean the thing being kept is a credential rather than a
# display fact, matched against the whole call rather than against the key.
CREDENTIAL = r"token|secret|password|credential|bearer|apikey|api_key|verifier"


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


def test_no_write_into_a_browser_is_a_token():
    """The hard constraint, held at the widest place it can be held.

    Not a count and not a page: every call in the view layer, checked on what it
    names. A token in storage survives the tab, the reload and whatever else
    reads that origin, and the whole reason the session lives in one variable is
    that it does not.
    """
    offenders = []
    for path in source_files():
        for key, call in storage_writes(path.read_text(), where=str(path.name)):
            if re.search(CREDENTIAL, key, re.I) and key != "controlbun.pkce":
                offenders.append(f"{path.relative_to(ROOT)}: key {key!r}")
            # The verifier is named, and it is the one thing on this list that
            # is allowed to be one. It is not a credential without the
            # authorization code, and it is removed the moment it is used.
            if key == "controlbun.pkce":
                continue
            if re.search(CREDENTIAL, call, re.I):
                offenders.append(f"{path.relative_to(ROOT)}: {call.strip()!r}")
    assert not offenders, (
        "a token reaches a reader's browser:\n  " + "\n  ".join(offenders)
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
        assert resolved <= {"theme", WHO_KEY}, (
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
    assert f'localStorage.getItem("{WHO_KEY}")' in script.group(2), (
        "the head no longer reads the key, so the bar decides after paint"
    )
    assert "document.documentElement.dataset.who" in script.group(2)

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
        needle = f'localStorage.getItem("{WHO_KEY}")'
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


def test_arriving_with_a_remembered_handle_and_no_session_says_what_it_needs():
    """The dead end this would otherwise be.

    A reader presses Add artifact a day later. The bar remembers a handle, the
    tab holds no token, and the page can do nothing until they authorize again.
    Showing them a second Sign in button with no account of why reads as the
    first press having failed.
    """
    page = SIGNED_IN.read_text()
    assert 'id="remembered"' in page, "the page has nowhere to say what it needs"
    said = re.search(r'say\(\s*\n?\s*"remembered",(.*?)\n\s*\);', page, re.S)
    assert said, "nothing fills the remembered note, so it never appears"
    text = said.group(1).lower()
    assert "not a session" in text
    assert "fresh sign-in" in text or "sign in again" in text
    assert "hugging face session" in text, (
        "the note has to say what signing out does not do, in the place "
        "somebody is reading about the handle being remembered"
    )
    # And the button that starts a fresh authorization is still on the page.
    assert 'id="begin"' in page


def test_signing_out_is_the_key_being_deleted_and_nothing_else():
    """No request, no revocation, no claim about the provider. Deleting the key
    is the whole of it, and the receipt says the half a reader would otherwise
    get wrong."""
    code = without_comments(NAV.read_text())
    assert f'const WHO = "{WHO_KEY}";' in code
    assert "localStorage.removeItem(WHO)" in code
    for reaching in ("fetch(", "XMLHttpRequest", "sendBeacon", "location.assign"):
        assert reaching not in code, (
            f"signing out reaches {reaching!r}. It has nothing to tell anybody: "
            "the token died with the tab and the account is the provider's."
        )
    said = re.search(r'id="nav-said"[^>]*>(.*?)</p>', NAV.read_text(), re.S)
    assert said, "there is no receipt for a press"
    words = " ".join(said.group(1).split()).lower()
    assert "forgot the handle in this browser" in words
    assert "did not end your hugging face session" in words


def test_the_bar_says_nothing_that_claims_a_standing():
    """Trip-wire vocabulary, on the one piece of copy that now sits on every
    page. Signing in confers nothing, so a word implying it does is the word
    that turns a handle into a status."""
    words = " ".join(re.sub(r"<[^>]+>", " ", nav_markup()).split()).lower()
    for claimed in ("verified", "approved", "authorized", "authorised",
                    "certified", "official", "trusted", "member since"):
        assert claimed not in words, f"the bar says {claimed!r}"


def test_remembering_a_handle_is_never_a_condition_on_reaching_anything():
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
        assert not re.search(rf"if\s*\(\s*!\s*[^)]*{re.escape(WHO_KEY)}", code), (
            f"{path.name} refuses somebody for not carrying the key"
        )


# --------------------------------------------------------------------------- #
# 4. What is remembered, run against the module that builds it.


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


def test_what_is_remembered_is_three_display_facts_and_nothing_else():
    who = run_js(
        'return h.whoFrom({sub: "opaque-subject", preferred_username: "someone",'
        ' captured_at: "2026-09-20T00:00:00Z"});'
    )
    assert set(who) == {"shape", "handle", "subject", "recorded_at"}
    assert who["handle"] == "someone"
    assert who["subject"] == "opaque-subject"
    assert who["recorded_at"] == "2026-09-20T00:00:00Z"


def test_no_key_that_reads_like_a_credential_can_reach_what_is_remembered():
    """The projection names its fields, so a capture that grows a token cannot
    push one into the browser. Same check `tests/test_signed_in_page.py` runs
    against the capture, on the record that outlives the tab."""
    who = run_js(
        'return h.whoFrom({sub: "s", preferred_username: "someone",'
        ' access_token: "should-not-travel", provider_token: "nor-this",'
        ' refresh_token: "nor-this-either", email: "nor-this-at-all"});'
    )
    flat = json.dumps(who).lower()
    for word in ("token", "secret", "password", "credential", "bearer",
                 "verifier", "apikey", "email"):
        assert word not in flat, f"what is remembered carried {word!r}"
    # And by value as well as by key name, because a projection that renamed a
    # field while still copying it would pass the scan above.
    for planted in ("should-not-travel", "nor-this", "nor-this-either",
                    "nor-this-at-all"):
        assert planted not in flat, f"what is remembered carried {planted!r}"


def test_no_handle_means_nothing_is_remembered():
    """A provider that named no handle is a state, not a failure. The bar has
    nothing to show, so nothing is written and the reader sees Sign in."""
    assert run_js('return h.whoFrom({sub: "s", preferred_username: null});') is None
    assert run_js("return h.whoFrom(null);") is None


def test_the_page_writes_exactly_what_the_module_built():
    """The seam. A page that assembled its own object beside the function would
    pass every check above while writing whatever it liked."""
    source = SIGNED_IN.read_text()
    assert re.search(r"const who = whoFrom\(entry\);", source)
    assert re.search(
        r"localStorage\.setItem\(WHO,\s*JSON\.stringify\(who\)\);", source
    ), "the page no longer writes the module's record, so the rule is elsewhere"


# --------------------------------------------------------------------------- #
# 5. What a reader is told, on the page that does the writing.


def test_the_page_says_what_it_keeps_in_the_browser():
    """It writes to somebody's browser now, so it says so. The page's own
    standard: a sentence that was true and stopped being true is worse than one
    that was never true, because it was checked once."""
    source = SIGNED_IN.read_text()
    words = " ".join(re.sub(r"<[^>]+>", " ", source).split()).lower()
    assert "kept in this browser" in words
    assert "no token is kept" in words
    assert "forgets the handle in this browser" in words
    assert "does not end your hugging face session" in words


def test_the_page_no_longer_says_the_submission_is_the_only_thing_it_writes():
    """It did say that, correctly, until the handle was kept."""
    words = " ".join(re.sub(r"<[^>]+>", " ", SIGNED_IN.read_text()).split()).lower()
    assert "the one thing it writes is the submission you send" not in words, (
        "the page still claims the submission is the only thing it writes"
    )


def test_the_built_page_says_it_too():
    """The half about rendered output, which is where copy finally binds."""
    built = DIST / "signed-in" / "index.html"
    if not built.exists():
        pytest.skip("site not built; run `make site`")
    html = re.sub(r"<(script|style).*?</\1>", "", built.read_text(), flags=re.S)
    words = " ".join(re.sub(r"<[^>]+>", " ", html).split()).lower()
    assert "kept in this browser" in words
    assert "forgets the handle in this browser" in words
