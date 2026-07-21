from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Literal, Mapping

from pydantic import Field, field_validator, model_validator

from v2.research.news_reasoning.r03_contracts import SHA256_PATTERN
from v2.research.news_reasoning.r03_reconciliation import (
    R03N1ReconciliationPermitV1,
    R03ReconciliationError,
    validate_reconciliation_execution,
    validate_reconciliation_permit,
)
from v2.research.overlay.canonical import canonical_sha256
from v2.research.overlay.contracts import StrictModel

TARGETED_PERMIT_VERSION = "r03-n1-numerator-targeted-permit-v1"
LEDGER_SCHEMA_VERSION = "r03-n1-affected-frame-byte-ledger-v1"
LEDGER_SEMANTICS_ID = "preserve-v2-before-trigger-trigger-after-component-ledger-v1"
ACCEPTED_RESULT_SHA256 = "6046eab6643d31254c398ad1e4183931130acf0ca076cd5aa93b1a69902265eb"
ACCEPTED_PAIRED_EVIDENCE_SHA256 = "4669d70649ce94178194e85eb80a40fe4b49145cfb6835d1ba1f2083714f7bdf"
EXPECTED_AFFECTED_FRAME_COUNT = 664
SEALED_RETAINED_TEXT_BYTES = 1_435_742_878
RECONCILIATION_RETAINED_TEXT_BYTES = 1_515_387_041
UNAFFECTED_RETAINED_TEXT_BYTES = 1_428_361_110
SEALED_IMPLIED_AFFECTED_TEXT_BYTES = 7_381_768
TICKER_SESSION_BYTE_CAP = 131_072


class R03AffectedFrameByteLedger(StrictModel):
    source_appearances: int = Field(gt=0)
    preceding_included_appearances: int = Field(ge=0)
    trigger_included_appearances: int = Field(ge=0, le=1)
    omitted_after_trigger_appearances: int = Field(ge=0)
    reconciliation_retained_appearances: int = Field(ge=0)
    preceding_included_zero_byte_appearances: int = Field(ge=0)
    trigger_included_zero_byte_appearances: int = Field(ge=0, le=1)
    source_text_bytes: int = Field(ge=0)
    preceding_headline_bytes: int = Field(ge=0)
    preceding_summary_bytes: int = Field(ge=0)
    preceding_content_bytes: int = Field(ge=0)
    trigger_headline_bytes: int = Field(ge=0)
    trigger_summary_bytes: int = Field(ge=0)
    trigger_content_prefix_bytes: int = Field(ge=0)
    reconciliation_retained_text_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_accounting(self) -> "R03AffectedFrameByteLedger":
        expected_source = self.preceding_included_appearances + 1 + self.omitted_after_trigger_appearances
        if self.source_appearances != expected_source:
            raise ValueError("source appearance partition mismatch")
        expected_retained = self.preceding_included_appearances + self.trigger_included_appearances
        if self.reconciliation_retained_appearances != expected_retained:
            raise ValueError("retained appearance partition mismatch")
        if self.preceding_included_zero_byte_appearances > self.preceding_included_appearances:
            raise ValueError("preceding zero-byte appearances exceed included appearances")
        if self.trigger_included_zero_byte_appearances > self.trigger_included_appearances:
            raise ValueError("trigger zero-byte appearance requires included trigger")
        trigger_bytes = self.trigger_headline_bytes + self.trigger_summary_bytes + self.trigger_content_prefix_bytes
        if self.trigger_included_appearances == 0 and trigger_bytes != 0:
            raise ValueError("omitted trigger cannot retain bytes")
        if self.trigger_included_zero_byte_appearances == 1 and trigger_bytes != 0:
            raise ValueError("zero-byte trigger cannot retain bytes")
        preceding_bytes = self.preceding_headline_bytes + self.preceding_summary_bytes + self.preceding_content_bytes
        if self.reconciliation_retained_text_bytes != preceding_bytes + trigger_bytes:
            raise ValueError("retained component byte sum mismatch")
        if self.reconciliation_retained_text_bytes > self.source_text_bytes:
            raise ValueError("retained bytes exceed source bytes")
        if self.reconciliation_retained_text_bytes > TICKER_SESSION_BYTE_CAP:
            raise ValueError("retained bytes exceed session cap")
        return self

    @property
    def trigger_retained_text_bytes(self) -> int:
        return self.trigger_headline_bytes + self.trigger_summary_bytes + self.trigger_content_prefix_bytes

    @property
    def preceding_retained_text_bytes(self) -> int:
        return self.preceding_headline_bytes + self.preceding_summary_bytes + self.preceding_content_bytes


def _ledger_key(ledger: R03AffectedFrameByteLedger) -> tuple[int, ...]:
    return tuple(ledger.model_dump(mode="json").values())


class R03NumeratorTargetedEvidence(StrictModel):
    schema_version: Literal["r03-n1-affected-frame-byte-ledger-v1"] = LEDGER_SCHEMA_VERSION
    selection: Literal["session_cap_affected_frames_only"] = "session_cap_affected_frames_only"
    total_news_positive_frames: int = Field(gt=0)
    affected_frame_count: int = Field(gt=0)
    ledgers: tuple[R03AffectedFrameByteLedger, ...]
    reconciliation_affected_text_bytes: int = Field(ge=0)
    trigger_only_affected_text_bytes: int = Field(ge=0)
    preceding_headline_plus_trigger_text_bytes: int = Field(ge=0)
    preceding_summary_plus_trigger_text_bytes: int = Field(ge=0)
    preceding_headline_summary_plus_trigger_text_bytes: int = Field(ge=0)
    all_retained_headline_summary_text_bytes: int = Field(ge=0)
    sealed_implied_affected_text_bytes: Literal[7381768] = SEALED_IMPLIED_AFFECTED_TEXT_BYTES
    ledger_multiset_sha256: str = Field(pattern=SHA256_PATTERN)
    evidence_sha256: str = Field(pattern=SHA256_PATTERN)

    @field_validator("ledgers", mode="before")
    @classmethod
    def deserialize_ledgers(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_identity(self) -> "R03NumeratorTargetedEvidence":
        if len(self.ledgers) != self.affected_frame_count:
            raise ValueError("affected frame count mismatch")
        if self.affected_frame_count > self.total_news_positive_frames:
            raise ValueError("affected frame count exceeds total frames")
        if tuple(sorted(self.ledgers, key=_ledger_key)) != self.ledgers:
            raise ValueError("ledger order is not canonical")
        expected = _derive_evidence_fields(self.ledgers)
        for field, value in expected.items():
            if getattr(self, field) != value:
                raise ValueError(f"derived evidence mismatch: {field}")
        unsigned = self.model_dump(mode="json", exclude={"evidence_sha256"})
        if canonical_sha256(unsigned) != self.evidence_sha256:
            raise ValueError("targeted evidence self-hash mismatch")
        return self


def _derive_evidence_fields(
    ledgers: tuple[R03AffectedFrameByteLedger, ...],
) -> dict[str, int | str]:
    serialized = [ledger.model_dump(mode="json") for ledger in ledgers]
    return {
        "reconciliation_affected_text_bytes": sum(ledger.reconciliation_retained_text_bytes for ledger in ledgers),
        "trigger_only_affected_text_bytes": sum(ledger.trigger_retained_text_bytes for ledger in ledgers),
        "preceding_headline_plus_trigger_text_bytes": sum(ledger.preceding_headline_bytes + ledger.trigger_retained_text_bytes for ledger in ledgers),
        "preceding_summary_plus_trigger_text_bytes": sum(ledger.preceding_summary_bytes + ledger.trigger_retained_text_bytes for ledger in ledgers),
        "preceding_headline_summary_plus_trigger_text_bytes": sum(ledger.preceding_headline_bytes + ledger.preceding_summary_bytes + ledger.trigger_retained_text_bytes for ledger in ledgers),
        "all_retained_headline_summary_text_bytes": sum(ledger.preceding_headline_bytes + ledger.preceding_summary_bytes + ledger.trigger_headline_bytes + ledger.trigger_summary_bytes for ledger in ledgers),
        "ledger_multiset_sha256": canonical_sha256(serialized),
    }


def build_numerator_targeted_evidence(
    *,
    total_news_positive_frames: int,
    affected_ledgers: Iterable[R03AffectedFrameByteLedger],
) -> R03NumeratorTargetedEvidence:
    ledgers = tuple(sorted(tuple(affected_ledgers), key=_ledger_key))
    unsigned: dict[str, Any] = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "selection": "session_cap_affected_frames_only",
        "total_news_positive_frames": total_news_positive_frames,
        "affected_frame_count": len(ledgers),
        "ledgers": [ledger.model_dump(mode="json") for ledger in ledgers],
        **_derive_evidence_fields(ledgers),
        "sealed_implied_affected_text_bytes": SEALED_IMPLIED_AFFECTED_TEXT_BYTES,
    }
    return R03NumeratorTargetedEvidence(
        **unsigned,
        evidence_sha256=canonical_sha256(unsigned),
    )


def numerator_ledger_schema_sha256() -> str:
    descriptor = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "semantics_id": LEDGER_SEMANTICS_ID,
        "selection": "session_cap_affected_frames_only",
        "component_partition": [
            "preceding_headline_bytes",
            "preceding_summary_bytes",
            "preceding_content_bytes",
            "trigger_headline_bytes",
            "trigger_summary_bytes",
            "trigger_content_prefix_bytes",
        ],
        "direct_identifiers_emitted": False,
        "numeric_values_may_be_quasi_identifiers": True,
        "raw_text_emitted": False,
        "canonical_order": "numeric_lexicographic_multiset",
    }
    return canonical_sha256(descriptor)


def numerator_ledger_implementation_sha256() -> str:
    evidence = build_numerator_targeted_evidence(
        total_news_positive_frames=9,
        affected_ledgers=(
            R03AffectedFrameByteLedger(
                source_appearances=5,
                preceding_included_appearances=3,
                trigger_included_appearances=1,
                omitted_after_trigger_appearances=1,
                reconciliation_retained_appearances=4,
                preceding_included_zero_byte_appearances=0,
                trigger_included_zero_byte_appearances=0,
                source_text_bytes=200_000,
                preceding_headline_bytes=300,
                preceding_summary_bytes=700,
                preceding_content_bytes=120_000,
                trigger_headline_bytes=100,
                trigger_summary_bytes=200,
                trigger_content_prefix_bytes=9_772,
                reconciliation_retained_text_bytes=131_072,
            ),
            R03AffectedFrameByteLedger(
                source_appearances=3,
                preceding_included_appearances=1,
                trigger_included_appearances=0,
                omitted_after_trigger_appearances=1,
                reconciliation_retained_appearances=1,
                preceding_included_zero_byte_appearances=1,
                trigger_included_zero_byte_appearances=0,
                source_text_bytes=90_000,
                preceding_headline_bytes=0,
                preceding_summary_bytes=0,
                preceding_content_bytes=0,
                trigger_headline_bytes=0,
                trigger_summary_bytes=0,
                trigger_content_prefix_bytes=0,
                reconciliation_retained_text_bytes=0,
            ),
            R03AffectedFrameByteLedger(
                source_appearances=2,
                preceding_included_appearances=0,
                trigger_included_appearances=1,
                omitted_after_trigger_appearances=1,
                reconciliation_retained_appearances=1,
                preceding_included_zero_byte_appearances=0,
                trigger_included_zero_byte_appearances=1,
                source_text_bytes=50_000,
                preceding_headline_bytes=0,
                preceding_summary_bytes=0,
                preceding_content_bytes=0,
                trigger_headline_bytes=0,
                trigger_summary_bytes=0,
                trigger_content_prefix_bytes=0,
                reconciliation_retained_text_bytes=0,
            ),
        ),
    )
    return canonical_sha256(
        {
            "semantics_id": LEDGER_SEMANTICS_ID,
            "evidence": evidence.model_dump(mode="json"),
        }
    )


def runtime_numerator_targeted_pins() -> dict[str, str]:
    return {
        "ledger_semantics_id": LEDGER_SEMANTICS_ID,
        "ledger_schema_sha256": numerator_ledger_schema_sha256(),
        "ledger_implementation_sha256": numerator_ledger_implementation_sha256(),
    }


class R03NumeratorTargetedPermitV1(StrictModel):
    schema_version: Literal["r03-n1-numerator-targeted-permit-v1"] = TARGETED_PERMIT_VERSION
    authorization: Literal["READ_ONLY_R03_N1_NUMERATOR_TARGETED_SCAN_AUTHORIZED"]
    base_reconciliation_permit: R03N1ReconciliationPermitV1
    accepted_result_sha256: Literal["6046eab6643d31254c398ad1e4183931130acf0ca076cd5aa93b1a69902265eb"] = ACCEPTED_RESULT_SHA256
    accepted_paired_evidence_sha256: Literal["4669d70649ce94178194e85eb80a40fe4b49145cfb6835d1ba1f2083714f7bdf"] = ACCEPTED_PAIRED_EVIDENCE_SHA256
    expected_affected_frame_count: Literal[664] = EXPECTED_AFFECTED_FRAME_COUNT
    sealed_retained_text_bytes: Literal[1435742878] = SEALED_RETAINED_TEXT_BYTES
    reconciliation_retained_text_bytes: Literal[1515387041] = RECONCILIATION_RETAINED_TEXT_BYTES
    unaffected_retained_text_bytes: Literal[1428361110] = UNAFFECTED_RETAINED_TEXT_BYTES
    sealed_implied_affected_text_bytes: Literal[7381768] = SEALED_IMPLIED_AFFECTED_TEXT_BYTES
    ledger_semantics_id: Literal["preserve-v2-before-trigger-trigger-after-component-ledger-v1"] = LEDGER_SEMANTICS_ID
    ledger_schema_sha256: str = Field(pattern=SHA256_PATTERN)
    ledger_implementation_sha256: str = Field(pattern=SHA256_PATTERN)
    execution_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    targeted_module_filesystem_sha256: str = Field(pattern=SHA256_PATTERN)
    targeted_runner_filesystem_sha256: str = Field(pattern=SHA256_PATTERN)
    base_runner_filesystem_sha256: str = Field(pattern=SHA256_PATTERN)
    prior_driver_filesystem_sha256: str = Field(pattern=SHA256_PATTERN)
    event_index_filesystem_sha256: str = Field(pattern=SHA256_PATTERN)
    calendar_input_filesystem_sha256: str = Field(pattern=SHA256_PATTERN)
    permit_sha256: str = Field(pattern=SHA256_PATTERN)


def validate_numerator_targeted_permit(
    permit: R03NumeratorTargetedPermitV1 | None,
    expected_permit_sha256: str,
) -> R03NumeratorTargetedPermitV1:
    if permit is None:
        raise R03ReconciliationError("targeted numerator scan permit required")
    try:
        permit = R03NumeratorTargetedPermitV1.model_validate(permit.model_dump(mode="json", warnings=False))
    except (TypeError, ValueError) as exc:
        raise R03ReconciliationError("targeted numerator permit validation failed") from exc
    if permit.permit_sha256 != expected_permit_sha256:
        raise R03ReconciliationError("targeted numerator permit is not explicitly pinned")
    unsigned = permit.model_dump(mode="json", exclude={"permit_sha256"})
    if canonical_sha256(unsigned) != permit.permit_sha256:
        raise R03ReconciliationError("targeted numerator permit self-hash mismatch")
    validate_reconciliation_permit(
        permit.base_reconciliation_permit,
        permit.base_reconciliation_permit.permit_sha256,
    )
    for field, value in runtime_numerator_targeted_pins().items():
        if getattr(permit, field) != value:
            raise R03ReconciliationError(f"runtime targeted numerator contract mismatch: {field}")
    return permit


EXECUTION_SURFACE_FIELDS = (
    "execution_commit",
    "targeted_module_filesystem_sha256",
    "targeted_runner_filesystem_sha256",
    "base_runner_filesystem_sha256",
    "prior_driver_filesystem_sha256",
    "event_index_filesystem_sha256",
    "calendar_input_filesystem_sha256",
)


def validate_numerator_execution_surface(
    permit: R03NumeratorTargetedPermitV1,
    observed: Mapping[str, str],
) -> None:
    if set(observed) != set(EXECUTION_SURFACE_FIELDS):
        raise R03ReconciliationError("targeted execution surface pin set mismatch")
    for field in EXECUTION_SURFACE_FIELDS:
        if observed[field] != getattr(permit, field):
            raise R03ReconciliationError(f"targeted execution surface mismatch: {field}")


def validate_numerator_targeted_execution(
    root: Path,
    permit: R03NumeratorTargetedPermitV1 | None,
    expected_permit_sha256: str,
) -> R03NumeratorTargetedPermitV1:
    validated = validate_numerator_targeted_permit(permit, expected_permit_sha256)
    validate_reconciliation_execution(
        root,
        validated.base_reconciliation_permit,
        validated.base_reconciliation_permit.permit_sha256,
    )
    return validated
