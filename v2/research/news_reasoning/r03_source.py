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

from pydantic import Field

from v2.research.overlay.canonical import canonical_sha256, sha256_hex
from v2.research.overlay.contracts import StrictModel

from .r03_contracts import (
    PLAN_COMMIT,
    R03ArticleRecord,
    R03SourceDescriptor,
    SHA256_PATTERN,
)

FROZEN_ALL_JSON_SHA256 = "56f1a5567c1aa5ed5b327201d36f1ca5833381fd3b389279298acdd3a6c1e9d3"
FROZEN_PAGE_SHA256 = "4723720c1384723f09c26e9f77941f77a76f1c33d2620e466535eec133213bd9"
FROZEN_MANIFEST_SHA256 = "dbb5c4110cc2a198ed506cfb6f38b7db172805f46dc1237c5b6de58f9b7fb894"
FROZEN_JSON_FILE_COUNT = 10_270
FROZEN_TOTAL_BYTES = 2_668_932_157
FROZEN_PAGE_COUNT = 9_269
FROZEN_MANIFEST_COUNT = 1_000


class R03SourceAccessDenied(PermissionError):
    pass


class R03RawTextEmissionError(RuntimeError):
    pass


class R03DataAccessPermit(StrictModel):
    authorization: Literal["READ_ONLY_DATA_CHECK_AUTHORIZED"]
    root_path_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_commit: Literal[PLAN_COMMIT] = PLAN_COMMIT
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
    full_frames_total: int = Field(ge=0)
    full_frames_retained: int = Field(ge=0)
    article_appearances_total: int = Field(ge=0)
    article_appearances_retained: int = Field(ge=0)
    input_text_bytes: int = Field(ge=0)
    retained_text_bytes: int = Field(ge=0)
    retention_sha256: str = Field(pattern=SHA256_PATTERN)


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


def recompute_payload_retention_from_read_only_raw_source(
    root: Path,
    permit: R03DataAccessPermit | None,
    compute_rows: Callable[[Path], Iterable[tuple[bool, int, int]]],
) -> R03PublicRetention:
    """Future data-check entry point; authorization is checked before callback."""

    validate_data_access(root, permit)
    return public_retention(compute_rows(root))


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
