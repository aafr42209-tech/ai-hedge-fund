from __future__ import annotations

"""Provider-free verifier for the R03 N1 reconciliation code-only layer."""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.r03_news_reasoning_data_check_verify import (  # noqa: E402
    assert_amendment_artifacts,
)
from v2.research.news_reasoning.r03_reconciliation import (  # noqa: E402
    CANONICAL_CLASSIFICATION,
    CANONICAL_CLASSIFICATION_PATH,
    CAUSE_STATUS_PATH,
    RECONCILIATION_AUTHORITY,
    runtime_contract_pins,
)
from v2.research.news_reasoning.r03_source import reject_raw_text_emission  # noqa: E402
from v2.research.overlay.canonical import canonical_sha256  # noqa: E402

LINEAGE_PATH = "docs/r03-news-reasoning-n1-reconciliation-lineage.json"
EVIDENCE_PATH = "docs/r03-news-reasoning-n1-reconciliation-code-only-evidence.json"
MANIFEST_PATH = "docs/r03-news-reasoning-n1-reconciliation-zero-call-manifest.json"
ATTESTATION_PATH = "docs/r03-news-reasoning-data-check-rerun-attestation.json"
MODULE_PATH = "v2/research/news_reasoning/r03_reconciliation.py"
TEST_PATH = "tests/test_r03_reconciliation.py"
VERIFIER_PATH = "scripts/r03_news_reasoning_reconciliation_verify.py"

HISTORICAL_LINEAGE_SHA256 = "eec62df18f1e5cd4d896274c54b0734fd32d34d92fd6dbefbecf2a50f404b881"
HISTORICAL_EVIDENCE_SHA256 = "5d0b57d8230e929db49e1c03dfbb97cfab7548750265759a37e97b3f4b931eda"
HISTORICAL_MANIFEST_FILESYSTEM_SHA256 = "3205bcfd43ffbb02ddccb3a51b4747efa6ab0a82ca3a3481637a936b2b91adc2"
ATTESTATION_SHA256 = "a21be7bc0a614b6b87ceef9ac3bf9cc89d25d40215dc67d7344994ce834034a0"
ATTESTATION_FILESYSTEM_SHA256 = "680e4634a40d2eaf96a19cc75dfa37db8e66375368e04cf05cc3d1a989c01c2a"

CODE_ONLY_ZERO_COUNTERS = {
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


def sha256_file(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def load_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON object required: {relative}")
    return value


def assert_self_hash(value: dict[str, Any], field: str, label: str) -> None:
    declared = value.get(field)
    unsigned = {key: item for key, item in value.items() if key != field}
    if declared != canonical_sha256(unsigned):
        raise VerificationError(f"{label} canonical self-hash mismatch")


def assert_attestation(attestation: dict[str, Any]) -> None:
    assert_self_hash(attestation, "attestation_sha256", "rerun attestation")
    if attestation["attestation_sha256"] != ATTESTATION_SHA256:
        raise VerificationError("rerun attestation canonical pin mismatch")
    if sha256_file(ATTESTATION_PATH) != ATTESTATION_FILESYSTEM_SHA256:
        raise VerificationError("rerun attestation filesystem pin mismatch")
    provenance = attestation.get("provenance_classification", {})
    if provenance.get("classification") != CANONICAL_CLASSIFICATION:
        raise VerificationError("canonical provenance classification mismatch")
    if provenance.get("not_classified_as") != "V2_REPRODUCTION_FAILURE":
        raise VerificationError("provenance exclusion mismatch")
    if attestation.get("investigation_note", {}).get("classification") != ("UNRESOLVED_ADAPTER_OR_PRIOR_CENSUS_SEMANTICS_DIVERGENCE"):
        raise VerificationError("non-normative cause status mismatch")
    if attestation.get("commit_gate") != "CLOSED":
        raise VerificationError("rerun commit gate must remain closed")


def assert_lineage(lineage: dict[str, Any]) -> None:
    assert_self_hash(lineage, "lineage_sha256", "reconciliation lineage")
    if lineage.get("authority") != RECONCILIATION_AUTHORITY:
        raise VerificationError("reconciliation authority mismatch")
    if lineage.get("canonical_classification") != {
        "path": CANONICAL_CLASSIFICATION_PATH,
        "value": CANONICAL_CLASSIFICATION,
        "cause_status_path": CAUSE_STATUS_PATH,
        "cause_status_is_normative": False,
    }:
        raise VerificationError("classification authority mapping mismatch")
    if lineage.get("runtime_contract_pins") != runtime_contract_pins():
        raise VerificationError("runtime contract pin mismatch")
    historical = lineage.get("historical_amendment_pins", {})
    if historical != {
        "lineage_canonical_sha256": HISTORICAL_LINEAGE_SHA256,
        "evidence_canonical_sha256": HISTORICAL_EVIDENCE_SHA256,
        "manifest_filesystem_sha256": HISTORICAL_MANIFEST_FILESYSTEM_SHA256,
        "temporal_scope": "PRE_RERUN_AMENDMENT_CODE_ONLY_SESSION",
        "boundary_counters_are_historical": True,
    }:
        raise VerificationError("historical amendment pin set mismatch")
    if lineage.get("rerun_attestation_pins") != {
        "canonical_sha256": ATTESTATION_SHA256,
        "filesystem_sha256": ATTESTATION_FILESYSTEM_SHA256,
        "temporal_scope": "POST_AMENDMENT_AUTHORIZED_RERUN_ATTEMPTS",
    }:
        raise VerificationError("rerun attestation pin set mismatch")
    if lineage.get("normative_retention_disposition") != "UNRESOLVED_NO_VALUE_RESEALED":
        raise VerificationError("retention value must remain unresolved")
    if lineage.get("boundary_counters") != CODE_ONLY_ZERO_COUNTERS:
        raise VerificationError("reconciliation code-only counters are not zero")


def assert_evidence(evidence: dict[str, Any], lineage: dict[str, Any]) -> None:
    assert_self_hash(evidence, "evidence_sha256", "reconciliation evidence")
    if evidence.get("lineage_canonical_sha256") != lineage.get("lineage_sha256"):
        raise VerificationError("evidence-to-lineage pin mismatch")
    if evidence.get("boundary_counters") != CODE_ONLY_ZERO_COUNTERS:
        raise VerificationError("reconciliation evidence counters are not zero")
    pins = evidence.get("artifact_sha256", {})
    expected_paths = (MODULE_PATH, TEST_PATH, VERIFIER_PATH, ATTESTATION_PATH, LINEAGE_PATH)
    if set(pins) != set(expected_paths):
        raise VerificationError("reconciliation evidence artifact pin set mismatch")
    for relative in expected_paths:
        if pins.get(relative) != sha256_file(relative):
            raise VerificationError(f"reconciliation evidence artifact mismatch: {relative}")


def assert_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("boundary_counters") != CODE_ONLY_ZERO_COUNTERS:
        raise VerificationError("reconciliation manifest counters are not zero")
    pins = manifest.get("artifact_sha256", {})
    expected_paths = (EVIDENCE_PATH, LINEAGE_PATH, MODULE_PATH, VERIFIER_PATH, ATTESTATION_PATH)
    if set(pins) != set(expected_paths):
        raise VerificationError("reconciliation manifest pin set mismatch")
    for relative in expected_paths:
        if pins.get(relative) != sha256_file(relative):
            raise VerificationError(f"reconciliation manifest artifact mismatch: {relative}")


def assert_reconciliation_artifacts() -> dict[str, str]:
    historical = assert_amendment_artifacts()
    if historical != {
        "lineage_sha256": HISTORICAL_LINEAGE_SHA256,
        "evidence_sha256": HISTORICAL_EVIDENCE_SHA256,
        "manifest_filesystem_sha256": HISTORICAL_MANIFEST_FILESYSTEM_SHA256,
    }:
        raise VerificationError("historical amendment verifier output mismatch")
    attestation = load_json(ATTESTATION_PATH)
    lineage = load_json(LINEAGE_PATH)
    evidence = load_json(EVIDENCE_PATH)
    manifest = load_json(MANIFEST_PATH)
    assert_attestation(attestation)
    assert_lineage(lineage)
    assert_evidence(evidence, lineage)
    assert_manifest(manifest)
    for artifact in (attestation, lineage, evidence, manifest):
        reject_raw_text_emission(artifact)
    return {
        "lineage_sha256": lineage["lineage_sha256"],
        "evidence_sha256": evidence["evidence_sha256"],
        "manifest_filesystem_sha256": sha256_file(MANIFEST_PATH),
        "attestation_sha256": attestation["attestation_sha256"],
    }


def main() -> int:
    try:
        result = assert_reconciliation_artifacts()
    except (AssertionError, KeyError, OSError, TypeError, ValueError) as exc:
        print(f"FAIL_R03_N1_RECONCILIATION: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("PASS_R03_N1_RECONCILIATION " f"lineage_sha256={result['lineage_sha256']} " f"evidence_sha256={result['evidence_sha256']} " f"manifest_sha256={result['manifest_filesystem_sha256']} " f"attestation_sha256={result['attestation_sha256']} " "raw_source_traversals=0 commits=0 pushes=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
