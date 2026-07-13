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
from .contracts import (
    AcquisitionArtifacts,
    AcquisitionIdentity,
    ArtifactReference,
    DevelopmentManifest,
    DevelopmentRunPlan,
    DevelopmentRunResult,
    EpisodeScore,
    FixtureManifestEntry,
    GeneratorConfig,
    OracleResult,
    ReplayVerification,
    RunPlanEntry,
    SyntheticEpisode,
    ValidationReport,
)
from .fixtures import generate_development_episodes
from .llm_policy import (
    SYSTEM_PROMPT_V1,
    AcquisitionClient,
    ScriptedAcquisitionClient,
    acquisition_key,
    build_policy_input,
    build_user_prompt,
    parse_and_validate,
)
from .lattice import hold_batch
from .oracle import assert_oracle_bound, solve_oracle
from .report import build_report
from .scoring import score_episode
from .specs import analysis_spec, analysis_spec_sha256, scoring_spec, scoring_spec_sha256


def generate_development_manifest(
    store: AppendOnlyArtifactStore,
    *,
    experiment_id: str,
    root_seed: str,
    contract_bytes: bytes,
    config: GeneratorConfig | None = None,
    count: int = 40,
) -> tuple[ArtifactReference, DevelopmentManifest]:
    config = config or GeneratorConfig()
    episodes = generate_development_episodes(config, root_seed, count)
    scoring_reference = store.write_json(f"{experiment_id}/scoring_spec.json", scoring_spec())
    analysis_reference = store.write_json(f"{experiment_id}/analysis_spec.json", analysis_spec())
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


def _verify_manifest_specs(store: AppendOnlyArtifactStore, manifest: DevelopmentManifest) -> None:
    store.verify(manifest.scoring_spec)
    store.verify(manifest.analysis_spec)
    if manifest.scoring_spec.sha256 != manifest.scoring_spec_sha256:
        raise RuntimeError("scoring spec hash mismatch")
    if manifest.analysis_spec.sha256 != manifest.analysis_spec_sha256:
        raise RuntimeError("analysis spec hash mismatch")
    if manifest.scoring_spec_sha256 != scoring_spec_sha256():
        raise RuntimeError("runtime scoring spec differs from manifest")
    if manifest.analysis_spec_sha256 != analysis_spec_sha256():
        raise RuntimeError("runtime analysis spec differs from manifest")
    if store.read_bytes(manifest.scoring_spec) != canonical_json_bytes(scoring_spec()):
        raise RuntimeError("scoring spec bytes differ from runtime spec")
    if store.read_bytes(manifest.analysis_spec) != canonical_json_bytes(analysis_spec()):
        raise RuntimeError("analysis spec bytes differ from runtime spec")


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
    validation: ValidationReport
    score: EpisodeScore


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


def _complete_acquisition(
    store: AppendOnlyArtifactStore,
    *,
    entry: RunPlanEntry,
    episode: SyntheticEpisode,
    client: AcquisitionClient,
    oracle: OracleResult,
) -> _AcquisitionOutcome:
    identity = entry.identity
    prefix = _acquisition_prefix(identity)
    request = _write_request_artifacts(
        store,
        identity=identity,
        episode=episode,
        client=client,
    )
    response = client.complete(
        system=SYSTEM_PROMPT_V1,
        user=request.user_prompt,
        identity=identity,
    )

    raw_ref = store.write_text(f"{prefix}/raw_response.txt", response.raw_text)
    response_metadata_ref = store.write_json(
        f"{prefix}/provider_response_metadata.json",
        response.model_dump(mode="python", exclude={"raw_text"}),
    )
    outcome = parse_and_validate(episode.public, response.raw_text)
    score = score_episode(episode, outcome.validation)
    assert_oracle_bound("llm", score.utility_e12, oracle)

    parsed_ref = store.write_json(f"{prefix}/parsed_decision.json", outcome.parsed_artifact)
    validation_ref = store.write_json(f"{prefix}/validation_report.json", outcome.validation)
    executable_ref = store.write_json(f"{prefix}/executable_batch.json", outcome.validation.executable)
    cost_ref = store.write_json(f"{prefix}/cost_ledger.json", outcome.validation.cost_ledger)
    score_ref = store.write_json(f"{prefix}/episode_score.json", score)
    oracle_ref = store.write_json(f"{prefix}/oracle_certificate.json", oracle.certificate)
    artifacts = AcquisitionArtifacts(
        identity=identity,
        fixture=entry.fixture,
        policy_input=request.policy_input,
        system_prompt=request.system_prompt,
        user_prompt=request.user_prompt_artifact,
        provider_request=request.provider_request,
        raw_response=raw_ref,
        provider_response_metadata=response_metadata_ref,
        parsed_decision=parsed_ref,
        validation_report=validation_ref,
        executable_batch=executable_ref,
        cost_ledger=cost_ref,
        episode_score=score_ref,
        oracle_certificate=oracle_ref,
    )
    return _AcquisitionOutcome(
        artifacts=artifacts,
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


def run_scripted_acquisition(
    store: AppendOnlyArtifactStore,
    *,
    manifest_reference: ArtifactReference,
    client: AcquisitionClient,
    replicates: int = 1,
) -> tuple[ArtifactReference, DevelopmentRunResult]:
    manifest = DevelopmentManifest.model_validate_json(store.read_bytes(manifest_reference))
    _verify_manifest_specs(store, manifest)
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
    _verify_manifest_specs(store, manifest)
    planned = {acquisition_key(entry.identity): entry for entry in plan.entries}
    if len(planned) != len(result.acquisitions):
        raise RuntimeError("run plan and acquisition result counts differ")

    oracle_cache: dict[str, OracleResult] = {}
    for acquisition in result.acquisitions:
        key = acquisition_key(acquisition.identity)
        if key not in planned:
            raise RuntimeError(f"unplanned acquisition: {key}")
        for reference in (
            acquisition.policy_input,
            acquisition.system_prompt,
            acquisition.user_prompt,
            acquisition.provider_request,
            acquisition.provider_response_metadata,
        ):
            store.verify(reference)
        episode = _load_episode(store, acquisition.fixture)
        raw_text = store.read_bytes(acquisition.raw_response).decode("utf-8")
        outcome = parse_and_validate(episode.public, raw_text)
        score = score_episode(episode, outcome.validation)
        oracle = _cached_oracle(oracle_cache, episode)
        assert_oracle_bound("replayed llm", score.utility_e12, oracle)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R01 provider-free development runner")
    parser.add_argument("--artifact-root", default=".research_artifacts/r01")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate-development")
    generate.add_argument("--experiment-id", required=True)
    generate.add_argument("--root-seed", required=True)
    generate.add_argument("--count", type=int, default=40)
    generate.add_argument("--contract", default="docs/research-contract-01-llm-overlay.md")

    template = subparsers.add_parser("scripted-template")
    template.add_argument("--manifest", required=True, help="artifact-root relative path")
    template.add_argument("--replicates", type=int, default=1)
    template.add_argument("--output", required=True, help="new JSON response-map path")

    dry_run = subparsers.add_parser("dry-run")
    dry_run.add_argument("--manifest", required=True, help="artifact-root relative path")
    dry_run.add_argument("--responses", required=True, help="JSON acquisition-key to raw-text map")
    dry_run.add_argument("--replicates", type=int, default=1)

    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("--result", required=True, help="artifact-root relative path")
    replay_parser.add_argument("--expected-manifest-sha256", required=True)
    replay_parser.add_argument("--expected-result-sha256", required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--result", required=True, help="artifact-root relative path")
    verify.add_argument("--expected-manifest-sha256", required=True)
    verify.add_argument("--expected-result-sha256", required=True)

    args = parser.parse_args(argv)
    store = AppendOnlyArtifactStore(args.artifact_root)
    if args.command == "generate-development":
        contract_bytes = Path(args.contract).read_bytes()
        reference, _manifest = generate_development_manifest(
            store,
            experiment_id=args.experiment_id,
            root_seed=args.root_seed,
            contract_bytes=contract_bytes,
            count=args.count,
        )
        _print_reference(reference)
        return 0
    if args.command == "scripted-template":
        manifest_reference = store.reference_for_existing(args.manifest)
        manifest = DevelopmentManifest.model_validate_json(store.read_bytes(manifest_reference))
        _verify_manifest_specs(store, manifest)
        payload = scripted_response_template(manifest, args.replicates)
        output = Path(args.output)
        with output.open("xb") as handle:
            handle.write(canonical_json_bytes(payload))
        print(canonical_json_bytes({"acquisitions": len(payload), "output": str(output)}).decode("utf-8"))
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
            replicates=args.replicates,
        )
        _print_reference(result_reference)
        return 0
    result_reference = store.reference_for_existing(args.result)
    verification = replay(
        store,
        result_reference=result_reference,
        persist_verification=args.command == "replay",
        expected_manifest_sha256=args.expected_manifest_sha256,
        expected_result_sha256=args.expected_result_sha256,
    )
    print(canonical_json_bytes(verification).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
