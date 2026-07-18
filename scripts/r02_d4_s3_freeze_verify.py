"""Read-only provider-free verifier for the R02 D4-S3 statistical freeze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from v2.research.overlay.canonical import sha256_hex
from v2.research.overlay.r02_d4_s3_freeze import (
    R02D4S3FreezeError,
    bootstrap_seed_integer_decimal,
    bootstrap_seed_sha256,
    verify_freeze,
)


FREEZE_SHA256 = "3538c09ffedd95f946a448ae298e04cad1cf933a99ff767b58472c4285c6b449"
FOCUSED_TEST_MANIFEST_SHA256 = (
    "a5dbf246e109ffcb907456c8ab16673d48bbd10638a7620555679d6d8c825716"
)


def _read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S3FreezeError(f"expected JSON object:{path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    freeze_path = repo_root / "docs" / "r02-d4-s3-statistical-freeze.json"
    test_manifest_path = repo_root / "docs" / "r02-d4-s3-focused-tests.json"
    if sha256_hex(freeze_path.read_bytes()) != FREEZE_SHA256:
        raise R02D4S3FreezeError("statistical freeze byte hash drift")
    if sha256_hex(test_manifest_path.read_bytes()) != FOCUSED_TEST_MANIFEST_SHA256:
        raise R02D4S3FreezeError("focused test manifest byte hash drift")
    freeze = _read_object(freeze_path)
    verify_freeze(repo_root, freeze)
    print(
        json.dumps(
            {
                "status": "PASS_S3_STATISTICAL_FREEZE_REPRODUCED",
                "freeze_sha256": FREEZE_SHA256,
                "focused_test_manifest_sha256": FOCUSED_TEST_MANIFEST_SHA256,
                "expected_collected_tests": 77,
                "frame_id": freeze["frame_id"],
                "frame_tree_sha256": freeze["frame_tree_sha256"],
                "total_n": freeze["total_n"],
                "total_eligible_count": freeze["total_eligible_count"],
                "m_min": freeze["m_min"],
                "bootstrap_seed_sha256": bootstrap_seed_sha256(),
                "bootstrap_seed_integer_decimal": bootstrap_seed_integer_decimal(),
                "provider_calls": 0,
                "codex_exec_invocations": 0,
                "micro_pilot_executed": False,
                "live_execution": False,
                "provider_budget_created": False,
                "live_authorization_created": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
