from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from gui.theme import NEON_CYAN, NEON_PINK, NEON_PURPLE, BG, TEXT_PRIMARY, TEXT_SECONDARY
from engine.translate import team_flag, team_en


def show_upcoming_matches(parent, matches: list):
    if not matches:
        return

    dialog = QDialog(parent)
    dialog.setWindowTitle("📢 Próximos Partidos")
    dialog.setMinimumWidth(450)
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {BG};
            color: {TEXT_PRIMARY};
            font-family: 'Courier New', monospace;
        }}
        QLabel {{
            background: transparent;
            color: {TEXT_PRIMARY};
            font-size: 13px;
        }}
        QPushButton {{
            background-color: #1a1a28;
            color: {NEON_CYAN};
            border: 1px solid {NEON_CYAN};
            padding: 8px 20px;
            font-size: 12px;
            font-weight: bold;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {NEON_CYAN};
            color: {BG};
        }}
    """)

    layout = QVBoxLayout(dialog)
    layout.setSpacing(12)

    title = QLabel(f'<span style="color:{NEON_PINK};font-size:16px;font-weight:bold;">📢 PRÓXIMOS PARTIDOS</span>')
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title)

    for i, match in enumerate(matches[:5]):
        ta_es = match.get("team_a", "?")
        tb_es = match.get("team_b", "?")
        ta_en = team_en(ta_es) if ta_es != "?" else ""
        tb_en = team_en(tb_es) if tb_es != "?" else ""
        flag_a = team_flag(ta_en)
        flag_b = team_flag(tb_en)
        stage = match.get("stage", "Fase de Grupos")
        prob = match.get("probabilidad", "")
        prediction = match.get("prediccion", "")
        ta_display = f"{flag_a} {ta_es}" if flag_a else ta_es
        tb_display = f"{flag_b} {tb_es}" if flag_b else tb_es

        card = QLabel(
            f'<div style="border:1px solid #2a2a3a; border-radius:6px; padding:10px; margin:2px;">'
            f'<span style="color:{NEON_CYAN};font-size:14px;font-weight:bold;">{ta_display} vs {tb_display}</span><br>'
            f'<span style="color:{TEXT_SECONDARY};font-size:11px;">{stage}</span>'
            f'{"&nbsp;&nbsp;—&nbsp;&nbsp;" + prediction if prediction else ""}'
            f'{"&nbsp;&nbsp;<span style=\"color:#00ff88;\">" + prob + "</span>" if prob else ""}'
            f'</div>'
        )
        card.setWordWrap(True)
        layout.addWidget(card)

    btn = QPushButton("CERRAR")
    btn.clicked.connect(dialog.accept)
    layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

    dialog.exec()
