"""Chapters 5 & 6 generators: state-space models, controllability/observability, pole placement,
integral action, predictive / current / minimum-order observers.

Patterns: exam 2017 Problem 4 (15 P: controllability, state feedback with integration of the control error,
observability with m = x1, predictive observer), exam 2016 Problem 4c/d/h, book Ex. 5.2–6.6, exercise book 5.x/6.x.
"""
from __future__ import annotations

import math

import numpy as np

from .. import plots
from ..mathutil import (pp2_steps, acker, augment_integral, c2d_ss, char_poly_from_poles, ctrb, current_observer_gain, fcol, fmat,
                        fnum, fvec, kw_gain, obsv, poly_z_tex, predictive_observer_gain, simulate_ss, ss_to_tf_zinv)
from .base import Misc, Part, Problem


def _c(rng, xs):
    return xs[int(rng.integers(len(xs)))]


POLE_SETS = [
    ([0.5 + 0.5j, 0.5 - 0.5j], "z_{1,2} = 0.5 \\pm j0.5"),
    ([0.5 + 0.3j, 0.5 - 0.3j], "z_{1,2} = 0.5 \\pm j0.3"),
    ([0.6 + 0.4j, 0.6 - 0.4j], "z_{1,2} = 0.6 \\pm j0.4"),
    ([0.2, 0.2], "z_{1,2} = 0.2"),
    ([0.0, 0.0], "z_{1,2} = 0 \\text{ (dead-beat)}"),
    ([0.5, 0.3], "z_1 = 0.5,\\ z_2 = 0.3"),
]


def _plant2(rng, difficulty):
    """Nice 2x2 discrete plants used in the book / exercise book."""
    choices = [
        (np.array([[0, 1], [-0.16, -1]]), np.array([0, 1.0]), np.array([1, 1.0]), "Book Ex. 6.1/6.4/6.5"),
        (np.array([[0, 1], [-1.5, 1.5]]), np.array([0, 1.0]), np.array([0.5, 0.5]), "Exercise book 6.1 (unstable)"),
        (np.array([[1, 0.5], [0, 1]]), np.array([0.125, 0.5]), np.array([1, 0.0]), "Exercise book 6.3/6.11 (double integrator)"),
        (np.array([[0, 1], [0, -0.5]]), np.array([1, 1.0]), np.array([1, 1.0]), "Exercise book 6.12"),
        (np.array([[1, 0.2], [0, 1]]), np.array([0.02, 0.2]), np.array([1, 0.0]), "Book Ex. 6.6 (double integrator, T=0.2)"),
        (np.array([[1, 0.1813], [0, 0.8187]]), np.array([0.01873, 0.1813]), np.array([1, 0.0]), "Exercise book 6.4/6.10"),
        (np.array([[0, 1], [-0.5, 1]]), np.array([1, 1.0]), np.array([0, 1.0]), "Exercise book 7.1"),
    ]
    if difficulty == 1:
        a0 = float(_c(rng, [0.16, -0.5, 0.24, 0.3, 1.5]))
        a1 = float(_c(rng, [1.0, -1.0, 0.5, -1.5, 0.2]))
        G = np.array([[0, 1], [-a0, -a1]])
        return G, np.array([0, 1.0]), np.array([float(_c(rng, [1.0, 0.5])), float(_c(rng, [1.0, 0.0, 0.5]))]), "companion form"
    return choices[int(rng.integers(len(choices)))]


def _plant3(rng):
    rows = [[0.315, -1.43, 2.1], [0.4, -1.7, 2.3], [-0.12, -0.01, 1.0], [0.06, -0.47, 1.2]]
    r = _c(rng, rows)
    G = np.array([[0, 1, 0], [0, 0, 1], r], dtype=float)
    c = np.array(_c(rng, [[0.5, 1, 0], [0.4, 1, 0], [1, 0, 0]]), dtype=float)
    return G, np.array([0, 0, 1.0]), c, "companion (Exam 2017 P4 / Exercise book 6.2 / Book Ex. 6.3)"


# ----------------------------------------------------------------- canonical
def ss_canonical(rng, difficulty, seed):
    n = 2 if difficulty == 1 else 3
    roots = list(rng.choice([1.0, 0.8, 0.5, -0.5, 0.2, 0.6, 0.4], size=n, replace=False))
    a = list(np.round(np.real(np.poly(roots)), 4))  # [1, a1, ..., an]
    b0 = float(_c(rng, [0.0, 0.0, 1.0])) if difficulty == 3 else 0.0
    bs = [float(_c(rng, [1.0, 0.5, 2.0])), float(_c(rng, [0.4, 5.0, -0.5, 0.0]))] + ([0.0] if n == 3 else [])
    b = [b0] + bs[:n]
    last_row = [-a[n - i] for i in range(n)]  # [-a_n, ..., -a_1]
    cT = [b[n - i] - a[n - i] * b0 for i in range(n)]
    num_tex = " + ".join(t for t in [fnum(b0) if b0 else ""] + [f"{fnum(b[i])}z^{{-{i}}}" for i in range(1, n + 1) if b[i]] if t).replace("+ -", "- ")
    den_tex = "1 " + " ".join(f"{'+' if a[i] >= 0 else '-'} {fnum(abs(a[i]))}z^{{-{i}}}" for i in range(1, n + 1) if abs(a[i]) > 1e-12)
    stmt = f"$$G(z) = \\dfrac{{{num_tex}}}{{{den_tex}}}$$\n\nWrite the plant in **controllability canonical form** (formula sheet p. 18)."
    parts = [
        Part("row", f"Last row of $G$: $[-a_{n}, \\dots, -a_1]$ ({n} values)", "vec", last_row, points=1.5, placeholder=f"{n} numbers",
             explain="Companion structure: shift chain x_i(k+1) = x_{i+1}(k), last row carries the negated denominator coefficients in reverse order."),
        Part("c", f"$c^T = [b_{n} - a_{n}b_0, \\dots, b_1 - a_1b_0]$ ({n} values)", "vec", cT, points=1.5, placeholder=f"{n} numbers"),
        Part("d", "Feedthrough $d = b_0$", "num", b0, points=0.5),
    ]
    G = np.vstack([np.hstack([np.zeros((n - 1, 1)), np.eye(n - 1)]), np.array(last_row)])
    sol = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol([0] * (n - 1) + [1])}u(k),\\quad y(k) = {fvec(cT)}\\,x(k) + {fnum(b0)}u(k)$$\n\n"
           "Check (Book Ex. 5.2): (z⁻¹+5z⁻²)/(1+4z⁻¹+3z⁻²) → last row [−3, −4], cᵀ = [5, 1].")
    parts[0].steps = [f"Denominator coefficients (z⁻¹ form): $a_1..a_{n} = {fvec(a[1:])}$.",
                      f"Last row = minus them in REVERSE order: $[-a_{n}, \\dots, -a_1] = {fvec(last_row)}$; the rows above are a shifted identity."]
    parts[1].steps = [f"Numerator coefficients $b_0..b_{n} = {fvec(b)}$.",
                      f"cᵀ = [b_n − a_n b₀, …, b₁ − a₁b₀] = {fvec(cT)} (with b₀ = {fnum(b0)})."]
    parts[2].steps = [f"d = b₀ = {fnum(b0)} (direct feed-through, 0 if the numerator starts with z⁻¹)."]
    return Problem("ss_canonical", "ss_models", "Controllability canonical form", difficulty, seed, stmt, parts, sol,
                   f"num = [{' '.join(fnum(x) for x in b)}]; den = [{' '.join(fnum(x) for x in a)}];\n[A,B,C,D] = tf2ss(num, den)   % MATLAB orders states in reverse (top row = -a)!",
                   source="Book Sec. 5.2.1, Ex. 5.2; Exercise book 5.1", remedy="Last row −a_n … −a₁; cᵀ = b_n … b₁ (b₀ = 0).")


def ss_jordan(rng, difficulty, seed):
    l1, l2 = sorted(rng.choice([0.9, 0.5, -0.5, 0.2, -1.0, -3.0, 0.8], size=2, replace=False), reverse=True)
    n1 = float(_c(rng, [1.0, 2.0]))
    n0 = float(_c(rng, [5.0, 0.4, -1.0, 1.0]))
    N = lambda z: n1 * z + n0  # noqa: E731
    c1 = N(l1) / (l1 - l2)
    c2 = N(l2) / (l2 - l1)
    stmt = (f"$$G(z) = \\dfrac{{{fnum(n1)}z {'+' if n0 >= 0 else '-'} {fnum(abs(n0))}}}{{(z {'-' if l1 >= 0 else '+'} {fnum(abs(l1))})(z {'-' if l2 >= 0 else '+'} {fnum(abs(l2))})}}$$\n\n"
            "Find the **Jordan canonical form** with $h = [1, 1]^T$, ordering $\\lambda_1 > \\lambda_2$.")
    parts = [Part("lam", "$[\\lambda_1, \\lambda_2]$", "vec", [l1, l2], points=1, placeholder="2 numbers"),
             Part("c", "$c^T = [c_1, c_2]$", "vec", [c1, c2], points=2, placeholder="2 numbers",
                  explain="Partial fractions $G(z) = \\sum c_i/(z-\\lambda_i)$; each term is $x_i(k+1) = \\lambda_ix_i(k) + u(k)$.")]
    sol = f"$c_1 = N(\\lambda_1)/(\\lambda_1-\\lambda_2) = {fnum(c1)}$, $c_2 = N(\\lambda_2)/(\\lambda_2-\\lambda_1) = {fnum(c2)}$ (Book Ex. 5.3: (z+5)/((z+1)(z+3)) → cᵀ = [2, −1])."
    return Problem("ss_jordan", "ss_models", "Jordan canonical form", difficulty, seed, stmt, parts, sol,
                   "[r, p] = residue(num, den)   % c_i = r, lambda_i = p\n% or: canon(ss(tf(num,den,T)), 'modal')",
                   source="Book Ex. 5.3, 5.4; Exercise book 5.1", remedy="Jordan form = partial fractions of G(z) (not G(z)/z!).")


def ss_discretize(rng, difficulty, seed):
    T = float(_c(rng, [0.1, 0.2, 0.5, 1.0]))
    kind = "diag" if difficulty == 1 else _c(rng, ["integ", "companion", "diag"])
    if kind == "diag":
        l1, l2 = rng.choice([0.0, -1.0, -0.5, -2.0, 5.0, -5.0], size=2, replace=False)
        A = np.diag([float(l1), float(l2)])
        b = np.array([1.0, 1.0])
        desc = f"\\dot x = {fmat(A)}x + {fcol(b)}u"
    elif kind == "integ":
        a = float(_c(rng, [1.0, 2.0, 0.5]))
        A = np.array([[0, 1.0], [0, -a]])
        b = np.array([0, 1.0])
        desc = f"\\dot x = {fmat(A)}x + {fcol(b)}u \\quad (G_P = 1/(s(s+{fnum(a)})))"
    else:
        p1, p2 = _c(rng, [(1.0, 2.0), (1.0, 3.0), (2.0, 4.0)])
        A = np.array([[0, 1.0], [-p1 * p2, -(p1 + p2)]])
        b = np.array([0, 1.0])
        desc = f"\\dot x = {fmat(A)}x + {fcol(b)}u"
    G, h = c2d_ss(A, b, T)
    h = h.ravel()
    Ge = np.eye(2) + A * T
    he = b * T
    stmt = f"Discretise $${desc}$$ exactly (ZOH) with $T = {fnum(T)}$ s: $G = e^{{AT}}$, $h = \\int_0^T e^{{A\\mu}}d\\mu\\, b$."
    parts = [Part("G", "$G$ row-wise $[g_{11}, g_{12}, g_{21}, g_{22}]$", "vec", list(G.ravel()), points=2, placeholder="4 numbers",
                  misconceptions=[Misc(list(Ge.ravel()), "c2d_euler", "G ≈ I + AT is the Euler approximation, not e^{AT}.")]),
             Part("h", "$h$", "vec", list(h), points=2, placeholder="2 numbers",
                  misconceptions=[Misc(list(he), "c2d_euler", "h ≈ T·b is the Euler approximation.")])]
    eig = np.linalg.eigvals(A)
    sol = (f"Eigenvalues of A: {', '.join(fnum(e) for e in eig)} → eigenvalues of G: $e^{{\\lambda T}}$ = {', '.join(fnum(math.exp(e.real * T)) for e in eig)}.\n\n"
           f"$$G = {fmat(G)},\\qquad h = {fcol(h)}$$\n\n"
           "Methods: $G = Me^{\\Lambda T}M^{-1}$; $h = A^{-1}(G - I)b$ if A is invertible; otherwise the augmented matrix exponential "
           "$\\exp\\left(\\begin{bmatrix}A & b\\\\0&0\\end{bmatrix}T\\right) = \\begin{bmatrix}G&h\\\\0&1\\end{bmatrix}$ (Theorem 5.1).")
    return Problem("ss_discretize", "ss_models", "Exact discretisation of a state-space model", difficulty, seed, stmt, parts, sol,
                   f"A = {np.array2string(A, separator=' ').replace(chr(10), ';')}; b = [{b[0]}; {b[1]}];\nsysd = c2d(ss(A, b, eye(2), 0), {T});\nG = sysd.A, h = sysd.B",
                   source="Book Sec. 5.3, Ex. 5.5, 5.6; Exercise book 5.2–5.5",
                   remedy="G = e^{AT} (not I + AT); h = A⁻¹(G − I)b.")


def ss_tf(rng, difficulty, seed):
    G, h, c, src = _plant2(rng, max(difficulty, 2))
    num, den = ss_to_tf_zinv(G, h, c)
    num = list(np.round(num, 10))
    stmt = f"$$x(k+1) = {fmat(G)}x(k) + {fcol(h)}u(k),\\quad y(k) = {fvec(c)}x(k)$$\n\nCompute $G_{{PU}}(z) = c^T(zI - G)^{{-1}}h$."
    parts = [Part("den", "Denominator $z^2 + \\alpha_1 z + \\alpha_0$: $[1, \\alpha_1, \\alpha_0]$", "vec", list(den), points=1, placeholder="3 numbers",
                  explain="Denominator = det(zI − G) = characteristic polynomial."),
             Part("num", "Numerator $\\beta_1 z + \\beta_0$: $[\\beta_1, \\beta_0]$", "vec", num[-2:], points=2, placeholder="2 numbers")]
    sol = f"$\\det(zI-G) = {poly_z_tex(den)}$, numerator $= {poly_z_tex(num[-2:])}$ (source: {src})."
    return Problem("ss_tf", "ss_models", "Pulse transfer function from state space", difficulty, seed, stmt, parts, sol,
                   "[num, den] = ss2tf(G, h, c, 0)", source="Book Sec. 5.4.3, Ex. 6.1",
                   remedy="G_PU(z) = cᵀ(zI − G)⁻¹h + d; denominator = det(zI − G).")


# --------------------------------------------------------------- ctrb / obsv
def ctrb_obsv(rng, difficulty, seed):
    if difficulty == 3:
        G, h, c, src = _plant3(rng)
    else:
        variant = _c(rng, ["normal", "unctrb", "unobs", "normal"])
        if variant == "unctrb":
            l1, l2 = _c(rng, [(0.5, 0.8), (1.2, 0.3), (0.9, -0.5)])
            G = np.diag([l1, l2])
            h = np.array([1.0, 0.0]) if rng.random() < 0.5 else np.array([0.0, 1.0])
            c = np.array([1.0, 1.0])
            src = "diagonal system with a zero entry in h"
        elif variant == "unobs":
            G = np.array([[0, 1], [-0.24, 1.0]])  # poles 0.4, 0.6
            h = np.array([0, 1.0])
            c = np.array([-0.4, 1.0])  # zero at 0.4 cancels pole 0.4 -> unobservable
            src = "pole-zero cancellation in cᵀ(zI−G)⁻¹h"
        else:
            G, h, c, src = _plant2(rng, 2)
    n = G.shape[0]
    Qc = ctrb(G, h)
    Qo = obsv(G, c)
    rc = int(np.linalg.matrix_rank(Qc, tol=1e-9))
    ro = int(np.linalg.matrix_rank(Qo, tol=1e-9))
    opts_c = ["completely state controllable", "not completely state controllable"]
    opts_o = ["completely state observable", "not completely state observable"]
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(h)}u(k),\\qquad m(k) = {fvec(c)}x(k)$$\n\nCheck controllability with $u$ and observability with $m$.")
    parts = [
        Part("detc", "$\\det Q_C$, $Q_C = [h,\\ Gh,\\ \\dots]$", "num", float(np.linalg.det(Qc)), points=1, tol_abs=1e-4),
        Part("ctrb", "Controllability", "choice", opts_c[0] if rc == n else opts_c[1], options=opts_c, points=1,
             explain=f"rank Q_C = {rc} (n = {n})."),
        Part("deto", "$\\det Q_O$, $Q_O = [c^T;\\ c^TG;\\ \\dots]$", "num", float(np.linalg.det(Qo)), points=1, tol_abs=1e-4),
        Part("obsv", "Observability", "choice", opts_o[0] if ro == n else opts_o[1], options=opts_o, points=1,
             explain=f"rank Q_O = {ro}. ⚠ Formula sheet p. 19 prints the 2nd row as cᵀGh — correct is cᵀG (Book Theorem 5.3)."),
    ]
    sol = f"$$Q_C = {fmat(Qc)},\\qquad Q_O = {fmat(Qo)}$$\n\nrank $Q_C$ = {rc}, rank $Q_O$ = {ro} (n = {n}). Source: {src}."
    cols = [h]
    for _ in range(n - 1):
        cols.append(G @ cols[-1])
    rws = [c]
    for _ in range(n - 1):
        rws.append(rws[-1] @ G)
    parts[0].steps = [
        "Q_C has the columns h, Gh, G²h, … (each new column = G times the previous one).",
        *[f"Column {i + 1}: " + ("$h$" if i == 0 else f"$G\\cdot$(column {i})") + f" = {fvec(cols[i])}" for i in range(n)],
        f"$Q_C = {fmat(Qc)}$.",
        f"Determinant (MATLAB `det(ctrb(G,h))`; by hand for 2×2: ad − bc) = {fnum(float(np.linalg.det(Qc)))}.",
    ]
    parts[1].steps = [f"det(Q_C) = {fnum(float(np.linalg.det(Qc)))} {'≠ 0 ⇒ full rank n' if rc == n else '= 0 ⇒ rank < n'} ⇒ **{'controllable' if rc == n else 'not controllable'}**. Write the determinant/rank as the reason."]
    parts[2].steps = [
        "Q_O has the ROWS cᵀ, cᵀG, cᵀG², … (each new row = previous row times G). Use the measured signal's vector c.",
        *[f"Row {i + 1}: " + ("$c^T$" if i == 0 else f"(row {i})$\\cdot G$") + f" = {fvec(rws[i])}" for i in range(n)],
        f"$Q_O = {fmat(Qo)}$, det = {fnum(float(np.linalg.det(Qo)))}.",
    ]
    parts[3].steps = [f"det(Q_O) = {fnum(float(np.linalg.det(Qo)))} ⇒ rank {ro} ⇒ **{'observable' if ro == n else 'not observable'}**."]
    return Problem("ctrb_obsv", "ctrb_obsv", "Controllability & observability", difficulty, seed, stmt, parts, sol,
                   "Qc = ctrb(G, h); rank(Qc), det(Qc)\nQo = obsv(G, c); rank(Qo), det(Qo)",
                   source="Pattern: Exam 2017 P4a/b, Exam 2016 P4c; Book Theorems 5.2/5.3",
                   remedy="rank[h Gh … Gⁿ⁻¹h] = n; rank[cᵀ; cᵀG; …] = n.")


# ------------------------------------------------------------ pole placement
def pole_placement(rng, difficulty, seed):
    if difficulty == 3:
        G, h, c, src = _plant3(rng)
        poles, ptex = _c(rng, [([0, 0, 0], "z_{1,2,3} = 0\\ (dead-beat)"), ([0.5 + 0.5j, 0.5 - 0.5j, 0.25], "z_{1,2} = 0.5\\pm j0.5,\\ z_3 = 0.25"),
                               ([0.2, 0.2, 0.2], "z_{1,2,3} = 0.2")])
    else:
        G, h, c, src = _plant2(rng, difficulty)
        poles, ptex = POLE_SETS[int(rng.integers(len(POLE_SETS)))]
    k = acker(G, h, poles)
    n = G.shape[0]
    try:
        Kw = kw_gain(G, h, c, k)
    except Exception:
        Kw = None
    try:
        Kw_ol = 1.0 / float(c @ np.linalg.solve(np.eye(n) - G, h))
    except Exception:
        Kw_ol = None
    alpha = char_poly_from_poles(poles)
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(h)}u(k),\\quad y(k) = {fvec(c)}x(k)$$\n\n"
            f"All states are measurable. Design $u(k) = -k^Tx(k) + K_ww(k)$ such that the closed-loop poles are ${ptex}$ and $y(\\infty) = w$ for a step.")
    parts = [Part("k", f"$k^T$ ({n} values)", "vec", list(k), points=3, placeholder=f"{n} numbers",
                  hint="Compare coefficients of det(zI − G + h kᵀ) with the desired polynomial, or use Ackermann.",
                  explain="Closed-loop matrix G − h kᵀ; its characteristic polynomial must equal Π(z − λᵢ).",
                  misconceptions=[Misc(list(-k), "pp_sign", "You placed the eigenvalues of G + h kᵀ: the law is u = −kᵀx.")])]
    if Kw is not None and np.isfinite(Kw):
        parts.append(Part("Kw", "$K_w$", "num", Kw, points=1.5,
                          explain="$K_w = 1/(c^T[I - G + hk^T]^{-1}h)$ ⇒ $G_W(1) = 1$.",
                          misconceptions=[Misc(Kw_ol, "kw_openloop", "That is 1/G_P(1), the open-loop DC gain inverse — K_w must use the CLOSED loop.")] if Kw_ol is not None and np.isfinite(Kw_ol) else []))
    Gc = G - np.outer(h, k)
    sol = (f"Desired: $P(z) = {poly_z_tex(alpha)}$.\n\n"
           f"Ackermann: $k^T = [0 \\cdots 1]Q_C^{{-1}}P(G)$ with $Q_C = {fmat(ctrb(G, h))}$ ⇒ $k^T = {fvec(k)}$.\n\n"
           f"Closed loop $G - hk^T = {fmat(Gc)}$" + (f", $K_w = {fnum(Kw)}$." if Kw is not None else ".") + f"\n\nSource of plant: {src}.")
    y = simulate_ss(Gc, h * (Kw or 0), c, [1.0] * 15)
    if n == 2:
        st_, _ = pp2_steps(G, h, poles)
        parts[0].steps = ["Check first: controllable? $Q_C = [h, Gh]$, det ≠ 0 ✓ (otherwise poles cannot be placed).",
                          "Closed loop with $u = -k^Tx$: $x(k+1) = (G - hk^T)x(k)$. Its characteristic polynomial must equal the desired one."] + st_
    else:
        parts[0].steps = ["For 3×3 use Ackermann in MATLAB: `k = acker(G, h, p)` with p = desired poles.",
                          f"Desired polynomial: ${poly_z_tex(alpha)}$.",
                          f"Ackermann: $k^T = [0\\ 0\\ 1]\\,Q_C^{{-1}}P(G)$ with $Q_C = {fmat(ctrb(G, h))}$ ⇒ $k^T = {fvec(k)}$.",
                          "Check: `eig(G - h*k)` must return the desired poles."]
    if len(parts) > 1:
        M_ = np.eye(n) - G + np.outer(h, k)
        x_ = np.linalg.solve(M_, h)
        parts[1].steps = [
            "Goal: output = reference in steady state ⇒ closed-loop gain at z = 1 must be 1.",
            f"$M = I - G + hk^T = {fmat(M_)}$.",
            f"Solve $Mx = h$ (i.e. $x = M^{{-1}}h$): $x = {fvec(x_)}$.",
            f"$c^Tx = {fnum(float(c @ x_))}$ ⇒ $K_w = 1/{fnum(float(c @ x_))} = {fnum(Kw)}$.",
        ]
    return Problem("pole_placement", "pole_placement", "State feedback by pole placement + K_w", difficulty, seed, stmt, parts, sol,
                   f"G = {np.array2string(G, separator=' ').replace(chr(10), ';')}; h = {np.array2string(h, separator=';')}; c = {np.array2string(c, separator=' ')};\n"
                   f"p = [{' '.join(fnum(x) for x in poles)}];\nk = acker(G, h, p)       % place() fails for repeated poles\n"
                   "Kw = 1/(c*((eye(size(G))-G+h*k)\\h))\nstep(ss(G-h*k, h*Kw, c, 0, -1))",
                   source="Book Ex. 6.1, 6.2; Exercise book 6.1–6.4, 6.12, 6.13",
                   plot=lambda: plots.step_compare({"y(k)": y}, "Closed-loop reference step"),
                   remedy="det(zI − G + hkᵀ) = desired polynomial; K_w from the closed-loop DC gain.")


def integral_sf(rng, difficulty, seed):
    if difficulty == 1:
        a = float(_c(rng, [1.5, 0.8, 1.2]))
        b = float(_c(rng, [1.0, 0.5, 2.0]))
        G, h, c = np.array([[a]]), np.array([b]), np.array([1.0])
        poles, ptex = _c(rng, [([0.5 + 0.3j, 0.5 - 0.3j], "0.5 \\pm j0.3"), ([0.0, 0.0], "0,\\ 0"), ([0.4, 0.5], "0.4,\\ 0.5")])
        src = "Exercise book 6.9"
    elif difficulty == 2:
        G, h, c, src = _plant2(rng, 2)
        poles, ptex = _c(rng, [([0, 0, 0], "0,0,0\\ (dead-beat)"), ([0.5 + 0.5j, 0.5 - 0.5j, 0.2], "0.5\\pm j0.5,\\ 0.2"),
                               ([0.53 + 0.36j, 0.53 - 0.36j, 0.1], "0.53\\pm j0.36,\\ 0.1")])
    else:
        G, h, c, src = _plant3(rng)
        poles, ptex = _c(rng, [([0.5 + 0.5j, 0.5 - 0.5j, 0.25, 0.2], "0.5\\pm j0.5,\\ 0.25,\\ 0.2"), ([0, 0, 0, 0], "0,0,0,0")])
    n = G.shape[0]
    Gh, hh = augment_integral(G, h, c)
    if np.linalg.matrix_rank(ctrb(Gh, hh)) < n + 1:
        return integral_sf(rng, difficulty, seed)
    kh = acker(Gh, hh, poles)
    k, K = kh[:n], -kh[n]
    wrong = []
    try:
        Gw = np.block([[G, np.zeros((n, 1))], [-c.reshape(1, -1), np.ones((1, 1))]])
        hw = np.concatenate([h, [0.0]])
        if np.linalg.matrix_rank(ctrb(Gw, hw)) == n + 1:
            khw = acker(Gw, hw, poles)
            wrong.append(Misc(list(khw[:n]), "integ_wrong_augment", "These gains come from the augmented model with −cᵀ (instead of −cᵀG) in the last row."))
    except Exception:
        pass
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(h)}u(k),\\quad y(k) = {fvec(c)}x(k)$$\n\n"
            f"Design a **state feedback controller with integration of the control error**, $u(k) = -k^Tx(k) + K\\,v(k)$, "
            f"$v(k) = v(k-1) + w(k) - y(k)$, with closed-loop poles at ${ptex}$.")
    last_row = list((-c.reshape(1, -1) @ G).ravel()) + [1.0]
    parts = [
        Part("row", f"Last row of $\\hat G$ ({n + 1} values)", "vec", last_row, points=1, placeholder=f"{n + 1} numbers",
             explain="$\\hat G = \\begin{bmatrix}G & 0\\\\ -c^TG & 1\\end{bmatrix}$ from $v(k+1) = v(k) + w(k+1) - c^T(Gx(k) + hu(k))$.",
             misconceptions=[Misc(list(-c) + [1.0], "integ_wrong_augment", "The last row is [−cᵀG, 1], not [−cᵀ, 1]: substitute y(k+1) = cᵀx(k+1).")]),
        Part("hlast", "Last entry of $\\hat h$", "num", float(-c @ h), points=0.5, tol_abs=1e-4,
             explain="$\\hat h = [h;\\ -c^Th]$.",
             misconceptions=[Misc(0.0, "integ_wrong_augment", "ĥ's last entry is −cᵀh (it is 0 only if cᵀh = 0).")] if abs(c @ h) > 1e-9 else []),
        Part("k", f"$k^T$ ({n} values)", "vec", list(k), points=2.5, placeholder=f"{n} numbers", misconceptions=wrong,
             hint="Ackermann on (Ĝ, ĥ) with n+1 desired poles gives k̂ᵀ = [kᵀ, −K]."),
        Part("K", "Integrator gain $K$", "num", K, points=1,
             misconceptions=[Misc(-K, "integ_K_sign", "k̂ᵀ = [kᵀ, −K]: K is MINUS the last entry.")]),
    ]
    # simulate
    x = np.zeros(n)
    v = 0.0
    ys, us = [], []
    for _ in range(15):
        y = float(c @ x)
        v = v + 1.0 - y
        u = float(-k @ x + K * v)
        ys.append(y)
        us.append(u)
        x = G @ x + h * u
    sol = (f"$$\\hat G = {fmat(Gh)},\\quad \\hat h = {fcol(hh)}$$\n\n"
           f"Desired polynomial ${poly_z_tex(char_poly_from_poles(poles))}$; Ackermann ⇒ $\\hat k^T = {fvec(kh)}$ ⇒ "
           f"$k^T = {fvec(k)}$, $K = {fnum(K)}$.\n\nCheck: $G_W(1) = 1$ (integrator ⇒ zero steady-state error, also for constant disturbances). Source: {src}.")
    matlab = (f"G = {np.array2string(G, separator=' ').replace(chr(10), ';')}; h = {np.array2string(h, separator=';')}; c = {np.array2string(c, separator=' ')};\n"
              "n = size(G,1);\nGh = [G zeros(n,1); -c*G 1];  hh = [h; -c*h];\n"
              f"kh = acker(Gh, hh, [{' '.join(fnum(x) for x in poles)}]);\nk = kh(1:n), K = -kh(end)\n"
              "% closed loop (states x, v), input w(k+1):\nAcl = [G-h*k, K*h; -c*G+c*h*k, 1-K*c*h];")
    cg = (c.reshape(1, -1) @ G).ravel()
    parts[0].steps = [
        "Extra state v(k) adds up the error: v(k) = v(k−1) + w(k) − y(k). Written one step ahead: v(k+1) = v(k) + w(k+1) − cᵀx(k+1).",
        "Insert x(k+1) = Gx(k) + hu(k): v(k+1) = −cᵀG·x(k) + 1·v(k) − cᵀh·u(k) + w(k+1).",
        f"So the new last row of Ĝ is [−cᵀG, 1]: $c^TG = {fvec(cg)}$ ⇒ row = {fvec(list(-cg) + [1.0])}.",
    ]
    parts[1].steps = [f"Last entry of ĥ is −cᵀh = −({fnum(float(c @ h))}) = {fnum(float(-c @ h))} (coefficient of u in the v-equation)."]
    parts[2].steps = [
        f"$\\hat G = {fmat(Gh)}$, $\\hat h = {fvec(hh)}^T$ (size n + 1 = {n + 1}).",
        f"Desired polynomial with all {n + 1} poles: ${poly_z_tex(char_poly_from_poles(poles))}$.",
        "MATLAB: `kh = acker(Gh, hh, p)` (by hand: coefficient comparison of det(zI − Ĝ + ĥk̂ᵀ)).",
        f"Result $\\hat k^T = {fvec(kh)}$ — the first {n} entries are $k^T = {fvec(k)}$.",
    ]
    parts[3].steps = [f"k̂ᵀ = [kᵀ, −K] ⇒ the last entry {fnum(kh[n])} equals −K ⇒ K = {fnum(K)}.",
                      "Control law: u(k) = −kᵀx(k) + K·v(k)."]
    return Problem("integral_sf", "pole_placement", "State feedback with integration of the control error", difficulty, seed, stmt, parts, sol, matlab,
                   source="Pattern: Exam 2017 P4a (5 P), Exam 2016 P4d/e; Book Ex. 6.3; Exercise book 6.8–6.10",
                   plot=lambda: plots.step_compare({"y(k)": ys, "u(k)": us}, "Reference step with integral action"),
                   remedy="Ĝ = [[G,0],[−cᵀG,1]], ĥ = [h; −cᵀh], k̂ᵀ = [kᵀ, −K].")


# ------------------------------------------------------------------ observers
def pred_observer(rng, difficulty, seed):
    if difficulty == 3:
        G, h, c0, src = _plant3(rng)
        c = np.array([1.0, 0, 0])
        poles, ptex = _c(rng, [([0, 0, 0], "0,0,0"), ([0.1, 0.1, 0.1], "0.1,0.1,0.1"), ([0.2, 0.15, 0.1], "0.2,\\,0.15,\\,0.1")])
    else:
        G, h, c, src = _plant2(rng, max(difficulty, 2))
        poles, ptex = _c(rng, [([0.2, 0.2], "0.2,\\,0.2"), ([0.0, 0.0], "0,\\,0"), ([0.1, 0.3], "0.1,\\,0.3")])
    n = G.shape[0]
    if np.linalg.matrix_rank(obsv(G, c)) < n:
        return pred_observer(rng, difficulty, seed + 1)
    p = predictive_observer_gain(G, c, poles)
    mis = []
    try:
        if np.linalg.matrix_rank(ctrb(G, c)) == n:
            mis.append(Misc(list(acker(G, c, poles)), "obs_not_dual", "You applied Ackermann to (G, c) — the dual problem uses (Gᵀ, c)."))
    except Exception:
        pass
    try:
        mis.append(Misc(list(current_observer_gain(G, c, poles)), "obs_pred_vs_curr", "That is the CURRENT observer gain (error matrix G − p cᵀG)."))
    except Exception:
        pass
    F = G - np.outer(p, c)
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(h)}u(k),\\quad m(k) = {fvec(c)}x(k)$$\n\n"
            f"Design a **predictive observer** $\\hat x(k+1) = G\\hat x(k) + hu(k) + p[m(k) - c^T\\hat x(k)]$ with observer poles at ${ptex}$.")
    parts = [Part("p", f"$p$ ({n} values)", "vec", list(p), points=3, placeholder=f"{n} numbers",
                  hint="det(zI − G + p cᵀ) = desired observer polynomial; duality: pᵀ = acker(Gᵀ, c, poles).",
                  explain="Error dynamics $\\tilde x(k+1) = (G - pc^T)\\tilde x(k)$.", misconceptions=mis),
             Part("F", f"$F = G - pc^T$ row-wise ({n * n} values)", "vec", list(F.ravel()), points=1, placeholder=f"{n * n} numbers")]
    sol = (f"Observability: $Q_O = {fmat(obsv(G, c))}$ (full rank).\n\n$p = {fvec(p)}$, $G - pc^T = {fmat(F)}$ "
           f"(eigenvalues {', '.join(fnum(e, 3) for e in np.linalg.eigvals(F))}).\n\n"
           "Pole choice: observer poles faster (closer to the origin) than the controller poles, e.g. dead-beat or 2–5× faster; "
           f"too fast amplifies measurement noise. Source: {src}.")
    if n == 2:
        st_, _ = pp2_steps(G.T, c, poles, kname="p", what="p\\,c^T")
        parts[0].steps = ["Check observability: $Q_O = [c^T; c^TG]$ must have det ≠ 0 ✓.",
                          "Estimation error obeys $\\tilde x(k+1) = (G - pc^T)\\tilde x(k)$ ⇒ choose p so that $\\det(zI - G + pc^T)$ = desired observer polynomial.",
                          "Trick (duality): $G - pc^T$ has the same eigenvalues as $G^T - c\\,p^T$, which is pole placement for $(G^T, c)$ — same steps as for the controller:"] + st_
    else:
        parts[0].steps = ["Check observability with the measured signal: rank obsv(G, c) = 3 ✓.",
                          "MATLAB (duality): `p = acker(G', c', [observer poles])'`.",
                          f"Result: p = {fvec(p)}. Check: `eig(G - p*c)` returns the observer poles."]
    parts[1].steps = [f"$pc^T$ = column p times row c = {fmat(np.outer(p, c))}.",
                      f"$F = G - pc^T = {fmat(F)}$ (row-wise: {', '.join(fnum(x) for x in F.ravel())})."]
    return Problem("pred_observer", "observers", "Predictive observer design", difficulty, seed, stmt, parts, sol,
                   f"p = acker(G', c', [{' '.join(fnum(x) for x in poles)}])'   % duality\neig(G - p*c)",
                   source="Pattern: Exam 2017 P4b (4 P), Exam 2016 P4h; Book Ex. 6.4; Exercise book 6.11, 6.12",
                   remedy="eig(G − p cᵀ) = observer poles; p = acker(Gᵀ, c, poles)ᵀ.")


def curr_observer(rng, difficulty, seed):
    G, h, c, src = _plant2(rng, max(difficulty, 2))
    if abs(np.linalg.det(G)) < 1e-9 or np.linalg.matrix_rank(obsv(G, c)) < 2:
        G, h, c, src = np.array([[0, 1], [-0.16, -1]]), np.array([0, 1.0]), np.array([1, 1.0]), "Book Ex. 6.5"
    poles, ptex = _c(rng, [([0.2, 0.2], "0.2,\\,0.2"), ([0.0, 0.0], "0,\\,0"), ([0.1, 0.3], "0.1,\\,0.3")])
    p = current_observer_gain(G, c, poles)
    pw = predictive_observer_gain(G, c, poles)
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(h)}u(k),\\quad m(k) = {fvec(c)}x(k)$$\n\n"
            f"Design a **current observer** $\\hat x(k+1) = G\\hat x(k) + hu(k) + p[m(k+1) - c^TG\\hat x(k) - c^Th u(k)]$ with poles ${ptex}$.")
    parts = [Part("p", "$p$", "vec", list(p), points=3, placeholder="2 numbers",
                  explain="Error dynamics $\\tilde x(k+1) = (G - pc^TG)\\tilde x(k)$ — replace cᵀ by cᵀG in the predictive design.",
                  misconceptions=[Misc(list(pw), "obs_pred_vs_curr", "That is the PREDICTIVE observer gain (G − p cᵀ).")])]
    cg = c @ G
    sol = f"$c^TG = {fvec(cg)}$; $\\det(zI - G + p\\,c^TG)$ = desired ⇒ $p = {fvec(p)}$. Source: {src} (Book Ex. 6.5: p = [8.75, −8])."
    st_, _ = pp2_steps(G.T, cg, poles, kname="p", what="p\\,c^TG")
    parts[0].steps = ["Current observer error: $\\tilde x(k+1) = (G - p\\,c^TG)\\tilde x(k)$ — like the predictive one but with the row $c^TG$ instead of $c^T$.",
                      f"Compute $c^TG = {fvec(cg)}$.",
                      "Duality: pole placement for $(G^T, (c^TG)^T)$:"] + st_
    return Problem("curr_observer", "observers", "Current observer design", difficulty, seed, stmt, parts, sol,
                   f"p = acker(G', (c*G)', [{' '.join(fnum(x) for x in poles)}])'\neig(G - p*c*G)",
                   source="Book Sec. 6.4.2, Ex. 6.5; Exercise book 6.11", remedy="Current observer: error matrix G − p cᵀG; uses m(k+1).")


def minorder_observer(rng, difficulty, seed):
    G, h, c, src = _plant2(rng, max(difficulty, 2))
    if abs(G[0, 1]) < 1e-9:
        G, h, src = np.array([[0, 1], [-0.16, -1.0]]), np.array([0, 1.0]), "Exercise book 6.13"
    lam = float(_c(rng, [0.0, 0.2, 0.1, 0.5]))
    Gaa, Gab, Gba, Gbb = G[0, 0], G[0, 1], G[1, 0], G[1, 1]
    ha, hb = h
    P = (Gbb - lam) / Gab
    f1 = Gbb - P * Gab
    f2 = f1 * P + Gba - P * Gaa
    f3 = hb - P * ha
    stmt = (f"$$x(k+1) = {fmat(G)}x(k) + {fcol(h)}u(k)$$\n\nOnly $m(k) = x_1(k)$ is measured. Design a **minimum-order observer** for $x_2$ "
            f"with observer pole $z = {fnum(lam)}$:\n\n$\\hat\\eta(k+1) = f_1\\hat\\eta(k) + f_2\\,m(k) + f_3\\,u(k)$, $\\hat x_2(k) = \\hat\\eta(k) + P\\,m(k)$.")
    parts = [Part("P", "$P$", "num", P, points=1.5, hint="Characteristic equation |z − G_bb + P·G_ab| = 0.",
                  explain="$z - G_{bb} + PG_{ab} = z - \\lambda$ ⇒ $P = (G_{bb} - \\lambda)/G_{ab}$."),
             Part("f", "$[f_1, f_2, f_3]$", "vec", [f1, f2, f3], points=2.5, placeholder="3 numbers",
                  explain="$f_1 = G_{bb}-PG_{ab}$, $f_2 = (G_{bb}-PG_{ab})P + G_{ba} - PG_{aa}$, $f_3 = h_b - Ph_a$.")]
    sol = (f"$G_{{aa}} = {fnum(Gaa)}, G_{{ab}} = {fnum(Gab)}, G_{{ba}} = {fnum(Gba)}, G_{{bb}} = {fnum(Gbb)}$, $h_a = {fnum(ha)}, h_b = {fnum(hb)}$\n\n"
           f"$P = {fnum(P)}$; $\\hat\\eta(k+1) = {fnum(f1)}\\hat\\eta(k) + {fnum(f2)}m(k) + {fnum(f3)}u(k)$; $\\hat x_2 = \\hat\\eta + {fnum(P)}m$.\n\n"
           f"Error: $e(k+1) = (G_{{bb}} - PG_{{ab}})e(k)$. Source: {src}. (Book Ex. 6.6: P = 5, η̂(k+1) = −5y + 0.1u; Exercise 6.13: x̂₂ = −1.2x₁ + η̂.)")
    parts[0].steps = [
        f"Split G with x₁ measured (a) and x₂ unknown (b): $G_{{aa}} = {fnum(Gaa)}$, $G_{{ab}} = {fnum(Gab)}$, $G_{{ba}} = {fnum(Gba)}$, $G_{{bb}} = {fnum(Gbb)}$; $h_a = {fnum(ha)}$, $h_b = {fnum(hb)}$.",
        "Error dynamics $e(k+1) = (G_{bb} - PG_{ab})e(k)$ — a scalar here, so the observer pole IS $G_{bb} - PG_{ab}$.",
        f"Set it equal to the desired pole: ${fnum(Gbb)} - P\\cdot{fnum(Gab)} = {fnum(lam)}$ ⇒ $P = ({fnum(Gbb)} - {fnum(lam)})/{fnum(Gab)} = {fnum(P)}$.",
    ]
    parts[1].steps = [
        f"$f_1 = G_{{bb}} - PG_{{ab}} = {fnum(f1)}$ (the observer pole).",
        f"$f_2 = f_1P + G_{{ba}} - PG_{{aa}} = {fnum(f1)}\\cdot{fnum(P)} + {fnum(Gba)} - {fnum(P)}\\cdot{fnum(Gaa)} = {fnum(f2)}$.",
        f"$f_3 = h_b - Ph_a = {fnum(hb)} - {fnum(P)}\\cdot{fnum(ha)} = {fnum(f3)}$.",
        f"Estimate: $\\hat x_2(k) = \\hat\\eta(k) + {fnum(P)}\\,m(k)$.",
    ]
    return Problem("minorder_observer", "observers", "Minimum-order observer", difficulty, seed, stmt, parts, sol, "",
                   source="Book Sec. 6.4.3, Ex. 6.6; Exercise book 6.13; Homework 8 (WP8)",
                   remedy="Observer for x_b only: error matrix G_bb − P G_ab; then η = x_b − P x_a.")


def observer_pole_choice(rng, difficulty, seed):
    cp = _c(rng, [(0.5, 0.5), (0.6, 0.4), (0.53, 0.36)])
    r = abs(complex(*cp))
    opts = [f"z = {fnum(round(r / 4, 2))} (double) — faster than the controller poles",
            f"z = {fnum(min(0.95, round(r + 0.25, 2)))} (double) — slower than the controller poles",
            "z = 1.1 (double) — outside the unit circle",
            "z = −0.95 (double) — close to −1"]
    parts = [Part("ch", "Most appropriate observer poles?", "choice", opts[0], options=list(rng.permutation(opts)), points=1,
                  explain="Separation principle: the observer error must decay faster than the controlled dynamics, so the estimate converges "
                          "before it is relied upon; typical choice 2–5× faster (smaller |z|), dead-beat possible. Very fast observers amplify noise; "
                          "poles near −1 cause ringing.")]
    return Problem("observer_pole_choice", "observers", "How to choose observer poles", difficulty, seed,
                   f"The state-feedback controller places the closed-loop poles at $z_{{1,2}} = {fnum(cp[0])} \\pm j{fnum(cp[1])}$.", parts,
                   "Observer poles faster than the controller poles (Book Ex. 6.4: controller 0.5±j0.5, observer 0.2, 0.2).", "",
                   source="Exam 2017 P4b ('give a short statement on how you choose your observer poles')",
                   remedy="Observer poles 2–5× faster (closer to the origin) than the controller poles.")


GENERATORS = {
    "ss_canonical": ss_canonical,
    "ss_jordan": ss_jordan,
    "ss_discretize": ss_discretize,
    "ss_tf": ss_tf,
    "ctrb_obsv": ctrb_obsv,
    "pole_placement": pole_placement,
    "integral_sf": integral_sf,
    "pred_observer": pred_observer,
    "curr_observer": curr_observer,
    "minorder_observer": minorder_observer,
    "observer_pole_choice": observer_pole_choice,
}
