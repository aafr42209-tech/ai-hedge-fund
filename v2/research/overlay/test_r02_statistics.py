from __future__ import annotations

import ast
from pathlib import Path

from .canonical import canonical_json_bytes, sha256_hex
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_frame import R02FrameManifest, R02FrameSeal
from .r02_statistics import (
    R02_DELTA_MIN_E12,
    R02_DELTA_TARGET_E12,
    R02_M_MIN,
    R02_OPPORTUNITY_TARGET_PPM,
    R02_POWER_TARGET_PPM,
    R02StatisticalFreeze,
    _opportunity_probabilities,
    _simulate_scenario,
    build_statistical_freeze,
    stratified_bootstrap_interval_e12,
    stratified_weighted_mean_e12,
)
from . import r02_statistics


ROOT = Path(__file__).resolve().parents[3]
FRAME_MANIFEST_PATH = ROOT / "docs" / "r02-d2c-frame-manifest.json"
FRAME_SEAL_PATH = ROOT / "docs" / "r02-d2c-frame-seal.json"
STATISTICAL_FREEZE_PATH = ROOT / "docs" / "r02-d2c-statistical-freeze.json"


def test_stratified_estimator_uses_frozen_weights_and_zero_contributions() -> None:
    representative = (0, 0, 0, 400)
    challenge = (0, 800)
    assert stratified_weighted_mean_e12(representative, challenge) == 175
    assert stratified_weighted_mean_e12((0,) * 120, (0,) * 40) == 0


def test_registered_bootstrap_is_deterministic_and_resamples_within_strata() -> None:
    seed = "1" * 64
    first = stratified_bootstrap_interval_e12((0,) * 120, (100,) * 40, seed_hex=seed)
    second = stratified_bootstrap_interval_e12((0,) * 120, (100,) * 40, seed_hex=seed)
    assert first == second == (25, 25)


def test_m_min_probability_floor_matches_frozen_opportunity_scenarios() -> None:
    probabilities = {item.scenario_id: item for item in _opportunity_probabilities()}
    worst = probabilities["rep-8pct-collapse-5pct"]
    assert R02_M_MIN == 46
    assert worst.exact_probability_ppb == 900_568_127
    assert worst.exact_probability_ppb >= R02_OPPORTUNITY_TARGET_PPM * 1_000
    assert probabilities["rep-8pct-collapse-0pct"].exact_probability_ppb == 924_743_716


def test_design_power_scenario_is_deterministic() -> None:
    manifest = R02FrameManifest.model_validate_json(FRAME_MANIFEST_PATH.read_bytes())
    seal = R02FrameSeal.model_validate_json(FRAME_SEAL_PATH.read_bytes())
    seed = sha256_hex(
        canonical_json_bytes(
            {
                "domain": "r02-d2c-statistical-simulation-v1",
                "frame_manifest_sha256": seal.frame_manifest.sha256,
                "frame_full_tree_sha256": seal.full_tree_sha256,
                "delta_min_e12": R02_DELTA_MIN_E12,
                "delta_target_e12": R02_DELTA_TARGET_E12,
            }
        )
    )
    scenario = _simulate_scenario(
        simulation_seed_hex=seed,
        total_n=160,
        representative_trigger_rate_bps=800,
        representative_candidate_collapse_rate_bps=500,
        valid_selector_rate_bps=9_500,
        fail_closed_rate_bps=500,
        conditional_standardized_mean_bps=10_000,
        scenario_label="design-worst",
        design_gate_scenario=True,
    )
    assert manifest.representative_trigger_count == 15
    assert scenario.estimated_power_ppm == 857_000
    assert scenario.wilson_lower_power_ppm == 833_935
    assert scenario.wilson_lower_power_ppm >= R02_POWER_TARGET_PPM


def test_frozen_statistical_package_reproduces_exactly() -> None:
    manifest = R02FrameManifest.model_validate_json(FRAME_MANIFEST_PATH.read_bytes())
    seal = R02FrameSeal.model_validate_json(FRAME_SEAL_PATH.read_bytes())
    frozen = R02StatisticalFreeze.model_validate_json(STATISTICAL_FREEZE_PATH.read_bytes())
    store = R02AppendOnlyArtifactStore(ROOT / seal.artifact_root_relative_path)
    reproduced = build_statistical_freeze(manifest, seal, store)

    assert canonical_json_bytes(reproduced) == canonical_json_bytes(frozen)
    assert frozen.oracle_selector_upper_bound_theta_e12 == 144_404_140
    assert frozen.observed_eligible_candidate_headroom_mean_e12 == 420_084_770
    assert frozen.observed_eligible_candidate_headroom_sample_sd_e12 == 381_049_791
    assert frozen.observed_eligible_candidate_headroom_standardized_mean_bps == 11_024
    assert frozen.maximum_frame_candidate_headroom_e12 == 1_722_160_500
    assert frozen.delta_min_e12 == 50_000_000
    assert frozen.delta_target_e12 == 100_000_000
    assert frozen.observed_total_eligible_count == 55
    assert frozen.provider_budget.provider_attempt_cap == 55
    assert frozen.provider_budget.aggregate_token_cap == 1_760_000
    assert frozen.provider_budget.maximum_draft_prompt_utf8_bytes == 1_848
    assert frozen.provider_calls == 0
    assert frozen.live_execution is False
    assert frozen.zero_call_preflight_status == "NOT_AUTHORIZED_NOT_FINALIZED"


def test_statistics_module_has_no_provider_network_or_process_imports() -> None:
    source_path = Path(r02_statistics.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(
        {
            "anthropic",
            "httpx",
            "openai",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
    )
    assert sha256_hex(source_path.read_bytes()) == r02_statistics._statistics_source_sha256()
