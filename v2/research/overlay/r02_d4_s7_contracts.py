"""Provider-free contracts for the R02 D4-S7 production transport gate."""

from __future__ import annotations

import base64
from typing import Literal

from pydantic import Field, model_validator

from .canonical import canonical_sha256, sha256_hex
from .contracts import StrictModel
from .r02_d4_s6_contracts import (
    R02_D4_S6_ATTEMPT_CAP,
    R02_D4_S6_FAIL_CLOSED_CAP,
    R02_D4_S6_RUN_PLAN_SHA256,
    R02_D4_S6_TIMEOUT_MS,
    R02_D4_S6_TOKEN_CAP,
    R02_D4_S6_TOKEN_RESERVE,
)

R02_D4_S7_BASE_COMMIT = "c88bde40015d88bf31f4af25587c339359971f2e"
R02_D4_S7_S5_FREEZE_SHA256 = "d931edfaa347165975a0edcff1a256f81cd7d56fc7268d7a2a19bf97379f50ab"
R02_D4_S7_S5_IDENTITY_SNAPSHOT_SHA256 = "248f3683db276d45f275b5a2c236bc02909f6b7bf1be4ff56f6886573b2df5dc"
R02_D4_S7_D3_PREREGISTRATION_SHA256 = "5e07d88e98e74f67a1377020ca8c19c6fada51756ebddd902706a1680eeb27d4"
R02_D4_S7_EXECUTABLE_SHA256 = "cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4"
R02_D4_S7_PREREGISTERED_RESPONSE_SCHEMA_SHA256 = "5466a24d3557e28251cb1393dac16e1049824637a27b969f3bea55c80ebc2eca"
R02_D4_S7_RESPONSE_SCHEMA_SHA256 = "f8089e667cff113d600e3c9c726fbbff4f80c8f522804525e37d8693bbd36937"
R02_D4_S7_PROVIDER = "openai-codex-chatgpt-subscription"
R02_D4_S7_MODEL = "gpt-5.6-sol"
R02_D4_S7_CAPTURE_SUMMARY_SHA256 = "6cb79e5f61d68032a4565a2eec66b6083bd34a4b69a6164c38da07d9f8ae7b23"


class R02D4S7LiveAuthorizationArtifact(StrictModel):
    """Future external approval. S7 provider-free work never creates this artifact."""

    schema_version: Literal["r02-d4-s7-live-authorization-artifact-v1"] = "r02-d4-s7-live-authorization-artifact-v1"
    authorization_id: str = Field(pattern=r"^r02-d4-s7-live-auth-[a-z0-9-]{4,80}$")
    run_id: str = Field(pattern=r"^r02-d4-[a-z0-9-]{4,80}$")
    approved_scope: Literal["INDIVISIBLE_ALL_69_LIVE"] = "INDIVISIBLE_ALL_69_LIVE"
    accepted_s6_commit: Literal[R02_D4_S7_BASE_COMMIT] = R02_D4_S7_BASE_COMMIT
    accepted_s6_review_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_s7_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    accepted_s7_review_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_s7_contract_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    s6_live_authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_calls_authorized: Literal[True] = True
    production_artifact_root_authorized: Literal[True] = True
    transport_evidence_root_authorized: Literal[True] = True
    all_69_one_shot_authorized: Literal[True] = True
    micro_pilot_authorized: Literal[False] = False
    retry_or_replacement_authorized: Literal[False] = False
    resume_authorized: Literal[False] = False


class R02D4S7TransportEvidence(StrictModel):
    schema_version: Literal["r02-d4-s7-transport-evidence-v1"] = "r02-d4-s7-transport-evidence-v1"
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_ordinal: int = Field(ge=0, lt=R02_D4_S6_ATTEMPT_CAP)
    selector_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    system_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    user_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stdin_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_schema_sha256: Literal[R02_D4_S7_RESPONSE_SCHEMA_SHA256] = R02_D4_S7_RESPONSE_SCHEMA_SHA256
    live_argv_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider: Literal[R02_D4_S7_PROVIDER] = R02_D4_S7_PROVIDER
    requested_model_id: Literal[R02_D4_S7_MODEL] = R02_D4_S7_MODEL
    executable_sha256: Literal[R02_D4_S7_EXECUTABLE_SHA256] = R02_D4_S7_EXECUTABLE_SHA256
    timeout_ms: Literal[R02_D4_S6_TIMEOUT_MS] = R02_D4_S6_TIMEOUT_MS
    stdout_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stderr_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stdout_base64: str
    stderr_base64: str
    exit_code: int | None
    timed_out: bool
    launch_error: str | None = None
    duration_ms: int = Field(ge=0)
    terminal_usage_event_count: int = Field(ge=0)
    parsed_provider_response_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    raw_response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parse_error_code: str | None = None
    external_provider_calls: Literal[0, 1]

    @model_validator(mode="after")
    def validate_capture(self) -> "R02D4S7TransportEvidence":
        try:
            stdout = base64.b64decode(self.stdout_base64, validate=True)
            stderr = base64.b64decode(self.stderr_base64, validate=True)
        except ValueError as exc:
            raise ValueError("transport evidence base64 is invalid") from exc
        if sha256_hex(stdout) != self.stdout_sha256:
            raise ValueError("transport stdout digest mismatch")
        if sha256_hex(stderr) != self.stderr_sha256:
            raise ValueError("transport stderr digest mismatch")
        if self.launch_error is not None and self.exit_code is not None:
            raise ValueError("launch error cannot also carry an exit code")
        return self


class R02D4S7EntrypointGate(StrictModel):
    schema_version: Literal["r02-d4-s7-entrypoint-gate-v1"] = "r02-d4-s7-entrypoint-gate-v1"
    status: Literal["PASS_PROVIDER_FREE_PRODUCTION_ENTRYPOINT_PREPARED"] = "PASS_PROVIDER_FREE_PRODUCTION_ENTRYPOINT_PREPARED"
    run_id: str = Field(pattern=r"^r02-d4-[a-z0-9-]{4,80}$")
    s6_live_authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    s7_live_authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    identity_snapshot_sha256: Literal[R02_D4_S7_S5_IDENTITY_SNAPSHOT_SHA256] = R02_D4_S7_S5_IDENTITY_SNAPSHOT_SHA256
    current_identity_capture_summary_sha256: Literal[R02_D4_S7_CAPTURE_SUMMARY_SHA256] = R02_D4_S7_CAPTURE_SUMMARY_SHA256
    executable_sha256: Literal[R02_D4_S7_EXECUTABLE_SHA256] = R02_D4_S7_EXECUTABLE_SHA256
    response_schema_sha256: Literal[R02_D4_S7_RESPONSE_SCHEMA_SHA256] = R02_D4_S7_RESPONSE_SCHEMA_SHA256
    preregistered_response_schema_sha256: Literal[R02_D4_S7_PREREGISTERED_RESPONSE_SCHEMA_SHA256] = R02_D4_S7_PREREGISTERED_RESPONSE_SCHEMA_SHA256
    prepared_run_plan_sha256: Literal[R02_D4_S6_RUN_PLAN_SHA256] = R02_D4_S6_RUN_PLAN_SHA256
    attempt_cap: Literal[R02_D4_S6_ATTEMPT_CAP] = R02_D4_S6_ATTEMPT_CAP
    token_reserve: Literal[R02_D4_S6_TOKEN_RESERVE] = R02_D4_S6_TOKEN_RESERVE
    aggregate_token_cap: Literal[R02_D4_S6_TOKEN_CAP] = R02_D4_S6_TOKEN_CAP
    timeout_ms: Literal[R02_D4_S6_TIMEOUT_MS] = R02_D4_S6_TIMEOUT_MS
    fail_closed_cap: Literal[R02_D4_S6_FAIL_CLOSED_CAP] = R02_D4_S6_FAIL_CLOSED_CAP
    micro_pilot_attempts: Literal[0] = 0
    retry_cap: Literal[0] = 0
    replacement_cap: Literal[0] = 0
    resume_cap: Literal[0] = 0
    production_root_materialized: Literal[False] = False
    transport_evidence_root_materialized: Literal[False] = False
    provider_process_started: Literal[False] = False


def raw_response_sha256(raw_response: str | None) -> str:
    return canonical_sha256({"raw_response": raw_response})
