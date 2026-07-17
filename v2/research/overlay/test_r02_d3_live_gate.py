from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from .artifacts import ArtifactIntegrityError
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_d3_contracts import selector_output_schema
from .r02_d3_live_gate import (
    R02_D3_EXPECTED_EXECUTABLE_SHA256,
    R02D3ContinuationContract,
    R02D3FailClosedRateContract,
    R02D3LiveGateError,
    R02D3TokenMeasurementContract,
    build_live_gate_freeze,
    build_live_gate_preflight,
    persist_live_gate_preflight,
    replay_live_gate_preflight,
)
from .r02_selector import R02SelectorParseError, parse_selector_response


ROOT = Path(__file__).resolve().parents[3]
AUTHORIZATION = ROOT / "docs/r02-d3-live-gate-provider-free-authorization.md"


def _freeze():
    return build_live_gate_freeze(
        ROOT,
        authorization_sha256=hashlib.sha256(AUTHORIZATION.read_bytes()).hexdigest(),
        expected_executable_sha256=R02_D3_EXPECTED_EXECUTABLE_SHA256,
    )


def test_live_gate_freeze_reproduces_all_six_prerequisites() -> None:
    freeze = _freeze()
    assert freeze.expected_executable_sha256 == R02_D3_EXPECTED_EXECUTABLE_SHA256
    assert tuple(pin.role for pin in freeze.source_pins) == (
        "SELECTOR_ACCEPTANCE_AND_FALLBACK",
        "R02_TYPED_CONTRACTS",
        "CODEX_JSONL_AND_TOKEN_PARSER",
        "D3_FROZEN_CONTRACTS",
        "D3_PREFLIGHT_AND_LIVE_ARGV",
        "D3_PREFLIGHT_REPLAY",
    )
    assert freeze.continuation.no_stop_action == (
        "MUST_CONTINUE_REMAINING_49_IN_FRAME_ORDER"
    )
    assert not freeze.continuation.utility_outcomes_available_to_gate
    assert freeze.token_measurement.accounting_formula == "input_tokens + output_tokens"
    assert freeze.fail_closed_rate.derived_rate_cap_ppm == 90_909
    assert not freeze.duplicate_reason_fallback.output_schema_unique_items_present
    assert freeze.provider_calls == 0
    assert not freeze.live_execution
    assert not freeze.micro_pilot_executed


def test_accepted_preregistration_bindings_reject_independent_drift() -> None:
    freeze = _freeze()
    value = freeze.model_dump(mode="python")
    value["accepted_contract_bindings"]["full_provider_attempt_cap"] = 54
    with pytest.raises(ValidationError, match="accepted provider attempt cap binding"):
        type(freeze).model_validate(value)


def test_external_executable_pin_is_required_and_mismatch_fails_closed() -> None:
    with pytest.raises(R02D3LiveGateError, match="externally supplied executable pin"):
        build_live_gate_freeze(
            ROOT,
            authorization_sha256=hashlib.sha256(AUTHORIZATION.read_bytes()).hexdigest(),
            expected_executable_sha256="0" * 64,
        )


def test_continuation_cannot_pause_or_request_second_approval() -> None:
    value = R02D3ContinuationContract().model_dump(mode="json")
    value["discretionary_pause_after_no_stop"] = True
    with pytest.raises(ValidationError):
        R02D3ContinuationContract.model_validate(value)
    value = R02D3ContinuationContract().model_dump(mode="json")
    value["second_authorization_after_no_stop"] = True
    with pytest.raises(ValidationError):
        R02D3ContinuationContract.model_validate(value)


def test_token_measurement_counts_subsets_once_and_rejects_field_drift() -> None:
    contract = R02D3TokenMeasurementContract()
    assert not contract.cached_input_subtracted
    assert not contract.reasoning_output_added_again
    assert contract.per_attempt_reservation_tokens == 32_000
    value = contract.model_dump(mode="json")
    value["required_fields"] = ["input_tokens", "output_tokens"]
    with pytest.raises(ValidationError):
        R02D3TokenMeasurementContract.model_validate(value)


def test_fail_closed_ppm_is_floor_and_attempt_cap_is_primary() -> None:
    contract = R02D3FailClosedRateContract()
    assert 5 * 1_000_000 // 55 == contract.derived_rate_cap_ppm
    assert contract.precedence == "ATTEMPT_CAP_PRIMARY_RATE_IS_DERIVED_REPORTING"


def test_schema_without_unique_items_still_falls_back_on_duplicates() -> None:
    reason_schema = selector_output_schema()["properties"]["reason_codes"]
    assert "uniqueItems" not in reason_schema
    raw = json.dumps(
        {
            "selected_candidate_id": "P00",
            "confidence": 50,
            "reason_codes": ["LOWER_COST", "LOWER_COST"],
        }
    )
    with pytest.raises(R02SelectorParseError):
        parse_selector_response(raw)


def test_append_only_persistence_and_replay_detect_tampering(tmp_path: Path) -> None:
    freeze = _freeze()
    preflight = build_live_gate_preflight(ROOT, freeze)
    store = R02AppendOnlyArtifactStore(tmp_path / "r02-live-gate")
    persisted = persist_live_gate_preflight(store, freeze, preflight)
    replay = replay_live_gate_preflight(ROOT, store, persisted)
    assert replay.verified_artifacts == 3
    assert replay.all_hashes_match
    target = store.root / persisted.preflight.relative_path
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ArtifactIntegrityError):
        replay_live_gate_preflight(ROOT, store, persisted)


def test_live_gate_modules_have_no_provider_or_live_client_imports() -> None:
    source = (ROOT / "v2/research/overlay/r02_d3_live_gate.py").read_text("utf-8")
    tree = ast.parse(source)
    forbidden = {"openai", "anthropic", "requests", "httpx", "aiohttp"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert not imported & forbidden
