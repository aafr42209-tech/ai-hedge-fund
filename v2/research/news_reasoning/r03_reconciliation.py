"""Versioned, synthetic-safe R03 N1 reconciliation contracts.

This module does not traverse a corpus.  It binds a future reconciliation
permit to executable text/record semantics and defines aggregate-only paired
frame evidence for a separately authorized rerun.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from v2.research.overlay.canonical import canonical_sha256
from v2.research.overlay.contracts import StrictModel

from .r03_contracts import R03ArticleRecord, SHA256_PATTERN
from .r03_payload import canonicalize_text
from .r03_source import R03DataCheckPermitV2, root_path_sha256

RECONCILIATION_AUTHORITY = "R03_N1_RECONCILIATION_CODE_ONLY_AUTHORIZED"
RECONCILIATION_PERMIT_VERSION = "r03-n1-reconciliation-permit-v1"
PAIRED_DIFF_SCHEMA_VERSION = "r03-n1-paired-frame-diff-v1"
CANONICAL_CLASSIFICATION_PATH = "provenance_classification.classification"
CANONICAL_CLASSIFICATION = "FIRST_V2_RAW_MEASUREMENT_EXPOSED_UNVERIFIED_SEAL"
CAUSE_STATUS_PATH = "investigation_note.classification"

NORMALIZATION_SEMANTICS_ID = "preserve-whitespace-nfc-lf-reject-nul-v1"
DECODER_SEMANTICS_ID = "strict-string-or-null-preserve-codepoints-v1"
ARTICLE_RECORD_SEMANTICS_ID = "strict-record-no-implicit-text-strip-v1"
VERSION_TIE_BREAK_ID = "max-available-updated-input-payload-text-sha256-v1"
RETAINED_PREDICATE_ID = "included-flag-with-zero-byte-diagnostics-v2"
INPUT_BYTE_MEASUREMENT_ID = "appearance-weighted-canonical-hsc-utf8-before-caps-v2"


class R03ReconciliationError(RuntimeError):
    pass


def decode_provider_text(value: object | None) -> str | None:
    """Strict boundary decoder: preserve strings byte-semantically; never strip."""

    if value is None:
        return None
    if type(value) is not str:
        raise TypeError("provider text must be a string or null")
    return value


def _text_digest(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _probe_outcome(operation: Callable[[object | None], str | None], value: object | None) -> dict[str, Any]:
    try:
        result = operation(value)
    except Exception as exc:
        return {"status": "ERROR", "error_type": type(exc).__name__}
    return {"status": "OK", "output_sha256": _text_digest(result)}


def normalization_implementation_sha256() -> str:
    probes: tuple[str | None, ...] = (
        None,
        "",
        "  keep surrounding whitespace  ",
        "line1\r\nline2\rline3",
        "e\u0301",
        "\u00a0keep non-ascii whitespace\u2003",
        "Ａﬀ①",
        "nul\x00rejected",
    )
    outcomes = [_probe_outcome(canonicalize_text, value) for value in probes]
    return canonical_sha256({"semantics_id": NORMALIZATION_SEMANTICS_ID, "outcomes": outcomes})


def decoder_implementation_sha256() -> str:
    probes: tuple[object | None, ...] = (None, "", "  keep  ", "x\r\ny", 7, True)
    outcomes = [_probe_outcome(decode_provider_text, value) for value in probes]
    return canonical_sha256({"semantics_id": DECODER_SEMANTICS_ID, "outcomes": outcomes})


def article_record_implementation_sha256() -> str:
    record = R03ArticleRecord(
        article_id="synthetic-contract-probe",
        created_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        updated_at=datetime(2024, 1, 2, 13, tzinfo=UTC),
        symbols=("AAA",),
        source=" source ",
        headline=" headline ",
        summary=" summary ",
        content=" content ",
        input_text_sha256="0" * 64,
    )
    observed = {
        "source_sha256": _text_digest(record.source),
        "headline_sha256": _text_digest(record.headline),
        "summary_sha256": _text_digest(record.summary),
        "content_sha256": _text_digest(record.content),
        "available_at": record.available_at.isoformat(),
    }
    return canonical_sha256({"semantics_id": ARTICLE_RECORD_SEMANTICS_ID, "observed": observed})


def canonical_payload_text_sha256(record: R03ArticleRecord) -> str:
    value = {
        "source_sha256": _text_digest(canonicalize_text(record.source)),
        "headline_sha256": _text_digest(canonicalize_text(record.headline)),
        "summary_sha256": _text_digest(canonicalize_text(record.summary)),
        "content_sha256": _text_digest(canonicalize_text(record.content)),
    }
    return canonical_sha256(value)


def reconciliation_version_key(record: R03ArticleRecord) -> tuple[datetime, datetime, str, str]:
    return (
        record.available_at,
        record.updated_at,
        record.input_text_sha256,
        canonical_payload_text_sha256(record),
    )


def select_reconciliation_versions(records: Iterable[R03ArticleRecord]) -> tuple[R03ArticleRecord, ...]:
    selected: dict[str, R03ArticleRecord] = {}
    for record in records:
        current = selected.get(record.article_id)
        if current is None or reconciliation_version_key(record) > reconciliation_version_key(current):
            selected[record.article_id] = record
    return tuple(selected[key] for key in sorted(selected))


def version_implementation_sha256() -> str:
    def record(*, created_at: datetime, updated_at: datetime, input_sha256: str, content: str) -> R03ArticleRecord:
        return R03ArticleRecord(
            article_id="synthetic-version-probe",
            created_at=created_at,
            updated_at=updated_at,
            symbols=("AAA",),
            source="source",
            headline="headline",
            summary=None,
            content=content,
            input_text_sha256=input_sha256,
        )

    same_created = datetime(2024, 1, 4, 12, tzinfo=UTC)
    earlier_updated = datetime(2024, 1, 1, 12, tzinfo=UTC)
    later_updated = datetime(2024, 1, 2, 12, tzinfo=UTC)
    payload_candidates = (
        record(
            created_at=same_created,
            updated_at=later_updated,
            input_sha256="1" * 64,
            content="alpha",
        ),
        record(
            created_at=same_created,
            updated_at=later_updated,
            input_sha256="1" * 64,
            content="beta",
        ),
    )
    low_payload, high_payload = sorted(payload_candidates, key=canonical_payload_text_sha256)
    cases = {
        "available_at": (
            record(
                created_at=datetime(2024, 1, 5, 12, tzinfo=UTC),
                updated_at=earlier_updated,
                input_sha256="0" * 64,
                content=low_payload.content or "",
            ),
            record(
                created_at=same_created,
                updated_at=later_updated,
                input_sha256="f" * 64,
                content=high_payload.content or "",
            ),
        ),
        "updated_at": (
            record(
                created_at=same_created,
                updated_at=later_updated,
                input_sha256="0" * 64,
                content=low_payload.content or "",
            ),
            record(
                created_at=same_created,
                updated_at=earlier_updated,
                input_sha256="f" * 64,
                content=high_payload.content or "",
            ),
        ),
        "input_text_sha256": (
            record(
                created_at=same_created,
                updated_at=later_updated,
                input_sha256="f" * 64,
                content=low_payload.content or "",
            ),
            record(
                created_at=same_created,
                updated_at=later_updated,
                input_sha256="0" * 64,
                content=high_payload.content or "",
            ),
        ),
        "payload_text_sha256": payload_candidates,
    }
    outcomes: dict[str, dict[str, str]] = {}
    for label, pair in cases.items():
        selected = select_reconciliation_versions(pair)[0]
        key = reconciliation_version_key(selected)
        outcomes[label] = {
            "available_at": key[0].isoformat(),
            "updated_at": key[1].isoformat(),
            "input_text_sha256": key[2],
            "payload_text_sha256": key[3],
        }
    return canonical_sha256({"semantics_id": VERSION_TIE_BREAK_ID, "outcomes": outcomes})


def retained_appearance(*, included: bool, source_bytes: int, retained_bytes: int) -> bool:
    if type(included) is not bool:
        raise TypeError("included must be boolean")
    if type(source_bytes) is not int or type(retained_bytes) is not int:
        raise TypeError("byte counts must be integers")
    if source_bytes < 0:
        raise ValueError("source bytes must be nonnegative")
    if retained_bytes < 0 or retained_bytes > source_bytes:
        raise ValueError("retained bytes must be within source bytes")
    if not included and retained_bytes != 0:
        raise ValueError("omitted appearance cannot retain text bytes")
    return included


def measure_input_text_bytes(record: R03ArticleRecord) -> int:
    headline = canonicalize_text(record.headline)
    summary = canonicalize_text(record.summary)
    content = canonicalize_text(record.content)
    return sum(len(value.encode("utf-8")) for value in (headline, summary, content) if value is not None)


def input_byte_measurement_implementation_sha256() -> str:
    record = R03ArticleRecord(
        article_id="synthetic-byte-probe",
        created_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        updated_at=datetime(2024, 1, 2, 13, tzinfo=UTC),
        symbols=("AAA",),
        source=" source excluded from denominator ",
        headline=" headline ",
        summary="e\u0301\r\nsummary",
        content=" content ",
        input_text_sha256="4" * 64,
    )
    empty_record = record.model_copy(update={"headline": None, "summary": None, "content": None})
    return canonical_sha256(
        {
            "semantics_id": INPUT_BYTE_MEASUREMENT_ID,
            "measured_bytes": measure_input_text_bytes(record),
            "empty_measured_bytes": measure_input_text_bytes(empty_record),
        }
    )


def retained_predicate_implementation_sha256() -> str:
    probes = (
        (True, 3, 3),
        (True, 3, 1),
        (True, 3, 0),
        (True, 0, 0),
        (False, 3, 0),
        (False, 0, 0),
        (False, 3, 1),
    )
    outcomes: list[dict[str, Any]] = []
    for included, source_bytes, retained_bytes in probes:
        try:
            value = retained_appearance(
                included=included,
                source_bytes=source_bytes,
                retained_bytes=retained_bytes,
            )
        except Exception as exc:
            outcomes.append({"status": "ERROR", "error_type": type(exc).__name__})
        else:
            outcomes.append({"status": "OK", "retained": value})
    return canonical_sha256({"semantics_id": RETAINED_PREDICATE_ID, "outcomes": outcomes})


class R03PairedAffectedFrame(StrictModel):
    source_appearances: int = Field(gt=0)
    prior_retained_appearances: int = Field(ge=0)
    reconciliation_retained_appearances: int = Field(ge=0)
    zero_source_appearances: int = Field(ge=0)
    prior_included_zero_byte_appearances: int = Field(ge=0)
    reconciliation_included_zero_byte_appearances: int = Field(ge=0)
    source_text_bytes: int = Field(ge=0)
    prior_retained_text_bytes: int = Field(ge=0)
    reconciliation_retained_text_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> "R03PairedAffectedFrame":
        if self.prior_retained_appearances > self.source_appearances:
            raise ValueError("prior retained appearances exceed source appearances")
        if self.reconciliation_retained_appearances > self.source_appearances:
            raise ValueError("reconciliation retained appearances exceed source appearances")
        if self.zero_source_appearances > self.source_appearances:
            raise ValueError("zero-source appearances exceed source appearances")
        if self.prior_included_zero_byte_appearances > self.prior_retained_appearances:
            raise ValueError("prior included-zero appearances exceed retained appearances")
        if self.reconciliation_included_zero_byte_appearances > self.reconciliation_retained_appearances:
            raise ValueError("reconciliation included-zero appearances exceed retained appearances")
        if self.prior_retained_text_bytes > self.source_text_bytes:
            raise ValueError("prior retained bytes exceed source bytes")
        if self.reconciliation_retained_text_bytes > self.source_text_bytes:
            raise ValueError("reconciliation retained bytes exceed source bytes")
        if self.source_text_bytes == 0 and self.zero_source_appearances != self.source_appearances:
            raise ValueError("zero source-byte frame must count every appearance as zero-source")
        if self.reconciliation_retained_appearances == 0 and self.reconciliation_retained_text_bytes != 0:
            raise ValueError("reconciliation zero-retained frame cannot retain text bytes")
        return self


def _pair_key(pair: R03PairedAffectedFrame) -> tuple[int, ...]:
    return (
        pair.source_appearances,
        pair.prior_retained_appearances,
        pair.reconciliation_retained_appearances,
        pair.zero_source_appearances,
        pair.prior_included_zero_byte_appearances,
        pair.reconciliation_included_zero_byte_appearances,
        pair.source_text_bytes,
        pair.prior_retained_text_bytes,
        pair.reconciliation_retained_text_bytes,
    )


class R03PairedFrameDiffEvidence(StrictModel):
    schema_version: Literal["r03-n1-paired-frame-diff-v1"] = PAIRED_DIFF_SCHEMA_VERSION
    selection: Literal["session_cap_affected_frames_only"] = "session_cap_affected_frames_only"
    total_news_positive_frames: int = Field(gt=0)
    affected_frame_count: int = Field(gt=0)
    pairs: tuple[R03PairedAffectedFrame, ...]
    prior_zero_retained_text_frames: int = Field(ge=0)
    reconciliation_zero_retained_text_frames: int = Field(ge=0)
    equal_retained_text_frames: int = Field(ge=0)
    changed_retained_text_frames: int = Field(ge=0)
    prior_retained_text_bytes_total: int = Field(ge=0)
    reconciliation_retained_text_bytes_total: int = Field(ge=0)
    retained_text_bytes_delta: int
    zero_source_appearances_total: int = Field(ge=0)
    prior_included_zero_byte_appearances_total: int = Field(ge=0)
    reconciliation_included_zero_byte_appearances_total: int = Field(ge=0)
    prior_appearance_byte_inconsistency_frames: int = Field(ge=0)
    reconciliation_appearance_byte_inconsistency_frames: int = Field(ge=0)
    pair_multiset_sha256: str = Field(pattern=SHA256_PATTERN)
    evidence_sha256: str = Field(pattern=SHA256_PATTERN)

    @field_validator("pairs", mode="before")
    @classmethod
    def deserialize_json_pairs(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_identity(self) -> "R03PairedFrameDiffEvidence":
        if len(self.pairs) != self.affected_frame_count:
            raise ValueError("affected frame count mismatch")
        if self.affected_frame_count > self.total_news_positive_frames:
            raise ValueError("affected frame count exceeds total news-positive frames")
        if tuple(sorted(self.pairs, key=_pair_key)) != self.pairs:
            raise ValueError("paired frame evidence must use canonical multiset order")
        prior_total = sum(pair.prior_retained_text_bytes for pair in self.pairs)
        reconciliation_total = sum(pair.reconciliation_retained_text_bytes for pair in self.pairs)
        expected = {
            "prior_zero_retained_text_frames": sum(pair.prior_retained_text_bytes == 0 for pair in self.pairs),
            "reconciliation_zero_retained_text_frames": sum(pair.reconciliation_retained_text_bytes == 0 for pair in self.pairs),
            "equal_retained_text_frames": sum(pair.prior_retained_text_bytes == pair.reconciliation_retained_text_bytes for pair in self.pairs),
            "changed_retained_text_frames": sum(pair.prior_retained_text_bytes != pair.reconciliation_retained_text_bytes for pair in self.pairs),
            "prior_retained_text_bytes_total": prior_total,
            "reconciliation_retained_text_bytes_total": reconciliation_total,
            "retained_text_bytes_delta": reconciliation_total - prior_total,
            "zero_source_appearances_total": sum(pair.zero_source_appearances for pair in self.pairs),
            "prior_included_zero_byte_appearances_total": sum(pair.prior_included_zero_byte_appearances for pair in self.pairs),
            "reconciliation_included_zero_byte_appearances_total": sum(pair.reconciliation_included_zero_byte_appearances for pair in self.pairs),
            "prior_appearance_byte_inconsistency_frames": sum(pair.prior_retained_appearances == 0 and pair.prior_retained_text_bytes > 0 for pair in self.pairs),
            "reconciliation_appearance_byte_inconsistency_frames": sum(pair.reconciliation_retained_appearances == 0 and pair.reconciliation_retained_text_bytes > 0 for pair in self.pairs),
            "pair_multiset_sha256": canonical_sha256([pair.model_dump(mode="json") for pair in self.pairs]),
        }
        for field, value in expected.items():
            if getattr(self, field) != value:
                raise ValueError(f"paired frame derived field mismatch: {field}")
        unsigned = self.model_dump(mode="json", exclude={"evidence_sha256"})
        if canonical_sha256(unsigned) != self.evidence_sha256:
            raise ValueError("paired frame evidence identity mismatch")
        return self


def paired_diff_schema_sha256() -> str:
    descriptor = {
        "schema_version": PAIRED_DIFF_SCHEMA_VERSION,
        "selection": "session_cap_affected_frames_only",
        "pair_fields": [
            "source_appearances",
            "prior_retained_appearances",
            "reconciliation_retained_appearances",
            "zero_source_appearances",
            "prior_included_zero_byte_appearances",
            "reconciliation_included_zero_byte_appearances",
            "source_text_bytes",
            "prior_retained_text_bytes",
            "reconciliation_retained_text_bytes",
        ],
        "direct_identifiers_emitted": False,
        "numeric_values_may_be_quasi_identifiers": True,
        "raw_text_emitted": False,
        "canonical_pair_order": "numeric_lexicographic_multiset",
        "identity": "canonical_sha256",
    }
    return canonical_sha256(descriptor)


def build_paired_frame_diff_evidence(
    *,
    total_news_positive_frames: int,
    affected_pairs: Iterable[R03PairedAffectedFrame],
) -> R03PairedFrameDiffEvidence:
    pairs = tuple(sorted(tuple(affected_pairs), key=_pair_key))
    unsigned: dict[str, Any] = {
        "schema_version": PAIRED_DIFF_SCHEMA_VERSION,
        "selection": "session_cap_affected_frames_only",
        "total_news_positive_frames": total_news_positive_frames,
        "affected_frame_count": len(pairs),
        "pairs": pairs,
        "prior_zero_retained_text_frames": sum(pair.prior_retained_text_bytes == 0 for pair in pairs),
        "reconciliation_zero_retained_text_frames": sum(pair.reconciliation_retained_text_bytes == 0 for pair in pairs),
        "equal_retained_text_frames": sum(pair.prior_retained_text_bytes == pair.reconciliation_retained_text_bytes for pair in pairs),
        "changed_retained_text_frames": sum(pair.prior_retained_text_bytes != pair.reconciliation_retained_text_bytes for pair in pairs),
        "prior_retained_text_bytes_total": sum(pair.prior_retained_text_bytes for pair in pairs),
        "reconciliation_retained_text_bytes_total": sum(pair.reconciliation_retained_text_bytes for pair in pairs),
        "retained_text_bytes_delta": sum(pair.reconciliation_retained_text_bytes - pair.prior_retained_text_bytes for pair in pairs),
        "zero_source_appearances_total": sum(pair.zero_source_appearances for pair in pairs),
        "prior_included_zero_byte_appearances_total": sum(pair.prior_included_zero_byte_appearances for pair in pairs),
        "reconciliation_included_zero_byte_appearances_total": sum(pair.reconciliation_included_zero_byte_appearances for pair in pairs),
        "prior_appearance_byte_inconsistency_frames": sum(pair.prior_retained_appearances == 0 and pair.prior_retained_text_bytes > 0 for pair in pairs),
        "reconciliation_appearance_byte_inconsistency_frames": sum(pair.reconciliation_retained_appearances == 0 and pair.reconciliation_retained_text_bytes > 0 for pair in pairs),
        "pair_multiset_sha256": canonical_sha256([pair.model_dump(mode="json") for pair in pairs]),
    }
    return R03PairedFrameDiffEvidence(**unsigned, evidence_sha256=canonical_sha256(unsigned))


def paired_diff_implementation_sha256() -> str:
    evidence = build_paired_frame_diff_evidence(
        total_news_positive_frames=6,
        affected_pairs=(
            R03PairedAffectedFrame(
                source_appearances=5,
                prior_retained_appearances=0,
                reconciliation_retained_appearances=4,
                zero_source_appearances=1,
                prior_included_zero_byte_appearances=0,
                reconciliation_included_zero_byte_appearances=1,
                source_text_bytes=200_000,
                prior_retained_text_bytes=120_000,
                reconciliation_retained_text_bytes=131_072,
            ),
            R03PairedAffectedFrame(
                source_appearances=3,
                prior_retained_appearances=3,
                reconciliation_retained_appearances=3,
                zero_source_appearances=3,
                prior_included_zero_byte_appearances=3,
                reconciliation_included_zero_byte_appearances=3,
                source_text_bytes=0,
                prior_retained_text_bytes=0,
                reconciliation_retained_text_bytes=0,
            ),
            R03PairedAffectedFrame(
                source_appearances=2,
                prior_retained_appearances=2,
                reconciliation_retained_appearances=2,
                zero_source_appearances=0,
                prior_included_zero_byte_appearances=0,
                reconciliation_included_zero_byte_appearances=0,
                source_text_bytes=140_000,
                prior_retained_text_bytes=100_000,
                reconciliation_retained_text_bytes=100_000,
            ),
        ),
    )
    return canonical_sha256(
        {
            "schema_sha256": paired_diff_schema_sha256(),
            "synthetic_evidence": evidence.model_dump(mode="json"),
        }
    )


def runtime_contract_pins() -> dict[str, str]:
    return {
        "normalization_semantics_id": NORMALIZATION_SEMANTICS_ID,
        "normalization_implementation_sha256": normalization_implementation_sha256(),
        "decoder_semantics_id": DECODER_SEMANTICS_ID,
        "decoder_implementation_sha256": decoder_implementation_sha256(),
        "article_record_semantics_id": ARTICLE_RECORD_SEMANTICS_ID,
        "article_record_implementation_sha256": article_record_implementation_sha256(),
        "version_tie_break_id": VERSION_TIE_BREAK_ID,
        "version_implementation_sha256": version_implementation_sha256(),
        "retained_predicate_id": RETAINED_PREDICATE_ID,
        "retained_predicate_implementation_sha256": retained_predicate_implementation_sha256(),
        "input_byte_measurement_id": INPUT_BYTE_MEASUREMENT_ID,
        "input_byte_measurement_implementation_sha256": input_byte_measurement_implementation_sha256(),
        "paired_diff_schema_sha256": paired_diff_schema_sha256(),
        "paired_diff_implementation_sha256": paired_diff_implementation_sha256(),
    }


class R03N1ReconciliationPermitV1(StrictModel):
    schema_version: Literal["r03-n1-reconciliation-permit-v1"] = RECONCILIATION_PERMIT_VERSION
    authorization: Literal["READ_ONLY_DATA_CHECK_RECONCILIATION_RERUN_AUTHORIZED"]
    base_permit: R03DataCheckPermitV2
    canonical_classification_path: Literal["provenance_classification.classification"] = CANONICAL_CLASSIFICATION_PATH
    canonical_classification: Literal["FIRST_V2_RAW_MEASUREMENT_EXPOSED_UNVERIFIED_SEAL"] = CANONICAL_CLASSIFICATION
    normalization_semantics_id: Literal["preserve-whitespace-nfc-lf-reject-nul-v1"] = NORMALIZATION_SEMANTICS_ID
    normalization_implementation_sha256: str = Field(pattern=SHA256_PATTERN)
    decoder_semantics_id: Literal["strict-string-or-null-preserve-codepoints-v1"] = DECODER_SEMANTICS_ID
    decoder_implementation_sha256: str = Field(pattern=SHA256_PATTERN)
    article_record_semantics_id: Literal["strict-record-no-implicit-text-strip-v1"] = ARTICLE_RECORD_SEMANTICS_ID
    article_record_implementation_sha256: str = Field(pattern=SHA256_PATTERN)
    whitespace_policy: Literal["PRESERVE"] = "PRESERVE"
    newline_policy: Literal["CRLF_CR_TO_LF"] = "CRLF_CR_TO_LF"
    unicode_policy: Literal["NFC"] = "NFC"
    nul_policy: Literal["REJECT"] = "REJECT"
    version_tie_break_id: Literal["max-available-updated-input-payload-text-sha256-v1"] = VERSION_TIE_BREAK_ID
    version_implementation_sha256: str = Field(pattern=SHA256_PATTERN)
    retained_predicate_id: Literal["included-flag-with-zero-byte-diagnostics-v2"] = RETAINED_PREDICATE_ID
    retained_predicate_implementation_sha256: str = Field(pattern=SHA256_PATTERN)
    input_byte_measurement_id: Literal["appearance-weighted-canonical-hsc-utf8-before-caps-v2"] = INPUT_BYTE_MEASUREMENT_ID
    input_byte_measurement_implementation_sha256: str = Field(pattern=SHA256_PATTERN)
    paired_diff_schema_sha256: str = Field(pattern=SHA256_PATTERN)
    paired_diff_implementation_sha256: str = Field(pattern=SHA256_PATTERN)
    permit_sha256: str = Field(pattern=SHA256_PATTERN)


def validate_reconciliation_permit(
    permit: R03N1ReconciliationPermitV1 | None,
    expected_permit_sha256: str,
) -> R03N1ReconciliationPermitV1:
    if permit is None:
        raise R03ReconciliationError("reconciliation rerun permit required")
    try:
        permit = R03N1ReconciliationPermitV1.model_validate(permit.model_dump(mode="json", warnings=False))
    except (TypeError, ValueError) as exc:
        raise R03ReconciliationError("reconciliation permit contract validation failed") from exc
    if permit.permit_sha256 != expected_permit_sha256:
        raise R03ReconciliationError("reconciliation permit is not explicitly pinned")
    unsigned = permit.model_dump(mode="json", exclude={"permit_sha256"})
    if canonical_sha256(unsigned) != permit.permit_sha256:
        raise R03ReconciliationError("reconciliation permit self-hash mismatch")
    base_unsigned = permit.base_permit.model_dump(mode="json", exclude={"permit_sha256"})
    if canonical_sha256(base_unsigned) != permit.base_permit.permit_sha256:
        raise R03ReconciliationError("base data-check permit self-hash mismatch")
    try:
        actual_pins = runtime_contract_pins()
    except Exception as exc:
        raise R03ReconciliationError("runtime reconciliation contract pin calculation failed") from exc
    for field, actual in actual_pins.items():
        if getattr(permit, field) != actual:
            raise R03ReconciliationError(f"runtime reconciliation contract mismatch: {field}")
    return permit


def validate_reconciliation_execution(
    root: Path,
    permit: R03N1ReconciliationPermitV1 | None,
    expected_permit_sha256: str,
) -> R03N1ReconciliationPermitV1:
    validated = validate_reconciliation_permit(permit, expected_permit_sha256)
    if root_path_sha256(root) != validated.base_permit.root_path_sha256:
        raise R03ReconciliationError("source root identity mismatch")
    return validated
