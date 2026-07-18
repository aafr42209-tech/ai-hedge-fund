"""Provider-free preparation gate for a future R02 D4 production entrypoint."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .r02_d3_preflight import R02D3Preregistration
from .r02_d4_s5_live_gate import revalidate_current_identity
from .r02_d4_s6_audit import audit_root_has_files
from .r02_d4_s6_contracts import (
    R02D4S6LiveAuthorizationArtifact,
    R02D4S6RunAuthorization,
)
from .r02_d4_s6_runner import build_provider_free_run_plan, R02D4S6Runner
from .r02_d4_s7_contracts import (
    R02_D4_S7_BASE_COMMIT,
    R02_D4_S7_CAPTURE_SUMMARY_SHA256,
    R02_D4_S7_D3_PREREGISTRATION_SHA256,
    R02_D4_S7_EXECUTABLE_SHA256,
    R02_D4_S7_RESPONSE_SCHEMA_SHA256,
    R02_D4_S7_S5_IDENTITY_SNAPSHOT_SHA256,
    R02D4S7EntrypointGate,
    R02D4S7LiveAuthorizationArtifact,
)
from .r02_d4_s7_transport import (
    R02D4S7CodexTransport,
    R02D4S7GuardedProcessRunner,
    R02D4S7TransportEvidenceStore,
)


class R02D4S7EntrypointError(RuntimeError):
    pass


IdentityRevalidator = Callable[[Path], dict[str, object]]
ExecutableHasher = Callable[[Path], str]
RepositoryStateReader = Callable[[Path], tuple[str, bool]]


def _read_canonical(path: Path, model: type) -> tuple[bytes, object]:
    try:
        raw = path.read_bytes()
        value = model.model_validate_json(raw)
    except Exception as exc:
        raise R02D4S7EntrypointError(f"authorization file is missing or invalid: {path}") from exc
    if raw != canonical_json_bytes(value):
        raise R02D4S7EntrypointError("authorization file is not canonical JSON")
    return raw, value


def _file_sha256(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def _git_repository_state(repo: Path) -> tuple[str, bool]:
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        capture_output=True,
        check=False,
        text=True,
    )
    status = subprocess.run(
        ("git", "status", "--porcelain=v1"),
        cwd=repo,
        capture_output=True,
        check=False,
        text=True,
    )
    if head.returncode != 0 or status.returncode != 0:
        raise R02D4S7EntrypointError("unable to verify production repository state")
    return head.stdout.strip(), not bool(status.stdout.strip())


def _verify_s7_contract(repo: Path, expected_sha256: str) -> None:
    path = repo / "docs/r02-d4-s7-production-gate-contract.json"
    raw = path.read_bytes()
    if sha256_hex(raw) != expected_sha256:
        raise R02D4S7EntrypointError("accepted S7 production-gate contract drift")
    value = json.loads(raw)
    if raw != canonical_json_bytes(value):
        raise R02D4S7EntrypointError("S7 production-gate contract is not canonical")
    if value.get("schema_version") != "r02-d4-s7-production-gate-contract-v1":
        raise R02D4S7EntrypointError("S7 production-gate contract schema drift")
    if value.get("accepted_s6_commit") != R02_D4_S7_BASE_COMMIT:
        raise R02D4S7EntrypointError("S7 contract S6 base-commit drift")
    for section in ("input_pins", "source_pins"):
        entries = value.get(section)
        if not isinstance(entries, list) or not entries:
            raise R02D4S7EntrypointError(f"S7 contract {section} is missing")
        for entry in entries:
            if not isinstance(entry, dict):
                raise R02D4S7EntrypointError(f"S7 contract {section} entry is invalid")
            relative_path = entry.get("relative_path")
            expected = entry.get("sha256")
            if not isinstance(relative_path, str) or not isinstance(expected, str):
                raise R02D4S7EntrypointError(f"S7 contract {section} pin is invalid")
            if _file_sha256(repo / relative_path) != expected:
                raise R02D4S7EntrypointError(f"S7 contract pinned byte drift: {relative_path}")


@dataclass(frozen=True)
class R02D4S7PreparedProductionEntrypoint:
    repository_root: Path
    production_root: Path
    transport_evidence_root: Path
    output_schema_path: Path
    s6_authorization_path: Path
    accepted_s7_commit: str
    authorization: R02D4S6RunAuthorization
    gate: R02D4S7EntrypointGate

    def materialize(self, process_runner: R02D4S7GuardedProcessRunner) -> R02D4S6Runner:
        if getattr(process_runner, "r02_d3_execution_capability", None) != ("LIVE_PROVIDER_PROCESS"):
            raise R02D4S7EntrypointError("production entrypoint requires the explicit LIVE process capability")
        if audit_root_has_files(self.production_root):
            raise R02D4S7EntrypointError("production root is no longer empty; retry and resume are prohibited")
        if audit_root_has_files(self.transport_evidence_root):
            raise R02D4S7EntrypointError("transport evidence root is no longer empty; retry is prohibited")
        current_commit, clean = _git_repository_state(self.repository_root)
        if current_commit != self.accepted_s7_commit or not clean:
            raise R02D4S7EntrypointError("pre-materialization repository commit or clean-state drift")
        current_snapshot = revalidate_current_identity(self.repository_root)
        if current_snapshot.get("capture_summary_sha256") != R02_D4_S7_CAPTURE_SUMMARY_SHA256:
            raise R02D4S7EntrypointError("pre-materialization execution identity drift")
        prereg_path = self.repository_root / "docs/r02-d3-preregistration.json"
        prereg = R02D3Preregistration.model_validate_json(prereg_path.read_bytes())
        if _file_sha256(Path(prereg.model_identity.executable_path).resolve()) != R02_D4_S7_EXECUTABLE_SHA256:
            raise R02D4S7EntrypointError("pre-materialization executable byte identity drift")
        transport = R02D4S7CodexTransport(
            repository_root=self.repository_root,
            output_schema_path=self.output_schema_path,
            process_runner=process_runner,
            evidence_store=R02D4S7TransportEvidenceStore(self.transport_evidence_root),
            live_authorized=True,
        )
        return R02D4S6Runner(
            repository_root=self.repository_root,
            audit_root=self.production_root,
            authorization=self.authorization,
            transport=transport,
            external_live_authorization_path=self.s6_authorization_path,
        )


def prepare_production_entrypoint(
    *,
    repository_root: str | Path,
    run_id: str,
    s6_live_authorization_path: str | Path,
    s7_live_authorization_path: str | Path,
    production_root: str | Path,
    transport_evidence_root: str | Path,
    identity_revalidator: IdentityRevalidator = revalidate_current_identity,
    executable_hasher: ExecutableHasher = _file_sha256,
    repository_state_reader: RepositoryStateReader = _git_repository_state,
) -> R02D4S7PreparedProductionEntrypoint:
    """Verify all provider-free gates without creating a root or starting a process."""

    repo = Path(repository_root).resolve()
    s6_path = Path(s6_live_authorization_path).resolve()
    s7_path = Path(s7_live_authorization_path).resolve()
    root = Path(production_root).resolve()
    evidence_root = Path(transport_evidence_root).resolve()
    expected_root = (repo / ".research_artifacts" / f"r02-d4-s6-{run_id}").resolve()
    if root != expected_root:
        raise R02D4S7EntrypointError("production root differs from the S6 run identity")
    expected_evidence_root = (repo / ".research_artifacts" / f"r02-d4-s7-transport-{run_id}").resolve()
    if evidence_root != expected_evidence_root:
        raise R02D4S7EntrypointError("transport evidence root differs from the S7 run identity")
    if audit_root_has_files(root):
        raise R02D4S7EntrypointError("production root is not empty; retry and resume are prohibited")
    if audit_root_has_files(evidence_root):
        raise R02D4S7EntrypointError("transport evidence root is not empty; retry is prohibited")
    s6_raw, s6_value = _read_canonical(s6_path, R02D4S6LiveAuthorizationArtifact)
    s7_raw, s7_value = _read_canonical(s7_path, R02D4S7LiveAuthorizationArtifact)
    assert isinstance(s6_value, R02D4S6LiveAuthorizationArtifact)
    assert isinstance(s7_value, R02D4S7LiveAuthorizationArtifact)
    if s6_value.run_id != run_id or s7_value.run_id != run_id:
        raise R02D4S7EntrypointError("authorization run identity mismatch")
    if s7_value.s6_live_authorization_sha256 != sha256_hex(s6_raw):
        raise R02D4S7EntrypointError("S7 authorization does not bind the S6 artifact")
    if s7_value.accepted_s6_review_sha256 != s6_value.accepted_s6_review_sha256:
        raise R02D4S7EntrypointError("S6 review identity differs across authorizations")
    if s7_value.accepted_s6_commit != R02_D4_S7_BASE_COMMIT:
        raise R02D4S7EntrypointError("accepted S6 implementation commit drift")
    current_commit, clean = repository_state_reader(repo)
    if current_commit != s7_value.accepted_s7_commit or not clean:
        raise R02D4S7EntrypointError("production repository commit or clean-state does not match authorization")
    _verify_s7_contract(repo, s7_value.accepted_s7_contract_sha256)
    snapshot_path = repo / "docs/r02-d4-s5-execution-identity-snapshot.json"
    if _file_sha256(snapshot_path) != R02_D4_S7_S5_IDENTITY_SNAPSHOT_SHA256:
        raise R02D4S7EntrypointError("S5 identity snapshot byte drift")
    committed_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    current_snapshot = identity_revalidator(repo)
    if current_snapshot != committed_snapshot:
        raise R02D4S7EntrypointError("current D3 execution identity drift")
    if current_snapshot.get("capture_summary_sha256") != R02_D4_S7_CAPTURE_SUMMARY_SHA256:
        raise R02D4S7EntrypointError("current identity capture summary drift")
    prereg_path = repo / "docs/r02-d3-preregistration.json"
    if _file_sha256(prereg_path) != R02_D4_S7_D3_PREREGISTRATION_SHA256:
        raise R02D4S7EntrypointError("D3 preregistration byte drift")
    prereg = R02D3Preregistration.model_validate_json(prereg_path.read_bytes())
    executable = Path(prereg.model_identity.executable_path).resolve()
    if executable_hasher(executable) != R02_D4_S7_EXECUTABLE_SHA256:
        raise R02D4S7EntrypointError("current executable byte identity drift")
    schema_path = (repo / "docs/r02-d4-s7-selector-output-schema.json").resolve()
    if _file_sha256(schema_path) != R02_D4_S7_RESPONSE_SCHEMA_SHA256:
        raise R02D4S7EntrypointError("S7 canonical output schema drift")
    plan = build_provider_free_run_plan(repo)
    authorization = R02D4S6RunAuthorization(
        run_id=run_id,
        mode="LIVE",
        authorization_sha256=canonical_sha256(s6_value),
        artifact_root_kind="PRODUCTION",
        provider_calls_authorized=True,
        production_artifact_root_authorized=True,
        all_69_one_shot_authorized=True,
        live_authorization_artifact=s6_value,
    )
    gate = R02D4S7EntrypointGate(
        run_id=run_id,
        s6_live_authorization_sha256=sha256_hex(s6_raw),
        s7_live_authorization_sha256=sha256_hex(s7_raw),
        prepared_run_plan_sha256=canonical_sha256(plan.plan),
    )
    return R02D4S7PreparedProductionEntrypoint(
        repository_root=repo,
        production_root=root,
        transport_evidence_root=evidence_root,
        output_schema_path=schema_path,
        s6_authorization_path=s6_path,
        accepted_s7_commit=s7_value.accepted_s7_commit,
        authorization=authorization,
        gate=gate,
    )
