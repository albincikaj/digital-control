"""Theory flashcards for the closed-book part (15 P).

Each card: id, topic, q, a (model answer, markdown+LaTeX), rubric [(criterion, points)], src, exam (past exam tag or "").
Model answers follow the lecture notes (Jakubek/Hametner/Schirrer) wording; grader remarks from the two
corrected past exams are turned into rubric items ("Def!", "why?", "with respect to …").
"""

CARDS = [
    # ------------------------------------------------------------------ Ch. 2
    dict(id="zt_def", topic="zt_basics", exam="2017 Th.e (2 P)",
         q="State the definition of the z-transform.",
         a=r"""For a sampled signal $x(kT)$, $k = 0,1,2,\dots$ with $x(kT) = 0$ for $k<0$ (one-sided):
$$X(z) = \mathcal Z\{x(kT)\} = \sum_{k=0}^{\infty} x(kT)\,z^{-k}$$
$z$ is a complex variable. It is the Laplace transform of the impulse-sampled signal $x^*(t)=\sum x(kT)\delta(t-kT)$ with $z = e^{Ts}$:
$X(z) = X^*(s)|_{s=\frac{1}{T}\ln z}$. The series converges for $|z| > R$ if $|x(kT)| < KR^k$.""",
         rubric=[("Formula Σ_{k=0}^{∞} x(kT) z^{−k} written correctly", 1.0), ("Named: samples x(kT), one-sided (x=0 for k<0), z complex", 0.5),
                 ("Link z = e^{Ts} / Laplace of impulse-sampled signal", 0.5)],
         src="Book Def. 2.1, Sec. 3.2; grader 2017: 'Def!' when only z = e^{Ts} was given"),
    dict(id="zt_inv_def", topic="zt_inverse", exam="",
         q="Define the inverse z-transform and name the three practical methods to compute it.",
         a=r"""$$x(kT) = \mathcal Z^{-1}\{X(z)\} = \frac{1}{2\pi j}\oint_C X(z)\,z^{k-1}\,dz$$
$C$: counter-clockwise closed path around the origin enclosing all poles of $X(z)z^{k-1}$.
Methods: **direct (long) division** into a power series in $z^{-1}$ (first few samples), **partial fraction expansion** of $X(z)/z$ + table (closed form), **computational method** ($X = \frac{N}{D}U$ with $U = 1$, i.e. Kronecker-delta input, solve the difference equation recursively).""",
         rubric=[("Contour-integral formula", 1.0), ("Three methods named", 1.0)], src="Book Def. 2.2, Sec. 2.3"),
    dict(id="zt_unique", topic="zt_inverse", exam="2016 Th.a (2 P)",
         q="Consider X(z). Does its inverse z-transform yield a unique x(kT)? A unique x(t)? Illustrate.",
         a=r"""**x(kT): yes**, unique. **x(t): no** — the z-transform only contains the values at the sampling instants; infinitely many continuous signals pass through the same samples (e.g. two different curves through identical points, or $\sin\omega t$ and $\sin(\omega+n\omega_s)t$ — aliasing).
Sketch: sample points plus **two different curves** through them.""",
         rubric=[("x(kT) unique: yes", 0.5), ("x(t) unique: no", 0.5), ("Diagram with TWO different x(t) through the same samples", 1.0)],
         src="Book remark Sec. 2.3; grader 2016: diagram needed a second x(t) with the same x(kT)"),
    dict(id="zt_shift", topic="zt_basics", exam="",
         q="State the shift-right and shift-left theorems.",
         a=r"""Shift right (delay): $\mathcal Z\{x(kT-nT)\} = z^{-n}X(z)$ (with $x = 0$ for $k<0$).
Shift left: $\mathcal Z\{x(kT+nT)\} = z^{n}\left[X(z) - \sum_{k=0}^{n-1}x(kT)z^{-k}\right]$, e.g. $\mathcal Z\{x(k+2)\} = z^2X - z^2x(0) - zx(1)$.""",
         rubric=[("Shift right z^{−n}X(z)", 1.0), ("Shift left incl. initial-value terms", 1.0)], src="Book Theorems 2.3, 2.4"),
    dict(id="zt_ivt_fvt", topic="zt_basics", exam="",
         q="State the initial and final value theorems (with the validity condition).",
         a=r"""Initial value: $x(0) = \lim_{z\to\infty}X(z)$.
Final value: $\lim_{k\to\infty}x(kT) = \lim_{z\to1}\left[(1-z^{-1})X(z)\right]$, **only if the final value exists**, i.e. all poles of $(1-z^{-1})X(z)$ lie strictly inside the unit circle (system stable). Counter-example: $1/(1-z^{-1}+z^{-2})$ (poles on |z| = 1) — FVT gives 0 but $y(k)$ oscillates forever.""",
         rubric=[("IVT formula", 0.5), ("FVT formula with (1 − z⁻¹)", 1.0), ("Condition: limit exists / poles inside unit circle", 0.5)],
         src="Book Theorems 2.5, 2.6; Exercise book 2.9"),
    dict(id="zt_conv", topic="diff_eq", exam="",
         q="State the real convolution theorem and the convolution summation.",
         a=r"""$X_1(z)X_2(z) = \mathcal Z\left\{\sum_{h=0}^{k}x_1(hT)x_2[(k-h)T]\right\}$ (causal sequences).
Hence $y(kT) = \sum_{h=0}^{k} g[(k-h)T]\,u(hT) = \sum_{h=0}^{k}u[(k-h)T]\,g(hT)$ with the weighting sequence $g = \mathcal Z^{-1}\{G(z)\}$.""",
         rubric=[("Product ↔ convolution sum", 1.0), ("y = Σ g(k−h)u(h)", 1.0)], src="Book Theorem 2.7, Sec. 2.4.4"),
    dict(id="ptf_def", topic="diff_eq", exam="",
         q="Define the pulse transfer function and the weighting sequence.",
         a=r"""From the difference equation $y(k) + a_1y(k-1) + \dots + a_ny(k-n) = b_0u(k-d) + \dots + b_nu(k-n-d)$ with zero initial conditions:
$$G(z) = \frac{Y(z)}{U(z)} = \frac{b_0 + b_1z^{-1} + \dots + b_nz^{-n}}{1 + a_1z^{-1} + \dots + a_nz^{-n}}z^{-d}$$
Weighting sequence $g(kT) = \mathcal Z^{-1}\{G(z)\}$ = response to the Kronecker delta $\delta_0(k)$ (since $U(z)=1 \Rightarrow Y = G$).""",
         rubric=[("G = Y/U, zero initial conditions, polynomial form", 1.0), ("g(k) = Z⁻¹{G} = pulse response", 1.0)], src="Book Sec. 2.4.2–2.4.3"),
    dict(id="deadtime", topic="diff_eq", exam="",
         q="How is a dead time represented in discrete time? Which assumption is made?",
         a=r"""$y(t) = u(t - T_t) \Rightarrow y(kT) = u(kT - dT)$ with $T_t = dT$ (**dead time approximated by an integer multiple d of T**). z-domain: $Y(z) = z^{-d}U(z)$.""",
         rubric=[("z^{−d}", 1.0), ("T_t = d·T, d integer", 1.0)], src="Book Sec. 2.4.1"),
    # ------------------------------------------------------------------ sampling
    dict(id="shannon", topic="sampling", exam="2016 Th.b (2 P), 2017 Th.c (1.5 P)",
         q="Summarise (verbally, briefly) the main message of Shannon's sampling theorem.",
         a=r"""A **band-limited** signal with no frequency components above $\omega_1$ can be **completely reconstructed** from its samples if the sampling frequency satisfies $\omega_s = 2\pi/T > 2\omega_1$.
**Why:** the spectrum of the impulse-sampled signal is periodic, $X^*(j\omega) = \frac1T\sum_n X(j(\omega - n\omega_s))$. For $\omega_s > 2\omega_1$ the primary and complementary components do not overlap and an ideal low-pass filter recovers $x(t)$; otherwise they overlap → **aliasing** (information lost).""",
         rubric=[("ω_s > 2ω_max (strict) for a band-limited signal", 1.0), ("Reason: periodic spectrum, overlap ⇒ aliasing / reconstruction by ideal low-pass", 1.0)],
         src="Book Sec. 3.4.1; grader 2016: 'why?' when only the inequality was given"),
    dict(id="aliasing", topic="sampling", exam="",
         q="What is aliasing? Give an example.",
         a=r"""If $\omega_s < 2\omega_1$ the shifted spectra overlap: the spectrum at $\omega_2$ also contains components from $n\omega_s \pm \omega_2$, which can no longer be distinguished.
Example (Book Ex. 3.2): $x(t) = \sin(\omega_2t + \theta)$ and $y(t) = \sin((\omega_2 + n\omega_s)t + \theta)$ give **identical samples** because $\sin(\omega_2kT + 2\pi kn + \theta) = \sin(\omega_2kT + \theta)$.""",
         rubric=[("Overlap of spectra / high frequency appears as low frequency", 1.0), ("Example with ω and ω + nω_s", 1.0)], src="Book Sec. 3.4, Ex. 3.2"),
    dict(id="ideal_lp", topic="sampling", exam="",
         q="Why is the ideal low-pass filter (needed for perfect reconstruction) not realisable?",
         a=r"""Its weighting function $g_I(t) = \frac1T\frac{\sin(\omega_st/2)}{\omega_st/2}$ is non-zero for $t<0$: it would respond **before** the input impulse is applied → **non-causal**, physically impossible. Practical reconstruction uses the zero-order hold (non-ideal low-pass).""",
         rubric=[("g_I(t) ≠ 0 for t < 0", 1.0), ("⇒ non-causal", 1.0)], src="Book Sec. 3.4, Fig. 3.3"),
    dict(id="zoh", topic="sampling", exam="",
         q="Give the transfer function and the frequency-response properties of the zero-order hold.",
         a=r"""$H_0(s) = \dfrac{1-e^{-Ts}}{s}$ — holds each sample constant for one period (staircase).
$|H_0(j\omega)| = T\left|\dfrac{\sin(\omega T/2)}{\omega T/2}\right|$, $\arg H_0 = -\omega T/2$ (+ sign jumps of sin): a non-ideal low-pass with **phase lag like a dead time T/2** and unwanted side lobes above $\omega_s$. For continuous design: $H_0 \approx \dfrac{1}{1 + 0.5Ts}$ (Padé of $e^{-Ts/2}$, gain normalised).""",
         rubric=[("H₀(s) formula", 1.0), ("Low-pass, delay ≈ T/2 (phase −ωT/2)", 1.0)], src="Book Sec. 3.1, 3.4, 4.2.1"),
    dict(id="zoh_quant", topic="sampling", exam="2016 Th.g (2 P)",
         q="A continuous signal is sampled with f_s = 4 Hz, quantised with interval 0.5 (round to nearest level) and passed through a ZOH. How do you draw the result?",
         a=r"""1. Sample every $T = 1/f_s = 0.25$ s (at $t = 0, 0.25, 0.5, \dots$).
2. Round each sample to the **nearest** multiple of 0.5.
3. Hold that value **constant until the next sampling instant** → staircase starting exactly at the sampling instants (it lags the signal by ≈ T/2 on average).""",
         rubric=[("Samples at t = kT, T = 0.25 s", 0.5), ("Rounded to nearest 0.5 level", 0.5), ("Held constant over [kT, (k+1)T) — staircase", 1.0)],
         src="Exam 2016 Th.g; Book Sec. 1.2"),
    dict(id="impulse_sampling", topic="sampling", exam="",
         q="What is the impulse-sampling model and when is it valid?",
         a=r"""The real sampler (finite pulse width) is replaced by a modulator with the carrier $\delta_T(t) = \sum\delta(t-kT)$: $x^*(t) = \sum_k x(kT)\delta(t-kT)$, $X^*(s) = \sum_k x(kT)e^{-kTs}$. Valid if the sampling duration is **very small compared to T** and a **hold element follows** the sampler.""",
         rubric=[("x*(t) = Σ x(kT)δ(t−kT)", 1.0), ("Validity: pulse width ≪ T, hold follows", 1.0)], src="Book Sec. 3.1"),
    dict(id="signals_dcs", topic="sampling", exam="",
         q="Which signal types occur in a digital control loop and which components convert between them?",
         a=r"""Continuous-time/continuous-value (plant), discrete-time (sampled), and discrete-time/discrete-value (quantised, digital). **Sample & hold + A/D converter** (sampling + quantisation, multiplexer for several channels) on the measurement side; **D/A converter + hold** (demultiplexer) on the actuator side; the computer runs the control algorithm.""",
         rubric=[("Analog / sampled / digital signals", 1.0), ("S/H + A/D, D/A + hold", 1.0)], src="Book Ch. 1"),
    # ------------------------------------------------------------------ ZOH / closed loop
    dict(id="zoh_ptf", topic="zoh_plant", exam="",
         q="Derive the pulse transfer function of a zero-order hold in series with a plant G_P(s).",
         a=r"""$G(s) = (1-e^{-Ts})\dfrac{G_P(s)}{s} = (1-e^{-Ts})G_1(s)$. Since $e^{-Ts}G_1(s)$ is $g_1(t-T)$, whose z-transform is $z^{-1}G_1(z)$:
$$G(z) = (1-z^{-1})\,\mathcal Z\left\{\frac{G_P(s)}{s}\right\}$$""",
         rubric=[("Split H₀ = (1 − e^{−Ts})/s", 1.0), ("e^{−Ts} ↔ z^{−1}; final formula", 1.0)], src="Book Sec. 3.3, Ex. 3.1"),
    dict(id="cascade", topic="zoh_plant", exam="",
         q="Why is G₁(z)G₂(z) ≠ G₁G₂(z)? When is which one used?",
         a=r"""With a **sampler between** the blocks, the second block sees an impulse-sampled input: $Y(z) = G_1(z)G_2(z)X(z)$. **Without** a sampler in between, the continuous product must be transformed together: $G_1G_2(z) = \mathcal Z\{G_1(s)G_2(s)\}$, which differs in general (e.g. $1/(s+1)$ and $1/(s+2)$, Book Ex. 3.4).""",
         rubric=[("Sampler between ⇒ product of z-transforms", 1.0), ("No sampler ⇒ transform of the product, generally different", 1.0)], src="Book Sec. 3.5.3, Ex. 3.4"),
    dict(id="std_loop", topic="closed_loop", exam="",
         q="Sketch the standard digital control loop and give G_W(z).",
         a=r"""$w \to (-) \to$ sampler + A/D $\to e(kT) \to$ digital controller $G_D \to u(kT) \to$ D/A + hold $\to$ plant $G_P \to y$, disturbance $z$ via $G_{PZ}$ added at the output; $y$ fed back.
With $G(z) = (1-z^{-1})\mathcal Z\{G_P/s\}$: $$G_W(z) = \frac{G_D(z)G(z)}{1+G_D(z)G(z)}$$""",
         rubric=[("Block chain incl. sampler/AD, controller, DA/hold, plant", 1.0), ("G_W formula", 1.0)], src="Book Sec. 3.5.5"),
    dict(id="disturbance_tf", topic="closed_loop", exam="Exam P2d (1 P) 2016/2017",
         q="Can a disturbance pulse transfer function G_d(z) = Y(z)/D(z) be written when d acts on the continuous plant? Reason.",
         a=r"""**In general no.** The disturbance is not sampled before it passes through continuous blocks, so the output contains $\mathcal Z\{G_{PZ}(s)Z(s)\} = G_{PZ}Z(z)$ which **cannot be factored** into (something)·$Z(z)$: $Y(z) = \dfrac{G_{PZ}Z(z)}{1 + G_D(z)G(z)}$ (book eq. 3.42). Only the response to a *specific* disturbance signal can be computed.""",
         rubric=[("No", 0.5), ("Reason: no sampler on d ⇒ only G_PZ Z(z) exists", 0.5)], src="Book Sec. 3.5.5; grader 2016 accepted 'no input sampler for d'"),
    dict(id="pid_pos_vel", topic="closed_loop", exam="",
         q="Position vs velocity algorithm of the discrete PID controller — difference and use case?",
         a=r"""Position algorithm computes $u(k)$ itself: $u(k) = u(k-1) + d_0e(k) + d_1e(k-1) + d_2e(k-2)$. Velocity algorithm computes only the **increment** $\Delta u(k) = u(k) - u(k-1) = d_0e(k) + d_1e(k-1) + d_2e(k-2)$ — used when the **actuator itself integrates** (e.g. stepper motor). Euler: $d_0 = K_p(1+T_V/T)$, $d_1 = K_p(T/T_N - 2T_V/T - 1)$, $d_2 = K_pT_V/T$.""",
         rubric=[("Absolute u vs increment Δu", 1.0), ("Velocity form for integrating actuators", 1.0)], src="Book Sec. 3.5.6"),
    # ------------------------------------------------------------------ mapping / stability
    dict(id="mapping", topic="mapping", exam="",
         q="Describe the mapping z = e^{Ts}: what happens to the imaginary axis, the left half plane, the primary strip?",
         a=r"""$|z| = e^{T\sigma}$, $\arg z = T\omega + 2\pi k$. The imaginary axis maps onto the **unit circle** (infinitely often), the open LHP into the **interior** of the unit circle, RHP outside. The **primary strip** $|\omega| < \omega_s/2$ maps one-to-one; $\pm\omega_s/2$ → $z = -1$. The mapping is unique only in the direction $s \to z$. Lines σ = const → circles, ω = const → rays, ζ = const → logarithmic spirals.""",
         rubric=[("jω-axis → unit circle, LHP → inside", 1.0), ("primary strip / uniqueness s→z only", 0.5), ("circles, rays, spirals", 0.5)], src="Book Sec. 3.6"),
    dict(id="rel_stab_region", topic="mapping", exam="2016 Th.i (1 P)",
         q="Sketch a region of relative stability in the z-domain and indicate the region that guarantees it.",
         a=r"""Absolute stability margin $\sigma < -\sigma_0$ ⇒ inside the circle $|z| < e^{-\sigma_0T}$. Minimum damping $\zeta \ge \zeta_0$ ⇒ inside the **logarithmic spiral** $|z| = \exp\left(-\frac{\zeta_0}{\sqrt{1-\zeta_0^2}}\arg z\right)$ (and its mirror image). Admissible region: the intersection — a cardioid-like region inside the unit circle around the positive real axis.""",
         rubric=[("Unit circle + inner circle e^{−σT} or ζ-spiral drawn", 0.5), ("Admissible region clearly marked", 0.5)], src="Book Sec. 3.6, Fig. 3.11/3.12"),
    dict(id="pole_resp", topic="mapping", exam="",
         q="How does the location of a real or complex z-plane pole show up in the transient response?",
         a=r"""Pole $p$ contributes $p^k$: $0<p<1$ monotonic decay (faster near 0), $p = 1$ constant (integrator), $p>1$ monotonic growth, $-1<p<0$ **alternating** sign decay, $p=-1$ undamped alternation. Complex pair $re^{\pm j\theta}$: oscillation with radius r (decay rate) and θ = ω_dT (frequency); $p = 0$ → dead-beat (finite settling).""",
         rubric=[("Real positive/negative behaviours", 1.0), ("Complex: r → damping, angle → frequency", 1.0)], src="Book Sec. 4.3.3; Formelsammlung p. 12–13"),
    dict(id="stab_def", topic="stability", exam="",
         q="Define asymptotic stability, stability limit and instability of a closed loop in the z-domain.",
         a=r"""Characteristic polynomial $P(z) = B_o(z) + A_o(z)$ of $1 + G_o(z) = 0$.
- **Asymptotically stable:** all closed-loop poles strictly inside the unit circle.
- **Stability limit:** a single pole at $z = 1$ or $z = -1$, or simple complex pairs on the unit circle (rest inside).
- **Unstable:** at least one pole outside (or multiple poles on) the unit circle.
Closed-loop zeros have no influence on stability.""",
         rubric=[("Inside unit circle ⇔ asymptotically stable", 1.0), ("Limit / unstable cases", 1.0)], src="Book Defs. 3.1–3.3"),
    dict(id="jury_conditions", topic="stability", exam="Exam P3 (5 P)",
         q="List the Jury stability conditions for P(z) = a_n zⁿ + … + a₀ (a_n > 0) and how the table is built.",
         a=r"""Rows: $a_0, a_1, \dots, a_n$ and reversed; $b_k = \begin{vmatrix}a_0 & a_{n-k}\\ a_n & a_k\end{vmatrix}$, $c_k = \begin{vmatrix}b_0 & b_{n-1-k}\\ b_{n-1} & b_k\end{vmatrix}$, …, last row has 3 elements.
Asymptotically stable **iff all**: $P(1) > 0$, $(-1)^nP(-1) > 0$, $|a_0| < |a_n|$, $|b_0| > |b_{n-1}|$, $|c_0| > |c_{n-2}|$, …, $|s_0| > |s_2|$ (n + 1 conditions).""",
         rubric=[("P(1) > 0 and (−1)ⁿP(−1) > 0", 1.0), ("|a₀| < |a_n| and |b₀| > |b_{n−1}| …", 1.0)], src="Book Theorem 3.1; grader 2017: missing P(1), P(−1) cost 2 P"),
    dict(id="w_transform", topic="stability", exam="",
         q="Explain the w-transformation stability test.",
         a=r"""$w = \frac{z-1}{z+1}$, $z = \frac{1+w}{1-w}$ maps the interior of the unit circle onto the **left half w-plane**. Substitute into $P(z) = 0$, multiply by $(1-w)^n$ and apply the **Hurwitz criterion** to $P(w)$. The w-plane is only qualitatively equivalent to the s-plane (strong frequency distortion) — fine for stability checks.""",
         rubric=[("Mapping unit disc → LHP", 1.0), ("Substitute, then Hurwitz", 1.0)], src="Book Sec. 3.7.2, Ex. 3.11/3.12"),
    # ------------------------------------------------------------------ Ch. 4
    dict(id="disc_methods", topic="discretization", exam="",
         q="Compare backward difference, Tustin and matched pole-zero discretisation.",
         a=r"""**Backward difference** $s = \frac{1-z^{-1}}{T}$: simple, always gives a stable filter (LHP → circle of radius 0.5 centred at 0.5), strong frequency distortion.
**Tustin** $s = \frac{2}{T}\frac{1-z^{-1}}{1+z^{-1}}$: maps LHP exactly onto the unit disc (stable ↔ stable), equal numbers of poles and zeros, frequency warping.
**Matched pole-zero**: poles and finite zeros mapped by $z = e^{sT}$, zeros at infinity → $z = -1$ (or 0), gain matched at $z=1/s=0$ (low-pass) or $z=-1/s=\infty$ (high-pass); complex pairs as a unit.""",
         rubric=[("All three substitution rules", 1.0), ("One property each (stability, warping, gain matching)", 1.0)], src="Book Sec. 4.2.2"),
    dict(id="sampling_time", topic="discretization", exam="2016 P4a (1 P)",
         q="How is the sampling time chosen for a control loop, and why not just by Shannon?",
         a=r"""Rules of thumb on the desired closed-loop step response: aperiodic $T \le 0.125\,T_1$ (T₁ from the tangent construction), oscillatory $T \le 0.125\,T_2$ ($T_2$ period of the oscillation) — about 8 samples per characteristic time. Shannon $T < 1/(2f_m)$ is not sufficient because loop signals are not band-limited and the ZOH adds a delay ≈ T/2 that eats phase margin.""",
         rubric=[("T ≤ 0.125·T₁ or 0.125·T₂", 1.0), ("Reason why Shannon is not enough", 1.0)], src="Book Sec. 4.1, Fig. 4.1"),
    dict(id="rl_conditions", topic="root_locus", exam="",
         q="State the magnitude and angle conditions of the root locus.",
         a=r"""For $G_o(z) = K\frac{\prod(z-q_\mu)}{\prod(z-p_\nu)}$, a point $z$ is on the root locus if
$$\sum\arg(z-q_\mu) - \sum\arg(z-p_\nu) = (2k+1)\pi\ (K>0)$$ and its gain follows from $$|K|\frac{\prod|z-q_\mu|}{\prod|z-p_\nu|} = 1.$$ Rules are identical to the s-plane; only the stability boundary is the unit circle.""",
         rubric=[("Angle condition", 1.0), ("Magnitude condition", 1.0)], src="Book Sec. 4.3.4 / Appendix"),
    dict(id="static_err", topic="root_locus", exam="",
         q="Define the position and velocity error constants of a digital loop.",
         a=r"""$e_p = \lim_{z\to1}\frac{1}{1+G_DG} = \frac{1}{1+K_p}$, $K_p = \lim_{z\to1}G_D(z)G(z)$.
$e_v = \lim_{z\to1}\frac{Tz^{-1}}{(1-z^{-1})G_DG} = \frac{1}{K_v}$, $K_v = \lim_{z\to1}\frac{(1-z^{-1})G_DG}{T}$. An integrator (pole at z = 1) in the open loop ⇒ $e_p = 0$.""",
         rubric=[("e_p and K_p", 1.0), ("e_v and K_v", 1.0)], src="Book Sec. 4.3.1"),
    dict(id="mfc_idea", topic="analytic_design", exam="2017 Th.h (2 P)",
         q="State the basic idea of the model following controller (MFC).",
         a=r"""Prescribe the **desired closed-loop reference behaviour** $G_W(z) = \frac{B_W}{A_W}z^{-d}$ (the 'model'); the loop should follow it. Controller structure with three polynomials: $PU = FW - QY$ (prefilter F, feedforward 1/P, feedback Q). Their coefficients follow from **comparing coefficients** of $G_W = \frac{FBz^{-d}}{PA + QBz^{-d}}$ with the desired one (Diophantine equation $\tilde PA + QB^-z^{-(1+d)} = A_WA_o$).
Rules: $G_W$ must contain the plant dead time; only well-damped zeros inside the unit circle ($B^+$) may be cancelled, others ($B^-$) stay in $G_W$; an observer polynomial $A_o$ makes the system solvable; integral action via $\tilde P(1) = 0$.""",
         rubric=[("Desired closed-loop TF prescribed (model)", 1.0), ("F, P, Q polynomials by coefficient comparison", 0.5), ("Dead time / B⁻ zeros kept, A_o", 0.5)],
         src="Book Sec. 4.4"),
    dict(id="ringing", topic="analytic_design", exam="",
         q="What is 'ringing' and how is it avoided?",
         a=r"""An oscillating control variable $u(k)$ (alternating sign every sample) although $y$ looks fine. Cause: a controller pole near $z = -1$, typically from cancelling a plant zero near $-1$ (Book Ex. 4.7: pole at $-0.9051$ in $G_{UW}$). Avoid: do not cancel such zeros — put them into $B^-$ ($\tilde G^-$ for IMC).""",
         rubric=[("u oscillates sample-to-sample", 1.0), ("Cancelled zero near −1; keep it in B⁻", 1.0)], src="Book Ex. 4.7, Sec. 4.6 remarks"),
    dict(id="deadbeat_idea", topic="analytic_design", exam="",
         q="What is a dead-beat controller and what are its requirements/drawbacks?",
         a=r"""The closed loop $F_W(z) = \sum f_{Wi}z^{-(i+d)}$ is a **finite polynomial in z⁻¹**: after a step the output reaches the set point in a minimal finite number of samples and stays (no ripple if $G_{UW}$ is also a polynomial). Requirements: contain the dead time, $F_W(1) = 1$ (integral behaviour of the open loop), never cancel plant poles on/outside the unit circle. Stable plant, $C = 1$: $F_W = \frac{B}{B(1)}z^{-d}$, $G_D = \frac{A}{B(1) - Bz^{-d}}$, $u(0) = 1/B(1)$. Drawback: large control values; limit $u(0)$ via $C(z) = 1 + c_1z^{-1}$ (one more step).""",
         rubric=[("Finite settling time, F_W polynomial", 1.0), ("Requirements / large u, constrained by C(z)", 1.0)], src="Book Sec. 4.5"),
    dict(id="imc_idea", topic="analytic_design", exam="",
         q="Explain the principle of internal model control (IMC) and its design steps.",
         a=r"""The controller contains a **model** $\tilde G$ of the plant; only the difference $Y - \tilde Y$ (model error + disturbance) is fed back. Equivalent standard controller $G_C = \frac{G_C^*}{1 - G_C^*\tilde G}$. Perfect model: $Y = G_C^*GW + (1 - G_C^*G)Z$.
Design: 1) factor $\tilde G = \tilde G^+\tilde G^-$ with $\tilde G^-$ containing dead time $z^{-d-1}$, zeros outside the unit circle and near $-1$, $\tilde G^-(1) = 1$; 2) $G_C^* = F/\tilde G^+$ with a low-pass $F$, $F(1) = 1$ (tuning parameter). Then $G_W = \tilde G^-F$.""",
         rubric=[("Model in the controller, Y − Ỹ fed back", 1.0), ("Factorisation + inverse of G̃⁺ + filter F", 1.0)], src="Book Sec. 4.6"),
    # ------------------------------------------------------------------ Ch. 5
    dict(id="ss_discrete", topic="ss_models", exam="",
         q="Give the discrete-time state-space model and its solution.",
         a=r"""$x(k+1) = Gx(k) + hu(k)$, $y(k) = c^Tx(k) + du(k)$.
Solution: $x(k) = G^kx(0) + \sum_{j=0}^{k-1}G^{k-j-1}hu(j)$, transition matrix $\Phi(k) = G^k = \mathcal Z^{-1}\{z(zI-G)^{-1}\}$. Pulse TF: $G_{PU}(z) = c^T(zI-G)^{-1}h + d$; its poles are the eigenvalues of G.""",
         rubric=[("Model equations", 1.0), ("Solution / transfer function", 1.0)], src="Book Sec. 5.2, 5.4"),
    dict(id="ss_c2d", topic="ss_models", exam="",
         q="How are G and h obtained from the continuous model ẋ = Ax + bu (ZOH)?",
         a=r"""With $u$ constant over each interval: $G = e^{AT}$, $h = \left(\int_0^Te^{A\mu}d\mu\right)b$. Practical: $G = Me^{\Lambda T}M^{-1}$ (eigenvectors M), $h = A^{-1}(G - I)b$ if A is invertible; general: $\exp\left(\begin{bmatrix}A&b\\0&0\end{bmatrix}T\right) = \begin{bmatrix}G&h\\0&1\end{bmatrix}$. Exact at the sampling instants (no approximation).""",
         rubric=[("G = e^{AT}", 1.0), ("h integral / formula", 1.0)], src="Book Sec. 5.3, Theorem 5.1"),
    dict(id="observability_def", topic="ctrb_obsv", exam="2017 Th.a (2 P)",
         q="Describe state observability and state its mathematical definition.",
         a=r"""A system $x(k+1) = Gx(k)$, $y(k) = c^Tx(k)$ is **completely state observable** if **every initial state x(0) can be determined from the observation of y(kT) over a finite number (n) of sampling periods**.
Criterion: $$\text{rank}\,Q_O = \text{rank}\begin{bmatrix}c^T\\c^TG\\\vdots\\c^TG^{n-1}\end{bmatrix} = n$$ (from $[y(0), \dots, y(n-1)]^T = Q_Ox(0)$ solvable).""",
         rubric=[("Verbal: any x(0) from n output samples", 1.0), ("Mathematical: rank Q_O = n with Q_O written out", 1.0)],
         src="Book Theorem 5.3; grader 2017: '✗ math. def.' when the rank condition was missing"),
    dict(id="controllability_def", topic="ctrb_obsv", exam="",
         q="Define complete state controllability and give the criterion.",
         a=r"""Completely state controllable if a piecewise constant input $u(kT)$ over (at most) n sampling periods exists that transfers **any initial state x(0) to any final state** $x_f$.
$$\text{rank}\,Q_C = \text{rank}\left[h\ \ Gh\ \cdots\ G^{n-1}h\right] = n$$""",
         rubric=[("Verbal definition", 1.0), ("rank Q_C = n", 1.0)], src="Book Theorem 5.2"),
    dict(id="ctrb_vs_stab", topic="ctrb_obsv", exam="2016 Th.e (2 P)",
         q="Describe the difference between full state controllability and stabilisability. Are all stabilisable systems fully controllable? Illustrate by an example.",
         a=r"""Controllable: every state can be steered anywhere (rank $Q_C = n$). **Stabilisable**: all **uncontrollable eigenmodes are asymptotically stable** (|λ| < 1) — the controllable part can be stabilised by feedback, the rest decays on its own.
Not every stabilisable system is controllable. **Example:** $x(k+1) = \begin{bmatrix}0.5&0\\0&0.8\end{bmatrix}x(k) + \begin{bmatrix}1\\0\end{bmatrix}u(k)$: mode 0.8 is uncontrollable ($Q_C$ rank 1) but stable ⇒ stabilisable, not controllable.""",
         rubric=[("Controllability definition", 0.5), ("Stabilisability: uncontrollable modes stable", 0.5), ("'No' + concrete example", 1.0)],
         src="Book Theorem 7.1; grader 2016: example was missing"),
    dict(id="detect_def", topic="ctrb_obsv", exam="",
         q="When is [G, Q] detectable?",
         a=r"""If for every eigenvalue $\lambda_i$ of G with $|\lambda_i| > 1$ the corresponding eigenvector satisfies $u_i^TQu_i > 0$, i.e. every **unstable mode is 'seen' in the cost function**.""",
         rubric=[("Unstable modes", 1.0), ("u_iᵀQu_i > 0 / appear in the cost", 1.0)], src="Book Theorem 7.2"),
    # ------------------------------------------------------------------ Ch. 6
    dict(id="state_fb", topic="pole_placement", exam="",
         q="State-vector feedback: control law, closed loop, design methods, reference gain.",
         a=r"""$u(k) = -k^Tx(k) + K_ww(k)$ ⇒ $x(k+1) = (G - hk^T)x(k) + K_whw(k)$. Choose $k^T$ so that $\det(zI - G + hk^T) = \prod(z-\lambda_i)$ — by **coefficient comparison** or **Ackermann** $k^T = [0\cdots1]Q_C^{-1}P(G)$ (requires controllability). $K_w = 1/(c^T[I - G + hk^T]^{-1}h)$ gives $G_W(1) = 1$ — but no robustness: model errors or constant disturbances cause a permanent error.""",
         rubric=[("Law and closed-loop matrix", 1.0), ("Pole placement method + K_w", 1.0)], src="Book Sec. 6.1, Ex. 6.1"),
    dict(id="integral_block", topic="pole_placement", exam="2017 Th.g (3 P)",
         q="Draw/describe the block diagram of a state vector feedback control system with integration of the control error.",
         a=r"""Signal flow: $w(k)$ → summing junction ($+w$, $-y$) → **discrete integrator** $v(k) = v(k-1) + w(k) - y(k)$ (sum block with a $q^{-1}$ feedback of $v$) → gain $K$ → summing junction ($+Kv$, $-k^Tx$) → $u(k)$ → plant ($h$, $q^{-1}I$, $G$ feedback, $c^T$) → $y(k)$. The **state vector** $x(k)$ is fed back through $k^T$ (double arrow), the **output** $y(k)$ to the first junction.
Law: $u(k) = -k^Tx(k) + Kv(k)$; augmented model $\hat G = \begin{bmatrix}G&0\\-c^TG&1\end{bmatrix}$, $\hat h = \begin{bmatrix}h\\-c^Th\end{bmatrix}$, $\hat k^T = [k^T, -K]$.""",
         rubric=[("Integrator of e = w − y with q⁻¹ loop", 1.0), ("Gain K and state feedback kᵀ subtracting", 1.0), ("Plant block with x and y feedback paths, labelled", 1.0)],
         src="Formelsammlung p. 21; grader 2017 gave 0 P to a diagram without the integrator structure"),
    dict(id="integral_why", topic="pole_placement", exam="",
         q="Why add integration of the control error to a state-feedback controller?",
         a=r"""With $K_w$ only, a constant disturbance or model mismatch leaves a **permanent control error** (Exercise 6.4). The integrator state $v$ forces $e = w - y \to 0$ in steady state ($G_W(1) = 1$ structurally), like the I-part of a PI controller. The augmented system must be controllable (rank $\hat Q_C = n+1$; holds if the plant is controllable and has no zero at z = 1).""",
         rubric=[("Steady-state error after disturbances/model errors", 1.0), ("Integrator ⇒ zero stationary error; augmented system", 1.0)], src="Book Sec. 6.3"),
    dict(id="deadbeat_sf", topic="pole_placement", exam="",
         q="What is a dead-beat state feedback controller?",
         a=r"""All closed-loop poles at the origin, $P(z) = z^n$ ⇒ Ackermann $k^T = [0\cdots1]Q_C^{-1}G^n$. $G - hk^T$ is nilpotent: every initial state reaches 0 in at most n steps; $G_W$ is a finite polynomial in $z^{-1}$ (Book Ex. 6.2). Large control effort.""",
         rubric=[("Poles at z = 0", 1.0), ("Settles in n steps / formula", 1.0)], src="Book Sec. 6.2"),
    dict(id="why_observer", topic="observers", exam="2016 Th.c (1 P)",
         q="Give one reason for utilising a state observer in state-space control architectures.",
         a=r"""State feedback needs the full state vector, but usually **not all states are measurable** (sensors expensive, impossible or noisy). The observer reconstructs $\hat x$ from the known input u and the measurements m (fewer sensors; with a minimum-order observer only the unmeasured states are estimated).""",
         rubric=[("Not all states measurable / fewer sensors", 1.0)], src="Book Sec. 6.4"),
    dict(id="pred_vs_curr", topic="observers", exam="2016 Th.d & 2017 Th.d (1 P)",
         q="Considering the measurement signal m(k), in which sense is the current observer different from the predictive observer?",
         a=r"""**Predictive:** $\hat x(k)$ is computed with measurements only up to $m(k-1)$ (it predicts one step ahead: $\hat x(k+1) = G\hat x(k) + hu(k) + P[m(k) - C^*\hat x(k)]$), so the control $u(k) = -k^T\hat x(k)$ does **not** use the current measurement.
**Current:** uses the **current measurement $m(k)$** to correct the estimate $\hat x(k)$ that is used for $u(k)$ (two steps: predict $z(k+1) = G\hat x(k) + hu(k)$, correct with $m(k+1)$). Error matrices: $G - PC^*$ vs. $G - PC^*G$.""",
         rubric=[("Predictive: x̂(k) from m up to k−1", 0.5), ("Current: uses m(k) for x̂(k) that enters u(k)", 0.5)],
         src="Book Sec. 6.4.2; grader comments 'to do what?' / 'current obs.?'"),
    dict(id="pred_obs_eq", topic="observers", exam="",
         q="Write the predictive observer equations and its error dynamics. How are observer poles chosen?",
         a=r"""$\hat x(k+1) = G\hat x(k) + hu(k) + P[m(k) - C^*\hat x(k)] = (G - PC^*)\hat x(k) + hu(k) + Pm(k)$. Error $\tilde x = x - \hat x$: $\tilde x(k+1) = (G - PC^*)\tilde x(k)$. Place eig(G − PC*) by coefficient comparison or duality (Ackermann on $G^T, C^{*T}$); requires observability. Observer poles **faster (closer to 0)** than the controller poles (e.g. Book Ex. 6.4: 0.2 vs 0.5 ± j0.5); too fast ⇒ noise sensitivity.""",
         rubric=[("Observer equation", 1.0), ("Error dynamics + pole choice", 1.0)], src="Book Sec. 6.4.1, Ex. 6.4"),
    dict(id="minorder", topic="observers", exam="",
         q="What is a minimum-order observer? Give its error equation.",
         a=r"""Only the $n - m$ **unmeasurable** states $x_b$ are estimated; the measured ones $x_a = m$ are used directly. Partition $G = \begin{bmatrix}G_{aa}&G_{ab}\\G_{ba}&G_{bb}\end{bmatrix}$; error $e(k+1) = (G_{bb} - PG_{ab})e(k)$, poles from $|zI - G_{bb} + PG_{ab}| = 0$ (requires rank of $[G_{ab}; G_{ab}G_{bb}; \dots]$ = n − m). Implementation via $\eta = x_b - Px_a$. If $x_a$ is heavily noise-corrupted, a full-order observer may perform better.""",
         rubric=[("Estimates only unmeasured states", 1.0), ("Error matrix G_bb − P G_ab", 1.0)], src="Book Sec. 6.4.3"),
    dict(id="separation", topic="observers", exam="",
         q="What does the separation principle state for state feedback with an observer?",
         a=r"""The closed-loop eigenvalues of plant + state feedback (on $\hat x$) + observer are the **union** of the controller poles eig(G − hkᵀ) and the observer poles eig(G − PC*). Controller and observer can be designed independently; the reference transfer function is the same as with measured states (observer modes are not excited by w if initialised correctly).""",
         rubric=[("Eigenvalues = controller ∪ observer", 1.0), ("Independent design", 1.0)], src="Book Sec. 6.4 (Fig. 6.4)"),
    # ------------------------------------------------------------------ Ch. 7
    dict(id="lqr_prereq", topic="lqr", exam="2016 Th.h (2 P), 2017 Th.b (1.5 P)",
         q="What are the prerequisites to guarantee a stable closed loop with an (infinite-horizon) LQR?",
         a=r"""1. **(G, H) stabilisable**: all uncontrollable eigenmodes are asymptotically stable (Theorem 7.1).
2. **[G, Q] detectable**: every unstable eigenmode is 'seen' by the state weighting, $u_i^TQu_i > 0$ (Theorem 7.2). (Plus R > 0, Q ⪰ 0.)
Controllability/observability are sufficient but **not necessary**.""",
         rubric=[("Stabilisability of (G, H)", 0.75), ("Detectability of [G, Q] (w.r.t. the weighting matrix!)", 0.75), ("(Controllability not necessary)", 0.5)],
         src="Book Sec. 7.3–7.4.2; graders: 'actually detectability', 'with respect to …'"),
    dict(id="lqr_cost", topic="lqr", exam="",
         q="Write the LQR cost function, the algebraic Riccati equation and the control law.",
         a=r"""$V = \frac12\sum_{i=0}^{\infty}\left[x^TQx + u^TRu\right]$ (finite horizon: $+\frac12x^T(N+1)Lx(N+1)$).
ARE: $S = Q + G^TSG - G^TSH(R + H^TSH)^{-1}H^TSG$ (positive definite solution).
Law: $u(k) = -(R + H^TSH)^{-1}H^TSG\,x(k) = -Kx(k)$ (MATLAB `dlqr`).""",
         rubric=[("Cost", 0.5), ("Riccati equation", 1.0), ("Control law with minus sign", 0.5)], src="Book Sec. 7.2–7.3; ⚠ formula sheet omits the minus in the finite-horizon law"),
    dict(id="lqr_weights", topic="lqr", exam="",
         q="How does the ratio q/r influence the LQR (scalar case)?",
         a=r"""**Strong control weight** $q/r \to 0$: stable plant → $u \to 0$, closed loop ≈ open loop; unstable plant $|a|>1$ → pole mirrored into the unit circle at $1/a$ (Book Ex. 7.3).
**Strong state weight** $q/r \to \infty$: $k \to a/b$, closed-loop pole → 0 (dead-beat-like, large inputs).""",
         rubric=[("r large: minimal effort, unstable poles mirrored 1/a", 1.0), ("q large: fast, pole → 0", 1.0)], src="Book Sec. 7.4.1"),
    dict(id="lqr_margin", topic="lqr", exam="",
         q="How can an absolute stability margin (poles inside |z| < 1/α) be prescribed for the LQR?",
         a=r"""Design the LQR for the modified system $(\alpha G, \alpha H)$ with $\alpha > 1$ (trajectories $\hat x = \alpha^kx$). Stability of the modified closed loop implies all original poles inside the circle of radius $1/\alpha$. Requires $[\alpha G, \alpha H]$ stabilisable and $[\alpha G, Q]$ detectable. Law: $u = -\alpha^2\hat R_{s,\infty}^{-1}H^T\hat SGx$.""",
         rubric=[("Replace G, H by αG, αH", 1.0), ("Poles inside 1/α; conditions", 1.0)], src="Book Sec. 7.4.2"),
    dict(id="modal_weighting", topic="lqr", exam="",
         q="What is modal weighting in LQR design?",
         a=r"""Weight individual **eigenmodes** instead of physical states: with eigenvectors $\Sigma = [u_1 \dots u_n]$ and desired mode weights $M = \text{diag}(m_k)$, $\hat Q = \Sigma M\Sigma^{-1}$, $Q = \hat Q^T\hat Q$ ⇒ mode $u_k$ enters the cost with $m_k^2$. Used e.g. to damp a weakly damped oscillation (torsional vibrations, Book Ex. 7.4; Exercise 7.4: M = diag(20, 20, 1)).""",
         rubric=[("Q built from eigenvectors and mode weights", 1.0), ("Purpose: penalise specific (oscillating) modes", 1.0)], src="Book Sec. 7.4.3"),
    dict(id="pontryagin", topic="lqr", exam="",
         q="How is the finite-horizon LQR derived (idea)?",
         a=r"""Minimise V subject to $x(k+1) = Gx + Hu$ with a Lagrange function and multipliers $p(k)$ (Pontryagin's minimum principle) → coupled two-point boundary value problem. For linear-quadratic problems the ansatz $p(k) = S(k)x(k)$ decouples it into the **backward Riccati difference equation** $S(k) = Q + G^T[S(k+1) - S(k+1)HR_s^{-1}H^TS(k+1)]G$, $S(N+1) = L$, and the time-varying law $u(k) = -R_s^{-1}H^TS(k+1)Gx(k)$.""",
         rubric=[("Lagrange multipliers / minimum principle", 1.0), ("p = Sx ⇒ backward Riccati recursion", 1.0)], src="Book Sec. 7.1–7.2"),
    # ------------------------------------------------------------------ Ch. 8
    dict(id="fblin_idea", topic="fb_lin", exam="2016 Th.f (2 P)",
         q="Explain the basic idea / concept of exact feedback linearisation in a few sentences.",
         a=r"""Use a (generally nonlinear) **coordinate transformation** $[\xi; \eta] = \Gamma(x)$ and a nonlinear **input transformation** $u = \psi(\xi, \eta, v)$ with an artificial input $v$, such that the dynamics from $v$ to the output $y$ become **globally (exactly) linear** — a chain of delays $\xi_1(k+1) = \xi_2(k), \dots, \xi_\delta(k+1) = v(k)$. Then linear design methods (dead-beat, MFC, pole placement) apply. Unlike Taylor linearisation it is not limited to an operating point; the internal dynamics η must be stable.""",
         rubric=[("Nonlinear state + input transformation", 1.0), ("Globally linear v → y, then linear design", 1.0)], src="Book Sec. 8.1–8.2, Ex. 8.1 (tank)"),
    dict(id="rel_degree_def", topic="fb_lin", exam="2017 Th.f (2 P)",
         q="Give an interpretation of the relative degree in the context of feedback linearisation.",
         a=r"""$\delta$ is defined by $\frac{\partial}{\partial u(k)}h\circ f^j(x(k),u(k)) = 0$ for $j \le \delta - 1$ and $\neq 0$ for $j = \delta$. Since $y(k+j) = h\circ f^j(x(k), u(k))$, the input $u(k)$ affects the output **for the first time after δ steps**: δ future output samples can be predicted from the current state **without knowing future inputs**. It is the length of the linear delay chain after linearisation (linear systems: pole excess of G(z)).""",
         rubric=[("Definition with the composition operator / derivative w.r.t. u", 1.0), ("Interpretation: steps until u affects y / predictable outputs", 1.0)],
         src="Book Sec. 8.2.2; grader 2017: 'ok, but what is the rel. degree?'"),
    dict(id="composition", topic="fb_lin", exam="",
         q="Define the composition operator used in discrete-time feedback linearisation.",
         a=r"""$h\circ f(z) = h(f(z))$, recursively $h\circ f^j(z) = h\circ f^{j-1}(f(z))$, $h\circ f^0 = h$. It plays the role of the Lie derivative in continuous time and expresses future outputs: $y(k+j) = h\circ f^j(x(k), u(k))$.""",
         rubric=[("Recursive definition", 1.0), ("Analogy to Lie derivative / predicts y(k+j)", 1.0)], src="Book Sec. 8.2.1"),
]

BY_ID = {c["id"]: c for c in CARDS}


def card_points(card) -> float:
    return sum(p for _, p in card["rubric"])


EXAM_CARDS = [c for c in CARDS if c["exam"] and "Th." in c["exam"]]


# ------------------------------------------------------------------------------------------------
# "Must memorise" short answers (beginner pass plan): the questions actually asked in 2016/2017 plus
# the most likely neighbours. Each answer is short enough to learn by heart and still hits every rubric item.
SHORT = {
    "zt_def": "X(z) = Z{x(kT)} = Σ_{k=0}^{∞} x(kT)·z^{−k} (one-sided, x = 0 for k < 0, z complex). "
              "It is the Laplace transform of the impulse-sampled signal x*(t) with z = e^{Ts}.",
    "zt_unique": "x(kT): yes, unique. x(t): no — infinitely many continuous signals have the same samples. "
                 "[Sketch: sample dots + TWO different curves through them.]",
    "shannon": "A band-limited signal (highest frequency ω₁) can be reconstructed exactly from its samples if ω_s = 2π/T > 2ω₁. "
               "Reason: sampling repeats the spectrum every ω_s; if ω_s < 2ω₁ the copies overlap (aliasing) and the original cannot be recovered.",
    "zoh_quant": "Sample every T = 1/f_s, round each sample to the nearest quantisation level, hold it constant until the next sampling instant → staircase.",
    "stab_def": "Asymptotically stable: all closed-loop poles strictly inside the unit circle. Stability limit: single pole on the unit circle "
                "(z = 1, z = −1 or a simple complex pair), rest inside. Unstable: a pole outside (or a multiple pole on) the unit circle.",
    "jury_conditions": "Stable ⇔ P(1) > 0, (−1)ⁿP(−1) > 0, |a₀| < |aₙ|, |b₀| > |b_{n−1}|, … with b_k = a₀a_k − aₙa_{n−k}.",
    "rel_stab_region": "[Sketch] unit circle; inner circle |z| = e^{−σT} (minimum decay rate) and the logarithmic spiral of constant ζ; "
                       "the allowed region is inside both, shaded.",
    "disturbance_tf": "No — the disturbance is not sampled before it enters the continuous plant, so only Y(z) = (G_PZ Z)(z)/(1 + G_D G(z)) exists; "
                      "D(z) cannot be factored out.",
    "mfc_idea": "Prescribe the desired closed-loop transfer function G_W(z) (the model). Controller: P·U = F·W − Q·Y with prefilter F, "
                "feedforward 1/P, feedback Q; their coefficients follow from comparing coefficients with the desired G_W. "
                "G_W must contain the plant dead time and unstable/badly damped plant zeros; only good zeros may be cancelled.",
    "observability_def": "Observable: every initial state x(0) can be determined from the output y(0), …, y(n−1) (n samples). "
                         "Criterion: rank Q_O = rank[cᵀ; cᵀG; …; cᵀG^{n−1}] = n.",
    "controllability_def": "Controllable: any initial state can be moved to any final state within n samples by a suitable input. "
                           "Criterion: rank Q_C = rank[h, Gh, …, G^{n−1}h] = n.",
    "ctrb_vs_stab": "Controllable: every state can be steered anywhere. Stabilisable: all UNcontrollable modes are already asymptotically stable. "
                    "Not every stabilisable system is controllable — e.g. G = diag(0.5, 0.8), h = [1; 0]: mode 0.8 cannot be influenced but is stable.",
    "integral_block": "[Draw] w → (+, −y) → integrator v(k) = v(k−1) + e(k) (sum with q⁻¹ feedback) → gain K → (+, −kᵀx) → u → plant "
                      "(x(k+1) = Gx + hu, y = cᵀx) → y. Feedback paths: state vector x through kᵀ, output y to the first summing point.",
    "why_observer": "Usually not all states can be measured (sensors too expensive or impossible); the observer reconstructs them from u and the measurement.",
    "pred_vs_curr": "Predictive observer: x̂(k) uses measurements only up to m(k−1). Current observer: also uses the current measurement m(k) "
                    "to correct x̂(k) before computing u(k) (error matrix G − PC*G instead of G − PC*).",
    "lqr_prereq": "(G, H) must be stabilisable (all uncontrollable modes stable) and (G, Q) must be detectable (every unstable mode is weighted in "
                  "the cost, uᵢᵀQuᵢ > 0). Controllability/observability are not necessary.",
    "fblin_idea": "Use a nonlinear state (coordinate) transformation and a nonlinear input transformation with an artificial input v so that the "
                  "dynamics from v to y become exactly (globally) linear — a chain of delays. Then design with linear methods. "
                  "Not a local Taylor linearisation; the internal dynamics must be stable.",
    "rel_degree_def": "δ = number of steps until the input u(k) first affects the output: ∂(h∘f^j)/∂u(k) = 0 for j < δ and ≠ 0 for j = δ. "
                      "Hence δ future outputs can be predicted without knowing future inputs (linear systems: pole excess).",
    "zoh": "H₀(s) = (1 − e^{−Ts})/s: holds each sample for one period (staircase); a low-pass with phase lag ≈ dead time T/2.",
    "aliasing": "If ω_s < 2ω_max the shifted spectra overlap: a high frequency ω appears as ω − nω_s in the samples "
                "(sin ωt and sin(ω + nω_s)t give identical samples).",
}
