from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from v2.research.news_reasoning.r03_audit import (
    append_audit_entry,
    build_implementation_evidence,
    empty_audit_log,
    R03AuditEntry,
    replay_audit_log,
)
from v2.research.news_reasoning.r03_contracts import R03PinKind, R03ZeroCounters
from v2.research.news_reasoning.r03_source import R03RawTextEmissionError

SHA = "a" * 64
NEGATIVE_TESTS = (
    "recompute_payload_retention_from_read_only_raw_source",
    "reject_article_byte_cap_perturbation",
    "reject_ticker_session_byte_cap_perturbation",
    "reject_article_ordering_perturbation",
    "reject_early_close_cutoff_perturbation",
    "reject_duplicate_selection_perturbation",
    "reject_raw_text_emission",
    "reject_nonzero_provider_counter",
)


def test_audit_chain_is_append_only_and_replays() -> None:
    log = empty_audit_log()
    log = append_audit_entry(log, "AUTHORITY", {"status": "CODE_ONLY"})
    log = append_audit_entry(log, "PAYLOAD_DIGEST", {"payload_sha256": SHA, "article_count": 2})
    assert replay_audit_log(log)
    values = log.entries[0].model_dump(mode="python")
    values["public_payload"] = {"status": "TAMPERED"}
    with pytest.raises(Exception, match="hash mismatch"):
        R03AuditEntry.model_validate(values)


def test_audit_rejects_raw_text_fields() -> None:
    with pytest.raises(R03RawTextEmissionError):
        append_audit_entry(empty_audit_log(), "EVIDENCE", {"headline": "synthetic"})


def test_reject_nonzero_provider_counter() -> None:
    for field in R03ZeroCounters.model_fields:
        with pytest.raises(ValidationError):
            R03ZeroCounters(**{field: 1})


def test_evidence_requires_pin_kind_coverage_and_zero_counters() -> None:
    evidence = build_implementation_evidence(
        schema_version="r03-provider-free-code-only-evidence-v1",
        implementation_plan_commit="6da16688b3da581d1a919d7c75e285827ed10e85",
        status="CODE_ONLY_IMPLEMENTED_REVIEW_REQUIRED_DATA_AND_INFERENCE_NO_GO",
        source_sha256={"module.py": SHA},
        source_pin_kind={"module.py": R03PinKind.FILESYSTEM_SHA256},
        test_sha256={"test.py": SHA},
        test_pin_kind={"test.py": R03PinKind.FILESYSTEM_SHA256},
        verifier_sha256=SHA,
        verifier_pin_kind=R03PinKind.FILESYSTEM_SHA256,
        stage_exit_tests={"I0": ("test_contract",)},
        negative_tests=NEGATIVE_TESTS,
        focused_test_command="synthetic-only",
        regression_test_command="r02-only",
        focused_result={"command": "synthetic-only", "exit_code": 0, "passed": 49},
        r02_api_result={"command": "r02-api", "exit_code": 0, "passed": 27},
        full_overlay_result={"command": "r02-full", "exit_code": 0, "passed": 433},
        style_exit_codes={"black": 0, "flake8": 0, "isort": 0},
        counters=R03ZeroCounters(),
        organizational_independence_established=False,
    )
    assert len(evidence.evidence_sha256) == 64
    values = evidence.model_dump(mode="python", exclude={"evidence_sha256"})
    values["source_pin_kind"] = {}
    with pytest.raises(Exception, match="coverage"):
        build_implementation_evidence(**values)


def test_implementation_modules_have_no_provider_network_or_process_imports() -> None:
    root = Path(__file__).resolve().parents[1] / "v2" / "research" / "news_reasoning"
    forbidden = {"anthropic", "openai", "requests", "httpx", "socket", "subprocess", "urllib", "transformers", "torch"}
    for path in sorted(root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert not imported & forbidden, f"{path.name}: {sorted(imported & forbidden)}"
