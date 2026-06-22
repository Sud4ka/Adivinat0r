# README AUDIT — ADIVINAT0R

## Discrepancias entre README.md y el código real

### 1. Cantidad de features

| Afirmación | README.md | Código real |
|:-----------|:----------|:------------|
| Features | 25 | **27** |
| Históricas | 17 | **16** (se eliminó `pr_norm` por multicolinealidad) |
| Player Power | 3 | 3 |
| ELO | No mencionado | **3** (`elo_a`, `elo_b`, `elo_diff`) |
| Live Form | 5 | 5 |

**Acción**: Actualizar todas las referencias a 27 features con las 4 categorías reales.

---

### 2. Feature Toggles UI-only

El README describe 6 feature toggles como funcionalidades activas:

| Toggle | ¿Afecta al modelo? |
|:-------|:-------------------|
| Momentum Neural | ❌ **UI-only** — `momentum.py` existe pero nunca se importa |
| Ambientales | ❌ **UI-only** — `environment.py` existe pero nunca se importa |
| H2H Profundo | ❌ **UI-only** — usa `compute_h2h()` básico siempre |
| Generaciones | ❌ **UI-only** — `generations.py` no se integra al predictor |
| xG Histórico | ❌ **UI-only** — no hay datos de xG |
| Modo Fantasía | ❌ **UI-only** — no afecta predicciones |

**Acción**: Documentar como "interfaz preparada para expansiones futuras" o eliminar del README como funcionalidad existente.

---

### 3. Funcionalidades implementadas pero no documentadas

| Funcionalidad | Archivo | README |
|:--------------|:--------|:-------|
| Sistema ELO (3 features) | `engine/elo.py` | ❌ Ausente |
| SHAP Explainability | `engine/explainability.py` | ❌ Ausente |
| Walk Forward Validation | `engine/backtesting.py` | ❌ Ausente |
| Decaimiento temporal (0.94) | `engine/stats.py:7` | ❌ Ausente |
| Calibration Metrics (ECE, Log Loss) | `engine/calibration_metrics.py` | ❌ Ausente |
| Dixon-Coles con τ | `engine/poisson.py` | ❌ Solo mencionado superficialmente |
| 92 equipos en teams.json | `data/teams.json` | ❌ Dice 73 |
| Corrección multicolinealidad | Eliminación de `pr_norm` | ❌ Ausente |

**Acción**: Agregar todas al README.

---

### 4. Código muerto (no utilizado)

| Archivo | Líneas | Estado |
|:--------|:-------|:-------|
| `engine/momentum.py` | 52 | No se importa en ningún lado |
| `engine/environment.py` | 117 | No se importa en ningún lado |
| `engine/alerts.py` | 59 | No se usa; `alerts_dialog.py` lo reemplaza |
| `engine/generations.py` | 142 | No se usa en el predictor |

**Acción**: Mencionar como "módulos disponibles para expansión" o eliminarlos de la lista de funcionalidades activas.

---

### 5. Dependencias faltantes en requirements.txt

- `shap>=0.52` — instalado, usado por `explainability.py`
- `numba` — instalado como dependencia de shap
- `cloudpickle` — instalado como dependencia de shap

**Acción**: Agregar `shap` a `requirements.txt`.

---

### 6. Datos incorrectos

| README | Dato real |
|:-------|:----------|
| "73 selecciones" en teams.json | **92** equipos |
| "25 características en 5 categorías" | **27** features en **4** categorías |
| Mention de "momentum neural" como feature activa | Solo toggle UI |
| "Ambientales" como feature activa | Solo toggle UI |

**Acción**: Corregir todas las cifras.

---

### 7. Métricas y validación

| Lo que README dice | Lo que realmente hay |
|:-------------------|:---------------------|
| Brier Score mencionado | ✅ Implementado |
| Accuracy mencionada | ✅ Implementada |
| Log Loss no mencionado | ✅ Implementado |
| ECE no mencionado | ✅ Implementado |
| Walk Forward Validation no mencionado | ✅ Implementado |
| Reliability Curve no mencionada | ✅ Implementada |

## Resumen de acciones correctivas

1. Actualizar cifras (27 features, 92 equipos, 4 categorías)
2. Reemplazar términos absolutos por lenguaje probabilístico
3. Agregar secciones: Metodología, Validación, Limitaciones
4. Documentar ELO, SHAP, backtesting, decaimiento temporal
5. Ser honesto sobre los feature toggles UI-only
6. Agregar shap a requirements.txt
7. Agregar sección de Estado Actual del Proyecto
8. Incluir métricas reales del backtesting
