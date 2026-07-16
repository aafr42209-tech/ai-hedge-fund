"""Mock-injected Codex exec adapter and strict JSONL transport contract for R01 B1."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from .artifacts import AppendOnlyArtifactStore, ArtifactError
from .canonical import canonical_sha256, sha256_hex
from .codex_preflight import pilot_sandbox_identity_sha256
from .contracts import (
    AcquisitionDisposition,
    AcquisitionIdentity,
    ArtifactReference,
    codex_feature_catalog_definition_sha256,
    codex_feature_catalog_snapshot_sha256,
    CodexAttemptFailureTransportArtifacts,
    CodexAttemptTransportArtifacts,
    CodexCommandSpec,
    CodexFeatureCatalogEntry,
    CodexProcessStatus,
    config_key_may_contain_secret,
    config_value_may_contain_secret,
    ProviderResponse,
)

POLICY_FIXTURE_DELIMITER = "\n\n--- R01 FIXTURE PROMPT ---\n\n"
PROVIDER_ID = "openai-codex-chatgpt-subscription"
FEATURE_NAME = re.compile(r"^[a-z0-9_]+$")
KNOWN_EVENT_TYPES = (
    "error",
    "item.completed",
    "item.started",
    "item.updated",
    "thread.started",
    "turn.completed",
    "turn.failed",
    "turn.started",
)
NON_TOOL_ITEM_TYPES = ("agent_message", "plan", "plan_update", "reasoning")
KNOWN_TOOL_ITEM_TYPES = (
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "web_search",
)
KNOWN_ITEM_TYPES = tuple(sorted(NON_TOOL_ITEM_TYPES + KNOWN_TOOL_ITEM_TYPES))
USAGE_FIELDS = (
    "cached_input_tokens",
    "input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
EVENT_FIELD_SPEC = {
    "error": {"required": ("type",), "optional": ("error", "message", "model")},
    "item.completed": {"required": ("item", "type"), "optional": ("model",)},
    "item.started": {"required": ("item", "type"), "optional": ("model",)},
    "item.updated": {"required": ("item", "type"), "optional": ("model",)},
    "thread.started": {
        "required": ("thread_id", "type"),
        "optional": ("model",),
    },
    "turn.completed": {
        "required": ("type", "usage"),
        "optional": ("model",),
    },
    "turn.failed": {"required": ("type",), "optional": ("error", "model")},
    "turn.started": {"required": ("type",), "optional": ("model",)},
}
ITEM_FIELD_SPEC = {
    "agent_message": {
        "required": ("id", "type"),
        "optional": ("model", "status", "text"),
    },
    "command_execution": {
        "required": ("id", "type"),
        "optional": (
            "aggregated_output",
            "command",
            "exit_code",
            "model",
            "status",
        ),
    },
    "file_change": {
        "required": ("id", "type"),
        "optional": ("changes", "model", "status"),
    },
    "mcp_tool_call": {
        "required": ("id", "type"),
        "optional": (
            "arguments",
            "error",
            "model",
            "result",
            "server",
            "status",
            "tool",
        ),
    },
    "plan": {
        "required": ("id", "type"),
        "optional": ("model", "status", "text"),
    },
    "plan_update": {
        "required": ("id", "type"),
        "optional": ("model", "plan", "status", "text"),
    },
    "reasoning": {
        "required": ("id", "type"),
        "optional": ("model", "status", "text"),
    },
    "web_search": {
        "required": ("id", "type"),
        "optional": ("model", "query", "status"),
    },
}


class CodexExecError(RuntimeError):
    """One classified acquisition failure with an explicit phase disposition."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        disposition: AcquisitionDisposition,
        origin_code: str | None = None,
        origin_disposition: AcquisitionDisposition | None = None,
    ) -> None:
        super().__init__(message)
        if (origin_code is None) != (origin_disposition is None):
            raise ValueError("origin code and disposition must be recorded together")
        self.code = code
        self.disposition = disposition
        self.origin_code = origin_code
        self.origin_disposition = origin_disposition


@dataclass(frozen=True)
class CodexProcessCapture:
    stdout: bytes
    stderr: bytes
    exit_code: int | None
    duration_ms: int
    timed_out: bool = False
    launch_error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stdout, bytes) or not isinstance(self.stderr, bytes):
            raise TypeError("stdout and stderr captures must be bytes")
        if isinstance(self.duration_ms, bool) or not isinstance(self.duration_ms, int):
            raise TypeError("duration_ms must be an integer")
        if isinstance(self.exit_code, bool) or (self.exit_code is not None and not isinstance(self.exit_code, int)):
            raise TypeError("exit_code must be an integer or None")
        if not isinstance(self.timed_out, bool):
            raise TypeError("timed_out must be a boolean")
        if self.launch_error is not None and not isinstance(self.launch_error, str):
            raise TypeError("launch_error must be text or None")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be nonnegative")
        if self.launch_error is not None and self.exit_code is not None:
            raise ValueError("launch-error capture cannot also have an exit code")
        if not self.timed_out and self.launch_error is None and self.exit_code is None:
            raise ValueError("completed capture requires an exit code")

    def process_status(self) -> CodexProcessStatus:
        return CodexProcessStatus(
            exit_code=self.exit_code,
            timed_out=self.timed_out,
            launch_error=self.launch_error,
            duration_ms=self.duration_ms,
            stdout_sha256=sha256_hex(self.stdout),
            stdout_size_bytes=len(self.stdout),
            stderr_sha256=sha256_hex(self.stderr),
            stderr_size_bytes=len(self.stderr),
        )


class CodexProcessRunner(Protocol):
    def run(
        self,
        *,
        argv: tuple[str, ...],
        stdin_bytes: bytes,
        working_directory: str,
        timeout_ms: int,
    ) -> CodexProcessCapture:
        ...


CaptureSink = Callable[[CodexCommandSpec, CodexProcessCapture], None]


class SubprocessCodexProcessRunner:
    """Shell-free Codex runner with a secret-bearing environment denylist."""

    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        source = dict(os.environ if environment is None else environment)
        self.environment = {key: value for key, value in source.items() if not config_key_may_contain_secret(key)}
        self.removed_environment_keys = tuple(sorted(set(source) - set(self.environment)))

    def run(
        self,
        *,
        argv: tuple[str, ...],
        stdin_bytes: bytes,
        working_directory: str,
        timeout_ms: int,
    ) -> CodexProcessCapture:
        started_ns = time.monotonic_ns()
        try:
            completed = subprocess.run(
                argv,
                input=stdin_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_directory,
                env=self.environment,
                check=False,
                shell=False,
                timeout=timeout_ms / 1_000,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = (time.monotonic_ns() - started_ns) // 1_000_000
            return CodexProcessCapture(
                stdout=exc.stdout if isinstance(exc.stdout, bytes) else b"",
                stderr=exc.stderr if isinstance(exc.stderr, bytes) else b"",
                exit_code=None,
                duration_ms=duration_ms,
                timed_out=True,
            )
        duration_ms = (time.monotonic_ns() - started_ns) // 1_000_000
        return CodexProcessCapture(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            duration_ms=duration_ms,
        )


@dataclass(frozen=True)
class _RawTransportArtifacts:
    command_spec: ArtifactReference
    stdout_jsonl: ArtifactReference
    stderr: ArtifactReference
    process_status: ArtifactReference


def _transport_artifact_prefix(identity: AcquisitionIdentity) -> str:
    discriminator = f"replicate-{identity.replicate_id:03d}" if identity.replicate_id is not None else f"perturbation-{identity.perturbation_id}"
    return f"{identity.experiment_id}/acquisitions/{identity.case_id}/" f"{identity.channel}/{discriminator}/attempt-{identity.attempt}/transport"


def compose_stdin_bytes(policy_instruction: str, fixture_prompt: str) -> bytes:
    """Return the exact bytes passed to `codex exec -`."""

    return (policy_instruction + POLICY_FIXTURE_DELIMITER + fixture_prompt).encode("utf-8")


def codex_jsonl_schema_spec() -> dict[str, object]:
    """Return the strict B1 parser identity hashed into every command spec."""

    return {
        "schema_version": "r01-codex-jsonl-parser-v2",
        "known_event_types": list(KNOWN_EVENT_TYPES),
        "required_counts": {
            "thread.started": 1,
            "turn.started": 1,
            "turn.completed": 1,
        },
        "contradictory_terminal_types": ["error", "turn.failed"],
        "final_message_event": "item.completed/agent_message",
        "usage_fields": list(USAGE_FIELDS),
        "non_tool_item_types": list(NON_TOOL_ITEM_TYPES),
        "known_tool_item_types": list(KNOWN_TOOL_ITEM_TYPES),
        "unknown_event_policy": "fail_closed",
        "unknown_item_policy": "schema_drift_stop_phase",
        "model_echo_policy": {
            "matching": "verified",
            "absent": "explicit_unverified_limitation",
            "mismatch": "stop_phase",
        },
        "transport_shape_spec_sha256": codex_transport_shape_spec_sha256(),
        "duplicate_json_key_policy": "fail_closed",
        "nonfinite_json_number_policy": "fail_closed",
    }


def codex_jsonl_schema_sha256() -> str:
    return canonical_sha256(codex_jsonl_schema_spec())


def codex_transport_shape_spec() -> dict[str, object]:
    """Return the pinned allowed field surface for every JSONL event and item."""

    return {
        "schema_version": "r01-codex-transport-shape-spec-v1",
        "event_fields": EVENT_FIELD_SPEC,
        "item_fields": ITEM_FIELD_SPEC,
        "model_echo_locations": ("event.model", "item.model"),
        "unknown_field_policy": "schema_drift_stop_phase",
    }


def codex_transport_shape_spec_sha256() -> str:
    return canonical_sha256(codex_transport_shape_spec())


def _canonical_unique(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} contains duplicates")
    return tuple(sorted(values))


def build_codex_command_spec(
    *,
    executable: str,
    model_id: str,
    feature_catalog: tuple[CodexFeatureCatalogEntry, ...],
    expected_feature_catalog_sha256: str,
    disabled_features: tuple[str, ...],
    active_feature_allowlist: tuple[str, ...],
    post_disable_effective_true_features: tuple[str, ...],
    config_overrides: tuple[str, ...],
    working_directory: str,
    expected_pilot_sandbox_sha256: str,
    expected_transport_shape_spec_sha256: str,
    timeout_ms: int,
    policy_instruction: str,
    fixture_prompt: str,
) -> tuple[CodexCommandSpec, bytes]:
    """Build the shell-free ordered argv and exact stdin identity."""

    disabled = _canonical_unique(disabled_features, "disabled feature list")
    allowlist = _canonical_unique(active_feature_allowlist, "active feature allowlist")
    post_disable_true = _canonical_unique(
        post_disable_effective_true_features,
        "post-disable effective-true feature list",
    )
    configs = _canonical_unique(config_overrides, "config overrides")
    if any(FEATURE_NAME.fullmatch(name) is None for name in disabled + allowlist):
        raise ValueError("feature names must contain lowercase letters, digits, or underscores")
    if set(disabled) & set(allowlist):
        raise ValueError("disabled features and active allowlist overlap")
    catalog = tuple(sorted(feature_catalog, key=lambda entry: entry.name))
    catalog_names = tuple(entry.name for entry in catalog)
    if len(catalog_names) != len(set(catalog_names)):
        raise ValueError("feature catalog contains duplicate names")
    actual_catalog_sha256 = codex_feature_catalog_snapshot_sha256(catalog)
    catalog_definition_sha256 = codex_feature_catalog_definition_sha256(catalog)
    if actual_catalog_sha256 != expected_feature_catalog_sha256:
        raise RuntimeError("feature catalog differs from the external trust anchor")
    if set(disabled) | set(allowlist) != set(catalog_names):
        raise ValueError("disabled features and active allowlist must cover the catalog")
    if not set(post_disable_true).issubset(allowlist):
        raise RuntimeError("post-disable effective-true features exceed the allowlist")
    if "tools.web_search=false" not in configs:
        raise ValueError("tools.web_search=false is mandatory")
    if any(any(character in value for character in "\r\n\0") or "=" not in value for value in configs):
        raise ValueError("config overrides must be one-line key=value strings")
    config_pairs = [value.split("=", 1) for value in configs]
    config_keys = [pair[0] for pair in config_pairs]
    if any(not key or not value for key, value in config_pairs):
        raise ValueError("config override keys and values must be nonempty")
    if len(config_keys) != len(set(config_keys)):
        raise ValueError("config override keys must be unique")
    if any(config_key_may_contain_secret(key) for key in config_keys):
        raise ValueError("secret-bearing config keys are prohibited")
    if any(config_value_may_contain_secret(value) for _, value in config_pairs):
        raise ValueError("secret-bearing config values are prohibited")
    actual_pilot_sandbox_sha256 = pilot_sandbox_identity_sha256(working_directory)
    if actual_pilot_sandbox_sha256 != expected_pilot_sandbox_sha256:
        raise RuntimeError("pilot sandbox differs from the external trust anchor")
    actual_transport_shape_spec_sha256 = codex_transport_shape_spec_sha256()
    if actual_transport_shape_spec_sha256 != expected_transport_shape_spec_sha256:
        raise RuntimeError("transport shape spec differs from the external trust anchor")
    directory = Path(working_directory)
    if timeout_ms <= 0:
        raise ValueError("timeout_ms must be positive")
    if not executable or not model_id or any(character in executable or character in model_id for character in "\r\n\0"):
        raise ValueError("executable and model_id are required")

    argv: list[str] = [executable]
    for feature in disabled:
        argv.extend(("--disable", feature))
    argv.extend(
        (
            "exec",
            "--model",
            model_id,
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--strict-config",
        )
    )
    for config in configs:
        argv.extend(("--config", config))
    argv.extend(("--json", "-"))
    stdin_bytes = compose_stdin_bytes(policy_instruction, fixture_prompt)
    spec = CodexCommandSpec(
        executable=executable,
        argv=tuple(argv),
        model_id=model_id,
        feature_catalog=catalog,
        feature_catalog_sha256=actual_catalog_sha256,
        feature_catalog_definition_sha256=catalog_definition_sha256,
        disabled_features=disabled,
        active_feature_allowlist=allowlist,
        post_disable_effective_true_features=post_disable_true,
        config_overrides=configs,
        working_directory=str(directory.resolve()),
        pilot_sandbox_sha256=actual_pilot_sandbox_sha256,
        timeout_ms=timeout_ms,
        policy_instruction_sha256=sha256_hex(policy_instruction.encode("utf-8")),
        fixture_prompt_sha256=sha256_hex(fixture_prompt.encode("utf-8")),
        stdin_sha256=sha256_hex(stdin_bytes),
        jsonl_schema_sha256=codex_jsonl_schema_sha256(),
        transport_shape_spec_sha256=actual_transport_shape_spec_sha256,
    )
    return spec, stdin_bytes


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _transport_error(code: str, message: str) -> CodexExecError:
    return CodexExecError(
        code,
        message,
        disposition=AcquisitionDisposition.RETRY_TRANSPORT,
    )


def _stop_error(code: str, message: str) -> CodexExecError:
    return CodexExecError(
        code,
        message,
        disposition=AcquisitionDisposition.STOP_PHASE,
    )


def complete_response_disposition(
    response: ProviderResponse,
) -> AcquisitionDisposition | None:
    """Classify complete transport quality without conflating harness failure."""

    if response.process_status_violation:
        return AcquisitionDisposition.STOP_PHASE
    if response.tool_use_violation:
        return AcquisitionDisposition.FAIL_CLOSED_SCORE
    return None


def _validate_fields(
    value: dict[str, Any],
    *,
    required: tuple[str, ...],
    optional: tuple[str, ...],
    label: str,
) -> None:
    actual = set(value)
    missing = set(required) - actual
    unknown = actual - set(required) - set(optional)
    if missing or unknown:
        raise _stop_error(
            "jsonl_schema_drift",
            f"{label} field shape differs from the pinned transport spec",
        )


def _observed_transport_shape(events: list[dict[str, Any]]) -> dict[str, object]:
    signatures: set[tuple[str, tuple[str, ...], str | None, tuple[str, ...]]] = set()
    for event in events:
        item = event.get("item")
        item_type = item.get("type") if isinstance(item, dict) else None
        item_fields = tuple(sorted(item)) if isinstance(item, dict) else ()
        signatures.add((event["type"], tuple(sorted(event)), item_type, item_fields))
    return {
        "schema_version": "r01-observed-codex-transport-shape-v1",
        "signatures": [
            {
                "event_type": event_type,
                "event_fields": event_fields,
                "item_type": item_type,
                "item_fields": item_fields,
            }
            for event_type, event_fields, item_type, item_fields in sorted(
                signatures,
                key=lambda value: (
                    value[0],
                    value[1],
                    value[2] or "",
                    value[3],
                ),
            )
        ],
    }


def _strict_usage(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        raise _transport_error("missing_usage", "terminal usage fields do not match the B1 schema")
    missing = set(USAGE_FIELDS) - set(value)
    unknown = set(value) - set(USAGE_FIELDS)
    if unknown:
        raise _stop_error(
            "jsonl_schema_drift",
            "terminal usage contains fields outside the pinned transport spec",
        )
    if missing:
        raise _transport_error("missing_usage", "terminal usage fields do not match the B1 schema")
    if any(isinstance(value[field], bool) or not isinstance(value[field], int) or value[field] < 0 for field in USAGE_FIELDS):
        raise _transport_error("invalid_usage", "terminal usage values must be nonnegative integers")
    return {field: value[field] for field in USAGE_FIELDS}


def parse_codex_jsonl(
    capture: CodexProcessCapture,
    *,
    requested_model_id: str,
) -> ProviderResponse:
    """Parse one complete Codex JSONL capture or raise a retry-classified error."""

    try:
        text = capture.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _transport_error("malformed_jsonl", "stdout is not valid UTF-8") from exc
    lines = text.splitlines()
    if not lines:
        raise _transport_error("empty_transport", "stdout JSONL is empty")

    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise _transport_error("malformed_jsonl", f"blank JSONL line at {line_number}")
        try:
            event = json.loads(
                line,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_nonfinite_constant,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            raise _transport_error("malformed_jsonl", f"invalid JSONL at line {line_number}") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise _transport_error("malformed_jsonl", f"event {line_number} lacks a string type")
        if event["type"] not in KNOWN_EVENT_TYPES:
            raise _stop_error("jsonl_schema_drift", f"unknown event type: {event['type']}")
        field_spec = EVENT_FIELD_SPEC[event["type"]]
        _validate_fields(
            event,
            required=field_spec["required"],
            optional=field_spec["optional"],
            label=f"event {event['type']}",
        )
        events.append(event)

    event_types = tuple(event["type"] for event in events)
    thread_events = [event for event in events if event["type"] == "thread.started"]
    if len(thread_events) != 1 or not isinstance(thread_events[0].get("thread_id"), str) or not thread_events[0]["thread_id"]:
        raise _transport_error("thread_identity_violation", "exactly one nonempty thread.started identifier is required")
    if event_types.count("turn.started") != 1:
        raise _transport_error("turn_start_violation", "exactly one turn.started event is required")
    terminal_events = [event for event in events if event["type"] == "turn.completed"]
    if len(terminal_events) > 1:
        raise _transport_error("duplicate_terminal_event", "multiple turn.completed events found")
    if any(kind in event_types for kind in ("turn.failed", "error")):
        raise _transport_error("contradictory_terminal_status", "failed or error event contradicts completion")
    if len(terminal_events) != 1:
        raise _transport_error("missing_terminal_event", "one turn.completed event is required")
    usage = _strict_usage(terminal_events[0].get("usage"))

    messages: list[str] = []
    item_types: list[str] = []
    model_echoes: list[str] = []
    for event in events:
        event_model = event.get("model")
        if event_model is not None:
            if not isinstance(event_model, str) or not event_model:
                raise _stop_error(
                    "jsonl_schema_drift",
                    "event model echo must be nonempty text",
                )
            model_echoes.append(event_model)
        if not event["type"].startswith("item."):
            continue
        item = event.get("item")
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            raise _transport_error("malformed_jsonl", "item event lacks an item type")
        item_type = item["type"]
        if item_type not in KNOWN_ITEM_TYPES:
            raise _stop_error(
                "jsonl_schema_drift",
                f"unknown item type: {item_type}",
            )
        item_field_spec = ITEM_FIELD_SPEC[item_type]
        _validate_fields(
            item,
            required=item_field_spec["required"],
            optional=item_field_spec["optional"],
            label=f"item {item_type}",
        )
        item_model = item.get("model")
        if item_model is not None:
            if not isinstance(item_model, str) or not item_model:
                raise _stop_error(
                    "jsonl_schema_drift",
                    "item model echo must be nonempty text",
                )
            model_echoes.append(item_model)
        item_types.append(item_type)
        if event["type"] == "item.completed" and item_type == "agent_message":
            if not isinstance(item.get("text"), str):
                raise _transport_error("malformed_jsonl", "completed agent message lacks text")
            messages.append(item["text"])
    if not messages:
        raise _transport_error("missing_final_message", "no completed agent message found")
    if not messages[-1].strip():
        raise _transport_error("empty_response", "final completed agent message is empty")

    unique_model_echoes = tuple(sorted(set(model_echoes)))
    if any(model_echo != requested_model_id for model_echo in unique_model_echoes):
        raise _stop_error(
            "model_identity_mismatch",
            "transport model echo differs from the requested model",
        )
    tool_types = tuple(sorted(set(item_types) & set(KNOWN_TOOL_ITEM_TYPES)))
    status = capture.process_status()
    return ProviderResponse(
        raw_text=messages[-1],
        provider=PROVIDER_ID,
        model_id=requested_model_id,
        request_id=thread_events[0]["thread_id"],
        input_tokens=usage["input_tokens"],
        cached_input_tokens=usage["cached_input_tokens"],
        output_tokens=usage["output_tokens"],
        reasoning_output_tokens=usage["reasoning_output_tokens"],
        model_identity_verified_by_transport=bool(unique_model_echoes),
        model_identity_evidence=("matching_transport_echo" if unique_model_echoes else "transport_echo_absent"),
        transport_model_echoes=unique_model_echoes,
        tool_use_violation=bool(tool_types),
        tool_event_types=tool_types,
        process_status_violation=(capture.timed_out or capture.launch_error is not None or capture.exit_code != 0),
        event_types=event_types,
        agent_message_count=len(messages),
        transport_sha256=status.stdout_sha256,
        observed_transport_shape_sha256=canonical_sha256(_observed_transport_shape(events)),
        process_status=status,
    )


class CodexExecClient:
    """Development-only adapter; B1 requires injected runner and raw-capture sink."""

    def __init__(
        self,
        *,
        executable: str,
        model_id: str,
        feature_catalog: tuple[CodexFeatureCatalogEntry, ...],
        expected_feature_catalog_sha256: str,
        disabled_features: tuple[str, ...],
        active_feature_allowlist: tuple[str, ...],
        post_disable_effective_true_features: tuple[str, ...],
        config_overrides: tuple[str, ...],
        working_directory: str,
        expected_pilot_sandbox_sha256: str,
        expected_transport_shape_spec_sha256: str,
        timeout_ms: int,
        process_runner: CodexProcessRunner,
        capture_sink: CaptureSink | None = None,
        transport_store: AppendOnlyArtifactStore | None = None,
        expected_command_spec_sha256_by_prompt: Mapping[str, str] | None = None,
    ) -> None:
        self._executable = executable
        self._model_id = model_id
        self._feature_catalog = feature_catalog
        self._expected_feature_catalog_sha256 = expected_feature_catalog_sha256
        self._disabled_features = disabled_features
        self._active_feature_allowlist = active_feature_allowlist
        self._post_disable_effective_true_features = post_disable_effective_true_features
        self._config_overrides = config_overrides
        self._working_directory = working_directory
        self._expected_pilot_sandbox_sha256 = expected_pilot_sandbox_sha256
        self._expected_transport_shape_spec_sha256 = expected_transport_shape_spec_sha256
        self._timeout_ms = timeout_ms
        self._process_runner = process_runner
        self._capture_sink = capture_sink
        self._transport_store = transport_store
        self._transport_artifacts: dict[str, CodexAttemptTransportArtifacts] = {}
        self._failure_transport_artifacts: dict[
            str,
            CodexAttemptFailureTransportArtifacts,
        ] = {}
        self._expected_command_specs = dict(expected_command_spec_sha256_by_prompt or {})
        self.provider_calls = 0

    def _persist_capture(
        self,
        identity: AcquisitionIdentity,
        spec: CodexCommandSpec,
        capture: CodexProcessCapture,
    ) -> _RawTransportArtifacts | None:
        if self._transport_store is None:
            return None
        prefix = _transport_artifact_prefix(identity)
        return _RawTransportArtifacts(
            command_spec=self._transport_store.write_json(f"{prefix}/command_spec.json", spec),
            stdout_jsonl=self._transport_store.write_bytes(f"{prefix}/stdout.jsonl", capture.stdout),
            stderr=self._transport_store.write_bytes(f"{prefix}/stderr.bin", capture.stderr),
            process_status=self._transport_store.write_json(
                f"{prefix}/process_status.json",
                capture.process_status(),
            ),
        )

    def transport_artifacts_for(
        self,
        identity: AcquisitionIdentity,
    ) -> CodexAttemptTransportArtifacts | None:
        return self._transport_artifacts.get(canonical_sha256(identity))

    def failure_transport_artifacts_for(
        self,
        identity: AcquisitionIdentity,
    ) -> CodexAttemptFailureTransportArtifacts | None:
        return self._failure_transport_artifacts.get(canonical_sha256(identity))

    def complete(
        self,
        *,
        system: str,
        user: str,
        identity: AcquisitionIdentity,
    ) -> ProviderResponse:
        if identity.channel != "development":
            raise CodexExecError(
                "forbidden_channel",
                "B1 Codex adapter accepts development acquisitions only",
                disposition=AcquisitionDisposition.STOP_PHASE,
            )
        try:
            spec, stdin_bytes = build_codex_command_spec(
                executable=self._executable,
                model_id=self._model_id,
                feature_catalog=self._feature_catalog,
                expected_feature_catalog_sha256=self._expected_feature_catalog_sha256,
                disabled_features=self._disabled_features,
                active_feature_allowlist=self._active_feature_allowlist,
                post_disable_effective_true_features=(self._post_disable_effective_true_features),
                config_overrides=self._config_overrides,
                working_directory=self._working_directory,
                expected_pilot_sandbox_sha256=self._expected_pilot_sandbox_sha256,
                expected_transport_shape_spec_sha256=(self._expected_transport_shape_spec_sha256),
                timeout_ms=self._timeout_ms,
                policy_instruction=system,
                fixture_prompt=user,
            )
        except (ValueError, RuntimeError) as exc:
            raise CodexExecError(
                "command_spec_build_failure",
                "Codex command spec failed its reviewed pre-call validation",
                disposition=AcquisitionDisposition.STOP_PHASE,
            ) from exc
        if self._expected_command_specs:
            expected = self._expected_command_specs.get(spec.fixture_prompt_sha256)
            if expected is None or canonical_sha256(spec) != expected:
                raise CodexExecError(
                    "command_spec_preflight_mismatch",
                    "live command spec differs from the reviewed B3 preflight",
                    disposition=AcquisitionDisposition.STOP_PHASE,
                )
        self.provider_calls += 1
        try:
            capture = self._process_runner.run(
                argv=spec.argv,
                stdin_bytes=stdin_bytes,
                working_directory=spec.working_directory,
                timeout_ms=spec.timeout_ms,
            )
        except CodexExecError:
            raise
        except (OSError, subprocess.SubprocessError) as exc:
            raise CodexExecError(
                "process_launch_failure",
                "Codex process runner failed before producing a capture",
                disposition=AcquisitionDisposition.RETRY_TRANSPORT,
            ) from exc
        try:
            raw_transport = self._persist_capture(identity, spec, capture)
        except ArtifactError as exc:
            raise CodexExecError(
                "transport_artifact_persistence_failure",
                "raw Codex transport artifacts could not be persisted completely",
                disposition=AcquisitionDisposition.STOP_PHASE,
            ) from exc
        if raw_transport is not None:
            self._failure_transport_artifacts[canonical_sha256(identity)] = CodexAttemptFailureTransportArtifacts(
                command_spec=raw_transport.command_spec,
                stdout_jsonl=raw_transport.stdout_jsonl,
                stderr=raw_transport.stderr,
                process_status=raw_transport.process_status,
            )
        try:
            if self._capture_sink is not None:
                self._capture_sink(spec, capture)
        except Exception as exc:
            raise CodexExecError(
                "artifact_sink_failure",
                "raw capture sink failed before transport parsing",
                disposition=AcquisitionDisposition.STOP_PHASE,
            ) from exc
        if capture.launch_error is not None:
            raise CodexExecError(
                "process_launch_failure",
                capture.launch_error,
                disposition=AcquisitionDisposition.RETRY_TRANSPORT,
            )
        try:
            response = parse_codex_jsonl(capture, requested_model_id=self._model_id)
            if raw_transport is not None:
                if self._transport_store is None:  # pragma: no cover - guarded by _persist_capture
                    raise CodexExecError(
                        "transport_store_unavailable",
                        "transport store disappeared after raw capture persistence",
                        disposition=AcquisitionDisposition.STOP_PHASE,
                    )
                prefix = _transport_artifact_prefix(identity)
                try:
                    provider_response = self._transport_store.write_json(
                        f"{prefix}/provider_response.json",
                        response,
                    )
                except ArtifactError as exc:
                    raise CodexExecError(
                        "provider_response_artifact_persistence_failure",
                        "parsed provider response could not be persisted",
                        disposition=AcquisitionDisposition.STOP_PHASE,
                    ) from exc
                self._failure_transport_artifacts[canonical_sha256(identity)] = CodexAttemptFailureTransportArtifacts(
                    command_spec=raw_transport.command_spec,
                    stdout_jsonl=raw_transport.stdout_jsonl,
                    stderr=raw_transport.stderr,
                    process_status=raw_transport.process_status,
                    provider_response=provider_response,
                )
                self._transport_artifacts[canonical_sha256(identity)] = CodexAttemptTransportArtifacts(
                    command_spec=raw_transport.command_spec,
                    stdout_jsonl=raw_transport.stdout_jsonl,
                    stderr=raw_transport.stderr,
                    process_status=raw_transport.process_status,
                    provider_response=provider_response,
                )
            disposition = complete_response_disposition(response)
            if disposition is AcquisitionDisposition.STOP_PHASE:
                raise CodexExecError(
                    "process_status_violation",
                    "complete Codex transport has a non-success process status",
                    disposition=AcquisitionDisposition.STOP_PHASE,
                )
            return response
        except CodexExecError as exc:
            if exc.disposition is AcquisitionDisposition.STOP_PHASE:
                raise
            if capture.timed_out:
                raise CodexExecError(
                    "timeout_without_complete_response",
                    "Codex process timed out without a complete response",
                    disposition=AcquisitionDisposition.RETRY_TRANSPORT,
                    origin_code=exc.code,
                    origin_disposition=exc.disposition,
                ) from exc
            if capture.exit_code not in (None, 0):
                disposition = AcquisitionDisposition.STOP_PHASE if identity.attempt == 1 else AcquisitionDisposition.RETRY_TRANSPORT
                raise CodexExecError(
                    "nonzero_exit_without_complete_response",
                    ("initial Codex process exited nonzero without a complete response; " "stop before retrying a possibly unavailable model" if identity.attempt == 1 else "Codex retry process exited nonzero without a complete response"),
                    disposition=disposition,
                    origin_code=exc.code,
                    origin_disposition=exc.disposition,
                ) from exc
            raise
