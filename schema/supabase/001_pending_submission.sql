-- 001_pending_submission.sql
--
-- Where a submission lands between somebody pressing submit and the author
-- publishing a rebuild. Run in the Supabase SQL editor.
--
-- **This is not the corpus and it is not a queue.** The published corpus stays
-- a file in git that anyone can rebuild and diff, which is the property the
-- falsifier depends on. This table holds what strangers sent, until the author
-- reads it with the service key and writes it into the record that the build
-- replays. Nothing here is approved, rejected, ranked or ordered: there is no
-- reviewer, because the namespace is the submitter's provider handle and there
-- is no question to ask. See `DECISIONS.md` 2026-09-19 on why a review step
-- with no stated rule fills with the reviewer's taste.
--
-- **Postgres stamps the identity, the browser does not.** The record the
-- browser builds carries `subject` and `author` out of the sign-in capture, and
-- a capture that arrives as a file is a stranger's JSON: nothing downstream can
-- tell an edited one from a real one. The columns below come from the verified
-- JWT instead, and the insert policy refuses a row whose columns disagree with
-- it. So a submission cannot claim to be from somebody it is not, and the
-- author replaying it does not have to trust the file to know who sent it.
--
-- **`record` is jsonb and nothing here validates it, on purpose.** Whether the
-- bytes at the pin are what the submitter says they are is answered by
-- `controlbun.artifact.confirmed` in Python, where the bytes actually are, and
-- that comparison already exists in one place for three callers. A `CHECK`
-- listing permitted kinds or formats would be the closed-enum failure in
-- `CLAUDE.md` arriving through a schema, and this table is the last place that
-- should decide what a legitimate artifact looks like.

create table public.pending_submission (
  id           uuid        primary key default gen_random_uuid(),

  -- When it arrived here, by this server's clock. The record carries the
  -- submitter's own `submitted_at` from their machine, which is theirs to
  -- state and not a fact this table should pretend to establish.
  received_at  timestamptz not null default now(),

  -- The Supabase account. Stable and opaque, and the anchor the policies use.
  account      uuid        not null references auth.users (id) on delete cascade,

  -- What the provider said this account is. `subject` is the binding, because
  -- handles are renameable and a claim bound to one either breaks on a rename
  -- or follows the handle to whoever takes it next. `handle` is what they were
  -- called on the day, recorded for display and never looked up by.
  subject      text        not null,
  handle       text        not null,

  -- The submission as the browser built it, shape and all.
  record       jsonb       not null,

  -- Set by the author, with the service key, when the row has been written
  -- into the tracked record. Null means not yet read, not "not yet approved".
  taken_at     timestamptz
);

alter table public.pending_submission enable row level security;

-- Insert as yourself and as nobody else. The `with check` is what makes the
-- stamping real: the defaults above could be overridden by a caller passing
-- explicit values, and this refuses the row when they disagree with the JWT.
create policy "a signed-in person inserts their own submission"
  on public.pending_submission
  for insert
  to authenticated
  with check (
    account = auth.uid()
    and subject = (auth.jwt() -> 'user_metadata' ->> 'sub')
    and handle  = (auth.jwt() -> 'user_metadata' ->> 'preferred_username')
  );

-- Read your own, so the page can confirm what it sent. Nobody reads anybody
-- else's: a submission is not public until the author publishes it, and a
-- table that let strangers browse pending rows would be a second corpus with
-- none of the properties the first one has.
create policy "a signed-in person reads their own submissions"
  on public.pending_submission
  for select
  to authenticated
  using (account = auth.uid());

-- No update and no delete policy, deliberately, so neither is possible through
-- the publishable key. A submission is a statement somebody made at a time. A
-- correction is another submission, which is the same rule the corpus applies
-- to a published row: immutable once written, and a new version rather than a
-- rewrite. The service key bypasses all of this, which is how the author sets
-- `taken_at` and how they remove something if they are asked to.

comment on table public.pending_submission is
  'Submissions between sending and publishing. Not the corpus, not a queue. '
  'Identity is stamped from the JWT rather than taken from the payload.';
