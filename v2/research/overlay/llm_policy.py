"""Provider-free policy prompt, scripted acquisition, and fail-closed parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .canonical import DecisionParseError, canonical_sha256, parse_decision_batch, sha256_hex
from .contracts import (
    AcquisitionIdentity,
    DecisionBatch,
    MAX_REASONING_CODEPOINTS,
    ProviderResponse,
    CodexProcessStatus,
    PublicEpisode,
    ValidationReport,
)
from .perturbations import identity_permutation, present_episode, render_presented_json
from .validator import validate_batch

SYSTEM_PROMPT_V1 = f"""You are the portfolio decision policy in a synthetic research fixture.
Return one JSON object matching the required schema. Do not omit or add assets.
Optimize only from the supplied anonymous numeric inputs and constraints.
Quantity is an integer number of shares, must be an exact visible-lot multiple,
and may not exceed two lots per asset. Reasoning for each asset must not exceed
{MAX_REASONING_CODEPOINTS} Unicode code points. Never use external facts or real markets."""


@runtime_checkable
class AcquisitionClient(Protocol):
    provider_calls: int

    def complete(
        self,
        *,
        system: str,
        user: str,
        identity: AcquisitionIdentity,
    ) -> ProviderResponse:
        ...


def acquisition_key(identity: AcquisitionIdentity) -> str:
    return canonical_sha256(identity)


class ScriptedAcquisitionClient:
    """Only Phase A client: returns pre-supplied text and never uses a network."""

    def __init__(self, responses: dict[str, ProviderResponse | str]) -> None:
        self._responses = responses
        self.provider_calls = 0

    def complete(
        self,
        *,
        system: str,
        user: str,
        identity: AcquisitionIdentity,
    ) -> ProviderResponse:
        del system, user
        self.provider_calls += 1
        key = acquisition_key(identity)
        if key not in self._responses:
            raise KeyError(f"no scripted response for acquisition {key}")
        response = self._responses[key]
        if isinstance(response, ProviderResponse):
            return response
        return ProviderResponse(
            raw_text=response,
            provider="scripted",
            model_id="scripted-v1",
            request_id=key,
            input_tokens=0,
            cached_input_tokens=0,
            output_tokens=0,
            reasoning_output_tokens=0,
            model_identity_verified_by_transport=True,
            model_identity_evidence="matching_transport_echo",
            transport_model_echoes=("scripted-v1",),
            tool_use_violation=False,
            process_status_violation=False,
            event_types=("scripted.response",),
            agent_message_count=1,
            transport_sha256=sha256_hex(response.encode("utf-8")),
            observed_transport_shape_sha256=canonical_sha256(
                {
                    "schema_version": "r01-scripted-transport-shape-v1",
                    "event_types": ["scripted.response"],
                }
            ),
            process_status=CodexProcessStatus(
                exit_code=0,
                timed_out=False,
                duration_ms=0,
                stdout_sha256=sha256_hex(response.encode("utf-8")),
                stdout_size_bytes=len(response.encode("utf-8")),
                stderr_sha256=sha256_hex(b""),
                stderr_size_bytes=0,
            ),
        )


def build_policy_input(public: PublicEpisode) -> dict[str, object]:
    return present_episode(public, identity_permutation())


def build_user_prompt(public: PublicEpisode, presented_json: str | None = None) -> str:
    payload = presented_json or render_presented_json(build_policy_input(public))
    return "Choose buy, sell, or hold for every A0-A5 asset. " "Quantity is shares, must be a lot-size multiple, and is capped at two lots. " "All six decisions are validated jointly; any violation makes the full batch hold.\n" 'Return: {"decisions":{"A0":{"action":"hold","quantity":0,' '"confidence":0,"reasoning":"short text"},...}}\n' f"FIXTURE={payload}"


@dataclass(frozen=True)
class ParsedPolicyOutcome:
    parsed_batch: DecisionBatch | None
    parsed_artifact: dict[str, object]
    validation: ValidationReport


def parse_and_validate(public: PublicEpisode, raw_text: str) -> ParsedPolicyOutcome:
    try:
        batch = parse_decision_batch(raw_text)
    except DecisionParseError as exc:
        validation = validate_batch(public, {})
        return ParsedPolicyOutcome(
            parsed_batch=None,
            parsed_artifact={"parse_error": str(exc)},
            validation=validation,
        )
    return ParsedPolicyOutcome(
        parsed_batch=batch,
        parsed_artifact=batch.model_dump(mode="python"),
        validation=validate_batch(public, batch),
    )
