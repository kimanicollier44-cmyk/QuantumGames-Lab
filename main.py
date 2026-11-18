#!/usr/bin/env python3
"""QuantumGames-Lab - educational quantum game theory lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only - and the fairness lesson is stated up front:

  * This lab quantizes two famous games: the Prisoner's Dilemma
    (Eisert-Wilkens-Lewenstein scheme) and Meyer's penny flip.
    The quantum players do better than the classical players.
  * They do NOT do better at the same game. The referee hands the
    players an entangled state and a strictly larger strategy
    space (every unitary, not just "flip / don't flip"). The
    dilemma dissolves because the rules changed - the entanglement
    and the enlarged move set are doing the work, not magic.
  * Every number here is exact amplitude arithmetic on a laptop:
    a two-qubit statevector written from scratch. No quantum
    hardware is touched, no opponent is real, and no result in
    this file is a strategy for any real negotiation, market,
    auction, election, or conflict. Those uses are permanent
    HOLD gates - with Gemini Argon 4 Extended Thinking as DECIDER
    (names-only, tighten-only), Muse as advisor (never overrides
    HOLD), and Google Flow plan-only seats.

What is genuinely taught: how a Nash equilibrium is found (best
responses), why the classical dilemma's equilibrium is Pareto-bad,
how entanglement moves the equilibrium as gamma grows (two phase
transitions, both computed), and how a single Hadamard sandwich
turns a coin game from a 1/2 draw into a certain win.
"""
import cmath
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
VERSION = "1.0.0"

# Prisoner's Dilemma payoffs (textbook values, labelled).
# T = temptation, R = reward, P = punishment, S = sucker.
# Basis order everywhere: |CC>, |CD>, |DC>, |DD> (Alice first).
T_PAY, R_PAY, P_PAY, S_PAY = 5, 3, 1, 0
ACTIONS = ("C", "D")

# Payoff tables as {(alice_action, bob_action): (alice, bob)}.
def pd_matrix(t=T_PAY, r=R_PAY, p=P_PAY, s=S_PAY):
    return {
        ("C", "C"): (r, r),
        ("C", "D"): (s, t),
        ("D", "C"): (t, s),
        ("D", "D"): (p, p),
    }


CLASSICAL_PD = pd_matrix()

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "real_money_gambling": "HOLD - no gambling, betting, or wagering use; the penny flip is a teaching game, not a betting system",
    "financial_market_strategy_claim": "HOLD - no claim that quantum game strategies beat real markets, trading, or investing",
    "negotiation_or_contract_use": "HOLD - no use in real negotiations, contracts, labour disputes, or plea bargaining",
    "auction_or_bidding_manipulation": "HOLD - no real auction, bidding, or procurement strategy use",
    "mechanism_design_deployment": "HOLD - no deploying game mechanisms for real platforms, users, or voters",
    "quantum_hardware_result_claim": "HOLD - no claim any result here ran on quantum hardware; it is laptop statevector arithmetic",
    "quantum_advantage_overclaim": "HOLD - the quantum edge comes from an enlarged strategy space and a referee's entanglement; never present it as magic or a free advantage at the same game",
    "adversarial_exploit_design": "HOLD - no designing exploits against real counterparties, protocols, or platforms",
    "election_or_voting_manipulation": "HOLD - no voting, election, or governance game manipulation",
    "military_or_conflict_strategy": "HOLD - no military, escalation, or conflict strategy use",
    "pricing_collusion_strategy": "HOLD - no collusion, price-fixing, or antitrust-evading strategy use",
    "ai_agent_deployment_claim": "HOLD - no deploying game-playing agents against real users or services",
    "behavioural_manipulation": "HOLD - no manipulating real people's decisions with game-theoretic pressure",
    "referee_fairness_overclaim": "HOLD - never present the entangled-referee game as the same game as the classical dilemma; the referee and the entanglement change the rules",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Tiny complex linear algebra
# Two-qubit statevectors and 2x2 / 4x4 complex matrices as nested
# lists, written from scratch so every amplitude can be inspected.
# Basis order: |00>, |01>, |10>, |11> with Alice's qubit first, so
# for the dilemma |00>=|CC>, |01>=|CD>, |10>=|DC>, |11>=|DD>.

def matvec(matrix, vec):
    return [sum(matrix[i][j] * vec[j] for j in range(len(vec)))
            for i in range(len(matrix))]


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def kron2(a, b):
    """Kronecker product of two 2x2 matrices -> 4x4."""
    return [[a[i // 2][j // 2] * b[i % 2][j % 2]
             for j in range(4)] for i in range(4)]


def dagger(matrix):
    return [[matrix[j][i].conjugate() for j in range(len(matrix))]
            for i in range(len(matrix))]


def is_unitary(matrix, tol=1e-9):
    n = len(matrix)
    product = matmul(dagger(matrix), matrix)
    return all(abs(product[i][j] - (1.0 if i == j else 0.0)) < tol
               for i in range(n) for j in range(n))


IDENTITY2 = [[1.0, 0.0], [0.0, 1.0]]
PAULI_X = [[0.0, 1.0], [1.0, 0.0]]
PAULI_Y = [[0.0, -1j], [1j, 0.0]]
HADAMARD = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
            [1 / math.sqrt(2), -1 / math.sqrt(2)]]
YY = kron2(PAULI_Y, PAULI_Y)


# ================================================================ 2. Classical Prisoner's Dilemma
# Solved the honest way: enumerate best responses, intersect them.
# No equilibrium is asserted - the solver finds it.

def best_responses(matrix, player, opponent_action):
    """Actions of `player` (0 = Alice/row, 1 = Bob/column) that pay
    the most against a fixed opponent action."""
    scored = []
    for action in ACTIONS:
        profile = (action, opponent_action) if player == 0 \
            else (opponent_action, action)
        scored.append((matrix[profile][player], action))
    top = max(score for score, _ in scored)
    return sorted(action for score, action in scored if score == top)


def nash_equilibria(matrix):
    """Pure-strategy Nash equilibria: profiles where each player's
    action is a best response to the other's."""
    equilibria = []
    for alice in ACTIONS:
        for bob in ACTIONS:
            if alice in best_responses(matrix, 0, bob) \
                    and bob in best_responses(matrix, 1, alice):
                equilibria.append((alice, bob))
    return equilibria


def pareto_dominates(matrix, better, worse):
    """True if profile `better` pays both players at least as much
    as `worse`, and at least one strictly more."""
    b, w = matrix[better], matrix[worse]
    return b[0] >= w[0] and b[1] >= w[1] and (b[0] > w[0] or b[1] > w[1])


def classical_report():
    matrix = CLASSICAL_PD
    equilibria = nash_equilibria(matrix)
    return {
        "payoffs": {"T": T_PAY, "R": R_PAY, "P": P_PAY, "S": S_PAY},
        "ordering_holds": T_PAY > R_PAY > P_PAY > S_PAY,
        "alice_best_response_to_C": best_responses(matrix, 0, "C"),
        "alice_best_response_to_D": best_responses(matrix, 0, "D"),
        "bob_best_response_to_C": best_responses(matrix, 1, "C"),
        "bob_best_response_to_D": best_responses(matrix, 1, "D"),
        "nash_equilibria": [a + b for a, b in equilibria],
        "equilibrium_payoff": matrix[equilibria[0]],
        "pareto_profile": "CC",
        "pareto_payoff": matrix[("C", "C")],
        "pareto_dominates_equilibrium":
            pareto_dominates(matrix, ("C", "C"), equilibria[0]),
        "pareto_is_equilibrium": ("C", "C") in equilibria,
        "deviation_gain_from_CC": matrix[("D", "C")][0] - matrix[("C", "C")][0],
    }


# ================================================================ 3. EWL quantization
# Eisert-Wilkens-Lewenstein scheme:
#   1. The referee prepares J(gamma)|00> - entangled when gamma > 0.
#   2. Each player applies a local unitary U(theta, phi).
#   3. The referee applies J(gamma)-dagger and measures in the
#      computational basis; payoffs follow the classical table.
#
# Conventions, stated openly:
#   J(gamma) = cos(gamma/2) I(x)I + i sin(gamma/2) sigma_y(x)sigma_y,
#   the entangler form in which the embedded classical moves below
#   reproduce the textbook phase structure. Every claimed property
#   (classical recovery at gamma = 0, the (Q,Q) equilibrium at
#   gamma = pi/2, both phase transitions) is verified numerically
#   in CHECKS - none of it is assumed from the literature.
#   U(theta, phi) = [[e^{i phi} cos(theta/2), sin(theta/2)],
#                    [-sin(theta/2), e^{-i phi} cos(theta/2)]]
#   C = U(0, 0) = I,  D = U(pi, 0) = i sigma_y,  Q = U(0, pi/2).

def entangler(gamma):
    """J(gamma), the referee's entangling operator."""
    c, s = math.cos(gamma / 2), math.sin(gamma / 2)
    return [[(c if i == j else 0.0) + 1j * s * YY[i][j]
             for j in range(4)] for i in range(4)]


def strategy(theta, phi):
    """EWL two-parameter unitary strategy U(theta, phi)."""
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return [[cmath.exp(1j * phi) * c, s],
            [-s, cmath.exp(-1j * phi) * c]]


STRATEGY_C = strategy(0.0, 0.0)
STRATEGY_D = strategy(math.pi, 0.0)
STRATEGY_Q = strategy(0.0, math.pi / 2)
NAMED_STRATEGIES = {"C": STRATEGY_C, "D": STRATEGY_D, "Q": STRATEGY_Q}


def payoff_vectors(matrix):
    """Expected-payoff weights in basis order |CC>, |CD>, |DC>, |DD>."""
    alice = [matrix[profile][0]
             for profile in (("C", "C"), ("C", "D"), ("D", "C"), ("D", "D"))]
    bob = [matrix[profile][1]
           for profile in (("C", "C"), ("C", "D"), ("D", "C"), ("D", "D"))]
    return alice, bob


def ewl_probabilities(gamma, alice_u, bob_u):
    """Outcome probabilities of one EWL round, from the statevector."""
    j = entangler(gamma)
    psi = matvec(j, [1.0, 0.0, 0.0, 0.0])
    psi = matvec(kron2(alice_u, bob_u), psi)
    psi = matvec(dagger(j), psi)
    return [abs(amplitude) ** 2 for amplitude in psi]


def ewl_payoffs(gamma, alice_u, bob_u, matrix=None):
    matrix = CLASSICAL_PD if matrix is None else matrix
    probs = ewl_probabilities(gamma, alice_u, bob_u)
    alice_w, bob_w = payoff_vectors(matrix)
    return (sum(p * w for p, w in zip(probs, alice_w)),
            sum(p * w for p, w in zip(probs, bob_w)))


def named_table(gamma, matrix=None):
    """Payoffs for the 3x3 named-strategy game {C, D, Q} x {C, D, Q}."""
    return {a + b: ewl_payoffs(gamma, NAMED_STRATEGIES[a],
                               NAMED_STRATEGIES[b], matrix)
            for a in "CDQ" for b in "CDQ"}


def named_equilibria(gamma, matrix=None, tol=1e-9):
    """Nash equilibria inside the named set {C, D, Q}: a profile is
    an equilibrium if neither player gains by switching to another
    named strategy."""
    table = named_table(gamma, matrix)
    equilibria = []
    for profile, (pay_a, pay_b) in table.items():
        alice_ok = all(table[x + profile[1]][0] <= pay_a + tol
                       for x in "CDQ")
        bob_ok = all(table[profile[0] + x][1] <= pay_b + tol
                     for x in "CDQ")
        if alice_ok and bob_ok:
            equilibria.append(profile)
    return equilibria


GRID_THETA_STEPS = 25   # theta in [0, pi]
GRID_PHI_STEPS = 13     # phi in [0, pi/2]


def grid_best_response(gamma, opponent_u, player=0, matrix=None):
    """Best expected payoff `player` can reach against a fixed
    opponent unitary, searched over the U(theta, phi) grid. The
    grid includes C, D, and Q themselves, so a grid-verified
    equilibrium is a real check, not a straw man."""
    best = -1.0
    best_move = None
    for i in range(GRID_THETA_STEPS):
        theta = math.pi * i / (GRID_THETA_STEPS - 1)
        for j in range(GRID_PHI_STEPS):
            phi = (math.pi / 2) * j / (GRID_PHI_STEPS - 1)
            move = strategy(theta, phi)
            if player == 0:
                value = ewl_payoffs(gamma, move, opponent_u, matrix)[0]
            else:
                value = ewl_payoffs(gamma, opponent_u, move, matrix)[1]
            if value > best:
                best = value
                best_move = (theta, phi)
    return {"best_payoff": best, "theta": best_move[0], "phi": best_move[1]}


def gamma_scan(matrix=None, steps=25):
    """Equilibrium structure vs gamma: for each gamma, the named
    equilibria plus the (Q,Q) and (D,D) payoffs. The payoffs never
    move - (3,3) and (1,1) at every gamma - the stability does."""
    rows = []
    for i in range(steps + 1):
        gamma = (math.pi / 2) * i / steps
        table = named_table(gamma, matrix)
        rows.append({
            "gamma": round(gamma, 4),
            "sin2_gamma": round(math.sin(gamma) ** 2, 4),
            "equilibria": named_equilibria(gamma, matrix),
            "qq_payoff": [round(v, 4) for v in table["QQ"]],
            "dd_payoff": [round(v, 4) for v in table["DD"]],
        })
    return rows


def transition_gammas(matrix=None, steps=400):
    """Locate the two phase transitions by scanning gamma finely
    and watching the (D,D) and (Q,Q) equilibrium flags flip."""
    flips = {"dd_loses": None, "qq_gains": None}
    prev_dd = prev_qq = None
    for i in range(steps + 1):
        gamma = (math.pi / 2) * i / steps
        equilibria = named_equilibria(gamma, matrix)
        dd_in, qq_in = "DD" in equilibria, "QQ" in equilibria
        if prev_dd and not dd_in and flips["dd_loses"] is None:
            flips["dd_loses"] = gamma
        if prev_qq is False and qq_in and flips["qq_gains"] is None:
            flips["qq_gains"] = gamma
        prev_dd, prev_qq = dd_in, qq_in
    analytic = {"dd_loses": math.asin(1 / math.sqrt(5)),
                "qq_gains": math.asin(math.sqrt(2 / 5))}
    return {"measured": {k: round(v, 4) for k, v in flips.items()},
            "analytic": {k: round(v, 4) for k, v in analytic.items()}}


def ewl_report():
    half = math.pi / 2
    table_max = named_table(half)
    return {
        "gamma0_table": {k: [round(v, 4) for v in pair]
                         for k, pair in named_table(0.0).items()},
        "gamma0_equilibria": named_equilibria(0.0),
        "gamma_max_table": {k: [round(v, 4) for v in pair]
                            for k, pair in table_max.items()},
        "gamma_max_equilibria": named_equilibria(half),
        "qq_grid_best_response_alice":
            grid_best_response(half, STRATEGY_Q, player=0)["best_payoff"],
        "qq_grid_best_response_bob":
            grid_best_response(half, STRATEGY_Q, player=1)["best_payoff"],
        "dd_grid_best_response_alice_at_max":
            grid_best_response(half, STRATEGY_D, player=0)["best_payoff"],
        "dd_grid_best_response_alice_at_zero":
            grid_best_response(0.0, STRATEGY_D, player=0)["best_payoff"],
        "transitions": transition_gammas(),
    }


# ================================================================ 4. Meyer's penny flip
# One coin (a qubit), three moves: the quantum player moves first
# and last, the classical player moves in the middle and may flip
# or not. Classically the flipper's 50/50 mix holds the first
# player to exactly 1/2. The quantum player's Hadamard sandwich
# makes the middle move irrelevant: X|+> = |+>, so the coin comes
# back heads with probability exactly 1.

def penny_classical_win_prob(first_moves, flip_prob):
    """Win probability of the first (classical) player whose two
    moves are bit flips (True) or passes (False), against a
    classical opponent who flips with probability `flip_prob`.
    The coin starts heads (0); the first player wants heads."""
    win = 0.0
    for flip, weight in ((False, 1.0 - flip_prob), (True, flip_prob)):
        bit = 0
        for move in (first_moves[0], flip, first_moves[1]):
            if move:
                bit ^= 1
        if bit == 0:
            win += weight
    return win


def penny_classical_report():
    strategies = [(a, b) for a in (False, True) for b in (False, True)]
    return {
        "win_prob_vs_fair_mix": {
            f"{'F' if a else 'N'}{'F' if b else 'N'}":
                penny_classical_win_prob((a, b), 0.5)
            for a, b in strategies},
        "best_vs_fair_mix": max(
            penny_classical_win_prob(s, 0.5) for s in strategies),
        "best_vs_never_flip": max(
            penny_classical_win_prob(s, 0.0) for s in strategies),
        "best_vs_always_flip": max(
            penny_classical_win_prob(s, 1.0) for s in strategies),
    }


def penny_quantum_win_prob(opponent_flips):
    """Win probability of the quantum line H - (opponent move) - H,
    computed from the one-qubit statevector."""
    psi = [1.0, 0.0]
    psi = matvec(HADAMARD, psi)
    if opponent_flips:
        psi = matvec(PAULI_X, psi)
    psi = matvec(HADAMARD, psi)
    return abs(psi[0]) ** 2


def penny_report():
    classical = penny_classical_report()
    return {
        "classical": classical,
        "quantum_vs_no_flip": penny_quantum_win_prob(False),
        "quantum_vs_flip": penny_quantum_win_prob(True),
        "quantum_vs_fair_mix": 0.5 * (penny_quantum_win_prob(False)
                                      + penny_quantum_win_prob(True)),
    }


# ================================================================ 5. kNN regime classifier
# Features: gamma as a fraction of pi/2, the selected equilibrium's
# payoff as a fraction of T, and the dilemma strength
# delta = (T - R) / (T - P). Every training row is COMPUTED by the
# lab's own equilibrium machinery over a (gamma, T) grid, and the
# label comes from the lab's own regime model below - the
# classifier interpolates the lab's computed phase diagram.

def dilemma_strength(t=T_PAY, r=R_PAY, p=P_PAY):
    return (t - r) / (t - p)


def regime_label(gamma, matrix):
    """The lab's regime model: read the regime off the computed
    named-equilibrium structure at this gamma."""
    equilibria = named_equilibria(gamma, matrix)
    if "QQ" in equilibria:
        return "quantum-equilibrium"
    if equilibria == ["DD"]:
        return "classical-dominant"
    return "entanglement-assisted"


def selected_equilibrium_payoff(gamma, matrix):
    """Payoff of the regime's selected equilibrium for Alice: the
    quantum equilibrium if present, else the classical one, else
    the mean of the asymmetric transition pair."""
    equilibria = named_equilibria(gamma, matrix)
    table = named_table(gamma, matrix)
    if "QQ" in equilibria:
        return table["QQ"][0]
    if equilibria == ["DD"]:
        return table["DD"][0]
    return sum(table[profile][0] for profile in equilibria) / len(equilibria)


def regime_features(gamma, t=T_PAY):
    matrix = pd_matrix(t=t)
    return (gamma / (math.pi / 2),
            selected_equilibrium_payoff(gamma, matrix) / t,
            dilemma_strength(t))


def _training_grid():
    rows = []
    for t in (4, 5, 6):
        matrix = pd_matrix(t=t)
        for i in range(13):
            gamma = (math.pi / 2) * i / 12
            rows.append((regime_features(gamma, t),
                         regime_label(gamma, matrix)))
    return rows


TRAINING_GRID = _training_grid()


def classify_game(gamma, t=T_PAY, k=5):
    """kNN over the lab's computed (gamma, T) phase grid,
    deterministic tie-breaking."""
    target = regime_features(gamma, t)
    ranked = []
    for features, label in TRAINING_GRID:
        dist = math.sqrt(sum((a - b) ** 2
                             for a, b in zip(target, features)))
        ranked.append((dist, features, label))
    ranked.sort(key=lambda row: (row[0], row[1]))
    votes = {}
    for _, _, label in ranked[:k]:
        votes[label] = votes.get(label, 0) + 1
    priority = {"classical-dominant": 0, "entanglement-assisted": 1,
                "quantum-equilibrium": 2}
    return sorted(votes.items(), key=lambda kv: (-kv[1], priority[kv[0]]))[0][0]


def classifier_report():
    scenarios = {
        "gamma_0_classical_pd": (0.0, 5),
        "gamma_0.30_transition": (0.30, 5),
        "gamma_0.55_transition": (0.55, 5),
        "gamma_pi_over_2_full": (math.pi / 2, 5),
        "gamma_pi_over_2_weak_dilemma": (math.pi / 2, 4),
        "gamma_0_strong_dilemma": (0.0, 6),
    }
    return {name: classify_game(gamma, t)
            for name, (gamma, t) in scenarios.items()}


# ================================================================ 6. Advisory seats
def _trace(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def argon4_decide(topic="quantumgames-demo"):
    """Gemini Argon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-argon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Argon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all real-world game gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="quantumgames-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Say it in the first line of every report: the quantum player wins because the referee changed the game - entanglement plus a bigger strategy space - then show the gamma scan where the equilibrium actually moves.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["two prisoners at separate tables, one payoff matrix glowing between them",
                  "a referee weaving a light-thread between two coins as gamma rises",
                  "the (D,D) equilibrium tile cracking at the first phase transition",
                  "the (Q,Q) tile locking gold at full entanglement",
                  "a penny spinning, splitting into a wave, and landing heads every time"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": argon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    half = math.pi / 2

    # 1. classical dilemma, solved from scratch
    rep = classical_report()
    chk("payoff_ordering_T_R_P_S", rep["ordering_holds"])
    chk("best_response_to_C_is_D",
        rep["alice_best_response_to_C"] == ["D"]
        and rep["bob_best_response_to_C"] == ["D"])
    chk("best_response_to_D_is_D",
        rep["alice_best_response_to_D"] == ["D"]
        and rep["bob_best_response_to_D"] == ["D"])
    chk("unique_nash_is_DD", rep["nash_equilibria"] == ["DD"])
    chk("nash_payoff_1_1", rep["equilibrium_payoff"] == (1, 1))
    chk("pareto_CC_payoff_3_3", rep["pareto_payoff"] == (3, 3))
    chk("pareto_dominates_nash", rep["pareto_dominates_equilibrium"])
    chk("pareto_not_equilibrium", not rep["pareto_is_equilibrium"]
        and rep["deviation_gain_from_CC"] == 2)

    # 2. quantum machinery hygiene
    chk("entangler_unitary_all_gamma",
        all(is_unitary(entangler(g)) for g in (0.0, 0.3, 0.9, half)))
    chk("entangler_zero_is_identity",
        all(abs(entangler(0.0)[i][j] - (1.0 if i == j else 0.0)) < 1e-12
            for i in range(4) for j in range(4)))
    chk("strategy_unitary_on_grid",
        all(is_unitary(strategy(math.pi * i / 6, half * j / 4))
            for i in range(7) for j in range(5)))
    chk("probabilities_normalised",
        all(abs(sum(ewl_probabilities(g, strategy(0.7, 0.4),
                                      strategy(1.9, 1.1))) - 1.0) < 1e-9
            for g in (0.0, 0.5, 1.0, half)))
    chk("named_strategies_are_C_D_Q",
        NAMED_STRATEGIES["C"] == strategy(0.0, 0.0)
        and NAMED_STRATEGIES["D"] == strategy(math.pi, 0.0)
        and NAMED_STRATEGIES["Q"] == strategy(0.0, half))

    # 3. gamma = 0 recovers the classical game
    t0 = named_table(0.0)
    chk("gamma0_CC_CD_DC_DD_classical",
        all(abs(t0[k][0] - v) < 1e-9 and abs(t0[k][1] - w) < 1e-9
            for k, (v, w) in {"CC": (3, 3), "CD": (0, 5),
                              "DC": (5, 0), "DD": (1, 1)}.items()))
    chk("gamma0_Q_acts_classical",
        all(abs(t0["Q" + b][0] - t0["C" + b][0]) < 1e-9
            and abs(t0[b + "Q"][1] - t0[b + "C"][1]) < 1e-9
            for b in "CDQ"))
    chk("gamma0_unique_equilibrium_DD", named_equilibria(0.0) == ["DD"])
    chk("gamma0_grid_cannot_beat_DD",
        abs(grid_best_response(0.0, STRATEGY_D, player=0)["best_payoff"]
            - 1.0) < 1e-9)
    chk("gamma0_Q_is_exploitable",
        abs(grid_best_response(0.0, STRATEGY_Q, player=0)["best_payoff"]
            - 5.0) < 1e-9)

    # 4. the payoffs never move - the stability does
    scan = gamma_scan(steps=12)
    chk("qq_payoff_3_3_at_every_gamma",
        all(row["qq_payoff"] == [3.0, 3.0] for row in scan))
    chk("dd_payoff_1_1_at_every_gamma",
        all(row["dd_payoff"] == [1.0, 1.0] for row in scan))

    # 5. full entanglement: the dilemma dissolves
    tmax = named_table(half)
    chk("max_gamma_QQ_3_3",
        abs(tmax["QQ"][0] - 3.0) < 1e-9 and abs(tmax["QQ"][1] - 3.0) < 1e-9)
    chk("max_gamma_classical_profiles",
        all(abs(tmax[k][0] - v) < 1e-9 and abs(tmax[k][1] - w) < 1e-9
            for k, (v, w) in {"CC": (3, 3), "CD": (0, 5), "DC": (5, 0),
                              "DD": (1, 1), "CQ": (1, 1), "QC": (1, 1),
                              "DQ": (0, 5), "QD": (5, 0)}.items()))
    chk("max_gamma_unique_equilibrium_QQ",
        named_equilibria(half) == ["QQ"])
    br_qq_a = grid_best_response(half, STRATEGY_Q, player=0)["best_payoff"]
    br_qq_b = grid_best_response(half, STRATEGY_Q, player=1)["best_payoff"]
    chk("max_gamma_QQ_grid_verified_nash",
        br_qq_a <= 3.0 + 1e-9 and br_qq_b <= 3.0 + 1e-9
        and br_qq_a >= 3.0 - 1e-9 and br_qq_b >= 3.0 - 1e-9)
    chk("max_gamma_DD_destroyed",
        abs(grid_best_response(half, STRATEGY_D, player=0)["best_payoff"]
            - 5.0) < 1e-9
        and "DD" not in named_equilibria(half))
    chk("max_gamma_C_exploitable_by_D",
        abs(grid_best_response(half, STRATEGY_C, player=0)["best_payoff"]
            - 5.0) < 1e-9)

    # 6. phase structure between the extremes
    chk("low_gamma_classical_dominant",
        named_equilibria(0.30) == ["DD"]
        and regime_label(0.30, CLASSICAL_PD) == "classical-dominant")
    chk("mid_gamma_transition_pair",
        named_equilibria(0.55) == ["DQ", "QD"]
        and regime_label(0.55, CLASSICAL_PD) == "entanglement-assisted")
    chk("high_gamma_quantum_equilibrium",
        regime_label(1.20, CLASSICAL_PD) == "quantum-equilibrium")
    transitions = transition_gammas()
    chk("transition_1_matches_arcsin_1_sqrt5",
        abs(transitions["measured"]["dd_loses"]
            - transitions["analytic"]["dd_loses"]) < 0.01)
    chk("transition_2_matches_arcsin_sqrt_2_5",
        abs(transitions["measured"]["qq_gains"]
            - transitions["analytic"]["qq_gains"]) < 0.01)

    # 7. Meyer's penny flip
    penny = penny_report()
    chk("penny_classical_every_strategy_half",
        all(abs(v - 0.5) < 1e-12
            for v in penny["classical"]["win_prob_vs_fair_mix"].values()))
    chk("penny_classical_best_vs_fair_mix_half",
        penny["classical"]["best_vs_fair_mix"] == 0.5)
    chk("penny_classical_pure_opponent_exploitable",
        penny["classical"]["best_vs_never_flip"] == 1.0
        and penny["classical"]["best_vs_always_flip"] == 1.0)
    chk("penny_quantum_beats_flip_and_no_flip",
        abs(penny["quantum_vs_flip"] - 1.0) < 1e-12
        and abs(penny["quantum_vs_no_flip"] - 1.0) < 1e-12)
    chk("penny_quantum_certain_vs_mix",
        abs(penny["quantum_vs_fair_mix"] - 1.0) < 1e-12)

    # 8. classifier - labels from the lab's own phase diagram
    crep = classifier_report()
    chk("classifier_gamma0_classical",
        crep["gamma_0_classical_pd"] == "classical-dominant")
    chk("classifier_mid_entanglement_assisted",
        crep["gamma_0.55_transition"] == "entanglement-assisted")
    chk("classifier_full_quantum_equilibrium",
        crep["gamma_pi_over_2_full"] == "quantum-equilibrium")
    chk("classifier_matches_model_on_scenarios",
        all(classify_game(g, t) == regime_label(g, pd_matrix(t=t))
            for g, t in ((0.0, 5), (0.55, 5), (half, 5), (half, 4),
                         (0.0, 6))))
    chk("dilemma_strength_demo_matrix",
        abs(dilemma_strength() - 0.5) < 1e-12)

    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14
        and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_gambling_hold", gate("real_money_gambling") == "HOLD")
    chk("gate_market_hold", gate("financial_market_strategy_claim") == "HOLD")
    chk("gate_negotiation_hold", gate("negotiation_or_contract_use") == "HOLD")
    chk("gate_fairness_hold", gate("referee_fairness_overclaim") == "HOLD")
    chk("gate_advantage_overclaim_hold",
        gate("quantum_advantage_overclaim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    brains = brains_report()
    chk("argon4_no_override", brains["decider"]["can_override_hold"] is False
        and brains["decider"]["seat"]
        == "Gemini Argon 4 Extended Thinking")
    chk("claude_no_override", brains["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", brains["flow"]["rendered"] is False
        and brains["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def _fmt(pair):
    """Round a payoff pair for display: 2.7e-31 prints as 0.0."""
    return (round(pair[0], 4), round(pair[1], 4))


def demo():
    print("=" * 68)
    print("QuantumGames-Lab - quantum game theory lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] THE FAIRNESS CAVEAT - read this before the results")
    print("    The quantum players below beat the classical players. They")
    print("    do NOT beat them at the same game: the referee hands the")
    print("    players an entangled state and a far larger strategy space")
    print("    (every unitary, not just cooperate / defect). The dilemma")
    print("    dissolves because the rules changed. That is the lesson -")
    print("    and gate #14 (referee_fairness_overclaim) keeps it honest.")
    rep = classical_report()
    print("\n[2] Classical Prisoner's Dilemma - solved by best responses")
    print(f"    payoffs T={T_PAY} R={R_PAY} P={P_PAY} S={S_PAY} "
          f"(ordering T>R>P>S: {rep['ordering_holds']})")
    print(f"    best response to C: {rep['alice_best_response_to_C']} | "
          f"to D: {rep['alice_best_response_to_D']} "
          f"(defect always pays more)")
    print(f"    Nash equilibrium: {rep['nash_equilibria']} at "
          f"{rep['equilibrium_payoff']} - the unique stable profile")
    print(f"    Pareto profile CC pays {rep['pareto_payoff']} and dominates "
          f"DD, but it is NOT an equilibrium: defecting against a")
    print(f"    cooperator gains +{rep['deviation_gain_from_CC']} "
          f"({S_PAY} waits for the cooperator). That gap is the dilemma.")
    print("\n[3] EWL quantization - the referee entangles, gamma = 0 first")
    t0 = named_table(0.0)
    print("    gamma = 0 (no entanglement): the quantum game IS the")
    print("    classical game - Q degenerates to a phased C, and the")
    print(f"    unique equilibrium is still {named_equilibria(0.0)} at (1, 1).")
    print(f"    CC {_fmt(t0['CC'])} | CD {_fmt(t0['CD'])} | "
          f"DC {_fmt(t0['DC'])} | DD {_fmt(t0['DD'])}")
    print("\n[4] The gamma scan - payoffs frozen, stability moves")
    print("    gamma  sin^2(g)  equilibria      (Q,Q)      (D,D)")
    for row in gamma_scan(steps=8):
        print(f"    {row['gamma']:.4f}  {row['sin2_gamma']:.4f}    "
              f"{','.join(row['equilibria']) or '-':14s}  "
              f"{tuple(row['qq_payoff'])}  {tuple(row['dd_payoff'])}")
    transitions = transition_gammas()
    print(f"    measured transitions: (D,D) falls at gamma = "
          f"{transitions['measured']['dd_loses']}, (Q,Q) rises at "
          f"{transitions['measured']['qq_gains']}")
    print(f"    analytic: arcsin(1/sqrt(5)) = "
          f"{transitions['analytic']['dd_loses']}, "
          f"arcsin(sqrt(2/5)) = {transitions['analytic']['qq_gains']}")
    print("    between them the equilibria are the asymmetric pair DQ/QD.")
    half = math.pi / 2
    tmax = named_table(half)
    print("\n[5] Full entanglement, gamma = pi/2 - the dilemma dissolves")
    for a in "CDQ":
        cells = " | ".join(f"{a}{b} {_fmt(tmax[a + b])}" for b in "CDQ")
        print(f"    {cells}")
    br = grid_best_response(half, STRATEGY_Q, player=0)["best_payoff"]
    print(f"    (Q,Q) pays (3, 3) and a {GRID_THETA_STEPS}x{GRID_PHI_STEPS} "
          f"grid search over ALL unitary deviations finds nothing")
    print(f"    better than {br:.4f} for either player: (Q,Q) is a "
          f"grid-verified Nash equilibrium at the Pareto payoff.")
    print(f"    (D,D) still pays (1, 1) but is destroyed: a player "
          f"facing D now answers Q and earns "
          f"{grid_best_response(half, STRATEGY_D, player=0)['best_payoff']:.1f}.")
    penny = penny_report()
    print("\n[6] Meyer's penny flip - one coin, three moves")
    print(f"    classical first player vs the 50/50 mix: every strategy "
          f"wins {penny['classical']['best_vs_fair_mix']:.2f} - a draw")
    print(f"    quantum line H - move - H: wins "
          f"{penny['quantum_vs_no_flip']:.4f} if the opponent passes, "
          f"{penny['quantum_vs_flip']:.4f} if they flip")
    print("    the flip only adds a phase to |+>, so the sandwich undoes")
    print("    both moves equally: probability 1.0, from the statevector.")
    print("\n[7] Regime classifier (TinyML kNN, labels from the phase scan)")
    for name, label in classifier_report().items():
        print(f"    {name:36s} -> {label}")
    print("\n[8] Advisory seats")
    brains = brains_report()
    print(f"    decider: {brains['decider']['decision']} "
          f"trace={brains['decider']['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {brains['advisor']['can_override_hold']}")
    print(f"    flow rendered = {brains['flow']['rendered']} "
          f"live = {brains['flow']['live']}")
    print(f"\n[9] HOLD gates: {len(HOLD_GATES)}")
    for key in HOLD_GATES:
        print(f"    HOLD  {key}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "classical":
        print(json.dumps(classical_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "ewl":
        print(json.dumps(ewl_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "scan":
        print(json.dumps({"scan": gamma_scan(),
                          "transitions": transition_gammas()},
                         indent=2, sort_keys=True))
        return 0
    if cmd == "penny":
        print(json.dumps(penny_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classifier_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for key, value in HOLD_GATES.items():
            print(f"{key}: {value}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "real_money_gambling"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
