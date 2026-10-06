# Digital Control Exam Trainer (TU Wien 328.011)

A local, gamified 5-day exam trainer built from your OCR'd lecture notes (`out/libri`), the exercise book (`out/exercises`), the Formelsammlung, your homework, and the 2016/2017 exams.

## Launch (Ubuntu)

```bash
cd ~/Desktop/tuwien/Digital_Control/dc_trainer
./run.sh                      # opens http://localhost:8501
```

`run.sh` runs the commands below. Use them directly if you prefer, e.g. on a fresh machine:

```bash
cd ~/Desktop/tuwien/Digital_Control/dc_trainer
uv venv --python /usr/bin/python3.12 .venv            # once
uv pip install --python .venv/bin/python -r requirements.txt   # once
.venv/bin/streamlit run app.py
```

Without `uv`, use `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt` instead.

Your progress is stored in `data/progress.db` (SQLite). Back it up by copying the file, and reset it under Settings.
Run the tests with `.venv/bin/python -m pytest -q`.

## Beginner track (default)
For starting from zero: Settings → *Study track* = **Beginner — pass first**. It adds
6 foundation modules (complex numbers, poles, partial fractions, Laplace, feedback, matrices), a plain-language primer in every module,
a 📋 step-by-step recipe next to every problem type, 20 ⭐ must-memorise theory answers (Review → Must memorise),
and a 5-day plan aimed at ≥ 25/50 (Jury → z-transform → theory → ZOH → state-space recipes in MATLAB).

## 🧮 Built-in calculator
A 🧮 tab sits on the right edge of every page. It opens a panel with four tabs:
**Calc** (complex numbers with `j`, DEG/RAD, `atan2`, `Ans`, variables, history, and **↳ Insert** into the last answer box you clicked),
**Roots** (polynomial roots + stability verdict), **Matrix** (det, inverse, eigenvalues, M·v, vᵀ·M, Mⁿ) and **Jury** (full table check).
It runs offline: mathjs is served from `static/`.

## What's inside
- **48 parameterised problem generators** that mirror the exam patterns (P1 z-transform, P2 ZOH + closed loop, P3 Jury, P4 state-space/observer/LQR) plus the Ch. 4 design methods. Each one is auto-graded with tolerances, a full worked solution, a MATLAB recipe for the open-book part, and **misconception detectors** (e.g. a missing (1−z⁻¹), dropping (−1)ⁿ in Jury, the −cᵀ vs −cᵀG augmentation, predictive vs current observer).
- **58 theory cards** for the 15-point closed-book part. Past-exam questions are marked, and the graders' comments have been turned into rubrics.
- **Learning modules** per topic: Intuition → Visual → Math → Worked example → Guided → Independent → Feedback → Retrieval quiz.
- **Gamification**: XP, levels, streaks, daily goal, achievements, a mastery map with prerequisite locks (switch on *cram mode* in Settings to unlock everything), 6 boss battles, a 10-minute speed run, spaced repetition, a mistake notebook with remediation exercises, and an Exam-Ready score.
- **Exam simulation**: 15 min theory + 100 min practical, with timer, partial credit and grade.
- **Formulas & Sources** page: OCR errors and Formelsammlung typos found during verification.
