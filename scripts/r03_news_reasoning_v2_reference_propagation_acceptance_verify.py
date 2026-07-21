from __future__ import annotations

"""Fail-closed verifier for the append-only R03 propagation acceptance overlay."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import (  # noqa: E402
    r03_news_reasoning_v2_reference_propagation_verify as propagation_verifier,
)
from v2.research.news_reasoning.r03_source import reject_raw_text_emission  # noqa: E402
from v2.research.overlay.canonical import canonical_sha256  # noqa: E402

INDEX_PATH = ROOT / "docs" / "r03-news-reasoning-document-composition-index.md"
ATTESTATION_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-reference-propagation-acceptance-attestation.json"
INDEPENDENT_REVIEW_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-reference-propagation-independent-review.md"

AUTHORITY = "R03_N1_V2_REFERENCE_PROPAGATION_ACCEPTANCE_ATTESTATION_AND_COMPOSITION_INDEX_CODE_AUTHORIZED"
DISPOSITION = "INDEPENDENT_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY"
MODE = "APPEND_ONLY_ACCEPTANCE_OVERLAY_PRESERVING_REVIEWED_CONTRACT"
REVIEWED_HEAD = "605ef598446b851bce8def647f8769a885a6274c"
ATTESTATION_SHA256 = "e9247117274a00365ea47e536c4ce338c9ccd38f59091ab01105f085863ab1aa"
INDEX_SHA256 = "923d06768141df9f7c0a275aa39ac415a77c5bc3765ce2c0765bf7a6971a92c5"
INDEPENDENT_REVIEW_SHA256 = "f6e710159840a96e16720aab54d046a3bcf45d3dd1a7271a190bfa9886f6449b"

REVIEWED_ARTIFACT_SHA256 = {
    "docs/r03-news-reasoning-charter-v2-retention-amendment.md": "71645e43aa1913cb8bc8ffb299e197e5434ca7edbf97fe6a7c341a757aab0464",
    "docs/r03-news-reasoning-n1-v2-effective-retention-contract.json": "d3081ef09d2f789671c75765374392ab01ea17333c594e40b5e1de2999313fa2",
    "docs/r03-news-reasoning-n1-v2-reference-propagation-evidence.json": "a51808092b125b9b0713fea414110ce400989e2d056fd837a942a34a8f06166a",
    "docs/r03-news-reasoning-n1-v2-reference-propagation-independent-review.md": INDEPENDENT_REVIEW_SHA256,
    "docs/r03-news-reasoning-n1-v2-reference-propagation-lineage.json": "0e16c47b6e248f267ed78318af01fbcee40d94e60d76ad1e84f6996f055292cb",
    "docs/r03-news-reasoning-n1-v2-reference-propagation-review-handoff.md": "f1162f53a8a1dd5b9ea813a7fd9e16b81b0fd3c47215e3d7690bc5ee96249baa",
    "docs/r03-news-reasoning-n1-v2-reference-propagation-zero-call-manifest.json": "654d696ae657ca6faed8bc47f72d9bcc80b5dc901c687e4650ceb5d578e0e0c9",
    "docs/r03-news-reasoning-provider-free-preregistration-v2-retention-amendment.md": "1ad550dfdd728c6fe83008616f6facb01ef36aac970bc4a82cddebcf48a00a37",
    "scripts/r03_news_reasoning_v2_reference_propagation_verify.py": "a2c42c343fc711d3de17d45e222282f8544f52f118c27828dbd468a246fbb3de",
    "tests/test_r03_v2_reference_propagation_verify.py": "b362c6be0cdfd12ea05e24a9b0f4a97130a27a304da05a39ce4fa41d5e921950",
}

BASE_DOCUMENT_SHA256 = {
    "docs/r03-news-reasoning-charter-draft.md": "a96766f5b15fdecc839c07d3f66a1cc78e40d778050a3eae2623d77ffdb90329",
    "docs/r03-news-reasoning-provider-free-preregistration-draft.md": "741fc091e689ac4a848cd2ea43fc99f26295b632831d33426028769b31bde211",
}

PRESERVATION = {
    "reviewed_contract_modified": False,
    "reviewed_artifacts_modified": False,
    "base_documents_modified": False,
    "acceptance_recorded_by_additive_composition": True,
}


class VerificationError(RuntimeError):
    """Raised when the acceptance overlay no longer matches its reviewed inputs."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"{path.name} must be a JSON object")
    return value


def reviewed_head_is_ancestor(commit: str) -> bool:
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        return False
    try:
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return completed.returncode == 0


def assert_self_hash(value: dict[str, Any]) -> None:
    unsigned = {key: item for key, item in value.items() if key != "acceptance_attestation_sha256"}
    if canonical_sha256(unsigned) != value.get("acceptance_attestation_sha256"):
        raise VerificationError("acceptance attestation self-hash mismatch")
    if value.get("acceptance_attestation_sha256") != ATTESTATION_SHA256:
        raise VerificationError("acceptance attestation identity mismatch")


def assert_reviewed_artifacts(attestation: dict[str, Any]) -> None:
    if attestation.get("reviewed_artifact_sha256") != REVIEWED_ARTIFACT_SHA256:
        raise VerificationError("reviewed artifact pin set mismatch")
    if attestation.get("base_document_sha256") != BASE_DOCUMENT_SHA256:
        raise VerificationError("base-document pin set mismatch")
    expected = {**REVIEWED_ARTIFACT_SHA256, **BASE_DOCUMENT_SHA256}
    observed = {relative_path: sha256_file(ROOT / relative_path) for relative_path in expected}
    if observed != expected:
        raise VerificationError("reviewed or base artifact filesystem drift")


def assert_independent_review(attestation: dict[str, Any]) -> None:
    expected = {
        "path": "docs/r03-news-reasoning-n1-v2-reference-propagation-independent-review.md",
        "filesystem_sha256": INDEPENDENT_REVIEW_SHA256,
        "disposition": DISPOSITION,
    }
    if attestation.get("independent_review") != expected:
        raise VerificationError("independent-review pin mismatch")
    if sha256_file(INDEPENDENT_REVIEW_PATH) != INDEPENDENT_REVIEW_SHA256:
        raise VerificationError("independent-review filesystem drift")
    marker = f"Disposition: `{DISPOSITION}`"
    if INDEPENDENT_REVIEW_PATH.read_text(encoding="utf-8").count(marker) != 1:
        raise VerificationError("independent-review disposition marker mismatch")


def assert_composition_index(attestation: dict[str, Any]) -> None:
    expected = {
        "path": "docs/r03-news-reasoning-document-composition-index.md",
        "filesystem_sha256": INDEX_SHA256,
    }
    if attestation.get("composition_index") != expected:
        raise VerificationError("composition-index pin mismatch")
    if sha256_file(INDEX_PATH) != INDEX_SHA256:
        raise VerificationError("composition-index filesystem drift")
    text = INDEX_PATH.read_text(encoding="utf-8")
    required_fragments = (
        DISPOSITION,
        "docs/r03-news-reasoning-charter-draft.md",
        "docs/r03-news-reasoning-charter-v2-retention-amendment.md",
        "docs/r03-news-reasoning-provider-free-preregistration-draft.md",
        "docs/r03-news-reasoning-provider-free-preregistration-v2-retention-amendment.md",
        "1,515,387,041 / 1,585,976,846 text bytes = 95.55%",
        "REPLACE_NOT_RECONCILE",
        propagation_verifier.CONTRACT_SHA256,
        INDEPENDENT_REVIEW_SHA256,
        "docs/r03-news-reasoning-n1-v2-reference-propagation-acceptance-attestation.json",
    )
    if any(fragment not in text for fragment in required_fragments):
        raise VerificationError("composition-index required reference missing")
    if "90.53%" not in text or "historical, non-normative" not in text:
        raise VerificationError("composition-index legacy-role statement mismatch")


def assert_attestation(attestation: dict[str, Any]) -> None:
    assert_self_hash(attestation)
    if attestation.get("authority") != AUTHORITY:
        raise VerificationError("acceptance authority mismatch")
    if attestation.get("mode") != MODE:
        raise VerificationError("acceptance mode mismatch")
    if attestation.get("accepted_disposition") != DISPOSITION:
        raise VerificationError("acceptance disposition mismatch")
    if attestation.get("reviewed_head") != REVIEWED_HEAD:
        raise VerificationError("reviewed HEAD pin mismatch")
    if not reviewed_head_is_ancestor(REVIEWED_HEAD):
        raise VerificationError("reviewed HEAD is not an ancestor of current HEAD")
    if attestation.get("accepted_contract") != {
        "path": "docs/r03-news-reasoning-n1-v2-effective-retention-contract.json",
        "status_as_authored": "EFFECTIVE_V2_RETENTION_REFERENCE_OVERLAY_PENDING_INDEPENDENT_REVIEW",
        "canonical_sha256": propagation_verifier.CONTRACT_SHA256,
        "filesystem_sha256": propagation_verifier.CONTRACT_FILESYSTEM_SHA256,
    }:
        raise VerificationError("accepted contract pin mismatch")
    if attestation.get("effective_retention") != propagation_verifier.EFFECTIVE_RETENTION:
        raise VerificationError("accepted retention mismatch")
    if attestation.get("precedence") != propagation_verifier.PRECEDENCE:
        raise VerificationError("acceptance precedence mismatch")
    if attestation.get("preservation") != PRESERVATION:
        raise VerificationError("acceptance preservation mismatch")
    if attestation.get("boundary_counters") != propagation_verifier.ZERO_COUNTERS:
        raise VerificationError("acceptance boundary counters are not zero")
    if attestation.get("non_authority") != propagation_verifier.NON_AUTHORITY:
        raise VerificationError("acceptance non-authority mismatch")
    assert_reviewed_artifacts(attestation)
    assert_independent_review(attestation)
    assert_composition_index(attestation)
    reject_raw_text_emission(attestation)


def main() -> int:
    if propagation_verifier.main() != 0:
        raise VerificationError("reference-propagation verifier failed")
    attestation = load_json(ATTESTATION_PATH)
    assert_attestation(attestation)
    print("PASS_R03_N1_V2_REFERENCE_PROPAGATION_ACCEPTANCE " f"attestation={attestation['acceptance_attestation_sha256']} " f"contract={propagation_verifier.CONTRACT_SHA256} " "effective_text_byte_retention_pct_2dp=95.55 " f"disposition={DISPOSITION} raw_source_traversals=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
