# R02 D3 indivisible 6+49 LIVE result

Date: 2026-07-18

## Final status

`HARD_STOP` after the first launched attempt. The planned 55-attempt protocol
did not complete, no selector outcome was produced, and the utility hypothesis
was not evaluated.

This run is sealed. No retry, replacement, or relabeling is allowed under the
approved contract.

## Frozen execution identity

- approved implementation commit: `a85c2925d04b67a7628b1c0301e8cd3a48142f66`
- runner readiness freeze: `a779a6b722870889128e58a9fbf4f149d78f88dc69535a7aabc7722a0e1957c6`
- external authorization: `9242b4c4c5c9658ceb489902322a58a6f7c4caa7a851dc09e00fac2e6d748a6c`
- executable: `codex-cli 0.144.1`, SHA-256 `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`
- requested model: `gpt-5.6-sol`
- run ID: `r02-d3-live-a779a6b7-20260718`

The approved source-pin worktree was checked out with LF preservation. A first
provider-free start stopped before reservation because ignored sealed frame
artifacts were absent from the detached worktree. The 162 sealed files were
then copied exactly and all 55 episodes passed provider-free load/hash checks.
The copied frame tree was `316eb5757b2eda3a04ec16f19a225df7a6e44fdf7f506482aa947b9cf77fb494`
under `r02_d3_preflight._filesystem_tree`, exactly matching the frozen
`R02_D2C_FRAME_TREE_SHA256` constant.
The same run ID and audit root were resumed; this was not a replacement run.

## Terminal event

Attempt 1, fixture `development-0003`, reached the provider API and received an
HTTP 400 `invalid_json_schema` response. The response-format schema required
array did not contain every property key; `schema_version` was missing.

Observed terminal accounting:

- reserved attempts: 1/55
- launched attempts: 1/55
- settled attempts: 0/55
- unsettled attempts: 1
- completed selector outcomes: 0
- debited tokens: 32,000 (full reserve)
- terminal code: `contradictory_terminal_status`
- retry/replacement: 0

The run terminated before the first ten-minute progress report, so the start
and terminal reports are the only progress reports.

## Provider-call accounting finding

The structured provider HTTP 400 proves one API submission occurred. The
terminal ledger nevertheless records `external_provider_calls: 0` because the
adapter increments that field only after successful response/token parsing.
Therefore the authoritative operational count is **one observed provider API
submission**, and the ledger value is an undercount that must be fixed before
any successor authorization.

## Audit seal

- strict replay: PASS
- terminal anchor sequence: 14
- audit files: 42
- audit bytes: 50,110
- audit tree SHA-256 (`r02_d3_preflight._filesystem_tree`, 42 files): `c36402037e40fdd24e79df35aeaa386f200c1f93574fca4b16c198cae452d652`
- durable raw root: `.research_artifacts/r02-d3-live-a779a6b7-20260718`
- structured evidence: `docs/r02-d3-live-evidence.json`

## Final disposition

| Question | Result |
| --- | --- |
| Did the indivisible 6+49 complete? | **NO — HARD_STOP** |
| Was a provider API submission observed? | **YES — 1** |
| Were selector/utility outcomes produced? | **NO** |
| Was the utility hypothesis evaluated? | **NO** |
| May this sealed run be retried or replaced? | **NO** |

Any successor must be a new protocol identity. Before a new freeze or approval,
provider-free work must correct the output-schema `required` contract, test it
against the provider-compatible schema rules, and make provider-call accounting
record attempted LIVE submissions even when parsing fails. A successor LIVE run
requires a new readiness freeze and new explicit authorization.
