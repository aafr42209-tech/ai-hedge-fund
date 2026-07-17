"""Append-only hash-chain persistence for R02 D3 production-run attempts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .artifacts import ArtifactError
from .canonical import canonical_sha256
from .contracts import ArtifactReference
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_d3_runner_contracts import R02D3AuditAnchor, R02D3AuditNode


_NODE_TYPE = re.compile(r"^[a-z][a-z0-9_]{2,80}$")


class R02D3AuditError(ArtifactError):
    pass


class R02D3AuditWriter:
    """Writes payload, node, then immutable checkpoint anchor for every append."""

    def __init__(
        self,
        root: str | Path,
        run_id: str,
        *,
        existing_anchor: R02D3AuditAnchor | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.store = R02AppendOnlyArtifactStore(self.root)
        self.run_id = run_id
        if existing_anchor is not None and existing_anchor.run_id != run_id:
            raise R02D3AuditError("resume anchor run identity mismatch")
        self._node_types = list(existing_anchor.node_types) if existing_anchor else []
        self._nodes = list(existing_anchor.nodes) if existing_anchor else []
        self._previous_sha256 = existing_anchor.head_node_sha256 if existing_anchor else None
        self.latest_anchor = existing_anchor

    @property
    def sequence(self) -> int:
        return len(self._nodes)

    @property
    def node_references(self) -> tuple[ArtifactReference, ...]:
        return tuple(self._nodes)

    def append_json(self, node_type: str, value: Any) -> ArtifactReference:
        return self._append(node_type, value=value, raw=None, suffix="json")

    def append_bytes(self, node_type: str, value: bytes, *, suffix: str = "bin") -> ArtifactReference:
        if not isinstance(value, bytes):
            raise TypeError("raw audit payload must be bytes")
        return self._append(node_type, value=None, raw=value, suffix=suffix)

    def _append(
        self,
        node_type: str,
        *,
        value: Any | None,
        raw: bytes | None,
        suffix: str,
    ) -> ArtifactReference:
        if not _NODE_TYPE.fullmatch(node_type):
            raise R02D3AuditError("invalid audit node type")
        sequence = self.sequence + 1
        stem = f"{sequence:05d}-{node_type}"
        if raw is None:
            payload_ref = self.store.write_json(f"payloads/{stem}.json", value)
        else:
            payload_ref = self.store.write_bytes(f"payloads/{stem}.{suffix}", raw)
        node = R02D3AuditNode(
            run_id=self.run_id,
            sequence=sequence,
            node_type=node_type,
            previous_node_sha256=self._previous_sha256,
            payload=payload_ref,
        )
        node_ref = self.store.write_json(f"nodes/{sequence:05d}.json", node)
        if node_ref.sha256 != canonical_sha256(node):
            raise R02D3AuditError("persisted audit node hash mismatch")
        self._node_types.append(node_type)
        self._nodes.append(node_ref)
        self._previous_sha256 = node_ref.sha256
        anchor = R02D3AuditAnchor(
            run_id=self.run_id,
            sequence=sequence,
            node_types=tuple(self._node_types),
            nodes=tuple(self._nodes),
            head_node_sha256=node_ref.sha256,
        )
        self.store.write_json(f"anchors/{sequence:05d}.json", anchor)
        self.latest_anchor = anchor
        return payload_ref


def audit_root_has_files(root: str | Path) -> bool:
    path = Path(root)
    return path.exists() and any(item.is_file() for item in path.rglob("*"))
