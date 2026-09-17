// @ts-check
import { defineConfig } from "astro/config";

// Static output, deliberately. v0 serves nothing publicly, and a build that emits
// files cannot drift into being a public surface the way a running process can.
// Pagefind runs after the build as an npm script rather than as an integration,
// which keeps the dependency a first-party binary instead of a third-party wrapper.
//
// format: "directory" emits kindness/index.html, so the URL is /kindness/ with no
// extension. Every static host resolves that natively, which is why this needs no
// nginx and no rewrite rules. The cost is that the output cannot be browsed over
// file://, since a directory does not resolve to its index there. Use
// `npm run preview` or `make serve`.
export default defineConfig({
  // The canonical origin. Nothing in the build depended on this while the site
  // was unpublished, which is why it was absent; a canonical link and the
  // link-preview tags both need an absolute origin, and guessing one per page is
  // how a staging URL ends up in somebody's shared link.
  //
  // `astro/public/CNAME` carries the same domain. Pages reads that file out of
  // the published output to know which custom domain to answer on, so the two
  // have to agree and both live in version control rather than in a dashboard.
  site: "https://controlbun.com",
  output: "static",
  build: { format: "directory" },
  devToolbar: { enabled: false },
});
