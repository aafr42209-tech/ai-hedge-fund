# R02 D3 provider-free preregistration and zero-call preflight report

Status: `REVIEW_CANDIDATE_PROVIDER_CALLS_ZERO`

Base commit: `4c45654d81efa07aa31a97e41f49ce16b29e0939`

Preflight ID: `r02-d3-preflight-5e07d88e98e7`

Provider calls: `0`

Live executions: `0`

Micro-pilot episodes executed: `0`

Reseal reason: `MULTI_REVIEW_PATH_B_DUPLICATION_HARDENING`

The reseal removes the script-local exclusive-write helper in favor of the
existing append-only artifact store and makes the five zero-call command tuples
originate from one contracts-layer builder. Snapshot validation and model
identity execution now delegate to that single source. No protocol, prompt,
bootstrap-seed preimage, budget, or authorization boundary changed.

## Evaluation bootstrap seed

The evaluation seed uses the domain
`R02-D3-EVALUATION-BOOTSTRAP-SEED-V1`. Its preimage is canonical JSON
containing only the accepted D2c commit, R02 contract identity, frame identity
and tree, frame-manifest and statistical-freeze hashes, the registered primary
estimand, `PCG64`, and `10,000` bootstrap draws. It contains no provider output,
utility result, hidden outcome, confidence, or post-preflight observation.

- Digest:
  `319dea85b61187c07089deedb525d4d927ffc03dc7ea2026e4be8022f2df9f68`
- Conversion: the complete 32-byte digest is interpreted as one unsigned
  big-endian integer; no truncation is permitted.
- Decimal seed:
  `22442343183242363715643782652922180789516558615738697691108320593833078267752`

## Selector prompt and output contract

The prompt is the byte-equivalent template already implemented at the D2b
selector boundary. The sole dynamic field is exactly one canonical
`selector_safe_payload`; candidate roles, canonical IDs, permutation seed/map,
oracle, headroom, and future returns remain prohibited.

- Stdin construction: `system_prompt + LF LF + rendered_user_prompt + LF`.
- Stdin-template SHA-256:
  `1c2b980aac214dcfbf66b2dba5521ceceb6b61fc9b04a76ff100f04aca06026d`.
- Strict response JSON Schema SHA-256:
  `5466a24d3557e28251cb1393dac16e1049824637a27b969f3bea55c80ebc2eca`.
- Confidence remains log-only and has no execution effect.
- Invalid schema, unknown presented ID, or acceptance failure retains the D2b
  typed baseline-fallback behavior and contributes paired delta zero.

## Model and transport identity

Requested model `gpt-5.6-sol` is selected for continuity with the sealed R01
command spec, not from R02 outcomes. The provider channel is
`openai-codex-chatgpt-subscription` through Codex JSONL stdin transport.

- Codex CLI: `codex-cli 0.144.1`.
- Native executable SHA-256:
  `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`.
- Feature catalog: 92 entries, canonical snapshot
  `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad`.
- All catalog features are passed through global `--disable`; the four
  non-tool flags that remain effective are explicitly allowlisted.
- Sandbox is read-only, execution is ephemeral, user config and rules are
  ignored, web search is false, reasoning effort is high, and the strict output
  schema is passed to `--output-schema`.
- A present provider model echo must equal the requested ID. Echo absence is an
  explicit recorded limitation accepted by the R02 draft; any mismatch is a
  hard stop. Command-spec identity is always mandatory.
- No temperature override is available or applied.

## Preregistered micro-pilot plan

No micro-pilot was executed. A future, separately authorized D3 micro-pilot is
limited to six fixed frame cases: the lexicographically first triggered fixture
in each representative/challenge by K=2/3/4 cell, executed by frame ordinal.

1. `development-0003` — representative, K=2
2. `development-0009` — representative, K=3
3. `development-0027` — representative, K=4
4. `development-0129` — challenge, K=3
5. `development-0153` — challenge, K=2
6. `development-0171` — challenge, K=4

Selection uses only frozen stratum, trigger, candidate count, fixture ID, and
frame ordinal. Hidden utility and candidate headroom values are not inputs.
Each attempted case permanently debits the 55-attempt evaluation budget,
remains in the ITT denominator, and cannot be retried, replaced, or deleted.
Utility outcomes are unavailable to the D3 continuation gate and D3 carries no
utility or investment claim.

## Budget and stop contract

- Micro-pilot cap: 6 attempts and 192,000 reserved tokens.
- Full evaluation cap: 55 attempts and 1,760,000 reserved tokens.
- Per attempt: 32,000 tokens, one attempt, zero retries.
- Incremental USD cap: 0.
- Selector fallback cap during micro-pilot: 1; the second fallback stops the
  phase.
- Full evaluation fail-closed cap: 5 of 55 (`90,909` ppm); exceeding it labels
  the run `INVALID_RUN`.
- Unsettled attempt cap: 0.
- Live command timeout: 900,000 ms.

Any trust-anchor, protected-tree, prompt, output-schema, requested-model,
present model-echo, executable, CLI, feature, command, transport, budget,
append-only, hash, or replay violation stops before the next call and labels the
run invalid. A stopped attempt is never silently removed or rerun.

## Zero-call capture and replay

The stored transport snapshot contains exact reversible bytes for five local
commands only: version, login status, baseline feature list, all-feature-disable
feature list, and all-feature-disable `exec --help`. The allowlist rejects every
`codex exec` command that lacks `--help`, including the registered future live
argv.

The append-only graph contains five data nodes plus its graph anchor. Replay
verifies every reference and canonical byte, rebuilds the preregistration,
seed, prompt, model identity, and preflight, reruns the five provider-free local
commands, and requires the transport snapshot to match byte-for-byte.

- Preregistration SHA-256:
  `5e07d88e98e74f67a1377020ca8c19c6fada51756ebddd902706a1680eeb27d4`.
- Transport snapshot SHA-256:
  `3cf5745ac66b941e983dd33477c56e4b522d96278664617e17e020a40c73d6db`.
- Preflight SHA-256:
  `d88b406253f3a1f005b33534a742ee90814d9bc53f88a36ed400e7473a2b38fc`.
- Audit graph SHA-256:
  `fced7e68793e0e3aacb385190e63a06cbb103cc9bbc50f312a305eef106cc858`.
- Local six-file tree SHA-256:
  `7e02e5359340e14df30033411e41656cdfdc77eefeb14429949cf404a392328f`.

## Authorization boundary

This package is a freeze candidate only. Independent review and explicit user
acceptance are required to finalize it. Even after acceptance, provider calls,
live execution, and D3 micro-pilot execution require a separate approval tied
to the final implementation commit and accepted preflight hash.
