from __future__ import annotations

"""Fail-closed verifier for the additive R03 V2 retention-reference overlay."""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import (  # noqa: E402
    r03_news_reasoning_v2_normative_reseal_verify as reseal_verifier,
)
from v2.research.news_reasoning.r03_source import reject_raw_text_emission  # noqa: E402
from v2.research.overlay.canonical import canonical_sha256  # noqa: E402

CHARTER_PATH = ROOT / "docs" / "r03-news-reasoning-charter-draft.md"
PREREG_PATH = ROOT / "docs" / "r03-news-reasoning-provider-free-preregistration-draft.md"
CHARTER_AMENDMENT_PATH = ROOT / "docs" / "r03-news-reasoning-charter-v2-retention-amendment.md"
PREREG_AMENDMENT_PATH = ROOT / "docs" / "r03-news-reasoning-provider-free-preregistration-v2-retention-amendment.md"
CONTRACT_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-effective-retention-contract.json"
LINEAGE_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-reference-propagation-lineage.json"
EVIDENCE_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-reference-propagation-evidence.json"
MANIFEST_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-reference-propagation-zero-call-manifest.json"
VERIFIER_PATH = ROOT / "scripts" / "r03_news_reasoning_v2_reference_propagation_verify.py"
TEST_PATH = ROOT / "tests" / "test_r03_v2_reference_propagation_verify.py"

AUTHORITY = "R03_N1_V2_NORMATIVE_REFERENCE_PROPAGATION_CODE_AUTHORIZED"
CHARTER_SHA256 = "a96766f5b15fdecc839c07d3f66a1cc78e40d778050a3eae2623d77ffdb90329"
PREREG_SHA256 = "741fc091e689ac4a848cd2ea43fc99f26295b632831d33426028769b31bde211"
CHARTER_AMENDMENT_SHA256 = "71645e43aa1913cb8bc8ffb299e197e5434ca7edbf97fe6a7c341a757aab0464"
PREREG_AMENDMENT_SHA256 = "1ad550dfdd728c6fe83008616f6facb01ef36aac970bc4a82cddebcf48a00a37"
CONTRACT_SHA256 = "7277792e284aaa90d8ca7bcef828102e28f587950f8a2ca7951b5dae93136704"
CONTRACT_FILESYSTEM_SHA256 = "d3081ef09d2f789671c75765374392ab01ea17333c594e40b5e1de2999313fa2"
LINEAGE_SHA256 = "22d8da2c435b02778287ffefa7e98d6a04108f458ae4e8e0e0bafc1824c976ff"

CHARTER_OLD_CLAUSE = "this policy fully preserves 150,394/151,820 news-positive frames (99.06%),\n" "retains 695,948/702,489 article appearances (99.07%), and retains\n" "1,435,742,878/1,585,976,846 text bytes (90.53%). Percent displays use"
PREREG_OLD_CLAUSE = "budget fully preserves 150,394/151,820 news-positive frames (99.06%), retains\n" "695,948/702,489 article appearances (99.07%), and retains\n" "1,435,742,878/1,585,976,846 text bytes (90.53%), using round-half-even to two"
CHARTER_OLD_CLAUSE_SHA256 = "4ce3cb4f72abf0af9e551cb3cd68a5a0895da8739a07c1e328e3652c28932cf4"
PREREG_OLD_CLAUSE_SHA256 = "5ab3b69d651b6c4cb456aabf1675c8bceaa152b04cdc97c8a1a03c7653cf4cc7"

EFFECTIVE_RETENTION = {
    "schema_version": "r03-public-retention-v2",
    "full_frames_total": 151820,
    "full_frames_retained": 150394,
    "article_appearances_total": 702489,
    "article_appearances_retained": 695948,
    "input_text_bytes": 1585976846,
    "retained_text_bytes": 1515387041,
    "full_frame_retention_pct_2dp": "99.06",
    "article_appearance_retention_pct_2dp": "99.07",
    "text_byte_retention_pct_2dp": "95.55",
    "retention_sha256": "8b659ac03fb4481ebbbcdc3579e484f5630d8e490d6981c0b4a7a2c3c02c1019",
}

NORMATIVE_SOURCE = {
    "v2_reseal_lineage_canonical_sha256": "8f3b3f0c25b3dd8b7c12af4232f6fb22b19db62e71b752d1555b9c114457a719",
    "v2_reseal_attestation_canonical_sha256": "44002b7a56e3c2432b4b4abf62088241d83c397d96c1a7e33828f03eeb3659f6",
    "v2_reseal_evidence_canonical_sha256": "a170b0bdabf967cef8f606a96bcce3f395bd90ada92a954b76bc0eeb1a7b2d6b",
    "v2_reseal_manifest_filesystem_sha256": "37ea72d5de7996e35919c3a8332093b525df46cfa0b0302d21bf9dc6d7425f14",
    "ancestor_fix_review_filesystem_sha256": "4c20f452c4f347457aa6f5f349af49f4f99f63f761bc3a1a5771d4db5d10deb7",
    "disposition": "INDEPENDENT_V2_NORMATIVE_RESEAL_AND_ANCESTOR_FIX_APPROVED",
}

PRECEDENCE = {
    "composition": "BASE_DOCUMENT_PLUS_PINNED_ADDITIVE_AMENDMENT",
    "scope": "SELECTED_PAYLOAD_RETENTION_ASSERTION_ONLY",
    "action": "REPLACE_NOT_RECONCILE",
    "legacy_90_53_role": "HISTORICAL_NON_NORMATIVE_ONLY",
    "p5_97_03_role": "SUPERSEDED_HISTORICAL_ONLY",
    "all_other_base_clauses_unchanged": True,
    "effective_value_required_for_future_r03_decisions": True,
}

NON_AUTHORITY = {
    "raw_source_access": False,
    "frame_or_fixture_creation": False,
    "fitting": False,
    "g1_g2_g3_execution": False,
    "oos_access": False,
    "inference_or_model_download": False,
    "provider_or_network_use": False,
    "dependency_change": False,
    "commit": False,
    "push": False,
}

ZERO_COUNTERS = {
    "raw_source_traversals": 0,
    "raw_source_copies": 0,
    "frame_materializations": 0,
    "fixture_materializations": 0,
    "model_fits": 0,
    "gate_executions": 0,
    "oos_accesses": 0,
    "local_inference_calls": 0,
    "model_downloads": 0,
    "provider_calls": 0,
    "network_attempts": 0,
    "dependency_changes": 0,
    "commits": 0,
    "pushes": 0,
}


class VerificationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON object required: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def assert_self_hash(value: dict[str, Any], field: str, label: str) -> None:
    unsigned = {key: item for key, item in value.items() if key != field}
    if canonical_sha256(unsigned) != value.get(field):
        raise VerificationError(f"{label} self-hash mismatch")


def assert_base_document_text(
    *,
    label: str,
    text: str,
    old_clause: str,
    old_clause_sha256: str,
) -> None:
    if sha256_text(old_clause) != old_clause_sha256:
        raise VerificationError(f"{label} old-clause constant hash mismatch")
    if text.count(old_clause) != 1:
        raise VerificationError(f"{label} old clause must remain exactly once")
    if "1,515,387,041/1,585,976,846 text bytes (95.55%)" in text:
        raise VerificationError(f"{label} base document was directly edited")


def assert_base_documents() -> None:
    if sha256_file(CHARTER_PATH) != CHARTER_SHA256 or sha256_file(PREREG_PATH) != PREREG_SHA256:
        raise VerificationError("base charter/preregistration hash mismatch")
    assert_base_document_text(
        label="charter",
        text=CHARTER_PATH.read_text(encoding="utf-8"),
        old_clause=CHARTER_OLD_CLAUSE,
        old_clause_sha256=CHARTER_OLD_CLAUSE_SHA256,
    )
    assert_base_document_text(
        label="preregistration",
        text=PREREG_PATH.read_text(encoding="utf-8"),
        old_clause=PREREG_OLD_CLAUSE,
        old_clause_sha256=PREREG_OLD_CLAUSE_SHA256,
    )


def assert_amendments(contract: dict[str, Any]) -> None:
    if sha256_file(CHARTER_AMENDMENT_PATH) != CHARTER_AMENDMENT_SHA256 or sha256_file(PREREG_AMENDMENT_PATH) != PREREG_AMENDMENT_SHA256:
        raise VerificationError("retention amendment filesystem hash mismatch")
    expected = {
        "charter": {
            "path": "docs/r03-news-reasoning-charter-v2-retention-amendment.md",
            "filesystem_sha256": CHARTER_AMENDMENT_SHA256,
        },
        "preregistration": {
            "path": "docs/r03-news-reasoning-provider-free-preregistration-v2-retention-amendment.md",
            "filesystem_sha256": PREREG_AMENDMENT_SHA256,
        },
    }
    if contract.get("amendments") != expected:
        raise VerificationError("effective-contract amendment pin mismatch")
    for label, path in (("charter", CHARTER_AMENDMENT_PATH), ("preregistration", PREREG_AMENDMENT_PATH)):
        text = path.read_text(encoding="utf-8")
        normalized_text = " ".join(text.split())
        if text.count("1,515,387,041/1,585,976,846 text bytes (95.55%)") != 1:
            raise VerificationError(f"{label} amendment effective value mismatch")
        if "REPLACE_NOT_RECONCILE" not in text or "byte-for-byte unchanged" not in normalized_text:
            raise VerificationError(f"{label} amendment precedence/preservation mismatch")


def assert_effective_contract(contract: dict[str, Any]) -> None:
    assert_self_hash(contract, "effective_contract_sha256", "effective retention contract")
    if contract.get("effective_contract_sha256") != CONTRACT_SHA256 or sha256_file(CONTRACT_PATH) != CONTRACT_FILESYSTEM_SHA256:
        raise VerificationError("effective retention contract identity mismatch")
    if contract.get("authority") != AUTHORITY or contract.get("status") != "EFFECTIVE_V2_RETENTION_REFERENCE_OVERLAY_PENDING_INDEPENDENT_REVIEW":
        raise VerificationError("effective retention contract authority/status mismatch")
    if contract.get("base_documents") != {
        "charter": {
            "path": "docs/r03-news-reasoning-charter-draft.md",
            "filesystem_sha256": CHARTER_SHA256,
            "superseded_clause_utf8_sha256": CHARTER_OLD_CLAUSE_SHA256,
            "preserved_byte_for_byte": True,
        },
        "preregistration": {
            "path": "docs/r03-news-reasoning-provider-free-preregistration-draft.md",
            "filesystem_sha256": PREREG_SHA256,
            "superseded_clause_utf8_sha256": PREREG_OLD_CLAUSE_SHA256,
            "preserved_byte_for_byte": True,
        },
    }:
        raise VerificationError("effective-contract base-document pin mismatch")
    if contract.get("normative_source") != NORMATIVE_SOURCE:
        raise VerificationError("effective-contract normative-source mismatch")
    if contract.get("effective_retention") != EFFECTIVE_RETENTION:
        raise VerificationError("effective retention mismatch")
    if contract.get("precedence") != PRECEDENCE:
        raise VerificationError("effective-contract precedence mismatch")
    if contract.get("non_authority") != NON_AUTHORITY:
        raise VerificationError("effective-contract non-authority mismatch")
    assert_amendments(contract)


def assert_lineage(lineage: dict[str, Any], contract: dict[str, Any]) -> None:
    assert_self_hash(lineage, "lineage_sha256", "reference-propagation lineage")
    if lineage.get("lineage_sha256") != LINEAGE_SHA256:
        raise VerificationError("reference-propagation lineage identity mismatch")
    if lineage.get("authority") != AUTHORITY or lineage.get("status") != "V2_NORMATIVE_REFERENCE_OVERLAY_IMPLEMENTED_PENDING_INDEPENDENT_REVIEW":
        raise VerificationError("reference-propagation lineage authority/status mismatch")
    if lineage.get("base_preservation") != {
        "charter_path": "docs/r03-news-reasoning-charter-draft.md",
        "charter_filesystem_sha256": CHARTER_SHA256,
        "preregistration_path": "docs/r03-news-reasoning-provider-free-preregistration-draft.md",
        "preregistration_filesystem_sha256": PREREG_SHA256,
        "base_documents_modified": False,
        "historical_seals_preserved": True,
    }:
        raise VerificationError("reference-propagation base preservation mismatch")
    if lineage.get("effective_contract") != {
        "path": "docs/r03-news-reasoning-n1-v2-effective-retention-contract.json",
        "canonical_sha256": contract["effective_contract_sha256"],
        "filesystem_sha256": CONTRACT_FILESYSTEM_SHA256,
    }:
        raise VerificationError("reference-propagation contract pin mismatch")
    if lineage.get("normative_source_pins") != {key: value for key, value in NORMATIVE_SOURCE.items() if key != "disposition"}:
        raise VerificationError("reference-propagation normative-source pin mismatch")
    if lineage.get("propagation_resolution") != {
        "charter_selected_payload_retention": "EFFECTIVE_FROM_ADDITIVE_V2_AMENDMENT",
        "preregistration_selected_payload_retention": "EFFECTIVE_FROM_ADDITIVE_V2_AMENDMENT",
        "effective_text_byte_retention_pct_2dp": "95.55",
        "legacy_90_53_references_in_base_documents": "PRESERVED_BUT_SUPERSEDED_AT_EFFECTIVE_CONTRACT_LAYER",
        "prior_unresolved_dispositions": "PRESERVED_AS_HISTORICAL_STATE",
        "replacement_mode": "REPLACE_NOT_RECONCILE",
    }:
        raise VerificationError("reference-propagation resolution mismatch")
    if lineage.get("boundary_counters") != ZERO_COUNTERS:
        raise VerificationError("reference-propagation lineage counters are not zero")


def assert_evidence(evidence: dict[str, Any], lineage: dict[str, Any], contract: dict[str, Any]) -> None:
    assert_self_hash(evidence, "evidence_sha256", "reference-propagation evidence")
    if evidence.get("authority") != AUTHORITY:
        raise VerificationError("reference-propagation evidence authority mismatch")
    if evidence.get("lineage_canonical_sha256") != lineage["lineage_sha256"] or evidence.get("effective_contract_canonical_sha256") != contract["effective_contract_sha256"]:
        raise VerificationError("reference-propagation evidence cross-pin mismatch")
    if evidence.get("effective_retention") != EFFECTIVE_RETENTION or evidence.get("precedence") != PRECEDENCE:
        raise VerificationError("reference-propagation evidence contract mismatch")
    if evidence.get("boundary_counters") != ZERO_COUNTERS:
        raise VerificationError("reference-propagation evidence counters are not zero")
    expected_paths = (CHARTER_PATH, PREREG_PATH, CHARTER_AMENDMENT_PATH, PREREG_AMENDMENT_PATH, CONTRACT_PATH, LINEAGE_PATH, VERIFIER_PATH, TEST_PATH)
    expected = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in expected_paths}
    if evidence.get("artifact_sha256") != expected:
        raise VerificationError("reference-propagation evidence artifact pin mismatch")


def assert_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("authority") != AUTHORITY or manifest.get("temporal_scope") != "N1_V2_NORMATIVE_REFERENCE_PROPAGATION_CODE_ONLY_SESSION":
        raise VerificationError("reference-propagation manifest scope mismatch")
    if manifest.get("boundary_counters") != ZERO_COUNTERS:
        raise VerificationError("reference-propagation manifest counters are not zero")
    expected_paths = (CHARTER_PATH, PREREG_PATH, CHARTER_AMENDMENT_PATH, PREREG_AMENDMENT_PATH, CONTRACT_PATH, LINEAGE_PATH, EVIDENCE_PATH, VERIFIER_PATH, TEST_PATH)
    expected = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in expected_paths}
    if manifest.get("artifact_sha256") != expected:
        raise VerificationError("reference-propagation manifest artifact pin mismatch")


def main() -> int:
    if reseal_verifier.main() != 0:
        raise VerificationError("V2 normative reseal verifier failed")
    contract = load_json(CONTRACT_PATH)
    lineage = load_json(LINEAGE_PATH)
    evidence = load_json(EVIDENCE_PATH)
    manifest = load_json(MANIFEST_PATH)
    assert_base_documents()
    assert_effective_contract(contract)
    assert_lineage(lineage, contract)
    assert_evidence(evidence, lineage, contract)
    assert_manifest(manifest)
    for artifact in (contract, lineage, evidence, manifest):
        reject_raw_text_emission(artifact)
    print("PASS_R03_N1_V2_REFERENCE_PROPAGATION " f"contract={contract['effective_contract_sha256']} " f"lineage={lineage['lineage_sha256']} " f"evidence={evidence['evidence_sha256']} " "effective_text_byte_retention_pct_2dp=95.55 raw_source_traversals=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
