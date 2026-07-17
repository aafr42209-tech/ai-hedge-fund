"""Fail-closed replay for the R02 D3 production runner audit chain."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .artifacts import ArtifactError
from .canonical import canonical_sha256, sha256_hex
from .contracts import ArtifactReference
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_d3_runner_contracts import (
    R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256,
    R02_D3_ACCEPTED_PREFLIGHT_SHA256,
    R02_D3_ACCEPTED_PREREGISTRATION_SHA256,
    R02_D3_EXPECTED_EXECUTABLE_SHA256,
    R02D3AttemptStarted,
    R02D3AuditAnchor,
    R02D3AuditNode,
    R02D3ContinuationDecision,
    R02D3ReadinessReplayVerification,
    R02D3RunAuthorization,
    R02D3RunLedger,
    R02D3RunPlan,
    R02D3RunnerReadinessFreeze,
    R02D3SelectorOutcome,
    R02D3TokenReservation,
    R02D3TokenSettlement,
)


class R02D3ReplayError(RuntimeError):
    pass


@dataclass(frozen=True)
class R02D3ReplayState:
    anchor: R02D3AuditAnchor
    authorization: R02D3RunAuthorization | None
    plan: R02D3RunPlan | None
    reservations: tuple[R02D3TokenReservation, ...]
    attempts_started: tuple[R02D3AttemptStarted, ...]
    settlements: tuple[R02D3TokenSettlement, ...]
    outcomes: tuple[R02D3SelectorOutcome, ...]
    decisions: tuple[R02D3ContinuationDecision, ...]
    ledgers: tuple[R02D3RunLedger, ...]
    payloads_by_type: dict[str, tuple[bytes, ...]]


_PAYLOAD_MODELS = {
    "run_authorization": R02D3RunAuthorization,
    "run_plan": R02D3RunPlan,
    "token_reservation": R02D3TokenReservation,
    "attempt_started": R02D3AttemptStarted,
    "token_settlement": R02D3TokenSettlement,
    "selector_outcome": R02D3SelectorOutcome,
    "continuation_decision": R02D3ContinuationDecision,
    "run_ledger": R02D3RunLedger,
}


def _reference_for(root: Path, path: Path) -> ArtifactReference:
    raw = path.read_bytes()
    return ArtifactReference(
        relative_path=path.relative_to(root).as_posix(),
        sha256=sha256_hex(raw),
        size_bytes=len(raw),
    )


def replay_audit_root(root: str | Path) -> R02D3ReplayState:
    audit_root = Path(root).resolve()
    anchor_paths = tuple(sorted((audit_root / "anchors").glob("*.json")))
    if not anchor_paths:
        raise R02D3ReplayError("audit root has no checkpoint anchor")
    expected_names = tuple(f"{index:05d}.json" for index in range(1, len(anchor_paths) + 1))
    if tuple(path.name for path in anchor_paths) != expected_names:
        raise R02D3ReplayError("checkpoint anchor sequence has a gap")
    store = R02AppendOnlyArtifactStore(audit_root)
    try:
        anchors = tuple(
            R02D3AuditAnchor.model_validate_json(path.read_bytes()) for path in anchor_paths
        )
    except (OSError, ValidationError) as exc:
        raise R02D3ReplayError("checkpoint anchor validation failed") from exc
    latest = anchors[-1]
    for index, anchor in enumerate(anchors, start=1):
        if anchor.sequence != index:
            raise R02D3ReplayError("checkpoint anchor sequence mismatch")
        if anchor.nodes != latest.nodes[:index] or anchor.node_types != latest.node_types[:index]:
            raise R02D3ReplayError("checkpoint anchor is not an immutable graph prefix")

    payloads: dict[str, list[bytes]] = {}
    previous: str | None = None
    decoded: dict[str, list[object]] = {key: [] for key in _PAYLOAD_MODELS}
    expected_files = {path.relative_to(audit_root).as_posix() for path in anchor_paths}
    try:
        for sequence, (node_type, node_ref) in enumerate(
            zip(latest.node_types, latest.nodes, strict=True), start=1
        ):
            raw_node = store.read_bytes(node_ref)
            node = R02D3AuditNode.model_validate_json(raw_node)
            if node.sequence != sequence or node.node_type != node_type:
                raise R02D3ReplayError("audit node order mismatch")
            if node.run_id != latest.run_id or node.previous_node_sha256 != previous:
                raise R02D3ReplayError("audit node chain mismatch")
            if canonical_sha256(node) != node_ref.sha256:
                raise R02D3ReplayError("audit node canonical hash mismatch")
            payload = store.read_bytes(node.payload)
            payloads.setdefault(node_type, []).append(payload)
            expected_files.add(node_ref.relative_path)
            expected_files.add(node.payload.relative_path)
            model = _PAYLOAD_MODELS.get(node_type)
            if model is not None:
                decoded[node_type].append(model.model_validate_json(payload))
            previous = node_ref.sha256
    except (ArtifactError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, R02D3ReplayError):
            raise
        raise R02D3ReplayError(f"audit graph replay failed: {exc}") from exc
    if previous != latest.head_node_sha256:
        raise R02D3ReplayError("audit graph terminal head mismatch")
    actual_files = {
        path.relative_to(audit_root).as_posix()
        for path in audit_root.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        raise R02D3ReplayError("orphan or partial audit artifact detected")

    reservations = tuple(decoded["token_reservation"])
    attempts = tuple(decoded["attempt_started"])
    settlements = tuple(decoded["token_settlement"])
    attempt_ids = tuple(value.attempt_id for value in attempts)
    if len(attempt_ids) != len(set(attempt_ids)):
        raise R02D3ReplayError("duplicate launched attempt identity")
    settlement_ids = tuple(value.attempt_id for value in settlements)
    if len(settlement_ids) != len(set(settlement_ids)):
        raise R02D3ReplayError("duplicate token settlement identity")
    if not set(attempt_ids).issubset({value.attempt_id for value in reservations}):
        raise R02D3ReplayError("attempt launch has no prior reservation")
    if not set(settlement_ids).issubset(set(attempt_ids)):
        raise R02D3ReplayError("settlement has no launched attempt")
    node_types = latest.node_types
    if node_types[:3] != ("run_authorization", "freeze_identity", "run_plan"):
        raise R02D3ReplayError("audit graph is missing its fixed run preamble")
    reservation_indexes = tuple(
        index for index, value in enumerate(node_types) if value == "token_reservation"
    )
    if len(reservation_indexes) != len(reservations):
        raise R02D3ReplayError("reservation node count mismatch")
    for index in reservation_indexes:
        if index < 2 or node_types[index - 2 : index] != (
            "episode_preparation",
            "prompt_identity",
        ):
            raise R02D3ReplayError("reservation is missing preparation or prompt identity")
    attempt_indexes = tuple(
        index for index, value in enumerate(node_types) if value == "attempt_started"
    )
    for index in attempt_indexes:
        if index == 0 or node_types[index - 1] != "token_reservation":
            raise R02D3ReplayError("attempt launch is not immediately bound to its reservation")
    if node_types.count("episode_preparation") != len(reservations) or node_types.count(
        "prompt_identity"
    ) != len(reservations):
        raise R02D3ReplayError("partial episode preparation graph detected")
    if decoded["run_ledger"] and decoded["run_ledger"][-1].status != "RUNNING":
        if node_types[-1] != "run_terminal" or node_types[-2] != "run_ledger":
            raise R02D3ReplayError("terminal ledger is missing its terminal anchor payload")

    return R02D3ReplayState(
        anchor=latest,
        authorization=(decoded["run_authorization"][0] if decoded["run_authorization"] else None),
        plan=(decoded["run_plan"][0] if decoded["run_plan"] else None),
        reservations=reservations,
        attempts_started=attempts,
        settlements=settlements,
        outcomes=tuple(decoded["selector_outcome"]),
        decisions=tuple(decoded["continuation_decision"]),
        ledgers=tuple(decoded["run_ledger"]),
        payloads_by_type={key: tuple(value) for key, value in payloads.items()},
    )


def verify_readiness_artifacts(repository_root: str | Path) -> R02D3ReadinessReplayVerification:
    root = Path(repository_root).resolve()
    freeze_path = root / "docs/r02-d3-runner-readiness-freeze.json"
    manifest_path = root / "docs/r02-d3-runner-readiness-manifest.json"
    schema_path = root / "docs/r02-d3-selector-output-schema.json"
    try:
        freeze = R02D3RunnerReadinessFreeze.model_validate_json(freeze_path.read_bytes())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError, json.JSONDecodeError) as exc:
        raise R02D3ReplayError("readiness artifact load failed") from exc
    freeze_sha256 = sha256_hex(freeze_path.read_bytes())
    if manifest.get("runner_readiness_freeze_sha256") != freeze_sha256:
        raise R02D3ReplayError("readiness freeze manifest hash mismatch")
    for pin in freeze.source_pins:
        path = root / pin.relative_path
        if not path.is_file() or sha256_hex(path.read_bytes()) != pin.sha256:
            raise R02D3ReplayError(f"runner source pin mismatch: {pin.relative_path}")
    if sha256_hex((root / "docs/r02-d3-live-gate-freeze-candidate.json").read_bytes()) != (
        R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256
    ):
        raise R02D3ReplayError("accepted live-gate freeze artifact drift")
    if sha256_hex((root / "docs/r02-d3-live-gate-preflight.json").read_bytes()) != (
        R02_D3_ACCEPTED_PREFLIGHT_SHA256
    ):
        raise R02D3ReplayError("accepted live-gate preflight artifact drift")
    preregistration_path = root / "docs/r02-d3-preregistration.json"
    if sha256_hex(preregistration_path.read_bytes()) != R02_D3_ACCEPTED_PREREGISTRATION_SHA256:
        raise R02D3ReplayError("accepted preregistration artifact drift")
    from .r02_d3_preflight import R02D3Preregistration

    preregistration = R02D3Preregistration.model_validate_json(
        preregistration_path.read_bytes()
    )
    if canonical_sha256(preregistration.prompt) != freeze.prompt_contract_sha256:
        raise R02D3ReplayError("frozen prompt contract drift")
    if canonical_sha256(preregistration.model_identity) != freeze.model_identity_sha256:
        raise R02D3ReplayError("frozen model identity drift")
    if preregistration.model_identity.executable_sha256 != R02_D3_EXPECTED_EXECUTABLE_SHA256:
        raise R02D3ReplayError("frozen executable identity drift")
    if sha256_hex(schema_path.read_bytes()) != freeze.output_schema_sha256:
        raise R02D3ReplayError("selector output schema artifact drift")
    labels = tuple(manifest.get("zero_call_allowed_command_labels", ()))
    if labels != freeze.zero_call_allowed_command_labels or any("live" in label.lower() for label in labels):
        raise R02D3ReplayError("live argv entered zero-call allowlist")
    commands = manifest.get("zero_call_commands")
    if not isinstance(commands, dict) or set(commands) != set(labels):
        raise R02D3ReplayError("zero-call command map does not match its labels")
    flattened = tuple(
        str(token)
        for argv in commands.values()
        if isinstance(argv, list)
        for token in argv
    )
    if "exec" in flattened or any("--output-schema" == token for token in flattened):
        raise R02D3ReplayError("provider-capable argv entered zero-call command map")
    return R02D3ReadinessReplayVerification(
        freeze_sha256=freeze_sha256,
        verified_source_pins=len(freeze.source_pins),
    )
