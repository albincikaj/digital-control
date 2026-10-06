"""All Streamlit pages."""
from __future__ import annotations

import random
import time
from datetime import date, timedelta

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from . import db, engine
from .content import MODULES
from .content_beginner import FOUNDATION_MODULES, PRIMERS
from .curriculum import EXAM_TOPICS, ORDER, TOPICS
from .grading import grade_part
from .misconceptions import MISCONCEPTIONS, get as get_misc
from .problems.registry import GENERATORS, make
from .theory import BY_ID, CARDS, EXAM_CARDS, SHORT, card_points
from .ui import clear_problem_state, countdown, fmt_answer, render_problem, show_plot

PAGES: dict = {}


def module(t):
    return MODULES.get(t) or FOUNDATION_MODULES[t]
GEN_TOPIC = {g: t for t, info in TOPICS.items() for g in info["gens"]}


def goto(name: str):
    if name in PAGES:
        st.switch_page(PAGES[name])


# ======================================================================== sidebar
def sidebar():
    xp = db.total_xp()
    lvl, title, frac, need = engine.level_info(xp)
    with st.sidebar:
        st.markdown(f"### Lv {lvl} · {title}")
        st.progress(min(1.0, frac), text=f"{xp} XP · {need} to next level")
        goal = engine.daily_goal()
        txp = engine.today_xp()
        st.progress(min(1.0, txp / goal), text=f"Today: {txp}/{goal} XP")
        st.markdown(f"🔥 Streak **{engine.streak()}** day(s) · 📓 {db.count('mistakes', 'resolved=0')} open mistakes")
        dte = engine.days_to_exam()
        if dte is not None:
            st.markdown(f"📅 Exam in **{dte}** day(s) · Plan day **{engine.plan_day()}/5**")


# ======================================================================== dashboard
def page_dashboard():
    st.title("Digital Control — Exam Trainer")
    er = engine.exam_ready()
    xp = db.total_xp()
    lvl, title, frac, need = engine.level_info(xp)
    c = st.columns(4)
    c[0].metric("Exam-Ready score", f"{er['score']:.0f} %", help="Exam-weighted mastery (practical problems + theory cards), blended 60/40 with your last two mock exams.")
    c[1].metric("Expected points", f"{er['expected_pts']:.1f} / 50", er["grade"], delta_color="off")
    c[2].metric(f"Level {lvl}", title, f"{xp} XP", delta_color="off")
    c[3].metric("Streak", f"{engine.streak()} days", f"today {engine.today_xp()}/{engine.daily_goal()} XP", delta_color="off")
    st.progress(min(1.0, er["score"] / 100), text="Exam readiness (≥ 50 % ≈ pass, ≥ 75 % ≈ good)")
    if er["mock"] is None:
        st.caption("No mock exam yet — readiness is capped at 85 % of mastery until you prove it under exam conditions.")

    rec = engine.recommendation()
    with st.container(border=True):
        st.markdown(f"#### ▶ Next best action\n{rec['label']}")
        if st.button("Go", type="primary", key="dash_go"):
            if rec.get("topic"):
                st.session_state["learn_topic"] = rec["topic"]
                st.session_state["practice_topic"] = rec["topic"]
            if rec.get("boss"):
                st.session_state["boss_sel"] = rec["boss"]
            goto(rec["page"])

    day = engine.plan_day()
    plan = engine.get_plan()[day]
    if engine.track() == "beginner":
        with st.container(border=True):
            st.markdown("""#### 🎯 Pass strategy (starting from zero) — target ≥ 25 / 50
| Source | Realistic points | How |
|---|---|---|
| P3 Jury + factored form | 5–6 | pure bookkeeping recipe — drill until fast |
| P1 z-transform | 5–7 | recipe: samples → U(z) → recursion → final value |
| P2 ZOH + closed loop | 4–6 | partial fractions + table recipe, check with MATLAB `c2d` |
| Theory (closed book) | 7–10 | memorise the ⭐ short answers (Review → Must memorise) |
| P4 state space | 4–8 | MATLAB recipes: `ctrb/obsv`, augmented `acker`, observer `acker(G',c',p)'` |
| **Total** | **25–37** | |

Order of effort: Jury → P1 → theory cards → P2 → P4 recipes. Skip deep Ch. 4 theory beyond one-sentence answers.""")
    left, right = st.columns([3, 2])
    with left:
        st.subheader(plan["title"])
        for t in plan["topics"]:
            m = db.mastery_get(t)
            icon = "✅" if m.get("learned") else "⬜"
            st.markdown(f"{icon} **{TOPICS[t]['name']}** — mastery {m['value'] * 100:.0f} %  \n<small>{TOPICS[t]['why']}</small>", unsafe_allow_html=True)
        st.markdown("**Goals today**\n" + "\n".join(f"- {g}" for g in plan["goals"]))
    with right:
        st.subheader("Weak spots")
        for t in engine.weakest_topics(4):
            st.markdown(f"- {TOPICS[t]['name']}: {er['per_topic'][t] * 100:.0f} %")
        due_c = len([c for c in engine.due_cards() if db.card_get(c['id'])['reps'] > 0])
        st.markdown(f"**Due:** {due_c} theory cards · {len(engine.due_topics())} topic reviews · "
                    f"{len([m for m in db.open_mistakes() if db.parse(m['due']) <= db.now()])} mistakes")
        st.subheader("Exam format (2016/2017 + infosheet 2026)")
        st.markdown("""| Part | Points | Content |
|---|---|---|
| Theory (closed book, 15 min) | 15 | definitions, ideas, sketches |
| P1 z-transform | 6–7 | U(z), FVT, diff. eq., y(k) / inverse z |
| P2 ZOH + closed loop | 7 | G(z) by hand, G_W, stability, G_d? |
| P3 Stability | 6 | Jury table + factored form |
| P4 State space | 15–16 | ctrb/obsv, pole placement + integrator / LQR, observer |
Pass ≥ 25/50 · 2: ≥ 37.5 · 1: ≥ 43.75""")


# ======================================================================== plan
def page_plan():
    st.title("5-day mastery curriculum")
    st.caption("Ordered by prerequisite importance × exam points (from the 2016/2017 exams) × difficulty. Day = days since you started the plan (Settings).")
    cur = engine.plan_day()
    st.info("Track: **" + ("Beginner — pass first" if engine.track() == "beginner" else "Standard") + "** (change in Settings).")
    for d, plan in engine.get_plan().items():
        with st.expander(f"{'👉 ' if d == cur else ''}{plan['title']}", expanded=(d == cur)):
            for t in plan["topics"]:
                m = db.mastery_get(t)
                st.markdown(f"- {'✅' if m.get('learned') else '⬜'} **{TOPICS[t]['name']}** (Book {TOPICS[t]['chapter']}, ~{TOPICS[t]['exam_pts']:g} exam P) — {TOPICS[t]['why']}")
            st.markdown("**Goals:**\n" + "\n".join(f"- {g}" for g in plan["goals"]))
            if plan.get("boss"):
                b = engine.BOSSES[plan["boss"]]
                st.markdown(f"**Boss:** {b['icon']} {b['name']} ({b['exam']})")
    st.subheader("Study protocol per session (≈ 90 min blocks)")
    st.markdown("""1. **Learn module** (Intuition → Visual → Math → Worked example → Guided → Independent → Feedback → Retrieval quiz), ~25 min per topic.
2. **Practice** the topic until mastery ≥ 70 % (difficulty adapts automatically).
3. **Theory cards** — 15 min, answer *in writing* before revealing (exactly like the closed-book part).
4. **Mistake notebook** — fix everything due.
5. End of day: **Boss battle** of the day; Day 3 & 5 evenings: **full mock exam** with timer.
6. Practical part is open book with MATLAB: copy the *MATLAB recipe* of each problem type into your own cheat file.""")


# ======================================================================== mastery map
def page_map():
    st.title("Mastery map")
    mast = db.mastery_all()
    er = engine.exam_ready()["per_topic"]
    lines = ["digraph G {", 'rankdir=LR; bgcolor="transparent"; node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11];']
    for t in ORDER:
        v = mast.get(t, {}).get("value", 0.0)
        unlocked = engine.is_unlocked(t, mast)
        if not unlocked:
            color, font = "#e5e7eb", "#6b7280"
            label = f"🔒 {TOPICS[t]['name']}"
        else:
            r = er.get(t, 0)
            color = "#dcfce7" if r >= 0.75 else ("#fef9c3" if r >= 0.4 else ("#fee2e2" if mast.get(t, {}).get("attempts") else "#ffffff"))
            font = "#111827"
            label = f"{TOPICS[t]['name']}\\n{v * 100:.0f} % · {TOPICS[t]['exam_pts']:g} P"
        lines.append(f'"{t}" [label="{label}", fillcolor="{color}", fontcolor="{font}"];')
    for t in ORDER:
        for p in TOPICS[t]["prereq"]:
            lines.append(f'"{p}" -> "{t}";')
    lines.append("}")
    st.graphviz_chart("\n".join(lines), width="stretch")
    st.caption("White = not started · red < 40 % · yellow 40–75 % · green ≥ 75 % (exam-weighted readiness) · grey = locked (prerequisites < 50 %).")
    st.subheader("Topics")
    for t in ORDER:
        m = mast.get(t, {})
        unlocked = engine.is_unlocked(t, mast)
        c1, c2, c3 = st.columns([3, 4, 2])
        c1.markdown(f"{'🔓' if unlocked else '🔒'} **{TOPICS[t]['name']}**")
        c2.progress(min(1.0, m.get("value", 0.0)), text=f"mastery {m.get('value', 0) * 100:.0f} % · readiness {er.get(t, 0) * 100:.0f} %")
        if not unlocked:
            if c3.button("Unlock anyway", key=f"unl_{t}"):
                engine.manual_unlock(t)
                st.rerun()
        elif c3.button("Learn", key=f"learn_{t}"):
            st.session_state["learn_topic"] = t
            goto("learn")


# ======================================================================== learn
STEPS = ["0 Plain-language primer", "1 Intuition", "2 Visual", "3 Math", "4 Worked example", "5 Guided problem", "6 Independent problem", "7 Feedback", "8 Retrieval quiz"]


def page_learn():
    st.title("Learning modules")
    mast = db.mastery_all()
    default = st.session_state.get("learn_topic", ORDER[0])
    labels = {t: f"{'✅ ' if mast.get(t, {}).get('learned') else ''}{'🔒 ' if not engine.is_unlocked(t, mast) else ''}{TOPICS[t]['name']}" for t in ORDER}
    topic = st.selectbox("Topic", ORDER, index=ORDER.index(default), format_func=lambda t: labels[t])
    st.session_state["learn_topic"] = topic
    T = TOPICS[topic]
    if not engine.is_unlocked(topic, mast):
        missing = [TOPICS[p]["name"] for p in T["prereq"] if mast.get(p, {}).get("value", 0) < 0.5]
        st.warning(f"🔒 Locked — reach 50 % mastery in: {', '.join(missing)}.")
        if st.button("Unlock anyway (cram mode for this topic)"):
            engine.manual_unlock(topic)
            st.rerun()
        return
    st.caption(f"Book chapter {T['chapter']} · ≈ {T['exam_pts']:g} exam points · {T['why']}")
    M = module(topic)
    sk = f"learnstep_{topic}"
    if sk not in st.session_state:
        st.session_state[sk] = STEPS[0]
    step = STEPS.index(st.radio("Step", STEPS, key=sk, horizontal=True))
    st.progress((step + 1) / len(STEPS))

    if step == 0:
        st.subheader("Plain-language primer (no background assumed)")
        if topic in PRIMERS:
            st.markdown(PRIMERS[topic])
        else:
            st.markdown(M["intuition"])
            st.caption("Foundation module: the primer is the intuition itself — continue to the visual and the math, then drill.")
    elif step == 1:
        st.subheader("Intuition")
        st.markdown(M["intuition"])
    elif step == 2:
        st.subheader("Visual / conceptual picture")
        if M.get("visual"):
            fig = M["visual"]()
            st.pyplot(fig, width="content")
            plt.close(fig)
            st.caption(M.get("visual_caption", ""))
        else:
            st.info("This topic is best seen through its matrices — see the next step.")
    elif step == 3:
        st.subheader("Mathematics (course notation)")
        st.markdown(M["math"])
    elif step == 4:
        st.subheader("Worked example from your material")
        st.markdown(M["worked"])
        if M.get("matlab"):
            with st.expander("MATLAB"):
                st.code(M["matlab"], language="matlab")
    elif step == 5:
        st.subheader("Guided problem (hints visible, check each step)")
        gk = f"learn_g_{topic}"
        if gk not in st.session_state:
            st.session_state[gk] = make(T["gens"][0], 1, random.randint(1, 10 ** 6))
        prob = st.session_state[gk]
        done, *_ = render_problem(prob, f"{gk}_{prob.seed}", mode="guided", guided=True)
        if done and st.button("Another guided problem"):
            clear_problem_state(f"{gk}_{prob.seed}")
            del st.session_state[gk]
            st.rerun()
    elif step == 6:
        st.subheader("Independent problem (no hints shown, adaptive difficulty)")
        ik = f"learn_i_{topic}"
        if ik not in st.session_state:
            g = random.choice(T["gens"])
            st.session_state[ik] = make(g, max(2, engine.adaptive_difficulty(topic)) if len(T["gens"]) else 2, random.randint(1, 10 ** 6))
        prob = st.session_state[ik]
        done, *_ = render_problem(prob, f"{ik}_{prob.seed}", mode="learn")
        if done and st.button("Another independent problem"):
            clear_problem_state(f"{ik}_{prob.seed}")
            del st.session_state[ik]
            st.rerun()
    elif step == 7:
        st.subheader("Feedback & common pitfalls")
        att = db.attempts(limit=20, topic=topic)
        if att:
            acc = np.mean([a["score"] / a["max_score"] for a in att if a["max_score"]])
            st.metric("Your recent accuracy in this topic", f"{acc * 100:.0f} %")
        tags = db.rows("SELECT tag, COUNT(*) n FROM mistakes WHERE topic=? GROUP BY tag ORDER BY n DESC", (topic,))
        if tags:
            st.markdown("**Your misconceptions here:**")
            for t in tags[:5]:
                m = get_misc(t["tag"])
                st.markdown(f"- **{m['title']}** ({t['n']}×) — {m['fix']}")
        st.markdown("**Pitfalls the graders punished / the book warns about:**\n" + "\n".join(f"- {p}" for p in M["pitfalls"]))
    elif step == 8:
        st.subheader("Retrieval quiz (answer from memory, then self-grade with the rubric)")
        cards = sorted([c for c in CARDS if c["topic"] == topic], key=lambda c: c["id"] not in SHORT)[:3]
        if not cards:
            st.info("Foundation topic — the retrieval quiz is a quick drill: solve 3 problems in Practice without the recipe open.")
        for c in cards:
            theory_card_widget(c, f"lq_{topic}")
        if st.button("✅ Mark module complete (+40 XP)", type="primary"):
            if not db.mastery_get(topic).get("learned"):
                engine.mark_learned(topic)
                db.add_xp(40, f"module:{topic}")
                for aid in engine.check_achievements():
                    st.toast(f"Achievement: {engine.ACHIEVEMENTS[aid][0]}", icon="🏆")
            st.success("Module completed. Practice until mastery ≥ 70 %, then move on.")
    def _go(delta):
        st.session_state[sk] = STEPS[step + delta]

    c1, c2 = st.columns(2)
    if step > 0:
        c1.button("◀ Back", on_click=_go, args=(-1,))
    if step < len(STEPS) - 1:
        c2.button("Next ▶", type="primary", on_click=_go, args=(1,))


# ======================================================================== theory card widget
def theory_card_widget(card, prefix, on_scored=None):
    k = f"{prefix}_{card['id']}"
    with st.container(border=True):
        st.markdown(f"**{card['q']}**  \n<small>{card_points(card):g} P{(' · past exam: ' + card['exam']) if card['exam'] else ''}</small>", unsafe_allow_html=True)
        st.text_area("Your answer (write it as in the exam)", key=f"{k}_ans", height=100, label_visibility="collapsed",
                     placeholder="Write your answer before revealing…")
        if not st.session_state.get(f"{k}_rev"):
            if st.button("Reveal model answer", key=f"{k}_revbtn"):
                st.session_state[f"{k}_rev"] = True
                st.rerun()
            return None
        if card["id"] in SHORT:
            st.success(f"⭐ **Memorise this answer:** {SHORT[card['id']]}")
        with st.expander("Full model answer", expanded=card["id"] not in SHORT):
            st.markdown(card["a"])
            st.caption(f"Source: {card['src']}")
        pts = 0.0
        for i, (crit, p) in enumerate(card["rubric"]):
            if st.checkbox(f"{crit} ({p:g} P)", key=f"{k}_r{i}"):
                pts += p
        if st.session_state.get(f"{k}_saved"):
            st.success(f"Saved: {st.session_state[f'{k}_saved']:.2g}/{card_points(card):g} P")
            return st.session_state[f"{k}_saved"]
        if st.button("Save self-grade", key=f"{k}_save"):
            frac = pts / card_points(card)
            engine.review_card(card["id"], frac)
            db.add_xp(int(round(8 * card_points(card) * frac)) + 2, f"card:{card['id']}")
            st.session_state[f"{k}_saved"] = pts
            if on_scored:
                on_scored(card, pts)
            for aid in engine.check_achievements():
                st.toast(f"Achievement: {engine.ACHIEVEMENTS[aid][0]}", icon="🏆")
            st.rerun()
    return None


# ======================================================================== practice
def page_practice():
    st.title("Practice")
    ss = st.session_state
    remedy = ss.pop("remedy_request", None)
    if remedy:
        gen, topic = remedy
        ss["practice_prob"] = make(gen, 1, random.randint(1, 10 ** 6))
        ss["practice_banner"] = "🎯 Targeted remediation exercise (difficulty 1) for the misconception you just showed."
    mast = db.mastery_all()
    options = ["⭐ Adaptive (recommended)"] + [t for t in ORDER if engine.is_unlocked(t, mast)]
    cur = ss.get("practice_topic")
    idx = options.index(cur) if cur in options else 0
    c1, c2, c3 = st.columns([3, 2, 2])
    sel = c1.selectbox("Topic", options, index=idx, format_func=lambda t: t if t.startswith("⭐") else TOPICS[t]["name"])
    gen_opts = ["any"] + (TOPICS[sel]["gens"] if sel in TOPICS else [])
    gsel = c2.selectbox("Problem type", gen_opts)
    dsel = c3.selectbox("Difficulty", ["auto", 1, 2, 3])
    if sel != cur:
        ss["practice_topic"] = sel

    def new_problem():
        topic = sel
        if topic.startswith("⭐"):
            due = engine.due_topics()
            topic = due[0] if due else engine.weakest_topics(1)[0]
        g = gsel if gsel != "any" else random.choice(TOPICS[topic]["gens"])
        d = engine.adaptive_difficulty(topic) if dsel == "auto" else int(dsel)
        ss["practice_prob"] = make(g, d, random.randint(1, 10 ** 6))
        ss.pop("practice_banner", None)

    cur_p = ss.get("practice_prob")
    stale = cur_p is not None and not ss.get("practice_banner") and (
        (sel in TOPICS and cur_p.topic != sel) or (gsel != "any" and cur_p.gen_id != gsel))
    if cur_p is None or stale:
        new_problem()
    elif st.button("🎲 New problem", type="primary"):
        clear_problem_state(f"pr_{cur_p.gen_id}_{cur_p.seed}")
        new_problem()
        st.rerun()
    if ss.get("practice_banner"):
        st.info(ss["practice_banner"])
    prob = ss["practice_prob"]
    m = db.mastery_get(prob.topic)
    st.progress(min(1.0, m["value"]), text=f"Mastery in {TOPICS[prob.topic]['name']}: {m['value'] * 100:.0f} %")
    done, score, mx = render_problem(prob, f"pr_{prob.gen_id}_{prob.seed}", mode="practice")
    if done:
        if st.button("Next problem ▶", type="primary", key="pr_next"):
            clear_problem_state(f"pr_{prob.gen_id}_{prob.seed}")
            new_problem()
            st.rerun()


# ======================================================================== review
def page_review():
    st.title("Spaced repetition")
    tab1, tab2 = st.tabs(["🧠 Theory cards (closed-book part)", "🔁 Topic reviews"])
    with tab1:
        due = engine.due_cards()
        reviewed = [c for c in due if db.card_get(c["id"])["reps"] > 0]
        new = [c for c in due if db.card_get(c["id"])["reps"] == 0]
        st.caption(f"{len(reviewed)} due for review · {len(new)} new · {len(CARDS)} cards total (past-exam questions first).")
        flt = st.radio("Filter", ["⭐ Must memorise", "Due + new", "Past-exam questions only", "By topic"], horizontal=True)
        pool = due
        if flt.startswith("⭐"):
            pool = [BY_ID[c] for c in SHORT]
            st.caption("The 20 answers most likely to earn points in the closed-book part. Write each answer from memory, then compare.")
        elif flt == "Past-exam questions only":
            pool = [c for c in CARDS if c["exam"]]
        elif flt == "By topic":
            t = st.selectbox("Topic", ORDER, format_func=lambda x: TOPICS[x]["name"], key="rev_topic")
            pool = [c for c in CARDS if c["topic"] == t]
        if not pool:
            st.success("Nothing due right now 🎉")
        else:
            i = st.session_state.get("rev_idx", 0) % len(pool)
            card = pool[i]
            st.markdown(f"Card {i + 1}/{len(pool)} · topic: {TOPICS[card['topic']]['name']}")
            theory_card_widget(card, f"rev{st.session_state.get('rev_round', 0)}")
            if st.button("Next card ▶"):
                st.session_state["rev_idx"] = i + 1
                st.session_state["rev_round"] = st.session_state.get("rev_round", 0) + 1
                st.rerun()
    with tab2:
        dt = engine.due_topics()
        if not dt:
            st.success("No topic reviews due. Topics come back after 0.5 → 1 → 2 → 4 days, failed ones after 10 minutes.")
        for t in dt:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{TOPICS[t]['name']}** — mastery {db.mastery_get(t)['value'] * 100:.0f} %")
            if c2.button("Review", key=f"revt_{t}"):
                st.session_state["practice_topic"] = t
                st.session_state.pop("practice_prob", None)
                goto("practice")


# ======================================================================== mistakes
def page_mistakes():
    st.title("Mistake notebook")
    om = db.open_mistakes()
    st.caption("Every wrong part lands here with its diagnosis. Solve a fresh remediation problem of the same type perfectly to resolve it; "
               "unresolved entries resurface every 10 minutes and push the topic back into review.")
    if not om:
        st.success("Notebook empty — no open mistakes. 🎉")
    groups = {}
    for m in om:
        groups.setdefault(m["tag"], []).append(m)
    ss = st.session_state
    active = ss.get("mist_active")
    if active:
        m = next((x for x in om if x["id"] == active["id"]), None)
        st.subheader("Remediation")
        prob = active["prob"]
        done, score, mx = render_problem(prob, f"mi_{prob.gen_id}_{prob.seed}", mode="remedy")
        if done:
            ok = score >= mx - 1e-9
            if m and not active.get("applied"):
                if ok:
                    db.update_mistake(m["id"], resolved=1, streak=(m["streak"] or 0) + 1)
                    db.add_xp(15, "mistake_fixed")
                    st.success("Resolved ✔ (+15 XP)")
                else:
                    db.update_mistake(m["id"], due=db.plus_days(10 / 1440), streak=0)
                    st.warning("Not yet — it will come back in 10 minutes.")
                active["applied"] = True
                engine.check_achievements()
            if st.button("Back to notebook"):
                clear_problem_state(f"mi_{prob.gen_id}_{prob.seed}")
                ss.pop("mist_active", None)
                st.rerun()
        st.divider()
    for tag, ms in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        info = get_misc(tag)
        title = info["title"] if tag in MISCONCEPTIONS else f"{tag.split(':')[0]} — part '{tag.split(':')[-1]}'"
        with st.expander(f"{title} — {len(ms)} open"):
            if tag in MISCONCEPTIONS:
                st.markdown(f"**Why it is wrong:** {info['why']}\n\n**Fix:** {info['fix']}")
            for m in ms[:8]:
                due = db.parse(m["due"]) <= db.now()
                st.markdown(f"- {m['ts'][:16]} · {TOPICS.get(m['topic'], {}).get('name', m['topic'])} · your answer `{m['user_answer']}` · correct `{m['correct_answer']}`"
                            + (f"  \n  _{m['diagnosis']}_" if m["diagnosis"] else "") + ("  ⏰ due" if due else ""))
                c1, c2 = st.columns(2)
                if c1.button("Fix with a new problem", key=f"fix_{m['id']}"):
                    gen = info.get("gen") if tag in MISCONCEPTIONS and info.get("gen") else m["gen_id"]
                    ss["mist_active"] = dict(id=m["id"], prob=make(gen, max(1, (m["difficulty"] or 2) - 1), random.randint(1, 10 ** 6)))
                    st.rerun()
                if c2.button("Retry the original", key=f"orig_{m['id']}"):
                    ss["mist_active"] = dict(id=m["id"], prob=make(m["gen_id"], m["difficulty"], m["seed"]))
                    st.rerun()
    st.subheader("Misconception statistics")
    tags = db.rows("SELECT tag, COUNT(*) n, SUM(resolved) r FROM mistakes GROUP BY tag ORDER BY n DESC LIMIT 12")
    if tags:
        for t in tags:
            st.markdown(f"- {get_misc(t['tag'])['title'] if t['tag'] in MISCONCEPTIONS else t['tag']}: {t['n']}× ({t['r'] or 0} resolved)")


# ======================================================================== speed run
def page_speed():
    st.title("⚡ Speed run — 10 minutes")
    ss = st.session_state
    sr = ss.get("speed")
    st.caption(f"Short items from all unlocked topics. Personal best: {db.get_setting('speed_best', 0)} P")
    if not sr:
        if st.button("Start 10-minute run", type="primary"):
            ss["speed"] = dict(deadline=time.time() + 600, score=0.0, n=0, prob=None, t0=time.time())
            st.rerun()
        return
    if time.time() > sr["deadline"]:
        st.subheader(f"Time! Score: {sr['score']:g} P in {sr['n']} items")
        if sr["score"] > (db.get_setting("speed_best", 0) or 0):
            db.set_setting("speed_best", sr["score"])
            st.success("New personal best!")
        if not sr.get("xp_given"):
            db.add_xp(int(10 * sr["score"]), "speed_run")
            sr["xp_given"] = True
            engine.check_achievements()
        if st.button("Finish"):
            ss.pop("speed")
            st.rerun()
        return
    countdown(sr["deadline"], "Speed run")
    st.metric("Score", f"{sr['score']:g} P", f"{sr['n']} items")
    if sr["prob"] is None:
        g = random.choice(engine.SPEED_POOL)
        sr["prob"] = make(g, engine.adaptive_difficulty(GEN_TOPIC.get(g, "zt_basics")), random.randint(1, 10 ** 6))
    prob = sr["prob"]
    k = f"sp_{prob.gen_id}_{prob.seed}"
    done, score, mx = render_problem(prob, k, mode="speed", allow_hints=False, show_recipe=False)
    if done:
        if not ss.get(f"{k}_counted"):
            sr["score"] += score
            sr["n"] += 1
            ss[f"{k}_counted"] = True
        if st.button("Next ▶", type="primary"):
            clear_problem_state(k)
            sr["prob"] = None
            st.rerun()


# ======================================================================== bosses
def page_boss():
    st.title("🐉 Boss battles")
    ss = st.session_state
    battle = ss.get("battle")
    if battle:
        _run_battle(battle)
        return
    wins = {r["boss_id"] for r in db.rows("SELECT boss_id FROM bosses WHERE won=1")}
    cols = st.columns(3)
    for i, (bid, b) in enumerate(engine.BOSSES.items()):
        with cols[i % 3].container(border=True):
            best = db.scalar("SELECT MAX(score*1.0/max_score) FROM bosses WHERE boss_id=?", (bid,))
            st.markdown(f"### {b['icon']} {b['name']}\n*{b['exam']}* · {b['minutes']} min\n\n{b['lore']}")
            st.markdown(f"{'🏆 Defeated' if bid in wins else '⚔️ Undefeated'} · best {best * 100:.0f} %" if best is not None else "⚔️ Not fought yet")
            if st.button("Fight", key=f"fight_{bid}", type="primary" if ss.get("boss_sel") == bid else "secondary"):
                probs = [make(g, d, random.randint(1, 10 ** 6)) for g, d in b["stages"]]
                ss["battle"] = dict(id=bid, probs=probs, stage=0, scores=[], t0=time.time(), deadline=time.time() + 60 * b["minutes"])
                st.rerun()


def _run_battle(battle):
    ss = st.session_state
    b = engine.BOSSES[battle["id"]]
    maxhp = sum(p.max_points for p in battle["probs"])
    dmg = sum(battle["scores"])
    st.subheader(f"{b['icon']} {b['name']} — stage {min(battle['stage'] + 1, len(battle['probs']))}/{len(battle['probs'])}")
    st.progress(max(0.0, 1 - dmg / maxhp), text=f"Boss HP {maxhp - dmg:g}/{maxhp:g} (deal ≥ 70 % damage to win)")
    countdown(battle["deadline"], "Boss timer")
    if battle["stage"] >= len(battle["probs"]):
        frac = dmg / maxhp
        won = frac >= 0.7
        in_time = time.time() <= battle["deadline"] + 5
        if not battle.get("logged"):
            db.log_boss(battle["id"], dmg, maxhp, won, time.time() - battle["t0"])
            db.add_xp((200 if won else 50) + (50 if won and in_time else 0), f"boss:{battle['id']}")
            battle["logged"] = True
            battle["new"] = engine.check_achievements()
        if won:
            st.success(f"🏆 Victory! {frac * 100:.0f} % damage{' within the time limit (+50 XP)' if in_time else ' (over time)'}.")
            st.balloons()
        else:
            st.error(f"Defeat — {frac * 100:.0f} % damage. Check the mistake notebook, then try again.")
        for aid in battle.get("new", []):
            st.toast(f"Achievement: {engine.ACHIEVEMENTS[aid][0]}", icon="🏆")
        if st.button("Leave arena"):
            ss.pop("battle")
            st.rerun()
        return
    prob = battle["probs"][battle["stage"]]
    k = f"bo_{prob.gen_id}_{prob.seed}"
    done, score, mx = render_problem(prob, k, mode="boss", allow_hints=False)
    if done:
        if not ss.get(f"{k}_counted"):
            battle["scores"].append(score)
            ss[f"{k}_counted"] = True
        if st.button("Next stage ▶", type="primary"):
            clear_problem_state(k)
            battle["stage"] += 1
            st.rerun()
    if st.button("Flee (forfeit)"):
        ss.pop("battle")
        st.rerun()


# ======================================================================== exam simulation
EXAM_LAYOUT = {
    "P1": dict(title="Problem 1: z-transform", pts=7, options=[[("zt_signal_exam", 2)], [("zt_inverse_comp", 2)]]),
    "P2": dict(title="Problem 2: Zero-order hold and continuous-time plant", pts=7, options=[[("zoh_plant", 2), ("closed_loop_P", 2)]]),
    "P3": dict(title="Problem 3: Stability", pts=6, options=[[("jury_cubic", 2), ("stability_factored", 1)]]),
    "P4": dict(title="Problem 4: State space design", pts=15,
               options=[[("ctrb_obsv", 3), ("integral_sf", 3), ("pred_observer", 3), ("observer_pole_choice", 1)],
                        [("lqr_integral", 2), ("stab_detect", 2), ("pred_observer", 2)]]),
}


def _pick_theory(rng):
    chosen, tot = [], 0.0
    pool = EXAM_CARDS[:]
    rng.shuffle(pool)
    others = [c for c in CARDS if c not in EXAM_CARDS]
    rng.shuffle(others)
    for c in pool + others:
        p = card_points(c)
        if tot + p <= 15.0 + 1e-9:
            chosen.append(c)
            tot += p
        if tot >= 15 - 1e-9:
            break
    return chosen, tot


def page_exam():
    st.title("📝 Exam simulation")
    ss = st.session_state
    ex = ss.get("exam")
    if not ex:
        st.markdown("""Mirrors the real format (Infosheet 2026, exams 2016/2017):
**Theory 15 P, 15 min, closed book** — then **Practical 35 P, 100 min, open book** (P1 7 · P2 7 · P3 6 · P4 15).
No feedback until you submit. Partial credit per sub-answer; theory is self-graded against the rubric afterwards.""")
        kind = st.radio("Mode", ["Full exam (115 min)", "Practical only (100 min)", "Theory only (15 min)"], horizontal=True)
        p4 = st.radio("Problem 4 variant", ["2017 style: pole placement + integrator + observer", "2016 style: LQR + integrator", "random"], horizontal=True)
        if st.button("Start exam", type="primary"):
            rng = random.Random()
            probs = {}
            if not kind.startswith("Theory"):
                for key, L in EXAM_LAYOUT.items():
                    opts = L["options"]
                    if key == "P4" and not p4.startswith("random"):
                        o = opts[0] if p4.startswith("2017") else opts[1]
                    else:
                        o = rng.choice(opts)
                    probs[key] = [make(g, d, rng.randint(1, 10 ** 6)) for g, d in o]
            cards, tpts = ([], 0.0) if kind.startswith("Practical") else _pick_theory(rng)
            phase = "practical" if kind.startswith("Practical") else "theory"
            ss["exam"] = dict(kind="full" if kind.startswith("Full") else ("practical" if kind.startswith("Practical") else "theory"),
                              probs=probs, cards=[c["id"] for c in cards], phase=phase, t0=time.time(),
                              deadline=time.time() + (15 * 60 if phase == "theory" else 100 * 60), answers={}, theory_answers={})
            st.rerun()
        hist = db.rows("SELECT ts, kind, theory, practical, total, max_total, duration FROM exams ORDER BY id DESC LIMIT 10")
        if hist:
            st.subheader("History")
            for h in hist:
                st.markdown(f"- {h['ts'][:16]} · {h['kind']} · **{h['total']:.1f}/{h['max_total']:.0f}** (theory {h['theory']:.1f}, practical {h['practical']:.1f}) · {h['duration'] / 60:.0f} min")
        return

    if ex["phase"] == "theory":
        countdown(ex["deadline"], "Theory part")
        st.subheader("Theory part (15 P) — closed book")
        for cid in ex["cards"]:
            c = BY_ID[cid]
            st.markdown(f"**({card_points(c):g} P)** {c['q']}")
            ex["theory_answers"][cid] = st.text_area("answer", key=f"ex_th_{cid}", height=110, label_visibility="collapsed")
        if st.button("Hand in theory part", type="primary"):
            ex["theory_time"] = time.time() - ex["t0"]
            if ex["kind"] == "theory":
                ex["phase"] = "grade_theory"
            else:
                ex["phase"] = "practical"
                ex["deadline"] = time.time() + 100 * 60
                ex["t_prac"] = time.time()
            st.rerun()
        return

    if ex["phase"] == "practical":
        countdown(ex["deadline"], "Practical part")
        st.subheader("Practical part (35 P) — open book, MATLAB allowed")
        for key, plist in ex["probs"].items():
            L = EXAM_LAYOUT[key]
            st.markdown(f"### {L['title']} ({L['pts']} P)")
            for prob in plist:
                with st.container(border=True):
                    st.markdown(prob.statement)
                    if prob.plot and prob.gen_id in ("zt_signal_exam",):
                        show_plot(prob)
                    for part in prob.parts:
                        st.markdown(part.label)
                        kk = f"ex_{prob.gen_id}_{prob.seed}_{part.key}"
                        if part.kind == "choice":
                            st.radio(part.label, part.options, index=None, key=kk, label_visibility="collapsed")
                        else:
                            st.text_input(part.label, key=kk, placeholder=part.placeholder, label_visibility="collapsed")
        if st.button("Hand in practical part", type="primary"):
            # capture answers now: widgets of this phase are not rendered (and their state is dropped) afterwards
            for plist in ex["probs"].values():
                for prob in plist:
                    for part in prob.parts:
                        kk = f"ex_{prob.gen_id}_{prob.seed}_{part.key}"
                        ex["answers"][kk] = ss.get(kk)
            ex["prac_time"] = time.time() - ex.get("t_prac", ex["t0"])
            ex["phase"] = "grade_theory" if ex["cards"] else "results"
            st.rerun()
        return

    if ex["phase"] == "grade_theory":
        st.subheader("Self-grade your theory answers against the rubric")
        st.caption("Be strict — the real graders deducted for missing definitions ('Def!'), missing reasons ('why?') and missing examples.")
        for cid in ex["cards"]:
            c = BY_ID[cid]
            with st.container(border=True):
                st.markdown(f"**{c['q']}** ({card_points(c):g} P)")
                st.markdown(f"*Your answer:* {ex['theory_answers'].get(cid) or '—'}")
                st.markdown(c["a"])
                for i, (crit, p) in enumerate(c["rubric"]):
                    st.checkbox(f"{crit} ({p:g} P)", key=f"exg_{cid}_{i}")
        if st.button("Compute results", type="primary"):
            ex["rubric"] = {f"exg_{cid}_{i}": bool(ss.get(f"exg_{cid}_{i}"))
                            for cid in ex["cards"] for i in range(len(BY_ID[cid]["rubric"]))}
            ex["phase"] = "results"
            st.rerun()
        return

    # ---- results
    if not ex.get("computed"):
        theory = 0.0
        tdetails = {}
        for cid in ex["cards"]:
            c = BY_ID[cid]
            got = sum(p for i, (_, p) in enumerate(c["rubric"]) if ex.get("rubric", {}).get(f"exg_{cid}_{i}"))
            theory += got
            tdetails[cid] = got
            engine.review_card(cid, got / card_points(c))
        prac = 0.0
        pdetails = {}
        topic_loss = {}
        for key, plist in ex["probs"].items():
            L = EXAM_LAYOUT[key]
            raw_max = sum(p.max_points for p in plist)
            scale = L["pts"] / raw_max
            got = 0.0
            items = []
            for prob in plist:
                res, raws = {}, {}
                for part in prob.parts:
                    kk = f"ex_{prob.gen_id}_{prob.seed}_{part.key}"
                    raws[part.key] = ex["answers"].get(kk)
                    res[part.key] = grade_part(part, raws[part.key])
                sc = sum(p.points for p in prob.parts if res[p.key]["correct"])
                got += sc * scale
                lost = (prob.max_points - sc) * scale
                topic_loss[prob.topic] = topic_loss.get(prob.topic, 0) + lost
                db.log_attempt(prob.gen_id, prob.topic, prob.difficulty, prob.seed, sc, prob.max_points, res, 0, 0, "exam")
                engine.update_mastery(prob.topic, sc / prob.max_points, prob.difficulty)
                for part in prob.parts:
                    r = res[part.key]
                    if not r["correct"]:
                        db.add_mistake(prob.gen_id, prob.topic, prob.difficulty, prob.seed, part.key, r.get("tag") or f"{prob.gen_id}:{part.key}",
                                       r.get("diagnosis") or "", raws[part.key], fmt_answer(part))
                items.append(dict(gen=prob.gen_id, title=prob.title, score=sc * scale, max=prob.max_points * scale,
                                  parts=[(part.label, part.points * scale, res[part.key]["correct"], raws[part.key], fmt_answer(part), res[part.key].get("diagnosis", ""))
                                         for part in prob.parts]))
            prac += got
            pdetails[key] = dict(score=got, max=L["pts"], items=items)
        max_total = (15 if ex["cards"] else 0) + (35 if ex["probs"] else 0)
        total = theory + prac
        dur = time.time() - ex["t0"]
        db.log_exam(ex["kind"], theory, prac, total, max_total, dur, dict(theory=tdetails, practical={k: v["score"] for k, v in pdetails.items()}))
        db.add_xp(int(10 * total), f"exam:{ex['kind']}")
        ex.update(computed=True, theory=theory, prac=prac, total=total, max_total=max_total, pdetails=pdetails, topic_loss=topic_loss, dur=dur,
                  new=engine.check_achievements())
    st.subheader("Results")
    c = st.columns(4)
    c[0].metric("Total", f"{ex['total']:.1f} / {ex['max_total']}")
    c[1].metric("Theory", f"{ex['theory']:.1f} / {15 if ex['cards'] else 0}")
    c[2].metric("Practical", f"{ex['prac']:.1f} / {35 if ex['probs'] else 0}")
    if ex["max_total"] == 50:
        c[3].metric("Grade", engine.grade_from_points(ex["total"]))
    st.caption(f"Time used: {ex['dur'] / 60:.1f} min" + (f" (theory {ex.get('theory_time', 0) / 60:.1f} min)" if ex["cards"] else ""))
    for aid in ex.get("new", []):
        st.toast(f"Achievement: {engine.ACHIEVEMENTS[aid][0]}", icon="🏆")
    if ex["topic_loss"]:
        st.markdown("**Where you lost points (practical):**")
        for t, l in sorted(ex["topic_loss"].items(), key=lambda kv: -kv[1]):
            if l > 0.05:
                st.markdown(f"- {TOPICS[t]['name']}: −{l:.1f} P")
    for key, d in ex["pdetails"].items():
        with st.expander(f"{EXAM_LAYOUT[key]['title']}: {d['score']:.1f}/{d['max']} P"):
            for it in d["items"]:
                st.markdown(f"**{it['title']}** — {it['score']:.1f}/{it['max']:.1f} P")
                for lab, pts, ok, raw, corr, diag in it["parts"]:
                    st.markdown(f"{'✅' if ok else '❌'} ({pts:.2g} P) {lab} — your `{raw}` · correct `{corr}`" + (f"  \n_{diag}_" if (diag and not ok) else ""))
    if st.button("Close exam"):
        ss.pop("exam")
        st.rerun()


# ======================================================================== stats
def page_stats():
    st.title("Stats & achievements")
    ach = db.achievements()
    cols = st.columns(4)
    for i, (aid, (name, desc)) in enumerate(engine.ACHIEVEMENTS.items()):
        with cols[i % 4].container(border=True):
            st.markdown(f"{'**' + name + '**' if aid in ach else '🔒 ' + name}  \n<small>{desc}</small>", unsafe_allow_html=True)
    st.subheader("XP per day")
    xp = db.xp_by_day()
    if xp:
        st.bar_chart({"XP": xp})
    st.subheader("Topic accuracy (last 30 attempts each)")
    rows = []
    for t in ORDER:
        a = db.attempts(limit=30, topic=t)
        if a:
            rows.append(dict(topic=TOPICS[t]["name"], attempts=len(a), accuracy=f"{np.mean([x['score'] / x['max_score'] for x in a if x['max_score']]) * 100:.0f} %",
                             mastery=f"{db.mastery_get(t)['value'] * 100:.0f} %", avg_time=f"{np.mean([x['duration'] or 0 for x in a]) / 60:.1f} min"))
    if rows:
        st.dataframe(rows, hide_index=True)
    st.subheader("Recent attempts")
    st.dataframe([dict(time=a["ts"][5:16], type=a["gen_id"], diff=a["difficulty"], score=f"{a['score']:g}/{a['max_score']:g}", mode=a["mode"])
                  for a in db.attempts(limit=25)], hide_index=True)


# ======================================================================== sources & formula notes
OCR_FLAGS = [
    ("Book Ex. 2.2", "Last expression `z/(z − e^{−aT}z^{−1})` — correct: z/(z − e^{−aT})."),
    ("Book Ex. 2.12", "`g(kT) = (0.5)^T` — correct: (0.5)^k."),
    ("Book Ex. 3.1", "Second numerator term printed with z⁻¹; correct (as in Ex. 3.3): (1 − e^{−T} − Te^{−T})z⁻²."),
    ("Book Ex. 3.9", "Polynomial OCR'd as `2z¹ − 3z³ …`; correct: 2z⁴ − 3z³ + 2z² − z + 1 (cf. Ex. 3.11)."),
    ("Book Ex. 3.11", "OCR shows P(w) = 2w⁴ + w³ + 2w² − w; recomputed: 9w⁴ + 8w³ + 14w² + 0·w + 1 (w¹ coefficient 0 ⇒ Hurwitz necessary condition violated — same conclusion). Verified by mapping the roots back to z."),
    ("Book eq. (3.50)", "Position algorithm: last term should be e([k−2]T), as on the formula sheet."),
    ("Book Jury determinants", "s₂ determinant garbled in OCR; formula sheet: s₂ = |r₀ r₁; r₃ r₂|."),
    ("Book Ex. 4.8 b", "G_D denominator OCR `1 − 0.8848z⁻¹ − 0.1152z⁻⁵`; correct: 1 − 0.8848z⁻⁴ − 0.1152z⁻⁵ (D(1) − B C z⁻³)."),
    ("Book Ex. 5.3", "`x₂(k+1) = −3x₂(k) + u(k−1)` — correct: + u(k)."),
    ("Formelsammlung p. 7", "Trapezoid PID: z²-coefficient should be K_p(1 + T_V/T + T/(2T_N)) and constant K_pT_V/T (book eq. 3.48); the Euler version is correct."),
    ("Formelsammlung p. 8", "ω_n = ω_d/√(1ζ²) — missing minus: √(1 − ζ²)."),
    ("Formelsammlung p. 19", "Q_O second row printed as cᵀGh — correct: cᵀG. Also 'G_PU(s)' should read G_PU(z)."),
    ("Formelsammlung p. 17", "'n_Q = n − 1 (Integrating controller)' — the book says n − 1 applies when the PLANT integrates (proportional controller suffices)."),
    ("Formelsammlung p. 24", "Finite-horizon LQR law printed without minus: u = −R_s⁻¹HᵀSGx (book 7.17). 'Chapter 6: Optimal Control' is Chapter 7 in the book."),
    ("Exercise book 2.5", "Difference equation garbled ('… + 2y(k)'); the result y = (1 − a^{k+1})/(1 − a) corresponds to y(k) − a·y(k−1) = σ(k)."),
    ("Exercise book 2.8 (2)", "'x(k) − σ(k) − (0.5)^k' — correct: x(k) = σ(k) − (0.5)^k."),
    ("Exercise book 3.3", "System 2 coefficient appears as 0.7258 and 0.7528 — inconsistent OCR; recompute with MATLAB if used."),
    ("Exercise book 4.2 b", "'7.2855 (z − 0.8187)/(z − 0.6376) − 7.2855 …' — the '−' should be '='."),
    ("Exercise book 4.5 d", "G_W denominator typo 0.8187z⁴ → 0.8187z³ (see P(z) in the same result)."),
    ("Exercise book 4.14", "G_W shown with z⁻⁵; with G̃⁻ = z⁻³ the closed loop is 0.5z⁻³/(1 − 0.5z⁻¹) — likely OCR error, verify."),
    ("Exercise book 6.8", "G_W printed as 0.5z⁻¹ + 0.5z⁻³; simulation of the given controller gives y = 0, 0.5, 1, 1 … ⇒ G_W = 0.5z⁻¹ + 0.5z⁻²."),
    ("Exercise book 7.3", "Both designs labelled 'Case 1' in the OCR; the second is Case 2 (Q₁₁ = 1000)."),
    ("Problem statements in general", "Many exercise-book problem statements are partially garbled by OCR (figures lost). The trainer only uses numbers that were re-derived and checked numerically."),
]


def page_sources():
    st.title("Formula essentials & source notes")
    t1, t2, t3 = st.tabs(["Formula essentials", "OCR / typo flags", "Material map"])
    with t1:
        for t in ORDER:
            with st.expander(TOPICS[t]["name"]):
                st.markdown(module(t)["math"])
    with t2:
        st.caption("Detected while cross-checking the OCR output, the formula sheet and the exercise results against recomputation. Never trust a single printed number — recompute.")
        for where, what in OCR_FLAGS:
            st.markdown(f"- **{where}:** {what}")
    with t3:
        st.markdown("""| File | Used for |
|---|---|
| `out/libri/auto/libri.md` (lecture notes, OCR) | concepts, notation, worked examples (Ch. 1–8; Appendix A orbital mechanics is outside the exam scope) |
| `out/exercises/auto/exercises.md` (exercise book, OCR) | problem patterns + reference results 2.1–7.5 |
| `LVA328011_VO_Digital-Control_Formelsammlung.pdf` | notation & formulas (allowed in the open-book part) |
| `test/2016-…`, `test/2017-…Prüfung` | exam structure, point weights, grader comments → rubrics |
| `VO_328011_Infosheet_VOUE_2026S.pdf` | exam format 15 + 35 P, grading scale |
| `exercises/`, `assignment4–8/` | homework topics: Jury/Tustin (4), root locus (5), MFC (6), pole placement/observer (7), LQR/min-order observer (8) |
| `lecture_material/` | MATLAB demos (aliasing, deadbeat, LQR modal weighting) |""")


# ======================================================================== settings
def page_settings():
    st.title("Settings")
    ex = db.get_setting("exam_date") or (date.today() + timedelta(days=5)).isoformat()
    d = st.date_input("Exam date", value=date.fromisoformat(ex))
    start = db.get_setting("plan_start") or date.today().isoformat()
    s = st.date_input("Plan start (Day 1)", value=date.fromisoformat(start))
    goal = st.number_input("Daily XP goal", 50, 3000, engine.daily_goal(), step=50)
    tr = st.radio("Study track", ["beginner", "standard"], index=0 if engine.track() == "beginner" else 1, horizontal=True,
                  format_func=lambda x: "Beginner — pass first (from zero)" if x == "beginner" else "Standard (relearning)")
    cram = st.toggle("Cram mode: unlock all topics", value=bool(db.get_setting("cram_mode", False)),
                     help="Ignore prerequisite locks (useful if you already know the basics).")
    if st.button("Save", type="primary"):
        db.set_setting("exam_date", d.isoformat())
        db.set_setting("plan_start", s.isoformat())
        db.set_setting("daily_goal", int(goal))
        db.set_setting("cram_mode", bool(cram))
        db.set_setting("track", tr)
        st.success("Saved.")
    st.divider()
    st.caption(f"Progress database: `{db.db_path()}`")
    if st.checkbox("I really want to delete all progress"):
        if st.button("Reset all progress", type="secondary"):
            db.reset_all()
            st.session_state.clear()
            st.success("Progress reset.")
