from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from . import r02_d4_design
from .r02_d4_design import (
    R02D4DesignError,
    build_power_report,
    build_test_vector_report,
    candidate_activity_features,
    exact_m_min_probability_ppm,
    expected_m_min,
    select_parsimony_candidate,
)

ROOT = Path(__file__).resolve().parents[3]


def _record(candidate_id: str, *, action: str, quantity: object) -> dict[str, object]:
    return {
        "canonical_candidate_id": candidate_id,
        "candidate": {"decisions": {"A0": {"action": action, "quantity": quantity}}},
    }


def test_parsimony_vectors_cover_precedence_and_permutation() -> None:
    report = build_test_vector_report()
    assert report["all_passed"] is True
    assert len(report["vectors"]) == 8
    assert {value["vector_id"] for value in report["vectors"]} >= {
        "unique-zero-activity-wins",
        "fewer-non-hold-actions-wins",
        "lower-total-absolute-quantity-wins",
        "canonical-id-breaks-feature-tie",
        "permutation-invariant-forward",
        "permutation-invariant-reverse",
    }


def test_activity_features_count_inconsistent_hold_and_quantity_as_active() -> None:
    features = candidate_activity_features(
        {
            "candidate": {
                "decisions": {
                    "A0": {"action": "hold", "quantity": 2},
                    "A1": {"action": "buy", "quantity": 0},
                    "A2": {"action": "hold", "quantity": 0},
                }
            }
        }
    )
    assert features.non_hold_action_count == 2
    assert features.total_absolute_quantity == 2
    assert features.zero_activity is False


@pytest.mark.parametrize(
    ("records", "code"),
    [
        ([], "PARSIMONY_CANDIDATE_SET_EMPTY"),
        ([_record("not-a-hash", action="hold", quantity=0)], "PARSIMONY_CANONICAL_ID_INVALID"),
        (
            [
                _record("a" * 64, action="hold", quantity=0),
                _record("a" * 64, action="buy", quantity=1),
            ],
            "PARSIMONY_CANONICAL_ID_DUPLICATE",
        ),
        ([_record("a" * 64, action="hold", quantity=True)], "PARSIMONY_ACTION_OR_QUANTITY_INVALID"),
    ],
)
def test_parsimony_comparator_fails_closed(
    records: list[dict[str, object]], code: str
) -> None:
    with pytest.raises(R02D4DesignError, match=code):
        select_parsimony_candidate(records)


def test_m_min_scales_without_using_d3_fixture_outcomes() -> None:
    assert [expected_m_min(n) for n in (160, 200, 240)] == [46, 57, 69]
    assert exact_m_min_probability_ppm(160) == 900_568
    assert exact_m_min_probability_ppm(200) == 943_424
    assert exact_m_min_probability_ppm(240) == 935_090


def test_small_power_report_is_deterministic_and_provider_free() -> None:
    first = build_power_report(outer_trials=8, bootstrap_resamples=40)
    second = build_power_report(outer_trials=8, bootstrap_resamples=40)
    assert first == second
    assert first["provider_calls"] == 0
    assert first["frame_generation"] is False
    assert first["live_execution"] is False
    assert len(first["scenario_results"]) == 12
    assert first["draft_selected_n"] == 200


def test_design_source_has_no_provider_network_process_or_frame_imports() -> None:
    source_path = Path(r02_d4_design.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    relative_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
            if node.level:
                relative_modules.add(node.module)
    assert imported.isdisjoint(r02_d4_design.forbidden_capability_names())
    assert "r02_frame" not in relative_modules
    assert "r02_d3_live_orchestrator" not in relative_modules
    assert "r02_d3_live_selector_adapter" not in relative_modules


def test_read_only_verifier_has_no_provider_network_or_process_imports() -> None:
    source_path = ROOT / "scripts" / "r02_d4_design_verify.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(r02_d4_design.forbidden_capability_names())


def test_machine_drafts_keep_seed_frame_provider_and_live_unresolved() -> None:
    paths = (
        ROOT / "docs" / "r02-d4-replication-design.json",
        ROOT / "docs" / "r02-d4-seed-contract.json",
        ROOT / "docs" / "r02-d4-prospective-power-sizing.json",
        ROOT / "docs" / "r02-d4-parsimony-test-vectors.json",
    )
    values = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    assert all(value["provider_calls"] == 0 for value in values)
    assert all(value["frame_generation"] is False for value in values)
    assert all(value["live_execution"] is False for value in values)
    seed = values[1]
    assert seed["frame_seed_created"] is False
    assert seed["resolved_frame_seed_sha256"] is None
    assert seed["resolved_frame_id"] is None


def test_expectation_management_constants_keep_incremental_separate() -> None:
    assert r02_d4_design.R02_D4_MIN_DISCORDANT_TOTAL == 20
    assert r02_d4_design.R02_D4_MIN_DISCORDANT_PER_STRATUM == 5
    assert r02_d4_design.R02_D4_FRAME_SEED_STATUS == "UNRESOLVED_DRAFT_NO_SEED_CREATED"
    assert r02_d4_design.R02_D4_PROVIDER_CALLS == 0
    assert r02_d4_design.R02_D4_FRAME_GENERATION is False
    assert r02_d4_design.R02_D4_LIVE_EXECUTION is False
