from __future__ import annotations

import ast
from pathlib import Path

from .r02_d3_posthoc_analysis import _candidate_features


def test_candidate_features_identify_unique_zero_activity_candidate() -> None:
    value = {
        "candidate": {
            "decisions": {
                "A0": {"action": "hold", "quantity": 0},
                "A1": {"action": "hold", "quantity": 0},
            }
        }
    }
    assert _candidate_features(value) == {
        "non_hold_action_count": 0,
        "total_absolute_quantity": 0,
        "zero_activity": True,
    }


def test_candidate_features_count_non_hold_actions_and_absolute_quantity() -> None:
    value = {
        "candidate": {
            "decisions": {
                "A0": {"action": "buy", "quantity": 3},
                "A1": {"action": "sell", "quantity": -2},
                "A2": {"action": "hold", "quantity": 0},
            }
        }
    }
    assert _candidate_features(value) == {
        "non_hold_action_count": 2,
        "total_absolute_quantity": 5,
        "zero_activity": False,
    }


def test_posthoc_source_has_no_provider_or_process_capability_imports() -> None:
    source = Path(__file__).with_name("r02_d3_posthoc_analysis.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"http", "httpx", "requests", "socket", "subprocess", "urllib"}
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    assert not imports.intersection(forbidden)
