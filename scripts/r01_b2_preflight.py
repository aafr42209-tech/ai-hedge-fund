"""Reproduce the R01 B2 zero-call Codex preflight captures."""

from __future__ import annotations

import argparse

from v2.research.overlay.codex_preflight import (
    SubprocessLocalCommandRunner,
    capture_zero_call_preflight,
    write_zero_call_preflight,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-executable", required=True)
    parser.add_argument("--output-directory", required=True)
    parser.add_argument("--expected-catalog-sha256", required=True)
    parser.add_argument("--expected-definition-sha256", required=True)
    args = parser.parse_args()

    summary, raw_artifacts = capture_zero_call_preflight(
        args.codex_executable,
        expected_catalog_sha256=args.expected_catalog_sha256,
        expected_definition_sha256=args.expected_definition_sha256,
        runner=SubprocessLocalCommandRunner(),
    )
    written = write_zero_call_preflight(args.output_directory, summary, raw_artifacts)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
