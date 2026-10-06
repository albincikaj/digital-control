"""Problem / Part data model shared by all generators."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Misc:
    """A predicted wrong answer that reveals a specific misconception."""
    value: Any
    tag: str
    diagnosis: str


@dataclass
class Part:
    key: str
    label: str                      # markdown/LaTeX prompt for this field
    kind: str                       # 'num' | 'vec' | 'choice' | 'bool'
    answer: Any
    points: float = 1.0
    hint: str = ""
    explain: str = ""               # WHY the answer is what it is (shown after grading)
    options: Optional[list] = None  # for 'choice'
    tol_rel: float = 0.02
    tol_abs: float = 0.006
    misconceptions: list = field(default_factory=list)
    placeholder: str = ""
    steps: list = field(default_factory=list)   # numeric sub-steps for the "solve step by step" walkthrough


@dataclass
class Problem:
    gen_id: str
    topic: str
    title: str
    difficulty: int
    seed: int
    statement: str
    parts: list
    solution: str
    matlab: str = ""
    source: str = ""
    plot: Optional[Callable[[], Any]] = None   # returns a matplotlib figure
    remedy: str = ""                            # short reminder of the key concept

    @property
    def max_points(self) -> float:
        return sum(p.points for p in self.parts)
