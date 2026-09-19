# Signing in, and dating what the memberships said

Premise, restated because a premise stated in one document gets violated in every
other one: the registry never designates, consumers pin, visibly. Signing in
confers no standing. It produces one thing, a dated record of what Hugging Face
said about an account at one moment, and nothing in the corpus reads it.

```
.venv/bin/python artifacts/signin.py serve
.venv/bin/python artifacts/signin.py show
```

It prints a URL and opens it. The URL carries a token generated for that run, and
the listener is on 127.0.0.1 and nothing else.

## It is not wired into the built site, and that is the recommendation

`tests/test_intake.py` fails the build if `astro/dist` ships a form, a POST
target, an `XMLHttpRequest`, a `sendBeacon` or a loopback address. That guard is
untouched by this tool and should stay untouched.

The guard is not the reason, though. The reason is that a sign-in button on the
published site is the front door of a write path, and the dual-use policy a write
path needs does not exist. `V2.md` says in its own opening that none of this is
settled and that v1 asks for the Account links to come out. Shipping a sign-in
while the links that advertised an account model are being removed would be
moving in two directions at once.

There is a second reason, narrower and worth writing down because it is the one
that would have been missed. **A sign-in link passes the guard as written.** It
is an anchor with an absolute `href`; it is not a form, not a POST, not a beacon,
and the Supabase authorize URL is not a loopback address. So the guard would have
said nothing, and the thing the guard exists to prevent would have arrived
anyway, one hop later, when the page that receives the callback needs to read
`orgs` and write it down. `tests/test_signin.py` closes that specific hole by
name: it fails if `astro/dist` ever carries `/auth/v1/`, `supabase` or
`signInWithOAuth`.

### If sign-in is taken into the site later, key the guard on structure

Not on a name, and not by adding an exemption for anything called "auth". The
difference that matters is **whether the element is a target that receives data
from this page**:

- A form, a POST target, an `enctype`, a `formaction`, a file input, an
  `XMLHttpRequest`, a `sendBeacon` or a `fetch` with a body all receive.
- An anchor whose `href` is an absolute URL to a third-party authorization
  endpoint sends this page's data nowhere. The browser navigates away and the
  page is gone.

So the widening, if it is ever wanted, is: the existing patterns stay exactly as
they are, and an `<a href>` to an off-site origin is permitted because it already
is. What must stay failing is the return leg, because that is the half that
reads a claim and writes it down. A static site cannot do that without shipping
script, so the honest version of "sign-in on the site" is a site that has a
backend, which is the decision `V2.md` is actually asking for.

The sign-in page this tool serves already meets the structural rule: one link
out, no script, no form, no field. `tests/test_signin.py` asserts that, so the
property is executable rather than a claim in this file.

## Why membership is captured rather than stored

A real sign-in through the configured Supabase provider lands `preferred_username`
and `sub` in `auth.users.raw_user_meta_data` and lands `orgs` as null, because
`orgs` is a Hugging Face claim rather than a standard OIDC one and does not make
the trip. So membership has to be read from a live userinfo call while the token
is available, which is the moment of sign-in and no later: Supabase returns
`provider_token` in the session on the sign-in itself and never on a refresh.

That forcing is the good outcome. People join and leave organizations. A
membership read once and cached forever is a stale fact wearing a badge. What
this writes instead is dated evidence, the same register the history audit and
the attestations already use: the result is dated, not permanent.

So the record says "member of `controlbun`, confirmed 2026-09-19". It does not
say the membership is verified, because nothing re-reads it. Checking again means
signing in again.

## The record, which is the handover

One JSON object per line, appended, never rewritten, at
`artifacts/memberships.jsonl`. Gitignored by default, with the reason at the
line in `.gitignore`.

```json
{
  "shape": "controlbun.registry/membership-capture@1",
  "captured_at": "2026-09-19T00:00:00Z",
  "provider": "custom:huggingface",
  "issuer": "https://huggingface.co",
  "userinfo_endpoint": "https://huggingface.co/oauth/userinfo",
  "sub": "<opaque provider subject>",
  "preferred_username": "<handle at the time of the capture>",
  "orgs": [ { "...": "exactly as the provider returned it" } ]
}
```

| field | what it is |
|---|---|
| `shape` | namespaced and versioned. The shape will change; a reader has to be able to tell which one it is holding |
| `captured_at` | UTC, second resolution. The evidence is the pair of the reading and this |
| `provider` | the string that was used, carried rather than checked. Nothing anywhere compares it to a list of names |
| `issuer`, `userinfo_endpoint` | read from the provider's discovery document at the moment of the capture, so the evidence says where it came from rather than being trusted to have come from the right place |
| `sub` | the binding. Opaque and stable |
| `preferred_username` | the handle, which is what a reader recognizes and is not the binding, because handles are renameable |
| `orgs` | three states, below |

**`orgs` has three states and they are three different facts.**

- A list is what the provider said. Every entry is passed through byte for byte,
  including keys this code has never seen. Reshaping an entry into `name` and
  `roleInOrg` would be a closed enumeration with a different hat on, and the next
  key Hugging Face adds would be dropped on the floor.
- An empty list is a real answer: the account is in no organization.
- `null` is that the provider said nothing about organizations at all, which
  happens when `read-memberships` was not granted or the claim was not returned.
  It carries `orgs_absence`, a sentence saying so. That is the rule
  `schema/migrations/008_absence_reason.sql` applies to an absent field: an
  absence is a positive statement with a reason, never an omission and never an
  error.

**No token, ever.** The Supabase session and the provider token exist in one
local variable for the length of one userinfo call. They reach no file, no page
and no log line, and `log_message` prints the route and drops the query string,
which is where the authorization code arrives. `tests/test_signin.py` checks all
of it, including that no key other than the ones above can appear in a capture.

## Setup, once

Needs `.env` to carry `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`, and needs
the Supabase project to have the Hugging Face provider configured against
`HF_OAUTH_CLIENT_ID` and `HF_OAUTH_CLIENT_SECRET`. Nothing here reads the client
secret: Supabase is the confidential client and performs the exchange, which is
also why no function of ours holds anything.

One thing has to be added by hand: **the loopback callback has to be in the
project's Redirect URLs allowlist**, or Supabase sends the browser to the site
URL and this tool sees nothing. The exact line is printed on startup. That is why
the port is fixed at 8931 rather than asked of the OS the way the intake tool
asks: an allowlist entry cannot follow a port that changes every run.

## The flow, and why it ships no JavaScript

```
browser  ->  {SUPABASE_URL}/auth/v1/authorize
             ?provider=custom:huggingface
             &redirect_to=http://127.0.0.1:8931/callback
             &code_challenge=...&code_challenge_method=s256
         ->  302 to huggingface.co/oauth/authorize
         ->  the person approves
         ->  Supabase's callback, then 302 back to loopback carrying ?code=
here     ->  POST {SUPABASE_URL}/auth/v1/token?grant_type=pkce
         ->  GET the userinfo endpoint with the provider token
         ->  one line appended
```

The PKCE parameters are ours and they are load-bearing. Supply them and the
return leg is `?code=` in the query string, which a server reads. Omit them and
Supabase runs the implicit flow and puts the answer in a URL fragment, which a
server never sees and only script can reach. So supplying them is what lets this
tool have no JavaScript at all, which in turn is why it cannot carry a scripted
write surface to leak.

## What this makes impossible to express

A membership somebody knows about but cannot sign in to demonstrate. There is no
way to write a capture by hand and no `--sub` flag, so an organization membership
that is true and unprovable through this provider has nowhere to go. That is
deliberate for evidence produced by a machine, and it is also exactly the case
`V2.md` section 1 says a claim has to leave room for: indexed entries whose
author never signed up, and evidence written about other people's work. A capture
is one kind of evidence for a claim. It is not the only kind, and a claim model
that accepts only captures would foreclose the seeding lane.

Also impossible: asking a second time without the person present. There is no
refresh path, by construction. Re-verification is a new sign-in, which is a new
line, which is why the lines are dated.

## Checks on the loopback constraint

Same four as the intake tool, with one deliberate difference.

- the bind is 127.0.0.1, and there is no flag that changes it
- a per-run token, in the URL and nowhere else
- the `Host` header is checked, because a name that resolves to 127.0.0.1
  defeats the bind by itself
- `Origin` and `Sec-Fetch-Site` are checked on the landing page

**The callback cannot use the last two.** Its URL is a literal line in the
Supabase allowlist, so it cannot carry the run token, and the browser arrives
from another site, so `Sec-Fetch-Site` says cross-site on a legitimate return.
The `Host` check still holds. What replaces the rest is structural: the pending
verifier is single use and lives only in this process, and the code has to
exchange against it at Supabase. A page that pushes a browser to the callback
with an invented code gets a refusal from the exchange. A page that somehow held
a real code of its own would be recording its own `sub` under its own name in a
local file, which is not an escalation.
