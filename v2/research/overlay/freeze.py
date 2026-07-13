"""Provider-free Phase B statistical freeze and lattice certification."""

from __future__ import annotations

from .arithmetic import BASIS_POINTS, UTILITY_SCALE, median_int
from .baselines import hold_policy
from .canonical import canonical_sha256, sha256_hex
from .contracts import (
    GeneratorConfig,
    OracleResult,
    ProviderFreeCaseCertificate,
    ProviderFreeFreeze,
    SyntheticEpisode,
)
from .fixtures import generate_development_episodes
from .oracle import solve_oracle
from .scoring import normalized_regret_e12
from .specs import scoring_spec_sha256

NORMALIZATION_EPSILON_E12 = UTILITY_SCALE // BASIS_POINTS


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
        feasible_lattice_bound_certificate_sha256=canonical_sha256(
            _lattice_certificate_identity(case_tuple)
        ),
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
