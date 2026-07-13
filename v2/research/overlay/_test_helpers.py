from __future__ import annotations

from functools import lru_cache

from .contracts import ASSET_IDS, Decision, DecisionBatch, GeneratorConfig, SyntheticEpisode
from .fixtures import generate_episode


@lru_cache(maxsize=None)
def episode(index: int = 0) -> SyntheticEpisode:
    return generate_episode(GeneratorConfig(), "r01-test-root", index)


def hold_batch(reasoning: str = "test") -> DecisionBatch:
    return DecisionBatch(decisions={asset_id: Decision(action="hold", quantity=0, confidence=50, reasoning=reasoning) for asset_id in ASSET_IDS})
