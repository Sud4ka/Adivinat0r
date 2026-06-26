import numpy as np


class MomentumTracker:
    def __init__(self, df=None):
        if df is None:
            from engine.stats import load_matches
            df = load_matches()
        self.df = df

    def get_momentum(self, team: str) -> float:
        team_matches = self.df[
            ((self.df["home_team"] == team) | (self.df["away_team"] == team))
        ].copy()

        if team_matches.empty:
            return 0.0

        team_matches = team_matches.sort_values("year", ascending=False)
        recent_years = team_matches["year"].unique()[:3]

        momentum = 0.0
        total_weight = 0.0

        for i, year in enumerate(recent_years):
            weight = 3.0 - i
            year_matches = team_matches[team_matches["year"] == year]

            year_score = 0.0
            for _, row in year_matches.iterrows():
                if row["home_team"] == team:
                    gf, ga = row["home_goals"], row["away_goals"]
                else:
                    gf, ga = row["away_goals"], row["home_goals"]

                gd = gf - ga
                if gd > 0:
                    year_score += min(1.0, gd / 4.0)
                elif gd < 0:
                    year_score += max(-1.0, gd / 4.0)
                else:
                    year_score += 0.0

            avg_score = year_score / max(1, len(year_matches))
            momentum += avg_score * weight
            total_weight += weight

        momentum /= total_weight
        return max(-1.0, min(1.0, momentum))

    def get_momentum_features(self, team_a: str, team_b: str) -> np.ndarray:
        ma = self.get_momentum(team_a)
        mb = self.get_momentum(team_b)
        return np.array([ma, mb, ma - mb])
