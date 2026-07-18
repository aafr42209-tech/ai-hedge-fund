from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from . import r02_d4_s3_freeze as s3


def test_bootstrap_seed_preimage_is_outcome_independent_and_pinned() -> None:
    preimage = s3.bootstrap_seed_preimage()
    assert preimage["frame_manifest_sha256"] == s3.R02_D4_S3_FRAME_MANIFEST_SHA256
    assert preimage["bootstrap_resamples"] == 10_000
    assert not any("outcome" in key or "delta_observed" in key for key in preimage)
    assert len(s3.bootstrap_seed_sha256()) == 64
    assert int(s3.bootstrap_seed_integer_decimal()) == int(s3.bootstrap_seed_sha256(), 16)


def test_variant_seed_derivation_is_deterministic_and_separated() -> None:
    first = s3.variant_seed_sha256("PRIMARY_ZERO_NULLIFICATION", fixture_ordinal=7)
    second = s3.variant_seed_sha256("PRIMARY_ZERO_NULLIFICATION", fixture_ordinal=7)
    other = s3.variant_seed_sha256("PRIMARY_LEAVE_ONE_OUT", fixture_ordinal=7)
    assert first == second
    assert first != other


def test_primary_invalid_run_precedes_every_effect_label() -> None:
    assert s3.classify_primary(
        valid_run=False,
        eligible_count=69,
        theta_e12=100_000_000,
        lower_e12=90_000_000,
        maximum_absolute_theta_shift_e12=0,
        all_zero_nullification_lowers_pass=True,
        all_leave_one_out_lowers_pass=True,
        winsor_5_lower_pass=True,
        winsor_10_lower_pass=True,
    ) == "INVALID_RUN"


def test_primary_low_information_precedes_effect_label() -> None:
    assert s3.classify_primary(
        valid_run=True,
        eligible_count=56,
        theta_e12=100_000_000,
        lower_e12=90_000_000,
        maximum_absolute_theta_shift_e12=0,
        all_zero_nullification_lowers_pass=True,
        all_leave_one_out_lowers_pass=True,
        winsor_5_lower_pass=True,
        winsor_10_lower_pass=True,
    ) == "INCONCLUSIVE_LOW_INFORMATION"


def test_primary_lower_bound_must_be_strictly_above_delta_min() -> None:
    assert s3.classify_primary(
        valid_run=True,
        eligible_count=69,
        theta_e12=60_000_000,
        lower_e12=50_000_000,
        maximum_absolute_theta_shift_e12=0,
        all_zero_nullification_lowers_pass=True,
        all_leave_one_out_lowers_pass=True,
        winsor_5_lower_pass=True,
        winsor_10_lower_pass=True,
    ) == "REPLICATION_NOT_SUPPORTED"


def test_primary_robust_requires_every_frozen_condition() -> None:
    base = dict(
        valid_run=True,
        eligible_count=69,
        theta_e12=100_000_000,
        lower_e12=55_000_000,
        maximum_absolute_theta_shift_e12=10_000_000,
        all_zero_nullification_lowers_pass=True,
        all_leave_one_out_lowers_pass=True,
        winsor_5_lower_pass=True,
        winsor_10_lower_pass=True,
    )
    assert s3.classify_primary(**base) == "REPLICATION_SUPPORTED_ROBUST"
    base["winsor_10_lower_pass"] = False
    assert s3.classify_primary(**base) == "REPLICATION_SUPPORTED_FRAGILE"


def test_parsimony_labels_are_secondary_and_strict() -> None:
    assert s3.classify_parsimony(valid_run=True, eligible_count=56, lower_e12=99_000_000) == (
        "PARSIMONY_POLICY_INCONCLUSIVE_LOW_INFORMATION"
    )
    assert s3.classify_parsimony(valid_run=True, eligible_count=69, lower_e12=50_000_001) == (
        "PARSIMONY_POLICY_SUPPORTED"
    )
    assert s3.classify_parsimony(valid_run=True, eligible_count=69, lower_e12=50_000_000) == (
        "PARSIMONY_POLICY_NOT_SUPPORTED"
    )


def test_incremental_discordance_floor_returns_not_identified() -> None:
    assert s3.classify_incremental(
        valid_run=True,
        total_discordance=19,
        representative_discordance=9,
        challenge_discordance=10,
        lower_e12=1,
        upper_e12=2,
    ) == "NOT_IDENTIFIED_REDUNDANT_SELECTOR"
    assert s3.classify_incremental(
        valid_run=True,
        total_discordance=20,
        representative_discordance=4,
        challenge_discordance=16,
        lower_e12=1,
        upper_e12=2,
    ) == "NOT_IDENTIFIED_REDUNDANT_SELECTOR"


def test_incremental_effect_labels_apply_only_after_discordance_floor() -> None:
    common = dict(
        valid_run=True,
        total_discordance=20,
        representative_discordance=5,
        challenge_discordance=15,
    )
    assert s3.classify_incremental(**common, lower_e12=1, upper_e12=2) == (
        "INCREMENTAL_LLM_SUPPORTED"
    )
    assert s3.classify_incremental(**common, lower_e12=-2, upper_e12=-1) == (
        "INCREMENTAL_LLM_HARM"
    )
    assert s3.classify_incremental(**common, lower_e12=-1, upper_e12=1) == (
        "INCREMENTAL_LLM_INCONCLUSIVE"
    )


def test_wilson_interval_is_deterministic_and_bounded() -> None:
    lower, upper = s3.wilson_interval_ppm(69, 69)
    assert (lower, upper) == (947_263, 1_000_000)
    assert s3.wilson_interval_ppm(0, 69) == (0, 52_737)


def test_sealed_inputs_verify_generation_attempt_cap_and_counts() -> None:
    s3.verify_sealed_inputs(Path(__file__).resolve().parents[3])


def test_generation_attempt_cap_tamper_is_rejected() -> None:
    with pytest.raises(s3.R02D4S3FreezeError, match="generation_attempt_cap"):
        s3.verify_generation_attempt_contract(
            {"generation_attempt_cap": 2},
            {"frame_generation_count": 1},
            {"frame_generation_count": 1},
        )


def test_focused_test_count_tamper_is_rejected() -> None:
    root = Path(__file__).resolve().parents[3]
    manifest = json.loads((root / "docs" / "r02-d4-s3-focused-tests.json").read_text("utf-8"))
    manifest["expected_collected_tests"] = 76
    with pytest.raises(s3.R02D4S3FreezeError, match="focused test count drift"):
        s3.verify_focused_test_manifest(root, manifest)


def test_freeze_and_exact_focused_test_manifest_reproduce() -> None:
    root = Path(__file__).resolve().parents[3]
    freeze = json.loads((root / "docs" / "r02-d4-s3-statistical-freeze.json").read_text("utf-8"))
    s3.verify_freeze(root, freeze)


def test_s3_source_has_no_provider_network_process_or_live_imports() -> None:
    tree = ast.parse(Path(s3.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(s3.forbidden_capability_names())


def test_scientific_priority_cannot_be_reordered() -> None:
    assert s3.R02_D4_S3_TOTAL_ELIGIBLE == 69
    assert s3.R02_D4_S3_M_MIN == 57
    assert s3.R02_D4_S3_MIN_TOTAL_DISCORDANCE == 20
    assert s3.R02_D4_S3_MIN_STRATUM_DISCORDANCE == 5
