"""Reproduce the R02 D4-S7 provider-free production-gate draft."""

from __future__ import annotations

import json
from pathlib import Path

from v2.research.overlay.canonical import (
    canonical_json_bytes,
    canonical_sha256,
    sha256_hex,
)
from v2.research.overlay.r02_d3_preflight import R02D3Preregistration
from v2.research.overlay.r02_d3_successor_contracts import (
    selector_output_schema,
    selector_output_schema_sha256,
)
from v2.research.overlay.r02_d4_s6_contracts import (
    R02_D4_S6_ATTEMPT_CAP,
    R02_D4_S6_FAIL_CLOSED_CAP,
    R02_D4_S6_RUN_PLAN_SHA256,
    R02_D4_S6_TIMEOUT_MS,
    R02_D4_S6_TOKEN_CAP,
    R02_D4_S6_TOKEN_RESERVE,
)
from v2.research.overlay.r02_d4_s6_runner import build_provider_free_run_plan
from v2.research.overlay.r02_d4_s7_contracts import (
    R02_D4_S7_BASE_COMMIT,
    R02_D4_S7_D3_PREREGISTRATION_SHA256,
    R02_D4_S7_EXECUTABLE_SHA256,
    R02_D4_S7_MODEL,
    R02_D4_S7_PREREGISTERED_RESPONSE_SCHEMA_SHA256,
    R02_D4_S7_RESPONSE_SCHEMA_SHA256,
    R02_D4_S7_S5_IDENTITY_SNAPSHOT_SHA256,
)
from v2.research.overlay.r02_d4_s7_entrypoint import _verify_s7_contract

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SHA256 = "c2b4b729e77690c3f02d28de503d4172e038d19b7230c954b8f2e4b167deb2b1"
FOCUSED_TESTS_SHA256 = "31a2ae9421bb0b2ceac20e0906248ec6724f051df9164408958d8eb1973f3406"


def _read_object(relative_path: str) -> dict[str, object]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {relative_path}")
    return value


def verify() -> dict[str, object]:
    contract_path = ROOT / "docs/r02-d4-s7-production-gate-contract.json"
    focused_path = ROOT / "docs/r02-d4-s7-focused-tests.json"
    if sha256_hex(contract_path.read_bytes()) != CONTRACT_SHA256:
        raise RuntimeError("S7 production-gate contract byte drift")
    if sha256_hex(focused_path.read_bytes()) != FOCUSED_TESTS_SHA256:
        raise RuntimeError("S7 focused-test manifest byte drift")
    _verify_s7_contract(ROOT, CONTRACT_SHA256)
    contract = _read_object("docs/r02-d4-s7-production-gate-contract.json")
    if contract.get("accepted_s6_commit") != R02_D4_S7_BASE_COMMIT:
        raise RuntimeError("accepted S6 commit drift")
    focused = _read_object("docs/r02-d4-s7-focused-tests.json")
    if focused.get("expected_collected_tests") != 150:
        raise RuntimeError("focused-test count drift")
    file_hashes = focused.get("test_file_sha256")
    if not isinstance(file_hashes, dict):
        raise RuntimeError("focused-test hashes are missing")
    for relative_path, expected in file_hashes.items():
        if not isinstance(relative_path, str) or not isinstance(expected, str):
            raise RuntimeError("focused-test hash entry is invalid")
        if sha256_hex((ROOT / relative_path).read_bytes()) != expected:
            raise RuntimeError(f"focused-test byte drift: {relative_path}")
    prereg_path = ROOT / "docs/r02-d3-preregistration.json"
    if sha256_hex(prereg_path.read_bytes()) != R02_D4_S7_D3_PREREGISTRATION_SHA256:
        raise RuntimeError("D3 preregistration byte drift")
    prereg = R02D3Preregistration.model_validate_json(prereg_path.read_bytes())
    identity = prereg.model_identity
    if identity.executable_sha256 != R02_D4_S7_EXECUTABLE_SHA256:
        raise RuntimeError("D3 executable identity drift")
    if identity.requested_model_id != R02_D4_S7_MODEL:
        raise RuntimeError("D3 model identity drift")
    if identity.response_schema_sha256 != R02_D4_S7_PREREGISTERED_RESPONSE_SCHEMA_SHA256:
        raise RuntimeError("D3 preregistered response-schema identity drift")
    schema_path = ROOT / "docs/r02-d4-s7-selector-output-schema.json"
    if schema_path.read_bytes() != canonical_json_bytes(selector_output_schema()):
        raise RuntimeError("S7 successor output-schema bytes drift")
    if selector_output_schema_sha256() != R02_D4_S7_RESPONSE_SCHEMA_SHA256:
        raise RuntimeError("S7 successor output-schema identity drift")
    snapshot_path = ROOT / "docs/r02-d4-s5-execution-identity-snapshot.json"
    if sha256_hex(snapshot_path.read_bytes()) != R02_D4_S7_S5_IDENTITY_SNAPSHOT_SHA256:
        raise RuntimeError("S5 identity snapshot byte drift")
    snapshot = _read_object("docs/r02-d4-s5-execution-identity-snapshot.json")
    if snapshot.get("provider_calls") != 0 or snapshot.get("codex_exec_invocations") != 0:
        raise RuntimeError("sealed identity snapshot is not provider-free")
    plan = build_provider_free_run_plan(ROOT)
    if canonical_sha256(plan.plan) != R02_D4_S6_RUN_PLAN_SHA256:
        raise RuntimeError("S6 prepared-plan drift")
    if len(plan.attempts) != R02_D4_S6_ATTEMPT_CAP:
        raise RuntimeError("S6 attempt-count drift")
    if list((ROOT / "docs").glob("r02-d4-s7-live-auth*.json")):
        raise RuntimeError("a forbidden S7 LIVE authorization artifact exists")
    protected = ROOT / ".research_artifacts"
    forbidden_roots = [item for item in protected.glob("r02-d4-s7-transport-r02-d4-s7-*") if item.exists()]
    if forbidden_roots:
        raise RuntimeError("an S7 production transport root was materialized")
    return {
        "status": "PASS_S7_PROVIDER_FREE_PRODUCTION_GATE_REPRODUCED",
        "attempt_cap": R02_D4_S6_ATTEMPT_CAP,
        "token_reserve": R02_D4_S6_TOKEN_RESERVE,
        "aggregate_token_cap": R02_D4_S6_TOKEN_CAP,
        "timeout_ms": R02_D4_S6_TIMEOUT_MS,
        "fail_closed_cap": R02_D4_S6_FAIL_CLOSED_CAP,
        "focused_test_count": 150,
        "provider_calls": 0,
        "codex_exec_invocations": 0,
        "production_root_materializations": 0,
    }


if __name__ == "__main__":
    result = verify()
    print(
        result["status"],
        f"attempts={result['attempt_cap']}",
        f"tokens={result['aggregate_token_cap']}",
        f"timeout_ms={result['timeout_ms']}",
        f"tests={result['focused_test_count']}",
    )
