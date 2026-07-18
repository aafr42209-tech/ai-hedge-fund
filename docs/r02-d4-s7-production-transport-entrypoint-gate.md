# R02 D4-S7 Provider-Free Production Transport and Entrypoint Gate

Status: `PROVIDER_FREE_DRAFT_NOT_LIVE_AUTHORIZED`

Base commit: `c88bde40015d88bf31f4af25587c339359971f2e`

This gate implements the production transport boundary and a provider-free
entrypoint preparation path. It does not create a LIVE authorization artifact,
materialize either production root, start Codex, call a provider, expose an
interim outcome, or execute the 69-case run.

## 1. Frozen predecessor contract

S7 does not change S6. The S6 prepared plan remains 69 eligible cases in frame
ordinal order, with one 32,000-token reservation per case, a 2,208,000-token
aggregate cap, 900,000 ms per attempt, at most six settled fail-closed results,
and no micro-pilot, retry, replacement, or resume. The complete prepared-plan
digest remains
`188c971db338d5456c72a1e6e71801119dd8f992dd90fd86c3952f09121cffc9`.

The canonical S7 contract is
`docs/r02-d4-s7-production-gate-contract.json`, SHA-256
`c2b4b729e77690c3f02d28de503d4172e038d19b7230c954b8f2e4b167deb2b1`.
It pins the accepted S6 commit, all S5/S6 trust inputs, all three production S7
modules, and the exact output-schema file.

## 2. Production transport

`R02D4S7CodexTransport` implements the S6 transport protocol. It:

- reconstructs the exact D3 system prompt, user template substitution, stdin,
  disabled-feature argv, model, reasoning effort, read-only sandbox, ephemeral
  mode, strict config, and `tools.web_search=false` setting;
- requires the S6 timeout argument to equal 900,000 ms;
- rejects a request that differs from the sealed S6 preparation hash;
- records an attempt identity before invoking the injected process runner and
  rejects a duplicate identity before any second process call;
- parses the complete Codex JSONL using the accepted strict parser, including
  the single terminal-usage event and input/output subset accounting rules;
- converts timeout, launch failure, nonzero exit, malformed transport, model or
  tool drift, missing/duplicate usage, and evidence-persistence failure into the
  existing S6 unsettled hard-stop path; and
- returns only the S6 typed transport result. It cannot add retry, replacement,
  resume, or a partial-run continuation mechanism.

The production process wrapper exists but is never constructed by module import
or provider-free verification. All S7 tests inject a fake process runner.

## 3. Two response-schema identities

The D3 preregistration records the predecessor response-schema identity
`5466a24d...b2eca`. The accepted D3 successor adapter exports the canonical
runtime JSON Schema bytes with SHA-256 `f8089e66...6937`. These are separate
historical identities, not aliases. S7 requires both: the preregistered identity
must remain in the D3 record, while the absolute `--output-schema` path must
contain the byte-exact successor export in
`docs/r02-d4-s7-selector-output-schema.json`.

## 4. Audit-root separation

The S6 audit root is a closed replay domain. Adding a transport file beneath it
correctly fails S6 replay as an orphan artifact. S7 therefore uses two exact,
run-bound roots:

```text
.research_artifacts/r02-d4-s6-{run_id}
.research_artifacts/r02-d4-s7-transport-{run_id}
```

The first contains only the accepted S6 payload/node/anchor graph. The second
contains append-only, exclusive-create transport evidence with full stdout and
stderr bytes, hashes, prompt/argv identities, process status, usage-event count,
parse disposition, and conservative external-call accounting. Both roots must
be absent or empty at preparation and materialization. A file in either root
blocks retry and resume.

Transport evidence is fsynced before a successful result returns to S6. If that
write fails after a possible launch, S6 conservatively accounts the attempt and
hard-stops; it does not score an unbound response.

## 5. Entrypoint gate and authorization

`prepare_production_entrypoint` is read-only. It verifies exact root names,
empty roots, sealed inputs, current D3 zero-call identity captures, executable
bytes, the canonical schema, the 69-case plan, and two canonical external
authorization files. It returns a frozen prepared object with
`production_root_materialized=false` and `provider_process_started=false`.

A future S7 authorization must bind:

- the exact S6 LIVE authorization bytes and accepted S6 review;
- the accepted S6 implementation commit;
- a future accepted S7 commit and independent-review digest;
- the canonical S7 contract digest; and
- the indivisible all-69 scope, both production roots, no micro-pilot, no retry
  or replacement, and no resume.

Preparation is not execution authorization. Preparation requires the repository
HEAD to equal the S7-authorized implementation commit and the worktree to be
clean. `materialize` re-runs the commit/clean-state, current identity, and
executable checks immediately before it can construct the LIVE process wrapper
and S6 runner. S7 intentionally creates no standalone LIVE CLI; future
invocation remains a separately reviewed and explicitly authorized gate.

No LIVE authorization artifact exists in this draft.

## 6. Provider-free verification

The exact focused manifest contains 150 tests. S7-specific tests use only fake
process captures and temporary roots, including a complete 69-case S6 run with
separate S6 audit and S7 evidence roots. Negative tests cover duplicate launch,
timeout, nonzero exit, duplicate usage, schema drift, capability injection,
noncanonical or cross-unbound authorization, root drift, identity drift, and
executable drift.

The verifier command is:

```powershell
.venv\Scripts\python.exe scripts\r02_d4_s7_provider_free_verify.py
```

Expected status:
`PASS_S7_PROVIDER_FREE_PRODUCTION_GATE_REPRODUCED`.

This draft is ready only for independent provider-free review. Commit, push,
LIVE authorization creation, production-root materialization, Codex exec, and
provider execution remain outside S7 authority.
