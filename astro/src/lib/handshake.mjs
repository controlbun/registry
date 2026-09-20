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
 * ## No token, ever
 *
 * Nothing here takes a token as an argument or returns one. The session and the
 * provider token live in one local variable in the page for the length of the
 * calls that need them, and no function in this file can be handed one by
 * accident because none of them has a parameter for it.
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
 * **No token crosses this function.** It takes the user object out of the
 * session and never the session, so there is no parameter a token can arrive
 * in and no branch that could put one in the body. The access token is the
 * caller's problem and it goes in a header, one function along, in `hub.mjs`.
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
// What the bar at the top is allowed to remember.

export const WHO_SHAPE = "controlbun.registry/remembered-who@1";

/**
 * Display facts, and nothing a request could be made with.
 *
 * The bar at the top ships both ways in and one of them is wrong for whoever is
 * reading. Deciding which needs something that outlives a page load, and the
 * session does not: the access token lives in one variable in one tab and is
 * gone on a reload, deliberately, and that is not moving.
 *
 * So what survives is three display facts, written here by name rather than by
 * spreading a capture. A projection that names its fields cannot pick up a
 * token when the capture grows one, which is the same reason `captureFrom`
 * names its fields, and it is the property `tests/test_nav_account.py` checks
 * by handing this a capture carrying three of them.
 *
 * **Remembering a handle is not holding a session and nothing here pretends
 * otherwise.** It changes what the bar offers and it changes nothing about what
 * anybody can do: `/signed-in/` asks for a fresh sign-in when the tab has no
 * session, and that page is reachable, linked and usable by somebody who has
 * never signed in at all.
 *
 * Null rather than a refusal when the provider named no handle. That is a real
 * state, it is the one `captureFrom` records as `preferred_username: null`, and
 * the honest reading of it is that there is nothing for the bar to show rather
 * than that something went wrong.
 */
export function whoFrom(capture) {
  const handle = capture && capture.preferred_username;
  if (!handle) return null;
  return {
    shape: WHO_SHAPE,
    handle,
    subject: capture.sub ?? null,
    recorded_at: capture.captured_at || nowStamp(),
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
