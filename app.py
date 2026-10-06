"""Digital Control (TU Wien 328.011) — gamified 5-day exam trainer.

Run:  .venv/bin/streamlit run app.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st  # noqa: E402

from dctrainer import auth, calculator, db, views  # noqa: E402

st.set_page_config(page_title="Digital Control Trainer", page_icon="🎛️", layout="wide")
if not auth.require_login():
    st.stop()
db.init()
if db.get_setting("plan_start") is None:
    from datetime import date, timedelta
    db.set_setting("plan_start", date.today().isoformat())
    db.set_setting("exam_date", (date.today() + timedelta(days=5)).isoformat())

pages = {
    "dashboard": st.Page(views.page_dashboard, title="Dashboard", icon="🏠", url_path="dashboard", default=True),
    "plan": st.Page(views.page_plan, title="5-Day Plan", icon="🗓️", url_path="plan"),
    "map": st.Page(views.page_map, title="Mastery Map", icon="🗺️", url_path="map"),
    "learn": st.Page(views.page_learn, title="Learn", icon="📚", url_path="learn"),
    "practice": st.Page(views.page_practice, title="Practice", icon="🎯", url_path="practice"),
    "review": st.Page(views.page_review, title="Review (SRS)", icon="🔁", url_path="review"),
    "mistakes": st.Page(views.page_mistakes, title="Mistake Notebook", icon="📓", url_path="mistakes"),
    "speed": st.Page(views.page_speed, title="Speed Run", icon="⚡", url_path="speed"),
    "boss": st.Page(views.page_boss, title="Boss Battles", icon="🐉", url_path="boss"),
    "exam": st.Page(views.page_exam, title="Exam Simulation", icon="📝", url_path="exam"),
    "stats": st.Page(views.page_stats, title="Stats & Achievements", icon="📊", url_path="stats"),
    "sources": st.Page(views.page_sources, title="Formulas & Sources", icon="📄", url_path="sources"),
    "settings": st.Page(views.page_settings, title="Settings", icon="⚙️", url_path="settings"),
}
views.PAGES.update(pages)
st.session_state["_pages"] = pages

nav = st.navigation({
    "Study": [pages["dashboard"], pages["plan"], pages["map"], pages["learn"], pages["practice"], pages["review"], pages["mistakes"]],
    "Challenge": [pages["speed"], pages["boss"], pages["exam"]],
    "More": [pages["stats"], pages["sources"], pages["settings"]],
})
views.sidebar()
with st.sidebar:
    auth.sidebar_controls()
    calculator.mount()
nav.run()
