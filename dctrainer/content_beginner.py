"""Zero-background content: foundation modules + a plain-language primer for every exam topic."""
from __future__ import annotations

import numpy as np

from . import plots

FOUNDATION_MODULES = {
    "f_complex": dict(
        intuition="A complex number is just a **point in a plane** (an arrow from the origin). Horizontal = real part, vertical = imaginary part "
                  "(written with j, where j² = −1). Instead of (x, y) you can describe the same point by its **length** (magnitude) and its "
                  "**direction** (angle). Digital control lives on this plane: every pole is such a point, and the **unit circle** (all points with length 1) "
                  "is the border between stable and unstable.",
        visual=lambda: plots.zplane(extra=[([0.6 + 0.8j], "ro", "z = 0.6 + j0.8 (length 1, 53.1°)"), ([0.3 - 0.4j], "bs", "0.3 − j0.4 (length 0.5)")],
                                    title="Points in the complex plane"),
        visual_caption="Both points have the same direction structure; the red one sits ON the unit circle, the blue one inside.",
        math=r"""- $z = a + jb$, $|z| = \sqrt{a^2 + b^2}$, $\arg z = \operatorname{atan2}(b, a)$
- Polar form $z = r\,e^{j\theta} = r(\cos\theta + j\sin\theta)$ (**Euler's formula**)
- Multiplying: lengths multiply, angles add. $|e^{j\theta}| = 1$ always.
- $e^{(\sigma + j\omega)T} = e^{\sigma T}\cdot e^{j\omega T}$: real part → length, imaginary part → angle (radians). This is the s→z map of the course.""",
        worked="""**Example:** $z = -1 + j1$. Length $\\sqrt{1+1} = 1.414$. Angle: tan⁻¹(1/−1) = −45° on a calculator — **wrong quadrant** (the point is up-left); atan2 gives **135°**.
**Example:** $s = -1 + j2$, $T = 0.2$: $z = e^{-0.2}e^{j0.4} = 0.819\\cdot(\\cos 0.4 + j\\sin 0.4) = 0.754 + j0.319$.""",
        pitfalls=["Calculator mode: degrees vs radians.", "atan2, not plain tan⁻¹, when the real part is negative."],
        matlab="abs(-1+1i), angle(-1+1i)*180/pi, exp((-1+2i)*0.2)"),
    "f_poles": dict(
        intuition="Every linear system's behaviour is decided by a few special numbers: its **poles** (the roots of the denominator of its transfer function). "
                  "Each pole contributes one 'mode' to the response: decaying, growing or oscillating. **Stability** = all modes die out. "
                  "Continuous time (variable s): a pole must have negative real part. Discrete time (variable z): a pole must have magnitude < 1.",
        visual=lambda: plots.pole_response_grid(),
        visual_caption="Discrete poles: 0.6 decays, 0.95 decays slowly, 1.0 stays (border), −0.6 alternates and decays, −1 alternates forever, 1.1 explodes.",
        math=r"""- Transfer function $G = \dfrac{\text{numerator}}{\text{denominator}}$; **poles** = roots of the denominator, **zeros** = roots of the numerator.
- Quadratic $x^2 + bx + c = 0$: $x = \dfrac{-b \pm \sqrt{b^2 - 4c}}{2}$ (complex pair if $b^2 < 4c$).
- **s-domain:** stable ⇔ all Re(pole) < 0 (left half-plane).
- **z-domain:** stable ⇔ all |pole| < 1 (inside the unit circle). A discrete pole p gives a mode $p^k$: |p| < 1 ⇒ $p^k \to 0$.""",
        worked="""**s:** $s^2 + 3s + 2 = (s+1)(s+2)$ ⇒ poles −1, −2 ⇒ stable.
**z:** $z^2 - 1.3z + 0.4 = (z - 0.8)(z - 0.5)$ ⇒ poles 0.8, 0.5, both |p| < 1 ⇒ stable. $z^2 - z - 0.6$ has roots 1.42 and −0.42 ⇒ 1.42 > 1 ⇒ unstable.""",
        pitfalls=["Don't use the s-rule for z-polynomials (z = 0.5 is stable!).", "Complex pair: magnitude = √(product of the roots) = √c for monic quadratics."],
        matlab="roots([1 -1.3 0.4]), abs(roots([1 -1 -0.6]))"),
    "f_pfe": dict(
        intuition="Partial fractions = **taking a complicated fraction apart into simple pieces** whose transforms you can look up in the table. "
                  "It is the single most used hand-calculation in this exam (ZOH problem, inverse z-transform).",
        visual=None, visual_caption="",
        math=r"""$$\frac{N(s)}{(s-r_1)(s-r_2)} = \frac{A}{s-r_1} + \frac{B}{s-r_2},\qquad A = \left.\frac{N(s)}{s - r_2}\right|_{s=r_1},\quad B = \left.\frac{N(s)}{s - r_1}\right|_{s=r_2}$$
**Cover-up rule:** to find the coefficient of a factor, cover that factor and evaluate the rest at its root.
Repeated factor $s^2$: use pieces $\frac{A}{s^2} + \frac{B}{s} + \dots$ (B by comparing coefficients or one extra test value).""",
        worked="""$\\dfrac{1}{s(s+1)} = \\dfrac{A}{s} + \\dfrac{B}{s+1}$: A = 1/(0+1) = 1, B = 1/(−1) = −1 ⇒ $\\dfrac1s - \\dfrac{1}{s+1}$.
Check with s = 1: left 1/2, right 1 − 1/2 = 1/2 ✓.
Exam 2017: $\\dfrac{s - 0.25}{s(s+1)}$: A = (0 − 0.25)/1 = −0.25, B = (−1 − 0.25)/(−1) = 1.25.""",
        pitfalls=["Always check with one test value of s.", "The numerator is evaluated too — not only the other factors."],
        matlab="[r,p,k] = residue([1 -0.25],[1 1 0])"),
    "f_laplace": dict(
        intuition="The Laplace transform turns differential equations (continuous time) into algebra. A system is described by its **transfer function G(s)** = "
                  "output/input. You only need a few facts: the poles (speed and stability), the **DC gain** G(0) (where a step response ends), and the shape "
                  "of a first-order response (63 % after one time constant).",
        visual=lambda: plots.step_compare({"y(t) of 2/(4s+1)": list(2 * (1 - np.exp(-np.arange(40) * 0.4 / 4)))}, "First-order step response", T=0.4),
        visual_caption="Gain 2, time constant 4 s: after 4 s the output is 63 % of 2 = 1.26.",
        math=r"""- $\mathcal L\{\sigma(t)\} = \frac1s$ (step), $\mathcal L\{e^{-at}\} = \frac{1}{s+a}$, $\mathcal L\{t\} = \frac{1}{s^2}$
- $G(s) = \dfrac{K}{\tau s + 1}$: pole $-1/\tau$, step response $K(1 - e^{-t/\tau})$
- Final value of a step response = $G(0)$ (if stable)
- Dead time $T_t$: factor $e^{-T_t s}$
- Dividing by s ($G/s$) = step response — this is why the ZOH formula contains $G_P(s)/s$.""",
        worked="""$G = \\dfrac{10}{(s+1)(s+2)}$: poles −1, −2 (stable), DC gain 10/2 = 5 ⇒ a unit step ends at 5.""",
        pitfalls=["Pole = −1/τ, not −τ.", "DC gain = put s = 0."],
        matlab="G = tf(10,[1 3 2]); pole(G), dcgain(G), step(G)"),
    "f_feedback": dict(
        intuition="Feedback = measure the output, compare with the target, act on the difference (error). A P-controller multiplies the error by K_p. "
                  "Closing the loop **moves the poles** (usually faster) and changes the steady-state gain. Without an integrator a small error remains.",
        visual=None, visual_caption="",
        math=r"""$$G_W = \frac{\text{forward path}}{1 + \text{loop}} = \frac{K_pG}{1 + K_pG}$$
With $G = B/A$: $G_W = \dfrac{K_pB}{A + K_pB}$ — the **closed-loop poles are the roots of A + K_pB**. The same formula holds in z (exam P2).
Error after a step: $1 - G_W(\text{DC})$; an integrator in the loop makes it 0.""",
        worked="""$G = \\dfrac{2}{s+1}$, $K_p = 2$: $G_W = \\dfrac{4}{s + 5}$ ⇒ pole −5 (was −1), DC gain 0.8 ⇒ error 0.2.""",
        pitfalls=["Negative feedback ⇒ PLUS in the denominator.", "K_p appears in numerator and denominator."],
        matlab="GW = feedback(2*tf(2,[1 1]), 1)"),
    "f_matrix": dict(
        intuition="State-space models (exam P4, 15 points!) are written with small matrices: x(k+1) = G x(k) + h u(k). You need only a handful of "
                  "operations — multiply a matrix by a vector, determinant, eigenvalues, inverse of 2×2 — and MATLAB does the rest in the open-book part.",
        visual=None, visual_caption="",
        math=r"""For $M = \begin{bmatrix}a&b\\c&d\end{bmatrix}$:
- $Mv = \begin{bmatrix}a v_1 + b v_2\\ c v_1 + d v_2\end{bmatrix}$ (row times column)
- $\det M = ad - bc$; $\det M \neq 0$ ⇔ invertible ⇔ full rank
- $M^{-1} = \frac{1}{ad-bc}\begin{bmatrix}d&-b\\-c&a\end{bmatrix}$
- Eigenvalues: roots of $\det(\lambda I - M) = \lambda^2 - (a+d)\lambda + (ad - bc)$
- **The eigenvalues of the system matrix G are the poles of the system.**""",
        worked="""$G = \\begin{bmatrix}0&1\\\\-0.16&-1\\end{bmatrix}$: det = 0·(−1) − 1·(−0.16) = 0.16; trace = −1 ⇒ λ² + λ + 0.16 = 0 ⇒ λ = −0.2, −0.8 (both |λ| < 1 ⇒ stable).""",
        pitfalls=["Matrix product order matters: Gh ≠ hG.", "Rank check = determinant ≠ 0 for square matrices."],
        matlab="G=[0 1;-0.16 -1]; det(G), eig(G), inv(G)"),
}

PRIMERS = {
    "zt_basics": """**In plain words.** A digital controller is a computer: every T seconds it reads one number from a sensor and outputs one number. So all signals become **lists of numbers** x(0), x(1), x(2), … The **z-transform** writes such a list as a single expression X(z) = x(0) + x(1)z⁻¹ + x(2)z⁻² + … — think of **z⁻¹ as a 'one-step-later' tag**. That's it.

**Every symbol.** T = sampling time [s]; k = sample number; x(kT) or x(k) = value at sample k; σ(k) = step (1, 1, 1, …); δ₀(k) = single pulse (1, 0, 0, …); G(z) = system in the z-world; Y(z) = G(z)·U(z) = output.

**Tiny example.** List 0.5, 0.5, 1, 1, 0, … ⇒ U(z) = 0.5 + 0.5z⁻¹ + 1z⁻² + 1z⁻³. Done — no integrals.

**Why it matters.** 'Shift by one step' becomes 'multiply by z⁻¹', so equations become algebra. The final value theorem tells you where a sequence ends: put (1 − z⁻¹)X(z) and let z → 1.

**What the exam asks (P1, 7 P):** write U(z) from a plot, form Y = GU, final value, write the recursion, compute 5 numbers. All mechanical → use the 📋 Recipe.""",
    "zt_inverse": """**In plain words.** Going back: you are given X(z) and must produce the list of numbers. The easiest way (and the one the 2016 exam demanded) is the **computational method**: treat X(z) as a system that receives a single pulse, write its recursion, and *compute numbers one after another* like a spreadsheet.

**Tiny example.** X = 1/(1 − 0.5z⁻¹) ⇒ x(k) = 0.5·x(k−1) + δ(k) ⇒ 1, 0.5, 0.25, 0.125, …

**What the exam asks:** 'compute x(k) up to k = 4 by the computational method' — 6 points for careful bookkeeping.""",
    "diff_eq": """**In plain words.** A difference equation is a *program*: 'new output = some old outputs + some inputs'. Example: y(k) = 0.5·y(k−1) + u(k). Its z-transform gives G(z) = Y/U. Feeding a single pulse gives the **weighting sequence g(k)** (the system's fingerprint). Any output is a weighted sum of past inputs (convolution).

**Tiny example.** y(k) = 0.5y(k−1) + u(k), pulse input ⇒ g = 1, 0.5, 0.25, … ⇒ G(z) = 1/(1 − 0.5z⁻¹).""",
    "sampling": """**In plain words.** Sampling = taking snapshots. If a signal wiggles faster than half the snapshot rate, the snapshots lie: a fast wave looks like a slow one (**aliasing**, like car wheels spinning backwards in films). **Shannon:** sample more than twice as fast as the fastest frequency. The **zero-order hold (ZOH)** turns the computer's numbers back into a voltage by holding each value until the next one — a staircase.

**What the exam asks:** theory only (2–4 P): state Shannon *with the reason*, sketch a ZOH staircase, explain aliasing. Memorise the short answers (🔁 Review → 'Must memorise').""",
    "zoh_plant": """**In plain words.** The real plant (motor, tank…) is continuous and described by G_P(s). Between two samples the ZOH keeps the input constant — so the plant really receives a series of **steps**. To know what the plant does from sample to sample, we take its **step response** (that's the division by s) and the difference of consecutive steps (that's the factor (1 − z⁻¹)):

$$G(z) = (1 - z^{-1})\\,\\mathcal Z\\{G_P(s)/s\\}$$

**How you actually do it:** partial fractions (Foundations ▸ partial fractions) + three table entries + some fraction algebra. Fully mechanical → 📋 Recipe. Your safety net: MATLAB `c2d(Gp, T, 'zoh')` gives the same numbers to check.

**What the exam asks (P2a, 3 P):** exactly this, 'manually', every year.""",
    "closed_loop": """**In plain words.** Put the controller (here just a gain K) in front of G(z) and feed the output back: G_W = KG/(1 + KG). If G = B/A, then G_W = KB/(A + KB). The closed-loop **poles are the roots of A + KB** — check |root| < 1 for stability.

**What the exam asks (P2b–d, 4 P):** G_W(z) (2 P), 'is it stable? reason!' (1 P), 'can you write a disturbance transfer function?' — answer **No**, the disturbance is not sampled (1 P).""",
    "mapping": """**In plain words.** The continuous world (s) and the digital world (z) are linked by z = e^{sT}. The stable left half of the s-plane becomes the inside of the unit circle. A pole's *distance from the origin* tells how fast it decays (small = fast), its *angle* tells how fast it oscillates. Design specs like 'damping ζ = 0.5' become a point you compute with one formula.""",
    "stability": """**In plain words.** Stable = every pole inside the unit circle. If the polynomial is factored you just look at the roots (P3b, 1 P). If not, the **Jury test** decides from the coefficients with a fixed table — no root finding. It is pure bookkeeping: 4 conditions for a cubic.

**What the exam asks (P3a, 5 P):** the Jury table for a cubic. This is the **most reliable 6 points** of the exam for a beginner — drill it until you are fast (⚖️ Boss 'The Jury').""",
    "discretization": """**In plain words.** If you already have an analog controller G_C(s), you can translate it into a digital one by replacing s with a formula in z (Tustin, backward difference) or by moving each pole/zero with z = e^{sT}. Also: choose T small enough (≈ 8 samples per oscillation period).

**Beginner priority:** low — know the three names and one property each for theory; in the practical MATLAB `c2d(Gc,T,'tustin')` does it.""",
    "root_locus": """**In plain words.** The root locus shows how the closed-loop poles move as you turn up the gain K. To design, you pick where you *want* the poles and then compute the controller zero (angle condition) and gain (magnitude condition).

**Beginner priority:** low for the exam — if it appears, MATLAB `rlocus`/`rltool` does it; follow the 📋 Recipe.""",
    "analytic_design": """**In plain words.** Three 'design-by-wish' methods: **dead-beat** (output reaches the target in the minimum number of steps), **MFC** (you prescribe the whole desired closed-loop transfer function and solve for the controller), **IMC** (the controller contains a model of the plant and inverts its 'nice' part).

**Beginner priority:** theory only — memorise the 2-point answer 'basic idea of MFC' (asked in 2017).""",
    "ss_models": """**In plain words.** Instead of one big equation, describe the system with a few internal quantities — the **state** x (e.g. position and velocity). Each step: new state = G·old state + h·input; output = cᵀ·state. G, h, c are small matrices/vectors. The **eigenvalues of G are the poles**.

**Tiny example.** Position p and velocity v, T = 0.2: p(k+1) = p(k) + 0.2v(k) + 0.02u(k), v(k+1) = v(k) + 0.2u(k) ⇒ G = [[1, 0.2], [0, 1]], h = [0.02, 0.2].""",
    "ctrb_obsv": """**In plain words.** **Controllable:** with the input you can push the state anywhere. **Observable:** from the measured output you can figure out the whole state. Test: build a matrix (Q_C from h, Gh, …; Q_O from cᵀ, cᵀG, …) and check its determinant ≠ 0.

**What the exam asks:** 1–2 P in P4 (MATLAB `ctrb`, `obsv`, `rank`) + theory 'define observability (with the formula)' (2 P).""",
    "pole_placement": """**In plain words.** If you can measure all states, use u = −kᵀx: feed back every state with its own gain. This lets you put the closed-loop poles **wherever you want** (if controllable). K_w scales the reference so the output reaches it. Adding an **integrator** of the error (w − y) removes any remaining offset.

**What the exam asks (P4a, 5 P):** 'state feedback with integration of the control error, poles at …' → build the augmented matrices and call `acker` in MATLAB (📋 Recipe). The theory part may ask you to **draw the block diagram** (3 P) — memorise it.""",
    "observers": """**In plain words.** If you cannot measure all states, **estimate** them: run a copy of the model in the computer with the same input, compare its predicted output with the real measurement, and correct the copy by p·(error). Choose p so the estimation error dies out fast (observer poles closer to 0 than the controller poles).

**What the exam asks (P4b, 4 P):** observability check + `p = acker(G', c', poles)'` + one sentence on how you chose the poles. Theory: predictive vs current observer, why use an observer (1 P each).""",
    "lqr": """**In plain words.** Instead of choosing poles, you say what you care about: Q (how bad are state deviations) and R (how expensive is control effort). The computer finds the best gains (`dlqr`). It only works if the system is **stabilisable** and the unstable parts are **detectable** in Q — that sentence is a recurring theory question.

**Beginner priority:** theory sentence (2 P, every year) + MATLAB `dlqr` recipe.""",
    "fb_lin": """**In plain words.** Some nonlinear systems can be made exactly linear by computing the input cleverly (cancelling the nonlinearity) and changing coordinates. The **relative degree** δ = how many steps until the input shows up in the output.

**Beginner priority:** theory only — memorise the two short answers (idea of exact feedback linearisation, meaning of relative degree; 2 P each, asked 2016 and 2017).""",
}
