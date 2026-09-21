"""Run `/submit/`'s own script against rows in the holding table and report
what it drew.

Same argument as `tests/ordering_harness.py`, which exists because a control
rendered, set `aria-pressed`, had no handler behind it, and passed every test we
had: presence is not behavior. Everything a submitter reads about a record they
sent is built by script out of a fetch, so asserting on the page's source is
asserting that the right strings exist somewhere, not that a reader sees them.

No jsdom and no new dependency. The script touches a small, fixed surface of the
DOM and that surface is shimmed here. Anything it touches that is not shimmed
throws, which is the right outcome for an untested path rather than a silent
pass. The fetch stub refuses any request that is not the read, and refuses one
that carries a method, so the harness also holds the read to being a read.

Nothing in here is a measurement and no row it is given is real. The rows come
from the tests, which build them with the same functions the page builds a
submission with.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "astro" / "src"
PAGE = SRC / "pages" / "submit.astro"

SHIM = r"""
// A DOM only as large as this page's script uses. Anything else throws.
const argv = process.argv.slice(-2);
const rows = JSON.parse(argv[0]);
const press = JSON.parse(argv[1]);

class El {
  constructor(tag, id) {
    this.tag = tag;
    this.id = id ?? "";
    this.attrs = {};
    this.dataset = {};
    this.children = [];
    this.own = "";
    this.hidden = false;
    this.className = "";
    this.listeners = [];
  }
  set textContent(value) { this.own = String(value); this.children = []; }
  get textContent() {
    return this.own + this.children.map((c) => c.textContent).join("");
  }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  getAttribute(name) { return this.attrs[name]; }
  append(...nodes) { for (const node of nodes) this.children.push(node); }
  appendChild(node) { this.children.push(node); return node; }
  replaceChildren(...nodes) { this.children = nodes; this.own = ""; }
  addEventListener(type, fn) {
    if (type !== "click") throw new Error("unshimmed event: " + type);
    this.listeners.push(fn);
  }
  querySelectorAll(sel) { throw new Error("unshimmed selector: " + sel); }
}

class TextNode {
  constructor(text) { this.own = String(text); this.children = []; this.tag = "#text"; }
  get textContent() { return this.own; }
}

// Every id the script reaches for, made on demand. A registry that answered
// only a listed set would make this harness a second copy of the page's markup,
// which is the thing that goes stale.
const byId = new Map();
function element(id) {
  if (!byId.has(id)) byId.set(id, new El("div", id));
  return byId.get(id);
}

// The two the script configures itself from, and the two it orders with.
Object.assign(element("handshake").dataset, {
  supabaseUrl: "https://shimmed.supabase.co",
  supabaseKey: "a-publishable-key-the-shim-invented",
  provider: "custom:huggingface",
});
const older = new El("button", "older");
older.dataset.newest = "false";
const newer = new El("button", "newer");
newer.dataset.newest = "true";

global.document = {
  getElementById: element,
  createElement: (tag) => new El(tag),
  createTextNode: (text) => new TextNode(text),
  querySelectorAll(sel) {
    if (sel !== "#played-order button") {
      throw new Error("unshimmed selector: " + sel);
    }
    return [older, newer];
  },
};
global.window = { addEventListener() {} };
global.location = { origin: "https://shimmed.invalid" };

// One session, shaped the way `heldSessionFrom` writes one, with an expiry far
// enough out that nothing renews and the harness makes one request.
const held = {
  shape: "controlbun.registry/held-session@1",
  recorded_at: "2026-09-20T00:00:00Z",
  provider: "custom:huggingface",
  access_token: "a-shimmed-access-token",
  refresh_token: "a-shimmed-refresh-token",
  expires_at: 4102444800,
  user: {
    id: "00000000-0000-4000-8000-00000000000a",
    user_metadata: { sub: "opaque", preferred_username: "sohampadia" },
  },
};
global.localStorage = {
  getItem: (key) => (key === "controlbun.session" ? JSON.stringify(held) : null),
  setItem() { throw new Error("the read wrote to localStorage"); },
  removeItem() { throw new Error("the read deleted the session"); },
};

const asked = [];
global.fetch = async (url, options = {}) => {
  asked.push({ url: String(url), method: options.method ?? "GET" });
  if (!String(url).includes("/rest/v1/pending_submission")) {
    throw new Error("unshimmed request: " + url);
  }
  if (options.method) {
    throw new Error("reading back used " + options.method + " rather than a read");
  }
  return {
    ok: true,
    status: 200,
    async json() { return rows; },
    async text() { return ""; },
  };
};

// SCRIPT GOES HERE

// Microtasks and a timer turn, because `ready` does not await the read: the
// form above it stays usable while it runs.
for (let i = 0; i < 40; i += 1) await new Promise((r) => setTimeout(r, 0));

if (press) {
  const button = press === "newest" ? newer : older;
  for (const fn of button.listeners) fn();
}

function describe(node) {
  if (node instanceof TextNode) return { tag: "#text", text: node.own, children: [] };
  return {
    tag: node.tag,
    id: node.id,
    class: node.className,
    attrs: node.attrs,
    hidden: node.hidden,
    text: node.own,
    children: node.children.map(describe),
  };
}

process.stdout.write(JSON.stringify({
  asked,
  list: describe(element("played-list")),
  said: element("played-said").textContent,
  none: { hidden: element("played-none").hidden },
  order: {
    hidden: element("played-order").hidden,
    now: element("played-order-now").textContent,
    pressed: {
      oldest: older.getAttribute("aria-pressed"),
      newest: newer.getAttribute("aria-pressed"),
    },
  },
}));
"""


def page_script() -> str:
    """The page's own script, with its imports pointed at the real modules."""
    blocks = re.findall(r"<script>(.*?)</script>", PAGE.read_text(), re.S)
    assert blocks, "the page ships no script"
    script = blocks[-1]
    return re.sub(
        r'from "\.\./lib/([\w.]+)"',
        lambda m: f'from "{(SRC / "lib" / m.group(1)).as_uri()}"',
        script,
    )


def render(rows: list[dict], *, press: str | None = None) -> dict:
    """What the page draws for these rows, and what it asked for to get them."""
    program = SHIM.replace("// SCRIPT GOES HERE", page_script())
    done = subprocess.run(
        ["node", "--input-type=module", "-e", program,
         json.dumps(rows), json.dumps(press)],
        capture_output=True, text=True,
    )
    if done.returncode != 0:
        raise AssertionError(done.stderr.strip())
    return json.loads(done.stdout)


def flatten(node: dict) -> str:
    """Everything a reader would read out of this node, words separated."""
    parts = [node.get("text") or ""]
    for child in node.get("children", []):
        parts.append(flatten(child))
    return " ".join(" ".join(parts).split())


def records(rendered: dict) -> list[dict]:
    return [child for child in rendered["list"]["children"]
            if child.get("class") == "played-row"]


def find(node: dict, **match) -> list[dict]:
    """Every node under this one matching every key given."""
    out = []
    if all(node.get(k) == v for k, v in match.items()):
        out.append(node)
    for child in node.get("children", []):
        out.extend(find(child, **match))
    return out
