"""Frozen R03 tier configurations and fail-closed model identities.

No fitting occurs in this module.  The future sklearn-backed adapter refuses
to construct a runtime identity when the separately approved dependency is
unavailable.
"""

from __future__ import annotations

import importlib.metadata
import platform
import sys
from collections.abc import Mapping
from typing import Any

import numpy as np
import scipy

from v2.research.overlay.canonical import canonical_sha256

from .r03_contracts import float64_hex, R03ContractError, R03T2ModelIdentity
from .r03_payload import assert_information_equal

T0_FEATURES = (
    "sector_relative_log_return_5",
    "sector_relative_log_return_20",
    "sector_relative_log_return_60",
    "volatility_20",
    "volatility_60",
    "downside_semideviation_20",
    "sector_beta_60",
    "mean_log_dollar_volume_20",
    "volume_shock_5_vs_20",
)
T0_ALPHA_GRID = (0.1, 1.0, 10.0, 100.0)
T2_ALPHA_GRID = (1, 10, 100, 1000)
T2_HASHING_VECTORIZER_ID = "sklearn.feature_extraction.text.HashingVectorizer(word,ngram_range=(1,2),n_features=262144,lowercase=True,alternate_sign=False)"
T2_TFIDF_TRANSFORMER_ID = "sklearn.feature_extraction.text.TfidfTransformer(norm=l2,use_idf=True,smooth_idf=True,sublinear_tf=True)"
T2_RIDGE_IMPLEMENTATION_ID = "sklearn.linear_model.Ridge(solver=lsqr,tol=1e-6,max_iter=10000)"


class R03TierError(R03ContractError):
    pass


class R03DependencyUnavailable(R03TierError):
    pass


def frozen_tier_configs() -> dict[str, dict[str, object]]:
    return {
        "T0": {
            "features": T0_FEATURES,
            "impute": "same_date_sector_then_universe_median",
            "clip_percentiles": (1, 99),
            "sector_demean": True,
            "zscore": True,
            "alpha_grid": T0_ALPHA_GRID,
            "fold_ends": (2017, 2018, 2019, 2020),
            "tie": "highest_worst_fold_net_utility_then_larger_alpha",
        },
        "T1": {"base": "T0", "sentiment": "frozen_finbert_sentiment_mean_3d", "availability_flag": True},
        "T2": {
            "base": "T0_residual",
            "vectorizer": T2_HASHING_VECTORIZER_ID,
            "tfidf": T2_TFIDF_TRANSFORMER_ID,
            "ridge": T2_RIDGE_IMPLEMENTATION_ID,
            "alpha_grid": T2_ALPHA_GRID,
            "monthly_expanding_matured_labels_only": True,
            "prediction_clip": "training_window_1_99",
        },
        "T3_CONTRACT_ONLY": {"payload": "byte_identical_to_T2", "inference": "NO_GO"},
    }


def tier_config_sha256(tier: str) -> str:
    configs = frozen_tier_configs()
    if tier not in configs:
        raise R03TierError(f"unknown tier: {tier}")
    return canonical_sha256(configs[tier])


def select_alpha_by_worst_fold(fold_utility_e12: Mapping[float | int, tuple[int, ...]]) -> float | int:
    if not fold_utility_e12 or any(not values for values in fold_utility_e12.values()):
        raise R03TierError("every alpha requires at least one fold utility")
    return max(fold_utility_e12, key=lambda alpha: (min(fold_utility_e12[alpha]), float(alpha)))


def assert_t2_t3_information_equal(t2_payload_sha256: str, t3_payload_sha256: str) -> None:
    assert_information_equal(t2_payload_sha256, t3_payload_sha256)


def installed_t2_runtime() -> dict[str, str]:
    try:
        sklearn_version = importlib.metadata.version("scikit-learn")
    except importlib.metadata.PackageNotFoundError as exc:
        raise R03DependencyUnavailable("scikit-learn is not installed; T2 fitting remains fail-closed") from exc
    return {
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "scikit_learn_version": sklearn_version,
    }


def numpy_blas_lapack_identity() -> str:
    config = getattr(np.__config__, "CONFIG", None)
    return canonical_sha256({"numpy_config": config if config is not None else "unavailable", "byteorder": sys.byteorder})


def build_t2_model_identity(
    *,
    runtime: Mapping[str, str],
    canonical_schema_sha256: str,
    payload_sha256: str,
    training_frame_sha256: str,
    split_sha256: str,
    feature_config_sha256: str,
    selected_alpha: int,
    prediction_clip_low: float,
    prediction_clip_high: float,
    fitted_parameter_sha256: str,
    blas_lapack_identity: str,
) -> R03T2ModelIdentity:
    required = {"python_version", "numpy_version", "scipy_version", "scikit_learn_version"}
    if set(runtime) != required or any(not runtime[key] for key in required):
        raise R03TierError("runtime identity is incomplete")
    unsigned = {
        "schema_version": "r03-t2-model-identity-v1",
        **dict(runtime),
        "hashing_vectorizer_id": T2_HASHING_VECTORIZER_ID,
        "tfidf_transformer_id": T2_TFIDF_TRANSFORMER_ID,
        "ridge_implementation_id": T2_RIDGE_IMPLEMENTATION_ID,
        "solver": "lsqr",
        "solver_tolerance_hex": float64_hex(1e-6),
        "solver_max_iterations": 10_000,
        "blas_lapack_identity": blas_lapack_identity,
        "canonical_schema_sha256": canonical_schema_sha256,
        "payload_sha256": payload_sha256,
        "training_frame_sha256": training_frame_sha256,
        "split_sha256": split_sha256,
        "feature_config_sha256": feature_config_sha256,
        "selected_alpha": selected_alpha,
        "prediction_clip_low_hex": float64_hex(prediction_clip_low),
        "prediction_clip_high_hex": float64_hex(prediction_clip_high),
        "fitted_parameter_sha256": fitted_parameter_sha256,
    }
    return R03T2ModelIdentity(**unsigned, model_sha256=canonical_sha256(unsigned))


def preprocess_t0_cross_section(
    rows: Mapping[str, Mapping[str, float | None]],
    sectors: Mapping[str, str],
) -> dict[str, dict[str, float]]:
    """Apply frozen impute/clip/sector-demean/z-score rules to one date."""

    tickers = sorted(rows)
    if set(tickers) != set(sectors):
        raise R03TierError("T0 rows and sector map must have identical tickers")
    output = {ticker: {} for ticker in tickers}
    for feature in T0_FEATURES:
        finite = {ticker: float(value) for ticker in tickers if (value := rows[ticker].get(feature)) is not None and np.isfinite(float(value))}
        universe_values = sorted(finite.values())
        universe_median = float(np.median(universe_values)) if universe_values else 0.0
        sector_values: dict[str, list[float]] = {}
        for ticker, value in finite.items():
            sector_values.setdefault(sectors[ticker], []).append(value)
        imputed = {
            ticker: finite.get(
                ticker,
                float(np.median(sector_values[sectors[ticker]])) if sectors[ticker] in sector_values else universe_median,
            )
            for ticker in tickers
        }
        values = np.asarray([imputed[ticker] for ticker in tickers], dtype=np.float64)
        low, high = np.percentile(values, [1, 99], method="linear")
        clipped = {ticker: float(np.clip(imputed[ticker], low, high)) for ticker in tickers}
        sector_mean = {sector: float(np.mean([clipped[ticker] for ticker in tickers if sectors[ticker] == sector])) for sector in sorted(set(sectors.values()))}
        demeaned = np.asarray([clipped[ticker] - sector_mean[sectors[ticker]] for ticker in tickers])
        scale = float(demeaned.std(ddof=0))
        for index, ticker in enumerate(tickers):
            output[ticker][feature] = 0.0 if scale == 0.0 else float(demeaned[index] / scale)
            output[ticker][feature + "_missing"] = 0.0 if ticker in finite else 1.0
    return output


def add_t1_sentiment(
    t0_rows: Mapping[str, Mapping[str, float]],
    sentiment_mean_3d: Mapping[str, float | None],
) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for ticker in sorted(t0_rows):
        value = sentiment_mean_3d.get(ticker)
        available = value is not None and np.isfinite(float(value))
        result[ticker] = {
            **dict(t0_rows[ticker]),
            "sentiment_mean_3d": float(value) if available else 0.0,
            "sentiment_available": 1.0 if available else 0.0,
        }
    return result


def fit_t2_after_separate_authorization(
    *,
    authorization: str,
    payloads: tuple[str, ...],
    residual_targets: np.ndarray,
    alpha: int,
) -> tuple[Any, Any, Any]:
    """Future fit adapter. Current CODE_ONLY authority fails before import."""

    if authorization != "FRAME_MATERIALIZATION_AND_T2_FIT_AUTHORIZED":
        raise R03TierError("T2 fitting requires separate frame-and-fit authorization")
    installed_t2_runtime()
    from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
    from sklearn.linear_model import Ridge

    vectorizer = HashingVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        n_features=2**18,
        lowercase=True,
        alternate_sign=False,
        norm=None,
    )
    transformer = TfidfTransformer(norm="l2", use_idf=True, smooth_idf=True, sublinear_tf=True)
    matrix = transformer.fit_transform(vectorizer.transform(payloads))
    model = Ridge(alpha=alpha, solver="lsqr", tol=1e-6, max_iter=10_000)
    model.fit(matrix, residual_targets)
    return vectorizer, transformer, model
