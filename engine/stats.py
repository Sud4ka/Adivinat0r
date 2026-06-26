import os
import json
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TEMPORAL_DECAY_FACTOR = 0.94

FEATURE_NAMES = [
    "h2h_a_wins_ratio", "h2h_b_wins_ratio", "h2h_draws_ratio",
    "stats_a_avg_goals_scored", "stats_a_avg_goals_conceded",
    "stats_b_avg_goals_scored", "stats_b_avg_goals_conceded",
    "stats_a_win_rate", "stats_b_win_rate",
    "stage_coeff",
    "ranking_delta",
    "home_continent_adv",
    "same_continent",
    "attack_diff", "creat_diff", "def_diff",
    "player_power_a", "player_power_b", "player_power_diff",
    "elo_a", "elo_b", "elo_diff",
    "form_gf_diff", "form_ga_diff", "form_win_rate_diff",
    "form_ppg_diff", "form_gd_norm",
    "momentum_a", "momentum_b", "momentum_diff",
    "env_score",
]


_cache_matches = None
_cache_teams = None
_cache_player_power = None
_cache_power_rankings = None
_cache_attack_defense = None


def invalidate_caches():
    global _cache_matches, _cache_teams, _cache_player_power
    global _cache_power_rankings, _cache_attack_defense
    _cache_matches = None
    _cache_teams = None
    _cache_player_power = None
    _cache_power_rankings = None
    _cache_attack_defense = None


def load_matches() -> pd.DataFrame:
    global _cache_matches
    if _cache_matches is None:
        path = os.path.join(DATA_DIR, "worldcups.csv")
        _cache_matches = pd.read_csv(path)
    return _cache_matches


def load_teams() -> dict:
    global _cache_teams
    if _cache_teams is None:
        path = os.path.join(DATA_DIR, "teams.json")
        with open(path) as f:
            _cache_teams = json.load(f)
    return _cache_teams


def load_fixtures_2026() -> dict:
    path = os.path.join(DATA_DIR, "fixtures_2026.json")
    with open(path) as f:
        return json.load(f)


def load_player_power() -> dict:
    global _cache_player_power
    if _cache_player_power is None:
        path = os.path.join(DATA_DIR, "player_power.json")
        try:
            with open(path) as f:
                _cache_player_power = json.load(f)
        except Exception:
            _cache_player_power = {}
    return _cache_player_power


def get_team_list() -> list:
    teams = load_teams()
    return sorted(teams.keys())


def compute_h2h(df: pd.DataFrame, team_a: str, team_b: str) -> dict:
    mask_a = ((df["home_team"] == team_a) & (df["away_team"] == team_b)) | \
             ((df["home_team"] == team_b) & (df["away_team"] == team_a))
    matches = df[mask_a]
    if matches.empty:
        return {"played": 0, "team_a_wins": 0, "team_b_wins": 0, "draws": 0}
    a_wins = 0
    b_wins = 0
    draws = 0
    for _, row in matches.iterrows():
        if row["home_goals"] > row["away_goals"]:
            if row["home_team"] == team_a:
                a_wins += 1
            else:
                b_wins += 1
        elif row["home_goals"] < row["away_goals"]:
            if row["home_team"] == team_a:
                b_wins += 1
            else:
                a_wins += 1
        else:
            draws += 1
    return {
        "played": len(matches),
        "team_a_wins": a_wins,
        "team_b_wins": b_wins,
        "draws": draws
    }


def compute_team_stats(df: pd.DataFrame, team: str, recent_years: int = 3) -> dict:
    team_matches = df[(df["home_team"] == team) | (df["away_team"] == team)]
    if team_matches.empty:
        return {"avg_goals_scored": 0, "avg_goals_conceded": 0, "win_rate": 0, "matches_analyzed": 0}
    total_matches = len(team_matches)
    total_goals_scored = 0
    total_goals_conceded = 0
    wins = 0
    draws = 0
    losses = 0
    years = sorted(team_matches["year"].unique(), reverse=True)
    recent_years_set = set(years[:recent_years]) if recent_years < len(years) else set(years)
    for _, row in team_matches.iterrows():
        weight = 2.0 if row["year"] in recent_years_set else 1.0
        if row["home_team"] == team:
            total_goals_scored += row["home_goals"] * weight
            total_goals_conceded += row["away_goals"] * weight
            if row["home_goals"] > row["away_goals"]:
                wins += 1 * weight
            elif row["home_goals"] == row["away_goals"]:
                draws += 1 * weight
            else:
                losses += 1 * weight
        else:
            total_goals_scored += row["away_goals"] * weight
            total_goals_conceded += row["home_goals"] * weight
            if row["away_goals"] > row["home_goals"]:
                wins += 1 * weight
            elif row["away_goals"] == row["home_goals"]:
                draws += 1 * weight
            else:
                losses += 1 * weight
    weighted_matches = wins + draws + losses
    return {
        "avg_goals_scored": total_goals_scored / weighted_matches if weighted_matches else 0,
        "avg_goals_conceded": total_goals_conceded / weighted_matches if weighted_matches else 0,
        "win_rate": wins / weighted_matches if weighted_matches else 0,
        "matches_analyzed": total_matches
    }


def compute_attack_defense_factors(df: pd.DataFrame = None) -> dict:
    global _cache_attack_defense
    if _cache_attack_defense is not None:
        return _cache_attack_defense
    if df is None:
        df = load_matches()
    all_home_goals = df["home_goals"].mean()
    all_away_goals = df["away_goals"].mean()
    teams = set(df["home_team"]).union(set(df["away_team"]))
    home_stats = df.groupby("home_team").agg(
        home_scored=("home_goals", "mean"),
        home_conceded=("away_goals", "mean"),
    )
    away_stats = df.groupby("away_team").agg(
        away_scored=("away_goals", "mean"),
        away_conceded=("home_goals", "mean"),
    )
    factors = {}
    for team in teams:
        hs = home_stats.get("home_scored", {}).get(team, all_home_goals)
        hc = home_stats.get("home_conceded", {}).get(team, all_away_goals)
        ac = away_stats.get("away_scored", {}).get(team, all_away_goals)
        acd = away_stats.get("away_conceded", {}).get(team, all_home_goals)
        factors[team] = {
            "attack": ((hs / max(all_home_goals, 0.01)) + (ac / max(all_away_goals, 0.01))) / 2,
            "defense": ((hc / max(all_away_goals, 0.01)) + (acd / max(all_home_goals, 0.01))) / 2,
        }
    _cache_attack_defense = factors
    return factors


def get_stage_coefficient(stage: str) -> float:
    stage_map = {
        "Group Stage": 0.5,
        "Round of 16": 0.7,
        "Quarter-finals": 0.85,
        "Semi-finals": 1.0,
        "Final": 1.2,
        "Third place": 0.6
    }
    return stage_map.get(stage, 0.5)


def get_continent(team: str) -> str:
    teams = load_teams()
    if team in teams:
        return teams[team].get("continent", "Europe")
    return "Europe"


def _load_power_rankings():
    global _cache_power_rankings
    if _cache_power_rankings is not None:
        return _cache_power_rankings

    try:
        from engine.worldcup_api import load_power_rankings as _lpr
        pr = _lpr()
    except Exception:
        pr = {}

    if not pr:
        _cache_power_rankings = pr
        return pr

    continent_avgs = {}
    for team, stats in pr.items():
        cont = get_continent(team)
        if cont not in continent_avgs:
            continent_avgs[cont] = {"attack": [], "creativity": [], "defense": []}
        for k in ("attack", "creativity", "defense"):
            v = stats.get(k, 0)
            if v > 0:
                continent_avgs[cont][k].append(v)

    continent_defaults = {}
    for cont, vals in continent_avgs.items():
        d = {}
        for k in ("attack", "creativity", "defense"):
            d[k] = round(sum(vals[k]) / len(vals[k]), 2) if vals[k] else 6.0
        continent_defaults[cont] = d

    for team in list(pr.keys()):
        cont = get_continent(team)
        defaults = continent_defaults.get(cont, {"attack": 6.0, "creativity": 6.0, "defense": 6.0})
        for k in ("attack", "creativity", "defense"):
            if pr[team].get(k, 0) == 0:
                pr[team][k] = max(pr[team].get(k, 0), defaults[k])

    _cache_power_rankings = pr
    return pr


_CACHED_TEAMS_FORM = {}


def set_live_teams_form(teams_form: dict):
    global _CACHED_TEAMS_FORM
    _CACHED_TEAMS_FORM = teams_form


def get_live_teams_form() -> dict:
    return _CACHED_TEAMS_FORM


def clear_live_teams_form():
    global _CACHED_TEAMS_FORM
    _CACHED_TEAMS_FORM = {}


def _get_elo_ratings():
    try:
        from engine.elo import load_elo_ratings, compute_all_elo
        ratings = load_elo_ratings()
        if not ratings:
            ratings = compute_all_elo()
        return ratings
    except Exception:
        return {}


def build_live_features(team_a: str, team_b: str) -> np.ndarray:
    from engine.live_data import build_live_feature_vector
    features = build_live_feature_vector(team_a, team_b, _CACHED_TEAMS_FORM)
    return np.array(features)


def _compute_cumulative_ranking(df: pd.DataFrame, team: str) -> int:
    """Count total wins in a filtered df (past matches only)."""
    if df.empty:
        return 0
    home_wins = ((df["home_team"] == team) & (df["home_goals"] > df["away_goals"])).sum()
    away_wins = ((df["away_team"] == team) & (df["away_goals"] > df["home_goals"])).sum()
    return int(home_wins + away_wins)


def build_feature_vector(
    df: pd.DataFrame, team_a: str, team_b: str, stage: str,
    host: str = None, cumulative_elo: dict = None
) -> np.ndarray:
    h2h = compute_h2h(df, team_a, team_b)
    stats_a = compute_team_stats(df, team_a)
    stats_b = compute_team_stats(df, team_b)
    stage_coeff = get_stage_coefficient(stage)
    continent_a = get_continent(team_a)
    continent_b = get_continent(team_b)

    wins_a = _compute_cumulative_ranking(df, team_a)
    wins_b = _compute_cumulative_ranking(df, team_b)
    ranking_delta = wins_a - wins_b

    home_continent_adv = 1.0 if host and continent_a == get_continent(host) else 0.0

    pr = _load_power_rankings()
    pr_a = pr.get(team_a)
    if pr_a is None:
        from engine.worldcup_api import SEED_POWER_RANKINGS
        pr_a = SEED_POWER_RANKINGS.get(team_a, {"attack": 6.0, "creativity": 6.0, "defense": 6.0})
    pr_b = pr.get(team_b)
    if pr_b is None:
        from engine.worldcup_api import SEED_POWER_RANKINGS
        pr_b = SEED_POWER_RANKINGS.get(team_b, {"attack": 6.0, "creativity": 6.0, "defense": 6.0})
    attack_a = pr_a.get("attack", 0)
    attack_b = pr_b.get("attack", 0)
    creat_a = pr_a.get("creativity", 0)
    creat_b = pr_b.get("creativity", 0)
    def_a = pr_a.get("defense", 0)
    def_b = pr_b.get("defense", 0)

    features = np.array([
        h2h["team_a_wins"] / (h2h["played"] + 1),
        h2h["team_b_wins"] / (h2h["played"] + 1),
        h2h["draws"] / (h2h["played"] + 1),
        stats_a["avg_goals_scored"],
        stats_a["avg_goals_conceded"],
        stats_b["avg_goals_scored"],
        stats_b["avg_goals_conceded"],
        stats_a["win_rate"],
        stats_b["win_rate"],
        stage_coeff,
        ranking_delta / 1000.0,
        home_continent_adv,
        1.0 if continent_a == continent_b else 0.0,
        attack_a - attack_b,
        creat_a - creat_b,
        def_a - def_b,
    ])

    pp = load_player_power()
    pp_a = float(pp.get(team_a, 0))
    pp_b = float(pp.get(team_b, 0))
    pp_max = max(pp_a, pp_b, 1.0)
    pp_features = np.array([
        pp_a / pp_max,
        pp_b / pp_max,
        (pp_a - pp_b) / pp_max,
    ])
    features = np.concatenate([features, pp_features])

    if cumulative_elo is not None:
        from engine.elo import get_elo_features
        elo_feats = get_elo_features(team_a, team_b, cumulative_elo)
    else:
        elo_ratings = _get_elo_ratings()
        try:
            from engine.elo import get_elo_features
            elo_feats = get_elo_features(team_a, team_b, elo_ratings)
        except Exception:
            elo_feats = np.array([0.75, 0.75, 0.0])
    features = np.concatenate([features, elo_feats])

    live_feats = build_live_features(team_a, team_b)
    features = np.concatenate([features, live_feats])

    from engine.momentum import MomentumTracker
    mt = MomentumTracker(df=df)
    momentum_feats = mt.get_momentum_features(team_a, team_b)
    features = np.concatenate([features, momentum_feats])

    try:
        from engine.environment import compute_env_score
        env = compute_env_score(team_a, team_b, host or "United States", match_number=0)
    except Exception:
        env = 1.0
    features = np.concatenate([features, np.array([env])])

    return features


def build_training_dataset(df: pd.DataFrame) -> tuple:
    df_sorted = df.sort_values("year").reset_index(drop=True)
    X = []
    y = []
    sample_weights = []
    max_year = int(df_sorted["year"].max())

    clear_live_teams_form()
    cumulative_elo = {}

    y_temp = []
    for idx, row in df_sorted.iterrows():
        if row["home_goals"] > row["away_goals"]:
            y_temp.append(0)
        elif row["home_goals"] == row["away_goals"]:
            y_temp.append(1)
        else:
            y_temp.append(2)
    y_temp = np.array(y_temp)

    class_counts = np.bincount(y_temp, minlength=3).astype(float)
    class_weights = len(y_temp) / (3.0 * class_counts + 1e-9)

    for idx, row in df_sorted.iterrows():
        past_mask = df_sorted.index < idx
        past_df = df_sorted[past_mask]

        features = build_feature_vector(
            past_df, row["home_team"], row["away_team"],
            row["stage"], row["host"],
            cumulative_elo=cumulative_elo,
        )

        if row["home_goals"] > row["away_goals"]:
            label = 0
        elif row["home_goals"] == row["away_goals"]:
            label = 1
        else:
            label = 2

        years_ago = max_year - int(row["year"])
        temporal_weight = TEMPORAL_DECAY_FACTOR ** years_ago
        combined_weight = temporal_weight * class_weights[label]

        X.append(features)
        y.append(label)
        sample_weights.append(combined_weight)

        from engine.elo import update_elo
        cumulative_elo = update_elo(
            cumulative_elo,
            row["home_team"], row["away_team"],
            int(row["home_goals"]), int(row["away_goals"]),
            row["stage"],
            is_neutral=True,
        )

    return np.array(X), np.array(y), np.array(sample_weights)
