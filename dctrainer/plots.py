"""Small, fast matplotlib figures (z-plane, sequences, staircase signals, mappings)."""
from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

plt.rcParams.update({"figure.dpi": 110, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3})


def _fig(w=5.2, h=2.8):
    fig, ax = plt.subplots(figsize=(w, h))
    return fig, ax


def stem_seq(seqs: dict, title: str = "", xlabel: str = "k"):
    fig, ax = _fig()
    markers = ["o", "s", "^", "d"]
    for i, (lab, y) in enumerate(seqs.items()):
        k = np.arange(len(y))
        ml, sl, bl = ax.stem(k + 0.08 * i, y, label=lab)
        plt.setp(ml, marker=markers[i % 4], markersize=4, color=f"C{i}")
        plt.setp(sl, color=f"C{i}", linewidth=1)
        plt.setp(bl, color="grey", linewidth=0.6)
    ax.set_xlabel(xlabel)
    if title:
        ax.set_title(title)
    if len(seqs) > 1:
        ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def step_compare(seqs: dict, title: str = "", T: float | None = None):
    fig, ax = _fig()
    for i, (lab, y) in enumerate(seqs.items()):
        k = np.arange(len(y))
        x = k * T if T else k
        ax.step(x, y, where="post", label=lab, color=f"C{i}")
        ax.plot(x, y, "o", ms=3, color=f"C{i}")
    ax.set_xlabel("t [s]" if T else "k")
    if title:
        ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def piecewise_signal(breaks, levels, T, n_samples, samples=None, title="u(t) and u(kT)"):
    """breaks: segment start times; levels: value on each segment (last extends to the end)."""
    t_end = n_samples * T
    fig, ax = _fig()
    xs, ys = [], []
    for i, (b, lv) in enumerate(zip(breaks, levels)):
        e = breaks[i + 1] if i + 1 < len(breaks) else t_end
        xs += [b, e]
        ys += [lv, lv]
    ax.plot(xs, ys, color="C0", lw=1.6, label="u(t)")
    if samples is not None:
        k = np.arange(len(samples))
        ml, sl, bl = ax.stem(k * T, samples, label="u(kT)")
        plt.setp(ml, color="C3", markersize=4)
        plt.setp(sl, color="C3", lw=0.8)
        plt.setp(bl, color="grey", lw=0.5)
    ax.set_xticks(np.arange(0, t_end + 1e-9, T))
    ax.tick_params(axis="x", labelrotation=45)
    ax.set_xlabel("t [s]")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def zplane(poles=(), zeros=(), extra=None, title="z-plane", circles=(), show_unit=True, lim=None):
    fig, ax = plt.subplots(figsize=(3.6, 3.6))
    th = np.linspace(0, 2 * np.pi, 400)
    if show_unit:
        ax.plot(np.cos(th), np.sin(th), color="k", lw=0.9)
    for r, lab in circles:
        ax.plot(r * np.cos(th), r * np.sin(th), "--", lw=0.8, label=lab)
    zeros = np.atleast_1d(np.asarray(zeros, complex))
    poles = np.atleast_1d(np.asarray(poles, complex))
    if zeros.size:
        ax.plot(zeros.real, zeros.imag, "o", mfc="none", mec="C0", ms=8, mew=1.5, label="zeros")
    if poles.size:
        ax.plot(poles.real, poles.imag, "x", color="C3", ms=8, mew=2, label="poles")
    if extra:
        for pts, style, lab in extra:
            pts = np.atleast_1d(np.asarray(pts, complex))
            ax.plot(pts.real, pts.imag, style, label=lab, ms=7)
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)
    m = max(1.25, *(abs(p) * 1.15 for p in np.concatenate([poles, zeros])) if (poles.size + zeros.size) else [1.25])
    if lim:
        m = lim
    ax.set_xlim(-m, m)
    ax.set_ylim(-m, m)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    return fig


def mapping_figure(T=0.2, zetas=(0.2, 0.5, 0.8), sigmas=(0.5, 1, 2)):
    """Lines of constant ζ (log spirals) and constant σ (circles) in the z-plane."""
    fig, ax = plt.subplots(figsize=(4.0, 4.0))
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), "k", lw=1, label="|z| = 1 (s = jω)")
    for s in sigmas:
        r = math.exp(-s * T)
        ax.plot(r * np.cos(th), r * np.sin(th), "--", lw=0.8, label=f"σ = −{s} → |z| = {r:.3f}")
    ratio = np.linspace(0, 0.5, 200)
    for zt in zetas:
        mag = np.exp(-2 * np.pi * zt / np.sqrt(1 - zt ** 2) * ratio)
        ang = 2 * np.pi * ratio
        z = mag * np.exp(1j * ang)
        ax.plot(z.real, z.imag, lw=1.2, label=f"ζ = {zt}")
        ax.plot(z.real, -z.imag, lw=1.2, color=ax.lines[-1].get_color())
    ax.set_aspect("equal")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_title(f"s→z mapping, T = {T} s")
    ax.legend(fontsize=6, loc="lower left")
    fig.tight_layout()
    return fig


def aliasing_figure(f_sig=1.0, f_s=1.25, t_end=4.0):
    fig, ax = _fig(5.4, 2.6)
    t = np.linspace(0, t_end, 2000)
    ax.plot(t, np.sin(2 * np.pi * f_sig * t), lw=1, label=f"x(t)=sin(2π·{f_sig}t)")
    fa = abs(f_sig - round(f_sig / f_s) * f_s)
    ax.plot(t, np.sin(2 * np.pi * (f_sig - round(f_sig / f_s) * f_s) * t), "--", lw=1,
            label=f"alias {fa:.2f} Hz")
    Ts = 1 / f_s
    k = np.arange(0, t_end / Ts + 1e-9)
    ax.plot(k * Ts, np.sin(2 * np.pi * f_sig * k * Ts), "o", color="C3", ms=5, label=f"samples, f_s={f_s} Hz")
    ax.set_xlabel("t [s]")
    ax.legend(fontsize=7, loc="upper right")
    ax.set_title("Aliasing: both signals give identical samples")
    fig.tight_layout()
    return fig


def zoh_figure(T=0.25, quant=None):
    fig, ax = _fig(5.4, 2.6)
    t = np.linspace(0, 2, 1000)
    x = 1 + 1.5 * np.sin(1.4 * t) * np.exp(-0.2 * t) + 0.3 * t
    ax.plot(t, x, lw=1.5, label="x(t)")
    k = np.arange(0, 2 / T)
    xs = 1 + 1.5 * np.sin(1.4 * k * T) * np.exp(-0.2 * k * T) + 0.3 * k * T
    if quant:
        xs = np.round(xs / quant) * quant
    ax.step(np.append(k * T, 2), np.append(xs, xs[-1]), where="post", color="C3", label="ZOH output")
    ax.plot(k * T, xs, "o", color="C3", ms=4)
    ax.set_xlabel("t [s]")
    ax.set_title("Zero-order hold: staircase ≈ signal delayed by T/2")
    ax.legend(fontsize=7)
    fig.tight_layout()
    return fig


def pole_response_grid():
    """Pole location ↔ impulse response (formula sheet p.12 style)."""
    poles = [0.6, 0.95, 1.0, -0.6, -1.0, 1.1]
    fig, axes = plt.subplots(2, 3, figsize=(6.2, 3.2))
    for ax, p in zip(axes.ravel(), poles):
        k = np.arange(12)
        y = p ** k
        ax.stem(k, y, basefmt=" ")
        ax.set_title(f"pole p = {p}", fontsize=8)
        ax.tick_params(labelsize=6)
    fig.suptitle("Impulse response pᵏ for real poles", fontsize=9)
    fig.tight_layout()
    return fig


def root_locus_figure(num_z, den_z, K_marks=(), title="Root locus (K > 0)"):
    """Numerically traced root locus for G_o = K num/den (numpy order)."""
    fig, ax = plt.subplots(figsize=(3.8, 3.8))
    th = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(th), np.sin(th), "k", lw=0.8)
    Ks = np.concatenate([np.linspace(0, 1, 200), np.logspace(0, 2.5, 300)])
    n = len(den_z) - 1
    nn = np.concatenate([np.zeros(len(den_z) - len(num_z)), num_z])
    pts = []
    for K in Ks:
        pts.append(np.roots(np.asarray(den_z) + K * nn))
    pts = np.array([np.sort_complex(p) for p in pts])
    ax.plot(pts.real, pts.imag, ".", ms=1.2, color="C0")
    ax.plot(np.roots(den_z).real, np.roots(den_z).imag, "x", color="C3", ms=8, mew=2)
    if len(num_z) > 1:
        zr = np.roots(num_z)
        ax.plot(zr.real, zr.imag, "o", mfc="none", mec="C2", ms=8, mew=1.5)
    for K, lab in K_marks:
        r = np.roots(np.asarray(den_z) + K * nn)
        ax.plot(r.real, r.imag, "s", ms=5, color="C1", label=lab)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    ax.set_aspect("equal")
    ax.set_title(title)
    if K_marks:
        ax.legend(fontsize=7)
    fig.tight_layout()
    _ = n
    return fig
