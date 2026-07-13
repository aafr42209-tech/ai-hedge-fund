# R01 LLM overlay research — Phase A / provider-free B0

`v2.research.overlay` is the provider-free, development-only foundation for R01.
It implements deterministic fixture generation, strict validation, exact integer
scoring, complete-enumeration oracle and baselines, append-only artifacts, replay,
bootstrap analysis, and nuisance transforms.

The package intentionally has no live LLM adapter and cannot generate evaluation
fixtures. Every report is marked:

> DEVELOPMENT_ONLY — NOT SEALED — NO INVESTMENT CLAIM

## Commands

Run from the repository root:

```powershell
python -m v2.research.overlay `
  provider-free-freeze `
  --root-seed r01-phase-b-development-fixtures-v1 `
  --count 40 `
  --output docs/r01-b0-provider-free-freeze.json
```

This command uses no provider. It writes a new safe repository-relative path
exclusively and freezes the development oracle-hold scale plus complete-lattice
bounds. Absolute, drive-qualified, parent, empty-segment, and dot output paths
are rejected.

For the provider-free scripted Phase A runner:

```powershell
python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  generate-development `
  --experiment-id r01-development `
  --root-seed local-development-seed `
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
  --output scripted-responses.json

python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  dry-run `
  --manifest r01-development/development_manifest.json `
  --responses scripted-responses.json

python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  replay `
  --result r01-development/run_result.json `
  --expected-manifest-sha256 MANIFEST_SHA256_FROM_GENERATE `
  --expected-result-sha256 RESULT_SHA256_FROM_DRY_RUN

python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  verify `
  --result r01-development/run_result.json `
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
manifest hash printed by `generate-development` and the result hash printed by
`dry-run`; a missing or mismatched external anchor fails closed before scoring.

Phase A and B0 accept scripted raw responses only. Provider integration, prompts,
evaluation generation, sealing, and GO/NO-GO verdicts remain unavailable until
their later contract phases.
