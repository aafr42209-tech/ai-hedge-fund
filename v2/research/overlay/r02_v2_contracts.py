"""Strict provider-free contracts for the R02 overlay-v2 intervention."""

from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .canonical import canonical_json_bytes, sha256_hex
from .contracts import ASSET_IDS, SIGNAL_IDS, StrictModel

ROOT = Path(__file__).resolve().parents[3]
PAYLOAD_SCHEMA_PATH = ROOT / "docs/r02-overlay-v2-payload-schema-draft.json"
RESPONSE_SCHEMA_PATH = ROOT / "docs/r02-overlay-v2-response-schema-draft.json"
PAYLOAD_SCHEMA_SHA256 = "6a827af6ff6c56f2b4db1c575a1fe2890417ac8feba1ffbb0feb9bec3e1456d5"
RESPONSE_SCHEMA_SHA256 = "963a7fb8ddfa002402e44e94518c6fd4ba3aa964b5a5d353eae09480bd9859c1"
PAYLOAD_SCHEMA_VERSION = "r02-overlay-v2-selector-input-draft-v1"
RESPONSE_SCHEMA_VERSION = "r02-overlay-v2-selector-response-draft-v1"
FIELD_REF_PATTERN = re.compile(r"^/(public_context|candidates)(?:/(?:[^~/]|~0|~1)*)+$")


class R02V2ContractError(RuntimeError):
    """Raised when an accepted overlay-v2 contract is unavailable or drifts."""


class R02V2ReasonCode(StrEnum):
    RISK_CONCENTRATION = "RISK_CONCENTRATION"
    POSITION_ASYMMETRY = "POSITION_ASYMMETRY"
    PUBLIC_SIGNAL_ALIGNMENT = "PUBLIC_SIGNAL_ALIGNMENT"
    CROSS_ASSET_INTERACTION = "CROSS_ASSET_INTERACTION"
    COST_TRADEOFF = "COST_TRADEOFF"
    PARSIMONY = "PARSIMONY"
    TIE_BREAK = "TIE_BREAK"


class R02V2FailureLabel(StrEnum):
    INVALID_JSON = "INVALID_JSON"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    UNKNOWN_PRESENTED_ID = "UNKNOWN_PRESENTED_ID"
    DUPLICATE_REASON_CODE = "DUPLICATE_REASON_CODE"
    INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE = "INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE"


class R02V2CostSchedule(StrictModel):
    commission_cents: int = Field(ge=0)
    half_spread_bps: int = Field(ge=0)
    slippage_bps: int = Field(ge=0)


class R02V2Asset(StrictModel):
    asset_id: str
    price_cents: int = Field(gt=0)
    lot_size_shares: int = Field(gt=0)
    holdings_shares: int = Field(ge=0)
    signals_bps: dict[str, int]
    confidences_bps: dict[str, int]
    max_weight_bps: int = Field(gt=0, le=10_000)
    costs: R02V2CostSchedule

    @model_validator(mode="after")
    def validate_asset(self) -> "R02V2Asset":
        if self.asset_id not in ASSET_IDS:
            raise ValueError("asset_id must be A0 through A5")
        if set(self.signals_bps) != set(SIGNAL_IDS):
            raise ValueError("signals_bps must contain S0 through S4")
        if set(self.confidences_bps) != set(SIGNAL_IDS):
            raise ValueError("confidences_bps must contain S0 through S4")
        if any(not -10_000 <= value <= 10_000 for value in self.signals_bps.values()):
            raise ValueError("signals_bps values must be in [-10000,10000]")
        if any(not 0 <= value <= 10_000 for value in self.confidences_bps.values()):
            raise ValueError("confidences_bps values must be in [0,10000]")
        if self.holdings_shares % self.lot_size_shares:
            raise ValueError("holdings must be an exact lot multiple")
        return self


class R02V2PublicContext(StrictModel):
    assets: tuple[R02V2Asset, ...]
    cash_cents: int = Field(ge=0)
    covariance_bp2: dict[str, dict[str, int]]
    gross_limit_bps: int = Field(gt=0, le=10_000)
    lambda_ppm: int = Field(gt=0)
    max_trade_lots: Literal[2] = 2
    pretrade_equity_cents: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_context(self) -> "R02V2PublicContext":
        if tuple(asset.asset_id for asset in self.assets) != ASSET_IDS:
            raise ValueError("assets must be ordered A0 through A5")
        if set(self.covariance_bp2) != set(ASSET_IDS):
            raise ValueError("covariance rows must contain A0 through A5")
        for row_id in ASSET_IDS:
            row = self.covariance_bp2[row_id]
            if set(row) != set(ASSET_IDS):
                raise ValueError("covariance columns must contain A0 through A5")
            for column_id in ASSET_IDS:
                if row[column_id] != self.covariance_bp2[column_id][row_id]:
                    raise ValueError("covariance must be symmetric")
        equity = self.cash_cents + sum(asset.price_cents * asset.holdings_shares for asset in self.assets)
        if equity != self.pretrade_equity_cents:
            raise ValueError("pretrade equity does not reproduce")
        return self


class R02V2Decision(StrictModel):
    action: Literal["buy", "sell", "hold"]
    quantity: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_action_quantity(self) -> "R02V2Decision":
        if self.action == "hold" and self.quantity != 0:
            raise ValueError("hold requires zero quantity")
        if self.action != "hold" and self.quantity <= 0:
            raise ValueError("buy and sell require positive quantity")
        return self


class R02V2CandidateBatch(StrictModel):
    schema_version: Literal["r02-candidate-decision-v1"] = "r02-candidate-decision-v1"
    decisions: dict[str, R02V2Decision]

    @field_validator("decisions")
    @classmethod
    def validate_decision_keys(cls, value: dict[str, R02V2Decision]) -> dict[str, R02V2Decision]:
        if set(value) != set(ASSET_IDS):
            raise ValueError("decisions must contain A0 through A5")
        return value


class R02V2PublicMetrics(StrictModel):
    non_hold_action_count: int = Field(ge=0, le=6)
    total_quantity_shares: int = Field(ge=0)
    estimated_transaction_cost_cents: int = Field(ge=0)
    projected_holdings_shares: dict[str, int]
    posttrade_gross_weight_bps: int = Field(ge=0)
    max_posttrade_asset_weight_bps: int = Field(ge=0)
    posttrade_variance_numerator: int = Field(ge=0)

    @field_validator("projected_holdings_shares")
    @classmethod
    def validate_projected_keys(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != set(ASSET_IDS) or any(item < 0 for item in value.values()):
            raise ValueError("projected holdings must contain nonnegative A0 through A5")
        return value


class R02V2PresentedCandidate(StrictModel):
    presented_id: str = Field(pattern=r"^P[0-9]{2}$")
    candidate: R02V2CandidateBatch
    public_metrics: R02V2PublicMetrics


class R02V2Payload(StrictModel):
    schema_version: Literal[PAYLOAD_SCHEMA_VERSION] = PAYLOAD_SCHEMA_VERSION
    public_context: R02V2PublicContext
    candidates: tuple[R02V2PresentedCandidate, ...] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def validate_candidates(self) -> "R02V2Payload":
        expected = tuple(f"P{index:02d}" for index in range(len(self.candidates)))
        if tuple(item.presented_id for item in self.candidates) != expected:
            raise ValueError("presented IDs must be contiguous and ordered")
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self)

    def sha256(self) -> str:
        return sha256_hex(self.canonical_bytes())


class R02V2Reason(StrictModel):
    code: R02V2ReasonCode
    field_refs: tuple[str, ...] = Field(min_length=1, max_length=6)

    @field_validator("field_refs")
    @classmethod
    def validate_unique_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("field_refs must be unique")
        if any(len(item) > 256 for item in value):
            raise ValueError("field reference exceeds 256 codepoints")
        if any(not FIELD_REF_PATTERN.fullmatch(item) for item in value):
            raise ValueError("field reference violates the accepted lexical contract")
        return value


class R02V2Response(StrictModel):
    schema_version: Literal[RESPONSE_SCHEMA_VERSION] = RESPONSE_SCHEMA_VERSION
    selected_candidate_id: str = Field(pattern=r"^P[0-9]{2}$")
    confidence: int = Field(ge=0, le=100)
    reasons: tuple[R02V2Reason, ...] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def validate_unique_reason_codes(self) -> "R02V2Response":
        codes = tuple(reason.code for reason in self.reasons)
        if len(codes) != len(set(codes)):
            raise ValueError("reason codes must be unique")
        return self


class R02V2PolicyBinding(StrictModel):
    policy_id: Literal["PUBLIC_SCORE_V2", "LLM_OVERLAY_V2"]
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class R02V2InformationParity(StrictModel):
    deterministic: R02V2PolicyBinding
    llm: R02V2PolicyBinding

    @model_validator(mode="after")
    def validate_same_payload(self) -> "R02V2InformationParity":
        if self.deterministic.payload_sha256 != self.llm.payload_sha256:
            raise ValueError("both policies must bind byte-identical payloads")
        return self


def _load_schema(path: Path, expected_sha256: str) -> dict[str, Any]:
    blob = path.read_bytes()
    if sha256_hex(blob) != expected_sha256:
        raise R02V2ContractError(f"accepted schema digest drift: {path.name}")
    try:
        value = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise R02V2ContractError(f"invalid accepted schema: {path.name}") from exc
    if not isinstance(value, dict) or blob != canonical_json_bytes(value):
        raise R02V2ContractError(f"accepted schema is not canonical: {path.name}")
    return value


def accepted_payload_schema() -> dict[str, Any]:
    return _load_schema(PAYLOAD_SCHEMA_PATH, PAYLOAD_SCHEMA_SHA256)


def accepted_response_schema() -> dict[str, Any]:
    return _load_schema(RESPONSE_SCHEMA_PATH, RESPONSE_SCHEMA_SHA256)


def validate_accepted_metaschemas() -> tuple[str, str]:
    """Validate both accepted drafts against JSON Schema 2020-12."""

    from jsonschema import Draft202012Validator

    payload = accepted_payload_schema()
    response = accepted_response_schema()
    Draft202012Validator.check_schema(payload)
    Draft202012Validator.check_schema(response)
    return PAYLOAD_SCHEMA_SHA256, RESPONSE_SCHEMA_SHA256


def validate_payload_instance(payload: R02V2Payload) -> None:
    from jsonschema import Draft202012Validator

    Draft202012Validator(accepted_payload_schema()).validate(payload.model_dump(mode="json"))


def validate_response_instance(response: R02V2Response) -> None:
    from jsonschema import Draft202012Validator

    Draft202012Validator(accepted_response_schema()).validate(response.model_dump(mode="json"))
