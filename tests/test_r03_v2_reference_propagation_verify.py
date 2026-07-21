from __future__ import annotations

import pytest

from scripts import r03_news_reasoning_v2_reference_propagation_verify as verifier
from v2.research.overlay.canonical import canonical_sha256


def _resign(value: dict[str, object], field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    value[field] = canonical_sha256(unsigned)
    return str(value[field])


def _replace(value: dict[str, object], path: tuple[str, ...], replacement: object) -> None:
    current: object = value
    for field in path[:-1]:
        assert isinstance(current, dict)
        current = current[field]
    assert isinstance(current, dict)
    current[path[-1]] = replacement


def test_reference_propagation_verifier_accepts_additive_overlay() -> None:
    assert verifier.main() == 0


@pytest.mark.parametrize(
    ("text", "match"),
    (
        ("no legacy clause", "exactly once"),
        (
            verifier.CHARTER_OLD_CLAUSE + "\n" + verifier.CHARTER_OLD_CLAUSE,
            "exactly once",
        ),
        (
            verifier.CHARTER_OLD_CLAUSE + "\n1,515,387,041/1,585,976,846 text bytes (95.55%)",
            "directly edited",
        ),
    ),
)
def test_base_document_direct_edit_or_duplicate_overlay_fails_closed(
    text: str,
    match: str,
) -> None:
    with pytest.raises(verifier.VerificationError, match=match):
        verifier.assert_base_document_text(
            label="charter",
            text=text,
            old_clause=verifier.CHARTER_OLD_CLAUSE,
            old_clause_sha256=verifier.CHARTER_OLD_CLAUSE_SHA256,
        )


@pytest.mark.parametrize(
    ("path", "replacement", "match"),
    (
        (("status",), "APPROVED_WITHOUT_REVIEW", "authority/status"),
        (("base_documents", "charter", "preserved_byte_for_byte"), False, "base-document"),
        (("normative_source", "v2_reseal_evidence_canonical_sha256"), "0" * 64, "normative-source"),
        (("effective_retention", "retained_text_bytes"), 1435742878, "effective retention"),
        (("precedence", "composition"), "IN_PLACE_EDIT", "precedence"),
        (("precedence", "action"), "RECONCILE", "precedence"),
        (("precedence", "all_other_base_clauses_unchanged"), False, "precedence"),
        (("non_authority", "raw_source_access"), True, "non-authority"),
        (("non_authority", "g1_g2_g3_execution"), True, "non-authority"),
    ),
)
def test_resigned_effective_contract_semantic_tamper_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, ...],
    replacement: object,
    match: str,
) -> None:
    contract = verifier.load_json(verifier.CONTRACT_PATH)
    _replace(contract, path, replacement)
    forged_hash = _resign(contract, "effective_contract_sha256")
    monkeypatch.setattr(verifier, "CONTRACT_SHA256", forged_hash)
    with pytest.raises(verifier.VerificationError, match=match):
        verifier.assert_effective_contract(contract)


def test_repointed_amendment_pin_fails_closed() -> None:
    contract = verifier.load_json(verifier.CONTRACT_PATH)
    amendments = contract["amendments"]
    assert isinstance(amendments, dict)
    charter = amendments["charter"]
    assert isinstance(charter, dict)
    charter["filesystem_sha256"] = "0" * 64
    with pytest.raises(verifier.VerificationError, match="amendment pin"):
        verifier.assert_amendments(contract)


@pytest.mark.parametrize(
    ("path", "replacement", "match"),
    (
        (("base_preservation", "base_documents_modified"), True, "base preservation"),
        (("effective_contract", "canonical_sha256"), "0" * 64, "contract pin"),
        (("normative_source_pins", "v2_reseal_evidence_canonical_sha256"), "0" * 64, "normative-source"),
        (("propagation_resolution", "effective_text_byte_retention_pct_2dp"), "90.53", "resolution"),
        (("propagation_resolution", "replacement_mode"), "RECONCILE", "resolution"),
        (("propagation_resolution", "prior_unresolved_dispositions"), "ACTIVE", "resolution"),
        (("boundary_counters", "raw_source_traversals"), 1, "counters"),
    ),
)
def test_resigned_lineage_semantic_tamper_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, ...],
    replacement: object,
    match: str,
) -> None:
    contract = verifier.load_json(verifier.CONTRACT_PATH)
    lineage = verifier.load_json(verifier.LINEAGE_PATH)
    _replace(lineage, path, replacement)
    forged_hash = _resign(lineage, "lineage_sha256")
    monkeypatch.setattr(verifier, "LINEAGE_SHA256", forged_hash)
    with pytest.raises(verifier.VerificationError, match=match):
        verifier.assert_lineage(lineage, contract)


def test_resigned_evidence_artifact_pin_fails_closed() -> None:
    contract = verifier.load_json(verifier.CONTRACT_PATH)
    lineage = verifier.load_json(verifier.LINEAGE_PATH)
    evidence = verifier.load_json(verifier.EVIDENCE_PATH)
    pins = evidence["artifact_sha256"]
    assert isinstance(pins, dict)
    pins["docs/r03-news-reasoning-charter-draft.md"] = "0" * 64
    _resign(evidence, "evidence_sha256")
    with pytest.raises(verifier.VerificationError, match="artifact pin"):
        verifier.assert_evidence(evidence, lineage, contract)


def test_manifest_nonzero_current_scope_fails_closed() -> None:
    manifest = verifier.load_json(verifier.MANIFEST_PATH)
    counters = manifest["boundary_counters"]
    assert isinstance(counters, dict)
    counters["gate_executions"] = 1
    with pytest.raises(verifier.VerificationError, match="counters"):
        verifier.assert_manifest(manifest)


def test_old_clause_constant_mutation_fails_closed() -> None:
    with pytest.raises(verifier.VerificationError, match="constant hash"):
        verifier.assert_base_document_text(
            label="charter",
            text=verifier.CHARTER_OLD_CLAUSE,
            old_clause=verifier.CHARTER_OLD_CLAUSE + " ",
            old_clause_sha256=verifier.CHARTER_OLD_CLAUSE_SHA256,
        )
