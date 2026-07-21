from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import r03_news_reasoning_reconciliation_rerun_verify as verifier
from v2.research.overlay.canonical import canonical_sha256


def _resign(value: dict[str, object]) -> None:
    unsigned = {key: item for key, item in value.items() if key != "attestation_sha256"}
    value["attestation_sha256"] = canonical_sha256(unsigned)


def _replace(value: dict[str, object], path: tuple[str, ...], replacement: object) -> None:
    current: object = value
    for field in path[:-1]:
        assert isinstance(current, dict)
        current = current[field]
    assert isinstance(current, dict)
    current[path[-1]] = replacement


def test_rerun_verifier_accepts_sealed_aggregate_result() -> None:
    assert verifier.main() == 0


@pytest.mark.parametrize(
    ("path", "replacement", "match"),
    (
        (("reconciliation_retention", "retained_text_bytes"), 0, "reconciliation retention"),
        (
            ("numerator_decomposition", "sealed_implied_minus_triggering_article_only_bytes"),
            0,
            "numerator decomposition",
        ),
        (("resolved_findings", "input_text_bytes"), "FALSE_CLAIM", "resolved findings"),
        (("artifacts", "result_canonical_sha256"), "0" * 64, "result canonical hash"),
        (("inventory", "total_bytes"), 0, "inventory"),
        (("source_counts", "selected_articles"), 0, "source counts"),
        (("paired_frame_diff", "retained_text_bytes_delta"), 0, "paired summary"),
        (
            ("unresolved_finding", "classification"),
            "FALSE_CLASSIFICATION",
            "unresolved finding",
        ),
        (("unresolved_finding", "additional_raw_scan_authorized"), True, "unresolved finding"),
        (("pins", "calendar_sha256"), "0" * 64, "attestation pins"),
        (("disposition",), "FALSE_DISPOSITION", "attestation disposition"),
    ),
)
def test_resigned_semantic_attestation_tamper_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, ...],
    replacement: object,
    match: str,
) -> None:
    value = json.loads(verifier.ATTESTATION_PATH.read_text(encoding="utf-8"))
    _replace(value, path, replacement)
    _resign(value)
    tampered = tmp_path / "tampered-attestation.json"
    tampered.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(verifier, "ATTESTATION_PATH", tampered)

    with pytest.raises(ValueError, match=match):
        verifier.main()
