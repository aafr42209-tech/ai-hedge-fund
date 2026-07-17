from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from . import r02_candidates
from .baselines import primary_deterministic
from .canonical import canonical_sha256
from .contracts import CostLedger, CostLine, SyntheticEpisode
from .r02_candidates import (
    R02IntegrityError,
    _baseline_candidate,
    build_candidate_permutation,
    build_candidate_set,
    canonical_candidate_bytes,
    canonical_candidate_id,
    evaluate_trigger,
    prepare_provider_free_episode,
    selector_safe_payload,
    verify_freeze_spec,
)
from .r02_contracts import (
    R02CandidateBatch,
    R02CandidateDecision,
    R02CandidatePermutation,
    R02CandidateRole,
    R02CandidateSet,
    R02EligibilityDecision,
    R02Identity,
    R02NoCallReason,
    R02PreparationState,
    R02_FREEZE_SHA256,
)

ROOT = Path(__file__).resolve().parents[3]
VECTORS_PATH = ROOT / "docs" / "r02-d1-test-vectors.json"


def _vectors() -> dict[str, object]:
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def _episode_for_vector(vector: dict[str, object]) -> SyntheticEpisode:
    catalog = _vectors()
    fixture = vector["fixture"]
    path = ROOT / str(catalog["source_store_root"]) / str(fixture["relative_path"])
    return SyntheticEpisode.model_validate_json(path.read_text(encoding="utf-8"))


def _expected_orders(candidate: R02CandidateBatch) -> str:
    return "|".join(
        f"{asset_id}:{candidate.decisions[asset_id].action}:{candidate.decisions[asset_id].quantity}"
        for asset_id in sorted(candidate.decisions)
    )


def _candidate_set_for(episode: SyntheticEpisode):
    freeze = verify_freeze_spec()
    baseline = primary_deterministic(episode)
    baseline_candidate = _baseline_candidate(baseline.validation)
    trigger_input, trigger = evaluate_trigger(
        baseline.validation.cost_ledger,
        baseline_candidate,
    )
    identity = R02Identity(
        experiment_id="r02-d2a-test",
        fixture_id=episode.public.case_id,
        fixture_content_sha256=episode.content_sha256,
    )
    eligibility = R02EligibilityDecision(
        identity=identity,
        public_fixture_sha256=canonical_sha256(episode.public),
        trigger_rule_sha256=canonical_sha256(freeze["trigger"]),
        trigger_input_sha256=canonical_sha256(trigger_input),
        trigger_input=trigger_input,
        trigger=trigger,
    )
    return baseline, eligibility, build_candidate_set(
        episode.public,
        baseline.validation,
        eligibility,
        freeze,
    )


@pytest.mark.parametrize("vector", _vectors()["vectors"], ids=lambda value: value["case_id"])
def test_frozen_d1_vectors_reproduce_exactly(vector) -> None:
    episode = _episode_for_vector(vector)
    _baseline, eligibility, candidate_set = _candidate_set_for(episode)
    permutation = build_candidate_permutation(candidate_set, episode.content_sha256)

    assert eligibility.trigger.model_dump(mode="json", exclude={"schema_version", "trigger_id"}) == vector["trigger"]
    assert [
        {
            "role": candidate.primary_role.value,
            "aliases": [alias.value for alias in candidate.aliases],
            "canonical_candidate_id": candidate.canonical_candidate_id,
            "orders": _expected_orders(candidate.candidate),
        }
        for candidate in candidate_set.candidates
    ] == vector["candidates"]
    assert permutation.derived_seed_hex == vector["permutation_seed"]
    assert list(permutation.presented_order) == vector["presented_order"]


def test_trigger_uses_exact_positive_integer_ceiling_boundary() -> None:
    candidate = R02CandidateBatch(
        decisions={
            f"A{index}": R02CandidateDecision(action="hold", quantity=0)
            for index in range(6)
        }
    )
    below = CostLedger(
        lines=(
            CostLine(
                asset_id="A0",
                action="buy",
                quantity=1,
                notional_cents=10_000,
                commission_cents=49,
                half_spread_cents=0,
                slippage_cents=0,
                total_cost_cents=49,
            ),
        ),
        total_cost_cents=49,
        total_notional_cents=10_000,
    )
    exact = below.model_copy(
        update={
            "lines": (
                below.lines[0].model_copy(
                    update={"commission_cents": 50, "total_cost_cents": 50}
                ),
            ),
            "total_cost_cents": 50,
        }
    )
    _input, below_decision = evaluate_trigger(below, candidate)
    _input, exact_decision = evaluate_trigger(exact, candidate)
    assert below_decision.max_traded_effective_cost_bps == 49
    assert below_decision.triggered is False
    assert exact_decision.max_traded_effective_cost_bps == 50
    assert exact_decision.triggered is True


def test_candidate_identity_is_compact_sorted_ascii_json() -> None:
    candidate = R02CandidateBatch(
        decisions={
            f"A{index}": R02CandidateDecision(action="hold", quantity=0)
            for index in reversed(range(6))
        }
    )
    encoded = canonical_candidate_bytes(candidate)
    assert b" " not in encoded
    assert b"\n" not in encoded
    assert encoded.startswith(b'{"decisions":{"A0"')
    assert canonical_candidate_id(candidate) == canonical_candidate_id(
        R02CandidateBatch.model_validate_json(encoded)
    )


def test_candidate_contract_rejects_extra_or_incomplete_fields() -> None:
    with pytest.raises(ValidationError):
        R02CandidateDecision.model_validate(
            {"action": "hold", "quantity": 0, "oracle_utility": 1}
        )
    with pytest.raises(ValidationError):
        R02CandidateBatch(
            decisions={"A0": R02CandidateDecision(action="hold", quantity=0)}
        )


def test_candidate_set_contract_rejects_mutated_content_identity() -> None:
    vector = next(value for value in _vectors()["vectors"] if value["trigger"]["triggered"])
    _baseline, _eligibility, candidate_set = _candidate_set_for(
        _episode_for_vector(vector)
    )
    payload = candidate_set.model_dump(mode="json")
    payload["raw_candidates"][0]["canonical_candidate_id"] = "0" * 64
    with pytest.raises(ValidationError, match="raw candidate identity mismatch"):
        R02CandidateSet.model_validate_json(json.dumps(payload))


def test_permutation_contract_rejects_non_hmac_order() -> None:
    vector = next(value for value in _vectors()["vectors"] if value["trigger"]["triggered"])
    episode = _episode_for_vector(vector)
    _baseline, _eligibility, candidate_set = _candidate_set_for(episode)
    permutation = build_candidate_permutation(candidate_set, episode.content_sha256)
    payload = permutation.model_dump(mode="json")
    payload["presented_order"][0], payload["presented_order"][1] = (
        payload["presented_order"][1],
        payload["presented_order"][0],
    )
    payload["presented_to_canonical_map"]["P00"], payload["presented_to_canonical_map"]["P01"] = (
        payload["presented_to_canonical_map"]["P01"],
        payload["presented_to_canonical_map"]["P00"],
    )
    payload["presented_candidates"][0], payload["presented_candidates"][1] = (
        payload["presented_candidates"][1],
        payload["presented_candidates"][0],
    )
    payload["presented_candidates"][0]["presented_id"] = "P00"
    payload["presented_candidates"][1]["presented_id"] = "P01"
    with pytest.raises(ValidationError, match="HMAC candidate order mismatch"):
        R02CandidatePermutation.model_validate_json(json.dumps(payload))


def test_selector_payload_hides_roles_hashes_seed_and_map() -> None:
    vector = next(value for value in _vectors()["vectors"] if value["trigger"]["triggered"])
    episode = _episode_for_vector(vector)
    _baseline, _eligibility, candidate_set = _candidate_set_for(episode)
    payload = selector_safe_payload(
        build_candidate_permutation(candidate_set, episode.content_sha256)
    )
    rendered = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "BASELINE",
        "NO_CHANGE",
        "canonical_candidate_id",
        "derived_seed",
        "presented_to_canonical_map",
        "oracle",
        "headroom",
        "future_returns",
    ):
        assert forbidden not in rendered
    assert set(payload) == {"schema_version", "candidates"}


def test_trigger_false_is_first_class_no_call_with_zero_delta() -> None:
    vector = next(value for value in _vectors()["vectors"] if not value["trigger"]["triggered"])
    episode = _episode_for_vector(vector)
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id="r02-d2a-no-call",
        provider_attempt_count=7,
    )
    assert preparation.state is R02PreparationState.NO_CALL_TERMINAL
    assert preparation.candidate_set is None
    assert preparation.permutation is None
    assert preparation.no_call is not None
    assert preparation.no_call.reason_code is R02NoCallReason.TRIGGER_FALSE
    assert preparation.no_call.provider_attempts_before == 7
    assert preparation.no_call.provider_attempts_after == 7
    assert preparation.episode_result is not None
    assert preparation.episode_result.paired_utility_delta_e12 == 0
    assert preparation.provider_calls == 0


def test_trigger_true_stops_at_selector_eligible_without_call_artifacts() -> None:
    vector = next(value for value in _vectors()["vectors"] if value["trigger"]["triggered"])
    preparation = prepare_provider_free_episode(
        _episode_for_vector(vector),
        experiment_id="r02-d2a-eligible",
    )
    assert preparation.state is R02PreparationState.SELECTOR_ELIGIBLE_NOT_CALLED
    assert preparation.candidate_set is not None
    assert len(preparation.candidate_set.candidates) >= 2
    assert preparation.permutation is not None
    assert preparation.no_call is None
    assert preparation.execution_decision is None
    assert preparation.episode_result is None
    assert preparation.provider_calls == 0


def test_raw_invalid_candidate_becomes_typed_integrity_no_call(monkeypatch) -> None:
    vector = next(value for value in _vectors()["vectors"] if value["trigger"]["triggered"])
    episode = _episode_for_vector(vector)
    original = r02_candidates._raw_candidate_batches

    def invalid_raw(public, baseline, ledger):
        raw = list(original(public, baseline, ledger))
        role, candidate = raw[2]
        decisions = dict(candidate.decisions)
        asset_id = next(
            asset.asset_id for asset in public.assets if asset.lot_size_shares > 1
        )
        decisions[asset_id] = R02CandidateDecision(action="buy", quantity=1)
        raw[2] = (role, R02CandidateBatch(decisions=decisions))
        return tuple(raw)

    monkeypatch.setattr(r02_candidates, "_raw_candidate_batches", invalid_raw)
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id="r02-d2a-integrity-stop",
        provider_attempt_count=3,
    )
    assert preparation.no_call is not None
    assert preparation.no_call.reason_code is R02NoCallReason.PRE_PROVIDER_INTEGRITY_STOP
    assert preparation.no_call.integrity_error_codes
    assert preparation.no_call.provider_attempts_before == 3
    assert preparation.no_call.provider_attempts_after == 3
    assert preparation.candidate_set is None


def test_freeze_hash_drift_fails_closed(tmp_path) -> None:
    path = tmp_path / "freeze.json"
    path.write_bytes(r02_candidates.DEFAULT_R02_FREEZE_PATH.read_bytes() + b"\n")
    with pytest.raises(R02IntegrityError, match="FREEZE_SPEC_SHA256_MISMATCH"):
        verify_freeze_spec(path)
    assert R02_FREEZE_SHA256 not in path.read_text(encoding="utf-8")


def test_role_order_is_exactly_the_frozen_order() -> None:
    assert tuple(role.value for role in r02_candidates.R02_ROLE_ORDER) == (
        "BASELINE",
        "NO_CHANGE",
        "HALF_BASELINE_DELTA",
        "DROP_MAX_COST_TRADE",
    )
    assert R02CandidateRole.BASELINE.value == "BASELINE"
