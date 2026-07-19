"""Generate or verify the provider-free R02 D4 LIVE post-hoc artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v2.research.overlay.canonical import canonical_json_bytes
from v2.research.overlay.r02_d4_posthoc_analysis import build_report, render_markdown

REPORT_PATH = ROOT / "docs/r02-d4-live-posthoc.json"
MARKDOWN_PATH = ROOT / "docs/r02-d4-live-posthoc.md"


def _write_new_or_equal(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise RuntimeError(f"existing artifact drift: {path}")
        return
    path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_report(ROOT)
    report_bytes = canonical_json_bytes(report)
    markdown_bytes = render_markdown(report).encode("utf-8")
    if args.write:
        _write_new_or_equal(REPORT_PATH, report_bytes)
        _write_new_or_equal(MARKDOWN_PATH, markdown_bytes)
    else:
        if REPORT_PATH.read_bytes() != report_bytes:
            raise RuntimeError("post-hoc JSON does not reproduce")
        if MARKDOWN_PATH.read_bytes() != markdown_bytes:
            raise RuntimeError("post-hoc Markdown does not reproduce")
    print("PASS_R02_D4_LIVE_POSTHOC_PROVIDER_FREE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
