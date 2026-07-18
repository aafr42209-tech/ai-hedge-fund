"""Read-only verifier for the sealed provider-free R02 D4-S2 frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from v2.research.overlay.canonical import canonical_json_bytes, sha256_hex
from v2.research.overlay.r02_audit import R02AppendOnlyArtifactStore
from v2.research.overlay.r02_d4_s2_frame import (
    R02_D4_S2_ARTIFACT_ROOT_RELATIVE,
    R02D4S2FrameManifest,
    R02D4S2FrameSeal,
    verify_intent,
    verify_persisted_frame,
)


class R02D4S2VerificationError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S2VerificationError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def verify_frame(repo_root: Path) -> dict[str, Any]:
    intent = _read_json(repo_root / "docs" / "r02-d4-s2-frame-intent.json")
    verify_intent(repo_root, intent)
    source_pins = intent.get("source_pins")
    if not isinstance(source_pins, dict):
        raise R02D4S2VerificationError("INTENT_SOURCE_PINS_MISSING")
    expected_sources = {
        "generation_script_sha256": repo_root / "scripts" / "r02_d4_s2_frame_generate.py",
        "verification_script_sha256": repo_root / "scripts" / "r02_d4_s2_frame_verify.py",
        "test_source_sha256": repo_root / "v2" / "research" / "overlay" / "test_r02_d4_s2_frame.py",
    }
    for field, path in expected_sources.items():
        if source_pins.get(field) != sha256_hex(path.read_bytes()):
            raise R02D4S2VerificationError(f"SOURCE_SHA256_MISMATCH:{field}")
    manifest_path = repo_root / "docs" / "r02-d4-s2-frame-manifest.json"
    seal_path = repo_root / "docs" / "r02-d4-s2-frame-seal.json"
    manifest = R02D4S2FrameManifest.model_validate(_read_json(manifest_path))
    seal = R02D4S2FrameSeal.model_validate(_read_json(seal_path))
    artifact_root = repo_root / R02_D4_S2_ARTIFACT_ROOT_RELATIVE
    store = R02AppendOnlyArtifactStore(artifact_root)
    artifact_manifest = R02D4S2FrameManifest.model_validate_json(
        store.read_bytes(seal.frame_manifest)
    )
    if canonical_json_bytes(manifest) != canonical_json_bytes(artifact_manifest):
        raise R02D4S2VerificationError("DOC_AND_ARTIFACT_MANIFEST_MISMATCH")
    verified = verify_persisted_frame(store, seal, reproduce=True)
    return {
        "schema_version": "r02-d4-s2-frame-verification-v1",
        "status": "PASS_PROVIDER_FREE_FRAME_REPRODUCED",
        "frame_id": verified.frame_id,
        "frame_manifest_sha256": sha256_hex(manifest_path.read_bytes()),
        "frame_seal_sha256": sha256_hex(seal_path.read_bytes()),
        "frame_tree_file_count": seal.full_tree_file_count,
        "frame_tree_sha256": seal.full_tree_sha256,
        "representative_count": verified.representative_count,
        "challenge_count": verified.challenge_count,
        "challenge_scanned_count": verified.challenge_scanned_count,
        "representative_trigger_count": verified.representative_trigger_count,
        "representative_eligible_count": verified.representative_eligible_count,
        "challenge_trigger_count": verified.challenge_trigger_count,
        "challenge_eligible_count": verified.challenge_eligible_count,
        "total_eligible_count": verified.total_eligible_count,
        "provider_calls": 0,
        "codex_exec_invocations": 0,
        "frame_generation": True,
        "frame_scan": True,
        "micro_pilot_executed": False,
        "live_execution": False,
        "retry_count": 0,
        "replacement_count": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = verify_frame(args.repo_root.resolve())
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
