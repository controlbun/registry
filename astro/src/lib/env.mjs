/**
 * The repository-root `.env`, read at build time by the pages that need it.
 *
 * Gitignored, and gitignored before the first file in this project existed.
 * Read with `node:fs` rather than through `import.meta.env`, because Astro's env
 * loading is rooted at `astro/` and the one `.env` this project has is a
 * directory up.
 *
 * **Two pages read it now, so there is one copy of the walk.** It lived in
 * `/signed-in/` while that was the only page holding a session. `/submit/`
 * needs the same two values, and a second copy of a five-level walk up the
 * tree is a second thing to get wrong in one direction only: the version that
 * finds nothing builds a page saying it cannot sign anybody in, which is a
 * quiet failure rather than a loud one.
 *
 * Neither value is a secret in the sense the client secret is. The project URL
 * is in every authorize redirect a person sees and the publishable key is the
 * one a browser is given. They are still read from an ignored file rather than
 * written into a tracked one, because a habit that distinguishes which of two
 * keys may be committed is a habit that commits the wrong one eventually. What
 * ships is the built page, which carries them by necessity.
 *
 * Found by walking up from the working directory rather than resolved against
 * this file's own URL: `import.meta.url` inside a bundled module is a module
 * path at build time and not a location on disk, which is how the first version
 * of this read nothing and reported "not configured" on a machine that had the
 * file.
 */

import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

export function fromEnv() {
  let at = resolve(process.cwd());
  for (let up = 0; up < 5; up += 1) {
    try {
      const out = {};
      for (const line of readFileSync(join(at, ".env"), "utf8").split("\n")) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
        const [key, ...rest] = trimmed.split("=");
        out[key.trim()] = rest.join("=").trim().replace(/^['"]|['"]$/g, "");
      }
      return out;
    } catch {
      const above = dirname(at);
      if (above === at) break;
      at = above;
    }
  }
  // A checkout with no `.env` builds. What it builds is a page that says it
  // cannot sign anybody in, which is the honest output of a build that was not
  // given an endpoint, rather than a button that fails on click.
  return {};
}

/** The project URL, the publishable key, and whether both are there. */
export function identityConfig() {
  const env = fromEnv();
  const url = env.SUPABASE_URL ?? "";
  const key = env.SUPABASE_PUBLISHABLE_KEY ?? "";
  return { url, key, configured: Boolean(url && key) };
}
