// Audit every installed package's license.
//
// CLAUDE.md requires flagging copyleft, and a node tree is hundreds of packages
// deep, so this has to be checked rather than glanced at. Fails the build on
// strong copyleft, reports weak copyleft and anything unrecognised for a human to
// look at rather than silently allowing it.

import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = new URL("../node_modules", import.meta.url).pathname;

// Fails the build. Redistributing a derived work under these terms is a decision
// nobody should make by accident.
const STRONG_COPYLEFT = /\b(AGPL|GPL-[23]|GPL-\d|^GPL$|SSPL|EUPL|CDDL)\b/i;

// Reported, not fatal. File-level copyleft is usually fine for a dependency you
// do not modify, but it is a decision rather than a default.
const WEAK_COPYLEFT = /\b(LGPL|MPL-|CPL-|EPL-)/i;

const PERMISSIVE = /\b(MIT|ISC|BSD|Apache|Unlicense|0BSD|CC0|WTFPL|Python-2|BlueOak|MIT-0)\b/i;

function licenseOf(pkg) {
  if (typeof pkg.license === "string") return pkg.license;
  if (pkg.license?.type) return pkg.license.type;
  if (Array.isArray(pkg.licenses)) {
    return pkg.licenses.map((l) => l.type ?? l).join(" OR ");
  }
  return null;
}

function* packages(dir) {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir)) {
    if (entry === ".bin" || entry === ".package-lock.json") continue;
    const path = join(dir, entry);
    if (!statSync(path).isDirectory()) continue;
    if (entry.startsWith("@")) {
      yield* packages(path);
      continue;
    }
    const manifest = join(path, "package.json");
    if (existsSync(manifest)) {
      try {
        yield JSON.parse(readFileSync(manifest, "utf8"));
      } catch {
        // A package without a readable manifest is reported as unknown below.
        yield { name: entry, version: "?", license: null };
      }
    }
    yield* packages(join(path, "node_modules"));
  }
}

const strong = [];
const weak = [];
const unknown = [];
let total = 0;

for (const pkg of packages(ROOT)) {
  if (!pkg.name) continue;
  total += 1;
  const license = licenseOf(pkg);
  const label = `${pkg.name}@${pkg.version ?? "?"}  ${license ?? "(none declared)"}`;
  if (license && STRONG_COPYLEFT.test(license)) strong.push(label);
  else if (license && WEAK_COPYLEFT.test(license)) weak.push(label);
  else if (!license || !PERMISSIVE.test(license)) unknown.push(label);
}

const show = (title, rows) => {
  if (!rows.length) return;
  console.log(`\n${title} (${rows.length}):`);
  for (const r of rows.sort()) console.log(`  ${r}`);
};

console.log(`scanned ${total} installed packages`);
show("STRONG COPYLEFT, build fails", strong);
show("weak copyleft, review", weak);
show("unrecognised licence, review", unknown);

if (!strong.length && !weak.length && !unknown.length) {
  console.log("all permissive, nothing to review");
}
if (strong.length) {
  console.error("\nstrong copyleft present in the dependency tree");
  process.exit(1);
}
