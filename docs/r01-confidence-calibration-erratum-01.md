# R01 confidence calibration erratum 01

Status: **APPEND-ONLY POST-SEAL CLARIFICATION**

This erratum does not modify the sealed calibration report, machine results, or
R01 closeout manifest. It clarifies only the interval convention used by the
descriptive confidence-bin table.

Bound source identities:

- sealed calibration report SHA-256:
  `16188f2dcd09fa905a0502f33ad6dc8953b21268ec2e32c4d594488e5e64586b`;
- sealed calibration JSON SHA-256:
  `41904983538677f4b1bc33c1c467dd7a0689fa9e8470de745ec1a82b4f728df1`;
- sealed closeout manifest SHA-256:
  `a9bb04131d9214a17b99a6423900e3b83f1a7345e4bf63c3ca760553654b3ada`.

## Clarification

Pair-collapsed confidence values can be half-integers because each value is the
arithmetic mean of replicate 0 and replicate 1. Bins are half-open intervals:

```text
[0, 50), [50, 60), [60, 70), [70, 80), [80, 90), [90, 101)
```

Therefore a pair mean of `89.5` belongs to the displayed `80–89` bin. The final
interval includes the maximum valid raw confidence of 100.

This convention reproduces all published bin counts and does not change the
`NO_THRESHOLD_JUSTIFIED` conclusion, any R01 label, or any sealed byte.
