"""Strict public and private schemas for R01."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .arithmetic import BASIS_POINTS, UTILITY_SCALE

ASSET_IDS = tuple(f"A{i}" for i in range(6))
SIGNAL_IDS = tuple(f"S{i}" for i in range(5))
Regime = Literal[
    "signal_consensus",
    "signal_conflict",
    "high_transaction_cost",
    "concentration_pressure",
    "existing_position_asymmetry",
    "noisy_confidence",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class CostSchedule(StrictModel):
    commission_cents: int = Field(ge=0)
    half_spread_bps: int = Field(ge=0, le=BASIS_POINTS)
    slippage_bps: int = Field(ge=0, le=BASIS_POINTS)


class AssetState(StrictModel):
    asset_id: str
    price_cents: int = Field(gt=0)
    lot_size_shares: int = Field(gt=0)
    holdings_shares: int = Field(ge=0)
    signals_bps: dict[str, int]
    confidences_bps: dict[str, int]
    max_weight_bps: int = Field(gt=0, le=BASIS_POINTS)
    costs: CostSchedule

    @model_validator(mode="after")
    def validate_asset(self) -> "AssetState":
        if self.asset_id not in ASSET_IDS:
            raise ValueError(f"unknown anonymous asset ID: {self.asset_id}")
        if set(self.signals_bps) != set(SIGNAL_IDS):
            raise ValueError("signals_bps must contain exactly S0 through S4")
        if set(self.confidences_bps) != set(SIGNAL_IDS):
            raise ValueError("confidences_bps must contain exactly S0 through S4")
        if any(value < -BASIS_POINTS or value > BASIS_POINTS for value in self.signals_bps.values()):
            raise ValueError("signal values must be in [-10000, 10000]")
        if any(value < 0 or value > BASIS_POINTS for value in self.confidences_bps.values()):
            raise ValueError("confidence values must be in [0, 10000]")
        if self.holdings_shares % self.lot_size_shares:
            raise ValueError("holdings must be an exact lot multiple")
        return self


class PublicEpisode(StrictModel):
    schema_version: Literal["r01-public-v1"] = "r01-public-v1"
    case_id: str = Field(min_length=1)
    seed_hex: str = Field(pattern=r"^[0-9a-f]{64}$")
    assets: tuple[AssetState, ...]
    cash_cents: int = Field(ge=0)
    covariance_bp2: dict[str, dict[str, int]]
    gross_limit_bps: int = Field(gt=0, le=BASIS_POINTS)
    lambda_ppm: int = Field(gt=0)
    max_trade_lots: Literal[2] = 2

    @model_validator(mode="after")
    def validate_episode(self) -> "PublicEpisode":
        ids = tuple(asset.asset_id for asset in self.assets)
        if len(ids) != len(ASSET_IDS) or set(ids) != set(ASSET_IDS):
            raise ValueError("assets must contain exactly A0 through A5")
        if set(self.covariance_bp2) != set(ASSET_IDS):
            raise ValueError("covariance rows must contain exactly A0 through A5")
        matrix: list[list[int]] = []
        for row_id in ASSET_IDS:
            row = self.covariance_bp2[row_id]
            if set(row) != set(ASSET_IDS):
                raise ValueError("covariance columns must contain exactly A0 through A5")
            matrix.append([row[column_id] for column_id in ASSET_IDS])
        for i in range(len(ASSET_IDS)):
            for j in range(len(ASSET_IDS)):
                if matrix[i][j] != matrix[j][i]:
                    raise ValueError("covariance matrix must be symmetric")
        minimum_eigenvalue = float(np.linalg.eigvalsh(np.asarray(matrix, dtype=np.float64)).min())
        if minimum_eigenvalue < -1e-6:
            raise ValueError("covariance matrix must be positive semidefinite")
        if self.pretrade_equity_cents <= 0:
            raise ValueError("pre-trade equity must be positive")
        return self

    @property
    def assets_by_id(self) -> dict[str, AssetState]:
        return {asset.asset_id: asset for asset in self.assets}

    @property
    def pretrade_equity_cents(self) -> int:
        return self.cash_cents + sum(asset.price_cents * asset.holdings_shares for asset in self.assets)


class HiddenEpisodeState(StrictModel):
    regime: Regime
    expected_returns_bps: dict[str, int]

    @field_validator("expected_returns_bps")
    @classmethod
    def validate_returns(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != set(ASSET_IDS):
            raise ValueError("expected returns must contain exactly A0 through A5")
        return value


class SyntheticEpisode(StrictModel):
    public: PublicEpisode
    hidden: HiddenEpisodeState
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Decision(StrictModel):
    action: Literal["buy", "sell", "hold"]
    quantity: int = Field(ge=0)
    confidence: int = Field(ge=0, le=100)
    reasoning: str = Field(max_length=2_000)

    @model_validator(mode="after")
    def validate_quantity_for_action(self) -> "Decision":
        if self.action == "hold" and self.quantity != 0:
            raise ValueError("hold requires quantity 0")
        if self.action != "hold" and self.quantity <= 0:
            raise ValueError("buy and sell require positive quantity")
        return self


class DecisionBatch(StrictModel):
    decisions: dict[str, Decision]

    @field_validator("decisions")
    @classmethod
    def validate_decision_keys(cls, value: dict[str, Decision]) -> dict[str, Decision]:
        if set(value) != set(ASSET_IDS):
            raise ValueError("decisions must contain exactly A0 through A5")
        return value


class Violation(StrictModel):
    code: str
    detail: str
    asset_id: str | None = None


class ExecutableBatch(StrictModel):
    decisions: dict[str, Decision]
    final_shares: dict[str, int]
    cash_after_cents: int
    posttrade_equity_cents: int
    weights_e12: dict[str, int]


class CostLine(StrictModel):
    asset_id: str
    action: Literal["buy", "sell"]
    quantity: int
    notional_cents: int
    commission_cents: int
    half_spread_cents: int
    slippage_cents: int
    total_cost_cents: int


class CostLedger(StrictModel):
    lines: tuple[CostLine, ...] = ()
    total_cost_cents: int = 0
    total_notional_cents: int = 0


class ValidationReport(StrictModel):
    raw_valid: bool
    fell_back: bool
    violations: tuple[Violation, ...]
    executable: ExecutableBatch
    cost_ledger: CostLedger
    executable_violation_count: Literal[0] = 0


class EpisodeScore(StrictModel):
    return_e12: int
    risk_e12: int
    cost_e12: int
    utility_e12: int
    turnover_e12: int
    total_cost_cents: int
    weights_e12: dict[str, int]


class OracleCertificate(StrictModel):
    solver: Literal["complete_enumeration_v1"] = "complete_enumeration_v1"
    candidate_count: int = Field(gt=0)
    feasible_count: int = Field(gt=0)
    best_batch_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    score_stream_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    best_utility_e12: int
    minimum_utility_e12: int
    maximum_abs_utility_e12: int = Field(ge=0)
    oracle_optimality_tolerance_e12: Literal[0] = 0


class PolicyResult(StrictModel):
    name: str
    validation: ValidationReport
    score: EpisodeScore


class OracleResult(StrictModel):
    validation: ValidationReport
    score: EpisodeScore
    certificate: OracleCertificate


class BaselineConfig(StrictModel):
    signal_weights_bps: dict[str, int] = Field(default_factory=lambda: {signal_id: 2_000 for signal_id in SIGNAL_IDS})
    forecast_scale_bps: int = Field(default=300, gt=0)

    @field_validator("signal_weights_bps")
    @classmethod
    def validate_weights(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != set(SIGNAL_IDS) or sum(value.values()) != BASIS_POINTS:
            raise ValueError("signal weights must contain S0-S4 and sum to 10000")
        if any(weight < 0 for weight in value.values()):
            raise ValueError("signal weights must be nonnegative")
        return value


class ScoringConfig(StrictModel):
    utility_scale: Literal[UTILITY_SCALE] = UTILITY_SCALE
    regret_scale_e12: int = Field(gt=0)
    normalization_epsilon_e12: int = Field(gt=0)


class GeneratorConfig(StrictModel):
    schema_version: Literal["r01-generator-draft-v1"] = "r01-generator-draft-v1"
    pretrade_equity_cents: int = 10_000_000
    min_price_cents: int = 2_000
    max_price_cents: int = 20_000
    min_lot_notional_bps: int = 400
    max_lot_notional_bps: int = 800
    min_asset_cap_bps: int = 2_000
    max_asset_cap_bps: int = 3_500
    min_gross_limit_bps: int = 8_000
    max_gross_limit_bps: int = 10_000
    min_confidence_bps: int = 2_000
    normal_commission_max_cents: int = 200
    high_cost_commission_min_cents: int = 500
    high_cost_commission_max_cents: int = 1_000
    normal_cost_bps_max: int = 10
    high_cost_bps_min: int = 25
    high_cost_bps_max: int = 75
    forecast_scale_bps: int = 300
    hidden_noise_bps: int = 25
    lambda_ppm: int = 1_000_000
    max_trade_lots: Literal[2] = 2
    max_generation_attempts: int = 100


class AcquisitionIdentity(StrictModel):
    contract_id: Literal["R01-llm-overlay-synthetic-v1"] = "R01-llm-overlay-synthetic-v1"
    experiment_id: str
    case_id: str
    channel: Literal["development", "primary", "invariance"]
    replicate_id: int | None = None
    perturbation_id: str | None = None
    attempt: int = Field(ge=1, le=2)

    @model_validator(mode="after")
    def validate_identity(self) -> "AcquisitionIdentity":
        if (self.replicate_id is None) == (self.perturbation_id is None):
            raise ValueError("exactly one of replicate_id or perturbation_id is required")
        return self


class ProviderResponse(StrictModel):
    raw_text: str
    provider: str
    model_id: str
    request_id: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BootstrapInterval(StrictModel):
    lower_e12: int
    upper_e12: int
    resamples: int = Field(gt=0)
    lower_zero_based_index: int = Field(ge=0)
    upper_zero_based_index: int = Field(ge=0)
    seed: int = Field(ge=0)


class PowerResult(StrictModel):
    successes: int = Field(ge=0)
    trials: int = Field(gt=0)
    power_e6: int = Field(ge=0, le=1_000_000)
    sample_size: int = Field(gt=0)
    bootstrap_resamples: int = Field(gt=0)
    power_seed: int = Field(ge=0)


class ArtifactReference(StrictModel):
    relative_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
            raise ValueError("artifact path must be a safe relative path")
        return normalized


class FixtureManifestEntry(StrictModel):
    case_id: str
    regime: Regime
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixture: ArtifactReference


class DevelopmentManifest(StrictModel):
    schema_version: Literal["r01-development-manifest-v1"] = "r01-development-manifest-v1"
    contract_id: Literal["R01-llm-overlay-synthetic-v1"] = "R01-llm-overlay-synthetic-v1"
    experiment_id: str
    status: Literal["DEVELOPMENT_ONLY_NOT_SEALED"] = "DEVELOPMENT_ONLY_NOT_SEALED"
    contract_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    generator_config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scoring_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    analysis_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scoring_spec: ArtifactReference
    analysis_spec: ArtifactReference
    root_seed_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixtures: tuple[FixtureManifestEntry, ...]


class RunPlanEntry(StrictModel):
    identity: AcquisitionIdentity
    fixture: ArtifactReference


class DevelopmentRunPlan(StrictModel):
    schema_version: Literal["r01-development-run-plan-v1"] = "r01-development-run-plan-v1"
    experiment_id: str
    status: Literal["DEVELOPMENT_ONLY_NOT_SEALED"] = "DEVELOPMENT_ONLY_NOT_SEALED"
    manifest: ArtifactReference
    entries: tuple[RunPlanEntry, ...]


class AcquisitionArtifacts(StrictModel):
    identity: AcquisitionIdentity
    fixture: ArtifactReference
    policy_input: ArtifactReference
    system_prompt: ArtifactReference
    user_prompt: ArtifactReference
    provider_request: ArtifactReference
    raw_response: ArtifactReference
    provider_response_metadata: ArtifactReference
    parsed_decision: ArtifactReference
    validation_report: ArtifactReference
    executable_batch: ArtifactReference
    cost_ledger: ArtifactReference
    episode_score: ArtifactReference
    oracle_certificate: ArtifactReference


class DevelopmentRunResult(StrictModel):
    schema_version: Literal["r01-development-run-result-v1"] = "r01-development-run-result-v1"
    experiment_id: str
    status: Literal["DEVELOPMENT_ONLY_NOT_SEALED"] = "DEVELOPMENT_ONLY_NOT_SEALED"
    run_plan: ArtifactReference
    acquisitions: tuple[AcquisitionArtifacts, ...]
    report_json: ArtifactReference
    report_markdown: ArtifactReference


class ReplayVerification(StrictModel):
    schema_version: Literal["r01-replay-verification-v1"] = "r01-replay-verification-v1"
    experiment_id: str
    verified_acquisitions: int = Field(ge=0)
    provider_calls: Literal[0] = 0
    all_hashes_match: Literal[True] = True
