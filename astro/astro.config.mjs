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
  output: "static",
  build: { format: "directory" },
  devToolbar: { enabled: false },
});
