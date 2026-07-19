from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from v2.research.news_reasoning.r03_contracts import (
    ARTICLE_BYTE_CAP,
    R03ArticleRecord,
    R03CanonicalBundle,
    TICKER_SESSION_BYTE_CAP,
)
from v2.research.news_reasoning.r03_payload import (
    assert_information_equal,
    build_canonical_bundle,
    canonical_bundle_bytes,
    parse_t3_response,
    R03PayloadError,
    resolve_news_pointer,
    select_latest_versions,
    validate_t3_grounding,
)

NOW = datetime(2022, 6, 1, 19, 0, tzinfo=timezone.utc)


def article(
    article_id: str,
    *,
    updated_hours: int = -1,
    digest_char: str = "a",
    headline: str | None = "Synthetic earnings update",
    summary: str | None = "Synthetic summary",
    content: str | None = "Synthetic body with no licensed text.",
    symbols: tuple[str, ...] = ("AAA",),
) -> R03ArticleRecord:
    updated = NOW + timedelta(hours=updated_hours)
    return R03ArticleRecord(
        article_id=article_id,
        created_at=updated - timedelta(minutes=5),
        updated_at=updated,
        symbols=symbols,
        source="SYNTHETIC",
        headline=headline,
        summary=summary,
        content=content,
        input_text_sha256=digest_char * 64,
    )


def bundle(records: tuple[R03ArticleRecord, ...]) -> R03CanonicalBundle:
    return build_canonical_bundle(records, ticker="AAA", decision_at=NOW, frozen_universe=frozenset({"AAA", "BBB"}))


def test_payload_is_deterministic_ordered_and_information_equal() -> None:
    first = bundle((article("b", updated_hours=-2), article("a", updated_hours=-1)))
    second = bundle((article("a", updated_hours=-1), article("b", updated_hours=-2)))
    assert first == second
    raw = canonical_bundle_bytes(first)
    assert raw.index(b'"article_id"') < raw.index(b'"available_at"') < raw.index(b'"symbols"')
    assert_information_equal(first.payload_sha256, second.payload_sha256)
    assert resolve_news_pointer(first, "/articles/0/headline") == "Synthetic earnings update"


def test_duplicate_rule_selects_updated_at_then_sha256() -> None:
    older = article("same", updated_hours=-2, digest_char="f")
    newer_low_hash = article("same", updated_hours=-1, digest_char="0", headline="Newer")
    same_time_high_hash = article("same", updated_hours=-1, digest_char="f", headline="Tie winner")
    assert select_latest_versions((older, newer_low_hash, same_time_high_hash)) == (same_time_high_hash,)


def test_duplicate_rule_selects_available_at_before_updated_at() -> None:
    later_available = article("same", updated_hours=-2, headline="Later available").model_copy(update={"created_at": NOW - timedelta(minutes=30)})
    later_updated = article("same", updated_hours=-1, headline="Later updated")
    assert select_latest_versions((later_updated, later_available)) == (later_available,)


def test_reject_duplicate_selection_perturbation() -> None:
    low = article("same", digest_char="0", headline="Low hash")
    high = article("same", digest_char="f", headline="High hash")
    selected = select_latest_versions((high, low))
    assert selected[0].headline == "High hash"
    assert bundle((high, low)).payload_sha256 != bundle((low.model_copy(update={"article_id": "different"}),)).payload_sha256


def test_caps_truncate_only_valid_utf8_body_prefix() -> None:
    large = article("large", content="x" * 40_000)
    result = bundle((large,))
    assert result.text_bytes == ARTICLE_BYTE_CAP
    assert result.payload_bytes > result.text_bytes
    assert result.articles[0].content_truncated is True
    assert len(str(result.articles[0].content).encode("utf-8")) < len(str(large.content).encode("utf-8"))
    canonical_bundle_bytes(result).decode("utf-8")


def test_session_truncation_makes_final_article_and_omits_later_articles() -> None:
    def with_text_bytes(article_id: str, updated_hours: int, target: int) -> R03ArticleRecord:
        headline = "Synthetic earnings update"
        summary = "Synthetic summary"
        preserved = len(headline.encode("utf-8")) + len(summary.encode("utf-8"))
        return article(article_id, updated_hours=updated_hours, content="x" * (target - preserved))

    records = tuple([with_text_bytes(article_id, -index, 30_000) for index, article_id in enumerate("abcd", start=1)] + [with_text_bytes("e", -5, 20_000), with_text_bytes("f", -6, 1_000)])
    result = bundle(records)
    assert tuple(item.article_id for item in result.articles) == ("a", "b", "c", "d", "e")
    assert result.articles[-1].content_truncated is True
    assert result.text_bytes == TICKER_SESSION_BYTE_CAP
    assert result.payload_bytes > result.text_bytes


def test_reject_article_byte_cap_perturbation() -> None:
    result = bundle((article("a"),))
    values = result.model_dump(mode="python")
    values["article_byte_cap"] = ARTICLE_BYTE_CAP - 1
    with pytest.raises(ValidationError):
        R03CanonicalBundle.model_validate(values)


def test_reject_ticker_session_byte_cap_perturbation() -> None:
    result = bundle((article("a"),))
    values = result.model_dump(mode="python")
    values["ticker_session_byte_cap"] = TICKER_SESSION_BYTE_CAP - 1
    with pytest.raises(ValidationError):
        R03CanonicalBundle.model_validate(values)


def test_reject_article_ordering_perturbation() -> None:
    result = bundle((article("a", updated_hours=-1), article("b", updated_hours=-2)))
    values = result.model_dump(mode="python")
    values["articles"] = tuple(reversed(values["articles"]))
    with pytest.raises(ValueError, match="canonical order"):
        R03CanonicalBundle.model_validate(values)


def test_missing_headline_and_wide_symbol_article_are_ineligible() -> None:
    missing = article("missing", headline=None)
    wide = article("wide", symbols=("AAA", "BBB", "CCC", "DDD", "EEE", "FFF"))
    assert bundle((missing, wide)).articles == ()


def test_information_parity_and_pointer_fail_closed() -> None:
    result = bundle((article("a"),))
    with pytest.raises(R03PayloadError, match="payload bytes differ"):
        assert_information_equal(result.payload_sha256, "0" * 64)
    with pytest.raises(R03PayloadError):
        resolve_news_pointer(result, "/articles/01/headline")


def test_t3_response_contract_and_grounding_are_provider_free() -> None:
    result = bundle((article("a"),))
    raw = '{"schema_version":"r03-t3-response-contract-v1","ticker":"AAA",' '"score_hex":"3ff0000000000000","confidence":80,"reasons":[' '{"code":"SYNTHETIC","field_refs":["/articles/0/headline"]}]}'
    response = parse_t3_response(raw)
    validate_t3_grounding(response, result)
    with pytest.raises(R03PayloadError, match="duplicate"):
        parse_t3_response(raw.replace('"ticker":"AAA"', '"ticker":"AAA","ticker":"BBB"'))
    with pytest.raises(R03PayloadError, match="non-finite"):
        parse_t3_response(raw.replace('"confidence":80', '"confidence":NaN'))
