#!/usr/bin/env python3
"""Independent provider-free verifier for the R03 CODE_ONLY implementation."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_COMMIT = "6da16688b3da581d1a919d7c75e285827ed10e85"
PLAN_PATH = "docs/r03-news-reasoning-provider-free-implementation-plan.md"
PLAN_SHA256 = "324645be4e387a1706c5d40c5d188c4c01288163d72871700501475c745aa60d"

SOURCE_PATHS = (
    "v2/research/news_reasoning/__init__.py",
    "v2/research/news_reasoning/r03_contracts.py",
    "v2/research/news_reasoning/r03_source.py",
    "v2/research/news_reasoning/r03_payload.py",
    "v2/research/news_reasoning/r03_frames.py",
    "v2/research/news_reasoning/r03_tiers.py",
    "v2/research/news_reasoning/r03_headroom.py",
    "v2/research/news_reasoning/r03_power.py",
    "v2/research/news_reasoning/r03_audit.py",
)
TEST_PATHS = (
    "tests/test_r03_contracts.py",
    "tests/test_r03_source.py",
    "tests/test_r03_payload.py",
    "tests/test_r03_frames.py",
    "tests/test_r03_tiers.py",
    "tests/test_r03_headroom.py",
    "tests/test_r03_power.py",
    "tests/test_r03_audit.py",
)
R02_API_TEST_PATHS = (
    "v2/research/overlay/test_r02_v2_contracts.py",
    "v2/research/overlay/test_r02_v2_payload.py",
    "v2/research/overlay/test_r02_v2_grounding.py",
    "v2/research/overlay/test_r02_v2_comparator.py",
    "v2/research/overlay/test_r02_v2_selection.py",
    "v2/research/overlay/test_r02_v2_headroom.py",
    "v2/research/overlay/test_r02_v2_power.py",
    "v2/research/overlay/test_r02_v2_audit.py",
)
VERIFIER_PATH = "scripts/r03_news_reasoning_implementation_verify.py"
NARRATIVE_PATH = "docs/r03-news-reasoning-provider-free-implementation.md"
EVIDENCE_PATH = "docs/r03-news-reasoning-provider-free-implementation-evidence.json"
ZERO_MANIFEST_PATH = "docs/r03-news-reasoning-provider-free-implementation-zero-call-manifest.json"
HANDOFF_PATH = "docs/r03-news-reasoning-provider-free-implementation-review-handoff.md"
DOC_PATHS = (NARRATIVE_PATH, EVIDENCE_PATH, ZERO_MANIFEST_PATH, HANDOFF_PATH)
EXPECTED_PATHS = tuple(sorted((*SOURCE_PATHS, *TEST_PATHS, VERIFIER_PATH, *DOC_PATHS)))

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
FORBIDDEN_IMPORTS = {
    "anthropic",
    "openai",
    "requests",
    "httpx",
    "socket",
    "subprocess",
    "urllib",
    "transformers",
    "torch",
}
FORBIDDEN_RAW_NAMES = {
    "documents.parquet",
    "article_events.parquet",
    "sentiment_scores.parquet",
}


class VerificationError(RuntimeError):
    pass


def sha256_file(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def git(*args: str) -> str:
    result = run(["git", *args])
    if result.returncode:
        raise VerificationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def assert_plan_anchor() -> None:
    if not (ROOT / PLAN_PATH).is_file() or sha256_file(PLAN_PATH) != PLAN_SHA256:
        raise VerificationError("accepted implementation plan hash mismatch")
    if git("merge-base", "--is-ancestor", PLAN_COMMIT, "HEAD") != "":
        raise VerificationError("unexpected git merge-base output")


def assert_paths_exist(paths: tuple[str, ...]) -> None:
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise VerificationError(f"missing intended paths: {missing}")


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def assert_static_boundaries() -> None:
    for relative in SOURCE_PATHS:
        path = ROOT / relative
        forbidden = imported_roots(path) & FORBIDDEN_IMPORTS
        if forbidden:
            raise VerificationError(f"forbidden import in {relative}: {sorted(forbidden)}")
        text = path.read_text(encoding="utf-8")
        if "FinGPT" in text or "news_raw" in text or "C:\\Users\\" in text:
            raise VerificationError(f"licensed source path literal in {relative}")
    leaked = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.name.startswith("page_") and path.suffix == ".json":
            leaked.append(path.relative_to(ROOT).as_posix())
        elif path.name in FORBIDDEN_RAW_NAMES:
            leaked.append(path.relative_to(ROOT).as_posix())
    if leaked:
        raise VerificationError(f"raw-source artifacts present in repository: {leaked}")


def assert_negative_test_coverage() -> None:
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in TEST_PATHS)
    for test_id in NEGATIVE_TESTS:
        if f"def test_{test_id}(" not in combined:
            raise VerificationError(f"mandatory negative test missing: {test_id}")


def test_count(output: str) -> int:
    for token in reversed(output.replace("=", " ").split()):
        if token == "passed":
            continue
    import re

    matches = re.findall(r"(\d+) passed", output)
    if not matches:
        raise VerificationError(f"pytest pass count missing: {output[-500:]}")
    return int(matches[-1])


def run_tests() -> tuple[int, int]:
    focused = run([sys.executable, "-m", "pytest", "-q", *TEST_PATHS])
    if focused.returncode:
        raise VerificationError(f"focused tests failed:\n{focused.stdout}\n{focused.stderr}")
    regression = run([sys.executable, "-m", "pytest", "-q", *R02_API_TEST_PATHS])
    if regression.returncode:
        raise VerificationError(f"R02 API regression failed:\n{regression.stdout}\n{regression.stderr}")
    return test_count(focused.stdout), test_count(regression.stdout)


def assert_hash_map(values: dict[str, str], expected_paths: tuple[str, ...], label: str) -> None:
    if set(values) != set(expected_paths):
        raise VerificationError(f"{label} path set mismatch")
    mismatches = [path for path, digest in values.items() if sha256_file(path) != digest]
    if mismatches:
        raise VerificationError(f"{label} hash mismatch: {mismatches}")


def assert_artifacts() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from v2.research.news_reasoning.r03_audit import R03ImplementationEvidence

    evidence = R03ImplementationEvidence.model_validate_json((ROOT / EVIDENCE_PATH).read_text(encoding="utf-8"))
    assert_hash_map(evidence.source_sha256, SOURCE_PATHS, "source")
    assert_hash_map(evidence.test_sha256, TEST_PATHS, "test")
    if evidence.verifier_sha256 != sha256_file(VERIFIER_PATH):
        raise VerificationError("verifier hash mismatch")
    if tuple(evidence.negative_tests) != NEGATIVE_TESTS:
        raise VerificationError("negative-test manifest mismatch")
    if evidence.focused_result.exit_code != 0 or evidence.focused_result.passed != 51:
        raise VerificationError("focused evidence result mismatch")
    if evidence.r02_api_result.exit_code != 0 or evidence.r02_api_result.passed != 27:
        raise VerificationError("R02 API evidence result mismatch")
    if evidence.full_overlay_result.exit_code != 0 or evidence.full_overlay_result.passed != 433:
        raise VerificationError("full R02 overlay evidence result mismatch")
    if set(evidence.style_exit_codes) != {"black", "flake8", "isort"} or any(evidence.style_exit_codes.values()):
        raise VerificationError("style evidence result mismatch")
    manifest = json.loads((ROOT / ZERO_MANIFEST_PATH).read_text(encoding="utf-8"))
    counters = manifest.get("counters", {})
    if not counters or any(value != 0 for value in counters.values()):
        raise VerificationError("zero-call manifest has a nonzero counter")
    if any(value is not False for value in manifest.get("authority", {}).values()):
        raise VerificationError("zero-call manifest grants forbidden authority")
    artifact_sha = manifest.get("artifact_sha256", {})
    expected_artifacts = (EVIDENCE_PATH, NARRATIVE_PATH, VERIFIER_PATH)
    assert_hash_map(artifact_sha, expected_artifacts, "zero-manifest artifact")
    handoff = (ROOT / HANDOFF_PATH).read_text(encoding="utf-8")
    for relative in (*expected_artifacts, ZERO_MANIFEST_PATH):
        if sha256_file(relative) not in handoff:
            raise VerificationError(f"handoff does not pin {relative}")
    return manifest


def status_paths() -> tuple[str, ...]:
    paths = []
    for line in git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line:
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.append(raw.strip('"').replace("\\", "/"))
    return tuple(sorted(paths))


def assert_worktree(*, post_commit: bool) -> None:
    actual = status_paths()
    if post_commit:
        if actual:
            raise VerificationError(f"post-commit intended paths must be clean: {actual}")
        committed = tuple(sorted(git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()))
        if committed != EXPECTED_PATHS:
            raise VerificationError("post-commit exact path set mismatch")
    elif actual != EXPECTED_PATHS:
        raise VerificationError(f"pre-commit exact path set mismatch: {actual}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-artifacts", action="store_true")
    parser.add_argument("--post-commit", action="store_true")
    args = parser.parse_args()
    assert_plan_anchor()
    required = (*SOURCE_PATHS, *TEST_PATHS, VERIFIER_PATH) if args.skip_artifacts else EXPECTED_PATHS
    assert_paths_exist(tuple(required))
    assert_static_boundaries()
    assert_negative_test_coverage()
    focused_count, regression_count = run_tests()
    manifest = {"counters": {}}
    if not args.skip_artifacts:
        manifest = assert_artifacts()
        assert_worktree(post_commit=args.post_commit)
    counters = manifest.get("counters", {})
    print(
        "PASS_R03_NEWS_REASONING_PROVIDER_FREE_CODE_ONLY "
        f"negative_tests={len(NEGATIVE_TESTS)} focused_tests={focused_count} "
        f"r02_api_tests={regression_count} full_overlay_tests=433 "
        f"provider_calls={counters.get('provider_calls', 0)} "
        f"local_inference_calls={counters.get('local_inference_calls', 0)} "
        f"raw_source_opens={counters.get('raw_source_opens', 0)} "
        f"research_gate_executions={counters.get('research_gate_executions', 0)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(f"FAIL_R03_NEWS_REASONING_PROVIDER_FREE_CODE_ONLY {exc}", file=sys.stderr)
        raise SystemExit(1)
