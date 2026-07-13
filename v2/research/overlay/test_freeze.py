from __future__ import annotations

from .canonical import canonical_sha256
from .contracts import GeneratorConfig
from .freeze import NORMALIZATION_EPSILON_E12, generate_provider_free_freeze


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
