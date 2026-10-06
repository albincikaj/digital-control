"""Shared Streamlit UI components: problem widget, feedback, timers, badges."""
from __future__ import annotations

import time

import matplotlib.pyplot as plt
import streamlit as st

from . import db, engine
from .curriculum import TOPICS
from .grading import grade_part
from .misconceptions import get as get_misc
from .problems.base import Problem
from .recipes import RECIPES


def fmt_answer(part, val=None):
    v = part.answer if val is None else val
    if part.kind == "vec":
        return "[" + ", ".join(f"{float(x):.4g}" for x in v) + "]"
    if part.kind == "num":
        return f"{float(v):.5g}"
    return str(v)


def countdown(deadline_epoch: float, label: str = "Time left"):
    """Client-side countdown (no reruns needed)."""
    st.iframe(f"""
    <div style="font-family:system-ui,sans-serif;font-size:20px;font-weight:600;padding:4px 10px;border-radius:8px;
                background:#f1f5f9;color:#0f172a;display:inline-block" id="cd">⏱ …</div>
    <script>
    const end = {deadline_epoch * 1000:.0f};
    function tick(){{
      const ms = end - Date.now(); const el = document.getElementById('cd');
      if (ms <= 0) {{ el.innerText = '⏱ {label}: 00:00 — time is up, submit now'; el.style.background='#fee2e2'; el.style.color='#991b1b'; return; }}
      const s = Math.floor(ms/1000), m = Math.floor(s/60), r = s % 60;
      el.innerText = '⏱ {label}: ' + String(m).padStart(2,'0') + ':' + String(r).padStart(2,'0');
      if (ms < 120000) {{ el.style.background='#fef3c7'; el.style.color='#92400e'; }}
      setTimeout(tick, 500);
    }}
    tick();
    </script>""", height=46)


def topic_badge(topic):
    return f":blue-badge[{TOPICS[topic]['name']}]"


def show_plot(prob: Problem):
    if prob.plot:
        try:
            fig = prob.plot()
            st.pyplot(fig, width="content")
            plt.close(fig)
        except Exception as e:  # never let a figure break a session
            st.caption(f"(figure unavailable: {e})")


def _record(prob: Problem, results: dict, hints: int, duration: float, mode: str, raw: dict):
    score = sum(p.points for p in prob.parts if results[p.key]["correct"])
    maxs = prob.max_points
    db.log_attempt(prob.gen_id, prob.topic, prob.difficulty, prob.seed, score, maxs, results, hints, duration, mode)
    frac = score / maxs if maxs else 0
    engine.update_mastery(prob.topic, frac, prob.difficulty)
    xp = engine.xp_for_problem(score, maxs, prob.difficulty, hints)
    if xp:
        db.add_xp(xp, f"{mode}:{prob.gen_id}")
    for p in prob.parts:
        r = results[p.key]
        if not r["correct"]:
            tag = r.get("tag") or f"{prob.gen_id}:{p.key}"
            db.add_mistake(prob.gen_id, prob.topic, prob.difficulty, prob.seed, p.key, tag,
                           r.get("diagnosis") or "", raw.get(p.key), fmt_answer(p))
    new = engine.check_achievements()
    return score, maxs, xp, new


def _part_input(prob, part, k, disabled=False):
    key = f"{k}_in_{part.key}"
    if part.kind == "choice":
        return st.radio(part.label, part.options, index=None, key=key, disabled=disabled, label_visibility="collapsed")
    return st.text_input(part.label, key=key, placeholder=part.placeholder or ("number" if part.kind == "num" else "comma-separated numbers"),
                         disabled=disabled, label_visibility="collapsed")


def feedback_block(prob: Problem, part, res: dict, raw):
    if res.get("error"):
        st.warning(res["error"])
        return
    if res["correct"]:
        st.success(f"✅ Correct — {fmt_answer(part)}")
    else:
        st.error(f"❌ Your answer: `{raw}` → correct: **{fmt_answer(part)}**")
        if res.get("tag"):
            m = get_misc(res["tag"])
            with st.container(border=True):
                st.markdown(f"**Diagnosis — {m['title']}**\n\n{res.get('diagnosis', '')}\n\n**Why:** {m['why']}\n\n**Fix:** {m['fix']}")
                if m.get("gen"):
                    if st.button("🎯 Targeted remediation exercise", key=f"rem_{prob.gen_id}_{prob.seed}_{part.key}"):
                        st.session_state["remedy_request"] = (m["gen"], m["topic"])
                        pages = st.session_state.get("_pages") or {}
                        if "practice" in pages:
                            st.switch_page(pages["practice"])
                        st.rerun()
        elif res.get("diagnosis"):
            st.info(f"🔎 Diagnosis: {res['diagnosis']}")
        else:
            st.info("🔎 No standard slip pattern detected — compare your steps with the worked solution below; the step where your number first differs is the misconception.")
    if part.explain:
        st.markdown(f"**Why:** {part.explain}")


def _fallback_steps(prob, part):
    st_ = []
    if part.hint:
        st_.append(f"💡 {part.hint}")
    if prob.gen_id in RECIPES:
        st_.append("Follow the matching line of the 📋 Recipe above for this step.")
    if part.explain:
        st_.append(part.explain)
    return st_ or ["Compare with the 📖 worked solution after submitting."]


def walkthrough(prob: Problem, part, k: str):
    """Progressive, numbered sub-steps that slice one part and finally reveal its answer."""
    ss = st.session_state
    key = f"{k}_ws_{part.key}"
    n = ss.get(key, 0)
    if n == 0:
        return
    steps = part.steps or _fallback_steps(prob, part)
    with st.container(border=True):
        st.markdown(f"**🪜 Step-by-step** ({min(n, len(steps))}/{len(steps)})")
        for i, txt in enumerate(steps[:n]):
            st.markdown(f"**{i + 1}.** {txt}")
        c1, c2 = st.columns(2)
        if n < len(steps):
            if c1.button("Next sub-step ▶", key=f"{key}_next", type="primary"):
                ss[key] = n + 1
                st.rerun()
            if c2.button("Show all remaining", key=f"{key}_all"):
                ss[key] = len(steps) + 1
                st.rerun()
        else:
            st.success(f"**Answer:** {fmt_answer(part)}")
            if part.explain and part.steps:
                st.caption(f"Why: {part.explain}")
            st.caption("Now type the answer in the box yourself and press *Check step* — writing it once fixes it in memory.")


def render_problem(prob: Problem, k: str, mode: str = "practice", guided: bool = False, record: bool = True,
                   show_solution_after: bool = True, allow_hints: bool = True, show_recipe: bool = True):
    """Render a problem. Returns (graded: bool, score, max) — graded True once submitted."""
    ss = st.session_state
    if f"{k}_t0" not in ss:
        ss[f"{k}_t0"] = time.time()
        ss[f"{k}_hints"] = set()
        ss[f"{k}_graded"] = None
        ss[f"{k}_partial"] = {}

    st.markdown(f"#### {prob.title}")
    st.caption(f"{TOPICS[prob.topic]['name']} · difficulty {'★' * prob.difficulty}{'☆' * (3 - prob.difficulty)} · {prob.source}")
    st.markdown(prob.statement)
    if prob.plot and prob.gen_id in ("zt_signal_exam", "sampling_alias", "rl_pi_design", "jury_gain_range"):
        show_plot(prob)

    graded = ss[f"{k}_graded"]
    if show_recipe and prob.gen_id in RECIPES:
        with st.expander("📋 Recipe — how to solve this type, step by step", expanded=guided):
            st.markdown(RECIPES[prob.gen_id])
    guided = guided or ss.get(f"{k}_guidedmode", False)
    if guided and graded is None:
        # step-by-step: each part checked individually with hints visible
        for part in prob.parts:
            with st.container(border=True):
                st.markdown(f"**Step:** {part.label}" + (f" · *{part.points:g} P*" if part.points else ""))
                if part.hint:
                    st.caption(f"💡 {part.hint}")
                raw = _part_input(prob, part, k)
                b1, b2, _ = st.columns([1, 2, 3])
                if b1.button("Check step", key=f"{k}_chk_{part.key}"):
                    ss[f"{k}_partial"][part.key] = (grade_part(part, raw), raw)
                if b2.button("🪜 Solve it step by step", key=f"{k}_wsbtn_{part.key}",
                             help="Slices this step into small sub-steps with your numbers and finally shows the answer (counts as a hint)."):
                    ss[f"{k}_ws_{part.key}"] = max(1, ss.get(f"{k}_ws_{part.key}", 0))
                    ss[f"{k}_hints"].add(part.key)
                    st.rerun()
                walkthrough(prob, part, k)
                if part.key in ss[f"{k}_partial"]:
                    r, rw = ss[f"{k}_partial"][part.key]
                    feedback_block(prob, part, r, rw)
        if st.button("✔ Finish guided problem", type="primary", key=f"{k}_finish"):
            res, raws = {}, {}
            for part in prob.parts:
                raw = ss.get(f"{k}_in_{part.key}")
                raws[part.key] = raw
                res[part.key] = grade_part(part, raw)
            ss[f"{k}_graded"] = (res, raws)
            if record:
                out = _record(prob, res, len(ss[f"{k}_hints"]) + 1, time.time() - ss[f"{k}_t0"], "guided", raws)
                ss[f"{k}_rec"] = out
            st.rerun()
        return False, 0, prob.max_points

    if graded is None:
        with st.form(f"{k}_form"):
            for part in prob.parts:
                st.markdown(f"{part.label}" + (f" · *{part.points:g} P*" if part.points else ""))
                if allow_hints and part.hint and part.key in ss[f"{k}_hints"]:
                    st.caption(f"💡 {part.hint}")
                _part_input(prob, part, k)
            c1, c2 = st.columns([1, 3])
            submitted = c1.form_submit_button("Submit", type="primary")
        if allow_hints and mode not in ("boss", "speed", "exam"):
            if st.button("🪜 Switch to guided mode (check each step + step-by-step solutions)", key=f"{k}_toguided"):
                ss[f"{k}_guidedmode"] = True
                st.rerun()
        if allow_hints and any(p.hint for p in prob.parts):
            hint_parts = [p for p in prob.parts if p.hint and p.key not in ss[f"{k}_hints"]]
            if hint_parts and st.button(f"💡 Hint (−20 % XP) — {len(hint_parts)} left", key=f"{k}_hintbtn"):
                ss[f"{k}_hints"].add(hint_parts[0].key)
                st.rerun()
        if submitted:
            res, raws = {}, {}
            for part in prob.parts:
                raw = ss.get(f"{k}_in_{part.key}")
                raws[part.key] = raw
                res[part.key] = grade_part(part, raw)
            ss[f"{k}_graded"] = (res, raws)
            if record:
                ss[f"{k}_rec"] = _record(prob, res, len(ss[f"{k}_hints"]), time.time() - ss[f"{k}_t0"], mode, raws)
            st.rerun()
        return False, 0, prob.max_points

    # ---- graded view
    res, raws = graded
    score = sum(p.points for p in prob.parts if res[p.key]["correct"])
    for part in prob.parts:
        with st.container(border=True):
            st.markdown(part.label)
            feedback_block(prob, part, res[part.key], raws.get(part.key))
    rec = ss.get(f"{k}_rec")
    if rec:
        _, _, xp, new = rec
        st.markdown(f"**Score: {score:g} / {prob.max_points:g} P** · +{xp} XP")
        for aid in new:
            name, desc = engine.ACHIEVEMENTS[aid]
            st.toast(f"Achievement unlocked: {name} — {desc}", icon="🏆")
        if score >= prob.max_points - 1e-9:
            st.balloons() if not ss.get(f"{k}_ballooned") else None
            ss[f"{k}_ballooned"] = True
    else:
        st.markdown(f"**Score: {score:g} / {prob.max_points:g} P**")
    if show_solution_after:
        with st.expander("📖 Full worked solution", expanded=score < prob.max_points):
            st.markdown(prob.solution)
            show_plot(prob)
        if prob.matlab:
            with st.expander("🧮 MATLAB recipe (open-book part)"):
                st.code(prob.matlab, language="matlab")
        if prob.remedy:
            st.caption(f"🔑 Key idea: {prob.remedy}")
    return True, score, prob.max_points


def clear_problem_state(k: str):
    for key in list(st.session_state.keys()):
        if key.startswith(k + "_"):
            del st.session_state[key]
