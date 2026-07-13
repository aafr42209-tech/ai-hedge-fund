# R01 LLM overlay research — Phase A

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
  --result r01-development/run_result.json

python -m v2.research.overlay `
  --artifact-root .research_artifacts `
  verify `
  --result r01-development/run_result.json
```

Acquisition keys are not pipe-delimited labels. They are the SHA-256 of the
canonical JSON acquisition identity:

```text
sha256(canonical_json(AcquisitionIdentity))
```

`scripted-template` derives these keys with the production implementation, so
they should not be constructed by hand. For externally anchored replay, pass
`--expected-manifest-sha256` and `--expected-result-sha256`; a mismatch fails
closed before scoring.

Phase A accepts scripted raw responses only. Provider integration, prompts,
evaluation generation, sealing, and GO/NO-GO verdicts remain unavailable until
their later contract phases.
