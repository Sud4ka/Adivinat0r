import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, brier_score_loss, log_loss

from engine.stats import (
    load_matches, get_stage_coefficient, get_continent, _load_power_rankings,
    load_player_power, _compute_cumulative_ranking
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
BACKTEST_PATH = os.path.join(DATA_DIR, "backtest_results.json")
TEMPORAL_DECAY_FACTOR = 0.94


def _build_features_for_row(df, row, mask, cumulative_elo=None, max_year=2022):
    team_a = row["home_team"]
    team_b = row["away_team"]
    stage = row["stage"]
    host = row["host"]

    submask = mask
    past_df = df[submask]

    from engine.stats import compute_h2h, compute_team_stats
    h2h = compute_h2h(past_df, team_a, team_b)
    stats_a = compute_team_stats(past_df, team_a)
    stats_b = compute_team_stats(past_df, team_b)
    stage_coeff = get_stage_coefficient(stage)
    continent_a = get_continent(team_a)
    continent_b = get_continent(team_b)

    ranking_a = _compute_cumulative_ranking(past_df, team_a)
    ranking_b = _compute_cumulative_ranking(past_df, team_b)
    ranking_delta = ranking_a - ranking_b

    home_continent_adv = 1.0 if host and continent_a == get_continent(host) else 0.0

    pr = _load_power_rankings()
    pr_a = pr.get(team_a, {})
    pr_b = pr.get(team_b, {})
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
    pp_features = np.array([pp_a / pp_max, pp_b / pp_max, (pp_a - pp_b) / pp_max])
    features = np.concatenate([features, pp_features])

    if cumulative_elo is not None:
        from engine.elo import get_elo_features
        elo_feats = get_elo_features(team_a, team_b, cumulative_elo)
    else:
        from engine.elo import load_elo_ratings, compute_all_elo
        ratings = load_elo_ratings()
        if not ratings:
            ratings = compute_all_elo()
        from engine.elo import get_elo_features
        elo_feats = get_elo_features(team_a, team_b, ratings)
    features = np.concatenate([features, elo_feats])

    return features


def walk_forward_validation() -> dict:
    df = load_matches()
    df = df.sort_values("year").reset_index(drop=True)
    max_year_total = int(df["year"].max())

    windows = [
        ("1930-2014 -> 2018", 2014, 2018),
        ("1930-2018 -> 2022", 2018, 2022),
    ]

    all_metrics = {}

    for window_name, train_up_to, test_year in windows:
        train_mask = df["year"] <= train_up_to
        test_mask = df["year"] == test_year

        X_train = []
        y_train = []
        sw_train = []
        cumulative_elo = {}

        train_indices = df[train_mask].index
        for idx in train_indices:
            row = df.loc[idx]
            past_mask = df.index < idx
            feats = _build_features_for_row(df, row, past_mask, cumulative_elo, max_year_total)
            X_train.append(feats)
            if row["home_goals"] > row["away_goals"]:
                y_train.append(0)
            elif row["home_goals"] == row["away_goals"]:
                y_train.append(1)
            else:
                y_train.append(2)
            years_ago = max_year_total - int(row["year"])
            sw_train.append(TEMPORAL_DECAY_FACTOR ** years_ago)

            from engine.elo import update_elo
            cumulative_elo = update_elo(
                cumulative_elo, row["home_team"], row["away_team"],
                int(row["home_goals"]), int(row["away_goals"]),
                row["stage"], is_neutral=True,
            )

        X_train = np.array(X_train)
        y_train = np.array(y_train)
        sw_train = np.array(sw_train)

        class_counts = np.bincount(y_train, minlength=3)
        class_weights = len(y_train) / (3 * class_counts + 1e-9)
        sw_train *= class_weights[y_train]

        from sklearn.preprocessing import StandardScaler
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
        from sklearn.linear_model import LogisticRegression

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        lr = LogisticRegression(max_iter=1000, solver="lbfgs", class_weight="balanced", random_state=42)
        rf = RandomForestClassifier(n_estimators=200, max_depth=6, class_weight="balanced", random_state=42)
        gb = GradientBoostingClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42)
        model = VotingClassifier(
            estimators=[("lr", lr), ("rf", rf), ("gb", gb)],
            voting="soft", weights=[1, 2, 2]
        )
        model.fit(X_train_scaled, y_train, sample_weight=sw_train)

        X_test = []
        y_test = []
        cumulative_elo_test = dict(cumulative_elo)

        test_indices = df[test_mask].index
        for idx in test_indices:
            row = df.loc[idx]
            past_mask = df.index < idx
            feats = _build_features_for_row(df, row, past_mask, cumulative_elo_test, max_year_total)
            X_test.append(feats)
            if row["home_goals"] > row["away_goals"]:
                y_test.append(0)
            elif row["home_goals"] == row["away_goals"]:
                y_test.append(1)
            else:
                y_test.append(2)

            from engine.elo import update_elo
            cumulative_elo_test = update_elo(
                cumulative_elo_test, row["home_team"], row["away_team"],
                int(row["home_goals"]), int(row["away_goals"]),
                row["stage"], is_neutral=True,
            )

        X_test = np.array(X_test)
        y_test = np.array(y_test)
        X_test_scaled = scaler.transform(X_test)

        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)

        acc = accuracy_score(y_test, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)

        brier_total = 0
        for i in range(len(y_test)):
            one_hot = np.zeros(3)
            one_hot[y_test[i]] = 1
            brier_total += np.sum((y_proba[i] - one_hot) ** 2)
        brier_multi = brier_total / len(y_test)

        try:
            ll = log_loss(y_test, y_proba)
        except Exception:
            ll = float("inf")

        all_metrics[window_name] = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "brier_score": round(brier_multi, 4),
            "log_loss": round(ll, 4),
            "test_samples": len(y_test),
        }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BACKTEST_PATH, "w") as f:
        json.dump(all_metrics, f, indent=2)

    return all_metrics


def load_backtest_results() -> dict:
    try:
        with open(BACKTEST_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


if __name__ == "__main__":
    results = walk_forward_validation()
    print(json.dumps(results, indent=2))
