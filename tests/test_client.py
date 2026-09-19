"""The Python client.

Most of these check what the client refuses to do. Those refusals are the product:
a client that quietly answers "give me kindness" has designated one, and it would
do so at exactly the moment a user is least likely to notice.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from controlbun import BareLabelError, NotFound, claimants, compare, load  # noqa: E402


@pytest.fixture(scope="module")
def database(tmp_path_factory):
    path = tmp_path_factory.mktemp("client") / "fixture.db"
    subprocess.run(
        [sys.executable, str(ROOT / "fixtures" / "build.py"), "--db", str(path)],
        check=True, capture_output=True,
    )
    return path


# --------------------------------------------------------------------------- #
# what it refuses


def test_a_bare_label_does_not_resolve(database):
    with pytest.raises(BareLabelError) as raised:
        load("kindness", database=database)
    message = str(raised.value)
    assert "does not resolve" in message
    assert 'compare("kindness")' in message, (
        "refusing is not enough; the error has to say where to go instead, or the "
        "next person just writes their own resolver"
    )


def test_the_refusal_survives_a_label_that_looks_namespaced(database):
    """`@v1` without an owner is still a bare label."""
    with pytest.raises(BareLabelError):
        load("kindness@v1", database=database)


def test_an_unmeasured_value_is_none_not_zero(database):
    bob = load("bob/kindness", database=database)
    assert bob.evidence.transfer is None
    assert bob.evidence.transfer != 0
    assert bob.measured("transfer") is False
    assert load("alice/kindness", database=database).measured("transfer") is True


def test_a_missing_activation_norm_raises_rather_than_guessing(database):
    sub = load("alice/kindness", database=database)
    object.__setattr__(sub.contract, "activation_norm", None)
    with pytest.raises(NotFound) as raised:
        sub.coefficient(0.1)
    assert "does not transfer across models" in str(raised.value)


def test_compare_applies_no_ordering(database):
    """Storage order, and no key derived from a measured result."""
    stored = [s.ref for s in claimants("kindness", database=database)]
    assert [s.ref for s in compare("kindness", database=database).claimants] == stored


# --------------------------------------------------------------------------- #
# what it does


def test_a_pinned_reference_resolves_to_exactly_one(database):
    """And the reference it hands back names the model.

    Four parts since `schema/migrations/010`. `alice/kindness@v1` is the
    short form and still resolves, because alice claims that label on one
    model; what comes back is the full reference, which is what a reader
    should paste into a paper.
    """
    sub = load("alice/kindness@v1", database=database)
    assert sub.ref == "alice/placeholder/does-not-resolve-1b/kindness@v1"
    assert sub.author == "alice" and sub.version == "v1"
    assert sub.model_id == "placeholder/does-not-resolve-1b"

    # And the full form resolves to the same row.
    assert load(sub.ref, database=database).ref == sub.ref


def test_an_unpinned_reference_takes_that_authors_newest(database):
    assert load("alice/kindness", database=database).version == "v1"


def test_an_unknown_reference_is_an_error_not_an_empty_object(database):
    with pytest.raises(NotFound):
        load("nobody/kindness", database=database)


def test_the_contract_carries_what_applying_it_requires(database):
    c = load("alice/kindness@v1", database=database).contract
    for field in ("model_id", "model_revision", "layer", "layer_convention",
                  "hook_point"):
        assert getattr(c, field), f"{field} missing; a vector applied without it " \
                                  "appears not to work rather than failing loudly"


def test_the_vector_loads_and_matches_its_declared_shape(database):
    sub = load("alice/kindness@v1", database=database)
    v = sub.vector()
    assert list(v.shape) == [8]
    assert str(v.dtype) == sub.contract.dtype


def test_coefficient_is_a_fraction_of_activation_magnitude(database):
    sub = load("alice/kindness@v1", database=database)
    assert sub.coefficient(0.1) == pytest.approx(0.1 * sub.contract.activation_norm)


def test_compare_surfaces_the_axis_asymmetry(database):
    """What one author checked and the other did not. No single submission page
    can show this, which is the reason Comparison exists at all."""
    only_one = compare("kindness", database=database).axes_nobody_checked()
    assert set(only_one) == {"sentiment", "verbosity", "formality", "refusal_rate"}


def test_verifications_are_separate_from_the_authors_own_numbers(database):
    alice = load("alice/kindness@v1", database=database)
    assert alice.evidence.trait is not None
    assert [v["evaluator"] for v in alice.verifications] == ["carol"]
    assert all(v["evaluator"] != "alice" for v in alice.verifications)


def test_everything_loaded_is_flagged_synthetic(database):
    assert all(s.is_synthetic for s in claimants("kindness", database=database))
