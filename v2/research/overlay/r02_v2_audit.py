"""Append-only provider-free audit and implementation evidence for overlay v2."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import Field, model_validator

from .canonical import canonical_sha256
from .contracts import StrictModel

IMPLEMENTATION_PLAN_COMMIT = "245adc2d1f023a87d1cbfd86a7b726aec810bd78"
TEST_GATES = (
    "SCHEMA_METASCHEMA_AND_BYTE_PARITY",
    "CANONICAL_PAYLOAD_AND_DIGEST_REPRODUCIBILITY",
    "PUBLIC_METRIC_RECOMPUTATION",
    "INFORMATION_PARITY_AND_FORBIDDEN_FIELD_REJECTION",
    "NINETEEN_SCORER_IDENTITY_AND_ARITHMETIC",
    "CANDIDATE_ORDER_PERMUTATION_INVARIANCE",
    "RFC6901_ESCAPE_INDEX_BOUNDS_AND_SCOPE",
    "HIDDEN_ORACLE_CALL_ORDER_ISOLATION",
    "SELECTION_REPLAY_AND_SPLIT_NONOVERLAP",
    "HEADROOM_LABELS_FLOORS_AND_DIAGNOSTICS",
    "POWER_GRID_COMPLETENESS_AND_WORST_CELL_RULE",
    "FAILURE_ITT_AND_NO_DROPPED_FAILURES",
    "NO_PROVIDER_NETWORK_SUBPROCESS_CREDENTIAL_OR_ROOT_CAPABILITY",
)


class R02V2AuditError(RuntimeError):
    """Raised when append-only evidence cannot be replayed exactly."""


class R02V2AuditEntry(StrictModel):
    schema_version: Literal["r02-overlay-v2-audit-entry-v1"] = "r02-overlay-v2-audit-entry-v1"
    ordinal: int = Field(ge=0)
    kind: Literal[
        "CONTRACT",
        "PAYLOAD",
        "GROUNDING",
        "COMPARATOR",
        "SELECTION",
        "HEADROOM",
        "POWER",
        "TEST",
    ]
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_entry_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    entry_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_entry_hash(self) -> "R02V2AuditEntry":
        expected = canonical_sha256(
            {
                "schema_version": self.schema_version,
                "ordinal": self.ordinal,
                "kind": self.kind,
                "payload_sha256": self.payload_sha256,
                "previous_entry_sha256": self.previous_entry_sha256,
            }
        )
        if self.entry_sha256 != expected:
            raise ValueError("audit entry hash mismatch")
        return self


class R02V2AuditLog(StrictModel):
    schema_version: Literal["r02-overlay-v2-audit-log-v1"] = "r02-overlay-v2-audit-log-v1"
    entries: tuple[R02V2AuditEntry, ...] = ()
    provider_calls: Literal[0] = 0
    live_runs: Literal[0] = 0
    fixture_roots_materialized: Literal[0] = 0
    log_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_chain(self) -> "R02V2AuditLog":
        previous: str | None = None
        for ordinal, entry in enumerate(self.entries):
            if entry.ordinal != ordinal:
                raise ValueError("audit ordinals must be contiguous")
            if entry.previous_entry_sha256 != previous:
                raise ValueError("audit previous hash mismatch")
            previous = entry.entry_sha256
        expected = canonical_sha256(
            {
                "schema_version": self.schema_version,
                "entries": self.entries,
                "provider_calls": 0,
                "live_runs": 0,
                "fixture_roots_materialized": 0,
            }
        )
        if self.log_sha256 != expected:
            raise ValueError("audit log hash mismatch")
        return self


class R02V2ImplementationEvidence(StrictModel):
    schema_version: Literal["r02-overlay-v2-implementation-evidence-v1"] = "r02-overlay-v2-implementation-evidence-v1"
    implementation_plan_commit: Literal[IMPLEMENTATION_PLAN_COMMIT] = IMPLEMENTATION_PLAN_COMMIT
    source_sha256: dict[str, str]
    test_sha256: dict[str, str]
    gate_to_tests: dict[str, tuple[str, ...]]
    focused_test_command: str
    full_overlay_test_command: str
    provider_calls: Literal[0] = 0
    live_runs: Literal[0] = 0
    fixture_roots_materialized: Literal[0] = 0
    production_roots_materialized: Literal[0] = 0
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_evidence(self) -> "R02V2ImplementationEvidence":
        if set(self.gate_to_tests) != set(TEST_GATES):
            raise ValueError("evidence must map all 13 accepted test gates")
        if any(not tests for tests in self.gate_to_tests.values()):
            raise ValueError("every test gate must map to at least one test")
        known_tests = set(self.test_sha256)
        if any(test not in known_tests for tests in self.gate_to_tests.values() for test in tests):
            raise ValueError("gate mapping references an unhashed test")
        expected = canonical_sha256({key: value for key, value in self.model_dump(mode="python").items() if key != "evidence_sha256"})
        if self.evidence_sha256 != expected:
            raise ValueError("implementation evidence hash mismatch")
        return self


def empty_audit_log() -> R02V2AuditLog:
    body = {
        "schema_version": "r02-overlay-v2-audit-log-v1",
        "entries": (),
        "provider_calls": 0,
        "live_runs": 0,
        "fixture_roots_materialized": 0,
    }
    return R02V2AuditLog(**body, log_sha256=canonical_sha256(body))


def append_audit_entry(
    log: R02V2AuditLog,
    *,
    kind: Literal[
        "CONTRACT",
        "PAYLOAD",
        "GROUNDING",
        "COMPARATOR",
        "SELECTION",
        "HEADROOM",
        "POWER",
        "TEST",
    ],
    payload: Any,
) -> R02V2AuditLog:
    entry_body = {
        "schema_version": "r02-overlay-v2-audit-entry-v1",
        "ordinal": len(log.entries),
        "kind": kind,
        "payload_sha256": canonical_sha256(payload),
        "previous_entry_sha256": (log.entries[-1].entry_sha256 if log.entries else None),
    }
    entry = R02V2AuditEntry(
        **entry_body,
        entry_sha256=canonical_sha256(entry_body),
    )
    body = {
        "schema_version": "r02-overlay-v2-audit-log-v1",
        "entries": (*log.entries, entry),
        "provider_calls": 0,
        "live_runs": 0,
        "fixture_roots_materialized": 0,
    }
    return R02V2AuditLog(**body, log_sha256=canonical_sha256(body))


def replay_audit_log(log: R02V2AuditLog) -> bool:
    replay = empty_audit_log()
    for entry in log.entries:
        entry_body = {
            "schema_version": entry.schema_version,
            "ordinal": entry.ordinal,
            "kind": entry.kind,
            "payload_sha256": entry.payload_sha256,
            "previous_entry_sha256": entry.previous_entry_sha256,
        }
        if canonical_sha256(entry_body) != entry.entry_sha256:
            return False
        body = {
            "schema_version": replay.schema_version,
            "entries": (*replay.entries, entry),
            "provider_calls": 0,
            "live_runs": 0,
            "fixture_roots_materialized": 0,
        }
        replay = R02V2AuditLog(
            **body,
            log_sha256=canonical_sha256(body),
        )
    return replay == log


def build_implementation_evidence(
    *,
    source_sha256: Mapping[str, str],
    test_sha256: Mapping[str, str],
    gate_to_tests: Mapping[str, tuple[str, ...]],
    focused_test_command: str,
    full_overlay_test_command: str,
) -> R02V2ImplementationEvidence:
    body = {
        "schema_version": "r02-overlay-v2-implementation-evidence-v1",
        "implementation_plan_commit": IMPLEMENTATION_PLAN_COMMIT,
        "source_sha256": dict(source_sha256),
        "test_sha256": dict(test_sha256),
        "gate_to_tests": dict(gate_to_tests),
        "focused_test_command": focused_test_command,
        "full_overlay_test_command": full_overlay_test_command,
        "provider_calls": 0,
        "live_runs": 0,
        "fixture_roots_materialized": 0,
        "production_roots_materialized": 0,
    }
    return R02V2ImplementationEvidence(
        **body,
        evidence_sha256=canonical_sha256(body),
    )
