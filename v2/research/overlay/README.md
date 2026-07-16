# R01 LLM overlay research — Phase A / provider-free B0-B3 readiness

`v2.research.overlay` is the provider-free, development-only foundation for R01.
It implements deterministic fixture generation, strict validation, exact integer
scoring, complete-enumeration oracle and baselines, append-only artifacts, replay,
bootstrap analysis, nuisance transforms, the Codex command/JSONL contract, and
the provider-free B2 feature/catalog/isolation gates, and the reviewed B3
preflight/live boundary.

The provider-capable Codex adapter uses a shell-free subprocess runner with a
secret-bearing environment denylist and append-only raw transport storage. It
cannot generate evaluation fixtures. Its B2 local subprocess runner accepts
only version, login-status, feature-list, and `exec --help` preflight commands;
plain `codex exec` is rejected before launch. Every report is marked:

> DEVELOPMENT_ONLY — NOT SEALED — NO INVESTMENT CLAIM

## Commands

Run from the repository root:

```powershell
$codexNative = Join-Path $env:APPDATA `
  "npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe"
$recheck = Join-Path $env:TEMP "r01-b2-preflight-recheck"
New-Item -ItemType Directory -Path $recheck

python -m scripts.r01_b2_preflight `
  --codex-executable $codexNative `
  --output-directory $recheck `
  --expected-catalog-sha256 14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad `
  --expected-definition-sha256 aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530
```

This zero-call command writes four files exclusively: exact reversible base64
captures of the baseline catalog, post-disable catalog, and global-disable help
output, plus a canonical summary. It refuses to overwrite an existing capture.

```powershell
python -m v2.research.overlay `
  provider-free-freeze `
  --root-seed r01-phase-b-development-fixtures-v1 `
  --count 40 `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2 `
  --output r01-b0-provider-free-freeze-recheck.json

python -m v2.research.overlay `
  provider-free-gap-summary `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2 `
  --output r01-b0-regime-gap-summary-recheck.json
```

This command uses no provider. It writes a new safe repository-relative path
exclusively and verifies the development oracle-hold scale, complete-lattice
bounds, and per-regime gap statistics against the committed B0 freeze. Absolute,
drive-qualified, parent, empty-segment, and dot output paths are rejected.

For the provider-free scripted Phase A runner:

```powershell
python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  generate-development `
  --experiment-id r01-development `
  --root-seed r01-phase-b-development-fixtures-v1 `
  --count 40 `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2 `
  --contract docs/research-contract-01-llm-overlay.md
```

Create an executable all-hold response template, edit its raw-response values if
needed, then run the provider-free acquisition:

```powershell
python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  scripted-template `
  --manifest r01-development/development_manifest.json `
  --replicates 1 `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2 `
  --output scripted-responses.json

python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  dry-run `
  --manifest r01-development/development_manifest.json `
  --responses scripted-responses.json `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2

python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  replay `
  --result r01-development/run_result.json `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2 `
  --expected-manifest-sha256 MANIFEST_SHA256_FROM_GENERATE `
  --expected-result-sha256 RESULT_SHA256_FROM_DRY_RUN

python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  verify `
  --result r01-development/run_result.json `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2 `
  --expected-manifest-sha256 MANIFEST_SHA256_FROM_GENERATE `
  --expected-result-sha256 RESULT_SHA256_FROM_DRY_RUN
```

Acquisition keys are not pipe-delimited labels. They are the SHA-256 of the
canonical JSON acquisition identity:

```text
sha256(canonical_json(AcquisitionIdentity))
```

`scripted-template` derives these keys with the production implementation, so
they should not be constructed by hand. Replay and verification require the
fixed B0 freeze hash shown above, the manifest hash printed by
`generate-development`, and the result hash printed by `dry-run`; a missing or
mismatched external anchor fails closed before scoring. Manifest generation also
rejects any root seed or fixture count that differs from the committed B0 freeze.

For B3, generate the development manifest first, create a new empty sandbox
outside the repository, and run the provider-free preflight. The account,
executable, freeze, manifest, feature catalog, six deterministic regime anchors,
rendered command specs, timeout, and token caps are all hashed before any model
process starts:

```powershell
$b3Sandbox = "C:\tmp\r01-b3-sandbox-20260716"
New-Item -ItemType Directory -Path $b3Sandbox

python -m v2.research.overlay `
  --artifact-root .research_artifacts/r01 `
  generate-development `
  --experiment-id r01-b3-prompt-v1-20260716 `
  --root-seed r01-phase-b-development-fixtures-v1 `
  --count 40 `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2 `
  --contract docs/research-contract-01-llm-overlay.md

python -m v2.research.overlay `
  --artifact-root .research_artifacts/r01 `
  b3-preflight `
  --manifest r01-b3-prompt-v1-20260716/development_manifest.json `
  --freeze-sha256 86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2 `
  --executable $codexNative `
  --expected-executable-sha256 cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4 `
  --sandbox-directory $b3Sandbox `
  --account-attestation docs/r01-b3-zero-cost-account-attestation.md `
  --expected-account-attestation-sha256 94ca690340273e02da7de19e0c1ea5efc8793547f2a87822dc40eb5b630b9746
```

`b3-preflight` makes zero provider calls. Do not run `b3-run` until the printed
preflight SHA-256 and its code commit have been independently reviewed and
copied into the B3 readiness report. `b3-run` is the live 12-acquisition command;
it refuses command-spec, account-attestation, executable, feature, sandbox, or
preflight hash drift before launching the next process.

Provider-free hardening uses explicit
`RETRY_TRANSPORT` / `FAIL_CLOSED_SCORE` / `STOP_PHASE` dispositions, verifies any
transport model echo, stops on unknown JSONL item or field shapes, binds the full
feature catalog into command-spec v2, and requires an externally anchored empty
sandbox outside the repository. Every complete response is consumed before
scoring: `STOP_PHASE` never scores, while `FAIL_CLOSED_SCORE` and downstream
parse/validation failures persist one disposition artifact and score one hold.
Retry-eligible failures advance only to append-only attempt 2; the second
consecutive transport failure, an initial nonzero exit without a complete
response, or the global development-attempt cap stops before another call.
Successful retries bind prior failure records, their raw transport graphs, and
token reservations. Replay reconsumes the response, verifies final-agent text
separately from JSONL stdout, and verifies both successful and failed transport
hashes. Stopped attempts may intentionally leave immutable raw evidence outside
a completed run result. Local `codex features list`
inspection and exact-tag source verification make no provider call. D2 user
approval is recorded; provider acquisition remains blocked until the B3
preflight identity is generated and independently reviewed. Evaluation
generation, sealing, and GO/NO-GO verdicts remain unavailable until their later
contract gates.
