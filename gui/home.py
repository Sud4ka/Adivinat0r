from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout, QGridLayout,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.theme import BG, NEON_CYAN, NEON_PINK, NEON_PURPLE, NEON_GREEN, NEON_AMBER, BG_CARD, TEXT_SECONDARY, TEXT_PRIMARY, BORDER, glitch_label
from engine.stats import load_fixtures_2026, load_teams
from engine.translate import team_es, team_flag, team_display, stage_es, UI_ES


class HomeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fixtures = load_fixtures_2026()
        self.teams = load_teams()
        self.standings = {}
        self.init_ui()

    def set_standings(self, standings: dict = None):
        self.standings = standings or {}
        self.refresh_standings()

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(10)

        title_label = QLabel(glitch_label("ADIVINAT0R", 38))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setMaximumHeight(70)
        layout.addWidget(title_label)

        subtitle = QLabel(
            f'<span style="color:{NEON_PINK}; font-size:12px;">'
            f'{UI_ES["home_subtitle"]}</span>'
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        hosts = " / ".join([team_es(h) for h in self.fixtures["hosts"]])
        total = sum(len(g) for g in self.fixtures["groups"].values())
        host_label = QLabel(
            f'<span style="color:{TEXT_SECONDARY}; font-size:11px;">'
            f"{UI_ES['home_hosts']}: {hosts}  |  {UI_ES['home_groups']}: {len(self.fixtures['groups'])}  |  "
            f"{UI_ES['home_teams']}: {total}</span>"
        )
        host_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(host_label)

        layout.addSpacing(6)

        phase_badge = QFrame()
        phase_badge.setStyleSheet(
            f"background:{NEON_GREEN}15; border:1px solid {NEON_GREEN}40; border-radius:8px; padding:6px;"
        )
        phase_layout = QHBoxLayout(phase_badge)
        phase_layout.setContentsMargins(10, 4, 10, 4)
        dot = QLabel(f'<span style="color:{NEON_GREEN};font-size:18px;">●</span>')
        phase_text = QLabel(
            f'<span style="color:{NEON_GREEN};font-size:12px;font-weight:bold;">'
            f'{UI_ES["home_phase_group_stage"]} 2026 — EN VIVO</span>'
        )
        phase_layout.addWidget(dot)
        phase_layout.addWidget(phase_text)
        phase_layout.addStretch()
        layout.addWidget(phase_badge)

        groups_label = QLabel(
            f'<span style="color:{NEON_CYAN}; font-size:15px; font-weight:bold;">'
            f'{UI_ES["home_standing"]}</span>'
        )
        groups_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(groups_label)

        self.groups_container = QVBoxLayout()
        self.groups_container.setSpacing(6)
        self.group_widgets = {}

        groups = self.fixtures["groups"]
        sorted_groups = sorted(groups.keys())

        for g_name in sorted_groups:
            group_box = QGroupBox(f"Grupo {g_name}")
            group_box.setStyleSheet(
                f"QGroupBox{{background:{BG_CARD};border:1px solid {BORDER};"
                f"border-radius:6px;margin-top:10px;padding:8px;font-size:12px;color:{NEON_CYAN};}}"
                f"QGroupBox::title{{subcontrol-origin:margin;padding:0 6px;color:{NEON_CYAN};}}"
            )
            g_layout = QVBoxLayout(group_box)
            g_layout.setSpacing(2)

            header = QHBoxLayout()
            for h in ["#", UI_ES['home_teams'], UI_ES['home_pts'], UI_ES['home_gf'], UI_ES['home_gc'], UI_ES['home_dg']]:
                lbl = QLabel(
                    f'<span style="color:{TEXT_SECONDARY};font-size:9px;font-weight:bold;">{h}</span>'
                )
                lbl.setFixedWidth(26 if h != UI_ES['home_teams'] else 150)
                header.addWidget(lbl)
            header.addStretch()
            g_layout.addLayout(header)

            self.group_widgets[g_name] = g_layout

            teams_list = groups[g_name]
            for rank, team_en in enumerate(teams_list, 1):
                team_es_name = team_es(team_en)
                is_host = team_en in self.fixtures["hosts"]
                color = NEON_PINK if is_host else NEON_CYAN
                flag = team_flag(team_en)
                display = f"{flag} {team_es_name}" if flag else team_es_name

                row = QHBoxLayout()
                rank_lbl = QLabel(
                    f'<span style="color:{TEXT_SECONDARY};font-size:11px;">{rank}</span>'
                )
                rank_lbl.setFixedWidth(26)
                row.addWidget(rank_lbl)

                name_lbl = QLabel(
                    f'<span style="color:{color};font-size:12px;font-weight:bold;">{display}</span>'
                )
                name_lbl.setFixedWidth(150)
                row.addWidget(name_lbl)

                for _ in range(4):
                    empty = QLabel(
                        f'<span style="color:{TEXT_SECONDARY};font-size:11px;">-</span>'
                    )
                    empty.setFixedWidth(26)
                    row.addWidget(empty)

                g_layout.addLayout(row)

            self.groups_container.addWidget(group_box)

        layout.addLayout(self.groups_container)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def refresh_standings(self):
        if not self.standings:
            return
        for g_name, teams_data in self.standings.items():
            if g_name not in self.group_widgets:
                continue
            g_layout = self.group_widgets[g_name]

            while g_layout.count() > 1:
                item = g_layout.takeAt(g_layout.count() - 1)
                if item and item.widget():
                    item.widget().deleteLater()
                elif item and item.layout():
                    self._clear_layout(item.layout())

            for rank, entry in enumerate(teams_data, 1):
                if isinstance(entry, dict):
                    team = entry.get("team", "")
                    pts = entry.get("Pts", 0)
                    gf = entry.get("GF", 0)
                    gc = entry.get("GA", 0)
                    gd = entry.get("GD", gf - gc)
                elif isinstance(entry, (list, tuple)):
                    team = entry[0]
                    pts = entry[1]
                    gf = entry[2]
                    gc = entry[3] if len(entry) > 3 else gf
                    gd = gf - gc
                else:
                    continue

                team_es_name = team_es(team)
                is_host = team in self.fixtures["hosts"]
                color = NEON_PINK if is_host else NEON_CYAN
                flag = team_flag(team)
                display = f"{flag} {team_es_name}" if flag else team_es_name
                gd_str = f"+{gd}" if gd > 0 else str(gd)

                row = QHBoxLayout()
                rank_lbl = QLabel(
                    f'<span style="color:{NEON_AMBER if rank <= 2 else TEXT_SECONDARY};font-size:11px;font-weight:bold;">{rank}</span>'
                )
                rank_lbl.setFixedWidth(26)
                row.addWidget(rank_lbl)

                name_lbl = QLabel(
                    f'<span style="color:{color};font-size:12px;font-weight:bold;">{display}</span>'
                )
                name_lbl.setFixedWidth(150)
                row.addWidget(name_lbl)

                for val in [pts, gf, gc, gd_str]:
                    v = QLabel(
                        f'<span style="color:{TEXT_PRIMARY};font-size:11px;">{val}</span>'
                    )
                    v.setFixedWidth(26)
                    row.addWidget(v)

                g_layout.addLayout(row)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
