# R03 N1 reconciliation raw rerun — independent review handoff

## 1. Requested disposition

`INDEPENDENT_RECONCILIATION_RERUN_RESULT_REVIEW_APPROVED`

The approved contract set was committed and pushed as `e910991` before the
rerun. The subsequent raw rerun completed once under
`READ_ONLY_DATA_CHECK_RECONCILIATION_RERUN_AUTHORIZED`. This handoff does not
authorize another raw traversal, a normative retention reseal, or a commit or
push of the new result artifacts.

The first independent result review reproduced the raw result but returned
`CHANGES_REQUESTED` because the verifier did not bind the attestation's semantic
claims back to the result. The verifier now independently recomputes those
claims, and 11 re-signed semantic-tamper cases fail closed. Independent
re-review returned `APPROVED`; no result value was resealed.

One non-blocking LOW remains: `execution_commit` is self-hash sealed and was
independently matched to the current full HEAD, but the verifier does not
separately assert that field after a re-signing mutation.

## 2. Exact execution pins

| Pin | Value |
|---|---|
| Reconciliation permit | `b33e735eeb848079a2acabeac8ccef6b9b45da1d090807934131d6138f00b5de` |
| Base permit | `a6d32b93c9351b05211f43d9dabbac1cf78ca915ba2022d30b0bcb222d8db718` |
| Root identity | `6d91b6f6cf116cc868ebb532a729ad78d95e52521be3d2e8cbc593ef88559f84` |
| Calendar | `2514 / c2fba202f2efbe462a44ac13ac6e99a235c0fc18851d894cc2b5f4ab5c30b34c` |
| Early closes | `21 / d796bb76e4a2408244739e271260c20a02f20ff93db75bd4ee8e8166e1e79a47` |
| Article/session caps | `32768 / 131072` |

Preflight passed every permit, runtime behavior, root, calendar, early-close,
cap, ordering, and truncation pin before the single raw callback.

## 3. Artifact identities

| Artifact | Identity |
|---|---|
| Permit filesystem SHA-256 | `acbf54985edb7a1d98a22c93e4d114d7479e91207c7d0a9c6a891a41ba9b098d` |
| Runner filesystem SHA-256 | `19ad8b083a7e3a3ba50c39676b032e302640f20f65fbe94839d1a84962487a52` |
| Result canonical SHA-256 | `6046eab6643d31254c398ad1e4183931130acf0ca076cd5aa93b1a69902265eb` |
| Result filesystem SHA-256 | `a6c943788f002bd630c45371d406c79dba04003d222d17d8881bc6a74f1b1df0` |
| Paired evidence SHA-256 | `4669d70649ce94178194e85eb80a40fe4b49145cfb6835d1ba1f2083714f7bdf` |
| Pair multiset SHA-256 | `86222a8b21e92b3f2ce9a43488ced629874af3c48946023b08c5e388a03b4b73` |
| Prior driver filesystem SHA-256 | `f64ba0a137151127d5956fd90713a31708da64e15e5dbd101bfee37c162d31af` |
| Event index filesystem SHA-256 | `89bef1bc58bd2e9558f7af923b38c78c5a46135e71465bc83138042c8e95e060` |
| Calendar input filesystem SHA-256 | `9ae1625de0fb91e0c6abaab18b0637a0798abc035368622e5f1aba84e0dec011` |
| Attestation canonical SHA-256 | `ccac84f3d635b8e9342465a4c0f3a7fca42fb084f2a835d2ebb77d30986bc866` |
| Attestation filesystem SHA-256 | `7a3af9b940ac1b16858e768f83b0b5635ff71b002b1f3c0a7b6b71e13257f750` |
| Verifier filesystem SHA-256 | `89f7b9715e5c3c272720e56e466312a248dbd9f0bfafc1e59cf81b8b110d5b42` |
| Verifier tests filesystem SHA-256 | `68690a3fca9fef5ac99355402db7e5a21bbff2e9d7aa51f14858c655ac912fd5` |

The 664 pairs contain numeric counts and byte totals only. They emit no raw
text or direct identifier, while retaining the approved numeric
quasi-identifier disclosure.

## 4. Resolved findings

The preserve-whitespace reconciliation run matches the sealed values exactly
for five of the six aggregate fields:

| Field | Sealed | Reconciliation | Result |
|---|---:|---:|---|
| Full frames total | 151820 | 151820 | exact |
| Full frames retained | 150394 | 150394 | exact |
| Article appearances total | 702489 | 702489 | exact |
| Article appearances retained | 695948 | 695948 | exact |
| Input text bytes | 1585976846 | 1585976846 | exact |

This closes the 467,586-byte denominator blocker and the +5 retained-appearance
blocker. The first v2 rerun differed because its local adapter stripped text and
used the positive-byte appearance predicate; the reviewed reconciliation
contract now reproduces the sealed denominator and appearance count.

## 5. Remaining retained-byte blocker

The sixth field remains unresolved:

| Path | Retained text bytes | Display |
|---|---:|---:|
| Sealed | 1435742878 | 90.53% |
| Reconciliation full accumulation | 1515387041 | 95.55% |
| Triggering-article-only reconstruction | 1430112659 | 90.17% |

All 664 session-cap-affected frames changed in the paired comparison.
Reconciliation contributes `87,025,931` bytes in those frames. A
triggering-article-only reconstruction contributes `1,751,549`, but the sealed
numerator implies `7,381,768`. The remaining distance from triggering-only to
the sealed implication is `5,630,219` bytes.

Therefore the earlier whole-frame/trigger-only hypothesis is directionally
correct but incomplete. Neither the reviewed full accumulation nor the explicit
triggering-only reconstruction reproduces the sealed numerator. No value is
resealed.

## 6. Boundary counters

- completed raw-source scans: 1;
- aborted partial scans: 0;
- raw copies, frame/fixture materializations: 0;
- fits, gates, OOS, inference, model downloads: 0;
- provider/network calls and dependency changes: 0;
- commits and pushes during the rerun: 0.

The tracked worktree was clean and synchronized at `e910991` when execution
started. The attestation and verifier created after completion are intentionally
uncommitted pending this review.

## 7. Review commands

No raw traversal is needed for review:

```text
.venv/Scripts/python.exe scripts/r03_news_reasoning_reconciliation_rerun_verify.py
.venv/Scripts/python.exe -m pytest -q tests/test_r03_reconciliation_rerun_verify.py
.venv/Scripts/python.exe -m pytest -q tests/test_r03_reconciliation.py
.venv/Scripts/python.exe -m black --check scripts/r03_news_reasoning_reconciliation_rerun_verify.py
.venv/Scripts/python.exe -m isort --check-only scripts/r03_news_reasoning_reconciliation_rerun_verify.py
.venv/Scripts/python.exe -m flake8 --max-line-length=420 scripts/r03_news_reasoning_reconciliation_rerun_verify.py
git diff --check
```

Expected verifier prefix:

`PASS_R03_N1_RECONCILIATION_RERUN`

## 8. Review questions

1. Do the result, paired evidence, and attestation self-hashes reproduce?
2. Do the permit and runtime pins match the approved reconciliation contract?
3. Does the five-of-six exact match close the denominator and +5 blockers?
4. Is the retained-byte numerator correctly left unresolved and unresealed?
5. Does the paired decomposition support rejecting the simple
   triggering-article-only hypothesis as incomplete?
6. Should a later code-only investigation add aggregate header/summary/content
   component counters before any separately authorized additional raw scan?
