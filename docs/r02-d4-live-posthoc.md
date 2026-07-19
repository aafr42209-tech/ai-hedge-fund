# R02 D4 LIVE post-hoc analysis

- Run: `r02-d4-s8-20260719`
- Status: `PROVIDER_FREE_POSTHOC_COMPLETE_INDEPENDENT_REVIEW_ACCEPTED`
- Valid sealed run: `true`
- Analysis boundary: provider-free; no new LIVE run, retry, replacement, or resume

## Frozen endpoints

- Primary replication: **REPLICATION_SUPPORTED_FRAGILE**; theta `85727257`, 95% bootstrap CI `[51557051, 119471784]`, threshold `50000000` e12.
- Deterministic parsimony: **PARSIMONY_POLICY_SUPPORTED**; theta `85727257`, 95% bootstrap CI `[51557051, 119471784]` e12.
- Incremental LLM: **NOT_IDENTIFIED_REDUNDANT_SELECTOR**; discordant `0`/69, theta `0`, 95% bootstrap CI `[0, 0]` e12.
- Exact selector agreement: `69`/`69` (1000000 ppm), Wilson 95% `[947263, 1000000]` ppm.

## Robustness

- Maximum one-fixture raw-theta shift: `6435445` e12 (`75069` ppm of |theta|).
- All 69 zero-nullification lower bounds pass: `false`; minimum `46272403`.
- All 69 literal leave-one-out lower bounds pass: `false`; minimum `47592771`.
- 5% winsorized lower: `70552631`; 10% winsorized lower: `63981564`.

## Execution statistics

- Attempts: `69`; settled fail-closed: `0`; unsettled: `0`.
- Provider calls in sealed source run: `69`; provider calls during analysis: `0`.
- Observed tokens: `822031`; debited tokens: `822031` / `2208000`.
- Transport duration sum: `398374` ms; median `5062` ms; max `17297` ms.

## Interpretation

The confirmatory full-frame ITT endpoint uses all 200 frozen fixtures, with zero contribution for the 131 non-eligible fixtures. The LLM selected the deterministic parsimony candidate in every eligible fixture, so the primary and parsimony vectors are byte-for-byte numerically identical. The frozen discordance floor is not met; incremental LLM value is therefore not identified, not evidence of benefit or harm.

Independent review reproduced every reported number and frozen label with no blocking finding; this report is accepted.
