"""Chapter 3 generators: ZOH + plant, closed-loop pulse TFs, s↔z mapping, Jury test, w-transform.

Patterns: exam 2016/2017 Problem 2 (ZOH + continuous plant, P-controller, stability, disturbance),
exam 2016/2017 Problem 3 (Jury test + factored polynomial), book Ex. 3.1–3.12, exercise book 3.x.
"""
from __future__ import annotations

import cmath
import math

import numpy as np

from .. import plots
from ..mathutil import (fnum, fvec, jury_table, pmul, poly_z_tex, poly_zinv_tex, tf_zinv_tex, trim,
                        w_transform, z_from_zeta_ratio, zoh_tf, zt_of_s, series_zinv_step)
from .base import Misc, Part, Problem


def _c(rng, xs):
    return xs[int(rng.integers(len(xs)))]


# ------------------------------------------------------------------ ZOH helpers
def plant_spec(rng, difficulty, allow_lead=True):
    """Return dict(kind, num, den, tex, terms, K, a, b, c) for a 'nice' continuous plant."""
    K = float(_c(rng, [1.0, 2.0, 4.0, 5.0, 10.0]))
    a = float(_c(rng, [0.5, 1.0, 2.0, 4.0, 5.0]))
    if difficulty == 1:
        kind = "first"
    elif difficulty == 2:
        kind = _c(rng, ["second", "integr", "lead"] if allow_lead else ["second", "integr"])
    else:
        kind = _c(rng, ["second_zero", "integr", "second", "lead"] if allow_lead else ["second_zero", "integr", "second"])
    if kind == "first":
        num, den = [K], [1.0, a]
        tex = f"\\dfrac{{{fnum(K)}}}{{s + {fnum(a)}}}"
        terms = [("s", K / a, 0.0), ("s", -K / a, -a)]
    elif kind == "second":
        b = float(_c(rng, [x for x in [1.0, 2.0, 3.0, 5.0, 0.5] if x != a]))
        num, den = [K], [1.0, a + b, a * b]
        tex = f"\\dfrac{{{fnum(K)}}}{{(s + {fnum(a)})(s + {fnum(b)})}}"
        terms = [("s", K / (a * b), 0.0), ("s", K / (a * (a - b)), -a), ("s", K / (b * (b - a)), -b)]
    elif kind == "integr":
        num, den = [K], [1.0, a, 0.0]
        tex = f"\\dfrac{{{fnum(K)}}}{{s(s + {fnum(a)})}}"
        terms = [("s2", K / a, 0.0), ("s", -K / a ** 2, 0.0), ("s", K / a ** 2, -a)]
    elif kind == "lead":
        b = float(_c(rng, [-0.25, -0.5, 2.0, 0.5, 3.0]))
        if abs(b - a) < 1e-9:
            b = -0.25
        num, den = [1.0, b], [1.0, a]
        tex = f"\\dfrac{{s {'+' if b >= 0 else '-'} {fnum(abs(b))}}}{{s + {fnum(a)}}}"
        terms = [("s", b / a, 0.0), ("s", (a - b) / a, -a)]
    else:  # second_zero
        b = float(_c(rng, [1.0, 3.0, 0.5]))
        c = float(_c(rng, [x for x in [2.0, 4.0, 5.0, 10.0] if x not in (a, b)]))
        if abs(b - a) < 1e-9:
            b = 3.0 if a != 3.0 else 1.5
        num, den = [K, K * b], [1.0, a + c, a * c]
        tex = f"\\dfrac{{{fnum(K)}(s + {fnum(b)})}}{{(s + {fnum(a)})(s + {fnum(c)})}}"
        terms = [("s", K * b / (a * c), 0.0), ("s", K * (a - b) / (a * (c - a)), -a), ("s", K * (c - b) / (c * (a - c)), -c)]
    return dict(kind=kind, num=num, den=den, tex=tex, terms=terms)


def terms_tex(terms):
    out = []
    for kind, r, p in terms:
        if kind == "s2":
            out.append(f"\\dfrac{{{fnum(r)}}}{{s^2}}")
        elif abs(p) < 1e-12:
            out.append(f"\\dfrac{{{fnum(r)}}}{{s}}")
        else:
            out.append(f"\\dfrac{{{fnum(r)}}}{{s {'+' if p < 0 else '-'} {fnum(abs(p))}}}")
    return " + ".join(out).replace("+ -", "- ")


def terms_z_tex(terms, T):
    out = []
    for kind, r, p in terms:
        if kind == "s2":
            out.append(f"\\dfrac{{{fnum(r)}\\cdot {fnum(T)}\\,z^{{-1}}}}{{(1-z^{{-1}})^2}}")
        else:
            e = math.exp(p * T)
            out.append(f"\\dfrac{{{fnum(r)}}}{{1 - {fnum(e)}\\,z^{{-1}}}}")
    return " + ".join(out).replace("+ -", "- ")


def plant_ztf(spec, T, d=0):
    return zoh_tf(spec["num"], spec["den"], T, delay_samples=d)


# --------------------------------------------------------------------------- 8
def zoh_plant(rng, difficulty, seed):
    spec = plant_spec(rng, difficulty)
    T = float(_c(rng, [0.1, 0.2, 0.25, 0.5, 1.0]))
    d = int(_c(rng, [0, 0, 1, 2])) if difficulty == 3 else 0
    num, den = plant_ztf(spec, T, d)
    den_nofactor = trim(pmul(den, [1.0, -1.0]))
    mis_num, mis_den = [], [Misc(den_nofactor, "zoh_no_factor", "Your denominator still contains (1 − z⁻¹): you computed Z{G_P/s} but forgot to multiply by (1 − z⁻¹).")]
    if spec["kind"] != "lead":
        n_ii, d_ii = zt_of_s(spec["num"], spec["den"], T)
        n_ii = [0.0] * d + [x / d_ii[0] for x in n_ii]
        if len(n_ii) <= len(num):
            n_ii = n_ii + [0.0] * (len(num) - len(n_ii))
            mis_num.append(Misc(n_ii, "zoh_forgot", "These are the coefficients of Z{G_P(s)} (impulse invariance) — the zero-order hold was ignored."))
    dly = f"\\,e^{{-{fnum(d * T)}s}}" if d else ""
    stmt = (f"A continuous-time plant $G_P(s) = {spec['tex']}{dly}$ is driven through a zero-order hold $H_0(s) = (1-e^{{-Ts}})/s$, "
            f"sampling time $T = {fnum(T)}$ s.\n\nDetermine the pulse transfer function $G(z) = (1-z^{{-1}})\\,\\mathcal Z\\{{G_P(s)/s\\}}$ "
            f"in the form $G(z) = \\dfrac{{b_0 + b_1z^{{-1}} + \\dots}}{{1 + a_1z^{{-1}} + \\dots}}$.")
    parts = [
        Part("num", f"Numerator coefficients $[b_0, b_1, \\dots]$ ({len(num)} values, include leading zeros)", "vec", num, points=2,
             hint="Partial fractions of G_P(s)/s, table entries 2/3/4, multiply by (1 − z⁻¹), bring to a common denominator."
                  + (" The dead time e^{−dTs} = e^{−" + fnum(d * T) + "s} is exactly d = " + str(d) + " samples → factor z^{−" + str(d) + "}." if d else ""),
             explain="The ZOH turns the staircase input into a sum of steps; hence the step-response transform $\\mathcal Z\\{G_P/s\\}$ times $(1-z^{-1})$.",
             misconceptions=mis_num, placeholder=f"{len(num)} numbers"),
        Part("den", f"Denominator coefficients $[1, a_1, \\dots]$ ({len(den)} values)", "vec", den, points=1,
             explain="Poles map as $z = e^{p_iT}$; the integrator pole of $1/s$ cancels against $(1-z^{-1})$.",
             misconceptions=mis_den, placeholder=f"{len(den)} numbers"),
    ]
    G1 = sum(num) / sum(den) if abs(sum(den)) > 1e-9 else None
    if G1 is not None:
        parts.append(Part("dc", "Stationary gain $G(z=1)$", "num", G1, points=0.5,
                          explain="The ZOH preserves the DC gain: $G(1) = G_P(0)$."))
    sol = (f"**1. Partial fractions** $\\dfrac{{G_P(s)}}{{s}} = {terms_tex(spec['terms'])}$\n\n"
           f"**2. Table** (entries 2, 3, 4 with $T = {fnum(T)}$): $\\mathcal Z\\{{G_P/s\\}} = {terms_z_tex(spec['terms'], T)}$\n\n"
           f"**3. Multiply by $(1-z^{{-1}})$** and combine over the common denominator"
           + (f", then **4. dead time** $z^{{-{d}}}$" if d else "") + ":\n\n"
           f"$$G(z) = {tf_zinv_tex(num, den)}$$\n\n"
           f"Poles: $z = {', '.join(fnum(complex(r)) for r in np.roots(den))}$ = $e^{{p_iT}}$ of the plant poles.")
    numstr = " ".join(fnum(x) for x in spec["num"])
    denstr = " ".join(fnum(x) for x in spec["den"])
    matlab = (f"T = {T};\nGp = tf([{numstr}], [{denstr}]{', ' + chr(39) + 'InputDelay' + chr(39) + ', ' + fnum(d * T) if d else ''});\n"
              "Gz = c2d(Gp, T, 'zoh')\n[nz, dz] = tfdata(Gz, 'v');  % coefficients in z (= z^-1 form after dividing by z^n)\n"
              "Gz_inv = filt(nz, dz, T)   % display in z^-1")
    after = []
    for kind_, r_, p_ in spec["terms"]:
        if kind_ == "s2":
            after.append(f"$\\dfrac{{{fnum(r_ * T)}\\,z^{{-1}}}}{{1 - z^{{-1}}}}$ (the $1/s^2$ term keeps one $(1-z^{{-1}})$ in its denominator)")
        elif abs(p_) < 1e-12:
            after.append(f"${fnum(r_)}$ (the $1/s$ term: $(1-z^{{-1}})\\cdot\\frac{{{fnum(r_)}}}{{1-z^{{-1}}}}$ = just the constant)")
        else:
            after.append(f"$\\dfrac{{{fnum(r_)}(1 - z^{{-1}})}}{{1 - {fnum(math.exp(p_ * T))}z^{{-1}}}}$")
    zpoles = [math.exp(p_ * T) for k_, r_, p_ in spec["terms"] if k_ == "s" and abs(p_) > 1e-12]
    if spec["kind"] == "integr":
        zpoles = [1.0] + zpoles
    parts[0].steps = [
        f"Write the plant divided by s: $\\dfrac{{G_P(s)}}{{s}}$. (Why: the hold makes the plant see steps; a step is $1/s$.)",
        f"Partial fractions (cover-up rule, see Foundations): $\\dfrac{{G_P(s)}}{{s}} = {terms_tex(spec['terms'])}$.",
        "Table (Formelsammlung p. 2): $\\frac{1}{s} \\to \\frac{1}{1-z^{-1}}$, $\\frac{1}{s+a} \\to \\frac{1}{1-e^{-aT}z^{-1}}$, $\\frac{1}{s^2} \\to \\frac{Tz^{-1}}{(1-z^{-1})^2}$.",
        f"With T = {fnum(T)}: $\\mathcal Z\\{{G_P/s\\}} = {terms_z_tex(spec['terms'], T)}$.",
        "Multiply every term by $(1 - z^{-1})$: " + "; ".join(after) + ".",
        f"Put everything over the common denominator $\\prod(1 - e^{{p_iT}}z^{{-1}})$ = ${poly_zinv_tex(den)}$ and multiply out the numerator.",
        f"Collect powers of $z^{{-1}}$ in the numerator ⇒ $[{', '.join(fnum(x) for x in num[d:])}]$." + (f" Dead time: multiply by $z^{{-{d}}}$ ⇒ shift right by {d}: $[{', '.join(fnum(x) for x in num)}]$." if d else ""),
        "Check: MATLAB `c2d(Gp, T, 'zoh')` must give the same numbers.",
    ]
    parts[1].steps = [
        "The poles of G(z) are the plant poles mapped by $z = e^{p\\,T}$ (plus z = 1 for an integrator).",
        f"Plant poles → z-poles: {', '.join(fnum(z_) for z_ in zpoles)}.",
        "Denominator = product of $(1 - z_i z^{-1})$: " + " · ".join(f"$(1 - {fnum(z_)}z^{{-1}})$" for z_ in zpoles) + f" = ${poly_zinv_tex(den)}$.",
        f"Coefficients: $[{', '.join(fnum(x) for x in den)}]$.",
    ]
    if len(parts) > 2:
        parts[2].steps = ["Put z = 1 (every $z^{-1}$ becomes 1): sum of numerator coefficients / sum of denominator coefficients.",
                          f"{fnum(sum(num))} / {fnum(sum(den))} = {fnum(G1)} — equals $G_P(0)$ (the hold keeps the DC gain)."]
    return Problem("zoh_plant", "zoh_plant", "Pulse transfer function of ZOH + plant", difficulty, seed, stmt, parts, sol, matlab,
                   source="Pattern: Exam 2016/2017 Problem 2a (3 P); Book Ex. 3.1, 3.6; Exercise book 3.1, 3.2",
                   plot=lambda: plots.zplane(np.roots(den), np.roots(trim(num[next(i for i, x in enumerate(num) if abs(x) > 1e-12):])) if any(abs(x) > 1e-12 for x in num[1:]) else [], title="G(z) poles/zeros"),
                   remedy="G(z) = (1 − z⁻¹)·Z{G_P(s)/s}.")


# --------------------------------------------------------------------------- 9
def closed_loop_P(rng, difficulty, seed):
    spec = plant_spec(rng, min(difficulty, 2), allow_lead=False)
    T = float(_c(rng, [0.1, 0.2, 0.25, 0.5, 1.0]))
    d = 1 if (difficulty == 3 and rng.random() < 0.5) else 0
    B, A = plant_ztf(spec, T, d)
    Kp = float(_c(rng, [0.5, 1.0, 2.0, 5.0, 0.2]))
    n = max(len(A), len(B))
    Ap = A + [0.0] * (n - len(A))
    Bp = B + [0.0] * (n - len(B))
    den_cl = [x + Kp * y for x, y in zip(Ap, Bp)]
    den_w = [x - Kp * y for x, y in zip(Ap, Bp)]
    num_cl = [Kp * y for y in Bp]
    poles = np.roots(den_cl)
    rho = float(max(abs(poles)))
    stable = rho < 1 - 1e-9
    opts = ["asymptotically stable", "unstable / at the stability limit"]
    dist_opts = [
        "No — d is not sampled before entering the continuous plant; only Y(z) = (G_w G_z D)(z)/(1 + G_D G(z)) exists, D(z) cannot be factored out",
        "Yes — G_d(z) = G_z(z) / (1 + G_D(z) G(z))",
        "Yes — G_d(z) = G_w G_z(z) / (1 + G_D(z) G(z))",
    ]
    dly = f"\\,e^{{-{fnum(d * T)}s}}" if d else ""
    stmt = (f"Plant $G_w(s) = {spec['tex']}{dly}$ with ZOH, $T = {fnum(T)}$ s, so that\n\n$$G(z) = {tf_zinv_tex(B, A)}$$\n\n"
            f"A digital P-controller $G_D = {fnum(Kp)}$ closes a unit negative-feedback loop. "
            "A disturbance $d$ acts through a continuous block $G_z(s)$ and is added to the plant input *after* the hold (exam block diagram).")
    parts = [
        Part("num", f"(a) $G_W(z) = Y/W$: numerator coefficients ({n} values, $z^{{-1}}$ form)", "vec", num_cl, points=1,
             misconceptions=[Misc(Bp, "cl_num_no_gain", "The controller gain is missing in the numerator.")], placeholder=f"{n} numbers",
             explain="$G_W = \\dfrac{G_D G}{1+G_D G} = \\dfrac{K_p B}{A + K_p B}$."),
        Part("den", f"(a) $G_W(z)$: denominator coefficients ({n} values)", "vec", den_cl, points=1,
             misconceptions=[Misc(den_w, "cl_sign", "You used A − K_p B; negative feedback gives A + K_p B.")], placeholder=f"{n} numbers"),
        Part("rho", "(b) Largest closed-loop pole magnitude $\\max|z_i|$", "num", rho, points=0.5,
             explain=f"Closed-loop poles: {', '.join(fnum(complex(p)) for p in poles)}."),
        Part("stab", "(b) The closed loop is …", "choice", opts[0] if stable else opts[1], options=opts, points=0.5,
             explain="Asymptotically stable ⇔ all closed-loop poles strictly inside the unit circle (Def. 3.1)."),
    ]
    if stable:
        parts.append(Part("ss", "(c) Steady-state output for a unit reference step, $G_W(1)$", "num", sum(num_cl) / sum(den_cl), points=0.5,
                          explain="FVT with W(z) = 1/(1 − z⁻¹) ⇒ y(∞) = G_W(1). A P-controller on a type-0 plant leaves an offset; with an integrating plant G_W(1) = 1."))
    if difficulty >= 2:
        parts.append(Part("dist", "(d) Can a disturbance pulse transfer function $G_d(z) = Y(z)/D(z)$ be written?", "choice", dist_opts[0],
                          options=list(rng.permutation(dist_opts)), points=1,
                          explain="d enters an unsampled continuous path: Y(z) contains $\\mathcal Z\\{G_wG_zD\\}$, which does not factor into (something)·D(z) (book eq. 3.42). Grader comment 2016: 'No, because there is no input sampler for d' ✓."))
    sol = (f"$G_D(z)G(z) = \\dfrac{{{fnum(Kp)}\\,({poly_zinv_tex(B)})}}{{{poly_zinv_tex(A)}}}$\n\n"
           f"$$G_W(z) = \\dfrac{{G_DG}}{{1+G_DG}} = {tf_zinv_tex(num_cl, den_cl)}$$\n\n"
           f"Characteristic polynomial (in z): ${poly_z_tex(den_cl)} = 0$ → poles {', '.join(fnum(complex(p)) for p in poles)}, "
           f"max |z| = {fnum(rho)} ⇒ **{'stable' if stable else 'NOT asymptotically stable'}**.")
    matlab = (f"T = {T}; Gp = tf([{' '.join(fnum(x) for x in spec['num'])}], [{' '.join(fnum(x) for x in spec['den'])}]{', ' + chr(39) + 'InputDelay' + chr(39) + ', ' + fnum(d * T) if d else ''});\n"
              f"G = c2d(Gp, T, 'zoh');\nGW = feedback({fnum(Kp)}*G, 1)\npole(GW), abs(pole(GW))\nstep(GW)")
    y = series_zinv_step(num_cl, den_cl, 25)
    parts[0].steps = [
        f"Read G(z) = B/A: numerator B = $[{', '.join(fnum(x) for x in Bp)}]$, denominator A = $[{', '.join(fnum(x) for x in Ap)}]$ (powers $z^0, z^{{-1}}, \\dots$).",
        "Closed loop: $G_W = \\dfrac{K_pG}{1 + K_pG} = \\dfrac{K_pB/A}{1 + K_pB/A}$; multiply top and bottom by A ⇒ $G_W = \\dfrac{K_pB}{A + K_pB}$.",
        f"Numerator $K_p\\cdot B = {fnum(Kp)}\\cdot[{', '.join(fnum(x) for x in Bp)}] = [{', '.join(fnum(x) for x in num_cl)}]$.",
    ]
    parts[1].steps = [
        f"Denominator = A + K_p·B, entry by entry (same power of $z^{{-1}}$):",
        *[f"$z^{{-{i}}}$: {fnum(Ap[i])} + {fnum(Kp)}·({fnum(Bp[i])}) = {fnum(den_cl[i])}" for i in range(n)],
    ]
    parts[2].steps = [
        f"Multiply the denominator by $z^{{{n - 1}}}$ to get positive powers: ${poly_z_tex(den_cl)} = 0$.",
        "Find its roots (quadratic formula, or MATLAB `roots`): " + ", ".join(fnum(complex(p_)) for p_ in poles) + ".",
        "Magnitudes: " + ", ".join(fnum(abs(p_)) for p_ in poles) + f" ⇒ largest = {fnum(rho)}.",
    ]
    parts[3].steps = [
        f"Rule (discrete): stable ⇔ every closed-loop pole has |z| < 1.",
        f"Largest magnitude {fnum(rho)} {'< 1' if stable else '≥ 1'} ⇒ **{'asymptotically stable' if stable else 'not asymptotically stable'}**. Write this reason in the exam (a bare 'checked with rltool' got 0 P in 2017).",
    ]
    for prt in parts[4:]:
        if prt.key == "ss":
            prt.steps = ["Final value for a unit step = $G_W(1)$ (put z = 1).",
                         f"Sum of numerator coefficients {fnum(sum(num_cl))} / sum of denominator coefficients {fnum(sum(den_cl))} = {fnum(sum(num_cl) / sum(den_cl))}."]
        if prt.key == "dist":
            prt.steps = ["Look where d enters: through the CONTINUOUS block $G_z(s)$ into the continuous plant — there is no sampler on d.",
                         "A pulse transfer function needs a sampled input. Without it the output only contains $\\mathcal Z\\{G_wG_zD\\}$, which cannot be written as (something)·D(z).",
                         "Answer: **No** — only $Y(z) = \\dfrac{(G_wG_zD)(z)}{1 + G_D(z)G(z)}$ for a specific disturbance."]
    return Problem("closed_loop_P", "closed_loop", "Closed loop with P-controller: G_W(z), stability, disturbance", difficulty, seed,
                   stmt, parts, sol, matlab, source="Pattern: Exam 2016/2017 Problem 2b–d (4 P); Book Ex. 3.6, 3.8",
                   plot=lambda: plots.step_compare({"y(k), unit step w": y}, "Closed-loop step response"),
                   remedy="G_W = K B/(A + K B); stability from the roots of A + K B.")


# -------------------------------------------------------------------------- 10
_SAMPLER_CASES = [
    ("Sampler in the error path; G(s) output is sampled; the SAMPLED output y(kT) is fed back through H(s) (H sees a sampled input).",
     "Y = G(z)·W(z) / (1 + G(z)·H(z))"),
    ("Samplers in the error path AND between G1 and G2; the continuous output y(t) is fed back through H(s).",
     "Y = G1(z)·G2(z)·W(z) / (1 + G1(z)·G2H(z))"),
    ("NO sampler in the error path; the signal is sampled only between G1(s) and G2(s); continuous y(t) fed back through H(s).",
     "Y = G2(z)·G1W(z) / (1 + G1G2H(z))"),
    ("No sampler in the forward path at all; output sampled; feedback through a sampler and H(s).",
     "Y = GW(z) / (1 + GH(z))"),
    ("Sampler in the error path; continuous y(t) fed back through H(s) (no sampler in the feedback).",
     "Y = G(z)·W(z) / (1 + GH(z))"),
]


def sampler_config(rng, difficulty, seed):
    i = int(rng.integers(len(_SAMPLER_CASES)))
    desc, ans = _SAMPLER_CASES[i]
    opts = [c[1] for c in _SAMPLER_CASES]
    parts = [Part("expr", "Which output expression is correct?", "choice", ans, options=list(rng.permutation(opts)), points=1,
                  explain="Rule: blocks connected WITHOUT a sampler in between must be transformed together (G₁G₂(z) ≠ G₁(z)G₂(z)); "
                          "if the input W is not sampled before the first block, only the product GW(z) exists.")]
    return Problem("sampler_config", "closed_loop", "Where are the samplers? Closed-loop pulse TFs", difficulty, seed,
                   f"Feedback configuration (formula sheet p. 6): {desc}", parts,
                   f"Correct: **{ans}**. Starred-signal algebra: star only products that are actually sampled.", "",
                   source="Book Sec. 3.5.3–3.5.4, Ex. 3.4/3.5; Exercise book 3.5–3.7",
                   remedy="G₁(z)G₂(z) ≠ G₁G₂(z): a sampler between blocks lets you multiply z-transforms.")


# -------------------------------------------------------------------------- 11
def pid_discrete(rng, difficulty, seed):
    Kp = float(_c(rng, [1.0, 2.0, 0.5, 4.0]))
    TN = float(_c(rng, [1.0, 2.0, 5.0, 0.5]))
    TV = float(_c(rng, [0.1, 0.2, 0.5, 0.0]))
    T = float(_c(rng, [0.1, 0.2, 0.05]))
    d0 = Kp * (1 + TV / T)
    d1 = Kp * (T / TN - 2 * TV / T - 1)
    d2 = Kp * TV / T
    stmt = (f"Continuous PID: $u(t) = K_p\\left[e + \\frac{{1}}{{T_N}}\\int e\\,d\\tau + T_V\\dot e\\right]$ with "
            f"$K_p = {fnum(Kp)}$, $T_N = {fnum(TN)}$ s, $T_V = {fnum(TV)}$ s, $T = {fnum(T)}$ s.\n\n"
            "Discretise with the **Euler (rectangle) rule** for the integral and the **backward difference** for the derivative: "
            "$G_D(z) = \\dfrac{d_0 + d_1z^{-1} + d_2z^{-2}}{1-z^{-1}}$.")
    parts = [Part("d", "$[d_0, d_1, d_2]$", "vec", [d0, d1, d2], points=3,
                  explain="Formula sheet p. 7: $d_0 = K_p(1+T_V/T)$, $d_1 = K_p(T/T_N - 2T_V/T - 1)$, $d_2 = K_pT_V/T$.",
                  placeholder="3 numbers"),
             Part("vel", "Velocity algorithm: coefficient of $e(k)$ in $\\Delta u(k)$", "num", d0, points=1,
                  explain="$\\Delta u(k) = u(k) - u(k-1) = d_0e(k) + d_1e(k-1) + d_2e(k-2)$ — the same $d_i$.")]
    sol = (f"$d_0 = {fnum(Kp)}(1 + {fnum(TV)}/{fnum(T)}) = {fnum(d0)}$, "
           f"$d_1 = {fnum(Kp)}({fnum(T)}/{fnum(TN)} - 2\\cdot{fnum(TV)}/{fnum(T)} - 1) = {fnum(d1)}$, $d_2 = {fnum(d2)}$.\n\n"
           "Position algorithm: $u(k) = u(k-1) + d_0e(k) + d_1e(k-1) + d_2e(k-2)$. "
           "⚠ The formula sheet's *trapezoid* variant has typos — the book (eq. 3.48) gives "
           "$z^2$-coefficient $K_p(1 + T_V/T + T/(2T_N))$ and constant $K_pT_V/T$.")
    return Problem("pid_discrete", "closed_loop", "Discrete PID (position / velocity algorithm)", difficulty, seed, stmt, parts, sol,
                   f"Kp={Kp}; TN={TN}; TV={TV}; T={T};\nd0 = Kp*(1+TV/T); d1 = Kp*(T/TN-2*TV/T-1); d2 = Kp*TV/T;\nGD = filt([d0 d1 d2],[1 -1],T)",
                   source="Book Sec. 3.5.6; Formelsammlung p. 7", remedy="Euler integral + backward derivative ⇒ d₀, d₁, d₂.")


# -------------------------------------------------------------------------- 12
def mapping_sz(rng, difficulty, seed):
    variant = _c(rng, ["spole", "zeta_ratio", "zeta_wd"] if difficulty > 1 else ["spole", "zeta_ratio"])
    if variant == "spole":
        sig = float(_c(rng, [1.0, 2.0, 0.5, 4.0]))
        wd = float(_c(rng, [2.0, 3.0, 1.0, 5.0]))
        T = float(_c(rng, [0.1, 0.2, 0.25]))
        z = cmath.exp(complex(-sig, wd) * T)
        stmt = f"Map the s-plane pole $s = -{fnum(sig)} + j{fnum(wd)}$ to the z-plane, $T = {fnum(T)}$ s."
        parts = [
            Part("mag", "$|z|$", "num", abs(z), points=1, explain=f"$|z| = e^{{\\sigma T}} = e^{{-{fnum(sig * T)}}} = {fnum(abs(z))}$",
                 misconceptions=[Misc(math.exp(-sig), "map_deg_rad", "Forgot to multiply by T.")]),
            Part("ang", "$\\arg z$ in degrees", "num", math.degrees(cmath.phase(z)), points=1,
                 explain=f"$\\arg z = \\omega T = {fnum(wd * T)}$ rad $= {fnum(math.degrees(wd * T))}°$",
                 misconceptions=[Misc(wd * T, "map_deg_rad", "That is the angle in radians — convert to degrees.")]),
            Part("re", "$\\mathrm{Re}\\,z$", "num", z.real, points=0.5),
            Part("im", "$\\mathrm{Im}\\,z$", "num", z.imag, points=0.5),
        ]
        sol = f"$z = e^{{sT}} = e^{{-{fnum(sig * T)}}}\\,e^{{j{fnum(wd * T)}}} = {fnum(z)}$"
        parts[0].steps = [f"$s = \\sigma + j\\omega$ with $\\sigma = -{fnum(sig)}$, $\\omega = {fnum(wd)}$. Mapping $z = e^{{sT}} = e^{{\\sigma T}}\\cdot e^{{j\\omega T}}$.",
                          f"Magnitude from the real part only: $e^{{\\sigma T}} = e^{{-{fnum(sig)}\\cdot{fnum(T)}}} = e^{{-{fnum(sig * T)}}} = {fnum(abs(z))}$."]
        parts[1].steps = [f"Angle from the imaginary part: $\\omega T = {fnum(wd)}\\cdot{fnum(T)} = {fnum(wd * T)}$ rad.",
                          f"Degrees: ${fnum(wd * T)}\\cdot 180/\\pi = {fnum(math.degrees(wd * T))}°$."]
        parts[2].steps = [f"Re = |z|·cos(angle) = {fnum(abs(z))}·cos({fnum(wd * T)} rad) = {fnum(z.real)}."]
        parts[3].steps = [f"Im = |z|·sin(angle) = {fnum(abs(z))}·sin({fnum(wd * T)} rad) = {fnum(z.imag)}."]
        extra = [([z, z.conjugate()], "rx", "z-poles")]
    elif variant == "zeta_ratio":
        zeta = float(_c(rng, [0.5, 0.6, 0.7, math.sqrt(2) / 2, 0.4]))
        N = int(_c(rng, [8, 10, 12, 6]))
        mag, ang, z = z_from_zeta_ratio(zeta, 1 / N)
        stmt = (f"Dominant closed-loop poles with damping ratio $\\zeta = {fnum(zeta)}$ and sampling frequency "
                f"$\\omega_s = {N}\\,\\omega_d$ are required. Compute them in the z-plane.")
        wrong_mag = math.exp(-2 * math.pi * zeta * (1 / N))
        parts = [
            Part("mag", "$|z_{1,2}|$", "num", mag, points=1,
                 explain="$|z| = \\exp\\left[-\\dfrac{2\\pi\\zeta}{\\sqrt{1-\\zeta^2}}\\dfrac{\\omega_d}{\\omega_s}\\right]$",
                 misconceptions=[Misc(wrong_mag, "map_wn_vs_wd", "You dropped √(1−ζ²): the ratio is ω_d/ω_s, and ζω_n = ζω_d/√(1−ζ²).")]),
            Part("ang", "$\\arg z_1$ in degrees", "num", math.degrees(ang), points=1, explain=f"$\\arg z = 2\\pi\\,\\omega_d/\\omega_s = 360°/{N}$"),
            Part("reim", "$[\\mathrm{Re}\\,z_1,\\ \\mathrm{Im}\\,z_1]$", "vec", [z.real, z.imag], points=1, placeholder="2 numbers"),
        ]
        sol = (f"$|z| = \\exp(-2\\pi\\cdot{fnum(zeta)}/\\sqrt{{1-{fnum(zeta)}^2}}\\cdot\\tfrac{{1}}{{{N}}}) = {fnum(mag)}$, "
               f"$\\arg z = 360°/{N} = {fnum(math.degrees(ang))}°$ ⇒ $z_{{1,2}} = {fnum(z.real)} \\pm j{fnum(z.imag)}$ (cf. Book Ex. 4.4: ζ=0.5, N=10 → 0.5629 ± j0.4090).")
        expo = -2 * math.pi * zeta / math.sqrt(1 - zeta ** 2) / N
        parts[0].steps = [f"$\\omega_s = {N}\\omega_d$ ⇒ $\\omega_d/\\omega_s = 1/{N}$.",
                          f"$\\sqrt{{1-\\zeta^2}} = \\sqrt{{1 - {fnum(zeta)}^2}} = {fnum(math.sqrt(1 - zeta ** 2))}$.",
                          f"Exponent: $-2\\pi\\cdot{fnum(zeta)}/{fnum(math.sqrt(1 - zeta ** 2))}\\cdot\\tfrac{{1}}{{{N}}} = {fnum(expo)}$.",
                          f"$|z| = e^{{{fnum(expo)}}} = {fnum(mag)}$."]
        parts[1].steps = [f"Angle $= 2\\pi\\,\\omega_d/\\omega_s = 360°/{N} = {fnum(math.degrees(ang))}°$."]
        parts[2].steps = [f"Re = {fnum(mag)}·cos({fnum(math.degrees(ang))}°) = {fnum(z.real)} (DEGREE mode).",
                          f"Im = {fnum(mag)}·sin({fnum(math.degrees(ang))}°) = {fnum(z.imag)}."]
        extra = [([z, z.conjugate()], "rx", "z₁,₂")]
    else:
        zeta = float(_c(rng, [0.5, 0.6, 0.7]))
        wd = float(_c(rng, [math.sqrt(3), 2.0, 1.0, 3.0]))
        T = float(_c(rng, [0.4, 0.2, 0.25, 0.5]))
        wn = wd / math.sqrt(1 - zeta ** 2)
        z = cmath.exp(complex(-zeta * wn, wd) * T)
        zw = cmath.exp(complex(-zeta * wd, wd) * T)
        stmt = f"Dominant poles: $\\zeta = {fnum(zeta)}$, damped frequency $\\omega_d = {fnum(wd)}$ rad/s, sampling time $T = {fnum(T)}$ s. Compute $z_{{1,2}}$."
        parts = [
            Part("wn", "$\\omega_n$", "num", wn, points=0.5, explain="$\\omega_n = \\omega_d/\\sqrt{1-\\zeta^2}$"),
            Part("reim", "$[\\mathrm{Re}\\,z_1,\\ \\mathrm{Im}\\,z_1]$", "vec", [z.real, z.imag], points=1.5,
                 misconceptions=[Misc([zw.real, zw.imag], "map_wn_vs_wd", "You used ζω_d instead of ζω_n for the real part.")],
                 placeholder="2 numbers"),
        ]
        sol = (f"$s = -\\zeta\\omega_n \\pm j\\omega_d = -{fnum(zeta * wn)} \\pm j{fnum(wd)}$ ⇒ $z = e^{{sT}} = {fnum(z)}$ "
               "(Exercise book Problem 4.6: ζ=0.5, ω_d=√3, T=0.4 → 0.5158 ± j0.4281).")
        parts[0].steps = [f"$\\omega_d = \\omega_n\\sqrt{{1-\\zeta^2}}$ ⇒ $\\omega_n = \\omega_d/\\sqrt{{1-\\zeta^2}} = {fnum(wd)}/{fnum(math.sqrt(1 - zeta ** 2))} = {fnum(wn)}$."]
        parts[1].steps = [f"s-pole: $s = -\\zeta\\omega_n + j\\omega_d = -{fnum(zeta * wn)} + j{fnum(wd)}$.",
                          f"$|z| = e^{{-\\zeta\\omega_nT}} = e^{{-{fnum(zeta * wn * T)}}} = {fnum(abs(z))}$; angle $= \\omega_dT = {fnum(wd * T)}$ rad.",
                          f"Re = {fnum(abs(z))}·cos({fnum(wd * T)}) = {fnum(z.real)}, Im = {fnum(abs(z))}·sin({fnum(wd * T)}) = {fnum(z.imag)} (RADIAN mode)."]
        extra = [([z, z.conjugate()], "rx", "z₁,₂")]
    return Problem("mapping_sz", "mapping", "s-plane ↔ z-plane mapping", difficulty, seed, stmt, parts, sol,
                   "T = 0.2; s = -1+2j; z = exp(s*T); abs(z), angle(z)*180/pi\n% damping lines: zgrid", source="Book Sec. 3.6, Ex. 3.7, 4.4, 4.5",
                   plot=lambda: plots.zplane(extra=extra, title="Desired pole location"),
                   remedy="z = e^{sT}: |z| = e^{σT}, arg z = ω_d T.")


# -------------------------------------------------------------------------- 13
def _random_cubic(rng, want_stable):
    for _ in range(200):
        if rng.random() < 0.5:
            r = list(rng.uniform(-0.95, 0.95, 3))
        else:
            rad = rng.uniform(0.3, 0.95)
            th = rng.uniform(0.3, 2.8)
            r = [rad * cmath.exp(1j * th), rad * cmath.exp(-1j * th), rng.uniform(-0.9, 0.9)]
        if not want_stable:
            j = int(rng.integers(3)) if all(np.isreal(r)) else 2
            r[j] = float(_c(rng, [1.2, -1.15, 1.4, -1.3, 1.05]))
        c = np.round(np.real(np.poly(r)), 2)
        if rng.random() < 0.15:
            c[-1] = 0.0  # a0 = 0 like exam 2017
        J = jury_table(c)
        if J["stable"] == want_stable:
            return c, J
    return np.array([1, 0.2, -0.5, 0.1]), jury_table([1, 0.2, -0.5, 0.1])


def _jury_md(J):
    n = J["n"]
    head = "| row | " + " | ".join(f"z^{i}" for i in range(n + 1)) + " |\n|---|" + "---|" * (n + 1) + "\n"
    lines = []
    letters = "abcdefg"
    for i, r in enumerate(J["rows"]):
        L = letters[i]
        lines.append(f"| {L} | " + " | ".join(fnum(x) for x in r) + " |" + " |" * (n + 1 - len(r)))
        lines.append(f"| {L} rev | " + " | ".join(fnum(x) for x in r[::-1]) + " |" + " |" * (n + 1 - len(r)))
    return head + "\n".join(lines)


def jury_cubic(rng, difficulty, seed):
    want = bool(rng.random() < 0.5)
    c, J = _random_cubic(rng, want)
    a = list(c[::-1])  # a0..a3
    b = J["rows"][1]
    b_wrong = [a[0] * a[3 - k] - a[3] * a[k] for k in range(3)]
    p1, pm1 = J["P1"], J["Pm1"]
    Pminus1 = float(np.polyval(c, -1.0))
    stable = J["stable"]
    opts = ["asymptotically stable", "not asymptotically stable"]
    inner_ok = all(cd[2] for cd in J["conds"][2:])
    outer_fail = not all(cd[2] for cd in J["conds"][:2])
    stmt = f"Examine the stability of a system with the characteristic polynomial\n\n$$P(z) = {poly_z_tex(c)}$$\n\nusing the **Jury stability test**."
    parts = [
        Part("p1", "$P(1)$", "num", p1, points=0.5, explain="Sum of all coefficients."),
        Part("pm1", "$(-1)^3P(-1)$", "num", pm1, points=1,
             explain=f"$P(-1) = {fnum(Pminus1)}$, times $(-1)^3 = -1$ ⇒ ${fnum(pm1)}$.",
             misconceptions=[Misc(Pminus1, "jury_forgot_sign_factor", "That is P(−1) itself — multiply by (−1)ⁿ = −1 for n = 3.")] if abs(Pminus1 - pm1) > 1e-6 else []),
        Part("b", "Third Jury row $[b_0, b_1, b_2]$ with $b_k = a_0a_k - a_3a_{3-k}$", "vec", b, points=2,
             hint="Row 1: a₀ a₁ a₂ a₃ (z⁰ first). Row 2: reversed. b_k = det[[a₀, a_{n−k}], [a_n, a_k]].",
             explain=f"$a = {fvec(a)}$ ⇒ $b_0 = a_0^2 - a_3^2$, $b_1 = a_0a_1 - a_3a_2$, $b_2 = a_0a_2 - a_3a_1$.",
             misconceptions=[Misc(b_wrong, "jury_b_formula", "Your b_k = a₀a_{n−k} − a_n a_k has the determinant columns swapped.")],
             placeholder="3 numbers"),
        Part("verdict", "Verdict", "choice", opts[0] if stable else opts[1], options=opts, points=1.5,
             explain="Stable iff ALL: P(1) > 0, (−1)ⁿP(−1) > 0, |a₀| < |a₃|, |b₀| > |b₂|.",
             misconceptions=[Misc(opts[0], "jury_incomplete", "The |a₀|<|a₃| and |b₀|>|b₂| checks pass, but P(1) or (−1)ⁿP(−1) fails — all conditions are needed.")]
             if (not stable and inner_ok and outer_fail) else []),
    ]
    cond_md = "\n".join(f"- ${name}$: {('%s' % fnum(val)) if not isinstance(val, tuple) else fnum(val[0]) + ' vs ' + fnum(val[1])} → {'✅' if ok else '❌'}"
                        for name, val, ok in J["conds"])
    roots = np.roots(c)
    sol = (f"$a_0..a_3 = {fvec(a)}$\n\n{_jury_md(J)}\n\nConditions:\n{cond_md}\n\n"
           f"⇒ **{'asymptotically stable' if stable else 'NOT asymptotically stable'}** "
           f"(check: roots {', '.join(fnum(complex(r), 3) for r in roots)}, max |z| = {fnum(max(abs(roots)))}).")
    matlab = (f"P = [{' '.join(fnum(x) for x in c)}];\nabs(roots(P))   % check\n"
              "a = fliplr(P);           % a0 ... an\nn = numel(a)-1; b = a(1)*a(1:n) - a(end)*a(end:-1:2)   % b_k = a0 a_k - an a_{n-k}")
    a0, a1, a2, a3 = a
    parts[0].steps = [
        f"Read the coefficients: $a_3 = {fnum(a3)}$ (z³), $a_2 = {fnum(a2)}$ (z²), $a_1 = {fnum(a1)}$ (z), $a_0 = {fnum(a0)}$ (constant).",
        f"P(1): put z = 1 ⇒ all powers are 1 ⇒ sum of coefficients: {fnum(a3)} + ({fnum(a2)}) + ({fnum(a1)}) + ({fnum(a0)}) = {fnum(p1)}.",
        f"Condition P(1) > 0: {'✓ satisfied' if p1 > 0 else '✗ violated'}.",
    ]
    parts[1].steps = [
        "Put z = −1: (−1)³ = −1, (−1)² = +1, (−1)¹ = −1.",
        f"P(−1) = −{fnum(a3)} + ({fnum(a2)}) − ({fnum(a1)}) + ({fnum(a0)}) = {fnum(Pminus1)}.",
        f"n = 3 ⇒ multiply by (−1)³ = −1: (−1)³P(−1) = {fnum(pm1)}.",
        f"Condition > 0: {'✓' if pm1 > 0 else '✗'}.",
    ]
    parts[2].steps = [
        f"Row 1 (z⁰ first): a₀ a₁ a₂ a₃ = {fnum(a0)}, {fnum(a1)}, {fnum(a2)}, {fnum(a3)}. Row 2 = reversed: {fnum(a3)}, {fnum(a2)}, {fnum(a1)}, {fnum(a0)}.",
        f"First check $|a_0| < |a_3|$: {fnum(abs(a0))} < {fnum(abs(a3))} {'✓' if abs(a0) < abs(a3) else '✗'}.",
        f"$b_0 = a_0a_0 - a_3a_3 = {fnum(a0)}\\cdot{fnum(a0)} - {fnum(a3)}\\cdot{fnum(a3)} = {fnum(b[0])}$",
        f"$b_1 = a_0a_1 - a_3a_2 = {fnum(a0)}\\cdot({fnum(a1)}) - {fnum(a3)}\\cdot({fnum(a2)}) = {fnum(b[1])}$",
        f"$b_2 = a_0a_2 - a_3a_1 = {fnum(a0)}\\cdot({fnum(a2)}) - {fnum(a3)}\\cdot({fnum(a1)}) = {fnum(b[2])}$",
        f"Check $|b_0| > |b_2|$: {fnum(abs(b[0]))} > {fnum(abs(b[2]))} {'✓' if abs(b[0]) > abs(b[2]) else '✗'}.",
    ]
    parts[3].steps = [
        "Collect all four conditions:",
        *[f"{nm.replace('^', '')}: {'✓' if ok else '✗'}" for nm, val, ok in J["conds"]],
        f"All ✓ ⇒ stable; any ✗ ⇒ not. Here: **{'asymptotically stable' if stable else 'not asymptotically stable'}**.",
    ]
    return Problem("jury_cubic", "stability", "Jury stability test (cubic)", difficulty, seed, stmt, parts, sol, matlab,
                   source="Pattern: Exam 2016/2017 Problem 3a (5 P); Book Ex. 3.9, 3.10; Exercise book 3.8",
                   plot=lambda: plots.zplane(roots, title="Roots of P(z)"),
                   remedy="List all n+1 Jury conditions with numbers; b_k = a₀a_k − a_n a_{n−k}.")


def jury_quartic(rng, difficulty, seed):
    for _ in range(300):
        rad = rng.uniform(0.2, 1.1, 2)
        th = rng.uniform(0.2, 2.9, 2)
        r = [rad[0] * cmath.exp(1j * th[0]), rad[0] * cmath.exp(-1j * th[0]), rad[1] * cmath.exp(1j * th[1]), rad[1] * cmath.exp(-1j * th[1])]
        c = np.round(np.real(np.poly(r)), 2)
        J = jury_table(c)
        if len(J["rows"]) == 3:
            break
    b, cc = J["rows"][1], J["rows"][2]
    opts = ["asymptotically stable", "not asymptotically stable"]
    stmt = f"Jury test for $$P(z) = {poly_z_tex(c)}.$$"
    parts = [
        Part("p", "$[P(1),\\ (-1)^4P(-1)]$", "vec", [J["P1"], J["Pm1"]], points=1, placeholder="2 numbers"),
        Part("b", "$[b_0, b_1, b_2, b_3]$", "vec", b, points=1.5, placeholder="4 numbers"),
        Part("c", "$[c_0, c_1, c_2]$ with $c_k = b_0b_k - b_3b_{3-k}$", "vec", cc, points=1.5, placeholder="3 numbers"),
        Part("verdict", "Verdict", "choice", opts[0] if J["stable"] else opts[1], options=opts, points=1),
    ]
    cond_md = "\n".join(f"- ${n}$ → {'✅' if ok else '❌'}" for n, v, ok in J["conds"])
    sol = f"{_jury_md(J)}\n\n{cond_md}\n\nmax |root| = {fnum(max(abs(np.roots(c))))}"
    return Problem("jury_quartic", "stability", "Jury stability test (4th order)", difficulty, seed, stmt, parts, sol,
                   f"abs(roots([{' '.join(fnum(x) for x in c)}]))", source="Book Ex. 3.9; Exercise book 3.10",
                   plot=lambda: plots.zplane(np.roots(c), title="Roots of P(z)"), remedy="Second reduction: c_k = b₀b_k − b_{n−1}b_{n−1−k}.")


def stability_factored(rng, difficulty, seed):
    kind = _c(rng, ["stable", "unstable", "limit"])
    r = [0.0 if rng.random() < 0.4 else float(_c(rng, [0.2, -0.3, 0.42])),
         float(_c(rng, [0.5, -0.6, 0.27, 0.8])),
         {"stable": float(_c(rng, [-0.89, 0.7, -0.5])), "unstable": float(_c(rng, [1.2, -1.1, 1.5])), "limit": float(_c(rng, [1.0, -1.0]))}[kind]]
    fac = "".join("z" if abs(x) < 1e-12 else f"(z {'-' if x > 0 else '+'} {fnum(abs(x))})" for x in r)
    opts = ["asymptotically stable: all roots strictly inside the unit circle",
            "at the stability limit: a single root on the unit circle",
            "unstable: a root outside the unit circle"]
    ans = {"stable": opts[0], "limit": opts[1], "unstable": opts[2]}[kind]
    parts = [Part("st", "Which statement can be made *instantly*?", "choice", ans, options=opts, points=1,
                  explain=f"The roots are read off directly: {', '.join(fnum(x) for x in r)}; compare |z| with 1 (Definitions 3.1–3.3).")]
    parts[0].steps = [
        "Each factor (z − r) is zero at z = r ⇒ that is a root (pole). A lone z means a root at 0; (z + 0.6) means r = −0.6.",
        "Roots: " + ", ".join(fnum(x) for x in r) + "; magnitudes: " + ", ".join(fnum(abs(x)) for x in r) + ".",
        "Compare every magnitude with 1 (inside < 1, on = 1, outside > 1).",
        f"⇒ {ans}.",
    ]
    return Problem("stability_factored", "stability", "Stability from the factored polynomial", difficulty, seed,
                   f"The characteristic polynomial can be factored as $P(z) = {fac}$.", parts,
                   f"Roots {', '.join(fnum(x) for x in r)} ⇒ {ans}.", "", source="Pattern: Exam 2016/2017 Problem 3b (1 P)",
                   remedy="Factored form ⇒ read the roots, compare with the unit circle.")


def _linear_k_range(conds):
    lo, hi = 0.0, math.inf
    for alpha, beta in conds:  # alpha + beta K > 0
        if abs(beta) < 1e-14:
            if alpha <= 0:
                return None
            continue
        kb = -alpha / beta
        if beta > 0:
            lo = max(lo, kb)
        else:
            hi = min(hi, kb)
    return lo, hi


def _kcrit_numeric(A, B, kmax=1e4):
    n = max(len(A), len(B))
    A = list(A) + [0.0] * (n - len(A))
    B = list(B) + [0.0] * (n - len(B))
    rho = lambda K: max(abs(np.roots([x + K * y for x, y in zip(A, B)])))  # noqa: E731
    K = 1e-6
    step = 0.01
    while K < kmax:
        if rho(K) >= 1:
            lo, hi = K - step, K
            for _ in range(60):
                mid = (lo + hi) / 2
                if rho(mid) >= 1:
                    hi = mid
                else:
                    lo = mid
            return (lo + hi) / 2
        K += step
        step *= 1.03
    return math.inf


def jury_gain_range(rng, difficulty, seed):
    a = float(_c(rng, [1.0, 2.0, 0.5]))
    T = float(_c(rng, [0.25, 0.5, 1.0, 0.2]))
    d = 1 if difficulty == 3 else 0
    spec = {"num": [1.0], "den": [1.0, a, 0.0]}
    B, A = zoh_tf(spec["num"], spec["den"], T, delay_samples=d)
    n = max(len(A), len(B))
    Ap = A + [0.0] * (n - len(A))
    Bp = B + [0.0] * (n - len(B))
    kc = _kcrit_numeric(Ap, Bp)
    stmt = (f"Plant $G_P(s) = \\dfrac{{1}}{{s(s+{fnum(a)})}}{f'e^{{-{fnum(d * T)}s}}' if d else ''}$ with ZOH, $T = {fnum(T)}$ s:\n\n"
            f"$$G(z) = {tf_zinv_tex(B, A)}$$\n\nA P-controller $G_D = K$ closes the loop. For which $K > 0$ is the closed loop asymptotically stable?")
    parts = [Part("kc", "Critical gain $K_{crit}$ (stable for $0 < K < K_{crit}$)", "num", kc, points=3, tol_rel=0.01,
                  hint="Characteristic polynomial A(z) + K·B(z) (positive powers). Write each Jury condition as an inequality in K.",
                  explain="The loop is stable on (0, K_crit); at K_crit a pole reaches the unit circle.")]
    if d == 0:
        c1 = (Ap[1], Bp[1])
        c0 = (Ap[2], Bp[2])
        conds = [(1 + c1[0] + c0[0], c1[1] + c0[1]), (1 - c1[0] + c0[0], -c1[1] + c0[1]), (1 - c0[0], -c0[1]), (1 + c0[0], c0[1])]
        lo, hi = _linear_k_range(conds)
        names = ["P(1) > 0", "P(−1) > 0", "|a₀| < 1 (complex pair reaches |z| = 1)", "|a₀| < 1 (lower bound)"]
        uppers = [(-conds[i][0] / conds[i][1], i) for i in range(4) if conds[i][1] < -1e-14]
        ia = min(uppers)[1] if uppers else 2
        active = names[ia]
        opts = ["P(1) > 0  → real pole at z = +1", "(−1)ⁿP(−1) > 0  → real pole at z = −1", "|a₀| < |a₂|  → complex pair on the unit circle"]
        ans = {0: opts[0], 1: opts[1]}.get(ia, opts[2])
        parts.append(Part("which", "Which Jury condition is violated first when K exceeds K_crit?", "choice", ans, options=opts, points=1))
        sol = (f"$P(z) = z^2 + ({fnum(c1[0])} + {fnum(c1[1])}K)z + ({fnum(c0[0])} + {fnum(c0[1])}K)$\n\n"
               f"- $P(1) = {fnum(conds[0][0])} + {fnum(conds[0][1])}K > 0$\n- $P(-1) = {fnum(conds[1][0])} + {fnum(conds[1][1])}K > 0$\n"
               f"- $|{fnum(c0[0])} + {fnum(c0[1])}K| < 1$\n\n⇒ ${fnum(lo)} < K < {fnum(hi)}$ (active: {active}). Cf. Book Ex. 3.8 (K_p < 2.3925).")
    else:
        sol = (f"$P(z) = {poly_z_tex(Ap)} + K({poly_z_tex(Bp)})$ (third order because of the dead time). "
               f"Writing all four Jury conditions and intersecting (or scanning K numerically) gives $0 < K < {fnum(kc)}$. "
               "Cf. Exercise book Problem 3.9 (T = 0.25, a = 1 → 0 < K < 2.84).")
    matlab = (f"T = {T}; G = c2d(tf(1,[1 {fnum(a)} 0]{', ' + chr(39) + 'InputDelay' + chr(39) + ', ' + fnum(d * T) if d else ''}), T);\n"
              "[Gm, ~, Wcg] = margin(G)   % Gm = K_crit (gain margin)\nrlocus(G); zgrid")
    return Problem("jury_gain_range", "stability", "Stable gain range via Jury", difficulty, seed, stmt, parts, sol, matlab,
                   source="Book Ex. 3.8, 3.10, 4.3; Exercise book 3.9; Unit 4 homework",
                   plot=lambda: plots.root_locus_figure(np.array(Bp), np.array(Ap), K_marks=[(kc, "K_crit")]),
                   remedy="Jury conditions become inequalities in K; intersect them.")


def w_transform_gen(rng, difficulty, seed):
    n = 2 if difficulty == 1 else 3
    for _ in range(100):
        roots = list(rng.uniform(-1.2, 1.2, n))
        c = np.round(np.real(np.poly(roots)), 2)
        if abs(c[-1]) > 0.01:
            break
    Pw = w_transform(c)
    stable = bool(max(abs(np.roots(c))) < 1)
    opts = ["asymptotically stable", "not asymptotically stable"]
    stmt = (f"Apply the w-transformation $z = \\dfrac{{1+w}}{{1-w}}$ to $P(z) = {poly_z_tex(c)}$ and use the Hurwitz criterion. "
            f"Multiply through by $(1-w)^{n}$ (do not normalise).")
    parts = [Part("pw", f"Coefficients of $P(w)$, highest power first ({n + 1} values)", "vec", list(Pw), points=2,
                  explain="Expand $\\sum_i a_i(1+w)^i(1-w)^{n-i}$.", placeholder=f"{n + 1} numbers"),
             Part("v", "Verdict", "choice", opts[0] if stable else opts[1], options=opts, points=1,
                  explain="Hurwitz: all coefficients of the same sign" + (" and α₂α₁ > α₃α₀ for n = 3." if n == 3 else " (sufficient for n = 2)."))]
    sol = f"$P(w) = {poly_z_tex(Pw, var='w')}$ ⇒ {'stable' if stable else 'not stable'} (roots of P(z): {', '.join(fnum(complex(r), 3) for r in np.roots(c))})."
    return Problem("w_transform", "stability", "w-transformation + Hurwitz", difficulty, seed, stmt, parts, sol,
                   f"syms w; P = poly2sym([{' '.join(fnum(x) for x in c)}], sym('z'));\nPw = expand(subs(P, sym('z'), (1+w)/(1-w))*(1-w)^{n})",
                   source="Book Ex. 3.11, 3.12; Exercise book 3.8, 3.10",
                   remedy="z = (1+w)/(1−w) maps |z| < 1 to Re w < 0.")


def sampling_alias(rng, difficulty, seed):
    f1 = float(_c(rng, [3.0, 5.0, 7.0, 12.0, 0.8]))
    fs = float(_c(rng, [4.0, 8.0, 10.0, 2.0]))
    n = round(f1 / fs)
    fa = abs(f1 - n * fs)
    T = 1 / fs
    w = 2 * math.pi * float(_c(rng, [0.5, 1.0, 2.0]))
    h0 = T * abs(math.sin(w * T / 2) / (w * T / 2))
    opts = ["yes — f_s > 2·f_max", "no — aliasing occurs"]
    stmt = (f"A sinusoid of frequency $f_1 = {fnum(f1)}$ Hz is sampled with $f_s = {fnum(fs)}$ Hz ($T = {fnum(T)}$ s).")
    parts = [
        Part("ok", "Can it be reconstructed from its samples (Shannon)?", "choice", opts[0] if fs > 2 * f1 else opts[1], options=opts, points=1,
             explain="Shannon: ω_s > 2ω₁ (strictly). Otherwise the complementary spectra X(j(ω ± nω_s))/T overlap."),
        Part("fa", "Apparent (alias) frequency in the samples [Hz]", "num", fa, points=1, tol_abs=1e-3,
             explain=f"Samples of frequencies f and f ± n·f_s are identical (Book Ex. 3.2): |{fnum(f1)} − {n}·{fnum(fs)}| = {fnum(fa)} Hz."),
        Part("fmin", "Minimum sampling frequency for this signal [Hz] (limit value)", "num", 2 * f1, points=0.5),
        Part("h0", f"ZOH magnitude $|H_0(j\\omega)| = T\\,|\\sin(\\omega T/2)/(\\omega T/2)|$ at $\\omega = {fnum(w)}$ rad/s", "num", h0, points=0.5,
             explain="The ZOH is a non-ideal low-pass with DC gain T and phase lag ωT/2 (≈ dead time T/2 — used for the 1/(1 + 0.5Ts) approximation)."),
    ]
    parts[0].steps = [f"Shannon: need $f_s > 2f_1$. Here $2f_1 = {fnum(2 * f1)}$ Hz and $f_s = {fnum(fs)}$ Hz.",
                      f"{fnum(fs)} {'>' if fs > 2 * f1 else '≤'} {fnum(2 * f1)} ⇒ {'reconstruction possible' if fs > 2 * f1 else 'aliasing occurs'}."]
    parts[1].steps = [f"Frequencies differing by a multiple of $f_s$ give identical samples. Find the multiple of $f_s$ closest to $f_1$: n = round({fnum(f1)}/{fnum(fs)}) = {n}.",
                      f"Alias = |{fnum(f1)} − {n}·{fnum(fs)}| = {fnum(fa)} Hz."]
    parts[2].steps = [f"Limit: $f_s = 2f_1 = {fnum(2 * f1)}$ Hz (strictly more is needed)."]
    parts[3].steps = [f"$\\omega T/2 = {fnum(w)}\\cdot{fnum(T)}/2 = {fnum(w * T / 2)}$ (radians).",
                      f"$\\sin({fnum(w * T / 2)})/{fnum(w * T / 2)} = {fnum(math.sin(w * T / 2) / (w * T / 2))}$.",
                      f"Times T = {fnum(T)}: {fnum(h0)}."]
    return Problem("sampling_alias", "sampling", "Shannon, aliasing, ZOH frequency response", difficulty, seed, stmt, parts,
                   f"Alias: {fnum(fa)} Hz. Ideal low-pass reconstruction needs f_s > 2f₁ and is not causal (g_I(t) ≠ 0 for t < 0).",
                   "", source="Book Sec. 3.4, Ex. 3.2; Exam theory 2016 Th.b, 2017 Th.c",
                   plot=lambda: plots.aliasing_figure(f1, fs, t_end=min(4.0, 6 / fs + 1)),
                   remedy="ω_s > 2ω_max; frequencies f and f ± n f_s are indistinguishable after sampling.")


GENERATORS = {
    "sampling_alias": sampling_alias,
    "zoh_plant": zoh_plant,
    "closed_loop_P": closed_loop_P,
    "sampler_config": sampler_config,
    "pid_discrete": pid_discrete,
    "mapping_sz": mapping_sz,
    "jury_cubic": jury_cubic,
    "jury_quartic": jury_quartic,
    "stability_factored": stability_factored,
    "jury_gain_range": jury_gain_range,
    "w_transform": w_transform_gen,
}
