import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, brier_score_loss, log_loss

from engine.stats import (
    load_matches, build_feature_vector,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
BACKTEST_PATH = os.path.join(DATA_DIR, "backtest_results.json")
TEMPORAL_DECAY_FACTOR = 0.94


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

        from engine.stats import clear_live_teams_form
        clear_live_teams_form()

        train_indices = df[train_mask].index
        for idx in train_indices:
            row = df.loc[idx]
            past_mask = df.index < idx
            past_df = df[past_mask]
            feats = build_feature_vector(
                past_df, row["home_team"], row["away_team"],
                row["stage"], row["host"],
                cumulative_elo=cumulative_elo,
            )
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
            past_df = df[past_mask]
            feats = build_feature_vector(
                past_df, row["home_team"], row["away_team"],
                row["stage"], row["host"],
                cumulative_elo=cumulative_elo_test,
            )
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
