from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QProgressBar, QTabWidget
)
from PyQt6.QtCore import Qt
from gui.theme import (
    NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_GREEN, NEON_AMBER,
    BG, BG_CARD, TEXT_SECONDARY, TEXT_PRIMARY, BORDER, neon_label
)
from engine.simulator import TournamentSimulator
from engine.stats import load_fixtures_2026, load_teams
from engine.translate import team_es, stage_es, get_team_list_es, UI_ES


class SimulatorScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fixtures = load_fixtures_2026()
        self.teams = load_teams()
        self.simulator = TournamentSimulator()
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

        title = QLabel(neon_label(UI_ES["sim_title"], NEON_GREEN, 22))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:12px;">'
            f'{UI_ES["sim_desc"]}</span>'
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        sim_group = QGroupBox(UI_ES["sim_config"])
        sim_layout = QVBoxLayout(sim_group)

        btn = QPushButton(UI_ES["sim_run"])
        btn.setMinimumHeight(44)
        btn.setStyleSheet(
            f"QPushButton{{background:{NEON_GREEN};color:{BG};"
            f"border:2px solid {NEON_GREEN};font-size:14px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{NEON_CYAN};border:2px solid {NEON_CYAN};color:{BG};}}"
        )
        btn.clicked.connect(self.run_simulation)
        sim_layout.addWidget(btn)

        self.sim_progress = QProgressBar()
        self.sim_progress.setMinimum(0)
        self.sim_progress.setMaximum(100)
        self.sim_progress.setTextVisible(True)
        self.sim_progress.setMinimumHeight(24)
        self.sim_progress.setStyleSheet(
            f"QProgressBar{{background:{BG_CARD};border:1px solid {BORDER};"
            f"text-align:center;color:{TEXT_PRIMARY};font-size:11px;}}"
            f"QProgressBar::chunk{{background:{NEON_CYAN};}}"
        )
        sim_layout.addWidget(self.sim_progress)
        layout.addWidget(sim_group)

        results_tabs = QTabWidget()
        results_tabs.setStyleSheet(
            f"QTabWidget::pane{{background:{BG_CARD};border:1px solid {BORDER};}}"
            f"QTabBar::tab{{background:#1a1a28;color:{TEXT_SECONDARY};padding:8px 16px;"
            f"border:1px solid {BORDER};font-size:11px;}}"
            f"QTabBar::tab:selected{{background:{NEON_PURPLE}30;color:{NEON_CYAN};"
            f"border-bottom:2px solid {NEON_CYAN};}}"
        )

        self.group_results_tab = QWidget()
        self.init_group_results()
        results_tabs.addTab(self.group_results_tab, UI_ES["sim_groups"])

        self.knockout_results_tab = QWidget()
        self.init_knockout_results()
        results_tabs.addTab(self.knockout_results_tab, UI_ES["sim_knockout"])

        self.stats_tab = QWidget()
        self.init_stats()
        results_tabs.addTab(self.stats_tab, UI_ES["sim_stats"])

        layout.addWidget(results_tabs)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def run_simulation(self):
        self.sim_progress.setValue(10)
        result = self.simulator.run_full_simulation()
        self.sim_progress.setValue(100)

        self.populate_group_results(result.get("standings", {}))
        self.populate_knockout_results(result.get("bracket", {}))
        self.populate_stats(result)

    def init_group_results(self):
        layout = QVBoxLayout(self.group_results_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        self.group_table = QTableWidget()
        self.group_table.setColumnCount(5)
        self.group_table.setHorizontalHeaderLabels([
            UI_ES["sim_group"], UI_ES["sim_1st"], UI_ES["sim_2nd"],
            UI_ES["sim_3rd"], UI_ES["sim_4th"]
        ])
        self.group_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.group_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.group_table.setAlternatingRowColors(True)
        self.group_table.setStyleSheet(
            f"QTableWidget{{background:{BG_CARD};color:{TEXT_PRIMARY};"
            f"border:1px solid {BORDER};font-size:11px;}}"
            f"QHeaderView::section{{background:#1a1a28;color:{NEON_CYAN};"
            f"border:1px solid {BORDER};padding:4px;}}"
            f"QTableWidget::item{{padding:4px;}}"
        )
        layout.addWidget(self.group_table)

    def init_knockout_results(self):
        layout = QVBoxLayout(self.knockout_results_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        self.knockout_table = QTableWidget()
        self.knockout_table.setColumnCount(3)
        self.knockout_table.setHorizontalHeaderLabels([
            UI_ES["sim_phase"], UI_ES["sim_fixture"], UI_ES["sim_result"]
        ])
        self.knockout_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.knockout_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.knockout_table.setAlternatingRowColors(True)
        self.knockout_table.setStyleSheet(
            f"QTableWidget{{background:{BG_CARD};color:{TEXT_PRIMARY};"
            f"border:1px solid {BORDER};font-size:11px;}}"
            f"QHeaderView::section{{background:#1a1a28;color:{NEON_CYAN};"
            f"border:1px solid {BORDER};padding:4px;}}"
        )
        layout.addWidget(self.knockout_table)

    def init_stats(self):
        layout = QVBoxLayout(self.stats_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        self.stats_text = QLabel("Ejecutá una simulación para ver estadísticas.")
        self.stats_text.setStyleSheet(f"color:{TEXT_SECONDARY};font-size:12px;")
        self.stats_text.setWordWrap(True)
        layout.addWidget(self.stats_text)

    def populate_group_results(self, standings):
        groups = list(standings.keys())
        self.group_table.setRowCount(len(groups))
        for i, g_name in enumerate(sorted(groups)):
            sorted_data = standings[g_name]
            self.group_table.setItem(i, 0, QTableWidgetItem(f"Grupo {g_name}"))
            for j in range(4):
                if j < len(sorted_data):
                    team = sorted_data[j][0]
                    pts = sorted_data[j][1]
                    es_name = f"{team_es(team)} ({pts}p)"
                else:
                    es_name = "--"
                item = QTableWidgetItem(es_name)
                if j < 2:
                    item.setForeground(Qt.GlobalColor.cyan)
                self.group_table.setItem(i, j + 1, item)

    def populate_knockout_results(self, bracket):
        rows = []
        for phase_key, stage_name in [
            ("round_of_16", "Octavos"), ("quarter_finals", "Cuartos"),
            ("semi_finals", "Semifinales"), ("final", "Final")
        ]:
            matches = bracket.get(phase_key, [])
            if phase_key == "final":
                if isinstance(matches, dict):
                    rows.append((stage_name, f"{team_es(matches.get('team_a','?'))} vs {team_es(matches.get('team_b','?'))}",
                                 f"{matches.get('goals_a',0)}-{matches.get('goals_b',0)}"))
                continue
            for m in matches:
                ta, tb = m
                rows.append((stage_name, f"{team_es(ta)} vs {team_es(tb)}", "--"))

        self.knockout_table.setRowCount(len(rows))
        for i, (phase, fixture, result) in enumerate(rows):
            self.knockout_table.setItem(i, 0, QTableWidgetItem(phase))
            self.knockout_table.setItem(i, 1, QTableWidgetItem(fixture))
            self.knockout_table.setItem(i, 2, QTableWidgetItem(result))

    def populate_stats(self, result):
        champion = result.get("bracket", {}).get("champion", "?")
        standings = result.get("standings", {})
        total_points = sum(sum(t[1] for t in g) for g in standings.values())

        text = (
            f'<span style="color:{NEON_AMBER};font-size:16px;font-weight:bold;">'
            f"🏆 Campeón: {team_es(champion)}</span><br><br>"
            f'<span style="color:{NEON_CYAN};">• Grupos: {len(standings)}</span><br>'
            f'<span style="color:{NEON_CYAN};">• Puntos totales: {total_points}</span><br>'
            f'<span style="color:{NEON_CYAN};">• Eliminatorias completadas</span><br>'
        )

        self.stats_text.setText(text)
