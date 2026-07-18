from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from .canonical import canonical_json_bytes, sha256_hex
from .r02_d4_s6_contracts import R02D4S6LiveAuthorizationArtifact
from .r02_d4_s7_contracts import (
    R02_D4_S7_EXECUTABLE_SHA256,
    R02D4S7LiveAuthorizationArtifact,
)
from .r02_d4_s7_entrypoint import prepare_production_entrypoint, R02D4S7EntrypointError
from .test_r02_d4_s7_transport import FakeProcessRunner

ROOT = Path(__file__).resolve().parents[3]


def _identity() -> dict[str, object]:
    value = json.loads((ROOT / "docs/r02-d4-s5-execution-identity-snapshot.json").read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _authorizations(tmp_path: Path, run_id: str) -> tuple[Path, Path]:
    s6 = R02D4S6LiveAuthorizationArtifact(
        authorization_id="r02-d4-live-auth-synthetic-s7-test",
        run_id=run_id,
        accepted_s6_review_sha256="a" * 64,
    )
    s6_raw = canonical_json_bytes(s6)
    s6_path = tmp_path / "synthetic-s6-live-authorization.json"
    s6_path.write_bytes(s6_raw)
    s7 = R02D4S7LiveAuthorizationArtifact(
        authorization_id="r02-d4-s7-live-auth-synthetic-test",
        run_id=run_id,
        accepted_s6_review_sha256="a" * 64,
        accepted_s7_commit="c" * 40,
        accepted_s7_review_sha256="b" * 64,
        accepted_s7_contract_sha256=sha256_hex((ROOT / "docs/r02-d4-s7-production-gate-contract.json").read_bytes()),
        s6_live_authorization_sha256=sha256_hex(s6_raw),
    )
    s7_path = tmp_path / "synthetic-s7-live-authorization.json"
    s7_path.write_bytes(canonical_json_bytes(s7))
    return s6_path, s7_path


def _prepare(tmp_path: Path, *, identity: dict[str, object] | None = None):
    run_id = "r02-d4-s7-synthetic-gate"
    s6_path, s7_path = _authorizations(tmp_path, run_id)
    root = ROOT / ".research_artifacts" / f"r02-d4-s6-{run_id}"
    evidence_root = ROOT / ".research_artifacts" / f"r02-d4-s7-transport-{run_id}"
    prepared = prepare_production_entrypoint(
        repository_root=ROOT,
        run_id=run_id,
        s6_live_authorization_path=s6_path,
        s7_live_authorization_path=s7_path,
        production_root=root,
        transport_evidence_root=evidence_root,
        identity_revalidator=lambda _: identity or _identity(),
        executable_hasher=lambda _: R02_D4_S7_EXECUTABLE_SHA256,
        repository_state_reader=lambda _: ("c" * 40, True),
    )
    return prepared, s6_path, s7_path, root, evidence_root


def test_provider_free_gate_prepares_without_materializing_production_root(
    tmp_path: Path,
) -> None:
    prepared, _, _, root, evidence_root = _prepare(tmp_path)
    assert prepared.gate.status == "PASS_PROVIDER_FREE_PRODUCTION_ENTRYPOINT_PREPARED"
    assert prepared.gate.attempt_cap == 69
    assert prepared.gate.aggregate_token_cap == 2_208_000
    assert prepared.gate.timeout_ms == 900_000
    assert prepared.gate.fail_closed_cap == 6
    assert prepared.gate.micro_pilot_attempts == 0
    assert prepared.gate.retry_cap == 0
    assert prepared.gate.replacement_cap == 0
    assert prepared.gate.resume_cap == 0
    assert prepared.gate.production_root_materialized is False
    assert prepared.gate.transport_evidence_root_materialized is False
    assert prepared.gate.provider_process_started is False
    assert not root.exists()
    assert not evidence_root.exists()


def test_materialize_rejects_fake_process_capability_before_root_creation(
    tmp_path: Path,
) -> None:
    prepared, _, _, root, evidence_root = _prepare(tmp_path)
    with pytest.raises(R02D4S7EntrypointError, match="LIVE process capability"):
        prepared.materialize(FakeProcessRunner())
    assert not root.exists()
    assert not evidence_root.exists()


def test_wrong_production_root_is_rejected(tmp_path: Path) -> None:
    run_id = "r02-d4-s7-synthetic-wrong-root"
    s6_path, s7_path = _authorizations(tmp_path, run_id)
    with pytest.raises(R02D4S7EntrypointError, match="production root"):
        prepare_production_entrypoint(
            repository_root=ROOT,
            run_id=run_id,
            s6_live_authorization_path=s6_path,
            s7_live_authorization_path=s7_path,
            production_root=tmp_path / "wrong-root",
            transport_evidence_root=tmp_path / "wrong-evidence-root",
            identity_revalidator=lambda _: _identity(),
            executable_hasher=lambda _: R02_D4_S7_EXECUTABLE_SHA256,
            repository_state_reader=lambda _: ("c" * 40, True),
        )


def test_noncanonical_authorization_is_rejected(tmp_path: Path) -> None:
    run_id = "r02-d4-s7-synthetic-noncanonical"
    s6_path, s7_path = _authorizations(tmp_path, run_id)
    s7_path.write_bytes(s7_path.read_bytes() + b"\n")
    root = ROOT / ".research_artifacts" / f"r02-d4-s6-{run_id}"
    evidence_root = ROOT / ".research_artifacts" / f"r02-d4-s7-transport-{run_id}"
    with pytest.raises(R02D4S7EntrypointError, match="canonical"):
        prepare_production_entrypoint(
            repository_root=ROOT,
            run_id=run_id,
            s6_live_authorization_path=s6_path,
            s7_live_authorization_path=s7_path,
            production_root=root,
            transport_evidence_root=evidence_root,
            identity_revalidator=lambda _: _identity(),
            executable_hasher=lambda _: R02_D4_S7_EXECUTABLE_SHA256,
            repository_state_reader=lambda _: ("c" * 40, True),
        )


def test_s7_authorization_must_bind_exact_s6_artifact(tmp_path: Path) -> None:
    run_id = "r02-d4-s7-synthetic-auth-drift"
    s6_path, s7_path = _authorizations(tmp_path, run_id)
    value = json.loads(s7_path.read_text(encoding="utf-8"))
    value["s6_live_authorization_sha256"] = "c" * 64
    s7_path.write_bytes(canonical_json_bytes(value))
    root = ROOT / ".research_artifacts" / f"r02-d4-s6-{run_id}"
    evidence_root = ROOT / ".research_artifacts" / f"r02-d4-s7-transport-{run_id}"
    with pytest.raises(R02D4S7EntrypointError, match="bind"):
        prepare_production_entrypoint(
            repository_root=ROOT,
            run_id=run_id,
            s6_live_authorization_path=s6_path,
            s7_live_authorization_path=s7_path,
            production_root=root,
            transport_evidence_root=evidence_root,
            identity_revalidator=lambda _: _identity(),
            executable_hasher=lambda _: R02_D4_S7_EXECUTABLE_SHA256,
            repository_state_reader=lambda _: ("c" * 40, True),
        )


def test_current_identity_drift_is_rejected(tmp_path: Path) -> None:
    identity = copy.deepcopy(_identity())
    identity["capture_summary_sha256"] = "d" * 64
    with pytest.raises(R02D4S7EntrypointError, match="identity drift"):
        _prepare(tmp_path, identity=identity)


def test_current_executable_drift_is_rejected(tmp_path: Path) -> None:
    run_id = "r02-d4-s7-synthetic-executable-drift"
    s6_path, s7_path = _authorizations(tmp_path, run_id)
    root = ROOT / ".research_artifacts" / f"r02-d4-s6-{run_id}"
    evidence_root = ROOT / ".research_artifacts" / f"r02-d4-s7-transport-{run_id}"
    with pytest.raises(R02D4S7EntrypointError, match="executable"):
        prepare_production_entrypoint(
            repository_root=ROOT,
            run_id=run_id,
            s6_live_authorization_path=s6_path,
            s7_live_authorization_path=s7_path,
            production_root=root,
            transport_evidence_root=evidence_root,
            identity_revalidator=lambda _: _identity(),
            executable_hasher=lambda _: "e" * 64,
            repository_state_reader=lambda _: ("c" * 40, True),
        )


def test_test_authorizations_are_temp_only_and_not_repo_artifacts(
    tmp_path: Path,
) -> None:
    _, s6_path, s7_path, _, _ = _prepare(tmp_path)
    assert tmp_path in s6_path.parents
    assert tmp_path in s7_path.parents
    assert ROOT not in s6_path.parents
    assert ROOT not in s7_path.parents
