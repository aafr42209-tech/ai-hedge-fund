"""Machine-readable scoring and analysis identities frozen before seal."""

from __future__ import annotations

from .analysis import analysis_spec
from .arithmetic import (
    BASIS_POINTS,
    COVARIANCE_BP2_SCALE,
    PARTS_PER_MILLION,
    UTILITY_SCALE,
)
from .canonical import canonical_sha256


def scoring_spec() -> dict[str, object]:
    return {
        "schema_version": "r01-scoring-v1",
        "authoritative_number_type": "signed_integer_fixed_point",
        "utility_scale": UTILITY_SCALE,
        "basis_points_scale": BASIS_POINTS,
        "parts_per_million_scale": PARTS_PER_MILLION,
        "covariance_bp2_scale": COVARIANCE_BP2_SCALE,
        "rounding": "round_ratio_half_even",
        "intermediate_rounding": "prohibited",
        "return_formula": ("RHE(sum(mu_bp_i*position_cents_i)*utility_scale," "basis_points*posttrade_equity_cents)"),
        "risk_formula": ("RHE(lambda_ppm*sum(position_i*covariance_bp2_i_j*position_j)*utility_scale," "ppm*covariance_bp2_scale*posttrade_equity_cents^2)"),
        "cost_formula": "RHE(total_cost_cents*utility_scale,pretrade_equity_cents)",
        "utility_formula": "return_e12-risk_e12-cost_e12",
        "regret_formula": "RHE(max(oracle-policy,0)*utility_scale,regret_scale_e12)",
        "integer_mean": "RHE(sum(values),count)",
        "oracle_solver": "complete_enumeration_v1",
        "oracle_optimality_tolerance_e12": 0,
        "equal_risk_distance": "asset_weight_e12_L1",
        "equal_risk_tie_break": "cost,turnover,final_share_vector_lexicographic",
        "max_trade_lots_per_asset": 2,
    }


def scoring_spec_sha256() -> str:
    return canonical_sha256(scoring_spec())


def analysis_spec_sha256() -> str:
    return canonical_sha256(analysis_spec())
