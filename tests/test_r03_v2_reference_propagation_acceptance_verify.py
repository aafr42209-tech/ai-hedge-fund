from __future__ import annotations

import copy
import subprocess
from pathlib import Path

import pytest

from scripts import (
    r03_news_reasoning_v2_reference_propagation_acceptance_verify as verifier,
)
from v2.research.overlay.canonical import canonical_sha256


def _replace(
    value: dict[str, object],
    path: tuple[str, ...],
    replacement: object,
) -> None:
    current: object = value
    for field in path[:-1]:
        assert isinstance(current, dict)
        current = current[field]
    assert isinstance(current, dict)
    current[path[-1]] = replacement


def _resign(value: dict[str, object]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "acceptance_attestation_sha256"}
    value["acceptance_attestation_sha256"] = canonical_sha256(unsigned)
    return str(value["acceptance_attestation_sha256"])


def test_acceptance_verifier_accepts_append_only_composition() -> None:
    assert verifier.main() == 0


@pytest.mark.parametrize(
    ("path", "replacement", "match"),
    (
        (("authority",), "WRONG", "authority"),
        (("mode",), "IN_PLACE_RESEAL", "mode"),
        (("accepted_disposition",), "RAW_RERUN_APPROVED", "disposition"),
        (("reviewed_head",), "0" * 40, "HEAD pin"),
        (("accepted_contract", "status_as_authored"), "ACCEPTED", "contract pin"),
        (("accepted_contract", "canonical_sha256"), "0" * 64, "contract pin"),
        (("effective_retention", "retained_text_bytes"), 1435742878, "retention"),
        (("precedence", "action"), "RECONCILE", "precedence"),
        (("preservation", "reviewed_contract_modified"), True, "preservation"),
        (("boundary_counters", "raw_source_traversals"), 1, "counters"),
        (("non_authority", "raw_source_access"), True, "non-authority"),
        (
            ("independent_review", "filesystem_sha256"),
            "0" * 64,
            "independent-review pin",
        ),
        (("composition_index", "filesystem_sha256"), "0" * 64, "index pin"),
        (
            (
                "reviewed_artifact_sha256",
                "docs/r03-news-reasoning-n1-v2-effective-retention-contract.json",
            ),
            "0" * 64,
            "artifact pin",
        ),
        (
            (
                "base_document_sha256",
                "docs/r03-news-reasoning-charter-draft.md",
            ),
            "0" * 64,
            "base-document pin",
        ),
    ),
)
def test_self_consistently_resigned_semantic_tamper_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, ...],
    replacement: object,
    match: str,
) -> None:
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    _replace(attestation, path, replacement)
    forged_hash = _resign(attestation)
    monkeypatch.setattr(verifier, "ATTESTATION_SHA256", forged_hash)
    with pytest.raises(verifier.VerificationError, match=match):
        verifier.assert_attestation(attestation)


def test_unresigned_attestation_tamper_fails_self_hash() -> None:
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    attestation["accepted_disposition"] = "FORGED"
    with pytest.raises(verifier.VerificationError, match="self-hash"):
        verifier.assert_attestation(attestation)


@pytest.mark.parametrize(
    ("commit", "returncode", "expected"),
    (
        (verifier.REVIEWED_HEAD, 0, True),
        (verifier.REVIEWED_HEAD, 1, False),
        ("g" * 40, 0, False),
        ("0" * 39, 0, False),
    ),
)
def test_reviewed_head_ancestry_predicate_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    commit: str,
    returncode: int,
    expected: bool,
) -> None:
    called = False

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal called
        called = True
        return subprocess.CompletedProcess(args=[], returncode=returncode)

    monkeypatch.setattr(verifier.subprocess, "run", fake_run)
    assert verifier.reviewed_head_is_ancestor(commit) is expected
    valid = len(commit) == 40 and all(char in "0123456789abcdef" for char in commit)
    assert called is valid


def test_reviewed_head_ancestry_process_failure_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise OSError("git unavailable")

    monkeypatch.setattr(verifier.subprocess, "run", fail_run)
    assert verifier.reviewed_head_is_ancestor(verifier.REVIEWED_HEAD) is False


def test_composition_index_missing_effective_reference_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    forged_text = verifier.INDEX_PATH.read_text(encoding="utf-8").replace(
        "REPLACE_NOT_RECONCILE",
        "RECONCILE",
    )
    target = tmp_path / "index.md"
    target.write_text(forged_text, encoding="utf-8")
    forged_sha = verifier.sha256_file(target)
    attestation = {
        "composition_index": {
            "path": "docs/r03-news-reasoning-document-composition-index.md",
            "filesystem_sha256": forged_sha,
        }
    }
    monkeypatch.setattr(verifier, "INDEX_PATH", target)
    monkeypatch.setattr(verifier, "INDEX_SHA256", forged_sha)
    with pytest.raises(verifier.VerificationError, match="required reference"):
        verifier.assert_composition_index(attestation)


def test_review_disposition_marker_removal_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    forged_text = verifier.INDEPENDENT_REVIEW_PATH.read_text(encoding="utf-8").replace(
        f"Disposition: `{verifier.DISPOSITION}`",
        "Disposition: `REMOVED`",
    )
    target = tmp_path / "review.md"
    target.write_text(forged_text, encoding="utf-8")
    forged_sha = verifier.sha256_file(target)
    attestation = {
        "independent_review": {
            "path": "docs/r03-news-reasoning-n1-v2-reference-propagation-independent-review.md",
            "filesystem_sha256": forged_sha,
            "disposition": verifier.DISPOSITION,
        }
    }
    monkeypatch.setattr(verifier, "INDEPENDENT_REVIEW_PATH", target)
    monkeypatch.setattr(verifier, "INDEPENDENT_REVIEW_SHA256", forged_sha)
    with pytest.raises(verifier.VerificationError, match="marker"):
        verifier.assert_independent_review(attestation)


def test_main_rejects_failed_propagation_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(verifier.propagation_verifier, "main", lambda: 1)
    with pytest.raises(verifier.VerificationError, match="propagation verifier"):
        verifier.main()


def test_reviewed_artifact_filesystem_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    original_sha256_file = verifier.sha256_file

    def forged_sha256_file(path: Path) -> str:
        if str(path).endswith("r03-news-reasoning-charter-draft.md"):
            return "0" * 64
        return original_sha256_file(path)

    monkeypatch.setattr(verifier, "sha256_file", forged_sha256_file)
    with pytest.raises(verifier.VerificationError, match="filesystem drift"):
        verifier.assert_reviewed_artifacts(attestation)


def test_attestation_copy_is_not_mutated_by_verification() -> None:
    attestation = verifier.load_json(verifier.ATTESTATION_PATH)
    before = copy.deepcopy(attestation)
    verifier.assert_attestation(attestation)
    assert attestation == before
