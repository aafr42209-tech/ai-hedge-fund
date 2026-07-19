# R02 overlay v2 provider-free implementation-plan review handoff

Date: 2026-07-19

Status: **TECHNICAL REVIEW ACCEPTED — ORGANIZATIONAL INDEPENDENCE NOT ESTABLISHED — IMPLEMENTATION/LIVE NO-GO**

Base commit: `69bdac5bbad9c41f3ae1bd769a83faa699ead950`

## 0. Received technical review

- reviewer: `Claude (Fable 5)`;
- environment and date: same local repository, `2026-07-19`;
- relationship: D4 and overlay-v2 same-session lineage;
- independence: technical verification only; organizational independence is
  not established;
- reviewed state: HEAD `69bdac5` plus exactly four modified and five new files;
- reviewed handoff SHA-256:
  `9d9440d8e0b53a3734b963657a6d9e33b9defd2d97cecf32879165c6e8a0b830`;
- verifier reproduced with exit `0`, `negative_tests=7`, provider calls `0`,
  LIVE runs `0`, and implementation files `0`;
- deep diff confirmed that headroom changed only `analysis_status`,
  preregistration changed only its dependent component pin, and all scientific
  power, operating-characteristic, threshold, and budget values were unchanged;
- disposition: `ACCEPT`, zero blocking findings, two informational notes.

Informational implementation obligations:

1. I0 must add `jsonschema` as a development dependency before executing the
   metaschema gate.
2. Implementation evidence must include a 13-gate-to-test traceability table.

The user explicitly accepted the plan and authorized commit and push of exactly
this nine-file planning change set. Implementation, fixture materialization,
provider calls, private-data export, pilot, confirmatory LIVE, retry,
replacement, and resume remain unauthorized.

## 1. Review scope

Review the provider-free implementation plan only. The reviewed change set is
exactly four status/hash-chain updates plus five new planning artifacts. No
implementation module, research fixture, provider adapter, production root,
provider call, Codex execution, pilot, or LIVE run exists in this change set.

The historical accepted preregistration remains anchored at commit `69bdac5`.
The only accepted-input semantic edit is correction of the stale
`analysis_status`; all scientific values remain byte-for-byte unchanged after
ignoring that field.

## 2. Pinned review set

- `docs/r02-overlay-v2-deterministic-comparator-design.md`:
  `3952c505b998f397c9aa7b72f8ad0b6e8e48dd4081b297cdca2652a319705676`
- `docs/r02-overlay-v2-headroom-and-power-design.json`:
  `933de346ed9a1482521e1c35c18f367f494f5f9fa32458c575526dff1c2c1d94`
- `docs/r02-overlay-v2-implementation-plan.json`:
  `3bfca6c818525e51c7ba9a424b7ca4ad71a4c52e03ab5e28c2d0c8d54ff80fa9`
- `docs/r02-overlay-v2-implementation-plan.md`:
  `70f08d5c94670a399d3a6ef1b0ad05c7b55da68308b8e0a79c0c8d40c4734768`
- `docs/r02-overlay-v2-payload-schema-draft.json`:
  `6a827af6ff6c56f2b4db1c575a1fe2890417ac8feba1ffbb0feb9bec3e1456d5`
- `docs/r02-overlay-v2-preregistration-draft.json`:
  `14503448dc6f5f7ca5b43ef093d6470852029089abb117fa06dcbfdfc43adc88`
- `docs/r02-overlay-v2-preregistration-review-handoff.md`:
  `ff0202c8c2a57fb396c2565828cf56dc286a491b88928b0cf32eef845e5314c3`
- `docs/r02-overlay-v2-response-schema-draft.json`:
  `963a7fb8ddfa002402e44e94518c6fd4ba3aa964b5a5d353eae09480bd9859c1`
- `docs/r02-overlay-v2-zero-call-manifest.json`:
  `65a3fc3f7634b80e25a765054752690608e0f65818d39dc50d62f670f815d151`
- `scripts/r02_overlay_v2_implementation_plan_verify.py`:
  `f65fc39098e8fedfb319df4e5cd40edc8ac82ec8a1009d30e3bddd344bfee342`
- `docs/r02-overlay-v2-implementation-plan-zero-call-manifest.json`:
  `6a3099284fb6391d1f26ef9af4e800a744c10a92526e325d3532bea56f7bd617`

Historical anchors:

- accepted preregistration commit:
  `69bdac5bbad9c41f3ae1bd769a83faa699ead950`;
- accepted pre-normalization review handoff:
  `e9a1fcaf70b03bef79f34624b19ea945b534c3f3e61d2246575744b3267871a3`;
- accepted pre-normalization zero-call manifest:
  `bd98b9e75b4e8f41b7796cd7089eeb39aa990140c11b08788de41bbc431fd1bf`.

## 3. Required review questions

1. Does the plan preserve the D3/D4 scoped interpretation without claiming
   general LLM failure?
2. Is status normalization limited to the stale field, with all scientific
   values unchanged?
3. Are the eight future modules minimal, cohesive, and free of provider
   capability?
4. Are information parity and post-selection-only oracle access enforceable by
   the proposed type/call boundaries?
5. Are integer formulas, units, rounding, canonicalization, and candidate-ID
   tie-breaking exact enough for implementation?
6. Do I0–I5 prevent fixture materialization and provider use while allowing
   fixed in-memory implementation tests?
7. Do the 13 test gates cover schema parity, public metrics, 19 scorers,
   grounding, replay, headroom, power, and failure ITT?
8. Does the plan avoid pilot-utility tuning and preserve split/seed firewalls?
9. Are implementation, commit, push, provider, fixture, and LIVE permissions
   all explicitly absent?
10. Are reviewer identity, environment, relationship, and organizational
    independence recorded honestly?

## 4. Reproduction

From repository root:

```powershell
.venv\Scripts\python.exe scripts\r02_overlay_v2_implementation_plan_verify.py
git status --short
```

Expected marker:

```text
PASS_R02_OVERLAY_V2_PROVIDER_FREE_IMPLEMENTATION_PLAN negative_tests=7 provider_calls=0 live_runs=0 implementation_files=0
```

The verifier may execute only read-only Git subprocesses. It contains no network,
provider, credential, fixture-generation, or production-root code.

## 5. Required provenance

Record reviewer name or stable role, environment, date, reviewed base and
artifact hashes, relationship to this drafting session, commands and exit codes,
blocking/nonblocking findings, and whether organizational independence is
established. Same-session reproduction is technical verification, not
organizational independence.

## 6. Required next order

1. technical review of this exact pinned set;
2. correction and re-verification of findings;
3. explicit plan acceptance;
4. separately authorized commit and push of the planning change set;
5. separate provider-free implementation approval;
6. implementation, tests, sealing, and implementation review;
7. later fixture/seed/headroom gates under separate approvals.

Plan acceptance must not be interpreted as implementation, fixture, provider,
private-data export, pilot, confirmatory LIVE, retry, replacement, resume,
commit, or push approval.
