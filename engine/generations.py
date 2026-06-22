LEGENDARY_SQUADS = {
    "Brazil 1970": {
        "team": "Brazil", "year": 1970, "goals_per_game": 3.0,
        "defensive_solidity": 0.85, "stage_reached": "Champion",
        "titles": 3, "win_rate": 0.83, "dominance_index": 0.95,
        "description": "Often considered the greatest team in history. Pelé, Jairzinho, Rivelino."
    },
    "Argentina 1986": {
        "team": "Argentina", "year": 1986, "goals_per_game": 2.2,
        "defensive_solidity": 0.78, "stage_reached": "Champion",
        "titles": 2, "win_rate": 0.75, "dominance_index": 0.88,
        "description": "Maradona's tournament. Hand of God and Goal of the Century."
    },
    "France 1998": {
        "team": "France", "year": 1998, "goals_per_game": 2.0,
        "defensive_solidity": 0.90, "stage_reached": "Champion",
        "titles": 1, "win_rate": 0.71, "dominance_index": 0.82,
        "description": "Zidane's double in the final. Home soil triumph."
    },
    "Germany 2014": {
        "team": "Germany", "year": 2014, "goals_per_game": 2.1,
        "defensive_solidity": 0.92, "stage_reached": "Champion",
        "titles": 4, "win_rate": 0.73, "dominance_index": 0.85,
        "description": "7-1 vs Brazil in semis. Gotze's extra time winner."
    },
    "Italy 2006": {
        "team": "Italy", "year": 2006, "goals_per_game": 1.7,
        "defensive_solidity": 0.95, "stage_reached": "Champion",
        "titles": 4, "win_rate": 0.67, "dominance_index": 0.80,
        "description": "Impregnable defense. Cannavaro, Buffon, Pirlo masterclass."
    },
    "Spain 2010": {
        "team": "Spain", "year": 2010, "goals_per_game": 1.6,
        "defensive_solidity": 0.93, "stage_reached": "Champion",
        "titles": 1, "win_rate": 0.63, "dominance_index": 0.78,
        "description": "Tiki-taka dominance. Iniesta's final winner."
    },
    "Netherlands 1974": {
        "team": "Netherlands", "year": 1974, "goals_per_game": 2.8,
        "defensive_solidity": 0.70, "stage_reached": "Runner-up",
        "titles": 0, "win_rate": 0.72, "dominance_index": 0.83,
        "description": "Total Football. Cruyff's iconic team. Finalists."
    },
    "Hungary 1954": {
        "team": "Hungary", "year": 1954, "goals_per_game": 3.8,
        "defensive_solidity": 0.60, "stage_reached": "Runner-up",
        "titles": 0, "win_rate": 0.80, "dominance_index": 0.86,
        "description": "Mighty Magyars. 27 match unbeaten streak. Puskas."
    },
    "France 2018": {
        "team": "France", "year": 2018, "goals_per_game": 1.8,
        "defensive_solidity": 0.88, "stage_reached": "Champion",
        "titles": 2, "win_rate": 0.71, "dominance_index": 0.84,
        "description": "Mbappe's breakout. RUTHLESS counter-attacking football."
    },
    "Argentina 2022": {
        "team": "Argentina", "year": 2022, "goals_per_game": 1.9,
        "defensive_solidity": 0.82, "stage_reached": "Champion",
        "titles": 3, "win_rate": 0.69, "dominance_index": 0.81,
        "description": "Messi's coronation. Dramatic final vs France."
    },
    "Brazil 2002": {
        "team": "Brazil", "year": 2002, "goals_per_game": 2.6,
        "defensive_solidity": 0.76, "stage_reached": "Champion",
        "titles": 5, "win_rate": 0.79, "dominance_index": 0.90,
        "description": "Ronaldo's redemption. 7 wins in 7 matches. Rivaldo, Ronaldinho."
    },
    "West Germany 1990": {
        "team": "Germany", "year": 1990, "goals_per_game": 1.7,
        "defensive_solidity": 0.91, "stage_reached": "Champion",
        "titles": 3, "win_rate": 0.67, "dominance_index": 0.79,
        "description": "Matthaus, Brehme, Klinsmann. Efficient German machine."
    }
}


class GenerationComparator:
    def __init__(self):
        self.legendary = LEGENDARY_SQUADS

    def get_squads_for_team(self, team: str) -> list:
        return [
            {**data, "id": name}
            for name, data in self.legendary.items()
            if data["team"] == team
        ]

    def get_preset_names(self) -> list:
        return sorted(self.legendary.keys())

    def compare(self, team: str, current_stats: dict, preset_id: str = None) -> dict:
        current = {
            "goals_per_game": current_stats.get("avg_goals_scored", 0),
            "defensive_solidity": 1.0 - min(1.0, current_stats.get("avg_goals_conceded", 0) / 3.0),
            "win_rate": current_stats.get("win_rate", 0),
            "matches_analyzed": current_stats.get("matches_analyzed", 0)
        }

        if preset_id and preset_id in self.legendary:
            preset = self.legendary[preset_id]
        else:
            team_squads = self.get_squads_for_team(team)
            if not team_squads:
                return {"current": current, "comparison": None, "rank": 0}
            preset = team_squads[0]

        normalized_current = self._normalize(current)
        normalized_preset = {
            "goals_per_game": preset["goals_per_game"] / 4.0,
            "defensive_solidity": preset["defensive_solidity"],
            "win_rate": preset["win_rate"],
            "dominance_index": preset["dominance_index"]
        }

        all_squads = list(self.legendary.values())
        all_squads_sorted = sorted(all_squads, key=lambda x: x["dominance_index"], reverse=True)
        rank = 1
        for sq in all_squads_sorted:
            if sq["dominance_index"] > current.get("dominance_index", 0) * 3:
                rank += 1

        return {
            "current": current,
            "preset": preset,
            "normalized_current": normalized_current,
            "normalized_preset": normalized_preset,
            "historical_rank": rank,
            "total_squads": len(self.legendary)
        }

    def _normalize(self, stats: dict) -> dict:
        return {
            "goals_per_game": min(1.0, stats.get("goals_per_game", 0) / 3.0),
            "defensive_solidity": stats.get("defensive_solidity", 0),
            "win_rate": stats.get("win_rate", 0),
            "dominance_index": (stats.get("win_rate", 0) * 0.4 +
                               min(1.0, stats.get("goals_per_game", 0) / 3.0) * 0.3 +
                               stats.get("defensive_solidity", 0) * 0.3)
        }

    def get_radar_labels(self) -> list:
        return ["Goals/Game", "Defense", "Win Rate", "Dominance"]
