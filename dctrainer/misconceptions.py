"""Registry of diagnosable misconceptions → explanation + remediation target.

Each entry: tag -> dict(title, why, fix, topic, gen)
`gen` is the generator used for the targeted remediation exercise (run at difficulty 1).
"""

MISCONCEPTIONS = {
    # ---- z-transform / difference equations
    "fvt_no_factor": dict(
        title="Final value theorem applied without (1 − z⁻¹)",
        why="You evaluated Y(z) (or G(1)·U(1)) at z = 1. The FVT is lim_{k→∞} y(k) = lim_{z→1} (1 − z⁻¹) Y(z). "
            "For a finite-length input U(z) is a polynomial, so (1 − z⁻¹)U(z) → 0 and the final value is 0.",
        fix="Always multiply by (1 − z⁻¹) first, cancel, then set z = 1. Check that the poles of (1 − z⁻¹)Y(z) are inside the unit circle.",
        topic="zt_basics", gen="fvt_ivt"),
    "fvt_not_applicable": dict(
        title="FVT used where it is not valid",
        why="The final value theorem only holds if (1 − z⁻¹)X(z) has all poles strictly inside the unit circle "
            "(the sequence must converge). Undamped oscillations (poles on |z| = 1 other than a single z = 1) or unstable poles make it meaningless — see Problem 2.9.",
        fix="Before using FVT, factor the denominator of (1 − z⁻¹)X(z) and check every pole magnitude.",
        topic="zt_basics", gen="fvt_ivt"),
    "diffeq_sign": dict(
        title="Sign flip when converting a pulse TF into a recursion",
        why="From Y(z)(1 + a₁z⁻¹ + a₂z⁻²) = … the recursion is y(k) = −a₁y(k−1) − a₂y(k−2) + …. "
            "The denominator coefficients change sign when moved to the right-hand side.",
        fix="Write the difference equation with all y-terms on the left first, then isolate y(k).",
        topic="diff_eq", gen="diffeq_weighting"),
    "sample_at_jump": dict(
        title="Wrong sample value at a discontinuity",
        why="At a jump the course convention is x(νT) = x(νT⁺) (value right after the jump) — Remark after Example 2.1.",
        fix="At each jump instant take the NEW level.",
        topic="zt_basics", gen="zt_signal_exam"),
    "pfe_no_divide_z": dict(
        title="Partial fractions on X(z) instead of X(z)/z",
        why="The table pair is z/(z−p) ↔ pᵏ. Therefore expand X(z)/z, then multiply back by z. "
            "Expanding X(z) directly gives terms 1/(z−p) ↔ p^{k−1}σ(k−1), i.e. shifted sequences.",
        fix="Expand X(z)/z = A/z + B/(z−1) + C/(z−p) ⇒ x(k) = Aδ₀(k) + Bσ(k) + C pᵏ.",
        topic="zt_inverse", gen="zt_pfe"),
    # ---- ZOH / closed loop
    "zoh_forgot": dict(
        title="ZOH ignored (impulse-invariant Z{G_P(s)} used)",
        why="With a zero-order hold the plant sees a staircase input. The correct pulse TF is "
            "G(z) = (1 − z⁻¹)·Z{G_P(s)/s}, not Z{G_P(s)}.",
        fix="Divide G_P(s) by s, do partial fractions, transform term-by-term with the table, multiply by (1 − z⁻¹).",
        topic="zoh_plant", gen="zoh_plant"),
    "zoh_no_factor": dict(
        title="Forgot the (1 − z⁻¹) factor of the ZOH",
        why="You computed Z{G_P(s)/s} (the step response transform) but did not multiply by (1 − z⁻¹). "
            "Your denominator still contains the integrator pole (1 − z⁻¹) that should cancel.",
        fix="G(z) = (1 − z⁻¹) Z{G_P(s)/s}: the factor (1 − e^{−Ts}) of H₀(s) becomes (1 − z⁻¹).",
        topic="zoh_plant", gen="zoh_plant"),
    "cl_sign": dict(
        title="Closed-loop denominator sign error",
        why="For negative feedback G_W = G_D G/(1 + G_D G) ⇒ characteristic polynomial A(z) + K·B(z), not A(z) − K·B(z).",
        fix="Write G_D G = K B/A, then G_W = K B/(A + K B).",
        topic="closed_loop", gen="closed_loop_P"),
    "cl_num_no_gain": dict(
        title="Controller gain missing in the closed-loop numerator",
        why="G_W = K B/(A + K B): the controller gain appears in numerator AND denominator.",
        fix="Multiply the numerator by the controller gain as well.",
        topic="closed_loop", gen="closed_loop_P"),
    # ---- mapping
    "map_wn_vs_wd": dict(
        title="ω_n used instead of ω_d (or vice versa)",
        why="z = e^{sT} with s = −ζω_n + jω_d: the magnitude is e^{−ζω_n T}, the angle is ω_d T (rad).",
        fix="Compute ω_n = ω_d/√(1−ζ²) when ω_d is given; angle uses ω_d.",
        topic="mapping", gen="mapping_sz"),
    "map_deg_rad": dict(
        title="Degrees/radians mix-up",
        why="arg z = ω_d T is in radians; convert with 180°/π only at the end.",
        fix="Keep radians inside cos/sin unless your calculator is in degree mode.",
        topic="mapping", gen="mapping_sz"),
    # ---- Jury
    "jury_forgot_sign_factor": dict(
        title="(−1)ⁿ factor dropped in the Jury condition",
        why="The condition is (−1)ⁿ P(−1) > 0. For odd n you must flip the sign of P(−1). (2016 exam: this cost points.)",
        fix="Compute P(−1) carefully term by term, then multiply by (−1)ⁿ.",
        topic="stability", gen="jury_cubic"),
    "jury_b_formula": dict(
        title="Wrong determinant pattern for b_k",
        why="Formula sheet: b_k = det[[a₀, a_{n−k}], [a_n, a_k]] = a₀a_k − a_n a_{n−k}, with rows written starting at a₀ (z⁰).",
        fix="Write row 1 as a₀ … a_n and row 2 reversed; b_k pairs column 0 with column (n−k).",
        topic="stability", gen="jury_cubic"),
    "jury_incomplete": dict(
        title="Jury verdict without all conditions",
        why="Asymptotic stability needs ALL: P(1) > 0, (−1)ⁿP(−1) > 0, |a₀| < |a_n|, |b₀| > |b_{n−1}|, … (2017 exam: P(1), P(−1) checks missing cost 2 points).",
        fix="Always list all n+1 conditions explicitly with their numeric values.",
        topic="stability", gen="jury_cubic"),
    # ---- discretisation / RL
    "disc_forward_euler": dict(
        title="Forward instead of backward difference",
        why="Backward difference: s ≈ (1 − z⁻¹)/T = (z − 1)/(Tz). Forward difference (z − 1)/T is NOT the course method and can map stable poles outside the unit circle.",
        fix="Substitute s = (z−1)/(Tz) and normalise to the form K(1 − q z⁻¹)/(1 − p z⁻¹).",
        topic="discretization", gen="discretize_lead"),
    "disc_tustin_factor": dict(
        title="Tustin factor 2/T wrong",
        why="Tustin: s = (2/T)(z − 1)/(z + 1). Using T/2 or 1/T gives wrong pole/zero locations.",
        fix="Write s = (2/T)(1 − z⁻¹)/(1 + z⁻¹) and multiply numerator and denominator by (1 + z⁻¹).",
        topic="discretization", gen="discretize_lead"),
    "rl_forgot_controller_pole": dict(
        title="Controller pole z = 1 missing in angle condition",
        why="The PI controller K(z − a)/(z − 1) adds a pole at z = 1. Its angle contribution φ_{pC} must be included in the angle condition.",
        fix="φ_{qC} = −180° + Σ φ_p (incl. z = 1) − Σ φ_q (plant zeros).",
        topic="root_locus", gen="rl_pi_design"),
    # ---- state space
    "c2d_euler": dict(
        title="Euler approximation instead of exact discretisation",
        why="G = e^{AT}, h = (∫₀ᵀ e^{Aμ}dμ) b. I + AT and Tb are only first-order approximations.",
        fix="Use eigen-decomposition G = M e^{ΛT} M⁻¹ or h = A⁻¹(G − I)b (A invertible); MATLAB: c2d(ss(A,b,c,0),T).",
        topic="ss_models", gen="ss_discretize"),
    "kw_openloop": dict(
        title="Reference gain from open-loop DC gain",
        why="K_w must make the CLOSED loop have unit gain: K_w = 1/(cᵀ[I − G + h kᵀ]⁻¹ h). Using 1/G_P(1) ignores the feedback.",
        fix="Evaluate the closed-loop transfer function at z = 1.",
        topic="pole_placement", gen="pole_placement"),
    "pp_sign": dict(
        title="Placed eigenvalues of G + h kᵀ",
        why="The control law is u = −kᵀx + K_w w, so the closed-loop matrix is G − h kᵀ.",
        fix="det(zI − G + h kᵀ) = desired polynomial.",
        topic="pole_placement", gen="pole_placement"),
    "integ_wrong_augment": dict(
        title="Wrong augmented system for integral action",
        why="With v(k) = v(k−1) + w(k) − y(k) the course uses v(k+1) = v(k) + w(k+1) − cᵀ(Gx(k) + h u(k)) ⇒ "
            "Ĝ = [[G, 0], [−cᵀG, 1]], ĥ = [h; −cᵀh]. Using −cᵀ instead of −cᵀG (and 0 instead of −cᵀh) is a different controller.",
        fix="Write the integrator update one step ahead and substitute x(k+1).",
        topic="pole_placement", gen="integral_sf"),
    "integ_K_sign": dict(
        title="Sign of K in k̂ᵀ = [kᵀ, −K]",
        why="Ackermann returns k̂ᵀ = [kᵀ, −K]; the integrator gain K is MINUS the last entry.",
        fix="u(k) = −k̂ᵀx̂ = −kᵀx(k) + K v(k).",
        topic="pole_placement", gen="integral_sf"),
    "obs_not_dual": dict(
        title="Observer gain not computed via duality",
        why="Observer poles are eig(G − p cᵀ). Pole placement for (Gᵀ, c) gives pᵀ — the transposes matter.",
        fix="p = acker(Gᵀ, c, poles)ᵀ, or compare coefficients of det(zI − G + p cᵀ).",
        topic="observers", gen="pred_observer"),
    "obs_pred_vs_curr": dict(
        title="Predictive vs current observer mixed up",
        why="Predictive: error matrix G − p cᵀ (uses m(k) to predict x̂(k+1)). Current: G − p cᵀG (uses m(k+1)).",
        fix="Check which measurement the observer uses, then pick the matching error matrix.",
        topic="observers", gen="curr_observer"),
    "lqr_wrong_root": dict(
        title="Wrong Riccati root",
        why="The algebraic Riccati equation has several solutions; the LQR uses the positive (semi)definite one.",
        fix="For scalar systems pick s > 0.",
        topic="lqr", gen="lqr_scalar"),
    "stab_rule": dict(
        title="s-plane vs z-plane stability rule mixed up",
        why="Continuous time (s): stable ⇔ all poles have negative real part. Discrete time (z): stable ⇔ all poles have magnitude < 1. "
            "A pole at z = 0.5 is stable; a pole at s = 0.5 is unstable; a pole at z = −0.5 is stable.",
        fix="First ask: is this an s- or a z-polynomial? Then apply the matching rule.",
        topic="f_poles", gen="f_poles"),
    "cover_up_sign": dict(
        title="Sign slip in the cover-up rule",
        why="For B/(s+a) you substitute s = −a into the REST of the expression; every remaining factor s becomes −a.",
        fix="Write the substitution explicitly: rest(−a) = …",
        topic="f_pfe", gen="f_pfe"),
    "pole_tau": dict(
        title="Pole vs time constant",
        why="K/(τs + 1) has its pole where τs + 1 = 0, i.e. s = −1/τ. A large time constant means a pole close to 0 (slow).",
        fix="Set the denominator to zero and solve for s.",
        topic="f_laplace", gen="f_laplace"),
}


def get(tag: str) -> dict:
    return MISCONCEPTIONS.get(tag, dict(title=tag, why="", fix="", topic=None, gen=None))
