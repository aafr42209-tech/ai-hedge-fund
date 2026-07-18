"""Independent fail-closed replay for an R02 D4-S6 audit root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .artifacts import ArtifactIntegrityError
from .canonical import canonical_json_bytes, canonical_sha256
from .contracts import ArtifactReference
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_d4_s6_contracts import (
    R02_D4_S6_ATTEMPT_CAP,
    R02_D4_S6_FAIL_CLOSED_CAP,
    R02_D4_S6_TOKEN_RESERVE,
    R02D4S6AttemptOutcome,
    R02D4S6AttemptStarted,
    R02D4S6AuditAnchor,
    R02D4S6AuditNode,
    R02D4S6ContinuationDecision,
    R02D4S6ContractBinding,
    R02D4S6RunAuthorization,
    R02D4S6RunLedger,
    R02D4S6RunPlan,
    R02D4S6RunTerminal,
    R02D4S6TokenReservation,
    R02D4S6TransportResult,
)


class R02D4S6ReplayError(RuntimeError):
    pass


@dataclass(frozen=True)
class R02D4S6ReplayState:
    authorization: R02D4S6RunAuthorization
    binding: R02D4S6ContractBinding
    plan: R02D4S6RunPlan
    terminal: R02D4S6RunTerminal
    terminal_anchor: R02D4S6AuditAnchor
    node_count: int
    attempted_count: int
    settled_fail_closed_count: int
    unsettled_count: int
    transport_invocations: int
    external_provider_calls: int


def _reference_for(store: R02AppendOnlyArtifactStore, path: Path) -> ArtifactReference:
    return store.reference_for_existing(path.relative_to(store.root).as_posix())


def _load_model(store, reference, model_type):
    raw = store.read_bytes(reference)
    try:
        model = model_type.model_validate_json(raw)
    except (ValidationError, ValueError) as exc:
        raise R02D4S6ReplayError(f"invalid {model_type.__name__} payload: {reference.relative_path}") from exc
    if raw != canonical_json_bytes(model):
        raise R02D4S6ReplayError(f"non-canonical payload bytes: {reference.relative_path}")
    return model


def replay_s6_audit_root(
    root: str | Path,
    *,
    repository_root: str | Path,
    expected_authorization: R02D4S6RunAuthorization | None = None,
    expected_plan: R02D4S6RunPlan | None = None,
    expected_prepared_run=None,
) -> R02D4S6ReplayState:
    audit_root = Path(root).resolve()
    store = R02AppendOnlyArtifactStore(audit_root)
    node_paths = sorted((audit_root / "nodes").glob("*.json"))
    anchor_paths = sorted((audit_root / "anchors").glob("*.json"))
    if not node_paths or len(node_paths) != len(anchor_paths):
        raise R02D4S6ReplayError("node and checkpoint-anchor counts do not reconcile")

    nodes: list[R02D4S6AuditNode] = []
    node_refs: list[ArtifactReference] = []
    payload_refs: list[ArtifactReference] = []
    anchors: list[R02D4S6AuditAnchor] = []
    previous_sha256: str | None = None
    for index, (node_path, anchor_path) in enumerate(zip(node_paths, anchor_paths, strict=True), start=1):
        if node_path.name != f"{index:05d}.json" or anchor_path.name != f"{index:05d}.json":
            raise R02D4S6ReplayError("audit sequence filenames are not contiguous")
        node_ref = _reference_for(store, node_path)
        node = _load_model(store, node_ref, R02D4S6AuditNode)
        if node.sequence != index or node.previous_node_sha256 != previous_sha256:
            raise R02D4S6ReplayError("audit node sequence or hash-chain mismatch")
        expected_payload_name = f"{index:05d}-{node.node_type}.json"
        if Path(node.payload.relative_path).name != expected_payload_name:
            raise R02D4S6ReplayError("audit payload filename does not bind node type")
        store.verify(node.payload)
        nodes.append(node)
        node_refs.append(node_ref)
        payload_refs.append(node.payload)
        previous_sha256 = node_ref.sha256

        anchor_ref = _reference_for(store, anchor_path)
        anchor = _load_model(store, anchor_ref, R02D4S6AuditAnchor)
        if anchor.run_id != node.run_id or anchor.sequence != index:
            raise R02D4S6ReplayError("checkpoint anchor run or sequence mismatch")
        if anchor.node_types != tuple(item.node_type for item in nodes):
            raise R02D4S6ReplayError("checkpoint anchor node-type history mismatch")
        if anchor.nodes != tuple(node_refs) or anchor.head_node_sha256 != node_ref.sha256:
            raise R02D4S6ReplayError("checkpoint anchor node history mismatch")
        anchors.append(anchor)

    if len({ref.relative_path for ref in payload_refs}) != len(payload_refs):
        raise R02D4S6ReplayError("duplicate audit payload reference")
    expected_files = {
        *(ref.relative_path for ref in node_refs),
        *(ref.relative_path for ref in payload_refs),
        *(path.relative_to(audit_root).as_posix() for path in anchor_paths),
    }
    actual_files = {path.relative_to(audit_root).as_posix() for path in audit_root.rglob("*") if path.is_file()}
    if actual_files != expected_files:
        raise R02D4S6ReplayError("audit root contains a missing or orphan artifact")

    node_types = tuple(node.node_type for node in nodes)
    if node_types[:3] != ("run_authorization", "contract_binding", "run_plan"):
        raise R02D4S6ReplayError("audit prefix does not bind authorization, S5, and plan")
    authorization = _load_model(store, nodes[0].payload, R02D4S6RunAuthorization)
    binding = _load_model(store, nodes[1].payload, R02D4S6ContractBinding)
    plan = _load_model(store, nodes[2].payload, R02D4S6RunPlan)
    if expected_authorization is not None and canonical_sha256(authorization) != canonical_sha256(expected_authorization):
        raise R02D4S6ReplayError("run authorization differs from the expected canonical bytes")
    if expected_plan is not None and canonical_sha256(plan) != canonical_sha256(expected_plan):
        raise R02D4S6ReplayError("run plan differs from the expected canonical bytes")

    from .r02_d4_s6_runner import (
        _attempt_id,
        _evaluate_settled_response,
        _usage_status,
        build_provider_free_run_plan,
    )

    rebuilt = build_provider_free_run_plan(repository_root) if expected_prepared_run is None else expected_prepared_run
    if canonical_sha256(rebuilt.plan) != canonical_sha256(plan):
        raise R02D4S6ReplayError("sealed-input plan reconstruction mismatch")
    prepared_by_fixture = {item.planned.fixture_id: item for item in rebuilt.attempts}

    cursor = 3
    reserved_attempts = 0
    reserved_tokens = 0
    settled_attempts = 0
    unsettled_attempts = 0
    settled_fail_closed = 0
    debited_tokens = 0
    attempted: list[str] = []
    external_provider_calls = 0
    latest_ledger: R02D4S6RunLedger | None = None
    terminal: R02D4S6RunTerminal | None = None
    while cursor < len(nodes):
        if nodes[cursor].node_type == "run_terminal":
            terminal = _load_model(store, nodes[cursor].payload, R02D4S6RunTerminal)
            cursor += 1
            break
        block = tuple(node.node_type for node in nodes[cursor : cursor + 6])
        if block != (
            "token_reservation",
            "attempt_started",
            "transport_result",
            "attempt_outcome",
            "continuation_decision",
            "run_ledger",
        ):
            raise R02D4S6ReplayError("attempt audit block is incomplete or reordered")
        if reserved_attempts >= R02_D4_S6_ATTEMPT_CAP:
            raise R02D4S6ReplayError("audit exceeds the 69-attempt cap")
        planned = plan.attempts[reserved_attempts]
        prepared = prepared_by_fixture[planned.fixture_id]
        reservation = _load_model(store, nodes[cursor].payload, R02D4S6TokenReservation)
        started = _load_model(store, nodes[cursor + 1].payload, R02D4S6AttemptStarted)
        transport = _load_model(store, nodes[cursor + 2].payload, R02D4S6TransportResult)
        outcome = _load_model(store, nodes[cursor + 3].payload, R02D4S6AttemptOutcome)
        decision = _load_model(store, nodes[cursor + 4].payload, R02D4S6ContinuationDecision)
        ledger = _load_model(store, nodes[cursor + 5].payload, R02D4S6RunLedger)
        attempt_id = _attempt_id(authorization.run_id, planned)
        identities = (
            reservation.run_id,
            started.run_id,
            transport.run_id,
            outcome.run_id,
            decision.run_id,
            ledger.run_id,
        )
        if identities != (authorization.run_id,) * len(identities):
            raise R02D4S6ReplayError("attempt block run identity mismatch")
        if any(
            item != planned.fixture_id
            for item in (
                reservation.fixture_id,
                started.fixture_id,
                transport.fixture_id,
                outcome.fixture_id,
            )
        ):
            raise R02D4S6ReplayError("attempt block fixture identity mismatch")
        if any(
            item != attempt_id
            for item in (
                reservation.attempt_id,
                started.attempt_id,
                transport.attempt_id,
                outcome.attempt_id,
            )
        ):
            raise R02D4S6ReplayError("attempt block attempt identity mismatch")
        if reservation.execution_ordinal != reserved_attempts or reservation.provider_attempt_ordinal != reserved_attempts + 1 or reservation.reserved_attempts_before != reserved_attempts or reservation.reserved_tokens_before != reserved_tokens or reservation.reserved_tokens_after != reserved_tokens + R02_D4_S6_TOKEN_RESERVE:
            raise R02D4S6ReplayError("attempt reservation does not match replayed ledger")
        if started.reservation_sha256 != canonical_sha256(reservation):
            raise R02D4S6ReplayError("attempt-start record does not bind its reservation")

        reserved_attempts += 1
        reserved_tokens += R02_D4_S6_TOKEN_RESERVE
        attempted.append(planned.fixture_id)
        expected_calls = 1 if authorization.mode == "LIVE" else 0
        if transport.external_provider_calls != expected_calls:
            raise R02D4S6ReplayError("transport call accounting conflicts with authorization")
        external_provider_calls += transport.external_provider_calls
        hard_stop_code, observed_total = _usage_status(transport)
        if hard_stop_code is None:
            assert observed_total is not None and transport.raw_response is not None
            expected_outcome = _evaluate_settled_response(
                run_id=authorization.run_id,
                attempt_id=attempt_id,
                prepared=prepared,
                raw_response=transport.raw_response,
                observed_total_tokens=observed_total,
            )
            if canonical_sha256(expected_outcome) != canonical_sha256(outcome):
                raise R02D4S6ReplayError("settled paired outcome reconstruction mismatch")
            settled_attempts += 1
            debited_tokens += observed_total
            if outcome.baseline_fallback:
                settled_fail_closed += 1
                if settled_fail_closed > R02_D4_S6_FAIL_CLOSED_CAP:
                    hard_stop_code = "SETTLED_FAIL_CLOSED_COUNT_WOULD_EXCEED_6"
        else:
            if outcome.settled or outcome.debit_tokens != R02_D4_S6_TOKEN_RESERVE:
                raise R02D4S6ReplayError("unsettled outcome does not carry the full debit")
            if outcome.error_codes != (hard_stop_code,):
                raise R02D4S6ReplayError("unsettled outcome hard-stop code mismatch")
            unsettled_attempts += 1
            debited_tokens += R02_D4_S6_TOKEN_RESERVE

        expected_action = "HARD_STOP" if hard_stop_code is not None else "COMPLETE" if reserved_attempts == R02_D4_S6_ATTEMPT_CAP else "CONTINUE"
        if decision.after_attempts != reserved_attempts or decision.action != expected_action or decision.hard_stop_code != hard_stop_code or decision.settled_fail_closed_count != settled_fail_closed or decision.unsettled_attempt_count != unsettled_attempts:
            raise R02D4S6ReplayError("continuation decision is not outcome-independent replay")
        expected_status = "INVALID_RUN" if expected_action == "HARD_STOP" else "COMPLETE" if expected_action == "COMPLETE" else "RUNNING"
        expected_ledger = R02D4S6RunLedger(
            run_id=authorization.run_id,
            reserved_attempt_count=reserved_attempts,
            reserved_tokens=reserved_tokens,
            launched_attempt_count=reserved_attempts,
            settled_attempt_count=settled_attempts,
            unsettled_attempt_count=unsettled_attempts,
            settled_fail_closed_count=settled_fail_closed,
            debited_tokens=debited_tokens,
            attempted_fixture_ids=tuple(attempted),
            status=expected_status,
            terminal_code=hard_stop_code,
            transport_invocations=reserved_attempts,
            external_provider_calls=external_provider_calls,
        )
        if canonical_sha256(expected_ledger) != canonical_sha256(ledger):
            raise R02D4S6ReplayError("run ledger reconstruction mismatch")
        latest_ledger = ledger
        cursor += 6
        if expected_action != "CONTINUE":
            if cursor >= len(nodes) or nodes[cursor].node_type != "run_terminal":
                raise R02D4S6ReplayError("terminal continuation decision is not followed by run_terminal")

    if terminal is None or cursor != len(nodes):
        raise R02D4S6ReplayError("audit lacks exactly one final terminal node")
    if latest_ledger is None or canonical_sha256(terminal.final_ledger) != canonical_sha256(latest_ledger):
        raise R02D4S6ReplayError("terminal ledger does not match the replayed ledger")
    if terminal.authorization_sha256 != canonical_sha256(authorization):
        raise R02D4S6ReplayError("terminal authorization digest mismatch")
    if terminal.contract_binding_sha256 != canonical_sha256(binding):
        raise R02D4S6ReplayError("terminal contract-binding digest mismatch")
    if terminal.run_plan_sha256 != canonical_sha256(plan):
        raise R02D4S6ReplayError("terminal run-plan digest mismatch")
    return R02D4S6ReplayState(
        authorization=authorization,
        binding=binding,
        plan=plan,
        terminal=terminal,
        terminal_anchor=anchors[-1],
        node_count=len(nodes),
        attempted_count=reserved_attempts,
        settled_fail_closed_count=settled_fail_closed,
        unsettled_count=unsettled_attempts,
        transport_invocations=reserved_attempts,
        external_provider_calls=external_provider_calls,
    )
