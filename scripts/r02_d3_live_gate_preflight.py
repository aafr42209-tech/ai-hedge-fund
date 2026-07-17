"""Generate or verify the provider-free R02 D3 live-gate freeze candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--expected-executable-sha256", required=True)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    authorization = Path(args.authorization).resolve()
    if not authorization.is_file() or root not in authorization.parents:
        raise ValueError("authorization must be an existing file inside the repository")
    sys.path.insert(0, str(root))

    from v2.research.overlay.canonical import canonical_json_bytes, canonical_sha256
    from v2.research.overlay.r02_audit import R02AppendOnlyArtifactStore
    from v2.research.overlay.r02_d3_live_gate import (
        R02D3LiveGatePersisted,
        build_live_gate_freeze,
        build_live_gate_preflight,
        persist_live_gate_preflight,
        replay_live_gate_preflight,
    )

    authorization_sha256 = hashlib.sha256(authorization.read_bytes()).hexdigest()
    freeze = build_live_gate_freeze(
        root,
        authorization_sha256=authorization_sha256,
        expected_executable_sha256=args.expected_executable_sha256,
    )
    preflight = build_live_gate_preflight(root, freeze)
    artifact_root = root / ".research_artifacts" / preflight.preflight_id

    if args.verify_existing:
        persisted = R02D3LiveGatePersisted.model_validate_json(
            (root / "docs/r02-d3-live-gate-preflight-anchors.json").read_bytes()
        )
        if persisted.preflight_id != preflight.preflight_id:
            raise ValueError("persisted live-gate preflight identity mismatch")
        store = R02AppendOnlyArtifactStore(artifact_root)
        replay = replay_live_gate_preflight(root, store, persisted)
        print(canonical_json_bytes(replay).decode("utf-8"))
        return 0

    store = R02AppendOnlyArtifactStore(artifact_root)
    persisted = persist_live_gate_preflight(store, freeze, preflight)
    replay = replay_live_gate_preflight(root, store, persisted)
    docs = root / "docs"
    review_store = R02AppendOnlyArtifactStore(docs)
    outputs = {
        "r02-d3-live-gate-freeze-candidate.json": canonical_json_bytes(freeze),
        "r02-d3-live-gate-preflight.json": canonical_json_bytes(preflight),
        "r02-d3-live-gate-preflight-anchors.json": canonical_json_bytes(persisted),
        "r02-d3-live-gate-preflight-replay.json": canonical_json_bytes(replay),
    }
    for relative_path, payload in outputs.items():
        review_store.write_bytes(relative_path, payload)
    print(
        json.dumps(
            {
                "preflight_id": preflight.preflight_id,
                "freeze_sha256": canonical_sha256(freeze),
                "preflight_sha256": canonical_sha256(preflight),
                "artifact_root": str(artifact_root),
                "provider_calls": 0,
                "live_execution": False,
                "micro_pilot_executed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
