"""Read-only full replay verifier for the sealed provider-free R02 D4-S2A frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from v2.research.overlay.canonical import canonical_json_bytes, sha256_hex
from v2.research.overlay.r02_audit import R02AppendOnlyArtifactStore
from v2.research.overlay.r02_d4_s2a_frame import (
    DEFAULT_R02_D4_S2A_ARTIFACT_ROOT,
    R02D4S2AFrameError,
    R02D4S2AFrameManifest,
    R02D4S2AFrameSeal,
    verify_intent,
    verify_persisted_frame,
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S2AFrameError(f"expected JSON object: {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    intent = _read_json(repo_root / "docs" / "r02-d4-s2a-frame-intent.json")
    verify_intent(repo_root, intent)
    source_pins = intent.get("source_pins")
    if not isinstance(source_pins, dict):
        raise R02D4S2AFrameError("intent source pins missing")
    extra_sources = {
        "generation_script_sha256": repo_root / "scripts" / "r02_d4_s2a_frame_generate.py",
        "verification_script_sha256": repo_root / "scripts" / "r02_d4_s2a_frame_verify.py",
        "test_source_sha256": repo_root / "v2" / "research" / "overlay" / "test_r02_d4_s2a_frame.py",
    }
    for field, path in extra_sources.items():
        if source_pins.get(field) != sha256_hex(path.read_bytes()):
            raise R02D4S2AFrameError(f"source pin mismatch:{field}")
    manifest_path = repo_root / "docs" / "r02-d4-s2a-frame-manifest.json"
    seal_path = repo_root / "docs" / "r02-d4-s2a-frame-seal.json"
    manifest = R02D4S2AFrameManifest.model_validate(_read_json(manifest_path))
    seal = R02D4S2AFrameSeal.model_validate(_read_json(seal_path))
    store = R02AppendOnlyArtifactStore(DEFAULT_R02_D4_S2A_ARTIFACT_ROOT)
    artifact_manifest = R02D4S2AFrameManifest.model_validate_json(
        store.read_bytes(seal.frame_manifest)
    )
    if canonical_json_bytes(manifest) != canonical_json_bytes(artifact_manifest):
        raise R02D4S2AFrameError("docs and artifact manifests differ")
    verified = verify_persisted_frame(store, seal, reproduce=True)
    print(
        json.dumps(
            {
                "status": "PASS_S2A_PROVIDER_FREE_FRAME_REPRODUCED",
                "frame_id": manifest.frame_id,
                "frame_manifest_sha256": sha256_hex(manifest_path.read_bytes()),
                "frame_seal_sha256": sha256_hex(seal_path.read_bytes()),
                "frame_tree_file_count": seal.full_tree_file_count,
                "frame_tree_sha256": seal.full_tree_sha256,
                "representative_count": verified.representative_count,
                "challenge_count": verified.challenge_count,
                "challenge_scanned_count": verified.challenge_scanned_count,
                "representative_eligible_count": verified.representative_eligible_count,
                "challenge_eligible_count": verified.challenge_eligible_count,
                "total_eligible_count": verified.total_eligible_count,
                "provider_calls": 0,
                "codex_exec_invocations": 0,
                "micro_pilot_executed": False,
                "live_execution": False,
                "retry_count": 0,
                "replacement_count": 0,
                "predecessor_partial_root_reused": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
