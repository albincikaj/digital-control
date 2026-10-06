import traceback
import numpy as np
import pytest

from dctrainer.problems.registry import GENERATORS, make
from dctrainer.grading import grade_part
from dctrainer.curriculum import TOPICS


def _answer_str(part):
    if part.kind == "vec":
        return ", ".join(repr(float(x)) for x in part.answer)
    if part.kind == "num":
        return repr(float(part.answer))
    return part.answer


@pytest.mark.parametrize("gen_id", sorted(GENERATORS))
def test_generator_runs_and_self_grades(gen_id):
    for diff in (1, 2, 3):
        for seed in range(1, 26):
            p = make(gen_id, diff, seed)
            assert p.parts, gen_id
            for part in p.parts:
                if part.kind == "choice":
                    assert part.answer in part.options, (gen_id, part.key, part.answer, part.options)
                else:
                    vals = part.answer if part.kind == "vec" else [part.answer]
                    assert all(np.isfinite(float(v)) for v in vals), (gen_id, seed, diff, part.key, part.answer)
                r = grade_part(part, _answer_str(part))
                assert r["correct"], (gen_id, seed, diff, part.key, r)
            assert p.statement and p.solution


def test_all_topic_gens_exist():
    for t, info in TOPICS.items():
        for g in info["gens"]:
            assert g in GENERATORS, (t, g)


def test_plots_render():
    import matplotlib.pyplot as plt
    for gen_id in GENERATORS:
        p = make(gen_id, 2, 7)
        if p.plot:
            fig = p.plot()
            plt.close(fig)
