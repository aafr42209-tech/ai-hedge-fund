"""R01 constrained LLM portfolio-overlay research engine.

Phase A is provider-free and development-only.  Nothing in this package is an
investment backtest or a live-trading path.
"""

from .arithmetic import UTILITY_SCALE, mean_int, round_ratio_half_even
from .canonical import canonical_json_bytes, sha256_hex
from .contracts import (
    ASSET_IDS,
    SIGNAL_IDS,
    Decision,
    DecisionBatch,
    PublicEpisode,
    SyntheticEpisode,
)

__all__ = [
    "ASSET_IDS",
    "SIGNAL_IDS",
    "UTILITY_SCALE",
    "Decision",
    "DecisionBatch",
    "PublicEpisode",
    "SyntheticEpisode",
    "canonical_json_bytes",
    "mean_int",
    "round_ratio_half_even",
    "sha256_hex",
]
