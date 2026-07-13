"""Provider-free Phase B statistical freeze and lattice certification."""

from __future__ import annotations

from pathlib import Path

from .arithmetic import BASIS_POINTS, UTILITY_SCALE, mean_int, median_int
from .baselines import hold_policy
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .contracts import (
    GeneratorConfig,
    OracleResult,
    ProviderFreeCaseCertificate,
    ProviderFreeFreeze,
    ProviderFreeRegimeGapStats,
    ProviderFreeRegimeGapSummary,
    SyntheticEpisode,
)
from .fixtures import REGIMES, generate_development_episodes
from .oracle import solve_oracle
from .scoring import normalized_regret_e12
from .specs import scoring_spec_sha256

NORMALIZATION_EPSILON_E12 = UTILITY_SCALE // BASIS_POINTS
FROZEN_DEVELOPMENT_ROOT_SEED_LABEL = "r01-phase-b-development-fixtures-v1"
FROZEN_DEVELOPMENT_FIXTURE_COUNT = 40
FROZEN_PROVIDER_FREE_FREEZE_SHA256 = "86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2"
FROZEN_PROVIDER_FREE_FREEZE_RELATIVE_PATH = "docs/r01-b0-provider-free-freeze.json"
FROZEN_PROVIDER_FREE_REGIME_GAP_SUMMARY_SHA256 = "0e6e8945f93779a77ffc7687d63062c010efd3aee3d6c8062551e54108fbf886"
FROZEN_PROVIDER_FREE_REGIME_GAP_SUMMARY_RELATIVE_PATH = "docs/r01-b0-regime-gap-summary.json"


def _lattice_certificate_identity(
    cases: tuple[ProviderFreeCaseCertificate, ...],
) -> dict[str, object]:
    return {
        "schema_version": "r01-feasible-lattice-bound-certificate-bundle-v1",
        "cases": [
            {
                "case_id": case.case_id,
                "fixture_content_sha256": case.fixture_content_sha256,
                "minimum_utility_e12": case.minimum_utility_e12,
                "maximum_abs_utility_e12": case.maximum_abs_utility_e12,
                "maximum_normalized_regret_e12": case.maximum_normalized_regret_e12,
                "oracle_certificate_sha256": case.oracle_certificate_sha256,
            }
            for case in cases
        ],
    }


def build_provider_free_freeze(
    episodes: tuple[SyntheticEpisode, ...],
    *,
    config: GeneratorConfig,
    root_seed_label: str,
    normalization_epsilon_e12: int = NORMALIZATION_EPSILON_E12,
) -> ProviderFreeFreeze:
    """Derive the fixed regret scale and complete-lattice bounds with zero providers."""

    if not episodes:
        raise ValueError("provider-free freeze requires development fixtures")
    if normalization_epsilon_e12 <= 0:
        raise ValueError("normalization_epsilon_e12 must be positive")

    intermediate: list[tuple[SyntheticEpisode, int, int, OracleResult]] = []
    gaps: list[int] = []
    for episode in episodes:
        oracle = solve_oracle(episode)
        hold_utility = hold_policy(episode).score.utility_e12
        gap = oracle.score.utility_e12 - hold_utility
        if gap < 0:
            raise RuntimeError("hold utility exceeds exact oracle")
        gaps.append(gap)
        intermediate.append((episode, hold_utility, gap, oracle))

    median_gap = median_int(gaps)
    regret_scale = max(median_gap, normalization_epsilon_e12)
    cases: list[ProviderFreeCaseCertificate] = []
    for episode, hold_utility, gap, oracle in intermediate:
        maximum_regret = normalized_regret_e12(
            oracle.certificate.minimum_utility_e12,
            oracle.score.utility_e12,
            regret_scale,
        )
        cases.append(
            ProviderFreeCaseCertificate(
                case_id=episode.public.case_id,
                regime=episode.hidden.regime,
                fixture_content_sha256=episode.content_sha256,
                oracle_utility_e12=oracle.score.utility_e12,
                hold_utility_e12=hold_utility,
                oracle_hold_gap_e12=gap,
                minimum_utility_e12=oracle.certificate.minimum_utility_e12,
                maximum_abs_utility_e12=oracle.certificate.maximum_abs_utility_e12,
                maximum_normalized_regret_e12=maximum_regret,
                oracle_certificate_sha256=canonical_sha256(oracle.certificate),
            )
        )
    case_tuple = tuple(cases)
    return ProviderFreeFreeze(
        generator_config_sha256=canonical_sha256(config),
        scoring_spec_sha256=scoring_spec_sha256(),
        root_seed_label=root_seed_label,
        root_seed_sha256=sha256_hex(root_seed_label.encode("utf-8")),
        fixture_count=len(case_tuple),
        normalization_epsilon_e12=normalization_epsilon_e12,
        median_oracle_hold_gap_e12=median_gap,
        regret_scale_e12=regret_scale,
        max_abs_utility_e12=max(case.maximum_abs_utility_e12 for case in case_tuple),
        max_normalized_regret_e12=max(case.maximum_normalized_regret_e12 for case in case_tuple),
        feasible_lattice_bound_certificate_sha256=canonical_sha256(_lattice_certificate_identity(case_tuple)),
        cases=case_tuple,
    )


def generate_provider_free_freeze(
    *,
    root_seed_label: str,
    count: int = 40,
    config: GeneratorConfig | None = None,
) -> ProviderFreeFreeze:
    """Generate development fixtures and derive their provider-free freeze."""

    resolved_config = config or GeneratorConfig()
    episodes = generate_development_episodes(resolved_config, root_seed_label, count)
    return build_provider_free_freeze(
        episodes,
        config=resolved_config,
        root_seed_label=root_seed_label,
    )


def verify_frozen_development_identity(
    freeze: ProviderFreeFreeze,
    *,
    expected_sha256: str,
) -> None:
    """Bind one freeze to the committed R01 B0 trust anchor."""

    if expected_sha256 != FROZEN_PROVIDER_FREE_FREEZE_SHA256:
        raise RuntimeError("unexpected provider-free freeze trust anchor")
    if canonical_sha256(freeze) != expected_sha256:
        raise RuntimeError("provider-free freeze differs from the external trust anchor")
    if freeze.root_seed_label != FROZEN_DEVELOPMENT_ROOT_SEED_LABEL:
        raise RuntimeError("provider-free freeze root seed label differs from R01 B0")
    if freeze.fixture_count != FROZEN_DEVELOPMENT_FIXTURE_COUNT:
        raise RuntimeError("provider-free freeze fixture count differs from R01 B0")


def load_committed_provider_free_freeze(
    *,
    expected_sha256: str,
) -> ProviderFreeFreeze:
    """Load the committed canonical B0 freeze after checking its external anchor."""

    if expected_sha256 != FROZEN_PROVIDER_FREE_FREEZE_SHA256:
        raise RuntimeError("unexpected provider-free freeze trust anchor")
    repository_root = Path(__file__).resolve().parents[3]
    freeze_path = repository_root / FROZEN_PROVIDER_FREE_FREEZE_RELATIVE_PATH
    raw = freeze_path.read_bytes()
    if sha256_hex(raw) != expected_sha256:
        raise RuntimeError("committed provider-free freeze hash mismatch")
    freeze = ProviderFreeFreeze.model_validate_json(raw)
    if canonical_json_bytes(freeze) != raw:
        raise RuntimeError("committed provider-free freeze is not canonical JSON")
    verify_frozen_development_identity(freeze, expected_sha256=expected_sha256)
    return freeze


def _gap_stats(
    gaps: tuple[int, ...],
    *,
    normalization_epsilon_e12: int,
) -> ProviderFreeRegimeGapStats:
    if not gaps:
        raise ValueError("regime gap statistics require at least one case")
    return ProviderFreeRegimeGapStats(
        case_count=len(gaps),
        zero_gap_count=sum(gap == 0 for gap in gaps),
        positive_lte_epsilon_count=sum(0 < gap <= normalization_epsilon_e12 for gap in gaps),
        gt_epsilon_count=sum(gap > normalization_epsilon_e12 for gap in gaps),
        min_gap_e12=min(gaps),
        median_gap_e12=median_int(gaps),
        mean_gap_e12=mean_int(gaps),
        max_gap_e12=max(gaps),
    )


def build_provider_free_regime_gap_summary(
    freeze: ProviderFreeFreeze,
    *,
    source_freeze_sha256: str,
) -> ProviderFreeRegimeGapSummary:
    """Derive exact per-regime oracle-hold gap statistics from one freeze."""

    if canonical_sha256(freeze) != source_freeze_sha256:
        raise RuntimeError("regime-gap source freeze hash mismatch")
    all_gaps = tuple(case.oracle_hold_gap_e12 for case in freeze.cases)
    regimes = {
        regime: _gap_stats(
            tuple(case.oracle_hold_gap_e12 for case in freeze.cases if case.regime == regime),
            normalization_epsilon_e12=freeze.normalization_epsilon_e12,
        )
        for regime in REGIMES
    }
    return ProviderFreeRegimeGapSummary(
        source_freeze_sha256=source_freeze_sha256,
        normalization_epsilon_e12=freeze.normalization_epsilon_e12,
        fixture_count=freeze.fixture_count,
        overall=_gap_stats(
            all_gaps,
            normalization_epsilon_e12=freeze.normalization_epsilon_e12,
        ),
        regimes=regimes,
    )


def load_committed_provider_free_regime_gap_summary(
    *,
    expected_freeze_sha256: str,
) -> ProviderFreeRegimeGapSummary:
    """Load and rederive the committed B0 regime-gap summary fail closed."""

    freeze = load_committed_provider_free_freeze(expected_sha256=expected_freeze_sha256)
    repository_root = Path(__file__).resolve().parents[3]
    summary_path = repository_root / FROZEN_PROVIDER_FREE_REGIME_GAP_SUMMARY_RELATIVE_PATH
    raw = summary_path.read_bytes()
    if sha256_hex(raw) != FROZEN_PROVIDER_FREE_REGIME_GAP_SUMMARY_SHA256:
        raise RuntimeError("committed provider-free regime-gap summary hash mismatch")
    summary = ProviderFreeRegimeGapSummary.model_validate_json(raw)
    if canonical_json_bytes(summary) != raw:
        raise RuntimeError("committed provider-free regime-gap summary is not canonical JSON")
    derived = build_provider_free_regime_gap_summary(
        freeze,
        source_freeze_sha256=expected_freeze_sha256,
    )
    if summary != derived:
        raise RuntimeError("committed provider-free regime-gap summary derivation mismatch")
    return summary
