"""Provider-free R02 D4-S4 provider-budget freeze and verifier."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_sha256, sha256_hex
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_d3_preflight import _filesystem_tree
from .r02_d4_s2a_frame import (
    DEFAULT_R02_D4_S2A_ARTIFACT_ROOT,
    R02D4S2AFrameManifest,
)
from .r02_statistics import R02ProviderBudgetFreeze, _prompt_budget_evidence

ROOT = Path(__file__).resolve().parents[3]
R02_D4_S4_BASE_COMMIT = "277d4e4d8f67f46572df073413c21b49f551f189"
R02_D4_S4_FRAME_ID = "r02-d4-s2a-frame-0716a1b9c13a"
R02_D4_S4_S2A_INTENT_SHA256 = (
    "f126fd3da9167aa6982ed40514e14019a2ed64a7de16d001cc5a914f2438f04c"
)
R02_D4_S4_FRAME_MANIFEST_SHA256 = (
    "368e01509b04a53928df2d729f0914dbd0c1ee14c5221a6e189fbf7b8bfa4ba1"
)
R02_D4_S4_FRAME_SEAL_SHA256 = (
    "40aec915d3d24598ad2cbc46713a949b8c8ee5401d5768695b9be918b8bb5838"
)
R02_D4_S4_FRAME_TREE_SHA256 = (
    "65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29"
)
R02_D4_S4_FRAME_TREE_FILE_COUNT = 202
R02_D4_S4_S3_FREEZE_SHA256 = (
    "3538c09ffedd95f946a448ae298e04cad1cf933a99ff767b58472c4285c6b449"
)
R02_D4_S4_S3_FOCUSED_TESTS_SHA256 = (
    "a5dbf246e109ffcb907456c8ab16673d48bbd10638a7620555679d6d8c825716"
)
R02_D4_S4_S3_ZERO_CALL_SHA256 = (
    "a25f1dd3744e9ae4500c429c5e5e4e4082a163ead504561df00eff1931375afd"
)
R02_D4_S4_ACCEPTED_DESIGN_SHA256 = (
    "784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900"
)
R02_D4_S4_D3_PREREGISTRATION_SHA256 = (
    "5e07d88e98e74f67a1377020ca8c19c6fada51756ebddd902706a1680eeb27d4"
)
R02_D4_S4_STATISTICS_SOURCE_SHA256 = (
    "9e051dbe7a64f434811fcafc1c1ce26013c14076214e959d884fb961a3d771fb"
)
R02_D4_S4_CANDIDATES_SOURCE_SHA256 = (
    "29c13547230d1729d8b9cec637ccb13335fbcae52c1360e63718359d993a320e"
)
R02_D4_S4_SELECTOR_SOURCE_SHA256 = (
    "a90cc600ffc772c5fb4b1c964b5efc0a551de84a41eaa5c0a030b6d02b9b20f9"
)
R02_D4_S4_CANONICAL_SOURCE_SHA256 = (
    "a00f6b3b2d623d7da54a6e6e3bbc243d9f9de8b151bef3268f0ea9a8c5166671"
)
R02_D4_S4_S2A_SOURCE_SHA256 = (
    "5ed3164d6f7dc39785de6b70ce1dc90c615feebe7e754b6971cd94e68292f5c2"
)
R02_D4_S4_S3_SOURCE_SHA256 = (
    "b80221af86a7db365c00d67d33378597c10f70b14c856c4080c94a7c2bbac7c2"
)

R02_D4_S4_TOTAL_N = 200
R02_D4_S4_ELIGIBLE_EPISODE_COUNT = 69
R02_D4_S4_INELIGIBLE_EPISODE_COUNT = 131
R02_D4_S4_PER_EPISODE_ATTEMPT_CAP = 1
R02_D4_S4_RETRY_ATTEMPT_CAP = 0
R02_D4_S4_REPLACEMENT_CAP = 0
R02_D4_S4_UNSETTLED_ATTEMPT_CAP = 0
R02_D4_S4_PROVIDER_ATTEMPT_CAP = 69
R02_D4_S4_PER_ATTEMPT_TOKEN_RESERVE = 32_000
R02_D4_S4_AGGREGATE_TOKEN_CAP = 2_208_000
R02_D4_S4_INCREMENTAL_USD_CAP = 0
R02_D4_S4_MAXIMUM_DRAFT_PROMPT_UTF8_BYTES = 1_842
R02_D4_S4_MAXIMUM_SELECTOR_PAYLOAD_UTF8_BYTES = 1_314
R02_D4_S4_R01_OBSERVED_MAX_ACCOUNTING_TOTAL_TOKENS = 15_750
R02_D4_S4_EXPECTED_FOCUSED_TEST_COUNT = 97


class R02D4S4BudgetError(RuntimeError):
    """Raised when a frozen provider-budget input or invariant drifts."""


def _require_equal(actual: object, expected: object, code: str) -> None:
    if actual != expected:
        raise R02D4S4BudgetError(code)


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise R02D4S4BudgetError(f"expected JSON object: {path}")
    return payload


def _verify_hash(repo_root: Path, relative_path: str, expected: str) -> None:
    actual = sha256_hex((repo_root / relative_path).read_bytes())
    _require_equal(actual, expected, f"byte hash drift: {relative_path}")


def expected_provider_budget() -> dict[str, object]:
    """Return the frozen numeric budget through the accepted typed contract."""

    return R02ProviderBudgetFreeze(
        eligible_episode_count=R02_D4_S4_ELIGIBLE_EPISODE_COUNT,
        provider_attempt_cap=R02_D4_S4_PROVIDER_ATTEMPT_CAP,
        aggregate_token_cap=R02_D4_S4_AGGREGATE_TOKEN_CAP,
        maximum_draft_prompt_utf8_bytes=(
            R02_D4_S4_MAXIMUM_DRAFT_PROMPT_UTF8_BYTES
        ),
        maximum_selector_payload_utf8_bytes=(
            R02_D4_S4_MAXIMUM_SELECTOR_PAYLOAD_UTF8_BYTES
        ),
    ).model_dump(mode="json")


def verify_generation_retry_contract(
    intent: Mapping[str, Any],
    manifest: Mapping[str, Any],
    seal: Mapping[str, Any],
) -> None:
    """Verify generation, retry, and replacement fields, including seal.retry_count."""

    _require_equal(
        intent.get("generation_attempt_cap"),
        1,
        "S2A generation_attempt_cap is not exactly one",
    )
    for name, payload in (("manifest", manifest), ("seal", seal)):
        _require_equal(
            payload.get("frame_generation_count"),
            1,
            f"S2A {name} frame_generation_count is not exactly one",
        )
        _require_equal(
            payload.get("retry_count"),
            R02_D4_S4_RETRY_ATTEMPT_CAP,
            f"S2A {name} retry_count is not zero",
        )
        _require_equal(
            payload.get("replacement_count"),
            R02_D4_S4_REPLACEMENT_CAP,
            f"S2A {name} replacement_count is not zero",
        )


def verify_budget_payload(payload: Mapping[str, Any]) -> None:
    expected = expected_provider_budget()
    _require_equal(dict(payload), expected, "provider budget payload drift")
    _require_equal(
        payload.get("eligible_episode_count"),
        R02_D4_S4_ELIGIBLE_EPISODE_COUNT,
        "provider budget eligible count drift",
    )
    _require_equal(
        payload.get("provider_attempt_cap"),
        R02_D4_S4_ELIGIBLE_EPISODE_COUNT
        * R02_D4_S4_PER_EPISODE_ATTEMPT_CAP,
        "provider attempt cap arithmetic mismatch",
    )
    _require_equal(
        payload.get("aggregate_token_cap"),
        R02_D4_S4_PROVIDER_ATTEMPT_CAP
        * R02_D4_S4_PER_ATTEMPT_TOKEN_RESERVE,
        "aggregate token cap arithmetic mismatch",
    )
    _require_equal(
        payload.get("retry_attempt_cap"),
        R02_D4_S4_RETRY_ATTEMPT_CAP,
        "provider retry cap is not zero",
    )
    _require_equal(
        payload.get("provider_calls"), 0, "provider calls are not zero"
    )
    _require_equal(
        payload.get("live_execution"), False, "LIVE execution is not false"
    )


def prompt_budget_evidence(repo_root: Path) -> tuple[int, int]:
    """Recompute request-size evidence without launching a provider process."""

    manifest_path = repo_root / "docs/r02-d4-s2a-frame-manifest.json"
    manifest = R02D4S2AFrameManifest.model_validate_json(manifest_path.read_bytes())
    _require_equal(
        manifest.total_eligible_count,
        R02_D4_S4_ELIGIBLE_EPISODE_COUNT,
        "prompt evidence eligible count drift",
    )
    artifact_root = repo_root / ".research_artifacts/r02-d4-s2a-frame-0716a1b9c13a"
    _require_equal(
        artifact_root.resolve(),
        DEFAULT_R02_D4_S2A_ARTIFACT_ROOT.resolve(),
        "prompt evidence artifact root drift",
    )
    evidence = _prompt_budget_evidence(
        manifest,
        R02AppendOnlyArtifactStore(artifact_root),
    )
    _require_equal(
        evidence,
        (
            R02_D4_S4_MAXIMUM_DRAFT_PROMPT_UTF8_BYTES,
            R02_D4_S4_MAXIMUM_SELECTOR_PAYLOAD_UTF8_BYTES,
        ),
        "prompt or selector payload byte evidence drift",
    )
    return evidence


def verify_sealed_inputs(repo_root: Path) -> None:
    pins = {
        "docs/r02-d4-s2a-frame-intent.json": R02_D4_S4_S2A_INTENT_SHA256,
        "docs/r02-d4-s2a-frame-manifest.json": R02_D4_S4_FRAME_MANIFEST_SHA256,
        "docs/r02-d4-s2a-frame-seal.json": R02_D4_S4_FRAME_SEAL_SHA256,
        "docs/r02-d4-s3-statistical-freeze.json": R02_D4_S4_S3_FREEZE_SHA256,
        "docs/r02-d4-s3-focused-tests.json": R02_D4_S4_S3_FOCUSED_TESTS_SHA256,
        "docs/r02-d4-s3-zero-call-manifest.json": R02_D4_S4_S3_ZERO_CALL_SHA256,
        "docs/r02-d4-replication-design.json": R02_D4_S4_ACCEPTED_DESIGN_SHA256,
        "docs/r02-d3-preregistration.json": R02_D4_S4_D3_PREREGISTRATION_SHA256,
        "v2/research/overlay/r02_statistics.py": R02_D4_S4_STATISTICS_SOURCE_SHA256,
        "v2/research/overlay/r02_candidates.py": R02_D4_S4_CANDIDATES_SOURCE_SHA256,
        "v2/research/overlay/r02_selector.py": R02_D4_S4_SELECTOR_SOURCE_SHA256,
        "v2/research/overlay/canonical.py": R02_D4_S4_CANONICAL_SOURCE_SHA256,
        "v2/research/overlay/r02_d4_s2a_frame.py": R02_D4_S4_S2A_SOURCE_SHA256,
        "v2/research/overlay/r02_d4_s3_freeze.py": R02_D4_S4_S3_SOURCE_SHA256,
    }
    for relative_path, expected in pins.items():
        _verify_hash(repo_root, relative_path, expected)

    intent = _read_object(repo_root / "docs/r02-d4-s2a-frame-intent.json")
    manifest = _read_object(repo_root / "docs/r02-d4-s2a-frame-manifest.json")
    seal = _read_object(repo_root / "docs/r02-d4-s2a-frame-seal.json")
    s3 = _read_object(repo_root / "docs/r02-d4-s3-statistical-freeze.json")
    verify_generation_retry_contract(intent, manifest, seal)

    for name, payload in (("manifest", manifest), ("seal", seal)):
        _require_equal(payload.get("frame_id"), R02_D4_S4_FRAME_ID, f"{name} frame ID drift")
        _require_equal(payload.get("provider_calls"), 0, f"{name} provider calls not zero")
        _require_equal(
            payload.get("codex_exec_invocations"),
            0,
            f"{name} Codex exec invocations not zero",
        )
        _require_equal(
            payload.get("live_execution"), False, f"{name} LIVE execution not false"
        )
    _require_equal(
        manifest.get("total_count"), R02_D4_S4_TOTAL_N, "S2A total count drift"
    )
    _require_equal(
        manifest.get("total_eligible_count"),
        R02_D4_S4_ELIGIBLE_EPISODE_COUNT,
        "S2A eligible count drift",
    )
    _require_equal(
        seal.get("frame_manifest", {}).get("sha256"),
        R02_D4_S4_FRAME_MANIFEST_SHA256,
        "S2A seal manifest reference drift",
    )
    _require_equal(
        seal.get("full_tree_file_count"),
        R02_D4_S4_FRAME_TREE_FILE_COUNT,
        "S2A seal tree file count drift",
    )
    _require_equal(
        seal.get("full_tree_sha256"),
        R02_D4_S4_FRAME_TREE_SHA256,
        "S2A seal tree hash drift",
    )
    artifact_tree = _filesystem_tree(DEFAULT_R02_D4_S2A_ARTIFACT_ROOT)
    _require_equal(
        artifact_tree,
        (R02_D4_S4_FRAME_TREE_FILE_COUNT, R02_D4_S4_FRAME_TREE_SHA256),
        "S2A artifact tree drift",
    )
    typed_manifest = R02D4S2AFrameManifest.model_validate_json(
        (repo_root / "docs/r02-d4-s2a-frame-manifest.json").read_bytes()
    )
    _require_equal(
        canonical_sha256(typed_manifest),
        R02_D4_S4_FRAME_MANIFEST_SHA256,
        "S2A canonical manifest hash drift",
    )
    _require_equal(
        s3.get("frame_id"), R02_D4_S4_FRAME_ID, "S3 frame ID drift"
    )
    _require_equal(
        s3.get("total_eligible_count"),
        R02_D4_S4_ELIGIBLE_EPISODE_COUNT,
        "S3 eligible count drift",
    )
    _require_equal(
        s3.get("provider_budget_created"),
        False,
        "S3 unexpectedly contains a provider budget",
    )
    _require_equal(
        s3.get("future_phases", {}).get("provider_budget_must_use_sealed_eligible_count"),
        R02_D4_S4_ELIGIBLE_EPISODE_COUNT,
        "S3 future provider-budget count drift",
    )
    prompt_budget_evidence(repo_root)


def verify_focused_test_manifest(repo_root: Path, manifest: Mapping[str, Any]) -> None:
    _require_equal(
        manifest.get("status"), "FROZEN_EXACT_TEST_SUITE", "focused test status drift"
    )
    _require_equal(
        manifest.get("expected_collected_tests"),
        R02_D4_S4_EXPECTED_FOCUSED_TEST_COUNT,
        "focused test count drift",
    )
    files = manifest.get("test_files")
    hashes = manifest.get("test_file_sha256")
    if not isinstance(files, list) or not isinstance(hashes, dict):
        raise R02D4S4BudgetError("focused test file/hash structure drift")
    _require_equal(len(files), 10, "focused test file count drift")
    _require_equal(set(files), set(hashes), "focused test file/hash keys drift")
    for relative_path in files:
        _verify_hash(repo_root, relative_path, str(hashes[relative_path]))
    _require_equal(manifest.get("provider_calls"), 0, "focused tests provider calls not zero")
    _require_equal(
        manifest.get("codex_exec_invocations"),
        0,
        "focused tests Codex exec invocations not zero",
    )
    _require_equal(manifest.get("live_execution"), False, "focused tests LIVE not false")


def verify_freeze(repo_root: Path, freeze: Mapping[str, Any]) -> None:
    verify_sealed_inputs(repo_root)
    _require_equal(
        freeze.get("schema_version"),
        "r02-d4-s4-provider-budget-freeze-v1",
        "provider-budget freeze schema drift",
    )
    _require_equal(
        freeze.get("status"),
        "PROVIDER_FREE_PROVIDER_BUDGET_FREEZE_PENDING_INDEPENDENT_REVIEW",
        "provider-budget freeze status drift",
    )
    _require_equal(
        freeze.get("freeze_base_commit"),
        R02_D4_S4_BASE_COMMIT,
        "provider-budget freeze base commit drift",
    )
    _require_equal(
        freeze.get("frame_id"), R02_D4_S4_FRAME_ID, "provider-budget frame ID drift"
    )
    _require_equal(
        freeze.get("sealed_eligible_episode_count"),
        R02_D4_S4_ELIGIBLE_EPISODE_COUNT,
        "provider-budget sealed eligible count drift",
    )
    _require_equal(
        freeze.get("provider_budget_created"),
        True,
        "provider-budget freeze is not marked created",
    )
    verify_budget_payload(freeze.get("provider_budget", {}))
    _require_equal(
        freeze.get("prompt_budget_evidence"),
        {
            "calculation": "MAX_OVER_69_ELIGIBLE_CASES_OF_UTF8_SYSTEM_PLUS_NEWLINE_PLUS_USER_AND_CANONICAL_SELECTOR_PAYLOAD",
            "evidence_source_sha256": R02_D4_S4_STATISTICS_SOURCE_SHA256,
            "maximum_draft_prompt_utf8_bytes": R02_D4_S4_MAXIMUM_DRAFT_PROMPT_UTF8_BYTES,
            "maximum_selector_payload_utf8_bytes": R02_D4_S4_MAXIMUM_SELECTOR_PAYLOAD_UTF8_BYTES,
            "reserve_reduced_by_byte_evidence": False,
            "status": "RECOMPUTED_PROVIDER_FREE_OVER_SEALED_FIXTURES",
        },
        "prompt budget evidence contract drift",
    )
    _require_equal(
        freeze.get("token_measurement"),
        {
            "accounting_formula": "input_tokens + output_tokens",
            "cached_input_is_subset_of_input": True,
            "cached_input_subtracted": False,
            "exactly_one_terminal_usage_event": True,
            "missing_or_invalid_usage_action": "DEBIT_ATTEMPT_AND_32000_TOKEN_RESERVE_THEN_HARD_STOP_UNSETTLED",
            "per_attempt_reservation_tokens": R02_D4_S4_PER_ATTEMPT_TOKEN_RESERVE,
            "reasoning_output_added_again": False,
            "reasoning_output_is_subset_of_output": True,
            "reported_total_over_reserve_action": "INVALID_RUN_BUDGET_BREACH",
            "required_fields": [
                "cached_input_tokens",
                "input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
            ],
            "source_contract": "R02_D3_TOKEN_MEASUREMENT_CONTRACT_REUSED_UNCHANGED",
        },
        "token measurement contract drift",
    )
    _require_equal(
        freeze.get("reservation_and_debit_contract"),
        {
            "attempt_slot_debited_before_launch": True,
            "attempted_case_remains_in_itt": True,
            "budget_exhaustion_action": "HARD_STOP_INVALID_RUN_NO_RETRY_OR_REPLACEMENT",
            "ineligible_fixture_provider_attempt_cap": 0,
            "missing_or_invalid_usage_action": "DEBIT_ATTEMPT_AND_32000_TOKEN_RESERVE_THEN_HARD_STOP_UNSETTLED",
            "next_attempt_requires_attempt_slot_and_full_32000_token_reservation": True,
            "reported_total_over_reserve_action": "INVALID_RUN_BUDGET_BREACH",
            "successful_usage_debit": "INPUT_TOKENS_PLUS_OUTPUT_TOKENS",
            "unused_reservation_is_not_a_NEW_attempt_credit": True,
        },
        "reservation and debit contract drift",
    )
    _require_equal(
        freeze.get("retry_and_replacement_contract"),
        {
            "generation_attempt_cap": 1,
            "frame_generation_count": 1,
            "manifest_retry_count": 0,
            "seal_retry_count": 0,
            "manifest_replacement_count": 0,
            "seal_replacement_count": 0,
            "provider_retry_attempt_cap": 0,
            "provider_replacement_cap": 0,
            "unsettled_attempt_cap": 0,
        },
        "retry and replacement contract drift",
    )
    _require_equal(
        freeze.get("budget_authorizes_provider_calls"),
        False,
        "budget freeze incorrectly authorizes provider calls",
    )
    _require_equal(
        freeze.get("authorization_boundary"),
        {
            "approved": "PROVIDER_FREE_PROVIDER_BUDGET_FREEZE_AUTHORING_ONLY",
            "codex_exec_authorized": False,
            "live_authorization_created": False,
            "live_execution_authorized": False,
            "micro_pilot_authorized": False,
            "provider_calls_authorized": False,
            "retry_or_replacement_authorized": False,
        },
        "authorization boundary drift",
    )
    _require_equal(
        freeze.get("sealed_inputs"),
        {
            "accepted_design_sha256": R02_D4_S4_ACCEPTED_DESIGN_SHA256,
            "frame_manifest_sha256": R02_D4_S4_FRAME_MANIFEST_SHA256,
            "frame_seal_sha256": R02_D4_S4_FRAME_SEAL_SHA256,
            "frame_tree_file_count": R02_D4_S4_FRAME_TREE_FILE_COUNT,
            "frame_tree_sha256": R02_D4_S4_FRAME_TREE_SHA256,
            "s2a_intent_sha256": R02_D4_S4_S2A_INTENT_SHA256,
            "s3_focused_tests_sha256": R02_D4_S4_S3_FOCUSED_TESTS_SHA256,
            "s3_statistical_freeze_sha256": R02_D4_S4_S3_FREEZE_SHA256,
            "s3_zero_call_sha256": R02_D4_S4_S3_ZERO_CALL_SHA256,
        },
        "sealed input reference drift",
    )
    _require_equal(
        freeze.get("source_references"),
        {
            "canonical_sha256": R02_D4_S4_CANONICAL_SOURCE_SHA256,
            "r02_candidates_sha256": R02_D4_S4_CANDIDATES_SOURCE_SHA256,
            "r02_d4_s2a_frame_sha256": R02_D4_S4_S2A_SOURCE_SHA256,
            "r02_d4_s3_freeze_sha256": R02_D4_S4_S3_SOURCE_SHA256,
            "r02_selector_sha256": R02_D4_S4_SELECTOR_SOURCE_SHA256,
            "r02_statistics_sha256": R02_D4_S4_STATISTICS_SOURCE_SHA256,
        },
        "source reference drift",
    )
    for field, expected in (
        ("provider_calls", 0),
        ("codex_exec_invocations", 0),
        ("micro_pilot_executed", False),
        ("live_execution", False),
        ("live_authorization_created", False),
        ("retry_count", 0),
        ("replacement_count", 0),
        ("commit_created", False),
        ("push_performed", False),
    ):
        _require_equal(freeze.get(field), expected, f"freeze boundary drift: {field}")
    source_hash = sha256_hex(
        (repo_root / "v2/research/overlay/r02_d4_s4_budget.py").read_bytes()
    )
    _require_equal(
        freeze.get("budget_source_sha256"), source_hash, "budget source hash drift"
    )
    focused_path = repo_root / "docs/r02-d4-s4-focused-tests.json"
    focused_hash = sha256_hex(focused_path.read_bytes())
    _require_equal(
        freeze.get("focused_test_manifest_sha256"),
        focused_hash,
        "focused test manifest hash drift",
    )
    verify_focused_test_manifest(repo_root, _read_object(focused_path))


def forbidden_capability_names() -> set[str]:
    """Names whose executable use would violate this authoring phase."""

    return {
        "provider_call",
        "codex_exec",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "micro_pilot",
        "live_execution",
        "retry",
        "replacement",
    }
