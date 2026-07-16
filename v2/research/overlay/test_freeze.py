from __future__ import annotations

import pytest

from .canonical import canonical_sha256
from .contracts import GeneratorConfig
from .freeze import (
    build_provider_free_regime_gap_summary,
    FROZEN_DEVELOPMENT_FIXTURE_COUNT,
    FROZEN_DEVELOPMENT_ROOT_SEED_LABEL,
    FROZEN_PROVIDER_FREE_FREEZE_SHA256,
    FROZEN_PROVIDER_FREE_REGIME_GAP_SUMMARY_SHA256,
    generate_provider_free_freeze,
    load_committed_provider_free_freeze,
    load_committed_provider_free_regime_gap_summary,
    NORMALIZATION_EPSILON_E12,
)
from .runner import main


def test_provider_free_freeze_is_deterministic_and_certified() -> None:
    first = generate_provider_free_freeze(root_seed_label="freeze-golden", count=1)
    second = generate_provider_free_freeze(root_seed_label="freeze-golden", count=1)

    assert first == second
    assert first.schema_version == "r01-provider-free-freeze-v1"
    assert first.generator_config_sha256 == canonical_sha256(GeneratorConfig())
    assert first.normalization_epsilon_e12 == NORMALIZATION_EPSILON_E12
    assert first.regret_scale_e12 == max(
        first.median_oracle_hold_gap_e12,
        first.normalization_epsilon_e12,
    )
    assert first.fixture_count == len(first.cases) == 1
    assert first.cases[0].oracle_hold_gap_e12 >= 0
    assert first.max_abs_utility_e12 == first.cases[0].maximum_abs_utility_e12
    assert first.max_normalized_regret_e12 == first.cases[0].maximum_normalized_regret_e12
    assert canonical_sha256(first) == "472cf9d0e3015aeaed44beae2e10af86cd3771c832263015362c4e7440f1a643"


def test_committed_provider_free_freeze_is_externally_anchored() -> None:
    freeze = load_committed_provider_free_freeze(expected_sha256=FROZEN_PROVIDER_FREE_FREEZE_SHA256)

    assert freeze.root_seed_label == FROZEN_DEVELOPMENT_ROOT_SEED_LABEL
    assert freeze.fixture_count == FROZEN_DEVELOPMENT_FIXTURE_COUNT
    assert canonical_sha256(freeze) == FROZEN_PROVIDER_FREE_FREEZE_SHA256
    with pytest.raises(RuntimeError, match="unexpected provider-free freeze trust anchor"):
        load_committed_provider_free_freeze(expected_sha256="0" * 64)


def test_generate_cli_rejects_unfrozen_seed_and_count(tmp_path) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "--artifact-root",
                str(tmp_path),
                "generate-development",
                "--experiment-id",
                "missing-anchor",
                "--root-seed",
                FROZEN_DEVELOPMENT_ROOT_SEED_LABEL,
            ]
        )
    common = [
        "--artifact-root",
        str(tmp_path),
        "generate-development",
        "--experiment-id",
        "blocked",
        "--freeze-sha256",
        FROZEN_PROVIDER_FREE_FREEZE_SHA256,
    ]
    with pytest.raises(RuntimeError, match="root seed"):
        main([*common, "--root-seed", "different-root-seed"])
    with pytest.raises(RuntimeError, match="fixture count"):
        main(
            [
                *common,
                "--root-seed",
                FROZEN_DEVELOPMENT_ROOT_SEED_LABEL,
                "--count",
                "39",
            ]
        )


def test_provider_free_regime_gap_summary_is_exact() -> None:
    freeze = load_committed_provider_free_freeze(expected_sha256=FROZEN_PROVIDER_FREE_FREEZE_SHA256)
    summary = build_provider_free_regime_gap_summary(
        freeze,
        source_freeze_sha256=FROZEN_PROVIDER_FREE_FREEZE_SHA256,
    )

    assert summary.fixture_count == 40
    assert summary.overall.zero_gap_count == 6
    assert summary.overall.positive_lte_epsilon_count == 0
    assert summary.overall.gt_epsilon_count == 34
    high_cost = summary.regimes["high_transaction_cost"]
    assert high_cost.case_count == 7
    assert high_cost.zero_gap_count == 6
    assert high_cost.positive_lte_epsilon_count == 0
    assert high_cost.gt_epsilon_count == 1
    assert high_cost.max_gap_e12 == 600135403
    assert canonical_sha256(summary) == FROZEN_PROVIDER_FREE_REGIME_GAP_SUMMARY_SHA256
    assert load_committed_provider_free_regime_gap_summary(expected_freeze_sha256=FROZEN_PROVIDER_FREE_FREEZE_SHA256) == summary
