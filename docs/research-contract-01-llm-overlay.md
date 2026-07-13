# R01 Research Contract: Constrained LLM Portfolio Overlay

## Contract status

- Contract ID: `R01-llm-overlay-synthetic-v1`
- Status: **DRAFT — NOT SEALED**
- Implementation base: `fork/main` at `09dd33167bd6b4ea63ae32e7246e70e80632cc81`
- Implementation branch: `codex/llm-overlay-research-01`
- Research mode: synthetic and fixture-only
- Historical market-performance claims: prohibited

No evaluation run is authorized while this document is marked `DRAFT` or while any required seal field is `TBD`.

## 1. Research question

> Given identical quantitative signals, portfolio state, risk limits, and transaction costs, does an LLM portfolio overlay make better decisions than a preregistered deterministic combiner?

The repository-specific treatment is the LLM's conversion of an already-formed signal panel into a portfolio order set. Signal discovery, market-data quality, and investor-persona profitability are outside this experiment.

## 2. Primary hypothesis

The LLM overlay has lower cost-adjusted normalized regret to a hidden oracle than the primary deterministic baseline on a sealed set of synthetic portfolio episodes.

Formally:

```text
H1: mean(NR_deterministic - NR_llm) > delta_min
```

where `NR` is normalized regret and `delta_min` is the preregistered superiority margin frozen after the development pilot and before evaluation fixtures are generated.

## 3. Claims permitted and prohibited

### Permitted claims

- Decision quality within the preregistered synthetic data-generating process.
- Portfolio-joint constraint compliance.
- Stability across repeated identical requests.
- Invariance to asset, signal, and JSON-key ordering.
- Sensitivity to costs, risk limits, and current holdings.
- Parse, fallback, abstention, and artifact-completeness rates.

### Prohibited claims

- Historical or forward market alpha.
- Expected real-money returns.
- Superiority of a named investor persona.
- Validity of the current `src/` backtester.
- Point-in-time validity of any real data provider.
- Production or live-trading readiness.
- Generalization beyond the sealed generator families.

## 4. Experimental unit

One experimental unit is a single synthetic portfolio decision episode.

Each episode contains:

- six anonymous assets identified only as `A0` through `A5`;
- asset prices and integer lot sizes;
- current integer share holdings and cash;
- five normalized quantitative signals per asset;
- signal confidence values;
- a positive-semidefinite covariance matrix;
- per-asset maximum weights;
- a portfolio gross-exposure limit;
- commission, spread, and slippage parameters;
- hidden expected returns used only by the oracle and scorer;
- a deterministic episode seed and canonical content hash.

The first contract is long-only. Short sales, margin, borrow fees, and covering logic require a separate follow-up contract.

No real ticker, company name, calendar date, price path, filing, estimate, or news text may appear in an R01 fixture.

## 5. Observable and hidden state

### Visible to every policy

- anonymous asset IDs;
- current prices, holdings, and cash;
- signal values and confidence;
- covariance and risk limits;
- the complete transaction-cost schedule;
- the same output schema and validation rules.

### Hidden from every policy except the oracle

- true expected returns;
- generator regime label when the label would reveal the optimal rule;
- oracle target portfolio;
- realized episode utility;
- evaluation-set aggregate results.

The deterministic baseline and LLM treatment must consume byte-identical canonical policy inputs for each episode.

## 6. Synthetic data-generating process

The generator must produce a balanced mixture of these preregistered regimes:

1. **Signal consensus** — most signals agree on relative attractiveness.
2. **Signal conflict** — signals disagree and confidence carries useful information.
3. **High transaction cost** — expected edge is small relative to turnover cost.
4. **Concentration pressure** — attractive assets approach position or gross limits.
5. **Existing-position asymmetry** — current holdings make buy and sell utility asymmetric.
6. **Noisy confidence** — signal magnitude and confidence are imperfectly aligned.

The generator must satisfy these requirements:

- covariance matrices are positive semidefinite;
- prices, holdings, and lot sizes imply feasible nontrivial actions;
- at least one feasible portfolio exists in every valid episode;
- hold is always feasible;
- the oracle is deterministic for fixed episode bytes;
- regime frequencies are fixed before evaluation;
- development and evaluation seeds are disjoint;
- no evaluation fixture may be inspected before the manifest is sealed.

Generator code, configuration, seed policy, and canonical serializer are part of the experiment identity.

### 6.1 Invariance audit subset

The sealed evaluation manifest selects `40` of the `200` standard evaluation fixtures as invariance audit anchors. Selection is deterministic, frozen before acquisition, and balanced so regime counts differ by at most one.

For each audit anchor and asset, the canonical reference action is the modal action across all five primary replicates. This reuses already-budgeted primary acquisitions and reduces contamination from identical-prompt sampling noise. If two or more actions tie for the mode, the canonical reference action is `ABSTAIN`. Four additional provider acquisitions are made:

1. asset-order permutation;
2. signal-order permutation;
3. JSON-key-order permutation that preserves all values;
4. representation permutation combining semantically irrelevant wording and numerically equivalent formatting.

These `160` successful audit acquisitions are excluded from the primary utility endpoint. They exist only for preregistered invariance metrics and gates.

## 7. Policies under comparison

### 7.1 Primary deterministic baseline

A fixed weighted signal score followed by deterministic ranking, risk scaling, cost-aware sizing, and portfolio-joint validation.

Rules and coefficients may be developed only on the development fixtures. They are frozen before evaluation fixtures are generated.

### 7.2 Safety baselines

- **Hold:** submit no orders.
- **Equal risk:** form an inverse-volatility target from the covariance diagonal using deterministic integer square root, then choose the feasible batch with minimum asset-level `L1` distance between target and post-trade `weight_e12`. Exact distance ties are resolved by lower cost, lower turnover, then the lexicographic `A0` through `A5` final-share vector.

Safety baselines are secondary comparisons and cannot replace the primary deterministic baseline after sealing.

### 7.3 LLM treatment

One provider, one exact model ID, one system prompt, one user-template version, and one sampling configuration form the primary treatment.

Cross-model, cross-provider, and persona comparisons are excluded from R01. They require new experiment IDs.

## 8. Required decision schema

Every policy returns exactly one decision object for every asset:

```json
{
  "decisions": {
    "A0": {
      "action": "buy | sell | hold",
      "quantity": 0,
      "confidence": 0,
      "reasoning": "short text"
    }
  }
}
```

Contract rules:

- every asset appears exactly once;
- no unknown asset is allowed;
- quantity is a nonnegative integer number of shares;
- a nonzero quantity must be an exact multiple of that asset's visible `lot_size`;
- a buy or sell may contain at most `2` lots per asset;
- `hold` requires quantity `0`;
- `buy` and `sell` require a strictly positive quantity;
- confidence is an integer in `[0, 100]`;
- reasoning is retained but never used by the primary scorer;
- omitted, duplicated, malformed, or extra decisions invalidate the raw batch.

## 9. Portfolio-joint validator

All policies pass through the same deterministic validator.

It checks:

- schema validity;
- action and quantity validity;
- sell quantity does not exceed current holdings;
- post-trade cash remains nonnegative after all costs;
- per-asset maximum weights;
- gross-exposure limit;
- finite prices, signals, covariance values, and costs;
- order-set feasibility independent of asset input order.

Validation is fail-closed:

- any invalid raw order batch becomes the hold portfolio for scoring;
- the original raw decision and all violations remain preserved;
- no silent clipping, ticker-priority fill, or partial rescue is allowed;
- raw violations and executable violations are reported separately.

Executable constraint violations must be exactly zero. Any nonzero executable violation invalidates the full experiment.

## 10. Transaction-cost and utility model

The same deterministic cost model applies to every policy:

```text
notional_cents(order) = price_cents * quantity_shares
half_spread_cents(order) = ceil(notional_cents * half_spread_bps / 10,000)
slippage_cents(order) = ceil(notional_cents * slippage_bps / 10,000)
cost_cents(order) = commission_cents + half_spread_cents + slippage_cents
cost_return(batch) = total_cost_cents(batch) / pretrade_equity_cents
```

Commission is charged once for each nonzero order. All cost terms are functions of fixture fields and executed quantity. No policy may supply or override its own cost estimate.

All orders in a batch are applied simultaneously. Post-trade weights use:

```text
posttrade_equity_cents = pretrade_equity_cents - total_cost_cents
w_i = posttrade_position_value_cents_i / posttrade_equity_cents
```

`posttrade_equity_cents` must be strictly positive.

Policy utility is:

```text
U(policy) = mu' w - lambda * (w' Sigma w) - cost(delta_w)
```

where:

- `mu` is hidden expected return;
- `w` is the post-trade portfolio weight vector;
- `Sigma` is the fixture covariance matrix;
- `lambda` is the frozen dimensionless risk-aversion parameter encoded as `lambda_ppm / 1,000,000`;
- `cost(delta_w)` is total deterministic transaction cost normalized by pre-trade equity.

### 10.1 Exact arithmetic and scoring identity

All authoritative utility values use signed integer fixed point with scale `UTILITY_SCALE = 10^12`. Floating-point utility, weights, regret, means, or verdict inputs are prohibited.

`round_ratio_half_even(n, d)` is the only permitted division primitive for scoring. `d` must be positive. It divides `abs(n)` into quotient `q` and remainder `r`; it increments `q` when `2r > d`, or when `2r == d` and `q` is odd, then restores the sign of `n`.

The scoring DAG is fixed as follows:

```text
return_e12 = round_ratio_half_even(
  sum_i(mu_bp_i * posttrade_position_value_cents_i) * UTILITY_SCALE,
  10,000 * posttrade_equity_cents
)

risk_e12 = round_ratio_half_even(
  lambda_ppm
    * sum_i_j(
        posttrade_position_value_cents_i
        * covariance_bp2_i_j
        * posttrade_position_value_cents_j
      )
    * UTILITY_SCALE,
  1,000,000 * 100,000,000 * posttrade_equity_cents^2
)

cost_e12 = round_ratio_half_even(
  total_cost_cents * UTILITY_SCALE,
  pretrade_equity_cents
)

utility_e12 = return_e12 - risk_e12 - cost_e12
```

Every numerator is formed from raw integer fixture and execution fields. There is exactly one final division for each utility term. Intermediate rounded weights, returns, covariance values, or costs must not feed another utility term. Human-readable decimals are derived displays and are never authoritative or hashed as score inputs.

The units, constants, formulas, operation order, and rounding rule above are part of `scoring_spec_sha256`.

The oracle maximizes the same utility over the same finite action lattice.

The oracle must be exact. R01 uses complete enumeration of the common finite lattice and fixes `oracle_optimality_tolerance_e12` to `0`. Approximate-oracle mode is prohibited. The generator must cap lot choices so enumeration is tractable for all six-asset episodes.

Every oracle result stores a complete enumeration certificate. If any policy has `utility_e12` greater than the oracle, the run is INVALID. Exact equality is resolved by lower total cost, lower turnover, then the lexicographic `A0` through `A5` final-share vector. Regret at exact equality is zero.

## 11. Primary endpoint

R01 uses one fixed utility scale for every evaluation episode. The scale is derived only from development fixtures:

```text
regret_scale = max(
  median_development(U(oracle) - U(hold)),
  normalization_epsilon
)
```

Both `normalization_epsilon` and the resulting `regret_scale` are seal fields. Evaluation data cannot change them.

Both are stored in authoritative `utility_e12` units. Normalized regret is stored as:

```text
NR_e12(p) = round_ratio_half_even(
  max(U_e12(oracle) - U_e12(p), 0) * UTILITY_SCALE,
  regret_scale_e12
)
```

Normalized regret for policy `p` is:

```text
NR(p) = max(U(oracle) - U(p), 0) / regret_scale
```

This fixed denominator prevents high-transaction-cost episodes, where hold is near optimal, from exploding because of a near-zero per-case denominator.

No post-hoc clipping or winsorization is allowed. Before the evaluation manifest is sealed, the generator must enumerate the complete feasible action lattice for every fixture and certify both:

```text
max_over_feasible_policies(abs(U(p))) <= max_abs_utility
max_over_feasible_policies(NR(p)) <= max_normalized_regret
```

The certificate is a generator preflight artifact, not a property inferred from any evaluated policy's realized action. A missing or failed certificate is a generator-contract failure and prevents seal. Because every executable policy output belongs to the certified lattice, poor policy performance remains a valid NO-GO outcome and cannot become INVALID merely by producing high regret.

The primary endpoint is:

```text
Delta = mean_over_cases(NR(primary_deterministic) - NR(LLM))
```

For the LLM, case-level `NR_e12` is `round_ratio_half_even(sum(replicate_NR_e12), 5)` across the five independent acquisition replicates. Every evaluation case receives equal weight regardless of replicate variance. Every other integer mean in R01, including the case-level primary endpoint, uses `round_ratio_half_even(sum(values), count)`.

A positive `Delta` favors the LLM.

## 12. Statistical analysis

- Unit of resampling: evaluation case, not individual replicate.
- Interval: paired nonparametric bootstrap two-sided 95% percentile confidence interval.
- Bootstrap resamples: 10,000.
- Bootstrap RNG seed: frozen in the sealed manifest.
- Primary test direction: LLM improvement beyond the `delta_min` superiority margin.
- Missing cases: prohibited; they are not dropped or replaced.
- Secondary endpoints: descriptive unless a later contract assigns multiplicity control.

The confirmatory GO condition is:

```text
lower_bound_95_ci > delta_min
```

`delta_min` must be selected from development-fixture scale only. It cannot be changed after the evaluation manifest exists.

The development pilot also freezes `delta_target`, where `delta_target > delta_min`, for prospective power analysis. Before seal, the preregistered power procedure must estimate at least `80%` power for `200` cases by simulating the actual decision rule: the lower endpoint of the paired two-sided 95% percentile bootstrap interval must exceed `delta_min`. This corresponds to nominal one-sided alpha `0.025`, not `0.05`. If estimated power is below `80%`, the sample size and all dependent budgets must be increased before seal, or the experiment must not seal. The margin cannot be reduced merely to pass the power gate.

The paired bootstrap operates on case-level `Delta_e12` values. Each of `10,000` resamples draws `n` case indices with replacement using NumPy `PCG64`, the sealed bootstrap seed, and the sealed NumPy version. Each resampled mean is `round_ratio_half_even(sum(values), n)`.

The percentile interval uses the nearest-rank rule. For `10,000` sorted bootstrap means, the lower and upper endpoints are the `250`th and `9,750`th values in one-based notation, implemented as zero-based indices `249` and `9,749`.

Prospective power uses the `40` development case effects as an empirical distribution. It shifts every development effect by `delta_target_e12 - mean_development_e12`, then runs `1,000` simulated trials. Each trial draws `200` cases with replacement from those `40` shifted effects and applies the same `10,000`-resample percentile procedure and GO inequality. For zero-based trial index `k`, the trial-data and inner-CI PCG64 seeds are the unsigned big-endian integers represented by the first `128` bits of SHA-256 over `"power-trial|<power_seed>|<k>"` and `"power-ci|<power_seed>|<k>"`, respectively. Estimated power is the integer success count divided by `1,000`.

RNG type, NumPy version, seed derivation, draw order, integer dtype, resample counts, integer-mean rule, and percentile indices are part of `analysis_spec_sha256`.

## 13. Secondary endpoints

- exact action agreement across identical repeats;
- per-asset quantity variance;
- raw constraint-violation rate;
- executable constraint-violation rate;
- parse and schema-failure rate;
- provider-call failure rate;
- fallback/hold rate;
- asset-order permutation flip rate;
- signal-order permutation flip rate;
- JSON-key-order permutation flip rate;
- irrelevant-wording and numeric-format flip rate;
- expected turnover;
- total transaction cost;
- confidence calibration against synthetic directional truth.

Permutation checks compare outputs after mapping permuted anonymous IDs back to the canonical asset order.

### 13.1 Exact action agreement

Parse or provider failures are encoded as the sentinel action `ABSTAIN`; they are not excluded.

For each standard evaluation `(case, asset)`, the five primary replicates create ten unordered replicate pairs. Exact action agreement is:

```text
action_agreement =
  sum(I[action_r == action_s])
  / number_of_case_asset_replicate_pairs
```

The gate applies to this pairwise, asset-level micro aggregate across all case-asset-replicate pairs. Quantity agreement is reported separately and does not alter the action label.

### 13.2 Invariance flip rate

For perturbation type `t`, compare its response to the per-asset modal action across the five primary replicates after inverse-mapping anonymous asset IDs. Parse or provider failures remain `ABSTAIN`. A tie for the primary modal action is also encoded as `ABSTAIN`:

```text
flip_rate_t =
  sum(I[action_permuted != modal_action_primary])
  / number_of_audit_case_assets
```

Each of the four perturbation-specific rates must pass the gate independently. A pooled rate and a strict batch-flip rate, where any changed asset flips the full order set, are reported descriptively but are not GO gates.

The canonical implementation of all gate metrics is hashed into `gate_metric_spec_sha256` at seal. Metric formulas cannot change during evaluation or replay.

## 14. Safety and quality gates

The experiment is eligible for GO only if all gates pass:

| Gate | Threshold |
| --- | ---: |
| Executable constraint violations | exactly `0` |
| Missing or corrupt required artifacts | exactly `0` |
| Parse plus fallback rate, primary and invariance separately | `<= 1%` for each |
| Raw violations on standard fixtures | `<= 1%` |
| Each asset-level invariance flip rate | `<= 5%` |
| Pairwise asset-level exact action agreement | `>= 90%` |
| Exact oracle certificates | `100%` |
| Policy utility above oracle beyond tolerance | exactly `0` |
| Prospective power at `delta_target` | `>= 80%` before seal |
| Provider/model identity mismatches | exactly `0` |
| Budget overruns | exactly `0` |

Adversarial validator fixtures are a separate deterministic property-test suite. They inject malformed and infeasible raw order batches directly into the validator, make zero provider calls, are not part of the `200` evaluation fixtures, and do not enter LLM rates. The suite must pass completely before seal. Any future adversarial LLM-prompt study requires a new contract and budget.

Passing the primary endpoint while failing any safety gate produces **NO-GO**.

## 15. Sample and provider-call budget

### Development

- Development fixtures: `40`.
- Final candidate-prompt pilot: at least `80` successful acquisitions, two per fixture.
- Maximum development provider attempts including prompt iteration and retries: `200`.
- Development fixtures and outputs are never included in the confirmatory result.

### Primary sealed evaluation

- Evaluation fixtures: `200`.
- Independent acquisition replicates per fixture: `5`.
- Required successful evaluation acquisitions: `1,000`.
- Maximum primary evaluation provider attempts including retries: `1,100`.
- Maximum attempts per `(case_id, replicate_id)`: `2`, consisting of one initial attempt and at most one retry.

### Invariance audit

- Audit anchors: `40`, selected from the `200` standard evaluation fixtures.
- Canonical anchor reference: per-asset modal action across the five primary replicates, requiring no extra call; modal ties become `ABSTAIN`.
- Perturbation types per anchor: `4`.
- Required successful invariance acquisitions: `160`.
- Maximum invariance provider attempts including retries: `180`.
- Maximum attempts per `(case_id, perturbation_id)`: `2`.

### Global cap

- Maximum provider attempts across R01: `1,480`.
- Every retry counts against the cap.
- Failed calls are not replaced with new fixtures or extra replicates.
- Input-token, output-token, and USD caps are required seal fields.

If a required acquisition remains unsuccessful after its per-acquisition retry, the run is INVALID even when global retry capacity remains. If any cap is exceeded, the run stops without a verdict. Continuing requires a new experiment ID and contract.

## 16. Acquisition and replay modes

Repeated identical prompts must be genuine independent acquisitions, not prompt-cache hits.

### Acquisition mode

- each primary `(case_id, replicate_id)` and audit `(case_id, perturbation_id)` permits one initial request and at most one retry;
- replicate ID is part of the artifact identity;
- perturbation ID is part of invariance-artifact identity;
- responses are append-only and never overwritten;
- the exact raw response is stored before parsing.

### Replay mode

- makes zero provider calls;
- loads only artifacts named by the sealed manifest;
- reproduces parsing, validation, scoring, and reports;
- fails if any hash differs.

An existing prompt cache may support replay, but a cache hit can never count as a new replicate.

## 17. Artifact contract

Every evaluation replicate preserves these distinct artifacts:

1. experiment manifest;
2. canonical fixture bytes;
3. canonical policy input;
4. exact system and user prompts;
5. provider request metadata;
6. raw provider response;
7. parsed raw decision;
8. validation report;
9. executable hold-or-order batch;
10. cost ledger;
11. episode score;
12. exact oracle certificate;
13. replay verification result.

Artifact identity includes:

- contract ID;
- experiment ID;
- case ID;
- replicate ID;
- perturbation ID or canonical sentinel;
- full SHA-256 fixture hash;
- full SHA-256 prompt hash;
- exact model and provider identity;
- sampling parameters;
- code commit;
- dependency-lock hash;
- generator configuration hash;
- oracle solver, version, configuration, and optimality tolerance;
- gate metric specification hash;
- power-analysis specification hash;
- request and response timestamps;
- provider request ID and response metadata when available.

All canonical JSON uses sorted keys, UTF-8, explicit numeric rules, and no non-semantic whitespace before hashing.

## 18. Fail-closed stop rules

Stop immediately and issue no GO/NO-GO performance verdict if any of these occur:

- model ID or sampling configuration changes;
- provider returns a different model identity;
- manifest, fixture, prompt, or artifact hash mismatch;
- raw response is missing;
- evaluation fixture is missing or replaced;
- provider-call, token, or USD budget is exceeded;
- a required acquisition exhausts its per-acquisition retry;
- executable constraint violation is detected;
- an oracle certificate is missing or a policy beats the oracle beyond tolerance;
- a fixture lacks or fails its pre-seal full-feasible-lattice utility and normalized-regret certificate;
- evaluation code or dependency lock changes after sealing;
- baseline, prompt, scorer, generator, or endpoint changes after sealing;
- replay fails to reproduce the sealed score.

A stopped run remains immutable. A corrected run requires a new experiment ID and a new seal.

## 19. Development, freeze, and evaluation phases

### Phase A — contract implementation

- implement schemas, generator, oracle, baselines, validator, scorer, paired-bootstrap and power analysis, asset-order/signal-order/JSON-key-order transforms and canonical inverse mappings, the representation-transform interface, and artifact store;
- add property tests for feasibility, determinism, hashing, and order invariance;
- make no real provider calls.

### Phase B — development pilot

- use only development fixtures;
- debug prompts and parsing;
- state in every candidate prompt that quantity is in shares, must be a visible-lot multiple, and is capped at two lots per asset;
- measure token use and expected cost;
- run the final candidate prompt for at least two acquisitions on every development fixture;
- set `delta_min`, `delta_target`, `normalization_epsilon`, `regret_scale`, token caps, USD cap, and final quality thresholds;
- freeze exact formulas and implementations for action agreement and invariance flip rates;
- measure identical-prompt disagreement on development acquisitions and confirm that the `5%` flip gate retains adequate margin above the sampling-noise floor; if it does not, change and document the sampling configuration or amend the draft thresholds before seal;
- freeze `scoring_spec_sha256` and `analysis_spec_sha256`;
- run the preregistered prospective power check for `200` evaluation cases;
- increase sample size and dependent budgets before seal if estimated power is below `80%`;
- do not generate evaluation fixtures.

### Phase C — seal

- freeze code commit and dependency lock;
- freeze model, provider, prompt, and sampling configuration;
- freeze generator and evaluation seed policy;
- freeze exact oracle implementation, certificate format, and tolerance;
- freeze the `40` invariance audit anchors and four perturbation transforms;
- freeze gate-metric and power-analysis specification hashes;
- generate the evaluation manifest;
- record all hashes and sign-off fields;
- change contract status to `SEALED`.

### Phase D — single acquisition run

- execute the manifest once;
- acquire both the `1,000` primary responses and `160` invariance responses within their separate attempt budgets;
- do not tune, replace, relabel, or extend cases;
- stop on any fail-closed condition.

### Phase E — replay and verdict

- replay from sealed raw artifacts with zero provider calls;
- calculate the preregistered primary endpoint and gates;
- publish one immutable `GO`, `NO-GO`, or `INVALID` verdict.

## 20. Implementation boundary

Recommended package layout:

```text
v2/research/overlay/
  __init__.py
  contracts.py
  fixtures.py
  oracle.py
  baselines.py
  llm_policy.py
  validator.py
  scoring.py
  artifacts.py
  runner.py
  report.py
  test_contracts.py
  test_fixtures.py
  test_validator.py
  test_scoring.py
  test_artifacts.py
```

R01 may reuse provider-client interfaces and raw-response parsing patterns from `v2/llm`. It must not use the current historical backtester, real data clients, event studies, optimizer stubs, or portfolio/risk stubs as part of the confirmatory path.

## 21. Required deliverables

- this reviewed and sealed research contract;
- implementation and property-test suite;
- development-pilot report;
- sealed experiment manifest;
- append-only acquisition artifacts;
- deterministic replay package;
- final verdict report;
- machine-readable primary and secondary results.

## 22. Verdict rules

### GO

Issue GO only when:

- the primary endpoint satisfies `lower_bound_95_ci > delta_min` using the paired two-sided 95% percentile bootstrap interval;
- every safety and artifact gate passes;
- replay reproduces all scores and the verdict.

GO authorizes planning the next research contract. It does not authorize historical backtesting, paper trading, or live trading.

### NO-GO

Issue NO-GO when the run is valid but:

- the primary endpoint does not satisfy `lower_bound_95_ci > delta_min`;
- any preregistered safety threshold fails;

The hypothesis must not be rescued by changing prompts, baselines, thresholds, or endpoints after evaluation.

### INVALID

Issue INVALID when a fail-closed stop condition prevents a valid confirmatory result. INVALID is not GO or NO-GO and cannot be relabeled.

## 23. Seal record

All fields below are mandatory before status changes to `SEALED`:

```yaml
contract_id: R01-llm-overlay-synthetic-v1
experiment_id: TBD
code_commit: TBD
dependency_lock_sha256: TBD
generator_config_sha256: TBD
evaluation_manifest_sha256: TBD
invariance_anchor_manifest_sha256: TBD
adversarial_validator_suite_sha256: TBD
provider: TBD
exact_model_id: TBD
model_version_metadata: TBD
sampling_parameters: TBD
system_prompt_sha256: TBD
user_template_sha256: TBD
delta_min_e12: TBD
delta_target_e12: TBD
normalization_epsilon_e12: TBD
regret_scale_e12: TBD
max_abs_utility_e12: TBD
max_normalized_regret_e12: TBD
feasible_lattice_bound_certificate_sha256: TBD
risk_aversion_lambda_ppm: TBD
max_trade_lots_per_asset: 2
utility_scale: 1000000000000
scoring_spec_sha256: TBD
analysis_spec_sha256: TBD
oracle_solver: TBD
oracle_solver_version: TBD
oracle_config_sha256: TBD
oracle_optimality_tolerance_e12: 0
gate_metric_spec_sha256: TBD
estimated_power_successes_at_delta_target: TBD
numpy_version: TBD
bootstrap_seed: TBD
power_seed: TBD
bootstrap_resamples: 10000
power_simulations: 1000
per_acquisition_max_attempts: 2
max_development_provider_attempts: 200
max_primary_evaluation_provider_attempts: 1100
max_invariance_provider_attempts: 180
max_provider_attempts: 1480
max_input_tokens: TBD
max_output_tokens: TBD
max_usd: TBD
sealed_at_utc: TBD
sealed_by: TBD
```

## 24. Decision log

- R01 is synthetic-only to eliminate historical market-data leakage and model-weight outcome contamination.
- R01 studies the portfolio overlay, not upstream signal generation or investor personas.
- Long-only scope is intentional; short and margin mechanics require a separate contract.
- One deterministic primary baseline prevents post-hoc baseline shopping.
- The primary deterministic baseline is intentionally strong: it uses a fixed signal-derived expected-return estimate and searches the same feasible lattice as the oracle. This makes R01 a conservative test of incremental LLM value.
- One primary endpoint prevents endpoint relabeling.
- The 95% confidence-interval lower bound must exceed `delta_min`; R01 uses a true superiority-margin criterion rather than a zero-margin significance test.
- Prospective power is checked at a separate `delta_target > delta_min` using the actual two-sided 95% bootstrap lower-bound rule, equivalent to nominal one-sided alpha `0.025`; an underpowered experiment cannot seal.
- Repeated calls measure expected LLM policy behavior and stability.
- Forty sealed audit anchors and four perturbations fund the invariance GO gate without contaminating the primary endpoint; each anchor uses the per-asset modal action across five primary replicates, with ties mapped to `ABSTAIN`, as its noise-robust reference.
- A fixed development-derived regret scale prevents near-optimal hold episodes from creating near-zero denominators.
- No evaluation-driven clipping or winsorization is allowed.
- Utility and normalized-regret bounds are certified over each fixture's complete feasible action lattice before seal, so poor policy performance cannot be relabeled INVALID.
- The oracle uses complete enumeration and authoritative integer scoring with `oracle_optimality_tolerance_e12: 0`; approximate oracle results are prohibited.
- Utility, regret, and their means use authoritative `e12` integer arithmetic; transaction cost is normalized by pre-trade equity.
- Quantity is measured in shares, must be a visible-lot multiple, and is capped at two lots per asset; these rules must appear in the LLM prompt.
- A modal-anchor tie becomes `ABSTAIN` and is intentionally eligible to count as a flip independently for each of the four perturbation types; it is never deduplicated or dropped.
- Adversarial validator fixtures are deterministic, provider-free pre-seal tests rather than evaluation calls.
- Acquisition and replay are separate so cache hits cannot masquerade as independent samples.
- Invalid raw order batches fail closed to hold; no silent execution repair is allowed.
- A negative result is a valid terminal result for R01.

## 25. Draft review resolution log

| Review issue | Resolution |
| --- | --- |
| Permutation gate had no call budget | Added `40` sealed audit anchors, four perturbations, `160` successful acquisitions, and `180` maximum attempts. |
| Per-case normalized-regret denominator could collapse | Replaced it with one fixed development-derived `regret_scale`; added epsilon, bounds, and seal fields. |
| Retry headroom was too small | Increased primary attempt capacity to `1,100`, added per-acquisition one-retry limits, and separated audit retry capacity. |
| Agreement and flip metrics were undefined | Added pairwise asset-level action agreement and perturbation-specific asset-level flip formulas plus a metric-spec hash. |
| Oracle exactness was unspecified | Required an exact finite-lattice oracle, certificate, solver identity, tolerance, and INVALID rule for oracle violations. |
| GO test used a zero CI margin | Changed GO to `lower_bound_95_ci > delta_min`. |
| Adversarial fixture ownership and budget were unspecified | Defined a separate provider-free deterministic validator suite outside the `200` evaluation fixtures. |
| No prospective power gate | Added `delta_target`, preregistered power analysis, and a minimum `80%` pre-seal power requirement. |
| Verdict section retained the obsolete zero-margin CI rule | Unified all GO language on the single confirmatory rule `lower_bound_95_ci > delta_min`. |
| Invariance flips could confound prompt perturbation with identical-prompt sampling noise | Replaced the replicate-0 anchor with the per-asset modal action across five primary replicates; modal ties fail closed to `ABSTAIN`. |
| Power analysis used alpha `0.05` while the 95% CI decision rule implied `0.025` | Required power simulation of the actual two-sided 95% bootstrap lower-bound rule and recorded nominal one-sided alpha `0.025`. |
| Realized-policy regret could turn poor performance into INVALID | Moved bound validation to a pre-seal certificate over every feasible action in each fixture. |
| NO-GO retained a subjective practical-meaningfulness clause | Removed it; practical relevance is fully represented by the sealed `delta_min` superiority margin. |
| Action agreement called a micro formula macro | Corrected the aggregate terminology to `micro`. |
| Utility arithmetic and rounding points were unspecified | Added the authoritative `utility_e12` scoring DAG, one final division per term, round-half-even, raw-integer inputs, and `scoring_spec_sha256`. |
| Phase A omitted bootstrap CI and prospective power computation | Added provider-free paired percentile bootstrap and 1,000-trial power simulation plus `analysis_spec_sha256`. |
| Utility mixed return units with currency transaction cost | Defined cost as total cents divided by pre-trade equity and fixed `lambda_ppm` units. |
| Quantity lattice rules were not explicit or guaranteed visible | Defined share units, exact lot multiples, a two-lot cap, and mandatory prompt disclosure. |
| Equal-risk nearest-feasible distance was undefined | Fixed deterministic inverse-volatility targets, asset-weight `L1` distance, and cost-turnover-lexicographic tie-breaking. |
| Power case generation was unspecified | Defined 200-case sampling with replacement from the shifted 40-case development empirical distribution. |
| Percentile indices and integer means were ambiguous | Fixed one-based ranks 250 and 9,750, zero-based indices 249 and 9,749, and round-half-even integer means. |
| Exact enumeration retained a nonzero-tolerance placeholder | Fixed `oracle_optimality_tolerance_e12` to `0` in the method and seal record. |
