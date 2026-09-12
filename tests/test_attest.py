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
        "with the same name attests a different moment. Recover it from "
        "version history rather than rebuilding it:\n  " + "\n  ".join(missing)
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


# --------------------------------------------------------------------------- #
# _attest/ is append-only: nothing in it is deleted and nothing in it is edited.
#
# Every file pinned by content. Adding a new stamp is fine and needs no entry
# here; changing or removing an existing one has to be a deliberate edit to this
# table, with a diff, rather than something a rebase can do quietly.

FROZEN_ATTEST = {
    "MANIFEST-a.sha256":
        "207c9658009a6613eb41c84511df63120d64311be756a3c46e823c6eea68f2bf",
    "MANIFEST-a.sha256.ots":
        "98eb73e052b9d6e24142915e176fdb658be3748f7f92b2abc9e871ab69efa956",
    "MANIFEST-a.sha256.ots.bak":
        "da433e55354207549fb9b0ba18363afbcfac49112860a5ca5d66bb9d2462ae50",
    "MANIFEST-b.sha256":
        "125885b177595228f741957ce0c159e6ea73b2693c758d8c9993b3b6788a6d7d",
    "MANIFEST-b.sha256.ots":
        "f383cb9395eb1ecfa61993dd4cf30fc3064d396c6fcbfd495be0ee2b32787b81",
    "MANIFEST-b.sha256.ots.bak":
        "68e1464c0ee92042a085253404868347a87572c0150b54ceb85fdb7639b1e85a",
    "MANIFEST-c.sha256":
        "79e882065f431c341e4d144aef2265d2c043a42149dd991d4474230fcea04a93",
    "MANIFEST-c.sha256.ots":
        "5e07c73416a4630bb94b93824f3b3db62204cfe8e9e0c1824f77943dfd75bcb3",
    "MANIFEST-c.sha256.ots.bak":
        "d5c72b243bfd25c88a473ed40081324acdb2d898488f738ecbc5b0f886cdcef8",
    "MANIFEST_BRIEF_2026-09-11_2320.sha256":
        "620ba3b6a985117063f77b216728be304159d79ce2639f9a92852d11192b1e5a",
    "MANIFEST_BRIEF_2026-09-11_2320.sha256.ots":
        "f23d72c9d9aa33bc28365898cdd0b2046627e88e38bdba282a43be8609698e23",
    "MANIFEST_BRIEF_2026-09-11_2320.sha256.ots.bak":
        "4ec6b7b691a8f9ddd4ea52d478571d3a48e717879d976d53fa64bb9d782c1f2c",
    "MANIFEST_BRIEF_2026-09-12_0013.sha256":
        "3bc7b57537a169bdd9e6011f0ad4684d9f2a81455927a6adb0fb033404efcf57",
    "MANIFEST_BRIEF_2026-09-12_0013.sha256.ots":
        "15943b2bb32d1138598dfec5781bff760dfcb6674cc0f9f77af1c33141887ab4",
    "MANIFEST_BRIEF_2026-09-12_0013.sha256.ots.bak":
        "0e7e827cc6ec7d1dc15bedbb36f1014ac06f365242e4bbcea69ba292c0ba6c91",
    "MANIFEST_BRIEF_2026-09-12_0019.sha256":
        "7bf7a601468d0d7a71fe3cd075bb1fcb98f0fd14bedfc31f43cd4a10ce45680a",
    "MANIFEST_BRIEF_2026-09-12_0019.sha256.ots":
        "be09019e5fba3621e92b38ff03c891a6de3a67755f194c53ff3543a38a5bd1c9",
    "MANIFEST_BRIEF_2026-09-12_0019.sha256.ots.bak":
        "8d982ba97f8b3962105cf51324bab18a428d8c0154941f707da3e0f61eead419",
    "MANIFEST_FINAL_2026-09-11_2317.sha256":
        "567240f80e4fdadd361d53def61aa5e460add3ee4af83d33ef8d93da970edc57",
    "MANIFEST_FINAL_2026-09-11_2317.sha256.ots":
        "a00636f7f9f3bfd16d2607e2a5f0e7b3f6f57a4958964162427daf9e3e18679b",
    "MANIFEST_FINAL_2026-09-11_2317.sha256.ots.bak":
        "351b8177ab6f6da9f36553a211b7c6d44a1ed8970a2f4f7e58069a12a1d9a71f",
    "MANIFEST_FINAL_2026-09-12_0013.sha256":
        "536533a1a3d5a94548718a4fc399067596b2aee59c1c49d7efee76330fb58ad5",
    "MANIFEST_FINAL_2026-09-12_0013.sha256.ots":
        "122a5e99c2c10931e24524467864ed4cf67e96b7a1b1e3ac8714ffe266ef6506",
    "MANIFEST_FINAL_2026-09-12_0013.sha256.ots.bak":
        "f731c08613cb675b9fa1e34d5733ba1a0974124bf543d72caeeaf996f52f94f0",
    "MANIFEST_FINAL_2026-09-12_0020.sha256":
        "7fce5bb13a4aee93b9823b8ce0a57a88ba2a82cc17217c67fccbaf2154e50973",
    "MANIFEST_FINAL_2026-09-12_0020.sha256.ots":
        "d1d5ac245b0c40b1a8dd1455233d1b07d6d59f5562df20892aea505b236f0c2c",
    "MANIFEST_FINAL_2026-09-12_0020.sha256.ots.bak":
        "6838123815f699ce8f9313c8cfd994522f2a617bfee5b43b765901ad04daa3d6",
}

# Deletion-protected, but freely editable. These are the documents the whole
# project is; the manifests exist to date them.
SEED_DOCUMENTS = [
    "BRIEF.md",
    "CLAUDE.md",
    "CONTEXT.md",
    "DECISIONS.md",
    "VALIDATION.md",
]


def test_no_attest_file_has_been_modified():
    changed = []
    for name, expected in FROZEN_ATTEST.items():
        path = ATTEST / name
        if not path.exists():
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            changed.append(f"{name}: {expected[:16]} -> {actual[:16]}")
    assert not changed, (
        "A file under _attest/ was modified. These are notarised records of past "
        "states; editing one does not update it, it destroys what it recorded:\n  "
        + "\n  ".join(changed)
    )


def test_no_attest_file_has_been_removed():
    gone = [n for n in FROZEN_ATTEST if not (ATTEST / n).exists()]
    assert not gone, (
        "A file under _attest/ is missing. Recover it from version history; a "
        "regenerated file with the same name attests a different moment:\n  "
        + "\n  ".join(gone)
    )


def test_seed_documents_still_exist():
    gone = [n for n in SEED_DOCUMENTS if not (ROOT / n).exists()]
    assert not gone, (
        "A seed document is missing. Every anchored manifest commits to these "
        "files by hash, so losing one orphans the proofs that date it:\n  "
        + "\n  ".join(gone)
    )
