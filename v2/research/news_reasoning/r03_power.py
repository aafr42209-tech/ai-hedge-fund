"""Provider-free R03 G2/G3 statistical machinery."""

from __future__ import annotations

import hashlib
import math

import numpy as np
from pydantic import Field, model_validator

from v2.research.overlay.canonical import canonical_sha256
from v2.research.overlay.contracts import StrictModel
from v2.research.overlay.r02_v2_power import wilson_interval_ppm

from .r03_contracts import (
    DELTA_STAR_E12,
    mean_e12,
    R03_G2_ABSOLUTE_PROFITABILITY_FLAG_RULE,
    R03_G2_INCREMENTAL_PRIMARY_GATE_RULE,
    R03_G2_LOSES_LESS_INTERPRETATION_RULE,
    R03ContractError,
    R03G2GateResult,
    R03G2IncrementalAxis,
    R03GateLabel,
    R03T2AbsoluteProfitabilityFlag,
)
from .r03_headroom import stationary_bootstrap_means_e12

G2_CONTRAST_BOOTSTRAP_LABEL = "R03_G2"
G2_ABSOLUTE_BOOTSTRAP_LABEL = "R03_G2_T2_ABSOLUTE"
G3_SD_MULTIPLIERS_PPM = (1_000_000, 1_500_000, 2_000_000)
G3_FAIL_RATES_PPM = (0, 50_000)
G3_PLANNED_N = 747
G3_MIN_POWER_PPM = 800_000


class R03PowerError(R03ContractError):
    pass


class R03G3Cell(StrictModel):
    cell_id: str
    sd_multiplier_ppm: int
    fail_rate_ppm: int
    planned_n: int = G3_PLANNED_N
    effect_e12: int


class R03G3CellResult(StrictModel):
    cell: R03G3Cell
    trials: int = Field(gt=0)
    supported_trials: int = Field(ge=0)
    estimated_power_ppm: int = Field(ge=0, le=1_000_000)
    wilson_lower_power_ppm: int = Field(ge=0, le=1_000_000)
    wilson_upper_power_ppm: int = Field(ge=0, le=1_000_000)
    passes: bool
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_result(self) -> "R03G3CellResult":
        unsigned = self.model_dump(mode="json", exclude={"result_sha256"})
        if canonical_sha256(unsigned) != self.result_sha256:
            raise R03PowerError("G3 cell result hash mismatch")
        if self.passes != (self.wilson_lower_power_ppm >= G3_MIN_POWER_PPM):
            raise R03PowerError("G3 cell pass flag mismatch")
        return self


class R03G3GridResult(StrictModel):
    cells: tuple[R03G3CellResult, ...]
    label: R03GateLabel
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_grid(self) -> "R03G3GridResult":
        if len(self.cells) != 6:
            raise R03PowerError("G3 grid requires six cells")
        expected = R03GateLabel.G3_CONTINUE if all(cell.passes for cell in self.cells) else R03GateLabel.G3_STOP
        if self.label != expected:
            raise R03PowerError("G3 grid label mismatch")
        unsigned = self.model_dump(mode="json", exclude={"result_sha256"})
        if canonical_sha256(unsigned) != self.result_sha256:
            raise R03PowerError("G3 grid hash mismatch")
        return self


def g3_cells() -> tuple[R03G3Cell, ...]:
    cells = []
    for sd in G3_SD_MULTIPLIERS_PPM:
        for fail in G3_FAIL_RATES_PPM:
            cells.append(
                R03G3Cell(
                    cell_id=f"SD{sd}_FAIL{fail}",
                    sd_multiplier_ppm=sd,
                    fail_rate_ppm=fail,
                    effect_e12=round(DELTA_STAR_E12 * (1_000_000 - fail) / 1_000_000),
                )
            )
    return tuple(cells)


def evaluate_g2(
    differences_e12: tuple[int, ...],
    t2_absolute_net_utilities_e12: tuple[int, ...],
    *,
    seed_sha256: str,
    resamples: int = 10_000,
) -> R03G2GateResult:
    """Build the independent incremental and report-only absolute G2 axes.

    The incremental axis is computed first and solely from the sealed contrast
    label. ``G2_INCREMENTAL_PASS`` is a non-pause, not efficacy evidence. The
    absolute-profitability flag cannot change or veto that primary axis.
    """

    if not differences_e12:
        raise R03PowerError("G2 requires a nonempty paired series")
    draws = sorted(
        stationary_bootstrap_means_e12(
            differences_e12,
            seed_sha256=seed_sha256,
            label=G2_CONTRAST_BOOTSTRAP_LABEL,
            resamples=resamples,
        )
    )
    upper = draws[max(0, math.ceil(0.95 * len(draws)) - 1)]
    label = R03GateLabel.G2_PAUSE if upper <= DELTA_STAR_E12 else R03GateLabel.G2_CONTINUE
    incremental_axis = R03G2IncrementalAxis.G2_INCREMENTAL_FAIL if label == R03GateLabel.G2_PAUSE else R03G2IncrementalAxis.G2_INCREMENTAL_PASS

    if not t2_absolute_net_utilities_e12:
        raise R03PowerError("G2 requires a nonempty absolute T2 paired series")
    if len(t2_absolute_net_utilities_e12) != len(differences_e12):
        raise R03PowerError("G2 contrast and absolute T2 paired series must have equal length")
    absolute_draws = sorted(
        stationary_bootstrap_means_e12(
            t2_absolute_net_utilities_e12,
            seed_sha256=seed_sha256,
            label=G2_ABSOLUTE_BOOTSTRAP_LABEL,
            resamples=resamples,
        )
    )
    absolute_point_estimate = mean_e12(list(t2_absolute_net_utilities_e12))
    absolute_profitability_flag = R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_POSITIVE if absolute_point_estimate > 0 else R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_NEGATIVE
    input_sha = canonical_sha256(
        {
            "gate": "G2",
            "differences_e12": differences_e12,
            "t2_absolute_net_utilities_e12": t2_absolute_net_utilities_e12,
            "resamples": resamples,
        }
    )
    unsigned = {
        "gate": "G2",
        "label": label,
        "incremental_axis": incremental_axis,
        "absolute_profitability_flag": absolute_profitability_flag,
        "point_estimate_e12": mean_e12(list(differences_e12)),
        "upper_95_e12": upper,
        "lower_95_e12": draws[max(0, math.ceil(0.05 * len(draws)) - 1)],
        "t2_absolute_point_estimate_e12": absolute_point_estimate,
        "t2_absolute_lower_95_e12": absolute_draws[max(0, math.ceil(0.05 * len(absolute_draws)) - 1)],
        "seed_sha256": seed_sha256,
        "input_sha256": input_sha,
        "incremental_primary_gate_rule": R03_G2_INCREMENTAL_PRIMARY_GATE_RULE,
        "absolute_profitability_flag_rule": R03_G2_ABSOLUTE_PROFITABILITY_FLAG_RULE,
        "loses_less_interpretation_rule": R03_G2_LOSES_LESS_INTERPRETATION_RULE,
    }
    return R03G2GateResult(**unsigned, result_sha256=canonical_sha256(unsigned))


def _domain_seed(seed_sha256: str, cell_id: str) -> int:
    return int.from_bytes(
        hashlib.sha256(bytes.fromhex(seed_sha256) + cell_id.encode()).digest()[:16],
        "big",
    )


def simulate_g3_cell(
    centered_proxy_e12: tuple[int, ...],
    cell: R03G3Cell,
    *,
    seed_sha256: str,
    trials: int = 1_000,
    block_length: int = 10,
) -> R03G3CellResult:
    if not centered_proxy_e12 or trials <= 0:
        raise R03PowerError("invalid G3 simulation inputs")
    proxy = np.asarray(centered_proxy_e12, dtype=np.float64)
    proxy -= proxy.mean()
    proxy *= cell.sd_multiplier_ppm / 1_000_000
    rng = np.random.Generator(np.random.PCG64(_domain_seed(seed_sha256, cell.cell_id)))
    supported = 0
    restart = 1.0 / block_length
    for _ in range(trials):
        indices = np.empty(cell.planned_n, dtype=np.int64)
        indices[0] = rng.integers(0, len(proxy))
        for index in range(1, cell.planned_n):
            indices[index] = rng.integers(0, len(proxy)) if rng.random() < restart else (indices[index - 1] + 1) % len(proxy)
        sample = proxy[indices] + DELTA_STAR_E12
        if cell.fail_rate_ppm:
            sample[rng.random(cell.planned_n) < cell.fail_rate_ppm / 1_000_000] = 0.0
        standard_error = sample.std(ddof=1) / math.sqrt(cell.planned_n)
        if sample.mean() - 1.6448536269514722 * standard_error > 0:
            supported += 1
    power_ppm = round(supported * 1_000_000 / trials)
    lower, upper = wilson_interval_ppm(supported, trials)
    unsigned = {
        "cell": cell.model_dump(mode="json"),
        "trials": trials,
        "supported_trials": supported,
        "estimated_power_ppm": power_ppm,
        "wilson_lower_power_ppm": lower,
        "wilson_upper_power_ppm": upper,
        "passes": lower >= G3_MIN_POWER_PPM,
    }
    return R03G3CellResult(**unsigned, result_sha256=canonical_sha256(unsigned))


def evaluate_g3_grid(cells: tuple[R03G3CellResult, ...]) -> R03G3GridResult:
    label = R03GateLabel.G3_CONTINUE if len(cells) == 6 and all(cell.passes for cell in cells) else R03GateLabel.G3_STOP
    unsigned = {"cells": cells, "label": label}
    return R03G3GridResult(cells=cells, label=label, result_sha256=canonical_sha256(unsigned))
