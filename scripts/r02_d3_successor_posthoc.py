"""Generate or verify the provider-free R02 D3 successor post-hoc report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _write_new_or_equal(
    path: Path,
    payload: bytes,
    *,
    verify_existing: bool,
    refresh_existing: bool,
) -> None:
    if verify_existing and refresh_existing:
        raise ValueError("verify-existing and refresh-existing are mutually exclusive")
    if verify_existing:
        if not path.is_file() or path.read_bytes() != payload:
            raise ValueError("existing post-hoc report differs from deterministic regeneration")
        return
    if path.exists():
        if path.read_bytes() == payload:
            return
        if not refresh_existing:
            raise ValueError(f"refusing to replace an existing post-hoc report: {path}")
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise ValueError(f"refusing to reuse stale post-hoc temporary: {temporary}")
    temporary.write_bytes(payload)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--verify-existing", action="store_true")
    parser.add_argument("--refresh-existing", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    if root not in output.parents:
        raise ValueError("post-hoc output must be inside the repository")
    sys.path.insert(0, str(root))

    from v2.research.overlay.canonical import canonical_json_bytes
    from v2.research.overlay.r02_d3_posthoc_analysis import build_posthoc_report

    report = build_posthoc_report(root)
    payload = canonical_json_bytes(report)
    _write_new_or_equal(
        output,
        payload,
        verify_existing=args.verify_existing,
        refresh_existing=args.refresh_existing,
    )
    print(payload.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
