/**
 * The shapes a browser sign-in produces, as functions with no DOM and no network.
 *
 * Premise, restated because a premise stated in one file gets violated in every
 * other one: **plurality is the product; the registry never designates,
 * consumers pin, visibly.** Nothing here ranks, scores, approves or filters
 * anybody. Signing in produces one thing, a dated record of what a provider said
 * about an account at one moment, and it confers no standing on the account or
 * on anything the account submits.
 *
 * ## Why this file is separate from the page
 *
 * Everything here is a pure function of its arguments, so the shape of the
 * evidence can be exercised without a browser, a provider or a person.
 * `tests/test_handshake.mjs.py` runs it under node against the same three-state
 * cases `artifacts/claim.py` reads. The page next door owns the DOM and the
 * network and owns no rule.
 *
 * ## `orgs` has three states and they are three different facts
 *
 * Carried here from `artifacts/signin.py`, which is deleted, because the rule
 * was worked out against a real sign-in and is the thing that had to survive the
 * file:
 *
 * - A list is what the provider said. Every entry is passed through byte for
 *   byte, including keys this code has never seen. Reshaping an entry into
 *   `name` and `roleInOrg` would be a closed enumeration with a different hat
 *   on, and the next key the provider adds would be dropped on the floor.
 * - An empty list is a real answer: the account is in no organization.
 * - `null` is the provider saying nothing about organizations at all, which
 *   happens when the membership scope was not granted or the claim was not
 *   returned. It carries `orgsAbsence`, a sentence saying so. That is the rule
 *   `schema/migrations/008_absence_reason.sql` applies to an absent field: an
 *   absence is a positive statement with a reason, never an omission and never
 *   an error.
 *
 * ## Two credentials, opposite lifetimes
 *
 * This section read "No token, ever" and was true of every function here until
 * one of them had to build the thing a return visit is restored from. What
 * replaced it is narrower, and it is the rule the whole sign-in turns on.
 *
 * - **The Supabase session**, `access_token` with its `refresh_token`, is what
 *   row-level security scopes to inserting one row into `pending_submission` as
 *   yourself. It reads nobody else's rows, and there is no update or delete
 *   policy at all, so it changes and removes nothing. It **persists**, in
 *   `localStorage`, under one key, so a visit tomorrow is not a second sign-in.
 *   `heldSessionFrom` is the projection that builds what is written, and it is
 *   the only function in this file that touches a credential.
 * - **The Hugging Face `provider_token`** can, with `contribute-repos`, create
 *   and write repositories in somebody's own namespace. It **never persists**,
 *   anywhere, in any form: it is held in one local variable in the page for the
 *   moment somebody agrees to an upload, and the frame ends. Storing it would
 *   buy nothing past its expiry, because Hugging Face returns it on the sign-in
 *   itself and never on a renewal.
 *
 * That last clause is read rather than recalled. Against supabase/auth
 * v2.197.0, which is the version the live project reports at `/auth/v1/health`,
 * checked 2026-09-20: `AccessTokenResponse` in `internal/tokens/service.go`
 * carries `provider_token` as `omitempty`, `RefreshTokenGrant` in that file
 * sets `Token`, `TokenType`, `ExpiresIn`, `ExpiresAt`, `RefreshToken` and
 * `User` and nothing else, and `ProviderAccessToken` is assigned in exactly one
 * place in `internal/api/token.go`, inside the PKCE branch, off the flow state.
 *
 * `heldSessionFrom` names its fields, so a token endpoint that grows a claim
 * cannot push one into a browser, and `provider_token` is not among the names.
 * `pendingRowFrom` still has no parameter a token can arrive in, which is why
 * it takes the user out of the held record rather than the record.
 *
 * ## Both directions, and the second one reads nothing
 *
 * `submissionFrom`, `pasteFrom` and `pendingRowFrom` build what gets sent.
 * `playback` and `inArrivalOrder`, added 2026-09-20, take a row back out of the
 * holding table for the one account that put it there. That direction reads no
 * field for meaning: it walks the keys the record has, in the order it has
 * them, and says what each value is. A record is not the corpus and a number in
 * one is a number somebody typed, so nothing here derives, checks or re-orders
 * anything off what a record says.
 *
 * ## No closed enum, anywhere
 *
 * `provider`, the organization's role, `kind`, `hook_point` and every other
 * field are carried through as strings and compared against nothing. What is
 * refused here is one thing and it is refused by name: an upload aimed at this
 * registry's own namespace, which is `served_copy` and a different question
 * (`schema/migrations/004`, `artifacts/publish.py`'s `ServedCopy`).
 */

export const CAPTURE_SHAPE = "controlbun.registry/membership-capture@1";
export const SUBMISSION_SHAPE = "controlbun.registry/link-submission@1";

/**
 * The other thing `/submit/` can send: one block of text, unread.
 *
 * `artifacts/agent_handoff.py` holds both halves of the handoff, the prompt an
 * author copies into their coding agent and the parser that reads what comes
 * back. **Only the prompt crosses to the browser.** The parser stays in Python
 * and runs when the author pulls, so there is one implementation of several
 * hundred lines of recovery rather than two that drift.
 *
 * What that costs is real and `/submit/` says it rather than hiding it: a
 * mistake in a paste is not found as somebody types, the way a mistake in a
 * field is. It is found when the author reads the row in, and what comes back
 * then is the sentence `parse` already produces, naming what was missing.
 */
export const PASTE_SHAPE = "controlbun.registry/agent-paste@1";

// The namespace this registry itself owns. Bytes uploaded into it would be a
// copy this project serves rather than a thing an author published, which is
// `served_repo` and a different column. `artifacts/publish.py` refuses it on
// the author's own machine; this refuses it in the browser, because the two
// callers are now on different computers and the rule is the same one.
export const OUR_NAMESPACE = "controlbun";

/** Something this path will not do, with the reason already in the message. */
export class Refused extends Error {}

/**
 * The absence sentence, in the register `008` asks for: a positive statement.
 *
 * Kept as a constant rather than written at the one call site, because
 * `artifacts/claim.py` reads captures written by this file and the sentence is
 * part of what a capture says.
 */
export const ORGS_ABSENCE =
  "the userinfo response carried no `orgs` claim, so nothing was observed " +
  "about organization membership at this moment. That is not the same as " +
  "membership of none, and it is not a failure: it is what happens when the " +
  "membership scope was not granted or the provider did not return the claim.";

// --------------------------------------------------------------------------
// What each authorization asks for. Two constants, in one file, because the
// second one has to contain the first and they are read by two pages now:
// `/signed-in/` starts a sign-in and `/submit/` asks for the upload permission,
// and a property that spans two files is a property that holds until somebody
// edits one of them.

/**
 * What signing in asks for, and nothing beyond it. Read scopes only.
 *
 * `email` is in here because Supabase refuses the sign-in without it. Its OIDC
 * handler builds an `auth.users` row and that row needs an address, so a
 * provider that returns no email claim fails the exchange with "Error getting
 * user email from external provider" after the reader has already logged in and
 * consented. Hugging Face only returns the claim when `email` is asked for, so
 * dropping it does not make the sign-in more private, it makes it fail. Checked
 * against the live project on 2026-09-20 by dropping it, which is how this was
 * found.
 *
 * Nothing in this project reads the address, writes it down or sends it
 * anywhere: it exists in the identity service's own user row and in no file,
 * page or table of this project's. `pendingRowFrom` takes `sub`,
 * `preferred_username` and the account id, and the capture shape has no field
 * for it.
 */
export const READ_SCOPES = "openid email profile read-memberships";

/**
 * What the upload offer asks for, in a second authorization, and only when
 * somebody chooses it.
 *
 * Hugging Face documents `contribute-repos` as "Create repositories and access
 * those created by this app. Cannot access any other repositories unless
 * additional permissions are granted", which is the narrowest scope that does
 * this job. Checked against the live scope list on 2026-09-20; an unknown scope
 * string is refused with `invalid_scope` before anybody is asked to log in.
 *
 * Restates the read scopes because Supabase **replaces** the configured list
 * rather than adding to it, so a second authorization asking only for the new
 * scope would silently drop the others.
 */
export const WRITE_SCOPES =
  "openid email profile read-memberships contribute-repos";

// --------------------------------------------------------------------------
// PKCE.

function base64url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/**
 * A verifier and its S256 challenge, both URL-safe and unpadded.
 *
 * The PKCE parameters are ours and they are load-bearing. Supply them and the
 * return leg is `?code=` in the query string. Omit them and Supabase runs the
 * implicit flow and puts the answer in a URL fragment, which is a session in
 * the address bar and in every history entry that copies it.
 */
export async function pkcePair() {
  const raw = new Uint8Array(64);
  crypto.getRandomValues(raw);
  const verifier = base64url(raw);
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(verifier),
  );
  return { verifier, challenge: base64url(new Uint8Array(digest)) };
}

/**
 * Where the browser goes. Supabase holds the client secret, so this does not.
 *
 * `scopes` replaces the project's configured default rather than adding to it,
 * which is what `loadCustomProvider` does with the parameter in supabase/auth,
 * so the wider request has to restate the narrow ones. That is why the caller
 * passes a whole list and not an extra.
 *
 * `code_challenge_method` is lowercase `s256` because that is what Supabase
 * validates against; it forwards `S256` to the provider on the other leg.
 */
export function authorizeUrl(supabaseUrl, { provider, redirectTo, challenge, scopes }) {
  const query = new URLSearchParams({
    provider,
    redirect_to: redirectTo,
    code_challenge: challenge,
    code_challenge_method: "s256",
  });
  if (scopes && scopes.length) query.set("scopes", scopes.join(" "));
  return `${supabaseUrl.replace(/\/+$/, "")}/auth/v1/authorize?${query}`;
}

// --------------------------------------------------------------------------
// The capture, which is a pure function of what userinfo said.

export function nowStamp(date = new Date()) {
  return date.toISOString().replace(/\.\d+Z$/, "Z");
}

/**
 * One capture, built from one userinfo response.
 *
 * **Bound to `sub`, never to `preferred_username`.** Handles are renameable, so
 * a record bound to the handle either breaks on a rename or follows the handle
 * to whoever takes it next. The handle is recorded too, because it is what a
 * reader recognizes, but `sub` is what identifies.
 *
 * The key names are the snake_case ones `artifacts/claim.py` reads, because
 * this file writes the file that tool reads and a second spelling would be a
 * second shape.
 */
export function captureFrom(said, { provider, issuer, endpoint, capturedAt }) {
  const sub = said && said.sub;
  if (!sub) {
    throw new Refused(
      "the userinfo response carried no `sub`. `sub` is the only stable " +
        "identifier here, since handles are renameable, so there is nothing " +
        "to bind a capture to and nothing was written.",
    );
  }
  const orgs = Array.isArray(said.orgs) ? said.orgs : null;
  const capture = {
    shape: CAPTURE_SHAPE,
    captured_at: capturedAt || nowStamp(),
    provider,
    issuer,
    userinfo_endpoint: endpoint,
    sub,
    preferred_username: said.preferred_username ?? null,
    orgs,
  };
  if (capture.orgs === null) capture.orgs_absence = ORGS_ABSENCE;
  return capture;
}

/** What the provider called the organization, in whichever key it used. */
export function orgName(org) {
  if (typeof org === "string") return org || null;
  if (org && typeof org === "object") {
    for (const key of ["name", "preferred_username", "sub"]) {
      if (typeof org[key] === "string" && org[key]) return org[key];
    }
  }
  return null;
}

/** `roleInOrg` where the provider gives one, and null where it did not. */
export function orgRole(org) {
  if (!org || typeof org !== "object") return null;
  for (const key of ["roleInOrg", "role"]) {
    if (typeof org[key] === "string" && org[key]) return org[key];
  }
  return null;
}

/**
 * One sentence per organization, in the register this registry uses.
 *
 * "Confirmed on" a date, never "verified": nothing re-reads this, and a word
 * implying something does is the word that turns dated evidence into a badge.
 */
export function confirmations(capture) {
  if (!Array.isArray(capture.orgs)) return [];
  const when = capture.captured_at || "";
  return capture.orgs.map((org) => {
    const name = orgName(org);
    return name
      ? `member of ${name}, confirmed ${when}`
      : `member of an organization the provider did not name, confirmed ${when}`;
  });
}

// --------------------------------------------------------------------------
// The submission, which is a pure function of the form and the capture.

/** Forty hex characters, the one rule `controlbun.fetch.commit_sha` states. */
export function commitSha(given) {
  const value = (given || "").trim();
  if (!/^[0-9a-f]{40}$/i.test(value)) {
    throw new Refused(
      `${JSON.stringify(value)} is not a 40-character commit sha. A branch or ` +
        "a tag is movable by whoever owns the repository, so a pin that named " +
        "one would resolve to different bytes later and the digest beside it " +
        "would stop meaning anything.",
    );
  }
  return value.toLowerCase();
}

/**
 * The refusal that keeps an upload out of this registry's own namespace.
 *
 * The end state the offer promises is a pin to a public artifact in the
 * submitter's own account. Bytes landing under `controlbun/*` would be a copy
 * this project serves, which is `served_repo`, a different column and a
 * different question.
 */
export function refuseOurNamespace(repo) {
  const owner = String(repo || "").split("/")[0];
  if (owner.toLowerCase() === OUR_NAMESPACE) {
    throw new Refused(
      `${repo} is under this registry's own namespace. The offer is to put ` +
        "your file in your account, so the row records where you published " +
        "it. Bytes here would be a copy this project serves, which is a " +
        "different column and a different question: see " +
        "schema/migrations/004_served_copy.sql.",
    );
  }
  return repo;
}

function trimmed(value) {
  return String(value ?? "").trim();
}

function stated(name, value, why) {
  const out = trimmed(value);
  if (!out) throw new Refused(`${name} is empty. ${why}`);
  return out;
}

function optional(value) {
  const out = trimmed(value);
  return out === "" ? null : out;
}

function asNumber(name, value) {
  const out = trimmed(value);
  if (out === "") return null;
  const parsed = Number(out);
  if (!Number.isFinite(parsed)) {
    throw new Refused(`${name} is ${JSON.stringify(out)}, which is not a number.`);
  }
  return parsed;
}

function asInteger(name, value) {
  const out = trimmed(value);
  if (!/^-?\d+$/.test(out)) {
    throw new Refused(
      `${name} is ${JSON.stringify(out)}, and it has to be a whole number. ` +
        "A band across several layers cannot be stated in this column at all: " +
        "that gap is recorded in DECISIONS.md 2026-09-18.",
    );
  }
  return Number(out);
}

/**
 * One submission, built from the form and the capture that signed it.
 *
 * **The namespace is the handle and there is no field for it.** It is read off
 * the capture and never off the form, so the one path where identity is already
 * known stops asking a question it can answer. `DECISIONS.md` 2026-09-19 gives
 * the argument and names what it forecloses: a pseudonym, a lab name the
 * submitter holds no account for, and a namespace shared by several people who
 * each sign in as themselves.
 *
 * **No tensor fact is computed here and that is deliberate.** `shape`, `dtype`,
 * the L2 norm and the sha256 are what the bytes say, and the one thing that
 * reads bytes in this project is `controlbun.artifact`. A second implementation
 * in JavaScript is the failure this repository has hit more often than any
 * other, so what crosses is the pointer and the contract, and the facts are
 * derived once, on the machine that rebuilds the corpus, from the bytes at the
 * pin.
 */
export function submissionFrom(form, { capture, submittedAt }) {
  const handle = capture && capture.preferred_username;
  if (!handle) {
    throw new Refused(
      "the capture carries no handle, so there is no namespace to submit " +
        "under. The namespace is the handle the provider reported and there " +
        "is no field to type one into, which is the whole of the rule.",
    );
  }
  const repo = refuseOurNamespace(
    stated("repo", form.repo, "A pin needs a repository to resolve in."),
  );
  const path = stated(
    "path",
    form.path,
    "A repo and a commit name a tree, not a file.",
  );
  return {
    shape: SUBMISSION_SHAPE,
    submitted_at: submittedAt || nowStamp(),
    // Who signed in, carried so the author replaying this can see that the
    // namespace was not typed. `sub` is the binding; the handle is display.
    provider: capture.provider,
    subject: capture.sub,
    author: handle,
    label: stated(
      "label",
      form.label,
      "The label is the thing other people will disagree with you about, and " +
        "a bare one is a view across everyone claiming it.",
    ),
    version: stated(
      "version",
      form.version,
      "`author/model/label@version` resolves to one frozen submission forever, " +
        "so there has to be a version to freeze.",
    ),
    definition: stated(
      "definition",
      form.definition,
      "It is load bearing twice: it feeds contrast-pair generation and it is " +
        "the thing another author disagrees with.",
    ),
    created_at: stated(
      "created_at",
      form.created_at,
      "When the work happened, which is not when it was typed in here.",
    ),
    artifact: {
      repo,
      commit: commitSha(form.commit),
      path,
      // Both empty is the ordinary case and means the Hub, which is where a
      // row recording neither has always resolved. See migration 007. Nothing
      // is filled in: a host written onto a row nobody stated one for is a
      // provenance claim that reads like a checked fact.
      host: optional(form.host),
      url_template: optional(form.url_template),
    },
    intervention: {
      id: stated(
        "intervention id",
        form.intervention_id,
        "It is the primary key and the thing an eval report or an attack " +
          "points at.",
      ),
      kind: stated("kind", form.kind, "An open string. Whatever you call this."),
      model_id: stated(
        "model_id",
        form.model_id,
        "A direction has no meaning apart from the model it was read out of.",
      ),
      model_revision: optional(form.model_revision),
      layer: asInteger("layer", form.layer),
      layer_convention: stated(
        "layer_convention",
        form.layer_convention,
        "Getting this wrong is silent. `block-0indexed` is a common value and " +
          "not the only one.",
      ),
      hook_point: stated(
        "hook_point",
        form.hook_point,
        "An open string. Where in the block this acts.",
      ),
      chat_template_hash: optional(form.chat_template_hash),
      activation_norm: asNumber("activation_norm", form.activation_norm),
      coeff_low: asNumber("coeff_low", form.coeff_low),
      coeff_high: asNumber("coeff_high", form.coeff_high),
      steering_position: optional(form.steering_position),
      license_status: optional(form.license_status),
    },
    // What was looked for and is not there, with the account of why. Empty is
    // normal and is not a degraded record. The field side takes any string:
    // there is no list of the fields allowed to carry a reason, for the reason
    // migration 008 gives at length.
    absent: Object.fromEntries(
      Object.entries(form.absent || {})
        .map(([field, reason]) => [field, trimmed(reason)])
        .filter(([, reason]) => reason !== ""),
    ),
    // True when the registry made the upload on the submitter's behalf, which
    // is a fact about how the bytes got there and not a property of the
    // submission. Recorded so the author replaying it can see which offer was
    // taken.
    uploaded_by_registry: Boolean(form.uploaded_by_registry),
  };
}

/**
 * Which of the two routes this is, or a refusal naming both.
 *
 * **A paste and filled fields together is refused, and neither wins.** That is
 * the rule this project already applies where one field carries both a value
 * and a reason for having none: `artifacts/intake.py insert` refuses that pair
 * rather than resolving it, because preferring either drops one of somebody's
 * two statements silently while the record still reads correct to whoever wrote
 * it. Two accounts of one whole submission is the same thing one object up.
 *
 * `absent` counts as filled in, because an absence is a positive statement
 * about a field. `uploaded_by_registry` does not: it is a fact about how the
 * bytes got where they are, recorded either way, and it is set by pressing a
 * button rather than by typing.
 */
export function chosenRoute(form, pasted) {
  const filled = Object.entries(form || {})
    .filter(([name]) => name !== "absent" && name !== "uploaded_by_registry")
    .filter(([, value]) => trimmed(value) !== "")
    .map(([name]) => name);
  for (const field of Object.keys((form && form.absent) || {})) {
    filled.push(`a reason for ${field} being absent`);
  }
  const text = String(pasted ?? "").trim();
  if (text && filled.length) {
    throw new Refused(
      `this is a paste and ${filled.sort().join(", ")} filled in as well. ` +
        "Those are two accounts of one submission and nothing here can tell " +
        "which was meant, so neither is sent and nothing is preferred. Clear " +
        "the paste box, or clear the fields.",
    );
  }
  if (text) return "paste";
  if (filled.length) return "fields";
  throw new Refused(
    "nothing is filled in and nothing is pasted, so there is no submission " +
      "to build. Fill the fields in, or copy the prompt, run it where the " +
      "extraction happened, and paste back what it produces.",
  );
}

/**
 * One paste, wrapped in who sent it and nothing else.
 *
 * **Nothing here reads the text.** Not a field, not a marker, not whether it
 * looks like the block the prompt asks for. A check here would be the first
 * line of a second parser, and the second parser is the thing this arrangement
 * exists to not have. The text crosses as it arrived, including the agent's
 * prose around it, which `parse` reads past.
 *
 * The three identity fields are the browser's own copy, exactly as
 * `submissionFrom` carries them, so the author's pull can say where they
 * disagree with what Postgres stamped rather than preferring one silently.
 */
export function pasteFrom(pasted, { capture, submittedAt }) {
  const handle = capture && capture.preferred_username;
  if (!handle) {
    throw new Refused(
      "the capture carries no handle, so there is no namespace to submit " +
        "under. The namespace is the handle the provider reported and there " +
        "is no field to type one into, which is the whole of the rule.",
    );
  }
  const text = String(pasted ?? "");
  if (!text.trim()) {
    throw new Refused("the paste box is empty, so there is nothing to send.");
  }
  return {
    shape: PASTE_SHAPE,
    submitted_at: submittedAt || nowStamp(),
    provider: capture.provider,
    subject: capture.sub,
    author: handle,
    pasted: text,
  };
}

// --------------------------------------------------------------------------
// The row that is sent, which is built from the session and never from the
// record.

/**
 * One `pending_submission` row: three identity columns and the record.
 *
 * **Every identity value here comes off the session and none of it off the
 * record.** That is not a preference, it is the only thing that can be sent.
 * `schema/supabase/001_pending_submission.sql` refuses an insert whose
 * `account`, `subject` or `handle` disagrees with the verified JWT, so a row
 * built from the record's own `subject` and `author` would be rejected by
 * Postgres the moment those two disagreed with the session. The record still
 * carries the browser's copy of both, unedited, and the author's pull compares
 * them and says where they differ rather than quietly preferring either.
 *
 * The record goes in whole and is not read. Nothing here inspects a label, a
 * kind, a host or a format, and nothing here decides whether a submission is
 * any good: the table is a place a stranger's statement lands, not a queue and
 * not a review step.
 *
 * **No token crosses this function.** It takes the user out of the held record
 * and never the held record, so there is no parameter a token can arrive in and
 * no branch that could put one in the body. That mattered less when the session
 * died with the tab and matters more now that it does not: `heldSessionFrom`
 * puts the access token and the refresh token in the same object as the three
 * identity fields, and this function is the seam that keeps them apart. The
 * access token is the caller's problem and it goes in a header, one function
 * along, in `hub.mjs`.
 */
export function pendingRowFrom(user, record) {
  const id = user && user.id;
  const metadata = (user && user.user_metadata) || {};
  const subject = metadata.sub;
  const handle = metadata.preferred_username;
  if (!id || !subject || !handle) {
    const missing = [
      id ? null : "the account id",
      subject ? null : "the provider subject",
      handle ? null : "the handle",
    ].filter(Boolean);
    throw new Refused(
      `this session carries no ${missing.join(" and no ")}, and the table ` +
        "stamps all three from the verified session rather than taking them " +
        "from what is sent. There is nothing to stamp, so nothing was sent. " +
        "Signing in again is the fix, because the values are written when the " +
        "session is made and never afterwards.",
    );
  }
  if (!record || typeof record !== "object") {
    throw new Refused(
      "there is no submission to send. Build one first; the button that does " +
        "it is the one that reports what a field is missing and why it exists.",
    );
  }
  return { account: id, subject, handle, record };
}

// --------------------------------------------------------------------------
// The other direction: a row that was sent, played back to whoever sent it.
//
// **A record coming back is not a submission arriving.** `submissionFrom` and
// `pasteFrom` above build something to send; these take a row out of the
// holding table and say what is in it, for the one account that put it there.
// The whole of the rule is that nothing here reads a record for meaning. It
// walks the keys it finds, in the order they are in, and says what each value
// is. No field is required, no field is preferred, no shape is refused and no
// key is dropped for being one this file has never seen, which is the same rule
// `captureFrom` applies to an organization entry and the same reason.
//
// A number that comes back this way is a number somebody typed. Nothing has
// fetched the bytes at the pin, so nothing here can re-derive one, and the page
// says that rather than letting a figure sit in the same grammar as a figure
// the falsifier checked.

/** What one value is, without deciding what it means. */
function valueShown(value) {
  if (value === null || value === undefined) return { state: "none", text: null };
  if (typeof value === "boolean") {
    return { state: "flag", text: value ? "yes" : "no" };
  }
  if (typeof value === "number") return { state: "number", text: String(value) };
  if (typeof value === "string") return { state: "text", text: value };
  // An array or an object nested deeper than this walks. Shown as it was sent
  // rather than flattened or dropped: a key this file has never met is the
  // ordinary way a record grows, and a reader checking their own work is
  // entitled to see what they sent whatever shape it took.
  return { state: "text", text: JSON.stringify(value) };
}

function entriesShown(record) {
  return Object.entries(record).map(([name, value]) => ({
    name,
    ...valueShown(value),
  }));
}

/**
 * One row out of the holding table, said back.
 *
 * **The stamped identity wins and the disagreement is surfaced.** Postgres
 * writes `handle` and `subject` from the verified session; the record carries
 * the browser's own copy of both. `artifacts/intake.py` substitutes the first
 * for the second when the author pulls the row and reports the difference
 * rather than swallowing it, and this does the same thing on the page, because
 * a handle renamed between a sign-in and a send is a real fact about a real
 * person and preferring one copy silently hides it.
 *
 * **Nothing here mints `author/model/label@version`.** That string resolves to
 * one frozen submission in the corpus, forever, and a row in a holding table is
 * not one: printing the ref here would claim a resolution that does not exist.
 * The label and the version come back as two values somebody typed, which is
 * what they are.
 *
 * `pasted` comes out whole and separate, because a paste has no fields: nothing
 * in this browser reads one, `artifacts/agent_handoff.py` is the one parser and
 * it runs on the author's machine. Everything else in a paste record, including
 * its shape and when it was built, is a field like any other.
 */
export function playback(row) {
  const record = (row && row.record) || {};
  const readable = record && typeof record === "object" && !Array.isArray(record)
    ? record
    : {};
  const stamped = {
    handle: (row && row.handle) ?? null,
    subject: (row && row.subject) ?? null,
  };
  const differs = [];
  for (const [field, was, inRecord] of [
    ["handle", stamped.handle, readable.author],
    ["subject", stamped.subject, readable.subject],
  ]) {
    if (typeof inRecord === "string" && inRecord !== "" && inRecord !== was) {
      differs.push({ field, stamped: was, in_record: inRecord });
    }
  }

  const flat = {};
  const groups = [];
  for (const [name, value] of Object.entries(readable)) {
    if (name === "pasted" && typeof value === "string") continue;
    if (value && typeof value === "object" && !Array.isArray(value)) {
      groups.push({ name, entries: entriesShown(value) });
    } else {
      flat[name] = value;
    }
  }

  return {
    id: (row && row.id) ?? null,
    received_at: (row && row.received_at) ?? null,
    // Read in, which never means approved. `artifacts/intake.py` says so in
    // those words and so does the schema comment: null is not yet read, and a
    // row that was refused when the author pulled it keeps a null here and
    // stays where it is.
    taken_at: (row && row.taken_at) ?? null,
    stamped,
    differs,
    pasted: typeof readable.pasted === "string" ? readable.pasted : null,
    groups: [{ name: null, entries: entriesShown(flat) }, ...groups],
  };
}

/**
 * The rows in the order they arrived, or that order reversed.
 *
 * **The only sequence a holding table has is its clock**, and this is a
 * separate function so the control on the page cannot say one thing and do
 * another. `tests/test_ordering_control.py` exists because that happened once
 * already on the corpus views: a bar that rendered, set `aria-pressed`, and had
 * no handler behind it, and then a handler that sorted on something other than
 * what the caption said.
 *
 * Nothing in the record is read. Not the label, not the layer, not whether the
 * author has read the row in, and not whether it carries a number. A row with
 * no `received_at` keeps the place it came in, because a missing clock is not a
 * reason to move somebody's row.
 */
export function inArrivalOrder(rows, { newestFirst = false } = {}) {
  const keep = Array.isArray(rows) ? [...rows] : [];
  const at = (row) => String((row && row.received_at) ?? "");
  const byClock = keep
    .map((row, index) => ({ row, index }))
    .sort((a, b) => {
      const left = at(a.row);
      const right = at(b.row);
      if (left === right || !left || !right) return a.index - b.index;
      return left < right ? -1 : 1;
    })
    .map(({ row }) => row);
  return newestFirst ? byClock.reverse() : byClock;
}

// --------------------------------------------------------------------------
// The session, which is the one thing that outlives the tab.

export const HELD_SHAPE = "controlbun.registry/held-session@1";

/** Seconds of headroom before the access token is treated as spent. */
export const RENEW_MARGIN = 60;

/** Unix seconds this access token stops being accepted, or null. */
function expiryOf(said, now) {
  const at = Number(said.expires_at);
  if (Number.isFinite(at) && at > 0) return at;
  const within = Number(said.expires_in);
  if (Number.isFinite(within)) {
    return Math.floor((now ?? Date.now()) / 1000) + within;
  }
  return null;
}

/**
 * The session, projected down to what a return visit needs and no further.
 *
 * This replaced `whoFrom`, which kept three display facts so the bar could name
 * a handle while the session died with the tab. That arrangement was honest
 * about what it held and dishonest about what it offered: the bar said **Add
 * artifact** to somebody whose session had been gone since the last reload, and
 * pressing it led to a page that could only ask them to sign in again. One key
 * holding the session and the identity together is what stops those two from
 * disagreeing, because there is no longer a second thing to disagree with.
 *
 * **What goes in, by name.** The access token, the refresh token, when the
 * access token is spent, the provider this session was made at, and the three
 * identity fields `pendingRowFrom` needs. **What does not.** `provider_token`
 * and `provider_refresh_token`, which is the whole rule: those reach a Hugging
 * Face account, Hugging Face returns them on a sign-in and never on a renewal,
 * so keeping one buys nothing and risks everything. The email on the Supabase
 * user row is not here either, for the reason `/signed-in/` gives: the address
 * exists in the identity service's own row and in no file, page or table of
 * this project's.
 *
 * A projection that names its fields cannot pick up a claim the endpoint grows
 * later, which is the same reason `captureFrom` names its fields, and it is the
 * property `tests/test_nav_account.py` checks by handing this a response
 * carrying both provider tokens.
 *
 * Refused rather than half kept when either token is missing. A record with no
 * refresh token is a session that cannot outlive the hour, and writing one
 * would put the bar back where it was: offering a way in that stops working
 * without saying when.
 */
export function heldSessionFrom(said, { provider, recordedAt, now } = {}) {
  const access = said && said.access_token;
  const refresh = said && said.refresh_token;
  if (!access || !refresh) {
    const missing = [
      access ? null : "no access token",
      refresh ? null : "no refresh token",
    ].filter(Boolean);
    throw new Refused(
      `the identity service answered with ${missing.join(" and ")}, so there ` +
        "is no session to hold and nothing was written to this browser. " +
        "Signing in again is the fix; there is nothing here to retry.",
    );
  }
  const user = (said && said.user) || {};
  const metadata = user.user_metadata || {};
  return {
    shape: HELD_SHAPE,
    recorded_at: recordedAt || nowStamp(),
    provider: provider ?? null,
    access_token: access,
    refresh_token: refresh,
    expires_at: expiryOf(said, now),
    // Shaped the way `pendingRowFrom` reads a session, so that function keeps
    // its one parameter and keeps having no parameter a token can arrive in.
    user: {
      id: user.id ?? null,
      user_metadata: {
        sub: metadata.sub ?? null,
        preferred_username: metadata.preferred_username ?? null,
      },
    },
  };
}

/**
 * Whether the access token is spent, with a minute of headroom.
 *
 * An unknown expiry counts as spent. Renewing a token that had time left costs
 * one request; using one that did not costs a person the press they had
 * already made, and the row is not written.
 */
export function accessSpent(held, { now = Date.now(), margin = RENEW_MARGIN } = {}) {
  const at = held && Number(held.expires_at);
  if (!Number.isFinite(at)) return true;
  return at - margin <= Math.floor(now / 1000);
}

/**
 * Who signed in, in the shape `submissionFrom` reads a capture in.
 *
 * A restored session carries no membership reading: that needs a Hugging Face
 * token, and this browser keeps none. So a submission built from a restored
 * session carries the session's own copy of the subject and the handle, which
 * are the values Postgres stamps the row with, and the two cannot disagree. A
 * submission built right after a sign-in carries what the userinfo endpoint
 * said a moment later, and those two can. That asymmetry is real and is the
 * reason this returns the identity rather than pretending to be a capture.
 */
export function signerFrom(held) {
  const metadata = (held && held.user && held.user.user_metadata) || {};
  return {
    provider: (held && held.provider) ?? null,
    sub: metadata.sub ?? null,
    preferred_username: metadata.preferred_username ?? null,
  };
}

/**
 * A file name to download, made of the thing it holds.
 *
 * Never a timestamp alone: two captures on one day would collide and the
 * browser would silently write `(1)`, which is a file somebody later reads as
 * the first one.
 */
export function downloadName(prefix, key, capturedAt) {
  const safe = String(key || "unnamed").replace(/[^A-Za-z0-9._-]+/g, "-");
  const when = String(capturedAt || "").replace(/[^0-9]/g, "");
  return `${prefix}-${safe}-${when}.json`;
}
