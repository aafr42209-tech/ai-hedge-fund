from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from .r02_v2_audit import (
    append_audit_entry,
    build_implementation_evidence,
    empty_audit_log,
    replay_audit_log,
    TEST_GATES,
)

SOURCE_NAMES = (
    "r02_v2_contracts.py",
    "r02_v2_payload.py",
    "r02_v2_grounding.py",
    "r02_v2_comparator.py",
    "r02_v2_selection.py",
    "r02_v2_headroom.py",
    "r02_v2_power.py",
    "r02_v2_audit.py",
)


def test_append_only_audit_replays_without_provider_capability() -> None:
    log = empty_audit_log()
    log = append_audit_entry(log, kind="CONTRACT", payload={"ok": True})
    log = append_audit_entry(log, kind="TEST", payload={"passed": 1})
    assert replay_audit_log(log)
    assert log.provider_calls == log.live_runs == log.fixture_roots_materialized == 0


def test_evidence_requires_complete_thirteen_gate_traceability() -> None:
    test_path = "v2/research/overlay/test_r02_v2_audit.py"
    evidence = build_implementation_evidence(
        source_sha256={"source.py": "a" * 64},
        test_sha256={test_path: "b" * 64},
        gate_to_tests={gate: (test_path,) for gate in TEST_GATES},
        focused_test_command="pytest r02_v2",
        full_overlay_test_command="pytest overlay",
    )
    assert len(evidence.gate_to_tests) == 13
    with pytest.raises(ValidationError, match="13 accepted test gates"):
        build_implementation_evidence(
            source_sha256={"source.py": "a" * 64},
            test_sha256={test_path: "b" * 64},
            gate_to_tests={TEST_GATES[0]: (test_path,)},
            focused_test_command="pytest r02_v2",
            full_overlay_test_command="pytest overlay",
        )


def test_implementation_modules_have_no_provider_or_process_imports() -> None:
    root = Path(__file__).resolve().parent
    forbidden = {
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
    }
    imported: set[str] = set()
    for name in SOURCE_NAMES:
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden)
