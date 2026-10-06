"""Learning engine: mastery model, adaptive difficulty, spaced repetition, XP/levels, streaks,
achievements, exam-readiness and next-best-action recommendations."""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from . import db
from .curriculum import DAY_PLAN, DAY_PLAN_BEGINNER, EXAM_TOPICS, ORDER, TOPICS, prereqs_met
from .theory import CARDS, card_points

# ---------------------------------------------------------------- mastery
DIFF_CAP = {1: 0.7, 2: 0.9, 3: 1.0}  # max mastery reachable by succeeding at a difficulty


def update_mastery(topic: str, frac: float, difficulty: int) -> dict:
    m = db.mastery_get(topic)
    w = 0.3 + 0.1 * (difficulty - 1)
    target = frac * DIFF_CAP.get(difficulty, 1.0)
    if frac >= 0.999 and m["value"] > target:
        target = m["value"]  # a correct easy item never lowers mastery
    m["value"] = max(0.0, min(1.0, m["value"] + w * (target - m["value"])))
    m["attempts"] = (m["attempts"] or 0) + 1
    m["last_ts"] = db.iso(db.now())
    if frac >= 0.999:
        m["best_diff"] = max(m.get("best_diff") or 0, difficulty)
    # topic spaced repetition (compressed for a 5-day horizon)
    iv = m.get("interval") or 0.5
    if frac >= 0.8:
        iv = min(4.0, iv * 2.0) if m["attempts"] > 1 else 0.5
        m["next_review"] = db.plus_days(iv)
    elif frac >= 0.5:
        m["next_review"] = db.plus_days(max(0.25, iv * 0.5))
    else:
        iv = 0.25
        m["next_review"] = db.plus_days(10 / 1440)  # 10 minutes
    m["interval"] = iv
    db.mastery_put(m)
    return m


def mark_learned(topic: str):
    m = db.mastery_get(topic)
    m["learned"] = 1
    if not m.get("next_review"):
        m["next_review"] = db.plus_days(0.5)
    db.mastery_put(m)


def adaptive_difficulty(topic: str) -> int:
    v = db.mastery_get(topic)["value"]
    return 1 if v < 0.35 else (2 if v < 0.7 else 3)


def is_unlocked(topic: str, mastery: dict | None = None) -> bool:
    if db.get_setting("cram_mode", False):
        return True
    mastery = mastery if mastery is not None else db.mastery_all()
    if mastery.get(topic, {}).get("manual_unlock"):
        return True
    vals = {t: mastery.get(t, {}).get("value", 0.0) for t in TOPICS}
    return prereqs_met(topic, vals, threshold=0.5)


def manual_unlock(topic: str):
    m = db.mastery_get(topic)
    m["manual_unlock"] = 1
    db.mastery_put(m)


# ---------------------------------------------------------------- theory cards (SM-2 style)
def review_card(card_id: str, frac: float):
    """frac = rubric score fraction (0..1)."""
    cd = db.card_get(card_id)
    cd["reps"] += 1
    cd["last_score"] = frac
    if frac < 0.5:
        cd["lapses"] += 1
        cd["ease"] = max(1.3, cd["ease"] - 0.2)
        cd["interval"] = 0.0
        cd["due"] = db.plus_days(10 / 1440)
    else:
        q = 3 + 2 * (frac - 0.5) / 0.5 if frac < 1 else 5  # 3..5
        cd["ease"] = max(1.3, cd["ease"] + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
        if cd["interval"] < 0.5:
            cd["interval"] = 0.5 if frac < 0.85 else 1.0
        else:
            cd["interval"] = min(5.0, cd["interval"] * cd["ease"] * (0.8 if frac < 0.85 else 1.0))
        cd["due"] = db.plus_days(cd["interval"])
    db.card_put(cd)
    return cd


def due_cards(limit=None):
    states = db.cards_all()
    nowt = db.now()
    due, new = [], []
    for c in CARDS:
        st = states.get(c["id"])
        if st is None:
            new.append(c)
        elif st["due"] and db.parse(st["due"]) <= nowt:
            due.append(c)
    # exam cards first among new ones
    new.sort(key=lambda c: (0 if c["exam"] else 1))
    out = due + new
    return out[:limit] if limit else out


def theory_mastery_by_topic() -> dict:
    states = db.cards_all()
    res = {}
    for t in TOPICS:
        cs = [c for c in CARDS if c["topic"] == t]
        if not cs:
            continue
        tot = sum(card_points(c) for c in cs)
        got = sum(card_points(c) * (states.get(c["id"], {}).get("last_score", 0.0) or 0.0) for c in cs)
        res[t] = got / tot if tot else 0.0
    return res


# ---------------------------------------------------------------- XP, levels, streaks
LEVEL_TITLES = ["Sampler", "Z-Transformer", "Pulse Pusher", "Hold Keeper", "Jury Member", "Pole Placer",
                "Observer", "Riccati Rider", "Dead-Beat Master", "Exam Slayer"]


def level_info(xp: int):
    lvl = int(math.floor(math.sqrt(max(xp, 0) / 60.0))) + 1
    lo = 60 * (lvl - 1) ** 2
    hi = 60 * lvl ** 2
    title = LEVEL_TITLES[min(lvl - 1, len(LEVEL_TITLES) - 1)]
    return lvl, title, (xp - lo) / (hi - lo), hi - xp


def xp_for_problem(score, max_score, difficulty, hints, first_try=True):
    if max_score <= 0:
        return 0
    base = 12 * score * (1.0 + 0.5 * (difficulty - 1))
    if hints:
        base *= max(0.4, 1 - 0.2 * hints)
    if first_try and score >= max_score - 1e-9:
        base += 5 * difficulty
    return int(round(base))


def daily_goal() -> int:
    return int(db.get_setting("daily_goal", 300))


def today_xp() -> int:
    return int(db.xp_by_day().get(db.today(), 0))


def streak() -> int:
    by_day = db.xp_by_day()
    goal = daily_goal()
    d = date.today()
    s = 0
    if by_day.get(d.isoformat(), 0) < goal:
        d = d - timedelta(days=1)  # today not finished yet doesn't break the streak
    while by_day.get(d.isoformat(), 0) >= goal:
        s += 1
        d -= timedelta(days=1)
    return s


def study_days() -> int:
    return len([d for d, v in db.xp_by_day().items() if v > 0])


# ---------------------------------------------------------------- achievements
ACHIEVEMENTS = {
    "first_blood": ("🩸 First Blood", "Solve your first problem completely."),
    "streak10": ("🔥 On Fire", "10 fully correct problems in a row."),
    "jury_judge": ("⚖️ Jury Judge", "Solve 5 Jury problems without error."),
    "zoh_hero": ("🪜 Staircase Hero", "Solve 5 ZOH pulse-transfer-function problems."),
    "observer": ("🔭 All-Seeing", "Solve predictive, current and minimum-order observer problems."),
    "theory30": ("🧠 Theory Grinder", "Review 30 theory cards."),
    "theory_all": ("📜 Closed-Book Ready", "Every theory card reviewed at least once with ≥ 75 %."),
    "boss1": ("🐉 Dragon Slayer", "Defeat your first boss."),
    "boss_all": ("👑 Boss Rush", "Defeat every boss."),
    "mock_pass": ("✅ Passed (mock)", "Score ≥ 25/50 in a mock exam."),
    "mock_good": ("🏅 Gut", "Score ≥ 37.5/50 in a mock exam."),
    "mock_very": ("🏆 Sehr gut", "Score ≥ 43.75/50 in a mock exam."),
    "fixer10": ("🛠️ Mistake Fixer", "Resolve 10 notebook mistakes."),
    "speed": ("⚡ Speed Demon", "Score ≥ 12 points in a 10-minute Speed Run."),
    "goal3": ("📅 Consistency", "Meet the daily goal 3 days in a row."),
    "all_learned": ("🎓 Full Syllabus", "Complete all learning modules."),
    "ready80": ("🚀 Exam Ready", "Exam-ready score ≥ 80 %."),
}


def check_achievements() -> list:
    """Returns list of newly unlocked achievement ids."""
    new = []

    def award(aid, cond):
        if cond and db.unlock_achievement(aid):
            new.append(aid)

    att = db.attempts(limit=200)
    full = [a for a in att if a["total_parts"] and a["correct_parts"] == a["total_parts"]]
    award("first_blood", len(full) >= 1)
    run = 0
    for a in att:
        if a["total_parts"] and a["correct_parts"] == a["total_parts"]:
            run += 1
        else:
            break
    award("streak10", run >= 10)
    award("jury_judge", sum(1 for a in full if a["gen_id"] in ("jury_cubic", "jury_quartic", "jury_gain_range")) >= 5)
    award("zoh_hero", sum(1 for a in full if a["gen_id"] == "zoh_plant") >= 5)
    award("observer", all(any(a["gen_id"] == g for a in full) for g in ("pred_observer", "curr_observer", "minorder_observer")))
    cards = db.cards_all()
    award("theory30", sum(c["reps"] for c in cards.values()) >= 30)
    award("theory_all", all(cards.get(c["id"], {}).get("last_score", 0) >= 0.75 for c in CARDS))
    wins = {r["boss_id"] for r in db.rows("SELECT boss_id FROM bosses WHERE won=1")}
    award("boss1", len(wins) >= 1)
    award("boss_all", set(BOSSES).issubset(wins))
    best = db.scalar("SELECT MAX(total) FROM exams WHERE kind='full'") or 0
    award("mock_pass", best >= 25)
    award("mock_good", best >= 37.5)
    award("mock_very", best >= 43.75)
    award("fixer10", db.count("mistakes", "resolved=1") >= 10)
    award("speed", (db.get_setting("speed_best", 0) or 0) >= 12)
    award("goal3", streak() >= 3)
    award("all_learned", all(db.mastery_get(t).get("learned") for t in EXAM_TOPICS))
    award("ready80", exam_ready()["score"] >= 80)
    for aid in new:
        db.add_xp(50, f"achievement:{aid}")
    return new


# ---------------------------------------------------------------- exam readiness
def grade_from_points(p: float) -> str:
    if p >= 43.75:
        return "1 (Sehr gut)"
    if p >= 37.5:
        return "2 (Gut)"
    if p >= 31.25:
        return "3 (Befriedigend)"
    if p >= 25:
        return "4 (Genügend)"
    return "5 (Nicht genügend)"


def exam_ready() -> dict:
    mast = db.mastery_all()
    th = theory_mastery_by_topic()
    tot_w = sum(t["exam_pts"] for t in TOPICS.values())
    per = {}
    acc = 0.0
    for tid, t in TOPICS.items():
        p = mast.get(tid, {}).get("value", 0.0)
        tm = th.get(tid)
        r = p if tm is None else (0.65 * p + 0.35 * tm)
        if tid == "sampling":
            r = 0.3 * p + 0.7 * (tm or 0.0)
        per[tid] = r
        acc += t["exam_pts"] * r
    mastery_score = 100 * acc / tot_w
    ex = db.rows("SELECT total, max_total FROM exams WHERE kind='full' ORDER BY id DESC LIMIT 2")
    if ex:
        mock = 100 * sum(e["total"] for e in ex) / sum(e["max_total"] for e in ex)
        score = 0.6 * mastery_score + 0.4 * mock
    else:
        mock = None
        score = 0.85 * mastery_score  # no mock exam yet: readiness unproven
    expected_pts = 50 * score / 100
    return dict(score=score, mastery=mastery_score, mock=mock, per_topic=per, expected_pts=expected_pts,
                grade=grade_from_points(expected_pts))


# ---------------------------------------------------------------- plan & recommendations
def track() -> str:
    return db.get_setting("track", "beginner")


def get_plan() -> dict:
    return DAY_PLAN_BEGINNER if track() == "beginner" else DAY_PLAN
def plan_day() -> int:
    start = db.get_setting("plan_start")
    if not start:
        start = db.today()
        db.set_setting("plan_start", start)
    d = (date.today() - date.fromisoformat(start)).days + 1
    return max(1, min(5, d))


def days_to_exam():
    ex = db.get_setting("exam_date")
    if not ex:
        return None
    return (date.fromisoformat(ex) - date.today()).days


def due_topics() -> list:
    mast = db.mastery_all()
    nowt = db.now()
    out = []
    for t in ORDER:
        m = mast.get(t)
        if m and m.get("next_review") and db.parse(m["next_review"]) <= nowt and (m.get("attempts") or 0) > 0:
            out.append(t)
    return out


def weakest_topics(n=3) -> list:
    er = exam_ready()["per_topic"]
    mast = db.mastery_all()
    cand = [t for t in EXAM_TOPICS if is_unlocked(t, mast)]
    cand.sort(key=lambda t: (er.get(t, 0) - 0.02 * TOPICS[t]["exam_pts"]))
    return cand[:n]


def recommendation() -> dict:
    """Next best action."""
    om = db.open_mistakes()
    due_m = [m for m in om if db.parse(m["due"]) <= db.now()]
    if len(due_m) >= 3:
        return dict(kind="mistakes", label=f"Fix {len(due_m)} mistakes in your notebook", page="mistakes")
    day = plan_day()
    plan = get_plan()
    for t in plan[day]["topics"]:
        if not db.mastery_get(t).get("learned"):
            return dict(kind="learn", topic=t, label=f"Learn: {TOPICS[t]['name']} (Day {day} plan)", page="learn")
    dt = due_topics()
    if dt:
        return dict(kind="practice", topic=dt[0], label=f"Spaced review: {TOPICS[dt[0]]['name']}", page="practice")
    dc = due_cards()
    if dc and len([c for c in dc if db.card_get(c["id"])["reps"] > 0]) >= 5:
        return dict(kind="review", label="Theory cards are due", page="review")
    boss = plan[day].get("boss")
    if boss and not db.scalar("SELECT 1 FROM bosses WHERE boss_id=? AND won=1", (boss,)):
        return dict(kind="boss", boss=boss, label=f"Boss of the day: {BOSSES[boss]['name']}", page="boss")
    w = weakest_topics(1)
    if w:
        return dict(kind="practice", topic=w[0], label=f"Strengthen weakest topic: {TOPICS[w[0]]['name']}", page="practice")
    return dict(kind="exam", label="Take a full mock exam", page="exam")


# ---------------------------------------------------------------- bosses
BOSSES = {
    "sampler": dict(name="The Sampler", icon="🎚️", exam="Exam P1 (7 P)", minutes=20,
                    stages=[("zt_signal_exam", 2), ("zt_inverse_comp", 2)],
                    lore="It turns every signal into a sequence of numbers. Beat it with U(z), the FVT and a clean recursion."),
    "zoh_hydra": dict(name="ZOH Hydra", icon="🪜", exam="Exam P2 (7 P)", minutes=25,
                      stages=[("zoh_plant", 2), ("closed_loop_P", 2), ("sampler_config", 2)],
                      lore="Cut off one head (1 − z⁻¹) and two grow back unless you remember the hold."),
    "jury_judge": dict(name="The Jury", icon="⚖️", exam="Exam P3 (6 P)", minutes=20,
                       stages=[("jury_cubic", 2), ("stability_factored", 1), ("jury_gain_range", 2)],
                       lore="Twelve angry coefficients. Every condition must be argued."),
    "design_gauntlet": dict(name="Design Gauntlet", icon="🛡️", exam="Ch. 4 / Homework 4–6", minutes=30,
                            stages=[("discretize_lead", 2), ("rl_pi_design", 2), ("deadbeat_stable", 2)],
                            lore="Three gates: discretise, place the zero, finish in finite time."),
    "ss_titan": dict(name="State-Space Titan", icon="🗿", exam="Exam 2017 P4 (15 P)", minutes=35,
                     stages=[("ctrb_obsv", 3), ("integral_sf", 3), ("pred_observer", 3), ("observer_pole_choice", 1)],
                     lore="The 15-point monster that scored 0/15 in the real 2017 exam. Not this time."),
    "lqr_overlord": dict(name="LQR Overlord", icon="👁️", exam="Exam 2016 P4 (16 P)", minutes=35,
                         stages=[("lqr_integral", 2), ("stab_detect", 2), ("lqr_scalar", 2), ("pred_observer", 2)],
                         lore="It minimises your score subject to your dynamics. Augment, detect, stabilise."),
}

SPEED_POOL = ["zt_table_quiz", "stability_factored", "mapping_sz", "sampler_config", "fvt_ivt", "observer_pole_choice",
              "stab_detect", "rel_degree", "sampling_alias", "mfc_degrees", "static_error", "pid_discrete", "sampling_time_rule"]
