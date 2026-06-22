from engine.stats import load_matches


class H2HAnalyzer:
    def __init__(self):
        self.df = load_matches()

    def get_h2h(self, team_a: str, team_b: str) -> dict:
        mask = (
            ((self.df["home_team"] == team_a) & (self.df["away_team"] == team_b)) |
            ((self.df["home_team"] == team_b) & (self.df["away_team"] == team_a))
        )
        matches = self.df[mask].copy()
        if matches.empty:
            return {"matches": [], "summary": self._empty_summary(team_a, team_b)}

        matches = matches.sort_values("year", ascending=False)
        timeline = []
        a_wins = b_wins = draws = 0
        a_goals = b_goals = 0
        ko_a = ko_b = ko_d = 0
        group_a = group_b = group_d = 0

        for _, row in matches.iterrows():
            if row["home_team"] == team_a:
                ha, aa = row["home_goals"], row["away_goals"]
            else:
                ha, aa = row["away_goals"], row["home_goals"]

            a_goals += ha
            b_goals += aa

            if ha > aa:
                a_wins += 1
                if row["stage"] != "Group Stage":
                    ko_a += 1
                else:
                    group_a += 1
            elif ha < aa:
                b_wins += 1
                if row["stage"] != "Group Stage":
                    ko_b += 1
                else:
                    group_b += 1
            else:
                draws += 1
                if row["stage"] != "Group Stage":
                    ko_d += 1
                else:
                    group_d += 1

            timeline.append({
                "year": int(row["year"]),
                "stage": row["stage"],
                "team_a_score": ha,
                "team_b_score": aa,
                "winner": team_a if ha > aa else team_b if ha < aa else "Draw",
                "tournament": row.get("host", "Unknown")
            })

        total = a_wins + b_wins + draws
        return {
            "matches": timeline,
            "summary": {
                "team_a": team_a, "team_b": team_b,
                "a_wins": a_wins, "b_wins": b_wins, "draws": draws,
                "a_win_pct": round(a_wins / total * 100, 1) if total else 0,
                "b_win_pct": round(b_wins / total * 100, 1) if total else 0,
                "draw_pct": round(draws / total * 100, 1) if total else 0,
                "a_avg_goals": round(a_goals / total, 2) if total else 0,
                "b_avg_goals": round(b_goals / total, 2) if total else 0,
                "knockout": {"a_wins": ko_a, "b_wins": ko_b, "draws": ko_d},
                "group": {"a_wins": group_a, "b_wins": group_b, "draws": group_d},
                "total_matches": total
            }
        }

    def _empty_summary(self, team_a, team_b):
        return {
            "team_a": team_a, "team_b": team_b,
            "a_wins": 0, "b_wins": 0, "draws": 0,
            "a_win_pct": 0, "b_win_pct": 0, "draw_pct": 0,
            "a_avg_goals": 0, "b_avg_goals": 0,
            "knockout": {"a_wins": 0, "b_wins": 0, "draws": 0},
            "group": {"a_wins": 0, "b_wins": 0, "draws": 0},
            "total_matches": 0
        }
