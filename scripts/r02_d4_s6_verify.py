"""Reproduce the R02 D4-S6 draft with fake transport and a temporary root only."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from v2.research.overlay.canonical import canonical_sha256, sha256_hex
from v2.research.overlay.r02_d3_preflight import _filesystem_tree
from v2.research.overlay.r02_d4_s6_contracts import (
    offline_fake_authorization,
    R02_D4_S6_ATTEMPT_CAP,
    R02_D4_S6_TIMEOUT_MS,
    R02_D4_S6_TOKEN_CAP,
    R02D4S6TransportResult,
)
from v2.research.overlay.r02_d4_s6_replay import replay_s6_audit_root
from v2.research.overlay.r02_d4_s6_runner import (
    build_provider_free_run_plan,
    R02D4S6Runner,
)

ROOT = Path(__file__).resolve().parents[1]
PROTECTED_ROOT = ROOT / ".research_artifacts"
EXPECTED_PROTECTED_FILE_COUNT = 3_687
EXPECTED_PROTECTED_TREE_SHA256 = "692ced9177f71cbe1af45a8f3ce06b7ec1c690fba87a8c7de254a1dfc834f891"
EXPECTED_D3_POSTHOC_SHA256 = "1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73"
EXPECTED_FILE_SHA256 = {
    "docs/r02-d4-s6-runner-contract.json": "edea01bf2dc6b3c110cf780bc5c774266871ae06b8d716685965fadf34f2f26f",
    "docs/r02-d4-s6-runner-implementation.md": "0c42f74513bb3432ffce0a2721195ecd7882a038f2aa2eaf63a3adeaab6da20e",
    "v2/research/overlay/r02_d4_s6_contracts.py": "9cc3e3dcc07d635555729ba7d19800e349658a259e8592b0bddb52963d7cc433",
    "v2/research/overlay/r02_d4_s6_audit.py": "935cf31e779da3fe1b7d5b0e381080af5c9d3952e075b1bd7a92c495ee03971b",
    "v2/research/overlay/r02_d4_s6_runner.py": "8b33288f21a2b85825c5f101a40c5f0f1c7170cad0437fa342c5c255049e3eac",
    "v2/research/overlay/r02_d4_s6_replay.py": "eb22acbfa40917c3465fa2060dca0879d4f0b1decf32ba66c64e83db7ef1cd78",
    "v2/research/overlay/test_r02_d4_s6_runner.py": "285cbae5d920cf99433b324ffa45490a83a77d5a04121c8f6ec936f0966b5ceb",
}


def _response() -> str:
    return json.dumps(
        {
            "schema_version": "r02-selector-response-v1",
            "selected_candidate_id": "P00",
            "confidence": 64,
            "reason_codes": ["TIE_BREAK_PREFERENCE"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


class VerifierFakeTransport:
    r02_d4_s6_execution_capability = "OFFLINE_FAKE"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int]] = []

    def execute(
        self,
        *,
        run_id: str,
        attempt_id: str,
        attempt,
        selector_request,
        timeout_ms: int,
    ) -> R02D4S6TransportResult:
        if canonical_sha256(selector_request) != attempt.selector_request_sha256:
            raise RuntimeError("selector request digest drift")
        self.calls.append((attempt.fixture_id, attempt_id, timeout_ms))
        raw = _response()
        return R02D4S6TransportResult(
            run_id=run_id,
            fixture_id=attempt.fixture_id,
            attempt_id=attempt_id,
            raw_response=raw,
            raw_response_sha256=canonical_sha256({"raw_response": raw}),
            input_tokens=100,
            cached_input_tokens=40,
            output_tokens=20,
            reasoning_output_tokens=5,
            terminal_usage_event_count=1,
            exit_code=0,
            timed_out=False,
            duration_ms=17,
            external_provider_calls=0,
        )


def _verify_file_hashes() -> None:
    for relative_path, expected in EXPECTED_FILE_SHA256.items():
        actual = sha256_hex((ROOT / relative_path).read_bytes())
        if actual != expected:
            raise RuntimeError(f"S6 byte hash drift: {relative_path}")
    focused_path = ROOT / "docs/r02-d4-s6-focused-tests.json"
    focused = json.loads(focused_path.read_text(encoding="utf-8"))
    if focused.get("expected_collected_tests") != 133:
        raise RuntimeError("focused test count drift")
    for relative_path, expected in focused["test_file_sha256"].items():
        if sha256_hex((ROOT / relative_path).read_bytes()) != expected:
            raise RuntimeError(f"focused test source drift: {relative_path}")


def _protected_tree() -> tuple[int, str]:
    value = _filesystem_tree(PROTECTED_ROOT)
    if value != (EXPECTED_PROTECTED_FILE_COUNT, EXPECTED_PROTECTED_TREE_SHA256):
        raise RuntimeError("protected production artifact tree drift")
    return value


def main() -> None:
    _verify_file_hashes()
    before = _protected_tree()
    if tuple(PROTECTED_ROOT.glob("r02-d4-s6-*")):
        raise RuntimeError("a production S6 artifact root already exists")
    posthoc_path = ROOT / "docs/r02-d3-successor-provider-free-posthoc.json"
    if sha256_hex(posthoc_path.read_bytes()) != EXPECTED_D3_POSTHOC_SHA256:
        raise RuntimeError("D3 post-hoc bytes drift")
    if json.loads(posthoc_path.read_text(encoding="utf-8"))["confirmatory_result_preserved"]["verdict"] != "SUPPORTED":
        raise RuntimeError("D3 confirmatory verdict drift")

    prepared = build_provider_free_run_plan(ROOT)
    transport = VerifierFakeTransport()
    authorization = offline_fake_authorization("r02-d4-s6-verifier-fake")
    with tempfile.TemporaryDirectory(prefix="r02-d4-s6-verifier-") as directory:
        audit_root = Path(directory) / "audit"
        result = R02D4S6Runner(
            repository_root=ROOT,
            audit_root=audit_root,
            authorization=authorization,
            transport=transport,
            prepared_run=prepared,
        ).run()
        replay = replay_s6_audit_root(
            audit_root,
            repository_root=ROOT,
            expected_authorization=authorization,
            expected_plan=prepared.plan,
        )
        if canonical_sha256(replay.terminal) != canonical_sha256(result.terminal):
            raise RuntimeError("independent terminal replay mismatch")
        if replay.node_count != 3 + (R02_D4_S6_ATTEMPT_CAP * 6) + 1:
            raise RuntimeError("complete audit node count drift")
    if len(transport.calls) != R02_D4_S6_ATTEMPT_CAP:
        raise RuntimeError("fake transport call count drift")
    if any(timeout != R02_D4_S6_TIMEOUT_MS for _, _, timeout in transport.calls):
        raise RuntimeError("per-attempt timeout argument drift")
    ledger = result.terminal.final_ledger
    if ledger.status != "COMPLETE" or ledger.reserved_tokens != R02_D4_S6_TOKEN_CAP or ledger.external_provider_calls != 0 or ledger.retry_count != 0 or ledger.replacement_count != 0 or ledger.resume_count != 0 or ledger.micro_pilot_attempts != 0:
        raise RuntimeError("terminal fake-run ledger drift")
    after = _protected_tree()
    if after != before:
        raise RuntimeError("production artifact tree changed during S6 verification")
    print("PASS_S6_PROVIDER_FREE_RUNNER_AUDIT_REPLAY_REPRODUCED " f"attempts={ledger.launched_attempt_count} reserved_tokens={ledger.reserved_tokens} " f"nodes={replay.node_count} provider_calls=0 codex_exec=0 live=false")


if __name__ == "__main__":
    main()
