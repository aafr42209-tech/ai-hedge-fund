from __future__ import annotations

"""Provider-free verifier for the R03 data-check amendment.

The committed CLI verifies aggregate-only amendment artifacts.  A future raw
rerun must call ``run_authorized_data_check`` with a separately issued v2
permit and an injected corpus adapter; permit validation completes before that
adapter receives the root path.
"""

import hashlib
import json
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v2.research.news_reasoning.r03_source import (  # noqa: E402
    R03DataCheckPermitV2,
    R03PublicRetentionV2,
    recompute_payload_retention_v2_from_read_only_raw_source,
    reject_raw_text_emission,
    round_half_even_percent,
)
from v2.research.overlay.canonical import canonical_sha256  # noqa: E402

LINEAGE_PATH = "docs/r03-news-reasoning-data-check-amendment-lineage.json"
EVIDENCE_PATH = "docs/r03-news-reasoning-data-check-amendment-evidence.json"
MANIFEST_PATH = "docs/r03-news-reasoning-data-check-amendment-zero-call-manifest.json"
CHARTER_PATH = "docs/r03-news-reasoning-charter-draft.md"
PREREG_PATH = "docs/r03-news-reasoning-provider-free-preregistration-draft.md"
VERIFIER_PATH = "scripts/r03_news_reasoning_data_check_verify.py"
SOURCE_PATH = "v2/research/news_reasoning/r03_source.py"
TEST_PATHS = (
    "tests/test_r03_source.py",
    "tests/test_r03_data_check_verify.py",
)
IMMUTABLE_AUDIT_PATH = "docs/r03-news-reasoning-provider-free-coverage-audit.json"
IMMUTABLE_AUDIT_SHA256 = "6275292839b9446825bc8d05cc334a82dc7fe865067501895fd0f2c15c821984"
EXPECTED_FRACTIONS = {
    "full_frames": (150_394, 151_820, "99.06"),
    "article_appearances": (695_948, 702_489, "99.07"),
    "text_bytes": (1_435_742_878, 1_585_976_846, "90.53"),
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


def safe_aggregate_output(
    permit: R03DataCheckPermitV2,
    retention: R03PublicRetentionV2,
) -> dict[str, Any]:
    output = {
        "schema_version": "r03-data-check-output-v2",
        "status": "COMPLETED_AGGREGATES_ONLY",
        "pins": {
            "permit_sha256": permit.permit_sha256,
            "root_path_sha256": permit.root_path_sha256,
            "early_close_session_count": permit.early_close_session_count,
            "early_close_sessions_sha256": permit.early_close_sessions_sha256,
            "calendar_session_count": permit.calendar_session_count,
            "calendar_sha256": permit.calendar_sha256,
            "article_byte_cap": permit.article_byte_cap,
            "ticker_session_byte_cap": permit.ticker_session_byte_cap,
            "article_ordering_sha256": hashlib.sha256(permit.article_ordering.encode("ascii")).hexdigest(),
            "truncation_semantics_sha256": hashlib.sha256(permit.truncation_semantics.encode("ascii")).hexdigest(),
            "rounding_rule_sha256": hashlib.sha256(permit.rounding_rule.encode("ascii")).hexdigest(),
        },
        "retention": retention.model_dump(mode="json"),
    }
    reject_raw_text_emission(output)
    return output


def run_authorized_data_check(
    root: Path,
    permit: R03DataCheckPermitV2 | None,
    expected_permit_sha256: str,
    compute_rows: Callable[[Path], tuple[Iterable[bool], Iterable[tuple[bool, int, int]]]],
) -> dict[str, Any]:
    retention = recompute_payload_retention_v2_from_read_only_raw_source(
        root,
        permit,
        expected_permit_sha256,
        compute_rows,
    )
    assert permit is not None
    return safe_aggregate_output(permit, retention)


def assert_lineage(lineage: dict[str, Any]) -> None:
    assert_self_hash(lineage, "lineage_sha256", "lineage")
    if lineage.get("authority") != "R03_DATA_CHECK_AMENDMENT_CODE_AUTHORIZED":
        raise VerificationError("lineage authority mismatch")
    if lineage.get("organizational_independence_established") is not False:
        raise VerificationError("organizational independence must remain false")
    if lineage.get("normative_contract") != {
        "article_byte_cap": 32768,
        "ticker_session_byte_cap": 131072,
        "article_ordering": "available_at_desc_article_id_asc",
        "truncation_semantics": "headline_summary_then_utf8_content_prefix_omit_after_session_truncation",
        "rounding_rule": "ROUND_HALF_EVEN_2DP",
    }:
        raise VerificationError("normative contract mismatch")
    retention = lineage.get("retention", {})
    for key, (numerator, denominator, display) in EXPECTED_FRACTIONS.items():
        expected = {
            "numerator": numerator,
            "denominator": denominator,
            "display_pct_2dp": display,
        }
        if retention.get(key) != expected:
            raise VerificationError(f"lineage fraction mismatch: {key}")
        if round_half_even_percent(numerator, denominator) != display:
            raise VerificationError(f"lineage rounding mismatch: {key}")
    counters = lineage.get("boundary_counters")
    if counters != ZERO_COUNTERS:
        raise VerificationError("lineage boundary counters are not the sealed zero set")


def assert_amendment_artifacts() -> dict[str, Any]:
    if sha256_file(IMMUTABLE_AUDIT_PATH) != IMMUTABLE_AUDIT_SHA256:
        raise VerificationError("immutable P5 coverage audit changed")
    lineage = load_json(LINEAGE_PATH)
    evidence = load_json(EVIDENCE_PATH)
    manifest = load_json(MANIFEST_PATH)
    assert_lineage(lineage)
    assert_self_hash(evidence, "evidence_sha256", "evidence")
    if evidence.get("boundary_counters") != ZERO_COUNTERS:
        raise VerificationError("evidence boundary counters are not zero")
    pinned = evidence.get("artifact_sha256", {})
    expected_pins = (
        SOURCE_PATH,
        *TEST_PATHS,
        VERIFIER_PATH,
        CHARTER_PATH,
        PREREG_PATH,
        LINEAGE_PATH,
    )
    if set(pinned) != set(expected_pins):
        raise VerificationError("evidence artifact pin set mismatch")
    for relative in expected_pins:
        if pinned.get(relative) != sha256_file(relative):
            raise VerificationError(f"evidence artifact hash mismatch: {relative}")
    if evidence.get("lineage_canonical_sha256") != lineage.get("lineage_sha256"):
        raise VerificationError("evidence-to-lineage canonical pin mismatch")
    if manifest.get("boundary_counters") != ZERO_COUNTERS:
        raise VerificationError("manifest boundary counters are not zero")
    manifest_pins = manifest.get("artifact_sha256", {})
    expected_manifest_pins = (
        EVIDENCE_PATH,
        LINEAGE_PATH,
        SOURCE_PATH,
        VERIFIER_PATH,
        CHARTER_PATH,
        PREREG_PATH,
    )
    if set(manifest_pins) != set(expected_manifest_pins):
        raise VerificationError("manifest artifact pin set mismatch")
    for relative in expected_manifest_pins:
        if manifest_pins.get(relative) != sha256_file(relative):
            raise VerificationError(f"manifest artifact hash mismatch: {relative}")
    reject_raw_text_emission(lineage)
    reject_raw_text_emission(evidence)
    reject_raw_text_emission(manifest)
    return {
        "lineage_sha256": lineage["lineage_sha256"],
        "evidence_sha256": evidence["evidence_sha256"],
        "manifest_filesystem_sha256": sha256_file(MANIFEST_PATH),
    }


def main() -> int:
    try:
        pins = assert_amendment_artifacts()
        print("PASS_R03_DATA_CHECK_AMENDMENT " f"lineage_sha256={pins['lineage_sha256']} " f"evidence_sha256={pins['evidence_sha256']} " f"manifest_sha256={pins['manifest_filesystem_sha256']} " "raw_source_traversals=0 provider_calls=0 network_attempts=0")
        return 0
    except Exception as exc:
        print(f"FAIL_R03_DATA_CHECK_AMENDMENT {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
