"""Provider-free verifier and decision rules for the R02 D4-S3 statistical freeze."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path
from typing import Any, Literal, Mapping

from .canonical import canonical_json_bytes, sha256_hex

ROOT = Path(__file__).resolve().parents[3]
R02_D4_S3_BASE_COMMIT = "c4fb28c66404fc783cfbc33d125012e1dff2c76e"
R02_D4_S3_FRAME_ID = "r02-d4-s2a-frame-0716a1b9c13a"
R02_D4_S3_FRAME_MANIFEST_SHA256 = (
    "368e01509b04a53928df2d729f0914dbd0c1ee14c5221a6e189fbf7b8bfa4ba1"
)
R02_D4_S3_FRAME_SEAL_SHA256 = (
    "40aec915d3d24598ad2cbc46713a949b8c8ee5401d5768695b9be918b8bb5838"
)
R02_D4_S3_FRAME_TREE_SHA256 = (
    "65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29"
)
R02_D4_S3_S2A_INTENT_SHA256 = (
    "f126fd3da9167aa6982ed40514e14019a2ed64a7de16d001cc5a914f2438f04c"
)
R02_D4_S3_S2A_ZERO_CALL_SHA256 = (
    "2afe3a93d8a66a0919dc5d3041bb0537bc249f6c4aa89ffcc9b861c5b9b71503"
)
R02_D4_S3_ACCEPTED_DESIGN_SHA256 = (
    "784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900"
)
R02_D4_S3_PROSPECTIVE_SIZING_SHA256 = (
    "9df82bc59865de6856cf2417925e771a4afc2142baaae912a853b0ad0f01be17"
)
R02_D4_S3_PARSIMONY_VECTORS_SHA256 = (
    "a304d36b31b570e7ae28a0a9ec89d4e8c7e2ef1ec0eda5b8c854b40e85f4ea77"
)
R02_D4_S3_D3_POSTHOC_SHA256 = (
    "1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73"
)
R02_D4_S3_REPRESENTATIVE_N = 150
R02_D4_S3_CHALLENGE_N = 50
R02_D4_S3_TOTAL_N = 200
R02_D4_S3_REPRESENTATIVE_ELIGIBLE = 19
R02_D4_S3_CHALLENGE_ELIGIBLE = 50
R02_D4_S3_TOTAL_ELIGIBLE = 69
R02_D4_S3_M_MIN = 57
R02_D4_S3_DELTA_MIN_E12 = 50_000_000
R02_D4_S3_ROBUST_MARGIN_E12 = 5_000_000
R02_D4_S3_MAX_SHIFT_PPM = 100_000
R02_D4_S3_BOOTSTRAP_RESAMPLES = 10_000
R02_D4_S3_BOOTSTRAP_LOWER_INDEX = 249
R02_D4_S3_BOOTSTRAP_UPPER_INDEX = 9_749
R02_D4_S3_MIN_TOTAL_DISCORDANCE = 20
R02_D4_S3_MIN_STRATUM_DISCORDANCE = 5
R02_D4_S3_GENERATION_ATTEMPT_CAP = 1
R02_D4_S3_WILSON_Z_DECIMAL = "1.959963984540054"
R02_D4_S3_EXPECTED_FOCUSED_TEST_COUNT = 77

FOCUSED_TEST_FILES = (
    "v2/research/overlay/test_r02_frame.py",
    "v2/research/overlay/test_r02_d3_posthoc_analysis.py",
    "v2/research/overlay/test_r02_d4_design.py",
    "v2/research/overlay/test_r02_d4_s1_seed.py",
    "v2/research/overlay/test_r02_d4_s1_reveal.py",
    "v2/research/overlay/test_r02_d4_s1_resolve.py",
    "v2/research/overlay/test_r02_d4_s2_frame.py",
    "v2/research/overlay/test_r02_d4_s2a_frame.py",
    "v2/research/overlay/test_r02_d4_s3_freeze.py",
)


class R02D4S3FreezeError(RuntimeError):
    """Raised when the provider-free S3 freeze or its lineage drifts."""


def _require_equal(actual: object, expected: object, code: str) -> None:
    if actual != expected:
        raise R02D4S3FreezeError(code)


def _read_object(path: Path) -> dict[str, Any]:
    import json

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S3FreezeError(f"expected JSON object:{path}")
    return value


def bootstrap_seed_preimage() -> dict[str, object]:
    return {
        "domain": "r02-d4-s3-evaluation-bootstrap-v1",
        "freeze_base_commit": R02_D4_S3_BASE_COMMIT,
        "accepted_design_sha256": R02_D4_S3_ACCEPTED_DESIGN_SHA256,
        "frame_id": R02_D4_S3_FRAME_ID,
        "frame_manifest_sha256": R02_D4_S3_FRAME_MANIFEST_SHA256,
        "frame_seal_sha256": R02_D4_S3_FRAME_SEAL_SHA256,
        "frame_tree_sha256": R02_D4_S3_FRAME_TREE_SHA256,
        "representative_n": R02_D4_S3_REPRESENTATIVE_N,
        "challenge_n": R02_D4_S3_CHALLENGE_N,
        "representative_weight_numerator": 3,
        "challenge_weight_numerator": 1,
        "weight_denominator": 4,
        "bootstrap_resamples": R02_D4_S3_BOOTSTRAP_RESAMPLES,
        "lower_rank_index_zero_based": R02_D4_S3_BOOTSTRAP_LOWER_INDEX,
        "upper_rank_index_zero_based": R02_D4_S3_BOOTSTRAP_UPPER_INDEX,
        "delta_min_e12": R02_D4_S3_DELTA_MIN_E12,
        "m_min": R02_D4_S3_M_MIN,
    }


def bootstrap_seed_sha256() -> str:
    return sha256_hex(canonical_json_bytes(bootstrap_seed_preimage()))


def bootstrap_seed_integer_decimal() -> str:
    return str(int(bootstrap_seed_sha256(), 16))


def variant_seed_sha256(
    analysis_id: str,
    *,
    fixture_ordinal: int | None = None,
    winsor_fraction_ppm: int | None = None,
) -> str:
    if not analysis_id or not analysis_id.isascii():
        raise ValueError("analysis_id must be nonempty ASCII")
    if fixture_ordinal is not None and not 0 <= fixture_ordinal < R02_D4_S3_TOTAL_N:
        raise ValueError("fixture ordinal out of range")
    if winsor_fraction_ppm not in (None, 50_000, 100_000):
        raise ValueError("winsor fraction is not frozen")
    preimage = {
        "domain": "r02-d4-s3-variant-bootstrap-v1",
        "base_bootstrap_seed_sha256": bootstrap_seed_sha256(),
        "analysis_id": analysis_id,
        "fixture_ordinal": fixture_ordinal,
        "winsor_fraction_ppm": winsor_fraction_ppm,
    }
    return sha256_hex(canonical_json_bytes(preimage))


PrimaryLabel = Literal[
    "INVALID_RUN",
    "INCONCLUSIVE_LOW_INFORMATION",
    "REPLICATION_NOT_SUPPORTED",
    "REPLICATION_SUPPORTED_ROBUST",
    "REPLICATION_SUPPORTED_FRAGILE",
]


def classify_primary(
    *,
    valid_run: bool,
    eligible_count: int,
    theta_e12: int,
    lower_e12: int,
    maximum_absolute_theta_shift_e12: int,
    all_zero_nullification_lowers_pass: bool,
    all_leave_one_out_lowers_pass: bool,
    winsor_5_lower_pass: bool,
    winsor_10_lower_pass: bool,
) -> PrimaryLabel:
    if not valid_run:
        return "INVALID_RUN"
    if eligible_count < R02_D4_S3_M_MIN:
        return "INCONCLUSIVE_LOW_INFORMATION"
    if lower_e12 <= R02_D4_S3_DELTA_MIN_E12:
        return "REPLICATION_NOT_SUPPORTED"
    robust = (
        lower_e12 - R02_D4_S3_DELTA_MIN_E12 >= R02_D4_S3_ROBUST_MARGIN_E12
        and abs(theta_e12) > 0
        and maximum_absolute_theta_shift_e12 * 1_000_000
        <= R02_D4_S3_MAX_SHIFT_PPM * abs(theta_e12)
        and all_zero_nullification_lowers_pass
        and all_leave_one_out_lowers_pass
        and winsor_5_lower_pass
        and winsor_10_lower_pass
    )
    return "REPLICATION_SUPPORTED_ROBUST" if robust else "REPLICATION_SUPPORTED_FRAGILE"


ParsimonyLabel = Literal[
    "INVALID_RUN",
    "PARSIMONY_POLICY_INCONCLUSIVE_LOW_INFORMATION",
    "PARSIMONY_POLICY_SUPPORTED",
    "PARSIMONY_POLICY_NOT_SUPPORTED",
]


def classify_parsimony(*, valid_run: bool, eligible_count: int, lower_e12: int) -> ParsimonyLabel:
    if not valid_run:
        return "INVALID_RUN"
    if eligible_count < R02_D4_S3_M_MIN:
        return "PARSIMONY_POLICY_INCONCLUSIVE_LOW_INFORMATION"
    if lower_e12 > R02_D4_S3_DELTA_MIN_E12:
        return "PARSIMONY_POLICY_SUPPORTED"
    return "PARSIMONY_POLICY_NOT_SUPPORTED"


IncrementalLabel = Literal[
    "INVALID_RUN",
    "NOT_IDENTIFIED_REDUNDANT_SELECTOR",
    "INCREMENTAL_LLM_SUPPORTED",
    "INCREMENTAL_LLM_HARM",
    "INCREMENTAL_LLM_INCONCLUSIVE",
]


def classify_incremental(
    *,
    valid_run: bool,
    total_discordance: int,
    representative_discordance: int,
    challenge_discordance: int,
    lower_e12: int,
    upper_e12: int,
) -> IncrementalLabel:
    if not valid_run:
        return "INVALID_RUN"
    if (
        total_discordance < R02_D4_S3_MIN_TOTAL_DISCORDANCE
        or representative_discordance < R02_D4_S3_MIN_STRATUM_DISCORDANCE
        or challenge_discordance < R02_D4_S3_MIN_STRATUM_DISCORDANCE
    ):
        return "NOT_IDENTIFIED_REDUNDANT_SELECTOR"
    if lower_e12 > 0:
        return "INCREMENTAL_LLM_SUPPORTED"
    if upper_e12 < 0:
        return "INCREMENTAL_LLM_HARM"
    return "INCREMENTAL_LLM_INCONCLUSIVE"


def wilson_interval_ppm(successes: int, total: int) -> tuple[int, int]:
    if total <= 0 or successes < 0 or successes > total:
        raise ValueError("invalid Wilson inputs")
    with localcontext() as context:
        context.prec = 50
        z = Decimal(R02_D4_S3_WILSON_Z_DECIMAL)
        n = Decimal(total)
        p = Decimal(successes) / n
        denominator = Decimal(1) + z * z / n
        center = (p + z * z / (Decimal(2) * n)) / denominator
        radius = (
            z
            * (p * (Decimal(1) - p) / n + z * z / (Decimal(4) * n * n)).sqrt()
            / denominator
        )
        scale = Decimal(1_000_000)
        lower = int(((center - radius) * scale).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
        upper = int(((center + radius) * scale).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
    return max(0, lower), min(1_000_000, upper)


def verify_sealed_inputs(repo_root: Path) -> None:
    pinned_files = {
        "docs/r02-d4-s2a-frame-intent.json": R02_D4_S3_S2A_INTENT_SHA256,
        "docs/r02-d4-s2a-frame-manifest.json": R02_D4_S3_FRAME_MANIFEST_SHA256,
        "docs/r02-d4-s2a-frame-seal.json": R02_D4_S3_FRAME_SEAL_SHA256,
        "docs/r02-d4-s2a-zero-call-manifest.json": R02_D4_S3_S2A_ZERO_CALL_SHA256,
        "docs/r02-d4-replication-design.json": R02_D4_S3_ACCEPTED_DESIGN_SHA256,
        "docs/r02-d4-prospective-power-sizing.json": R02_D4_S3_PROSPECTIVE_SIZING_SHA256,
        "docs/r02-d4-parsimony-test-vectors.json": R02_D4_S3_PARSIMONY_VECTORS_SHA256,
        "docs/r02-d3-successor-provider-free-posthoc.json": R02_D4_S3_D3_POSTHOC_SHA256,
    }
    for relative_path, expected_hash in pinned_files.items():
        _require_equal(
            sha256_hex((repo_root / relative_path).read_bytes()),
            expected_hash,
            f"sealed input drift:{relative_path}",
        )
    intent = _read_object(repo_root / "docs" / "r02-d4-s2a-frame-intent.json")
    manifest = _read_object(repo_root / "docs" / "r02-d4-s2a-frame-manifest.json")
    seal = _read_object(repo_root / "docs" / "r02-d4-s2a-frame-seal.json")
    verify_generation_attempt_contract(intent, manifest, seal)
    _verify_sealed_frame_fields(manifest, seal)


def verify_generation_attempt_contract(
    intent: Mapping[str, Any],
    manifest: Mapping[str, Any],
    seal: Mapping[str, Any],
) -> None:
    _require_equal(
        intent.get("generation_attempt_cap"),
        R02_D4_S3_GENERATION_ATTEMPT_CAP,
        "S2A generation_attempt_cap is not exactly one",
    )
    _require_equal(manifest.get("frame_generation_count"), 1, "manifest generation count drift")
    _require_equal(seal.get("frame_generation_count"), 1, "seal generation count drift")


def _verify_sealed_frame_fields(
    manifest: Mapping[str, Any], seal: Mapping[str, Any]
) -> None:
    _require_equal(manifest.get("frame_id"), R02_D4_S3_FRAME_ID, "frame identity drift")
    _require_equal(manifest.get("representative_count"), 150, "representative count drift")
    _require_equal(manifest.get("challenge_count"), 50, "challenge count drift")
    _require_equal(manifest.get("total_count"), 200, "total count drift")
    _require_equal(manifest.get("representative_eligible_count"), 19, "rep eligible drift")
    _require_equal(manifest.get("challenge_eligible_count"), 50, "challenge eligible drift")
    _require_equal(manifest.get("total_eligible_count"), 69, "total eligible drift")
    _require_equal(seal.get("full_tree_sha256"), R02_D4_S3_FRAME_TREE_SHA256, "tree drift")
    _require_equal(manifest.get("provider_calls"), 0, "provider call contamination")
    _require_equal(manifest.get("live_execution"), False, "LIVE contamination")


def verify_focused_test_manifest(repo_root: Path, manifest: Mapping[str, Any]) -> None:
    _require_equal(manifest.get("test_files"), list(FOCUSED_TEST_FILES), "focused test file list drift")
    expected_argv = [
        ".venv\\Scripts\\python.exe",
        "-m",
        "pytest",
        *FOCUSED_TEST_FILES,
        "-q",
    ]
    _require_equal(manifest.get("argv"), expected_argv, "focused test argv drift")
    _require_equal(
        manifest.get("expected_collected_tests"),
        R02_D4_S3_EXPECTED_FOCUSED_TEST_COUNT,
        "focused test count drift",
    )
    file_hashes = manifest.get("test_file_sha256")
    if not isinstance(file_hashes, Mapping):
        raise R02D4S3FreezeError("focused test hashes missing")
    for relative_path in FOCUSED_TEST_FILES:
        _require_equal(
            file_hashes.get(relative_path),
            sha256_hex((repo_root / relative_path).read_bytes()),
            f"focused test source drift:{relative_path}",
        )


def verify_freeze(repo_root: Path, freeze: Mapping[str, Any]) -> None:
    verify_sealed_inputs(repo_root)
    expected_top = {
        "schema_version": "r02-d4-s3-statistical-freeze-v1",
        "status": "PROVIDER_FREE_STATISTICAL_FREEZE_PENDING_INDEPENDENT_REVIEW",
        "freeze_base_commit": R02_D4_S3_BASE_COMMIT,
        "frame_id": R02_D4_S3_FRAME_ID,
        "frame_manifest_sha256": R02_D4_S3_FRAME_MANIFEST_SHA256,
        "frame_seal_sha256": R02_D4_S3_FRAME_SEAL_SHA256,
        "frame_tree_sha256": R02_D4_S3_FRAME_TREE_SHA256,
        "representative_n": 150,
        "challenge_n": 50,
        "total_n": 200,
        "representative_eligible_count": 19,
        "challenge_eligible_count": 50,
        "total_eligible_count": 69,
        "m_min": 57,
        "generation_attempt_cap_verified": True,
        "provider_calls": 0,
        "codex_exec_invocations": 0,
        "micro_pilot_executed": False,
        "live_execution": False,
        "provider_budget_created": False,
        "live_authorization_created": False,
        "commit_created": False,
        "push_performed": False,
    }
    for field, expected in expected_top.items():
        _require_equal(freeze.get(field), expected, f"freeze field mismatch:{field}")
    _require_equal(
        freeze.get("freeze_source_sha256"),
        sha256_hex(Path(__file__).read_bytes()),
        "freeze verifier source drift",
    )
    bootstrap = freeze.get("bootstrap")
    if not isinstance(bootstrap, Mapping):
        raise R02D4S3FreezeError("bootstrap contract missing")
    _require_equal(bootstrap.get("preimage"), bootstrap_seed_preimage(), "bootstrap preimage drift")
    _require_equal(bootstrap.get("seed_sha256"), bootstrap_seed_sha256(), "bootstrap seed drift")
    _require_equal(
        bootstrap.get("seed_integer_decimal"),
        bootstrap_seed_integer_decimal(),
        "bootstrap seed integer drift",
    )
    _require_equal(bootstrap.get("resamples"), 10_000, "bootstrap resamples drift")
    _require_equal(bootstrap.get("lower_rank_index_zero_based"), 249, "lower rank drift")
    _require_equal(bootstrap.get("upper_rank_index_zero_based"), 9_749, "upper rank drift")
    _require_equal(bootstrap.get("bit_generator"), "PCG64", "bit generator drift")
    _require_equal(bootstrap.get("numpy_version"), "1.26.4", "numpy version drift")
    estimands = freeze.get("estimands")
    if not isinstance(estimands, list) or [value.get("id") for value in estimands] != [
        "PRIMARY_REPLICATION",
        "DETERMINISTIC_POLICY",
        "INCREMENTAL_LLM",
        "AGREEMENT",
    ]:
        raise R02D4S3FreezeError("estimand separation drift")
    labels = freeze.get("label_precedence")
    if not isinstance(labels, Mapping):
        raise R02D4S3FreezeError("label precedence missing")
    _require_equal(labels.get("m_min"), 57, "label M_min drift")
    _require_equal(labels.get("delta_min_e12"), 50_000_000, "label delta_min drift")
    _require_equal(labels.get("robust_margin_e12"), 5_000_000, "robust margin drift")
    _require_equal(labels.get("maximum_theta_shift_ppm"), 100_000, "influence threshold drift")
    discordance = freeze.get("incremental_discordance_floor")
    _require_equal(
        discordance,
        {"total": 20, "representative": 5, "challenge": 5},
        "discordance floor drift",
    )
    _require_equal(
        freeze.get("future_mechanism_study"),
        "AMBIGUITY_ENGINEERED_CANDIDATES_SEPARATE_NOT_PART_OF_D4",
        "mechanism-study boundary drift",
    )
    test_path = repo_root / "docs" / "r02-d4-s3-focused-tests.json"
    test_hash = sha256_hex(test_path.read_bytes())
    _require_equal(
        freeze.get("focused_test_manifest_sha256"),
        test_hash,
        "focused test manifest hash drift",
    )
    verify_focused_test_manifest(repo_root, _read_object(test_path))


def forbidden_capability_names() -> set[str]:
    return {
        "asyncio",
        "http",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "codex_exec_client",
        "r02_d3_live_orchestrator",
    }
