"""Run a page's own ordering script and report what it does to the list.

The ordering control shipped with buttons, `aria-pressed`, an explanatory caption
and no handler. Every test we had passed, because they all asked whether the markup
was present. Presence is not behavior, and a control that looks finished and does
nothing is worse than an absent one: the reader concludes the ordering cannot be
changed rather than that it is broken.

So this executes the real script text out of the real built page, against the real
rows, in Node. No jsdom and no new dependency: the script touches a small, fixed
surface of the DOM, and that surface is shimmed here. Anything it touches that is
not shimmed throws, which is the correct outcome for an untested code path rather
than a silent pass.

Both frontends are driven through this, because they render the same control from
the same two inputs and both of them had the same dead buttons.
"""

from __future__ import annotations

import json
import re
import subprocess
from html.parser import HTMLParser

SHIM = r"""
// A DOM only as large as the ordering script actually uses. Anything else throws.
// The last three, because `node -e` does not put the script itself in argv and
// the index shifts with how the command is spelled.
const argv = process.argv.slice(-3);
const spec = JSON.parse(argv[0]);
const script = argv[1];
const clicks = JSON.parse(argv[2]);

class El {
  constructor(node) {
    this.tag = node.tag;
    this.attrs = node.attrs || {};
    this.dataset = {};
    for (const [k, v] of Object.entries(this.attrs)) {
      if (k.startsWith("data-")) {
        const name = k.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
        this.dataset[name] = v;
      }
    }
    this.children = (node.children || []).map((c) => new El(c));
    this.id = node.id;
    this.textContent = node.text || "";
  }
  setAttribute(k, v) { this.attrs[k] = v; }
  getAttribute(k) { return this.attrs[k]; }
  appendChild(el) {
    const i = this.children.indexOf(el);
    if (i !== -1) this.children.splice(i, 1);
    this.children.push(el);
  }
  addEventListener(type, fn) {
    if (type !== "click") throw new Error("unshimmed event: " + type);
    (this.listeners = this.listeners || []).push(fn);
  }
  querySelectorAll(sel) {
    if (sel !== "[data-order-key]") throw new Error("unshimmed selector: " + sel);
    return this.children.filter((c) => "orderKey" in c.dataset);
  }
  querySelector(sel) {
    // The caption element that names the active ordering. Kept narrow on purpose:
    // a shim that answers every selector would let an untested path pass here.
    if (sel !== "strong") throw new Error("unshimmed selector: " + sel);
    return this.named || null;
  }
}

const bar = spec.bar ? new El(spec.bar) : null;
if (bar) { bar.named = new El({ tag: "strong", text: spec.named }); }
const lists = spec.lists.map((l) => new El(l));

global.document = {
  querySelector(sel) {
    if (sel === ".ordering") return bar;
    throw new Error("unshimmed selector: " + sel);
  },
  querySelectorAll(sel) {
    if (sel === "[data-orderable]") return lists;
    throw new Error("unshimmed selector: " + sel);
  },
};

// Frozen so the decay denominator is identical across runs and the expected
// ordering can be computed from the same instant on the Python side.
const FIXED_NOW = spec.now;
const RealDate = Date;
global.Date = new Proxy(RealDate, {
  apply: (t, s, a) => Reflect.apply(t, s, a),
  construct: (t, a) => Reflect.construct(t, a),
  get: (t, p) => (p === "now" ? () => FIXED_NOW : Reflect.get(t, p)),
});

eval(script);

const result = { bound: bar ? (bar.children.some((c) => c.listeners)) : false,
                 orders: {} };
for (const key of clicks) {
  const button = bar.children.find((c) => c.dataset.orderKey === key);
  if (!button) { result.orders[key] = null; continue; }
  if (!button.listeners) { result.orders[key] = "unbound"; continue; }
  button.listeners.forEach((fn) => fn());
  result.orders[key] = lists.map((l) => l.children.map((c) => c.id));
  result["pressed_after_" + key] =
    bar.children.filter((c) => c.getAttribute("aria-pressed") === "true")
       .map((c) => c.dataset.orderKey);
  result["named_after_" + key] = bar.named ? bar.named.textContent : null;
}
process.stdout.write(JSON.stringify(result));
"""


class _Page(HTMLParser):
    """Pulls out just the three things the control is made of.

    A real parse rather than a regex, because the label view nests the claimant
    blocks several divs deep and getting the container's direct children wrong
    would make this harness agree with a broken page.
    """

    VOID = {"meta", "br", "hr", "img", "input", "link", "source"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.bar: dict | None = None
        self.lists: list[dict] = []
        self.scripts: list[str] = []
        self._stack: list[dict] = []
        self._collecting: dict | None = None
        self._in_script = False
        self._script = ""
        self._n = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            self._in_script, self._script = True, ""
            return
        if tag in self.VOID:
            return

        self._n += 1
        node = {"tag": tag, "attrs": a, "children": [], "text": "",
                "id": f"{tag}{self._n}"}

        if self._stack:
            self._stack[-1]["children"].append(node)
        self._stack.append(node)

        # A root worth capturing: the control itself, or a container of items.
        if self._collecting is None:
            if a.get("class") == "ordering":
                self._collecting = node
                self.bar = node
            elif "data-orderable" in a:
                self._collecting = node
                self.lists.append(node)

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
            self.scripts.append(self._script)
            return
        if tag in self.VOID:
            return
        while self._stack:
            node = self._stack.pop()
            if node is self._collecting:
                self._collecting = None
            if node["tag"] == tag:
                break

    def handle_data(self, data):
        if self._in_script:
            self._script += data
        elif self._stack:
            self._stack[-1]["text"] += data


def _flatten_bar(bar: dict) -> dict:
    """The buttons may be wrapped; the shim wants them as direct children."""
    buttons: list[dict] = []

    def walk(node):
        for child in node["children"]:
            if "data-order-key" in child["attrs"]:
                buttons.append(child)
            walk(child)

    walk(bar)
    return {"tag": "div", "attrs": {}, "children": buttons, "text": "",
            "id": "bar"}


def ordering_script(html: str) -> str:
    """The one script that drives the control, and only that one.

    A page carries several unrelated scripts. Picking by content rather than by
    position means this keeps working when one is added above it.
    """
    page = _Page()
    page.feed(html)
    found = [s for s in page.scripts if "data-orderable" in s]
    if len(found) != 1:
        raise AssertionError(
            f"expected exactly one ordering script, found {len(found)}"
        )
    return found[0]


def run(html: str, clicks: list[str], now_ms: int) -> dict:
    """Click each named ordering and report the resulting item order."""
    page = _Page()
    page.feed(html)
    if page.bar is None:
        raise AssertionError("no ordering control on the page")

    spec = {
        "bar": _flatten_bar(page.bar),
        "lists": page.lists,
        "now": now_ms,
        "named": named_order(html),
    }
    proc = subprocess.run(
        ["node", "-e", SHIM, "--", json.dumps(spec),
         ordering_script(html), json.dumps(clicks)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(f"ordering script failed in Node:\n{proc.stderr}")
    return json.loads(proc.stdout)


def items(html: str) -> list[list[dict]]:
    """Every orderable container's direct children, with their ordering keys."""
    page = _Page()
    page.feed(html)
    return [
        [
            {
                "id": c["id"],
                "created": c["attrs"].get("data-created"),
                "engagement": c["attrs"].get("data-engagement"),
                "text": _text(c),
            }
            for c in lst["children"]
        ]
        for lst in page.lists
    ]


def _text(node: dict) -> str:
    return re.sub(r"\s+", " ", " ".join(_walk(node))).strip()


def _walk(node: dict) -> list[str]:
    out = [node["text"]]
    for c in node["children"]:
        out += _walk(c)
    return out


def bar_choices(html: str) -> list[str]:
    page = _Page()
    page.feed(html)
    if page.bar is None:
        return []
    return [b["attrs"]["data-order-key"] for b in _flatten_bar(page.bar)["children"]]


def named_order(html: str) -> str:
    """The ordering the caption claims is applied."""
    page = _Page()
    page.feed(html)
    if page.bar is None:
        return ""
    for node in _descend(page.bar):
        if node["tag"] == "strong":
            return node["text"].strip()
    return ""


def button_names(html: str) -> dict[str, str]:
    """Each ordering key and the label the reader sees on its button."""
    page = _Page()
    page.feed(html)
    if page.bar is None:
        return {}
    return {
        b["attrs"]["data-order-key"]: _text(b)
        for b in _flatten_bar(page.bar)["children"]
    }


def _descend(node: dict):
    for child in node["children"]:
        yield child
        yield from _descend(child)
