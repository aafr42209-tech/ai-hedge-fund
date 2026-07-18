"""D3-identity Codex transport adapted to the frozen R02 D4-S6 runner."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .codex_exec_client import (
    CodexExecError,
    CodexProcessCapture,
    CodexProcessRunner,
    complete_response_disposition,
    parse_codex_jsonl,
    SubprocessCodexProcessRunner,
)
from .r02_contracts import R02SelectorRequest
from .r02_d3_preflight import R02D3Preregistration, render_live_argv
from .r02_d3_successor_contracts import (
    selector_output_schema,
    selector_output_schema_sha256,
)
from .r02_d4_s6_contracts import (
    R02_D4_S6_TIMEOUT_MS,
    R02D4S6PlannedAttempt,
    R02D4S6TransportResult,
)
from .r02_d4_s6_runner import verify_s5_contract
from .r02_d4_s7_contracts import (
    R02_D4_S7_D3_PREREGISTRATION_SHA256,
    R02_D4_S7_EXECUTABLE_SHA256,
    R02_D4_S7_MODEL,
    R02_D4_S7_PREREGISTERED_RESPONSE_SCHEMA_SHA256,
    R02_D4_S7_PROVIDER,
    R02_D4_S7_RESPONSE_SCHEMA_SHA256,
    R02D4S7TransportEvidence,
    raw_response_sha256,
)


class R02D4S7TransportError(RuntimeError):
    pass


class R02D4S7GuardedProcessRunner(Protocol):
    r02_d3_execution_capability: Literal["OFFLINE_FAKE", "LIVE_PROVIDER_PROCESS"]

    def run(
        self,
        *,
        argv: tuple[str, ...],
        stdin_bytes: bytes,
        working_directory: str,
        timeout_ms: int,
    ) -> CodexProcessCapture:
        ...


@dataclass(frozen=True)
class R02D4S7LiveProcessRunner:
    delegate: CodexProcessRunner
    r02_d3_execution_capability: Literal["LIVE_PROVIDER_PROCESS"] = "LIVE_PROVIDER_PROCESS"

    @classmethod
    def from_environment(cls) -> "R02D4S7LiveProcessRunner":
        return cls(delegate=SubprocessCodexProcessRunner())

    def run(
        self,
        *,
        argv: tuple[str, ...],
        stdin_bytes: bytes,
        working_directory: str,
        timeout_ms: int,
    ) -> CodexProcessCapture:
        return self.delegate.run(
            argv=argv,
            stdin_bytes=stdin_bytes,
            working_directory=working_directory,
            timeout_ms=timeout_ms,
        )


class R02D4S7TransportEvidenceStore:
    """Append-only full-capture evidence isolated from the closed S6 audit root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def write(self, evidence: R02D4S7TransportEvidence) -> Path:
        directory = self.root / "attempts"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (f"{evidence.execution_ordinal:03d}-{evidence.attempt_id}.json")
        raw = canonical_json_bytes(evidence)
        with path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        if path.read_bytes() != raw:
            raise R02D4S7TransportError("persisted transport evidence byte drift")
        return path


def _terminal_usage_event_count(stdout: bytes) -> int:
    try:
        text = stdout.decode("utf-8", errors="strict")
        events = [json.loads(line) for line in text.splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 0
    return sum(1 for event in events if isinstance(event, dict) and event.get("type") == "turn.completed")


class R02D4S7CodexTransport:
    """One-attempt process transport; retry, replacement, and resume do not exist."""

    def __init__(
        self,
        *,
        repository_root: str | Path,
        output_schema_path: str | Path,
        process_runner: R02D4S7GuardedProcessRunner,
        evidence_store: R02D4S7TransportEvidenceStore,
        live_authorized: bool,
    ) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.output_schema_path = Path(output_schema_path).resolve()
        self.process_runner = process_runner
        self.evidence_store = evidence_store
        self._launched_attempt_ids: set[str] = set()
        capability = getattr(process_runner, "r02_d3_execution_capability", None)
        if capability not in ("OFFLINE_FAKE", "LIVE_PROVIDER_PROCESS"):
            raise R02D4S7TransportError("unknown process-runner capability")
        if live_authorized != (capability == "LIVE_PROVIDER_PROCESS"):
            raise R02D4S7TransportError("process-runner capability and LIVE authorization differ")
        self.r02_d4_s6_execution_capability = capability
        verify_s5_contract(self.repository_root)
        prereg_path = self.repository_root / "docs/r02-d3-preregistration.json"
        if sha256_hex(prereg_path.read_bytes()) != R02_D4_S7_D3_PREREGISTRATION_SHA256:
            raise R02D4S7TransportError("D3 preregistration byte drift")
        self.preregistration = R02D3Preregistration.model_validate_json(prereg_path.read_bytes())
        identity = self.preregistration.model_identity
        if identity.executable_sha256 != R02_D4_S7_EXECUTABLE_SHA256:
            raise R02D4S7TransportError("D3 executable identity drift")
        if identity.requested_model_id != R02_D4_S7_MODEL:
            raise R02D4S7TransportError("D3 model identity drift")
        if identity.response_schema_sha256 != R02_D4_S7_PREREGISTERED_RESPONSE_SCHEMA_SHA256:
            raise R02D4S7TransportError("D3 preregistered response schema drift")
        expected_schema = canonical_json_bytes(selector_output_schema())
        if self.output_schema_path.read_bytes() != expected_schema:
            raise R02D4S7TransportError("selector schema is not canonical and frozen")
        if sha256_hex(expected_schema) != R02_D4_S7_RESPONSE_SCHEMA_SHA256 or selector_output_schema_sha256() != R02_D4_S7_RESPONSE_SCHEMA_SHA256:
            raise R02D4S7TransportError("selector schema identity drift")

    def _prompt_and_argv(self, request: R02SelectorRequest) -> tuple[str, str, bytes, tuple[str, ...]]:
        prompt = self.preregistration.prompt
        payload = canonical_json_bytes(request.selector_payload).decode("utf-8")
        expected_user = prompt.user_prompt_template.replace(prompt.payload_placeholder, payload)
        if request.prompt.system_prompt != prompt.system_prompt:
            raise R02D4S7TransportError("system prompt drift")
        if request.prompt.user_prompt != expected_user:
            raise R02D4S7TransportError("user prompt drift")
        stdin = f"{prompt.system_prompt}\n\n{expected_user}\n".encode("utf-8")
        argv = render_live_argv(self.preregistration, self.output_schema_path)
        return prompt.system_prompt, expected_user, stdin, argv

    def _persist(
        self,
        *,
        run_id: str,
        attempt_id: str,
        attempt: R02D4S6PlannedAttempt,
        request: R02SelectorRequest,
        system_prompt: str,
        user_prompt: str,
        stdin: bytes,
        argv: tuple[str, ...],
        capture: CodexProcessCapture,
        terminal_count: int,
        parsed_sha256: str | None,
        raw_sha256: str,
        parse_error_code: str | None,
    ) -> None:
        evidence = R02D4S7TransportEvidence(
            run_id=run_id,
            fixture_id=attempt.fixture_id,
            attempt_id=attempt_id,
            execution_ordinal=attempt.execution_ordinal,
            selector_request_sha256=canonical_sha256(request),
            system_prompt_sha256=sha256_hex(system_prompt.encode("utf-8")),
            user_prompt_sha256=sha256_hex(user_prompt.encode("utf-8")),
            stdin_sha256=sha256_hex(stdin),
            live_argv_sha256=sha256_hex(canonical_json_bytes(argv)),
            stdout_sha256=sha256_hex(capture.stdout),
            stderr_sha256=sha256_hex(capture.stderr),
            stdout_base64=base64.b64encode(capture.stdout).decode("ascii"),
            stderr_base64=base64.b64encode(capture.stderr).decode("ascii"),
            exit_code=capture.exit_code,
            timed_out=capture.timed_out,
            launch_error=capture.launch_error,
            duration_ms=capture.duration_ms,
            terminal_usage_event_count=terminal_count,
            parsed_provider_response_sha256=parsed_sha256,
            raw_response_sha256=raw_sha256,
            parse_error_code=parse_error_code,
            external_provider_calls=(1 if self.r02_d4_s6_execution_capability == "LIVE_PROVIDER_PROCESS" else 0),
        )
        self.evidence_store.write(evidence)

    def execute(
        self,
        *,
        run_id: str,
        attempt_id: str,
        attempt: R02D4S6PlannedAttempt,
        selector_request: R02SelectorRequest,
        timeout_ms: int,
    ) -> R02D4S6TransportResult:
        if timeout_ms != R02_D4_S6_TIMEOUT_MS:
            raise R02D4S7TransportError("timeout differs from the S5/S6 freeze")
        if attempt.selector_request_sha256 != canonical_sha256(selector_request):
            raise R02D4S7TransportError("selector request differs from the prepared plan")
        if selector_request.identity.fixture_id != attempt.fixture_id:
            raise R02D4S7TransportError("selector request fixture identity drift")
        if attempt_id in self._launched_attempt_ids:
            raise R02D4S7TransportError("duplicate provider attempt blocked")
        system_prompt, user_prompt, stdin, argv = self._prompt_and_argv(selector_request)
        self._launched_attempt_ids.add(attempt_id)
        try:
            capture = self.process_runner.run(
                argv=argv,
                stdin_bytes=stdin,
                working_directory=str(self.repository_root),
                timeout_ms=timeout_ms,
            )
        except Exception as exc:
            capture = CodexProcessCapture(
                stdout=b"",
                stderr=b"",
                exit_code=None,
                duration_ms=0,
                launch_error=f"{type(exc).__name__}:{exc}",
            )
        terminal_count = _terminal_usage_event_count(capture.stdout)
        raw_response: str | None = None
        parsed = None
        parse_error_code: str | None = None
        if capture.timed_out:
            parse_error_code = "TIMEOUT"
        elif capture.launch_error is not None:
            parse_error_code = "PROCESS_LAUNCH_FAILURE"
        elif capture.exit_code != 0:
            parse_error_code = "NONZERO_EXIT"
        else:
            try:
                parsed = parse_codex_jsonl(
                    capture,
                    requested_model_id=self.preregistration.model_identity.requested_model_id,
                )
                disposition = complete_response_disposition(parsed)
                if disposition is not None:
                    parse_error_code = disposition.value
                    parsed = None
                else:
                    raw_response = parsed.raw_text
            except CodexExecError as exc:
                parse_error_code = exc.code
        raw_sha256 = raw_response_sha256(raw_response)
        self._persist(
            run_id=run_id,
            attempt_id=attempt_id,
            attempt=attempt,
            request=selector_request,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            stdin=stdin,
            argv=argv,
            capture=capture,
            terminal_count=terminal_count,
            parsed_sha256=(canonical_sha256(parsed) if parsed is not None else None),
            raw_sha256=raw_sha256,
            parse_error_code=parse_error_code,
        )
        external_calls = 1 if self.r02_d4_s6_execution_capability == "LIVE_PROVIDER_PROCESS" else 0
        return R02D4S6TransportResult(
            run_id=run_id,
            fixture_id=attempt.fixture_id,
            attempt_id=attempt_id,
            raw_response=raw_response,
            raw_response_sha256=raw_sha256,
            input_tokens=(parsed.input_tokens if parsed is not None else None),
            cached_input_tokens=(parsed.cached_input_tokens if parsed is not None else None),
            output_tokens=(parsed.output_tokens if parsed is not None else None),
            reasoning_output_tokens=(parsed.reasoning_output_tokens if parsed is not None else None),
            terminal_usage_event_count=terminal_count,
            exit_code=capture.exit_code,
            timed_out=capture.timed_out,
            launch_error=(capture.launch_error if capture.launch_error is not None else (f"transport:{parse_error_code}" if parse_error_code else None)),
            duration_ms=capture.duration_ms,
            external_provider_calls=external_calls,
        )
