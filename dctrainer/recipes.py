"""Mechanical, step-by-step recipes for every exam problem type — written for a zero-background student.
Each step says WHAT to do and WHY. Shown next to problems ("📋 Recipe") and in guided mode."""

RECIPES = {
    "zt_signal_exam": """**Recipe — signal → U(z) → Y(z) (Exam P1, 7 P)**
1. **List the samples.** Read u(t) at t = 0, T, 2T, … At a jump take the value *after* the jump. *Why:* the computer only sees these numbers.
2. **Write U(z)** = u(0) + u(T)z⁻¹ + u(2T)z⁻² + … *Why:* z⁻ᵏ is just a label meaning 'k samples later'.
3. **Y(z) = G(z)·U(z)** — write it as one fraction. *Why:* in the z-domain systems multiply.
4. **Final value:** compute (1 − z⁻¹)·Y(z), cancel, put z = 1. If the input stops (finite list) the answer is 0. *Why:* that is the final value theorem.
5. **Difference equation:** from G = b/(1 − a z⁻¹): Y(1 − a z⁻¹) = bU ⇒ y(k) − a·y(k−1) = b·u(k) ⇒ **y(k) = a·y(k−1) + b·u(k)**. *Why:* z⁻¹Y means y(k−1).
6. **Numbers y(0..4):** start with y(−1) = 0 and apply step 5 again and again. Write each line. *Why:* graders give points for visible steps.""",
    "zt_inverse_comp": """**Recipe — inverse z-transform, computational method (Exam 2016 P1, 6 P)**
1. Divide numerator and denominator by the highest power of z ⇒ everything in z⁻¹. Example: z(z+2)/(z−0.4)² = (1 + 2z⁻¹)/(1 − 0.8z⁻¹ + 0.16z⁻²).
2. Write X·(denominator) = (numerator)·U with U = 1 (a single pulse at k = 0).
3. Turn every z⁻ᵐ into a delay: x(k) − 0.8x(k−1) + 0.16x(k−2) = u(k) + 2u(k−1).
4. Move the past x-terms to the right (**signs flip!**): x(k) = 0.8x(k−1) − 0.16x(k−2) + u(k) + 2u(k−1).
5. u(0) = 1, all other u = 0; x(negative) = 0. Compute x(0), x(1), … one by one.""",
    "zt_pfe": """**Recipe — partial fractions for x(k) in closed form**
1. Divide by z: look at X(z)/z. *Why:* the table pair is z/(z − p) ↔ pᵏ, so we need the extra z.
2. Split X(z)/z = A/z + B/(z − 1) + C/(z − p) with the **cover-up rule**: cover a factor, put its root into the rest.
3. Multiply back by z: X = A + B·z/(z − 1) + C·z/(z − p).
4. Table: A → Aδ₀(k), z/(z−1) → 1, z/(z−p) → pᵏ. So x(k) = Aδ₀(k) + B + C·pᵏ.
5. Final value = B (if |p| < 1).""",
    "diffeq_weighting": """**Recipe — difference equation → G(z), g(k), y(k)**
1. Replace y(k−m) by z⁻ᵐY(z) and u(k−m) by z⁻ᵐU(z).
2. G(z) = Y/U = (u-side polynomial)/(y-side polynomial).
3. g(k): run the recursion with u = 1, 0, 0, 0, … (single pulse).
4. y(k): run the recursion with the given input (or convolve g with u — same result).
5. Steady state of a step response = G(1) (sum of numerator coeffs / sum of denominator coeffs).""",
    "convolution": """**Recipe — convolution sum**
y(k) = g(0)u(k) + g(1)u(k−1) + … + g(k)u(0). Write the g-list forward and the u-list backwards under it, multiply pairs, add. Repeat for each k.""",
    "fvt_ivt": """**Recipe — initial / final value**
- x(0): let z → ∞ — every z⁻¹ term disappears; keep the constant terms.
- x(∞): (1) multiply X(z) by (1 − z⁻¹); (2) cancel; (3) check every remaining pole has |p| < 1 — if not, write 'FVT not applicable'; (4) put z = 1.""",
    "zoh_plant": """**Recipe — G(z) of ZOH + plant, by hand (Exam P2a, 3 P)**
1. Write G_P(s)/s (divide the plant by s). *Why:* the hold makes the plant see steps.
2. **Partial fractions** (cover-up rule): G_P(s)/s = A/s + B/(s+a) (+ C/(s+b) …). For 1/(s²(s+a)) use the three terms 1/s², 1/s, 1/(s+a).
3. **Table** term by term: A/s → A/(1 − z⁻¹); B/(s+a) → B/(1 − e^{−aT}z⁻¹); 1/s² → T z⁻¹/(1 − z⁻¹)². Compute e^{−aT} numerically.
4. **Multiply by (1 − z⁻¹).** The A/(1 − z⁻¹) term becomes just A.
5. **Put everything over one denominator** and multiply out ⇒ (b₀ + b₁z⁻¹ + …)/(1 + a₁z⁻¹ + …).
6. Dead time e^{−dTs} ⇒ multiply by z⁻ᵈ.
7. **Check:** G(1) must equal G_P(0) (same DC gain). In MATLAB: `c2d(Gp, T, 'zoh')`.""",
    "closed_loop_P": """**Recipe — closed loop with a P-controller (Exam P2b–d, 4 P)**
1. Write G(z) = B/A (numerator B, denominator A, both in z⁻¹).
2. G_W = K·B/(A + K·B). Add the coefficient lists: A + K·B (pad with zeros).
3. **Stability:** convert A + K·B to positive powers of z, find the roots (quadratic formula, or Jury). All |root| < 1 ⇒ stable. *Give the numbers as the reason.*
4. Steady state for a step: G_W(1).
5. 'Can you write G_d(z) = Y/D?' ⇒ **No**: the disturbance enters the continuous plant without a sampler, so only Y(z) = (G G_z D)(z)/(1 + K G(z)) exists.""",
    "jury_cubic": """**Recipe — Jury test for a cubic (Exam P3a, 5 P) — pure bookkeeping**
1. Read a₀, a₁, a₂, a₃ (a₀ = constant term, a₃ = coefficient of z³).
2. **P(1)** = a₃ + a₂ + a₁ + a₀. Must be > 0.
3. **(−1)³P(−1)** = −(−a₃ + a₂ − a₁ + a₀). Must be > 0. (Write P(−1) term by term — the 2016 student lost a point here.)
4. **|a₀| < |a₃|.**
5. Row 1: a₀ a₁ a₂ a₃; Row 2: a₃ a₂ a₁ a₀. Compute **b₀ = a₀² − a₃²**, **b₁ = a₀a₁ − a₃a₂**, **b₂ = a₀a₂ − a₃a₁**.
6. **|b₀| > |b₂|.**
7. All four true ⇒ asymptotically stable; any false ⇒ not. **Write every condition with its numbers** (the 2017 student lost 2 P for skipping P(1), P(−1)).""",
    "jury_quartic": """**Recipe — Jury 4th order:** as for the cubic, then a 3rd row b₀..b₃ (b_k = a₀a_k − a₄a_{4−k}) and a 4th row c₀..c₂ (c_k = b₀b_k − b₃b_{3−k}); conditions |a₀|<|a₄|, |b₀|>|b₃|, |c₀|>|c₂| plus P(1) > 0, P(−1) > 0.""",
    "stability_factored": """**Recipe — factored polynomial (Exam P3b, 1 P):** read off the roots (z − r) ⇒ root r. If every |r| < 1: 'asymptotically stable because all poles lie inside the unit circle'. One sentence is enough.""",
    "jury_gain_range": """**Recipe — stable K range:** characteristic polynomial A(z) + K·B(z); write each Jury condition as 'number + number·K > 0'; solve each for K; the stable range is where all hold.""",
    "w_transform": """**Recipe — w-transform:** replace z by (1+w)/(1−w), multiply by (1−w)ⁿ, expand, then Hurwitz (all coefficients same sign; for 3rd order also α₂α₁ > α₃α₀).""",
    "mapping_sz": """**Recipe — desired pole in z**
1. |z| = exp(−2πζ/√(1−ζ²) · ω_d/ω_s) (if ω_s = N·ω_d then ω_d/ω_s = 1/N).
2. angle = 360°/N.
3. Re = |z|cos(angle), Im = |z|sin(angle). Calculator in DEGREE mode if the angle is in degrees.""",
    "sampling_alias": """**Recipe — Shannon:** need f_s > 2·f_signal. Alias frequency = |f − n·f_s| with n the nearest integer to f/f_s.""",
    "sampler_config": """**Recipe:** a sampler between two blocks ⇒ multiply their z-transforms; no sampler ⇒ transform the product together.""",
    "pid_discrete": """**Recipe:** d₀ = K_p(1 + T_V/T), d₁ = K_p(T/T_N − 2T_V/T − 1), d₂ = K_pT_V/T (Formelsammlung p. 7).""",
    "discretize_lead": """**Recipe — discretise K(s+a)/(s+b)**
- Backward: K_D = K(1+aT)/(1+bT), q = 1/(1+aT), p = 1/(1+bT).
- Tustin: K_D = K(2/T + a)/(2/T + b), q = (2/T − a)/(2/T + a), p = (2/T − b)/(2/T + b).
- Matched: q = e^{−aT}, p = e^{−bT}, then choose K_D so that G_D(1) = G_C(0).
In the exam: MATLAB `c2d(Gc, T, 'tustin')` / `'matched'`.""",
    "rl_pi_design": """**Recipe — root-locus PI design (MATLAB-friendly)**
1. Desired pole z₁ from ζ and N (see mapping recipe).
2. Angle of the zero: φ = 180° − angle(G(z₁)) + angle(z₁ − 1) (MATLAB: `angle(evalfr(G,z1))`).
3. Zero q_C = Re z₁ − Im z₁/tan φ.
4. Gain K_p = 1/|G(z₁)·(z₁ − q_C)/(z₁ − 1)|.""",
    "deadbeat_stable": """**Recipe — dead-beat (stable plant):** B(1) = sum of numerator coefficients; F_W = B(z)z⁻ᵈ/B(1); G_D = A(z)/(B(1) − B(z)z⁻ᵈ); u(0) = 1/B(1).""",
    "imc_first_order": """**Recipe — IMC:** G̃ = b z^{−(d+1)}/(1 − a z⁻¹); invert the part without delay: G_C* = (1 − a z⁻¹)/b · F(z); G_W = z^{−(d+1)}F(z).""",
    "mfc_degrees": """**Recipe — MFC degrees:** n_Q = n (n − 1 if the plant integrates); n_P̃ ≥ n_Q − n_B+ + d; n_Ao = n_P̃ + n − n_AW.""",
    "ss_canonical": """**Recipe — controllability canonical form:** last row of G = minus the denominator coefficients in REVERSE order (−aₙ … −a₁); h = [0 … 0 1]ᵀ; cᵀ = numerator coefficients in reverse order (bₙ … b₁).""",
    "ss_jordan": """**Recipe — Jordan form:** poles λᵢ on the diagonal, h = all ones, cᵢ = partial-fraction coefficient of G(z) at λᵢ (cover-up rule on G(z) itself).""",
    "ss_discretize": """**Recipe — exact discretisation:** MATLAB `sysd = c2d(ss(A,b,c,0),T)`. By hand for diagonal A: G = diag(e^{λT}), h_i = (e^{λT} − 1)/λ · b_i (T·b_i if λ = 0).""",
    "ss_tf": """**Recipe:** denominator = det(zI − G) = z² − (trace)z + det(G); numerator from cᵀ·adj(zI − G)·h.""",
    "ctrb_obsv": """**Recipe — controllability & observability (Exam P4a/b)**
1. Q_C = [h, Gh, G²h] — each column is G times the previous one.
2. Controllable ⇔ det(Q_C) ≠ 0 (rank n). Write the matrix and the determinant!
3. Q_O = [cᵀ; cᵀG; cᵀG²] — each row is the previous row times G. Use the MEASURED output (e.g. m = x₁ ⇒ cᵀ = [1 0 0]).
4. Observable ⇔ det(Q_O) ≠ 0.
MATLAB: `rank(ctrb(G,h))`, `rank(obsv(G,c))`.""",
    "pole_placement": """**Recipe — pole placement (2×2 by hand, larger in MATLAB)**
1. Check controllability (Q_C full rank).
2. Write G − h·kᵀ with unknowns k = [K₁ K₂].
3. det(zI − G + h kᵀ) = z² + (…)z + (…) — coefficients contain K₁, K₂.
4. Desired: (z − λ₁)(z − λ₂) = z² − (λ₁+λ₂)z + λ₁λ₂.
5. Equal coefficients ⇒ two linear equations ⇒ K₁, K₂.
6. K_w = 1/(cᵀ(I − G + hkᵀ)⁻¹h).
MATLAB: `k = acker(G,h,p)`, `Kw = 1/(c*((eye(n)-G+h*k)\\h))`.""",
    "integral_sf": """**Recipe — state feedback with integrator (Exam 2017 P4a, 5 P) — do it in MATLAB**
1. Build Ĝ = [G 0; −cᵀG 1] and ĥ = [h; −cᵀh]. *Why:* the extra state v adds up the error w − y.
2. Check rank of ctrb(Ĝ, ĥ) = n + 1.
3. k̂ = acker(Ĝ, ĥ, [all n+1 desired poles]).
4. kᵀ = first n entries; **K = −(last entry)**.
5. Control law: u(k) = −kᵀx(k) + K·v(k), v(k) = v(k−1) + w(k) − y(k).
```
n=size(G,1); Gh=[G zeros(n,1); -c*G 1]; hh=[h; -c*h];
kh=acker(Gh,hh,p); k=kh(1:n), K=-kh(end)
```""",
    "pred_observer": """**Recipe — predictive observer (Exam P4b, 4 P)**
1. Check observability with the measured signal.
2. p = acker(Gᵀ, cᵀ, observer poles)ᵀ — 'duality': the observer is pole placement on the transposed system.
3. Observer: x̂(k+1) = G x̂(k) + h u(k) + p (m(k) − cᵀx̂(k)).
4. **Say how you chose the poles:** 'faster (closer to 0) than the controller poles, e.g. 0.1 or dead-beat 0'.
MATLAB: `p = acker(G', c', [0.1 0.1 0.1])'`.""",
    "curr_observer": """**Recipe — current observer:** like the predictive one but with cᵀG instead of cᵀ: p = acker(Gᵀ, (cᵀG)ᵀ, poles)ᵀ.""",
    "minorder_observer": """**Recipe — minimum-order observer (x₁ measured, 2×2):** P = (G₂₂ − λ)/G₁₂; f₁ = G₂₂ − P·G₁₂; f₂ = f₁·P + G₂₁ − P·G₁₁; f₃ = h₂ − P·h₁; x̂₂ = η̂ + P·x₁.""",
    "observer_pole_choice": """**Recipe:** observer poles FASTER than controller poles ⇒ closer to the origin (smaller |z|), but not near −1.""",
    "lqr_scalar": """**Recipe — scalar LQR:** solve b²s² + (r(1−a²) − q b²)s − q r = 0, take s > 0; k = a·b·s/(r + b²s); closed-loop pole a − b·k.""",
    "lqr_matrix": """**Recipe — LQR in MATLAB:** `[k,S,e] = dlqr(G,H,Q,R)`; then K_w = 1/(c*((eye(n)-G+H*k)\\H)); e = closed-loop poles.""",
    "lqr_integral": """**Recipe — LQR with integrator (Exam 2016 P4):** c2d → build Ĝ, ĥ (as in the integrator recipe) → `kh = dlqr(Gh,hh,eye(n+1),R)` → k = kh(1:n), K = −kh(end). Design on the AUGMENTED system (2016 lost points there).""",
    "riccati_step": """**Recipe — one Riccati step:** R_s = R + HᵀSH (a number for one input); kᵀ = HᵀSG/R_s; S_new = Q + Gᵀ(S − S H HᵀS/R_s)G.""",
    "stab_detect": """**Recipe:** a mode is uncontrollable if its h-entry is 0 (diagonal G). Stabilisable ⇔ all uncontrollable modes have |λ| < 1. Detectable ⇔ every mode with |λ| > 1 has a positive weight in Q.""",
    "rel_degree": """**Recipe — relative degree:** compute cᵀh, cᵀGh, cᵀG²h, …; δ = position of the first non-zero one (1 if cᵀh ≠ 0).""",
    "static_error": """**Recipe:** K_p = G_D(1)·G(1); e_p = 1/(1+K_p). With an integrator in the loop e_p = 0.""",
    "sampling_time_rule": """**Recipe:** oscillatory: T₂ = 2π/ω_d with ω_d = ω_n√(1−ζ²); T ≤ 0.125·T₂. Aperiodic: T ≤ 0.125·T₁.""",
    "zt_table_quiz": """**Recipe:** use the table (Formelsammlung p. 2): e^{−akT} ↔ 1/(1 − e^{−aT}z⁻¹); kT ↔ Tz⁻¹/(1 − z⁻¹)²; cos ωkT ↔ (1 − z⁻¹cos ωT)/(1 − 2z⁻¹cos ωT + z⁻²).""",
    "f_complex": """**Recipe:** |a + jb| = √(a² + b²); angle = atan2(b, a); r·e^{jθ} = r cos θ + j r sin θ.""",
    "f_poles": """**Recipe:** roots of x² + bx + c: (−b ± √(b² − 4c))/2. Continuous stable ⇔ Re < 0; discrete stable ⇔ |root| < 1.""",
    "f_pfe": """**Recipe — cover-up rule:** for the coefficient of 1/(s − r): delete that factor from the denominator and evaluate the rest at s = r.""",
    "f_laplace": """**Recipe:** K/(τs + 1): pole −1/τ, final value K, y(t) = K(1 − e^{−t/τ}).""",
    "f_feedback": """**Recipe:** G_W = K_pG/(1 + K_pG); for G = K/(s+a): G_W = K_pK/(s + a + K_pK).""",
    "f_matrix": """**Recipe:** det = ad − bc; eigenvalues: λ² − (a+d)λ + det = 0; inverse = 1/det·[[d, −b], [−c, a]].""",
}
