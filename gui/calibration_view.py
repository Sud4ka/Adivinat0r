from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt
from gui.theme import (
    NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_GREEN, NEON_AMBER, BG_CARD,
    TEXT_SECONDARY, TEXT_PRIMARY, BORDER, neon_label
)
from engine.calibration import CalibrationTracker
from engine.translate import UI_ES


class CalibrationScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.calibration = CalibrationTracker()
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
        layout.setSpacing(12)

        title = QLabel(neon_label(UI_ES["cal_title"], NEON_GREEN, 22))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:12px;">'
            f'{UI_ES["cal_desc"]}</span>'
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        metrics = QGroupBox(UI_ES["cal_metrics"])
        metrics_layout = QVBoxLayout(metrics)
        metrics_layout.setSpacing(10)

        def metric_row(label_text, prefix=""):
            row = QHBoxLayout()
            lbl = QLabel(f'<span style="color:{TEXT_PRIMARY};font-size:14px;">{label_text}</span>')
            val = QLabel("--")
            val.setStyleSheet(
                f"color:{NEON_CYAN};font-size:16px;font-weight:bold;"
                f"font-family:'Orbitron','Courier New',monospace;"
            )
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(1000)
            bar.setTextVisible(False)
            bar.setMinimumHeight(18)
            row.addWidget(lbl, 1)
            row.addWidget(val, 0)
            row.addWidget(bar, 2)
            metrics_layout.addLayout(row)
            return val, bar

        self.brier_val, self.brier_bar = metric_row(UI_ES["cal_brier"])
        self.acc_val, self.acc_bar = metric_row(UI_ES["cal_accuracy"])
        self.logloss_val, self.logloss_bar = metric_row(UI_ES["cal_logloss"])
        layout.addWidget(metrics)

        hist = QGroupBox(UI_ES["cal_histogram"])
        hist_layout = QVBoxLayout(hist)
        self.hist_label = QLabel(f'{UI_ES["cal_reliability"]}<br><br>Ejecutá predicciones para ver la calibración.')
        self.hist_label.setStyleSheet(f"color:{TEXT_SECONDARY};font-size:12px;padding:10px;")
        self.hist_label.setWordWrap(True)
        hist_layout.addWidget(self.hist_label)
        layout.addWidget(hist)

        details = QGroupBox(UI_ES["cal_details"])
        det_layout = QVBoxLayout(details)
        self.details_labels = {}
        details_info = [
            ("samples", "Muestras Calibradas"),
            ("recent", "Últimas 10 Predicciones"),
            ("overconfident", "Sobreconfianza"),
            ("underconfident", "Subconfianza"),
            ("trend", "Tendencia"),
        ]
        for key, label in details_info:
            lbl = QLabel(f'{label}: <span style="color:{NEON_PINK};">--</span>')
            lbl.setStyleSheet(f"color:{TEXT_SECONDARY};font-size:12px;padding:3px 0;")
            self.details_labels[key] = lbl
            det_layout.addWidget(lbl)
        layout.addWidget(details)

        btn = QPushButton(UI_ES["cal_refresh"])
        btn.setMinimumHeight(40)
        btn.setStyleSheet(
            f"QPushButton{{background:{NEON_PURPLE};color:{TEXT_PRIMARY};"
            f"border:2px solid {NEON_PURPLE};font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{NEON_GREEN};border:2px solid {NEON_GREEN};}}"
        )
        btn.clicked.connect(self.refresh)
        layout.addWidget(btn)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.refresh()

    def refresh(self):
        self.calibration.reload()
        brier = self.calibration.get_brier_score()
        acc = self.calibration.get_accuracy()
        recent = self.calibration.get_recent_predictions(10)
        by_stage = self.calibration.get_accuracy_by_stage()

        self.brier_val.setText(f"{brier:.3f}")
        self.brier_bar.setValue(max(0, min(1000, int((1 - brier) * 1000))))
        self.brier_bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{NEON_GREEN if brier < 0.2 else NEON_PURPLE};}}"
        )

        self.acc_val.setText(f"{acc:.1f}%")
        self.acc_bar.setValue(int(acc * 10))
        self.acc_bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{NEON_GREEN if acc > 60 else NEON_AMBER};}}"
        )

        logloss = self.calibration.get_log_loss()
        self.logloss_val.setText(f"{logloss:.3f}")
        self.logloss_bar.setValue(max(0, min(1000, int((1 - min(logloss, 1)) * 1000))))
        self.logloss_bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{NEON_CYAN};}}"
        )

        curve = self.calibration.get_reliability_curve()
        reliability_lines = []
        if curve:
            for b in curve:
                diff = b["accuracy"] - b["confidence"]
                icon = "✅" if abs(diff) < 0.05 else "⚠️" if diff > 0 else "❌"
                reliability_lines.append(
                    f"[{b['confidence']:.0%}]: acc={b['accuracy']:.0%} ({b['count']} muestras) {icon}"
                )
        if not reliability_lines:
            reliability_lines.append("Ejecutá predicciones para ver la calibración.")
        else:
            ece_val = self.calibration.get_ece()
            reliability_lines.insert(0, f"ECE: {ece_val:.4f} {'✅' if ece_val < 0.1 else '⚠️'}")
        self.hist_label.setText(
            f'{UI_ES["cal_reliability"]}<br><br>' + "<br>".join(reliability_lines)
        )

        sample_count = len(recent)
        self.details_labels["samples"].setText(
            f'Muestras Calibradas: <span style="color:{NEON_PINK};">{sample_count}</span>'
        )

        ece = self.calibration.get_ece()
        self.details_labels["overconfident"].setText(
            f'ECE: <span style="color:{NEON_PINK};">{ece:.4f}</span>'
        )

        curve = self.calibration.get_reliability_curve()
        if curve:
            text = "; ".join(f"{b['bin_center']:.1f}->{b['accuracy']:.2f}" for b in curve[:5])
            self.details_labels["underconfident"].setText(
                f'Curva Confiabilidad: <span style="color:{NEON_PINK};">{text}</span>'
            )
