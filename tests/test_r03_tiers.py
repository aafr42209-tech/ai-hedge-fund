from __future__ import annotations

import importlib.metadata

import pytest

from v2.research.news_reasoning.r03_contracts import R03T2ModelIdentity
from v2.research.news_reasoning.r03_tiers import (
    add_t1_sentiment,
    assert_t2_t3_information_equal,
    build_t2_model_identity,
    fit_t2_after_separate_authorization,
    frozen_tier_configs,
    installed_t2_runtime,
    preprocess_t0_cross_section,
    R03DependencyUnavailable,
    select_alpha_by_worst_fold,
    tier_config_sha256,
)

SHA = "a" * 64


def runtime() -> dict[str, str]:
    return {"python_version": "3.11.15", "numpy_version": "1.26.4", "scipy_version": "1.17.1", "scikit_learn_version": "synthetic-0"}


def identity(**updates) -> R03T2ModelIdentity:
    values = dict(
        runtime=runtime(),
        canonical_schema_sha256=SHA,
        payload_sha256="b" * 64,
        training_frame_sha256="c" * 64,
        split_sha256="d" * 64,
        feature_config_sha256="e" * 64,
        selected_alpha=10,
        prediction_clip_low=-0.5,
        prediction_clip_high=0.5,
        fitted_parameter_sha256="f" * 64,
        blas_lapack_identity="synthetic-blas",
    )
    values.update(updates)
    return build_t2_model_identity(**values)


def test_frozen_tiers_bind_single_t2_comparator() -> None:
    configs = frozen_tier_configs()
    assert tuple(configs) == ("T0", "T1", "T2", "T3_CONTRACT_ONLY")
    assert configs["T2"]["alpha_grid"] == (1, 10, 100, 1000)
    assert "n_features=262144" in str(configs["T2"]["vectorizer"])
    assert len(tier_config_sha256("T2")) == 64


def test_alpha_selection_uses_worst_fold_then_larger_alpha() -> None:
    utilities = {1: (10, 12), 10: (10, 11), 100: (9, 100), 1000: (10, 11)}
    assert select_alpha_by_worst_fold(utilities) == 1000


def test_t2_model_identity_is_reproducible_and_drift_sensitive() -> None:
    first = identity()
    assert first == identity()
    assert first.model_sha256 != identity(blas_lapack_identity="different-blas").model_sha256
    values = first.model_dump(mode="python")
    values["model_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        R03T2ModelIdentity.model_validate(values)


def test_sklearn_absence_fails_closed_without_dependency_install(monkeypatch) -> None:
    original = importlib.metadata.version

    def missing(name: str) -> str:
        if name == "scikit-learn":
            raise importlib.metadata.PackageNotFoundError(name)
        return original(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    with pytest.raises(R03DependencyUnavailable, match="fitting remains fail-closed"):
        installed_t2_runtime()


def test_t2_t3_payload_identity_is_exact() -> None:
    assert_t2_t3_information_equal(SHA, SHA)
    with pytest.raises(ValueError):
        assert_t2_t3_information_equal(SHA, "b" * 64)


def test_t0_preprocessing_and_t1_join_are_deterministic() -> None:
    features = frozen_tier_configs()["T0"]["features"]
    rows = {
        "AAA": {feature: 1.0 for feature in features},
        "BBB": {feature: 2.0 for feature in features},
        "CCC": {feature: None for feature in features},
    }
    sectors = {"AAA": "TECH", "BBB": "TECH", "CCC": "HEALTH"}
    t0 = preprocess_t0_cross_section(rows, sectors)
    assert t0 == preprocess_t0_cross_section(rows, sectors)
    assert all(t0["CCC"][feature + "_missing"] == 1.0 for feature in features)
    t1 = add_t1_sentiment(t0, {"AAA": 0.2, "BBB": None})
    assert t1["AAA"]["sentiment_available"] == 1.0
    assert t1["BBB"]["sentiment_mean_3d"] == 0.0


def test_t2_fit_path_requires_separate_authority_before_sklearn_import() -> None:
    with pytest.raises(ValueError, match="separate frame-and-fit authorization"):
        fit_t2_after_separate_authorization(
            authorization="CODE_ONLY_AUTHORIZED",
            payloads=("synthetic text",),
            residual_targets=__import__("numpy").asarray([0.0]),
            alpha=1,
        )
