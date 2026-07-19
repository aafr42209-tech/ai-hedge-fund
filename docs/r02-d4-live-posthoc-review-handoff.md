# R02 D4 LIVE post-hoc independent-review handoff

Status: `PENDING_INDEPENDENT_REVIEW`

This handoff covers provider-free statistical analysis of the already completed sealed run `r02-d4-s8-20260719`. It authorizes no new LIVE run, provider call, Codex execution, retry, replacement, or resume.

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

- `docs/r02-d4-live-posthoc.json`: `1556ca1bf3585d765e7d4627ef1b0425848729cfca857910d218f89227627177`
- `docs/r02-d4-live-posthoc.md`: `03a036c00853b5a8f040a5b9e74cfa7c086854aec9b4a8359b34848952782ab7`
- `v2/research/overlay/r02_d4_posthoc_analysis.py`: `73cac6e77fa25cd53e4442e68f04e4e6eda52cb8f446f42f965969700698c795`
- `scripts/r02_d4_posthoc.py`: `71158d25ee81ee184f1892d01da606641be9568a3995fc1f77da27c460e5dab8`
- `scripts/r02_d4_posthoc_verify.py`: `14dcb8e7f47c7924ae71730de8f4f72920e7cca37b47ef6b867e3b596038b627`
- `v2/research/overlay/test_r02_d4_posthoc_analysis.py`: `a923d8e45f042ecbd7255ad8696a03b227ccb2c92aadc30ccd7b733c168fede9`

## Expected endpoint results

- Primary: `REPLICATION_SUPPORTED_FRAGILE`, theta `85,727,257`, 95% CI `[51,557,051, 119,471,784]` e12.
- Parsimony: `PARSIMONY_POLICY_SUPPORTED`, exact vector equality with primary.
- Incremental LLM: `NOT_IDENTIFIED_REDUNDANT_SELECTOR`; discordance `0/69`.
- Agreement: `69/69`; Wilson 95% `[947,263, 1,000,000]` ppm.

The fragile label is required because the minimum zero-nullification lower bound (`46,272,403`) and minimum leave-one-out lower bound (`47,592,771`) fall below the frozen `50,000,000` threshold, even though the unmodified lower bound exceeds it.
