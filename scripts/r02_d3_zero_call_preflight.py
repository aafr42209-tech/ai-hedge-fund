"""Generate the R02 D3 provider-free preregistration/preflight review artifacts."""

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
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    authorization = Path(args.authorization).resolve()
    if not authorization.is_file() or root not in authorization.parents:
        raise ValueError("authorization must be an existing file inside the repository")
    sys.path.insert(0, str(root))

    from v2.research.overlay.canonical import canonical_json_bytes, canonical_sha256
    from v2.research.overlay.r02_audit import R02AppendOnlyArtifactStore
    from v2.research.overlay.r02_d3_contracts import R02D3PersistedPreflight
    from v2.research.overlay.r02_d3_preflight import (
        SubprocessZeroCallRunner,
        build_preregistration,
        build_zero_call_preflight,
        capture_transport_snapshot,
        persist_zero_call_preflight,
    )
    from v2.research.overlay.r02_d3_replay import replay_zero_call_preflight

    authorization_sha256 = hashlib.sha256(authorization.read_bytes()).hexdigest()
    preregistration = build_preregistration(
        root,
        authorization_sha256=authorization_sha256,
    )
    if args.verify_existing:
        existing_preflight = json.loads(
            (root / "docs" / "r02-d3-zero-call-preflight.json").read_text(
                encoding="utf-8"
            )
        )
        preflight_id = existing_preflight["preflight_id"]
        store = R02AppendOnlyArtifactStore(
            root / ".research_artifacts" / preflight_id
        )
        persisted = R02D3PersistedPreflight.model_validate_json(
            (root / "docs" / "r02-d3-zero-call-preflight-anchors.json").read_bytes()
        )
        verification = replay_zero_call_preflight(
            store,
            persisted,
            root,
            authorization_sha256=authorization_sha256,
            expected_preflight_sha256=persisted.preflight.sha256,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            runner=SubprocessZeroCallRunner(preregistration.model_identity),
        )
        print(verification.model_dump_json())
        return 0
    transport = capture_transport_snapshot(
        preregistration,
        SubprocessZeroCallRunner(preregistration.model_identity),
    )
    preflight = build_zero_call_preflight(root, preregistration, transport)
    artifact_root = root / ".research_artifacts" / preflight.preflight_id
    store = R02AppendOnlyArtifactStore(artifact_root)
    persisted = persist_zero_call_preflight(
        store,
        "preflight",
        preregistration,
        transport,
        preflight,
    )
    verification = replay_zero_call_preflight(
        store,
        persisted,
        root,
        authorization_sha256=authorization_sha256,
        expected_preflight_sha256=persisted.preflight.sha256,
        expected_audit_graph_sha256=persisted.audit_graph.sha256,
        runner=SubprocessZeroCallRunner(preregistration.model_identity),
    )
    graph = json.loads(store.read_bytes(persisted.audit_graph))
    preregistration_reference = graph["nodes"][0]
    docs = root / "docs"
    outputs = {
        docs / "r02-d3-preregistration.json": store.read_bytes(
            type(persisted.preflight).model_validate(preregistration_reference)
        ),
        docs / "r02-d3-zero-call-preflight.json": store.read_bytes(persisted.preflight),
        docs / "r02-d3-zero-call-preflight-anchors.json": canonical_json_bytes(persisted),
        docs / "r02-d3-zero-call-preflight-replay.json": canonical_json_bytes(verification),
    }
    review_store = R02AppendOnlyArtifactStore(docs)
    for path, payload in outputs.items():
        review_store.write_bytes(path.name, payload)
    print(
        json.dumps(
            {
                "preflight_id": preflight.preflight_id,
                "preregistration_sha256": canonical_sha256(preregistration),
                "transport_snapshot_sha256": canonical_sha256(transport),
                "preflight_sha256": persisted.preflight.sha256,
                "audit_graph_sha256": persisted.audit_graph.sha256,
                "artifact_root": str(artifact_root),
                "review_artifacts": [str(path) for path in sorted(outputs)],
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
