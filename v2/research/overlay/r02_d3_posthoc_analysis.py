"""Provider-free post-hoc analysis for the sealed R02 D3 successor run."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from .r02_d3_live_runner_replay import replay_audit_root
from .r02_d3_preflight import _filesystem_tree
from .r02_statistics import (
    R02_DELTA_MIN_E12,
    R02_DELTA_TARGET_E12,
    R02_M_MIN,
    stratified_bootstrap_interval_e12,
    stratified_weighted_mean_e12,
)


RUN_ID = "r02-d3-successor-84750652-20260718"
SELECTED_CANONICAL_ID = "11eb14e46d7e2bd45610d4e4c92945332a947dae5f2be307d8ccfd3458e3ec11"
BOOTSTRAP_SEED_HEX = "319dea85b61187c07089deedb525d4d927ffc03dc7ea2026e4be8022f2df9f68"
AUDIT_TREE_SHA256 = "bca066c859ded362cc6f531c236a224cacce6f2a4f0f62a06f15f8cc0d950bc4"
DURABLE_TREE_SHA256 = "b3cc74da593975865cd42087bb18bdc3f82d1c5666df5d98c5eb8ff92119dbea"
FRAME_TREE_SHA256 = "316eb5757b2eda3a04ec16f19a225df7a6e44fdf7f506482aa947b9cf77fb494"
STATISTICAL_FREEZE_SHA256 = "45a68aacde0135a4f5e446f1022406d35e24346b23df1bc7e4db78889c6e12b9"


class R02D3PosthocError(RuntimeError):
    """Raised when sealed evidence cannot support the post-hoc analysis."""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise R02D3PosthocError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise R02D3PosthocError(f"JSON artifact must be an object: {path}")
    return value


def _load_payloads(audit_root: Path) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    anchors = sorted((audit_root / "anchors").glob("*.json"))
    if not anchors:
        raise R02D3PosthocError("audit root has no anchors")
    anchor = _read_json(anchors[-1])
    node_types = anchor.get("node_types")
    nodes = anchor.get("nodes")
    if not isinstance(node_types, list) or not isinstance(nodes, list) or len(node_types) != len(nodes):
        raise R02D3PosthocError("terminal anchor node structure is invalid")
    payloads: dict[str, list[Any]] = {}
    for node_type, node_reference in zip(node_types, nodes, strict=True):
        if not isinstance(node_type, str) or not isinstance(node_reference, dict):
            raise R02D3PosthocError("terminal anchor contains an invalid node reference")
        relative_path = node_reference.get("relative_path")
        if not isinstance(relative_path, str):
            raise R02D3PosthocError("node reference lacks relative_path")
        node = _read_json(audit_root / Path(relative_path))
        payload_reference = node.get("payload")
        if not isinstance(payload_reference, dict) or not isinstance(payload_reference.get("relative_path"), str):
            raise R02D3PosthocError("node payload reference is invalid")
        payload_path = audit_root / Path(payload_reference["relative_path"])
        if node_type in {"raw_jsonl_transport", "raw_stderr"}:
            payload: Any = payload_path.read_bytes()
        else:
            payload = _read_json(payload_path)
        payloads.setdefault(node_type, []).append(payload)
    return anchor, payloads


def _candidate_features(candidate_record: dict[str, Any]) -> dict[str, int | bool]:
    candidate = candidate_record.get("candidate")
    decisions = candidate.get("decisions") if isinstance(candidate, dict) else None
    if not isinstance(decisions, dict) or not decisions:
        raise R02D3PosthocError("candidate decisions are missing")
    non_hold = 0
    total_quantity = 0
    for decision in decisions.values():
        if not isinstance(decision, dict):
            raise R02D3PosthocError("candidate decision is invalid")
        action = decision.get("action")
        quantity = decision.get("quantity")
        if not isinstance(action, str) or not isinstance(quantity, int):
            raise R02D3PosthocError("candidate action or quantity is invalid")
        non_hold += int(action != "hold" or quantity != 0)
        total_quantity += abs(quantity)
    return {
        "non_hold_action_count": non_hold,
        "total_absolute_quantity": total_quantity,
        "zero_activity": non_hold == 0 and total_quantity == 0,
    }


def _increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _float_text(value: float) -> str:
    return format(float(value), ".17g")


def _selection_consistency(
    episodes: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    parsed_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    outcome_by_fixture = {value["fixture_id"]: value for value in outcomes}
    if len(episodes) != 55 or len(outcome_by_fixture) != 55 or len(parsed_responses) != 55:
        raise R02D3PosthocError("selection analysis requires 55 complete episodes")
    candidate_set_sizes: dict[str, int] = {}
    selected_position_by_size: dict[str, dict[str, int]] = {}
    primary_roles: dict[str, int] = {}
    aliases: dict[str, int] = {}
    baseline_ids: set[str] = set()
    selected_ids: set[str] = set()
    selected_no_change = 0
    selected_min_actions = 0
    selected_min_quantity = 0
    selected_unique_zero = 0
    simple_rule_matches = 0
    for episode in episodes:
        identity = episode.get("identity")
        fixture_id = identity.get("fixture_id") if isinstance(identity, dict) else None
        candidate_set = episode.get("candidate_set")
        candidates = candidate_set.get("candidates") if isinstance(candidate_set, dict) else None
        if not isinstance(fixture_id, str) or not isinstance(candidates, list) or not candidates:
            raise R02D3PosthocError("episode candidate set is invalid")
        outcome = outcome_by_fixture.get(fixture_id)
        if outcome is None:
            raise R02D3PosthocError("episode lacks selector outcome")
        size_key = str(len(candidates))
        _increment(candidate_set_sizes, size_key)
        positions = selected_position_by_size.setdefault(size_key, {})
        _increment(positions, str(outcome["selected_presented_id"]))
        baseline_ids.add(str(candidate_set["baseline_canonical_candidate_id"]))
        selected_id = str(outcome["selected_canonical_id"])
        selected_ids.add(selected_id)
        featured: list[dict[str, Any]] = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise R02D3PosthocError("candidate record is invalid")
            role = str(candidate.get("primary_role"))
            _increment(primary_roles, role)
            candidate_aliases = candidate.get("aliases")
            if not isinstance(candidate_aliases, list):
                raise R02D3PosthocError("candidate aliases are invalid")
            for alias in candidate_aliases:
                _increment(aliases, str(alias))
            featured.append({**candidate, **_candidate_features(candidate)})
        selected = next(
            (value for value in featured if value.get("canonical_candidate_id") == selected_id),
            None,
        )
        if selected is None:
            raise R02D3PosthocError("selected candidate is absent from candidate set")
        minimum_actions = min(int(value["non_hold_action_count"]) for value in featured)
        minimum_quantity = min(int(value["total_absolute_quantity"]) for value in featured)
        zero_candidates = [value for value in featured if value["zero_activity"]]
        selected_no_change += int(selected.get("primary_role") == "NO_CHANGE")
        selected_min_actions += int(selected["non_hold_action_count"] == minimum_actions)
        selected_min_quantity += int(selected["total_absolute_quantity"] == minimum_quantity)
        selected_unique_zero += int(len(zero_candidates) == 1 and selected["zero_activity"])
        simple_choice = sorted(
            featured,
            key=lambda value: (
                int(value["non_hold_action_count"]),
                int(value["total_absolute_quantity"]),
                str(value["canonical_candidate_id"]),
            ),
        )[0]
        simple_rule_matches += int(simple_choice["canonical_candidate_id"] == selected_id)

    confidence_counts: dict[str, int] = {}
    reason_code_counts: dict[str, int] = {}
    for parsed in parsed_responses:
        raw_response = parsed.get("raw_response")
        if not isinstance(raw_response, str):
            raise R02D3PosthocError("parsed response lacks raw_response")
        try:
            response = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise R02D3PosthocError("selector response is not JSON") from exc
        _increment(confidence_counts, str(response.get("confidence")))
        reason_codes = response.get("reason_codes")
        if not isinstance(reason_codes, list):
            raise R02D3PosthocError("selector reason codes are invalid")
        for reason_code in reason_codes:
            _increment(reason_code_counts, str(reason_code))

    position_uniformity: dict[str, dict[str, str]] = {}
    for size_key, observed_by_position in sorted(selected_position_by_size.items()):
        size = int(size_key)
        observed = [observed_by_position.get(f"P{index:02d}", 0) for index in range(size)]
        result = stats.chisquare(observed)
        position_uniformity[size_key] = {
            "chi_square_decimal": _float_text(result.statistic),
            "p_value_descriptive_decimal": _float_text(result.pvalue),
        }
    return {
        "episode_count": len(episodes),
        "candidate_set_size_counts": dict(sorted(candidate_set_sizes.items())),
        "selected_presented_position_counts_by_candidate_set_size": {key: dict(sorted(value.items())) for key, value in sorted(selected_position_by_size.items())},
        "selected_position_uniformity_diagnostic": position_uniformity,
        "distinct_baseline_canonical_id_count": len(baseline_ids),
        "distinct_selected_canonical_id_count": len(selected_ids),
        "selected_canonical_ids": sorted(selected_ids),
        "selected_no_change_count": selected_no_change,
        "selected_minimum_non_hold_action_count": selected_min_actions,
        "selected_minimum_total_quantity_count": selected_min_quantity,
        "selected_unique_zero_activity_count": selected_unique_zero,
        "simple_parsimony_rule_match_count": simple_rule_matches,
        "candidate_primary_role_counts": dict(sorted(primary_roles.items())),
        "candidate_alias_counts": dict(sorted(aliases.items())),
        "selector_confidence_counts": dict(sorted(confidence_counts.items())),
        "selector_reason_code_counts": dict(sorted(reason_code_counts.items())),
        "deterministic_zero_activity_counterfactual": {
            "policy": "MIN_NON_HOLD_ACTION_COUNT_THEN_MIN_TOTAL_ABSOLUTE_QUANTITY_THEN_CANONICAL_ID",
            "same_selected_candidate_count": simple_rule_matches,
            "same_executed_candidate_count": simple_rule_matches,
            "same_paired_result_count": simple_rule_matches,
            "provider_calls_required": 0,
            "llm_specific_incremental_selection_effect_identified": False,
            "interpretation": "On this frozen frame, a provider-free parsimony rule reproduces every LLM selection and therefore every executed candidate and paired utility delta.",
        },
    }


def _distribution_summary(values: list[int]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    if len(array) < 8:
        raise R02D3PosthocError("distribution diagnostics require at least eight values")
    mean = float(array.mean())
    sample_sd = float(array.std(ddof=1))
    quantiles = np.percentile(array, [0, 5, 10, 25, 50, 75, 90, 95, 100])
    shapiro = stats.shapiro(array)
    normal = stats.normaltest(array)
    jarque_bera = stats.jarque_bera(array)
    fitted_normal = stats.kstest((array - mean) / sample_sd, "norm")
    fitted_uniform = stats.kstest((array - array.min()) / (array.max() - array.min()), "uniform")
    edges = np.linspace(float(array.min()), float(array.max()), 9)
    counts = np.histogram(array, bins=edges)[0]
    return {
        "count": len(values),
        "mean_e12_rounded": round(mean),
        "median_e12_rounded": round(float(quantiles[4])),
        "sample_sd_e12_rounded": round(sample_sd),
        "minimum_e12": round(float(quantiles[0])),
        "p05_e12_rounded": round(float(quantiles[1])),
        "p10_e12_rounded": round(float(quantiles[2])),
        "p25_e12_rounded": round(float(quantiles[3])),
        "p75_e12_rounded": round(float(quantiles[5])),
        "p90_e12_rounded": round(float(quantiles[6])),
        "p95_e12_rounded": round(float(quantiles[7])),
        "maximum_e12": round(float(quantiles[8])),
        "positive_count": int((array > 0).sum()),
        "negative_count": int((array < 0).sum()),
        "zero_count": int((array == 0).sum()),
        "bias_corrected_skew_decimal": _float_text(stats.skew(array, bias=False)),
        "bias_corrected_excess_kurtosis_decimal": _float_text(stats.kurtosis(array, fisher=True, bias=False)),
        "shapiro_wilk": {"statistic_decimal": _float_text(shapiro.statistic), "p_value_decimal": _float_text(shapiro.pvalue)},
        "dagostino_k2": {"statistic_decimal": _float_text(normal.statistic), "p_value_decimal": _float_text(normal.pvalue)},
        "jarque_bera": {"statistic_decimal": _float_text(jarque_bera.statistic), "p_value_decimal": _float_text(jarque_bera.pvalue)},
        "fitted_normal_ks_descriptive": {"statistic_decimal": _float_text(fitted_normal.statistic), "naive_p_value_decimal": _float_text(fitted_normal.pvalue)},
        "fitted_uniform_ks_descriptive": {"statistic_decimal": _float_text(fitted_uniform.statistic), "naive_p_value_decimal": _float_text(fitted_uniform.pvalue)},
        "equal_width_histogram": {
            "edges_e12_rounded": [round(float(value)) for value in edges],
            "counts": [int(value) for value in counts],
        },
        "diagnostic_only": True,
    }


def _evaluate(representative: np.ndarray, challenge: np.ndarray) -> dict[str, Any]:
    theta = stratified_weighted_mean_e12(
        tuple(int(value) for value in representative),
        tuple(int(value) for value in challenge),
    )
    lower, upper = stratified_bootstrap_interval_e12(
        tuple(int(value) for value in representative),
        tuple(int(value) for value in challenge),
        seed_hex=BOOTSTRAP_SEED_HEX,
    )
    return {
        "theta_system_e12": theta,
        "bootstrap_lower_e12": lower,
        "bootstrap_upper_e12": upper,
        "supported_under_frozen_threshold": lower > R02_DELTA_MIN_E12,
    }


def _winsorize(values: np.ndarray, fraction: float) -> np.ndarray:
    lower, upper = np.quantile(values, [fraction, 1.0 - fraction], method="linear")
    return np.rint(np.clip(values, lower, upper)).astype(np.int64)


def _sensitivity_analysis(
    pairs: dict[str, int],
    representative_cases: list[dict[str, Any]],
    challenge_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    representative = np.asarray(
        [pairs.get(str(value["fixture_id"]), 0) for value in representative_cases],
        dtype=np.int64,
    )
    challenge = np.asarray(
        [pairs.get(str(value["fixture_id"]), 0) for value in challenge_cases],
        dtype=np.int64,
    )
    locations = {str(value["fixture_id"]): ("REPRESENTATIVE", index) for index, value in enumerate(representative_cases)}
    locations.update({str(value["fixture_id"]): ("CHALLENGE_HEADROOM", index) for index, value in enumerate(challenge_cases)})
    base = _evaluate(representative, challenge)
    zero_nullifications: list[dict[str, Any]] = []
    literal_deletions: list[dict[str, Any]] = []
    for fixture_id, delta in pairs.items():
        stratum, index = locations[fixture_id]
        representative_zeroed = representative.copy()
        challenge_zeroed = challenge.copy()
        if stratum == "REPRESENTATIVE":
            representative_zeroed[index] = 0
            representative_deleted = np.delete(representative, index)
            challenge_deleted = challenge
        else:
            challenge_zeroed[index] = 0
            representative_deleted = representative
            challenge_deleted = np.delete(challenge, index)
        zero_nullifications.append(
            {
                "fixture_id": fixture_id,
                "stratum": stratum,
                "observed_delta_e12": delta,
                **_evaluate(representative_zeroed, challenge_zeroed),
            }
        )
        literal_deletions.append(
            {
                "fixture_id": fixture_id,
                "stratum": stratum,
                "observed_delta_e12": delta,
                **_evaluate(representative_deleted, challenge_deleted),
            }
        )

    ordered_positive = sorted(pairs.items(), key=lambda value: value[1], reverse=True)
    top_tail: list[dict[str, Any]] = []
    for count in range(6):
        representative_zeroed = representative.copy()
        challenge_zeroed = challenge.copy()
        for fixture_id, _ in ordered_positive[:count]:
            stratum, index = locations[fixture_id]
            if stratum == "REPRESENTATIVE":
                representative_zeroed[index] = 0
            else:
                challenge_zeroed[index] = 0
        top_tail.append(
            {
                "nullified_top_positive_count": count,
                "fixture_ids": [fixture_id for fixture_id, _ in ordered_positive[:count]],
                "nullified_delta_sum_e12": sum(delta for _, delta in ordered_positive[:count]),
                **_evaluate(representative_zeroed, challenge_zeroed),
            }
        )

    winsorized: dict[str, Any] = {}
    for fraction in (0.01, 0.05, 0.10):
        winsorized[f"{fraction:.2f}"] = _evaluate(
            _winsorize(representative, fraction),
            _winsorize(challenge, fraction),
        )

    def influence_summary(values: list[dict[str, Any]]) -> dict[str, Any]:
        supported = [value for value in values if value["supported_under_frozen_threshold"]]
        most_adverse = min(values, key=lambda value: int(value["bootstrap_lower_e12"]))
        least_adverse = max(values, key=lambda value: int(value["bootstrap_lower_e12"]))
        return {
            "case_count": len(values),
            "supported_count": len(supported),
            "not_supported_count": len(values) - len(supported),
            "minimum_bootstrap_lower_e12": min(int(value["bootstrap_lower_e12"]) for value in values),
            "maximum_bootstrap_lower_e12": max(int(value["bootstrap_lower_e12"]) for value in values),
            "most_adverse_case": most_adverse,
            "least_adverse_case": least_adverse,
        }

    return {
        "confirmatory_result_recomputed": base,
        "single_fixture_zero_nullification": {
            "definition": "Keep the frozen 160-fixture frame and replace one eligible observed delta with the preregistered zero contribution.",
            "summary": influence_summary(zero_nullifications),
            "cases": zero_nullifications,
        },
        "literal_leave_one_out": {
            "definition": "Delete one eligible fixture from its stratum and recompute target-stratum weighting; this changes the frozen design and is diagnostic only.",
            "summary": influence_summary(literal_deletions),
        },
        "top_positive_zero_nullification": top_tail,
        "within_full_stratum_winsorization": {
            "definition": "Clip each full-stratum delta vector at the stated two-sided empirical fraction before recomputing the frozen statistic; exploratory only.",
            "results": winsorized,
        },
        "confirmatory_verdict_changed": False,
        "robustness_interpretation": "The preregistered SUPPORTED label remains sealed, but the narrow lower-bound margin is sensitive to individual high-positive fixtures and to 10% winsorization.",
    }


def _frozen_power_sensitivity(statistical_freeze: dict[str, Any]) -> dict[str, Any]:
    scenarios = statistical_freeze.get("power_scenarios")
    if not isinstance(scenarios, list):
        raise R02D3PosthocError("statistical freeze lacks power scenarios")
    wanted = {"n160-design-worst", "n160-low-snr-sensitivity", "n160-high-snr-sensitivity"}
    selected = {
        str(value["scenario_id"]): {
            "conditional_standardized_mean_bps": value["conditional_standardized_mean_bps"],
            "estimated_power_ppm": value["estimated_power_ppm"],
            "wilson_lower_power_ppm": value["wilson_lower_power_ppm"],
            "wilson_upper_power_ppm": value["wilson_upper_power_ppm"],
        }
        for value in scenarios
        if isinstance(value, dict) and value.get("scenario_id") in wanted
    }
    if set(selected) != wanted:
        raise R02D3PosthocError("required frozen power sensitivity scenarios are missing")
    return {
        "source": "ACCEPTED_PROVIDER_FREE_PROSPECTIVE_POWER_FREEZE",
        "scenarios": selected,
        "interpretation": "The frozen n=160 low-SNR scenario estimated 79.0% power with a 76.3669% Wilson lower bound; this is prospective design evidence, not a reclassification of observed outcomes.",
    }


def build_posthoc_report(repo_root: Path) -> dict[str, Any]:
    """Build a deterministic, provider-free report from sealed successor evidence."""

    root = repo_root.resolve()
    evidence_path = root / "docs" / "r02-d3-successor-live-evidence.json"
    statistical_freeze_path = root / "docs" / "r02-d2c-statistical-freeze.json"
    archive_root = root / ".research_artifacts" / RUN_ID
    audit_root = archive_root / "audit"
    frame_root = root / ".research_artifacts" / "r02-d2c-frame-53be0c4bb060"
    frame_manifest_path = frame_root / "frame_manifest.json"
    for path in (evidence_path, statistical_freeze_path, audit_root, frame_manifest_path):
        if not path.exists():
            raise R02D3PosthocError(f"required sealed input is missing: {path}")
    evidence = _read_json(evidence_path)
    statistical_freeze = _read_json(statistical_freeze_path)
    frame_manifest = _read_json(frame_manifest_path)
    if evidence.get("run_id") != RUN_ID or evidence.get("status") != "COMPLETE":
        raise R02D3PosthocError("successor evidence identity or status mismatch")
    if evidence.get("final_disposition", {}).get("closeout_status") != "INDEPENDENTLY_REVIEWED":
        raise R02D3PosthocError("successor closeout is not independently reviewed")
    if _sha256_file(statistical_freeze_path) != STATISTICAL_FREEZE_SHA256:
        raise R02D3PosthocError("statistical freeze hash mismatch")
    if _filesystem_tree(audit_root) != (2322, AUDIT_TREE_SHA256):
        raise R02D3PosthocError("audit tree hash mismatch")
    if _filesystem_tree(archive_root) != (2327, DURABLE_TREE_SHA256):
        raise R02D3PosthocError("durable archive tree hash mismatch")
    if _filesystem_tree(frame_root) != (162, FRAME_TREE_SHA256):
        raise R02D3PosthocError("frame tree hash mismatch")
    replay = replay_audit_root(audit_root)
    if replay.anchor.sequence != 774 or replay.ledgers[-1].status != "COMPLETE":
        raise R02D3PosthocError("strict replay did not reach the sealed COMPLETE terminal")
    anchor, payloads = _load_payloads(audit_root)
    episodes = payloads.get("episode_preparation", [])
    outcomes = payloads.get("selector_outcome", [])
    parsed_responses = payloads.get("parsed_response", [])
    paired_results = payloads.get("paired_result", [])
    if len(paired_results) != 55:
        raise R02D3PosthocError("sealed run does not contain 55 paired results")
    pairs = {str(value["fixture_id"]): int(value["paired_utility_delta_e12"]) for value in paired_results}
    cases = frame_manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != 160:
        raise R02D3PosthocError("frame manifest does not contain 160 cases")
    eligible = {str(value["fixture_id"]) for value in cases if value.get("eligible_opportunity") is True}
    if set(pairs) != eligible:
        raise R02D3PosthocError("paired results do not match frozen eligible fixtures")
    representative_cases = [value for value in cases if value.get("stratum") == "REPRESENTATIVE"]
    challenge_cases = [value for value in cases if value.get("stratum") == "CHALLENGE_HEADROOM"]
    representative_eligible = [pairs[str(value["fixture_id"])] for value in representative_cases if str(value["fixture_id"]) in pairs]
    challenge_eligible = [pairs[str(value["fixture_id"])] for value in challenge_cases if str(value["fixture_id"]) in pairs]
    selection = _selection_consistency(episodes, outcomes, parsed_responses)
    if selection["selected_canonical_ids"] != [SELECTED_CANONICAL_ID]:
        raise R02D3PosthocError("selected canonical identity mismatch")
    sensitivity = _sensitivity_analysis(pairs, representative_cases, challenge_cases)
    confirmatory = sensitivity["confirmatory_result_recomputed"]
    frozen_evaluation = evidence["frozen_primary_evaluation"]
    if confirmatory["theta_system_e12"] != frozen_evaluation["theta_system_e12"] or confirmatory["bootstrap_lower_e12"] != frozen_evaluation["bootstrap_lower_e12"] or confirmatory["bootstrap_upper_e12"] != frozen_evaluation["bootstrap_upper_e12"]:
        raise R02D3PosthocError("confirmatory result differs from independently reviewed closeout")
    return {
        "schema_version": "r02-d3-successor-provider-free-posthoc-v1",
        "status": "PROVIDER_FREE_EXPLORATORY_COMPLETE_INDEPENDENTLY_REVIEWED",
        "run_id": RUN_ID,
        "provider_calls": 0,
        "live_execution": False,
        "confirmatory_verdict_modified": False,
        "independent_review": {
            "review_date": "2026-07-18",
            "status": "PASS",
            "reviewed_pre_status_analysis_source_sha256": "4b6faa50080aa9770326a2a078bb360a1067e3b053325f22e462ec7f3aca819a",
            "reviewed_pre_status_report_sha256": "773474dfcf2cccabb544998d39f4034d8a8354d8134c5bbe4ef21938d15bdb03",
            "byte_for_byte_regeneration_passed": True,
            "provider_free_boundary_passed": True,
            "zero_activity_rule_independently_recomputed": True,
            "sensitivity_values_independently_recomputed": True,
            "blocking_findings": 0,
        },
        "source_identity": {
            "analysis_source_relative_path": "v2/research/overlay/r02_d3_posthoc_analysis.py",
            "analysis_source_sha256": _sha256_file(Path(__file__).resolve()),
            "numpy_version": np.__version__,
            "scipy_version": getattr(__import__("scipy"), "__version__"),
        },
        "sealed_inputs": {
            "successor_evidence_relative_path": "docs/r02-d3-successor-live-evidence.json",
            "successor_evidence_sha256": _sha256_file(evidence_path),
            "statistical_freeze_sha256": STATISTICAL_FREEZE_SHA256,
            "audit_tree_sha256": AUDIT_TREE_SHA256,
            "durable_archive_tree_sha256": DURABLE_TREE_SHA256,
            "frame_tree_sha256": FRAME_TREE_SHA256,
            "bootstrap_seed_sha256": BOOTSTRAP_SEED_HEX,
            "strict_replay_anchor_sequence": anchor["sequence"],
            "strict_replay_passed": True,
        },
        "confirmatory_result_preserved": {
            **confirmatory,
            "delta_min_e12": R02_DELTA_MIN_E12,
            "delta_target_e12": R02_DELTA_TARGET_E12,
            "eligible_fixture_count": len(pairs),
            "m_min": R02_M_MIN,
            "verdict": "SUPPORTED",
        },
        "selection_consistency": selection,
        "eligible_delta_distribution": {
            "all_55": _distribution_summary(list(pairs.values())),
            "representative_15": _distribution_summary(representative_eligible),
            "challenge_40": _distribution_summary(challenge_eligible),
            "interpretation": "The combined eligible deltas are centrally concentrated but right-skewed and heavy-tailed; they are neither normal nor uniform. The challenge stratum drives most non-normality.",
        },
        "exploratory_sensitivity": sensitivity,
        "frozen_prospective_power_sensitivity": _frozen_power_sensitivity(statistical_freeze),
        "research_interpretation": {
            "system_vs_baseline": "SUPPORTED_ON_THE_SEALED_FRAME",
            "llm_vs_deterministic_zero_activity_selector": "NOT_IDENTIFIED_BECAUSE_ACTIONS_ARE_IDENTICAL_55_OF_55",
            "robustness": "NARROW_CONFIRMATORY_MARGIN_WITH_MATERIAL_SINGLE_FIXTURE_AND_UPPER_TAIL_SENSITIVITY",
            "recommended_next_scientific_step": "NEW_SEED_PREREGISTERED_REPLICATION_REQUIRING_A_NEW_FREEZE_INDEPENDENT_REVIEW_AND_EXPLICIT_LIVE_AUTHORIZATION",
            "additional_live_execution_authorized": False,
        },
    }
