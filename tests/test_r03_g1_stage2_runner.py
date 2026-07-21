from __future__ import annotations

import ast
import hashlib
import inspect
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import mock_open

import pytest
from pydantic import ValidationError

import v2.research.news_reasoning.r03_g1_execution as g1
import v2.research.news_reasoning.r03_g1_stage2_runner as runner
from v2.research.overlay.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / ".research_artifacts/r03-news-reasoning/universe-snapshot-v1.json"
INCIDENT_PATH = ROOT / ".research_artifacts/r03-news-reasoning/g1-stage2-incident-01.json"
AGGREGATE_INCIDENT_PATH = ROOT / ".research_artifacts/r03-news-reasoning/g1-stage2-aggregate-construction-incident-01.json"
FORMULA_AMENDMENT_PATH = ROOT / "docs/r03-news-reasoning-t0-feature-formula-amendment.md"
RECONCILIATION_AMENDMENT_PATH = ROOT / "docs/r03-news-reasoning-g1-gate-definition-reconciliation-amendment.md"


def _pin_threads(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in g1.THREAD_ENV_KEYS:
        monkeypatch.setenv(key, "1")
    runtime = g1.installed_t0_runtime_identity()
    monkeypatch.setattr(g1, "_T0_RUNTIME_CACHE", runtime)


def test_protocol_binds_exact_external_assets_internal_universe_and_ordinal_clock() -> None:
    protocol = runner.stage2_runner_protocol_identity()
    assert protocol.schema_version == "r03-g1-stage2-runner-protocol-v2"
    assert tuple(pin.role for pin in protocol.external_asset_pins) == ("MARKET_BARS",)
    assert tuple(pin.absolute_path for pin in protocol.external_asset_pins) == (runner.MARKET_BARS_PATH,)
    assert protocol.asset_access_rule == g1.G1_STAGE2_ASSET_ACCESS_RULE
    assert protocol.session_ordinal_rule == g1.G1_SESSION_ORDINAL_RULE
    assert protocol.market_universe_ticker_rule == g1.G1_MARKET_UNIVERSE_TICKER_RULE
    assert protocol.nominal_decision_time == runner.NOMINAL_DECISION_TIME
    assert protocol.real_early_close_schedule_in_scope is False
    assert protocol.gate_reconciliation_rule == g1.G1_GATE_RECONCILIATION_RULE
    assert protocol.pre_execution_power_prediction_rule == g1.G1_PRE_EXECUTION_POWER_PREDICTION_RULE
    assert protocol.continue_evidential_weight_rule == g1.G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE
    assert protocol.sandwich_reporting_rule == g1.G1_SANDWICH_REPORTING_RULE
    assert protocol.bound_certificate_root_rule == g1.G1_BOUND_CERTIFICATE_ROOT_RULE
    assert protocol.driver_entrypoint == "run_g1_stage2"
    assert protocol.aggregate_output_path == runner.G1_AGGREGATE_OUTPUT_PATH
    assert protocol.aggregate_serialization_rule == runner.G1_AGGREGATE_SERIALIZATION_RULE
    assert protocol.t0_protocol_id == runner.G1_REVIEWED_T0_PROTOCOL_ID
    assert protocol.runner_protocol_sha256 == runner.G1_REVIEWED_STAGE2_RUNNER_PROTOCOL_ID
    assert protocol.universe_source_path not in {pin.absolute_path for pin in protocol.external_asset_pins}
    with pytest.raises(runner.R03G1Stage2AccessError, match="unknown Stage 2 asset role"):
        runner.stage2_asset_pin("ARTICLE_EVENTS")
    assert canonical_sha256(protocol.model_dump(mode="json", exclude={"runner_protocol_sha256"})) == protocol.runner_protocol_sha256


def test_internal_universe_snapshot_is_minimal_sorted_and_hash_pinned() -> None:
    snapshot_text = SNAPSHOT_PATH.read_text(encoding="utf-8")
    payload = json.loads(snapshot_text)
    snapshot = runner.UniverseSnapshot.model_validate_json(snapshot_text)
    assert len(snapshot.ticker_sector_mapping) == 100
    assert tuple(entry.ticker for entry in snapshot.ticker_sector_mapping) == tuple(sorted(entry.ticker for entry in snapshot.ticker_sector_mapping))
    assert snapshot.source_sha256 == g1.T0_UNIVERSE_SOURCE_SHA256
    assert snapshot.snapshot_sha256 == g1.T0_UNIVERSE_SNAPSHOT_SHA256
    assert set(payload) == {
        "schema_version",
        "source_path",
        "source_sha256",
        "ticker_sector_mapping",
        "snapshot_sha256",
    }


def test_universe_snapshot_mutations_fail_closed() -> None:
    payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    payload["ticker_sector_mapping"][0]["sector"] = "MUTATED"
    with pytest.raises(runner.R03G1Stage2AccessError, match="snapshot hash"):
        runner.UniverseSnapshot.model_validate_json(json.dumps(payload))
    payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    payload["source_sha256"] = "0" * 64
    with pytest.raises(runner.R03G1Stage2AccessError, match="source hash"):
        runner.UniverseSnapshot.model_validate_json(json.dumps(payload))


def test_formula_amendment_and_protocol_rules_are_hash_pinned() -> None:
    assert hashlib.sha256(FORMULA_AMENDMENT_PATH.read_bytes()).hexdigest() == g1.T0_FEATURE_FORMULA_AMENDMENT_SHA256
    protocol = g1.t0_protocol_identity()
    assert protocol.feature_formula_contract == "R03_T0_FEATURE_FORMULA_AMENDMENT_V1"
    assert protocol.feature_formula_amendment_path == ("docs/r03-news-reasoning-t0-feature-formula-amendment.md")
    assert protocol.raw_feature_formula_rule == g1.T0_RAW_FEATURE_FORMULA_RULE
    assert protocol.label_formula_rule == g1.T0_LABEL_FORMULA_RULE
    assert protocol.raw_missing_rule == g1.T0_RAW_MISSING_RULE
    assert hashlib.sha256(RECONCILIATION_AMENDMENT_PATH.read_bytes()).hexdigest() == g1.G1_GATE_RECONCILIATION_AMENDMENT_SHA256
    amendment = RECONCILIATION_AMENDMENT_PATH.read_text(encoding="utf-8")
    assert g1.G1_PRE_EXECUTION_POWER_PREDICTION_RULE in amendment
    assert g1.G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE in amendment
    assert g1.G1_SANDWICH_REPORTING_RULE in amendment


def test_frozen_fold_timestamp_row_and_certificate_conventions() -> None:
    decisions = tuple(datetime(year, month, day, 15, 30, tzinfo=timezone.utc) for year in g1.T0_FOLD_END_YEARS for month, day in ((1, 2), (12, 29)))
    windows = runner._fold_validation_windows(decisions)
    assert tuple(window.fold_end_year for window in windows) == g1.T0_FOLD_END_YEARS
    assert tuple(window.decision_count for window in windows) == (2, 2, 2, 2)
    assert tuple(window.first_validation_at.month for window in windows) == (1, 1, 1, 1)
    assert tuple(window.last_validation_at.month for window in windows) == (12, 12, 12, 12)
    decision_date = decisions[0].date()
    assert runner.t0_row_id("DEVELOPMENT", 7, decision_date, "AAPL") == "DEVELOPMENT|000007|2017-01-02|AAPL"
    assert runner.g1_bound_decision_id(7, decision_date) == "CALIBRATION|000007|2017-01-02"


def test_disallowed_raw_news_path_is_rejected_before_filesystem_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counters = runner.Stage2AccessCounters()

    def forbidden_resolution(*args, **kwargs):
        raise AssertionError("disallowed path reached filesystem resolution")

    monkeypatch.setattr(Path, "resolve", forbidden_resolution)
    with pytest.raises(runner.R03G1Stage2AccessError, match="exact allowlist"):
        runner.load_stage2_asset(
            "MARKET_BARS",
            "C:/Users/User/Desktop/FinGPT/data/news_preflight/AAPL_2025/page_0032.json",
            counters,
        )
    assert counters.raw_news_access_attempts == 1
    assert counters.disallowed_path_attempts == 1
    assert counters.allowed_asset_reads == 0


def test_prefix_and_relative_path_near_misses_fail_closed() -> None:
    for near_miss in (
        "C:/Users/User/Desktop/FinGPT/data/raw",
        "C:/Users/User/Desktop/FinGPT/data/raw/market_bars_real.parquet.bak",
        "data/raw/market_bars_real.parquet",
    ):
        counters = runner.Stage2AccessCounters()
        with pytest.raises(runner.R03G1Stage2AccessError, match="exact allowlist"):
            runner.load_stage2_asset("MARKET_BARS", near_miss, counters)
        assert counters.disallowed_path_attempts == 1
        assert counters.raw_news_access_attempts == 1
        assert counters.allowed_asset_reads == 0


def test_resolved_path_alias_is_rejected_before_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counters = runner.Stage2AccessCounters()
    monkeypatch.setattr(
        Path,
        "resolve",
        lambda self, strict=True: Path("C:/Users/User/Desktop/FinGPT/alias.parquet"),
    )
    with pytest.raises(runner.R03G1Stage2AccessError, match="resolved asset path"):
        runner.load_stage2_asset(
            "MARKET_BARS",
            runner.MARKET_BARS_PATH,
            counters,
        )
    assert counters.disallowed_path_attempts == 1
    assert counters.allowed_asset_reads == 0


def test_hash_mismatch_stops_before_parquet_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counters = runner.Stage2AccessCounters()
    monkeypatch.setattr(
        Path,
        "resolve",
        lambda self, strict=True: Path(runner.MARKET_BARS_PATH),
    )
    monkeypatch.setattr("builtins.open", mock_open(read_data=b"mutated"))

    def forbidden_decode(*args, **kwargs):
        raise AssertionError("hash mismatch reached parquet decoder")

    import pyarrow.parquet as parquet

    monkeypatch.setattr(parquet, "read_table", forbidden_decode)
    with pytest.raises(runner.R03G1Stage2AccessError, match="content hash"):
        runner.load_stage2_asset(
            "MARKET_BARS",
            runner.MARKET_BARS_PATH,
            counters,
        )
    assert counters.allowed_asset_reads == 0


def test_synthetic_gateway_success_returns_aggregate_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pyarrow as pa
    import pyarrow.parquet as parquet

    payload_bytes = b"synthetic parquet bytes"
    synthetic_table = pa.table(
        {
            "ticker": pa.array(["AAPL"], type=pa.string()),
            "timestamp": pa.array([0], type=pa.timestamp("ns", tz="UTC")),
            "open": pa.array([1.0], type=pa.float64()),
            "high": pa.array([1.0], type=pa.float64()),
            "low": pa.array([1.0], type=pa.float64()),
            "close": pa.array([1.0], type=pa.float64()),
            "volume": pa.array([1], type=pa.int64()),
        }
    )
    synthetic_pin = runner.Stage2AssetPin(
        role="MARKET_BARS",
        location="EXTERNAL",
        absolute_path=runner.MARKET_BARS_PATH,
        sha256=hashlib.sha256(payload_bytes).hexdigest(),
    )
    monkeypatch.setattr(runner, "stage2_asset_pin", lambda role: synthetic_pin)
    monkeypatch.setattr(
        Path,
        "resolve",
        lambda self, strict=True: Path(runner.MARKET_BARS_PATH),
    )
    monkeypatch.setattr("builtins.open", mock_open(read_data=payload_bytes))
    decoded_bytes: list[bytes] = []

    def _decode_verified_buffer(source: object, *args: object, **kwargs: object) -> object:
        assert isinstance(source, pa.BufferReader)
        decoded_bytes.append(source.read())
        return synthetic_table

    monkeypatch.setattr(parquet, "read_table", _decode_verified_buffer)
    counters = runner.Stage2AccessCounters()
    loaded = runner.load_stage2_asset(
        "MARKET_BARS",
        runner.MARKET_BARS_PATH,
        counters,
    )
    assert loaded.payload is synthetic_table
    assert loaded.receipt.row_count == 1
    assert loaded.receipt.byte_count == len(payload_bytes)
    assert loaded.receipt.column_names == (
        "ticker",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    )
    assert counters.allowed_asset_reads == 1
    assert counters.disallowed_path_attempts == 0
    assert decoded_bytes == [payload_bytes]


def test_zero_call_manifest_refuses_any_contaminated_counter() -> None:
    clean = runner.Stage2AccessCounters()
    manifest = runner.build_zero_call_manifest(clean)
    assert manifest.raw_news_access_attempts == 0
    assert canonical_sha256(manifest.model_dump(mode="json", exclude={"manifest_sha256"})) == manifest.manifest_sha256
    dirty = runner.Stage2AccessCounters(raw_news_access_attempts=1)
    with pytest.raises(runner.R03G1Stage2AccessError, match="contaminated"):
        runner.build_zero_call_manifest(dirty)


def test_synthetic_market_and_article_schemas(monkeypatch: pytest.MonkeyPatch) -> None:
    _pin_threads(monkeypatch)
    import pyarrow as pa

    market = pa.table(
        {
            "ticker": pa.array(["AAPL"], type=pa.string()),
            "timestamp": pa.array([0], type=pa.timestamp("ns", tz="UTC")),
            "open": pa.array([1.0], type=pa.float64()),
            "high": pa.array([1.0], type=pa.float64()),
            "low": pa.array([1.0], type=pa.float64()),
            "close": pa.array([1.0], type=pa.float64()),
            "volume": pa.array([1], type=pa.int64()),
        }
    )
    assert runner._validate_market_bars_table(market) == (
        1,
        ("ticker", "timestamp", "open", "high", "low", "close", "volume"),
    )
    article = pa.table(
        {
            "ticker": pa.array(["AAPL"]),
            "published_at": pa.array([0], type=pa.timestamp("ns", tz="UTC")),
        }
    )
    assert runner._validate_article_events_table(article)[0] == 1
    raw_article = article.append_column("headline", pa.array(["forbidden"]))
    with pytest.raises(runner.R03G1Stage2AccessError, match="raw-text"):
        runner._validate_article_events_table(raw_article)


def test_market_universe_requires_exact_ticker_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    import pyarrow as pa

    snapshot = runner.UniverseSnapshot.model_validate_json(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    exact = pa.table({"ticker": pa.array([entry.ticker for entry in snapshot.ticker_sector_mapping])})
    runner._assert_exact_market_universe_tickers(exact, snapshot)
    same_count_wrong_set = pa.table({"ticker": pa.array([entry.ticker for entry in snapshot.ticker_sector_mapping[1:]] + ["ZZZZ"])})
    with pytest.raises(runner.R03G1Stage2AccessError, match="ticker sets"):
        runner._assert_exact_market_universe_tickers(same_count_wrong_set, snapshot)


def test_pyarrow_runtime_identity_binds_numeric_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    identity = runner.installed_stage2_io_runtime_identity()
    assert identity.pyarrow_version
    assert identity.t0_numeric_runtime_sha256 == g1.initialize_t0_numeric_runtime().runtime_sha256
    assert canonical_sha256(identity.model_dump(mode="json", exclude={"runtime_sha256"})) == identity.runtime_sha256


def test_runner_has_one_read_gateway_one_exclusive_writer_and_no_recursive_discovery_surface() -> None:
    module_path = Path(inspect.getsourcefile(runner) or "")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    io_owners: dict[str, set[str]] = {}
    forbidden_calls = {"glob", "iglob", "rglob", "walk"}
    seen_forbidden = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        calls = set()
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if isinstance(child.func, ast.Name):
                name = child.func.id
            elif isinstance(child.func, ast.Attribute):
                name = child.func.attr
            else:
                continue
            if name in {"open", "read_table", "resolve"}:
                calls.add(name)
            if name in forbidden_calls:
                seen_forbidden.add(name)
        if calls:
            io_owners[node.name] = calls
    assert io_owners == {
        "_write_g1_stage2_aggregate": {"open"},
        "load_stage2_asset": {"open", "read_table", "resolve"},
    }
    assert seen_forbidden == set()
    assert 'open("xb")' in inspect.getsource(runner._write_g1_stage2_aggregate)
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert imports.isdisjoint({"requests", "httpx", "socket", "subprocess"})


def test_driver_has_one_fixed_entrypoint_and_reviewed_step_order() -> None:
    assert tuple(inspect.signature(runner.run_g1_stage2).parameters) == ("preparation_commit_sha",)
    source = inspect.getsource(runner.run_g1_stage2)
    ordered_calls = (
        "assert_single_thread_environment",
        "load_g1_stage2_inputs",
        "build_g1_prepared_frame",
        "select_g1_development_alpha",
        "fit_t0_calibration_series",
        "make_bound_certificate",
        "_t0_utility_series",
        "evaluate_g1_cost_cells",
        "_build_aggregate_record",
        "_write_g1_stage2_aggregate",
    )
    positions = tuple(source.index(name) for name in ordered_calls)
    assert positions == tuple(sorted(positions))


def test_driver_refuses_reviewed_protocol_drift_before_asset_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    protocol = runner.stage2_runner_protocol_identity().model_copy(update={"runner_protocol_sha256": "0" * 64})
    monkeypatch.setattr(runner, "stage2_runner_protocol_identity", lambda: protocol)
    monkeypatch.setattr(
        runner,
        "load_g1_stage2_inputs",
        lambda counters: pytest.fail("asset read reached after protocol drift"),
    )
    with pytest.raises(runner.R03G1Stage2AccessError, match="reviewed runner"):
        runner.run_g1_stage2("a" * 40)


def test_driver_refuses_bad_preparation_commit_before_asset_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_threads(monkeypatch)
    monkeypatch.setattr(
        runner,
        "load_g1_stage2_inputs",
        lambda counters: pytest.fail("asset read reached after bad commit"),
    )
    with pytest.raises(g1.R03G1PreparationError, match="commit"):
        runner.run_g1_stage2("INVALID")


def test_aggregate_serialization_is_canonical_and_single_lf() -> None:
    class SyntheticRecord:
        def model_dump(self, *, mode: str) -> dict[str, int]:
            assert mode == "json"
            return {"z": 2, "a": 1}

    payload = runner.serialize_g1_stage2_aggregate(SyntheticRecord())  # type: ignore[arg-type]
    assert payload == b'{"a":1,"z":2}\n'


def test_synthetic_full_driver_validates_serializes_and_writes_exclusively(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _pin_threads(monkeypatch)
    preparation_commit_sha = "fecd81298e289c114e4954e3b2fca1e654594abd"
    development_decisions = tuple(datetime(year, month, day, 15, 30, tzinfo=timezone.utc) for year in g1.T0_FOLD_END_YEARS for month, day in ((1, 2), (12, 29)))
    calibration_decisions = tuple(datetime(2022, 1, 3 + index, 15, 30, tzinfo=timezone.utc) for index in range(8))
    tickers = tuple(f"T{index:02d}" for index in range(20))
    prepared = runner.G1PreparedFrame(
        session_dates=tuple(decision.date() for decision in development_decisions + calibration_decisions),
        rows=(
            g1.T0FitRowMetadata(
                row_id="synthetic-row",
                decision_at=development_decisions[0],
                feature_cutoff_at=development_decisions[0] - timedelta(days=1),
                label_maturity_at=development_decisions[0] + timedelta(days=7),
                decision_session_ordinal=100,
                feature_session_ordinal=99,
                label_session_ordinal=105,
                split_name="DEVELOPMENT",
                phase_book=0,
            ),
        ),
        row_tickers=(tickers[0],),
        feature_matrix=((0.0,) * 18,),
        target_e12=(0,),
        decision_ordinals={decision: 200 + index for index, decision in enumerate(calibration_decisions)},
        realized_by_decision={decision: {ticker: (index - 10) * 1_000_000 for index, ticker in enumerate(tickers)} for decision in calibration_decisions},
        development_decisions=development_decisions,
        calibration_decisions=calibration_decisions,
        calibration_coverage_end_exclusive_at=calibration_decisions[-1] + timedelta(days=1),
        fold_validation_windows=runner._fold_validation_windows(development_decisions),
    )
    cells = {(fold, cost) for fold in g1.T0_FOLD_END_YEARS for cost in g1.T0_COST_CELLS_BPS}
    utilities = {alpha: {cell: alpha for cell in cells} for alpha in g1.T0_ALPHA_E1_GRID}
    run_hashes = {alpha: {fold: format(1 + alpha_index * len(g1.T0_FOLD_END_YEARS) + fold_index, "064x") for fold_index, fold in enumerate(g1.T0_FOLD_END_YEARS)} for alpha_index, alpha in enumerate(g1.T0_ALPHA_E1_GRID)}
    alpha_selection = g1.select_t0_alpha(utilities, run_hashes)
    model_series = SimpleNamespace(t0_model_series_id="b" * 64)

    def synthetic_load(counters: runner.Stage2AccessCounters) -> runner.G1Stage2LoadedInputs:
        counters.allowed_asset_reads = 2
        receipts = []
        for pin in runner.stage2_asset_pins():
            unsigned = {
                "schema_version": "r03-g1-stage2-asset-load-receipt-v1",
                "role": pin.role,
                "resolved_path": pin.absolute_path,
                "sha256": pin.sha256,
                "byte_count": 1,
                "row_count": 0,
                "column_names": (),
            }
            receipts.append(
                runner.Stage2AssetLoadReceipt(
                    **unsigned,
                    receipt_sha256=canonical_sha256(unsigned),
                )
            )
        return runner.G1Stage2LoadedInputs(
            market_bars=object(),
            universe_snapshot=object(),  # type: ignore[arg-type]
            receipts=tuple(receipts),
        )

    monkeypatch.setattr(runner, "load_g1_stage2_inputs", synthetic_load)
    monkeypatch.setattr(runner, "build_g1_prepared_frame", lambda market_bars, universe_snapshot: prepared)
    monkeypatch.setattr(runner, "select_g1_development_alpha", lambda prepared, runtime: alpha_selection)
    monkeypatch.setattr(runner, "fit_t0_calibration_series", lambda *args, **kwargs: model_series)
    monkeypatch.setattr(
        runner,
        "_calibration_scores",
        lambda prepared, model_series: {decision: {ticker: float(index) for index, ticker in enumerate(tickers)} for decision in calibration_decisions},
    )
    monkeypatch.setattr(runner, "WORKSPACE_ROOT", str(tmp_path))
    output_path = tmp_path / runner.G1_AGGREGATE_OUTPUT_PATH
    output_path.parent.mkdir(parents=True)

    aggregate = runner.run_g1_stage2(preparation_commit_sha)

    payload = output_path.read_bytes()
    assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
    persisted = runner.G1Stage2AggregateRecord.model_validate_json(payload)
    assert persisted == aggregate
    assert persisted.aggregate_sha256 == canonical_sha256(persisted.model_dump(mode="json", exclude={"aggregate_sha256"}))
    with pytest.raises(runner.R03G1Stage2AccessError, match="refusing to overwrite"):
        runner._write_g1_stage2_aggregate(aggregate)


def test_incident_record_is_aggregate_only_and_closes_both_kb_copies() -> None:
    incident = json.loads(INCIDENT_PATH.read_text(encoding="utf-8"))
    assert incident["accessed_file_count"] == 1
    assert incident["matched_line_count"] == 1
    assert incident["raw_news_access_attempts"] == 1
    assert incident["raw_content_present_in_incident_record"] is False
    assert incident["raw_content_reopened_for_incident_record"] is False
    assert incident["raw_content_hash_computed_for_incident_record"] is False
    assert incident["frame_materializations_after_incident"] == 0
    assert incident["fitting_calls_after_incident"] == 0
    assert incident["g1_gate_decisions_after_incident"] == 0
    assert incident["provider_calls"] == incident["network_calls"] == 0
    assert incident["codex_project_kb_purge"]["status"] == "COMPLETE"
    assert incident["independent_session_project_kb_purge"]["status"] == "COMPLETE"
    serialized = json.dumps(incident, sort_keys=True).lower()
    assert all(token not in serialized for token in ("article_body", "content_excerpt", "headline_text", "raw_text_value"))


def test_aggregate_construction_incident_note_is_value_free() -> None:
    incident = json.loads(AGGREGATE_INCIDENT_PATH.read_text(encoding="utf-8"))
    assert incident == {
        "schema_version": "r03-g1-stage2-aggregate-construction-incident-v1",
        "incident_id": "R03_G1_STAGE2_AGGREGATE_CONSTRUCTION_INCIDENT_01",
        "aggregate_output_path": runner.G1_AGGREGATE_OUTPUT_PATH,
        "note": ("G1 cost cells were computed in memory and the run then failed during aggregate " "record construction. No G1 value was emitted, observed, or persisted, and no " "execution record exists."),
    }


def test_protocol_mutation_requires_rehash() -> None:
    protocol = runner.stage2_runner_protocol_identity()
    mutated = protocol.model_dump(mode="json")
    mutated["nominal_decision_time"] = "MUTATED"
    with pytest.raises(ValidationError):
        runner.Stage2RunnerProtocolIdentity.model_validate(mutated)
