"""Strict contracts and frozen constants for the R02 D3 preflight candidate."""

from __future__ import annotations

import base64
from typing import Literal

from pydantic import Field, model_validator

from .canonical import canonical_sha256, sha256_hex
from .codex_preflight import parse_codex_feature_catalog
from .contracts import (
    ArtifactReference,
    StrictModel,
    codex_feature_catalog_definition_sha256,
    codex_feature_catalog_snapshot_sha256,
)
from .r02_contracts import R02SelectorReasonCode, R02SelectorResponsePayload


R02_D3_BASE_COMMIT = "4c45654d81efa07aa31a97e41f49ce16b29e0939"
R02_D1_FREEZE_SHA256 = "2d5961806b5051ff56c874b8b05933df014136bacb98717c4846f2b48f645778"
R02_D1_MANIFEST_SHA256 = "81026cdd1ab83fe7f0cea30951cf8cb1351dca6150d9aaecbfa696d932bbdeaf"
R02_D2C_FRAME_MANIFEST_SHA256 = (
    "71dcaa85eabe0ff95420469415946049b2ac12b7f0a5be183853fabf355168f9"
)
R02_D2C_FRAME_SEAL_SHA256 = (
    "25c3bba605e2a16ac320255214b6c7365083251a1028e3dc273aba4d9b4b4e21"
)
R02_D2C_STATISTICAL_FREEZE_SHA256 = (
    "45a68aacde0135a4f5e446f1022406d35e24346b23df1bc7e4db78889c6e12b9"
)
R02_D2C_FREEZE_MANIFEST_SHA256 = (
    "f9583c01c63c6e4d5257a2547ef313b3d8fe8e89e250295e0e673b4d7bf47b5c"
)
R02_D2C_FRAME_ID = "r02-d2c-frame-53be0c4bb060"
R02_D2C_FRAME_TREE_SHA256 = (
    "316eb5757b2eda3a04ec16f19a225df7a6e44fdf7f506482aa947b9cf77fb494"
)
R01_FILE_COUNT = 299
R01_TREE_SHA256 = "6ecbab78625ced153cb4b446fc8e911890476c144f361769e2073c142fd5c30e"
R01_MODEL_COMMAND_SPEC_PATH = (
    ".research_artifacts/r01-b3-1f65106/"
    "r01-b3-prompt-v2-resource-v3-20260717/b3_preflight/"
    "command_specs/development-0000.json"
)
R01_MODEL_COMMAND_SPEC_SHA256 = (
    "e474dfa6943e1f9ea25053a8d97a2476a0ac57b29214e5932c671c6786abb6c4"
)
R02_D3_REQUESTED_MODEL_ID = "gpt-5.6-sol"
R02_D3_PROVIDER = "openai-codex-chatgpt-subscription"
R02_D3_CODEX_CLI_VERSION = "codex-cli 0.144.1"
R02_D3_FEATURE_CATALOG_SHA256 = (
    "14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad"
)
R02_D3_FEATURE_DEFINITION_SHA256 = (
    "aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530"
)
R02_D3_BOOTSTRAP_DOMAIN = "R02-D3-EVALUATION-BOOTSTRAP-SEED-V1"
R02_D3_PAYLOAD_PLACEHOLDER = "{{SELECTOR_SAFE_PAYLOAD_CANONICAL_JSON}}"
R02_D3_OUTPUT_SCHEMA_PLACEHOLDER = "{{OUTPUT_SCHEMA_ABSOLUTE_PATH}}"
R02_D3_LOCAL_COMMAND_TIMEOUT_SECONDS = 30
R02_D3_LIVE_TIMEOUT_MS = 900_000
R02_D3_PROTECTED_PATHS = (
    "docs/r02-d1-candidate-trigger-freeze.json",
    "docs/r02-d1-freeze-manifest.json",
    "docs/r02-d2c-frame-manifest.json",
    "docs/r02-d2c-frame-seal.json",
    "docs/r02-d2c-freeze-manifest.json",
    "docs/r02-d2c-statistical-freeze.json",
    "v2/research/overlay/r02_candidates.py",
    "v2/research/overlay/r02_frame.py",
    "v2/research/overlay/r02_statistics.py",
)
R02_D3_SYSTEM_PROMPT = (
    "You are a constrained portfolio candidate selector. Compare only the "
    "opaque presented candidates supplied by the user. Return one strict JSON object."
)
R02_D3_REASON_CODES = tuple(reason.value for reason in R02SelectorReasonCode)
R02_D3_USER_PROMPT_TEMPLATE = (
    "Select exactly one presented candidate. Return keys schema_version, "
    "selected_candidate_id, confidence, and reason_codes only. confidence must be "
    "a JSON integer from 0 through 100. reason_codes must contain one to three "
    f"unique values from [{','.join(R02_D3_REASON_CODES)}]. Candidate payload:\n"
    f"{R02_D3_PAYLOAD_PLACEHOLDER}"
)
R02_D3_POST_DISABLE_ACTIVE_ALLOWLIST = (
    "resize_all_images",
    "terminal_resize_reflow",
    "tool_search_always_defer_mcp_tools",
    "tui_app_server",
)
R02_D3_NODE_TYPES = (
    "preregistration",
    "selector_output_schema",
    "transport_snapshot",
    "zero_call_assertions",
    "preflight",
)
R02_D3_HARD_STOP_CONDITIONS = (
    "TRUST_ANCHOR_OR_PROTECTED_TREE_DRIFT",
    "PROMPT_OR_OUTPUT_SCHEMA_DRIFT",
    "MODEL_REQUEST_ID_OR_PRESENT_PROVIDER_ECHO_MISMATCH",
    "CODEX_EXECUTABLE_VERSION_FEATURE_OR_COMMAND_DRIFT",
    "TRANSPORT_TIMEOUT_NONZERO_EXIT_OR_UNSETTLED_ATTEMPT",
    "ATTEMPT_OR_TOKEN_BUDGET_WOULD_BE_EXCEEDED",
    "AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE",
    "SECOND_SELECTOR_FALLBACK_WITHIN_MICRO_PILOT",
)


def selector_output_schema() -> dict[str, object]:
    return R02SelectorResponsePayload.model_json_schema()


def selector_output_schema_sha256() -> str:
    return canonical_sha256(selector_output_schema())


class R02D3MicroPilotCase(StrictModel):
    schema_version: Literal["r02-d3-micro-pilot-case-v1"] = (
        "r02-d3-micro-pilot-case-v1"
    )
    stratum: Literal["REPRESENTATIVE", "CHALLENGE_HEADROOM"]
    candidate_count: Literal[2, 3, 4]
    fixture_id: str = Field(pattern=r"^development-[0-9]{4}$")
    frame_ordinal: int = Field(ge=0, lt=160)


class R02D3ExecutionContract(StrictModel):
    schema_version: Literal["r02-d3-execution-contract-v1"] = (
        "r02-d3-execution-contract-v1"
    )
    status: Literal["NOT_AUTHORIZED_SEPARATE_D3_APPROVAL_REQUIRED"] = (
        "NOT_AUTHORIZED_SEPARATE_D3_APPROVAL_REQUIRED"
    )
    full_frame_count: Literal[160] = 160
    eligible_episode_count: Literal[55] = 55
    micro_pilot_case_count: Literal[6] = 6
    selection_rule: Literal[
        "LEXICOGRAPHIC_FIRST_FIXTURE_ID_WITHIN_EACH_STRATUM_X_K_CELL"
    ] = "LEXICOGRAPHIC_FIRST_FIXTURE_ID_WITHIN_EACH_STRATUM_X_K_CELL"
    execution_order: Literal["FRAME_ORDINAL_ASCENDING"] = "FRAME_ORDINAL_ASCENDING"
    cases: tuple[R02D3MicroPilotCase, ...]
    provider_attempts_per_case: Literal[1] = 1
    retry_attempts_per_case: Literal[0] = 0
    replacement_cases_allowed: Literal[False] = False
    attempted_cases_debit_full_evaluation_budget: Literal[True] = True
    attempted_cases_remain_in_itt: Literal[True] = True
    failed_or_fallback_delta_e12: Literal[0] = 0
    utility_outcomes_available_to_continuation_gate: Literal[False] = False
    micro_pilot_has_investment_or_utility_claim: Literal[False] = False

    @model_validator(mode="after")
    def validate_execution(self) -> "R02D3ExecutionContract":
        cells = tuple((case.stratum, case.candidate_count) for case in self.cases)
        expected_cells = tuple(
            (stratum, candidate_count)
            for stratum in ("REPRESENTATIVE", "CHALLENGE_HEADROOM")
            for candidate_count in (2, 3, 4)
        )
        if set(cells) != set(expected_cells) or len(cells) != len(set(cells)):
            raise ValueError("micro-pilot must contain one case per stratum-by-K cell")
        if tuple(case.frame_ordinal for case in self.cases) != tuple(
            sorted(case.frame_ordinal for case in self.cases)
        ):
            raise ValueError("micro-pilot cases must follow frame ordinal")
        return self


class R02D3BudgetStopContract(StrictModel):
    schema_version: Literal["r02-d3-budget-stop-contract-v1"] = (
        "r02-d3-budget-stop-contract-v1"
    )
    full_provider_attempt_cap: Literal[55] = 55
    full_token_cap: Literal[1_760_000] = 1_760_000
    per_attempt_token_reserve: Literal[32_000] = 32_000
    per_episode_attempt_cap: Literal[1] = 1
    retry_attempt_cap: Literal[0] = 0
    incremental_usd_cap: Literal[0] = 0
    micro_pilot_attempt_cap: Literal[6] = 6
    micro_pilot_token_cap: Literal[192_000] = 192_000
    micro_pilot_selector_fallback_cap: Literal[1] = 1
    full_evaluation_fail_closed_attempt_cap: Literal[5] = 5
    full_evaluation_fail_closed_rate_cap_ppm: Literal[90_909] = 90_909
    unsettled_attempt_cap: Literal[0] = 0
    live_timeout_ms: Literal[R02_D3_LIVE_TIMEOUT_MS] = R02_D3_LIVE_TIMEOUT_MS
    breach_label: Literal["INVALID_RUN"] = "INVALID_RUN"
    no_rerun_or_replacement_after_attempt: Literal[True] = True
    hard_stop_conditions: tuple[str, ...] = R02_D3_HARD_STOP_CONDITIONS

    @model_validator(mode="after")
    def validate_budget(self) -> "R02D3BudgetStopContract":
        if self.micro_pilot_token_cap != (
            self.micro_pilot_attempt_cap * self.per_attempt_token_reserve
        ):
            raise ValueError("micro-pilot token cap does not reconcile")
        if self.full_token_cap != self.full_provider_attempt_cap * self.per_attempt_token_reserve:
            raise ValueError("full token cap does not reconcile")
        if self.hard_stop_conditions != R02_D3_HARD_STOP_CONDITIONS:
            raise ValueError("hard-stop conditions drifted")
        return self


class R02D3LocalCommandCapture(StrictModel):
    schema_version: Literal["r02-d3-local-command-capture-v1"] = (
        "r02-d3-local-command-capture-v1"
    )
    label: Literal[
        "version",
        "login_status",
        "baseline_features",
        "post_disable_features",
        "exec_help",
    ]
    argv: tuple[str, ...]
    stdout_base64: str
    stderr_base64: str
    stdout_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stderr_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    exit_code: Literal[0] = 0

    @model_validator(mode="after")
    def validate_capture(self) -> "R02D3LocalCommandCapture":
        try:
            stdout = base64.b64decode(self.stdout_base64, validate=True)
            stderr = base64.b64decode(self.stderr_base64, validate=True)
        except ValueError as exc:
            raise ValueError("command capture is not valid base64") from exc
        if sha256_hex(stdout) != self.stdout_sha256:
            raise ValueError("command stdout hash mismatch")
        if sha256_hex(stderr) != self.stderr_sha256:
            raise ValueError("command stderr hash mismatch")
        return self

    def stdout_bytes(self) -> bytes:
        return base64.b64decode(self.stdout_base64, validate=True)

    def stderr_bytes(self) -> bytes:
        return base64.b64decode(self.stderr_base64, validate=True)


class R02D3TransportSnapshot(StrictModel):
    schema_version: Literal["r02-d3-zero-call-transport-snapshot-v1"] = (
        "r02-d3-zero-call-transport-snapshot-v1"
    )
    preregistration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    executable_path: str = Field(min_length=1)
    executable_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    codex_cli_version: Literal[R02_D3_CODEX_CLI_VERSION] = R02_D3_CODEX_CLI_VERSION
    authentication_mode: Literal["ChatGPT"] = "ChatGPT"
    feature_catalog_count: Literal[92] = 92
    feature_catalog_sha256: Literal[R02_D3_FEATURE_CATALOG_SHA256] = (
        R02_D3_FEATURE_CATALOG_SHA256
    )
    feature_definition_sha256: Literal[R02_D3_FEATURE_DEFINITION_SHA256] = (
        R02_D3_FEATURE_DEFINITION_SHA256
    )
    disabled_features: tuple[str, ...]
    post_disable_active_features: tuple[str, ...]
    captures: tuple[R02D3LocalCommandCapture, ...]
    external_provider_calls: Literal[0] = 0
    provider_request_commands_executed: Literal[0] = 0

    @model_validator(mode="after")
    def validate_transport(self) -> "R02D3TransportSnapshot":
        _validate_transport_snapshot(self)
        return self


def build_zero_call_commands(
    executable_path: str,
    disabled_features: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    prefix: list[str] = [executable_path]
    for feature in disabled_features:
        prefix.extend(("--disable", feature))
    disabled = tuple(prefix)
    return (
        ("version", (executable_path, "--version")),
        ("login_status", (executable_path, "login", "status")),
        ("baseline_features", (executable_path, "features", "list")),
        ("post_disable_features", (*disabled, "features", "list")),
        ("exec_help", (*disabled, "exec", "--help")),
    )


def zero_call_commands_from_snapshot(
    snapshot: R02D3TransportSnapshot,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return build_zero_call_commands(
        snapshot.executable_path,
        snapshot.disabled_features,
    )


def _validate_transport_snapshot(snapshot: R02D3TransportSnapshot) -> None:
    labels = tuple(capture.label for capture in snapshot.captures)
    expected_labels = tuple(label for label, _argv in zero_call_commands_from_snapshot(snapshot))
    if labels != expected_labels or len(labels) != len(set(labels)):
        raise ValueError("zero-call capture labels or order drifted")
    by_label = {capture.label: capture for capture in snapshot.captures}
    expected_commands = dict(zero_call_commands_from_snapshot(snapshot))
    if any(by_label[label].argv != expected_commands[label] for label in expected_labels):
        raise ValueError("zero-call command argv drifted")
    version = by_label["version"].stdout_bytes().decode("utf-8", errors="strict").strip()
    if version != snapshot.codex_cli_version:
        raise ValueError("Codex CLI version drifted")
    login = (
        by_label["login_status"].stdout_bytes()
        + b"\n"
        + by_label["login_status"].stderr_bytes()
    ).decode("utf-8", errors="strict").strip()
    if login != "Logged in using ChatGPT":
        raise ValueError("Codex authentication mode drifted")
    baseline = parse_codex_feature_catalog(
        by_label["baseline_features"].stdout_bytes(), expected_count=92
    )
    post_disable = parse_codex_feature_catalog(
        by_label["post_disable_features"].stdout_bytes(), expected_count=92
    )
    if codex_feature_catalog_snapshot_sha256(baseline) != snapshot.feature_catalog_sha256:
        raise ValueError("feature catalog snapshot drifted")
    if codex_feature_catalog_definition_sha256(baseline) != snapshot.feature_definition_sha256:
        raise ValueError("feature catalog definition drifted")
    if tuple(entry.name for entry in baseline) != snapshot.disabled_features:
        raise ValueError("disabled feature set drifted")
    if codex_feature_catalog_definition_sha256(post_disable) != snapshot.feature_definition_sha256:
        raise ValueError("post-disable feature definition drifted")
    active = tuple(entry.name for entry in post_disable if entry.enabled)
    if active != snapshot.post_disable_active_features:
        raise ValueError("post-disable active feature set mismatch")
    if active != R02_D3_POST_DISABLE_ACTIVE_ALLOWLIST:
        raise ValueError("post-disable active feature allowlist drifted")
    help_bytes = by_label["exec_help"].stdout_bytes()
    for required in (b"Usage: codex exec", b"--output-schema", b"--ignore-user-config"):
        if required not in help_bytes:
            raise ValueError("Codex exec help contract drifted")


class R02D3ZeroCallAssertions(StrictModel):
    schema_version: Literal["r02-d3-zero-call-assertions-v1"] = (
        "r02-d3-zero-call-assertions-v1"
    )
    accepted_commit_matches: Literal[True] = True
    protected_tracked_diff_empty: Literal[True] = True
    d1_hashes_match: Literal[True] = True
    d2c_hashes_match: Literal[True] = True
    d2c_frame_tree_matches: Literal[True] = True
    r01_seal_matches: Literal[True] = True
    prompt_matches_d2b_template: Literal[True] = True
    bootstrap_seed_recomputed: Literal[True] = True
    model_command_spec_anchored: Literal[True] = True
    transport_commands_allowlisted: Literal[True] = True
    transport_capture_valid: Literal[True] = True
    output_schema_valid: Literal[True] = True
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    micro_pilot_executed: Literal[False] = False


class R02D3ZeroCallPreflight(StrictModel):
    schema_version: Literal["r02-d3-zero-call-preflight-v1"] = (
        "r02-d3-zero-call-preflight-v1"
    )
    status: Literal["READY_FOR_INDEPENDENT_REVIEW_PROVIDER_CALLS_ZERO"] = (
        "READY_FOR_INDEPENDENT_REVIEW_PROVIDER_CALLS_ZERO"
    )
    preflight_id: str = Field(pattern=r"^r02-d3-preflight-[0-9a-f]{12}$")
    preregistration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    transport_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selector_output_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    assertions: R02D3ZeroCallAssertions
    zero_call_preflight_finalization: Literal["CANDIDATE_REVIEW_PENDING"] = (
        "CANDIDATE_REVIEW_PENDING"
    )
    d3_live_authorization: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    micro_pilot_executed: Literal[False] = False

    @model_validator(mode="after")
    def validate_preflight(self) -> "R02D3ZeroCallPreflight":
        expected_id = f"r02-d3-preflight-{self.preregistration_sha256[:12]}"
        if self.preflight_id != expected_id:
            raise ValueError("preflight ID does not match preregistration")
        if self.selector_output_schema_sha256 != selector_output_schema_sha256():
            raise ValueError("preflight output schema hash mismatch")
        return self


class R02D3PreflightAuditGraph(StrictModel):
    schema_version: Literal["r02-d3-preflight-audit-graph-v1"] = (
        "r02-d3-preflight-audit-graph-v1"
    )
    preflight_id: str = Field(pattern=r"^r02-d3-preflight-[0-9a-f]{12}$")
    node_types: tuple[str, ...]
    nodes: tuple[ArtifactReference, ...]
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False

    @model_validator(mode="after")
    def validate_graph(self) -> "R02D3PreflightAuditGraph":
        if self.node_types != R02_D3_NODE_TYPES:
            raise ValueError("D3 preflight audit node order drifted")
        if len(self.nodes) != len(self.node_types):
            raise ValueError("D3 preflight audit node/reference count mismatch")
        return self


class R02D3PersistedPreflight(StrictModel):
    schema_version: Literal["r02-d3-persisted-preflight-v1"] = (
        "r02-d3-persisted-preflight-v1"
    )
    preflight: ArtifactReference
    audit_graph: ArtifactReference


class R02D3ReplayVerification(StrictModel):
    schema_version: Literal["r02-d3-preflight-replay-verification-v1"] = (
        "r02-d3-preflight-replay-verification-v1"
    )
    preflight_id: str = Field(pattern=r"^r02-d3-preflight-[0-9a-f]{12}$")
    verified_artifacts: Literal[6] = 6
    all_hashes_match: Literal[True] = True
    preregistration_recomputed: Literal[True] = True
    bootstrap_seed_recomputed: Literal[True] = True
    prompt_contract_recomputed: Literal[True] = True
    model_identity_recomputed: Literal[True] = True
    transport_recaptured: Literal[True] = True
    preflight_recomputed: Literal[True] = True
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    micro_pilot_executed: Literal[False] = False
