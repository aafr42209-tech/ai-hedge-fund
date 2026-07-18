# R02 D4-S1 reviewer reveal handoff

## Current gate

Status: `COORDINATOR_REVEAL_SEALED_REVIEWER_REVEAL_PENDING`

The user authorized S1 seed resolution only, assigned Codex as coordinator and
Claude as reviewer, and did not authorize frame generation or scan. This
handoff requests only the one reviewer reveal required by the frozen
commit/reveal order. It does not authorize seed-derived frame work, provider
calls, Codex exec, micro-pilot, LIVE, LIVE authorization artifacts, retry,
replacement, commit, or push.

## Immutable lineage to verify before reviewer custody access

| Item | Required SHA-256 or value |
|---|---|
| Accepted design commit | `d9f984866c8775153d9c1ac1aea9b49fc9647635` |
| Accepted design manifest | `784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900` |
| Generator config | `e6598cca07c846650f7d7c157c16a6d77aefd4a94966c6624288239b5ae04ccf` |
| Frozen seed contract | `7b670cc9613a16e6f170b613a3b05a24529699c379bad14cad911736e34792fa` |
| S1 intent | `638a8a0a5de3718576fee7446e064282fa871f18b335364c0294ec831cdd016e` |
| Coordinator commitment artifact | `7ea3288a36424f939d295ec2e96751b33908a82dba78818cfdd16adbdd0687fe` |
| Reviewer commitment artifact | `2c93c329e30693ea3de99f9114f1f16af9282acfaff6b2b49e2e555438092215` |
| Prior S1 zero-call manifest | `79c8fa298d3268ef2f0abb15408f285f79b83f8914bae4032572f03579639c9b` |
| Coordinator reveal artifact | `a674c1ae1852b51650b680916ce6c5dbdb8d652384bae1a6209c970558e0c8a5` |
| Coordinator-reveal zero-call manifest | `9775488293d9a590e754e5e5d6a7d53c3e881e35c735e12370eb4add65b16d7a` |

Commitments:

- coordinator:
  `7d2f9653b12d3b3ad6746ea067829b1b5222564821ace311f1f7fb98550fb5d3`
- reviewer:
  `4943ea6a6f990fe88d400d6d3afe880c2634c65a4a842c9d2966d662ee52b144`

The coordinator reveal exists only in
`docs/r02-d4-s1-coordinator-reveal.json`. Read it from that artifact; this
handoff intentionally does not duplicate the reveal value. Verify that hashing
the decoded 32 raw bytes reproduces the coordinator commitment before accessing
reviewer custody.

## Required read-only checks

From repository root:

```powershell
.\.venv\Scripts\python.exe scripts\r02_d4_s1_reveal_verify.py `
  --repo-root . `
  --stage coordinator-reveal

.\.venv\Scripts\python.exe -m pytest `
  v2\research\overlay\test_r02_d4_s1_reveal.py -q
```

Expected:

- `PASS_COORDINATOR_REVEAL_SEALED`
- `coordinator_reveal_commitment_match=true`
- `reviewer_nonce_reveal_hex=null`
- `resolved_frame_seed_sha256=null`
- `8 passed`
- provider calls 0, frame generation false, frame scan false, LIVE false
- protected artifact root: 3,284 files, 49,269,991 bytes,
  `3a7ed6ede78176affb13a2b49590ecfe49d5a7156a0c2467d4302021345c7279`
- sealed D3 post-hoc:
  `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
- D3 verdict unchanged: `SUPPORTED`

If any check fails, stop with `ABORT_S1_NO_SEED`. Do not access reviewer
custody and do not generate a replacement nonce.

## Claude action: reviewer reveal exactly once

1. Reuse only the reviewer DPAPI custody blob created for commitment
   `4943ea6a...2b144`. Do not generate a nonce.
2. Fail closed if the expected custody blob is absent, its sealed blob hash is
   not `04b9b87c83845b5719118bc8efe4549d276609ef492378ef47e464f606faeccd`,
   or it cannot be decrypted under the same Windows CURRENT_USER scope.
3. Decrypt the stored reviewer nonce. Before disclosure, verify it is exactly
   32 bytes and that SHA-256 over the raw bytes equals the reviewer commitment.
4. Reveal that verified nonce exactly once by creating
   `docs/r02-d4-s1-reviewer-reveal.json`. Do not print the plaintext in command
   output or commentary. The artifact is the reveal record.
5. Copy the coordinator reveal exactly from its sealed artifact into the
   reviewer reveal artifact. Do not transform, normalize, or re-encode either
   reveal beyond lowercase 64-character hex.
6. Keep `resolved_frame_seed_sha256` null. Codex will independently validate
   both reveals and derive the canonical slot-zero seed once after this artifact
   is returned.
7. Return the reviewer reveal artifact SHA-256. Do not commit or push.

Required reviewer reveal artifact shape:

```json
{
  "schema_version": "r02-d4-s1-reviewer-reveal-v1",
  "status": "REVIEWER_REVEAL_SEALED_SEED_DERIVATION_PENDING",
  "date": "2026-07-18",
  "coordinator_reveal_artifact_path": "docs/r02-d4-s1-coordinator-reveal.json",
  "coordinator_reveal_artifact_sha256": "a674c1ae1852b51650b680916ce6c5dbdb8d652384bae1a6209c970558e0c8a5",
  "reviewer_commitment_artifact_path": "docs/r02-d4-s1-reviewer-commitment.json",
  "reviewer_commitment_artifact_sha256": "2c93c329e30693ea3de99f9114f1f16af9282acfaff6b2b49e2e555438092215",
  "accepted_design_commit": "d9f984866c8775153d9c1ac1aea9b49fc9647635",
  "accepted_design_manifest_sha256": "784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900",
  "generator_config_sha256": "e6598cca07c846650f7d7c157c16a6d77aefd4a94966c6624288239b5ae04ccf",
  "seed_slot": 0,
  "coordinator": "CODEX",
  "reviewer": "CLAUDE",
  "sequence_ordinal": 4,
  "commitment_algorithm": "SHA256_RAW_32_BYTE_NONCE",
  "nonce_byte_length": 32,
  "coordinator_nonce_commitment_sha256": "7d2f9653b12d3b3ad6746ea067829b1b5222564821ace311f1f7fb98550fb5d3",
  "reviewer_nonce_commitment_sha256": "4943ea6a6f990fe88d400d6d3afe880c2634c65a4a842c9d2966d662ee52b144",
  "coordinator_nonce_reveal_hex": "<copy exactly from coordinator reveal artifact>",
  "reviewer_nonce_reveal_hex": "<decrypt once from reviewer custody and verify>",
  "reviewer_reveal_commitment_match": true,
  "reviewer_reveal_count": 1,
  "reviewer_escrow_blob_sha256": "04b9b87c83845b5719118bc8efe4549d276609ef492378ef47e464f606faeccd",
  "reviewer_escrow_retained_encrypted_for_s1_closeout_audit": true,
  "resolved_frame_seed_sha256": null,
  "resolved_frame_id": null,
  "frame_seed_created": false,
  "retry_cap": 0,
  "replacement_cap": 0,
  "alternate_seed_slots": 0,
  "provider_calls": 0,
  "frame_generation": false,
  "frame_scan": false,
  "live_execution": false,
  "commit_created": false,
  "push_performed": false,
  "authorization": "S1_REVIEWER_REVEAL_ONLY_SEED_DERIVATION_PENDING_NO_FRAME_NO_SCAN_NO_PROVIDER_NO_LIVE"
}
```

## Fail-closed rule

Any artifact drift, custody error, nonce-length error, commitment mismatch, or
write failure aborts S1 without a seed. No retry, replacement, alternate slot,
or discarded-seed path exists. A newly named independent review is required
after an abort.

## Required reviewer response

On success, report `PASS_REVIEWER_REVEAL_SEALED` and include only:

- reviewer reveal artifact SHA-256,
- confirmation that the stored nonce was decrypted and revealed exactly once,
- confirmation that both commitment comparisons passed,
- confirmation that seed derivation, frame generation/scan, provider, LIVE,
  commit, and push did not occur.

Do not repeat either reveal value in the response.
