"""Chapter 4 generators: discretisation of analog controllers, root-locus design, deadbeat, IMC, MFC degrees.

Patterns: Homework 4 (discretisation), Homework 5 (root locus, angle/magnitude condition),
Homework 6 (MFC), book Ex. 4.1–4.12, exercise book 4.x.
"""
from __future__ import annotations

import cmath
import math

import numpy as np

from .. import plots
from ..mathutil import (fnum, fvec, pmul, poly_z_tex, poly_zinv_tex, series_zinv, series_zinv_step, tf_zinv_tex,
                        z_from_zeta_ratio, zoh_tf)
from .base import Misc, Part, Problem


def _c(rng, xs):
    return xs[int(rng.integers(len(xs)))]


# -------------------------------------------------------------------------- 17
def discretize_lead(rng, difficulty, seed):
    T = float(_c(rng, [0.1, 0.2, 0.05, 0.25]))
    pi_ctrl = difficulty == 3 and rng.random() < 0.5
    K = float(_c(rng, [2.0, 5.0, 10.0, 20.0, 8.7]))
    a = float(_c(rng, [1.0, 2.0, 0.5, 0.0667]))
    b = 0.0 if pi_ctrl else float(_c(rng, [x for x in [4.0, 5.0, 6.667, 10.0] if x != a]))
    method = "matched" if pi_ctrl else (_c(rng, ["backward", "tustin"]) if difficulty == 1 else _c(rng, ["backward", "tustin", "matched"]))
    mis = {"KD": [], "q": [], "p": []}
    if method == "backward":
        KD = K * (1 + a * T) / (1 + b * T)
        q = 1 / (1 + a * T)
        p = 1 / (1 + b * T)
        rule = "s = \\dfrac{1-z^{-1}}{T}"
        mis["q"].append(Misc(1 - a * T, "disc_forward_euler", "Zero at 1 − aT comes from the FORWARD difference s = (z−1)/T."))
        mis["p"].append(Misc(1 - b * T, "disc_forward_euler", "Pole at 1 − bT comes from the FORWARD difference."))
        steps = (f"$G_D = K\\dfrac{{(1-z^{{-1}})/T + a}}{{(1-z^{{-1}})/T + b}} = K\\dfrac{{(1+aT) - z^{{-1}}}}{{(1+bT) - z^{{-1}}}}"
                 f" = \\underbrace{{K\\dfrac{{1+aT}}{{1+bT}}}}_{{K_D}}\\dfrac{{1 - z^{{-1}}/(1+aT)}}{{1 - z^{{-1}}/(1+bT)}}$")
    elif method == "tustin":
        w = 2 / T
        KD = K * (w + a) / (w + b)
        q = (w - a) / (w + a)
        p = (w - b) / (w + b)
        rule = "s = \\dfrac{2}{T}\\dfrac{1-z^{-1}}{1+z^{-1}}"
        w2 = T / 2
        mis["q"].append(Misc((w2 - a) / (w2 + a), "disc_tustin_factor", "You used T/2 instead of 2/T."))
        mis["p"].append(Misc((w2 - b) / (w2 + b), "disc_tustin_factor", "You used T/2 instead of 2/T."))
        steps = (f"Multiply by $(1+z^{{-1}})$: $G_D = K\\dfrac{{(2/T + a) - (2/T - a)z^{{-1}}}}{{(2/T + b) - (2/T - b)z^{{-1}}}}$, $2/T = {fnum(w)}$")
    else:
        q = math.exp(-a * T)
        p = math.exp(-b * T)
        rule = "z = e^{sT}"
        if pi_ctrl:
            KD = 2 * K / (1 + q)  # match at z=-1 / s=inf
            steps = (f"Zero $s=-{fnum(a)} \\to z = e^{{-{fnum(a * T)}}} = {fnum(q)}$, pole $s=0 \\to z=1$. DC gain is infinite, so match the "
                     f"high-frequency gain: $G_D(-1) = G_C(\\infty) = K$ ⇒ $K_D\\dfrac{{-1-q}}{{-2}} = K$ ⇒ $K_D = \\dfrac{{2K}}{{1+q}}$ (Book Ex. 4.2).")
        else:
            KD = K * a / b * (1 - p) / (1 - q)
            steps = (f"Zero $e^{{-aT}} = {fnum(q)}$, pole $e^{{-bT}} = {fnum(p)}$; DC matching $G_D(1) = G_C(0) = Ka/b$ ⇒ "
                     f"$K_D = \\dfrac{{Ka}}{{b}}\\dfrac{{1-p}}{{1-q}}$ (Book Ex. 4.1).")
    ctex = f"{fnum(K)}\\dfrac{{s + {fnum(a)}}}{{{'s' if pi_ctrl else 's + ' + fnum(b)}}}"
    mname = {"backward": "backward difference", "tustin": "bilinear (Tustin)", "matched": "matched pole-zero mapping"}[method]
    stmt = (f"Discretise the analog controller $G_C(s) = {ctex}$ with the **{mname}** method, $T = {fnum(T)}$ s, "
            "into the form $G_D(z) = K_D\\dfrac{1 - q\\,z^{-1}}{1 - p\\,z^{-1}}$.")
    parts = [
        Part("KD", "$K_D$", "num", KD, points=1, misconceptions=mis["KD"]),
        Part("q", "$q$ (controller zero)", "num", q, points=1, misconceptions=mis["q"]),
        Part("p", "$p$ (controller pole)", "num", p, points=1, misconceptions=mis["p"]),
        Part("de", "Control law $u(k) = p\\,u(k-1) + K_De(k) + c\\,e(k-1)$: enter $c$", "num", -KD * q, points=1,
             explain="$c = -K_Dq$ (inverse z-transform of the normalised $G_D$)."),
    ]
    sol = (f"Rule: ${rule}$.\n\n{steps}\n\n$K_D = {fnum(KD)}$, $q = {fnum(q)}$, $p = {fnum(p)}$\n\n"
           f"$u(k) = {fnum(p)}u(k-1) + {fnum(KD)}e(k) - {fnum(KD * q)}e(k-1)$")
    mm = {"backward": "% backward difference by hand: s = (z-1)/(T z)\nz = tf('z', T); GD = minreal(" + fnum(K) + "*((z-1)/(T*z) + " + fnum(a) + ")/((z-1)/(T*z) + " + fnum(b) + "))",
          "tustin": f"GD = c2d(tf({fnum(K)}*[1 {fnum(a)}], [1 {fnum(b)}]), {T}, 'tustin')",
          "matched": f"GD = c2d(tf({fnum(K)}*[1 {fnum(a)}], [1 {fnum(b)}]), {T}, 'matched')"}[method]
    return Problem("discretize_lead", "discretization", "Discretising an analog controller", difficulty, seed, stmt, parts, sol,
                   f"T = {T};\n{mm}", source="Book Sec. 4.2, Ex. 4.1, 4.2; Homework 4; Exercise book 4.1–4.3",
                   remedy="Backward: s=(1−z⁻¹)/T. Tustin: s=(2/T)(1−z⁻¹)/(1+z⁻¹). Matched: z=e^{sT} + gain matching.")


def sampling_time_rule(rng, difficulty, seed):
    osc = rng.random() < 0.6
    if osc:
        zeta = float(_c(rng, [0.5, 0.6, 0.7, 0.4]))
        wn = float(_c(rng, [2.0, 4.0, 5.0, 10.0]))
        wd = wn * math.sqrt(1 - zeta ** 2)
        T2 = 2 * math.pi / wd
        Tmax = 0.125 * T2
        stmt = f"The desired closed loop has dominant poles with $\\zeta = {fnum(zeta)}$, $\\omega_n = {fnum(wn)}$ rad/s (oscillatory step response)."
        parts = [Part("T2", "Oscillation period $T_2 = 2\\pi/\\omega_d$ [s]", "num", T2, points=1,
                      misconceptions=[Misc(2 * math.pi / wn, "map_wn_vs_wd", "Use the DAMPED frequency ω_d = ω_n√(1−ζ²).")]),
                 Part("T", "Largest admissible sampling time by the rule $T \\le 0.125\\,T_2$ [s]", "num", Tmax, points=1)]
        sol = f"$\\omega_d = {fnum(wd)}$, $T_2 = {fnum(T2)}$ s ⇒ $T \\le {fnum(Tmax)}$ s (≈ 8 samples per period; Book Ex. 4.1 uses T = 0.2 s for T₂ = 1.814 s)."
    else:
        tau = float(_c(rng, [0.5, 1.0, 2.0, 4.0]))
        T1 = tau
        stmt = f"The desired closed loop is aperiodic with time constant (tangent construction) $T_1 = {fnum(T1)}$ s."
        parts = [Part("T", "Largest admissible sampling time by $T \\le 0.125\\,T_1$ [s]", "num", 0.125 * T1, points=1)]
        sol = f"$T \\le 0.125\\cdot{fnum(T1)} = {fnum(0.125 * T1)}$ s."
    return Problem("sampling_time_rule", "discretization", "Choice of the sampling time", difficulty, seed, stmt, parts,
                   sol + "\n\nShannon alone ($T < 1/(2f_m)$) is far too optimistic for control loops (signals are not band-limited).", "",
                   source="Book Sec. 4.1; Formelsammlung p. 9; Exam 2016 Problem 4a", remedy="T ≤ 0.125·T₁ (aperiodic) or 0.125·T₂ (oscillatory).")


# -------------------------------------------------------------------------- 18
def _rl_design(G_num_z, G_den_z, z1, include_ctrl_pole=True):
    """Angle condition for PI controller (z - qC)/(z - 1). G given in positive powers (numpy)."""
    zeros = np.roots(G_num_z) if len(np.trim_zeros(G_num_z, "f")) > 1 else np.array([])
    poles = np.roots(G_den_z)
    phi_p = sum(math.degrees(cmath.phase(z1 - p)) for p in poles)
    phi_q = sum(math.degrees(cmath.phase(z1 - q)) for q in zeros)
    phi_c = math.degrees(cmath.phase(z1 - 1)) if include_ctrl_pole else 0.0
    phi_qc = (-180 + phi_p + phi_c - phi_q) % 360
    return phi_qc, zeros, poles, phi_p, phi_q, phi_c


def rl_pi_design(rng, difficulty, seed):
    for _ in range(100):
        zeta = float(_c(rng, [0.5, 0.6, 0.7, math.sqrt(2) / 2]))
        N = int(_c(rng, [8, 10, 12]))
        mag, ang, z1 = z_from_zeta_ratio(zeta, 1 / N)
        if difficulty < 3:
            a = float(_c(rng, [1.0, 2.0, 0.5]))
            b = float(_c(rng, [x for x in [5.0, 3.0, 4.0, 2.5] if x != a]))
            K = float(_c(rng, [10.0, 30.0, 5.0, 2.0]))
            T = float(_c(rng, [0.25, 0.2, 0.1]))
            num, den = zoh_tf([K], [1, a + b, a * b], T)
            ptex = f"\\dfrac{{{fnum(K)}}}{{(s+{fnum(a)})(s+{fnum(b)})}}"
        else:
            a = float(_c(rng, [0.4, 0.2, 0.5]))
            td = int(_c(rng, [1, 2]))
            T = float(_c(rng, [1.0, 2.5, 2.0]))
            num, den = zoh_tf([1.0], [1.0, a], T, delay_samples=td)
            ptex = f"\\dfrac{{e^{{-{fnum(td * T)}s}}}}{{s+{fnum(a)}}}"
        n = max(len(num), len(den))
        Bz = np.array(list(num) + [0.0] * (n - len(num)))  # positive powers aligned with den
        Az = np.array(list(den) + [0.0] * (n - len(den)))
        lead = Bz[np.nonzero(np.abs(Bz) > 1e-12)[0][0]]
        phi, zeros, poles, phi_p, phi_q, phi_c = _rl_design(Bz, Az, z1)
        if not (5 < phi < 175):
            continue
        qC = z1.real - z1.imag / math.tan(math.radians(phi))
        if not (-0.9 < qC < 0.99):
            continue
        Kroot = abs(z1 - 1) * np.prod([abs(z1 - p) for p in poles]) / (abs(z1 - qC) * np.prod([abs(z1 - q) for q in zeros]) if len(zeros) else abs(z1 - qC))
        Kp = Kroot / lead
        phi_w, *_ = _rl_design(Bz, Az, z1, include_ctrl_pole=False)
        qC_w = z1.real - z1.imag / math.tan(math.radians(phi_w)) if 1 < phi_w < 179 else 99.0
        break
    # closed loop
    num_o = pmul([1.0, -qC], list(Bz * Kp))
    den_o = pmul([1.0, -1.0], list(Az))
    m = max(len(num_o), len(den_o))
    num_o = [0.0] * (m - len(num_o)) + list(num_o)
    den_o = [0.0] * (m - len(den_o)) + list(den_o)
    char = [x + y for x, y in zip(den_o, num_o)]
    cl_poles = np.roots(char)
    stmt = (f"Plant $G_P(s) = {ptex}$ with ZOH, $T = {fnum(T)}$ s:\n\n$$G(z) = {tf_zinv_tex(num, den)}$$\n\n"
            f"Design a discrete PI controller $G_D(z) = K_p\\dfrac{{z - q_C}}{{z - 1}}$ with the **root locus method** such that the closed loop has "
            f"dominant poles with $\\zeta = {fnum(zeta)}$ and $\\omega_s = {N}\\,\\omega_d$.")
    parts = [
        Part("z1", "(a) Desired pole $z_1 = [\\mathrm{Re},\\ \\mathrm{Im}]$ (upper half-plane)", "vec", [z1.real, z1.imag], points=1,
             explain=f"$|z_1| = e^{{-2\\pi\\zeta/\\sqrt{{1-\\zeta^2}}\\cdot 1/{N}}} = {fnum(mag)}$, $\\arg z_1 = 360°/{N}$.", placeholder="2 numbers"),
        Part("phi", "(b) Required angle contribution of the controller zero $\\varphi_{qC}$ [deg]", "num", phi, points=1, tol_abs=0.3, tol_rel=0.005,
             hint="Angle condition: Σφ_q − Σφ_p = ±180°. Include the controller pole at z = 1!",
             explain=f"$\\varphi_{{qC}} = -180° + \\Sigma\\varphi_p + \\varphi_{{pC}} - \\Sigma\\varphi_q = -180° + {fnum(phi_p, 2)}° + {fnum(phi_c, 2)}° - {fnum(phi_q, 2)}°$",
             misconceptions=[Misc(phi_w, "rl_forgot_controller_pole", "This angle ignores the controller pole at z = 1.")]),
        Part("qC", "(c) Controller zero $q_C$", "num", qC, points=2, tol_abs=0.004, tol_rel=0.01,
             hint="tan φ_qC = Im z₁ / (Re z₁ − q_C).",
             misconceptions=[Misc(qC_w, "rl_forgot_controller_pole", "Your zero results from an angle condition without the controller pole at z = 1.")]),
        Part("Kp", "(d) Controller gain $K_p$ (magnitude condition)", "num", Kp, points=2, tol_rel=0.02,
             hint="|G_o(z₁)| = 1 ⇒ root-locus gain K = Π|z₁ − p| / Π|z₁ − q|; then K_p = K / (leading coefficient of B(z)).",
             explain=f"Root-locus gain $K = {fnum(Kroot)}$, $K_p = K/{fnum(lead)} = {fnum(Kp)}$."),
    ]
    sol = (f"1. $z_1 = {fnum(z1)}$\n2. Poles (incl. controller pole $z=1$): {', '.join(fnum(complex(p)) for p in list(poles) + [1.0])}; "
           f"plant zeros: {', '.join(fnum(complex(q)) for q in zeros) if len(zeros) else 'none'}.\n"
           f"3. Angle condition ⇒ $\\varphi_{{qC}} = {fnum(phi, 2)}°$ ⇒ $q_C = \\mathrm{{Re}}z_1 - \\mathrm{{Im}}z_1/\\tan\\varphi_{{qC}} = {fnum(qC)}$\n"
           f"4. Magnitude condition ⇒ $K = {fnum(Kroot)}$, $K_p = {fnum(Kp)}$\n\n"
           f"Closed-loop poles: {', '.join(fnum(complex(p), 3) for p in cl_poles)} — check that $z_1$ is among them and judge dominance "
           "(a pole near the controller zero nearly cancels, Book Ex. 4.4 remark).")
    matlab = (f"T = {T}; G = c2d(tf({'[' + fnum(K) + ']' if difficulty < 3 else '1'}, {'[1 ' + fnum(a + b) + ' ' + fnum(a * b) + ']' if difficulty < 3 else '[1 ' + fnum(a) + ']'}"
              f"{'' if difficulty < 3 else ', ' + chr(39) + 'InputDelay' + chr(39) + ', ' + fnum(td * T)}), T, 'zoh');\n"
              f"z1 = {z1.real:.4f} + {z1.imag:.4f}i;\n"
              "phiG = angle(evalfr(G, z1)) - angle(z1 - 1);       % plant + controller pole\n"
              "phiq = pi - phiG;  phiq = mod(phiq, 2*pi)         % needed zero angle\n"
              "qC = real(z1) - imag(z1)/tan(phiq)\n"
              "Kp = 1/abs(evalfr(G, z1)*(z1-qC)/(z1-1))\n"
              "GD = Kp*tf([1 -qC],[1 -1],T); rlocus(GD*G); zgrid; step(feedback(GD*G,1))")
    return Problem("rl_pi_design", "root_locus", "Root-locus PI design (angle + magnitude condition)", difficulty, seed, stmt, parts, sol, matlab,
                   source="Book Ex. 4.4, 4.5; Homework 5; Exercise book 4.4–4.6",
                   plot=lambda: plots.zplane(list(poles) + [1.0], list(zeros) + [qC], extra=[([z1, z1.conjugate()], "g*", "desired z₁,₂")], title="Open loop with PI controller"),
                   remedy="Angle condition fixes the zero, magnitude condition fixes the gain.")


def static_error(rng, difficulty, seed):
    integ = difficulty > 1 and rng.random() < 0.5
    T = float(_c(rng, [0.1, 0.2, 0.5, 1.0]))
    a = float(_c(rng, [1.0, 2.0, 0.5]))
    K = float(_c(rng, [1.0, 2.0, 4.0]))
    Kc = float(_c(rng, [0.5, 1.0, 2.0, 3.0]))
    if integ:
        B, A = zoh_tf([K], [1.0, a, 0.0], T)
        # (1 - z^-1) G at z=1: A has factor (1 - z^-1)
        Ared = np.polydiv(np.array(A), np.array([1.0, -1.0]))[0]
        lim1 = Kc * sum(B) / sum(Ared)
        ev = T / lim1
        stmt = (f"Unit-feedback loop: P-controller $G_D = {fnum(Kc)}$, plant $G_P(s) = \\dfrac{{{fnum(K)}}}{{s(s+{fnum(a)})}}$ with ZOH, "
                f"$T = {fnum(T)}$ s: $G(z) = {tf_zinv_tex(B, A)}$.")
        parts = [Part("ep", "Position error $e_p$ for a unit step", "num", 0.0, points=1,
                      explain="Type-1 open loop (pole at z = 1) ⇒ $K_p = \\infty$, $e_p = 0$."),
                 Part("ev", "Velocity error $e_v$ for a unit ramp $w(t) = t$", "num", ev, points=2,
                      explain=f"$e_v = \\lim_{{z\\to1}}\\dfrac{{Tz^{{-1}}}}{{(1-z^{{-1}})G_DG}} = T/\\lim(1-z^{{-1}})G_DG = {fnum(T)}/{fnum(lim1)}$.")]
        sol = f"$\\lim_{{z\\to1}}(1-z^{{-1}})G_DG = {fnum(lim1)}$ ⇒ $K_v = {fnum(lim1 / T)}$, $e_v = 1/K_v = {fnum(ev)}$."
    else:
        B, A = zoh_tf([K], [1.0, a], T)
        Kpos = Kc * sum(B) / sum(A)
        stmt = (f"Unit-feedback loop: P-controller $G_D = {fnum(Kc)}$, plant $G_P(s) = \\dfrac{{{fnum(K)}}}{{s+{fnum(a)}}}$ with ZOH, $T = {fnum(T)}$ s.")
        parts = [Part("Kp", "Position error constant $K_p = \\lim_{z\\to1}G_DG$", "num", Kpos, points=1,
                      explain="The ZOH keeps the DC gain: G(1) = G_P(0) = K/a."),
                 Part("ep", "Position error $e_p$", "num", 1 / (1 + Kpos), points=1, explain="$e_p = 1/(1+K_p)$.")]
        sol = f"$K_p = {fnum(Kc)}\\cdot{fnum(K / a)} = {fnum(Kpos)}$, $e_p = 1/(1+K_p) = {fnum(1 / (1 + Kpos))}$."
    return Problem("static_error", "root_locus", "Static specifications (position / velocity error)", difficulty, seed, stmt, parts, sol, "",
                   source="Book Sec. 4.3.1; Formelsammlung p. 12", remedy="e_p = 1/(1+K_p); integrator in the loop ⇒ e_p = 0.")


# -------------------------------------------------------------------------- 20
def deadbeat_stable(rng, difficulty, seed):
    T = float(_c(rng, [1.0, 0.25, 0.5, 0.2]))
    if difficulty == 1:
        K = float(_c(rng, [0.4, 2.0, 4.0]))
        tau = float(_c(rng, [1.0, 4.0, 2.0]))
        d = 0
        num, den = zoh_tf([K / tau], [1.0, 1.0 / tau], T)
        ptex = f"\\dfrac{{{fnum(K)}}}{{1 + {fnum(tau)}s}}"
    elif difficulty == 2:
        K = float(_c(rng, [2.0, 10.0]))
        d = 0
        num, den = zoh_tf([K], [1.0, 3.0, 2.0], T)
        ptex = f"\\dfrac{{{fnum(K)}}}{{(s+1)(s+2)}}"
    else:
        K = float(_c(rng, [4.0, 2.0]))
        tau = float(_c(rng, [4.0, 2.0]))
        T = 1.0
        d = int(_c(rng, [1, 2, 3]))
        num, den = zoh_tf([K / tau], [1.0, 1.0 / tau], T, delay_samples=0)
        ptex = f"\\dfrac{{{fnum(K)}\\,e^{{-{d}s}}}}{{1 + {fnum(tau)}s}}"
    B = list(num)  # [0, b1, b2, ...]
    A = list(den)
    B1 = sum(B)
    FW = [0.0] * d + [x / B1 for x in B]
    GUW = [x / B1 for x in A]
    u0 = 1 / B1
    dtex = f"\\,z^{{-{d}}}" if d else ""
    stmt = (f"Plant $G_P(s) = {ptex}$, ZOH, $T = {fnum(T)}$ s ⇒ $G(z) = \\dfrac{{B(z)}}{{A(z)}}z^{{-d}} = {tf_zinv_tex(B, A)}"
            f"{dtex}$ (asymptotically stable).\n\n"
            "Design a **dead-beat controller** for minimal settling time with $C(z) = 1$ (no control constraint).")
    parts = [
        Part("B1", "$B(1)$", "num", B1, points=0.5),
        Part("FW", f"$F_W(z) = \\dfrac{{B(z)}}{{B(1)}}z^{{-d}}$: coefficients of $z^0, z^{{-1}}, \\dots$ ({len(FW)} values)", "vec", FW, points=1.5,
             explain="Closed loop becomes a finite polynomial in z⁻¹ (FIR) with $F_W(1) = 1$ ⇒ y reaches w after n + d steps.",
             placeholder=f"{len(FW)} numbers"),
        Part("u0", "First control value $u(0) = 1/B(1)$ after a unit step", "num", u0, points=1,
             explain="$G_{UW} = A(z)/B(1)$; initial value theorem ⇒ $u(0) = 1/B(1)$."),
        Part("GUW", f"$G_{{UW}}(z) = A(z)/B(1)$: coefficients ({len(GUW)} values)", "vec", GUW, points=1, placeholder=f"{len(GUW)} numbers"),
    ]
    umax = round(u0 * float(_c(rng, [0.5, 0.6, 0.8])), 1)
    c1 = 1 / (umax * B1) - 1
    if difficulty >= 2:
        parts.append(Part("c1", f"Constraint $u(0) = {fnum(umax)}$: required $c_1$ in $C(z) = 1 + c_1z^{{-1}}$", "num", c1, points=1,
                          explain="$u(0) = 1/(B(1)(1+c_1))$ ⇒ $c_1 = 1/(u(0)B(1)) - 1$ (one more step settling time)."))
    GD_den = [B1] + [0.0] * (len(FW) - 1)
    GD_den = [x - y * B1 for x, y in zip(GD_den, FW)]
    sol = (f"$B(1) = {fnum(B1)}$, $F_W = {poly_zinv_tex(FW)}$, $u(0) = {fnum(u0)}$\n\n"
           f"$$G_D(z) = \\dfrac{{A(z)}}{{B(1) - B(z)z^{{-d}}}} = \\dfrac{{{poly_zinv_tex(A)}}}{{{poly_zinv_tex(GD_den)}}}$$\n\n"
           f"$G_{{UW}} = {poly_zinv_tex(GUW)}$ ⇒ $u(k) = $ {fvec(GUW)} then constant $1/G_P(0)$."
           + (f"\n\nWith $u(0) = {fnum(umax)}$: $c_1 = {fnum(c1)}$, $F_W = B(z)C(z)z^{{-d}}/(B(1)C(1))$ — one extra step." if difficulty >= 2 else ""))
    y = series_zinv_step(FW, [1.0], 8)
    u = series_zinv_step(GUW, [1.0], 8)
    return Problem("deadbeat_stable", "analytic_design", "Dead-beat controller (stable plant)", difficulty, seed, stmt, parts, sol,
                   f"T = {T}; G = c2d(tf(...), T);\n[B, A] = tfdata(G, 'v');  B1 = sum(B);\nFW = filt(B/B1, 1, T)   % times z^-d\nGD = filt(A, B1*[1 zeros(1,numel(B)-1)] - [B zeros(1,0)], T)",
                   source="Book Ex. 4.8; Formelsammlung p. 14; Exercise book 4.7–4.9",
                   plot=lambda: plots.step_compare({"y(k)": y, "u(k)": u}, "Dead-beat reference step"),
                   remedy="Stable plant: F_W = B z^{−d}/B(1), G_D = A/(B(1) − B z^{−d}), u(0) = 1/B(1).")


def imc_first_order(rng, difficulty, seed):
    K = float(_c(rng, [1.0, 2.0]))
    tau = float(_c(rng, [5.0, 4.0, 2.0]))
    T = 1.0
    d = int(_c(rng, [1, 2, 3]))
    alpha = float(_c(rng, [0.25, 0.5, 0.75]))
    a = math.exp(-T / tau)
    b = K * (1 - a)
    stmt = (f"Design an **IMC** for $\\tilde G(s) = \\dfrac{{{fnum(K)}\\,e^{{-{d}s}}}}{{1 + {fnum(tau)}s}}$, $T = 1$ s, "
            f"with filter $F(z) = \\dfrac{{1-\\alpha}}{{1-\\alpha z^{{-1}}}}$, $\\alpha = {fnum(alpha)}$.")
    gc = [(1 - alpha) / b, -a * (1 - alpha) / b]
    parts = [
        Part("ab", "$\\tilde G(z) = \\dfrac{b\\,z^{-(d+1)}}{1 - a z^{-1}}$: $[a, b]$", "vec", [a, b], points=1, placeholder="2 numbers",
             explain=f"$a = e^{{-T/\\tau}} = {fnum(a)}$, $b = K(1-a) = {fnum(b)}$; the dead time adds $z^{{-{d}}}$ to the ZOH delay $z^{{-1}}$."),
        Part("delay", "Total delay $n$ in $\\tilde G^-(z) = z^{-n}$", "num", d + 1, points=1, tol_abs=0.01, tol_rel=0),
        Part("gc", "$G_C^*(z) = \\dfrac{c_0 + c_1z^{-1}}{1-\\alpha z^{-1}}$: $[c_0, c_1]$", "vec", gc, points=1.5, placeholder="2 numbers",
             explain="$G_C^* = F/\\tilde G^+$ with $\\tilde G^+ = b/(1-az^{-1})$ (invertible part)."),
        Part("gw", "$G_W(1)$", "num", 1.0, points=0.5, explain="$G_W = \\tilde G^-F$, $F(1) = 1$, $\\tilde G^-(1) = 1$ ⇒ no offset."),
    ]
    sol = (f"$\\tilde G = \\dfrac{{{fnum(b)}z^{{-{d + 1}}}}}{{1-{fnum(a)}z^{{-1}}}}$, $\\tilde G^- = z^{{-{d + 1}}}$, $\\tilde G^+ = \\dfrac{{{fnum(b)}}}{{1-{fnum(a)}z^{{-1}}}}$\n\n"
           f"$G_C^* = \\dfrac{{1-{fnum(a)}z^{{-1}}}}{{{fnum(b)}}}\\cdot\\dfrac{{{fnum(1 - alpha)}}}{{1-{fnum(alpha)}z^{{-1}}}}$, "
           f"$G_W = \\dfrac{{{fnum(1 - alpha)}z^{{-{d + 1}}}}}{{1-{fnum(alpha)}z^{{-1}}}}$ (Book Ex. 4.12; Exercise book 4.14).")
    return Problem("imc_first_order", "analytic_design", "Internal Model Control (first order + dead time)", difficulty, seed, stmt, parts, sol, "",
                   source="Book Sec. 4.6, Ex. 4.12; Exercise book 4.14",
                   remedy="Factor G̃ = G̃⁺G̃⁻ (delay & bad zeros in G̃⁻), invert G̃⁺, add low-pass F with F(1)=1.")


def mfc_degrees(rng, difficulty, seed):
    n = int(_c(rng, [1, 2, 3]))
    d = int(_c(rng, [0, 1, 2]))
    nBp = int(_c(rng, [0, 1])) if n > 1 else 0
    integ_plant = rng.random() < 0.3
    nAW = int(_c(rng, [x for x in [1, 2, 3] if x <= n + 1]))
    nQ = n - 1 if integ_plant else n
    nP = max(nQ - nBp + d, nAW - n, 0)
    nAo = nP + n - nAW
    stmt = (f"MFC design: plant $\\dfrac{{B(z)}}{{A(z)}}z^{{-{d}}}$ with $n = {n}$ (degree of A), dead time $d = {d}$, "
            f"$n_{{B^+}} = {nBp}$ (degree of the cancelled 'good' zeros), desired $A_W$ of degree {nAW}. "
            + ("The plant is **integrating** (no integral action needed in the controller)." if integ_plant else
               "The controller must have **integral action** ($\\tilde P(1) = 0$)."))
    parts = [Part("nQ", "$n_Q$", "num", nQ, points=1, tol_abs=0.01, tol_rel=0,
                  explain="$n_Q = n$ with the extra integral-action equation; $n_Q = n-1$ when the plant integrates and the last equation is dropped."),
             Part("nP", "minimal $n_{\\tilde P}$", "num", nP, points=1, tol_abs=0.01, tol_rel=0,
                  explain="$n_{\\tilde P} \\ge n_Q - n_{B^+} + d$ and $n_{A_o} = n_{\\tilde P} + n - n_{A_W} \\ge 0$."),
             Part("nAo", "$n_{A_o}$ (observer polynomial degree)", "num", nAo, points=1, tol_abs=0.01, tol_rel=0)]
    sol = (f"$n_Q = {nQ}$; $n_{{\\tilde P}} \\ge {nQ} - {nBp} + {d} = {nQ - nBp + d}$ (and ≥ {nAW - n} so that $n_{{A_o}} \\ge 0$) ⇒ $n_{{\\tilde P}} = {nP}$; "
           f"$n_{{A_o}} = {nP} + {n} - {nAW} = {nAo}$. Check Book Ex. 4.6 (n=2, d=2, n_B+=1 → n_Q=2, n_P̃=3, n_Ao=3) and Ex. 4.7.\n\n"
           "⚠ The formula sheet labels $n_Q = n-1$ '(Integrating controller)'; the book (p. 4.4) says this applies when the **plant** has integral behaviour so a proportional controller suffices.")
    return Problem("mfc_degrees", "analytic_design", "MFC: polynomial degree conditions", difficulty, seed, stmt, parts, sol, "",
                   source="Book Sec. 4.4 eqs. (4.38)–(4.41); Formelsammlung p. 17; Homework 6",
                   remedy="n_Q = n (n−1 for integrating plant); n_P̃ ≥ n_Q − n_B+ + d; n_Ao = n_P̃ + n − n_AW.")


GENERATORS = {
    "discretize_lead": discretize_lead,
    "sampling_time_rule": sampling_time_rule,
    "rl_pi_design": rl_pi_design,
    "static_error": static_error,
    "deadbeat_stable": deadbeat_stable,
    "imc_first_order": imc_first_order,
    "mfc_degrees": mfc_degrees,
}
