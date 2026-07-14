# R01 Phase B Implementation Plan v7 — Codex Development Pilot

> **DRAFT PLAN — DEVELOPMENT ONLY — NOT SEALED — NO INVESTMENT CLAIM**

## 1. Plan identity

- Plan ID: `R01-PHASE-B-PLAN-v7`
- Supersedes plan SHA-256: `45df0e378451b48458ef36075fd0abfdcd3342d6208e3d0eba2e6035c828b93b`
- Research contract: `docs/research-contract-01-llm-overlay.md`
- Contract SHA-256 before v7 hardening: `ec27c5dd17542dc837b5501b9e98a467d845277ed6051201e6221f6663de55c5`
- Base commit: `fe521fefcaf25475a7bd92c8626f6eccd6ca3033`
- Base branch: `codex/llm-overlay-research-01`
- Created: `2026-07-13`; revised: `2026-07-14`
- Status: `DRAFT`

This plan implements only Phase B of R01: a development-fixture pilot using one
Codex model through ChatGPT subscription authentication. It does not authorize
evaluation-fixture generation, sealing, a confirmatory run, historical
backtesting, paper trading, or live trading.

## 2. Decision already made

R01 will use **Option A**:

- acquisition surface: local `codex exec`;
- authentication: ChatGPT subscription sign-in;
- repository API-key integration: none;
- usage-based API spend: zero;
- research target: one explicitly selected Codex model overlay, not a generic
  claim about all LLMs or all providers;
- sampling: all user-visible settings are pinned; provider-managed settings that
  Codex does not expose are declared as such rather than inferred.

The official Codex documentation establishes that local Codex supports ChatGPT
subscription authentication, an explicit model selection, non-interactive JSONL
events, and turn-level token usage. The local planning environment currently has
`codex-cli 0.144.1`; the version used for the pilot remains a preflight decision
and must be recorded exactly.

References:

- <https://developers.openai.com/codex/codex-manual.md>
- <https://developers.openai.com/codex/noninteractive>

## 3. Phase B objective

Attach one real Codex acquisition path to the provider-free Phase A engine, use
only the 40 development fixtures to develop and select a prompt, measure
stability and resource use, freeze candidate statistical parameters, and
produce a Phase C seal-readiness package.

Phase B must answer:

1. Can Codex return executable portfolio decisions without using tools or
   external facts?
2. Are parse, schema, constraint, and fallback rates acceptable?
3. Is identical-prompt sampling noise low enough for the proposed invariance
   flip gate?
4. Does the final development effect support a prospective 200-case design with
   at least 80% power under the preregistered decision rule?
5. What token, attempt, and incremental-cash budgets must be sealed?

Phase B cannot answer whether the overlay has confirmatory incremental value.
Only the later sealed evaluation may answer that question.

## 4. Non-negotiable boundaries

- Use only manifests with `channel = development` and
  `DEVELOPMENT_ONLY_NOT_SEALED` status.
- Do not add a CLI command, function, seed, or import path capable of generating
  evaluation fixtures.
- Do not call the legacy backtester, live-data clients, market-data providers,
  or existing persona agents.
- Do not reuse prompt-cache results as independent acquisitions.
- Start a fresh ephemeral Codex process for every acquisition; never use
  `resume`.
- Store the complete provider transport and final response before parsing.
- Never overwrite an acquisition artifact.
- Do not silently repair an invalid order batch.
- Do not retry a complete response merely because it parses badly, violates the
  schema, uses a tool, or produces a poor decision. Such responses remain
  observed failures and execute as the fail-closed hold fallback.
- Stop before the next call whenever an attempt or resource guard would be
  exceeded.
- Keep Phase C seal, Phase D acquisition, and Phase E replay out of this plan.

## 5. Required contract amendments before live acquisition

The contract remains `DRAFT`, so the following amendments must be applied and
reviewed before the first real Codex call. The amended contract receives a new
SHA-256.

### 5.1 Codex policy identity

Codex CLI does not expose a caller-supplied system-role message. Therefore:

- record the Codex-managed system layer as `provider_managed_not_exposed`;
- rename or supplement `system_prompt_sha256` with
  `policy_instruction_sha256`;
- inject the current `SYSTEM_PROMPT_V1` content as a clearly delimited,
  user-level policy-instruction block before the fixture template;
- hash the exact UTF-8 instruction block and exact user template separately;
- define the evaluated policy as the resulting Codex agent configuration, not
  as a raw Responses API model call.

The prompt-role difference is a study limitation and must appear in the pilot
report and final interpretation.

### 5.2 Model and sampling identity

Freeze and report:

- `provider = openai-codex-chatgpt-subscription`;
- exact `codex --version` output;
- explicit `codex exec --model <MODEL>` string;
- exact reasoning-effort setting;
- exact service-tier setting when user-controllable;
- `temperature = provider_managed_not_exposed`;
- `top_p = provider_managed_not_exposed`;
- backend snapshot/version metadata when emitted, otherwise
  `not_exposed_by_provider`;
- operating system, Python version, and acquisition command-spec hash.

Absence of provider metadata must be represented explicitly. It must never be
reconstructed from release dates or model names.

The requested CLI model string is the authoritative user-controlled model
identity. If the transport echoes a different model, the acquisition fails
closed. If the transport does not echo a model, record
`model_identity_verified_by_transport = false`; the study may claim only the
requested Codex model surface, not a verified backend snapshot.

### 5.3 Cost accounting

Define `max_usd` as maximum **incremental usage-based provider spend** for R01.
Under ChatGPT subscription authentication:

- proposed `max_usd = 0`;
- the fixed subscription price is a pre-existing sunk cost and is not allocated
  per acquisition;
- token usage and subscription/quota interruptions are reported separately;
- no automatic fallback to API-key billing is allowed.

The zero-call preflight must also confirm that the selected ChatGPT workspace
cannot consume metered overage or purchased usage credits without a separate
user decision. If that cannot be established, `max_usd = 0` is not yet valid and
live acquisition remains blocked.

### 5.4 Retry eligibility

Clarify `unsuccessful acquisition` and retry behavior:

- every failed attempt receives one explicit disposition:
  `RETRY_TRANSPORT`, `FAIL_CLOSED_SCORE`, or `STOP_PHASE`;
- `RETRY_TRANSPORT`: process launch failure, timeout with no complete terminal
  response, nonzero CLI exit without a complete response, malformed JSONL
  transport, missing final agent message, or missing required usage record; a
  timeout/nonzero wrapper retains the original parser code and disposition;
- `FAIL_CLOSED_SCORE`: parse failure, decision-schema failure, duplicate asset, quantity
  violation, reasoning-length violation, tool-use violation, or poor utility;
- `STOP_PHASE`: artifact persistence or hash failure, forbidden channel, model
  mismatch, feature/catalog/sandbox mismatch, unknown event/item/field shape,
  and any complete transport with timeout or nonzero process status;
- a complete but invalid response is scored once as `ABSTAIN`/hold and counts in
  parse, fallback, and agreement metrics;
- a `STOP_PHASE` failure is never converted to `ABSTAIN` and never enters an LLM
  quality, fallback, or agreement metric;
- `successful acquisition` means a successful process status plus a complete
  provider transport with the required terminal response and usage evidence;
  it does not mean a valid or profitable policy decision;
- attempt 2 uses the same acquisition target and a new append-only attempt
  identity; attempt 1 remains immutable.

This prevents response-quality cherry-picking through retries.

### 5.5 Token accounting

Define authoritative fields from the terminal `turn.completed.usage` event:

- input tokens;
- cached input tokens;
- output tokens;
- reasoning output tokens when present;
- total measured tokens under a frozen formula.

The existing `ProviderResponse.input_tokens` and `output_tokens` remain, while
the additional categories are strict typed fields or required metadata. Missing
required usage fields fail closed.

The contract amendment must also state whether each input/output cap is
per-attempt, phase-cumulative, or R01-global. Cached and reasoning fields must
not be added to another category when the provider defines them as subsets. The
budget formula is frozen only after the emitted Codex usage schema is verified;
until then, every category is preserved separately.

### 5.6 Pre-provider statistical freeze

Remove all LLM-dependent freedom from the normalization and superiority margin
before the first provider call:

- compute `normalization_epsilon_e12` and `regret_scale_e12` in B0 using only
  deterministic development fixtures, the exact oracle, and hold;
- freeze their values and the complete derivation artifact before B2 completes;
- require the fixed B0 freeze SHA as a caller-supplied external trust anchor on
  manifest generation, every acquisition entry point, and replay; bind the
  development root-seed label to `r01-phase-b-development-fixtures-v1` and the
  fixture count to `40`;
- derive and hash a provider-free per-regime oracle-hold gap summary. D2 must
  explicitly accept the unchanged high-cost stratum and its prospective power
  cost or stop for a new provider-free contract and freeze;
- select and freeze `delta_min_e12` at D2 as a practical fraction of the already
  frozen oracle-hold scale, without observing any Codex response;
- freeze a deterministic `delta_target` rule at D2 before B3. The rule is
  `delta_target_e12 = delta_min_e12 + target_headroom_e12`, where
  `target_headroom_e12 > 0` is a user-approved practical value that cannot refer
  to observed LLM effects;
- amend contract Sections 2, 11, 12, 19, and the seal record so they no longer
  permit `delta_min` or the normalization scale to be selected after the pilot.

B5 may calculate normalized regret only from these frozen values. B7 verifies
their hashes and runs power; it cannot propose or alter them. This eliminates
the B5-to-B7 dependency cycle and prevents scale or margin selection from being
used to improve the observed result.

The 40 two-replicate development effects feed the existing prospective power
procedure without variance correction. Under the additive decomposition
`Var(mean_r) = sigma_between^2 + sigma_within^2 / r`, using `r = 2` instead of
the confirmatory `r = 5` mechanically adds `0.3 * sigma_within^2` to the case-
mean variance and tends to reduce estimated power. However, B4 selects for high
repeat agreement, which can select a lower-`sigma_within` prompt and act in the
opposite direction. The net bias is not known a priori. The no-correction choice
is frozen at D2 before power results are available; the report must present both
mechanisms and may call the result conservative only if a predeclared component
analysis supports that conclusion.

### 5.7 Claim scope

Amend contract Section 3 to prohibit generalization from the evaluated Codex
agent harness to:

- the same named base model called outside Codex;
- a raw Responses API model call;
- another Codex CLI version, personality, tool surface, provider, or auth mode;
- other LLMs or portfolio-manager agents.

R01 evaluates one complete Codex agent configuration. It does not isolate the
causal contribution of the underlying model weights.

### 5.8 Schema-version decision

Phase B adds provider transport, usage, policy-instruction, command-spec, and
binary-identity fields. B0 bumps the development manifest from
`r01-development-manifest-v1` to `r01-development-manifest-v2` because it now
binds the new `r01-provider-free-freeze-v1` artifact. Its replacement golden
hash is `d766076fe1928885b4b26ea1a7abd77b12280fb93d6795a6e9b2e00ce0e7cdf1`;
the nested freeze-reference golden is
`1251af89c5c84d7b857b3c0751bea88aa3deff13240d4913c8f28dd7d0a77d5d`,
and the standalone one-case freeze golden is
`472cf9d0e3015aeaed44beae2e10af86cd3771c832263015362c4e7440f1a643`.
Run-plan, run-result, replay, and report schemas remain v1 because B1 does not
change their fields. B1 initially allocated `r01-codex-command-spec-v1`,
`r01-codex-process-status-v1`,
`r01-codex-attempt-transport-artifacts-v1`, and the explicitly versioned
`r01-provider-response-v2` envelope. Pre-B2 hardening supersedes the affected
artifacts with `r01-codex-command-spec-v2` and `r01-provider-response-v3` to bind
the complete feature catalog, sandbox identity, transport-shape hash, model-echo
evidence, and observed transport-shape hash. Process-status and attempt-wrapper
v1 remain byte-compatible. Unrelated Phase A artifact versions retain byte
compatibility.

## 6. Carried hardening work — first Phase B commit

Close the final two review items before adding the live client:

1. Specify trailing-content behavior for `parse_json_object` with tests and one
   resolution-log entry. The intended policy is: surrounding prose may be
   ignored only when exactly one unambiguous valid decision object is recovered;
   duplicate valid candidate objects or ambiguous trailing objects fail closed.
2. Apply the shared artifact-relative path normalization to
   `scripted-template --output`; reject absolute paths, drive-qualified paths,
   `..`, empty segments, and `.` targets. Add parameterized CLI tests.

Completion gate:

- focused overlay tests pass;
- no behavior outside the R01 namespace changes;
- provider-free dry-run/replay behavior remains available, but every artifact
  schema affected by Section 5.8 receives an explicit new version and new golden
  hashes; only unaffected Phase A artifact versions retain byte compatibility.

## 7. Acquisition architecture

### 7.1 New modules

Recommended layout:

```text
v2/research/overlay/
  codex_exec_client.py       # subprocess adapter and JSONL transport parser
  pilot.py                   # development-only orchestration and budgets
  pilot_report.py            # deterministic pilot metrics and markdown
  prompt_candidates.py       # versioned instruction/template identities
  test_codex_exec_client.py  # mocked subprocess/transport tests only
  test_pilot.py
  test_pilot_report.py
```

The live adapter implements the existing `AcquisitionClient` protocol. Any
required response-envelope extension must be versioned rather than hidden in an
untyped dictionary.

### 7.2 Exact process contract

Construct the command as an argument vector, never through a shell:

```text
codex
  <generated --disable <feature> for every pinned catalog entry not in the D2 allowlist>
  exec
  --model <exact-model-id>
  --sandbox read-only
  --ephemeral
  --ignore-user-config
  --ignore-rules
  --skip-git-repo-check
  --strict-config
  --config tools.web_search=false
  --json
  -
```

Additional fixed `--config key=value` settings are permitted only when listed in
the command spec and hashed. The ordered argv, complete pinned feature catalog,
approved active-feature allowlist, generated disabled-feature list, effective-
true set, personality state, and every configuration value are included in
`command_spec_sha256`. The combined policy instruction and fixture prompt are
passed through stdin as UTF-8 bytes.

`--sandbox read-only` limits tool permissions; it does not remove tools. B2 must
therefore use an allowlist, not a hand-maintained blocklist:

1. run `codex features list` against the pinned binary and strictly parse every
   `(name, stage, enabled)` row: the first whitespace-delimited token is `name`,
   the final token is the boolean `enabled`, and every intervening token joined
   by one space is `stage` (including multiword stages such as
   `under development`); compare the parsed row count with the pinned catalog
   row count and block on any mismatch;
2. hash the complete catalog and baseline effective-true set;
3. generate `--disable` for every catalog name outside a D2-approved non-tool
   allowlist;
4. run `codex <generated disables> features list` and capture the resulting
   effective-true set;
5. block the first provider call if any effective-true feature is absent from
   the allowlist, if a catalog row is unparsed, or if the catalog hash changes;
6. use the identical generated disable list for every `codex exec` acquisition.

The desired allowlist is empty. D2 may add the minimum non-tool infrastructure
needed for ChatGPT authentication only after recording a per-feature rationale.
No tool, plugin, MCP, shell, browser, external-context, workspace-dependency, or
unknown/new feature may be allowlisted; inability to disable one reopens Option
A rather than becoming a prompt-tuning problem.

`enable_request_compression`, `remote_compaction_v2`, and `fast_mode` must also
be disabled. If the pinned CLI cannot disable one, D2 may accept it only as an
explicit limitation on prompt-byte fidelity or sampling identity. The feature
and rationale then become experiment identity.

On local `codex-cli 0.144.1`, the complete catalog has 92 rows: 30 `removed`,
29 `stable`, 27 `under development`, 3 `experimental`, and 3 `deprecated`.
The baseline effective-true set has 35 entries. Disabling all 92 catalog names
reports 88 false entries and four `removed` entries as true: `resize_all_images`,
`terminal_resize_reflow`, `tool_search_always_defer_mcp_tools`, and
`tui_app_server`. Their `removed` label is not proof of runtime inertness. B2
must establish that each is inert for noninteractive text-only execution or
stop Option A. `--strict-config` remains an `exec`-only guard and is not passed
to `features list`.

The plan must not substitute prompt wording for a removable feature control.

Do not use `--output-schema`: provider-side schema enforcement would suppress
the parse/schema failures R01 intends to measure. Do not use
`--output-last-message`; the runner extracts the final agent message from the
captured JSONL transport and stores the complete transport first.

Pin the Codex installation before B3. Record and verify before every acquisition
the launcher hash, package version and package metadata hash, resolved native
executable hash, and JSONL parser schema hash. Do not run `codex update`, package
updates, or automatic repair during R01. Any version, binary, dependency, or
event-schema drift stops the current development identity; after seal it
requires a new experiment ID and seal.

### 7.3 Isolation

Each process runs in a dedicated empty directory outside the repository tree so
repository `AGENTS.md`, source files, and user artifacts cannot enter context.
The directory contains no market data and no research outcome files.

Before each process:

- verify the resolved working directory is the expected pilot sandbox;
- verify it contains no `AGENTS.md`, `.codex`, or data file;
- use read-only sandbox mode;
- pass no secrets in argv, prompts, artifacts, or logs;
- set a frozen process timeout;
- preserve stdout JSONL, stderr, exit code, duration, and CLI version.

### 7.4 Transport validation

The JSONL parser must require exactly:

- one `thread.started` identifier;
- one completed turn;
- at least one final completed `agent_message`;
- one authoritative terminal usage object;
- no contradictory terminal status.

The last completed agent message is the policy raw response. Any command
execution, file change, MCP call, web search, browser call, or other external
tool event sets `tool_use_violation = true`. A completed response with such an
event is not retried; it fails closed to hold and remains in all quality rates.

### 7.5 Artifact order

For every attempt, write with exclusive creation in this order:

1. acquisition identity;
2. exact policy-instruction bytes;
3. exact fixture prompt bytes;
4. command spec without credentials;
5. stdout provider transport JSONL;
6. stderr bytes and process-status record;
7. extracted provider-response envelope;
8. parsed decision or parse-error artifact;
9. validation report;
10. executable fallback batch;
11. cost ledger and episode score;
12. acquisition index entry.

Replay never invokes `codex` and reads only sealed artifact bytes.

## 8. Development-only CLI

Add commands under the existing R01 CLI. Names are provisional until code
review, but behavior is fixed:

```text
pilot-preflight       # zero provider calls; environment and identity report
pilot-plan            # deterministic development acquisition plan
pilot-acquire         # execute only an approved development plan
pilot-report          # deterministic report from stored artifacts
pilot-power           # prospective power simulation from final pilot effects
```

`pilot-power` is only a thin I/O wrapper around the existing Phase A power
implementation. It must not duplicate its RNG, bootstrap, shifting, percentile,
or decision-rule logic; doing so would drift `analysis_spec_sha256`.

Every command must reject:

- a non-development manifest or identity;
- a manifest with an unexpected contract hash;
- an unapproved prompt/model/command-spec hash;
- a plan exceeding the development attempt envelope;
- an artifact path outside the configured root;
- overwrite or acquisition-key collision;
- evaluation, primary, or sealed status.

There will be no `generate-evaluation`, `seal`, or confirmatory acquisition
command in Phase B.

## 9. Provider-attempt envelope

The contract permits at most 200 development provider attempts, including all
prompt iterations and retries. Preallocate the budget before any call:

| Block | Initial attempts | Purpose |
| --- | ---: | --- |
| Prompt-candidate work | 36 | Up to three prompt versions on six regime-balanced fixtures, two repeats each |
| Final prompt full pilot | 80 | Forty development fixtures, two independent repeats each |
| Development nuisance audit | 30 | Six extra canonical anchor calls plus six anchors times four perturbations |
| Retry and interruption reserve | 54 | Transport-only retries and operational headroom |
| **Total cap** | **200** | Hard stop |

Prompt-candidate work may stop early. Unused attempts remain unused; they are not
reassigned after seeing favorable or unfavorable performance without a written
development decision record.

The six prompt/audit fixtures are selected deterministically before the first
call: one fixture per regime from the development manifest using a fixed rule
and a hashed anchor manifest.

Every planned development acquisition permits at most two attempts: one initial
attempt and one transport-only retry. No fixture, replicate, or perturbation may
consume more than its two-attempt allocation, even when global reserve remains.
Complete invalid responses are not retry-eligible.

Codex CLI does not expose a hard output-token flag. Before each call, the runner
therefore reserves a conservative per-attempt token allowance against a
provisional phase cap. It launches a call only when the remaining cap covers the
full reserve, applies the frozen process timeout, records actual usage, and
stops if an observed call exceeds its reserve. The provisional cap and reserve
require user approval at D2; neither may be inferred after seeing favorable
outputs.

## 10. Pilot sequence

### B0 — governance and offline hardening

- apply the contract amendments in Section 5;
- close the two carried review items in Section 6;
- generate the 40 development fixtures without provider access;
- compute and freeze `normalization_epsilon_e12`, `regret_scale_e12`, their
  derivation artifact, and the feasible-lattice certificates with zero provider
  calls;
- decide and document the required Phase B artifact-schema version bumps and
  golden-hash replacements;
- record the new contract SHA-256;
- review the amended contract and this plan;
- make zero provider calls.

#### B0 implementation record — 2026-07-14

- amended contract SHA-256:
  `3fac1bbe1973546f9f2fadcaf75df1b6678f4b7aab2bee778755de36f36f9a92`;
- provider-free freeze artifact: `docs/r01-b0-provider-free-freeze.json`,
  SHA-256 `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`;
- `normalization_epsilon_e12 = 100000000`,
  `median_oracle_hold_gap_e12 = 3136616200`, and
  `regret_scale_e12 = 3136616200`;
- feasible-lattice bundle SHA-256:
  `63e5d30f0acba50b69c3326c9a529abe456798ee4d8a3dd3d99f1264b3804c23`;
- global certified `max_abs_utility_e12 = 25088993397` and
  `max_normalized_regret_e12 = 9067403675655`;
- provider-free regime-gap summary:
  `docs/r01-b0-regime-gap-summary.json`, schema
  `r01-provider-free-regime-gap-summary-v1`, SHA-256
  `0e6e8945f93779a77ffc7687d63062c010efd3aee3d6c8062551e54108fbf886`;
- exact gap facts: `6/40` zero-gap cases, all in `high_transaction_cost`;
  that regime has seven cases, with one positive gap `600135403 > epsilon`, so
  it is near-degenerate `6/7`, not fully degenerate;
- carried parser-ambiguity and safe-output-path fixes closed with regression
  tests;
- no provider call made; B1, B2, D2, and all evaluation work remain blocked.

### B1 — mocked Codex adapter

- implement command construction and strict JSONL parsing;
- extend typed provider-response and artifact models;
- test success, timeout, nonzero exit, malformed JSONL, missing usage, duplicate
  terminal event, empty response, and tool-use violation;
- test retry eligibility separately from response-quality failure;
- use mocked subprocesses only.

#### B1 implementation record — 2026-07-14

- amended contract SHA-256:
  `946527fe1d6af2db3c9b11526c43472a9de9dd59ec84a41050ebafff25767b97`;
- added `codex_exec_client.py` with deterministic shell-free argv construction,
  exact stdin bytes, injected process runner, mandatory raw-capture sink, and no
  default subprocess implementation;
- strict JSONL parser SHA-256:
  `cf7ed097a3a8734485f7d229c57eb95a3fe594f5dcc5795b3793fb17332d1da4`;
- schema/golden identities: stable command spec
  `b13eda86e49ed60a6a80b149db2eaed4f418541a9d68ce9b5ef66890f73faf2e`,
  provider response
  `98f00424dcaae95aa452949cba7260e9988d442dd5274a90377d44528a190f57`,
  and process status
  `df1989e4c60454a542b4806b6fd718ee54144f771b74a12a095aa269ea60cb10`;
- local `codex-cli 0.144.1` help confirms every planned `exec` flag exists; no
  provider command was executed;
- mocked tests cover success, timeout, launch/nonzero failure, malformed and
  drifted JSONL, missing usage/final message, duplicate/contradictory terminal
  state, empty response, tool-use violation, response-quality no-retry,
  forbidden channels, and sink failure;
- all `75` focused overlay tests pass after B1;
- B2 feature-catalog/preflight work, D2 decisions, and all provider calls remain
  blocked.

#### H7/M12 pre-D2 hardening record — 2026-07-14

- require `--freeze-sha256` on manifest generation and every current
  acquisition/replay CLI; reject an alternate SHA, development root seed, or
  fixture count before any provider-capable path;
- load and verify the committed canonical B0 freeze in code rather than trusting
  a newly self-consistent manifest;
- commit the deterministic regime-gap summary above and add its schema/hash to
  the contract seal record;
- reserve the high-cost-stratum accept-or-restart choice for D2; no provider
  response may be observed first;
- updated contract SHA-256:
  `31e7948632fe492cd49f5c8b3f4eba1a9b7aa2355af16b2d5d01c04bea2d0570`;
- no provider call made.

#### H8/H9 and M13–M16 pre-B2 hardening record — 2026-07-14

- replace the retry boolean with `RETRY_TRANSPORT`, `FAIL_CLOSED_SCORE`, and
  `STOP_PHASE`; artifact sink and forbidden-channel failures are phase stops and
  cannot enter LLM fallback metrics;
- inspect model echoes at pinned event/item locations, verify matching echoes,
  record absence explicitly, and stop on mismatch;
- separate known tool items from unknown item types; pin allowed event/item
  fields and record each acquisition's observed transport-shape hash;
- add strict 92-row feature-catalog parsing, multiword-stage handling, complete
  disable/allowlist coverage, external catalog hash, and post-disable subset
  enforcement;
- require an externally anchored empty pilot sandbox outside the repository and
  reject secret-bearing config keys;
- schema identities: `r01-codex-command-spec-v2`,
  `r01-provider-response-v3`, JSONL schema
  `ba8751646f3f01a0806f23fe967cf8d5d4d2370fa89682c8a34d77efc0a698ff`,
  transport-shape spec
  `89537de83021a90cdd984b97899895325db3745fdf1e65855439845a747af462`,
  complete feature-catalog snapshot
  `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad`,
  and feature-catalog definition
  `aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530`;
- golden identities: stable command spec
  `497739b89a388dec7df584fcc3f3ec26cec4d43c57ff29f69c7ee2ab8d1e2f4c`
  and provider response
  `75f2157756cd3f6e7807ab00942c7f4be1c541ca31a313b797368c9221676963`;
- updated contract SHA-256:
  `ec27c5dd17542dc837b5501b9e98a467d845277ed6051201e6221f6663de55c5`;
- all `86` focused overlay tests pass; no provider call made.

#### Post-B2 disposition and reproducibility hardening — 2026-07-14

- parser-originated `STOP_PHASE` always dominates timeout/nonzero wrapping;
  retry wrappers retain the original parser code and disposition;
- complete transports with timeout or nonzero process status map to
  `STOP_PHASE`, not retry or hold, and the client consumes that classification
  before returning a response;
- generic key/session/private config markers and CR/LF/NUL separators are
  rejected, and recognizable secret-bearing config values are rejected; the
  feature parser applies the pinned name regex directly;
- every provider-free subprocess command has a fixed 30-second timeout;
- runner-raised `CodexExecError` and unexpected programming errors are not
  reclassified as retryable transport failures;
- `scripts/r01_b2_preflight.py` reproduces the zero-call facts and writes
  exclusive reversible raw captures plus canonical summary
  `docs/r01-b2-zero-call-capture.json`, SHA-256
  `409ee28ca3dc83aa69b6bacaefcd957c2c7641780af852f63ab8feb290c55242`;
- its subprocess runner uses an exact provider-free command allowlist and
  rejects plain `codex exec` before process launch;
- the global-flag probe `codex --disable shell_tool exec --help` succeeds on
  pinned `codex-cli 0.144.1`; its exact stdout preimage is committed;
- updated contract SHA-256:
  `33deed096d138b74e21a4761dca25cadc9a200bcfd17136d391c4b84f7377446`;
- all `96` overlay tests pass; no provider call made.

Validation scope: the `96`-test count is the provider-free overlay suite only.
The full v2 suite retains pre-existing live-data failures in `v2/data` and
`v2/event_study` when provider/network credentials are unavailable; those tests
are outside this Phase B gate and were not changed by this hardening.

### B2 — zero-call preflight

Produce a hashed preflight report containing:

- Codex CLI version;
- launcher, package, resolved native executable, and dependency-lock hashes;
- authentication mode confirmation without credentials;
- available/selected exact model string;
- user-visible reasoning and service settings;
- provider-managed setting declarations;
- the complete pinned feature catalog and baseline effective-true set;
- the proposed non-tool allowlist, generated disable set, post-disable
  effective-true set, and any unparsed catalog rows;
- shell, tool, plugin, MCP, browser, external-context, workspace-dependency, and
  personality removal status;
- `enable_request_compression`, `remote_compaction_v2`, and `fast_mode` status;
- evidence for or against runtime inertness of any still-true `removed` entry;
- command-spec hash, including the ordered argv and strict configuration;
- isolated working-directory proof;
- contract, prompt, code, and dependency identities;
- remaining development attempt and token budgets;
- the externally supplied B0 freeze SHA and proof that root seed and count match
  the committed freeze;
- the provider-free regime-gap summary and the explicit D2 accept-or-restart
  choice for the unchanged high-cost stratum.

Current zero-call observation on pinned local `codex-cli 0.144.1`:

- the complete B2 report is `docs/r01-b2-zero-call-preflight.md`, SHA-256
  `8cf6ed8f02681da68496d8762697769f34d2975fdf49b8d4e656a903b5c0a7f3`,
  anchored to provider-free hardening commit
  `fe521fefcaf25475a7bd92c8626f6eccd6ca3033`;
- the committed capture summary and reversible raw preimages reproduce both
  92-row catalogs and prove that global `--disable` before `exec` is accepted;
- `codex login status` reports ChatGPT authentication without exposing a
  credential;
- the strict parser reads all `92` rows and reproduces stage counts
  `30/29/27/3/3`, baseline effective-true count `35`, and catalog-definition
  snapshot/definition SHA-256 values
  `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad` and
  `aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530`;
- generated disable coverage spans all `92` names and preserves the catalog
  definition, but the post-disable result is `88` false and four still true:
  `resize_all_images`, `terminal_resize_reflow`,
  `tool_search_always_defer_mcp_tools`, and `tui_app_server`;
- therefore the desired empty allowlist correctly blocks command-spec creation.
  B2 remains `BLOCKED_PENDING_D2` until inertness is established or Option A is
  stopped; no prompt wording can override this gate;
- model-echo availability cannot be established without a provider transport.
  The parser is ready to verify or stop, and D2 must accept echo absence as a
  possible identity limitation before any authorized B3 call.

The timeout/nonzero rules are not discretionary D2 choices: a parser
`STOP_PHASE` is never downgraded, and a complete response with a process-status
violation is `STOP_PHASE`. D2 records acknowledgement of these frozen rules;
changing either requires a new plan and contract identity before any call.

User decision gate D2 selects the exact model and reasoning effort after this
report and approves the provisional development token cap and per-attempt
reserve. D2 also freezes `delta_min_e12`, `target_headroom_e12`, the resulting
`delta_target` rule, and the no-correction two-replicate variance policy before
the first provider call. D2 approves the minimal non-tool allowlist and any
unavoidable request-compression, remote-compaction, or fast-mode limitation. No
model fallback or unclassified effective-true feature is allowed. D2 must also
choose one of two provider-free outcomes: accept the anchored generator with the
`high_transaction_cost` `6/7` zero-gap stratum and record its power cost, or stop
and issue a new contract and freeze. It cannot exclude, rebalance, or alter that
stratum after a Codex response exists.

### B3 — 12-call micro-pilot

Run prompt candidate v1 on the six regime-balanced fixtures, twice each.
Measure:

- transport completion;
- tool-use violations;
- parse/schema/constraint failures;
- hold fallback;
- token categories and process duration;
- action disagreement;
- regret and delta versus the deterministic primary baseline.

The preregistered tool-use threshold is zero. If any of the 12 responses emits a
tool event, stop the micro-pilot and reopen the user decision on Option A. Do not
use the remaining prompt budget to tune wording until tool use disappears. Other
structural transport failures may be corrected under a new development
experiment identity. Every prior call and prompt version remains recorded.

Before the first B3 call, the runner must consume
`complete_response_disposition` for every complete response. A
`FAIL_CLOSED_SCORE` result must enter the hold scorer exactly once; if no
consumer is wired, B3 is blocked and no call is authorized.

### B4 — bounded prompt iteration

- permit at most three total prompt versions in the 36-attempt candidate block;
- change only the policy instruction and user template;
- prohibit scorer, oracle, fixture, baseline, and metric changes motivated by
  prompt results;
- prohibit use of normalized regret, delta, oracle proximity, or any other
  performance outcome in prompt selection;
- record the reason and diff for each prompt version;
- select the final prompt using the following ordered criteria:
  1. no tool-use or executable constraint violation;
  2. lowest parse-plus-fallback rate;
  3. highest identical-repeat action agreement;
  4. lower measured token use.

Later criteria cannot override an earlier criterion. Exact ties use the earlier
prompt version. This selection rule is frozen before candidate v2.

User decision gate D3 approves the final prompt hash. After approval, no further
prompt edit is permitted within R01 without a new development decision record;
after Phase C seal, any edit requires a new experiment ID and seal.

### B5 — final 40-fixture development pilot

- run the approved prompt twice on every development fixture;
- use fresh ephemeral processes and distinct replicate identities;
- do not replace parse failures or poor decisions;
- compute pairwise micro action agreement over the two repeats;
- compute per-case replicate mean scores using the frozen integer arithmetic;
- preserve per-regime and aggregate results.

For development case `c`:

```text
NR_llm_dev_e12(c) = round_ratio_half_even(NR_rep_0_e12 + NR_rep_1_e12, 2)
Delta_dev_e12(c) = NR_primary_deterministic_e12(c) - NR_llm_dev_e12(c)
```

These 40 exploratory case effects feed the prospective power procedure. They
do not replace the confirmatory five-replicate case definition.

The pairwise development disagreement is an estimate of the sampling-noise
floor. It is not the confirmatory five-replicate metric.

The raw two-replicate case effects are used without variance correction in the
frozen Phase A power procedure. Report the observed within-pair squared
difference, the mechanical `r = 2` versus `r = 5` variance increment, and the
opposing prompt-selection effect. Do not assume their net direction and do not
modify the 40 effects after inspecting power.

Measure completed attempts per hour, cooldown and rate-limit events, retry
latency, and observed quota headroom. The seal-readiness package must estimate
whether one immutable Phase D run can acquire 1,160 required responses within
the 1,280-attempt primary-plus-invariance cap. If quota feasibility cannot be
supported, Phase B returns `NOT_READY_FOR_PHASE_C`.

Convert observed sustainable throughput into optimistic, central, and adverse
calendar-duration estimates, including enforced cooldown windows and a retry
allowance. Report the expected start-to-finish calendar days for Phase D and the
risk that the selected model, backend identity, subscription quota, or CLI
surface changes during that interval. D6 must choose a contingency before seal:
shorten the run through a pre-seal design/budget change, accept the quantified
availability risk, or decline to seal. A model change during the immutable run
cannot be repaired by switching models.

### B6 — development nuisance audit

For each of the six preselected anchors, first acquire one additional canonical
response. Combined with the two B5 responses, this yields three canonical
replicates. The development anchor is the per-asset modal action across those
three responses; a three-way tie becomes `ABSTAIN`. Then acquire one response
for each frozen perturbation type:

- asset order;
- signal order;
- JSON key order/representation;
- wording-only representation transform.

Compare each inverse-mapped perturbed response with the three-replicate
development anchor. Report both:

- the unconditional three-modal-anchor flip rate using the evaluation metric's
  `ABSTAIN` treatment; and
- a diagnostic unanimous-anchor flip rate restricted to assets on which all
  three canonical responses agree, with its denominator and exclusion rate.

Neither statistic is level-equivalent to the sealed five-replicate modal-anchor
flip rate. No numeric conversion to the five-replicate 5% gate is identifiable
from three replicates, so both are diagnostics rather than a gate pass. D6 must
accept this residual uncertainty, amend the design on independent grounds, or
decline to seal. Do not reinterpret the relationship after seeing evaluation
data.

### B7 — thresholds and power

Create a decision package, not an automatic seal:

- verification of the pre-provider `delta_min_e12`, `delta_target` rule,
  `normalization_epsilon_e12`, and `regret_scale_e12` hashes;
- final quality thresholds and exact metric formulas;
- input/output/total token caps;
- final attempt and incremental-USD caps;
- `scoring_spec_sha256`, `analysis_spec_sha256`, and
  `gate_metric_spec_sha256`;
- the preregistered 1,000-simulation prospective power result for 200 cases.

Execution order is mandatory:

1. verify the B0/D2 statistical identities without changing them;
2. invoke the existing Phase A power implementation as a wrapper; do not
   reimplement or alter it;
3. if power is below 80%, increase prospective sample size and dependent budgets
   through a contract amendment or stop R01;
4. never lower `delta_min`, change `delta_target`, or variance-correct the
   observed effects merely to pass the power gate.

User decision gate D4 approves the remaining quality and final resource caps;
it cannot reopen B0/D2 quantities. Decision gate D5 approves any sample-size or
budget expansion.

### B8 — quality-gate evidence limit

Phase B cannot statistically establish the sealed `parse + fallback <= 1%`
gate. Even with zero failures, the rule-of-three 95% upper bound is:

- `3 / 80 = 3.75%` for the final canonical development acquisitions; and
- `3 / 24 = 12.5%` for the development perturbation acquisitions.

The contract's evaluation gate is an observed-rate rule, not a confidence-bound
rule, but the development sample cannot demonstrate that its true rate is below
1%. The 200-attempt development cap is also too small to obtain the roughly 300
zero-failure observations needed for a sub-1% rule-of-three upper bound.

D6 must record exactly one outcome before Phase C:

1. accept the residual risk while retaining the 1% evaluation gate and making
   no claim that Phase B validated it;
2. amend the gate for an independent methodological reason documented before
   evaluation fixtures exist; or
3. decline to seal R01.

Unused retry reserve cannot be described as solving this evidence limitation.

## 11. Pilot report

Add a deterministic `r01-development-pilot-report-v2` JSON artifact and matching
Markdown view. At minimum report:

- all prompt versions and hashes;
- model, CLI, command, OS, and dependency identities;
- launcher, package, resolved native executable, and JSONL-schema identities;
- requested and effective disabled-feature states and personality state;
- provider-managed/unexposed settings;
- planned, attempted, completed, retried, and failed acquisition counts;
- retry reasons;
- tool-use violations;
- parse, schema, constraint, fallback, and abstention rates;
- pairwise micro action agreement;
- nuisance flip rates by transform and in aggregate;
- unconditional three-modal and unanimous-anchor diagnostic flip rates;
- per-case and per-regime normalized regret;
- delta versus every registered baseline;
- input, cached-input, output, reasoning-output, and total tokens;
- token distributions and process durations;
- throughput, cooldowns, quota interruptions, and Phase D completion estimate;
- optimistic, central, and adverse Phase D calendar-duration estimates plus
  model-retirement and model-rotation risk over those intervals;
- incremental USD spend and accounting basis;
- prospective power results;
- the frozen `r = 2` no-variance-correction decision, the mechanical variance
  increment, the opposing agreement-selection effect, and the resulting
  direction uncertainty relative to `r = 5`;
- rule-of-three bounds and the explicit 1% gate residual-risk decision;
- proposed seal fields with source-artifact references;
- unresolved limitations and a Phase C readiness verdict.

The report status remains `DEVELOPMENT_ONLY_NOT_SEALED`. A favorable development
result is not a GO verdict.

## 12. Tests and validation

### Unit tests

- deterministic command construction and command-spec hash;
- strict parsing and hashing of the complete feature catalog;
- parsing of multiword stage labels such as `under development`, plus a
  regression test proving that one missing catalog row blocks the preflight;
- generated disable coverage, active-feature allowlist enforcement, and
  effective-true subset verification;
- pinned launcher/package/native-binary/JSONL-schema identity checks;
- stdin byte identity;
- JSONL event parsing and final-message extraction;
- strict usage accounting;
- tool-event detection;
- retry eligibility matrix;
- development-only channel guard;
- attempt-ledger exhaustion;
- two-attempt maximum for every development acquisition;
- append-only artifact ordering and tamper detection;
- report determinism and golden hashes;
- prompt-candidate selection ordering;
- trailing-content and output-path carryovers.

### Integration tests

- fake `codex` executable emitting controlled JSONL;
- unparsed/new feature rows and catalog-hash drift;
- effective feature present outside the approved allowlist;
- tool/context feature that remains true despite generated disable flags;
- version, binary, or JSONL-schema drift between acquisitions;
- subprocess timeout and nonzero-exit behavior;
- raw transport written before parser invocation;
- replay proves zero provider calls;
- a complete invalid response is not retried;
- evaluation/primary acquisition attempts are rejected;
- no command can generate evaluation fixtures.

### Live smoke test

Only after B0-B2 review, run one explicitly authorized development acquisition.
Verify artifacts, token usage, tool prohibition, replay, and budget accounting
before authorizing the 12-call micro-pilot.

### Regression gates

- all existing R01 overlay tests pass;
- all new Phase B offline tests pass;
- no new failure appears in the repository's offline test set attributable to
  R01;
- existing unrelated live-data failures remain outside scope and are not
  relabeled as R01 failures.

## 13. Commit sequence

1. `fix: close remaining R01 Phase A review items`
2. `docs: freeze R01 provider-free scale and margin decisions`
3. `docs: align R01 contract and schema versions with Codex subscription pilot`
4. `feat: add mocked Codex acquisition adapter`
5. `feat: add R01 development pilot runner and budgets`
6. `feat: add R01 pilot metrics and report`
7. `test: harden R01 Phase B fail-closed boundaries`
8. `docs: record R01 micro-pilot decision`
9. `docs: record R01 development pilot and seal proposal`

Code commits must precede the live pilot. Raw provider artifacts remain under
the gitignored append-only artifact root. Tracked reports contain hashes and
summaries, not credentials or hidden provider data.

## 14. User decision gates

| Gate | User decision | Evidence supplied by Codex |
| --- | --- | --- |
| D1 | Acquisition route | **Decided:** Option A, Codex CLI with ChatGPT subscription |
| D2 | Exact model, reasoning effort, minimal active-feature allowlist, request-compression/remote-compaction/fast-mode limitations, `delta_min`, `delta_target` rule, no-correction variance policy, provisional token cap and reserve, and accept-or-provider-free-restart decision for the unchanged high-cost gap stratum | Externally anchored provider-free scale and regime-gap artifacts, complete feature-catalog diff, and zero-call preflight |
| D3 | Final prompt | Candidate comparison, hashes, failures, token use |
| D4 | Remaining quality thresholds and final token/resource caps | Development pilot decision package; B0/D2 statistics cannot reopen |
| D5 | Sample/budget expansion if power <80% | Frozen power simulation result |
| D6 | Proceed to Phase C seal and accept, amend, or reject the 1% gate, anchor-comparability, quota, calendar-duration/model-availability, and model-identity residual risks | Complete Phase B exit checklist and quantified limitations |

No other ordinary implementation choice requires user intervention unless it
changes the research question, provider surface, budget authority, or
fail-closed behavior.

## 15. Phase B exit criteria

Phase B is complete only when all are true:

- amended contract and implementation have been reviewed against their exact
  hashes;
- the two carried Phase A review items are closed;
- provider-free `normalization_epsilon`, `regret_scale`, `delta_min`, and
  `delta_target` rule were frozen before the first provider call;
- all affected artifact schemas were explicitly version-bumped and their golden
  hashes regenerated with a resolution-log entry;
- one model, CLI version, reasoning setting, policy instruction, user template,
  and command spec are selected;
- the pinned launcher, package, resolved native executable, and JSONL schema
  hashes match every acquisition;
- the complete pinned feature catalog is parsed and hashed; the effective-true
  set is a subset of the D2-approved non-tool allowlist;
- every tool/plugin/MCP/shell/browser/external-context/unknown feature is false,
  and any accepted transport or serving transformation is explicit identity;
- all 40 development fixtures have at least two final-prompt acquisitions;
- the development nuisance audit is complete;
- total development attempts do not exceed 200;
- all raw transports and derived artifacts pass integrity verification;
- token use and incremental cost are measured under documented formulas;
- observed throughput and quota headroom support the planned immutable Phase D
  acquisition, or Phase B is `NOT_READY_FOR_PHASE_C`;
- identical-prompt noise and perturbation flips are reported together;
- thresholds and metric implementations are frozen as candidate seal fields;
- D6 records the 1% quality-gate evidence limitation and the three-versus-five
  replicate anchor limitation;
- prospective power is at least 80%, or a pre-seal sample/budget amendment has
  been approved and rerun;
- no evaluation fixture exists;
- the Phase B report says either `READY_FOR_PHASE_C` or
  `NOT_READY_FOR_PHASE_C`, with no investment-performance claim.

## 16. Stop conditions

Stop Phase B immediately when:

- a non-development fixture or identity reaches the acquisition client;
- Codex authentication would fall back to API-key billing;
- the exact requested model is unavailable or the transport reports a different
  model; absence of a transport model echo is recorded as an explicit
  limitation rather than treated as proof;
- the pinned Codex launcher, package, native executable, dependency, command
  spec, or JSONL schema hash changes;
- any micro-pilot response emits a tool event;
- the feature catalog cannot be parsed, its hash changes, or the effective-true
  set contains a name outside the D2-approved allowlist;
- a tool, plugin, MCP, shell, browser, external-context, workspace-dependency,
  or unknown/new feature remains true;
- the process emits an unrecognized terminal transport state;
- append-only artifact creation or hash verification fails;
- the next call would violate an attempt or reserved-token guard;
- provider output omits required identity or usage evidence;
- evaluation-fixture generation becomes reachable;
- implementation changes the oracle, scorer, baseline, or generator based on
  observed LLM performance without an explicit contract amendment;
- observed quota or rate-limit behavior cannot support one immutable Phase D
  run and no pre-seal redesign has been approved;
- the user declines a required decision gate.

A stopped development pilot may be corrected and rerun only under a new
development experiment identity with all prior artifacts preserved. It cannot
be relabeled as a successful pilot.

## 17. Plan v2/v3/v4/v5/v6 review resolution log

| Review finding | Resolution |
| --- | --- |
| H1: B5 normalized regret depended on a B7 regret scale | Freeze `normalization_epsilon_e12` and `regret_scale_e12` provider-free in B0; B7 verifies only. |
| H2: post-pilot `delta_min` allowed outcome-aware margin selection | Freeze `delta_min_e12` and the `delta_target` rule at D2 before the first Codex response. |
| H3: read-only sandbox left Codex tool surfaces enabled | Generate disables from the complete pinned feature catalog, enforce an approved active-feature allowlist, hash both sets, and stop on any micro-pilot tool event. |
| H4: 80 calls cannot establish a 1% true failure rate | Add rule-of-three bounds and require an explicit D6 accept, independently justified amendment, or no-seal decision. |
| M1: prompt selection could bias the power distribution and `delta_target` was undefined | Remove regret/delta from prompt selection and freeze a provider-independent target-headroom formula at D2. |
| M2: two-repeat development anchor was not comparable with the five-repeat modal anchor | Add a third canonical response for six anchors, report three-modal and unanimous-anchor diagnostics, and prohibit direct equivalence claims. |
| M3: two-repeat case effects inflate variance versus five repeats | Freeze no variance correction before calls; report the mechanical inflation, opposing agreement-selection effect, and indeterminate net direction. |
| M4: ChatGPT quota might not support 1,160 required Phase D responses | Measure throughput, interruptions, and quota headroom; require a Phase D completion estimate for seal readiness. |
| M5: Codex auto-update or JSONL drift could break the sealed parser | Pin and repeatedly hash launcher, package, native executable, dependencies, command spec, and JSONL schema; drift is a stop condition. |
| M6: development retry reserve lacked a per-acquisition limit | Limit every development acquisition to one initial attempt plus one transport-only retry. |
| M7: provider and usage fields implied an unacknowledged schema change | Require explicit schema-version bumps and resolution-logged golden-hash regeneration in B0. |
| M8: claim scope did not exclude generalization beyond the Codex harness | Require a contract-level prohibition on base-model, raw-API, other-version, and other-agent generalization. |
| LOW: `pilot-power` could duplicate Phase A analysis | Restrict it to a thin wrapper around the existing hashed implementation. |
| H5: the 15-name blocklist left 20 effective-true features | Replace the blocklist with complete-catalog enumeration, generated disables, and an effective-true allowlist gate; classify transport transforms at D2. |
| M9: quota feasibility lacked Phase D calendar and model-retirement risk | Produce three calendar-duration scenarios and require a D6 availability-risk contingency. |
| M10: two-replicate power was called unconditionally conservative | Document the mechanical variance increase, opposing agreement-selection effect, and unknown net direction. |
| M11: Section 6 retained conditional Phase A byte-compatibility language | Require new versions and golden hashes for every affected schema; preserve compatibility only for unaffected versions. |
| H6: the validation parser silently dropped all 27 `under development` rows | Correct the pinned catalog facts to 92 rows; parse first token/name, final token/enabled, and the complete middle/stage; require an exact pinned row-count match and regression-test both a multiword stage and a missing row. |
| H7: the committed B0 freeze was reproducible but not an externally enforced code anchor | Require the caller-supplied fixed freeze SHA on generation, acquisition, and replay; load the committed canonical artifact; reject alternate root seed and count before provider-capable execution. |
| M12: six zero oracle-hold gaps were concentrated in the high-cost stratum | Commit exact per-regime gap statistics, correct the claim to six zero gaps among seven high-cost cases, and require D2 to accept the prospective power cost or restart provider-free. |
| H8: model identity was never verified from transport | Inspect pinned event/item model fields; matching echoes verify, absence is explicit, and mismatch stops the phase. Zero-call B2 records that echo availability remains empirically unknown. |
| H9: `retry_eligible` conflated scoring and harness failures | Replace the boolean with three dispositions and prohibit `STOP_PHASE` failures from entering hold/fallback metrics. |
| M13: unknown item types were charged to LLM fallback | Maintain separate known non-tool/tool item sets; known tools fail closed to score, unknown items stop as schema drift. |
| M14: known events accepted unknown internal fields | Hash a pinned field-shape spec, enforce it per event/item, and retain an observed-shape hash per acquisition. |
| M15: pilot sandbox isolation was only documented | Require an empty nonsymlink directory outside the repository and bind its external identity before spec creation. |
| M16: command specs did not prove full catalog coverage | Bind all catalog entries and the external definition hash into command-spec v2; require exact disable/allowlist coverage and a post-disable subset. |
| LOW: config overrides could persist secrets | Deny secret-bearing config key markers before argv or artifact construction. |
| MEDIUM: timeout/nonzero wrapping could hide `STOP_PHASE` parser causes | Preserve `STOP_PHASE` precedence; wrap only retry-eligible failures and retain the original code/disposition. |
| MEDIUM: complete process-status violations had no consumed disposition | Classify them as `STOP_PHASE` in the client before response return; never score them as hold. |
| LOW: generic secret config names and control separators passed validation | Deny key/session/private markers and CR/LF/NUL in executable, model, and config inputs. |
| LOW: feature-name syntax was enforced only by downstream schema validation | Apply the same pinned regex during catalog parsing and retain the schema validator as a second check. |
| INFO: global `--disable` placement and catalog preimages were undocumented | Commit a zero-call reproducer, reversible raw captures, canonical summary, and exact global-flag help evidence. |
| MEDIUM: B2 subprocess commands could hang indefinitely | Bound every provider-free command to 30 seconds and fail the preflight closed on expiry. |
| MEDIUM: config values could contain recognizable provider secrets | Scan values for API-key, bearer, token, password, and provider-token patterns as well as scanning keys. |
| LOW-MEDIUM: runner exceptions were all reclassified as retryable | Preserve `CodexExecError`, retry only OS/subprocess launch errors, and propagate unexpected programming errors. |
| LOW-MEDIUM: `FAIL_CLOSED_SCORE` had no downstream consumer | Make disposition consumption and one-hold scoring a hard B3 precondition. |
