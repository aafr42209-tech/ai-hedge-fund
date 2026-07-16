"""Provider-free preparation and reviewed live-client construction for R01 B3."""

from __future__ import annotations

import json
from pathlib import Path

from .artifacts import AppendOnlyArtifactStore
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .codex_exec_client import (
    build_codex_command_spec,
    codex_transport_shape_spec_sha256,
    CodexExecClient,
    SubprocessCodexProcessRunner,
)
from .codex_preflight import (
    build_codex_feature_gate,
    capture_zero_call_preflight,
    parse_codex_feature_catalog,
    pilot_sandbox_identity_sha256,
    SubprocessLocalCommandRunner,
)
from .contracts import (
    ArtifactReference,
    B3Preflight,
    CodexCommandSpec,
    CodexFeatureGate,
    DevelopmentBudgetCarryForward,
    DevelopmentManifest,
    LIVE_PROCESS_TIMEOUT_MS,
)
from .llm_policy import build_user_prompt_v2, SYSTEM_PROMPT_V2
from .runner import _load_episode, _verify_manifest_specs, build_b3_anchor_manifest

MODEL_ID = "gpt-5.6-sol"
ACTIVE_FEATURE_ALLOWLIST = (
    "resize_all_images",
    "terminal_resize_reflow",
    "tool_search_always_defer_mcp_tools",
    "tui_app_server",
)
CONFIG_OVERRIDES = (
    "model_reasoning_effort=high",
    "tools.web_search=false",
)
EXPECTED_CLI_VERSION = "codex-cli 0.144.1"


def _file_sha256(path: str | Path) -> str:
    return sha256_hex(Path(path).read_bytes())


def _load_budget_carry_forward(
    path: str | Path,
    *,
    expected_sha256: str,
) -> DevelopmentBudgetCarryForward:
    payload = Path(path).read_bytes()
    if sha256_hex(payload) != expected_sha256:
        raise RuntimeError("development budget carry-forward differs from the external trust anchor")
    return DevelopmentBudgetCarryForward.model_validate_json(payload)


def _current_feature_gate(
    executable: str,
    *,
    committed_capture_path: str | Path,
) -> tuple[dict[str, object], CodexFeatureGate]:
    committed = json.loads(Path(committed_capture_path).read_text(encoding="utf-8"))
    summary, raw = capture_zero_call_preflight(
        executable,
        expected_catalog_sha256=committed["feature_catalog_sha256"],
        expected_definition_sha256=committed["feature_catalog_definition_sha256"],
        runner=SubprocessLocalCommandRunner(),
    )
    if canonical_json_bytes(summary) != canonical_json_bytes(committed):
        raise RuntimeError("current zero-call Codex identity differs from the committed B2 capture")
    if summary["codex_cli_version"] != EXPECTED_CLI_VERSION:
        raise RuntimeError("Codex CLI version differs from the D2-approved identity")
    gate = build_codex_feature_gate(
        parse_codex_feature_catalog(raw["baseline_features"]),
        parse_codex_feature_catalog(raw["post_disable_features"]),
        active_feature_allowlist=ACTIVE_FEATURE_ALLOWLIST,
        expected_feature_catalog_sha256=committed["feature_catalog_sha256"],
    )
    if gate.post_disable_effective_true_features != ACTIVE_FEATURE_ALLOWLIST:
        raise RuntimeError("post-disable effective-true features differ from the D2 allowlist")
    return summary, gate


def prepare_b3_preflight(
    store: AppendOnlyArtifactStore,
    *,
    manifest_reference: ArtifactReference,
    expected_freeze_sha256: str,
    executable: str,
    expected_executable_sha256: str,
    sandbox_directory: str,
    account_attestation_path: str | Path,
    expected_account_attestation_sha256: str,
    resource_amendment_path: str | Path,
    expected_resource_amendment_sha256: str,
    budget_carry_forward_path: str | Path,
    expected_budget_carry_forward_sha256: str,
    committed_capture_path: str | Path,
) -> tuple[ArtifactReference, B3Preflight]:
    executable_path = Path(executable).resolve()
    if not executable_path.is_file():
        raise ValueError("Codex executable must be an existing file")
    if _file_sha256(executable_path) != expected_executable_sha256:
        raise RuntimeError("Codex executable differs from the external trust anchor")
    if _file_sha256(account_attestation_path) != expected_account_attestation_sha256:
        raise RuntimeError("zero-cost account attestation differs from the external trust anchor")
    if _file_sha256(resource_amendment_path) != expected_resource_amendment_sha256:
        raise RuntimeError("D2 resource amendment differs from the external trust anchor")
    budget_carry_forward = _load_budget_carry_forward(
        budget_carry_forward_path,
        expected_sha256=expected_budget_carry_forward_sha256,
    )
    if budget_carry_forward.schema_version != "r01-development-budget-carry-forward-v3":
        raise RuntimeError("new B3 preflight requires aggregate budget carry-forward v3")

    manifest = DevelopmentManifest.model_validate_json(store.read_bytes(manifest_reference))
    _verify_manifest_specs(
        store,
        manifest,
        expected_freeze_sha256=expected_freeze_sha256,
    )
    current_summary, feature_gate = _current_feature_gate(
        str(executable_path),
        committed_capture_path=committed_capture_path,
    )
    feature_gate_reference = store.write_json(
        f"{manifest.experiment_id}/b3_preflight/feature_gate.json",
        feature_gate,
    )
    anchor_reference, anchors = build_b3_anchor_manifest(
        store,
        manifest_reference=manifest_reference,
        manifest=manifest,
    )
    expected_sandbox_sha256 = pilot_sandbox_identity_sha256(sandbox_directory)
    command_spec_references: list[ArtifactReference] = []
    for anchor in anchors.anchors:
        episode = _load_episode(store, anchor.fixture)
        command_spec, _stdin = build_codex_command_spec(
            executable=str(executable_path),
            model_id=MODEL_ID,
            feature_catalog=feature_gate.feature_catalog,
            expected_feature_catalog_sha256=feature_gate.feature_catalog_sha256,
            disabled_features=feature_gate.disabled_features,
            active_feature_allowlist=feature_gate.active_feature_allowlist,
            post_disable_effective_true_features=feature_gate.post_disable_effective_true_features,
            config_overrides=CONFIG_OVERRIDES,
            working_directory=sandbox_directory,
            expected_pilot_sandbox_sha256=expected_sandbox_sha256,
            expected_transport_shape_spec_sha256=codex_transport_shape_spec_sha256(),
            timeout_ms=LIVE_PROCESS_TIMEOUT_MS,
            policy_instruction=SYSTEM_PROMPT_V2,
            fixture_prompt=build_user_prompt_v2(episode.public),
        )
        command_spec_references.append(
            store.write_json(
                f"{manifest.experiment_id}/b3_preflight/command_specs/{anchor.case_id}.json",
                command_spec,
            )
        )
    preflight = B3Preflight(
        experiment_id=manifest.experiment_id,
        manifest=manifest_reference,
        anchor_manifest=anchor_reference,
        feature_gate=feature_gate_reference,
        command_specs=tuple(command_spec_references),
        account_attestation_sha256=expected_account_attestation_sha256,
        resource_amendment_sha256=expected_resource_amendment_sha256,
        budget_carry_forward_document_sha256=expected_budget_carry_forward_sha256,
        budget_carry_forward=budget_carry_forward,
        executable=str(executable_path),
        executable_sha256=expected_executable_sha256,
        codex_cli_version=str(current_summary["codex_cli_version"]),
    )
    reference = store.write_json(
        f"{manifest.experiment_id}/b3_preflight.json",
        preflight,
    )
    return reference, preflight


def build_live_b3_client(
    store: AppendOnlyArtifactStore,
    *,
    preflight_reference: ArtifactReference,
    expected_preflight_sha256: str,
    sandbox_directory: str,
    account_attestation_path: str | Path,
    resource_amendment_path: str | Path,
    budget_carry_forward_path: str | Path,
    committed_capture_path: str | Path,
) -> tuple[CodexExecClient, B3Preflight]:
    if preflight_reference.sha256 != expected_preflight_sha256:
        raise RuntimeError("B3 preflight differs from the reviewed external trust anchor")
    preflight = B3Preflight.model_validate_json(store.read_bytes(preflight_reference))
    if _file_sha256(account_attestation_path) != preflight.account_attestation_sha256:
        raise RuntimeError("zero-cost account attestation changed after B3 preflight")
    if preflight.resource_amendment_sha256 is None or _file_sha256(resource_amendment_path) != preflight.resource_amendment_sha256:
        raise RuntimeError("D2 resource amendment changed after B3 preflight")
    current_carry_forward = _load_budget_carry_forward(
        budget_carry_forward_path,
        expected_sha256=preflight.budget_carry_forward_document_sha256,
    )
    if current_carry_forward != preflight.budget_carry_forward:
        raise RuntimeError("development budget carry-forward changed after B3 preflight")
    if _file_sha256(preflight.executable) != preflight.executable_sha256:
        raise RuntimeError("Codex executable changed after B3 preflight")
    _summary, current_gate = _current_feature_gate(
        preflight.executable,
        committed_capture_path=committed_capture_path,
    )
    persisted_gate = CodexFeatureGate.model_validate_json(store.read_bytes(preflight.feature_gate))
    if current_gate != persisted_gate:
        raise RuntimeError("Codex feature gate changed after B3 preflight")
    sandbox_sha256 = pilot_sandbox_identity_sha256(sandbox_directory)

    expected_command_specs: dict[str, str] = {}
    for reference in preflight.command_specs:
        spec = CodexCommandSpec.model_validate_json(store.read_bytes(reference))
        if spec.executable != preflight.executable or spec.model_id != preflight.model_id:
            raise RuntimeError("reviewed command spec differs from the B3 preflight identity")
        if spec.pilot_sandbox_sha256 != sandbox_sha256:
            raise RuntimeError("pilot sandbox changed after B3 preflight")
        expected_command_specs[spec.fixture_prompt_sha256] = reference.sha256
    if len(expected_command_specs) != len(preflight.command_specs):
        raise RuntimeError("B3 preflight command prompt hashes are not unique")

    process_runner = SubprocessCodexProcessRunner()
    client = CodexExecClient(
        executable=preflight.executable,
        model_id=preflight.model_id,
        feature_catalog=persisted_gate.feature_catalog,
        expected_feature_catalog_sha256=persisted_gate.feature_catalog_sha256,
        disabled_features=persisted_gate.disabled_features,
        active_feature_allowlist=persisted_gate.active_feature_allowlist,
        post_disable_effective_true_features=persisted_gate.post_disable_effective_true_features,
        config_overrides=CONFIG_OVERRIDES,
        working_directory=sandbox_directory,
        expected_pilot_sandbox_sha256=sandbox_sha256,
        expected_transport_shape_spec_sha256=codex_transport_shape_spec_sha256(),
        timeout_ms=preflight.timeout_ms,
        process_runner=process_runner,
        transport_store=store,
        expected_command_spec_sha256_by_prompt=expected_command_specs,
    )
    return client, preflight
