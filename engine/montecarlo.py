import random
import numpy as np
from collections import defaultdict
from engine.stats import load_fixtures_2026, load_teams


class MonteCarloSimulator:
    def __init__(self, predictor=None, num_simulations: int = 10000):
        self.predictor = predictor
        self.fixtures = load_fixtures_2026()
        self.teams = load_teams()
        self.num_simulations = num_simulations
        self.results = None
        self._probs_cache = {}
        self._factors = {}

    def run(self):
        counts = defaultdict(lambda: defaultdict(int))

        for sim_idx in range(self.num_simulations):
            standings = self._simulate_group_stage()
            qualifiers = self._get_qualifiers(standings)
            champion = self._simulate_knockout(qualifiers)

            for group_name, sorted_teams in standings.items():
                for rank, (team, _, _, _) in enumerate(sorted_teams):
                    if rank == 0:
                        counts[team]["group_winner"] += 1
                    elif rank == 1:
                        counts[team]["group_runner"] += 1

            for team_name, _ in qualifiers:
                counts[team_name]["round_of_32"] += 1

            counts[champion]["champion"] += 1

        self.results = {}
        for team, data in counts.items():
            self.results[team] = {
                "champion_pct": (data["champion"] / self.num_simulations) * 100,
                "group_winner_pct": (data.get("group_winner", 0) / self.num_simulations) * 100,
                "group_runner_pct": (data.get("group_runner", 0) / self.num_simulations) * 100,
                "round_of_32_pct": (data.get("round_of_32", 0) / self.num_simulations) * 100,
            }

        return self.results

    def get_ranking(self):
        if not self.results:
            return []
        return sorted(self.results.items(), key=lambda x: x[1]["champion_pct"], reverse=True)

    def _get_probs(self, team_a, team_b):
        key = (team_a, team_b)
        if key in self._probs_cache:
            return self._probs_cache[key]
        try:
            if self.predictor:
                r = self.predictor.predict_proba(team_a, team_b, "Group Stage")
                a = r.get(f"{team_a}_win", 0.33)
                d = r.get(f"{team_a}_draw", 0.33)
            else:
                a, d = 0.33, 0.33
        except Exception:
            a, d = 0.33, 0.33
        self._probs_cache[key] = (a, d)
        return a, d

    def _simulate_group_stage(self):
        groups = self.fixtures["groups"]
        standings = {}
        for group_name, teams_in_group in groups.items():
            points = {t: 0 for t in teams_in_group}
            gd = {t: 0 for t in teams_in_group}
            gs = {t: 0 for t in teams_in_group}
            for i in range(len(teams_in_group)):
                for j in range(i + 1, len(teams_in_group)):
                    ta, tb = teams_in_group[i], teams_in_group[j]
                    ga, gb = self._pick_score(ta, tb)
                    gs[ta] += ga
                    gs[tb] += gb
                    gd[ta] += ga - gb
                    gd[tb] += gb - ga
                    if ga > gb:
                        points[ta] += 3
                    elif ga < gb:
                        points[tb] += 3
                    else:
                        points[ta] += 1
                        points[tb] += 1
            sorted_teams = sorted(teams_in_group, key=lambda t: (points[t], gd[t], gs[t]), reverse=True)
            standings[group_name] = [(t, points[t], gs[t], gd[t]) for t in sorted_teams]
        return standings

    def _pick_score(self, team_a, team_b):
        a_win, draw = self._get_probs(team_a, team_b)
        r = random.random()
        if r < a_win:
            outcome = 0
        elif r < a_win + draw:
            outcome = 1
        else:
            outcome = 2

        if not self._factors:
            from engine.stats import compute_attack_defense_factors, load_matches
            df = load_matches()
            self._factors = compute_attack_defense_factors(df)

        league_avg = 1.35
        fa = self._factors.get(team_a, {"attack": 1.0, "defense": 1.0})
        fb = self._factors.get(team_b, {"attack": 1.0, "defense": 1.0})
        lambda_a = fa["attack"] * fb["defense"] * league_avg
        lambda_b = fb["attack"] * fa["defense"] * league_avg

        if outcome == 0:
            ga = max(1, np.random.poisson(lambda_a))
            gb = max(0, np.random.poisson(lambda_b * 0.7))
        elif outcome == 2:
            ga = max(0, np.random.poisson(lambda_a * 0.7))
            gb = max(1, np.random.poisson(lambda_b))
        else:
            base = np.random.poisson((lambda_a + lambda_b) / 2)
            ga = gb = max(0, base)
        return ga, gb

    def _get_qualifiers(self, standings):
        winners = []
        runners = []
        third = []
        for gn, st in standings.items():
            winners.append((gn, st[0][0]))
            runners.append((gn, st[1][0]))
            third.append((gn, st[2][0], st[2][1]))
        third.sort(key=lambda x: x[2], reverse=True)
        best_third = third[:8]
        return winners + runners + [(t[0], t[1]) for t in best_third]

    def _simulate_knockout(self, qualifiers):
        teams = [t[1] for t in qualifiers]
        random.shuffle(teams)
        while len(teams) > 1:
            next_round = []
            for i in range(0, len(teams) - 1, 2):
                if i + 1 >= len(teams):
                    next_round.append((teams[i], teams[i]))
                    continue
                ga, gb = self._pick_score(teams[i], teams[i + 1])
                if ga > gb:
                    next_round.append((teams[i], teams[i]))
                elif gb > ga:
                    next_round.append((teams[i + 1], teams[i + 1]))
                else:
                    if random.random() < 0.5:
                        next_round.append((teams[i], teams[i]))
                    else:
                        next_round.append((teams[i + 1], teams[i + 1]))
            teams = [t[1] for t in next_round]
        return teams[0] if teams else "Unknown"
