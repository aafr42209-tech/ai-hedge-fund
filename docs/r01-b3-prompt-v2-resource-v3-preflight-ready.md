# R01 B3 prompt-v2/resource-v3 provider-free preflight readiness

Date: 2026-07-17
Status: `READY_FOR_INDEPENDENT_REVIEW_PROVIDER_CALLS_ZERO`

No `b3-run` command or provider acquisition was executed while preparing this
report. The global development ledger still carries the 15 provider attempts
that existed before D2 Resource Amendment 02. The `provider_calls: 0` value
below means zero new provider calls during preparation of this replacement
preflight; it does not erase those historical attempts.

## Review gate

The only pair proposed for a possible later live-call approval is:

- interpretation-code commit: `1f65106`;
- B3 preflight SHA-256:
  `5937161ac9c2bb9c22172d0be27a5a730cc2a3dc1c8bf51044270b65ee68353e`.

This pair is not approved for a provider call by this report. The previous
`f403e1a` + `95130a03...4bde` approval ended with the resource-v2 STOP and does
not authorize another call. Do not run `b3-run` until an independent reviewer
has verified the new pair and the user has separately and explicitly approved
execution.

## Frozen identity and inputs

- experiment ID: `r01-b3-prompt-v2-resource-v3-20260717`;
- artifact root: `.research_artifacts/r01-b3-1f65106`;
- external sandbox: `C:\tmp\r01-b3-sandbox-1f65106`;
- development manifest SHA-256:
  `d9ef5150073717a802212cafbb1b9182b10c4ab329ca01ea57e16fb0baaa26ba`;
- provider-free freeze SHA-256:
  `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`;
- research-contract SHA-256:
  `90f57724223e283cc41a4ec4b1a48b63b70350177f1f2fcd51cb46550ca2e448`;
- preflight schema: `r01-b3-preflight-v4`;
- preflight status: `READY_FOR_REVIEW_PROVIDER_CALLS_ZERO`;
- model: `gpt-5.6-sol`;
- reasoning effort: `high`;
- service tier: provider default;
- timeout: `900000` ms;
- CLI identity: `codex-cli 0.144.1`;
- authentication mode: `ChatGPT`;
- executable SHA-256:
  `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`;
- zero-cost account-attestation SHA-256:
  `94ca690340273e02da7de19e0c1ea5efc8793547f2a87822dc40eb5b630b9746`;
- D2 Resource Amendment 02 SHA-256:
  `e165471e03ce199dffb127202dd620f19fb4be2badee48ea07b14e4c6557b0f0`;
- aggregate carry-forward v3 SHA-256:
  `cea3fd3aa38478d13c23cedb6cb0d41b01bfa16bb2cb781d50e5e27e4a03bbe8`;
- anchor-manifest SHA-256:
  `79335fec6891b15ab83fe4290e39a3e7ba36947d17d3f5b52491afdea59ac338`;
- feature-gate SHA-256:
  `f9cf5c8b3abed7f594941122bfc4a844a0cbd2c884eed516bed9f5da3258d0a6`.

The six command specs are one per deterministic regime anchor. They share:

- policy-instruction SHA-256:
  `f6ee61910d887d488139f9b66e642a72a1cc718c157b79317627d59da6324953`;
- prompt v2 source-file SHA-256:
  `8dfa68021981b457b05dbc6f8a3d2678017e8595dc1084d444d2689c286d6785`;
- feature catalog SHA-256:
  `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad`;
- feature-catalog definition SHA-256:
  `aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530`;
- transport-shape v2 SHA-256:
  `d94c5a0370bdede3dd4e5138e9e84e111368a77fc0ddea5e213cb908f083a315`;
- JSONL parser v3 SHA-256:
  `33f4b4ceceb67421a9e9f901e45ae2c4cfb42b2442325a68f6d055de7e63af8d`;
- external empty-sandbox SHA-256:
  `a6d5afc9da4963330f9fc0df64a584112520b0be69deafcc581057cfdca3754a`;
- config overrides: `model_reasoning_effort=high` and
  `tools.web_search=false`;
- 88 disabled features and the exact four-entry active/effective-true
  allowlist: `resize_all_images`, `terminal_resize_reflow`,
  `tool_search_always_defer_mcp_tools`, and `tui_app_server`.

The six fixture-prompt hashes are unique. The anchors are the minimum frozen
case ID in each regime: `development-0005` signal consensus,
`development-0001` signal conflict, `development-0000` high transaction cost,
`development-0004` concentration pressure, `development-0002` existing
position asymmetry, and `development-0003` noisy confidence. Two independent
replicates per anchor fix 12 planned acquisitions.

## Prompt v2 boundary

The old prompt functions remain available only for historical compatibility.
All active runner request artifacts, client calls, and B3 command-spec builds
use `SYSTEM_PROMPT_V2` and `build_user_prompt_v2`.

Prompt v2 now requires exactly one JSON object with no markdown or surrounding
prose. It repeats in both system and user instructions that every confidence
must be a JSON integer from `0` through `100`, prohibits fractional or decimal
forms, and gives `96` rather than `0.96` as the valid 96% representation. Its
example is a syntactically valid complete A0-through-A5 decision object rather
than an ellipsis-containing pseudo-object. Provider-free tests parse that
example and reject fractional confidence through the real decision parser.

The policy-instruction hashes differ as intended:

- prompt v1: `0b0e7802b4ac50af8d4f64450e0513960886110391e5a48fab12564a7080196c`;
- prompt v2: `f6ee61910d887d488139f9b66e642a72a1cc718c157b79317627d59da6324953`.

## Amended resource boundary and aggregate carry

The preflight binds the user-approved Amendment 02 without changing the
development attempt cap, total-token cap, or zero-cost requirement:

- per-attempt token reserve: `128000`;
- development token cap: `12800000`;
- development provider-attempt cap: `200`;
- incremental USD cap: `0`;
- B3 planned acquisitions: `12`;
- B3 provider-attempt ceiling: `24`;
- no automatic reserve increase is allowed;
- any complete response above `128000` is an immediate non-retryable,
  unscored `STOP_PHASE` before another provider call.

Aggregate carry schema `r01-development-budget-carry-forward-v3` binds the
prior aggregate carry, approved resource-v2 preflight, terminal evidence, STOP
report, and the persisted ordinal-15 acquisition-failure artifact. The latter
SHA-256,
`0ec69aa27e9316ea4506f1ca02e83bd2253c8c8b48d0328f24301344b5247127`,
matches exactly one immutable file in the stopped resource-v2 root.

Carried state is:

- provider attempts: `15`;
- successful settled responses for token accounting: `14`;
- failed or unsettled attempts: `1`;
- settled actual tokens: `307507`;
- observed unsettled actual tokens: `13651`;
- unsettled conservative charge: `32000`;
- total conservative charge: `339507`.

The next possible reservation ordinal is `16`. The 24-attempt worst case ends
at ordinal `39` with conservative charge
`339507 + 24 * 128000 = 3411507`, below the unchanged `12800000` cap.

Historical byte identities are not rewritten. Real preflight, carry,
reservation, and usage artifacts from the 32K generation still parse only as
v1/v2-era objects, and their 64K successors still parse only as v2/v3-era
objects. New reservations/usage/carry use v3; new summaries and preflight use
v4.

## Artifact-graph audit

Starting from the externally constructed reference for `b3_preflight.json`,
every nested `ArtifactReference` was followed recursively and its size and
SHA-256 were recomputed from disk:

- 53 unique reachable references;
- 53 actual files under the experiment root;
- missing files: `0`;
- unreferenced files: `0`;
- size mismatches: `0`;
- SHA-256 mismatches: `0`;
- references escaping the experiment root: `0`;
- live acquisition/provider-response/token-usage artifacts: `0`;
- external sandbox entries after preflight: `0`.

All six command specs agree on model, timeout, executable, feature catalog,
catalog definition, transport shape, JSONL parser, policy instruction, sandbox,
config overrides, disable count, and effective-true allowlist. Their fixture
prompt hashes alone vary as intended.

## Provider-free validation

- focused contract/B3 tests: `22 passed in 54.73s`;
- full overlay suite: `127 passed in 69.11s`;
- Black: `36 files would be left unchanged`;
- isort: passed;
- `compileall`: passed;
- `git diff --check`: passed before the implementation commit;
- real historical compatibility parse: nine representative v1/v2 preflight,
  carry, reservation, and usage artifacts plus the new carry v3 all validated;
- implementation commit `1f65106` was pushed before manifest/preflight
  generation;
- implementation working tree was clean before preflight/report generation.

The first restricted preflight invocation stopped at provider-free
`codex login status` because the sandbox could not read the existing login
state. The successful invocation used the exact same frozen inputs with local
permission to inspect login and feature state. Neither invocation ran
`codex exec`; the rejected invocation wrote no partial preflight, and the final
53-file graph contains no partial or orphan file.

## Independent cross-review questions

1. Do schema branching and tests preserve real 32K and 64K artifact parsing
   under their original constants while making 128K/12.8M the only active v4
   preflight boundary?
2. Does aggregate carry v3 transitively bind the prior carry, reviewed
   resource-v2 preflight, terminal evidence, STOP report, and exactly one
   persisted ordinal-15 failure without permitting a reset of 15 attempts or
   `339507` conservative tokens?
3. Do schema validation, reservation, settlement, replay, and preflight checks
   jointly force next ordinal `16`, attempt ceiling `200`, and the unchanged
   `12800000` total-token cap?
4. Does every response over `128000` become an immediate non-retryable,
   unscored `STOP_PHASE`, with no automatic upward amendment?
5. Do active request artifacts, client calls, and all six reviewed command
   specs use prompt v2, whose complete JSON example and repeated instruction
   require integer confidence `0..100` and prohibit fractional forms?
6. Do the 53-file reference graph, six anchor specs, current feature gate,
   executable, account attestation, resource amendment, aggregate carry, and
   empty sandbox reproduce every hash and count in this report?
7. Is `1f65106` plus
   `5937161ac9c2bb9c22172d0be27a5a730cc2a3dc1c8bf51044270b65ee68353e`
   sufficient to freeze a possible next live boundary, subject to login and
   account state being rechecked immediately before execution?

## Known limits

- The preflight hash fixes data and command specs; interpretation code is fixed
  separately by commit `1f65106`. Both identities are required.
- Login and account status are live external state and cannot be frozen by a
  file hash. The live client must recheck them before any later process launch.
- The account attestation is a reviewed document hash, not a technical payment
  rail lock. The zero-additional-cost condition remains an operator gate.
- The 128K bound is a post-response safety control. It stops follow-up work
  after an oversized response but cannot undo tokens already consumed by that
  response.
- Provider-free prompt tests prove wording, hashing, example validity, and
  parser rejection; they cannot prove that a live model will follow prompt v2.
  That is the purpose of the separately reviewed micro-pilot.

## Final gate

Provider-call authorization remains `NO`. Independent cross-review of the exact
`1f65106` + `5937161a...8353e` pair and a separate explicit user execution
approval are required before any `b3-run` command.
