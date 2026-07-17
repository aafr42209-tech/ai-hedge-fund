"""Scripted-only R02 D2b selector boundary, acceptance gate, and scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from .baselines import primary_deterministic
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .contracts import (
    ASSET_IDS,
    Decision,
    DecisionBatch,
    PolicyResult,
    SyntheticEpisode,
    ValidationReport,
)
from .r02_candidates import canonical_candidate_id, selector_safe_payload
from .r02_contracts import (
    R02AcceptanceGate,
    R02AcceptanceStatus,
    R02BaselineFallbackRecord,
    R02CandidateBatch,
    R02CandidateDecision,
    R02FallbackReason,
    R02ModelIdentityEvidence,
    R02PreparationState,
    R02ProviderFreePreparation,
    R02ScriptedCommandSpec,
    R02ScriptedExchange,
    R02ScriptedTransportRecord,
    R02SelectionRun,
    R02SelectorPromptDraft,
    R02SelectorReasonCode,
    R02SelectorRequest,
    R02SelectorResponsePayload,
    R02SelectorResponseRecord,
    R02SelectorResponseStatus,
    R02SelectorSafePayload,
    R02SelectorTokenLedger,
    R02TriggeredEpisodeResult,
    R02TriggeredExecutionDecision,
)
from .scoring import score_episode
from .validator import validate_batch


class R02SelectorBoundaryError(RuntimeError):
    pass


class R02SelectorParseError(ValueError):
    def __init__(self, *codes: str) -> None:
        self.codes = tuple(dict.fromkeys(code for code in codes if code)) or (
            "SELECTOR_RESPONSE_INVALID",
        )
        super().__init__(";".join(self.codes))


def _selector_runtime_source_sha256() -> str:
    return sha256_hex(Path(__file__).read_bytes())


def _candidate_from_validation(validation: ValidationReport) -> R02CandidateBatch:
    return R02CandidateBatch(
        decisions={
            asset_id: R02CandidateDecision(
                action=validation.executable.decisions[asset_id].action,
                quantity=validation.executable.decisions[asset_id].quantity,
            )
            for asset_id in ASSET_IDS
        }
    )


def _validation_batch(candidate: R02CandidateBatch) -> DecisionBatch:
    return DecisionBatch(
        decisions={
            asset_id: Decision(
                action=candidate.decisions[asset_id].action,
                quantity=candidate.decisions[asset_id].quantity,
                confidence=100,
                reasoning="r02:acceptance-gate",
            )
            for asset_id in ASSET_IDS
        }
    )


def _semantic_validation_matches(candidate: R02CandidateBatch, validation) -> bool:
    return all(
        candidate.decisions[asset_id].action
        == validation.executable.decisions[asset_id].action
        and candidate.decisions[asset_id].quantity
        == validation.executable.decisions[asset_id].quantity
        for asset_id in ASSET_IDS
    )


def build_selector_request(
    preparation: R02ProviderFreePreparation,
) -> R02SelectorRequest:
    if preparation.state is not R02PreparationState.SELECTOR_ELIGIBLE_NOT_CALLED:
        raise R02SelectorBoundaryError("selector request requires an eligible D2a preparation")
    if preparation.permutation is None:
        raise R02SelectorBoundaryError("eligible preparation is missing its permutation")
    payload = R02SelectorSafePayload.model_validate_json(
        canonical_json_bytes(selector_safe_payload(preparation.permutation))
    )
    payload_json = canonical_json_bytes(payload).decode("utf-8")
    allowed_reasons = ",".join(reason.value for reason in R02SelectorReasonCode)
    system_prompt = (
        "You are a constrained portfolio candidate selector. Compare only the "
        "opaque presented candidates supplied by the user. Return one strict JSON object."
    )
    user_prompt = (
        "Select exactly one presented candidate. Return keys schema_version, "
        "selected_candidate_id, confidence, and reason_codes only. confidence must be "
        "a JSON integer from 0 through 100. reason_codes must contain one to three "
        f"unique values from [{allowed_reasons}]. Candidate payload:\n{payload_json}"
    )
    prompt = R02SelectorPromptDraft(
        selector_payload_sha256=canonical_sha256(payload),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    command_spec = R02ScriptedCommandSpec(
        selector_runtime_source_sha256=_selector_runtime_source_sha256(),
    )
    return R02SelectorRequest(
        identity=preparation.identity,
        candidate_permutation_sha256=canonical_sha256(preparation.permutation),
        selector_payload=payload,
        prompt=prompt,
        command_spec=command_spec,
    )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise R02SelectorParseError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise R02SelectorParseError(f"NONFINITE_JSON_CONSTANT:{value}")


def parse_selector_response(raw_response: str) -> R02SelectorResponsePayload:
    if not isinstance(raw_response, str):
        raise R02SelectorParseError("RESPONSE_NOT_TEXT")
    if not raw_response.strip():
        raise R02SelectorParseError("EMPTY_RESPONSE")
    try:
        parsed = json.loads(
            raw_response,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except R02SelectorParseError:
        raise
    except json.JSONDecodeError as exc:
        raise R02SelectorParseError("INVALID_JSON") from exc
    if not isinstance(parsed, dict):
        raise R02SelectorParseError("TOP_LEVEL_NOT_OBJECT")
    try:
        return R02SelectorResponsePayload.model_validate_json(raw_response)
    except ValidationError as exc:
        codes = tuple(
            f"SCHEMA:{'.'.join(str(part) for part in error['loc'])}:{error['type']}"
            for error in exc.errors()
        )
        raise R02SelectorParseError(*codes) from exc


class ScriptedR02SelectorClient:
    """Deterministic test transport. It has no network or provider implementation."""

    def __init__(
        self,
        exchanges: tuple[R02ScriptedExchange, ...],
        *,
        initial_attempt_count: int = 0,
    ) -> None:
        if initial_attempt_count < 0:
            raise ValueError("initial attempt count must be nonnegative")
        self._exchanges = exchanges
        self._index = 0
        self._attempt_count = initial_attempt_count

    @property
    def attempt_count(self) -> int:
        return self._attempt_count

    def select(
        self,
        request: R02SelectorRequest,
    ) -> tuple[str, R02SelectorTokenLedger, R02ScriptedTransportRecord]:
        if self._index >= len(self._exchanges):
            raise R02SelectorBoundaryError("scripted selector exchange exhausted")
        if (
            request.command_spec.selector_runtime_source_sha256
            != _selector_runtime_source_sha256()
        ):
            raise R02SelectorBoundaryError("selector runtime source identity drift")
        exchange = self._exchanges[self._index]
        self._index += 1
        before = self._attempt_count
        self._attempt_count += 1
        ledger = R02SelectorTokenLedger(
            identity=request.identity,
            scripted_attempt_ordinal=self._attempt_count,
            scripted_attempts_before=before,
            scripted_attempts_after=self._attempt_count,
            input_tokens=exchange.input_tokens,
            cached_input_tokens=exchange.cached_input_tokens,
            output_tokens=exchange.output_tokens,
            reasoning_output_tokens=exchange.reasoning_output_tokens,
            accounting_total_tokens=exchange.input_tokens + exchange.output_tokens,
        )
        raw_response_sha256 = sha256_hex(exchange.raw_response.encode("utf-8"))
        transport = R02ScriptedTransportRecord(
            identity=request.identity,
            selector_request_sha256=canonical_sha256(request),
            command_spec_sha256=canonical_sha256(request.command_spec),
            token_ledger_sha256=canonical_sha256(ledger),
            raw_response_sha256=raw_response_sha256,
        )
        return exchange.raw_response, ledger, transport


def run_scripted_selector_episode(
    episode: SyntheticEpisode,
    preparation: R02ProviderFreePreparation,
    client: ScriptedR02SelectorClient,
    *,
    baseline_factory: Callable[[SyntheticEpisode], PolicyResult] = primary_deterministic,
) -> R02SelectionRun:
    if episode.public.case_id != preparation.identity.fixture_id:
        raise R02SelectorBoundaryError("selector fixture ID mismatch")
    if episode.content_sha256 != preparation.identity.fixture_content_sha256:
        raise R02SelectorBoundaryError("selector fixture content hash mismatch")
    if client.attempt_count != preparation.provider_attempt_count:
        raise R02SelectorBoundaryError("selector attempt counter does not continue preparation")
    if preparation.candidate_set is None or preparation.permutation is None:
        raise R02SelectorBoundaryError("selector preparation is incomplete")

    request = build_selector_request(preparation)
    raw_response, token_ledger, transport = client.select(request)
    raw_response_sha256 = sha256_hex(raw_response.encode("utf-8"))
    command_spec_sha256 = canonical_sha256(request.command_spec)
    model_identity = R02ModelIdentityEvidence(
        command_spec_sha256=command_spec_sha256,
        selector_runtime_source_sha256=_selector_runtime_source_sha256(),
    )
    parsed_response: R02SelectorResponsePayload | None
    response_errors: tuple[str, ...]
    try:
        parsed_response = parse_selector_response(raw_response)
        response_errors = ()
        response_status = R02SelectorResponseStatus.VALID
    except R02SelectorParseError as exc:
        parsed_response = None
        response_errors = exc.codes
        response_status = R02SelectorResponseStatus.INVALID
    response = R02SelectorResponseRecord(
        identity=preparation.identity,
        selector_request_sha256=canonical_sha256(request),
        scripted_transport_sha256=canonical_sha256(transport),
        raw_response_sha256=raw_response_sha256,
        status=response_status,
        parsed_response=parsed_response,
        validation_error_codes=response_errors,
        model_identity_evidence=model_identity,
    )

    selected_presented_id = (
        parsed_response.selected_candidate_id if parsed_response is not None else None
    )
    selected_canonical_id = (
        preparation.permutation.presented_to_canonical_map.get(selected_presented_id)
        if selected_presented_id is not None
        else None
    )
    selected_candidate = next(
        (
            candidate
            for candidate in preparation.candidate_set.candidates
            if candidate.canonical_candidate_id == selected_canonical_id
        ),
        None,
    )
    selected_validation = None
    fallback_reason: R02FallbackReason | None = None
    acceptance_errors: tuple[str, ...] = ()
    if parsed_response is None:
        fallback_reason = R02FallbackReason.SELECTOR_SCHEMA_INVALID
        acceptance_errors = response_errors
    elif selected_canonical_id is None or selected_candidate is None:
        fallback_reason = R02FallbackReason.UNKNOWN_PRESENTED_ID
        acceptance_errors = ("UNKNOWN_PRESENTED_ID",)
    else:
        selected_validation = validate_batch(
            episode.public,
            _validation_batch(selected_candidate.candidate),
        )
        semantic_match = _semantic_validation_matches(
            selected_candidate.candidate,
            selected_validation,
        )
        if (
            not selected_validation.raw_valid
            or selected_validation.fell_back
            or not semantic_match
        ):
            fallback_reason = R02FallbackReason.ACCEPTANCE_VALIDATION_FAILED
            acceptance_errors = tuple(
                dict.fromkeys(
                    (
                        *(
                            f"VALIDATION:{violation.code}"
                            for violation in selected_validation.violations
                        ),
                        *(('EXECUTABLE_MISMATCH',) if not semantic_match else ()),
                    )
                )
            ) or ("ACCEPTANCE_VALIDATION_FAILED",)

    acceptance_status = (
        R02AcceptanceStatus.ACCEPTED
        if fallback_reason is None
        else R02AcceptanceStatus.REJECTED
    )
    acceptance = R02AcceptanceGate(
        identity=preparation.identity,
        selector_request_sha256=canonical_sha256(request),
        selector_response_sha256=canonical_sha256(response),
        candidate_set_sha256=canonical_sha256(preparation.candidate_set),
        status=acceptance_status,
        selected_presented_id=selected_presented_id,
        selected_canonical_id=selected_canonical_id,
        validation_report=selected_validation,
        validation_report_sha256=(
            canonical_sha256(selected_validation)
            if selected_validation is not None
            else None
        ),
        error_codes=acceptance_errors,
    )

    baseline = baseline_factory(episode)
    if not baseline.validation.raw_valid or baseline.validation.fell_back:
        raise R02SelectorBoundaryError("primary baseline is not executable")
    baseline_batch = _candidate_from_validation(baseline.validation)
    baseline_id = canonical_candidate_id(baseline_batch)
    if baseline_id != preparation.candidate_set.baseline_canonical_candidate_id:
        raise R02SelectorBoundaryError("primary baseline identity drift")

    fallback = None
    if fallback_reason is not None:
        executed_batch = baseline_batch
        executed_validation = baseline.validation
        executed_id = baseline_id
        fallback = R02BaselineFallbackRecord(
            identity=preparation.identity,
            acceptance_gate_sha256=canonical_sha256(acceptance),
            reason_code=fallback_reason,
            selected_presented_id=selected_presented_id,
            selected_canonical_id=selected_canonical_id,
            baseline_canonical_candidate_id=baseline_id,
            baseline_batch=baseline_batch,
        )
        disposition = "BASELINE_FALLBACK"
    else:
        assert selected_candidate is not None
        assert selected_validation is not None
        executed_batch = selected_candidate.candidate
        executed_validation = selected_validation
        executed_id = selected_candidate.canonical_candidate_id
        disposition = "SELECTED_CANDIDATE_ACCEPTED"
    execution = R02TriggeredExecutionDecision(
        identity=preparation.identity,
        acceptance_gate_sha256=canonical_sha256(acceptance),
        selected_presented_id=selected_presented_id,
        selected_canonical_id=selected_canonical_id,
        executed_canonical_id=executed_id,
        acceptance_disposition=disposition,
        baseline_fallback=fallback_reason is not None,
        executable_batch=executed_batch,
        validation_report=executed_validation,
    )
    executed_score = score_episode(episode, executed_validation)
    result = R02TriggeredEpisodeResult(
        identity=preparation.identity,
        execution_decision_sha256=canonical_sha256(execution),
        baseline_score=baseline.score,
        executed_score=executed_score,
        paired_utility_delta_e12=(
            executed_score.utility_e12 - baseline.score.utility_e12
        ),
        scripted_attempt_count=token_ledger.scripted_attempts_after,
    )
    return R02SelectionRun(
        identity=preparation.identity,
        preparation=preparation,
        selector_request=request,
        raw_response=raw_response,
        token_ledger=token_ledger,
        scripted_transport=transport,
        selector_response=response,
        acceptance_gate=acceptance,
        baseline_fallback=fallback,
        execution_decision=execution,
        episode_result=result,
    )
