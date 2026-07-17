"""Generate or verify R02 D3 production-runner zero-call readiness artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


SOURCE_ROLES = (
    ("RUNNER_CONTRACTS", "v2/research/overlay/r02_d3_runner_contracts.py"),
    ("SELECTOR_TRANSPORT_ADAPTER", "v2/research/overlay/r02_d3_live_selector_adapter.py"),
    ("FIFTY_FIVE_ATTEMPT_ORCHESTRATOR", "v2/research/overlay/r02_d3_live_orchestrator.py"),
    ("APPEND_ONLY_AUDIT", "v2/research/overlay/r02_d3_live_audit.py"),
    ("FAIL_CLOSED_REPLAY", "v2/research/overlay/r02_d3_live_runner_replay.py"),
    ("ZERO_CALL_READINESS_SCRIPT", "scripts/r02_d3_live_runner_readiness.py"),
)
ZERO_CALL_LABELS = ("PYTEST_OFFLINE_FAKE", "VERIFY_EXISTING_READINESS")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new_or_equal(path: Path, payload: bytes) -> None:
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"refusing to replace an existing readiness artifact: {path}")
        return
    path.write_bytes(payload)


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
    from v2.research.overlay.r02_d3_contracts import selector_output_schema
    from v2.research.overlay.r02_d3_live_orchestrator import load_accepted_preregistration
    from v2.research.overlay.r02_d3_live_runner_replay import verify_readiness_artifacts
    from v2.research.overlay.r02_d3_runner_contracts import (
        R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256,
        R02_D3_ACCEPTED_PREFLIGHT_SHA256,
        R02_D3_EXPECTED_EXECUTABLE_SHA256,
        R02D3RunnerReadinessFreeze,
        R02D3RunnerSourcePin,
    )

    if args.expected_executable_sha256 != R02_D3_EXPECTED_EXECUTABLE_SHA256:
        raise ValueError("externally supplied executable pin differs from accepted D3")
    accepted_freeze = root / "docs/r02-d3-live-gate-freeze-candidate.json"
    accepted_preflight = root / "docs/r02-d3-live-gate-preflight.json"
    if _sha256(accepted_freeze) != R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256:
        raise ValueError("accepted live-gate freeze identity drift")
    if _sha256(accepted_preflight) != R02_D3_ACCEPTED_PREFLIGHT_SHA256:
        raise ValueError("accepted live-gate preflight identity drift")
    preflight = json.loads(accepted_preflight.read_text(encoding="utf-8"))
    if (
        preflight.get("expected_executable_sha256") != R02_D3_EXPECTED_EXECUTABLE_SHA256
        or preflight.get("observed_executable_sha256") != R02_D3_EXPECTED_EXECUTABLE_SHA256
    ):
        raise ValueError("accepted executable binding drift")

    docs = root / "docs"
    schema_path = docs / "r02-d3-selector-output-schema.json"
    freeze_path = docs / "r02-d3-runner-readiness-freeze.json"
    manifest_path = docs / "r02-d3-runner-readiness-manifest.json"
    replay_path = docs / "r02-d3-runner-readiness-replay.json"
    if args.verify_existing:
        verification = verify_readiness_artifacts(root)
        if replay_path.read_bytes() != canonical_json_bytes(verification):
            raise ValueError("readiness replay artifact drift")
        print(canonical_json_bytes(verification).decode("utf-8"))
        return 0

    schema_bytes = canonical_json_bytes(selector_output_schema())
    source_pins = tuple(
        R02D3RunnerSourcePin(
            role=role,
            relative_path=relative_path,
            sha256=_sha256(root / relative_path),
        )
        for role, relative_path in SOURCE_ROLES
    )
    preregistration = load_accepted_preregistration(root)
    freeze = R02D3RunnerReadinessFreeze(
        authorization_sha256=_sha256(authorization),
        output_schema_sha256=hashlib.sha256(schema_bytes).hexdigest(),
        prompt_contract_sha256=canonical_sha256(preregistration.prompt),
        model_identity_sha256=canonical_sha256(preregistration.model_identity),
        source_pins=source_pins,
        zero_call_allowed_command_labels=ZERO_CALL_LABELS,
    )
    freeze_bytes = canonical_json_bytes(freeze)
    freeze_sha256 = hashlib.sha256(freeze_bytes).hexdigest()
    manifest = {
        "schema_version": "r02-d3-runner-readiness-manifest-v1",
        "status": "READY_FOR_INDEPENDENT_REVIEW_NOT_LIVE_AUTHORIZED",
        "runner_readiness_freeze_sha256": freeze_sha256,
        "accepted_live_gate_freeze_sha256": R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256,
        "accepted_preflight_sha256": R02_D3_ACCEPTED_PREFLIGHT_SHA256,
        "expected_executable_sha256": R02_D3_EXPECTED_EXECUTABLE_SHA256,
        "selector_output_schema_sha256": freeze.output_schema_sha256,
        "source_pins": [value.model_dump(mode="json") for value in source_pins],
        "zero_call_allowed_command_labels": list(ZERO_CALL_LABELS),
        "zero_call_commands": {
            "PYTEST_OFFLINE_FAKE": [
                ".venv/Scripts/python.exe",
                "-m",
                "pytest",
                "-q",
                "v2/research/overlay/test_r02_d3_live_runner.py",
            ],
            "VERIFY_EXISTING_READINESS": [
                ".venv/Scripts/python.exe",
                "scripts/r02_d3_live_runner_readiness.py",
                "--verify-existing",
            ],
        },
        "live_argv_allowed_by_zero_call": False,
        "provider_calls": 0,
        "live_execution": False,
        "micro_pilot_executed": False,
        "full_6_plus_49_executed": False,
    }
    _write_new_or_equal(schema_path, schema_bytes)
    _write_new_or_equal(freeze_path, freeze_bytes)
    _write_new_or_equal(manifest_path, canonical_json_bytes(manifest))
    verification = verify_readiness_artifacts(root)
    _write_new_or_equal(replay_path, canonical_json_bytes(verification))
    print(
        json.dumps(
            {
                "freeze_sha256": freeze_sha256,
                "verified_source_pins": len(source_pins),
                "provider_calls": 0,
                "live_execution": False,
                "micro_pilot_executed": False,
                "full_6_plus_49_executed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
