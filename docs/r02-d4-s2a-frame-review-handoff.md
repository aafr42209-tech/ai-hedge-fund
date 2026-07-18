# R02 D4-S2A provider-free frame independent review handoff

## Required verdict boundary

This handoff requests read-only review of one provider-free frame generation,
frozen admission scan, seal, and deterministic byte replay. The passing verdict
is `PASS_PROVIDER_FREE_S2A_FRAME_SEALED`.

A pass admits only the provider-free frame draft. It does not authorize a
statistical freeze, provider budget, provider call, Codex exec, micro-pilot,
LIVE execution, retry/replacement, commit, or push. Do not run the generation
script during review.

## Starting lineage

- Branch: `codex/llm-overlay-research-01`
- HEAD/upstream at generation: `17d9a382075d5008c79b42d52f2a8409947b4b04`
- Accepted design: `d9f984866c8775153d9c1ac1aea9b49fc9647635`
- S1 resolved-seed artifact SHA-256:
  `a05f3b2da66dfda6ba3369effa1734f8c760e6c1735db80306b07f51a8abeef5`
- Reused slot-0 seed:
  `0716a1b9c13aec596b29776f48b3d8d1fc0a9afacc1c5010bd2cf2a9629d0621`
- Accepted abort closeout commit: `17d9a382...7b4b04`
- Predecessor abort verdict: `PASS_ABORT_S2_NO_RETRY`
- Quarantined predecessor root:
  `.research_artifacts/r02-d4-frame-0716a1b9c13a`, 201 files,
  SHA-256 `2f15d7c9...d132`
- Successor identity/root:
  `r02-d4-s2a-frame-0716a1b9c13a` /
  `.research_artifacts/r02-d4-s2a-frame-0716a1b9c13a`

## Expected byte hashes

| Item | SHA-256 |
|---|---|
| intent | `f126fd3da9167aa6982ed40514e14019a2ed64a7de16d001cc5a914f2438f04c` |
| docs frame manifest | `368e01509b04a53928df2d729f0914dbd0c1ee14c5221a6e189fbf7b8bfa4ba1` |
| docs frame seal | `40aec915d3d24598ad2cbc46713a949b8c8ee5401d5768695b9be918b8bb5838` |
| replay-verifier diagnostic | `3d01f8dd17c3bebf6efed3efda834db8abe43dc6acc4279f57419d250758f43a` |
| zero-call manifest | `2afe3a93d8a66a0919dc5d3041bb0537bc249f6c4aa89ffcc9b861c5b9b71503` |
| S2A frame builder | `5ed3164d6f7dc39785de6b70ce1dc90c615feebe7e754b6971cd94e68292f5c2` |
| generation script | `79b76ad19637cbf1d49f6e52d76e4fd37d9c6fb812a60c659511ae91c6613bc3` |
| pre-generation verifier | `b18863976a756eddfc151b2173a14c8ce68414f16f4ff2abfff5902ea6b876cf` |
| additive sealed-replay verifier | `8d81486ac4f268b9f654324a5d8cb0360960f9cc97abb894609b679bcf610383` |
| S2A focused tests | `4187f3427e65e22fcd256c061a0fc6f85b6b58c52ff9c2326397fa87d1cc6198` |
| unchanged S2 base builder | `178e9b5d943d2062517dfd5be746968e135b4a4bc1248092f17960b00e9786c3` |
| unchanged candidate generator | `29c13547230d1729d8b9cec637ccb13335fbcae52c1360e63718359d993a320e` |
| unchanged fixture generator | `732ca6ff358590edd856ba68bcb6cefb612246da9d81b97aa08d12db786eabfe` |

The artifact-root `frame_manifest.json` must be byte-identical to the docs frame
manifest and therefore have the same `368e0150...4ba1` hash.

## Fifteen skeptical checks

1. Confirm branch/HEAD/upstream and that all S2A files remain uncommitted and
   unpushed. Confirm no tracked pre-S2A file changed.
2. Recompute every hash in the table. Any mismatch is blocking.
3. Run `verify_intent(...)` only and confirm same slot-0 seed, fixed 150/50,
   scan start 150, scan limit 4096, 900-second execution limit, one generation
   attempt, zero retry/replacement, and the distinct S2A root.
4. Confirm the quarantined predecessor root remains exactly 201 files /
   806,977 bytes / `2f15d7c9...d132` and was not completed or reused.
5. Confirm the S2A root contains exactly 202 files: 150 representative
   fixtures, 50 challenge fixtures, `challenge_scan.json`, and
   `frame_manifest.json`. Numbered fixture paths must be complete and unique.
6. Recompute the S2A root using `r02_d3_preflight._filesystem_tree`:
   202 files / 973,115 bytes /
   `65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29`.
7. Confirm docs/artifact manifest byte identity, seal reference identity, payload
   file count 201, and payload tree SHA-256
   `0abf13023136b787007f649d5b4b20c619e862effe8c6029a5bc6a9458e4dc50`.
8. Parse the frozen scan. Require source indexes 150 through 560 contiguous
   (411 records), ADMITTED=50, NOT_TRIGGERED=351,
   NO_POSITIVE_CANDIDATE_HEADROOM=10, admitted list equal to ADMITTED records,
   and first/last admitted indexes 152/560.
9. Confirm the exact admission rule, accepted seed, outcome-shopping=false,
   provider_calls=0, live_execution=false, and predecessor root reused=false.
10. Confirm frame counts and opportunity counts: representative 150 with 19
    triggered/eligible, challenge 50 with 50 triggered/eligible, total eligible
    69. This reproduces the frozen frame only; do not derive a provider budget.
11. Confirm source pins and inspect all new sources for provider/network/process,
    Codex exec, LIVE, alternate seed/count/root, retry, or replacement paths.
    Pre-generation focused gate was 61 passed.
12. Run the additive read-only verifier, not the generation script:
    `.venv\Scripts\python.exe scripts\r02_d4_s2a_sealed_replay_verify.py --repo-root C:\Users\User\Desktop\ai-hedge-fund-fresh`.
    Expected status is
    `PASS_S2A_PROVIDER_FREE_FRAME_REPRODUCED_ADDITIVE_VERIFIER`, with the same
    manifest/seal/tree hashes and 19/50/69 opportunity counts.
13. Review the verifier diagnostic. The pre-generation verifier failed before
    opening the artifact store because strict `model_validate(dict)` rejected
    the JSON list representation of a tuple. Confirm it performed zero
    regeneration and zero writes, remained byte-pinned, and the additive
    verifier changed only parsing to `model_validate_json(bytes)`.
14. Recompute all ten predecessor child roots in the zero-call manifest. Require
    them unchanged. The additive protected root must be 3,687 files /
    51,050,083 bytes /
    `692ced9177f71cbe1af45a8f3ce06b7ec1c690fba87a8c7de254a1dfc834f891`.
15. Confirm D3 post-hoc remains byte SHA-256
    `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
    with verdict `SUPPORTED`, and confirm provider/Codex exec/micro-pilot/LIVE,
    generation retry, replacement, commit, and push all remain zero.

## Verdict format

If every check reproduces, report:

`PASS_PROVIDER_FREE_S2A_FRAME_SEALED`

Then list the five docs hashes, S2A root tuple, scan tuple, 19/50/69 counts,
full-replay result, verifier-parser diagnostic disposition, unchanged
predecessor/D3 evidence, and zero-call accounting. If any check fails, report
`BLOCKING_FINDINGS` with the exact file, field, expected value, and observed
value.

## What a pass means

A pass accepts the provider-free S2A frame and scan only. The next phase would
be a separately authorized statistical freeze based on this sealed frame,
followed later by a numeric provider budget and a separate LIVE authorization.
No later phase is authorized by this handoff.
