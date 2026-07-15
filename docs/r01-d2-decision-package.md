# R01 D2 Decision Package v1

> **PENDING USER APPROVAL — PROVIDER CALLS REMAIN FORBIDDEN**

## Status

- Decision gate: `D2`
- State: `READY_FOR_CROSS_REVIEW_PENDING_USER_APPROVAL`
- Implementation parent commit: `1b0ef0e`
- Provider calls made: `0`
- Development attempts spent: `0`
- Evaluation fixtures created: `0`

This package records a provider-free recommendation. It does not approve D2,
build an acquisition command, or authorize the B3 micro-pilot.

## Evidence anchors

- Provider-free freeze SHA-256:
  `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`.
- Research contract SHA-256:
  `3a2f2dab0acd4c6a274f660f3dd69b3dea0f60d1de263e1034e653a7e03028bc`.
- Provider-free regime-gap summary SHA-256:
  `0e6e8945f93779a77ffc7687d63062c010efd3aee3d6c8062551e54108fbf886`.
- B2 feature snapshot SHA-256:
  `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad`.
- Exact-tag Codex source proof:
  `docs/r01-b2-codex-source-feature-proof.json`, SHA-256
  `1de5d131356deb6dec8186eb07795e47717d4960937b9142689a5e9cc3554f91`.
- Codex package/tag/commit: `0.144.1` / `rust-v0.144.1` /
  `44918ea10c0f99151c6710411b4322c2f5c96bea`.
- Source feature registry SHA-256:
  `fa22fba77b192cac755ab9b03c78e1d2b0a101ca9cdaa4ce928cf61722f3872a`.
- Source feature tests SHA-256:
  `53cbad126a94c757dd26c9e7788a402697bdde04a4d9a6077202e0fdbf6a788b`.
- Bundled model catalog SHA-256:
  `678a11fa060b6a30573992fd15b25911f4d2f939ce43c016dffb5d08e22a4b08`.
- Provider-free overlay test result: `102 passed`.

## Recommended D2 resolution

| Field | Recommendation | State |
| --- | --- | --- |
| Exact model | `gpt-5.6-sol` | Pending user approval and first-call availability check |
| Reasoning effort | `high` | Pending user approval |
| Service tier | provider default; do not request `priority` or `fast` | Pending user approval |
| Temperature / top-p | `provider_managed_not_exposed` | Record as limitation |
| Model fallback | prohibited | Frozen |
| Transport model echo | absence accepted as a limitation; any mismatch is `STOP_PHASE` | Pending user approval |
| Live process timeout | `300000` ms | Pending user approval |
| Per-attempt token reserve | `32000` total tokens | Pending user approval |
| Development token cap | `6400000` total tokens | Pending user approval |
| Development attempt cap | `200` attempts, existing block allocation unchanged | Frozen |
| Incremental USD cap | `0`; no API key, metered overage, purchased credits, or automatic billing fallback | Pending entitlement confirmation |
| `delta_min_e12` | `50000000000` | Pending user approval |
| `target_headroom_e12` | `50000000000` | Pending user approval |
| `delta_target_e12` | `100000000000` | Derived from the two approved values above |
| Two-versus-five replicate variance correction | none; report both known bias mechanisms | Pending user approval |
| High-cost stratum | accept unchanged with `6/7` zero oracle-hold gaps and carry the power cost | Pending user approval |

The margin recommendation treats `delta_min` as 5% of one normalized
oracle-hold scale unit and targets a 10% effect. These values are independent of
all provider output. They must not be reduced after B3 to improve power or a
verdict.

## Minimal non-tool allowlist

Recommend approving exactly these four residual entries:

- `resize_all_images`
- `terminal_resize_reflow`
- `tool_search_always_defer_mcp_tools`
- `tui_app_server`

At exact Codex tag `rust-v0.144.1`, all four are `Removed`, default to `true`,
and their config keys are explicitly ignored by `Features::apply_map`. A scan of
the exact tagged Rust source found no behavior consumer outside the feature
registry, removed-key config guards, and feature tests. They are therefore
source-established no-op registry residues for this pinned binary identity, not
active tools. Any package, binary, catalog, definition, or source-identity
change invalidates this conclusion and stops the phase.

All other `88` catalog entries remain disabled. In particular,
`enable_request_compression`, `remote_compaction_v2`, and `fast_mode` remain
false. Shell, browser, web search, MCP, plugin, app, external-context,
workspace-dependency, and personality surfaces remain disabled.

## B3 implementation gate now covered

The provider-free runner now consumes every complete response disposition:

- `STOP_PHASE` never reaches parsing or scoring;
- an impossible complete-response `RETRY_TRANSPORT` is converted to a
  fail-closed harness stop;
- `FAIL_CLOSED_SCORE` becomes the canonical hold exactly once;
- parse/schema/portfolio failures receive an explicit `FAIL_CLOSED_SCORE`
  record and the same one-hold treatment;
- replay reconstructs the provider response metadata, reconsumes the
  disposition, and verifies the persisted disposition artifact byte-for-byte.

The nested run-result contract was version-bumped to
`r01-development-run-result-v2`, and each acquisition now binds an
`r01-complete-response-disposition-v1` artifact.

## Remaining authorization gate

D2 is not approved until the user explicitly accepts or amends every pending
row above. Until then:

- no acquisition command spec may be emitted;
- no Codex provider process may start;
- no attempt or token budget may be consumed;
- B3, B4, and later phases remain blocked.

## Requested cross-review

Review should answer:

1. Does the exact-tag source proof justify treating the four residual entries
   as no-op allowlist members for `codex-cli 0.144.1`?
2. Can any `STOP_PHASE` or harness exception still enter hold/fallback metrics?
3. Can `FAIL_CLOSED_SCORE` be parsed, scored, or replayed more than once?
4. Is the run-result schema bump complete across acquisition and replay?
5. Are the proposed model, timeout, token, margin, variance, and high-cost
   decisions independent of provider outcomes and sufficiently conservative?
