from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.r03_news_reasoning_data_check_verify import (
    EXPECTED_FRACTIONS,
    run_authorized_data_check,
)
from v2.research.news_reasoning.r03_source import (
    R03DataCheckPermitV2,
    R03SourceAccessDenied,
    root_path_sha256,
)
from v2.research.overlay.canonical import canonical_sha256


def permit_values(root: Path) -> dict[str, object]:
    return {
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


def make_permit(values: dict[str, object]) -> R03DataCheckPermitV2:
    permit_sha256 = canonical_sha256(values)
    return R03DataCheckPermitV2(**values, permit_sha256=permit_sha256)


def test_authorized_mode_validates_complete_permit_before_callback() -> None:
    root = Path("synthetic-never-opened")
    permit = make_permit(permit_values(root))
    called = False

    def synthetic_rows(received_root: Path):
        nonlocal called
        called = True
        assert received_root == root
        return (True, False), ((True, 32, 32), (False, 16, 0), (True, 8, 4))

    output = run_authorized_data_check(root, permit, permit.permit_sha256, synthetic_rows)
    assert called is True
    assert output["status"] == "COMPLETED_AGGREGATES_ONLY"
    assert output["retention"]["full_frames_total"] == 2
    assert output["retention"]["article_appearances_total"] == 3
    assert set(output) == {"schema_version", "status", "pins", "retention"}
    assert "article_ordering" not in output["pins"]
    assert "truncation_semantics" not in output["pins"]
    assert "rounding_rule" not in output["pins"]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("authorization", "READ_ONLY_DATA_CHECK_AUTHORIZED"),
        ("plan_commit", "0" * 40),
        ("implementation_commit", "0" * 40),
        ("early_close_session_count", 20),
        ("calendar_session_count", 2513),
        ("article_byte_cap", 32767),
        ("ticker_session_byte_cap", 131071),
        ("article_ordering", "oldest_first"),
        ("truncation_semantics", "include_after_truncation"),
        ("rounding_rule", "ROUND_DOWN_2DP"),
    ),
)
def test_permit_contract_rejects_normative_pin_perturbation(field: str, value: object) -> None:
    values = permit_values(Path("synthetic-never-opened"))
    values[field] = value
    with pytest.raises(ValidationError):
        make_permit(values)


@pytest.mark.parametrize("field", ("early_close_sessions_sha256", "calendar_sha256"))
def test_hash_pin_perturbation_fails_before_callback(field: str) -> None:
    root = Path("synthetic-never-opened")
    original = make_permit(permit_values(root))
    values = permit_values(root)
    values[field] = "c" * 64
    perturbed = make_permit(values)
    called = False

    def forbidden(_: Path):
        nonlocal called
        called = True
        return (), ()

    with pytest.raises(R03SourceAccessDenied, match="explicitly pinned permit"):
        run_authorized_data_check(root, perturbed, original.permit_sha256, forbidden)
    assert called is False


def test_root_pin_perturbation_fails_before_callback() -> None:
    root = Path("synthetic-never-opened")
    values = permit_values(root)
    values["root_path_sha256"] = root_path_sha256(Path("different-never-opened"))
    permit = make_permit(values)
    called = False

    def forbidden(_: Path):
        nonlocal called
        called = True
        return (), ()

    with pytest.raises(R03SourceAccessDenied, match="root identity"):
        run_authorized_data_check(root, permit, permit.permit_sha256, forbidden)
    assert called is False


def test_permit_self_hash_perturbation_fails_before_callback() -> None:
    root = Path("synthetic-never-opened")
    permit = make_permit(permit_values(root)).model_copy(update={"permit_sha256": "c" * 64})
    called = False

    def forbidden(_: Path):
        nonlocal called
        called = True
        return (), ()

    with pytest.raises(R03SourceAccessDenied, match="permit hash mismatch"):
        run_authorized_data_check(root, permit, permit.permit_sha256, forbidden)
    assert called is False


def test_model_copy_cannot_bypass_normative_permit_validation() -> None:
    root = Path("synthetic-never-opened")
    base = make_permit(permit_values(root))
    perturbations = {
        "authorization": "READ_ONLY_DATA_CHECK_AUTHORIZED",
        "plan_commit": "0" * 40,
        "implementation_commit": "0" * 40,
        "early_close_session_count": 20,
        "calendar_session_count": 2513,
        "article_byte_cap": 32767,
        "ticker_session_byte_cap": 131071,
        "article_ordering": "oldest_first",
        "truncation_semantics": "include_after_truncation",
        "rounding_rule": "ROUND_DOWN_2DP",
    }
    for field, value in perturbations.items():
        unsigned = base.model_dump(mode="json", exclude={"permit_sha256"})
        unsigned[field] = value
        forged = base.model_copy(update={field: value, "permit_sha256": canonical_sha256(unsigned)})
        called = False

        def forbidden(_: Path):
            nonlocal called
            called = True
            return (), ()

        with pytest.raises(R03SourceAccessDenied, match="contract validation"):
            run_authorized_data_check(root, forged, forged.permit_sha256, forbidden)
        assert called is False, field


def test_sealed_expected_fractions_are_exact_integer_identities() -> None:
    assert EXPECTED_FRACTIONS == {
        "full_frames": (150_394, 151_820, "99.06"),
        "article_appearances": (695_948, 702_489, "99.07"),
        "text_bytes": (1_435_742_878, 1_585_976_846, "90.53"),
    }
