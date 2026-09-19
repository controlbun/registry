"""Sign in with Hugging Face on 127.0.0.1, and date what the memberships said.

Premise, restated because a premise stated in one document gets violated in every
other one: **plurality is the product; the registry never designates, consumers
pin, visibly.** Nothing here ranks, scores, approves or filters anybody. Signing
in produces one thing: a dated record of what Hugging Face said about an account
at one moment. It confers no standing and gates no namespace, and signing in
writes nothing into the corpus.

**Turning a capture into a claim is a separate command run on purpose.**
`artifacts/claim.py record` reads a capture and writes `namespace_claim` and
`namespace_membership_observation` rows through a tracked record, which is what
keeps a subject id out of a file somebody types into. Nothing here calls it and
nothing here knows the namespace being claimed: a capture says who signed in and
says nothing about what they are claiming.

**This is not a sign-in on the published site, and the difference is structural
rather than a matter of naming.** It listens on 127.0.0.1 and on nothing else.
`tests/test_intake.py` fails the build if `astro/dist` ever ships a form, a POST
target, a scripted request or a loopback address, and that guard is untouched by
this file: nothing here is imported by the view layer, nothing here is built into
the site, and `tests/test_signin.py` fails if that changes. See `SIGNIN.md` for
the argument, which is that a sign-in button is the front door of a write path
and the dual-use policy that a write path needs does not exist yet.

**Memberships are captured and dated, not stored.** A real sign-in through the
configured Supabase provider lands `preferred_username` and `sub` in
`raw_user_meta_data` and lands `orgs` as null, because `orgs` is a Hugging Face
claim rather than a standard OIDC one and does not survive the trip. That drop is
the good outcome. People join and leave organizations, so a membership read once
and cached forever is a stale fact wearing a badge. This calls the userinfo
endpoint while the token is live, records what `orgs` said **and when**, and
stops. Re-checking means signing in again. A page that says "member of
`controlbun`, confirmed 2026-09-19" is honest; one that says the membership is
verified is not, because nothing re-reads it.

**Nothing here writes, logs or renders a token.** The Supabase session and the
Hugging Face `provider_token` exist in one local variable for the length of one
userinfo call and reach no file, no page and no log line. `log_message` prints
the route and drops the query string, which is where the authorization code
arrives. `tests/test_signin.py` scans this module for both.

**Bound to `sub`, never to `preferred_username`.** Hugging Face handles are
renameable, so a record bound to the handle either breaks on a rename or follows
the handle to whoever takes it next. The handle is recorded too, because it is
what a reader recognizes, but `sub` is what identifies.

## The flow, every hop verified on 2026-09-19 against the live project

    browser  ->  {SUPABASE_URL}/auth/v1/authorize?provider=custom:huggingface
                 &redirect_to=http://127.0.0.1:8931/callback
                 &code_challenge=...&code_challenge_method=s256
             ->  302 to huggingface.co/oauth/authorize, Supabase's own client id,
                 response_type=code, code_challenge_method=S256
             ->  the person approves
             ->  Supabase's callback, then 302 back to the loopback address
                 carrying ?code=
    here     ->  POST {SUPABASE_URL}/auth/v1/token?grant_type=pkce
                 {auth_code, code_verifier}  -> a session
             ->  GET huggingface.co/oauth/userinfo with the provider token
             ->  one line appended to `memberships.jsonl`

`provider=huggingface` is rejected with "Provider huggingface could not be
found"; the provider string is `custom:huggingface`, which is what a custom OIDC
provider is addressed as. It is an argument here rather than a constant, and
nothing checks it against a list of names this file happens to know.

The PKCE parameters are ours and are not decoration. Supabase validates them:
a bad method answers "Invalid code_challenge_method", a short challenge answers
"code challenge has to be between 43 and 128 characters", and a method with no
challenge answers "PKCE flow requires code_challenge_method and code_challenge".
Supplying them puts the return leg in the query string as `?code=`, which a
server reads. Omitting them puts it in a fragment, which a server never sees and
only JavaScript can reach. So this tool ships no JavaScript at all, which is also
why it can carry no scripted write surface to leak.

## What it needs before it runs

    HF_OAUTH_CLIENT_ID, HF_OAUTH_CLIENT_SECRET   registered app, held by Supabase
    SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY       read from `.env`, never printed

The loopback callback has to be in the project's Redirect URLs allowlist or
Supabase sends the browser to the site URL instead and this tool sees nothing.
That is why the port is fixed rather than asked of the OS the way the intake
tool asks: an allowlist entry cannot follow a port that changes every run. The
exact line to allowlist is printed on startup.

    .venv/bin/python artifacts/signin.py serve
    .venv/bin/python artifacts/signin.py show
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# Loopback, and not a default. There is no flag that changes this, for the reason
# `artifacts/intake.py` gives at the same line: a flag would be the argument in
# the docstring undone in one character.
HOST = "127.0.0.1"

# Fixed, unlike the intake tool's, because a redirect allowlist is a list of
# literal URLs and a port the OS picks per run cannot be on it. Changeable with
# `--port` for somebody whose 8931 is taken, who then changes the allowlist too.
PORT = 8931

CALLBACK_PATH = "/callback"

# Addressed rather than enumerated. A custom OIDC provider in Supabase is named
# `custom:<name>`, and this is the one that is configured; it is an argument so a
# second provider is a different string rather than a change to this file, and
# nothing anywhere compares it against a set of names.
PROVIDER = "custom:huggingface"

# Fetched rather than remembered. Every endpoint this talks to at the identity
# provider comes out of the provider's own discovery document at the moment of
# the capture, and the document's `issuer` and `userinfo_endpoint` are written
# into the record, so the evidence says where it came from.
DISCOVERY = "https://huggingface.co/.well-known/openid-configuration"

RECORD = HERE / "memberships.jsonl"

# The capture shape, versioned and namespaced, because whatever reads this file
# needs to know which shape it is reading and the shape will change.
SHAPE = "controlbun.registry/membership-capture@1"

TIMEOUT = 30


class Refused(ValueError):
    """Something this tool will not do, with the reason already in the message.

    One class for every refusal, because the reader is the operator with a
    browser open rather than somebody debugging this module, and a sentence they
    can act on is the entire product of the error path.
    """


# --------------------------------------------------------------------------- #
# Configuration, read from a file that is not in the repository.


def read_env(path: Path | None = None) -> dict[str, str]:
    """`KEY=value` lines from `.env`. Absent is a refusal that names the file.

    `.env` was gitignored before the first file in this repository existed and
    nothing here puts any of it on stdout, in a page or in the record.
    """
    path = path or (ROOT / ".env")
    if not path.exists():
        raise Refused(
            f"no {path} to read. This needs SUPABASE_URL and "
            "SUPABASE_PUBLISHABLE_KEY, and the Supabase project needs the "
            "Hugging Face provider configured against HF_OAUTH_CLIENT_ID and "
            "HF_OAUTH_CLIENT_SECRET. None of those belong in a tracked file."
        )
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def config(env: dict[str, str]) -> tuple[str, str]:
    """The project URL and the publishable key, or a refusal naming what is gone.

    The publishable key is the one a browser is given, so it is not a secret in
    the sense the client secret is. It is still never printed, because a habit
    that distinguishes which of two keys may be echoed is a habit that echoes
    the wrong one eventually.
    """
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY")
               if not env.get(k)]
    if missing:
        raise Refused(f"{', '.join(missing)} not set in .env")
    return env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_PUBLISHABLE_KEY"]


# --------------------------------------------------------------------------- #
# The durable record. Same two functions as the intake tool's, same reasons.


# `path=None` rather than `path=RECORD`, because a default argument binds at
# definition and the module constant is what a test repoints. The version with
# the constant in the signature read better and quietly wrote to the real file
# from a temp tree.
def read_record(path: Path | None = None) -> list[dict]:
    """Every capture, oldest first. Absent is empty, not an error."""
    path = path or RECORD
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


def append_record(entry: dict, path: Path | None = None) -> None:
    """Append one capture. Never rewrites, never reorders, never deletes.

    A capture is a statement about one moment. Editing it would be editing what
    was observed rather than observing again, and observing again is a second
    line, which is the whole point of dating them.
    """
    path = path or RECORD
    with path.open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# The capture itself, which is a pure function of what userinfo said.


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def capture_from(userinfo: dict, *, provider: str, issuer: str,
                 endpoint: str, captured_at: str | None = None) -> dict:
    """One line of the record, built from one userinfo response.

    Pure, and separated from the network for that reason: everything about the
    shape of the evidence can be exercised without a browser, a project or a
    person.

    **`orgs` has three states and they are three different facts.** A list is
    what the provider said. An empty list is a real answer, that the account is
    in no organization. A null is that the provider said nothing about
    organizations at all, which happens when the scope was not granted or the
    claim was not returned, and it carries its own sentence rather than reading
    as an empty answer or as a failure. That is the same rule
    `schema/migrations/008_absence_reason.sql` applies to an absent field: an
    absence is a positive statement with a reason, never an omission.

    **Every org entry is passed through as the provider wrote it.** Nothing here
    reads `name` or `roleInOrg` or reshapes an entry into keys this file knows
    about, because a shape built out of the keys we happen to have seen is a
    closed enumeration with a different hat on, and the next key Hugging Face
    adds would be dropped on the floor.
    """
    sub = userinfo.get("sub")
    if not sub:
        raise Refused(
            "the userinfo response carried no `sub`. `sub` is the only stable "
            "identifier here, since handles are renameable, so there is nothing "
            "to bind a capture to and nothing is written."
        )
    orgs = userinfo.get("orgs")
    entry = {
        "shape": SHAPE,
        "captured_at": captured_at or now(),
        "provider": provider,
        "issuer": issuer,
        "userinfo_endpoint": endpoint,
        "sub": sub,
        "preferred_username": userinfo.get("preferred_username"),
        "orgs": orgs if isinstance(orgs, list) else None,
    }
    if entry["orgs"] is None:
        entry["orgs_absence"] = (
            "the userinfo response carried no `orgs` claim, so nothing was "
            "observed about organization membership at this moment. That is "
            "not the same as membership of none, and it is not a failure: it "
            "is what happens when the `read-memberships` scope was not granted "
            "or the provider did not return the claim."
        )
    return entry


def confirmations(entry: dict) -> list[str]:
    """One sentence per organization, in the register this registry uses.

    "Confirmed on" a date, never "verified": nothing re-reads this and a word
    that implies something does is the word that turns dated evidence into a
    badge. The organization's own name is taken from whatever key the provider
    used for it, and an entry with no recognizable name still gets a sentence
    rather than being dropped.
    """
    orgs = entry.get("orgs")
    if orgs is None:
        return []
    when = entry.get("captured_at", "")
    out = []
    for org in orgs:
        if isinstance(org, dict):
            name = org.get("name") or org.get("preferred_username") or org.get("sub")
        else:
            name = org
        if name:
            out.append(f"member of {name}, confirmed {when}")
        else:
            out.append("member of an organization the provider did not name, "
                       f"confirmed {when}")
    return out


# --------------------------------------------------------------------------- #
# PKCE, and the two network hops.


def pkce_pair() -> tuple[str, str]:
    """A verifier and its S256 challenge, both URL-safe and unpadded."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def authorize_url(supabase_url: str, *, provider: str, redirect_to: str,
                  challenge: str) -> str:
    """Where the browser goes. Supabase holds the client secret, so we do not.

    `code_challenge_method` is lowercase `s256` because that is what Supabase
    validates against; it forwards `S256` to the provider on the other leg.
    """
    query = urllib.parse.urlencode({
        "provider": provider,
        "redirect_to": redirect_to,
        "code_challenge": challenge,
        "code_challenge_method": "s256",
    })
    return f"{supabase_url}/auth/v1/authorize?{query}"


def _post_json(url: str, payload: dict, headers: dict) -> dict:
    body = json.dumps(payload).encode()
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={**headers, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:400]
        raise Refused(f"the token exchange answered {error.code}: {detail}") from error


def _get_json(url: str, headers: dict | None = None) -> dict:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        # The body is read and dropped rather than shown, because this call
        # carries the provider token in a header and an error page can echo a
        # request back at you.
        error.read()
        raise Refused(
            f"{urlsplit(url).netloc} answered {error.code} to the userinfo "
            "call. Nothing was recorded."
        ) from error


def discovery(url: str = DISCOVERY) -> dict:
    """The provider's own document. Fetched every run, never remembered."""
    document = _get_json(url)
    for key in ("issuer", "userinfo_endpoint"):
        if not document.get(key):
            raise Refused(f"the discovery document at {url} carries no {key}")
    return document


def exchange(supabase_url: str, key: str, *, code: str, verifier: str) -> dict:
    """The authorization code for a session. The session is never written down."""
    return _post_json(f"{supabase_url}/auth/v1/token?grant_type=pkce",
                      {"auth_code": code, "code_verifier": verifier},
                      {"apikey": key, "Authorization": f"Bearer {key}"})


def userinfo(endpoint: str, token: str) -> dict:
    """What the provider says about the account holding this token, right now."""
    return _get_json(endpoint, {"Authorization": f"Bearer {token}"})


def capture(supabase_url: str, key: str, *, code: str, verifier: str,
            provider: str, document: dict | None = None) -> dict:
    """Code in, one record line out. The two tokens live only in this frame.

    Neither the Supabase session nor the provider token is returned, assigned to
    anything longer-lived, or passed to anything that writes. The one thing that
    leaves here is the capture.
    """
    session = exchange(supabase_url, key, code=code, verifier=verifier)
    provider_token = session.get("provider_token")
    if not provider_token:
        raise Refused(
            "the session carried no provider token, so there was nothing to "
            "call the userinfo endpoint with and no membership was observed. "
            "Supabase returns it only on the sign-in itself and never on a "
            "refresh, so the fix is to sign in again rather than to retry this."
        )
    document = document or discovery()
    said = userinfo(document["userinfo_endpoint"], provider_token)
    return capture_from(said, provider=provider, issuer=document["issuer"],
                        endpoint=document["userinfo_endpoint"])


# --------------------------------------------------------------------------- #
# The server. One person, one machine, one sign-in at a time.


@dataclass
class SignIn:
    """Everything one run holds, under one lock.

    There is one pending flow because there is one operator with one browser.
    Serializing costs nothing and the way to get it wrong ends with one
    person's code exchanged against another person's verifier.
    """

    supabase_url: str
    key: str
    provider: str
    record: Path
    token: str = field(default_factory=lambda: secrets.token_urlsafe(24))
    lock: threading.Lock = field(default_factory=threading.Lock)
    pending: str | None = None

    def start(self) -> str:
        """Mint a verifier, hold it, and hand back its challenge."""
        verifier, challenge = pkce_pair()
        self.pending = verifier
        return challenge

    def take(self) -> str:
        """The pending verifier, once. A second callback has nothing to use."""
        verifier, self.pending = self.pending, None
        if not verifier:
            raise Refused(
                "no sign-in is in flight, so this callback has no verifier to "
                "exchange against. Start again from the page this tool printed."
            )
        return verifier


def _page(title: str, body: str) -> bytes:
    """One template, no script, no form, no field.

    There is nothing on any page this serves that submits: the only interactive
    element is a link to the identity provider, which is a navigation away from
    here rather than a target that receives anything from here. That difference
    is the one `SIGNIN.md` argues is the structural way to tell an auth redirect
    from a write path.
    """
    return (
        "<!doctype html><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title>"
        "<style>"
        "body{font:16px/1.55 ui-sans-serif,system-ui,sans-serif;max-width:40rem;"
        "margin:4rem auto;padding:0 1.5rem;color:#111}"
        "h1{font-size:1.4rem;margin:0 0 1rem}"
        "a.go{display:inline-block;margin:1.5rem 0;padding:.6rem 1.1rem;"
        "border:1px solid #111;border-radius:.3rem;color:#111;text-decoration:none}"
        "code{background:#f3f3f3;padding:.1rem .3rem;border-radius:.2rem}"
        "ul{padding-left:1.2rem}.absent{color:#555;border-left:3px solid #ddd;"
        "padding-left:.8rem}"
        "</style>"
        f"<h1>{html.escape(title)}</h1>{body}"
    ).encode()


def landing(url: str) -> bytes:
    """What is about to be read, said before it is read rather than after."""
    return _page("Sign in with Hugging Face", f"""
<p>This reads one thing from Hugging Face and writes one line about it:
which organizations your account was in <strong>at this moment</strong>, and
the moment.</p>
<ul>
  <li>Your <code>sub</code> and handle. The record identifies you by
      <code>sub</code>, because handles can be renamed.</li>
  <li>The <code>orgs</code> list exactly as Hugging Face returns it.</li>
  <li>The time of the reading.</li>
</ul>
<p>It is evidence with a date on it, not a standing. Nothing re-checks it, so
membership that ends later will not un-record itself here; checking again means
signing in again. No token is written anywhere.</p>
<p>Signing in publishes nothing. The line stays in a file this repository
ignores. Binding an account to a namespace is a second, separate command that
somebody runs on purpose, and what it publishes is the claim rather than this
file.</p>
<a class="go" href="{html.escape(url)}">Continue to Hugging Face</a>
<p>The line is appended to <code>artifacts/memberships.jsonl</code> on this
machine.</p>""")


def captured(entry: dict) -> bytes:
    """The capture, rendered as what it is."""
    who = html.escape(entry.get("preferred_username") or "(no handle returned)")
    rows = confirmations(entry)
    if entry.get("orgs") is None:
        orgs = ("<p class=absent>"
                + html.escape(entry.get("orgs_absence", "")) + "</p>")
    elif not rows:
        orgs = (f"<p>No organization, as of {html.escape(entry['captured_at'])}. "
                "That is an answer, not a blank.</p>")
    else:
        orgs = "<ul>" + "".join(f"<li>{html.escape(r)}</li>" for r in rows) + "</ul>"
    return _page("Recorded", f"""
<p>Signed in as <strong>{who}</strong>, <code>{html.escape(entry['sub'])}</code>.</p>
{orgs}
<p>Written to <code>artifacts/memberships.jsonl</code>. You can close this tab
and stop the tool.</p>""")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "registry-signin"
    sys_version = ""
    signin: SignIn = None  # type: ignore[assignment]

    def log_message(self, fmt, *args):
        # The route and nothing else. The default logs the request line, which
        # on the callback carries the authorization code, and a terminal
        # scrollback is a place a code should never reach.
        route = urlsplit(getattr(self, "path", "") or "").path or "-"
        sys.stderr.write(f"{getattr(self, 'command', None) or '-'} {route}\n")

    def _reply(self, code: int, blob: bytes, kind: str = "text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(blob)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(blob)

    def _refused(self, reason: str, code: int = 400):
        self._reply(code, _page("Not done", f"<p>{html.escape(reason)}</p>"))

    def _host_ok(self) -> bool:
        """A name that resolves to 127.0.0.1 defeats the bind on its own."""
        port = self.server.server_address[1]
        return self.headers.get("Host") in (f"{HOST}:{port}", f"localhost:{port}")

    def _admitted(self) -> bool:
        """The landing page's checks, which are the intake tool's four.

        The run token is in the URL this tool printed and nowhere else, the
        `Host` header catches a rebound name, and `Origin` and `Sec-Fetch-Site`
        catch a page the operator did not open reaching a loopback port from
        the same browser.
        """
        port = self.server.server_address[1]
        got = parse_qs(urlsplit(self.path).query).get("k", [""])[0]
        if not secrets.compare_digest(got, self.signin.token):
            return False
        if not self._host_ok():
            return False
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://{HOST}:{port}",
                                     f"http://localhost:{port}"):
            return False
        if self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
            return False
        return True

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == CALLBACK_PATH:
            self._callback()
            return
        if route != "/":
            self._refused("no such page on this tool", 404)
            return
        if not self._admitted():
            self._refused("not admitted", 403)
            return
        with self.signin.lock:
            challenge = self.signin.start()
        port = self.server.server_address[1]
        url = authorize_url(
            self.signin.supabase_url, provider=self.signin.provider,
            redirect_to=f"http://{HOST}:{port}{CALLBACK_PATH}",
            challenge=challenge)
        self._reply(200, landing(url))

    def _callback(self):
        """The one route the provider drives, so the one with different checks.

        It cannot carry the run token: the URL is a literal line in the Supabase
        project's allowlist and the browser arrives here from another site, so
        `Origin` and `Sec-Fetch-Site` say cross-site on a legitimate return. The
        `Host` check still holds, and what replaces the rest is structural: the
        pending verifier is single use and held only in this process, and the
        code has to exchange against it at Supabase. A page that pushes a
        browser here with an invented code gets a refusal from the exchange, and
        a page that somehow had a real code of its own would be recording its
        own `sub` under its own name, which is a line in a local file rather
        than anything gained.
        """
        if not self._host_ok():
            self._refused("not admitted", 403)
            return
        query = parse_qs(urlsplit(self.path).query)
        if "error" in query or "error_description" in query:
            said = (query.get("error_description") or query.get("error"))[0]
            self._refused(f"the provider stopped the sign-in: {said}")
            return
        code = query.get("code", [""])[0]
        if not code:
            self._refused(
                "the callback carried no `code`. If the address bar shows a "
                "`#access_token=` fragment instead, Supabase ran the implicit "
                "flow, which means the PKCE parameters did not reach it. If it "
                "shows the site URL instead of this address, the loopback "
                "callback is not in the project's Redirect URLs allowlist.")
            return
        with self.signin.lock:
            try:
                verifier = self.signin.take()
                entry = capture(self.signin.supabase_url, self.signin.key,
                                code=code, verifier=verifier,
                                provider=self.signin.provider)
            except Refused as refused:
                self._refused(str(refused))
                return
            append_record(entry, self.signin.record)
        self._reply(200, captured(entry))


def serve(*, port: int = PORT, provider: str = PROVIDER,
          record: Path | None = None, open_browser: bool = True) -> None:
    supabase_url, key = config(read_env())
    signin = SignIn(supabase_url, key, provider, record or RECORD)
    handler = type("BoundHandler", (Handler,), {"signin": signin})
    httpd = ThreadingHTTPServer((HOST, port), handler)
    bound = httpd.server_address[1]
    url = f"http://{HOST}:{bound}/?k={signin.token}"
    callback = f"http://{HOST}:{bound}{CALLBACK_PATH}"
    # Flushed, because these lines are the whole interface and a buffered
    # stdout hands them over when the process exits.
    print(f"sign-in on {url}", flush=True)
    print(f"allowlist this exact callback in the Supabase project: {callback}",
          flush=True)
    print(f"provider {provider}. Loopback only, and the link above is good for "
          "this run alone. Ctrl-C to stop.", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()


def show(record: Path | None = None) -> None:
    """Read the record back. Captures are dated, so they are listed by date."""
    entries = read_record(record)
    if not entries:
        print("no captures recorded")
        return
    for entry in entries:
        who = entry.get("preferred_username") or "(no handle)"
        print(f"{entry['captured_at']}  {who}  {entry['sub']}  "
              f"via {entry.get('provider')}")
        if entry.get("orgs") is None:
            print(f"    no organizations observed: {entry.get('orgs_absence', '')}")
        elif not entry["orgs"]:
            print("    no organization, which is an answer rather than a blank")
        for line in confirmations(entry):
            print(f"    {line}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    run = sub.add_parser("serve", help=f"sign in, on {HOST} and nowhere else")
    run.add_argument("--port", type=int, default=PORT,
                     help="fixed, because the callback is allowlisted literally")
    run.add_argument("--provider", default=PROVIDER,
                     help="the Supabase provider string, passed through as given")
    run.add_argument("--no-browser", action="store_true")

    sub.add_parser("show", help="read the dated captures back")

    args = ap.parse_args(argv)
    try:
        if args.command == "serve":
            serve(port=args.port, provider=args.provider,
                  open_browser=not args.no_browser)
        else:
            show()
    except Refused as refused:
        raise SystemExit(str(refused)) from refused
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
