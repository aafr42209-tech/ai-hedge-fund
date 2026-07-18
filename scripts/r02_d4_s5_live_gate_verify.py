"""Read-only verifier for the R02 D4-S5 execution preflight/live-gate freeze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from v2.research.overlay.canonical import sha256_hex
from v2.research.overlay.r02_d4_s5_live_gate import (
    revalidate_current_identity,
    verify_live_gate_freeze,
)

EXPECTED_FREEZE_SHA256 = (
    "d931edfaa347165975a0edcff1a256f81cd7d56fc7268d7a2a19bf97379f50ab"
)
EXPECTED_FOCUSED_TESTS_SHA256 = (
    "5252ee06f1f1cb588d703292a2ccb2ffc484d11ab98eb4344fc9b0eaf460a07d"
)
EXPECTED_IDENTITY_SNAPSHOT_SHA256 = (
    "248f3683db276d45f275b5a2c236bc02909f6b7bf1be4ff56f6886573b2df5dc"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    freeze_path = repo_root / "docs/r02-d4-s5-live-gate-freeze.json"
    focused_path = repo_root / "docs/r02-d4-s5-focused-tests.json"
    identity_path = repo_root / "docs/r02-d4-s5-execution-identity-snapshot.json"

    if sha256_hex(freeze_path.read_bytes()) != EXPECTED_FREEZE_SHA256:
        raise SystemExit("S5 live-gate freeze byte hash drift")
    if sha256_hex(focused_path.read_bytes()) != EXPECTED_FOCUSED_TESTS_SHA256:
        raise SystemExit("S5 focused-test manifest byte hash drift")
    if sha256_hex(identity_path.read_bytes()) != EXPECTED_IDENTITY_SNAPSHOT_SHA256:
        raise SystemExit("S5 execution-identity snapshot byte hash drift")

    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    verify_live_gate_freeze(repo_root, freeze)
    identity = revalidate_current_identity(repo_root)
    print(
        json.dumps(
            {
                "aggregate_token_cap": freeze["budget_ledger"]["aggregate_token_cap"],
                "codex_exec_invocations": freeze["codex_exec_invocations"],
                "execution_plan_sha256": freeze["execution_order"][
                    "execution_plan_sha256"
                ],
                "expected_collected_tests": 121,
                "fail_closed_attempt_cap": freeze["failure_rate_contract"][
                    "primary_attempt_cap"
                ],
                "fail_closed_rate_cap_ppm": freeze["failure_rate_contract"][
                    "derived_rate_cap_ppm"
                ],
                "identity_capture_summary_sha256": identity[
                    "capture_summary_sha256"
                ],
                "identity_revalidated": True,
                "live_authorization": freeze["live_authorization"],
                "live_execution": freeze["live_execution"],
                "micro_pilot_attempts": freeze["micro_pilot_contract"]["attempt_cap"],
                "per_attempt_live_timeout_ms": freeze["timeout_contract"][
                    "per_attempt_live_timeout_ms"
                ],
                "provider_attempt_cap": freeze["budget_ledger"][
                    "provider_attempt_cap"
                ],
                "provider_calls": freeze["provider_calls"],
                "replacement_count": freeze["replacement_count"],
                "retry_count": freeze["retry_count"],
                "status": "PASS_S5_EXECUTION_PREFLIGHT_LIVE_GATE_REPRODUCED",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
