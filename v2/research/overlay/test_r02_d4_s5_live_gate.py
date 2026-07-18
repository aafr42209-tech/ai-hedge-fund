from __future__ import annotations

import ast
import copy
import json

import pytest

from .canonical import canonical_sha256
from .r02_d4_s5_live_gate import (
    ROOT,
    R02_D4_S5_AGGREGATE_TOKEN_CAP,
    R02_D4_S5_D3_FAIL_CLOSED_RATE_CEILING_PPM,
    R02_D4_S5_ELIGIBLE_COUNT,
    R02_D4_S5_ELIGIBLE_FRAME_ORDINALS,
    R02_D4_S5_EXECUTION_PLAN_SHA256,
    R02_D4_S5_EXPECTED_FOCUSED_TEST_COUNT,
    R02_D4_S5_FAIL_CLOSED_ATTEMPT_CAP,
    R02_D4_S5_FAIL_CLOSED_RATE_PPM,
    R02_D4_S5_LIVE_TIMEOUT_MS,
    R02_D4_S5_MAX_PROVIDER_WAIT_MS,
    R02_D4_S5_NEXT_FAIL_CLOSED_RATE_PPM,
    R02_D4_S5_PROVIDER_ATTEMPT_CAP,
    R02D4S5LiveGateError,
    build_execution_plan,
    expected_budget_ledger_contract,
    expected_continuation_contract,
    expected_failure_rate_contract,
    expected_hard_stop_conditions,
    expected_timeout_contract,
    expected_token_measurement_contract,
    local_identity_command_labels,
    revalidate_current_identity,
    verify_focused_test_manifest,
    verify_live_gate_freeze,
    verify_sealed_inputs,
)


def _read(relative_path: str) -> dict[str, object]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_execution_plan_has_exact_69_case_order_and_hash() -> None:
    plan = build_execution_plan(_read("docs/r02-d4-s2a-frame-manifest.json"))
    assert len(plan) == R02_D4_S5_ELIGIBLE_COUNT == 69
    assert tuple(item["frame_ordinal"] for item in plan) == R02_D4_S5_ELIGIBLE_FRAME_ORDINALS
    assert canonical_sha256(plan) == R02_D4_S5_EXECUTION_PLAN_SHA256


def test_execution_plan_first_and_last_are_pinned() -> None:
    plan = build_execution_plan(_read("docs/r02-d4-s2a-frame-manifest.json"))
    assert plan[0]["fixture_id"] == "development-0002"
    assert plan[0]["frame_ordinal"] == 2
    assert plan[-1]["fixture_id"] == "development-0560"
    assert plan[-1]["frame_ordinal"] == 199


def test_failure_rate_contract_is_exact() -> None:
    contract = expected_failure_rate_contract()
    assert contract["primary_attempt_cap"] == R02_D4_S5_FAIL_CLOSED_ATTEMPT_CAP == 6
    assert contract["derived_rate_cap_ppm"] == R02_D4_S5_FAIL_CLOSED_RATE_PPM == 86_956
    assert contract["next_integer_cap_rate_ppm"] == R02_D4_S5_NEXT_FAIL_CLOSED_RATE_PPM == 101_449


def test_failure_cap_is_maximal_without_loosening_d3_rate() -> None:
    assert R02_D4_S5_FAIL_CLOSED_RATE_PPM <= R02_D4_S5_D3_FAIL_CLOSED_RATE_CEILING_PPM
    assert R02_D4_S5_NEXT_FAIL_CLOSED_RATE_PPM > R02_D4_S5_D3_FAIL_CLOSED_RATE_CEILING_PPM


def test_budget_ledger_is_exact() -> None:
    ledger = expected_budget_ledger_contract()
    assert ledger["provider_attempt_cap"] == R02_D4_S5_PROVIDER_ATTEMPT_CAP == 69
    assert ledger["aggregate_token_cap"] == R02_D4_S5_AGGREGATE_TOKEN_CAP == 2_208_000
    assert ledger["retry_cap"] == 0
    assert ledger["replacement_cap"] == 0
    assert ledger["unsettled_attempt_cap"] == 0


def test_continuation_contract_disables_micro_pilot_and_interim_gate() -> None:
    continuation = expected_continuation_contract()
    assert continuation["micro_pilot_used"] is False
    assert continuation["micro_pilot_attempts"] == 0
    assert continuation["interim_outcome_disclosure"] is False
    assert continuation["execution_scope_if_separately_authorized"] == "ALL_69_ELIGIBLE_ONE_SHOT"


def test_timeout_contract_is_exact() -> None:
    timeout = expected_timeout_contract()
    assert timeout["per_attempt_live_timeout_ms"] == R02_D4_S5_LIVE_TIMEOUT_MS == 900_000
    assert timeout["maximum_provider_wait_ms_if_all_attempts_timeout"] == R02_D4_S5_MAX_PROVIDER_WAIT_MS == 62_100_000
    assert timeout["local_identity_command_timeout_seconds"] == 30


def test_token_measurement_contract_is_exact() -> None:
    token = expected_token_measurement_contract()
    assert token["accounting_formula"] == "input_tokens + output_tokens"
    assert token["per_attempt_reservation_tokens"] == 32_000
    assert token["cached_input_subtracted"] is False
    assert token["reasoning_output_added_again"] is False


def test_hard_stop_conditions_include_required_boundaries() -> None:
    conditions = expected_hard_stop_conditions()
    assert "MISSING_SEPARATE_LIVE_AUTHORIZATION" in conditions
    assert "SETTLED_FAIL_CLOSED_COUNT_WOULD_EXCEED_6" in conditions
    assert "RETRY_REPLACEMENT_OR_RESUME_REQUESTED" in conditions


def test_sealed_inputs_reproduce() -> None:
    verify_sealed_inputs(ROOT)


def test_identity_snapshot_is_provider_free_and_matches_d3() -> None:
    snapshot = _read("docs/r02-d4-s5-execution-identity-snapshot.json")
    assert snapshot["status"] == "PASS_D3_EXECUTION_IDENTITY_REVALIDATED_PROVIDER_FREE"
    assert snapshot["identity_matches_d3"] is True
    assert snapshot["capture_count"] == 5
    assert snapshot["provider_calls"] == 0
    assert snapshot["codex_exec_invocations"] == 0


def test_current_identity_revalidation_matches_snapshot() -> None:
    snapshot = revalidate_current_identity(ROOT)
    assert snapshot["identity_matches_d3"] is True
    assert snapshot["capture_summary_sha256"] == "6cb79e5f61d68032a4565a2eec66b6083bd34a4b69a6164c38da07d9f8ae7b23"


def test_live_gate_freeze_reproduces() -> None:
    verify_live_gate_freeze(ROOT, _read("docs/r02-d4-s5-live-gate-freeze.json"))


def test_micro_pilot_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s5-live-gate-freeze.json")
    block = copy.deepcopy(freeze["micro_pilot_contract"])
    assert isinstance(block, dict)
    block["attempt_cap"] = 1
    freeze["micro_pilot_contract"] = block
    with pytest.raises(R02D4S5LiveGateError):
        verify_live_gate_freeze(ROOT, freeze)


def test_failure_cap_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s5-live-gate-freeze.json")
    block = copy.deepcopy(freeze["failure_rate_contract"])
    assert isinstance(block, dict)
    block["primary_attempt_cap"] = 7
    freeze["failure_rate_contract"] = block
    with pytest.raises(R02D4S5LiveGateError):
        verify_live_gate_freeze(ROOT, freeze)


def test_execution_order_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s5-live-gate-freeze.json")
    block = copy.deepcopy(freeze["execution_order"])
    assert isinstance(block, dict)
    ordinals = list(block["eligible_frame_ordinals"])
    ordinals[0], ordinals[1] = ordinals[1], ordinals[0]
    block["eligible_frame_ordinals"] = ordinals
    freeze["execution_order"] = block
    with pytest.raises(R02D4S5LiveGateError):
        verify_live_gate_freeze(ROOT, freeze)


def test_budget_ledger_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s5-live-gate-freeze.json")
    block = copy.deepcopy(freeze["budget_ledger"])
    assert isinstance(block, dict)
    block["provider_attempt_cap"] = 70
    freeze["budget_ledger"] = block
    with pytest.raises(R02D4S5LiveGateError):
        verify_live_gate_freeze(ROOT, freeze)


def test_timeout_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s5-live-gate-freeze.json")
    block = copy.deepcopy(freeze["timeout_contract"])
    assert isinstance(block, dict)
    block["per_attempt_live_timeout_ms"] = 900_001
    freeze["timeout_contract"] = block
    with pytest.raises(R02D4S5LiveGateError):
        verify_live_gate_freeze(ROOT, freeze)


def test_live_authorization_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s5-live-gate-freeze.json")
    freeze["live_authorization"] = "AUTHORIZED"
    with pytest.raises(R02D4S5LiveGateError):
        verify_live_gate_freeze(ROOT, freeze)


def test_runner_implementation_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s5-live-gate-freeze.json")
    freeze["runner_implementation_created"] = True
    with pytest.raises(R02D4S5LiveGateError):
        verify_live_gate_freeze(ROOT, freeze)


def test_retry_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s5-live-gate-freeze.json")
    freeze["retry_count"] = 1
    with pytest.raises(R02D4S5LiveGateError):
        verify_live_gate_freeze(ROOT, freeze)


def test_focused_test_count_tamper_is_rejected() -> None:
    manifest = _read("docs/r02-d4-s5-focused-tests.json")
    assert manifest["expected_collected_tests"] == R02_D4_S5_EXPECTED_FOCUSED_TEST_COUNT
    manifest["expected_collected_tests"] = R02_D4_S5_EXPECTED_FOCUSED_TEST_COUNT - 1
    with pytest.raises(R02D4S5LiveGateError):
        verify_focused_test_manifest(ROOT, manifest)


def test_focused_test_hash_tamper_is_rejected() -> None:
    manifest = _read("docs/r02-d4-s5-focused-tests.json")
    hashes = copy.deepcopy(manifest["test_file_sha256"])
    assert isinstance(hashes, dict)
    hashes["v2/research/overlay/test_r02_d4_s5_live_gate.py"] = "0" * 64
    manifest["test_file_sha256"] = hashes
    with pytest.raises(R02D4S5LiveGateError):
        verify_focused_test_manifest(ROOT, manifest)


def test_live_gate_source_only_uses_allowlisted_local_identity_capture() -> None:
    source = (ROOT / "v2/research/overlay/r02_d4_s5_live_gate.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    direct_imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not direct_imports.intersection({"subprocess", "socket", "requests", "urllib"})
    assert local_identity_command_labels() == (
        "version",
        "login_status",
        "baseline_features",
        "post_disable_features",
        "exec_help",
    )
