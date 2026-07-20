from __future__ import annotations

import unicodedata
from datetime import datetime, UTC
from pathlib import Path

import pytest
from pydantic import ValidationError

import v2.research.news_reasoning.r03_reconciliation as reconciliation
from v2.research.news_reasoning.r03_contracts import PLAN_COMMIT, R03ArticleRecord
from v2.research.news_reasoning.r03_reconciliation import (
    build_paired_frame_diff_evidence,
    CANONICAL_CLASSIFICATION,
    CANONICAL_CLASSIFICATION_PATH,
    decode_provider_text,
    measure_input_text_bytes,
    R03N1ReconciliationPermitV1,
    R03PairedAffectedFrame,
    R03PairedFrameDiffEvidence,
    R03ReconciliationError,
    retained_appearance,
    runtime_contract_pins,
    select_reconciliation_versions,
    validate_reconciliation_execution,
    validate_reconciliation_permit,
)
from v2.research.news_reasoning.r03_source import (
    IMPLEMENTATION_COMMIT,
    public_retention_v2,
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
    return R03DataCheckPermitV2(**unsigned, permit_sha256=canonical_sha256(unsigned))


def _permit(root: Path) -> R03N1ReconciliationPermitV1:
    pins = runtime_contract_pins()
    unsigned = {
        "schema_version": "r03-n1-reconciliation-permit-v1",
        "authorization": "READ_ONLY_DATA_CHECK_RECONCILIATION_RERUN_AUTHORIZED",
        "base_permit": _base_permit(root).model_dump(mode="json"),
        "canonical_classification_path": CANONICAL_CLASSIFICATION_PATH,
        "canonical_classification": CANONICAL_CLASSIFICATION,
        **pins,
        "whitespace_policy": "PRESERVE",
        "newline_policy": "CRLF_CR_TO_LF",
        "unicode_policy": "NFC",
        "nul_policy": "REJECT",
    }
    return R03N1ReconciliationPermitV1(**unsigned, permit_sha256=canonical_sha256(unsigned))


def _record(*, content: str, updated_hour: int = 13) -> R03ArticleRecord:
    return R03ArticleRecord(
        article_id="synthetic-article",
        created_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        updated_at=datetime(2024, 1, 2, updated_hour, tzinfo=UTC),
        symbols=("AAA",),
        source=" source ",
        headline=" headline ",
        summary=" summary ",
        content=content,
        input_text_sha256="3" * 64,
    )


def test_decoder_and_record_contract_preserve_whitespace() -> None:
    assert decode_provider_text("  value\r\n") == "  value\r\n"
    assert _record(content=" content ").content == " content "
    with pytest.raises(TypeError, match="string or null"):
        decode_provider_text(7)


def test_runtime_contract_pins_are_stable() -> None:
    assert runtime_contract_pins() == {
        "normalization_semantics_id": "preserve-whitespace-nfc-lf-reject-nul-v1",
        "normalization_implementation_sha256": "c4a77fc184ac2bf3766ef0949584c43294f5d28de1083b9d0112ac95209d0bae",
        "decoder_semantics_id": "strict-string-or-null-preserve-codepoints-v1",
        "decoder_implementation_sha256": "c0030fa39c1d6f47d62a052cde757c30af12f0e8d3c295a7951a8825fd0d7780",
        "article_record_semantics_id": "strict-record-no-implicit-text-strip-v1",
        "article_record_implementation_sha256": "6f54ba168db4322c93576d46133e9f6364497873869e528ea5acecf3c00f33e4",
        "version_tie_break_id": "max-available-updated-input-payload-text-sha256-v1",
        "version_implementation_sha256": "53e02571f782c3a8df45437cef6bc64dc7835917f693c5e593135e51994bb810",
        "retained_predicate_id": "included-flag-with-zero-byte-diagnostics-v2",
        "retained_predicate_implementation_sha256": "5fb5d814483b001bcdea9e7c701007ab8f3d01be45fdd5b7f021d4c7b1368116",
        "input_byte_measurement_id": "appearance-weighted-canonical-hsc-utf8-before-caps-v2",
        "input_byte_measurement_implementation_sha256": "70cad6961d40343cfbfc0777e6c266fdc176aca04de15e29637dc0ce42ef10ec",
        "paired_diff_schema_sha256": "9e04049787ef73d3845cc0b55614109245e9804ac21d14afae2d17bdad99e1c9",
        "paired_diff_implementation_sha256": "1e48e4e9f5906223f8b9edd8536ad4963978065d4aa5679b87f684e21fc622de",
    }


def test_permit_round_trip_and_root_identity_validate_before_execution(tmp_path: Path) -> None:
    permit = _permit(tmp_path)
    assert validate_reconciliation_permit(permit, permit.permit_sha256) == permit
    assert validate_reconciliation_execution(tmp_path, permit, permit.permit_sha256) == permit
    with pytest.raises(R03ReconciliationError, match="source root identity"):
        validate_reconciliation_execution(tmp_path / "other", permit, permit.permit_sha256)


def test_runtime_pin_calculation_failure_uses_contract_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    permit = _permit(tmp_path)

    def fail_pin_calculation() -> dict[str, str]:
        raise IndexError("synthetic pin probe failure")

    monkeypatch.setattr(reconciliation, "runtime_contract_pins", fail_pin_calculation)
    with pytest.raises(R03ReconciliationError, match="pin calculation failed"):
        validate_reconciliation_permit(permit, permit.permit_sha256)


def test_model_copy_literal_forgery_is_closed_by_round_trip(tmp_path: Path) -> None:
    permit = _permit(tmp_path)
    forged = permit.model_copy(update={"whitespace_policy": "STRIP"})
    unsigned = forged.model_dump(mode="json", exclude={"permit_sha256"})
    forged = forged.model_copy(update={"permit_sha256": canonical_sha256(unsigned)})
    with pytest.raises(R03ReconciliationError, match="contract validation"):
        validate_reconciliation_permit(forged, forged.permit_sha256)


@pytest.mark.parametrize(
    "field",
    (
        "normalization_implementation_sha256",
        "decoder_implementation_sha256",
        "article_record_implementation_sha256",
        "version_implementation_sha256",
        "retained_predicate_implementation_sha256",
        "input_byte_measurement_implementation_sha256",
        "paired_diff_schema_sha256",
        "paired_diff_implementation_sha256",
    ),
)
def test_re_signed_runtime_hash_forgery_fails_before_use(tmp_path: Path, field: str) -> None:
    permit = _permit(tmp_path)
    forged = permit.model_copy(update={field: "f" * 64})
    unsigned = forged.model_dump(mode="json", exclude={"permit_sha256"})
    forged = forged.model_copy(update={"permit_sha256": canonical_sha256(unsigned)})
    with pytest.raises(R03ReconciliationError, match=field):
        validate_reconciliation_permit(forged, forged.permit_sha256)


def test_runtime_behavior_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    permit = _permit(tmp_path)
    monkeypatch.setattr(reconciliation, "canonicalize_text", lambda value: value.strip() if value else value)
    with pytest.raises(R03ReconciliationError, match="normalization_implementation_sha256"):
        validate_reconciliation_permit(permit, permit.permit_sha256)


def test_nfkc_for_nfc_drift_changes_normalization_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    permit = _permit(tmp_path)
    original = reconciliation.canonicalize_text

    def nfkc(value: str | None) -> str | None:
        normalized = original(value)
        return None if normalized is None else unicodedata.normalize("NFKC", normalized)

    monkeypatch.setattr(reconciliation, "canonicalize_text", nfkc)
    with pytest.raises(R03ReconciliationError, match="normalization_implementation_sha256"):
        validate_reconciliation_permit(permit, permit.permit_sha256)


def test_source_inclusion_changes_input_byte_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    permit = _permit(tmp_path)
    original = reconciliation.measure_input_text_bytes

    def includes_source(record: R03ArticleRecord) -> int:
        source = reconciliation.canonicalize_text(record.source)
        return original(record) + (len(source.encode("utf-8")) if source is not None else 0)

    monkeypatch.setattr(reconciliation, "measure_input_text_bytes", includes_source)
    with pytest.raises(R03ReconciliationError, match="input_byte_measurement_implementation_sha256"):
        validate_reconciliation_permit(permit, permit.permit_sha256)


def test_version_key_priority_swap_changes_version_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    permit = _permit(tmp_path)

    def reordered(record: R03ArticleRecord) -> tuple[datetime, datetime, str, str]:
        return (
            record.updated_at,
            record.available_at,
            record.input_text_sha256,
            reconciliation.canonical_payload_text_sha256(record),
        )

    monkeypatch.setattr(reconciliation, "reconciliation_version_key", reordered)
    with pytest.raises(R03ReconciliationError, match="version_implementation_sha256"):
        validate_reconciliation_permit(permit, permit.permit_sha256)


@pytest.mark.parametrize("mutation", ("reverse", "constant"))
def test_pair_order_drift_changes_paired_implementation_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    permit = _permit(tmp_path)
    original = reconciliation._pair_key
    replacement = (lambda pair: tuple(-value for value in original(pair))) if mutation == "reverse" else (lambda pair: (0,))
    monkeypatch.setattr(reconciliation, "_pair_key", replacement)
    with pytest.raises(R03ReconciliationError, match="paired_diff_implementation_sha256"):
        validate_reconciliation_permit(permit, permit.permit_sha256)


def test_base_permit_self_hash_is_revalidated(tmp_path: Path) -> None:
    permit = _permit(tmp_path)
    forged_base = permit.base_permit.model_copy(update={"calendar_sha256": "9" * 64})
    forged = permit.model_copy(update={"base_permit": forged_base})
    unsigned = forged.model_dump(mode="json", exclude={"permit_sha256"})
    forged = forged.model_copy(update={"permit_sha256": canonical_sha256(unsigned)})
    with pytest.raises(R03ReconciliationError, match="base data-check permit self-hash"):
        validate_reconciliation_permit(forged, forged.permit_sha256)


def test_content_payload_hash_is_final_version_tie_break() -> None:
    first = _record(content="alpha")
    second = _record(content="beta")
    selected = select_reconciliation_versions((first, second))
    assert len(selected) == 1
    assert reconciliation.reconciliation_version_key(selected[0]) == max(
        reconciliation.reconciliation_version_key(first),
        reconciliation.reconciliation_version_key(second),
    )


def test_retained_predicate_observes_included_zero_bytes_like_public_v2() -> None:
    assert retained_appearance(included=True, source_bytes=7, retained_bytes=1) is True
    assert retained_appearance(included=True, source_bytes=7, retained_bytes=0) is True
    assert retained_appearance(included=True, source_bytes=0, retained_bytes=0) is True
    assert retained_appearance(included=False, source_bytes=7, retained_bytes=0) is False
    public = public_retention_v2((True,), ((True, 0, 0),))
    assert public.article_appearances_retained == 1
    with pytest.raises(ValueError, match="omitted"):
        retained_appearance(included=False, source_bytes=7, retained_bytes=1)


def test_input_byte_measurement_preserves_whitespace_and_excludes_source() -> None:
    record = _record(content=" content ")
    expected = sum(len(value.encode("utf-8")) for value in (record.headline, record.summary, record.content) if value is not None)
    assert measure_input_text_bytes(record) == expected
    empty = record.model_copy(update={"headline": None, "summary": None, "content": None})
    assert measure_input_text_bytes(empty) == 0


def test_paired_frame_evidence_is_identifier_free_self_hashed_and_derived() -> None:
    pairs = (
        R03PairedAffectedFrame(
            source_appearances=8,
            prior_retained_appearances=0,
            reconciliation_retained_appearances=7,
            zero_source_appearances=1,
            prior_included_zero_byte_appearances=0,
            reconciliation_included_zero_byte_appearances=1,
            source_text_bytes=200_000,
            prior_retained_text_bytes=0,
            reconciliation_retained_text_bytes=131_072,
        ),
        R03PairedAffectedFrame(
            source_appearances=5,
            prior_retained_appearances=4,
            reconciliation_retained_appearances=4,
            zero_source_appearances=0,
            prior_included_zero_byte_appearances=0,
            reconciliation_included_zero_byte_appearances=0,
            source_text_bytes=150_000,
            prior_retained_text_bytes=120_000,
            reconciliation_retained_text_bytes=120_000,
        ),
    )
    evidence = build_paired_frame_diff_evidence(
        total_news_positive_frames=151_820,
        affected_pairs=reversed(pairs),
    )
    assert evidence.affected_frame_count == 2
    assert evidence.prior_zero_retained_text_frames == 1
    assert evidence.reconciliation_zero_retained_text_frames == 0
    assert evidence.changed_retained_text_frames == 1
    assert evidence.retained_text_bytes_delta == 131_072
    assert evidence.zero_source_appearances_total == 1
    assert evidence.reconciliation_included_zero_byte_appearances_total == 1
    reject_raw_text_emission(evidence.model_dump(mode="json"))
    assert all("id" not in key.casefold() for pair in evidence.pairs for key in type(pair).model_fields)


def test_paired_frame_evidence_tampering_fails_identity() -> None:
    pair = R03PairedAffectedFrame(
        source_appearances=2,
        prior_retained_appearances=1,
        reconciliation_retained_appearances=2,
        zero_source_appearances=0,
        prior_included_zero_byte_appearances=0,
        reconciliation_included_zero_byte_appearances=0,
        source_text_bytes=140_000,
        prior_retained_text_bytes=0,
        reconciliation_retained_text_bytes=131_072,
    )
    evidence = build_paired_frame_diff_evidence(
        total_news_positive_frames=151_820,
        affected_pairs=(pair,),
    )
    value = evidence.model_dump(mode="json")
    value["retained_text_bytes_delta"] += 1
    with pytest.raises(ValidationError, match="derived field mismatch"):
        R03PairedFrameDiffEvidence.model_validate(value)


def test_paired_frame_count_cannot_exceed_total_frames() -> None:
    pair = R03PairedAffectedFrame(
        source_appearances=1,
        prior_retained_appearances=1,
        reconciliation_retained_appearances=1,
        zero_source_appearances=0,
        prior_included_zero_byte_appearances=0,
        reconciliation_included_zero_byte_appearances=0,
        source_text_bytes=1,
        prior_retained_text_bytes=1,
        reconciliation_retained_text_bytes=1,
    )
    with pytest.raises(ValidationError, match="affected frame count exceeds"):
        build_paired_frame_diff_evidence(
            total_news_positive_frames=1,
            affected_pairs=(pair, pair),
        )


def test_prior_inconsistency_is_diagnostic_but_reconciliation_inconsistency_is_rejected() -> None:
    prior_anomaly = R03PairedAffectedFrame(
        source_appearances=2,
        prior_retained_appearances=0,
        reconciliation_retained_appearances=1,
        zero_source_appearances=0,
        prior_included_zero_byte_appearances=0,
        reconciliation_included_zero_byte_appearances=0,
        source_text_bytes=10,
        prior_retained_text_bytes=1,
        reconciliation_retained_text_bytes=1,
    )
    evidence = build_paired_frame_diff_evidence(
        total_news_positive_frames=1,
        affected_pairs=(prior_anomaly,),
    )
    assert evidence.prior_appearance_byte_inconsistency_frames == 1
    assert evidence.reconciliation_appearance_byte_inconsistency_frames == 0
    with pytest.raises(ValidationError, match="reconciliation zero-retained frame"):
        R03PairedAffectedFrame(
            source_appearances=2,
            prior_retained_appearances=1,
            reconciliation_retained_appearances=0,
            zero_source_appearances=0,
            prior_included_zero_byte_appearances=0,
            reconciliation_included_zero_byte_appearances=0,
            source_text_bytes=10,
            prior_retained_text_bytes=1,
            reconciliation_retained_text_bytes=1,
        )


def test_classification_paths_have_distinct_normative_roles() -> None:
    assert CANONICAL_CLASSIFICATION_PATH == "provenance_classification.classification"
    assert CANONICAL_CLASSIFICATION == "FIRST_V2_RAW_MEASUREMENT_EXPOSED_UNVERIFIED_SEAL"
    assert reconciliation.CAUSE_STATUS_PATH == "investigation_note.classification"
