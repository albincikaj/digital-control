"""Foundations (zero-background track): complex numbers, poles & stability, partial fractions,
first-order systems / Laplace, feedback, 2x2 matrices. Every later exam topic uses these tools."""
from __future__ import annotations

import cmath
import math

import numpy as np

from .. import plots
from ..mathutil import fmat, fnum
from .base import Misc, Part, Problem


def _c(rng, xs):
    return xs[int(rng.integers(len(xs)))]


def f_complex(rng, difficulty, seed):
    if difficulty == 1:
        a = float(_c(rng, [3.0, 1.0, -1.0, 0.6, 0.5]))
        b = float(_c(rng, [4.0, 1.0, 1.0, 0.8, -0.5]))
        z = complex(a, b)
        stmt = f"Consider the complex number $z = {fnum(a)} {'+' if b >= 0 else '-'} j{fnum(abs(b))}$ (j = √−1; engineers write j instead of i)."
        parts = [
            Part("mag", "Magnitude $|z| = \\sqrt{a^2 + b^2}$", "num", abs(z), points=1,
                 hint="Pythagoras: real part = a, imaginary part = b, length of the arrow from 0 to the point (a, b).",
                 explain=f"$\\sqrt{{{fnum(a)}^2 + {fnum(b)}^2}} = {fnum(abs(z))}$ — the distance of the point from the origin."),
            Part("ang", "Angle $\\arg z$ in degrees (measured from the positive real axis, between −180° and 180°)", "num",
                 math.degrees(cmath.phase(z)), points=1, tol_abs=0.5,
                 hint="atan2(b, a): if a < 0 you must add/subtract 180° to the plain arctan(b/a).",
                 explain="Use atan2(b, a) — a calculator's tan⁻¹(b/a) is only right when a > 0.",
                 misconceptions=[Misc(math.degrees(math.atan(b / a)), "map_deg_rad", "tan⁻¹(b/a) loses the quadrant when the real part is negative.")] if a < 0 else []),
        ]
        sol = f"$|z| = {fnum(abs(z))}$, $\\arg z = {fnum(math.degrees(cmath.phase(z)))}°$. Polar form: $z = {fnum(abs(z))}\\,e^{{j\\,{fnum(cmath.phase(z))}}}$."
        pts = [z]
        parts[0].steps = [
            f"Identify the two parts: the **real part** is the number without j: $a = {fnum(a)}$; the **imaginary part** is the number in front of j: $b = {fnum(b)}$.",
            f"Picture the point $({fnum(a)}, {fnum(b)})$ in the plane. The magnitude is the length of the arrow from the origin to this point (Pythagoras).",
            f"Square both parts: $a^2 = {fnum(a)}^2 = {fnum(a * a)}$ and $b^2 = {fnum(b)}^2 = {fnum(b * b)}$ (a square is never negative).",
            f"Add them: ${fnum(a * a)} + {fnum(b * b)} = {fnum(a * a + b * b)}$.",
            f"Take the square root: $\\sqrt{{{fnum(a * a + b * b)}}} = {fnum(abs(z))}$.",
        ]
        base = math.degrees(math.atan(abs(b) / abs(a))) if a != 0 else 90.0
        quad = ("first quadrant (right, up): angle = base angle" if a > 0 and b >= 0 else
                "fourth quadrant (right, down): angle = −base angle" if a > 0 else
                "second quadrant (left, up): angle = 180° − base angle" if b >= 0 else
                "third quadrant (left, down): angle = −(180° − base angle)")
        parts[1].steps = [
            "The angle is the direction of the arrow, measured from the positive real axis (pointing right), counter-clockwise positive.",
            f"Base angle from the sizes only: $\\tan^{{-1}}(|b|/|a|) = \\tan^{{-1}}({fnum(abs(b))}/{fnum(abs(a))}) = {fnum(base, 2)}°$ (calculator in DEGREE mode).",
            f"Where is the point? $a = {fnum(a)}$ ({'right' if a > 0 else 'left'} of 0), $b = {fnum(b)}$ ({'up' if b >= 0 else 'down'}) ⇒ {quad}.",
            f"So $\\arg z = {fnum(math.degrees(cmath.phase(z)), 2)}°$.",
        ]
    elif difficulty == 2:
        r = float(_c(rng, [0.5, 0.8, 1.0, 0.7]))
        th = float(_c(rng, [30.0, 45.0, 60.0, 90.0, 120.0, 36.0]))
        z = cmath.rect(r, math.radians(th))
        stmt = f"A point in the plane has magnitude $r = {fnum(r)}$ and angle $\\theta = {fnum(th)}°$, i.e. $z = r\\,e^{{j\\theta}}$."
        parts = [Part("re", "Real part $r\\cos\\theta$", "num", z.real, points=1,
                      misconceptions=[Misc(r * math.cos(th), "map_deg_rad", "Your calculator is in RADIAN mode but θ is given in degrees.")]),
                 Part("im", "Imaginary part $r\\sin\\theta$", "num", z.imag, points=1)]
        sol = f"$z = {fnum(r)}(\\cos{fnum(th)}° + j\\sin{fnum(th)}°) = {fnum(z)}$. Euler: $e^{{j\\theta}} = \\cos\\theta + j\\sin\\theta$."
        pts = [z]
        parts[0].steps = [
            "Euler's formula: $r\\,e^{j\\theta} = r\\cos\\theta + j\\,r\\sin\\theta$. The real part is $r\\cos\\theta$.",
            f"Set the calculator to DEGREE mode (θ is given in degrees). $\\cos({fnum(th)}°) = {fnum(math.cos(math.radians(th)))}$.",
            f"Multiply by the length: ${fnum(r)}\\cdot{fnum(math.cos(math.radians(th)))} = {fnum(z.real)}$.",
        ]
        parts[1].steps = [
            "The imaginary part is $r\\sin\\theta$.",
            f"$\\sin({fnum(th)}°) = {fnum(math.sin(math.radians(th)))}$.",
            f"${fnum(r)}\\cdot{fnum(math.sin(math.radians(th)))} = {fnum(z.imag)}$.",
        ]
    else:
        T = float(_c(rng, [0.1, 0.2, 0.5]))
        s = complex(-float(_c(rng, [1.0, 2.0, 0.5])), float(_c(rng, [2.0, 3.0, 4.0])))
        z = cmath.exp(s * T)
        stmt = (f"In digital control we constantly compute $z = e^{{sT}}$. Take $s = {fnum(s)}$ and $T = {fnum(T)}$ s. "
                "Rule: $e^{(\\sigma + j\\omega)T} = e^{\\sigma T}\\cdot e^{j\\omega T}$ — the real part gives the magnitude, the imaginary part the angle (in radians).")
        parts = [Part("mag", "$|z| = e^{\\sigma T}$", "num", abs(z), points=1),
                 Part("ang", "$\\arg z = \\omega T$ in radians", "num", s.imag * T, points=1,
                      misconceptions=[Misc(math.degrees(s.imag * T), "map_deg_rad", "That is degrees; the formula ωT gives radians.")]),
                 Part("re", "$\\mathrm{Re}\\,z$", "num", z.real, points=1)]
        sol = f"$|z| = e^{{{fnum(s.real * T)}}} = {fnum(abs(z))}$, $\\arg z = {fnum(s.imag * T)}$ rad, $z = {fnum(z)}$."
        pts = [z]
        sig, om = s.real, s.imag
        parts[0].steps = [
            f"Split $s = \\sigma + j\\omega$: $\\sigma = {fnum(sig)}$ (real part), $\\omega = {fnum(om)}$ (imaginary part).",
            f"$e^{{sT}} = e^{{\\sigma T}}\\cdot e^{{j\\omega T}}$. The factor $e^{{j\\omega T}}$ has length 1, so the length comes only from $e^{{\\sigma T}}$.",
            f"$\\sigma T = {fnum(sig)}\\cdot{fnum(T)} = {fnum(sig * T)}$.",
            f"$e^{{{fnum(sig * T)}}} = {fnum(abs(z))}$ (calculator: e^x key).",
        ]
        parts[1].steps = [
            "The angle comes only from $e^{j\\omega T}$: angle $= \\omega T$, in **radians**.",
            f"$\\omega T = {fnum(om)}\\cdot{fnum(T)} = {fnum(om * T)}$ rad (that is {fnum(math.degrees(om * T), 2)}°, but the question wants radians).",
        ]
        parts[2].steps = [
            "Real part = length × cos(angle).",
            f"$\\cos({fnum(om * T)}\\text{{ rad}}) = {fnum(math.cos(om * T))}$ (calculator in RADIAN mode).",
            f"${fnum(abs(z))}\\cdot{fnum(math.cos(om * T))} = {fnum(z.real)}$.",
        ]
    return Problem("f_complex", "f_complex", "Complex numbers: magnitude, angle, e^{jθ}", difficulty, seed, stmt, parts, sol,
                   "z = 3+4i; abs(z), angle(z)*180/pi\nr = 0.8; th = 60; r*exp(1i*th*pi/180)",
                   source="Foundation for s↔z mapping, root locus, poles", plot=lambda: plots.zplane(extra=[(pts, "ro", "z")], title="Your point"),
                   remedy="|a+jb| = √(a²+b²); angle = atan2(b, a); e^{jθ} = cos θ + j sin θ.")


def f_poles(rng, difficulty, seed):
    domain = "s" if difficulty == 1 else _c(rng, ["s", "z"])
    if domain == "s":
        r1, r2 = _c(rng, [(-1.0, -2.0), (-1.0, -4.0), (1.0, -2.0), (-0.5, -3.0), (2.0, -1.0)])
        p = -(r1 + r2)
        q = r1 * r2
        stable = r1 < 0 and r2 < 0
        stmt = (f"A continuous-time system has the denominator (characteristic polynomial) $s^2 {'+' if p >= 0 else '-'} {fnum(abs(p))}s {'+' if q >= 0 else '-'} {fnum(abs(q))}$. "
                "Its **poles** are the roots. Continuous rule: stable ⇔ every pole has **negative real part** (left half-plane).")
        rule = "Re(pole) < 0"
    else:
        r1, r2 = _c(rng, [(0.5, 0.2), (0.8, -0.5), (1.2, 0.5), (-0.9, 0.3), (1.0, 0.4), (-1.5, 0.2)])
        p = -(r1 + r2)
        q = r1 * r2
        stable = abs(r1) < 1 and abs(r2) < 1
        stmt = (f"A **discrete-time** system has the characteristic polynomial $z^2 {'+' if p >= 0 else '-'} {fnum(abs(p))}z {'+' if q >= 0 else '-'} {fnum(abs(q))}$. "
                "Discrete rule: stable ⇔ every pole lies **strictly inside the unit circle** (|pole| < 1).")
        rule = "|pole| < 1"
    opts = ["stable", "not stable"]
    roots = sorted([r1, r2], reverse=True)
    parts = [Part("r", "Both poles, largest first", "vec", roots, points=2, placeholder="2 numbers",
                  hint="Quadratic formula: x = (−b ± √(b² − 4c))/2 for x² + bx + c.",
                  explain="Poles = values that make the denominator zero."),
             Part("st", "Stability verdict", "choice", opts[0] if stable else opts[1], options=opts, points=1,
                  explain=f"Rule here: {rule}. Poles {fnum(r1)}, {fnum(r2)}.",
                  misconceptions=[Misc(opts[0] if not stable else opts[1], "stab_rule",
                                       "You used the wrong rule: continuous systems need Re < 0, discrete ones need |pole| < 1.")])]
    sol = f"Roots: {fnum(roots[0])}, {fnum(roots[1])} ⇒ {'stable' if stable else 'not stable'} ({rule})."
    v = domain
    D = p * p - 4 * q
    parts[0].steps = [
        f"Poles = values of {v} that make the polynomial zero: solve ${v}^2 {'+' if p >= 0 else '-'} {fnum(abs(p))}{v} {'+' if q >= 0 else '-'} {fnum(abs(q))} = 0$.",
        f"Quadratic formula for ${v}^2 + B{v} + C$: ${v} = \\dfrac{{-B \\pm \\sqrt{{B^2 - 4C}}}}{{2}}$ with $B = {fnum(p)}$, $C = {fnum(q)}$.",
        f"Inside the root (discriminant): $B^2 - 4C = {fnum(p * p)} - {fnum(4 * q)} = {fnum(D)}$; $\\sqrt{{{fnum(D)}}} = {fnum(math.sqrt(D))}$.",
        f"${v}_1 = ({fnum(-p)} + {fnum(math.sqrt(D))})/2 = {fnum(roots[0])}$, ${v}_2 = ({fnum(-p)} - {fnum(math.sqrt(D))})/2 = {fnum(roots[1])}$.",
        f"Quick self-check (no need to redo the formula): because ${v}^2 + B{v} + C = ({v} - r_1)({v} - r_2) = {v}^2 - (r_1 + r_2){v} + r_1r_2$, "
        f"the two roots must ADD UP to −B and MULTIPLY to C. "
        f"Sum: ${fnum(roots[0])} + ({fnum(roots[1])}) = {fnum(roots[0] + roots[1])}$ and −B = {fnum(-p)} ✓. "
        f"Product: ${fnum(roots[0])}\\cdot({fnum(roots[1])}) = {fnum(roots[0] * roots[1])}$ and C = {fnum(q)} ✓. "
        "If either check fails, you made a sign slip somewhere.",
    ]
    parts[1].steps = [
        f"Is this a continuous (s) or a discrete (z) polynomial? It is in **{v}**, so the rule is: {rule}.",
        *[f"Pole {fnum(r)}: " + (f"real part {fnum(r)} {'< 0 ✓' if r < 0 else '≥ 0 ✗'}" if v == 's' else f"|{fnum(r)}| = {fnum(abs(r))} {'< 1 ✓' if abs(r) < 1 else '≥ 1 ✗'}") for r in roots],
        f"All poles must pass ⇒ **{'stable' if stable else 'not stable'}**.",
    ]
    return Problem("f_poles", "f_poles", "Poles and stability (s-plane vs z-plane)", difficulty, seed, stmt, parts, sol,
                   f"roots([1 {fnum(p)} {fnum(q)}])", source="Foundation for every stability question",
                   plot=lambda: plots.zplane(roots, title="Poles (unit circle = discrete stability border)"),
                   remedy="Poles = roots of the denominator. s: Re < 0. z: |p| < 1.")


def f_pfe(rng, difficulty, seed):
    K = float(_c(rng, [1.0, 2.0, 4.0, 6.0, 10.0]))
    a = float(_c(rng, [1.0, 2.0, 0.5]))
    if difficulty == 1:
        b = float(_c(rng, [x for x in [3.0, 4.0, 5.0] if x != a]))
        A, B = K / (b - a), K / (a - b)
        stmt = (f"Split $\\dfrac{{{fnum(K)}}}{{(s+{fnum(a)})(s+{fnum(b)})}} = \\dfrac{{A}}{{s+{fnum(a)}}} + \\dfrac{{B}}{{s+{fnum(b)}}}$ "
                "(**cover-up rule**: to get A, cover the factor (s+a), and put s = −a into what is left).")
        parts = [Part("A", "$A$", "num", A, points=1, hint=f"A = {fnum(K)}/(s+{fnum(b)}) evaluated at s = −{fnum(a)}.",
                      explain=f"$A = {fnum(K)}/(-{fnum(a)}+{fnum(b)}) = {fnum(A)}$"),
                 Part("B", "$B$", "num", B, points=1, explain=f"$B = {fnum(K)}/(-{fnum(b)}+{fnum(a)}) = {fnum(B)}$")]
        sol = f"$A = {fnum(A)}$, $B = {fnum(B)}$. Check: put s = 0 on both sides: {fnum(K / (a * b))} = {fnum(A / a + B / b)} ✓"
        parts[0].steps = [
            f"A belongs to the factor $(s + {fnum(a)})$. Its root is where it becomes zero: $s = -{fnum(a)}$.",
            f"**Cover** $(s+{fnum(a)})$ in the original fraction. What remains: $\\dfrac{{{fnum(K)}}}{{s + {fnum(b)}}}$.",
            f"Put $s = -{fnum(a)}$ into what remains: $\\dfrac{{{fnum(K)}}}{{-{fnum(a)} + {fnum(b)}}} = \\dfrac{{{fnum(K)}}}{{{fnum(b - a)}}} = {fnum(A)}$.",
        ]
        parts[1].steps = [
            f"B belongs to $(s + {fnum(b)})$, root $s = -{fnum(b)}$.",
            f"Cover $(s+{fnum(b)})$; what remains: $\\dfrac{{{fnum(K)}}}{{s + {fnum(a)}}}$.",
            f"Put $s = -{fnum(b)}$: $\\dfrac{{{fnum(K)}}}{{-{fnum(b)} + {fnum(a)}}} = \\dfrac{{{fnum(K)}}}{{{fnum(a - b)}}} = {fnum(B)}$.",
            f"Check with $s = 0$: left ${fnum(K)}/({fnum(a)}\\cdot{fnum(b)}) = {fnum(K / (a * b))}$; right $A/{fnum(a)} + B/{fnum(b)} = {fnum(A / a + B / b)}$ ✓.",
        ]
    else:
        A, B = K / a, -K / a
        stmt = (f"Split $\\dfrac{{{fnum(K)}}}{{s(s+{fnum(a)})}} = \\dfrac{{A}}{{s}} + \\dfrac{{B}}{{s+{fnum(a)}}}$. "
                "(This is exactly step 1 of every ZOH problem: G_P(s)/s split into simple pieces.)")
        parts = [Part("A", "$A$ (cover s, put s = 0)", "num", A, points=1, explain=f"$A = {fnum(K)}/(0+{fnum(a)}) = {fnum(A)}$"),
                 Part("B", "$B$ (cover s+a, put s = −a)", "num", B, points=1, explain=f"$B = {fnum(K)}/(-{fnum(a)}) = {fnum(B)}$",
                      misconceptions=[Misc(-B, "cover_up_sign", "Sign: you substitute s = −a, so the remaining factor s becomes −a.")])]
        sol = f"$A = {fnum(A)}$, $B = {fnum(B)}$ ⇒ $\\dfrac{{{fnum(A)}}}{{s}} {'-' if B < 0 else '+'} \\dfrac{{{fnum(abs(B))}}}{{s+{fnum(a)}}}$."
        parts[0].steps = [
            "A belongs to the factor $s$, whose root is $s = 0$.",
            f"Cover $s$; what remains is $\\dfrac{{{fnum(K)}}}{{s + {fnum(a)}}}$.",
            f"Put $s = 0$: $\\dfrac{{{fnum(K)}}}{{{fnum(a)}}} = {fnum(A)}$.",
        ]
        parts[1].steps = [
            f"B belongs to $(s + {fnum(a)})$, root $s = -{fnum(a)}$.",
            f"Cover $(s + {fnum(a)})$; what remains is $\\dfrac{{{fnum(K)}}}{{s}}$.",
            f"Put $s = -{fnum(a)}$: $\\dfrac{{{fnum(K)}}}{{-{fnum(a)}}} = {fnum(B)}$ (the leftover s becomes −{fnum(a)}, hence the minus sign).",
        ]
    return Problem("f_pfe", "f_pfe", "Partial fractions with the cover-up rule", difficulty, seed, stmt, parts, sol,
                   "[r, p, k] = residue(num, den)", source="Foundation for ZOH (exam P2a) and inverse z-transform (P1)",
                   remedy="Cover the factor, substitute its root into the rest.")


def f_laplace(rng, difficulty, seed):
    K = float(_c(rng, [2.0, 1.0, 4.0, 0.5]))
    tau = float(_c(rng, [1.0, 2.0, 4.0, 0.5]))
    t1 = float(_c(rng, [1.0, 2.0, 3.0]))
    y_t = K * (1 - math.exp(-t1 / tau))
    stmt = (f"A first-order system $G(s) = \\dfrac{{{fnum(K)}}}{{{fnum(tau)}s + 1}}$ (gain K, time constant τ) receives a unit step. "
            f"Its step response is $y(t) = K(1 - e^{{-t/\\tau}})$.")
    parts = [Part("pole", "Pole of G(s)", "num", -1 / tau, points=1, explain="τs + 1 = 0 ⇒ s = −1/τ.",
                  misconceptions=[Misc(-tau, "pole_tau", "The pole is −1/τ, not −τ.")]),
             Part("final", "Final value $y(\\infty)$ (= DC gain G(0))", "num", K, points=1,
                  explain="Set s = 0: G(0) = K. A step of height 1 ends at K."),
             Part("yt", f"$y(t)$ at $t = {fnum(t1)}$ s", "num", y_t, points=1,
                  explain=f"${fnum(K)}(1 - e^{{-{fnum(t1)}/{fnum(tau)}}}) = {fnum(y_t)}$ (after one τ: 63 % of the final value).")]
    parts[0].steps = [
        "A pole is a value of s that makes the denominator zero.",
        f"Denominator: ${fnum(tau)}s + 1 = 0$.",
        f"Subtract 1 and divide by {fnum(tau)}: $s = -1/{fnum(tau)} = {fnum(-1 / tau)}$.",
    ]
    parts[1].steps = [
        "After a unit step the output settles at the **DC gain** G(0) (s = 0 means 'constant signals').",
        f"$G(0) = \\dfrac{{{fnum(K)}}}{{{fnum(tau)}\\cdot 0 + 1}} = {fnum(K)}$.",
    ]
    parts[2].steps = [
        f"Use $y(t) = K(1 - e^{{-t/\\tau}})$ with $K = {fnum(K)}$, $\\tau = {fnum(tau)}$, $t = {fnum(t1)}$.",
        f"$t/\\tau = {fnum(t1)}/{fnum(tau)} = {fnum(t1 / tau)}$.",
        f"$e^{{-{fnum(t1 / tau)}}} = {fnum(math.exp(-t1 / tau))}$.",
        f"$1 - {fnum(math.exp(-t1 / tau))} = {fnum(1 - math.exp(-t1 / tau))}$.",
        f"Multiply by K: ${fnum(K)}\\cdot{fnum(1 - math.exp(-t1 / tau))} = {fnum(y_t)}$.",
    ]
    T = tau / 10
    k = np.arange(0, 50)
    y = K * (1 - np.exp(-k * T / tau))
    return Problem("f_laplace", "f_laplace", "Laplace basics: first-order system", difficulty, seed, stmt, parts,
                   f"Pole −1/τ = {fnum(-1 / tau)}, final value K = {fnum(K)}, y({fnum(t1)}) = {fnum(y_t)}.",
                   f"G = tf({K}, [{tau} 1]); step(G); pole(G), dcgain(G)", source="Foundation: G(s), poles, DC gain, step response",
                   plot=lambda: plots.step_compare({"y(t)": list(y)}, "First-order step response", T=T),
                   remedy="Pole −1/τ; final value G(0); 63 % after one time constant.")


def f_feedback(rng, difficulty, seed):
    K = float(_c(rng, [1.0, 2.0, 4.0]))
    a = float(_c(rng, [1.0, 2.0, 0.5]))
    kp = float(_c(rng, [1.0, 2.0, 5.0, 0.5]))
    pole = -(a + kp * K)
    dc = kp * K / (a + kp * K)
    stmt = (f"Plant $G(s) = \\dfrac{{{fnum(K)}}}{{s + {fnum(a)}}}$, P-controller $K_p = {fnum(kp)}$, unit negative feedback. "
            "Closed loop: $G_W = \\dfrac{K_pG}{1 + K_pG}$ (forward path over 1 + loop).")
    parts = [Part("pole", "Closed-loop pole", "num", pole, points=1, hint="Multiply out: K_pK/(s + a + K_pK).",
                  explain=f"$G_W = \\dfrac{{{fnum(kp * K)}}}{{s + {fnum(a)} + {fnum(kp * K)}}}$ ⇒ pole {fnum(pole)} — feedback moved the pole further left (faster).",
                  misconceptions=[Misc(-(a - kp * K), "cl_sign", "Negative feedback ADDS K_pK: the denominator is 1 + K_pG.")]),
             Part("dc", "Steady-state output for a unit step, $G_W(0)$", "num", dc, points=1),
             Part("err", "Remaining steady-state error $1 - G_W(0)$", "num", 1 - dc, points=1,
                  explain="A P-controller on a plant without integrator always leaves an offset; larger K_p ⇒ smaller error. An integrator removes it.")]
    parts[0].steps = [
        f"Open loop (controller times plant): $K_pG = \\dfrac{{{fnum(kp)}\\cdot{fnum(K)}}}{{s + {fnum(a)}}} = \\dfrac{{{fnum(kp * K)}}}{{s + {fnum(a)}}}$.",
        f"Closed loop: $G_W = \\dfrac{{K_pG}}{{1 + K_pG}}$. Multiply top and bottom by $(s + {fnum(a)})$: "
        f"$G_W = \\dfrac{{{fnum(kp * K)}}}{{(s + {fnum(a)}) + {fnum(kp * K)}}}$.",
        f"Simplify the denominator: $s + {fnum(a + kp * K)}$.",
        f"Pole: $s + {fnum(a + kp * K)} = 0$ ⇒ $s = {fnum(pole)}$ (the open-loop pole was −{fnum(a)}).",
    ]
    parts[1].steps = [
        f"Steady state for a step = put $s = 0$ in $G_W = \\dfrac{{{fnum(kp * K)}}}{{s + {fnum(a + kp * K)}}}$.",
        f"$\\dfrac{{{fnum(kp * K)}}}{{{fnum(a + kp * K)}}} = {fnum(dc)}$.",
    ]
    parts[2].steps = [
        "The target is 1 (unit step); the output only reaches $G_W(0)$.",
        f"Error $= 1 - {fnum(dc)} = {fnum(1 - dc)}$.",
    ]
    return Problem("f_feedback", "f_feedback", "Feedback loop basics", difficulty, seed, stmt, parts,
                   f"Pole {fnum(pole)}, DC gain {fnum(dc)}, error {fnum(1 - dc)}.",
                   f"G = tf({K},[1 {a}]); GW = feedback({kp}*G, 1); pole(GW), dcgain(GW)",
                   source="Foundation for G_W(z) (exam P2b) and integral action (P4)", remedy="G_W = K_pG/(1 + K_pG); error = 1 − G_W(0).")


def f_matrix(rng, difficulty, seed):
    l1, l2 = _c(rng, [(0.5, 0.2), (1.0, 0.5), (-1.0, 2.0), (0.8, 0.4), (3.0, 1.0)])
    b = float(_c(rng, [1.0, 2.0, 0.5]))
    M = np.array([[0.0, 1.0], [-l1 * l2, l1 + l2]]) if rng.random() < 0.5 else np.array([[l1, b], [0.0, l2]])
    v = np.array([float(_c(rng, [1.0, 2.0])), float(_c(rng, [0.0, 1.0, -1.0]))])
    det = float(np.linalg.det(M))
    eig = sorted(np.real(np.linalg.eigvals(M)), reverse=True)
    stmt = (f"$$M = {fmat(M)},\\qquad v = {fmat(v.reshape(-1, 1))}$$\n\nFor a 2×2 matrix $\\begin{{bmatrix}}a&b\\\\c&d\\end{{bmatrix}}$: "
            "det = ad − bc; eigenvalues are the roots of $\\lambda^2 - (a+d)\\lambda + \\det = 0$; product $Mv$ = row × column.")
    parts = [Part("Mv", "$Mv$", "vec", list(M @ v), points=1, placeholder="2 numbers",
                  explain="Row 1 · v, row 2 · v."),
             Part("det", "$\\det M$", "num", det, points=1, tol_abs=1e-3),
             Part("eig", "Eigenvalues, largest first", "vec", eig, points=1, placeholder="2 numbers",
                  explain="Eigenvalues of the system matrix G = poles of the discrete system.")]
    if difficulty >= 2 and abs(det) > 1e-9:
        parts.append(Part("inv", "$M^{-1}$ row-wise", "vec", list(np.linalg.inv(M).ravel()), points=1, placeholder="4 numbers",
                          explain="$\\frac{1}{ad-bc}\\begin{bmatrix}d&-b\\\\-c&a\\end{bmatrix}$ — swap a and d, negate b and c, divide by det."))
    a_, b_, c_, d_ = M.ravel()
    mv = M @ v
    tr = a_ + d_
    disc = tr * tr - 4 * det
    parts[0].steps = [
        f"Row times column. Row 1 of M is $[{fnum(a_)}, {fnum(b_)}]$, the vector is $[{fnum(v[0])}, {fnum(v[1])}]$.",
        f"Entry 1: ${fnum(a_)}\\cdot{fnum(v[0])} + {fnum(b_)}\\cdot{fnum(v[1])} = {fnum(mv[0])}$.",
        f"Entry 2 (row 2): ${fnum(c_)}\\cdot{fnum(v[0])} + {fnum(d_)}\\cdot{fnum(v[1])} = {fnum(mv[1])}$.",
    ]
    parts[1].steps = [
        f"$a = {fnum(a_)}, b = {fnum(b_)}, c = {fnum(c_)}, d = {fnum(d_)}$ (top-left, top-right, bottom-left, bottom-right).",
        f"$\\det = ad - bc = {fnum(a_)}\\cdot{fnum(d_)} - {fnum(b_)}\\cdot({fnum(c_)}) = {fnum(a_ * d_)} - ({fnum(b_ * c_)}) = {fnum(det)}$.",
    ]
    parts[2].steps = [
        f"Trace = sum of the diagonal = ${fnum(a_)} + {fnum(d_)} = {fnum(tr)}$; det = {fnum(det)}.",
        f"Eigenvalues solve $\\lambda^2 - {fnum(tr)}\\lambda + {fnum(det)} = 0$.",
        f"Discriminant: ${fnum(tr)}^2 - 4\\cdot{fnum(det)} = {fnum(disc)}$, root $= {fnum(math.sqrt(max(disc, 0)))}$.",
        f"$\\lambda = ({fnum(tr)} \\pm {fnum(math.sqrt(max(disc, 0)))})/2$ ⇒ {fnum(eig[0])} and {fnum(eig[1])}.",
    ]
    if len(parts) > 3:
        parts[3].steps = [
            f"Swap a and d, negate b and c: $\\begin{{bmatrix}}{fnum(d_)} & {fnum(-b_)}\\\\ {fnum(-c_)} & {fnum(a_)}\\end{{bmatrix}}$.",
            f"Divide every entry by det = {fnum(det)} ⇒ {', '.join(fnum(x) for x in np.linalg.inv(M).ravel())} (row-wise).",
        ]
    return Problem("f_matrix", "f_matrix", "2×2 matrices: product, determinant, eigenvalues", difficulty, seed, stmt, parts,
                   f"det = {fnum(det)}, eigenvalues {', '.join(fnum(e) for e in eig)}.",
                   "M = [...]; M*v, det(M), eig(M), inv(M)", source="Foundation for state space (exam P4)",
                   remedy="det = ad − bc; eigenvalues from λ² − trace·λ + det = 0.")


GENERATORS = {
    "f_complex": f_complex,
    "f_poles": f_poles,
    "f_pfe": f_pfe,
    "f_laplace": f_laplace,
    "f_feedback": f_feedback,
    "f_matrix": f_matrix,
}
