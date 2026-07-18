"""One-shot provider-free generation for the authorized R02 D4-S2A frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from v2.research.overlay.canonical import canonical_json_bytes, sha256_hex
from v2.research.overlay.r02_audit import R02AppendOnlyArtifactStore
from v2.research.overlay.r02_d4_s2a_frame import (
    DEFAULT_R02_D4_S2A_ARTIFACT_ROOT,
    R02D4S2AFrameError,
    build_provider_free_frame,
    persist_provider_free_frame,
    verify_intent,
    verify_persisted_frame,
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S2AFrameError(f"expected JSON object: {path}")
    return value


def _write_new(path: Path, value: object) -> None:
    if path.exists():
        raise R02D4S2AFrameError(f"refusing to overwrite: {path}")
    path.write_bytes(canonical_json_bytes(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    intent_path = repo_root / "docs" / "r02-d4-s2a-frame-intent.json"
    artifact_root = repo_root / ".research_artifacts" / "r02-d4-s2a-frame-0716a1b9c13a"
    manifest_output = repo_root / "docs" / "r02-d4-s2a-frame-manifest.json"
    seal_output = repo_root / "docs" / "r02-d4-s2a-frame-seal.json"
    predecessor_root = repo_root / ".research_artifacts" / "r02-d4-frame-0716a1b9c13a"
    if artifact_root.resolve() != DEFAULT_R02_D4_S2A_ARTIFACT_ROOT.resolve():
        raise R02D4S2AFrameError("unexpected S2A artifact root")
    if not predecessor_root.is_dir():
        raise R02D4S2AFrameError("quarantined predecessor root missing")
    for target in (artifact_root, manifest_output, seal_output):
        if target.exists():
            raise R02D4S2AFrameError(f"one-shot target already exists: {target}")
    intent = _read_json(intent_path)
    verify_intent(repo_root, intent)
    build = build_provider_free_frame()
    manifest, seal = persist_provider_free_frame(build, artifact_root=artifact_root)
    verified = verify_persisted_frame(
        R02AppendOnlyArtifactStore(artifact_root), seal, reproduce=False
    )
    _write_new(manifest_output, manifest)
    _write_new(seal_output, seal)
    print(
        json.dumps(
            {
                "status": "PASS_S2A_FRAME_GENERATED_SCANNED_AND_SEALED",
                "frame_id": manifest.frame_id,
                "frame_manifest_sha256": sha256_hex(manifest_output.read_bytes()),
                "frame_seal_sha256": sha256_hex(seal_output.read_bytes()),
                "frame_tree_sha256": seal.full_tree_sha256,
                "representative_count": manifest.representative_count,
                "challenge_count": manifest.challenge_count,
                "challenge_scanned_count": manifest.challenge_scanned_count,
                "total_eligible_count": verified.total_eligible_count,
                "provider_calls": 0,
                "codex_exec_invocations": 0,
                "micro_pilot_executed": False,
                "live_execution": False,
                "retry_count": 0,
                "replacement_count": 0,
                "in_generation_process_full_replay": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
