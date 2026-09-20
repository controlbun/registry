// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// Static output, deliberately. A build that emits files cannot drift into being
// a public surface the way a running process can, which is the property
// `tests/test_intake.py` holds by scanning the output.
//
// The reason written here used to be "v0 serves nothing publicly", which stopped
// being true on 2026-09-20. The conclusion did not: emitting files rather than
// running a route is what makes the guard checkable at all.
// Pagefind runs after the build as an npm script rather than as an integration,
// which keeps the dependency a first-party binary instead of a third-party wrapper.
//
// format: "directory" emits about/index.html, so the URL is /about/ with no
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

  // A sitemap, because until 2026-09-20 the site had neither this nor a
  // `robots.txt` and an index had no list of what is here to read. It is
  // generated from the routes the build actually emits rather than written by
  // hand, so a page added later is in it without anybody remembering.
  //
  // **It carries no priority and no changefreq.** Both are numbers this project
  // would be inventing: nothing here knows which page matters more than another,
  // and a made-up 0.8 beside a made-up 0.5 is a ranking of our own pages
  // asserted to a stranger. Absent is the honest value and the major consumers
  // document that they ignore both anyway.
  //
  // The filter takes out the two pages that are machinery rather than reading.
  // `/signed-in/` is an OAuth return leg that means nothing without a code in
  // the query string, and `/404/` is the page a consumer lands on when it
  // follows something that is gone. Neither is content, and neither is being
  // hidden: both stay reachable and neither is disallowed anywhere.
  integrations: [
    sitemap({
      filter: (page) =>
        !page.endsWith("/signed-in/") && !page.endsWith("/404/"),
    }),
  ],
});
