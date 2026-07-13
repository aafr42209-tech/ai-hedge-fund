"""Development-only machine and human-readable reports."""

from __future__ import annotations

from typing import Any

WARNING = "DEVELOPMENT_ONLY — NOT SEALED — NO INVESTMENT CLAIM"


def build_report(cases: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    valid = sum(int(case["raw_valid"]) for case in cases)
    fallbacks = sum(int(case["fell_back"]) for case in cases)
    report = {
        "schema_version": "r01-development-report-v1",
        "status": WARNING,
        "case_count": len(cases),
        "raw_valid_count": valid,
        "fallback_count": fallbacks,
        "cases": cases,
    }
    lines = [
        "# R01 Development Report",
        "",
        f"**{WARNING}**",
        "",
        f"- Acquisitions: `{len(cases)}`",
        f"- Raw-valid: `{valid}`",
        f"- Hold fallbacks: `{fallbacks}`",
        "",
        "| Case | Regime | LLM utility_e12 | Oracle utility_e12 | Raw valid |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for case in cases:
        lines.append(f"| {case['case_id']} | {case['regime']} | {case['llm_utility_e12']} | " f"{case['oracle_utility_e12']} | {str(case['raw_valid']).lower()} |")
    lines.append("")
    return report, "\n".join(lines)
