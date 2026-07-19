from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jsonschema
import pytest
from pydantic import ValidationError

from v2.research.news_reasoning.r03_contracts import (
    contract_schema_bundle,
    contract_schema_sha256,
    e12_from_float,
    float64_from_hex,
    float64_hex,
    R03ArticleRecord,
    R03FrameRow,
    R03HashPin,
    R03PinKind,
    R03TrainingFrameIdentity,
    R03ZeroCounters,
)

SHA = "1" * 64
NOW = datetime(2022, 1, 3, 15, tzinfo=timezone.utc)


def test_contract_schema_bundle_passes_metaschema() -> None:
    schemas = contract_schema_bundle()
    assert len(schemas) == 12
    for schema in schemas.values():
        jsonschema.Draft202012Validator.check_schema(schema)
    assert len(contract_schema_sha256()) == 64


def test_contracts_are_strict_and_forbid_extras() -> None:
    with pytest.raises(ValidationError):
        R03HashPin(sha256=SHA, pin_kind=R03PinKind.FILESYSTEM_SHA256, unexpected=True)
    with pytest.raises(ValidationError):
        R03ZeroCounters(provider_calls=1)


def test_numeric_contract_normalizes_binary64_and_e12() -> None:
    assert float64_hex(-0.0) == float64_hex(0.0) == "0000000000000000"
    assert float64_from_hex(float64_hex(0.125)) == 0.125
    assert e12_from_float(0.0005) == 500_000_000
    with pytest.raises(ValueError):
        float64_hex(float("nan"))


def test_article_record_rejects_naive_time_and_unsorted_symbols() -> None:
    with pytest.raises(ValueError):
        R03ArticleRecord(
            article_id="synthetic-1",
            created_at=datetime(2022, 1, 1),
            updated_at=datetime(2022, 1, 1),
            symbols=("AAA",),
            headline="Synthetic headline",
            input_text_sha256=SHA,
        )
    with pytest.raises(ValueError):
        R03ArticleRecord(
            article_id="synthetic-1",
            created_at=NOW,
            updated_at=NOW,
            symbols=("BBB", "AAA"),
            headline="Synthetic headline",
            input_text_sha256=SHA,
        )


def test_training_identity_rejects_unmatured_labels() -> None:
    with pytest.raises(ValueError):
        R03TrainingFrameIdentity(
            split_sha256=SHA,
            training_frame_sha256=SHA,
            feature_frame_sha256=SHA,
            label_frame_sha256=SHA,
            maximum_source_at=NOW,
            maximum_label_maturity_at=NOW + timedelta(days=1),
            fit_cutoff_at=NOW,
        )


def test_frame_row_enforces_temporal_order() -> None:
    with pytest.raises(ValueError):
        R03FrameRow(
            decision_id="d1",
            ticker="AAA",
            sector="TECH",
            decision_at=NOW,
            feature_cutoff_at=NOW,
            label_maturity_at=NOW + timedelta(days=7),
            phase_book=0,
            payload_sha256=SHA,
        )
