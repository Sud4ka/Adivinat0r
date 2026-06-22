ALTITUDE_MAP = {
    "Bolivia": 3640, "Ecuador": 2850, "Colombia": 2600, "Mexico": 2240,
    "Ethiopia": 2350, "Kenya": 1795, "South Africa": 1750, "Peru": 1540,
    "Chile": 570, "Brazil": 760, "Argentina": 250, "United States": 760,
    "Canada": 110, "Japan": 40, "South Korea": 60, "Qatar": 30,
    "Russia": 150, "Germany": 35, "France": 50, "England": 15,
    "Spain": 650, "Italy": 100, "Netherlands": 5, "Portugal": 100,
    "Belgium": 10, "Switzerland": 500, "Croatia": 130, "Sweden": 15,
    "Denmark": 10, "Poland": 110, "Austria": 260, "Hungary": 100,
    "Serbia": 120, "Greece": 50, "Turkey": 50, "Romania": 80,
    "Bulgaria": 150, "Scotland": 50, "Ireland": 20, "Norway": 10,
    "Wales": 50, "Nigeria": 360, "Ghana": 200, "Cameroon": 320,
    "Morocco": 250, "Senegal": 50, "Algeria": 400, "Tunisia": 150,
    "Ivory Coast": 80, "Angola": 300, "Mali": 340, "Egypt": 100,
    "Australia": 330, "New Zealand": 20, "Iran": 1200, "Saudi Arabia": 600,
    "Iraq": 100, "China": 1500, "South Korea": 60, "Japan": 40,
    "Indonesia": 150, "Uruguay": 30, "Paraguay": 130, "Costa Rica": 1200,
    "Honduras": 1000, "Panama": 100, "Jamaica": 20, "Haiti": 30,
    "El Salvador": 650, "Slovakia": 200, "Ukraine": 180, "Slovenia": 300,
    "Bosnia": 500, "Czech Republic": 350, "Soviet Union": 150,
    "Yugoslavia": 200, "Czechoslovakia": 300, "Zaire": 600,
    "Togo": 200, "Trinidad and Tobago": 50, "United Arab Emirates": 30,
}

CLIMATE_ZONES = {
    "Argentina": "temperate", "Brazil": "tropical", "Uruguay": "temperate",
    "Colombia": "tropical", "Chile": "temperate", "Peru": "tropical",
    "Ecuador": "tropical", "Paraguay": "subtropical", "Bolivia": "tropical",
    "Mexico": "subtropical", "United States": "temperate", "Canada": "cold",
    "Costa Rica": "tropical", "Honduras": "tropical", "Panama": "tropical",
    "Jamaica": "tropical", "Haiti": "tropical", "El Salvador": "tropical",
    "England": "temperate", "France": "temperate", "Germany": "temperate",
    "Italy": "mediterranean", "Spain": "mediterranean", "Portugal": "mediterranean",
    "Netherlands": "temperate", "Belgium": "temperate", "Switzerland": "temperate",
    "Sweden": "cold", "Denmark": "temperate", "Norway": "cold",
    "Poland": "cold", "Austria": "temperate", "Hungary": "temperate",
    "Croatia": "mediterranean", "Serbia": "temperate", "Greece": "mediterranean",
    "Turkey": "mediterranean", "Romania": "temperate", "Bulgaria": "temperate",
    "Scotland": "temperate", "Ireland": "temperate", "Wales": "temperate",
    "Soviet Union": "cold", "Yugoslavia": "temperate", "Czechoslovakia": "temperate",
    "Russia": "cold", "Ukraine": "cold", "Slovakia": "cold", "Slovenia": "temperate",
    "Bosnia": "temperate", "Czech Republic": "temperate",
    "Nigeria": "tropical", "Ghana": "tropical", "Cameroon": "tropical",
    "Morocco": "mediterranean", "Senegal": "tropical", "Algeria": "arid",
    "Tunisia": "mediterranean", "Ivory Coast": "tropical", "Angola": "tropical",
    "Mali": "arid", "Egypt": "arid", "South Africa": "subtropical",
    "Zaire": "tropical", "Togo": "tropical",
    "Australia": "subtropical", "New Zealand": "temperate",
    "Iran": "arid", "Saudi Arabia": "arid", "Japan": "temperate",
    "South Korea": "temperate", "China": "temperate", "Iraq": "arid",
    "Indonesia": "tropical", "Qatar": "arid", "United Arab Emirates": "arid",
    "Kuwait": "arid",
}

CLIMATE_PENALTY = {
    "cold": 1.1, "temperate": 1.0, "mediterranean": 1.0,
    "subtropical": 0.95, "tropical": 0.9, "arid": 0.85
}


def get_venue_altitude(host: str) -> int:
    return ALTITUDE_MAP.get(host, 100)


def get_altitude_penalty(team: str, venue_altitude: int) -> float:
    team_altitude = ALTITUDE_MAP.get(team, 100)
    diff = abs(venue_altitude - team_altitude)
    if diff < 500:
        return 1.0
    elif diff < 1500:
        return 0.97
    elif diff < 2500:
        return 0.93
    else:
        return 0.88


def get_climate_penalty(team_a: str, team_b: str, host: str) -> float:
    host_zone = CLIMATE_ZONES.get(host, "temperate")
    zone_a = CLIMATE_ZONES.get(team_a, "temperate")
    zone_b = CLIMATE_ZONES.get(team_b, "temperate")
    penalty_a = CLIMATE_PENALTY.get(zone_a, 1.0) / CLIMATE_PENALTY.get(host_zone, 1.0)
    penalty_b = CLIMATE_PENALTY.get(zone_b, 1.0) / CLIMATE_PENALTY.get(host_zone, 1.0)
    return (penalty_a / max(0.01, penalty_b))


def get_rest_days_factor(team: str, match_number: int = 0) -> float:
    base = 1.0
    penalty = max(0, match_number - 3) * 0.02
    return base - min(0.15, penalty)


def get_travel_factor(team_a: str, team_b: str, host: str) -> float:
    base_team_a = ALTITUDE_MAP.get(team_a, 100)
    base_team_b = ALTITUDE_MAP.get(team_b, 100)
    host_alt = ALTITUDE_MAP.get(host, 100)
    travel_a = abs(base_team_a - host_alt) / 5000.0
    travel_b = abs(base_team_b - host_alt) / 5000.0
    return max(0.85, 1.0 - travel_a) / max(0.85, 1.0 - travel_b)


def compute_env_score(team_a: str, team_b: str, host: str, match_number: int = 0) -> float:
    venue_alt = get_venue_altitude(host)
    alt_a = get_altitude_penalty(team_a, venue_alt)
    alt_b = get_altitude_penalty(team_b, venue_alt)
    env_alt = alt_a / max(0.01, alt_b)

    env_climate = get_climate_penalty(team_a, team_b, host)

    rest_a = get_rest_days_factor(team_a, match_number)
    rest_b = get_rest_days_factor(team_b, match_number)
    env_rest = rest_a / max(0.01, rest_b)

    env_travel = get_travel_factor(team_a, team_b, host)

    raw = (env_alt * 0.3 + env_climate * 0.25 + env_rest * 0.25 + env_travel * 0.2)
    return max(0.5, min(2.0, raw))
