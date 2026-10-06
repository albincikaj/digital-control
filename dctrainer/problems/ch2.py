"""Chapter 2 generators: z-transform, inverse z-transform, difference equations, convolution.

Patterns: exam 2017 Problem 1 (signal → U(z), Y = G U, FVT, difference equation, y(k)),
exam 2016 Problem 1 (inverse z-transform via computational method), book Ex. 2.7–2.14,
exercise book Problems 2.1–2.10.
"""
from __future__ import annotations

import numpy as np

from ..mathutil import fnum, fvec, poly_zinv_tex, recursion_steps, series_zinv, series_zinv_step, tf_zinv_tex
from .. import plots
from .base import Misc, Part, Problem


def _c(rng, xs):
    return xs[int(rng.integers(len(xs)))]


# --------------------------------------------------------------------------- 1
def zt_signal_exam(rng, difficulty, seed):
    T = _c(rng, [0.1, 0.2, 0.25, 0.5])
    nseg = 2 if difficulty == 1 else _c(rng, [2, 3])
    pool = [0.5, 1.0, 0.8, 0.2, 1.5, 2.0, 0.4, 0.6]
    levels = list(rng.choice(pool, size=nseg, replace=False))
    lens = [int(_c(rng, [1, 2, 2])) for _ in range(nseg)]
    persist = difficulty == 3 and rng.random() < 0.5
    u = []
    for lv, ln in zip(levels, lens):
        u += [float(lv)] * ln
    N = len(u)
    starts = np.cumsum([0] + lens[:-1])
    a = float(_c(rng, [0.2, 0.4, 0.5, 0.6, 0.8]))
    b = float(_c(rng, [1.0, 0.5, 2.0]))
    # sequences
    n_y = 5
    useq = u + ([levels[-1]] * 10 if persist else [0.0] * 10)
    y = series_zinv([b], [1.0, -a], n_y, u=useq)
    y_wrong = series_zinv([b], [1.0, a], n_y, u=useq)
    wrong_samples = []
    for k in range(N + (1 if not persist else 0)):
        if k in starts:
            i = list(starts).index(k)
            wrong_samples.append(0.0 if i == 0 else float(levels[i - 1]))
        elif k == N:
            wrong_samples.append(float(levels[-1]))
        else:
            wrong_samples.append(useq[k])
    G1 = b / (1 - a)
    if persist:
        final = levels[-1] * G1
    else:
        final = 0.0

    # statement
    pieces = []
    t0 = 0.0
    for lv, ln in zip(levels, lens):
        t1 = t0 + ln * T
        pieces.append(f"{fnum(lv)} \\quad \\text{{for }} {fnum(t0)} \\le t < {fnum(t1)}\\,\\text{{s}}")
        t0 = t1
    if persist:
        pieces[-1] = pieces[-1].split("\\quad")[0] + f"\\quad \\text{{for }} t \\ge {fnum(t0 - lens[-1] * T)}\\,\\text{{s}}"
    else:
        pieces.append(f"0 \\quad \\text{{for }} t \\ge {fnum(t0)}\\,\\text{{s}}")
    stmt = (
        f"The continuous-time signal $u(t)$ is sampled with $T = {fnum(T)}$ s:\n\n"
        f"$$u(t)=\\begin{{cases}}{' \\\\ '.join(pieces)}\\end{{cases}}$$\n\n"
        f"It drives the system $G(z) = \\dfrac{{{fnum(b)}}}{{1 - {fnum(a)}\\,z^{{-1}}}}$, i.e. $Y(z) = G(z)U(z)$."
    )
    n_u = N + 2 if persist else N
    u_ans = useq[:n_u]
    parts = [
        Part("useq", f"(a) Samples $u(kT)$ for $k = 0,\\dots,{n_u - 1}$ (these are the coefficients of $U(z)=\\sum u(kT)z^{{-k}}$)",
             "vec", u_ans, points=2,
             hint="Read the signal at t = kT. At a jump instant take the value right AFTER the jump: x(νT) = x(νT⁺).",
             explain="By definition $U(z)=\\sum_k u(kT)z^{-k}$, so the coefficient of $z^{-k}$ is just the sample $u(kT)$. "
                     "At discontinuities the course convention is the right-hand value.",
             misconceptions=[Misc(wrong_samples[:n_u], "sample_at_jump", "You took the value BEFORE the jump at the switching instants. Convention: x(νT) = x(νT⁺).")] if len(wrong_samples) >= n_u else [],
             placeholder=f"{n_u} numbers, e.g. 0.5, 0.5, 1"),
        Part("final", "(b) Final value $\\lim_{k\\to\\infty} y(kT)$", "num", final, points=2,
             hint="Final value theorem: y(∞) = lim_{z→1}(1 − z⁻¹)Y(z). Is U(z) a finite polynomial or does it contain 1/(1 − z⁻¹)?",
             explain=("U(z) is a finite polynomial, so $(1-z^{-1})G(z)U(z)\\to 0$ for $z\\to 1$ (G stable). The output decays to zero."
                      if not persist else
                      f"The tail $u = {fnum(levels[-1])}$ persists, so $U(z)$ contains ${fnum(levels[-1])}\\,z^{{-{int(starts[-1])}}}/(1-z^{{-1}})$. "
                      f"The FVT gives $y(\\infty) = {fnum(levels[-1])}\\cdot G(1) = {fnum(levels[-1])}\\cdot {fnum(G1)} = {fnum(final)}$."),
             misconceptions=[Misc(sum(u) * G1, "fvt_no_factor", "You evaluated G(1)·U(1) — the factor (1 − z⁻¹) of the final value theorem is missing.")] if not persist else
             [Misc(0.0, "fvt_no_factor", "The input does NOT return to zero here — U(z) contains a step term, so the final value is not 0.")]),
        Part("alpha", "(c) Difference equation $y(k) = \\alpha\\, y(k-1) + \\beta\\, u(k)$: enter $\\alpha$", "num", a, points=0.5,
             hint="Multiply out Y(z)(1 − a z⁻¹) = b U(z), then inverse-transform term by term (z⁻¹ ↔ one-step delay).",
             explain=f"$Y(z)(1-{fnum(a)}z^{{-1}}) = {fnum(b)}U(z) \\Rightarrow y(k) - {fnum(a)}y(k-1) = {fnum(b)}u(k)$.",
             misconceptions=[Misc(-a, "diffeq_sign", "Sign flip: moving −a·y(k−1) to the right-hand side gives +a·y(k−1).")]),
        Part("beta", "(c) … and $\\beta$", "num", b, points=0.5),
        Part("y", f"(d) $y(kT)$ for $k = 0,\\dots,{n_y - 1}$ (computational method / recursion)", "vec", y, points=2,
             hint="Use y(k) = a·y(k−1) + b·u(k) with y(−1) = 0, step by step.",
             explain="Recursion of the difference equation with zero initial conditions (computational method).",
             misconceptions=[Misc(y_wrong, "diffeq_sign", "Your sequence matches the recursion with −a instead of +a: sign error in the difference equation.")],
             placeholder="5 numbers"),
    ]
    s_last = int(starts[-1])
    U_tex = (poly_zinv_tex(u[:s_last]) + f" + \\dfrac{{{fnum(levels[-1])}\\,z^{{-{s_last}}}}}{{1-z^{{-1}}}}") if persist else poly_zinv_tex(u)
    steps = "\n".join(f"- $y({k}) = {fnum(a)}\\cdot {fnum(y[k - 1] if k else 0)} + {fnum(b)}\\cdot {fnum(useq[k])} = {fnum(y[k])}$" for k in range(n_y))
    sol = (
        f"**(a)** Sampling at $t=kT$ (right-hand value at jumps): $u(kT) = {fvec(u_ans)}$, hence "
        f"$U(z) = {U_tex}$.\n\n"
        f"$Y(z) = G(z)U(z) = \\dfrac{{{fnum(b)}\\,U(z)}}{{1-{fnum(a)}z^{{-1}}}}$\n\n"
        f"**(b)** FVT: $y(\\infty) = \\lim_{{z\\to1}}(1-z^{{-1}})Y(z) = {fnum(final)}$ "
        f"({'finite input → (1−z⁻¹)U(z)→0' if not persist else 'step tail survives the (1 − z⁻¹) factor'}). "
        f"Valid because the only pole of $G$ ($z={fnum(a)}$) is inside the unit circle.\n\n"
        f"**(c)** $y(k) - {fnum(a)}\\,y(k-1) = {fnum(b)}\\,u(k)$.\n\n**(d)** Recursion:\n{steps}"
    )
    # ---- step-by-step walkthroughs
    seg_txt = []
    t0 = 0.0
    for lv, ln in zip(levels, lens):
        seg_txt.append(f"{fnum(lv)} from t = {fnum(t0)} s to {fnum(t0 + ln * T)} s")
        t0 += ln * T
    parts[0].steps = [
        f"The sampling instants are $t = kT = 0, {fnum(T)}, {fnum(2 * T)}, \\dots$ (one every T = {fnum(T)} s).",
        f"The signal is {', then '.join(seg_txt)}" + ("" if persist else ", then 0") + ".",
        "At an instant where the signal jumps, take the value AFTER the jump (course convention x(νT) = x(νT⁺)).",
        *[f"$k = {k}$: $t = {fnum(k * T)}$ s ⇒ $u({k}) = {fnum(useq[k])}$" for k in range(n_u)],
        f"So $U(z) = {U_tex}$ — each sample becomes the coefficient of $z^{{-k}}$.",
    ]
    if persist:
        parts[1].steps = [
            f"The input does not return to zero: it stays at {fnum(levels[-1])} forever.",
            "Final value theorem: $y(\\infty) = \\lim_{z\\to1}(1-z^{-1})Y(z)$. For a constant input in the end, this equals (final input) × G(1).",
            f"$G(1) = \\dfrac{{{fnum(b)}}}{{1 - {fnum(a)}}} = {fnum(G1)}$ (put z = 1, so $z^{{-1}} = 1$).",
            f"$y(\\infty) = {fnum(levels[-1])}\\cdot{fnum(G1)} = {fnum(final)}$.",
        ]
    else:
        parts[1].steps = [
            f"Final value theorem: $y(\\infty) = \\lim_{{z\\to1}}(1-z^{{-1}})\\,G(z)\\,U(z)$.",
            f"U(z) is a finite polynomial (the input is 0 after k = {N - 1}), so U(1) is just a finite number.",
            f"G(1) = {fnum(b)}/(1 − {fnum(a)}) = {fnum(G1)} is finite too (its pole z = {fnum(a)} is inside the unit circle — the FVT is allowed).",
            "But the factor $(1 - z^{-1})$ becomes $1 - 1 = 0$ at z = 1. Zero times finite numbers = 0.",
            "Physical sense: the input stops, so the output decays back to 0. ⇒ $y(\\infty) = 0$.",
        ]
    parts[2].steps = [
        f"Start from $Y(z) = \\dfrac{{{fnum(b)}}}{{1 - {fnum(a)}z^{{-1}}}}U(z)$ and multiply both sides by the denominator: "
        f"$Y(z)(1 - {fnum(a)}z^{{-1}}) = {fnum(b)}U(z)$.",
        f"Multiply out: $Y(z) - {fnum(a)}z^{{-1}}Y(z) = {fnum(b)}U(z)$.",
        "Translate back: $Y(z) \\to y(k)$, $z^{-1}Y(z) \\to y(k-1)$ (one step earlier), $U(z) \\to u(k)$.",
        f"$y(k) - {fnum(a)}y(k-1) = {fnum(b)}u(k)$ ⇒ move the old value to the right: $y(k) = {fnum(a)}\\,y(k-1) + {fnum(b)}\\,u(k)$.",
        f"Compare with $y(k) = \\alpha y(k-1) + \\beta u(k)$: $\\alpha = {fnum(a)}$.",
    ]
    parts[3].steps = [f"Same equation: $\\beta$ is the factor in front of $u(k)$: $\\beta = {fnum(b)}$."]
    parts[4].steps = [
        f"Use $y(k) = {fnum(a)}\\,y(k-1) + {fnum(b)}\\,u(k)$ with $y(-1) = 0$ (nothing happened before k = 0).",
        *recursion_steps([b], [1.0, -a], useq, n_y),
        "Write every line like this in the exam — the graders award points for the visible recursion.",
    ]
    matlab = (f"T = {T};\nu = [{' '.join(fnum(x) for x in useq[:8])}];\n"
              f"y = filter({fnum(b)}, [1 -{fnum(a)}], u)   % y(k) = {fnum(a)} y(k-1) + {fnum(b)} u(k)\n"
              f"G = tf({fnum(b)}*[1 0], [1 -{fnum(a)}], T);  % same G(z) in positive powers\n"
              f"dcgain(G)   % G(1)")
    breaks = [0.0] + list(np.cumsum(lens[:-1]) * T) + ([] if persist else [N * T])
    lv_plot = [float(x) for x in levels] + ([] if persist else [0.0])
    return Problem("zt_signal_exam", "zt_basics", "Signal → U(z) → Y(z), FVT, difference equation", difficulty, seed,
                   stmt, parts, sol, matlab, source="Pattern: Exam 2017 Problem 1 (7 P); Exercise book Problems 2.1/2.2",
                   plot=lambda: plots.piecewise_signal(breaks, lv_plot, T, N + 3, samples=useq[:N + 3]),
                   remedy="U(z) coefficients = samples; FVT needs (1 − z⁻¹); recursion signs flip.")


# --------------------------------------------------------------------------- 2
def zt_inverse_comp(rng, difficulty, seed):
    poles = _c(rng, [(0.4, 0.4), (0.5, 0.5), (0.5, 0.2), (0.8, 0.5), (-0.5, 0.5), (0.6, 0.3), (0.3, 0.3)])
    p1, p2 = poles
    a1, a2 = -(p1 + p2), p1 * p2
    if difficulty < 3:
        b = float(_c(rng, [2.0, 1.0, 0.5, -0.5, 3.0]))
        num = [1.0, b]
        num_tex = f"z(z {'+' if b >= 0 else '-'} {fnum(abs(b))})"
    else:
        n1 = float(_c(rng, [1.0, 2.0, 0.5]))
        n0 = float(_c(rng, [0.5, -1.0, 1.0, 0.2]))
        num = [0.0, n1, n0]
        num_tex = f"{fnum(n1)}z {'+' if n0 >= 0 else '-'} {fnum(abs(n0))}"
    den = [1.0, a1, a2]
    den_tex = f"(z - {fnum(p1)})^2" if p1 == p2 else f"(z {'-' if p1 >= 0 else '+'} {fnum(abs(p1))})(z {'-' if p2 >= 0 else '+'} {fnum(abs(p2))})"
    x = series_zinv(num, den, 5)
    xw = series_zinv(num, [1.0, -a1, -a2], 5)
    stmt = (f"Given the z-transform of a continuous-time signal $x(t)$:\n\n$$X(z) = \\dfrac{{{num_tex}}}{{{den_tex}}}$$\n\n"
            "**Manually** compute the sequence $x(k)$ up to $k = 4$ with the **computational method**.")
    rec = (f"x(k) = {fnum(-a1)}\\,x(k-1) {'-' if a2 >= 0 else '+'} {fnum(abs(a2))}\\,x(k-2) + "
           + " + ".join(f"{fnum(c)}\\,u(k-{i})" if i else f"{fnum(c)}\\,u(k)" for i, c in enumerate(num) if abs(c) > 1e-12))
    parts = [
        Part("den", "(a) Denominator of $X(z)$ written in powers of $z^{-1}$: coefficients $[1,\\ a_1,\\ a_2]$", "vec", den, points=1,
             hint="Divide numerator and denominator by z² (the highest power).",
             explain=f"$({den_tex})/z^2 = 1 {'+' if a1 >= 0 else '-'} {fnum(abs(a1))}z^{{-1}} {'+' if a2 >= 0 else '-'} {fnum(abs(a2))}z^{{-2}}$.",
             placeholder="3 numbers"),
        Part("x", "(b) $x(0), x(1), x(2), x(3), x(4)$", "vec", x, points=5,
             hint="X(z) = N(z⁻¹)/D(z⁻¹)·U(z) with U(z) = 1 (Kronecker delta input). Write the difference equation and recurse with x(k<0) = 0.",
             explain="Computational method: $X(z)$ is the unit-pulse response of $N/D$; the recursion is " f"${rec}$ with $u = \\delta_0$.",
             misconceptions=[Misc(xw, "diffeq_sign", "Your values follow the recursion with the denominator signs NOT flipped.")],
             placeholder="5 numbers"),
    ]
    u = [1, 0, 0, 0, 0]
    lines = []
    for k in range(5):
        lines.append(f"- $k={k}$: $x({k}) = {fnum(x[k])}$")
    sol = (f"$X(z) = \\dfrac{{{poly_zinv_tex(num)}}}{{{poly_zinv_tex(den)}}}\\,U(z)$ with $U(z)=1 \\Leftrightarrow u(k)=\\delta_0(k)$.\n\n"
           f"Difference equation: ${rec}$, $u(0)=1$, $u(k\\ne0)=0$, $x(k<0)=0$.\n\n" + "\n".join(lines) +
           "\n\nCheck: the same numbers result from long division (direct division method).")
    matlab = (f"num = [{' '.join(fnum(c) for c in num)}]; den = [{' '.join(fnum(c) for c in den)}];  % in z^-1\n"
              f"x = filter(num, den, [1 zeros(1,4)])   % unit-pulse response = x(k)\n% or: impz(num, den, 5)")
    _ = u
    parts[0].steps = [
        f"Multiply out the denominator: ${den_tex} = z^2 {'+' if a1 >= 0 else '-'} {fnum(abs(a1))}z {'+' if a2 >= 0 else '-'} {fnum(abs(a2))}$.",
        "Divide numerator AND denominator by the highest power $z^2$: $z^2 \\to 1$, $z \\to z^{-1}$, constant $\\to z^{-2}$.",
        f"Denominator becomes $1 {'+' if a1 >= 0 else '-'} {fnum(abs(a1))}z^{{-1}} {'+' if a2 >= 0 else '-'} {fnum(abs(a2))}z^{{-2}}$ ⇒ coefficients $[1, {fnum(a1)}, {fnum(a2)}]$.",
        f"(The numerator likewise becomes ${poly_zinv_tex(num)}$.)",
    ]
    parts[1].steps = [
        f"Write $X(z)\\cdot({poly_zinv_tex(den)}) = ({poly_zinv_tex(num)})\\cdot U(z)$ with $U(z) = 1$ — a single pulse u(0) = 1, all other u = 0.",
        "Translate every $z^{-m}$ into a delay of m steps (x(k−m), u(k−m)) and move the old x-values to the right side — **their signs flip**:",
        f"${rec}$",
        "Start values: x(−1) = x(−2) = 0, u(0) = 1, u(k) = 0 for k ≥ 1. Now compute one line per k:",
        *recursion_steps(num, den, [1.0], 5, "x"),
    ]
    return Problem("zt_inverse_comp", "zt_inverse", "Inverse z-transform: computational method", difficulty, seed, stmt, parts, sol, matlab,
                   source="Pattern: Exam 2016 Problem 1 (6 P); Book Ex. 2.9, 2.10",
                   plot=lambda: plots.stem_seq({"x(k)": series_zinv(num, den, 12)}, "x(k)"),
                   remedy="X(z) = N/D·1 ⇒ recursion with δ₀ input; denominator signs flip on the right-hand side.")


# --------------------------------------------------------------------------- 3
def zt_pfe(rng, difficulty, seed):
    p = float(_c(rng, [0.2, 0.5, -0.5, 0.8, 0.6, 0.4]))
    n1 = float(_c(rng, [10.0, 2.0, 1.0, 4.0, 5.0]))
    n0 = float(_c(rng, [5.0, 1.0, -1.0, 2.0, 0.0])) if difficulty > 1 else 0.0
    N = lambda z: n1 * z + n0  # noqa: E731
    A = n0 / p  # = N(0)/((0-1)(0-p))
    B = N(1.0) / (1 - p)
    C = N(p) / (p * (p - 1))
    stmt = (f"Find the inverse z-transform of\n\n$$X(z) = \\dfrac{{{fnum(n1)}z {'+' if n0 >= 0 else '-'} {fnum(abs(n0))}}}{{(z-1)(z {'-' if p >= 0 else '+'} {fnum(abs(p))})}}$$\n\n"
            "with the **partial fraction expansion method**, in the form $x(k) = A\\,\\delta_0(k) + B\\,\\sigma(k) + C\\,p^k$.")
    parts = [
        Part("A", "$A$ (coefficient of $\\delta_0(k)$)", "num", A, points=1,
             hint="Expand X(z)/z = A/z + B/(z−1) + C/(z−p). A = residue at z = 0.",
             explain="$A = \\left.\\dfrac{N(z)}{(z-1)(z-p)}\\right|_{z=0}$.",
             misconceptions=[Misc(0.0, "pfe_no_divide_z", "A = 0 suggests you expanded X(z) instead of X(z)/z.")] if abs(A) > 1e-9 else []),
        Part("B", "$B$ (coefficient of $\\sigma(k)$)", "num", B, points=1,
             explain="$B = \\left.\\dfrac{N(z)}{z(z-p)}\\right|_{z=1}$."),
        Part("C", f"$C$ (coefficient of $({fnum(p)})^k$)", "num", C, points=1,
             explain="$C = \\left.\\dfrac{N(z)}{z(z-1)}\\right|_{z=p}$.",
             misconceptions=[Misc(N(p) / (p - 1), "pfe_no_divide_z", "This is the residue of X(z) (not X(z)/z) — off by the factor 1/p.")]),
        Part("fin", "Final value $x(\\infty)$", "num", B, points=1,
             explain=f"$|p| = {fnum(abs(p))} < 1$, so $p^k \\to 0$ and $x(\\infty) = B$ (equivalently FVT).",
             misconceptions=[Misc(B + C, "fvt_no_factor", "You added C as if pᵏ → 1. Only the σ(k)-term survives.")]),
    ]
    sol = (f"$\\dfrac{{X(z)}}{{z}} = \\dfrac{{{fnum(n1)}z {'+' if n0 >= 0 else '-'} {fnum(abs(n0))}}}{{z(z-1)(z-{fnum(p)})}} = \\dfrac{{A}}{{z}} + \\dfrac{{B}}{{z-1}} + \\dfrac{{C}}{{z-{fnum(p)}}}$\n\n"
           f"- $A = N(0)/((0-1)(0-{fnum(p)})) = {fnum(A)}$\n- $B = N(1)/(1\\cdot(1-{fnum(p)})) = {fnum(B)}$\n"
           f"- $C = N({fnum(p)})/({fnum(p)}({fnum(p)}-1)) = {fnum(C)}$\n\n"
           f"$X(z) = {fnum(A)} + {fnum(B)}\\dfrac{{z}}{{z-1}} + {fnum(C)}\\dfrac{{z}}{{z-{fnum(p)}}}$ ⇒ table entries 1, 2, 13:\n\n"
           f"$$x(k) = {fnum(A)}\\,\\delta_0(k) + {fnum(B)}\\,\\sigma(k) + ({fnum(C)})({fnum(p)})^k$$")
    matlab = (f"% residuez works in z^-1:  X = (n1 z^-1 + n0 z^-2)/(1 - (1+p) z^-1 + p z^-2)\n"
              f"[r, pp, k] = residuez([0 {fnum(n1)} {fnum(n0)}], conv([1 -1],[1 {fnum(-p)}]))\n% r = [B; C] (order of pp), k = direct term A")
    num_z = [0.0, n1, n0]
    den_z = [1.0, -(1 + p), p]
    parts[0].steps = [
        "Divide X(z) by z first (because the table pair is z/(z − p) ↔ pᵏ): $\\dfrac{X(z)}{z} = \\dfrac{N(z)}{z(z-1)(z-p)}$ — three factors ⇒ three pieces A/z + B/(z−1) + C/(z−p).",
        "A belongs to the factor z (root z = 0). Cover z and put z = 0 into the rest:",
        f"$A = \\dfrac{{N(0)}}{{(0-1)(0-{fnum(p)})}} = \\dfrac{{{fnum(n0)}}}{{{fnum(p)}}} = {fnum(A)}$.",
    ]
    parts[1].steps = [
        "B belongs to (z − 1), root z = 1. Cover (z − 1), put z = 1 into the rest:",
        f"$N(1) = {fnum(n1)} + {fnum(n0)} = {fnum(N(1.0))}$; the rest of the denominator is $z(z-{fnum(p)})$ at z = 1: $1\\cdot(1-{fnum(p)}) = {fnum(1 - p)}$.",
        f"$B = {fnum(N(1.0))}/{fnum(1 - p)} = {fnum(B)}$.",
    ]
    parts[2].steps = [
        f"C belongs to (z − {fnum(p)}), root z = {fnum(p)}. Cover it, put z = {fnum(p)} into the rest:",
        f"$N({fnum(p)}) = {fnum(n1)}\\cdot{fnum(p)} + {fnum(n0)} = {fnum(N(p))}$; the rest $z(z-1)$ at z = {fnum(p)}: ${fnum(p)}\\cdot({fnum(p - 1)}) = {fnum(p * (p - 1))}$.",
        f"$C = {fnum(N(p))}/{fnum(p * (p - 1))} = {fnum(C)}$.",
        "Multiply back by z: X = A + B·z/(z−1) + C·z/(z−p) ⇒ x(k) = A·δ₀(k) + B + C·pᵏ.",
    ]
    parts[3].steps = [
        f"For large k: δ₀(k) = 0 (it is only 1 at k = 0), and $({fnum(p)})^k \\to 0$ because |{fnum(p)}| < 1.",
        f"Only the constant B survives ⇒ $x(\\infty) = {fnum(B)}$.",
    ]
    return Problem("zt_pfe", "zt_inverse", "Inverse z-transform: partial fractions", difficulty, seed, stmt, parts, sol, matlab,
                   source="Book Ex. 2.8; Exercise book Problems 2.4, 2.8",
                   plot=lambda: plots.stem_seq({"x(k)": series_zinv(num_z, den_z, 12)}),
                   remedy="Always expand X(z)/z, then multiply by z: z/(z−p) ↔ pᵏ.")


# --------------------------------------------------------------------------- 4
def diffeq_weighting(rng, difficulty, seed):
    p1, p2 = _c(rng, [(0.7, 0.2), (0.5, 0.4), (0.6, 0.3), (0.8, 0.5), (0.5, -0.3), (0.5, 0.2)])
    a1, a2 = round(-(p1 + p2), 4), round(p1 * p2, 4)
    b0, b1 = (1.0, 0.0) if difficulty == 1 else _c(rng, [(1.0, 0.0), (0.0, 1.0), (1.0, 0.5)])
    u = _c(rng, [[1, 1, 1], [1, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1, 1]])
    num = [b0, b1]
    den = [1.0, a1, a2]
    g = series_zinv(num, den, 6)
    y = series_zinv(num, den, 6, u=u)
    gw = series_zinv(num, [1.0, -a1, -a2], 6)
    G1 = (b0 + b1) / (1 + a1 + a2)
    rhs = " + ".join(t for t in [f"{fnum(b0)}u(k)" if b0 else "", f"{fnum(b1)}u(k-1)" if b1 else ""] if t)
    stmt = (f"A system is described by the difference equation\n\n$$y(k) {'+' if a1 >= 0 else '-'} {fnum(abs(a1))}\\,y(k-1) {'+' if a2 >= 0 else '-'} {fnum(abs(a2))}\\,y(k-2) = {rhs}$$\n\n"
            f"The input is $u(k) = {fvec(u)}$ for $k = 0,1,\\dots$ and zero afterwards.")
    parts = [
        Part("den", "(a) $G(z) = Y(z)/U(z)$: denominator coefficients $[1,\\ a_1,\\ a_2]$ in $z^{-1}$", "vec", den, points=1,
             explain="z-transform each term with the shift-right theorem $\\mathcal Z\\{y(k-n)\\} = z^{-n}Y(z)$.", placeholder="3 numbers"),
        Part("g", "(b) Weighting sequence $g(k)$, $k=0..5$", "vec", g, points=2,
             hint="g(k) is the response to u = δ₀(k): run the recursion with u(0) = 1, u(k>0) = 0.",
             explain="$g(k) = \\mathcal Z^{-1}\\{G(z)\\}$ = unit-pulse response.",
             misconceptions=[Misc(gw, "diffeq_sign", "Recursion with the wrong sign of the y-terms.")], placeholder="6 numbers"),
        Part("y", "(c) Output $y(k)$, $k=0..5$, for the given input", "vec", y, points=2,
             hint="Either recurse with the actual input, or convolve: y(k) = Σ g(k−h)u(h).",
             explain="Computational method with the given input; identical to the convolution sum $\\sum_h g(k-h)u(h)$.",
             placeholder="6 numbers"),
        Part("dc", "(d) Stationary gain $G(1)$ (final value of the unit-step response)", "num", G1, points=1,
             explain="FVT with $U(z) = 1/(1-z^{-1})$: $y(\\infty) = G(1)$ (poles inside the unit circle)."),
    ]
    conv_lines = [f"- $y({k}) = " + " + ".join(f"g({k - h})u({h})" for h in range(len(u)) if k - h >= 0) + f" = {fnum(y[k])}$" for k in range(4)]
    sol = (f"$$G(z) = \\dfrac{{{poly_zinv_tex(num)}}}{{{poly_zinv_tex(den)}}}$$\n\n"
           f"Recursion: $y(k) = {fnum(-a1)}y(k-1) {'-' if a2 >= 0 else '+'} {fnum(abs(a2))}y(k-2) + {rhs}$.\n\n"
           f"Weighting sequence ($u=\\delta_0$): $g = {fvec(g)}$\n\nOutput with the given input: $y = {fvec(y)}$\n\n"
           "Convolution check:\n" + "\n".join(conv_lines) + f"\n\n$G(1) = {fnum(b0 + b1)}/{fnum(1 + a1 + a2)} = {fnum(G1)}$")
    matlab = (f"num = [{fnum(b0)} {fnum(b1)}]; den = [1 {fnum(a1)} {fnum(a2)}];\n"
              f"g = filter(num, den, [1 zeros(1,5)])\nu = [{' '.join(str(x) for x in u)} zeros(1,{6 - len(u)})];\n"
              "y = filter(num, den, u)\nyc = conv(g, u); yc(1:6)   % convolution check")
    parts[0].steps = [
        "Transform term by term: y(k) → Y(z), y(k−1) → z⁻¹Y(z), y(k−2) → z⁻²Y(z); same for u.",
        f"$Y(z)(1 {'+' if a1 >= 0 else '-'} {fnum(abs(a1))}z^{{-1}} {'+' if a2 >= 0 else '-'} {fnum(abs(a2))}z^{{-2}}) = ({poly_zinv_tex(num)})U(z)$.",
        f"G = Y/U ⇒ denominator coefficients $[1, {fnum(a1)}, {fnum(a2)}]$ (the y-side of the equation).",
    ]
    parts[1].steps = [
        f"Isolate y(k): $y(k) = {fnum(-a1)}y(k-1) {'-' if a2 >= 0 else '+'} {fnum(abs(a2))}y(k-2) + {rhs}$.",
        "Weighting sequence = response to a single pulse: u(0) = 1, all other u = 0, y(negative) = 0.",
        *recursion_steps(num, den, [1.0], 6, "g"),
    ]
    parts[2].steps = [
        f"Same recursion, now with the given input u = {fvec(u)} (then zeros):",
        *recursion_steps(num, den, u, 6, "y"),
    ]
    parts[3].steps = [
        "Steady state of a step response: put z = 1 in G(z) (every z⁻¹ becomes 1).",
        f"Numerator sum: {fnum(b0)} + {fnum(b1)} = {fnum(b0 + b1)}; denominator sum: 1 + ({fnum(a1)}) + ({fnum(a2)}) = {fnum(1 + a1 + a2)}.",
        f"G(1) = {fnum(b0 + b1)}/{fnum(1 + a1 + a2)} = {fnum(G1)}.",
    ]
    return Problem("diffeq_weighting", "diff_eq", "Difference equation → G(z), g(k), y(k)", difficulty, seed, stmt, parts, sol, matlab,
                   source="Exercise/Homework 2 (presentation_ex_2); Exercise book Problem 2.7; Book Ex. 2.12",
                   plot=lambda: plots.stem_seq({"g(k)": g, "y(k)": y}),
                   remedy="Shift-right theorem; weighting sequence = pulse response; convolution = same y.")


# --------------------------------------------------------------------------- 5
def convolution(rng, difficulty, seed):
    p = float(_c(rng, [0.5, 0.8, -0.5, 0.6]))
    c = float(_c(rng, [1.0, 2.0]))
    g = [c * p ** k for k in range(6)]
    u = list(_c(rng, [[0, 1, 2, 3], [1, 2, 1], [2, 1, 0, 1], [1, 1, 1], [0, 1, 1, 2]]))
    uu = u + [0] * 6
    y = [sum(g[k - h] * uu[h] for h in range(k + 1)) for k in range(6)]
    kq = int(_c(rng, [2, 3, 4]))
    stmt = (f"A system has the weighting sequence $g(k) = {fnum(c)}\\cdot({fnum(p)})^k$, $k \\ge 0$. "
            f"The input is $u(k) = {fvec(u)}$ (zero afterwards).")
    parts = [
        Part("yk", f"(a) $y({kq})$ via the convolution sum", "num", y[kq], points=1,
             hint=f"y({kq}) = Σ_h u({kq}−h)·g(h), h = 0..{kq}.",
             explain=f"$y({kq}) = " + " + ".join(f"u({kq - h})g({h})" for h in range(kq + 1)) + "$"),
        Part("y", "(b) $y(k)$ for $k = 0..5$", "vec", y, points=2, placeholder="6 numbers"),
    ]
    sol = (f"$g = {fvec(g)}$\n\n" + "\n".join(
        f"- $y({k}) = " + " + ".join(f"{fnum(uu[k - h])}\\cdot{fnum(g[h])}" for h in range(k + 1)) + f" = {fnum(y[k])}$" for k in range(6)))
    matlab = f"g = {fnum(c)}*({fnum(p)}).^(0:5);\nu = [{' '.join(str(x) for x in u)}];\ny = conv(g, u); y(1:6)"
    parts[0].steps = [
        f"List the weighting sequence: g = {fvec(g[:kq + 1])} (g(0), g(1), …).",
        f"Formula: $y({kq}) = \\sum_{{h=0}}^{{{kq}}} u({kq}-h)\\,g(h)$ — pair g(0) with the NEWEST input u({kq}), g(1) with u({kq - 1}), …",
        *[f"h = {h}: u({kq - h})·g({h}) = {fnum(uu[kq - h])}·{fnum(g[h])} = {fnum(uu[kq - h] * g[h])}" for h in range(kq + 1)],
        f"Add them: y({kq}) = {fnum(y[kq])}.",
    ]
    parts[1].steps = [f"y({k}) = " + " + ".join(f"{fnum(uu[k - h])}·{fnum(g[h])}" for h in range(k + 1)) + f" = {fnum(y[k])}" for k in range(6)]
    return Problem("convolution", "diff_eq", "Convolution summation", difficulty, seed, stmt, parts, sol, matlab,
                   source="Book Ex. 2.13; Exercise book Problem 2.6",
                   plot=lambda: plots.stem_seq({"g(k)": g, "u(k)": uu[:6], "y(k)": y}),
                   remedy="y(k) = Σ_{h=0}^{k} g(k−h)u(h): flip one sequence, slide, multiply, add.")


# --------------------------------------------------------------------------- 6
def fvt_ivt(rng, difficulty, seed):
    case = _c(rng, ["stable", "stable", "osc", "unstable"]) if difficulty > 1 else "stable"
    if case == "stable":
        p = float(_c(rng, [0.5, 0.2, 0.8, -0.5]))
        K = float(_c(rng, [1.0, 2.0, 0.5, 2.7]))
        b0 = float(_c(rng, [0.0, 0.0, 1.0]))
        num = [b0, K]
        den = list(np.convolve([1, -1], [1, -p]))
        x0 = b0
        fin = (b0 + K) / (1 - p)
        tex = f"\\dfrac{{{poly_zinv_tex(num)}}}{{(1-z^{{-1}})(1 {'-' if p >= 0 else '+'} {fnum(abs(p))}z^{{-1}})}}"
        why = f"$(1-z^{{-1}})X(z)$ has its only pole at $z={fnum(p)}$, inside the unit circle ⇒ FVT valid."
    elif case == "osc":
        num, den = [1.0], [1.0, -1.0, 1.0]
        x0, fin = 1.0, None
        tex = "\\dfrac{1}{1 - z^{-1} + z^{-2}}"
        why = "Poles $z = e^{\\pm j\\pi/3}$ lie ON the unit circle: undamped oscillation, the limit does not exist (Problem 2.9)."
    else:
        q = float(_c(rng, [1.5, 2.0, 1.2]))
        num = [0.0, 1.0]
        den = list(np.convolve([1, -1], [1, -q]))
        x0, fin = 0.0, None
        tex = f"\\dfrac{{z^{{-1}}}}{{(1-z^{{-1}})(1-{fnum(q)}z^{{-1}})}}"
        why = f"Pole at $z = {fnum(q)}$ outside the unit circle ⇒ $x(k)$ diverges; FVT not applicable."
    opts = ["Yes — FVT is applicable", "No — FVT is not applicable"]
    stmt = f"Consider $$X(z) = {tex}.$$"
    parts = [
        Part("x0", "(a) Initial value $x(0)$ (initial value theorem)", "num", x0, points=1,
             hint="x(0) = lim_{z→∞} X(z): every z⁻¹ term vanishes.",
             explain="$x(0) = \\lim_{z\\to\\infty}X(z)$ = ratio of the $z^0$ coefficients."),
        Part("app", "(b) Can the final value theorem be applied?", "choice", opts[0] if fin is not None else opts[1], options=opts, points=1,
             explain=why,
             misconceptions=[Misc(opts[0], "fvt_not_applicable", "The FVT result would be a number, but the sequence never converges — check the poles first.")] if fin is None else []),
    ]
    if fin is not None:
        parts.append(Part("fin", "(c) Final value $x(\\infty)$", "num", fin, points=1,
                          explain="$x(\\infty) = \\lim_{z\\to1}(1-z^{-1})X(z)$: the $(1-z^{-1})$ cancels, then set $z=1$."))
    seq = series_zinv(num, den, 15)
    sol = f"{why}\n\nFirst values: $x = {fvec(seq[:8])}\\dots$" + (f"\n\n$x(\\infty) = {fnum(fin)}$" if fin is not None else "")
    return Problem("fvt_ivt", "zt_basics", "Initial & final value theorems", difficulty, seed, stmt, parts, sol,
                   f"x = filter([{' '.join(fnum(c) for c in num)}], [{' '.join(fnum(c) for c in den)}], [1 zeros(1,30)]); stem(0:30, x)",
                   source="Book Theorems 2.5/2.6, Ex. 2.6; Exercise book Problems 2.5, 2.9",
                   plot=lambda: plots.stem_seq({"x(k)": seq}),
                   remedy="Check poles of (1 − z⁻¹)X(z) before using the FVT.")


# --------------------------------------------------------------------------- 7
def zt_table_quiz(rng, difficulty, seed):
    a = float(_c(rng, [0.5, 1.0, 2.0, 4.0]))
    T = float(_c(rng, [0.1, 0.2, 0.25, 0.5]))
    n = int(_c(rng, [2, 3, 4]))
    w = float(_c(rng, [1.0, 2.0, np.pi]))
    pole = float(np.exp(-a * T))
    opts_shift = [
        f"z^{n} X(z) − " + " − ".join(f"z^{n - i} x({i})" if n - i > 1 else f"z x({i})" for i in range(n)),
        f"z^-{n} X(z)",
        f"z^{n} X(z)",
        f"z^{n} X(z) + " + " + ".join(f"z^{n - i} x({i})" if n - i > 1 else f"z x({i})" for i in range(n)),
    ]
    parts = [
        Part("pole", f"Pole of $\\mathcal Z\\{{e^{{-{fnum(a)}kT}}\\}}$ for $T = {fnum(T)}$ s", "num", pole, points=1,
             explain=f"Table entry 3: $1/(1-e^{{-aT}}z^{{-1}})$ ⇒ pole $z = e^{{-aT}} = e^{{-{fnum(a * T)}}} = {fnum(pole)}$.",
             misconceptions=[Misc(float(np.exp(-a)), "map_deg_rad", "You forgot the sampling time: the pole is e^{−aT}, not e^{−a}.")]),
        Part("ramp", f"Numerator coefficient $c$ in $\\mathcal Z\\{{kT\\}} = c\\,z^{{-1}}/(1-z^{{-1}})^2$ for $T = {fnum(T)}$", "num", T, points=1,
             explain="Table entry 4: $\\mathcal Z\\{\\rho(kT)\\} = Tz^{-1}/(1-z^{-1})^2$."),
        Part("shift", f"$\\mathcal Z\\{{x(k+{n})\\}}$ = ?", "choice", opts_shift[0], options=list(rng.permutation(opts_shift)), points=1,
             explain=f"Shift-left theorem: $z^{n}[X(z) - \\sum_{{k=0}}^{{{n - 1}}} x(k)z^{{-k}}]$."),
        Part("cos", f"Denominator of $\\mathcal Z\\{{\\cos({fnum(w)}kT)\\}}$, $T={fnum(T)}$: coefficient of $z^{{-1}}$", "num", -2 * np.cos(w * T), points=1,
             explain=f"Entry 10: $1 - 2z^{{-1}}\\cos\\omega T + z^{{-2}}$ ⇒ $-2\\cos({fnum(w * T)}) = {fnum(-2 * np.cos(w * T))}$ (radians!).",
             misconceptions=[Misc(-2 * np.cos(np.radians(w * T)), "map_deg_rad", "Calculator in degree mode: ωT is in radians.")]),
    ]
    return Problem("zt_table_quiz", "zt_basics", "z-transform table & theorems quick-fire", difficulty, seed,
                   "Answer from the z-transform table (Formelsammlung p. 2) and the shift theorems.", parts,
                   "See the explanations of each part (table entries 3, 4, 10 and the shift-left theorem).", "",
                   source="Book Table 2.1, Theorems 2.3/2.4", remedy="Know table entries 2–5, 9, 10, 13 by heart.")


GENERATORS = {
    "zt_signal_exam": zt_signal_exam,
    "zt_inverse_comp": zt_inverse_comp,
    "zt_pfe": zt_pfe,
    "diffeq_weighting": diffeq_weighting,
    "convolution": convolution,
    "fvt_ivt": fvt_ivt,
    "zt_table_quiz": zt_table_quiz,
}
