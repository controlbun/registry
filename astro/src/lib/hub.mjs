/**
 * The network hops: exchange a code for a session, ask who signed in, send the
 * submission, and, only if the person says so, put one file in their own
 * account.
 *
 * Premise, restated because a premise stated in one file gets violated in every
 * other one: **plurality is the product; the registry never designates,
 * consumers pin, visibly.** Nothing here reads a score, an ordering or a
 * ranking, and nothing here decides whether a submission is any good. The
 * table a submission lands in is not a queue: there is nothing to approve,
 * because the namespace is the handle the provider reported and there is no
 * question for a reviewer to answer.
 *
 * ## Nothing here is this site's origin
 *
 * Every function below sends data to exactly two places: the Supabase project,
 * and Hugging Face. The published site has no origin that receives, still emits
 * files and still runs no route, which is the property `astro.config.mjs` keeps
 * and `tests/test_intake.py` holds. What changed on 2026-09-20 is that the page
 * became a client, and the guard became a question about where a request is
 * aimed rather than about whether one exists at all.
 *
 * ## One of those requests now writes, and it is named
 *
 * `sendPending` inserts one row into a Supabase table this project owns. That
 * is a write to somebody else's origin on the reader's instruction and with
 * the reader's own session, and it is a real widening of what the earlier
 * version of this file said: the Supabase project was then only the code
 * exchange. The table is not the corpus and the row is not published by
 * arriving. `MAY_SEND_TO` in `tests/test_intake.py` names the destination and
 * the reason, so a third one is a test edit rather than a line that arrived.
 *
 * ## The token is used for the request it is for and never stored
 *
 * No function here writes to `localStorage`, `sessionStorage`, a cookie, a
 * field or a log line. A token is an argument, it is passed to `fetch` in one
 * header, and the frame ends. The page holds it in one local variable for the
 * length of a click and closing the tab ends it.
 *
 * ## Scope is asked for at the moment of upload
 *
 * Signing in asks for `openid email profile read-memberships`. Creating a repository
 * on somebody's behalf needs `contribute-repos`, which Hugging Face documents
 * as "Create repositories and access those created by this app. Cannot access
 * any other repositories unless additional permissions are granted." That is
 * the narrowest scope that does this job, and it is asked for in a second
 * authorization when the person chooses the offer. A reader, a namespace
 * claimant and anybody submitting a link to an already-public file is never
 * asked for it.
 *
 * ## Wire formats, read rather than remembered
 *
 * The commit and LFS hops below are the ones `huggingface_hub` 0.36.0 makes,
 * read out of the installed `hf_api.py` and `_commit_api.py` on 2026-09-20
 * rather than recalled. A `.safetensors` path is LFS on the Hub at every size,
 * which is what `/preupload/` answered for 1 KB, 200 KB and 20 MB, so the
 * three-hop LFS route is the ordinary one here and the base64 route is the
 * exception.
 */

export class HubError extends Error {}

/** A fetch whose failure says which endpoint answered and with what. */
async function ask(url, options, what) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (unreachable) {
    throw new HubError(
      `${what} could not be reached (${unreachable.message}). Nothing was ` +
        "written anywhere.",
    );
  }
  if (!response.ok) {
    // The body is read for the message and the request is not echoed back,
    // because these calls carry a token in a header and an error page can
    // reflect a request.
    const detail = (await response.text().catch(() => "")).slice(0, 400);
    throw new HubError(`${what} answered ${response.status}. ${detail}`);
  }
  return response;
}

// --------------------------------------------------------------------------
// Identity.

/**
 * The provider's own document, fetched every time and never remembered.
 *
 * So the capture says where it came from rather than being trusted to have come
 * from the right place.
 */
export async function discovery(url) {
  const document = await (await ask(url, {}, "the discovery document")).json();
  for (const key of ["issuer", "userinfo_endpoint"]) {
    if (!document[key]) {
      throw new HubError(`the discovery document at ${url} carries no ${key}`);
    }
  }
  return document;
}

/**
 * The authorization code for a session. The session is never written down.
 *
 * `provider_token` comes back on the sign-in itself and never on a refresh,
 * which is why membership has to be read now or not at all.
 */
export async function exchange(supabaseUrl, key, { code, verifier }) {
  const url = `${supabaseUrl.replace(/\/+$/, "")}/auth/v1/token?grant_type=pkce`;
  const response = await ask(
    url,
    {
      method: "POST",
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ auth_code: code, code_verifier: verifier }),
    },
    "the token exchange",
  );
  return response.json();
}

/**
 * One row into `pending_submission`, as the person who is signed in.
 *
 * **This is the one request on this site that writes to something this project
 * owns, and it is the reason the guard in `tests/test_intake.py` had to name
 * it.** The row lands in a table that is not the corpus: the published corpus
 * is a file in git, the author pulls this table into it with the service key,
 * and nothing here appears on the site until that happens and a build is
 * published. `schema/supabase/001_pending_submission.sql` carries the argument.
 *
 * **The identity on the row is stamped by Postgres and not taken from the
 * body.** The insert policy refuses any row whose `account`, `subject` or
 * `handle` disagrees with the verified JWT, which is what makes a forged
 * submission impossible rather than merely discouraged. `pendingRowFrom` in
 * `handshake.mjs` builds the body out of the session for that reason.
 *
 * `Prefer: return=representation` so the answer is the row Postgres actually
 * wrote. The receipt the submitter sees is that row and not an echo of what
 * the browser sent, which is the difference between showing a fact and showing
 * a hope.
 *
 * The access token is an argument, it goes into one header, and the frame ends.
 */
export async function sendPending(supabaseUrl, key, { accessToken, row }) {
  const url = `${supabaseUrl.replace(/\/+$/, "")}/rest/v1/pending_submission`;
  const response = await ask(
    url,
    {
      method: "POST",
      headers: {
        apikey: key,
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        Prefer: "return=representation",
      },
      body: JSON.stringify(row),
    },
    "sending the submission",
  );
  const said = await response.json();
  const written = Array.isArray(said) ? said[0] : said;
  if (!written || !written.id) {
    throw new HubError(
      "the submission was accepted and the answer carried no row, so there is " +
        "no receipt to show. Signing in again and sending once more would " +
        "make a second row rather than replacing this one, so check with the " +
        "author before you do.",
    );
  }
  return written;
}

/** What the provider says about the account holding this token, right now. */
export async function userinfo(endpoint, token) {
  const response = await ask(
    endpoint,
    { headers: { Authorization: `Bearer ${token}` } },
    "the userinfo endpoint",
  );
  return response.json();
}

// --------------------------------------------------------------------------
// The upload, which happens only when somebody asks for it.

const HUB = "https://huggingface.co";

/**
 * Create one public repository in the submitter's own namespace.
 *
 * `exist_ok` is not sent: a repository that is already there is reported as
 * such and the offer stops, because writing into a repository somebody else
 * made for another purpose is not what was agreed to.
 */
export async function createRepo(token, { namespace, name }) {
  const response = await ask(
    `${HUB}/api/repos/create`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      // `name` and `organization` as two fields, which is what
      // `huggingface_hub.create_repo` sends after splitting a repo id on the
      // slash. A personal namespace goes in `organization` the same way an
      // org's does; the Hub does not distinguish here and neither does this.
      body: JSON.stringify({
        name,
        organization: namespace,
        type: "model",
        private: false,
      }),
    },
    "creating the repository",
  );
  return response.json();
}

/** How the Hub wants this file sent: `lfs` for a tensor, `regular` for text. */
export async function uploadMode(token, repo, { path, size, sample }) {
  const response = await ask(
    `${HUB}/api/models/${repo}/preupload/main`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ files: [{ path, size, sample }] }),
    },
    "asking the Hub how to send this file",
  );
  const said = await response.json();
  const file = (said.files || []).find((f) => f.path === path);
  if (!file) {
    throw new HubError(
      `the Hub answered about ${JSON.stringify((said.files || []).map((f) => f.path))} ` +
        `rather than about ${path}, so nothing was sent.`,
    );
  }
  return file.uploadMode;
}

/**
 * The three LFS hops: ask for somewhere to put it, put it, say it is there.
 *
 * The digest here is the object id the protocol is addressed by. It is not the
 * row's `artifact_sha256`: that is derived on the machine that rebuilds the
 * corpus, from the bytes fetched back at the pin, by the one thing in this
 * project that reads bytes.
 */
export async function putLfs(token, repo, { path, bytes, oid }) {
  const batch = await ask(
    `${HUB}/${repo}.git/info/lfs/objects/batch`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/vnd.git-lfs+json",
        Accept: "application/vnd.git-lfs+json",
      },
      body: JSON.stringify({
        operation: "upload",
        transfers: ["basic"],
        hash_algo: "sha_256",
        objects: [{ oid, size: bytes.byteLength }],
      }),
    },
    "asking for somewhere to put the file",
  );
  const object = ((await batch.json()).objects || [])[0];
  if (!object) {
    throw new HubError(
      "the Hub answered with no object to upload, so nothing was sent.",
    );
  }
  if (object.error) {
    throw new HubError(
      `the Hub refused the upload: ${object.error.message || object.error.code}`,
    );
  }
  const actions = object.actions || {};
  // No action at all means the Hub already holds these exact bytes. That is a
  // success and not a failure, and saying so is better than an empty branch.
  if (actions.upload) {
    await ask(
      actions.upload.href,
      {
        method: "PUT",
        headers: actions.upload.header || {},
        body: bytes,
      },
      "storing the file",
    );
  }
  if (actions.verify) {
    await ask(
      actions.verify.href,
      {
        method: "POST",
        headers: {
          ...(actions.verify.header || {}),
          "Content-Type": "application/vnd.git-lfs+json",
        },
        body: JSON.stringify({ oid, size: bytes.byteLength }),
      },
      "confirming the file arrived",
    );
  }
  return { key: "lfsFile", value: { path, algo: "sha256", oid, size: bytes.byteLength } };
}

/** Base64 in chunks, because `String.fromCharCode` on a whole file overflows. */
function base64Of(bytes) {
  const view = new Uint8Array(bytes);
  let binary = "";
  for (let at = 0; at < view.length; at += 0x8000) {
    binary += String.fromCharCode.apply(null, view.subarray(at, at + 0x8000));
  }
  return btoa(binary);
}

/** The small-file route: the bytes travel inside the commit itself. */
export function inlineFile(path, bytes) {
  return {
    key: "file",
    value: { content: base64Of(bytes), path, encoding: "base64" },
  };
}

/**
 * One commit with one file in it, and the sha it produced.
 *
 * The sha is the point: it is what the row pins, it is content-addressed, and
 * it keeps resolving to these bytes however many times the repository moves on.
 */
export async function commit(token, repo, { entry, summary }) {
  const ndjson =
    JSON.stringify({ key: "header", value: { summary, description: "" } }) +
    "\n" +
    JSON.stringify(entry) +
    "\n";
  const response = await ask(
    `${HUB}/api/models/${repo}/commit/main`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/x-ndjson",
      },
      body: ndjson,
    },
    "making the commit",
  );
  const said = await response.json();
  const sha = said.commitOid || (said.commitUrl || "").split("/").pop();
  if (!/^[0-9a-f]{40}$/i.test(sha || "")) {
    throw new HubError(
      "the commit succeeded and the Hub did not answer with a 40-character " +
        "sha, so there is nothing to pin. The file is in the repository; the " +
        "commit it landed in is on the repository's commits page.",
    );
  }
  return sha.toLowerCase();
}

/** sha256 of what is about to be sent, as hex. The LFS object id. */
export async function digestOf(bytes) {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
