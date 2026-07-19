# R02 overlay v2 scope annotation for D3 and D4

Status: **DRAFT — PROVIDER-FREE — REVIEW REQUIRED**

## Required interpretation

R02 D3 and D4 support three statements that must remain joined:

1. They are not evidence that LLMs in general cannot add portfolio value.
2. The implemented D2b selector could not identify utility-aware LLM value
   because its payload omitted utility-relevant public state.
3. That implemented selector is nevertheless operationally redundant:
   deterministic parsimony reproduced `55/55` D3 selections and `69/69` D4
   selections, so provider-free replacement of that implementation is supported.

The D4 labels remain unchanged:

- `REPLICATION_SUPPORTED_FRAGILE` for the baseline-relative primary endpoint;
- `PARSIMONY_POLICY_SUPPORTED` for deterministic parsimony;
- `NOT_IDENTIFIED_REDUNDANT_SELECTOR` for incremental LLM value.

The fragile primary result and selector redundancy are separate findings.
Removing the provider-backed selector does not make the baseline-relative effect
robust.

## Why incremental value was not identifiable

The D2b selector saw only two to four opaque candidates containing anonymous
asset actions and quantities. It saw no prices, holdings, public signals,
confidence measures, costs, covariance structure, limits, or other fixture
context. Its prompt required comparison only among opaque candidates, and its
reason vocabulary was almost entirely a structured parsimony vocabulary.

The observed `69/69` D4 agreement is therefore evidence of redundancy for the
implemented selector, not a general test of context-aware LLM reasoning.

## Hidden-oracle boundary

`v2/research/overlay/scoring.py::score_episode` reads
`episode.hidden.expected_returns_bps`. The hidden expected returns and hidden
regime are evaluation-only information. They are forbidden from both the
deterministic public-information comparator and the LLM payload.

Overlay v2 may use the hidden oracle only after a selection has been made, for
provider-free design-split evaluation, headroom validation, confirmatory scoring,
regret, and confidence calibration. Oracle-derived outcomes may not be used to
select individual confirmatory fixtures.

## Consequence for overlay v2

Overlay v2 is a new intervention with a new payload, prompt, output schema,
parser, comparator, power analysis, and authorization chain. It must compare an
LLM against the strongest preregistered deterministic policy that receives the
same canonical public-information payload bytes.

No provider call is scientifically justified until the selected deterministic
public-information comparator leaves adequate positive oracle headroom on an
untouched provider-free validation split and the separate blinded-discordance
pilot contract has been reviewed and approved.
