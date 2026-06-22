from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QGroupBox,
    QGridLayout, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from gui.theme import (
    NEON_CYAN, NEON_PINK, NEON_PURPLE, BG_CARD, TEXT_SECONDARY,
    TEXT_PRIMARY, BORDER, neon_label
)
from engine.stats import load_teams, load_matches, compute_team_stats
from engine.translate import team_es, get_team_list_es, UI_ES


class TeamStatsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.teams = load_teams()
        self.df = load_matches()
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

        title = QLabel(neon_label(UI_ES["stats_title"], NEON_PURPLE, 22))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        selector_layout = QHBoxLayout()
        selector_label = QLabel(
            f'<span style="color:{TEXT_PRIMARY}; font-size:13px;">{UI_ES["stats_select"]}</span>'
        )
        self.team_combo = QComboBox()
        self.team_list_es = get_team_list_es()
        self.team_combo.addItems(self.team_list_es)
        self.team_combo.currentTextChanged.connect(self.update_stats)
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.team_combo, 1)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        self.stats_group = QGroupBox(UI_ES["stats_profile"])
        self.stats_grid = QGridLayout(self.stats_group)
        self.stats_grid.setSpacing(6)

        def tr(key):
            m = {
                "appearances": "Apariciones",
                "matches_played": "Partidos Jugados",
                "wins": "Victorias",
                "draws": "Empates",
                "losses": "Derrotas",
                "goals_for": "Goles a Favor",
                "goals_against": "Goles en Contra",
                "best_finish": "Mejor Resultado",
                "titles": "Títulos Mundiales",
                "continent": "Continente",
            }
            return m.get(key, key)

        self.labels = {}
        fields = [
            "appearances", "matches_played", "wins", "draws", "losses",
            "goals_for", "goals_against", "best_finish", "titles", "continent",
        ]
        for i, key in enumerate(fields):
            row, col = i // 2, i % 2
            name = QLabel(f'<span style="color:{TEXT_SECONDARY};font-size:11px;">{tr(key)}:</span>')
            val = QLabel("--")
            val.setStyleSheet(
                f"color:{NEON_CYAN}; font-size:14px; font-weight:bold; "
                f"background:{BG_CARD}; border:1px solid {BORDER}; "
                f"border-radius:4px; padding:5px 8px;"
            )
            self.labels[key] = val
            fl = QVBoxLayout()
            fl.setSpacing(2)
            fl.addWidget(name)
            fl.addWidget(val)
            self.stats_grid.addLayout(fl, row, col)
        self.stats_grid.setColumnStretch(0, 1)
        self.stats_grid.setColumnStretch(1, 1)
        layout.addWidget(self.stats_group)

        self.detailed_group = QGroupBox(UI_ES["stats_metrics"])
        self.detailed_layout = QVBoxLayout(self.detailed_group)
        self.avg_scored = QLabel("Prom. Goles a Favor por Partido: --")
        self.avg_conceded = QLabel("Prom. Goles en Contra por Partido: --")
        self.win_rate = QLabel("Porcentaje de Victorias: --")
        self.matches = QLabel("Partidos Analizados: --")
        for lbl in [self.avg_scored, self.avg_conceded, self.win_rate, self.matches]:
            lbl.setStyleSheet(f"color:{NEON_PINK}; font-size:13px; padding:3px 0;")
            self.detailed_layout.addWidget(lbl)
        layout.addWidget(self.detailed_group)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.update_stats()

    def update_stats(self):
        team_es_name = self.team_combo.currentText()
        from engine.translate import team_en
        team = team_en(team_es_name)
        if not team or team not in self.teams:
            return
        data = self.teams[team]
        for key, lbl in self.labels.items():
            lbl.setText(str(data.get(key, "--")))

        stats = compute_team_stats(self.df, team)
        self.avg_scored.setText(f"Prom. Goles a Favor por Partido: {stats['avg_goals_scored']:.2f}")
        self.avg_conceded.setText(f"Prom. Goles en Contra por Partido: {stats['avg_goals_conceded']:.2f}")
        self.win_rate.setText(f"Porcentaje de Victorias: {stats['win_rate'] * 100:.1f}%")
        self.matches.setText(f"Partidos Analizados: {stats['matches_analyzed']}")
