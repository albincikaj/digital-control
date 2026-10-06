"""Central registry of all problem generators."""
from __future__ import annotations

import numpy as np

from . import ch0, ch2, ch3, ch4, ch56, ch78
from .base import Problem

GENERATORS = {}
for mod in (ch0, ch2, ch3, ch4, ch56, ch78):
    GENERATORS.update(mod.GENERATORS)


def make(gen_id: str, difficulty: int = 2, seed: int | None = None) -> Problem:
    if seed is None:
        seed = int(np.random.default_rng().integers(1, 2**31 - 1))
    rng = np.random.default_rng(seed)
    p = GENERATORS[gen_id](rng, int(difficulty), int(seed))
    p.seed = int(seed)
    p.gen_id = gen_id
    return p


def gens_for_topic(topic: str) -> list[str]:
    from ..curriculum import TOPICS
    return list(TOPICS[topic]["gens"])
