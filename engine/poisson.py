import numpy as np
from scipy.stats import poisson


class GoalModel:
    def __init__(self, league_avg: float = 1.35, tau: float = 0.05):
        self.league_avg = league_avg
        self.tau = tau

    def estimate_lambdas(self, team_a: str, team_b: str, factors: dict) -> tuple:
        fa = factors.get(team_a, {"attack": 1.0, "defense": 1.0})
        fb = factors.get(team_b, {"attack": 1.0, "defense": 1.0})
        lambda_a = fa["attack"] * fb["defense"] * self.league_avg
        lambda_b = fb["attack"] * fa["defense"] * self.league_avg
        return max(lambda_a, 0.01), max(lambda_b, 0.01)

    def dixon_coles_tau(self, x: int, y: int, lambda_a: float, lambda_b: float) -> float:
        if x == 0 and y == 0:
            return 1.0 - lambda_a * lambda_b * self.tau
        elif x == 0 and y == 1:
            return 1.0 + lambda_a * self.tau
        elif x == 1 and y == 0:
            return 1.0 + lambda_b * self.tau
        elif x == 1 and y == 1:
            return 1.0 - self.tau
        return 1.0

    def joint_probability(self, x: int, y: int, lambda_a: float, lambda_b: float) -> float:
        p_independent = poisson.pmf(x, lambda_a) * poisson.pmf(y, lambda_b)
        tau_factor = self.dixon_coles_tau(x, y, lambda_a, lambda_b)
        return p_independent * tau_factor

    def simulate_score(self, team_a: str, team_b: str, factors: dict, max_goals: int = 6) -> tuple:
        lambda_a, lambda_b = self.estimate_lambdas(team_a, team_b, factors)

        probs = np.zeros((max_goals + 1, max_goals + 1))
        for x in range(max_goals + 1):
            for y in range(max_goals + 1):
                probs[x, y] = self.joint_probability(x, y, lambda_a, lambda_b)
        probs /= probs.sum()

        flat = probs.flatten()
        idx = np.random.choice(len(flat), p=flat)
        x = idx // (max_goals + 1)
        y = idx % (max_goals + 1)
        return x, y

    def match_outcome_probs(self, team_a: str, team_b: str, factors: dict, max_goals: int = 6) -> dict:
        lambda_a, lambda_b = self.estimate_lambdas(team_a, team_b, factors)
        prob_a_win = 0.0
        prob_draw = 0.0
        prob_b_win = 0.0

        for x in range(max_goals + 1):
            for y in range(max_goals + 1):
                p = self.joint_probability(x, y, lambda_a, lambda_b)
                if x > y:
                    prob_a_win += p
                elif x == y:
                    prob_draw += p
                else:
                    prob_b_win += p

        total = prob_a_win + prob_draw + prob_b_win
        if total > 0:
            prob_a_win /= total
            prob_draw /= total
            prob_b_win /= total

        return {
            "home_win": round(float(prob_a_win), 4),
            "draw": round(float(prob_draw), 4),
            "away_win": round(float(prob_b_win), 4),
        }
