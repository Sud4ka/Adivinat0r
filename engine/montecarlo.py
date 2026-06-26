import random
import numpy as np
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from engine.stats import load_fixtures_2026, load_teams, compute_attack_defense_factors

NUM_WORKERS = min(8, os.cpu_count() or 4)


class MonteCarloSimulator:
    def __init__(self, predictor=None, num_simulations: int = 10000):
        self.predictor = predictor
        self.fixtures = load_fixtures_2026()
        self.teams = load_teams()
        self.num_simulations = num_simulations
        self.results = None
        self._factors = compute_attack_defense_factors()
        self._probs_lookup = {}

    def _precompute_probs(self):
        if self._probs_lookup:
            return
        teams = []
        for g in self.fixtures["groups"].values():
            teams.extend(g)
        teams = list(set(teams))
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                a, b = teams[i], teams[j]
                try:
                    r = self.predictor.predict_proba(a, b, "Group Stage")
                    self._probs_lookup[(a, b)] = (
                        r.get(f"{a}_win", 0.33),
                        r.get(f"{a}_draw", 0.33),
                    )
                    self._probs_lookup[(b, a)] = (
                        r.get(f"{a}_loss", 0.33),
                        r.get(f"{a}_draw", 0.33),
                    )
                except Exception:
                    self._probs_lookup[(a, b)] = (0.33, 0.33)
                    self._probs_lookup[(b, a)] = (0.33, 0.33)

    def run(self):
        if self.predictor is not None:
            self._precompute_probs()

        if self.num_simulations <= 100 or self.predictor is None:
            return self._run_sequential()

        chunk_size = max(100, self.num_simulations // NUM_WORKERS)
        chunks = []
        remaining = self.num_simulations
        while remaining > 0:
            n = min(chunk_size, remaining)
            chunks.append(n)
            remaining -= n

        from threading import Lock
        results_lock = Lock()
        aggregated = defaultdict(lambda: defaultdict(int))

        def _sim_chunk(n_sims, seed_offset):
            local_cache = {}
            local_counts = defaultdict(lambda: defaultdict(int))
            rng = random.Random(seed_offset)

            for _ in range(n_sims):
                standings = self._simulate_group_stage(local_cache, rng)
                qualifiers = self._get_qualifiers(standings)
                champion = self._simulate_knockout(qualifiers, local_cache, rng)

                for group_name, sorted_teams in standings.items():
                    for rank, (team, _, _, _) in enumerate(sorted_teams):
                        if rank == 0:
                            local_counts[team]["group_winner"] += 1
                        elif rank == 1:
                            local_counts[team]["group_runner"] += 1

                for _, team_name in qualifiers:
                    local_counts[team_name]["round_of_32"] += 1

                local_counts[champion]["champion"] += 1

            return dict(local_counts)

        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = []
            for i, n in enumerate(chunks):
                futures.append(executor.submit(_sim_chunk, n, i * 10000))

            for future in as_completed(futures):
                chunk_counts = future.result()
                with results_lock:
                    for team, data in chunk_counts.items():
                        for k, v in data.items():
                            aggregated[team][k] += v

        self.results = {}
        for team, data in aggregated.items():
            self.results[team] = {
                "champion_pct": (data["champion"] / self.num_simulations) * 100,
                "group_winner_pct": (data.get("group_winner", 0) / self.num_simulations) * 100,
                "group_runner_pct": (data.get("group_runner", 0) / self.num_simulations) * 100,
                "round_of_32_pct": (data.get("round_of_32", 0) / self.num_simulations) * 100,
            }

        return self.results

    def _run_sequential(self):
        cache = {}
        rng = random.Random(42)
        aggregated = defaultdict(lambda: defaultdict(int))

        for _ in range(self.num_simulations):
            standings = self._simulate_group_stage(cache, rng)
            qualifiers = self._get_qualifiers(standings)
            champion = self._simulate_knockout(qualifiers, cache, rng)

            for group_name, sorted_teams in standings.items():
                for rank, (team, _, _, _) in enumerate(sorted_teams):
                    if rank == 0:
                        aggregated[team]["group_winner"] += 1
                    elif rank == 1:
                        aggregated[team]["group_runner"] += 1

            for _, team_name in qualifiers:
                aggregated[team_name]["round_of_32"] += 1

            aggregated[champion]["champion"] += 1

        self.results = {}
        for team, data in aggregated.items():
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

    def _get_probs(self, team_a, team_b, cache):
        if self._probs_lookup:
            pair = (team_a, team_b)
            if pair in self._probs_lookup:
                return self._probs_lookup[pair]
        key = (team_a, team_b)
        if key in cache:
            return cache[key]
        try:
            if self.predictor:
                r = self.predictor.predict_proba(team_a, team_b, "Group Stage")
                a = r.get(f"{team_a}_win", 0.33)
                d = r.get(f"{team_a}_draw", 0.33)
            else:
                a, d = 0.33, 0.33
        except Exception:
            a, d = 0.33, 0.33
        cache[key] = (a, d)
        return a, d

    def _simulate_group_stage(self, cache, rng):
        groups = self.fixtures["groups"]
        standings = {}
        for group_name, teams_in_group in groups.items():
            points = {t: 0 for t in teams_in_group}
            gd = {t: 0 for t in teams_in_group}
            gs = {t: 0 for t in teams_in_group}
            for i in range(len(teams_in_group)):
                for j in range(i + 1, len(teams_in_group)):
                    ta, tb = teams_in_group[i], teams_in_group[j]
                    ga, gb = self._pick_score(ta, tb, cache, rng)
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

    def _pick_score(self, team_a, team_b, cache, rng):
        a_win, draw = self._get_probs(team_a, team_b, cache)
        r = rng.random()
        if r < a_win:
            outcome = 0
        elif r < a_win + draw:
            outcome = 1
        else:
            outcome = 2

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

    def _simulate_knockout(self, qualifiers, cache, rng):
        teams = [t[1] for t in qualifiers]
        rng.shuffle(teams)
        while len(teams) > 1:
            next_round = []
            for i in range(0, len(teams) - 1, 2):
                if i + 1 >= len(teams):
                    next_round.append((teams[i], teams[i]))
                    continue
                ga, gb = self._pick_score(teams[i], teams[i + 1], cache, rng)
                if ga > gb:
                    next_round.append((teams[i], teams[i]))
                elif gb > ga:
                    next_round.append((teams[i + 1], teams[i + 1]))
                else:
                    if rng.random() < 0.5:
                        next_round.append((teams[i], teams[i]))
                    else:
                        next_round.append((teams[i + 1], teams[i + 1]))
            teams = [t[1] for t in next_round]
        return teams[0] if teams else "Unknown"
