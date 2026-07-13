# Research Assessment and Promotion Contract

**Status:** Historical investment-performance claims are **NO-GO** on the current `src/` backtester. Controlled LLM decision research is **GO**. Real-market evaluation requires a new, fail-closed `v2` research contract.

**Assessment date:** 2026-07-13

**Repository baseline inspected:** `main` at `58c4589` before this assessment commit

## Executive decision

The repository has independent research value, but not as evidence that a named investor persona or the current multi-agent system earns excess returns.

The strongest repository-specific question is:

> Given identical quantitative signals, portfolio state, risk limits, and costs, does an LLM portfolio overlay make better decisions than a deterministic combiner?

The recommended sequence is:

1. Controlled synthetic/fixture-only LLM policy evaluation.
2. Persona-label and prompt-invariance experiments.
3. Data-provider revision and provenance measurement.
4. `v2` point-in-time, execution, cost, and validation implementation.
5. Forward paper-trading with a frozen model and a single preregistered endpoint.

Historical persona return comparisons using `src/` remain out of scope.

## Verified current behavior

### Same-session look-ahead-shaped execution

`src/backtesting/engine.py` obtains the current session's close, supplies `end_date=current_date` to the agents, and executes the returned order at that same close:

- current close selection: `src/backtesting/engine.py:119-123`
- agent information boundary: `src/backtesting/engine.py:132-140`
- same-price execution: `src/backtesting/engine.py:145-150`

This cannot support causal historical performance claims. The research engine must form a decision at an explicit timestamp and fill no earlier than the next eligible exchange session.

### The LLM selects final orders

`src/agents/portfolio_manager.py` creates deterministic per-ticker allowed-action hints, sends them to an LLM, and merges the structured response into the final decision map:

- allowed-action construction: `src/agents/portfolio_manager.py:96-157`
- LLM decision path: `src/agents/portfolio_manager.py:177-257`
- response merge: `src/agents/portfolio_manager.py:259-262`

The structured response constrains the action vocabulary, but it does not enforce that the chosen action was allowed for that ticker or that quantity is within the advertised maximum.

The allowed-action calculation is also per-ticker rather than portfolio-joint. Each ticker can be shown the same total cash or margin capacity. Final fills are then applied sequentially in ticker order, so equivalent decision sets can produce different portfolios after ticker permutation.

### Execution has no market frictions

`src/backtesting/trader.py` routes buy, sell, short, and cover actions directly into portfolio accounting. It has no commission, bid-ask spread, slippage, delay, borrow fee, market-impact, liquidity, or capacity contract.

Portfolio methods clamp some infeasible orders to available cash or holdings, but this is not equivalent to portfolio-level constraint validation. It also hides the distinction between the raw LLM violation and the executable order unless both are recorded separately.

### Price and reference-data contracts are insufficient

The current price model contains OHLCV but no adjusted-close or authoritative corporate-action ledger. There is no historical-universe membership, delisting-return, provider-revision, `available_at`, or immutable raw-snapshot identity contract.

The current `src/tools/api.py` also contains Yahoo price and StockAnalysis financial fallback paths. These sources are not bound to provider identity and revision metadata. The StockAnalysis fallback functions do not receive the historical `end_date`, so they must not be treated as point-in-time fundamentals.

### Passing tests do not validate research validity

The focused backtesting suite passed on 2026-07-13:

```text
37 passed, 2 warnings in 5.19s
```

The execution tests cover routing, zero or negative quantity guards, and unknown actions. They do not cover transaction costs, T+1 execution, post-LLM allowed-action enforcement, portfolio-joint feasibility, or ticker-order invariance.

## `v2` readiness assessment

`v2` is a useful scaffold, not a research engine.

Implemented foundations:

- an FD API client and provider protocol;
- Pydantic data models;
- a quantitative signal result schema;
- a `BaseSignal` interface and numerical helpers.

Unimplemented or docstring-level areas:

- backtesting;
- optimizer;
- execution simulation;
- risk management;
- CPCV/PBO validation;
- event studies and concrete features/signals.

The current data protocol explicitly returns empty lists or `None` on failure. The client therefore cannot distinguish a true no-record result from network failure, rate-limit exhaustion, authorization failure, or malformed provider data. A research pipeline must fail closed with typed completeness and error states.

Temporal fields are also insufficient for the README's point-in-time promise. Prices have a bar date, news has an optional date string, earnings has a report period, and filings have a filing date. There is no authoritative acceptance/publication timestamp, provider revision, retrieval timestamp, or content hash.

## Research programs worth running

### 1. Synthetic LLM overlay incremental-value study — highest priority

Primary hypothesis:

> With identical signals and constraints, the LLM overlay has lower cost-adjusted regret to a hidden oracle than a preregistered deterministic combiner.

The fixture generator should create expected returns, covariance, transaction-cost schedules, current holdings, risk limits, and noisy/conflicting signals. The LLM and all baselines receive the same observable inputs. Oracle state remains hidden.

Primary endpoint:

```text
deterministic baseline regret - LLM overlay regret
```

A positive value favors the LLM.

Secondary endpoints:

- exact action agreement across repeated identical calls;
- order-quantity variance;
- raw constraint-violation rate;
- executable constraint-violation rate after validation;
- ticker, analyst, and JSON-key permutation flip rates;
- sensitivity to irrelevant wording and numeric formatting;
- expected turnover and transaction cost;
- fallback and parse-failure rates;
- confidence calibration where the synthetic outcome is known.

Required comparison policies:

- fixed weighted-score or ranking baseline;
- hold baseline;
- equal-risk baseline;
- LLM overlay.

Development fixtures and evaluation fixtures must be separate. Generator families, seeds, prompt, model, call budget, effect-size threshold, and endpoint must be frozen before the sealed evaluation.

### 2. Persona distinctness and reasoning-faithfulness study

The repository contains both deterministic analyst modules and LLM-mediated named-investor agents. Their value can be tested without return claims through a two-factor design:

1. hold the calculation recipe fixed and change only the persona label;
2. hold the persona prompt fixed and change the supplied calculation recipe.

This separates methodology from branding. Useful endpoints are action divergence, monotonic response to a controlled fact change, persona-label sensitivity, explanation/action consistency, and cross-agent redundancy.

### 3. Model-memory and drift audit

Ticker/date masking is a useful negative control, not proof that historical performance is uncontaminated. Price paths, financial values, and news text can re-identify the company or event.

Useful paired experiments include:

- named versus anonymized assets;
- real versus synthetic tickers;
- persona-label swaps;
- company-name swaps with facts held constant;
- repeated calls across provider model versions and dates.

This study may support claims about memory dependence and model drift. It must not be reported as historical alpha validation.

### 4. Provider revision and completeness study

Repeatedly retrieve identical historical queries, store immutable raw responses, and measure field-level and content-hash changes over time. This establishes whether a provider silently revises prices, fundamentals, filings, news, or estimates.

This is valuable independently of strategy performance and is a prerequisite for reproducible future research.

### 5. Forward paper-trading study — final promotion target

Forward evaluation is the cleanest defense against model-training outcome contamination. The LLM overlay and deterministic baseline must consume the same sealed signals and risk limits, form decisions at the same timestamp, and execute through the same next-session cost model.

The primary endpoint should be a single paired, net-of-cost performance difference. Hold/equal-risk results remain secondary safety comparisons.

## Mandatory promotion gates for real-market evaluation

Real-data evaluation is blocked until all gates pass:

1. Point-in-time records with event time, `available_at`, publication/acceptance timestamp, retrieval time, and provider revision.
2. Immutable raw response storage with canonical query identity and content hash.
3. Typed fail-closed completeness states; provider errors must never masquerade as empty data.
4. Total-return price authority with dividends, splits, mergers, symbol changes, and other corporate actions.
5. Historical universe membership, IPO eligibility, delistings, and delisting returns.
6. Exchange-calendar-aware decision time and next-eligible-session fill contract.
7. Commission, spread, slippage, turnover, borrow, liquidity, capacity, and market-impact costs.
8. Portfolio-joint constraint validation before execution.
9. Deterministic cache/run identity binding code, configuration, data, model, prompt, and raw LLM response.
10. Exact model/version and sampling metadata; model aliases alone are insufficient.
11. Explicit training-leakage design. Forward evaluation is primary; masking is diagnostic only.
12. Implemented CPCV/PBO where historical model selection is performed, plus one frozen primary endpoint.
13. Preregistered LLM/API call budget and stop rules.

## Artifact contract

Every LLM decision must preserve four distinct artifacts:

1. raw provider response;
2. parsed raw decision;
3. validator report and sanitized executable order;
4. execution result and cost ledger.

Each artifact must bind to the fixture/data hash, prompt hash, exact model identity, code commit, configuration hash, request timestamp, and provider request metadata. Silent clipping or fallback without an explicit artifact invalidates the run.

## Reuse judgment

Potentially reusable:

- deterministic technical, fundamental, valuation, sentiment, growth, and risk recipes as candidate baselines;
- portfolio accounting tests as a mechanical starting point;
- `v2` schemas and provider interface as scaffolding;
- the current portfolio-manager boundary as the treatment interface for fixture-only research.

Not reusable as evidence:

- current `src/` backtest returns;
- persona profitability rankings;
- frictionless execution results;
- current provider fallbacks as historical truth;
- README promises that are not implemented and verified.

## Final decision

- Current `src/` persona performance research: **NO-GO**.
- Controlled synthetic LLM policy research: **GO**.
- Persona distinctness and model-memory diagnostics: **GO**, without return claims.
- Historical real-data overlay performance: **NO-GO** until every promotion gate passes.
- Forward paper-trading after a frozen `v2` contract: **GO candidate**.

The first sealed study should stop the program if the LLM does not improve cost-adjusted regret, constraint handling, or decision invariance over the deterministic baseline. A negative result is a valid research outcome and should not be relabeled through prompt or endpoint changes after evaluation.
