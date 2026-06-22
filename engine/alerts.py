import time
import threading


class AlertSystem:
    def __init__(self):
        self.favorite_teams = set()
        self.enabled = True
        self._notification = None

    def _try_plyer(self):
        if self._notification is not None:
            return self._notification
        try:
            from plyer import notification
            self._notification = notification
        except ImportError:
            self._notification = None
        return self._notification

    def notify(self, title: str, message: str, timeout: int = 5):
        n = self._try_plyer()
        if n:
            try:
                n.notify(title=title, message=message, timeout=timeout)
            except Exception:
                pass
        print(f"[ALERT] {title}: {message}")

    def notify_match_alert(self, team_a: str, team_b: str, prediction: str, confidence: float):
        if not self.enabled:
            return
        title = f"Match Alert: {team_a} vs {team_b}"
        message = f"Prediction: {prediction} (Confidence: {confidence:.1f}%)"
        threading.Thread(target=self.notify, args=(title, message), daemon=True).start()

    def notify_convergence(self, team_a: str, team_b: str, confidence: float):
        if not self.enabled or confidence < 80:
            return
        title = "Strong Signal Detected"
        message = f"Concentración Máxima confident in {team_a} vs {team_b} ({confidence:.1f}%)"
        threading.Thread(target=self.notify, args=(title, message), daemon=True).start()

    def notify_probability_shift(self, team_a: str, team_b: str, old_prob: float, new_prob: float):
        if not self.enabled or abs(new_prob - old_prob) <= 10:
            return
        direction = "up" if new_prob > old_prob else "down"
        title = f"Probability Shift: {team_a} vs {team_b}"
        message = f"{team_a} win probability moved {direction} by {abs(new_prob - old_prob):.1f}%"
        threading.Thread(target=self.notify, args=(title, message), daemon=True).start()

    def set_favorites(self, teams: list):
        self.favorite_teams = set(teams)

    def add_favorite(self, team: str):
        self.favorite_teams.add(team)

    def remove_favorite(self, team: str):
        self.favorite_teams.discard(team)
