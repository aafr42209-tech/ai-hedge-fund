# R02 D4 LIVE post-hoc independent-review handoff

Status: `INDEPENDENT_REVIEW_ACCEPTED`

This handoff covers provider-free statistical analysis of the already completed sealed run `r02-d4-s8-20260719`. It authorizes no new LIVE run, provider call, Codex execution, retry, replacement, or resume.

Independent review reproduced every reported number, frozen label, seed, and pinned input with no blocking finding. The accepted review of analysis commit `1950e8bded6a581f4a0806c6fa44637505f96913` is sealed in `docs/r02-d4-live-posthoc-independent-review.json`.

## Review targets

- Confirm the report reproduces from the sealed 1,254-file S6 audit root and 69-file S7 transport root.
- Confirm the full-frame ITT vector contains 200 fixtures: 150 representative and 50 challenge, with 131 frozen zero contributions.
- Confirm the base PCG64 bootstrap uses 10,000 resamples, seed `ab143af338e991209a9c3fb387623d126ab8399aba268285758234eb15f71804`, and order-statistic indexes 249 and 9,749.
- Confirm all 140 frozen robustness variants are evaluated: 69 single-fixture zero-nullifications, 69 literal leave-one-out analyses, and 5%/10% within-stratum winsorization.
- Confirm parsimony reconstruction uses the sealed candidate records and exact frozen lexicographic selector.
- Confirm analysis-side external-call counters remain zero.

## Reproduction commands

```powershell
.venv\Scripts\python.exe scripts\r02_d4_posthoc.py
.venv\Scripts\python.exe scripts\r02_d4_posthoc_verify.py
.venv\Scripts\python.exe -m pytest -q v2\research\overlay\test_r02_d4_posthoc_analysis.py
```

Expected markers:

```text
PASS_R02_D4_LIVE_POSTHOC_PROVIDER_FREE
PASS_R02_D4_LIVE_POSTHOC_INDEPENDENT_PROVIDER_FREE_VERIFY
2 passed
```

## Pinned files

- `docs/r02-d4-live-posthoc.json`: `623b8888a90af34bf7f0be20cf45ff19691e8c1545de76d00534102643b71042`
- `docs/r02-d4-live-posthoc.md`: `79bb4d4ce54a96e5a0168276a7d9e6b78ce83dda8af89c352af3d417ee964f48`
- `docs/r02-d4-live-posthoc-independent-review.json`: `efc668d817f2b344568ad549550d2dadaa8aa918c6180d5cb6ca753eabd80496`
- `v2/research/overlay/r02_d4_posthoc_analysis.py`: `52c64dba878d7489166224d0f80cb7f85ecb795a5a5bf56cdcd501afc07ec248`
- `scripts/r02_d4_posthoc.py`: `71158d25ee81ee184f1892d01da606641be9568a3995fc1f77da27c460e5dab8`
- `scripts/r02_d4_posthoc_verify.py`: `31de78adb84de5b6473ece7a50a7cb6f7e265a83197f24e63e67398a5883e53f`
- `v2/research/overlay/test_r02_d4_posthoc_analysis.py`: `a923d8e45f042ecbd7255ad8696a03b227ccb2c92aadc30ccd7b733c168fede9`

## Expected endpoint results

- Primary: `REPLICATION_SUPPORTED_FRAGILE`, theta `85,727,257`, 95% CI `[51,557,051, 119,471,784]` e12.
- Parsimony: `PARSIMONY_POLICY_SUPPORTED`, exact vector equality with primary.
- Incremental LLM: `NOT_IDENTIFIED_REDUNDANT_SELECTOR`; discordance `0/69`.
- Agreement: `69/69`; Wilson 95% `[947,263, 1,000,000]` ppm.

The fragile label is required because the minimum zero-nullification lower bound (`46,272,403`) and minimum leave-one-out lower bound (`47,592,771`) fall below the frozen `50,000,000` threshold, even though the unmodified lower bound exceeds it.
