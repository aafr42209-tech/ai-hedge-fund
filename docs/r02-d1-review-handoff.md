# R02 D1 provider-free freeze independent-review handoff

Review base: `253b777afb03df4b8944621ce32f2100da9d4016`

Review range: `253b777afb03df4b8944621ce32f2100da9d4016..HEAD`

Branch: `codex/llm-overlay-research-01`

Provider calls in this range: **0**

## Scope

Authorized and implemented here:

- append-only clarification of the sealed calibration bin convention;
- exact provider-free trigger and deterministic candidate-generator freeze
  candidate;
- six trigger/candidate/dedup/permutation test vectors;
- exploratory trigger-rate, candidate-headroom, and N/M_min analysis;
- machine freeze manifest.

Explicitly excluded:

- production R02 implementation;
- selector prompt or model selection;
- provider call, D3, or R02 execution;
- modification of sealed R01 documents or artifacts;
- final statistical freeze, provider budget, or preflight.

## Files and hashes

| File | SHA-256 |
| --- | --- |
| `docs/r01-confidence-calibration-erratum-01.md` | `a314578748d51adaae319b568253ace064cd6e28afa11acf1f2d22ad072b655b` |
| `docs/r02-d1-candidate-trigger-freeze.json` | `2d5961806b5051ff56c874b8b05933df014136bacb98717c4846f2b48f645778` |
| `docs/r02-d1-candidate-trigger-freeze.md` | `bcbe368b13d66cbade1f89c9b34699b8c72365934b3abd1d2e7a638f95aa5590` |
| `docs/r02-d1-test-vectors.json` | `2ce211673d11b3acd7865d42e2fcba012bef2e3d0099abc61b5cfa9c7279efd3` |
| `docs/r02-d1-provider-free-design-analysis.json` | `12ad836d66adb095145d7337efbfdb76b86812ac3d88cd7edfd9c514e8b29765` |
| `docs/r02-d1-provider-free-design-analysis.md` | `a2e9e726c5d3b6b146ec8c4edee3dd7d7f7406fcadbeafc1ddb538a11998e33e` |
| `docs/r02-d1-freeze-manifest.json` | `81026cdd1ab83fe7f0cea30951cf8cb1351dca6150d9aaecbfa696d932bbdeaf` |

This handoff is intentionally not self-hashed.

## Reproduction anchors

- design-frame provider-free freeze SHA-256:
  `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`;
- design-frame manifest SHA-256:
  `d9ef5150073717a802212cafbb1b9182b10c4ab329ca01ea57e16fb0baaa26ba`;
- design fixtures: 40;
- exact trigger: baseline has a trade and maximum per-line effective cost is at
  least 50 bps;
- observed design trigger rate: 5/40;
- triggered K distribution: K2=3, K3=1, K4=1;
- positive candidate-headroom cases: 4/5;
- recommended but not frozen: N=160, representative/challenge=120/40,
  `M_min=46`.

## Required review questions

1. Does the erratum preserve every sealed byte while unambiguously defining
   bins as `[0,50), ..., [90,101)`?
2. Is the trigger exactly reproducible from public fixture + deterministic
   baseline ledger, including commission and `ceil_ratio`, with no oracle or
   outcome edge?
3. Are all four candidate roles, integer-lot rounding, max-cost tie-break,
   validate-before-dedup rule, alias rule, and K=1 no-call behavior complete and
   deterministic?
4. Do all six vectors reproduce fixture hashes, trigger values, candidate IDs,
   dedup aliases, HMAC seeds, and presented order from freeze SHA
   `2d596180…5778`?
5. Does the information barrier allow hidden utility only for post-generation
   challenge admission and analysis, never trigger, candidate bytes,
   permutation, or selector request?
6. Do the 40-case counts and candidate-headroom diagnostic reproduce, including
   rejection of the broader 12-case trigger?
7. Are N=160 and `M_min=46` clearly recommendations rather than a statistical
   freeze, with final delta_min/bootstrap/budget work still blocking?
8. Are R2-D1 acceptance, R2-D2 implementation, and every live gate still closed
   pending independent review and a new user decision?
9. Are provider calls and changed `.research_artifacts` both zero?

Report findings by severity with file and line. Provider calls and R01 artifact
changes are prohibited during review.
