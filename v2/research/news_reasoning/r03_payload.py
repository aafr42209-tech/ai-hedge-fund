"""Deterministic synthetic-safe R03 news payload construction."""

from __future__ import annotations

import json
import unicodedata
from datetime import datetime, timedelta
from typing import Any

from v2.research.overlay.canonical import sha256_hex

from .r03_contracts import (
    ARTICLE_BYTE_CAP,
    R03ArticleRecord,
    R03CanonicalArticle,
    R03CanonicalBundle,
    R03ContractError,
    R03T3Response,
    TICKER_SESSION_BYTE_CAP,
)


class R03PayloadError(R03ContractError):
    pass


def canonicalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    if "\x00" in value:
        raise R03PayloadError("NUL is forbidden in canonical text")
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def _iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise R03PayloadError("canonical timestamp must be timezone-aware")
    return value.isoformat().replace("+00:00", "Z")


def _article_dict(article: R03CanonicalArticle) -> dict[str, Any]:
    return {
        "article_id": article.article_id,
        "available_at": _iso(article.available_at),
        "symbols": list(article.symbols),
        "source": article.source,
        "headline": article.headline,
        "summary": article.summary,
        "content": article.content,
        "summary_present": article.summary_present,
        "content_present": article.content_present,
        "content_truncated": article.content_truncated,
    }


def _payload_dict(
    ticker: str,
    decision_at: datetime,
    articles: tuple[R03CanonicalArticle, ...] | list[R03CanonicalArticle],
) -> dict[str, Any]:
    return {
        "schema_version": "r03-canonical-news-bundle-v1",
        "ticker": ticker,
        "decision_at": _iso(decision_at),
        "article_byte_cap": ARTICLE_BYTE_CAP,
        "ticker_session_byte_cap": TICKER_SESSION_BYTE_CAP,
        "articles": [_article_dict(article) for article in articles],
    }


def _ordered_json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def canonical_bundle_bytes(bundle: R03CanonicalBundle) -> bytes:
    payload = _ordered_json_bytes(_payload_dict(bundle.ticker, bundle.decision_at, bundle.articles))
    text_bytes = sum(_article_text_bytes(article) for article in bundle.articles)
    if text_bytes != bundle.text_bytes or len(payload) != bundle.payload_bytes or sha256_hex(payload) != bundle.payload_sha256:
        raise R03PayloadError("bundle byte identity mismatch")
    return payload


def _utf8_prefix(value: str, maximum_bytes: int) -> str:
    if maximum_bytes <= 0:
        return ""
    raw = value.encode("utf-8")
    if len(raw) <= maximum_bytes:
        return value
    return raw[:maximum_bytes].decode("utf-8", errors="ignore")


def _text_bytes(headline: str, summary: str | None, content: str | None) -> int:
    return sum(len(value.encode("utf-8")) for value in (headline, summary, content) if value is not None)


def _article_text_bytes(article: R03CanonicalArticle) -> int:
    return _text_bytes(article.headline, article.summary, article.content)


def _fit_article(record: R03ArticleRecord, maximum_bytes: int) -> R03CanonicalArticle:
    headline = canonicalize_text(record.headline)
    summary = canonicalize_text(record.summary)
    content = canonicalize_text(record.content)
    source = canonicalize_text(record.source)
    if headline is None or headline == "":
        raise R03PayloadError("headline is required")
    full = R03CanonicalArticle(
        article_id=record.article_id,
        available_at=record.available_at,
        symbols=record.symbols,
        source=source,
        headline=headline,
        summary=summary,
        content=content,
        summary_present=summary is not None,
        content_present=content is not None,
        content_truncated=False,
    )
    if _article_text_bytes(full) <= maximum_bytes:
        return full
    preserved_bytes = _text_bytes(headline, summary, None)
    if content is None or preserved_bytes > maximum_bytes:
        raise R03PayloadError("article headline/summary exceed text byte cap")
    fitted = full.model_copy(update={"content": _utf8_prefix(content, maximum_bytes - preserved_bytes), "content_truncated": True})
    if _article_text_bytes(fitted) > maximum_bytes:
        raise R03PayloadError("article cannot fit text byte cap")
    return fitted


def select_latest_versions(records: tuple[R03ArticleRecord, ...]) -> tuple[R03ArticleRecord, ...]:
    selected: dict[str, R03ArticleRecord] = {}
    for record in records:
        current = selected.get(record.article_id)
        key = (record.available_at, record.updated_at, record.input_text_sha256)
        if current is None or key > (current.available_at, current.updated_at, current.input_text_sha256):
            selected[record.article_id] = record
    return tuple(selected.values())


def eligible_records(
    records: tuple[R03ArticleRecord, ...],
    *,
    ticker: str,
    decision_at: datetime,
    frozen_universe: frozenset[str],
) -> tuple[R03ArticleRecord, ...]:
    if decision_at.tzinfo is None or decision_at.utcoffset() is None:
        raise R03PayloadError("decision_at must be timezone-aware")
    lower = decision_at - timedelta(hours=72)
    result = []
    for record in select_latest_versions(records):
        if not (lower < record.available_at <= decision_at):
            continue
        if record.headline is None or canonicalize_text(record.headline) == "":
            continue
        if not 1 <= len(record.symbols) <= 5:
            continue
        if not set(record.symbols) & frozen_universe:
            continue
        if ticker not in record.symbols:
            continue
        result.append(record)
    return tuple(sorted(result, key=lambda r: (-r.available_at.timestamp(), r.article_id)))


def _fit_for_session(
    prior: list[R03CanonicalArticle],
    record: R03ArticleRecord,
) -> tuple[R03CanonicalArticle | None, bool]:
    article = _fit_article(record, ARTICLE_BYTE_CAP)
    remaining = TICKER_SESSION_BYTE_CAP - sum(_article_text_bytes(item) for item in prior)
    if _article_text_bytes(article) <= remaining:
        return article, False
    preserved_bytes = _text_bytes(article.headline, article.summary, None)
    if article.content is None or preserved_bytes > remaining:
        return None, True
    fitted = article.model_copy(update={"content": _utf8_prefix(article.content, remaining - preserved_bytes), "content_truncated": True})
    return fitted, True


def build_canonical_bundle(
    records: tuple[R03ArticleRecord, ...],
    *,
    ticker: str,
    decision_at: datetime,
    frozen_universe: frozenset[str],
) -> R03CanonicalBundle:
    articles: list[R03CanonicalArticle] = []
    for record in eligible_records(records, ticker=ticker, decision_at=decision_at, frozen_universe=frozen_universe):
        fitted, session_truncated = _fit_for_session(articles, record)
        if fitted is not None:
            articles.append(fitted)
        if session_truncated:
            break
    payload = _ordered_json_bytes(_payload_dict(ticker, decision_at, articles))
    text_bytes = sum(_article_text_bytes(article) for article in articles)
    if text_bytes > TICKER_SESSION_BYTE_CAP:
        raise R03PayloadError("ticker-session text exceeds byte cap")
    return R03CanonicalBundle(
        ticker=ticker,
        decision_at=decision_at,
        articles=tuple(articles),
        text_bytes=text_bytes,
        payload_bytes=len(payload),
        payload_sha256=sha256_hex(payload),
    )


def assert_information_equal(t2_payload_sha256: str, t3_payload_sha256: str) -> None:
    if t2_payload_sha256 != t3_payload_sha256:
        raise R03PayloadError("T2 and T3 payload bytes differ")


def resolve_news_pointer(bundle: R03CanonicalBundle, pointer: str) -> Any:
    if not pointer.startswith("/") or pointer == "/":
        raise R03PayloadError("pointer must be a non-root RFC6901 path")
    current: Any = _payload_dict(bundle.ticker, bundle.decision_at, bundle.articles)
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise R03PayloadError("pointer key not found")
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise R03PayloadError("non-canonical array index")
            index = int(token)
            if index >= len(current):
                raise R03PayloadError("array index out of range")
            current = current[index]
        else:
            raise R03PayloadError("pointer descends through scalar")
    return current


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise R03PayloadError(f"duplicate response key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise R03PayloadError(f"non-finite response constant: {value}")


def parse_t3_response(raw: str | bytes) -> R03T3Response:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        value = json.loads(raw, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_nonfinite_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise R03PayloadError("invalid T3 response JSON") from exc
    if not isinstance(value, dict):
        raise R03PayloadError("T3 response must be a JSON object")
    try:
        if isinstance(value.get("reasons"), list):
            value["reasons"] = tuple(
                {
                    **reason,
                    "field_refs": tuple(reason.get("field_refs", ())),
                }
                for reason in value["reasons"]
            )
        return R03T3Response.model_validate(value)
    except Exception as exc:
        raise R03PayloadError("T3 response contract violation") from exc


def validate_t3_grounding(response: R03T3Response, bundle: R03CanonicalBundle) -> None:
    if response.ticker != bundle.ticker:
        raise R03PayloadError("T3 response ticker does not match payload")
    for reason in response.reasons:
        for pointer in reason.field_refs:
            if not pointer.startswith("/articles/"):
                raise R03PayloadError("T3 grounding must reference an article field")
            resolve_news_pointer(bundle, pointer)
