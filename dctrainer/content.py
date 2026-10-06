"""Learning-module content per topic: Intuition → Visual → Mathematics → Worked example → Pitfalls → MATLAB.

Worked examples are taken from the lecture notes / past exams and the numbers are recomputed at import time
with the same helpers the trainer uses (so text and app can never disagree).
"""
from __future__ import annotations

import numpy as np

from . import plots
from .mathutil import (acker, augment_integral, current_observer_gain, dare_gain, fmat, fnum, fvec, jury_table,
                       kw_gain, predictive_observer_gain, series_zinv, z_from_zeta_ratio, zoh_tf)

# ----------------------------------------------------------------- precomputed numbers
_y17 = series_zinv([1.0], [1.0, -0.4], 5, u=[0.5, 0.5, 1, 1, 0, 0, 0])
_x16 = series_zinv([1.0, 2.0], [1.0, -0.8, 0.16], 5)
_x27 = series_zinv([0, 10.0, 5.0], [1.0, -1.2, 0.2], 7)
_n31, _d31 = zoh_tf([1.0], [1.0, 1.0, 0.0], 1.0)
_n17, _d17 = zoh_tf([1.0, -0.25], [1.0, 1.0], 0.25)
_J16 = jury_table([1, 0.2, -0.5, 0.1])
_m, _a, _z44 = z_from_zeta_ratio(0.5, 0.1)
_G61 = np.array([[0, 1], [-0.16, -1.0]])
_h61 = np.array([0, 1.0])
_c61 = np.array([1, 1.0])
_k61 = acker(_G61, _h61, [0.5 + 0.5j, 0.5 - 0.5j])
_kw61 = kw_gain(_G61, _h61, _c61, _k61)
_p64 = predictive_observer_gain(_G61, _c61, [0.2, 0.2])
_p65 = current_observer_gain(_G61, _c61, [0.2, 0.2])
_G17 = np.array([[0, 1, 0], [0, 0, 1], [0.315, -1.43, 2.1]])
_h17 = np.array([0, 0, 1.0])
_c17 = np.array([0.5, 1, 0.0])
_Gh17, _hh17 = augment_integral(_G17, _h17, _c17)
_kh17 = acker(_Gh17, _hh17, [0.5 + 0.5j, 0.5 - 0.5j, 0.25, 0.2])
_p17 = predictive_observer_gain(_G17, np.array([1.0, 0, 0]), [0.1, 0.1, 0.1])
_S75, _K75 = dare_gain([[1, 0.5], [0, 1]], [0.125, 0.5], np.eye(2), 1.0)

MODULES = {
    "zt_basics": dict(
        intuition="A digital controller only ever sees numbers x(0), x(1), x(2), … The z-transform packs this whole sequence into one function "
                  "X(z) = Σ x(k) z⁻ᵏ, where **z⁻¹ means 'one sample later'**. Delays become multiplications, difference equations become algebra — "
                  "exactly like the Laplace transform for differential equations.",
        visual=lambda: plots.piecewise_signal([0, 0.4, 0.8], [0.5, 1.0, 0.0], 0.2, 8, samples=[0.5, 0.5, 1, 1, 0, 0, 0, 0],
                                              title="Exam 2017 P1: u(t) and u(kT), T = 0.2 s"),
        visual_caption="Each sample becomes the coefficient of one power of z⁻¹: U(z) = 0.5 + 0.5z⁻¹ + z⁻² + z⁻³.",
        math=r"""**Definition** $X(z) = \sum_{k=0}^{\infty}x(kT)z^{-k}$ (one-sided).

| $x(kT)$ | $X(z)$ |
|---|---|
| $\delta_0(k)$ | $1$ |
| $\sigma(k)$ | $\dfrac{1}{1-z^{-1}}$ |
| $a^k$, $e^{-akT}$ | $\dfrac{1}{1-az^{-1}}$, $\dfrac{1}{1-e^{-aT}z^{-1}}$ |
| $kT$ | $\dfrac{Tz^{-1}}{(1-z^{-1})^2}$ |
| $\sin\omega kT$ | $\dfrac{z^{-1}\sin\omega T}{1-2z^{-1}\cos\omega T+z^{-2}}$ |

**Shift right** $\mathcal Z\{x(k-n)\} = z^{-n}X(z)$ · **shift left** $\mathcal Z\{x(k+n)\} = z^n[X(z) - \sum_{k=0}^{n-1}x(k)z^{-k}]$

**IVT** $x(0) = \lim_{z\to\infty}X(z)$ · **FVT** $x(\infty) = \lim_{z\to1}(1-z^{-1})X(z)$ (only if the limit exists!)""",
        worked=f"""**Exam 2017, Problem 1 (7 P)** — $u(t) = 0.5$ on $[0, 0.4)$, $1$ on $[0.4, 0.8)$, $0$ afterwards; $T = 0.2$ s; $G(z) = 1/(1-0.4z^{{-1}})$.

1. Samples: $u = [0.5, 0.5, 1, 1, 0, \\dots]$ ⇒ $U(z) = 0.5 + 0.5z^{{-1}} + z^{{-2}} + z^{{-3}}$, $Y(z) = \\dfrac{{0.5 + 0.5z^{{-1}} + z^{{-2}} + z^{{-3}}}}{{1 - 0.4z^{{-1}}}}$ ✓ (2 P)
2. Final value: $(1-z^{{-1}})Y(z) \\to 0$ for $z \\to 1$ (finite input) ⇒ $y(\\infty) = 0$ ✓ (2 P)
3. Difference equation: $y(k) = 0.4\\,y(k-1) + u(k)$ — **this 1 P was lost in the real exam (left blank)**.
4. Recursion: $y = {fvec(_y17)}$ ✓ (2 P)""",
        pitfalls=["Sample at a jump = value AFTER the jump (x(νT) = x(νT⁺)).",
                  "FVT: multiply by (1 − z⁻¹) BEFORE setting z = 1; check stability first.",
                  "Don't forget the 'easy' sub-questions (difference equation!) — 1 P each."],
        matlab="u = [0.5 0.5 1 1 0 0 0];\ny = filter(1, [1 -0.4], u)      % y(k) = 0.4 y(k-1) + u(k)\nG = tf([1 0],[1 -0.4], 0.2);    % z/(z-0.4)\nlsim(G, u)"),
    "zt_inverse": dict(
        intuition="Going back from X(z) to numbers: (1) **long division** gives the first samples, (2) **partial fractions** give a closed formula, "
                  "(3) the **computational method** treats X(z) as a system driven by a single unit pulse and simply runs the recursion. "
                  "In the exam (2016 P1) the computational method by hand was required.",
        visual=lambda: plots.stem_seq({"x(k) of (10z+5)/(z²−1.2z+0.2)": series_zinv([0, 10, 5], [1, -1.2, 0.2], 10)}, "Book Ex. 2.7–2.9"),
        visual_caption="The three methods give the same sequence {0, 10, 17, 18.4, 18.68, …} → 18.75.",
        math=r"""**Computational method:** $X(z) = \dfrac{N(z^{-1})}{D(z^{-1})}U(z)$, $U(z) = 1 \Leftrightarrow u = \delta_0$. Write $D\cdot X = N\cdot U$ as a difference equation and recurse with $x(k<0) = 0$.

**Partial fractions:** expand $\dfrac{X(z)}{z} = \dfrac{A}{z} + \sum\dfrac{B_i}{z-p_i}$ ⇒ $x(k) = A\delta_0(k) + \sum B_ip_i^k$.
Complex pairs: match $\dfrac{1 - e^{-aT}z^{-1}\cos\omega T}{1 - 2e^{-aT}z^{-1}\cos\omega T + e^{-2aT}z^{-2}}$ and the sin-entry.""",
        worked=f"""**Exam 2016, Problem 1 (6 P):** $X(z) = \\dfrac{{z(z+2)}}{{(z-0.4)^2}} = \\dfrac{{1 + 2z^{{-1}}}}{{1 - 0.8z^{{-1}} + 0.16z^{{-2}}}}$

Difference equation: $x(k) = 0.8x(k-1) - 0.16x(k-2) + u(k) + 2u(k-1)$, $u = \\delta_0$:
$x = {fvec(_x16)}$ (full marks in the real exam).

**Book Ex. 2.8:** $\\dfrac{{X}}{{z}} = \\dfrac{{10z+5}}{{z(z-1)(z-0.2)}} = \\dfrac{{25}}{{z}} + \\dfrac{{18.75}}{{z-1}} - \\dfrac{{43.75}}{{z-0.2}}$ ⇒ $x(k) = 25\\delta_0 + 18.75 - 43.75(0.2)^k$; check: {fvec(_x27)}.""",
        pitfalls=["Divide numerator AND denominator by the highest power of z before reading coefficients.",
                  "Recursion: denominator coefficients change sign on the right-hand side.",
                  "Partial fractions of X(z)/z, not X(z)."],
        matlab="x = filter([1 2], [1 -0.8 0.16], [1 zeros(1,4)])   % computational method\n[r,p,k] = residuez([0 10 5], [1 -1.2 0.2])        % partial fractions in z^-1"),
    "diff_eq": dict(
        intuition="A difference equation IS the controller program. Its z-transform G(z) = Y/U is the pulse transfer function; "
                  "feeding a single unit pulse gives the weighting sequence g(k) — the discrete 'impulse response'. Any output is a weighted sum of past inputs (convolution).",
        visual=lambda: plots.stem_seq({"g(k) = 0.5ᵏ": [0.5 ** k for k in range(8)]}, "Weighting sequence of y(k) − 0.5y(k−1) = u(k)"),
        visual_caption="Book Ex. 2.12: G(z) = 1/(1 − 0.5z⁻¹) ⇒ g(k) = 0.5ᵏ.",
        math=r"""$y(k) + a_1y(k-1) + \dots + a_ny(k-n) = b_0u(k-d) + \dots$ ⇒ $G(z) = \dfrac{b_0 + b_1z^{-1} + \dots}{1 + a_1z^{-1} + \dots}z^{-d}$

$g(k) = \mathcal Z^{-1}\{G(z)\}$, $y(k) = \sum_{h=0}^{k}g(k-h)u(h)$.

Initial conditions: use the shift-left table $\mathcal Z\{x(k+1)\} = zX - zx(0)$, $\mathcal Z\{x(k+2)\} = z^2X - z^2x(0) - zx(1)$.""",
        worked="""**Book Ex. 2.14:** $x(k+2) - 1.2x(k+1) + 0.35x(k) = 0$, $x(0)=0$, $x(1)=1$:
$[z^2 - 1.2z + 0.35]X(z) = z$ ⇒ $X/z = \\dfrac{-5}{z-0.5} + \\dfrac{5}{z-0.7}$ ⇒ $x(k) = 5(0.7)^k - 5(0.5)^k = \\{0, 1, 1.2, 1.09, 0.888, \\dots\\}$, final value 0.

**Homework 2:** $y(k) - 0.9y(k-1) + 0.14y(k-2) = u(k)$ ⇒ $G(z) = 1/(1 - 0.9z^{-1} + 0.14z^{-2})$, $g = \\{1, 0.9, 0.67, 0.477, \\dots\\}$.""",
        pitfalls=["g(k) is the response to δ₀, not to a step.", "Convolution: indices of g and u add up to k."],
        matlab="g = filter(1, [1 -0.9 0.14], [1 zeros(1,9)])\ny = conv(g, [1 1 1]); y(1:8)"),
    "sampling": dict(
        intuition="Sampling multiplies the signal with a train of Dirac pulses → the spectrum is copied every ω_s. If the copies overlap, high frequencies "
                  "masquerade as low ones (aliasing) and the original cannot be recovered. The ZOH turns numbers back into a staircase — a low-pass that "
                  "behaves roughly like a dead time of T/2.",
        visual=lambda: plots.aliasing_figure(1.0, 1.25),
        visual_caption="f = 1 Hz sampled at 1.25 Hz looks like 0.25 Hz — Shannon violated.",
        math=r"""$x^*(t) = \sum x(kT)\delta(t-kT)$, $X^*(j\omega) = \frac1T\sum_n X(j(\omega - n\omega_s))$

**Shannon:** reconstruction possible if $\omega_s > 2\omega_1$ (band-limited x). Ideal low-pass $g_I(t) = \frac1T\frac{\sin(\omega_st/2)}{\omega_st/2}$ is non-causal.

**ZOH:** $H_0(s) = \frac{1-e^{-Ts}}{s}$, $|H_0(j\omega)| = T\left|\frac{\sin(\omega T/2)}{\omega T/2}\right|$, phase $-\omega T/2$ ⇒ $H_0 \approx \frac{1}{1+0.5Ts}$ (gain-normalised).""",
        worked="""**Exam 2016 Th.g (2 P):** sample a signal at f_s = 4 Hz (every 0.25 s), round to the nearest multiple of 0.5, hold → staircase that starts at each sampling instant. Full marks for correct timing + rounding + hold.

**Exam 2017 Th.c (1.5 P):** 'The sampling frequency must be at least double the highest frequency in the signal, otherwise aliasing appears; ω_s > 2ω' → 1.5/1.5.
**Exam 2016 Th.b:** the same statement without explanation got 1/2 ('why?') → add the spectrum argument.""",
        pitfalls=["Strict inequality ω_s > 2ω₁; assumption: band-limited signal.", "Always give the WHY (overlapping spectra).",
                  "Shannon is not the practical rule for control loops (T ≤ 0.125·T₂)."],
        matlab="t = 0:1e-3:4; k = 0:0.8:4;\nplot(t, sin(2*pi*t), k, sin(2*pi*k), 'o')   % aliasing demo\n% lecture_material/run_example_unit4_3_aliasing.mdl"),
    "zoh_plant": dict(
        intuition="The plant does not see numbers — it sees the staircase from the hold. A staircase is a sum of shifted steps, so we need the plant's STEP "
                  "response transform Z{G_P/s} and the difference of consecutive steps gives the factor (1 − z⁻¹).",
        visual=lambda: plots.zoh_figure(0.25),
        visual_caption="ZOH output = Σ u(kT)[σ(t − kT) − σ(t − (k+1)T)].",
        math=r"""$$G(z) = (1 - z^{-1})\,\mathcal Z\left\{\frac{G_P(s)}{s}\right\}$$
Recipe: (1) partial fractions of $G_P(s)/s$; (2) table: $\frac{1}{s} \to \frac{1}{1-z^{-1}}$, $\frac{1}{s+a} \to \frac{1}{1-e^{-aT}z^{-1}}$, $\frac{1}{s^2} \to \frac{Tz^{-1}}{(1-z^{-1})^2}$; (3) multiply by $(1-z^{-1})$, common denominator; (4) dead time $e^{-dTs} \to z^{-d}$.
Poles map as $e^{p_iT}$; DC gain is preserved: $G(1) = G_P(0)$.""",
        worked=f"""**Book Ex. 3.1:** $G_P = \\frac{{1}}{{s(s+1)}}$, $T = 1$: $\\frac{{G_P}}{{s}} = \\frac{{1}}{{s^2}} - \\frac1s + \\frac{{1}}{{s+1}}$ ⇒
$G(z) = \\dfrac{{{fnum(_n31[1])}z^{{-1}} + {fnum(_n31[2])}z^{{-2}}}}{{(1-z^{{-1}})(1-0.3679z^{{-1}})}}$.

**Exam 2017 P2a (3 P, lost in the real exam — the student used the Padé approximation instead):** $G_w = \\frac{{s-0.25}}{{s+1}}$, $T = 0.25$:
$\\frac{{G_w}}{{s}} = \\frac{{-0.25}}{{s}} + \\frac{{1.25}}{{s+1}}$ ⇒ $G(z) = -0.25 + 1.25\\frac{{1-z^{{-1}}}}{{1-0.7788z^{{-1}}}} = \\dfrac{{1 {fnum(_n17[1])}z^{{-1}}}}{{1 {fnum(_d17[1])}z^{{-1}}}}$ (biproper: $b_0 = 1 = G_w(\\infty)$).""",
        pitfalls=["Never use the Padé/ZOH approximation 1/(1 + 0.5Ts) when the EXACT G(z) is asked.",
                  "Don't forget (1 − z⁻¹) — the integrator pole must cancel.", "Dead time must be an integer number of samples → z⁻ᵈ."],
        matlab="Gz = c2d(tf([1 -0.25],[1 1]), 0.25, 'zoh')\n% with dead time: tf(1,[1 1],'InputDelay',0.5)"),
    "closed_loop": dict(
        intuition="Close the loop around G(z): G_W = G_D G/(1 + G_D G). Only signals that pass a sampler have z-transforms of their own — "
                  "a disturbance that enters the continuous plant never gets sampled, so you can compute its EFFECT but not a transfer function Y/D.",
        visual=lambda: plots.step_compare({"Book Ex. 3.6, K_p = 0.5": series_zinv([0, 0.18395, 0.1321], [1, -1.18395, 0.5], 20, u=[1] * 20)}, "Closed-loop step"),
        visual_caption="G_W = (0.1839z⁻¹ + 0.1321z⁻²)/(1 − 1.184z⁻¹ + 0.5z⁻²) (integrating plant ⇒ no offset).",
        math=r"""$G_W(z) = \dfrac{G_D(z)G(z)}{1 + G_D(z)G(z)}$, with $G_DG = \frac{KB}{A}$: $G_W = \frac{KB}{A + KB}$.
Disturbance through $G_{PZ}(s)$ (no sampler): $Y(z) = \dfrac{G_{PZ}Z(z)}{1 + G_DG(z)}$ — $G_{PZ}Z(z) \ne G_{PZ}(z)Z(z)$.
Sampler rules: blocks without a sampler in between are transformed together ($G_1G_2(z)$).
PID (Euler): $G_D = \dfrac{d_0 + d_1z^{-1} + d_2z^{-2}}{1 - z^{-1}}$.""",
        worked="""**Book Ex. 3.6:** $G(z) = \\frac{0.3679z^{-1} + 0.2642z^{-2}}{(1-z^{-1})(1-0.3679z^{-1})}$, $K_p = 0.5$:
denominator $(1 - 1.3679z^{-1} + 0.3679z^{-2}) + 0.5(0.3679z^{-1} + 0.2642z^{-2}) = 1 - 1.184z^{-1} + 0.5z^{-2}$; poles $|z| = \\sqrt{0.5} = 0.707$ ⇒ stable.

**Exam P2d (1 P each year):** 'Can you derive G_d(z) = Y/D?' → **No**, d is not sampled before the continuous plant (2016: full point for 'no input sampler for d').""",
        pitfalls=["A + K·B (plus sign!).", "K appears in the numerator too.", "Stability: check the roots, don't guess from a plot ('checked with rltool' got 0 P in 2017 without reasoning)."],
        matlab="G = c2d(tf(1,[1 1 0]), 1);\nGW = feedback(0.5*G, 1); pole(GW), abs(pole(GW))\nstep(GW)"),
    "mapping": dict(
        intuition="z = e^{sT} bends the s-plane: the stability boundary (imaginary axis) becomes the unit circle, faster decay means smaller |z|, "
                  "higher frequency means larger angle. Design specs in s (ζ, ω_n, σ) become circles and spirals in z.",
        visual=lambda: plots.mapping_figure(0.2),
        visual_caption="σ = const → circles |z| = e^{−σT}; ζ = const → logarithmic spirals.",
        math=r"""$z = e^{Ts}$: $|z| = e^{\sigma T}$, $\arg z = \omega T$.
$s = -\zeta\omega_n \pm j\omega_d$ with $T = 2\pi/\omega_s$:
$$|z| = \exp\left[-\frac{2\pi\zeta}{\sqrt{1-\zeta^2}}\frac{\omega_d}{\omega_s}\right],\qquad \arg z = 2\pi\frac{\omega_d}{\omega_s}$$
(⚠ formula sheet p. 8 misprints $\omega_n = \omega_d/\sqrt{1\zeta^2}$ — it is $\sqrt{1-\zeta^2}$.)""",
        worked=f"""**Book Ex. 4.4:** $\\zeta = 0.5$, $\\omega_s = 10\\omega_d$: $|z| = \\exp(-2\\pi\\cdot0.5/\\sqrt{{0.75}}\\cdot0.1) = {fnum(_m)}$, $\\arg z = 36°$ ⇒ $z_{{1,2}} = {fnum(_z44.real)} \\pm j{fnum(_z44.imag)}$.
**Book Ex. 3.7:** $s = -1 \\pm j\\omega$, $T = 0.2$ → circle $|z| = e^{{-0.2}} = 0.819$.""",
        pitfalls=["arg z in radians inside cos/sin.", "Use ω_d for the angle, ζω_n for the radius."],
        matlab="z = exp((-0.5*2 + 1j*2*sqrt(0.75))*0.2)\nzgrid   % damping spirals in rlocus plots"),
    "stability": dict(
        intuition="Stable ⇔ every closed-loop pole strictly inside the unit circle. The Jury table checks this from the coefficients without computing "
                  "roots — mechanical, fast, and worth 5–6 points every year.",
        visual=lambda: plots.zplane(np.roots([1, 0.2, -0.5, 0.1]), title="2016 P3: roots of z³ + 0.2z² − 0.5z + 0.1"),
        visual_caption="All roots inside the unit circle — Jury must say 'stable'.",
        math=r"""$P(z) = a_nz^n + \dots + a_0$. Rows: $a_0 \dots a_n$ / reversed; $b_k = a_0a_k - a_na_{n-k}$; $c_k = b_0b_k - b_{n-1}b_{n-1-k}$ …

**Stable ⇔** $P(1) > 0$, $(-1)^nP(-1) > 0$, $|a_0| < |a_n|$, $|b_0| > |b_{n-1}|$, $|c_0| > |c_{n-2}|$, …

**w-transform:** $z = \frac{1+w}{1-w}$, multiply by $(1-w)^n$, then Hurwitz.""",
        worked=f"""**Exam 2016, Problem 3a (5 P):** $P(z) = z^3 + 0.2z^2 - 0.5z + 0.1$, $a = [0.1, -0.5, 0.2, 1]$
- $P(1) = 0.8 > 0$ ✓
- $(-1)^3P(-1) = -(-1 + 0.2 + 0.5 + 0.1) = {fnum(_J16['Pm1'])} > 0$ ✓ — **the student wrote 1.2 and lost 1 P**
- $|a_0| = 0.1 < 1$ ✓
- $b = {fvec(_J16['rows'][1])}$: $|b_0| = 0.99 > |b_2| = 0.52$ ✓ ⇒ **asymptotically stable**.

**Exam 2017 P3:** $P = z^3 + 0.1z^2 - 0.3z$ ($a_0 = 0$) — table was right, but P(1) and P(−1) checks were missing ⇒ 3/5.
**P3b (1 P):** factored $P = z(z+0.6)(z-0.5)$ ⇒ all roots inside ⇒ stable — instant.""",
        pitfalls=["(−1)ⁿ factor; compute P(−1) term by term.", "List ALL n+1 conditions with numbers.",
                  "Rows start with a₀ (z⁰).", "For K-ranges: each condition becomes a linear inequality."],
        matlab="P = [1 0.2 -0.5 0.1]; abs(roots(P))\n% Jury by hand; for K-range: margin(G) gives the gain margin = K_crit"),
    "discretization": dict(
        intuition="Design a controller in s (you know how), then translate it to z. Every translation rule distorts something; Tustin keeps stability "
                  "exactly, matched pole-zero keeps pole locations, backward difference is crude but always stable. Sample fast enough (≈ 8 samples per period).",
        visual=lambda: plots.zplane([0.4286], [0.7143], extra=[([0.2], "bs", "Tustin pole"), ([0.667], "gD", "Tustin zero")], title="Book Ex. 4.1: backward (x/o) vs Tustin"),
        visual_caption="Same G_C(s) = 20.267(s+2)/(s+6.667), T = 0.2 s, different z-plane locations.",
        math=r"""Backward: $s = \frac{1-z^{-1}}{T}$ · Tustin: $s = \frac{2}{T}\frac{1-z^{-1}}{1+z^{-1}}$ · Matched: $z_i = e^{s_iT}$, zeros at ∞ → $z = -1$, gain matched at $z = 1$ (or $z=-1$ for high-pass/integrators).
Sampling time: $T \le 0.125\,T_1$ (aperiodic) / $T \le 0.125\,T_2$ (oscillatory). ZOH in continuous design: $\frac{1}{1+0.5Ts}$.""",
        worked="""**Book Ex. 4.1** ($G_C = 20.267\\frac{s+2}{s+6.667}$, $T = 0.2$):
- backward: $12.16\\frac{1-0.7143z^{-1}}{1-0.4286z^{-1}}$
- Tustin: $14.592\\frac{1-0.667z^{-1}}{1-0.2z^{-1}}$
- matched: $13.581\\frac{1-0.6703z^{-1}}{1-0.2636z^{-1}}$
**Book Ex. 4.2** (PI, matched, gain at z = −1): $9.279\\frac{z-0.8752}{z-1}$.""",
        pitfalls=["Tustin factor is 2/T.", "Matched: for an integrator (pole at s = 0) match the gain at z = −1 / s = ∞."],
        matlab="Gc = tf(20.267*[1 2],[1 6.667]);\nc2d(Gc, 0.2, 'tustin'), c2d(Gc, 0.2, 'matched')"),
    "root_locus": dict(
        intuition="Pick where you want the dominant closed-loop poles (from ζ and ω_s/ω_d). The angle condition tells you where the controller zero must "
                  "sit so that the locus passes through that point; the magnitude condition gives the gain that puts the poles exactly there.",
        visual=lambda: plots.root_locus_figure(np.array([0.3679, 0.2642]), np.array([1, -1.3679, 0.3679]), K_marks=[(0.42, "K_p = 0.42 (ζ = 0.6)")],
                                               title="Book Ex. 4.3"),
        visual_caption="K_p,crit ≈ 2.39 where the locus leaves the unit circle.",
        math=r"""Angle: $\sum\varphi_q - \sum\varphi_p = \pm180°$ ⇒ $\varphi_{qC} = -180° + \sum\varphi_p - \sum\varphi_q$ (incl. the controller pole at z = 1).
$q_C = \mathrm{Re}\,z_1 - \mathrm{Im}\,z_1/\tan\varphi_{qC}$; gain $K = \frac{\prod|z_1 - p|}{\prod|z_1 - q|}$.
Static errors: $e_p = \frac{1}{1+K_p}$, $e_v = 1/K_v$.""",
        worked="""**Book Ex. 4.4:** $G = \\frac{0.5404(z+0.5586)}{(z-0.6065)(z-0.2865)}$, $z_1 = 0.5629 + j0.4090$:
$\\varphi_{qC} = -180° + 136.9° + 96.1° + 55.9° - 20° = 88.9°$ ⇒ $q_C = 0.555$; magnitude ⇒ $K = 0.2489$, $K_p = K/0.5404 = 0.461$.
Third pole 0.518 ≈ controller zero 0.555 ⇒ z₁,₂ dominant.""",
        pitfalls=["Include the controller's own pole z = 1.", "Angles of vectors FROM poles/zeros TO z₁.", "K (root-locus gain) vs K_p (controller gain)."],
        matlab="G = zpk(-0.5586, [0.6065 0.2865], 0.5404, 0.25);\nrltool(G)   % or rlocus(G*tf([1 -0.555],[1 -1],0.25)); zgrid"),
    "analytic_design": dict(
        intuition="Instead of tuning a PID, prescribe the closed-loop behaviour you want and solve for the controller: dead-beat = 'finish in n steps', "
                  "MFC = 'behave like this model', IMC = 'invert the invertible part of a model, filter the rest'. In the exam these mostly appear as theory "
                  "('basic idea of MFC', 2 P).",
        visual=lambda: plots.step_compare({"y (dead-beat, Ex. 4.8)": [0, 0, 0, 0, 1, 1, 1, 1], "u": [1.1302, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]},
                                          "Dead-beat: y(k) = w(k − 4)"),
        visual_caption="Book Ex. 4.8: 4e^{−3s}/(1+4s), T = 1 s.",
        math=r"""**Dead-beat, stable plant, C = 1:** $F_W = \frac{B(z)}{B(1)}z^{-d}$, $G_D = \frac{A(z)}{B(1) - B(z)z^{-d}}$, $u(0) = \frac{1}{B(1)}$; constraint: $c_1 = \frac{1}{u(0)B(1)} - 1$.
**MFC:** $PU = FW - QY$, $G_W = \frac{FBz^{-d}}{PA + QBz^{-d}}$; Diophantine $\tilde PA + QB^-z^{-(1+d)} = A_WA_o$; degrees $n_Q = n$ ($n-1$ for integrating plants), $n_{\tilde P} \ge n_Q - n_{B^+} + d$, $n_{A_o} = n_{\tilde P} + n - n_{A_W}$.
**IMC:** $\tilde G = \tilde G^+\tilde G^-$, $G_C^* = F/\tilde G^+$, $G_W = \tilde G^-F$, $G_Z = 1 - \tilde G^-F$.""",
        worked="""**Book Ex. 4.8:** $G = \\frac{0.8848z^{-1}}{1-0.7788z^{-1}}z^{-3}$ ⇒ $F_W = z^{-4}$, $G_D = \\frac{1.1302 - 0.8802z^{-1}}{1 - z^{-4}}$, $u(0) = 1.1302$.
With $u(0) = 1$: $c_1 = 0.1302$ ⇒ $F_W = 0.8848z^{-4} + 0.1152z^{-5}$ (OCR of the book shows the $G_D$ denominator as '…z⁻¹ − 0.1152z⁻⁵'; correct is $1 - 0.8848z^{-4} - 0.1152z^{-5}$).
**Book Ex. 4.12 (IMC):** $\\tilde G = \\frac{0.1813z^{-3}}{1-0.8187z^{-1}}$, $\\alpha = 0.5$ ⇒ $G_C^* = \\frac{2.7579 - 2.2579z^{-1}}{1 - 0.5z^{-1}}$.""",
        pitfalls=["Never cancel plant poles/zeros on or outside the unit circle.", "Cancelling zeros near −1 ⇒ ringing.", "G_W must contain the plant dead time."],
        matlab="% Homework 6 (MFC) and lecture_material/deadbeat_design.zip contain full MATLAB solutions"),
    "ss_models": dict(
        intuition="Instead of one n-th order difference equation, keep n first-order ones in a vector: x(k+1) = Gx(k) + hu(k). The same plant has many "
                  "state representations (companion, Jordan, physical), all with the same eigenvalues = poles.",
        visual=None, visual_caption="",
        math=r"""Controllability canonical form: last row $[-a_n, \dots, -a_1]$, $h = [0, \dots, 0, 1]^T$, $c^T = [b_n - a_nb_0, \dots, b_1 - a_1b_0]$.
Jordan form: $G = \mathrm{diag}(\lambda_i)$, $h = [1, \dots, 1]^T$, $c_i$ = residues of $G(z)$.
Discretisation: $G = e^{AT}$, $h = \int_0^Te^{A\mu}d\mu\,b = A^{-1}(G - I)b$.
$G_{PU}(z) = c^T(zI-G)^{-1}h + d$.""",
        worked="""**Book Ex. 5.2:** $\\frac{z^{-1} + 5z^{-2}}{1 + 4z^{-1} + 3z^{-2}}$ ⇒ $G = \\begin{bmatrix}0&1\\\\-3&-4\\end{bmatrix}$, $c^T = [5, 1]$.
**Book Ex. 5.5:** $\\frac{1}{s(s+2)}$: $G = \\begin{bmatrix}1 & 0.5(1-e^{-2T})\\\\0 & e^{-2T}\\end{bmatrix}$, $h = \\begin{bmatrix}0.5(T + 0.5(e^{-2T}-1))\\\\0.5(1-e^{-2T})\\end{bmatrix}$.
**Exam 2016 P4b:** 'transform into Jordan canonical form' — MATLAB `canon(ptf,'modal')`.""",
        pitfalls=["MATLAB tf2ss orders states differently (first row = −a).", "e^{AT} ≠ I + AT."],
        matlab="sysd = c2d(ss(A,b,c,0), T); G = sysd.A, h = sysd.B\ncanon(sysd, 'modal')"),
    "ctrb_obsv": dict(
        intuition="Controllable: the input can push the state anywhere. Observable: from the output you can reconstruct where the state started. "
                  "A pole-zero cancellation in G(z) hides a mode — it becomes uncontrollable or unobservable.",
        visual=None, visual_caption="",
        math=r"""$Q_C = [h\ \ Gh\ \cdots\ G^{n-1}h]$, controllable ⇔ rank $Q_C = n$.
$Q_O = \begin{bmatrix}c^T\\c^TG\\\vdots\\c^TG^{n-1}\end{bmatrix}$, observable ⇔ rank $Q_O = n$ (formula sheet misprints row 2 as $c^TGh$).
Stabilisable: uncontrollable modes stable. Detectable: unobservable (unweighted) modes stable.""",
        worked=f"""**Exam 2017 P4a/b:** $G = {fmat(_G17)}$, $h = [0, 0, 1]^T$: $Q_C = {fmat(np.column_stack([_h17, _G17 @ _h17, _G17 @ _G17 @ _h17]))}$ — triangular with unit anti-diagonal ⇒ rank 3, controllable (companion form is always controllable).
With $m = x_1$: $c^T = [1, 0, 0]$ ⇒ $Q_O = I$ ⇒ observable.""",
        pitfalls=["Give the rank/determinant explicitly, not just 'yes'.", "Use the MEASURED output (m) for observability, not y."],
        matlab="rank(ctrb(G,h)), rank(obsv(G,[1 0 0]))"),
    "pole_placement": dict(
        intuition="Feeding back all states lets you put ALL closed-loop poles wherever you want (if controllable). K_w fixes the steady-state gain, but only "
                  "an integrator on the control error makes the zero error robust against disturbances and model errors.",
        visual=None, visual_caption="",
        math=r"""$u = -k^Tx + K_ww$: $\det(zI - G + hk^T) = \prod(z - \lambda_i)$; Ackermann $k^T = [0\cdots1]Q_C^{-1}P(G)$; $K_w = \frac{1}{c^T(I - G + hk^T)^{-1}h}$.
**Integral action:** $v(k) = v(k-1) + w(k) - y(k)$, $u = -k^Tx + Kv$,
$\hat G = \begin{bmatrix}G&0\\-c^TG&1\end{bmatrix}$, $\hat h = \begin{bmatrix}h\\-c^Th\end{bmatrix}$, $\hat k^T = [k^T, -K]$ (Ackermann with n + 1 poles).""",
        worked=f"""**Book Ex. 6.1:** $G = \\begin{{bmatrix}}0&1\\\\-0.16&-1\\end{{bmatrix}}$, poles $0.5 \\pm j0.5$: $P = z^2 + (1+K_2)z + 0.16 + K_1 = z^2 - z + 0.5$ ⇒ $k^T = {fvec(_k61)}$, $K_w = {fnum(_kw61)}$.

**Exam 2017 P4a (5 P, 0 P in the real exam):** plant above with $c^T = [0.5, 1, 0]$, poles $0.5\\pm j0.5, 0.25, 0.2$:
$\\hat G = {fmat(_Gh17)}$, $\\hat h = {fvec(_hh17)}^T$ ⇒ $\\hat k^T = {fvec(_kh17)}$ ⇒ $k^T = {fvec(_kh17[:3])}$, $K = {fnum(-_kh17[3])}$.""",
        pitfalls=["Use acker() for repeated poles (place() fails).", "Last row of Ĝ is −cᵀG (not −cᵀ).", "K = −(last entry of k̂ᵀ)."],
        matlab="Gh = [G zeros(3,1); -c*G 1]; hh = [h; -c*h];\nkh = acker(Gh, hh, [0.5+0.5i 0.5-0.5i 0.25 0.2]);\nk = kh(1:3), K = -kh(4)"),
    "observers": dict(
        intuition="Run a copy of the plant model in the computer, feed it the same input, and nudge it with the measurement error m − Cx̂. "
                  "The nudge gain P sets how fast the estimation error dies out — make it faster than the controller.",
        visual=None, visual_caption="",
        math=r"""**Predictive:** $\hat x(k+1) = G\hat x + hu + P[m(k) - C^*\hat x(k)]$, error matrix $G - PC^*$.
**Current:** $\hat x(k+1) = G\hat x + hu + P[m(k+1) - C^*G\hat x(k) - C^*hu(k)]$, error matrix $G - PC^*G$.
**Minimum-order** (measure $x_a$): $e(k+1) = (G_{bb} - PG_{ab})e(k)$; $\hat\eta(k+1) = (G_{bb}-PG_{ab})\hat\eta + [(G_{bb}-PG_{ab})P + G_{ba} - PG_{aa}]m + (h_b - Ph_a)u$, $\hat x_b = \hat\eta + Pm$.
Duality: $P^T$ = acker$(G^T, C^{*T}, \text{poles})$.""",
        worked=f"""Same plant as Ex. 6.1, $m = y = [1, 1]x$, observer poles 0.2, 0.2:
- predictive (Ex. 6.4): $p = {fvec(_p64)}$
- current (Ex. 6.5): $p = {fvec(_p65)}$
- minimum-order (Ex. 6.6, double integrator T = 0.2, dead-beat): $P = 5$, $\\hat\\eta(k+1) = -5y(k) + 0.1u(k)$.

**Exam 2017 P4b:** $m = x_1$, poles 0.1 (triple): $p = {fvec(_p17)}$.""",
        pitfalls=["Predictive vs current: which measurement, which error matrix.", "Observer poles faster than controller poles — and SAY so (2017 asked for a statement)."],
        matlab="p = acker(G', c', [0.2 0.2])'       % predictive\npc = acker(G', (c*G)', [0.2 0.2])'  % current"),
    "lqr": dict(
        intuition="Instead of choosing poles, choose what you care about: state error (Q) vs control effort (R). The Riccati equation finds the best "
                  "constant feedback. It is only guaranteed stable if every unstable mode can be influenced (stabilisable) and is penalised (detectable).",
        visual=None, visual_caption="",
        math=r"""$V = \frac12\sum(x^TQx + u^TRu)$; ARE $S = Q + G^TSG - G^TSH(R + H^TSH)^{-1}H^TSG$; $u = -(R+H^TSH)^{-1}H^TSGx$.
Finite horizon: $S(k) = Q + G^T[S(k+1) - S(k+1)HR_s^{-1}H^TS(k+1)]G$, $S(N+1) = L$.
Scalar: $b^2s^2 + (r(1-a^2) - qb^2)s - qr = 0$; $r\to\infty$: unstable pole $a \to 1/a$; $q\to\infty$: pole → 0.
Stability needs **(G, H) stabilisable and [G, Q] detectable**.""",
        worked=f"""**Exercise 7.5:** $G = \\begin{{bmatrix}}1&0.5\\\\0&1\\end{{bmatrix}}$, $h = [0.125, 0.5]^T$, $Q = I$, $R = 1$ ⇒ `dlqr` ⇒ $k^T = {fvec(_K75.ravel())}$, $K_w = 0.6514$.
**Book Ex. 7.1:** $S = \\begin{{bmatrix}}9.4869 & 2.4710\\\\2.4710 & 1.9741\\end{{bmatrix}}$ from the generalised eigenvalue problem.
**Exam 2016 P4e (4 P, 2/4):** LQR designed for the plain plant although the AUGMENTED plant (with integrator) was required.""",
        pitfalls=["Design dlqr on the augmented system when integral action is asked.", "Theory answer must name the matrices: (G,H) stabilisable, [G,Q] detectable."],
        matlab="[k, S, e] = dlqr(G, H, Q, R)   % e = closed-loop poles\n% lecture_material/Ex_7_4_LQR_multitors_discr.m (modal weighting)"),
    "fb_lin": dict(
        intuition="Some nonlinear systems can be made EXACTLY linear by a clever change of coordinates and by computing the input that cancels the "
                  "nonlinearity — then any linear design works globally. The relative degree says after how many steps the input shows up in the output.",
        visual=None, visual_caption="",
        math=r"""$x(k+1) = f(x, u)$, $y = h(x)$; composition $h\circ f^j$. Relative degree δ: $\frac{\partial}{\partial u(k)}h\circ f^j = 0$ for $j < \delta$, $\ne 0$ for $j = \delta$.
Coordinates $\xi_j = h\circ f_0^{j-1}(x)$, $j = 1..\delta$; artificial input $v = h\circ f^\delta(\cdot, u)$ ⇒ delay chain $\xi_\delta(k+1) = v(k)$, $y = \xi_1$.
Control: dead-beat $v = w$ ⇒ $y(k+\delta) = w(k)$; MFC; pole placement.""",
        worked="""**Book Ex. 8.1 (tank):** $h(k+1) = h + \\frac{T_s}{A(h)}(u - a\\sqrt{2gh})$; choose $u = \\frac{A(h)}{T_s}(\\nu - h) + a\\sqrt{2gh}$ ⇒ $h(k+1) = \\nu(k)$ (linear!), then $\\nu$ from a first-order filter of $h_d$.
**Book Ex. 8.2:** $G(z) = \\frac{z-0.8}{z^2+z+0.5}$, $c^Tb = 1 \\ne 0$ ⇒ δ = 1 (= pole excess).""",
        pitfalls=["Say WHAT δ is (definition), not only what linearisation is (2017 grader: 'what is the rel. degree?').", "Internal dynamics η must be stable."],
        matlab=""),
}
