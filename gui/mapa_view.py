from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from gui.theme import (
    CYBERPUNK_STYLESHEET, NEON_CYAN, NEON_PINK, BG, NEON_GREEN,
    TEXT_SECONDARY, BG_SURFACE as SURFACE, BORDER
)
from engine.translate import team_es

try:
    from engine.translate import team_display, team_flag
except ImportError:
    def team_display(name):
        return team_es(name)
    def team_flag(name):
        return ""


HOSTS = ["United States", "Canada", "Mexico"]


class MapaScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.matches = []
        self.standings = {}
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(25, 15, 25, 15)
        self.layout.setSpacing(12)

        title = QLabel(
            f'<span style="color:{NEON_CYAN};font-size:22px;font-weight:bold;">'
            f'MAPA DE RESULTADOS</span>'
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        self.loading = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:14px;">'
            f'Cargando resultados...</span>'
        )
        self.loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.loading)

        self.content = QVBoxLayout()
        self.content.setSpacing(16)
        self.layout.addLayout(self.content)
        self.layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def set_data(self, matches, standings):
        self.matches = matches or []
        self.standings = standings or {}
        self.refresh()

    def refresh(self):
        while self.content.count():
            item = self.content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        has_data = bool(self.standings) or bool(self.matches)
        self.loading.setVisible(not has_data)
        if not has_data:
            return

        for g_name in sorted(self.standings.keys()):
            self._add_group_table(g_name, self.standings[g_name])

        played = [m for m in self.matches if m.get("played")]
        if played:
            section = QLabel(
                f'<span style="color:{NEON_GREEN};font-size:15px;font-weight:bold;">'
                f'PARTIDOS DISPUTADOS</span>'
            )
            section.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content.addWidget(section)
            for m in played:
                self._add_match(m)

    def _add_group_table(self, g_name, teams):
        box = QGroupBox(f"GRUPO {g_name}")
        box.setStyleSheet(
            f"QGroupBox{{background:{BG};border:1px solid {BORDER};"
            f"border-radius:6px;margin-top:12px;padding:10px;font-size:12px;color:{NEON_GREEN};}}"
            f"QGroupBox::title{{subcontrol-origin:margin;padding:0 8px;color:{NEON_GREEN};}}"
        )
        vbox = QVBoxLayout(box)
        vbox.setSpacing(2)

        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels(
            ["#", "Equipo", "Pts", "P", "W", "D", "L", "GF", "GA", "GD"]
        )
        table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        for i in (0, 2, 3, 4, 5, 6, 7, 8, 9):
            table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents
            )
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setMinimumHeight(len(teams) * 28 + 30)
        table.setMaximumHeight(len(teams) * 28 + 30)
        table.setStyleSheet(
            f"QTableWidget{{background:{BG};border:1px solid {BORDER};"
            f"border-radius:4px;color:{TEXT_SECONDARY};font-size:11px;}}"
            f"QHeaderView::section{{background:{BG};color:{NEON_CYAN};"
            f"border:none;padding:4px;font-weight:bold;font-size:10px;}}"
            f"QTableWidget::item{{padding:4px 6px;}}"
        )

        table.setRowCount(len(teams))
        for row, entry in enumerate(teams):
            team_name = entry.get("team", "")
            team_es_name = team_es(team_name)
            flag = team_flag(team_name)
            display = team_display(team_name)
            name_str = display if display and display != team_es_name else (
                f"{flag} {team_es_name}" if flag else team_es_name
            )

            pts = entry.get("Pts", 0)
            p = entry.get("P", 0)
            w = entry.get("W", 0)
            d = entry.get("D", 0)
            l = entry.get("L", 0)
            gf = entry.get("GF", 0)
            ga = entry.get("GA", 0)
            gd = entry.get("GD", gf - ga)

            is_host = team_name in HOSTS
            bg_color = QColor("#1a1028") if is_host else QColor("transparent")

            items = [
                (str(row + 1), True),
                (name_str, False),
                (str(pts), True),
                (str(p), True),
                (str(w), True),
                (str(d), True),
                (str(l), True),
                (str(gf), True),
                (str(ga), True),
                (str(gd), True),
            ]
            for col, (val, center) in enumerate(items):
                item = QTableWidgetItem(val)
                if center:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_host:
                    item.setBackground(bg_color)
                table.setItem(row, col, item)

        vbox.addWidget(table)
        self.content.addWidget(box)

    def _add_match(self, m):
        home = team_es(m.get("home", ""))
        away = team_es(m.get("away", ""))
        hs = m.get("home_score", 0)
        aw = m.get("away_score", 0)
        label = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:12px;">'
            f'&nbsp;&nbsp;&nbsp;&nbsp;{home} </span>'
            f'<span style="color:{NEON_PINK};font-size:12px;font-weight:bold;">'
            f'{hs}-{aw}</span>'
            f'<span style="color:{TEXT_SECONDARY};font-size:12px;"> {away}</span>'
        )
        self.content.addWidget(label)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
