from __future__ import annotations

import base64
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import pytest
from pydantic import ValidationError

from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .r02_candidates import prepare_provider_free_episode
from .r02_d3_preflight import (
    R02_D3_BOOTSTRAP_DOMAIN,
    R02_D3_FEATURE_CATALOG_SHA256,
    R02_D3_OUTPUT_SCHEMA_PLACEHOLDER,
    R02D3BootstrapSeedContract,
    R02D3TransportSnapshot,
    build_preregistration,
    build_zero_call_preflight,
    capture_transport_snapshot,
    is_provider_free_local_command,
    load_frame_episode,
    render_frozen_prompt,
    render_live_argv,
    selector_output_schema,
    selector_output_schema_sha256,
    zero_call_commands,
)
from .r02_selector import build_selector_request


ROOT = Path(__file__).resolve().parents[3]
AUTHORIZATION_PATH = ROOT / "docs" / "r02-d3-provider-free-authorization.md"


def _authorization_sha256() -> str:
    return hashlib.sha256(AUTHORIZATION_PATH.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _preregistration():
    return build_preregistration(
        ROOT,
        authorization_sha256=_authorization_sha256(),
    )


class FakeZeroCallRunner:
    def __init__(self, preregistration=None) -> None:
        self.preregistration = preregistration or _preregistration()
        self.calls: list[tuple[str, ...]] = []
        self._labels = {
            argv: label
            for label, argv in zero_call_commands(self.preregistration.model_identity)
        }

    def run(self, argv: tuple[str, ...]) -> tuple[bytes, bytes, int]:
        self.calls.append(argv)
        label = self._labels.get(argv)
        if label is None:
            raise AssertionError("fake runner received a non-zero-call command")
        if label == "version":
            return b"codex-cli 0.144.1\n", b"", 0
        if label == "login_status":
            return b"", b"Logged in using ChatGPT\n", 0
        raw_files = {
            "baseline_features": "r01-b2-codex-features-baseline.raw.b64",
            "post_disable_features": "r01-b2-codex-features-post-disable.raw.b64",
            "exec_help": "r01-b2-codex-global-disable-help.raw.b64",
        }
        return base64.b64decode((ROOT / "docs" / raw_files[label]).read_bytes()), b"", 0


@lru_cache(maxsize=1)
def _transport_snapshot():
    return capture_transport_snapshot(_preregistration(), FakeZeroCallRunner())


def test_bootstrap_seed_is_domain_separated_outcome_independent_and_exact() -> None:
    seed = _preregistration().bootstrap_seed
    assert seed.domain == R02_D3_BOOTSTRAP_DOMAIN
    assert seed.digest_sha256 == (
        "319dea85b61187c07089deedb525d4d927ffc03dc7ea2026e4be8022f2df9f68"
    )
    assert seed.seed_integer_decimal == str(
        int.from_bytes(bytes.fromhex(seed.digest_sha256), "big")
    )
    altered = dict(seed.preimage)
    altered["domain"] = "R02-D3-DIFFERENT-DOMAIN"
    assert sha256_hex(canonical_json_bytes(altered)) != seed.digest_sha256
    assert seed.outcome_independent is True


def test_bootstrap_seed_contract_rejects_preimage_or_integer_tamper() -> None:
    raw = json.loads(_preregistration().bootstrap_seed.model_dump_json())
    raw["preimage"]["bootstrap_resamples"] = 9_999
    with pytest.raises(ValidationError, match="preimage drifted"):
        R02D3BootstrapSeedContract.model_validate(raw)
    raw = json.loads(_preregistration().bootstrap_seed.model_dump_json())
    raw["seed_integer_decimal"] = "1"
    with pytest.raises(ValidationError, match="seed integer mismatch"):
        R02D3BootstrapSeedContract.model_validate(raw)


def test_frozen_prompt_reproduces_d2b_safe_prompt_exactly() -> None:
    preregistration = _preregistration()
    episode = load_frame_episode(ROOT, preregistration.execution.cases[0].fixture_id)
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id="r02-d3-micro-pilot",
    )
    request = build_selector_request(preparation)
    system_prompt, user_prompt, stdin = render_frozen_prompt(
        preparation,
        preregistration,
    )
    rendered_payload = canonical_json_bytes(request.selector_payload).decode("utf-8")
    assert system_prompt == request.prompt.system_prompt
    assert user_prompt == request.prompt.user_prompt
    assert user_prompt.count(rendered_payload) == 1
    assert stdin == f"{system_prompt}\n\n{user_prompt}\n".encode("utf-8")
    assert preregistration.prompt.confidence_policy == "LOG_ONLY_NO_EXECUTION_EFFECT"


def test_output_schema_and_live_argv_are_frozen_but_never_zero_call_allowlisted(
    tmp_path,
) -> None:
    preregistration = _preregistration()
    schema_path = (tmp_path / "selector-schema.json").resolve()
    argv = render_live_argv(preregistration, schema_path)
    assert R02_D3_OUTPUT_SCHEMA_PLACEHOLDER not in argv
    assert str(schema_path) in argv
    assert "--output-schema" in argv
    assert "--json" in argv
    assert argv[-1] == "-"
    assert is_provider_free_local_command(argv, preregistration.model_identity) is False
    assert selector_output_schema_sha256() == preregistration.prompt.response_schema_sha256
    assert selector_output_schema()["additionalProperties"] is False


def test_micro_pilot_selection_covers_every_stratum_by_k_cell_without_outcomes() -> None:
    execution = _preregistration().execution
    assert tuple(
        (case.stratum, case.candidate_count, case.fixture_id, case.frame_ordinal)
        for case in execution.cases
    ) == (
        ("REPRESENTATIVE", 2, "development-0003", 3),
        ("REPRESENTATIVE", 3, "development-0009", 9),
        ("REPRESENTATIVE", 4, "development-0027", 27),
        ("CHALLENGE_HEADROOM", 3, "development-0129", 120),
        ("CHALLENGE_HEADROOM", 2, "development-0153", 122),
        ("CHALLENGE_HEADROOM", 4, "development-0171", 123),
    )
    assert execution.utility_outcomes_available_to_continuation_gate is False
    assert execution.attempted_cases_debit_full_evaluation_budget is True
    assert execution.retry_attempts_per_case == 0


def test_budget_and_stop_contract_reconcile_with_d2c() -> None:
    budget = _preregistration().budget_stop
    assert budget.micro_pilot_attempt_cap == 6
    assert budget.micro_pilot_token_cap == 6 * 32_000
    assert budget.full_provider_attempt_cap == 55
    assert budget.full_token_cap == 55 * 32_000
    assert budget.micro_pilot_selector_fallback_cap == 1
    assert budget.full_evaluation_fail_closed_attempt_cap == 5
    assert budget.unsettled_attempt_cap == 0
    assert budget.retry_attempt_cap == 0
    assert budget.breach_label == "INVALID_RUN"


def test_fake_zero_call_capture_reproduces_frozen_transport() -> None:
    preregistration = _preregistration()
    runner = FakeZeroCallRunner(preregistration)
    snapshot = capture_transport_snapshot(preregistration, runner)
    assert len(runner.calls) == 5
    assert all(
        is_provider_free_local_command(argv, preregistration.model_identity)
        for argv in runner.calls
    )
    assert snapshot.feature_catalog_sha256 == R02_D3_FEATURE_CATALOG_SHA256
    assert snapshot.post_disable_active_features == (
        "resize_all_images",
        "terminal_resize_reflow",
        "tool_search_always_defer_mcp_tools",
        "tui_app_server",
    )
    assert snapshot.external_provider_calls == 0
    assert snapshot.provider_request_commands_executed == 0


def test_transport_snapshot_rejects_capture_tamper() -> None:
    raw = json.loads(_transport_snapshot().model_dump_json())
    raw["captures"][0]["stdout_base64"] = base64.b64encode(b"wrong\n").decode("ascii")
    with pytest.raises(ValidationError, match="stdout hash mismatch"):
        R02D3TransportSnapshot.model_validate_json(json.dumps(raw))


def test_zero_call_preflight_has_no_execution_authority() -> None:
    preregistration = _preregistration()
    preflight = build_zero_call_preflight(ROOT, preregistration, _transport_snapshot())
    assert preflight.preflight_id == f"r02-d3-preflight-{canonical_sha256(preregistration)[:12]}"
    assert preflight.status == "READY_FOR_INDEPENDENT_REVIEW_PROVIDER_CALLS_ZERO"
    assert preflight.zero_call_preflight_finalization == "CANDIDATE_REVIEW_PENDING"
    assert preflight.d3_live_authorization == "NOT_AUTHORIZED"
    assert preflight.provider_calls == 0
    assert preflight.live_execution is False
    assert preflight.micro_pilot_executed is False


def test_preregistration_rejects_wrong_authorization_shape() -> None:
    with pytest.raises(ValidationError):
        build_preregistration(
            ROOT,
            authorization_sha256="not-a-sha",
        )
