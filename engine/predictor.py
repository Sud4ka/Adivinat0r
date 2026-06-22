import os
import numpy as np
import joblib
from abc import ABC, abstractmethod
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier

from engine.stats import (
    load_matches, build_training_dataset, build_feature_vector,
    load_teams, set_live_teams_form, get_live_teams_form
)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")


class BasePredictor(ABC):
    @abstractmethod
    def fit(self, X, y, sample_weight=None):
        pass

    @abstractmethod
    def predict_proba(self, team_a: str, team_b: str, stage: str, host: str = None) -> dict:
        pass


class LogisticPredictor(BasePredictor):
    def __init__(self):
        self.model = None
        self.scaler = None
        self.df = None

    def fit(self, X, y, sample_weight=None):
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = LogisticRegression(max_iter=1000, solver="lbfgs", class_weight="balanced", random_state=42)
        self.model.fit(X_scaled, y, sample_weight=sample_weight)
        self.df = load_matches()

    def predict_proba(self, team_a: str, team_b: str, stage: str, host: str = None) -> dict:
        if self.model is None:
            self._load_or_train()
        features = build_feature_vector(self.df, team_a, team_b, stage, host).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        probs = self.model.predict_proba(features_scaled)[0]

        class_labels = {0: "win", 1: "draw", 2: "loss"}
        result = {}
        for i, label in class_labels.items():
            prob = float(probs[i]) if i < len(probs) else 0.0
            result[f"{team_a}_{label}"] = prob

        from engine.poisson import GoalModel
        from engine.stats import compute_attack_defense_factors
        factors = compute_attack_defense_factors(self.df)
        gm = GoalModel()
        lambda_a, lambda_b = gm.estimate_lambdas(team_a, team_b, factors)
        x, y = gm.simulate_score(team_a, team_b, factors)
        result["predicted_score"] = f"{x}-{y}"

        return result

    def _check_dimensions(self):
        if self.model is None:
            return False
        expected = self.model.coef_.shape[1]
        sample_features = build_feature_vector(self.df, "Argentina", "Brazil", "Group Stage")
        actual = len(sample_features)
        if expected != actual:
            return False
        return True

    def _load_or_train(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self.df = load_matches()
            if not self._check_dimensions():
                self.df = load_matches()
                X, y, sw = build_training_dataset(self.df)
                self.fit(X, y, sw)
                os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
                joblib.dump(self.model, MODEL_PATH)
                joblib.dump(self.scaler, SCALER_PATH)
        else:
            self.df = load_matches()
            X, y, sw = build_training_dataset(self.df)
            self.fit(X, y, sw)
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.scaler, SCALER_PATH)

    def retrain(self):
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        if os.path.exists(SCALER_PATH):
            os.remove(SCALER_PATH)
        self.model = None
        self.scaler = None
        self._load_or_train()

    def retrain_with_live_data(self, teams_form: dict = None):
        if teams_form:
            set_live_teams_form(teams_form)
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        if os.path.exists(SCALER_PATH):
            os.remove(SCALER_PATH)
        self.model = None
        self.scaler = None
        self.df = load_matches()
        from engine.live_data import compute_all_teams_form, load_2026_results
        if not teams_form:
            matches_2026 = load_2026_results()
            teams_form = compute_all_teams_form(matches_2026)
            set_live_teams_form(teams_form)
        X, y, sw = build_training_dataset(self.df)
        self.fit(X, y, sw)
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.scaler, SCALER_PATH)


class EnsemblePredictor(BasePredictor):
    def __init__(self):
        self.model = None
        self.scaler = None
        self.df = None
        self._factors = {}
        self.validation_metrics = {}

    def fit(self, X, y, sample_weight=None, validation_split=0.0):
        n = len(X)
        if validation_split > 0 and n >= 50:
            split = int(n * (1 - validation_split))
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]
            sw_train = sample_weight[:split] if sample_weight is not None else None
        else:
            X_train, y_train, sw_train = X, y, sample_weight
            X_val = y_val = None

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_train)

        lr = LogisticRegression(max_iter=1000, solver="lbfgs", class_weight="balanced", random_state=42)
        rf = RandomForestClassifier(n_estimators=200, max_depth=6, class_weight="balanced", random_state=42)
        gb = GradientBoostingClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42)

        self.model = VotingClassifier(
            estimators=[("lr", lr), ("rf", rf), ("gb", gb)],
            voting="soft",
            weights=[1, 2, 2]
        )
        self.model.fit(X_scaled, y_train, sample_weight=sw_train)
        self.df = load_matches()

        if X_val is not None and len(X_val) > 0:
            from sklearn.metrics import accuracy_score, log_loss
            X_val_scaled = self.scaler.transform(X_val)
            y_pred = self.model.predict(X_val_scaled)
            y_proba = self.model.predict_proba(X_val_scaled)
            self.validation_metrics = {
                "accuracy": round(float(accuracy_score(y_val, y_pred)), 4),
                "log_loss": round(float(log_loss(y_val, y_proba)), 4),
                "val_samples": len(y_val),
            }

    def predict_proba(self, team_a: str, team_b: str, stage: str, host: str = None) -> dict:
        if self.model is None:
            self._load_or_train()
        features = build_feature_vector(self.df, team_a, team_b, stage, host).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        probs = self.model.predict_proba(features_scaled)[0]

        class_labels = {0: "win", 1: "draw", 2: "loss"}
        result = {}
        for i, label in class_labels.items():
            result[f"{team_a}_{label}"] = float(probs[i]) if i < len(probs) else 0.0

        from engine.poisson import GoalModel
        from engine.stats import compute_attack_defense_factors
        if not self._factors:
            self._factors = compute_attack_defense_factors(self.df)
        gm = GoalModel()
        x, y = gm.simulate_score(team_a, team_b, self._factors)
        result["predicted_score"] = f"{x}-{y}"

        return result

    def _check_dimensions(self):
        if self.model is None:
            return False
        expected = self.model.n_features_in_
        sample_features = build_feature_vector(self.df, "Argentina", "Brazil", "Group Stage")
        actual = len(sample_features)
        return expected == actual

    def _load_or_train(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self.df = load_matches()
            if not self._check_dimensions():
                self.df = load_matches()
                X, y, sw = build_training_dataset(self.df)
                self.fit(X, y, sw, validation_split=0.15)
                os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
                joblib.dump(self.model, MODEL_PATH)
                joblib.dump(self.scaler, SCALER_PATH)
        else:
            self.df = load_matches()
            X, y, sw = build_training_dataset(self.df)
            self.fit(X, y, sw, validation_split=0.15)
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.scaler, SCALER_PATH)

    def retrain(self):
        for p in [MODEL_PATH, SCALER_PATH]:
            if os.path.exists(p):
                os.remove(p)
        self.model = None
        self.scaler = None
        self._load_or_train()

    def retrain_with_live_data(self, teams_form=None):
        from engine.stats import set_live_teams_form
        from engine.live_data import compute_all_teams_form, load_2026_results
        if teams_form:
            set_live_teams_form(teams_form)
        else:
            matches_2026 = load_2026_results()
            teams_form = compute_all_teams_form(matches_2026)
            set_live_teams_form(teams_form)
        self.retrain()


def create_predictor(model_type: str = "ensemble") -> BasePredictor:
    if model_type == "ensemble":
        return EnsemblePredictor()
    if model_type == "logistic":
        return LogisticPredictor()
    raise ValueError(f"Unknown model type: {model_type}")
