"""Provider-free post-hoc analysis for the sealed R02 D4 LIVE run."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .canonical import canonical_json_bytes
from .contracts import ASSET_IDS, Decision, DecisionBatch
from .r02_d4_design import select_parsimony_candidate
from .r02_d4_s3_freeze import (
    bootstrap_seed_sha256,
    classify_incremental,
    classify_parsimony,
    classify_primary,
    variant_seed_sha256,
    wilson_interval_ppm,
)
from .r02_d4_s6_replay import replay_s6_audit_root
from .r02_d4_s6_runner import build_provider_free_run_plan
from .r02_statistics import (
    stratified_bootstrap_interval_e12,
    stratified_weighted_mean_e12,
)
from .scoring import score_episode
from .validator import validate_batch


RUN_ID = "r02-d4-s8-20260719"
AUDIT_ROOT = ".research_artifacts/r02-d4-s6-r02-d4-s8-20260719"
TRANSPORT_ROOT = ".research_artifacts/r02-d4-s7-transport-r02-d4-s8-20260719"
FRAME_ROOT = ".research_artifacts/r02-d4-s2a-frame-0716a1b9c13a"
S3_FREEZE = "docs/r02-d4-s3-statistical-freeze.json"
S6_AUTH = "docs/r02-d4-s6-live-authorization.json"
S7_AUTH = "docs/r02-d4-s7-live-authorization.json"
EXPECTED_S6_AUTH_SHA256 = "5eb08e1994add052cf7994f56add7a40df2ef8531bdba32afbed0c9f493178d4"
EXPECTED_S7_AUTH_SHA256 = "c05bf7a733f6b8985e54bcd5170f6534112b7ed28e8addecfba9d9a16c9a5042"
EXPECTED_TERMINAL_SHA256 = "52833353ffb49edf90c20efe892dc713aa65abb19ed9d8d14f4a57d27f0c447f"
EXPECTED_TERMINAL_ANCHOR_SHA256 = "72f1b14e8cada46e724ba0e2b88d0b465f083bd47c1d9a1d68fce871286f3b43"
DELTA_MIN_E12 = 50_000_000
M_MIN = 57


class R02D4PosthocError(RuntimeError):
    """Raised when sealed evidence cannot support the frozen analysis."""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise R02D4PosthocError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise R02D4PosthocError(f"JSON artifact must be an object: {path}")
    return value


def _walk_json(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.json") if path.is_file())


def _tree_digest(root: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return len(files), digest.hexdigest()


def _distribution(values: Iterable[int]) -> dict[str, Any]:
    array = np.asarray(tuple(values), dtype=np.int64)
    if not len(array):
        raise R02D4PosthocError("empty distribution")
    quantiles = np.rint(
        np.quantile(array, [0.0, 0.25, 0.5, 0.75, 1.0], method="linear")
    ).astype(np.int64)
    return {
        "count": int(len(array)),
        "negative_count": int(np.sum(array < 0)),
        "zero_count": int(np.sum(array == 0)),
        "positive_count": int(np.sum(array > 0)),
        "mean_e12_round_half_even": int(np.rint(np.mean(array))),
        "min_e12": int(quantiles[0]),
        "p25_e12": int(quantiles[1]),
        "median_e12": int(quantiles[2]),
        "p75_e12": int(quantiles[3]),
        "max_e12": int(quantiles[4]),
    }


def _estimate(rep: tuple[int, ...], challenge: tuple[int, ...], seed: str) -> dict[str, int]:
    lower, upper = stratified_bootstrap_interval_e12(rep, challenge, seed_hex=seed)
    return {
        "theta_e12": stratified_weighted_mean_e12(rep, challenge),
        "lower_e12": lower,
        "upper_e12": upper,
    }


def _winsorize(values: tuple[int, ...], fraction_ppm: int) -> tuple[int, ...]:
    fraction = fraction_ppm / 1_000_000
    array = np.asarray(values, dtype=np.int64)
    lower, upper = np.quantile(array, [fraction, 1.0 - fraction], method="linear")
    return tuple(int(value) for value in np.rint(np.clip(array, lower, upper)).astype(np.int64))


def _parsimony_utility(attempt: Any) -> tuple[str, int]:
    records = [record.model_dump(mode="json") for record in attempt.preparation.candidate_set.candidates]
    selection = select_parsimony_candidate(records)
    record = next(
        item
        for item in attempt.preparation.candidate_set.candidates
        if item.canonical_candidate_id == selection.canonical_candidate_id
    )
    batch = DecisionBatch(
        decisions={
            asset_id: Decision(
                action=record.candidate.decisions[asset_id].action,
                quantity=record.candidate.decisions[asset_id].quantity,
                confidence=100,
                reasoning="r02:d4-posthoc-parsimony",
            )
            for asset_id in ASSET_IDS
        }
    )
    validation = validate_batch(attempt.episode.public, batch)
    return selection.canonical_candidate_id, score_episode(attempt.episode, validation).utility_e12


def _load_outcomes(audit_root: Path) -> dict[str, dict[str, Any]]:
    outcomes: dict[str, dict[str, Any]] = {}
    for path in sorted((audit_root / "payloads").glob("*-attempt_outcome.json")):
        value = _read_json(path)
        fixture_id = value.get("fixture_id")
        if not isinstance(fixture_id, str) or fixture_id in outcomes:
            raise R02D4PosthocError("invalid or duplicate attempt outcome fixture")
        outcomes[fixture_id] = value
    if len(outcomes) != 69:
        raise R02D4PosthocError(f"expected 69 attempt outcomes, found {len(outcomes)}")
    return outcomes


def _transport_summary(root: Path) -> dict[str, Any]:
    records = [_read_json(path) for path in _walk_json(root)]
    if len(records) != 69:
        raise R02D4PosthocError(f"expected 69 transport records, found {len(records)}")
    if any(record.get("run_id") != RUN_ID for record in records):
        raise R02D4PosthocError("transport run_id drift")
    duration_values = tuple(int(record["duration_ms"]) for record in records)
    return {
        "record_count": len(records),
        "provider": sorted({str(record.get("provider")) for record in records}),
        "requested_model_id": sorted({str(record.get("requested_model_id")) for record in records}),
        "external_provider_calls": sum(int(record.get("external_provider_calls", 0)) for record in records),
        "exit_code_zero_count": sum(record.get("exit_code") == 0 for record in records),
        "timeout_count": sum(bool(record.get("timed_out")) for record in records),
        "launch_error_count": sum(record.get("launch_error") is not None for record in records),
        "parse_error_count": sum(record.get("parse_error_code") is not None for record in records),
        "terminal_usage_event_count": sum(int(record.get("terminal_usage_event_count", 0)) for record in records),
        "duration_ms": {"sum": sum(duration_values), **_distribution(duration_values)},
    }


def build_report(repository_root: str | Path) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    audit_root = root / AUDIT_ROOT
    transport_root = root / TRANSPORT_ROOT
    frame_root = root / FRAME_ROOT
    for required in (audit_root, transport_root, frame_root):
        if not required.is_dir():
            raise R02D4PosthocError(f"missing sealed root: {required}")

    if _sha256_file(root / S6_AUTH) != EXPECTED_S6_AUTH_SHA256:
        raise R02D4PosthocError("S6 authorization digest drift")
    if _sha256_file(root / S7_AUTH) != EXPECTED_S7_AUTH_SHA256:
        raise R02D4PosthocError("S7 authorization digest drift")

    replay = replay_s6_audit_root(audit_root, repository_root=root)
    terminal_sha = hashlib.sha256(canonical_json_bytes(replay.terminal)).hexdigest()
    anchor_sha = hashlib.sha256(canonical_json_bytes(replay.terminal_anchor)).hexdigest()
    if terminal_sha != EXPECTED_TERMINAL_SHA256 or anchor_sha != EXPECTED_TERMINAL_ANCHOR_SHA256:
        raise R02D4PosthocError("terminal or terminal-anchor digest drift")

    transport = _transport_summary(transport_root)
    valid_run = (
        replay.authorization.run_id == RUN_ID
        and replay.terminal.terminal_status == "COMPLETE"
        and replay.attempted_count == 69
        and replay.settled_fail_closed_count == 0
        and replay.unsettled_count == 0
        and replay.external_provider_calls == 69
        and transport["external_provider_calls"] == 69
        and transport["exit_code_zero_count"] == 69
        and transport["timeout_count"] == 0
        and transport["launch_error_count"] == 0
        and transport["parse_error_count"] == 0
        and transport["terminal_usage_event_count"] == 69
    )
    if not valid_run:
        raise R02D4PosthocError("sealed LIVE evidence is not a valid complete run")

    manifest = _read_json(frame_root / "frame_manifest.json")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != 200:
        raise R02D4PosthocError("frame must contain exactly 200 cases")
    case_by_id = {case["fixture_id"]: case for case in cases}
    if len(case_by_id) != 200:
        raise R02D4PosthocError("duplicate frame fixture_id")

    outcomes = _load_outcomes(audit_root)
    prepared = build_provider_free_run_plan(root)
    if len(prepared.attempts) != 69:
        raise R02D4PosthocError("prepared run attempt count drift")

    eligible_rows: dict[str, dict[str, Any]] = {}
    for attempt in prepared.attempts:
        fixture_id = attempt.planned.fixture_id
        outcome = outcomes.get(fixture_id)
        case = case_by_id.get(fixture_id)
        if outcome is None or case is None or not case.get("eligible_opportunity"):
            raise R02D4PosthocError(f"eligible fixture binding failure: {fixture_id}")
        parsimony_id, parsimony_utility = _parsimony_utility(attempt)
        agreement = outcome["executed_canonical_id"] == parsimony_id
        primary_delta = int(outcome["paired_utility_delta_e12"])
        parsimony_delta = parsimony_utility - int(outcome["baseline_utility_e12"])
        incremental_delta = 0 if outcome["baseline_fallback"] or agreement else int(outcome["executed_utility_e12"]) - parsimony_utility
        eligible_rows[fixture_id] = {
            "frame_ordinal": int(case["frame_ordinal"]),
            "stratum": case["stratum"],
            "primary_delta_e12": primary_delta,
            "parsimony_delta_e12": parsimony_delta,
            "incremental_delta_e12": incremental_delta,
            "agreement": agreement,
            "observed_total_tokens": int(outcome["observed_total_tokens"]),
            "debit_tokens": int(outcome["debit_tokens"]),
        }

    full_rows = []
    for case in sorted(cases, key=lambda value: int(value["frame_ordinal"])):
        row = eligible_rows.get(case["fixture_id"])
        full_rows.append(
            {
                "fixture_id": case["fixture_id"],
                "frame_ordinal": int(case["frame_ordinal"]),
                "stratum": case["stratum"],
                "eligible": row is not None,
                "primary_delta_e12": 0 if row is None else row["primary_delta_e12"],
                "parsimony_delta_e12": 0 if row is None else row["parsimony_delta_e12"],
                "incremental_delta_e12": 0 if row is None else row["incremental_delta_e12"],
            }
        )

    def vectors(field: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
        return (
            tuple(row[field] for row in full_rows if row["stratum"] == "REPRESENTATIVE"),
            tuple(row[field] for row in full_rows if row["stratum"] == "CHALLENGE_HEADROOM"),
        )

    base_seed = bootstrap_seed_sha256()
    primary_rep, primary_challenge = vectors("primary_delta_e12")
    parsimony_rep, parsimony_challenge = vectors("parsimony_delta_e12")
    incremental_rep, incremental_challenge = vectors("incremental_delta_e12")
    primary = _estimate(primary_rep, primary_challenge, base_seed)
    parsimony = _estimate(parsimony_rep, parsimony_challenge, base_seed)
    incremental = _estimate(incremental_rep, incremental_challenge, base_seed)

    zero_results = []
    leave_results = []
    for fixture_id, row in sorted(eligible_rows.items(), key=lambda item: item[1]["frame_ordinal"]):
        ordinal = row["frame_ordinal"]
        zero_rep = list(primary_rep)
        zero_challenge = list(primary_challenge)
        if row["stratum"] == "REPRESENTATIVE":
            zero_rep[ordinal] = 0
        else:
            zero_challenge[ordinal - 150] = 0
        zero = _estimate(
            tuple(zero_rep),
            tuple(zero_challenge),
            variant_seed_sha256("PRIMARY_ZERO_NULLIFICATION", fixture_ordinal=ordinal),
        )
        zero_results.append({"fixture_id": fixture_id, "frame_ordinal": ordinal, **zero})

        if row["stratum"] == "REPRESENTATIVE":
            leave_rep = primary_rep[:ordinal] + primary_rep[ordinal + 1 :]
            leave_challenge = primary_challenge
        else:
            index = ordinal - 150
            leave_rep = primary_rep
            leave_challenge = primary_challenge[:index] + primary_challenge[index + 1 :]
        leave = _estimate(
            leave_rep,
            leave_challenge,
            variant_seed_sha256("PRIMARY_LITERAL_LEAVE_ONE_OUT", fixture_ordinal=ordinal),
        )
        leave_results.append({"fixture_id": fixture_id, "frame_ordinal": ordinal, **leave})

    winsor = {}
    for fraction in (50_000, 100_000):
        winsor[str(fraction)] = _estimate(
            _winsorize(primary_rep, fraction),
            _winsorize(primary_challenge, fraction),
            variant_seed_sha256(
                "PRIMARY_WITHIN_FULL_STRATUM_WINSORIZATION",
                winsor_fraction_ppm=fraction,
            ),
        )

    maximum_shift = max(abs(item["theta_e12"] - primary["theta_e12"]) for item in zero_results)
    primary_label = classify_primary(
        valid_run=valid_run,
        eligible_count=len(eligible_rows),
        theta_e12=primary["theta_e12"],
        lower_e12=primary["lower_e12"],
        maximum_absolute_theta_shift_e12=maximum_shift,
        all_zero_nullification_lowers_pass=all(item["lower_e12"] > DELTA_MIN_E12 for item in zero_results),
        all_leave_one_out_lowers_pass=all(item["lower_e12"] > DELTA_MIN_E12 for item in leave_results),
        winsor_5_lower_pass=winsor["50000"]["lower_e12"] > DELTA_MIN_E12,
        winsor_10_lower_pass=winsor["100000"]["lower_e12"] > DELTA_MIN_E12,
    )
    parsimony_label = classify_parsimony(
        valid_run=valid_run,
        eligible_count=len(eligible_rows),
        lower_e12=parsimony["lower_e12"],
    )
    discordant = [row for row in eligible_rows.values() if not row["agreement"]]
    discordance_by_stratum = Counter(row["stratum"] for row in discordant)
    incremental_label = classify_incremental(
        valid_run=valid_run,
        total_discordance=len(discordant),
        representative_discordance=discordance_by_stratum["REPRESENTATIVE"],
        challenge_discordance=discordance_by_stratum["CHALLENGE_HEADROOM"],
        lower_e12=incremental["lower_e12"],
        upper_e12=incremental["upper_e12"],
    )
    agreement_count = sum(row["agreement"] for row in eligible_rows.values())
    agreement_lower, agreement_upper = wilson_interval_ppm(agreement_count, len(eligible_rows))

    audit_count, audit_tree_sha = _tree_digest(audit_root)
    transport_count, transport_tree_sha = _tree_digest(transport_root)
    tokens = tuple(row["observed_total_tokens"] for row in eligible_rows.values())
    debits = tuple(row["debit_tokens"] for row in eligible_rows.values())
    return {
        "schema_version": "r02-d4-live-posthoc-v1",
        "status": "PROVIDER_FREE_POSTHOC_COMPLETE_PENDING_INDEPENDENT_REVIEW",
        "run_id": RUN_ID,
        "analysis_provider_calls": 0,
        "analysis_codex_exec_invocations": 0,
        "new_live_runs": 0,
        "valid_run": valid_run,
        "evidence": {
            "s3_statistical_freeze_sha256": _sha256_file(root / S3_FREEZE),
            "s6_live_authorization_sha256": EXPECTED_S6_AUTH_SHA256,
            "s7_live_authorization_sha256": EXPECTED_S7_AUTH_SHA256,
            "terminal_sha256": terminal_sha,
            "terminal_anchor_sha256": anchor_sha,
            "audit_root": AUDIT_ROOT,
            "audit_file_count": audit_count,
            "audit_tree_sha256": audit_tree_sha,
            "transport_root": TRANSPORT_ROOT,
            "transport_file_count": transport_count,
            "transport_tree_sha256": transport_tree_sha,
            "frame_manifest_sha256": _sha256_file(frame_root / "frame_manifest.json"),
        },
        "execution": {
            "attempted_count": replay.attempted_count,
            "settled_fail_closed_count": replay.settled_fail_closed_count,
            "unsettled_count": replay.unsettled_count,
            "external_provider_calls": replay.external_provider_calls,
            "transport": transport,
            "observed_total_tokens": {"sum": sum(tokens), **_distribution(tokens)},
            "debited_tokens": {"cap": 2_208_000, "sum": sum(debits), **_distribution(debits)},
        },
        "frame": {
            "total_count": 200,
            "representative_count": len(primary_rep),
            "challenge_count": len(primary_challenge),
            "eligible_count": len(eligible_rows),
            "representative_eligible_count": sum(row["stratum"] == "REPRESENTATIVE" for row in eligible_rows.values()),
            "challenge_eligible_count": sum(row["stratum"] == "CHALLENGE_HEADROOM" for row in eligible_rows.values()),
            "m_min": M_MIN,
        },
        "bootstrap": {
            "base_seed_sha256": base_seed,
            "resamples": 10_000,
            "bit_generator": "PCG64",
            "lower_rank_index_zero_based": 249,
            "upper_rank_index_zero_based": 9_749,
        },
        "primary_replication": {
            "label": primary_label,
            "threshold_e12": DELTA_MIN_E12,
            **primary,
            "full_frame_distribution": _distribution(primary_rep + primary_challenge),
            "eligible_distribution": _distribution(row["primary_delta_e12"] for row in eligible_rows.values()),
            "robustness": {
                "maximum_absolute_theta_shift_e12": maximum_shift,
                "maximum_absolute_theta_shift_ppm_of_abs_theta": int(np.rint(maximum_shift * 1_000_000 / abs(primary["theta_e12"]))),
                "all_zero_nullification_lowers_pass": all(item["lower_e12"] > DELTA_MIN_E12 for item in zero_results),
                "minimum_zero_nullification_lower_e12": min(item["lower_e12"] for item in zero_results),
                "all_leave_one_out_lowers_pass": all(item["lower_e12"] > DELTA_MIN_E12 for item in leave_results),
                "minimum_leave_one_out_lower_e12": min(item["lower_e12"] for item in leave_results),
                "winsorized": winsor,
                "variant_count": len(zero_results) + len(leave_results) + len(winsor),
            },
        },
        "deterministic_parsimony": {
            "label": parsimony_label,
            "threshold_e12": DELTA_MIN_E12,
            **parsimony,
            "exact_vector_equal_to_primary": (primary_rep, primary_challenge) == (parsimony_rep, parsimony_challenge),
            "full_frame_distribution": _distribution(parsimony_rep + parsimony_challenge),
        },
        "incremental_llm": {
            "label": incremental_label,
            "threshold_e12": 0,
            **incremental,
            "discordant_total": len(discordant),
            "discordant_representative": discordance_by_stratum["REPRESENTATIVE"],
            "discordant_challenge": discordance_by_stratum["CHALLENGE_HEADROOM"],
            "full_frame_distribution": _distribution(incremental_rep + incremental_challenge),
        },
        "agreement": {
            "agreement_count": agreement_count,
            "eligible_count": len(eligible_rows),
            "point_ppm": int(np.rint(agreement_count * 1_000_000 / len(eligible_rows))),
            "wilson_95_lower_ppm": agreement_lower,
            "wilson_95_upper_ppm": agreement_upper,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    primary = report["primary_replication"]
    parsimony = report["deterministic_parsimony"]
    incremental = report["incremental_llm"]
    agreement = report["agreement"]
    execution = report["execution"]
    robustness = primary["robustness"]
    return "\n".join(
        [
            "# R02 D4 LIVE post-hoc analysis",
            "",
            f"- Run: `{report['run_id']}`",
            f"- Status: `{report['status']}`",
            f"- Valid sealed run: `{str(report['valid_run']).lower()}`",
            "- Analysis boundary: provider-free; no new LIVE run, retry, replacement, or resume",
            "",
            "## Frozen endpoints",
            "",
            f"- Primary replication: **{primary['label']}**; theta `{primary['theta_e12']}`, 95% bootstrap CI `[{primary['lower_e12']}, {primary['upper_e12']}]`, threshold `{primary['threshold_e12']}` e12.",
            f"- Deterministic parsimony: **{parsimony['label']}**; theta `{parsimony['theta_e12']}`, 95% bootstrap CI `[{parsimony['lower_e12']}, {parsimony['upper_e12']}]` e12.",
            f"- Incremental LLM: **{incremental['label']}**; discordant `{incremental['discordant_total']}`/69, theta `{incremental['theta_e12']}`, 95% bootstrap CI `[{incremental['lower_e12']}, {incremental['upper_e12']}]` e12.",
            f"- Exact selector agreement: `{agreement['agreement_count']}`/`{agreement['eligible_count']}` ({agreement['point_ppm']} ppm), Wilson 95% `[{agreement['wilson_95_lower_ppm']}, {agreement['wilson_95_upper_ppm']}]` ppm.",
            "",
            "## Robustness",
            "",
            f"- Maximum one-fixture raw-theta shift: `{robustness['maximum_absolute_theta_shift_e12']}` e12 (`{robustness['maximum_absolute_theta_shift_ppm_of_abs_theta']}` ppm of |theta|).",
            f"- All 69 zero-nullification lower bounds pass: `{str(robustness['all_zero_nullification_lowers_pass']).lower()}`; minimum `{robustness['minimum_zero_nullification_lower_e12']}`.",
            f"- All 69 literal leave-one-out lower bounds pass: `{str(robustness['all_leave_one_out_lowers_pass']).lower()}`; minimum `{robustness['minimum_leave_one_out_lower_e12']}`.",
            f"- 5% winsorized lower: `{robustness['winsorized']['50000']['lower_e12']}`; 10% winsorized lower: `{robustness['winsorized']['100000']['lower_e12']}`.",
            "",
            "## Execution statistics",
            "",
            f"- Attempts: `{execution['attempted_count']}`; settled fail-closed: `{execution['settled_fail_closed_count']}`; unsettled: `{execution['unsettled_count']}`.",
            f"- Provider calls in sealed source run: `{execution['external_provider_calls']}`; provider calls during analysis: `0`.",
            f"- Observed tokens: `{execution['observed_total_tokens']['sum']}`; debited tokens: `{execution['debited_tokens']['sum']}` / `{execution['debited_tokens']['cap']}`.",
            f"- Transport duration sum: `{execution['transport']['duration_ms']['sum']}` ms; median `{execution['transport']['duration_ms']['median_e12']}` ms; max `{execution['transport']['duration_ms']['max_e12']}` ms.",
            "",
            "## Interpretation",
            "",
            "The confirmatory full-frame ITT endpoint uses all 200 frozen fixtures, with zero contribution for the 131 non-eligible fixtures. The LLM selected the deterministic parsimony candidate in every eligible fixture, so the primary and parsimony vectors are byte-for-byte numerically identical. The frozen discordance floor is not met; incremental LLM value is therefore not identified, not evidence of benefit or harm.",
            "",
            "Independent review remains required before treating this report as accepted.",
            "",
        ]
    )
