"""Frozen provider-free sensitivity grid and confirmatory sizing rules."""

from __future__ import annotations

import hashlib
import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .arithmetic import round_ratio_half_even
from .canonical import canonical_sha256
from .contracts import StrictModel
from .r02_v2_headroom import MIN_MEAN_HEADROOM_E12

DISCORDANCE_RATES_PPM = (50_000, 100_000, 200_000)
CONDITIONAL_MEANS_E12 = (
    250_000_000,
    500_000_000,
    1_000_000_000,
    2_000_000_000,
)
CONDITIONAL_SDS_E12 = CONDITIONAL_MEANS_E12
CHALLENGE_TO_REPRESENTATIVE_RATIOS_PPM = (500_000, 1_000_000, 1_500_000)
FAIL_CLOSED_RATES_PPM = (0, 50_000)
MIN_POWER_PPM = 800_000
MIN_CONFIRMATORY_N = 200
MAX_CONFIRMATORY_N = 400


class R02V2PowerError(RuntimeError):
    """Raised when a power computation leaves the preregistered grid."""


class R02V2PowerCell(StrictModel):
    cell_id: str
    discordance_rate_ppm: int
    conditional_mean_e12: int
    conditional_sd_e12: int
    challenge_to_representative_mean_ratio_ppm: int
    fail_closed_rate_ppm: int
    full_frame_expected_effect_e12: int
    included: bool


class R02V2CellPowerResult(StrictModel):
    cell_id: str
    total_n: int = Field(ge=MIN_CONFIRMATORY_N, le=MAX_CONFIRMATORY_N)
    trials: int = Field(gt=0)
    bootstrap_resamples: int = Field(gt=0)
    supported_trials: int = Field(ge=0)
    estimated_power_ppm: int = Field(ge=0, le=1_000_000)
    wilson_lower_power_ppm: int = Field(ge=0, le=1_000_000)
    wilson_upper_power_ppm: int = Field(ge=0, le=1_000_000)
    simulation_seed_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    passes: bool


class R02V2PowerGridReport(StrictModel):
    schema_version: Literal["r02-overlay-v2-power-grid-report-v1"] = "r02-overlay-v2-power-grid-report-v1"
    included_cell_count: int = Field(gt=0)
    required_n_by_cell: dict[str, int | None]
    least_powered_governing_cell_id: str | None
    maximum_required_n: int | None
    decision: Literal["POWER_GATE_GO", "POWER_GATE_NO_GO"]
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report_hash(self) -> "R02V2PowerGridReport":
        expected = canonical_sha256({key: value for key, value in self.model_dump(mode="python").items() if key != "report_sha256"})
        if self.report_sha256 != expected:
            raise ValueError("power-grid report hash mismatch")
        return self


def sensitivity_grid() -> tuple[R02V2PowerCell, ...]:
    cells: list[R02V2PowerCell] = []
    for rate in DISCORDANCE_RATES_PPM:
        for mean in CONDITIONAL_MEANS_E12:
            for sd in CONDITIONAL_SDS_E12:
                for ratio in CHALLENGE_TO_REPRESENTATIVE_RATIOS_PPM:
                    for fail_rate in FAIL_CLOSED_RATES_PPM:
                        expected = rate * mean // 1_000_000
                        cell_id = f"D{rate:06d}_M{mean:010d}_S{sd:010d}_" f"R{ratio:07d}_F{fail_rate:06d}"
                        cells.append(
                            R02V2PowerCell(
                                cell_id=cell_id,
                                discordance_rate_ppm=rate,
                                conditional_mean_e12=mean,
                                conditional_sd_e12=sd,
                                challenge_to_representative_mean_ratio_ppm=ratio,
                                fail_closed_rate_ppm=fail_rate,
                                full_frame_expected_effect_e12=expected,
                                included=expected >= MIN_MEAN_HEADROOM_E12,
                            )
                        )
    if len(cells) != 288:
        raise R02V2PowerError("sensitivity grid is not complete")
    return tuple(cells)


def wilson_interval_ppm(successes: int, trials: int) -> tuple[int, int]:
    if trials <= 0 or not 0 <= successes <= trials:
        raise R02V2PowerError("invalid Wilson counts")
    z = 1.959963984540054
    probability = successes / trials
    denominator = 1 + z * z / trials
    center = (probability + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt(probability * (1 - probability) / trials + z * z / (4 * trials**2)) / denominator
    return (
        round((center - margin) * 1_000_000),
        round((center + margin) * 1_000_000),
    )


def passes_power_gate(wilson_lower_power_ppm: int) -> bool:
    if not 0 <= wilson_lower_power_ppm <= 1_000_000:
        raise R02V2PowerError("Wilson lower power must be a ppm probability")
    return wilson_lower_power_ppm >= MIN_POWER_PPM


def _domain_seed(seed_sha256: str, *parts: str) -> int:
    if len(seed_sha256) != 64 or any(character not in "0123456789abcdef" for character in seed_sha256):
        raise R02V2PowerError("seed must be lowercase SHA-256 hex")
    message = "|".join(("r02-overlay-v2-power", seed_sha256, *parts))
    return int.from_bytes(
        hashlib.sha256(message.encode("ascii")).digest()[:16],
        "big",
    )


def _weighted_mean(rep: np.ndarray, challenge: np.ndarray) -> int:
    numerator = 3 * int(rep.sum()) * len(challenge) + int(challenge.sum()) * len(rep)
    return round_ratio_half_even(
        numerator,
        4 * len(rep) * len(challenge),
    )


def _bootstrap_lower(
    rep: np.ndarray,
    challenge: np.ndarray,
    *,
    rng: np.random.Generator,
    resamples: int,
) -> int:
    estimates: list[int] = []
    for _ in range(resamples):
        estimates.append(
            _weighted_mean(
                rep[rng.integers(0, len(rep), size=len(rep))],
                challenge[rng.integers(0, len(challenge), size=len(challenge))],
            )
        )
    return sorted(estimates)[max(math.ceil(0.025 * resamples) - 1, 0)]


def _draw_effects(
    *,
    rng: np.random.Generator,
    count: int,
    discordance_rate_ppm: int,
    conditional_mean_e12: int,
    conditional_sd_e12: int,
    fail_closed_rate_ppm: int,
    effect_bounds_e12: tuple[int, int],
) -> np.ndarray:
    discordant = rng.integers(0, 1_000_000, size=count) < discordance_rate_ppm
    failed = rng.integers(0, 1_000_000, size=count) < fail_closed_rate_ppm
    conditional = np.rint(
        rng.normal(
            conditional_mean_e12,
            conditional_sd_e12,
            size=count,
        )
    ).astype(np.int64)
    conditional = np.clip(
        conditional,
        effect_bounds_e12[0],
        effect_bounds_e12[1],
    )
    return np.where(discordant & ~failed, conditional, 0).astype(np.int64)


def simulate_cell_power(
    cell: R02V2PowerCell,
    *,
    total_n: int,
    seed_sha256: str,
    effect_bounds_e12: tuple[int, int],
    trials: int = 1_000,
    bootstrap_resamples: int = 1_000,
) -> R02V2CellPowerResult:
    if not cell.included:
        raise R02V2PowerError("excluded grid cell may not govern power")
    if total_n < MIN_CONFIRMATORY_N or total_n > MAX_CONFIRMATORY_N or total_n % 4:
        raise R02V2PowerError("confirmatory N must be a 200..400 multiple of 4")
    if trials <= 0 or bootstrap_resamples <= 0:
        raise R02V2PowerError("simulation counts must be positive")
    if effect_bounds_e12[0] >= effect_bounds_e12[1]:
        raise R02V2PowerError("effect bounds are not ordered")
    representative_n = total_n * 3 // 4
    challenge_n = total_n // 4
    supported = 0
    for trial in range(trials):
        trial_rng = np.random.Generator(
            np.random.PCG64(
                _domain_seed(
                    seed_sha256,
                    cell.cell_id,
                    str(total_n),
                    str(trial),
                )
            )
        )
        representative = _draw_effects(
            rng=trial_rng,
            count=representative_n,
            discordance_rate_ppm=cell.discordance_rate_ppm,
            conditional_mean_e12=cell.conditional_mean_e12,
            conditional_sd_e12=cell.conditional_sd_e12,
            fail_closed_rate_ppm=cell.fail_closed_rate_ppm,
            effect_bounds_e12=effect_bounds_e12,
        )
        challenge_mean = round_ratio_half_even(
            cell.conditional_mean_e12 * cell.challenge_to_representative_mean_ratio_ppm,
            1_000_000,
        )
        challenge = _draw_effects(
            rng=trial_rng,
            count=challenge_n,
            discordance_rate_ppm=cell.discordance_rate_ppm,
            conditional_mean_e12=challenge_mean,
            conditional_sd_e12=cell.conditional_sd_e12,
            fail_closed_rate_ppm=cell.fail_closed_rate_ppm,
            effect_bounds_e12=effect_bounds_e12,
        )
        lower = _bootstrap_lower(
            representative,
            challenge,
            rng=trial_rng,
            resamples=bootstrap_resamples,
        )
        supported += int(lower > MIN_MEAN_HEADROOM_E12)
    estimated = round_ratio_half_even(supported * 1_000_000, trials)
    lower, upper = wilson_interval_ppm(supported, trials)
    return R02V2CellPowerResult(
        cell_id=cell.cell_id,
        total_n=total_n,
        trials=trials,
        bootstrap_resamples=bootstrap_resamples,
        supported_trials=supported,
        estimated_power_ppm=estimated,
        wilson_lower_power_ppm=lower,
        wilson_upper_power_ppm=upper,
        simulation_seed_sha256=seed_sha256,
        passes=passes_power_gate(lower),
    )


def evaluate_power_grid(
    *,
    seed_sha256: str,
    effect_bounds_e12: tuple[int, int],
    trials: int,
    bootstrap_resamples: int,
    sample_sizes: tuple[int, ...] = tuple(range(200, 401, 4)),
) -> R02V2PowerGridReport:
    included = tuple(cell for cell in sensitivity_grid() if cell.included)
    required: dict[str, int | None] = {}
    for cell in included:
        required_n: int | None = None
        for total_n in sample_sizes:
            result = simulate_cell_power(
                cell,
                total_n=total_n,
                seed_sha256=seed_sha256,
                effect_bounds_e12=effect_bounds_e12,
                trials=trials,
                bootstrap_resamples=bootstrap_resamples,
            )
            if result.passes:
                required_n = total_n
                break
        required[cell.cell_id] = required_n
    failed = sorted(cell_id for cell_id, value in required.items() if value is None)
    if failed:
        governing = failed[0]
        maximum: int | None = None
        decision: Literal["POWER_GATE_GO", "POWER_GATE_NO_GO"] = "POWER_GATE_NO_GO"
    else:
        maximum = max(value for value in required.values() if value is not None)
        governing = min(cell_id for cell_id, value in required.items() if value == maximum)
        decision = "POWER_GATE_GO"
    body = {
        "schema_version": "r02-overlay-v2-power-grid-report-v1",
        "included_cell_count": len(included),
        "required_n_by_cell": required,
        "least_powered_governing_cell_id": governing,
        "maximum_required_n": maximum,
        "decision": decision,
    }
    return R02V2PowerGridReport(
        **body,
        report_sha256=canonical_sha256(body),
    )


def blinded_pilot_go_no_go(
    *,
    representative_successes: int,
    representative_trials: int,
    challenge_successes: int,
    challenge_trials: int,
) -> Literal["PILOT_GO", "PILOT_NO_GO"]:
    total_successes = representative_successes + challenge_successes
    total_trials = representative_trials + challenge_trials
    representative_lower, _ = wilson_interval_ppm(
        representative_successes,
        representative_trials,
    )
    challenge_lower, _ = wilson_interval_ppm(
        challenge_successes,
        challenge_trials,
    )
    pooled_lower, _ = wilson_interval_ppm(total_successes, total_trials)
    supports = representative_successes >= 2 and challenge_successes >= 2 and total_successes >= 5 and representative_lower * 300 >= 5 * 1_000_000 and challenge_lower * 100 >= 5 * 1_000_000 and pooled_lower * 400 >= 20 * 1_000_000
    return "PILOT_GO" if supports else "PILOT_NO_GO"


def confirmatory_sample_size(
    *,
    utility_power_n: int,
    representative_discordance_lower_ppm: int,
    challenge_discordance_lower_ppm: int,
    pooled_discordance_lower_ppm: int,
) -> int | None:
    for total_n in range(
        max(MIN_CONFIRMATORY_N, 4 * math.ceil(utility_power_n / 4)),
        MAX_CONFIRMATORY_N + 1,
        4,
    ):
        representative_n = total_n * 3 // 4
        challenge_n = total_n // 4
        if representative_n * representative_discordance_lower_ppm >= 5 * 1_000_000 and challenge_n * challenge_discordance_lower_ppm >= 5 * 1_000_000 and total_n * pooled_discordance_lower_ppm >= 20 * 1_000_000:
            return total_n
    return None
