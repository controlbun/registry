"""Every internal link resolves to a page that was built.

A 404 on your own site is a specific kind of failure: it says the page thought
something existed, which is a claim about the corpus rather than a broken button.
`/carol/` shipped that way for days. carol ran the only attack in the fixture
corpus and owned an eval suite, and her name was linked from the page her attack
appears on, and there was no page at the other end, because an owner existed only
if they had published an artifact.

Nothing in the suite could catch it. The invariant tests read source, the page
tests read one page at a time, and the falsifier re-derives numbers. None of them
follow a link.

Importable as a module so `falsifier/verify.py` can fold the result into its own
report, and runnable on its own:

    .venv/bin/python falsifier/links.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "astro" / "dist"

# Only root-relative links are ours to resolve. An external URL is somebody else's
# uptime and checking it would make the build depend on the network.
HREF = re.compile(r'href="(/[^"]*)"')


def built_pages(dist: Path) -> set[str]:
    """Every URL the build actually produced, in clean-URL form."""
    urls = set()
    for p in dist.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(dist).as_posix()
        if rel.endswith("/index.html"):
            urls.add("/" + rel[: -len("index.html")])
        elif rel == "index.html":
            urls.add("/")
        else:
            # Assets are linked directly and resolve by exact path.
            urls.add("/" + rel)
    return urls


def broken_links(dist: Path = DIST) -> dict[str, set[str]]:
    """Link target -> the pages that link to it, for targets that do not exist."""
    pages = built_pages(dist)
    broken: dict[str, set[str]] = {}

    for p in sorted(dist.rglob("index.html")):
        rel = p.relative_to(dist).as_posix()
        source = "/" + rel[: -len("index.html")] if rel.endswith("index.html") else "/" + rel
        for href in HREF.findall(p.read_text()):
            # A fragment or query is a target on a page, not another page.
            target = href.split("#")[0].split("?")[0]
            if not target:
                continue
            if target not in pages:
                broken.setdefault(target, set()).add(source)
    return broken


def main() -> int:
    if not DIST.exists():
        print("no built site; run `make site` first", file=sys.stderr)
        return 1

    broken = broken_links()
    if broken:
        print(f"links: {len(broken)} target(s) do not resolve\n", file=sys.stderr)
        for target, sources in sorted(broken.items()):
            print(f"  {target}", file=sys.stderr)
            for s in sorted(sources):
                print(f"      linked from {s}", file=sys.stderr)
        print(
            "\nA link to a page that was never built tells the reader something "
            "exists when it does not.",
            file=sys.stderr,
        )
        return 1

    pages = len(list(DIST.rglob("index.html")))
    print(f"links: every internal link resolves, across {pages} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
