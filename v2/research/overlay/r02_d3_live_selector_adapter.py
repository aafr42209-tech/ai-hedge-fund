"""R02 production selector transport adapter with an injected process boundary."""

from __future__ import annotations

import base64
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
)
from .r02_contracts import R02ProviderFreePreparation, R02SelectorRequest
from .r02_d3_contracts import selector_output_schema, selector_output_schema_sha256
from .r02_d3_preflight import R02D3Preregistration, render_frozen_prompt, render_live_argv
from .r02_d3_runner_contracts import (
    R02_D3_ACCEPTED_PREREGISTRATION_SHA256,
    R02_D3_EXPECTED_EXECUTABLE_SHA256,
    R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT,
    R02D3LiveTokenLedger,
    R02D3LiveTransportRecord,
    R02D3PromptIdentity,
    R02D3RunAuthorization,
)


class R02D3SelectorTransportError(RuntimeError):
    def __init__(self, code: str, capture: CodexProcessCapture, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.capture = capture


class R02D3GuardedProcessRunner(Protocol):
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
class R02D3LiveProviderProcessRunner:
    """Explicit LIVE-only wrapper around the reviewed process boundary."""

    delegate: CodexProcessRunner
    r02_d3_execution_capability: Literal["LIVE_PROVIDER_PROCESS"] = (
        "LIVE_PROVIDER_PROCESS"
    )

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


@dataclass(frozen=True)
class R02D3BoundAttempt:
    authorization: R02D3RunAuthorization
    preparation: R02ProviderFreePreparation
    attempt_id: str
    provider_attempt_ordinal: int


class R02D3CodexSelectorAdapter:
    """Duck-typed ``select(request)`` transport without R01 run semantics."""

    def __init__(
        self,
        *,
        preregistration: R02D3Preregistration,
        output_schema_path: str | Path,
        working_directory: str | Path,
        process_runner: R02D3GuardedProcessRunner,
    ) -> None:
        self.preregistration = preregistration
        self.output_schema_path = Path(output_schema_path).resolve()
        self.working_directory = str(Path(working_directory).resolve())
        self.process_runner = process_runner
        self._bound: R02D3BoundAttempt | None = None
        self._launched_attempt_ids: set[str] = set()
        if canonical_sha256(preregistration) != R02_D3_ACCEPTED_PREREGISTRATION_SHA256:
            raise ValueError("accepted D3 preregistration identity drift")
        if (
            preregistration.model_identity.executable_sha256
            != R02_D3_EXPECTED_EXECUTABLE_SHA256
        ):
            raise ValueError("accepted D3 executable identity drift")
        if not self.output_schema_path.is_file():
            raise ValueError("frozen selector output schema file is missing")
        expected_schema = canonical_json_bytes(selector_output_schema())
        if self.output_schema_path.read_bytes() != expected_schema:
            raise ValueError("selector output schema bytes are not canonical and frozen")
        if sha256_hex(expected_schema) != selector_output_schema_sha256():
            raise ValueError("selector output schema identity drift")

    def bind_attempt(self, bound: R02D3BoundAttempt) -> None:
        self._require_runner_capability(bound)
        if bound.attempt_id in self._launched_attempt_ids:
            raise R02D3SelectorTransportError(
                "DUPLICATE_PROVIDER_CALL_BLOCKED",
                CodexProcessCapture(
                    stdout=b"",
                    stderr=b"",
                    exit_code=None,
                    duration_ms=0,
                    launch_error="duplicate attempt identity",
                ),
                "duplicate provider attempt identity",
            )
        self._bound = bound

    def describe(self, request: R02SelectorRequest) -> tuple[R02D3PromptIdentity, bytes, tuple[str, ...]]:
        bound = self._require_bound(request)
        system_prompt, user_prompt, stdin_bytes = render_frozen_prompt(
            bound.preparation,
            self.preregistration,
        )
        argv = render_live_argv(self.preregistration, self.output_schema_path)
        identity = R02D3PromptIdentity(
            run_id=bound.authorization.run_id,
            fixture_id=bound.preparation.identity.fixture_id,
            attempt_id=bound.attempt_id,
            selector_request_sha256=canonical_sha256(request),
            system_prompt_sha256=sha256_hex(system_prompt.encode("utf-8")),
            user_prompt_sha256=sha256_hex(user_prompt.encode("utf-8")),
            stdin_sha256=sha256_hex(stdin_bytes),
            output_schema_sha256=sha256_hex(self.output_schema_path.read_bytes()),
            live_argv_sha256=sha256_hex(canonical_json_bytes(argv)),
            requested_model_id=self.preregistration.model_identity.requested_model_id,
        )
        return identity, stdin_bytes, argv

    def select(
        self,
        request: R02SelectorRequest,
    ) -> tuple[str, R02D3LiveTokenLedger, R02D3LiveTransportRecord]:
        bound = self._require_bound(request)
        self._require_runner_capability(bound)
        if bound.attempt_id in self._launched_attempt_ids:
            raise R02D3SelectorTransportError(
                "DUPLICATE_PROVIDER_CALL_BLOCKED",
                CodexProcessCapture(
                    stdout=b"",
                    stderr=b"",
                    exit_code=None,
                    duration_ms=0,
                    launch_error="duplicate attempt identity",
                ),
                "duplicate provider attempt identity",
            )
        prompt_identity, stdin_bytes, argv = self.describe(request)
        self._launched_attempt_ids.add(bound.attempt_id)
        capture = self.process_runner.run(
            argv=argv,
            stdin_bytes=stdin_bytes,
            working_directory=self.working_directory,
            timeout_ms=self.preregistration.budget_stop.live_timeout_ms,
        )
        if capture.timed_out:
            raise R02D3SelectorTransportError("TIMEOUT", capture, "selector process timed out")
        if capture.launch_error is not None:
            raise R02D3SelectorTransportError(
                "PROCESS_LAUNCH_FAILURE",
                capture,
                "selector process could not be launched",
            )
        try:
            parsed = parse_codex_jsonl(
                capture,
                requested_model_id=self.preregistration.model_identity.requested_model_id,
            )
        except CodexExecError as exc:
            raise R02D3SelectorTransportError(exc.code, capture, str(exc)) from exc
        disposition = complete_response_disposition(parsed)
        if disposition is not None:
            code = (
                "PROCESS_STATUS_VIOLATION"
                if parsed.process_status_violation
                else "TOOL_USE_VIOLATION"
            )
            raise R02D3SelectorTransportError(code, capture, disposition.value)
        if parsed.provider != "openai-codex-chatgpt-subscription":
            raise R02D3SelectorTransportError(
                "PROVIDER_IDENTITY_MISMATCH",
                capture,
                "parsed provider identity drift",
            )
        usage_values = (
            parsed.input_tokens,
            parsed.cached_input_tokens,
            parsed.output_tokens,
            parsed.reasoning_output_tokens,
        )
        accounting_total_tokens = parsed.input_tokens + parsed.output_tokens
        if (
            any(value > R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT for value in usage_values)
            or accounting_total_tokens > R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT
        ):
            raise R02D3SelectorTransportError(
                "USAGE_VALUE_OUT_OF_RANGE",
                capture,
                "reported usage exceeds the auditable integer bound",
            )
        external_provider_calls = 1 if bound.authorization.mode == "LIVE" else 0
        ledger = R02D3LiveTokenLedger(
            run_id=bound.authorization.run_id,
            fixture_id=bound.preparation.identity.fixture_id,
            attempt_id=bound.attempt_id,
            provider_attempt_ordinal=bound.provider_attempt_ordinal,
            input_tokens=parsed.input_tokens,
            cached_input_tokens=parsed.cached_input_tokens,
            output_tokens=parsed.output_tokens,
            reasoning_output_tokens=parsed.reasoning_output_tokens,
            accounting_total_tokens=accounting_total_tokens,
            external_provider_calls=external_provider_calls,
        )
        transport = R02D3LiveTransportRecord(
            run_id=bound.authorization.run_id,
            fixture_id=bound.preparation.identity.fixture_id,
            attempt_id=bound.attempt_id,
            selector_request_sha256=canonical_sha256(request),
            prompt_identity_sha256=canonical_sha256(prompt_identity),
            stdout_sha256=sha256_hex(capture.stdout),
            stderr_sha256=sha256_hex(capture.stderr),
            stdout_base64=base64.b64encode(capture.stdout).decode("ascii"),
            stderr_base64=base64.b64encode(capture.stderr).decode("ascii"),
            exit_code=capture.exit_code,
            timed_out=capture.timed_out,
            launch_error=capture.launch_error,
            duration_ms=capture.duration_ms,
            parsed_provider_response_sha256=canonical_sha256(parsed),
            raw_response_sha256=sha256_hex(parsed.raw_text.encode("utf-8")),
            external_provider_calls=external_provider_calls,
        )
        self._bound = None
        return parsed.raw_text, ledger, transport

    def _require_bound(self, request: R02SelectorRequest) -> R02D3BoundAttempt:
        if self._bound is None:
            raise ValueError("selector adapter has no bound attempt")
        if request.identity != self._bound.preparation.identity:
            raise ValueError("bound attempt and selector request identities differ")
        return self._bound

    def _require_runner_capability(self, bound: R02D3BoundAttempt) -> None:
        expected = (
            "LIVE_PROVIDER_PROCESS" if bound.authorization.mode == "LIVE" else "OFFLINE_FAKE"
        )
        actual = getattr(self.process_runner, "r02_d3_execution_capability", None)
        if actual != expected:
            raise R02D3SelectorTransportError(
                "RUNNER_CAPABILITY_MISMATCH",
                CodexProcessCapture(
                    stdout=b"",
                    stderr=b"",
                    exit_code=None,
                    duration_ms=0,
                    launch_error=f"expected {expected}, received {actual!r}",
                ),
                "process runner capability does not match authorization mode",
            )
