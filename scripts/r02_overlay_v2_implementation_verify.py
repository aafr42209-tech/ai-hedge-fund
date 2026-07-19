"""Provider-free verifier for the R02 overlay-v2 I0-I5 implementation freeze."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, TypeVar

ROOT = Path(__file__).resolve().parents[1]
BASE_HEAD = "245adc2d1f023a87d1cbfd86a7b726aec810bd78"
EVIDENCE_PATH = ROOT / "docs/r02-overlay-v2-implementation-evidence.json"
ZERO_CALL_PATH = ROOT / "docs/r02-overlay-v2-implementation-zero-call-manifest.json"
IMPLEMENTATION_DOC_PATH = ROOT / "docs/r02-overlay-v2-provider-free-implementation.md"

SOURCE_PATHS = (
    "v2/research/overlay/r02_v2_contracts.py",
    "v2/research/overlay/r02_v2_payload.py",
    "v2/research/overlay/r02_v2_grounding.py",
    "v2/research/overlay/r02_v2_comparator.py",
    "v2/research/overlay/r02_v2_selection.py",
    "v2/research/overlay/r02_v2_headroom.py",
    "v2/research/overlay/r02_v2_power.py",
    "v2/research/overlay/r02_v2_audit.py",
)
TEST_PATHS = (
    "v2/research/overlay/_r02_v2_test_helpers.py",
    "v2/research/overlay/test_r02_v2_contracts.py",
    "v2/research/overlay/test_r02_v2_payload.py",
    "v2/research/overlay/test_r02_v2_grounding.py",
    "v2/research/overlay/test_r02_v2_comparator.py",
    "v2/research/overlay/test_r02_v2_selection.py",
    "v2/research/overlay/test_r02_v2_headroom.py",
    "v2/research/overlay/test_r02_v2_power.py",
    "v2/research/overlay/test_r02_v2_audit.py",
)
ARTIFACT_PATHS = (
    "docs/r02-overlay-v2-provider-free-implementation.md",
    "docs/r02-overlay-v2-implementation-evidence.json",
    "docs/r02-overlay-v2-implementation-zero-call-manifest.json",
    "docs/r02-overlay-v2-implementation-review-handoff.md",
    "scripts/r02_overlay_v2_implementation_verify.py",
)
DEPENDENCY_PATHS = ("pyproject.toml", "poetry.lock")
INTENDED_PATHS = frozenset((*SOURCE_PATHS, *TEST_PATHS, *ARTIFACT_PATHS, *DEPENDENCY_PATHS))
EXCLUDED_USER_PATHS = frozenset(
    {
        "docs/news-llm-reasoning-reuse-feasibility-handoff.md",
        "docs/r03-news-reasoning-charter-draft.md",
        "docs/r03-news-reasoning-data-reuse-decision.md",
        "docs/r03-news-reasoning-p5-review-handoff.md",
        "docs/r03-news-reasoning-p5-zero-call-manifest.json",
        "docs/r03-news-reasoning-provider-free-coverage-audit.json",
        "docs/r03-news-reasoning-provider-free-preregistration-draft.md",
        "docs/r03-pit-universe-feasibility-evidence.json",
        "docs/r03-pit-universe-feasibility.md",
    }
)
FORBIDDEN_IMPORT_ROOTS = frozenset({"anthropic", "httpx", "openai", "requests", "socket", "subprocess", "urllib"})
EXPECTED_GATES = (
    "SCHEMA_METASCHEMA_AND_BYTE_PARITY",
    "CANONICAL_PAYLOAD_AND_DIGEST_REPRODUCIBILITY",
    "PUBLIC_METRIC_RECOMPUTATION",
    "INFORMATION_PARITY_AND_FORBIDDEN_FIELD_REJECTION",
    "NINETEEN_SCORER_IDENTITY_AND_ARITHMETIC",
    "CANDIDATE_ORDER_PERMUTATION_INVARIANCE",
    "RFC6901_ESCAPE_INDEX_BOUNDS_AND_SCOPE",
    "HIDDEN_ORACLE_CALL_ORDER_ISOLATION",
    "SELECTION_REPLAY_AND_SPLIT_NONOVERLAP",
    "HEADROOM_LABELS_FLOORS_AND_DIAGNOSTICS",
    "POWER_GRID_COMPLETENESS_AND_WORST_CELL_RULE",
    "FAILURE_ITT_AND_NO_DROPPED_FAILURES",
    "NO_PROVIDER_NETWORK_SUBPROCESS_CREDENTIAL_OR_ROOT_CAPABILITY",
)
T = TypeVar("T", bound=BaseException)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_canonical(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    parsed = json.loads(raw)
    require(raw == canonical_json_bytes(parsed), f"noncanonical JSON: {path}")
    return parsed


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def status_entries() -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in git("status", "--porcelain=v1", "--untracked-files=all").stdout.splitlines():
        require(len(line) >= 4, "malformed git status entry")
        entries[line[3:]] = line[:2]
    return entries


def require_repository_state() -> None:
    head = git("rev-parse", "HEAD").stdout.strip()
    entries = status_entries()
    unexpected = set(entries) - INTENDED_PATHS - EXCLUDED_USER_PATHS
    require(not unexpected, f"unexpected worktree paths: {sorted(unexpected)}")
    intended_entries = {path: code for path, code in entries.items() if path in INTENDED_PATHS}
    expected_precommit = {
        **{path: " M" for path in DEPENDENCY_PATHS},
        **{path: "??" for path in (*SOURCE_PATHS, *TEST_PATHS, *ARTIFACT_PATHS)},
    }
    if head == BASE_HEAD:
        require(intended_entries == expected_precommit, "pre-commit implementation change set mismatch")
        return

    require(git("merge-base", "--is-ancestor", BASE_HEAD, head, check=False).returncode == 0, "base is not an ancestor")
    changed = set(git("diff", "--name-only", f"{BASE_HEAD}..{head}").stdout.splitlines())
    committed_implementation = changed - EXCLUDED_USER_PATHS
    if not committed_implementation:
        require(changed <= EXCLUDED_USER_PATHS, "pre-commit descendant contains unrelated committed paths")
        require(intended_entries == expected_precommit, "pre-commit descendant implementation change set mismatch")
        return
    require(committed_implementation == INTENDED_PATHS, "post-commit implementation file set mismatch")
    require(not intended_entries, "post-commit intended paths must be clean")


def imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def require_file_hashes(evidence: dict[str, Any]) -> None:
    hashes = evidence["file_sha256"]
    require(set(hashes) == set((*SOURCE_PATHS, *TEST_PATHS, *DEPENDENCY_PATHS)), "evidence file hash set mismatch")
    for relative, expected in hashes.items():
        require(sha256_path(ROOT / relative) == expected, f"file digest drift: {relative}")
    for pin in evidence["accepted_inputs"].values():
        require(sha256_path(ROOT / pin["path"]) == pin["sha256"], f"accepted input digest drift: {pin['path']}")


def require_static_boundaries() -> None:
    for relative in SOURCE_PATHS:
        roots = imported_roots(ROOT / relative)
        require(not (roots & FORBIDDEN_IMPORT_ROOTS), f"forbidden capability import in {relative}")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    require('jsonschema = "^4.23.0"' in pyproject, "jsonschema dev dependency missing")


def require_evidence(evidence: dict[str, Any]) -> None:
    require(evidence["schema_version"] == "r02-overlay-v2-provider-free-implementation-evidence-v1", "schema version mismatch")
    require(evidence["base_head"] == BASE_HEAD, "base HEAD mismatch")
    require(
        evidence["status"]
        == "TECHNICALLY_ACCEPTED_PROVIDER_FREE_IMPLEMENTATION_FIXTURE_AND_LIVE_NO_GO",
        "implementation status mismatch",
    )
    require(evidence["implementation_file_count"] == 8, "implementation file count mismatch")
    require(tuple(evidence["implementation_files"]) == SOURCE_PATHS, "implementation file list mismatch")
    require(tuple(evidence["test_and_helper_files"]) == TEST_PATHS, "test file list mismatch")
    require(
        set(evidence["excluded_unrelated_user_paths"]) == EXCLUDED_USER_PATHS,
        "excluded user path set mismatch",
    )
    require(set(evidence["gate_to_tests"]) == set(EXPECTED_GATES), "thirteen-gate traceability mismatch")
    require(all(evidence["gate_to_tests"][gate] for gate in EXPECTED_GATES), "empty gate mapping")
    require(evidence["test_results"]["focused"]["passed"] == 27, "focused test count mismatch")
    require(evidence["test_results"]["full_overlay"]["passed"] == 433, "full test count mismatch")
    require(evidence["test_results"]["focused"]["exit_code"] == 0, "focused tests did not pass")
    require(evidence["test_results"]["full_overlay"]["exit_code"] == 0, "full tests did not pass")
    require(
        evidence["power_gate_policy"]
        == {
            "comparison": "GREATER_THAN_OR_EQUAL",
            "estimator": "TWO_SIDED_95_PERCENT_WILSON_LOWER_BOUND",
            "point_estimate_may_govern": False,
            "threshold_ppm": 800_000,
        },
        "power-gate estimator policy mismatch",
    )
    counters = evidence["zero_call_counters"]
    require(all(value == 0 for value in counters.values()), "zero-call counter is nonzero")
    boundary = evidence["authorization_boundary"]
    require(boundary["provider_calls_authorized"] is False, "provider calls authorized")
    require(boundary["fixture_materialization_authorized"] is False, "fixture materialization authorized")
    require(boundary["pilot_live_authorized"] is False, "pilot LIVE authorized")
    require(boundary["confirmatory_live_authorized"] is False, "confirmatory LIVE authorized")
    require(boundary["commit_authorized"] is False, "implementation commit authorized")
    require(boundary["push_authorized"] is False, "implementation push authorized")
    acceptance = evidence["technical_acceptance"]
    require(acceptance["accepted"] is True, "technical acceptance missing")
    require(acceptance["blocking_findings_open"] == 0, "blocking findings remain")
    require(
        acceptance["accepted_implementation_commit"]
        == "8bf074818bb780baa3a2954685af74659bc19f3b",
        "accepted implementation commit mismatch",
    )
    require(acceptance["organizational_independence_established"] is False, "independence overclaim")
    require(acceptance["status_promotion_commit_authorized"] is False, "status promotion commit authorized")
    require(acceptance["status_promotion_push_authorized"] is False, "status promotion push authorized")


def require_zero_call_manifest(zero: dict[str, Any], evidence: dict[str, Any]) -> None:
    require(zero["schema_version"] == "r02-overlay-v2-implementation-zero-call-manifest-v1", "zero-call schema mismatch")
    require(zero["base_head"] == BASE_HEAD, "zero-call base mismatch")
    require(zero["evidence_sha256"] == sha256_path(EVIDENCE_PATH), "evidence pin mismatch")
    require(zero["implementation_doc_sha256"] == sha256_path(IMPLEMENTATION_DOC_PATH), "implementation doc pin mismatch")
    require(zero["verifier_sha256"] == sha256_path(Path(__file__)), "verifier pin mismatch")
    require(zero["status"] == evidence["status"], "zero-call status drift")
    require(
        set(zero["excluded_unrelated_user_paths"]) == EXCLUDED_USER_PATHS,
        "zero-call excluded user path set mismatch",
    )
    require(zero["zero_call_counters"] == evidence["zero_call_counters"], "zero-call counter drift")
    require(zero["authorization_boundary"] == evidence["authorization_boundary"], "authorization boundary drift")
    require(zero["technical_acceptance"] == evidence["technical_acceptance"], "technical acceptance drift")
    require(zero["power_gate_policy"] == evidence["power_gate_policy"], "power-gate policy drift")
    require(
        zero["worktree_policy"]
        == "BASE_OR_DESCENDANT_WITH_ONLY_NINE_ENUMERATED_USER_PATHS_COMMITTED_MODIFIED_OR_UNTRACKED_AND_EXACT_TWO_MODIFIED_PLUS_TWENTY_TWO_NEW_IMPLEMENTATION_PATHS; POST_COMMIT_DIFF_MUST_ADD_EXACT_TWENTY_FOUR_IMPLEMENTATION_PATHS",
        "worktree policy drift",
    )
    require(len(zero["negative_tests"]) == 10, "negative-test declaration mismatch")


def assert_raises(expected: type[T], action: Callable[[], Any]) -> None:
    try:
        action()
    except expected:
        return
    except Exception as exc:
        raise AssertionError(f"unexpected exception {type(exc).__name__}: {exc}") from exc
    raise AssertionError(f"expected {expected.__name__}")


def run_negative_tests(evidence: dict[str, Any]) -> int:
    with tempfile.TemporaryDirectory(prefix="r02-v2-implementation-negative-") as directory:
        path = Path(directory) / "noncanonical.json"
        path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        assert_raises(AssertionError, lambda: load_canonical(path))

    changed = copy.deepcopy(evidence)
    changed["zero_call_counters"]["provider_calls"] = 1
    assert_raises(AssertionError, lambda: require_evidence(changed))

    changed = copy.deepcopy(evidence)
    changed["implementation_file_count"] = 7
    assert_raises(AssertionError, lambda: require_evidence(changed))

    changed = copy.deepcopy(evidence)
    del changed["gate_to_tests"][EXPECTED_GATES[0]]
    assert_raises(AssertionError, lambda: require_evidence(changed))

    changed = copy.deepcopy(evidence)
    changed["file_sha256"][SOURCE_PATHS[0]] = "0" * 64
    assert_raises(AssertionError, lambda: require_file_hashes(changed))

    with tempfile.TemporaryDirectory(prefix="r02-v2-import-negative-") as directory:
        path = Path(directory) / "bad.py"
        path.write_text("import requests\n", encoding="utf-8")
        require(imported_roots(path) & FORBIDDEN_IMPORT_ROOTS == {"requests"}, "forbidden import negative control failed")

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    require('jsonschema = "^4.23.0"' in pyproject, "jsonschema positive control failed")
    require('jsonschema = "^4.23.0"' not in pyproject.replace('jsonschema = "^4.23.0"', ""), "jsonschema negative control failed")

    changed = copy.deepcopy(evidence)
    changed["authorization_boundary"]["fixture_materialization_authorized"] = True
    assert_raises(AssertionError, lambda: require_evidence(changed))

    changed = copy.deepcopy(evidence)
    changed["power_gate_policy"]["estimator"] = "POINT_ESTIMATE"
    assert_raises(AssertionError, lambda: require_evidence(changed))

    changed = copy.deepcopy(evidence)
    changed["status"] = "REMEDIATED_RESEALED_PROVIDER_FREE_REVIEW_REQUIRED"
    assert_raises(AssertionError, lambda: require_evidence(changed))
    return 10


def main() -> None:
    evidence = load_canonical(EVIDENCE_PATH)
    zero = load_canonical(ZERO_CALL_PATH)
    require_repository_state()
    require_file_hashes(evidence)
    require_static_boundaries()
    require_evidence(evidence)
    require_zero_call_manifest(zero, evidence)
    negative_tests = run_negative_tests(evidence)
    print("PASS_R02_OVERLAY_V2_PROVIDER_FREE_IMPLEMENTATION " f"negative_tests={negative_tests} focused_tests=27 full_overlay_tests=433 " "provider_calls=0 live_runs=0 implementation_files=8")


if __name__ == "__main__":
    main()
