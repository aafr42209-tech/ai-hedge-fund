# R02 D4-S1 reviewer commitment handoff

## Current gate

Status: `COORDINATOR_COMMITMENT_SEALED_REVIEWER_COMMITMENT_PENDING`

This handoff authorizes no action. The user separately authorized R02 D4-S1
seed resolution only and assigned Codex as coordinator and Claude as reviewer.
Frame generation, frame scan, provider calls, Codex exec, micro-pilot, LIVE,
LIVE authorization artifacts, retry, replacement, commit, and push remain
unauthorized.

The frozen contract combines seed resolution and frame generation in its second
protocol sentence. The user imposed a stricter split gate: this S1 may resolve
and seal seed slot zero, but a later explicit authorization is required before
any frame generation or scan. This safer difference is recorded in the S1
intent and must not be widened.

## Immutable inputs to verify first

| Item | Required value |
|---|---|
| Accepted design commit | `d9f984866c8775153d9c1ac1aea9b49fc9647635` |
| Accepted design manifest | `docs/r02-d4-replication-design.json` |
| Accepted design manifest SHA-256 | `784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900` |
| Generator config SHA-256 | `e6598cca07c846650f7d7c157c16a6d77aefd4a94966c6624288239b5ae04ccf` |
| Frozen seed contract SHA-256 | `7b670cc9613a16e6f170b613a3b05a24529699c379bad14cad911736e34792fa` |
| S1 intent SHA-256 | `638a8a0a5de3718576fee7446e064282fa871f18b335364c0294ec831cdd016e` |
| Coordinator commitment artifact SHA-256 | `7ea3288a36424f939d295ec2e96751b33908a82dba78818cfdd16adbdd0687fe` |
| S1 zero-call manifest SHA-256 | `79c8fa298d3268ef2f0abb15408f285f79b83f8914bae4032572f03579639c9b` |

`accepted_design_manifest_sha256` means the machine-readable accepted design
JSON above. `docs/r02-d4-zero-call-manifest.json` is boundary evidence and is
not the accepted design manifest. The generator config value must independently
match both `docs/r02-d2c-frame-manifest.json:generator_config_sha256` and
`canonical_sha256(GeneratorConfig())`.

## Coordinator commitment already sealed

- Artifact: `docs/r02-d4-s1-coordinator-commitment.json`
- Algorithm: `SHA256_RAW_32_BYTE_NONCE`
- Nonce length: 32 raw bytes
- Coordinator commitment:
  `7d2f9653b12d3b3ad6746ea067829b1b5222564821ace311f1f7fb98550fb5d3`
- Coordinator reveal: absent
- Reviewer nonce information received by coordinator: none
- Seed: unresolved

Verify the artifact byte hash and commitment before generating any reviewer
nonce. If either differs, stop with `ABORT_S1_COORDINATOR_COMMITMENT_DRIFT`.

## Claude action: reviewer commitment only

1. Verify every immutable input above and run the read-only checks below.
2. Only after the coordinator artifact is verified, generate exactly one
   independent nonce using Python `secrets.token_bytes(32)` or an equivalent
   operating-system CSPRNG.
3. Compute `sha256(reviewer_nonce_raw_bytes).hexdigest()`. Do not hash its text,
   Base64, or hex representation.
4. Keep the reviewer nonce outside the repository in reviewer-controlled
   encrypted custody. Do not emit or persist plaintext. Do not let Codex create
   or choose this nonce.
5. Create `docs/r02-d4-s1-reviewer-commitment.json` with the fields below. The
   reviewer commitment is the only new interactive seed field allowed now.
   Both reveal fields and the resolved seed must remain null.
6. Return the reviewer commitment and the SHA-256 of the reviewer commitment
   artifact. Do not reveal the reviewer nonce yet. Do not commit or push.

Required reviewer artifact shape:

```json
{
  "schema_version": "r02-d4-s1-reviewer-commitment-v1",
  "status": "REVIEWER_COMMITMENT_SEALED_COORDINATOR_REVEAL_PENDING",
  "date": "2026-07-18",
  "coordinator_commitment_artifact_path": "docs/r02-d4-s1-coordinator-commitment.json",
  "coordinator_commitment_artifact_sha256": "7ea3288a36424f939d295ec2e96751b33908a82dba78818cfdd16adbdd0687fe",
  "accepted_design_commit": "d9f984866c8775153d9c1ac1aea9b49fc9647635",
  "accepted_design_manifest_sha256": "784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900",
  "generator_config_sha256": "e6598cca07c846650f7d7c157c16a6d77aefd4a94966c6624288239b5ae04ccf",
  "seed_slot": 0,
  "coordinator": "CODEX",
  "reviewer": "CLAUDE",
  "sequence_ordinal": 2,
  "commitment_algorithm": "SHA256_RAW_32_BYTE_NONCE",
  "nonce_byte_length": 32,
  "coordinator_nonce_commitment_sha256": "7d2f9653b12d3b3ad6746ea067829b1b5222564821ace311f1f7fb98550fb5d3",
  "reviewer_nonce_commitment_sha256": "<64 lowercase hex>",
  "coordinator_nonce_reveal_hex": null,
  "reviewer_nonce_reveal_hex": null,
  "resolved_frame_seed_sha256": null,
  "resolved_frame_id": null,
  "frame_seed_created": false,
  "retry_cap": 0,
  "replacement_cap": 0,
  "provider_calls": 0,
  "frame_generation": false,
  "frame_scan": false,
  "live_execution": false,
  "commit_created": false,
  "push_performed": false,
  "authorization": "S1_REVIEWER_COMMITMENT_ONLY_NO_REVEAL_NO_FRAME_NO_SCAN_NO_PROVIDER_NO_LIVE"
}
```

Reviewer custody metadata may be added as a nested object, but it must not
contain the plaintext nonce, an unencrypted nonce path, or any outcome-derived
input.

## Read-only checks

From repository root:

```powershell
.\.venv\Scripts\python.exe scripts\r02_d4_s1_seed_verify.py --repo-root .
.\.venv\Scripts\python.exe -m pytest v2\research\overlay\test_r02_d4_s1_seed.py -q
```

Expected results before reviewer nonce generation:

- `PASS_COORDINATOR_COMMITMENT_SEALED`
- `8 passed`
- protected artifact root: 3,284 files, 49,269,991 bytes,
  `3a7ed6ede78176affb13a2b49590ecfe49d5a7156a0c2467d4302021345c7279`
  using `v2.research.overlay.r02_d3_preflight._filesystem_tree`
- sealed D3 post-hoc SHA-256:
  `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
- D3 verdict unchanged: `SUPPORTED`

## Fail-closed rule

Any static-pin drift, coordinator artifact mismatch, nonce generation or
custody error, malformed commitment, or later reveal mismatch aborts S1 without
a seed. No retry, replacement, alternate seed slot, or discarded-seed path
exists. A newly named independent review is required after an abort.

## Required reviewer response

On success, report:

`PASS_REVIEWER_COMMITMENT_SEALED`

and include only:

- reviewer commitment SHA-256,
- reviewer commitment artifact SHA-256,
- confirmation that the nonce was independently generated once and retained in
  encrypted reviewer custody,
- confirmation that no reveal, seed, frame, scan, provider, LIVE, commit, or
  push action occurred.

On failure, report `ABORT_S1_NO_SEED` plus the exact failing check. Never create
a replacement nonce.
