"""Append-only payload/node/checkpoint persistence for R02 D4-S6."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .artifacts import ArtifactError
from .canonical import canonical_sha256
from .contracts import ArtifactReference
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_d4_s6_contracts import (
    R02D4S6AuditAnchor,
    R02D4S6AuditNode,
    R02D4S6RunAuthorization,
)


class R02D4S6AuditError(ArtifactError):
    pass


def audit_root_has_files(root: str | Path) -> bool:
    path = Path(root)
    return path.exists() and any(item.is_file() for item in path.rglob("*"))


def validate_s6_artifact_root(
    root: str | Path,
    *,
    repository_root: str | Path,
    authorization: R02D4S6RunAuthorization,
) -> Path:
    """Reject production writes in fake mode and ambiguous production locations."""

    resolved = Path(root).resolve()
    repo = Path(repository_root).resolve()
    protected = (repo / ".research_artifacts").resolve()
    if authorization.mode == "OFFLINE_FAKE":
        if resolved == repo or repo in resolved.parents:
            raise R02D4S6AuditError("offline fake artifact root must be outside the repository")
        if resolved == protected or protected in resolved.parents:
            raise R02D4S6AuditError("offline fake mode cannot target the production artifact tree")
    else:
        expected = (protected / f"r02-d4-s6-{authorization.run_id}").resolve()
        if resolved != expected:
            raise R02D4S6AuditError("LIVE artifact root does not match the single run identity")
    if audit_root_has_files(resolved):
        raise R02D4S6AuditError("S6 audit root is not empty; retry and resume are prohibited")
    return resolved


class R02D4S6AuditWriter:
    """Writes payload, hash-chain node, then immutable checkpoint anchor per append."""

    def __init__(
        self,
        root: str | Path,
        *,
        run_id: str,
        repository_root: str | Path,
        authorization: R02D4S6RunAuthorization,
    ) -> None:
        if authorization.run_id != run_id:
            raise R02D4S6AuditError("audit writer run identity mismatch")
        self.root = validate_s6_artifact_root(
            root,
            repository_root=repository_root,
            authorization=authorization,
        )
        self.run_id = run_id
        self.store = R02AppendOnlyArtifactStore(self.root)
        self._node_types: list[str] = []
        self._nodes: list[ArtifactReference] = []
        self._previous_sha256: str | None = None
        self.latest_anchor: R02D4S6AuditAnchor | None = None

    @property
    def sequence(self) -> int:
        return len(self._nodes)

    @property
    def node_references(self) -> tuple[ArtifactReference, ...]:
        return tuple(self._nodes)

    def append_json(self, node_type: str, value: Any) -> ArtifactReference:
        if re.fullmatch(r"[a-z][a-z0-9_]{2,80}", node_type) is None:
            raise R02D4S6AuditError("invalid audit node type")
        sequence = self.sequence + 1
        stem = f"{sequence:05d}-{node_type}"
        payload_ref = self.store.write_json(f"payloads/{stem}.json", value)
        node = R02D4S6AuditNode(
            run_id=self.run_id,
            sequence=sequence,
            node_type=node_type,
            previous_node_sha256=self._previous_sha256,
            payload=payload_ref,
        )
        node_ref = self.store.write_json(f"nodes/{sequence:05d}.json", node)
        if node_ref.sha256 != canonical_sha256(node):
            raise R02D4S6AuditError("persisted audit node hash mismatch")
        self.store.verify(payload_ref)
        self.store.verify(node_ref)
        self._node_types.append(node_type)
        self._nodes.append(node_ref)
        self._previous_sha256 = node_ref.sha256
        anchor = R02D4S6AuditAnchor(
            run_id=self.run_id,
            sequence=sequence,
            node_types=tuple(self._node_types),
            nodes=tuple(self._nodes),
            head_node_sha256=node_ref.sha256,
        )
        anchor_ref = self.store.write_json(f"anchors/{sequence:05d}.json", anchor)
        if anchor_ref.sha256 != canonical_sha256(anchor):
            raise R02D4S6AuditError("persisted audit anchor hash mismatch")
        self.store.verify(anchor_ref)
        self.latest_anchor = anchor
        return payload_ref
