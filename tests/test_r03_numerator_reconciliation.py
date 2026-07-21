from __future__ import annotations

from pathlib import Path

import pytest

from v2.research.news_reasoning import r03_numerator_reconciliation as targeted
from v2.research.news_reasoning.r03_numerator_reconciliation import (
    build_numerator_targeted_evidence,
    R03AffectedFrameByteLedger,
    R03NumeratorTargetedEvidence,
    R03NumeratorTargetedPermitV1,
    runtime_numerator_targeted_pins,
    validate_numerator_execution_surface,
    validate_numerator_targeted_execution,
    validate_numerator_targeted_permit,
)
from v2.research.news_reasoning.r03_reconciliation import (
    CANONICAL_CLASSIFICATION,
    CANONICAL_CLASSIFICATION_PATH,
    R03N1ReconciliationPermitV1,
    R03ReconciliationError,
    runtime_contract_pins,
)
from v2.research.news_reasoning.r03_source import (
    IMPLEMENTATION_COMMIT,
    PLAN_COMMIT,
    R03DataCheckPermitV2,
    reject_raw_text_emission,
    root_path_sha256,
)
from v2.research.overlay.canonical import canonical_sha256


def _base_permit(root: Path) -> R03DataCheckPermitV2:
    unsigned = {
        "schema_version": "r03-data-check-permit-v2",
        "authorization": "READ_ONLY_DATA_CHECK_RERUN_AUTHORIZED",
        "root_path_sha256": root_path_sha256(root),
        "plan_commit": PLAN_COMMIT,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "early_close_session_count": 21,
        "early_close_sessions_sha256": "1" * 64,
        "calendar_session_count": 2514,
        "calendar_sha256": "2" * 64,
        "article_byte_cap": 32768,
        "ticker_session_byte_cap": 131072,
        "article_ordering": "available_at_desc_article_id_asc",
        "truncation_semantics": "headline_summary_then_utf8_content_prefix_omit_after_session_truncation",
        "rounding_rule": "ROUND_HALF_EVEN_2DP",
    }
    return R03DataCheckPermitV2(
        **unsigned,
        permit_sha256=canonical_sha256(unsigned),
    )


def _reconciliation_permit(root: Path) -> R03N1ReconciliationPermitV1:
    unsigned = {
        "schema_version": "r03-n1-reconciliation-permit-v1",
        "authorization": "READ_ONLY_DATA_CHECK_RECONCILIATION_RERUN_AUTHORIZED",
        "base_permit": _base_permit(root).model_dump(mode="json"),
        "canonical_classification_path": CANONICAL_CLASSIFICATION_PATH,
        "canonical_classification": CANONICAL_CLASSIFICATION,
        **runtime_contract_pins(),
        "whitespace_policy": "PRESERVE",
        "newline_policy": "CRLF_CR_TO_LF",
        "unicode_policy": "NFC",
        "nul_policy": "REJECT",
    }
    return R03N1ReconciliationPermitV1(
        **unsigned,
        permit_sha256=canonical_sha256(unsigned),
    )


def _targeted_permit(root: Path) -> R03NumeratorTargetedPermitV1:
    unsigned = {
        "schema_version": "r03-n1-numerator-targeted-permit-v1",
        "authorization": "READ_ONLY_R03_N1_NUMERATOR_TARGETED_SCAN_AUTHORIZED",
        "base_reconciliation_permit": _reconciliation_permit(root).model_dump(mode="json"),
        "accepted_result_sha256": targeted.ACCEPTED_RESULT_SHA256,
        "accepted_paired_evidence_sha256": targeted.ACCEPTED_PAIRED_EVIDENCE_SHA256,
        "expected_affected_frame_count": targeted.EXPECTED_AFFECTED_FRAME_COUNT,
        "sealed_retained_text_bytes": targeted.SEALED_RETAINED_TEXT_BYTES,
        "reconciliation_retained_text_bytes": targeted.RECONCILIATION_RETAINED_TEXT_BYTES,
        "unaffected_retained_text_bytes": targeted.UNAFFECTED_RETAINED_TEXT_BYTES,
        "sealed_implied_affected_text_bytes": targeted.SEALED_IMPLIED_AFFECTED_TEXT_BYTES,
        **runtime_numerator_targeted_pins(),
        "execution_commit": "1" * 40,
        "targeted_module_filesystem_sha256": "2" * 64,
        "targeted_runner_filesystem_sha256": "3" * 64,
        "base_runner_filesystem_sha256": "4" * 64,
        "prior_driver_filesystem_sha256": "5" * 64,
        "event_index_filesystem_sha256": "6" * 64,
        "calendar_input_filesystem_sha256": "7" * 64,
    }
    return R03NumeratorTargetedPermitV1(
        **unsigned,
        permit_sha256=canonical_sha256(unsigned),
    )


def _ledger(**updates: int) -> R03AffectedFrameByteLedger:
    values = {
        "source_appearances": 5,
        "preceding_included_appearances": 3,
        "trigger_included_appearances": 1,
        "omitted_after_trigger_appearances": 1,
        "reconciliation_retained_appearances": 4,
        "preceding_included_zero_byte_appearances": 0,
        "trigger_included_zero_byte_appearances": 0,
        "source_text_bytes": 200_000,
        "preceding_headline_bytes": 300,
        "preceding_summary_bytes": 700,
        "preceding_content_bytes": 120_000,
        "trigger_headline_bytes": 100,
        "trigger_summary_bytes": 200,
        "trigger_content_prefix_bytes": 9_772,
        "reconciliation_retained_text_bytes": 131_072,
    }
    values.update(updates)
    return R03AffectedFrameByteLedger(**values)


def test_component_ledger_and_evidence_derive_exact_candidates() -> None:
    ledgers = (
        _ledger(),
        _ledger(
            source_appearances=2,
            preceding_included_appearances=0,
            trigger_included_appearances=1,
            omitted_after_trigger_appearances=1,
            reconciliation_retained_appearances=1,
            source_text_bytes=50_000,
            preceding_headline_bytes=0,
            preceding_summary_bytes=0,
            preceding_content_bytes=0,
            trigger_headline_bytes=50,
            trigger_summary_bytes=75,
            trigger_content_prefix_bytes=0,
            reconciliation_retained_text_bytes=125,
        ),
    )
    evidence = build_numerator_targeted_evidence(
        total_news_positive_frames=151_820,
        affected_ledgers=reversed(ledgers),
    )
    assert evidence.affected_frame_count == 2
    assert evidence.reconciliation_affected_text_bytes == 131_197
    assert evidence.trigger_only_affected_text_bytes == 10_197
    assert evidence.preceding_headline_summary_plus_trigger_text_bytes == 11_197
    assert evidence.all_retained_headline_summary_text_bytes == 1_425
    assert evidence.sealed_implied_affected_text_bytes == 7_381_768
    assert R03NumeratorTargetedEvidence.model_validate(evidence.model_dump(mode="json")) == evidence
    reject_raw_text_emission(evidence.model_dump(mode="json"))


@pytest.mark.parametrize(
    "updates, match",
    (
        ({"source_appearances": 4}, "source appearance partition"),
        ({"reconciliation_retained_appearances": 3}, "retained appearance partition"),
        ({"preceding_included_zero_byte_appearances": 4}, "preceding zero-byte"),
        (
            {
                "trigger_included_appearances": 0,
                "reconciliation_retained_appearances": 3,
            },
            "omitted trigger",
        ),
        ({"reconciliation_retained_text_bytes": 131_071}, "component byte sum"),
        (
            {
                "source_text_bytes": 131_073,
                "preceding_content_bytes": 120_001,
                "reconciliation_retained_text_bytes": 131_073,
            },
            "session cap",
        ),
    ),
)
def test_component_ledger_invariants_fail_closed(updates: dict[str, int], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        _ledger(**updates)


def test_evidence_tamper_and_order_fail_closed() -> None:
    evidence = build_numerator_targeted_evidence(
        total_news_positive_frames=10,
        affected_ledgers=(
            _ledger(),
            _ledger(
                source_text_bytes=210_000,
                preceding_content_bytes=119_999,
                reconciliation_retained_text_bytes=131_071,
            ),
        ),
    )
    value = evidence.model_dump(mode="json")
    value["trigger_only_affected_text_bytes"] += 1
    with pytest.raises(ValueError, match="derived evidence"):
        R03NumeratorTargetedEvidence.model_validate(value)
    reversed_value = evidence.model_dump(mode="json")
    reversed_value["ledgers"] = list(reversed(reversed_value["ledgers"]))
    unsigned = {key: item for key, item in reversed_value.items() if key != "evidence_sha256"}
    reversed_value["evidence_sha256"] = canonical_sha256(unsigned)
    with pytest.raises(ValueError, match="ledger order"):
        R03NumeratorTargetedEvidence.model_validate(reversed_value)


def test_runtime_targeted_pins_are_stable() -> None:
    assert runtime_numerator_targeted_pins() == {
        "ledger_semantics_id": "preserve-v2-before-trigger-trigger-after-component-ledger-v1",
        "ledger_schema_sha256": "5cab84bd1e26bd2ffb08fe7f5acd9ff7f374bb9c3a76d0e2f965aad631067de6",
        "ledger_implementation_sha256": "a0c2a9e05fed829b5bf6b6ee9df2796a9e26aa3429d75a31934b6e29d4ff281b",
    }


def test_targeted_permit_round_trip_and_root_identity(tmp_path: Path) -> None:
    permit = _targeted_permit(tmp_path)
    assert validate_numerator_targeted_permit(permit, permit.permit_sha256) == permit
    assert validate_numerator_targeted_execution(tmp_path, permit, permit.permit_sha256) == permit
    with pytest.raises(R03ReconciliationError, match="source root identity"):
        validate_numerator_targeted_execution(
            tmp_path / "other",
            permit,
            permit.permit_sha256,
        )


@pytest.mark.parametrize(
    "field",
    (
        "accepted_result_sha256",
        "accepted_paired_evidence_sha256",
        "expected_affected_frame_count",
        "sealed_retained_text_bytes",
        "reconciliation_retained_text_bytes",
        "unaffected_retained_text_bytes",
        "sealed_implied_affected_text_bytes",
        "ledger_semantics_id",
        "ledger_schema_sha256",
        "ledger_implementation_sha256",
    ),
)
def test_resigned_targeted_permit_forgery_fails_closed(
    tmp_path: Path,
    field: str,
) -> None:
    permit = _targeted_permit(tmp_path)
    current = getattr(permit, field)
    forged_value: object = "0" * 64 if isinstance(current, str) else current + 1
    forged = permit.model_copy(update={field: forged_value})
    unsigned = forged.model_dump(mode="json", exclude={"permit_sha256"})
    forged = forged.model_copy(update={"permit_sha256": canonical_sha256(unsigned)})
    with pytest.raises(R03ReconciliationError):
        validate_numerator_targeted_permit(forged, forged.permit_sha256)


def test_targeted_permit_requires_instance_and_external_pin(tmp_path: Path) -> None:
    with pytest.raises(R03ReconciliationError, match="permit required"):
        validate_numerator_targeted_permit(None, "0" * 64)
    permit = _targeted_permit(tmp_path)
    with pytest.raises(R03ReconciliationError, match="explicitly pinned"):
        validate_numerator_targeted_permit(permit, "0" * 64)


def test_targeted_execution_surface_is_exact(tmp_path: Path) -> None:
    permit = _targeted_permit(tmp_path)
    observed = {field: getattr(permit, field) for field in targeted.EXECUTION_SURFACE_FIELDS}
    validate_numerator_execution_surface(permit, observed)
    with pytest.raises(R03ReconciliationError, match="pin set mismatch"):
        validate_numerator_execution_surface(permit, {"execution_commit": "1" * 40})
    for field in targeted.EXECUTION_SURFACE_FIELDS:
        forged = dict(observed)
        forged[field] = "0" * len(forged[field])
        with pytest.raises(R03ReconciliationError, match=field):
            validate_numerator_execution_surface(permit, forged)


def test_runtime_ledger_drift_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    permit = _targeted_permit(tmp_path)
    monkeypatch.setattr(targeted, "_ledger_key", lambda ledger: (0,))
    with pytest.raises(R03ReconciliationError, match="ledger_implementation_sha256"):
        validate_numerator_targeted_permit(permit, permit.permit_sha256)
