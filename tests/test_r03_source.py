from __future__ import annotations

from pathlib import Path

import pytest

from v2.research.news_reasoning.r03_source import (
    public_retention,
    R03RawTextEmissionError,
    R03SourceAccessDenied,
    recompute_payload_retention_from_read_only_raw_source,
    reject_raw_text_emission,
)


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
