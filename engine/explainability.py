import numpy as np
import shap

from engine.stats import FEATURE_NAMES as STATS_FEATURE_NAMES

FEATURE_NAMES = STATS_FEATURE_NAMES

TOP_K = 5


def explain_prediction(model, scaler, feature_vector: np.ndarray) -> dict:
    feature_vector_2d = feature_vector.reshape(1, -1)
    feature_vector_scaled = scaler.transform(feature_vector_2d)

    background = _sample_background(scaler, n_samples=80)
    if background is None:
        return {"error": "No se pudo generar explicación"}

    try:
        explainer = shap.KernelExplainer(model.predict_proba, background)
        shap_values = explainer.shap_values(feature_vector_scaled, silent=True)
    except Exception as e:
        return {"error": str(e)}

    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        n_classes = shap_values.shape[2]
        base_arr = shap_values[0]
    elif isinstance(shap_values, list):
        n_classes = len(shap_values)
        base_arr = None
    else:
        return {"error": "Formato SHAP no reconocido"}

    explanations = {}
    for class_idx in range(n_classes):
        if base_arr is not None:
            sv = base_arr[:, class_idx]
        else:
            sv = shap_values[class_idx][0] if shap_values[class_idx].ndim > 1 else shap_values[class_idx]

        feature_contribs = list(zip(FEATURE_NAMES, sv))
        feature_contribs.sort(key=lambda x: abs(x[1]), reverse=True)

        top_positive = [(name, round(val, 4)) for name, val in feature_contribs if val > 0][:TOP_K]
        top_negative = [(name, round(val, 4)) for name, val in feature_contribs if val < 0][:TOP_K]

        explanations[class_idx] = {
            "top_positive": top_positive,
            "top_negative": top_negative,
        }

    return explanations


def _sample_background(scaler, n_samples=80):
    from engine.stats import load_matches, build_feature_vector
    df = load_matches()
    n_total = len(df)
    if n_total == 0:
        return None
    step = max(1, n_total // n_samples)
    backgrounds = []
    for i in range(0, n_total, step):
        row = df.iloc[i]
        try:
            fv = build_feature_vector(df, row["home_team"], row["away_team"], row["stage"], row.get("host"))
            backgrounds.append(fv)
        except Exception:
            continue
        if len(backgrounds) >= n_samples:
            break
    if not backgrounds:
        return None
    bg = np.array(backgrounds)
    return scaler.transform(bg)
