from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v2.research.news_reasoning.r03_reconciliation import (  # noqa: E402
    R03N1ReconciliationPermitV1,
    R03PairedFrameDiffEvidence,
    validate_reconciliation_permit,
)
from v2.research.news_reasoning.r03_source import reject_raw_text_emission  # noqa: E402
from v2.research.overlay.canonical import canonical_sha256  # noqa: E402

ATTESTATION_PATH = ROOT / "docs" / "r03-news-reasoning-n1-reconciliation-rerun-attestation.json"
LINEAGE_PATH = ROOT / "docs" / "r03-news-reasoning-n1-reconciliation-lineage.json"
EVIDENCE_PATH = ROOT / "docs" / "r03-news-reasoning-n1-reconciliation-code-only-evidence.json"
MANIFEST_PATH = ROOT / "docs" / "r03-news-reasoning-n1-reconciliation-zero-call-manifest.json"
HANDOFF_PATH = ROOT / "docs" / "r03-news-reasoning-n1-reconciliation-review-handoff.md"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _filesystem_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_without(value: dict[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def _require_equal(label: str, observed: object, expected: object) -> None:
    if observed != expected:
        raise ValueError(f"{label} mismatch: observed={observed!r} expected={expected!r}")


def _require_subset(label: str, observed: dict[str, Any], expected: dict[str, Any]) -> None:
    for field, value in expected.items():
        _require_equal(f"{label}.{field}", observed.get(field), value)


def _six_decimal_average(numerator: int, denominator: int) -> str:
    return str((Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.000001")))


def main() -> int:
    attestation = _load(ATTESTATION_PATH)
    artifacts = attestation["artifacts"]
    permit_path = ROOT / artifacts["permit_path"]
    runner_path = ROOT / artifacts["runner_path"]
    result_path = ROOT / artifacts["result_path"]
    permit_value = _load(permit_path)
    result = _load(result_path)
    lineage = _load(LINEAGE_PATH)
    evidence = _load(EVIDENCE_PATH)

    _require_equal(
        "attestation canonical hash",
        _canonical_without(attestation, "attestation_sha256"),
        attestation["attestation_sha256"],
    )
    _require_equal(
        "result canonical hash",
        _canonical_without(result, "result_sha256"),
        result["result_sha256"],
    )
    for label, path, field in (
        ("permit filesystem hash", permit_path, "permit_filesystem_sha256"),
        ("runner filesystem hash", runner_path, "runner_filesystem_sha256"),
        ("result filesystem hash", result_path, "result_filesystem_sha256"),
    ):
        _require_equal(label, _filesystem_sha256(path), artifacts[field])
    _require_equal(
        "attested result canonical hash",
        result["result_sha256"],
        artifacts["result_canonical_sha256"],
    )
    for label, path_field, hash_field in (
        ("prior driver", "prior_driver_path", "prior_driver_filesystem_sha256"),
        ("event index", "event_index_path", "event_index_filesystem_sha256"),
        ("calendar input", "calendar_input_path", "calendar_input_filesystem_sha256"),
    ):
        _require_equal(
            f"{label} filesystem hash",
            _filesystem_sha256(Path(artifacts[path_field])),
            artifacts[hash_field],
        )

    permit = R03N1ReconciliationPermitV1.model_validate(permit_value)
    validate_reconciliation_permit(permit, permit.permit_sha256)
    _require_equal(
        "reconciliation permit hash",
        permit.permit_sha256,
        attestation["pins"]["reconciliation_permit_sha256"],
    )
    _require_equal(
        "result permit hash",
        result["pins"]["reconciliation_permit_sha256"],
        permit.permit_sha256,
    )
    base = permit.base_permit
    permit_pin_values = {
        "base_permit_sha256": base.permit_sha256,
        "root_path_sha256": base.root_path_sha256,
        "calendar_session_count": base.calendar_session_count,
        "calendar_sha256": base.calendar_sha256,
        "early_close_session_count": base.early_close_session_count,
        "early_close_sessions_sha256": base.early_close_sessions_sha256,
        "article_byte_cap": base.article_byte_cap,
        "ticker_session_byte_cap": base.ticker_session_byte_cap,
    }
    _require_subset("attestation pins", attestation["pins"], permit_pin_values)
    _require_subset("result pins", result["pins"], permit_pin_values)

    paired = R03PairedFrameDiffEvidence.model_validate(result["paired_frame_diff_evidence"])
    _require_equal("paired evidence hash", paired.evidence_sha256, artifacts["paired_evidence_sha256"])
    _require_equal("pair multiset hash", paired.pair_multiset_sha256, artifacts["pair_multiset_sha256"])
    _require_equal("paired frame count", paired.affected_frame_count, 664)
    reject_raw_text_emission(result)

    _require_equal("inventory", attestation["inventory"], result["inventory"])
    _require_equal("source counts", attestation["source_counts"], result["source_counts"])
    _require_equal("sealed retention", attestation["sealed_retention"], result["sealed_retention"])
    _require_subset(
        "reconciliation retention",
        result["reconciliation_retention"],
        attestation["reconciliation_retention"],
    )

    sealed = result["sealed_retention"]
    reconciliation = result["reconciliation_retention"]
    prior = result["prior_census_bug_reconstruction"]
    comparison_keys = tuple(sealed)
    expected_reconciliation_mismatches = {field: {"sealed": sealed[field], "reconciliation": reconciliation[field]} for field in comparison_keys if sealed[field] != reconciliation[field]}
    expected_prior_mismatches = {field: {"sealed": sealed[field], "prior_reconstruction": prior[field]} for field in comparison_keys if sealed[field] != prior[field]}
    _require_equal(
        "sealed versus reconciliation mismatches",
        result["sealed_vs_reconciliation_mismatches"],
        expected_reconciliation_mismatches,
    )
    _require_equal(
        "sealed versus prior reconstruction mismatches",
        result["sealed_vs_prior_reconstruction_mismatches"],
        expected_prior_mismatches,
    )

    expected_resolved = {
        "input_text_bytes": "MATCHES_SEALED_EXACTLY_WHITESPACE_DENOMINATOR_BLOCKER_CLOSED",
        "article_appearances_retained": "MATCHES_SEALED_EXACTLY_INCLUDED_ZERO_BYTE_SEMANTICS_CLOSED",
        "full_frames": "MATCHES_SEALED_EXACTLY",
        "session_cap_affected_frames": "MATCHES_PRIOR_PROVENANCE_AT_664",
    }
    _require_equal("resolved findings", attestation["resolved_findings"], expected_resolved)
    for field in (
        "full_frames_total",
        "full_frames_retained",
        "article_appearances_total",
        "article_appearances_retained",
        "input_text_bytes",
    ):
        _require_equal(f"resolved aggregate {field}", reconciliation[field], sealed[field])

    approved = attestation["approved_contract"]
    _require_equal(
        "approved lineage canonical hash",
        _canonical_without(lineage, "lineage_sha256"),
        approved["lineage_canonical_sha256"],
    )
    _require_equal(
        "approved evidence canonical hash",
        _canonical_without(evidence, "evidence_sha256"),
        approved["evidence_canonical_sha256"],
    )
    _require_equal(
        "approved manifest filesystem hash",
        _filesystem_sha256(MANIFEST_PATH),
        approved["manifest_filesystem_sha256"],
    )
    _require_equal(
        "approved handoff filesystem hash",
        _filesystem_sha256(HANDOFF_PATH),
        approved["handoff_filesystem_sha256"],
    )

    expected_paired_summary = {
        "affected_frame_count": paired.affected_frame_count,
        "changed_retained_text_frames": paired.changed_retained_text_frames,
        "equal_retained_text_frames": paired.equal_retained_text_frames,
        "reconciliation_retained_text_bytes_total": paired.reconciliation_retained_text_bytes_total,
        "triggering_article_only_retained_text_bytes_total": paired.prior_retained_text_bytes_total,
        "retained_text_bytes_delta": paired.retained_text_bytes_delta,
        "triggering_article_zero_retained_text_frames": paired.prior_zero_retained_text_frames,
        "reconciliation_zero_retained_text_frames": paired.reconciliation_zero_retained_text_frames,
        "reconciliation_included_zero_byte_appearances_total": paired.reconciliation_included_zero_byte_appearances_total,
        "zero_source_appearances_total": paired.zero_source_appearances_total,
    }
    _require_equal(
        "paired summary",
        attestation["paired_frame_diff"],
        expected_paired_summary,
    )

    unaffected = reconciliation["retained_text_bytes"] - paired.reconciliation_retained_text_bytes_total
    sealed_implied = sealed["retained_text_bytes"] - unaffected
    expected_decomposition = {
        "unaffected_frame_retained_text_bytes": unaffected,
        "sealed_implied_affected_frame_retained_text_bytes": sealed_implied,
        "sealed_implied_affected_frame_average_bytes": _six_decimal_average(sealed_implied, paired.affected_frame_count),
        "reconciliation_affected_frame_average_bytes": _six_decimal_average(
            paired.reconciliation_retained_text_bytes_total,
            paired.affected_frame_count,
        ),
        "triggering_article_only_average_bytes": _six_decimal_average(
            paired.prior_retained_text_bytes_total,
            paired.affected_frame_count,
        ),
        "sealed_implied_minus_triggering_article_only_bytes": (sealed_implied - paired.prior_retained_text_bytes_total),
    }
    _require_equal(
        "numerator decomposition",
        attestation["numerator_decomposition"],
        expected_decomposition,
    )
    _require_equal(
        "prior reconstruction arithmetic",
        prior["retained_text_bytes"],
        unaffected + paired.prior_retained_text_bytes_total,
    )

    unresolved = attestation["unresolved_finding"]
    expected_unresolved = {
        "classification": "PRIOR_CENSUS_AFFECTED_FRAME_ACCUMULATION_RULE_NOT_YET_IDENTIFIED",
        "reconciliation_minus_sealed_retained_text_bytes": (reconciliation["retained_text_bytes"] - sealed["retained_text_bytes"]),
        "triggering_article_only_reconstruction_retained_text_bytes": prior["retained_text_bytes"],
        "triggering_article_only_reconstruction_minus_sealed": (prior["retained_text_bytes"] - sealed["retained_text_bytes"]),
        "conclusion": "preserve-whitespace v2 measurement resolves denominator and appearance differences, but neither full accumulation nor triggering-article-only accumulation reproduces the sealed numerator",
        "normative_retention_disposition": "UNRESOLVED_NO_VALUE_RESEALED",
        "additional_raw_scan_authorized": False,
    }
    _require_equal("unresolved finding", unresolved, expected_unresolved)
    _require_equal(
        "attestation disposition",
        attestation["disposition"],
        "FAIL_CLOSED_RETAINED_BYTE_NUMERATOR_UNRESOLVED",
    )
    _require_equal(
        "attestation commit gate",
        attestation["commit_gate"],
        "CLOSED_PENDING_INDEPENDENT_RESULT_REVIEW",
    )
    _require_equal(
        "result disposition",
        result["disposition"],
        "COMPLETED_AGGREGATE_EVIDENCE_REVIEW_REQUIRED_NO_VALUE_RESEALED",
    )
    _require_equal(
        "result commit gate",
        result["commit_gate"],
        "CLOSED_PENDING_INDEPENDENT_RESULT_REVIEW",
    )

    execution = attestation["execution"]
    _require_equal("completed raw scans", execution["completed_raw_source_scans"], 1)
    zero_fields = (
        "aborted_partial_raw_source_scan_attempts",
        "raw_source_copies",
        "frame_materializations",
        "fixture_materializations",
        "model_fits",
        "gate_executions",
        "oos_accesses",
        "local_inference_calls",
        "model_downloads",
        "provider_calls",
        "network_attempts",
        "dependency_changes",
        "commits_during_rerun",
        "pushes_during_rerun",
    )
    for field in zero_fields:
        _require_equal(f"execution counter {field}", execution[field], 0)
    _require_subset("result execution", result["execution"], {field: value for field, value in execution.items() if field in result["execution"]})
    _require_equal(
        "normative retention disposition",
        attestation["unresolved_finding"]["normative_retention_disposition"],
        "UNRESOLVED_NO_VALUE_RESEALED",
    )

    print("PASS_R03_N1_RECONCILIATION_RERUN " f"attestation_sha256={attestation['attestation_sha256']} " f"result_sha256={result['result_sha256']} " f"paired_sha256={paired.evidence_sha256} " f"completed_raw_source_scans={execution['completed_raw_source_scans']} " "commits_during_rerun=0 pushes_during_rerun=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
