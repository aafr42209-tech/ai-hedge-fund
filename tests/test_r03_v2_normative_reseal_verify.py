from __future__ import annotations

import copy
from pathlib import Path

import pytest

from scripts import r03_news_reasoning_v2_normative_reseal_verify as verifier
from v2.research.overlay.canonical import canonical_sha256


def _resign(value: dict[str, object], field: str) -> None:
    unsigned = {key: item for key, item in value.items() if key != field}
    value[field] = canonical_sha256(unsigned)


def _replace(value: dict[str, object], path: tuple[str, ...], replacement: object) -> None:
    current: object = value
    for field in path[:-1]:
        assert isinstance(current, dict)
        current = current[field]
    assert isinstance(current, dict)
    current[path[-1]] = replacement


def _patched_loader(
    monkeypatch: pytest.MonkeyPatch,
    target_path: Path,
    replacement: dict[str, object],
) -> None:
    original = verifier.load_json

    def load(path: Path) -> dict[str, object]:
        if path == target_path:
            return copy.deepcopy(replacement)
        return original(path)

    monkeypatch.setattr(verifier, "load_json", load)


def test_v2_normative_reseal_verifier_accepts_sealed_artifacts() -> None:
    assert verifier.main() == 0


@pytest.mark.parametrize(
    ("path", "replacement", "match"),
    (
        (("normative_retention", "retained_text_bytes"), 1435742878, "normative retention"),
        (("replacement_disposition", "action"), "RECONCILE", "replacement disposition"),
        (("replacement_disposition", "legacy_value_status"), "NORMATIVE", "replacement disposition"),
        (("replacement_disposition", "lost_v1_driver_recovery"), "RECOVERED", "replacement disposition"),
        (("replacement_disposition", "post_hoc_fit_to_655960_forbidden"), False, "replacement disposition"),
        (("canonical_hash_policy", "normative_contract_anchor"), "FILESYSTEM_SHA256", "canonical hash policy"),
        (("semantic_aliases", "targeted_result.total_news_positive_frames"), "full_frames_retained", "semantic alias"),
        (("boundary_counters", "raw_source_traversals"), 1, "counters"),
    ),
)
def test_resigned_lineage_semantic_tamper_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, ...],
    replacement: object,
    match: str,
) -> None:
    lineage = verifier.load_json(verifier.LINEAGE_PATH)
    _replace(lineage, path, replacement)
    _resign(lineage, "lineage_sha256")
    with pytest.raises(verifier.VerificationError, match=match):
        verifier.assert_lineage(lineage)


@pytest.mark.parametrize(
    ("path", "replacement", "match"),
    (
        (("execution_surface", "targeted_runner_filesystem_sha256"), "0" * 64, "execution-surface"),
        (("result_pins", "targeted_result_canonical_sha256"), "0" * 64, "result pin"),
        (("independent_review", "disposition"), "CHANGES_REQUESTED", "independent-review"),
        (("legacy_failure_source", "generator_driver_status"), "RECOVERED", "legacy failure-source"),
        (("prior_and_current_execution_scopes", "targeted_raw_scan_completed"), 2, "execution-scope"),
    ),
)
def test_resigned_attestation_semantic_tamper_fails_closed(
    path: tuple[str, ...],
    replacement: object,
    match: str,
) -> None:
    lineage = verifier.load_json(verifier.LINEAGE_PATH)
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    _replace(attestation, path, replacement)
    _resign(attestation, "attestation_sha256")
    with pytest.raises(verifier.VerificationError, match=match):
        verifier.assert_attestation(attestation, lineage)


def test_execution_commit_must_be_an_ancestor_of_current_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    permit = verifier.load_json(verifier.PERMIT_PATH)
    monkeypatch.setattr(verifier, "execution_commit_is_ancestor", lambda commit: False)
    with pytest.raises(verifier.VerificationError, match="observed execution surface"):
        verifier.assert_execution_surface(attestation, permit)


def _resign_targeted_result(result: dict[str, object]) -> tuple[str, str, str]:
    evidence = result["targeted_evidence"]
    assert isinstance(evidence, dict)
    ledgers = evidence["ledgers"]
    assert isinstance(ledgers, list)
    evidence["ledger_multiset_sha256"] = canonical_sha256(ledgers)
    _resign(evidence, "evidence_sha256")
    _resign(result, "result_sha256")
    return (
        str(result["result_sha256"]),
        str(evidence["evidence_sha256"]),
        str(evidence["ledger_multiset_sha256"]),
    )


def test_resigned_targeted_ledger_partition_tamper_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = verifier.load_json(verifier.TARGETED_RESULT_PATH)
    evidence = result["targeted_evidence"]
    assert isinstance(evidence, dict)
    ledgers = evidence["ledgers"]
    assert isinstance(ledgers, list)
    ledger = ledgers[0]
    assert isinstance(ledger, dict)
    ledger["source_appearances"] = int(ledger["source_appearances"]) + 1
    ledgers.sort(key=lambda item: tuple(item[field] for field in verifier.LEDGER_FIELDS))
    result_hash, evidence_hash, multiset_hash = _resign_targeted_result(result)
    monkeypatch.setattr(verifier, "TARGETED_RESULT_SHA256", result_hash)
    monkeypatch.setattr(verifier, "TARGETED_EVIDENCE_SHA256", evidence_hash)
    monkeypatch.setattr(verifier, "LEDGER_MULTISET_SHA256", multiset_hash)
    _patched_loader(monkeypatch, verifier.TARGETED_RESULT_PATH, result)
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    with pytest.raises(verifier.VerificationError, match="source appearance partition"):
        verifier.assert_targeted_result(attestation)


def test_resigned_targeted_ledger_order_tamper_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = verifier.load_json(verifier.TARGETED_RESULT_PATH)
    evidence = result["targeted_evidence"]
    assert isinstance(evidence, dict)
    ledgers = evidence["ledgers"]
    assert isinstance(ledgers, list)
    evidence["ledgers"] = list(reversed(ledgers))
    result_hash, evidence_hash, multiset_hash = _resign_targeted_result(result)
    monkeypatch.setattr(verifier, "TARGETED_RESULT_SHA256", result_hash)
    monkeypatch.setattr(verifier, "TARGETED_EVIDENCE_SHA256", evidence_hash)
    monkeypatch.setattr(verifier, "LEDGER_MULTISET_SHA256", multiset_hash)
    _patched_loader(monkeypatch, verifier.TARGETED_RESULT_PATH, result)
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    with pytest.raises(verifier.VerificationError, match="multiset ordering"):
        verifier.assert_targeted_result(attestation)


def test_resigned_targeted_total_frame_alias_tamper_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = verifier.load_json(verifier.TARGETED_RESULT_PATH)
    evidence = result["targeted_evidence"]
    assert isinstance(evidence, dict)
    evidence["total_news_positive_frames"] = 150394
    result_hash, evidence_hash, multiset_hash = _resign_targeted_result(result)
    monkeypatch.setattr(verifier, "TARGETED_RESULT_SHA256", result_hash)
    monkeypatch.setattr(verifier, "TARGETED_EVIDENCE_SHA256", evidence_hash)
    monkeypatch.setattr(verifier, "LEDGER_MULTISET_SHA256", multiset_hash)
    _patched_loader(monkeypatch, verifier.TARGETED_RESULT_PATH, result)
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    with pytest.raises(verifier.VerificationError, match="frame-count semantic alias"):
        verifier.assert_targeted_result(attestation)


def test_resigned_evidence_artifact_pin_tamper_fails_closed() -> None:
    lineage = verifier.load_json(verifier.LINEAGE_PATH)
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    evidence = verifier.load_json(verifier.EVIDENCE_PATH)
    pins = evidence["artifact_sha256"]
    assert isinstance(pins, dict)
    pins["scripts/r03_news_reasoning_v2_normative_reseal_verify.py"] = "0" * 64
    _resign(evidence, "evidence_sha256")
    with pytest.raises(verifier.VerificationError, match="artifact pin"):
        verifier.assert_evidence(evidence, lineage, attestation)


def test_manifest_nonzero_current_scope_fails_closed() -> None:
    manifest = verifier.load_json(verifier.MANIFEST_PATH)
    counters = manifest["boundary_counters"]
    assert isinstance(counters, dict)
    counters["raw_source_traversals"] = 1
    with pytest.raises(verifier.VerificationError, match="counters"):
        verifier.assert_manifest(manifest)
