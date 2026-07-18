"""Additive read-only replay verifier for the already sealed R02 D4-S2A frame.

The pre-generation verifier remains byte-pinned. This verifier corrects only its
strict Python list-vs-tuple JSON parsing boundary by validating JSON bytes.
"""

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


PRE_GENERATION_VERIFIER_SHA256 = (
    "b18863976a756eddfc151b2173a14c8ce68414f16f4ff2abfff5902ea6b876cf"
)


def _read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S2AFrameError(f"expected JSON object: {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    intent_path = repo_root / "docs" / "r02-d4-s2a-frame-intent.json"
    intent = _read_object(intent_path)
    verify_intent(repo_root, intent)
    source_pins = intent.get("source_pins")
    if not isinstance(source_pins, dict):
        raise R02D4S2AFrameError("intent source pins missing")
    pre_generation_sources = {
        "generation_script_sha256": repo_root / "scripts" / "r02_d4_s2a_frame_generate.py",
        "verification_script_sha256": repo_root / "scripts" / "r02_d4_s2a_frame_verify.py",
        "test_source_sha256": repo_root / "v2" / "research" / "overlay" / "test_r02_d4_s2a_frame.py",
    }
    for field, path in pre_generation_sources.items():
        observed = sha256_hex(path.read_bytes())
        if source_pins.get(field) != observed:
            raise R02D4S2AFrameError(f"pre-generation source pin mismatch:{field}")
    if source_pins.get("verification_script_sha256") != PRE_GENERATION_VERIFIER_SHA256:
        raise R02D4S2AFrameError("pre-generation verifier identity mismatch")
    manifest_path = repo_root / "docs" / "r02-d4-s2a-frame-manifest.json"
    seal_path = repo_root / "docs" / "r02-d4-s2a-frame-seal.json"
    manifest = R02D4S2AFrameManifest.model_validate_json(manifest_path.read_bytes())
    seal = R02D4S2AFrameSeal.model_validate_json(seal_path.read_bytes())
    store = R02AppendOnlyArtifactStore(DEFAULT_R02_D4_S2A_ARTIFACT_ROOT)
    artifact_manifest_bytes = store.read_bytes(seal.frame_manifest)
    artifact_manifest = R02D4S2AFrameManifest.model_validate_json(artifact_manifest_bytes)
    if canonical_json_bytes(manifest) != canonical_json_bytes(artifact_manifest):
        raise R02D4S2AFrameError("docs and artifact manifests differ")
    verified = verify_persisted_frame(store, seal, reproduce=True)
    print(
        json.dumps(
            {
                "status": "PASS_S2A_PROVIDER_FREE_FRAME_REPRODUCED_ADDITIVE_VERIFIER",
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
                "generation_attempt_count": 1,
                "generation_retry_count": 0,
                "read_only_replay_attempt_count": 2,
                "predecessor_partial_root_reused": False,
                "pre_generation_verifier_sha256": PRE_GENERATION_VERIFIER_SHA256,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
