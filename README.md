# ⚽ ADIVINAT0R — Motor de Simulación y Análisis Probabilístico del Mundial 2026

![Python](https://img.shields.io/badge/Python-3.11%2B-00ffe1?style=flat&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-ff2079?style=flat)
![scikit--learn](https://img.shields.io/badge/scikit--learn-1.3%2B-7b2ff7?style=flat)
![License](https://img.shields.io/badge/license-MIT-00ff88?style=flat)

**ADIVINAT0R** es una aplicación de escritorio con temática **cyberpunk** que analiza probabilísticamente los partidos de la Copa del Mundo 2026 mediante un **Ensemble VotingClassifier** (LR + Random Forest 200 + Gradient Boosting 150) entrenado sobre **31 features** extraídas de datos históricos (1930–2022), sistema de rating **ELO dinámico**, **Power Rankings** desde la API Fantasy de FIFA, factores de **momentum** y **ambiente** (altitud/clima), y un modelo **Poisson bivariado (Dixon-Coles)** para simular marcadores.

La interfaz gráfica está completamente en español con banderas para los 48 equipos clasificados, resultados en vivo desde la API oficial de FIFA y actualización automática de datos estadísticos.

> **Nota importante**: ADIVINAT0R no predice resultados con certeza. El sistema estima probabilidades y simula escenarios utilizando datos históricos, métricas actuales y modelos estadísticos. Las probabilidades mostradas representan escenarios plausibles según la información disponible y no constituyen garantías de resultado.

---

## 📋 Estado Actual del Proyecto

### Funcionalidades implementadas

| Componente | Estado |
|:-----------|:-------|
| Ensemble VotingClassifier (LR + RF 200 + GB 150) | ✅ Estable |
| 31 features en 5 categorías (históricas, ELO, player power, forma 2026, momentum/ambiente) | ✅ Estable |
| Sistema ELO dinámico (K variable según fase) | ✅ Estable |
| Decaimiento temporal (0.94^años) | ✅ Estable |
| Modelo Poisson/Dixon-Coles con correlación τ | ✅ Estable |
| Walk Forward Validation (1930–2014→2018, 1930–2018→2022) | ✅ Estable |
| SHAP explainability (factores por predicción) | ✅ Estable |
| Calibration metrics (ECE, Log Loss, Brier, Reliability Curve) | ✅ Estable |
| Power Rankings vía API Fantasy FIFA | ✅ Estable |
| Resultados en vivo vía API Calendar FIFA | ✅ Estable |
| Simulador Monte Carlo del torneo (paralelizado, 10K sims en ~46s) | ✅ Estable |
| H2H histórico | ✅ Estable |
| Generaciones legendarias | ✅ Estable |
| Módulo Fantasía | ✅ Experimental |
| Scraping Wikipedia para datos históricos | ✅ Estable |

### Funcionalidades UI-only (interfaz preparada para expansión)

| Toggle | Descripción |
|:-------|:------------|
| H2H Profundo | Interfaz preparada — usa H2H básico actualmente |
| xG Histórico | Interfaz preparada — sin datos de xG disponibles |
| Modo Fantasía | Interfaz preparada — no afecta predicciones |

### Funcionalidades integradas al modelo (v2.2.0)

| Módulo | Estado |
|:-------|:-------|
| Momentum Neural | ✅ Integrado en feature vector (momentum_a, momentum_b, momentum_diff) |
| Ambientales | ✅ Integrado en feature vector (env_score: altitud, clima, fatiga) |

### Fuentes de datos

1. **Partidos históricos**: Dataset FIFA World Cup (Kaggle) — 967 partidos, 1930–2022
2. **Resultados 2026**: API oficial FIFA (`api.fifa.com/v3/calendar/matches`)
3. **Power Rankings**: API Fantasy FIFA (`play.fifa.com`) — ~1500 jugadores
4. **Player Power**: Puntaje promedio por equipo desde Fantasy API
5. **Estadísticas de selecciones**: Wikipedia + datos curados (92 equipos)

---

## 🚀 Instalación y uso

### Requisitos

- Python 3.11 o superior
- pip

### Instalación

```bash
git clone https://github.com/tuusuario/adivinat0r.git
cd adivinat0r
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Ejecutar

```bash
python main.py
```

La aplicación entrena el modelo, conecta con las APIs de FIFA y muestra la interfaz.

---

## 🧠 Metodología

### Ensemble VotingClassifier

El modelo central es un ensamble de tres clasificadores combinados por **voto blando** (soft voting):

| Componente | Hiperparámetros | Peso en voto |
|:-----------|:----------------|:-------------|
| Logistic Regression | max_iter=1000, solver=lbfgs, class_weight=balanced | 1 |
| Random Forest | 200 árboles, max_depth=6, class_weight=balanced | 2 |
| Gradient Boosting | 150 árboles, max_depth=4, learning_rate=0.05 | 2 |

### Features (31 dimensiones)

| Categoría | Features | Descripción |
|:----------|:---------|:------------|
| 📊 **Históricas** (16) | H2H ratios, promedio goles, win rate, coeficiente fase, ranking delta, ventaja continente, ataque/creatividad/defensa diff | Extraídas del dataset histórico con filtro temporal (solo datos anteriores al partido) |
| ⚡ **ELO dinámico** (3) | elo_a, elo_b, elo_diff | Rating ELO internacional con K=32 mundial, K=24 eliminatorias, K=16 amistosos |
| 🪄 **Player Power** (3) | pp_a, pp_b, pp_diff | Puntaje promedio de jugadores por equipo desde Fantasy FIFA API |
| 🔴 **Forma 2026** (5) | Diferenciales de goles, win rate, ppg, goal difference | Calculados desde resultados reales del torneo en curso |
| 🔥 **Momentum** (3) | momentum_a, momentum_b, momentum_diff | Tendencia de rendimiento en los últimos 3 mundiales ponderada por recencia |
| 🌍 **Ambiente** (1) | env_score | Factor compuesto por altitud (0.3), clima (0.25), descanso (0.25) y viaje (0.2) |

### Decaimiento temporal

Los partidos más recientes tienen mayor peso en el entrenamiento mediante un factor de decaimiento exponencial:
```
weight = 0.94 ^ años_desde_2022
```

Rango: 0.0034 (1930) a 1.0 (2022). Un partido de 2022 pesa ~2.4× más que uno de 1930.

Además, los pesos se ajustan por frecuencia de clase para compensar el desbalance (60.6% local, 22.6% empate, 16.8% visita).

### Sistema ELO dinámico

El rating ELO se computa cronológicamente partido a partido durante el entrenamiento, evitando data leakage. Se actualiza tras cada partido y las features reflejan el rating inmediatamente anterior al encuentro.

```python
Δ = K × margin_weight × (resultado_real - resultado_esperado)
```

- **K=32**: Mundiales
- **K=24**: Eliminatorias
- **K=16**: Amistosos (no aplica — dataset solo contiene mundiales)
- **margin_weight**: 1.0 + (goles_diferencia - 1) × 0.1 para victorias por más de 1 gol

### Modelo Poisson / Dixon-Coles

Para estimar marcadores probables se utiliza un modelo de goles con dependencia:

```python
P(X=x, Y=y) = Poisson(x, λ_A) × Poisson(y, λ_B) × τ(x, y)
```

Donde λ_A = ataque_A × defensa_B × league_avg y τ es el factor de correlación de Dixon-Coles que ajusta para resultados de pocos goles (0-0, 0-1, 1-0, 1-1) donde los modelos Poisson independientes suelen fallar.

---

## 📊 Validación

### Walk Forward Validation

El modelo se evalúa con validación temporal que respeta la estructura secuencial de los datos:

| Ventana de entrenamiento | Evaluación | Accuracy | Brier Score (multi-clase) | Log Loss |
|:-------------------------|:-----------|:---------|:--------------------------|:---------|
| 1930–2014 (903 partidos) | 2018 (64) | 48.44% | 0.640 | 1.060 |
| 1930–2018 (935 partidos) | 2022 (64) | 56.25% | 0.577 | 0.974 |

**Nota**: Una línea base aleatoria para 3 clases equiprobables produce Brier ≈ 0.667 y Log Loss ≈ 1.099.

### Métricas de calibración

| Métrica | Propósito |
|:--------|:----------|
| **Brier Score** | Error cuadrático medio entre probabilidades predichas y resultados |
| **Log Loss** | Penalización logarítmica por confianza en predicciones incorrectas |
| **ECE** (Expected Calibration Error) | Diferencia media entre confianza y precisión por bin |
| **Reliability Curve** | Gráfico de confianza vs precisión por decil |

---

## 🔍 Interpretabilidad (SHAP)

Cada predicción incluye un análisis de factores contribuyentes utilizando **SHAP KernelExplainer** ejecutado en un hilo secundario para no bloquear la interfaz. El background de 80 muestras se cachea entre predicciones.

```
Factores a favor de Argentina:
  + elo_diff: +0.0385
  + stats_b_win_rate: -0.0621  (baja tasa del rival ayuda)
  ...
Factores en contra:
  - ranking_delta: -0.0817
  ...
```

Esto permite entender qué features influyeron en cada decisión del modelo, proporcionando transparencia al resultado probabilístico.

---

## 🖥️ Pantallas de la aplicación

### 🏠 INICIO
Tabla de posiciones en vivo con banderas, puntos, GF, GC, DG. Indicador EN VIVO.

### 🗺️ MAPA
Resultados reales del Mundial 2026 con tabla de posiciones actualizada desde API FIFA.

### 🔮 PREDICTOR
Selección de equipos, fase, cálculo de probabilidades con barras, marcador estimado vía Dixon-Coles, factores SHAP (en hilo secundario sin bloquear la UI), y actualización de datos estadísticos. Usa **EnsemblePredictor** (LR + RF + GB con soft voting).

### 🏆 ESTADÍSTICAS
Perfil histórico completo de 92 selecciones: apariciones, partidos, rendimiento, títulos.

### 🤜🤛 H2H
Enfrentamiento histórico entre dos selecciones con estadísticas cara a cara.

### 👑 GENERACIONES
Exploración de generaciones legendarias (Brasil 1970, Argentina 1986, etc.).

### 🎲 SIMULADOR
Simulación Monte Carlo del torneo completo: fase de grupos + eliminatorias. Precomputa 1,128 probabilidades pairwise y ejecuta 10,000 simulaciones en paralelo (~46s total).

### 📈 CALIBRACIÓN
Brier Score, Log Loss, ECE, Reliability Curve del modelo en datos reales.

### 🎮 FANTASÍA
Armado de plantel con $100M y simulación de puntaje Fantasy.

---

## 🪄 FIFA Power Rankings

ADIVINAT0R integra el sistema de FIFA Power Rankings evaluando jugadores en 3 dimensiones:

| Dimensión | Fuente |
|:----------|:-------|
| ⚔️ **Ataque** | Puntaje promedio de delanteros (FWD) |
| 🎨 **Creatividad** | Puntaje promedio de mediocampistas (MID) |
| 🛡️ **Defensa** | Puntaje promedio de defensas y arqueros (DEF/GK) |

Los datos se obtienen de la API Fantasy de FIFA (~1500 jugadores). Equipos sin datos reciben valores por defecto basados en el promedio continental.

---

## 🎨 Temática Cyberpunk

```
🎨 Paleta de colores
   Fondo:        #0a0a0f
   Superficie:   #0d0d1a
   Bordes:       #1a2a3a
   Celeste:      #00ffe1  (señal positiva, Equipo B)
   Rosa:         #ff2079  (alertas, Equipo A, hosts)
   Ámbar:        #f7c750  (advertencias)
   Verde:        #00ff88  (indicador EN VIVO)
   Púrpura:      #7b2ff7  (empates, acentos)

🔤 Fuentes
   Títulos:      Orbitron
   Cuerpo:       Share Tech Mono / Courier New
```

---

## 📁 Estructura del proyecto

```
adivinat0r/
├── main.py                    # Punto de entrada
├── requirements.txt           # Dependencias
├── AUDIT_REPORT.md            # Auditoría técnica
├── README_AUDIT.md            # Auditoría de documentación
├── CHANGELOG_AI.md            # Registro de cambios
├── data/
│   ├── worldcups.csv          # 967 partidos históricos (1930–2022)
│   ├── teams.json             # Estadísticas de 92 selecciones
│   ├── fixtures_2026.json     # Grupos del Mundial 2026
│   ├── real_results.json      # Resultados en vivo (caché API FIFA)
│   ├── elo_ratings.json       # Ratings ELO históricos
│   ├── backtest_results.json  # Resultados de validación temporal
│   ├── calibration_log.json   # Registro de calibración
│   ├── players_cache.json     # Datos de jugadores FIFA
│   ├── player_power.json      # Poder de jugadores por equipo
│   └── power_rankings.json    # Power Rankings (ataque/creatividad/defensa)
├── engine/
│   ├── stats.py               # Ingeniería de 31 features + caché global + factores ataque/defensa
│   ├── predictor.py            # Ensemble VotingClassifier (LR+RF+GB) con soft voting
│   ├── poisson.py              # Modelo Dixon-Coles con correlación τ
│   ├── elo.py                  # Sistema de rating ELO dinámico
│   ├── backtesting.py          # Walk Forward Validation (usa build_feature_vector de stats)
│   ├── explainability.py       # SHAP: factores por predicción (background cacheado)
│   ├── calibration_metrics.py  # ECE, Reliability Curve, Brier desglosado
│   ├── calibration.py          # Tracking de precisión en tiempo real
│   ├── montecarlo.py           # Simulador Monte Carlo paralelizado (ThreadPoolExecutor)
│   ├── live_data.py            # Forma actual 2026 (5 features en vivo)
│   ├── worldcup_api.py         # API FIFA: resultados + Power Rankings
│   ├── momentum.py             # Tracker de momentum (integrado al feature vector)
│   ├── environment.py          # Factor ambiental: altitud, clima, viaje (integrado)
│   ├── h2h.py                  # Análisis Head-to-Head
│   ├── simulator.py            # Simulador de torneo (single-run)
│   ├── generations.py          # Generaciones legendarias
│   ├── alerts.py               # Sistema de notificaciones
│   ├── translate.py            # Traducción inglés↔español + banderas
│   └── datascraper.py          # Scraper de Wikipedia
└── gui/
    ├── theme.py               # Estilos cyberpunk
    ├── home.py                # Tabla de posiciones
    ├── mapa_view.py           # Resultados reales del mundial
    ├── predictor_view.py      # Pantalla de predicción
    ├── team_stats_view.py     # Estadísticas por equipo
    ├── h2h_view.py            # Pantalla H2H
    ├── generations_view.py    # Generaciones legendarias
    ├── simulator_view.py      # Simulador de torneo
    ├── calibration_view.py    # Calibración y precisión
    ├── fantasy_view.py        # Modo Fantasía
    └── alerts_dialog.py       # Pop-up de próximos partidos
```

---

## 📦 Dependencias

| Paquete | Versión | Propósito |
|:--------|:--------|:----------|
| PyQt6 | ≥6.5 | Interfaz gráfica |
| pandas | ≥2.0 | Manipulación de datos |
| scikit-learn | ≥1.3 | Ensemble VotingClassifier |
| joblib | ≥1.3 | Persistencia del modelo |
| matplotlib | ≥3.7 | Gráficos |
| numpy | ≥1.24 | Cómputo numérico |
| scipy | ≥1.11 | Estadística (Poisson, Dixon-Coles) |
| shap | ≥0.40 | Explicabilidad SHAP |
| beautifulsoup4 | ≥4.12 | Scraping Wikipedia |
| requests | ≥2.31 | HTTP |
| plyer | ≥2.1 | Notificaciones de escritorio |

---

## ⚠️ Limitaciones

1. **Incertidumbre inherente**: El fútbol tiene alta varianza. Lesiones, arbitraje, clima y eventos aleatorios afectan los resultados. Ningún modelo puede garantizar predicciones correctas.

2. **Datos limitados**: El dataset contiene 967 partidos de 22 torneos. Para aprendizaje automático, es un conjunto pequeño. Las estimaciones tienen intervalos de confianza amplios.

3. **Solo Mundiales**: El modelo solo se entrena con partidos de Copas del Mundo. No incluye eliminatorias, amistosos ni torneos continentales. Esto limita la cantidad de datos por equipo.

4. **Features estáticas**: Los Power Rankings y Player Power se obtienen de la API Fantasy de FIFA y reflejan el estado actual de los planteles, no su valor histórico. Equipos históricos pueden tener datos incompletos.

5. **Simetría temporal limitada**: El backtesting muestra que el modelo tiene Accuracy 48–56% en ventanas temporales. Una línea base aleatoria sería 33%. El modelo supera al azar pero con margen moderado.

6. **Modelo Poisson simplificado**: El modelo Dixon-Coles implementado asume league_avg fijo (1.35 goles/partido) y τ constante. La versión original de Dixon-Coles estima estos parámetros por máxima verosimilitud.

7. **Dependencia de APIs externas**: Los resultados en vivo y Power Rankings dependen de APIs de FIFA que pueden cambiar o estar caídas.

---

## 🔬 Recomendaciones futuras

- Implementar estimación de parámetros Dixon-Coles por máxima verosimilitud
- Incorporar datos de eliminatorias y amistosos para aumentar el dataset
- Agregar features de cuotas de apuestas como señal de mercado
- Implementar Platt Scaling o Temperature Scaling para mejorar calibración
- Agregar análisis de incertidumbre (intervalos de confianza en las probabilidades)
- Integrar módulo H2H profundo con estadísticas avanzadas de enfrentamientos
- Agregar datos históricos de xG (expected goals) si se consigue una fuente confiable

---

## 🧑‍💻 Contribuir

1. Hacé un fork del proyecto
2. Creá una rama (`git checkout -b feature/mi-idea`)
3. Comiteá tus cambios (`git commit -am 'Agrego mi idea'`)
4. Subí la rama (`git push origin feature/mi-idea`)
5. Abrí un Pull Request

---

## 📄 Licencia

MIT

---

<div align="center">
  <b>ADIVINAT0R</b> — Análisis probabilístico, no adivinación. 🤖⚽
</div>
