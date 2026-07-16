# R01 B3 Provider-Free Preflight Readiness

Status: `READY_FOR_EXTERNAL_REVIEW_PROVIDER_CALLS_ZERO`

Generated: `2026-07-16` (Asia/Seoul)

Provider calls made: `0`

Development provider attempts spent: `0`

Provider tokens consumed: `0`

The 12-acquisition B3 command remains blocked. This report freezes the exact
provider-free implementation and preflight identity for cross-review; it does
not authorize `b3-run`.

## Code and contract identity

- Branch: `codex/llm-overlay-research-01`
- Review base: `bdc0827`
- B3 implementation commit:
  `bcc3dbc2dc0d4c223e675ad1d6ecb255f54d625a`
- Implementation review range: `bdc0827..bcc3dbc`
- Research contract SHA-256:
  `f1e46e11397ab1dd41cc1bda3c2f2c20720201733bb2d2e6a192d6cf241c69f3`
- Provider-free freeze SHA-256:
  `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`
- Zero-cost account attestation SHA-256:
  `94ca690340273e02da7de19e0c1ea5efc8793547f2a87822dc40eb5b630b9746`

The development manifest's bound contract hash equals the current contract
file hash byte-for-byte.

## Preflight trust anchors

- Local append-only artifact root:
  `.research_artifacts/r01-b3-bcc3dbc` (gitignored)
- Experiment ID: `r01-b3-prompt-v1-20260716`
- Development manifest SHA-256:
  `d3430a981116ec634bb00da03042faab270c0e8fa19c9170ae8a56ba518c905a`
- B3 preflight SHA-256:
  `df53917b4943e41999c66506b66c09255cd05c6d3db69a870aed9f53b0482481`
- B3 anchor manifest SHA-256:
  `e920a8b11d147185c1e61030e08db1d02f4a2bae807d33ad59288f4852a6a445`
- Feature-gate artifact SHA-256:
  `f9cf5c8b3abed7f594941122bfc4a844a0cbd2c884eed516bed9f5da3258d0a6`
- Native executable SHA-256:
  `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`
- Empty pilot-sandbox identity SHA-256:
  `013f733f68e82737ec7fa610047c179b7194f7dbea886e90bc69678cf1a15906`
- Codex CLI identity: `codex-cli 0.144.1`
- Authentication mode: `ChatGPT`
- Preflight status: `READY_FOR_REVIEW_PROVIDER_CALLS_ZERO`

A recursive independent pass followed all `53` unique artifact references from
the externally anchored preflight root and recomputed every size and SHA-256.
Missing files, conflicting references, and byte/hash mismatches: `0`.

## Frozen live settings

| Field | Frozen value |
| --- | --- |
| Model | `gpt-5.6-sol` |
| Reasoning effort | `high` |
| Service tier | `provider_default` |
| Process timeout | `900000 ms` |
| Per-attempt token reserve | `32000` |
| Development total-token cap | `6400000` |
| Development provider-attempt cap | `200` |
| B3 planned successful acquisitions | `12` |
| B3 maximum provider attempts | `24` |
| Incremental USD cap | `$0` |

The B3 attempt ceiling is two attempts for each of 12 planned acquisitions.
Attempt-1 nonzero exit without a complete response stops immediately; other
eligible transport failures may advance only once to attempt 2. No third call
is possible for an acquisition.

## Feature gate

- Catalog SHA-256:
  `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad`
- Catalog-definition SHA-256:
  `aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530`
- Disabled feature count: `88`
- Residual reviewed allowlist and observed effective-true set are identical:
  `resize_all_images`, `terminal_resize_reflow`,
  `tool_search_always_defer_mcp_tools`, and `tui_app_server`.

## Deterministic anchors and command specs

| Regime | Case | Command-spec SHA-256 | Fixture-prompt SHA-256 |
| --- | --- | --- | --- |
| `signal_consensus` | `development-0005` | `1e63bf047d182edf2d03333eb9b775b3129ef4827b2cdca8bc41f3278f4b3b33` | `c9c60ec12a87b5fc4e7e305bfe5f73f23de41538d03536d9c335b9cf9665d600` |
| `signal_conflict` | `development-0001` | `461249ec51f872a07ab50f78adbc9f92d0eb963cd134cfa39113e1fbe7cdf63c` | `0377ffebe471438728b6c872f489234139d52e9a74133ff0a45051e4bcc97fda` |
| `high_transaction_cost` | `development-0000` | `4615d9bb4d85a12cd67f1760d7bc2502a39c5bcf46fc2078a2c006d505f75ba3` | `b7b27ecfdf229391fcf62f06769d24dbc11625bb96843aa1070354b0df171dce` |
| `concentration_pressure` | `development-0004` | `75a2ad38f044c260e941adacd589f24e966cac9b028e13b511a2994f6a1f031d` | `54dfdf95dc6ed25292baa50d0788c782a1552d2891ebc96412dd85760ef87e56` |
| `existing_position_asymmetry` | `development-0002` | `734ec9183f1f7ab131d1c1dca189584d1d4094a8726dfa933f6d6db105620816` | `b2c60414353c6f5328773d519d542d694e1f2af806fe419436c7f9b7d8b4d80b` |
| `noisy_confidence` | `development-0003` | `53d5f14eae99497dd11fee8d7fbd9aabae9374f2653a094b076f6f2c7ac19215` | `3a256298d7f0304e23e2c1f6a3292e2c78724e3aaeb987eb61f03d58da8a17b1` |

Each spec binds the same executable, model, `900000 ms` timeout, complete
feature disable set, external empty-sandbox identity, policy prompt, and exact
fixture prompt. The two replicates per anchor reuse the reviewed command shape
but retain distinct acquisition identities and append-only attempt paths.

## Failure-audit closure

- Command-spec validation failures become `STOP_PHASE` before provider-call
  accounting and persist an acquisition-failure record when the runner owns a
  reservation.
- Raw capture and parsed-provider artifact persistence failures become explicit
  `STOP_PHASE` errors rather than unclassified crashes.
- A captured failed attempt binds command spec, stdout JSONL, stderr, process
  status, optional parsed response, and token reservation through
  `r01-acquisition-failure-v2`.
- Replay verifies every byte/hash edge for failed attempts preceding a success.
- Attempt updates use full Pydantic validation; attempt 3 is prohibited.
- Retry, attempt, token, and timeout safety values have one source of truth in
  `contracts.py` and are revalidated by persisted contracts.

## Provider-free validation

- Overlay tests: `121 passed`
- Python compile: passed
- Black: passed (`36 files would be left unchanged`)
- isort: passed
- `git diff --check`: passed
- Provider calls: `0`

The first preflight invocation stopped before artifact creation because the CLI
login had expired. After explicit ChatGPT device authentication,
`codex login status` returned `Logged in using ChatGPT`; the same manifest and
still-empty sandbox then produced the frozen preflight above. Neither login
check nor either preflight invocation launched `codex exec` or made a provider
model call.

## Cross-review request

Review `bdc0827..bcc3dbc` plus this readiness report and independently answer:

1. Can any command-build, artifact-persistence, retry, or replay failure still
   escape without a classified audit record where one is expected?
2. Does every failed retry transport enter the replay-verifiable graph without
   allowing a stopped attempt into scoring?
3. Do the six command specs exactly match the selected regime anchors, approved
   model/runtime settings, feature gate, executable, and empty sandbox?
4. Can any acquisition exceed attempt 2, the 24-attempt B3 ceiling, the
   200-attempt development ceiling, or the approved token caps?
5. Is `df53917b4943e41999c66506b66c09255cd05c6d3db69a870aed9f53b0482481`
   sufficient to freeze the exact live boundary before `b3-run`?

Do not run `b3-run`, approve additional spending, or make a provider call while
performing this review.
