import json
import os
import numpy as np
from datetime import datetime

CALIB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CALIB_PATH = os.path.join(CALIB_DIR, "calibration_log.json")


class CalibrationTracker:
    def __init__(self):
        self.log = self._load_log()

    def _load_log(self):
        if os.path.exists(CALIB_PATH):
            try:
                with open(CALIB_PATH) as f:
                    return json.load(f)
            except Exception:
                return {"predictions": []}
        return {"predictions": []}

    def _save_log(self):
        os.makedirs(CALIB_DIR, exist_ok=True)
        with open(CALIB_PATH, "w") as f:
            json.dump(self.log, f, indent=2)

    def log_prediction(self, team_a: str, team_b: str, stage: str,
                       prob_a: float, prob_draw: float, prob_b: float,
                       actual: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "team_a": team_a, "team_b": team_b,
            "stage": stage,
            "prob_a": prob_a, "prob_draw": prob_draw, "prob_b": prob_b,
            "actual": actual
        }
        self.log["predictions"].append(entry)
        self._save_log()

    def _get_probs_matrix(self):
        preds = self.log["predictions"]
        if not preds:
            return None, None
        n = len(preds)
        probs = np.zeros((n, 3))
        y_true = np.zeros(n, dtype=int)
        valid = np.ones(n, dtype=bool)
        for i, p in enumerate(preds):
            probs[i] = [p["prob_a"], p["prob_draw"], p["prob_b"]]
            actual_map = {"team_a": 0, "draw": 1, "team_b": 2}
            actual_idx = actual_map.get(p.get("actual", ""), -1)
            if actual_idx < 0:
                valid[i] = False
            else:
                y_true[i] = actual_idx
        return probs[valid], y_true[valid]

    def get_brier_score(self) -> float:
        preds = self.log["predictions"]
        if not preds:
            return 0.0
        scores = []
        for p in preds:
            probs = [p["prob_a"], p["prob_draw"], p["prob_b"]]
            actual_idx = {"team_a": 0, "draw": 1, "team_b": 2}.get(p.get("actual", ""), -1)
            if actual_idx < 0:
                continue
            one_hot = [0, 0, 0]
            one_hot[actual_idx] = 1
            sq_error = sum((probs[i] - one_hot[i]) ** 2 for i in range(3))
            scores.append(sq_error)
        return round(sum(scores) / len(scores), 4) if scores else 0.0

    def get_accuracy(self) -> float:
        preds = self.log["predictions"]
        if not preds:
            return 0.0
        correct = 0
        for p in preds:
            probs = [p["prob_a"], p["prob_draw"], p["prob_b"]]
            predicted_idx = int(np.argmax(probs))
            actual_map = {"team_a": 0, "draw": 1, "team_b": 2}
            actual_idx = actual_map.get(p.get("actual", ""), -1)
            if predicted_idx == actual_idx:
                correct += 1
        return round(correct / len(preds) * 100, 1) if preds else 0.0

    def get_log_loss(self) -> float:
        from engine.calibration_metrics import compute_log_loss
        probs, y_true = self._get_probs_matrix()
        if probs is None or len(probs) == 0:
            return 0.0
        return compute_log_loss(probs, y_true)

    def get_ece(self, n_bins: int = 10) -> float:
        from engine.calibration_metrics import compute_ece
        probs, y_true = self._get_probs_matrix()
        if probs is None or len(probs) == 0:
            return 0.0
        return compute_ece(probs, y_true, n_bins)

    def get_reliability_curve(self, n_bins: int = 10) -> list:
        from engine.calibration_metrics import compute_reliability_curve
        probs, y_true = self._get_probs_matrix()
        if probs is None or len(probs) == 0:
            return []
        return compute_reliability_curve(probs, y_true, n_bins)

    def get_accuracy_by_stage(self) -> dict:
        preds = self.log["predictions"]
        stages = {}
        for p in preds:
            stage = p.get("stage", "Unknown")
            if stage not in stages:
                stages[stage] = {"correct": 0, "total": 0}
            probs = [p["prob_a"], p["prob_draw"], p["prob_b"]]
            predicted_idx = int(np.argmax(probs))
            actual_map = {"team_a": 0, "draw": 1, "team_b": 2}
            actual_idx = actual_map.get(p.get("actual", ""), -1)
            stages[stage]["total"] += 1
            if predicted_idx == actual_idx:
                stages[stage]["correct"] += 1
        result = {}
        for stage, data in stages.items():
            result[stage] = round(data["correct"] / data["total"] * 100, 1)
        return result

    def get_recent_predictions(self, n: int = 12) -> list:
        preds = self.log["predictions"][-n:]
        result = []
        for p in preds:
            probs = [p["prob_a"], p["prob_draw"], p["prob_b"]]
            predicted_idx = int(np.argmax(probs))
            max_prob = max(probs)
            color = "green" if max_prob >= 0.75 else "amber" if max_prob >= 0.70 else "dark"
            actual_map = {"team_a": 0, "draw": 1, "team_b": 2}
            actual_idx = actual_map.get(p.get("actual", ""), -1)
            correct = predicted_idx == actual_idx
            result.append({
                "teams": f"{p['team_a']} vs {p['team_b']}",
                "predicted": ["A Win", "Draw", "B Win"][predicted_idx],
                "actual": p.get("actual", "?"),
                "confidence": round(max_prob * 100, 1),
                "correct": correct,
                "color": color
            })
        return result

    def get_concentracion_delta(self) -> float:
        return 0.0

    def reload(self):
        self.log = self._load_log()

    def reset(self):
        self.log = {"predictions": []}
        if os.path.exists(CALIB_PATH):
            os.remove(CALIB_PATH)
