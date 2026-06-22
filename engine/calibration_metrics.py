import numpy as np


def compute_ece(probs: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error — lower is better."""
    n_classes = probs.shape[1] if probs.ndim > 1 else 1
    if n_classes == 1:
        probs = np.column_stack([1 - probs, probs])
        n_classes = 2

    y_true_onehot = np.eye(n_classes)[y_true]
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == y_true).astype(float)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            avg_confidence = np.mean(confidences[in_bin])
            avg_accuracy = np.mean(accuracies[in_bin])
            ece += np.abs(avg_accuracy - avg_confidence) * prop_in_bin

    return float(ece)


def compute_reliability_curve(probs: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> list:
    """Return list of (bin_center, accuracy, confidence, count) for each bin."""
    n_classes = probs.shape[1] if probs.ndim > 1 else 1
    if n_classes == 1:
        probs = np.column_stack([1 - probs, probs])
        n_classes = 2

    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == y_true).astype(float)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    curve = []
    for i in range(n_bins):
        in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
        count = int(np.sum(in_bin))
        if count > 0:
            bin_center = (bin_boundaries[i] + bin_boundaries[i + 1]) / 2
            avg_conf = float(np.mean(confidences[in_bin]))
            avg_acc = float(np.mean(accuracies[in_bin]))
            curve.append({
                "bin_center": round(bin_center, 3),
                "accuracy": round(avg_acc, 4),
                "confidence": round(avg_conf, 4),
                "count": count,
            })
    return curve


def compute_brier_score_decomposed(probs: np.ndarray, y_true: np.ndarray) -> dict:
    """Decompose Brier Score into refinement, calibration, and uncertainty."""
    n_classes = probs.shape[1] if probs.ndim > 1 else 1
    if n_classes == 1:
        probs = np.column_stack([1 - probs, probs])
        n_classes = 2

    y_true_onehot = np.eye(n_classes)[y_true]
    n = len(y_true)

    brier = np.mean(np.sum((probs - y_true_onehot) ** 2, axis=1))

    base_rate = np.mean(y_true_onehot, axis=0)
    uncertainty = np.mean(np.sum(base_rate * (1 - base_rate)))

    return {
        "brier_score": round(float(brier), 4),
        "uncertainty": round(float(uncertainty), 4),
    }


def compute_log_loss(probs: np.ndarray, y_true: np.ndarray, eps: float = 1e-15) -> float:
    n_classes = probs.shape[1]
    if n_classes == 1:
        probs = np.column_stack([1 - probs, probs])
        n_classes = 2
    probs = np.clip(probs, eps, 1 - eps)
    ll = -np.mean(np.log(probs[np.arange(len(y_true)), y_true]))
    return round(float(ll), 4)
