import json
import os
import re
import threading
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TEAMS_PATH = os.path.join(DATA_DIR, "teams.json")

FALLBACK_STATS = {
    "Argentina": {"appearances": 18, "matches_played": 89, "wins": 48, "draws": 17, "losses": 24, "goals_for": 155, "goals_against": 101, "best_finish": "Champion", "titles": 3, "continent": "South America"},
    "Brazil": {"appearances": 22, "matches_played": 114, "wins": 76, "draws": 19, "losses": 19, "goals_for": 237, "goals_against": 108, "best_finish": "Champion", "titles": 5, "continent": "South America"},
    "Germany": {"appearances": 20, "matches_played": 112, "wins": 68, "draws": 22, "losses": 22, "goals_for": 232, "goals_against": 130, "best_finish": "Champion", "titles": 4, "continent": "Europe"},
    "France": {"appearances": 16, "matches_played": 73, "wins": 41, "draws": 15, "losses": 17, "goals_for": 136, "goals_against": 85, "best_finish": "Champion", "titles": 2, "continent": "Europe"},
    "England": {"appearances": 16, "matches_played": 76, "wins": 32, "draws": 22, "losses": 22, "goals_for": 104, "goals_against": 72, "best_finish": "Champion", "titles": 1, "continent": "Europe"},
    "Spain": {"appearances": 16, "matches_played": 70, "wins": 33, "draws": 17, "losses": 20, "goals_for": 108, "goals_against": 80, "best_finish": "Champion", "titles": 1, "continent": "Europe"},
    "Netherlands": {"appearances": 11, "matches_played": 55, "wins": 30, "draws": 14, "losses": 11, "goals_for": 96, "goals_against": 55, "best_finish": "Runners-up", "titles": 0, "continent": "Europe"},
    "Uruguay": {"appearances": 14, "matches_played": 61, "wins": 26, "draws": 14, "losses": 21, "goals_for": 94, "goals_against": 77, "best_finish": "Champion", "titles": 2, "continent": "South America"},
    "Italy": {"appearances": 18, "matches_played": 83, "wins": 45, "draws": 21, "losses": 17, "goals_for": 128, "goals_against": 77, "best_finish": "Champion", "titles": 4, "continent": "Europe"},
    "Portugal": {"appearances": 8, "matches_played": 35, "wins": 17, "draws": 6, "losses": 12, "goals_for": 61, "goals_against": 41, "best_finish": "Semi-finals", "titles": 0, "continent": "Europe"},
    "Belgium": {"appearances": 14, "matches_played": 51, "wins": 21, "draws": 10, "losses": 20, "goals_for": 74, "goals_against": 73, "best_finish": "Semi-finals", "titles": 0, "continent": "Europe"},
    "Croatia": {"appearances": 6, "matches_played": 31, "wins": 13, "draws": 8, "losses": 10, "goals_for": 43, "goals_against": 38, "best_finish": "Runners-up", "titles": 0, "continent": "Europe"},
    "Mexico": {"appearances": 17, "matches_played": 62, "wins": 17, "draws": 16, "losses": 29, "goals_for": 64, "goals_against": 96, "best_finish": "Quarter-finals", "titles": 0, "continent": "North America"},
    "Switzerland": {"appearances": 12, "matches_played": 43, "wins": 13, "draws": 9, "losses": 21, "goals_for": 55, "goals_against": 74, "best_finish": "Quarter-finals", "titles": 0, "continent": "Europe"},
    "Sweden": {"appearances": 12, "matches_played": 50, "wins": 17, "draws": 13, "losses": 20, "goals_for": 79, "goals_against": 76, "best_finish": "Runners-up", "titles": 0, "continent": "Europe"},
    "Japan": {"appearances": 7, "matches_played": 25, "wins": 7, "draws": 5, "losses": 13, "goals_for": 25, "goals_against": 36, "best_finish": "Round of 16", "titles": 0, "continent": "Asia"},
    "South Korea": {"appearances": 11, "matches_played": 39, "wins": 7, "draws": 11, "losses": 21, "goals_for": 40, "goals_against": 74, "best_finish": "Semi-finals", "titles": 0, "continent": "Asia"},
    "Colombia": {"appearances": 7, "matches_played": 24, "wins": 10, "draws": 4, "losses": 10, "goals_for": 33, "goals_against": 31, "best_finish": "Quarter-finals", "titles": 0, "continent": "South America"},
    "Morocco": {"appearances": 6, "matches_played": 21, "wins": 5, "draws": 6, "losses": 10, "goals_for": 20, "goals_against": 26, "best_finish": "Semi-finals", "titles": 0, "continent": "Africa"},
    "Senegal": {"appearances": 3, "matches_played": 10, "wins": 3, "draws": 2, "losses": 5, "goals_for": 8, "goals_against": 13, "best_finish": "Quarter-finals", "titles": 0, "continent": "Africa"},
    "Ghana": {"appearances": 4, "matches_played": 15, "wins": 5, "draws": 4, "losses": 6, "goals_for": 14, "goals_against": 18, "best_finish": "Quarter-finals", "titles": 0, "continent": "Africa"},
    "Australia": {"appearances": 6, "matches_played": 20, "wins": 4, "draws": 4, "losses": 12, "goals_for": 17, "goals_against": 39, "best_finish": "Round of 16", "titles": 0, "continent": "Oceania"},
    "Iran": {"appearances": 6, "matches_played": 18, "wins": 2, "draws": 4, "losses": 12, "goals_for": 9, "goals_against": 33, "best_finish": "Group Stage", "titles": 0, "continent": "Asia"},
    "Saudi Arabia": {"appearances": 6, "matches_played": 19, "wins": 4, "draws": 3, "losses": 12, "goals_for": 14, "goals_against": 38, "best_finish": "Round of 16", "titles": 0, "continent": "Asia"},
    "Tunisia": {"appearances": 6, "matches_played": 18, "wins": 2, "draws": 5, "losses": 11, "goals_for": 14, "goals_against": 31, "best_finish": "Group Stage", "titles": 0, "continent": "Africa"},
    "Ecuador": {"appearances": 4, "matches_played": 13, "wins": 4, "draws": 3, "losses": 6, "goals_for": 14, "goals_against": 18, "best_finish": "Round of 16", "titles": 0, "continent": "South America"},
    "Paraguay": {"appearances": 8, "matches_played": 27, "wins": 7, "draws": 10, "losses": 10, "goals_for": 30, "goals_against": 39, "best_finish": "Quarter-finals", "titles": 0, "continent": "South America"},
    "Algeria": {"appearances": 4, "matches_played": 13, "wins": 3, "draws": 4, "losses": 6, "goals_for": 14, "goals_against": 21, "best_finish": "Round of 16", "titles": 0, "continent": "Africa"},
    "Ivory Coast": {"appearances": 4, "matches_played": 12, "wins": 4, "draws": 2, "losses": 6, "goals_for": 16, "goals_against": 19, "best_finish": "Group Stage", "titles": 0, "continent": "Africa"},
    "Turkey": {"appearances": 2, "matches_played": 10, "wins": 4, "draws": 2, "losses": 4, "goals_for": 13, "goals_against": 18, "best_finish": "Semi-finals", "titles": 0, "continent": "Europe"},
    "Scotland": {"appearances": 8, "matches_played": 23, "wins": 5, "draws": 7, "losses": 11, "goals_for": 26, "goals_against": 39, "best_finish": "Group Stage", "titles": 0, "continent": "Europe"},
    "Norway": {"appearances": 3, "matches_played": 8, "wins": 2, "draws": 3, "losses": 3, "goals_for": 7, "goals_against": 8, "best_finish": "Round of 16", "titles": 0, "continent": "Europe"},
    "New Zealand": {"appearances": 2, "matches_played": 6, "wins": 0, "draws": 3, "losses": 3, "goals_for": 4, "goals_against": 14, "best_finish": "Group Stage", "titles": 0, "continent": "Oceania"},
    "Iraq": {"appearances": 1, "matches_played": 3, "wins": 0, "draws": 0, "losses": 3, "goals_for": 1, "goals_against": 4, "best_finish": "Group Stage", "titles": 0, "continent": "Asia"},
    "Jordan": {"appearances": 0, "matches_played": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0, "best_finish": "Debut", "titles": 0, "continent": "Asia"},
    "Austria": {"appearances": 7, "matches_played": 29, "wins": 12, "draws": 5, "losses": 12, "goals_for": 43, "goals_against": 47, "best_finish": "Semi-finals", "titles": 0, "continent": "Europe"},
    "Panama": {"appearances": 1, "matches_played": 3, "wins": 0, "draws": 0, "losses": 3, "goals_for": 2, "goals_against": 11, "best_finish": "Group Stage", "titles": 0, "continent": "North America"},
    "Canada": {"appearances": 2, "matches_played": 6, "wins": 0, "draws": 1, "losses": 5, "goals_for": 3, "goals_against": 18, "best_finish": "Group Stage", "titles": 0, "continent": "North America"},
    "Bosnia and Herzegovina": {"appearances": 1, "matches_played": 3, "wins": 1, "draws": 0, "losses": 2, "goals_for": 4, "goals_against": 4, "best_finish": "Group Stage", "titles": 0, "continent": "Europe"},
    "Czechia": {"appearances": 10, "matches_played": 34, "wins": 12, "draws": 5, "losses": 17, "goals_for": 48, "goals_against": 51, "best_finish": "Runners-up", "titles": 0, "continent": "Europe"},
    "Haiti": {"appearances": 1, "matches_played": 3, "wins": 0, "draws": 0, "losses": 3, "goals_for": 2, "goals_against": 14, "best_finish": "Group Stage", "titles": 0, "continent": "North America"},
    "Curaçao": {"appearances": 0, "matches_played": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0, "best_finish": "Debut", "titles": 0, "continent": "North America"},
    "Cabo Verde": {"appearances": 0, "matches_played": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0, "best_finish": "Debut", "titles": 0, "continent": "Africa"},
    "Congo DR": {"appearances": 1, "matches_played": 3, "wins": 0, "draws": 0, "losses": 3, "goals_for": 0, "goals_against": 14, "best_finish": "Group Stage", "titles": 0, "continent": "Africa"},
    "Uzbekistan": {"appearances": 0, "matches_played": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0, "best_finish": "Debut", "titles": 0, "continent": "Asia"},
    "Qatar": {"appearances": 1, "matches_played": 3, "wins": 0, "draws": 0, "losses": 3, "goals_for": 1, "goals_against": 7, "best_finish": "Group Stage", "titles": 0, "continent": "Asia"},
    "Egypt": {"appearances": 4, "matches_played": 7, "wins": 0, "draws": 2, "losses": 5, "goals_for": 5, "goals_against": 12, "best_finish": "Round of 16", "titles": 0, "continent": "Africa"},
    "South Africa": {"appearances": 3, "matches_played": 9, "wins": 1, "draws": 4, "losses": 4, "goals_for": 11, "goals_against": 14, "best_finish": "Group Stage", "titles": 0, "continent": "Africa"},
}

WIKI_PAGES = {
    "Argentina": "Argentina_at_the_FIFA_World_Cup",
    "Brazil": "Brazil_at_the_FIFA_World_Cup",
    "Germany": "Germany_at_the_FIFA_World_Cup",
    "France": "France_at_the_FIFA_World_Cup",
    "England": "England_at_the_FIFA_World_Cup",
    "Spain": "Spain_at_the_FIFA_World_Cup",
    "Netherlands": "Netherlands_at_the_FIFA_World_Cup",
    "Uruguay": "Uruguay_at_the_FIFA_World_Cup",
    "Italy": "Italy_at_the_FIFA_World_Cup",
    "Portugal": "Portugal_at_the_FIFA_World_Cup",
    "Belgium": "Belgium_at_the_FIFA_World_Cup",
    "Croatia": "Croatia_at_the_FIFA_World_Cup",
    "Mexico": "Mexico_at_the_FIFA_World_Cup",
    "Switzerland": "Switzerland_at_the_FIFA_World_Cup",
    "Sweden": "Sweden_at_the_FIFA_World_Cup",
    "Japan": "Japan_at_the_FIFA_World_Cup",
    "South Korea": "South_Korea_at_the_FIFA_World_Cup",
    "Colombia": "Colombia_at_the_FIFA_World_Cup",
    "Morocco": "Morocco_at_the_FIFA_World_Cup",
    "Senegal": "Senegal_at_the_FIFA_World_Cup",
    "Ghana": "Ghana_at_the_FIFA_World_Cup",
    "Australia": "Australia_at_the_FIFA_World_Cup",
    "Iran": "Iran_at_the_FIFA_World_Cup",
    "Saudi Arabia": "Saudi_Arabia_at_the_FIFA_World_Cup",
    "Tunisia": "Tunisia_at_the_FIFA_World_Cup",
    "Ecuador": "Ecuador_at_the_FIFA_World_Cup",
    "Turkey": "Turkey_at_the_FIFA_World_Cup",
    "Scotland": "Scotland_at_the_FIFA_World_Cup",
    "Egypt": "Egypt_at_the_FIFA_World_Cup",
    "Czechia": "Czech_Republic_at_the_FIFA_World_Cup",
    "Bosnia and Herzegovina": "Bosnia_and_Herzegovina_at_the_FIFA_World_Cup",
    "Haiti": "Haiti_at_the_FIFA_World_Cup",
    "Congo DR": "DR_Congo_at_the_FIFA_World_Cup",
    "South Africa": "South_Africa_at_the_FIFA_World_Cup",
    "Ivory Coast": "Ivory_Coast_at_the_FIFA_World_Cup",
    "Algeria": "Algeria_at_the_FIFA_World_Cup",
    "Paraguay": "Paraguay_at_the_FIFA_World_Cup",
    "New Zealand": "New_Zealand_at_the_FIFA_World_Cup",
    "Norway": "Norway_at_the_FIFA_World_Cup",
    "Austria": "Austria_at_the_FIFA_World_Cup",
    "Panama": "Panama_at_the_FIFA_World_Cup",
    "Canada": "Canada_at_the_FIFA_World_Cup",
}

BEST_FINISH_MAP = {
    "Champion": "Champion",
    "Runners-up": "Runners-up",
    "Third place": "Third place",
    "Fourth place": "Fourth place",
    "Semi-finals": "Semi-finals",
    "Quarter-finals": "Quarter-finals",
    "Round of 16": "Round of 16",
    "Group stage": "Group Stage",
    "First round": "Group Stage",
}


def _clean_num(text: str) -> int | None:
    clean = re.sub(r'[^0-9]', '', text)
    if clean and clean.isdigit():
        v = int(clean)
        if 0 < v < 300:
            return v
    return None


def scrape_team_from_wikipedia(team_name: str) -> dict | None:
    page = WIKI_PAGES.get(team_name)
    if not page:
        return None

    url = f"https://en.wikipedia.org/wiki/{page}"
    try:
        req = Request(url, headers={"User-Agent": "Adivinat0r/2.0"})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
    except Exception:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return None

    result = {}
    full_text = soup.get_text()

    m = re.search(r'(\d+)\s*World\s*Cup\s*(?:appearances|finals)', full_text, re.IGNORECASE)
    if m:
        result["appearances"] = int(m.group(1))

    for key, norm in BEST_FINISH_MAP.items():
        pat = r'Best\s*(?:result|finish|performance)[:\s]+' + re.escape(key)
        if re.search(pat, full_text, re.IGNORECASE):
            result["best_finish"] = norm
            break
    if "best_finish" not in result:
        m = re.search(r'Best\s*(?:result|finish|performance)[:\s]+([^\n,.]+)', full_text, re.IGNORECASE)
        if m:
            result["best_finish"] = m.group(1).strip()

    infobox = soup.find("table", class_="infobox")
    if infobox:
        ib_text = infobox.get_text()
        m2 = re.search(r'(\d+)\s*title', ib_text, re.IGNORECASE)
        if m2:
            result["titles"] = int(m2.group(1))

    table = soup.find("table", class_="wikitable")
    if table:
        for row in table.find_all("tr"):
            text = row.get_text(strip=True)
            if text.startswith("Total") or text.startswith("Overall"):
                cells = row.find_all(["td", "th"])
                texts = [c.get_text(strip=True) for c in cells]
                nums = []
                for t in texts:
                    v = _clean_num(t)
                    if v is not None:
                        nums.append(v)
                if len(nums) < 4:
                    continue
                for offset in range(min(3, len(nums) - 4)):
                    mp = nums[0 + offset]
                    w = nums[1 + offset]
                    d_or_l = nums[2 + offset]
                    l_or_gf = nums[3 + offset]
                    if w + d_or_l + l_or_gf >= mp - 2 and w + d_or_l + l_or_gf <= mp + 2:
                        result["matches_played"] = mp
                        result["wins"] = w
                        result["draws"] = d_or_l
                        result["losses"] = l_or_gf
                        if len(nums) > 4 + offset:
                            result["goals_for"] = nums[4 + offset]
                        if len(nums) > 5 + offset:
                            result["goals_against"] = nums[5 + offset]
                        break
                if "matches_played" in result:
                    gf_from_scores = result.get("goals_for", 0)
                    if gf_from_scores > 0:
                        pass
                    break

    return result if result.get("matches_played") or result.get("appearances") else None


def update_team_data(team_name: str, current_data: dict) -> dict:
    scraped = scrape_team_from_wikipedia(team_name)
    if scraped:
        for f in ["matches_played", "wins", "draws", "losses", "goals_for", "goals_against", "appearances", "best_finish", "titles"]:
            if f in scraped:
                current_data[f] = scraped[f]
    return current_data


def run_update(progress_callback=None):
    try:
        with open(TEAMS_PATH) as f:
            teams = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        teams = FALLBACK_STATS.copy()
        with open(TEAMS_PATH, "w") as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)
        return 0, 0

    changed_count = 0
    processed = 0
    for name in sorted(teams.keys()):
        if name not in WIKI_PAGES:
            continue
        processed += 1
        old = dict(teams[name])
        teams[name] = update_team_data(name, teams[name])
        if old != teams[name]:
            changed_count += 1
        if progress_callback:
            progress_callback(processed, len(WIKI_PAGES), name)

    with open(TEAMS_PATH, "w") as f:
        json.dump(teams, f, indent=2, ensure_ascii=False)

    return changed_count, processed


def run_update_async(callback=None):
    def _task():
        try:
            c, t = run_update()
            msg = f"Actualizados {c}/{t} equipos desde Wikipedia" if c else f"Datos actualizados ({t} equipos verificados)"
            if callback:
                callback(True, msg)
        except Exception as e:
            if callback:
                callback(False, str(e))

    t = threading.Thread(target=_task, daemon=True)
    t.start()
    return t


def ensure_teams_data():
    try:
        with open(TEAMS_PATH) as f:
            teams = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        teams = FALLBACK_STATS.copy()
        with open(TEAMS_PATH, "w") as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)
        return

    changed = False
    for name, data in FALLBACK_STATS.items():
        if name not in teams:
            teams[name] = data
            changed = True
        else:
            for k, v in data.items():
                if k not in teams[name]:
                    teams[name][k] = v
                    changed = True

    if changed:
        with open(TEAMS_PATH, "w") as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)
