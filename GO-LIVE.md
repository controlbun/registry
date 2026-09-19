# Go live: the ordered list

Written 2026-09-19 against tip `b8d1579`. This is a runbook, not a plan. `V1.md`
section A is the plan and `DECISIONS.md` is authoritative on conflict.

## Premise, restated because this file is about mechanics

The registry never designates; consumers pin, visibly. Nothing in this runbook
changes what the site asserts. Flipping visibility and pointing DNS are transport,
and the one thing to watch is the paragraph below about what the corpus now
publishes under a real name.

## Read this first

Everything reversible is done. What is left needs the author's credentials or is
irreversible, and it is listed in the order it has to happen.

**The audit is dated, not permanent.** The entry in `minor_updates.md` covers tip
`b8d1579`. If more commits land before the flip, re-run it at the real tip on the
real day and date a new entry. `V1.md` A1 asks for the audit on the day, not the
week.

**Read "Should this stop the flip" at the bottom before starting.** Five items
there are unresolved, and the first of them stops being fixable at step 5.

---

## Already done, nothing to do

- `astro.config.mjs` has `site: "https://controlbun.com"`.
- `astro/public/CNAME` carries `controlbun.com` and reaches `astro/dist/CNAME`.
- `astro/public/.nojekyll` added 2026-09-19 and verified to reach `astro/dist/`.
  Without it, Pages runs Jekyll over a branch deploy, Jekyll drops directories
  beginning with an underscore, `_astro/` disappears and every page serves with no
  CSS and no JavaScript and no error anywhere. This was the one silent breakage.
- `artifacts/memberships.jsonl` is now gitignored, which `artifacts/seed.py`
  already claimed it was.
- `make verify` green at `b8d1579` from a clean `git archive` extract, run outside
  the working tree because another agent is mid-change in it. 32 pages, every
  internal link resolves, every published number re-derives, all proofs bind.
- Built site is 1.7 MB over 86 files. Pages allows 1 GB, a soft 100 GB per month
  and a soft 10 builds per hour.
- Canonical and link-preview tags absolute on all 32 pages, checked per page and
  not only on the home page. No `localhost` or `127.0.0.1` anywhere in the output.

---

## The sitting, in order

### 0. Commit the four paths from 2026-09-19

Left uncommitted because another agent was mid-change in the same working tree, so
the tree carries its files too. Commit these by path and nothing else:

```
git add .gitignore minor_updates.md GO-LIVE.md astro/public/.nojekyll
git commit -m "Everything reversible for going public"
```

**Check:** `git status --porcelain` still shows the other agent's changes and none
of these four.

### 1. Re-run the history audit at the real tip

Only if commits have landed since `b8d1579`. Append a dated entry to
`minor_updates.md` superseding the one there.

Split every scan. A combined expression has already exceeded a matcher's
complexity limit once, and the PEM scans in the `b8d1579` audit errored on a
pattern starting with a dash until they were rerun with `grep -e`. A scan that
errors and a scan that finds nothing print the same thing.

The check that settles it is not a pattern scan. Compare every literal value in
`.env` against every blob in history:

```
git rev-list --all --objects | cut -d' ' -f1 | sort -u \
  | git cat-file --batch-check | awk '$2=="blob"{print $1}' \
  | git cat-file --batch > /tmp/allblobs.bin
# then, per value, without echoing it:
grep -a -c -o -F -e "$value" /tmp/allblobs.bin
```

**Went wrong if:** any count is above zero, or any scan prints a usage message
instead of a number.

### 2. Decide the five items at the bottom of this file

Two are one-line decisions and two are writing. None needs credentials.

### 3. Push `main`

`origin/main` was 28 commits behind the local tip on 2026-09-19. The pre-push hook
runs `make verify`, so a red gate blocks the push, which is the point.

```
git push origin main
```

**Check:** `git ls-remote --heads origin` shows `main` at your local tip.

**Went wrong if:** the hook fails. Do not use `--no-verify`. A locally built
`astro/dist` is the whole argument for having no hosted build, and pushing past
the gate deletes that argument.

Optional, same command family: `origin/worktree-both-labeled` is a stray branch
that would be public. `git push origin --delete worktree-both-labeled` removes it.
It is noise, not a leak; the audit covered it.

### 4. Build the deploy branch and push it

Pages serves the root of a branch, so that branch's root is the contents of
`astro/dist`, not the repo.

First time. Run from the repo root. This was tested against a scratch clone on
2026-09-19 and staged 86 files, exactly the contents of `astro/dist`, with no
repo file left behind.

```
make verify                                  # rebuilds astro/dist and gates it
SHA=$(git rev-parse --short HEAD)
git worktree add --detach /tmp/pages
cd /tmp/pages
git checkout --orphan gh-pages
git rm -rf . >/dev/null
cp -R /Users/sohampadia/workspace/registry/astro/dist/. .
git add -A && git commit -m "Deploy $SHA"
git push -u origin gh-pages
```

Every deploy after that:

```
make verify
SHA=$(git rev-parse --short HEAD)
cd /tmp/pages && git rm -rf . >/dev/null
cp -R /Users/sohampadia/workspace/registry/astro/dist/. .
git add -A && git commit -m "Deploy $SHA" && git push origin gh-pages
```

`cp -R dist/.` and not `dist/*`, so the dotfile comes with it. An orphan branch
and `git rm -rf .` rather than a reset, so the branch root is the built site and
nothing else: no `.gitignore` from `main` reaching over to ignore `astro/dist`,
no stale page surviving a rename.

**Check, before pushing:** `ls -a /tmp/pages` shows `CNAME`, `.nojekyll`,
`index.html`, `404.html` and `_astro/`.

**Went wrong if:** `.nojekyll` or `CNAME` is missing. GitHub's own docs warn that
generators which force push over a publishing source overwrite the `CNAME` file
Pages added. Here both files come from `astro/public/` and are rebuilt every time,
which is why they live in version control rather than in a dashboard.

### 5. Flip the repository public

**Irreversible in the sense that matters.** Every commit and every branch becomes
readable, and cloning it takes seconds. Visibility can be flipped back; a clone
cannot.

`github.com/controlbun/registry` -> Settings -> General -> Danger Zone -> Change
visibility -> Public.

This comes before Pages, not after. GitHub's docs: "If the account that owns the
repository uses GitHub Free or GitHub Free for organizations, the repository must
be public."

**Check:** open the repo in a logged-out browser.

### 6. Enable Pages on the branch

Settings -> Pages -> Source: Deploy from a branch -> Branch `gh-pages`, folder
`/ (root)` -> Save.

**Check:** Settings -> Pages shows a deployment, and the Custom domain field has
filled itself in with `controlbun.com`. Pages reads that from the `CNAME` file in
the branch root, which is why nothing is typed into a dashboard here.

Do not expect `controlbun.github.io/registry/` to serve the site at this point.
Once the custom domain is set, that URL redirects to `controlbun.com`, which does
not point at GitHub until step 8. A redirect to a page that does not load is the
expected state between step 6 and step 9, not a failure.

**Went wrong if:** no deployment appears at all. The publishing source has to
exist and have been pushed by an admin with a verified email address.

### 7. Verify the domain at the org, before pointing DNS

Organization Settings -> Pages -> Add a domain -> `controlbun.com`. GitHub shows a
TXT record to create.

At Porkbun, add:

| Type | Host                                   | Value                    |
|------|----------------------------------------|--------------------------|
| TXT  | `_github-pages-challenge-controlbun`   | the value GitHub displays |

Full record name is `_github-pages-challenge-controlbun.controlbun.com`. Porkbun's
Host field takes the part before the domain.

Wait, confirm with `dig +short TXT _github-pages-challenge-controlbun.controlbun.com`,
then return to GitHub and click Verify.

**Why before DNS:** verification is what stops somebody else pointing their Pages
site at this domain if the repo is ever deleted, downgraded or unlinked. GitHub
also recommends adding the custom domain before configuring DNS, for the same
takeover reason.

### 8. Point DNS at Porkbun

**Current state, as of 2026-09-19.** The apex has three A records at
`207.207.210.23`, `.36` and `.50`, and `www` is a CNAME to `uixie.porkbun.com`.
Both are Porkbun's parking page. **Delete them.** There are no AAAA records and no
CAA record, so nothing blocks Let's Encrypt.

Then add, at the apex, all eight:

| Type | Host    | Value                 |
|------|---------|-----------------------|
| A    | (blank) | `185.199.108.153`     |
| A    | (blank) | `185.199.109.153`     |
| A    | (blank) | `185.199.110.153`     |
| A    | (blank) | `185.199.111.153`     |
| AAAA | (blank) | `2606:50c0:8000::153` |
| AAAA | (blank) | `2606:50c0:8001::153` |
| AAAA | (blank) | `2606:50c0:8002::153` |
| AAAA | (blank) | `2606:50c0:8003::153` |

And for `www`:

| Type  | Host  | Value                  |
|-------|-------|------------------------|
| CNAME | `www` | `controlbun.github.io` |

`controlbun.github.io` and not `controlbun.github.io/registry`. The target is the
org's Pages domain with no repository path.

Source for all of it: GitHub's "Managing a custom domain for your GitHub Pages
site", fetched 2026-09-19, not recalled. GitHub recommends setting up `www`
alongside an apex domain because A records break if GitHub's IPs change and a
CNAME does not, and GitHub creates the redirects between the two automatically
once both resolve.

**Check:**

```
dig +short controlbun.com A          # the four 185.199.x.153
dig +short controlbun.com AAAA       # the four 2606:50c0:800x::153
dig +short www.controlbun.com CNAME  # controlbun.github.io.
```

**Went wrong if:** a parking record survives. A stale `207.207.210.x` in the set
means some requests reach Porkbun and some reach GitHub, which looks like an
intermittent outage rather than a DNS mistake.

### 9. Wait for HTTPS, then check it before telling anyone

Pages requests a Let's Encrypt certificate once DNS resolves. GitHub documents
that **Enforce HTTPS can take up to 24 hours to become available**. In practice it
is usually well under that, but 24 hours is the number to plan against.

Settings -> Pages -> tick **Enforce HTTPS** once it is no longer greyed out.

**Check:**

```
curl -sI https://controlbun.com/ | head -1          # 200
curl -sI http://controlbun.com/ | head -2           # 301 to https
curl -sI https://www.controlbun.com/ | head -2      # 301 to the apex
curl -s https://controlbun.com/ | grep -c '_astro'  # above zero
```

That last one is the Jekyll check. If it returns zero, `.nojekyll` did not make it
into the deploy branch and the site is serving unstyled.

Then open `https://controlbun.com/about/` and confirm the canonical tag reads
`https://controlbun.com/about/`. Checking one page is what missed this class of
bug before.

**Went wrong if:** a certificate warning. Usually means DNS had not fully
propagated when Pages asked, and removing and re-adding the custom domain in
Settings -> Pages triggers a fresh request.

### 10. Name holds, same sitting

The trigger is the name going public, which is step 5, not the DNS. `V1.md` A4 and
the 2026-09-13 entry both key off that event.

**PyPI.** There is no name reservation. Pre-registration was removed with
Warehouse, so holding `controlbun` means uploading a distribution. Two facts that
constrain the choice: deletion is permanent and irreversible, and a filename can
never be reused even after a project is deleted and recreated. So the version
number spent on the hold is spent forever.

`registry` on PyPI is taken by an unrelated "Windows registry API" at 0.4.2, so the
distribution name has to be `controlbun` while `pyproject.toml` still says
`registry`. Distribution name and import name differing is ordinary.

**The smallest honest thing to publish** is a package that says what it is and
does nothing else: distribution `controlbun`, version `0.0.0`, a one-line summary
along the lines of "Name held for controlbun.com. No functionality yet." and a
module whose only import-time behavior is to point at the site. No scores, no
fixtures, no vendored artifacts, nothing that could be mistaken for the client.
The rule against fabricated numbers applies to a placeholder exactly as it applies
to a README.

**npm is different and the plan needs changing.** npm's disputes policy says it is
"against npm's Terms of Use to publish a package, register a username or an
organization name simply for the purposes of reserving it for future use", and
that "package names are considered squatted if the package has no genuine
function". The same sentence covers organization names, so taking the `controlbun`
scope as a hold is covered too. There is no JavaScript deliverable planned here.
The honest options are to skip npm until there is one, or to publish something
that genuinely functions. Publishing an empty placeholder is the one option that
is written down in `V1.md` and is the one npm forbids.

**Trademark, and the two entries disagree about when.** The 2026-09-13 entry sets
a trigger rather than a date: "file before `controlbun` appears anywhere public
with real traffic". `V1.md` A4 reads it as the flip starting a roughly one-month
clock rather than ending it. The reconciling words are "with real traffic", and a
site nobody has been told about does not have any, so the two are compatible as
long as the filing lands before the first time this is shown to anyone. Treat
announcing it, not flipping it, as the deadline.

Section 1(b), classes 009 and 042, $700 at filing and $300 later, goods
descriptions picked through the ID Manual selector rather than typed, because the
free-form box adds $200 per class.

---

## Should this stop the flip

Five items. None is a security hole. Two are one-line decisions and two are the
author's writing. The first one has a closing window and the rest do not.

**1. A cluster allocation path is in the tracked tree and in history, and the
window to remove it closes at step 5.** `minor_updates.md` carries
`/work/neu/<allocation-id>/...` inside the 2026-09-19 entry that certifies the path
is not tracked. Quoting it to say it is absent is what put it there. It is in two
reachable blobs, on `cbd207d` and `4abd755`, so editing the working tree would not
remove it. It is not a credential, grants no access, and discloses an allocation
id beside an affiliation the same file already names. The decision is to accept it
or to rewrite history, and a rewrite is cheap now, with one remote and one clone,
and impossible after the repo is public and cloned. Accepting it is defensible.
Discovering it afterwards is not.

**2. There is no LICENSE file.** A public repo with no license is all rights
reserved by default, which is the opposite of what a registry built on reuse and
plurality is claiming. `pyproject.toml` has no `license` field either, and PyPI
metadata will carry that absence. This is the one item that argues for a short
delay rather than a decision in the moment, because it is legal and because the
project audits other people's licenses in public.

**3. The README says "Private."** It is the first thing a visitor reads on the
public repo and it will be false the moment step 5 completes. It also describes the
repo as "Design docs", which has been wrong since there was a working site. Prose,
so it is the author's. The structural requirement is only that it says what the
thing is, that it links to `controlbun.com`, and that it stops saying private.

**4. `/about/` still carries the accuracy defect recorded on 2026-09-16.** It lists
"a causal test against norm-matched random directions" among the evidence for the
pro-human direction. `VALIDATION.md` says that test is "confirmed for +d ... with
the -d half withdrawn", dated 2026-08-27 as estimator-dependent. Half of that test
was retracted and the page states the whole of it, in a list whose job is to say
the direction carries more evidence than most. It was deferred while the site was
private. Step 5 publishes it under the author's name on the page that signs the
project.

**5. `CLAUDE.md` contains its own deletion instruction.** The repo section says the
repo is "Private as of 2026-09-19" and instructs: "Delete this paragraph and the
qualifier above when the repo is actually public, and not before." That is now a
step, and it is left here rather than done because another agent is editing that
file. Editing `CLAUDE.md` invalidates no manifest that matters, per the 2026-09-12
entry, but the change belongs in its own commit.

**Not blocking, recorded so it is not rediscovered.** The dual-use override is
knowing and is recorded in `V1.md`. What going public adds is that `BRIEF.md` and
`VALIDATION.md` become readable, and both carry the project's own analysis of
misuse surface and refusal-removal artifacts, with no policy answering it. A reader
who finds the analysis and no answer reads that worse than a site with neither.
The site serves no weights and the one artifact URL points at a repo the author
already published, so the surface added today is zero. It is the asymmetry between
the analysis and the silence that is the cost, and the mitigation is one page
whenever it is wanted.

**Also not blocking.** The license audit flags four weak-copyleft build
dependencies: two `@img/sharp` platform binaries under LGPL-3.0-or-later and
`lightningcss` under MPL-2.0. None ships in `astro/dist`, which is the only thing
published, so nothing served carries those obligations.

**Also not blocking.** `V1.md` B3 is half done. `/about/` now reads "Built by
Soham Padia", so the site is signed, but there is still no contact route and no
outbound link anywhere on the site except the one Hub URL the real artifact points
at. Nothing links to the repo either, so a reader who wants to check the proofs in
`_attest/` has to guess where they are. That is the part of B3 the blind visitor
asked about and it is one line in a footer.
