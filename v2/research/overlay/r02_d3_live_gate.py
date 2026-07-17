"""Append-only provider-free freeze candidate for the R02 D3 live gate."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .artifacts import ArtifactReference
from .canonical import canonical_json_bytes, canonical_sha256
from .contracts import StrictModel
from .r02_audit import R02AppendOnlyArtifactStore, _ensure_r02_artifact_root
from .r02_d3_preflight import R02D3Preregistration

R02_D3_ACCEPTED_COMMIT = "87da1d77d734d4687df40d5b2b561ea2fde7cc18"
R02_D3_PREREGISTRATION_SHA256 = (
    "5e07d88e98e74f67a1377020ca8c19c6fada51756ebddd902706a1680eeb27d4"
)
R02_D3_PREFLIGHT_SHA256 = (
    "d88b406253f3a1f005b33534a742ee90814d9bc53f88a36ed400e7473a2b38fc"
)
R02_D3_MANIFEST_SHA256 = (
    "5b071e6643d26f49e7fae01f3188644129951a3ccf3095616a2aa202961ee770"
)
R02_D3_BOOTSTRAP_SEED_SHA256 = (
    "319dea85b61187c07089deedb525d4d927ffc03dc7ea2026e4be8022f2df9f68"
)
R02_D3_EXPECTED_EXECUTABLE_SHA256 = (
    "cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4"
)
R02_D3_SELECTOR_OUTPUT_SCHEMA_SHA256 = (
    "5466a24d3557e28251cb1393dac16e1049824637a27b969f3bea55c80ebc2eca"
)
R02_D3_LIVE_GATE_ID = "r02-d3-live-gate-v1"

SOURCE_PINS = (
    (
        "SELECTOR_ACCEPTANCE_AND_FALLBACK",
        "v2/research/overlay/r02_selector.py",
        "a90cc600ffc772c5fb4b1c964b5efc0a551de84a41eaa5c0a030b6d02b9b20f9",
    ),
    (
        "R02_TYPED_CONTRACTS",
        "v2/research/overlay/r02_contracts.py",
        "64a099560432152da875843d6cddb4d08acd3a402198adb14a5aec65ef0dab05",
    ),
    (
        "CODEX_JSONL_AND_TOKEN_PARSER",
        "v2/research/overlay/codex_exec_client.py",
        "4b3bb2e5bc9d1f406105bc7fd589bbfcb7541d259ebaf209252cb42ed329a1bd",
    ),
    (
        "D3_FROZEN_CONTRACTS",
        "v2/research/overlay/r02_d3_contracts.py",
        "978d4fcf2cb2775a40ac515276a4c0c69899284dc05096360b5a661b2ab2ef47",
    ),
    (
        "D3_PREFLIGHT_AND_LIVE_ARGV",
        "v2/research/overlay/r02_d3_preflight.py",
        "2376c5a4773de506aa577387397e4f59a497e623b7cfc262edbbbf9b1deb32a7",
    ),
    (
        "D3_PREFLIGHT_REPLAY",
        "v2/research/overlay/r02_d3_replay.py",
        "bff977ef81e8ca8bcd828ab9b39bd2070cd761f9a22eee718adf412c05030850",
    ),
)

USAGE_FIELDS = (
    "cached_input_tokens",
    "input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


class R02D3LiveGateError(RuntimeError):
    pass


class R02D3LiveSourcePin(StrictModel):
    role: Literal[
        "SELECTOR_ACCEPTANCE_AND_FALLBACK",
        "R02_TYPED_CONTRACTS",
        "CODEX_JSONL_AND_TOKEN_PARSER",
        "D3_FROZEN_CONTRACTS",
        "D3_PREFLIGHT_AND_LIVE_ARGV",
        "D3_PREFLIGHT_REPLAY",
    ]
    relative_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class R02D3ContinuationContract(StrictModel):
    schema_version: Literal["r02-d3-continuation-contract-v1"] = (
        "r02-d3-continuation-contract-v1"
    )
    micro_pilot_attempts: Literal[6] = 6
    full_evaluation_attempts: Literal[55] = 55
    remaining_attempts_after_micro: Literal[49] = 49
    utility_outcomes_available_to_gate: Literal[False] = False
    discretionary_pause_after_no_stop: Literal[False] = False
    second_authorization_after_no_stop: Literal[False] = False
    no_stop_action: Literal["MUST_CONTINUE_REMAINING_49_IN_FRAME_ORDER"] = (
        "MUST_CONTINUE_REMAINING_49_IN_FRAME_ORDER"
    )
    future_live_authorization_scope: Literal[
        "MICRO_6_PLUS_AUTOMATIC_REMAINING_49"
    ] = "MICRO_6_PLUS_AUTOMATIC_REMAINING_49"


class R02D3TokenMeasurementContract(StrictModel):
    schema_version: Literal["r02-d3-token-measurement-contract-v1"] = (
        "r02-d3-token-measurement-contract-v1"
    )
    terminal_event_type: Literal["turn.completed"] = "turn.completed"
    usage_field_path: Literal["turn.completed.usage"] = "turn.completed.usage"
    required_fields: tuple[str, ...] = USAGE_FIELDS
    exactly_one_terminal_usage_event: Literal[True] = True
    values_are_nonnegative_integers: Literal[True] = True
    cached_input_is_subset_of_input: Literal[True] = True
    reasoning_output_is_subset_of_output: Literal[True] = True
    accounting_formula: Literal["input_tokens + output_tokens"] = (
        "input_tokens + output_tokens"
    )
    cached_input_subtracted: Literal[False] = False
    reasoning_output_added_again: Literal[False] = False
    per_attempt_reservation_tokens: Literal[32000] = 32000
    missing_or_invalid_usage_action: Literal[
        "DEBIT_ATTEMPT_AND_32000_TOKEN_RESERVE_THEN_HARD_STOP_UNSETTLED"
    ] = "DEBIT_ATTEMPT_AND_32000_TOKEN_RESERVE_THEN_HARD_STOP_UNSETTLED"
    reported_total_over_reserve_action: Literal["INVALID_RUN_BUDGET_BREACH"] = (
        "INVALID_RUN_BUDGET_BREACH"
    )

    @model_validator(mode="after")
    def validate_measurement(self) -> "R02D3TokenMeasurementContract":
        if self.required_fields != USAGE_FIELDS:
            raise ValueError("token usage fields drifted")
        return self


class R02D3FailClosedRateContract(StrictModel):
    schema_version: Literal["r02-d3-fail-closed-rate-contract-v1"] = (
        "r02-d3-fail-closed-rate-contract-v1"
    )
    primary_attempt_cap: Literal[5] = 5
    denominator_attempts: Literal[55] = 55
    ppm_multiplier: Literal[1000000] = 1000000
    rounding: Literal["FLOOR"] = "FLOOR"
    derived_rate_cap_ppm: Literal[90909] = 90909
    precedence: Literal["ATTEMPT_CAP_PRIMARY_RATE_IS_DERIVED_REPORTING"] = (
        "ATTEMPT_CAP_PRIMARY_RATE_IS_DERIVED_REPORTING"
    )

    @model_validator(mode="after")
    def validate_rate(self) -> "R02D3FailClosedRateContract":
        derived = self.primary_attempt_cap * self.ppm_multiplier // self.denominator_attempts
        if derived != self.derived_rate_cap_ppm:
            raise ValueError("fail-closed ppm floor derivation drifted")
        return self


class R02D3DuplicateReasonFallbackContract(StrictModel):
    schema_version: Literal["r02-d3-duplicate-reason-fallback-v1"] = (
        "r02-d3-duplicate-reason-fallback-v1"
    )
    selector_output_schema_sha256: Literal[
        R02_D3_SELECTOR_OUTPUT_SCHEMA_SHA256
    ] = R02_D3_SELECTOR_OUTPUT_SCHEMA_SHA256
    output_schema_unique_items_present: Literal[False] = False
    local_parser_requires_unique_reason_codes: Literal[True] = True
    duplicate_reason_code_action: Literal[
        "SELECTOR_SCHEMA_INVALID_BASELINE_FALLBACK_DELTA_ZERO"
    ] = "SELECTOR_SCHEMA_INVALID_BASELINE_FALLBACK_DELTA_ZERO"
    repair_or_dedup_allowed: Literal[False] = False
    fallback_counts_as_fail_closed_attempt: Literal[True] = True


class R02D3AcceptedContractBindings(StrictModel):
    schema_version: Literal["r02-d3-accepted-contract-bindings-v1"] = (
        "r02-d3-accepted-contract-bindings-v1"
    )
    micro_pilot_case_count: int = Field(ge=0)
    micro_pilot_attempt_cap: int = Field(ge=0)
    eligible_episode_count: int = Field(ge=0)
    full_provider_attempt_cap: int = Field(ge=0)
    utility_outcomes_available_to_continuation_gate: bool
    per_attempt_token_reserve: int = Field(ge=0)
    unsettled_attempt_cap: int = Field(ge=0)
    full_evaluation_fail_closed_attempt_cap: int = Field(ge=0)
    full_evaluation_fail_closed_rate_cap_ppm: int = Field(ge=0)
    failed_or_fallback_delta_e12: int
    selector_response_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class R02D3LiveGateFreeze(StrictModel):
    schema_version: Literal["r02-d3-live-gate-freeze-v1"] = (
        "r02-d3-live-gate-freeze-v1"
    )
    status: Literal["FREEZE_CANDIDATE_PROVIDER_FREE"] = (
        "FREEZE_CANDIDATE_PROVIDER_FREE"
    )
    live_gate_id: Literal[R02_D3_LIVE_GATE_ID] = R02_D3_LIVE_GATE_ID
    accepted_d3_commit: Literal[R02_D3_ACCEPTED_COMMIT] = R02_D3_ACCEPTED_COMMIT
    accepted_d3_preregistration_sha256: Literal[
        R02_D3_PREREGISTRATION_SHA256
    ] = R02_D3_PREREGISTRATION_SHA256
    accepted_d3_preflight_sha256: Literal[R02_D3_PREFLIGHT_SHA256] = (
        R02_D3_PREFLIGHT_SHA256
    )
    accepted_d3_manifest_sha256: Literal[R02_D3_MANIFEST_SHA256] = (
        R02_D3_MANIFEST_SHA256
    )
    bootstrap_seed_sha256: Literal[R02_D3_BOOTSTRAP_SEED_SHA256] = (
        R02_D3_BOOTSTRAP_SEED_SHA256
    )
    authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    implementation_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preflight_script_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_executable_sha256: Literal[R02_D3_EXPECTED_EXECUTABLE_SHA256] = (
        R02_D3_EXPECTED_EXECUTABLE_SHA256
    )
    expected_executable_pin_origin: Literal[
        "USER_ACCEPTED_FREEZE_DOCUMENT_NOT_RUNTIME_DISCOVERY"
    ] = "USER_ACCEPTED_FREEZE_DOCUMENT_NOT_RUNTIME_DISCOVERY"
    source_pins: tuple[R02D3LiveSourcePin, ...]
    accepted_contract_bindings: R02D3AcceptedContractBindings
    continuation: R02D3ContinuationContract
    token_measurement: R02D3TokenMeasurementContract
    fail_closed_rate: R02D3FailClosedRateContract
    duplicate_reason_fallback: R02D3DuplicateReasonFallbackContract
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    micro_pilot_executed: Literal[False] = False
    live_authorization: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"

    @model_validator(mode="after")
    def validate_source_pins(self) -> "R02D3LiveGateFreeze":
        actual = tuple((pin.role, pin.relative_path, pin.sha256) for pin in self.source_pins)
        if actual != SOURCE_PINS:
            raise ValueError("live source pins drifted")
        binding = self.accepted_contract_bindings
        if binding.micro_pilot_case_count != self.continuation.micro_pilot_attempts:
            raise ValueError("accepted micro-pilot case count binding drifted")
        if binding.micro_pilot_attempt_cap != self.continuation.micro_pilot_attempts:
            raise ValueError("accepted micro-pilot attempt cap binding drifted")
        if binding.eligible_episode_count != self.continuation.full_evaluation_attempts:
            raise ValueError("accepted eligible episode count binding drifted")
        if binding.full_provider_attempt_cap != self.continuation.full_evaluation_attempts:
            raise ValueError("accepted provider attempt cap binding drifted")
        if (
            binding.eligible_episode_count - binding.micro_pilot_case_count
            != self.continuation.remaining_attempts_after_micro
        ):
            raise ValueError("accepted continuation remainder binding drifted")
        if (
            binding.utility_outcomes_available_to_continuation_gate
            != self.continuation.utility_outcomes_available_to_gate
        ):
            raise ValueError("accepted continuation utility binding drifted")
        if binding.per_attempt_token_reserve != self.token_measurement.per_attempt_reservation_tokens:
            raise ValueError("accepted token reserve binding drifted")
        if binding.unsettled_attempt_cap != 0:
            raise ValueError("accepted unsettled attempt cap binding drifted")
        if (
            binding.full_evaluation_fail_closed_attempt_cap
            != self.fail_closed_rate.primary_attempt_cap
        ):
            raise ValueError("accepted fail-closed attempt cap binding drifted")
        if binding.full_provider_attempt_cap != self.fail_closed_rate.denominator_attempts:
            raise ValueError("accepted fail-closed denominator binding drifted")
        if (
            binding.full_evaluation_fail_closed_rate_cap_ppm
            != self.fail_closed_rate.derived_rate_cap_ppm
        ):
            raise ValueError("accepted fail-closed ppm binding drifted")
        if binding.failed_or_fallback_delta_e12 != 0:
            raise ValueError("accepted fallback delta binding drifted")
        if (
            binding.selector_response_schema_sha256
            != self.duplicate_reason_fallback.selector_output_schema_sha256
        ):
            raise ValueError("accepted selector schema binding drifted")
        return self


class R02D3LiveGatePreflight(StrictModel):
    schema_version: Literal["r02-d3-live-gate-preflight-v1"] = (
        "r02-d3-live-gate-preflight-v1"
    )
    preflight_id: str = Field(pattern=r"^r02-d3-live-gate-[0-9a-f]{12}$")
    freeze_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_executable_sha256: Literal[R02_D3_EXPECTED_EXECUTABLE_SHA256] = (
        R02_D3_EXPECTED_EXECUTABLE_SHA256
    )
    observed_executable_sha256: Literal[R02_D3_EXPECTED_EXECUTABLE_SHA256] = (
        R02_D3_EXPECTED_EXECUTABLE_SHA256
    )
    accepted_commit_is_ancestor: Literal[True] = True
    accepted_d3_hashes_match: Literal[True] = True
    source_pins_match: Literal[True] = True
    token_parser_pin_match: Literal[True] = True
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    micro_pilot_executed: Literal[False] = False

    @model_validator(mode="after")
    def validate_identity(self) -> "R02D3LiveGatePreflight":
        expected_id = f"r02-d3-live-gate-{self.freeze_sha256[:12]}"
        if self.preflight_id != expected_id:
            raise ValueError("live-gate preflight identity mismatch")
        return self


class R02D3LiveGateAuditGraph(StrictModel):
    schema_version: Literal["r02-d3-live-gate-audit-graph-v1"] = (
        "r02-d3-live-gate-audit-graph-v1"
    )
    preflight_id: str
    node_types: tuple[Literal["live_gate_freeze", "live_gate_preflight"], ...]
    nodes: tuple[ArtifactReference, ...]

    @model_validator(mode="after")
    def validate_graph(self) -> "R02D3LiveGateAuditGraph":
        if self.node_types != ("live_gate_freeze", "live_gate_preflight"):
            raise ValueError("live-gate audit node order drifted")
        if len(self.nodes) != len(self.node_types):
            raise ValueError("live-gate audit graph length mismatch")
        return self


class R02D3LiveGatePersisted(StrictModel):
    schema_version: Literal["r02-d3-live-gate-persisted-v1"] = (
        "r02-d3-live-gate-persisted-v1"
    )
    preflight_id: str
    freeze: ArtifactReference
    preflight: ArtifactReference
    audit_graph: ArtifactReference


class R02D3LiveGateReplay(StrictModel):
    schema_version: Literal["r02-d3-live-gate-replay-v1"] = (
        "r02-d3-live-gate-replay-v1"
    )
    preflight_id: str
    verified_artifacts: Literal[3] = 3
    all_hashes_match: Literal[True] = True
    freeze_recomputed: Literal[True] = True
    preflight_recomputed: Literal[True] = True
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    micro_pilot_executed: Literal[False] = False


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_hash(path: Path, expected: str) -> None:
    if not path.is_file() or _sha256_file(path) != expected:
        raise R02D3LiveGateError(f"hash mismatch: {path}")


def _accepted_commit_is_ancestor(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", R02_D3_ACCEPTED_COMMIT, "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise R02D3LiveGateError("accepted D3 ancestry check failed") from exc
    return result.returncode == 0


def build_live_gate_freeze(
    root: Path,
    *,
    authorization_sha256: str,
    expected_executable_sha256: str,
) -> R02D3LiveGateFreeze:
    root = root.resolve()
    if expected_executable_sha256 != R02_D3_EXPECTED_EXECUTABLE_SHA256:
        raise R02D3LiveGateError("externally supplied executable pin mismatch")
    if not _accepted_commit_is_ancestor(root):
        raise R02D3LiveGateError("accepted D3 commit is not an ancestor of HEAD")
    _require_hash(root / "docs/r02-d3-preregistration.json", R02_D3_PREREGISTRATION_SHA256)
    _require_hash(root / "docs/r02-d3-zero-call-preflight.json", R02_D3_PREFLIGHT_SHA256)
    _require_hash(root / "docs/r02-d3-preflight-manifest.json", R02_D3_MANIFEST_SHA256)
    for _role, relative_path, expected in SOURCE_PINS:
        _require_hash(root / relative_path, expected)
    preregistration = R02D3Preregistration.model_validate_json(
        (root / "docs/r02-d3-preregistration.json").read_bytes()
    )
    executable = Path(preregistration.model_identity.executable_path).resolve()
    _require_hash(executable, expected_executable_sha256)
    return R02D3LiveGateFreeze(
        authorization_sha256=authorization_sha256,
        implementation_source_sha256=_sha256_file(Path(__file__).resolve()),
        preflight_script_sha256=_sha256_file(
            root / "scripts/r02_d3_live_gate_preflight.py"
        ),
        source_pins=tuple(
            R02D3LiveSourcePin(role=role, relative_path=relative_path, sha256=expected)
            for role, relative_path, expected in SOURCE_PINS
        ),
        accepted_contract_bindings=R02D3AcceptedContractBindings(
            micro_pilot_case_count=preregistration.execution.micro_pilot_case_count,
            micro_pilot_attempt_cap=preregistration.budget_stop.micro_pilot_attempt_cap,
            eligible_episode_count=preregistration.execution.eligible_episode_count,
            full_provider_attempt_cap=preregistration.budget_stop.full_provider_attempt_cap,
            utility_outcomes_available_to_continuation_gate=(
                preregistration.execution.utility_outcomes_available_to_continuation_gate
            ),
            per_attempt_token_reserve=preregistration.budget_stop.per_attempt_token_reserve,
            unsettled_attempt_cap=preregistration.budget_stop.unsettled_attempt_cap,
            full_evaluation_fail_closed_attempt_cap=(
                preregistration.budget_stop.full_evaluation_fail_closed_attempt_cap
            ),
            full_evaluation_fail_closed_rate_cap_ppm=(
                preregistration.budget_stop.full_evaluation_fail_closed_rate_cap_ppm
            ),
            failed_or_fallback_delta_e12=preregistration.execution.failed_or_fallback_delta_e12,
            selector_response_schema_sha256=preregistration.prompt.response_schema_sha256,
        ),
        continuation=R02D3ContinuationContract(),
        token_measurement=R02D3TokenMeasurementContract(),
        fail_closed_rate=R02D3FailClosedRateContract(),
        duplicate_reason_fallback=R02D3DuplicateReasonFallbackContract(),
    )


def build_live_gate_preflight(
    root: Path,
    freeze: R02D3LiveGateFreeze,
) -> R02D3LiveGatePreflight:
    recomputed = build_live_gate_freeze(
        root,
        authorization_sha256=freeze.authorization_sha256,
        expected_executable_sha256=freeze.expected_executable_sha256,
    )
    if canonical_json_bytes(recomputed) != canonical_json_bytes(freeze):
        raise R02D3LiveGateError("live-gate freeze did not reproduce")
    digest = canonical_sha256(freeze)
    return R02D3LiveGatePreflight(
        preflight_id=f"r02-d3-live-gate-{digest[:12]}",
        freeze_sha256=digest,
    )


def persist_live_gate_preflight(
    store: R02AppendOnlyArtifactStore,
    freeze: R02D3LiveGateFreeze,
    preflight: R02D3LiveGatePreflight,
) -> R02D3LiveGatePersisted:
    _ensure_r02_artifact_root(store)
    freeze_ref = store.write_json("freeze.json", freeze)
    preflight_ref = store.write_json("preflight.json", preflight)
    graph = R02D3LiveGateAuditGraph(
        preflight_id=preflight.preflight_id,
        node_types=("live_gate_freeze", "live_gate_preflight"),
        nodes=(freeze_ref, preflight_ref),
    )
    graph_ref = store.write_json("audit_graph.json", graph)
    return R02D3LiveGatePersisted(
        preflight_id=preflight.preflight_id,
        freeze=freeze_ref,
        preflight=preflight_ref,
        audit_graph=graph_ref,
    )


def replay_live_gate_preflight(
    root: Path,
    store: R02AppendOnlyArtifactStore,
    persisted: R02D3LiveGatePersisted,
) -> R02D3LiveGateReplay:
    freeze_bytes = store.read_bytes(persisted.freeze)
    preflight_bytes = store.read_bytes(persisted.preflight)
    graph_bytes = store.read_bytes(persisted.audit_graph)
    freeze = R02D3LiveGateFreeze.model_validate_json(freeze_bytes)
    preflight = R02D3LiveGatePreflight.model_validate_json(preflight_bytes)
    graph = R02D3LiveGateAuditGraph.model_validate_json(graph_bytes)
    if freeze_bytes != canonical_json_bytes(freeze):
        raise R02D3LiveGateError("stored live-gate freeze is not canonical")
    if preflight_bytes != canonical_json_bytes(preflight):
        raise R02D3LiveGateError("stored live-gate preflight is not canonical")
    if graph_bytes != canonical_json_bytes(graph):
        raise R02D3LiveGateError("stored live-gate graph is not canonical")
    if graph.nodes != (persisted.freeze, persisted.preflight):
        raise R02D3LiveGateError("live-gate graph reference mismatch")
    recomputed_freeze = build_live_gate_freeze(
        root,
        authorization_sha256=freeze.authorization_sha256,
        expected_executable_sha256=freeze.expected_executable_sha256,
    )
    recomputed_preflight = build_live_gate_preflight(root, recomputed_freeze)
    if canonical_json_bytes(recomputed_freeze) != freeze_bytes:
        raise R02D3LiveGateError("live-gate freeze replay mismatch")
    if canonical_json_bytes(recomputed_preflight) != preflight_bytes:
        raise R02D3LiveGateError("live-gate preflight replay mismatch")
    return R02D3LiveGateReplay(preflight_id=preflight.preflight_id)


def load_persisted(path: Path) -> R02D3LiveGatePersisted:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise R02D3LiveGateError("invalid live-gate persisted anchor") from exc
    return R02D3LiveGatePersisted.model_validate(value)
