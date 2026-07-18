# R02 D4-S3 provider-free statistical freeze

Date: 2026-07-18

Status: **PROVIDER-FREE FREEZE — PENDING INDEPENDENT REVIEW — LIVE NO-GO**

Provider calls, Codex exec, micro-pilot, LIVE, provider budget, and LIVE
authorization artifacts: **0**

## 1. Frozen input

This freeze consumes only the independently accepted S2A frame:

- base commit: `c4fb28c66404fc783cfbc33d125012e1dff2c76e`;
- frame ID: `r02-d4-s2a-frame-0716a1b9c13a`;
- manifest SHA-256: `368e0150...4ba1`;
- seal SHA-256: `40aec915...5838`;
- tree SHA-256: `65c0acc6...ea29`;
- allocation: 150 representative, 50 challenge;
- eligible opportunities: 19 representative, 50 challenge, 69 total.

The accepted `M_min=57` information floor is satisfied by the sealed frame.
This is a pre-execution information qualification, not an effect result.

The S2A intent's previously under-validated `generation_attempt_cap` is now an
explicit S3 gate. The intent value, frame manifest count, and frame seal count
must each equal one. Tampering is covered by a focused negative test.

## 2. Scientific hierarchy

The four endpoints remain separate and ordered:

1. **Primary replication:** LLM-selected system utility minus the unchanged
   deterministic baseline over the full 200-fixture ITT frame.
2. **Deterministic policy:** parsimony-selected system utility minus the same
   baseline, also over the full frame.
3. **Incremental LLM:** LLM-selected utility minus parsimony-selected utility,
   with zero contribution on agreement and every primary ITT zero path.
4. **Agreement:** exact canonical candidate-ID agreement among the 69
   selector-eligible fixtures, with a Wilson 95% interval.

The primary label is evaluated first. Parsimony, incremental, and agreement
results cannot rescue or reverse it. An ambiguity-engineered candidate study
changes the intervention and remains outside D4.

Exact replication may again produce 100% LLM-parsimony agreement. In that
case, `NOT_IDENTIFIED_REDUNDANT_SELECTOR` is the expected valid incremental
label, not a failed primary replication and not evidence of no effect.

## 3. ITT arithmetic

All effect estimands use integer `e12` utilities and the frozen expression:

```text
theta = round_half_even(3/4 * mean(D_representative)
                        + 1/4 * mean(D_challenge))
```

For the primary estimand, trigger-false, no-call, invalid-response, and
baseline-fallback paths contribute exactly zero. The incremental estimand also
contributes zero when LLM and parsimony select the same canonical candidate.

The primary and deterministic-policy thresholds remain
`delta_min=50,000,000 e12`; support requires a lower bound strictly greater
than the threshold.

## 4. Bootstrap

The primary, parsimony, and incremental raw intervals use:

- fixture resampling with replacement within each stratum;
- retained 150/50 resample sizes and 3:1 target weighting;
- 10,000 resamples;
- NumPy 1.26.4 `PCG64`;
- sorted zero-based positions 249 and 9,749 for the two-sided 95% nearest-rank
  percentile interval;
- round-half-even integer arithmetic for every bootstrap replicate.

The outcome-independent bootstrap seed is the SHA-256 of a canonical preimage
containing only accepted design, frame identity, sample sizes, weights,
resample count, rank positions, `delta_min`, and `M_min`:

`ab143af338e991209a9c3fb387623d126ab8399aba268285758234eb15f71804`

Robustness variants derive separate canonical SHA-256 seeds from that base
seed, an analysis ID, and only the frozen fixture ordinal or winsor fraction.
No observed delta enters a seed.

## 5. Primary label precedence

Apply in order:

1. `INVALID_RUN` for identity, integrity, settlement, accounting, attempt,
   replay, or authorization failure.
2. `INCONCLUSIVE_LOW_INFORMATION` when `M < 57`.
3. `REPLICATION_NOT_SUPPORTED` when the valid unmodified lower bound is not
   strictly greater than `50,000,000 e12`.
4. Otherwise, `REPLICATION_SUPPORTED_ROBUST` only when every robustness gate
   passes; else `REPLICATION_SUPPORTED_FRAGILE`.

`ROBUST` requires all of:

- unmodified lower-bound margin at least `5,000,000 e12`;
- maximum absolute raw-theta shift after one eligible delta is zeroed no more
  than 100,000 ppm of the absolute unmodified theta;
- every one of 69 fixed-frame eligible-fixture zero-nullification lower bounds
  strictly above `delta_min`;
- every one of 69 literal eligible-fixture leave-one-out lower bounds strictly
  above `delta_min`;
- both 5% and 10% within-full-stratum winsorized lower bounds strictly above
  `delta_min`.

Winsorization uses NumPy linear empirical quantiles, clipping within each full
stratum, and `numpy.rint` ties-to-even conversion to `int64`. These are
diagnostic qualifiers, never replacements for the unmodified primary test.

The rules anticipate D3's narrow 1,470,259-e12 margin, influential
`development-0189`, incomplete zero-nullification/leave-one-out stability, 5%
pass, and 10% failure without modifying or reclassifying D3's sealed
`SUPPORTED` verdict.

## 6. Secondary labels

Parsimony precedence:

- invalid integrity: `INVALID_RUN`;
- `M < 57`: `PARSIMONY_POLICY_INCONCLUSIVE_LOW_INFORMATION`;
- lower bound strictly above `delta_min`: `PARSIMONY_POLICY_SUPPORTED`;
- otherwise: `PARSIMONY_POLICY_NOT_SUPPORTED`.

Incremental precedence:

- invalid integrity: `INVALID_RUN`;
- total discordance below 20, representative discordance below 5, or challenge
  discordance below 5: `NOT_IDENTIFIED_REDUNDANT_SELECTOR`;
- otherwise lower bound above zero: `INCREMENTAL_LLM_SUPPORTED`;
- otherwise upper bound below zero: `INCREMENTAL_LLM_HARM`;
- otherwise: `INCREMENTAL_LLM_INCONCLUSIVE`.

Agreement uses Wilson's score interval with
`z=1.959963984540054`, Decimal precision 50, and half-even ppm rounding.

## 7. Prospective design context

No new power calculation is performed in S3. The accepted provider-free grid
remains frozen:

- target power at least 85%; Wilson lower at least 80%;
- 8,000-bps low-SNR condition;
- n=160 raw bounded and gamma scenarios fail;
- n=200 raw bounded: 87.1% / 84.8796% lower;
- n=200 raw gamma: 89.0% / 86.9095% lower;
- n=240 passes but is not the smallest passing size;
- n=200 `M_min=57` opportunity probability: 94.3424%.

The sealed frame's `M=69` clears the information floor. It does not authorize
or numerically determine a provider budget in this phase.

## 8. Exact test manifest

`docs/r02-d4-s3-focused-tests.json` freezes the complete ordered pytest file
list, exact argv, each test-source SHA-256, and exactly 77 collected tests. The
S3 verifier rejects both list/count drift and source drift. Dedicated negative
tests prove rejection of a changed generation-attempt cap and test count.

## 9. Remaining gates

After independent acceptance, the next phase may draft a numeric provider
budget using exactly 69 sealed eligible opportunities. That budget, any
provider call, and LIVE authorization each require separate explicit user
approval. S3 creates none of them.
