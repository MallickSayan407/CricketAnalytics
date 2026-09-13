# =============================================================================
# CRICKET ANALYTICS - T20I DATA PROCESSOR
# CORRECTED VERSION
#
# Confirmed fixes:
# 1. No-balls do NOT count as legal balls.
# 2. Career runs_conceded is accumulated independently of balls_bowled.
# 3. timed out is NOT credited as a bowler wicket (already preserved).
# 4. Super Over deliveries remain excluded from normal statistics.
# =============================================================================

import csv
import json
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

ZIP_PATH = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"
)

OUTPUT_DIR = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"
)


# ============================================================
# OUTPUT SCHEMAS
# ============================================================

MATCH_FIELDS = [
    "match_id",
    "match_date",
    "gender",
    "match_type",
    "team1",
    "team2",
    "venue",
    "city",
    "country",
    "toss_winner",
    "toss_decision",
    "winner",
    "result_type",
    "result_description",
    "result_method",
    "eliminator",
    "overs",
]

MATCH_TEAM_FIELDS = [
    "match_id",
    "team_id",
    "team_name",
    "gender",
    "runs",
    "wickets",
    "total_balls",
    "allocated_balls",
    "fours",
    "sixes",
    "extras",
    "run_rate",
]

PLAYER_MATCH_FIELDS = [
    "match_id",
    "player_id",
    "player_external_id",
    "player_name",
    "team_id",
    "team_name",
    "gender",
    "batting_runs",
    "balls_faced",
    "fours",
    "sixes",
    "batting_strike_rate",
    "not_out",
    "batted",
    "balls_bowled",
    "runs_conceded",
    "wickets",
    "bowling_economy",
    "maidens",
]

PLAYER_STAT_FIELDS = [
    "player_id",
    "player_external_id",
    "player_name",
    "gender",
    "team_name",
    "matches",
    "batting_innings",
    "runs",
    "balls_faced",
    "highest_score",
    "not_outs",
    "fours",
    "sixes",
    "fifties",
    "centuries",
    "batting_average",
    "strike_rate",
    "bowling_innings",
    "balls_bowled",
    "wickets",
    "runs_conceded",
    "economy",
    "bowling_average",
    "best_bowling_wickets",
    "five_wicket_hauls",
]

TEAM_FIELDS = [
    "team_id",
    "team_name",
    "gender",
]


# ============================================================
# TEAM NORMALIZATION
# ============================================================

# Keep historical T20I country/team names as supplied by
# Cricsheet. Only normalize obvious spelling/identity aliases
# where the same team is represented under multiple names.

TEAM_NORMALIZATION = {
    "United States of America": "United States of America",
    "USA": "United States of America",
    "U.S.A.": "United States of America",

    "United Arab Emirates": "United Arab Emirates",
    "UAE": "United Arab Emirates",

    "West Indies": "West Indies",

    "Hong Kong": "Hong Kong",
    "Hong Kong, China": "Hong Kong",

    "Türkiye": "Turkey",

    "Turks and Caicos Islands": "Turks and Caicos Island",
}


def normalize_team_name(name):
    return TEAM_NORMALIZATION.get(name, name)


# ============================================================
# HELPERS
# ============================================================

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def calculate_strike_rate(runs, balls):
    if balls <= 0:
        return 0.0

    return round((runs / balls) * 100, 2)


def calculate_economy(runs, balls):
    if balls <= 0:
        return 0.0

    return round((runs / balls) * 6, 2)


def calculate_average(runs, dismissals):
    if dismissals <= 0:
        return None

    return round(runs / dismissals, 2)


def calculate_bowling_average(runs, wickets):
    if wickets <= 0:
        return None

    return round(runs / wickets, 2)


def write_csv(path, fields, rows):

    with path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def parse_match_date(info):

    dates = info.get("dates", [])

    if isinstance(dates, list):

        if not dates:
            return None

        return str(dates[0])

    if dates:
        return str(dates)

    return None


def extract_country(info):

    # Cricsheet may contain country information depending on
    # the source/version. Preserve it when present.
    country = info.get("country")

    if country:
        return country

    return ""


# ============================================================
# MAIN PROCESSOR
# ============================================================

def main():

    print("=" * 90)
    print("T20 INTERNATIONAL DATASET PROCESSOR")
    print("=" * 90)

    if not ZIP_PATH.exists():

        print("\nERROR: ZIP file not found:")
        print(ZIP_PATH)

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Master collections
    # --------------------------------------------------------

    teams = {}

    matches = []
    match_team_rows = []
    player_match_rows = []

    # --------------------------------------------------------
    # Career aggregation
    #
    # Key:
    # (player_external_id, gender)
    # --------------------------------------------------------

    career = {}

    # --------------------------------------------------------
    # Duplicate protection
    # --------------------------------------------------------

    match_ids_seen = set()

    match_team_seen = set()

    player_match_seen = set()

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    total_matches = 0
    total_deliveries = 0

    regulation_deliveries = 0
    super_over_deliveries = 0

    regulation_runs = 0
    super_over_runs = 0

    no_result_count = 0
    tied_count = 0
    super_over_match_count = 0

    # ========================================================
    # OPEN ZIP
    # ========================================================

    with zipfile.ZipFile(ZIP_PATH, "r") as z:

        members = [
            name
            for name in z.namelist()
            if name.lower().endswith(".json")
        ]

        print(f"\nJSON files: {len(members):,}")

        for index, member in enumerate(
            members,
            start=1
        ):

            with z.open(member) as f:

                data = json.load(f)

            info = data.get("info", {})

            match_id = Path(member).stem

            if match_id in match_ids_seen:

                raise ValueError(
                    f"Duplicate match ID detected: {match_id}"
                )

            match_ids_seen.add(match_id)

            total_matches += 1

            # =================================================
            # MATCH METADATA
            # =================================================

            match_date = parse_match_date(info)

            gender = info.get(
                "gender",
                "unknown"
            )

            match_type = info.get(
                "match_type",
                "T20"
            )

            raw_teams = info.get(
                "teams",
                []
            )

            normalized_teams = [
                normalize_team_name(team)
                for team in raw_teams
            ]

            if len(normalized_teams) >= 2:

                team1 = normalized_teams[0]
                team2 = normalized_teams[1]

            elif len(normalized_teams) == 1:

                team1 = normalized_teams[0]
                team2 = ""

            else:

                team1 = ""
                team2 = ""

            # -------------------------------------------------
            # Team registration
            # -------------------------------------------------

            for team_name in normalized_teams:

                team_key = (
                    team_name,
                    gender
                )

                if team_key not in teams:

                    teams[team_key] = {
                        "team_id": None,
                        "team_name": team_name,
                        "gender": gender,
                    }

            # =================================================
            # TOSS
            # =================================================

            toss = info.get(
                "toss",
                {}
            )

            toss_winner = toss.get(
                "winner"
            )

            if toss_winner:
                toss_winner = normalize_team_name(
                    toss_winner
                )

            toss_decision = toss.get(
                "decision"
            )

            # =================================================
            # OUTCOME
            # =================================================

            outcome = info.get(
                "outcome",
                {}
            )

            result = outcome.get(
                "result"
            )

            winner = outcome.get(
                "winner"
            )

            if winner:
                winner = normalize_team_name(
                    winner
                )

            eliminator = outcome.get(
                "eliminator"
            )

            if eliminator:
                eliminator = normalize_team_name(
                    eliminator
                )

            result_method = outcome.get(
                "method"
            )

            result_description = ""

            if result == "winner":

                result_type = "WINNER"

                match_status = "COMPLETED"

                result_description = (
                    f"{winner} won"
                    if winner
                    else "Winner recorded"
                )

            elif result == "tie":

                result_type = "TIED"

                tied_count += 1

                # A Super Over determines the winner but the
                # underlying regulation match remains a tie.
                if eliminator:

                    winner = eliminator

                    result_description = (
                        f"Tied; {eliminator} won "
                        f"via Super Over"
                    )

                else:

                    result_description = (
                        "Match tied"
                    )

                match_status = "COMPLETED"

            elif result == "no result":

                result_type = "NO_RESULT"

                match_status = "NO_RESULT"

                winner = None

                no_result_count += 1

                result_description = (
                    "No result"
                )

            elif result == "draw":

                result_type = "DRAW"

                match_status = "COMPLETED"

                result_description = (
                    "Match drawn"
                )

            else:

                # Some Cricsheet records can provide an outcome
                # winner without an explicit result.
                if winner:

                    result_type = "WINNER"

                    match_status = "COMPLETED"

                    result_description = (
                        f"{winner} won"
                    )

                else:

                    result_type = "UNKNOWN"

                    match_status = "COMPLETED"

                    result_description = (
                        "Result not specified"
                    )

            # =================================================
            # VENUE / CITY
            # =================================================

            venue = info.get(
                "venue",
                ""
            )

            city = info.get(
                "city",
                ""
            )

            country = extract_country(
                info
            )

            # =================================================
            # OVERS
            # =================================================

            overs = info.get(
                "overs"
            )

            # Most T20Is are 20 overs, but don't force 20
            # because shortened matches can have fewer.
            if overs is None:

                overs_value = 20

            else:

                overs_value = safe_int(
                    overs
                )

            # =================================================
            # SUPER OVER DETECTION
            # =================================================

            innings = data.get(
                "innings",
                []
            )

            super_over_count = sum(
                1
                for innings_data in innings
                if innings_data.get(
                    "super_over",
                    False
                )
            )

            if super_over_count > 0:

                super_over_match_count += 1

            # =================================================
            # MATCH-LEVEL PLAYER DATA
            # =================================================

            player_match = {}

            # -------------------------------------------------
            # Match-level dismissed batter tracking
            # -------------------------------------------------

            dismissed_batters = set()

            # -------------------------------------------------
            # Match-team statistics
            # -------------------------------------------------

            team_stats = {}

            for team_name in normalized_teams:

                team_stats[team_name] = {
                    "runs": 0,
                    "wickets": 0,
                    "total_balls": 0,
                    "allocated_balls": 0,
                    "fours": 0,
                    "sixes": 0,
                    "extras": 0,
                }

            # =================================================
            # PROCESS INNINGS
            # =================================================

            for innings_data in innings:

                is_super_over = bool(
                    innings_data.get(
                        "super_over",
                        False
                    )
                )

                batting_team = normalize_team_name(
                    innings_data.get(
                        "team",
                        ""
                    )
                )

                if batting_team not in team_stats:

                    team_stats[batting_team] = {
                        "runs": 0,
                        "wickets": 0,
                        "total_balls": 0,
                        "allocated_balls": 0,
                        "fours": 0,
                        "sixes": 0,
                        "extras": 0,
                    }

                overs_data = innings_data.get(
                    "overs",
                    []
                )

                # -------------------------------------------------
                # Determine bowling team
                # -------------------------------------------------

                bowling_team = None

                for candidate in normalized_teams:

                    if candidate != batting_team:

                        bowling_team = candidate

                        break

                # =================================================
                # OVERS
                # =================================================

                for over_data in overs_data:

                    over_number = safe_int(
                        over_data.get(
                            "over",
                            0
                        )
                    )

                    deliveries = over_data.get(
                        "deliveries",
                        []
                    )

                    # =================================================
                    # DELIVERIES
                    # =================================================

                    for delivery in deliveries:

                        total_deliveries += 1

                        runs = delivery.get(
                            "runs",
                            {}
                        )

                        batter_runs = safe_int(
                            runs.get(
                                "batter",
                                0
                            )
                        )

                        extras_runs = safe_int(
                            runs.get(
                                "extras",
                                0
                            )
                        )

                        total_runs = safe_int(
                            runs.get(
                                "total",
                                0
                            )
                        )

                        if is_super_over:

                            super_over_deliveries += 1
                            super_over_runs += total_runs

                        else:

                            regulation_deliveries += 1
                            regulation_runs += total_runs

                        # -------------------------------------------------
                        # Team statistics
                        # -------------------------------------------------

                        if not is_super_over:

                            team_stats[batting_team][
                                "runs"
                            ] += total_runs

                            team_stats[batting_team][
                                "extras"
                            ] += extras_runs

                        # -------------------------------------------------
                        # Extras
                        # -------------------------------------------------

                        delivery_extras = delivery.get(
                            "extras",
                            {}
                        )

                        # A legal ball is neither a wide nor a no-ball.
                        # This rule is used consistently for balls faced,
                        # balls bowled, team legal balls and maidens.
                        is_wide = "wides" in delivery_extras
                        is_no_ball = "noballs" in delivery_extras
                        is_legal_ball = (
                            not is_wide
                            and not is_no_ball
                        )

                        if not is_super_over:

                            # Team extras are already represented by
                            # runs.extras above.
                            pass

                        # -------------------------------------------------
                        # Batter
                        # -------------------------------------------------

                        batter = delivery.get(
                            "batter"
                        )

                        if batter:

                            player_key = (
                                batter,
                                gender
                            )

                            if player_key not in player_match:

                                player_match[player_key] = {
                                    "name": batter,
                                    "gender": gender,
                                    "team_name": batting_team,

                                    "batting_runs": 0,
                                    "balls_faced": 0,
                                    "fours": 0,
                                    "sixes": 0,

                                    "balls_bowled": 0,
                                    "runs_conceded": 0,
                                    "wickets": 0,
                                    "maidens": 0,

                                    "batted": False,
                                }

                            # Super Over excluded from normal
                            # player statistics.
                            if not is_super_over:

                                player_match[player_key][
                                    "batting_runs"
                                ] += batter_runs

                                player_match[player_key][
                                    "batted"
                                ] = True

                                # -------------------------------------------------
                                # Balls faced
                                #
                                # A delivery counts as a ball faced unless it
                                # is a wide.
                                # -------------------------------------------------

                                if is_legal_ball:

                                    player_match[player_key][
                                        "balls_faced"
                                    ] += 1

                                if batter_runs == 4:

                                    player_match[player_key][
                                        "fours"
                                    ] += 1

                                if batter_runs == 6:

                                    player_match[player_key][
                                        "sixes"
                                    ] += 1

                        # -------------------------------------------------
                        # Bowler
                        # -------------------------------------------------

                        bowler = delivery.get(
                            "bowler"
                        )

                        if bowler:

                            player_key = (
                                bowler,
                                gender
                            )

                            if player_key not in player_match:

                                player_match[player_key] = {
                                    "name": bowler,
                                    "gender": gender,
                                    "team_name": bowling_team or "",

                                    "batting_runs": 0,
                                    "balls_faced": 0,
                                    "fours": 0,
                                    "sixes": 0,

                                    "balls_bowled": 0,
                                    "runs_conceded": 0,
                                    "wickets": 0,
                                    "maidens": 0,

                                    "batted": False,
                                }

                            if not is_super_over:

                                # Wides and no-balls do not count as legal balls.
                                if is_legal_ball:

                                    player_match[player_key][
                                        "balls_bowled"
                                    ] += 1

                                # Bowler runs exclude byes and leg-byes.
                                bowler_runs = batter_runs

                                bowler_runs += safe_int(
                                    delivery_extras.get(
                                        "wides",
                                        0
                                    )
                                )

                                bowler_runs += safe_int(
                                    delivery_extras.get(
                                        "noballs",
                                        0
                                    )
                                )

                                player_match[player_key][
                                    "runs_conceded"
                                ] += bowler_runs

                        # -------------------------------------------------
                        # Wickets
                        # -------------------------------------------------

                        delivery_wickets = delivery.get(
                            "wickets",
                            []
                        )

                        if delivery_wickets:

                            for wicket in delivery_wickets:

                                kind = wicket.get(
                                    "kind",
                                    ""
                                )

                                player_out = wicket.get(
                                    "player_out"
                                )

                                # Count team wickets for all genuine
                                # dismissals except retirements/hurt.
                                if not is_super_over:

                                    if kind not in {
                                        "retired hurt",
                                        "retired not out"
                                    }:

                                        team_stats[batting_team][
                                            "wickets"
                                        ] += 1

                                    if player_out:

                                        dismissed_batters.add(
                                            player_out
                                        )

                                # Bowler credited wickets.
                                bowler_not_credited = {
                                    "run out",
                                    "retired hurt",
                                    "retired not out",
                                    "obstructing the field",
                                    "retired out",
                                    "timed out"
                                }

                                if (
                                    not is_super_over
                                    and kind not in bowler_not_credited
                                    and bowler
                                ):

                                    player_key = (
                                        bowler,
                                        gender
                                    )

                                    if player_key in player_match:

                                        player_match[player_key][
                                            "wickets"
                                        ] += 1

            # =================================================
            # MAIDENS
            # =================================================

            # Determine maidens from completed regulation overs.
            #
            # A maiden is an over with zero runs from the
            # bowler. We calculate this directly from deliveries.

            for innings_data in innings:

                if innings_data.get(
                    "super_over",
                    False
                ):

                    continue

                batting_team = normalize_team_name(
                    innings_data.get(
                        "team",
                        ""
                    )
                )

                bowling_team = None

                for candidate in normalized_teams:

                    if candidate != batting_team:

                        bowling_team = candidate

                        break

                for over_data in innings_data.get(
                    "overs",
                    []
                ):

                    over_runs = 0
                    legal_balls = 0
                    bowler_names = set()

                    for delivery in over_data.get(
                        "deliveries",
                        []
                    ):

                        runs = delivery.get(
                            "runs",
                            {}
                        )

                        over_runs += safe_int(
                            runs.get(
                                "total",
                                0
                            )
                        )

                        delivery_extras = delivery.get(
                            "extras",
                            {}
                        )

                        if (
                            "wides" not in delivery_extras
                            and "noballs" not in delivery_extras
                        ):

                            legal_balls += 1

                        bowler = delivery.get(
                            "bowler"
                        )

                        if bowler:

                            bowler_names.add(
                                bowler
                            )

                    # Only normal 6-ball equivalent overs count as
                    # maidens here. Partial rain-shortened overs are
                    # not treated as maidens.
                    if (
                        over_runs == 0
                        and legal_balls >= 6
                        and len(bowler_names) == 1
                    ):

                        bowler = next(
                            iter(bowler_names)
                        )

                        player_key = (
                            bowler,
                            gender
                        )

                        if player_key in player_match:

                            player_match[player_key][
                                "maidens"
                            ] += 1

            # =================================================
            # MATCH TEAM ROWS
            # =================================================

            for team_name, stats in team_stats.items():

                if team_name == "":

                    continue

                runs = stats["runs"]

                wickets = stats["wickets"]

                total_balls = stats["total_balls"]

                # -------------------------------------------------
                # Recalculate legal balls from innings directly.
                # -------------------------------------------------

                legal_balls = 0

                for innings_data in innings:

                    if innings_data.get(
                        "super_over",
                        False
                    ):

                        continue

                    innings_team = normalize_team_name(
                        innings_data.get(
                            "team",
                            ""
                        )
                    )

                    if innings_team != team_name:

                        continue

                    for over_data in innings_data.get(
                        "overs",
                        []
                    ):

                        for delivery in over_data.get(
                            "deliveries",
                            []
                        ):

                            delivery_extras = delivery.get(
                                "extras",
                                {}
                            )

                            if (
                                "wides" not in delivery_extras
                                and "noballs" not in delivery_extras
                            ):

                                legal_balls += 1

                total_balls = legal_balls

                # -------------------------------------------------
                # Allocated balls
                #
                # For T20 statistics we use the actual legal balls
                # bowled by the team, capped at 120 per completed
                # innings where appropriate.
                #
                # For shortened matches, actual legal balls remain
                # the source of truth.
                # -------------------------------------------------

                allocated_balls = total_balls

                # -------------------------------------------------
                # Fours / sixes
                # -------------------------------------------------

                fours = 0
                sixes = 0

                for player_key, pdata in player_match.items():

                    if pdata["team_name"] != team_name:

                        continue

                    fours += pdata["fours"]
                    sixes += pdata["sixes"]

                run_rate = (
                    round(
                        runs / (total_balls / 6),
                        2
                    )
                    if total_balls > 0
                    else 0.0
                )

                team_key = (
                    match_id,
                    team_name
                )

                if team_key in match_team_seen:

                    raise ValueError(
                        f"Duplicate match-team row: {team_key}"
                    )

                match_team_seen.add(
                    team_key
                )

                match_team_rows.append({
                    "match_id": match_id,
                    "team_id": "",
                    "team_name": team_name,
                    "gender": gender,
                    "runs": runs,
                    "wickets": wickets,
                    "total_balls": total_balls,
                    "allocated_balls": allocated_balls,
                    "fours": fours,
                    "sixes": sixes,
                    "extras": stats["extras"],
                    "run_rate": run_rate,
                })

            # =================================================
            # PLAYER MATCH ROWS
            # =================================================

            registry = info.get(
                "registry",
                {}
            )

            people_registry = registry.get(
                "people",
                {}
            )

            players_by_team = info.get(
                "players",
                {}
            )

            # Build a player -> team map from Cricsheet metadata.
            player_team_map = {}

            for raw_team, players in players_by_team.items():

                normalized_team = normalize_team_name(
                    raw_team
                )

                for player in players:

                    player_team_map[
                        player
                    ] = normalized_team

            for player_key, pdata in player_match.items():

                player_name = pdata["name"]

                team_name = player_team_map.get(
                    player_name,
                    pdata["team_name"]
                )

                external_id = people_registry.get(
                    player_name
                )

                if not external_id:

                    raise ValueError(
                        f"Missing registry ID for "
                        f"{player_name} in {match_id}"
                    )

                player_unique_key = (
                    match_id,
                    external_id
                )

                if player_unique_key in player_match_seen:

                    raise ValueError(
                        f"Duplicate player-match row: "
                        f"{player_unique_key}"
                    )

                player_match_seen.add(
                    player_unique_key
                )

                batting_runs_value = pdata[
                    "batting_runs"
                ]

                balls_faced_value = pdata[
                    "balls_faced"
                ]

                balls_bowled_value = pdata[
                    "balls_bowled"
                ]

                runs_conceded_value = pdata[
                    "runs_conceded"
                ]

                wickets_value = pdata[
                    "wickets"
                ]

                batting_strike_rate = calculate_strike_rate(
                    batting_runs_value,
                    balls_faced_value
                )

                bowling_economy = calculate_economy(
                    runs_conceded_value,
                    balls_bowled_value
                )

                not_out = (
                    pdata["batted"]
                    and player_name not in dismissed_batters
                )

                player_match_rows.append({
                    "match_id": match_id,
                    "player_id": "",
                    "player_external_id": external_id,
                    "player_name": player_name,
                    "team_id": "",
                    "team_name": team_name,
                    "gender": gender,
                    "batting_runs": batting_runs_value,
                    "balls_faced": balls_faced_value,
                    "fours": pdata["fours"],
                    "sixes": pdata["sixes"],
                    "batting_strike_rate": batting_strike_rate,
                    "not_out": str(
                        bool(not_out)
                    ).lower(),
                    "batted": str(
                        bool(pdata["batted"])
                    ).lower(),
                    "balls_bowled": balls_bowled_value,
                    "runs_conceded": runs_conceded_value,
                    "wickets": wickets_value,
                    "bowling_economy": bowling_economy,
                    "maidens": pdata["maidens"],
                })

                # =================================================
                # CAREER AGGREGATION
                # =================================================

                career_key = (
                    external_id,
                    gender
                )

                if career_key not in career:

                    career[career_key] = {
                        "external_id": external_id,
                        "name": player_name,
                        "gender": gender,
                        "team_name": team_name,

                        "matches": 0,

                        "batting_innings": 0,
                        "runs": 0,
                        "balls_faced": 0,
                        "highest_score": 0,
                        "not_outs": 0,
                        "fours": 0,
                        "sixes": 0,
                        "fifties": 0,
                        "centuries": 0,

                        "bowling_innings": 0,
                        "balls_bowled": 0,
                        "wickets": 0,
                        "runs_conceded": 0,

                        "best_bowling_wickets": 0,
                        "five_wicket_hauls": 0,

                        "dismissals": 0,
                    }

                c = career[career_key]

                c["matches"] += 1

                if pdata["batted"]:

                    c["batting_innings"] += 1

                    c["runs"] += batting_runs_value

                    c["balls_faced"] += balls_faced_value

                    c["highest_score"] = max(
                        c["highest_score"],
                        batting_runs_value
                    )

                    c["fours"] += pdata["fours"]

                    c["sixes"] += pdata["sixes"]

                    if not_out:

                        c["not_outs"] += 1

                    else:

                        c["dismissals"] += 1

                    if (
                        batting_runs_value >= 100
                    ):

                        c["centuries"] += 1

                    elif (
                        batting_runs_value >= 50
                    ):

                        c["fifties"] += 1

                if balls_bowled_value > 0:

                    c["bowling_innings"] += 1

                    c["balls_bowled"] += (
                        balls_bowled_value
                    )

                    c["wickets"] += (
                        wickets_value
                    )

                    c["best_bowling_wickets"] = max(
                        c["best_bowling_wickets"],
                        wickets_value
                    )

                    if wickets_value >= 5:

                        c["five_wicket_hauls"] += 1

                # Runs conceded are independent of whether a legal ball
                # was recorded in this player-match row. This preserves
                # runs from edge cases such as a bowler conceding runs
                # on a non-legal delivery without a legal ball.
                c["runs_conceded"] += (
                    runs_conceded_value
                )

            # =================================================
            # MATCH ROW
            # =================================================

            matches.append({
                "match_id": match_id,
                "match_date": match_date,
                "gender": gender,
                "match_type": match_type,
                "team1": team1,
                "team2": team2,
                "venue": venue,
                "city": city,
                "country": country,
                "toss_winner": toss_winner,
                "toss_decision": toss_decision,
                "winner": winner,
                "result_type": result_type,
                "result_description": result_description,
                "result_method": result_method,
                "eliminator": eliminator,
                "overs": overs_value,
            })

            # -------------------------------------------------
            # Progress
            # -------------------------------------------------

            if index % 500 == 0:

                print(
                    f"Processed {index:,} / "
                    f"{len(members):,} matches..."
                )

    # ========================================================
    # ASSIGN DETERMINISTIC TEAM IDs
    # ========================================================

    sorted_team_keys = sorted(
        teams.keys(),
        key=lambda x: (
            x[1],
            x[0].lower()
        )
    )

    team_id_map = {}

    for index, team_key in enumerate(
        sorted_team_keys,
        start=1
    ):

        team_id_map[team_key] = index

        teams[team_key]["team_id"] = index

    # ========================================================
    # UPDATE MATCH TEAM IDs
    # ========================================================

    for row in match_team_rows:

        team_key = (
            row["team_name"],
            row["gender"]
        )

        row["team_id"] = team_id_map[
            team_key
        ]

    # ========================================================
    # UPDATE PLAYER TEAM IDs
    # ========================================================

    # Player IDs are assigned later during MySQL import, so
    # leave player_id empty in processed CSVs.
    #
    # Team IDs are deterministic within this dataset.

    for row in player_match_rows:

        team_key = (
            row["team_name"],
            row["gender"]
        )

        row["team_id"] = team_id_map.get(
            team_key,
            ""
        )

    # ========================================================
    # CAREER CSV
    # ========================================================

    player_statistics = []

    for career_key, c in career.items():

        batting_average = calculate_average(
            c["runs"],
            c["dismissals"]
        )

        strike_rate = calculate_strike_rate(
            c["runs"],
            c["balls_faced"]
        )

        economy = calculate_economy(
            c["runs_conceded"],
            c["balls_bowled"]
        )

        bowling_average = calculate_bowling_average(
            c["runs_conceded"],
            c["wickets"]
        )

        player_statistics.append({
            "player_id": "",
            "player_external_id": c["external_id"],
            "player_name": c["name"],
            "gender": c["gender"],
            "team_name": c["team_name"],
            "matches": c["matches"],
            "batting_innings": c["batting_innings"],
            "runs": c["runs"],
            "balls_faced": c["balls_faced"],
            "highest_score": c["highest_score"],
            "not_outs": c["not_outs"],
            "fours": c["fours"],
            "sixes": c["sixes"],
            "fifties": c["fifties"],
            "centuries": c["centuries"],
            "batting_average": batting_average,
            "strike_rate": strike_rate,
            "bowling_innings": c["bowling_innings"],
            "balls_bowled": c["balls_bowled"],
            "wickets": c["wickets"],
            "runs_conceded": c["runs_conceded"],
            "economy": economy,
            "bowling_average": bowling_average,
            "best_bowling_wickets": c[
                "best_bowling_wickets"
            ],
            "five_wicket_hauls": c[
                "five_wicket_hauls"
            ],
        })

    # ========================================================
    # TEAM CSV
    # ========================================================

    team_rows = []

    for team_key in sorted(
        teams.keys(),
        key=lambda x: (
            x[1],
            x[0].lower()
        )
    ):

        team_rows.append(
            teams[team_key]
        )

    # ========================================================
    # SORT OUTPUT
    # ========================================================

    matches.sort(
        key=lambda x: (
            x["match_date"] or "",
            x["match_id"]
        )
    )

    match_team_rows.sort(
        key=lambda x: (
            x["match_id"],
            x["team_name"]
        )
    )

    player_match_rows.sort(
        key=lambda x: (
            x["match_id"],
            x["team_name"],
            x["player_name"]
        )
    )

    player_statistics.sort(
        key=lambda x: (
            x["gender"],
            -safe_int(x["runs"]),
            x["player_name"]
        )
    )

    # ========================================================
    # WRITE FILES
    # ========================================================

    write_csv(
        OUTPUT_DIR / "teams.csv",
        TEAM_FIELDS,
        team_rows
    )

    write_csv(
        OUTPUT_DIR / "matches.csv",
        MATCH_FIELDS,
        matches
    )

    write_csv(
        OUTPUT_DIR / "match_team_stats.csv",
        MATCH_TEAM_FIELDS,
        match_team_rows
    )

    write_csv(
        OUTPUT_DIR / "player_match_performance.csv",
        PLAYER_MATCH_FIELDS,
        player_match_rows
    )

    write_csv(
        OUTPUT_DIR / "player_statistics.csv",
        PLAYER_STAT_FIELDS,
        player_statistics
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 90)
    print("PROCESSING COMPLETE")
    print("=" * 90)

    print(
        f"\nMatches:                       "
        f"{len(matches):,}"
    )

    print(
        f"Teams:                         "
        f"{len(team_rows):,}"
    )

    print(
        f"Match-team rows:               "
        f"{len(match_team_rows):,}"
    )

    print(
        f"Player-match rows:             "
        f"{len(player_match_rows):,}"
    )

    print(
        f"Career player rows:            "
        f"{len(player_statistics):,}"
    )

    print(
        f"\nTotal deliveries:              "
        f"{total_deliveries:,}"
    )

    print(
        f"Regulation deliveries:         "
        f"{regulation_deliveries:,}"
    )

    print(
        f"Super Over deliveries:         "
        f"{super_over_deliveries:,}"
    )

    print(
        f"\nRegulation runs:                "
        f"{regulation_runs:,}"
    )

    print(
        f"Super Over runs excluded:      "
        f"{super_over_runs:,}"
    )

    print(
        f"\nNo-result matches:              "
        f"{no_result_count:,}"
    )

    print(
        f"Tied matches:                   "
        f"{tied_count:,}"
    )

    print(
        f"Matches with Super Over:        "
        f"{super_over_match_count:,}"
    )

    print(
        f"\nOutput directory:"
    )

    print(
        OUTPUT_DIR
    )

    print("\nFiles created:")

    for filename in [
        "teams.csv",
        "matches.csv",
        "match_team_stats.csv",
        "player_match_performance.csv",
        "player_statistics.csv",
    ]:

        path = OUTPUT_DIR / filename

        print(
            f"  {filename:<35} "
            f"{path.stat().st_size:,} bytes"
        )

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()