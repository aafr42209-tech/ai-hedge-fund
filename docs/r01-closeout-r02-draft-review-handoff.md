# R01 closeout and R02 draft independent-review handoff

Review base: `24a0277774c01a745a058bde58d4d308eade51fe`

Review range: `24a0277774c01a745a058bde58d4d308eade51fe..HEAD`

Branch: `codex/llm-overlay-research-01`

Provider calls in this range: **0**

## Authorized scope

- seal R01 with a final closeout report and machine manifest;
- perform provider-free descriptive confidence calibration;
- draft the R02 baseline-anchored candidate-selection research contract;
- draft R02 trigger-aware statistics and audit schemas.

Explicit exclusions:

- no provider call;
- no D3 approval;
- no R02 execution or implementation;
- no modification or backfill of existing R01 artifacts;
- no R01 confirmatory relabeling;
- no confidence threshold selection.

## Files and expected hashes

| File | SHA-256 |
| --- | --- |
| `docs/r01-confidence-calibration-exploratory.json` | `41904983538677f4b1bc33c1c467dd7a0689fa9e8470de745ec1a82b4f728df1` |
| `docs/r01-confidence-calibration-technical-report.md` | `16188f2dcd09fa905a0502f33ad6dc8953b21268ec2e32c4d594488e5e64586b` |
| `docs/r01-final-closeout-manifest.json` | `a9bb04131d9214a17b99a6423900e3b83f1a7345e4bf63c3ca760553654b3ada` |
| `docs/r01-final-closeout.md` | `3f49b228ecf006b70e39e9897574c75f078ca12eca4bce5dfdf5e98ca770a9e3` |
| `docs/r02-candidate-generator-options.md` | `e360db59e7d852d0d661360ec8871f629afa24961fdee946048c31d177ebbfe3` |
| `docs/research-contract-02-candidate-selection-draft.md` | `3c08c1c8131c110a96794a20d9ab41ba65b7f67c1b45cb602a26542449c44421` |
| `docs/r02-statistical-design-draft.md` | `50fee05114678e645ee3f3ebb30c6dc62cd7a50980864d4020b267ab88b914a5` |
| `docs/r02-audit-schema-draft.json` | `1a987172d14b371348fb39dd44c4268dc534c1438b08b563b5b5a5fe8c9c13b6` |
| `docs/r02-audit-schema-draft.md` | `2264ae5219bd68aadeb2ba69060742450cd1ae521465fc438a597f2e167cec1b` |

This handoff file is intentionally not self-hashed.

## Reproduced R01 anchors

- existing artifact files: 299;
- canonical tree SHA-256:
  `6ecbab78625ced153cb4b446fc8e911890476c144f361769e2073c142fd5c30e`;
- run-result SHA-256:
  `c262fac9efd5b725138e9b89b92f9043f17ee5398012348957ecf6331fd6c349`;
- replay SHA-256:
  `a915ffbbd75e74aaa545cf91ea8ee7a904903609f04b03b1bd954c6fe3b31339`;
- preflight SHA-256:
  `5937161ac9c2bb9c22172d0be27a5a730cc2a3dc1c8bf51044270b65ee68353e`;
- changed files under `.research_artifacts`: 0.

## Validation already run

```text
JSON parse: 3/3 machine documents passed
git diff --check: clean
pytest v2/research/overlay -q: 127 passed
provider calls: 0
```

## Required review questions

1. Do the closeout manifest hashes reproduce, and does the R01 tree remain
   exactly 299 files with the stated canonical hash?
2. Are the final labels symmetric and contract-safe: infrastructure PASS,
   structural stability PASS, utility hypothesis NOT TESTED, and no investment
   claim or confirmatory relabeling?
3. Does calibration correctly retain 72 raw values, collapse to 36 paired asset
   observations, treat six fixture pairs as the inferential boundary, and avoid
   selecting a threshold?
4. Does the R02 contract prevent the LLM from generating portfolios, require
   baseline/no-change protection, remove veto and continuous scale fields, and
   block oracle/outcome leakage into candidates and prompts?
5. Does the statistical design make the all-fixture paired delta primary,
   include zero deltas for baseline/no-call episodes, couple N to trigger rate,
   and force `INCONCLUSIVE_LOW_TRIGGER` when `M < M_min`?
6. Do the audit schemas bind trigger, candidate set, permutation, no-call,
   provider call, fallback, and scoring paths without orphan evidence?
7. Is every R02 item visibly a provider-free draft with implementation,
   preflight, D3, and execution gates still closed?

Report findings by severity with file and line. State explicitly whether the
package is approved for **provider-free design completion only**. Do not run a
provider command or create/modify R01 artifacts during review.
