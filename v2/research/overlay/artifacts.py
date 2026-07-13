"""Append-only, hash-verified artifact persistence for R01."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, sha256_hex
from .contracts import ArtifactReference

DEFAULT_ARTIFACT_ROOT = Path(".research_artifacts/r01")


class ArtifactError(RuntimeError):
    pass


class ArtifactExistsError(ArtifactError):
    pass


class ArtifactIntegrityError(ArtifactError):
    pass


class AppendOnlyArtifactStore:
    def __init__(self, root: str | Path = DEFAULT_ARTIFACT_ROOT) -> None:
        self.root = Path(root).resolve()

    def _resolve(self, relative_path: str) -> Path:
        reference = ArtifactReference(relative_path=relative_path, sha256="0" * 64, size_bytes=0)
        path = (self.root / reference.relative_path).resolve()
        if path != self.root and self.root not in path.parents:
            raise ArtifactError("artifact path escapes the configured root")
        return path

    def write_bytes(self, relative_path: str, content: bytes) -> ArtifactReference:
        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise ArtifactExistsError(f"artifact already exists: {relative_path}") from exc
        return ArtifactReference(
            relative_path=relative_path.replace("\\", "/"),
            sha256=sha256_hex(content),
            size_bytes=len(content),
        )

    def write_text(self, relative_path: str, content: str) -> ArtifactReference:
        return self.write_bytes(relative_path, content.encode("utf-8"))

    def write_json(self, relative_path: str, value: Any) -> ArtifactReference:
        return self.write_bytes(relative_path, canonical_json_bytes(value))

    def read_bytes(self, reference: ArtifactReference) -> bytes:
        path = self._resolve(reference.relative_path)
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise ArtifactIntegrityError(f"missing artifact: {reference.relative_path}") from exc
        if len(content) != reference.size_bytes or sha256_hex(content) != reference.sha256:
            raise ArtifactIntegrityError(f"artifact hash mismatch: {reference.relative_path}")
        return content

    def reference_for_existing(self, relative_path: str) -> ArtifactReference:
        path = self._resolve(relative_path)
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise ArtifactIntegrityError(f"missing artifact: {relative_path}") from exc
        return ArtifactReference(
            relative_path=relative_path.replace("\\", "/"),
            sha256=sha256_hex(content),
            size_bytes=len(content),
        )

    def read_json(self, reference: ArtifactReference) -> Any:
        import json

        try:
            return json.loads(self.read_bytes(reference))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArtifactIntegrityError(f"invalid JSON artifact: {reference.relative_path}") from exc

    def verify(self, reference: ArtifactReference) -> None:
        self.read_bytes(reference)
