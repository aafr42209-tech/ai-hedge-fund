"""Frozen deterministic public-information scorer family for overlay v2."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .arithmetic import BASIS_POINTS, round_ratio_half_even
from .canonical import canonical_sha256
from .contracts import ASSET_IDS, SIGNAL_IDS, StrictModel
from .r02_v2_contracts import R02V2Payload
from .r02_v2_payload import (
    assert_public_metrics_reproduce,
    canonical_candidate_id,
    decision_batch_from_v2,
    public_episode_from_context,
)
from .scoring import score_with_returns
from .validator import validate_batch

FORECAST_SCALES_BPS = (150, 300, 600)
EQUAL_SIGNAL_WEIGHTS = {signal_id: 2_000 for signal_id in SIGNAL_IDS}
HEAVY_SIGNAL_WEIGHTS = {heavy_id: {signal_id: 4_000 if signal_id == heavy_id else 1_500 for signal_id in SIGNAL_IDS} for heavy_id in SIGNAL_IDS}


class R02V2ComparatorError(RuntimeError):
    """Raised when a deterministic scorer violates the frozen public boundary."""


class R02V2ScorerConfig(StrictModel):
    scorer_id: str
    kind: Literal["ZERO_FORECAST_MIN_RISK_COST", "PUBLIC_SIGNAL_PROXY"]
    signal_weights_bps: dict[str, int]
    forecast_scale_bps: int = Field(ge=0)
    complexity_rank: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_config(self) -> "R02V2ScorerConfig":
        if set(self.signal_weights_bps) != set(SIGNAL_IDS):
            raise ValueError("signal weights must contain S0 through S4")
        if sum(self.signal_weights_bps.values()) not in {0, 10_000}:
            raise ValueError("signal weights must sum to zero or 10000")
        if self.kind == "ZERO_FORECAST_MIN_RISK_COST":
            if self.forecast_scale_bps != 0 or any(self.signal_weights_bps.values()):
                raise ValueError("zero-forecast scorer must have zero proxy inputs")
        elif self.forecast_scale_bps not in FORECAST_SCALES_BPS:
            raise ValueError("public scorer forecast scale is not frozen")
        return self


class R02V2CandidateScore(StrictModel):
    presented_id: str
    canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    return_e12: int
    risk_e12: int
    cost_e12: int
    utility_e12: int


class R02V2ComparatorSelection(StrictModel):
    schema_version: Literal["r02-overlay-v2-comparator-selection-v1"] = "r02-overlay-v2-comparator-selection-v1"
    scorer_id: str
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selected_presented_id: str
    selected_canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_scores: tuple[R02V2CandidateScore, ...]
    selection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_selection_hash(self) -> "R02V2ComparatorSelection":
        expected = canonical_sha256(
            {
                "schema_version": self.schema_version,
                "scorer_id": self.scorer_id,
                "payload_sha256": self.payload_sha256,
                "selected_presented_id": self.selected_presented_id,
                "selected_canonical_candidate_id": (self.selected_canonical_candidate_id),
                "candidate_scores": self.candidate_scores,
            }
        )
        if self.selection_sha256 != expected:
            raise ValueError("comparator selection hash mismatch")
        return self


def scorer_configurations() -> tuple[R02V2ScorerConfig, ...]:
    configs: list[R02V2ScorerConfig] = [
        R02V2ScorerConfig(
            scorer_id="ZERO_FORECAST_MIN_RISK_COST",
            kind="ZERO_FORECAST_MIN_RISK_COST",
            signal_weights_bps={signal_id: 0 for signal_id in SIGNAL_IDS},
            forecast_scale_bps=0,
            complexity_rank=0,
        )
    ]
    weight_sets = (
        ("EQUAL", EQUAL_SIGNAL_WEIGHTS, 1),
        *(
            (
                f"{signal_id}_HEAVY",
                HEAVY_SIGNAL_WEIGHTS[signal_id],
                2 + index,
            )
            for index, signal_id in enumerate(SIGNAL_IDS)
        ),
    )
    for weight_id, weights, complexity_rank in weight_sets:
        for scale in FORECAST_SCALES_BPS:
            configs.append(
                R02V2ScorerConfig(
                    scorer_id=f"PUBLIC_{weight_id}_SCALE_{scale:04d}",
                    kind="PUBLIC_SIGNAL_PROXY",
                    signal_weights_bps=dict(weights),
                    forecast_scale_bps=scale,
                    complexity_rank=complexity_rank,
                )
            )
    if len(configs) != 19 or len({item.scorer_id for item in configs}) != 19:
        raise R02V2ComparatorError("frozen scorer family is not exactly 19")
    return tuple(configs)


def scorer_by_id(scorer_id: str) -> R02V2ScorerConfig:
    by_id = {config.scorer_id: config for config in scorer_configurations()}
    try:
        return by_id[scorer_id]
    except KeyError as exc:
        raise R02V2ComparatorError(f"unknown frozen scorer: {scorer_id}") from exc


def public_return_proxy_bps(
    payload: R02V2Payload,
    config: R02V2ScorerConfig,
) -> dict[str, int]:
    if config.kind == "ZERO_FORECAST_MIN_RISK_COST":
        return {asset_id: 0 for asset_id in ASSET_IDS}
    assets = {asset.asset_id: asset for asset in payload.public_context.assets}
    return {
        asset_id: round_ratio_half_even(
            sum(config.signal_weights_bps[signal_id] * assets[asset_id].signals_bps[signal_id] * assets[asset_id].confidences_bps[signal_id] for signal_id in SIGNAL_IDS) * config.forecast_scale_bps,
            BASIS_POINTS**3,
        )
        for asset_id in ASSET_IDS
    }


def select_with_scorer(
    payload: R02V2Payload,
    scorer_id: str,
) -> R02V2ComparatorSelection:
    assert_public_metrics_reproduce(payload)
    config = scorer_by_id(scorer_id)
    public = public_episode_from_context(payload.public_context)
    expected_returns = public_return_proxy_bps(payload, config)
    scores: list[R02V2CandidateScore] = []
    for presented in payload.candidates:
        validation = validate_batch(
            public,
            decision_batch_from_v2(presented.candidate),
        )
        if not validation.raw_valid or validation.fell_back:
            raise R02V2ComparatorError(f"candidate became nonexecutable: {presented.presented_id}")
        score = score_with_returns(
            public,
            expected_returns,
            validation.executable,
            validation.cost_ledger,
        )
        scores.append(
            R02V2CandidateScore(
                presented_id=presented.presented_id,
                canonical_candidate_id=canonical_candidate_id(presented.candidate),
                return_e12=score.return_e12,
                risk_e12=score.risk_e12,
                cost_e12=score.cost_e12,
                utility_e12=score.utility_e12,
            )
        )
    selected = min(
        scores,
        key=lambda item: (-item.utility_e12, item.canonical_candidate_id),
    )
    body = {
        "schema_version": "r02-overlay-v2-comparator-selection-v1",
        "scorer_id": config.scorer_id,
        "payload_sha256": payload.sha256(),
        "selected_presented_id": selected.presented_id,
        "selected_canonical_candidate_id": selected.canonical_candidate_id,
        "candidate_scores": tuple(scores),
    }
    return R02V2ComparatorSelection(
        **body,
        selection_sha256=canonical_sha256(body),
    )


def all_scorer_selections(
    payload: R02V2Payload,
) -> tuple[R02V2ComparatorSelection, ...]:
    return tuple(select_with_scorer(payload, config.scorer_id) for config in scorer_configurations())
