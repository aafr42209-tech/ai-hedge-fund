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
python -m v2.research.overlay generate-development `
  --artifact-root .research_artifacts `
  --experiment-id r01-development `
  --root-seed local-development-seed `
  --contract docs/research-contract-01-llm-overlay.md
```

Create a scripted-response JSON object keyed by acquisition key, then run:

```powershell
python -m v2.research.overlay dry-run `
  --artifact-root .research_artifacts `
  --manifest r01-development/development_manifest.json `
  --responses scripted-responses.json

python -m v2.research.overlay replay `
  --artifact-root .research_artifacts `
  --result r01-development/development_run_result.json

python -m v2.research.overlay verify `
  --artifact-root .research_artifacts `
  --reference r01-development/development_run_result.json
```

Acquisition keys use this exact form:

```text
<experiment_id>|<case_id>|development|<replicate_id>|<attempt>
```

Phase A accepts scripted raw responses only. Provider integration, prompts,
evaluation generation, sealing, and GO/NO-GO verdicts remain unavailable until
their later contract phases.
