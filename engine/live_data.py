import json
import os
import threading
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_2026_results():
    path = os.path.join(DATA_DIR, "real_results.json")
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("matches", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def compute_team_form_2026(team, matches_2026):
    team_matches = []
    for m in matches_2026:
        if not m.get("played") or m.get("home_score") is None:
            continue
        if m["home"] == team:
            team_matches.append({
                "gf": m["home_score"], "ga": m["away_score"],
                "pts": 3 if m["home_score"] > m["away_score"] else (1 if m["home_score"] == m["away_score"] else 0)
            })
        elif m["away"] == team:
            team_matches.append({
                "gf": m["away_score"], "ga": m["home_score"],
                "pts": 3 if m["away_score"] > m["home_score"] else (1 if m["away_score"] == m["home_score"] else 0)
            })

    if not team_matches:
        return {"goals_scored": 0, "goals_conceded": 0, "win_rate": 0, "ppg": 0, "gd": 0}

    n = len(team_matches)
    total_gf = sum(m["gf"] for m in team_matches)
    total_ga = sum(m["ga"] for m in team_matches)
    total_pts = sum(m["pts"] for m in team_matches)
    wins = sum(1 for m in team_matches if m["pts"] == 3)

    return {
        "goals_scored": round(total_gf / n, 2),
        "goals_conceded": round(total_ga / n, 2),
        "win_rate": round(wins / n, 2),
        "ppg": round(total_pts / n, 2),
        "gd": total_gf - total_ga,
        "matches_played": n,
    }


def compute_all_teams_form(matches_2026=None):
    if matches_2026 is None:
        matches_2026 = load_2026_results()

    teams = set()
    for m in matches_2026:
        if not m.get("played"):
            continue
        teams.add(m["home"])
        teams.add(m["away"])

    return {t: compute_team_form_2026(t, matches_2026) for t in sorted(teams) if t}


def build_live_feature_vector(team_a, team_b, teams_form):
    fa = teams_form.get(team_a, {})
    fb = teams_form.get(team_b, {})

    gf_diff = fa.get("goals_scored", 0) - fb.get("goals_scored", 0)
    ga_diff = fa.get("goals_conceded", 0) - fb.get("goals_conceded", 0)
    wr_diff = fa.get("win_rate", 0) - fb.get("win_rate", 0)
    ppg_diff = fa.get("ppg", 0) - fb.get("ppg", 0)
    gd_a = fa.get("gd", 0)
    gd_b = fb.get("gd", 0)
    gd_norm = (gd_a - gd_b) / max(1, abs(gd_a) + abs(gd_b))

    return [gf_diff, ga_diff, wr_diff, ppg_diff, gd_norm]


LIVE_FEATURE_COUNT = 5
LIVE_FEATURE_NAMES = [
    "form_gf_diff", "form_ga_diff", "form_win_rate_diff",
    "form_ppg_diff", "form_gd_norm"
]


def get_form_summary(teams_form):
    lines = []
    for team, form in sorted(teams_form.items()):
        mp = form.get("matches_played", 0)
        if mp == 0:
            continue
        lines.append(
            f"{team}: {mp} PJ | GF {form['goals_scored']}/p | GC {form['goals_conceded']}/p "
            f"| WR {form['win_rate']:.0%} | PPG {form['ppg']:.2f} | GD {form['gd']:+d}"
        )
    return "\n".join(lines) if lines else "Sin datos del Mundial 2026"


def update_async(callback=None):
    def _task():
        try:
            from engine.worldcup_api import save_real_results
            matches, standings = save_real_results()
            count = len(matches) if matches else 0
            played = sum(1 for m in matches if m["played"]) if matches else 0

            teams_form = {}
            if matches:
                teams_form = compute_all_teams_form(matches)
            teams_with_data = sum(1 for t in teams_form.values() if t.get("matches_played", 0) > 0)

            msg = (
                f"Datos 2026 actualizados: {played}/{count} partidos, "
                f"{teams_with_data} equipos con estadísticas en vivo"
            )
            if callback:
                callback(True, msg, teams_form)
        except Exception as e:
            if callback:
                callback(False, str(e), {})

    t = threading.Thread(target=_task, daemon=True)
    t.start()
    return t
