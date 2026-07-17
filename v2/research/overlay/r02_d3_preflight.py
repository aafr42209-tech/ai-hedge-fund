"""Provider-free R02 D3 preregistration and zero-call preflight candidate."""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field, field_validator, model_validator

from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .codex_preflight import parse_codex_feature_catalog
from .contracts import (
    StrictModel,
    SyntheticEpisode,
    normalize_artifact_relative_path,
)
from .r02_audit import R02AppendOnlyArtifactStore, _ensure_r02_artifact_root
from .r02_contracts import R02_CONTRACT_ID, R02ProviderFreePreparation
from .r02_d3_contracts import (
    R01_FILE_COUNT,
    R01_MODEL_COMMAND_SPEC_PATH,
    R01_MODEL_COMMAND_SPEC_SHA256,
    R01_TREE_SHA256,
    R02_D1_FREEZE_SHA256,
    R02_D1_MANIFEST_SHA256,
    R02_D2C_FRAME_ID,
    R02_D2C_FRAME_MANIFEST_SHA256,
    R02_D2C_FRAME_SEAL_SHA256,
    R02_D2C_FRAME_TREE_SHA256,
    R02_D2C_FREEZE_MANIFEST_SHA256,
    R02_D2C_STATISTICAL_FREEZE_SHA256,
    R02_D3_BASE_COMMIT,
    R02_D3_BOOTSTRAP_DOMAIN,
    R02_D3_CODEX_CLI_VERSION,
    R02_D3_FEATURE_CATALOG_SHA256,
    R02_D3_FEATURE_DEFINITION_SHA256,
    R02_D3_LOCAL_COMMAND_TIMEOUT_SECONDS,
    R02_D3_NODE_TYPES,
    R02_D3_OUTPUT_SCHEMA_PLACEHOLDER,
    R02_D3_PAYLOAD_PLACEHOLDER,
    R02_D3_POST_DISABLE_ACTIVE_ALLOWLIST,
    R02_D3_PROTECTED_PATHS,
    R02_D3_PROVIDER,
    R02_D3_REASON_CODES,
    R02_D3_REQUESTED_MODEL_ID,
    R02_D3_SYSTEM_PROMPT,
    R02_D3_USER_PROMPT_TEMPLATE,
    R02D3BudgetStopContract,
    R02D3ExecutionContract,
    R02D3LocalCommandCapture,
    R02D3MicroPilotCase,
    R02D3PersistedPreflight,
    R02D3PreflightAuditGraph,
    R02D3TransportSnapshot,
    R02D3ZeroCallAssertions,
    R02D3ZeroCallPreflight,
    build_zero_call_commands,
    selector_output_schema,
    selector_output_schema_sha256,
)
from .r02_selector import build_selector_request


class R02D3PreflightError(RuntimeError):
    pass


class R02D3BootstrapSeedContract(StrictModel):
    schema_version: Literal["r02-d3-bootstrap-seed-contract-v1"] = (
        "r02-d3-bootstrap-seed-contract-v1"
    )
    domain: Literal[R02_D3_BOOTSTRAP_DOMAIN] = R02_D3_BOOTSTRAP_DOMAIN
    algorithm: Literal["SHA256_CANONICAL_JSON_FULL_DIGEST_BIG_ENDIAN_INTEGER"] = (
        "SHA256_CANONICAL_JSON_FULL_DIGEST_BIG_ENDIAN_INTEGER"
    )
    bit_generator: Literal["PCG64"] = "PCG64"
    bootstrap_resamples: Literal[10_000] = 10_000
    preimage: dict[str, str | int]
    digest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seed_integer_decimal: str = Field(pattern=r"^[0-9]+$")
    outcome_independent: Literal[True] = True

    @model_validator(mode="after")
    def validate_seed(self) -> "R02D3BootstrapSeedContract":
        if self.preimage != _bootstrap_seed_preimage():
            raise ValueError("evaluation bootstrap seed preimage drifted")
        digest = sha256_hex(canonical_json_bytes(self.preimage))
        if self.digest_sha256 != digest:
            raise ValueError("evaluation bootstrap seed digest mismatch")
        if self.seed_integer_decimal != str(int.from_bytes(bytes.fromhex(digest), "big")):
            raise ValueError("evaluation bootstrap seed integer mismatch")
        return self


class R02D3PromptContract(StrictModel):
    schema_version: Literal["r02-d3-selector-prompt-contract-v1"] = (
        "r02-d3-selector-prompt-contract-v1"
    )
    status: Literal["FREEZE_CANDIDATE_REVIEW_PENDING"] = (
        "FREEZE_CANDIDATE_REVIEW_PENDING"
    )
    input_contract: Literal["SELECTOR_SAFE_PAYLOAD_ONLY"] = (
        "SELECTOR_SAFE_PAYLOAD_ONLY"
    )
    system_prompt: Literal[R02_D3_SYSTEM_PROMPT] = R02_D3_SYSTEM_PROMPT
    user_prompt_template: Literal[R02_D3_USER_PROMPT_TEMPLATE] = (
        R02_D3_USER_PROMPT_TEMPLATE
    )
    payload_placeholder: Literal[R02_D3_PAYLOAD_PLACEHOLDER] = (
        R02_D3_PAYLOAD_PLACEHOLDER
    )
    system_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    user_prompt_template_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stdin_template_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    response_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    allowed_reason_codes: tuple[str, ...] = R02_D3_REASON_CODES
    confidence_policy: Literal["LOG_ONLY_NO_EXECUTION_EFFECT"] = (
        "LOG_ONLY_NO_EXECUTION_EFFECT"
    )

    @model_validator(mode="after")
    def validate_prompt(self) -> "R02D3PromptContract":
        if self.user_prompt_template.count(self.payload_placeholder) != 1:
            raise ValueError("selector payload placeholder must occur exactly once")
        if self.allowed_reason_codes != R02_D3_REASON_CODES:
            raise ValueError("selector reason-code enum drifted")
        if self.system_prompt_sha256 != sha256_hex(self.system_prompt.encode("utf-8")):
            raise ValueError("system prompt hash mismatch")
        if self.user_prompt_template_sha256 != sha256_hex(
            self.user_prompt_template.encode("utf-8")
        ):
            raise ValueError("user prompt template hash mismatch")
        stdin_template = f"{self.system_prompt}\n\n{self.user_prompt_template}\n"
        if self.stdin_template_sha256 != sha256_hex(stdin_template.encode("utf-8")):
            raise ValueError("stdin template hash mismatch")
        if self.response_schema_sha256 != selector_output_schema_sha256():
            raise ValueError("selector output schema hash mismatch")
        return self


class R02D3ModelIdentityContract(StrictModel):
    schema_version: Literal["r02-d3-model-identity-contract-v1"] = (
        "r02-d3-model-identity-contract-v1"
    )
    provider: Literal[R02_D3_PROVIDER] = R02_D3_PROVIDER
    requested_model_id: Literal[R02_D3_REQUESTED_MODEL_ID] = R02_D3_REQUESTED_MODEL_ID
    selection_basis: Literal[
        "SEALED_R01_CONTINUITY_NOT_SELECTED_ON_R02_OUTCOMES"
    ] = "SEALED_R01_CONTINUITY_NOT_SELECTED_ON_R02_OUTCOMES"
    r01_command_spec_path: Literal[R01_MODEL_COMMAND_SPEC_PATH] = (
        R01_MODEL_COMMAND_SPEC_PATH
    )
    r01_command_spec_sha256: Literal[R01_MODEL_COMMAND_SPEC_SHA256] = (
        R01_MODEL_COMMAND_SPEC_SHA256
    )
    transport: Literal["codex-cli-jsonl-stdin"] = "codex-cli-jsonl-stdin"
    codex_cli_version: Literal[R02_D3_CODEX_CLI_VERSION] = R02_D3_CODEX_CLI_VERSION
    executable_path: str = Field(min_length=1)
    executable_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    feature_catalog_sha256: Literal[R02_D3_FEATURE_CATALOG_SHA256] = (
        R02_D3_FEATURE_CATALOG_SHA256
    )
    feature_definition_sha256: Literal[R02_D3_FEATURE_DEFINITION_SHA256] = (
        R02_D3_FEATURE_DEFINITION_SHA256
    )
    disabled_features: tuple[str, ...] = Field(min_length=1)
    allowed_post_disable_active_features: tuple[str, ...] = (
        R02_D3_POST_DISABLE_ACTIVE_ALLOWLIST
    )
    reasoning_effort: Literal["high"] = "high"
    sandbox: Literal["read-only"] = "read-only"
    web_search: Literal[False] = False
    ephemeral: Literal[True] = True
    ignore_user_config: Literal[True] = True
    ignore_rules: Literal[True] = True
    strict_config: Literal[True] = True
    response_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    live_argv_template: tuple[str, ...]
    provider_model_echo_policy: Literal[
        "EXACT_IF_PRESENT_ABSENCE_RECORDED_MISMATCH_STOP"
    ] = "EXACT_IF_PRESENT_ABSENCE_RECORDED_MISMATCH_STOP"
    temperature_override: None = None

    @field_validator("disabled_features")
    @classmethod
    def validate_disabled_features(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if tuple(sorted(value)) != value or len(value) != len(set(value)):
            raise ValueError("disabled feature names must be unique and sorted")
        return value

    @model_validator(mode="after")
    def validate_model_identity(self) -> "R02D3ModelIdentityContract":
        if self.allowed_post_disable_active_features != R02_D3_POST_DISABLE_ACTIVE_ALLOWLIST:
            raise ValueError("post-disable active-feature allowlist drifted")
        if self.response_schema_sha256 != selector_output_schema_sha256():
            raise ValueError("model contract response schema hash mismatch")
        expected = _live_argv_template(
            self.executable_path,
            self.disabled_features,
            self.requested_model_id,
        )
        if self.live_argv_template != expected:
            raise ValueError("live argv template drifted")
        return self


class R02D3Preregistration(StrictModel):
    schema_version: Literal["r02-d3-preregistration-v1"] = (
        "r02-d3-preregistration-v1"
    )
    status: Literal["FREEZE_CANDIDATE_REVIEW_PENDING"] = (
        "FREEZE_CANDIDATE_REVIEW_PENDING"
    )
    contract_id: Literal[R02_CONTRACT_ID] = R02_CONTRACT_ID
    accepted_d2c_commit: Literal[R02_D3_BASE_COMMIT] = R02_D3_BASE_COMMIT
    authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    r02_d1_freeze_sha256: Literal[R02_D1_FREEZE_SHA256] = R02_D1_FREEZE_SHA256
    r02_d1_manifest_sha256: Literal[R02_D1_MANIFEST_SHA256] = R02_D1_MANIFEST_SHA256
    d2c_frame_manifest_sha256: Literal[R02_D2C_FRAME_MANIFEST_SHA256] = (
        R02_D2C_FRAME_MANIFEST_SHA256
    )
    d2c_frame_seal_sha256: Literal[R02_D2C_FRAME_SEAL_SHA256] = (
        R02_D2C_FRAME_SEAL_SHA256
    )
    d2c_statistical_freeze_sha256: Literal[R02_D2C_STATISTICAL_FREEZE_SHA256] = (
        R02_D2C_STATISTICAL_FREEZE_SHA256
    )
    d2c_freeze_manifest_sha256: Literal[R02_D2C_FREEZE_MANIFEST_SHA256] = (
        R02_D2C_FREEZE_MANIFEST_SHA256
    )
    d2c_frame_id: Literal[R02_D2C_FRAME_ID] = R02_D2C_FRAME_ID
    d2c_frame_tree_sha256: Literal[R02_D2C_FRAME_TREE_SHA256] = (
        R02_D2C_FRAME_TREE_SHA256
    )
    r01_file_count: Literal[R01_FILE_COUNT] = R01_FILE_COUNT
    r01_tree_sha256: Literal[R01_TREE_SHA256] = R01_TREE_SHA256
    contracts_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preflight_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    replay_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bootstrap_seed: R02D3BootstrapSeedContract
    prompt: R02D3PromptContract
    model_identity: R02D3ModelIdentityContract
    execution: R02D3ExecutionContract
    budget_stop: R02D3BudgetStopContract
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    micro_pilot_executed: Literal[False] = False
    d3_authorized: Literal[False] = False


class LocalCommandRunner(Protocol):
    def run(self, argv: tuple[str, ...]) -> tuple[bytes, bytes, int]:
        ...


class SubprocessZeroCallRunner:
    def __init__(self, model_identity: R02D3ModelIdentityContract) -> None:
        self._model_identity = model_identity

    def run(self, argv: tuple[str, ...]) -> tuple[bytes, bytes, int]:
        if not is_provider_free_local_command(argv, self._model_identity):
            raise R02D3PreflightError("command is outside the D3 zero-call allowlist")
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                check=False,
                timeout=R02_D3_LOCAL_COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise R02D3PreflightError("zero-call local command timed out") from exc
        return completed.stdout, completed.stderr, completed.returncode


def _bootstrap_seed_preimage() -> dict[str, str | int]:
    return {
        "accepted_d2c_commit": R02_D3_BASE_COMMIT,
        "bit_generator": "PCG64",
        "bootstrap_resamples": 10_000,
        "contract_id": R02_CONTRACT_ID,
        "d2c_frame_id": R02_D2C_FRAME_ID,
        "d2c_frame_manifest_sha256": R02_D2C_FRAME_MANIFEST_SHA256,
        "d2c_frame_tree_sha256": R02_D2C_FRAME_TREE_SHA256,
        "d2c_statistical_freeze_sha256": R02_D2C_STATISTICAL_FREEZE_SHA256,
        "domain": R02_D3_BOOTSTRAP_DOMAIN,
        "primary_estimand": (
            "round_half_even(3/4*mean(D_REPRESENTATIVE)+"
            "1/4*mean(D_CHALLENGE))"
        ),
    }


def build_bootstrap_seed_contract() -> R02D3BootstrapSeedContract:
    preimage = _bootstrap_seed_preimage()
    digest = sha256_hex(canonical_json_bytes(preimage))
    return R02D3BootstrapSeedContract(
        preimage=preimage,
        digest_sha256=digest,
        seed_integer_decimal=str(int.from_bytes(bytes.fromhex(digest), "big")),
    )


def build_prompt_contract() -> R02D3PromptContract:
    stdin_template = f"{R02_D3_SYSTEM_PROMPT}\n\n{R02_D3_USER_PROMPT_TEMPLATE}\n"
    return R02D3PromptContract(
        system_prompt_sha256=sha256_hex(R02_D3_SYSTEM_PROMPT.encode("utf-8")),
        user_prompt_template_sha256=sha256_hex(
            R02_D3_USER_PROMPT_TEMPLATE.encode("utf-8")
        ),
        stdin_template_sha256=sha256_hex(stdin_template.encode("utf-8")),
        response_schema_sha256=selector_output_schema_sha256(),
    )


def _live_argv_template(
    executable_path: str,
    disabled_features: tuple[str, ...],
    requested_model_id: str,
) -> tuple[str, ...]:
    argv: list[str] = [executable_path]
    for feature in disabled_features:
        argv.extend(("--disable", feature))
    argv.extend(
        (
            "exec",
            "--model",
            requested_model_id,
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--strict-config",
            "--config",
            "model_reasoning_effort=high",
            "--config",
            "tools.web_search=false",
            "--output-schema",
            R02_D3_OUTPUT_SCHEMA_PLACEHOLDER,
            "--json",
            "-",
        )
    )
    return tuple(argv)


def render_live_argv(
    preregistration: R02D3Preregistration,
    output_schema_path: str | Path,
) -> tuple[str, ...]:
    path = Path(output_schema_path)
    if not path.is_absolute():
        raise ValueError("selector output schema path must be absolute")
    return tuple(
        str(path) if value == R02_D3_OUTPUT_SCHEMA_PLACEHOLDER else value
        for value in preregistration.model_identity.live_argv_template
    )


def render_frozen_prompt(
    preparation: R02ProviderFreePreparation,
    preregistration: R02D3Preregistration,
) -> tuple[str, str, bytes]:
    request = build_selector_request(preparation)
    payload_json = canonical_json_bytes(request.selector_payload).decode("utf-8")
    user_prompt = preregistration.prompt.user_prompt_template.replace(
        preregistration.prompt.payload_placeholder,
        payload_json,
    )
    if request.prompt.system_prompt != preregistration.prompt.system_prompt:
        raise R02D3PreflightError("frozen system prompt differs from D2b")
    if request.prompt.user_prompt != user_prompt:
        raise R02D3PreflightError("frozen user prompt differs from D2b")
    stdin = f"{preregistration.prompt.system_prompt}\n\n{user_prompt}\n".encode("utf-8")
    return preregistration.prompt.system_prompt, user_prompt, stdin


def _sha256_file(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def _filesystem_tree(root: Path) -> tuple[int, str]:
    entries: list[tuple[str, int, str]] = []
    for value in (path for path in root.rglob("*") if path.is_file()):
        payload = value.read_bytes()
        entries.append(
            (
                value.relative_to(root).as_posix(),
                len(payload),
                sha256_hex(payload),
            )
        )
    records = [
        f"{relative_path}\0{size_bytes}\0{digest}"
        for relative_path, size_bytes, digest in sorted(entries)
    ]
    return len(records), sha256_hex("\n".join(records).encode("utf-8"))


def resolve_codex_executable() -> Path:
    launcher = shutil.which("codex")
    if launcher is None:
        raise R02D3PreflightError("codex executable is not on PATH")
    package_root = Path(launcher).resolve().parent / "node_modules" / "@openai" / "codex"
    matches = tuple(
        path.resolve()
        for path in package_root.rglob("codex.exe")
        if path.is_file()
    )
    if len(matches) != 1:
        raise R02D3PreflightError("expected exactly one npm Codex native executable")
    return matches[0]


def _require_hash(root: Path, relative_path: str, expected: str) -> None:
    actual = _sha256_file(root / relative_path)
    if actual != expected:
        raise R02D3PreflightError(f"hash mismatch: {relative_path}")


def _git_output(root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ("git", "-C", str(root), *args),
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout.decode("utf-8", errors="strict").strip()
    except (subprocess.SubprocessError, UnicodeDecodeError) as exc:
        raise R02D3PreflightError(f"local git command failed: {' '.join(args)}") from exc


def _accepted_base_is_ancestor(root: Path) -> bool:
    completed = subprocess.run(
        ("git", "-C", str(root), "merge-base", "--is-ancestor", R02_D3_BASE_COMMIT, "HEAD"),
        capture_output=True,
        check=False,
        timeout=30,
    )
    return completed.returncode == 0


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D3PreflightError(f"expected JSON object: {path}")
    return value


def _build_execution_contract(frame: dict[str, object]) -> R02D3ExecutionContract:
    raw_cases = frame.get("cases")
    if not isinstance(raw_cases, list):
        raise R02D3PreflightError("D2c frame cases missing")
    selected: list[R02D3MicroPilotCase] = []
    for stratum in ("REPRESENTATIVE", "CHALLENGE_HEADROOM"):
        for candidate_count in (2, 3, 4):
            candidates = [
                case
                for case in raw_cases
                if isinstance(case, dict)
                and case.get("stratum") == stratum
                and case.get("candidate_count") == candidate_count
                and case.get("triggered") is True
            ]
            if not candidates:
                raise R02D3PreflightError("triggered micro-pilot stratum-by-K cell is empty")
            chosen = min(candidates, key=lambda case: str(case.get("fixture_id")))
            selected.append(
                R02D3MicroPilotCase(
                    stratum=stratum,
                    candidate_count=candidate_count,
                    fixture_id=str(chosen["fixture_id"]),
                    frame_ordinal=int(chosen["frame_ordinal"]),
                )
            )
    selected.sort(key=lambda case: case.frame_ordinal)
    return R02D3ExecutionContract(cases=tuple(selected))


def _build_model_identity(
    root: Path,
    executable: Path,
) -> R02D3ModelIdentityContract:
    r01_command = _load_json(root / R01_MODEL_COMMAND_SPEC_PATH)
    if r01_command.get("model_id") != R02_D3_REQUESTED_MODEL_ID:
        raise R02D3PreflightError("sealed R01 model identity does not match D3 request")
    capture = _load_json(root / "docs" / "r01-b2-zero-call-capture.json")
    disabled = capture.get("disabled_features")
    if not isinstance(disabled, list) or not all(isinstance(value, str) for value in disabled):
        raise R02D3PreflightError("R01 zero-call disabled-feature catalog missing")
    disabled_tuple = tuple(sorted(disabled))
    return R02D3ModelIdentityContract(
        executable_path=str(executable.resolve()),
        executable_sha256=_sha256_file(executable),
        disabled_features=disabled_tuple,
        response_schema_sha256=selector_output_schema_sha256(),
        live_argv_template=_live_argv_template(
            str(executable.resolve()),
            disabled_tuple,
            R02_D3_REQUESTED_MODEL_ID,
        ),
    )


def build_preregistration(
    repository_root: str | Path,
    *,
    authorization_sha256: str,
    executable_path: str | Path | None = None,
) -> R02D3Preregistration:
    root = Path(repository_root).resolve()
    if not _accepted_base_is_ancestor(root):
        raise R02D3PreflightError("accepted D2c commit is not an ancestor of HEAD")
    expected_hashes = {
        "docs/r02-d1-candidate-trigger-freeze.json": R02_D1_FREEZE_SHA256,
        "docs/r02-d1-freeze-manifest.json": R02_D1_MANIFEST_SHA256,
        "docs/r02-d2c-frame-manifest.json": R02_D2C_FRAME_MANIFEST_SHA256,
        "docs/r02-d2c-frame-seal.json": R02_D2C_FRAME_SEAL_SHA256,
        "docs/r02-d2c-statistical-freeze.json": R02_D2C_STATISTICAL_FREEZE_SHA256,
        "docs/r02-d2c-freeze-manifest.json": R02_D2C_FREEZE_MANIFEST_SHA256,
        R01_MODEL_COMMAND_SPEC_PATH: R01_MODEL_COMMAND_SPEC_SHA256,
    }
    for relative_path, expected in expected_hashes.items():
        _require_hash(root, relative_path, expected)
    d2c_frame = _load_json(root / "docs" / "r02-d2c-frame-manifest.json")
    d2c_statistics = _load_json(root / "docs" / "r02-d2c-statistical-freeze.json")
    if d2c_frame.get("frame_id") != R02_D2C_FRAME_ID:
        raise R02D3PreflightError("D2c frame identity mismatch")
    if d2c_statistics.get("evaluation_bootstrap_resamples") != 10_000:
        raise R02D3PreflightError("D2c bootstrap draw count mismatch")
    if d2c_statistics.get("bit_generator") != "PCG64":
        raise R02D3PreflightError("D2c bit generator mismatch")
    frame_root = root / ".research_artifacts" / R02_D2C_FRAME_ID
    if _filesystem_tree(frame_root) != (162, R02_D2C_FRAME_TREE_SHA256):
        raise R02D3PreflightError("sealed D2c frame tree mismatch")
    r01_root = root / ".research_artifacts" / "r01-b3-1f65106"
    if _filesystem_tree(r01_root) != (R01_FILE_COUNT, R01_TREE_SHA256):
        raise R02D3PreflightError("sealed R01 tree mismatch")
    executable = (
        Path(executable_path).resolve()
        if executable_path is not None
        else resolve_codex_executable()
    )
    if not executable.is_file():
        raise R02D3PreflightError("Codex executable does not exist")
    source_path = Path(__file__).resolve()
    contracts_path = source_path.with_name("r02_d3_contracts.py")
    replay_path = source_path.with_name("r02_d3_replay.py")
    if not contracts_path.is_file() or not replay_path.is_file():
        raise R02D3PreflightError("D3 contract or replay source is missing")
    return R02D3Preregistration(
        authorization_sha256=authorization_sha256,
        contracts_source_sha256=_sha256_file(contracts_path),
        preflight_source_sha256=_sha256_file(source_path),
        replay_source_sha256=_sha256_file(replay_path),
        bootstrap_seed=build_bootstrap_seed_contract(),
        prompt=build_prompt_contract(),
        model_identity=_build_model_identity(root, executable),
        execution=_build_execution_contract(d2c_frame),
        budget_stop=R02D3BudgetStopContract(),
    )


def zero_call_commands(
    model_identity: R02D3ModelIdentityContract,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return build_zero_call_commands(
        model_identity.executable_path,
        model_identity.disabled_features,
    )


def is_provider_free_local_command(
    argv: tuple[str, ...],
    model_identity: R02D3ModelIdentityContract,
) -> bool:
    return argv in {command for _label, command in zero_call_commands(model_identity)}


def _capture(
    label: str,
    argv: tuple[str, ...],
    runner: LocalCommandRunner,
) -> R02D3LocalCommandCapture:
    stdout, stderr, exit_code = runner.run(argv)
    if exit_code != 0:
        raise R02D3PreflightError(f"zero-call command failed: {label}")
    return R02D3LocalCommandCapture(
        label=label,
        argv=argv,
        stdout_base64=base64.b64encode(stdout).decode("ascii"),
        stderr_base64=base64.b64encode(stderr).decode("ascii"),
        stdout_sha256=sha256_hex(stdout),
        stderr_sha256=sha256_hex(stderr),
        exit_code=0,
    )


def capture_transport_snapshot(
    preregistration: R02D3Preregistration,
    runner: LocalCommandRunner,
) -> R02D3TransportSnapshot:
    captures = tuple(
        _capture(label, argv, runner)
        for label, argv in zero_call_commands(preregistration.model_identity)
    )
    by_label = {capture.label: capture for capture in captures}
    baseline = parse_codex_feature_catalog(
        by_label["baseline_features"].stdout_bytes(),
        expected_count=92,
    )
    post_disable = parse_codex_feature_catalog(
        by_label["post_disable_features"].stdout_bytes(),
        expected_count=92,
    )
    return R02D3TransportSnapshot(
        preregistration_sha256=canonical_sha256(preregistration),
        executable_path=preregistration.model_identity.executable_path,
        executable_sha256=preregistration.model_identity.executable_sha256,
        disabled_features=tuple(entry.name for entry in baseline),
        post_disable_active_features=tuple(
            entry.name for entry in post_disable if entry.enabled
        ),
        captures=captures,
    )


def _protected_diff_empty(root: Path) -> bool:
    return not _git_output(root, "diff", "--name-only", "HEAD", "--", *R02_D3_PROTECTED_PATHS)


def build_zero_call_preflight(
    repository_root: str | Path,
    preregistration: R02D3Preregistration,
    transport_snapshot: R02D3TransportSnapshot,
) -> R02D3ZeroCallPreflight:
    root = Path(repository_root).resolve()
    if transport_snapshot.preregistration_sha256 != canonical_sha256(preregistration):
        raise R02D3PreflightError("transport snapshot preregistration anchor mismatch")
    if transport_snapshot.executable_sha256 != _sha256_file(
        Path(preregistration.model_identity.executable_path)
    ):
        raise R02D3PreflightError("Codex executable bytes drifted after capture")
    if not _protected_diff_empty(root):
        raise R02D3PreflightError("protected D1/D2c tracked paths have changed")
    assertions = R02D3ZeroCallAssertions()
    preregistration_sha256 = canonical_sha256(preregistration)
    return R02D3ZeroCallPreflight(
        preflight_id=f"r02-d3-preflight-{preregistration_sha256[:12]}",
        preregistration_sha256=preregistration_sha256,
        transport_snapshot_sha256=canonical_sha256(transport_snapshot),
        selector_output_schema_sha256=selector_output_schema_sha256(),
        assertions=assertions,
    )


def persist_zero_call_preflight(
    store: R02AppendOnlyArtifactStore,
    prefix: str,
    preregistration: R02D3Preregistration,
    transport_snapshot: R02D3TransportSnapshot,
    preflight: R02D3ZeroCallPreflight,
) -> R02D3PersistedPreflight:
    _ensure_r02_artifact_root(store)
    normalized_prefix = normalize_artifact_relative_path(prefix).rstrip("/")
    if preflight.preregistration_sha256 != canonical_sha256(preregistration):
        raise ValueError("preflight preregistration anchor mismatch")
    if preflight.transport_snapshot_sha256 != canonical_sha256(transport_snapshot):
        raise ValueError("preflight transport anchor mismatch")
    nodes = (
        store.write_json(f"{normalized_prefix}/preregistration.json", preregistration),
        store.write_json(
            f"{normalized_prefix}/selector_output_schema.json",
            selector_output_schema(),
        ),
        store.write_json(
            f"{normalized_prefix}/transport_snapshot.json",
            transport_snapshot,
        ),
        store.write_json(
            f"{normalized_prefix}/zero_call_assertions.json",
            preflight.assertions,
        ),
        store.write_json(f"{normalized_prefix}/preflight.json", preflight),
    )
    graph = R02D3PreflightAuditGraph(
        preflight_id=preflight.preflight_id,
        node_types=R02_D3_NODE_TYPES,
        nodes=nodes,
    )
    graph_ref = store.write_json(f"{normalized_prefix}/audit_graph.json", graph)
    return R02D3PersistedPreflight(
        preflight=nodes[-1],
        audit_graph=graph_ref,
    )


def load_frame_episode(
    repository_root: str | Path,
    fixture_id: str,
) -> SyntheticEpisode:
    root = Path(repository_root).resolve()
    frame = _load_json(root / "docs" / "r02-d2c-frame-manifest.json")
    cases = frame.get("cases")
    if not isinstance(cases, list):
        raise R02D3PreflightError("D2c frame cases missing")
    matches = [case for case in cases if isinstance(case, dict) and case.get("fixture_id") == fixture_id]
    if len(matches) != 1:
        raise R02D3PreflightError("fixture ID is not unique in D2c frame")
    artifact = matches[0].get("fixture_artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("relative_path"), str):
        raise R02D3PreflightError("fixture artifact reference missing")
    path = root / ".research_artifacts" / R02_D2C_FRAME_ID / artifact["relative_path"]
    if _sha256_file(path) != artifact.get("sha256"):
        raise R02D3PreflightError("fixture artifact hash mismatch")
    return SyntheticEpisode.model_validate_json(path.read_bytes())
