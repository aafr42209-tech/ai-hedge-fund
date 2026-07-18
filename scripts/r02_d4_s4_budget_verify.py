"""Read-only verifier for the R02 D4-S4 provider-budget freeze draft."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from v2.research.overlay.canonical import sha256_hex
from v2.research.overlay.r02_d4_s4_budget import verify_freeze

EXPECTED_FREEZE_SHA256 = (
    "722eb1aee9e115c76990387f7baf8a19dbfd66226ebaae4060acf29f1bf74e70"
)
EXPECTED_FOCUSED_TESTS_SHA256 = (
    "c1505d9e36b02bf1c4bb6263a2811ab338bc35278cb563bec8942ea445fe58e8"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    freeze_path = repo_root / "docs/r02-d4-s4-provider-budget-freeze.json"
    focused_path = repo_root / "docs/r02-d4-s4-focused-tests.json"

    freeze_sha256 = sha256_hex(freeze_path.read_bytes())
    focused_sha256 = sha256_hex(focused_path.read_bytes())
    if freeze_sha256 != EXPECTED_FREEZE_SHA256:
        raise SystemExit("S4 provider-budget freeze byte hash drift")
    if focused_sha256 != EXPECTED_FOCUSED_TESTS_SHA256:
        raise SystemExit("S4 focused-test manifest byte hash drift")

    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    verify_freeze(repo_root, freeze)
    budget = freeze["provider_budget"]
    print(
        json.dumps(
            {
                "aggregate_token_cap": budget["aggregate_token_cap"],
                "codex_exec_invocations": freeze["codex_exec_invocations"],
                "eligible_episode_count": budget["eligible_episode_count"],
                "expected_collected_tests": 97,
                "frame_id": freeze["frame_id"],
                "live_authorization_created": freeze["live_authorization_created"],
                "live_execution": freeze["live_execution"],
                "maximum_draft_prompt_utf8_bytes": budget[
                    "maximum_draft_prompt_utf8_bytes"
                ],
                "maximum_selector_payload_utf8_bytes": budget[
                    "maximum_selector_payload_utf8_bytes"
                ],
                "per_attempt_token_reserve": budget["per_attempt_token_reserve"],
                "provider_attempt_cap": budget["provider_attempt_cap"],
                "provider_calls": freeze["provider_calls"],
                "replacement_count": freeze["replacement_count"],
                "retry_count": freeze["retry_count"],
                "seal_retry_count_verified": freeze[
                    "retry_and_replacement_contract"
                ]["seal_retry_count"]
                == 0,
                "status": "PASS_S4_PROVIDER_BUDGET_FREEZE_REPRODUCED",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
