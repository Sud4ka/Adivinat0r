from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QScrollArea, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt
from gui.theme import (
    NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_GREEN, BG_CARD,
    TEXT_SECONDARY, TEXT_PRIMARY, BORDER, neon_label
)
from engine.translate import team_es, team_en, get_team_list_es, UI_ES


class GenerationsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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

        title = QLabel(neon_label(UI_ES["gen_title"], NEON_PURPLE, 22))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:12px;">'
            f'{UI_ES["gen_desc"]}</span>'
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        selector = QHBoxLayout()
        selector.addWidget(QLabel(
            f'<span style="color:{TEXT_PRIMARY};">{UI_ES["gen_select"]}</span>'
        ))
        self.team_combo = QComboBox()
        self.team_combo.addItems(get_team_list_es())
        selector.addWidget(self.team_combo, 1)
        selector.addStretch()
        layout.addLayout(selector)

        analyze = QPushButton(UI_ES["gen_analyze"])
        analyze.setMinimumHeight(40)
        analyze.setStyleSheet(
            f"QPushButton{{background:{NEON_PURPLE};color:{TEXT_PRIMARY};"
            f"border:2px solid {NEON_PURPLE};font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{NEON_PINK};border:2px solid {NEON_PINK};}}"
        )
        analyze.clicked.connect(self.analyze_generation)
        layout.addWidget(analyze)

        result = QGroupBox(UI_ES["gen_analysis"])
        result_layout = QVBoxLayout(result)

        self.summary_label = QLabel(UI_ES["gen_select_team"])
        self.summary_label.setStyleSheet(f"color:{TEXT_SECONDARY};font-size:12px;")
        self.summary_label.setWordWrap(True)
        result_layout.addWidget(self.summary_label)

        self.generations_table = QTableWidget()
        self.generations_table.setColumnCount(4)
        self.generations_table.setHorizontalHeaderLabels([
            UI_ES["gen_generation"], UI_ES["gen_era"],
            UI_ES["gen_players"], UI_ES["gen_achievements"]
        ])
        self.generations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.generations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.generations_table.setStyleSheet(
            f"QTableWidget{{background:{BG_CARD};color:{TEXT_PRIMARY};"
            f"border:1px solid {BORDER};font-size:11px;}}"
            f"QHeaderView::section{{background:#1a1a28;color:{NEON_CYAN};"
            f"border:1px solid {BORDER};padding:4px;}}"
        )
        result_layout.addWidget(self.generations_table)
        layout.addWidget(result)

        trends = QGroupBox(UI_ES["gen_trends"])
        trends_layout = QVBoxLayout(trends)
        self.trends_text = QTextEdit()
        self.trends_text.setReadOnly(True)
        self.trends_text.setStyleSheet(
            f"background:{BG_CARD};color:{TEXT_PRIMARY};border:1px solid {BORDER};"
            f"font-size:11px;padding:8px;"
        )
        self.trends_text.setMaximumHeight(250)
        trends_layout.addWidget(self.trends_text)
        layout.addWidget(trends)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def analyze_generation(self):
        team_es_name = self.team_combo.currentText()
        team = team_en(team_es_name)

        sample_data = {
            "Brazil": [
                ("1958-1970", "Era Dorada", "Pelé, Garrincha, Rivelino", "3 Copas del Mundo"),
                ("1994-2002", "Era Ronaldo", "Ronaldo, Rivaldo, Ronaldinho", "2 Copas del Mundo"),
                ("2006-2018", "Era Moderna", "Neymar, Coutinho, Marcelo", "2 Copas Confederaciones"),
            ],
            "Germany": [
                ("1972-1980", "Era Beckenbauer", "Beckenbauer, Müller, Maier", "1 Euro, 1 Mundial"),
                ("1990-1996", "Era Matthäus", "Matthäus, Klinsmann, Sammer", "1 Mundial, 1 Euro"),
                ("2010-2014", "Era Lahm", "Lahm, Schweinsteiger, Neuer", "1 Mundial"),
            ],
            "Argentina": [
                ("1986-1990", "Era Maradona", "Maradona, Valdano, Ruggeri", "1 Mundial"),
                ("2005-2010", "Era Riquelme", "Riquelme, Messi, Mascherano", "1 Oro Olímpico"),
                ("2021-2026", "Era Messi-Scaloni", "Messi, Di María, Alvarez", "1 Mundial, 2 Copas América"),
            ],
            "default": [
                ("1960-1980", "Fundacional", "Pioneros del fútbol local", "Crecimiento del fútbol"),
                ("1990-2000", "Expansión Global", "Exportación de talento", "Participación en Mundiales"),
                ("2010-presente", "Era Moderna", "Jugadores en ligas top", "Competitividad internacional"),
            ]
        }

        gens = sample_data.get(team, sample_data["default"])
        self.generations_table.setRowCount(len(gens))
        for i, (era, name, players, achievements) in enumerate(gens):
            self.generations_table.setItem(i, 0, QTableWidgetItem(name))
            self.generations_table.setItem(i, 1, QTableWidgetItem(era))
            self.generations_table.setItem(i, 2, QTableWidgetItem(players))
            self.generations_table.setItem(i, 3, QTableWidgetItem(achievements))

        self.summary_label.setText(
            f'<span style="color:{NEON_PINK};font-size:14px;font-weight:bold;">'
            f'{team_es_name}</span>'
            f'<span style="color:{TEXT_SECONDARY};"> — '
            f'{len(gens)} generaciones identificadas. '
            f"Cada generación representa un ciclo competitivo clave en la historia del equipo.</span>"
        )

        trends_text = (
            f"Tendencias Generacionales para {team_es_name}\n"
            f"{'─' * 40}\n\n"
            f"🔵 Evolución: {gens[0][1]} → {gens[-1][1]}\n"
            f"🏆 Logros acumulados: {sum(len(g[3]) for g in gens)} hitos principales\n"
            f"📈 Ciclo actual: {gens[-1][0]} ({gens[-1][1]})\n"
            f"⚡ Jugador clave: {gens[-1][2].split(',')[0]}\n\n"
            f"La generación actual muestra {len(gens)} ciclos de evolución, "
            f"con una tendencia hacia {gens[-1][3].lower()}."
        )
        self.trends_text.setText(trends_text)
