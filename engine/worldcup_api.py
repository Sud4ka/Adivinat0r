import json
import os
import threading
from urllib.request import urlopen, Request
from urllib.error import URLError

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RESULTS_PATH = os.path.join(DATA_DIR, "real_results.json")
PLAYERS_PATH = os.path.join(DATA_DIR, "players_cache.json")

API_MATCHES = "https://api.fifa.com/api/v3/calendar/matches?idSeason=285023&idCompetition=17&language=en&count=500"
API_PLAYERS = "https://play.fifa.com/json/fantasy/players.json"
FANTASY_TEAMS = "https://play.fifa.com/json/fantasy/squads_fifa.json"

TEAM_NAME_MAP = {
    "IR Iran": "Iran",
    "Korea Republic": "South Korea",
    "USA": "United States",
    "IRN": "Iran", "KOR": "South Korea", "KSA": "Saudi Arabia",
    "RSA": "South Africa", "CRC": "Costa Rica", "CMR": "Cameroon",
    "CIV": "Ivory Coast", "DR Congo": "Congo DR", "Czech Republic": "Czechia",
    "Türkiye": "Turkey", "Côte d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde", "Korea DPR": "North Korea",
}

TEAM_FIFA_ID_MAP = {
    "43911": "Mexico", "43883": "South Africa", "43822": "South Korea", "43976": "Australia",
    "43888": "Tunisia", "43960": "Netherlands", "43819": "Japan",
    "43901": "Costa Rica", "43974": "Wales", "43930": "Uruguay",
    "43927": "Ecuador", "43941": "Denmark", "43946": "France",
    "43969": "Spain", "43948": "Germany", "43924": "Brazil",
    "43962": "Poland", "43872": "Morocco", "43921": "United States",
    "43971": "Switzerland", "43935": "Belgium", "43938": "Croatia",
    "43879": "Senegal", "43922": "Argentina",
    "43860": "Ghana", "43963": "Portugal",
    "43849": "Cameroon", "43942": "England",
    "1902465": "Serbia", "43817": "Iran",
    "43834": "Qatar", "43835": "Saudi Arabia",
    "43899": "Canada",
    "44149": "South Korea",
    "44155": "Portugal",
    "44111": "Bosnia and Herzegovina",
    "44128": "Czechia",
    "44135": "Haiti",
    "44140": "Curaçao",
    "44147": "Cabo Verde",
    "44148": "Congo DR",
    "44150": "Uzbekistan",
    "44139": "Jordan",
    "44112": "Algeria",
    "44122": "Austria",
    "44121": "Turkey",
    "44126": "Scotland",
    "44129": "Egypt",
    "44130": "Ivory Coast",
    "44131": "Norway",
    "44132": "New Zealand",
    "44133": "Iraq",
    "44134": "Paraguay",
    "44136": "Panama",
    "44137": "Sweden",
    "44138": "Ecuador",
    "44141": "Colombia",
    "44142": "Croatia",
    "44144": "Ghana",
}


def _fetch_json(url, timeout=15):
    try:
        req = Request(url, headers={"User-Agent": "Adivinat0r/2.0"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _resolve_team(name_or_abbr):
    return TEAM_NAME_MAP.get(name_or_abbr, name_or_abbr)


def _team_name_from_match(home_or_away):
    name_list = home_or_away.get("TeamName", [])
    if name_list:
        return name_list[0].get("Description", "")
    abbr = home_or_away.get("Abbreviation", "")
    return TEAM_FIFA_ID_MAP.get(abbr, abbr)


def fetch_real_results():
    data = _fetch_json(API_MATCHES)
    if not data:
        return None

    matches = []
    for m in data.get("Results", []):
        home = m.get("Home") or {}
        away = m.get("Away") or {}
        home_id = home.get("IdTeam")
        away_id = away.get("IdTeam")
        home_score = m.get("HomeTeamScore")
        away_score = m.get("AwayTeamScore")

        home_name = TEAM_FIFA_ID_MAP.get(str(home_id), _team_name_from_match(home)) if home_id else _team_name_from_match(home)
        away_name = TEAM_FIFA_ID_MAP.get(str(away_id), _team_name_from_match(away)) if away_id else _team_name_from_match(away)
        home_name = TEAM_NAME_MAP.get(home_name, home_name)
        away_name = TEAM_NAME_MAP.get(away_name, away_name)

        stage = ""
        group = ""
        if m.get("StageName"):
            stage = m["StageName"][0].get("Description", "")
        if m.get("GroupName"):
            group = m["GroupName"][0].get("Description", "")
        date = m.get("Date", "")
        match_time = m.get("MatchTime", "0'")

        played = home_score is not None and away_score is not None

        matches.append({
            "home": home_name,
            "away": away_name,
            "home_score": home_score if played else None,
            "away_score": away_score if played else None,
            "stage": stage,
            "group": group,
            "date": date,
            "match_time": match_time,
            "played": played,
        })

    return matches


def compute_standings(matches):
    groups = {}
    for m in matches:
        if not m.get("group"):
            continue
        g = m["group"].replace("Group ", "")
        if not g:
            continue
        if g not in groups:
            groups[g] = {}
        for team_key in ("home", "away"):
            t = m[team_key]
            if not t:
                continue
            t = TEAM_NAME_MAP.get(t, t)
            if t not in groups[g]:
                groups[g][t] = {"P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "Pts": 0}
            if m["played"] and m["home_score"] is not None and m["away_score"] is not None:
                hs, aw = m["home_score"], m["away_score"]
                is_home = (team_key == "home")
                gf = hs if is_home else aw
                ga = aw if is_home else hs
                groups[g][t]["P"] += 1
                groups[g][t]["GF"] += gf
                groups[g][t]["GA"] += ga
                groups[g][t]["GD"] += (gf - ga)
                if gf > ga:
                    groups[g][t]["W"] += 1
                    groups[g][t]["Pts"] += 3
                elif gf == ga:
                    groups[g][t]["D"] += 1
                    groups[g][t]["Pts"] += 1
                else:
                    groups[g][t]["L"] += 1

    for g in groups:
        sorted_teams = sorted(groups[g].items(), key=lambda x: (-x[1]["Pts"], -x[1]["GD"], -x[1]["GF"]))
        groups[g] = [{"team": t, **s} for t, s in sorted_teams]

    return groups


def fetch_fantasy_players():
    return _fetch_json(API_PLAYERS)


def get_team_player_quality(players_data, team_abbr_map=None):
    if not players_data:
        return {}
    team_scores = {}
    for p in players_data:
        team_name = p.get("team_name", p.get("team", ""))
        if not team_name:
            continue
        score = p.get("avgPoints", p.get("totalPoints", 0))
        if team_name not in team_scores:
            team_scores[team_name] = []
        team_scores[team_name].append(score)

    result = {}
    for team, scores in team_scores.items():
        if scores:
            result[team] = round(sum(scores) / len(scores), 2)
    return result


def save_real_results():
    matches = fetch_real_results()
    if matches:
        standings = compute_standings(matches)
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(RESULTS_PATH, "w") as f:
            json.dump({"matches": matches, "standings": standings}, f, indent=2, ensure_ascii=False)
        return matches, standings
    return None, None


def load_cached_results():
    try:
        with open(RESULTS_PATH) as f:
            data = json.load(f)
        return data.get("matches", []), data.get("standings", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return [], {}


def update_async(callback=None):
    def _task():
        try:
            matches, standings = save_real_results()
            fetch_and_cache_player_power()
            fetch_and_cache_power_rankings()
            count = len(matches) if matches else 0
            played = sum(1 for m in matches if m["played"]) if matches else 0
            msg = f"Resultados reales: {played}/{count} partidos jugados"
            if callback:
                callback(True, msg)
        except Exception as e:
            if callback:
                callback(False, str(e))
    t = threading.Thread(target=_task, daemon=True)
    t.start()
    return t


POWER_RANKINGS_PATH = os.path.join(DATA_DIR, "power_rankings.json")

SEED_POWER_RANKINGS = {
    "Argentina": {"attack": 8.12, "creativity": 0, "defense": 0},
    "New Zealand": {"attack": 7.80, "creativity": 0, "defense": 0},
    "France": {"attack": 7.65, "creativity": 0, "defense": 0},
    "Sweden": {"attack": 7.50, "creativity": 7.20, "defense": 0},
    "England": {"attack": 7.40, "creativity": 0, "defense": 0},
    "Norway": {"attack": 7.35, "creativity": 0, "defense": 0},
    "Ivory Coast": {"attack": 7.30, "creativity": 7.10, "defense": 0},
    "Brazil": {"attack": 7.25, "creativity": 0, "defense": 0},
    "Colombia": {"attack": 7.15, "creativity": 0, "defense": 0},
    "Iran": {"attack": 0, "creativity": 8.23, "defense": 0},
    "Germany": {"attack": 0, "creativity": 7.80, "defense": 0},
    "South Korea": {"attack": 0, "creativity": 7.60, "defense": 0},
    "Paraguay": {"attack": 0, "creativity": 7.40, "defense": 0},
    "Netherlands": {"attack": 0, "creativity": 7.30, "defense": 0},
    "Morocco": {"attack": 0, "creativity": 7.15, "defense": 0},
    "Egypt": {"attack": 0, "creativity": 7.10, "defense": 0},
    "Canada": {"attack": 0, "defense": 7.28, "creativity": 0},
    "Bosnia and Herzegovina": {"attack": 0, "defense": 7.10, "creativity": 0},
    "Austria": {"attack": 0, "defense": 6.95, "creativity": 0},
    "United States": {"attack": 0, "defense": 6.85, "creativity": 0},
    "Cape Verde": {"attack": 0, "defense": 6.70, "creativity": 6.60},
    "Mexico": {"attack": 0, "defense": 6.60, "creativity": 0},
    "Australia": {"attack": 0, "defense": 6.50, "creativity": 0},
    "Scotland": {"attack": 6.50, "defense": 0, "creativity": 0},
}


def compute_power_rankings_from_fantasy(players_data, squad_map):
    if not players_data or not squad_map:
        return SEED_POWER_RANKINGS
    from collections import defaultdict
    team_positions = defaultdict(list)
    for p in players_data:
        sid = p.get("squadId")
        team = squad_map.get(sid)
        if not team:
            continue
        team = TEAM_NAME_MAP.get(team, team)
        pos = p.get("position", "MID")
        avg = p.get("stats", {}).get("avgPoints", 0) or 0
        total = p.get("stats", {}).get("totalPoints", 0) or 0
        if total > 0:
            team_positions[team].append({"pos": pos, "avg": avg, "total": total})
    result = {}
    for team, plist in team_positions.items():
        fwds = [p for p in plist if p["pos"] in ("FWD",)]
        mids = [p for p in plist if p["pos"] in ("MID",)]
        defs = [p for p in plist if p["pos"] in ("DEF", "GK")]
        attack = round(sum(p["avg"] for p in fwds) / len(fwds), 2) if fwds else 0
        creativity = round(sum(p["avg"] for p in mids) / len(mids), 2) if mids else 0
        defense = round(sum(p["avg"] for p in defs) / len(defs), 2) if defs else 0
        if any((attack, creativity, defense)):
            result[team] = {"attack": attack, "creativity": creativity, "defense": defense}
    for team, seed in SEED_POWER_RANKINGS.items():
        if team in result:
            for k in ("attack", "creativity", "defense"):
                if result[team][k] == 0 and seed[k] > 0:
                    result[team][k] = seed[k]
        else:
            result[team] = seed
    return result


def fetch_and_cache_power_rankings():
    src = SEED_POWER_RANKINGS
    players = fetch_fantasy_players()
    squads = fetch_squad_mapping()
    if players and squads:
        src = compute_power_rankings_from_fantasy(players, squads)
    # Normalize to 0-10
    for cat in ("attack", "creativity", "defense"):
        vals = [src[t][cat] for t in src if src[t].get(cat, 0) > 0]
        mx = max(vals) if vals else 10
        for t in src:
            if t in src:
                src[t][cat] = round(min(src[t].get(cat, 0) / mx * 10, 10), 2)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(POWER_RANKINGS_PATH, "w") as f:
        json.dump(src, f, indent=2, ensure_ascii=False)
    return src


def load_power_rankings():
    try:
        with open(POWER_RANKINGS_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return SEED_POWER_RANKINGS


FETCH_SQUADS = "https://play.fifa.com/json/fantasy/squads.json"


def fetch_squad_mapping():
    data = _fetch_json(FETCH_SQUADS)
    if not data:
        return {}
    return {s["id"]: s["name"] for s in data}


def compute_team_player_power(players_data, squad_map):
    if not players_data or not squad_map:
        return {}
    from collections import defaultdict
    team_scores = defaultdict(list)
    for p in players_data:
        sid = p.get("squadId")
        team = squad_map.get(sid)
        if not team:
            continue
        total = p.get("stats", {}).get("totalPoints", 0) or 0
        if total > 0:
            team_scores[team].append(total)
    result = {}
    for team, scores in team_scores.items():
        if scores:
            result[team] = round(sum(scores) / len(scores), 2)
    return result


def fetch_and_cache_player_power():
    players = fetch_fantasy_players()
    squads = fetch_squad_mapping()
    if players and squads:
        power = compute_team_player_power(players, squads)
        if power:
            path = os.path.join(DATA_DIR, "player_power.json")
            with open(path, "w") as f:
                json.dump(power, f, indent=2, ensure_ascii=False)
            return power
    return {}


def load_player_power():
    path = os.path.join(DATA_DIR, "player_power.json")
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


if __name__ == "__main__":
    m, s = save_real_results()
    if m:
        print(f"Fetched {len(m)} matches, {sum(1 for x in m if x['played'])} played")
        for g, teams in sorted(s.items()):
            print(f"\n{g}:")
            for t in teams:
                print(f"  {t['team']}: {t['Pts']}pts ({t['W']}W {t['D']}D {t['L']}L) GF:{t['GF']} GA:{t['GA']}")
    else:
        print("Failed to fetch from API")
        m, s = load_cached_results()
        print(f"Loaded {len(m)} cached matches")
    pp = fetch_and_cache_player_power()
    if pp:
        print(f"\nPlayer power for {len(pp)} teams:")
        for t, p in sorted(pp.items(), key=lambda x: -x[1])[:10]:
            print(f"  {t}: {p}")
