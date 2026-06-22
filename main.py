import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QHBoxLayout,
    QVBoxLayout, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from gui.theme import CYBERPUNK_STYLESHEET, NEON_CYAN, NEON_PINK, BG, NEON_GREEN, TEXT_SECONDARY
from gui.home import HomeScreen
from gui.predictor_view import PredictorScreen
from gui.team_stats_view import TeamStatsScreen
from gui.simulator_view import SimulatorScreen
from gui.h2h_view import H2HScreen
from gui.calibration_view import CalibrationScreen
from gui.fantasy_view import FantasyScreen
from gui.generations_view import GenerationsScreen
from gui.alerts_dialog import show_upcoming_matches
from gui.mapa_view import MapaScreen
from engine.stats import load_matches, build_training_dataset, load_fixtures_2026
from engine.predictor import create_predictor
from engine.translate import team_es, stage_es
from engine.datascraper import run_update_async, ensure_teams_data
from engine.worldcup_api import save_real_results, load_cached_results, fetch_and_cache_player_power, fetch_and_cache_power_rankings, update_async as wcup_update
from engine.stats import set_live_teams_form
from engine.live_data import compute_all_teams_form, update_async as live_update_async


class TrainThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.predictor = create_predictor()

    def run(self):
        try:
            df = load_matches()
            X, y, sw = build_training_dataset(df)
            self.predictor.fit(X, y, sw)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def get_predictor(self):
        return self.predictor


class LiveUpdateThread(QThread):
    finished = pyqtSignal(bool, str, dict)

    def __init__(self, predictor=None):
        super().__init__()
        self.predictor = predictor

    def run(self):
        try:
            from engine.live_data import update_async as live_update
            import time
            results = {}
            errors = []

            def _callback(success, msg, teams_form):
                if success:
                    results.update(teams_form)
                else:
                    errors.append(msg)

            t = live_update(callback=_callback)
            t.join(timeout=30)

            if results:
                self.finished.emit(True, "Datos del Mundial 2026 actualizados", results)
            else:
                from engine.live_data import compute_all_teams_form, load_2026_results
                cached = load_2026_results()
                if cached:
                    results = compute_all_teams_form(cached)
                    self.finished.emit(True, "Datos cargados desde caché", results)
                else:
                    self.finished.emit(False, "No se pudieron obtener datos en vivo", {})
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", {})


class LiveIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._on = True
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._toggle)
        self._timer.start(1500)

    def _toggle(self):
        self._on = not self._on
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QBrush
        p = QPainter(self)
        color = NEON_GREEN if self._on else "#004422"
        p.setBrush(QBrush(QColor(color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 10, 10)
        p.end()


class MainWindow(QMainWindow):
    data_updated = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADIVINAT0R — Predictor Mundial 2026")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(CYBERPUNK_STYLESHEET)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)

        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setStyleSheet(f"background:{BG}; border-bottom:1px solid #1a2a3a;")
        top_bar.setFixedHeight(48)
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(15, 5, 15, 5)

        logo = QLabel(
            f'<span style="color:{NEON_CYAN};font-size:16px;font-weight:bold;'
            f'font-family:Orbitron,Courier New,monospace;letter-spacing:3px;">'
            f'ADIVINAT0R</span>'
        )
        bar_layout.addWidget(logo)
        bar_layout.addSpacing(10)

        indicator = LiveIndicator()
        bar_layout.addWidget(indicator)
        status = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:10px;">'
            f' Mundial 2026 · EN VIVO</span>'
        )
        bar_layout.addWidget(status)
        bar_layout.addStretch()

        version = QLabel(
            f'<span style="color:{TEXT_SECONDARY};font-size:10px;">v2.0</span>'
        )
        bar_layout.addWidget(version)

        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        self.home_tab = None
        self.predictor_tab = None
        self.stats_tab = None
        self.simulator_tab = None
        self.h2h_tab = None
        self.calibration_tab = None
        self.fantasy_tab = None
        self.generations_tab = None
        self.mapa_tab = None

        self.init_tabs()
        self.train_model_async()

        self.data_updated.connect(self.on_data_update)

        ensure_teams_data()
        run_update_async(lambda ok, msg: self.data_updated.emit(ok, msg))

        QTimer.singleShot(200, self.load_real_results)
        QTimer.singleShot(800, self.show_upcoming_matches_alert)

    def show_upcoming_matches_alert(self):
        fixtures = load_fixtures_2026()
        groups = fixtures.get("groups", {})
        upcoming = []
        for g_name, teams in sorted(groups.items()):
            if len(teams) >= 2:
                for i in range(0, len(teams) - 1, 2):
                    if len(upcoming) >= 5:
                        break
                    upcoming.append({
                        "team_a": team_es(teams[i]),
                        "team_b": team_es(teams[i + 1]),
                        "stage": "Fase de Grupos",
                    })
            if len(upcoming) >= 5:
                break
        if upcoming:
            show_upcoming_matches(self, upcoming)

    def init_tabs(self):
        self.home_tab = HomeScreen()
        self.tabs.addTab(self.home_tab, " INICIO ")

        self.mapa_tab = MapaScreen()
        self.tabs.addTab(self.mapa_tab, " MAPA ")

        self.predictor_tab = PredictorScreen()
        self.predictor_tab.update_requested.connect(self.on_live_data_update_requested)
        self.tabs.addTab(self.predictor_tab, " PREDICTOR ")

        self.stats_tab = TeamStatsScreen()
        self.tabs.addTab(self.stats_tab, " ESTADÍSTICAS ")

        self.h2h_tab = H2HScreen()
        self.tabs.addTab(self.h2h_tab, " H2H ")

        self.generations_tab = GenerationsScreen()
        self.tabs.addTab(self.generations_tab, " GENERACIONES ")

        self.simulator_tab = SimulatorScreen()
        self.tabs.addTab(self.simulator_tab, " SIMULADOR ")

        self.calibration_tab = CalibrationScreen()
        self.tabs.addTab(self.calibration_tab, " CALIBRACIÓN ")

        self.fantasy_tab = FantasyScreen()
        self.tabs.addTab(self.fantasy_tab, " FANTASÍA ")

    def train_model_async(self):
        self.train_thread = TrainThread()
        self.train_thread.finished.connect(self.on_train_complete)
        self.train_thread.error.connect(self.on_train_error)
        self.train_thread.start()

    def on_train_complete(self):
        predictor = self.train_thread.get_predictor()
        if self.predictor_tab:
            self.predictor_tab.predictor = predictor
        if self.simulator_tab:
            pass
        self.statusBar().showMessage("Modelo entrenado correctamente", 5000)

    def load_real_results(self):
        matches, standings = save_real_results()
        if matches is None:
            matches, standings = load_cached_results()
            if not matches:
                QTimer.singleShot(5000, self.load_real_results)
                return
        self._update_standings_tabs(matches, standings)

        from engine.live_data import compute_all_teams_form
        teams_form = compute_all_teams_form(matches)
        set_live_teams_form(teams_form)

        wcup_update(lambda ok, msg: self.data_updated.emit(ok, msg))
        fetch_and_cache_player_power()
        fetch_and_cache_power_rankings()

    def _update_standings_tabs(self, matches, standings):
        if self.mapa_tab and hasattr(self.mapa_tab, 'set_data'):
            self.mapa_tab.set_data(matches, standings)
        if self.home_tab and hasattr(self.home_tab, 'set_standings'):
            self.home_tab.set_standings(standings)

    def on_data_update(self, success, msg):
        if success:
            matches, standings = load_cached_results()
            if matches:
                self._update_standings_tabs(matches, standings)
                from engine.live_data import compute_all_teams_form
                teams_form = compute_all_teams_form(matches)
                set_live_teams_form(teams_form)
            self.statusBar().showMessage(msg, 5000)

    def on_train_error(self, error_msg):
        self.statusBar().showMessage(f"Error de entrenamiento: {error_msg}", 10000)

    def on_live_data_update_requested(self):
        self.statusBar().showMessage("Actualizando datos estadísticos del Mundial 2026...", 0)
        thread = LiveUpdateThread(self.train_thread.get_predictor() if hasattr(self, 'train_thread') else None)
        thread.finished.connect(lambda ok, msg, tf: self._on_live_update_done(ok, msg, tf))
        thread.start()
        self._update_thread = thread

    def _on_live_update_done(self, success, msg, teams_form):
        if success and teams_form:
            set_live_teams_form(teams_form)
            predictor = self.train_thread.get_predictor() if hasattr(self, 'train_thread') else None
            if predictor:
                try:
                    predictor.retrain_with_live_data(teams_form)
                    msg += " | Modelo reentrenado con datos en vivo"
                except Exception as e:
                    msg += f" | Error reentrenando: {e}"
            from engine.worldcup_api import load_cached_results
            from engine.live_data import load_2026_results, compute_all_teams_form
            cached_matches, cached_standings = load_cached_results()
            if cached_matches:
                self._update_standings_tabs(cached_matches, cached_standings)
        if self.predictor_tab and hasattr(self.predictor_tab, 'on_update_complete'):
            self.predictor_tab.on_update_complete(success, msg)
        self.statusBar().showMessage(msg, 8000)

    def closeEvent(self, event):
        if hasattr(self, 'train_thread') and self.train_thread.isRunning():
            self.train_thread.quit()
            self.train_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Share Tech Mono", 10)
    font.setStyleHint(QFont.StyleHint.Monospace)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
