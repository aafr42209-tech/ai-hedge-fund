"""Fail-closed read-only source boundary and public aggregate accounting.

No function in this module is invoked against the licensed corpus during
CODE_ONLY work.  Raw-source entry points require an explicit future permit
and expose only counts and digests.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from v2.research.overlay.canonical import canonical_sha256, sha256_hex
from v2.research.overlay.contracts import StrictModel

from .r03_contracts import (
    ARTICLE_BYTE_CAP,
    PLAN_COMMIT,
    R03ArticleRecord,
    R03SourceDescriptor,
    SHA256_PATTERN,
    TICKER_SESSION_BYTE_CAP,
)

FROZEN_ALL_JSON_SHA256 = "56f1a5567c1aa5ed5b327201d36f1ca5833381fd3b389279298acdd3a6c1e9d3"
FROZEN_PAGE_SHA256 = "4723720c1384723f09c26e9f77941f77a76f1c33d2620e466535eec133213bd9"
FROZEN_MANIFEST_SHA256 = "dbb5c4110cc2a198ed506cfb6f38b7db172805f46dc1237c5b6de58f9b7fb894"
FROZEN_JSON_FILE_COUNT = 10_270
FROZEN_TOTAL_BYTES = 2_668_932_157
FROZEN_PAGE_COUNT = 9_269
FROZEN_MANIFEST_COUNT = 1_000
IMPLEMENTATION_COMMIT = "4c47ec61d85e3382c4dd4acfaa0281ca8a1950cd"
DATA_CHECK_CONTRACT_VERSION = "r03-public-retention-v2"
DATA_CHECK_PERMIT_VERSION = "r03-data-check-permit-v2"
DATA_CHECK_RERUN_AUTHORIZATION = "READ_ONLY_DATA_CHECK_RERUN_AUTHORIZED"
ARTICLE_ORDERING = "available_at_desc_article_id_asc"
TRUNCATION_SEMANTICS = "headline_summary_then_utf8_content_prefix_omit_after_session_truncation"
ROUNDING_RULE = "ROUND_HALF_EVEN_2DP"


class R03SourceAccessDenied(PermissionError):
    pass


class R03RawTextEmissionError(RuntimeError):
    pass


class R03DataAccessPermit(StrictModel):
    authorization: Literal["READ_ONLY_DATA_CHECK_AUTHORIZED"]
    root_path_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_commit: Literal[PLAN_COMMIT] = PLAN_COMMIT
    permit_sha256: str = Field(pattern=SHA256_PATTERN)


class R03DataCheckPermitV2(StrictModel):
    """User-issued identity for a separately authorized raw-source rerun."""

    schema_version: Literal["r03-data-check-permit-v2"] = DATA_CHECK_PERMIT_VERSION
    authorization: Literal["READ_ONLY_DATA_CHECK_RERUN_AUTHORIZED"]
    root_path_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_commit: Literal[PLAN_COMMIT] = PLAN_COMMIT
    implementation_commit: Literal["4c47ec61d85e3382c4dd4acfaa0281ca8a1950cd"] = IMPLEMENTATION_COMMIT
    early_close_session_count: Literal[21] = 21
    early_close_sessions_sha256: str = Field(pattern=SHA256_PATTERN)
    calendar_session_count: Literal[2514] = 2_514
    calendar_sha256: str = Field(pattern=SHA256_PATTERN)
    article_byte_cap: Literal[32768] = ARTICLE_BYTE_CAP
    ticker_session_byte_cap: Literal[131072] = TICKER_SESSION_BYTE_CAP
    article_ordering: Literal["available_at_desc_article_id_asc"] = ARTICLE_ORDERING
    truncation_semantics: Literal["headline_summary_then_utf8_content_prefix_omit_after_session_truncation"] = TRUNCATION_SEMANTICS
    rounding_rule: Literal["ROUND_HALF_EVEN_2DP"] = ROUNDING_RULE
    permit_sha256: str = Field(pattern=SHA256_PATTERN)


class R03SourceInventory(StrictModel):
    json_file_count: int = Field(ge=0)
    total_bytes: int = Field(ge=0)
    page_count: int = Field(ge=0)
    manifest_count: int = Field(ge=0)
    all_json_sha256: str = Field(pattern=SHA256_PATTERN)
    page_sha256: str = Field(pattern=SHA256_PATTERN)
    manifest_sha256: str = Field(pattern=SHA256_PATTERN)


class R03PublicRetention(StrictModel):
    """Legacy v1 record; retained for historical API compatibility only."""

    full_frames_total: int = Field(ge=0)
    full_frames_retained: int = Field(ge=0)
    article_appearances_total: int = Field(ge=0)
    article_appearances_retained: int = Field(ge=0)
    input_text_bytes: int = Field(ge=0)
    retained_text_bytes: int = Field(ge=0)
    retention_sha256: str = Field(pattern=SHA256_PATTERN)


def round_half_even_percent(numerator: int, denominator: int) -> str:
    """Return a canonical two-place percent using integer half-even rounding."""

    if not isinstance(numerator, int) or isinstance(numerator, bool):
        raise TypeError("numerator must be an integer")
    if not isinstance(denominator, int) or isinstance(denominator, bool):
        raise TypeError("denominator must be an integer")
    if numerator < 0 or denominator < 0 or numerator > denominator:
        raise ValueError("fraction must satisfy 0 <= numerator <= denominator")
    if denominator == 0:
        return "0.00"
    quotient, remainder = divmod(numerator * 10_000, denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient % 2 == 1):
        quotient += 1
    return f"{quotient // 100}.{quotient % 100:02d}"


class R03PublicRetentionV2(StrictModel):
    """Versioned evidence contract with independent frame/appearance streams."""

    schema_version: Literal["r03-public-retention-v2"] = DATA_CHECK_CONTRACT_VERSION
    full_frames_total: int = Field(ge=0)
    full_frames_retained: int = Field(ge=0)
    article_appearances_total: int = Field(ge=0)
    article_appearances_retained: int = Field(ge=0)
    input_text_bytes: int = Field(ge=0)
    retained_text_bytes: int = Field(ge=0)
    full_frame_retention_pct_2dp: str = Field(pattern=r"^(?:0|[1-9][0-9]*)\.[0-9]{2}$")
    article_appearance_retention_pct_2dp: str = Field(pattern=r"^(?:0|[1-9][0-9]*)\.[0-9]{2}$")
    text_byte_retention_pct_2dp: str = Field(pattern=r"^(?:0|[1-9][0-9]*)\.[0-9]{2}$")
    retention_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_identity(self) -> "R03PublicRetentionV2":
        if self.full_frames_retained > self.full_frames_total:
            raise ValueError("retained frame numerator exceeds denominator")
        if self.article_appearances_retained > self.article_appearances_total:
            raise ValueError("retained appearance numerator exceeds denominator")
        if self.retained_text_bytes > self.input_text_bytes:
            raise ValueError("retained byte numerator exceeds denominator")
        expected_rates = (
            round_half_even_percent(self.full_frames_retained, self.full_frames_total),
            round_half_even_percent(self.article_appearances_retained, self.article_appearances_total),
            round_half_even_percent(self.retained_text_bytes, self.input_text_bytes),
        )
        actual_rates = (
            self.full_frame_retention_pct_2dp,
            self.article_appearance_retention_pct_2dp,
            self.text_byte_retention_pct_2dp,
        )
        if actual_rates != expected_rates:
            raise ValueError("canonical round-half-even display mismatch")
        unsigned = self.model_dump(mode="json", exclude={"retention_sha256"})
        if canonical_sha256(unsigned) != self.retention_sha256:
            raise ValueError("retention identity hash mismatch")
        return self


def root_path_sha256(root: Path) -> str:
    normalized = str(root.resolve()).replace("\\", "/").casefold().encode("utf-8")
    return sha256_hex(normalized)


def validate_data_access(root: Path, permit: R03DataAccessPermit | None) -> None:
    if permit is None:
        raise R03SourceAccessDenied("READ_ONLY_DATA_CHECK_AUTHORIZED permit required")
    unsigned = permit.model_dump(mode="json", exclude={"permit_sha256"})
    if canonical_sha256(unsigned) != permit.permit_sha256:
        raise R03SourceAccessDenied("data-access permit hash mismatch")
    if root_path_sha256(root) != permit.root_path_sha256:
        raise R03SourceAccessDenied("source root identity mismatch")


def validate_data_check_permit_v2(
    root: Path,
    permit: R03DataCheckPermitV2 | None,
    expected_permit_sha256: str,
) -> None:
    """Validate every rerun pin before any callback or filesystem traversal."""

    if permit is None:
        raise R03SourceAccessDenied("READ_ONLY_DATA_CHECK_RERUN_AUTHORIZED permit required")
    try:
        permit = R03DataCheckPermitV2.model_validate(permit.model_dump(mode="json", warnings=False))
    except (TypeError, ValueError) as exc:
        raise R03SourceAccessDenied("data-check permit contract validation failed") from exc
    if permit.permit_sha256 != expected_permit_sha256:
        raise R03SourceAccessDenied("data-check permit is not the explicitly pinned permit")
    unsigned = permit.model_dump(mode="json", exclude={"permit_sha256"})
    if canonical_sha256(unsigned) != permit.permit_sha256:
        raise R03SourceAccessDenied("data-check permit hash mismatch")
    if root_path_sha256(root) != permit.root_path_sha256:
        raise R03SourceAccessDenied("source root identity mismatch")


def _aggregate_digest(entries: list[tuple[str, int, str]]) -> str:
    digest = hashlib.sha256()
    for relative, size, file_sha256 in sorted(entries):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\x00")
        digest.update(file_sha256.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def scan_read_only_inventory(root: Path, permit: R03DataAccessPermit | None) -> R03SourceInventory:
    """Scan bytes read-only after authorization; never return source bytes."""

    validate_data_access(root, permit)
    entries: list[tuple[str, int, str]] = []
    for file_path in sorted(root.rglob("*.json"), key=lambda p: p.as_posix()):
        payload = file_path.read_bytes()
        relative = file_path.relative_to(root).as_posix()
        entries.append((relative, len(payload), sha256_hex(payload)))
    pages = [entry for entry in entries if Path(entry[0]).name.startswith("page_")]
    manifests = [entry for entry in entries if Path(entry[0]).name == "manifest.json"]
    return R03SourceInventory(
        json_file_count=len(entries),
        total_bytes=sum(entry[1] for entry in entries),
        page_count=len(pages),
        manifest_count=len(manifests),
        all_json_sha256=_aggregate_digest(entries),
        page_sha256=_aggregate_digest(pages),
        manifest_sha256=_aggregate_digest(manifests),
    )


def assert_inventory_matches_descriptor(inventory: R03SourceInventory, descriptor: R03SourceDescriptor) -> None:
    compared = {
        "json_file_count": descriptor.json_file_count,
        "total_bytes": descriptor.total_bytes,
        "page_count": descriptor.page_count,
        "manifest_count": descriptor.manifest_count,
        "all_json_sha256": descriptor.all_json_sha256,
        "page_sha256": descriptor.page_sha256,
        "manifest_sha256": descriptor.manifest_sha256,
    }
    if inventory.model_dump() != compared:
        raise R03SourceAccessDenied("source inventory does not match sealed descriptor")


def iter_decoded_records(
    root: Path,
    permit: R03DataAccessPermit | None,
    decode_page: Callable[[bytes], Iterable[R03ArticleRecord]],
) -> Iterator[R03ArticleRecord]:
    """Decode records internally after authorization without logging payloads."""

    validate_data_access(root, permit)
    for file_path in sorted(root.rglob("page_*.json"), key=lambda p: p.as_posix()):
        payload: bytes | None = None
        try:
            payload = file_path.read_bytes()
            records = decode_page(payload)
            yield from records
        except Exception as exc:
            digest = sha256_hex(payload) if payload is not None else "unavailable"
            raise R03SourceAccessDenied(f"page decode failed for sha256={digest}") from exc


def public_retention(
    rows: Iterable[tuple[bool, int, int]],
) -> R03PublicRetention:
    """Aggregate ``(full_frame_retained, input_bytes, retained_bytes)`` rows."""

    materialized = tuple(rows)
    unsigned = {
        "full_frames_total": len(materialized),
        "full_frames_retained": sum(1 for kept, _, _ in materialized if kept),
        "article_appearances_total": len(materialized),
        "article_appearances_retained": sum(1 for _, _, retained in materialized if retained > 0),
        "input_text_bytes": sum(source for _, source, _ in materialized),
        "retained_text_bytes": sum(retained for _, _, retained in materialized),
    }
    return R03PublicRetention(**unsigned, retention_sha256=canonical_sha256(unsigned))


def public_retention_v2(
    frame_rows: Iterable[bool],
    appearance_rows: Iterable[tuple[bool, int, int]],
) -> R03PublicRetentionV2:
    """Aggregate independent frame and article-appearance evidence streams."""

    frames = tuple(frame_rows)
    appearances = tuple(appearance_rows)
    if any(type(kept) is not bool for kept in frames):
        raise TypeError("frame rows must contain booleans")
    for retained, source_bytes, retained_bytes in appearances:
        if type(retained) is not bool:
            raise TypeError("appearance retained flags must be booleans")
        if type(source_bytes) is not int or type(retained_bytes) is not int:
            raise TypeError("appearance byte counts must be integers")
        if source_bytes < 0 or retained_bytes < 0 or retained_bytes > source_bytes:
            raise ValueError("appearance bytes must satisfy 0 <= retained <= source")
        if not retained and retained_bytes != 0:
            raise ValueError("omitted appearance cannot retain text bytes")

    unsigned = {
        "schema_version": DATA_CHECK_CONTRACT_VERSION,
        "full_frames_total": len(frames),
        "full_frames_retained": sum(frames),
        "article_appearances_total": len(appearances),
        "article_appearances_retained": sum(1 for retained, _, _ in appearances if retained),
        "input_text_bytes": sum(source for _, source, _ in appearances),
        "retained_text_bytes": sum(retained for _, _, retained in appearances),
    }
    unsigned.update(
        {
            "full_frame_retention_pct_2dp": round_half_even_percent(unsigned["full_frames_retained"], unsigned["full_frames_total"]),
            "article_appearance_retention_pct_2dp": round_half_even_percent(unsigned["article_appearances_retained"], unsigned["article_appearances_total"]),
            "text_byte_retention_pct_2dp": round_half_even_percent(unsigned["retained_text_bytes"], unsigned["input_text_bytes"]),
        }
    )
    return R03PublicRetentionV2(**unsigned, retention_sha256=canonical_sha256(unsigned))


def recompute_payload_retention_from_read_only_raw_source(
    root: Path,
    permit: R03DataAccessPermit | None,
    compute_rows: Callable[[Path], Iterable[tuple[bool, int, int]]],
) -> R03PublicRetention:
    """Future data-check entry point; authorization is checked before callback."""

    validate_data_access(root, permit)
    return public_retention(compute_rows(root))


def recompute_payload_retention_v2_from_read_only_raw_source(
    root: Path,
    permit: R03DataCheckPermitV2 | None,
    expected_permit_sha256: str,
    compute_rows: Callable[[Path], tuple[Iterable[bool], Iterable[tuple[bool, int, int]]]],
) -> R03PublicRetentionV2:
    """Authorized v2 entry point; validation precedes the injected raw adapter."""

    validate_data_check_permit_v2(root, permit, expected_permit_sha256)
    frame_rows, appearance_rows = compute_rows(root)
    return public_retention_v2(frame_rows, appearance_rows)


def reject_raw_text_emission(value: object) -> None:
    """Reject evidence/log structures that contain raw-text field names."""

    forbidden = {"headline", "summary", "content", "body", "raw_text", "prompt"}

    def walk(item: object) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if str(key).casefold() in forbidden:
                    raise R03RawTextEmissionError(f"raw-text field forbidden: {key}")
                walk(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)

    walk(value)
