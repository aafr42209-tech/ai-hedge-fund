"""Provider-free execution preflight and live-gate freeze for R02 D4-S5."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_sha256, sha256_hex
from .r02_d3_preflight import (
    R02D3Preregistration,
    SubprocessZeroCallRunner,
    capture_transport_snapshot,
)
from .r02_d4_s2a_frame import R02D4S2AFrameManifest

ROOT = Path(__file__).resolve().parents[3]
R02_D4_S5_BASE_COMMIT = "f81909f82f3641da4b89d1e04bc0705b178f5a59"
R02_D4_S5_FRAME_ID = "r02-d4-s2a-frame-0716a1b9c13a"
R02_D4_S5_FRAME_MANIFEST_SHA256 = (
    "368e01509b04a53928df2d729f0914dbd0c1ee14c5221a6e189fbf7b8bfa4ba1"
)
R02_D4_S5_FRAME_SEAL_SHA256 = (
    "40aec915d3d24598ad2cbc46713a949b8c8ee5401d5768695b9be918b8bb5838"
)
R02_D4_S5_FRAME_TREE_SHA256 = (
    "65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29"
)
R02_D4_S5_S3_FREEZE_SHA256 = (
    "3538c09ffedd95f946a448ae298e04cad1cf933a99ff767b58472c4285c6b449"
)
R02_D4_S5_S4_BUDGET_SHA256 = (
    "722eb1aee9e115c76990387f7baf8a19dbfd66226ebaae4060acf29f1bf74e70"
)
R02_D4_S5_IDENTITY_SNAPSHOT_SHA256 = (
    "248f3683db276d45f275b5a2c236bc02909f6b7bf1be4ff56f6886573b2df5dc"
)
R02_D4_S5_D3_PREREGISTRATION_SHA256 = (
    "5e07d88e98e74f67a1377020ca8c19c6fada51756ebddd902706a1680eeb27d4"
)
R02_D4_S5_D3_LIVE_GATE_SHA256 = (
    "b650b8379d36292eaafd1d2df29f0f400df486da94d8c8e74f22348db2cd7b07"
)
R02_D4_S5_EXECUTABLE_SHA256 = (
    "cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4"
)
R02_D4_S5_FEATURE_CATALOG_SHA256 = (
    "14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad"
)
R02_D4_S5_FEATURE_DEFINITION_SHA256 = (
    "aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530"
)
R02_D4_S5_RESPONSE_SCHEMA_SHA256 = (
    "5466a24d3557e28251cb1393dac16e1049824637a27b969f3bea55c80ebc2eca"
)
R02_D4_S5_SYSTEM_PROMPT_SHA256 = (
    "139d5baa9277fd0095619829a4c8fcaed209ebde6cb18d3d78389619b693b358"
)
R02_D4_S5_USER_PROMPT_SHA256 = (
    "5011d5dd4bdd25e252c068f70f0ddf9f4dd83ce30f8f3f3130b125b8e91bb9dc"
)

R02_D4_S5_ELIGIBLE_COUNT = 69
R02_D4_S5_PROVIDER_ATTEMPT_CAP = 69
R02_D4_S5_PER_ATTEMPT_TOKEN_RESERVE = 32_000
R02_D4_S5_AGGREGATE_TOKEN_CAP = 2_208_000
R02_D4_S5_RETRY_CAP = 0
R02_D4_S5_REPLACEMENT_CAP = 0
R02_D4_S5_UNSETTLED_CAP = 0
R02_D4_S5_MICRO_PILOT_ATTEMPTS = 0
R02_D4_S5_LIVE_TIMEOUT_MS = 900_000
R02_D4_S5_LOCAL_COMMAND_TIMEOUT_SECONDS = 30
R02_D4_S5_MAX_PROVIDER_WAIT_MS = 62_100_000
R02_D4_S5_D3_FAIL_CLOSED_RATE_CEILING_PPM = 90_909
R02_D4_S5_FAIL_CLOSED_ATTEMPT_CAP = 6
R02_D4_S5_FAIL_CLOSED_RATE_PPM = 86_956
R02_D4_S5_NEXT_FAIL_CLOSED_RATE_PPM = 101_449
R02_D4_S5_EXECUTION_PLAN_SHA256 = (
    "a5e461a74a594a7f54a4751c8cb330ab4032c23ce25bdcbbd0dda6599c6af7d1"
)
R02_D4_S5_EXPECTED_FOCUSED_TEST_COUNT = 121
R02_D4_S5_ELIGIBLE_FRAME_ORDINALS = (
    2,
    8,
    14,
    20,
    26,
    38,
    50,
    62,
    74,
    80,
    86,
    92,
    98,
    104,
    116,
    122,
    128,
    134,
    146,
    *range(150, 200),
)

SOURCE_PINS = {
    "v2/research/overlay/r02_selector.py": "a90cc600ffc772c5fb4b1c964b5efc0a551de84a41eaa5c0a030b6d02b9b20f9",
    "v2/research/overlay/r02_contracts.py": "64a099560432152da875843d6cddb4d08acd3a402198adb14a5aec65ef0dab05",
    "v2/research/overlay/codex_exec_client.py": "4b3bb2e5bc9d1f406105bc7fd589bbfcb7541d259ebaf209252cb42ed329a1bd",
    "v2/research/overlay/r02_d3_contracts.py": "978d4fcf2cb2775a40ac515276a4c0c69899284dc05096360b5a661b2ab2ef47",
    "v2/research/overlay/r02_d3_preflight.py": "2376c5a4773de506aa577387397e4f59a497e623b7cfc262edbbbf9b1deb32a7",
    "v2/research/overlay/r02_d3_live_selector_adapter.py": "497ee163b8fed658c10a95ed0cebbe9cd9a2f511ddf910ae7f630777df04e4f7",
    "v2/research/overlay/r02_d3_live_orchestrator.py": "90d136202d385b025e0bf34b3e13429ee7a062cf1c9023115d2765828e0a10b2",
    "v2/research/overlay/r02_d3_live_runner_replay.py": "8d5459e9824d13ffd709f2baa0e1e7d47eda43e915d06806ef5dd8e86cdf0fa6",
    "v2/research/overlay/r02_d3_runner_contracts.py": "d5a70029f98140ba5cb400034e72774b12549f30bcf040602e2a427ddd95d86f",
    "v2/research/overlay/canonical.py": "a00f6b3b2d623d7da54a6e6e3bbc243d9f9de8b151bef3268f0ea9a8c5166671",
    "v2/research/overlay/r02_d4_s3_freeze.py": "b80221af86a7db365c00d67d33378597c10f70b14c856c4080c94a7c2bbac7c2",
    "v2/research/overlay/r02_d4_s4_budget.py": "8e9f3ca75d448ab69a1a0f21c810dd112e75c015673ce5bb1cc3a2c52a1b7a19",
}


class R02D4S5LiveGateError(RuntimeError):
    """Raised when an S5 preflight or frozen execution invariant drifts."""


def _require_equal(actual: object, expected: object, code: str) -> None:
    if actual != expected:
        raise R02D4S5LiveGateError(code)


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise R02D4S5LiveGateError(f"expected JSON object: {path}")
    return payload


def _verify_hash(repo_root: Path, relative_path: str, expected: str) -> None:
    _require_equal(
        sha256_hex((repo_root / relative_path).read_bytes()),
        expected,
        f"byte hash drift: {relative_path}",
    )


def build_execution_plan(manifest: Mapping[str, Any]) -> list[dict[str, object]]:
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        raise R02D4S5LiveGateError("frame case list missing")
    eligible = sorted(
        (
            case
            for case in cases
            if isinstance(case, dict) and case.get("eligible_opportunity") is True
        ),
        key=lambda case: int(case["frame_ordinal"]),
    )
    plan = [
        {
            "execution_ordinal": execution_ordinal,
            "frame_ordinal": int(case["frame_ordinal"]),
            "fixture_id": str(case["fixture_id"]),
            "stratum": str(case["stratum"]),
            "candidate_count": int(case["candidate_count"]),
            "fixture_sha256": str(case["fixture_artifact"]["sha256"]),
        }
        for execution_ordinal, case in enumerate(eligible)
    ]
    _require_equal(len(plan), R02_D4_S5_ELIGIBLE_COUNT, "eligible execution count drift")
    _require_equal(
        tuple(item["frame_ordinal"] for item in plan),
        R02_D4_S5_ELIGIBLE_FRAME_ORDINALS,
        "eligible frame order drift",
    )
    _require_equal(
        canonical_sha256(plan),
        R02_D4_S5_EXECUTION_PLAN_SHA256,
        "eligible execution plan hash drift",
    )
    return plan


def expected_failure_rate_contract() -> dict[str, object]:
    derived = (
        R02_D4_S5_FAIL_CLOSED_ATTEMPT_CAP * 1_000_000 // R02_D4_S5_ELIGIBLE_COUNT
    )
    next_rate = (
        (R02_D4_S5_FAIL_CLOSED_ATTEMPT_CAP + 1)
        * 1_000_000
        // R02_D4_S5_ELIGIBLE_COUNT
    )
    _require_equal(derived, R02_D4_S5_FAIL_CLOSED_RATE_PPM, "failure rate derivation drift")
    _require_equal(next_rate, R02_D4_S5_NEXT_FAIL_CLOSED_RATE_PPM, "next rate drift")
    if derived > R02_D4_S5_D3_FAIL_CLOSED_RATE_CEILING_PPM:
        raise R02D4S5LiveGateError("D4 failure rate loosens D3 ceiling")
    if next_rate <= R02_D4_S5_D3_FAIL_CLOSED_RATE_CEILING_PPM:
        raise R02D4S5LiveGateError("D4 failure cap is not maximal under D3 ceiling")
    return {
        "denominator_attempts": R02_D4_S5_ELIGIBLE_COUNT,
        "d3_rate_ceiling_ppm": R02_D4_S5_D3_FAIL_CLOSED_RATE_CEILING_PPM,
        "derived_rate_cap_ppm": derived,
        "next_integer_cap_rate_ppm": next_rate,
        "ppm_multiplier": 1_000_000,
        "precedence": "ATTEMPT_CAP_PRIMARY_RATE_IS_DERIVED_REPORTING",
        "primary_attempt_cap": R02_D4_S5_FAIL_CLOSED_ATTEMPT_CAP,
        "rounding": "FLOOR",
        "selection_rule": "MAX_INTEGER_CAP_WITH_DERIVED_RATE_NO_GREATER_THAN_D3_90909_PPM",
    }


def expected_budget_ledger_contract() -> dict[str, object]:
    return {
        "aggregate_token_cap": R02_D4_S5_AGGREGATE_TOKEN_CAP,
        "attempt_slot_debited_before_launch": True,
        "attempted_case_remains_in_itt": True,
        "initial_attempts_remaining": R02_D4_S5_PROVIDER_ATTEMPT_CAP,
        "initial_tokens_remaining": R02_D4_S5_AGGREGATE_TOKEN_CAP,
        "missing_or_invalid_usage_debit_tokens": R02_D4_S5_PER_ATTEMPT_TOKEN_RESERVE,
        "next_attempt_requires_full_reservation": True,
        "per_attempt_token_reserve": R02_D4_S5_PER_ATTEMPT_TOKEN_RESERVE,
        "provider_attempt_cap": R02_D4_S5_PROVIDER_ATTEMPT_CAP,
        "replacement_cap": R02_D4_S5_REPLACEMENT_CAP,
        "retry_cap": R02_D4_S5_RETRY_CAP,
        "successful_usage_debit": "INPUT_TOKENS_PLUS_OUTPUT_TOKENS",
        "unsettled_attempt_cap": R02_D4_S5_UNSETTLED_CAP,
        "unused_reservation_creates_attempt_credit": False,
    }


def expected_continuation_contract() -> dict[str, object]:
    return {
        "discretionary_pause_allowed": False,
        "execution_scope_if_separately_authorized": "ALL_69_ELIGIBLE_ONE_SHOT",
        "full_evaluation_attempts": R02_D4_S5_ELIGIBLE_COUNT,
        "interim_outcome_disclosure": False,
        "micro_pilot_attempts": R02_D4_S5_MICRO_PILOT_ATTEMPTS,
        "micro_pilot_used": False,
        "no_hard_stop_action": "MUST_CONTINUE_NEXT_ELIGIBLE_CASE_IN_FROZEN_ORDER",
        "remaining_attempts_after_micro": R02_D4_S5_ELIGIBLE_COUNT,
        "resume_after_hard_stop": False,
        "second_authorization_after_start": False,
        "stop_authority": "FROZEN_HARD_STOP_CONDITIONS_ONLY",
        "utility_outcomes_available_during_run": False,
    }


def expected_timeout_contract() -> dict[str, object]:
    return {
        "local_identity_command_timeout_seconds": R02_D4_S5_LOCAL_COMMAND_TIMEOUT_SECONDS,
        "maximum_provider_wait_ms_if_all_attempts_timeout": R02_D4_S5_MAX_PROVIDER_WAIT_MS,
        "per_attempt_live_timeout_ms": R02_D4_S5_LIVE_TIMEOUT_MS,
        "timeout_action": "DEBIT_ATTEMPT_AND_FULL_RESERVE_THEN_HARD_STOP_UNSETTLED_INVALID_RUN",
    }


def expected_token_measurement_contract() -> dict[str, object]:
    return {
        "accounting_formula": "input_tokens + output_tokens",
        "cached_input_is_subset_of_input": True,
        "cached_input_subtracted": False,
        "exactly_one_terminal_usage_event": True,
        "per_attempt_reservation_tokens": R02_D4_S5_PER_ATTEMPT_TOKEN_RESERVE,
        "reasoning_output_added_again": False,
        "reasoning_output_is_subset_of_output": True,
        "required_fields": [
            "cached_input_tokens",
            "input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
        ],
        "terminal_event_type": "turn.completed",
        "usage_field_path": "turn.completed.usage",
        "values_are_nonnegative_integers": True,
    }


def expected_hard_stop_conditions() -> list[str]:
    return [
        "MISSING_SEPARATE_LIVE_AUTHORIZATION",
        "TRUST_ANCHOR_PROTECTED_TREE_OR_SOURCE_PIN_DRIFT",
        "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
        "PROMPT_OUTPUT_SCHEMA_MODEL_PROVIDER_EXECUTABLE_FEATURE_OR_COMMAND_DRIFT",
        "ATTEMPT_OR_TOKEN_BUDGET_WOULD_BE_EXCEEDED",
        "TRANSPORT_TIMEOUT_NONZERO_EXIT_MISSING_USAGE_OR_UNSETTLED_ATTEMPT",
        "REPORTED_USAGE_OVER_32000_TOKEN_RESERVE",
        "SETTLED_FAIL_CLOSED_COUNT_WOULD_EXCEED_6",
        "AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE",
        "RETRY_REPLACEMENT_OR_RESUME_REQUESTED",
    ]


def _identity_capture_rows(preregistration: R02D3Preregistration) -> list[dict[str, object]]:
    snapshot = capture_transport_snapshot(
        preregistration,
        SubprocessZeroCallRunner(preregistration.model_identity),
    )
    return [
        {
            "label": capture.label,
            "argv_sha256": canonical_sha256(list(capture.argv)),
            "stdout_sha256": capture.stdout_sha256,
            "stderr_sha256": capture.stderr_sha256,
            "exit_code": capture.exit_code,
        }
        for capture in snapshot.captures
    ]


def revalidate_current_identity(repo_root: Path) -> dict[str, object]:
    preregistration = R02D3Preregistration.model_validate_json(
        (repo_root / "docs/r02-d3-preregistration.json").read_bytes()
    )
    rows = _identity_capture_rows(preregistration)
    snapshot = _read_object(
        repo_root / "docs/r02-d4-s5-execution-identity-snapshot.json"
    )
    _require_equal(rows, snapshot.get("captures"), "current identity capture drift")
    _require_equal(
        canonical_sha256(rows),
        snapshot.get("capture_summary_sha256"),
        "current identity capture summary drift",
    )
    identity = snapshot.get("execution_identity")
    if not isinstance(identity, dict):
        raise R02D4S5LiveGateError("execution identity block missing")
    _require_equal(
        preregistration.model_identity.executable_sha256,
        R02_D4_S5_EXECUTABLE_SHA256,
        "D3 preregistered executable hash drift",
    )
    _require_equal(
        identity.get("executable_sha256"),
        R02_D4_S5_EXECUTABLE_SHA256,
        "snapshot executable hash drift",
    )
    _require_equal(
        identity.get("feature_catalog_sha256"),
        R02_D4_S5_FEATURE_CATALOG_SHA256,
        "snapshot feature catalog drift",
    )
    _require_equal(
        identity.get("feature_definition_sha256"),
        R02_D4_S5_FEATURE_DEFINITION_SHA256,
        "snapshot feature definition drift",
    )
    _require_equal(snapshot.get("provider_calls"), 0, "identity capture provider calls not zero")
    _require_equal(
        snapshot.get("codex_exec_invocations"),
        0,
        "identity capture Codex exec invocations not zero",
    )
    return snapshot


def verify_sealed_inputs(repo_root: Path) -> None:
    pins = {
        "docs/r02-d4-s2a-frame-manifest.json": R02_D4_S5_FRAME_MANIFEST_SHA256,
        "docs/r02-d4-s2a-frame-seal.json": R02_D4_S5_FRAME_SEAL_SHA256,
        "docs/r02-d4-s3-statistical-freeze.json": R02_D4_S5_S3_FREEZE_SHA256,
        "docs/r02-d4-s4-provider-budget-freeze.json": R02_D4_S5_S4_BUDGET_SHA256,
        "docs/r02-d4-s5-execution-identity-snapshot.json": R02_D4_S5_IDENTITY_SNAPSHOT_SHA256,
        "docs/r02-d3-preregistration.json": R02_D4_S5_D3_PREREGISTRATION_SHA256,
        "docs/r02-d3-live-gate-freeze-candidate.json": R02_D4_S5_D3_LIVE_GATE_SHA256,
        **SOURCE_PINS,
    }
    for relative_path, expected in pins.items():
        _verify_hash(repo_root, relative_path, expected)
    manifest = _read_object(repo_root / "docs/r02-d4-s2a-frame-manifest.json")
    seal = _read_object(repo_root / "docs/r02-d4-s2a-frame-seal.json")
    s4 = _read_object(repo_root / "docs/r02-d4-s4-provider-budget-freeze.json")
    _require_equal(manifest.get("frame_id"), R02_D4_S5_FRAME_ID, "manifest frame ID drift")
    _require_equal(seal.get("frame_id"), R02_D4_S5_FRAME_ID, "seal frame ID drift")
    _require_equal(manifest.get("total_eligible_count"), 69, "eligible count drift")
    _require_equal(manifest.get("retry_count"), 0, "manifest retry count drift")
    _require_equal(seal.get("retry_count"), 0, "seal retry count drift")
    _require_equal(manifest.get("replacement_count"), 0, "manifest replacement drift")
    _require_equal(seal.get("replacement_count"), 0, "seal replacement drift")
    _require_equal(seal.get("full_tree_sha256"), R02_D4_S5_FRAME_TREE_SHA256, "tree drift")
    _require_equal(
        s4.get("provider_budget", {}).get("provider_attempt_cap"),
        R02_D4_S5_PROVIDER_ATTEMPT_CAP,
        "S4 attempt cap drift",
    )
    _require_equal(
        s4.get("provider_budget", {}).get("aggregate_token_cap"),
        R02_D4_S5_AGGREGATE_TOKEN_CAP,
        "S4 token cap drift",
    )
    build_execution_plan(manifest)


def verify_focused_test_manifest(repo_root: Path, manifest: Mapping[str, Any]) -> None:
    _require_equal(manifest.get("status"), "FROZEN_EXACT_TEST_SUITE", "test status drift")
    _require_equal(
        manifest.get("expected_collected_tests"),
        R02_D4_S5_EXPECTED_FOCUSED_TEST_COUNT,
        "focused test count drift",
    )
    files = manifest.get("test_files")
    hashes = manifest.get("test_file_sha256")
    if not isinstance(files, list) or not isinstance(hashes, dict):
        raise R02D4S5LiveGateError("focused test structure drift")
    _require_equal(len(files), 11, "focused test file count drift")
    _require_equal(set(files), set(hashes), "focused test hash key drift")
    for relative_path in files:
        _verify_hash(repo_root, relative_path, str(hashes[relative_path]))
    _require_equal(manifest.get("provider_calls"), 0, "test provider calls not zero")
    _require_equal(manifest.get("codex_exec_invocations"), 0, "test Codex exec not zero")
    _require_equal(manifest.get("live_execution"), False, "test LIVE not false")


def verify_live_gate_freeze(repo_root: Path, freeze: Mapping[str, Any]) -> None:
    verify_sealed_inputs(repo_root)
    _require_equal(
        freeze.get("schema_version"),
        "r02-d4-s5-live-gate-freeze-v1",
        "S5 live-gate schema drift",
    )
    _require_equal(
        freeze.get("status"),
        "PROVIDER_FREE_EXECUTION_PREFLIGHT_LIVE_GATE_PENDING_INDEPENDENT_REVIEW",
        "S5 status drift",
    )
    _require_equal(freeze.get("freeze_base_commit"), R02_D4_S5_BASE_COMMIT, "base commit drift")
    _require_equal(freeze.get("frame_id"), R02_D4_S5_FRAME_ID, "freeze frame ID drift")
    _require_equal(freeze.get("budget_ledger"), expected_budget_ledger_contract(), "ledger drift")
    _require_equal(
        freeze.get("failure_rate_contract"),
        expected_failure_rate_contract(),
        "failure-rate contract drift",
    )
    _require_equal(
        freeze.get("continuation_contract"),
        expected_continuation_contract(),
        "continuation contract drift",
    )
    _require_equal(freeze.get("timeout_contract"), expected_timeout_contract(), "timeout drift")
    _require_equal(
        freeze.get("token_measurement"),
        expected_token_measurement_contract(),
        "token measurement drift",
    )
    _require_equal(
        freeze.get("hard_stop_conditions"),
        expected_hard_stop_conditions(),
        "hard-stop contract drift",
    )
    order = freeze.get("execution_order")
    if not isinstance(order, dict):
        raise R02D4S5LiveGateError("execution order block missing")
    _require_equal(
        order.get("eligible_frame_ordinals"),
        list(R02_D4_S5_ELIGIBLE_FRAME_ORDINALS),
        "frozen ordinal sequence drift",
    )
    _require_equal(
        order.get("execution_plan_sha256"),
        R02_D4_S5_EXECUTION_PLAN_SHA256,
        "frozen execution plan hash drift",
    )
    _require_equal(
        freeze.get("micro_pilot_contract"),
        {
            "attempt_cap": 0,
            "case_count": 0,
            "decision": "NO_MICRO_PILOT",
            "rationale": "D3_TRANSPORT_ALREADY_VALIDATED_AND_INTERIM_GATE_WOULD_ADD_OPTIONAL_STOPPING_SURFACE",
            "utility_outcomes_available_before_full_closeout": False,
        },
        "micro-pilot contract drift",
    )
    _require_equal(
        freeze.get("settled_fallback_contract"),
        {
            "failed_or_fallback_delta_e12": 0,
            "fallback_counts_as_fail_closed_attempt": True,
            "maximum_settled_fail_closed_attempts": 6,
            "repair_or_dedup_allowed": False,
            "seventh_settled_fail_closed_action": "HARD_STOP_INVALID_RUN",
        },
        "settled fallback contract drift",
    )
    for field, expected in (
        ("provider_calls", 0),
        ("codex_exec_invocations", 0),
        ("micro_pilot_executed", False),
        ("live_execution", False),
        ("live_authorization_created", False),
        ("runner_implementation_created", False),
        ("retry_count", 0),
        ("replacement_count", 0),
        ("commit_created", False),
        ("push_performed", False),
    ):
        _require_equal(freeze.get(field), expected, f"S5 boundary drift: {field}")
    _require_equal(
        freeze.get("live_authorization"), "NOT_AUTHORIZED", "LIVE authorization drift"
    )
    source_hash = sha256_hex(
        (repo_root / "v2/research/overlay/r02_d4_s5_live_gate.py").read_bytes()
    )
    _require_equal(freeze.get("live_gate_source_sha256"), source_hash, "S5 source hash drift")
    focused_path = repo_root / "docs/r02-d4-s5-focused-tests.json"
    _require_equal(
        freeze.get("focused_test_manifest_sha256"),
        sha256_hex(focused_path.read_bytes()),
        "S5 focused-test manifest hash drift",
    )
    verify_focused_test_manifest(repo_root, _read_object(focused_path))


def local_identity_command_labels() -> tuple[str, ...]:
    return (
        "version",
        "login_status",
        "baseline_features",
        "post_disable_features",
        "exec_help",
    )
