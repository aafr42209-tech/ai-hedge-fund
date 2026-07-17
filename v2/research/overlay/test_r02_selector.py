from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from .baselines import primary_deterministic
from .canonical import canonical_json_bytes
from .contracts import SyntheticEpisode
from .r02_candidates import prepare_provider_free_episode, selector_safe_payload
from .r02_contracts import (
    R02AcceptanceStatus,
    R02FallbackReason,
    R02ScriptedExchange,
    R02SelectionRun,
    R02SelectorRequest,
    R02SelectorResponseStatus,
    R02SelectorTokenLedger,
)
from .r02_selector import (
    R02SelectorBoundaryError,
    R02SelectorParseError,
    ScriptedR02SelectorClient,
    build_selector_request,
    parse_selector_response,
    run_scripted_selector_episode,
)
from . import r02_selector


ROOT = Path(__file__).resolve().parents[3]


def _triggered_episode() -> SyntheticEpisode:
    vectors = json.loads(
        (ROOT / "docs" / "r02-d1-test-vectors.json").read_text(encoding="utf-8")
    )
    vector = next(value for value in vectors["vectors"] if value["trigger"]["triggered"])
    path = ROOT / vectors["source_store_root"] / vector["fixture"]["relative_path"]
    return SyntheticEpisode.model_validate_json(path.read_text(encoding="utf-8"))


def _nontriggered_episode() -> SyntheticEpisode:
    vectors = json.loads(
        (ROOT / "docs" / "r02-d1-test-vectors.json").read_text(encoding="utf-8")
    )
    vector = next(
        value for value in vectors["vectors"] if not value["trigger"]["triggered"]
    )
    path = ROOT / vectors["source_store_root"] / vector["fixture"]["relative_path"]
    return SyntheticEpisode.model_validate_json(path.read_text(encoding="utf-8"))


def _preparation(*, attempt_count: int = 0):
    episode = _triggered_episode()
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id="r02-d2b-scripted-selector",
        provider_attempt_count=attempt_count,
    )
    assert preparation.candidate_set is not None
    assert preparation.permutation is not None
    return episode, preparation


def _response(candidate_id: str, *, confidence: int = 73) -> str:
    return json.dumps(
        {
            "schema_version": "r02-selector-response-v1",
            "selected_candidate_id": candidate_id,
            "confidence": confidence,
            "reason_codes": ["LOWER_TOTAL_QUANTITY"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _exchange(raw_response: str) -> R02ScriptedExchange:
    return R02ScriptedExchange(
        raw_response=raw_response,
        input_tokens=47,
        cached_input_tokens=11,
        output_tokens=19,
        reasoning_output_tokens=7,
    )


def _nonbaseline_presented_id(preparation) -> str:
    assert preparation.candidate_set is not None
    assert preparation.permutation is not None
    baseline_id = preparation.candidate_set.baseline_canonical_candidate_id
    return next(
        presented_id
        for presented_id, canonical_id in preparation.permutation.presented_to_canonical_map.items()
        if canonical_id != baseline_id
    )


def _run(raw_response: str, *, attempt_count: int = 0) -> R02SelectionRun:
    episode, preparation = _preparation(attempt_count=attempt_count)
    client = ScriptedR02SelectorClient(
        (_exchange(raw_response),),
        initial_attempt_count=attempt_count,
    )
    return run_scripted_selector_episode(episode, preparation, client)


def test_selector_request_uses_only_frozen_safe_payload_and_draft_prompt() -> None:
    _episode, preparation = _preparation()
    request = build_selector_request(preparation)
    expected_payload = selector_safe_payload(preparation.permutation)

    assert canonical_json_bytes(request.selector_payload) == canonical_json_bytes(expected_payload)
    rendered_payload = canonical_json_bytes(request.selector_payload).decode("utf-8")
    assert request.prompt.user_prompt.count(rendered_payload) == 1
    assert request.prompt.status == "DRAFT_NOT_FROZEN"
    assert request.prompt.input_contract == "SELECTOR_SAFE_PAYLOAD_ONLY"
    assert request.command_spec.transport_kind == "SCRIPTED_ONLY"
    assert request.command_spec.external_provider_enabled is False

    rendered_prompt = f"{request.prompt.system_prompt}\n{request.prompt.user_prompt}".lower()
    for forbidden in (
        "baseline",
        "no_change",
        "half_baseline_delta",
        "drop_max_cost_trade",
        "canonical_candidate_id",
        "presented_to_canonical_map",
        "derived_seed",
        "oracle",
        "headroom",
        "future_returns",
    ):
        assert forbidden not in rendered_prompt


def test_selector_response_parser_accepts_exact_strict_contract() -> None:
    parsed = parse_selector_response(_response("P00"))
    assert parsed.selected_candidate_id == "P00"
    assert parsed.confidence == 73
    assert [reason.value for reason in parsed.reason_codes] == ["LOWER_TOTAL_QUANTITY"]


@pytest.mark.parametrize(
    "raw_response",
    (
        "",
        "[]",
        "prefix {\"schema_version\":\"r02-selector-response-v1\"}",
        '{"schema_version":"r02-selector-response-v1","selected_candidate_id":"P00",'
        '"confidence":50.5,"reason_codes":["LOWER_TOTAL_QUANTITY"]}',
        '{"schema_version":"r02-selector-response-v1","selected_candidate_id":"P00",'
        '"confidence":50,"reason_codes":["NOT_FROZEN"]}',
        '{"schema_version":"r02-selector-response-v1","selected_candidate_id":"P00",'
        '"confidence":50,"reason_codes":["LOWER_TOTAL_QUANTITY"],"extra":true}',
        '{"schema_version":"r02-selector-response-v1","selected_candidate_id":"P00",'
        '"selected_candidate_id":"P01","confidence":50,'
        '"reason_codes":["LOWER_TOTAL_QUANTITY"]}',
        '{"schema_version":"r02-selector-response-v1","selected_candidate_id":"P00",'
        '"confidence":NaN,"reason_codes":["LOWER_TOTAL_QUANTITY"]}',
        '{"schema_version":"r02-selector-response-v1","selected_candidate_id":"P00",'
        '"confidence":50,"reason_codes":["LOWER_TOTAL_QUANTITY",'
        '"LOWER_TOTAL_QUANTITY"]}',
    ),
)
def test_selector_response_parser_rejects_noncontract_responses(raw_response: str) -> None:
    with pytest.raises(R02SelectorParseError):
        parse_selector_response(raw_response)


def test_accepted_candidate_records_execution_delta_and_token_ledger() -> None:
    _episode, preparation = _preparation(attempt_count=4)
    selected_id = _nonbaseline_presented_id(preparation)
    client = ScriptedR02SelectorClient(
        (_exchange(_response(selected_id)),),
        initial_attempt_count=4,
    )
    run = run_scripted_selector_episode(_episode, preparation, client)

    assert run.selector_response.status is R02SelectorResponseStatus.VALID
    assert run.acceptance_gate.status is R02AcceptanceStatus.ACCEPTED
    assert run.baseline_fallback is None
    assert run.execution_decision.baseline_fallback is False
    assert run.episode_result.paired_utility_delta_e12 == (
        run.episode_result.executed_score.utility_e12
        - run.episode_result.baseline_score.utility_e12
    )
    assert run.token_ledger.scripted_attempts_before == 4
    assert run.token_ledger.scripted_attempts_after == 5
    assert run.token_ledger.accounting_total_tokens == 66
    assert run.token_ledger.external_provider_calls == 0
    assert run.scripted_transport.external_provider_calls == 0
    assert run.episode_result.external_provider_calls == 0


def test_unknown_presented_id_typed_fallback_executes_baseline_with_zero_delta() -> None:
    run = _run(_response("P99"))
    assert run.selector_response.status is R02SelectorResponseStatus.VALID
    assert run.acceptance_gate.status is R02AcceptanceStatus.REJECTED
    assert run.baseline_fallback is not None
    assert run.baseline_fallback.reason_code is R02FallbackReason.UNKNOWN_PRESENTED_ID
    assert run.execution_decision.baseline_fallback is True
    assert run.episode_result.paired_utility_delta_e12 == 0


def test_invalid_selector_schema_typed_fallback_executes_baseline_with_zero_delta() -> None:
    run = _run('{"selected_candidate_id":"P00"}')
    assert run.selector_response.status is R02SelectorResponseStatus.INVALID
    assert run.selector_response.parsed_response is None
    assert run.acceptance_gate.status is R02AcceptanceStatus.REJECTED
    assert run.baseline_fallback is not None
    assert run.baseline_fallback.reason_code is R02FallbackReason.SELECTOR_SCHEMA_INVALID
    assert run.episode_result.paired_utility_delta_e12 == 0


def test_acceptance_revalidation_failure_typed_fallbacks_to_baseline(monkeypatch) -> None:
    episode, preparation = _preparation()
    selected_id = _nonbaseline_presented_id(preparation)
    baseline_validation = primary_deterministic(episode).validation

    def replace_with_different_validated_batch(_public, _batch):
        return baseline_validation

    monkeypatch.setattr(
        r02_selector,
        "validate_batch",
        replace_with_different_validated_batch,
    )
    client = ScriptedR02SelectorClient((_exchange(_response(selected_id)),))
    run = run_scripted_selector_episode(episode, preparation, client)

    assert run.acceptance_gate.status is R02AcceptanceStatus.REJECTED
    assert run.baseline_fallback is not None
    assert (
        run.baseline_fallback.reason_code
        is R02FallbackReason.ACCEPTANCE_VALIDATION_FAILED
    )
    assert run.episode_result.paired_utility_delta_e12 == 0


def test_attempt_counter_mismatch_fails_before_scripted_attempt() -> None:
    episode, preparation = _preparation(attempt_count=3)
    client = ScriptedR02SelectorClient((_exchange(_response("P00")),))
    with pytest.raises(R02SelectorBoundaryError, match="attempt counter"):
        run_scripted_selector_episode(episode, preparation, client)
    assert client.attempt_count == 0


def test_nontriggered_preparation_cannot_cross_selector_boundary() -> None:
    episode = _nontriggered_episode()
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id="r02-d2b-nontriggered-boundary",
    )
    with pytest.raises(R02SelectorBoundaryError, match="eligible D2a preparation"):
        build_selector_request(preparation)


def test_exhausted_scripted_client_fails_without_incrementing_attempt() -> None:
    _episode, preparation = _preparation(attempt_count=2)
    request = build_selector_request(preparation)
    client = ScriptedR02SelectorClient((), initial_attempt_count=2)
    with pytest.raises(R02SelectorBoundaryError, match="exhausted"):
        client.select(request)
    assert client.attempt_count == 2


def test_selector_contracts_reject_prompt_barrier_and_ledger_mutations() -> None:
    _episode, preparation = _preparation()
    request = build_selector_request(preparation)
    request_data = json.loads(request.model_dump_json())
    request_data["prompt"]["user_prompt"] += " baseline"
    with pytest.raises(ValidationError, match="information barrier"):
        R02SelectorRequest.model_validate_json(json.dumps(request_data))

    run = _run(_response("P00"))
    ledger_data = json.loads(run.token_ledger.model_dump_json())
    ledger_data["accounting_total_tokens"] += 1
    with pytest.raises(ValidationError, match="accounting total"):
        R02SelectorTokenLedger.model_validate_json(json.dumps(ledger_data))


def test_d2b_selector_module_has_no_provider_network_or_process_imports() -> None:
    source = Path(r02_selector.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint(
        {"anthropic", "httpx", "openai", "requests", "socket", "subprocess", "urllib"}
    )
