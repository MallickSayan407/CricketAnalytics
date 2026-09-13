import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime


ZIP_PATH = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\tests_json.zip"


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def main():
    print("=" * 80)
    print("TEST CRICKET RAW DATA VALIDATION")
    print("=" * 80)
    print(f"ZIP: {ZIP_PATH}")
    print()

    match_count = 0
    json_errors = 0

    match_ids = set()
    duplicate_match_ids = []

    genders = Counter()
    match_types = Counter()
    team_types = Counter()

    team_names = set()
    player_names = set()
    registry_ids = set()

    venues = set()
    cities = set()
    countries = set()
    seasons = Counter()

    date_values = []

    innings_counts = Counter()
    innings_by_gender = Counter()

    delivery_count = 0
    regulation_delivery_count = 0

    batter_runs = 0
    match_runs = 0

    extras = Counter()
    wicket_count = 0
    wicket_kinds = Counter()

    result_types = Counter()
    winners = Counter()

    declarations = 0
    forfeited_innings = 0
    follow_on_matches = 0
    follow_on_candidates = 0

    matches_with_missing = 0
    missing_fields = Counter()

    miscounted_overs = 0
    matches_with_miscounted_overs = 0

    absent_hurt_entries = 0
    penalty_innings = 0

    player_registry_missing = []
    participant_registry_missing = []

    zero_delivery_innings = 0
    empty_overs = 0

    innings_team_counts = Counter()

    unusual_innings_matches = []

    # Match-level audit details
    match_result_examples = []
    draw_examples = []
    tie_examples = []
    no_result_examples = []

    print("Opening ZIP...")

    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        json_files = [
            name for name in z.namelist()
            if name.lower().endswith(".json")
        ]

        print(f"JSON files found: {len(json_files)}")
        print()

        for index, filename in enumerate(json_files, start=1):

            try:
                with z.open(filename) as f:
                    data = json.load(f)
            except Exception as exc:
                json_errors += 1
                print(f"JSON ERROR: {filename}: {exc}")
                continue

            match_count += 1

            info = data.get("info", {})

            # -----------------------------------------------------------------
            # MATCH ID
            # -----------------------------------------------------------------
            match_id = filename.rsplit("/", 1)[-1].replace(".json", "")

            if match_id in match_ids:
                duplicate_match_ids.append(match_id)

            match_ids.add(match_id)

            # -----------------------------------------------------------------
            # BASIC INFO
            # -----------------------------------------------------------------
            gender = info.get("gender")
            match_type = info.get("match_type")
            team_type = info.get("team_type")

            genders[gender] += 1
            match_types[match_type] += 1
            team_types[team_type] += 1

            for team in info.get("teams", []):
                team_names.add(team)

            # -----------------------------------------------------------------
            # DATES
            # -----------------------------------------------------------------
            dates = info.get("dates", [])

            for value in dates:
                parsed = parse_date(value)
                if parsed:
                    date_values.append(parsed)

            # -----------------------------------------------------------------
            # SEASON
            # -----------------------------------------------------------------
            season = info.get("season")
            seasons[(gender, str(season))] += 1

            # -----------------------------------------------------------------
            # VENUE / CITY / COUNTRY
            # -----------------------------------------------------------------
            venue = info.get("venue")
            city = info.get("city")
            country = info.get("country")

            if venue:
                venues.add(venue)

            if city:
                cities.add(city)

            if country:
                countries.add(country)

            # -----------------------------------------------------------------
            # PLAYERS
            # -----------------------------------------------------------------
            players = info.get("players", {})

            for team, team_players in players.items():

                for player in team_players:
                    player_names.add(player)

            # -----------------------------------------------------------------
            # REGISTRY
            # -----------------------------------------------------------------
            registry = info.get("registry", {})
            people_registry = registry.get("people", {})

            for player_name, external_id in people_registry.items():
                registry_ids.add(external_id)

            # Check every declared player has a registry ID.
            for team, team_players in players.items():

                for player in team_players:

                    if player not in people_registry:
                        player_registry_missing.append(
                            (match_id, team, player)
                        )

            # -----------------------------------------------------------------
            # OUTCOME
            # -----------------------------------------------------------------
            outcome = info.get("outcome", {})

            winner = outcome.get("winner")
            result = outcome.get("result")
            eliminator = outcome.get("eliminator")

            if winner:
                result_types["WINNER"] += 1
                winners[winner] += 1

                if len(match_result_examples) < 10:
                    match_result_examples.append(
                        (match_id, winner)
                    )

            elif result:
                result_upper = str(result).upper()
                result_types[result_upper] += 1

                if result_upper == "DRAW":
                    if len(draw_examples) < 10:
                        draw_examples.append(match_id)

                elif result_upper == "TIE":
                    if len(tie_examples) < 10:
                        tie_examples.append(
                            (match_id, eliminator)
                        )

                elif result_upper == "NO RESULT":
                    if len(no_result_examples) < 10:
                        no_result_examples.append(match_id)

            else:
                result_types["UNKNOWN"] += 1

            # -----------------------------------------------------------------
            # MISSING DATA
            # -----------------------------------------------------------------
            missing = info.get("missing", [])

            if missing:
                matches_with_missing += 1

                for item in missing:
                    if isinstance(item, str):
                        missing_fields[item] += 1
                    else:
                        missing_fields[str(item)] += 1

            # -----------------------------------------------------------------
            # INNINGS
            # -----------------------------------------------------------------
            innings = data.get("innings", [])

            innings_count = len(innings)
            innings_counts[innings_count] += 1
            innings_by_gender[(gender, innings_count)] += 1

            innings_team_set = set()

            for innings_index, innings_data in enumerate(innings, start=1):

                batting_team = innings_data.get("team")

                if batting_team:
                    innings_team_set.add(batting_team)

                overs = innings_data.get("overs")

                # Forfeited innings may not contain normal overs.
                if innings_data.get("forfeited") is True:
                    forfeited_innings += 1

                if innings_data.get("declared") is True:
                    declarations += 1

                if innings_data.get("absent_hurt"):
                    absent_hurt_entries += len(
                        innings_data.get("absent_hurt", [])
                    )

                if innings_data.get("penalty_runs"):
                    penalty_innings += 1

                if overs is None:
                    zero_delivery_innings += 1
                    continue

                if len(overs) == 0:
                    zero_delivery_innings += 1

                for over in overs:

                    deliveries = over.get("deliveries", [])

                    if len(deliveries) == 0:
                        empty_overs += 1

                    # Miscounted overs
                    if "miscounted_overs" in innings_data:
                        pass

                    for delivery in deliveries:

                        delivery_count += 1
                        regulation_delivery_count += 1

                        runs = delivery.get("runs", {})

                        batter_runs += int(
                            runs.get("batter", 0)
                        )

                        match_runs += int(
                            runs.get("total", 0)
                        )

                        delivery_extras = delivery.get("extras", {})

                        for extra_type, value in delivery_extras.items():
                            extras[extra_type] += int(value)

                        wickets = delivery.get("wickets", [])

                        if wickets:
                            wicket_count += len(wickets)

                            for wicket in wickets:
                                wicket_kind = wicket.get(
                                    "kind",
                                    "UNKNOWN"
                                )

                                wicket_kinds[wicket_kind] += 1

            innings_team_counts[len(innings_team_set)] += 1

            # -----------------------------------------------------------------
            # MISCOUNTED OVERS
            # -----------------------------------------------------------------
            match_has_miscounted = False

            for innings_data in innings:

                if innings_data.get("miscounted_overs"):
                    match_has_miscounted = True

                    miscounted_overs += len(
                        innings_data["miscounted_overs"]
                    )

            if match_has_miscounted:
                matches_with_miscounted_overs += 1

            # -----------------------------------------------------------------
            # FOLLOW-ON / TEST-SPECIFIC METADATA
            # -----------------------------------------------------------------
            #
            # Cricsheet does not represent a follow-on as a simple
            # top-level boolean. We therefore identify likely follow-ons
            # structurally: the same team bats again as innings 3.
            #
            if len(innings) >= 3:

                first_team = innings[0].get("team")
                second_team = innings[1].get("team")
                third_team = innings[2].get("team")

                if (
                    first_team
                    and second_team
                    and third_team
                    and third_team == first_team
                ):
                    follow_on_candidates += 1

            # -----------------------------------------------------------------
            # UNUSUAL INNINGS STRUCTURES
            # -----------------------------------------------------------------
            if innings_count not in (2, 4):
                unusual_innings_matches.append(
                    (match_id, gender, innings_count)
                )

            # -----------------------------------------------------------------
            # PROGRESS
            # -----------------------------------------------------------------
            if index % 100 == 0:
                print(
                    f"Processed {index:,} / "
                    f"{len(json_files):,} matches..."
                )

    # =========================================================================
    # REPORT
    # =========================================================================

    print()
    print("=" * 80)
    print("TEST RAW DATA VALIDATION REPORT")
    print("=" * 80)

    print()
    print("MATCH UNIVERSE")
    print("-" * 80)
    print(f"Matches: {match_count:,}")
    print(f"Unique match IDs: {len(match_ids):,}")
    print(f"Duplicate match IDs: {len(duplicate_match_ids):,}")
    print(f"JSON errors: {json_errors:,}")

    print()
    print("GENDER")
    print("-" * 80)

    for key, value in sorted(genders.items()):
        print(f"{key}: {value:,}")

    print()
    print("MATCH TYPE")
    print("-" * 80)

    for key, value in sorted(match_types.items()):
        print(f"{key}: {value:,}")

    print()
    print("TEAM TYPE")
    print("-" * 80)

    for key, value in sorted(team_types.items()):
        print(f"{key}: {value:,}")

    print()
    print("DATE RANGE")
    print("-" * 80)

    if date_values:
        print(f"Earliest date: {min(date_values)}")
        print(f"Latest date:   {max(date_values)}")

    print()
    print("SEASONS")
    print("-" * 80)

    season_totals = Counter()

    for (gender, season), count in sorted(seasons.items()):
        print(f"{gender:>6} | {season:<12} | {count:>5}")
        season_totals[season] += count

    print()
    print("TEAMS / PLAYERS / VENUES")
    print("-" * 80)
    print(f"Unique team names: {len(team_names):,}")
    print(f"Unique player names: {len(player_names):,}")
    print(f"Unique registry IDs: {len(registry_ids):,}")
    print(f"Unique venues: {len(venues):,}")
    print(f"Unique cities: {len(cities):,}")
    print(f"Unique countries: {len(countries):,}")

    print()
    print("PLAYER REGISTRY")
    print("-" * 80)
    print(
        f"Players missing registry ID: "
        f"{len(player_registry_missing):,}"
    )

    if player_registry_missing:
        print()
        print("Examples:")

        for row in player_registry_missing[:20]:
            print(row)

    print()
    print("INNINGS")
    print("-" * 80)

    for count, matches in sorted(innings_counts.items()):
        print(
            f"{count:>3} innings: "
            f"{matches:>5} matches"
        )

    print()
    print("INNINGS BY GENDER")
    print("-" * 80)

    for (gender, innings_count), count in sorted(
        innings_by_gender.items()
    ):
        print(
            f"{gender:>6} | "
            f"{innings_count:>3} innings | "
            f"{count:>5} matches"
        )

    print()
    print("DELIVERIES / RUNS")
    print("-" * 80)
    print(f"Total deliveries: {delivery_count:,}")
    print(f"Batter runs: {batter_runs:,}")
    print(f"Match runs: {match_runs:,}")

    print()
    print("EXTRAS")
    print("-" * 80)

    total_extras = sum(extras.values())

    for key, value in sorted(extras.items()):
        print(f"{key}: {value:,}")

    print(f"Total extras: {total_extras:,}")

    print()
    print("WICKETS")
    print("-" * 80)
    print(f"Total wicket events: {wicket_count:,}")

    for key, value in sorted(wicket_kinds.items()):
        print(f"{key}: {value:,}")

    print()
    print("MATCH RESULTS")
    print("-" * 80)

    for key, value in sorted(result_types.items()):
        print(f"{key}: {value:,}")

    print()
    print("TOP WINNERS")
    print("-" * 80)

    for team, count in winners.most_common(20):
        print(f"{team}: {count:,}")

    print()
    print("TEST-SPECIFIC STRUCTURE")
    print("-" * 80)
    print(f"Declared innings: {declarations:,}")
    print(f"Forfeited innings: {forfeited_innings:,}")
    print(
        f"Likely follow-on structures: "
        f"{follow_on_candidates:,}"
    )
    print(f"Zero-delivery innings: {zero_delivery_innings:,}")
    print(f"Empty overs: {empty_overs:,}")
    print(
        f"Matches with miscounted overs: "
        f"{matches_with_miscounted_overs:,}"
    )
    print(f"Miscounted overs: {miscounted_overs:,}")
    print(f"Penalty-run innings: {penalty_innings:,}")
    print(f"Absent-hurt entries: {absent_hurt_entries:,}")

    print()
    print("MISSING DATA")
    print("-" * 80)
    print(f"Matches with missing metadata: {matches_with_missing:,}")

    for key, value in missing_fields.most_common():
        print(f"{key}: {value:,}")

    print()
    print("UNUSUAL INNINGS COUNTS")
    print("-" * 80)
    print(
        f"Matches with innings count other than 2 or 4: "
        f"{len(unusual_innings_matches):,}"
    )

    if unusual_innings_matches:
        for row in unusual_innings_matches[:30]:
            print(row)

    print()
    print("RESULT EXAMPLES")
    print("-" * 80)

    print("Winner examples:")
    for row in match_result_examples:
        print(row)

    print()
    print("Draw examples:")
    for row in draw_examples:
        print(row)

    print()
    print("Tie examples:")
    for row in tie_examples:
        print(row)

    print()
    print("No-result examples:")
    for row in no_result_examples:
        print(row)

    # =========================================================================
    # BASIC VALIDATION
    # =========================================================================

    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)

    checks_passed = 0
    checks_failed = 0

    def check(condition, label):
        nonlocal checks_passed, checks_failed

        if condition:
            print(f"PASS: {label}")
            checks_passed += 1
        else:
            print(f"FAIL: {label}")
            checks_failed += 1

    check(
        match_count == len(match_ids),
        "All match IDs are unique"
    )

    check(
        json_errors == 0,
        "No JSON parsing errors"
    )

    check(
        match_types == Counter({"Test": match_count}),
        "All records are Test matches"
    )

    check(
        len(player_registry_missing) == 0,
        "All declared players have registry IDs"
    )

    check(
        len(duplicate_match_ids) == 0,
        "No duplicate match IDs"
    )

    check(
        batter_runs <= match_runs,
        "Batter runs do not exceed total match runs"
    )

    check(
        match_runs == batter_runs + total_extras,
        "Match runs = batter runs + extras"
    )

    check(
        wicket_count > 0,
        "Wicket events were detected"
    )

    check(
        len(team_names) >= 2,
        "Multiple teams detected"
    )

    check(
        len(player_names) > 0,
        "Players detected"
    )

    print()
    print(
        f"VALIDATION SUMMARY: "
        f"PASS={checks_passed} "
        f"FAIL={checks_failed}"
    )

    if checks_failed == 0:
        print()
        print("TEST RAW DATA VALIDATION: PASS")
    else:
        print()
        print("TEST RAW DATA VALIDATION: FAIL")

    print("=" * 80)


if __name__ == "__main__":
    main()