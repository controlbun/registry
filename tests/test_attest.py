"""The attestation set is append-only.

Nothing in `_attest/` is ever deleted, moved out, or regenerated. The proofs are
the only dated record that the design existed when it did, and a proof is useless
without the manifest it commits to, so losing either half loses the evidence.

This file is the tripwire. Removing a manifest now requires editing the inventory
below, which is a deliberate act with a diff attached rather than an accident
during a rebase, a reset, or a tidy-up.

No dependency on the `ots` binary: a detached OpenTimestamps proof carries the
digest of the file it attests at a fixed offset, so binding is checkable directly.

    bytes 0..31   magic, b"\\x00OpenTimestamps\\x00\\x00Proof\\x00..."
    byte  31      format version
    byte  32      hash op, 0x08 for sha256
    bytes 33..65  the attested file's digest
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTEST = ROOT / "_attest"

MAGIC = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"
OP_SHA256 = 0x08
BITCOIN_ATTESTATION_TAG = bytes.fromhex("0588960d73d71901")

# Every manifest that must exist. Add to this when a new pair is stamped; never
# remove from it. `.ots.bak` files are the pre-upgrade proofs that `ots upgrade`
# sets aside and are covered by the sibling check rather than listed here.
REQUIRED_MANIFESTS = [
    "MANIFEST-a.sha256",
    "MANIFEST-b.sha256",
    "MANIFEST-c.sha256",
    "MANIFEST_BRIEF_2026-09-11_2320.sha256",
    "MANIFEST_BRIEF_2026-09-12_0013.sha256",
    "MANIFEST_BRIEF_2026-09-12_0019.sha256",
    "MANIFEST_FINAL_2026-09-11_2317.sha256",
    "MANIFEST_FINAL_2026-09-12_0013.sha256",
    "MANIFEST_FINAL_2026-09-12_0020.sha256",
]

# Confirmed in the Bitcoin blockchain. These must never revert to pending, which
# would mean the file was replaced by an older copy.
ANCHORED = [
    "MANIFEST-a.sha256",
    "MANIFEST-b.sha256",
    "MANIFEST-c.sha256",
    "MANIFEST_BRIEF_2026-09-11_2320.sha256",
    "MANIFEST_BRIEF_2026-09-12_0013.sha256",
    "MANIFEST_BRIEF_2026-09-12_0019.sha256",
    "MANIFEST_FINAL_2026-09-11_2317.sha256",
    "MANIFEST_FINAL_2026-09-12_0013.sha256",
    "MANIFEST_FINAL_2026-09-12_0020.sha256",
]


def attested_digest(proof: Path) -> str:
    raw = proof.read_bytes()
    assert raw.startswith(MAGIC), f"{proof.name} is not an OpenTimestamps proof"
    assert raw[32] == OP_SHA256, f"{proof.name} does not attest a sha256"
    return raw[33:65].hex()


def test_no_manifest_has_gone_missing():
    missing = [n for n in REQUIRED_MANIFESTS if not (ATTEST / n).exists()]
    assert not missing, (
        "A manifest is gone. It is not recoverable by regenerating it: a new file "
        "with the same name attests a different moment. Restore it from git "
        "history rather than rebuilding it:\n  " + "\n  ".join(missing)
    )


def test_every_manifest_still_has_its_proof():
    orphans = [n for n in REQUIRED_MANIFESTS if not (ATTEST / f"{n}.ots").exists()]
    assert not orphans, (
        "A manifest lost its proof. The manifest alone proves nothing:\n  "
        + "\n  ".join(orphans)
    )


def test_every_proof_still_binds_its_manifest():
    broken = []
    for name in REQUIRED_MANIFESTS:
        manifest, proof = ATTEST / name, ATTEST / f"{name}.ots"
        if not (manifest.exists() and proof.exists()):
            continue
        actual = hashlib.sha256(manifest.read_bytes()).hexdigest()
        claimed = attested_digest(proof)
        if actual != claimed:
            broken.append(f"{name}: file {actual[:16]} vs proof {claimed[:16]}")
    assert not broken, (
        "A proof no longer commits to its manifest, which means the manifest was "
        "edited after stamping. Rewriting an anchored proof's manifest orphans the "
        "proof, which is the only thing it is for:\n  " + "\n  ".join(broken)
    )


def test_anchored_proofs_have_not_reverted_to_pending():
    reverted = []
    for name in ANCHORED:
        proof = ATTEST / f"{name}.ots"
        if proof.exists() and BITCOIN_ATTESTATION_TAG not in proof.read_bytes():
            reverted.append(name)
    assert not reverted, (
        "A confirmed proof carries no Bitcoin attestation any more, so it was "
        "overwritten by an older pending copy, most likely a .bak restored over "
        "the wrong file:\n  " + "\n  ".join(reverted)
    )
