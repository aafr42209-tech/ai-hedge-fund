# R01 B3 resource-v2 provider-free preflight readiness

Date: 2026-07-16
Status: `READY_FOR_INDEPENDENT_REVIEW_PROVIDER_CALLS_ZERO`

No `b3-run` command or provider acquisition was executed while preparing this
report. The global development ledger still carries the four provider attempts
that existed before the resource amendment. The `provider_calls: 0` value below
means zero new provider calls during preparation of this replacement preflight;
it does not erase those four historical attempts.

## Review gate

The only pair proposed for the next live-call approval is:

- implementation commit: `f403e1a` (`fix: carry amended B3 resource limits`);
- B3 preflight SHA-256:
  `95130a039edbd43a9c610078ce6d904beb5e038bed65e9bf0252924b3bb04bde`.

The previous `af8381f` + `e86c7565...23d09` approval does not authorize another
call. Do not run `b3-run` until an independent reviewer has verified this new
pair and the user has explicitly approved it.

## Frozen identity and inputs

- experiment ID: `r01-b3-prompt-v1-resource-v2-20260716`;
- artifact root: `.research_artifacts/r01-b3-f403e1a`;
- external empty sandbox: `C:\tmp\r01-b3-sandbox-f403e1a`;
- preflight schema: `r01-b3-preflight-v3`;
- development manifest SHA-256:
  `a44751fb96797ca9110349cdeac7bfae326a915911a33fd765c7bc2d8b8057b0`;
- B3 anchor manifest SHA-256:
  `dec47fb4c1092ff931fc62444b568bd889dda6002c2652cbe7ed91306c24263c`;
- feature gate SHA-256:
  `f9cf5c8b3abed7f594941122bfc4a844a0cbd2c884eed516bed9f5da3258d0a6`;
- provider-free freeze SHA-256:
  `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`;
- research contract SHA-256:
  `6edb5573aec4d54283cc916de3def8b14c875888106770653af680354b8c7276`;
- D2 resource-amendment SHA-256:
  `cb1e39b9c19ece973c6a19d44b59389bcd8bbfeea2638b78c554b3808d050124`;
- aggregate carry-forward SHA-256:
  `002cc7b8e726e3d5041bc1d888e2a7da15ea258aa661ff1dd17ecb9de9397953`;
- zero-cost account-attestation SHA-256:
  `94ca690340273e02da7de19e0c1ea5efc8793547f2a87822dc40eb5b630b9746`;
- native executable SHA-256:
  `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`;
- pinned Codex CLI version: `0.144.1`.

The aggregate carry is schema `r01-development-budget-carry-forward-v2` and
links the reviewed prior preflight, terminal evidence, STOP report, and prior
carry document. Its source values are:

- provider attempts: `4`;
- complete responses for token accounting: `3`;
- failed or unsettled attempts: `1`;
- settled actual tokens: `71,623`;
- observed unsettled actual tokens: `13,651`;
- unsettled conservative charge: `32,000`;
- total conservative charge: `103,623`.

## Amended resource boundary

The preflight binds the user-approved amendment without changing the existing
development attempt cap or zero-cost requirement:

- model: `gpt-5.6-sol`;
- reasoning effort: `high`;
- service tier: provider default;
- timeout: `900000` ms;
- per-attempt token reserve: `64,000`;
- development token cap: `12,800,000`;
- development provider-attempt cap: `200`;
- B3 planned acquisitions: `12`;
- B3 provider-attempt ceiling: `24`;
- next reservation ordinal: `5`;
- worst-case global ordinal after this micro-pilot: `28`;
- worst-case conservative charge after this micro-pilot:
  `103,623 + 24 * 64,000 = 1,639,623` tokens.

The runner reserves before every call, starts from the carried counters, and
settles the response before enforcing the per-attempt bound. A response over
`64,000` therefore consumes its provider tokens before it can be detected, but
the detected excess is `STOP_PHASE`: it is not scored, is not retried, and does
not authorize an automatic reserve increase or another call.

Historical 32K/6.4M reservation, usage, summary, carry, and preflight schemas
remain parseable for audit. They are not active resource settings and cannot be
used by the current live preflight entry point to bypass the amendment.

## Artifact-graph audit

Starting from `b3_preflight.json`, every nested `ArtifactReference` was followed
recursively and its size and SHA-256 were recomputed from disk:

- unique references: `53`;
- files under the new artifact root: `53`;
- missing references: `0`;
- unreferenced files: `0`;
- size or SHA-256 mismatches: `0`;
- external sandbox entries after preflight: `0`;
- provider calls recorded by preflight: `0`.

Six command specs are present, one for the deterministic minimum-case anchor in
each of the six regimes. Their six fixture-prompt hashes are unique. All six
agree on model, timeout, executable, feature catalog, catalog definition,
transport-shape v2, JSONL parser v3, and empty-sandbox identity:

- feature catalog SHA-256:
  `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad`;
- feature-catalog definition SHA-256:
  `aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530`;
- transport-shape specification SHA-256:
  `d94c5a0370bdede3dd4e5138e9e84e111368a77fc0ddea5e213cb908f083a315`;
- JSONL parser-schema SHA-256:
  `33f4b4ceceb67421a9e9f901e45ae2c4cfb42b2442325a68f6d055de7e63af8d`;
- pilot-sandbox identity SHA-256:
  `3b2dd03ded747485bfbbc3e575e18c8f4ca1b3df08666162ee57fd2ef1856194`;
- config overrides: `model_reasoning_effort=high` and
  `tools.web_search=false`;
- active feature allowlist: `4`;
- disabled features: `88`;
- effective-true features after disable: `4`.

## Provider-free validation

- full overlay suite: `126 passed in 75.74s`;
- Black: `36 files would be left unchanged`;
- isort: passed;
- `compileall`: passed;
- `git diff --check`: passed before the implementation commit;
- implementation working tree: clean before preflight/report generation.

The final test run used a dedicated `C:\tmp\pytest-f403e1a` base directory so
tests that require an out-of-repository pilot sandbox exercised the real
boundary. Earlier restricted invocations either could not read pytest's default
temporary directory or intentionally failed when a repository-local base
directory violated that boundary; neither invocation made a provider call.
The dedicated test directories were removed after the passing run.

One initial manifest command was rejected before artifact creation because an
operator-supplied freeze SHA was mistyped; the command was rerun with the
committed external trust anchor above. One restricted preflight invocation was
also rejected at provider-free `codex login status`; the successful invocation
used the same frozen inputs with permission to read the existing login state.
Neither rejected invocation launched `codex exec`, and the final artifact graph
contains no partial or orphan files.

## Independent cross-review questions

1. Do schema branching and tests preserve byte-level parsing of historical
   32K/6.4M ledgers while making 64K/12.8M the only active v3 boundary?
2. Does aggregate carry v2 transitively bind the prior carry, reviewed
   preflight, terminal evidence, and STOP report without permitting a reset of
   ordinal `4` or conservative charge `103,623`?
3. Do schema validation, reservation, settlement, replay, and preflight checks
   jointly force next ordinal `5`, attempt ceiling `200`, and the amended token
   cap?
4. Does every response over `64,000` become an immediate non-retryable,
   unscored `STOP_PHASE`, with no automatic upward amendment?
5. Do the 53-file reference graph, six anchor specs, current feature gate,
   executable, account attestation, resource amendment, aggregate carry, and
   empty sandbox reproduce the hashes in this report?
6. Is `f403e1a` plus
   `95130a039edbd43a9c610078ce6d904beb5e038bed65e9bf0252924b3bb04bde`
   sufficient to freeze the next live boundary, subject to login/account state
   being rechecked immediately before execution?

## Known limits

- The preflight hash fixes data and command specs; interpretation code is fixed
  separately by commit `f403e1a`. Both identities are required.
- Login and account status are live external state and cannot be frozen by a
  file hash. The live client rechecks them before any next process launch.
- The account attestation is a reviewed document hash, not a technical payment
  rail lock. The additional-cost condition remains an operator gate.
- The 64K bound is a post-response safety control. It stops follow-up work after
  an oversized response but cannot undo tokens already consumed by that
  response.
