# R01 B3 Transport-v3 Provider-Free Preflight Readiness

Status: `READY_FOR_EXTERNAL_REVIEW_PROVIDER_CALLS_ZERO`

The first live B3 acquisition stopped before scoring after pinned Codex CLI
`0.144.1` emitted three deprecation diagnostics ahead of `turn.started`. That
attempt remains immutable stopped evidence. This replacement preflight uses a
new experiment identity and artifact root, pins the exact observed diagnostic
triple in transport parser v3, and carries the prior attempt and conservative
token charge into every new budget boundary.

Do not run `b3-run` until an independent reviewer approves the pair:

- implementation commit: `af8381f`;
- B3 preflight SHA-256:
  `e86c75659b1dc54e16722d2ee37403e0c6fba3f59318d00103fb84ad79823d09`.

The earlier review through `a4b52f5` does not authorize another provider call.

## Code, contract, and incident identity

- Transport remediation commit: `02fafa1` (`fix: pin B3 deprecation diagnostics`).
- Global-budget carry-forward commit: `af8381f`
  (`fix: carry B3 budgets across experiments`).
- Research contract: `docs/research-contract-01-llm-overlay.md`, SHA-256
  `f0c29d0bb4c6e55673206f3d1c3415f82318cdc0fcb8208df568df00e528a5a1`.
- First-call STOP report: `docs/r01-b3-first-call-stop.md`, SHA-256
  `5c14367d0ef4923cecd6f6334a9e7c54afd0d3e6e7966938c8790a4659ed4cc3`.
- Development-budget carry-forward:
  `docs/r01-b3-budget-carry-forward.json`, SHA-256
  `13872058b922736e31c83e54ecbf8c17e36c20f68205ab249a9883b954248507`.
- Zero-cost account attestation:
  `docs/r01-b3-zero-cost-account-attestation.md`, SHA-256
  `94ca690340273e02da7de19e0c1ea5efc8793547f2a87822dc40eb5b630b9746`.

## Replacement preflight trust anchors

- Artifact root: `.research_artifacts/r01-b3-af8381f`.
- Experiment ID: `r01-b3-prompt-v1-transport-v3-20260716`.
- Development manifest SHA-256:
  `74b273ec154e675a89a699c076002c784da268c2590816403cd831fd8e640005`.
- Provider-free fixture freeze SHA-256:
  `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`.
- B3 anchor manifest SHA-256:
  `7c0c38d6c454be39cc19076e79ecc0578f9a3bdc275e52a6d1f6973bfabf1d8f`.
- Feature gate SHA-256:
  `f9cf5c8b3abed7f594941122bfc4a844a0cbd2c884eed516bed9f5da3258d0a6`.
- Native executable SHA-256:
  `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`.
- Empty pilot-sandbox identity SHA-256:
  `2c2e2693513098def82799b7554129e3826f06de71d6e3fcd8d79add4c5cc97d`.
- B3 preflight schema: `r01-b3-preflight-v2`.
- B3 preflight status: `READY_FOR_REVIEW_PROVIDER_CALLS_ZERO`.
- B3 preflight SHA-256:
  `e86c75659b1dc54e16722d2ee37403e0c6fba3f59318d00103fb84ad79823d09`.

The manifest binds the current research-contract hash. The preflight binds the
manifest, anchor manifest, feature gate, six command specs, executable,
attestation, carry-forward document, and inline carry-forward state. The live
builder rehashes the executable, attestation, carry document, feature gate, and
empty sandbox before constructing a client.

## Global development-budget carry-forward

The replacement root does not reset development counters:

- prior provider attempts: `1`;
- prior successful responses: `0`;
- prior failed or unsettled attempts: `1`;
- observed unsettled actual tokens: `13,651`;
- conservative carried charge: `32,000`;
- first possible new provider-attempt ordinal: `2`;
- development attempt cap: `200`;
- development token cap: `6,400,000`;
- per-attempt reserve: `32,000`;
- B3 planned acquisitions: `12`;
- B3 maximum provider attempts: `24`;
- worst-case global attempts after this B3: `25`;
- worst-case conservative charge after this B3: `800,000`.

The carry record transitively binds the stopped experiment, old preflight,
failure record, and STOP report. Token-summary v2 preserves the carry state;
replay starts expected reservation ordinals after the prior attempt and
recomputes global success, failure, actual-token, and conservative-charge totals.

## Frozen live and transport settings

- Model: `gpt-5.6-sol`.
- Reasoning effort: `high`.
- Service tier: provider default.
- Process timeout: `900000 ms`.
- First nonzero process exit: immediate `STOP_PHASE`.
- `RETRY_TRANSPORT`: at most attempt `2`; no third launch.
- JSONL parser schema: `r01-codex-jsonl-schema-v3`, SHA-256
  `33f4b4ceceb67421a9e9f901e45ae2c4cfb42b2442325a68f6d055de7e63af8d`.
- Transport shape spec: v2, SHA-256
  `d94c5a0370bdede3dd4e5138e9e84e111368a77fc0ddea5e213cb908f083a315`.
- Provider-response schema: `r01-provider-response-v4`.
- Config overrides: `model_reasoning_effort=high`,
  `tools.web_search=false`.

Parser v3 permits either no pre-turn diagnostics or exactly the ordered three
CLI `item.completed/error` deprecation notices observed in the stopped attempt.
Their exact field shape, IDs, placement, order, and message hashes are pinned.
Partial, reordered, late, additional, or unknown diagnostics remain
`jsonl_schema_drift / STOP_PHASE`. The stopped response is not reparsed into a
score and is not adopted into this experiment.

## Feature gate

- Codex CLI: `codex-cli 0.144.1`.
- Feature catalog rows: `92`.
- Explicitly disabled features: `88`.
- Effective-true allowlist:
  `resize_all_images`, `terminal_resize_reflow`,
  `tool_search_always_defer_mcp_tools`, `tui_app_server`.
- Feature-catalog snapshot SHA-256:
  `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad`.

Local feature inspection and exact command-spec rendering made no provider call.

## Deterministic anchors and command specs

Each regime uses the lexicographically first frozen development case and two
replicates, for 12 planned acquisitions. Prompt hashes are unique.

| Regime | Case | Command-spec SHA-256 | Prompt SHA-256 |
|---|---|---|---|
| `signal_consensus` | `development-0005` | `366d6fa300d3058fccdd9b180cbefb080d4d7fbbfa3b862fbe48ddc129e9258a` | `c9c60ec12a87b5fc4e7e305bfe5f73f23de41538d03536d9c335b9cf9665d600` |
| `signal_conflict` | `development-0001` | `b62385398e1d54b801043539203c08ee2b802c06daaf115b8d3b63b0c6dfe194` | `0377ffebe471438728b6c872f489234139d52e9a74133ff0a45051e4bcc97fda` |
| `high_transaction_cost` | `development-0000` | `44238aa371605d7ff810675726c94645e7c02b30a562883fbf74e8358fc40004` | `b7b27ecfdf229391fcf62f06769d24dbc11625bb96843aa1070354b0df171dce` |
| `concentration_pressure` | `development-0004` | `092ccf43443ed95d441faa98cfdd7a7f92ccb84c648f018ada86d1070a51ef3f` | `54dfdf95dc6ed25292baa50d0788c782a1552d2891ebc96412dd85760ef87e56` |
| `existing_position_asymmetry` | `development-0002` | `d9117126c8307644862b9812a069390c0d3245df69dc73f8f26cefd8519a8215` | `b2c60414353c6f5328773d519d542d694e1f2af806fe419436c7f9b7d8b4d80b` |
| `noisy_confidence` | `development-0003` | `47e38aecafd212e59702a3544b9d13fb9dc963f85c8ebd8b2586b519a4bb2c20` | `3a256298d7f0304e23e2c1f6a3292e2c78724e3aaeb987eb61f03d58da8a17b1` |

All six specs bind the same model, timeout, executable path, feature catalog,
transport shape, config overrides, and empty-sandbox identity.

## Provider-free validation

- Full overlay suite: `125 passed`.
- `compileall`: passed.
- Black: passed for all 36 overlay Python files.
- isort: passed for the overlay package.
- `git diff --check`: clean.
- Recursive artifact references verified: `52`, plus the root preflight file =
  `53` total artifact files.
- Missing, size-mismatched, hash-mismatched, conflicting, or unreferenced
  artifact files: `0`.
- Replacement sandbox entries after preflight: `0`.
- Provider calls made by manifest generation and replacement preflight: `0`.
- Historical provider calls carried from the stopped attempt: `1`.
- Provider calls after that STOP: `0`.
- No response, score, run result, or replay result was created for the
  replacement experiment.

## Known limits

- The effective execution boundary is the pair `af8381f` plus preflight SHA
  `e86c7565...23d09`; a data hash alone does not pin interpretation code.
- ChatGPT login and account state are external to the preflight hash and must be
  rechecked immediately before any approved live run.
- The zero-cost attestation is a reviewed document hash, not a technical payment
  rail block.
- The Codex executable is pinned by path and SHA-256; reproducible source-to-
  binary build provenance remains unavailable.

## Cross-review request

Review `a4b52f5..HEAD` without running `b3-run` or any provider call. Confirm:

1. the exact diagnostic exception cannot admit a partial, reordered, late,
   additional, or differently shaped error item;
2. the first stopped attempt remains immutable, unscored evidence and cannot be
   adopted into the replacement run;
3. the replacement preflight cannot reset prior provider ordinals or the
   conservative `32,000` charge;
4. replay and token-summary v2 reconstruct global totals from the carried state;
5. the 53-file artifact graph, six specs, empty sandbox, executable, gate,
   attestation, and carry document all match the hashes above;
6. no second provider call is authorized until the reviewer approves both
   `af8381f` and preflight SHA `e86c7565...23d09`.
