"""Numerical helpers that follow the course conventions.

Conventions (as in the lecture notes / Formelsammlung):
* Polynomials in z^-1 are stored as coefficient lists ``[c0, c1, c2, ...]``
  meaning ``c0 + c1 z^-1 + c2 z^-2 + ...``.
* Polynomials in z (positive powers) use numpy order (highest power first).
* State space: x(k+1) = G x(k) + h u(k), y(k) = c^T x(k) + d u(k).
* Jury table: rows start with a0 (coefficient of z^0); b_k = a0*a_k - a_n*a_{n-k}.
"""
from __future__ import annotations

import cmath
import math

import numpy as np
from scipy import linalg, signal


# ---------------------------------------------------------------- formatting
def fnum(x, nd: int = 4) -> str:
    """Compact number formatting for LaTeX/markdown."""
    if isinstance(x, complex) or isinstance(x, np.complexfloating):
        x = complex(x)
        if abs(x.imag) < 1e-12:
            return fnum(x.real, nd)
        sign = "+" if x.imag >= 0 else "-"
        return f"{fnum(x.real, nd)} {sign} j{fnum(abs(x.imag), nd)}"
    x = float(x)
    if abs(x) < 10 ** (-nd) / 2:
        return "0"
    if abs(x) >= 1e5 or abs(x) < 1e-3:
        s = f"{x:.{nd}g}"
        if "e" in s:
            m, e = s.split("e")
            return f"{m}\\cdot 10^{{{int(e)}}}"
        return s
    s = f"{x:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def fvec(v, nd: int = 4) -> str:
    v = np.ravel(np.asarray(v)) if not isinstance(v, (list, tuple)) else v
    return "[" + ",\\; ".join(fnum(x, nd) for x in v) + "]"


def fmat(M, nd: int = 4) -> str:
    M = np.atleast_2d(np.asarray(M, dtype=float))
    rows = [" & ".join(fnum(x, nd) for x in r) for r in M]
    return r"\begin{bmatrix}" + r" \\ ".join(rows) + r"\end{bmatrix}"


def fcol(v, nd: int = 4) -> str:
    return fmat(np.asarray(v, dtype=float).reshape(-1, 1), nd)


def poly_zinv_tex(c, var: str = "z", nd: int = 4, drop_zero: bool = True) -> str:
    """LaTeX for c0 + c1 z^-1 + ... ."""
    terms = []
    for i, ci in enumerate(c):
        if drop_zero and abs(ci) < 1e-12:
            continue
        mag = fnum(abs(ci), nd)
        if i == 0:
            t = mag
        elif mag == "1":
            t = f"{var}^{{-{i}}}"
        else:
            t = f"{mag}\\,{var}^{{-{i}}}"
        sign = "-" if ci < 0 else "+"
        terms.append((sign, t))
    if not terms:
        return "0"
    out = ("-" if terms[0][0] == "-" else "") + terms[0][1]
    for s, t in terms[1:]:
        out += f" {s} {t}"
    return out


def poly_z_tex(c, var: str = "z", nd: int = 4) -> str:
    """LaTeX for numpy-ordered polynomial in positive powers of z."""
    c = list(np.atleast_1d(c))
    n = len(c) - 1
    terms = []
    for i, ci in enumerate(c):
        p = n - i
        if abs(ci) < 1e-12:
            continue
        mag = fnum(abs(ci), nd)
        if p == 0:
            t = mag
        else:
            zp = var if p == 1 else f"{var}^{{{p}}}"
            t = zp if mag == "1" else f"{mag}\\,{zp}"
        terms.append(("-" if ci < 0 else "+", t))
    if not terms:
        return "0"
    out = ("-" if terms[0][0] == "-" else "") + terms[0][1]
    for s, t in terms[1:]:
        out += f" {s} {t}"
    return out


def tf_zinv_tex(num, den, nd: int = 4, delay: int = 0) -> str:
    s = rf"\dfrac{{{poly_zinv_tex(num, nd=nd)}}}{{{poly_zinv_tex(den, nd=nd)}}}"
    if delay:
        s += f"\\,z^{{-{delay}}}"
    return s


# ----------------------------------------------------------- polynomial algebra
def pmul(a, b):
    return list(np.convolve(np.asarray(a, float), np.asarray(b, float)))


def padd(a, b):
    n = max(len(a), len(b))
    a = list(a) + [0.0] * (n - len(a))
    b = list(b) + [0.0] * (n - len(b))
    return [x + y for x, y in zip(a, b)]


def trim(c, tol=1e-12):
    c = list(c)
    while len(c) > 1 and abs(c[-1]) < tol:
        c.pop()
    return c


def zinv_to_z(num, den):
    """Convert num/den in z^-1 to positive powers (numpy order), equal length."""
    n = max(len(num), len(den))
    nz = list(num) + [0.0] * (n - len(num))
    dz = list(den) + [0.0] * (n - len(den))
    return np.array(nz, float), np.array(dz, float)


def eval_zinv(c, z):
    return sum(ci * z ** (-i) for i, ci in enumerate(c))


def series_zinv(num, den, n_terms: int, u=None):
    """Recursive evaluation y(k) for Y = num/den * U (direct division / computational method).

    u: input sequence (default Kronecker delta). den[0] must be nonzero.
    """
    num = list(num)
    den = list(den)
    if u is None:
        u = [1.0] + [0.0] * (n_terms - 1)
    u = list(u) + [0.0] * max(0, n_terms - len(u))
    y = []
    for k in range(n_terms):
        acc = 0.0
        for i, b in enumerate(num):
            if k - i >= 0:
                acc += b * u[k - i]
        for i in range(1, len(den)):
            if k - i >= 0:
                acc -= den[i] * y[k - i]
        y.append(acc / den[0])
    return y


def series_zinv_step(num, den, n_terms: int):
    return series_zinv(num, den, n_terms, u=[1.0] * n_terms)


# ------------------------------------------------------------------ ZOH / c2d
def zoh_tf(num_s, den_s, T, delay_samples: int = 0):
    """Pulse transfer function of ZOH + G_P(s) (exact), returned in z^-1 form.

    Returns (num, den) with den[0] == 1. Numerator includes delay samples.
    """
    nd, dd, _ = signal.cont2discrete((np.asarray(num_s, float), np.asarray(den_s, float)), T, method="zoh")
    nd = np.atleast_1d(np.squeeze(nd))
    dd = np.atleast_1d(np.squeeze(dd))
    # positive powers, same length -> z^-1 coefficients directly
    n = max(len(nd), len(dd))
    nd = np.concatenate([np.zeros(n - len(nd)), nd])
    dd = np.concatenate([np.zeros(n - len(dd)), dd])
    lead = dd[0]
    num = list(nd / lead)
    den = list(dd / lead)
    num = [0.0] * delay_samples + num
    num = [0.0 if abs(x) < 1e-13 else x for x in num]
    return trim(num), trim(den)


def zt_of_s(num_s, den_s, T):
    """Impulse-invariant z-transform Z{G(s)} (sampling the impulse response), z^-1 form.

    Used for the misconception 'forgot the ZOH'. Assumes strictly proper, simple poles.
    """
    r, p, k = signal.residue(num_s, den_s)
    num = np.array([0.0], complex)
    den = np.array([1.0], complex)
    for ri, pi in zip(r, p):
        e = cmath.exp(pi * T)
        tden = np.array([1.0, -e], complex)
        a = np.convolve(num, tden)
        b = np.convolve(np.array([ri], complex), den)
        n = max(len(a), len(b))
        num = np.pad(a, (0, n - len(a))) + np.pad(b, (0, n - len(b)))
        den = np.convolve(den, tden)
    return trim([float(x.real) for x in num]), trim([float(x.real) for x in den])


# ----------------------------------------------------------------- stability
def roots_zinv(den):
    """Roots (in z) of polynomial given in z^-1 coefficients."""
    return np.roots(np.asarray(den, float)) if len(den) > 1 else np.array([])


def jury_table(a_desc):
    """Jury table for P(z) = a_n z^n + ... + a_0 given in numpy order (a_n first).

    Returns dict with rows (list of lists, each starting with z^0 coefficient), conditions, stable.
    Follows the formula sheet: b_k = a0*a_k - a_n*a_{n-k}.
    """
    a_desc = [float(x) for x in a_desc]
    n = len(a_desc) - 1
    a = a_desc[::-1]  # a[0] = a0 ... a[n] = an
    P = np.poly1d(a_desc)
    rows = [a]
    conds = []
    p1 = P(1.0)
    pm1 = (-1) ** n * P(-1.0)
    conds.append(("P(1) > 0", p1, p1 > 0))
    conds.append((f"(-1)^{n} P(-1) > 0", pm1, pm1 > 0))
    conds.append((f"|a_0| < |a_{n}|", (abs(a[0]), abs(a[n])), abs(a[0]) < abs(a[n])))
    cur = a
    letters = "bcdefghi"
    li = 0
    while len(cur) > 3:
        m = len(cur) - 1
        nxt = [cur[0] * cur[k] - cur[m] * cur[m - k] for k in range(m)]
        rows.append(nxt)
        L = letters[li]
        conds.append((f"|{L}_0| > |{L}_{m-1}|", (abs(nxt[0]), abs(nxt[-1])), abs(nxt[0]) > abs(nxt[-1])))
        cur = nxt
        li += 1
    stable = all(c[2] for c in conds)
    return {"n": n, "rows": rows, "conds": conds, "stable": stable, "P1": p1, "Pm1": pm1}


def w_transform(a_desc):
    """P(w) = (1-w)^n P((1+w)/(1-w)) coefficients (numpy order)."""
    n = len(a_desc) - 1
    res = np.zeros(n + 1)
    for i, ai in enumerate(a_desc):
        p = n - i  # power of z
        term = np.poly1d([1.0, 1.0]) ** p * np.poly1d([-1.0, 1.0]) ** (n - p)
        coeffs = np.concatenate([np.zeros(n + 1 - len(term.coeffs)), term.coeffs])
        res += ai * coeffs
    return res


# ------------------------------------------------------------- state space
def ctrb(G, h):
    G = np.asarray(G, float)
    h = np.asarray(h, float).reshape(-1, 1)
    n = G.shape[0]
    cols = [h]
    for _ in range(n - 1):
        cols.append(G @ cols[-1])
    return np.hstack(cols)


def obsv(G, c):
    G = np.asarray(G, float)
    c = np.asarray(c, float).reshape(1, -1)
    n = G.shape[0]
    rows = [c]
    for _ in range(n - 1):
        rows.append(rows[-1] @ G)
    return np.vstack(rows)


def char_poly_from_poles(poles):
    return np.real(np.poly(poles))


def acker(G, h, poles):
    """Ackermann: k^T = [0 ... 1] Qc^-1 P(G)."""
    G = np.asarray(G, float)
    n = G.shape[0]
    alpha = char_poly_from_poles(poles)  # [1, a_{n-1}, ..., a0]
    PG = np.zeros_like(G)
    for i, ai in enumerate(alpha):
        PG = PG + ai * np.linalg.matrix_power(G, n - i)
    Qc = ctrb(G, h)
    e = np.zeros((1, n))
    e[0, -1] = 1.0
    return (e @ np.linalg.solve(Qc, PG)).ravel()


def kw_gain(G, h, c, k):
    G = np.asarray(G, float)
    n = G.shape[0]
    h = np.asarray(h, float).reshape(-1, 1)
    c = np.asarray(c, float).reshape(1, -1)
    k = np.asarray(k, float).reshape(1, -1)
    M = np.eye(n) - G + h @ k
    return float(1.0 / (c @ np.linalg.solve(M, h)).item())


def augment_integral(G, h, c):
    G = np.asarray(G, float)
    n = G.shape[0]
    h = np.asarray(h, float).reshape(-1, 1)
    c = np.asarray(c, float).reshape(1, -1)
    Gh = np.block([[G, np.zeros((n, 1))], [-c @ G, np.ones((1, 1))]])
    hh = np.vstack([h, -c @ h])
    return Gh, hh


def predictive_observer_gain(G, c, poles):
    """p such that eig(G - p c^T) = poles."""
    G = np.asarray(G, float)
    return acker(G.T, np.asarray(c, float), poles)


def current_observer_gain(G, c, poles):
    """p such that eig(G - p c^T G) = poles."""
    G = np.asarray(G, float)
    cg = (np.asarray(c, float).reshape(1, -1) @ G).ravel()
    return acker(G.T, cg, poles)


def dare_gain(G, H, Q, R):
    G = np.asarray(G, float)
    H = np.asarray(H, float).reshape(G.shape[0], -1)
    Q = np.asarray(Q, float)
    R = np.atleast_2d(np.asarray(R, float))
    S = linalg.solve_discrete_are(G, H, Q, R)
    K = np.linalg.solve(R + H.T @ S @ H, H.T @ S @ G)
    return S, K


def c2d_ss(A, b, T):
    A = np.asarray(A, float)
    n = A.shape[0]
    b = np.asarray(b, float).reshape(n, -1)
    M = np.zeros((n + b.shape[1], n + b.shape[1]))
    M[:n, :n] = A
    M[:n, n:] = b
    E = linalg.expm(M * T)
    return E[:n, :n], E[:n, n:]


def ss_to_tf_zinv(G, h, c, d=0.0):
    num, den = signal.ss2tf(np.asarray(G, float), np.asarray(h, float).reshape(-1, 1),
                            np.asarray(c, float).reshape(1, -1), np.atleast_2d(d))
    return list(np.squeeze(num)), list(den)


def simulate_ss(G, h, c, u, x0=None):
    G = np.asarray(G, float)
    n = G.shape[0]
    h = np.asarray(h, float).reshape(-1)
    c = np.asarray(c, float).reshape(-1)
    x = np.zeros(n) if x0 is None else np.asarray(x0, float)
    ys = []
    for uk in u:
        ys.append(float(c @ x))
        x = G @ x + h * uk
    return ys


# ------------------------------------------------------------- s <-> z mapping
def z_from_zeta_ratio(zeta, wd_over_ws):
    mag = math.exp(-2 * math.pi * zeta / math.sqrt(1 - zeta ** 2) * wd_over_ws)
    ang = 2 * math.pi * wd_over_ws
    return mag, ang, complex(mag * math.cos(ang), mag * math.sin(ang))


def angle_deg(z):
    return math.degrees(cmath.phase(z))


def wrap180(a):
    return (a + 180.0) % 360.0 - 180.0


# ------------------------------------------------------------- walkthrough helpers
def recursion_steps(num, den, u, n, name="y", uname="u"):
    """Human-readable recursion lines y(k) = -a1 y(k-1) ... + b0 u(k) + ... with numbers substituted."""
    y = series_zinv(num, den, n, u=u)
    uu = list(u) + [0.0] * n
    lines = []
    for k in range(n):
        sym, val = [], []
        for i in range(1, len(den)):
            if abs(den[i]) > 1e-12:
                c = -den[i]
                prev = y[k - i] if k - i >= 0 else 0.0
                sym.append(f"({fnum(c)})·{name}({k - i})")
                val.append(f"({fnum(c)})·{fnum(prev)}")
        for i, b in enumerate(num):
            if abs(b) > 1e-12:
                uv = uu[k - i] if k - i >= 0 else 0.0
                sym.append(f"({fnum(b)})·{uname}({k - i})")
                val.append(f"({fnum(b)})·{fnum(uv)}")
        lines.append(f"$k = {k}$: ${name}({k}) = " + " + ".join(sym) + " = " + " + ".join(val) + f" = \\mathbf{{{fnum(y[k])}}}$")
    return lines


def pp2_steps(G, h, poles, kname="K", what="h k^T"):
    """Coefficient comparison for 2x2 pole placement: det(zI - G + h k^T) = desired. Returns (steps, k)."""
    G = np.asarray(G, float)
    h = np.asarray(h, float)
    g11, g12, g21, g22 = G.ravel()
    h1, h2 = h
    alpha = np.real(np.poly(poles))  # [1, a1, a0]
    tr, dt = g11 + g22, g11 * g22 - g12 * g21
    # z^1 coefficient: -tr + h1 K1 + h2 K2 ; z^0: dt + K1 (h2 g12 - h1 g22) + K2 (h1 g21 - h2 g11)
    A = np.array([[h1, h2], [h2 * g12 - h1 * g22, h1 * g21 - h2 * g11]])
    rhs = np.array([alpha[1] + tr, alpha[2] - dt])
    k = np.linalg.solve(A, rhs)
    K1, K2 = f"{kname}_1", f"{kname}_2"
    steps = [
        f"Desired polynomial: $({' '.join('(z - ' + fnum(complex(p), 3) + ')' for p in poles)}) = z^2 {'+' if alpha[1] >= 0 else '-'} {fnum(abs(alpha[1]))}z {'+' if alpha[2] >= 0 else '-'} {fnum(abs(alpha[2]))}$.",
        f"Write ${what}$ with unknowns ${K1}, {K2}$. For a 2×2 matrix the characteristic polynomial is $z^2 - (\\text{{trace}})z + \\det$ of $G - {what}$.",
        f"Trace and determinant of G alone: trace $= {fnum(g11)} + {fnum(g22)} = {fnum(tr)}$, det $= {fnum(g11)}\\cdot{fnum(g22)} - {fnum(g12)}\\cdot{fnum(g21)} = {fnum(dt)}$.",
        f"Coefficient of $z^1$: $-({fnum(tr)}) + ({fnum(h1)}){K1} + ({fnum(h2)}){K2}$ must equal ${fnum(alpha[1])}$ ⇒ "
        f"$({fnum(A[0, 0])}){K1} + ({fnum(A[0, 1])}){K2} = {fnum(rhs[0])}$.",
        f"Coefficient of $z^0$: ${fnum(dt)} + ({fnum(A[1, 0])}){K1} + ({fnum(A[1, 1])}){K2}$ must equal ${fnum(alpha[2])}$ ⇒ "
        f"$({fnum(A[1, 0])}){K1} + ({fnum(A[1, 1])}){K2} = {fnum(rhs[1])}$.",
        f"Solve the two linear equations (substitution or Cramer's rule): ${K1} = {fnum(k[0])}$, ${K2} = {fnum(k[1])}$.",
    ]
    return steps, k
