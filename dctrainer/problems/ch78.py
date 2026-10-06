"""Chapters 7 & 8 generators: LQR (scalar Riccati, matrix DARE, finite-horizon recursion, weights,
stabilisability/detectability) and feedback linearisation (relative degree).

Patterns: exam 2016 Problem 4 (LQR with integration, Q = I, R = 0.25, observer), theory questions
"prerequisites for a stable LQR" (2016 & 2017), "relative degree" (2017); book Ch. 7, 8; exercise book 7.x.
"""
from __future__ import annotations

import math

import numpy as np

from .. import plots
from ..mathutil import augment_integral, c2d_ss, dare_gain, fcol, fmat, fnum, fvec, kw_gain, simulate_ss
from .base import Misc, Part, Problem


def _c(rng, xs):
    return xs[int(rng.integers(len(xs)))]


def lqr_scalar(rng, difficulty, seed):
    a = float(_c(rng, [0.5, 0.8, 1.5, 2.0, 1.2]))
    b = float(_c(rng, [1.0, 0.5, 2.0]))
    q = float(_c(rng, [1.0, 2.0, 10.0]))
    r = float(_c(rng, [1.0, 0.5, 4.0]))
    # b^2 s^2 + (r(1-a^2) - q b^2) s - q r = 0
    A2, A1, A0 = b * b, r * (1 - a * a) - q * b * b, -q * r
    disc = A1 * A1 - 4 * A2 * A0
    s = (-A1 + math.sqrt(disc)) / (2 * A2)
    s_neg = (-A1 - math.sqrt(disc)) / (2 * A2)
    k = a * b * s / (r + b * b * s)
    pole = a - b * k
    k_neg = a * b * s_neg / (r + b * b * s_neg)
    stmt = (f"Scalar plant $x(k+1) = {fnum(a)}x(k) + {fnum(b)}u(k)$, cost $V = \\sum_{{i=0}}^{{\\infty}}(q\\,x^2 + r\\,u^2)$ with $q = {fnum(q)}$, $r = {fnum(r)}$.\n\n"
            "Solve the algebraic Riccati equation $s = q + a^2\\left(s - \\dfrac{s^2b^2}{r + sb^2}\\right)$ and find $u = -kx$.")
    parts = [
        Part("s", "Riccati solution $s$ (the admissible one)", "num", s, points=2,
             hint="Multiply out: b²s² + (r(1 − a²) − q b²)s − q r = 0, take the positive root.",
             misconceptions=[Misc(s_neg, "lqr_wrong_root", "Negative root — S must be positive (semi)definite.")]),
        Part("k", "$k = \\dfrac{abs}{r + b^2s}$", "num", k, points=1.5,
             misconceptions=[Misc(k_neg, "lqr_wrong_root", "Gain from the wrong Riccati root.")]),
        Part("pole", "Closed-loop pole $a - bk$", "num", pole, points=1,
             explain="Always inside the unit circle for q > 0, r > 0 (stabilisable & detectable scalar system)."),
    ]
    sol = (f"Quadratic: ${fnum(A2)}s^2 {'+' if A1 >= 0 else '-'} {fnum(abs(A1))}s - {fnum(-A0)} = 0$ ⇒ $s = {fnum(s)}$ (other root {fnum(s_neg)} rejected).\n\n"
           f"$k = {fnum(a)}\\cdot{fnum(b)}\\cdot{fnum(s)}/({fnum(r)} + {fnum(b * b)}\\cdot{fnum(s)}) = {fnum(k)}$, pole $= {fnum(pole)}$.\n\n"
           f"Limits (Book 7.4.1): $q/r\\to0$: stable $a$ → pole stays $a$ (u ≡ 0); unstable $a$ → pole mirrored to $1/a = {fnum(1 / a)}$. "
           "$q/r\\to\\infty$: pole → 0 (dead-beat-like, large u).")
    parts[0].steps = [
        f"Riccati (scalar): $s = q + a^2\\left(s - \\dfrac{{s^2b^2}}{{r + sb^2}}\\right)$ with a = {fnum(a)}, b = {fnum(b)}, q = {fnum(q)}, r = {fnum(r)}.",
        "Multiply out (it becomes a quadratic in s): $b^2s^2 + (r(1-a^2) - qb^2)s - qr = 0$.",
        f"Numbers: ${fnum(A2)}s^2 + ({fnum(A1)})s + ({fnum(A0)}) = 0$.",
        f"Quadratic formula: $s = \\dfrac{{-({fnum(A1)}) \\pm \\sqrt{{{fnum(A1)}^2 - 4\\cdot{fnum(A2)}\\cdot({fnum(A0)})}}}}{{2\\cdot{fnum(A2)}}}$ ⇒ {fnum(s)} or {fnum(s_neg)}.",
        f"Take the POSITIVE root: s = {fnum(s)}.",
    ]
    parts[1].steps = [f"$k = \\dfrac{{a\\,b\\,s}}{{r + b^2s}} = \\dfrac{{{fnum(a)}\\cdot{fnum(b)}\\cdot{fnum(s)}}}{{{fnum(r)} + {fnum(b * b)}\\cdot{fnum(s)}}} = {fnum(k)}$."]
    parts[2].steps = [f"Closed loop $x(k+1) = (a - bk)x(k)$ ⇒ pole $= {fnum(a)} - {fnum(b)}\\cdot{fnum(k)} = {fnum(pole)}$ (inside the unit circle ✓)."]
    return Problem("lqr_scalar", "lqr", "Scalar LQR via the algebraic Riccati equation", difficulty, seed, stmt, parts, sol,
                   f"[k, s, e] = dlqr({a}, {b}, {q}, {r})", source="Book Sec. 7.4.1 (7.38)–(7.47)",
                   remedy="Positive root of the scalar ARE; k = abs/(r + b²s).")


def lqr_matrix(rng, difficulty, seed):
    cases = [
        (np.array([[1, 0.5], [0, 1]]), np.array([0.125, 0.5]), np.array([1, 0.0]), "Exercise book 7.5"),
        (np.array([[0, 0], [-0.5, 1]]), np.array([1, 0.0]), np.array([0, 1.0]), "Exercise book 7.2"),
        (np.array([[1, 0.1813], [0, 0.8187]]), np.array([0.01873, 0.1813]), np.array([1, 0.0]), "Exercise book 6.10 plant"),
        (np.array([[0, 1], [-0.16, -1]]), np.array([0, 1.0]), np.array([1, 1.0]), "Book Ex. 6.1 plant"),
    ]
    G, H, c, src = cases[int(rng.integers(len(cases)))]
    q = float(_c(rng, [1.0, 10.0, 100.0]))
    R = float(_c(rng, [1.0, 0.25, 4.0]))
    Q = np.diag([q, 1.0])
    S, K = dare_gain(G, H, Q, R)
    k = K.ravel()
    Kw = kw_gain(G, H, c, k)
    cl = np.linalg.eigvals(G - np.outer(H, k))
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(H)}u(k),\\quad y = {fvec(c)}x$$\n\n"
            f"Infinite-horizon LQR with $Q = {fmat(Q)}$, $R = {fnum(R)}$ (use MATLAB `dlqr` in the open-book part). Then add $K_w$ for unit steady-state gain.")
    parts = [Part("k", "$k^T$", "vec", list(k), points=2, placeholder="2 numbers", tol_rel=0.01),
             Part("rho", "Largest closed-loop pole magnitude", "num", float(max(abs(cl))), points=1),
             Part("Kw", "$K_w$", "num", Kw, points=1)]
    sol = (f"$$S = {fmat(S)},\\quad k^T = (R + H^TSH)^{{-1}}H^TSG = {fvec(k)}$$\n\nClosed-loop poles: {', '.join(fnum(e, 3) for e in cl)}; $K_w = {fnum(Kw)}$. "
           f"Source plant: {src}.\n\nIncreasing $q_{{11}}$ (state weight) ⇒ faster, more aggressive control; increasing R ⇒ smaller inputs, slower response.")
    y = simulate_ss(G - np.outer(H, k), H * Kw, c, [1.0] * 15)
    return Problem("lqr_matrix", "lqr", "LQR design with dlqr + reference gain", difficulty, seed, stmt, parts, sol,
                   f"G = {np.array2string(G, separator=' ').replace(chr(10), ';')}; H = {np.array2string(H, separator=';')}; c = {np.array2string(c, separator=' ')};\n"
                   f"Q = diag([{q} 1]); R = {R};\n[k, S, e] = dlqr(G, H, Q, R)\nKw = 1/(c*((eye(2)-G+H*k)\\H))",
                   source="Exam 2016 P4e–g; Exercise book 7.2, 7.5", plot=lambda: plots.step_compare({"y(k)": y}, "LQR closed-loop step"),
                   remedy="k = (R + HᵀSH)⁻¹HᵀSG with S from the DARE; then K_w as for pole placement.")


def lqr_integral(rng, difficulty, seed):
    """Exam 2016 P4: one-mass oscillator, ZOH, augmented with integrator, LQR with Q = I."""
    m = 1.0
    kk = float(_c(rng, [5.0, 4.0, 2.0]))
    d = float(_c(rng, [0.1, 0.5]))
    Ts = float(_c(rng, [0.1, 0.05]))
    R = float(_c(rng, [0.25, 1.0]))
    A = np.array([[0, 1.0], [-kk / m, -d / m]])
    b = np.array([0, 1.0])
    c = np.array([kk / m, d / m])  # G(s) = (d/m s + k/m)/(s^2 + d/m s + k/m)
    G, h = c2d_ss(A, b, Ts)
    h = h.ravel()
    Gh, hh = augment_integral(G, h, c)
    S, K = dare_gain(Gh, hh, np.eye(3), R)
    kh = K.ravel()
    cl = np.linalg.eigvals(Gh - np.outer(hh, kh))
    stmt = (f"One-mass oscillator $G(s) = \\dfrac{{\\frac{{d}}{{m}}s + \\frac{{k}}{{m}}}}{{s^2 + \\frac{{d}}{{m}}s + \\frac{{k}}{{m}}}}$, "
            f"$m = 1$, $k = {fnum(kk)}$, $d = {fnum(d)}$, ZOH with $T_s = {fnum(Ts)}$ s. Use the state basis "
            f"$x = [x_1, x_2]^T$ with $\\dot x = {fmat(A)}x + {fcol(b)}u$, $y = {fvec(c)}x$.\n\n"
            f"Extend with integration of the control error and design an LQR with $\\hat Q = I_3$, $R = {fnum(R)}$ for the **augmented** system.")
    parts = [Part("G", "Discrete $G$ row-wise", "vec", list(G.ravel()), points=1, placeholder="4 numbers"),
             Part("kh", "$\\hat k^T = [k^T, -K]$ (3 values)", "vec", list(kh), points=3, tol_rel=0.02, placeholder="3 numbers",
                  hint="dlqr on (Ĝ, ĥ) with Ĝ = [[G,0],[−cᵀG,1]], ĥ = [h; −cᵀh].",
                  misconceptions=[Misc(list(dare_gain(G, h, np.eye(2), R)[1].ravel()) + [0.0], "integ_wrong_augment",
                                       "That looks like an LQR for the NON-augmented plant (grader 2016: 'not designed for augmented plant!').")]),
             Part("rho", "Largest closed-loop pole magnitude", "num", float(max(abs(cl))), points=1)]
    w_n = math.sqrt(kk)
    sol = (f"$G = {fmat(G)}$, $h = {fcol(h)}$\n\n$\\hat G = {fmat(Gh)}$, $\\hat h = {fcol(hh)}$\n\n$\\hat k^T = {fvec(kh)}$ ⇒ $K = {fnum(-kh[-1])}$.\n\n"
           f"Sampling time check: oscillation period $2\\pi/\\omega_d \\approx {fnum(2 * math.pi / w_n)}$ s ⇒ $T_s \\le 0.125T_2 = {fnum(0.125 * 2 * math.pi / w_n)}$ s.\n\n"
           "Increase R if |u| is too large (2016 P4g: |u| < 1.2).")
    return Problem("lqr_integral", "lqr", "LQR with integral action (Exam 2016 P4 pattern)", difficulty, seed, stmt, parts, sol,
                   f"m=1; k={kk}; d={d}; Ts={Ts};\nsys = ss([0 1; -k/m -d/m], [0;1], [k/m d/m], 0);\nsd = c2d(sys, Ts); G = sd.A; h = sd.B; c = sd.C;\n"
                   f"Gh = [G zeros(2,1); -c*G 1]; hh = [h; -c*h];\n[kh, S, e] = dlqr(Gh, hh, eye(3), {R})\nk = kh(1:2), K = -kh(3)",
                   source="Pattern: Exam 2016 Problem 4 (16 P)", remedy="Augment first, then dlqr on the augmented system.")


def riccati_step(rng, difficulty, seed):
    G = np.array([[0, 1], [-0.5, 1.0]])
    H = np.array([1.0, 1.0])
    Lw = float(_c(rng, [1.0, 2.0]))
    L = Lw * np.eye(2)
    Q = np.eye(2)
    R = float(_c(rng, [1.0, 2.0]))
    Rs = R + H @ L @ H
    k = (H @ L @ G) / Rs
    S = Q + G.T @ (L - np.outer(L @ H, H @ L) / Rs) @ G
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(H)}u(k)$$ finite-horizon cost with $Q = I$, $R = {fnum(R)}$, terminal weight $L = {fnum(Lw)}I$. "
            "Compute ONE backward step of the Riccati recursion from $S(N+1) = L$.")
    parts = [Part("Rs", "$R_s = R + H^TS(N+1)H$", "num", float(Rs), points=1),
             Part("k", "$k^T(N) = R_s^{-1}H^TS(N+1)G$", "vec", list(k), points=2, placeholder="2 numbers"),
             Part("S", "$S(N)$ row-wise", "vec", list(S.ravel()), points=2, placeholder="4 numbers")]
    sol = (f"$R_s = {fnum(Rs)}$, $k^T(N) = {fvec(k)}$ (control law $u = -k^Tx$; ⚠ the formula sheet omits this minus sign), $S(N) = {fmat(S)}$.\n\n"
           "Exercise book 7.1 (L = I, R = 1): k(7) = [−0.1667, 0.6667], S(7) = [[1.1667, −0.1667], [−0.1667, 1.6667]]. "
           "Iterating backwards the gains converge to the stationary LQR gain.")
    return Problem("riccati_step", "lqr", "Riccati recursion (finite horizon)", difficulty, seed, stmt, parts, sol, "",
                   source="Book Sec. 7.2; Exercise book 7.1", remedy="S(k) = Q + Gᵀ[S − S H R_s⁻¹ Hᵀ S]G backwards from S(N+1) = L.")


def stab_detect(rng, difficulty, seed):
    l1 = float(_c(rng, [1.5, 0.5, 2.0, 0.8]))
    l2 = float(_c(rng, [1.1, 0.3, 0.9, 1.2]))
    h = np.array(_c(rng, [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]), dtype=float)
    q = np.array(_c(rng, [[1.0, 1.0], [1.0, 0.0], [0.0, 1.0]]), dtype=float)
    lams = [l1, l2]
    stabil = all(abs(lams[i]) < 1 or abs(h[i]) > 0 for i in range(2))
    detect = all(abs(lams[i]) <= 1 or q[i] > 0 for i in range(2))
    yes_no = ["yes", "no"]
    stmt = (f"$$x(k+1) = {fmat(np.diag(lams))}x(k) + {fcol(h)}u(k),\\qquad Q = {fmat(np.diag(q))},\\ R = 1$$")
    parts = [Part("stab", "Is $(G, H)$ stabilisable?", "choice", "yes" if stabil else "no", options=yes_no, points=1,
                  explain="Stabilisable ⇔ every uncontrollable mode is asymptotically stable (Theorem 7.1). Here mode i is uncontrollable iff hᵢ = 0."),
             Part("det", "Is $[G, Q]$ detectable?", "choice", "yes" if detect else "no", options=yes_no, points=1,
                  explain="Detectable ⇔ every unstable mode is seen by the cost: uᵢᵀQuᵢ > 0 (Theorem 7.2); for diagonal G, uᵢ = eᵢ ⇒ Q_ii > 0."),
             Part("lqr", "Is the infinite-horizon LQR closed loop guaranteed to be stable?", "choice", "yes" if (stabil and detect) else "no",
                  options=yes_no, points=1, explain="Needs BOTH stabilisability of (G, H) and detectability of [G, Q] (exam theory 2016/2017).")]
    sol = (f"Modes: λ₁ = {fnum(l1)} ({'controllable' if h[0] else 'uncontrollable'}, Q₁₁ = {fnum(q[0])}), "
           f"λ₂ = {fnum(l2)} ({'controllable' if h[1] else 'uncontrollable'}, Q₂₂ = {fnum(q[1])}).\n\n"
           "Book Ex. 7.2: uncontrollable unstable mode ⇒ Riccati S₂₂ grows without bound. Sec. 7.4.2: x(k+1) = x + u with V = Σu² ⇒ u ≡ 0, unstable (not detectable).")
    parts[0].steps = [
        "Diagonal G ⇒ each state is its own mode; mode i is controllable iff hᵢ ≠ 0.",
        *[f"Mode λ = {fnum(lams[i])}: h = {fnum(h[i])} ⇒ {'controllable' if h[i] else 'UNcontrollable'}" + ("" if h[i] else f", |λ| {'< 1 (stable, OK)' if abs(lams[i]) < 1 else '≥ 1 (unstable ✗)'}") for i in range(2)],
        f"Stabilisable ⇔ every uncontrollable mode is stable ⇒ **{'yes' if stabil else 'no'}**.",
    ]
    parts[1].steps = [
        "Detectable ⇔ every UNSTABLE mode (|λ| > 1) is weighted in Q (Q_ii > 0 for diagonal G).",
        *[f"Mode λ = {fnum(lams[i])}: " + (f"unstable, Q = {fnum(q[i])} ⇒ {'seen ✓' if q[i] > 0 else 'not seen ✗'}" if abs(lams[i]) > 1 else "stable ⇒ no condition") for i in range(2)],
        f"⇒ **{'yes' if detect else 'no'}**.",
    ]
    parts[2].steps = ["LQR is guaranteed stable only if BOTH hold.", f"⇒ **{'yes' if (stabil and detect) else 'no'}**."]
    return Problem("stab_detect", "lqr", "Stabilisability & detectability (LQR prerequisites)", difficulty, seed, stmt, parts, sol, "",
                   source="Exam theory 2016 Th.h, 2017 Th.b; Book Theorems 7.1, 7.2, Ex. 7.2",
                   remedy="LQR stable ⇔ (G,H) stabilisable AND [G,Q] detectable.")


def rel_degree(rng, difficulty, seed):
    n = 3 if difficulty > 1 else 2
    delta = int(_c(rng, list(range(1, n + 1))))
    # build companion with c chosen so that c^T G^{j} h = 0 for j < delta-1
    a = list(np.round(rng.uniform(-0.8, 0.8, n), 2))
    G = np.vstack([np.hstack([np.zeros((n - 1, 1)), np.eye(n - 1)]), np.array([a])])
    h = np.zeros(n)
    h[-1] = 1.0
    c = np.zeros(n)
    c[n - delta] = 1.0
    if delta < n:
        c[0] = float(_c(rng, [0.5, -0.8, 0.4]))
    vals = [float(c @ np.linalg.matrix_power(G, j) @ h) for j in range(n)]
    delta = next(j + 1 for j, v in enumerate(vals) if abs(v) > 1e-9)
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(h)}u(k),\\quad y(k) = {fvec(c)}x(k)$$\n\n"
            "Determine the relative degree δ (composition operator $h\\circ f^j$, Book Sec. 8.2.2).")
    parts = [Part("delta", "$\\delta$", "num", delta, points=2, tol_abs=0.01, tol_rel=0,
                  hint="y(k+j) = cᵀGʲx(k) + Σ cᵀGⁱh u(…): find the first j with ∂y(k+j)/∂u(k) = cᵀG^{j−1}h ≠ 0.",
                  explain=f"$c^TG^{{j-1}}h$ for j = 1..{n}: {', '.join(fnum(v) for v in vals)} → first non-zero at j = {delta}.")]
    sol = (f"$c^Th = {fnum(vals[0])}$" + "".join(f", $c^TG^{j}h = {fnum(vals[j])}$" for j in range(1, n)) +
           f" ⇒ δ = {delta}: the input u(k) first influences y(k+{delta}). Interpretation: δ future output samples can be predicted "
           "without knowing future inputs (Book remark after (8.12)); for linear systems δ = pole excess of G(z).")
    parts[0].steps = [
        "y(k+j) depends on u(k) through the number $c^TG^{j-1}h$ (how strongly the input reaches the output after j steps).",
        *[f"j = {j + 1}: $c^TG^{{{j}}}h = {fnum(v)}$ {'≠ 0 ⇒ stop' if abs(v) > 1e-9 else '= 0 ⇒ continue'}" for j, v in enumerate(vals[:delta])],
        f"δ = {delta}: the input first appears in the output after {delta} step(s).",
    ]
    return Problem("rel_degree", "fb_lin", "Relative degree", difficulty, seed, stmt, parts, sol, "",
                   source="Exam 2017 Th.f; Book Sec. 8.2.2, Ex. 8.2", remedy="δ = first j with cᵀG^{j−1}h ≠ 0 (= pole excess).")


GENERATORS = {
    "lqr_scalar": lqr_scalar,
    "lqr_matrix": lqr_matrix,
    "lqr_integral": lqr_integral,
    "riccati_step": riccati_step,
    "stab_detect": stab_detect,
    "rel_degree": rel_degree,
}
