# R03 N1 retained-byte numerator — targeted scan authorization handoff

## 1. Current disposition

`TARGETED_NUMERATOR_SCAN_DESIGN_READY_NO_RERUN_AUTHORITY`

The preceding reconciliation rerun result received independent approval. Its
retention disposition remains `UNRESOLVED_NO_VALUE_RESEALED`: neither 90.53%,
95.55%, nor another value is normative.

This handoff records a code-only targeted accounting design and an exact local
permit. It does not authorize or report another raw traversal. No retention
value is changed, no frame or fixture is materialized, and no commit or push is
authorized by this document.

## 2. Question isolated by the scan

Five of the six historical retention fields reproduced exactly. The only open
field is retained text bytes:

| Quantity | Bytes |
|---|---:|
| Historical sealed numerator | 1,435,742,878 |
| Accepted reconciliation numerator | 1,515,387,041 |
| Signed gap | +79,644,163 |
| Reconciliation unaffected-frame bytes | 1,428,361,110 |
| Historical-seal-implied affected-frame bytes | 7,381,768 |
| Reconciliation affected-frame bytes | 87,025,931 |

The existing aggregate-only result cannot attribute this gap among the 664
session-cap-affected frames. One new traversal is therefore the minimum raw
operation capable of producing the missing accounting evidence.

## 3. Output contract

The proposed result contains one identifier-free numeric ledger per affected
frame, canonically sorted as a multiset. Each ledger partitions retained bytes
into:

- preceding headline, summary, and content bytes;
- trigger headline, summary, and retained content-prefix bytes;
- included, omitted-after-trigger, and included-zero-byte appearance counts;
- source and reconciliation frame totals.

The result emits no ticker, date, article identifier, path, source locator, or
raw text. Numeric byte combinations can still be quasi-identifiers to a corpus
holder; the schema states that limitation. `reject_raw_text_emission` is applied
before output sealing.

The runner also computes five explicit affected-frame accumulation candidates:
trigger only; preceding headline plus trigger; preceding summary plus trigger;
preceding headline and summary plus trigger; and all retained headline and
summary bytes. It does not choose a normative candidate or reseal retention.

## 4. Exact authorization pins

| Pin | Value |
|---|---|
| Required authority | `READ_ONLY_R03_N1_NUMERATOR_TARGETED_SCAN_AUTHORIZED` |
| Targeted permit canonical SHA-256 | `93bbaaf0cb90e7c5adb59c6d730101ee88e5532b380d45eaf48cc2d1fea6a4b8` |
| Targeted permit filesystem SHA-256 | `d9a2ca4e7832daadd8b30cd11be242d98bf16cf43d4c134c19aad06997f57eca` |
| Base execution commit | `e9109913a2cf198e63f5fbd116abc91c58fc6ee2` |
| Raw-root identity | `6d91b6f6cf116cc868ebb532a729ad78d95e52521be3d2e8cbc593ef88559f84` |
| Calendar | `2514 / c2fba202f2efbe462a44ac13ac6e99a235c0fc18851d894cc2b5f4ab5c30b34c` |
| Early-close sessions | `21 / d796bb76e4a2408244739e271260c20a02f20ff93db75bd4ee8e8166e1e79a47` |
| Accepted reconciliation result | `6046eab6643d31254c398ad1e4183931130acf0ca076cd5aa93b1a69902265eb` |
| Accepted paired evidence | `4669d70649ce94178194e85eb80a40fe4b49145cfb6835d1ba1f2083714f7bdf` |
| Targeted module filesystem SHA-256 | `43ada011967a532585ba0ea456a539515501c43c6b9b57d8111b0e24fd8a7efc` |
| Targeted runner filesystem SHA-256 | `93e4251418182ba7810d2c6d27cbc037a557ad659a2b8512503d041a61d6fff4` |
| Base runner filesystem SHA-256 | `19ad8b083a7e3a3ba50c39676b032e302640f20f65fbe94839d1a84962487a52` |
| Prior driver filesystem SHA-256 | `f64ba0a137151127d5956fd90713a31708da64e15e5dbd101bfee37c162d31af` |
| Event index filesystem SHA-256 | `89bef1bc58bd2e9558f7af923b38c78c5a46135e71465bc83138042c8e95e060` |
| Calendar input filesystem SHA-256 | `9ae1625de0fb91e0c6abaab18b0637a0798abc035368622e5f1aba84e0dec011` |
| Ledger schema SHA-256 | `5cab84bd1e26bd2ffb08fe7f5acd9ff7f374bb9c3a76d0e2f965aad631067de6` |
| Ledger implementation SHA-256 | `a0c2a9e05fed829b5bf6b6ee9df2796a9e26aa3429d75a31934b6e29d4ff281b` |
| Expected affected frames | `664` |

The CLI requires the permit hash as a separate argument. The permit also pins
the runner, imported drivers, inputs, and execution commit, and the runner
recomputes those filesystem hashes before its only raw-source callback.

## 5. Verification completed without raw traversal

- Targeted contract plus reconciliation/verifier focused tests: `63 passed`;
  broader R03 verification set: `88 passed`.
- Black and isort checks: pass.
- Exact preflight: pass with the permit, root, calendar, early-close, and
  accepted-result pins above.
- Raw-source callbacks reached during this design session: `0`.
- Staging, commit, and push during this design session: `0`.

The preflight command was:

```text
C:/Users/User/Desktop/FinGPT/.venv/Scripts/python.exe .research_artifacts/r03-news-reasoning/run_numerator_targeted_scan_v1.py --preflight --expected-permit-sha256 93bbaaf0cb90e7c5adb59c6d730101ee88e5532b380d45eaf48cc2d1fea6a4b8
```

## 6. Separate authority required

Actual execution requires an explicit approval naming both the authority and
the exact permit hash:

```text
READ_ONLY_R03_N1_NUMERATOR_TARGETED_SCAN_AUTHORIZED
permit_sha256=93bbaaf0cb90e7c5adb59c6d730101ee88e5532b380d45eaf48cc2d1fea6a4b8
```

If granted, scope is one read-only raw traversal and one aggregate-only result
file. It excludes a second scan, retention reseal, frame/fixture creation,
fitting, G1-G3, OOS, inference/model download, provider/network use, dependency
change, commit, and push. Any pin drift fails closed before traversal.
