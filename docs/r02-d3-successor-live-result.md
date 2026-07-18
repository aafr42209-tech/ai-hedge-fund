# R02 D3 successor indivisible 6+49 LIVE result

Date: 2026-07-18

## Final status

The one explicitly authorized successor LIVE run completed normally. All 55
planned episodes were reserved, launched, settled, evaluated, and terminally
sealed. No retry, resume, replacement, or second authorization occurred.

**Run status: `COMPLETE`. Frozen primary utility verdict: `SUPPORTED`.**

The verdict is limited to the sealed R02 system-utility hypothesis and frozen
frame. It is not an investment, trading, deployment, or additional-LIVE
authorization.

## Frozen execution identity

- run ID: `r02-d3-successor-84750652-20260718`
- approved implementation commit: `e5643a34bed91e7d9618ab434f9b695e127c4bfe`
- prelaunch package commit: `9d1b9525f85caf88b41beabf49e97928b2ec1ef6`
- successor readiness freeze: `847506528aa68b32bc1a7ec5ef0261d369ee638addc7c1590a3180369751bd54`
- external authorization: `0053aa6191e7cc860c9a3968644e0c9968939f41cf7f730a1172f21635ac0f19`
- launcher: `10cdc3970f112e5da28f5cc1c13ac7da799fbdfdd36653094e19b61ca569c1d5`
- executable: `codex-cli 0.144.1`, SHA-256 `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`
- requested model: `gpt-5.6-sol`
- strict successor output schema: `f8089e667cff113d600e3c9c726fbbff4f80c8f522804525e37d8693bbd36937`
- authorization scope: `INDIVISIBLE_6_PLUS_49_LIVE`

## Terminal accounting

- reserved attempts: 55/55
- launched attempts / provider submissions: 55/55
- settled attempts: 55/55
- completed selector outcomes and paired results: 55/55
- unsettled attempts: 0
- selector fallbacks: 0
- settlement failures: 0
- invalid budget breaches: 0
- debited tokens: 655,122 of the frozen 1,760,000 cap
- terminal code: none
- terminal anchor sequence: 774

The successor launch-point accounting reconciles exactly: 55 audited launches,
55 external-provider calls in the terminal ledger, and 55 settlements.

## Selector behavior

All 55 provider responses passed strict structured-output parsing. The opaque
presented IDs selected were P00 18 times, P01 16, P02 13, and P03 8. After
presentation-order reversal, every selection resolved to the same canonical
candidate ID `11eb14e46d7e2bd45610d4e4c92945332a947dae5f2be307d8ccfd3458e3ec11`.
No deterministic-baseline fallback was used.

## Frozen primary evaluation

The calculation used the accepted D2c statistical freeze SHA-256
`45a68aacde0135a4f5e446f1022406d35e24346b23df1bc7e4db78889c6e12b9`
and the outcome-independent evaluation seed
`319dea85b61187c07089deedb525d4d927ffc03dc7ea2026e4be8022f2df9f68`.
It applied 10,000 PCG64 fixture-within-stratum bootstrap resamples and the
frozen 250th/9,750th nearest-rank interval.

The primary ITT population is the full 160-fixture frame: 120 representative
fixtures and 40 challenge fixtures. The 55 eligible LIVE fixtures contribute
their paired deltas; the 105 trigger-false representative fixtures contribute
the preregistered zero delta.

| Frozen quantity | Result |
| --- | ---: |
| Eligible paired fixtures, M | 55 |
| Minimum M | 46 |
| System effect, theta e12 | 92,928,891 |
| 95% bootstrap lower e12 | 51,470,259 |
| 95% bootstrap upper e12 | 138,094,263 |
| Minimum effect, delta_min e12 | 50,000,000 |
| Lower minus delta_min e12 | 1,470,259 |
| Decision | **SUPPORTED** |

Among the 55 eligible paired results, 43 deltas were positive and 12 negative;
their sum was 14,868,622,616 e12. The frozen decision rule is satisfied because
the bootstrap lower bound is strictly greater than `delta_min`, M is at least
46, and all fail-closed execution gates passed. The lower-bound margin is
positive but narrow, so the exact frozen label should be preserved without
stronger extrapolation.

## Audit and durable evidence seal

- strict replay on original audit: PASS
- strict replay on durable copy: PASS
- audit files: 2,322
- audit bytes: 46,379,372
- audit tree SHA-256 (`r02_d3_preflight._filesystem_tree`): `bca066c859ded362cc6f531c236a224cacce6f2a4f0f62a06f15f8cc0d950bc4`
- durable raw files: 2,327
- durable raw bytes: 46,392,220
- durable raw tree SHA-256 (same method): `b3cc74da593975865cd42087bb18bdc3f82d1c5666df5d98c5eb8ff92119dbea`
- durable raw root: `.research_artifacts/r02-d3-successor-84750652-20260718`
- structured evidence: `docs/r02-d3-successor-live-evidence.json`

The archived audit copy is byte-for-byte tree-identical to the original audit.
The archived stderr is empty. The audit contains one terminal record with
`status=COMPLETE` and no terminal code.

## Independent review handoff

An independent reviewer completed every handoff check on 2026-07-18 with no
blocking finding:

1. Recompute the authorization, launcher, executable, readiness-freeze, output-
   schema, and prelaunch hashes.
2. Recompute both filesystem-tree hashes using
   `v2.research.overlay.r02_d3_preflight._filesystem_tree`.
3. Run `replay_audit_root` against the durable audit copy and confirm anchor
   774, 55 reservations/launches/settlements/outcomes, one terminal, and exact
   terminal-ledger reconciliation.
4. Rebuild the 160-fixture delta vector from the frozen frame and 55
   `paired_result` payloads, then recompute the weighted mean and frozen
   bootstrap interval with the preregistered seed.
5. Confirmed no retry/replacement process or second run exists and that the
   closeout diff contains documentation only.

The reviewer independently reproduced the `SUPPORTED` verdict bit-for-bit,
including theta `92,928,891` e12 and interval
`[51,470,259, 138,094,263]` e12.

## Final disposition

| Question | Answer |
| --- | --- |
| Did the indivisible 6+49 complete? | **YES — COMPLETE** |
| Did provider-call accounting reconcile? | **YES — 55 = 55 = 55** |
| Were fallback or unsettled attempts present? | **NO** |
| Was the frozen utility hypothesis evaluated? | **YES — SUPPORTED** |
| Is a retry or replacement allowed? | **NO** |
| Is another LIVE run authorized? | **NO** |
| Is investment or deployment authorized? | **NO** |
| Closeout state | **INDEPENDENTLY REVIEWED** |
