"""Run the home page's own picker script and report what the combobox does.

Same argument as `ordering_harness.py`, and the same failure it exists to catch.
The ordering control shipped with buttons, `aria-pressed`, a caption explaining
itself, and no handler bound. Every test passed, because they all asked whether
the markup was present. A type-ahead is worse in that respect than a button: it
has no resting appearance to be wrong, so a field whose popup never opens looks
exactly like a field nobody clicked.

So this executes the real script text out of the real built page, against the
real datalist, in Node. No jsdom and no new dependency. The DOM here is only as
large as the picker script actually uses, and anything it touches that is not
shimmed throws, which is the right outcome for an untested code path rather than
a silent pass.

The picker is enhancement over `<input list>` plus `<datalist>`, so two separate
things are worth asking and only one of them needs this file:

  * what the page hands a reader with no JavaScript, which is in the HTML and is
    read there, and
  * what the script makes of it, which is only observable by running it.
"""

from __future__ import annotations

import json
import subprocess
from html.parser import HTMLParser

# Ids the script reaches for, so the shim only has to build these. Missing one
# is not silently tolerated: `combobox()` returns early when an element is
# absent, and the tests assert the listbox exists afterwards.
WATCHED = (
    "pick-kind", "pick-label", "pick-need", "answer", "pick-status",
    "pick-kind-field", "pick-label-field", "kinds", "labels",
)

SHIM = r"""
// A DOM only as large as the picker script uses. Anything else throws. The last
// three arguments, because `node -e` does not put the script itself in argv and
// the index shifts with how the command is spelled.
const argv = process.argv.slice(-3);
const spec = JSON.parse(argv[0]);
const script = argv[1];
const steps = JSON.parse(argv[2]);

// Every element with an id, whether it came from the page or was built by the
// script. Registering on assignment is what lets a test look up a row by the id
// that `aria-activedescendant` points at, which is the only way to check that
// the attribute names something real rather than a plausible string.
const byId = {};

const EVENTS = new Set(["input", "change", "click", "keydown", "blur", "mousedown"]);

class El {
  constructor(tag, attrs) {
    this.tag = tag;
    this.attrs = Object.assign({}, attrs || {});
    this.children = [];
    this.listeners = {};
    this.own = "";
    this.className = this.attrs.class || "";
    this.hidden = false;
    this.scrolled = 0;
    this.value = this.attrs.value === undefined ? "" : this.attrs.value;
    this.size = this.attrs.size === undefined ? 0 : Number(this.attrs.size);
    if (this.attrs.id) byId[this.attrs.id] = this;
  }
  get id() { return this.attrs.id || ""; }
  set id(v) { this.attrs.id = v; byId[v] = this; }
  get textContent() {
    return this.own + this.children.map((c) => c.textContent).join("");
  }
  set textContent(v) { this.children = []; this.own = String(v); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k] === undefined ? null : this.attrs[k]; }
  removeAttribute(k) { delete this.attrs[k]; }
  appendChild(el) {
    const at = this.children.indexOf(el);
    if (at !== -1) this.children.splice(at, 1);
    this.children.push(el);
    return el;
  }
  replaceChildren(...nodes) { this.children = nodes; }
  addEventListener(type, fn) {
    if (!EVENTS.has(type)) throw new Error("unshimmed event: " + type);
    (this.listeners[type] = this.listeners[type] || []).push(fn);
  }
  scrollIntoView() { this.scrolled += 1; }
  // Only the popup measures itself, and only to decide which edge to hang from.
  // The number comes from the spec so a test can put the popup off the right of
  // the viewport without laying anything out.
  getBoundingClientRect() {
    return { left: 0, top: 0, bottom: 0, width: 0, height: 0,
             right: spec.popup_right };
  }
}

for (const node of spec.nodes) {
  const el = new El(node.tag, node.attrs);
  el.own = node.text || "";
  for (const child of node.children || []) el.appendChild(new El(child.tag, child.attrs));
}

global.document = {
  getElementById(id) { return byId[id] || null; },
  createElement(tag) { return new El(tag, {}); },
  querySelector(sel) { throw new Error("unshimmed selector: " + sel); },
  querySelectorAll(sel) { throw new Error("unshimmed selector: " + sel); },
};
global.window = { innerWidth: spec.viewport };

eval(script);

function fire(el, type, event) {
  if (!el) throw new Error("no such element for " + type);
  let defaulted = true;
  const ev = Object.assign({ preventDefault() { defaulted = false; } }, event || {});
  (el.listeners[type] || []).forEach((fn) => fn(ev));
  return defaulted;
}

const trace = [];
for (const step of steps) {
  const el = byId[step.on];
  if (step.do === "type") {
    el.value = step.value;
    trace.push({ step: step, prevented: !fire(el, "input", {}) });
  } else if (step.do === "key") {
    trace.push({ step: step, prevented: !fire(el, "keydown", { key: step.key }) });
  } else if (step.do === "click") {
    trace.push({ step: step, prevented: !fire(el, "click", {}) });
  } else if (step.do === "blur") {
    trace.push({ step: step, prevented: !fire(el, "blur", {}) });
  } else if (step.do === "choose") {
    // What a pointer does to a row: mousedown, which must be cancelled or the
    // input blurs and the popup closes before the click lands, then click.
    const row = el.children[step.index];
    if (!row) throw new Error("no row " + step.index + " in " + step.on);
    const held = !fire(row, "mousedown", {});
    fire(row, "click", {});
    trace.push({ step: step, prevented: held });
  } else if (step.do === "select") {
    el.value = step.value;
    trace.push({ step: step, prevented: !fire(el, "change", {}) });
  } else {
    throw new Error("unshimmed step: " + step.do);
  }
}

function report(inputId) {
  const input = byId[inputId];
  const listId = input.getAttribute("aria-controls");
  const listbox = listId ? byId[listId] : null;
  return {
    value: input.value,
    size: input.size,
    role: input.getAttribute("role"),
    expanded: input.getAttribute("aria-expanded"),
    controls: listId,
    autocomplete: input.getAttribute("aria-autocomplete"),
    active: input.getAttribute("aria-activedescendant"),
    // Removed on enhancement, so the browser does not draw its own popup under
    // this one. Still null-checked rather than assumed.
    list: input.getAttribute("list"),
    listbox: listbox === null ? null : {
      id: listbox.id,
      hidden: listbox.hidden,
      role: listbox.getAttribute("role"),
      label: listbox.getAttribute("aria-label"),
      cls: listbox.className,
      options: listbox.children.map((li) => ({
        id: li.id,
        role: li.getAttribute("role"),
        selected: li.getAttribute("aria-selected"),
        cls: li.className,
        text: li.textContent,
        value: li.children[0] ? li.children[0].textContent : "",
        note: li.children[1] ? li.children[1].textContent : "",
        hit: hitOf(li),
        scrolled: li.scrolled,
      })),
    },
  };
}

function hitOf(li) {
  const val = li.children[0];
  if (!val) return "";
  const bold = val.children.filter((c) => c.className === "hit");
  return bold.map((c) => c.textContent).join("");
}

process.stdout.write(JSON.stringify({
  fields: { "pick-kind": report("pick-kind"), "pick-label": report("pick-label") },
  answer: byId["answer"].textContent,
  status: byId["pick-status"] ? byId["pick-status"].textContent : null,
  // Every id the shim knows about, which is every id the page emitted plus
  // every one the script minted. A test can assert an activedescendant resolves.
  ids: Object.keys(byId),
  trace: trace,
}));
"""


class _Picker(HTMLParser):
    """Pulls out the handful of elements the picker script reaches for.

    A real parse rather than a regex, because a datalist holding ninety-five
    options between two inputs is exactly the shape a regex gets wrong, and a
    harness that disagrees with the page about which options exist would agree
    with a broken page.
    """

    VOID = {"meta", "br", "hr", "img", "input", "link", "source", "option"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: dict[str, dict] = {}
        self.scripts: list[str] = []
        self._datalist: dict | None = None
        self._text_into: dict | None = None
        self._in_script = False
        self._script = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            self._in_script, self._script = True, ""
            return
        if tag == "option" and self._datalist is not None:
            self._datalist["children"].append({"tag": "option", "attrs": a})
            return
        node = {"tag": tag, "attrs": a, "children": [], "text": ""}
        if tag == "datalist":
            self._datalist = node
        if a.get("id") in WATCHED:
            self.nodes[a["id"]] = node
            if tag not in self.VOID:
                self._text_into = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
            self.scripts.append(self._script)
            return
        if tag == "datalist":
            self._datalist = None
        if self._text_into is not None and self._text_into["tag"] == tag:
            self._text_into = None

    def handle_data(self, data):
        if self._in_script:
            self._script += data
        elif self._text_into is not None:
            self._text_into["text"] += data


def parse(html: str) -> _Picker:
    page = _Picker()
    page.feed(html)
    return page


def picker_script(html: str) -> str:
    """The one script that drives the picker, and only that one.

    Picked by content rather than by position, so it keeps working when a script
    is added above it. The page already carries three.
    """
    found = [s for s in parse(html).scripts if "pick-kind" in s]
    if len(found) != 1:
        raise AssertionError(f"expected exactly one picker script, found {len(found)}")
    return found[0]


def suggestions(html: str, list_id: str) -> list[str]:
    """What the datalist offers, in the order the page emitted it.

    This is the no-script layer read on its own terms. The enhanced list is built
    from it, so a drift between the two is a real defect and not a detail.
    """
    node = parse(html).nodes.get(list_id)
    if node is None:
        raise AssertionError(f"no datalist #{list_id} in the page")
    return [c["attrs"].get("value", "") for c in node["children"]]


def run(html: str, steps: list[dict], viewport: int = 1024,
        popup_right: int = 0) -> dict:
    """Enhance the page in Node, drive the steps, and report what happened."""
    page = parse(html)
    missing = [i for i in WATCHED if i not in page.nodes]
    if missing:
        raise AssertionError(f"the page is missing elements the script needs: {missing}")

    spec = {
        "nodes": list(page.nodes.values()),
        "viewport": viewport,
        "popup_right": popup_right,
    }
    proc = subprocess.run(
        ["node", "-e", SHIM, "--", json.dumps(spec),
         picker_script(html), json.dumps(steps)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(f"the picker script failed in Node:\n{proc.stderr}")
    return json.loads(proc.stdout)


# ------------------------------------------------------------------ step sugar


def typing(field: str, value: str) -> dict:
    return {"do": "type", "on": field, "value": value}


def press(field: str, key: str) -> dict:
    return {"do": "key", "on": field, "key": key}


def click(field: str) -> dict:
    return {"do": "click", "on": field}


def blur(field: str) -> dict:
    return {"do": "blur", "on": field}


def choose(list_id: str, index: int) -> dict:
    return {"do": "choose", "on": list_id, "index": index}


def values(field: dict) -> list[str]:
    """The words a popup is offering, in the order it is offering them."""
    return [o["value"] for o in field["listbox"]["options"]]
