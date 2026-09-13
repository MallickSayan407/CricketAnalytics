import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

ZIP_PATH = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"
)


# ============================================================
# HELPERS
# ============================================================

def normalize_date(value):
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value else None


def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def print_counter(title, counter, limit=None):
    print(f"\n{title}")
    print("-" * len(title))

    items = counter.most_common(limit)

    for key, value in items:
        print(f"{key}: {value}")


# ============================================================
# MAIN VALIDATION
# ============================================================

def main():

    print("=" * 80)
    print("T20 INTERNATIONAL DATASET VALIDATION")
    print("=" * 80)

    if not ZIP_PATH.exists():
        print("\nERROR: ZIP file not found:")
        print(ZIP_PATH)
        return

    print(f"\nZIP file:")
    print(ZIP_PATH)

    print(f"ZIP size: {ZIP_PATH.stat().st_size:,} bytes")

    # --------------------------------------------------------
    # Open ZIP
    # --------------------------------------------------------

    with zipfile.ZipFile(ZIP_PATH, "r") as z:

        members = [
            name
            for name in z.namelist()
            if name.lower().endswith(".json")
            and not name.endswith("/")
        ]

        print(f"\nJSON files found: {len(members):,}")

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        match_ids = []
        duplicate_match_ids = []

        genders = Counter()
        match_types = Counter()
        team_types = Counter()

        seasons = Counter()
        years = Counter()

        teams = Counter()
        venues = Counter()
        cities = Counter()

        result_types = Counter()
        match_statuses = Counter()
        eliminators = Counter()

        innings_counts = Counter()

        delivery_count = 0
        regulation_delivery_count = 0
        super_over_delivery_count = 0

        batter_runs = 0
        match_runs = 0
        regulation_match_runs = 0
        super_over_runs = 0

        extras = Counter()
        wickets = Counter()
        dismissal_types = Counter()

        player_names = set()
        registry_ids = set()

        participants_without_registry = set()

        invalid_json_files = []
        invalid_match_ids = []

        invalid_match_types = []
        invalid_genders = []

        matches_with_super_over = []
        matches_with_no_result = []
        matches_with_tie = []
        matches_with_eliminator = []

        date_values = []

        # For checking teams/players participating in matches
        match_participants = defaultdict(set)

        # ----------------------------------------------------
        # Parse every JSON file
        # ----------------------------------------------------

        for index, member in enumerate(members, start=1):

            try:
                with z.open(member) as f:
                    data = json.load(f)

            except Exception as exc:
                invalid_json_files.append((member, str(exc)))
                continue

            info = data.get("info", {})

            # ------------------------------------------------
            # Match ID
            # ------------------------------------------------

            match_id = Path(member).stem

            match_ids.append(match_id)

            if not match_id.isdigit():
                invalid_match_ids.append(match_id)

            # ------------------------------------------------
            # Gender
            # ------------------------------------------------

            gender = info.get("gender", "UNKNOWN")
            genders[gender] += 1

            if gender not in {"male", "female"}:
                invalid_genders.append(
                    (match_id, gender)
                )

            # ------------------------------------------------
            # Match type
            # ------------------------------------------------

            match_type = info.get("match_type", "UNKNOWN")
            match_types[match_type] += 1

            if match_type != "T20":
                invalid_match_types.append(
                    (match_id, match_type)
                )

            # ------------------------------------------------
            # Team type
            # ------------------------------------------------

            team_type = info.get("team_type", "UNKNOWN")
            team_types[team_type] += 1

            # ------------------------------------------------
            # Dates
            # ------------------------------------------------

            date_value = normalize_date(info.get("dates"))

            if date_value:
                date_values.append(date_value)

            # ------------------------------------------------
            # Season
            # ------------------------------------------------

            season = str(info.get("season", "UNKNOWN"))
            seasons[season] += 1

            if date_value and len(date_value) >= 4:
                years[date_value[:4]] += 1

            # ------------------------------------------------
            # Teams
            # ------------------------------------------------

            match_teams = info.get("teams", [])

            for team in match_teams:
                teams[team] += 1

            # ------------------------------------------------
            # Venue / city
            # ------------------------------------------------

            venue = info.get("venue", "UNKNOWN")
            city = info.get("city", "UNKNOWN")

            venues[venue] += 1
            cities[city] += 1

            # ------------------------------------------------
            # Players and registry
            # ------------------------------------------------

            players_by_team = info.get("players", {})

            for team, players in players_by_team.items():

                for player in players:

                    player_names.add(player)
                    match_participants[match_id].add(player)

            registry = info.get("registry", {})
            people_registry = registry.get("people", {})

            for player_name, player_id in people_registry.items():

                registry_ids.add(player_id)

            # ------------------------------------------------
            # Detect participants missing registry IDs
            # ------------------------------------------------

            for team, players in players_by_team.items():

                for player in players:

                    player_id = people_registry.get(player)

                    if not player_id:
                        participants_without_registry.add(
                            (match_id, player)
                        )

            # ------------------------------------------------
            # Outcome
            # ------------------------------------------------

            outcome = info.get("outcome", {})

            result = outcome.get("result")

            if result:
                result_types[result] += 1

            if result == "no result":
                match_statuses["NO_RESULT"] += 1
                matches_with_no_result.append(match_id)

            elif result == "tie":
                match_statuses["TIED"] += 1
                matches_with_tie.append(match_id)

            elif result == "draw":
                match_statuses["DRAW"] += 1

            elif outcome.get("winner"):
                match_statuses["WINNER"] += 1

            else:
                match_statuses["UNKNOWN"] += 1

            winner = outcome.get("winner")

            if winner:
                result_types[f"winner:{winner}"] += 1

            eliminator = outcome.get("eliminator")

            if eliminator:
                eliminators[eliminator] += 1
                matches_with_eliminator.append(match_id)

            # ------------------------------------------------
            # Innings
            # ------------------------------------------------

            innings = data.get("innings", [])

            innings_counts[len(innings)] += 1

            match_has_super_over = False

            for innings_data in innings:

                is_super_over = bool(
                    innings_data.get("super_over", False)
                )

                if is_super_over:
                    match_has_super_over = True

                team = innings_data.get("team", "UNKNOWN")

                overs = innings_data.get("overs", [])

                for over in overs:

                    deliveries = over.get("deliveries", [])

                    for delivery in deliveries:

                        delivery_count += 1

                        if is_super_over:
                            super_over_delivery_count += 1
                        else:
                            regulation_delivery_count += 1

                        runs = delivery.get("runs", {})

                        batter_run = safe_int(
                            runs.get("batter", 0)
                        )

                        extras_run = safe_int(
                            runs.get("extras", 0)
                        )

                        total_run = safe_int(
                            runs.get("total", 0)
                        )

                        batter_runs += batter_run
                        match_runs += total_run

                        if is_super_over:
                            super_over_runs += total_run
                        else:
                            regulation_match_runs += total_run

                        # ------------------------------------
                        # Extras
                        # ------------------------------------

                        delivery_extras = delivery.get(
                            "extras", {}
                        )

                        for extra_type, amount in delivery_extras.items():

                            extras[extra_type] += safe_int(amount)

                        # ------------------------------------
                        # Wickets
                        # ------------------------------------

                        delivery_wickets = delivery.get(
                            "wickets", []
                        )

                        for wicket in delivery_wickets:

                            wickets[wicket.get(
                                "kind", "UNKNOWN"
                            )] += 1

                            dismissal_types[wicket.get(
                                "kind", "UNKNOWN"
                            )] += 1

            if match_has_super_over:

                matches_with_super_over.append(match_id)

        # ====================================================
        # DUPLICATE MATCH IDs
        # ====================================================

        id_counter = Counter(match_ids)

        duplicate_match_ids = [
            (match_id, count)
            for match_id, count in id_counter.items()
            if count > 1
        ]

        # ====================================================
        # SUMMARY
        # ====================================================

        print("\n" + "=" * 80)
        print("BASIC DATASET SUMMARY")
        print("=" * 80)

        print(f"\nMatches:                 {len(match_ids):,}")
        print(f"Unique match IDs:        {len(set(match_ids)):,}")
        print(f"Duplicate match IDs:     {len(duplicate_match_ids):,}")

        print(f"JSON errors:              {len(invalid_json_files):,}")
        print(f"Invalid match IDs:        {len(invalid_match_ids):,}")

        print(f"\nTotal players:             {len(player_names):,}")
        print(f"Registry IDs:              {len(registry_ids):,}")
        print(
            f"Participants missing ID:   "
            f"{len(participants_without_registry):,}"
        )

        # ====================================================
        # GENDER
        # ====================================================

        print_counter(
            "GENDER",
            genders
        )

        # ====================================================
        # MATCH TYPE
        # ====================================================

        print_counter(
            "MATCH TYPES",
            match_types
        )

        # ====================================================
        # TEAM TYPE
        # ====================================================

        print_counter(
            "TEAM TYPES",
            team_types
        )

        # ====================================================
        # SEASONS
        # ====================================================

        print_counter(
            "SEASONS",
            seasons
        )

        # ====================================================
        # YEARS
        # ====================================================

        print_counter(
            "YEARS",
            years
        )

        # ====================================================
        # TEAMS
        # ====================================================

        print(
            f"\nUnique teams: {len(teams):,}"
        )

        print_counter(
            "TOP TEAMS BY MATCH APPEARANCES",
            teams,
            limit=30
        )

        # ====================================================
        # VENUES
        # ====================================================

        print(
            f"\nUnique venues: {len(venues):,}"
        )

        print_counter(
            "TOP VENUES",
            venues,
            limit=30
        )

        # ====================================================
        # CITIES
        # ====================================================

        print(
            f"\nUnique cities: {len(cities):,}"
        )

        print_counter(
            "TOP CITIES",
            cities,
            limit=30
        )

        # ====================================================
        # RESULTS
        # ====================================================

        print_counter(
            "RESULT TYPES",
            result_types
        )

        print_counter(
            "MATCH STATUSES",
            match_statuses
        )

        print_counter(
            "SUPER OVER ELIMINATORS",
            eliminators
        )

        # ====================================================
        # INNINGS
        # ====================================================

        print_counter(
            "NUMBER OF INNINGS PER MATCH",
            innings_counts
        )

        print(
            f"\nMatches containing Super Over innings: "
            f"{len(set(matches_with_super_over)):,}"
        )

        print(
            f"Matches with no result: "
            f"{len(matches_with_no_result):,}"
        )

        print(
            f"Matches tied: "
            f"{len(matches_with_tie):,}"
        )

        print(
            f"Matches with eliminator: "
            f"{len(matches_with_eliminator):,}"
        )

        # ====================================================
        # DELIVERIES / RUNS
        # ====================================================

        print("\n" + "=" * 80)
        print("BALL-BY-BALL TOTALS")
        print("=" * 80)

        print(
            f"\nTotal deliveries:            "
            f"{delivery_count:,}"
        )

        print(
            f"Regulation deliveries:       "
            f"{regulation_delivery_count:,}"
        )

        print(
            f"Super Over deliveries:        "
            f"{super_over_delivery_count:,}"
        )

        print(
            f"\nBatter runs:                  "
            f"{batter_runs:,}"
        )

        print(
            f"Total match runs:             "
            f"{match_runs:,}"
        )

        print(
            f"Regulation match runs:        "
            f"{regulation_match_runs:,}"
        )

        print(
            f"Super Over runs:              "
            f"{super_over_runs:,}"
        )

        # ====================================================
        # EXTRAS
        # ====================================================

        print_counter(
            "EXTRAS",
            extras
        )

        print(
            f"\nTotal extras: "
            f"{sum(extras.values()):,}"
        )

        # ====================================================
        # WICKETS
        # ====================================================

        print_counter(
            "WICKET / DISMISSAL TYPES",
            wickets
        )

        print(
            f"\nTotal wickets recorded: "
            f"{sum(wickets.values()):,}"
        )

        # ====================================================
        # DATE RANGE
        # ====================================================

        if date_values:

            print("\n" + "=" * 80)
            print("DATE RANGE")
            print("=" * 80)

            print(
                f"\nEarliest match: "
                f"{min(date_values)}"
            )

            print(
                f"Latest match:   "
                f"{max(date_values)}"
            )

        # ====================================================
        # VALIDATION ERRORS
        # ====================================================

        print("\n" + "=" * 80)
        print("VALIDATION CHECKS")
        print("=" * 80)

        checks = []

        checks.append((
            "JSON files exist",
            len(members) > 0
        ))

        checks.append((
            "No JSON parsing errors",
            len(invalid_json_files) == 0
        ))

        checks.append((
            "Match IDs are unique",
            len(duplicate_match_ids) == 0
        ))

        checks.append((
            "All match IDs numeric",
            len(invalid_match_ids) == 0
        ))

        checks.append((
            "All matches are T20",
            len(invalid_match_types) == 0
        ))

        checks.append((
            "Gender is male/female",
            len(invalid_genders) == 0
        ))

        checks.append((
            "All participants have registry IDs",
            len(participants_without_registry) == 0
        ))

        for name, passed in checks:

            print(
                f"[{'PASS' if passed else 'FAIL'}] "
                f"{name}"
            )

        # ====================================================
        # DETAILED ERRORS
        # ====================================================

        if duplicate_match_ids:

            print("\nDUPLICATE MATCH IDs")
            print("-------------------")

            for item in duplicate_match_ids[:50]:
                print(item)

        if invalid_json_files:

            print("\nINVALID JSON FILES")
            print("------------------")

            for item in invalid_json_files[:20]:
                print(item)

        if invalid_match_ids:

            print("\nINVALID MATCH IDs")
            print("-----------------")

            for match_id in invalid_match_ids[:50]:
                print(match_id)

        if invalid_match_types:

            print("\nINVALID MATCH TYPES")
            print("-------------------")

            for item in invalid_match_types[:50]:
                print(item)

        if invalid_genders:

            print("\nINVALID GENDERS")
            print("----------------")

            for item in invalid_genders[:50]:
                print(item)

        if participants_without_registry:

            print("\nPARTICIPANTS WITHOUT REGISTRY IDs")
            print("----------------------------------")

            for item in sorted(participants_without_registry)[:100]:
                print(item)

        # ====================================================
        # FINAL STATUS
        # ====================================================

        all_passed = all(
            passed
            for _, passed in checks
        )

        print("\n" + "=" * 80)

        if all_passed:
            print("T20I RAW DATASET VALIDATION: PASS")
        else:
            print("T20I RAW DATASET VALIDATION: FAIL")

        print("=" * 80)


if __name__ == "__main__":
    main()