"""Raw-text-free append-only R03 audit, replay, and evidence contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import Field, model_validator

from v2.research.overlay.canonical import canonical_sha256
from v2.research.overlay.contracts import StrictModel

from .r03_contracts import PLAN_COMMIT, R03PinKind, R03ZeroCounters
from .r03_source import reject_raw_text_emission


class R03AuditError(RuntimeError):
    pass


class R03AuditEntry(StrictModel):
    schema_version: Literal["r03-audit-entry-v1"] = "r03-audit-entry-v1"
    ordinal: int = Field(ge=0)
    kind: Literal["AUTHORITY", "CONTRACT", "PAYLOAD_DIGEST", "MODEL_ID", "BOUND_CERTIFICATE", "GATE_RESULT", "EVIDENCE"]
    public_payload: dict[str, Any]
    previous_entry_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    entry_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_entry(self) -> "R03AuditEntry":
        reject_raw_text_emission(self.public_payload)
        unsigned = self.model_dump(mode="json", exclude={"entry_sha256"})
        if canonical_sha256(unsigned) != self.entry_sha256:
            raise R03AuditError("audit entry hash mismatch")
        return self


class R03AuditLog(StrictModel):
    schema_version: Literal["r03-audit-log-v1"] = "r03-audit-log-v1"
    entries: tuple[R03AuditEntry, ...]
    counters: R03ZeroCounters = R03ZeroCounters()
    log_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_log(self) -> "R03AuditLog":
        previous = None
        for ordinal, entry in enumerate(self.entries):
            if entry.ordinal != ordinal or entry.previous_entry_sha256 != previous:
                raise R03AuditError("audit chain linkage mismatch")
            previous = entry.entry_sha256
        unsigned = self.model_dump(mode="json", exclude={"log_sha256"})
        if canonical_sha256(unsigned) != self.log_sha256:
            raise R03AuditError("audit log hash mismatch")
        return self


class R03TestResult(StrictModel):
    command: str
    exit_code: Literal[0] = 0
    passed: int = Field(gt=0)


class R03ImplementationEvidence(StrictModel):
    schema_version: Literal["r03-provider-free-code-only-evidence-v1"] = "r03-provider-free-code-only-evidence-v1"
    implementation_plan_commit: Literal[PLAN_COMMIT] = PLAN_COMMIT
    status: Literal["CODE_ONLY_IMPLEMENTED_REVIEW_REQUIRED_DATA_AND_INFERENCE_NO_GO"]
    source_sha256: dict[str, str]
    source_pin_kind: dict[str, R03PinKind]
    test_sha256: dict[str, str]
    test_pin_kind: dict[str, R03PinKind]
    verifier_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_pin_kind: R03PinKind
    stage_exit_tests: dict[str, tuple[str, ...]]
    negative_tests: tuple[str, ...]
    focused_test_command: str
    regression_test_command: str
    focused_result: R03TestResult
    r02_api_result: R03TestResult
    full_overlay_result: R03TestResult
    style_exit_codes: dict[str, int]
    counters: R03ZeroCounters
    organizational_independence_established: Literal[False] = False
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_evidence(self) -> "R03ImplementationEvidence":
        if set(self.source_sha256) != set(self.source_pin_kind):
            raise R03AuditError("source pin-kind coverage mismatch")
        if set(self.test_sha256) != set(self.test_pin_kind):
            raise R03AuditError("test pin-kind coverage mismatch")
        if set(self.style_exit_codes) != {"black", "flake8", "isort"} or any(self.style_exit_codes.values()):
            raise R03AuditError("style result coverage or exit code mismatch")
        reject_raw_text_emission(self.model_dump(mode="json", exclude={"evidence_sha256"}))
        unsigned = self.model_dump(mode="json", exclude={"evidence_sha256"})
        if canonical_sha256(unsigned) != self.evidence_sha256:
            raise R03AuditError("implementation evidence hash mismatch")
        return self


def empty_audit_log() -> R03AuditLog:
    counters = R03ZeroCounters()
    unsigned = {"schema_version": "r03-audit-log-v1", "entries": (), "counters": counters}
    return R03AuditLog(entries=(), counters=counters, log_sha256=canonical_sha256(unsigned))


def append_audit_entry(log: R03AuditLog, kind: str, public_payload: Mapping[str, Any]) -> R03AuditLog:
    reject_raw_text_emission(dict(public_payload))
    previous = log.entries[-1].entry_sha256 if log.entries else None
    unsigned_entry = {
        "schema_version": "r03-audit-entry-v1",
        "ordinal": len(log.entries),
        "kind": kind,
        "public_payload": dict(public_payload),
        "previous_entry_sha256": previous,
    }
    entry = R03AuditEntry(**unsigned_entry, entry_sha256=canonical_sha256(unsigned_entry))
    unsigned_log = {
        "schema_version": "r03-audit-log-v1",
        "entries": (*log.entries, entry),
        "counters": log.counters,
    }
    return R03AuditLog(entries=(*log.entries, entry), counters=log.counters, log_sha256=canonical_sha256(unsigned_log))


def replay_audit_log(log: R03AuditLog) -> bool:
    R03AuditLog.model_validate(log.model_dump(mode="python"))
    return True


def build_implementation_evidence(**values: Any) -> R03ImplementationEvidence:
    unsigned = dict(values)
    return R03ImplementationEvidence(**unsigned, evidence_sha256=canonical_sha256(unsigned))
