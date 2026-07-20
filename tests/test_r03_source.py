from __future__ import annotations

from pathlib import Path

import pytest

from v2.research.news_reasoning.r03_source import (
    public_retention,
    public_retention_v2,
    R03DataCheckPermitV2,
    R03RawTextEmissionError,
    R03SourceAccessDenied,
    recompute_payload_retention_from_read_only_raw_source,
    recompute_payload_retention_v2_from_read_only_raw_source,
    reject_raw_text_emission,
    root_path_sha256,
    round_half_even_percent,
)
from v2.research.overlay.canonical import canonical_sha256


def test_recompute_payload_retention_from_read_only_raw_source() -> None:
    called = False

    def forbidden_callback(_: Path):
        nonlocal called
        called = True
        return ()

    with pytest.raises(R03SourceAccessDenied, match="permit required"):
        recompute_payload_retention_from_read_only_raw_source(Path("synthetic-never-opened"), None, forbidden_callback)
    assert called is False


def test_public_retention_is_digest_reproducible() -> None:
    rows = ((True, 100, 90), (False, 80, 0), (True, 50, 50))
    first = public_retention(rows)
    second = public_retention(rows)
    assert first == second
    assert first.full_frames_retained == 2
    assert first.article_appearances_retained == 2
    assert first.retained_text_bytes == 140


def test_public_retention_v2_separates_frame_and_appearance_denominators() -> None:
    frame_rows = (True, False, True)
    appearance_rows = (
        (True, 100, 90),
        (True, 80, 80),
        (False, 50, 0),
        (True, 20, 10),
    )
    first = public_retention_v2(frame_rows, appearance_rows)
    second = public_retention_v2(frame_rows, appearance_rows)
    assert first == second
    assert first.schema_version == "r03-public-retention-v2"
    assert (first.full_frames_retained, first.full_frames_total) == (2, 3)
    assert (first.article_appearances_retained, first.article_appearances_total) == (3, 4)
    assert (first.retained_text_bytes, first.input_text_bytes) == (180, 250)
    assert first.full_frame_retention_pct_2dp == "66.67"
    assert first.article_appearance_retention_pct_2dp == "75.00"
    assert first.text_byte_retention_pct_2dp == "72.00"


def test_round_half_even_percent_handles_both_exact_tie_directions() -> None:
    assert round_half_even_percent(1, 32) == "3.12"
    assert round_half_even_percent(3, 32) == "9.38"
    assert round_half_even_percent(695_948, 702_489) == "99.07"
    assert round_half_even_percent(1_435_742_878, 1_585_976_846) == "90.53"


def test_public_retention_v2_rejects_float_and_inconsistent_rows() -> None:
    with pytest.raises(TypeError, match="byte counts must be integers"):
        public_retention_v2((True,), ((True, 1.0, 1),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="omitted appearance"):
        public_retention_v2((True,), ((False, 10, 1),))


def test_v2_rerun_permit_fails_before_callback_or_traversal() -> None:
    root = Path("synthetic-never-opened")
    unsigned = {
        "schema_version": "r03-data-check-permit-v2",
        "authorization": "READ_ONLY_DATA_CHECK_RERUN_AUTHORIZED",
        "root_path_sha256": root_path_sha256(root),
        "plan_commit": "6da16688b3da581d1a919d7c75e285827ed10e85",
        "implementation_commit": "4c47ec61d85e3382c4dd4acfaa0281ca8a1950cd",
        "early_close_session_count": 21,
        "early_close_sessions_sha256": "a" * 64,
        "calendar_session_count": 2514,
        "calendar_sha256": "b" * 64,
        "article_byte_cap": 32768,
        "ticker_session_byte_cap": 131072,
        "article_ordering": "available_at_desc_article_id_asc",
        "truncation_semantics": "headline_summary_then_utf8_content_prefix_omit_after_session_truncation",
        "rounding_rule": "ROUND_HALF_EVEN_2DP",
    }
    permit_sha256 = canonical_sha256(unsigned)
    permit = R03DataCheckPermitV2(**unsigned, permit_sha256=permit_sha256)
    called = False

    def forbidden_callback(_: Path):
        nonlocal called
        called = True
        return (), ()

    with pytest.raises(R03SourceAccessDenied, match="explicitly pinned permit"):
        recompute_payload_retention_v2_from_read_only_raw_source(root, permit, "c" * 64, forbidden_callback)
    assert called is False


def test_reject_raw_text_emission() -> None:
    for key in ("headline", "summary", "content", "body", "raw_text", "prompt"):
        with pytest.raises(R03RawTextEmissionError):
            reject_raw_text_emission({"safe": [{key: "synthetic secret"}]})
    reject_raw_text_emission({"article_count": 3, "payload_sha256": "a" * 64})


def test_source_module_contains_no_approved_corpus_path_literal() -> None:
    import inspect

    import v2.research.news_reasoning.r03_source as source

    text = inspect.getsource(source)
    assert "FinGPT" not in text
    assert "news_raw" not in text
