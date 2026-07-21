# R03 N1 V2 normative retention reseal — independent review handoff

## 1. Disposition requested

Implemented under `R03_N1_V2_NORMATIVE_RESEAL_CODE_AUTHORIZED`.

Requested disposition:

`INDEPENDENT_V2_NORMATIVE_RESEAL_REVIEW_PENDING`

The lineage status is `V2_NORMATIVE_RESEALED_PENDING_INDEPENDENT_REVIEW`.
This handoff does not claim independent acceptance. No raw traversal, result
rewrite, frame or fixture materialization, fitting, G1-G3, OOS access,
inference, model download, provider/network use, dependency change, commit, or
push is authorized or reported in the current code-only scope.

## 2. Normative replacement

The new normative contract value is:

| Measure | Numerator | Denominator | Display |
|---|---:|---:|---:|
| Full frames | 150,394 | 151,820 | 99.06% |
| Article appearances | 695,948 | 702,489 | 99.07% |
| Text bytes | 1,515,387,041 | 1,585,976,846 | 95.55% |

Retention canonical SHA-256:
`8b659ac03fb4481ebbbcdc3579e484f5630d8e490d6981c0b4a7a2c3c02c1019`.

This is `REPLACE_NOT_RECONCILE`. The historical 90.53% files remain
byte-for-byte preserved, but that value is classified
`HISTORICAL_NON_NORMATIVE_UNREPRODUCIBLE` and is forbidden as a future decision
input. Nothing was deleted or rewritten.

## 3. Why recovery was closed

The independently reviewed investigation established that the historical
1,435,742,878 value came from `read-only-data-check.json`, which declares
`COMPLETED_FAIL_CLOSED_N1_TEXT_RETENTION_MISMATCH` and records the HIGH finding
`R03_PUBLIC_RETENTION_DENOMINATOR_CONFLATION`.

The value has no tracked generation commit. The contemporaneous public
aggregator only summed driver-produced rows; the untracked V1 selection driver
was overwritten and no V1 bytecode remains. Consequently, another search for a
rule that happens to produce 655,960 bytes would be post-hoc fitting, not
provenance recovery. The lineage records the recovery as
`CLOSED_UNRECOVERABLE` and forbids such fitting.

## 4. Exact seal anchors

| Artifact | Canonical SHA-256 | Filesystem SHA-256 |
|---|---|---|
| V2 reseal lineage | `8f3b3f0c25b3dd8b7c12af4232f6fb22b19db62e71b752d1555b9c114457a719` | `e7730dcc3e4b260f89ff3bbf1591fbe8cac15bc6386ac6fbd8eeb00dc860af24` |
| Execution-surface attestation | `44002b7a56e3c2432b4b4abf62088241d83c397d96c1a7e33828f03eeb3659f6` | `1ae3e2af3f59feb08940615f6ac22a19542077b29ad95496b625d7f9e902dbe1` |
| V2 reseal evidence | `a170b0bdabf967cef8f606a96bcce3f395bd90ada92a954b76bc0eeb1a7b2d6b` | `3c2b0c5d07859c367692067802824b74ead58cc1a17bba592f08dddb3d6349b0` |
| Zero-call manifest | n/a | `37ea72d5de7996e35919c3a8332093b525df46cfa0b0302d21bf9dc6d7425f14` |
| Targeted result | `797a960ed9a7a4e9b1fe3e2f7cf92957a3afcf47fb87df25456ee946f3fc8045` | review anchor `67214163917e631696edf7b7d564795430794b795ee5d282dbd5277ff34e2aaa` |
| Targeted evidence | `06a059b1d7b869e4c567d109931faec9d491c84ba2c17f98a874f8f0237d4109` | nested |
| Ledger multiset | `43029119e288584e6a516687e52d5cf35625806dd34f15d722c4ef2caf576f75` | nested |
| Independent targeted-result review | n/a | `264ae4861d2ffb55983625cbe9db110bc3ebd5487f6392bf336efb030a4ea44f` |
| Verifier | n/a | `49995cffa95f01146938254436375b9b1b7d9bcfb043ff70e7e411bc8a8b2d9e` |
| Tamper tests | n/a | `ccbb398bfccf628505f25222494b0b09fce03ca038dd0f46a2a452b970dc25e0` |

Canonical hashes are normative contract anchors. Filesystem hashes are file
identity or review-session anchors only. In particular, the targeted result is
CRLF-serialized, so its filesystem hash is explicitly nonnormative.

## 5. Execution-surface closure

The raw targeted result was not modified to add a new block. A separate
self-hashed attestation closes that review observation and pins:

- base execution commit `e9109913a2cf198e63f5fbd116abc91c58fc6ee2`;
- targeted module and runner;
- reconciliation runner and prior V2 driver;
- event-index and calendar-input filesystem identities;
- targeted permit, result, evidence, and ledger canonical identities;
- the independent 44-check result review.

The verifier recomputes every execution-surface filesystem hash and proves that
the raw execution commit is an ancestor of the current Git HEAD before
accepting the attestation. It does not traverse the news raw root.

The initial reviewed verifier compared the raw execution commit directly with
the then-current HEAD. The first seal commit `c38bdc3b3fa93288a5fbb8d93c83ac4c95611445`
correctly moved HEAD and exposed that post-commit state bug. This corrected set
uses ancestry instead of equality and adds a regression test that forces the
non-ancestor case to fail closed. The correction changes only the verifier,
tests, evidence, manifest, and this handoff; lineage, attestation, normative
values, and raw results remain unchanged. A new independent review is required
before a follow-up correction commit or push.

## 6. Byte-accounting closure

The 664 affected-frame ledgers establish:

```text
1,428,361,110 + 87,025,931 = 1,515,387,041
1,428,361,110 +  7,381,768 = 1,435,742,878
87,025,931 - 7,381,768 = 79,644,163
80,300,123 - 79,644,163 = 655,960
```

The V2 value is independently reproduced and fully accounted. The last line
does not validate the legacy value; it isolates the residue for which no
recoverable generating rule exists.

`targeted_result.total_news_positive_frames` is explicitly aliased to
`full_frames_total`. The field name changes no value or counting rule.

## 7. Fail-closed verification

The new verifier layers on top of the historical reconciliation-rerun verifier
and checks:

- all prior amendment, contract, and rerun seals;
- the original fail-closed legacy result and its HIGH observation;
- permit, result, evidence, ledger multiset, and execution-surface pins;
- all 664 ledger partitions, component sums, cap bounds, canonical ordering,
  uniqueness, and derived global totals;
- replacement rather than reconciliation;
- canonical-hash and semantic-alias policies;
- lineage, attestation, evidence, and manifest cross-pins;
- current code-only zero counters and aggregate-only output boundaries.

Synthetic tests re-sign tampered lineage, attestation, evidence, permit/result,
and ledger structures. They cover legacy-value reinstatement, `RECONCILE`
substitution, fake driver recovery, permission to fit 655,960, filesystem hash
promotion, alias drift, execution-surface drift, result-pin drift, nonzero scan
counters, ledger partition/order changes, and artifact-pin mutation.

## 8. Reproduction results

- Historical data-check verifier: pass.
- Reconciliation contract verifier: pass.
- Reconciliation rerun verifier: pass.
- V2 normative reseal verifier: pass.
- Focused V2 reseal tamper tests: 20 passed.
- Broader R03 set covering six files: 108 passed.
- Black, isort, flake8 with line length 420, and `git diff --check`: pass.
- Current reseal-scope raw traversals, copies, fits, gates, OOS, inference,
  provider/network calls, dependency changes, commits, and pushes: all zero.

The two earlier authorized completed raw scans remain recorded in their prior
result scopes. The zero-call manifest does not rewrite those historical counts.

## 9. Independent review questions

1. Do all three canonical self-hashes and the manifest filesystem hash
   reproduce?
2. Are the historical 90.53% artifacts unchanged and explicitly nonnormative?
3. Does the legacy source artifact independently prove its fail-closed status
   and HIGH denominator-conflation observation?
4. Is the lost-driver conclusion supported without inventing a replacement
   rule for 655,960?
5. Do the two V2 measurements and 664-ledger accounting support replacement of
   the legacy value rather than reconciliation to it?
6. Does the separate attestation close the missing execution-surface block
   without changing the independently reviewed targeted result?
7. Are canonical hashes used for normative identity and filesystem hashes only
   for file/review anchors?
8. Does the `total_news_positive_frames` alias prevent the previously noted
   semantic ambiguity?
9. Do direct, re-signed mutations fail closed before any acceptance output?
10. Should the requested disposition advance to
    `INDEPENDENT_V2_NORMATIVE_RESEAL_REVIEW_APPROVED`?

Until that disposition is independently granted, the review gate remains
closed. Commit and push remain separate user decisions.
