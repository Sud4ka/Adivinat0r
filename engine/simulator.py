import random
import numpy as np
from copy import deepcopy
from engine.predictor import BasePredictor, LogisticPredictor
from engine.stats import load_fixtures_2026, load_teams


class TournamentSimulator:
    def __init__(self, predictor: BasePredictor = None):
        self.predictor = predictor or LogisticPredictor()
        self.fixtures = load_fixtures_2026()
        self.teams = load_teams()

    def simulate_group_stage(self) -> dict:
        groups = self.fixtures["groups"]
        standings = {}

        for group_name, teams_in_group in groups.items():
            points = {t: 0 for t in teams_in_group}
            gd = {t: 0 for t in teams_in_group}
            gs = {t: 0 for t in teams_in_group}

            for i in range(len(teams_in_group)):
                for j in range(i + 1, len(teams_in_group)):
                    team_a = teams_in_group[i]
                    team_b = teams_in_group[j]
                    result = self._simulate_match(team_a, team_b, "Group Stage")
                    goals_a = result["goals_a"]
                    goals_b = result["goals_b"]

                    gs[team_a] += goals_a
                    gs[team_b] += goals_b
                    gd[team_a] += goals_a - goals_b
                    gd[team_b] += goals_b - goals_a

                    if goals_a > goals_b:
                        points[team_a] += 3
                    elif goals_a < goals_b:
                        points[team_b] += 3
                    else:
                        points[team_a] += 1
                        points[team_b] += 1

            sorted_teams = sorted(teams_in_group, key=lambda t: (points[t], gd[t], gs[t]), reverse=True)
            standings[group_name] = [(t, points[t], gs[t], gd[t]) for t in sorted_teams]

        return standings

    def _simulate_match(self, team_a: str, team_b: str, stage: str) -> dict:
        try:
            probs = self.predictor.predict_proba(team_a, team_b, stage)
        except Exception:
            return {"team_a": team_a, "team_b": team_b, "goals_a": 0, "goals_b": 0}

        a_win = probs.get(f"{team_a}_win", 0.33)
        draw = probs.get(f"{team_a}_draw", 0.33)
        b_win = probs.get(f"{team_a}_loss", 0.33)

        r = random.random()
        if r < a_win:
            outcome = 0
        elif r < a_win + draw:
            outcome = 1
        else:
            outcome = 2

        teams_data = self.teams
        avg_a = teams_data.get(team_a, {}).get("goals_for", 30) / max(1, teams_data.get(team_a, {}).get("matches_played", 10))
        avg_b = teams_data.get(team_b, {}).get("goals_for", 30) / max(1, teams_data.get(team_b, {}).get("matches_played", 10))

        if outcome == 0:
            goals_a = max(1, int(round(random.gauss(avg_a, 1.0))))
            goals_b = max(0, int(round(random.gauss(avg_b * 0.6, 0.8))))
        elif outcome == 2:
            goals_a = max(0, int(round(random.gauss(avg_a * 0.6, 0.8))))
            goals_b = max(1, int(round(random.gauss(avg_b, 1.0))))
        else:
            avg_goals = (avg_a + avg_b) / 2
            goals_a = max(0, int(round(random.gauss(avg_goals * 0.8, 0.7))))
            goals_b = max(0, int(round(random.gauss(avg_goals * 0.8, 0.7))))

        return {"team_a": team_a, "team_b": team_b, "goals_a": goals_a, "goals_b": goals_b}

    def determine_knockout_qualifiers(self, standings: dict) -> list:
        group_winners = []
        group_runners_up = []
        third_placed = []

        for group_name, sorted_teams in standings.items():
            group_winners.append((group_name, sorted_teams[0][0]))
            group_runners_up.append((group_name, sorted_teams[1][0]))
            third_placed.append((group_name, sorted_teams[2][0]))

        third_placed.sort(key=lambda x: standings[x[0]][2][1], reverse=True)
        best_third = third_placed[:8]

        qualifiers = group_winners + group_runners_up + best_third
        return qualifiers

    def simulate_knockout(self, qualifiers: list) -> dict:
        random.shuffle(qualifiers)
        teams = [t[1] for t in qualifiers]

        bracket = {
            "round_of_32": [],
            "round_of_16": [],
            "quarter_finals": [],
            "semi_finals": [],
            "final": None,
            "champion": None
        }

        round_of_32_matches = []
        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                round_of_32_matches.append((teams[i], teams[i + 1]))
        bracket["round_of_32"] = round_of_32_matches

        round_of_32_winners = self._play_round(round_of_32_matches, "Round of 16")
        bracket["round_of_16"] = round_of_32_winners

        round_of_16_winners = self._play_round(round_of_32_winners, "Round of 16")
        bracket["quarter_finals"] = round_of_16_winners

        qf_winners = self._play_round(round_of_16_winners, "Quarter-finals")
        bracket["quarter_finals"] = qf_winners

        sf_winners = self._play_round(qf_winners, "Semi-finals")
        bracket["semi_finals"] = sf_winners

        if len(sf_winners) >= 2:
            final_match = (sf_winners[0][1], sf_winners[1][1])
            final_result = self._simulate_match(sf_winners[0][1], sf_winners[1][1], "Final")
            bracket["final"] = final_result
            bracket["champion"] = sf_winners[0][1] if final_result["goals_a"] > final_result["goals_b"] else sf_winners[1][1]

            third_place = (sf_winners[0][1], sf_winners[1][1])
            bracket["third_place"] = third_place

        return bracket

    def _play_round(self, matchups: list, stage: str) -> list:
        winners = []
        for team_a, team_b in matchups:
            result = self._simulate_match(team_a, team_b, stage)
            if result["goals_a"] > result["goals_b"]:
                winners.append((team_a, team_a))
            elif result["goals_a"] < result["goals_b"]:
                winners.append((team_b, team_b))
            else:
                if random.random() < 0.5:
                    winners.append((team_a, team_a))
                else:
                    winners.append((team_b, team_b))
        return winners

    def run_full_simulation(self) -> dict:
        standings = self.simulate_group_stage()
        qualifiers = self.determine_knockout_qualifiers(standings)
        bracket = self.simulate_knockout(qualifiers)
        return {
            "standings": standings,
            "qualifiers": qualifiers,
            "bracket": bracket
        }
