"""Tests for QuantumGames-Lab: classical PD, EWL, penny flip, gates."""
import math

import pytest

import main as m

HALF = math.pi / 2


# ---- classical Prisoner's Dilemma
def test_payoff_ordering():
    assert m.T_PAY > m.R_PAY > m.P_PAY > m.S_PAY


def test_best_response_is_always_defect():
    for player in (0, 1):
        for opp in ("C", "D"):
            assert m.best_responses(m.CLASSICAL_PD, player, opp) == ["D"]


def test_unique_nash_dd():
    assert m.nash_equilibria(m.CLASSICAL_PD) == [("D", "D")]
    assert m.CLASSICAL_PD[("D", "D")] == (1, 1)


def test_pareto_cc_dominates_but_not_equilibrium():
    assert m.CLASSICAL_PD[("C", "C")] == (3, 3)
    assert m.pareto_dominates(m.CLASSICAL_PD, ("C", "C"), ("D", "D"))
    assert ("C", "C") not in m.nash_equilibria(m.CLASSICAL_PD)


# ---- quantum machinery
def test_entangler_unitary_and_identity_at_zero():
    for gamma in (0.0, 0.3, 0.9, HALF):
        assert m.is_unitary(m.entangler(gamma))
    j0 = m.entangler(0.0)
    assert all(abs(j0[i][j] - (1.0 if i == j else 0.0)) < 1e-12
               for i in range(4) for j in range(4))


def test_strategy_unitary_on_grid():
    for i in range(7):
        for j in range(5):
            assert m.is_unitary(m.strategy(math.pi * i / 6, HALF * j / 4))


def test_probabilities_normalised():
    for gamma in (0.0, 0.5, 1.0, HALF):
        probs = m.ewl_probabilities(gamma, m.strategy(0.7, 0.4),
                                    m.strategy(1.9, 1.1))
        assert abs(sum(probs) - 1.0) < 1e-9


# ---- gamma = 0 recovers the classical game
def test_gamma0_classical_table():
    table = m.named_table(0.0)
    for profile, expected in {"CC": (3, 3), "CD": (0, 5),
                              "DC": (5, 0), "DD": (1, 1)}.items():
        assert table[profile] == pytest.approx(expected, abs=1e-9)


def test_gamma0_q_degenerates_to_c():
    table = m.named_table(0.0)
    for b in "CDQ":
        assert table["Q" + b][0] == pytest.approx(table["C" + b][0],
                                                  abs=1e-9)


def test_gamma0_unique_equilibrium_dd():
    assert m.named_equilibria(0.0) == ["DD"]


def test_gamma0_no_unitary_beats_dd():
    br = m.grid_best_response(0.0, m.STRATEGY_D, player=0)
    assert br["best_payoff"] == pytest.approx(1.0, abs=1e-9)


def test_gamma0_q_is_exploitable():
    br = m.grid_best_response(0.0, m.STRATEGY_Q, player=0)
    assert br["best_payoff"] == pytest.approx(5.0, abs=1e-9)


# ---- payoffs frozen, stability moves
def test_qq_and_dd_payoffs_constant_in_gamma():
    for row in m.gamma_scan(steps=12):
        assert row["qq_payoff"] == [3.0, 3.0]
        assert row["dd_payoff"] == [1.0, 1.0]


def test_phase_regimes():
    assert m.named_equilibria(0.30) == ["DD"]
    assert m.named_equilibria(0.55) == ["DQ", "QD"]
    assert m.named_equilibria(1.20) == ["QQ"]


def test_transitions_match_analytic():
    transitions = m.transition_gammas()
    assert transitions["measured"]["dd_loses"] == pytest.approx(
        math.asin(1 / math.sqrt(5)), abs=0.01)
    assert transitions["measured"]["qq_gains"] == pytest.approx(
        math.asin(math.sqrt(2 / 5)), abs=0.01)


# ---- full entanglement
def test_max_gamma_table():
    table = m.named_table(HALF)
    for profile, expected in {"QQ": (3, 3), "CQ": (1, 1), "QC": (1, 1),
                              "DQ": (0, 5), "QD": (5, 0)}.items():
        assert table[profile] == pytest.approx(expected, abs=1e-9)


def test_max_gamma_unique_equilibrium_qq():
    assert m.named_equilibria(HALF) == ["QQ"]


def test_max_gamma_qq_grid_verified_nash():
    for player in (0, 1):
        br = m.grid_best_response(HALF, m.STRATEGY_Q, player=player)
        assert br["best_payoff"] == pytest.approx(3.0, abs=1e-9)


def test_max_gamma_dd_destroyed():
    br = m.grid_best_response(HALF, m.STRATEGY_D, player=0)
    assert br["best_payoff"] == pytest.approx(5.0, abs=1e-9)
    assert "DD" not in m.named_equilibria(HALF)


# ---- Meyer's penny flip
def test_penny_classical_fair_mix_is_a_draw():
    report = m.penny_classical_report()
    assert all(v == 0.5 for v in report["win_prob_vs_fair_mix"].values())
    assert report["best_vs_fair_mix"] == 0.5


def test_penny_classical_pure_opponent_exploitable():
    report = m.penny_classical_report()
    assert report["best_vs_never_flip"] == 1.0
    assert report["best_vs_always_flip"] == 1.0


def test_penny_quantum_always_wins():
    assert m.penny_quantum_win_prob(False) == pytest.approx(1.0, abs=1e-12)
    assert m.penny_quantum_win_prob(True) == pytest.approx(1.0, abs=1e-12)
    assert m.penny_report()["quantum_vs_fair_mix"] == pytest.approx(
        1.0, abs=1e-12)


# ---- classifier
def test_classifier_scenarios():
    assert m.classify_game(0.0, 5) == "classical-dominant"
    assert m.classify_game(0.55, 5) == "entanglement-assisted"
    assert m.classify_game(HALF, 5) == "quantum-equilibrium"


def test_classifier_matches_regime_model():
    for gamma, t in ((0.0, 5), (0.55, 5), (HALF, 5), (HALF, 4), (0.0, 6)):
        assert m.classify_game(gamma, t) == m.regime_label(
            gamma, m.pd_matrix(t=t))


def test_dilemma_strength():
    assert m.dilemma_strength() == pytest.approx(0.5)


# ---- gates + seats
def test_hold_gates_14_all_hold():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_specific_gates():
    assert m.gate("real_money_gambling") == "HOLD"
    assert m.gate("referee_fairness_overclaim") == "HOLD"
    assert m.gate("quantum_advantage_overclaim") == "HOLD"
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    brains = m.brains_report()
    assert brains["decider"]["can_override_hold"] is False
    assert brains["decider"]["seat"] == "Gemini Argon 4 Extended Thinking"
    assert brains["advisor"]["can_override_hold"] is False
    assert brains["flow"]["rendered"] is False
    assert brains["flow"]["live"] == 0


def test_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks)
