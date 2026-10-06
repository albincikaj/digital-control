"""Regression: helpers reproduce numbers printed in the lecture notes, exercise book and past exams."""
import numpy as np
from pytest import approx

from dctrainer.mathutil import (acker, augment_integral, c2d_ss, current_observer_gain, dare_gain, jury_table, kw_gain,
                                predictive_observer_gain, series_zinv, w_transform, z_from_zeta_ratio, zoh_tf)
from dctrainer.problems.ch4 import _rl_design


def test_ex_2_9_computational():
    assert series_zinv([0, 10, 5], [1, -1.2, 0.2], 7) == approx([0, 10, 17, 18.4, 18.68, 18.736, 18.7472])


def test_exam2016_p1():
    assert series_zinv([1, 2], [1, -0.8, 0.16], 5) == approx([1, 2.8, 2.08, 1.216, 0.64])


def test_exam2017_p1():
    assert series_zinv([1], [1, -0.4], 5, u=[0.5, 0.5, 1, 1, 0]) == approx([0.5, 0.7, 1.28, 1.512, 0.6048])


def test_zoh_examples():
    n, d = zoh_tf([1], [1, 1, 0], 1.0)  # Ex 3.1/3.6
    assert n == approx([0, 0.3679, 0.2642], abs=1e-4) and d == approx([1, -1.3679, 0.3679], abs=1e-4)
    n, d = zoh_tf([10], [1, 3, 2], 0.1)  # Ex 4.7
    assert n == approx([0, 0.0453, 0.0410], abs=1e-4) and d == approx([1, -1.7236, 0.7408], abs=1e-4)
    n, d = zoh_tf([1, -0.25], [1, 1], 0.25)  # Exam 2017 P2a
    assert n == approx([1, -1.0553], abs=1e-4) and d == approx([1, -0.7788], abs=1e-4)
    n, d = zoh_tf([1], [1, 1, 0], 0.25, delay_samples=1)  # Exercise 3.9
    assert n == approx([0, 0, 0.0288, 0.0265], abs=1e-4)


def test_jury_exams():
    J = jury_table([1, 0.2, -0.5, 0.1])  # 2016
    assert J["rows"][1] == approx([-0.99, -0.25, 0.52]) and J["stable"] and J["Pm1"] == approx(0.2)
    assert not jury_table([2, -3, 2, -1, 1])["stable"]  # Ex 3.9
    assert jury_table([2, -3, 2, -1, 1])["rows"][2] == approx([8, -17, 11])


def test_w_transform():
    assert w_transform([1, -2, 1.08, -0.144]) == approx([4.224, 3.488, 0.352, -0.064])  # Exercise 3.8
    K = 0.3
    assert w_transform([1, -1, 0, K]) == approx([2 - K, 4 + 3 * K, 2 - 3 * K, K])  # Ex 3.12


def test_mapping_ex44():
    m, a, z = z_from_zeta_ratio(0.5, 0.1)
    assert (z.real, z.imag) == approx((0.5629, 0.4090), abs=1e-4)


def test_rl_ex44():
    num, den = np.array([0, 0.5404, 0.5404 * 0.5586]), np.array(np.poly([0.6065, 0.2865]))
    z1 = complex(0.5629, 0.4090)
    phi, *_ = _rl_design(num, den, z1)
    qc = z1.real - z1.imag / np.tan(np.radians(phi))
    assert phi == approx(88.9, abs=0.3) and qc == approx(0.555, abs=0.003)


def test_state_space_examples():
    G = np.array([[0, 1], [-0.16, -1.0]]); h = np.array([0, 1.0]); c = np.array([1, 1.0])
    k = acker(G, h, [0.5 + 0.5j, 0.5 - 0.5j])
    assert k == approx([0.34, -2]) and kw_gain(G, h, c, k) == approx(0.25)  # Ex 6.1
    assert acker(G, h, [0, 0]) == approx([-0.16, -1])  # Ex 6.2
    assert predictive_observer_gain(G, c, [0.2, 0.2]) == approx([-8, 6.6])  # Ex 6.4
    assert current_observer_gain(G, c, [0.2, 0.2]) == approx([8.75, -8])  # Ex 6.5
    Gh, hh = augment_integral([[0, 1, 0], [0, 0, 1], [-0.12, -0.01, 1]], [0, 0, 1], [0.5, 1, 0])
    assert acker(Gh, hh, [0, 0, 0, 0]) == approx([-0.12, 97 / 300, 2, -2 / 3])  # Ex 6.3
    Gh, hh = augment_integral([[1.5]], [1], [1])
    assert acker(Gh, hh, [0.5 + 0.3j, 0.5 - 0.3j]) == approx([1.16, -0.34])  # Exercise 6.9
    G3 = np.array([[0, 1, 0], [0, 0, 1], [0.4, -1.7, 2.3]])
    assert acker(G3, [0, 0, 1], [0, 0, 0]) == approx([0.4, -1.7, 2.3])  # Exercise 6.2


def test_c2d_ex56():
    G, h = c2d_ss([[0, 1], [-2, -3]], [0, 1], 1.0)
    e1, e2 = np.exp(-1), np.exp(-2)
    assert G.ravel() == approx([2 * e1 - e2, e1 - e2, -2 * e1 + 2 * e2, -e1 + 2 * e2])
    assert h.ravel() == approx([-e1 + 0.5 * e2 + 0.5, e1 - e2])


def test_lqr_examples():
    S, K = dare_gain([[1, 0.5], [0, 1]], [0.125, 0.5], np.eye(2), 1)
    assert K.ravel() == approx([0.6514, 1.3142], abs=1e-4)  # Exercise 7.5
    S, K = dare_gain([[0, 0], [-0.5, 1]], [1, 0], np.eye(2), 1)
    assert S.ravel() == approx([1.8431, -1.6861, -1.6861, 4.3723], abs=1e-4)  # Exercise 7.2
    assert K.ravel() == approx([0.2965, -0.5931], abs=1e-4)
    S, _ = dare_gain([[2, 1], [0, 1.1]], [1, 2], np.eye(2), 1)
    assert S.ravel() == approx([9.4869, 2.4710, 2.4710, 1.9741], abs=1e-4)  # Ex 7.1


def test_deadbeat_problems():
    n, d = zoh_tf([0.4], [1, 1], 0.25)  # Exercise 4.9
    assert 1 / sum(n) == approx(11.302, abs=1e-3)
    n, d = zoh_tf([2], [1, 3, 2], 0.25)  # Exercise 4.7
    B1 = sum(n)
    assert [x / B1 for x in n[1:]] == approx([0.5622, 0.4378], abs=1e-4) and 1 / B1 == approx(11.489, abs=1e-3)


def test_walkthrough_coefficient_comparison_matches_acker():
    from dctrainer.mathutil import pp2_steps, acker, predictive_observer_gain, current_observer_gain
    cases = [([[0, 1], [-0.16, -1]], [0, 1], [1, 1]), ([[1, 0.5], [0, 1]], [0.125, 0.5], [1, 0]),
             ([[0, 1], [0, -0.5]], [1, 1], [1, 1]), ([[1, 0.1813], [0, 0.8187]], [0.01873, 0.1813], [1, 0])]
    for G, h, c in cases:
        G = np.array(G, float); c = np.array(c, float)
        for poles in ([0.5 + 0.5j, 0.5 - 0.5j], [0.2, 0.2], [0, 0], [0.5, 0.3]):
            assert pp2_steps(G, h, poles)[1] == approx(acker(G, h, poles), abs=1e-8)
            if np.linalg.matrix_rank(np.vstack([c, c @ G])) == 2:
                assert pp2_steps(G.T, c, poles)[1] == approx(predictive_observer_gain(G, c, poles), abs=1e-8)
                if abs(np.linalg.det(G)) > 1e-9:
                    assert pp2_steps(G.T, c @ G, poles)[1] == approx(current_observer_gain(G, c, poles), abs=1e-8)
