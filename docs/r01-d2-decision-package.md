# R01 D2 Decision Package v1

> **D2 APPROVED — B3 EXECUTION REMAINS BLOCKED PENDING PREFLIGHT HASH REVIEW**

## Status

- Decision gate: `D2`
- State: `D2_APPROVED_B3_PREFLIGHT_IMPLEMENTED_REVIEW_PENDING`
- Approval date: `2026-07-16` (Asia/Seoul)
- Implementation parent commit: `6ffc1ce`
- Provider calls made: `0`
- Development attempts spent: `0`
- Evaluation fixtures created: `0`

The user approved this package without amendment. The approval resolves D2 but
does not bypass the zero-cost account proof or authorize a provider process
before the live B3 command, anchor manifest, and token ledger pass review.

## Evidence anchors

- Provider-free freeze SHA-256:
  `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`.
- Research contract SHA-256:
  `f1e46e11397ab1dd41cc1bda3c2f2c20720201733bb2d2e6a192d6cf241c69f3`.
- User approval record: `docs/r01-d2-user-approval.md`, SHA-256
  `95e55764963cc86e18e6e66348956bcde84082e3f0da28faf1c60145eb4e150c`.
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
- Provider-free overlay test result after B3 failure-audit hardening: `121 passed`.
- Zero-cost account attestation: `docs/r01-b3-zero-cost-account-attestation.md`,
  SHA-256 `94ca690340273e02da7de19e0c1ea5efc8793547f2a87822dc40eb5b630b9746`.

## Approved D2 resolution

| Field | Recommendation | State |
| --- | --- | --- |
| Exact model | `gpt-5.6-sol` | Approved; spelling is present in the pinned local catalog, while entitlement remains a first-call preflight check |
| Reasoning effort | `high` | Approved |
| Service tier | provider default; do not request `priority` or `fast` | Approved |
| Temperature / top-p | `provider_managed_not_exposed` | Record as limitation |
| Model fallback | prohibited | Frozen |
| Transport model echo | absence accepted as a limitation; any mismatch is `STOP_PHASE` | Approved |
| Live process timeout | `900000` ms | Approved |
| Per-attempt token reserve | `32000` total tokens | Approved |
| Development token cap | `6400000` total tokens | Approved |
| Development attempt cap | `200` attempts, existing block allocation unchanged | Frozen |
| Consecutive `RETRY_TRANSPORT` cap | `2`; the second failure becomes `STOP_PHASE` before attempt 3 | Frozen |
| Initial model-availability failure | attempt-1 `nonzero_exit_without_complete_response` is `STOP_PHASE` | Frozen |
| Incremental USD cap | `0`; no API key, metered overage, purchased credits, or automatic billing fallback | Approved policy; account-state proof required before first call |
| `delta_min_e12` | `50000000000` | Approved |
| `target_headroom_e12` | `50000000000` | Approved |
| `delta_target_e12` | `100000000000` | Approved |
| Two-versus-five replicate variance correction | none; report both known bias mechanisms | Approved |
| High-cost stratum | accept unchanged with `6/7` zero oracle-hold gaps and carry the power cost | Approved |

The margin recommendation treats `delta_min` as 5% of one normalized
oracle-hold scale unit and targets a 10% effect. These values are independent of
all provider output. They must not be reduced after B3 to improve power or a
verdict.

The `32000` reserve is an accounting ceiling, not a promise that every response
must emit that many tokens. Even so, the proposed live timeout is raised from
`300000` to `900000` ms so a high-reasoning request does not enter transport
retry merely because the original ceiling implied roughly `107` reserved
tokens/second. At the revised ceiling the same conservative ratio is about
`36` tokens/second. Every retry consumes both the attempt and token caps; no
replacement fixture or replicate is created if either cap stops the run.

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
active tools under the pinned package-to-tag attribution. The attribution is a
named limitation: the npm package manifest links version `0.144.1` to tag
`rust-v0.144.1`, but no reproducible build cryptographically proves that the
prebuilt binary was built from commit
`44918ea10c0f99151c6710411b4322c2f5c96bea`. Any package, binary, catalog,
definition, or source-identity change invalidates this conclusion and stops the
phase.

All other `88` catalog entries remain disabled. In particular,
`enable_request_compression`, `remote_compaction_v2`, and `fast_mode` remain
false. Shell, browser, web search, MCP, plugin, app, external-context,
workspace-dependency, and personality surfaces remain disabled.

## Provider-free B3 safety gates now covered

The provider-free runner now consumes every complete response disposition and
every bounded transport retry:

- `STOP_PHASE` never reaches parsing or scoring;
- an impossible complete-response `RETRY_TRANSPORT` is converted to a
  fail-closed harness stop;
- `FAIL_CLOSED_SCORE` becomes the canonical hold exactly once;
- parse/schema/portfolio failures receive an explicit `FAIL_CLOSED_SCORE`
  record and the same one-hold treatment;
- replay reconstructs the provider response metadata, reconsumes the
  disposition, verifies final-agent text independently from JSONL stdout, and
  verifies the persisted disposition artifact byte-for-byte;
- attempt-1 nonzero-without-complete-response stops immediately;
- other `RETRY_TRANSPORT` failures advance at most once to attempt 2, bind the
  first failure record into a later success, and stop on the second consecutive
  failure before attempt 3;
- the development `200`-attempt cap is checked immediately before every call;
- stopped attempts may leave immutable raw/failure evidence outside a completed
  run result, but those blobs never enter scoring or fallback metrics.

The nested run-result contract was version-bumped to
`r01-development-run-result-v4`; each acquisition binds an
`r01-complete-response-disposition-v1` artifact and any successful retry binds
its preceding `r01-acquisition-failure-v2` record, token reservation, and
failed-attempt transport graph for replay.

## Post-approval execution gate

D2 is approved. Before the first B3 provider process starts:

- preserve the recorded personal-Pro balance of `KRW 0`, disabled Auto top-up,
  and prohibition on purchased/shared credits so the approved incremental USD
  cap remains zero; this is attested in the zero-cost record above;
- implement and hash the live B3 command spec and deterministic six-case anchor
  manifest;
- wire the `32000` per-attempt reservation, actual token-usage ledger, `6400000`
  development cap, and `200`-attempt cap into the live path;
- rerun provider-free tests and review the exact implementation and identities;
  the first B3 preflight hash must still be generated and externally frozen.

The zero-cost attestation, live command construction, deterministic anchor
selection, token ledger, bounded failure audit, and provider-free regression
suite are implemented. The remaining gate is one-shot generation and external
review of the exact B3 preflight hash against the committed implementation.
Until that review passes, no Codex provider process may start and provider
calls, attempts, and consumed tokens remain zero. B3 execution, B4, and later
phases remain blocked.

## Requested cross-review

Review should answer:

1. Does the exact-tag source proof justify treating the four residual entries
   as no-op allowlist members for `codex-cli 0.144.1`?
2. Can any `STOP_PHASE` or harness exception still enter hold/fallback metrics?
3. Can `FAIL_CLOSED_SCORE` be parsed, scored, or replayed more than once?
4. Is the run-result schema bump complete across acquisition and replay?
5. Are the proposed model, timeout, token, margin, variance, and high-cost
   decisions independent of provider outcomes and sufficiently conservative?
6. Do the first-nonzero stop rule, two-failure retry bound, global attempt cap,
   and retry-history replay binding close the pre-D2 budget-leak finding?
