import os
import tempfile

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HDR = """
import os, sys
sys.path.insert(0, {root!r})
os.environ['DC_TRAINER_DB'] = {db!r}
from dctrainer import db, views
db.init()
"""


def _app(body, dbp):
    os.environ["DC_TRAINER_DB"] = dbp
    return AppTest.from_string(HDR.format(root=ROOT, db=dbp) + body, default_timeout=90)


def _ans(part):
    if part.kind == "vec":
        return ", ".join(f"{float(x):.10g}" for x in part.answer)
    if part.kind == "num":
        return f"{float(part.answer):.10g}"
    return part.answer


def _fill(at, prob, prefix, correct=True):
    for part in prob.parts:
        key = f"{prefix}_in_{part.key}"
        if part.kind == "choice":
            val = part.answer if correct else [o for o in part.options if o != part.answer][0]
            at.radio(key=key).set_value(val)
        else:
            val = _ans(part) if correct else ("999" if part.kind == "num" else ", ".join(["999"] * len(part.answer)))
            at.text_input(key=key).set_value(val)


def test_practice_correct_and_wrong():
    dbp = os.path.join(tempfile.mkdtemp(), "t.db")
    at = _app("views.page_practice()", dbp)
    at.run()
    assert not at.exception
    for correct in (True, False):
        prob = at.session_state["practice_prob"]
        prefix = f"pr_{prob.gen_id}_{prob.seed}"
        _fill(at, prob, prefix, correct)
        [b for b in at.button if b.label == "Submit"][0].click()
        at.run()
        assert not at.exception, [e.message for e in at.exception]
        res, _ = at.session_state[f"{prefix}_graded"]
        assert all(r["correct"] for r in res.values()) == correct, res
        nxt = [b for b in at.button if b.label.startswith("Next problem")]
        assert nxt
        nxt[0].click()
        at.run()
        assert not at.exception
    import sqlite3
    c = sqlite3.connect(dbp)
    assert c.execute("select count(*) from attempts").fetchone()[0] == 2
    assert c.execute("select count(*) from mistakes").fetchone()[0] >= 1
    assert c.execute("select sum(amount) from xp_log").fetchone()[0] > 0


def test_every_generator_through_widget():
    """Render + submit every generator through the real widget (correct answers)."""
    from dctrainer.problems.registry import GENERATORS
    dbp = os.path.join(tempfile.mkdtemp(), "t.db")
    body = """
import streamlit as st
from dctrainer.problems.registry import make
from dctrainer.ui import render_problem
g = st.session_state.get('g')
if g:
    if 'p' not in st.session_state:
        st.session_state['p'] = make(g, 2, 11)
    p = st.session_state['p']
    render_problem(p, 'w', mode='test')
"""
    for g in sorted(GENERATORS):
        at = _app(body, dbp)
        at.session_state["g"] = g
        at.run()
        assert not at.exception, (g, [e.message for e in at.exception])
        prob = at.session_state["p"]
        _fill(at, prob, "w", True)
        [b for b in at.button if b.label == "Submit"][0].click()
        at.run()
        assert not at.exception, (g, [e.message for e in at.exception])
        res, _ = at.session_state["w_graded"]
        assert all(r["correct"] for r in res.values()), (g, res)


def test_learn_module_all_steps():
    from dctrainer.views import STEPS as views_steps
    dbp = os.path.join(tempfile.mkdtemp(), "t.db")
    at = _app("views.page_learn()", dbp)
    at.run()
    for topic in ["f_complex", "f_matrix", "zt_basics", "zoh_plant", "pole_placement", "observers", "lqr", "sampling"]:
        at.session_state["learn_topic"] = topic
        at.session_state[f"learnstep_{topic}"] = "1 Intuition"
        os.environ["DC_TRAINER_DB"] = dbp
        db_set = _app(f"db.set_setting('cram_mode', True)", dbp)
        db_set.run()
        at.run()
        for step in range(8):
            at.session_state[f"learnstep_{topic}"] = views_steps[step]
            at.run()
            assert not at.exception, (topic, step, [e.message for e in at.exception])


def test_exam_flow_full():
    dbp = os.path.join(tempfile.mkdtemp(), "t.db")
    at = _app("views.page_exam()", dbp)
    at.run()
    [b for b in at.button if b.label == "Start exam"][0].click()
    at.run()
    assert not at.exception
    ex = at.session_state["exam"]
    assert ex["phase"] == "theory" and ex["cards"]
    [b for b in at.button if b.label.startswith("Hand in theory")][0].click()
    at.run()
    ex = at.session_state["exam"]
    assert ex["phase"] == "practical"
    # answer everything correctly
    for key, plist in ex["probs"].items():
        for prob in plist:
            for part in prob.parts:
                kk = f"ex_{prob.gen_id}_{prob.seed}_{part.key}"
                if part.kind == "choice":
                    at.radio(key=kk).set_value(part.answer)
                else:
                    at.text_input(key=kk).set_value(_ans(part))
    [b for b in at.button if b.label.startswith("Hand in practical")][0].click()
    at.run()
    assert not at.exception, [e.message for e in at.exception]
    [b for b in at.button if b.label == "Compute results"][0].click()
    at.run()
    assert not at.exception, [e.message for e in at.exception]
    ex = at.session_state["exam"]
    assert abs(ex["prac"] - 35) < 1e-6, ex["prac"]


def test_boss_first_stage():
    dbp = os.path.join(tempfile.mkdtemp(), "t.db")
    at = _app("views.page_boss()", dbp)
    at.run()
    [b for b in at.button if b.key == "fight_ss_titan"][0].click()
    at.run()
    assert not at.exception
    battle = at.session_state["battle"]
    for i in range(len(battle["probs"])):
        prob = at.session_state["battle"]["probs"][i]
        prefix = f"bo_{prob.gen_id}_{prob.seed}"
        _fill(at, prob, prefix, True)
        [b for b in at.button if b.label == "Submit"][0].click()
        at.run()
        assert not at.exception, [e.message for e in at.exception]
        [b for b in at.button if b.label.startswith("Next stage")][0].click()
        at.run()
        assert not at.exception, [e.message for e in at.exception]
    import sqlite3
    assert sqlite3.connect(dbp).execute("select won from bosses").fetchone()[0] == 1


def test_walkthrough_every_generator():
    from dctrainer.problems.registry import GENERATORS
    dbp = os.path.join(tempfile.mkdtemp(), "t.db")
    body = """
import streamlit as st
from dctrainer.problems.registry import make
from dctrainer.ui import render_problem
g = st.session_state.get('g')
if 'p' not in st.session_state:
    st.session_state['p'] = make(g, 2, 7)
render_problem(st.session_state['p'], 'w', mode='test', guided=True)
"""
    for g in sorted(GENERATORS):
        at = _app(body, dbp)
        at.session_state["g"] = g
        at.run()
        prob = at.session_state["p"]
        for part in prob.parts:
            [b for b in at.button if b.key == f"w_wsbtn_{part.key}"][0].click()
            at.run()
            assert not at.exception, (g, [e.message for e in at.exception])
            alls = [b for b in at.button if b.key == f"w_ws_{part.key}_all"]
            if alls:
                alls[0].click()
                at.run()
                assert not at.exception, (g, [e.message for e in at.exception])
            assert any("Answer:" in s.value for s in at.success), (g, part.key)
