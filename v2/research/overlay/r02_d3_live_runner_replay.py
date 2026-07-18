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
from .r02_d3_successor_contracts import (
    selector_output_schema,
    validate_openai_strict_json_schema,
)
from .r02_d3_runner_contracts import (
    R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256,
    R02_D3_ACCEPTED_PREFLIGHT_SHA256,
    R02_D3_ACCEPTED_PREREGISTRATION_SHA256,
    R02_D3_EXPECTED_EXECUTABLE_SHA256,
    R02_D3_PREDECESSOR_RUNNER_READINESS_FREEZE_SHA256,
    R02_D3_RUNNER_SOURCE_ROLES,
    R02D3AttemptStarted,
    R02D3AuditAnchor,
    R02D3AuditNode,
    R02D3ContinuationDecision,
    R02D3PrelaunchFailure,
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
    prelaunch_failures: tuple[R02D3PrelaunchFailure, ...]
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
    "prelaunch_failure": R02D3PrelaunchFailure,
    "token_settlement": R02D3TokenSettlement,
    "selector_outcome": R02D3SelectorOutcome,
    "continuation_decision": R02D3ContinuationDecision,
    "run_ledger": R02D3RunLedger,
    "run_terminal": R02D3RunLedger,
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
    prelaunch_failures = tuple(decoded["prelaunch_failure"])
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
    prelaunch_ids = tuple(value.attempt_id for value in prelaunch_failures)
    if len(prelaunch_ids) != len(set(prelaunch_ids)):
        raise R02D3ReplayError("duplicate prelaunch failure identity")
    if set(prelaunch_ids) & (
        set(attempt_ids) | {value.attempt_id for value in reservations}
    ):
        raise R02D3ReplayError("prelaunch failure identity entered launch accounting")
    node_types = latest.node_types
    if node_types[:3] != ("run_authorization", "freeze_identity", "run_plan"):
        raise R02D3ReplayError("audit graph is missing its fixed run preamble")
    authorizations = tuple(decoded["run_authorization"])
    if len(authorizations) != 1:
        raise R02D3ReplayError("audit graph must contain exactly one run authorization")
    authorization = authorizations[0]
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
    ledgers = tuple(decoded["run_ledger"])
    if ledgers:
        latest_ledger = ledgers[-1]
        if latest_ledger.status == "RUNNING":
            checkpoint_attempts = attempts[: latest_ledger.launched_attempt_count]
            checkpoint_attempt_ids = {value.attempt_id for value in checkpoint_attempts}
            checkpoint_settlements = tuple(
                value for value in settlements if value.attempt_id in checkpoint_attempt_ids
            )
            if (
                latest_ledger.reserved_attempt_count
                != latest_ledger.launched_attempt_count
                or latest_ledger.reserved_attempt_count > len(reservations)
                or latest_ledger.launched_attempt_count > len(attempts)
                or latest_ledger.attempted_fixture_ids
                != tuple(value.fixture_id for value in checkpoint_attempts)
                or tuple(
                    value.attempt_id
                    for value in reservations[: latest_ledger.reserved_attempt_count]
                )
                != tuple(value.attempt_id for value in checkpoint_attempts)
                or latest_ledger.settled_attempt_count
                != len([value for value in checkpoint_settlements if value.settled])
                or latest_ledger.unsettled_attempt_count
                != len([value for value in checkpoint_settlements if not value.settled])
                or latest_ledger.debited_tokens
                != sum(value.debit_tokens for value in checkpoint_settlements)
                or (
                    authorization.runner_readiness_freeze_sha256
                    != R02_D3_PREDECESSOR_RUNNER_READINESS_FREEZE_SHA256
                    and latest_ledger.external_provider_calls
                    != (
                        latest_ledger.launched_attempt_count
                        if authorization.mode == "LIVE"
                        else 0
                    )
                )
            ):
                raise R02D3ReplayError(
                    "running ledger is not a valid audit checkpoint prefix"
                )
        elif (
            latest_ledger.reserved_attempt_count != len(reservations)
            or latest_ledger.launched_attempt_count != len(attempts)
            or latest_ledger.settled_attempt_count
            != len([value for value in settlements if value.settled])
            or latest_ledger.unsettled_attempt_count
            != len([value for value in settlements if not value.settled])
            or latest_ledger.debited_tokens
            != sum(value.debit_tokens for value in settlements)
            or (
                authorization.runner_readiness_freeze_sha256
                != R02_D3_PREDECESSOR_RUNNER_READINESS_FREEZE_SHA256
                and latest_ledger.external_provider_calls
                != (len(attempts) if authorization.mode == "LIVE" else 0)
            )
        ):
            raise R02D3ReplayError("terminal ledger does not reconcile with audit accounting")
    if prelaunch_failures:
        if len(prelaunch_failures) != 1 or node_types[-3:] != (
            "prelaunch_failure",
            "run_ledger",
            "run_terminal",
        ):
            raise R02D3ReplayError("prelaunch rejection is not terminalized in the audit chain")
        if not ledgers or ledgers[-1].terminal_code != prelaunch_failures[0].code:
            raise R02D3ReplayError("prelaunch rejection terminal code mismatch")
    if ledgers and ledgers[-1].status != "RUNNING":
        if node_types[-1] != "run_terminal" or node_types[-2] != "run_ledger":
            raise R02D3ReplayError("terminal ledger is missing its terminal anchor payload")
        terminals = tuple(decoded["run_terminal"])
        if len(terminals) != 1 or terminals[0] != ledgers[-1]:
            raise R02D3ReplayError("terminal anchor payload differs from the terminal ledger")

    return R02D3ReplayState(
        anchor=latest,
        authorization=authorization,
        plan=(decoded["run_plan"][0] if decoded["run_plan"] else None),
        reservations=reservations,
        attempts_started=attempts,
        prelaunch_failures=prelaunch_failures,
        settlements=settlements,
        outcomes=tuple(decoded["selector_outcome"]),
        decisions=tuple(decoded["continuation_decision"]),
        ledgers=ledgers,
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
        schema_raw = schema_path.read_bytes()
        schema = json.loads(schema_raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError, json.JSONDecodeError) as exc:
        raise R02D3ReplayError("readiness artifact load failed") from exc
    freeze_sha256 = sha256_hex(freeze_path.read_bytes())
    if manifest.get("runner_readiness_freeze_sha256") != freeze_sha256:
        raise R02D3ReplayError("readiness freeze manifest hash mismatch")
    expected_role_paths = set(R02_D3_RUNNER_SOURCE_ROLES)
    actual_role_paths = {(pin.role, pin.relative_path) for pin in freeze.source_pins}
    if len(freeze.source_pins) != len(expected_role_paths) or actual_role_paths != expected_role_paths:
        raise R02D3ReplayError("runner source pin role or path set mismatch")
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
    if sha256_hex(schema_raw) != freeze.output_schema_sha256:
        raise R02D3ReplayError("selector output schema artifact drift")
    if schema != selector_output_schema():
        raise R02D3ReplayError("selector output schema was not reproduced from source")
    try:
        validate_openai_strict_json_schema(schema)
    except ValueError as exc:
        raise R02D3ReplayError("selector output schema is not provider strict") from exc
    manifest_pins = manifest.get("source_pins")
    expected_manifest_pins = [
        value.model_dump(mode="json") for value in freeze.source_pins
    ]
    if manifest_pins != expected_manifest_pins:
        raise R02D3ReplayError("readiness manifest source pins differ from freeze")
    hardening = manifest.get("live_gate_hardening")
    required_hardening = {
        "provider_compatible_strict_schema_validated",
        "live_submission_accounting_at_launch",
        "predecessor_freeze_preserved_as_sealed_history",
    }
    if not isinstance(hardening, dict) or any(
        hardening.get(key) is not True for key in required_hardening
    ):
        raise R02D3ReplayError("successor live-gate hardening manifest is incomplete")
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
