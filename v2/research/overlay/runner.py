"""Provider-free Phase A orchestration and deterministic replay."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .artifacts import AppendOnlyArtifactStore
from .baselines import equal_risk_policy, hold_policy, primary_deterministic
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .codex_exec_client import CodexExecError, complete_response_disposition
from .contracts import (
    AcquisitionArtifacts,
    AcquisitionDisposition,
    AcquisitionFailureRecord,
    AcquisitionIdentity,
    ArtifactReference,
    CompleteResponseDispositionRecord,
    DevelopmentManifest,
    DevelopmentRunPlan,
    DevelopmentRunResult,
    EpisodeScore,
    FixtureManifestEntry,
    GeneratorConfig,
    normalize_artifact_relative_path,
    OracleResult,
    ProviderFreeFreeze,
    ProviderResponse,
    ReplayVerification,
    RunPlanEntry,
    SyntheticEpisode,
    ValidationReport,
)
from .fixtures import generate_development_episodes
from .freeze import (
    build_provider_free_freeze,
    generate_provider_free_freeze,
    load_committed_provider_free_freeze,
    load_committed_provider_free_regime_gap_summary,
    verify_frozen_development_identity,
)
from .lattice import hold_batch
from .llm_policy import (
    acquisition_key,
    AcquisitionClient,
    build_policy_input,
    build_user_prompt,
    fail_closed_outcome,
    parse_and_validate,
    ParsedPolicyOutcome,
    ScriptedAcquisitionClient,
    SYSTEM_PROMPT_V1,
)
from .oracle import assert_oracle_bound, solve_oracle
from .report import build_report
from .scoring import score_episode
from .specs import (
    analysis_spec,
    analysis_spec_sha256,
    scoring_spec,
    scoring_spec_sha256,
)

MAX_CONSECUTIVE_RETRY_TRANSPORT = 2
DEVELOPMENT_ATTEMPT_CAP = 200


def generate_development_manifest(
    store: AppendOnlyArtifactStore,
    *,
    experiment_id: str,
    root_seed: str,
    contract_bytes: bytes,
    expected_freeze_sha256: str,
    config: GeneratorConfig | None = None,
    count: int = 40,
) -> tuple[ArtifactReference, DevelopmentManifest]:
    config = config or GeneratorConfig()
    episodes = generate_development_episodes(config, root_seed, count)
    provider_free_freeze = build_provider_free_freeze(
        episodes,
        config=config,
        root_seed_label=root_seed,
    )
    if canonical_sha256(provider_free_freeze) != expected_freeze_sha256:
        raise RuntimeError("generated provider-free freeze differs from the external trust anchor")
    scoring_reference = store.write_json(f"{experiment_id}/scoring_spec.json", scoring_spec())
    analysis_reference = store.write_json(f"{experiment_id}/analysis_spec.json", analysis_spec())
    provider_free_freeze_reference = store.write_json(
        f"{experiment_id}/provider_free_freeze.json",
        provider_free_freeze,
    )
    entries: list[FixtureManifestEntry] = []
    for episode in episodes:
        reference = store.write_json(
            f"{experiment_id}/fixtures/{episode.public.case_id}.json",
            episode,
        )
        entries.append(
            FixtureManifestEntry(
                case_id=episode.public.case_id,
                regime=episode.hidden.regime,
                content_sha256=episode.content_sha256,
                fixture=reference,
            )
        )
    manifest = DevelopmentManifest(
        experiment_id=experiment_id,
        contract_sha256=sha256_hex(contract_bytes),
        generator_config_sha256=canonical_sha256(config),
        scoring_spec_sha256=scoring_spec_sha256(),
        analysis_spec_sha256=analysis_spec_sha256(),
        scoring_spec=scoring_reference,
        analysis_spec=analysis_reference,
        provider_free_freeze_sha256=provider_free_freeze_reference.sha256,
        provider_free_freeze=provider_free_freeze_reference,
        normalization_epsilon_e12=provider_free_freeze.normalization_epsilon_e12,
        regret_scale_e12=provider_free_freeze.regret_scale_e12,
        feasible_lattice_bound_certificate_sha256=(provider_free_freeze.feasible_lattice_bound_certificate_sha256),
        root_seed_sha256=sha256_hex(root_seed.encode("utf-8")),
        fixtures=tuple(entries),
    )
    reference = store.write_json(f"{experiment_id}/development_manifest.json", manifest)
    return reference, manifest


def _acquisition_prefix(identity: AcquisitionIdentity) -> str:
    discriminator = f"replicate-{identity.replicate_id:03d}" if identity.replicate_id is not None else f"perturbation-{identity.perturbation_id}"
    return f"{identity.experiment_id}/acquisitions/{identity.case_id}/" f"{identity.channel}/{discriminator}/attempt-{identity.attempt}"


def _load_episode(store: AppendOnlyArtifactStore, reference: ArtifactReference) -> SyntheticEpisode:
    episode = SyntheticEpisode.model_validate_json(store.read_bytes(reference))
    if canonical_sha256({"public": episode.public, "hidden": episode.hidden}) != episode.content_sha256:
        raise RuntimeError(f"fixture content hash mismatch: {episode.public.case_id}")
    return episode


def _verify_manifest_specs(
    store: AppendOnlyArtifactStore,
    manifest: DevelopmentManifest,
    *,
    expected_freeze_sha256: str,
) -> None:
    if manifest.provider_free_freeze_sha256 != expected_freeze_sha256:
        raise RuntimeError("provider-free freeze hash differs from the external trust anchor")
    store.verify(manifest.scoring_spec)
    store.verify(manifest.analysis_spec)
    store.verify(manifest.provider_free_freeze)
    if manifest.scoring_spec.sha256 != manifest.scoring_spec_sha256:
        raise RuntimeError("scoring spec hash mismatch")
    if manifest.analysis_spec.sha256 != manifest.analysis_spec_sha256:
        raise RuntimeError("analysis spec hash mismatch")
    if manifest.provider_free_freeze.sha256 != manifest.provider_free_freeze_sha256:
        raise RuntimeError("provider-free freeze hash mismatch")
    if manifest.scoring_spec_sha256 != scoring_spec_sha256():
        raise RuntimeError("runtime scoring spec differs from manifest")
    if manifest.analysis_spec_sha256 != analysis_spec_sha256():
        raise RuntimeError("runtime analysis spec differs from manifest")
    if store.read_bytes(manifest.scoring_spec) != canonical_json_bytes(scoring_spec()):
        raise RuntimeError("scoring spec bytes differ from runtime spec")
    if store.read_bytes(manifest.analysis_spec) != canonical_json_bytes(analysis_spec()):
        raise RuntimeError("analysis spec bytes differ from runtime spec")
    freeze = ProviderFreeFreeze.model_validate_json(store.read_bytes(manifest.provider_free_freeze))
    if freeze.generator_config_sha256 != manifest.generator_config_sha256:
        raise RuntimeError("provider-free freeze generator config mismatch")
    if freeze.scoring_spec_sha256 != manifest.scoring_spec_sha256:
        raise RuntimeError("provider-free freeze scoring spec mismatch")
    if freeze.root_seed_sha256 != manifest.root_seed_sha256:
        raise RuntimeError("provider-free freeze root seed mismatch")
    if freeze.normalization_epsilon_e12 != manifest.normalization_epsilon_e12:
        raise RuntimeError("provider-free freeze epsilon mismatch")
    if freeze.regret_scale_e12 != manifest.regret_scale_e12:
        raise RuntimeError("provider-free freeze regret scale mismatch")
    if freeze.feasible_lattice_bound_certificate_sha256 != manifest.feasible_lattice_bound_certificate_sha256:
        raise RuntimeError("provider-free freeze lattice certificate mismatch")
    freeze_cases = {(case.case_id, case.fixture_content_sha256) for case in freeze.cases}
    manifest_cases = {(case.case_id, case.content_sha256) for case in manifest.fixtures}
    if freeze.fixture_count != len(manifest.fixtures) or freeze_cases != manifest_cases:
        raise RuntimeError("provider-free freeze fixture identity mismatch")


@dataclass(frozen=True)
class _RequestArtifacts:
    user_prompt: str
    policy_input: ArtifactReference
    system_prompt: ArtifactReference
    user_prompt_artifact: ArtifactReference
    provider_request: ArtifactReference


@dataclass(frozen=True)
class _AcquisitionOutcome:
    artifacts: AcquisitionArtifacts
    disposition: CompleteResponseDispositionRecord
    validation: ValidationReport
    score: EpisodeScore


def _initial_attempt_identity(identity: AcquisitionIdentity) -> AcquisitionIdentity:
    return identity.model_copy(update={"attempt": 1})


def _failure_record(
    identity: AcquisitionIdentity,
    error: CodexExecError,
) -> AcquisitionFailureRecord:
    return AcquisitionFailureRecord(
        identity=identity,
        code=error.code,
        disposition=error.disposition,
        origin_code=error.origin_code,
        origin_disposition=error.origin_disposition,
    )


def _bounded_retry_failure(
    identity: AcquisitionIdentity,
    error: CodexExecError,
) -> tuple[CodexExecError, AcquisitionIdentity | None]:
    if error.disposition is not AcquisitionDisposition.RETRY_TRANSPORT:
        return error, None
    if identity.attempt >= MAX_CONSECUTIVE_RETRY_TRANSPORT:
        return (
            CodexExecError(
                "retry_transport_limit_reached",
                "two consecutive RETRY_TRANSPORT failures stop the acquisition before a third call",
                disposition=AcquisitionDisposition.STOP_PHASE,
                origin_code=error.code,
                origin_disposition=error.disposition,
            ),
            None,
        )
    return error, identity.model_copy(update={"attempt": identity.attempt + 1})


def development_acquisition_identities(
    manifest: DevelopmentManifest,
    replicates: int,
) -> tuple[AcquisitionIdentity, ...]:
    if replicates <= 0:
        raise ValueError("replicate count must be positive")
    return tuple(
        AcquisitionIdentity(
            experiment_id=manifest.experiment_id,
            case_id=fixture.case_id,
            channel="development",
            replicate_id=replicate,
            attempt=1,
        )
        for fixture in manifest.fixtures
        for replicate in range(replicates)
    )


def scripted_response_template(
    manifest: DevelopmentManifest,
    replicates: int,
) -> dict[str, str]:
    """Return an executable all-hold template keyed by canonical acquisition hash."""

    raw_hold = canonical_json_bytes(hold_batch()).decode("utf-8")
    identities = development_acquisition_identities(manifest, replicates)
    template = {acquisition_key(identity): raw_hold for identity in identities}
    if len(template) != len(identities):
        raise RuntimeError("acquisition-key collision")
    return template


def _build_development_plan(
    manifest_reference: ArtifactReference,
    manifest: DevelopmentManifest,
    replicates: int,
) -> DevelopmentRunPlan:
    fixtures = {fixture.case_id: fixture.fixture for fixture in manifest.fixtures}
    entries = tuple(RunPlanEntry(identity=identity, fixture=fixtures[identity.case_id]) for identity in development_acquisition_identities(manifest, replicates))
    return DevelopmentRunPlan(
        experiment_id=manifest.experiment_id,
        manifest=manifest_reference,
        entries=entries,
    )


def _cached_oracle(
    cache: dict[str, OracleResult],
    episode: SyntheticEpisode,
) -> OracleResult:
    if episode.content_sha256 not in cache:
        cache[episode.content_sha256] = solve_oracle(episode)
    return cache[episode.content_sha256]


def _write_request_artifacts(
    store: AppendOnlyArtifactStore,
    *,
    identity: AcquisitionIdentity,
    episode: SyntheticEpisode,
    client: AcquisitionClient,
) -> _RequestArtifacts:
    prefix = _acquisition_prefix(identity)
    policy_input = build_policy_input(episode.public)
    user_prompt = build_user_prompt(episode.public)
    policy_input_ref = store.write_json(f"{prefix}/policy_input.json", policy_input)
    system_ref = store.write_text(f"{prefix}/system_prompt.txt", SYSTEM_PROMPT_V1)
    user_ref = store.write_text(f"{prefix}/user_prompt.txt", user_prompt)
    request_ref = store.write_json(
        f"{prefix}/provider_request.json",
        {
            "identity": identity,
            "acquisition_key": acquisition_key(identity),
            "system_prompt_sha256": system_ref.sha256,
            "user_prompt_sha256": user_ref.sha256,
            "client_type": type(client).__name__,
            "phase": "DEVELOPMENT_ONLY_NOT_SEALED",
        },
    )
    return _RequestArtifacts(
        user_prompt=user_prompt,
        policy_input=policy_input_ref,
        system_prompt=system_ref,
        user_prompt_artifact=user_ref,
        provider_request=request_ref,
    )


def _consume_complete_response(
    episode: SyntheticEpisode,
    response: ProviderResponse,
) -> tuple[ParsedPolicyOutcome, CompleteResponseDispositionRecord]:
    disposition = complete_response_disposition(response)
    if disposition is AcquisitionDisposition.STOP_PHASE:
        raise CodexExecError(
            "complete_response_stop_phase",
            "complete response is not eligible for scoring",
            disposition=AcquisitionDisposition.STOP_PHASE,
        )
    if disposition is AcquisitionDisposition.RETRY_TRANSPORT:
        raise CodexExecError(
            "missing_complete_response_disposition_consumer",
            "complete response cannot enter transport retry",
            disposition=AcquisitionDisposition.STOP_PHASE,
        )

    if disposition is AcquisitionDisposition.FAIL_CLOSED_SCORE:
        tool_types = ", ".join(response.tool_event_types) or "unspecified complete-response violation"
        outcome = fail_closed_outcome(
            episode.public,
            code="tool_use_violation",
            detail=f"complete response emitted forbidden tool events: {tool_types}",
        )
    else:
        outcome = parse_and_validate(episode.public, response.raw_text)
        if outcome.validation.fell_back:
            disposition = AcquisitionDisposition.FAIL_CLOSED_SCORE

    reason_codes = tuple(sorted({violation.code for violation in outcome.validation.violations}))
    if outcome.validation.fell_back and not reason_codes:
        raise CodexExecError(
            "fail_closed_without_reason",
            "fail-closed response has no recorded violation reason",
            disposition=AcquisitionDisposition.STOP_PHASE,
        )
    record = CompleteResponseDispositionRecord(
        disposition=disposition,
        reason_codes=reason_codes,
        scored_as_hold=disposition is AcquisitionDisposition.FAIL_CLOSED_SCORE,
    )
    return outcome, record


def _complete_acquisition(
    store: AppendOnlyArtifactStore,
    *,
    entry: RunPlanEntry,
    episode: SyntheticEpisode,
    client: AcquisitionClient,
    oracle: OracleResult,
    provider_call_ceiling: int | None = None,
) -> _AcquisitionOutcome:
    identity = entry.identity
    prior_attempt_failures: list[ArtifactReference] = []
    while True:
        if provider_call_ceiling is not None and client.provider_calls >= provider_call_ceiling:
            raise CodexExecError(
                "development_attempt_cap_reached",
                "development provider-attempt cap reached before the next call",
                disposition=AcquisitionDisposition.STOP_PHASE,
            )
        prefix = _acquisition_prefix(identity)
        request = _write_request_artifacts(
            store,
            identity=identity,
            episode=episode,
            client=client,
        )
        try:
            response = client.complete(
                system=SYSTEM_PROMPT_V1,
                user=request.user_prompt,
                identity=identity,
            )
        except CodexExecError as error:
            effective_error, retry_identity = _bounded_retry_failure(identity, error)
            failure_ref = store.write_json(
                f"{prefix}/acquisition_failure.json",
                _failure_record(identity, effective_error),
            )
            if retry_identity is None:
                raise effective_error from error
            prior_attempt_failures.append(failure_ref)
            identity = retry_identity
            continue
        break

    raw_ref = store.write_text(f"{prefix}/raw_response.txt", response.raw_text)
    response_metadata = response.model_dump(mode="python", exclude={"raw_text"})
    response_metadata["raw_text_sha256"] = raw_ref.sha256
    response_metadata_ref = store.write_json(
        f"{prefix}/provider_response_metadata.json",
        response_metadata,
    )
    outcome, disposition = _consume_complete_response(episode, response)
    score = score_episode(episode, outcome.validation)
    assert_oracle_bound("llm", score.utility_e12, oracle)

    disposition_ref = store.write_json(
        f"{prefix}/response_disposition.json",
        disposition,
    )
    parsed_ref = store.write_json(f"{prefix}/parsed_decision.json", outcome.parsed_artifact)
    validation_ref = store.write_json(f"{prefix}/validation_report.json", outcome.validation)
    executable_ref = store.write_json(f"{prefix}/executable_batch.json", outcome.validation.executable)
    cost_ref = store.write_json(f"{prefix}/cost_ledger.json", outcome.validation.cost_ledger)
    score_ref = store.write_json(f"{prefix}/episode_score.json", score)
    oracle_ref = store.write_json(f"{prefix}/oracle_certificate.json", oracle.certificate)
    artifacts = AcquisitionArtifacts(
        identity=identity,
        fixture=entry.fixture,
        prior_attempt_failures=tuple(prior_attempt_failures),
        policy_input=request.policy_input,
        system_prompt=request.system_prompt,
        user_prompt=request.user_prompt_artifact,
        provider_request=request.provider_request,
        raw_response=raw_ref,
        provider_response_metadata=response_metadata_ref,
        response_disposition=disposition_ref,
        parsed_decision=parsed_ref,
        validation_report=validation_ref,
        executable_batch=executable_ref,
        cost_ledger=cost_ref,
        episode_score=score_ref,
        oracle_certificate=oracle_ref,
    )
    return _AcquisitionOutcome(
        artifacts=artifacts,
        disposition=disposition,
        validation=outcome.validation,
        score=score,
    )


def _baseline_utilities(
    episode: SyntheticEpisode,
    oracle: OracleResult,
) -> dict[str, int]:
    policies = (
        primary_deterministic(episode),
        hold_policy(episode),
        equal_risk_policy(episode),
    )
    for policy in policies:
        assert_oracle_bound(policy.name, policy.score.utility_e12, oracle)
    return {
        "deterministic_utility_e12": policies[0].score.utility_e12,
        "hold_utility_e12": policies[1].score.utility_e12,
        "equal_risk_utility_e12": policies[2].score.utility_e12,
    }


def _write_development_result(
    store: AppendOnlyArtifactStore,
    *,
    experiment_id: str,
    plan_reference: ArtifactReference,
    acquisitions: list[AcquisitionArtifacts],
    report_cases: list[dict[str, Any]],
) -> tuple[ArtifactReference, DevelopmentRunResult]:
    report_json, report_markdown = build_report(report_cases)
    report_json_ref = store.write_json(f"{experiment_id}/development_report.json", report_json)
    report_markdown_ref = store.write_text(f"{experiment_id}/development_report.md", report_markdown)
    result = DevelopmentRunResult(
        experiment_id=experiment_id,
        run_plan=plan_reference,
        acquisitions=tuple(acquisitions),
        report_json=report_json_ref,
        report_markdown=report_markdown_ref,
    )
    result_ref = store.write_json(f"{experiment_id}/run_result.json", result)
    return result_ref, result


def _reconstruct_provider_response(
    raw_bytes: bytes,
    metadata_bytes: bytes,
) -> ProviderResponse:
    try:
        metadata = json.loads(metadata_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("provider response metadata is not replayable") from exc
    if not isinstance(metadata, dict) or "raw_text" in metadata:
        raise RuntimeError("provider response metadata is not replayable")
    if metadata.pop("raw_text_sha256", None) != sha256_hex(raw_bytes):
        raise RuntimeError("raw response hash does not match provider response metadata")
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("raw response is not valid UTF-8") from exc
    return ProviderResponse.model_validate_json(canonical_json_bytes({"raw_text": raw_text, **metadata}))


def run_scripted_acquisition(
    store: AppendOnlyArtifactStore,
    *,
    manifest_reference: ArtifactReference,
    client: AcquisitionClient,
    expected_freeze_sha256: str,
    replicates: int = 1,
    max_provider_attempts: int = DEVELOPMENT_ATTEMPT_CAP,
) -> tuple[ArtifactReference, DevelopmentRunResult]:
    if max_provider_attempts <= 0 or max_provider_attempts > DEVELOPMENT_ATTEMPT_CAP:
        raise ValueError(f"development provider-attempt cap must be in [1, {DEVELOPMENT_ATTEMPT_CAP}]")
    manifest = DevelopmentManifest.model_validate_json(store.read_bytes(manifest_reference))
    _verify_manifest_specs(
        store,
        manifest,
        expected_freeze_sha256=expected_freeze_sha256,
    )
    plan = _build_development_plan(
        manifest_reference,
        manifest,
        replicates,
    )
    plan_reference = store.write_json(f"{manifest.experiment_id}/run_plan.json", plan)

    acquisitions: list[AcquisitionArtifacts] = []
    report_cases: list[dict[str, Any]] = []
    baseline_cache: dict[str, dict[str, int]] = {}
    oracle_cache: dict[str, OracleResult] = {}
    provider_call_ceiling = client.provider_calls + max_provider_attempts
    for entry in plan.entries:
        identity = entry.identity
        episode = _load_episode(store, entry.fixture)
        oracle = _cached_oracle(oracle_cache, episode)
        outcome = _complete_acquisition(
            store,
            entry=entry,
            episode=episode,
            client=client,
            oracle=oracle,
            provider_call_ceiling=provider_call_ceiling,
        )
        acquisitions.append(outcome.artifacts)
        if episode.content_sha256 not in baseline_cache:
            baseline_cache[episode.content_sha256] = _baseline_utilities(episode, oracle)
        report_cases.append(
            {
                "case_id": episode.public.case_id,
                "regime": episode.hidden.regime,
                "replicate_id": identity.replicate_id,
                "raw_valid": outcome.validation.raw_valid,
                "fell_back": outcome.validation.fell_back,
                "acquisition_disposition": outcome.disposition.disposition,
                "llm_utility_e12": outcome.score.utility_e12,
                "oracle_utility_e12": oracle.score.utility_e12,
                **baseline_cache[episode.content_sha256],
            }
        )

    return _write_development_result(
        store,
        experiment_id=manifest.experiment_id,
        plan_reference=plan_reference,
        acquisitions=acquisitions,
        report_cases=report_cases,
    )


def _assert_json_bytes(store: AppendOnlyArtifactStore, reference: ArtifactReference, value: Any) -> None:
    expected = canonical_json_bytes(value)
    actual = store.read_bytes(reference)
    if actual != expected:
        raise RuntimeError(f"replay byte mismatch: {reference.relative_path}")


def replay(
    store: AppendOnlyArtifactStore,
    *,
    result_reference: ArtifactReference,
    expected_freeze_sha256: str,
    expected_manifest_sha256: str,
    expected_result_sha256: str,
    persist_verification: bool = True,
) -> ReplayVerification:
    if result_reference.sha256 != expected_result_sha256:
        raise RuntimeError("run-result hash differs from the external trust anchor")
    result = DevelopmentRunResult.model_validate_json(store.read_bytes(result_reference))
    plan = DevelopmentRunPlan.model_validate_json(store.read_bytes(result.run_plan))
    if plan.manifest.sha256 != expected_manifest_sha256:
        raise RuntimeError("manifest hash differs from the external trust anchor")
    manifest = DevelopmentManifest.model_validate_json(store.read_bytes(plan.manifest))
    if manifest.experiment_id != plan.experiment_id or result.experiment_id != plan.experiment_id:
        raise RuntimeError("manifest, plan, and result experiment identities differ")
    _verify_manifest_specs(
        store,
        manifest,
        expected_freeze_sha256=expected_freeze_sha256,
    )
    planned = {acquisition_key(entry.identity): entry for entry in plan.entries}
    if len(planned) != len(result.acquisitions):
        raise RuntimeError("run plan and acquisition result counts differ")

    oracle_cache: dict[str, OracleResult] = {}
    for acquisition in result.acquisitions:
        key = acquisition_key(_initial_attempt_identity(acquisition.identity))
        if key not in planned:
            raise RuntimeError(f"unplanned acquisition: {key}")
        if len(acquisition.prior_attempt_failures) != acquisition.identity.attempt - 1:
            raise RuntimeError("final acquisition attempt does not match its bound failure history")
        for expected_attempt, failure_reference in enumerate(
            acquisition.prior_attempt_failures,
            start=1,
        ):
            failure = AcquisitionFailureRecord.model_validate_json(store.read_bytes(failure_reference))
            if failure.identity != acquisition.identity.model_copy(update={"attempt": expected_attempt}):
                raise RuntimeError("retry failure identity does not match the final acquisition")
            if failure.disposition is not AcquisitionDisposition.RETRY_TRANSPORT:
                raise RuntimeError("a completed retry chain may bind only RETRY_TRANSPORT failures")
        for reference in (
            acquisition.policy_input,
            acquisition.system_prompt,
            acquisition.user_prompt,
            acquisition.provider_request,
            acquisition.provider_response_metadata,
        ):
            store.verify(reference)
        episode = _load_episode(store, acquisition.fixture)
        response = _reconstruct_provider_response(
            store.read_bytes(acquisition.raw_response),
            store.read_bytes(acquisition.provider_response_metadata),
        )
        outcome, disposition = _consume_complete_response(episode, response)
        score = score_episode(episode, outcome.validation)
        oracle = _cached_oracle(oracle_cache, episode)
        assert_oracle_bound("replayed llm", score.utility_e12, oracle)
        _assert_json_bytes(store, acquisition.response_disposition, disposition)
        _assert_json_bytes(store, acquisition.parsed_decision, outcome.parsed_artifact)
        _assert_json_bytes(store, acquisition.validation_report, outcome.validation)
        _assert_json_bytes(store, acquisition.executable_batch, outcome.validation.executable)
        _assert_json_bytes(store, acquisition.cost_ledger, outcome.validation.cost_ledger)
        _assert_json_bytes(store, acquisition.episode_score, score)
        _assert_json_bytes(store, acquisition.oracle_certificate, oracle.certificate)
    store.verify(result.report_json)
    store.verify(result.report_markdown)
    verification = ReplayVerification(
        experiment_id=result.experiment_id,
        verified_acquisitions=len(result.acquisitions),
    )
    if persist_verification:
        store.write_json(f"{result.experiment_id}/replay_verification.json", verification)
    return verification


def _print_reference(reference: ArtifactReference) -> None:
    print(canonical_json_bytes(reference).decode("utf-8"))


def _write_safe_relative_json(relative_path: str, payload: Any) -> Path:
    output = Path(normalize_artifact_relative_path(relative_path))
    with output.open("xb") as handle:
        handle.write(canonical_json_bytes(payload))
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R01 provider-free development runner")
    parser.add_argument("--artifact-root", default=".research_artifacts/r01")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate-development")
    generate.add_argument("--experiment-id", required=True)
    generate.add_argument("--root-seed", required=True)
    generate.add_argument("--count", type=int, default=40)
    generate.add_argument("--freeze-sha256", required=True)
    generate.add_argument("--contract", default="docs/research-contract-01-llm-overlay.md")

    template = subparsers.add_parser("scripted-template")
    template.add_argument("--manifest", required=True, help="artifact-root relative path")
    template.add_argument("--replicates", type=int, default=1)
    template.add_argument("--output", required=True, help="new JSON response-map path")
    template.add_argument("--freeze-sha256", required=True)

    freeze_parser = subparsers.add_parser("provider-free-freeze")
    freeze_parser.add_argument("--root-seed", required=True)
    freeze_parser.add_argument("--count", type=int, default=40)
    freeze_parser.add_argument("--output", required=True, help="new safe relative JSON path")
    freeze_parser.add_argument("--freeze-sha256", required=True)

    gap_summary = subparsers.add_parser("provider-free-gap-summary")
    gap_summary.add_argument("--output", required=True, help="new safe relative JSON path")
    gap_summary.add_argument("--freeze-sha256", required=True)

    dry_run = subparsers.add_parser("dry-run")
    dry_run.add_argument("--manifest", required=True, help="artifact-root relative path")
    dry_run.add_argument("--responses", required=True, help="JSON acquisition-key to raw-text map")
    dry_run.add_argument("--replicates", type=int, default=1)
    dry_run.add_argument("--freeze-sha256", required=True)

    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("--result", required=True, help="artifact-root relative path")
    replay_parser.add_argument("--expected-manifest-sha256", required=True)
    replay_parser.add_argument("--expected-result-sha256", required=True)
    replay_parser.add_argument("--freeze-sha256", required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--result", required=True, help="artifact-root relative path")
    verify.add_argument("--expected-manifest-sha256", required=True)
    verify.add_argument("--expected-result-sha256", required=True)
    verify.add_argument("--freeze-sha256", required=True)

    args = parser.parse_args(argv)
    store = AppendOnlyArtifactStore(args.artifact_root)
    if args.command == "generate-development":
        committed_freeze = load_committed_provider_free_freeze(expected_sha256=args.freeze_sha256)
        if args.root_seed != committed_freeze.root_seed_label:
            raise RuntimeError("development root seed differs from the committed B0 freeze")
        if args.count != committed_freeze.fixture_count:
            raise RuntimeError("development fixture count differs from the committed B0 freeze")
        contract_bytes = Path(args.contract).read_bytes()
        reference, _manifest = generate_development_manifest(
            store,
            experiment_id=args.experiment_id,
            root_seed=args.root_seed,
            contract_bytes=contract_bytes,
            count=args.count,
            expected_freeze_sha256=args.freeze_sha256,
        )
        _print_reference(reference)
        return 0
    if args.command == "scripted-template":
        manifest_reference = store.reference_for_existing(args.manifest)
        manifest = DevelopmentManifest.model_validate_json(store.read_bytes(manifest_reference))
        _verify_manifest_specs(
            store,
            manifest,
            expected_freeze_sha256=args.freeze_sha256,
        )
        payload = scripted_response_template(manifest, args.replicates)
        output = _write_safe_relative_json(args.output, payload)
        print(canonical_json_bytes({"acquisitions": len(payload), "output": str(output)}).decode("utf-8"))
        return 0
    if args.command == "provider-free-freeze":
        freeze = generate_provider_free_freeze(
            root_seed_label=args.root_seed,
            count=args.count,
        )
        verify_frozen_development_identity(
            freeze,
            expected_sha256=args.freeze_sha256,
        )
        output = _write_safe_relative_json(args.output, freeze)
        print(
            canonical_json_bytes(
                {
                    "fixture_count": freeze.fixture_count,
                    "output": str(output),
                    "sha256": canonical_sha256(freeze),
                }
            ).decode("utf-8")
        )
        return 0
    if args.command == "provider-free-gap-summary":
        summary = load_committed_provider_free_regime_gap_summary(expected_freeze_sha256=args.freeze_sha256)
        output = _write_safe_relative_json(args.output, summary)
        print(
            canonical_json_bytes(
                {
                    "fixture_count": summary.fixture_count,
                    "output": str(output),
                    "sha256": canonical_sha256(summary),
                }
            ).decode("utf-8")
        )
        return 0
    if args.command == "dry-run":
        responses_payload = json.loads(Path(args.responses).read_text(encoding="utf-8"))
        if not isinstance(responses_payload, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in responses_payload.items()):
            raise ValueError("responses must be a JSON object mapping acquisition keys to raw text")
        manifest_reference = store.reference_for_existing(args.manifest)
        result_reference, _result = run_scripted_acquisition(
            store,
            manifest_reference=manifest_reference,
            client=ScriptedAcquisitionClient(responses_payload),
            expected_freeze_sha256=args.freeze_sha256,
            replicates=args.replicates,
        )
        _print_reference(result_reference)
        return 0
    result_reference = store.reference_for_existing(args.result)
    verification = replay(
        store,
        result_reference=result_reference,
        persist_verification=args.command == "replay",
        expected_freeze_sha256=args.freeze_sha256,
        expected_manifest_sha256=args.expected_manifest_sha256,
        expected_result_sha256=args.expected_result_sha256,
    )
    print(canonical_json_bytes(verification).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
