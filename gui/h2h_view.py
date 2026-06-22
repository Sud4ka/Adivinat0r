from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from gui.theme import (
    NEON_CYAN, NEON_PINK, NEON_PURPLE, BG_CARD, TEXT_SECONDARY,
    TEXT_PRIMARY, BORDER, neon_label
)
from engine.h2h import H2HAnalyzer as HeadToHeadAnalyzer
from engine.translate import team_es, stage_es, get_team_list_es, UI_ES


class H2HScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = HeadToHeadAnalyzer()
        self.team_list_es = get_team_list_es()
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

        title = QLabel(neon_label(UI_ES["h2h_title"], NEON_CYAN, 22))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:12px;">'
            f'{UI_ES["h2h_desc"]}</span>'
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        selector = QHBoxLayout()
        self.team_a = QComboBox()
        self.team_a.addItems(self.team_list_es)
        self.team_b = QComboBox()
        self.team_b.addItems(self.team_list_es)

        selector.addWidget(QLabel(f'<span style="color:{NEON_PINK};">{UI_ES["h2h_team_a"]}</span>'))
        selector.addWidget(self.team_a, 1)
        selector.addWidget(QLabel(f'<span style="color:#8888a0;">VS</span>'))
        selector.addWidget(QLabel(f'<span style="color:{NEON_CYAN};">{UI_ES["h2h_team_b"]}</span>'))
        selector.addWidget(self.team_b, 1)
        selector.addStretch()
        layout.addLayout(selector)

        btn = QPushButton(UI_ES["h2h_analyze"])
        btn.setMinimumHeight(40)
        btn.setStyleSheet(
            f"QPushButton{{background:{NEON_PURPLE};color:{TEXT_PRIMARY};"
            f"border:2px solid {NEON_PURPLE};font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{NEON_PINK};border:2px solid {NEON_PINK};}}"
        )
        btn.clicked.connect(self.analyze_h2h)
        layout.addWidget(btn)

        self.result_group = QGroupBox(f"{UI_ES['h2h_result']}")
        res_layout = QVBoxLayout(self.result_group)

        self.h2h_table = QTableWidget()
        self.h2h_table.setColumnCount(5)
        self.h2h_table.setHorizontalHeaderLabels([
            UI_ES["h2h_date"], UI_ES["h2h_tournament"],
            f"{UI_ES['h2h_team_a']}", f"{UI_ES['h2h_resultado']}",
            f"{UI_ES['h2h_team_b']}"
        ])
        self.h2h_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.h2h_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.h2h_table.setAlternatingRowColors(True)
        self.h2h_table.setStyleSheet(
            f"QTableWidget{{background:{BG_CARD};color:{TEXT_PRIMARY};"
            f"border:1px solid {BORDER};font-size:11px;}}"
            f"QHeaderView::section{{background:#1a1a28;color:{NEON_CYAN};"
            f"border:1px solid {BORDER};padding:4px;}}"
            f"QTableWidget::item{{padding:4px;}}"
        )
        res_layout.addWidget(self.h2h_table)

        metrics = QGroupBox(UI_ES["h2h_metrics"])
        metrics_layout = QVBoxLayout(metrics)
        self.total_label = QLabel(f"{UI_ES['h2h_total']}: 0")
        self.win_a_label = QLabel(f"{UI_ES['h2h_team_a']}: 0")
        self.win_b_label = QLabel(f"{UI_ES['h2h_team_b']}: 0")
        self.draws_label = QLabel(f"{UI_ES['h2h_draws']}: 0")
        self.pred_label = QLabel(f"{UI_ES['h2h_prediction']}: --")
        for lbl in [self.total_label, self.win_a_label, self.win_b_label, self.draws_label, self.pred_label]:
            lbl.setStyleSheet(f"color:{NEON_PINK};font-size:13px;padding:3px 0;")
            metrics_layout.addWidget(lbl)
        res_layout.addWidget(metrics)

        self.result_group.setVisible(False)
        layout.addWidget(self.result_group)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def analyze_h2h(self):
        from engine.translate import team_en
        ta = team_en(self.team_a.currentText())
        tb = team_en(self.team_b.currentText())

        data = self.analyzer.get_h2h(ta, tb)
        matches = data.get("matches", [])
        summary = data.get("summary", {})

        self.h2h_table.setRowCount(len(matches))
        for i, m in enumerate(matches):
            year = m.get("year", "")
            tournament = m.get("tournament", m.get("stage", ""))
            score_a = m.get("team_a_score", 0)
            score_b = m.get("team_b_score", 0)
            winner = m.get("winner", "")
            winner_es = team_es(winner) if winner != "Draw" else UI_ES["h2h_draws"]

            self.h2h_table.setItem(i, 0, QTableWidgetItem(str(year)))
            self.h2h_table.setItem(i, 1, QTableWidgetItem(tournament))
            self.h2h_table.setItem(i, 2, QTableWidgetItem(team_es(ta)))
            self.h2h_table.setItem(i, 3, QTableWidgetItem(f"{score_a}-{score_b}"))
            self.h2h_table.setItem(i, 4, QTableWidgetItem(team_es(tb)))

        total = summary.get("total_matches", 0)
        a_wins = summary.get("a_wins", 0)
        b_wins = summary.get("b_wins", 0)
        draws = summary.get("draws", 0)
        a_pct = summary.get("a_win_pct", 0)
        b_pct = summary.get("b_win_pct", 0)
        d_pct = summary.get("draw_pct", 0)
        a_avg = summary.get("a_avg_goals", 0)
        b_avg = summary.get("b_avg_goals", 0)

        self.total_label.setText(f"{UI_ES['h2h_total']}: {total}")
        self.win_a_label.setText(f"{team_es(ta)}: {a_wins} ({a_pct}%) — Prom. {a_avg} goles")
        self.win_b_label.setText(f"{team_es(tb)}: {b_wins} ({b_pct}%) — Prom. {b_avg} goles")
        self.draws_label.setText(f"{UI_ES['h2h_draws']}: {draws} ({d_pct}%)")

        if a_wins > b_wins:
            pred_team = team_es(ta)
            conf = a_wins / max(total, 1) * 100
        elif b_wins > a_wins:
            pred_team = team_es(tb)
            conf = b_wins / max(total, 1) * 100
        else:
            pred_team = UI_ES["h2h_draws"]
            conf = draws / max(total, 1) * 100
        self.pred_label.setText(f"{UI_ES['h2h_prediction']}: {pred_team} ({conf:.1f}%)")

        self.result_group.setVisible(True)
