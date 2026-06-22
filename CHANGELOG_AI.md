# CHANGELOG AI — ADIVINAT0R

## [2.1.0] — 2026-06

### Añadido

#### FASE 2 — Walk Forward Validation (`engine/backtesting.py`)
- Validación temporal con 2 ventanas: 1930-2014→2018 y 1930-2018→2022
- Métricas: Accuracy, Precision, Recall, F1, Brier Score, Log Loss
- `build_feature_vector` filtrado por fecha (solo datos anteriores al partido evaluado)
- Resultados guardados en `data/backtest_results.json`
- Accuracy real sin data leakage: 48.4% (2018), 51.6% (2022)

#### FASE 3 — Sistema ELO (`engine/elo.py`)
- Rating ELO internacional con K variable:
  - K=32 para Mundiales
  - K=24 para Eliminatorias
  - K=16 para Amistosos
- Inicialización automática desde 1930
- 3 features: `elo_a`, `elo_b`, `elo_diff` (normalizados)
- Cache persistente en `data/elo_ratings.json`
- Top 3 equipos: Netherlands 1718, France 1704, Brazil 1699

#### FASE 4 — Pesos Temporales
- Decaimiento exponencial en `build_training_dataset()`: `TEMPORAL_DECAY_FACTOR = 0.94`
- Partidos 2022 pesan ~2.4× más que 1930
- Pesos aplicados como `sample_weight` durante el entrenamiento
- Rango de pesos: 0.0034 (1930) a 1.0000 (2022)

#### FASE 5 — SHAP Explainability (`engine/explainability.py`)
- KernelExplainer para explicaciones locales compatibles con VotingClassifier
- Top 5 factores positivos y negativos por clase (win/draw/loss)
- 28 feature names sincronizados con `engine.stats.FEATURE_NAMES`
- Background sampling automático desde el dataset histórico
- Integrado en `predictor_view.py` → actualiza `self.factors_label`

#### FASE 6 — Calibración Avanzada (`engine/calibration_metrics.py`)
- Expected Calibration Error (ECE)
- Reliability Curve por bins de confianza
- Brier Score desglosado (refinement + calibration + uncertainty)
- Log Loss real
- Integrado en `CalibrationTracker` y `CalibrationScreen`

#### FASE 7 — Dixon-Coles Poisson (`engine/poisson.py`)
- Modelo de goles con dependencia τ (tau) para correlación en resultados de pocos goles
- `GoalModel` class con métodos:
  - `estimate_lambdas()` → λ_A, λ_B
  - `dixon_coles_tau()` → factor de corrección para 0-0, 0-1, 1-0, 1-1
  - `joint_probability()` → P(X=x, Y=y) con corrección τ
  - `simulate_score()` → marcador muestreado con τ
  - `match_outcome_probs()` → probabilidades exactas por suma hasta max_goals
- Reemplaza Poisson ingenuo en `predictor.py`

#### FASE 8 — Optimización de Rendimiento
- `compute_attack_defense_factors()` vectorizado con `groupby().agg()`
- `build_training_dataset()` ordena cronológicamente y filtra por índice
- Feature matrix precalculada evita recomputaciones en cada iteración

### Modificado

- **engine/stats.py**:
  - `build_training_dataset()` ahora retorna `(X, y, sample_weights)` en lugar de `(X, y)`
  - `build_feature_vector()` ahora incluye 3 features ELO (total: 28 dimensiones)
  - `FEATURE_NAMES` constante pública con 28 nombres
  - `TEMPORAL_DECAY_FACTOR = 0.94` para pesos temporales

- **engine/predictor.py**:
  - `fit()` acepta `sample_weight` y lo pasa a `VotingClassifier.fit()`
  - `predict_proba()` usa `GoalModel.simulate_score()` en vez de Poisson ingenuo
  - Todos los métodos actualizados para el nuevo signature de `build_training_dataset`
  - `_load_or_train()` y `retrain*()` regeneran modelos automáticamente
  - `random_state=42` en todos los clasificadores para reproducibilidad

- **engine/calibration.py**:
  - `get_log_loss()` usando `calibration_metrics.compute_log_loss()`
  - `get_ece()` usando `calibration_metrics.compute_ece()`
  - `get_reliability_curve()` usando `calibration_metrics.compute_reliability_curve()`

- **gui/predictor_view.py**:
  - `run_prediction()` muestra SHAP explanations en `self.factors_label`
  - `model_info` muestra Log Loss y ECE además de Brier y Accuracy
  - Fallback al texto original si SHAP no está disponible

- **gui/calibration_view.py**:
  - `logloss_val` ahora muestra Log Loss real (no Brier como antes)
  - Detalles incluyen ECE y Reliability Curve

- **main.py**:
  - `TrainThread.run()` maneja el nuevo signature de 3 valores

### Corregido

- **Data Leakage CRÍTICO**: `build_training_dataset()` ahora filtra por índice secuencial (`past_mask = df_sorted.index < idx`), eliminando la contaminación con información futura en:
  - `compute_h2h()` (usaba todo el dataset)
  - `compute_team_stats()` (usaba todo el dataset)
  - `compute_attack_defense_factors()` (usaba todo el dataset)

### Eliminado

- Modelos joblib antiguos (`model.joblib`, `scaler.joblib`) — regenerados con 28 features
- Código redundante de Poisson ingenuo en predictor.py (reemplazado por Dixon-Coles)

### Métricas de Validación

| Ventana | Accuracy | Precision | Recall | F1 | Brier | Log Loss |
|---------|----------|-----------|--------|-----|-------|----------|
| 1930-2014→2018 | 48.44% | 45.83% | 48.44% | 42.39% | 0.2022 | 1.0102 |
| 1930-2018→2022 | 51.56% | 51.49% | 51.56% | 51.16% | 0.2063 | 1.0328 |

### Feature Vector (28 dimensiones)

1. h2h_a_wins_ratio
2. h2h_b_wins_ratio
3. h2h_draws_ratio
4. stats_a_avg_goals_scored
5. stats_a_avg_goals_conceded
6. stats_b_avg_goals_scored
7. stats_b_avg_goals_conceded
8. stats_a_win_rate
9. stats_b_win_rate
10. stage_coeff
11. ranking_delta
12. home_continent_adv
13. same_continent
14. attack_diff
15. creat_diff
16. def_diff
17. pr_norm
18. player_power_a
19. player_power_b
20. player_power_diff
21. elo_a
22. elo_b
23. elo_diff
24. form_gf_diff
25. form_ga_diff
26. form_win_rate_diff
27. form_ppg_diff
28. form_gd_norm
