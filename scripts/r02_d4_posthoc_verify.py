"""Independent provider-free verifier for the R02 D4 post-hoc report."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v2.research.overlay.canonical import canonical_json_bytes
from v2.research.overlay.r02_d4_posthoc_analysis import build_report

REPORT_PATH = ROOT / "docs/r02-d4-live-posthoc.json"
REPORT_SHA256 = "623b8888a90af34bf7f0be20cf45ff19691e8c1545de76d00534102643b71042"


def _weighted_mean(rep: list[int], challenge: list[int]) -> int:
    with localcontext() as context:
        context.prec = 50
        value = (
            Decimal(3) * Decimal(sum(rep)) / Decimal(len(rep))
            + Decimal(sum(challenge)) / Decimal(len(challenge))
        ) / Decimal(4)
        return int(value.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def main() -> int:
    report_bytes = REPORT_PATH.read_bytes()
    assert hashlib.sha256(report_bytes).hexdigest() == REPORT_SHA256
    report = json.loads(report_bytes)
    assert canonical_json_bytes(report) == report_bytes
    assert canonical_json_bytes(build_report(ROOT)) == report_bytes
    assert report["status"] == "PROVIDER_FREE_POSTHOC_COMPLETE_INDEPENDENT_REVIEW_ACCEPTED"

    frame = json.loads(
        (ROOT / ".research_artifacts/r02-d4-s2a-frame-0716a1b9c13a/frame_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    outcomes = {}
    for path in sorted(
        (ROOT / ".research_artifacts/r02-d4-s6-r02-d4-s8-20260719/payloads").glob(
            "*-attempt_outcome.json"
        )
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        outcomes[value["fixture_id"]] = value
    assert len(outcomes) == 69
    assert all(value["status"] == "SETTLED_ACCEPTED" for value in outcomes.values())
    assert all(not value["baseline_fallback"] for value in outcomes.values())

    rep: list[int] = []
    challenge: list[int] = []
    for case in sorted(frame["cases"], key=lambda value: value["frame_ordinal"]):
        outcome = outcomes.get(case["fixture_id"])
        delta = 0 if outcome is None else int(outcome["paired_utility_delta_e12"])
        (rep if case["stratum"] == "REPRESENTATIVE" else challenge).append(delta)
    assert (len(rep), len(challenge)) == (150, 50)
    assert _weighted_mean(rep, challenge) == 85_727_257
    assert report["primary_replication"]["theta_e12"] == 85_727_257
    assert report["primary_replication"]["label"] == "REPLICATION_SUPPORTED_FRAGILE"
    assert report["primary_replication"]["lower_e12"] == 51_557_051
    assert report["primary_replication"]["upper_e12"] == 119_471_784
    assert report["deterministic_parsimony"]["exact_vector_equal_to_primary"] is True
    assert report["deterministic_parsimony"]["label"] == "PARSIMONY_POLICY_SUPPORTED"
    assert report["incremental_llm"]["label"] == "NOT_IDENTIFIED_REDUNDANT_SELECTOR"
    assert report["incremental_llm"]["discordant_total"] == 0
    assert report["agreement"]["agreement_count"] == 69
    assert report["execution"]["observed_total_tokens"]["sum"] == 822_031
    assert report["execution"]["transport"]["duration_ms"]["sum"] == 398_374
    assert report["analysis_provider_calls"] == 0
    assert report["new_live_runs"] == 0
    print("PASS_R02_D4_LIVE_POSTHOC_INDEPENDENT_PROVIDER_FREE_VERIFY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
