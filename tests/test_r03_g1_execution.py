from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

import v2.research.news_reasoning.r03_g1_execution as g1
from v2.research.overlay.canonical import canonical_sha256


def _pin_threads(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in g1.THREAD_ENV_KEYS:
        monkeypatch.setenv(key, "1")
    runtime = g1.installed_t0_runtime_identity()
    monkeypatch.setattr(g1, "_T0_RUNTIME_CACHE", runtime)


def _row(
    row_id: str,
    decision: datetime,
    ordinal: int,
    *,
    split: str = "DEVELOPMENT",
    matured_at: datetime | None = None,
) -> g1.T0FitRowMetadata:
    return g1.T0FitRowMetadata(
        row_id=row_id,
        decision_at=decision,
        feature_cutoff_at=decision - timedelta(days=1),
        label_maturity_at=matured_at or decision + timedelta(days=7),
        decision_session_ordinal=ordinal,
        feature_session_ordinal=ordinal - 1,
        label_session_ordinal=ordinal + 5,
        split_name=split,
        phase_book=ordinal % 5,
    )


def _matrix(rows: int) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float((row + 1) * (column + 2)) / 100.0 for column in range(18)) for row in range(rows))


def _utilities() -> dict[int, dict[tuple[int, int], int]]:
    cells = {(fold, cost) for fold in g1.T0_FOLD_END_YEARS for cost in g1.T0_COST_CELLS_BPS}
    values = {
        1: 10,
        10: 20,
        100: 30,
        1000: 30,
    }
    return {alpha: {cell: values[alpha] for cell in cells} for alpha in values}


def _candidate_runs() -> dict[int, dict[int, str]]:
    return {alpha: {fold: format(1 + alpha_index * 4 + fold_index, "064x") for fold_index, fold in enumerate(g1.T0_FOLD_END_YEARS)} for alpha_index, alpha in enumerate(g1.T0_ALPHA_E1_GRID)}


def _snapshot(
    monkeypatch: pytest.MonkeyPatch,
    refit_at: datetime,
) -> g1.T0SnapshotIdentity:
    _pin_threads(monkeypatch)
    decisions = [datetime(2020, 1, 2 + index, 15, tzinfo=timezone.utc) for index in range(4)]
    rows = tuple(_row(f"r{index}", decision, 100 + index) for index, decision in enumerate(decisions))
    matrix = _matrix(len(rows))
    targets = (100_000_000, -50_000_000, 200_000_000, 25_000_000)
    frame = g1.build_training_frame_identity(rows, matrix, targets)
    selection = g1.select_t0_alpha(_utilities(), _candidate_runs())
    runtime = g1.installed_t0_runtime_identity()
    return g1._fit_t0_snapshot(
        matrix,
        targets,
        refit_at=refit_at,
        training_frame=frame,
        alpha_selection=selection,
        runtime=runtime,
    )


def test_protocol_freezes_preprocessing_scale_solver_and_refit() -> None:
    protocol = g1.t0_protocol_identity()
    assert protocol.schema_version == "r03-t0-protocol-identity-v2"
    assert protocol.base_features == g1.T0_BASE_FEATURES
    assert len(protocol.base_features) == 9
    assert len(protocol.design_columns) == 18
    assert protocol.design_columns == tuple(column for feature in protocol.base_features for column in (feature, f"{feature}_missing"))
    assert protocol.imputation == "same_date_sector_then_universe_median"
    assert protocol.clipping.endswith("percentile_1_99_linear")
    assert protocol.zscore_ddof == 0
    assert protocol.additional_scaling == "NONE"
    assert "NO_SAMPLE_NORMALIZATION" in protocol.solver_contract
    assert "ASSUME_A_POS" in protocol.solver_contract
    assert "NO_FALLBACK" in protocol.solver_contract
    assert protocol.refit_protocol == g1.T0_REFIT_PROTOCOL
    assert protocol.fold_validation_window_rule == g1.T0_FOLD_VALIDATION_WINDOW_RULE
    assert protocol.timestamp_rule == g1.T0_TIMESTAMP_RULE
    assert protocol.row_id_rule == g1.T0_ROW_ID_RULE
    assert protocol.purge_decision_rows == "ALWAYS_EXCLUDED"
    assert protocol.calibration_alpha_reselection == "FORBIDDEN"
    assert protocol.g1_bootstrap_primitive == g1.G1_BOOTSTRAP_PRIMITIVE
    assert protocol.g1_bootstrap_domain_seed_rule == g1.G1_BOOTSTRAP_DOMAIN_SEED_RULE
    assert protocol.governing_cost_cell_rule == g1.G1_GOVERNING_COST_CELL_RULE
    assert protocol.gate_reconciliation_rule == g1.G1_GATE_RECONCILIATION_RULE
    assert protocol.pre_execution_power_prediction_rule == g1.G1_PRE_EXECUTION_POWER_PREDICTION_RULE
    assert protocol.continue_evidential_weight_rule == g1.G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE
    assert protocol.sandwich_reporting_rule == g1.G1_SANDWICH_REPORTING_RULE
    assert protocol.bound_certificate_decision_id_rule == g1.G1_BOUND_CERTIFICATE_DECISION_ID_RULE
    assert protocol.bound_certificate_root_rule == g1.G1_BOUND_CERTIFICATE_ROOT_RULE
    assert protocol.stage2_asset_access_rule == g1.G1_STAGE2_ASSET_ACCESS_RULE
    assert protocol.market_universe_ticker_rule == g1.G1_MARKET_UNIVERSE_TICKER_RULE
    assert protocol.feature_formula_contract == g1.T0_FEATURE_FORMULA_CONTRACT
    assert g1.T0_RAW_FEATURE_FORMULA_RULE == ("FLOAT64_LOG_RETURN_WINDOWS_SR_SUM_VOL_DDOF0_DOWNSIDE_ZERO_SEALED_SECTOR_BETA_EXPLICIT_DEPARTURE_" "TO_UNIVERSE_BETA_VALID_NAMES_MIN1_SPLIT_ADJUSTED_CLOSE_ASSUMED_UNCERTIFIED_LOG_DOLLAR_VOLUME_" "LOG_MEAN_VOLUME_RATIO_V2")
    assert g1.T0_LABEL_FORMULA_RULE == "H5_SIMPLE_RETURN_MINUS_SAME_SESSION_EQUAL_WEIGHT_SECTOR_MEAN_V1"
    assert g1.T0_RAW_MISSING_RULE == ("COMPLETE_WINDOW_REQUIRED_INVALID_NONFINITE_OR_NONPOSITIVE_INPUT_AND_ZERO_BETA_DENOMINATOR_ARE_MISSING_V1")
    assert protocol.raw_feature_formula_rule == g1.T0_RAW_FEATURE_FORMULA_RULE
    assert protocol.label_formula_rule == g1.T0_LABEL_FORMULA_RULE
    assert protocol.raw_missing_rule == g1.T0_RAW_MISSING_RULE
    assert protocol.protocol_sha256 == "b754d194339d0a4131d0832785991b2360d83513f99ff86379ffdcf898e29e53"
    assert canonical_sha256(protocol.model_dump(mode="json", exclude={"protocol_sha256"})) == protocol.protocol_sha256
    amendment_path = Path(__file__).resolve().parents[1] / g1.T0_FEATURE_FORMULA_AMENDMENT_PATH
    assert hashlib.sha256(amendment_path.read_bytes()).hexdigest() == g1.T0_FEATURE_FORMULA_AMENDMENT_SHA256
    reconciliation_path = Path(__file__).resolve().parents[1] / g1.G1_GATE_RECONCILIATION_AMENDMENT_PATH
    assert hashlib.sha256(reconciliation_path.read_bytes()).hexdigest() == g1.G1_GATE_RECONCILIATION_AMENDMENT_SHA256
    amendment = reconciliation_path.read_text(encoding="utf-8")
    assert "H_clairvoyant = U_clairvoyant_feasible - U_B0" in amendment
    assert "G1 calibration `U_clairvoyant_feasible - U_T0`" in amendment
    assert "G1 is expected to return" in amendment
    assert "band_undetermined: true" in amendment
    assert "before any G1 number or output existed" in amendment


def test_preprocessing_is_impute_clip_demean_zscore_with_unscaled_missing_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    rows = {
        "A": {feature: 1.0 for feature in g1.T0_BASE_FEATURES},
        "B": {feature: 3.0 for feature in g1.T0_BASE_FEATURES},
        "C": {feature: None for feature in g1.T0_BASE_FEATURES},
    }
    transformed = g1.preprocess_t0_cross_section(rows, {"A": "S1", "B": "S1", "C": "S2"})
    assert tuple(transformed) == ("A", "B", "C")
    assert all(len(values) == 18 for values in transformed.values())
    for values in transformed.values():
        assert all(math.isfinite(value) for value in values)
    assert transformed["A"][1::2] == (0.0,) * 9
    assert transformed["B"][1::2] == (0.0,) * 9
    assert transformed["C"][1::2] == (1.0,) * 9


def test_alpha_selection_minimizes_over_all_twelve_cells_then_larger_alpha() -> None:
    selection = g1.select_t0_alpha(_utilities(), _candidate_runs())
    assert selection.selected_t0_alpha_e1 == 1000
    assert g1.t0_alpha_from_e1(selection.selected_t0_alpha_e1) == 100.0
    assert all(len(candidate.cell_utility_e12) == 12 for candidate in selection.candidates)
    broken = _utilities()
    del broken[1][(2017, 5)]
    with pytest.raises(g1.R03G1PreparationError, match="fold x cost"):
        g1.select_t0_alpha(broken, _candidate_runs())
    with pytest.raises(g1.R03G1PreparationError, match="outside the frozen grid"):
        g1.t0_alpha_from_e1(2)


def test_t_minus_one_exact_h5_maturity_and_purge_exclusion() -> None:
    base = datetime(2022, 12, 1, 15, tzinfo=timezone.utc)
    bad_feature = _row("bad-feature", base, 100).model_dump()
    bad_feature["feature_session_ordinal"] = 100
    with pytest.raises(ValidationError, match="t-1"):
        g1.T0FitRowMetadata(**bad_feature)
    bad_label = _row("bad-label", base, 100).model_dump()
    bad_label["label_session_ordinal"] = 106
    with pytest.raises(ValidationError, match="exact matured h=5"):
        g1.T0FitRowMetadata(**bad_label)

    rows = tuple(
        sorted(
            (
                _row("development", base, 100, matured_at=base + timedelta(days=5)),
                _row(
                    "purge-2022-12-23",
                    datetime(2022, 12, 23, 15, tzinfo=timezone.utc),
                    101,
                    split="PURGE_2",
                    matured_at=datetime(2022, 12, 30, 14, tzinfo=timezone.utc),
                ),
                _row(
                    "purge-2022-12-27",
                    datetime(2022, 12, 27, 15, tzinfo=timezone.utc),
                    102,
                    split="PURGE_2",
                    matured_at=datetime(2023, 1, 3, 14, tzinfo=timezone.utc),
                ),
                _row(
                    "calibration-matured-at-cutoff",
                    datetime(2022, 12, 20, 15, tzinfo=timezone.utc),
                    103,
                    split="CALIBRATION",
                    matured_at=datetime(2023, 1, 3, 15, 30, tzinfo=timezone.utc),
                ),
                _row(
                    "calibration-unmatured",
                    datetime(2022, 12, 21, 15, tzinfo=timezone.utc),
                    104,
                    split="CALIBRATION",
                    matured_at=datetime(2023, 1, 3, 15, 31, tzinfo=timezone.utc),
                ),
            ),
            key=lambda row: (row.decision_at, row.row_id),
        )
    )
    refit = datetime(2023, 1, 3, 15, 30, tzinfo=timezone.utc)
    selected = g1.eligible_fit_indices(rows, refit_at=refit, stage="CALIBRATION")
    assert tuple(rows[index].row_id for index in selected) == (
        "development",
        "calibration-matured-at-cutoff",
    )


def test_training_frame_uses_float64_and_int64_component_hashes_without_json_floats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    decisions = [datetime(2020, 1, 2 + index, 15, tzinfo=timezone.utc) for index in range(3)]
    rows = tuple(_row(f"r{index}", decision, 10 + index) for index, decision in enumerate(decisions))
    identity = g1.build_training_frame_identity(rows, _matrix(3), (1, 2, 3))
    dumped = identity.model_dump(mode="json")
    assert identity.feature_count == 18
    assert all(not isinstance(value, float) for value in dumped.values())
    assert canonical_sha256(dumped)
    with pytest.raises(g1.R03G1PreparationError, match="e12 integers"):
        g1.build_training_frame_identity(rows, _matrix(3), (1, 2.0, 3))  # type: ignore[arg-type]


def test_snapshot_persistence_and_same_runtime_bitwise_determinism(monkeypatch: pytest.MonkeyPatch) -> None:
    refit = datetime(2021, 1, 4, 15, 30, tzinfo=timezone.utc)
    first = _snapshot(monkeypatch, refit)
    second = _snapshot(monkeypatch, refit)
    assert first == second
    assert len(first.coefficient_float64_le_hex) == 18 * 16
    assert len(bytes.fromhex(first.intercept_float64_le_hex)) == 8
    assert canonical_sha256(first.model_dump(mode="json"))
    predictions = g1.predict_t0(first, _matrix(2))
    assert predictions.dtype.name == "float64"
    assert predictions.tobytes() == g1.predict_t0(second, _matrix(2)).tobytes()
    serialized = json.loads(first.model_dump_json())
    assert all(not isinstance(value, float) for value in serialized.values())


def test_thread_contract_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _pin_threads(monkeypatch)
    assert g1.assert_single_thread_environment() == tuple(f"{key}=1" for key in g1.THREAD_ENV_KEYS)
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "2")
    with pytest.raises(g1.R03G1PreparationError, match="thread controls"):
        g1.assert_single_thread_environment()


def test_monthly_intervals_are_half_open_unique_gapless_and_nonfuture(monkeypatch: pytest.MonkeyPatch) -> None:
    january = datetime(2021, 1, 4, 15, 30, tzinfo=timezone.utc)
    february = datetime(2021, 2, 1, 15, 30, tzinfo=timezone.utc)
    decisions = (
        january,
        january + timedelta(days=7),
        february,
        february + timedelta(days=7),
    )
    snapshots = (_snapshot(monkeypatch, january), _snapshot(monkeypatch, february))
    end = datetime(2021, 3, 1, 15, 30, tzinfo=timezone.utc)
    series = g1.build_t0_model_series(
        snapshots,
        coverage_decisions=decisions,
        coverage_end_exclusive_at=end,
    )
    assert series.intervals[0].effective_from == january
    assert series.intervals[0].effective_until == february
    assert g1.serving_snapshot(series, january).t0_snapshot_id == snapshots[0].t0_snapshot_id
    assert g1.serving_snapshot(series, february).t0_snapshot_id == snapshots[1].t0_snapshot_id
    with pytest.raises(g1.R03G1PreparationError, match="one nonfuture"):
        g1.serving_snapshot(series, end)

    intervals = list(series.intervals)
    intervals[1] = g1.T0SnapshotInterval(
        effective_from=february + timedelta(minutes=1),
        effective_until=intervals[1].effective_until,
        t0_snapshot_id=intervals[1].t0_snapshot_id,
    )
    with pytest.raises(ValidationError, match="refit/effective|overlap or leave a gap"):
        g1.T0ModelSeriesIdentity(
            schema_version=series.schema_version,
            execution_status=series.execution_status,
            t0_protocol_id=series.t0_protocol_id,
            alpha_selection_sha256=series.alpha_selection_sha256,
            t0_alpha_e1=series.t0_alpha_e1,
            coverage_start_at=series.coverage_start_at,
            coverage_end_exclusive_at=series.coverage_end_exclusive_at,
            coverage_decision_count=series.coverage_decision_count,
            coverage_decisions_sha256=series.coverage_decisions_sha256,
            snapshots=series.snapshots,
            intervals=tuple(intervals),
            t0_model_series_id="0" * 64,
        )


def test_calibration_series_refits_monthly_with_fixed_alpha_and_only_matured_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    development_times = (
        datetime(2020, 12, 1, 15, 30, tzinfo=timezone.utc),
        datetime(2020, 12, 2, 15, 30, tzinfo=timezone.utc),
        datetime(2020, 12, 3, 15, 30, tzinfo=timezone.utc),
        datetime(2020, 12, 4, 15, 30, tzinfo=timezone.utc),
    )
    calibration_decisions = (
        datetime(2021, 1, 4, 15, 30, tzinfo=timezone.utc),
        datetime(2021, 1, 11, 15, 30, tzinfo=timezone.utc),
        datetime(2021, 2, 1, 15, 30, tzinfo=timezone.utc),
        datetime(2021, 2, 8, 15, 30, tzinfo=timezone.utc),
    )
    rows = []
    for index, decision in enumerate(development_times):
        rows.append(
            _row(
                f"development-{index}",
                decision,
                100 + index,
                matured_at=decision + timedelta(days=10),
            )
        )
    for index, decision in enumerate(calibration_decisions):
        rows.append(
            _row(
                f"calibration-{index}",
                decision,
                200 + index,
                split="CALIBRATION",
                matured_at=decision + timedelta(days=10),
            )
        )
    rows = sorted(rows, key=lambda row: (row.decision_at, row.row_id))
    matrix = _matrix(len(rows))
    targets = tuple((index + 1) * 10_000_000 for index in range(len(rows)))
    selection = g1.select_t0_alpha(_utilities(), _candidate_runs())
    runtime = g1.installed_t0_runtime_identity()
    series = g1.fit_t0_calibration_series(
        rows,
        matrix,
        targets,
        calibration_decisions=calibration_decisions,
        coverage_end_exclusive_at=datetime(2021, 3, 1, 15, 30, tzinfo=timezone.utc),
        alpha_selection=selection,
        runtime=runtime,
    )
    assert tuple(snapshot.refit_at for snapshot in series.snapshots) == (
        calibration_decisions[0],
        calibration_decisions[2],
    )
    assert {snapshot.t0_alpha_e1 for snapshot in series.snapshots} == {selection.selected_t0_alpha_e1}
    assert series.snapshots[0].training_frame_sha256 != series.snapshots[1].training_frame_sha256
    assert g1.serving_snapshot(series, calibration_decisions[1]) == series.snapshots[0]
    assert g1.serving_snapshot(series, calibration_decisions[3]) == series.snapshots[1]


def test_development_candidate_uses_the_same_monthly_expanding_solver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    training_times = tuple(datetime(2016, 1, 4 + index, 15, 30, tzinfo=timezone.utc) for index in range(4))
    validation_decisions = (
        datetime(2017, 1, 3, 15, 30, tzinfo=timezone.utc),
        datetime(2017, 1, 10, 15, 30, tzinfo=timezone.utc),
        datetime(2017, 2, 1, 15, 30, tzinfo=timezone.utc),
        datetime(2017, 2, 8, 15, 30, tzinfo=timezone.utc),
    )
    rows = []
    for index, decision in enumerate(training_times + validation_decisions):
        rows.append(
            _row(
                f"development-{index}",
                decision,
                300 + index,
                matured_at=decision + timedelta(days=10),
            )
        )
    rows = sorted(rows, key=lambda row: (row.decision_at, row.row_id))
    matrix = _matrix(len(rows))
    targets = tuple((index + 1) * 15_000_000 for index in range(len(rows)))
    runtime = g1.installed_t0_runtime_identity()
    first, predictions = g1.fit_t0_development_fold_candidate(
        rows,
        matrix,
        targets,
        validation_decisions=validation_decisions,
        fold_end_year=2017,
        t0_alpha_e1=1,
        runtime=runtime,
    )
    second, _ = g1.fit_t0_development_fold_candidate(
        rows,
        matrix,
        targets,
        validation_decisions=validation_decisions,
        fold_end_year=2017,
        t0_alpha_e1=10,
        runtime=runtime,
    )
    assert len(first.training_frame_sha256) == 2
    assert first.prediction_row_count == len(validation_decisions)
    assert set(predictions) == {f"development-{index}" for index in range(len(training_times), len(training_times + validation_decisions))}
    assert first.coefficient_sha256 != second.coefficient_sha256
    assert canonical_sha256(first.model_dump(mode="json"))


def test_model_series_reuse_and_workload_count() -> None:
    g1.assert_g2_reuses_t0_series("a" * 64, "a" * 64)
    with pytest.raises(g1.R03G1PreparationError, match="exact G1 T0"):
        g1.assert_g2_reuses_t0_series("a" * 64, "b" * 64)
    estimate = g1.estimate_development_fit_count({2017: 12, 2018: 12, 2019: 12, 2020: 12})
    assert estimate.expected_fit_count == 4 * 48


def test_seed_is_commit_derived_and_not_a_stored_value() -> None:
    commit = "a" * 40
    assert g1.derive_g1_seed(commit) == g1.derive_g1_seed(commit)
    assert g1.derive_g1_seed(commit) != g1.derive_g1_seed("b" * 40)
    with pytest.raises(g1.R03G1PreparationError, match="commit"):
        g1.derive_g1_seed("A" * 40)
    source = inspect.getsource(g1)
    assert "G1_SEED_SHA256 =" not in source


def test_synthetic_g1_record_uses_all_cost_cells_and_zero_forbidden_counters(monkeypatch: pytest.MonkeyPatch) -> None:
    _pin_threads(monkeypatch)
    record = g1.evaluate_g1_cost_cells(
        {
            5: (100_000_000,) * 8,
            10: (200_000_000,) * 8,
            15: (300_000_000,) * 8,
        },
        greedy_feasible_lower_by_cost_e12={5: 0, 10: 0, 15: 0},
        preparation_commit_sha="a" * 40,
        t0_model_series_id="b" * 64,
        bound_certificate_root_sha256="c" * 64,
        thread_environment_preconfigured_before_process_start=True,
    )
    assert record.label == "STOP_NO_ECONOMIC_HEADROOM"
    assert record.governing_cost_bps_per_side == 15
    assert record.t0_protocol_id == g1.t0_protocol_identity().protocol_sha256
    assert record.g1_bootstrap_primitive == g1.G1_BOOTSTRAP_PRIMITIVE
    assert record.g1_bootstrap_domain_seed_rule == g1.G1_BOOTSTRAP_DOMAIN_SEED_RULE
    assert record.governing_cost_cell_rule == g1.G1_GOVERNING_COST_CELL_RULE
    assert record.gate_reconciliation_rule == g1.G1_GATE_RECONCILIATION_RULE
    assert record.pre_execution_power_prediction_rule == g1.G1_PRE_EXECUTION_POWER_PREDICTION_RULE
    assert record.continue_evidential_weight_rule == g1.G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE
    assert record.sandwich_reporting_rule == g1.G1_SANDWICH_REPORTING_RULE
    assert record.bound_certificate_root_rule == g1.G1_BOUND_CERTIFICATE_ROOT_RULE
    assert tuple(cell.cost_bps_per_side for cell in record.power_disclosure_cells) == g1.T0_COST_CELLS_BPS
    assert record.power_disclosure_cells[-1].decision_band_width_e12 == 300_000_000
    assert record.band_undetermined is False
    assert record.thread_environment_preconfigured_before_process_start is True
    assert record.raw_news_access_attempts == 0
    assert record.provider_calls == record.network_attempts == 0
    assert canonical_sha256(record.model_dump(mode="json"))


def test_synthetic_g1_record_discloses_undetermined_middle_band(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    record = g1.evaluate_g1_cost_cells(
        {cost: (1_000_000_000,) * 8 for cost in g1.T0_COST_CELLS_BPS},
        greedy_feasible_lower_by_cost_e12={cost: 0 for cost in g1.T0_COST_CELLS_BPS},
        preparation_commit_sha="a" * 40,
        t0_model_series_id="b" * 64,
        bound_certificate_root_sha256="c" * 64,
        thread_environment_preconfigured_before_process_start=True,
    )
    assert record.label == "G1_CONTINUE_NO_FUTILITY_PROOF"
    assert record.band_undetermined is True
    assert all(cell.band_undetermined for cell in record.power_disclosure_cells)
    assert all(not cell.lower_exceeds_delta_star for cell in record.power_disclosure_cells)
    assert all(not cell.upper_95_at_or_below_delta_star for cell in record.power_disclosure_cells)

    headroom_record = g1.evaluate_g1_cost_cells(
        {cost: (1_000_000_000,) * 8 for cost in g1.T0_COST_CELLS_BPS},
        greedy_feasible_lower_by_cost_e12={cost: 800_000_000 for cost in g1.T0_COST_CELLS_BPS},
        preparation_commit_sha="a" * 40,
        t0_model_series_id="b" * 64,
        bound_certificate_root_sha256="c" * 64,
        thread_environment_preconfigured_before_process_start=True,
    )
    assert headroom_record.label == "G1_CONTINUE_NO_FUTILITY_PROOF"
    assert headroom_record.band_undetermined is False
    assert all(cell.lower_exceeds_delta_star for cell in headroom_record.power_disclosure_cells)


def test_g1_bootstrap_delegates_exactly_to_sealed_headroom_primitive(monkeypatch: pytest.MonkeyPatch) -> None:
    _pin_threads(monkeypatch)
    from v2.research.news_reasoning.r03_headroom import stationary_bootstrap_means_e12

    values = (10_000_000_000, 20_000_000_000, 30_000_000_000, 40_000_000_000)
    seed_sha256 = "d" * 64
    label = f"{g1.G1_SEED_DOMAIN}:COST_BPS=5"
    expected = stationary_bootstrap_means_e12(
        values,
        seed_sha256=seed_sha256,
        label=label,
        resamples=g1.G1_RESAMPLES,
        block_length=g1.G1_BLOCK_LENGTH,
    )
    assert g1._stationary_bootstrap_means_e12(values, seed_sha256=seed_sha256, label=label) == expected


def test_numeric_runtime_initialization_and_flake8_gate_are_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    _pin_threads(monkeypatch)
    first = g1.initialize_t0_numeric_runtime()
    second = g1.initialize_t0_numeric_runtime()
    assert first.runtime_sha256 == second.runtime_sha256
    assert first.thread_environment_contract == g1.T0_THREAD_ENVIRONMENT_CONTRACT
    assert g1.R03_FLAKE8_EXTEND_IGNORE == ("E203",)


def test_clean_process_initializes_after_package_import_when_thread_env_is_preconfigured() -> None:
    environment = os.environ.copy()
    for key in g1.THREAD_ENV_KEYS:
        environment[key] = "1"
    script = "import v2.research.news_reasoning.r03_g1_execution as g1; " "runtime = g1.initialize_t0_numeric_runtime(); " "assert runtime.thread_environment_contract == " "'PRECONFIGURED_BEFORE_PROCESS_START'"
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


def test_module_has_no_raw_news_provider_network_or_top_level_numeric_imports() -> None:
    module_path = Path(inspect.getsourcefile(g1) or "")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "v2.research.news_reasoning.r03_source",
        "v2.research.news_reasoning.r03_payload",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "subprocess",
        "openai",
        "anthropic",
    }
    assert imported.isdisjoint(forbidden)
    top_level_imports = {alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names}
    assert "numpy" not in top_level_imports
    assert "scipy" not in top_level_imports
    public_refit_functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("fit_")}
    assert public_refit_functions == {
        "fit_t0_calibration_series",
        "fit_t0_development_fold_candidate",
    }
