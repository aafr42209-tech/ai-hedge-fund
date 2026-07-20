# R03 data-check amendment — independent review handoff

## 1. Authority and non-authority

Implemented under `R03_DATA_CHECK_AMENDMENT_CODE_AUTHORIZED`.

This handoff grants no `READ_ONLY_DATA_CHECK_RERUN_AUTHORIZED` authority. No
raw-source traversal, copy, frame/fixture materialization, fitting, research
gate, OOS access, inference, provider/network call, dependency change, commit,
or push occurred. A production rerun remains impossible without a separately
issued v2 permit that pins the root, permit, 21-session early-close identity,
and 2,514-session calendar identity.

## 2. Exact review set

| Artifact | Filesystem SHA-256 |
|---|---|
| `v2/research/news_reasoning/r03_source.py` | `a470473d2ddfe67e37a7ad109ec727ae3c5679f4df650ca1b364a59dad230c68` |
| `tests/test_r03_source.py` | `fa524178a7860534517227a6810259e278756372b9f4a04fe47aadd8543529b9` |
| `scripts/r03_news_reasoning_data_check_verify.py` | `08d5347a301dfdc89417e26f8bea0c9549a3f191acce4596b701ecd1f844d924` |
| `tests/test_r03_data_check_verify.py` | `d8646d4f007546e8c8613fc8fcfb0dfcf1d5d49ad9665bfa20f64fc23de38e6e` |
| `docs/r03-news-reasoning-charter-draft.md` | `a96766f5b15fdecc839c07d3f66a1cc78e40d778050a3eae2623d77ffdb90329` |
| `docs/r03-news-reasoning-provider-free-preregistration-draft.md` | `741fc091e689ac4a848cd2ea43fc99f26295b632831d33426028769b31bde211` |
| `docs/r03-news-reasoning-data-check-amendment-lineage.json` | `8c514ea72f35fd0a93d8d74a6afdfa8547b81ff5fae26d9a7e75831ec0ce38d4` |
| `docs/r03-news-reasoning-data-check-amendment-evidence.json` | `905eecbdd2838e05e0d5b71a7353ad43c447f5186d7ea2f833831a7dcf672565` |
| `docs/r03-news-reasoning-data-check-amendment-zero-call-manifest.json` | `3205bcfd43ffbb02ddccb3a51b4747efa6ab0a82ca3a3481637a936b2b91adc2` |

Canonical self-hashes:

- lineage: `eec62df18f1e5cd4d896274c54b0734fd32d34d92fd6dbefbecf2a50f404b881`
- evidence: `5d0b57d8230e929db49e1c03dfbb97cfab7548750265759a37e97b3f4b931eda`

This handoff remains outside its own pin set. Report its final filesystem hash
as the review-session anchor.

## 3. Protected historical artifacts

The following were preserved:

- P5 coverage audit: `6275292839b9446825bc8d05cc334a82dc7fe865067501895fd0f2c15c821984`
- accepted implementation plan and original CODE_ONLY evidence/manifest;
- pre-existing uncommitted implementation handoff §12, current filesystem
  SHA-256 `3380f216dc890bafc229beb82ea9e55a7c6798062a2f2fe88fbdf8017d566044`.

The new lineage supersedes only the P5 selected-payload retention expectations;
it does not rewrite the historical artifact.

## 4. Contract amendment

`R03PublicRetentionV2` and `public_retention_v2` use separate frame and
article-appearance streams. Exact integer numerators and denominators are
first-class identity fields. The three display values use integer-only
round-half-even to two places; floats are rejected from input byte counts. The
legacy v1 API remains unchanged and is explicitly historical.

Sealed N1 values:

| Level | Exact fraction | Display |
|---|---:|---:|
| Full frames | `150394/151820` | `99.06%` |
| Article appearances | `695948/702489` | `99.07%` |
| Text bytes | `1435742878/1585976846` | `90.53%` |

The 32,768/131,072-byte caps and newest-first,
omit-after-session-truncation semantics remain normative. The old 97.03% is
recorded as an article-cap-only calculation error.

## 5. Fail-closed verifier boundary

`R03DataCheckPermitV2` pins authorization, root/permit hashes, plan and
implementation commits, early-close/calendar counts and hashes, caps, ordering,
truncation semantics, and rounding. The separately supplied expected permit
hash is checked before the permit self-hash and root identity. All validation
completes before the injected corpus adapter receives the root path.

The committed CLI validates aggregate-only amendment artifacts. The reusable
authorized entry point can execute only when a future caller provides both a
complete production permit and adapter. Safe output exposes aggregate counts,
exact fractions/canonical decimals, and hashes; semantic literals are emitted
only as SHA-256 identities.

## 6. Verification results

- R03 focused: 72 passed.
- Sealed R02 API command (the eight exact overlay test files recorded in the
  evidence): 27 collected and 27 passed. The reviewer's separately scoped
  non-R03 check reported 28 passed; it is not the sealed R02 API command and
  does not replace its count.
- Full R02 overlay: 433 passed in 475.22 seconds.
- Black, isort, flake8 (`--max-line-length=420`): exit 0.
- Amendment verifier: `PASS_R03_DATA_CHECK_AMENDMENT`.
- `git diff --check`: exit 0.
- Provider/network/subprocess import hits in amended source/verifier: zero.
- Boundary counters: all zero.

## 7. Required reviewer questions

1. Are frame and article-appearance denominators impossible to conflate in v2?
2. Is round-half-even implemented with exact integer arithmetic, including both
   tie directions?
3. Does every permit/root/commit/calendar/early-close/cap/order/omit/rounding
   perturbation fail before the callback?
4. Can aggregate output expose any source text, article ID, or reconstructable
   per-article payload?
5. Do lineage/evidence/manifest self- and cross-pins close correctly?
6. Is the original P5 audit byte-for-byte unchanged?
7. Are raw rerun, frames, fitting, gates, OOS, inference, provider/network,
   dependencies, commit, and push still unauthorized?
8. Is organizational independence still represented as false?

## 8. Review disposition

Independent technical review completed on 2026-07-20 against review-session
handoff SHA-256
`a9f1a204f8d5cd6da0cbab82e87d4d102c4da870374dc8d811e3d6efe39e6264`.

The reviewer independently reproduced the lineage and evidence canonical
hashes, manifest filesystem hash, verifier PASS marker with all zero counters,
72 focused R03 tests, 433 full R02 overlay tests, style checks, `git diff
--check`, and the absence of staging, commit, or push actions. The reviewer
confirmed the permit validation order, runtime revalidation of copied Pydantic
models, separate retention denominators, integer-only half-even arithmetic,
aggregate-only output boundary, and immutable P5 audit identity. No open code,
seal, or test finding remains.

Review notes disposed:

1. The reviewed pre-record handoff anchor is the `a9f1a204...` value above; the
   earlier `00ea596c...` report predated the pending-review handoff edit and is
   superseded.
2. The sealed eight-file R02 API command remains exactly 27/27. The separately
   reported 28-test non-R03 scope is recorded in §6 without changing the sealed
   evidence count.

Disposition: **INDEPENDENT_TECHNICAL_REVIEW_ACCEPTED**. Organizational
independence remains recorded as false. `READ_ONLY_DATA_CHECK_RERUN_AUTHORIZED`
is not granted, and no raw rerun or later research-ladder state is authorized.
