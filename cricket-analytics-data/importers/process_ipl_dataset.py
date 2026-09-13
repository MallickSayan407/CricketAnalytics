import csv
import io
import json
import os
import zipfile
from collections import defaultdict
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

ZIP_PATH = r"D:\CricketAnalytics\cricket-analytics-data\raw\ipl\ipl_json.zip"

OUTPUT_DIR = r"D:\CricketAnalytics\cricket-analytics-data\processed\ipl"

# Set to None for the complete dataset.
# Set to 10/50/etc. for a development pilot.
PROCESS_LIMIT = None


# ============================================================================
# TEAM NORMALIZATION
# ============================================================================

# Historical Cricsheet names -> canonical franchise names.
#
# We preserve the historical name in the raw JSON, but use the canonical
# identity for analytics and database relationships.

TEAM_NORMALIZATION = {
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Royal Challengers Bengaluru": "Royal Challengers Bengaluru",

    "Kings XI Punjab": "Punjab Kings",
    "Punjab Kings": "Punjab Kings",

    "Delhi Daredevils": "Delhi Capitals",
    "Delhi Capitals": "Delhi Capitals",

    "Deccan Chargers": "Deccan Chargers",

    "Gujarat Lions": "Gujarat Lions",
    "Gujarat Titans": "Gujarat Titans",

    "Rising Pune Supergiant": "Rising Pune Supergiant",
    "Rising Pune Supergiants": "Rising Pune Supergiant",

    "Pune Warriors": "Pune Warriors",

    "Kochi Tuskers Kerala": "Kochi Tuskers Kerala",

    "Mumbai Indians": "Mumbai Indians",
    "Kolkata Knight Riders": "Kolkata Knight Riders",
    "Chennai Super Kings": "Chennai Super Kings",
    "Rajasthan Royals": "Rajasthan Royals",
    "Sunrisers Hyderabad": "Sunrisers Hyderabad",
    "Lucknow Super Giants": "Lucknow Super Giants",
}


# ============================================================================
# TEAM SHORT NAMES
# ============================================================================

TEAM_SHORT_NAMES = {
    "Mumbai Indians": "MI",
    "Kolkata Knight Riders": "KKR",
    "Chennai Super Kings": "CSK",
    "Rajasthan Royals": "RR",
    "Royal Challengers Bengaluru": "RCB",
    "Sunrisers Hyderabad": "SRH",
    "Punjab Kings": "PBKS",
    "Delhi Capitals": "DC",
    "Deccan Chargers": "DEC",
    "Gujarat Titans": "GT",
    "Gujarat Lions": "GL",
    "Lucknow Super Giants": "LSG",
    "Pune Warriors": "PWI",
    "Rising Pune Supergiant": "RPS",
    "Kochi Tuskers Kerala": "KTK",
}


# ============================================================================
# HELPERS
# ============================================================================

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_team(team_name):
    return TEAM_NORMALIZATION.get(
        team_name,
        team_name
    )


def normalize_season(season):
    return str(season)


def normalize_stage(stage):
    """Normalize Cricsheet IPL event stages for analytics."""
    if stage is None:
        return "League"

    value = str(stage).strip()
    if not value:
        return "League"

    normalized = " ".join(value.lower().split())

    stage_map = {
        "league": "League",
        "league stage": "League",
        "qualifier 1": "Qualifier 1",
        "qualifier1": "Qualifier 1",
        "eliminator": "Eliminator",
        "qualifier 2": "Qualifier 2",
        "qualifier2": "Qualifier 2",
        "final": "Final",
    }

    return stage_map.get(normalized, value)


def get_match_stage(info):
    """Read Cricsheet event.stage; default to League when absent."""
    event = info.get("event", {})
    if not isinstance(event, dict):
        return "League"
    return normalize_stage(event.get("stage"))


def get_match_date(info):
    dates = info.get("dates", [])

    if not dates:
        return ""

    return str(dates[0])


def calculate_strike_rate(runs, balls):
    if balls <= 0:
        return 0.0

    return round(
        (runs / balls) * 100,
        2
    )


def calculate_economy(runs, balls):
    if balls <= 0:
        return 0.0

    return round(
        (runs * 6) / balls,
        2
    )


def is_legal_delivery(delivery):
    extras = delivery.get("extras", {})

    return (
        "wides" not in extras
        and "noballs" not in extras
    )


def is_super_over(innings):
    return innings.get("super_over") is True


def get_delivery_total_runs(delivery):
    runs = delivery.get("runs", {})

    return safe_int(
        runs.get("total")
    )


# ============================================================================
# PLAYER MATCH AGGREGATION
# ============================================================================

def process_player_match_performance(
    match_id,
    innings_list,
    player_registry,
    team_name_by_player
):
    """
    Produces one performance record per player per match.

    Super Over innings are deliberately excluded from normal player
    statistics.

    Player-team association is taken from the match's info.players mapping.
    """

    players = defaultdict(
        lambda: {
            "player_name": "",
            "player_external_id": "",
            "team_name": "",
            "batting_runs": 0,
            "balls_faced": 0,
            "fours": 0,
            "sixes": 0,
            "balls_bowled": 0,
            "runs_conceded": 0,
            "wickets": 0,
            "maidens": 0,
            "not_out": False,
            "batted": False,
        }
    )

    # ---------------------------------------------------------------
    # Process only normal innings.
    # ---------------------------------------------------------------

    # Keep dismissals at match scope so not_out cannot be overwritten by
    # a later normal innings.
    all_dismissed_batters = set()

    for innings in innings_list:

        if is_super_over(innings):
            continue

        batting_team_raw = innings.get("team", "")
        batting_team = normalize_team(
            batting_team_raw
        )

        overs = innings.get("overs", [])

        # -----------------------------------------------------------
        # Determine batters and batting statistics.
        # -----------------------------------------------------------

        batter_balls = defaultdict(int)
        batter_runs = defaultdict(int)
        batter_fours = defaultdict(int)
        batter_sixes = defaultdict(int)

        dismissed_batters = set()

        # Bowling statistics are accumulated by bowler name.
        bowler_balls = defaultdict(int)
        bowler_runs = defaultdict(int)
        bowler_wickets = defaultdict(int)
        bowler_maidens = defaultdict(int)

        for over in overs:

            deliveries = over.get(
                "deliveries",
                []
            )

            legal_balls_in_over = 0
            runs_conceded_in_over = defaultdict(int)

            for delivery in deliveries:

                batter = delivery.get(
                    "batter",
                    ""
                )

                bowler = delivery.get(
                    "bowler",
                    ""
                )

                runs = delivery.get(
                    "runs",
                    {}
                )

                batter_run_value = safe_int(
                    runs.get("batter")
                )

                total_run_value = safe_int(
                    runs.get("total")
                )

                extras = delivery.get(
                    "extras",
                    {}
                )

                extras_total = sum(
                    safe_int(value)
                    for value in extras.values()
                    if isinstance(value, (int, float, str))
                )

                # ---------------------------------------------------
                # Batting
                # ---------------------------------------------------

                if batter:

                    players[batter]["player_name"] = batter
                    players[batter]["batted"] = True

                    batter_runs[batter] += batter_run_value

                    if batter_run_value == 4:
                        batter_fours[batter] += 1

                    elif batter_run_value == 6:
                        batter_sixes[batter] += 1

                    # A batter faces a ball unless it is a wide.
                    if "wides" not in extras:
                        batter_balls[batter] += 1

                # ---------------------------------------------------
                # Bowling
                # ---------------------------------------------------

                if bowler:

                    players[bowler]["player_name"] = bowler

                    if is_legal_delivery(delivery):
                        bowler_balls[bowler] += 1
                        legal_balls_in_over += 1

                    # For bowling runs conceded:
                    #
                    # Wides + no-balls are charged to the bowler.
                    # Byes, leg-byes and penalty runs are not.
                    bowler_extras = 0

                    if "wides" in extras:
                        bowler_extras += safe_int(
                            extras["wides"]
                        )

                    if "noballs" in extras:
                        bowler_extras += safe_int(
                            extras["noballs"]
                        )

                    bowler_runs[bowler] += (
                        batter_run_value
                        + bowler_extras
                    )

                    runs_conceded_in_over[bowler] += (
                        batter_run_value
                        + bowler_extras
                    )

                # ---------------------------------------------------
                # Wickets
                # ---------------------------------------------------

                for wicket in delivery.get(
                    "wickets",
                    []
                ):

                    player_out = wicket.get(
                        "player_out"
                    )

                    if player_out:
                        dismissed_batters.add(
                            player_out
                        )

                    wicket_kind = wicket.get(
                        "kind"
                    )

                    # Do not count retired hurt / retired out /
                    # obstructing the field as bowler wickets.
                    #
                    # Bowler credited dismissals include:
                    # caught
                    # bowled
                    # caught and bowled
                    # lbw
                    # stumped
                    # hit wicket
                    #
                    credited_wickets = {
                        "caught",
                        "bowled",
                        "caught and bowled",
                        "lbw",
                        "stumped",
                        "hit wicket",
                    }

                    if (
                        bowler
                        and wicket_kind in credited_wickets
                    ):
                        bowler_wickets[bowler] += 1

            # Keep dismissals at match scope.
            all_dismissed_batters.update(dismissed_batters)

            # -------------------------------------------------------
            # Maiden over detection
            # -------------------------------------------------------

            if legal_balls_in_over == 6:

                bowler_with_runs = [
                    bowler
                    for bowler, runs_value
                    in runs_conceded_in_over.items()
                    if runs_value > 0
                ]

                if not bowler_with_runs:

                    # Find the bowler responsible for this over.
                    over_bowlers = set()

                    for delivery in deliveries:

                        bowler = delivery.get(
                            "bowler"
                        )

                        if bowler:
                            over_bowlers.add(
                                bowler
                            )

                    if len(over_bowlers) == 1:

                        maiden_bowler = next(
                            iter(over_bowlers)
                        )

                        bowler_maidens[
                            maiden_bowler
                        ] += 1

        # -----------------------------------------------------------
        # Merge batting/bowling data into player records.
        # -----------------------------------------------------------

        for player_name in set(
            list(batter_runs.keys())
            + list(bowler_balls.keys())
        ):

            record = players[player_name]

            # Accumulate across all NORMAL innings in this match.
            # A player may bat in one innings and bowl in another, so these
            # values must never overwrite each other.
            record["batting_runs"] += batter_runs.get(player_name, 0)
            record["balls_faced"] += batter_balls.get(player_name, 0)
            record["fours"] += batter_fours.get(player_name, 0)
            record["sixes"] += batter_sixes.get(player_name, 0)

            record["balls_bowled"] += bowler_balls.get(player_name, 0)
            record["runs_conceded"] += bowler_runs.get(player_name, 0)
            record["wickets"] += bowler_wickets.get(player_name, 0)
            record["maidens"] += bowler_maidens.get(player_name, 0)

            record["not_out"] = (
                player_name not in all_dismissed_batters
                and record["batted"]
            )

            record["team_name"] = (
                team_name_by_player.get(
                    player_name,
                    batting_team
                )
            )

            record["player_external_id"] = (
                player_registry.get(
                    player_name,
                    ""
                )
            )

    output = []

    for player_name, record in players.items():

        # A player who appears only as a fielder and never bats/bowls
        # should not automatically receive a performance row.
        if (
            not record["batted"]
            and record["balls_bowled"] == 0
        ):
            continue

        output.append({
            "match_id": match_id,
            "player_external_id": record[
                "player_external_id"
            ],
            "player_name": player_name,
            "team_name": record["team_name"],
            "batting_runs": record["batting_runs"],
            "balls_faced": record["balls_faced"],
            "fours": record["fours"],
            "sixes": record["sixes"],
            "batting_strike_rate": calculate_strike_rate(
                record["batting_runs"],
                record["balls_faced"]
            ),
            "not_out": record["not_out"],
            "balls_bowled": record["balls_bowled"],
            "runs_conceded": record["runs_conceded"],
            "wickets": record["wickets"],
            "bowling_economy": calculate_economy(
                record["runs_conceded"],
                record["balls_bowled"]
            ),
            "maidens": record["maidens"],
            "batted": record["batted"],
        })

    return output


# ============================================================================
# MATCH TEAM STATISTICS
# ============================================================================

def process_match_team_stats(match_id, innings_list, scheduled_overs=20):
    """
    Produce one normal team-statistics record per team per match.

    Super Overs are excluded from normal team statistics.

    total_balls:
        Actual legal deliveries bowled.

    allocated_balls:
        Balls allocated to the innings for NRR purposes.

    NRR allocation rules:

        - Normal full innings -> full scheduled/reduced allocation.
        - All-out innings -> full allocated quota, even if all out early.
        - Successful chase -> actual legal balls faced.
        - Unsuccessful chase -> allocated chase quota.
        - Reduced-over chase -> Cricsheet target.overs is used as the quota.
        - Super Overs -> excluded.
    """

    team_stats = defaultdict(
        lambda: {
            "runs": 0,
            "wickets": 0,
            "total_balls": 0,
            "allocated_balls": 0,
            "fours": 0,
            "sixes": 0,
            "extras": 0,
        }
    )

    # ---------------------------------------------------------------
    # Ignore Super Overs for normal match statistics.
    # ---------------------------------------------------------------

    normal_innings = [
        innings
        for innings in innings_list
        if not is_super_over(innings)
    ]

    scheduled_balls = max(
        0,
        safe_int(scheduled_overs) * 6
    )

    for innings_index, innings in enumerate(normal_innings):

        team_raw = innings.get("team", "")
        team = normalize_team(team_raw)

        actual_legal_balls = 0
        innings_wickets = 0
        innings_runs = 0

        # -----------------------------------------------------------
        # Process deliveries.
        # -----------------------------------------------------------

        for over in innings.get("overs", []):

            for delivery in over.get("deliveries", []):

                runs = delivery.get("runs", {})

                total_runs = safe_int(
                    runs.get("total")
                )

                batter_runs = safe_int(
                    runs.get("batter")
                )

                extra_runs = safe_int(
                    runs.get("extras")
                )

                innings_runs += total_runs

                team_stats[team]["runs"] += total_runs
                team_stats[team]["extras"] += extra_runs

                if batter_runs == 4:
                    team_stats[team]["fours"] += 1

                elif batter_runs == 6:
                    team_stats[team]["sixes"] += 1

                if is_legal_delivery(delivery):
                    actual_legal_balls += 1
                    team_stats[team]["total_balls"] += 1

                wickets = delivery.get("wickets", [])

                if wickets:
                    wicket_count = len(wickets)
                    innings_wickets += wicket_count
                    team_stats[team]["wickets"] += wicket_count

        # -----------------------------------------------------------
        # Determine allocated balls for NRR.
        # -----------------------------------------------------------

        allocated_balls = scheduled_balls

        target = innings.get("target")

        # ===========================================================
        # SECOND INNINGS / CHASE
        # ===========================================================

        if isinstance(target, dict):

            target_overs = target.get("overs")
            target_runs = target.get("runs")

            # Cricsheet target.overs represents the overs available
            # for the chase, including reduced-over matches.
            if target_overs is not None:
                target_balls = max(
                    0,
                    safe_int(target_overs) * 6
                )
                allocated_balls = target_balls

            # If the chasing team actually reaches the target,
            # NRR uses the actual legal balls faced rather than
            # the complete target allocation.
            if (
                target_runs is not None
                and innings_runs >= safe_int(target_runs)
                and actual_legal_balls > 0
            ):
                allocated_balls = actual_legal_balls

        # ===========================================================
        # FIRST INNINGS / INNINGS WITHOUT A TARGET
        # ===========================================================

        elif innings_index == 0:

            # An all-out innings is charged with the full allocation
            # for NRR even though fewer balls were actually faced.
            if innings_wickets >= 10:
                allocated_balls = scheduled_balls

            # A genuinely reduced first innings that ended before
            # its available quota and was not all out uses the
            # actual legal balls as its allocation.
            elif (
                actual_legal_balls < scheduled_balls
                and actual_legal_balls > 0
            ):
                allocated_balls = actual_legal_balls

        # -----------------------------------------------------------
        # Safety fallback.
        # -----------------------------------------------------------

        if allocated_balls <= 0:
            allocated_balls = actual_legal_balls

        team_stats[team]["allocated_balls"] = allocated_balls

    # ----------------------------------------------------------------
    # Build output.
    # ----------------------------------------------------------------

    output = []

    for team, stats in team_stats.items():

        output.append({
            "match_id": match_id,
            "team_name": team,
            "runs": stats["runs"],
            "wickets": stats["wickets"],
            "total_balls": stats["total_balls"],
            "allocated_balls": stats["allocated_balls"],
            "fours": stats["fours"],
            "sixes": stats["sixes"],
            "extras": stats["extras"],
            "run_rate": calculate_economy(
                stats["runs"],
                stats["total_balls"]
            ),
        })

    return output

# ============================================================================
# CAREER / SEASON PLAYER AGGREGATION
# ============================================================================

def update_player_aggregate(
    aggregate,
    performance,
    match_id,
    season
):

    player_id = performance[
        "player_external_id"
    ]

    key = (
        player_id,
        season
    )

    if key not in aggregate:

        aggregate[key] = {
            "player_external_id": player_id,
            "player_name": performance[
                "player_name"
            ],
            "team_name": performance[
                "team_name"
            ],
            "season": season,
            "matches": set(),
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
            "five_wicket_hauls": 0,
            "best_bowling_wickets": 0,
        }

    row = aggregate[key]

    row["matches"].add(
        match_id
    )

    if performance["batted"]:

        row["batting_innings"] += 1

        row["runs"] += performance[
            "batting_runs"
        ]

        row["balls_faced"] += performance[
            "balls_faced"
        ]

        row["highest_score"] = max(
            row["highest_score"],
            performance["batting_runs"]
        )

        if performance["not_out"]:
            row["not_outs"] += 1

        row["fours"] += performance[
            "fours"
        ]

        row["sixes"] += performance[
            "sixes"
        ]

        score = performance[
            "batting_runs"
        ]

        if score >= 100:
            row["centuries"] += 1

        elif score >= 50:
            row["fifties"] += 1

    if performance["balls_bowled"] > 0:

        row["bowling_innings"] += 1

        row["balls_bowled"] += performance[
            "balls_bowled"
        ]

        row["wickets"] += performance[
            "wickets"
        ]

        row["runs_conceded"] += performance[
            "runs_conceded"
        ]

        row["best_bowling_wickets"] = max(
            row["best_bowling_wickets"],
            performance["wickets"]
        )


def finalize_player_statistics(rows):

    output = []

    for row in rows.values():

        matches = len(
            row["matches"]
        )

        dismissals = (
            row["batting_innings"]
            - row["not_outs"]
        )

        if dismissals > 0:

            batting_average = round(
                row["runs"] / dismissals,
                2
            )

        else:

            batting_average = 0.0

        strike_rate = calculate_strike_rate(
            row["runs"],
            row["balls_faced"]
        )

        economy = calculate_economy(
            row["runs_conceded"],
            row["balls_bowled"]
        )

        if row["wickets"] > 0:

            bowling_average = round(
                row["runs_conceded"]
                / row["wickets"],
                2
            )

        else:

            bowling_average = 0.0

        output.append({
            "player_external_id": row[
                "player_external_id"
            ],
            "player_name": row[
                "player_name"
            ],
            "team_name": row[
                "team_name"
            ],
            "season": row[
                "season"
            ],
            "matches": matches,
            "batting_innings": row[
                "batting_innings"
            ],
            "runs": row["runs"],
            "balls_faced": row[
                "balls_faced"
            ],
            "highest_score": row[
                "highest_score"
            ],
            "not_outs": row[
                "not_outs"
            ],
            "fours": row["fours"],
            "sixes": row["sixes"],
            "fifties": row["fifties"],
            "centuries": row[
                "centuries"
            ],
            "batting_average": batting_average,
            "strike_rate": strike_rate,
            "bowling_innings": row[
                "bowling_innings"
            ],
            "balls_bowled": row[
                "balls_bowled"
            ],
            "wickets": row["wickets"],
            "runs_conceded": row[
                "runs_conceded"
            ],
            "economy": economy,
            "bowling_average": bowling_average,
            "best_bowling_wickets": row[
                "best_bowling_wickets"
            ],
            "five_wicket_hauls": row[
                "five_wicket_hauls"
            ],
        })

    return output


# ============================================================================
# MAIN PROCESSOR
# ============================================================================

def main():

    print("=" * 80)
    print("CRICKET ANALYTICS")
    print("IPL JSON PROCESSOR")
    print("=" * 80)

    print()
    print("Source:")
    print(ZIP_PATH)

    print()
    print("Output:")
    print(OUTPUT_DIR)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    matches_output = []
    match_team_output = []
    player_match_output = []

    player_season_aggregate = {}

    players = {}
    teams = set()
    venues = set()

    processed_matches = 0

    with zipfile.ZipFile(
        ZIP_PATH,
        "r"
    ) as archive:

        json_files = sorted([
            name
            for name in archive.namelist()
            if name.lower().endswith(".json")
        ])

        if PROCESS_LIMIT is not None:

            json_files = json_files[
                :PROCESS_LIMIT
            ]

        total = len(
            json_files
        )

        print()
        print(
            f"Processing {total} IPL matches..."
        )

        for index, filename in enumerate(
            json_files,
            start=1
        ):

            with archive.open(filename) as raw_file:

                data = json.load(
                    io.TextIOWrapper(
                        raw_file,
                        encoding="utf-8"
                    )
                )

            info = data.get(
                "info",
                {}
            )

            match_id = filename.rsplit(
                "/",
                1
            )[-1].replace(
                ".json",
                ""
            )

            date = get_match_date(
                info
            )

            season = normalize_season(
                info.get(
                    "season",
                    ""
                )
            )

            stage = get_match_stage(info)

            gender = info.get(
                "gender",
                "male"
            )

            match_type = info.get(
                "match_type",
                "T20"
            )

            raw_teams = info.get(
                "teams",
                []
            )

            canonical_teams = [
                normalize_team(team)
                for team in raw_teams
            ]

            for team in canonical_teams:
                teams.add(team)

            venue = info.get(
                "venue",
                ""
            )

            city = info.get(
                "city",
                ""
            )

            if venue:
                venues.add(venue)

            # ---------------------------------------------------------------
            # Player registry
            # ---------------------------------------------------------------

            registry = info.get(
                "registry",
                {}
            )

            people = registry.get(
                "people",
                {}
            )

            # Player list by team is the authoritative team association.
            team_name_by_player = {}

            players_by_team = info.get(
                "players",
                {}
            )

            for raw_team, team_players in (
                players_by_team.items()
            ):

                canonical_team = normalize_team(
                    raw_team
                )

                for player_name in team_players:

                    external_id = people.get(
                        player_name,
                        ""
                    )

                    players[
                        external_id
                    ] = {
                        "player_external_id":
                            external_id,
                        "player_name":
                            player_name,
                        "team_name":
                            canonical_team,
                        "gender":
                            gender,
                    }

                    team_name_by_player[
                        player_name
                    ] = canonical_team

            # ---------------------------------------------------------------
            # Outcome
            # ---------------------------------------------------------------

            outcome = info.get(
                "outcome",
                {}
            )

            winner_raw = outcome.get(
                "winner"
            )

            eliminator_raw = outcome.get(
                "eliminator"
            )

            result_raw = outcome.get(
                "result"
            )

            if result_raw == "no result":

                match_status = "NO_RESULT"
                result_type = "NO_RESULT"
                winner = ""

            elif result_raw == "tie":

                match_status = "COMPLETED"
                result_type = "TIED"

                winner = normalize_team(
                    eliminator_raw
                    if eliminator_raw
                    else ""
                )

            elif winner_raw:

                match_status = "COMPLETED"
                result_type = "WINNER"

                winner = normalize_team(
                    winner_raw
                )

            else:

                match_status = "UNKNOWN"
                result_type = ""
                winner = ""

            # ---------------------------------------------------------------
            # Toss
            # ---------------------------------------------------------------

            toss = info.get(
                "toss",
                {}
            )

            toss_winner = normalize_team(
                toss.get(
                    "winner",
                    ""
                )
            )

            toss_decision = toss.get(
                "decision",
                ""
            )

            # ---------------------------------------------------------------
            # Super-over information
            # ---------------------------------------------------------------

            super_over_count = sum(
                1
                for innings in data.get(
                    "innings",
                    []
                )
                if is_super_over(
                    innings
                )
            )

            if super_over_count > 0:
                result_description = (
                    f"Super Overs: "
                    f"{super_over_count}"
                )
            else:
                result_description = ""

            # ---------------------------------------------------------------
            # Match row
            # ---------------------------------------------------------------

            matches_output.append({
                "match_id": match_id,
                "match_date": date,
                "season": season,
                "stage": stage,
                "gender": gender,
                "match_type": match_type,
                "team1": (
                    canonical_teams[0]
                    if len(canonical_teams) > 0
                    else ""
                ),
                "team2": (
                    canonical_teams[1]
                    if len(canonical_teams) > 1
                    else ""
                ),
                "venue": venue,
                "city": city,
                "toss_winner": toss_winner,
                "toss_decision": toss_decision,
                "winner": winner,
                "match_status": match_status,
                "result_type": result_type,
                "result_description":
                    result_description,
                "super_over_count":
                    super_over_count,
            })

            # ---------------------------------------------------------------
            # Team statistics
            # ---------------------------------------------------------------

            team_stats = process_match_team_stats(
                match_id,
                data.get("innings", []),
                data.get("info", {}).get("overs", 20)
            )

            for row in team_stats:

                match_team_output.append(
                    row
                )

            # ---------------------------------------------------------------
            # Player match statistics
            # ---------------------------------------------------------------

            performances = (
                process_player_match_performance(
                    match_id,
                    data.get(
                        "innings",
                        []
                    ),
                    people,
                    team_name_by_player
                )
            )

            for performance in performances:

                player_match_output.append(
                    performance
                )

                update_player_aggregate(
                    player_season_aggregate,
                    performance,
                    match_id,
                    season
                )

            processed_matches += 1

            if (
                index % 100 == 0
                or index == total
            ):

                print(
                    f"Processed "
                    f"{index}/{total}"
                )

    # =========================================================================
    # FINALIZE
    # =========================================================================

    player_statistics_output = (
        finalize_player_statistics(
            player_season_aggregate
        )
    )

    # =========================================================================
    # WRITE CSV
    # =========================================================================

    def write_csv(
        filename,
        rows,
        fieldnames
    ):

        path = os.path.join(
            OUTPUT_DIR,
            filename
        )

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()

            writer.writerows(rows)

        print(
            f"Written: {path}"
        )

    write_csv(
        "matches.csv",
        matches_output,
        [
            "match_id",
            "match_date",
            "season",
            "stage",
            "gender",
            "match_type",
            "team1",
            "team2",
            "venue",
            "city",
            "toss_winner",
            "toss_decision",
            "winner",
            "match_status",
            "result_type",
            "result_description",
            "super_over_count",
        ]
    )

    write_csv(
        "teams.csv",
        [
            {
                "team_id": team,
                "team_name": team,
                "gender": "male",
            }
            for team in sorted(teams)
        ],
        [
            "team_id",
            "team_name",
            "gender",
        ]
    )

    write_csv(
        "players.csv",
        list(players.values()),
        [
            "player_external_id",
            "player_name",
            "gender",
            "team_name",
        ]
    )

    write_csv(
        "match_team_stats.csv",
        match_team_output,
        [
            "match_id",
            "team_name",
            "runs",
            "wickets",
            "total_balls",
            "allocated_balls",
            "fours",
            "sixes",
            "extras",
            "run_rate",
        ]
    )

    write_csv(
        "player_match_performance.csv",
        player_match_output,
        [
            "match_id",
            "player_external_id",
            "player_name",
            "team_name",
            "batting_runs",
            "balls_faced",
            "fours",
            "sixes",
            "batting_strike_rate",
            "not_out",
            "balls_bowled",
            "runs_conceded",
            "wickets",
            "bowling_economy",
            "maidens",
            "batted",
        ]
    )

    write_csv(
        "player_statistics.csv",
        player_statistics_output,
        [
            "player_external_id",
            "player_name",
            "team_name",
            "season",
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
    )

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print()
    print("=" * 80)
    print("IPL PROCESSING SUMMARY")
    print("=" * 80)

    print()
    print(
        f"Matches processed:       "
        f"{len(matches_output)}"
    )

    print(
        f"Canonical teams:         "
        f"{len(teams)}"
    )

    print(
        f"Players:                 "
        f"{len(players)}"
    )

    print(
        f"Venues:                  "
        f"{len(venues)}"
    )

    print(
        f"Match-team rows:         "
        f"{len(match_team_output)}"
    )

    print(
        f"Player-match rows:       "
        f"{len(player_match_output)}"
    )

    print(
        f"Player-season rows:      "
        f"{len(player_statistics_output)}"
    )

    stage_counts = defaultdict(int)
    for match in matches_output:
        stage_counts[match["stage"]] += 1

    print()
    print("Stage breakdown:")

    preferred_stage_order = [
        "League",
        "Qualifier 1",
        "Eliminator",
        "Qualifier 2",
        "Final",
    ]

    printed_stages = set()

    for stage_name in preferred_stage_order:
        if stage_name in stage_counts:
            print(
                f"  {stage_name:<15}"
                f"{stage_counts[stage_name]:>6}"
            )
            printed_stages.add(stage_name)

    for stage_name in sorted(stage_counts):
        if stage_name not in printed_stages:
            print(
                f"  {stage_name:<15}"
                f"{stage_counts[stage_name]:>6}"
            )

    print()
    print(
        "IPL PROCESSING COMPLETE"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()