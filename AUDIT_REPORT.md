# AUDIT REPORT — ADIVINAT0R

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Archivos auditados | 7 (stats.py, predictor.py, calibration.py, live_data.py, montecarlo.py, worldcup_api.py, main.py) |
| Data Leakage crítico | 4 instancias |
| Redundancia de features | 3 instancias |
| Sobreentrenamiento potencial | Alto (sin validación temporal) |
| Errores conceptuales | 5 |
| Riesgo general | ALTO |

---

## 1. DATA LEAKAGE CRÍTICO

### 1.1 H2H con información futura — `engine/stats.py:41`

**Problema**: `compute_h2h(df, team_a, team_b)` recibe el DataFrame completo con **todos** los partidos históricos (1930-2022). Cuando es llamada desde `build_training_dataset()`, para un partido de 1958, la función usa partidos de 1962, 1970, etc. para calcular el H2H.

**Código afectado**:
```python
def compute_h2h(df: pd.DataFrame, team_a: str, team_b: str) -> dict:
    mask_a = ((df["home_team"] == team_a) & (df["away_team"] == team_b)) | \
             ((df["home_team"] == team_b) & (df["away_team"] == team_a))
    matches = df[mask_a]  # ← Usa TODOS los partidos, incluidos futuros
```

**Impacto**: El modelo aprende patrones que incluyen resultados futuros. Accuracy inflada artificialmente.

**Severidad**: 🔴 CRÍTICO

### 1.2 Team stats con información futura — `engine/stats.py:63`

**Problema**: `compute_team_stats(df, team)` recibe el df completo. Cuando se computa el feature vector para un partido de 1978, las estadísticas del equipo incluyen partidos de 1986, 1994, etc.

**Código afectado**:
```python
def compute_team_stats(df: pd.DataFrame, team: str, recent_years: int = 3) -> dict:
    team_matches = df[(df["home_team"] == team) | (df["away_team"] == team)]
    # ← Incluye partidos FUTUROS al match que se está evaluando
```

**Impacto**: Igual que 1.1. Las estadísticas promedio de goles, win rate, etc. están contaminadas con datos futuros.

**Severidad**: 🔴 CRÍTICO

### 1.3 Attack/Defense factors con información futura — `engine/stats.py:117`

**Problema**: `compute_attack_defense_factors(df)` usa todo el dataset. Los factores de ataque/defensa para un partido de 1930 incluyen datos de 2022.

**Código afectado**:
```python
def compute_attack_defense_factors(df: pd.DataFrame) -> dict:
    all_home_goals = df["home_goals"].mean()  # ← Media de TODOS los mundiales
```

**Impacto**: Los factores λ del Poisson están contaminados con datos futuros.

**Severidad**: 🔴 CRÍTICO

### 1.4 ranking_delta con datos posteriores — `engine/stats.py:190`

**Problema**: `ranking_delta` usa `teams.json`, que contiene estadísticas **acumuladas** de toda la historia (`wins`, `titles`). Si un equipo ganó un título después del partido que se está evaluando, ese título se incluye ilegítimamente.

**Código afectado**:
```python
ranking_a = teams_data.get(team_a, {}).get("titles", 0) * 100 + teams_data.get(team_a, {}).get("wins", 0)
```

**Impacto**: Ranking histórico inflado para equipos exitosos en el futuro.

**Severidad**: 🟡 ALTO

---

## 2. REDUNDANCIA Y MULTICOLINEALIDAD

### 2.1 pr_norm como combinación lineal

**Problema**: `pr_norm` es `(attack_diff + creat_diff + def_diff) / max(abs(sum), 1)`. Esto es una combinación lineal directa de las tres features individuales `attack_a - attack_b`, `creat_a - creat_b`, `def_a - def_b`.

**Impacto**: Perfecta multicolinealidad. El modelo no puede distinguir el efecto individual de cada feature.

**Severidad**: 🟡 ALTO

### 2.2 stage_coeff como feature independiente

**Problema**: `stage_coeff` tiene solo 6 valores discretos (0.5, 0.7, 0.85, 1.0, 1.2, 0.6). Un modelo lineal lo tratará como variable continua, pero la relación con la probabilidad de victoria no es necesariamente lineal.

**Impacto**: Representación subóptima de una variable categórica ordinal.

**Severidad**: 🟢 BAJO

### 2.3 player_power redundant con power_rankings

**Problema**: Tanto `power_rankings` (attack/creativity/defense) como `player_power` vienen de la misma API Fantasy de FIFA. Midan constructos similares (calidad del plantel).

**Impacto**: Features correlacionadas que pueden causar inestabilidad en los coeficientes.

**Severidad**: 🟢 BAJO

---

## 3. SOBREENTRENAMIENTO

### 3.1 Sin validación temporal

**Problema**: El modelo se entrena en TODOS los datos y se evalúa en los mismos datos. No hay walk-forward validation, no hay train/test split temporal.

**Código afectado**:
```python
def build_training_dataset(df: pd.DataFrame) -> tuple:
    X = []
    y = []
    for _, row in df.iterrows():  # ← Entrena en cada fila, evalúa en las mismas
```

**Impacto**: No se puede medir la capacidad predictiva real. Posible sobreajuste severo.

**Severidad**: 🔴 CRÍTICO

### 3.2 Ensemble sin regularización temporal

**Problema**: `RandomForestClassifier(max_depth=6)` y `GradientBoostingClassifier(max_depth=4)` pueden sobreajustar patrones históricos que no se repiten.

**Impacto**: Complejidad innecesaria sin validación que la justifique.

**Severidad**: 🟡 ALTO

---

## 4. ERRORES CONCEPTUALES

### 4.1 Poisson no es Dixon-Coles

**Problema**: La implementación actual genera goles como `Poisson(λ)` independientes para cada equipo. El verdadero modelo Dixon-Coles incluye:

1. Un parámetro de correlación `τ` para resultados bajos (0-0, 1-1)
2. Factor de localía (home advantage)
3. Dependencia entre los goles de ambos equipos

**Código afectado**:
```python
lambda_a = fa["attack"] * fb["defense"] * league_avg  # ← No hay correlación
lambda_b = fb["attack"] * fa["defense"] * league_avg
result["predicted_score"] = f"{max(0, np.random.poisson(lambda_a))}-{max(0, np.random.poisson(lambda_b))}"
```

**Impacto**: Las predicciones de marcador no capturan la correlación empírica entre goles.

**Severidad**: 🟡 ALTO

### 4.2 Decaimiento temporal mal implementado

**Problema**: `compute_team_stats` aplica weight=2.0 a los 3 años más recientes de cada equipo, pero esto:

1. Es por equipo individual, no por fecha del partido
2. No hay decaimiento exponencial real
3. `build_training_dataset` no usa sample weights en el entrenamiento

**Código afectado**:
```python
weight = 2.0 if row["year"] in recent_years_set else 1.0
# Esto se usa para promediar stats, no como peso de entrenamiento
```

**Impacto**: Los partidos recientes no pesan más en el entrenamiento que los antiguos.

**Severidad**: 🟡 ALTO

### 4.3 Sin métricas de calibración

**Problema**: `CalibrationTracker` solo mide Brier Score y accuracy. No hay:

- Log Loss
- Reliability curve
- Expected Calibration Error (ECE)
- Precision/Recall/F1 por clase

**Impacto**: No se puede evaluar la calibración de probabilidades ni detectar overconfidence.

**Severidad**: 🟡 ALTO

### 4.4 Power Rankings con Leakage de fantasy API

**Problema**: `SEED_POWER_RANKINGS` contiene valores hardcodeados del Mundial 2026 actual. Si algún equipo no está en el seed, queda con 0 en ataque/creatividad/defensa.

**Impacto**: Equipos nuevos o little-known reciben score 0, sesgando predicciones.

**Severidad**: 🟢 BAJO

### 4.5 StandardScaler mal aplicado

**Problema**: El scaler se ajusta sobre todo el dataset (incluyendo datos de test futuros). Esto es data leakage adicional.

```python
self.scaler = StandardScaler()
X_scaled = self.scaler.fit_transform(X)  # ← fit_transform sobre TODO
```

**Severidad**: 🟡 ALTO

---

## 5. PROBLEMAS DE PERFORMANCE

### 5.1 Loop en build_training_dataset

**Problema**: Itera fila por fila con `for _, row in df.iterrows()`, llamando a `build_feature_vector` que internamente tiene más loops.

**Impacto**: O(n²) en la práctica. 967 partidos × múltiples operaciones por feature.

**Severidad**: 🟢 BAJO

### 5.2 compute_attack_defense_factors llamado múltiples veces

**Problema**: Cada `_estimate_lambda()` llama a `compute_attack_defense_factors()` que recalcula desde cero.

**Impacto**: Cálculo redundante O(n) por cada predicción.

**Severidad**: 🟢 BAJO

---

## 6. RECOMENDACIONES PRIORIZADAS

| Prioridad | Cambio | Fase | Esfuerzo |
|-----------|--------|------|----------|
| 🔴 P0 | Eliminar data leakage (H2H, team stats, attack/defense) | F1+F4 | 2h |
| 🔴 P0 | Walk-forward validation | F2 | 3h |
| 🟡 P1 | Pesos temporales reales | F4 | 1h |
| 🟡 P1 | ELO ratings | F3 | 3h |
| 🟡 P1 | SHAP explainability | F5 | 2h |
| 🟡 P1 | Calibration metrics | F6 | 1h |
| 🟢 P2 | Poisson Dixon-Coles real | F7 | 2h |
| 🟢 P2 | Optimización vectorización | F8 | 1h |

---

## 7. MÉTRICAS BASE (ANTES)

Medidas sobre datos actuales (contaminados):

- Accuracy: ~55-60% (inflada por data leakage)
- Brier Score: ~0.35 (artificialmente bajo)
- Log Loss: ~1.1

*Nota: Estas métricas no son fiables por el data leakage detectado.*
