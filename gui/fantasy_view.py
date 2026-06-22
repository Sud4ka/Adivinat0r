from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QScrollArea, QTextEdit, QSlider, QGridLayout, QSpinBox
)
from PyQt6.QtCore import Qt
from gui.theme import (
    NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_GREEN, NEON_AMBER,
    BG_CARD, TEXT_SECONDARY, TEXT_PRIMARY, BORDER, neon_label
)
from engine.translate import UI_ES


class FantasyScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.budget = 100.0
        self.squad = []
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

        title = QLabel(neon_label(UI_ES["fan_title"], NEON_AMBER, 22))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:12px;">'
            f'{UI_ES["fan_desc"]}</span>'
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        budget_group = QGroupBox(UI_ES["fan_budget"])
        budget_layout = QHBoxLayout(budget_group)
        self.budget_label = QLabel(
            f'<span style="color:{NEON_AMBER};font-size:22px;font-weight:bold;">${self.budget:.1f}M</span>'
        )
        budget_layout.addWidget(self.budget_label)
        budget_layout.addStretch()
        layout.addWidget(budget_group)

        roster = QGroupBox(UI_ES["fan_squad"])
        roster_layout = QVBoxLayout(roster)
        self.roster_text = QTextEdit()
        self.roster_text.setReadOnly(True)
        self.roster_text.setStyleSheet(
            f"background:{BG_CARD};color:{TEXT_PRIMARY};border:1px solid {BORDER};"
            f"font-size:12px;padding:8px;"
        )
        self.roster_text.setMaximumHeight(180)
        roster_layout.addWidget(self.roster_text)

        sim = QPushButton(UI_ES["fan_simulate"])
        sim.setMinimumHeight(40)
        sim.setStyleSheet(
            f"QPushButton{{background:{NEON_PURPLE};color:{TEXT_PRIMARY};"
            f"border:2px solid {NEON_PURPLE};font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{NEON_GREEN};border:2px solid {NEON_GREEN};}}"
        )
        sim.clicked.connect(self.simulate_fantasy)
        roster_layout.addWidget(sim)
        layout.addWidget(roster)

        results = QGroupBox(UI_ES["fan_results"])
        results_layout = QVBoxLayout(results)
        self.results_label = QLabel(UI_ES["fan_no_team"])
        self.results_label.setStyleSheet(f"color:{TEXT_SECONDARY};font-size:12px;")
        self.results_label.setWordWrap(True)
        results_layout.addWidget(self.results_label)

        points = QGroupBox(UI_ES["fan_points"])
        points_layout = QVBoxLayout(points)
        self.points_text = QTextEdit()
        self.points_text.setReadOnly(True)
        self.points_text.setStyleSheet(
            f"background:{BG_CARD};color:{NEON_CYAN};border:1px solid {BORDER};"
            f"font-size:11px;padding:8px;"
        )
        self.points_text.setMaximumHeight(150)
        points_layout.addWidget(self.points_text)
        layout.addWidget(results)
        layout.addWidget(points)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def simulate_fantasy(self):
        import random
        players = [
            ("Messi", "Argentina", 45), ("C. Ronaldo", "Portugal", 40),
            ("Mbappé", "Francia", 38), ("Haaland", "Noruega", 35),
            ("Vinícius Jr.", "Brasil", 32), ("Bellingham", "Inglaterra", 30),
            ("De Bruyne", "Bélgica", 28), ("Salah", "Egipto", 26),
            ("Musiala", "Alemania", 24), ("Yamal", "España", 22),
            ("Wirtz", "Alemania", 20), ("Kvaratskhelia", "Georgia", 18),
            ("Gyökeres", "Suecia", 18), ("Palmer", "Inglaterra", 16),
            ("Doku", "Bélgica", 14), ("Szoboszlai", "Hungría", 12),
        ]
        random.shuffle(players)

        total = 0
        picks = []
        for name, country, value in players:
            if total + value <= self.budget:
                picks.append((name, country, value))
                total += value

        self.squad = picks
        self.budget_label.setText(
            f'<span style="color:{NEON_AMBER};font-size:22px;font-weight:bold;">'
            f"${self.budget - total:.1f}M</span>"
        )

        roster_html = "<br>".join(
            f"{i+1}. <b>{name}</b> ({country}) — ${value}M"
            for i, (name, country, value) in enumerate(picks)
        )
        self.roster_text.setHtml(
            f'<span style="color:{NEON_PINK};">{UI_ES["fan_squad_size"]}: {len(picks)}</span><br>{roster_html}'
        )

        sim_pts = {name: random.randint(10, 80) + random.randint(-5, 5) for name, _, _ in picks}
        total_pts = sum(sim_pts.values())
        rankings = sorted(sim_pts.items(), key=lambda x: -x[1])

        self.results_label.setText(
            f'<span style="color:{NEON_GREEN};font-size:16px;font-weight:bold;">'
            f"{UI_ES['fan_sim_done']}: {total_pts} {UI_ES['fan_points']}</span>"
        )

        pts_html = "<br>".join(
            f"{i+1}. {name}: {pts} pts"
            for i, (name, pts) in enumerate(rankings)
        )
        self.points_text.append(
            f"📊 {UI_ES['fan_results']}\n{'─' * 30}\n{pts_html}"
        )
