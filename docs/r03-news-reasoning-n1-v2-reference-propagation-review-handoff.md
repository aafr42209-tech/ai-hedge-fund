# R03 N1 V2 normative-reference propagation review handoff

Date: 2026-07-21  
Authority: `R03_N1_V2_NORMATIVE_REFERENCE_PROPAGATION_CODE_AUTHORIZED`  
Requested disposition: `INDEPENDENT_TECHNICAL_REVIEW_REQUESTED_NO_COMMIT_AUTHORITY`

## 1. Review claim

This code-only overlay propagates the independently approved V2 normative
retention value into the effective R03 charter and provider-free
preregistration reference surface without editing either sealed base document.

The effective selected-payload retention assertion is:

> 1,515,387,041 / 1,585,976,846 text bytes = 95.55%, using
> `ROUND_HALF_EVEN_2DP`.

Its precedence is `REPLACE_NOT_RECONCILE`. The historical 90.53% clause remains
present in each sealed base document for audit history; it is not an effective
normative value after composition with the corresponding amendment.

## 2. Base-document preservation

| Sealed base document | Filesystem SHA-256 | Result |
|---|---|---|
| `docs/r03-news-reasoning-charter-draft.md` | `a96766f5b15fdecc839c07d3f66a1cc78e40d778050a3eae2623d77ffdb90329` | byte-for-byte unchanged |
| `docs/r03-news-reasoning-provider-free-preregistration-draft.md` | `741fc091e689ac4a848cd2ea43fc99f26295b632831d33426028769b31bde211` | byte-for-byte unchanged |

The verifier also pins each exact superseded clause, requires it to remain
exactly once, and rejects a direct 95.55% edit in either base document.

## 3. New sealed artifacts

| Artifact | Canonical SHA-256 | Filesystem SHA-256 |
|---|---|---|
| effective retention contract | `7277792e284aaa90d8ca7bcef828102e28f587950f8a2ca7951b5dae93136704` | `d3081ef09d2f789671c75765374392ab01ea17333c594e40b5e1de2999313fa2` |
| reference-propagation lineage | `22d8da2c435b02778287ffefa7e98d6a04108f458ae4e8e0e0bafc1824c976ff` | `0e16c47b6e248f267ed78318af01fbcee40d94e60d76ad1e84f6996f055292cb` |
| reference-propagation evidence | `7db22408f9d5f2fe5d4df6df3d60b483f82d950b90caa919192f41b797f08a14` | `a51808092b125b9b0713fea414110ce400989e2d056fd837a942a34a8f06166a` |
| zero-call manifest | n/a | `654d696ae657ca6faed8bc47f72d9bcc80b5dc901c687e4650ceb5d578e0e0c9` |

Supporting filesystem pins:

| Artifact | Filesystem SHA-256 |
|---|---|
| charter V2 retention amendment | `71645e43aa1913cb8bc8ffb299e197e5434ca7edbf97fe6a7c341a757aab0464` |
| preregistration V2 retention amendment | `1ad550dfdd728c6fe83008616f6facb01ef36aac970bc4a82cddebcf48a00a37` |
| fail-closed verifier | `a2c42c343fc711d3de17d45e222282f8544f52f118c27828dbd468a246fbb3de` |
| adversarial test module | `b362c6be0cdfd12ea05e24a9b0f4a97130a27a304da05a39ce4fa41d5e921950` |

The contract pins the approved normative lineage
`8f3b3f0c25b3dd8b7c12af4232f6fb22b19db62e71b752d1555b9c114457a719`
and attestation
`44002b7a56e3c2432b4b4abf62088241d83c397d96c1a7e33828f03eeb3659f6`.

## 4. Fail-closed behavior

The new verifier first executes the approved V2 normative-reseal verifier. It
then checks the base documents, their exact historical clauses, both additive
amendments, the effective contract, lineage, evidence, manifest, and every
pinned filesystem artifact. JSON artifacts are subject to the existing raw-text
emission rejection boundary.

Adversarial tests cover direct base edits, duplicated historical clauses,
self-consistently re-signed contract and lineage tampering, amendment repointing,
evidence pin drift, manifest counter drift, and verifier clause-constant drift.

## 5. Reproduced gates

- `scripts/r03_news_reasoning_data_check_verify.py`: PASS
- `scripts/r03_news_reasoning_reconciliation_verify.py`: PASS
- `scripts/r03_news_reasoning_reconciliation_rerun_verify.py`: PASS
- `scripts/r03_news_reasoning_v2_normative_reseal_verify.py`: PASS
- `scripts/r03_news_reasoning_v2_reference_propagation_verify.py`: PASS
- fourteen `test_r03*.py` modules: `179 passed`
- focused propagation module: included above, `24 passed`
- black, isort, and flake8 with `--max-line-length=420`: PASS
- `git diff --check`: PASS for the unchanged tracked diff; all nine new paths
  remain untracked and unstaged

The historical `r03_news_reasoning_implementation_verify.py` is not a current
composition gate: it reports the already-known `r03_source.py` snapshot mismatch
after the later authorized and committed amendment/reconciliation changes. Its
sealed expected hash and the historical CODE_ONLY artifacts were not modified.

## 6. Boundary counters and non-authority

For this propagation scope:

- raw-source traversals: 0
- frame or fixture creation: 0
- fitting, G1-G3, OOS, inference, or model downloads: 0
- provider or network calls: 0
- dependency changes: 0
- staging, commits, or pushes: 0

This overlay does not authorize a raw rerun, reseal a new measured value, alter
byte budgets, or change any non-retention charter/preregistration clause.

## 7. Independent-review questions

1. Do the two additive amendments compose unambiguously with the unchanged base
   documents so that 95.55% is effective and 90.53% is historical only?
2. Do contract, lineage, evidence, and manifest form a reproducible fail-closed
   pin chain to the approved V2 normative reseal?
3. Do adversarial tests prevent self-consistent re-signing from changing the
   effective value, precedence, base identity, or zero-call boundary?
4. Is disposition
   `INDEPENDENT_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY` warranted?
