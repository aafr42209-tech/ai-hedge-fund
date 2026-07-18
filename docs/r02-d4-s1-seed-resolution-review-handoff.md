# R02 D4-S1 seed resolution independent review handoff

## Review target

Review verdict requested: accept or reject the provider-free S1 seed resolution
only.

Current status:
`SEED_SLOT_ZERO_RESOLVED_AND_SEALED_PENDING_INDEPENDENT_CLOSEOUT_REVIEW`

Resolved slot-zero seed SHA-256:
`0716a1b9c13aec596b29776f48b3d8d1fc0a9afacc1c5010bd2cf2a9629d0621`

This seed is not authorization to generate or scan a frame. Frame generation,
frame scan, provider calls, Codex exec, micro-pilot, LIVE, LIVE authorization
artifacts, retry, replacement, commit, and push remain outside this review.
Do not repeat either reveal value in the review response.

## Required byte identities

| Artifact | Required SHA-256 |
|---|---|
| `docs/r02-d4-replication-design.json` | `784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900` |
| `docs/r02-d4-seed-contract.json` | `7b670cc9613a16e6f170b613a3b05a24529699c379bad14cad911736e34792fa` |
| `docs/r02-d4-s1-seed-intent.json` | `638a8a0a5de3718576fee7446e064282fa871f18b335364c0294ec831cdd016e` |
| `docs/r02-d4-s1-coordinator-commitment.json` | `7ea3288a36424f939d295ec2e96751b33908a82dba78818cfdd16adbdd0687fe` |
| `docs/r02-d4-s1-reviewer-commitment.json` | `2c93c329e30693ea3de99f9114f1f16af9282acfaff6b2b49e2e555438092215` |
| `docs/r02-d4-s1-coordinator-reveal.json` | `a674c1ae1852b51650b680916ce6c5dbdb8d652384bae1a6209c970558e0c8a5` |
| `docs/r02-d4-s1-reviewer-reveal.json` | `52227dcbcc3c8754a95a425172fc9f31479f62b5b4155ae5c1ed15995c198ec0` |
| `docs/r02-d4-s1-resolved-seed.json` | `a05f3b2da66dfda6ba3369effa1734f8c760e6c1735db80306b07f51a8abeef5` |
| `docs/r02-d4-s1-zero-call-manifest.json` | `79c8fa298d3268ef2f0abb15408f285f79b83f8914bae4032572f03579639c9b` |
| `docs/r02-d4-s1-coordinator-reveal-zero-call-manifest.json` | `9775488293d9a590e754e5e5d6a7d53c3e881e35c735e12370eb4add65b16d7a` |
| `docs/r02-d4-s1-seed-resolution-zero-call-manifest.json` | `c6bd5a1f79cfa218cad5a7a55deaad671df97e0c0b87a7f892e3664a90e1d3cb` |
| `v2/research/overlay/r02_d4_s1_resolve.py` | `2c8685a6ad8c05a3727d1f8efe867620a35b66485290bf78dea1cd60d05640d7` |
| `v2/research/overlay/test_r02_d4_s1_resolve.py` | `6c767021a6f21b6d695233cc23db697581b5d1383785fbc34e99b1be6245969d` |
| `scripts/r02_d4_s1_resolve_verify.py` | `0fb8828e53af91a3682e25164e2255cd27fb7b7981301c143ac622aef35df262` |

Accepted design commit:
`d9f984866c8775153d9c1ac1aea9b49fc9647635`

Generator config SHA-256:
`e6598cca07c846650f7d7c157c16a6d77aefd4a94966c6624288239b5ae04ccf`

## Mandatory skeptical checks

1. Verify all hashes above before reading the resolved preimage.
2. Confirm coordinator and reviewer commitment artifacts have ordinals 1 and 2,
   and both reveal artifacts have ordinals 3 and 4.
3. Recompute each commitment as SHA-256 over the decoded 32 raw nonce bytes.
   Both must match their prior commitments. Do not print the reveal values.
4. Confirm the coordinator reveal copied into the reviewer artifact is byte-for-
   byte equal to the sealed coordinator reveal.
5. Confirm the resolved artifact preimage has exactly the keys in the frozen
   `preimage_template`, with the three static pins and four interactive fields
   filled and every other frozen value unchanged.
6. Confirm the preimage uses seed slot 0, representative 150, challenge 50,
   total 200, and no D3 fixture ID, individual delta, utility, rank, provider
   output, frame scan, or outcome score.
7. Recompute SHA-256 over repository canonical JSON bytes for the exact preimage.
   It must equal both `preimage_canonical_sha256` and
   `resolved_frame_seed_sha256`:
   `0716a1b9c13aec596b29776f48b3d8d1fc0a9afacc1c5010bd2cf2a9629d0621`.
8. Confirm `seed_derivation_count=1`, `seed_replacement_count=0`,
   `alternate_seed_slots=0`, and no retry/replacement surface exists.
9. Confirm `frame_seed_created=true` means only that the seed digest is sealed;
   `resolved_frame_id` remains null and frame generation/scan remain false.
10. Recompute the protected artifact root with
    `v2.research.overlay.r02_d3_preflight._filesystem_tree`. Required identity:
    3,284 files, 49,269,991 bytes,
    `3a7ed6ede78176affb13a2b49590ecfe49d5a7156a0c2467d4302021345c7279`.
11. Confirm the sealed D3 post-hoc remains
    `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
    and verdict `SUPPORTED` is unchanged.
12. Confirm HEAD remains the accepted design commit, tracked diff is empty,
    provider calls are 0, and no commit or push occurred.

## Reproduction commands

From repository root:

```powershell
.\.venv\Scripts\python.exe scripts\r02_d4_s1_resolve_verify.py `
  --repo-root . `
  --stage resolved-seed

.\.venv\Scripts\python.exe -m pytest -q `
  v2\research\overlay\test_r02_d4_design.py `
  v2\research\overlay\test_r02_d4_s1_seed.py `
  v2\research\overlay\test_r02_d4_s1_reveal.py `
  v2\research\overlay\test_r02_d4_s1_resolve.py

.\.venv\Scripts\python.exe scripts\r02_d3_successor_posthoc.py `
  --repo-root . `
  --output docs\r02-d3-successor-provider-free-posthoc.json `
  --verify-existing
```

Expected:

- `PASS_SEED_SLOT_ZERO_RESOLVED_AND_SEALED`
- D4/S1 tests: `36 passed`
- post-hoc byte replay: pass
- frame generation false, frame scan false, provider calls 0, LIVE false

## Verdict rule

Return `PASS_S1_SEED_RESOLUTION` only if every check reproduces. This accepts
only the seed-resolution closeout draft. It grants no frame, provider, LIVE,
commit, or push authority.

For any mismatch return `BLOCKING_FINDINGS` with exact artifact, field, expected
value, and observed value. Because both reveals are consumed, no re-reveal,
retry, replacement, alternate seed, or discarded-seed path is allowed. A
blocking identity failure means `ABORT_S1_NO_FRAME` and requires a newly named
review; it must not trigger another seed derivation.
