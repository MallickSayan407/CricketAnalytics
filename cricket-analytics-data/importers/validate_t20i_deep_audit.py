import csv
import json
import os
import zipfile
from collections import Counter, defaultdict


# =============================================================================
# CONFIGURATION
# =============================================================================

RAW_ZIP = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"

PROCESSED_DIR = r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"

MATCHES_CSV = os.path.join(PROCESSED_DIR, "matches.csv")
MATCH_TEAM_STATS_CSV = os.path.join(PROCESSED_DIR, "match_team_stats.csv")
PLAYER_MATCH_CSV = os.path.join(PROCESSED_DIR, "player_match_performance.csv")
PLAYER_STATS_CSV = os.path.join(PROCESSED_DIR, "player_statistics.csv")
TEAMS_CSV = os.path.join(PROCESSED_DIR, "teams.csv")


# =============================================================================
# TEAM NORMALIZATION
# =============================================================================

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


# =============================================================================
# COUNTERS
# =============================================================================

PASS_COUNT = 0
WARN_COUNT = 0
FAIL_COUNT = 0


# =============================================================================
# HELPERS
# =============================================================================

def section(title):
    print()
    print("=" * 90)
    print(title)
    print("=" * 90)


def pass_msg(message):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {message}")


def warn_msg(message):
    global WARN_COUNT
    WARN_COUNT += 1
    print(f"[WARN] {message}")


def fail_msg(message):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {message}")


def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def nearly_equal(a, b, tolerance=0.02):
    return abs(a - b) <= tolerance


def normalize_team(name):
    if name is None:
        return ""

    name = str(name).strip()

    return TEAM_NORMALIZATION.get(name, name)


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def innings_is_super_over(innings):
    if not isinstance(innings, dict):
        return False

    value = innings.get("super_over")

    if isinstance(value, bool):
        return value

    if str(value).lower() in {"true", "1", "yes"}:
        return True

    return False


def get_extras(delivery):
    extras = delivery.get("extras", {})

    if isinstance(extras, dict):
        return extras

    return {}


def get_wickets(delivery):
    wickets = delivery.get("wickets", [])

    if isinstance(wickets, list):
        return wickets

    return []


def iter_deliveries(innings):
    overs = innings.get("overs", [])

    if not isinstance(overs, list):
        return

    for over in overs:

        if not isinstance(over, dict):
            continue

        deliveries = over.get("deliveries", [])

        if not isinstance(deliveries, list):
            continue

        for delivery in deliveries:

            if isinstance(delivery, dict):
                yield delivery


# =============================================================================
# START
# =============================================================================

print("=" * 90)
print("T20I DEEP DATASET AUDIT - OPTIMIZED")
print("=" * 90)

print()
print("READ-ONLY AUDIT")
print("No files or database records will be modified.")


# =============================================================================
# FILE CHECK
# =============================================================================

section("FILE CHECK")

required_files = [
    RAW_ZIP,
    MATCHES_CSV,
    MATCH_TEAM_STATS_CSV,
    PLAYER_MATCH_CSV,
    PLAYER_STATS_CSV,
    TEAMS_CSV,
]

missing = []

for path in required_files:

    if os.path.exists(path):
        pass_msg(f"Exists: {path}")
    else:
        fail_msg(f"Missing: {path}")
        missing.append(path)

if missing:
    raise SystemExit(1)


# =============================================================================
# LOAD PROCESSED DATA
# =============================================================================

section("LOADING PROCESSED DATA")

matches = load_csv(MATCHES_CSV)
match_team_stats = load_csv(MATCH_TEAM_STATS_CSV)
player_match = load_csv(PLAYER_MATCH_CSV)
player_stats = load_csv(PLAYER_STATS_CSV)
teams = load_csv(TEAMS_CSV)

print(f"Processed matches:             {len(matches):,}")
print(f"Processed match-team rows:     {len(match_team_stats):,}")
print(f"Processed player-match rows:   {len(player_match):,}")
print(f"Processed career rows:         {len(player_stats):,}")
print(f"Processed teams:                {len(teams):,}")


# =============================================================================
# BUILD FAST LOOKUPS
# =============================================================================

processed_matches = {
    row["match_id"]: row
    for row in matches
}

processed_match_team = defaultdict(dict)

for row in match_team_stats:

    key = (
        row["match_id"],
        normalize_team(row["team_name"]),
    )

    processed_match_team[key] = row


processed_player_match = {}

for row in player_match:

    key = (
        row["match_id"],
        row["player_name"],
    )

    processed_player_match[key] = row


processed_career = {
    row["player_name"]: row
    for row in player_stats
}


processed_team_keys = set()

for row in teams:

    processed_team_keys.add(
        (
            normalize_team(row["team_name"]),
            row["gender"].strip().lower(),
        )
    )


# =============================================================================
# PROCESSED BASELINE
# =============================================================================

section("PROCESSED DATASET BASELINE")

if len(matches) == 5700:
    pass_msg("Processed match count = 5,700")
else:
    fail_msg(
        f"Expected 5,700 matches, found {len(matches):,}"
    )

if len(match_team_stats) == 11400:
    pass_msg("Processed match-team count = 11,400")
else:
    fail_msg(
        f"Expected 11,400 match-team rows, found {len(match_team_stats):,}"
    )

if len(processed_matches) == len(matches):
    pass_msg("Processed match IDs are unique")
else:
    fail_msg("Duplicate processed match IDs detected")


# =============================================================================
# RAW ZIP SCAN
# =============================================================================

section("RAW ZIP SCAN")

raw_match_count = 0
raw_match_ids = set()

raw_json_errors = []

raw_gender = Counter()
raw_match_type = Counter()
raw_result_type = Counter()

raw_team_gender_keys = set()
raw_registry_names = set()

raw_total_deliveries = 0
raw_regulation_deliveries = 0
raw_super_over_deliveries = 0

raw_regulation_runs = 0
raw_regulation_batter_runs = 0
raw_regulation_extras = 0

raw_super_over_runs = 0

raw_legal_balls = 0
raw_super_over_legal_balls = 0

raw_wides = 0
raw_noballs = 0
raw_legbyes = 0
raw_byes = 0
raw_penalty = 0

raw_fours = 0
raw_sixes = 0

raw_wickets = 0

raw_all_out_innings = 0
raw_shortened_innings = 0

raw_super_over_matches = set()
raw_tied_matches = set()
raw_no_result_matches = set()

raw_match_team_stats = {}

raw_player_match_stats = defaultdict(
    lambda: {
        "runs": 0,
        "balls_faced": 0,
        "fours": 0,
        "sixes": 0,
        "balls_bowled": 0,
        "runs_conceded": 0,
        "wickets": 0,
    }
)


with zipfile.ZipFile(RAW_ZIP, "r") as z:

    json_files = [
        name
        for name in z.namelist()
        if name.lower().endswith(".json")
    ]

    print(f"JSON files in ZIP: {len(json_files):,}")

    for filename in json_files:

        try:

            with z.open(filename) as f:
                data = json.load(f)

        except Exception as exc:

            raw_json_errors.append(
                (filename, str(exc))
            )

            continue

        info = data.get("info", {})

        match_id = os.path.splitext(
            os.path.basename(filename)
        )[0]

        raw_match_count += 1
        raw_match_ids.add(match_id)

        gender = str(
            info.get("gender", "")
        ).strip().lower()

        match_type = str(
            info.get("match_type", "")
        ).strip()

        raw_gender[gender] += 1
        raw_match_type[match_type] += 1

        # ---------------------------------------------------------------
        # Teams
        # ---------------------------------------------------------------

        match_teams = info.get("teams", [])

        if not isinstance(match_teams, list):
            match_teams = []

        normalized_match_teams = []

        for team in match_teams:

            team = str(team).strip()
            normalized = normalize_team(team)

            normalized_match_teams.append(normalized)

            raw_team_gender_keys.add(
                (
                    normalized,
                    gender,
                )
            )

        # ---------------------------------------------------------------
        # Players
        # ---------------------------------------------------------------

        players = info.get("players", {})

        if isinstance(players, dict):

            for team_players in players.values():

                if isinstance(team_players, list):

                    for name in team_players:
                        raw_registry_names.add(
                            str(name).strip()
                        )

                elif isinstance(team_players, dict):

                    for name in team_players.keys():
                        raw_registry_names.add(
                            str(name).strip()
                        )

        # ---------------------------------------------------------------
        # Result
        # ---------------------------------------------------------------

        outcome = info.get("outcome", {})

        if not isinstance(outcome, dict):
            outcome = {}

        if "winner" in outcome:

            result_type = "WINNER"

        else:

            result = str(
                outcome.get("result", "")
            ).lower()

            if result == "tie":
                result_type = "TIED"

            elif result in {
                "no result",
                "no_result",
                "no-result",
            }:
                result_type = "NO_RESULT"

            else:
                result_type = result.upper()

        raw_result_type[result_type] += 1

        if result_type == "TIED":
            raw_tied_matches.add(match_id)

        if result_type == "NO_RESULT":
            raw_no_result_matches.add(match_id)

        # ---------------------------------------------------------------
        # Match team accumulators
        # ---------------------------------------------------------------

        team_stats = defaultdict(
            lambda: {
                "runs": 0,
                "batter_runs": 0,
                "extras": 0,
                "legal_balls": 0,
                "fours": 0,
                "sixes": 0,
                "wickets": 0,
            }
        )

        innings_list = data.get("innings", [])

        if not isinstance(innings_list, list):
            innings_list = []

        for innings in innings_list:

            if not isinstance(innings, dict):
                continue

            team = normalize_team(
                innings.get("team", "")
            )

            is_super = innings_is_super_over(innings)

            deliveries = list(
                iter_deliveries(innings)
            )

            # -----------------------------------------------------------
            # Innings classification
            # -----------------------------------------------------------

            if not is_super:

                dismissed = set()

                for delivery in deliveries:

                    for wicket in get_wickets(delivery):

                        if not isinstance(wicket, dict):
                            continue

                        kind = str(
                            wicket.get("kind", "")
                        ).lower()

                        player_out = wicket.get(
                            "player_out"
                        )

                        if (
                            player_out
                            and kind not in {
                                "retired hurt",
                                "retired not out",
                            }
                        ):
                            dismissed.add(
                                str(player_out)
                            )

                if len(dismissed) >= 10:
                    raw_all_out_innings += 1

                overs = innings.get(
                    "overs", []
                )

                if isinstance(overs, list) and overs:

                    last_over = safe_int(
                        overs[-1].get("over")
                    )

                    if (
                        last_over < 19
                        and len(dismissed) < 10
                    ):
                        raw_shortened_innings += 1

            else:

                raw_super_over_matches.add(
                    match_id
                )

            # -----------------------------------------------------------
            # Deliveries
            # -----------------------------------------------------------

            for delivery in deliveries:

                raw_total_deliveries += 1

                extras = get_extras(
                    delivery
                )

                runs = delivery.get(
                    "runs", {}
                )

                if not isinstance(runs, dict):
                    runs = {}

                batter_runs = safe_int(
                    runs.get("batter")
                )

                extra_runs = safe_int(
                    runs.get("extras")
                )

                total_runs = (
                    batter_runs + extra_runs
                )

                is_wide = (
                    "wides" in extras
                )

                is_no_ball = (
                    "noballs" in extras
                )

                is_legal = (
                    not is_wide
                    and not is_no_ball
                )

                if is_wide:
                    raw_wides += safe_int(
                        extras.get("wides")
                    )

                if is_no_ball:
                    raw_noballs += safe_int(
                        extras.get("noballs")
                    )

                raw_legbyes += safe_int(
                    extras.get("legbyes")
                )

                raw_byes += safe_int(
                    extras.get("byes")
                )

                raw_penalty += safe_int(
                    extras.get("penalty")
                )

                if is_super:

                    raw_super_over_deliveries += 1

                    raw_super_over_runs += (
                        total_runs
                    )

                    if is_legal:
                        raw_super_over_legal_balls += 1

                    continue

                # -------------------------------------------------------
                # Regulation
                # -------------------------------------------------------

                raw_regulation_deliveries += 1

                raw_regulation_runs += (
                    total_runs
                )

                raw_regulation_batter_runs += (
                    batter_runs
                )

                raw_regulation_extras += (
                    extra_runs
                )

                if is_legal:
                    raw_legal_balls += 1

                stats = team_stats[team]

                stats["runs"] += total_runs
                stats["batter_runs"] += batter_runs
                stats["extras"] += extra_runs

                if is_legal:
                    stats["legal_balls"] += 1

                if batter_runs == 4:
                    stats["fours"] += 1
                    raw_fours += 1

                if batter_runs == 6:
                    stats["sixes"] += 1
                    raw_sixes += 1

                for wicket in get_wickets(delivery):

                    if not isinstance(wicket, dict):
                        continue

                    kind = str(
                        wicket.get("kind", "")
                    ).lower()

                    if kind not in {
                        "retired hurt",
                        "retired not out",
                    }:

                        stats["wickets"] += 1
                        raw_wickets += 1

                # -------------------------------------------------------
                # Batter
                # -------------------------------------------------------

                batter = str(
                    delivery.get("batter", "")
                ).strip()

                if batter:

                    key = (
                        match_id,
                        batter,
                    )

                    p = raw_player_match_stats[key]

                    p["runs"] += batter_runs

                    if is_legal:
                        p["balls_faced"] += 1

                    if batter_runs == 4:
                        p["fours"] += 1

                    if batter_runs == 6:
                        p["sixes"] += 1

                # -------------------------------------------------------
                # Bowler
                # -------------------------------------------------------

                bowler = str(
                    delivery.get("bowler", "")
                ).strip()

                if bowler:

                    key = (
                        match_id,
                        bowler,
                    )

                    p = raw_player_match_stats[key]

                    bowler_runs = (
                        batter_runs
                        + safe_int(
                            extras.get("wides")
                        )
                        + safe_int(
                            extras.get("noballs")
                        )
                    )

                    p["runs_conceded"] += (
                        bowler_runs
                    )

                    if is_legal:
                        p["balls_bowled"] += 1

                    for wicket in get_wickets(delivery):

                        if not isinstance(wicket, dict):
                            continue

                        kind = str(
                            wicket.get("kind", "")
                        ).lower()

                        if kind not in {
                            "retired hurt",
                            "retired not out",
                            "retired out",
                            "obstructing the field",
                        }:

                            p["wickets"] += 1

        # ---------------------------------------------------------------
        # Save raw match-team stats
        # ---------------------------------------------------------------

        for team in normalized_match_teams:

            stats = team_stats[team]

            raw_match_team_stats[
                (
                    match_id,
                    team,
                )
            ] = stats


# =============================================================================
# RAW SUMMARY
# =============================================================================

section("RAW DATASET SUMMARY")

print(f"Raw matches:                         {raw_match_count:,}")
print(f"Raw unique match IDs:                {len(raw_match_ids):,}")
print(f"Raw JSON errors:                     {len(raw_json_errors):,}")

print()
print(f"Total deliveries:                    {raw_total_deliveries:,}")
print(f"Regulation deliveries:               {raw_regulation_deliveries:,}")
print(f"Super Over deliveries:               {raw_super_over_deliveries:,}")

print()
print(f"Regulation runs:                     {raw_regulation_runs:,}")
print(f"Regulation batter runs:              {raw_regulation_batter_runs:,}")
print(f"Regulation extras:                   {raw_regulation_extras:,}")
print(f"Super Over runs:                     {raw_super_over_runs:,}")

print()
print(f"Regulation legal balls:              {raw_legal_balls:,}")
print(f"Super Over legal balls:              {raw_super_over_legal_balls:,}")

print()
print(f"Wides:                               {raw_wides:,}")
print(f"No-balls:                            {raw_noballs:,}")
print(f"Leg-byes:                            {raw_legbyes:,}")
print(f"Byes:                                {raw_byes:,}")
print(f"Penalty runs:                        {raw_penalty:,}")

print()
print(f"Fours:                               {raw_fours:,}")
print(f"Sixes:                               {raw_sixes:,}")
print(f"Wickets:                             {raw_wickets:,}")

print()
print(f"All-out innings:                     {raw_all_out_innings:,}")
print(f"Shortened innings:                   {raw_shortened_innings:,}")
print(f"Super Over matches:                  {len(raw_super_over_matches):,}")


# =============================================================================
# RAW BASELINE CHECKS
# =============================================================================

section("RAW BASELINE CHECKS")

if raw_match_count == 5700:
    pass_msg("Raw match count = 5,700")
else:
    fail_msg(
        f"Expected 5,700 raw matches, found {raw_match_count:,}"
    )

if len(raw_match_ids) == 5700:
    pass_msg("Raw match IDs are unique")
else:
    fail_msg("Raw match IDs are not unique")

if not raw_json_errors:
    pass_msg("No JSON parsing errors")
else:
    fail_msg(
        f"{len(raw_json_errors)} JSON parsing errors"
    )

if raw_gender["male"] == 3539:
    pass_msg("Raw male matches = 3,539")
else:
    fail_msg("Raw male match count mismatch")

if raw_gender["female"] == 2161:
    pass_msg("Raw female matches = 2,161")
else:
    fail_msg("Raw female match count mismatch")

if raw_match_type.get("T20", 0) == 5700:
    pass_msg("All raw matches are T20")
else:
    fail_msg(
        f"Unexpected match types: {dict(raw_match_type)}"
    )


# =============================================================================
# RESULT CHECKS
# =============================================================================

section("RESULT RECONCILIATION")

if raw_result_type["WINNER"] == 5536:
    pass_msg("Raw WINNER count = 5,536")
else:
    fail_msg("Raw WINNER count mismatch")

if raw_result_type["TIED"] == 51:
    pass_msg("Raw TIED count = 51")
else:
    fail_msg("Raw TIED count mismatch")

if raw_result_type["NO_RESULT"] == 113:
    pass_msg("Raw NO_RESULT count = 113")
else:
    fail_msg("Raw NO_RESULT count mismatch")


# =============================================================================
# RAW VS PROCESSED MATCH IDS
# =============================================================================

section("RAW VS PROCESSED MATCH IDS")

processed_ids = set(
    processed_matches.keys()
)

missing_processed = (
    raw_match_ids - processed_ids
)

extra_processed = (
    processed_ids - raw_match_ids
)

print(
    f"Raw IDs missing from processed:      "
    f"{len(missing_processed):,}"
)

print(
    f"Processed IDs absent from raw:       "
    f"{len(extra_processed):,}"
)

if not missing_processed:
    pass_msg(
        "Every raw match exists in processed data"
    )
else:
    fail_msg(
        f"{len(missing_processed)} raw matches missing"
    )

if not extra_processed:
    pass_msg(
        "No extra processed matches"
    )
else:
    fail_msg(
        f"{len(extra_processed)} extra processed matches"
    )


# =============================================================================
# SUPER OVER PROTECTION
# =============================================================================

section("SUPER OVER PROTECTION")

if raw_super_over_deliveries == 550:
    pass_msg("Super Over deliveries = 550")
else:
    fail_msg(
        f"Expected 550 Super Over deliveries, "
        f"found {raw_super_over_deliveries:,}"
    )

if raw_super_over_runs == 1028:
    pass_msg("Super Over runs = 1,028")
else:
    fail_msg(
        f"Expected 1,028 Super Over runs, "
        f"found {raw_super_over_runs:,}"
    )

processed_team_runs = sum(
    safe_int(row["runs"])
    for row in match_team_stats
)

processed_player_runs = sum(
    safe_int(row["batting_runs"])
    for row in player_match
)

processed_extras = sum(
    safe_int(row["extras"])
    for row in match_team_stats
)

print()
print(
    f"Processed team runs:                 "
    f"{processed_team_runs:,}"
)

print(
    f"Processed player runs:               "
    f"{processed_player_runs:,}"
)

print(
    f"Processed extras:                    "
    f"{processed_extras:,}"
)

if processed_team_runs == raw_regulation_runs:
    pass_msg(
        "Processed team runs exclude Super Over runs"
    )
else:
    fail_msg(
        "Processed team runs do not match regulation runs"
    )

if (
    processed_player_runs + processed_extras
    == raw_regulation_runs
):
    pass_msg(
        "Processed player runs + extras = regulation runs"
    )
else:
    fail_msg(
        "Player runs + extras mismatch"
    )


# =============================================================================
# LEGAL BALLS
# =============================================================================

section("LEGAL BALL AUDIT")

processed_balls = sum(
    safe_int(row["total_balls"])
    for row in match_team_stats
)

print(
    f"Raw regulation legal balls:          "
    f"{raw_legal_balls:,}"
)

print(
    f"Processed total_balls:                "
    f"{processed_balls:,}"
)

if processed_balls == raw_legal_balls:
    pass_msg(
        "Processed total_balls exactly matches raw legal balls"
    )
else:
    fail_msg(
        "Processed total_balls mismatch"
    )


# =============================================================================
# MATCH-TEAM RECONCILIATION
# =============================================================================

section("MATCH-TEAM RAW VS PROCESSED")

team_mismatches = []

for key, raw_stats in raw_match_team_stats.items():

    row = processed_match_team.get(key)

    if row is None:

        team_mismatches.append(
            (
                key,
                "missing",
                raw_stats,
                None,
            )
        )

        continue

    checks = {
        "runs": (
            raw_stats["runs"],
            safe_int(row["runs"]),
        ),

        "fours": (
            raw_stats["fours"],
            safe_int(row["fours"]),
        ),

        "sixes": (
            raw_stats["sixes"],
            safe_int(row["sixes"]),
        ),

        "extras": (
            raw_stats["extras"],
            safe_int(row["extras"]),
        ),

        "total_balls": (
            raw_stats["legal_balls"],
            safe_int(row["total_balls"]),
        ),

        "wickets": (
            raw_stats["wickets"],
            safe_int(row["wickets"]),
        ),
    }

    for field, (expected, actual) in checks.items():

        if expected != actual:

            team_mismatches.append(
                (
                    key,
                    field,
                    expected,
                    actual,
                )
            )


print(
    f"Raw match-team keys checked:          "
    f"{len(raw_match_team_stats):,}"
)

print(
    f"Match-team mismatches:                "
    f"{len(team_mismatches):,}"
)

if not team_mismatches:

    pass_msg(
        "Raw and processed match-team statistics reconcile exactly"
    )

else:

    fail_msg(
        f"{len(team_mismatches)} match-team mismatches"
    )

    print()
    print("First 20 mismatches:")

    for item in team_mismatches[:20]:
        print(item)


# =============================================================================
# TEAM NORMALIZATION
# =============================================================================

section("TEAM NORMALIZATION")

print(
    f"Raw team/gender keys:                 "
    f"{len(raw_team_gender_keys):,}"
)

print(
    f"Processed team/gender keys:           "
    f"{len(processed_team_keys):,}"
)

missing_team_keys = (
    raw_team_gender_keys
    - processed_team_keys
)

extra_team_keys = (
    processed_team_keys
    - raw_team_gender_keys
)

if not missing_team_keys:
    pass_msg(
        "Every raw team/gender combination exists in processed data"
    )
else:
    fail_msg(
        f"{len(missing_team_keys)} raw team/gender combinations missing"
    )

if not extra_team_keys:
    pass_msg(
        "No unexpected processed team/gender combinations"
    )
else:
    fail_msg(
        f"{len(extra_team_keys)} unexpected processed team/gender combinations"
    )


# =============================================================================
# PLAYER-MATCH RECONCILIATION
# =============================================================================

section("PLAYER-MATCH RAW VS PROCESSED")

player_match_mismatches = []

raw_player_match_keys = set(
    raw_player_match_stats.keys()
)

processed_player_match_keys = set(
    processed_player_match.keys()
)

missing_player_match = (
    raw_player_match_keys
    - processed_player_match_keys
)

extra_player_match = (
    processed_player_match_keys
    - raw_player_match_keys
)

print(
    f"Raw player-match keys:                "
    f"{len(raw_player_match_keys):,}"
)

print(
    f"Processed player-match keys:           "
    f"{len(processed_player_match_keys):,}"
)

print(
    f"Missing processed keys:                "
    f"{len(missing_player_match):,}"
)

print(
    f"Extra processed keys:                  "
    f"{len(extra_player_match):,}"
)

if not missing_player_match:
    pass_msg(
        "Every raw player-match key exists in processed data"
    )
else:
    fail_msg(
        f"{len(missing_player_match)} player-match keys missing"
    )

if not extra_player_match:
    pass_msg(
        "No extra processed player-match keys"
    )
else:
    fail_msg(
        f"{len(extra_player_match)} extra player-match keys"
    )


for key in raw_player_match_keys:

    raw = raw_player_match_stats[key]

    row = processed_player_match.get(key)

    if row is None:
        continue

    checks = {
        "batting_runs": (
            raw["runs"],
            safe_int(row["batting_runs"]),
        ),

        "balls_faced": (
            raw["balls_faced"],
            safe_int(row["balls_faced"]),
        ),

        "fours": (
            raw["fours"],
            safe_int(row["fours"]),
        ),

        "sixes": (
            raw["sixes"],
            safe_int(row["sixes"]),
        ),

        "balls_bowled": (
            raw["balls_bowled"],
            safe_int(row["balls_bowled"]),
        ),

        "runs_conceded": (
            raw["runs_conceded"],
            safe_int(row["runs_conceded"]),
        ),

        "wickets": (
            raw["wickets"],
            safe_int(row["wickets"]),
        ),
    }

    for field, (expected, actual) in checks.items():

        if expected != actual:

            player_match_mismatches.append(
                (
                    key,
                    field,
                    expected,
                    actual,
                )
            )


print(
    f"Player-match field mismatches:        "
    f"{len(player_match_mismatches):,}"
)

if not player_match_mismatches:

    pass_msg(
        "Raw and processed player-match statistics reconcile exactly"
    )

else:

    fail_msg(
        f"{len(player_match_mismatches)} player-match field mismatches"
    )

    print()
    print("First 30 mismatches:")

    for item in player_match_mismatches[:30]:
        print(item)


# =============================================================================
# CAREER RECONCILIATION
# =============================================================================

section("CAREER STATISTICS RECONCILIATION")

raw_career = defaultdict(
    lambda: {
        "matches": 0,
        "runs": 0,
        "balls_faced": 0,
        "fours": 0,
        "sixes": 0,
        "balls_bowled": 0,
        "runs_conceded": 0,
        "wickets": 0,
    }
)

# We need unique match counts.
raw_career_matches = defaultdict(set)

for (match_id, player_name), stats in raw_player_match_stats.items():

    c = raw_career[player_name]

    raw_career_matches[
        player_name
    ].add(match_id)

    c["runs"] += stats["runs"]
    c["balls_faced"] += stats["balls_faced"]
    c["fours"] += stats["fours"]
    c["sixes"] += stats["sixes"]
    c["balls_bowled"] += stats["balls_bowled"]
    c["runs_conceded"] += stats["runs_conceded"]
    c["wickets"] += stats["wickets"]


career_mismatches = []

raw_career_players = set(
    raw_career.keys()
)

processed_career_players = set(
    processed_career.keys()
)

missing_career = (
    raw_career_players
    - processed_career_players
)

extra_career = (
    processed_career_players
    - raw_career_players
)

print(
    f"Raw career players:                  "
    f"{len(raw_career_players):,}"
)

print(
    f"Processed career players:             "
    f"{len(processed_career_players):,}"
)

print(
    f"Missing career rows:                  "
    f"{len(missing_career):,}"
)

print(
    f"Extra career rows:                    "
    f"{len(extra_career):,}"
)

if not missing_career:
    pass_msg(
        "Every raw career player has a processed career row"
    )
else:
    fail_msg(
        f"{len(missing_career)} career players missing"
    )

if not extra_career:
    pass_msg(
        "No extra career players"
    )
else:
    fail_msg(
        f"{len(extra_career)} extra career players"
    )


for player_name in raw_career_players:

    raw = raw_career[player_name]

    row = processed_career.get(
        player_name
    )

    if row is None:
        continue

    checks = {
        "matches": (
            len(raw_career_matches[player_name]),
            safe_int(row["matches"]),
        ),

        "runs": (
            raw["runs"],
            safe_int(row["runs"]),
        ),

        "balls_faced": (
            raw["balls_faced"],
            safe_int(row["balls_faced"]),
        ),

        "fours": (
            raw["fours"],
            safe_int(row["fours"]),
        ),

        "sixes": (
            raw["sixes"],
            safe_int(row["sixes"]),
        ),

        "balls_bowled": (
            raw["balls_bowled"],
            safe_int(row["balls_bowled"]),
        ),

        "runs_conceded": (
            raw["runs_conceded"],
            safe_int(row["runs_conceded"]),
        ),

        "wickets": (
            raw["wickets"],
            safe_int(row["wickets"]),
        ),
    }

    for field, (expected, actual) in checks.items():

        if expected != actual:

            career_mismatches.append(
                (
                    player_name,
                    field,
                    expected,
                    actual,
                )
            )


print(
    f"Career field mismatches:              "
    f"{len(career_mismatches):,}"
)

if not career_mismatches:

    pass_msg(
        "Career statistics reconcile exactly"
    )

else:

    fail_msg(
        f"{len(career_mismatches)} career mismatches"
    )

    print()
    print("First 30 mismatches:")

    for item in career_mismatches[:30]:
        print(item)


# =============================================================================
# CAREER DERIVED STATISTICS
# =============================================================================

section("CAREER DERIVED STATISTICS")

derived_errors = []

for row in player_stats:

    name = row["player_name"]

    runs = safe_int(
        row["runs"]
    )

    balls = safe_int(
        row["balls_faced"]
    )

    balls_bowled = safe_int(
        row["balls_bowled"]
    )

    runs_conceded = safe_int(
        row["runs_conceded"]
    )

    not_outs = safe_int(
        row["not_outs"]
    )

    batting_innings = safe_int(
        row["batting_innings"]
    )

    strike_rate = safe_float(
        row["strike_rate"]
    )

    economy = safe_float(
        row["economy"]
    )

    if not_outs > batting_innings:

        derived_errors.append(
            (
                name,
                "not_outs > batting_innings",
            )
        )

    if balls > 0:

        expected_sr = (
            runs / balls * 100
        )

        if not nearly_equal(
            strike_rate,
            expected_sr,
        ):

            derived_errors.append(
                (
                    name,
                    "strike_rate",
                    expected_sr,
                    strike_rate,
                )
            )

    if balls_bowled > 0:

        expected_econ = (
            runs_conceded
            / balls_bowled
            * 6
        )

        if not nearly_equal(
            economy,
            expected_econ,
        ):

            derived_errors.append(
                (
                    name,
                    "economy",
                    expected_econ,
                    economy,
                )
            )


print(
    f"Derived-stat errors:                  "
    f"{len(derived_errors):,}"
)

if not derived_errors:

    pass_msg(
        "Career derived statistics are mathematically consistent"
    )

else:

    fail_msg(
        f"{len(derived_errors)} derived-stat errors"
    )

    print()
    print("First 20 derived-stat errors:")

    for item in derived_errors[:20]:
        print(item)


# =============================================================================
# SUPER OVER SPECIAL CASE
# =============================================================================

section("SPECIAL MULTIPLE-SUPER-OVER MATCH")

special_match_id = "1485939"

with zipfile.ZipFile(RAW_ZIP, "r") as z:

    filename = special_match_id + ".json"

    if filename in z.namelist():

        with z.open(filename) as f:
            data = json.load(f)

        innings = data.get(
            "innings",
            []
        )

        total_innings = len(innings)

        super_over_innings = sum(
            1
            for item in innings
            if innings_is_super_over(item)
        )

        total_deliveries = sum(
            1
            for item in innings
            for _ in iter_deliveries(item)
        )

        print(
            f"Match ID:                           "
            f"{special_match_id}"
        )

        print(
            f"Total innings:                       "
            f"{total_innings}"
        )

        print(
            f"Super Over innings:                  "
            f"{super_over_innings}"
        )

        print(
            f"Total deliveries:                    "
            f"{total_deliveries}"
        )

        if (
            total_innings == 8
            and super_over_innings == 6
        ):

            pass_msg(
                "Special multiple-Super-Over match has "
                "8 innings / 6 Super Over innings"
            )

        else:

            fail_msg(
                "Special multiple-Super-Over structure mismatch"
            )

    else:

        warn_msg(
            f"Special match {special_match_id} not found"
        )


# =============================================================================
# KNOWN PLAYER SANITY
# =============================================================================

section("KNOWN PLAYER SANITY")

known_players = [
    "V Kohli",
    "Babar Azam",
    "RG Sharma",
    "JC Buttler",
    "S Mandhana",
    "BL Mooney",
    "Mohammad Rizwan",
    "MJ Guptill",
    "DB Sharma",
    "AU Rashid",
    "IS Sodhi",
    "TG Southee",
]

for name in known_players:

    row = processed_career.get(name)

    if row is None:

        warn_msg(
            f"{name} not found"
        )

        continue

    print(
        f"{name:<25} "
        f"matches={safe_int(row['matches']):<4} "
        f"runs={safe_int(row['runs']):<5} "
        f"wickets={safe_int(row['wickets']):<3} "
        f"avg={safe_float(row['batting_average']):.2f} "
        f"SR={safe_float(row['strike_rate']):.2f}"
    )


# =============================================================================
# NO RESULT / TIE PROCESSED CHECK
# =============================================================================

section("PROCESSED NO-RESULT / TIE CHECK")

processed_no_results = {
    match_id
    for match_id, row in processed_matches.items()
    if row["result_type"].strip().upper()
    == "NO_RESULT"
}

processed_ties = {
    match_id
    for match_id, row in processed_matches.items()
    if row["result_type"].strip().upper()
    == "TIED"
}

print(
    f"Raw no-results:                       "
    f"{len(raw_no_result_matches):,}"
)

print(
    f"Processed no-results:                 "
    f"{len(processed_no_results):,}"
)

print(
    f"Raw ties:                             "
    f"{len(raw_tied_matches):,}"
)

print(
    f"Processed ties:                       "
    f"{len(processed_ties):,}"
)

if processed_no_results == raw_no_result_matches:

    pass_msg(
        "Raw and processed no-result match sets are identical"
    )

else:

    fail_msg(
        "Raw and processed no-result sets differ"
    )

if processed_ties == raw_tied_matches:

    pass_msg(
        "Raw and processed tied match sets are identical"
    )

else:

    fail_msg(
        "Raw and processed tied sets differ"
    )


# =============================================================================
# GLOBAL PROCESSED TOTALS
# =============================================================================

section("GLOBAL PROCESSED TOTALS")

player_runs = sum(
    safe_int(row["batting_runs"])
    for row in player_match
)

player_fours = sum(
    safe_int(row["fours"])
    for row in player_match
)

player_sixes = sum(
    safe_int(row["sixes"])
    for row in player_match
)

player_wickets = sum(
    safe_int(row["wickets"])
    for row in player_match
)

team_fours = sum(
    safe_int(row["fours"])
    for row in match_team_stats
)

team_sixes = sum(
    safe_int(row["sixes"])
    for row in match_team_stats
)

team_wickets = sum(
    safe_int(row["wickets"])
    for row in match_team_stats
)

print(
    f"Player batting runs:                  {player_runs:,}"
)

print(
    f"Team runs:                            {processed_team_runs:,}"
)

print(
    f"Team extras:                          {processed_extras:,}"
)

print(
    f"Player fours:                         {player_fours:,}"
)

print(
    f"Team fours:                           {team_fours:,}"
)

print(
    f"Player sixes:                         {player_sixes:,}"
)

print(
    f"Team sixes:                           {team_sixes:,}"
)

print(
    f"Player wickets:                       {player_wickets:,}"
)

print(
    f"Team wickets:                         {team_wickets:,}"
)

if player_runs + processed_extras == processed_team_runs:
    pass_msg(
        "Player batting runs + extras = team runs"
    )
else:
    fail_msg(
        "Player batting runs + extras mismatch"
    )

if player_fours == team_fours:
    pass_msg(
        "Player fours = team fours"
    )
else:
    fail_msg(
        "Player fours != team fours"
    )

if player_sixes == team_sixes:
    pass_msg(
        "Player sixes = team sixes"
    )
else:
    fail_msg(
        "Player sixes != team sixes"
    )

if player_wickets <= team_wickets:
    pass_msg(
        "Bowler wickets do not exceed team wickets"
    )
else:
    fail_msg(
        "Bowler wickets exceed team wickets"
    )


# =============================================================================
# FINAL RESULT
# =============================================================================

section("FINAL DEEP AUDIT RESULT")

print()
print(
    f"PASS checks:                         {PASS_COUNT:,}"
)

print(
    f"WARN checks:                         {WARN_COUNT:,}"
)

print(
    f"FAIL checks:                         {FAIL_COUNT:,}"
)

print()

if FAIL_COUNT == 0:

    print(
        "T20I DEEP AUDIT: PASS"
    )

    print()
    print(
        "The T20I raw and processed datasets passed "
        "all critical deep-audit checks."
    )

    print()
    print(
        "NEXT STEP: T20I MYSQL IMPORTER"
    )

else:

    print(
        "T20I DEEP AUDIT: FAIL"
    )

    print()
    print(
        "DO NOT IMPORT T20I DATA INTO MYSQL YET."
    )

print("=" * 90)