import json
import os
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ELO_PATH = os.path.join(DATA_DIR, "elo_ratings.json")

INITIAL_ELO = 1500
K_WORLD_CUP = 32
K_QUALIFIER = 24
K_FRIENDLY = 16
HOME_ADVANTAGE_ELO = 100


def _is_world_cup_match(stage: str) -> bool:
    return stage in ("Group Stage", "Round of 16", "Quarter-finals", "Semi-finals", "Final", "Third place")


def _is_qualifier(stage: str) -> bool:
    return "qualif" in stage.lower() or "qualifier" in stage.lower()


def _get_k_factor(stage: str) -> int:
    if _is_world_cup_match(stage):
        return K_WORLD_CUP
    if _is_qualifier(stage):
        return K_QUALIFIER
    return K_FRIENDLY


def _expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def load_elo_ratings() -> dict:
    try:
        with open(ELO_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_elo_ratings(ratings: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ELO_PATH, "w") as f:
        json.dump(ratings, f, indent=2)


def get_elo(team: str, ratings: dict) -> float:
    return ratings.get(team, INITIAL_ELO)


def update_elo(
    ratings: dict,
    team_a: str,
    team_b: str,
    goals_a: int,
    goals_b: int,
    stage: str,
    is_neutral: bool = True,
) -> tuple:
    if team_a not in ratings:
        ratings[team_a] = INITIAL_ELO
    if team_b not in ratings:
        ratings[team_b] = INITIAL_ELO

    ra = ratings[team_a]
    rb = ratings[team_b]

    if not is_neutral:
        ra += HOME_ADVANTAGE_ELO

    ea = _expected_score(ra, rb)
    eb = 1.0 - ea

    goal_diff = abs(goals_a - goals_b)
    if goal_diff == 0:
        sa, sb = 0.5, 0.5
    elif goals_a > goals_b:
        sa, sb = 1.0, 0.0
    else:
        sa, sb = 0.0, 1.0

    goal_margin = min(goal_diff, 3)
    margin_weight = 1.0 + (goal_margin - 1) * 0.1 if goal_margin > 1 else 1.0

    k = _get_k_factor(stage)
    delta = k * margin_weight * (sa - ea)

    ratings[team_a] = round(ra + delta, 1)
    ratings[team_b] = round(rb - delta, 1)

    return ratings


def compute_all_elo() -> dict:
    ratings = {}
    import pandas as pd
    from engine.stats import load_matches
    df = load_matches()
    df_sorted = df.sort_values(["year", "stage"])

    for _, row in df_sorted.iterrows():
        if row["home_team"] not in ratings:
            ratings[row["home_team"]] = INITIAL_ELO
        if row["away_team"] not in ratings:
            ratings[row["away_team"]] = INITIAL_ELO
        stage = row["stage"]
        ratings = update_elo(
            ratings,
            row["home_team"],
            row["away_team"],
            int(row["home_goals"]),
            int(row["away_goals"]),
            stage,
            is_neutral=True,
        )

    save_elo_ratings(ratings)
    return ratings


def get_elo_features(team_a: str, team_b: str, ratings: dict) -> np.ndarray:
    elo_a = get_elo(team_a, ratings)
    elo_b = get_elo(team_b, ratings)
    elo_diff = elo_a - elo_b
    return np.array([elo_a / 2000.0, elo_b / 2000.0, elo_diff / 1000.0])


def get_team_elo_features(team_a: str, team_b: str) -> np.ndarray:
    ratings = load_elo_ratings()
    if not ratings:
        ratings = compute_all_elo()
    return get_elo_features(team_a, team_b, ratings)
