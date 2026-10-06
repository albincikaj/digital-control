"""Course map: topics, prerequisites, exam weights, generators, and the 5-day plan.

Exam weights are derived from the two past exams (2016-06-28, 2017-06-26) and the 2026 infosheet:
Theory 15 P (closed book, 15 min) + Practical 35 P (open book, 100 min):
  P1 z-transform 6–7 P · P2 ZOH + closed loop 7 P · P3 Jury 6 P · P4 state-space / observer / LQR 15–16 P.
`exam_pts` = expected points per exam attributable to the topic (practical + theory share).
"""
from __future__ import annotations

FOUNDATIONS = {
    "f_complex": dict(name="Foundations: complex numbers", chapter="—", day=1, prereq=[], exam_pts=0.0, gens=["f_complex"],
                      why="Poles are points in the complex plane; |z| < 1 decides stability; z = e^{sT}."),
    "f_poles": dict(name="Foundations: poles & stability", chapter="—", day=1, prereq=[], exam_pts=0.0, gens=["f_poles"],
                    why="Every stability question (P2c, P3, P4) is 'where are the poles?'."),
    "f_pfe": dict(name="Foundations: partial fractions", chapter="—", day=1, prereq=[], exam_pts=0.0, gens=["f_pfe"],
                  why="Step 1 of the ZOH problem (P2a) and of the inverse z-transform."),
    "f_laplace": dict(name="Foundations: Laplace & first-order systems", chapter="—", day=1, prereq=[], exam_pts=0.0, gens=["f_laplace"],
                      why="G(s), DC gain, time constant — the plants in P2 and P4 are given in s."),
    "f_feedback": dict(name="Foundations: feedback loops", chapter="—", day=2, prereq=[], exam_pts=0.0, gens=["f_feedback"],
                       why="G_W = KG/(1 + KG) is P2b; offset ⇒ why integral action (P4)."),
    "f_matrix": dict(name="Foundations: 2×2 matrices", chapter="—", day=3, prereq=[], exam_pts=0.0, gens=["f_matrix"],
                     why="State space (P4, 15 P) is written with matrices; eigenvalues = poles."),
}

TOPICS = {
    "zt_basics": dict(
        name="z-Transform & theorems", chapter="2.1–2.2", day=1, prereq=[], exam_pts=4.0,
        gens=["zt_signal_exam", "fvt_ivt", "zt_table_quiz"],
        why="Exam P1 every year (signal → U(z), Y = GU, final value). Definition asked in theory 2017."),
    "zt_inverse": dict(
        name="Inverse z-transform", chapter="2.3", day=1, prereq=["zt_basics"], exam_pts=3.5,
        gens=["zt_inverse_comp", "zt_pfe"],
        why="Exam 2016 P1 (6 P): computational method by hand. Uniqueness of x(kT) vs x(t) in theory 2016."),
    "diff_eq": dict(
        name="Difference equations, G(z), g(k), convolution", chapter="2.4–2.5", day=1, prereq=["zt_basics"], exam_pts=2.0,
        gens=["diffeq_weighting", "convolution"],
        why="Exam 2017 P1c (difference equation); Homework 2."),
    "sampling": dict(
        name="Sampling, Shannon, aliasing, ZOH", chapter="1, 3.1–3.4", day=2, prereq=[], exam_pts=2.5,
        gens=["sampling_alias"],
        why="Theory: Shannon (2016 & 2017), ZOH staircase plot with quantisation (2016)."),
    "zoh_plant": dict(
        name="ZOH + plant → G(z)", chapter="3.3, 3.5", day=2, prereq=["zt_basics"], exam_pts=3.5,
        gens=["zoh_plant"],
        why="Exam P2a (3 P) both years — 'determine G(z) with ZOH manually'."),
    "closed_loop": dict(
        name="Closed-loop pulse TFs, disturbance, PID", chapter="3.5", day=2, prereq=["zoh_plant", "diff_eq"], exam_pts=3.5,
        gens=["closed_loop_P", "sampler_config", "pid_discrete"],
        why="Exam P2b–d (4 P): G_W(z) with P-controller, stability, 'can you write G_d(z)?'."),
    "mapping": dict(
        name="s ↔ z mapping, relative stability", chapter="3.6", day=2, prereq=["zt_basics"], exam_pts=1.5,
        gens=["mapping_sz"],
        why="Theory 2016: sketch region of relative stability; needed for root-locus specs."),
    "stability": dict(
        name="Stability: Jury, w-transform", chapter="3.7", day=2, prereq=["mapping"], exam_pts=6.0,
        gens=["jury_cubic", "stability_factored", "jury_gain_range", "w_transform", "jury_quartic"],
        why="Exam P3 (6 P) both years: Jury table for a cubic + instant statement from factored form."),
    "discretization": dict(
        name="Discretising analog controllers, choice of T", chapter="4.1–4.2", day=3, prereq=["mapping"], exam_pts=1.0,
        gens=["discretize_lead", "sampling_time_rule"],
        why="Homework 4; sampling-time justification asked in Exam 2016 P4a."),
    "root_locus": dict(
        name="Root-locus design, static errors", chapter="4.3", day=3, prereq=["stability"], exam_pts=1.0,
        gens=["rl_pi_design", "static_error"],
        why="Homework 5; possible practical task (MATLAB rlocus/rltool)."),
    "analytic_design": dict(
        name="Dead-beat, MFC, IMC", chapter="4.4–4.6", day=3, prereq=["closed_loop"], exam_pts=2.0,
        gens=["deadbeat_stable", "imc_first_order", "mfc_degrees"],
        why="Theory 2017: 'basic idea of the model following controller' (2 P); Homework 6 (MFC)."),
    "ss_models": dict(
        name="State-space models & discretisation", chapter="5.1–5.4", day=3, prereq=["diff_eq"], exam_pts=2.0,
        gens=["ss_canonical", "ss_jordan", "ss_discretize", "ss_tf"],
        why="Exam 2016 P4a/b (ZOH discretisation, Jordan form)."),
    "ctrb_obsv": dict(
        name="Controllability & observability", chapter="5.5–5.6", day=4, prereq=["ss_models"], exam_pts=4.0,
        gens=["ctrb_obsv"],
        why="Exam P4 checks both years; theory: definition of observability (2017), controllability vs stabilisability (2016)."),
    "pole_placement": dict(
        name="Pole placement, K_w, integral action", chapter="6.1–6.3", day=4, prereq=["ctrb_obsv"], exam_pts=7.0,
        gens=["pole_placement", "integral_sf"],
        why="Exam 2017 P4a (5 P): state feedback with integration of the control error; block diagram in theory 2017 (3 P)."),
    "observers": dict(
        name="Observers: predictive, current, minimum-order", chapter="6.4", day=4, prereq=["pole_placement"], exam_pts=5.0,
        gens=["pred_observer", "curr_observer", "minorder_observer", "observer_pole_choice"],
        why="Exam P4b (4 P) / 2016 P4h; theory both years: current vs predictive observer, why use an observer."),
    "lqr": dict(
        name="Optimal control: LQR & Riccati", chapter="7", day=5, prereq=["pole_placement"], exam_pts=4.5,
        gens=["lqr_scalar", "lqr_matrix", "lqr_integral", "riccati_step", "stab_detect"],
        why="Exam 2016 P4 (LQR with integrator); theory both years: prerequisites for a stable LQR."),
    "fb_lin": dict(
        name="Feedback linearisation", chapter="8", day=5, prereq=["ss_models"], exam_pts=2.0,
        gens=["rel_degree"],
        why="Theory both years: idea of exact feedback linearisation (2016), relative degree (2017)."),
}

TOPICS = {**FOUNDATIONS, **TOPICS}
_EXTRA_PREREQ = {"zoh_plant": ["f_pfe", "f_laplace"], "closed_loop": ["f_feedback"], "mapping": ["f_complex"],
                 "stability": ["f_poles"], "ss_models": ["f_matrix"], "zt_inverse": ["f_pfe"]}
for _t, _ps in _EXTRA_PREREQ.items():
    TOPICS[_t]["prereq"] = list(TOPICS[_t]["prereq"]) + _ps

ORDER = list(TOPICS.keys())
EXAM_TOPICS = [t for t in ORDER if TOPICS[t]["exam_pts"] > 0]

DAY_PLAN = {
    1: dict(title="Day 1 — z-transform engine (Exam P1)",
            topics=["zt_basics", "zt_inverse", "diff_eq"],
            goals=["Learn modules: z-transform, inverse, difference equations",
                   "Boss: The Sampler (Exam 2017 P1)",
                   "20+ theory cards (Ch. 2)", "Mock: P1 only, 20 min"],
            boss="sampler"),
    2: dict(title="Day 2 — Sampling, ZOH, closed loop, Jury (Exam P2 + P3)",
            topics=["sampling", "zoh_plant", "closed_loop", "mapping", "stability"],
            goals=["Learn modules: sampling, ZOH, closed loop, mapping, stability",
                   "Bosses: ZOH Hydra (P2) and Jury Judge (P3)", "Theory cards Ch. 3", "Review mistakes of Day 1"],
            boss="zoh_hydra"),
    3: dict(title="Day 3 — Design (Ch. 4) + state-space basics",
            topics=["discretization", "root_locus", "analytic_design", "ss_models"],
            goals=["Learn: discretisation, root locus, dead-beat/MFC/IMC (idea level!)", "Learn: state-space models",
                   "Boss: Design Gauntlet", "Theory cards Ch. 4–5", "First FULL mock exam in the evening"],
            boss="design_gauntlet"),
    4: dict(title="Day 4 — State-space design (Exam P4, 15 P)",
            topics=["ctrb_obsv", "pole_placement", "observers"],
            goals=["Learn: controllability/observability, pole placement + integral action, observers",
                   "Boss: State-Space Titan (Exam 2017 P4)", "Theory cards Ch. 6", "Mistake notebook to zero"],
            boss="ss_titan"),
    5: dict(title="Day 5 — LQR, feedback linearisation, exam rehearsal",
            topics=["lqr", "fb_lin"],
            goals=["Learn: LQR & Riccati, feedback linearisation", "Boss: LQR Overlord (Exam 2016 P4)",
                   "ALL theory cards once more (closed-book part = 15 P!)", "Full mock exam under time pressure, then fix weak topics"],
            boss="lqr_overlord"),
}

# ------------------------------------------------------------------------------------------------
# Pass-first plan for a student starting from zero. Target: ≥ 25/50 by securing the mechanical points
# (Jury 6, z-transform 7, ZOH + closed loop 7) + memorised theory (~8 of 15) + recipe/MATLAB parts of P4 (~5).
DAY_PLAN_BEGINNER = {
    1: dict(title="Day 1 — Foundations + z-transform (target: P1 = 7 P)",
            topics=["f_complex", "f_poles", "f_pfe", "f_laplace", "zt_basics", "diff_eq"],
            goals=["Foundations: complex numbers, poles, partial fractions, Laplace (≈ 3 h, primer + 5 drills each)",
                   "z-transform module + recipe; 10 'Exam P1' problems until fully correct twice in a row",
                   "Must-memorise theory: 5 cards (z-transform definition, Shannon, uniqueness, stability definition, ZOH)",
                   "Boss: The Sampler"],
            boss="sampler"),
    2: dict(title="Day 2 — Jury, ZOH, closed loop (target: P3 = 6 P, P2 = 7 P)",
            topics=["zt_inverse", "stability", "f_feedback", "zoh_plant", "closed_loop"],
            goals=["Jury recipe drilled until you need < 8 minutes for a cubic (Boss: The Jury)",
                   "Inverse z-transform (computational method)",
                   "ZOH G(z) by recipe — check every result with c2d in MATLAB", "G_W, stability, 'no G_d(z)' answer",
                   "Must-memorise theory: 5 more cards"],
            boss="jury_judge"),
    3: dict(title="Day 3 — Sampling theory, mapping, matrices, state space intro + first mock",
            topics=["sampling", "mapping", "f_matrix", "ss_models", "ctrb_obsv"],
            goals=["Primers + cards for sampling/Shannon/ZOH (pure theory points)", "2×2 matrix drills; state-space primer",
                   "Controllability/observability recipe (det of Q_C, Q_O)", "Boss: ZOH Hydra",
                   "Evening: mock exam — Practical only, then review every lost point"],
            boss="zoh_hydra"),
    4: dict(title="Day 4 — State feedback, integrator, observer by recipe + MATLAB (target: 6–9 of P4's 15 P)",
            topics=["pole_placement", "observers"],
            goals=["2×2 pole placement by hand (coefficient comparison) — then always MATLAB acker",
                   "Integral-action recipe (Ĝ, ĥ, K = −last entry) and observer recipe (acker on transposes)",
                   "Write your own MATLAB cheat file from the recipes (allowed in the exam!)",
                   "Must-memorise: block diagram with integrator, predictive vs current observer, why observer",
                   "Boss: State-Space Titan"],
            boss="ss_titan"),
    5: dict(title="Day 5 — Theory sweep + LQR recipe + two full mocks",
            topics=["lqr", "fb_lin", "analytic_design", "discretization", "root_locus"],
            goals=["ALL must-memorise cards twice (closed-book 15 P is your biggest lever now)",
                   "LQR: prerequisites sentence + dlqr recipe; feedback linearisation & MFC idea (theory only)",
                   "Ch. 4 design topics: primer level only (names + one sentence each)",
                   "Full mock exam (115 min) ×2 with review in between; fix the mistake notebook"],
            boss="lqr_overlord"),
}

# Theory-part weight: the closed-book part is worth 15/50 points.
THEORY_WEIGHT = 15.0
PRACTICAL_WEIGHT = 35.0


def prereqs_met(topic: str, mastery: dict, threshold: float = 0.5) -> bool:
    return all(mastery.get(p, 0.0) >= threshold for p in TOPICS[topic]["prereq"])
