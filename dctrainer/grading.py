"""Answer parsing, tolerance checks and misconception diagnosis."""
from __future__ import annotations

import ast
import math
import operator
import re

from .problems.base import Part

_ALLOWED_FUNCS = {
    "sqrt": math.sqrt, "exp": math.exp, "log": math.log, "ln": math.log,
    "sin": math.sin, "cos": math.cos, "tan": math.tan, "atan": math.atan,
    "abs": abs,
}
_ALLOWED_NAMES = {"pi": math.pi, "e": math.e}
_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Pow: operator.pow}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _eval(node.operand)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.Name) and node.id in _ALLOWED_NAMES:
        return _ALLOWED_NAMES[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_FUNCS:
        return _ALLOWED_FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError("unsupported expression")


def parse_num(s: str) -> float:
    s = str(s).strip().replace(",", ".").replace("^", "**")
    if not s:
        raise ValueError("empty")
    return float(_eval(ast.parse(s, mode="eval")))


def parse_vec(s: str) -> list:
    s = str(s).strip()
    s = s.strip("[](){}")
    # allow '0.5, 0.7; 1.2' or whitespace separated; decimal comma not supported in vectors
    tokens = [t for t in re.split(r"[;,\s]+", s) if t]
    return [parse_num(t) for t in tokens]


def close(a: float, b: float, tol_rel: float, tol_abs: float) -> bool:
    return abs(a - b) <= max(tol_abs, tol_rel * abs(b))


def vec_close(a, b, tol_rel, tol_abs) -> bool:
    return len(a) == len(b) and all(close(x, y, tol_rel, tol_abs) for x, y in zip(a, b))


def _match(part: Part, user, target) -> bool:
    if part.kind == "num":
        return close(user, float(target), part.tol_rel, part.tol_abs)
    if part.kind == "vec":
        return vec_close(user, [float(t) for t in target], part.tol_rel, part.tol_abs)
    return str(user) == str(target)


def generic_diagnosis(part: Part, user) -> str:
    """Heuristic detectors for typical slip patterns when no specific misconception matched."""
    tr, ta = part.tol_rel, part.tol_abs
    if part.kind == "num":
        a = float(part.answer)
        if abs(a) > 1e-9:
            if close(user, -a, tr, ta):
                return "Sign error — your magnitude is right but the sign is flipped. Re-check the sign convention (e.g. `−a₁` in the companion matrix, `(−1)ⁿP(−1)`, `u = −kᵀx`)."
            if abs(user) > 1e-12 and close(user, 1 / a, tr, ta):
                return "You computed the reciprocal. Check which quantity is in the numerator."
            for f, msg in ((2, "a factor 2"), (0.5, "a factor ½"), (math.degrees(1), "a degree/radian mix-up (factor 57.3)"),
                           (1 / math.degrees(1), "a degree/radian mix-up (factor 1/57.3)")):
                if close(user, a * f, tr, ta):
                    return f"Off by {msg}."
        return ""
    if part.kind == "vec":
        a = [float(x) for x in part.answer]
        if len(user) != len(a):
            return f"Expected {len(a)} numbers, you entered {len(user)}."
        if vec_close(user, [-x for x in a], tr, ta):
            return "All signs flipped — systematic sign error."
        if vec_close(user, a[::-1], tr, ta):
            return "Order reversed — check the ordering convention (ascending powers of z⁻¹ / state order / z⁰ first in the Jury table)."
        if len(a) > 1 and vec_close(user[1:], a[:-1], tr, ta):
            return "Shifted by one sample (you are one step *late*): check the delay z⁻¹ / which sample is k = 0."
        if len(a) > 1 and vec_close(user[:-1], a[1:], tr, ta):
            return "Shifted by one sample (you are one step *early*): did you forget a z⁻¹ (e.g. the ZOH delay or b₀ = 0)?"
        nz = [(u, t) for u, t in zip(user, a) if abs(t) > 1e-9]
        if nz:
            ratios = [u / t for u, t in nz]
            r = ratios[0]
            if abs(r - 1) > 0.05 and all(abs(x - r) <= 0.02 * max(1, abs(r)) for x in ratios):
                return f"All entries scaled by ≈{r:.3g} — a gain/normalisation factor is missing or doubled."
        good = 0
        for u, t in zip(user, a):
            if close(u, t, tr, ta):
                good += 1
            else:
                break
        wrong_idx = [i for i, (u, t) in enumerate(zip(user, a)) if not close(u, t, tr, ta)]
        if good > 0:
            return f"First {good} entr{'y' if good == 1 else 'ies'} correct; error starts at entry {good + 1}. In a recursion this usually means a wrong coefficient/sign that only acts on past values."
        if wrong_idx and len(wrong_idx) < len(a):
            return f"Entries {', '.join(str(i + 1) for i in wrong_idx)} are wrong; the others are right."
    return ""


def grade_part(part: Part, raw) -> dict:
    """Return dict(correct, parsed, diagnosis, tag, error)."""
    res = {"correct": False, "parsed": None, "diagnosis": "", "tag": None, "error": None}
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        res["error"] = ("Type a number in the box first (e.g. `1.28`, `-1/3`, `sqrt(2)`)." if part.kind == "num" else
                        "Type the numbers first, separated by commas (e.g. `0.5, 0.7, 1.28`)." if part.kind == "vec" else
                        "Select one of the options first.")
        return res
    try:
        if part.kind == "num":
            user = parse_num(raw)
        elif part.kind == "vec":
            user = parse_vec(raw)
        else:
            user = raw
    except Exception:
        res["error"] = "Could not parse your input. Use numbers like `0.25`, `-1/3`, `exp(-0.5)`; vectors as `1, 0.5, -2`."
        return res
    res["parsed"] = user
    if user is None or user == "":
        res["error"] = "No answer given."
        return res
    if _match(part, user, part.answer):
        res["correct"] = True
        return res
    for m in part.misconceptions:
        try:
            if _match(part, user, m.value):
                res["diagnosis"] = m.diagnosis
                res["tag"] = m.tag
                return res
        except Exception:
            continue
    res["diagnosis"] = generic_diagnosis(part, user)
    return res
