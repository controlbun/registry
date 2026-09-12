// @ts-check
import { defineConfig } from "astro/config";

// Static output, deliberately. v0 serves nothing publicly, and a build that emits
// files cannot drift into being a public surface the way a running process can.
// Pagefind runs after the build as an npm script rather than as an integration,
// which keeps the dependency a first-party binary instead of a third-party wrapper.
export default defineConfig({
  output: "static",
  build: { format: "file" },
  devToolbar: { enabled: false },
});
