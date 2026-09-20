/**
 * The session this browser keeps, and the only file that writes it.
 *
 * Premise, restated because a premise stated in one file gets violated in every
 * other one: **plurality is the product; the registry never designates,
 * consumers pin, visibly.** Holding a session confers no standing. It decides
 * which door the bar names first and decides nothing about who may open one.
 *
 * ## Why this file exists at all
 *
 * It was three functions inside `/signed-in/` while that page was the only one
 * that could hold a session. `/submit/` is a second page that has to restore
 * one, renew it and drop it, and a second copy of those three would be a second
 * set of rules for the same key: one page renewing and the other assuming, one
 * page deleting a refused session and the other keeping it. The property that
 * mattered was **one function writes the key**, and moving it here is how that
 * property survives there being two pages rather than one.
 *
 * ## What may be written, by name
 *
 * `keep` takes what a token endpoint answered and writes `heldSessionFrom`'s
 * projection of it, never the answer. So there is no call site that can hold a
 * literal it assembled itself, which is how the Hugging Face `provider_token`
 * or the email on the Supabase user row would arrive in a reader's browser.
 * That token is the one credential here that is never written anywhere in any
 * form: it reaches a Hugging Face account, and Hugging Face returns it on the
 * sign-in itself and never on a renewal, so keeping it would buy nothing past
 * its expiry.
 *
 * ## No DOM here
 *
 * Every function is storage, arithmetic or one request. What a reader is told
 * about each state is the page's, because the two pages are telling somebody
 * about different things: one is finishing a sign-in and the other is holding a
 * record they have not sent yet.
 */

import { accessSpent, heldSessionFrom, Refused } from "./handshake.mjs";
import { refreshSession } from "./hub.mjs";

/**
 * The one key, and the one thing in this project that writes it.
 *
 * `SiteNav.astro` and `Head.astro` read it and never write it, and they spell
 * it out rather than importing this, because both of those ship inline and
 * unbundled so the bar decides before first paint.
 */
export const HELD = "controlbun.session";

/** Every page that holds the session hears about a change, including this tab. */
function announce() {
  window.dispatchEvent(new Event("controlbun:session"));
}

/**
 * Write the session. The only call into storage for it anywhere.
 *
 * Takes the endpoint's answer rather than a record, so the projection cannot be
 * skipped by a caller that built its own object.
 */
export function keep(said, { provider } = {}) {
  const held = heldSessionFrom(said, { provider });
  localStorage.setItem(HELD, JSON.stringify(held));
  announce();
  return held;
}

/** The session is gone. Said in one place, so the bar cannot disagree. */
export function forget() {
  localStorage.removeItem(HELD);
  announce();
}

/**
 * What this browser kept, or null.
 *
 * A record with no refresh token is not restored: it names somebody and cannot
 * renew, which is the state the bar used to offer a way in on.
 */
export function restore() {
  let held = null;
  try {
    held = JSON.parse(localStorage.getItem(HELD) || "null");
  } catch (unreadable) {
    return null;
  }
  return held && held.access_token && held.refresh_token ? held : null;
}

/**
 * What to say when a session came back and could not be renewed.
 *
 * One sentence for both pages. A refusal is a state and not an error: the
 * reader did nothing wrong, and there is exactly one thing to do about it.
 */
export function staleSaid(problem) {
  return (
    "The session this browser kept could not be renewed, so it has been " +
    "deleted here and nothing was sent. The identity service said: " +
    `${problem.message ?? problem} ` +
    "That is what a session signed out somewhere else looks like, or one " +
    "left longer than the identity service keeps one. It is " +
    "not a failure of anything you typed. " +
    "Signing in again is the whole of the fix. It leaves this page, so take " +
    "the copy first if you have built a record."
  );
}

/**
 * The session a page load starts with, and which of four things happened.
 *
 * Returned rather than rendered, because the two pages say different things
 * about the same four answers. `none` is nobody signed in here, `held` is a
 * session with time left, `renewed` is one whose access token was spent and
 * was replaced just now, and `stale` is one the identity service refused,
 * which is deleted before this returns.
 */
export async function resume(supabaseUrl, key, { provider } = {}) {
  const kept = restore();
  if (!kept) return { state: "none", held: null };
  if (!accessSpent(kept)) return { state: "held", held: kept };
  try {
    const said = await refreshSession(supabaseUrl, key, {
      refreshToken: kept.refresh_token,
    });
    return { state: "renewed", held: keep(said, { provider }) };
  } catch (problem) {
    forget();
    return { state: "stale", held: null, problem };
  }
}

/**
 * The session, renewed if the access token is spent, or a refusal.
 *
 * Called before the one request that needs it rather than on a timer, because a
 * page left open for an hour and a page opened tomorrow are the same problem
 * and this is the only place either of them is felt. Renewing is a request;
 * re-authorizing is a redirect, and a redirect from a page holding a record
 * somebody typed takes the record with it.
 *
 * `onStale` is how the page says what happened in its own words before the
 * throw, so a caller never has to guess at the state from the message.
 */
export async function usable(supabaseUrl, key, { provider, held, onStale } = {}) {
  if (!held) {
    throw new Refused(
      "there is no session in this browser, so there is nothing to send " +
        "with. Sign in again and nothing was sent in the meantime.",
    );
  }
  if (!accessSpent(held)) return held;
  try {
    const said = await refreshSession(supabaseUrl, key, {
      refreshToken: held.refresh_token,
    });
    return keep(said, { provider });
  } catch (problem) {
    forget();
    if (onStale) onStale(problem);
    throw new Refused(
      "this session could not be renewed, so nothing was sent. What went " +
        "wrong is above; the record you built is still on this page and the " +
        "button beside it still downloads a copy.",
    );
  }
}
