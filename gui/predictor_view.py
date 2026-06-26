from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QProgressBar, QScrollArea, QGridLayout, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from gui.theme import (
    NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_AMBER, NEON_GREEN,
    BG, BG_CARD, TEXT_SECONDARY, TEXT_PRIMARY, BORDER, neon_label
)
from engine.stats import get_team_list, load_matches, load_teams
from engine.predictor import EnsemblePredictor
from engine.calibration import CalibrationTracker
from engine.translate import team_es, team_en, stage_es, get_team_list_es, UI_ES


class PredictorScreen(QWidget):
    update_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.predictor = EnsemblePredictor()
        self.team_list_en = get_team_list()
        self.team_list_es = get_team_list_es()
        self.teams = load_teams()
        self.df = load_matches()
        self.calibration = CalibrationTracker()
        self.feature_toggles = {
            "momentum": True, "environmental": True, "h2h_deep": True,
            "generation": True, "xg_historical": True, "fantasy": False,
        }
        self.concentracion_active = False
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(10)

        title = QLabel(neon_label(UI_ES["pred_title"], NEON_CYAN, 22))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            f'<span style="color:{TEXT_SECONDARY}; font-size:12px;">'
            f'{UI_ES["pred_desc"]}</span>'
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        sel_group = QGroupBox("Configuración del Partido")
        sel_layout = QVBoxLayout(sel_group)

        teams_row = QHBoxLayout()
        ta_l = QVBoxLayout()
        ta_l.addWidget(QLabel(
            f'<span style="color:{NEON_PINK};font-size:13px;font-weight:bold;">{UI_ES["pred_team_a"]}</span>'
        ))
        self.team_a = QComboBox()
        self.team_a.addItems(self.team_list_es)
        ta_l.addWidget(self.team_a)

        vs = QLabel(
            f'<span style="color:#8888a0;font-size:18px;font-weight:bold;">{UI_ES["pred_vs"]}</span>'
        )
        vs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs.setMaximumWidth(50)

        tb_l = QVBoxLayout()
        tb_l.addWidget(QLabel(
            f'<span style="color:{NEON_CYAN};font-size:13px;font-weight:bold;">{UI_ES["pred_team_b"]}</span>'
        ))
        self.team_b = QComboBox()
        self.team_b.addItems(self.team_list_es)
        tb_l.addWidget(self.team_b)

        idx_a = self.team_list_es.index(team_es("Argentina")) if team_es("Argentina") in self.team_list_es else 0
        idx_b = self.team_list_es.index(team_es("Algeria")) if team_es("Algeria") in self.team_list_es else min(1, len(self.team_list_es)-1)
        self.team_a.setCurrentIndex(idx_a)
        self.team_b.setCurrentIndex(idx_b)

        teams_row.addLayout(ta_l, 1)
        teams_row.addWidget(vs, 0)
        teams_row.addLayout(tb_l, 1)
        sel_layout.addLayout(teams_row)

        stage_row = QHBoxLayout()
        stage_row.addWidget(QLabel(f'<span style="color:{TEXT_PRIMARY};">{UI_ES["pred_stage"]}</span>'))
        self.stage_combo = QComboBox()
        stages_en = ["Group Stage", "Round of 16", "Quarter-finals", "Semi-finals", "Final", "Third place"]
        for s in stages_en:
            self.stage_combo.addItem(stage_es(s), s)
        stage_row.addWidget(self.stage_combo, 1)
        stage_row.addStretch()
        sel_layout.addLayout(stage_row)

        layout.addWidget(sel_group)

        toggle_group = QGroupBox(UI_ES["pred_feature_toggles"])
        toggle_grid = QGridLayout(toggle_group)
        toggle_grid.setSpacing(6)
        self.toggle_checks = {}
        features = [
            ("momentum", "Momentum Neural"),
            ("environmental", "Ambientales"),
            ("h2h_deep", "H2H Profundo"),
            ("generation", "Generaciones"),
            ("xg_historical", "xG Histórico"),
            ("fantasy", "Modo Fantasía"),
        ]
        for i, (key, label) in enumerate(features):
            cb = QCheckBox(label)
            cb.setChecked(self.feature_toggles.get(key, True))
            cb.toggled.connect(lambda checked, k=key: self._toggle_feature(k, checked))
            self.toggle_checks[key] = cb
            toggle_grid.addWidget(cb, i // 3, i % 3)
        layout.addWidget(toggle_group)

        action_row = QHBoxLayout()
        self.predict_btn = QPushButton(UI_ES["pred_run"])
        self.predict_btn.setMinimumHeight(44)
        self.predict_btn.setStyleSheet(
            f"QPushButton{{background:{NEON_PURPLE};color:{TEXT_PRIMARY};"
            f"border:2px solid {NEON_PURPLE};font-size:14px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{NEON_PINK};border:2px solid {NEON_PINK};}}"
        )
        self.predict_btn.clicked.connect(self.run_prediction)
        action_row.addWidget(self.predict_btn)

        self.concentracion_btn = QPushButton(UI_ES["pred_concentracion"])
        self.concentracion_btn.setMinimumHeight(44)
        self.concentracion_btn.setStyleSheet(
            f"QPushButton{{background:{NEON_PINK}22;color:{NEON_PINK};"
            f"border:2px solid {NEON_PINK};font-size:12px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{NEON_PINK};color:{BG};}}"
            f"QPushButton:checked{{background:{NEON_PINK};color:{BG};}}"
        )
        self.concentracion_btn.setCheckable(True)
        self.concentracion_btn.toggled.connect(self._toggle_concentracion)
        action_row.addWidget(self.concentracion_btn)

        self.update_data_btn = QPushButton("📡 ACTUALIZAR DATOS ESTADÍSTICOS")
        self.update_data_btn.setMinimumHeight(44)
        self.update_data_btn.setStyleSheet(
            f"QPushButton{{background:{NEON_GREEN}22;color:{NEON_GREEN};"
            f"border:2px solid {NEON_GREEN};font-size:12px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{NEON_GREEN};color:{BG};}}"
        )
        self.update_data_btn.clicked.connect(self._on_update_clicked)
        action_row.addWidget(self.update_data_btn)
        layout.addLayout(action_row)

        self.result_group = QGroupBox("Resultados de la Predicción")
        self.result_layout = QVBoxLayout(self.result_group)
        self.result_layout.setSpacing(8)

        self.score_label = QLabel(UI_ES["pred_score"])
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setStyleSheet(
            f"color:{NEON_CYAN}; font-size:20px; font-weight:bold; "
            f"font-family:'Orbitron','Courier New',monospace; "
            f"border:1px solid {BORDER}; border-radius:6px; padding:10px;"
        )
        self.result_layout.addWidget(self.score_label)

        bars = QVBoxLayout()
        self.prob_a_bar = QProgressBar()
        self.prob_draw_bar = QProgressBar()
        self.prob_b_bar = QProgressBar()
        for bar in [self.prob_a_bar, self.prob_draw_bar, self.prob_b_bar]:
            bar.setMinimum(0)
            bar.setMaximum(1000)
            bar.setTextVisible(False)
            bar.setMinimumHeight(22)

        self.prob_a_label = QLabel(f"{UI_ES['pred_team_a']}: 0%")
        self.prob_draw_label = QLabel(f"{UI_ES['pred_draw']}: 0%")
        self.prob_b_label = QLabel(f"{UI_ES['pred_team_b']}: 0%")
        for lbl in [self.prob_a_label, self.prob_draw_label, self.prob_b_label]:
            lbl.setStyleSheet("font-family:'Orbitron','Courier New',monospace; font-size:13px;")

        bars.addWidget(self.prob_a_label)
        bars.addWidget(self.prob_a_bar)
        bars.addWidget(self.prob_draw_label)
        bars.addWidget(self.prob_draw_bar)
        bars.addWidget(self.prob_b_label)
        bars.addWidget(self.prob_b_bar)
        self.result_layout.addLayout(bars)

        info_row = QHBoxLayout()

        factors_group = QGroupBox(UI_ES["pred_key_factors"])
        factors_layout = QVBoxLayout(factors_group)
        self.factors_label = QLabel("Ejecutá una predicción para ver los factores clave")
        self.factors_label.setStyleSheet(f"color:{TEXT_SECONDARY}; font-size:11px;")
        self.factors_label.setWordWrap(True)
        factors_layout.addWidget(self.factors_label)
        info_row.addWidget(factors_group, 1)

        model_group = QGroupBox(UI_ES["pred_active_model"])
        model_layout = QVBoxLayout(model_group)
        self.model_info = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:11px;">'
            "Algoritmo: Ensemble (LR + RF + GB)<br>"
            "Entrenamiento: -- muestras<br>"
            "Características: 31 activas<br>"
            "Calibración: --</span>"
        )
        self.model_info.setWordWrap(True)
        model_layout.addWidget(self.model_info)
        info_row.addWidget(model_group, 1)

        self.result_layout.addLayout(info_row)
        self.result_group.setVisible(False)
        layout.addWidget(self.result_group)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _on_update_clicked(self):
        self.update_data_btn.setText("ACTUALIZANDO...")
        self.update_data_btn.setEnabled(False)
        self.update_requested.emit()

    def _toggle_feature(self, key, checked):
        self.feature_toggles[key] = checked

    def _toggle_concentracion(self, checked):
        self.concentracion_active = checked
        text = UI_ES["pred_concentracion_on"] if checked else UI_ES["pred_concentracion"]
        self.concentracion_btn.setText(text)

    def on_update_complete(self, success, msg):
        self.update_data_btn.setText("📡 ACTUALIZAR DATOS ESTADÍSTICOS")
        self.update_data_btn.setEnabled(True)
        if success:
            self.model_info.setText(
                f'<span style="color:{TEXT_SECONDARY};font-size:11px;">'
                f"Modelo reentrenado con datos del Mundial 2026</span>"
            )

    def run_prediction(self):
        ta_es = self.team_a.currentText()
        tb_es = self.team_b.currentText()
        ta = team_en(ta_es)
        tb = team_en(tb_es)
        stage_idx = self.stage_combo.currentIndex()
        stage = self.stage_combo.itemData(stage_idx)

        if ta == tb:
            return

        self.predict_btn.setText("PREDICIENDO...")
        self.predict_btn.setEnabled(False)

        try:
            result = self.predictor.predict_proba(ta, tb, stage)
        except Exception as e:
            self.score_label.setText(f"Error: {str(e)}")
            self.predict_btn.setText(UI_ES["pred_run"])
            self.predict_btn.setEnabled(True)
            self.result_group.setVisible(True)
            return

        win_a = result.get(f"{ta}_win", 0) * 100
        draw = result.get(f"{ta}_draw", 0) * 100
        win_b = result.get(f"{ta}_loss", 0) * 100
        scoreline = result.get("predicted_score", "0-0")

        self.prob_a_label.setText(f"{ta_es}: {win_a:.1f}%")
        self.prob_a_bar.setValue(int(win_a * 10))
        self.prob_a_bar.setStyleSheet(f"QProgressBar::chunk{{background:{NEON_PINK};}}")

        self.prob_draw_label.setText(f"{UI_ES['pred_draw']}: {draw:.1f}%")
        self.prob_draw_bar.setValue(int(draw * 10))
        self.prob_draw_bar.setStyleSheet(f"QProgressBar::chunk{{background:{NEON_PURPLE};}}")

        self.prob_b_label.setText(f"{tb_es}: {win_b:.1f}%")
        self.prob_b_bar.setValue(int(win_b * 10))
        self.prob_b_bar.setStyleSheet(f"QProgressBar::chunk{{background:{NEON_CYAN};}}")

        self.score_label.setText(f"Marcador: {ta_es} {scoreline} {tb_es}")

        try:
            from engine.live_data import load_2026_results
            _real = load_2026_results()
            _actual = None
            for _m in _real:
                if not _m.get("played") or _m.get("home_score") is None:
                    continue
                if (_m["home"] == ta and _m["away"] == tb) or (_m["home"] == tb and _m["away"] == ta):
                    hs, aw = _m["home_score"], _m["away_score"]
                    if ta == _m["home"]:
                        _actual = "team_a" if hs > aw else ("draw" if hs == aw else "team_b")
                    else:
                        _actual = "team_b" if hs > aw else ("draw" if hs == aw else "team_a")
                    break
            if _actual:
                self.calibration.log_prediction(ta, tb, stage, win_a / 100.0, draw / 100.0, win_b / 100.0, _actual)
        except Exception:
            pass

        from PyQt6.QtCore import QThread, pyqtSignal

        class ShapWorker(QThread):
            result_ready = pyqtSignal(str)

            def __init__(self, predictor, ta, tb, stage, ta_es, tb_es, win_a, draw, win_b):
                super().__init__()
                self.predictor = predictor
                self.ta = ta
                self.tb = tb
                self.stage = stage
                self.ta_es = ta_es
                self.tb_es = tb_es
                self.win_a = win_a
                self.draw = draw
                self.win_b = win_b

            def run(self):
                try:
                    from engine.stats import FEATURE_NAMES, load_matches, build_feature_vector
                    df = load_matches()
                    fv = build_feature_vector(df, self.ta, self.tb, self.stage)
                    from engine.explainability import explain_prediction
                    if hasattr(self.predictor, 'model') and hasattr(self.predictor, 'scaler'):
                        explanation = explain_prediction(self.predictor.model, self.predictor.scaler, fv)
                        if "error" not in explanation:
                            top_class = 0 if self.win_a > max(self.draw, self.win_b) else (1 if self.draw > self.win_b else 2)
                            class_label = {0: self.ta_es, 1: "Empate", 2: self.tb_es}.get(top_class, self.ta_es)
                            pos = explanation.get(top_class, {}).get("top_positive", [])
                            neg = explanation.get(top_class, {}).get("top_negative", [])
                            lines = [f"Factores a favor de {class_label}:"]
                            for name, val in pos[:3]:
                                lines.append(f"  + {name}: {val:+.3f}")
                            if neg:
                                lines.append(f"Factores en contra:")
                                for name, val in neg[:3]:
                                    lines.append(f"  - {name}: {val:+.3f}")
                            factors_text = "<br>".join(lines)
                        else:
                            factors_text = explanation["error"]
                    else:
                        factors_text = "SHAP no disponible para este predictor"
                except Exception:
                    factors_text = "SHAP no disponible"
                self.result_ready.emit(factors_text)

        self._shap_worker = ShapWorker(
            self.predictor, ta, tb, stage, ta_es, tb_es, win_a, draw, win_b
        )
        self._shap_worker.result_ready.connect(self._on_shap_ready)
        self._shap_worker.start()

        self.factors_label.setText("Calculando factores SHAP...")

        brier = self.calibration.get_brier_score()
        acc = self.calibration.get_accuracy()
        logloss = self.calibration.get_log_loss()
        ece = self.calibration.get_ece()
        n_matches = len(self.df)
        self.model_info.setText(
            f'<span style="color:{TEXT_SECONDARY};font-size:11px;">'
            f"Algoritmo: Ensemble (LR + RF + GB)<br>"
            f"Entrenamiento: {n_matches} muestras<br>"
            f"Características: 31<br>"
            f"Precisión: {acc}%  |  Brier: {brier:.3f}<br>"
            f"Log Loss: {logloss:.3f}  |  ECE: {ece:.3f}</span>"
        )

        self.result_group.setVisible(True)
        self.predict_btn.setText(UI_ES["pred_run"])
        self.predict_btn.setEnabled(True)

    def _on_shap_ready(self, factors_text):
        self.factors_label.setText(factors_text)
