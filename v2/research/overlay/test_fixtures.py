from __future__ import annotations

import numpy as np
import pytest

from .contracts import ASSET_IDS, GeneratorConfig
from .fixtures import generate_development_episodes, generate_episode, regime_counts
from .lattice import hold_batch, iter_candidate_batches
from .validator import validate_batch


def test_generator_is_byte_and_hash_deterministic() -> None:
    config = GeneratorConfig()
    left = generate_episode(config, "determinism", 3)
    right = generate_episode(config, "determinism", 3)
    different = generate_episode(config, "determinism", 4)
    assert left == right
    assert left.content_sha256 == right.content_sha256
    assert left.content_sha256 != different.content_sha256


def test_development_regimes_are_balanced() -> None:
    counts = regime_counts(generate_development_episodes(GeneratorConfig(), "balanced", 40))
    assert sum(counts.values()) == 40
    assert max(counts.values()) - min(counts.values()) <= 1


def test_generator_properties_over_fixed_seed_matrix() -> None:
    config = GeneratorConfig()
    for index in range(100):
        fixture = generate_episode(config, "property-matrix", index)
        public = fixture.public
        matrix = np.asarray(
            [[public.covariance_bp2[row][column] for column in ASSET_IDS] for row in ASSET_IDS],
            dtype=np.float64,
        )
        assert float(np.linalg.eigvalsh(matrix).min()) >= -1e-6
        assert validate_batch(public, hold_batch()).raw_valid
        assert any(validation.raw_valid and any(decision.action != "hold" for decision in batch.decisions.values()) for batch in iter_candidate_batches(public) if (validation := validate_batch(public, batch)))


def test_phase_a_refuses_evaluation_generation() -> None:
    with pytest.raises(ValueError, match="development fixtures only"):
        generate_episode(GeneratorConfig(), "forbidden", 0, split="evaluation")
