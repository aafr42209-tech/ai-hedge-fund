"""Strict public and private schemas for R01."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .arithmetic import BASIS_POINTS

ASSET_IDS = tuple(f"A{i}" for i in range(6))
SIGNAL_IDS = tuple(f"S{i}" for i in range(5))
MAX_REASONING_CODEPOINTS = 2_000
Regime = Literal[
    "signal_consensus",
    "signal_conflict",
    "high_transaction_cost",
    "concentration_pressure",
    "existing_position_asymmetry",
    "noisy_confidence",
]


def normalize_artifact_relative_path(value: str) -> str:
    """Return one safe portable artifact path or fail before filesystem access."""

    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    has_windows_drive = len(normalized) >= 2 and normalized[0].isalpha() and normalized[1] == ":"
    if not normalized or normalized.startswith("/") or has_windows_drive or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("artifact path must be a safe relative path")
    return normalized


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
        # Validation only: this float result never enters the authoritative scoring DAG.
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
    reasoning: str = Field(max_length=MAX_REASONING_CODEPOINTS)

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


class ProviderFreeCaseCertificate(StrictModel):
    case_id: str
    regime: Regime
    fixture_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    oracle_utility_e12: int
    hold_utility_e12: int
    oracle_hold_gap_e12: int = Field(ge=0)
    minimum_utility_e12: int
    maximum_abs_utility_e12: int = Field(ge=0)
    maximum_normalized_regret_e12: int = Field(ge=0)
    oracle_certificate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ProviderFreeFreeze(StrictModel):
    schema_version: Literal["r01-provider-free-freeze-v1"] = "r01-provider-free-freeze-v1"
    status: Literal["DEVELOPMENT_ONLY_NOT_SEALED"] = "DEVELOPMENT_ONLY_NOT_SEALED"
    fixture_namespace: Literal["development"] = "development"
    generator_config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scoring_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    root_seed_label: str = Field(min_length=1)
    root_seed_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixture_count: int = Field(gt=0)
    normalization_epsilon_rule: Literal["one_basis_point_utility_e12"] = "one_basis_point_utility_e12"
    normalization_epsilon_e12: int = Field(gt=0)
    median_rule: Literal["sorted_middle_half_even_v1"] = "sorted_middle_half_even_v1"
    median_oracle_hold_gap_e12: int = Field(ge=0)
    regret_scale_e12: int = Field(gt=0)
    max_abs_utility_e12: int = Field(ge=0)
    max_normalized_regret_e12: int = Field(ge=0)
    feasible_lattice_bound_certificate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    cases: tuple[ProviderFreeCaseCertificate, ...]

    @model_validator(mode="after")
    def validate_freeze_identity(self) -> "ProviderFreeFreeze":
        if self.fixture_count != len(self.cases):
            raise ValueError("fixture_count must match provider-free cases")
        identities = {(case.case_id, case.fixture_content_sha256) for case in self.cases}
        if len(identities) != len(self.cases):
            raise ValueError("provider-free case identities must be unique")
        if self.regret_scale_e12 != max(
            self.median_oracle_hold_gap_e12,
            self.normalization_epsilon_e12,
        ):
            raise ValueError("regret scale must equal max(median gap, epsilon)")
        if self.max_abs_utility_e12 != max(case.maximum_abs_utility_e12 for case in self.cases):
            raise ValueError("max_abs_utility_e12 does not match cases")
        if self.max_normalized_regret_e12 != max(case.maximum_normalized_regret_e12 for case in self.cases):
            raise ValueError("max_normalized_regret_e12 does not match cases")
        return self


class ProviderFreeRegimeGapStats(StrictModel):
    case_count: int = Field(gt=0)
    zero_gap_count: int = Field(ge=0)
    positive_lte_epsilon_count: int = Field(ge=0)
    gt_epsilon_count: int = Field(ge=0)
    min_gap_e12: int = Field(ge=0)
    median_gap_e12: int = Field(ge=0)
    mean_gap_e12: int = Field(ge=0)
    max_gap_e12: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_gap_stats(self) -> "ProviderFreeRegimeGapStats":
        if self.zero_gap_count + self.positive_lte_epsilon_count + self.gt_epsilon_count != self.case_count:
            raise ValueError("gap buckets must sum to case_count")
        if not (self.min_gap_e12 <= self.median_gap_e12 <= self.max_gap_e12):
            raise ValueError("gap min, median, and max must be ordered")
        if not self.min_gap_e12 <= self.mean_gap_e12 <= self.max_gap_e12:
            raise ValueError("gap mean must lie within min and max")
        return self


class ProviderFreeRegimeGapSummary(StrictModel):
    schema_version: Literal["r01-provider-free-regime-gap-summary-v1"] = "r01-provider-free-regime-gap-summary-v1"
    status: Literal["DEVELOPMENT_ONLY_NOT_SEALED"] = "DEVELOPMENT_ONLY_NOT_SEALED"
    source_freeze_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalization_epsilon_e12: int = Field(gt=0)
    fixture_count: int = Field(gt=0)
    overall: ProviderFreeRegimeGapStats
    regimes: dict[Regime, ProviderFreeRegimeGapStats]
    decision_status: Literal["TBD_D2"] = "TBD_D2"

    @model_validator(mode="after")
    def validate_regime_summary(self) -> "ProviderFreeRegimeGapSummary":
        expected_regimes = {
            "signal_consensus",
            "signal_conflict",
            "high_transaction_cost",
            "concentration_pressure",
            "existing_position_asymmetry",
            "noisy_confidence",
        }
        if set(self.regimes) != expected_regimes:
            raise ValueError("regime summary must contain every R01 regime exactly once")
        if sum(stats.case_count for stats in self.regimes.values()) != self.fixture_count:
            raise ValueError("regime case counts must sum to fixture_count")
        for field_name in (
            "zero_gap_count",
            "positive_lte_epsilon_count",
            "gt_epsilon_count",
        ):
            if sum(getattr(stats, field_name) for stats in self.regimes.values()) != getattr(self.overall, field_name):
                raise ValueError(f"regime {field_name} values must match overall")
        if self.overall.case_count != self.fixture_count:
            raise ValueError("overall case_count must match fixture_count")
        return self


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


class CodexCommandSpec(StrictModel):
    schema_version: Literal["r01-codex-command-spec-v1"] = "r01-codex-command-spec-v1"
    executable: str = Field(min_length=1)
    argv: tuple[str, ...]
    model_id: str = Field(min_length=1)
    sandbox: Literal["read-only"] = "read-only"
    ephemeral: Literal[True] = True
    ignore_user_config: Literal[True] = True
    ignore_rules: Literal[True] = True
    skip_git_repo_check: Literal[True] = True
    strict_config: Literal[True] = True
    jsonl: Literal[True] = True
    disabled_features: tuple[str, ...]
    active_feature_allowlist: tuple[str, ...]
    config_overrides: tuple[str, ...]
    working_directory: str = Field(min_length=1)
    timeout_ms: int = Field(gt=0)
    policy_instruction_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixture_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stdin_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    jsonl_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_command_identity(self) -> "CodexCommandSpec":
        if self.disabled_features != tuple(sorted(set(self.disabled_features))):
            raise ValueError("disabled features must be unique and sorted")
        if self.active_feature_allowlist != tuple(sorted(set(self.active_feature_allowlist))):
            raise ValueError("active feature allowlist must be unique and sorted")
        if set(self.disabled_features) & set(self.active_feature_allowlist):
            raise ValueError("disabled features and active allowlist must be disjoint")
        if any(not name or name.lower() != name or not name.isascii() or not name.replace("_", "").isalnum() for name in self.disabled_features + self.active_feature_allowlist):
            raise ValueError("feature names must be lowercase alphanumeric identifiers")
        if self.config_overrides != tuple(sorted(set(self.config_overrides))):
            raise ValueError("config overrides must be unique and sorted")
        if any("=" not in value or "\n" in value or "\r" in value for value in self.config_overrides):
            raise ValueError("config overrides must be one-line key=value strings")
        config_pairs = [value.split("=", 1) for value in self.config_overrides]
        config_keys = [pair[0] for pair in config_pairs]
        if any(not key or not value for key, value in config_pairs):
            raise ValueError("config override keys and values must be nonempty")
        if len(config_keys) != len(set(config_keys)):
            raise ValueError("config override keys must be unique")
        if "tools.web_search=false" not in self.config_overrides:
            raise ValueError("web search must be disabled")
        if "--output-schema" in self.argv or "--output-last-message" in self.argv:
            raise ValueError("provider-side output filtering is prohibited")
        expected_argv: list[str] = [self.executable]
        for feature in self.disabled_features:
            expected_argv.extend(("--disable", feature))
        expected_argv.extend(
            (
                "exec",
                "--model",
                self.model_id,
                "--sandbox",
                "read-only",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                "--strict-config",
            )
        )
        for config in self.config_overrides:
            expected_argv.extend(("--config", config))
        expected_argv.extend(("--json", "-"))
        if self.argv != tuple(expected_argv):
            raise ValueError("argv does not match the command-spec fields")
        return self


class CodexProcessStatus(StrictModel):
    schema_version: Literal["r01-codex-process-status-v1"] = "r01-codex-process-status-v1"
    exit_code: int | None
    timed_out: bool
    launch_error: str | None = None
    duration_ms: int = Field(ge=0)
    stdout_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stdout_size_bytes: int = Field(ge=0)
    stderr_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stderr_size_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_process_status(self) -> "CodexProcessStatus":
        if self.launch_error is not None and self.exit_code is not None:
            raise ValueError("launch error cannot also have an exit code")
        if not self.timed_out and self.launch_error is None and self.exit_code is None:
            raise ValueError("completed process status requires an exit code")
        return self


class ProviderResponse(StrictModel):
    schema_version: Literal["r01-provider-response-v2"] = "r01-provider-response-v2"
    raw_text: str
    provider: str
    model_id: str
    request_id: str
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_output_tokens: int = Field(ge=0)
    model_identity_verified_by_transport: bool
    tool_use_violation: bool
    tool_event_types: tuple[str, ...] = ()
    process_status_violation: bool
    event_types: tuple[str, ...]
    agent_message_count: int = Field(gt=0)
    transport_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    process_status: CodexProcessStatus

    @model_validator(mode="after")
    def validate_provider_response(self) -> "ProviderResponse":
        if self.tool_event_types != tuple(sorted(set(self.tool_event_types))):
            raise ValueError("tool event types must be unique and sorted")
        if self.tool_use_violation != bool(self.tool_event_types):
            raise ValueError("tool-use flag must match tool event types")
        if self.transport_sha256 != self.process_status.stdout_sha256:
            raise ValueError("transport hash must match process stdout hash")
        expected_process_violation = self.process_status.timed_out or self.process_status.launch_error is not None or self.process_status.exit_code != 0
        if self.process_status_violation != expected_process_violation:
            raise ValueError("process-status flag does not match process status")
        return self


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
        return normalize_artifact_relative_path(value)


class CodexAttemptTransportArtifacts(StrictModel):
    schema_version: Literal["r01-codex-attempt-transport-artifacts-v1"] = "r01-codex-attempt-transport-artifacts-v1"
    command_spec: ArtifactReference
    stdout_jsonl: ArtifactReference
    stderr: ArtifactReference
    process_status: ArtifactReference
    provider_response: ArtifactReference


class FixtureManifestEntry(StrictModel):
    case_id: str
    regime: Regime
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixture: ArtifactReference


class DevelopmentManifest(StrictModel):
    schema_version: Literal["r01-development-manifest-v2"] = "r01-development-manifest-v2"
    contract_id: Literal["R01-llm-overlay-synthetic-v1"] = "R01-llm-overlay-synthetic-v1"
    experiment_id: str
    status: Literal["DEVELOPMENT_ONLY_NOT_SEALED"] = "DEVELOPMENT_ONLY_NOT_SEALED"
    contract_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    generator_config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scoring_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    analysis_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scoring_spec: ArtifactReference
    analysis_spec: ArtifactReference
    provider_free_freeze_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_free_freeze: ArtifactReference
    normalization_epsilon_e12: int = Field(gt=0)
    regret_scale_e12: int = Field(gt=0)
    feasible_lattice_bound_certificate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
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
