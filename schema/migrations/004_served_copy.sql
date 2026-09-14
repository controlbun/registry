-- 004_served_copy.sql
--
-- Where an artifact can be fetched from, split into two things that are not the
-- same thing.
--
-- `artifact_repo` and `artifact_commit` already exist in 001 and record where the
-- **author** published it. That is provenance. It is never rewritten, never
-- replaced by our copy, and it stays correct even after we stop serving.
--
-- What this adds is where **we** serve a copy from, when we serve one. Two
-- columns rather than reusing the first pair, because the difference is the whole
-- point: a reader has to be able to see that the bytes they got came from us and
-- where the author actually put them, and to notice when those two disagree. One
-- pair of columns cannot express a mirror that drifted from its origin.
--
-- Both are NULL today and will stay NULL until there is a dual-use policy. Serving
-- a copy makes this a distributor rather than an index, and "we only pointed at it"
-- stops being available as an answer, so the first artifact whose rights are
-- resolved is the artifact that needs the policy to already exist.
--
-- Neither is an eval result, so NOT NULL would be permitted by the invariant. They
-- are nullable anyway, because absence is the normal state: most artifacts will be
-- pointed at rather than held, and "we do not serve this" is a fact about rights
-- and size rather than a gap in the record.

ALTER TABLE intervention ADD COLUMN served_repo TEXT;
ALTER TABLE intervention ADD COLUMN served_commit TEXT;

-- Resolution is by commit SHA for the same reason 001 gives for the author's
-- copy: a branch or tag is movable by whoever owns the repo, and a pin that can
-- move is not a pin. A fetch without a commit is a fetch of whatever is there
-- today, which is exactly what `author/label@version` promises not to be.
--
-- Recording the path separately is unnecessary: our copy keeps the author's
-- filename, so `artifact_path` resolves against whichever repo is being used.
