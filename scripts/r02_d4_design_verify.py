"""Read-only verifier for the R02 D4 provider-free design drafts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from v2.research.overlay.r02_d4_design import (
    build_power_report,
    select_parsimony_candidate,
)


class R02D4VerificationError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4VerificationError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_zero_boundary(name: str, value: dict[str, Any]) -> None:
    expected = {
        "provider_calls": 0,
        "frame_generation": False,
        "live_execution": False,
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise R02D4VerificationError(f"ZERO_BOUNDARY_MISMATCH:{name}:{key}")


def _verify_power(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "docs" / "r02-d4-prospective-power-sizing.json"
    observed = _read_json(path)
    _assert_zero_boundary(path.name, observed)
    source = repo_root / str(observed["calculation_source"])
    if _sha256_file(source) != observed.get("calculation_source_sha256"):
        raise R02D4VerificationError("POWER_SOURCE_SHA256_MISMATCH")
    computed = build_power_report()
    if observed.get("simulation_seed_sha256") != computed["simulation_seed_sha256"]:
        raise R02D4VerificationError("POWER_SIMULATION_SEED_MISMATCH")
    if observed.get("targets") != computed["targets"]:
        raise R02D4VerificationError("POWER_TARGETS_MISMATCH")
    if observed.get("opportunity_grid") != computed["opportunity_grid"]:
        raise R02D4VerificationError("POWER_OPPORTUNITY_GRID_MISMATCH")
    fields = (
        "scenario_id",
        "total_n",
        "distribution",
        "winsor_fraction_ppm",
        "supported_trials",
        "estimated_power_ppm",
        "wilson_lower_power_ppm",
        "wilson_upper_power_ppm",
        "sizing_gate",
    )
    observed_scenarios = observed.get("scenario_results")
    computed_scenarios = computed.get("scenario_results")
    if not isinstance(observed_scenarios, list) or not isinstance(computed_scenarios, list):
        raise R02D4VerificationError("POWER_SCENARIOS_MISSING")
    if len(observed_scenarios) != len(computed_scenarios):
        raise R02D4VerificationError("POWER_SCENARIO_COUNT_MISMATCH")
    for observed_item, computed_item in zip(
        observed_scenarios, computed_scenarios, strict=True
    ):
        for field in fields:
            if observed_item.get(field) != computed_item.get(field):
                raise R02D4VerificationError(
                    f"POWER_SCENARIO_MISMATCH:{observed_item.get('scenario_id')}:{field}"
                )
        passes = bool(
            computed_item["passes_power_target"]
            and computed_item["passes_wilson_lower_target"]
        )
        if observed_item.get("passes_targets") != passes:
            raise R02D4VerificationError(
                f"POWER_SCENARIO_PASS_MISMATCH:{observed_item.get('scenario_id')}"
            )
    if observed.get("sizing_gate_pass_by_n") != computed["sizing_gate_pass_by_n"]:
        raise R02D4VerificationError("POWER_SIZING_GATE_MISMATCH")
    if observed.get("draft_selected_n") != computed["draft_selected_n"]:
        raise R02D4VerificationError("POWER_SELECTED_N_MISMATCH")
    return {
        "scenario_count": len(observed_scenarios),
        "draft_selected_n": observed["draft_selected_n"],
        "draft_selected_m_min": observed["draft_selected_m_min"],
        "simulation_seed_sha256": observed["simulation_seed_sha256"],
    }


def _verify_vectors(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "docs" / "r02-d4-parsimony-test-vectors.json"
    observed = _read_json(path)
    _assert_zero_boundary(path.name, observed)
    vectors = observed.get("vectors")
    if not isinstance(vectors, list) or len(vectors) != 8:
        raise R02D4VerificationError("PARSIMONY_VECTOR_COUNT_MISMATCH")
    for vector in vectors:
        raw = vector.get("candidates")
        if not isinstance(raw, list):
            raise R02D4VerificationError("PARSIMONY_VECTOR_CANDIDATES_MISSING")
        records = [
            {
                "canonical_candidate_id": item["id"],
                "candidate": {"decisions": item["decisions"]},
            }
            for item in raw
        ]
        selected = select_parsimony_candidate(records)
        if selected.canonical_candidate_id != vector.get("expected"):
            raise R02D4VerificationError(
                f"PARSIMONY_VECTOR_MISMATCH:{vector.get('vector_id')}"
            )
    return {"positive_vector_count": len(vectors), "all_positive_vectors_passed": True}


def verify_design(repo_root: Path) -> dict[str, Any]:
    design = _read_json(repo_root / "docs" / "r02-d4-replication-design.json")
    seed = _read_json(repo_root / "docs" / "r02-d4-seed-contract.json")
    _assert_zero_boundary("r02-d4-replication-design.json", design)
    _assert_zero_boundary("r02-d4-seed-contract.json", seed)
    if design.get("frame_scan") is not False or design.get("micro_pilot") is not False:
        raise R02D4VerificationError("DESIGN_BOUNDARY_MISMATCH")
    if seed.get("frame_seed_created") is not False:
        raise R02D4VerificationError("FRAME_SEED_MUST_REMAIN_UNRESOLVED")
    if seed.get("resolved_frame_seed_sha256") is not None:
        raise R02D4VerificationError("FRAME_SEED_DIGEST_MUST_BE_NULL")
    posthoc = repo_root / "docs" / "r02-d3-successor-provider-free-posthoc.json"
    expected_posthoc = design["sealed_r02_d3"]["provider_free_posthoc_sha256"]
    if _sha256_file(posthoc) != expected_posthoc:
        raise R02D4VerificationError("SEALED_POSTHOC_SHA256_MISMATCH")
    power = _verify_power(repo_root)
    vectors = _verify_vectors(repo_root)
    return {
        "schema_version": "r02-d4-provider-free-design-verification-v1",
        "status": "PASS_PROVIDER_FREE_DRAFT_REPRODUCED",
        "provider_calls": 0,
        "frame_generation": False,
        "frame_scan": False,
        "live_execution": False,
        "frame_seed_created": False,
        "sealed_r02_d3_verdict_unchanged": "SUPPORTED",
        "power": power,
        "parsimony": vectors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = verify_design(args.repo_root.resolve())
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
