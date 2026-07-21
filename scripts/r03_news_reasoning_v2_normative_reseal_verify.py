from __future__ import annotations

"""Fail-closed verifier for the R03 N1 V2 normative retention reseal."""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import (  # noqa: E402
    r03_news_reasoning_reconciliation_rerun_verify as rerun_verifier,
)
from v2.research.news_reasoning.r03_source import reject_raw_text_emission  # noqa: E402
from v2.research.overlay.canonical import canonical_sha256  # noqa: E402

LINEAGE_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-normative-reseal-lineage.json"
ATTESTATION_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-normative-reseal-attestation.json"
EVIDENCE_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-normative-reseal-evidence.json"
MANIFEST_PATH = ROOT / "docs" / "r03-news-reasoning-n1-v2-normative-reseal-zero-call-manifest.json"
REVIEW_PATH = ROOT / "docs" / "r03-news-reasoning-n1-numerator-targeted-scan-independent-review.md"
TARGETED_MODULE_PATH = ROOT / "v2" / "research" / "news_reasoning" / "r03_numerator_reconciliation.py"
TARGETED_RUNNER_PATH = ROOT / ".research_artifacts" / "r03-news-reasoning" / "run_numerator_targeted_scan_v1.py"
BASE_RUNNER_PATH = ROOT / ".research_artifacts" / "r03-news-reasoning" / "run_reconciliation_rerun_v1.py"
PRIOR_DRIVER_PATH = ROOT / ".research_artifacts" / "r03-news-reasoning" / "run_read_only_data_check_v2.py"
LEGACY_RESULT_PATH = ROOT / ".research_artifacts" / "r03-news-reasoning" / "read-only-data-check.json"
PERMIT_PATH = ROOT / ".research_artifacts" / "r03-news-reasoning" / "numerator-targeted-scan-permit-v1.json"
TARGETED_RESULT_PATH = ROOT / ".research_artifacts" / "r03-news-reasoning" / "numerator-targeted-scan-result-v1.json"
EVENT_INDEX_PATH = Path("C:/Users/User/Desktop/FinGPT/artifacts/news_main/article_events.parquet")
CALENDAR_INPUT_PATH = Path("C:/Users/User/Desktop/FinGPT/data/raw/market_bars_real.parquet")
TEST_PATH = ROOT / "tests" / "test_r03_v2_normative_reseal_verify.py"
VERIFIER_PATH = ROOT / "scripts" / "r03_news_reasoning_v2_normative_reseal_verify.py"

AUTHORITY = "R03_N1_V2_NORMATIVE_RESEAL_CODE_AUTHORIZED"
STATUS = "V2_NORMATIVE_RESEALED_PENDING_INDEPENDENT_REVIEW"
PERMIT_SHA256 = "93bbaaf0cb90e7c5adb59c6d730101ee88e5532b380d45eaf48cc2d1fea6a4b8"
TARGETED_RESULT_SHA256 = "797a960ed9a7a4e9b1fe3e2f7cf92957a3afcf47fb87df25456ee946f3fc8045"
TARGETED_EVIDENCE_SHA256 = "06a059b1d7b869e4c567d109931faec9d491c84ba2c17f98a874f8f0237d4109"
LEDGER_MULTISET_SHA256 = "43029119e288584e6a516687e52d5cf35625806dd34f15d722c4ef2caf576f75"
LEGACY_RESULT_SHA256 = "24423b02034a00caf614361aabde1b84d16610c102faf18dcfb937bd4b1e2c04"
LEGACY_RESULT_FILESYSTEM_SHA256 = "1a725db609350bd5d4f1ea404040a132f5aed29a2e7775cfa0f0debd4ed9d791"
REVIEW_FILESYSTEM_SHA256 = "264ae4861d2ffb55983625cbe9db110bc3ebd5487f6392bf336efb030a4ea44f"
RECONCILIATION_RESULT_SHA256 = "6046eab6643d31254c398ad1e4183931130acf0ca076cd5aa93b1a69902265eb"
RECONCILIATION_ATTESTATION_SHA256 = "ccac84f3d635b8e9342465a4c0f3a7fca42fb084f2a835d2ebb77d30986bc866"

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

NORMATIVE_RETENTION = {
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

LEGACY_RETENTION = {
    "full_frames_total": 151820,
    "full_frames_retained": 150394,
    "article_appearances_total": 702489,
    "article_appearances_retained": 695948,
    "input_text_bytes": 1585976846,
    "retained_text_bytes": 1435742878,
    "retention_sha256": "8f0ab7a5fe319b53b603b1bd8273ad184a5d41f2b4572a569bd6b02bb080c790",
}

ACCOUNTING = {
    "unaffected_retained_text_bytes": 1428361110,
    "v2_affected_retained_text_bytes": 87025931,
    "legacy_implied_affected_retained_text_bytes": 7381768,
    "preceding_headline_summary_plus_trigger_text_bytes": 6725808,
    "preceding_content_text_bytes": 80300123,
    "legacy_unexplained_preceding_content_text_bytes": 655960,
    "v2_minus_legacy_retained_text_bytes": 79644163,
}

EXECUTION_SURFACE = {
    "execution_commit": "e9109913a2cf198e63f5fbd116abc91c58fc6ee2",
    "targeted_module_filesystem_sha256": "43ada011967a532585ba0ea456a539515501c43c6b9b57d8111b0e24fd8a7efc",
    "targeted_runner_filesystem_sha256": "93e4251418182ba7810d2c6d27cbc037a557ad659a2b8512503d041a61d6fff4",
    "base_runner_filesystem_sha256": "19ad8b083a7e3a3ba50c39676b032e302640f20f65fbe94839d1a84962487a52",
    "prior_driver_filesystem_sha256": "f64ba0a137151127d5956fd90713a31708da64e15e5dbd101bfee37c162d31af",
    "event_index_filesystem_sha256": "89bef1bc58bd2e9558f7af923b38c78c5a46135e71465bc83138042c8e95e060",
    "calendar_input_filesystem_sha256": "9ae1625de0fb91e0c6abaab18b0637a0798abc035368622e5f1aba84e0dec011",
}

LEDGER_FIELDS = (
    "source_appearances",
    "preceding_included_appearances",
    "trigger_included_appearances",
    "omitted_after_trigger_appearances",
    "reconciliation_retained_appearances",
    "preceding_included_zero_byte_appearances",
    "trigger_included_zero_byte_appearances",
    "source_text_bytes",
    "preceding_headline_bytes",
    "preceding_summary_bytes",
    "preceding_content_bytes",
    "trigger_headline_bytes",
    "trigger_summary_bytes",
    "trigger_content_prefix_bytes",
    "reconciliation_retained_text_bytes",
)


class VerificationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"JSON object required: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_self_hash(value: dict[str, Any], field: str, label: str) -> None:
    unsigned = {key: item for key, item in value.items() if key != field}
    if canonical_sha256(unsigned) != value.get(field):
        raise VerificationError(f"{label} self-hash mismatch")


def git_head() -> str:
    head = (ROOT / ".git" / "HEAD").read_text(encoding="ascii").strip()
    if not head.startswith("ref: "):
        return head
    ref = head[5:]
    loose = ROOT / ".git" / ref
    if loose.exists():
        return loose.read_text(encoding="ascii").strip()
    for line in (ROOT / ".git" / "packed-refs").read_text(encoding="ascii").splitlines():
        if line and not line.startswith(("#", "^")):
            value, name = line.split(" ", 1)
            if name == ref:
                return value
    raise VerificationError("HEAD ref cannot be resolved")


def assert_legacy_failure() -> None:
    legacy = load_json(LEGACY_RESULT_PATH)
    if sha256_file(LEGACY_RESULT_PATH) != LEGACY_RESULT_FILESYSTEM_SHA256:
        raise VerificationError("legacy result filesystem hash mismatch")
    assert_self_hash(legacy, "result_sha256", "legacy result")
    if legacy.get("result_sha256") != LEGACY_RESULT_SHA256:
        raise VerificationError("legacy result canonical hash mismatch")
    if legacy.get("status") != "COMPLETED_FAIL_CLOSED_N1_TEXT_RETENTION_MISMATCH":
        raise VerificationError("legacy failure status mismatch")
    if legacy.get("implementation_commit") != "4c47ec61d85e3382c4dd4acfaa0281ca8a1950cd":
        raise VerificationError("legacy implementation commit mismatch")
    if legacy.get("retention") != LEGACY_RETENTION:
        raise VerificationError("legacy retention mismatch")
    comparison = legacy.get("rate_comparison", {})
    if comparison.get("text_byte_retention_pct_rounded_2") != "90.53" or comparison.get("text_byte_retention_pct_expected") != "97.03" or comparison.get("text_byte_retention_matches_expected") is not False:
        raise VerificationError("legacy fail-closed comparison mismatch")
    observation = legacy.get("implementation_contract_observation", {})
    if observation.get("severity") != "HIGH" or observation.get("code") != "R03_PUBLIC_RETENTION_DENOMINATOR_CONFLATION":
        raise VerificationError("legacy HIGH observation mismatch")


def assert_execution_surface(attestation: dict[str, Any], permit: dict[str, Any]) -> None:
    if attestation.get("execution_surface") != EXECUTION_SURFACE:
        raise VerificationError("execution-surface attestation mismatch")
    if {field: permit.get(field) for field in EXECUTION_SURFACE} != EXECUTION_SURFACE:
        raise VerificationError("permit execution-surface pin mismatch")
    observed = {
        "execution_commit": git_head(),
        "targeted_module_filesystem_sha256": sha256_file(TARGETED_MODULE_PATH),
        "targeted_runner_filesystem_sha256": sha256_file(TARGETED_RUNNER_PATH),
        "base_runner_filesystem_sha256": sha256_file(BASE_RUNNER_PATH),
        "prior_driver_filesystem_sha256": sha256_file(PRIOR_DRIVER_PATH),
        "event_index_filesystem_sha256": sha256_file(EVENT_INDEX_PATH),
        "calendar_input_filesystem_sha256": sha256_file(CALENDAR_INPUT_PATH),
    }
    if observed != EXECUTION_SURFACE:
        raise VerificationError("observed execution surface mismatch")


def _ledger_key(ledger: dict[str, Any]) -> tuple[int, ...]:
    if set(ledger) != set(LEDGER_FIELDS):
        raise VerificationError("ledger field set mismatch")
    values = tuple(ledger[field] for field in LEDGER_FIELDS)
    if any(type(value) is not int for value in values):
        raise VerificationError("ledger values must be integers")
    return values


def assert_targeted_result(attestation: dict[str, Any]) -> dict[str, Any]:
    permit = load_json(PERMIT_PATH)
    assert_self_hash(permit, "permit_sha256", "targeted permit")
    if permit.get("permit_sha256") != PERMIT_SHA256:
        raise VerificationError("targeted permit canonical hash mismatch")
    assert_execution_surface(attestation, permit)

    result = load_json(TARGETED_RESULT_PATH)
    assert_self_hash(result, "result_sha256", "targeted result")
    if result.get("result_sha256") != TARGETED_RESULT_SHA256:
        raise VerificationError("targeted result canonical hash mismatch")
    if result.get("permit_sha256") != PERMIT_SHA256:
        raise VerificationError("targeted result permit pin mismatch")
    evidence = result.get("targeted_evidence")
    if not isinstance(evidence, dict):
        raise VerificationError("targeted evidence missing")
    assert_self_hash(evidence, "evidence_sha256", "targeted evidence")
    if evidence.get("evidence_sha256") != TARGETED_EVIDENCE_SHA256:
        raise VerificationError("targeted evidence canonical hash mismatch")
    ledgers = evidence.get("ledgers")
    if not isinstance(ledgers, list) or len(ledgers) != 664:
        raise VerificationError("targeted ledger count mismatch")
    keys = [_ledger_key(ledger) for ledger in ledgers]
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise VerificationError("targeted ledger multiset ordering mismatch")
    if canonical_sha256(ledgers) != evidence.get("ledger_multiset_sha256") or evidence.get("ledger_multiset_sha256") != LEDGER_MULTISET_SHA256:
        raise VerificationError("targeted ledger multiset hash mismatch")

    sums = {field: 0 for field in LEDGER_FIELDS}
    for ledger in ledgers:
        for field in LEDGER_FIELDS:
            sums[field] += ledger[field]
        if ledger["source_appearances"] != ledger["preceding_included_appearances"] + 1 + ledger["omitted_after_trigger_appearances"]:
            raise VerificationError("ledger source appearance partition mismatch")
        if ledger["reconciliation_retained_appearances"] != ledger["preceding_included_appearances"] + ledger["trigger_included_appearances"]:
            raise VerificationError("ledger retained appearance partition mismatch")
        trigger = ledger["trigger_headline_bytes"] + ledger["trigger_summary_bytes"] + ledger["trigger_content_prefix_bytes"]
        preceding = ledger["preceding_headline_bytes"] + ledger["preceding_summary_bytes"] + ledger["preceding_content_bytes"]
        if ledger["reconciliation_retained_text_bytes"] != preceding + trigger:
            raise VerificationError("ledger retained-byte component mismatch")
        if ledger["reconciliation_retained_text_bytes"] > min(ledger["source_text_bytes"], 131072):
            raise VerificationError("ledger byte bound mismatch")

    trigger_total = sums["trigger_headline_bytes"] + sums["trigger_summary_bytes"] + sums["trigger_content_prefix_bytes"]
    derived = {
        "reconciliation_affected_text_bytes": sums["reconciliation_retained_text_bytes"],
        "trigger_only_affected_text_bytes": trigger_total,
        "preceding_headline_plus_trigger_text_bytes": sums["preceding_headline_bytes"] + trigger_total,
        "preceding_summary_plus_trigger_text_bytes": sums["preceding_summary_bytes"] + trigger_total,
        "preceding_headline_summary_plus_trigger_text_bytes": sums["preceding_headline_bytes"] + sums["preceding_summary_bytes"] + trigger_total,
        "all_retained_headline_summary_text_bytes": sums["preceding_headline_bytes"] + sums["preceding_summary_bytes"] + sums["trigger_headline_bytes"] + sums["trigger_summary_bytes"],
    }
    for field, value in derived.items():
        if evidence.get(field) != value:
            raise VerificationError(f"targeted derived aggregate mismatch: {field}")
    if evidence.get("affected_frame_count") != 664 or evidence.get("total_news_positive_frames") != NORMATIVE_RETENTION["full_frames_total"]:
        raise VerificationError("targeted frame-count semantic alias mismatch")
    if evidence.get("sealed_implied_affected_text_bytes") != ACCOUNTING["legacy_implied_affected_retained_text_bytes"]:
        raise VerificationError("legacy implied affected bytes mismatch")
    if result.get("reconciliation_retention") != NORMATIVE_RETENTION:
        raise VerificationError("targeted normative retention mismatch")
    if result.get("diagnostics") != {
        "article_cap_affected_appearances": 849,
        "session_cap_affected_frames": 664,
        "session_truncated_distinct_articles": 659,
        "utf8_prefix_requests": 621,
        "utf8_boundary_adjustment_bytes": 0,
    }:
        raise VerificationError("targeted diagnostics mismatch")
    execution = result.get("execution", {})
    if execution.get("completed_raw_source_scans") != 1 or any(value != 0 for key, value in execution.items() if key != "completed_raw_source_scans"):
        raise VerificationError("targeted execution counters mismatch")
    if derived["reconciliation_affected_text_bytes"] - ACCOUNTING["legacy_implied_affected_retained_text_bytes"] != ACCOUNTING["v2_minus_legacy_retained_text_bytes"]:
        raise VerificationError("targeted numerator gap identity mismatch")
    if sums["preceding_content_bytes"] - ACCOUNTING["v2_minus_legacy_retained_text_bytes"] != ACCOUNTING["legacy_unexplained_preceding_content_text_bytes"]:
        raise VerificationError("targeted unexplained legacy residue mismatch")
    reject_raw_text_emission(result)
    return result


def assert_lineage(lineage: dict[str, Any]) -> None:
    assert_self_hash(lineage, "lineage_sha256", "V2 reseal lineage")
    if lineage.get("authority") != AUTHORITY or lineage.get("status") != STATUS:
        raise VerificationError("V2 reseal lineage authority/status mismatch")
    if lineage.get("normative_retention") != NORMATIVE_RETENTION:
        raise VerificationError("V2 normative retention mismatch")
    if lineage.get("replacement_disposition") != {
        "action": "REPLACE_NOT_RECONCILE",
        "legacy_value_status": "HISTORICAL_NON_NORMATIVE_UNREPRODUCIBLE",
        "legacy_artifacts_preserved_byte_for_byte": True,
        "legacy_value_forbidden_as_future_decision_input": True,
        "lost_v1_driver_recovery": "CLOSED_UNRECOVERABLE",
        "post_hoc_fit_to_655960_forbidden": True,
    }:
        raise VerificationError("replacement disposition mismatch")
    if lineage.get("numerator_accounting") != ACCOUNTING:
        raise VerificationError("numerator accounting mismatch")
    if lineage.get("canonical_hash_policy") != {
        "normative_contract_anchor": "CANONICAL_SHA256",
        "filesystem_sha256_role": "REVIEW_SESSION_ANCHOR_ONLY",
        "targeted_result_crlf_filesystem_hash_is_nonnormative": True,
    }:
        raise VerificationError("canonical hash policy mismatch")
    if lineage.get("semantic_aliases") != {
        "targeted_result.total_news_positive_frames": "full_frames_total",
        "alias_changes_no_value": True,
    }:
        raise VerificationError("semantic alias mapping mismatch")
    if lineage.get("boundary_counters") != ZERO_COUNTERS:
        raise VerificationError("V2 reseal code-only counters are not zero")


def assert_attestation(attestation: dict[str, Any], lineage: dict[str, Any]) -> None:
    assert_self_hash(attestation, "attestation_sha256", "V2 reseal attestation")
    if attestation.get("authority") != AUTHORITY:
        raise VerificationError("V2 reseal attestation authority mismatch")
    if attestation.get("lineage_canonical_sha256") != lineage.get("lineage_sha256"):
        raise VerificationError("attestation lineage pin mismatch")
    if attestation.get("execution_surface") != EXECUTION_SURFACE:
        raise VerificationError("execution-surface attestation mismatch")
    if attestation.get("result_pins") != {
        "reconciliation_result_canonical_sha256": RECONCILIATION_RESULT_SHA256,
        "reconciliation_attestation_canonical_sha256": RECONCILIATION_ATTESTATION_SHA256,
        "targeted_permit_canonical_sha256": PERMIT_SHA256,
        "targeted_result_canonical_sha256": TARGETED_RESULT_SHA256,
        "targeted_evidence_canonical_sha256": TARGETED_EVIDENCE_SHA256,
        "targeted_ledger_multiset_sha256": LEDGER_MULTISET_SHA256,
    }:
        raise VerificationError("V2 reseal result pin mismatch")
    if attestation.get("independent_review") != {
        "path": "docs/r03-news-reasoning-n1-numerator-targeted-scan-independent-review.md",
        "filesystem_sha256": REVIEW_FILESYSTEM_SHA256,
        "disposition": "APPROVED_RESULT_ARTIFACT_VERIFIED_PROVENANCE_UNRESOLVED",
        "check_count": 44,
        "recommended_path": "B_REPLACE_LEGACY_WITH_V2",
    }:
        raise VerificationError("independent-review attestation mismatch")
    if sha256_file(REVIEW_PATH) != REVIEW_FILESYSTEM_SHA256:
        raise VerificationError("independent-review filesystem hash mismatch")
    if attestation.get("legacy_failure_source") != {
        "path": ".research_artifacts/r03-news-reasoning/read-only-data-check.json",
        "canonical_sha256": LEGACY_RESULT_SHA256,
        "filesystem_sha256": LEGACY_RESULT_FILESYSTEM_SHA256,
        "status": "COMPLETED_FAIL_CLOSED_N1_TEXT_RETENTION_MISMATCH",
        "high_observation": "R03_PUBLIC_RETENTION_DENOMINATOR_CONFLATION",
        "generator_driver_status": "UNTRACKED_V1_DRIVER_LOST",
    }:
        raise VerificationError("legacy failure-source attestation mismatch")
    if attestation.get("prior_and_current_execution_scopes") != {
        "targeted_raw_scan_completed": 1,
        "targeted_raw_scan_other_counters_zero": True,
        "current_reseal_code_only_counters": ZERO_COUNTERS,
    }:
        raise VerificationError("execution-scope attestation mismatch")


def assert_evidence(evidence: dict[str, Any], lineage: dict[str, Any], attestation: dict[str, Any]) -> None:
    assert_self_hash(evidence, "evidence_sha256", "V2 reseal evidence")
    if evidence.get("authority") != AUTHORITY:
        raise VerificationError("V2 reseal evidence authority mismatch")
    if evidence.get("lineage_canonical_sha256") != lineage.get("lineage_sha256") or evidence.get("attestation_canonical_sha256") != attestation.get("attestation_sha256"):
        raise VerificationError("V2 reseal evidence cross-pin mismatch")
    if evidence.get("normative_retention") != NORMATIVE_RETENTION or evidence.get("numerator_accounting") != ACCOUNTING:
        raise VerificationError("V2 reseal evidence numeric mismatch")
    if evidence.get("boundary_counters") != ZERO_COUNTERS:
        raise VerificationError("V2 reseal evidence counters are not zero")
    pins = evidence.get("artifact_sha256", {})
    expected_paths = (LINEAGE_PATH, ATTESTATION_PATH, REVIEW_PATH, TARGETED_MODULE_PATH, VERIFIER_PATH, TEST_PATH)
    expected = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in expected_paths}
    if pins != expected:
        raise VerificationError("V2 reseal evidence artifact pin mismatch")


def assert_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("authority") != AUTHORITY or manifest.get("temporal_scope") != "N1_V2_NORMATIVE_RESEAL_CODE_ONLY_SESSION":
        raise VerificationError("V2 reseal manifest scope mismatch")
    if manifest.get("boundary_counters") != ZERO_COUNTERS:
        raise VerificationError("V2 reseal manifest counters are not zero")
    pins = manifest.get("artifact_sha256", {})
    expected_paths = (LINEAGE_PATH, ATTESTATION_PATH, EVIDENCE_PATH, REVIEW_PATH, TARGETED_MODULE_PATH, VERIFIER_PATH, TEST_PATH)
    expected = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in expected_paths}
    if pins != expected:
        raise VerificationError("V2 reseal manifest artifact pin mismatch")


def main() -> int:
    if rerun_verifier.main() != 0:
        raise VerificationError("prior reconciliation rerun verifier failed")
    lineage = load_json(LINEAGE_PATH)
    attestation = load_json(ATTESTATION_PATH)
    evidence = load_json(EVIDENCE_PATH)
    manifest = load_json(MANIFEST_PATH)
    assert_legacy_failure()
    assert_lineage(lineage)
    assert_attestation(attestation, lineage)
    assert_targeted_result(attestation)
    assert_evidence(evidence, lineage, attestation)
    assert_manifest(manifest)
    for artifact in (lineage, attestation, evidence, manifest):
        reject_raw_text_emission(artifact)
    print("PASS_R03_N1_V2_NORMATIVE_RESEAL " f"lineage={lineage['lineage_sha256']} " f"attestation={attestation['attestation_sha256']} " f"evidence={evidence['evidence_sha256']} " f"retained_text_bytes={NORMATIVE_RETENTION['retained_text_bytes']} " "text_byte_retention_pct_2dp=95.55 raw_source_traversals=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
