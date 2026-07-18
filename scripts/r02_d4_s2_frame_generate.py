"""One-shot provider-free generation for the accepted R02 D4-S2 frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from v2.research.overlay.canonical import canonical_json_bytes, sha256_hex
from v2.research.overlay.r02_audit import R02AppendOnlyArtifactStore
from v2.research.overlay.r02_d4_s2_frame import (
    DEFAULT_R02_D4_S2_ARTIFACT_ROOT,
    R02_D4_S2_ARTIFACT_ROOT_RELATIVE,
    R02_D4_S2_FRAME_ID,
    R02D4S2FrameError,
    build_provider_free_frame,
    persist_provider_free_frame,
    verify_intent,
    verify_persisted_frame,
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S2FrameError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _write_new(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(canonical_json_bytes(value))
        handle.write(b"\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    intent_path = repo_root / "docs" / "r02-d4-s2-frame-intent.json"
    manifest_output = repo_root / "docs" / "r02-d4-s2-frame-manifest.json"
    seal_output = repo_root / "docs" / "r02-d4-s2-frame-seal.json"
    artifact_root = repo_root / R02_D4_S2_ARTIFACT_ROOT_RELATIVE
    if artifact_root.resolve() != DEFAULT_R02_D4_S2_ARTIFACT_ROOT.resolve():
        raise R02D4S2FrameError("repository root does not match the frozen artifact target")
    for target in (artifact_root, manifest_output, seal_output):
        if target.exists():
            raise R02D4S2FrameError(f"ONE_SHOT_TARGET_ALREADY_EXISTS:{target}")
    intent = _read_json(intent_path)
    verify_intent(repo_root, intent)
    source_pins = intent["source_pins"]
    assert isinstance(source_pins, dict)
    if source_pins.get("generation_script_sha256") != sha256_hex(Path(__file__).read_bytes()):
        raise R02D4S2FrameError("generation script source drift")
    build = build_provider_free_frame()
    manifest, seal = persist_provider_free_frame(build, artifact_root=artifact_root)
    verified = verify_persisted_frame(R02AppendOnlyArtifactStore(artifact_root), seal)
    _write_new(manifest_output, manifest)
    _write_new(seal_output, seal)
    print(
        json.dumps(
            {
                "status": "FRAME_GENERATED_SCANNED_AND_SEALED_PENDING_INDEPENDENT_REVIEW",
                "frame_id": R02_D4_S2_FRAME_ID,
                "frame_manifest_sha256": sha256_hex(manifest_output.read_bytes()),
                "frame_seal_sha256": sha256_hex(seal_output.read_bytes()),
                "frame_tree_sha256": seal.full_tree_sha256,
                "representative_count": verified.representative_count,
                "challenge_count": verified.challenge_count,
                "challenge_scanned_count": verified.challenge_scanned_count,
                "total_eligible_count": verified.total_eligible_count,
                "provider_calls": 0,
                "codex_exec_invocations": 0,
                "frame_generation": True,
                "frame_scan": True,
                "live_execution": False,
                "retry_count": 0,
                "replacement_count": 0,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
