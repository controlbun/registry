"""The Python client.

Most of these check what the client refuses to do. Those refusals are the product:
a client that quietly answers "give me a label" has designated one, and it would
do so at exactly the moment a user is least likely to notice.

**Two databases.** The real corpus is five submissions by one author, so it holds
the absences well and holds no disagreement at all: nothing in it was evaluated
by anyone else, attacked, or claimed by a second person. Refusals and absences
are checked against the real rows, where they are real; the plural states are
checked against `tests/probe.py`, which builds two claimants on one word and
throws them away.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import probe
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import (  # noqa: E402
    Ambiguous, BareLabelError, NotFound, claimants, compare, load,
)

# The real corpus, spelled out once. `soham/pro-human` is four parallel takes on
# one model, and naming a version is the only reference that resolves.
REAL_MODEL = "allenai/Olmo-3-1125-32B"
REAL_REF = f"soham/{REAL_MODEL}/pro-human@meandiff"


@pytest.fixture(scope="module")
def database(tmp_path_factory):
    """The probe corpus, as a path the client can be pointed at."""
    path = tmp_path_factory.mktemp("client") / "probe.db"
    probe.build(path)
    return path


@pytest.fixture(scope="module")
def real(tmp_path_factory):
    """The real corpus, seeded the way `make site` seeds it.

    Into a temporary file, so nothing here touches `registry.db`.
    """
    path = tmp_path_factory.mktemp("client-real") / "registry.db"
    subprocess.run(
        [sys.executable, str(ROOT / "artifacts" / "seed.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return path


# --------------------------------------------------------------------------- #
# what it refuses


def test_a_bare_label_does_not_resolve(database):
    with pytest.raises(BareLabelError) as raised:
        load(probe.LABEL_A, database=database)
    message = str(raised.value)
    assert "does not resolve" in message
    assert f'compare("{probe.LABEL_A}")' in message, (
        "refusing is not enough; the error has to say where to go instead, or the "
        "next person just writes their own resolver"
    )


def test_the_refusal_survives_a_label_that_looks_namespaced(database):
    """`@v1` without an owner is still a bare label."""
    with pytest.raises(BareLabelError):
        load(f"{probe.LABEL_A}@v1", database=database)


def test_a_bare_label_is_refused_against_the_real_corpus_too(real):
    """The same refusal where one author holds the only claim on the word.

    Worth its own case since the fixtures went. `pro-human` has exactly one
    claimant, so there is an obvious answer and the client still declines to
    give it: a bare label is a view across everybody claiming it, and that is
    true of a view with one row in it. The version that resolved "while it is
    unambiguous" is the designation arriving the first day the corpus is small.
    """
    with pytest.raises(BareLabelError):
        load("pro-human", database=real)


def test_an_unmeasured_value_is_none_not_zero(real):
    """A real absence: `soham/pro-human@L24` has no transfer ratio.

    The arena ran the control-pair battery on the three layer-32 directions and
    not on this one, so there is nothing to report and nothing is reported. Its
    siblings do carry the number, which is what makes this a comparison rather
    than a claim that the client returns None for everything.
    """
    unmeasured = load(f"soham/{REAL_MODEL}/pro-human@L24", database=real)
    assert unmeasured.evidence.transfer is None
    assert unmeasured.evidence.transfer != 0
    assert unmeasured.measured("transfer") is False
    assert load(REAL_REF, database=real).measured("transfer") is True


def test_a_missing_activation_norm_raises_rather_than_guessing(real):
    """Another real absence, and the one with teeth.

    None of the author's rows records an activation norm: the bake-off did not
    scale by residual magnitude, so its coefficients are raw multipliers of a
    unit vector. Recording the layer's measured residual norm here would say
    they were fractions of activation magnitude, which they are not. So the
    client cannot express a coefficient as a fraction and says so rather than
    picking a scale nobody supplied.

    This used to null the field out on a loaded object to reach the state. It is
    the state the corpus is in now, so the hack is gone.
    """
    sub = load(REAL_REF, database=real)
    assert sub.contract.activation_norm is None, (
        "a row now records an activation norm, so this reaches the state by "
        "accident rather than on purpose"
    )
    with pytest.raises(NotFound) as raised:
        sub.coefficient(0.1)
    assert "does not transfer across models" in str(raised.value)


def test_several_current_versions_are_not_resolved_by_picking_one(real):
    """`soham/pro-human` is three layer-32 takes and a layer-24 one.

    Nothing orders them: they are parallel takes by one author, differing only
    in the estimator, and `superseded_by` is empty on all four because none
    revises another. So the short form has no head to resolve to and the client
    refuses rather than reading a revision order off version strings.
    """
    with pytest.raises(Ambiguous) as raised:
        load(f"soham/{REAL_MODEL}/pro-human", database=real)
    assert "choosing on your behalf" in str(raised.value)


def test_compare_applies_no_ordering(database):
    """Storage order, and no key derived from a measured result."""
    stored = [s.ref for s in claimants(probe.LABEL_A, database=database)]
    assert [s.ref for s in compare(probe.LABEL_A, database=database).claimants] \
        == stored


# --------------------------------------------------------------------------- #
# what it does


def test_a_pinned_reference_resolves_to_exactly_one(database):
    """And the reference it hands back names the model.

    Four parts since `schema/migrations/010`. `probe-a/probe-trait@v1` is the
    short form and still resolves, because probe-a claims that label on one
    model; what comes back is the full reference, which is what a reader
    should paste into a paper.
    """
    sub = load(f"probe-a/{probe.LABEL_A}@v1", database=database)
    assert sub.ref == f"probe-a/{probe.MODEL_A[0]}/{probe.LABEL_A}@v1"
    assert sub.author == "probe-a" and sub.version == "v1"
    assert sub.model_id == probe.MODEL_A[0]

    # And the full form resolves to the same row.
    assert load(sub.ref, database=database).ref == sub.ref


def test_a_real_pinned_reference_resolves_to_exactly_one(real):
    """The same, against the corpus the site publishes.

    `author/model/label@version` resolves to one frozen submission forever, and
    that is the identity the whole schema is keyed on. Checked against a real
    row because the reference a reader will actually paste is this one.
    """
    sub = load(REAL_REF, database=real)
    assert sub.ref == REAL_REF
    assert sub.author == "soham" and sub.version == "meandiff"
    assert sub.model_id == REAL_MODEL


def test_an_unpinned_reference_takes_that_authors_head(database):
    """One current version, so the short form resolves to it.

    The contrast with the real corpus is the point: there, four versions are
    current and the client refuses. Here one is, and nothing is being chosen.
    """
    assert load(f"probe-a/{probe.LABEL_A}", database=database).version == "v1"


def test_an_unknown_reference_is_an_error_not_an_empty_object(database):
    with pytest.raises(NotFound):
        load(f"nobody/{probe.LABEL_A}", database=database)


def test_the_contract_carries_what_applying_it_requires(database):
    c = load(f"probe-a/{probe.LABEL_A}@v1", database=database).contract
    for field in ("model_id", "model_revision", "layer", "layer_convention",
                  "hook_point"):
        assert getattr(c, field), f"{field} missing; a vector applied without it " \
                                  "appears not to work rather than failing loudly"


def test_the_vector_loads_and_matches_its_declared_shape(database):
    sub = load(f"probe-a/{probe.LABEL_A}@v1", database=database)
    v = sub.vector()
    assert list(v.shape) == [probe.DIM]
    assert str(v.dtype) == sub.contract.dtype


def test_a_real_vector_loads_and_matches_its_declared_shape(real):
    """The vendored bytes, through the same check.

    5120 is the residual width of the model the arena ran, and the row's claim
    to that shape was confirmed against these bytes when the row was written.
    Loading here confirms it a second time, from the other side.
    """
    sub = load(REAL_REF, database=real)
    v = sub.vector()
    assert list(v.shape) == [5120]
    assert str(v.dtype) == sub.contract.dtype


def test_coefficient_is_a_fraction_of_activation_magnitude(database):
    """The arithmetic, where an activation norm exists to do it with.

    No real row records one, so this runs against the probe. What it proves is
    that the client multiplies rather than guessing, and the companion case
    above proves it raises rather than guessing when the norm is absent.
    """
    sub = load(f"probe-a/{probe.LABEL_A}@v1", database=database)
    assert sub.coefficient(0.1) == pytest.approx(0.1 * sub.contract.activation_norm)


def test_compare_surfaces_the_axis_asymmetry(database):
    """What one author checked and the other did not. No single submission page
    can show this, which is the reason Comparison exists at all.

    Only the probe can show it. The real corpus is one author, so every axis in
    it was checked by everybody who claims the label, and an asymmetry between
    one person and themselves is not the thing this measures.
    """
    only_one = compare(probe.LABEL_A, database=database).axes_nobody_checked()
    assert set(only_one) == {
        "probe_axis_one", "probe_axis_two", "probe_axis_three", "probe_axis_four",
    }


def test_verifications_are_separate_from_the_authors_own_numbers(database):
    """Somebody else's measurement of your artifact is listed under their name.

    Nobody has done this in the real corpus, which is why the probe carries an
    evaluator who is not the author. Their number sits in `verifications` and
    never merges into the author's own evidence, because averaging the two would
    erase which of them measured what.
    """
    subject = load(f"probe-a/{probe.LABEL_A}@v1", database=database)
    assert subject.evidence.trait is not None
    assert [v["evaluator"] for v in subject.verifications] == ["probe-attacker"]
    assert all(v["evaluator"] != "probe-a" for v in subject.verifications)


def test_nobody_has_verified_anything_in_the_real_corpus(real):
    """An empty list, and it renders as one rather than as a failure.

    This is the corpus's actual state: no eval by anyone other than the author
    has been pointed at any of these rows. Asserting it keeps the test above
    honest about what it is standing in for, and it will fail the day the
    situation changes, which is the day somebody should reread both.
    """
    for version in ("meandiff", "logistic", "lda", "L24"):
        sub = load(f"soham/{REAL_MODEL}/pro-human@{version}", database=real)
        assert sub.verifications == []


def test_the_client_reads_the_synthetic_flag_rather_than_assuming_it(database, real):
    """Both answers, from the same code path.

    A single-corpus version of this could pass with the field hardcoded. Every
    probe row is flagged and every real row is not, so the client has to be
    reading the column: the flag is what a page uses to decide whether to carry
    the fabricated-figure marker, and one that always answered the same way
    would put the marker on everything or on nothing.
    """
    assert all(s.is_synthetic for s in claimants(probe.LABEL_A, database=database))
    assert not any(s.is_synthetic for s in claimants("pro-human", database=real))
