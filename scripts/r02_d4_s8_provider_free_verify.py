"""Provider-free verifier for the R02 D4-S8 two-artifact authorization freeze."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from v2.research.overlay.r02_d4_s6_contracts import R02D4S6LiveAuthorizationArtifact
from v2.research.overlay.r02_d4_s7_contracts import R02D4S7LiveAuthorizationArtifact

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "r02-d4-s8-20260719"
S6_PATH = ROOT / "docs/r02-d4-s6-live-authorization.json"
S7_PATH = ROOT / "docs/r02-d4-s7-live-authorization.json"
FREEZE_PATH = ROOT / "docs/r02-d4-s8-freeze-manifest.json"
ZERO_CALL_PATH = ROOT / "docs/r02-d4-s8-zero-call-manifest.json"
S6_SHA256 = "5eb08e1994add052cf7994f56add7a40df2ef8531bdba32afbed0c9f493178d4"
S7_SHA256 = "c05bf7a733f6b8985e54bcd5170f6534112b7ed28e8addecfba9d9a16c9a5042"
HEAD = "3efd3b82cdb813383211a18a3a19482f734782c7"
S7_CONTRACT_SHA256 = "c2b4b729e77690c3f02d28de503d4172e038d19b7230c954b8f2e4b167deb2b1"
S6_REVIEW_SHA256 = "00c180968a51e37c97966af3bea970c536fbca29efd2d0583f7da0283504d549"
S7_REVIEW_SHA256 = "4c8530325ccf1758824ca1b709fbc0b4f7db45855e53670aaf7c1f6a6d5a99aa"
S6_ROOT = ROOT / ".research_artifacts/r02-d4-s6-r02-d4-s8-20260719"
S7_ROOT = ROOT / ".research_artifacts/r02-d4-s7-transport-r02-d4-s8-20260719"
S8_FILES = frozenset(
    {
        "docs/r02-d4-s6-live-authorization.json",
        "docs/r02-d4-s7-live-authorization.json",
        "docs/r02-d4-s8-freeze-manifest.json",
        "docs/r02-d4-s8-independent-review-handoff.md",
        "docs/r02-d4-s8-zero-call-manifest.json",
        "scripts/r02_d4_s8_provider_free_verify.py",
    }
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_canonical(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise AssertionError(f"{path}: non-canonical JSON bytes")
    return value, raw


def assert_raises(
    fn: Callable[[], Any],
    label: str,
    expected: type[BaseException] = AssertionError,
) -> None:
    try:
        fn()
    except expected:
        return
    except Exception as exc:
        raise AssertionError(f"negative test raised unexpected {type(exc).__name__}: {label}") from exc
    raise AssertionError(f"negative test did not fail: {label}")


def repository_state() -> tuple[str, tuple[str, ...], bool, tuple[str, ...]]:
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = tuple(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).splitlines())
    base_is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", HEAD, current],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).returncode == 0
    changed_from_base = tuple(
        subprocess.check_output(
            ["git", "diff", "--name-only", f"{HEAD}..{current}"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    return current, status, base_is_ancestor, changed_from_base


def verify() -> None:
    s6, s6_raw = load_canonical(S6_PATH)
    s7, s7_raw = load_canonical(S7_PATH)
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    zero = json.loads(ZERO_CALL_PATH.read_text(encoding="utf-8"))

    R02D4S6LiveAuthorizationArtifact.model_validate(s6)
    R02D4S7LiveAuthorizationArtifact.model_validate(s7)
    assert sha256_bytes(s6_raw) == S6_SHA256
    assert sha256_bytes(s7_raw) == S7_SHA256
    assert s6["run_id"] == s7["run_id"] == RUN_ID
    assert s7["s6_live_authorization_sha256"] == sha256_bytes(s6_raw)
    require_review_and_contract_pins(s6, s7)
    assert s7["accepted_s7_commit"] == HEAD
    assert s7["accepted_s6_commit"] == "c88bde40015d88bf31f4af25587c339359971f2e"
    assert s6["approved_scope"] == s7["approved_scope"] == "INDIVISIBLE_ALL_69_LIVE"
    assert all(s6[k] is False for k in ("micro_pilot_authorized", "retry_or_replacement_authorized", "resume_authorized"))
    assert all(s7[k] is False for k in ("micro_pilot_authorized", "retry_or_replacement_authorized", "resume_authorized"))

    assert freeze["scope"] == {
        "attempt_count": 69,
        "execution_order": "ELIGIBLE_CASES_BY_FRAME_ORDINAL_ASCENDING",
        "aggregate_token_cap": 2208000,
        "per_attempt_token_reserve": 32000,
        "per_attempt_timeout_ms": 900000,
        "settled_failure_cap": 6,
        "micro_pilot_attempts": 0,
        "retry_cap": 0,
        "replacement_cap": 0,
        "resume_cap": 0,
        "indivisible_all_69_one_shot": True,
    }
    assert freeze["run_id"] == RUN_ID
    assert freeze["execution_enabled"] is False
    assert freeze["roots"]["materialized"] is False
    assert freeze["roots"]["distinct"] is True
    assert zero["provider_calls"] == zero["codex_exec_invocations"] == zero["live_runs"] == 0
    assert zero["production_root_materializations"] == zero["micro_pilot_runs"] == 0
    assert zero["retry_runs"] == zero["replacement_runs"] == zero["resume_runs"] == 0
    assert not S6_ROOT.exists() and not S7_ROOT.exists()
    require_repository_state(*repository_state())

    # Negative tests use memory or a temporary directory only.
    assert_raises(lambda: load_canonical_from_bytes(s6_raw + b"\n"), "trailing newline")
    assert_raises(lambda: require_same_run_id(s6, {**s7, "run_id": "r02-d4-s8-other"}), "run-id drift")
    assert_raises(lambda: require_s6_binding(s7, "0" * 64), "S6 digest drift")
    assert_raises(
        lambda: require_review_and_contract_pins(
            {**s6, "accepted_s6_review_sha256": "0" * 64}, s7
        ),
        "S6 review digest drift",
    )
    assert_raises(
        lambda: require_review_and_contract_pins(
            s6, {**s7, "accepted_s7_review_sha256": "0" * 64}
        ),
        "S7 review digest drift",
    )
    assert_raises(
        lambda: require_review_and_contract_pins(
            s6, {**s7, "accepted_s7_contract_sha256": "0" * 64}
        ),
        "S7 contract digest drift",
    )
    for capability in (
        "micro_pilot_authorized",
        "retry_or_replacement_authorized",
        "resume_authorized",
    ):
        assert_raises(
            lambda capability=capability: require_no_capability({**s7, capability: True}),
            f"{capability} capability",
        )
    with tempfile.TemporaryDirectory() as temp:
        occupied = Path(temp) / "root"
        occupied.mkdir()
        (occupied / "sentinel").write_text("x", encoding="utf-8")
        assert_raises(lambda: require_empty_root(occupied), "nonempty root")
    assert_raises(
        lambda: require_repository_state("0" * 40, tuple(), False, tuple()),
        "wrong repository head",
    )
    assert_raises(
        lambda: require_repository_state(HEAD, (" M unrelated.txt",), True, tuple()),
        "dirty repository",
    )
    require_repository_state("1" * 40, tuple(), True, tuple(sorted(S8_FILES)))

    print("PASS_R02_D4_S8_PROVIDER_FREE_TWO_ARTIFACT_FREEZE")
    print(f"run_id={RUN_ID} attempts=69 token_cap=2208000 timeout_ms=900000 failure_cap=6")
    print(f"s6_sha256={S6_SHA256} s7_sha256={S7_SHA256} provider_calls=0 codex_exec=0 roots_materialized=0")
    print("negative_tests=7 passed")


def load_canonical_from_bytes(raw: bytes) -> dict[str, Any]:
    value = json.loads(raw)
    if raw != canonical_bytes(value):
        raise AssertionError("non-canonical")
    return value


def require_same_run_id(s6: dict[str, Any], s7: dict[str, Any]) -> None:
    if s6.get("run_id") != s7.get("run_id"):
        raise AssertionError("run identity mismatch")


def require_s6_binding(s7: dict[str, Any], digest: str) -> None:
    if s7.get("s6_live_authorization_sha256") != digest:
        raise AssertionError("S6 binding mismatch")


def require_review_and_contract_pins(s6: dict[str, Any], s7: dict[str, Any]) -> None:
    if s6.get("accepted_s6_review_sha256") != S6_REVIEW_SHA256:
        raise AssertionError("S6 review digest mismatch")
    if s7.get("accepted_s6_review_sha256") != S6_REVIEW_SHA256:
        raise AssertionError("cross-artifact S6 review digest mismatch")
    if s7.get("accepted_s7_review_sha256") != S7_REVIEW_SHA256:
        raise AssertionError("S7 review digest mismatch")
    if s7.get("accepted_s7_contract_sha256") != S7_CONTRACT_SHA256:
        raise AssertionError("S7 contract digest mismatch")


def require_no_capability(value: dict[str, Any]) -> None:
    if any(value.get(key) is not False for key in ("micro_pilot_authorized", "retry_or_replacement_authorized", "resume_authorized")):
        raise AssertionError("forbidden capability")


def require_empty_root(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise AssertionError("root is not empty")


def require_repository_state(
    current: str,
    status: tuple[str, ...],
    base_is_ancestor: bool,
    changed_from_base: tuple[str, ...],
) -> None:
    allowed_untracked = {f"?? {path}" for path in S8_FILES}
    pre_commit = current == HEAD and set(status) == allowed_untracked
    post_commit = (
        current != HEAD
        and not status
        and base_is_ancestor
        and set(changed_from_base) == S8_FILES
    )
    if not (pre_commit or post_commit):
        raise AssertionError("repository is neither exact pre-commit S8 state nor clean S8-only descendant")


if __name__ == "__main__":
    verify()
