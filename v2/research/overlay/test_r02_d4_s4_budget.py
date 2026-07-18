from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from .r02_d4_s4_budget import (
    ROOT,
    R02_D4_S4_AGGREGATE_TOKEN_CAP,
    R02_D4_S4_ELIGIBLE_EPISODE_COUNT,
    R02_D4_S4_EXPECTED_FOCUSED_TEST_COUNT,
    R02_D4_S4_MAXIMUM_DRAFT_PROMPT_UTF8_BYTES,
    R02_D4_S4_MAXIMUM_SELECTOR_PAYLOAD_UTF8_BYTES,
    R02_D4_S4_PER_ATTEMPT_TOKEN_RESERVE,
    R02_D4_S4_PROVIDER_ATTEMPT_CAP,
    R02D4S4BudgetError,
    expected_provider_budget,
    forbidden_capability_names,
    prompt_budget_evidence,
    verify_budget_payload,
    verify_focused_test_manifest,
    verify_freeze,
    verify_generation_retry_contract,
    verify_sealed_inputs,
)
from .r02_statistics import R02ProviderBudgetFreeze


def _read(relative_path: str) -> dict[str, object]:
    payload = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sealed_triplet() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return (
        _read("docs/r02-d4-s2a-frame-intent.json"),
        _read("docs/r02-d4-s2a-frame-manifest.json"),
        _read("docs/r02-d4-s2a-frame-seal.json"),
    )


def test_numeric_budget_is_exactly_69_times_32000() -> None:
    assert R02_D4_S4_ELIGIBLE_EPISODE_COUNT == 69
    assert R02_D4_S4_PROVIDER_ATTEMPT_CAP == 69
    assert R02_D4_S4_PER_ATTEMPT_TOKEN_RESERVE == 32_000
    assert R02_D4_S4_AGGREGATE_TOKEN_CAP == 2_208_000
    assert R02_D4_S4_PROVIDER_ATTEMPT_CAP * R02_D4_S4_PER_ATTEMPT_TOKEN_RESERVE == R02_D4_S4_AGGREGATE_TOKEN_CAP


def test_expected_provider_budget_matches_typed_contract() -> None:
    budget = expected_provider_budget()
    assert budget["eligible_episode_count"] == 69
    assert budget["provider_attempt_cap"] == 69
    assert budget["retry_attempt_cap"] == 0
    assert budget["aggregate_token_cap"] == 2_208_000
    assert budget["incremental_usd_cap"] == 0
    assert budget["provider_calls"] == 0
    assert budget["live_execution"] is False


def test_typed_budget_rejects_attempt_cap_tamper() -> None:
    payload = expected_provider_budget()
    payload["provider_attempt_cap"] = 68
    with pytest.raises(ValueError):
        R02ProviderBudgetFreeze.model_validate(payload)


def test_typed_budget_rejects_aggregate_token_tamper() -> None:
    payload = expected_provider_budget()
    payload["aggregate_token_cap"] = 2_207_999
    with pytest.raises(ValueError):
        R02ProviderBudgetFreeze.model_validate(payload)


def test_prompt_budget_evidence_is_exact() -> None:
    assert prompt_budget_evidence(ROOT) == (
        R02_D4_S4_MAXIMUM_DRAFT_PROMPT_UTF8_BYTES,
        R02_D4_S4_MAXIMUM_SELECTOR_PAYLOAD_UTF8_BYTES,
    )


def test_sealed_inputs_reproduce() -> None:
    verify_sealed_inputs(ROOT)


def test_generation_attempt_cap_tamper_is_rejected() -> None:
    intent, manifest, seal = _sealed_triplet()
    intent["generation_attempt_cap"] = 2
    with pytest.raises(R02D4S4BudgetError):
        verify_generation_retry_contract(intent, manifest, seal)


def test_manifest_generation_count_tamper_is_rejected() -> None:
    intent, manifest, seal = _sealed_triplet()
    manifest["frame_generation_count"] = 2
    with pytest.raises(R02D4S4BudgetError):
        verify_generation_retry_contract(intent, manifest, seal)


def test_seal_generation_count_tamper_is_rejected() -> None:
    intent, manifest, seal = _sealed_triplet()
    seal["frame_generation_count"] = 2
    with pytest.raises(R02D4S4BudgetError):
        verify_generation_retry_contract(intent, manifest, seal)


def test_manifest_retry_count_tamper_is_rejected() -> None:
    intent, manifest, seal = _sealed_triplet()
    manifest["retry_count"] = 1
    with pytest.raises(R02D4S4BudgetError):
        verify_generation_retry_contract(intent, manifest, seal)


def test_seal_retry_count_tamper_is_rejected() -> None:
    intent, manifest, seal = _sealed_triplet()
    seal["retry_count"] = 1
    with pytest.raises(R02D4S4BudgetError):
        verify_generation_retry_contract(intent, manifest, seal)


def test_manifest_replacement_count_tamper_is_rejected() -> None:
    intent, manifest, seal = _sealed_triplet()
    manifest["replacement_count"] = 1
    with pytest.raises(R02D4S4BudgetError):
        verify_generation_retry_contract(intent, manifest, seal)


def test_seal_replacement_count_tamper_is_rejected() -> None:
    intent, manifest, seal = _sealed_triplet()
    seal["replacement_count"] = 1
    with pytest.raises(R02D4S4BudgetError):
        verify_generation_retry_contract(intent, manifest, seal)


def test_budget_payload_retry_cap_tamper_is_rejected() -> None:
    payload = expected_provider_budget()
    payload["retry_attempt_cap"] = 1
    with pytest.raises(R02D4S4BudgetError):
        verify_budget_payload(payload)


def test_freeze_reproduces() -> None:
    verify_freeze(ROOT, _read("docs/r02-d4-s4-provider-budget-freeze.json"))


def test_freeze_eligible_count_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s4-provider-budget-freeze.json")
    freeze["sealed_eligible_episode_count"] = 68
    with pytest.raises(R02D4S4BudgetError):
        verify_freeze(ROOT, freeze)


def test_freeze_aggregate_token_tamper_is_rejected() -> None:
    freeze = _read("docs/r02-d4-s4-provider-budget-freeze.json")
    budget = copy.deepcopy(freeze["provider_budget"])
    assert isinstance(budget, dict)
    budget["aggregate_token_cap"] = 2_208_001
    freeze["provider_budget"] = budget
    with pytest.raises(R02D4S4BudgetError):
        verify_freeze(ROOT, freeze)


def test_focused_test_count_tamper_is_rejected() -> None:
    manifest = _read("docs/r02-d4-s4-focused-tests.json")
    assert manifest["expected_collected_tests"] == R02_D4_S4_EXPECTED_FOCUSED_TEST_COUNT
    manifest["expected_collected_tests"] = R02_D4_S4_EXPECTED_FOCUSED_TEST_COUNT - 1
    with pytest.raises(R02D4S4BudgetError):
        verify_focused_test_manifest(ROOT, manifest)


def test_focused_test_hash_tamper_is_rejected() -> None:
    manifest = _read("docs/r02-d4-s4-focused-tests.json")
    hashes = copy.deepcopy(manifest["test_file_sha256"])
    assert isinstance(hashes, dict)
    hashes["v2/research/overlay/test_r02_d4_s4_budget.py"] = "0" * 64
    manifest["test_file_sha256"] = hashes
    with pytest.raises(R02D4S4BudgetError):
        verify_focused_test_manifest(ROOT, manifest)


def test_budget_source_has_no_execution_imports() -> None:
    source_path = ROOT / "v2/research/overlay/r02_d4_s4_budget.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not imported.intersection({"subprocess", "socket", "requests", "urllib"})
    assert {"provider_call", "codex_exec", "retry", "replacement"}.issubset(
        forbidden_capability_names()
    )
