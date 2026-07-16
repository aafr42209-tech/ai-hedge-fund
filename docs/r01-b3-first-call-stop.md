# R01 B3 First-Call STOP Record

Status: `STOPPED_UNSCORED_TRANSPORT_SCHEMA_DRIFT`

Date: `2026-07-16` (Asia/Seoul)

Provider calls made by the stopped experiment: `1`

Remaining planned acquisitions executed: `0`

## Frozen launch identity

- Experiment: `r01-b3-prompt-v1-20260716`
- Implementation commit:
  `bcc3dbc2dc0d4c223e675ad1d6ecb255f54d625a`
- Readiness report commit:
  `a4b52f51dc7abf616fbdd86fe329201445b2c653`
- Preflight SHA-256:
  `df53917b4943e41999c66506b66c09255cd05c6d3db69a870aed9f53b0482481`
- Acquisition: `development-0005`, development replicate `0`, attempt `1`

All pre-run gates matched immediately before launch: clean pinned commit,
preflight and 53 recursive references, executable, account attestation, empty
sandbox, feature gate, and `Logged in using ChatGPT`.

## Stop outcome

- Failure code/disposition: `jsonl_schema_drift` / `STOP_PHASE`
- Process: exit `0`, not timed out, duration `38532 ms`, empty stderr
- Complete transport observed: one thread, one turn start, one final agent
  message, one turn completion, and all required usage fields
- Raw usage observation: input `12321`, cached input `0`, output `1330`,
  reasoning output `1034`; accounting total `13651`
- Conservative failed-attempt budget charge: `32000`
- Provider response artifacts: `0`
- Scores: `0`
- Run results: `0`
- Retry attempts: `0`

The parser stopped on the first of three `item.completed/error` items. All three
messages were CLI deprecated-feature diagnostics emitted before `turn.started`:

1. `use_legacy_landlock` deprecation SHA-256:
   `e052476a559bbf088d2b71299fe87e7528156c6023246c5c1d2004dfc49b7503`
2. `web_search_cached` deprecation SHA-256:
   `347c0457b18c0751dc40216069532bbe56642de70196c76633db9faa4f46dbb7`
3. `web_search_request` deprecation SHA-256:
   `462cbd24fc7212da04c67ee5dc8406a250a157e2e8fce605e7d6d3e7e1002c60`

They were followed by an otherwise complete agent response. The response text
is retained only as stopped raw evidence and is not parsed as a portfolio
decision, scored, reported, or adopted by a later experiment.

## Append-only evidence

- Acquisition failure SHA-256:
  `dfa0e2136e76ae1d50739cedba06b0f70ce0e6513fc594e0ee4eec0cb6eeb6a3`
- Token reservation SHA-256:
  `5b4a082095c7e978834b6aabeda6ca0c1722c40649090cb48e8994fbfb83b5e3`
- Command spec SHA-256:
  `1e63bf047d182edf2d03333eb9b775b3129ef4827b2cdca8bc41f3278f4b3b33`
- Stdout JSONL SHA-256:
  `b42af8746b7b3b1bf72262a18d832928e3d5dbe90d1c3a7ca57c1197963a3e6c`
- Stderr SHA-256:
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Process-status SHA-256:
  `bdb5c6540cfdb326bb16cdd48e6f88b116b0e876ea642db7fcea7252ea20e0a8`

The `r01-acquisition-failure-v2` record binds the token reservation and complete
failed-attempt transport graph. The sandbox remained empty after the stop.

## Provider-free remediation rule

The transport contract is narrowed, not broadly relaxed:

- parser schema: `r01-codex-jsonl-parser-v3`;
- transport-shape schema: `r01-codex-transport-shape-spec-v2`;
- provider-response schema: `r01-provider-response-v4`;
- valid diagnostic set: empty, or the exact ordered three messages above,
  emitted as `item.completed/error` before `turn.started` with fields exactly
  `id`, `message`, and `type`;
- every partial, reordered, duplicate, late, unknown, or shape-drifted error
  item remains `STOP_PHASE`.

The preserved raw capture parses under this new rule without tool-use or
process-status violations. This provider-free compatibility check does not
change the stopped record or authorize its use in metrics.

Before another provider call, create a new experiment identity and contract-
bound manifest, generate a new zero-call preflight, independently review its
code commit and preflight hash, and retain the original attempt in the global
development budget.

Provider-free remediation validation: `125 passed`; Python compile, Black,
isort, and `git diff --check` pass. Remediated research contract SHA-256:
`f0c29d0bb4c6e55673206f3d1c3415f82318cdc0fcb8208df568df00e528a5a1`.
