"""Frozen R02 D2a trigger, candidate generation, and provider-free preparation."""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Callable

from .baselines import primary_deterministic
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .contracts import (
    ASSET_IDS,
    CostLedger,
    Decision,
    DecisionBatch,
    EpisodeScore,
    PolicyResult,
    PublicEpisode,
    SyntheticEpisode,
    ValidationReport,
)
from .r02_contracts import (
    R02CandidateBatch,
    R02CandidateDecision,
    R02CandidatePermutation,
    R02CandidateRole,
    R02CandidateSet,
    R02CanonicalCandidate,
    R02EligibilityDecision,
    R02EpisodeResult,
    R02ExecutionDecision,
    R02Identity,
    R02NoCallReason,
    R02NoCallRecord,
    R02PreparationState,
    R02PresentedCandidate,
    R02ProviderFreePreparation,
    R02RawCandidateAudit,
    R02TriggerCostLine,
    R02TriggerDecision,
    R02TriggerInput,
    R02_ACCEPTED_COMMIT,
    R02_FREEZE_SHA256,
    R02_MANIFEST_SHA256,
    R02_ROLE_ORDER,
    R02_ROOT_SEED,
    R02_SEED_LABEL,
)
from .validator import validate_batch

DEFAULT_R02_FREEZE_PATH = Path(__file__).resolve().parents[3] / "docs" / "r02-d1-candidate-trigger-freeze.json"


class R02IntegrityError(RuntimeError):
    def __init__(self, *codes: str) -> None:
        normalized = tuple(code for code in codes if code)
        if not normalized:
            normalized = ("UNSPECIFIED_R02_INTEGRITY_ERROR",)
        self.codes = normalized
        super().__init__(";".join(normalized))


def verify_freeze_spec(path: str | Path = DEFAULT_R02_FREEZE_PATH) -> dict[str, object]:
    freeze_path = Path(path)
    content = freeze_path.read_bytes()
    if sha256_hex(content) != R02_FREEZE_SHA256:
        raise R02IntegrityError("FREEZE_SPEC_SHA256_MISMATCH")
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise R02IntegrityError("FREEZE_SPEC_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise R02IntegrityError("FREEZE_SPEC_NOT_OBJECT")
    return value


def _candidate_payload(batch: R02CandidateBatch) -> dict[str, object]:
    return {
        "schema_version": batch.schema_version,
        "decisions": {
            asset_id: {
                "action": batch.decisions[asset_id].action,
                "quantity": batch.decisions[asset_id].quantity,
            }
            for asset_id in ASSET_IDS
        },
    }


def canonical_candidate_bytes(batch: R02CandidateBatch) -> bytes:
    return json.dumps(
        _candidate_payload(batch),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_candidate_id(batch: R02CandidateBatch) -> str:
    return sha256_hex(canonical_candidate_bytes(batch))


def _candidate_from_decisions(decisions: dict[str, Decision]) -> R02CandidateBatch:
    return R02CandidateBatch(
        decisions={
            asset_id: R02CandidateDecision(
                action=decisions[asset_id].action,
                quantity=decisions[asset_id].quantity,
            )
            for asset_id in ASSET_IDS
        }
    )


def _validation_batch(candidate: R02CandidateBatch, role: R02CandidateRole) -> DecisionBatch:
    return DecisionBatch(
        decisions={
            asset_id: Decision(
                action=candidate.decisions[asset_id].action,
                quantity=candidate.decisions[asset_id].quantity,
                confidence=100,
                reasoning=f"r02:{role.value}",
            )
            for asset_id in ASSET_IDS
        }
    )


def _semantic_executable_matches(candidate: R02CandidateBatch, validation_batch: DecisionBatch) -> bool:
    return all(
        candidate.decisions[asset_id].action == validation_batch.decisions[asset_id].action
        and candidate.decisions[asset_id].quantity == validation_batch.decisions[asset_id].quantity
        for asset_id in ASSET_IDS
    )


def _baseline_candidate(validation: ValidationReport) -> R02CandidateBatch:
    if not validation.raw_valid or validation.fell_back:
        raise R02IntegrityError("PRIMARY_BASELINE_NOT_RAW_VALID")
    return _candidate_from_decisions(validation.executable.decisions)


def evaluate_trigger(
    cost_ledger: CostLedger,
    baseline_candidate: R02CandidateBatch,
) -> tuple[R02TriggerInput, R02TriggerDecision]:
    lines = tuple(
        R02TriggerCostLine(
            asset_id=line.asset_id,
            notional_cents=line.notional_cents,
            total_cost_cents=line.total_cost_cents,
            effective_cost_bps=(line.total_cost_cents * 10_000 + line.notional_cents - 1) // line.notional_cents,
        )
        for line in sorted(cost_ledger.lines, key=lambda item: item.asset_id)
    )
    trigger_input = R02TriggerInput(
        baseline_canonical_candidate_id=canonical_candidate_id(baseline_candidate),
        cost_lines=lines,
    )
    maximum = max((line.effective_cost_bps for line in lines), default=0)
    triggered = bool(lines) and maximum >= 50
    reason = (
        "MAX_TRADED_EFFECTIVE_COST_BPS_GE_50"
        if triggered
        else "MAX_TRADED_EFFECTIVE_COST_BPS_LT_50_OR_NO_TRADE"
    )
    return trigger_input, R02TriggerDecision(
        trade_count=len(lines),
        max_traded_effective_cost_bps=maximum,
        triggered=triggered,
        reason_codes=(reason,),
    )


def _raw_candidate_batches(
    public: PublicEpisode,
    baseline: R02CandidateBatch,
    cost_ledger: CostLedger,
) -> tuple[tuple[R02CandidateRole, R02CandidateBatch], ...]:
    no_change = R02CandidateBatch(
        decisions={
            asset_id: R02CandidateDecision(action="hold", quantity=0) for asset_id in ASSET_IDS
        }
    )

    half_decisions: dict[str, R02CandidateDecision] = {}
    for asset_id in ASSET_IDS:
        decision = baseline.decisions[asset_id]
        if decision.action == "hold":
            half_decisions[asset_id] = R02CandidateDecision(action="hold", quantity=0)
            continue
        lot_size = public.assets_by_id[asset_id].lot_size_shares
        if decision.quantity % lot_size:
            raise R02IntegrityError(f"BASELINE_NON_INTEGER_LOT:{asset_id}")
        scaled_lots = (decision.quantity // lot_size) // 2
        half_decisions[asset_id] = (
            R02CandidateDecision(action=decision.action, quantity=scaled_lots * lot_size)
            if scaled_lots > 0
            else R02CandidateDecision(action="hold", quantity=0)
        )
    half = R02CandidateBatch(decisions=half_decisions)

    drop_decisions = dict(baseline.decisions)
    if cost_ledger.lines:
        drop_line = min(cost_ledger.lines, key=lambda item: (-item.total_cost_cents, item.asset_id))
        drop_decisions[drop_line.asset_id] = R02CandidateDecision(action="hold", quantity=0)
    drop = R02CandidateBatch(decisions=drop_decisions)

    return (
        (R02CandidateRole.BASELINE, baseline),
        (R02CandidateRole.NO_CHANGE, no_change),
        (R02CandidateRole.HALF_BASELINE_DELTA, half),
        (R02CandidateRole.DROP_MAX_COST_TRADE, drop),
    )


def _generator_source_sha256() -> str:
    return sha256_hex(Path(__file__).read_bytes())


def _generator_config_sha256(freeze: dict[str, object]) -> str:
    required = (
        "candidate_generator",
        "candidate_canonicalization",
        "presentation_permutation",
    )
    try:
        payload = {key: freeze[key] for key in required}
    except KeyError as exc:
        raise R02IntegrityError(f"FREEZE_CONFIG_MISSING:{exc.args[0]}") from exc
    return canonical_sha256(payload)


def build_candidate_set(
    public: PublicEpisode,
    baseline_validation: ValidationReport,
    eligibility: R02EligibilityDecision,
    freeze: dict[str, object],
) -> R02CandidateSet:
    baseline_candidate = _baseline_candidate(baseline_validation)
    raw_records: list[R02RawCandidateAudit] = []
    validated: list[tuple[R02CandidateRole, R02CandidateBatch, str]] = []
    for role, candidate in _raw_candidate_batches(
        public,
        baseline_candidate,
        baseline_validation.cost_ledger,
    ):
        validation = validate_batch(public, _validation_batch(candidate, role))
        if not validation.raw_valid:
            codes = tuple(f"RAW_INVALID:{role.value}:{item.code}" for item in validation.violations)
            raise R02IntegrityError(*(codes or (f"RAW_INVALID:{role.value}",)))
        if validation.fell_back:
            raise R02IntegrityError(f"RAW_FELL_BACK:{role.value}")
        executable_matches = _semantic_executable_matches(
            candidate,
            DecisionBatch(decisions=validation.executable.decisions),
        )
        if not executable_matches:
            raise R02IntegrityError(f"EXECUTABLE_MISMATCH:{role.value}")
        candidate_id = canonical_candidate_id(candidate)
        validation_sha256 = canonical_sha256(validation)
        raw_records.append(
            R02RawCandidateAudit(
                role=role,
                candidate=candidate,
                canonical_candidate_id=candidate_id,
                validation_report=validation,
                validation_report_sha256=validation_sha256,
            )
        )
        validated.append((role, candidate, candidate_id))

    by_id: dict[str, R02CanonicalCandidate] = {}
    order: list[str] = []
    for role, candidate, candidate_id in validated:
        if candidate_id not in by_id:
            by_id[candidate_id] = R02CanonicalCandidate(
                primary_role=role,
                canonical_candidate_id=candidate_id,
                candidate=candidate,
            )
            order.append(candidate_id)
        else:
            current = by_id[candidate_id]
            by_id[candidate_id] = current.model_copy(
                update={"aliases": (*current.aliases, role)}
            )
    candidates = tuple(by_id[candidate_id] for candidate_id in order)
    candidate_set_identity = canonical_sha256(
        tuple(candidate.model_dump(mode="python") for candidate in candidates)
    )
    return R02CandidateSet(
        identity=eligibility.identity,
        eligibility_decision_sha256=canonical_sha256(eligibility),
        generator_source_sha256=_generator_source_sha256(),
        generator_config_sha256=_generator_config_sha256(freeze),
        baseline_canonical_candidate_id=canonical_candidate_id(baseline_candidate),
        raw_candidates=tuple(raw_records),
        candidates=candidates,
        canonical_candidate_set_sha256=candidate_set_identity,
    )


def build_candidate_permutation(
    candidate_set: R02CandidateSet,
    fixture_content_sha256: str,
    overlay_spec_sha256: str = R02_FREEZE_SHA256,
) -> R02CandidatePermutation:
    seed_message = (
        R02_SEED_LABEL
        + b"\x00"
        + fixture_content_sha256.encode("ascii")
        + b"\x00"
        + overlay_spec_sha256.encode("ascii")
    )
    derived_seed = hmac.new(R02_ROOT_SEED, seed_message, hashlib.sha256).digest()
    original = tuple(candidate.canonical_candidate_id for candidate in candidate_set.candidates)
    keyed = sorted(
        (
            hmac.new(derived_seed, candidate_id.encode("ascii"), hashlib.sha256).hexdigest(),
            candidate_id,
        )
        for candidate_id in original
    )
    presented_order = tuple(candidate_id for _key, candidate_id in keyed)
    presented_map = {
        f"P{index:02d}": candidate_id for index, candidate_id in enumerate(presented_order)
    }
    candidates_by_id = {
        candidate.canonical_candidate_id: candidate.candidate
        for candidate in candidate_set.candidates
    }
    presented_candidates = tuple(
        R02PresentedCandidate(
            presented_id=presented_id,
            candidate=candidates_by_id[candidate_id],
        )
        for presented_id, candidate_id in presented_map.items()
    )
    permutation_identity = canonical_sha256(
        {
            "seed_label": R02_SEED_LABEL.decode("ascii"),
            "seed_input_sha256": sha256_hex(seed_message),
            "derived_seed_hex": derived_seed.hex(),
            "original_canonical_order": original,
            "presented_order": presented_order,
            "presented_to_canonical_map": presented_map,
        }
    )
    return R02CandidatePermutation(
        identity=candidate_set.identity,
        candidate_set_sha256=canonical_sha256(candidate_set),
        seed_input_sha256=sha256_hex(seed_message),
        derived_seed_hex=derived_seed.hex(),
        original_canonical_order=original,
        presented_order=presented_order,
        presented_to_canonical_map=presented_map,
        presented_candidates=presented_candidates,
        permutation_sha256=permutation_identity,
    )


def selector_safe_payload(permutation: R02CandidatePermutation) -> dict[str, object]:
    """Return the only candidate fields allowed to cross a future selector boundary."""

    return {
        "schema_version": "r02-selector-input-v1",
        "candidates": [
            item.model_dump(mode="python") for item in permutation.presented_candidates
        ],
    }


def _terminal_no_call(
    *,
    identity: R02Identity,
    eligibility: R02EligibilityDecision,
    baseline_score: EpisodeScore,
    baseline_candidate: R02CandidateBatch,
    provider_attempt_count: int,
    reason: R02NoCallReason,
    candidate_set: R02CandidateSet | None = None,
    integrity_error_codes: tuple[str, ...] = (),
) -> R02ProviderFreePreparation:
    eligibility_sha256 = canonical_sha256(eligibility)
    candidate_set_sha256 = canonical_sha256(candidate_set) if candidate_set is not None else None
    baseline_id = canonical_candidate_id(baseline_candidate)
    no_call = R02NoCallRecord(
        identity=identity,
        eligibility_decision_sha256=eligibility_sha256,
        candidate_set_sha256=candidate_set_sha256,
        reason_code=reason,
        provider_attempts_before=provider_attempt_count,
        provider_attempts_after=provider_attempt_count,
        baseline_canonical_candidate_id=baseline_id,
        executed_canonical_candidate_id=baseline_id,
        baseline_batch=baseline_candidate,
        executed_batch=baseline_candidate,
        integrity_error_codes=integrity_error_codes,
    )
    execution = R02ExecutionDecision(
        identity=identity,
        eligibility_decision_sha256=eligibility_sha256,
        candidate_set_sha256=candidate_set_sha256,
        executed_canonical_id=baseline_id,
        executable_batch=baseline_candidate,
    )
    result = R02EpisodeResult(
        identity=identity,
        execution_decision_sha256=canonical_sha256(execution),
        baseline_score=baseline_score,
        executed_score=baseline_score,
        provider_attempt_count=provider_attempt_count,
    )
    return R02ProviderFreePreparation(
        identity=identity,
        provider_attempt_count=provider_attempt_count,
        state=R02PreparationState.NO_CALL_TERMINAL,
        eligibility=eligibility,
        candidate_set=candidate_set,
        no_call=no_call,
        execution_decision=execution,
        episode_result=result,
    )


def prepare_provider_free_episode(
    episode: SyntheticEpisode,
    *,
    experiment_id: str,
    replicate_id: int = 0,
    provider_attempt_count: int = 0,
    freeze_path: str | Path = DEFAULT_R02_FREEZE_PATH,
    baseline_factory: Callable[[SyntheticEpisode], PolicyResult] = primary_deterministic,
) -> R02ProviderFreePreparation:
    """Build the complete authorized D2a graph without a provider boundary."""

    freeze = verify_freeze_spec(freeze_path)
    baseline = baseline_factory(episode)
    baseline_validation = baseline.validation
    baseline_candidate = _baseline_candidate(baseline_validation)
    trigger_input, trigger = evaluate_trigger(
        baseline_validation.cost_ledger,
        baseline_candidate,
    )
    identity = R02Identity(
        experiment_id=experiment_id,
        fixture_id=episode.public.case_id,
        fixture_content_sha256=episode.content_sha256,
        replicate_id=replicate_id,
    )
    trigger_rule = freeze.get("trigger")
    if not isinstance(trigger_rule, dict):
        raise R02IntegrityError("FREEZE_TRIGGER_MISSING")
    eligibility = R02EligibilityDecision(
        identity=identity,
        public_fixture_sha256=canonical_sha256(episode.public),
        trigger_rule_sha256=canonical_sha256(trigger_rule),
        trigger_input_sha256=canonical_sha256(trigger_input),
        trigger_input=trigger_input,
        trigger=trigger,
    )
    if not trigger.triggered:
        return _terminal_no_call(
            identity=identity,
            eligibility=eligibility,
            baseline_score=baseline.score,
            baseline_candidate=baseline_candidate,
            provider_attempt_count=provider_attempt_count,
            reason=R02NoCallReason.TRIGGER_FALSE,
        )

    try:
        candidate_set = build_candidate_set(
            episode.public,
            baseline_validation,
            eligibility,
            freeze,
        )
    except R02IntegrityError as exc:
        return _terminal_no_call(
            identity=identity,
            eligibility=eligibility,
            baseline_score=baseline.score,
            baseline_candidate=baseline_candidate,
            provider_attempt_count=provider_attempt_count,
            reason=R02NoCallReason.PRE_PROVIDER_INTEGRITY_STOP,
            integrity_error_codes=exc.codes,
        )
    if len(candidate_set.candidates) == 1:
        return _terminal_no_call(
            identity=identity,
            eligibility=eligibility,
            baseline_score=baseline.score,
            baseline_candidate=baseline_candidate,
            provider_attempt_count=provider_attempt_count,
            reason=R02NoCallReason.CANDIDATE_COLLAPSE,
            candidate_set=candidate_set,
        )
    permutation = build_candidate_permutation(candidate_set, episode.content_sha256)
    return R02ProviderFreePreparation(
        identity=identity,
        accepted_commit=R02_ACCEPTED_COMMIT,
        freeze_spec_sha256=R02_FREEZE_SHA256,
        freeze_manifest_sha256=R02_MANIFEST_SHA256,
        provider_attempt_count=provider_attempt_count,
        state=R02PreparationState.SELECTOR_ELIGIBLE_NOT_CALLED,
        eligibility=eligibility,
        candidate_set=candidate_set,
        permutation=permutation,
    )
